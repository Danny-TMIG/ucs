#!/usr/bin/env python3
"""
record.py -- turn an orchestrate.py output into a seed record.

Reads a JSON orchestration result on stdin, writes one record on stdout.
The record has the nine seed fields. produced_by is "pipe.record". format is
"pipe.llm-output". facts include target, wall_s, output_chars.
"""
import json, sys, time

d = json.load(sys.stdin)
out = d.get("output", "")
rec = {
    "path": f"build/records/{d.get('target','?')}/{int(time.time()*1000)}.json",
    "format": "pipe.llm-output",
    "semantics": "text",
    "ok": d.get("exit") == 0 and bool(out.strip()),
    "reason": "" if (d.get("exit") == 0 and out.strip()) else (d.get("stderr") or "empty output"),
    "size": len(out.encode()),
    "facts": {
        "target": d.get("target"),
        "wall_s": d.get("wall_s"),
        "output_chars": len(out),
        "output_lines": len(out.splitlines()) if out else 0,
        "prompt": d.get("prompt", ""),
    },
    "produced_by": "pipe.record",
    "reduced_to": "record/v1",
}
print(json.dumps(rec))
