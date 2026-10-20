import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from desk import desk
def must(c): return {"kind":"must","predicate":c,"falsifier":f"assert {c!r} is not None"}
def must_not(c): return {"kind":"must_not","predicate":c,"falsifier":f"assert {c!r} is None"}
desk.press("constraint","must",must)
desk.press("constraint","must_not",must_not)
