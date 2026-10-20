FIELD = {
    "key": {"type": "str", "required": True},
    "id": {"type": "int", "required": True},
    "project": {"type": "dict", "required": True},
    "type": {"type": "str", "required": True,
             "enum": ["bug","task","story","epic","subtask","spike","incident","chore","decision","rfcs"]},
    "status": {"type": "str", "required": True},
    "priority": {"type": "str", "required": False},
    "resolution": {"type": "str", "required": False},
    "assignee": {"type": "str", "required": False},
    "reporter": {"type": "str", "required": True},
    "creator": {"type": "str", "required": True},
    "created": {"type": "str", "required": True},
    "updated": {"type": "str", "required": True},
    "resolved": {"type": "str", "required": False},
    "duedate": {"type": "str", "required": False},
    "labels": {"type": "list", "required": False},
    "components": {"type": "list", "required": False},
    "fix_versions": {"type": "list", "required": False},
    "affects_versions": {"type": "list", "required": False},
    "parent": {"type": "str", "required": False},
    "epic": {"type": "str", "required": False},
    "subtasks": {"type": "list", "required": False},
    "links": {"type": "list", "required": False},
    "watchers": {"type": "list", "required": False},
    "votes": {"type": "int", "required": False},
    "fields": {"type": "dict", "required": False},
}

STATE = {
    "open": {"next": ["in_progress","blocked","closed","rejected","duplicate"]},
    "in_progress": {"next": ["open","blocked","in_review","closed","rejected"]},
    "blocked": {"next": ["open","in_progress","closed","rejected"]},
    "in_review": {"next": ["in_progress","closed","rejected","changes_requested"]},
    "changes_requested": {"next": ["in_progress","closed","rejected"]},
    "closed": {"next": ["reopened"]},
    "rejected": {"next": ["reopened"]},
    "duplicate": {"next": []},
    "reopened": {"next": ["in_progress","closed"]},
}

EDGE = {
    "blocks": "blocked_by", "blocked_by": "blocks",
    "relates_to": "relates_to",
    "duplicates": "duplicated_by", "duplicated_by": "duplicates",
    "causes": "caused_by", "caused_by": "causes",
    "parent_of": "child_of", "child_of": "parent_of",
    "clones": "cloned_by", "cloned_by": "clones",
    "implements": "implemented_by", "implemented_by": "implements",
    "tests": "tested_by", "tested_by": "tests",
}

EVENT = {
    "created": ["ts","author","payload"],
    "transition": ["ts","author","from","to"],
    "field_edit": ["ts","author","from","to"],
    "comment": ["ts","author","payload"],
    "attach": ["ts","author","payload","hash"],
    "link": ["ts","author","from","to","edge"],
    "unlink": ["ts","author","from","to","edge"],
}

def validate_envelope(env):
    errs = []
    for name, spec in FIELD.items():
        if spec["required"] and name not in env:
            errs.append(f"missing {name}")
            continue
        if name not in env:
            continue
        t = spec["type"]
        if t == "str" and not isinstance(env[name], str): errs.append(f"{name} must be str")
        if t == "int" and not isinstance(env[name], int): errs.append(f"{name} must be int")
        if t == "list" and not isinstance(env[name], list): errs.append(f"{name} must be list")
        if t == "dict" and not isinstance(env[name], dict): errs.append(f"{name} must be dict")
        if "enum" in spec and env[name] not in spec["enum"]:
            errs.append(f"{name}={env[name]!r} not in enum")
    return errs

def validate_transition(from_state, to_state):
    if from_state not in STATE:
        return [f"unknown from {from_state!r}"]
    if to_state not in STATE[from_state]["next"]:
        return [f"invalid {from_state}->{to_state}"]
    return []

def validate_edge(edge):
    return [] if edge in EDGE else [f"unknown edge {edge!r}"]

def validate_event(ev):
    k = ev.get("kind")
    if k not in EVENT:
        return [f"unknown event {k!r}"]
    errs = []
    for f in EVENT[k]:
        if f not in ev:
            errs.append(f"{k}: missing {f}")
    return errs

if __name__ == "__main__":
    good = {"key":"A-1","id":1,"project":{"key":"A"},"type":"bug","status":"open",
            "reporter":"u","creator":"u","created":"t","updated":"t"}
    assert validate_envelope(good) == []
    bad = dict(good); del bad["key"]
    assert validate_envelope(bad)
    assert validate_transition("open","in_progress") == []
    assert validate_transition("closed","in_progress")
    assert validate_edge("blocks") == []
    assert validate_edge("nope")
    assert validate_event({"kind":"transition","ts":"t","author":"u","from":"open","to":"in_progress"}) == []
    print("record OK")
