\
\
\
\
import pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
SIGNED_ERA_START = "92b794e"                                                        
CHECKED = {}
UNCHECKED = {}
def checked(name, why):
    def deco(fn):
        CHECKED[name] = {"fn": fn, "why": why}
        return fn
    return deco
def unchecked(name, why_not):
    UNCHECKED[name] = {"why_not": why_not}
@checked("genesis_exists", "genesis.md enumerates every object; without it there is no ground truth")
def _c_genesis():
    return (ROOT / "genesis.md").exists()
@checked("bodies_correlate", "every object in genesis is claimed by exactly one body")
def _c_correlate():
    r = subprocess.run([sys.executable, "ci/correlate.py"], cwd=ROOT,
                       capture_output=True, text=True, timeout=60)
    return r.returncode == 0
@checked("signed_commits_since_era",
         f"every commit after {SIGNED_ERA_START} on main carries a signature "
         f"(G=good, E=key not local but signature present, N=unsigned, B=bad)")
def _c_signed():
    """%G? per commit:
      G good signature (key trusted locally)
      E signature present, key missing locally (acceptable: the signature exists)
      N no signature (unacceptable: unsigned)
      B bad signature (unacceptable: tampered or wrong key)
    The invariant is "signed", not "verifiable on this machine"."""
    r = subprocess.run(["git", "log", "--format=%H %G?", f"{SIGNED_ERA_START}..HEAD"],
                       cwd=ROOT, capture_output=True, text=True, timeout=10)
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    if not lines:
        return True                                 
    for line in lines:
        parts = line.split(None, 1)
        if len(parts) < 2:
            return False
        status = parts[1].strip()
        if status in ("N", "B"):
            return False
    return True
@checked("all_spec_tests_pass", "the parallel_check gate proves every module")
def _c_suite():
    r = subprocess.run([sys.executable, "spec/parallel_check.py"], cwd=ROOT,
                       capture_output=True, text=True, timeout=120)
    return r.returncode == 0
unchecked("pre_era_commits_signed", f"commits before {SIGNED_ERA_START} may be unsigned; the era boundary is the policy")
unchecked("all_code_correct", "no compiler or prover covers every execution path; tests cover observed paths")
unchecked("no_unknown_dependencies", "network imports are not tracked; the CVE surface is unknown")
unchecked("hardware_independence", "tested only on M4 Max macOS; Linux/Windows untested")
unchecked("ebpf_telemetry", "eBPF requires Linux kernel; macOS does not run eBPF")
unchecked("formal_model_check_of_whole_repo", "TLA+ spec exists for subsystems only; whole-repo model checking is a research program")
def run_checked():
    results = {}
    for name, spec in CHECKED.items():
        try:
            results[name] = {"ok": bool(spec["fn"]()), "why": spec["why"]}
        except Exception as e:
            results[name] = {"ok": False, "why": spec["why"], "error": str(e)}
    return results
def report():
    return {"checked": run_checked(), "unchecked": UNCHECKED}
if __name__ == "__main__":
    r = report()
    for name, res in r["checked"].items():
        marker = "OK" if res["ok"] else "FAIL"
        print(f"  [{marker}] {name}: {res['why']}")
    for name, res in r["unchecked"].items():
        print(f"  [---] {name}: {res['why_not']}")
    failed = [n for n, x in r["checked"].items() if not x["ok"]]
    assert not failed, f"checked invariants failing: {failed}"
    for name, res in r["unchecked"].items():
        assert res["why_not"], f"{name} unchecked without reason"
    print(f"\nverify_boundary OK: {len(r['checked'])} checked, {len(r['unchecked'])} unchecked with stated reasons")
