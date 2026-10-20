import ast, gzip, importlib.util, json, pathlib, subprocess, tarfile, zipfile

yaml = __import__("yaml") if importlib.util.find_spec("yaml") else None
tomllib = __import__("tomllib") if importlib.util.find_spec("tomllib") else None

STATE_DIRS = {".git", "build", "logs", "tmp", ".cache", "dist", "target",
              "node_modules", ".venv", "htmlcov", "__pycache__",
              ".mypy_cache", ".pytest_cache", ".backup-comments"}

SPEC_DIRS = {"spec", "bench", "ci", "hats", "auth", "enterprise",
             "tools", "specs", "standards"}

LOCK_NAMES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml",
              "Cargo.lock", "poetry.lock", "Pipfile.lock",
              "composer.lock", "go.sum", "Gemfile.lock"}

CONTAINER_EXTS = {".zip", ".gz", ".tar", ".tgz", ".bz2", ".xz", ".7z",
                  ".rar", ".jar", ".war", ".gguf"}

BINARY_EXTS = {".pyc", ".pyo", ".pyd", ".so", ".dylib", ".dll", ".a",
               ".o", ".obj", ".class", ".wasm", ".exe",
               ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp",
               ".ico", ".tiff", ".tif", ".svgz",
               ".mp3", ".wav", ".ogg", ".flac", ".m4a",
               ".mp4", ".mov", ".avi", ".webm",
               ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
               ".bin", ".dat", ".db", ".sqlite", ".sqlite3",
               ".swp", ".swo", ".tmp", ".bak", ".orig", ".rej", ".pid"}

MAGIC_BIN = (b"\x89PNG", b"\xff\xd8\xff", b"%PDF", b"PK\x03\x04",
             b"\x1f\x8b", b"GGUF", b"\x7fELF", b"\xca\xfe\xba\xbe")

SPECIFIC = {}

def specific(*exts):
    def deco(fn):
        for e in exts: SPECIFIC[e] = fn
        return fn
    return deco

@specific(".py", ".pyi")
def parse_python(path):
    ast.parse(path.read_text()); return True, "", {}

@specific(".sh", ".bash", ".zsh")
def parse_shell(path):
    r = subprocess.run(["bash","-n",str(path)], capture_output=True, text=True, timeout=10)
    return (True,"",{}) if r.returncode == 0 else (False, r.stderr.strip()[:200], {})

@specific(".json", ".jsonl", ".ndjson")
def parse_json(path):
    json.loads(path.read_text()); return True, "", {}

@specific(".yaml", ".yml")
def parse_yaml(path):
    if yaml is None: return True, "skipped", {}
    try: yaml.safe_load(path.read_text()); return True, "", {}
    except Exception as e: return False, str(e), {}

@specific(".toml")
def parse_toml(path):
    if tomllib is None: return True, "skipped", {}
    try: tomllib.loads(path.read_text()); return True, "", {}
    except Exception as e: return False, str(e), {}

@specific(".md", ".markdown")
def parse_markdown(path):
    depth = 0
    for ln in path.read_text().splitlines():
        if ln.startswith("```"): depth = 1 - depth
    return (True,"",{}) if not depth else (False, "unclosed fence", {})


def parse_text(path):
    path.read_text(encoding="utf-8"); return True, "", {}

def parse_binary(path):
    return True, "", {"bytes": path.stat().st_size}

def parse_container(path, ext):
    try:
        if ext == ".zip" or ext in {".jar", ".war"}:
            with zipfile.ZipFile(path) as z: z.testzip()
        elif ext in {".gz", ".tgz"}:
            with gzip.open(path, "rb") as g: g.read(1)
        elif ext == ".tar":
            with tarfile.open(path) as t: t.getmembers()
        elif ext == ".gguf":
            with open(path, "rb") as f:
                if f.read(4) != b"GGUF": return False, "bad gguf magic", {}
        else:
            return parse_binary(path)
        return True, "", {}
    except Exception as e:
        return False, f"container: {e}", {}


def class_of(path, root):
    try: parts = path.relative_to(root).parts
    except ValueError: parts = path.parts
    if not parts: return "state"
    if parts[0] in STATE_DIRS: return "state"
    ext = path.suffix.lower()
    if ext in BINARY_EXTS: return "binary"
    if ext in CONTAINER_EXTS: return "container"
    if path.name in LOCK_NAMES: return "config"
    if path.name.startswith("."): return "config"
    if ext in {".lock", ".cfg", ".ini", ".conf"}: return "config"
    try:
        with open(path, "rb") as f: head = f.read(8)
        for sig in MAGIC_BIN:
            if head.startswith(sig): return "binary"
    except OSError:
        pass
    return "text"


def describe(path, root):
    try: rel = str(path.relative_to(root))
    except ValueError: rel = str(path)
    if not path.exists():
        return {"path": rel, "class": "missing", "verdict": "failed",
                "reason": "file missing", "size": 0}
    size = path.stat().st_size
    cls = class_of(path, root)
    ext = path.suffix.lower()
    if cls == "state":
        return {"path": rel, "class": "state", "verdict": "skipped",
                "reason": "state dir", "size": size}
    if cls == "binary":
        return {"path": rel, "class": "binary", "verdict": "parsed",
                "reason": "binary", "size": size}
    if cls == "container":
        ok, reason, facts = parse_container(path, ext)
        return {"path": rel, "class": "container",
                "verdict": "parsed" if ok else "failed",
                "reason": reason, "size": size, "facts": facts}
    # text, dispatch on extension
    parser = SPECIFIC.get(ext)
    kind = "text"
    if parser is None:
        parser = parse_text
        kind = "text-opaque"
    try:
        ok, reason, facts = parser(path)
    except Exception as e:
        ok, reason, facts = False, f"raised: {e}", {}
    verdict = "parsed" if ok else "failed"
    return {"path": rel, "class": kind, "verdict": verdict,
            "reason": reason, "size": size, "facts": facts}
