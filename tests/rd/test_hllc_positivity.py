#!/usr/bin/env python3
"""Compile the actual rd_hllc.h kernel and check it against independent algebra.

* An independent Python HLLC in the standard flux form (Toro, Einfeldt/Batten
  speeds), assembled on the median-dual faces in laboratory variables.
* Conservation against an independent boundary-flux quadrature.
* Exact zero residual for a uniform state.
* Admissible forward-Euler step at the returned per-vertex coefficient.
* Galilean covariance: shifting velocities and w by b maps residuals by G(b).
* A contact at rest relative to w gives zero residual (Rusanov does not).
* Clockwise vertex order (outward normals from the solver formula) is rejected.
Kernel tests only; not a moving-mesh or topology-change theorem.
"""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import numpy as np

REPO = Path(__file__).resolve().parents[2]


def primitive(u, gamma):
    rho = u[0]; v = u[1:3]/rho
    return rho, v, (gamma-1)*(u[3]-.5*rho*v@v)


def lab_flux(u, w, gamma):
    rho, v, p = primitive(u, gamma)
    g = np.outer(v-w, u)
    g[0, 1] += p; g[1, 2] += p; g[:, 3] += p*v
    return g                          # g[axis, component]


def hllc_flux(ul, ur, nu, w, gamma):
    """Independent HLLC numerical flux through a face moving with w, lab variables."""
    length = np.hypot(*nu); nhat = nu/length
    out = []
    for u in (ul, ur):
        rho, v, p = primitive(u, gamma)
        un = (v-w)@nhat
        out.append((rho, v, p, un, np.sqrt(gamma*p/rho), u))
    (rl, vl, pl, unl, cl, UL), (rr, vr, pr, unr, cr, UR) = out
    hl = (UL[3]+pl)/rl - vl@w + .5*w@w      # frame enthalpy: (E'+p)/rho
    hr = (UR[3]+pr)/rr - vr@w + .5*w@w
    wl, wr = np.sqrt(rl), np.sqrt(rr)
    vroe = (wl*(vl-w)+wr*(vr-w))/(wl+wr); hroe = (wl*hl+wr*hr)/(wl+wr)
    croe = np.sqrt((gamma-1)*(hroe-.5*vroe@vroe)); unroe = vroe@nhat
    sl = min(unl-cl, unr-cr, unroe-croe); sr = max(unl+cl, unr+cr, unroe+croe)
    ss = (pr-pl+rl*unl*(sl-unl)-rr*unr*(sr-unr))/(rl*(sl-unl)-rr*(sr-unr))
    fl = lab_flux(UL, w, gamma).T@nhat; fr = lab_flux(UR, w, gamma).T@nhat

    def star(rho, v, p, un, S, U):
        vs = v-w+(ss-un)*nhat                # frame velocity with normal part replaced by S*
        ef = U[3]-rho*v@w+.5*rho*w@w          # frame total energy E'
        f = rho*(S-un)/(S-ss)
        e_star = f*(ef/rho+(ss-un)*(ss+p/(rho*(S-un))))
        vlab = vs+w
        return np.array([f, f*vlab[0], f*vlab[1], e_star+f*(vs@w)+.5*f*w@w])
    if sl >= 0: flux = fl
    elif sr <= 0: flux = fr
    elif ss >= 0: flux = fl+sl*(star(rl, vl, pl, unl, sl, UL)-UL)
    else: flux = fr+sr*(star(rr, vr, pr, unr, sr, UR)-UR)
    return length*flux, max(abs(sl), abs(sr))


def galilean(b):
    return np.array([[1, 0, 0, 0], [-b[0], 1, 0, 0], [-b[1], 0, 1, 0], [.5*b@b, -b[0], -b[1], 1.]])


def main():
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        src = folder / 'kernel.c'
        src.write_text('#include "rd_hllc.h"\n'
                       'double kernel(double *u,double *n,double *w,double g,double *p,double *r,double *c,double *s) '
                       '{return rd_hllc_residual((const double (*)[4])u,(const double (*)[2])n,w,g,p,(double (*)[3])r,c,s);}\n')
        libpath = folder / 'kernel.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-O2', '-std=c11', '-Wall', '-Werror', '-Wno-unused-function', '-I'+str(REPO/'src/hydro'),
                        str(src), '-o', str(libpath), '-lm'], check=True)
        fn = ctypes.CDLL(str(libpath)).kernel
        ptr = np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')
        fn.argtypes = [ptr, ptr, ptr, ctypes.c_double, ptr, ptr, ptr, ptr]
        fn.restype = ctypes.c_double

        def call(u, normals, w, gamma):
            phi, residual, coeff, scale = np.zeros(4), np.zeros((4, 3)), np.zeros(3), np.zeros(1)
            result = fn(np.ascontiguousarray(u), np.ascontiguousarray(normals), np.ascontiguousarray(w),
                        gamma, phi, residual, coeff, scale)
            return result, phi, residual, coeff, scale[0]

        rng = np.random.default_rng(20260930)
        worst = dict(conservation=0., reference=0., galilean=0.)
        min_margin = np.inf
        trials = 4000
        for trial in range(trials):
            xy = rng.normal(size=(3, 2))
            d1, d2 = xy[1]-xy[0], xy[2]-xy[0]
            if d1[0]*d2[1]-d1[1]*d2[0] < 0:
                xy = xy[::-1].copy()
            edges = np.roll(xy, -1, axis=0) - np.roll(xy, -2, axis=0)   # x_{j+1} - x_{j+2}
            normals = np.column_stack((edges[:, 1], -edges[:, 0]))       # solver formula: inward for CCW
            rho = 10.**rng.uniform(-3, 3, 3)
            pressure = 10.**rng.uniform(-6, 3, 3)
            velocity = rng.normal(size=(3, 2))*3
            w = rng.normal(size=2)*3
            gamma = (1.4, 5/3)[trial % 2]
            u = np.column_stack((rho, rho[:, None]*velocity, pressure/(gamma-1)+.5*rho*np.sum(velocity**2, axis=1)))
            uniform = trial % 10 == 0
            if uniform:
                u[:] = u[0]
            result, phi, residual, coeff, scale = call(u, normals, w, gamma)
            assert result > 0 and np.all(coeff > 0), trial

            # Conservation against an independent boundary quadrature.
            flux = np.array([lab_flux(u[j], w, gamma) for j in range(3)])
            expected = .5*np.einsum('jak,ja->k', flux, normals)
            abs_scale = max(float(np.sum(abs(flux)*abs(normals[:, :, None]))), scale, 1e-30)
            defect = max(np.max(abs(phi-expected)), np.max(abs(residual.sum(axis=1)-phi)))/abs_scale
            worst['conservation'] = max(worst['conservation'], defect)
            assert defect < 1e-13, (trial, defect)

            # Independent HLLC assembly on the median-dual faces.
            reference = np.zeros((3, 4)); ref_coeff = np.zeros(3)
            for i in range(3):
                for j in range(3):
                    if i == j: continue
                    nu = (normals[j]-normals[i])/6
                    h, s = hllc_flux(u[i], u[j], nu, w, gamma)
                    reference[i] += h - lab_flux(u[i], w, gamma).T@nu
                    ref_coeff[i] += np.hypot(*nu)*s
            if uniform:
                assert np.array_equal(residual, np.zeros_like(residual)), trial
            else:
                rel = np.max(abs(residual.T-reference))/abs_scale
                worst['reference'] = max(worst['reference'], rel)
                assert rel < 1e-10, (trial, rel)
                # Roe sound speed is a cancelling difference for cold, fast states;
                # the two implementations order it differently (seen: 1.1e-12).
                assert np.allclose(coeff, ref_coeff, rtol=1e-10, atol=0), trial

            # Unit nodal mass: dt*coeff_i <= 1 must give admissible states.
            dt = rng.uniform(.01, .999)/np.max(coeff)
            new = u - dt*residual.T
            internal = new[:, 3] - .5*np.sum(new[:, 1:3]**2, axis=1)/new[:, 0]
            assert np.all(new[:, 0] > 0) and np.all(internal > 0), trial
            min_margin = min(min_margin, float(np.min(internal/(u[:, 3]-.5*np.sum(u[:, 1:3]**2, axis=1)/u[:, 0]))))

            # Galilean covariance of the complete element residual.
            if not uniform:
                b = rng.normal(size=2)*3
                shifted = u@galilean(b).T
                result2, phi2, residual2, coeff2, _ = call(shifted, normals, w-b, gamma)
                assert result2 > 0
                rel = np.max(abs(residual2 - galilean(b)@residual))/abs_scale
                worst['galilean'] = max(worst['galilean'], rel)
                assert rel < 1e-10, (trial, rel)
                assert np.allclose(coeff2, coeff, rtol=1e-10), trial

        # Contact at rest relative to w: HLLC gives zero, Rusanov diffuses it.
        normals = np.array([[-1., -1.], [1., 0.], [0., 1.]])
        w = np.array([.7, -.3]); gamma = 5/3
        rho = np.array([1., .03, 4.])
        u = np.column_stack((rho, rho[:, None]*w, np.full(3, 1.6/(gamma-1))+.5*rho*(w@w)))
        _, _, residual, _, scale = call(u, normals, w, gamma)
        assert np.max(abs(residual)) <= 1e-14*scale, residual

        # Clockwise vertices with the solver's normal formula give outward
        # normals and are rejected.  (A global sign flip of CCW normals cannot
        # be detected from normals alone: it is the 180-degree rotated triangle.)
        cw = np.array([[0., 0.], [0., 1.], [1., 0.]])
        edges = np.roll(cw, -1, axis=0) - np.roll(cw, -2, axis=0)
        assert call(u, np.column_stack((edges[:, 1], -edges[:, 0])), w, gamma)[0] < 0
        bad = u.copy(); bad[0, 0] = -1
        assert call(bad, normals, w, gamma)[0] < 0
        print(f'PASS: {trials} compiled HLLC kernels; conservation {worst["conservation"]:.2e}, '
              f'independent HLLC {worst["reference"]:.2e}, Galilean {worst["galilean"]:.2e}, '
              f'min internal-energy ratio after CFL-limited step {min_margin:.3e}; '
              'uniform exact, resting contact exact, orientation guard')


if __name__ == '__main__':
    main()
