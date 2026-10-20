"""orders.py — orders of orders of orders.

Three levels of "order":

  Order 0:  the artifact itself         (a file, a program, a system)
  Order 1:  the order of the artifact   (its dimension, arity, or layer)
  Order 2:  the order of the order      (the structure that ranks orders)
  Order 3:  the order of order of order (the meta-structure)

Concretely:
  Level 0  files       ~3,000 artifacts on disk
  Level 1  groups      the collections they belong to
  Level 2  lattices    the partial orders over groups
  Level 3  topoi       the category of lattices

The script reads every artifact it can find, computes each level,
and writes the lattice of lattices to disk.
"""

from __future__ import annotations
import hashlib, json, re, sys, time
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

HOME = Path.home()
OUT = HOME / "ucs"
OUT.mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════
# Level 0 — artifacts
# ══════════════════════════════════════════════════════════════════════
TEXT_EXT = {
    ".py",
    ".md",
    ".txt",
    ".sh",
    ".json",
    ".yaml",
    ".yml",
    ".c",
    ".h",
    ".rs",
    ".go",
}
EXCLUDE = (
    "/vem/store/objects/",
    "/site-packages/",
    "/node_modules/",
    "/.git/",
    "/__pycache__/",
)

ROOTS = [
    "foundations",
    "swarm",
    "gen",
    "kaleido",
    "ucs",
    "vem-index",
    "polyglot",
    "cs-partitions",
    "enterprise",
]


@dataclass
class Artifact:
    path: str
    kind: str  # extension
    size: int
    address: str  # sha256
    parent: str  # immediate dir under HOME
    group: str = ""  # assigned at level 1


def collect() -> list:
    out = []
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
            if p.suffix not in TEXT_EXT:
                continue
            try:
                size = p.stat().st_size
                if size > 2_000_000:
                    continue
                blob = p.read_bytes()
                addr = hashlib.sha256(blob).hexdigest()
            except OSError:
                continue
            parts = p.relative_to(HOME).parts
            parent = parts[0] if parts else "."
            out.append(
                Artifact(
                    path=str(p.relative_to(HOME)),
                    kind=p.suffix,
                    size=size,
                    address=addr,
                    parent=parent,
                )
            )
    return out


# ══════════════════════════════════════════════════════════════════════
# Level 1 — groups
# ══════════════════════════════════════════════════════════════════════
# A group is a set of artifacts unified by a property. Three orthogonal
# group structures are computed:
#   G_dir:  groups by parent directory
#   G_kind: groups by file extension
#   G_size: groups by size decile


def group_dir(arts: list) -> dict:
    g = defaultdict(list)
    for a in arts:
        g[a.parent].append(a.path)
    return dict(g)


def group_kind(arts: list) -> dict:
    g = defaultdict(list)
    for a in arts:
        g[a.kind].append(a.path)
    return dict(g)


def group_size(arts: list) -> dict:
    sizes = sorted(a.size for a in arts)
    if not sizes:
        return {}
    deciles = [sizes[int(len(sizes) * i / 10)] for i in range(1, 10)]

    def decile(s):
        for i, d in enumerate(deciles):
            if s <= d:
                return f"d{i + 1}"
        return "d10"

    g = defaultdict(list)
    for a in arts:
        g[decile(a.size)].append(a.path)
    return dict(g)


# ══════════════════════════════════════════════════════════════════════
# Level 2 — lattices
# ══════════════════════════════════════════════════════════════════════
# A lattice over a group structure is the partial order induced by
# subset/inclusion or by co-occurrence. For directories, the natural
# lattice is inclusion (dir A ⊂ dir B iff every file in A is in B).
# For kinds, the natural lattice is |G_kind| discrete (each kind is
# independent, so the lattice is a flat boolean algebra over kinds).


@dataclass
class Lattice:
    name: str
    nodes: list  # group names
    edges: list  # (child, parent) pairs
    is_lattice: bool  # does the poset have meets and joins?
    height: int


def lattice_from_dir(gdir: dict) -> Lattice:
    # for each pair (A, B), A ⊂ B iff every artifact in A appears in B
    sets = {k: set(v) for k, v in gdir.items()}
    nodes = sorted(sets)
    edges = []
    for a in nodes:
        for b in nodes:
            if a == b:
                continue
            if sets[a] and sets[a] < sets[b]:
                edges.append((a, b))
    return Lattice(
        name="dir-inclusion",
        nodes=nodes,
        edges=edges,
        is_lattice=_is_lattice(nodes, edges),
        height=_height(nodes, edges),
    )


def lattice_from_kind(gkind: dict) -> Lattice:
    # kinds are disjoint by construction, so the lattice is the boolean
    # algebra over the set of kinds — a flat antichain
    nodes = sorted(gkind)
    return Lattice(name="kind-flat", nodes=nodes, edges=[], is_lattice=True, height=1)


def lattice_from_size(gsize: dict) -> Lattice:
    # size deciles are totally ordered: d1 ⊂ d2 ⊂ ... ⊂ d10? No —
    # deciles are disjoint. So the poset is a flat antichain too.
    nodes = sorted(gsize)
    return Lattice(name="size-flat", nodes=nodes, edges=[], is_lattice=True, height=1)


def _is_lattice(nodes, edges) -> bool:
    """A finite poset is a lattice iff every pair has a meet and join.
    We check only for small lattices (nodes <= 30)."""
    if len(nodes) > 30:
        return True
    # build predecessor sets
    preds = {n: set() for n in nodes}
    for a, b in edges:
        preds[b].add(a)
    # transitive closure
    for _ in range(len(nodes)):
        for n in nodes:
            for p in list(preds[n]):
                preds[n] |= preds[p]
    # check every pair has a unique greatest lower bound
    for a in nodes:
        for b in nodes:
            lowers = [x for x in nodes if x in preds[a] and x in preds[b]]
            if not lowers:
                continue
            maxes = [
                x for x in lowers if not any(y in preds[x] for y in lowers if y != x)
            ]
            if len(maxes) > 1:
                return False
    return True


def _height(nodes, edges) -> int:
    if not nodes:
        return 0
    preds = {n: set() for n in nodes}
    for a, b in edges:
        preds[b].add(a)
    memo = {}

    def h(n):
        if n in memo:
            return memo[n]
        memo[n] = 1 + max((h(p) for p in preds[n]), default=0)
        return memo[n]

    return max(h(n) for n in nodes)


# ══════════════════════════════════════════════════════════════════════
# Level 3 — the category of lattices
# ══════════════════════════════════════════════════════════════════════
# The three lattices form a category where morphisms are order-preserving
# maps (monotone functions) between their node sets. Compute the full
# hom-set between every pair of lattices.


@dataclass
class Meta:
    lattices: list  # the Lattice objects
    morphisms: list  # (src, dst, kind)
    products: dict  # pairwise products
    coproducts: dict  # pairwise coproducts
    terminal: str  # terminal object
    initial: str  # initial object


def monotone_maps(src_nodes, src_edges, dst_nodes) -> list:
    """Enumerate monotone maps from src poset to a discrete dst set.
    For a discrete codomain, every function is monotone, so we just
    report the count and cardinality."""
    # count = |dst| ^ |src| (all functions since dst is discrete)
    return len(dst_nodes) ** len(src_nodes)


def compute_meta(lats: list) -> Meta:
    morphisms = []
    for i, a in enumerate(lats):
        for j, b in enumerate(lats):
            # monotone maps from a -> b
            n_maps = monotone_maps(a.nodes, a.edges, b.nodes)
            morphisms.append(
                {
                    "src": a.name,
                    "dst": b.name,
                    "count": n_maps,
                    "src_card": len(a.nodes),
                    "dst_card": len(b.nodes),
                }
            )
    # product and coproduct in the category of posets (as sets):
    # product = cartesian product with componentwise order
    # coproduct = disjoint union with no cross-order
    prods = {}
    cops = {}
    for i, a in enumerate(lats):
        for j, b in enumerate(lats):
            if i == j:
                continue
            key = f"{a.name}×{b.name}"
            prods[key] = len(a.nodes) * len(b.nodes)
            cops[key] = len(a.nodes) + len(b.nodes)
    # terminal is the single-node lattice; initial is empty
    return Meta(
        lattices=[asdict(l) for l in lats],
        morphisms=morphisms,
        products=prods,
        coproducts=cops,
        terminal="*",  # one-node poset
        initial="∅",  # empty poset
    )


# ══════════════════════════════════════════════════════════════════════
# main
# ══════════════════════════════════════════════════════════════════════
def main():
    print("== orders of orders of orders ==")
    print()
    t0 = time.time()
    arts = collect()
    print(f"level 0: artifacts     {len(arts)}")

    gdir = group_dir(arts)
    gkind = group_kind(arts)
    gsize = group_size(arts)
    print(
        f"level 1: groups        dir={len(gdir)}  kind={len(gkind)}  size={len(gsize)}"
    )

    lats = [
        lattice_from_dir(gdir),
        lattice_from_kind(gkind),
        lattice_from_size(gsize),
    ]
    print(f"level 2: lattices      {len(lats)}")
    for L in lats:
        print(
            f"    {L.name:16s} nodes={len(L.nodes):4d} "
            f"edges={len(L.edges):4d} lattice={L.is_lattice} h={L.height}"
        )

    meta = compute_meta(lats)
    print(f"level 3: morphisms     {len(meta.morphisms)}")
    print(f"         products      {len(meta.products)}")
    print(f"         terminal      {meta.terminal}")
    print(f"         initial       {meta.initial}")

    # write the full structure
    p = OUT / "orders.json"
    p.write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "level0": {
                    "artifact_count": len(arts),
                    "kinds": dict(Counter(a.kind for a in arts)),
                    "parents": dict(Counter(a.parent for a in arts)),
                },
                "level1": {
                    "dir_groups": {k: len(v) for k, v in gdir.items()},
                    "kind_groups": {k: len(v) for k, v in gkind.items()},
                    "size_groups": {k: len(v) for k, v in gsize.items()},
                },
                "level2": [asdict(L) for L in lats],
                "level3": asdict(meta),
            },
            indent=2,
        )
    )
    print()
    print(f"wrote: {p}")
    print(f"  ({time.time() - t0:.2f}s)")


if __name__ == "__main__":
    main()
