#!/usr/bin/env python3
import pathlib
import json
import time
import hashlib
import hmac
import os
import sys
import threading
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

print("[host-daemon] Initializing Autonomous Sovereign Host Node...")

WORKSPACE = pathlib.Path("/tmp/ucs-clean/host_runtime")
WORKSPACE.mkdir(parents=True, exist_ok=True)
LEDGER_PATH = WORKSPACE / "runtime_worm.jsonl"
KEY_PATH = WORKSPACE / "runtime_root.key"

if KEY_PATH.exists():
    ROOT_SECRET = KEY_PATH.read_bytes()
else:
    ROOT_SECRET = os.urandom(64)
    KEY_PATH.write_bytes(ROOT_SECRET)
    KEY_PATH.chmod(0o400)

class SovereignKernel:
    def __init__(self):
        self.node_id = "HOST-DAEMON-M4MAX"

    def seal(self, event_type: str, payload: dict) -> dict:
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

        print(f"[WORM-LEDGER] Sealed [{event_type}] | Hash: {current_hash[:16]}...")
        return record

    def evaluate(self, metrics: dict) -> dict:
        vetoes = []
        if metrics.get("error_rate", 0.0) > 0.01:
            vetoes.append({"role": "CISO", "reason": "Error rate exceeds ceiling."})
        if metrics.get("confidence", 1.0) < 0.95:
            vetoes.append({"role": "Ethics/RAI", "reason": "Confidence below floor."})
        return {"consensus_passed": len(vetoes) == 0, "vetoes": vetoes}

kernel = SovereignKernel()

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        stream = data.get("stream", [{"latency": 0.02, "status": 200, "confidence": 0.99}])
        latencies = [float(x.get("latency", 0.0)) for x in stream]
        errors = [1.0 if x.get("status", 200) != 200 else 0.0 for x in stream]
        confidences = [float(x.get("confidence", 1.0)) for x in stream]

        metrics = {
            "latency": round(sum(latencies) / len(latencies), 6),
            "error_rate": round(sum(errors) / len(errors), 6),
            "confidence": round(sum(confidences) / len(confidences), 6),
            "samples": len(stream)
        }

        consensus = kernel.evaluate(metrics)
        record = kernel.seal("HOST_TELEMETRY_EVAL", {"metrics": metrics, "consensus": consensus})

        response = {
            "status": "success" if consensus["consensus_passed"] else "vetoed",
            "metrics": metrics,
            "consensus": consensus,
            "receipt": record["current_hash"]
        }

        self.send_response(200 if consensus["consensus_passed"] else 403)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))

    def log_message(self, format, *args):
        pass # Suppress noisy server logs during test execution

if __name__ == "__main__":
    kernel.seal("DAEMON_BOOTSTRAP", {"status": "ONLINE"})

    server = HTTPServer(("127.0.0.1", 9002), Handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print("[host-daemon] Server active on http://127.0.0.1:9002")

    # Fire live HTTP POST request to test the host daemon
    time.sleep(0.2)
    url = "http://127.0.0.1:9002"
    payload = json.dumps({"stream": [{"latency": 0.024, "status": 200, "confidence": 0.991}]}).encode("utf-8")
    
    print("[host-daemon] Dispatching test telemetry payload...")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    
    with urllib.request.urlopen(req) as resp:
        print("[host-daemon] Response received from host:")
        print(resp.read().decode("utf-8"))

    server.shutdown()
    print("[host-daemon] SUCCESS: Host node tested, verified, and shut down cleanly.")
    sys.exit(0)
