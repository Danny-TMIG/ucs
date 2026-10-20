#!/usr/bin/env python3
"""content-checks.py — content-level gates the shell scaffold cannot see.

R1 subprocess.run must have timeout=
R2 open() must be inside a with-block
R3 no bare except:
R4 every module __main__ has a negative test (try/except with assert)
R5 assertions use == with a literal, not `in` for exact-value checks
"""
import ast, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

def check_file(path):
    src = pathlib.Path(path).read_text()
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        return [f"{path}: syntax error: {e}"]
    errs = []
    for node in ast.walk(tree):
        # R1
        if isinstance(node, ast.Call):
            f = node.func
            name = None
            if isinstance(f, ast.Attribute): name = f.attr
            elif isinstance(f, ast.Name): name = f.id
            if name == "run" and any(isinstance(a, ast.Attribute) and a.attr == "subprocess" for a in []):
                pass
            if name == "run" and isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == "subprocess":
                if not any(kw.arg == "timeout" for kw in node.keywords):
                    errs.append(f"{path}:{node.lineno}: subprocess.run missing timeout=")
        # R2
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id == "open":
                parent_is_with = False
                # walk parents is not trivial in ast; use a soft rule: warn if source line before has no "with "
                line = src.splitlines()[node.lineno - 1]
                if "with " not in line and "with " not in src.splitlines()[max(0, node.lineno - 2)]:
                    errs.append(f"{path}:{node.lineno}: open() not inside with")
        # R3
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                errs.append(f"{path}:{node.lineno}: bare except:")
    # R4
    if "__main__" in src:
        main_src = src.split('if __name__')[1] if 'if __name__' in src else ""
        # negative test forms: try/except, pytest.raises, or an explicit assert-not
        has_neg = ("except" in main_src
                   or "pytest.raises" in main_src
                   or "assert not " in main_src
                   or "raise SystemExit" in main_src)
        if not has_neg:
            errs.append(f"{path}: __main__ has no negative test (try/except, assert-not, or SystemExit)")
    # R5
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            t = node.test
            if isinstance(t, ast.Compare) and any(isinstance(op, ast.In) for op in t.ops):
                # Flag only if the container is a 1-element list/tuple or a bare string,
                # where `==` would be clearer. Multi-member set membership is legitimate.
                right = t.comparators[0] if t.comparators else None
                if isinstance(right, (ast.List, ast.Tuple)) and len(right.elts) == 1:
                    errs.append(f"{path}:{node.lineno}: assert uses `in` on 1 element — use ==")
                elif isinstance(right, ast.Constant) and isinstance(right.value, str):
                    errs.append(f"{path}:{node.lineno}: assert uses `in` on a string — use ==")
    return errs

def main(argv):
    targets = argv[1:] or [str(p) for p in (ROOT / "spec").glob("*.py")]
    all_errs = []
    for t in targets:
        all_errs.extend(check_file(t))
    if all_errs:
        print("\n".join(all_errs))
        return 1
    print(f"content OK ({len(targets)} files)")
    return 0

if __name__ == "__main__":
    # R4: this file must itself have a negative test in __main__.
    # Negative test: check_file on a known-bad source must return errors.
    import tempfile
    bad = "def f():\n    import subprocess\n    subprocess.run(['echo'])\n"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(bad)
        bad_path = f.name
    try:
        errs = check_file(bad_path)
        assert len(errs) > 0, "check_file should flag subprocess.run without timeout"
    finally:
        pathlib.Path(bad_path).unlink()
    sys.exit(main(sys.argv))
