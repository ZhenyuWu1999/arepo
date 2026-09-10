#!/usr/bin/env python3
"""Independent scalar ALE/N ledger audit on a fixed periodic triangulation.

This is an algorithm discriminator, not an Euler/MPI validation. It reproduces
the concentrated N hierarchy's geometric close, frozen-star predictor, temporal
mass correction and optional Arpaia storage rebase. Exact integrals of a P1
scalar and linear vertex trajectories allow topology and quadrature errors to
be excluded. Requires NumPy and SciPy. Prints machine-readable measurements.
"""
import json
import numpy as np
from scipy.spatial import Delaunay


def mesh(n=8):
    rng = np.random.default_rng(20260908)
    xy = (np.indices((n, n)).reshape(2, -1).T + 0.5) / n
    xy += rng.uniform(-0.18, 0.18, xy.shape) / n
    shifts = np.array([(i, j) for i in (-1, 0, 1) for j in (-1, 0, 1)])
    tiled = (xy[None, :, :] + shifts[:, None, :]).reshape(-1, 2)
    indices = np.tile(np.arange(len(xy)), len(shifts))
    triang = Delaunay(tiled).simplices
    centres = tiled[triang].mean(axis=1)
    triang = triang[np.all((centres >= 0) & (centres < 1), axis=1)]
    ids = indices[triang]
    xtri = tiled[triang].copy()
    for k in range(len(ids)):
        if area(xtri[k:k+1])[0] < 0:
            ids[k, [1, 2]] = ids[k, [2, 1]]
            xtri[k, [1, 2]] = xtri[k, [2, 1]]
    assert len(ids) == 2 * len(xy)
    return xy, ids, xtri


def area(x):
    a, b = x[:, 1] - x[:, 0], x[:, 2] - x[:, 0]
    return 0.5 * (a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0])


def scatter(ids, values, n):
    ans = np.zeros(n)
    np.add.at(ans, ids.ravel(), np.broadcast_to(values, ids.shape).ravel())
    return ans


def residual(x, sigma, u):
    # A grad(lambda_i) = one half the inward normal of the opposite edge.
    edge = np.roll(x, -1, axis=1) - np.roll(x, -2, axis=1)
    agrad = np.stack((edge[:, :, 1], -edge[:, :, 0]), axis=2) / 2
    relative = np.array([0.31, -0.17]) - sigma.mean(axis=1)
    k = np.einsum('tij,tj->ti', agrad, relative)
    kp, km = np.maximum(k, 0), np.minimum(k, 0)
    inflow = (km * u).sum(axis=1) / km.sum(axis=1)
    return kp * (u - inflow[:, None])


def run(form, H, mixed=True, uniform=False):
    assert form in ('campoli', 'arpaia', 'arpaia_predictor_endpoint_commit')
    xy, ids, xinitial = mesh()
    n = len(xy)
    x, y = xy.T
    sigma = np.column_stack((0.19*np.sin(2*np.pi*y)+0.11*np.cos(2*np.pi*x),
                             0.13*np.sin(2*np.pi*x)+0.07*np.cos(2*np.pi*y)))
    u = 1 + 0.16*np.sin(2*np.pi*x) + 0.12*np.cos(2*np.pi*(x+y))
    if uniform:
        u[:] = 1
    bins = np.where(x < 0.5, 1, 2) if mixed else np.ones(n, dtype=int)
    tb = bins[ids].min(axis=1)
    star = bins.copy()
    np.minimum.at(star, ids.ravel(), np.repeat(tb, 3))
    live = bins == star
    hbase = H / bins.max()
    g = scatter(ids, area(xinitial)[:, None]/3, n)
    q = g*u
    q0 = q.sum()
    predicted_extra = 0.0
    max_basis = 0.0
    for tick in range(1, int(bins.max())+1):
        t = tick*hbase
        xn = xinitial + t*sigma[ids]
        endpoint = scatter(ids, area(xn)[:, None]/3, n)
        due = tick % tb == 0
        active = tick % bins == 0
        stage_live = live & active
        ii = ids[due]
        dt = tb[due]*hbase
        vel = sigma[ii]
        xp = xn[due]
        xm = xp - 0.5*dt[:, None, None]*vel
        xo = xp - dt[:, None, None]*vel
        ao, am, ap = area(xo), area(xm), area(xp)
        assert min(ao.min(), am.min(), ap.min()) > 0
        dg = scatter(ii, ((ap-ao)/3)[:, None], n)
        q += dg*u
        g += dg
        close = np.where(active, endpoint-g, 0)
        max_basis = max(max_basis, float(np.max(np.abs(close))))
        q += close*u
        g[active] = endpoint[active]
        de = am+(ap-ao)/2 if form != 'campoli' else ap
        divisor = scatter(ii, (de/3)[:, None], n)
        if form == 'arpaia':
            q[stage_live] *= divisor[stage_live]/endpoint[stage_live]
        r0 = residual(xm, vel, u[ii])
        predictor = scatter(ii, -dt[:, None]*r0, n)
        du = np.zeros(n)
        du[stage_live] = predictor[stage_live]/divisor[stage_live]
        r1 = residual(xm, vel, (u+du)[ii])
        k = scatter(ii, -0.5*dt[:, None]*(r0+r1)
                    + ((ap-ao)/6)[:, None]*du[ii], n)
        q += k
        if form == 'arpaia':
            predicted_extra += np.sum((endpoint[stage_live]/divisor[stage_live]-1)*k[stage_live])
            q[stage_live] *= endpoint[stage_live]/divisor[stage_live]
        # The proposed third form uses the Arpaia predictor divisor but keeps
        # physical Q in endpoint storage throughout. It is not the existing
        # Arpaia implementation and is not claimed to reproduce it exactly.
        u[active] = q[active]/endpoint[active]
    return dict(form=form, H=H, mixed=mixed, uniform=uniform,
                mass_change=float(q.sum()-q0), predicted_rebase_defect=float(predicted_extra),
                attribution_error=float(q.sum()-q0-predicted_extra),
                max_basis_close=max_basis, min_u=float(u.min()))


if __name__ == '__main__':
    results = [run(form, H, mixed, uniform)
               for mixed in (False, True)
               for uniform in (False, True)
               for H in (0.02, 0.01, 0.005)
               for form in ('campoli', 'arpaia', 'arpaia_predictor_endpoint_commit')]
    print(json.dumps(results, indent=2))
    for r in results:
        assert r['max_basis_close'] < 2e-15, r
        assert abs(r['attribution_error']) < 2e-14, r
        if r['form'] != 'arpaia' or r['uniform']:
            assert abs(r['mass_change']) < 2e-14, r
    assert any(abs(r['mass_change']) > 1e-9 for r in results if r['form'] == 'arpaia' and not r['uniform'])
