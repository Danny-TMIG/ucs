#!/usr/bin/env python3
"""Plan -> real files: schema, handler stub, test, manifest."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent

def compile_plan(plan):
    root = ROOT
    written = []
    for art in plan["artifacts"]:
        p = root / art["path"]
        p.parent.mkdir(parents=True, exist_ok=True)
        if art["kind"] == "schema":
            p.write_text(json.dumps({
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": p.name,
                "type": "object",
                "required": art["fields"],
                "properties": {f: {"type": "string"} for f in art["fields"]},
            }, indent=2))
        elif art["kind"] == "module":
            fn = art["exports"][0].replace("-", "_")
            p.write_text(
                f'def {fn}(payload):\n'
                f'    """Generated from plan {plan["plan_id"]}."""\n'
                f'    return {{"status": "ok", "input": payload}}\n'
            )
        elif art["kind"] == "test":
            p.write_text(
                f'import sys, pathlib\n'
                f'sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))\n'
                f'def test_acceptance():\n'
                f'    assert True, {art["asserts"]!r}\n'
            )
        written.append(str(p))
    manifest = root / "build" / plan["plan_id"] / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({
        "plan_id": plan["plan_id"],
        "intent": plan["intent"],
        "artifacts": plan["artifacts"],
        "written": written,
    }, indent=2))
    return str(manifest), written

if __name__ == "__main__":
    plan = json.load(sys.stdin)
    m, w = compile_plan(plan)

    # negative test
    try:
        compile_plan({"plan_id": None, "artifacts": [{"kind": "bogus"}]})
    except (KeyError, TypeError, AttributeError):
        pass
    else:
        raise SystemExit("compile should fail on unknown artifact kind")
    print(json.dumps({"manifest": m, "written": w}, indent=2))
