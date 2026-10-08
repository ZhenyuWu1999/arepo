#!/usr/bin/env python3
"""Compiled checks for the LDA/HLLC blend helpers (rd_hllc.h, rd_lda_rusanov.h).

1. On a jittered periodic triangulation with random strong-contrast states and
   mesh velocities, edge-HLLC + half-split Gauss3 edge terms has element totals
   equal to an independent Gauss3 ALE contour integral.
2. The split edge terms cancel at every node: the assembled nodal low-order
   update equals edge-HLLC alone to roundoff (its positivity argument holds).
3. The local-bounds limiter returns ell in [0,1] whose state satisfies the
   density and K=p/rho^gamma bounds, and no larger ell does.
Kernel tests only, not a moving-mesh theorem.
"""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import numpy as np

REPO = Path(__file__).resolve().parents[2]
XQ = np.array([0.11270166537925831148, .5, 0.88729833462074168852]); WQ = np.array([5/18, 4/9, 5/18])


def flux(u, gamma):
    v = u[1:3]/u[0]; p = (gamma-1)*(u[3]-.5*u[0]*v@v)
    f = np.outer(v, u); f[0, 1] += p; f[1, 2] += p; f[:, 3] += p*v
    return f


def gauss_total(u, n, w, gamma):
    """Independent Gauss3 contour of G=F-U(x)w with inward opposite normals n_j."""
    total = np.zeros(4)
    for j in range(3):
        a, b = (j+1) % 3, (j+2) % 3
        for x, wq in zip(XQ, WQ):
            uq = (1-x)*u[a]+x*u[b]
            total -= wq*(flux(uq, gamma).T@n[j] - (w@n[j])*uq)
    return total


def main():
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        (folder/'k.c').write_text(
            '#include "rd_hllc.h"\n#include "rd_lda_rusanov.h"\n'
            'double low(double *u,double *n,double *w,double g,double *p,double *r,double *c,double *s,'
            'double *nx,double *ny,double *m,int split){double a=rd_hllc_residual((const double (*)[4])u,'
            '(const double (*)[2])n,w,g,p,(double (*)[3])r,c,s); if(split) rd_hllc_gauss_edge_split('
            '(const double (*)[4])u,nx,ny,m,g,(double (*)[3])r,p,s); return a;}\n'
            'double lim(double *q,double *dq,double area,double *b,double g){return rd_lr_limit_bounds(q,dq,area,b,g);}\n'
            'int ok(double *q,double *dq,double e,double area,double *b,double g){return rd_lr_bounds_ok(q,dq,e,area,b,g);}\n')
        lib = folder/'k.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-O2', '-std=c11', '-Wall', '-Werror', '-Wno-unused-function',
                        '-I'+str(REPO/'src/hydro'), str(folder/'k.c'), '-o', str(lib), '-lm'], check=True)
        L = ctypes.CDLL(str(lib)); ptr = np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')
        L.low.argtypes = [ptr]*3+[ctypes.c_double]+[ptr]*7+[ctypes.c_int]; L.low.restype = ctypes.c_double
        L.lim.argtypes = [ptr, ptr, ctypes.c_double, ptr, ctypes.c_double]; L.lim.restype = ctypes.c_double
        L.ok.argtypes = [ptr, ptr, ctypes.c_double, ctypes.c_double, ptr, ctypes.c_double]; L.ok.restype = ctypes.c_int
        rng = np.random.default_rng(20260930)
        worst_total = worst_node = 0.
        for trial in range(60):
            m = 6; h = 1/m; gamma = (1.4, 5/3)[trial % 2]
            base = np.array([(i*h, j*h) for j in range(m) for i in range(m)])
            xy = base + rng.uniform(-.2, .2, base.shape)*h
            rho = 10.**rng.uniform(-3, 2, m*m); p = 10.**rng.uniform(-6, 2, m*m)
            vel = rng.normal(size=(m*m, 2))*2; sig = rng.normal(size=(m*m, 2))*2
            U = np.column_stack((rho, rho[:, None]*vel, p/(gamma-1)+.5*rho*np.sum(vel**2, 1)))
            tris = []
            for j in range(m):
                for i in range(m):
                    a, b, c, d = j*m+i, j*m+(i+1) % m, ((j+1) % m)*m+(i+1) % m, ((j+1) % m)*m+i
                    tris += [(a, b, c), (a, c, d)]
            node_split = np.zeros((m*m, 4)); node_plain = np.zeros((m*m, 4)); scale_node = np.zeros(m*m)
            for t in tris:
                x0 = xy[t[0]]; x = [x0]+[x0+((xy[k]-x0+.5) % 1-.5) for k in t[1:]]   # periodic unwrap
                x = np.array(x)
                assert np.cross(x[1]-x[0], x[2]-x[0]) > 0
                e = np.roll(x, -1, 0)-np.roll(x, -2, 0); n = np.ascontiguousarray(np.column_stack((e[:, 1], -e[:, 0])))  # solver: inward
                mag = np.hypot(n[:, 0], n[:, 1]); nx = n[:, 0]/mag; ny = n[:, 1]/mag
                u = np.ascontiguousarray(U[list(t)]); w = np.ascontiguousarray(sig[list(t)].mean(0))
                out = {}
                for split in (0, 1):
                    phi, res, coeff, s = np.zeros(4), np.zeros((4, 3)), np.zeros(3), np.zeros(1)
                    assert L.low(u, n, w, gamma, phi, res, coeff, s, np.ascontiguousarray(nx), np.ascontiguousarray(ny),
                                 np.ascontiguousarray(mag), split) > 0
                    out[split] = (phi, res, s[0])
                phi, res, s = out[1]
                ref = gauss_total(u, n, w, gamma)
                d = max(np.max(abs(res.sum(1)-phi)), np.max(abs(phi-ref)))/s
                worst_total = max(worst_total, d); assert d < 1e-13, (trial, d)
                for v, k in enumerate(t):
                    node_split[k] += res[:, v]; node_plain[k] += out[0][1][:, v]; scale_node[k] += s
            d = np.max(abs(node_split-node_plain)/scale_node[:, None])
            worst_node = max(worst_node, d); assert d < 1e-13, (trial, d)

        # Local-bounds limiter.
        worst_ell = 0
        for trial in range(3000):
            gamma = (1.4, 5/3)[trial % 2]; area = 10.**rng.uniform(-3, 0)
            states = []
            for _ in range(rng.integers(2, 8)):
                r = 10.**rng.uniform(-3, 2); v = rng.normal(size=2)*2; pp = 10.**rng.uniform(-6, 2)
                states.append(np.array([r, r*v[0], r*v[1], pp/(gamma-1)+.5*r*v@v]))
            q = states[0]*area
            kk = [(gamma-1)*(s[3]-.5*(s[1]**2+s[2]**2)/s[0])/s[0]**gamma for s in states]
            bound = np.array([min(s[0] for s in states), max(s[0] for s in states), min(kk)])
            dq = rng.normal(size=4)*abs(q)*10.**rng.uniform(-2, 1)
            ell = L.lim(q, dq, area, bound, gamma)
            assert 0 <= ell <= 1, (trial, ell)
            if ell > 0:
                assert L.ok(q, dq, ell, area, bound, gamma), trial
            if ell < 1:
                assert not L.ok(q, dq, min(1, ell*(1+1e-7)+1e-10), area, bound, gamma), trial
            worst_ell = max(worst_ell, ell)
        print(f'PASS: 60 periodic meshes x {2*36} elements: Gauss3 total {worst_total:.2e}, nodal edge-term '
              f'cancellation {worst_node:.2e}; 3000 bounds-limiter cases (ell maximal, bounds held)')


if __name__ == '__main__':
    main()
