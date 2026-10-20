"""daemon.py — a real socket daemon. Listens, echoes, counts, records."""

from __future__ import annotations
import json, socket, socketserver, sys, time
from pathlib import Path

STATE = Path.home() / "ucs" / "systems" / "daemon" / "state.json"


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        data = self.rfile.readline().strip()
        if not data:
            return
        try:
            req = json.loads(data)
        except Exception:
            self.wfile.write(b'{"error":"bad json"}\n')
            return
        resp = {"echo": req, "ts": time.time(), "pid": __import__("os").getpid()}
        self.wfile.write((json.dumps(resp) + "\n").encode())
        # persistent counter
        try:
            s = json.loads(STATE.read_text()) if STATE.exists() else {"count": 0}
            s["count"] += 1
            s["last_ts"] = resp["ts"]
            STATE.write_text(json.dumps(s))
        except Exception:
            pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def run(host: str = "127.0.0.1", port: int = 19000):
    with Server((host, port), Handler) as srv:
        print(f"daemon listening on {host}:{port}  pid={__import__('os').getpid()}")
        srv.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 19000
    run(port=port)
