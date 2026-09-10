#!/usr/bin/env python3
"""Algebraic discriminators for topology, local clocks, and conservative transfer.

This is not a full Euler solver. The first test integrates the exact residual
of a frozen periodic P1 scalar with zero mesh velocity, isolating triangle
lifetime coverage from geometric/basis errors. The second tests a same-time
four-node Euler representation transfer, including a positivity fallback.
Only NumPy is required; measurements and assertions are reproducible.
"""
import json
import numpy as np


def area(x):
    a, b = x[1] - x[0], x[2] - x[0]
    return (a[0]*b[1] - a[1]*b[0])/2


def periodic_triangles(n=4, flipped=False):
    result = []
    for i in range(n):
        for j in range(n):
            corners = [(i, j), (i+1, j), (i+1, j+1), (i, j+1)]
            xy = np.array(corners, dtype=float)/n
            ids = np.array([(a % n)*n + (b % n) for a, b in corners])
            pairs = [(0, 1, 3), (1, 2, 3)] if flipped and (i, j) == (1, 1) else [(0, 1, 2), (0, 2, 3)]
            result.extend((ids[list(t)], xy[list(t)]) for t in pairs)
    return result


def exact_scalar_residual(triangle, u):
    ids, x = triangle
    edge = np.roll(x, -1, axis=0)-np.roll(x, -2, axis=0)
    agrad = np.column_stack((edge[:, 1], -edge[:, 0]))/2
    return float((agrad @ np.array([.31, -.17])) @ u[ids])


def time_coverage():
    n, h, ticks, flip_tick = 4, .01, 8, 4
    xy = np.indices((n, n)).reshape(2, -1).T/n
    u = 1+.16*np.sin(2*np.pi*xy[:, 0])+.12*np.cos(2*np.pi*(xy[:, 0]+xy[:, 1]))
    old, new = periodic_triangles(n), periodic_triangles(n, True)
    r_old = np.array([exact_scalar_residual(t, u) for t in old])
    r_new = np.array([exact_scalar_residual(t, u) for t in new])
    assert abs(r_old.sum()) < 1e-16 and abs(r_new.sum()) < 1e-16
    out = []
    for fine_id in (5, 9, 10, 6):
        for equal in (True, False):
            bins = np.ones(n*n, dtype=int) if equal else np.full(n*n, ticks)
            bins[fine_id] = 1
            naive = 0.
            fixed = 0.
            clipped = 0.
            for tick in range(1, ticks+1):
                current, residuals = (old, r_old) if tick < flip_tick else (new, r_new)
                for (ids, _), r in zip(current, residuals):
                    interval = int(bins[ids].min())
                    if tick % interval == 0:
                        naive += interval*h*r
                    clipped += h*r
                for (ids, _), r in zip(old, r_old):
                    interval = int(bins[ids].min())
                    if tick % interval == 0:
                        fixed += interval*h*r
            out.append(dict(fine_id_zero_based=fine_id, equal_bins=equal,
                            naive_integrated_residual=naive,
                            fixed_connectivity_integrated_residual=fixed,
                            lifetime_partition_integrated_residual=clipped))
            assert abs(fixed) < 1e-16 and abs(clipped) < 1e-16
            assert (abs(naive) < 1e-16) if equal else (abs(naive) > 1e-6)
    return dict(H=h*ticks, h=h, flip_time=(flip_tick-1)*h,
                mesh_velocity=0., global_spatial_residuals=[r_old.sum(), r_new.sum()],
                cases=out)


def masses(x, triangles):
    m = np.zeros(4)
    for t in triangles:
        a = area(x[list(t)])
        assert a > 0
        m[list(t)] += a/3
    return m


def admissible(u, eps=1e-12):
    rho = u[:, 0]
    if np.any(rho < eps):
        return False
    internal = u[:, 3]-(u[:, 1]**2+u[:, 2]**2)/(2*rho)
    return bool(np.all(internal >= eps))


def transfer(u, old_patch, new_patch, exterior, limit=True):
    old, new = old_patch+exterior, new_patch+exterior
    delta = new-old
    defect = delta @ u
    # Full affected-star mass weights give the same correction in nodal U.
    high = new[:, None]*(u-defect/new.sum())
    average = (old_patch @ u)/old_patch.sum()
    low = exterior[:, None]*u + new_patch[:, None]*average
    assert admissible(low/new[:, None])
    alpha = 1.
    if limit and not admissible(high/new[:, None]):
        lo, hi = 0., 1.
        for _ in range(60):
            mid = (lo+hi)/2
            if admissible((low+mid*(high-low))/new[:, None]):
                lo = mid
            else:
                hi = mid
        alpha = lo
    q = low+alpha*(high-low)
    return q/new[:, None], alpha, defect


def topology_transfer():
    x = np.array([[0., 0.], [1.1, -.1], [1., 1.2], [-.2, .9]])
    old = masses(x, [(0, 1, 2), (0, 2, 3)])
    new = masses(x, [(0, 1, 3), (1, 2, 3)])
    ext = np.array([.13, .09, .17, .12])
    delta = new-old
    assert abs(delta.sum()) < 1e-15
    assert np.max(np.abs(delta @ x)) < 1e-15
    rng = np.random.default_rng(20260909)
    worst_conservation = 0.
    worst_reverse = 0.
    limited, unlimited = 0, 0
    for _ in range(1000):
        rho = np.exp(rng.uniform(-2., 2., 4))
        v = rng.uniform(-3., 3., (4, 2))
        internal = np.exp(rng.uniform(-4., 2., 4))
        u = np.column_stack((rho, rho[:, None]*v,
                             internal+.5*rho*(v*v).sum(axis=1)))
        up, alpha, _ = transfer(u, old, new, ext)
        assert admissible(up, eps=0)
        error = np.max(np.abs((new+ext) @ up-(old+ext) @ u))
        worst_conservation = max(worst_conservation, float(error))
        limited += int(alpha < 1)
        if alpha == 1:
            back, alpha_back, _ = transfer(up, new, old, ext)
            assert alpha_back == 1
            worst_reverse = max(worst_reverse, float(np.max(np.abs(back-u))))
            unlimited += 1
    affine = np.column_stack((1+.03*x[:, 0], .1+.02*x[:, 1],
                              -.12+.01*x[:, 0], 3+.05*x[:, 1]))
    ua, alpha, defect = transfer(affine, old, new, ext)
    affine_error = float(np.max(np.abs(ua-affine)))
    assert alpha == 1 and affine_error < 1e-14
    assert worst_conservation < 1e-12 and worst_reverse < 1e-12
    assert limited > 0 and unlimited > 0
    return dict(random_euler_patches=1000, positivity_limited=limited,
                unlimited=unlimited, max_conservation_error=worst_conservation,
                max_unlimited_flip_reverse_error=worst_reverse,
                affine_preservation_error=affine_error,
                zeroth_moment_error=float(abs(delta.sum())),
                first_moment_error=float(np.max(np.abs(delta @ x))))


if __name__ == '__main__':
    print(json.dumps(dict(time_coverage=time_coverage(),
                          topology_transfer=topology_transfer()), indent=2))
