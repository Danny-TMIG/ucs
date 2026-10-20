
"""Referee: the authority that approves or rejects a proposal."""
import datetime, json, pathlib

ROOT = pathlib.Path.cwd().resolve()
REFEREES = ROOT / "build" / "referees.jsonl"

def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

KINDS = {"human", "agency", "certifier", "system"}

def register(ref_id, kind, authority, scope=None):
    if kind not in KINDS:
        raise ValueError(f"unknown referee kind {kind!r}")
    if not ref_id or not authority:
        raise ValueError("referee needs id and authority")
    REFEREES.parent.mkdir(parents=True, exist_ok=True)
    e = {"ts": _now(), "id": ref_id, "kind": kind, "authority": authority,
         "scope": scope or [], "action": "register"}
    with REFEREES.open("a") as f:
        f.write(json.dumps(e) + "\n")
    return e

def get(ref_id):
    if not REFEREES.exists():
        return None
    latest = None
    for line in REFEREES.read_text().splitlines():
        e = json.loads(line)
        if e["id"] == ref_id:
            latest = e
    return latest

def can_referee(ref_id, subject_scope):
    r = get(ref_id)
    if r is None:
        return False
    if not r["scope"]:
        return True
    return any(s in subject_scope for s in r["scope"])

if __name__ == "__main__":
    import tempfile, os
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    REFEREES = pathlib.Path.cwd() / "build" / "referees.jsonl"
    register("ref-1", "human", "approve", scope=["licence","certification"])
    assert can_referee("ref-1", ["licence"])
    assert not can_referee("ref-1", ["merger"])
    register("ref-2", "agency", "approve")
    assert can_referee("ref-2", ["anything"])
    try:
        register("x", "alien", "approve")
        raise SystemExit("bad kind should fail")
    except ValueError:
        pass
    print("referee OK")
