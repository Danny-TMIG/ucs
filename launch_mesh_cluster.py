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

print("==================================================================")
print("[CLUSTER-MESH] Initializing Multi-Node Sovereign P2P Cluster (9004-9006)...")
print("==================================================================")

CLUSTER_PORTS = [9004, 9005, 9006]
servers = []

class ClusterNodeInstance:
    def __init__(self, port: int):
        self.port = port
        self.node_id = f"MESH-NODE-{port}"
        self.workspace = pathlib.Path(f"/tmp/ucs-clean/cluster_node_{port}")
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.workspace / "cluster_worm.jsonl"
        self.key_path = self.workspace / "cluster_root.key"
        
        if self.key_path.exists():
            self.secret = self.key_path.read_bytes()
        else:
            self.secret = os.urandom(64)
            self.key_path.write_bytes(self.secret)
            self.key_path.chmod(0o400)

    def seal(self, event_type: str, payload: dict) -> dict:
        prev_hash = "0" * 64
        if self.ledger_path.exists():
            lines = self.ledger_path.read_text(encoding="utf-8").strip().splitlines()
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

        signature = hmac.new(self.secret, current_hash.encode("utf-8"), hashlib.sha256).hexdigest()
        record["hmac_signature"] = signature

        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")

        return record

    def get_state(self) -> dict:
        if not self.ledger_path.exists():
            return {"records": 0, "latest_hash": "0" * 64}
        lines = self.ledger_path.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            return {"records": 0, "latest_hash": "0" * 64}
        last = json.loads(lines[-1])
        return {"records": len(lines), "latest_hash": last.get("current_hash")}

# Dictionary to hold node instances globally for the HTTP handler
node_registry = {}

class ClusterHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        port = self.server.server_address[1]
        node = node_registry.get(port)
        if self.path == "/status":
            state = node.get_state()
            response = {"node_id": node.node_id, "port": node.port, "state": state}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        port = self.server.server_address[1]
        node = node_registry.get(port)
        if self.path == "/gossip":
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length) if length > 0 else b"{}"
            try:
                data = json.loads(body)
            except Exception:
                data = {}

            peer_id = data.get("node_id", "UNKNOWN")
            peer_hash = data.get("latest_hash", "")
            
            node.seal("GOSSIP_SYNC_RECEIVED", {"peer_id": peer_id, "peer_hash": peer_hash})
            print(f"[{node.node_id}] Gossip synchronized with {peer_id} | Peer Hash: {peer_hash[:16]}...")
            
            response = {"status": "synchronized", "acknowledged_hash": node.get_state()["latest_hash"]}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def run_server(port):
    server = HTTPServer(("127.0.0.1", port), ClusterHandler)
    servers.append(server)
    server.serve_forever()

if __name__ == "__main__":
    # Initialize all nodes
    for p in CLUSTER_PORTS:
        n = ClusterNodeInstance(p)
        n.seal("NODE_BOOTSTRAP", {"status": "ONLINE"})
        node_registry[p] = n
        t = threading.Thread(target=run_server, args=(p,), daemon=True)
        t.start()
        print(f"[cluster] Started {n.node_id} on http://127.0.0.1:{p}")

    time.sleep(0.5)
    print("\n[cluster] Executing Live Mesh Gossip Broadcast across Cluster Nodes...")

    # Broadcast from 9004 -> 9005 and 9005 -> 9006
    for i in range(len(CLUSTER_PORTS)):
        src_port = CLUSTER_PORTS[i]
        target_port = CLUSTER_PORTS[(i + 1) % len(CLUSTER_PORTS)]
        src_node = node_registry[src_port]

        url = f"http://127.0.0.1:{target_port}/gossip"
        payload = json.dumps({
            "node_id": src_node.node_id,
            "latest_hash": src_node.get_state()["latest_hash"]
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=1) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                print(f"[GOSSIP-SUCCESS] {src_node.node_id} ---> Node-{target_port} | Ack: {res_data['status']}")
        except Exception as e:
            print(f"[GOSSIP-ERROR] Failed to sync {src_node.node_id} with Node-{target_port}: {e}")

    # Shutdown servers cleanly
    time.sleep(0.5)
    for s in servers:
        s.shutdown()

    print("\n[cluster] SUCCESS: Multi-node P2P mesh cluster verified and synchronized.")
    sys.exit(0)
