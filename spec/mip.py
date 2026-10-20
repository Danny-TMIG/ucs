import nature
class NoSubstrate(Exception): pass
class NoCode(Exception): pass
_UNITS = {}
def _register(substrate, code, fn, schema=None):
    _UNITS.setdefault(code,{})[substrate]={"invoke":fn,"schema":schema or {}}
def register_default():
    for e in nature.registry():
        code=e["code"]; fam=e["op_family"]
        def make(fam=fam, code=code):
            def invoke(inp):
                if fam=="stochastic_search": return nature.run([code], x0=inp.get("x0",0.5))
                if fam=="phase_sync": return nature.run(["kuramoto"], x0=inp.get("x0",0.5))
                if fam=="potential_flow": return nature.run(["fick"], x0=inp.get("x0",0.5))
                if fam=="gain_control": return nature.run(["homeostasis"], x0=inp.get("x0",0.5))
                return {"family":fam,"input":inp}
            return invoke
        _register("python", code, make(), schema={"in":"dict","out":"dict","err":["NoSubstrate"]})
def message(code):
    reg={e["code"]:e for e in nature.registry()}
    if code not in reg: raise NoCode(code)
    e=reg[code]
    return {"code":e["code"],"family":e["op_family"],"params":e["params"],
            "substrate":list(_UNITS.get(code,{})),
            "schema":{"in":"dict","out":"dict","err":["NoSubstrate","NoCode"]}}
def dispatch(code, inp, substrate="python"):
    if code not in _UNITS: raise NoCode(code)
    if substrate not in _UNITS[code]: raise NoSubstrate(f"{code} no {substrate}; have {list(_UNITS[code])}")
    return _UNITS[code][substrate]["invoke"](inp)
def substrates(): return sorted({s for u in _UNITS.values() for s in u})
register_default()
if __name__=="__main__":
    m=message("levy_flight"); assert m["family"]=="stochastic_search"
    out=dispatch("levy_flight",{"x0":0.9}); assert "fitness_after" in out
    try: dispatch("levy_flight",{},substrate="crn")
    except NoSubstrate: pass
    else: raise SystemExit("expected NoSubstrate")
    try: dispatch("nope",{})
    except NoCode: pass
    else: raise SystemExit("expected NoCode")
    _register("llama", "levy_flight", lambda i: {"note":"stub"})
    assert "llama" in message("levy_flight")["substrate"]
    print(f"mip OK (substrates {substrates()})")
