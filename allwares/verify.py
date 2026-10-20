#!/usr/bin/env python3
import hashlib, hmac, json, re, sys
from pathlib import Path

AW = Path(__file__).parent
KEYF = AW / "KEY"


def load_key():
    if not KEYF.exists():
        print(f"FAIL: key missing at {KEYF}")
        sys.exit(2)
    return KEYF.read_bytes()


def sha256_of(t):
    return hashlib.sha256(t.encode()).hexdigest()


def sign(k, i, a, s):
    return hmac.new(k, f"{i}|{a}|{s}".encode(), hashlib.sha256).hexdigest()


def main():
    chain = json.loads((AW / "chain.json").read_text())
    key = load_key()
    print(f"chain length: {chain['length']}")
    prev = "genesis"
    fails = []
    for link in chain["links"]:
        # recompute from the ware file on disk
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", link["id"])[:180]
        ware_file = AW / "wares" / f"{safe}.json"
        if not ware_file.exists():
            fails.append(f"link {link['index']}: ware file missing")
            prev = link["body_hash"]
            continue
        want_body = hashlib.sha256(ware_file.read_bytes()).hexdigest()
        if want_body != link["body_hash"]:
            fails.append(f"link {link['index']}: body mismatch")
            prev = link["body_hash"]
            continue
        if link["prev_hash"] != prev:
            fails.append(f"link {link['index']}: prev mismatch")
            prev = link["body_hash"]
            continue
        want_sig = sign(key, link["id"], link["body_hash"], link["body_hash"])
        if want_sig != link["sig"]:
            fails.append(f"link {link['index']}: sig invalid")
            prev = link["body_hash"]
            continue
        prev = link["body_hash"]
    body = {k: v for k, v in chain.items() if k not in ("chain_sig", "generated_at")}
    blob = json.dumps(body, sort_keys=True).encode()
    if hmac.new(key, blob, hashlib.sha256).hexdigest() != chain["chain_sig"]:
        fails.append("chain_sig invalid")
        print(f"chain_sig: INVALID")
    else:
        print(f"chain_sig: OK ({chain['chain_sig'][:16]})")
    print()
    if fails:
        print(f"FAILED: {len(fails)}")
        sys.exit(1)
    print(f"OK: all {chain['length']} links verified")
    sys.exit(0)


if __name__ == "__main__":
    main()
