"""resolve.py — resolve any mnemonic across every ISA in the registry."""

from __future__ import annotations
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from grammar import Opcode, ISA, Registry


def load_registry() -> Registry:
    reg = Registry()
    data = json.loads((HERE / "registry.json").read_text())
    for isa_name, isa_data in data["isas"].items():
        isa = ISA(name=isa_name, source=isa_data.get("source", ""))
        for op_data in isa_data["opcodes"]:
            isa.add(
                Opcode(
                    mnemonic=op_data.get("mnemonic", ""),
                    operands=op_data.get("operands", []),
                    encoding=op_data.get("encoding", ""),
                    semantics=op_data.get("semantics", ""),
                    source=op_data.get("source", ""),
                )
            )
        reg.add_isa(isa)
    return reg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mnemonic", nargs="?")
    ap.add_argument("--isa")
    ap.add_argument("--list-isas", action="store_true")
    ap.add_argument("--counts", action="store_true")
    args = ap.parse_args()

    reg = load_registry()

    if args.list_isas:
        for name, isa in reg.isas.items():
            print(f"  {name:14s} {len(isa.opcodes):5d}  ({isa.source})")
        return

    if args.counts:
        print(f"isas:     {len(reg.isas)}")
        print(f"opcodes:  {reg.count()}")
        print(f"mnemonics: {len(reg.by_mnemonic)}")
        return

    if not args.mnemonic:
        ap.print_help()
        return

    hits = reg.resolve(args.mnemonic, args.isa)
    if not hits:
        print(f"no opcode named {args.mnemonic!r}")
        return
    print(f"== {args.mnemonic} ({len(hits)} hits) ==")
    for op in hits:
        enc = f"  [{op.encoding}]" if op.encoding else ""
        ops = f"  ({', '.join(op.operands)})" if op.operands else ""
        print(f"  {op.isa:14s}{enc}{ops}  <- {op.source}")


if __name__ == "__main__":
    main()
