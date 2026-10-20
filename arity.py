"""arity.py — dissolve boundaries with sub-arity.

Every behavior from ucs.py has arity = 1 (it takes ctx). Sub-arity means:
decompose every behavior into its atomic operations, each of which is itself
a behavior, recursively, until you reach primitives that cannot be split.

A behavior B with sub-arity k decomposes into k sub-behaviors B_1..B_k.
Each B_i has its own sub-arity. The recursion terminates at primitives:
opcodes of the register machine (LOAD, STORE, ADD, CALL, RET, ...).

This system:
  1. Loads every behavior from ~/ucs/out/registry.json
  2. Decomposes each into sub-behaviors by splitting on natural delimiters
     (spaces, dots, underscores, camelCase, dashes) — the grammar of the name
  3. Assigns each sub-behavior an arity = number of tokens
  4. Recurses until tokens are atoms (single words)
  5. Builds a sub-arity tree and a flattened primitive set
  6. Dissolves category boundaries by indexing behaviors by their primitives,
     not their category

The result: every behavior has a sub-arity decomposition; every sub-behavior
is itself addressable; category membership is derived, not declared.
"""

from __future__ import annotations
import argparse, json, re, sys
from collections import defaultdict, Counter
from pathlib import Path

HOME = Path.home()
UCS = HOME / "ucs"
OUT = UCS / "out"
OUT.mkdir(parents=True, exist_ok=True)
REG_PATH = OUT / "registry.json"

# ── tokenizer: the grammar of a behavior name ─────────────────────────
TOKEN_RE = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|$)|[0-9]+")


def tokenize(name: str) -> list:
    """Split a behavior name into atomic tokens.
    Handles: spaces, camelCase, snake_case, kebab-case, dots."""
    parts = re.split(r"[\s._\-]+", name)
    toks = []
    for p in parts:
        if not p:
            continue
        toks.extend(TOKEN_RE.findall(p) or [p.lower()])
    return toks


# ── sub-arity of a behavior ───────────────────────────────────────────
def sub_arity(name: str) -> int:
    """Arity = number of atomic tokens in the name."""
    return len(tokenize(name))


# ── decomposition tree ────────────────────────────────────────────────
def decompose(name: str, depth: int = 0, max_depth: int = 8) -> dict:
    """Recursively decompose a behavior name into a sub-arity tree."""
    toks = tokenize(name)
    node = {
        "name": name,
        "tokens": toks,
        "arity": len(toks),
        "depth": depth,
    }
    if len(toks) <= 1 or depth >= max_depth:
        node["primitive"] = True
        return node
    node["primitive"] = False
    node["children"] = [decompose(t, depth + 1, max_depth) for t in toks]
    return node


# ── flatten: collect all distinct sub-behaviors ───────────────────────
def flatten(node: dict, out: list):
    out.append(
        {
            "path": node["name"],
            "tokens": node["tokens"],
            "arity": node["arity"],
            "depth": node["depth"],
            "primitive": node.get("primitive", False),
        }
    )
    for c in node.get("children", []):
        flatten(c, out)


# ── boundary dissolution: re-index behaviors by primitives ────────────
def primitives_of(node: dict) -> set:
    prims = set()
    if node.get("primitive"):
        prims.add(node["name"].lower())
    for c in node.get("children", []):
        prims |= primitives_of(c)
    return prims


# ── main ──────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=8)
    ap.add_argument(
        "--show", action="store_true", help="print the decomposition of each behavior"
    )
    ap.add_argument(
        "--primitives", action="store_true", help="print the global primitive set"
    )
    args = ap.parse_args()

    if not REG_PATH.exists():
        print(f"missing {REG_PATH}; run ucs.py registry first")
        sys.exit(1)

    reg = json.loads(REG_PATH.read_text())
    behaviors = reg["behaviors"]
    print(f"== sub-arity decomposition ==")
    print(f"  behaviors loaded: {len(behaviors)}")
    print(f"  max depth:        {args.max_depth}")
    print()

    # decompose every behavior
    trees = {}
    flat_by_behavior = defaultdict(list)
    arity_hist = Counter()
    for b in behaviors:
        key = b["key"]
        tree = decompose(b["name"], max_depth=args.max_depth)
        trees[key] = tree
        flat = []
        flatten(tree, flat)
        flat_by_behavior[key] = flat
        arity_hist[tree["arity"]] += 1

    # report arity distribution
    print("== sub-arity distribution ==")
    for a in sorted(arity_hist):
        n = arity_hist[a]
        bar = "#" * min(60, n)
        print(f"  arity {a:2d}: {n:5d}  {bar}")
    print()

    # global primitive set (boundary dissolved)
    all_prims = set()
    prim_to_behaviors = defaultdict(list)
    for key, tree in trees.items():
        prims = primitives_of(tree)
        all_prims |= prims
        for p in prims:
            prim_to_behaviors[p].append(key)

    print(f"== global primitive set ==")
    print(f"  distinct primitives: {len(all_prims)}")
    print(f"  total sub-behaviors: {sum(len(v) for v in flat_by_behavior.values())}")
    print()

    # the boundary dissolution: behaviors sharing primitives
    print("== boundary dissolution: primitives shared across categories ==")
    top_prims = sorted(prim_to_behaviors.items(), key=lambda kv: -len(kv[1]))[:30]
    for p, keys in top_prims:
        cats = sorted(set(k.split(".")[0] for k in keys))
        print(
            f"  {p:24s} shared by {len(keys):4d} behaviors across "
            f"{len(cats)} categories: {','.join(cats[:8])}"
            + ("..." if len(cats) > 8 else "")
        )
    print()

    # categories after dissolution: group behaviors by dominant primitive
    print("== behaviors by dominant primitive ==")
    dom = defaultdict(list)
    for key, tree in trees.items():
        toks = tokenize(tree["name"])
        if not toks:
            continue
        d = toks[0].lower()
        dom[d].append(key)
    for d in sorted(dom, key=lambda k: -len(dom[k]))[:30]:
        print(f"  {d:24s} {len(dom[d]):4d} behaviors")
    print()

    # optional: print the decomposition of the first few behaviors
    if args.show:
        print("== sample decompositions ==")
        for b in behaviors[:5]:
            print(f"\n  [{b['key']}]")
            print(json.dumps(trees[b["key"]], indent=2))
        print()

    if args.primitives:
        print("== all primitives ==")
        for p in sorted(all_prims):
            print(f"  {p}")
        print()

    # persist
    out = {
        "behaviors": len(behaviors),
        "total_sub_behaviors": sum(len(v) for v in flat_by_behavior.values()),
        "distinct_primitives": len(all_prims),
        "arity_histogram": dict(arity_hist),
        "primitive_to_behaviors": {p: ks for p, ks in prim_to_behaviors.items()},
        "dominant_primitive": {d: ks for d, ks in dom.items()},
        "trees": trees,
    }
    p = OUT / "sub_arity.json"
    p.write_text(json.dumps(out, indent=2, default=str))
    print(f"wrote: {p}")
    print(f"  behaviors:           {out['behaviors']}")
    print(f"  total sub-behaviors: {out['total_sub_behaviors']}")
    print(f"  distinct primitives: {out['distinct_primitives']}")


if __name__ == "__main__":
    main()
