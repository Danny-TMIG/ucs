#!/usr/bin/env python3
"""allwares.py — automated creation of all wares."""

import argparse, hashlib, hmac, json, os, re, secrets, sys, time
from collections import defaultdict
from dataclasses import dataclass, asdict, field
from pathlib import Path

import os as _os
HOME = Path.home()
UC = HOME / "ucs"
CHAIN_DIR = Path(_os.environ.get("UCS_CHAIN_DIR", HOME / ".config" / "ucs"))
AW = CHAIN_DIR / "allwares"
OUT = AW / "wares"
FLEET = AW / "fleet"
KEYF = AW / "KEY"

for d in (AW, OUT, FLEET):
    d.mkdir(parents=True, exist_ok=True)


@dataclass
class Ware:
    id: str
    family: str
    kind: str
    source: str
    address: str
    callable_: bool
    call_kind: str
    attested: bool
    attestation: str
    links: list = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d["callable"] = d.pop("callable_")
        return d


def load_or_create_key():
    if KEYF.exists():
        return KEYF.read_bytes()
    k = secrets.token_bytes(32)
    KEYF.write_bytes(k)
    KEYF.chmod(0o600)
    return k


def sha256_of(text):
    return hashlib.sha256(text.encode()).hexdigest()


def sign(key, ware_id, address, source):
    return hmac.new(
        key, f"{ware_id}|{address}|{source}".encode(), hashlib.sha256
    ).hexdigest()


def wares_from_ucs():
    p = UC / "out" / "registry.json"
    if not p.exists():
        return []
    reg = json.loads(p.read_text())
    out = []
    for b in reg.get("behaviors", []):
        key = b["key"]
        cat = b["cat"]
        name = b["name"]
        kind = b["kind"]
        source = f"ucs:{key}"
        out.append(
            Ware(
                id=key,
                family=f"ucs:{kind}",
                kind=kind,
                source=source,
                address=sha256_of(source),
                callable_=True,
                call_kind="python",
                attested=False,
                attestation="",
                links=["isa:*"],
            )
        )
    return out


def wares_from_isa():
    p = UC / "opcodes_all" / "isa_registry.json"
    if not p.exists():
        return []
    reg = json.loads(p.read_text())
    out = []
    for name, d in sorted(reg.get("isas", {}).items()):
        source = f"isa:{name}:{d.get('source', '')}:{len(d.get('opcodes', []))}"
        out.append(
            Ware(
                id=f"isa:{name}",
                family="isa:registry",
                kind="isa",
                source=source,
                address=sha256_of(source),
                callable_=True,
                call_kind="python",
                attested=False,
                attestation="",
                links=["ucs:*"],
            )
        )
    return out


def wares_from_hoods():
    hc = UC / "hood_compilers" / "out"
    if not hc.exists():
        return []
    out = []
    for f in sorted(hc.glob("*.py")):
        if f.name == "__init__.py":
            continue
        source = f.read_text()
        cls = f.stem.capitalize()
        out.append(
            Ware(
                id=f"hood:{cls}",
                family="hood:taxonomy",
                kind="hood",
                source=f"hood:{cls}",
                address=sha256_of(source),
                callable_=True,
                call_kind="python",
                attested=False,
                attestation="",
                links=["chain:hoods"],
            )
        )
    return out


def wares_from_enterprise():
    p = UC / "enterprise" / "enterprise_registry.json"
    if not p.exists():
        return []
    reg = json.loads(p.read_text())
    out = []
    for r in reg.get("per_file", []):
        path = r["path"]
        source = f"ent:{path}:{r.get('size', 0)}"
        out.append(
            Ware(
                id=f"ent:{path}",
                family="enterprise:artifact",
                kind="artifact",
                source=source,
                address=sha256_of(source),
                callable_=path.endswith((".py", ".sh")),
                call_kind="python" if path.endswith(".py") else "data",
                attested=False,
                attestation="",
                links=[f"forbes:{s}" for s in r.get("forbes", [])]
                + [f"gartner:{g}" for g in r.get("gartner", [])],
            )
        )
    return out


def wares_from_vem():
    out = []
    for records in sorted((HOME / "vem-index").glob("records*.jsonl")):
        for line in records.read_text().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            vid = r.get("vid", "")
            path = r.get("path", "")
            out.append(
                Ware(
                    id=f"vem:{vid[:16]}",
                    family="vem:index",
                    kind="vem-entry",
                    source=f"vem:{vid}",
                    address=vid or sha256_of(path),
                    callable_=False,
                    call_kind="data",
                    attested=False,
                    attestation="",
                    links=[f"ent:{path}"],
                )
            )
    return out


def build_chain(key, wares):
    wares = sorted(wares, key=lambda w: w.id)
    links = []
    prev = "genesis"
    for i, w in enumerate(wares):
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", w.id)[:180]
        ware_file = OUT / f"{safe}.json"
        if not ware_file.exists():
            continue
        body = hashlib.sha256(ware_file.read_bytes()).hexdigest()
        sig = sign(key, w.id, body, body)
        links.append(
            {
                "index": i,
                "id": w.id,
                "family": w.family,
                "body_hash": body,
                "prev_hash": prev,
                "sig": sig,
            }
        )
        prev = body
    chain = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "length": len(links),
        "links": links,
    }
    body = {k: v for k, v in chain.items() if k != "generated_at"}
    blob = json.dumps(body, sort_keys=True).encode()
    chain["chain_sig"] = hmac.new(key, blob, hashlib.sha256).hexdigest()
    (AW / "chain.json").write_text(json.dumps(chain, indent=2))
    (AW / "chain.sig").write_text(chain["chain_sig"])
    return chain


VERIFIER = r"""#!/usr/bin/env python3
import hashlib, hmac, json, re, sys
from pathlib import Path

AW = Path(__file__).parent
KEYF = AW / "KEY"

def load_key():
    if not KEYF.exists():
        print(f"FAIL: key missing at {KEYF}"); sys.exit(2)
    return KEYF.read_bytes()

def sha256_of(t): return hashlib.sha256(t.encode()).hexdigest()
def sign(k, i, a, s):
    return hmac.new(k, f"{i}|{a}|{s}".encode(), hashlib.sha256).hexdigest()

def main():
    chain = json.loads((AW / "chain.json").read_text())
    key = load_key()
    print(f"chain length: {chain['length']}")
    prev = "genesis"; fails = []
    for link in chain["links"]:
        # recompute from the ware file on disk
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", link["id"])[:180]
        ware_file = AW / "wares" / f"{safe}.json"
        if not ware_file.exists():
            fails.append(f"link {link['index']}: ware file missing")
            prev = link["body_hash"]; continue
        want_body = hashlib.sha256(ware_file.read_bytes()).hexdigest()
        if want_body != link["body_hash"]:
            fails.append(f"link {link['index']}: body mismatch")
            prev = link["body_hash"]; continue
        if link["prev_hash"] != prev:
            fails.append(f"link {link['index']}: prev mismatch")
            prev = link["body_hash"]; continue
        want_sig = sign(key, link["id"], link["body_hash"], link["body_hash"])
        if want_sig != link["sig"]:
            fails.append(f"link {link['index']}: sig invalid")
            prev = link["body_hash"]; continue
        prev = link["body_hash"]
    body = {k: v for k, v in chain.items()
            if k not in ("chain_sig", "generated_at")}
    blob = json.dumps(body, sort_keys=True).encode()
    if hmac.new(key, blob, hashlib.sha256).hexdigest() != chain["chain_sig"]:
        fails.append("chain_sig invalid")
        print(f"chain_sig: INVALID")
    else:
        print(f"chain_sig: OK ({chain['chain_sig'][:16]})")
    print()
    if fails:
        print(f"FAILED: {len(fails)}"); sys.exit(1)
    print(f"OK: all {chain['length']} links verified"); sys.exit(0)

if __name__ == "__main__":
    main()
"""


def build_all():
    key = load_or_create_key()
    print("[1/5] collecting wares ...")
    sources = {
        "ucs": wares_from_ucs(),
        "isa": wares_from_isa(),
        "hood": wares_from_hoods(),
        "enterprise": wares_from_enterprise(),
        "vem": wares_from_vem(),
    }
    for name, ws in sources.items():
        print(f"      {name:12s} {len(ws):5d}")
    all_wares = []
    for ws in sources.values():
        all_wares.extend(ws)
    print(f"      total        {len(all_wares)}")
    print("[2/5] attesting ...")
    for w in all_wares:
        w.attestation = sign(key, w.id, w.address, w.source)
        w.attested = True
    print("[3/5] writing wares ...")
    by_family = defaultdict(list)
    for w in all_wares:
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", w.id)[:180]
        ware_file = OUT / f"{safe}.json"
        ware_file.write_text(json.dumps(w.to_dict(), indent=2))
        by_family[w.family].append(w.id)
    print("[4/5] writing fleets ...")
    fleet_index = {}
    for family, ids in sorted(by_family.items()):
        fam_dir = FLEET / re.sub(r"[^A-Za-z0-9._-]+", "_", family)
        fam_dir.mkdir(parents=True, exist_ok=True)
        (fam_dir / "index.json").write_text(
            json.dumps({"family": family, "count": len(ids), "ids": ids}, indent=2)
        )
        fleet_index[family] = {"count": len(ids), "dir": str(fam_dir.relative_to(HOME))}
    print("[5/5] matrix + chain ...")
    matrix = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ware_count": len(all_wares),
        "families": {f: len(ids) for f, ids in sorted(by_family.items())},
        "fleets": fleet_index,
        "by_kind": {},
        "by_call_kind": {},
    }
    for w in all_wares:
        matrix["by_kind"][w.kind] = matrix["by_kind"].get(w.kind, 0) + 1
        matrix["by_call_kind"][w.call_kind] = (
            matrix["by_call_kind"].get(w.call_kind, 0) + 1
        )
    (AW / "matrix.json").write_text(json.dumps(matrix, indent=2))
    chain = build_chain(key, all_wares)
    (AW / "verify.py").write_text(VERIFIER)
    (AW / "verify.py").chmod(0o755)
    return {
        "wares": len(all_wares),
        "families": len(by_family),
        "chain_sig": chain["chain_sig"],
    }


def report():
    p = AW / "matrix.json"
    if not p.exists():
        print("no matrix; run build first")
        return {}
    m = json.loads(p.read_text())
    print(f"== allwares ==")
    print(f"  wares:    {m['ware_count']}")
    print(f"  families: {len(m['families'])}")
    print()
    print("  by family:")
    for fam, n in sorted(m["families"].items(), key=lambda kv: -kv[1]):
        print(f"    {fam:28s} {n:5d}")
    print()
    print("  by kind:")
    for k, n in sorted(m["by_kind"].items(), key=lambda kv: -kv[1]):
        print(f"    {k:16s} {n:5d}")
    print()
    print("  by call kind:")
    for k, n in sorted(m["by_call_kind"].items(), key=lambda kv: -kv[1]):
        print(f"    {k:16s} {n:5d}")
    c = AW / "chain.json"
    if c.exists():
        ch = json.loads(c.read_text())
        print()
        print(f"  chain:    {ch['length']} links, sig={ch['chain_sig'][:16]}")
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "verify", "report", "cycle", "rekey"])
    args = ap.parse_args()
    import subprocess

    if args.cmd == "build":
        build_all()
    elif args.cmd == "rekey":
        if KEYF.exists():
            KEYF.unlink()
        build_all()
        print(f"rekey: {KEYF}")
    elif args.cmd == "verify":
        sys.exit(subprocess.run([sys.executable, str(AW / "verify.py")]).returncode)
    elif args.cmd == "report":
        report()
    elif args.cmd == "cycle":
        build_all()
        print()
        rc = subprocess.run([sys.executable, str(AW / "verify.py")]).returncode
        print()
        report()
        sys.exit(rc)


if __name__ == "__main__":
    main()
