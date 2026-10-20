import pathlib, sys, tempfile
def check(root=None):
    root = pathlib.Path(root) if root else pathlib.Path(__file__).resolve().parent.parent
    gaps = []
    sdlc = root / "tools/sdlc.sh"
    runbook = root / "ops/runbooks/rollback.md"
    if not sdlc.exists():
        return False, [f"missing tools/sdlc.sh under {root}"]
    if "sdlc_rollback()" not in sdlc.read_text():
        gaps.append("tools/sdlc.sh: no sdlc_rollback() function")
    if not runbook.exists():
        return not gaps, gaps + ["missing ops/runbooks/rollback.md"]
    rb = runbook.read_text()
    if "sdlc_rollback" not in "\n".join(rb.splitlines()[:20]):
        gaps.append("rollback.md: sdlc_rollback not in first 20 lines")
    if len(rb.splitlines()) > 100:
        gaps.append(f"rollback.md is {len(rb.splitlines())} lines > 100")
    return not gaps, gaps
if __name__ == "__main__":
    ok, gaps = check()
    if ok:
        print("oncall OK: sdlc_rollback exists, runbook one-page, rollback in first 20 lines")
    else:
        print("\n".join(gaps))
        with tempfile.TemporaryDirectory() as d:
            fr = pathlib.Path(d)
            (fr / "tools").mkdir(); (fr / "ops/runbooks").mkdir(parents=True)
            (fr / "tools/sdlc.sh").write_text("# no rollback here\n")
            (fr / "ops/runbooks/rollback.md").write_text("nope\n")
            ok2, _ = check(root=fr)
            assert not ok2, "stripped sdlc must fail oncall check"
        sys.exit(1)
