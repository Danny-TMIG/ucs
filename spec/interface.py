import math
def bulk_morpho(p): return (p*p-1.0)**2
def bulk_flow(p): return p*p
def bulk_threshold(p): return 0.25*(p**4)-0.5*(p**2)
def bulk_adaptation(p): return p*p
def bulk_oscillator(p): return 1.0-math.cos(p)
def bulk_population(p): return p*p*(1.0-p)*(1.0+p)
BULKS = {"morpho":bulk_morpho,"flow":bulk_flow,"threshold":bulk_threshold,
         "adaptation":bulk_adaptation,"oscillator":bulk_oscillator,"population":bulk_population}
def solve_1d(bulk, kappa, n=128, iters=2500, dt=None):
    dx = 1.0/(n-1)
    if dt is None: dt = 0.1*dx*dx/max(kappa,1e-6)
    phi = [-1.0 + 2.0*i/(n-1) for i in range(n)]
    eps=1e-4
    def fp(p): return (bulk(p+eps)-bulk(p-eps))/(2*eps)
    for _ in range(iters):
        new=list(phi)
        for i in range(1,n-1):
            lap = (phi[i+1]-2*phi[i]+phi[i-1])/(dx*dx)
            new[i] = phi[i] - dt*(fp(phi[i]) - kappa*lap)
        phi = new
    return phi
def interface_energy(phi, kappa, dx):
    s=0.0
    for i in range(len(phi)-1):
        s += ((phi[i+1]-phi[i])/dx)**2 * dx
    return kappa*s
if __name__=="__main__":
    dx = 1.0/127
    for name, bulk in BULKS.items():
        phi = solve_1d(bulk, kappa=0.01, n=128, iters=2000)
        sigma = interface_energy(phi, 0.01, dx)
        assert sigma > 0, (name, sigma)
    try:
        solve_1d(lambda p: 1/0, 0.01, n=8, iters=2)
        raise SystemExit("interface should fail on bad bulk")
    except ZeroDivisionError:
        pass
    print("interface OK")
