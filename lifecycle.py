#!/usr/bin/env python3
"""lifecycle.py - pre-flight and ongoing lifecycle manager."""

from __future__ import annotations
import json, os, subprocess, sys, time
from pathlib import Path

HOME = Path.home()
UC = HOME / "ucs"


def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)


def check_tmp_files():
    stray = []
    for p in UC.rglob("*.tmp"):
        stray.append(str(p.relative_to(HOME)))
    return len(stray) == 0, str(len(stray)) + " .tmp files", stray


def check_chain_parse():
    out = []
    for name in ("hood_compilers/chain/chain.json", "allwares/chain.json"):
        p = UC / name
        if not p.exists():
            out.append((name, False, "missing"))
            continue
        try:
            json.loads(p.read_text())
            out.append((name, True, "parses"))
        except Exception as e:
            out.append((name, False, str(e)[:60]))
    return all(ok for _, ok, _ in out), out


def check_verifiers():
    checks = [
        ("resolve", UC / "resolve.py"),
        ("everything", UC / "everything.py"),
        ("hood_chain", UC / "hood_compilers" / "chain" / "verify.py"),
        ("allwares", UC / "allwares" / "verify.py"),
    ]
    results = []
    for name, p in checks:
        if not p.exists():
            results.append((name, False, "missing"))
            continue
        rc, stdout, _ = run([sys.executable, str(p)], timeout=180)
        last = stdout.strip().splitlines()[-1:] or [""]
        results.append((name, rc == 0, last[0][:60]))
    return all(ok for _, ok, _ in results), results


def check_key():
    k = UC / "allwares" / "KEY"
    if not k.exists():
        return False, "missing"
    mode = oct(k.stat().st_mode & 0o777)
    if mode != "0o600":
        return False, "mode " + mode + " (want 0o600)"
    return True, "mode " + mode + ", " + str(k.stat().st_size) + " bytes"


def check_disk():
    total = sum(1 for _ in UC.rglob("*") if _.is_file())
    bytes_ = sum(_.stat().st_size for _ in UC.rglob("*") if _.is_file())
    return True, str(total) + " files, " + str(bytes_) + " bytes"


def check_dirs():
    dirs = [
        "foundations",
        "ucs",
        "ucs/hood_compilers",
        "ucs/opcodes_all",
        "ucs/systems",
        "ucs/enterprise",
        "ucs/lastmile",
        "ucs/allwares",
        "vem-index",
        "swarm",
        "gen",
        "kaleido",
        "polyglot",
        "cs-partitions",
    ]
    out = []
    for d in dirs:
        p = HOME / d
        if not p.exists():
            out.append((d, False, "missing"))
            continue
        n = sum(1 for _ in p.rglob("*") if _.is_file())
        out.append((d, True, str(n) + " files"))
    return all(ok for _, ok, _ in out), out


def pre_flight():
    print("== pre-flight ==")
    results = []

    ok, msg, _ = check_tmp_files()
    print("  " + ("OK  " if ok else "FAIL") + "  tmp files        " + msg)
    results.append(ok)

    ok, out = check_chain_parse()
    for name, o, m in out:
        print("  " + ("OK  " if o else "FAIL") + "  chain " + name.ljust(30) + m)
    results.append(ok)

    ok, msg = check_key()
    print("  " + ("OK  " if ok else "FAIL") + "  key              " + msg)
    results.append(ok)

    ok, msg = check_disk()
    print("  OK    disk             " + msg)

    ok, out = check_dirs()
    print("")
    print("  -- directories --")
    for name, o, m in out:
        print("  " + ("OK  " if o else "FAIL") + "  " + name.ljust(22) + m)
    results.append(ok)

    ok, out = check_verifiers()
    print("")
    print("  -- verifiers --")
    for name, o, m in out:
        print("  " + ("OK  " if o else "FAIL") + "  " + name.ljust(22) + m)
    results.append(ok)

    passed = sum(1 for r in results if r)
    print("")
    print(
        "  checks: "
        + str(len(results))
        + "  passed: "
        + str(passed)
        + "  failed: "
        + str(len(results) - passed)
    )
    return all(results)


def ongoing(seconds=10):
    print("== ongoing lifecycle ==")
    print("  interval: " + str(seconds) + "s")
    print("  Ctrl-C to stop")
    print("")
    prev = None
    try:
        while True:
            ok, out = check_verifiers()

            # signature excludes variable text (durations, timestamps)
            def sig_of(items):
                return tuple(
                    (n, o, m.split("time:")[0].strip()[:40]) for n, o, m in items
                )

            sig = sig_of(out)
            if sig != prev:
                print("[" + time.strftime("%H:%M:%S") + "] change")
                for name, o, m in out:
                    print("  " + ("OK  " if o else "FAIL") + "  " + name.ljust(12) + m)
                prev = sig
            else:
                print("[" + time.strftime("%H:%M:%S") + "] no change")
            time.sleep(seconds)
    except KeyboardInterrupt:
        print("")
        print("  stopped")


def main():
    args = sys.argv[1:]
    if not args or args[0] == "pre-flight":
        sys.exit(0 if pre_flight() else 1)
    if args[0] == "ongoing":
        secs = int(args[1]) if len(args) > 1 else 10
        ongoing(seconds=secs)


if __name__ == "__main__":
    main()
