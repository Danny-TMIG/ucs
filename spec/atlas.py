#!/usr/bin/env python3
import threading
class CycleError(Exception): pass
class NoSuchNode(Exception): pass
class Node:
    __slots__ = ("kind", "id", "data", "edges_out")
    def __init__(self, kind, id, data, edges_out=None):
        self.kind=kind; self.id=id; self.data=data; self.edges_out=list(edges_out or [])
class Atlas:
    def __init__(self):
        self._nodes={}; self._lock=threading.Lock(); self._regens={}
    def add(self, node):
        with self._lock:
            if node.id in self._nodes: raise ValueError(f"duplicate node id: {node.id}")
            self._nodes[node.id]=node; return node
    def add_edge(self, src_id, edge_kind, dst_id):
        with self._lock:
            if src_id==dst_id: raise CycleError(f"self-loop: {src_id}")
            if src_id in self._reachable(dst_id): raise CycleError(f"edge {src_id}->{dst_id} would form cycle")
            self._nodes[src_id].edges_out.append((edge_kind, dst_id))
    def _reachable(self, start):
        seen=set(); stack=[start]
        while stack:
            cur=stack.pop()
            if cur in seen: continue
            seen.add(cur)
            n=self._nodes.get(cur)
            if n is None: continue
            for _,child in n.edges_out:
                if child not in seen: stack.append(child)
        return seen
    def get(self, node_id):
        n=self._nodes.get(node_id)
        if n is None: raise NoSuchNode(node_id)
        return n
    def downstream(self, node_id):
        out=[]; seen={node_id}; frontier=[node_id]
        while frontier:
            cur=frontier.pop(0); n=self._nodes.get(cur)
            if n is None: continue
            for _,child in n.edges_out:
                if child in seen: continue
                seen.add(child); out.append(child); frontier.append(child)
        return out
    def by_class(self, pred): return [n.id for n in self._nodes.values() if pred(n)]
    def register_regenerator(self, kind, fn): self._regens[kind]=fn
    def call(self, node_id):
        order=self.downstream(node_id); regenerated=[]
        for nid in order:
            n=self._nodes[nid]; fn=self._regens.get(n.kind)
            if fn is not None:
                nd=fn(n)
                if nd is not None: n.data=nd
            regenerated.append(nid)
        return regenerated

if __name__ == "__main__":
    a=Atlas()
    for k,i,d in [("intent","i1",{"goal":"build foo"}),("plan","p1",{"plan_id":"p1"}),
                  ("artifact","a1",{}),("artifact","a2",{}),("test","t1",{"passed":True}),
                  ("evidence","e1",{"passed":True})]:
        a.add(Node(k,i,d))
    a.add_edge("i1","decomposes_to","p1"); a.add_edge("p1","has_artifact","a1")
    a.add_edge("p1","has_artifact","a2"); a.add_edge("a2","tested_by","t1")
    a.add_edge("t1","recorded_as","e1")
    assert a.downstream("i1")==["p1","a1","a2","t1","e1"]
    try:
        a.add_edge("e1","would_cycle","i1"); raise SystemExit("expected CycleError")
    except CycleError: pass
    try:
        a.add_edge("p1","self","p1"); raise SystemExit("expected self CycleError")
    except CycleError: pass
    try:
        a.add(Node("plan","p1",{})); raise SystemExit("expected ValueError")
    except ValueError: pass
    def ra(n): n.data["regenerated"]=True; return n.data
    def rt(n): n.data["reran"]=True; return n.data
    a.register_regenerator("artifact", ra); a.register_regenerator("test", rt)
    assert a.call("p1")==["a1","a2","t1","e1"]
    print("atlas OK")
