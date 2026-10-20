import pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
def record(kind, id, statement, where, checked_by):
    return {"kind": kind, "id": id, "statement": statement,
            "where": where, "checked_by": checked_by}
AXIOMS = [
    record("axiom","A1","There is a spec, separate from app code","genesis.md","hats/invariants.py"),
    record("axiom","A2","Every message has an envelope","specs/contracts","spec/payload.py"),
    record("axiom","A3","State-changing call requires a member","auth/member.py","auth/member.py"),
    record("axiom","A4","State-changing execution requires quorum","auth/approval.py","auth/approval.py"),
    record("axiom","A5","Commit graph is a DAG","git","hats/invariants.py"),
]
POSTULATES = [
    record("postulate","P1","Q16.16 sufficient for murmur","spec/murmur.py","spec/murmur.py"),
    record("postulate","P2","7 topological neighbors","spec/murmur.py","spec/murmur.py"),
    record("postulate","P3","AI below beta/pi is bandwidth-bound","spec/decide.py","spec/decide.py"),
    record("postulate","P4","Accuracy CI lower >= theta","spec/decide.py","spec/decide.py"),
    record("postulate","P5","Schema-gated bond only","spec/mimc.py","spec/mimc.py"),
    record("postulate","P6","Quant = (bits, group_size)","spec/mesh.py","spec/mesh.py"),
    record("postulate","P7","Merkle root = tree identity","spec/memo.py","spec/memo.py"),
]
INVARIANTS = [
    record("invariant","I1","Spec tree named in genesis","genesis.md","hats/invariants.py"),
    record("invariant","I2","One body per genesis id","standards/bodies","ci/correlate.py"),
    record("invariant","I3","Every id in atlas","standards/atlases","ci/correlate.py"),
    record("invariant","I4","Every id cited by book","standards/books","ci/correlate.py"),
    record("invariant","I5","Every failure prevented","standards/bodies","ci/correlate.py"),
    record("invariant","I6","No signing material","git","hats/invariants.py"),
    record("invariant","I7","Signed era","git","hats/invariants.py"),
    record("invariant","I8","Tags ancestor of main","git","hats/invariants.py"),
    record("invariant","I9","DAG","git","hats/invariants.py"),
    record("invariant","I10","Rollback one-page","ops/runbooks/rollback.md","hats/oncall_check.py"),
    record("invariant","I11","parallel_check runs all","spec/parallel_check.py","hats/invariants.py"),
    record("invariant","I12","Spec modules documented","docs/hats/README.md","hats/educator_check.py"),
]
VERBS = [
    record("verb","route","dispatch by (layer,class)","spec/desk.py","spec/desk.py"),
    record("verb","dispatch","MIP call","spec/mip.py","spec/mip.py"),
    record("verb","bond","schema-gated composition","spec/mimc.py","spec/mimc.py"),
    record("verb","decompose","intent to plan","spec/decompose.py","spec/decompose.py"),
    record("verb","compile","plan to artifacts","spec/compile.py","spec/compile.py"),
    record("verb","execute","run test","spec/execute.py","spec/execute.py"),
    record("verb","revise","retry on failure","spec/revise.py","spec/revise.py"),
    record("verb","spawn","N agents","spec/swarm.py","spec/swarm.py"),
    record("verb","place","placement","spec/decide.py","spec/decide.py"),
    record("verb","measure","Monte Carlo accuracy","spec/decide.py","spec/decide.py"),
    record("verb","solve_1d","Euler-Lagrange","spec/interface.py","spec/interface.py"),
    record("verb","murmurate","3 local rules","spec/murmur.py","spec/murmur.py"),
    record("verb","generate","model call","spec/serve.py","spec/serve.py"),
    record("verb","reason","model or refuse","spec/reason.py","spec/reason.py"),
    record("verb","invoke","substrate call","spec/llama_expert.py","spec/llama_expert.py"),
    record("verb","record","append ledger","bench/ledger.py","bench/ledger.py"),
    record("verb","fold","partition by regime","bench/kaleidogami.py","bench/kaleidogami.py"),
]
PREDICATES = [
    record("predicate","NoRoute","no route","spec/desk.py","spec/desk.py"),
    record("predicate","AmbiguousRoute","dup route","spec/desk.py","spec/desk.py"),
    record("predicate","NoSubstrate","no substrate","spec/mip.py","spec/mip.py"),
    record("predicate","NoCode","no code","spec/mip.py","spec/mip.py"),
    record("predicate","BondTypeError","schema mismatch","spec/mimc.py","spec/mimc.py"),
    record("predicate","ReasoningUnavailable","no model","spec/reason.py","spec/reason.py"),
    record("predicate","ModelUnavailable","no substrate model","spec/llama_expert.py","spec/llama_expert.py"),
    record("predicate","LedgerCorrupted","chain broken","bench/ledger.py","bench/ledger.py"),
    record("predicate","PermissionError","unauthorized","spec/state.py","spec/state.py"),
]
def nouns():
    if not (ROOT/"genesis.md").exists(): return []
    out = []
    for line in (ROOT/"genesis.md").read_text().splitlines():
        m = re.match(r"\|\s*(ucs\.[A-Za-z0-9_]+)\s*\|\s*(\w+)\s*\|\s*([^|]+?)\s*\|\s*(body\.\w+)\s*\|", line)
        if m: out.append(record("noun", m.group(1), f"{m.group(2)} object",
                                m.group(3).strip(), m.group(4).strip()))
    return out
def grammar():
    return {"axioms":AXIOMS,"postulates":POSTULATES,"invariants":INVARIANTS,
            "verbs":VERBS,"predicates":PREDICATES,"nouns":nouns()}
def check_element(rec):
    where, checked = rec["where"], rec["checked_by"]
    if "/" in where and not any(c in where for c in ("*"," ","(",")")):
        if not (ROOT/where).exists(): return False, f"file missing: {where}"
    if "/" in checked and not any(c in checked for c in ("*"," ","(",")")):
        if not (ROOT/checked).exists(): return False, f"check file missing: {checked}"
    return True, ""
if __name__ == "__main__":
    g = grammar(); total = sum(len(v) for v in g.values()); ok = 0
    for kind, records in g.items():
        if not records: continue
        print(f"\n{kind.upper()} ({len(records)}):")
        for rec in records:
            good, reason = check_element(rec); ok += good
            marker = "OK" if good else "MISSING"
            extra = "" if good else f"  ({reason})"
            print(f"  [{marker}] {rec['id']}{extra}")
    print(f"\nGrammar: {ok}/{total} elements grounded, {total-ok} missing")
    bad = record("axiom","X0","bogus","does/not/exist.py","also/missing.py")
    if check_element(bad)[0]: raise SystemExit("negative test failed")
    if ok < total: raise SystemExit(f"grammar incomplete: {total-ok} missing")
    print("\ngrammar OK: every load-bearing element is grounded")
