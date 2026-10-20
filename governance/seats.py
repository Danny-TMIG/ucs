
"""Seats: finite slots that hold an agency or referee for a term."""
import datetime, json, pathlib

ROOT = pathlib.Path.cwd().resolve()
SEATS = ROOT / "build" / "seats.jsonl"

def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def define(seat_id, capacity, purpose):
    if capacity < 1:
        raise ValueError("capacity must be >= 1")
    if not seat_id or not purpose:
        raise ValueError("seat needs id and purpose")
    SEATS.parent.mkdir(parents=True, exist_ok=True)
    e = {"ts": _now(), "seat": seat_id, "capacity": capacity,
         "purpose": purpose, "action": "define"}
    with SEATS.open("a") as f:
        f.write(json.dumps(e) + "\n")
    return e

def occupy(seat_id, holder, expires=None):
    if not holder:
        raise ValueError("holder required")
    occupied, capacity = state(seat_id)
    if occupied >= capacity:
        raise ValueError(f"seat {seat_id} full ({occupied}/{capacity})")
    e = {"ts": _now(), "seat": seat_id, "holder": holder,
         "expires": expires, "action": "occupy"}
    with SEATS.open("a") as f:
        f.write(json.dumps(e) + "\n")
    return e

def vacate(seat_id, holder):
    e = {"ts": _now(), "seat": seat_id, "holder": holder, "action": "vacate"}
    with SEATS.open("a") as f:
        f.write(json.dumps(e) + "\n")
    return e

def state(seat_id, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if not SEATS.exists():
        return 0, 0
    capacity = 0
    holders = {}
    for line in SEATS.read_text().splitlines():
        e = json.loads(line)
        if e["seat"] != seat_id:
            continue
        if e["action"] == "define":
            capacity = e["capacity"]
        elif e["action"] == "occupy":
            exp = e.get("expires")
            if exp:
                dt = datetime.datetime.fromisoformat(exp)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                if dt < now:
                    continue
            holders[e["holder"]] = e
        elif e["action"] == "vacate":
            holders.pop(e["holder"], None)
    return len(holders), capacity

if __name__ == "__main__":
    import tempfile, os
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    SEATS = pathlib.Path.cwd() / "build" / "seats.jsonl"
    define("board", 2, "review board")
    occupy("board", "alice")
    occupy("board", "bob")
    assert state("board") == (2, 2)
    try:
        occupy("board", "carol")
        raise SystemExit("full seat should reject")
    except ValueError:
        pass
    vacate("board", "alice")
    occupy("board", "carol")
    assert state("board") == (2, 2)
    print("seats OK")
