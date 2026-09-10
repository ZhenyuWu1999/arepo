"""Fast estimate of the safe retention window of a post-flip triangle.

At each detected flip we freeze the three vertex velocities and follow the
triangle analytically: signed area is a quadratic in t, so the inversion time
is a root, and the N-scheme bound dt_N ~ inradius is evaluated on the same
trajectory.  Frozen velocities are an approximation, stated as such; it is
accurate over the few-CFL windows that turn out to matter.
"""
import numpy as np
from scipy.spatial import Delaunay

GAMMA, CFL, CHI = 1.4, 0.3, 0.5


def sarea(P):           # P: (...,3,2)
    a, b, c = P[..., 0, :], P[..., 1, :], P[..., 2, :]
    return 0.5*((b[..., 0]-a[..., 0])*(c[..., 1]-a[..., 1])
                - (b[..., 1]-a[..., 1])*(c[..., 0]-a[..., 0]))


def inrad(P):
    A = np.abs(sarea(P))
    s = 0.5*(np.linalg.norm(P[..., 1, :]-P[..., 0, :], axis=-1)
             + np.linalg.norm(P[..., 2, :]-P[..., 1, :], axis=-1)
             + np.linalg.norm(P[..., 0, :]-P[..., 2, :], axis=-1))
    return A/np.maximum(s, 1e-300)


def field(p, kind):
    x, y = p[:, 0], p[:, 1]
    if kind == "kh":
        v = np.zeros_like(p)
        v[:, 0] = 0.5*np.tanh((y-0.5)/0.05)
        v[:, 1] = 0.05*np.sin(4*np.pi*x)*np.exp(-((y-0.5)/0.1)**2)
        return v, np.ones(len(p))
    if kind == "gresho":
        r = np.hypot(x-0.5, y-0.5)+1e-12
        vp = np.where(r < .2, 5*r, np.where(r < .4, 2-5*r, 0.))
        return np.stack([-vp*(y-.5)/r, vp*(x-.5)/r], 1), np.sqrt(GAMMA*5.)*np.ones(len(p))
    if kind == "rt":
        v = np.zeros_like(p); v[:, 1] = 0.05*np.sin(2*np.pi*x)*np.exp(-((y-.5)/.15)**2)
        return v, np.where(y > .5, 1.2, 0.6)
    raise ValueError


def run(kind, n_side=34, n_cfl=60., sub=0.15, chi=CHI, seed=3):
    rng = np.random.default_rng(seed)
    lo, hi = -.25, 1.25
    g = np.linspace(lo, hi, int(n_side*(hi-lo)))
    X, Y = np.meshgrid(g, g); p = np.stack([X.ravel(), Y.ravel()], 1)
    h0 = g[1]-g[0]; p = p + rng.uniform(-.35*h0, .35*h0, p.shape)
    cs_ref = 1.0 if kind != "gresho" else np.sqrt(GAMMA*5.)
    dt_cfl = CFL*h0/cs_ref; dt = sub*dt_cfl
    ins = lambda q: (q[:, 0] > .08)&(q[:, 0] < .92)&(q[:, 1] > .08)&(q[:, 1] < .92)
    prev, t_inv, t50, t10, nflip = None, [], [], [], 0

    for step in range(int(n_cfl/sub)):
        simp = Delaunay(p).simplices
        keep = ins(p[simp].mean(1))
        keys = set(frozenset(s) for s in simp[keep])
        v, cs = field(p, kind)
        w = v.copy()
        if chi > 0:
            tri = Delaunay(p); ind, ptr = tri.vertex_neighbor_vertices
            cnt = np.diff(ind); acc = np.add.reduceat(p[ptr], ind[:-1], axis=0)
            d = acc/np.maximum(cnt, 1)[:, None] - p
            dn = np.linalg.norm(d, axis=1)
            spd = np.minimum(chi*cs, dn/dt*0.5)
            w += np.where(dn[:, None] > 0, d/np.maximum(dn, 1e-30)[:, None], 0)*spd[:, None]

        if prev is not None:
            died = [np.array(sorted(k)) for k in (prev - keys)]
            nflip += len(died)
            if died:
                idx = np.array(died)
                P0, V0 = p[idx], w[idx]
                A0 = sarea(P0); sgn = np.sign(A0); r0 = inrad(P0)
                # scan the analytic trajectory
                taus = np.linspace(0, 200*dt_cfl, 601)[1:]
                hit_inv = np.full(len(idx), np.nan)
                hit50 = np.full(len(idx), np.nan)
                hit10 = np.full(len(idx), np.nan)
                for tau in taus:
                    Pt = P0 + tau*V0
                    A = sarea(Pt)*sgn
                    r = inrad(Pt)
                    m = np.isnan(hit_inv) & (A <= 0)
                    hit_inv[m] = tau
                    m = np.isnan(hit50) & (r <= .5*r0)
                    hit50[m] = tau
                    m = np.isnan(hit10) & (r <= .1*r0)
                    hit10[m] = tau
                t_inv.append(hit_inv/dt_cfl); t50.append(hit50/dt_cfl); t10.append(hit10/dt_cfl)
        prev = keys
        p = p + dt*w

    cat = lambda L: np.concatenate(L) if L else np.array([])
    return dict(kind=kind, chi=chi, nflip=nflip, inv=cat(t_inv), h50=cat(t50), h10=cat(t10))


def show(r):
    print(f"\n  field={r['kind']:7s} regularisation chi={r['chi']:.2f}   flips detected={r['nflip']}")
    for name, a in [("dt_N -> 50%", r["h50"]), ("dt_N -> 10%", r["h10"]), ("inverted", r["inv"])]:
        fin = a[np.isfinite(a)]
        frac = len(fin)/max(len(a), 1)
        if len(fin) == 0:
            print(f"    {name:12s}: never within 200 CFL steps")
            continue
        print(f"    {name:12s}: reached by {100*frac:5.1f}% of retired triangles;"
              f"  5%={np.percentile(fin,5):6.1f}  median={np.median(fin):6.1f}"
              f"  95%={np.percentile(fin,95):7.1f}   (CFL steps)")


print("="*94)
print("Safe retention window of a post-flip RD triangle, in units of the LOCAL CFL step")
print("dt_N ~ inradius is the N-scheme positivity bound for that triangle")
print("="*94)
for kind in ["kh", "gresho", "rt"]:
    for chi in [CHI, 0.0]:
        show(run(kind, chi=chi))
print("\nA hierarchical wait of one coarse step costs 2^k CFL steps of the fine node:")
print("  k= 1   2   3    4    5    6    7     8     9    10")
print("     2   4   8   16   32   64  128   256   512  1024")
