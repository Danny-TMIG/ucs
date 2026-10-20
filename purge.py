#!/usr/bin/env python3
"""purge.py - classify and clean stubs/faux/holders. No quote collisions."""

from __future__ import annotations
import ast, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

HOME = Path.home()
UC = HOME / "ucs"
TRASH = UC / "_trash"

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

# quote starters built from chr() so no triple-quote appears in this file
DQ3 = chr(34) * 3
SQ3 = chr(39) * 3
QUOTE_STARTERS = (DQ3, SQ3, "r" + DQ3, "r" + SQ3)


def w(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def classify(p):
    try:
        src = p.read_text(errors="ignore")
    except OSError:
        return {"class": "UNREADABLE"}
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return {"class": "SYNTAX_ERROR", "detail": str(e)[:80]}

    empty_funcs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            real = [
                s
                for s in node.body
                if not (
                    isinstance(s, ast.Expr)
                    and isinstance(s.value, ast.Constant)
                    and isinstance(s.value.value, str)
                )
            ]
            if not real:
                empty_funcs.append((node.name, node.lineno))
                continue
            if len(real) == 1:
                s = real[0]
                if isinstance(s, ast.Pass):
                    empty_funcs.append((node.name, node.lineno))
                elif isinstance(s, ast.Return) and s.value is None:
                    empty_funcs.append((node.name, node.lineno))
                elif (
                    isinstance(s, ast.Return)
                    and isinstance(s.value, ast.Constant)
                    and s.value.value is None
                ):
                    empty_funcs.append((node.name, node.lineno))
                elif (
                    isinstance(s, ast.Expr)
                    and isinstance(s.value, ast.Constant)
                    and s.value.value is Ellipsis
                ):
                    empty_funcs.append((node.name, node.lineno))

    faux = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for handler in node.handlers:
                t = handler.type
                if t is None or (
                    isinstance(t, ast.Name) and t.id in ("Exception", "BaseException")
                ):
                    real = [
                        s
                        for s in handler.body
                        if not (
                            isinstance(s, ast.Expr)
                            and isinstance(s.value, ast.Constant)
                        )
                    ]
                    if not real or all(isinstance(s, ast.Pass) for s in real):
                        faux.append(handler.lineno)

    HOLDERS = {
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
    }
    holders = []
    for node in ast.walk(tree):
        name = None
        if isinstance(node, ast.FunctionDef):
            name = node.name
        elif isinstance(node, ast.Name):
            name = node.id
        elif isinstance(node, ast.arg):
            name = node.arg
        if name and name.lower() in HOLDERS:
            holders.append(name)

    n_funcs = sum(
        1
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    if n_funcs and len(empty_funcs) == n_funcs and n_funcs >= 3:
        cls = "STUB"
    elif faux and n_funcs and len(empty_funcs) / n_funcs > 0.5:
        cls = "FAUX"
    elif len(set(holders)) >= 2:
        cls = "HOLDER"
    elif empty_funcs:
        cls = "PARTIAL"
    else:
        cls = "REAL"
    return {
        "class": cls,
        "functions": n_funcs,
        "empty_funcs": empty_funcs,
        "faux_excepts": faux,
        "holders": list(set(holders))[:10],
    }


def rewrite_stub(src, empty_funcs, faux_excepts, holders):
    changes = []
    lines = src.splitlines(keepends=True)

    for name, lineno in sorted(empty_funcs, key=lambda t: -t[1]):
        i = lineno - 1
        if i < 0 or i >= len(lines):
            continue
        j = i + 1
        # skip leading docstring
        if j < len(lines):
            stripped = lines[j].lstrip()
            matched_quote = None
            for q in QUOTE_STARTERS:
                if stripped.startswith(q):
                    matched_quote = q
                    break
            if matched_quote:
                close = stripped.find(matched_quote, len(matched_quote))
                if close == -1:
                    j += 1
                    while j < len(lines) and matched_quote[:3] not in lines[j]:
                        j += 1
                    j += 1
                else:
                    j += 1
        if j < len(lines):
            indent = len(lines[j]) - len(lines[j].lstrip())
            indent_s = " " * indent
            new_body = (
                indent_s
                + "raise NotImplementedError("
                + chr(10)
                + indent_s
                + "    "
                + chr(34)
                + name
                + " is not implemented"
                + chr(34)
                + ")"
                + chr(10)
            )
            fn_indent = len(lines[i]) - len(lines[i].lstrip())
            k = j + 1
            while k < len(lines):
                if lines[k].strip() == "":
                    k += 1
                    continue
                if len(lines[k]) - len(lines[k].lstrip()) <= fn_indent:
                    break
                k += 1
            lines[j:k] = [new_body]
            changes.append("raised " + name + " at line " + str(lineno))

    src = "".join(lines)

    pat = re.compile(
        chr(10)
        + r"([ \t]*)except[ \t]*(?:Exception|BaseException)?[ \t]*:"
        + r"[ \t]*"
        + chr(10)
        + r"([ \t]*)pass\b"
    )
    for _ in range(len(faux_excepts)):
        new_src, n = pat.subn(
            chr(10) + r"\1except Exception as _e:" + chr(10) + r"\2raise", src, count=1
        )
        if n:
            src = new_src
            changes.append("faux except replaced")

    for old in sorted(set(holders), key=lambda x: -len(x)):
        pat = re.compile(r"\b" + re.escape(old) + r"\b")
        new_src, n = pat.subn("value", src)
        if n:
            src = new_src
            changes.append("renamed " + old + " -> value (" + str(n) + " hits)")

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
            out[str(p.relative_to(HOME))] = classify(p)
    return out


def apply_all(scan, delete_files):
    stats = {
        "files_touched": 0,
        "files_deleted": 0,
        "functions_raised": 0,
        "faux_fixed": 0,
        "holders_renamed": 0,
        "changes": [],
    }
    for rel, info in scan.items():
        if info["class"] not in ("STUB", "FAUX", "HOLDER", "PARTIAL"):
            continue
        p = HOME / rel
        if delete_files and info["class"] == "STUB":
            TRASH.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), str(TRASH / rel.replace("/", "_")))
            stats["files_deleted"] += 1
            stats["changes"].append("deleted " + rel)
            continue
        try:
            src = p.read_text()
        except OSError:
            continue
        new_src, changes = rewrite_stub(
            src,
            info.get("empty_funcs", []),
            info.get("faux_excepts", []),
            info.get("holders", []),
        )
        if new_src != src:
            w(p, new_src)
            stats["files_touched"] += 1
            stats["changes"].extend(rel + ": " + c for c in changes)
            for c in changes:
                if c.startswith("raised"):
                    stats["functions_raised"] += 1
                if c.startswith("faux"):
                    stats["faux_fixed"] += 1
                if c.startswith("renamed"):
                    stats["holders_renamed"] += 1
    return stats


def verify_all():
    checks = [
        ("resolve", UC / "resolve.py"),
        ("everything", UC / "everything.py"),
        ("hood_chain", UC / "hood_compilers" / "chain" / "verify.py"),
        ("allwares", UC / "allwares" / "verify.py"),
    ]
    results = {}
    for name, p in checks:
        if not p.exists():
            results[name] = {"rc": -1, "msg": "missing"}
            continue
        try:
            r = subprocess.run(
                [sys.executable, str(p)], capture_output=True, text=True, timeout=120
            )
            last = r.stdout.strip().splitlines()[-1:] or [""]
            results[name] = {"rc": r.returncode, "msg": last[0][:80]}
        except Exception as e:
            results[name] = {"rc": -1, "msg": str(e)[:80]}
    return results


def main():
    if "--report" in sys.argv or len(sys.argv) == 1:
        print("[scan]")
        scan = scan_all()
        by = {}
        for info in scan.values():
            by[info["class"]] = by.get(info["class"], 0) + 1
        for c, n in sorted(by.items(), key=lambda kv: -kv[1]):
            print("  " + c.ljust(14) + " " + str(n))
        out = UC / "purge_scan.json"
        out.write_text(
            json.dumps(
                {
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "by_class": by,
                    "files": scan,
                },
                indent=2,
            )
        )
        print("  report: " + str(out))

    if "--apply" in sys.argv or "--full" in sys.argv:
        print("[apply]")
        scan = scan_all()
        stats = apply_all(scan, delete_files=False)
        print("  files touched:      " + str(stats["files_touched"]))
        print("  functions raised:   " + str(stats["functions_raised"]))
        print("  faux excepts fixed: " + str(stats["faux_fixed"]))
        print("  holders renamed:    " + str(stats["holders_renamed"]))

    if "--delete" in sys.argv:
        print("[delete]")
        scan = scan_all()
        stats = apply_all(scan, delete_files=True)
        print("  files deleted:      " + str(stats["files_deleted"]))
        print("  trash:              " + str(TRASH))

    if "--verify" in sys.argv or "--full" in sys.argv:
        print("[verify]")
        results = verify_all()
        for name, r in results.items():
            status = "OK  " if r["rc"] == 0 else "FAIL"
            print("  " + status + "  " + name.ljust(14) + "  " + r["msg"])


if __name__ == "__main__":
    main()
