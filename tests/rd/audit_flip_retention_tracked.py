"""How long may RD retain an old (post-flip) triangle before its own N-scheme
timestep bound collapses?

For a triangle T with inflow parameters k_i = 0.5 * lambda . n_i, the N scheme
is positive under  dt <= |T| / sum_i k_i^+ .  With |lambda| = a fixed signal
speed, that bound scales as  |T| / perimeter ~ inradius.  So the relevant
quality measure of a retained triangle is its inradius, not merely a positive
area.

We move an AREPO-like 2-D point set (Lagrangian velocity + Lloyd-type
regularisation at CellShapingSpeed = 0.5 c_s), detect Delaunay flips, and then
follow each retired triangle along the true trajectory, recording the time at
which its N-timestep bound falls to 50% / 10% of its value at the flip, and the
time at which it inverts -- all in units of the local hydro CFL step.
"""
import numpy as np
from scipy.spatial import Delaunay

GAMMA = 1.4
CFL = 0.3
CHI = 0.5          # All.CellShapingSpeed


def signed_area(p, idx):
    a, b, c = p[idx[:, 0]], p[idx[:, 1]], p[idx[:, 2]]
    return 0.5 * ((b[:, 0]-a[:, 0])*(c[:, 1]-a[:, 1]) - (b[:, 1]-a[:, 1])*(c[:, 0]-a[:, 0]))


def inradius(p, idx):
    a, b, c = p[idx[:, 0]], p[idx[:, 1]], p[idx[:, 2]]
    A = np.abs(signed_area(p, idx))
    s = (np.linalg.norm(b-a, axis=1) + np.linalg.norm(c-b, axis=1)
         + np.linalg.norm(a-c, axis=1)) * 0.5
    return A / np.maximum(s, 1e-300)


def field(p, kind):
    x, y = p[:, 0], p[:, 1]
    if kind == "kh":                       # Mach ~0.5 shear layer
        v = np.zeros_like(p)
        v[:, 0] = 0.5*np.tanh((y-0.5)/0.05)
        v[:, 1] = 0.05*np.sin(4*np.pi*x)*np.exp(-((y-0.5)/0.1)**2)
        return v, np.ones(len(p))
    if kind == "gresho":
        r = np.hypot(x-0.5, y-0.5) + 1e-12
        vphi = np.where(r < 0.2, 5*r, np.where(r < 0.4, 2-5*r, 0.0))
        cs = np.sqrt(GAMMA*5.0)*np.ones(len(p))
        return np.stack([-vphi*(y-0.5)/r, vphi*(x-0.5)/r], 1), cs
    if kind == "rt":                       # slow buoyant, deep bin contrast
        v = np.zeros_like(p)
        v[:, 1] = 0.02*np.sin(2*np.pi*x)*np.exp(-((y-0.5)/0.15)**2)
        cs = np.where(y > 0.5, 1.2, 0.6)   # 2x sound-speed jump -> different bins
        return v, cs
    raise ValueError(kind)


def run(kind, n_side=34, t_end_cfl=150.0, sub=0.1, chi=CHI, seed=3):
    rng = np.random.default_rng(seed)
    lo, hi = -0.25, 1.25
    g = np.linspace(lo, hi, int(n_side*(hi-lo)))
    X, Y = np.meshgrid(g, g)
    p = np.stack([X.ravel(), Y.ravel()], 1)
    h0 = g[1]-g[0]
    p = p + rng.uniform(-0.35*h0, 0.35*h0, size=p.shape)

    cs_ref = 1.0 if kind != "gresho" else np.sqrt(GAMMA*5.0)
    dt_cfl = CFL*h0/cs_ref
    dt = sub*dt_cfl
    n_steps = int(t_end_cfl/sub)

    inside = lambda q: ((q[:, 0] > .08) & (q[:, 0] < .92) & (q[:, 1] > .08) & (q[:, 1] < .92))

    prev = None
    pending = {}
    rec50, rec10, rec0 = [], [], []
    n_flips = 0
    ntri = []
    for step in range(n_steps):
        t = step*dt
        simp = Delaunay(p).simplices
        keep = inside(p[simp].mean(1))
        keys = set(frozenset(s) for s in simp[keep])
        ntri.append(keep.sum())

        if prev is not None:
            for k in prev - keys:
                idx = np.array(sorted(k))
                A = signed_area(p, idx[None])[0]
                pending[k] = dict(t=t, idx=idx, q0=inradius(p, idx[None])[0], sgn=np.sign(A))

        drop = []
        for k, r in pending.items():
            A = signed_area(p, r["idx"][None])[0]*r["sgn"]
            q = inradius(p, r["idx"][None])[0]
            age = (t-r["t"])/dt_cfl
            if A <= 0:
                rec0.append(age); drop.append(k); continue
            if q <= 0.5*r["q0"] and "h50" not in r:
                rec50.append(age); r["h50"] = 1
            if q <= 0.1*r["q0"] and "h10" not in r:
                rec10.append(age); r["h10"] = 1
            if age > 1200:
                drop.append(k)
        for k in drop:
            pending.pop(k)
        prev = keys
        n_flips += 0

        v, cs = field(p, kind)
        w = v.copy()
        if chi > 0:      # Lloyd-type regularisation, speed capped at chi*c_s
            tri = Delaunay(p)
            ind, ptr = tri.vertex_neighbor_vertices
            cnt = np.diff(ind)
            acc = np.add.reduceat(p[ptr], ind[:-1], axis=0)
            nbar = acc/np.maximum(cnt, 1)[:, None]
            d = nbar - p
            dn = np.linalg.norm(d, axis=1)
            spd = np.minimum(chi*cs, dn/dt*0.5)
            w = w + np.where(dn[:, None] > 0, d/np.maximum(dn, 1e-30)[:, None], 0)*spd[:, None]
        p = p + dt*w

    n_flips = len(rec0)+len(pending)+len(rec50)  # lower bound bookkeeping
    return dict(kind=kind, chi=chi, ntri=np.mean(ntri), dt_cfl=dt_cfl,
                t_end_cfl=t_end_cfl, rec50=np.array(rec50), rec10=np.array(rec10),
                rec0=np.array(rec0), n_alive=len(pending))


def show(r):
    def s(a, name):
        if len(a) == 0:
            print(f"    {name:22s} : none reached within {r['t_end_cfl']:.0f} CFL steps")
            return
        print(f"    {name:22s} : n={len(a):5d}  5%={np.percentile(a,5):7.2f}  "
              f"median={np.median(a):7.2f}  95%={np.percentile(a,95):8.2f}")
    print(f"\n  field={r['kind']:7s} chi={r['chi']:.2f}  interior triangles={r['ntri']:.0f}")
    s(r["rec50"], "age at dt_N -> 50%")
    s(r["rec10"], "age at dt_N -> 10%")
    s(r["rec0"], "age at inversion")
    print(f"    still healthy at end   : {r['n_alive']}")


print("="*92)
print("Age (in local CFL steps) of a retained post-flip triangle when its N-scheme")
print("timestep bound dt_N ~ inradius falls to 50% / 10%, and when it inverts")
print("="*92)
for kind in ["kh", "gresho", "rt"]:
    for chi in [CHI, 0.0]:
        show(run(kind, chi=chi))
print()
print("A hierarchical wait of one coarse step costs 2^k CFL steps of the fine node.")
