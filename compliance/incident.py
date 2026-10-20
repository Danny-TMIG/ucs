
import datetime, json, pathlib

ROOT = pathlib.Path.cwd().resolve()
INCIDENTS = ROOT / "build" / "incidents.jsonl"

def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def open_incident(inc_id, severity, summary, reporter):
    if severity not in ("sev1","sev2","sev3","sev4"):
        raise ValueError(f"bad severity {severity!r}")
    INCIDENTS.parent.mkdir(parents=True, exist_ok=True)
    e = {"ts": _now(), "id": inc_id, "severity": severity, "summary": summary,
         "reporter": reporter, "action": "open"}
    with INCIDENTS.open("a") as f:
        f.write(json.dumps(e) + "\n")
    return e

def note(inc_id, author, text):
    e = {"ts": _now(), "id": inc_id, "author": author, "text": text, "action": "note"}
    with INCIDENTS.open("a") as f:
        f.write(json.dumps(e) + "\n")
    return e

def close(inc_id, by, resolution, spec_change, residual_risk):
    for f_ in ("resolution", "spec_change", "residual_risk"):
        if not locals()[f_]:
            raise ValueError(f"closing incident requires {f_}")
    e = {"ts": _now(), "id": inc_id, "action": "close", "by": by,
         "resolution": resolution, "spec_change": spec_change,
         "residual_risk": residual_risk}
    with INCIDENTS.open("a") as f:
        f.write(json.dumps(e) + "\n")
    return e

def status(inc_id):
    if not INCIDENTS.exists():
        return "unknown"
    state = "unknown"
    for line in INCIDENTS.read_text().splitlines():
        e = json.loads(line)
        if e["id"] != inc_id:
            continue
        if e["action"] == "open":
            state = "open"
        elif e["action"] == "close":
            state = "closed"
    return state

if __name__ == "__main__":
    import tempfile, os
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    INCIDENTS = pathlib.Path.cwd() / "build" / "incidents.jsonl"
    open_incident("INC-1", "sev2", "outage", "alice")
    assert status("INC-1") == "open"
    try:
        close("INC-1", "alice", "", "", "")
        raise SystemExit("close without fields should fail")
    except ValueError:
        pass
    close("INC-1", "alice", "fixed", "loop.py guard", "single-maintainer")
    assert status("INC-1") == "closed"
    print("incident OK")
