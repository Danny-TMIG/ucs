\
\
\
import hashlib, json, pathlib, time
LEDGER = pathlib.Path("bench/ledger.json")
class LedgerCorrupted(Exception): pass
def _digest(entry):
    payload = json.dumps({k: v for k, v in entry.items() if k != "hash"}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()
def read_all(verify=True):
    if not LEDGER.exists(): return []
    entries = json.loads(LEDGER.read_text())
    if verify:
        prev = None
        for i, e in enumerate(entries):
            if e.get("prev_hash") != prev:
                raise LedgerCorrupted(f"entry {i} prev_hash mismatch")
            if e.get("hash") != _digest(e):
                raise LedgerCorrupted(f"entry {i} hash mismatch")
            prev = e["hash"]
    return entries
def record(grammar, size, wall, extra=None):
    entries = read_all()
    prev = entries[-1]["hash"] if entries else None
    e = {"grammar": grammar, "size": size, "wall": wall,
         "ts": time.time(), "prev_hash": prev, "extra": extra or {}}
    e["hash"] = _digest(e)
    entries.append(e)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(entries, indent=2))
    return e
def by_grammar(g):
    return [e for e in read_all() if e["grammar"] == g]
if __name__ == "__main__":
    import tempfile, os
    os.chdir(tempfile.mkdtemp()); pathlib.Path("bench").mkdir()
    a = record("py", 100, 0.01); b = record("py", 200, 0.02); c = record("rs", 300, 0.05)
    assert a["prev_hash"] is None and b["prev_hash"] == a["hash"]
    assert c["prev_hash"] == b["hash"]
    entries = read_all(verify=True); assert len(entries) == 3
    entries[1]["wall"] = 9.99
    pathlib.Path("bench/ledger.json").write_text(json.dumps(entries))
    try:
        read_all(verify=True)
    except LedgerCorrupted:
        pass
    else:
        raise SystemExit("ledger should detect tampering")
    print("ledger OK (chain verified, tamper detected)")
