import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from tickets import store

def all_keys():
    root = store.ROOT
    if not root.exists():
        return []
    return [p.name for p in root.iterdir() if p.is_dir()]

def select(**predicates):
    out = []
    for k in all_keys():
        env = store.fold(k)
        if env is None:
            continue
        ok = True
        for field, want in predicates.items():
            v = env.get(field)
            if isinstance(want, (list, tuple, set)):
                if v not in want:
                    ok = False; break
            elif callable(want):
                if not want(v):
                    ok = False; break
            else:
                if v != want:
                    ok = False; break
        if ok:
            out.append(env)
    return out

def linked(key, edge=None):
    env = store.fold(key)
    if env is None:
        return []
    return [l for l in env.get("links", []) if edge is None or l["edge"] == edge]

if __name__ == "__main__":
    import tempfile, os, pathlib
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    store.ROOT = pathlib.Path.cwd() / "tickets"
    store.ROOT.mkdir()
    for k, s in [("A-1","open"), ("A-2","in_progress"), ("A-3","closed")]:
        store.write_envelope(k, {"key":k,"id":int(k.split("-")[1]),
            "project":{"key":"A"},"type":"bug","status":s,
            "reporter":"u","creator":"u","created":"t","updated":"t"})
    assert len(select(status="open")) == 1
    assert len(select(status=("open","in_progress"))) == 2
    assert len(select(type="bug")) == 3
    assert len(select(status=lambda s: s != "closed")) == 2
    print("query OK")
