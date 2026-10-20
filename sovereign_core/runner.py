#!/usr/bin/env python3
import sys
from ledger import SovereignLedger
from swarm import MurmurationsEngine
from telemetry import FloatTelemetryEngine

def run_pipeline():
    print("[sovereign-core] Initializing Sovereign Pipeline Execution...")
    ledger = SovereignLedger()
    swarm = MurmurationsEngine()
    
    # 1. Test arbitrary role projection via Basis Axiom
    cai_o = swarm.project_role("Chief_AI_Officer", {"CDO": 0.2, "CISO": 0.2, "CRO": 0.1, "CLO": 0.1, "Ethics/RAI": 0.3, "CPO": 0.1})
    ledger.append("ROLE_PROJECTED", cai_o)
    print(f"  [projection] Projected role [{cai_o['projected_role']}] across 6 basis nodes.")

    # 2. Test live float telemetry ingestion
    stream = [
        {"latency": 0.0412, "status": 200, "confidence": 0.989},
        {"latency": 0.0385, "status": 200, "confidence": 0.992},
        {"latency": 0.1420, "status": 500, "confidence": 0.810}
    ]
    metrics = FloatTelemetryEngine.compute(stream)
    ledger.append("TELEMETRY_COMPUTED", metrics)
    print(f"  [telemetry] Computed -> Latency: {metrics['mean_latency']}s | Error Rate: {metrics['error_rate']} | Confidence: {metrics['confidence_score']}")

    # 3. Swarm Consensus Evaluation
    consensus = swarm.evaluate(metrics)
    ledger.append("SWARM_CONSENSUS", consensus)
    
    if not consensus["consensus_passed"]:
        print(f"  [swarm] HALTED by executive vetoes: {consensus['vetoes']}")
    else:
        print("  [swarm] PASSED consensus.")

    # 4. Cryptographic Ledger Integrity Verification
    if ledger.verify():
        print("[sovereign-core] SUCCESS: WORM cryptographic verification PASSED. Architecture fully operational.")
        sys.exit(0)
    else:
        print("[sovereign-core] ERROR: WORM ledger integrity check FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()
