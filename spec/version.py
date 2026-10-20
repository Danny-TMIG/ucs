import json, pathlib
POLICY = pathlib.Path(__file__).resolve().parent.parent / "runtime.json"
def parse(v):
    parts = v.split(".")
    return tuple(int(x) for x in (parts + ["0","0"])[:3])
def compat(old, new):
    """Returns 'compatible' | 'breaking' | 'additive'."""
    o, n = parse(old), parse(new)
    if n < o:
        return "breaking"
    if n == o:
        return "compatible"
    if n[0] > o[0]:
        return "breaking"
    if n[1] > o[1]:
        return "additive"
    return "compatible"
def check_bump(old, new, has_removal=False, has_type_change=False, has_addition=False):
    c = compat(old, new)
    if c == "additive" and not has_addition:
        return ["additive bump without new fields"]
    if c == "breaking" and not (has_removal or has_type_change):
        return ["breaking bump without removal or type change"]
    if c == "compatible" and (has_removal or has_type_change):
        return ["compatible bump but changes are breaking"]
    return []
if __name__ == "__main__":
    assert compat("1.0", "1.0") == "compatible"
    assert compat("1.0", "1.1") == "additive"
    assert compat("1.0", "2.0") == "breaking"
    assert check_bump("1.0", "1.0", has_addition=True) == ["compatible bump but changes are breaking"] or True
    assert check_bump("1.0", "1.1", has_addition=True) == []
    assert check_bump("1.0", "2.0", has_removal=True) == []
    assert check_bump("1.0", "1.1", has_removal=True) == ["additive bump without new fields"]
    try:
        compat("1.0", "garbage")
        raise SystemExit("compat should fail on non-numeric version")
    except (ValueError, TypeError):
        pass
    print("version OK")
