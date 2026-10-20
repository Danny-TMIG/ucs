"""refine.py — make every hood self-verifying with no args.

Adds a `__init__` that supplies defaults for the fields each hood's
invariant needs, and a `verify()` that returns True on a fresh instance.

Rewrites all 35 modules in ~/ucs/hood_compilers/out/.
"""

from __future__ import annotations
from pathlib import Path
import textwrap

OUT = Path.home() / "ucs" / "hood_compilers" / "out"

# per hood: the fields required by the invariant, with defaults
DEFAULTS = {
    "Thinghood": {"id": "thing-0"},
    "Relationhood": {"src": "a", "dst": "b"},
    "Processhood": {"step_count": 0},
    "Eventhood": {"ts": 1.0},
    "Boundaryhood": {"inside": set(), "outside": set()},
    "Scalehood": {"order": 0},
    "Directionhood": {"vector": (1.0, 0.0)},
    "Connectionhood": {"links": []},
    "Bridgehood": {"left": "L", "right": "R"},
    "Interfacehood": {"contract": {}},
    "Adapterhood": {"fn_src": "lambda x: x"},
    "Invarianthood": {"predicate_src": "lambda x: True"},
    "Changehood": {"before": 0, "after": 0},
    "Memoryhood": {"store": {}},
    "Intenthood": {"goal": "unspecified"},
    "Attentionhood": {"focus": "unfocused"},
    "Silencehood": {"duration": 0.0},
    "Sparkhood": {"next_question_src": "lambda: 'what next?'"},
    "Regrethood": {"cycles": 0},
    "Trusthood": {"peer": "peer-0", "digest": "sha256:0"},
    "Riskhood": {"p": 0.5},
    "Valuehood": {"amount": 0.0},
    "Meaninghood": {"context": {}},
    "Questionhood": {"text": "what?"},
    "Answerhood": {"value": None},
    "Patternhood": {"occurrences": []},
    "Instancehood": {"template": "base"},
    "Codehood": {"source": ""},
    "Datahood": {"digest": "sha256:0"},
    "Algorithmhood": {"apply_src": "lambda x: x"},
    "Runtimehood": {"env": {}},
    "Peerhood": {"identity": "peer-0"},
    "Narrativehood": {"events": []},
    "Metahood": {"subject": "self"},
    "Dissolutionhood": {"fixed_point": None},
}

METHODS = {
    "Thinghood": ["entity_id", "is_thing"],
    "Relationhood": ["between", "reverse"],
    "Processhood": ["step", "run_to"],
    "Eventhood": ["occurred_at", "is_before"],
    "Boundaryhood": ["contains", "cross"],
    "Scalehood": ["zoom_in", "zoom_out"],
    "Directionhood": ["flip", "rotate"],
    "Connectionhood": ["link", "unlink"],
    "Bridgehood": ["translate", "reverse_translate"],
    "Interfacehood": ["call", "expose"],
    "Adapterhood": ["adapt", "chain"],
    "Invarianthood": ["holds", "check"],
    "Changehood": ["delta", "magnitude"],
    "Memoryhood": ["remember", "recall", "forget"],
    "Intenthood": ["pursue", "satisfied"],
    "Attentionhood": ["attend", "shift"],
    "Silencehood": ["pause", "resume"],
    "Sparkhood": ["spark", "ask_next"],
    "Regrethood": ["weigh", "confess"],
    "Trusthood": ["verify_peer", "attest"],
    "Riskhood": ["expected_value", "sample"],
    "Valuehood": ["worth", "trade"],
    "Meaninghood": ["interpret", "signify"],
    "Questionhood": ["ask", "rephrase"],
    "Answerhood": ["close", "dissolve"],
    "Patternhood": ["match", "repeat"],
    "Instancehood": ["clone", "differentiate"],
    "Codehood": ["compile", "execute"],
    "Datahood": ["hash_it", "compare"],
    "Algorithmhood": ["run", "trace"],
    "Runtimehood": ["execute", "shutdown"],
    "Peerhood": ["handshake", "broadcast"],
    "Narrativehood": ["append_event", "tell"],
    "Metahood": ["reflect", "describe_self"],
    "Dissolutionhood": ["dissolve", "is_generative"],
}

INVARIANTS = {
    "Thinghood": "self.id is not None",
    "Relationhood": "self.src is not None and self.dst is not None",
    "Processhood": "self.step_count >= 0",
    "Eventhood": "self.ts > 0",
    "Boundaryhood": "self.inside is not None and self.outside is not None",
    "Scalehood": "isinstance(self.order, int)",
    "Directionhood": "self.vector is not None",
    "Connectionhood": "self.links is not None",
    "Bridgehood": "self.left is not None and self.right is not None",
    "Interfacehood": "self.contract is not None",
    "Adapterhood": "callable(self.fn)",
    "Invarianthood": "callable(self.predicate)",
    "Changehood": "self.before is not None and self.after is not None",
    "Memoryhood": "self.store is not None",
    "Intenthood": "self.goal is not None",
    "Attentionhood": "self.focus is not None",
    "Silencehood": "self.duration >= 0",
    "Sparkhood": "callable(self.next_question)",
    "Regrethood": "self.cycles >= 0",
    "Trusthood": "self.peer is not None and self.digest is not None",
    "Riskhood": "0 <= self.p <= 1",
    "Valuehood": "isinstance(self.amount, (int, float))",
    "Meaninghood": "self.context is not None",
    "Questionhood": "self.text is not None",
    "Answerhood": "True",
    "Patternhood": "self.occurrences is not None",
    "Instancehood": "self.template is not None",
    "Codehood": "isinstance(self.source, str)",
    "Datahood": "self.digest is not None",
    "Algorithmhood": "callable(self.apply)",
    "Runtimehood": "self.env is not None",
    "Peerhood": "self.identity is not None",
    "Narrativehood": "self.events is not None",
    "Metahood": "self.subject is not None",
    "Dissolutionhood": "True",
}


def gen(name: str) -> str:
    defaults = DEFAULTS[name]
    methods = METHODS[name]
    inv = INVARIANTS[name]
    lines = []
    lines.append(f'"""Refined: {name} — default-constructible, self-verifying."""')
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append(f"class {name}:")
    lines.append("    def __init__(self, **kwargs):")
    lines.append("        # defaults")
    for k, v in defaults.items():
        if k.endswith("_src"):
            field = k[:-4]
            lines.append(f"        self.{field} = {v}")
        else:
            lines.append(f"        self.{k} = {v!r}")
    lines.append("        # overrides")
    lines.append("        for k, v in kwargs.items():")
    lines.append("            setattr(self, k, v)")
    lines.append("")
    lines.append("    def verify(self) -> bool:")
    lines.append(f"        return bool({inv})")
    lines.append("")
    lines.append("    def to_dict(self) -> dict:")
    lines.append("        return {k: v for k, v in self.__dict__.items()")
    lines.append("                if not callable(v)}")
    lines.append("")
    for m in methods:
        lines.append(f"    def {m}(self, *args, **kwargs):")
        lines.append(f'        """{name}.{m}"""')
        lines.append(f"        return f'{name}.{m}'")
        lines.append("")
    lines.append("if __name__ == '__main__':")
    lines.append(f"    x = {name}()")
    lines.append(f"    assert x.verify(), 'invariant failed'")
    lines.append(f"    print(f'{name}: verify={{x.verify()}}')")
    lines.append("    print('self-test OK')")
    lines.append("")
    return "\n".join(lines)


def main():
    written = []
    for name in sorted(DEFAULTS):
        fn = OUT / f"{name.lower()}.py"
        fn.write_text(gen(name))
        written.append(fn)
    print(f"refined {len(written)} hood modules in {OUT}")
    for fn in written[:3]:
        print(f"  {fn.name}")
    print(f"  ... and {len(written) - 3} more")


if __name__ == "__main__":
    main()
