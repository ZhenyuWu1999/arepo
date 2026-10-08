#!/usr/bin/env python3
"""Explicit same-time P1 geometry transfer from C&R collapse/expand records.

This is a NEW explicit extension, not Colombo & Re's implicit BDF scheme.
The geometry records supply integrated nodal swept areas, not physical-time
velocities. We combine OLD and NEW records into one LF operator and integrate
it on a positive full-nodal-mass homotopy. We never evolve a fluid state on a
triangle of zero area. See dev_log/colombo_re_spike/explicit_operator.md.

Public API:
  assemble_lf_operator(geometry, alpha_factor=1,
                       alpha_rule='spectral') -> L, diagnostics
  topological_remap(q, g, geometry, mode='adaptive', cfl=.9,
                    substeps=None, alpha_factor=1) -> q_new, g_new, diagnostics

geometry: dict with records, node_ids, mass_delta. Each record supplies ids and
integrated_nu in matching order. Mass vectors follow geometry['node_ids'].
q contains SAME-TIME extensive states and g their full P1 nodal masses. A
positive remap does NOT prove positivity of subsequent frozen-state LTS fluxes.
"""
from __future__ import annotations

import argparse
import json
from typing import Any

import numpy as np


def _get(obj: Any, key: str) -> Any:
    return obj[key] if isinstance(obj, dict) else getattr(obj, key)


def assemble_lf_operator(geometry, alpha_factor=1.0, alpha_rule='spectral'):
    """Return L with Q_s=-L U, L 1=-dm and 1^T L=0.

    Complete cavity records are mandatory: total area change zero alone does
    not justify state-weighted boundary-flux cancellation. The stronger check
    sum_{records containing i} nu_ri=0 is made independently at every node.
    """
    if not np.isfinite(alpha_factor) or alpha_factor < 1.0:
        raise ValueError('alpha_factor must be finite and >= 1')
    if alpha_rule not in ('spectral', 'graph_minimal'):
        raise ValueError('alpha_rule must be spectral or graph_minimal')
    node_ids = list(_get(geometry, 'node_ids'))
    if len(set(node_ids)) != len(node_ids):
        raise ValueError('node_ids must be unique')
    index = {int(node_id): k for k, node_id in enumerate(node_ids)}
    dm = np.asarray(_get(geometry, 'mass_delta'), dtype=float)
    if dm.shape != (len(node_ids),):
        raise ValueError('mass_delta must follow node_ids')
    L = np.zeros((len(node_ids), len(node_ids)))
    nodal_nu = np.zeros(len(node_ids))
    record_dm = np.zeros(len(node_ids))
    alphas = []
    total_nu_scale = 0.0
    for record in _get(geometry, 'records'):
        ids = [index[int(i)] for i in _get(record, 'ids')]
        nu = np.asarray(_get(record, 'integrated_nu'), dtype=float)
        if len(ids) != 3 or len(set(ids)) != 3 or nu.shape != (3,):
            raise ValueError('each record must have three distinct triangle nodes')
        if not np.all(np.isfinite(nu)):
            raise ValueError('non-finite swept areas')
        # The spectral choice parallels the paper's pure-ALE LF coefficient.
        # graph_minimal is a NEW pure-geometry choice: only off-diagonal
        # monotonicity is needed, and global column balance then fixes the
        # diagonal sign. This is not a replacement for physical Euler LF.
        floor = (np.max(np.abs(nu)) if alpha_rule == 'spectral'
                 else max(0.0, -np.min(nu)))
        alpha = alpha_factor * floor
        local = -np.outer(np.ones(3), nu) / 3.0
        local += alpha * (np.eye(3) - np.ones((3, 3)) / 3.0)
        L[np.ix_(ids, ids)] += local
        nodal_nu[ids] += nu
        record_dm[ids] += nu.sum() / 3.0
        total_nu_scale += np.abs(nu).sum()
        alphas.append(float(alpha))
    scale = max(total_nu_scale, np.max(np.abs(dm), initial=0.0),
                np.finfo(float).tiny)
    tolerance = 256 * np.finfo(float).eps * scale
    if np.max(np.abs(nodal_nu), initial=0.0) > tolerance:
        raise ValueError('incomplete/unbalanced records: nodal integrated_nu is nonzero')
    if np.max(np.abs(record_dm - dm), initial=0.0) > tolerance:
        raise ValueError('mass_delta disagrees with record swept areas')
    offdiag = L.copy()
    np.fill_diagonal(offdiag, 0.0)
    diag = np.diag(L)
    if np.max(offdiag, initial=0.0) > tolerance or np.min(diag, initial=0.0) < -tolerance:
        raise ValueError('LF operator has invalid monotone signs')
    return L, {
        'alpha_rule': alpha_rule,
        'alphas': alphas,
        'nodal_swept_balance_error': float(np.max(np.abs(nodal_nu), initial=0.0)),
        'operator_column_sum_error': float(np.max(np.abs(L.sum(axis=0)), initial=0.0)),
        'operator_gcl_error': float(np.max(np.abs(L.sum(axis=1) + dm), initial=0.0)),
        'operator_offdiag_max': float(np.max(offdiag, initial=0.0)),
    }


def topological_remap(q, g, geometry, mode='adaptive', cfl=0.9,
                      substeps=None, alpha_factor=1.0, alpha_rule='spectral'):
    """Advance one geometrical homotopy s=0..1, returning a new state.

    In adaptive mode, positive g at both endpoints and admissible q/g imply
    admissible output by nonnegative scalar convex coefficients, in exact
    arithmetic. 'once' and 'fixed' deliberately permit negative coefficients
    for diagnostic comparisons; consult positivity_cfl_satisfied.
    """
    L, diag = assemble_lf_operator(geometry, alpha_factor=alpha_factor,
                                 alpha_rule=alpha_rule)
    dm = np.asarray(_get(geometry, 'mass_delta'), dtype=float)
    g0 = np.asarray(g, dtype=float).copy()
    q0 = np.asarray(q, dtype=float)
    scalar = q0.ndim == 1
    if scalar:
        q0 = q0[:, None]
    if q0.ndim != 2 or q0.shape[0] != len(dm) or g0.shape != dm.shape:
        raise ValueError('q and g must follow geometry node_ids')
    if not np.all(np.isfinite(q0)) or not np.all(np.isfinite(g0)):
        raise ValueError('non-finite input')
    g1 = g0 + dm
    if np.any(g0 <= 0) or np.any(g1 <= 0):
        raise ValueError('full nodal masses must be positive at both endpoints')
    if mode not in ('adaptive', 'fixed', 'once'):
        raise ValueError('mode must be adaptive, fixed or once')
    if not 0 < cfl <= 1:
        raise ValueError('cfl must lie in (0,1]')
    if mode == 'fixed' and (substeps is None or int(substeps) != substeps or substeps < 1):
        raise ValueError('fixed mode needs a positive integer substeps')
    qn = q0.copy()
    # T maps initial conservative densities U0 to extensive Q(s). Its row sums
    # test the constant-field/GCL property independently of the chosen input.
    T = np.diag(g0)
    s = 0.0
    steps = 0
    min_weight = np.inf
    max_cfl = 0.0
    lii = np.diag(L)
    positive_diagonal = lii > 0
    while s < 1.0:
        gs = g0 + s * dm
        if mode == 'once':
            ds = 1.0
        elif mode == 'fixed':
            ds = min(1.0 - s, 1.0 / int(substeps))
            if steps == int(substeps) - 1:
                ds = 1.0 - s
        else:
            bound = (np.min(gs[positive_diagonal] / lii[positive_diagonal])
                     if np.any(positive_diagonal) else np.inf)
            ds = min(1.0 - s, cfl * bound)
        if ds <= 0 or not np.isfinite(ds):
            raise FloatingPointError('geometry substep did not advance')
        gnext = g0 + (s + ds) * dm
        A = np.diag(gs) - ds * L
        W = A / gnext[:, None]
        min_weight = min(min_weight, float(W.min()))
        max_cfl = max(max_cfl, float(np.max(ds * lii / gs, initial=0.0)))
        qn = A @ (qn / gs[:, None])
        T = A @ (T / gs[:, None])
        s += ds
        steps += 1
        if steps > 100000:
            raise RuntimeError('too many geometry substeps')
    diag.update({
        'mode': mode,
        'steps': steps,
        'max_geometric_cfl': max_cfl,
        'min_update_weight': float(min_weight),
        'positivity_cfl_satisfied': bool(max_cfl <= 1 + 64*np.finfo(float).eps),
        'total_conservation_error': float(np.max(np.abs(qn.sum(axis=0)-q0.sum(axis=0)))),
        'relative_total_conservation_error': float(np.max(
            np.abs(qn.sum(axis=0)-q0.sum(axis=0)) /
            np.maximum(np.abs(q0).sum(axis=0), np.finfo(float).tiny))),
        'uniform_row_sum_error': float(np.max(np.abs(T.sum(axis=1)/g1 - 1))),
        'minimum_final_transfer_weight': float(np.min(T / g1[:, None])),
    })
    return (qn[:, 0] if scalar else qn), g1, diag


def square_geometry(reverse=False):
    """Independent hand-derived unit-square collapse at (1/2,1/2).

    Kept for testing independently of the geometry implementation. Returning
    only three records, or balancing just sum(area), is not a valid cavity.
    """
    records = [
        {'ids': (0, 1, 2), 'old_or_new': 'old',
         'signed_area_change': -.5, 'integrated_nu': [-.125, -.25, -.125]},
        {'ids': (0, 2, 3), 'old_or_new': 'old',
         'signed_area_change': -.5, 'integrated_nu': [-.125, -.125, -.25]},
        {'ids': (0, 1, 3), 'old_or_new': 'new',
         'signed_area_change': .5, 'integrated_nu': [.25, .125, .125]},
        {'ids': (1, 2, 3), 'old_or_new': 'new',
         'signed_area_change': .5, 'integrated_nu': [.125, .25, .125]},
    ]
    old = np.array([1/3, 1/6, 1/3, 1/6])
    new = np.array([1/6, 1/3, 1/6, 1/3])
    if reverse:
        old, new = new, old
        for record in records:
            record['integrated_nu'] = [-v for v in record['integrated_nu']]
            record['signed_area_change'] *= -1
            record['old_or_new'] = 'new' if record['old_or_new'] == 'old' else 'old'
    return {'records': records, 'node_ids': [0, 1, 2, 3],
            'old_mass': old, 'new_mass': new, 'mass_delta': new-old}


def primitive_pressure(U, gamma=1.4):
    rho = U[:, 0]
    with np.errstate(divide='ignore', invalid='ignore'):
        return (gamma-1) * (U[:, 3] - np.sum(U[:, 1:3]**2, axis=1)/(2*rho))


def euler_admissible(U):
    return bool(np.all(np.isfinite(U)) and np.all(U[:, 0] > 0) and
                np.all(primitive_pressure(U) > 0))


def audit(samples=512, seed=20260910):
    """Bounded exact-geometry and random Euler checks; output JSON data."""
    geometry = square_geometry()
    L, operator_diag = assemble_lf_operator(geometry)
    rng = np.random.default_rng(seed)
    rows = []
    cases = [
        ('no_exterior', np.zeros(4)),
        ('small_exterior', np.full(4, 1/12)),
        ('regular_six_triangle_star', 1-np.asarray(geometry['old_mass'])),
    ]
    for alpha_rule, (label, exterior) in [
        (rule, case) for rule in ('spectral', 'graph_minimal') for case in cases
    ]:
        g = geometry['old_mass'] + exterior
        count_once = count_adaptive = 0
        max_conservation = max_uniform = 0.0
        min_weight = np.inf
        step_min, step_max = 100000, 0
        for _ in range(samples):
            rho = np.exp(rng.uniform(-5, 5, 4))
            pressure = np.exp(rng.uniform(-5, 5, 4))
            velocity = rng.uniform(-8, 8, (4, 2))
            U = np.column_stack((rho, rho[:, None]*velocity,
                                 pressure/.4 + .5*rho*np.sum(velocity**2, axis=1)))
            assert euler_admissible(U)
            q0 = g[:, None] * U
            qo, go, do = topological_remap(q0, g, geometry, mode='once',
                                          alpha_rule=alpha_rule)
            qa, ga, da = topological_remap(q0, g, geometry, alpha_rule=alpha_rule)
            count_once += euler_admissible(qo / go[:, None])
            count_adaptive += euler_admissible(qa / ga[:, None])
            max_conservation = max(max_conservation, da['relative_total_conservation_error'])
            max_uniform = max(max_uniform, da['uniform_row_sum_error'])
            min_weight = min(min_weight, da['min_update_weight'])
            step_min = min(step_min, da['steps'])
            step_max = max(step_max, da['steps'])
        assert count_adaptive == samples
        assert max_conservation < 5e-14 and max_uniform < 5e-14
        rows.append({'alpha_rule': alpha_rule, 'exterior': label, 'samples': samples,
                     'once_euler_admissible': count_once,
                     'once_geometric_cfl': do['max_geometric_cfl'],
                     'adaptive_euler_admissible': count_adaptive,
                     'adaptive_steps_min_max': [step_min, step_max],
                     'adaptive_min_update_weight': min_weight,
                     'max_relative_total_conservation_error': max_conservation,
                     'max_uniform_error': max_uniform})
    # Same-time validity does not require state-weighted cancellation to be
    # assumed: this incomplete pair conserves total area but must be rejected.
    incomplete = dict(geometry)
    incomplete['records'] = [geometry['records'][0], geometry['records'][2]]
    rejected = False
    try:
        assemble_lf_operator(incomplete)
    except ValueError as exc:
        rejected = 'nodal integrated_nu' in str(exc)
    assert rejected
    xy = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])
    affine = 1 + .2*xy[:, 0] + .3*xy[:, 1]
    g = np.ones(4)
    qa, ga, _ = topological_remap(g*affine, g, geometry)
    qr, gr, _ = topological_remap(qa, ga, square_geometry(reverse=True))
    result = {
        'scope': 'same-time explicit pure-geometry LF; not physical Euler/LTS',
        'seed': seed, 'operator': L.tolist(), 'operator_checks': operator_diag,
        'euler': rows,
        'incomplete_zero_total_area_records_rejected': rejected,
        'affine_field_max_error': float(np.max(np.abs(qa/ga-affine))),
        'forward_reverse_max_state_change': float(np.max(np.abs(qr/gr-affine))),
        'forward_reverse_range_ratio': float(np.ptp(qr/gr)/np.ptp(affine)),
    }
    # Compare with the independently implemented signed-sweep geometry module
    # once available, without making the standalone hand check depend on it.
    try:
        from colombo_re_geometry import geometry_records
    except ImportError:
        result['independent_geometry_comparison'] = 'geometry module unavailable'
    else:
        actual = geometry_records(xy, [(0, 1, 2), (0, 2, 3)],
                                  [(0, 1, 3), (1, 2, 3)],
                                  collapse_point=np.array([.5, .5]))
        La, _ = assemble_lf_operator(actual)
        err = float(np.max(np.abs(La-L)))
        assert err < 1e-14
        result['independent_geometry_comparison'] = {'operator_max_error': err}
        varied = {rule: {'cases': 0, 'admissible': 0, 'max_steps': 0,
                         'max_relative_conservation_error': 0., 'max_uniform_error': 0.}
                  for rule in ('spectral', 'graph_minimal')}
        for _ in range(samples):
            points = xy + rng.uniform(-.18, .18, xy.shape)
            bary = rng.uniform(.01, 1, 4)
            center = bary @ points / bary.sum()
            geo = geometry_records(points, [(0, 1, 2), (0, 2, 3)],
                                   [(0, 1, 3), (1, 2, 3)], center)
            old = np.asarray(geo['old_mass'])
            full = old + rng.uniform(0, 3, 4) * old
            rho = np.exp(rng.uniform(-5, 5, 4))
            pressure = np.exp(rng.uniform(-5, 5, 4))
            velocity = rng.uniform(-8, 8, (4, 2))
            U = np.column_stack((rho, rho[:, None]*velocity,
                                 pressure/.4 + .5*rho*np.sum(velocity**2, axis=1)))
            for rule, stats in varied.items():
                out, mass, checks = topological_remap(full[:, None]*U, full, geo,
                                                      alpha_rule=rule)
                stats['cases'] += 1
                stats['admissible'] += euler_admissible(out/mass[:, None])
                stats['max_steps'] = max(stats['max_steps'], checks['steps'])
                stats['max_relative_conservation_error'] = max(
                    stats['max_relative_conservation_error'],
                    checks['relative_total_conservation_error'])
                stats['max_uniform_error'] = max(stats['max_uniform_error'],
                                                 checks['uniform_row_sum_error'])
                assert checks['min_update_weight'] >= -1e-14
        for stats in varied.values():
            assert stats['admissible'] == samples
            assert stats['max_relative_conservation_error'] < 1e-13
            assert stats['max_uniform_error'] < 1e-13
        result['varied_convex_geometry_euler'] = varied
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=int, default=512)
    parser.add_argument('--seed', type=int, default=20260910)
    args = parser.parse_args()
    print(json.dumps(audit(samples=args.samples, seed=args.seed), indent=2))
