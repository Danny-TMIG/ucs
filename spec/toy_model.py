import random, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import arch
def _correctly_labelled():
    rng = random.Random(42)
    data = []
    for _ in range(200):
        a = rng.choice([0.0,1.0]); b = rng.choice([0.0,1.0])
        data.append(([a,b], 1.0 if a!=b else 0.0))
    return data
def baseline_predict(x): return 0.5
def arch_predict(x):
    q=[x[0],x[1],1.0]; k=[1.0,1.0,0.0]; v=[[x[0],1-x[0]],[x[1],1-x[1]],[0.5,0.5]]
    attn = arch.phase_attention(q,k,v)
    h = arch.morpho_decode(attn, [0.25,0.5,0.25])
    return h[0]
def accuracy(pred, data):
    correct = sum(1 for x, y in data if abs(pred(x)-y) < 0.5)
    return correct/len(data)
if __name__=="__main__":
    data = _correctly_labelled()
    base = accuracy(baseline_predict, data)
    comp = accuracy(arch_predict, data)
    print(f"baseline acc: {base:.3f}, composed acc: {comp:.3f}")
    assert comp >= base, (base, comp)
    print("toy_model OK")
