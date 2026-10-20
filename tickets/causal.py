import pathlib as _p, sys as _s
_root = _p.Path(__file__).resolve().parent.parent
if str(_root) not in _s.path:
    _s.path.insert(0, str(_root))
from tickets import store

def chain(key, max_depth=50):
    """Return the ordered causal chain ending at `key`, most distant first."""
    seen = []
    def walk(k, depth):
        if depth > max_depth or k in seen:
            return
        env = store.fold(k)
        if env is None:
            return
        for l in env.get("links", []):
            if l.get("edge") == "caused_by":
                walk(l["to"], depth + 1)
        seen.append(k)
    walk(key, 0)
    return seen

def root_cause(key, max_depth=50):
    c = chain(key, max_depth)
    return c[0] if c else key

if __name__ == "__main__":
    import tempfile, os, pathlib
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    store.ROOT = pathlib.Path.cwd() / "tickets"; store.ROOT.mkdir()
    for k in ["R","A","B","C"]:
        store.write_envelope(k, {"key":k,"id":ord(k[0]),"project":{"key":"X"},
            "type":"incident","status":"open","reporter":"u","creator":"u",
            "created":"t","updated":"t"})
    store.append_event("A", {"kind":"link","ts":"t","author":"u","from":"A","to":"R","edge":"caused_by"})
    store.append_event("B", {"kind":"link","ts":"t","author":"u","from":"B","to":"A","edge":"caused_by"})
    store.append_event("C", {"kind":"link","ts":"t","author":"u","from":"C","to":"B","edge":"caused_by"})
    assert chain("C") == ["R","A","B","C"], chain("C")
    assert root_cause("C") == "R"
    print("causal OK")
