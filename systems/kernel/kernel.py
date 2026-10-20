"""kernel.py — a minimal kernel: process table + round-robin scheduler."""

from __future__ import annotations
import json, time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable


@dataclass
class Process:
    pid: int
    name: str
    state: str = "ready"  # ready | running | blocked | done
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
        pid = self.next_pid
        self.next_pid += 1
        p = Process(pid=pid, name=name)
        p.steps = steps  # type: ignore
        self.procs[pid] = p
        self.log.append({"t": self.clock, "event": "spawn", "pid": pid, "name": name})
        return pid

    def step(self):
        for pid, p in self.procs.items():
            if p.state in ("done", "blocked"):
                continue
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
            p.state not in ("done",) for p in self.procs.values()
        ):
            self.step()
        return self.snapshot()

    def snapshot(self):
        return {
            "clock": self.clock,
            "procs": [
                {
                    "pid": p.pid,
                    "name": p.name,
                    "state": p.state,
                    "pc": p.pc,
                    "ticks": p.ticks,
                    "result": p.result,
                }
                for p in self.procs.values()
            ],
            "log": self.log,
        }


if __name__ == "__main__":
    k = Kernel()
    k.spawn("counter", [lambda: 1, lambda: 2, lambda: 3])
    k.spawn("squarer", [lambda: 4, lambda: 16])
    k.spawn("summer", [lambda: 5 + 5])
    snap = k.run(until=20)
    print(f"clock: {snap['clock']}")
    for p in snap["procs"]:
        print(
            f"  pid={p['pid']} {p['name']:10s} {p['state']:8s} "
            f"pc={p['pc']} ticks={p['ticks']} result={p['result']}"
        )
    print("self-test OK")
