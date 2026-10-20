"""noncurated.py — build every ISA entry not already in the curated catalog.

Sources scanned:
  L  llvm-mc --version / llc --version / clang --version   (target triples)
  B  objdump -i                                             (BFD formats)
  Q  qemu-system-*                                          (system targets)
  A  as --version, ld --version, gcc --version              (architectures)
  R  rustc --print target-list                              (Rust target triples)
  G  go tool dist list                                      (Go targets)
  J  javac -version + jdk modules                           (JVM family)
  C  dotnet --list-runtimes                                 (CLR family)
  X  xcrun --show-sdk-version + xcodebuild -version        (Apple SDKs)
  S  swift --version                                        (Swift targets)

Each scanner yields (isa_name, family, source_tool, raw_line).
Deduplicate against the curated catalog in isa_grammar.py.
Write the union to noncurated.json.
"""

from __future__ import annotations
import json, re, shutil, subprocess, sys
from dataclasses import dataclass, asdict, field
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))


def run(cmd, timeout=15) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout or ""
    except Exception:
        return ""


# ── L: LLVM target list ───────────────────────────────────────────────
def scan_llvm():
    out = []
    for tool in ("llvm-mc", "llc", "clang"):
        p = shutil.which(tool)
        if not p:
            continue
        txt = run([p, "--version"])
        lines = txt.splitlines()
        try:
            i = next(i for i, l in enumerate(lines) if "Registered Targets" in l)
        except StopIteration:
            continue
        for l in lines[i + 1 :]:
            m = re.match(r"\s*(\S+)\s*-\s*(.*)$", l)
            if not m:
                continue
            out.append((m.group(1), "llvm", f"{tool}-targets", l.strip()))
        break
    return out


# ── B: BFD/objdump formats ────────────────────────────────────────────
def scan_binutils():
    p = shutil.which("objdump")
    if not p:
        return []
    txt = run([p, "-i"])
    out = []
    in_section = False
    for l in txt.splitlines():
        if "BFD header file version" in l or "file format" in l.lower():
            in_section = True
        if not in_section:
            continue
        m = re.match(r"\s*(\S+)\s+(\S+)", l)
        if not m:
            continue
        arch, fmt = m.group(1), m.group(2)
        if arch in ("BFD", "Header", "file", ""):
            continue
        out.append((f"{arch}/{fmt}", "binutils", "objdump-i", l.strip()))
    return out


# ── Q: QEMU system targets ────────────────────────────────────────────
QEMU_TARGETS = [
    "aarch64",
    "alpha",
    "arm",
    "avr",
    "cris",
    "hppa",
    "i386",
    "lm32",
    "m68k",
    "microblaze",
    "microblazeel",
    "mips",
    "mips64",
    "mips64el",
    "mipsel",
    "moxie",
    "nios2",
    "or1k",
    "ppc",
    "ppc64",
    "riscv32",
    "riscv64",
    "rx",
    "s390x",
    "sh4",
    "sh4eb",
    "sparc",
    "sparc64",
    "tricore",
    "x86_64",
    "xtensa",
    "xtensaeb",
    "loongarch64",
    "hppa",
    "hexagon",
]


def scan_qemu():
    out = []
    for t in QEMU_TARGETS:
        if shutil.which(f"qemu-system-{t}"):
            out.append((f"qemu:{t}", "qemu", "qemu-system", f"qemu-system-{t}"))
    return out


# ── R: Rust target triples ────────────────────────────────────────────
def scan_rust():
    p = shutil.which("rustc")
    if not p:
        return []
    txt = run([p, "--print", "target-list"])
    return [
        (t.strip(), "rust", "rustc-target-list", t.strip())
        for t in txt.splitlines()
        if t.strip()
    ]


# ── G: Go targets ─────────────────────────────────────────────────────
def scan_go():
    p = shutil.which("go")
    if not p:
        return []
    txt = run([p, "tool", "dist", "list"])
    return [
        (t.strip(), "go", "go-dist-list", t.strip())
        for t in txt.splitlines()
        if t.strip()
    ]


# ── A: GCC/as/ld --version ────────────────────────────────────────────
def scan_gcc():
    out = []
    for tool in ("gcc", "as", "ld"):
        p = shutil.which(tool)
        if not p:
            continue
        txt = run([p, "--version"])
        # "gcc ... configured with: --target=... --with-arch=..."
        for m in re.finditer(r"--(?:target|with-arch)=([A-Za-z0-9_\-]+)", txt):
            out.append((f"{tool}:{m.group(1)}", "gcc", f"{tool}-version", m.group(0)))
    return out


# ── J: JVM family ─────────────────────────────────────────────────────
def scan_jvm_family():
    out = []
    if shutil.which("javac"):
        out.append(("jvm-hotspot", "jvm", "javac", "javac"))
        out.append(("jvm-classfile", "jvm", "javac", "class file format"))
    if shutil.which("kotlinc"):
        out.append(("jvm-kotlin", "jvm", "kotlinc", "kotlin → jvm"))
    if shutil.which("scalac"):
        out.append(("jvm-scala", "jvm", "scalac", "scala → jvm"))
    return out


# ── C: .NET family ────────────────────────────────────────────────────
def scan_dotnet_family():
    out = []
    if shutil.which("dotnet"):
        out.append(("cil", ".net", "dotnet", "CIL/IL"))
        out.append(("clr", ".net", "dotnet", "common language runtime"))
        out.append(("coreclr", ".net", "dotnet", "coreclr"))
        out.append(("mono", ".net", "dotnet", "mono runtime"))
    return out


# ── X: Apple SDKs ─────────────────────────────────────────────────────
def scan_apple():
    out = []
    if shutil.which("xcrun"):
        txt = run(["xcrun", "--show-sdk-version"])
        if txt.strip():
            out.append((f"apple-sdk-{txt.strip()}", "apple", "xcrun", txt.strip()))
        for sdk in (
            "macosx",
            "iphoneos",
            "iphonesimulator",
            "watchos",
            "watchsimulator",
            "appletvos",
            "appletvsimulator",
            "xros",
            "xrsimulator",
            "driverkit",
        ):
            t = run(["xcrun", "--sdk", sdk, "--show-sdk-path"])
            if t.strip():
                out.append((f"apple-sdk-{sdk}", "apple", "xcrun", t.strip()))
    return out


# ── S: Swift ──────────────────────────────────────────────────────────
def scan_swift():
    p = shutil.which("swift")
    if not p:
        return []
    txt = run([p, "--version"])
    out = []
    for m in re.finditer(r"Swift version ([0-9.]+)", txt):
        out.append((f"swift-{m.group(1)}", "swift", "swift-version", m.group(0)))
    return out


# ── P: Python interpreters ────────────────────────────────────────────
def scan_python():
    out = []
    for name in ("python3", "pypy3", "python3.11", "python3.12", "python3.13"):
        p = shutil.which(name)
        if not p:
            continue
        txt = run([p, "--version"])
        if not txt.strip():
            continue
        impl = "pypy" if "pypy" in name else "cpython"
        out.append((f"{impl}-{txt.strip().split()[-1]}", "python", name, txt.strip()))
    return out


# ── N: Node/JS engines ────────────────────────────────────────────────
def scan_js():
    out = []
    for name in ("node", "deno", "bun", "qjs", "d8"):
        p = shutil.which(name)
        if not p:
            continue
        txt = run([p, "--version"])
        if txt.strip():
            out.append((f"{name}-{txt.strip().split()[0]}", "js", name, txt.strip()))
    return out


# ── curated catalog loader ────────────────────────────────────────────
def load_curated_names() -> set:
    try:
        import isa_grammar

        return set(name for name, _, _ in isa_grammar.CURATED_SPECS)
    except Exception:
        return set()


# ── merge ─────────────────────────────────────────────────────────────
def build():
    curated = load_curated_names()
    all_src = {
        "llvm": scan_llvm(),
        "binutils": scan_binutils(),
        "qemu": scan_qemu(),
        "rust": scan_rust(),
        "go": scan_go(),
        "gcc": scan_gcc(),
        "jvm": scan_jvm_family(),
        "dotnet": scan_dotnet_family(),
        "apple": scan_apple(),
        "swift": scan_swift(),
        "python": scan_python(),
        "js": scan_js(),
    }
    # flatten and dedupe by isa_name, but keep track of which sources claim it
    by_name = {}
    for src, rows in all_src.items():
        for isa_name, family, tool, raw in rows:
            key = isa_name.lower()
            e = by_name.setdefault(
                key,
                {
                    "isa": isa_name,
                    "family": family,
                    "sources": [],
                    "raw": [],
                },
            )
            e["sources"].append(f"{src}/{tool}")
            e["raw"].append(raw)
    # classify against curated
    for key, e in by_name.items():
        e["curated"] = key in curated
    non_curated = [e for e in by_name.values() if not e["curated"]]
    curated_seen = [e for e in by_name.values() if e["curated"]]
    return {
        "sources": {k: len(v) for k, v in all_src.items()},
        "total_discovered": len(by_name),
        "curated_matched": len(curated_seen),
        "non_curated": non_curated,
        "curated": curated_seen,
    }


def main():
    result = build()
    out = HERE / "noncurated.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"sources scanned:  {len(result['sources'])}")
    for s, n in result["sources"].items():
        print(f"  {s:10s} {n:5d}")
    print()
    print(f"total discovered: {result['total_discovered']}")
    print(f"curated match:    {result['curated_matched']}")
    print(f"non-curated:      {len(result['non_curated'])}")
    print()
    print("== non-curated ISAs / targets ==")
    for e in sorted(result["non_curated"], key=lambda x: x["isa"].lower()):
        print(f"  {e['isa']:40s} [{e['family']}]  srcs={len(e['sources'])}")
    print()
    print(f"wrote: {out}")


if __name__ == "__main__":
    main()
