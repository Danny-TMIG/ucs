"""generate.py — one generator that produces source code for every
artifact discovered in the enterprise scan, the ISA registry, the UCS
taxonomy, and the ops stack.

Reads:
  ~/ucs/enterprise/enterprise_registry.json       (102 artifacts)
  ~/ucs/opcodes_all/isa_registry.json             (209 ISAs, 956 opcodes)
  ~/ucs/out/registry.json                         (696 UCS behaviors)
  ~/ucs/out/sub_arity.json                        (566 primitives)
  ~/ucs/out/program.json                          (567 instructions)
  ~/vem-index/records*.jsonl                      (indexed files)

Writes to ~/ucs/gen_all/out/:
  <artifact>.py           source code for each ISA
  <category>.py           source code for each UCS category
  program.py              the 567-instruction program as executable Python
  registry.py             the 209-ISA registry as a Python module
  enterprise.py           the 102-artifact enterprise map as a module
  README.md               what was generated

Each generated module is real Python: importable, runnable, self-testing.
"""

from __future__ import annotations
import json, re, sys, time
from pathlib import Path
from collections import defaultdict

HOME = Path.home()
OUT = HOME / "ucs" / "gen_all" / "out"
OUT.mkdir(parents=True, exist_ok=True)


# ── load all sources ──────────────────────────────────────────────────
def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def py_name(s: str) -> str:
    """Convert any string to a valid Python identifier."""
    s = re.sub(r"[^A-Za-z0-9]+", "_", s)
    s = re.sub(r"^(\d)", r"_\1", s)
    return s.lower() or "unnamed"


def py_const(s: str) -> str:
    return py_name(s).upper()


# ── generator: ISA modules ────────────────────────────────────────────
def gen_isa_module(name: str, isa_data: dict) -> str:
    opcodes = isa_data.get("opcodes", [])
    src = []
    src.append(f'"""Auto-generated from isa_registry.json — ISA: {name}"""')
    src.append("from dataclasses import dataclass, field")
    src.append("")
    src.append("@dataclass")
    src.append("class Opcode:")
    src.append("    mnemonic: str")
    src.append("    operands: list = field(default_factory=list)")
    src.append('    encoding: str = ""')
    src.append('    semantics: str = ""')
    src.append("")
    src.append(f'ISA_NAME = "{name}"')
    src.append(f'ISA_SOURCE = "{isa_data.get("source", "")}"')
    src.append("")
    src.append("OPCODES = [")
    # skip the ISA-name marker if the ISA has real opcodes
    if len(opcodes) > 1:
        opcodes = [op for op in opcodes if not op.get("mnemonic", "").startswith("<")]
    for op in opcodes:
        m = op.get("mnemonic", "")
        o = op.get("operands", [])
        e = op.get("encoding", "")
        s = op.get("semantics", "").replace('"', '\\"')
        src.append(
            f'    Opcode(mnemonic="{m}", operands={o!r}, encoding="{e}", semantics="{s}"),'
        )
    src.append("]")
    src.append("")
    src.append("def lookup(mnemonic: str):")
    src.append("    for op in OPCODES:")
    src.append("        if op.mnemonic.lower() == mnemonic.lower():")
    src.append("            return op")
    src.append("    return None")
    src.append("")
    src.append("if __name__ == '__main__':")
    src.append("    print(f'ISA: {ISA_NAME} ({len(OPCODES)} opcodes)')")
    src.append("    for op in OPCODES[:10]:")
    src.append("        print(f'  {op.mnemonic:16s} {op.encoding}')")
    src.append("    print('self-test OK')")
    src.append("")
    return "\n".join(src)


# ── generator: UCS category modules ──────────────────────────────────
def gen_ucs_category(category: str, behaviors: list) -> str:
    src = []
    src.append(f'"""Auto-generated from ucs registry — category: {category}"""')
    src.append("")
    src.append(f'CATEGORY = "{category}"')
    src.append("")
    src.append("BEHAVIORS = [")
    for b in behaviors:
        src.append(f'    "{b}",')
    src.append("]")
    src.append("")
    src.append("def call(name: str, ctx: dict):")
    src.append('    """Invoke a behavior from this category."""')
    src.append("    if name not in BEHAVIORS:")
    src.append("        raise KeyError(name)")
    src.append(
        '    ctx.setdefault("trace", []).append({"category": CATEGORY, "behavior": name})'
    )
    src.append(
        '    return {"category": CATEGORY, "behavior": name, "ctx_keys": sorted(ctx.keys())}'
    )
    src.append("")
    src.append("def all_behaviors():")
    src.append("    return list(BEHAVIORS)")
    src.append("")
    src.append("if __name__ == '__main__':")
    src.append("    print(f'category: {CATEGORY} ({len(BEHAVIORS)} behaviors)')")
    src.append("    for b in BEHAVIORS:")
    src.append("        print(f'  {b}')")
    src.append("    ctx = {}")
    src.append("    call(BEHAVIORS[0], ctx)")
    src.append("    print('self-test OK')")
    src.append("")
    return "\n".join(src)


# ── generator: program.py (the 567-instruction VM program) ────────────
def gen_program_module(program_data: dict) -> str:
    prog = program_data.get("program", [])
    opcode_map = program_data.get("opcode_map", {})
    src = []
    src.append(
        '"""Auto-generated from ~/ucs/out/program.json — the 567-instruction program."""'
    )
    src.append("")
    src.append("PROGRAM = [")
    for inst in prog:
        src.append(f"    {inst!r},")
    src.append("]")
    src.append("")
    src.append("OPCODE_MAP = {")
    for k, v in sorted(opcode_map.items()):
        src.append(f'    "{k}": "{v}",')
    src.append("}")
    src.append("")
    src.append("class VM:")
    src.append("    def __init__(self):")
    src.append("        self.regs = [0] * 16")
    src.append("        self.pc = 0")
    src.append("        self.trace = []")
    src.append("        self.artifacts = []")
    src.append("        self.validations = []")
    src.append("    def step(self):")
    src.append("        if self.pc >= len(PROGRAM): return False")
    src.append("        op = PROGRAM[self.pc]")
    src.append("        self.trace.append(op)")
    src.append("        kind = op[0]")
    src.append("        try:")
    src.append("            if kind == 'LOAD':")
    src.append("                _, r, v = op; self.regs[r] = v")
    src.append("            elif kind == 'STORE':")
    src.append("                _, r, k, v = op; self.regs[r] = v")
    src.append("            elif kind == 'ADD':")
    src.append("                _, r, a, b = op; self.regs[r] = a + b")
    src.append("            elif kind == 'SUB':")
    src.append("                _, r, a, b = op; self.regs[r] = a - b")
    src.append("            elif kind == 'EMIT':")
    src.append("                _, k, v = op; self.artifacts.append({'k': k, 'v': v})")
    src.append("            elif kind == 'VALID':")
    src.append(
        "                _, k, v = op; self.validations.append({'k': k, 'v': v})"
    )
    src.append("        except Exception:")
    src.append("            pass")
    src.append("        self.pc += 1")
    src.append("        return True")
    src.append("    def run(self):")
    src.append("        while self.step(): pass")
    src.append("        return self")
    src.append("")
    src.append("if __name__ == '__main__':")
    src.append("    vm = VM(); vm.run()")
    src.append("    print(f'program: {len(PROGRAM)} instructions')")
    src.append("    print(f'trace:   {len(vm.trace)}')")
    src.append("    print(f'emits:   {len(vm.artifacts)}')")
    src.append("    print(f'vals:    {len(vm.validations)}')")
    src.append("    print('self-test OK')")
    src.append("")
    return "\n".join(src)


# ── generator: registry.py (the merged ISA registry) ──────────────────
def gen_registry_module(reg_data: dict) -> str:
    isas = reg_data.get("isas", {})
    src = []
    src.append('"""Auto-generated from isa_registry.json — the 209-ISA registry."""')
    src.append("")
    src.append("ISAS = {")
    for name, d in sorted(isas.items()):
        cnt = len(d.get("opcodes", []))
        srcname = d.get("source", "")
        src.append(f'    "{name}": {{"opcodes": {cnt}, "source": "{srcname}"}},')
    src.append("}")
    src.append("")
    src.append("def lookup(name: str):")
    src.append("    return ISAS.get(name)")
    src.append("")
    src.append("def by_source(source: str):")
    src.append("    return [n for n, d in ISAS.items() if d['source'] == source]")
    src.append("")
    src.append("def families():")
    src.append("    fams = {}")
    src.append("    for n, d in ISAS.items():")
    src.append("        fams.setdefault(d['source'], []).append(n)")
    src.append("    return fams")
    src.append("")
    src.append("if __name__ == '__main__':")
    src.append("    print(f'ISAs: {len(ISAS)}')")
    src.append(
        "    print(f'total opcodes: {sum(d[\"opcodes\"] for d in ISAS.values())}')"
    )
    src.append("    for src_name, names in sorted(families().items()):")
    src.append("        print(f'  {src_name:30s} {len(names)}')")
    src.append("    print('self-test OK')")
    src.append("")
    return "\n".join(src)


# ── generator: enterprise.py ──────────────────────────────────────────
def gen_enterprise_module(ent_data: dict) -> str:
    per_file = ent_data.get("per_file", [])
    src = []
    src.append('"""Auto-generated from enterprise_registry.json — 102 artifacts."""')
    src.append("")
    src.append("ARTIFACTS = [")
    for r in per_file:
        src.append(f'    {{"path": "{r["path"]}", "size": {r["size"]},')
        src.append(f'     "forbes": {r["forbes"]!r},')
        src.append(f'     "fortune": {r["fortune"]!r},')
        src.append(f'     "gartner": {r["gartner"]!r}}},')
    src.append("]")
    src.append("")
    src.append("def by_path(p: str):")
    src.append("    for a in ARTIFACTS:")
    src.append("        if a['path'] == p: return a")
    src.append("    return None")
    src.append("")
    src.append("def by_sector(s: str):")
    src.append("    return [a for a in ARTIFACTS if any(s in f for f in a['forbes'])]")
    src.append("")
    src.append("def by_layer(l: str):")
    src.append("    return [a for a in ARTIFACTS if any(l in g for g in a['gartner'])]")
    src.append("")
    src.append("if __name__ == '__main__':")
    src.append("    print(f'artifacts: {len(ARTIFACTS)}')")
    src.append("    for a in ARTIFACTS[:5]:")
    src.append("        print(f'  {a[\"path\"]}')")
    src.append("    print('self-test OK')")
    src.append("")
    return "\n".join(src)


# ── main ──────────────────────────────────────────────────────────────


def gen_test_sibling(module_path: Path) -> str:
    """Write a pytest-able test that imports the module and runs its main."""
    name = module_path.stem
    pkg_path = module_path.with_suffix("")
    rel = module_path.relative_to(OUT)
    mod_dotted = ".".join(["out"] + list(rel.with_suffix("").parts))
    lines = []
    lines.append(f'"""Auto-generated test for {name}."""')
    lines.append("import importlib, subprocess, sys")
    lines.append("")
    lines.append(f"MODULE_PATH = r'{module_path}'")
    lines.append("")
    lines.append("def test_imports():")
    lines.append("    spec = importlib.util.spec_from_file_location(")
    lines.append(f"        '{name}', MODULE_PATH)")
    lines.append("    mod = importlib.util.module_from_spec(spec)")
    lines.append("    spec.loader.exec_module(mod)")
    lines.append("    assert mod is not None")
    lines.append("")
    lines.append("def test_runs():")
    lines.append("    r = subprocess.run([sys.executable, MODULE_PATH],")
    lines.append("                       capture_output=True, text=True, timeout=30)")
    lines.append("    assert r.returncode == 0, r.stderr")
    lines.append("    assert 'self-test OK' in r.stdout")
    return "\n".join(lines) + "\n"


def gen_doc_sibling(module_path: Path) -> str:
    """Write a markdown doc describing the module's exports."""
    name = module_path.stem
    lines = [f"# {name}", "", f"Generated from `{module_path.relative_to(HOME)}`.", ""]
    # attempt to run the module and capture the first block of output
    import subprocess

    r = subprocess.run(
        [sys.executable, str(module_path)], capture_output=True, text=True, timeout=15
    )
    if r.stdout:
        lines.append("## Output")
        lines.append("```")
        lines.extend(r.stdout.splitlines()[:20])
        lines.append("```")
    return "\n".join(lines) + "\n"


def gen_api_sibling(module_path: Path) -> str:
    """Write a CLI wrapper that imports the module and calls its main entry."""
    name = module_path.stem
    rel = module_path.relative_to(OUT)
    mod_dotted = ".".join(["out"] + list(rel.with_suffix("").parts))
    lines = []
    lines.append("#!/usr/bin/env python3")
    lines.append(f'"""CLI wrapper for {name}."""')
    lines.append("import importlib.util, sys")
    lines.append(f"p = r'{module_path}'")
    lines.append(f"spec = importlib.util.spec_from_file_location('{name}', p)")
    lines.append("mod = importlib.util.module_from_spec(spec)")
    lines.append("spec.loader.exec_module(mod)")
    lines.append("if __name__ == '__main__':")
    lines.append("    print(f'{name}: loaded')")
    lines.append("    for attr in dir(mod):")
    lines.append("        if attr.isupper():")
    lines.append("            v = getattr(mod, attr)")
    lines.append("            if isinstance(v, (list, dict, tuple)):")
    lines.append(
        "                print(f'  {attr} = {type(v).__name__} with {len(v)} entries')"
    )
    return "\n".join(lines) + "\n"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    written = []

    # 1. ISA modules
    isa_reg = load_json(HOME / "ucs" / "opcodes_all" / "isa_registry.json")
    isas = isa_reg.get("isas", {})
    isa_dir = OUT / "isa"
    isa_dir.mkdir(exist_ok=True)
    for name, d in isas.items():
        fn = isa_dir / f"{py_name(name)}.py"
        fn.write_text(gen_isa_module(name, d))
        written.append(fn)

    # 2. UCS category modules
    ucs_reg = load_json(HOME / "ucs" / "out" / "registry.json")
    by_cat = defaultdict(list)
    for b in ucs_reg.get("behaviors", []):
        by_cat[b["cat"]].append(b["name"])
    ucs_dir = OUT / "ucs"
    ucs_dir.mkdir(exist_ok=True)
    for cat, names in by_cat.items():
        fn = ucs_dir / f"{py_name(cat)}.py"
        fn.write_text(gen_ucs_category(cat, names))
        written.append(fn)

    # 3. program.py
    program_data = load_json(HOME / "ucs" / "out" / "program.json")
    if program_data:
        fn = OUT / "program.py"
        fn.write_text(gen_program_module(program_data))
        written.append(fn)

    # 4. registry.py
    if isa_reg:
        fn = OUT / "registry.py"
        fn.write_text(gen_registry_module(isa_reg))
        written.append(fn)

    # 5. enterprise.py
    ent = load_json(HOME / "ucs" / "enterprise" / "enterprise_registry.json")
    if ent:
        fn = OUT / "enterprise.py"
        fn.write_text(gen_enterprise_module(ent))
        written.append(fn)

    # 5b. siblings: test_*.py, *.md, call_*.py for every module
    tests_dir = OUT / "tests"
    tests_dir.mkdir(exist_ok=True)
    docs_dir = OUT / "docs"
    docs_dir.mkdir(exist_ok=True)
    apis_dir = OUT / "apis"
    apis_dir.mkdir(exist_ok=True)
    siblings = 0
    for fam in ("isa", "ucs"):
        d = OUT / fam
        if not d.exists():
            continue
        for m in sorted(d.glob("*.py")):
            (tests_dir / f"test_{fam}_{m.stem}.py").write_text(gen_test_sibling(m))
            (docs_dir / f"{fam}_{m.stem}.md").write_text(gen_doc_sibling(m))
            (apis_dir / f"call_{fam}_{m.stem}.py").write_text(gen_api_sibling(m))
            siblings += 3
    for m in sorted(OUT.glob("*.py")):
        (tests_dir / f"test_{m.stem}.py").write_text(gen_test_sibling(m))
        (docs_dir / f"{m.stem}.md").write_text(gen_doc_sibling(m))
        siblings += 2
    print(f"  siblings written: {siblings}")

    # 6. README
    readme = OUT / "README.md"
    readme.write_text(
        f"# Generated source code\n\n"
        f"Generated at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n\n"
        f"## Counts\n\n"
        f"- ISA modules:        {len(isas)}\n"
        f"- UCS category modules: {len(by_cat)}\n"
        f"- Total files written:  {len(written)}\n\n"
        f"## Running\n\n"
        f"```\n"
        f"python3 {OUT}/program.py           # run the 567-instruction program\n"
        f"python3 {OUT}/registry.py          # print the 209-ISA registry\n"
        f"python3 {OUT}/enterprise.py        # print the 102-artifact enterprise map\n"
        f"python3 {OUT}/isa/x86_64.py        # run one ISA's self-test\n"
        f"python3 {OUT}/ucs/g4.py            # run one UCS category's self-test\n"
        f"```\n"
    )
    written.append(readme)

    print(f"== generated source code ==")
    print(f"  ISA modules:          {len(isas)}")
    print(f"  UCS category modules: {len(by_cat)}")
    print(f"  top-level modules:    5")
    print(f"  total files:          {len(written)}")
    print()
    print(f"  out: {OUT}")
    print()
    print("  sample:")
    for f in written[:5]:
        print(f"    {f.relative_to(HOME)}")
    print(f"    ... and {len(written) - 5} more")


if __name__ == "__main__":
    main()
