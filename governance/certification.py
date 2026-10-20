
"""Certification: an agency asserts a claim about another entity."""
import datetime, json, pathlib

ROOT = pathlib.Path.cwd().resolve()
CERTS = ROOT / "build" / "certs.jsonl"

def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

CLAIMS = {"conformance", "security", "quality", "compliance", "fitness"}

def issue(cert_id, subject, claim, standard, certifier, evidence=None):
    if claim not in CLAIMS:
        raise ValueError(f"unknown claim {claim!r}")
    if not all([cert_id, subject, claim, standard, certifier]):
        raise ValueError("certification needs id, subject, claim, standard, certifier")
    CERTS.parent.mkdir(parents=True, exist_ok=True)
    e = {"ts": _now(), "id": cert_id, "subject": subject, "claim": claim,
         "standard": standard, "certifier": certifier,
         "evidence": evidence or [], "action": "issue"}
    with CERTS.open("a") as f:
        f.write(json.dumps(e) + "\n")
    return e

def withdraw(cert_id, by, reason):
    if not by or not reason:
        raise ValueError("withdraw needs by and reason")
    e = {"ts": _now(), "id": cert_id, "action": "withdraw", "by": by, "reason": reason}
    with CERTS.open("a") as f:
        f.write(json.dumps(e) + "\n")
    return e

def valid(cert_id):
    if not CERTS.exists():
        return False
    state = False
    for line in CERTS.read_text().splitlines():
        e = json.loads(line)
        if e["id"] != cert_id:
            continue
        if e["action"] == "issue":
            state = True
        elif e["action"] == "withdraw":
            state = False
    return state

def by_subject(subject, claim=None):
    if not CERTS.exists():
        return []
    out = []
    for line in CERTS.read_text().splitlines():
        e = json.loads(line)
        if e["action"] != "issue" or e["subject"] != subject:
            continue
        if claim and e["claim"] != claim:
            continue
        if valid(e["id"]):
            out.append(e)
    return out

if __name__ == "__main__":
    import tempfile, os
    tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
    CERTS = pathlib.Path.cwd() / "build" / "certs.jsonl"
    issue("C-1", "team-1", "security", "SOC2", "regulator")
    assert valid("C-1") is True
    assert len(by_subject("team-1")) == 1
    withdraw("C-1", "regulator", "lapsed")
    assert valid("C-1") is False
    assert by_subject("team-1") == []
    try:
        issue("C-2", "team-1", "nonsense", "X", "Y")
        raise SystemExit("bad claim should fail")
    except ValueError:
        pass
    print("certification OK")
