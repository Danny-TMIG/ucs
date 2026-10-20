#!/usr/bin/env python3
import concurrent.futures, subprocess, sys, time
TESTS = [
    ("atlas",        [sys.executable, "spec/atlas.py"]),
    ("invariants",   [sys.executable, "spec/invariants.py"]),
    ("revise",       [sys.executable, "spec/revise.py"]),
    ("swarm",        [sys.executable, "spec/swarm.py"]),
    ("bound",        [sys.executable, "bench/bound.py"]),
    ("decide",       [sys.executable, "spec/decide.py"]),
    ("runtime.json", [sys.executable, "-c",
                      "import json,pathlib;"
                      "m=json.loads(pathlib.Path('runtime.json').read_text());"
                      "missing=[(k,p) for k,p in m['files'].items() if not pathlib.Path(p).exists()];"
                      "assert not missing, missing;"
                      "print('runtime manifest OK')"]),
    ("loop",         [sys.executable, "-c",
                      "import sys;sys.path.insert(0,'spec');"
                      "import loop;"
                      "r=loop.run_loop({'goal':'build foo','acceptance':['foo returns ok']});"
                      "assert r['outcome']=='accepted', r;"
                      "print('loop OK')"]),
]
def run_one(name, cmd):
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {"name": name, "exit": r.returncode, "wall": time.perf_counter()-t0,
            "stdout": r.stdout.strip(), "stderr": r.stderr.strip()}
def main():
    t0 = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(TESTS)) as pool:
        results = [f.result() for f in [pool.submit(run_one, n, c) for n, c in TESTS]]
    wall = time.perf_counter() - t0
    serial = sum(r["wall"] for r in results)
    print(f"{'test':14s} {'exit':>4s} {'wall(s)':>8s}  last line")
    print("-" * 60)
    failed = []
    for r in results:
        last = (r["stdout"].splitlines() or [""])[-1][:36]
        print(f"{r['name']:14s} {r['exit']:>4d} {r['wall']:>8.3f}  {last}")
        if r["exit"] != 0: failed.append(r)
    print("-" * 60)
    print(f"total: {wall:.3f}s  serial: {serial:.3f}s  speedup: {serial/wall:.2f}x")
    if failed:
        for r in failed:
            print(f"\n{r['name']} stderr:\n{r['stderr']}")
        return 1
    print("\nALL PARALLEL OK")
    return 0
if __name__ == "__main__":
    sys.exit(main())
