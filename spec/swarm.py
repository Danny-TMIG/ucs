\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
import copy
import pathlib
import sys
import uuid
import atlas
import revise
import decide
class InvariantViolation(Exception):
    pass
def _assert_identity(agents):
    """I1: all agents structurally identical (same keys, same shape)."""
    if len(agents) < 2:
        return
    base = agents[0]["data"]
    for a in agents[1:]:
        if set(a["data"].keys()) != set(base.keys()):
            raise InvariantViolation("I1 identity: agents have different shapes")
def _assert_locality(agent, neighbors, feedback):
    """I2: feedback dict only contains keys the agent or its neighbors own."""
    own = set(feedback.get("own", {}).keys())
    neighbor = set()
    for n in neighbors:
        neighbor |= set(n.get("shared", {}).keys())
    claimed = set(feedback.get("claimed_keys", set()))
    if not claimed.issubset(own | neighbor):
        raise InvariantViolation(
            f"I2 locality: feedback claims keys not owned locally: "
            f"{claimed - (own | neighbor)}")
def _assert_selection(fitness, distribution):
    """I3: fitness is a number, distribution is a non-empty named set."""
    if not isinstance(fitness, (int, float)):
        raise InvariantViolation("I3 selection: fitness not numeric")
    if not distribution or "name" not in distribution:
        raise InvariantViolation("I3 selection: distribution must have a name")
def _assert_redundancy(agents, removed_id, assignments):
    """I4: after removing one agent, at least one agent remains and every
    agent in `agents` is assigned a task (the lattice can absorb the loss)."""
    remaining = [a["id"] for a in agents if a["id"] != removed_id]
    if not remaining:
        raise InvariantViolation("I4 redundancy: no agents remain")
    for a in agents:
        if a["id"] not in assignments:
            raise InvariantViolation(f"I4 redundancy: agent {a['id']} unassigned")
        if not assignments[a["id"]]:
            raise InvariantViolation(f"I4 redundancy: agent {a['id']} has no tasks")
def spawn(base_plan, n):
    """Stage 1. Deep-copy the base plan into n identical agents."""
    agents = []
    for _ in range(n):
        a = {
            "id": str(uuid.uuid4()),
            "data": copy.deepcopy(base_plan),
            "shared": {},
            "specialized": False,
        }
        agents.append(a)
    _assert_identity(agents)
    return agents
def specialize(agents, feedback_by_id, assignments=None):
    """Stage 2. Each agent updates from its own feedback only."""
    for a in agents:
        fb = feedback_by_id.get(a["id"], {})
        _assert_locality(a, [], fb)
        a["data"] = {**a["data"], "specialization": fb.get("own", {})}
        a["shared"] = fb.get("shared", {})
        a["specialized"] = True
    return agents
def connect(agents, topology="path"):
    """Stage 3. Build the lattice as a DAG (atlas rejects cycles).
    topologies:
      path  — agent[i] -> agent[i+1]        (n-1 edges, DAG)
      star  — agent[0] -> agent[i]  i>0     (n-1 edges, DAG)
      ring  — rejected: would cycle; falls back to path
    """
    g = atlas.Atlas()
    for a in agents:
        g.add(atlas.Node("agent", a["id"], {"shared": a["shared"]}))
    ids = [a["id"] for a in agents]
    if topology in ("path", "ring"):
        for i in range(len(ids) - 1):
            g.add_edge(ids[i], "neighbor", ids[i + 1])
        if topology == "ring":
            g._ring_fallback = True
    elif topology == "star":
        hub = ids[0]
        for other in ids[1:]:
            g.add_edge(hub, "neighbor", other)
    return g
def select(agents, fitness_by_id, distribution):
    """Stage 4. Compute fitness; bias next spawn toward high fitness."""
    ranked = []
    for a in agents:
        f = fitness_by_id.get(a["id"], 0.0)
        _assert_selection(f, distribution)
        ranked.append({"id": a["id"], "fitness": f})
    ranked.sort(key=lambda x: -x["fitness"])
    keep = max(1, len(ranked) // 2)
    return {"ranked": ranked, "survivors": ranked[:keep],
            "distribution": distribution}
def deploy(agents, assignments):
    """Stage 5. Verify redundancy, return deployment record."""
    for a in agents:
        if a["id"] not in assignments:
            raise InvariantViolation(f"deploy: agent {a['id']} unassigned")
    _assert_redundancy(agents, agents[-1]["id"], assignments)
    return {"agents": len(agents), "assigned": len(assignments),
            "topology": "connected"}
def swarm_cycle(base_intent, n=3, cycles=2,
                distribution=None):
    if distribution is None:
        distribution = {"name": "toy", "cases": 10}
    history = []
    base_plan = base_intent
    for cycle in range(1, cycles + 1):
        agents = spawn(base_plan, n)
        feedback = {a["id"]: {"own": {"cycle": cycle}, "shared": {}}
                    for a in agents}
        agents = specialize(agents, feedback)
        g = connect(agents, topology="path")
        fitness = {a["id"]: float(n - i) for i, a in enumerate(agents)}
        sel = select(agents, fitness, distribution)
        assignments = {a["id"]: [f"task-{cycle}-{i}"]
                       for i, a in enumerate(agents)}
        dep = deploy(agents, assignments)
        history.append({
            "cycle": cycle,
            "n_agents": len(agents),
            "survivors": [s["id"] for s in sel["survivors"]],
            "topology_edges": len(g.downstream(agents[0]["id"])),
            "deployed": dep,
        })
        best = sel["survivors"][0]["id"]
        best_agent = next(a for a in agents if a["id"] == best)
        base_plan = {**best_agent["data"]}
    return {"cycles": cycles, "n": n, "history": history}
if __name__ == "__main__":
    base_intent = {"goal": "build foo", "acceptance": ["foo returns ok"]}
    agents = spawn(base_intent, 3)
    assert len(agents) == 3
    _assert_identity(agents)
    agents = specialize(agents, {a["id"]: {"own": {"k": 1}} for a in agents})
    assert all(a["specialized"] for a in agents)
    try:
        _assert_locality({"shared": {}}, [],
                         {"claimed_keys": {"ghost"}})
        raise SystemExit("I2 should have failed")
    except InvariantViolation as e:
        assert "locality" in str(e), e
    sel = select(agents, {a["id"]: 1.0 for a in agents},
                 {"name": "test", "cases": 5})
    assert len(sel["survivors"]) >= 1
    try:
        _assert_selection("not-a-number", {"name": "t"})
        raise SystemExit("I3 should have failed")
    except InvariantViolation as e:
        assert "selection" in str(e), e
    assignments = {a["id"]: [f"t{i}"] for i, a in enumerate(agents)}
    dep = deploy(agents, assignments)
    assert dep["agents"] == 3
    out = swarm_cycle(base_intent, n=3, cycles=2)
    assert len(out["history"]) == 2
    for h in out["history"]:
        assert h["n_agents"] == 3
        assert h["deployed"]["agents"] == 3
    print("swarm OK")
