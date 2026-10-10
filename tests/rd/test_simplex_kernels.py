#!/usr/bin/env python3
"""Production simplex geometry and N residual versus independent face integrals."""
import ctypes
import math
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np

from test_euler_dimensions import REPO, SolveInfo, flux


class Diagnostics(ctypes.Structure):
    _fields_ = [('solve', SolveInfo), ('conservation_defect', ctypes.c_double),
                ('solve_defect', ctypes.c_double), ('roundoff_scale', ctypes.c_double),
                ('max_phi', ctypes.c_double)]


def main():
    ptr = np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')
    rng = np.random.default_rng(73913)
    with tempfile.TemporaryDirectory(prefix='rd_simplex_') as tmp:
        so = Path(tmp)/'simplex.so'
        blas = Path('/opt/homebrew/opt/openblas')
        libs = ['-I'+str(blas/'include'), '-L'+str(blas/'lib'), '-lopenblas'] if blas.exists() else ['-llapacke', '-llapack', '-lblas']
        subprocess.run([os.environ.get('CC', 'cc'), '-std=c99', '-O2', '-shared', '-fPIC',
                        str(REPO/'src/hydro/rd_euler.c'), str(REPO/'src/hydro/rd_linalg.c'),
                        str(REPO/'src/mesh/rd_simplex_geometry.c'), *libs, '-o', str(so)], check=True)
        lib = ctypes.CDLL(str(so))
        lib.rd_simplex_geometry.argtypes = [ctypes.c_int, ptr, ptr, ptr, ptr]
        lib.rd_simplex_geometry.restype = ctypes.c_int
        lib.rd_euler_n_residual.argtypes = [ctypes.c_int, ptr, ptr, ptr, ctypes.c_double, ctypes.c_double,
                                           ctypes.c_int, ptr, ptr, ctypes.POINTER(Diagnostics)]
        lib.rd_euler_n_residual.restype = ctypes.c_int
        defects = dict(closure=0., gradient=0., phi_integral=0., conservation=0., solve=0.)
        stagnant = 0
        for d in (2, 3):
            nv, nc = d+1, d+2
            for case in range(350):
                matrix = rng.normal(size=(d, d))
                while abs(np.linalg.det(matrix)) < .15:
                    matrix = rng.normal(size=(d, d))
                x = np.ascontiguousarray(np.vstack([np.zeros(d), np.eye(d)])@matrix+rng.normal(size=d))
                x = np.ascontiguousarray(x[rng.permutation(nv)])
                vol = np.zeros(1); normal = np.empty((nv, d)); area = np.empty(nv)
                assert lib.rd_simplex_geometry(d, x, vol, normal, area) == 0
                want = np.linalg.det(x[1:]-x[0])/math.factorial(d)
                np.testing.assert_allclose(vol[0], want, rtol=2e-13, atol=1e-14)
                n = normal*area[:, None]
                closure = np.max(abs(n.sum(axis=0)))/area.sum()
                gradient = np.max(abs((x-x[0]).T@n/(d*abs(vol[0]))-np.eye(d)))
                defects['closure'] = max(defects['closure'], closure)
                defects['gradient'] = max(defects['gradient'], gradient)
                assert closure < 1e-14 and gradient < 2e-13

                gamma = (1.4, 5/3)[case % 2]
                rho = rng.uniform(.5, 1.5, nv); pressure = rng.uniform(.5, 1.5, nv)
                velocity = rng.uniform(-.7, .7, (nv, d))
                if case % 5 == 0:
                    velocity[:] = 0
                if case % 10 == 0:
                    rho[:] = 1.; pressure[:] = 1.; velocity[:] = rng.uniform(-1, 1, d)
                energy = pressure/(gamma-1)+.5*rho*(velocity**2).sum(axis=1)
                u = np.ascontiguousarray(np.column_stack([rho, rho[:, None]*velocity, energy]))
                phi = np.empty(nc); residual = np.empty((nv, nc)); diag = Diagnostics()
                assert lib.rd_euler_n_residual(d, u, normal, area, gamma, -1., 0, phi, residual, ctypes.byref(diag)) == 0
                if case % 10 == 5:
                    assert diag.solve.used_svd and diag.solve.rank == nc-1, (d, diag.solve.rank)
                    stagnant += 1
                if case % 10 == 0:
                    np.testing.assert_array_equal(phi, 0.)
                    np.testing.assert_array_equal(residual, 0.)
                scale = max(diag.roundoff_scale, 1.)
                defects['conservation'] = max(defects['conservation'], diag.conservation_defect/scale)
                defects['solve'] = max(defects['solve'], diag.solve_defect/scale)
                np.testing.assert_allclose(residual.sum(axis=0), phi, atol=2e-13*scale)

                # Euler flux is quadratic in Z, so face Gaussian quadrature
                # is an independent exact integral of its divergence.
                z = np.column_stack([np.sqrt(rho), np.sqrt(rho)[:, None]*velocity, (energy+pressure)/np.sqrt(rho)])
                integral = np.zeros(nc)
                for face in range(nv):
                    zface = np.delete(z, face, axis=0)
                    if d == 2:
                        t = np.array([.5-1/np.sqrt(12), .5+1/np.sqrt(12)])
                        bary = np.column_stack([1-t, t])
                    else:
                        bary = np.full((3, 3), 1/6)+np.eye(3)/2
                    for zz in bary@zface:
                        uu = np.r_[zz[0]**2, zz[0]*zz[1:-1],
                                   (zz[0]*zz[-1]+(gamma-1)/2*(zz[1:-1]@zz[1:-1]))/gamma]
                        integral -= area[face]/len(bary)*flux(uu, normal[face], gamma)
                error = np.max(abs(phi-integral))/max(scale, np.max(abs(integral)))
                defects['phi_integral'] = max(defects['phi_integral'], error)
                np.testing.assert_allclose(phi, integral, atol=3e-13*scale)
            # Explicit invalid inputs: collapsed simplex and non-unit normals.
            assert lib.rd_simplex_geometry(d, np.zeros_like(x), vol, normal, area) != 0
            assert lib.rd_euler_n_residual(d, u, np.ascontiguousarray(2*normal), area, gamma, -1., 0,
                                           phi, residual, ctypes.byref(diag)) != 0
        print(f'PASS: 700 production triangle/tetra geometries and N residuals; {stagnant} zero-velocity cases (rank 3 in 2D, rank 4 in 3D); {defects}')


if __name__ == '__main__':
    main()
