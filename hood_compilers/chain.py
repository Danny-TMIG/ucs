"""chain.py — turn the 35 hood modules into a signed chain.

Each link is a hood. Each link stores:
  prev_hash   hash of the previous link (or "genesis" for the first)
  hood        the hood name
  body_hash   sha256 of the hood's source file
  sig         HMAC of (prev_hash || hood || body_hash) with the chain key
  index       position in the chain (0..34)

Verification walks the chain from link 0. Each link:
  - recomputes sig from (prev_hash, hood, body_hash) and checks it matches
  - recomputes prev_hash and checks it matches the previous link's body_hash
  - recomputes body_hash and checks it matches the file on disk

If any check fails, the chain is broken at that link.

Output:
  ~/ucs/hood_compilers/chain/chain.json       the chain (list of links)
  ~/ucs/hood_compilers/chain/chain.sig        HMAC of the whole chain
  ~/ucs/hood_compilers/chain/verify.py        standalone verifier
  ~/ucs/hood_compilers/chain/KEY              the chain key (mode 0600)
"""

from __future__ import annotations
import hashlib, hmac, json, os, secrets, stat, sys, time
from pathlib import Path

import os as _os
HOME = Path.home()
HC = HOME / "ucs" / "hood_compilers"
OUT = HC / "out"
CHAIN_DIR = Path(_os.environ.get("UCS_CHAIN_DIR", HOME / ".config" / "ucs"))
CH = CHAIN_DIR / "hood_compilers" / "chain"
CH.mkdir(parents=True, exist_ok=True)

KEYFILE = CH / "KEY"


# ── key management ────────────────────────────────────────────────────
def load_or_create_key() -> bytes:
    if KEYFILE.exists():
        return KEYFILE.read_bytes()
    key = secrets.token_bytes(32)
    KEYFILE.write_bytes(key)
    KEYFILE.chmod(0o600)
    return key


# ── link construction ─────────────────────────────────────────────────
def body_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sign(key: bytes, prev: str, hood: str, body: str) -> str:
    msg = f"{prev}|{hood}|{body}".encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


# ── chain build ───────────────────────────────────────────────────────
def build_chain() -> dict:
    key = load_or_create_key()
    # deterministic order: alphabetical by hood file stem
    files = sorted(p for p in OUT.glob("*.py") if p.name != "__init__.py")
    links = []
    prev = "genesis"
    for idx, p in enumerate(files):
        hood = p.stem
        bh = body_hash(p)
        sig = sign(key, prev, hood, bh)
        link = {
            "index": idx,
            "hood": hood,
            "file": p.name,
            "body_hash": bh,
            "prev_hash": prev,
            "sig": sig,
        }
        links.append(link)
        prev = bh
    chain = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "length": len(links),
        "links": links,
    }
    # sign the whole chain, excluding the timestamp so the signature
    # is deterministic across rebuilds of the same content
    body = {k: v for k, v in chain.items() if k not in ("chain_sig", "generated_at")}
    blob = json.dumps(body, sort_keys=True).encode()
    chain["chain_sig"] = hmac.new(key, blob, hashlib.sha256).hexdigest()

    (CH / "chain.json").write_text(json.dumps(chain, indent=2))

    # also write the chain signature to a separate file
    (CH / "chain.sig").write_text(chain["chain_sig"] + "\n")
    return chain


# ── standalone verifier ───────────────────────────────────────────────
VERIFIER_SRC = '''#!/usr/bin/env python3
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

CH   = Path(__file__).parent
HC   = CH.parent
OUT  = HC / "out"
KEYF = CH / "KEY"

def load_key() -> bytes:
    if not KEYF.exists():
        print(f"FAIL: key missing at {KEYF}"); sys.exit(2)
    return KEYF.read_bytes()

def body_hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def sign(key: bytes, prev: str, hood: str, body: str) -> str:
    return hmac.new(key, f"{prev}|{hood}|{body}".encode(),
                    hashlib.sha256).hexdigest()

def main():
    strict = "--strict" in sys.argv
    chain = json.loads((CH / "chain.json").read_text())
    key   = load_key()

    print(f"chain length: {chain['length']}")
    print()

    prev = "genesis"
    failures = []
    for link in chain["links"]:
        idx  = link["index"]
        hood = link["hood"]
        f    = OUT / link["file"]
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
    body = {k: v for k, v in chain.items()
            if k not in ("chain_sig", "generated_at")}
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
        present  = set(p.name for p in OUT.glob("*.py")
                       if p.name != "__init__.py")
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
    import sys as _sys
    if "rekey" in _sys.argv:
        if KEYFILE.exists():
            KEYFILE.unlink()
        main()
        print(f"rekey: {KEYFILE}")
    else:
        main()
'''


def write_verifier():
    (CH / "verify.py").write_text(VERIFIER_SRC)
    (CH / "verify.py").chmod(0o755)


# ── main ──────────────────────────────────────────────────────────────
def main():
    print("== hood chain ==")
    chain = build_chain()
    write_verifier()
    print(f"  links:     {chain['length']}")
    print(f"  chain_sig: {chain['chain_sig'][:16]}...")
    print(f"  key:       {KEYFILE}")
    print(f"  chain:     {CH / 'chain.json'}")
    print(f"  verifier:  {CH / 'verify.py'}")
    print()
    print("verify: python3 ~/ucs/hood_compilers/chain/verify.py")
    print("strict: python3 ~/ucs/hood_compilers/chain/verify.py --strict")


if __name__ == "__main__":
    import sys as _sys
    if "rekey" in _sys.argv:
        if KEYFILE.exists():
            KEYFILE.unlink()
        main()
        print(f"rekey: {KEYFILE}")
    else:
        main()
