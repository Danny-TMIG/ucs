import pathlib as _p, sys as _s
_root = _p.Path(__file__).resolve().parent.parent
if str(_root) not in _s.path:
    _s.path.insert(0, str(_root))
import pathlib
from tickets import store, record

def check_chain(key):
    ok, reason = store.verify_chain(key)
    if not ok:
        return [f"{key}: {reason}"]
    return []

def check_edges():
    errs = []
    for key in store.all_keys() if hasattr(store, "all_keys") else [p.name for p in store.ROOT.iterdir() if p.is_dir()]:
        env = store.fold(key)
        if env is None:
            continue
        for l in env.get("links", []):
            target = l.get("to")
            edge = l.get("edge")
            if edge not in record.EDGE:
                errs.append(f"{key}: unknown edge {edge!r}")
                continue
            tenv = store.fold(target)
            if tenv is None:
                errs.append(f"{key}: edge {edge} points at missing {target}")
                continue
            inv = record.EDGE[edge]
            inverse_present = any(x.get("edge") == inv and x.get("to") == key for x in tenv.get("links", []))
            if not inverse_present:
                errs.append(f"{key}: {edge} -> {target} missing inverse {inv}")
    return errs

def check_transitions():
    errs = []
    keys = [p.name for p in store.ROOT.iterdir() if p.is_dir()] if store.ROOT.exists() else []
    for key in keys:
        env = store.read_envelope(key)
        if env is None:
            continue
        cur = env.get("status")
        for ev in store.read_events(key):
            if ev["kind"] != "transition":
                continue
            f, t = ev.get("from"), ev.get("to")
            if f != cur:
                errs.append(f"{key}: transition from {f} but actual state {cur}")
            bad = record.validate_transition(f, t)
            if bad:
                errs.append(f"{key}: {bad[0]}")
            cur = t
    return errs

def check_ancestors():
    errs = []
    keys = [p.name for p in store.ROOT.iterdir() if p.is_dir()] if store.ROOT.exists() else []
    for key in keys:
        seen = set()
        cur = key
        while True:
            env = store.fold(cur)
            if env is None:
                break
            parent = env.get("parent")
            if not parent:
                break
            if parent in seen or parent == key:
                errs.append(f"{key}: ancestor cycle through {parent}")
                break
            seen.add(parent)
            cur = parent
    return errs

def check_all():
    errs = []
    keys = [p.name for p in store.ROOT.iterdir() if p.is_dir()] if store.ROOT.exists() else []
    for key in keys:
        errs.extend(check_chain(key))
    errs.extend(check_edges())
    errs.extend(check_transitions())
    errs.extend(check_ancestors())
    return errs

if __name__ == "__main__":
    import tempfile, os, pathlib
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    store.ROOT = pathlib.Path.cwd() / "tickets"
    store.ROOT.mkdir()
    for k, s in [("A-1","open"), ("A-2","open")]:
        store.write_envelope(k, {"key":k,"id":int(k.split("-")[1]),
            "project":{"key":"A"},"type":"bug","status":s,
            "reporter":"u","creator":"u","created":"t","updated":"t"})
    store.append_event("A-1", {"kind":"link","ts":"t","author":"u","from":"A-1","to":"A-2","edge":"blocks"})
    store.append_event("A-2", {"kind":"link","ts":"t","author":"u","from":"A-2","to":"A-1","edge":"blocked_by"})
    store.append_event("A-1", {"kind":"transition","ts":"t","author":"u","from":"open","to":"in_progress"})
    assert check_all() == [], check_all()
    store.append_event("A-1", {"kind":"link","ts":"t","author":"u","from":"A-1","to":"A-2","edge":"relates_to"})
    assert check_edges(), "missing inverse should fail"
    print("invariants OK")
