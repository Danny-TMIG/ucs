import ast, gzip, importlib.util, json, pathlib, subprocess, tarfile, zipfile

yaml = __import__("yaml") if importlib.util.find_spec("yaml") else None
tomllib = __import__("tomllib") if importlib.util.find_spec("tomllib") else None

STATE_DIRS = {".git", "build", "logs", "tmp", ".cache", "dist", "target",
              "node_modules", ".venv", "htmlcov", "__pycache__",
              ".mypy_cache", ".pytest_cache", ".backup-comments", "systems"}

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
               ".key", ".pem", ".crt", ".der", ".p12",
               ".bin", ".dat", ".db", ".sqlite", ".sqlite3",
               ".swp", ".swo", ".tmp", ".bak", ".orig", ".rej", ".pid"}

MAGIC_BIN = (b"\x89PNG", b"\xff\xd8\xff", b"%PDF", b"PK\x03\x04",
             b"\x1f\x8b", b"GGUF", b"\x7fELF", b"\xca\xfe\xba\xbe")


def parse_python(path):
    ast.parse(path.read_text()); return True, "", {}

def parse_shell(path):
    r = subprocess.run(["bash","-n",str(path)], capture_output=True, text=True, timeout=10)
    return (True,"",{}) if r.returncode == 0 else (False, r.stderr.strip()[:200], {})

def parse_json(path):
    json.loads(path.read_text()); return True, "", {}

def parse_jsonl(path):
    n = 0
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip(): continue
        try: json.loads(line)
        except json.JSONDecodeError as e: return False, f"line {i}: {e}", {}
        n += 1
    return True, "", {"lines": n}

def parse_yaml(path):
    if yaml is None: return True, "skipped", {}
    try: yaml.safe_load(path.read_text()); return True, "", {}
    except Exception as e: return False, str(e), {}

def parse_toml(path):
    if tomllib is None: return True, "skipped", {}
    try: tomllib.loads(path.read_text()); return True, "", {}
    except Exception as e: return False, str(e), {}

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


SPECIFIC = {
    ".py": parse_python, ".pyi": parse_python,
    ".sh": parse_shell, ".bash": parse_shell, ".zsh": parse_shell,
    ".json": parse_json,
    ".jsonl": parse_jsonl, ".ndjson": parse_jsonl,
    ".yaml": parse_yaml, ".yml": parse_yaml,
    ".toml": parse_toml,
    ".md": parse_markdown, ".markdown": parse_markdown,
    ".txt": parse_text, ".log": parse_text,
    ".cfg": parse_text, ".ini": parse_text, ".conf": parse_text, ".env": parse_text,
    ".js": parse_text, ".mjs": parse_text, ".cjs": parse_text,
    ".ts": parse_text, ".tsx": parse_text, ".jsx": parse_text,
    ".html": parse_text, ".htm": parse_text, ".css": parse_text, ".scss": parse_text,
    ".xml": parse_text, ".svg": parse_text, ".plist": parse_text,
    ".c": parse_text, ".h": parse_text, ".cpp": parse_text, ".cc": parse_text, ".hpp": parse_text,
    ".go": parse_text, ".rs": parse_text, ".java": parse_text, ".rb": parse_text,
    ".php": parse_text, ".sql": parse_text, ".g4": parse_text, ".proto": parse_text,
    ".gr": parse_text, ".csv": parse_text, ".tsv": parse_text,
}


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
    if ext in SPECIFIC:
        try:
            path.read_text(encoding="utf-8")
            return "text"
        except UnicodeDecodeError:
            return "binary"
    return "text"


def describe(path, root):
    try: rel = str(path.relative_to(root))
    except ValueError: rel = str(path)
    if not path.exists():
        return {"path": rel, "class": "missing", "format": "?", "verdict": "failed",
                "reason": "file missing", "size": 0}
    size = path.stat().st_size
    if size == 0:
        return {"path": rel, "class": "empty", "format": "empty",
                "verdict": "skipped", "reason": "empty", "size": 0}
    cls = class_of(path, root)
    ext = path.suffix.lower()
    if cls == "state":
        return {"path": rel, "class": "state", "format": "state",
                "verdict": "skipped", "reason": "state dir", "size": size}
    if cls == "binary":
        return {"path": rel, "class": "binary", "format": ext or "(binary)",
                "verdict": "parsed", "reason": "binary", "size": size}
    if cls == "container":
        ok, reason, facts = parse_container(path, ext)
        return {"path": rel, "class": "container", "format": ext,
                "verdict": "parsed" if ok else "failed",
                "reason": reason, "size": size, "facts": facts}
    parser = SPECIFIC.get(ext)
    if parser is None:
        return {"path": rel, "class": "text-opaque", "format": ext or "(none)",
                "verdict": "parsed", "reason": "text", "size": size}
    try:
        ok, reason, facts = parser(path)
    except Exception as e:
        ok, reason, facts = False, f"raised: {e}", {}
    return {"path": rel, "class": "text", "format": ext,
            "verdict": "parsed" if ok else "failed",
            "reason": reason, "size": size, "facts": facts}
