PRIMITIVES = {
    "read":     {"in": "source",    "out": "bytes"},
    "write":    {"in": "bytes",     "out": "sink"},
    "parse":    {"in": "bytes",     "out": "typed"},
    "resolve":  {"in": "typed",     "out": "typed"},
    "validate": {"in": "typed",     "out": "errors"},
    "transform":{"in": "typed",     "out": "typed"},
    "execute":  {"in": "typed",     "out": "result"},
    "observe":  {"in": "result",    "out": "evidence"},
    "decide":   {"in": "evidence",  "out": "verdict"},
    "persist":  {"in": "typed",     "out": "state"},
    "publish":  {"in": "state",     "out": "external"},
}

class Agent:
    __slots__ = ("id", "primitive", "in_type", "out_type", "neighbors")
    def __init__(self, id, primitive):
        self.id = id
        self.primitive = primitive
        self.in_type = PRIMITIVES[primitive]["in"]
        self.out_type = PRIMITIVES[primitive]["out"]
        self.neighbors = []

def compatible(a, b):
    if a.id == b.id:
        return False
    if a.primitive == b.primitive and a.out_type == a.in_type:
        return False
    return a.out_type == b.in_type

def flock(primitive, n):
    return [Agent(f"{primitive}-{i}", primitive) for i in range(n)]

def murmurate(agents):
    for a in agents:
        a.neighbors = [b for b in agents if compatible(a, b)]

def route(start_id, agents, hops=20):
    by_id = {a.id: a for a in agents}
    cur = by_id[start_id]
    trace = [cur.id]
    seen = {cur.id}
    for _ in range(hops):
        nxt = next((b for b in cur.neighbors if b.id not in seen), None)
        if nxt is None:
            break
        cur = nxt
        trace.append(cur.id)
        seen.add(cur.id)
    return trace

def shape(agents):
    murmurate(agents)
    edges = sum(len(a.neighbors) for a in agents)
    primitives = sorted({a.primitive for a in agents})
    longest = 0
    for a in agents:
        t = route(a.id, agents, hops=len(agents) + 1)
        longest = max(longest, len(t))
    return {"agents": len(agents), "edges": edges,
            "primitives": primitives, "longest_chain": longest}

def assemble(primitives, n_each=1):
    agents = []
    for p in primitives:
        agents.extend(flock(p, n_each))
    murmurate(agents)
    return agents

if __name__ == "__main__":
    stack = ["read", "parse", "transform", "execute", "observe", "decide", "persist", "publish"]
    agents = assemble(stack, n_each=2)
    s = shape(agents)
    trace = route("read-0", agents, hops=len(agents) + 1)
    assert trace[0] == "read-0", trace
    assert trace[-1].startswith("publish-"), trace
    assert len(trace) >= 6, trace
    solo = assemble(["validate"], n_each=1)
    assert shape(solo)["edges"] == 0
    t2 = assemble(["read","parse","transform","write"])
    assert route("write-0", t2) == ["write-0"]
    print(f"murmuration OK: {s['agents']} agents, {s['edges']} edges, "
          f"chain {len(trace)}, longest {s['longest_chain']}, trace {trace}")
