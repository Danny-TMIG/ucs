
"""Licence: what an agency is permitted to do, on what terms, until when."""
import datetime, json, pathlib

ROOT = pathlib.Path.cwd().resolve()
LICENCES = ROOT / "build" / "licences.jsonl"

def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

SCOPES = {"read", "write", "execute", "delegate", "publish", "certify"}

def issue(licence_id, agency_id, scope, terms, expires=None, issuer=None):
    if scope not in SCOPES:
        raise ValueError(f"unknown scope {scope!r}")
    if not licence_id or not agency_id:
        raise ValueError("licence needs id and agency")
    LICENCES.parent.mkdir(parents=True, exist_ok=True)
    e = {"ts": _now(), "id": licence_id, "agency": agency_id, "scope": scope,
         "terms": terms, "expires": expires, "issuer": issuer, "action": "issue"}
    with LICENCES.open("a") as f:
        f.write(json.dumps(e) + "\n")
    return e

def revoke(licence_id, by, reason):
    if not by or not reason:
        raise ValueError("revoke needs by and reason")
    e = {"ts": _now(), "id": licence_id, "action": "revoke", "by": by, "reason": reason}
    with LICENCES.open("a") as f:
        f.write(json.dumps(e) + "\n")
    return e

def active(licence_id, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if not LICENCES.exists():
        return False
    state = False
    expires = None
    for line in LICENCES.read_text().splitlines():
        e = json.loads(line)
        if e["id"] != licence_id:
            continue
        if e["action"] == "issue":
            state = True
            expires = e.get("expires")
        elif e["action"] == "revoke":
            state = False
    if not state or not expires:
        return state
    dt = datetime.datetime.fromisoformat(expires)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return state and dt > now

if __name__ == "__main__":
    import tempfile, os
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    LICENCES = pathlib.Path.cwd() / "build" / "licences.jsonl"
    issue("L-1", "team-1", "read", "internal only", expires="2099-01-01T00:00:00+00:00")
    assert active("L-1") is True
    revoke("L-1", "regulator", "expired")
    assert active("L-1") is False
    issue("L-2", "team-1", "write", "internal", expires="2000-01-01T00:00:00+00:00")
    assert active("L-2") is False
    try:
        issue("L-3", "team-1", "nuke", "x")
        raise SystemExit("bad scope should fail")
    except ValueError:
        pass
    print("licence OK")
