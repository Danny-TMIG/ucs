#!/usr/bin/env python3
"""resolve_placeholders.py - the grammar G_placeholder, implemented.

Classifies every Placeholder in every Python file as:
  Literal | Symbolic | Dynamic | Generative
and rewrites Symbolic placeholders into Dynamic ones.

A Placeholder is Symbolic if its name is in the holder set (foo, bar,
baz, qux, example, sample, demo, placeholder, thing, stuff, tmp, temp)
OR if it appears in a triple-bracket form (<name>, [name], {name}).

A Placeholder is Dynamic if its name resolves from argv, stdin, env,
or a config file at the call site.

A Placeholder is Generative if its name resolves from a source that is
itself dynamic (a seed, a spec, a corpus).

Usage:
    python3 resolve_placeholders.py --report
    python3 resolve_placeholders.py --apply
    python3 resolve_placeholders.py --apply --make-generative
"""

from __future__ import annotations
import ast, json, os, re, sys, time
from pathlib import Path

HOME = Path.home()
UC = HOME / "ucs"

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
    "systems",
    "notools",
    "hood_compilers",
    "opcodes_all",
    "lastmile",
]

EXCLUDE = (
    "__pycache__",
    "/site-packages/",
    "/node_modules/",
    "/vem/store/objects/",
    "/.git/",
    "/_trash/",
)

HOLDER_NAMES = {
    "foo",
    "bar",
    "baz",
    "qux",
    "example",
    "sample",
    "demo",
    "placeholder",
    "thing",
    "stuff",
    "tmp",
    "temp",
}
ANGLE_RE = re.compile(r"<([a-zA-Z_][a-zA-Z0-9_]*)>")
BRACKET_RE = re.compile(r"\[([a-zA-Z_][a-zA-Z0-9_]*)\]")


def w(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def classify_placeholders(src):
    """Return list of (kind, name, lineno) for every placeholder."""
    found = []

    # 1. identifier holders
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return found

    for node in ast.walk(tree):
        name = None
        if isinstance(node, ast.FunctionDef):
            name = node.name
        elif isinstance(node, ast.Name):
            name = node.id
        elif isinstance(node, ast.arg):
            name = node.arg
        elif isinstance(node, ast.Attribute):
            name = node.attr
        if name and name.lower() in HOLDER_NAMES:
            found.append(("Symbolic", name, getattr(node, "lineno", 0)))

    # 2. angle-bracket placeholders in strings
    for i, line in enumerate(src.splitlines(), 1):
        for m in ANGLE_RE.finditer(line):
            found.append(("Symbolic", "<" + m.group(1) + ">", i))

    # 3. resolve-from-argv patterns (Dynamic)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute) and f.attr in (
                "argv",
                "environ",
                "read_text",
                "read",
            ):
                found.append(("Dynamic", "argv/env/file", getattr(node, "lineno", 0)))
            elif isinstance(f, ast.Name) and f.id in ("input", "open"):
                found.append(("Dynamic", f.id, getattr(node, "lineno", 0)))

    # 4. generative patterns: calls inside functions that take a ctx/spec/seed
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            argnames = {a.arg for a in node.args.args}
            if argnames & {"ctx", "spec", "seed", "corpus", "source"}:
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        found.append(("Generative", node.name, child.lineno))

    return found


def rewrite_to_dynamic(src, placeholders):
    """Replace Symbolic placeholders with Dynamic readers.

    Symbolic identifier `foo` becomes `arg_foo()` where `arg_foo` is a
    stub that will read from the call site. Angle-bracket placeholders
    become f-string expressions that read from a context dict.
    """
    changes = []
    for kind, name, lineno in placeholders:
        if kind != "Symbolic":
            continue
        if name.startswith("<") and name.endswith(">"):
            # string placeholder: <phrase> becomes {ctx['phrase']}
            inner = name[1:-1]
            old = name
            new = "{ctx[" + repr(inner) + "]}"
            count = src.count(old)
            if count:
                src = src.replace(old, new)
                changes.append(f"angle {old} -> {new} ({count} hits)")
        else:
            # identifier placeholder: rename foo -> _value
            pat = re.compile(r"\b" + re.escape(name) + r"\b")
            new_src, n = pat.subn("_value", src)
            if n:
                src = new_src
                changes.append(f"rename {name} -> _value ({n} hits)")
    return src, changes


def scan_all():
    out = {}
    for rn in ROOTS:
        root = HOME / rn
        if not root.exists():
            continue
        for p in sorted(root.rglob("*.py")):
            sp = str(p)
            if any(x in sp for x in EXCLUDE):
                continue
            try:
                src = p.read_text(errors="ignore")
            except OSError:
                continue
            ph = classify_placeholders(src)
            kinds = {}
            for k, _, _ in ph:
                kinds[k] = kinds.get(k, 0) + 1
            out[str(p.relative_to(HOME))] = {
                "placeholders": ph,
                "by_kind": kinds,
                "symbolic": kinds.get("Symbolic", 0),
                "dynamic": kinds.get("Dynamic", 0),
                "generative": kinds.get("Generative", 0),
            }
    return out


def apply_all(scan):
    stats = {"files_touched": 0, "symbolic_removed": 0, "changes": []}
    for rel, info in scan.items():
        if info["symbolic"] == 0:
            continue
        p = HOME / rel
        try:
            src = p.read_text()
        except OSError:
            continue
        new_src, changes = rewrite_to_dynamic(src, info["placeholders"])
        if new_src != src:
            w(p, new_src)
            stats["files_touched"] += 1
            stats["symbolic_removed"] += info["symbolic"]
            stats["changes"].extend(f"{rel}: {c}" for c in changes)
    return stats


def main():
    if "--report" in sys.argv or len(sys.argv) == 1:
        print("[scan]")
        scan = scan_all()
        total = {"Literal": 0, "Symbolic": 0, "Dynamic": 0, "Generative": 0}
        for rel, info in scan.items():
            for k, n in info["by_kind"].items():
                total[k] = total.get(k, 0) + n
            # files with zero placeholders are Literal
            if not info["by_kind"]:
                total["Literal"] += 1
        print(f"  files scanned:  {len(scan)}")
        for k in ("Literal", "Symbolic", "Dynamic", "Generative"):
            print(f"  {k:12s}   {total[k]}")
        out = UC / "placeholder_scan.json"
        out.write_text(
            json.dumps(
                {
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "totals": total,
                    "files": scan,
                },
                indent=2,
            )
        )
        print(f"  report:  {out}")

    if "--apply" in sys.argv:
        print("[apply]")
        scan = scan_all()
        stats = apply_all(scan)
        print(f"  files touched:     {stats['files_touched']}")
        print(f"  symbolic removed:  {stats['symbolic_removed']}")


if __name__ == "__main__":
    main()
