#!/usr/bin/env python3
"""Compile src/hydro/rd_flip_transfer.h and check the flip-element transfer.

* single convex 2-2 flips and multi-flip cavities from real Delaunay rebuilds
  of moving jittered point sets (SciPy), with full nodal masses;
* exact conservation of all four totals; admissible output; theta in [0,1];
* uniform states and affine conserved fields are unchanged (theta = 1);
* extreme contrasts (Sedov-like energy ratio 1e8, counter-streaming flows)
  stay admissible and respect the density hull and entropy minimum;
* the high endpoint is exactly invertible (flip followed by its reverse);
* independent NumPy formulas for the defect and both endpoints.
Kernel tests only; not a moving-mesh or time-integration result.
"""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import numpy as np
from scipy.spatial import Delaunay

REPO = Path(__file__).resolve().parents[2]
GAMMA = 5 / 3


def build():
    folder = Path(tempfile.mkdtemp())
    src = folder / 'kernel.c'
    src.write_text(
        '#include "rd_flip_transfer.h"\n'
        'int kernel(int n,const double*g,const double*dm,const double*u,double gamma,double floor_fraction,'
        'double dmp_relax,int entropy,double*out,double*diag){\n'
        ' struct rd_flip_options o={gamma,floor_fraction,dmp_relax,entropy}; struct rd_flip_diagnostics d;\n'
        ' double (*ul)[4]=malloc(sizeof(double[4])*n),(*uh)[4]=malloc(sizeof(double[4])*n),(*w)[4]=malloc(sizeof(double[4])*n);\n'
        ' int s=rd_flip_transfer(n,g,dm,(const double(*)[4])u,&o,ul,uh,w,(double(*)[4])out,&d);\n'
        ' free(ul);free(uh);free(w);\n'
        ' diag[0]=d.theta;diag[1]=d.defect_scale;diag[2]=d.max_change;diag[3]=d.high_accepted;diag[4]=d.donors;diag[5]=d.receivers;\n'
        ' return s;}\n')
    lib = folder / 'kernel.so'
    subprocess.run(['cc', '-shared', '-fPIC', '-O2', '-std=c11', '-Wall', '-Werror', '-Wno-unused-function',
                    '-include', 'stdlib.h', '-I' + str(REPO / 'src/hydro'), str(src), '-o', str(lib), '-lm'], check=True)
    fn = ctypes.CDLL(str(lib)).kernel
    p = np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')
    fn.argtypes = [ctypes.c_int, p, p, p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, p, p]
    fn.restype = ctypes.c_int
    return fn


KERNEL = build()


def transfer(g, dm, u, dmp_relax=0.0, entropy=1, floor_fraction=1e-12):
    out = np.zeros_like(u); diag = np.zeros(6)
    s = KERNEL(len(g), np.ascontiguousarray(g, float), np.ascontiguousarray(dm, float), np.ascontiguousarray(u, float),
               GAMMA, floor_fraction, dmp_relax, entropy, out, diag)
    return s, out, diag


def internal(u):
    return u[..., 3] - 0.5 * (u[..., 1] ** 2 + u[..., 2] ** 2) / u[..., 0]


def K(u):
    return (GAMMA - 1) * internal(u) / u[..., 0] ** GAMMA


def euler_states(n, rng, contrast=3.0):
    rho = 10 ** rng.uniform(-contrast, contrast, n); v = rng.normal(size=(n, 2)) * 3
    p = 10 ** rng.uniform(-2 * contrast, contrast, n)
    return np.c_[rho, rho[:, None] * v, p / (GAMMA - 1) + .5 * rho * (v ** 2).sum(1)]


def tri_area(x, t):
    a, b, c = x[t[:, 0]], x[t[:, 1]], x[t[:, 2]]
    return .5 * ((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0]))


def cavities(x_now, tri_old, tri_new):
    """Changed cavities between two triangulations of the same points at the same time."""
    key = lambda t: tuple(sorted(t))
    old = {key(t): t for t in tri_old}; new = {key(t): t for t in tri_new}
    gone = [old[k] for k in old.keys() - new.keys()]; born = [new[k] for k in new.keys() - old.keys()]
    parent = {}
    def find(i):
        while parent.setdefault(i, i) != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for t in gone + born:
        for v in t[1:]:
            parent[find(v)] = find(t[0])
    groups = {}
    for t in gone + born:
        groups.setdefault(find(t[0]), set()).update(t)
    out = []
    for nodes in groups.values():
        nodes = sorted(nodes); idx = {v: k for k, v in enumerate(nodes)}
        a = np.zeros(len(nodes)); b = np.zeros(len(nodes))
        for t in gone:
            if t[0] in idx:
                ar = abs(tri_area(x_now, np.array([t]))[0])
                for v in t: a[idx[v]] += ar / 3
        for t in born:
            if t[0] in idx:
                ar = abs(tri_area(x_now, np.array([t]))[0])
                for v in t: b[idx[v]] += ar / 3
        out.append((np.array(nodes), a, b))
    return out


def check_case(g, dm, u, worst, rng_tag):
    s, out, diag = transfer(g, dm, u)
    assert s == 0, (rng_tag, s)
    gnew = g + dm
    tot0 = (g[:, None] * u).sum(0); tot1 = (gnew[:, None] * out).sum(0)
    scale = (g[:, None] * np.abs(u)).sum(0)
    scale = np.where(scale > 0, scale, 1.0)        # e.g. zero momentum everywhere
    err = np.max(np.abs(tot1 - tot0) / scale)
    worst['conservation'] = max(worst['conservation'], err)
    assert err < 1e-13, (rng_tag, err)
    assert np.all(out[:, 0] > 0) and np.all(internal(out) > 0), rng_tag
    assert 0 <= diag[0] <= 1
    assert np.all(out[:, 0] >= u[:, 0].min() * (1 - 1e-13)) and np.all(out[:, 0] <= u[:, 0].max() * (1 + 1e-13)), rng_tag
    # entropy minimum up to the kernel's round-off allowance: e = E - |m|^2/2rho is known only to a few
    # ulp of E (cold, fast gas has KE/e ~ 1e5 in these random states)
    slack = 16 * np.finfo(float).eps * np.abs(out[:, 3]) * (GAMMA - 1) / out[:, 0] ** GAMMA
    assert np.all(K(out) + slack >= K(u).min() * (1 - 1e-12)), rng_tag
    # independent endpoints
    D = dm @ u; uh = u - D / gnew.sum()
    donors = dm < 0; ubar = (-dm[donors]) @ u[donors] / (-dm[donors]).sum() if donors.any() else 0 * u[0]
    ul = u.copy(); rec = dm > 0
    ul[rec] = (g[rec, None] * u[rec] + dm[rec, None] * ubar) / gnew[rec, None]
    ref = (1 - diag[0]) * ul + diag[0] * uh
    umax = np.max(np.abs(u), axis=0)
    rel = np.max(np.abs(ref - out) / np.where(umax > 0, umax, 1.0))
    worst['reference'] = max(worst['reference'], rel)
    assert rel < 1e-12, (rng_tag, rel)
    if diag[0] == 0:
        assert np.array_equal(out[donors], u[donors]), rng_tag   # donors bit-for-bit
    worst['theta_min'] = min(worst['theta_min'], diag[0])
    worst['limited'] += diag[0] < 1
    return out, diag


def main():
    rng = np.random.default_rng(20261008)
    worst = dict(conservation=0., reference=0., theta_min=1., limited=0, cases=0, multi=0)

    # 1. single convex 2-2 flips, nodes a,b,c,d (old ac, new bd)
    for trial in range(4000):
        ang = np.sort(rng.uniform(0, 2 * np.pi, 4)); rad = rng.uniform(.5, 1.5, 4)
        x = np.c_[rad * np.cos(ang), rad * np.sin(ang)]
        T = lambda i, j, k: tri_area(x, np.array([[i, j, k]]))[0]
        A = [T(0, 1, 2), T(0, 2, 3), T(0, 1, 3), T(1, 2, 3)]
        if min(A) < 1e-3: continue
        dm = np.array([-A[3], A[1], -A[2], A[0]]) / 3
        a = np.array([A[0] + A[1], A[0], A[0] + A[1], A[1]]) / 3
        g = a + rng.uniform(.05, 2, 4)
        u = euler_states(4, rng)
        check_case(g, dm, u, worst, trial); worst['cases'] += 1

    # 2. multi-flip cavities from real Delaunay rebuilds of moving jittered points
    for trial in range(60):
        n = 12; h = 1 / n
        base = np.stack(np.meshgrid(np.arange(n), np.arange(n)), -1).reshape(-1, 2) * h + h / 2
        x0 = base + rng.uniform(-.3, .3, base.shape) * h
        x1 = x0 + rng.normal(size=x0.shape) * .25 * h
        t0 = Delaunay(x0).simplices; t1 = Delaunay(x1).simplices
        # the flip is applied at time 1 positions: old connectivity t0 pulled to x1 must be valid
        if np.any(np.abs(tri_area(x1, t0)) < 1e-12) or np.any(np.sign(tri_area(x1, t0)) != np.sign(tri_area(x0, t0))):
            continue
        u_all = euler_states(len(x1), rng, contrast=2)
        m_old = np.zeros(len(x1))
        for t in t0:
            m_old[t] += abs(tri_area(x1, np.array([t]))[0]) / 3
        for nodes, a, b in cavities(x1, t0, t1):
            check_case(m_old[nodes], b - a, u_all[nodes], worst, ('multi', trial))
            worst['multi'] += 1

    # 3. uniform state and affine conserved fields are unchanged with theta = 1
    for trial in range(500):
        ang = np.sort(rng.uniform(0, 2 * np.pi, 4)); x = np.c_[np.cos(ang), np.sin(ang)]
        T = lambda i, j, k: tri_area(x, np.array([[i, j, k]]))[0]
        A = [T(0, 1, 2), T(0, 2, 3), T(0, 1, 3), T(1, 2, 3)]
        if min(A) < 1e-2: continue
        dm = np.array([-A[3], A[1], -A[2], A[0]]) / 3; g = np.array([A[0] + A[1], A[0], A[0] + A[1], A[1]]) / 3 + .5
        uni = np.tile(euler_states(1, rng, 1), (4, 1))
        s, out, diag = transfer(g, dm, uni); assert s == 0 and diag[0] == 1
        assert np.allclose(out, uni, rtol=1e-13, atol=0)
        grad = rng.normal(size=(2, 4)) * .05; c0 = np.array([2., .1, -.1, 5.])
        aff = c0 + x @ grad                                # affine in all conserved components
        s, out, diag = transfer(g, dm, aff); assert s == 0 and diag[0] == 1
        assert np.allclose(out, aff, rtol=1e-12, atol=1e-14)
        # high endpoint invertible: flip, then reverse from the new masses
        u = euler_states(4, rng, 0.3)
        s, mid, d1 = transfer(g, dm, u, dmp_relax=-1, entropy=0)
        if d1[0] == 1:
            s, back, d2 = transfer(g + dm, -dm, mid, dmp_relax=-1, entropy=0)
            if d2[0] == 1:
                assert np.allclose(back, u, rtol=1e-12, atol=1e-14)

    # 4. extreme contrasts: Sedov-like hot node among cold ones, counter-streaming flow
    sedov = np.array([[1, 0, 0, 100.], [1, 0, 0, 1e-6], [1, 0, 0, 1e-6], [1, 0, 0, 1e-6]])
    stream = np.array([[1, 5, 0, 12.6], [1, -5, 0, 12.6], [1, 5, 0, 12.6], [1, -5, 0, 12.6]])
    for name, u in (('hot donor', sedov), ('hot receiver', sedov[[1, 0, 2, 3]]), ('counter-streaming', stream)):
        g = np.array([.5, .25, .5, .25]) + .1; dm = np.array([-1, 1, -1, 1]) / 6
        out, diag = check_case(g, dm, u.astype(float), worst, name)
        if name == 'hot receiver':
            # the uniform shift removes D_E/M from the cold nodes: inadmissible, so theta < 1
            assert diag[0] < 1, name

    print(f"PASS: {worst['cases']} single flips + {worst['multi']} Delaunay cavities; conservation "
          f"{worst['conservation']:.2e}, reference {worst['reference']:.2e}, limited {int(worst['limited'])} "
          f"(min theta {worst['theta_min']:.3g}); uniform/affine unchanged with theta=1; high endpoint invertible; "
          "extreme contrasts admissible within density hull and entropy minimum")


if __name__ == '__main__':
    main()
