\
\
\
\
\
\
\
\
\
\
from __future__ import annotations
import json, sys
from pathlib import Path
from collections import Counter
HOME = Path.home()
OUT = HOME / "ucs" / "enterprise"
def load() -> dict:
    return json.loads((OUT / "enterprise_registry.json").read_text())
def score_artifact(rec: dict) -> dict:
    f = len(rec["forbes"])
    n = len(rec["fortune"])
    g = len(rec["gartner"])
    h = len(rec["hype"])
    q = len(rec["quadrant"])
    score = g * 3 + f * 2 + n * 2 + h * 1 + q * 1
    return {
        "path": rec["path"],
        "score": score,
        "forbes": f,
        "fortune": n,
        "gartner": g,
        "hype": h,
        "quadrant": q,
        "labels": {
            "forbes": rec["forbes"][:5],
            "fortune": rec["fortune"][:5],
            "gartner": rec["gartner"][:5],
        },
    }
def main():
    reg = load()
    scored = [score_artifact(r) for r in reg["per_file"]]
    scored.sort(key=lambda r: -r["score"])
    print(f"== top 30 artifacts by enterprise score ==")
    for r in scored[:30]:
        print(
            f"  {r['score']:4d}  F{r['forbes']} N{r['fortune']} G{r['gartner']}  {r['path']}"
        )
    print()
    print(f"== artifacts scoring zero on all frames ==")
    zeros = [r for r in scored if r["score"] == 0]
    print(f"  count: {len(zeros)} / {len(scored)}")
    for r in zeros[:10]:
        print(f"    {r['path']}")
    print()
    print(f"== coverage ==")
    forbes = Counter()
    fortune = Counter()
    gartner = Counter()
    for r in scored:
        for x in r["labels"]["forbes"]:
            forbes[x.split("/")[0]] += 1
        for x in r["labels"]["fortune"]:
            fortune[x.split("/")[0]] += 1
        for x in r["labels"]["gartner"]:
            gartner[x.split("/")[0]] += 1
    print(f"  forbes sectors:  {len(forbes)}")
    print(f"  fortune roles:   {len(fortune)}")
    print(f"  gartner layers:  {len(gartner)}")
    print()
    print("  top sectors:")
    for k, n in forbes.most_common(10):
        print(f"    {k:40s} {n}")
    print()
    print("  top gartner layers:")
    for k, n in gartner.most_common(10):
        print(f"    {k:40s} {n}")
    print()
    out = OUT / "scored.json"
    out.write_text(
        json.dumps(
            {
                "count": len(scored),
                "top_30": scored[:30],
                "zeros": len(zeros),
                "coverage": {
                    "forbes_sectors": len(forbes),
                    "fortune_roles": len(fortune),
                    "gartner_layers": len(gartner),
                },
            },
            indent=2,
        )
    )
    print(f"wrote: {out}")
if __name__ == "__main__":
    main()
