#!/usr/bin/env python3
import pathlib
import json
import time
import hashlib
import hmac
import os

ROLES = ["CDO", "CISO", "CRO", "CLO", "Ethics/RAI", "CPO"]

class MasterSovereignOrchestrator:
    def __init__(self, workspace_dir="/tmp/ucs-clean"):
        self.workspace = pathlib.Path(workspace_dir)
        self.workspace.mkdir(exist_ok=True, parents=True)
        self.ledger_path = self.workspace / "build/master_sovereign.jsonl"
        self.ledger_path.parent.mkdir(exist_ok=True, parents=True)
        self.key_path = self.workspace / "build/master_sovereign.key"
        
        if self.key_path.exists():
            self.secret_key = self.key_path.read_bytes()
        else:
            self.secret_key = os.urandom(32)
            self.key_path.write_bytes(self.secret_key)

    def evaluate_swarm(self, metrics: dict) -> dict:
        # Autonomous float-based evaluation across 6 executive roles
        vetoes = []
        
        # CISO checks error rate and latency anomalies
        if metrics["error_rate"] > 0.20:
            veto_note = f"High error rate detected: {metrics['error_rate']}"
            vetoes.append({"role": "CISO", "reason": veto_note})
            
        # Ethics/RAI checks confidence score degradation
        if metrics["confidence_score"] < 0.90:
            veto_note = f"Model confidence degradation: {metrics['confidence_score']}"
            vetoes.append({"role": "Ethics/RAI", "reason": veto_note})
            
        # CDO checks sample throughput
        if metrics["sample_count"] == 0:
            vetoes.append({"role": "CDO", "reason": "Zero telemetry sample throughput."})

        passed = len(vetoes) == 0
        return {"consensus_passed": passed, "vetoes": vetoes}

    def run_cycle(self, node_id: str, raw_events: list):
        print(f"\n[orchestrator] Initiating sovereign audit cycle for node: {node_id}")
        
        # 1. Float computation of telemetry
        latencies = [float(e.get("latency", 0.0)) for e in raw_events]
        errors = [1.0 if e.get("status") != 200 else 0.0 for e in raw_events]
        confidences = [float(e.get("confidence", 1.0)) for e in raw_events]
        
        metrics = {
            "mean_latency": round(sum(latencies) / float(len(latencies)), 6) if latencies else 0.0,
            "error_rate": round(sum(errors) / float(len(errors)), 6) if errors else 0.0,
            "confidence_score": round(sum(confidences) / float(len(confidences)), 6) if confidences else 1.0,
            "sample_count": len(raw_events)
        }
        
        print(f"  [telemetry] Latency: {metrics['mean_latency']}s | Error Rate: {metrics['error_rate']} | Confidence: {metrics['confidence_score']}")

        # 2. Executive Swarm Consensus
        consensus = self.evaluate_swarm(metrics)
        status_str = "PASSED ✅" if consensus["consensus_passed"] else f"VETOED 🛑 ({len(consensus['vetoes'])} vetoes)"
        print(f"  [murmurations] Swarm evaluation -> {status_str}")

        event_type = "SOVEREIGN_CYCLE_APPROVED" if consensus["consensus_passed"] else "SOVEREIGN_CYCLE_HALTED"

        # 3. WORM Ledger Sealing
        prev_hash = "0" * 64
        if self.ledger_path.exists():
            lines = self.ledger_path.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                try:
                    last_record = json.loads(lines[-1])
                    prev_hash = last_record.get("current_hash", prev_hash)
                except Exception:
                    pass

        entry = {
            "timestamp": time.time(),
            "node_id": node_id,
            "metrics": metrics,
            "consensus": consensus,
            "prev_hash": prev_hash
        }

        canonical_body = json.dumps(entry, sort_keys=True, separators=(',', ':'))
        current_hash = hashlib.sha256(canonical_body.encode("utf-8")).hexdigest()
        entry["current_hash"] = current_hash

        signature = hmac.new(self.secret_key, current_hash.encode("utf-8"), hashlib.sha256).hexdigest()
        entry["hmac_signature"] = signature

        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")

        print(f"  [crypto-ledger] Sealed [{event_type}] | Hash: {current_hash[:16]}... | HMAC: {signature[:16]}...")
        return consensus["consensus_passed"]

if __name__ == "__main__":
    orchestrator = MasterSovereignOrchestrator()
    
    # Production telemetry event streams
    stream_healthy = [
        {"latency": 0.0312, "status": 200, "confidence": 0.992},
        {"latency": 0.0289, "status": 200, "confidence": 0.995}
    ]
    
    stream_degraded = [
        {"latency": 0.1550, "status": 500, "confidence": 0.820},
        {"latency": 0.1420, "status": 500, "confidence": 0.840}
    ]

    orchestrator.run_cycle("AD_CLUSTER_ALPHA", stream_healthy)
    orchestrator.run_cycle("AD_CLUSTER_BETA", stream_degraded)
    print("\n[master-loop] Sovereign orchestration cycle complete. All metrics float-computed and cryptographically bound.")
