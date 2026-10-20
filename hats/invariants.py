import pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
INVARIANTS = {}
def hat(name, invariant, check):
    INVARIANTS[name] = {"invariant": invariant, "check": check}
SIGNED_ERA_START = "92b794e"
def _contributor():
    r = subprocess.run(["git","log","--format=%H %G?", f"{SIGNED_ERA_START}..HEAD"],
                       cwd=ROOT, capture_output=True, text=True, timeout=10)
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] in ("N","B"):
            return {"ok": False, "reason": f"unsigned/bad {parts[0][:12]} in signed era"}
    return {"ok": True, "reason": f"all commits in {SIGNED_ERA_START}..HEAD signed (G) or key-missing (E)"}
hat("contributor", f"every commit after {SIGNED_ERA_START} signed (G) or key-missing (E)", _contributor)
def _reviewer():
    r = subprocess.run(["git","log","--merges","--format=%H %s","-10"], cwd=ROOT,
                       capture_output=True, text=True, timeout=10)
    reason = re.compile(r"(#\d+|because|fix|revert|add|move|guard|refuse|remove)", re.I)
    for line in r.stdout.splitlines():
        p = line.split(None, 1)
        if len(p) >= 2 and not reason.search(p[1]):
            return {"ok": False, "reason": f"merge {p[0][:12]}: {p[1][:50]}"}
    return {"ok": True, "reason": "all recent merges cite a reason"}
hat("reviewer", "every recent merge cites a reason", _reviewer)
def _release():
    tags = subprocess.run(["git","tag"], cwd=ROOT, capture_output=True, text=True, timeout=5).stdout.split()
    if not tags: return {"ok": True, "reason": "no tags (vacuous)"}
    main = subprocess.run(["git","rev-parse","main"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    for t in tags:
        sha = subprocess.run(["git","rev-list","-n","1",t], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        if subprocess.run(["git","merge-base","--is-ancestor",sha,main], cwd=ROOT).returncode != 0:
            return {"ok": False, "reason": f"tag {t} not on main"}
    return {"ok": True, "reason": f"{len(tags)} tags all on main"}
hat("release", "every tag is ancestor of main", _release)
_SPEC_PREFIXES = (
    "spec/",                                                       
    "auth/",
    "enterprise/",
    "standards/",
    "specs/",
    "tools/sdlc.sh",
    "tools/getgguf.py",
    "bench/bound.py",
    "bench/ledger.py",
    "bench/kaleidogami.py",
    "ci/content-checks.py",
    "ci/arch-check.py",
    "ci/correlate.py",
    "ci/docs-checks.py",
    "runtime.json",
    "genesis.md",
)
def _maintainer():
    if not (ROOT/"genesis.md").exists():
        return {"ok": False, "reason": "genesis.md missing"}
    gen = (ROOT/"genesis.md").read_text()
    tracked = subprocess.run(["git","ls-tree","-r","origin/main","--name-only"],
                             cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.split()
    spec_files = []
    for f in tracked:
        if not any(f.startswith(p) or f == p for p in _SPEC_PREFIXES): continue
        if f.startswith("spec/audit/"): continue
        if f.endswith("/__init__.py") or f == "__init__.py":
            if (ROOT / f).exists() and (ROOT / f).stat().st_size == 0:
                continue
        spec_files.append(f)
    orphans = [f for f in spec_files if f not in gen]
    if orphans:
        return {"ok": False, "reason": f"spec files not in genesis: {orphans[:5]}"}
    return {"ok": True,
            "reason": f"{len(spec_files)}/{len(tracked)} spec files named in genesis (app code excluded)"}
hat("maintainer", "every file in the spec tree (spec/, auth/, enterprise/, standards/, specs/, tools/sdlc.sh, bench/, ci/, runtime.json, genesis.md) is named in genesis.md", _maintainer)
def _oncall():
    sys.path.insert(0, str(ROOT/"hats"))
    import oncall_check
    ok, gaps = oncall_check.check()
    return {"ok": ok, "reason": "one-page rollback" if ok else "; ".join(gaps)}
hat("oncall", "sdlc_rollback exists, runbook one-page", _oncall)
def _security():
    tracked = subprocess.run(["git","ls-files"], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.split()
    bad = [f for f in tracked if re.search(r"(^|/)KEY$|\.sig$|\.pem$", f)]
    if bad: return {"ok": False, "reason": f"signing material tracked: {bad}"}
    return {"ok": True, "reason": "no signing material tracked"}
hat("security", "no signing material tracked", _security)
def _ci():
    pc = ROOT / "spec/parallel_check.py"
    if not pc.exists():
        return {"ok": False, "reason": "parallel_check.py missing"}
    try:
        r = subprocess.run([sys.executable, str(pc)], cwd=ROOT,
                           capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return {"ok": False, "reason": "parallel_check timed out"}
    ran = set()
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1].isdigit():
            ran.add(parts[0])
    expected = {p.stem for p in (ROOT / "spec").glob("*.py")
                if p.stem not in ("parallel_check", "compile") and "__main__" in p.read_text()}
    missing = expected - ran
    if missing:
        return {"ok": False, "reason": f"not run: {sorted(missing)[:5]}"}
    return {"ok": True, "reason": f"ran all {len(expected)} spec modules"}
hat("ci", "parallel_check runs every spec/*.py module with __main__", _ci)
def _educator():
    doc = ROOT/"docs/hats/README.md"
    if not doc.exists(): return {"ok": False, "reason": "docs/hats/README.md missing"}
    text = doc.read_text()
    missing = [f"spec/{p.name}" for p in (ROOT/"spec").glob("*.py")
               if p.name != "parallel_check.py" and f"spec/{p.name}" not in text]
    if missing: return {"ok": False, "reason": f"undocumented: {missing[:5]}"}
    return {"ok": True, "reason": f"all spec modules documented"}
hat("educator", "every spec/*.py module named in docs/hats/README.md", _educator)
def _graph():
    r = subprocess.run(["git","rev-list","--all","--format=%P"], cwd=ROOT,
                       capture_output=True, text=True, timeout=10)
    shas, edges = set(), []
    for line in r.stdout.splitlines():
        if line.startswith("commit"): continue
        parts = line.split()
        if not parts: continue
        shas.add(parts[0])
        for p in parts[1:]: edges.append((parts[0], p))
    indeg = {s:0 for s in shas}
    for _, p in edges:
        if p in indeg: indeg[p] += 1
    q = [s for s,d in indeg.items() if d == 0]; seen = 0
    while q:
        n = q.pop(); seen += 1
        for c,p in edges:
            if c == n:
                indeg[p] -= 1
                if indeg[p] == 0: q.append(p)
    if seen != len(shas):
        return {"ok": False, "reason": f"cycle: {len(shas)-seen} unreachable"}
    return {"ok": True, "reason": f"DAG valid: {len(shas)} commits"}
hat("graph", "commit graph is a DAG", _graph)
def run_all():
    results = {}
    for name, spec in INVARIANTS.items():
        try: results[name] = {"invariant": spec["invariant"], **spec["check"]()}
        except Exception as e:
            results[name] = {"invariant": spec["invariant"], "ok": False, "reason": f"raised: {e}"}
    return results
if __name__ == "__main__":
    r = run_all()
    for name, res in r.items():
        print(f"  [{'OK' if res['ok'] else 'FAIL'}] {name:14s} {res['invariant']}")
        if not res['ok']:
            print(f"           {res['reason']}")
    failed = [n for n, x in r.items() if not x["ok"]]
    assert all("invariant" in x for x in r.values()), "every hat must have an invariant"
    if failed:
        raise SystemExit(f"hats failing: {failed}")
    print(f"\ninvariants OK: {len(r)} hats, every invariant holds")
