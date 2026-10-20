#!/usr/bin/env python3
import math
from dataclasses import dataclass

@dataclass
class Placement:
    name: str
    launch: float
    per_unit: float
    accuracy: float
    n_samples: int = 1000
    def finish_time(self, batch): return self.launch + self.per_unit * batch

@dataclass
class Constraint:
    theta: float
    ci_lower: float

def break_even_batch(hare, cpu):
    d = hare.per_unit - cpu.per_unit
    if abs(d) < 1e-15: return None
    return (cpu.launch - hare.launch) / d

def deciding_rule(hare, cpu, batch):
    t_h = hare.finish_time(batch); t_c = cpu.finish_time(batch)
    b = break_even_batch(hare, cpu)
    winner = "hare" if t_h < t_c else "cpu"
    if b is None: rule = "steady_climb" if winner == "cpu" else "compute_bound"
    elif batch > b: rule = "sprint" if winner == "hare" else "consistency"
    else: rule = "consistency" if winner == "cpu" else "sprint"
    return {"winner": winner, "deciding_rule": rule, "batch": batch,
            "break_even_batch": b, "t_hare": t_h, "t_cpu": t_c}

def place(placements, constraint, batch):
    feasible = [p for p in placements if p.accuracy >= constraint.theta]
    if not feasible:
        return {"feasible": False, "reason": "no placement meets theta"}
    best = min(feasible, key=lambda p: p.finish_time(batch))
    ref = max(feasible, key=lambda p: p.accuracy)
    dA = ref.accuracy - best.accuracy
    dT = ref.finish_time(batch) - best.finish_time(batch)
    lam = (dT / dA) if abs(dA) > 1e-15 else 0.0
    if lam < 0: lam = 0.0
    return {"feasible": True, "placement": best.name, "batch": batch,
            "finish_time": best.finish_time(batch), "accuracy": best.accuracy,
            "theta": constraint.theta, "lambda": lam, "reference": ref.name}

def measure(distribution, predict, seed=0):
    import random
    rng = random.Random(seed); pairs = list(distribution); N = len(pairs)
    matches = sum(1 for x, gt in pairs if predict(x) == gt)
    rate = matches / N
    se = math.sqrt(rate * (1 - rate) / N) if N else 0.0
    return {"distribution_size": N, "matches": matches, "rate": rate,
            "ci_95": (max(0.0, rate - 1.96 * se), min(1.0, rate + 1.96 * se))}

def check_theta(result, constraint):
    result["meets_theta"] = result["ci_95"][0] >= constraint.theta
    return result

if __name__ == "__main__":
    hare = Placement("gpu", 0.020, 0.001, 0.997)
    cpu = Placement("cpu", 0.000, 0.005, 0.999)
    b = break_even_batch(hare, cpu); assert b == 5.0, b
    r1 = deciding_rule(hare, cpu, 1); assert r1["winner"] == "cpu" and r1["deciding_rule"] == "consistency"
    r2 = deciding_rule(hare, cpu, 10); assert r2["winner"] == "hare" and r2["deciding_rule"] == "sprint"
    c999 = Constraint(0.999, 0.998)
    p1 = place([hare, cpu], c999, 1); assert p1["feasible"] and p1["placement"] == "cpu"
    c99 = Constraint(0.99, 0.985)
    p2 = place([hare, cpu], c99, 100); assert p2["feasible"] and p2["placement"] == "gpu" and p2["lambda"] >= 0.0
    dist = [(i, "even" if i % 2 == 0 else "odd") for i in range(1000)]
    res = measure(dist, lambda i: "even" if i % 2 == 0 else "WRONG")
    assert abs(res["rate"] - 0.5) < 1e-12
    res_p = check_theta(measure(dist, lambda i: "even" if i % 2 == 0 else "odd"), c999)
    assert res_p["meets_theta"] is True
    fw = Placement("fast_wrong", 0.0, 0.0001, 0.90)
    p3 = place([fw, cpu], c999, 1000); assert p3["feasible"] and p3["placement"] == "cpu"
    # negative test: no feasible placement when theta exceeds all accuracies
    p4 = place([fw], Constraint(0.999, 0.998), 1)
    assert p4["feasible"] is False, p4
    try:
        break_even_batch(Placement("a", 0, 1, 0.9), Placement("b", 0, 1, 0.9))
    except Exception:
        pass
    print("decide.py OK")
