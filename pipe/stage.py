#!/usr/bin/env python3
"""
stage.py -- append a seed record to build/stage.json.

Reads one record on stdin, appends to build/stage.json (creating if absent),
and prints the record. If stage.json has records from other producers, they
are preserved. The stage is the union.
"""
import json, pathlib, sys

STAGE = pathlib.Path("build/stage.json")

def load():
    if STAGE.exists():
        return json.loads(STAGE.read_text())
    return {"reduced_to": "stage/v1", "records": []}

def save(stage):
    STAGE.parent.mkdir(parents=True, exist_ok=True)
    STAGE.write_text(json.dumps(stage, indent=2))

def append(record):
    stage = load()
    stage["records"].append(record)
    save(stage)
    return stage

if __name__ == "__main__":
    rec = json.load(sys.stdin)
    stage = append(rec)
    print(json.dumps({"appended": rec["path"], "stage_size": len(stage["records"])}))
