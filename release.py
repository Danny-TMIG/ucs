import datetime, json, pathlib, subprocess, sys
ROOT = pathlib.Path.cwd().resolve()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "atlas"))
sys.path.insert(0, str(ROOT / "governance"))
sys.path.insert(0, str(ROOT / "compliance"))

def _gate(name, cmd, timeout=300):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return {"name": name, "ok": r.returncode == 0, "stdout": r.stdout[-1500:], "stderr": r.stderr[-1500:]}

def _validate_atlas():
    import atlas
    errs = []
    for d in atlas.DOMAINS:
        if atlas.validate_domain(d): errs.append(d)
    for f in atlas.FUNCTION_CATEGORIES:
        if atlas.validate_function_category(f): errs.append(f)
    for s in atlas.SKILL_FAMILIES:
        if atlas.validate_skill_family(s): errs.append(s)
    for o in atlas.EXECUTION_OPS:
        if atlas.validate_execution_op(o): errs.append(o)
    for r in atlas.RESULT_STATES:
        if atlas.validate_result(r): errs.append(r)
    return errs

def _validate_governance():
    import governance.agency, governance.licence
    return []

def _validate_compliance():
    import compliance.report
    return []

def _validate_murmuration():
    import murmuration.murmuration as m
    stack = ["read","parse","transform","execute","observe","decide","persist","publish"]
    agents = m.assemble(stack, n_each=2)
    trace = m.route("read-0", agents, hops=len(agents)+1)
    if not (trace and trace[-1].startswith("publish-")):
        return [f"murmuration chain does not reach publish: {trace}"]
    return []

def _validate_mastery():
    import mastery.mastery as mm
    return mm.validate_all()

if __name__ == "__main__":
    sha = subprocess.run(["git","rev-parse","HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    gates = [
        ("parse", [sys.executable, "-c",
            "import ast,pathlib\n"
            "for p in pathlib.Path('.').rglob('*.py'):\n"
            "    if any(x in p.parts for x in ('.git','build','__pycache__','.venv','.backup-comments')): continue\n"
            "    ast.parse(p.read_text())\n"
            "print('parse OK')"]),
        ("import", [sys.executable, "ci/import-check.py"]),
        ("stage", [sys.executable, "orchestrate.py", "stage"]),
        ("content", [sys.executable, "ci/content-checks.py"]),
        ("correlate", [sys.executable, "ci/correlate.py"]),
    ]
    results = []
    for name, cmd in gates:
        print(f"[{name}]")
        r = _gate(name, cmd)
        results.append({"name": name, "ok": r["ok"]})
        if not r["ok"]:
            print(f"  FAIL")
            for line in (r["stdout"] + r["stderr"]).splitlines()[-15:]:
                print(f"  {line}")
            (ROOT/"build").mkdir(exist_ok=True)
            (ROOT/"build"/"release-failed.json").write_text(json.dumps(
                {"sha": sha, "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 "failed": name, "stdout": r["stdout"], "stderr": r["stderr"]}, indent=2))
            sys.exit(1)
        print(f"  OK")

    print("[validate]")
    errs = []
    errs.extend(("atlas", e) for e in _validate_atlas())
    errs.extend(("governance", e) for e in _validate_governance())
    errs.extend(("compliance", e) for e in _validate_compliance())
    errs.extend(("murmuration", e) for e in _validate_murmuration())
    errs.extend(("mastery", e) for e in _validate_mastery())
    if errs:
        print(f"  FAIL ({len(errs)} errors)")
        for k, e in errs[:15]:
            print(f"  [{k}] {e}")
        (ROOT/"build").mkdir(exist_ok=True)
        (ROOT/"build"/"release-failed.json").write_text(json.dumps(
            {"sha": sha, "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "failed": "validate", "errors": [{"gate": k, "error": e} for k, e in errs]}, indent=2))
        sys.exit(1)
    print(f"  OK")

    tag = f"v0.1.0-{sha[:7]}"
    existing = subprocess.run(["git","tag"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    if tag not in existing:
        r = subprocess.run(["git","tag","-s",tag,"-m",f"release {sha[:7]}"], cwd=ROOT,
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[tag] FAIL: {r.stderr[:200]}")
        else:
            print(f"[tag] OK: {tag}")
    else:
        print(f"[tag] exists: {tag}")

    (ROOT/"build").mkdir(exist_ok=True)
    (ROOT/"build"/"release.json").write_text(json.dumps(
        {"sha": sha, "tag": tag,
         "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "gates": results}, indent=2))
    print(f"RELEASED {sha[:12]} as {tag}")
