import json, os, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)
src = open(os.path.join(ROOT, "spec.yaml")).read()
entity = "Record"
fields = []
cur = None
for line in src.splitlines():
    s = line.strip()
    if s.startswith("- name:"):
        cur = {"name": s.split(":", 1)[1].strip()}
        fields.append(cur)
    elif s.startswith("type:") and cur is not None and "type" not in cur:
        cur["type"] = s.split(":", 1)[1].strip()
    elif s.startswith("required:") and cur is not None:
        cur["required"] = s.split(":", 1)[1].strip()
    elif s.startswith("entity:"):
        entity = s.split(":", 1)[1].strip()

py = ["from dataclasses import dataclass", "", "@dataclass", f"class {entity}:"]
ts = [f"export interface {entity} {{"]
go = ["package main", "", f"type {entity} struct {{"]
props = {}
for f in fields:
    p, _, _ = f["type"], 0, 0
    pt = {"int": "int", "str": "str", "float": "float"}.get(f["type"], "object")
    py.append(
        f"    {f['name']}: {pt}" + ("" if f.get("required") == "true" else " = None")
    )
    tt = {"int": "number", "str": "string"}.get(f["type"], "unknown")
    ts.append(f"  {f['name']}{'' if f.get('required') == 'true' else '?'}: {tt};")
    gt = {"int": "int", "str": "string"}.get(f["type"], "interface{}")
    go.append(f'    {f["name"][0].upper() + f["name"][1:]} {gt} `json:"{f["name"]}"`')
    props[f["name"]] = {
        "type": {"int": "integer", "str": "string"}.get(f["type"], "object")
    }
ts.append("}")
go.append("}")
schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": entity,
    "type": "object",
    "properties": props,
    "required": [f["name"] for f in fields if f.get("required") == "true"],
}

arts = {
    "record.py": "\n".join(py) + "\n",
    "record.ts": "\n".join(ts) + "\n",
    "record.go": "\n".join(go) + "\n",
    "schema.json": json.dumps(schema, indent=2) + "\n",
    "README.md": f"# {entity}\n\nGenerated from spec.yaml.\n",
}
manifest = {}
for name, content in arts.items():
    open(os.path.join(OUT, name), "w").write(content)
    manifest[name] = {
        "bytes": len(content),
        "sha256": hashlib.sha256(content.encode()).hexdigest(),
    }
json.dump(manifest, open(os.path.join(ROOT, "build", "manifest.json"), "w"), indent=2)
for name in arts:
    print(f"  {name}  ({manifest[name]['bytes']}B)")
