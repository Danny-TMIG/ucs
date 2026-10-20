import json, re, sys, uuid
def decompose(intent):
    goal = intent["goal"].lower()
    slug = re.sub(r"[^a-z0-9]+", "-", goal).strip("-")[:40] or "task"
    plan_id = str(uuid.uuid4())
    artifacts = []
    for acc in intent["acceptance"]:
        a_slug = re.sub(r"[^a-z0-9]+", "-", acc.lower()).strip("-")[:40] or "check"
        artifacts.append({
            "kind": "test",
            "path": f"build/{plan_id}/tests/test_{a_slug}.py",
            "asserts": acc,
        })
    artifacts.append({
        "kind": "module",
        "path": f"build/{plan_id}/handlers/{slug}.py",
        "exports": [slug],
    })
    artifacts.append({
        "kind": "schema",
        "path": f"build/{plan_id}/schemas/{slug}.schema.json",
        "fields": ["id", "status"],
    })
    return {"plan_id": plan_id, "intent": intent, "artifacts": artifacts}
if __name__ == "__main__":
    try:
        decompose({"goal": None})
        raise SystemExit("decompose should fail on None goal")
    except (AttributeError, KeyError, TypeError):
        pass
    print(json.dumps(decompose(json.load(sys.stdin)), indent=2))
