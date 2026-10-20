import ast, importlib.util, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOCAL_TOP = {"spec","bench","auth","ci","hats","enterprise","tools","pipe"}


def _rel(path):
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _stdlib(name):
    top = name.split(".")[0]
    if top in ("", "__future__"):
        return True
    try:
        return importlib.util.find_spec(top) is not None
    except (ModuleNotFoundError, ValueError):
        return False


def _local(name, importer):
    parts = name.split(".")
    candidates = [
        importer.parent / pathlib.Path(*parts).with_suffix(".py"),
        importer.parent / pathlib.Path(*parts) / "__init__.py",
        importer.parent / f"{parts[-1]}.py",
        ROOT / pathlib.Path(*parts).with_suffix(".py"),
        ROOT / pathlib.Path(*parts) / "__init__.py",
        ROOT / f"{parts[-1]}.py",
    ]
    for d in ("spec", "bench", "auth", "ci", "hats", "enterprise", "tools"):
        candidates.append(ROOT / d / f"{parts[-1]}.py")
        candidates.append(ROOT / d / pathlib.Path(*parts).with_suffix(".py"))
    for c in candidates:
        if c.exists():
            return c
    return None


def _exports(path):
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return set()
    n = set()
    for x in tree.body:
        if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            n.add(x.name)
        elif isinstance(x, ast.Assign):
            for t in x.targets:
                if isinstance(t, ast.Name):
                    n.add(t.id)
        elif isinstance(x, (ast.Import, ast.ImportFrom)):
            for a in x.names:
                n.add(a.asname or a.name.split(".")[0])
    return n


def _guarded(tree, target):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        if not any(isinstance(h.type, ast.Name) and h.type.id in ("ImportError", "Exception")
                   for h in node.handlers if h.type is not None):
            continue
        for c in ast.walk(node):
            if c is target:
                return True
    return False


def check_file(path):
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError as e:
        return [f"{_rel(path)}: syntax: {e}"]
    errs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if _guarded(tree, node):
                continue
            if _stdlib(node.module):
                continue
            t = _local(node.module, path)
            if t is None:
                errs.append(f"{_rel(path)}:{node.lineno}: from {node.module} not found")
                continue
            exp = _exports(t)
            for a in node.names:
                if a.name == "*":
                    continue
                if a.name not in exp:
                    errs.append(f"{_rel(path)}:{node.lineno}: {node.module} doesn't export {a.name}")
        elif isinstance(node, ast.Import):
            if _guarded(tree, node):
                continue
            for a in node.names:
                if _stdlib(a.name):
                    continue
                if _local(a.name, path) is None:
                    errs.append(f"{_rel(path)}:{node.lineno}: import {a.name} not found")
    return errs


def discover():
    out = []
    for d in LOCAL_TOP:
        b = ROOT / d
        if not b.exists():
            continue
        for f in b.rglob("*.py"):
            if "__pycache__" in f.parts:
                continue
            out.append(f)
    return out


def main():
    errs = []
    for f in discover():
        errs.extend(check_file(f))
    if errs:
        print(f"{len(errs)} errors:")
        for e in errs:
            print(f"  {e}")
        return 1
    print(f"import-check OK: {len(discover())} files")
    return 0


if __name__ == "__main__":
    import tempfile
    t = pathlib.Path(tempfile.mkdtemp())
    (t / "spec").mkdir()
    (t / "spec" / "serve.py").write_text("def generate(x): return x\n")
    (t / "spec" / "user.py").write_text("import serve\n")
    assert check_file(t / "spec" / "user.py") == []
    bad = t / "bad.py"
    bad.write_text("import not_a_real_module_xyz\n")
    assert check_file(bad)
    sys.exit(main())
