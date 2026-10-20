import atlas, mip
class BondTypeError(Exception): pass
class Species:
    def __init__(self, code, family, params, substrate, invoke, schema):
        self.code=code; self.family=family; self.params=params
        self.substrate=substrate; self.invoke=invoke; self.schema=schema
    @property
    def channel(self): return (self.code, self.family)
    def __call__(self, inp): return self.invoke(inp)
def species_from_code(code, substrate="python"):
    m = mip.message(code)
    if substrate not in m["substrate"]: raise mip.NoSubstrate(code)
    invoke = lambda inp, _c=code, _s=substrate: mip.dispatch(_c, inp, _s)
    return Species(m["code"], m["family"], m["params"], substrate, invoke, m["schema"])
def bond(s1, s2):
    if s1.schema.get("out") != s2.schema.get("in"):
        raise BondTypeError(f"{s1.code}.out={s1.schema.get('out')!r} != {s2.code}.in={s2.schema.get('in')!r}")
    def composed(inp): return s2(s1(inp))
    return Species(f"({s1.code} > {s2.code})","composite",{},"mixed",composed,
                   {"in":s1.schema["in"],"out":s2.schema["out"],"err":[]})
class Cascade:
    def __init__(self): self.g=atlas.Atlas(); self._sp={}
    def add(self, sp):
        self.g.add(atlas.Node("species", sp.code, {"family":sp.family,"schema":sp.schema}))
        self._sp[sp.code]=sp; return sp
    def bond(self, a, b):
        if self._sp[a].schema.get("out") != self._sp[b].schema.get("in"):
            raise BondTypeError(f"cascade bond {a}->{b}")
        self.g.add_edge(a, "bonds_with", b)
    def run(self, entry, inp):
        order = self.g.downstream(entry); cur = inp
        trace = [("entry", entry, cur)]
        for c in order:
            cur = self._sp[c](cur); trace.append(("step", c, cur))
        return {"result":cur, "trace":trace}
if __name__=="__main__":
    s1=species_from_code("levy_flight"); s2=species_from_code("kuramoto")
    try: bond(s1, Species("bad","f",{},  "python", lambda i:i, {"in":"list","out":"dict","err":[]}))
    except BondTypeError: pass
    else: raise SystemExit("expected BondTypeError")
    c = bond(s1, s2); assert c.family=="composite"
    cas = Cascade(); cas.add(s1); cas.add(s2); cas.bond("levy_flight","kuramoto")
    r = cas.run("levy_flight", {"x0":0.9}); assert len(r["trace"])==2
    print("mimc OK")
