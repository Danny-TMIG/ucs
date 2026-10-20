"""Resolution and dependency lookup module."""
import pathlib

def resolve_path(filename, root=None):
    r = pathlib.Path(root or ".")
    match = list(r.rglob(filename))
    return match[0] if match else None

if __name__ == "__main__":
    print("resolve.py OK")
