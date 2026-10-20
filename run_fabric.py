#!/usr/bin/env python3
"""run_fabric.py — single-file localhost fabric for Danny-TMIG/ucs.

Ports default to 8081/8082/8083 but each service auto-picks a free port
if the preferred one is taken. Set AETHER_BASE_PORT to shift the range,
or AETHER_GOVERN_PORT / AETHER_COMPUTE_PORT / AETHER_COGNITION_PORT
to pin individual ports.
"""
import argparse, datetime, http.server, json, os, socket, socketserver, sys, threading, time, urllib.request, uuid

BIND = "127.0.0.1"
_BASE = int(os.environ.get("AETHER_BASE_PORT", 8081))
_PREFERRED = {
    "govern":    int(os.environ.get("AETHER_GOVERN_PORT",    _BASE)),
    "compute":   int(os.environ.get("AETHER_COMPUTE_PORT",   _BASE + 1)),
    "cognition": int(os.environ.get("AETHER_COGNITION_PORT", _BASE + 2)),
}
PORTS = {}


def _free_port(preferred):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((BIND, preferred)); s.listen(1); return preferred
    except OSError:
        s.close()
    for p in range(preferred + 1, preferred + 200):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((BIND, p)); s.listen(1); return p
        except OSError:
            s.close()
    raise RuntimeError(f"no free port near {preferred}")


def envelope(kind, correlation_id, body):
    return {"schema_version": "1.0", "id": str(uuid.uuid4()),
            "correlation_id": correlation_id, "sovereign_domain": "local",
            "purpose": kind, "classification": "internal", "integrity": "unsigned",
            "body": body, "ts": datetime.datetime.now(datetime.timezone.utc).isoformat()}


def _post(port, path, payload, timeout=5):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"http://{BIND}:{port}{path}", data=data,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def govern_authz(req, cid):
    return envelope("authorization-decision", cid, {"decision": "allow", "request_id": req.get("id")})


def govern_exec(req, cid):
    order = envelope("execution-order", cid, {"order": req.get("body", {}), "from": "govern"})
    result = _post(PORTS["compute"], "/execution-order", order)
    return envelope("governed-outcome", cid, {"order_id": order["id"], "compute": result})


def compute_exec(req, cid):
    oid = req.get("id")
    result = envelope("execution-result", cid, {"status": "completed", "order_id": oid})
    evidence = envelope("execution-evidence", cid, {"order_id": oid, "ticket": "local-demo", "revoked": False, "revoked_by": None})
    return {"result": result, "evidence": evidence}


def cognition_evidence(req, cid):
    return envelope("cognitive-state-update-directive", cid, {"note": "cognition stub", "echo": req.get("body")})


ROUTES = {"govern": {"/authorization-request": govern_authz, "/execution-order": govern_exec},
          "compute": {"/execution-order": compute_exec},
          "cognition": {"/evidence": cognition_evidence}}


class BaseHandler(http.server.BaseHTTPRequestHandler):
    routes = {}
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n) if n else b"{}"
        try: req = json.loads(raw or b"{}")
        except json.JSONDecodeError: return self._send(400, {"error": "invalid json"})
        cid = req.get("correlation_id") or str(uuid.uuid4())
        fn = self.routes.get(self.path)
        if not fn: return self._send(404, {"error": "no route", "path": self.path})
        try: self._send(200, fn(req, cid))
        except Exception as e: self._send(500, {"error": str(e)})
    def do_GET(self):
        if self.path == "/health": self._send(200, {"ok": True, "service": self.server.service_name})
        else: self._send(404, {"error": "no route"})
    def _send(self, code, payload):
        out = json.dumps(payload).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)
    def log_message(self, *a): pass


class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def start(name):
    port = _free_port(_PREFERRED[name])
    PORTS[name] = port
    handler = type(f"{name.title()}Handler", (BaseHandler,), {"routes": ROUTES[name]})
    srv = ThreadedServer((BIND, port), handler)
    srv.service_name = name
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _assert(cond, msg):
    if not cond: raise AssertionError(msg)


def smoke():
    fails = []
    def check(name, fn):
        try: fn(); print(f"  PASS  {name}")
        except Exception as e: print(f"  FAIL  {name}: {e}"); fails.append(name)
    print("smoke:")
    for svc, port in PORTS.items():
        check(f"{svc} /health", lambda p=port, s=svc: _assert(
            json.loads(urllib.request.urlopen(f"http://{BIND}:{p}/health", timeout=5).read()).get("service") == s, "bad health"))
    check("govern /authorization-request", lambda: _assert(
        _post(PORTS["govern"], "/authorization-request", {"id": "req-1", "correlation_id": "c-1"}).get("body", {}).get("decision") == "allow", "not allow"))
    def full():
        r = _post(PORTS["govern"], "/execution-order", {"correlation_id": "c-2", "body": {"op": "demo"}})
        _assert(r["purpose"] == "governed-outcome", r)
        inner = r["body"]["compute"]
        _assert(inner["result"]["body"]["status"] == "completed", inner)
        _assert(inner["evidence"]["body"]["ticket"] == "local-demo", inner)
    check("govern -> compute round trip", full)
    check("cognition /evidence", lambda: _assert(
        _post(PORTS["cognition"], "/evidence", {"correlation_id": "c-3", "body": {"note": "x"}})["purpose"] == "cognitive-state-update-directive", "wrong purpose"))
    if fails: print(f"\nFAIL: {len(fails)} check(s) failed"); return False
    print("\nOK: all smoke checks passed"); return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()
    servers = [start(s) for s in _PREFERRED]
    time.sleep(0.3)
    print("fabric listeners:")
    for svc, port in PORTS.items(): print(f"  {svc:9s} http://{BIND}:{port}")
    print()
    ok = smoke()
    if args.test:
        for s in servers: s.shutdown()
        sys.exit(0 if ok else 1)
    print("\nserving — Ctrl-C to stop")
    try:
        while True: time.sleep(3600)
    except KeyboardInterrupt: print("\nstopping")
    finally:
        for s in servers: s.shutdown()


if __name__ == "__main__":
    main()
