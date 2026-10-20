import json, pathlib
SCHEMA = json.loads((pathlib.Path(__file__).resolve().parent.parent / "specs/contracts/payload.schema.json").read_text())
DEFS = SCHEMA["$defs"]
def validate(kind, body):
    errs = []
    if kind not in DEFS:
        return [f"unknown payload kind: {kind}"]
    spec = DEFS[kind]
    for k in spec.get("required", []):
        if k not in body:
            errs.append(f"missing required: {k}")
    for k, v in body.items():
        if k not in spec.get("properties", {}) and spec.get("additionalProperties") is False:
            errs.append(f"unknown field: {k}")
    return errs
if __name__ == "__main__":
    assert validate("intent", {"goal": "x", "acceptance": ["y"]}) == []
    assert validate("intent", {"goal": "x"}) == ["missing required: acceptance"]
    assert validate("authorization_decision", {"decision": "allow"}) == ["missing required: request_id"]
    assert validate("authorization_decision", {"decision": "weird", "request_id": "r"}) == []
    assert validate("nope", {}) == ["unknown payload kind: nope"]
    try:
        validate("nonexistent_kind", {})
        raise SystemExit("payload should fail on unknown kind")
    except SystemExit:
        pass
    print("payload OK")
