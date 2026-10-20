#!/usr/bin/env python3
"""invariants.py — the loop's own invariants, checked after every run."""
from dataclasses import dataclass


@dataclass
class Invariant:
    name: str
    check: callable
    message: str


def _has_plan(outcome):
    return "plan_id" in outcome.get("body", {}) or "plan_id" in outcome


def _has_artifacts(outcome):
    arts = outcome.get("body", {}).get("artifacts") or outcome.get("artifacts")
    return isinstance(arts, list) and len(arts) >= 1


def _has_evidence(outcome):
    ev = outcome.get("body", {}).get("evidence") or outcome.get("evidence")
    return isinstance(ev, str) and ev.endswith("evidence.json")


def _every_artifact_has_kind(outcome):
    arts = outcome.get("body", {}).get("artifacts") or outcome.get("artifacts") or []
    return all(isinstance(a, str) and a for a in arts)


def _outcome_is_known(outcome):
    o = outcome.get("body", {}).get("outcome") or outcome.get("outcome")
    return o in ("accepted", "failed", "rejected")


INVARIANTS = [
    Invariant("I1 has plan_id", _has_plan, "governed-outcome missing plan_id"),
    Invariant("I2 has artifacts", _has_artifacts, "governed-outcome has no artifacts"),
    Invariant("I3 has evidence path", _has_evidence, "governed-outcome has no evidence path"),
    Invariant("I4 artifact paths non-empty", _every_artifact_has_kind,
              "an artifact path is empty or non-string"),
    Invariant("I5 outcome is known", _outcome_is_known,
              "outcome is not accepted/failed/rejected"),
]


def check(outcome):
    failures = []
    for inv in INVARIANTS:
        try:
            if not inv.check(outcome):
                failures.append({"invariant": inv.name, "message": inv.message})
        except Exception as e:  # noqa: BLE001
            failures.append({"invariant": inv.name, "message": f"raised: {e}"})
    return (not failures, failures)


if __name__ == "__main__":
    good = {"body": {
        "plan_id": "p1", "artifacts": ["build/p1/handlers/foo.py"],
        "evidence": "build/p1/evidence.json", "outcome": "accepted",
    }}
    ok, fails = check(good)
    assert ok and not fails, fails

    bad = {"body": {"plan_id": "p1", "artifacts": ["x"], "outcome": "accepted"}}
    ok, fails = check(bad)
    assert not ok and any("I3" in f["invariant"] for f in fails), fails

    bad2 = {"body": {"plan_id": "p1", "artifacts": ["x"],
                     "evidence": "e/evidence.json", "outcome": "weird"}}
    ok, fails = check(bad2)
    assert not ok and any("I5" in f["invariant"] for f in fails), fails

    print("invariants OK")
