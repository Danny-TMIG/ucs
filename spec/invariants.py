#!/usr/bin/env python3
from dataclasses import dataclass
@dataclass
class Invariant:
    name: str; check: callable; message: str
def _has_plan(o): return "plan_id" in o.get("body", {}) or "plan_id" in o
def _has_artifacts(o):
    a=o.get("body",{}).get("artifacts") or o.get("artifacts")
    return isinstance(a, list) and len(a)>=1
def _has_evidence(o):
    e=o.get("body",{}).get("evidence") or o.get("evidence")
    return isinstance(e, str) and e.endswith("evidence.json")
def _arts_nonempty(o):
    a=o.get("body",{}).get("artifacts") or o.get("artifacts") or []
    return all(isinstance(x,str) and x for x in a)
def _outcome_known(o):
    x=o.get("body",{}).get("outcome") or o.get("outcome")
    return x in ("accepted","failed","rejected")
INVARIANTS=[
    Invariant("I1",_has_plan,"missing plan_id"),
    Invariant("I2",_has_artifacts,"no artifacts"),
    Invariant("I3",_has_evidence,"no evidence"),
    Invariant("I4",_arts_nonempty,"empty artifact path"),
    Invariant("I5",_outcome_known,"unknown outcome"),
]
def check(o):
    fails=[]
    for inv in INVARIANTS:
        try:
            if not inv.check(o): fails.append({"invariant":inv.name,"message":inv.message})
        except Exception as e: fails.append({"invariant":inv.name,"message":str(e)})
    return (not fails, fails)
if __name__=="__main__":
    good={"body":{"plan_id":"p1","artifacts":["a"],"evidence":"e/evidence.json","outcome":"accepted"}}
    ok,f=check(good); assert ok and not f
    ok,f=check({"body":{"plan_id":"p1","artifacts":["a"],"outcome":"accepted"}})
    assert not ok and any("I3" in x["invariant"] for x in f)
    ok,f=check({"body":{"plan_id":"p1","artifacts":["a"],"evidence":"e/evidence.json","outcome":"x"}})
    assert not ok and any("I5" in x["invariant"] for x in f)
    print("invariants OK")
