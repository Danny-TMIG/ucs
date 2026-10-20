import math
def _ci95(s):
    n=len(s); m=sum(s)/n; v=sum((x-m)**2 for x in s)/max(n-1,1); se=math.sqrt(v/n)
    return (m-1.96*se, m+1.96*se)
def bound(sample, grammar, max_size, wall_limit):
    if not sample: return False, "empty sample"
    for s in sample:
        if s.get("grammar")!=grammar: return False, f"grammar violation: {s.get('grammar')!r}"
        if s.get("size",0)>max_size: return False, f"size violation: {s['size']} > {max_size}"
        if s.get("wall",0)>wall_limit: return False, f"wall violation: {s['wall']} > {wall_limit}"
    walls=[s["wall"] for s in sample]
    return True, {"grammar":grammar,"max_size":max_size,"wall_limit":wall_limit,"n":len(walls),
                  "mean":sum(walls)/len(walls),"mean_ci_95":_ci95(walls),
                  "max_observed":max(walls),"all_within_limit":True}
if __name__=="__main__":
    s=[{"grammar":"py","size":800,"wall":0.012},{"grammar":"py","size":1200,"wall":0.018},
       {"grammar":"py","size":1500,"wall":0.021}]
    ok,st=bound(s,"py",2048,0.5); assert ok and st["n"]==3 and st["all_within_limit"]
    ok,r=bound(s+[{"grammar":"py","size":500,"wall":2.0}],"py",2048,0.5); assert not ok and "wall" in r
    ok,r=bound([{"grammar":"py","size":9999,"wall":0.1}],"py",2048,0.5); assert not ok and "size" in r
    ok,r=bound([{"grammar":"rs","size":100,"wall":0.1}],"py",2048,0.5); assert not ok and "grammar" in r
    print("bound OK")
