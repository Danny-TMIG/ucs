#!/usr/bin/env python3
import shutil, subprocess, sys, pathlib, os
LLAMA = shutil.which("llama-cli") or shutil.which("llama")
DEFAULT_MODEL = os.environ.get("AETHER_GGUF", "")
def available():
    return LLAMA is not None and bool(DEFAULT_MODEL) and pathlib.Path(DEFAULT_MODEL).exists()
def generate(prompt, n=20, timeout=60):
    if not available():
        raise RuntimeError(f"llama.cpp not available (llama-cli={LLAMA!r}, model={DEFAULT_MODEL!r})")
    r = subprocess.run([LLAMA, "-m", DEFAULT_MODEL, "-p", prompt, "-n", str(n), "--no-display-prompt"],
                       capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0: raise RuntimeError(r.stderr[:500])
    return r.stdout.strip()
if __name__=="__main__":
    if not available():
        print("serve: model absent (ok). To enable: brew install llama.cpp; export AETHER_GGUF=path/to/model.gguf")
        sys.exit(0)
    out = generate("The capital of France is", n=10)
    assert out, "empty generation"
    print(f"serve OK: {out[:80]!r}")
