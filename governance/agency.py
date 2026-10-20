
"""Agency: who may act, on what, under whose authority."""
import datetime, json, pathlib

ROOT = pathlib.Path.cwd().resolve()
AGENCIES = ROOT / "build" / "agencies.jsonl"

def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

KINDS = {"individual", "team", "vendor", "system", "regulator", "certifier"}

def register(agency_id, kind, name, parent=None, authority=None):
    if kind not in KINDS:
        raise ValueError(f"unknown agency kind {kind!r}")
    if not agency_id or not name:
        raise ValueError("agency needs id and name")
    AGENCIES.parent.mkdir(parents=True, exist_ok=True)
    e = {"ts": _now(), "id": agency_id, "kind": kind, "name": name,
         "parent": parent, "authority": authority or [], "action": "register"}
    with AGENCIES.open("a") as f:
        f.write(json.dumps(e) + "\n")
    return e

def get(agency_id):
    if not AGENCIES.exists():
        return None
    latest = None
    for line in AGENCIES.read_text().splitlines():
        e = json.loads(line)
        if e["id"] == agency_id:
            latest = e
    return latest

def chain(agency_id):
    """Return agency + every ancestor."""
    out = []
    cur = get(agency_id)
    while cur:
        out.append(cur)
        cur = get(cur["parent"]) if cur.get("parent") else None
    return out

if __name__ == "__main__":
    import tempfile, os
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    AGENCIES = pathlib.Path.cwd() / "build" / "agencies.jsonl"
    register("vendor-1", "vendor", "Vendor One")
    register("team-1", "team", "Team One", parent="vendor-1", authority=["read","write"])
    assert get("team-1")["parent"] == "vendor-1"
    assert [a["id"] for a in chain("team-1")] == ["team-1", "vendor-1"]
    try:
        register("x", "bad-kind", "x")
        raise SystemExit("bad kind should fail")
    except ValueError:
        pass
    print("agency OK")
