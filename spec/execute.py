\
\
\
\
\
import json, pathlib, subprocess, sys, uuid, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
def _resolve(p):
    p = pathlib.Path(p)
    return p if p.is_absolute() else (ROOT / p)
def execute(manifest_path):
    manifest_path = _resolve(manifest_path)
    m = json.loads(manifest_path.read_text())
    results = []
    for art in m["artifacts"]:
        if art["kind"] != "test":
            continue
        p = _resolve(art["path"])
        if not p.exists():
            results.append({"test": str(p), "exit": 127,
                            "stdout": "", "stderr": f"missing: {p}"})
            continue
        r = subprocess.run([sys.executable, str(p)],
                           capture_output=True, text=True, timeout=30)
        results.append({"test": str(p), "exit": r.returncode,
                        "stdout": r.stdout[-500:], "stderr": r.stderr[-500:]})
    passed = bool(results) and all(r["exit"] == 0 for r in results)
    evidence = {
        "schema_version": "1.0",
        "id": str(uuid.uuid4()),
        "plan_id": m["plan_id"],
        "purpose": "execution-evidence",
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "passed": passed,
        "results": results,
    }
    ev_path = ROOT / "build" / m["plan_id"] / "evidence.json"
    ev_path.parent.mkdir(parents=True, exist_ok=True)
    ev_path.write_text(json.dumps(evidence, indent=2))
    return evidence, str(ev_path)
if __name__ == "__main__":
    ev, path = execute(sys.argv[1])
    try:
        execute("definitely-nonexistent-manifest.json")
        raise SystemExit("execute should fail on missing manifest")
    except (FileNotFoundError, KeyError):
        pass
    print(json.dumps({"passed": ev["passed"], "evidence": path,
                      "results": ev["results"]}, indent=2))
    sys.exit(0 if ev["passed"] else 1)
