#!/usr/bin/env python3
import ast, pathlib, re, subprocess, sys

ROOT = pathlib.Path.cwd().resolve()
SKIP = {".git","build",".venv",".backup-comments","__pycache__","node_modules"}

def files(suffix):
    for p in ROOT.rglob(f"*{suffix}"):
        if any(x in p.parts for x in SKIP): continue
        yield p

def sh_valid(path):
    return subprocess.run(["bash","-n",str(path)], capture_output=True).returncode == 0

def py_valid(text):
    try: ast.parse(text); return True
    except SyntaxError: return False

FIXERS = []

def fixer(fn):
    FIXERS.append(fn)
    return fn

@fixer
def yaml_no_top_level_import(path):
    text = path.read_text()
    if "import yaml" not in text: return False
    if "find_spec" in text and "yaml" in text: return False
    new = re.sub(r"(?m)^\s*import yaml\s*$",
                 "import importlib.util\nyaml = __import__(\"yaml\") if importlib.util.find_spec(\"yaml\") else None",
                 text, count=1)
    if new == text: return False
    path.write_text(new); return True

@fixer
def py_try_missing_indent(path):
    text = path.read_text()
    if py_valid(text): return False
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.rstrip().endswith("try:"): continue
        indent = len(line) - len(line.lstrip())
        for j in range(i+1, min(i+4, len(lines))):
            if not lines[j].strip(): continue
            cur = len(lines[j]) - len(lines[j].lstrip())
            if cur <= indent:
                lines[j] = " "*(indent+4) + lines[j].lstrip()
                new = "\n".join(lines) + "\n"
                if py_valid(new): path.write_text(new); return True
            break
    return False

@fixer
def py_stray_indent(path):
    text = path.read_text()
    if py_valid(text): return False
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.strip() or i == 0: continue
        cur = len(line) - len(line.lstrip())
        prev = lines[i-1]
        if not prev.strip(): continue
        prev_ind = len(prev) - len(prev.lstrip())
        if cur > prev_ind and not prev.rstrip().endswith(":"):
            lines[i] = line.lstrip()
            new = "\n".join(lines) + "\n"
            if py_valid(new): path.write_text(new); return True
    return False

@fixer
def py_unclosed_triple(path):
    text = path.read_text()
    if py_valid(text): return False
    for q in ('"""', "'''"):
        if text.count(q) % 2 == 1:
            new = text.rstrip() + "\n" + q + "\n"
            if py_valid(new): path.write_text(new); return True
    return False

@fixer
def sh_unclosed_brace(path):
    if sh_valid(path): return False
    text = path.read_text()
    depth = 0
    for ch in text:
        if ch == "{": depth += 1
        elif ch == "}": depth = max(0, depth-1)
    if depth > 0:
        new = text.rstrip() + "\n" + "}\n"*depth
        path.write_text(new)
        if sh_valid(path): return True
        path.write_text(text)
    return False

@fixer
def sh_unclosed_quote(path):
    if sh_valid(path): return False
    text = path.read_text()
    for q in ('"', "'"):
        if text.count(q) % 2 == 1:
            new = text.rstrip() + "\n" + q + "\n"
            path.write_text(new)
            if sh_valid(path): return True
            path.write_text(text)
    return False

@fixer
def sh_unclosed_fi(path):
    if sh_valid(path): return False
    text = path.read_text()
    opens = len(re.findall(r"(?m)^\s*if\b", text)) - len(re.findall(r"(?m)^\s*fi\b", text))
    if opens > 0:
        new = text.rstrip() + "\n" + "fi\n"*opens
        path.write_text(new)
        if sh_valid(path): return True
        path.write_text(text)
    return False

@fixer
def sh_unclosed_done(path):
    if sh_valid(path): return False
    text = path.read_text()
    opens = len(re.findall(r"(?m)^\s*(for|while)\b", text)) - len(re.findall(r"(?m)^\s*done\b", text))
    if opens > 0:
        new = text.rstrip() + "\n" + "done\n"*opens
        path.write_text(new)
        if sh_valid(path): return True
        path.write_text(text)
    return False

def verify():
    errs = []
    for p in files(".py"):
        try: ast.parse(p.read_text())
        except SyntaxError as e: errs.append(f"{p.relative_to(ROOT)}:{e.lineno}: {e.msg}")
    for p in files(".sh"):
        if not sh_valid(p): errs.append(f"{p.relative_to(ROOT)}: {subprocess.run(['bash','-n',str(p)],capture_output=True,text=True).stderr.strip()[:120]}")
    return errs

if __name__ == "__main__":
    seen = set()
    for iteration in range(20):
        changed = False
        for p in list(files(".py")) + list(files(".sh")):
            key = str(p)
            for fn in FIXERS:
                try:
                    if fn(p):
                        if (key, fn.__name__) in seen:
                            # fixer already ran on this file and is re-applying: a bug in the fixer
                            print(f"  LOOP  {key} {fn.__name__} — fixer is not idempotent")
                            sys.exit(2)
                        seen.add((key, fn.__name__))
                        print(f"  fixed {key} via {fn.__name__}")
                        changed = True
                        break
                except Exception as e:
                    print(f"  fixer {fn.__name__} on {key} raised: {e}")
                    sys.exit(3)
        errs = verify()
        if not errs:
            print("clean")
            sys.exit(0)
        if not changed:
            break
    print("STILL BROKEN:")
    for e in errs: print(f"  {e}")
    sys.exit(1)
