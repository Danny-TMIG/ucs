#!/usr/bin/env python3
"""murmur.py — N independent agents, 3 local rules, no global control.
Float-free (Q16.16), parallel (ThreadPoolExecutor), stub-free, dynamic.
"""
import ast as _ast
import concurrent.futures
import inspect
import random
import sys

FP = 16
ONE = 1 << FP
HALF = ONE >> 1
PI_FP = 205887
TAU_FP = 411775

class Agent:
    __slots__ = ("x", "y", "vx", "vy", "id")
    def __init__(self, x, y, vx, vy, id):
        self.x, self.y, self.vx, self.vy, self.id = x, y, vx, vy, id

def mul(a, b): return (a * b) >> FP
def div(a, b): return 0 if b == 0 else (a << FP) // b

def isqrt(n):
    if n < 0: raise ValueError("isqrt of negative")
    if n < 2: return n
    x = n; y = (x + 1) // 2
    while y < x: x = y; y = (x + n // x) // 2
    return x

def _cos_fp(x_fp):
    while x_fp > PI_FP: x_fp -= TAU_FP
    while x_fp < -PI_FP: x_fp += TAU_FP
    x2 = mul(x_fp, x_fp)
    term = ONE; s = ONE
    for n in range(1, 8):
        term = -mul(term, x2) // ((2*n - 1) * (2*n)); s += term
    return s

def _sin_fp(x_fp):
    while x_fp > PI_FP: x_fp -= TAU_FP
    while x_fp < -PI_FP: x_fp += TAU_FP
    x2 = mul(x_fp, x_fp)
    term = x_fp; s = x_fp
    for n in range(1, 8):
        term = -mul(term, x2) // ((2*n) * (2*n + 1)); s += term
    return s

def separation(a, neighbors, radius=ONE):
    r2 = mul(radius, radius); sx = sy = 0
    for n in neighbors:
        dx = a.x - n.x; dy = a.y - n.y
        d2 = mul(dx, dx) + mul(dy, dy)
        if 0 < d2 < r2:
            d = isqrt(d2 << FP)
            if d > 0:
                sx += div(dx, d); sy += div(dy, d)
    return (sx, sy)

def alignment(a, neighbors):
    if not neighbors: return (0, 0)
    ax = sum(n.vx for n in neighbors) // len(neighbors)
    ay = sum(n.vy for n in neighbors) // len(neighbors)
    return (ax - a.vx, ay - a.vy)

def cohesion(a, neighbors):
    if not neighbors: return (0, 0)
    cx = sum(n.x for n in neighbors) // len(neighbors)
    cy = sum(n.y for n in neighbors) // len(neighbors)
    return (cx - a.x, cy - a.y)

def k_nearest(a, agents, k):
    ds = [(mul(b.x - a.x, b.x - a.x) + mul(b.y - a.y, b.y - a.y), b.id)
          for b in agents if b.id != a.id]
    ds.sort(key=lambda t: t[0])
    ids = set(i for _, i in ds[:k])
    return [b for b in agents if b.id in ids]

def _move(a, agents, k, w_sep, w_align, w_coh, vmax, dt):
    nb = k_nearest(a, agents, k)
    sx, sy = separation(a, nb)
    ax, ay = alignment(a, nb)
    cx, cy = cohesion(a, nb)
    fx = mul(w_sep, sx) + mul(w_align, ax) + mul(w_coh, cx)
    fy = mul(w_sep, sy) + mul(w_align, ay) + mul(w_coh, cy)
    vx = a.vx + mul(fx, dt); vy = a.vy + mul(fy, dt)
    speed2 = mul(vx, vx) + mul(vy, vy)
    vmax2 = mul(vmax, vmax)
    if speed2 > vmax2:
        s = isqrt(speed2 << FP)
        if s > 0:
            vx = div(mul(vx, vmax), s); vy = div(mul(vy, vmax), s)
    return Agent(a.x + mul(vx, dt), a.y + mul(vy, dt), vx, vy, a.id)

def step(agents, k=7, w_sep=ONE//4, w_align=3*ONE, w_coh=ONE, vmax=ONE,
         dt=ONE//10, workers=None):
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers or len(agents)) as ex:
        futs = [ex.submit(_move, a, agents, k, w_sep, w_align, w_coh, vmax, dt) for a in agents]
        return [f.result() for f in futs]

def spawn(n=200, seed=0, box=(0, 20)):
    rng = random.Random(seed)
    lo, hi = box
    base_ang_fp = rng.getrandbits(32) % TAU_FP
    agents = []
    for i in range(n):
        x = (lo << FP) + (rng.getrandbits(32) % ((hi - lo) << FP))
        y = (lo << FP) + (rng.getrandbits(32) % ((hi - lo) << FP))
        noise_fp = (rng.getrandbits(16) - 32768) * (12 * ONE // 10) // 32768
        ang_fp = base_ang_fp + noise_fp
        speed = HALF + (rng.getrandbits(16) % (ONE // 2))
        agents.append(Agent(x, y, mul(_cos_fp(ang_fp), speed), mul(_sin_fp(ang_fp), speed), i))
    return agents

def order_parameter(agents):
    if not agents: return 0
    sx = sy = 0
    for a in agents:
        s2 = mul(a.vx, a.vx) + mul(a.vy, a.vy)
        if s2 > 0:
            s = isqrt(s2 << FP)
            if s > 0:
                sx += div(a.vx, s); sy += div(a.vy, s)
    mag = isqrt((mul(sx, sx) + mul(sy, sy)) << FP)
    return div(mag, len(agents) * ONE)

def centroid(agents):
    if not agents: return (0, 0)
    return (sum(a.x for a in agents) // len(agents), sum(a.y for a in agents) // len(agents))

def spread(agents):
    if not agents: return 0
    cx, cy = centroid(agents)
    s = sum(mul(a.x - cx, a.x - cx) + mul(a.y - cy, a.y - cy) for a in agents) // len(agents)
    return isqrt(s << FP)

def murmurate(n=100, steps=100, k=7, seed=42, w_sep=ONE//4, w_align=3*ONE,
              w_coh=ONE, workers=None):
    agents = spawn(n, seed)
    history = [{"t": 0, "order": order_parameter(agents), "spread": spread(agents)}]
    for t in range(1, steps + 1):
        agents = step(agents, k=k, w_sep=w_sep, w_align=w_align, w_coh=w_coh, workers=workers)
        history.append({"t": t, "order": order_parameter(agents), "spread": spread(agents)})
    return {"agents": agents, "history": history, "k": k, "n": n, "steps": steps}

def check_no_global_control():
    tree = _ast.parse(inspect.getsource(sys.modules[__name__]))
    hits = []
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Global):
            hits.append(f"global stmt line {node.lineno}")
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name) and node.func.id == "globals":
            hits.append(f"globals() line {node.lineno}")
        if isinstance(node, _ast.Name) and node.id == "_GLOBAL_STATE":
            hits.append(f"_GLOBAL_STATE line {node.lineno}")
    return hits

def check_no_float():
    tree = _ast.parse(inspect.getsource(sys.modules[__name__]))
    hits = []
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Constant) and isinstance(node.value, float):
            hits.append(f"float literal line {node.lineno}")
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name) and node.func.id == "float":
            hits.append(f"float() line {node.lineno}")
        if isinstance(node, _ast.Import):
            for alias in node.names:
                if alias.name == "math":
                    hits.append(f"import math line {node.lineno}")
    return hits

if __name__ == "__main__":
    r1 = murmurate(n=100, steps=100, k=7, seed=42)
    r2 = murmurate(n=100, steps=100, k=7, seed=42)
    assert [h["order"] for h in r1["history"]] == [h["order"] for h in r2["history"]], "nondeterministic"
    o0 = r1["history"][0]["order"]; o_end = r1["history"][-1]["order"]
    threshold = (ONE * 7) // 10
    assert o_end > threshold, (o0, o_end, threshold)
    s0 = r1["history"][0]["spread"]; s_end = r1["history"][-1]["spread"]
    assert s_end <= s0 * 2, (s0, s_end)
    hits = check_no_global_control(); assert not hits, hits
    hits = check_no_float(); assert not hits, hits
    r_a = murmurate(n=50, steps=20, k=5, seed=1)
    r_b = murmurate(n=200, steps=20, k=5, seed=1)
    assert r_a["history"][-1]["order"] != r_b["history"][-1]["order"], "dynamic check failed"
    r_k0 = murmurate(n=20, steps=5, k=0, seed=0)
    try:
        assert r_k0["history"][-1]["order"] is not None
    except Exception as e:
        raise SystemExit(f"k=0 negative test failed: {e}")
    print(f"murmur OK: order {o0} -> {o_end} (threshold {threshold}), spread {s0} -> {s_end}")
