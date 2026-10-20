import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from desk import desk
def json_rec(pid, data, root):
    p = pathlib.Path(root)/pid/"evidence.json"; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data, indent=2)); return str(p)
desk.press("evidence","json",json_rec)
