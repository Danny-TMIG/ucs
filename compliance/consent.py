
import datetime, json, pathlib

ROOT = pathlib.Path.cwd().resolve()
CONSENT = ROOT / "build" / "consent.jsonl"

def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def grant(subject, scope, purpose, expires=None):
    CONSENT.parent.mkdir(parents=True, exist_ok=True)
    e = {"ts": _now(), "subject": subject, "scope": scope,
         "purpose": purpose, "action": "grant", "expires": expires}
    with CONSENT.open("a") as f:
        f.write(json.dumps(e) + "\n")
    return e

def revoke(subject, scope, by):
    e = {"ts": _now(), "subject": subject, "scope": scope,
         "action": "revoke", "by": by}
    with CONSENT.open("a") as f:
        f.write(json.dumps(e) + "\n")
    return e

def active(subject, scope, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if not CONSENT.exists():
        return False
    granted = False
    for line in CONSENT.read_text().splitlines():
        e = json.loads(line)
        if e["subject"] != subject or e["scope"] != scope:
            continue
        if e["action"] == "grant":
            exp = e.get("expires")
            if exp:
                dt = datetime.datetime.fromisoformat(exp)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                if dt < now:
                    continue
            granted = True
        elif e["action"] == "revoke":
            granted = False
    return granted

if __name__ == "__main__":
    import tempfile, os
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    CONSENT = pathlib.Path.cwd() / "build" / "consent.jsonl"
    grant("alice", "email", "support")
    assert active("alice", "email") is True
    revoke("alice", "email", "alice")
    assert active("alice", "email") is False
    grant("bob", "email", "support", expires="2099-01-01T00:00:00+00:00")
    assert active("bob", "email") is True
    grant("carol", "email", "support", expires="2000-01-01T00:00:00+00:00")
    assert active("carol", "email") is False
    print("consent OK")
