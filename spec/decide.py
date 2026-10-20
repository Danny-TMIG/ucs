#!/usr/bin/env python3
"""decide.py — the calculus framework in which "99.9%" is well-defined.

Four objects, each the numerical form of a calculus primitive:

  1. break_even_batch(...)   root of T_hare(B) - T_cpu(B)
  2. deciding_rule(...)      sign of dT/dB at the break-even
  3. place(...)              constrained min T subject to A >= theta, with
                             Lagrange multiplier lambda (price of accuracy)
  4. measure(...)            Monte Carlo estimate + 95% CI of the accuracy
                             integral A = ∫ 1[match(x)] dP_D(x)

No function asserts an accuracy is achievable. They define what it would mean.
"""
import math
import random
from dataclasses import dataclass, field


# ---------- profiles ----------

@dataclass
class Placement:
    name: str
    launch: float        # fixed cost (s)
    per_unit: float      # time per unit of batch (s/unit)
    accuracy: float      # measured accuracy on the named distribution
    n_samples: int = 1000

    def finish_time(self, batch):
        return self.launch + self.per_unit * batch


@dataclass
class Constraint:
    theta: float         # required accuracy, e.g. 0.999
    ci_lower: float      # CI lower bound on the measured accuracy


# ---------- 1. break-even root ----------

def break_even_batch(hare: Placement, cpu: Placement):
    """Root of T_hare(B) - T_cpu(B) = 0.

    T_hare(B) = hare.launch + hare.per_unit * B
    T_cpu(B)  = cpu.launch  + cpu.per_unit  * B

    Solve: B* = (cpu.launch - hare.launch) / (hare.per_unit - cpu.per_unit)

    Returns None if the lines are parallel (no finite crossing).
    """
    denom = hare.per_unit - cpu.per_unit
    if abs(denom) < 1e-15:
        return None
    return (cpu.launch - hare.launch) / denom


# ---------- 2. deciding rule via derivative sign ----------

def deciding_rule(hare: Placement, cpu: Placement, batch: float):
    """Which placement wins, and which fable rule fires.

    d/dB [T_hare - T_cpu] = hare.per_unit - cpu.per_unit (constant).

    The winner is the one whose finish-time line is *below* at this B.
    The deciding rule names the bottleneck:

      - if the crossing is at B* and B > B*  -> 'sprint'      (hare, long race)
      - if B <= B*                            -> 'consistency' (cpu, short race)
      - if no crossing (parallel)             -> 'steady_climb' or 'compute_bound'
    """
    t_hare = hare.finish_time(batch)
    t_cpu = cpu.finish_time(batch)
    b_star = break_even_batch(hare, cpu)

    winner = "hare" if t_hare < t_cpu else "cpu"

    if b_star is None:
        # parallel lines: whoever is lower everywhere wins everywhere
        rule = "steady_climb" if winner == "cpu" else "compute_bound"
    elif batch > b_star:
        rule = "sprint" if winner == "hare" else "consistency"
    else:
        rule = "consistency" if winner == "cpu" else "sprint"

    margin = abs(t_hare - t_cpu) / max(t_hare, t_cpu)
    return {
        "winner": winner,
        "deciding_rule": rule,
        "batch": batch,
        "break_even_batch": b_star,
        "t_hare": t_hare,
        "t_cpu": t_cpu,
        "margin": margin,
    }


# ---------- 3. constrained min T subject to A >= theta ----------

def place(placements, constraint: Constraint, batch: float):
    """minimize T(placement) subject to A(placement) >= theta.

    Lagrangian: L = T - lambda * (A - theta).
    We solve by scanning feasible placements, reporting lambda as the
    marginal time saved per unit of accuracy *that was given up* to reach
    the chosen placement relative to the max-accuracy feasible placement.

    lambda >= 0: the price of accuracy in seconds per accuracy-unit.
    """
    feasible = [p for p in placements if p.accuracy >= constraint.theta]
    if not feasible:
        return {"feasible": False, "reason": "no placement meets theta",
                "theta": constraint.theta,
                "max_accuracy": max(p.accuracy for p in placements)}

    # fastest feasible placement
    best = min(feasible, key=lambda p: p.finish_time(batch))

    # lambda: seconds PAID per accuracy-unit GIVEN UP, relative to the
    # most-accurate feasible placement (the accuracy-optimal point).
    # Positive by construction: T_ref >= T_best whenever the fast placement
    # is genuinely faster. If the reference is faster *and* more accurate,
    # dT < 0 and dA < 0 still yield lambda >= 0 (best was dominated).
    ref = max(feasible, key=lambda p: p.accuracy)
    dA = ref.accuracy - best.accuracy
    dT = ref.finish_time(batch) - best.finish_time(batch)
    lam = (dT / dA) if abs(dA) > 1e-15 else 0.0
    # dominated placements: best is both faster and more accurate -> lam = 0
    if lam < 0:
        lam = 0.0

    return {
        "feasible": True,
        "placement": best.name,
        "batch": batch,
        "finish_time": best.finish_time(batch),
        "accuracy": best.accuracy,
        "theta": constraint.theta,
        "lambda": lam,          # seconds per accuracy-unit (price of accuracy)
        "reference": ref.name,
        "rejected": [
            {"name": p.name, "accuracy": p.accuracy, "finish_time": p.finish_time(batch)}
            for p in placements
            if p.name != best.name and p.accuracy >= constraint.theta
        ],
    }


# ---------- 4. Monte Carlo accuracy integral + CI ----------

def measure(distribution, predict, n=None, seed=0):
    """A = ∫ 1[match(x)] dP_D(x), estimated by Monte Carlo.

    distribution: list of (input, ground_truth) pairs (the named distribution D)
    predict:      function input -> answer
    Returns point estimate, 95% CI (normal approximation), and diagnostics.
    """
    rng = random.Random(seed)
    pairs = list(distribution)
    if n is not None and n < len(pairs):
        pairs = rng.sample(pairs, n)
    N = len(pairs)
    if N == 0:
        raise ValueError("empty distribution")
    matches = 0
    failures = []
    for x, gt in pairs:
        try:
            out = predict(x)
        except Exception as e:  # noqa: BLE001
            failures.append((x, f"exception: {e}"))
            continue
        if out == gt:
            matches += 1
        else:
            failures.append((x, {"expected": gt, "got": out}))
    rate = matches / N
    se = math.sqrt(rate * (1 - rate) / N) if N > 0 else 0.0
    ci_lower = max(0.0, rate - 1.96 * se)
    ci_upper = min(1.0, rate + 1.96 * se)
    return {
        "distribution_size": N,
        "matches": matches,
        "rate": rate,
        "se": se,
        "ci_95": (ci_lower, ci_upper),
        "meets_theta": None,     # filled by caller via check_theta
        "failures": failures[:10],
    }


def check_theta(result, constraint: Constraint):
    """Does the CI lower bound meet theta? That is the honest form of 99.9%."""
    ci_lower = result["ci_95"][0]
    result["meets_theta"] = ci_lower >= constraint.theta
    result["theta"] = constraint.theta
    return result


# ---------- self-tests ----------

if __name__ == "__main__":
    # Synthetic profiles with hand-computable closed forms.
    hare = Placement("gpu", launch=0.020, per_unit=0.001, accuracy=0.997)
    cpu = Placement("cpu", launch=0.000, per_unit=0.005, accuracy=0.999)

    # 1. break-even root, hand-computed:
    #    B* = (0 - 0.020) / (0.001 - 0.005) = 5.0
    b_star = break_even_batch(hare, cpu)
    assert abs(b_star - 5.0) < 1e-12, b_star
    print("1. break-even:", b_star, "(expected 5.0)")

    # 2. deciding rule: at B=1 cpu should win by consistency; at B=10 by sprint
    r1 = deciding_rule(hare, cpu, batch=1)
    assert r1["winner"] == "cpu", r1
    assert r1["deciding_rule"] == "consistency", r1
    r2 = deciding_rule(hare, cpu, batch=10)
    assert r2["winner"] == "hare", r2
    assert r2["deciding_rule"] == "sprint", r2
    print("2. rules:", r1["deciding_rule"], "->", r1["winner"],
          "|", r2["deciding_rule"], "->", r2["winner"])

    # 3. constrained placement: theta 0.999 leaves only cpu feasible.
    constraint = Constraint(theta=0.999, ci_lower=0.998)
    p1 = place([hare, cpu], constraint, batch=1)
    assert p1["feasible"] and p1["placement"] == "cpu", p1
    # theta 0.99 leaves both feasible; at B=100 hare is faster.
    constraint2 = Constraint(theta=0.99, ci_lower=0.985)
    p2 = place([hare, cpu], constraint2, batch=100)
    assert p2["feasible"] and p2["placement"] == "gpu", p2
    assert p2["lambda"] >= 0.0
    print("3. placement:", p1["placement"], "|", p2["placement"],
          "| lambda:", round(p2["lambda"], 6))

    # 4. measure: Monte Carlo of a known predictor on a synthetic distribution.
    #    Predictor is correct on evens, wrong on odds -> rate 0.5.
    dist = [(i, "even" if i % 2 == 0 else "odd") for i in range(1000)]
    def predict(i):
        return "even" if i % 2 == 0 else "WRONG"
    res = measure(dist, predict, seed=0)
    assert abs(res["rate"] - 0.5) < 1e-12, res["rate"]
    ci_lo, ci_hi = res["ci_95"]
    assert ci_lo <= 0.5 <= ci_hi
    # now a perfect predictor meets a high theta:
    res_perfect = check_theta(measure(dist, lambda i: "even" if i % 2 == 0 else "odd"), constraint)
    assert res_perfect["meets_theta"] is True, res_perfect
    print("4. measure: rate", res["rate"],
          "ci", (round(ci_lo, 4), round(ci_hi, 4)),
          "| perfect meets theta:", res_perfect["meets_theta"])

    # 5. honest failure: a fast placement rejected by the accuracy gate.
    fast_wrong = Placement("fast_wrong", launch=0.0, per_unit=0.0001, accuracy=0.90)
    p3 = place([fast_wrong, cpu], Constraint(theta=0.999, ci_lower=0.998), batch=1000)
    assert p3["feasible"] and p3["placement"] == "cpu", p3
    print("5. fast_wrong rejected; placement:", p3["placement"])

    print("decide.py OK")
