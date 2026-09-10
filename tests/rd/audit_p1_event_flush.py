#!/usr/bin/env python3
"""Scalar P1 ALE/N audit of event-time triangle closure and active transfer.

Uses the existing Campoli scalar audit kernel, fixed dyadic bins and prescribed
linear trajectories. This is not an Euler solver or an AREPO integration test.
Requested diagonal changes are synthetic; they are not Delaunay event detection.
At a requested topology event, flush any removed triangle up to that event;
new triangles start their next integral at their birth time. Keep touched
inactive nodes frozen through the end of their current own interval. The
unlatched ablation demonstrates why rebuilding only the current star fails.
This intentionally duplicates the small reference kernel to keep earlier
audit artifacts unchanged. It is not an AREPO or Euler PDE implementation.
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
    assert mode in ('patch_sync', 'active_transfer', 'triangle_sync_all_states', 'event_flush', 'event_flush_unlatched')
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
    frozen_until = np.zeros(n, dtype=int)
    for tick in range(1, cycles*global_period+1):
        tb = bins[ids].min(axis=1)
        star = bins.copy()
        np.minimum.at(star, ids.ravel(), np.repeat(tb, 3))
        active = tick % bins == 0
        live = active & (star == bins)
        due = tick % tb == 0
        current_keys = keys(ids)
        lengths = np.array([tick-last[k] for k in current_keys])
        if mode.startswith('event_flush'):
            if tick in request_ticks:
                candidates, _ = triangulation(not flipped)
                forced = np.array([k not in set(keys(candidates)) for k in current_keys])
                due |= forced
                for v in np.unique(ids[forced]):
                    if not active[v]:
                        frozen_until[v] = ((tick+bins[v]-1)//bins[v])*bins[v]
            if mode == 'event_flush':
                live &= tick > frozen_until
        for j in np.flatnonzero(due):
            key = current_keys[j]
            prebirth_ticks += max(0, birth[key]-(tick-int(lengths[j] if mode.startswith('event_flush') else tb[j])))
            last[key] = tick
        xn = initial+tick*h*sigma[ids]
        endpoint = scatter(ids, area(xn)[:, None]/3, n)
        ii = ids[due]
        dt = (lengths[due] if mode.startswith('event_flush') else tb[due])*h
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
        ready = True if mode.startswith('event_flush') else (np.all(active[patch]) if mode == 'patch_sync' else tick % flip_period == 0)
        if pending and ready:
            new_ids, new_initial = triangulation(not flipped)
            new_mass = scatter(new_ids, area(new_initial+tick*h*sigma[new_ids])[:, None]/3, n)
            delta = new_mass-endpoint
            # A completed common-time patch has q=m*u and g=m for its nodes.
            state_error = float(np.max(np.abs(q[patch]-endpoint[patch]*u[patch])))
            ledger_error = float(np.max(np.abs(g[patch]-endpoint[patch])))
            support = patch if mode == 'triangle_sync_all_states' else patch[active[patch]]
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
            if mode != 'triangle_sync_all_states' and len(inactive):
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
                if mode.startswith('event_flush'):
                    for v in key:
                        if not active[v]:
                            frozen_until[v] = ((tick+bins[v]-1)//bins[v])*bins[v]
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
    if mode not in ('triangle_sync_all_states', 'event_flush_unlatched'):
        assert answer['max_global_mass_error'] < 2e-12, answer
        assert max_close < 2e-13, answer
    assert len(events) == cycles
    if uniform:
        assert answer['uniform_error'] < 2e-12, answer
    return answer


if __name__ == '__main__':
    results = [run(mode, vertex, uniform, moving, .02/8, offset, periods, 8, 4)
               for periods in ((1, 2, 4, 4), (1, 8, 8, 8))
               for offset in (1, 3)
               for vertex in (5, 9, 10, 6)
               for uniform in (False, True)
               for moving in (False, True)
               for mode in ('event_flush', 'event_flush_unlatched')]
    deep = [run(mode, 5, uniform, True, .02/1024, 1, periods, 1024, 2)
            for periods in ((1, 2, 256, 1024), (1, 1024, 1024, 1024))
            for uniform in (False, True)
            for mode in ('event_flush', 'event_flush_unlatched')]
    assert any(r['max_global_mass_error'] > 1e-9 for r in results
               if r['mode'] == 'event_flush_unlatched' and not r['uniform'])
    for r in results+deep:
        assert all(e['tick'] % round(r['global_H']/r['h']) == r['request_offset']
                   for e in r['events'])
    print(json.dumps(dict(standard_cases=results, deep_cases=deep), indent=2))

