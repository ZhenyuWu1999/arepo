#!/usr/bin/env python3
"""Compile the actual C kernel; verify flux consistency and its convex update.

Random triangles/states include strong pressure contrasts, moving frames and
near-CFL-limit forward steps. These are kernel tests, not a moving-mesh theorem.
"""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import numpy as np

REPO = Path(__file__).resolve().parents[2]


def main():
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        src = folder / 'kernel.c'
        src.write_text('#include "rd_rusanov.h"\n'
                       'double kernel(double *u,double *n,double *w,double g,double *p,double *r,double *s) '
                       '{return rd_rusanov_residual((const double (*)[4])u,(const double (*)[2])n,w,g,p,(double (*)[3])r,s);}\n')
        libpath = folder / 'kernel.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-O2', '-std=c11', '-I'+str(REPO/'src/hydro'),
                        str(src), '-o', str(libpath), '-lm'], check=True)
        fn = ctypes.CDLL(str(libpath)).kernel
        ptr = np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')
        fn.argtypes = [ptr, ptr, ptr, ctypes.c_double, ptr, ptr, ptr]
        fn.restype = ctypes.c_double
        rng = np.random.default_rng(20260929)
        worst = 0.
        for trial in range(5000):
            xy = rng.normal(size=(3, 2))
            edges = np.roll(xy, -1, axis=0) - np.roll(xy, -2, axis=0)
            normals = np.ascontiguousarray(np.column_stack((-edges[:, 1], edges[:, 0])))
            rho = 10.**rng.uniform(-3, 3, 3)
            pressure = 10.**rng.uniform(-6, 3, 3)
            velocity = rng.normal(size=(3, 2))*3
            w = rng.normal(size=2)*3
            gamma = (1.4, 5/3)[trial % 2]
            u = np.column_stack((rho, rho[:, None]*velocity,
                                 pressure/(gamma-1)+.5*rho*np.sum(velocity**2, axis=1)))
            if trial % 10 == 0:
                u[:] = u[0]
            phi, residual, scale = np.zeros(4), np.zeros((4, 3)), np.zeros(1)
            alpha = fn(u, normals, w, gamma, phi, residual, scale)
            assert alpha > 0, trial
            # Independent boundary-flux quadrature, using inward opposite normals.
            flux = velocity[:, :, None]*u[:, None, :]
            if trial % 10 == 0:
                velocity[:] = velocity[0]; pressure[:] = pressure[0]
                flux = velocity[:, :, None]*u[:, None, :]
            flux[:, 0, 1] += pressure; flux[:, 1, 2] += pressure
            flux[:, :, 3] += pressure[:, None]*velocity
            flux -= w[None, :, None]*u[:, None, :]
            expected = .5*np.einsum('jak,ja->k', flux, normals)
            abs_scale = max(float(np.sum(abs(flux)*abs(normals[:, :, None]))), float(scale[0]), 1e-30)
            defect = max(np.max(abs(phi-expected)), np.max(abs(residual.sum(axis=1)-phi)))/abs_scale
            worst = max(worst, defect)
            assert defect < 1e-13, (trial, defect)
            # Unit nodal mass. Each vertex receives two bars, weight 2dt alpha/3 each.
            dt = rng.uniform(.01, .999)*3/(4*alpha)
            new = u - dt*residual.T
            internal = new[:, 3] - .5*np.sum(new[:, 1:3]**2, axis=1)/new[:, 0]
            assert np.all(new[:, 0] > 0) and np.all(internal > 0), trial
            if trial % 10 == 0:
                assert np.array_equal(residual, np.zeros_like(residual))
        bad = u.copy(); bad[0, 0] = -1
        assert fn(bad, normals, w, gamma, phi, residual, scale) < 0
        print(f'PASS: 5000 compiled Rusanov kernels; positivity, uniform state, independent flux/conservation; worst={worst:.3e}')


if __name__ == '__main__':
    main()
