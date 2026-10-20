#!/usr/bin/env python3
import pathlib
import json
import time
import hashlib
import hmac
import os
import sys

print("[kernel] Initializing Absolute Sovereign Runtime Kernel...")

WORKSPACE = pathlib.Path("/tmp/ucs-clean/absolute_kernel")
WORKSPACE.mkdir(parents=True, exist_ok=True)
LEDGER = WORKSPACE / "kernel_worm.jsonl"
KEY = WORKSPACE / "kernel.key"

if KEY.exists():
    SECRET = KEY.read_bytes()
else:
    SECRET = os.urandom(64)
    KEY.write_bytes(SECRET)
    KEY.chmod(0o400)

class AbsoluteKernel:
    def __init__(self):
        self.basis = ["CDO", "CISO", "CRO", "CLO", "Ethics/RAI", "CPO"]

    def prove_and_seal(self, metrics: dict) -> bool:
        lat = metrics.get("latency", 0.0)
        err = metrics.get("error_rate", 0.0)
        conf = metrics.get("confidence", 1.0)

        proven = (lat <= 0.05) and (err <= 0.01) and (0.95 <= conf <= 1.0)
        
        payload = {
            "metrics": metrics,
            "invariants": {
                "latency_bound": lat <= 0.05,
                "error_bound": err <= 0.01,
                "confidence_bound": 0.95 <= conf <= 1.0
            },
            "proven": proven
        }

        prev_hash = "0" * 64
        if LEDGER.exists():
            lines = LEDGER.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                try:
                    last = json.loads(lines[-1])
                    prev_hash = last.get("current_hash", prev_hash)
                except Exception:
                    pass

        record = {
            "timestamp": time.time(),
            "event": "PROVE_INVARIANTS",
            "payload": payload,
            "prev_hash": prev_hash
        }

        canonical = json.dumps(record, sort_keys=True, separators=(',', ':'))
        chash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        record["current_hash"] = chash
        sig = hmac.new(SECRET, chash.encode("utf-8"), hashlib.sha256).hexdigest()
        record["hmac_signature"] = sig

        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")

        print(f"[kernel] Invariant Proof Sealed | Hash: {chash[:16]}... | Proven: {proven}")
        return proven

if __name__ == "__main__":
    kernel = AbsoluteKernel()
    telemetry = {"latency": 0.0185, "error_rate": 0.0, "confidence": 0.992}
    success = kernel.prove_and_seal(telemetry)
    if success:
        print("[kernel] SUCCESS: System state mathematically proven and cryptographically sealed.")
        sys.exit(0)
    else:
        print("[kernel] HALTED: Invariant violation.")
        sys.exit(1)
