
"""Reviewer: a referee acting in a review capacity, with a verdict."""
import datetime, json, pathlib
import sys as _s, pathlib as _p
_root = _p.Path(__file__).resolve().parent.parent
if str(_root) not in _s.path:
    _s.path.insert(0, str(_root))

ROOT = pathlib.Path.cwd().resolve()
REVIEWS = ROOT / "build" / "reviews.jsonl"

def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

VERDICTS = {"approve", "reject", "abstain", "changes_requested"}

def submit(subject, reviewer, verdict, comment):
    if verdict not in VERDICTS:
        raise ValueError(f"unknown verdict {verdict!r}")
    if not reviewer:
        raise ValueError("review needs reviewer")
    REVIEWS.parent.mkdir(parents=True, exist_ok=True)
    e = {"ts": _now(), "subject": subject, "reviewer": reviewer,
         "verdict": verdict, "comment": comment, "action": "submit"}
    with REVIEWS.open("a") as f:
        f.write(json.dumps(e) + "\n")
    return e

def tally(subject, required=1):
    """Return (passed, verdicts)."""
    if not REVIEWS.exists():
        return False, {}
    counts = {}
    for line in REVIEWS.read_text().splitlines():
        e = json.loads(line)
        if e["subject"] != subject:
            continue
        counts[e["verdict"]] = counts.get(e["verdict"], 0) + 1
    return counts.get("approve", 0) >= required and counts.get("reject", 0) == 0, counts

if __name__ == "__main__":
    import tempfile, os
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    REVIEWS = pathlib.Path.cwd() / "build" / "reviews.jsonl"
    submit("PROP-1", "alice", "approve", "ok")
    ok, counts = tally("PROP-1", required=1)
    assert ok and counts == {"approve": 1}
    submit("PROP-1", "bob", "reject", "no")
    ok, counts = tally("PROP-1", required=1)
    assert not ok
    try:
        submit("PROP-1", "alice", "maybe", "x")
        raise SystemExit("bad verdict should fail")
    except ValueError:
        pass
    print("reviewer OK")
