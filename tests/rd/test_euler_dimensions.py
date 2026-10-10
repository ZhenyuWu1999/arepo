#!/usr/bin/env python3
"""Compile shared production C; compare spectral K against flux derivatives.

The oracle uses complex-step Euler Jacobians and polynomial spectral
projectors, not the entry-by-entry formula implemented in rd_euler.c.
Tests cover both dimensions, mesh-relative shifts, rotations, geometric
scaling, two independent shear modes and singular compatible upwind solves.
"""
import ctypes
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np

REPO = Path(__file__).resolve().parents[2]


class SolveInfo(ctypes.Structure):
    _fields_ = [('rank', ctypes.c_int), ('used_svd', ctypes.c_int),
                ('exact_singular', ctypes.c_int), ('pivot_ratio', ctypes.c_double)]


def flux(u, normal, gamma):
    rho, momentum, energy = u[0], u[1:-1], u[-1]
    velocity = momentum/rho
    pressure = (gamma-1)*(energy-.5*np.dot(momentum, momentum)/rho)
    vn = np.dot(velocity, normal)
    return np.r_[rho*vn, momentum*vn+pressure*normal, (energy+pressure)*vn]


def main():
    rng = np.random.default_rng(20261010)
    ptr = np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')
    with tempfile.TemporaryDirectory(prefix='rd_euler_dimensions_') as tmp:
        so = Path(tmp)/'kernels.so'
        blas = Path('/opt/homebrew/opt/openblas')
        libs = ['-I'+str(blas/'include'), '-L'+str(blas/'lib'), '-lopenblas'] if blas.exists() else ['-llapacke', '-llapack', '-lblas']
        subprocess.run([os.environ.get('CC', 'cc'), '-std=c99', '-O2', '-shared', '-fPIC',
                        str(REPO/'src/hydro/rd_euler.c'), str(REPO/'src/hydro/rd_linalg.c'),
                        *libs, '-o', str(so)], check=True)
        lib = ctypes.CDLL(str(so))
        lib.rd_euler_spectral_matrix.argtypes = [ctypes.c_int, ptr, ctypes.c_double, ctypes.c_double,
                                                ctypes.c_double, ptr, ctypes.c_double, ptr, ptr]
        lib.rd_euler_spectral_matrix.restype = ctypes.c_int
        lib.rd_upwind_solve.argtypes = [ctypes.c_int, ptr, ptr, ctypes.c_int, ctypes.c_double,
                                       ctypes.c_int, ctypes.POINTER(SolveInfo)]
        lib.rd_upwind_solve.restype = ctypes.c_int

        def k_matrix(d, v, h, c, gamma, normal, measure, lambdas):
            out = np.empty((d+2, d+2))
            assert lib.rd_euler_spectral_matrix(d, np.ascontiguousarray(v), h, c, gamma,
                                                np.ascontiguousarray(normal), measure,
                                                np.ascontiguousarray(lambdas), out) == 0
            return out

        worst = 0.
        for d in (2, 3):
            n = d+2
            eye = np.eye(n)
            for case in range(400):
                gamma = (1.4, 5/3)[case % 2]
                v = rng.uniform(-2, 2, d) if case % 10 else np.zeros(d)
                rho, p = rng.uniform(.3, 2, 2)
                c = np.sqrt(gamma*p/rho)
                h = gamma/(gamma-1)*p/rho+.5*v@v
                normal = rng.normal(size=d); normal /= np.linalg.norm(normal)
                measure = 10**rng.uniform(-3, 2)
                shift = v@normal if case % 7 == 0 else rng.uniform(-2, 2)
                lam = np.array([v@normal+c-shift, v@normal-c-shift, v@normal-shift])
                u = np.r_[rho, rho*v, p/(gamma-1)+.5*rho*(v@v)]
                jac = np.column_stack([np.imag(flux(u.astype(complex)+1e-30j*eye[k], normal, gamma))/1e-30 for k in range(n)])
                b = (jac-(v@normal)*eye)/c
                projectors = [.5*(b@b+b), .5*(b@b-b), eye-b@b]
                rot, _ = np.linalg.qr(rng.normal(size=(d, d)))
                transform = np.eye(n); transform[1:-1, 1:-1] = rot
                matrices = []
                for eigenvalues in (np.maximum(lam, 0), np.minimum(lam, 0), lam):
                    got = k_matrix(d, v, h, c, gamma, normal, measure, eigenvalues)
                    want = measure/d*sum(l*p for l, p in zip(eigenvalues, projectors))
                    scale = max(1., np.max(abs(want)))
                    worst = max(worst, np.max(abs(got-want))/scale)
                    np.testing.assert_allclose(got, want, rtol=2e-12, atol=2e-12*scale)
                    rotated = k_matrix(d, rot@v, h, c, gamma, rot@normal, measure, eigenvalues)
                    np.testing.assert_allclose(rotated, transform@got@transform.T, rtol=2e-12, atol=2e-12*scale)
                    scaled = k_matrix(d, v, h, c, gamma, normal, 3*measure, eigenvalues)
                    np.testing.assert_allclose(scaled, 3*got, rtol=2e-14, atol=2e-14*scale)
                    matrices.append(got)
                np.testing.assert_allclose(matrices[0]+matrices[1], measure/d*(jac-shift*eye), rtol=2e-12, atol=2e-12*scale)

            # The full 3D operator restricted to planar flow reduces to 2D
            # after allowing for the different geometric factor 1/d.
            if d == 3:
                v = np.array([.3, -.2]); normal = np.array([.6, .8])
                c = 1.1; h = c*c/.4+.5*v@v
                lambdas = np.maximum(np.array([v@normal+c, v@normal-c, v@normal]), 0)
                two = k_matrix(2, v, h, c, 1.4, normal, .7, lambdas)
                three = k_matrix(3, np.r_[v, 0.], h, c, 1.4, np.r_[normal, 0.], .7, lambdas)
                np.testing.assert_allclose(three[np.ix_([0, 1, 2, 4], [0, 1, 2, 4])]*1.5, two, atol=2e-15)

            # LU and SVD (including several RHS columns) on independent
            # known-rank systems. An incompatible RHS must remain detectable.
            for rank in (n, n-1):
                q, _ = np.linalg.qr(rng.normal(size=(n, n)))
                diagonal = np.arange(1., n+1); diagonal[rank:] = 0
                s = np.ascontiguousarray(q@np.diag(diagonal)@q.T)
                target = rng.normal(size=(n, 3)); rhs = np.ascontiguousarray(s@target)
                original = rhs.copy(); info = SolveInfo()
                assert lib.rd_upwind_solve(n, s, rhs, 3, -1., 0, ctypes.byref(info)) == 0
                assert info.rank == rank
                np.testing.assert_allclose(s@rhs, original, atol=5e-14)
                if rank < n:
                    assert info.used_svd
                    rhs = np.ascontiguousarray(q[:, -1, None]); original = rhs.copy()
                    assert lib.rd_upwind_solve(n, s, rhs, 1, -1., 1, ctypes.byref(info)) == 0
                    assert np.linalg.norm(s@rhs-original) > .9
        print(f'2D/3D production K: 800 states, all splits, rotations, scales; max normalized defect={worst:.3e}; LU/SVD PASS')


if __name__ == '__main__':
    main()
