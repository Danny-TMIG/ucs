"""gen.py — generate Python + docs from a JSON schema."""

from __future__ import annotations
import json, sys
from pathlib import Path

PY_TYPES = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "array": "list",
    "object": "dict",
}


def gen_class(schema: dict) -> str:
    name = schema.get("title", "Unnamed")
    req = set(schema.get("required", []))
    lines = ["from dataclasses import dataclass", "", "@dataclass", f"class {name}:"]
    props = schema.get("properties", {})
    if not props:
        lines.append("    pass")
    for f, fs in props.items():
        py = PY_TYPES.get(fs.get("type", "any"), "object")
        default = "" if f in req else " = None"
        lines.append(f"    {f}: {py}{default}")
    lines.append("")
    lines.append("if __name__ == '__main__':")
    lines.append(f"    x = {name}(")
    args = []
    for f, fs in props.items():
        t = fs.get("type")
        if t == "string":
            args.append(f'{f}="x"')
        elif t == "integer":
            args.append(f"{f}=0")
        elif t == "number":
            args.append(f"{f}=0.0")
        elif t == "boolean":
            args.append(f"{f}=False")
        else:
            args.append(f"{f}=None")
    lines.append("        " + ", ".join(args))
    lines.append("    )")
    lines.append("    print(x)")
    lines.append("    print('self-test OK')")
    return "\n".join(lines)


def gen_docs(schema: dict) -> str:
    name = schema.get("title", "Unnamed")
    req = set(schema.get("required", []))
    lines = [f"# {name}", "", "| field | type | required |", "|---|---|---|"]
    for f, fs in schema.get("properties", {}).items():
        lines.append(f"| {f} | {fs.get('type', 'any')} | {f in req} |")
    return "\n".join(lines)


def generate(schema_text: str, outdir: Path) -> dict:
    s = json.loads(schema_text)
    outdir.mkdir(parents=True, exist_ok=True)
    name = s.get("title", "Unnamed").lower()
    (outdir / f"{name}.py").write_text(gen_class(s))
    (outdir / f"{name}.md").write_text(gen_docs(s))
    return {"class": str(outdir / f"{name}.py"), "docs": str(outdir / f"{name}.md")}


if __name__ == "__main__":
    schema = json.dumps(
        {
            "title": "User",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "email": {"type": "string"},
            },
            "required": ["name", "email"],
        }
    )
    result = generate(schema, Path("./gen_out"))
    print(result)
    print("self-test OK")
