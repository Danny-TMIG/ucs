#!/usr/bin/env python3
"""run.py — compile a source expression all the way to an executable.

Pipeline:
    source text
      -> comp.py   (lex/parse -> stack IR)
      -> trans.py  (IR -> x86-64 asm skeleton)
      -> clang     (asm -> executable)
      -> run       (executable, print exit code)

The asm is stack-based and incomplete (it prints via a runtime helper we
provide). To make it self-contained we emit a small C runtime alongside
the asm and link both together.
"""

from __future__ import annotations
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
COMP = HERE.parent / "comp" / "comp.py"
TRANS = HERE.parent / "trans" / "trans.py"
RUNTIME_C = HERE / "runtime.c"
ASM_S = HERE / "prog.s"
EXE = HERE / "prog"

RUNTIME_C.write_text(r"""
#include <stdio.h>
void print_int(long x) { printf("%ld\n", x); }
""")


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def compile_source(src: str) -> list:
    r = sh([sys.executable, str(COMP)])
    # comp.py has no CLI; import it instead
    import importlib.util

    spec = importlib.util.spec_from_file_location("comp", COMP)
    comp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(comp)
    return comp.compile_source(src)


def translate(ir: list) -> str:
    import importlib.util

    spec = importlib.util.spec_from_file_location("trans", TRANS)
    trans = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trans)
    return trans.translate(ir)


def assemble_and_link(asm_text: str) -> bool:
    ASM_S.write_text(asm_text)
    # assemble
    r = sh(["clang", "-arch", "x86_64", "-c", str(ASM_S), "-o", str(HERE / "prog.o")])
    if r.returncode != 0:
        print("assemble failed:", r.stderr[:300])
        return False
    # compile runtime
    r = sh(
        [
            "clang",
            "-arch",
            "x86_64",
            "-c",
            str(RUNTIME_C),
            "-o",
            str(HERE / "runtime.o"),
        ]
    )
    if r.returncode != 0:
        print("runtime compile failed:", r.stderr[:300])
        return False
    # link
    r = sh(
        [
            "clang",
            "-arch",
            "x86_64",
            str(HERE / "prog.o"),
            str(HERE / "runtime.o"),
            "-o",
            str(EXE),
            "-nostartfiles",
            "-Wl,-e,_start",
        ]
    )
    if r.returncode != 0:
        print("link failed:", r.stderr[:300])
        return False
    return True


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "((3+4)*5) - 7"
    print(f"source: {src}")
    ir = compile_source(src)
    print(f"IR:     {ir}")
    asm = translate(ir)
    print("ASM:")
    for line in asm.splitlines():
        print(f"  {line}")
    if assemble_and_link(asm):
        print(f"binary: {EXE}")
        r = sh([str(EXE)])
        print(f"exit:   {r.returncode}")
        if r.stdout:
            print(f"stdout: {r.stdout.strip()}")
    else:
        print("(asm is a stack skeleton; full encode not attempted)")


if __name__ == "__main__":
    main()
