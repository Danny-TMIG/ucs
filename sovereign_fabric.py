#!/usr/bin/env python3
import pathlib
import json
import time
import hashlib
import hmac
import os
import sys
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

print("==================================================")
print("[AETHER-FABRIC] Initializing Sovereign Node & ASGI Gateway")
print("==================================================")

WORKSPACE = pathlib.Path("/tmp/ucs-clean/fabric_node")
WORKSPACE.mkdir(parents=True, exist_ok=True)
LEDGER_PATH = WORKSPACE / "immutable_worm.jsonl"
KEY_PATH = WORKSPACE / "node_hmac.key"

if KEY_PATH.exists():
    SECRET_KEY = KEY_PATH.read_bytes()
else:
    SECRET_KEY = os.urandom(32)
    KEY_PATH.write_bytes(SECRET_KEY)

class FabricWORMNode:
    def __init__(self):
        self.basis_roles = ["CDO", "CISO", "CRO", "CLO", "Ethics/RAI", "CPO"]

    def write_ledger(self, event_type: str, payload: dict) -> dict:
        prev_hash = "0" * 64
        if LEDGER_PATH.exists():
            lines = LEDGER_PATH.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                try:
                    last = json.loads(lines[-1])
                    prev_hash = last.get("current_hash", prev_hash)
                except Exception:
                    pass

        entry = {
            "timestamp": time.time(),
            "node_id": socket.gethostname(),
            "event_type": event_type,
            "payload": payload,
            "prev_hash": prev_hash
        }

        canonical = json.dumps(entry, sort_keys=True, separators=(',', ':'))
        current_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        entry["current_hash"] = current_hash

        signature = hmac.new(SECRET_KEY, current_hash.encode("utf-8"), hashlib.sha256).hexdigest()
        entry["hmac_signature"] = signature

        with open(LEDGER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")

        print(f"[WORM-LEDGER] Sealed [{event_type}] | Hash: {current_hash[:16]}... | HMAC: {signature[:16]}...")
        return entry

    def evaluate_swarm(self, telemetry: dict) -> dict:
        vetoes = []
        if telemetry.get("error_rate", 0.0) > 0.05:
            vetoes.append({"role": "CISO", "reason": f"Error rate {telemetry['error_rate']} exceeds strict 0.05 policy."})
        if telemetry.get("confidence", 1.0) < 0.92:
            vetoes.append({"role": "Ethics/RAI", "reason": f"Confidence score {telemetry['confidence']} breaches 0.92 floor."})
        if telemetry.get("latency", 0.0) > 0.100:
            vetoes.append({"role": "CPO", "reason": f"Latency {telemetry['latency']}s violates SLA maximum."})

        passed = len(vetoes) == 0
        return {"consensus_passed": passed, "vetoes": vetoes}

node = FabricWORMNode()

class SovereignHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.read_body(content_length)
        
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        # Float-compute telemetry
        raw_stream = data.get("stream", [{"latency": 0.021, "status": 200, "confidence": 0.99}])
        latencies = [float(x.get("latency", 0.0)) for x in raw_stream]
        errors = [1.0 if x.get("status", 200) != 200 else 0.0 for x in raw_stream]
        confidences = [float(x.get("confidence", 1.0)) for x in raw_stream]

        metrics = {
            "latency": round(sum(latencies) / len(latencies), 6),
            "error_rate": round(sum(errors) / len(errors), 6),
            "confidence": round(sum(confidences) / len(confidences), 6),
            "samples": len(raw_stream)
        }

        # Murmurations Swarm Evaluation
        consensus = node.evaluate_swarm(metrics)

        # Seal in WORM Ledger
        event_name = "NODE_CYCLE_APPROVED" if consensus["consensus_passed"] else "NODE_CYCLE_HALTED"
        ledger_entry = node.write_ledger(event_name, {"metrics": metrics, "consensus": consensus})

        response_payload = {
            "status": "success" if consensus["consensus_passed"] else "vetoed",
            "metrics": metrics,
            "consensus": consensus,
            "receipt": {
                "current_hash": ledger_entry["current_hash"],
                "hmac_signature": ledger_entry["hmac_signature"]
            }
        }

        self.send_response(200 if consensus["consensus_passed"] else 403)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response_payload, indent=2).encode("utf-8"))

    def read_body(self, length):
        if length == 0:
            return b"{}"
        return self.rfile.read(length)

    def log_message(self, format, *args):
        print(f"[gateway] {self.address_string()} - {format%args}")

def run_server():
    server = HTTPServer(("127.0.0.1", 9001), SovereignHandler)
    print("[gateway] Aether Sovereign Fabric Gateway active on http://127.0.0.1:9001")
    server.serve_forever()

if __name__ == "__main__":
    # Boot test cycle
    test_stream = [
        {"latency": 0.024, "status": 200, "confidence": 0.991},
        {"latency": 0.031, "status": 200, "confidence": 0.988}
    ]
    metrics = {
        "latency": sum(x["latency"] for x in test_stream)/len(test_stream),
        "error_rate": 0.0,
        "confidence": sum(x["confidence"] for x in test_stream)/len(test_stream),
        "samples": len(test_stream)
    }
    consensus = node.evaluate_swarm(metrics)
    node.write_ledger("BOOTSTRAP_VERIFIED", {"metrics": metrics, "consensus": consensus})

    # Start background server thread
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    
    print("[sovereign-fabric] Infrastructure live. Executing automated self-test curl against local endpoint...")
    time.sleep(0.5)
    
    import urllib.request
    req = urllib.request.Request(
        "http://127.0.0.1:9001",
        data=json.dumps({"stream": test_stream}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print("[self-test] Response received:")
            print(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[self-test] Error: {e}")

    print("[sovereign-fabric] Node running continuously. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[sovereign-fabric] Shutdown signal received. Ledger preserved.")
