
import hashlib, json, pathlib

ROOT = pathlib.Path.cwd().resolve()
LINEAGE = ROOT / "build" / "lineage.json"

def _digest(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def record(artifact, sources, tool, version="1"):
    """artifact produced from sources by tool."""
    entry = {
        "artifact": str(artifact),
        "sources": [str(s) for s in sources],
        "source_hashes": [_digest(pathlib.Path(s)) for s in sources if pathlib.Path(s).exists()],
        "tool": tool,
        "version": version,
    }
    data = json.loads(LINEAGE.read_text()) if LINEAGE.exists() else []
    data.append(entry)
    LINEAGE.parent.mkdir(parents=True, exist_ok=True)
    LINEAGE.write_text(json.dumps(data, indent=2))
    return entry

def verify(artifact):
    data = json.loads(LINEAGE.read_text()) if LINEAGE.exists() else []
    for e in reversed(data):
        if e["artifact"] == str(artifact):
            for s, h in zip(e["sources"], e["source_hashes"]):
                if not pathlib.Path(s).exists() or _digest(pathlib.Path(s)) != h:
                    return False, f"source changed: {s}"
            return True, ""
    return False, "no lineage record"

if __name__ == "__main__":
    import tempfile, os
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    LINEAGE = pathlib.Path.cwd() / "build" / "lineage.json"
    src = pathlib.Path.cwd() / "src.py"; src.write_text("x = 1")
    art = pathlib.Path.cwd() / "out.json"; art.write_text("{}")
    record(art, [src], "compile.py")
    ok, err = verify(art)
    assert ok, err
    src.write_text("x = 2")
    ok, err = verify(art)
    assert not ok and "changed" in err
    print("lineage OK")
