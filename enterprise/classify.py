\
from __future__ import annotations
import json, re, sys, time
from collections import defaultdict, Counter
from pathlib import Path
HOME = Path.home()
sys.path.insert(0, str(HOME / "ucs" / "enterprise"))
from frameworks import (
    FORBES_SECTORS,
    FORTUNE_FUNCTIONS,
    GARTNER_LAYERS,
    HYPE_PHASES,
    MAGIC_QUADRANT,
)
OUT = HOME / "ucs" / "enterprise"
OUT.mkdir(parents=True, exist_ok=True)
ROOTS = [
    "foundations",
    "swarm",
    "gen",
    "kaleido",
    "ucs",
    "vem-index",
    "polyglot",
    "cs-partitions",
    "vem",
    "enterprise",
    "resolve",
]
ROOT_FILES = [
    "procedural-mesh.py",
    "constellation-partition.py",
    "generative_expectations.py",
    "great_expectations.py",
    "spec_throughput.py",
    "tape_out_boundaries.py",
    "vem-protocol.md",
    "gdm-spec.md",
    "gdm-test-suite.py",
    "gexp-test.sh",
    "run_spec_throughput.sh",
    "verify_all.sh",
]
TEXT_EXT = {".py", ".md", ".txt", ".rst", ".org", ".sh", ".json", ".yaml", ".yml", ".c"}
def read_head(p: Path, n: int = 8192) -> str:
    try:
        return p.read_text(errors="ignore")[:n]
    except OSError:
        return ""
def walk() -> list[Path]:
    out = []
    EXCLUDE = (
        "/vem/store/objects/",
        "/site-packages/",
        "/node_modules/",
        "/.git/",
        "/__pycache__/",
    )
    for rn in ROOTS:
        r = HOME / rn
        if not r.exists():
            continue
        for p in sorted(r.rglob("*")):
            sp = str(p)
            if any(x in sp for x in EXCLUDE):
                continue
            if not p.is_file():
                continue
            if p.name.endswith(".rec.json"):
                continue
            if p.suffix not in TEXT_EXT:
                continue
            try:
                if p.stat().st_size <= 1_000_000:
                    out.append(p)
            except OSError:
                pass
    for f in ROOT_FILES:
        p = HOME / f
        if p.exists() and p.is_file():
            out.append(p)
    return out
def classify_forbes(text: str, path: str) -> list[str]:
    hits = []
    hay = (text + " " + path).lower()
    for sector, industries in FORBES_SECTORS.items():
        for ind in industries:
            if ind.lower() in hay:
                hits.append(f"{sector}/{ind}")
    return sorted(set(hits))
def classify_fortune(text: str, path: str) -> list[str]:
    hits = []
    hay = (text + " " + path).lower()
    for role, funcs in FORTUNE_FUNCTIONS.items():
        for fn in funcs:
            if fn.lower() in hay:
                hits.append(f"{role}/{fn}")
    return sorted(set(hits))
def classify_gartner(text: str, path: str) -> list[str]:
    hits = []
    hay = (text + " " + path).lower()
    for layer, cats in GARTNER_LAYERS.items():
        for c in cats:
            if c.lower() in hay:
                hits.append(f"{layer}/{c}")
    return sorted(set(hits))
def classify_hype(text: str) -> list[str]:
    hits = []
    hay = text.lower()
    for phase in HYPE_PHASES:
        if phase.lower() in hay:
            hits.append(phase)
    return hits
def classify_quadrant(text: str) -> list[str]:
    hits = []
    hay = text.lower()
    for q in MAGIC_QUADRANT:
        if q.lower() in hay:
            hits.append(q)
    return hits
def main():
    files = walk()
    print(f"== enterprise classification ==")
    print(f"  files scanned: {len(files)}")
    print()
    forbes_grid = defaultdict(lambda: defaultdict(int))
    fortune_grid = defaultdict(lambda: defaultdict(int))
    gartner_grid = defaultdict(lambda: defaultdict(int))
    hype_counter = Counter()
    quadrant_counter = Counter()
    per_file = []
    for p in files:
        text = read_head(p)
        path = str(p.relative_to(HOME))
        f_hits = classify_forbes(text, path)
        fn_hits = classify_fortune(text, path)
        g_hits = classify_gartner(text, path)
        h_hits = classify_hype(text)
        q_hits = classify_quadrant(text)
        top = path.split("/")[0]
        for h in f_hits:
            forbes_grid[top][h] += 1
        for h in fn_hits:
            fortune_grid[top][h] += 1
        for h in g_hits:
            gartner_grid[top][h] += 1
        for h in h_hits:
            hype_counter[h] += 1
        for h in q_hits:
            quadrant_counter[h] += 1
        per_file.append(
            {
                "path": path,
                "size": p.stat().st_size,
                "forbes": f_hits,
                "fortune": fn_hits,
                "gartner": g_hits,
                "hype": h_hits,
                "quadrant": q_hits,
            }
        )
    forbes_total = Counter()
    for top, cells in forbes_grid.items():
        for cell, n in cells.items():
            forbes_total[cell] += n
    fortune_total = Counter()
    for top, cells in fortune_grid.items():
        for cell, n in cells.items():
            fortune_total[cell] += n
    gartner_total = Counter()
    for top, cells in gartner_grid.items():
        for cell, n in cells.items():
            gartner_total[cell] += n
    print(f"== Forbes Global 2000 sectors touched ({len(forbes_total)}) ==")
    for cell, n in forbes_total.most_common(20):
        print(f"  {cell:60s} {n:5d}")
    print()
    print(f"== Fortune 500 functions touched ({len(fortune_total)}) ==")
    for cell, n in fortune_total.most_common(20):
        print(f"  {cell:40s} {n:5d}")
    print()
    print(f"== Gartner layers touched ({len(gartner_total)}) ==")
    for cell, n in gartner_total.most_common(20):
        print(f"  {cell:40s} {n:5d}")
    print()
    print(f"== Hype cycle phases mentioned ==")
    for phase in HYPE_PHASES:
        print(f"  {phase:36s} {hype_counter.get(phase, 0):5d}")
    print()
    print(f"== Magic Quadrant positions mentioned ==")
    for q in MAGIC_QUADRANT:
        print(f"  {q:36s} {quadrant_counter.get(q, 0):5d}")
    print()
    p = OUT / "enterprise_registry.json"
    p.write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "files_scanned": len(files),
                "forbes_totals": dict(forbes_total),
                "fortune_totals": dict(fortune_total),
                "gartner_totals": dict(gartner_total),
                "hype_totals": dict(hype_counter),
                "quadrant_totals": dict(quadrant_counter),
                "per_file": per_file,
            },
            indent=2,
        )
    )
    print(f"wrote: {p}")
if __name__ == "__main__":
    main()
