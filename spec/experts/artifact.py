import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from desk import desk
def module_ctor(pid, name, root):
    p = pathlib.Path(root)/pid/"handlers"/f"{name}.py"; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(f"def {name}(payload):\n    return {{'ok': True}}\n"); return str(p)
def test_ctor(pid, name, root):
    p = pathlib.Path(root)/pid/"tests"/f"test_{name}.py"; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text("def test_x():\n    assert True\n"); return str(p)
def schema_ctor(pid, name, root):
    p = pathlib.Path(root)/pid/"schemas"/f"{name}.schema.json"; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps({"$id":f"{name}.schema.json","type":"object"})); return str(p)
def doc_ctor(pid, name, root):
    p = pathlib.Path(root)/pid/"DESIGN.md"; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(f"# {name}\n"); return str(p)
for k, f in [("module",module_ctor),("test",test_ctor),("schema",schema_ctor),("doc",doc_ctor)]:
    desk.press("artifact",k,f)
