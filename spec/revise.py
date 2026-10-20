#!/usr/bin/env python3
"""revise.py — on failure, re-decompose with failure as added constraint, retry once."""
import pathlib

import decompose
import compile as compiler
import execute


MAX_ATTEMPTS = 2


def run(intent, root=None):
    root = pathlib.Path(root) if root else pathlib.Path(".")
    attempts = []
    current = dict(intent)
    last = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        plan = decompose.decompose(current)
        manifest, written = compiler.compile_plan(plan)
        evidence, ev_path = execute.execute(manifest)
        record = {
            "attempt": attempt,
            "intent": current,
            "plan_id": plan["plan_id"],
            "passed": evidence["passed"],
            "evidence": ev_path,
            "artifacts": written,
            "test_results": evidence["results"],
        }
        attempts.append(record)
        last = record
        if evidence["passed"]:
            return {"outcome": "accepted", "attempts": attempts, "final": last}
        failures = []
        for r in evidence["results"]:
            if r["exit"] != 0:
                failures.append(r.get("stderr") or r.get("stdout") or "failed")
        revised_acceptance = list(current.get("acceptance", []))
        for f in failures:
            note = f"fix prior failure: {f.strip().splitlines()[0][:200]}"
            if note not in revised_acceptance:
                revised_acceptance.append(note)
        current = {**current, "acceptance": revised_acceptance}
    return {"outcome": "failed_after_retries", "attempts": attempts, "final": last}


if __name__ == "__main__":
    intent = {"goal": "build foo", "acceptance": ["foo returns ok"]}
    result = run(intent)
    assert result["outcome"] == "accepted", result
    assert len(result["attempts"]) == 1

    real_execute = execute.execute
    call_count = {"n": 0}

    def flaky_execute(manifest):
        call_count["n"] += 1
        ev, path = real_execute(manifest)
        if call_count["n"] == 1:
            ev["passed"] = False
            ev["results"] = [{"test": "x", "exit": 1,
                              "stdout": "", "stderr": "forced failure"}]
        return ev, path

    execute.execute = flaky_execute
    try:
        result = run({"goal": "build foo", "acceptance": ["foo returns ok"]})
        assert result["outcome"] == "accepted", result
        assert len(result["attempts"]) == 2, result
        second = result["attempts"][1]["intent"]["acceptance"]
        assert any("fix prior failure" in a for a in second), second
    finally:
        execute.execute = real_execute
    print("revise OK")
