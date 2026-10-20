import pathlib, decompose, execute
import compile as compiler
MAX = 2
def run(intent, root=None):
    attempts = []; cur = dict(intent); last = None
    for i in range(1, MAX + 1):
        plan = decompose.decompose(cur)
        manifest, written = compiler.compile_plan(plan)
        ev, ep = execute.execute(manifest)
        rec = {"attempt": i, "intent": cur, "plan_id": plan["plan_id"],
               "passed": ev["passed"], "evidence": ep, "artifacts": written,
               "test_results": ev["results"]}
        attempts.append(rec); last = rec
        if ev["passed"]:
            return {"outcome": "accepted", "attempts": attempts, "final": last}
        fails = [r.get("stderr") or r.get("stdout") or "failed"
                 for r in ev["results"] if r["exit"] != 0]
        acc = list(cur.get("acceptance", []))
        for f in fails:
            note = f"fix prior failure: {f.strip().splitlines()[0][:200]}"
            if note not in acc: acc.append(note)
        cur = {**cur, "acceptance": acc}
    return {"outcome": "failed_after_retries", "attempts": attempts, "final": last}
if __name__ == "__main__":
    r = run({"goal": "build foo", "acceptance": ["foo returns ok"]})
    assert r["outcome"] == "accepted" and len(r["attempts"]) == 1
    real = execute.execute; n = {"c": 0}
    def flaky(m):
        n["c"] += 1; ev, p = real(m)
        if n["c"] == 1:
            ev["passed"] = False
            ev["results"] = [{"test": "x", "exit": 1, "stdout": "", "stderr": "forced"}]
        return ev, p
    execute.execute = flaky
    try:
        r = run({"goal": "build foo", "acceptance": ["foo returns ok"]})
        assert r["outcome"] == "accepted" and len(r["attempts"]) == 2
        assert any("fix prior failure" in a for a in r["attempts"][1]["intent"]["acceptance"])
    finally:
        execute.execute = real
    execute.execute = lambda m: ({"passed": False, "results": [{"test": "x", "exit": 1, "stdout": "", "stderr": "forced"}]}, "x")
    try:
        r = run({"goal": "y", "acceptance": ["z"]})
        if r["outcome"] != "failed_after_retries":
            raise SystemExit(f"expected failed_after_retries, got {r['outcome']}")
    finally:
        execute.execute = real
    print("revise OK")
