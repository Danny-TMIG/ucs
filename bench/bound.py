#!/usr/bin/env python3
"""bound.py — produce a falsifiable bounded statement about compile times.

Bounds held:
  - grammar/size (domain)
  - per-event wall limit T
  - sample size N and 95% CI on the mean
Does not bound the space of all compiles.
"""
import math
import json
import sys


def _ci95(samples):
    n = len(samples)
    mean = sum(samples) / n
    var = sum((x - mean) ** 2 for x in samples) / max(n - 1, 1)
    se = math.sqrt(var / n)
    return (mean - 1.96 * se, mean + 1.96 * se)


def bound(sample, grammar, max_size, wall_limit):
    """sample: list of {"grammar": str, "size": int, "wall": float}
    Returns (ok, statement_or_reason)."""
    if not sample:
        return False, "empty sample"
    for s in sample:
        if s.get("grammar") != grammar:
            return False, f"grammar violation: {s.get('grammar')!r} != {grammar!r}"
        if s.get("size", 0) > max_size:
            return False, f"size violation: {s['size']} > {max_size}"
        if s.get("wall", 0) > wall_limit:
            return False, f"wall violation: {s['wall']} > {wall_limit}"
    walls = [s["wall"] for s in sample]
    ci = _ci95(walls)
    return True, {
        "grammar": grammar,
        "max_size": max_size,
        "wall_limit": wall_limit,
        "n": len(walls),
        "mean": sum(walls) / len(walls),
        "mean_ci_95": ci,
        "max_observed": max(walls),
        "all_within_limit": True,
    }


if __name__ == "__main__":
    sample = [
        {"grammar": "py", "size": 800, "wall": 0.012},
        {"grammar": "py", "size": 1200, "wall": 0.018},
        {"grammar": "py", "size": 1500, "wall": 0.021},
    ]
    ok, st = bound(sample, "py", max_size=2048, wall_limit=0.5)
    assert ok, st
    assert st["n"] == 3
    assert st["all_within_limit"] is True
    assert st["mean_ci_95"][0] <= st["mean"] <= st["mean_ci_95"][1]

    # wall violation
    bad = sample + [{"grammar": "py", "size": 500, "wall": 2.0}]
    ok, reason = bound(bad, "py", 2048, 0.5)
    assert not ok and "wall" in reason, reason

    # size violation
    ok, reason = bound([{"grammar": "py", "size": 9999, "wall": 0.1}], "py", 2048, 0.5)
    assert not ok and "size" in reason, reason

    # grammar violation
    ok, reason = bound([{"grammar": "rs", "size": 100, "wall": 0.1}], "py", 2048, 0.5)
    assert not ok and "grammar" in reason, reason

    print("bound OK")
