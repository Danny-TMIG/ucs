#!/usr/bin/env python3
"""The closed loop: intent -> validate -> decompose -> compile -> execute -> outcome."""
import json, uuid, datetime
import validate, decompose, compile as compiler, execute

def run_loop(intent):
    cid = str(uuid.uuid4())
    errs = validate.validate(intent)
    if errs:
        return {"correlation_id": cid, "purpose": "governed-outcome",
                "outcome": "rejected", "reason": errs}
    plan = decompose.decompose(intent)
    manifest, written = compiler.compile_plan(plan)
    evidence, ev_path = execute.execute(manifest)
    return {
        "correlation_id": cid,
        "purpose": "governed-outcome",
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "outcome": "accepted" if evidence["passed"] else "failed",
        "plan_id": plan["plan_id"],
        "artifacts": written,
        "evidence": ev_path,
        "test_results": evidence["results"],
    }

if __name__ == "__main__":
    import sys
    intent = json.load(sys.stdin)
    print(json.dumps(run_loop(intent), indent=2))
