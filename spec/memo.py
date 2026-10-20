#!/usr/bin/env python3
"""memo.py — rolling hash + memoization over a file tree.

Tree hash = Merkle root over sorted (path, file_hash) pairs.
Memo caches a function's result against the current root. When the root
changes (any file added/modified/removed), the cache is invalidated.
Excludes .git, build, __pycache__, node_modules, .venv."""
import hashlib, pathlib

SKIP = {".git", "build", "__pycache__", "node_modules", ".venv"}

def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def tree_manifest(root="."):
    root = pathlib.Path(root)
    out = {}
    for p in root.rglob("*"):
        if any(part in SKIP for part in p.parts): continue
        if not p.is_file(): continue
        out[str(p.relative_to(root))] = file_hash(p)
    return out

def tree_root(manifest):
    h = hashlib.sha256()
    for path in sorted(manifest):
        h.update(path.encode()); h.update(b"\0")
        h.update(manifest[path].encode()); h.update(b"\0")
    return h.hexdigest()

class Memo:
    def __init__(self, root="."):
        self.root = pathlib.Path(root)
        self._root_hash = None
        self._cache = {}

    def current_root(self):
        r = tree_root(tree_manifest(self.root))
        if r != self._root_hash:
            self._root_hash = r
            self._cache = {}
        return r

    def call(self, fn, *args, **kwargs):
        root = self.current_root()
        key = (root, fn.__name__, args, tuple(sorted(kwargs.items())))
        if key in self._cache:
            return self._cache[key]
        result = fn(*args, **kwargs)
        self._cache[key] = result
        return result

if __name__ == "__main__":
    import tempfile, os
    tmp = tempfile.mkdtemp()
    os.chdir(tmp)
    pathlib.Path("a.txt").write_text("hello")
    pathlib.Path("b.txt").write_text("world")
    m = tree_manifest(".")
    assert len(m) == 2, m
    r1 = tree_root(m)
    # change one file → root changes
    pathlib.Path("a.txt").write_text("hello!")
    m2 = tree_manifest(".")
    r2 = tree_root(m2)
    assert r1 != r2, (r1, r2)
    # memoization: cache hit while tree unchanged, miss after change
    calls = {"n": 0}
    def fn(): calls["n"] += 1; return "result"
    memo = Memo(root=".")
    assert memo.call(fn) == "result"
    assert memo.call(fn) == "result"
    assert calls["n"] == 1, calls  # second call was cached
    pathlib.Path("c.txt").write_text("new")
    assert memo.call(fn) == "result"
    assert calls["n"] == 2, calls  # cache invalidated because root changed
    # every file counted
    manifest = tree_manifest(".")
    total_files = sum(1 for p in pathlib.Path(".").rglob("*") if p.is_file())
    assert len(manifest) == total_files, (len(manifest), total_files)
    # negative test: excluded dirs not counted
    pathlib.Path(".git").mkdir(); pathlib.Path(".git/x").write_text("y")
    m3 = tree_manifest(".")
    assert ".git/x" not in m3, m3
    # negative test: hashing a nonexistent file raises FileNotFoundError
    try:
        file_hash(pathlib.Path("/nonexistent-does-not-exist-xyz"))
    except FileNotFoundError:
        pass
    else:
        raise SystemExit("file_hash should raise FileNotFoundError on missing file")
    # negative test: Memo on an unwritable root still hashes without a cache file
    try:
        m_empty = Memo(root="/tmp/__memo_negative_nonexistent__")
        m_empty.current_root()  # empty tree — sha256 of nothing
    except Exception as e:
        raise SystemExit(f"Memo on empty root should not raise: {e}")
    print(f"memo OK: {len(manifest)} files hashed, root {r2[:12]}, cache invalidation verified")
