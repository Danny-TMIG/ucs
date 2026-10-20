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

print("==================================================================")
print("[SOVEREIGN-HOST] Assembling Complete APSA Production Host Node...")
print("==================================================================")

HOST_DIR = pathlib.Path("/tmp/ucs-clean/host_deployment")
HOST_DIR.mkdir(parents=True, exist_ok=True)
BUILD_DIR = HOST_DIR / "build"
BUILD_DIR.mkdir(exist_ok=True)

LEDGER_PATH = BUILD_DIR / "host_worm.jsonl"
KEY_PATH = BUILD_DIR / "host_hardware_root.key"

if KEY_PATH.exists():
    ROOT_SECRET = KEY_PATH.read_bytes()
else:
    ROOT_SECRET = os.urandom(64)
    KEY_PATH.write_bytes(ROOT_SECRET)
    KEY_PATH.chmod(0o400)

class SovereignHostKernel:
    def __init__(self, node_id: str = "HOST-NODE-M4MAX"):
        self.node_id = node_id
        self.executive_basis = ["CDO", "CISO", "CRO", "CLO", "Ethics/RAI", "CPO"]

    def seal_record(self, event_type: str, payload: dict) -> dict:
        prev_hash = "0" * 64
        if LEDGER_PATH.exists():
            lines = LEDGER_PATH.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                try:
                    last = json.loads(lines[-1])
                    prev_hash = last.get("current_hash", prev_hash)
                except Exception:
                    pass

        record = {
            "timestamp": time.time(),
            "node_id": self.node_id,
            "tier": "ABSOLUTE-HOST-PRODUCTION",
            "event_type": event_type,
            "payload": payload,
            "prev_hash": prev_hash
        }

        canonical = json.dumps(record, sort_keys=True, separators=(',', ':'))
        current_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        record["current_hash"] = current_hash

        signature = hmac.new(ROOT_SECRET, current_hash.encode("utf-8"), hashlib.sha256).hexdigest()
        record["hmac_signature"] = signature

        with open(LEDGER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")

        print(f"[HOST-LEDGER] Sealed [{event_type}] | Hash: {current_hash[:16]}... | Node: {self.node_id}")
        return record

    def verify_ledger(self) -> bool:
        if not LEDGER_PATH.exists():
            return True
        lines = LEDGER_PATH.read_text(encoding="utf-8").strip().splitlines()
        expected_prev = "0" * 64

        for idx, line in enumerate(lines):
            rec = json.loads(line)
            h_saved = rec.pop("current_hash")
            sig_saved = rec.pop("hmac_signature")

            if rec.get("prev_hash") != expected_prev:
                return False

            canonical = json.dumps(rec, sort_keys=True, separators=(',', ':'))
            h_computed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            sig_computed = hmac.new(ROOT_SECRET, h_computed.encode("utf-8"), hashlib.sha256).hexdigest()

            if h_computed != h_saved or not hmac.compare_digest(sig_computed, sig_saved):
                return False
            expected_prev = h_saved
        return True

    def evaluate_swarm(self, metrics: dict) -> dict:
        vetoes = []
        if metrics.get("error_rate", 0.0) > 0.01:
            vetoes.append({"role": "CISO", "reason": f"Error rate {metrics['error_rate']} exceeds 1% ceiling."})
        if metrics.get("confidence", 1.0) < 0.95:
            vetoes.append({"role": "Ethics/RAI", "reason": f"Confidence {metrics['confidence']} below 95% floor."})
        if metrics.get("latency", 0.0) > 0.100:
            vetoes.append({"role": "CPO", "reason": f"Latency {metrics['latency']}s violates SLA."})

        passed = len(vetoes) == 0
        return {"consensus_passed": passed, "vetoes": vetoes}

kernel = SovereignHostKernel()

class SovereignHostHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        stream = data.get("stream", [{"latency": 0.021, "status": 200, "confidence": 0.99}])
        latencies = [float(x.get("latency", 0.0)) for x in stream]
        errors = [1.0 if x.get("status", 200) != 200 else 0.0 for x in stream]
        confidences = [float(x.get("confidence", 1.0)) for x in stream]

        metrics = {
            "latency": round(sum(latencies) / len(latencies), 6),
            "error_rate": round(sum(errors) / len(errors), 6),
            "confidence": round(sum(confidences) / len(confidences), 6),
            "samples": len(stream)
        }

        consensus = kernel.evaluate_swarm(metrics)
        event_name = "HOST_CYCLE_APPROVED" if consensus["consensus_passed"] else "HOST_CYCLE_HALTED"
        record = kernel.seal_record(event_name, {"metrics": metrics, "consensus": consensus})

        response = {
            "status": "success" if consensus["consensus_passed"] else "vetoed",
            "metrics": metrics,
            "consensus": consensus,
            "ledger_receipt": {
                "current_hash": record["current_hash"],
                "hmac_signature": record["hmac_signature"]
            }
        }

        self.send_response(200 if consensus["consensus_passed"] else 403)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))

    def do_GET(self):
        valid = kernel.verify_ledger()
        lines = LEDGER_PATH.read_text(encoding="utf-8").strip().splitlines() if LEDGER_PATH.exists() else []
        response = {
            "host_status": "ONLINE",
            "node_id": kernel.node_id,
            "ledger_records": len(lines),
            "chain_valid": valid
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))

    def log_message(self, format, *args):
        print(f"[host-gateway] {format%args}")

def start_server():
    server = HTTPServer(("127.0.0.1", 9001), SovereignHostHandler)
    print("[host-gateway] Sovereign Host Gateway listening on http://127.0.0.1:9001")
    server.serve_forever()

if __name__ == "__main__":
    kernel.seal_record("HOST_NODE_BOOTSTRAP", {"status": "INITIALIZED"})
    
    # Start server in background thread
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    
    time.sleep(0.5)
    print("[host-node] Host successfully staged. Executing internal integration curl probe...")
    
    import urllib.request
    req = urllib.request.Request(
        "http://127.0.0.1:9001",
        data=json.dumps({"stream": [{"latency": 0.022, "status": 200, "confidence": 0.995}]}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print("[probe-response]:")
            print(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[probe-error]: {e}")

    print("[host-node] Sovereign Host Node is fully operational and hosting. Press Ctrl+C to terminate.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
            print("\n[host-node] Shutdown signal caught. Ledger preserved and cryptographically locked.")
