import math, pathlib, random
CATALOG = pathlib.Path(__file__).resolve().parent.parent / "data" / "nature.txt"
OP_MAP = {
    "foraging":("stochastic_search",+1,{"alpha":1.5}),
    "walk":("stochastic_search",+1,{"momentum":0.7}),
    "consensus":("distribute_converge",+1,{"threshold":0.5}),
    "stigmergy":("distribute_converge",+1,{"decay":0.1}),
    "flocking":("local_align",+1,{"k":7}),
    "oscillator":("phase_sync",+1,{"K":1.0}),
    "morpho":("pattern_form",+1,{"F":0.04,"k":0.06}),
    "threshold":("bistable",+1,{"kappa":0.5}),
    "adaptation":("gain_control",-1,{"tau":1.0}),
    "population":("coupled_ode",+1,{"r":0.3}),
    "flow":("potential_flow",-1,{"D":1.0}),
}
def _parse(path=CATALOG):
    rows=[]
    for line in pathlib.Path(path).read_text().splitlines():
        line=line.strip()
        if not line or line.startswith("#"): continue
        parts=[p.strip() for p in line.split("|")]
        if len(parts)!=3: continue
        rows.append({"code":parts[0],"class":parts[1],"local_rule":parts[2]})
    return rows
def registry(path=CATALOG):
    out=[]
    for row in _parse(path):
        fam, sign, params = OP_MAP.get(row["class"], ("unknown",0,{}))
        out.append({**row, "op_family":fam, "direction":sign, "params":params})
    return out
def boost(reg=None):
    reg = reg or registry()
    return [e for e in reg if e["op_family"] in ("phase_sync","bistable") and e["direction"]==+1]
def lift(reg=None):
    reg = reg or registry()
    return [e for e in reg if e["op_family"] in ("pattern_form","stochastic_search") and e["direction"]==+1]
def drag(reg=None):
    reg = reg or registry()
    return [e for e in reg if e["op_family"] in ("potential_flow","gain_control") and e["direction"]==-1]
def _landscape(x): return math.exp(-((x-0.2)**2)/0.02) + 0.6*math.exp(-((x-0.8)**2)/0.02)
def run(operators, x0=None, steps=200, rng=None):
    rng = rng or random.Random(0)
    x = x0 if x0 is not None else rng.uniform(0,1)
    trace=[x]
    for op in operators:
        for _ in range(steps):
            if op in ("levy_flight","brownian_search"):
                j=rng.gauss(0,0.1)
                if op=="levy_flight": j*=(1+abs(rng.gauss(0,1)))
                x=min(1.0,max(0.0,x+j))
            elif op=="kuramoto": x+=0.05*(0.2-x)
            elif op=="fick":
                e=1e-4; g=(_landscape(x+e)-_landscape(x-e))/(2*e)
                x=min(1.0,max(0.0,x+0.01*g))
            elif op=="homeostasis": x+=0.05*(0.5-x)
            trace.append(x)
    return {"x0":trace[0],"x_final":x,"fitness_before":_landscape(trace[0]),
            "fitness_after":_landscape(x),"improved":_landscape(x)>_landscape(trace[0]),"trace_len":len(trace)}
if __name__=="__main__":
    reg=registry(); assert len(reg)>40
    assert all(e["op_family"]!="unknown" for e in reg), [e["class"] for e in reg if e["op_family"]=="unknown"]
    assert len(boost())>0 and len(lift())>0 and len(drag())>0
    out=run(["brownian_search","fick"], x0=0.9); assert out["improved"], out
    out2=run(["homeostasis"], x0=0.9); assert abs(out2["x_final"]-0.5)<0.2, out2
    print(f"nature OK ({len(reg)} entries, boost {len(boost())}, lift {len(lift())}, drag {len(drag())})")
