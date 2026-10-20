import json, pathlib, hashlib, datetime
STATE_ROOT = pathlib.Path("build/_state")
READERS = {"loop", "swarm", "revise", "atlas", "desk"}
WRITERS = {"loop", "swarm", "revise"}
def state_path(key):
    return STATE_ROOT / f"{key}.json"
def write(key, value, who="loop"):
    if who not in WRITERS:
        raise PermissionError(f"{who} is not an authorized writer")
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    p = state_path(key)
    prev = p.read_text() if p.exists() else ""
    payload = {"key": key, "value": value,
               "prev_hash": hashlib.sha256(prev.encode()).hexdigest() if prev else None,
               "ts": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    p.write_text(json.dumps(payload, indent=2))
    return p
def read(key, who="loop"):
    if who not in READERS:
        raise PermissionError(f"{who} is not an authorized reader")
    p = state_path(key)
    if not p.exists():
        return None
    return json.loads(p.read_text())
def history(key):
    p = state_path(key)
    if not p.exists():
        return []
    return [json.loads(p.read_text())]
def snapshot():
    if not STATE_ROOT.exists():
        return {}
    return {p.stem: json.loads(p.read_text()) for p in STATE_ROOT.glob("*.json")}
if __name__ == "__main__":
    import tempfile, os
    os.chdir(tempfile.mkdtemp())
    write("test", {"x": 1}, who="loop")
    assert read("test", who="loop")["value"] == {"x": 1}
    try: write("bad", {}, who="desk")
    except PermissionError: pass
    else: raise SystemExit("expected PermissionError on write by desk")
    try: read("test", who="readonly")
    except PermissionError: pass
    else: raise SystemExit("expected PermissionError on read by readonly")
    s = snapshot(); assert "test" in s
    print("state OK")
