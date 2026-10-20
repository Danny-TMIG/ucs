#!/usr/bin/env python3
"""atlas.py — typed graph of IR records with composition and generative downstream."""
import threading


class CycleError(Exception):
    pass


class NoSuchNode(Exception):
    pass


class Node:
    __slots__ = ("kind", "id", "data", "edges_out")

    def __init__(self, kind, id, data, edges_out=None):
        self.kind = kind
        self.id = id
        self.data = data
        self.edges_out = list(edges_out or [])

    def __repr__(self):
        return f"Node({self.kind}, {self.id!r}, out={len(self.edges_out)})"


class Atlas:
    def __init__(self):
        self._nodes = {}
        self._lock = threading.Lock()
        self._regens = {}

    def add(self, node):
        with self._lock:
            if node.id in self._nodes:
                raise ValueError(f"duplicate node id: {node.id}")
            self._nodes[node.id] = node
            return node

    def add_edge(self, src_id, edge_kind, dst_id):
        """Adding src->dst forms a cycle iff src is reachable FROM dst."""
        with self._lock:
            if src_id == dst_id:
                raise CycleError(f"self-loop: {src_id}")
            if src_id in self._reachable(dst_id):
                raise CycleError(f"edge {src_id}->{dst_id} would form cycle")
            self._nodes[src_id].edges_out.append((edge_kind, dst_id))

    def _reachable(self, start):
        seen = set()
        stack = [start]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            n = self._nodes.get(cur)
            if n is None:
                continue
            for _, child in n.edges_out:
                if child not in seen:
                    stack.append(child)
        return seen

    def get(self, node_id):
        n = self._nodes.get(node_id)
        if n is None:
            raise NoSuchNode(node_id)
        return n

    def downstream(self, node_id):
        out = []
        seen = {node_id}
        frontier = [node_id]
        while frontier:
            cur = frontier.pop(0)
            n = self._nodes.get(cur)
            if n is None:
                continue
            for _, child in n.edges_out:
                if child in seen:
                    continue
                seen.add(child)
                out.append(child)
                frontier.append(child)
        return out

    def by_class(self, pred):
        return [n.id for n in self._nodes.values() if pred(n)]

    def register_regenerator(self, kind, fn):
        self._regens[kind] = fn

    def call(self, node_id):
        order = self.downstream(node_id)
        regenerated = []
        for nid in order:
            n = self._nodes[nid]
            fn = self._regens.get(n.kind)
            if fn is not None:
                new_data = fn(n)
                if new_data is not None:
                    n.data = new_data
            regenerated.append(nid)
        return regenerated


if __name__ == "__main__":
    a = Atlas()
    a.add(Node("intent", "i1", {"goal": "build foo"}))
    a.add(Node("plan", "p1", {"plan_id": "p1"}))
    a.add(Node("artifact", "a1", {"path": "build/p1/handlers/foo.py"}))
    a.add(Node("artifact", "a2", {"path": "build/p1/tests/test_foo.py"}))
    a.add(Node("test", "t1", {"passed": True}))
    a.add(Node("evidence", "e1", {"passed": True, "path": "build/p1/evidence.json"}))

    a.add_edge("i1", "decomposes_to", "p1")
    a.add_edge("p1", "has_artifact", "a1")
    a.add_edge("p1", "has_artifact", "a2")
    a.add_edge("a2", "tested_by", "t1")
    a.add_edge("t1", "recorded_as", "e1")

    ds = a.downstream("i1")
    assert ds == ["p1", "a1", "a2", "t1", "e1"], ds
    assert a.by_class(lambda n: n.kind == "artifact") == ["a1", "a2"]
    assert a.by_class(lambda n: n.kind == "evidence" and n.data.get("passed")) == ["e1"]

    # cycle: e1 -> i1 must raise
    try:
        a.add_edge("e1", "would_cycle", "i1")
        raise SystemExit("FAIL: expected CycleError on e1->i1")
    except CycleError as e:
        assert "cycle" in str(e).lower(), e

    # self-loop
    try:
        a.add_edge("p1", "self", "p1")
        raise SystemExit("FAIL: expected CycleError on p1->p1")
    except CycleError as e:
        assert "self" in str(e).lower(), e

    # duplicate id
    try:
        a.add(Node("plan", "p1", {}))
        raise SystemExit("FAIL: expected ValueError on duplicate p1")
    except ValueError as e:
        assert "duplicate" in str(e).lower(), e

    def regen_artifact(n):
        n.data["regenerated"] = True
        return n.data

    def regen_test(n):
        n.data["reran"] = True
        return n.data

    a.register_regenerator("artifact", regen_artifact)
    a.register_regenerator("test", regen_test)

    regenerated = a.call("p1")
    assert regenerated == ["a1", "a2", "t1", "e1"], regenerated
    assert a.get("a1").data.get("regenerated") is True
    assert a.get("a2").data.get("regenerated") is True
    assert a.get("t1").data.get("reran") is True
    assert a.get("e1").data.get("regenerated") is None
    print("atlas OK")
