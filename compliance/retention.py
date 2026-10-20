
import datetime, pathlib

ROOT = pathlib.Path.cwd().resolve()

POLICY = {
    "spec": {"days": 3650},
    "bench": {"days": 365},
    "ci": {"days": 3650},
    "hats": {"days": 3650},
    "tickets": {"days": 2555},
    "decisions": {"days": None},
    "build": {"days": 7},
    "logs": {"days": 30},
    "tmp": {"days": 1},
}

def classify(path):
    try:
        top = path.relative_to(ROOT).parts[0]
    except (ValueError, IndexError):
        return "unknown"
    return top if top in POLICY else "unknown"

def expired(path, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    top = classify(path)
    if top == "unknown":
        return False
    days = POLICY[top]["days"]
    if days is None:
        return False
    mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime, tz=datetime.timezone.utc)
    return (now - mtime).days > days

if __name__ == "__main__":
    import tempfile, os, time
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    ROOT = pathlib.Path.cwd()
    for d in ["spec", "logs", "decisions"]:
        (ROOT/d).mkdir()
    f1 = ROOT/"spec"/"a.py"; f1.write_text("x")
    f2 = ROOT/"logs"/"old.log"; f2.write_text("y")
    f3 = ROOT/"decisions"/"GOV-1.md"; f3.write_text("z")
    old = time.time() - 60*86400
    os.utime(f2, (old, old))
    assert expired(f1) is False
    assert expired(f2) is True
    assert expired(f3) is False
    print("retention OK")
