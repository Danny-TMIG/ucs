#!/usr/bin/env python3
"""arch-check.py — nine-family scorecard as machine check.
A family is present iff its files exist. No placeholders."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
FAMILIES = {
    1: ("identity/boundary", [ROOT/"specs/intent/intent.schema.json"]),
    2: ("composition", [ROOT/"specs/contracts/payload.schema.json", ROOT/"spec/payload.py"]),
    3: ("dependency", [ROOT/"spec/atlas.py"]),
    4: ("behavior/state", [ROOT/"spec/state.py"]),
    5: ("invariants", [ROOT/"spec/invariants.py"]),
    6: ("failure", [ROOT/"spec/revise.py"]),
    7: ("change/version", [ROOT/"spec/version.py", ROOT/"spec/migrate.py"]),
    8: ("resource/env", [ROOT/"runtime.json"]),
    9: ("verification", [ROOT/"spec/parallel_check.py"]),
}

def evaluate(families):
    results = {}
    for n, (name, files) in families.items():
        missing = [str(f.relative_to(ROOT)) for f in files if not f.exists()]
        results[n] = {"name": name, "ok": not missing, "missing": missing}
    return results

def main():
    results = evaluate(FAMILIES)
    print(json.dumps(results, indent=2))
    bad = [n for n, r in results.items() if not r["ok"]]
    if bad:
        print(f"\nfamilies with gaps: {bad}"); return 1
    print("\nall nine families present"); return 0

if __name__ == "__main__":
    real_rc = main()
    # negative test: a family with a nonexistent file must fail
    fam = dict(FAMILIES)
    fam[99] = ("negative", [ROOT/"spec" / "__does_not_exist__.py"])
    neg_results = evaluate(fam)
    assert neg_results[99]["ok"] is False, neg_results[99]
    assert neg_results[99]["missing"], neg_results[99]
    # positive: every real family file exists
    for n, r in evaluate(FAMILIES).items():
        assert r["ok"] is True, (n, r)
    print(f"\narch-check negative test OK: family 99 detected missing file")
    sys.exit(real_rc)
