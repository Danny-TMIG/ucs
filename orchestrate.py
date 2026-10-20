import argparse, json, os, pathlib, subprocess, sys, time
ROOT = pathlib.Path.cwd().resolve()
sys.path.insert(0, str(ROOT/"ci"))
import parsers

SKIP_TOP = {".git",".backup-comments","__pycache__","build","node_modules",".venv",
            "htmlcov",".mypy_cache",".pytest_cache","tmp","logs",".cache","dist","target","pipe"}

TARGETS = {
    "local": {"cmd":["llama-cli","-m","{gguf}","-p","{prompt}","-n","200","--no-display-prompt"], "needs":["AETHER_GGUF"]},
    "cloud": {"cmd":["curl","-s","-X","POST","{url}","-H","Content-Type: application/json","-d","{body}"], "needs":["AETHER_CLOUD_URL"]},
    "ssh":   {"cmd":["ssh","{host}","llama-cli","-m","{ssh_model}","-p","{prompt}","-n","200","--no-display-prompt"], "needs":["AETHER_SSH_HOST","AETHER_SSH_MODEL"]},
    "docker":{"cmd":["docker","run","--rm","ghcr.io/ggerganov/llama.cpp:full","-m","{docker_model}","-p","{prompt}","-n","200"], "needs":["AETHER_DOCKER_MODEL"]},
}

def walk():
    out = []
    for p in ROOT.rglob("*"):
        if not p.is_file(): continue
        try: top = p.relative_to(ROOT).parts[0]
        except (ValueError, IndexError): continue
        if top in SKIP_TOP: continue
        out.append(p)
    return out

def cmd_list(_):
    for n in TARGETS:
        a = "available" if all(os.environ.get(k) for k in TARGETS[n]["needs"]) else f"needs {TARGETS[n]['needs']}"
        print(f"  {n:8s} {a}")
    return 0

def cmd_stage(_):
    files = walk(); print(f"describing {len(files)} files")
    results = [parsers.describe(f, ROOT) for f in files]
    from collections import Counter
    v = Counter(r["verdict"] for r in results)
    out = ROOT/"build"/"stage.json"; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"records":results}, indent=2))
    print(f"stage: {len(results)} records, parsed={v['parsed']}, skipped={v['skipped']}, failed={v['failed']}")
    for r in results:
        if r["verdict"] == "failed": print(f"  {r['path']}: [{r.get('format','?')}] {r.get('reason','failed')}")
    return 0 if v["failed"] == 0 else 1

def cmd_run(args):
    target = args.target if args.target in TARGETS else next((t for t in TARGETS if all(os.environ.get(k) for k in TARGETS[t]["needs"])), None)
    if target is None: print("no target available"); return 2
    cmd = [a.replace("{prompt}"," ".join(args.prompt)).replace("{gguf}",os.environ.get("AETHER_GGUF",""))
            .replace("{ssh_model}",os.environ.get("AETHER_SSH_MODEL","")).replace("{docker_model}",os.environ.get("AETHER_DOCKER_MODEL",""))
            .replace("{url}",os.environ.get("AETHER_CLOUD_URL","")).replace("{host}",os.environ.get("AETHER_SSH_HOST",""))
            .replace("{body}",json.dumps({"prompt":" ".join(args.prompt)})) for a in TARGETS[target]["cmd"]]
    t0 = time.perf_counter()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        e, out, err = r.returncode, r.stdout.strip(), r.stderr.strip()[:500]
    except subprocess.TimeoutExpired:
        e, out, err = 124, "", "timeout"
    print(json.dumps({"target":target,"exit":e,"wall_s":round(time.perf_counter()-t0,3),"output":out[:200]}, indent=2))
    return 0 if e == 0 else 1

CHECKS = [
    ("stage",[sys.executable,"orchestrate.py","stage"]),
    ("import-check",[sys.executable,"ci/import-check.py"]),
    ("hats",[sys.executable,"hats/invariants.py"]),
    ("correlate",[sys.executable,"ci/correlate.py"]),
    ("content",[sys.executable,"ci/content-checks.py"]),
    ("mastery",[sys.executable,"mastery/mastery.py"]),
    ("murmuration",[sys.executable,"murmuration/murmuration.py"]),
    ("atlas",[sys.executable,"atlas/atlas.py"]),
    ("tickets",[sys.executable,"-c",
        "import sys,pathlib; sys.path.insert(0,'.'); "
        "import tickets.record, tickets.store, tickets.query, tickets.causal; "
        "print('tickets OK')"]),
    ("governance",[sys.executable,"-c",
        "import sys,pathlib; sys.path.insert(0,'.'); "
        "import governance.agency, governance.licence, governance.certification, "
        "governance.referee, governance.reviewer, governance.seats; "
        "print('governance OK')"]),
    ("compliance",[sys.executable,"-c",
        "import sys,pathlib; sys.path.insert(0,'.'); "
        "import compliance.access, compliance.retention, compliance.lineage, "
        "compliance.consent, compliance.incident, compliance.report; "
        "print('compliance OK')"]),
]

def cmd_verify(_):
    checks = []
    for name, cmd in CHECKS:
        if cmd[1] != "-c" and not (ROOT/cmd[1]).exists():
            checks.append({"name":name,"ok":True,"reason":"not present"}); continue
        try:
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=180)
            checks.append({"name":name,"ok":r.returncode==0,"reason":"" if r.returncode==0 else (r.stderr or r.stdout)[-200:]})
        except subprocess.TimeoutExpired:
            checks.append({"name":name,"ok":False,"reason":"timeout"})
    for c in checks: print(f"  [{'OK' if c['ok'] else 'FAIL'}] {c['name']} {c['reason']}")
    return 0 if all(c["ok"] for c in checks) else 1

def cmd_self_test(_):
    import tempfile
    t = pathlib.Path(tempfile.mkdtemp())
    (t/"spec").mkdir(); (t/"spec"/"a.py").write_text("x=1\n")
    (t/"build").mkdir(); (t/"build"/"b.json").write_text("{}")
    orig = ROOT; globals()["ROOT"] = t
    try:
        found = [str(p.relative_to(t)) for p in walk()]
        assert "spec/a.py" in found, found
        assert "build/b.json" not in found, found
    finally: globals()["ROOT"] = orig
    assert parsers.describe(t/"spec"/"a.py", t)["verdict"] == "parsed"
    assert parsers.describe(t/"build"/"b.json", t)["verdict"] == "skipped"
    print(f"self-test OK: {len(TARGETS)} targets, {len(CHECKS)} checks")
    return 0

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    sub.add_parser("stage").set_defaults(fn=cmd_stage)
    sub.add_parser("verify").set_defaults(fn=cmd_verify)
    sub.add_parser("self-test").set_defaults(fn=cmd_self_test)
    r = sub.add_parser("run"); r.add_argument("target_or_prompt"); r.add_argument("prompt", nargs="*"); r.set_defaults(fn=cmd_run, target=None)
    a = ap.parse_args()
    if a.cmd == "run" and a.target_or_prompt not in TARGETS:
        a.prompt = [a.target_or_prompt] + a.prompt; a.target = None
    elif a.cmd == "run": a.target = a.target_or_prompt
    return a.fn(a)

if __name__ == "__main__": sys.exit(main())
