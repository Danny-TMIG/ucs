"""opcodes.py — dissolve the boundary between behavior and machine.

Maps every primitive from ~/ucs/out/sub_arity.json to an opcode of a
small register VM. Executes the VM. Produces a trace that is the
flattened execution of every behavior.

Opcodes:
  LOAD r, v       load value into register
  STORE r, k, v   store value at key
  ADD r, a, b     r = a + b
  CALL f, args    call primitive
  RET             return
  JMP label       jump
  JZ r, label     jump if zero
  EMIT k, v       emit artifact
  VALID k, v      record validation
"""

from __future__ import annotations
import json, sys
from pathlib import Path
from collections import defaultdict

HOME = Path.home()
UCS = HOME / "ucs"
OUT = UCS / "out"
SUB = OUT / "sub_arity.json"

# primitive → opcode mapping by semantic domain
OPCODE_MAP = {
    "load": "LOAD",
    "read": "LOAD",
    "fetch": "LOAD",
    "query": "LOAD",
    "store": "STORE",
    "write": "STORE",
    "persist": "STORE",
    "cache": "STORE",
    "add": "ADD",
    "merge": "ADD",
    "compose": "ADD",
    "aggregate": "ADD",
    "remove": "SUB",
    "reduce": "SUB",
    "delete": "SUB",
    "evict": "SUB",
    "call": "CALL",
    "invoke": "CALL",
    "execute": "CALL",
    "run": "CALL",
    "return": "RET",
    "yield": "RET",
    "emit": "RET",
    "resolve": "CALL",
    "validate": "VALID",
    "verify": "VALID",
    "generate": "EMIT",
    "synthesize": "EMIT",
    "build": "EMIT",
    "schedule": "JMP",
    "queue": "JMP",
    "jump": "JMP",
    "check": "JZ",
    "detect": "JZ",
    "if": "JZ",
    "loop": "JMP",
    "iterate": "JMP",
    "recurse": "CALL",
    "init": "LOAD",
    "bootstrap": "LOAD",
    "self": "CALL",
    "compile": "EMIT",
    "link": "CALL",
    "publish": "EMIT",
    "sign": "VALID",
    "attest": "VALID",
    "hash": "CALL",
    "lock": "CALL",
    "unlock": "CALL",
    "wait": "JMP",
}

# richer classifier: maps a primitive to an opcode by semantic class
CLASSES = [
    # (opcode, set of primitive substrings that map to it)
    (
        "LOAD",
        {
            "load",
            "read",
            "fetch",
            "query",
            "get",
            "input",
            "receive",
            "accept",
            "import",
            "discover",
            "watch",
            "monitor",
            "observe",
            "listen",
            "poll",
            "scan",
            "sample",
            "probe",
        },
    ),
    (
        "STORE",
        {
            "store",
            "write",
            "persist",
            "cache",
            "save",
            "put",
            "output",
            "emit_file",
            "index",
            "snapshot",
            "version",
            "archive_file",
            "dump",
            "serialize",
            "lock",
            "acquire",
        },
    ),
    (
        "ADD",
        {
            "add",
            "merge",
            "compose",
            "aggregate",
            "combine",
            "join",
            "union",
            "concat",
            "fold",
            "sum",
            "accumulate",
            "concat",
            "gather",
            "collect",
        },
    ),
    (
        "SUB",
        {
            "remove",
            "reduce",
            "delete",
            "evict",
            "subtract",
            "split",
            "partition",
            "decompose",
            "destroy",
            "kill",
            "drop",
        },
    ),
    (
        "CALL",
        {
            "call",
            "invoke",
            "execute",
            "run",
            "apply",
            "eval",
            "resolve",
            "compute",
            "transform",
            "map",
            "apply_fn",
            "dispatch",
            "compile",
            "link",
            "rebuild",
            "build",
            "generate",
            "synthesize",
            "emit",
            "construct",
            "create",
            "spawn",
            "fork",
            "exec",
        },
    ),
    (
        "VALID",
        {
            "validate",
            "verify",
            "check",
            "assert",
            "test",
            "attest",
            "sign",
            "hash",
            "measure",
            "audit",
            "inspect",
            "benchmark",
            "profile",
            "trace",
            "probe",
            "certify",
        },
    ),
    (
        "JZ",
        {
            "if",
            "cond",
            "case",
            "match",
            "branch",
            "switch",
            "when",
            "detect",
            "differentiate",
            "diverge",
            "compare",
        },
    ),
    (
        "JMP",
        {
            "jump",
            "goto",
            "schedule",
            "queue",
            "delay",
            "wait",
            "retry",
            "loop",
            "iterate",
            "recurse",
            "resume",
            "continue",
            "next",
            "restart",
            "rewind",
        },
    ),
    (
        "RET",
        {
            "return",
            "yield",
            "finish",
            "halt",
            "stop",
            "end",
            "done",
            "exit",
            "complete",
            "publish",
            "release",
            "ship",
        },
    ),
    ("NOP", {"noop", "nop", "skip", "pass", "ignore", "defer"}),
]


def pick_opcode(prim: str) -> str:
    p = prim.lower()
    # exact
    if p in OPCODE_MAP:
        return OPCODE_MAP[p]
    # semantic class membership
    for op, s in CLASSES:
        if p in s:
            return op
        for w in s:
            if w in p or p in w:
                return op
    # heuristic: look for verb-like prefixes
    for op, s in CLASSES:
        for w in s:
            if p.startswith(w) or p.endswith(w):
                return op
    return "CALL"


# ── tiny VM ───────────────────────────────────────────────────────────
class VM:
    def __init__(self):
        self.regs = [0] * 16
        self.trace = []
        self.artifacts = []
        self.validations = []

    def run(self, program: list):
        pc = 0
        while pc < len(program):
            op = program[pc]
            self.trace.append(op)
            kind = op[0]
            try:
                if kind == "LOAD":
                    _, r, v = op
                    self.regs[r] = v
                elif kind == "STORE":
                    _, r, k, v = op
                    self.regs[r] = v
                elif kind == "ADD":
                    _, r, a, b = op
                    self.regs[r] = a + b
                elif kind == "SUB":
                    _, r, a, b = op
                    self.regs[r] = a - b
                elif kind == "CALL":
                    _, f, *_ = op
                elif kind == "RET":
                    pass
                elif kind == "EMIT":
                    _, k, v = op
                    self.artifacts.append({"k": k, "v": v})
                elif kind == "VALID":
                    _, k, v = op
                    self.validations.append({"k": k, "v": v})
                elif kind == "JMP":
                    pass
                elif kind == "JZ":
                    pass
            except Exception:
                pass
            pc += 1


# ── compile primitives to a program ───────────────────────────────────
def compile_program(prims: list) -> list:
    prog = []
    r = 0
    for p in prims:
        op = pick_opcode(p)
        if op == "LOAD":
            prog.append(("LOAD", r, p))
            r = (r + 1) % 16
        elif op == "STORE":
            prog.append(("STORE", r, p, p))
        elif op == "ADD":
            prog.append(("ADD", r, 1, 1))
        elif op == "SUB":
            prog.append(("SUB", r, 1, 1))
        elif op == "CALL":
            prog.append(("CALL", p))
        elif op == "EMIT":
            prog.append(("EMIT", p, p))
        elif op == "VALID":
            prog.append(("VALID", p, True))
        elif op == "JMP":
            prog.append(("JMP", p))
        elif op == "JZ":
            prog.append(("JZ", r, p))
        else:
            prog.append(("CALL", p))
    prog.append(("RET",))
    return prog


# ── main ──────────────────────────────────────────────────────────────
def main():
    if not SUB.exists():
        print(f"missing {SUB}; run arity.py first")
        sys.exit(1)
    data = json.loads(SUB.read_text())
    prims = sorted(data["primitive_to_behaviors"].keys())
    print(f"== opcode dissolution ==")
    print(f"  distinct primitives: {len(prims)}")
    print()

    prog = compile_program(prims)
    vm = VM()
    vm.run(prog)

    print(f"  program length: {len(prog)} instructions")
    print(f"  registers used: 16")
    print(f"  artifacts:      {len(vm.artifacts)}")
    print(f"  validations:    {len(vm.validations)}")
    print()

    # opcode histogram
    hist = defaultdict(int)
    for op in prog:
        hist[op[0]] += 1
    print("== opcode histogram ==")
    for op, n in sorted(hist.items(), key=lambda kv: -kv[1]):
        bar = "#" * min(60, n)
        print(f"  {op:6s} {n:5d}  {bar}")
    print()

    # persist
    p = OUT / "program.json"
    p.write_text(
        json.dumps(
            {
                "primitives": prims,
                "opcode_map": {p: pick_opcode(p) for p in prims},
                "program": prog,
                "trace_count": len(vm.trace),
                "artifacts": vm.artifacts,
                "validations": vm.validations,
            },
            indent=2,
        )
    )
    print(f"wrote: {p}")
    print()
    print("== the dissolution, stated ==")
    print("  every behavior  -> sub-arity tree  -> tokens")
    print("  every token     -> primitive       -> opcode")
    print("  every opcode    -> VM instruction  -> execution")
    print(
        f"  {data['behaviors']} behaviors flattened to "
        f"{len(prims)} primitives across {len(hist)} opcodes."
    )


if __name__ == "__main__":
    main()
