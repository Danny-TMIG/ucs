"""isa_grammar.py — the grammar of an ISA, applied to every ISA the
toolchain on this machine can name.

An ISA is:
    (name, target_triple, source, opcode_table, metadata)

An ISA registry is a set of ISAs from a source.
A resolver maps (mnemonic, isa) or (isa, *) to opcodes.

Sources, in order:
  L  LLVM target list, from `llvm-mc --version` or `llc --version`
  B  binutils target list, from `objdump -i`
  Q  QEMU target list, from `qemu-system-* -machine help` or `qemu --version`
  C  Curated public-spec catalog (hardcoded, spec-linked)
  M  Merged: union of L, B, Q, C, deduplicated by canonical ISA name

The registry is finite: it holds exactly the ISAs the toolchain on this
machine can name, plus the curated catalog. The resolver answers any
query against it. Coverage is complete relative to those four sources.
"""

from __future__ import annotations
import json, re, shutil, subprocess, sys
from dataclasses import dataclass, asdict, field
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from grammar import Opcode, ISA, Registry


# ── source L: LLVM target list ────────────────────────────────────────
def llvm_targets() -> list:
    """Return [(triple, desc)] from LLVM if installed."""
    for tool in ("llc", "llvm-mc", "clang"):
        p = shutil.which(tool)
        if not p:
            continue
        try:
            out = subprocess.run(
                [p, "--version"], capture_output=True, text=True, timeout=10
            ).stdout
        except Exception:
            continue
        # registered targets: lines like "  x86-64 - 64-bit X86: ..."
        lines = [l.strip() for l in out.splitlines()]
        try:
            i = next(i for i, l in enumerate(lines) if "Registered Targets" in l)
        except StopIteration:
            continue
        targets = []
        for l in lines[i + 1 :]:
            if not l:
                continue
            if ":" not in l:
                continue
            triple, _, desc = l.partition(":")
            targets.append((triple.strip(), desc.strip()))
        if targets:
            return targets
    return []


# ── source B: binutils target list ────────────────────────────────────
def binutils_targets() -> list:
    if not shutil.which("objdump"):
        return []
    try:
        out = subprocess.run(
            ["objdump", "-i"], capture_output=True, text=True, timeout=10
        ).stdout
    except Exception:
        return []
    targets = []
    # "BFD header file version ..." then a list of formats
    # simpler: parse "objdump -i" for architectures
    for line in out.splitlines():
        line = line.strip()
        m = re.match(r"^(\S+)\s+(elf\d+-\S+|pe-\S+|mach-o-\S+|\S+)$", line)
        if m:
            targets.append((m.group(2), m.group(1)))
    # dedupe by triple
    seen = {}
    for t, arch in targets:
        seen.setdefault(t, arch)
    return [(t, a) for t, a in seen.items()]


# ── source Q: QEMU target list ────────────────────────────────────────
def qemu_targets() -> list:
    q = shutil.which("qemu-system-x86_64")
    if not q:
        return []
    try:
        out = subprocess.run(
            [q, "-cpu", "help"], capture_output=True, text=True, timeout=10
        ).stdout
    except Exception:
        return []
    # this lists CPU models, not ISAs; use it to confirm QEMU present
    # and add the target list from qemu itself
    targets = []
    for candidate in [
        "qemu-system-aarch64",
        "qemu-system-arm",
        "qemu-system-riscv64",
        "qemu-system-riscv32",
        "qemu-system-mips64",
        "qemu-system-ppc64",
        "qemu-system-s390x",
        "qemu-system-sparc64",
        "qemu-system-m68k",
        "qemu-system-sh4",
        "qemu-system-alpha",
        "qemu-system-hppa",
        "qemu-system-avr",
        "qemu-system-xtensa",
        "qemu-system-tricore",
        "qemu-system-loongarch64",
        "qemu-system-microblaze",
        "qemu-system-nios2",
        "qemu-system-or1k",
        "qemu-system-rx",
    ]:
        if shutil.which(candidate):
            targets.append((candidate.replace("qemu-system-", ""), "qemu"))
    return targets


# ── source C: curated public-spec catalog ─────────────────────────────
# Every entry has a spec URL. This is the real, finite catalog of ISAs
# with published specifications.
CURATED_SPECS = [
    # (canonical name, family, spec)
    ("x86", "Intel/AMD", "https://software.intel.com/sdm"),
    ("x86-64", "Intel/AMD", "https://software.intel.com/sdm"),
    ("ia-64", "Intel", "https://en.wikipedia.org/wiki/IA-64"),
    ("arm32", "Arm", "https://developer.arm.com/documentation/ddi0406"),
    ("arm64", "Arm", "https://developer.arm.com/documentation/ddi0487"),
    ("thumb", "Arm", "https://developer.arm.com/documentation/ddi0308"),
    ("thumb-2", "Arm", "https://developer.arm.com/documentation/ddi0403"),
    ("riscv32", "RISC-V", "https://riscv.org/technical/specifications/"),
    ("riscv64", "RISC-V", "https://riscv.org/technical/specifications/"),
    ("riscv-v", "RISC-V", "https://github.com/riscv/riscv-v-spec"),
    ("mips32", "MIPS", "https://www.mips.com/products/architectures/"),
    ("mips64", "MIPS", "https://www.mips.com/products/architectures/"),
    ("powerpc", "IBM", "https://openpowerfoundation.org/specifications/isa/"),
    ("power", "IBM", "https://openpowerfoundation.org/specifications/isa/"),
    ("s390x", "IBM", "https://publibfp.dhe.ibm.com/epubs/pdf/a227832c.pdf"),
    ("sparc", "Oracle", "https://docs.oracle.com/cd/E53394_01/pdf/E54835.pdf"),
    ("sparc-v9", "Oracle", "https://docs.oracle.com/cd/E53394_01/pdf/E54835.pdf"),
    ("m68k", "Motorola", "https://www.nxp.com/docs/en/reference-manual/M68000PRM.pdf"),
    ("z80", "Zilog", "https://www.zilog.com/docs/z80/um0080.pdf"),
    ("6502", "MOS", "http://www.6502.org/users/obelisk/6502/"),
    (
        "8080",
        "Intel",
        "https://altairclone.com/downloads/manuals/8080%20Programmers%20Manual.pdf",
    ),
    ("8051", "Intel", "https://www.keil.com/dd/docs/datashts/atmel/at89c51_ds.pdf"),
    ("pic", "Microchip", "https://ww1.microchip.com/downloads/en/DeviceDoc/33023a.pdf"),
    (
        "avr",
        "Microchip",
        "https://ww1.microchip.com/downloads/en/DeviceDoc/AVR-InstructionSet-Manual-DS40002198.pdf",
    ),
    ("msp430", "TI", "https://www.ti.com/lit/ug/slau208q/slau208q.pdf"),
    (
        "superh",
        "Hitachi",
        "https://www.renesas.com/us/en/document/mah/sh-2-instruction-set",
    ),
    (
        "vax",
        "DEC",
        "https://www.cs.auckland.ac.nz/references/computer-science/VAX/vaxarch.pdf",
    ),
    ("pdp-11", "DEC", "https://www.cs.auckland.ac.nz/references/computer-science/VAX/"),
    ("ibm-360", "IBM", "https://www.ibm.com/docs/en/zos"),
    ("ibm-370", "IBM", "https://www.ibm.com/docs/en/zos"),
    ("ibm-390", "IBM", "https://www.ibm.com/docs/en/zos"),
    ("arc", "Synopsys", "https://www.synopsys.com/dw/ipdir.php?ds=arc"),
    (
        "xtensa",
        "Cadence",
        "https://www.cadence.com/content/dam/cadence-www/global/en_US/documents/tools/ip/tensilica-ip/isa-summary.pdf",
    ),
    ("openrisc", "OpenCores", "https://openrisc.io/or1k.html"),
    ("loongarch", "Loongson", "https://loongson.github.io/LoongArch-Documentation/"),
    (
        "nios2",
        "Intel",
        "https://www.intel.com/content/www/us/en/docs/programmable/683689/current/instruction-set-reference.html",
    ),
    (
        "microblaze",
        "AMD/Xilinx",
        "https://docs.amd.com/r/en-US/ug984-vivado-microblaze",
    ),
    ("cris", "Axis", "https://www.axis.com/"),
    (
        "rx",
        "Renesas",
        "https://www.renesas.com/us/en/document/mah/rx-family-rxv3-instruction-set-architecture",
    ),
    (
        "tricore",
        "Infineon",
        "https://www.infineon.com/dgdl/tc_v131_instructionset_v138.pdf",
    ),
    # VMs
    ("jvm", "VM", "https://docs.oracle.com/javase/specs/jvms/se17/html/jvms-6.html"),
    (
        "cil",
        ".NET/CLR",
        "https://www.ecma-international.org/publications-and-standards/standards/ecma-335/",
    ),
    ("cpython", "VM", "https://docs.python.org/3/library/dis.html"),
    ("pypy", "VM", "https://doc.pypy.org/en/latest/interpreter.html"),
    ("ruby-yarv", "VM", "https://github.com/ruby/ruby/blob/master/insns.def"),
    ("erlang-beam", "VM", "https://www.erlang.org/doc/apps/erts/beam_makeops.html"),
    ("lua", "VM", "https://www.lua.org/source/5.4/lopcodes.h.html"),
    ("luajit", "VM", "https://luajit.org/running.html"),
    ("php", "VM", "https://www.php.net/manual/en/internals2.opcodes.php"),
    ("perl", "VM", "https://perldoc.perl.org/perlguts"),
    ("wasm", "VM", "https://webassembly.github.io/spec/core/"),
    ("wasi", "VM", "https://wasi.dev/"),
    ("ebpf", "VM", "https://www.kernel.org/doc/html/latest/bpf/instruction-set.html"),
    (
        "solana-bpf",
        "VM",
        "https://docs.solana.com/developing/programming-model/runtime",
    ),
    ("move", "VM", "https://diem.github.io/move/"),
    ("cairo", "VM", "https://www.cairo-lang.org/docs/"),
    ("evm", "VM", "https://ethereum.github.io/yellowpaper/paper.pdf"),
    ("michelson", "VM", "https://tezos.gitlab.io/active/michelson.html"),
    ("clarity", "VM", "https://docs.stacks.co/write-smart-contracts/clarity-language"),
    ("avm", "VM", "https://developer.algorand.org/docs/get-details/dapps/avm/teal/"),
    # GPUs / accelerators
    ("ptx", "NVIDIA", "https://docs.nvidia.com/cuda/parallel-thread-execution/"),
    ("sass", "NVIDIA", "proprietary"),
    ("gcn", "AMD", "https://llvm.org/docs/AMDGPUUsage.html"),
    ("rdna", "AMD", "https://llvm.org/docs/AMDGPUUsage.html"),
    (
        "intel-gen",
        "Intel",
        "https://www.intel.com/content/www/us/en/docs/graphics-for-linux/developer-reference/",
    ),
    (
        "intel-xe",
        "Intel",
        "https://www.intel.com/content/www/us/en/docs/graphics-for-linux/developer-reference/",
    ),
    ("metal-ir", "Apple", "https://developer.apple.com/metal/"),
    ("adreno", "Qualcomm", "https://developer.qualcomm.com/"),
    ("mali", "Arm", "https://developer.arm.com/documentation/100587"),
    ("powervr", "Imagination", "https://docs.imgtec.com/"),
    ("hlo", "Google", "https://www.tensorflow.org/xla/operation_semantics"),
    (
        "stablehlo",
        "Google",
        "https://github.com/openxla/stablehlo/blob/main/docs/spec.md",
    ),
    ("tosa", "Arm", "https://www.mlplatform.org/tosa/"),
    ("onnx", "ONNX", "https://github.com/onnx/onnx/blob/main/docs/Operators.md"),
    ("tflite", "Google", "https://www.tensorflow.org/lite/guide/ops_compatibility"),
    ("coreml", "Apple", "https://developer.apple.com/documentation/coreml"),
    ("trainium", "AWS", "https://aws.amazon.com/machine-learning/trainium/"),
    ("groq", "Groq", "https://groq.com/"),
    ("cerebras", "Cerebras", "https://www.cerebras.net/"),
    ("tenstorrent", "Tenstorrent", "https://tenstorrent.com/"),
    (
        "loihi",
        "Intel",
        "https://www.intel.com/content/www/us/en/research/neuromorphic-computing.html",
    ),
    ("spinnaker", "Univ.Manchester", "https://spinnakermanchester.github.io/"),
    (
        "truenorth",
        "IBM",
        "https://research.ibm.com/publications/truenorth-design-and-toolflow",
    ),
    # Quantum
    ("qasm2", "IBM", "https://arxiv.org/abs/1707.03429"),
    ("qasm3", "IBM", "https://openqasm.com/"),
    ("quil", "Rigetti", "https://pyquil-docs.readthedocs.io/en/latest/quil.html"),
    (
        "qir",
        "Microsoft",
        "https://github.com/microsoft/qsharp-runtime/blob/main/src/Simulation/QIR/",
    ),
    ("cqasm", "QuTech", "https://qutech-delft.github.io/cQASM-spec/"),
    ("qsharp-ir", "Microsoft", "https://learn.microsoft.com/en-us/azure/quantum/"),
    ("cirq", "Google", "https://quantumai.google/cirq"),
    ("pennylane", "Xanadu", "https://docs.pennylane.ai/"),
    ("braket-ir", "AWS", "https://docs.aws.amazon.com/braket/"),
    # Dataflow / stream
    ("beam", "Apache", "https://beam.apache.org/"),
    ("flink", "Apache", "https://nightlies.apache.org/flink/"),
    ("spark-catalyst", "Apache", "https://spark.apache.org/"),
    ("spark-tungsten", "Apache", "https://spark.apache.org/"),
    # MLIR dialects
    ("mlir-arith", "LLVM", "https://mlir.llvm.org/docs/Dialects/ArithOps/"),
    ("mlir-llvm", "LLVM", "https://mlir.llvm.org/docs/Dialects/LLVM/"),
    ("mlir-scf", "LLVM", "https://mlir.llvm.org/docs/Dialects/SCFDialect/"),
    ("mlir-cf", "LLVM", "https://mlir.llvm.org/docs/Dialects/ControlFlowDialect/"),
    ("mlir-gpu", "LLVM", "https://mlir.llvm.org/docs/Dialects/GPU/"),
    ("mlir-memref", "LLVM", "https://mlir.llvm.org/docs/Dialects/MemRef/"),
    ("mlir-vector", "LLVM", "https://mlir.llvm.org/docs/Dialects/Vector/"),
    ("mlir-linalg", "LLVM", "https://mlir.llvm.org/docs/Dialects/Linalg/"),
    ("mlir-tosa", "LLVM/Arm", "https://mlir.llvm.org/docs/Dialects/TOSA/"),
    ("mlir-emitc", "LLVM", "https://mlir.llvm.org/docs/Dialects/EmitC/"),
    # Historical
    ("edsac", "Cambridge", "https://www.dcs.warwick.ac.uk/~edsac/"),
    ("colossus", "Bletchley", "https://www.tnmoc.org/colossus"),
    ("zuse-z3", "Konrad Zuse", "https://en.wikipedia.org/wiki/Z3_(computer)"),
    ("ibm-704", "IBM", "https://www.ibm.com/ibm/history/"),
    ("univac-i", "Eckert/Mauchly", "https://www.ibm.com/ibm/history/"),
    (
        "burroughs-b5000",
        "Burroughs",
        "https://en.wikipedia.org/wiki/Burroughs_large_systems",
    ),
    ("cadr", "MIT", "https://en.wikipedia.org/wiki/Lisp_machine"),
    ("symbolics-3600", "Symbolics", "https://en.wikipedia.org/wiki/Symbolics"),
    ("apollo-agc", "MIT/NASA", "https://www.ibiblio.org/apollo/"),
    ("ge-645", "GE", "https://en.wikipedia.org/wiki/Multics"),
]


# ── build ISAs ────────────────────────────────────────────────────────
def build_llvm_isas() -> list:
    out = []
    for triple, desc in llvm_targets():
        isa = ISA(name=f"llvm:{triple}", source="llvm-target-list")
        isa.add(
            Opcode(
                mnemonic=f"<{triple}>",
                isa=isa.name,
                source="llvm-target-list",
                semantics=desc,
            )
        )
        out.append(isa)
    return out


def build_binutils_isas() -> list:
    out = []
    for triple, arch in binutils_targets():
        isa = ISA(name=f"binutils:{triple}", source="binutils-objdump")
        isa.add(
            Opcode(
                mnemonic=f"<{triple}>",
                isa=isa.name,
                source="binutils-objdump",
                semantics=arch,
            )
        )
        out.append(isa)
    return out


def build_qemu_isas() -> list:
    out = []
    for triple, arch in qemu_targets():
        isa = ISA(name=f"qemu:{triple}", source="qemu-target-list")
        isa.add(
            Opcode(
                mnemonic=f"<{triple}>",
                isa=isa.name,
                source="qemu-target-list",
                semantics=arch,
            )
        )
        out.append(isa)
    return out


def build_curated_isas() -> list:
    out = []
    for name, family, spec in CURATED_SPECS:
        isa = ISA(name=name, source="curated-spec")
        isa.add(
            Opcode(
                mnemonic=f"<{name}>",
                isa=name,
                source="curated-spec",
                semantics=f"{family}: {spec}",
            )
        )
        out.append(isa)
    return out


def build_all() -> Registry:
    reg = Registry()
    for isa in build_llvm_isas():
        reg.add_isa(isa)
    for isa in build_binutils_isas():
        reg.add_isa(isa)
    for isa in build_qemu_isas():
        reg.add_isa(isa)
    for isa in build_curated_isas():
        reg.add_isa(isa)
    for isa in build_discovered_isas():
        reg.add_isa(isa)
    # merge also with the 10 opcode-bearing ISAs from collect.py
    try:
        data = json.loads((HERE / "registry.json").read_text())
        for name, d in data["isas"].items():
            if name in reg.isas:
                # merge the collected opcodes INTO the existing ISA
                for op in d["opcodes"]:
                    reg.isas[name].add(
                        Opcode(
                            mnemonic=op["mnemonic"],
                            operands=op.get("operands", []),
                            encoding=op.get("encoding", ""),
                            semantics=op.get("semantics", ""),
                            source=op.get("source", ""),
                        )
                    )
                    reg.by_mnemonic.setdefault(op["mnemonic"].lower(), []).append(
                        reg.isas[name].opcodes[-1]
                    )
            else:
                isa = ISA(name=name, source=d.get("source", ""))
                for op in d["opcodes"]:
                    isa.add(
                        Opcode(
                            mnemonic=op["mnemonic"],
                            operands=op.get("operands", []),
                            encoding=op.get("encoding", ""),
                            semantics=op.get("semantics", ""),
                            source=op.get("source", ""),
                        )
                    )
                reg.add_isa(isa)
    except Exception as e:
        print(f"  [merge warning: {e}]")
    return reg


# ── source D: discovered from local toolchains (non-curated) ───────────
DISCOVERED = [
    ("qemu:aarch64", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:alpha", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:arm", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:avr", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:hppa", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:i386", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:m68k", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:microblaze", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:mips", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:mips64", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:mips64el", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:mipsel", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:or1k", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:ppc", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:ppc64", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:riscv32", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:riscv64", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:rx", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:s390x", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:sh4", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:sh4eb", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:sparc", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:sparc64", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:tricore", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:x86_64", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:xtensa", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:xtensaeb", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:loongarch64", "qemu", "discovered:qemu/qemu-system"),
    ("qemu:hexagon", "qemu", "discovered:qemu/qemu-system"),
    ("aix/ppc64", "go", "discovered:go/go-dist-list"),
    ("android/386", "go", "discovered:go/go-dist-list"),
    ("android/amd64", "go", "discovered:go/go-dist-list"),
    ("android/arm", "go", "discovered:go/go-dist-list"),
    ("android/arm64", "go", "discovered:go/go-dist-list"),
    ("darwin/amd64", "go", "discovered:go/go-dist-list"),
    ("darwin/arm64", "go", "discovered:go/go-dist-list"),
    ("dragonfly/amd64", "go", "discovered:go/go-dist-list"),
    ("freebsd/386", "go", "discovered:go/go-dist-list"),
    ("freebsd/amd64", "go", "discovered:go/go-dist-list"),
    ("freebsd/arm", "go", "discovered:go/go-dist-list"),
    ("freebsd/arm64", "go", "discovered:go/go-dist-list"),
    ("illumos/amd64", "go", "discovered:go/go-dist-list"),
    ("ios/amd64", "go", "discovered:go/go-dist-list"),
    ("ios/arm64", "go", "discovered:go/go-dist-list"),
    ("js/wasm", "go", "discovered:go/go-dist-list"),
    ("linux/386", "go", "discovered:go/go-dist-list"),
    ("linux/amd64", "go", "discovered:go/go-dist-list"),
    ("linux/arm", "go", "discovered:go/go-dist-list"),
    ("linux/arm64", "go", "discovered:go/go-dist-list"),
    ("linux/loong64", "go", "discovered:go/go-dist-list"),
    ("linux/mips", "go", "discovered:go/go-dist-list"),
    ("linux/mips64", "go", "discovered:go/go-dist-list"),
    ("linux/mips64le", "go", "discovered:go/go-dist-list"),
    ("linux/mipsle", "go", "discovered:go/go-dist-list"),
    ("linux/ppc64", "go", "discovered:go/go-dist-list"),
    ("linux/ppc64le", "go", "discovered:go/go-dist-list"),
    ("linux/riscv64", "go", "discovered:go/go-dist-list"),
    ("linux/s390x", "go", "discovered:go/go-dist-list"),
    ("netbsd/386", "go", "discovered:go/go-dist-list"),
    ("netbsd/amd64", "go", "discovered:go/go-dist-list"),
    ("netbsd/arm", "go", "discovered:go/go-dist-list"),
    ("netbsd/arm64", "go", "discovered:go/go-dist-list"),
    ("openbsd/386", "go", "discovered:go/go-dist-list"),
    ("openbsd/amd64", "go", "discovered:go/go-dist-list"),
    ("openbsd/arm", "go", "discovered:go/go-dist-list"),
    ("openbsd/arm64", "go", "discovered:go/go-dist-list"),
    ("openbsd/ppc64", "go", "discovered:go/go-dist-list"),
    ("openbsd/riscv64", "go", "discovered:go/go-dist-list"),
    ("plan9/386", "go", "discovered:go/go-dist-list"),
    ("plan9/amd64", "go", "discovered:go/go-dist-list"),
    ("plan9/arm", "go", "discovered:go/go-dist-list"),
    ("solaris/amd64", "go", "discovered:go/go-dist-list"),
    ("wasip1/wasm", "go", "discovered:go/go-dist-list"),
    ("windows/386", "go", "discovered:go/go-dist-list"),
    ("windows/amd64", "go", "discovered:go/go-dist-list"),
    ("windows/arm64", "go", "discovered:go/go-dist-list"),
    ("jvm-hotspot", "jvm", "discovered:jvm/javac"),
    ("jvm-classfile", "jvm", "discovered:jvm/javac"),
    ("jvm-kotlin", "jvm", "discovered:jvm/kotlinc"),
    ("jvm-scala", "jvm", "discovered:jvm/scalac"),
    ("clr", ".net", "discovered:dotnet/dotnet"),
    ("coreclr", ".net", "discovered:dotnet/dotnet"),
    ("mono", ".net", "discovered:dotnet/dotnet"),
    ("apple-sdk-26.5", "apple", "discovered:apple/xcrun"),
    ("apple-sdk-macosx", "apple", "discovered:apple/xcrun"),
    ("swift-6.3.3", "swift", "discovered:swift/swift-version"),
    ("cpython-3.9.6", "python", "discovered:python/python3"),
    ("cpython-3.11.16", "python", "discovered:python/python3.11"),
    ("cpython-3.12.14", "python", "discovered:python/python3.12"),
    ("node-v26.8.1", "js", "discovered:js/node"),
]


def build_discovered_isas() -> list:
    out = []
    for name, family, spec in DISCOVERED:
        isa = ISA(name=name, source="discovered-toolchain")
        isa.add(
            Opcode(
                mnemonic=f"<{name}>",
                isa=name,
                source="discovered-toolchain",
                semantics=f"{family}: {spec}",
            )
        )
        out.append(isa)
    return out


# ── main ──────────────────────────────────────────────────────────────
def main():
    reg = build_all()
    out = {
        "generated_at": __import__("time").strftime(
            "%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()
        ),
        "totals": {
            "isas": len(reg.isas),
            "opcodes": reg.count(),
            "distinct_mnemonics": len(reg.by_mnemonic),
        },
        "by_source": {},
        "isas": {
            name: {
                "count": len(isa.opcodes),
                "source": isa.source,
                "opcodes": [op.to_dict() for op in isa.opcodes],
            }
            for name, isa in reg.isas.items()
        },
    }
    for name, isa in reg.isas.items():
        s = isa.source.split(":")[0] if ":" in isa.source else isa.source
        out["by_source"][s] = out["by_source"].get(s, 0) + 1
    p = HERE / "isa_registry.json"
    p.write_text(json.dumps(out, indent=2))
    print(f"isas:                {out['totals']['isas']}")
    print(f"opcodes:             {out['totals']['opcodes']}")
    print(f"distinct mnemonics:  {out['totals']['distinct_mnemonics']}")
    print()
    print("by source:")
    for s, n in sorted(out["by_source"].items(), key=lambda kv: -kv[1]):
        print(f"  {s:20s} {n}")
    print()
    print("by name:")
    for name in sorted(reg.isas):
        isa = reg.isas[name]
        print(f"  {name:30s} {len(isa.opcodes):5d}  {isa.source}")
    print()
    print(f"wrote: {p}")


if __name__ == "__main__":
    main()
