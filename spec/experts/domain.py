import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from desk import desk
def code_expert(intent):
    return {"domain":"code","kinds":["module","test","schema"],"goal":intent.get("goal","")}
def doc_expert(intent):
    return {"domain":"doc","kinds":["doc"],"goal":intent.get("goal","")}
desk.press("domain","code",code_expert)
desk.press("domain","doc",doc_expert)
