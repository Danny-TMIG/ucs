import hashlib, json, pathlib

ROOT = pathlib.Path.cwd().resolve() / "tickets"

def _digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, default=str).encode()).hexdigest()

def _ticket_dir(key):
    return ROOT / key

def write_envelope(key, env):
    d = _ticket_dir(key); d.mkdir(parents=True, exist_ok=True)
    (d / "envelope.json").write_text(json.dumps(env, indent=2, default=str))

def read_envelope(key):
    p = _ticket_dir(key) / "envelope.json"
    return json.loads(p.read_text()) if p.exists() else None

def append_event(key, ev):
    d = _ticket_dir(key); d.mkdir(parents=True, exist_ok=True)
    p = d / "events.jsonl"
    prev = None
    if p.exists():
        lines = p.read_text().splitlines()
        if lines:
            prev = json.loads(lines[-1]).get("hash")
    ev = dict(ev)
    ev["prev_hash"] = prev
    ev["hash"] = _digest(ev)
    with p.open("a") as f:
        f.write(json.dumps(ev, default=str) + "\n")
    return ev

def read_events(key):
    p = _ticket_dir(key) / "events.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

def verify_chain(key):
    evs = read_events(key)
    prev = None
    for i, ev in enumerate(evs):
        if ev.get("prev_hash") != prev:
            return False, f"event {i} prev_hash mismatch"
        body = {k: v for k, v in ev.items() if k != "hash"}
        if ev.get("hash") != _digest(body):
            return False, f"event {i} hash mismatch"
        prev = ev["hash"]
    return True, ""

def fold(key):
    env = read_envelope(key)
    if env is None:
        return None
    for ev in read_events(key):
        k = ev["kind"]
        if k == "transition":
            env["status"] = ev["to"]
        elif k == "field_edit":
            to = ev.get("to") or {}
            for f, v in to.items():
                env[f] = v
        elif k == "link":
            env.setdefault("links", []).append({"to": ev["to"], "edge": ev["edge"]})
        elif k == "unlink":
            env["links"] = [l for l in env.get("links", [])
                            if not (l["to"] == ev["to"] and l["edge"] == ev["edge"])]
        env["updated"] = ev["ts"]
    return env

if __name__ == "__main__":
    import tempfile, os
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    ROOT = pathlib.Path.cwd() / "tickets"
    env = {"key":"A-1","id":1,"project":{"key":"A"},"type":"bug","status":"open",
           "reporter":"u","creator":"u","created":"t","updated":"t"}
    write_envelope("A-1", env)
    append_event("A-1", {"kind":"transition","ts":"t1","author":"u","from":"open","to":"in_progress"})
    append_event("A-1", {"kind":"field_edit","ts":"t2","author":"u","from":{},"to":{"priority":"P1"}})
    append_event("A-1", {"kind":"link","ts":"t3","author":"u","from":"A-1","to":"A-2","edge":"blocks"})
    ok, err = verify_chain("A-1"); assert ok, err
    f = fold("A-1")
    assert f["status"] == "in_progress", f
    assert f["priority"] == "P1", f
    assert f["links"] == [{"to":"A-2","edge":"blocks"}], f
    print("store OK")
