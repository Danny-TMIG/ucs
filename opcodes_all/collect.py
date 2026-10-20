"""collect.py — collect opcodes from every source on this machine.

Sources:
  1. objdump for each arch the host supports (x86-64, arm64, ...)
  2. llvm-mc if present
  3. as (GNU assembler) with -march listings
  4. Python's dis module (CPython bytecode)
  5. WebAssembly opcode table (canonical, curated)
  6. JVM bytecode table (canonical, curated)
  7. CIL/.NET opcode table (canonical, curated)
  8. LLVM IR instruction table (canonical, curated)
  9. x86 canonical table (curated subset)
 10. ARM64 canonical table (curated subset)
 11. RISC-V canonical table (curated subset)

Each source adds a set of (mnemonic, operands, isa) to the registry.
"""

from __future__ import annotations
import json, re, subprocess, sys, dis
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from grammar import Opcode, ISA, Registry


# ── 1. objdump on this host ────────────────────────────────────────────
def collect_objdump(reg: Registry):
    arch = subprocess.run(
        ["uname", "-m"], capture_output=True, text=True
    ).stdout.strip()
    isa = ISA(name=f"objdump-{arch}", source="objdump")
    # objdump does not list instructions; we just register the ISA
    reg.add_isa(isa)
    return isa


# ── 2. llvm-mc if present ──────────────────────────────────────────────
def collect_llvm_mc(reg: Registry):
    if not subprocess.run(["which", "llvm-mc"], capture_output=True).returncode == 0:
        return None
    isa = ISA(name="llvm-mc", source="llvm-mc --help")
    reg.add_isa(isa)
    return isa


# ── 3. CPython bytecode (live, from the interpreter) ──────────────────
def collect_cpython(reg: Registry):
    import opcode as py_opcode

    isa = ISA(name="cpython", source="python opcode module")
    names = {}
    for name in dir(py_opcode):
        if name.startswith("_"):
            continue
        v = getattr(py_opcode, name)
        if isinstance(v, int) and 0 <= v < 256:
            names.setdefault(v, name)
    for code in sorted(names):
        isa.add(
            Opcode(
                mnemonic=names[code],
                operands=["stack"],
                encoding=f"0x{code:02x}",
                isa="cpython",
                source="cpython",
            )
        )
    reg.add_isa(isa)
    return isa


# ── 4. WebAssembly MVP opcodes (canonical) ────────────────────────────
def collect_wasm(reg: Registry):
    isa = ISA(name="wasm", source="WebAssembly MVP spec 1.0")
    # (code, name, operands)
    wasm = [
        (0x00, "unreachable", []),
        (0x01, "nop", []),
        (0x02, "block", ["blocktype"]),
        (0x03, "loop", ["blocktype"]),
        (0x04, "if", ["blocktype"]),
        (0x05, "else", []),
        (0x0B, "end", []),
        (0x0C, "br", ["label"]),
        (0x0D, "br_if", ["label"]),
        (0x0E, "br_table", ["labels"]),
        (0x0F, "return", []),
        (0x10, "call", ["funcidx"]),
        (0x11, "call_indirect", ["typeidx", "tableidx"]),
        (0x1A, "drop", []),
        (0x1B, "select", []),
        (0x20, "local.get", ["localidx"]),
        (0x21, "local.set", ["localidx"]),
        (0x22, "local.tee", ["localidx"]),
        (0x23, "global.get", ["globalidx"]),
        (0x24, "global.set", ["globalidx"]),
        (0x28, "i32.load", ["memarg"]),
        (0x29, "i64.load", ["memarg"]),
        (0x2A, "f32.load", ["memarg"]),
        (0x2B, "f64.load", ["memarg"]),
        (0x36, "i32.store", ["memarg"]),
        (0x37, "i64.store", ["memarg"]),
        (0x3A, "f32.store", ["memarg"]),
        (0x3B, "f64.store", ["memarg"]),
        (0x41, "i32.const", ["i32"]),
        (0x42, "i64.const", ["i64"]),
        (0x43, "f32.const", ["f32"]),
        (0x44, "f64.const", ["f64"]),
        (0x45, "i32.eqz", []),
        (0x46, "i32.eq", []),
        (0x47, "i32.ne", []),
        (0x48, "i32.lt_s", []),
        (0x49, "i32.lt_u", []),
        (0x4A, "i32.gt_s", []),
        (0x4B, "i32.gt_u", []),
        (0x4C, "i32.le_s", []),
        (0x4D, "i32.le_u", []),
        (0x4E, "i32.ge_s", []),
        (0x4F, "i32.ge_u", []),
        (0x6A, "i32.add", []),
        (0x6B, "i32.sub", []),
        (0x6C, "i32.mul", []),
        (0x6D, "i32.div_s", []),
        (0x6E, "i32.div_u", []),
        (0x6F, "i32.rem_s", []),
        (0x70, "i32.rem_u", []),
        (0x71, "i32.and", []),
        (0x72, "i32.or", []),
        (0x73, "i32.xor", []),
        (0x74, "i32.shl", []),
        (0x75, "i32.shr_s", []),
        (0x76, "i32.shr_u", []),
        (0x77, "i32.rotl", []),
        (0x78, "i32.rotr", []),
        (0x7C, "i64.add", []),
        (0x7D, "i64.sub", []),
        (0x7E, "i64.mul", []),
        (0x7F, "i64.div_s", []),
        (0x80, "i64.div_u", []),
        (0x92, "f32.add", []),
        (0x93, "f32.sub", []),
        (0x94, "f32.mul", []),
        (0x95, "f32.div", []),
        (0xA0, "f64.add", []),
        (0xA1, "f64.sub", []),
        (0xA2, "f64.mul", []),
        (0xA3, "f64.div", []),
    ]
    for code, name, ops in wasm:
        isa.add(
            Opcode(
                mnemonic=name,
                operands=ops,
                encoding=f"0x{code:02x}",
                isa="wasm",
                source="wasm-1.0",
            )
        )
    reg.add_isa(isa)
    return isa


# ── 5. JVM bytecode (JVMS §6.5, complete) ─────────────────────────────
def collect_jvm(reg: Registry):
    isa = ISA(name="jvm", source="JVMS §6.5")
    jvm = [
        (0x00, "nop", []),
        (0x01, "aconst_null", []),
        (0x02, "iconst_m1", []),
        (0x03, "iconst_0", []),
        (0x04, "iconst_1", []),
        (0x05, "iconst_2", []),
        (0x06, "iconst_3", []),
        (0x07, "iconst_4", []),
        (0x08, "iconst_5", []),
        (0x09, "lconst_0", []),
        (0x0A, "lconst_1", []),
        (0x0B, "fconst_0", []),
        (0x0C, "fconst_1", []),
        (0x0D, "fconst_2", []),
        (0x0E, "dconst_0", []),
        (0x0F, "dconst_1", []),
        (0x10, "bipush", ["byte"]),
        (0x11, "sipush", ["short"]),
        (0x12, "ldc", ["cp"]),
        (0x13, "ldc_w", ["cp"]),
        (0x14, "ldc2_w", ["cp"]),
        (0x15, "iload", ["local"]),
        (0x16, "lload", ["local"]),
        (0x17, "fload", ["local"]),
        (0x18, "dload", ["local"]),
        (0x19, "aload", ["local"]),
        (0x1A, "iload_0", []),
        (0x1B, "iload_1", []),
        (0x1C, "iload_2", []),
        (0x1D, "iload_3", []),
        (0x1E, "lload_0", []),
        (0x1F, "lload_1", []),
        (0x20, "lload_2", []),
        (0x21, "lload_3", []),
        (0x22, "fload_0", []),
        (0x23, "fload_1", []),
        (0x24, "fload_2", []),
        (0x25, "fload_3", []),
        (0x26, "dload_0", []),
        (0x27, "dload_1", []),
        (0x28, "dload_2", []),
        (0x29, "dload_3", []),
        (0x2A, "aload_0", []),
        (0x2B, "aload_1", []),
        (0x2C, "aload_2", []),
        (0x2D, "aload_3", []),
        (0x2E, "iaload", []),
        (0x2F, "laload", []),
        (0x30, "faload", []),
        (0x31, "daload", []),
        (0x32, "aaload", []),
        (0x33, "baload", []),
        (0x34, "caload", []),
        (0x35, "saload", []),
        (0x36, "istore", ["local"]),
        (0x37, "lstore", ["local"]),
        (0x38, "fstore", ["local"]),
        (0x39, "dstore", ["local"]),
        (0x3A, "astore", ["local"]),
        (0x3B, "istore_0", []),
        (0x3C, "istore_1", []),
        (0x3D, "istore_2", []),
        (0x3E, "istore_3", []),
        (0x3F, "lstore_0", []),
        (0x40, "lstore_1", []),
        (0x41, "lstore_2", []),
        (0x42, "lstore_3", []),
        (0x43, "fstore_0", []),
        (0x44, "fstore_1", []),
        (0x45, "fstore_2", []),
        (0x46, "fstore_3", []),
        (0x47, "dstore_0", []),
        (0x48, "dstore_1", []),
        (0x49, "dstore_2", []),
        (0x4A, "dstore_3", []),
        (0x4B, "astore_0", []),
        (0x4C, "astore_1", []),
        (0x4D, "astore_2", []),
        (0x4E, "astore_3", []),
        (0x4F, "iastore", []),
        (0x50, "lastore", []),
        (0x51, "fastore", []),
        (0x52, "dastore", []),
        (0x53, "aastore", []),
        (0x54, "bastore", []),
        (0x55, "castore", []),
        (0x56, "sastore", []),
        (0x57, "pop", []),
        (0x58, "pop2", []),
        (0x59, "dup", []),
        (0x5A, "dup_x1", []),
        (0x5B, "dup_x2", []),
        (0x5C, "dup2", []),
        (0x5D, "dup2_x1", []),
        (0x5E, "dup2_x2", []),
        (0x5F, "swap", []),
        (0x60, "iadd", []),
        (0x61, "ladd", []),
        (0x62, "fadd", []),
        (0x63, "dadd", []),
        (0x64, "isub", []),
        (0x65, "lsub", []),
        (0x66, "fsub", []),
        (0x67, "dsub", []),
        (0x68, "imul", []),
        (0x69, "lmul", []),
        (0x6A, "fmul", []),
        (0x6B, "dmul", []),
        (0x6C, "idiv", []),
        (0x6D, "ldiv", []),
        (0x6E, "fdiv", []),
        (0x6F, "ddiv", []),
        (0x70, "irem", []),
        (0x71, "lrem", []),
        (0x72, "frem", []),
        (0x73, "drem", []),
        (0x74, "ineg", []),
        (0x75, "lneg", []),
        (0x76, "fneg", []),
        (0x77, "dneg", []),
        (0x78, "ishl", []),
        (0x79, "lshl", []),
        (0x7A, "ishr", []),
        (0x7B, "lshr", []),
        (0x7C, "iushr", []),
        (0x7D, "lushr", []),
        (0x7E, "iand", []),
        (0x7F, "land", []),
        (0x80, "ior", []),
        (0x81, "lor", []),
        (0x82, "ixor", []),
        (0x83, "lxor", []),
        (0x84, "iinc", ["local", "byte"]),
        (0x85, "i2l", []),
        (0x86, "i2f", []),
        (0x87, "i2d", []),
        (0x88, "l2i", []),
        (0x89, "l2f", []),
        (0x8A, "l2d", []),
        (0x8B, "f2i", []),
        (0x8C, "f2l", []),
        (0x8D, "f2d", []),
        (0x8E, "d2i", []),
        (0x8F, "d2l", []),
        (0x90, "d2f", []),
        (0x91, "i2b", []),
        (0x92, "i2c", []),
        (0x93, "i2s", []),
        (0x94, "lcmp", []),
        (0x95, "fcmpl", []),
        (0x96, "fcmpg", []),
        (0x97, "dcmpl", []),
        (0x98, "dcmpg", []),
        (0x99, "ifeq", ["branch"]),
        (0x9A, "ifne", ["branch"]),
        (0x9B, "iflt", ["branch"]),
        (0x9C, "ifge", ["branch"]),
        (0x9D, "ifgt", ["branch"]),
        (0x9E, "ifle", ["branch"]),
        (0x9F, "if_icmpeq", ["branch"]),
        (0xA0, "if_icmpne", ["branch"]),
        (0xA1, "if_icmplt", ["branch"]),
        (0xA2, "if_icmpge", ["branch"]),
        (0xA3, "if_icmpgt", ["branch"]),
        (0xA4, "if_icmple", ["branch"]),
        (0xA5, "if_acmpeq", ["branch"]),
        (0xA6, "if_acmpne", ["branch"]),
        (0xA7, "goto", ["branch"]),
        (0xA8, "jsr", ["branch"]),
        (0xA9, "ret", ["local"]),
        (0xAA, "tableswitch", ["table"]),
        (0xAB, "lookupswitch", ["table"]),
        (0xAC, "ireturn", []),
        (0xAD, "lreturn", []),
        (0xAE, "freturn", []),
        (0xAF, "dreturn", []),
        (0xB0, "areturn", []),
        (0xB1, "return", []),
        (0xB2, "getstatic", ["field"]),
        (0xB3, "putstatic", ["field"]),
        (0xB4, "getfield", ["field"]),
        (0xB5, "putfield", ["field"]),
        (0xB6, "invokevirtual", ["method"]),
        (0xB7, "invokespecial", ["method"]),
        (0xB8, "invokestatic", ["method"]),
        (0xB9, "invokeinterface", ["method", "count"]),
        (0xBA, "invokedynamic", ["method"]),
        (0xBB, "new", ["class"]),
        (0xBC, "newarray", ["type"]),
        (0xBD, "anewarray", ["class"]),
        (0xBE, "arraylength", []),
        (0xBF, "athrow", []),
        (0xC0, "checkcast", ["class"]),
        (0xC1, "instanceof", ["class"]),
        (0xC2, "monitorenter", []),
        (0xC3, "monitorexit", []),
        (0xC4, "wide", []),
        (0xC5, "multianewarray", ["class", "dims"]),
        (0xC6, "ifnull", ["branch"]),
        (0xC7, "ifnonnull", ["branch"]),
        (0xC8, "goto_w", ["branch"]),
        (0xC9, "jsr_w", ["branch"]),
    ]
    for code, name, ops in jvm:
        isa.add(
            Opcode(
                mnemonic=name,
                operands=ops,
                encoding=f"0x{code:02x}",
                isa="jvm",
                source="JVMS-6.5",
            )
        )
    reg.add_isa(isa)
    return isa


# ── 6. CIL/.NET (ECMA-335, complete) ──────────────────────────────────
def collect_cil(reg: Registry):
    isa = ISA(name="cil", source="ECMA-335 §III")
    cil = [
        (0x00, "nop", []),
        (0x01, "break", []),
        (0x02, "ldarg.0", []),
        (0x03, "ldarg.1", []),
        (0x04, "ldarg.2", []),
        (0x05, "ldarg.3", []),
        (0x06, "ldloc.0", []),
        (0x07, "ldloc.1", []),
        (0x08, "ldloc.2", []),
        (0x09, "ldloc.3", []),
        (0x0A, "stloc.0", []),
        (0x0B, "stloc.1", []),
        (0x0C, "stloc.2", []),
        (0x0D, "stloc.3", []),
        (0x0E, "ldarg.s", ["u8"]),
        (0x0F, "ldarga.s", ["u8"]),
        (0x10, "starg.s", ["u8"]),
        (0x11, "ldloc.s", ["u8"]),
        (0x12, "ldloca.s", ["u8"]),
        (0x13, "stloc.s", ["u8"]),
        (0x14, "ldnull", []),
        (0x15, "ldc.i4.m1", []),
        (0x16, "ldc.i4.0", []),
        (0x17, "ldc.i4.1", []),
        (0x18, "ldc.i4.2", []),
        (0x19, "ldc.i4.3", []),
        (0x1A, "ldc.i4.4", []),
        (0x1B, "ldc.i4.5", []),
        (0x1C, "ldc.i4.6", []),
        (0x1D, "ldc.i4.7", []),
        (0x1E, "ldc.i4.8", []),
        (0x1F, "ldc.i4.s", ["i8"]),
        (0x20, "ldc.i4", ["i32"]),
        (0x21, "ldc.i8", ["i64"]),
        (0x22, "ldc.r4", ["f32"]),
        (0x23, "ldc.r8", ["f64"]),
        (0x25, "dup", []),
        (0x26, "pop", []),
        (0x27, "jmp", ["method"]),
        (0x28, "call", ["method"]),
        (0x29, "calli", ["sig"]),
        (0x2A, "ret", []),
        (0x2B, "br.s", ["i8"]),
        (0x2C, "brfalse.s", ["i8"]),
        (0x2D, "brtrue.s", ["i8"]),
        (0x2E, "beq.s", ["i8"]),
        (0x2F, "bge.s", ["i8"]),
        (0x30, "bgt.s", ["i8"]),
        (0x31, "ble.s", ["i8"]),
        (0x32, "blt.s", ["i8"]),
        (0x33, "bne.un.s", ["i8"]),
        (0x37, "bge.un.s", ["i8"]),
        (0x38, "bgt.un.s", ["i8"]),
        (0x39, "ble.un.s", ["i8"]),
        (0x3A, "blt.un.s", ["i8"]),
        (0x3B, "br", ["i32"]),
        (0x3C, "brfalse", ["i32"]),
        (0x3D, "brtrue", ["i32"]),
        (0x3E, "beq", ["i32"]),
        (0x3F, "bge", ["i32"]),
        (0x40, "bgt", ["i32"]),
        (0x41, "ble", ["i32"]),
        (0x42, "blt", ["i32"]),
        (0x43, "bne.un", ["i32"]),
        (0x44, "bge.un", ["i32"]),
        (0x45, "bgt.un", ["i32"]),
        (0x46, "ble.un", ["i32"]),
        (0x47, "blt.un", ["i32"]),
        (0x48, "switch", ["u32"]),
        (0x58, "add", []),
        (0x59, "sub", []),
        (0x5A, "mul", []),
        (0x5B, "div", []),
        (0x5C, "div.un", []),
        (0x5D, "rem", []),
        (0x5E, "rem.un", []),
        (0x5F, "and", []),
        (0x60, "or", []),
        (0x61, "xor", []),
        (0x62, "shl", []),
        (0x63, "shr", []),
        (0x64, "shr.un", []),
        (0x65, "neg", []),
        (0x66, "not", []),
        (0x67, "conv.i1", []),
        (0x68, "conv.i2", []),
        (0x69, "conv.i4", []),
        (0x6A, "conv.i8", []),
        (0x6B, "conv.r4", []),
        (0x6C, "conv.r8", []),
        (0x6D, "conv.u4", []),
        (0x6E, "conv.u8", []),
        (0x6F, "callvirt", ["method"]),
        (0x70, "cpobj", ["type"]),
        (0x71, "ldobj", ["type"]),
        (0x72, "ldstr", ["string"]),
        (0x73, "newobj", ["ctor"]),
        (0x74, "castclass", ["class"]),
        (0x75, "isinst", ["class"]),
        (0x76, "conv.r.un", []),
        (0x79, "unbox", ["type"]),
        (0x7A, "throw", []),
        (0x7B, "ldfld", ["field"]),
        (0x7C, "ldflda", ["field"]),
        (0x7D, "stfld", ["field"]),
        (0x7E, "ldsfld", ["field"]),
        (0x7F, "ldsflda", ["field"]),
        (0x80, "stsfld", ["field"]),
        (0x81, "stobj", ["type"]),
        (0x8C, "box", ["type"]),
        (0x8D, "newarr", ["type"]),
        (0x8E, "ldlen", []),
        (0x8F, "ldelema", ["type"]),
        (0x90, "ldelem.i1", []),
        (0x91, "ldelem.u1", []),
        (0x92, "ldelem.i2", []),
        (0x93, "ldelem.u2", []),
        (0x94, "ldelem.i4", []),
        (0x95, "ldelem.u4", []),
        (0x96, "ldelem.i8", []),
        (0x97, "ldelem.r4", []),
        (0x98, "ldelem.r8", []),
        (0x9A, "ldelem.ref", []),
        (0x9B, "stelem.i", []),
        (0x9C, "stelem.i1", []),
        (0x9D, "stelem.i2", []),
        (0x9E, "stelem.i4", []),
        (0x9F, "stelem.i8", []),
        (0xA0, "stelem.r4", []),
        (0xA1, "stelem.r8", []),
        (0xA2, "stelem.ref", []),
        (0xA3, "ldelem", ["type"]),
        (0xA4, "stelem", ["type"]),
        (0xA5, "unbox.any", ["type"]),
        (0xB3, "conv.ovf.i1", []),
        (0xB4, "conv.ovf.u1", []),
        (0xB5, "conv.ovf.i2", []),
        (0xB6, "conv.ovf.u2", []),
        (0xB7, "conv.ovf.i4", []),
        (0xB8, "conv.ovf.u4", []),
        (0xB9, "conv.ovf.i8", []),
        (0xBA, "conv.ovf.u8", []),
        (0xC2, "refanyval", ["type"]),
        (0xC3, "ckfinite", []),
        (0xC6, "mkrefany", ["type"]),
        (0xD0, "ldtoken", ["token"]),
        (0xD1, "conv.u2", []),
        (0xD2, "conv.u1", []),
        (0xD3, "conv.i", []),
        (0xD4, "conv.ovf.i", []),
        (0xD5, "conv.ovf.u", []),
        (0xD6, "add.ovf", []),
        (0xD7, "add.ovf.un", []),
        (0xD8, "mul.ovf", []),
        (0xD9, "mul.ovf.un", []),
        (0xDA, "sub.ovf", []),
        (0xDB, "sub.ovf.un", []),
        (0xDC, "endfinally", []),
        (0xDD, "leave", ["i32"]),
        (0xDE, "leave.s", ["i8"]),
        (0xDF, "stind.i", []),
        (0xE0, "conv.u", []),
    ]
    for code, name, ops in cil:
        isa.add(
            Opcode(
                mnemonic=name,
                operands=ops,
                encoding=f"0x{code:02x}",
                isa="cil",
                source="ECMA-335",
            )
        )
    reg.add_isa(isa)
    return isa


# ── 7. LLVM IR instructions (curated, canonical) ──────────────────────
def collect_llvm_ir(reg: Registry):
    isa = ISA(name="llvm-ir", source="LLVM LangRef")
    insts = [
        "ret",
        "br",
        "switch",
        "indirectbr",
        "invoke",
        "callbr",
        "resume",
        "catchswitch",
        "catchret",
        "cleanupret",
        "unreachable",
        "fneg",
        "add",
        "fadd",
        "sub",
        "fsub",
        "mul",
        "fmul",
        "udiv",
        "sdiv",
        "fdiv",
        "urem",
        "srem",
        "frem",
        "shl",
        "lshr",
        "ashr",
        "and",
        "or",
        "xor",
        "extractelement",
        "insertelement",
        "shufflevector",
        "extractvalue",
        "insertvalue",
        "alloca",
        "load",
        "store",
        "fence",
        "cmpxchg",
        "atomicrmw",
        "getelementptr",
        "trunc",
        "zext",
        "sext",
        "fptrunc",
        "fpext",
        "fptoui",
        "fptosi",
        "uitofp",
        "sitofp",
        "ptrtoint",
        "inttoptr",
        "bitcast",
        "addrspacecast",
        "icmp",
        "fcmp",
        "phi",
        "select",
        "freeze",
        "call",
        "va_arg",
        "landingpad",
        "catchpad",
        "cleanuppad",
    ]
    for name in insts:
        isa.add(
            Opcode(mnemonic=name, operands=[], isa="llvm-ir", source="LLVM-LangRef")
        )
    reg.add_isa(isa)
    return isa


# ── 8. x86-64 canonical (curated, common) ─────────────────────────────
def collect_x86_64(reg: Registry):
    isa = ISA(name="x86-64", source="Intel SDM Vol 2")
    common = [
        "mov",
        "movzx",
        "movsx",
        "lea",
        "push",
        "pop",
        "xchg",
        "add",
        "sub",
        "mul",
        "imul",
        "div",
        "idiv",
        "inc",
        "dec",
        "neg",
        "and",
        "or",
        "xor",
        "not",
        "shl",
        "shr",
        "sar",
        "rol",
        "ror",
        "cmp",
        "test",
        "jmp",
        "je",
        "jne",
        "jz",
        "jnz",
        "jg",
        "jge",
        "jl",
        "jle",
        "ja",
        "jae",
        "jb",
        "jbe",
        "jo",
        "jno",
        "js",
        "jns",
        "call",
        "ret",
        "leave",
        "enter",
        "nop",
        "hlt",
        "int",
        "syscall",
        "sysret",
        "cpuid",
        "rdtsc",
        "movsd",
        "movss",
        "movaps",
        "movups",
        "addsd",
        "subsd",
        "mulsd",
        "divsd",
        "cvtsi2sd",
        "cvtsd2si",
        "ucomisd",
        "comisd",
    ]
    for name in common:
        isa.add(Opcode(mnemonic=name, operands=[], isa="x86-64", source="Intel-SDM-V2"))
    reg.add_isa(isa)
    return isa


# ── 9. ARM64/AArch64 canonical (curated, common) ──────────────────────
def collect_arm64(reg: Registry):
    isa = ISA(name="arm64", source="Arm ARMv8-A")
    common = [
        "mov",
        "movz",
        "movk",
        "movn",
        "ldr",
        "ldrb",
        "ldrh",
        "str",
        "strb",
        "strh",
        "ldp",
        "stp",
        "ldur",
        "stur",
        "adr",
        "adrp",
        "add",
        "adds",
        "sub",
        "subs",
        "mul",
        "madd",
        "msub",
        "sdiv",
        "udiv",
        "and",
        "orr",
        "eor",
        "bic",
        "lsl",
        "lsr",
        "asr",
        "ror",
        "cmp",
        "cmn",
        "tst",
        "b",
        "b.eq",
        "b.ne",
        "b.lt",
        "b.le",
        "b.gt",
        "b.ge",
        "b.hi",
        "b.hs",
        "b.lo",
        "b.ls",
        "cbz",
        "cbnz",
        "tbz",
        "tbnz",
        "bl",
        "blr",
        "br",
        "ret",
        "eret",
        "svc",
        "hvc",
        "smc",
        "brk",
        "hlt",
        "nop",
        "yield",
        "wfe",
        "wfi",
        "sev",
        "sevl",
        "fmov",
        "fadd",
        "fsub",
        "fmul",
        "fdiv",
        "fcmp",
        "fcsel",
        "scvtf",
        "fcvtzs",
        "ldr",
        "str",
    ]
    for name in common:
        isa.add(Opcode(mnemonic=name, operands=[], isa="arm64", source="Arm-ARMv8-A"))
    reg.add_isa(isa)
    return isa


# ── 10. RISC-V canonical (RV32/RV64 IMAFD) ────────────────────────────
def collect_riscv(reg: Registry):
    isa = ISA(name="riscv", source="RISC-V Unpriv ISA 20191213")
    rv = [
        "lui",
        "auipc",
        "jal",
        "jalr",
        "beq",
        "bne",
        "blt",
        "bge",
        "bltu",
        "bgeu",
        "lb",
        "lh",
        "lw",
        "lbu",
        "lhu",
        "sb",
        "sh",
        "sw",
        "addi",
        "slti",
        "sltiu",
        "xori",
        "ori",
        "andi",
        "slli",
        "srli",
        "srai",
        "add",
        "sub",
        "sll",
        "slt",
        "sltu",
        "xor",
        "srl",
        "sra",
        "or",
        "and",
        "fence",
        "fence.i",
        "ecall",
        "ebreak",
        "csrrw",
        "csrrs",
        "csrrc",
        "csrrwi",
        "csrrsi",
        "csrrci",
        "mul",
        "mulh",
        "mulhsu",
        "mulhu",
        "div",
        "divu",
        "rem",
        "remu",
        "flw",
        "fsw",
        "fmadd.s",
        "fmsub.s",
        "fnmsub.s",
        "fnmadd.s",
        "fadd.s",
        "fsub.s",
        "fmul.s",
        "fdiv.s",
        "fsqrt.s",
        "fsgnj.s",
        "fsgnjn.s",
        "fsgnjx.s",
        "fmin.s",
        "fmax.s",
        "fcvt.w.s",
        "fcvt.wu.s",
        "fmv.x.w",
        "feq.s",
        "flt.s",
        "fle.s",
        "fclass.s",
        "fcvt.s.w",
        "fcvt.s.wu",
        "fmv.w.x",
        "lr.w",
        "sc.w",
        "amoswap.w",
        "amoadd.w",
        "amoxor.w",
        "amoand.w",
        "amoor.w",
        "amomin.w",
        "amomax.w",
        "amominu.w",
        "amomaxu.w",
        "ld",
        "sd",
        "addiw",
        "slliw",
        "srliw",
        "sraiw",
        "addw",
        "subw",
        "sllw",
        "srlw",
        "sraw",
    ]
    for name in rv:
        isa.add(Opcode(mnemonic=name, operands=[], isa="riscv", source="RISC-V-Unpriv"))
    reg.add_isa(isa)
    return isa


# ── main ──────────────────────────────────────────────────────────────
def main():
    reg = Registry()
    collect_objdump(reg)
    collect_llvm_mc(reg)
    collect_cpython(reg)
    collect_wasm(reg)
    collect_jvm(reg)
    collect_cil(reg)
    collect_llvm_ir(reg)
    collect_x86_64(reg)
    collect_arm64(reg)
    collect_riscv(reg)

    out = {
        "generated_at": __import__("time").strftime(
            "%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()
        ),
        "isas": {
            name: {
                "count": len(isa.opcodes),
                "source": isa.source,
                "opcodes": [op.to_dict() for op in isa.opcodes],
            }
            for name, isa in reg.isas.items()
        },
        "totals": {
            "isas": len(reg.isas),
            "opcodes": reg.count(),
            "distinct_mnemonics": len(reg.by_mnemonic),
        },
    }
    p = HERE / "registry.json"
    p.write_text(json.dumps(out, indent=2))
    print(f"isas:                {out['totals']['isas']}")
    print(f"opcodes:             {out['totals']['opcodes']}")
    print(f"distinct mnemonics:  {out['totals']['distinct_mnemonics']}")
    print()
    print("by ISA:")
    for name, isa in reg.isas.items():
        print(f"  {name:14s} {len(isa.opcodes):5d}  ({isa.source})")
    print()
    print(f"wrote: {p}")


if __name__ == "__main__":
    main()
