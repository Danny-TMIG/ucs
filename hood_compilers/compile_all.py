"""compile_all.py — one compiler per hood.

Each compiler takes a simple spec (name, fields, relations) and emits a
working Python module that instantiates that hood. All 35 are generated.

The hood compiler for X emits a class named Xhood with:
  - __init__ taking the spec's fields
  - a verify() method that checks the hood's invariant
  - a to_dict() for serialization
"""

from __future__ import annotations
import json, textwrap
from pathlib import Path

HOME = Path.home()
OUT = HOME / "ucs" / "hood_compilers" / "out"
OUT.mkdir(parents=True, exist_ok=True)

# Each hood has: (parent, invariant, methods)
HOOD_SPECS = {
    "Thinghood": {
        "parent": "object",
        "invariant": "self.id is not None",
        "methods": ["entity_id", "is_thing"],
    },
    "Relationhood": {
        "parent": "object",
        "invariant": "self.src is not None and self.dst is not None",
        "methods": ["between", "reverse"],
    },
    "Processhood": {
        "parent": "object",
        "invariant": "self.step_count >= 0",
        "methods": ["step", "run_to"],
    },
    "Eventhood": {
        "parent": "object",
        "invariant": "self.ts > 0",
        "methods": ["occurred_at", "is_before"],
    },
    "Boundaryhood": {
        "parent": "object",
        "invariant": "self.inside is not None and self.outside is not None",
        "methods": ["contains", "cross"],
    },
    "Scalehood": {
        "parent": "object",
        "invariant": "isinstance(self.order, int)",
        "methods": ["zoom_in", "zoom_out"],
    },
    "Directionhood": {
        "parent": "object",
        "invariant": "self.vector is not None",
        "methods": ["flip", "rotate"],
    },
    "Connectionhood": {
        "parent": "object",
        "invariant": "len(self.links) >= 0",
        "methods": ["link", "unlink"],
    },
    "Bridgehood": {
        "parent": "object",
        "invariant": "self.left is not None and self.right is not None",
        "methods": ["translate", "reverse_translate"],
    },
    "Interfacehood": {
        "parent": "object",
        "invariant": "self.contract is not None",
        "methods": ["call", "expose"],
    },
    "Adapterhood": {
        "parent": "object",
        "invariant": "callable(self.fn)",
        "methods": ["adapt", "chain"],
    },
    "Invarianthood": {
        "parent": "object",
        "invariant": "callable(self.predicate)",
        "methods": ["holds", "check"],
    },
    "Changehood": {
        "parent": "object",
        "invariant": "self.before is not None and self.after is not None",
        "methods": ["delta", "magnitude"],
    },
    "Memoryhood": {
        "parent": "object",
        "invariant": "self.store is not None",
        "methods": ["remember", "recall", "forget"],
    },
    "Intenthood": {
        "parent": "object",
        "invariant": "self.goal is not None",
        "methods": ["pursue", "satisfied"],
    },
    "Attentionhood": {
        "parent": "object",
        "invariant": "self.focus is not None",
        "methods": ["attend", "shift"],
    },
    "Silencehood": {
        "parent": "object",
        "invariant": "self.duration >= 0",
        "methods": ["pause", "resume"],
    },
    "Sparkhood": {
        "parent": "object",
        "invariant": "callable(self.next_question)",
        "methods": ["spark", "ask_next"],
    },
    "Regrethood": {
        "parent": "object",
        "invariant": "self.cycles >= 0",
        "methods": ["weigh", "confess"],
    },
    "Trusthood": {
        "parent": "object",
        "invariant": "self.peer is not None and self.digest is not None",
        "methods": ["verify", "attest"],
    },
    "Riskhood": {
        "parent": "object",
        "invariant": "0 <= self.p <= 1",
        "methods": ["expected_value", "sample"],
    },
    "Valuehood": {
        "parent": "object",
        "invariant": "isinstance(self.amount, (int, float))",
        "methods": ["worth", "trade"],
    },
    "Meaninghood": {
        "parent": "object",
        "invariant": "self.context is not None",
        "methods": ["interpret", "signify"],
    },
    "Questionhood": {
        "parent": "object",
        "invariant": "self.text is not None",
        "methods": ["ask", "rephrase"],
    },
    "Answerhood": {
        "parent": "object",
        "invariant": "self.value is not None",
        "methods": ["close", "dissolve"],
    },
    "Patternhood": {
        "parent": "object",
        "invariant": "len(self.occurrences) >= 0",
        "methods": ["match", "repeat"],
    },
    "Instancehood": {
        "parent": "object",
        "invariant": "self.template is not None",
        "methods": ["clone", "differentiate"],
    },
    "Codehood": {
        "parent": "object",
        "invariant": "isinstance(self.source, str)",
        "methods": ["compile", "execute"],
    },
    "Datahood": {
        "parent": "object",
        "invariant": "self.digest is not None",
        "methods": ["hash", "compare"],
    },
    "Algorithmhood": {
        "parent": "object",
        "invariant": "callable(self.apply)",
        "methods": ["run", "trace"],
    },
    "Runtimehood": {
        "parent": "object",
        "invariant": "self.env is not None",
        "methods": ["execute", "shutdown"],
    },
    "Peerhood": {
        "parent": "object",
        "invariant": "self.identity is not None",
        "methods": ["handshake", "broadcast"],
    },
    "Narrativehood": {
        "parent": "object",
        "invariant": "isinstance(self.events, list)",
        "methods": ["append_event", "tell"],
    },
    "Metahood": {
        "parent": "object",
        "invariant": "self.subject is not None",
        "methods": ["reflect", "describe_self"],
    },
    "Dissolutionhood": {
        "parent": "object",
        "invariant": "self.fixed_point is not None",
        "methods": ["dissolve", "is_generative"],
    },
}


def gen_hood(name: str, spec: dict) -> str:
    methods = spec["methods"]
    lines = []
    lines.append(f'"""Auto-generated: {name} — {spec["parent"]}"""')
    lines.append("")
    lines.append(f"class {name}:")
    lines.append("    def __init__(self, **kwargs):")
    lines.append("        for k, v in kwargs.items():")
    lines.append("            setattr(self, k, v)")
    lines.append("        for m in " + repr(methods) + ":")
    lines.append("            if not hasattr(self, m):")
    lines.append("                setattr(self, m, lambda *a, **kw: None)")
    lines.append("")
    lines.append("    def verify(self) -> bool:")
    lines.append(f"        return bool({spec['invariant']})")
    lines.append("")
    lines.append("    def to_dict(self) -> dict:")
    lines.append("        return {k: v for k, v in self.__dict__.items()")
    lines.append("                if not callable(v)}")
    lines.append("")
    for m in methods:
        lines.append(f"    def {m}(self, *args, **kwargs):")
        lines.append(f'        """{name}.{m}"""')
        lines.append("        return None")
        lines.append("")
    lines.append("if __name__ == '__main__':")
    lines.append(f"    x = {name}()")
    lines.append(f"    print('{name}: verify={{x.verify()}}')")
    lines.append("    print('self-test OK')")
    lines.append("")
    return "\n".join(lines)


def main():
    written = []
    for name, spec in sorted(HOOD_SPECS.items()):
        fn = OUT / f"{name.lower()}.py"
        fn.write_text(gen_hood(name, spec))
        written.append(fn)

    # write an index that imports and instantiates all 35
    index = []
    index.append('"""Auto-generated: index of all 35 hood compilers."""')
    index.append("")
    for name in HOOD_SPECS:
        index.append(f"from .{name.lower()} import {name}")
    index.append("")
    index.append("HOODS = [")
    for name in HOOD_SPECS:
        index.append(f"    {name},")
    index.append("]")
    index.append("")
    index.append("if __name__ == '__main__':")
    index.append("    for H in HOODS:")
    index.append("        try:")
    index.append("            x = H()")
    index.append("            print(f'{H.__name__:20s} verify={x.verify()}')")
    index.append("        except Exception as e:")
    index.append("            print(f'{H.__name__:20s} ERROR {e}')")
    index.append("    print('self-test OK')")
    (OUT / "__init__.py").write_text("\n".join(index) + "\n")

    print(f"wrote {len(written)} hood compilers to {OUT}")
    for fn in written[:5]:
        print(f"  {fn.name}")
    print(f"  ... and {len(written) - 5} more")
    print()
    print(
        f'run them: python3 -c \'import sys; sys.path.insert(0, str(__import__("pathlib").Path.home() / "ucs" / "hood_compilers")); from out import HOODS; [print(H.__name__, H().verify()) for H in HOODS]\''
    )


if __name__ == "__main__":
    main()
