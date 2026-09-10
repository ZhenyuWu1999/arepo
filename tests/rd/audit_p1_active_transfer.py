#!/usr/bin/env python3
"""Scalar P1 ALE/N experiment for triangle-synchronous, active-only transfer.

Uses the existing Campoli scalar audit kernel, fixed dyadic bins and prescribed
linear trajectories. This is not an Euler solver or an AREPO integration test.
Requested diagonal changes are synthetic; they are not Delaunay event detection.
Extends audit_p1_patch_sync.py without changing that archived discriminator.
Inactive states and Q-g*U are held fixed through each topology transfer. Only
triangles being removed/added must synchronize; active nodes absorb the defect.
Also checks Euler transfer feasibility separately, not Euler PDE evolution.
"""
import json
import numpy as np

from audit_ale_hierarchy_mass_rebase import area, residual, scatter
from audit_flip_time_coverage import periodic_triangles


def triangulation(flipped):
    records = periodic_triangles(4, flipped)
    return np.array([v[0] for v in records]), np.array([v[1] for v in records])


def keys(ids):
    return [tuple(sorted(row)) for row in ids]


def run(mode, fine_vertex, uniform=False, moving=True, h=.0025, request_offset=2,
        patch_periods=(1, 2, 4, 4), exterior_period=8, cycles=4):
    assert mode in ('patch_sync', 'active_transfer', 'triangle_sync_all_states')
    xy = np.indices((4, 4)).reshape(2, -1).T/4
    n = len(xy)
    patch = np.array([5, 9, 10, 6])
    bins = np.full(n, exterior_period)
    rotated = np.roll(patch, -int(np.where(patch == fine_vertex)[0][0]))
    bins[rotated] = patch_periods
    global_period = int(bins.max())
    assert all(v > 0 and v & (v-1) == 0 for v in bins)
    x, y = xy.T
    sigma = np.column_stack((.19*np.sin(2*np.pi*y)+.11*np.cos(2*np.pi*x),
                             .13*np.sin(2*np.pi*x)+.07*np.cos(2*np.pi*y)))
    if not moving:
        sigma[:] = 0
    u = 1+.16*np.sin(2*np.pi*x)+.12*np.cos(2*np.pi*(x+y))
    if uniform:
        u[:] = 1
    flipped = False
    ids, initial = triangulation(flipped)
    g = scatter(ids, area(initial)[:, None]/3, n)
    q = g*u
    total0 = float(q.sum())
    birth = dict.fromkeys(keys(ids), 0)
    last = birth.copy()
    request_ticks = [request_offset+global_period*j for j in range(cycles)]
    other_ids, _ = triangulation(True)
    changed_ids = np.array([row for row in ids if tuple(sorted(row)) not in set(keys(other_ids))]
                           + [row for row in other_ids if tuple(sorted(row)) not in set(keys(ids))])
    flip_period = int(bins[changed_ids].min(axis=1).max())
    assert flip_period == sorted(patch_periods)[1]
    pending = False
    events, global_errors = [], []
    missing_ticks = prebirth_ticks = 0
    max_close = max_transfer_error = max_sync_state_error = max_inactive_debt_error = 0.
    min_area = 1.
    for tick in range(1, cycles*global_period+1):
        tb = bins[ids].min(axis=1)
        star = bins.copy()
        np.minimum.at(star, ids.ravel(), np.repeat(tb, 3))
        active = tick % bins == 0
        live = active & (star == bins)
        due = tick % tb == 0
        current_keys = keys(ids)
        for j in np.flatnonzero(due):
            key = current_keys[j]
            prebirth_ticks += max(0, birth[key]-(tick-int(tb[j])))
            last[key] = tick
        xn = initial+tick*h*sigma[ids]
        endpoint = scatter(ids, area(xn)[:, None]/3, n)
        ii = ids[due]
        dt = tb[due]*h
        vel = sigma[ii]
        xp = xn[due]
        xm = xp-.5*dt[:, None, None]*vel
        xo = xp-dt[:, None, None]*vel
        ao, am, ap = area(xo), area(xm), area(xp)
        min_area = min(min_area, float(min(ao.min(), am.min(), ap.min())))
        assert min_area > 0
        dg = scatter(ii, ((ap-ao)/3)[:, None], n)
        q += dg*u
        g += dg
        close = np.where(active, endpoint-g, 0)
        max_close = max(max_close, float(np.max(np.abs(close))))
        q += close*u
        g[active] = endpoint[active]
        divisor = scatter(ii, (ap/3)[:, None], n)
        r0 = residual(xm, vel, u[ii])
        predictor = scatter(ii, -dt[:, None]*r0, n)
        du = np.zeros(n)
        du[live] = predictor[live]/divisor[live]
        r1 = residual(xm, vel, (u+du)[ii])
        q += scatter(ii, -.5*dt[:, None]*(r0+r1)
                     + ((ap-ao)/6)[:, None]*du[ii], n)
        u[active] = q[active]/endpoint[active]

        if tick in request_ticks:
            pending = True
        ready = np.all(active[patch]) if mode == 'patch_sync' else tick % flip_period == 0
        if pending and ready:
            new_ids, new_initial = triangulation(not flipped)
            new_mass = scatter(new_ids, area(new_initial+tick*h*sigma[new_ids])[:, None]/3, n)
            delta = new_mass-endpoint
            # A completed common-time patch has q=m*u and g=m for its nodes.
            state_error = float(np.max(np.abs(q[patch]-endpoint[patch]*u[patch])))
            ledger_error = float(np.max(np.abs(g[patch]-endpoint[patch])))
            support = patch[active[patch]] if mode == 'active_transfer' else patch
            inactive = patch[~active[patch]]
            if mode != 'triangle_sync_all_states':
                assert np.all(active[support])
                assert np.all(due[np.any(np.isin(ids, support), axis=1)])
                sync_error = max(float(np.max(np.abs(q[support]-endpoint[support]*u[support]))),
                                 float(np.max(np.abs(g[support]-endpoint[support]))))
                assert sync_error < 1e-13
                max_sync_state_error = max(max_sync_state_error, sync_error)
            old_inactive_u = u[inactive].copy()
            old_debt = q[inactive]-g[inactive]*u[inactive]
            before = q.sum()
            defect = float(delta[patch] @ u[patch])
            shift = defect/new_mass[support].sum()
            q[patch] += delta[patch]*u[patch]
            q[support] -= new_mass[support]*shift
            u[support] -= shift
            g[patch] += delta[patch]
            if mode == 'active_transfer' and len(inactive):
                assert np.array_equal(old_inactive_u, u[inactive])
                debt_error = float(np.max(np.abs(q[inactive]-g[inactive]*u[inactive]-old_debt)))
                max_inactive_debt_error = max(max_inactive_debt_error, debt_error)
                assert debt_error < 1e-15
            max_transfer_error = max(max_transfer_error, float(abs(q.sum()-before)))
            old_keys, new_keys = set(current_keys), set(keys(new_ids))
            for key in old_keys-new_keys:
                missing_ticks += tick-last[key]
                del last[key], birth[key]
            for key in new_keys-old_keys:
                birth[key] = last[key] = tick
            events.append(dict(tick=tick, global_sync=bool(np.all(active)),
                               active_patch_nodes=int(active[patch].sum()),
                               unclosed_incident_triangles=int(np.sum(
                                   np.any(np.isin(ids, patch), axis=1) & ~due)),
                               pretransfer_state_error=state_error,
                               modified_nodes=len(support),
                               nodal_uniform_shift=shift))
            ids, initial = new_ids, new_initial
            flipped = not flipped
            pending = False
        if tick % int(bins.max()) == 0:
            global_errors.append(float(q.sum()-total0))
    answer = dict(mode=mode, fine_vertex=fine_vertex, uniform=uniform,
                  moving=moving, h=h, request_offset=request_offset,
                  patch_periods=patch_periods, global_H=global_period*h,
                  patch_H=max(patch_periods)*h, flip_H=flip_period*h,
                  max_global_mass_error=max(map(abs, global_errors)),
                  global_mass_errors=global_errors, max_geometry_close=max_close,
                  max_transfer_mass_error=max_transfer_error,
                  max_common_time_state_error=max_sync_state_error,
                  max_inactive_debt_error=max_inactive_debt_error,
                  orphan_interval_ticks=missing_ticks, prebirth_interval_ticks=prebirth_ticks,
                  min_triangle_area=min_area, min_u=float(u.min()),
                  uniform_error=float(np.max(np.abs(u-1))) if uniform else None,
                  events=events)
    assert max_transfer_error < 2e-15
    assert missing_ticks == prebirth_ticks == 0, answer
    if mode != 'triangle_sync_all_states':
        assert answer['max_global_mass_error'] < 2e-12, answer
        assert max_close < 2e-13, answer
    assert len(events) == cycles
    if uniform:
        assert answer['uniform_error'] < 2e-12, answer
    return answer


def admissible(u):
    u = np.atleast_2d(u)
    if np.any(u[:, 0] <= 0):
        return False
    return bool(np.all(u[:, 3] - .5*np.sum(u[:, 1:3]**2, axis=1)/u[:, 0] > 0))


def euler_transfer_audit(samples=1000):
    """Unit-square AC->BD transfer, active old-diagonal nodes A,C.

    Feasibility is conditional: the target sum of active extensive states must
    itself be admissible. The constant active-state low-order map is a witness
    when it is. No positivity claim is made for the Euler time integrator.
    """
    rng = np.random.default_rng(20260910)
    old_patch = np.array([1/3, 1/6, 1/3, 1/6])
    new_patch = np.array([1/6, 1/3, 1/6, 1/3])
    exterior = np.full(4, 1/12)
    old, new = old_patch+exterior, new_patch+exterior
    active = np.array([0, 2])
    inactive = np.array([1, 3])
    counts = dict(high_admissible=0, limited=0, infeasible=0)
    max_mass_error = 0.
    for _ in range(samples):
        rho, p = 10**rng.uniform(-1, 1, (2, 4))
        vel = rng.normal(0, 1, (4, 2))
        u = np.column_stack((rho, rho[:, None]*vel, p/.4+.5*rho*np.sum(vel**2, axis=1)))
        defect = (new-old) @ u
        target = new[active] @ u[active]-defect
        if not admissible(target):
            counts['infeasible'] += 1
            continue
        hi = u[active]-defect/new[active].sum()
        lo = np.broadcast_to(target/new[active].sum(), hi.shape)
        assert admissible(lo)
        if admissible(hi):
            counts['high_admissible'] += 1
            candidate = hi
        else:
            counts['limited'] += 1
            left, right = 0., 1.
            for _ in range(55):
                alpha = (left+right)/2
                if admissible(lo+alpha*(hi-lo)):
                    left = alpha
                else:
                    right = alpha
            candidate = lo+.99*left*(hi-lo)
        updated = u.copy()
        updated[active] = candidate
        assert np.array_equal(updated[inactive], u[inactive])
        assert admissible(updated)
        max_mass_error = max(max_mass_error, float(np.max(np.abs(new @ updated-old @ u))))
    # Simple exact obstruction: inactive nodes gain too much representation mass.
    rho = np.array([1., 100., 1., 100.])
    target_density = float(old @ rho-new[inactive] @ rho[inactive])
    assert target_density < 0 and counts['infeasible'] > 0
    assert counts['high_admissible'] > 0 and counts['limited'] > 0
    assert max_mass_error < 2e-13
    return dict(samples=samples, counts=counts, max_conservation_error=max_mass_error,
                infeasible_density_example=target_density,
                scope='Euler state transfer only; random sample counts are not physical failure probabilities')


if __name__ == '__main__':
    results = [run(mode, vertex, uniform, moving, h, offset)
               for offset in (2, 3)
               for h in (.0025, .00125)
               for moving in (False, True)
               for uniform in (False, True)
               for vertex in (5, 9, 10, 6)
               for mode in ('patch_sync', 'active_transfer', 'triangle_sync_all_states')]
    deep = [run(mode, 5, uniform, True, .02/1024, 1, periods, 1024, 1)
            for periods in ((1, 2, 256, 1024), (1, 1024, 1024, 1024))
            for uniform in (False, True)
            for mode in ('patch_sync', 'active_transfer')]
    assert any(r['max_global_mass_error'] > 1e-9 for r in results
               if r['mode'] == 'triangle_sync_all_states' and not r['uniform'])
    print(json.dumps(dict(standard_cases=results, deep_cases=deep,
                         euler_transfer=euler_transfer_audit()), indent=2))
