"""isa_info.py — inverse resolver.

Given an ISA name, return its family, source, spec, and opcode count.
Given a family, return every ISA in that family.
Given no argument, list every ISA in the merged registry grouped by family.
"""

from __future__ import annotations
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))


def load_isa_registry():
    p = HERE / "isa_registry.json"
    if not p.exists():
        print(f"missing {p}; run isa_grammar.py first")
        sys.exit(1)
    return json.loads(p.read_text())


def load_curated_family() -> dict:
    """Map curated ISA name -> family from isa_grammar.CURATED_SPECS."""
    try:
        import isa_grammar

        table = {n.lower(): f for n, f, _ in isa_grammar.CURATED_SPECS}
        # aliases: collected ISA names that match a curated family
        table.setdefault("riscv", "RISC-V")
        table.setdefault("riscv-v", "RISC-V")
        return table
    except Exception:
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", nargs="?")
    ap.add_argument("--family")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--counts", action="store_true")
    ap.add_argument("--has", help="opcode mnemonic to look for across every ISA")
    args = ap.parse_args()

    data = load_isa_registry()
    isas = data["isas"]
    families = load_curated_family()

    if args.counts:
        print(f"isas:               {data['totals']['isas']}")
        print(f"opcodes:            {data['totals']['opcodes']}")
        print(f"distinct mnemonics: {data['totals']['distinct_mnemonics']}")
        return

    if args.all:
        # group by source
        by_src = {}
        for name, d in isas.items():
            src = d.get("source", "?")
            by_src.setdefault(src, []).append((name, len(d["opcodes"])))
        for src in sorted(by_src):
            print(f"== {src} ({len(by_src[src])}) ==")
            for name, n in sorted(by_src[src]):
                print(f"  {name:36s} {n:5d}")
        return

    if args.family:
        fam = args.family.lower()
        matches = [
            (n, d)
            for n, d in isas.items()
            if families.get(n.lower(), "").lower() == fam
        ]
        if not matches:
            print(f"no ISAs in family {fam!r}")
            return
        print(f"== family {fam} ({len(matches)}) ==")
        for name, d in sorted(matches):
            print(f"  {name:36s} {len(d['opcodes']):5d}  {d.get('source', '')}")
        return

    if args.has:
        import sys as _sys
        from pathlib import Path as _P

        _sys.path.insert(0, str(_P(__file__).parent))
        try:
            from isa_aliases import resolve, is_semantic
        except Exception:

            def resolve(m):
                return {m}

            def is_semantic(m):
                return False

        m = args.has.lower()
        wanted = resolve(m)
        semantic = is_semantic(m)

        hits = []
        for name, d in isas.items():
            for op in d["opcodes"]:
                mn = op.get("mnemonic", "").lower()
                if mn in wanted:
                    hits.append((name, op))
                    break

        header = f"== ISAs with opcode {m!r}"
        if semantic:
            header += f" (semantic: {sorted(wanted)[:6]}...)"
        header += f" ({len(hits)}) =="
        print(header)
        for name, op in sorted(hits):
            enc = f" [{op.get('encoding', '')}]" if op.get("encoding") else ""
            ops = (
                f"  ({', '.join(op.get('operands', []))})" if op.get("operands") else ""
            )
            print(f"  {name:36s} {op.get('mnemonic', ''):16s}{enc}{ops}")
        return

    if not args.name:
        # list everything grouped
        families_seen = {}
        for name in sorted(isas):
            fam = families.get(name.lower(), "discovered")
            families_seen.setdefault(fam, []).append(name)
        for fam in sorted(families_seen):
            print(f"== {fam} ({len(families_seen[fam])}) ==")
            for n in families_seen[fam]:
                print(f"  {n}")
        return

    # look up a single ISA
    key = args.name.lower()
    for name, d in isas.items():
        if name.lower() == key:
            fam = families.get(key, "discovered")
            print(f"name:    {name}")
            print(f"family:  {fam}")
            print(f"source:  {d.get('source', '')}")
            print(f"opcodes: {len(d['opcodes'])}")
            print(
                f"spec:    "
                + next(
                    (
                        op.get("semantics", "")
                        for op in d["opcodes"]
                        if "http" in op.get("semantics", "")
                    ),
                    "(none)",
                )
            )
            return
    print(f"no ISA named {args.name!r}")


if __name__ == "__main__":
    main()
