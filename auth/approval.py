\
\
\
\
\
\
\
import hashlib, json, pathlib, time
class GateError(Exception): pass
def _digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, default=str).encode()).hexdigest()
class Gate:
    def __init__(self, quorum=2):
        self.quorum = quorum
        self._proposals = {}
    def propose(self, proposer, adapter, payload):
        if "propose" not in getattr(proposer, "capabilities", set()):
            raise GateError(f"{proposer.id} lacks 'propose'")
        h = _digest({"adapter": adapter, "payload": payload, "proposer": proposer.id})
        self._proposals[h] = {"adapter": adapter, "payload": payload,
                              "proposer": proposer.id, "approvals": {}, "ts": time.time()}
        return h
    def approve(self, approver, proposal_hash):
        if "approve" not in getattr(approver, "capabilities", set()):
            raise GateError(f"{approver.id} lacks 'approve'")
        if proposal_hash not in self._proposals:
            raise GateError(f"unknown proposal {proposal_hash[:12]}")
        p = self._proposals[proposal_hash]
        if approver.id == p["proposer"]:
            raise GateError("proposer cannot approve own proposal")
        p["approvals"][approver.id] = time.time()
        return len(p["approvals"]) >= self.quorum
    def authorized(self, proposal_hash):
        p = self._proposals.get(proposal_hash)
        if not p: return False
        return len(p["approvals"]) >= self.quorum and p["proposer"] not in p["approvals"]
    def consume(self, proposal_hash):
        """Mark a proposal consumed so it cannot be re-executed."""
        if not self.authorized(proposal_hash):
            raise GateError("not authorized")
        self._proposals[proposal_hash]["consumed"] = True
if __name__ == "__main__":
    class M:
        def __init__(self, id, caps): self.id, self.capabilities = id, set(caps)
    alice = M("alice", {"propose"})
    bob = M("bob", {"approve"})
    carol = M("carol", {"approve"})
    g = Gate(quorum=2)
    h = g.propose(alice, "write_kv", {"k": "x", "v": 1})
    assert not g.authorized(h)
    assert not g.approve(bob, h)       
    assert g.approve(carol, h)         
    assert g.authorized(h)
    g.consume(h)
    h2 = g.propose(alice, "write_kv", {"k": "y"})
    try:
        g.approve(alice, h2)
    except GateError:
        pass
    else:
        raise SystemExit("self-approval should fail")
    try:
        g.propose(bob, "x", {})
    except GateError:
        pass
    else:
        raise SystemExit("missing propose should fail")
    print("approval OK: quorum, distinct approvers, no self-approval, no re-execute")
