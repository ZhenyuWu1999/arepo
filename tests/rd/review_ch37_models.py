#!/usr/bin/env python3
"""Audit log3 section 37's scalar F1 model; not an AREPO integration test.

Compare the reported (wrapped-index, unwrapped-coordinate) mesh with a true
periodic lift. Retain its point pattern, scalar LDA/F1, alternating mask and
Heun diagnostic ODEs. No due-triangle or frozen-star scheduler is simulated.
Run with OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 and one JSON output path.
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix, diags, eye
from scipy.sparse.linalg import svds


def assemble(n, periodic_lift):
    idx = lambda i, j: (i % n) * n + j % n
    pts = np.array([[(i + .37 * np.sin(2*np.pi*j/n))/n,
                     (j + .21 * np.cos(2*np.pi*i/n))/n]
                    for i in range(n) for j in range(n)])
    triangles = []
    for i in range(n):
        for j in range(n):
            a, b, c, d = idx(i,j), idx(i+1,j), idx(i+1,j+1), idx(i,j+1)
            triangles.extend(((a,b,c), (a,c,d)))
    s = np.zeros(n*n)
    rows, cols, masses, residuals, signed_areas = [], [], [], [], []
    largest_edge = 0.
    for tri in triangles:
        p = pts[list(tri)].copy()
        if periodic_lift:
            delta = p-p[0]
            p = p[0] + delta-np.rint(delta)
        e1, e2 = p[1]-p[0], p[2]-p[0]
        signed_area = .5*(e1[0]*e2[1]-e1[1]*e2[0])
        signed_areas.append(signed_area)
        area = abs(signed_area)
        edges = p[[2,0,1]]-p[[1,2,0]]
        largest_edge = max(largest_edge, float(np.linalg.norm(edges, axis=1).max()))
        inward_half = .5*np.column_stack((-edges[:,1], edges[:,0]))
        k = inward_half @ np.array([1., .4])
        positive = np.maximum(k, 0.)
        beta = positive/positive.sum()
        for m, i in enumerate(tri):
            s[i] += area/3
            for l, j in enumerate(tri):
                rows.append(i)
                cols.append(j)
                masses.append(beta[m]*area/3)
                residuals.append(beta[m]*k[l])
    shape = (n*n, n*n)
    mass = coo_matrix((masses, (rows, cols)), shape=shape).tocsr()
    residual = coo_matrix((residuals, (rows, cols)), shape=shape).tocsr()
    error = eye(n*n, format='csr') - diags(1/s)@mass
    ones = np.ones(n*n)
    norm = float(svds(error, k=1, which='LM', return_singular_vectors=False,
                      v0=np.linspace(.5, 1.5, n*n), tol=1.e-11)[0])
    diagnostics = dict(n=n, area_total=float(s.sum()),
                       negative_orientation=int(np.count_nonzero(np.array(signed_areas)<0)),
                       largest_edge=largest_edge, operator_norm_2=norm,
                       E_constant_max=float(np.max(np.abs(error@ones))),
                       R_constant_max=float(np.max(np.abs(residual@ones))),
                       mass_column_defect=float(np.max(np.abs(np.asarray(mass.sum(axis=0)).ravel()-s))),
                       conservation_column_defect=float(np.max(np.abs(np.asarray(residual.sum(axis=0)).ravel()))))
    if periodic_lift:
        assert abs(s.sum()-1) < 1.e-13
        assert diagnostics['negative_orientation'] == 0
        assert largest_edge < 2/n
    assert diagnostics['mass_column_defect'] < 1.e-13
    assert diagnostics['R_constant_max'] < 1.e-13
    assert diagnostics['conservation_column_defect'] < 1.e-13
    return pts, s, mass, residual, error, diagnostics


def integrate(model):
    pts, s, mass, residual, error, diagnostics = model
    count = len(s)
    u0 = 1 + .3*np.sin(2*np.pi*pts[:,0])*np.cos(2*np.pi*pts[:,1])
    live = (np.arange(count)%2 == 0).astype(float)
    rate_matrix = -diags(1/s)@residual
    eq = rate_matrix + error@rate_matrix
    masked = rate_matrix + error@diags(live)@rate_matrix
    active_stale = rate_matrix + error@diags(live)@rate_matrix
    v = rate_matrix@u0
    direct = masked@u0-eq@u0
    identity = -error@((1-live)*v)
    assert np.max(np.abs(direct-identity)) < 1.e-12
    jacobi = v + (-residual@u0-mass@v)/s
    assert np.max(np.abs(jacobi-eq@u0)) < 1.e-12
    out = []
    for steps in (50, 100, 200, 400, 800, 1600):
        dt = .05/steps
        ue, um, us = u0.copy(), u0.copy(), u0.copy()
        cache = np.zeros(count)
        for tick in range(steps):
            k1 = eq@ue
            ue += .5*dt*(k1 + eq@(ue+dt*k1))
            k1 = masked@um
            um += .5*dt*(k1 + masked@(um+dt*k1))
            if tick%2 == 0:
                # A globally assembled rate, cached every two ticks.
                cache = error@((1-live)*(rate_matrix@us))
            k1 = active_stale@us+cache
            us += .5*dt*(k1 + active_stale@(us+dt*k1)+cache)
        row = dict(steps=steps, dt=dt,
                   masked_vs_equal_mean_L1=float(np.mean(np.abs(um-ue))),
                   stale_vs_equal_mean_L1=float(np.mean(np.abs(us-ue))),
                   masked_vs_equal_area_L1=float(s@np.abs(um-ue)/s.sum()),
                   stale_vs_equal_area_L1=float(s@np.abs(us-ue)/s.sum()),
                   max_mass_drift=float(max(abs(s@(u-u0)) for u in (ue,um,us))))
        assert row['max_mass_drift'] < 1.e-12
        out.append(row)
    return dict(initial_relative_rate_difference=float(np.linalg.norm(direct)/np.linalg.norm(eq@u0)),
                ladder=out)


def main():
    report = {'scope': __doc__, 'geometry': {}, 'model_ladders': {}}
    for name, lift in [('original_coordinate_handling', False), ('periodically_lifted', True)]:
        report['geometry'][name] = []
        for n in (12,24,48):
            model = assemble(n, lift)
            report['geometry'][name].append(model[-1])
            if n == 24:
                report['model_ladders'][name] = integrate(model)
    h = np.array([1., .5, .25])
    observed = np.array([6.15304e-4, 1.67929e-4, 5.13448e-5])
    design = np.column_stack((h*h, h))
    coeff = np.linalg.lstsq(design, observed, rcond=None)[0]
    predicted = design@coeff
    report['two_term_fit'] = dict(coefficients=coeff.tolist(), predicted=predicted.tolist(),
        observed_slopes=np.log2(observed[:-1]/observed[1:]).tolist(),
        fitted_slopes=np.log2(predicted[:-1]/predicted[1:]).tolist(),
        fitted_linear_shares=(coeff[1]*h/predicted).tolist(),
        caveat='An assumed scalar L1 fit neither measures signed temporal error nor identifies its cause.')
    path = Path(sys.argv[1])
    with path.open('x') as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
