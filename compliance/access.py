
import datetime, json, pathlib

ROOT = pathlib.Path.cwd().resolve()
LOG = ROOT / "build" / "access.jsonl"

def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def record(who, action, resource, decision, reason=""):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": _now(), "who": who, "action": action,
             "resource": resource, "decision": decision, "reason": reason}
    with LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry

def allowed(who, action, resource):
    """Structural check: action must be in a fixed set, resource must resolve."""
    ACTIONS = {"read", "write", "execute", "delete", "delegate", "approve"}
    if action not in ACTIONS:
        record(who, action, resource, "deny", f"unknown action {action!r}")
        return False
    if not isinstance(resource, str) or not resource:
        record(who, action, resource, "deny", "empty resource")
        return False
    record(who, action, resource, "allow")
    return True

if __name__ == "__main__":
    import tempfile, os
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    LOG = pathlib.Path.cwd() / "build" / "access.jsonl"
    assert allowed("alice", "read", "spec/loop.py") is True
    assert allowed("alice", "nuke", "spec/loop.py") is False
    assert allowed("alice", "read", "") is False
    lines = LOG.read_text().strip().split("\n")
    assert len(lines) == 3
    print("access OK")
