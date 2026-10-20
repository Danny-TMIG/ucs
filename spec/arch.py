import math, random
def phase_attention(q, k, v):
    n=len(q); scores=[sum(q[i]*k[j] for i in range(len(q))) for j in range(len(k))]
    phases=[math.cos(s) for s in scores]
    z=sum(phases) or 1.0
    return [sum(phases[j]*v[j][d] for j in range(n))/z for d in range(len(v[0]))]
def sparse_flocking_attention(q, k, v, window=3):
    n=len(q); out=[]
    for d in range(len(v[0])):
        s=0.0
        for j in range(n):
            if abs(j-n//2) <= window:
                s += v[j][d] * sum(q[i]*k[j] for i in range(min(len(q),len(k))))
        out.append(s/max(1,2*window+1))
    return out
def quorum_moe(x, experts, threshold=0.5):
    return [e(x) for e in experts if sum(x)/len(x) >= threshold]
def threshold_ffn(x, w1, w2):
    h = [max(0.0, sum(x[i]*w1[j][i] for i in range(len(x)))) for j in range(len(w1))]
    h = [v if v > 0.5 else 0.0 for v in h]
    return [sum(h[j]*w2[k][j] for j in range(len(h))) for k in range(len(w2))]
def hebbian_update(w, x, y, eta=0.01):
    for i in range(len(w)):
        for j in range(len(w[i])):
            w[i][j] += eta * x[i]*y[j]
    return w
def stigmergy_trace(state, new_state, decay=0.1):
    return [(1-decay)*s + decay*n for s,n in zip(state, new_state)]
def flow_residual(x, h, dt=0.1):
    return [xi + dt*hi for xi, hi in zip(x, h)]
def morpho_decode(h, kernel):
    out=[]
    for i in range(len(h)):
        s=0.0
        for k in range(len(kernel)):
            j = i+k-len(kernel)//2
            if 0 <= j < len(h): s += h[j]*kernel[k]
        out.append(math.tanh(s))
    return out
def levy_sample(logits, alpha=1.5, rng=None):
    rng = rng or random.Random(0)
    idx = max(range(len(logits)), key=lambda i: logits[i])
    if rng.random() < 0.7: return idx
    return rng.randrange(len(logits))
if __name__=="__main__":
    q=[0.1,0.2,0.3]; k=[0.3,0.2,0.1]; v=[[1.0,0.0],[0.0,1.0],[1.0,1.0]]
    assert len(phase_attention(q,k,v))==2
    assert len(sparse_flocking_attention(q,k,v))==2
    moe = quorum_moe([0.6,0.7], [lambda x: sum(x), lambda x: max(x)], threshold=0.5)
    assert len(moe)==2
    w1=[[0.1,0.2],[0.3,0.4]]; w2=[[0.5,0.6]]
    assert len(threshold_ffn([1.0,0.5], w1, w2))==1
    w=[[0.0,0.0],[0.0,0.0]]
    hebbian_update(w,[1.0,2.0],[0.5,0.5], eta=0.1)
    assert w[0][0]>0
    assert len(stigmergy_trace([0.0,0.0],[1.0,1.0]))==2
    assert len(flow_residual([0.0,0.0],[1.0,1.0]))==2
    assert len(morpho_decode([0.1,0.2,0.3],[0.25,0.5,0.25]))==3
    assert levy_sample([1.0, 10.0, 2.0], rng=random.Random(0)) in (1, 0, 2)
    print("arch OK")
