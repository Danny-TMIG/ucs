#!/usr/bin/env python3
"""member.py — the identity layer that owns every state-changing adapter.

A member is:
  - id: a stable string (its handle)
  - capabilities: the set of things it is allowed to do
  - adapters: {name: fn} — state-changing operations it owns

A call is: member.invoke(adapter_name, payload)
  - checks member has the capability that the adapter requires
  - checks the adapter exists
  - checks the payload is JSON-serializable (so it can be hashed)
  - calls the adapter with the payload
  - records the call in the state ledger with the caller's identity
"""
import hashlib, json, pathlib, time

class NotAMember(Exception): pass
class MissingCapability(Exception): pass
class UnknownAdapter(Exception): pass
class BadPayload(Exception): pass

STATE = pathlib.Path("build/_members")

def _digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, default=str).encode()).hexdigest()

class Member:
    def __init__(self, id, capabilities, adapters):
        if not id or not isinstance(id, str):
            raise NotAMember("id must be a non-empty string")
        self.id = id
        self.capabilities = set(capabilities)
        self.adapters = dict(adapters)
        self._log = STATE / f"{id}.json"

    def _record(self, entry):
        entries = json.loads(self._log.read_text()) if self._log.exists() else []
        prev = entries[-1]["hash"] if entries else None
        entry = {**entry, "prev_hash": prev, "ts": time.time()}
        entry["hash"] = _digest(entry)
        entries.append(entry)
        self._log.parent.mkdir(parents=True, exist_ok=True)
        self._log.write_text(json.dumps(entries, indent=2))
        return entry

    def invoke(self, adapter_name, payload, capability_required=None):
        if adapter_name not in self.adapters:
            raise UnknownAdapter(f"{self.id} has no adapter {adapter_name!r}")
        if capability_required and capability_required not in self.capabilities:
            raise MissingCapability(f"{self.id} lacks {capability_required!r}")
        try:
            json.dumps(payload, default=str)
        except (TypeError, ValueError) as e:
            raise BadPayload(f"payload not serializable: {e}")
        self._record({"action": "invoke", "adapter": adapter_name,
                      "capability": capability_required,
                      "payload_hash": _digest(payload)})
        result = self.adapters[adapter_name](payload)
        self._record({"action": "result", "adapter": adapter_name,
                      "result_hash": _digest(result)})
        return result

    def log(self):
        return json.loads(self._log.read_text()) if self._log.exists() else []

if __name__ == "__main__":
    import tempfile, os
    os.chdir(tempfile.mkdtemp())
    m = Member("alice", {"write", "read"}, {"write_kv": lambda p: {"ok": True, "k": p["k"]}})
    r = m.invoke("write_kv", {"k": "x", "v": 1}, capability_required="write")
    assert r == {"ok": True, "k": "x"}
    log = m.log()
    assert len(log) == 2 and log[0]["action"] == "invoke" and log[1]["action"] == "result"
    # negative: missing capability
    try:
        m.invoke("write_kv", {}, capability_required="admin")
    except MissingCapability:
        pass
    else:
        raise SystemExit("should raise MissingCapability")
    # negative: unknown adapter
    try:
        m.invoke("nope", {})
    except UnknownAdapter:
        pass
    else:
        raise SystemExit("should raise UnknownAdapter")
    # negative: empty id
    try:
        Member("", set(), {})
    except NotAMember:
        pass
    else:
        raise SystemExit("should raise NotAMember on empty id")
    print("member OK: identity, capability, adapter, log, three refusals verified")
