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


DoublePtr = ctypes.POINTER(ctypes.c_double)


class ElementGeometry(ctypes.Structure):
    _fields_ = [('ndim', ctypes.c_int), ('measure', ctypes.c_double),
                ('unit_normal', DoublePtr), ('face_measure', DoublePtr)]


class ElementInput(ctypes.Structure):
    _fields_ = [('geometry', ElementGeometry), ('conserved', DoublePtr)]


class ElementOutput(ctypes.Structure):
    _fields_ = [('total', DoublePtr), ('spatial', DoublePtr), ('temporal', DoublePtr)]


def cptr(array):
    return array.ctypes.data_as(DoublePtr)


def main():
    ptr = np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')
    rng = np.random.default_rng(73913)
    with tempfile.TemporaryDirectory(prefix='rd_simplex_') as tmp:
        so = Path(tmp)/'simplex.so'
        blas = Path('/opt/homebrew/opt/openblas')
        libs = ['-I'+str(blas/'include'), '-L'+str(blas/'lib'), '-lopenblas'] if blas.exists() else ['-llapacke', '-llapack', '-lblas']
        subprocess.run([os.environ.get('CC', 'cc'), '-std=c99', '-O2', '-shared', '-fPIC',
                        str(REPO/'src/hydro/rd_euler.c'), str(REPO/'src/hydro/rd_element.c'),
                        str(REPO/'src/hydro/rd_linalg.c'),
                        str(REPO/'src/mesh/rd_simplex_geometry.c'), *libs, '-o', str(so)], check=True)
        lib = ctypes.CDLL(str(so))
        lib.rd_simplex_geometry.argtypes = [ctypes.c_int, ptr, ptr, ptr, ptr]
        lib.rd_simplex_geometry.restype = ctypes.c_int
        lib.rd_euler_n_residual.argtypes = [ctypes.c_int, ptr, ptr, ptr, ctypes.c_double, ctypes.c_double,
                                           ctypes.c_int, ptr, ptr, ctypes.POINTER(Diagnostics)]
        lib.rd_euler_n_residual.restype = ctypes.c_int
        lib.rd_euler_lda_residual.argtypes = [ctypes.c_int, ptr, ptr, ptr, ctypes.c_double, ctypes.c_double,
                                             ctypes.c_int, ptr, ptr, ptr, ptr, ctypes.POINTER(Diagnostics)]
        lib.rd_euler_lda_residual.restype = ctypes.c_int
        lib.rd_element_roe_residual.argtypes = [ctypes.POINTER(ElementInput), ctypes.c_int,
                                               ctypes.c_double, ctypes.c_double, ctypes.c_int, DoublePtr,
                                               ctypes.POINTER(ElementOutput), ctypes.POINTER(Diagnostics)]
        lib.rd_element_roe_residual.restype = ctypes.c_int
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

                # The common boundary is component-major, while the pure
                # Euler kernel is vertex-major. Check exact adapter identity
                # in both dimensions, including non-square 4x3 / 5x4 arrays.
                element = ElementInput(ElementGeometry(d, abs(vol[0]), cptr(normal), cptr(area)), cptr(u))
                common_phi = np.empty(nc); common = np.empty((nc, nv))
                common_time = np.full((nc, nv), 912.)
                output = ElementOutput(cptr(common_phi), cptr(common), cptr(common_time))
                adapter_diag = Diagnostics()
                assert lib.rd_element_roe_residual(ctypes.byref(element), 0, gamma, -1., 0, None,
                                                   ctypes.byref(output), ctypes.byref(adapter_diag)) == 0
                np.testing.assert_array_equal(common_phi, phi)
                np.testing.assert_array_equal(common, residual.T)
                np.testing.assert_array_equal(common_time, 912.)
                assert adapter_diag.solve.rank == diag.solve.rank
                assert adapter_diag.conservation_defect == diag.conservation_defect

                # Independent LDA/F1 oracle: complex-step flux Jacobian and
                # spectral polynomials, avoiding production matrix entries.
                z = np.column_stack([np.sqrt(rho), np.sqrt(rho)[:, None]*velocity, (energy+pressure)/np.sqrt(rho)])
                mean = z.mean(axis=0); vel = mean[1:-1]/mean[0]; h = mean[-1]/mean[0]
                cs = np.sqrt((gamma-1)*(h-.5*vel@vel)); eye = np.eye(nc)
                roe = np.r_[1., vel, (h+(gamma-1)/2*(vel@vel))/gamma]
                plus, minus = [], []
                for nn, aa in zip(normal, area):
                    jac = np.column_stack([np.imag(flux(roe.astype(complex)+1e-30j*eye[k], nn, gamma))/1e-30 for k in range(nc)])
                    b = (jac-vel@nn*eye)/cs
                    projectors = [.5*(b@b+b), .5*(b@b-b), eye-b@b]
                    lam = np.array([vel@nn+cs, vel@nn-cs, vel@nn])
                    plus.append(aa/d*sum(ll*pp for ll, pp in zip(np.maximum(lam, 0), projectors)))
                    minus.append(aa/d*sum(ll*pp for ll, pp in zip(np.minimum(lam, 0), projectors)))
                sm = sum(minus); target = np.ascontiguousarray(rng.normal(size=nc))
                lda_phi = np.empty(nc); lda = np.empty((nv, nc)); f1 = np.empty_like(lda); ld = Diagnostics()
                assert lib.rd_euler_lda_residual(d, u, normal, area, gamma, -1., 0, target,
                                               lda_phi, lda, f1, ctypes.byref(ld)) == 0
                np.testing.assert_allclose(lda_phi, phi, atol=2e-13*scale)
                want = np.array([-kp@np.linalg.lstsq(sm, phi, rcond=None)[0] for kp in plus])
                np.testing.assert_allclose(lda, want, atol=2e-11*scale, rtol=2e-10)
                np.testing.assert_allclose(lda.sum(axis=0), phi, atol=2e-12*scale)
                if ld.solve.rank == nc:
                    want_time = np.array([-kp@np.linalg.solve(sm, target) for kp in plus])
                    np.testing.assert_allclose(f1, want_time, atol=2e-10*max(1., abs(want_time).max()), rtol=2e-10)
                    np.testing.assert_allclose(f1.sum(axis=0), target, atol=2e-11)
                else:
                    np.testing.assert_array_equal(f1, 0.)

                assert lib.rd_element_roe_residual(ctypes.byref(element), 1, gamma, -1., 0, cptr(target),
                                                   ctypes.byref(output), ctypes.byref(adapter_diag)) == 0
                np.testing.assert_array_equal(common_phi, lda_phi)
                np.testing.assert_array_equal(common, lda.T)
                np.testing.assert_array_equal(common_time, f1.T)
                assert adapter_diag.solve.rank == ld.solve.rank
                assert adapter_diag.solve_defect == ld.solve_defect

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
            # Reject mismatched contracts before touching caller buffers.
            for bad in ('dimension', 'measure', 'scheme', 'N_temporal', 'missing_F1_output'):
                common.fill(812.); common_phi.fill(812.)
                element.geometry.ndim = 4 if bad == 'dimension' else d
                element.geometry.measure = 0. if bad == 'measure' else 1.
                output.temporal = DoublePtr() if bad == 'missing_F1_output' else cptr(common_time)
                scheme = 7 if bad == 'scheme' else (1 if bad == 'missing_F1_output' else 0)
                temporal = cptr(target) if bad in ('N_temporal', 'missing_F1_output') else None
                assert lib.rd_element_roe_residual(ctypes.byref(element), scheme, gamma, -1., 0, temporal,
                                                   ctypes.byref(output), ctypes.byref(adapter_diag)) == -1
                np.testing.assert_array_equal(common, 812.)
                np.testing.assert_array_equal(common_phi, 812.)
        print(f'PASS: 700 production triangle/tetra geometries, N/LDA/F1 residuals and exact common-interface layouts; {stagnant} zero-velocity cases (rank 3 in 2D, rank 4 in 3D); {defects}')


if __name__ == '__main__':
    main()
