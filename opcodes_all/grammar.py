"""grammar.py — the grammar of an opcode.

An opcode is a tuple:
    (mnemonic, operands, encoding, semantics, isa, source)

Where:
  mnemonic  : str    the assembly name, e.g. "MOV"
  operands  : list   operand classes, e.g. ["reg","imm"]
  encoding  : str    hex bytes or bit pattern (if known)
  semantics : str    informal meaning, e.g. "reg := imm"
  isa       : str    which ISA it belongs to
  source    : str    where we learned it from

An ISA is a set of opcodes.
A registry is a set of ISAs.
A resolver maps any (mnemonic, isa) to its canonical opcode.
"""

from __future__ import annotations
import json, re, subprocess, sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional


@dataclass
class Opcode:
    mnemonic: str
    operands: list = field(default_factory=list)
    encoding: str = ""
    semantics: str = ""
    isa: str = ""
    source: str = ""

    def to_dict(self):
        d = asdict(self)
        d["operands"] = list(self.operands)
        return d


@dataclass
class ISA:
    name: str
    opcodes: list = field(default_factory=list)
    source: str = ""

    def add(self, op: Opcode):
        op.isa = self.name
        self.opcodes.append(op)


class Registry:
    def __init__(self):
        self.isas: dict[str, ISA] = {}
        self.by_mnemonic: dict[str, list] = {}

    def add_isa(self, isa: ISA):
        self.isas[isa.name] = isa
        for op in isa.opcodes:
            self.by_mnemonic.setdefault(op.mnemonic.lower(), []).append(op)

    def resolve(self, mnemonic: str, isa: Optional[str] = None) -> list:
        hits = self.by_mnemonic.get(mnemonic.lower(), [])
        if isa:
            hits = [h for h in hits if h.isa == isa]
        return hits

    def count(self):
        return sum(len(i.opcodes) for i in self.isas.values())
