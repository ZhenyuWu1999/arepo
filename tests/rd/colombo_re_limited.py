#!/usr/bin/env python3
"""Same-time convex limiting of a CR-inspired positive geometry transfer.

The high endpoint is the EXISTING full-patch uniform-shift correction, not a
new Colombo--Re result. This module tests a low-dissipation extension of the
new explicit CR-inspired low endpoint. It neither advances a physical PDE
nor proves hierarchical transport positivity or global convergence order.
"""
from __future__ import annotations

import numpy as np

from colombo_re_explicit import topological_remap


def internal_energy_density(state):
    """Euler conservative density order: rho, momentum(s), total energy."""
    state = np.asarray(state, dtype=float)
    with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
        return state[:, -1] - np.sum(state[:, 1:-1]**2, axis=1)/(2*state[:, 0])


def limited_remap(q, g, geometry, *, low_endpoint='cr_graph_minimal',
                  dmp_relax=None, floor_fraction=1e-12, cfl=0.9):
    """Return Qnew, gnew, diagnostics for one SAME-TIME topology event.

    q: scalar (n,) or (n,1), or Euler (n,4)/(n,5). g: positive full nodal
    masses. Their order follows geometry['node_ids']; old_mass and new_mass
    are changed-patch P1 masses. All surrounding contributions g-old_mass
    must be nonnegative. Low options: cr_graph_minimal, cr_spectral, full_patch.

    A single theta blends the whole cavity and every conserved component.
    rho and internal-energy-density floors are floor_fraction times their
    respective minimum input values. dmp_relax optionally imposes input
    min/max +/- dmp_relax*(max-min) on scalar values or Euler density ONLY.
    Bounds include a scale-relative floating-point tolerance. Pressure and
    momentum are not subject to componentwise DMP constraints.
    """
    q = np.asarray(q, dtype=float)
    scalar_vector = q.ndim == 1
    if scalar_vector:
        q = q[:, None]
    g = np.asarray(g, dtype=float)
    node_ids = geometry['node_ids']
    n = len(node_ids)
    if q.ndim != 2 or q.shape[0] != n or q.shape[1] not in (1, 4, 5):
        raise ValueError('q must be scalar (n,)/(n,1) or Euler (n,4)/(n,5)')
    if g.shape != (n,) or len(set(node_ids)) != n:
        raise ValueError('g and q must follow unique geometry node_ids')
    if not np.all(np.isfinite(q)) or not np.all(np.isfinite(g)):
        raise ValueError('q and g must be finite')
    if not np.isfinite(floor_fraction) or not 0 <= floor_fraction < 1:
        raise ValueError('floor_fraction must lie in [0,1)')
    if dmp_relax is not None and (not np.isfinite(dmp_relax) or dmp_relax < 0):
        raise ValueError('dmp_relax must be nonnegative or None')
    if not np.isfinite(cfl) or not 0 < cfl <= 1:
        raise ValueError('cfl must lie in (0,1]')
    if low_endpoint not in ('cr_graph_minimal', 'cr_spectral', 'full_patch'):
        raise ValueError('unknown low_endpoint')
    a, b, dm = (np.asarray(geometry[k], dtype=float)
                for k in ('old_mass', 'new_mass', 'mass_delta'))
    if any(v.shape != (n,) or not np.all(np.isfinite(v)) for v in (a, b, dm)):
        raise ValueError('invalid geometry mass vectors')
    scale = max(np.max(np.abs(g), initial=0.), np.sum(a), np.sum(b),
                np.finfo(float).tiny)
    tolerance = 256*np.finfo(float).eps*scale
    if (np.any(a < 0) or np.any(b < 0) or np.sum(a) <= 0
            or abs(np.sum(dm)) > tolerance
            or np.max(np.abs(dm-(b-a))) > tolerance):
        raise ValueError('invalid or unbalanced changed-patch masses')
    outside = g-a
    gp = g+dm
    if np.any(g <= 0) or np.any(gp <= 0) or np.any(outside < -tolerance):
        raise ValueError('positive full masses and nonnegative exterior required')
    u = q/g[:, None]
    euler = q.shape[1] != 1
    if not np.all(np.isfinite(u)) or np.any(u[:, 0] <= 0):
        raise ValueError('input scalar/density must be strictly positive')
    ein = internal_energy_density(u) if euler else None
    if euler and (np.any(ein <= 0) or not np.all(np.isfinite(ein))):
        raise ValueError('input Euler internal energy must be strictly positive')
    density_floor = floor_fraction*float(np.min(u[:, 0]))
    energy_floor = floor_fraction*float(np.min(ein)) if euler else None
    old_min, old_max = float(u[:, 0].min()), float(u[:, 0].max())
    bound_tol = 128*np.finfo(float).eps*max(abs(old_min), abs(old_max),
                                         np.finfo(float).tiny)
    relaxation = 0 if dmp_relax is None else dmp_relax*(old_max-old_min)
    lower, upper = old_min-relaxation-bound_tol, old_max+relaxation+bound_tol

    def accepted(candidate, with_dmp=True):
        w = candidate/gp[:, None]
        if not np.all(np.isfinite(w)) or np.any(w[:, 0] <= density_floor):
            return False
        if euler and np.any(internal_energy_density(w) <= energy_floor):
            return False
        return (not with_dmp or dmp_relax is None
                or bool(np.all(w[:, 0] >= lower) and np.all(w[:, 0] <= upper)))

    if low_endpoint == 'full_patch':
        # Same low endpoint as audit_p1_ledger_remap.py. Only tolerate a
        # round-off negative exterior; do not clip it and alter conservation.
        low = outside[:, None]*u + b[:, None]*((a @ u)/a.sum())
        low_diag = {'steps': 0, 'positivity_cfl_satisfied': True}
    else:
        low, low_gp, low_diag = topological_remap(
            q, g, geometry, cfl=cfl, alpha_rule=low_endpoint.removeprefix('cr_'))
        if not np.array_equal(low_gp, gp):
            raise AssertionError('low endpoint used a different target mass')
    if not accepted(low):
        raise FloatingPointError('positive low endpoint failed requested bounds')

    # Existing constant conservative-density shift. For spatially affine U,
    # dm@U=0 because both P1 triangulations integrate affine fields exactly.
    defect = dm @ u
    high = gp[:, None]*(u-defect/gp.sum())
    high_positive, high_accepted = accepted(high, False), accepted(high)
    theta = 1.
    iterations = 0
    if high_accepted:
        result = high.copy()
    else:
        left, right = 0., 1.
        accepted_left = low.copy()
        for _ in range(60):
            midpoint = (left+right)/2
            candidate = (1-midpoint)*low+midpoint*high
            if accepted(candidate):
                left = midpoint
                accepted_left = candidate.copy()
            else:
                right = midpoint
        theta = left*(1.-1e-12)
        result = (1-theta)*low+theta*high
        iterations = 60
        # Floating-point evaluation is not strictly monotone at a tight DMP
        # boundary: retreating theta can round to a rejected value. Keep the
        # actual accepted bisection endpoint rather than halving theta and
        # adding macroscopic diffusion for a one-ulp predicate discrepancy.
        if not accepted(result):
            theta = left
            result = accepted_left
        assert accepted(result)

    final = result/gp[:, None]
    relative_conservation = float(np.max(
        np.abs(result.sum(axis=0)-q.sum(axis=0))/
        np.maximum(np.abs(q).sum(axis=0), np.finfo(float).tiny)))
    diag = dict(theta=float(theta), low_endpoint=low_endpoint,
                high_endpoint='existing_full_patch_uniform_shift',
                high_positive=bool(high_positive), high_accepted=bool(high_accepted),
                low_steps=low_diag['steps'], dmp_relax=dmp_relax,
                density_floor=density_floor, internal_energy_density_floor=energy_floor,
                min_final_density=float(final[:, 0].min()),
                min_final_internal_energy_density=(float(internal_energy_density(final).min())
                                                   if euler else None),
                max_density_dmp_violation=float(max(0., lower-final[:, 0].min(),
                                                     final[:, 0].max()-upper)),
                limiter_iterations=iterations,
                max_high_density_change=float(np.max(np.abs(high[:, 0]/gp-u[:, 0]))),
                relative_total_conservation_error=relative_conservation,
                positivity_cfl_satisfied=low_diag['positivity_cfl_satisfied'])
    return (result[:, 0] if scalar_vector else result), gp, diag
