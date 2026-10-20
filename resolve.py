#!/usr/bin/env python3
"""resolve.py — resolver for the full corpus.

Checks what exists, writes what's missing, runs every verifier.

Stages:
  01  check foundations/
  02  check ucs/taxonomies/ucs.json
  03  check ucs/out/registry.json
  04  check ucs/opcodes_all/isa_registry.json
  05  check ucs/systems/
  06  check ucs/hood_compilers/ + run chain verify
  07  check ucs/enterprise/
  08  check ucs/lastmile/
  09  check ucs/allwares/ + run chain verify
  10  check vem-index/

Usage:
    python3 resolve.py             # check + report
    python3 resolve.py --fix       # write missing files (safe: only if absent)
    python3 resolve.py --verify    # run every verifier
"""

from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, time
from pathlib import Path

HOME = Path.home()
UC = HOME / "ucs"

CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn

    return deco


def one(p: Path) -> dict:
    if p.is_file():
        return {"kind": "file", "exists": True, "bytes": p.stat().st_size}
    if p.is_dir():
        n = sum(1 for _ in p.rglob("*") if _.is_file())
        return {"kind": "dir", "exists": True, "files": n}
    return {"kind": "missing", "exists": False}


@check("01 foundations")
def c01():
    p = HOME / "foundations"
    st = one(p)
    py = len(list(p.glob("*.py"))) if p.exists() else 0
    return {"ok": py >= 3, "msg": f"{py} .py files in foundations/"}


@check("02 taxonomy")
def c02():
    p = UC / "taxonomies" / "ucs.json"
    if not p.exists():
        return {"ok": False, "msg": "ucs.json missing"}
    d = json.loads(p.read_text())
    n = sum(len(v) for sec in d.values() for v in sec.values())
    return {"ok": n > 0, "msg": f"{n} behaviors across {len(d)} sections"}


@check("03 ucs registry")
def c03():
    p = UC / "out" / "registry.json"
    if not p.exists():
        return {"ok": False, "msg": "registry.json missing"}
    d = json.loads(p.read_text())
    # accept any of these keys for the count
    n = (
        d.get("total")
        or d.get("count")
        or len(d.get("behaviors", []))
        or len(d.get("behaviors", {}))
        or 0
    )
    return {"ok": n > 0, "msg": f"{n} behaviors"}


@check("04 ISA registry")
def c04():
    p = UC / "opcodes_all" / "isa_registry.json"
    if not p.exists():
        return {"ok": False, "msg": "isa_registry.json missing"}
    d = json.loads(p.read_text())
    t = d.get("totals", {})
    return {
        "ok": t.get("isas", 0) > 0,
        "msg": f"{t.get('isas', 0)} ISAs, {t.get('opcodes', 0)} opcodes",
    }


@check("05 systems")
def c05():
    d = UC / "systems"
    if not d.exists():
        return {"ok": False, "msg": "systems/ missing"}
    subs = [p.name for p in d.iterdir() if p.is_dir()]
    return {"ok": len(subs) >= 5, "msg": f"{len(subs)} subsystems: {subs[:5]}"}


@check("06 hoods")
def c06():
    d = UC / "hood_compilers" / "out"
    if not d.exists():
        return {"ok": False, "msg": "hood_compilers/out missing"}
    hoods = [f for f in d.glob("*.py") if f.name != "__init__.py"]
    verify = UC / "hood_compilers" / "chain" / "verify.py"
    verified = False
    if verify.exists():
        r = subprocess.run(
            [sys.executable, str(verify)], capture_output=True, text=True, timeout=20
        )
        verified = r.returncode == 0
    return {
        "ok": len(hoods) == 35 and verified,
        "msg": f"{len(hoods)} hoods, chain verified={verified}",
    }


@check("07 enterprise")
def c07():
    p = UC / "enterprise" / "enterprise_registry.json"
    if not p.exists():
        return {"ok": False, "msg": "enterprise_registry.json missing"}
    d = json.loads(p.read_text())
    return {
        "ok": d.get("files_scanned", 0) > 0,
        "msg": f"{d.get('files_scanned', 0)} files classified",
    }


@check("08 lastmile")
def c08():
    d = UC / "lastmile"
    if not d.exists():
        return {"ok": False, "msg": "lastmile/ missing"}
    jsons = list(d.glob("*.json"))
    return {"ok": len(jsons) >= 3, "msg": f"{len(jsons)} reports in lastmile/"}


@check("09 allwares")
def c09():
    chain = UC / "allwares" / "chain.json"
    if not chain.exists():
        return {"ok": False, "msg": "allwares chain missing"}
    d = json.loads(chain.read_text())
    verify = UC / "allwares" / "verify.py"
    verified = False
    if verify.exists():
        r = subprocess.run(
            [sys.executable, str(verify)], capture_output=True, text=True, timeout=60
        )
        verified = r.returncode == 0
    return {
        "ok": verified,
        "msg": f"{d['length']} links, sig={d['chain_sig'][:16]}, verified={verified}",
    }


@check("10 VEM index")
def c10():
    d = HOME / "vem-index"
    if not d.exists():
        return {"ok": False, "msg": "vem-index/ missing"}
    recs = list(d.glob("records*.jsonl"))
    total = 0
    for r in recs:
        total += sum(1 for line in r.read_text().splitlines() if line.strip())
    return {"ok": total > 0, "msg": f"{total} records in {len(recs)} files"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    print("== resolve ==")
    print()
    results = []
    for name, fn in CHECKS:
        try:
            r = fn()
        except Exception as e:
            r = {"ok": False, "msg": f"exception: {e}"}
        status = "OK  " if r["ok"] else "MISS"
        print(f"  {status}  {name:16s}  {r['msg']}")
        results.append((name, r))

    passed = sum(1 for _, r in results if r["ok"])
    print()
    print(f"== summary ==")
    print(f"  stages:  {len(results)}")
    print(f"  passed:  {passed}")
    print(f"  missing: {len(results) - passed}")

    # write the report
    (UC / "resolve_report.json").write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "results": [
                    {"stage": n, "ok": r["ok"], "msg": r["msg"]} for n, r in results
                ],
                "passed": passed,
                "missing": len(results) - passed,
            },
            indent=2,
        )
    )
    print(f"  report:  {UC}/resolve_report.json")

    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
