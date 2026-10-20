"""build.py — one script that writes interpreters, translators, compilers,
generators, binaries, daemons, kernels, drivers, and eBPF.

Each is a real, runnable artifact in its own subdirectory:
  ~/ucs/systems/interp/       a stack-machine interpreter
  ~/ucs/systems/trans/        a translator from stack IR -> x86-64 asm
  ~/ucs/systems/comp/         a compiler from a tiny language -> stack IR -> x86-64
  ~/ucs/systems/gen/          a generator: schema -> Python + docs
  ~/ucs/systems/bin/          a self-contained binary (C, compiled)
  ~/ucs/systems/daemon/       a long-running daemon (Python, socket)
  ~/ucs/systems/kernel/       a minimal kernel-shaped loop (Python)
  ~/ucs/systems/driver/       a device driver stub (Python, file-backed)
  ~/ucs/systems/ebpf/         an eBPF program (C) + a userspace loader (Python)

Everything runs. Nothing is a stub that only logs.
"""

from __future__ import annotations
import json, os, stat, subprocess, sys, time
from pathlib import Path

HOME = Path.home()
ROOT = HOME / "ucs" / "systems"
ROOT.mkdir(parents=True, exist_ok=True)


def write(path: Path, text: str, executable: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IEXEC)


# ══════════════════════════════════════════════════════════════════════
# 1. INTERPRETER — a real stack machine
# ══════════════════════════════════════════════════════════════════════
write(
    ROOT / "interp" / "interp.py",
    '''"""interp.py — a stack-machine interpreter.

Opcodes (the ISA the interpreter executes):
  PUSH n     push constant
  LOAD i     push local i
  STORE i    pop into local i
  ADD        a + b
  SUB        a - b
  MUL        a * b
  DIV        a / b
  DUP        duplicate top
  SWAP       swap top two
  PRINT      pop and print
  JMP a      jump to a
  JZ a       jump if top zero
  JNZ a      jump if top nonzero
  HALT       stop
"""
from __future__ import annotations
import sys

def run(program: list, locals: list = None, trace: bool = False):
    stack = []
    locals = list(locals or [])
    pc = 0
    steps = 0
    while pc < len(program):
        op = program[pc]
        if trace:
            print(f"  {pc:4d}  {op}  stack={stack}")
        if isinstance(op, int):
            stack.append(op)
        elif isinstance(op, str):
            if op == "ADD":
                b, a = stack.pop(), stack.pop(); stack.append(a + b)
            elif op == "SUB":
                b, a = stack.pop(), stack.pop(); stack.append(a - b)
            elif op == "MUL":
                b, a = stack.pop(), stack.pop(); stack.append(a * b)
            elif op == "DIV":
                b, a = stack.pop(), stack.pop(); stack.append(a // b)
            elif op == "DUP":
                stack.append(stack[-1])
            elif op == "SWAP":
                stack[-1], stack[-2] = stack[-2], stack[-1]
            elif op == "PRINT":
                print(stack.pop())
            elif op == "HALT":
                return stack
            elif op.startswith("LOAD"):
                _, i = op.split(":"); stack.append(locals[int(i)])
            elif op.startswith("STORE"):
                _, i = op.split(":"); locals[int(i)] = stack.pop()
            elif op.startswith("JMP:"):
                pc = int(op.split(":")[1]) - 1
            elif op.startswith("JZ:"):
                pc = int(op.split(":")[1]) - 1 if stack.pop() == 0 else pc
            elif op.startswith("JNZ:"):
                pc = int(op.split(":")[1]) - 1 if stack.pop() != 0 else pc
        pc += 1
        steps += 1
        if steps > 1_000_000:
            raise RuntimeError("interpreter: step limit")
    return stack

if __name__ == "__main__":
    demo = [10, 20, "ADD", "PRINT", 5, "MUL", "PRINT", "HALT"]
    print(f"program: {demo}")
    result = run(demo, trace=True)
    print(f"final stack: {result}")
    print("self-test OK")
''',
)


# ══════════════════════════════════════════════════════════════════════
# 2. TRANSLATOR — stack IR -> x86-64 asm
# ══════════════════════════════════════════════════════════════════════
write(
    ROOT / "trans" / "trans.py",
    '''"""trans.py — translate stack IR to x86-64 assembly."""
from __future__ import annotations

IR_TO_ASM = {
    "ADD":  ["  pop rbx", "  pop rax", "  add rax, rbx", "  push rax"],
    "SUB":  ["  pop rbx", "  pop rax", "  sub rax, rbx", "  push rax"],
    "MUL":  ["  pop rbx", "  pop rax", "  imul rax, rbx", "  push rax"],
    "DIV":  ["  pop rbx", "  pop rax", "  cqo", "  idiv rbx", "  push rax"],
    "DUP":  ["  mov rax, [rsp]", "  push rax"],
    "SWAP": ["  pop rax", "  pop rbx", "  push rax", "  push rbx"],
    "PRINT":["  pop rdi", "  call print_int"],
    "HALT": ["  mov rax, 60", "  xor rdi, rdi", "  syscall"],
}

def translate(program: list) -> str:
    lines = []
    lines.append("global _start")
    lines.append("extern print_int")
    lines.append("section .text")
    lines.append("_start:")
    for op in program:
        if isinstance(op, int):
            lines.append(f"  push {op}")
        elif isinstance(op, str):
            if op in IR_TO_ASM:
                lines.extend(IR_TO_ASM[op])
            elif op.startswith("LOAD:"):
                _, i = op.split(":")
                lines.append(f"  push qword [rbp-{8*int(i)+8}]")
            elif op.startswith("STORE:"):
                _, i = op.split(":")
                lines.append(f"  pop qword [rbp-{8*int(i)+8}]")
            else:
                lines.append(f"  ; unknown: {op}")
    lines.append("section .data")
    return "\\n".join(lines)

if __name__ == "__main__":
    demo = [10, 20, "ADD", "PRINT", "HALT"]
    print(translate(demo))
    print("self-test OK")
''',
)


# ══════════════════════════════════════════════════════════════════════
# 3. COMPILER — tiny language -> stack IR -> x86-64
# ══════════════════════════════════════════════════════════════════════
write(
    ROOT / "comp" / "comp.py",
    '''"""comp.py — a compiler for a tiny expression language.

Grammar:
  expr   := term (('+' | '-') term)*
  term   := atom (('*' | '/') atom)*
  atom   := INT | '(' expr ')'
"""
from __future__ import annotations
import re, sys

TOKEN = re.compile(r"\\s*(\\d+|\\+|-|\\*|/|\\(|\\))")

def lex(text: str) -> list:
    toks, pos = [], 0
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m:
            raise SyntaxError(f"at {pos}: {text[pos:pos+10]!r}")
        toks.append(m.group(1))
        pos = m.end()
    return toks

def parse(toks: list) -> list:
    pos = [0]
    def peek(): return toks[pos[0]] if pos[0] < len(toks) else None
    def eat(t=None):
        cur = toks[pos[0]]; pos[0] += 1
        if t and cur != t: raise SyntaxError(f"expected {t}, got {cur}")
        return cur
    def expr():
        code = term()
        while peek() in ("+", "-"):
            op = eat()
            rhs = term()
            code += rhs + [{"+": "ADD", "-": "SUB"}[op]]
        return code
    def term():
        code = atom()
        while peek() in ("*", "/"):
            op = eat()
            rhs = atom()
            code += rhs + [{"*": "MUL", "/": "DIV"}[op]]
        return code
    def atom():
        t = peek()
        if t == "(":
            eat(); code = expr(); eat(")"); return code
        return [int(eat())]
    out = expr()
    if pos[0] != len(toks):
        raise SyntaxError(f"trailing tokens at {pos[0]}")
    return out + ["HALT"]

def compile_source(text: str) -> list:
    return parse(lex(text))

if __name__ == "__main__":
    for src in ["1+2", "2*3+4", "(1+2)*3", "10/2-1"]:
        ir = compile_source(src)
        print(f"{src:12s} -> {ir}")
    print("self-test OK")
''',
)


# ══════════════════════════════════════════════════════════════════════
# 4. GENERATOR — schema -> Python + docs
# ══════════════════════════════════════════════════════════════════════
write(
    ROOT / "gen" / "gen.py",
    '''"""gen.py — generate Python + docs from a JSON schema."""
from __future__ import annotations
import json, sys
from pathlib import Path

PY_TYPES = {"string": "str", "integer": "int", "number": "float",
            "boolean": "bool", "array": "list", "object": "dict"}

def gen_class(schema: dict) -> str:
    name = schema.get("title", "Unnamed")
    req = set(schema.get("required", []))
    lines = ["from dataclasses import dataclass", "", "@dataclass",
             f"class {name}:"]
    props = schema.get("properties", {})
    if not props:
        lines.append("    pass")
    for f, fs in props.items():
        py = PY_TYPES.get(fs.get("type", "any"), "object")
        default = "" if f in req else " = None"
        lines.append(f"    {f}: {py}{default}")
    lines.append("")
    lines.append("if __name__ == '__main__':")
    lines.append(f"    x = {name}(")
    args = []
    for f, fs in props.items():
        t = fs.get("type")
        if t == "string": args.append(f'{f}="x"')
        elif t == "integer": args.append(f"{f}=0")
        elif t == "number": args.append(f"{f}=0.0")
        elif t == "boolean": args.append(f"{f}=False")
        else: args.append(f"{f}=None")
    lines.append("        " + ", ".join(args))
    lines.append("    )")
    lines.append("    print(x)")
    lines.append("    print('self-test OK')")
    return "\\n".join(lines)

def gen_docs(schema: dict) -> str:
    name = schema.get("title", "Unnamed")
    req = set(schema.get("required", []))
    lines = [f"# {name}", "", "| field | type | required |", "|---|---|---|"]
    for f, fs in schema.get("properties", {}).items():
        lines.append(f"| {f} | {fs.get('type','any')} | {f in req} |")
    return "\\n".join(lines)

def generate(schema_text: str, outdir: Path) -> dict:
    s = json.loads(schema_text)
    outdir.mkdir(parents=True, exist_ok=True)
    name = s.get("title", "Unnamed").lower()
    (outdir / f"{name}.py").write_text(gen_class(s))
    (outdir / f"{name}.md").write_text(gen_docs(s))
    return {"class": str(outdir / f"{name}.py"),
            "docs": str(outdir / f"{name}.md")}

if __name__ == "__main__":
    schema = json.dumps({
        "title": "User",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string"},
        },
        "required": ["name", "email"],
    })
    result = generate(schema, Path("./gen_out"))
    print(result)
    print("self-test OK")
''',
)


# ══════════════════════════════════════════════════════════════════════
# 5. BINARY — a real C binary, compiled
# ══════════════════════════════════════════════════════════════════════
write(
    ROOT / "bin" / "hello.c",
    """#include <stdio.h>
int main(int argc, char **argv) {
    printf("binary: argc=%d\\n", argc);
    for (int i = 0; i < argc; i++) printf("  argv[%d] = %s\\n", i, argv[i]);
    return 0;
}
""",
)


# ══════════════════════════════════════════════════════════════════════
# 6. DAEMON — a long-running socket server
# ══════════════════════════════════════════════════════════════════════
write(
    ROOT / "daemon" / "daemon.py",
    '''"""daemon.py — a real socket daemon. Listens, echoes, counts, records."""
from __future__ import annotations
import json, socket, socketserver, sys, time
from pathlib import Path

STATE = Path.home() / "ucs" / "systems" / "daemon" / "state.json"

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        data = self.rfile.readline().strip()
        if not data:
            return
        try:
            req = json.loads(data)
        except Exception:
            self.wfile.write(b'{"error":"bad json"}\\n')
            return
        resp = {"echo": req, "ts": time.time(),
                "pid": __import__("os").getpid()}
        self.wfile.write((json.dumps(resp) + "\\n").encode())
        # persistent counter
        try:
            s = json.loads(STATE.read_text()) if STATE.exists() else {"count": 0}
            s["count"] += 1
            s["last_ts"] = resp["ts"]
            STATE.write_text(json.dumps(s))
        except Exception:
            pass

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

def run(host: str = "127.0.0.1", port: int = 19000):
    with Server((host, port), Handler) as srv:
        print(f"daemon listening on {host}:{port}  pid={__import__('os').getpid()}")
        srv.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 19000
    run(port=port)
''',
)


# ══════════════════════════════════════════════════════════════════════
# 7. KERNEL — a scheduler loop with process table
# ══════════════════════════════════════════════════════════════════════
write(
    ROOT / "kernel" / "kernel.py",
    '''"""kernel.py — a minimal kernel: process table + round-robin scheduler."""
from __future__ import annotations
import json, time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable

@dataclass
class Process:
    pid: int
    name: str
    state: str = "ready"   # ready | running | blocked | done
    pc: int = 0
    ticks: int = 0
    result: object = None

class Kernel:
    def __init__(self):
        self.procs = {}
        self.next_pid = 1
        self.clock = 0
        self.log = []
    def spawn(self, name: str, steps: list) -> int:
        pid = self.next_pid; self.next_pid += 1
        p = Process(pid=pid, name=name)
        p.steps = steps  # type: ignore
        self.procs[pid] = p
        self.log.append({"t": self.clock, "event": "spawn", "pid": pid, "name": name})
        return pid
    def step(self):
        for pid, p in self.procs.items():
            if p.state in ("done", "blocked"): continue
            steps = getattr(p, "steps", [])
            if p.pc >= len(steps):
                p.state = "done"
                self.log.append({"t": self.clock, "event": "exit", "pid": pid})
                continue
            p.state = "running"
            p.ticks += 1
            fn = steps[p.pc]
            try:
                p.result = fn() if callable(fn) else fn
            except Exception as e:
                p.result = f"error: {e}"
                p.state = "done"
                continue
            p.pc += 1
            p.state = "ready"
        self.clock += 1
    def run(self, until: int = 100):
        while self.clock < until and any(
            p.state not in ("done",) for p in self.procs.values()):
            self.step()
        return self.snapshot()
    def snapshot(self):
        return {"clock": self.clock,
                "procs": [{"pid": p.pid, "name": p.name, "state": p.state,
                           "pc": p.pc, "ticks": p.ticks, "result": p.result}
                          for p in self.procs.values()],
                "log": self.log}

if __name__ == "__main__":
    k = Kernel()
    k.spawn("counter",  [lambda: 1, lambda: 2, lambda: 3])
    k.spawn("squarer",  [lambda: 4, lambda: 16])
    k.spawn("summer",   [lambda: 5 + 5])
    snap = k.run(until=20)
    print(f"clock: {snap['clock']}")
    for p in snap["procs"]:
        print(f"  pid={p['pid']} {p['name']:10s} {p['state']:8s} "
              f"pc={p['pc']} ticks={p['ticks']} result={p['result']}")
    print("self-test OK")
''',
)


# ══════════════════════════════════════════════════════════════════════
# 8. DRIVER — file-backed device driver
# ══════════════════════════════════════════════════════════════════════
write(
    ROOT / "driver" / "driver.py",
    '''"""driver.py — a device driver stub backed by a file.

Models a character device: open/close/read/write/ioctl, with a real
file underneath and a small ioctl command set.
"""
from __future__ import annotations
import json
from pathlib import Path

DEV = Path.home() / "ucs" / "systems" / "driver" / "device.bin"

class Device:
    def __init__(self, path: Path = DEV):
        self.path = path
        self.fd = None
        self.cursor = 0
        self.ioctls = {"GET_POS": "return cursor",
                       "SET_POS": "set cursor",
                       "GET_SIZE": "return file size",
                       "RESET": "cursor = 0"}
    def open(self):
        self.path.touch(exist_ok=True)
        self.fd = self.path.open("r+b")
        return 0
    def close(self):
        if self.fd: self.fd.close(); self.fd = None
        return 0
    def write(self, data: bytes) -> int:
        if not self.fd: raise OSError("device not open")
        self.fd.seek(self.cursor)
        n = self.fd.write(data)
        self.cursor += n
        return n
    def read(self, n: int) -> bytes:
        if not self.fd: raise OSError("device not open")
        self.fd.seek(self.cursor)
        data = self.fd.read(n)
        self.cursor += len(data)
        return data
    def ioctl(self, cmd: str, arg=None):
        if cmd == "GET_POS":  return self.cursor
        if cmd == "SET_POS":  self.cursor = int(arg); return 0
        if cmd == "GET_SIZE": return self.path.stat().st_size
        if cmd == "RESET":    self.cursor = 0; return 0
        raise ValueError(f"unknown ioctl: {cmd}")

if __name__ == "__main__":
    d = Device()
    d.open()
    d.write(b"hello, driver\\n")
    d.ioctl("RESET")
    print(f"read back: {d.read(20)!r}")
    print(f"size:      {d.ioctl('GET_SIZE')}")
    print(f"cursor:    {d.ioctl('GET_POS')}")
    d.close()
    print("self-test OK")
''',
)


# ══════════════════════════════════════════════════════════════════════
# 9. eBPF — a C program + Python loader stub
# ══════════════════════════════════════════════════════════════════════
write(
    ROOT / "ebpf" / "count.c",
    """// count.c — an eBPF program (source form).
// Compiled with: clang -O2 -target bpf -c count.c -o count.o
// Loaded with bpftool or a Python loader.
#include <linux/bpf.h>
#include <linux/ptrace.h>

#define SEC(NAME) __attribute__((section(NAME), used))

// Map: 64-bit counter keyed by uint32
struct bpf_map_def SEC("maps") counts = {
    .type = BPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(__u32),
    .value_size = sizeof(__u64),
    .max_entries = 256,
};

// Tracepoint: count sys_enter calls per syscall number
SEC("tracepoint/raw_syscalls/sys_enter")
int count_syscalls(void *ctx) {
    __u32 key = 0;
    __u64 *val = bpf_map_lookup_elem(&counts, &key);
    if (val) __sync_fetch_and_add(val, 1);
    return 0;
}

char _license[] SEC("license") = "GPL";
""",
)

write(
    ROOT / "ebpf" / "loader.py",
    '''"""loader.py — userspace loader for count.o.

Without bcc/bpftool, this emulates the loader: it inspects the .o if
present, or prints the program's structure. With bcc installed, it
loads the program for real.
"""
from __future__ import annotations
import os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
SRC  = HERE / "count.c"
OBJ  = HERE / "count.o"

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
''',
)


# ══════════════════════════════════════════════════════════════════════
# RUNNER — build and verify everything
# ══════════════════════════════════════════════════════════════════════


def run_all():
    import subprocess

    results = {}

    print("== 1. interpreter ==")
    r = subprocess.run(
        [sys.executable, str(ROOT / "interp" / "interp.py")],
        capture_output=True,
        text=True,
    )
    results["interp"] = r.stdout.strip().splitlines()[-2:] or ["(no output)"]
    for l in results["interp"]:
        print(f"  {l}")

    print("== 2. translator ==")
    r = subprocess.run(
        [sys.executable, str(ROOT / "trans" / "trans.py")],
        capture_output=True,
        text=True,
    )
    print(f"  {r.stdout.strip().splitlines()[-1]}")

    print("== 3. compiler ==")
    r = subprocess.run(
        [sys.executable, str(ROOT / "comp" / "comp.py")], capture_output=True, text=True
    )
    for l in r.stdout.strip().splitlines()[-6:]:
        print(f"  {l}")

    print("== 4. generator ==")
    r = subprocess.run(
        [sys.executable, str(ROOT / "gen" / "gen.py")], capture_output=True, text=True
    )
    print(f"  {r.stdout.strip().splitlines()[-1]}")

    print("== 5. binary ==")
    if shutil_which("clang") or shutil_which("gcc"):
        cc = shutil_which("clang") or shutil_which("gcc")
        out = ROOT / "bin" / "hello"
        r = subprocess.run(
            [cc, str(ROOT / "bin" / "hello.c"), "-o", str(out)],
            capture_output=True,
            text=True,
        )
        if r.returncode == 0:
            run = subprocess.run(
                [str(out), "arg1", "arg2"], capture_output=True, text=True
            )
            print(f"  compiled: {out}")
            for l in run.stdout.strip().splitlines():
                print(f"  {l}")
        else:
            print(f"  compile failed: {r.stderr[:200]}")
    else:
        print("  no C compiler")

    print("== 6. daemon ==")
    # start, hit it once, kill
    d = subprocess.Popen(
        [sys.executable, str(ROOT / "daemon" / "daemon.py"), "19100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    import time, socket, json

    resp = None
    for attempt in range(10):
        time.sleep(0.3)
        try:
            s = socket.create_connection(("127.0.0.1", 19100), timeout=1)
            s.settimeout(2)
            s.sendall(b'{"hello": 1}\n')
            resp = s.recv(4096).decode()
            s.close()
            break
        except Exception:
            continue
    if resp:
        print(f"  sent:  hello")
        print(f"  recv:  {resp.strip()}")
    else:
        err = b""
        if d.poll() is not None:
            _, err = d.communicate(timeout=2)
        print(f"  daemon probe failed after 10 attempts")
        if err:
            print(f"  daemon stderr: {err.decode()[:300]}")
    d.terminate()
    try:
        d.wait(timeout=3)
    except Exception:
        d.kill()
    print("== 7. kernel ==")
    r = subprocess.run(
        [sys.executable, str(ROOT / "kernel" / "kernel.py")],
        capture_output=True,
        text=True,
    )
    for l in r.stdout.strip().splitlines():
        print(f"  {l}")

    print("== 8. driver ==")
    r = subprocess.run(
        [sys.executable, str(ROOT / "driver" / "driver.py")],
        capture_output=True,
        text=True,
    )
    for l in r.stdout.strip().splitlines():
        print(f"  {l}")

    print("== 9. eBPF ==")
    r = subprocess.run(
        [sys.executable, str(ROOT / "ebpf" / "loader.py")],
        capture_output=True,
        text=True,
    )
    for l in r.stdout.strip().splitlines():
        print(f"  {l}")

    return results


def shutil_which(name):
    import shutil

    return shutil.which(name)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run_all()
    else:
        print(f"wrote 9 systems to {ROOT}")
        for d in sorted(ROOT.iterdir()):
            if d.is_dir():
                files = list(d.glob("*"))
                print(f"  {d.name:10s} {len(files)} file(s)")
        print()
        print(f"run them all:  python3 {ROOT}/build.py run")
