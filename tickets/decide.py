import pathlib as _p, sys as _s
_root = _p.Path(__file__).resolve().parent.parent
if str(_root) not in _s.path:
    _s.path.insert(0, str(_root))
import datetime, pathlib
from tickets import store, record

ROOT = pathlib.Path.cwd().resolve()

def _decision_path(state, key):
    return ROOT / "decisions" / state / f"{key}.md"

def _render(env, payload, status):
    lines = [
        f"# {env['key']}",
        "",
        f"**Status:** {status}",
        f"**Date:** {datetime.date.today().isoformat()}",
        f"**spec change:** {payload.get('spec_change', 'none')}",
        "",
        "## Decision",
        payload.get("decision", ""),
        "",
        "## closure_vehicle",
        payload.get("closure_vehicle", ""),
        "",
        "## Residual risk",
        payload.get("residual_risk", "none stated"),
        "",
    ]
    return "\n".join(lines)

REQUIRED_FOR_CLOSE = {"decision", "closure_vehicle"}

def on_transition(key, from_state, to_state, payload=None):
    payload = payload or {}
    env = store.fold(key)
    if env is None:
        raise ValueError(f"ticket {key} does not exist")
    if to_state == "closed":
        missing = REQUIRED_FOR_CLOSE - set(payload)
        if missing:
            raise ValueError(f"closing {key} requires {sorted(missing)}")
        p = _decision_path("closed", key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(_render(env, payload, "Closed"))
        store.append_event(key, {"kind":"transition","ts":datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                 "author":payload.get("author","system"),
                                 "from":from_state,"to":to_state,"payload":payload})
        return str(p)
    if env["type"] in ("decision","rfcs") and to_state == "in_progress":
        p = _decision_path("open", key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(_render(env, payload, "Open"))
        store.append_event(key, {"kind":"transition","ts":datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                 "author":payload.get("author","system"),
                                 "from":from_state,"to":to_state,"payload":payload})
        return str(p)
    store.append_event(key, {"kind":"transition","ts":datetime.datetime.now(datetime.timezone.utc).isoformat(),
                             "author":payload.get("author","system"),
                             "from":from_state,"to":to_state,"payload":payload})
    return None

if __name__ == "__main__":
    import tempfile, os, pathlib
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    store.ROOT = pathlib.Path.cwd() / "tickets"; store.ROOT.mkdir()
    ROOT = pathlib.Path.cwd()
    store.write_envelope("D-1", {"key":"D-1","id":1,"project":{"key":"D"},"type":"decision",
        "status":"open","reporter":"u","creator":"u","created":"t","updated":"t"})
    try:
        on_transition("D-1","open","closed",{})
        raise SystemExit("close without payload should fail")
    except ValueError:
        pass
    p = on_transition("D-1","open","closed",
        {"decision":"x","closure_vehicle":"y","spec_change":"z"})
    assert pathlib.Path(p).exists()
    assert "closure_vehicle" in pathlib.Path(p).read_text()
    store.write_envelope("D-2", {"key":"D-2","id":2,"project":{"key":"D"},"type":"decision",
        "status":"open","reporter":"u","creator":"u","created":"t","updated":"t"})
    p = on_transition("D-2","open","in_progress",{})
    assert pathlib.Path(p).exists()
    print("decide OK")
