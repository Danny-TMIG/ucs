\
\
\
\
\
\
\
import argparse, json, os, pathlib, subprocess, sys, urllib.request
HF_API = "https://huggingface.co/api/models/{}"
HF_RESOLVE = "https://huggingface.co/{repo}/resolve/main/{filename}"
def list_files(repo):
    url = HF_API.format(repo)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        meta = json.loads(r.read().decode())
    siblings = meta.get("siblings", [])
    return [s["rfilename"] for s in siblings]
def resolve(repo, pattern):
    files = list_files(repo)
    hits = [f for f in files if pattern in f]
    if not hits:
        raise SystemExit(f"no file matching {pattern!r} in {repo}; candidates:\n  " + "\n  ".join(files[:20]))
    hits = [h for h in hits if h.endswith(".gguf")] or hits
    return hits[0]
def download(repo, filename, dest):
    url = HF_RESOLVE.format(repo=repo, filename=filename)
    dest = pathlib.Path(dest) / pathlib.Path(filename).name
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"-> {url}\n-> {dest}")
    r = subprocess.run(["curl", "-L", "--fail", "--progress-bar", "-o", str(dest), url],
                       timeout=3600)
    if r.returncode != 0:
        raise SystemExit(f"curl exited {r.returncode}")
    return dest
def verify(path):
    p = pathlib.Path(path)
    size = p.stat().st_size
    if size < 1024:
        raise SystemExit(f"{p} is {size} bytes — probably an error page, not a model")
    with p.open("rb") as f:
        magic = f.read(4)
    if magic != b"GGUF":
        raise SystemExit(f"{p} magic {magic!r} != b'GGUF' — not a GGUF file")
    print(f"OK: {p} ({size:,} bytes, magic=GGUF)")
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", help="e.g. Qwen/Qwen2.5-14B-Instruct-GGUF")
    ap.add_argument("pattern", help="substring of filename, e.g. q4_k_m or Q4_K_M")
    ap.add_argument("--dest", default=os.path.expanduser("~/models"))
    a = ap.parse_args()
    filename = resolve(a.repo, a.pattern)
    print(f"resolved: {filename}")
    path = download(a.repo, filename, a.dest)
    verify(path)
if __name__ == "__main__":
    import tempfile
    with tempfile.NamedTemporaryFile("wb", suffix=".gguf", delete=False) as f:
        f.write(b"Entry not found" + b"\x00" * 2000)
        bad = f.name
    try:
        verify(bad)
    except SystemExit:
        pass
    else:
        raise SystemExit("verify() should reject non-GGUF file")
    finally:
        pathlib.Path(bad).unlink()
    main()
