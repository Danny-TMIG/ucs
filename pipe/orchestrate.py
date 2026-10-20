#!/usr/bin/env python3
"""
orchestrate.py -- one job, one table of targets, one output shape.

The orchestrator runs on the machine it is on. It can dispatch a job to:
  local   -- llama.cpp on this machine (AETHER_GGUF)
  cloud   -- HTTP POST to AETHER_CLOUD_URL
  ssh     -- a remote machine via ssh (AETHER_SSH_HOST, AETHER_SSH_MODEL)
  docker  -- a container (docker run)

The target is a table entry. Adding hardware is adding a row. No orchestrator
change required. The output of every target is text; the record stage does not
care which target produced it.
"""
import json, os, pathlib, subprocess, sys, time

TARGETS = {
    "local": {
        "cmd": ["llama-cli", "-m", "{model}", "-p", "{prompt}", "-n", "200", "--no-display-prompt"],
        "needs": ["AETHER_GGUF"],
    },
    "cloud": {
        "cmd": ["curl", "-s", "-X", "POST", "{url}", "-H", "Content-Type: application/json", "-d", "{body}"],
        "needs": ["AETHER_CLOUD_URL"],
    },
    "ssh": {
        "cmd": ["ssh", "{host}", "llama-cli", "-m", "{model}", "-p", "{prompt}", "-n", "200", "--no-display-prompt"],
        "needs": ["AETHER_SSH_HOST", "AETHER_SSH_MODEL"],
    },
    "docker": {
        "cmd": ["docker", "run", "--rm", "ghcr.io/ggerganov/llama.cpp:full",
                "-m", "{model}", "-p", "{prompt}", "-n", "200"],
        "needs": ["AETHER_DOCKER_MODEL"],
    },
}

def available():
    return [name for name, t in TARGETS.items() if all(os.environ.get(k) for k in t["needs"])]

def pick():
    order = ["local", "cloud", "ssh", "docker"]
    avail = available()
    for t in order:
        if t in avail:
            return t
    raise SystemExit(f"no target available: set one of {[k for t in TARGETS.values() for k in t['needs']]}")

def render(target, prompt):
    t = TARGETS[target]
    args = []
    for a in t["cmd"]:
        a = a.replace("{prompt}", prompt)
        a = a.replace("{model}", os.environ.get("AETHER_GGUF") or os.environ.get("AETHER_SSH_MODEL") or os.environ.get("AETHER_DOCKER_MODEL", ""))
        a = a.replace("{url}", os.environ.get("AETHER_CLOUD_URL", ""))
        a = a.replace("{host}", os.environ.get("AETHER_SSH_HOST", ""))
        a = a.replace("{body}", json.dumps({"prompt": prompt}))
        args.append(a)
    return args

def run(target, prompt, timeout=180):
    args = render(target, prompt)
    t0 = time.perf_counter()
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    wall = time.perf_counter() - t0
    return {
        "target": target,
        "exit": r.returncode,
        "wall_s": round(wall, 3),
        "output": r.stdout.strip(),
        "stderr": r.stderr.strip()[:500],
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"usage: orchestrate.py <prompt>")
        print(f"  available targets: {available() or '(none)'}")
        sys.exit(2)
    prompt = " ".join(sys.argv[1:])
    target = pick()
    result = run(target, prompt)
    result["prompt"] = prompt
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["exit"] == 0 else 1)
