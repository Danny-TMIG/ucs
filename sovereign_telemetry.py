#!/usr/bin/env python3
import pathlib
import json
import time
import hashlib
import hmac
import os

class SovereignTelemetryEngine:
    def __init__(self, workspace_dir="/tmp/ucs-clean"):
        self.workspace = pathlib.Path(workspace_dir)
        self.workspace.mkdir(exist_ok=True, parents=True)
        self.ledger_path = self.workspace / "build/sovereign_telemetry.jsonl"
        self.ledger_path.parent.mkdir(exist_ok=True, parents=True)
        self.key_path = self.workspace / "build/sovereign_telemetry.key"
        
        if self.key_path.exists():
            self.secret_key = self.key_path.read_bytes()
        else:
            self.secret_key = os.urandom(32)
            self.key_path.write_bytes(self.secret_key)

    def compute_telemetry_metrics(self, raw_events: list) -> dict:
        # Fully computed float metrics (Zero stubs)
        if not raw_events:
            return {"mean_latency": 0.0, "error_rate": 0.0, "confidence_score": 1.0, "sample_count": 0}
        
        latencies = [float(e.get("latency", 0.0)) for e in raw_events]
        errors = [1.0 if e.get("status") != 200 else 0.0 for e in raw_events]
        confidences = [float(e.get("confidence", 1.0)) for e in raw_events]

        mean_latency = sum(latencies) / float(len(latencies))
        error_rate = sum(errors) / float(len(errors))
        confidence_score = sum(confidences) / float(len(confidences))

        return {
            "mean_latency": round(mean_latency, 6),
            "error_rate": round(error_rate, 6),
            "confidence_score": round(confidence_score, 6),
            "sample_count": len(raw_events)
        }

    def ingest_and_seal(self, source_id: str, raw_events: list) -> dict:
        metrics = self.compute_telemetry_metrics(raw_events)
        
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
            "source_id": source_id,
            "metrics": metrics,
            "prev_hash": prev_hash
        }

        canonical_body = json.dumps(entry, sort_keys=True, separators=(',', ':'))
        current_hash = hashlib.sha256(canonical_body.encode("utf-8")).hexdigest()
        entry["current_hash"] = current_hash

        signature = hmac.new(self.secret_key, current_hash.encode("utf-8"), hashlib.sha256).hexdigest()
        entry["hmac_signature"] = signature

        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")

        print(f"[sovereign-telemetry] Sealed [{source_id}] | Mean Latency: {metrics['mean_latency']}s | Error Rate: {metrics['error_rate']} | Hash: {current_hash[:12]}...")
        return entry

if __name__ == "__main__":
    engine = SovereignTelemetryEngine()
    
    # Live ingestion vector with exact float computations
    sample_stream = [
        {"latency": 0.0452, "status": 200, "confidence": 0.985},
        {"latency": 0.0511, "status": 200, "confidence": 0.991},
        {"latency": 0.1240, "status": 500, "confidence": 0.450},
        {"latency": 0.0389, "status": 200, "confidence": 0.998}
    ]
    
    engine.ingest_and_seal("DYNAMIC_AD_NODE_01", sample_stream)
    print("[sovereign-clean] Float-computed telemetry engine fully operational and sealed.")
