import concurrent.futures, os, pathlib, signal, subprocess, sys, time
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
TIMEOUT = 15
SKIP = {"compile", "verify_boundary"}
def _tests():
    tests = []
    for p in sorted(HERE.glob("*.py")):
        if p.stem == "parallel_check" or p.stem in SKIP:
            continue
        if "__main__" in p.read_text():
            tests.append((p.stem, [sys.executable, str(p.relative_to(ROOT))]))
    for p in sorted((ROOT / "bench").glob("*.py")):
        tests.append((p.stem, [sys.executable, str(p.relative_to(ROOT))]))
    return tests
def run_one(name, cmd):
    t0 = time.perf_counter()
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, start_new_session=True)
        try:
            out, err = proc.communicate(timeout=TIMEOUT)
            return {"name": name, "exit": proc.returncode,
                    "wall": time.perf_counter() - t0,
                    "stdout": out.strip(), "stderr": err.strip()}
        except subprocess.TimeoutExpired:
            try: os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError: pass
            try: out, err = proc.communicate(timeout=2)
            except subprocess.TimeoutExpired: proc.kill(); out, err = "", ""
            return {"name": name, "exit": 124, "wall": time.perf_counter() - t0,
                    "stdout": out.strip() if out else "",
                    "stderr": f"TIMEOUT after {TIMEOUT}s"}
    except Exception as e:
        return {"name": name, "exit": 125, "wall": time.perf_counter() - t0,
                "stdout": "", "stderr": f"raised: {e}"}
def main():
    TESTS = _tests()
    t0 = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(TESTS)) as pool:
        results = [f.result() for f in [pool.submit(run_one, n, c) for n, c in TESTS]]
    wall = time.perf_counter() - t0
    serial = sum(r["wall"] for r in results)
    print(f"{'test':20s} {'exit':>4s} {'wall(s)':>8s}  last line")
    print("-" * 62)
    failed = []
    for r in results:
        last = (r["stdout"].splitlines() or [""])[-1][:34]
        print(f"{r['name']:20s} {r['exit']:>4d} {r['wall']:>8.3f}  {last}")
        if r["exit"] != 0: failed.append(r)
    print("-" * 62)
    print(f"total: {wall:.3f}s serial: {serial:.3f}s speedup: {serial/wall:.2f}x")
    if failed:
        for r in failed:
            print(f"\n{r['name']} exit={r['exit']}: {r['stderr'][:200]}")
        return 1
    print("\nALL PARALLEL OK")
    return 0
if __name__ == "__main__":
    _neg = run_one("neg", [sys.executable, "-c", "raise SystemExit(1)"])
    assert _neg["exit"] != 0, _neg
    sys.exit(main())
