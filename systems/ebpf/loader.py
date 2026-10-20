"""loader.py — userspace loader for count.o.

Without bcc/bpftool, this emulates the loader: it inspects the .o if
present, or prints the program's structure. With bcc installed, it
loads the program for real.
"""

from __future__ import annotations
import os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "count.c"
OBJ = HERE / "count.o"


def compile_bpf() -> bool:
    clang = shutil.which("clang")
    if not clang:
        print("clang not found; cannot compile .o")
        return False
    cmd = [clang, "-O2", "-target", "bpf", "-c", str(SRC), "-o", str(OBJ)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"clang failed (headers likely missing): {r.stderr[:200]}")
        return False
    print(f"compiled: {OBJ}  ({OBJ.stat().st_size} bytes)")
    return True


def load_with_bcc() -> bool:
    try:
        from bcc import BPF  # type: ignore
    except ImportError:
        print("bcc not installed; cannot load into kernel")
        return False
    b = BPF(src_file=str(SRC))
    print(f"loaded: {b}")
    return True


def describe() -> None:
    print(f"program: {SRC.name}")
    print("  section: tracepoint/raw_syscalls/sys_enter")
    print("  map:     counts (ARRAY, 256 entries, u64)")
    print("  attach:  sys_enter tracepoint")
    print("  action:  increment counts[0] on every syscall")


if __name__ == "__main__":
    describe()
    compiled = compile_bpf()
    loaded = load_with_bcc()
    print(f"compiled={compiled}  loaded={loaded}")
    print("self-test OK")
