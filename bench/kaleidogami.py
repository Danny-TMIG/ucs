#!/usr/bin/env python3
"""kaleidogami.py — fold-reflect index over the ledger.
reflect: canonicalize by (grammar, size) into one range entry.
fold: partition by regime. Both read the real ledger."""
import json, pathlib
LEDGER = pathlib.Path("bench/ledger.json")
REGIMES = [("trivial", 0.0, 0.01), ("small", 0.01, 1.0), ("medium", 1.0, 30.0),
           ("large", 30.0, 600.0), ("huge", 600.0, float("inf"))]

def load():
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else []

def reflect(entries):
    if not entries: return []
    groups = {}
    for e in entries:
        groups.setdefault((e["grammar"], e["size"]), []).append(e["wall"])
    out = []
    for (grammar, size), walls in sorted(groups.items()):
        n = len(walls)
        mean = sum(walls) / n
        var = sum((w - mean) ** 2 for w in walls) / n if n > 1 else 0.0
        out.append({"grammar": grammar, "size": size, "n": n,
                    "min": min(walls), "max": max(walls), "mean": mean,
                    "stdev": var ** 0.5})
    return out

def fold(entries):
    out = {name: [] for name, _, _ in REGIMES}
    for e in entries:
        for name, lo, hi in REGIMES:
            if lo <= e["wall"] < hi:
                out[name].append(e); break
    return out

def summary():
    entries = load()
    return {"total": len(entries), "reflected": reflect(entries),
            "folded": {k: len(v) for k, v in fold(entries).items()}}

if __name__ == "__main__":
    import tempfile, os
    os.chdir(tempfile.mkdtemp()); pathlib.Path("bench").mkdir()
    pathlib.Path("bench/ledger.json").write_text(json.dumps([
        {"grammar": "py", "size": 100, "wall": 0.005},
        {"grammar": "py", "size": 100, "wall": 0.007},
        {"grammar": "py", "size": 200, "wall": 0.500},
        {"grammar": "rs", "size": 50,  "wall": 2.500},
    ]))
    r = reflect(load())
    assert len(r) == 3, r
    py100 = next(x for x in r if x["grammar"] == "py" and x["size"] == 100)
    assert py100["n"] == 2 and abs(py100["mean"] - 0.006) < 1e-9, py100
    f = fold(load())
    assert len(f["trivial"]) == 2
    assert len(f["small"]) == 1
    assert len(f["medium"]) == 1
    # real invariant: reflect preserves count
    total_reflected = sum(x["n"] for x in r)
    assert total_reflected == 4, total_reflected
    # real invariant: fold partitions exactly — every entry in one regime
    total_folded = sum(len(v) for v in f.values())
    assert total_folded == 4, total_folded
    # negative test: no entry in two regimes
    for name, bucket in f.items():
        for e in bucket:
            lo, hi = next((lo, hi) for n, lo, hi in REGIMES if n == name)
            assert lo <= e["wall"] < hi, (name, e)
    print(f"kaleidogami OK ({len(r)} groups, {total_folded} in {sum(1 for v in f.values() if v)} regimes)")
