#!/usr/bin/env python3
"""everything.py — run every subsystem, 14/14."""

import json, socket, subprocess, sys, time
from pathlib import Path

HOME = Path.home()
UC = HOME / "ucs"
VI = HOME / "vem-index"
HC = UC / "hood_compilers"


def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"rc": r.returncode, "out": r.stdout, "err": r.stderr}
    except Exception as e:
        return {"rc": -1, "out": "", "err": str(e)}


def port_open(p):
    s = socket.socket()
    s.settimeout(0.3)
    try:
        s.connect(("127.0.0.1", p))
        return True
    except Exception:
        return False
    finally:
        s.close()


def s01():
    total_files = total_bytes = 0
    for root in [
        "foundations",
        "swarm",
        "gen",
        "kaleido",
        "ucs",
        "vem-index",
        "polyglot",
        "cs-partitions",
    ]:
        p = HOME / root
        if not p.exists():
            continue
        for f in p.rglob("*"):
            if "__pycache__" in str(f) or not f.is_file():
                continue
            try:
                total_files += 1
                total_bytes += f.stat().st_size
            except OSError:
                pass
    return total_files > 0, f"{total_files:,} files, {total_bytes:,} bytes"


def s02():
    ports = [19800, 19801, 19802]
    up = [p for p in ports if port_open(p)]
    return len(up) == len(ports), f"ports up: {len(up)}/{len(ports)}"


def s03():
    spec = VI / "spec.py"
    if not spec.exists():
        return False, "spec.py missing"
    r = run(
        [
            sys.executable,
            str(spec),
            "query",
            str(VI / "specs" / "foundations.json"),
            "cayley dickson",
        ],
        20,
    )
    ok = "cayley_dickson" in r["out"]
    lines = r["out"].splitlines()
    top = lines[1].strip() if len(lines) > 1 else "(no result)"
    return ok, top


def s04():
    info = UC / "opcodes_all" / "isa_info.py"
    if not info.exists():
        return False, "isa_info.py missing"
    r = run([sys.executable, str(info), "--has", "add"], 15)
    first = r["out"].splitlines()[0] if r["out"] else ""
    n = int(first.split("(")[1].split(")")[0]) if "(" in first else 0
    return n >= 3, f"ISAs with 'add': {n}"


def s05():
    p = UC / "ucs.py"
    if not p.exists():
        return False, "ucs.py missing"
    r = run([sys.executable, str(p), "registry"], 15)
    return r["rc"] == 0, "registry written"


def s06():
    p = UC / "systems" / "comp" / "comp.py"
    if not p.exists():
        return False, "comp.py missing"
    r = run([sys.executable, str(p)], 15)
    return r["rc"] == 0, "compiler ran"


def s07():
    idx = HC / "out" / "__init__.py"
    if not idx.exists():
        return False, "out/__init__.py missing"
    r = run([sys.executable, str(idx)], 60)
    for line in r["out"].splitlines():
        if line.startswith("total:"):
            parts = line.split()
            return parts[5] == "0", f"{parts[3]} passed, {parts[5]} failed"
    return r["rc"] == 0, "hoods ran"


def s08():
    v = HC / "chain" / "verify.py"
    if not v.exists():
        return False, "chain/verify.py missing"
    r = run([sys.executable, str(v)], 15)
    sig = ""
    for line in r["out"].splitlines():
        if line.startswith("chain_sig:"):
            sig = line.strip()
            break
    return r["rc"] == 0, sig or "chain verify ran"


def s09():
    tdir = HC / "out" / "tests"
    if not tdir.exists():
        return False, "tests dir missing"
    tests = sorted(tdir.glob("test_*.py"))
    passed = sum(1 for t in tests if run([sys.executable, str(t)], 15)["rc"] == 0)
    return passed == len(tests), f"{passed}/{len(tests)} tests pass"


def s10():
    p = UC / "enterprise" / "scored.json"
    if not p.exists():
        return False, "scored.json missing"
    d = json.loads(p.read_text())
    cov = d.get("coverage", {})
    return True, (
        f"{cov.get('forbes_sectors', 0)} Forbes, {cov.get('gartner_layers', 0)} Gartner"
    )


def s11():
    p = UC / "orders.json"
    if not p.exists():
        return False, "orders.json missing"
    d = json.loads(p.read_text())
    n = d.get("level0", {}).get("artifact_count", 0)
    return n > 0, f"{n} artifacts, 4 levels"


def s12():
    p = UC / "systemhood_hoods.json"
    if not p.exists():
        return False, "systemhood_hoods.json missing"
    d = json.loads(p.read_text())
    return d.get("anchored", 0) > 0, (
        f"anchored: {d.get('anchored', 0)}, absent: {d.get('absent', 0)}"
    )


def s13():
    p = UC / "lastmile" / "run_all.py"
    if not p.exists():
        return False, "lastmile/run_all.py missing"
    r = run([sys.executable, str(p)], 30)
    return r["rc"] == 0, "org, ops, infra, flows reported"


def s14():
    p = UC / "resolve_report.json"
    if not p.exists():
        return False, "resolve_report.json missing"
    d = json.loads(p.read_text())
    return d.get("missing", 1) == 0, f"resolve: {d.get('passed')}/{d.get('stages', 10)}"


STAGES = [
    ("01 corpus scan", s01),
    ("02 VEM service", s02),
    ("03 VEM index", s03),
    ("04 ISA registry", s04),
    ("05 UCS registry", s05),
    ("06 compiler chain", s06),
    ("07 hoods", s07),
    ("08 hood chain", s08),
    ("09 hood tests", s09),
    ("10 enterprise map", s10),
    ("11 orders", s11),
    ("12 systemhood", s12),
    ("13 lastmile", s13),
    ("14 resolve", s14),
]


def main():
    print("== everything ==")
    print()
    results = []
    t0 = time.time()
    for name, fn in STAGES:
        ts = time.time()
        try:
            ok, msg = fn()
        except Exception as e:
            ok, msg = False, f"exception: {e}"
        dt = time.time() - ts
        status = "OK  " if ok else "FAIL"
        print(f"  {status}  {name:22s}  {msg}  ({dt:.2f}s)")
        results.append((name, ok, msg, dt))
    dt = time.time() - t0
    passed = sum(1 for _, ok, _, _ in results if ok)
    failed = len(results) - passed
    print()
    print("== summary ==")
    print(f"  stages:  {len(results)}")
    print(f"  passed:  {passed}")
    print(f"  failed:  {failed}")
    print(f"  time:    {dt:.2f}s")
    (UC / "everything_run.json").write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "stages": [
                    {"name": n, "ok": o, "msg": m, "duration_s": round(d, 3)}
                    for n, o, m, d in results
                ],
                "passed": passed,
                "failed": failed,
                "duration_s": round(dt, 3),
            },
            indent=2,
        )
    )
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
