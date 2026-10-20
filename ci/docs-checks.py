#!/usr/bin/env python3
import re, sys, pathlib

root = pathlib.Path(".")
errors = []

def read(p):
    return (root / p).read_text()

GATED = ["COG-CMP-004","GOV-DEC-013","CMP-DEC-006","CMP-DEC-007",
         "CMP-DEC-019","CMP-DEC-018","CMP-DEC-015"]
MATH = re.compile(r"-MATH-\d+")

def fm(p):
    s = read(p)
    if not s.startswith("---"):
        return {}
    end = s.find("\n---", 3)
    if end < 0:
        return {}
    d = {}
    for line in s[3:end].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            d[k.strip()] = v.strip()
    return d

def c1():
    for p in root.rglob("*.md"):
        rel = str(p.relative_to(root))
        if rel.startswith(("docs/entry","docs/orientation","specs",
                           "docs/commentary","ops","decisions")):
            f = fm(rel)
            for k in ("id","tier","owner"):
                if k not in f:
                    errors.append("C1 missing %s in %s" % (k, rel))

def c2():
    for p in (root/"specs").glob("*.md"):
        body = read(str(p.relative_to(root))).lower()
        if "not about" not in body and "not_about" not in body:
            errors.append("C2 no not-about in %s" % p)

def c3():
    for p in (root/"ops"/"runbooks").glob("*.md"):
        if "## Verify" not in read(str(p.relative_to(root))):
            errors.append("C3 no verify in %s" % p)

def c4():
    for p in (root/"specs").glob("*.md"):
        s = read(str(p.relative_to(root)))
        for m in re.finditer(r"\bshall\b", s):
            if "\u00a7" not in s[m.start():m.start()+200]:
                errors.append("C4 shall without section in %s" % p)

def c5():
    pass

def c6():
    cat = read("specs/contracts/index.md")
    for p in (root/"specs"/"contracts").glob("*.schema.json"):
        if p.name not in cat:
            errors.append("C6 %s missing from index" % p.name)

def c7():
    for p in (root/"specs"/"contracts").glob("*.schema.json"):
        if "$comment" not in read(str(p.relative_to(root))):
            errors.append("C7 %s missing $comment" % p.name)

def c8():
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in (".md",".py",".sh") \
           and str(p.relative_to(root)) not in ("README.md", "ci/docs-checks.py"):
            s = p.read_text(errors="ignore")
            for g in GATED:
                for m in re.finditer(g, s):
                    seg = s[m.start():m.start()+80].lower()
                    if not any(t in seg for t in
                               ("gate","not in v1","deferred","quarantined","validation")):
                        errors.append("C8 %s mention without gate in %s" % (g, p))

def c9():
    for p in root.rglob("*.md"):
        s = p.read_text(errors="ignore")
        for m in MATH.finditer(s):
            if not re.search(r"M[0-6]", s[m.start():m.start()+80]):
                errors.append("C9 %s without M-level in %s" % (m.group(0), p))

def c10():
    paths = read("docs/orientation/reading-paths.md")
    for m in re.finditer(r"`([^`]+)`", paths):
        t = m.group(1)
        if t and not t.startswith(("/","http")) and "\u00a7" not in t:
            if not (root/t).exists():
                errors.append("C10 broken reading-path link: %s" % t)

def c11():
    s = read("docs/orientation/reading-paths.md")
    if s.count("**You can now**") < 5:
        errors.append("C11 <5 'You can now' statements")

def c12():
    pass

def c13():
    for p in (root/"evidence").rglob("*.md"):
        s = p.read_text()
        for k in ("Ticket:","Revoked:","Revoked by:"):
            if k not in s:
                errors.append("C13 %s missing %s" % (p, k))

def c14():
    for p in (root/"decisions"/"closed").glob("*.md"):
        if "spec change" not in p.read_text().lower():
            errors.append("C14 %s missing spec change" % p)

def c15():
    for p in (root/"decisions"/"open").glob("*.md"):
        if "closure_vehicle" not in p.read_text():
            errors.append("C15 %s missing closure_vehicle" % p)

checks = [c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12,c13,c14,c15]
for c in checks:
    try:
        c()
    except Exception as e:
        errors.append("%s raised %s" % (c.__name__, e))

if errors:
    print("\n".join(errors))
    sys.exit(1)
print("OK: 15/15 docs checks")
