
import datetime, json, pathlib

ROOT = pathlib.Path.cwd().resolve()

def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def gather():
    out = {"ts": _now(), "gates": {}}
    for name, path in [
        ("access", "build/access.jsonl"),
        ("incidents", "build/incidents.jsonl"),
        ("consent", "build/consent.jsonl"),
        ("lineage", "build/lineage.json"),
    ]:
        p = ROOT / path
        out["gates"][name] = {"present": p.exists(),
                              "size": p.stat().st_size if p.exists() else 0}
    r = ROOT / "build" / "release.json"
    out["released"] = r.exists()
    if r.exists():
        out["release"] = json.loads(r.read_text())
    return out

def write():
    data = gather()
    p = ROOT / "build" / "compliance.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))
    return p

if __name__ == "__main__":
    import tempfile, os
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    ROOT = pathlib.Path.cwd()
    (ROOT/"build").mkdir()
    (ROOT/"build"/"access.jsonl").write_text('{"ts":"t"}\n')
    p = write()
    assert p.exists()
    d = json.loads(p.read_text())
    assert d["gates"]["access"]["present"] is True
    assert d["released"] is False
    print("report OK")
