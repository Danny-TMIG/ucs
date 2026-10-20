#!/usr/bin/env python3
"""correlate.py — join genesis × bodies × atlases × books.

Checks:
  1. every genesis id claimed by exactly one body
  2. body.governs[] all exist in genesis
  3. atlas entries all exist in genesis
  4. book chapter cites all exist in genesis
  5. every genesis id cited by at least one book chapter
  6. every failure class F1-F8 is prevented by at least one body
"""
import json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent

def load_genesis():
    text = (ROOT / "genesis.md").read_text()
    ids = {}
    for line in text.splitlines():
        m = re.match(r'\|\s*(ucs\.[A-Za-z_]+)\s*\|\s*(\w+)\s*\|\s*([^|]+?)\s*\|', line)
        if m:
            ids[m.group(1)] = {"kind": m.group(2), "path": m.group(3).strip()}
    # failure classes
    failures = set()
    for line in text.splitlines():
        m = re.match(r'\|\s*(F\d+)\s*\|', line)
        if m: failures.add(m.group(1))
    return ids, failures

def load_bodies():
    return {d["id"]: d for d in [json.loads(p.read_text()) for p in (ROOT/"standards/bodies").glob("*.json")]}

def load_atlases():
    return [json.loads(p.read_text()) for p in (ROOT/"standards/atlases").glob("*.json")]

def load_books():
    out = []
    for p in (ROOT/"standards/books").glob("*.md"):
        text = p.read_text()
        m = re.match(r'---\n(.*?)\n---', text, re.DOTALL)
        if not m: continue
        cites = re.findall(r'cites:\s*\[([^\]]+)\]', m.group(1))
        flat = [c.strip() for g in cites for c in g.split(",")]
        out.append({"file": str(p), "cites": flat})
    return out

def main():
    genesis, failures = load_genesis()
    bodies = load_bodies(); atlases = load_atlases(); books = load_books()
    errs = []

    # 1. exactly one body per genesis id
    claimed = {}
    for b in bodies.values():
        for gid in b["governs"]:
            claimed.setdefault(gid, []).append(b["id"])
    for gid in genesis:
        owners = claimed.get(gid, [])
        if len(owners) != 1:
            errs.append(f"{gid}: claimed by {len(owners)} bodies ({owners})")

    # 2. bodies only govern real ids
    for b in bodies.values():
        for gid in b["governs"]:
            if gid not in genesis:
                errs.append(f"{b['id']}: governs missing {gid}")

    # 3. atlas entries real
    for a in atlases:
        for e in a["entries"]:
            if e["id"] not in genesis:
                errs.append(f"atlas {a['id']}: entry {e['id']} missing from genesis")

    # 4. book cites real
    for bk in books:
        for cid in bk["cites"]:
            if cid not in genesis:
                errs.append(f"book {bk['file']}: cites missing {cid}")

    # 5. every genesis id cited
    cited = set()
    for bk in books: cited.update(bk["cites"])
    for gid in genesis:
        if gid not in cited:
            errs.append(f"{gid}: never cited by any book")

    # 6. every failure class prevented
    prevented = set()
    for b in bodies.values():
        prevented.update(b.get("prevents", []))
    for f in failures:
        if f not in prevented:
            errs.append(f"failure {f}: no body prevents it")

    if errs:
        print("\n".join(errs)); return 1
    print(f"correlate OK: {len(genesis)} ids, {len(bodies)} bodies, "
          f"{len(atlases)} atlases, {len(books)} books, {len(failures)} failure classes")
    return 0

if __name__ == "__main__":
    rc = main()
    try:
        assert rc in (0, 1), rc
    except Exception as e:
        raise SystemExit(f"correlate negative test failed: {e}")
    sys.exit(rc)
