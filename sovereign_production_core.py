#!/usr/bin/env python3
import pathlib
import json
import time
import hashlib
import hmac
import os
import sys

print("[sovereign-core] Initializing Production Sovereign Core & Evidence Ledger...")

WORKSPACE = pathlib.Path("/tmp/ucs-clean/production")
WORKSPACE.mkdir(parents=True, exist_ok=True)
LEDGER_FILE = WORKSPACE / "immutable_evidence.jsonl"
KEY_FILE = WORKSPACE / "hmac_master.key"

if KEY_FILE.exists():
    MASTER_KEY = KEY_FILE.read_bytes()
else:
    MASTER_KEY = os.urandom(32)
    KEY_FILE.write_bytes(MASTER_KEY)

class AbsoluteSovereignEngine:
    def __init__(self):
        self.executive_basis = ["CDO", "CISO", "CRO", "CLO", "Ethics/RAI", "CPO"]

    def append_record(self, event_type: str, payload: dict) -> dict:
        prev_hash = "0" * 64
        if LEDGER_FILE.exists():
            lines = LEDGER_FILE.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                try:
                    last_record = json.loads(lines[-1])
                    prev_hash = last_record.get("current_hash", prev_hash)
                except Exception:
                    pass

        record = {
            "timestamp": time.time(),
            "event_type": event_type,
            "payload": payload,
            "prev_hash": prev_hash
        }

        canonical = json.dumps(record, sort_keys=True, separators=(',', ':'))
        current_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        record["current_hash"] = current_hash

        signature = hmac.new(MASTER_KEY, current_hash.encode("utf-8"), hashlib.sha256).hexdigest()
        record["hmac_signature"] = signature

        with open(LEDGER_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")

        print(f"[WORM-LEDGER] Sealed [{event_type}] | Hash: {current_hash[:16]}... | HMAC: {signature[:16]}...")
        return record

    def verify_chain(self) -> bool:
        if not LEDGER_FILE.exists():
            return True
        lines = LEDGER_FILE.read_text(encoding="utf-8").strip().splitlines()
        expected_prev = "0" * 64

        for idx, line in enumerate(lines):
            rec = json.loads(line)
            h_saved = rec.pop("current_hash")
            sig_saved = rec.pop("hmac_signature")

            if rec.get("prev_hash") != expected_prev:
                print(f"[CRITICAL] Chain broken at index {idx}")
                return False

            canonical = json.dumps(rec, sort_keys=True, separators=(',', ':'))
            h_computed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            sig_computed = hmac.new(MASTER_KEY, h_computed.encode("utf-8"), hashlib.sha256).hexdigest()

            if h_computed != h_saved or not hmac.compare_digest(sig_computed, sig_saved):
                print(f"[CRITICAL] Signature mismatch at index {idx}")
                return False
            expected_prev = h_saved

        print(f"[WORM-LEDGER] Chain Verified: {len(lines)} records cryptographically immutable.")
        return True

    def project_role(self, role_name: str, weights: dict) -> dict:
        print(f"[BASIS-AXIOM] Projecting role '{role_name}' across 6 basis executive nodes...")
        for role in self.executive_basis:
            if role not in weights:
                raise ValueError(f"Mandatory basis role missing weight: {role}")
        return {
            "projected_role": role_name,
            "weights": weights,
            "basis_set": self.executive_basis
        }

    def process_telemetry(self, raw_stream: list) -> dict:
        if not raw_stream:
            return {"latency": 0.0, "error_rate": 0.0, "confidence": 1.0, "samples": 0}

        latencies = [float(x.get("latency", 0.0)) for x in raw_stream]
        errors = [1.0 if x.get("status", 200) != 200 else 0.0 for x in raw_stream]
        confidences = [float(x.get("confidence", 1.0)) for x in raw_stream]

        metrics = {
            "latency": round(sum(latencies) / len(latencies), 6),
            "error_rate": round(sum(errors) / len(errors), 6),
            "confidence": round(sum(confidences) / len(confidences), 6),
            "samples": len(raw_stream)
        }
        print(f"[TELEMETRY] Computed -> Latency: {metrics['latency']}s | Error Rate: {metrics['error_rate']} | Confidence: {metrics['confidence']} | Samples: {metrics['samples']}")
        return metrics

    def evaluate_swarm_consensus(self, metrics: dict) -> dict:
        print("[SWARM] Evaluating decentralized consensus across 6 executive roles...")
        vetoes = []

        if metrics["error_rate"] > 0.08:
            vetoes.append({"role": "CISO", "reason": f"Error rate {metrics['error_rate']} exceeds threshold 0.08"})
        if metrics["confidence"] < 0.90:
            vetoes.append({"role": "Ethics/RAI", "reason": f"Confidence {metrics['confidence']} below threshold 0.90"})
        if metrics["latency"] > 0.100:
            vetoes.append({"role": "CPO", "reason": f"Latency {metrics['latency']}s violates SLA maximum"})

        passed = len(vetoes) == 0
        status = "PASSED ✅" if passed else f"HALTED 🛑 ({len(vetoes)} vetoes)"
        print(f"[SWARM] Result: {status}")
        for v in vetoes:
            print(f"  -> Veto [{v['role']}]: {v['reason']}")

        return {"consensus_passed": passed, "vetoes": vetoes}

if __name__ == "__main__":
    engine = AbsoluteSovereignEngine()

    role_proof = engine.project_role("Chief_Security_Architecture_Officer", {
        "CDO": 0.1, "CISO": 0.4, "CRO": 0.2, "CLO": 0.1, "Ethics/RAI": 0.1, "CPO": 0.1
    })
    engine.append_record("ROLE_PROJECTION", role_proof)

    stream = [
        {"latency": 0.0215, "status": 200, "confidence": 0.992},
        {"latency": 0.0310, "status": 200, "confidence": 0.988},
        {"latency": 0.0195, "status": 200, "confidence": 0.995}
    ]
    metrics = engine.process_telemetry(stream)
    engine.append_record("TELEMETRY_BATCH", metrics)

    consensus = engine.evaluate_swarm_consensus(metrics)
    engine.append_record("SWARM_CONSENSUS", consensus)

    if not consensus["consensus_passed"]:
        print("[SOVEREIGN] Pipeline execution halted by executive veto.")
        sys.exit(1)

    if engine.verify_chain():
        print("[SOVEREIGN] SUCCESS: Production core verified, immutably sealed, and operational.")
        sys.exit(0)
    else:
        print("[SOVEREIGN] FATAL: Immutable chain verification failed.")
        sys.exit(1)
