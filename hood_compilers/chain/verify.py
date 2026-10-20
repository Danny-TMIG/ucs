#!/usr/bin/env python3
"""verify.py — standalone verifier for the hood chain.

Verifies each link in order:
  1. body_hash of the file on disk matches the link's body_hash
  2. prev_hash matches the previous link's body_hash
  3. sig recomputes correctly from (prev_hash, hood, body_hash) with the key
  4. chain_sig matches HMAC of the whole chain

Exit code 0 if the entire chain verifies, 1 otherwise.

Usage:
    python3 verify.py                 # verify against current files on disk
    python3 verify.py --strict       # also require no extra files in out/
"""

from __future__ import annotations
import hashlib, hmac, json, sys
from pathlib import Path

import os
HC = Path(__file__).parent.parent
OUT = HC / "out"
CH = Path(os.environ.get("UCS_CHAIN_DIR", Path.home() / ".config" / "ucs")) / "hood_compilers" / "chain"
KEYF = CH / "KEY"


def load_key() -> bytes:
    if not KEYF.exists():
        print(f"FAIL: key missing at {KEYF}")
        sys.exit(2)
    return KEYF.read_bytes()


def body_hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sign(key: bytes, prev: str, hood: str, body: str) -> str:
    return hmac.new(key, f"{prev}|{hood}|{body}".encode(), hashlib.sha256).hexdigest()


def main():
    strict = "--strict" in sys.argv
    chain = json.loads((CH / "chain.json").read_text())
    key = load_key()

    print(f"chain length: {chain['length']}")
    print()

    prev = "genesis"
    failures = []
    for link in chain["links"]:
        idx = link["index"]
        hood = link["hood"]
        f = OUT / link["file"]
        if not f.exists():
            failures.append(f"link {idx} {hood}: file missing")
            print(f"  [{idx:2d}] {hood:20s} MISSING")
            continue
        bh = body_hash(f)
        # 1. body_hash check
        if bh != link["body_hash"]:
            failures.append(f"link {idx} {hood}: body_hash mismatch")
            print(f"  [{idx:2d}] {hood:20s} BODY-CHANGED")
            prev = bh
            continue
        # 2. prev_hash check
        if link["prev_hash"] != prev:
            failures.append(f"link {idx} {hood}: prev_hash mismatch")
            print(f"  [{idx:2d}] {hood:20s} PREV-BROKEN")
            prev = bh
            continue
        # 3. sig check
        want = sign(key, link["prev_hash"], hood, bh)
        if want != link["sig"]:
            failures.append(f"link {idx} {hood}: sig invalid")
            print(f"  [{idx:2d}] {hood:20s} SIG-INVALID")
            prev = bh
            continue
        print(f"  [{idx:2d}] {hood:20s} OK  {bh[:16]}")
        prev = bh

    # 4. chain_sig check
    body = {k: v for k, v in chain.items() if k not in ("chain_sig", "generated_at")}
    blob = json.dumps(body, sort_keys=True).encode()
    want_chain = hmac.new(key, blob, hashlib.sha256).hexdigest()
    if want_chain != chain["chain_sig"]:
        failures.append("chain_sig invalid")
        print()
        print("chain_sig: INVALID")
    else:
        print()
        print(f"chain_sig: OK ({chain['chain_sig'][:16]})")

    if strict:
        expected = set(l["file"] for l in chain["links"])
        present = set(p.name for p in OUT.glob("*.py") if p.name != "__init__.py")
        extra = present - expected
        if extra:
            failures.append(f"extra files: {sorted(extra)}")
            print(f"extra:     {sorted(extra)}")

    print()
    if failures:
        print(f"FAILED: {len(failures)} issue(s)")
        for f in failures[:10]:
            print(f"  {f}")
        sys.exit(1)
    print(f"OK: all {chain['length']} links verified")
    sys.exit(0)


if __name__ == "__main__":
    main()
