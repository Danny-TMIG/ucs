import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "specs/intent/intent.schema.json").read_text())
def validate(intent):
    errs = []
    for k in SCHEMA["required"]:
        if k not in intent:
            errs.append(f"missing required: {k}")
    for k, v in intent.items():
        if k not in SCHEMA["properties"]:
            errs.append(f"unknown field: {k}")
            continue
        spec = SCHEMA["properties"][k]
        if spec.get("type") == "string" and not isinstance(v, str):
            errs.append(f"{k} must be string")
        if spec.get("type") == "array" and not isinstance(v, list):
            errs.append(f"{k} must be array")
    if isinstance(intent.get("acceptance"), list) and not intent["acceptance"]:
        errs.append("acceptance must be non-empty")
    return errs
if __name__ == "__main__":
    data = json.load(sys.stdin)
    errs = validate(data)
    if errs:
        print("\n".join(errs)); sys.exit(1)
    try:
        validate({"goal": "", "acceptance": []})
        errs = validate({"acceptance": ["y"]})
        assert "goal" in " ".join(errs), errs
    except Exception as e:                
        raise SystemExit(f"validate negative test failed: {e}")
    print("OK")
