#!/usr/bin/env python3
import pathlib
import json
import time
import hashlib
import hmac
import os
import sys
import urllib.request
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

print("[p2p-mesh] Initializing Sovereign P2P Mesh Node & Gossip Sync Engine...")

NODE_PORT = int(os.environ.get("NODE_PORT", 9004))
WORKSPACE = pathlib.Path(f"/tmp/ucs-clean/p2p_node_{NODE_PORT}")
WORKSPACE.mkdir(parents=True, exist_ok=True)
MESH_LEDGER = WORKSPACE / "mesh_worm.jsonl"
KEY_PATH = WORKSPACE / "mesh_root.key"

if KEY_PATH.exists():
    MESH_SECRET = KEY_PATH.read_bytes()
else:
    MESH_SECRET = os.urandom(64)
    KEY_PATH.write_bytes(MESH_SECRET)
    KEY_PATH.chmod(0o400)

class P2PMeshNode:
    def __init__(self, port: int):
        self.port = port
        self.node_id = f"MESH-NODE-{port}"
        self.peers = [9004, 9005, 9006]

    def seal_mesh_record(self, event_type: str, payload: dict) -> dict:
        prev_hash = "0" * 64
        if MESH_LEDGER.exists():
            lines = MESH_LEDGER.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                try:
                    last = json.loads(lines[-1])
                    prev_hash = last.get("current_hash", prev_hash)
                except Exception:
                    pass

        record = {
            "timestamp": time.time(),
            "node_id": self.node_id,
            "port": self.port,
            "event_type": event_type,
            "payload": payload,
            "prev_hash": prev_hash
        }

        canonical = json.dumps(record, sort_keys=True, separators=(',', ':'))
        current_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        record["current_hash"] = current_hash

        signature = hmac.new(MESH_SECRET, current_hash.encode("utf-8"), hashlib.sha256).hexdigest()
        record["hmac_signature"] = signature

        with open(MESH_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")

        print(f"[{self.node_id}] Sealed [{event_type}] | Hash: {current_hash[:16]}...")
        return record

    def get_latest_state(self) -> dict:
        if not MESH_LEDGER.exists():
            return {"records": 0, "latest_hash": "0" * 64}
        lines = MESH_LEDGER.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            return {"records": 0, "latest_hash": "0" * 64}
        last = json.loads(lines[-1])
        return {
            "records": len(lines),
            "latest_hash": last.get("current_hash"),
            "hmac_signature": last.get("hmac_signature")
        }

class MeshHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status":
            state = node.get_latest_state()
            response = {"node_id": node.node_id, "port": node.port, "state": state}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/gossip":
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length) if length > 0 else b"{}"
            try:
                data = json.loads(body)
            except Exception:
                data = {}

            peer_id = data.get("node_id", "UNKNOWN")
            peer_hash = data.get("latest_hash", "")
            print(f"[{node.node_id}] Received gossip sync packet from {peer_id} (Hash: {peer_hash[:16]}...)")

            node.seal_mesh_record("GOSSIP_SYNC_RECEIVED", {"peer_id": peer_id, "peer_hash": peer_hash})
            
            response = {"status": "synchronized", "acknowledged_hash": node.get_latest_state()["latest_hash"]}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    node = P2PMeshNode(NODE_PORT)
    node.seal_mesh_record("NODE_BOOTSTRAP", {"status": "ONLINE"})

    server = HTTPServer(("127.0.0.1", NODE_PORT), MeshHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"[{node.node_id}] P2P Mesh Daemon active on http://127.0.0.1:{NODE_PORT}")

    # Simulate a peer gossip handshake
    time.sleep(0.3)
    target_peer_port = 9005 if NODE_PORT != 9005 else 9004
    url = f"http://127.0.0.1:{target_peer_port}/gossip"
    payload = json.dumps({
        "node_id": node.node_id,
        "latest_hash": node.get_latest_state()["latest_hash"]
    }).encode("utf-8")

    print(f"[{node.node_id}] Attempting gossip broadcast to peer port {target_peer_port}...")
    try:
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=1) as resp:
            print(f"[{node.node_id}] Peer gossip response: {resp.read().decode('utf-8')}")
    except Exception as e:
        print(f"[{node.node_id}] Peer offline or unreached ({e}). Operating in autonomous air-gapped isolation mode.")

    server.shutdown()
    print(f"[{node.node_id}] Mesh test cycle complete. Ledger sealed and saved.")
    sys.exit(0)
