#!/usr/bin/env python3
"""Small scalar P1 ALE/N experiment for delayed, patch-synchronous flips.

Uses the existing Campoli scalar audit kernel, fixed dyadic bins and prescribed
linear trajectories. This is not an Euler solver or an AREPO integration test.
Requested diagonal changes are synthetic; they are not Delaunay event detection.
The unsafe ablation extends the same conservative transfer to unsynchronized
ledgers deliberately, to test whether a conservative instantaneous map suffices.
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


def run(mode, fine_vertex, uniform=False, moving=True, h=.0025, request_offset=2):
    assert mode in ('fixed', 'patch_sync', 'immediate')
    xy = np.indices((4, 4)).reshape(2, -1).T/4
    n = len(xy)
    patch = np.array([5, 9, 10, 6])
    bins = np.full(n, 8)
    bins[patch] = 4
    bins[fine_vertex] = 1
    bins[patch[(np.where(patch == fine_vertex)[0][0]+1) % 4]] = 2
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
    request_ticks = [request_offset+8*j for j in range(4)]
    pending = False
    events, global_errors = [], []
    missing_ticks = prebirth_ticks = 0
    max_close = max_transfer_error = max_sync_state_error = 0.
    min_area = 1.
    for tick in range(1, 33):
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

        if tick in request_ticks and mode != 'fixed':
            pending = True
        if pending and (mode == 'immediate' or np.all(active[patch])):
            new_ids, new_initial = triangulation(not flipped)
            new_mass = scatter(new_ids, area(new_initial+tick*h*sigma[new_ids])[:, None]/3, n)
            delta = new_mass-endpoint
            # A completed common-time patch has q=m*u and g=m for its nodes.
            state_error = float(np.max(np.abs(q[patch]-endpoint[patch]*u[patch])))
            ledger_error = float(np.max(np.abs(g[patch]-endpoint[patch])))
            if mode == 'patch_sync':
                assert np.all(active[patch])
                assert np.all(due[np.any(np.isin(ids, patch), axis=1)])
                assert state_error < 1e-15 and ledger_error < 1e-15
                max_sync_state_error = max(max_sync_state_error, state_error, ledger_error)
            before = q.sum()
            defect = float(delta[patch] @ u[patch])
            shift = defect/new_mass[patch].sum()
            q[patch] += delta[patch]*u[patch]-new_mass[patch]*shift
            u[patch] -= shift
            g[patch] += delta[patch]
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
                               nodal_uniform_shift=shift))
            ids, initial = new_ids, new_initial
            flipped = not flipped
            pending = False
        if tick % int(bins.max()) == 0:
            global_errors.append(float(q.sum()-total0))
    answer = dict(mode=mode, fine_vertex=fine_vertex, uniform=uniform,
                  moving=moving, h=h, request_offset=request_offset,
                  global_H=8*h, patch_H=4*h,
                  max_global_mass_error=max(map(abs, global_errors)),
                  global_mass_errors=global_errors, max_geometry_close=max_close,
                  max_transfer_mass_error=max_transfer_error,
                  max_common_time_state_error=max_sync_state_error,
                  orphan_interval_ticks=missing_ticks, prebirth_interval_ticks=prebirth_ticks,
                  min_triangle_area=min_area, min_u=float(u.min()),
                  uniform_error=float(np.max(np.abs(u-1))) if uniform else None,
                  events=events)
    assert max_transfer_error < 2e-15
    if mode != 'immediate':
        assert answer['max_global_mass_error'] < 2e-14, answer
        assert max_close < 2e-15, answer
        assert missing_ticks == prebirth_ticks == 0, answer
    if mode == 'patch_sync':
        assert len(events) == 4 and not any(e['global_sync'] for e in events)
        assert [e['tick'] for e in events] == [4, 12, 20, 28]
    if uniform:
        assert answer['uniform_error'] < 2e-14, answer
    return answer


if __name__ == '__main__':
    results = [run(mode, vertex, uniform, moving, h, offset)
               for offset in (2, 3)
               for h in (.0025, .00125)
               for moving in (False, True)
               for uniform in (False, True)
               for vertex in (5, 9, 10, 6)
               for mode in ('fixed', 'patch_sync', 'immediate')]
    for offset in (2, 3):
        assert any(r['max_global_mass_error'] > 1e-9 for r in results
                   if r['mode'] == 'immediate' and not r['uniform']
                   and r['request_offset'] == offset)
    print(json.dumps(results, indent=2))
