#!/usr/bin/env python3
"""migrate.py — forward and backward migration for state files."""
import json, pathlib, shutil

MIGRATIONS = {
    ("v1", "v2"): lambda d: {**d, "schema": "v2", "migrated_from": "v1"},
    ("v2", "v3"): lambda d: {**d, "schema": "v3", "versioned": True},
}

def up(payload, from_v, to_v):
    key = (from_v, to_v)
    if key not in MIGRATIONS:
        raise KeyError(f"no migration {from_v} -> {to_v}")
    return MIGRATIONS[key](payload)

def down(payload, from_v, to_v):
    """Undo a previously-applied from_v -> to_v migration."""
    if (from_v, to_v) not in MIGRATIONS:
        raise KeyError(f"no migration {from_v} -> {to_v} to reverse")
    return {k: v for k, v in payload.items()
            if k not in ("migrated_from", "versioned")} | {"schema": from_v}

def migrate_file(path, from_v, to_v, reverse=False):
    p = pathlib.Path(path)
    data = json.loads(p.read_text())
    backup = p.with_suffix(p.suffix + f".{from_v}.bak")
    shutil.copy(p, backup)
    out = down(data, from_v, to_v) if reverse else up(data, from_v, to_v)
    p.write_text(json.dumps(out, indent=2))
    return str(p), str(backup)

if __name__ == "__main__":
    import tempfile, os
    os.chdir(tempfile.mkdtemp())
    pathlib.Path("s.json").write_text(json.dumps({"a": 1, "schema": "v1"}))
    m, b = migrate_file("s.json", "v1", "v2")
    assert json.loads(pathlib.Path("s.json").read_text())["schema"] == "v2"
    m, b = migrate_file("s.json", "v1", "v2", reverse=True)
    assert json.loads(pathlib.Path("s.json").read_text())["schema"] == "v1"
    assert pathlib.Path(b).exists()
    print("migrate OK")
