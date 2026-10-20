"""run_all.py — last mile: org, ops, infra, flows."""

from __future__ import annotations
import json, os, socket, subprocess, sys, time
from pathlib import Path

HOME = Path.home()
OUT = HOME / "ucs" / "lastmile"
OUT.mkdir(parents=True, exist_ok=True)


ORG_TREE = {
    "owner": {
        "description": "The single accountable party for the corpus",
        "path": str(HOME),
        "responsibilities": [
            "approves changes to the chain key",
            "decides which artifacts are promoted to used status",
            "reviews the manifest weekly",
        ],
    },
    "stewards": {
        "vem": {"owner": "index", "scope": "~/vem-index/"},
        "hoods": {"owner": "chain", "scope": "~/ucs/hood_compilers/"},
        "isa": {"owner": "registry", "scope": "~/ucs/opcodes_all/"},
        "systems": {"owner": "pipeline", "scope": "~/ucs/systems/"},
        "enterprise": {"owner": "classifier", "scope": "~/ucs/enterprise/"},
        "uci": {"owner": "coordinator", "scope": "~/ucs/"},
    },
    "roles": {
        "index": "maintains VEM index; runs reindex on corpus change",
        "chain": "rebuilds hood chain; re-signs after generator changes",
        "registry": "adds ISAs; refreshes resolvers",
        "pipeline": "keeps compiler chain green; owns bin/prog.asm",
        "classifier": "re-runs enterprise map; owns ROOTS exclusion list",
        "coordinator": "runs lastmile; owns the runbook",
    },
}


def run_org() -> dict:
    scopes = {}
    for name, info in ORG_TREE["stewards"].items():
        scope = Path(info["scope"].replace("~", str(HOME)))
        if scope.exists():
            files = [p for p in scope.rglob("*") if p.is_file()]
            scopes[name] = {
                "owner": info["owner"],
                "scope": str(scope.relative_to(HOME)),
                "files": len(files),
                "bytes": sum(p.stat().st_size for p in files),
            }
        else:
            scopes[name] = {
                "owner": info["owner"],
                "scope": str(scope),
                "files": 0,
                "bytes": 0,
                "missing": True,
            }
    result = {"org": ORG_TREE, "state": scopes}
    (OUT / "org.json").write_text(json.dumps(result, indent=2))
    return result


OPS = {
    "start_vem": (
        "for port in 19800 19801 19802; do "
        "curl -s http://127.0.0.1:$port/stats >/dev/null 2>&1 || "
        "nohup ~/venvs/vem/bin/python ~/vem/service.py --port $port "
        "> ~/vem/service.$port.log 2>&1 & done"
    ),
    "stop_vem": "pkill -f 'vem/service.py' 2>/dev/null || true",
    "reindex": "python3 ~/vem-index/spec.py run ~/vem-index/specs/all.json --no-resume",
    "rebuild_hoods": (
        "python3 ~/ucs/hood_compilers/compile_all.py && "
        "python3 ~/ucs/hood_compilers/refine.py && "
        "python3 ~/ucs/hood_compilers/harden.py"
    ),
    "resign_chain": "python3 ~/ucs/hood_compilers/chain.py",
    "verify_chain": "python3 ~/ucs/hood_compilers/chain/verify.py",
    "run_hoods": "python3 ~/ucs/hood_compilers/out/__init__.py",
    "run_tests": (
        "for t in ~/ucs/hood_compilers/out/tests/test_*.py; do python3 $t; done"
    ),
    "enterprise": "python3 ~/ucs/enterprise/classify.py && python3 ~/ucs/enterprise/score.py",
    "health": "curl -s http://127.0.0.1:19800/stats",
    "backup": "tar czf ~/ucs/backup-$(date +%Y%m%d).tgz ~/ucs ~/vem-index 2>/dev/null",
    "restore": "tar xzf ~/ucs/backup-YYYYMMDD.tgz -C ~",
}


def exec_cmd(cmd, timeout=15):
    t0 = time.time()
    try:
        r = subprocess.run(
            ["bash", "-c", cmd], capture_output=True, text=True, timeout=timeout
        )
        return {
            "rc": r.returncode,
            "stdout": r.stdout[:2000],
            "stderr": r.stderr[:500],
            "duration_s": round(time.time() - t0, 3),
        }
    except subprocess.TimeoutExpired:
        return {"rc": -1, "error": "timeout", "duration_s": timeout}


def run_ops(execute=False):
    readonly = ["health", "verify_chain", "run_hoods"]
    results = {}
    for name in readonly:
        cmd = OPS[name]
        results[name] = exec_cmd(cmd) if execute else {"cmd": cmd, "mode": "listed"}
    out = {"runbook": OPS, "results": results}
    (OUT / "ops.json").write_text(json.dumps(out, indent=2))
    return out


def probe_port(port):
    s = socket.socket()
    s.settimeout(0.3)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def run_infra():
    ports = [19800, 19801, 19802]
    port_state = {p: probe_port(p) for p in ports}
    keyfile = HOME / "ucs" / "hood_compilers" / "chain" / "KEY"
    key_state = {
        "exists": keyfile.exists(),
        "mode": oct(keyfile.stat().st_mode & 0o777) if keyfile.exists() else None,
        "bytes": keyfile.stat().st_size if keyfile.exists() else 0,
    }
    services = [
        {"name": "vem", "ports": ports, "depends_on": []},
        {"name": "vem-index", "ports": [], "depends_on": ["vem"]},
        {"name": "hoods", "ports": [], "depends_on": []},
        {"name": "chain", "ports": [], "depends_on": ["hoods"]},
        {"name": "enterprise", "ports": [], "depends_on": []},
    ]
    dirs = {}
    for name in [
        "vem-index",
        "ucs",
        "ucs/hood_compilers",
        "ucs/opcodes_all",
        "ucs/systems",
        "ucs/enterprise",
        "ucs/lastmile",
    ]:
        p = HOME / name
        dirs[name] = {
            "exists": p.exists(),
            "files": len(list(p.rglob("*"))) if p.exists() else 0,
        }
    out = {
        "ports": port_state,
        "key": key_state,
        "services": services,
        "dirs": dirs,
        "host": {"system": os.uname().sysname, "machine": os.uname().machine},
    }
    (OUT / "infra.json").write_text(json.dumps(out, indent=2))
    return out


FLOWS = {
    "vem_query": {
        "stages": [
            "user writes query string",
            "spec.py loads specs/<name>.json",
            "spec fans out to every port in shard.ports",
            "each port: parse q, corpus, k",
            "each port: embed the query text",
            "each port: cosine over corpus vids",
            "each port: return top-k hits",
            "spec merges all hits, dedup by vid",
            "spec attaches paths from records_<name>.jsonl",
            "spec returns sorted top-k with paths",
        ],
        "crosses": ["spec.py", "vem/service.py x N", "records_*.jsonl"],
        "failures": [
            "no ports listening: connection refused",
            "no corpus on that port: empty results",
            "index missing: no path to attach",
        ],
    },
    "compile_expression": {
        "stages": [
            "user writes ((3+4)*5) - 7",
            "comp.py: lex to tokens",
            "comp.py: parse to postfix IR",
            "trans.py: IR to x86-64 asm (AT&T)",
            "clang: asm to prog.o",
            "clang: prog.o to prog (link)",
            "run: prog syscall exit with top of stack",
            "parent shell sees exit code",
        ],
        "crosses": ["comp.py", "trans.py", "clang", "prog"],
        "failures": [
            "syntax error: no IR",
            "unmatched operand: TypeError in emitter",
            "asm dialect mismatch: clang refuses",
            "wrong syscall number: exit 140",
        ],
    },
    "hood_verify": {
        "stages": [
            "verify.py loads chain/chain.json and chain/KEY",
            "for each link: recompute body_hash from out/<hood>.py",
            "compare to link.body_hash",
            "compare link.prev_hash to previous body_hash",
            "recompute link.sig from (prev, hood, body_hash) with KEY",
            "compare to link.sig",
            "after all links: recompute chain_sig excluding chain_sig+generated_at",
            "compare to chain.chain_sig",
            "report per-link PASS/FAIL, overall exit 0 or 1",
        ],
        "crosses": ["chain/verify.py", "chain.json", "chain/KEY", "out/*.py"],
        "failures": [
            "a modified hood: BODY-CHANGED at that link only",
            "key rotated: all sigs invalid",
            "chain.json edited: chain_sig invalid",
        ],
    },
}


def run_flows():
    (OUT / "flows.json").write_text(json.dumps(FLOWS, indent=2))
    return FLOWS


def main():
    execute = "--exec" in sys.argv
    print("== last mile: org, ops, infra, flows ==")
    print()

    print("-- ORG --")
    org = run_org()
    for name, state in org["state"].items():
        m = " (missing)" if state.get("missing") else ""
        print(
            f"  {name:12s} owner={state['owner']:12s} "
            f"files={state['files']:5d} bytes={state['bytes']:>10,}{m}"
        )
    print()

    print("-- OPS --")
    ops = run_ops(execute=execute)
    for name in ["health", "verify_chain", "run_hoods"]:
        r = ops["results"][name]
        if execute:
            line = r.get("stdout", "").strip().splitlines() or [""]
            print(f"  {name:14s} rc={r.get('rc', '?')}  {line[-1][:60]}")
        else:
            print(f"  {name:14s} cmd listed")
    if not execute:
        print("  (run with --exec to execute read-only commands)")
    print()

    print("-- INFRA --")
    infra = run_infra()
    for p, up in infra["ports"].items():
        print(f"  port {p}: {'UP' if up else 'down'}")
    print(
        f"  chain KEY: exists={infra['key']['exists']} "
        f"mode={infra['key']['mode']} bytes={infra['key']['bytes']}"
    )
    for name, d in infra["dirs"].items():
        print(f"  dir {name:22s} exists={d['exists']} files={d['files']}")
    print()

    print("-- FLOWS --")
    for name, flow in FLOWS.items():
        print(
            f"  {name:22s} {len(flow['stages'])} stages, "
            f"crosses {len(flow['crosses'])} artifacts"
        )
    print()

    print(f"wrote: {OUT}/")
    for f in ["org.json", "ops.json", "infra.json", "flows.json"]:
        p = OUT / f
        if p.exists():
            print(f"  {f}  ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
