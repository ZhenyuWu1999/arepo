#!/usr/bin/env python3
"""Independent moving-tetra mathematics; no native moving-RD solver claim.

Cross products/temporal polynomials are checked against barycentric gradients,
face quadrature and Reynolds transport. Connectivity tests use manufactured
2-3/4-4 cavities and SciPy Delaunay changes at a common coordinate time.
The five-component transfer is a mathematical model, not production C.
"""
import argparse
from itertools import permutations
import json
from pathlib import Path

import numpy as np
from scipy.spatial import Delaunay

from test_euler_dimensions import flux


UNIT = np.vstack([np.zeros(3), np.eye(3)])
TIME, WEIGHT = np.polynomial.legendre.leggauss(2)
TIME, WEIGHT = (TIME + 1) / 2, WEIGHT / 2
FACE_BARY = np.full((3, 3), 1 / 6) + np.eye(3) / 2


def volume(x):
    return np.linalg.det(x[1:] - x[0]) / 6


def area_vectors(x):
    """Inward, signed-orientation-continuous vectors for positive tetrahedra."""
    out = np.empty((4, 3))
    for i in range(4):
        j, k, ell = [a for a in range(4) if a != i]
        out[i] = (-1) ** (i + 1) * np.cross(x[k] - x[j], x[ell] - x[j]) / 2
    return out


def average_vectors(x, displacement):
    old = area_vectors(x)
    mid = area_vectors(x + displacement / 2)
    new = area_vectors(x + displacement)
    return mid + (old - 2 * mid + new) / 6


def volume_polynomial(x, displacement):
    """Determinant multilinearity, ascending powers on s in [0,1]."""
    edge, delta = x[1:] - x[0], displacement[1:] - displacement[0]
    coeff = np.zeros(4)
    for mask in range(8):
        rows = [delta[i] if mask & (1 << i) else edge[i] for i in range(3)]
        coeff[mask.bit_count()] += np.linalg.det(rows) / 6
    return coeff


def volume_minimum(coeff):
    """All stationary points, including lower degree and repeated roots.

    This is a double-precision oracle, not a certified near-zero orientation
    predicate. The diagnostic implementation will need a scale/error policy.
    """
    roots = np.polynomial.polynomial.polyroots(np.arange(1, 4) * coeff[1:])
    candidates = [0., 1.]
    for z in roots:
        if abs(z.imag) <= 64 * np.finfo(float).eps * max(1., abs(z.real)) and 0 < z.real < 1:
            candidates.append(float(z.real))
    values = np.polynomial.polynomial.polyval(candidates, coeff)
    k = int(np.argmin(values))
    return candidates[k], float(values[k])


def boundary_transport(x, velocity, u):
    """Integral of u_h sigma_h.n_out; both fields P1 on each face."""
    result = np.zeros(u.shape[1])
    normals = area_vectors(x)
    for face in range(4):
        ids = [i for i in range(4) if i != face]
        uq, wq = FACE_BARY @ u[ids], FACE_BARY @ velocity[ids]
        result -= np.mean(uq * (wq @ normals[face])[:, None], axis=0)
    return result


def galilean(u, frame):
    result = u.copy()
    result[..., 1:4] -= u[..., :1] * frame
    result[..., 4] += .5 * (frame @ frame) * u[..., 0] - u[..., 1:4] @ frame
    return result


def alpha(normals, relative, sound):
    return np.max((abs(normals @ relative) + sound * np.linalg.norm(normals, axis=1)) / 3)


def check_geometry(rng):
    worst = dict(gradient=0., average=0., gcl=0., frozen_transport=0.,
                 contour=0., affine_reynolds=0., partition=0., galilean=0.,
                 volume_polynomial=0., minimum=0., cfl_bound=0.)
    for case in range(300):
        q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
        if np.linalg.det(q) < 0:
            q[:, 0] *= -1
        x = UNIT @ (q @ np.diag(rng.uniform(.5, 1.5, 3))).T + rng.uniform(-1, 1, 3)
        dt = rng.uniform(.02, .1)
        velocity = rng.normal(size=(4, 3))
        displacement = dt * velocity
        coeff = volume_polynomial(x, displacement)
        tmin, vmin = volume_minimum(coeff)
        assert vmin > 0
        vv = [volume(x + s * displacement) for s in np.linspace(0, 1, 19)]
        scale = max(vv)
        worst['volume_polynomial'] = max(worst['volume_polynomial'],
            np.max(abs(np.polynomial.polynomial.polyval(np.linspace(0, 1, 19), coeff) - vv)) / scale)
        worst['minimum'] = max(worst['minimum'], abs(volume(x + tmin * displacement) - vmin) / scale)
        assert vmin <= min(vv) + 1e-14 * scale

        inward = area_vectors(x)
        grad = np.linalg.inv(np.column_stack([np.ones(4), x]))[1:].T
        worst['gradient'] = max(worst['gradient'], np.max(abs(inward - 3 * volume(x) * grad)) / np.linalg.norm(inward))
        mean = average_vectors(x, displacement)
        integrated = sum(weight * area_vectors(x + s * displacement) for s, weight in zip(TIME, WEIGHT))
        worst['average'] = max(worst['average'], np.max(abs(mean - integrated)) / np.linalg.norm(mean))
        assert np.linalg.norm(mean.sum(axis=0)) < 1e-13 * np.linalg.norm(mean)
        np.testing.assert_array_equal(average_vectors(x, np.zeros((4, 3))), inward)
        # Reordering orientation by an even permutation changes only indexing.
        if case == 0:
            for p in permutations(range(4)):
                p = np.array(p)
                if volume(x[p]) > 0:
                    np.testing.assert_allclose(area_vectors(x[p]), inward[p], atol=1e-14)

        delta_v = volume(x + displacement) - volume(x)
        swept = dt * sum(weight * boundary_transport(x + s * displacement, velocity, np.ones((4, 1)))[0]
                         for s, weight in zip(TIME, WEIGHT))
        worst['gcl'] = max(worst['gcl'], abs(delta_v - swept) / scale)
        # Endpoint volume handles only Ubar * integral V'; spatially constant
        # divergence does not mean divergence is constant in time.
        u = rng.normal(size=(4, 5))
        exact = dt * sum(weight * boundary_transport(x + s * displacement, velocity, u)
                         for s, weight in zip(TIME, WEIGHT))
        split = delta_v * u.mean(axis=0) + dt * (velocity.mean(axis=0) @ mean.T) @ u / 3
        worst['frozen_transport'] = max(worst['frozen_transport'], np.max(abs(exact - split)) / (scale * max(1., abs(u).max())))

        # Contour = divergence of P1 nodal physical flux, not F(P1 U).
        rho, pressure = rng.uniform(.5, 2, (2, 4))
        vel = rng.uniform(-.3, .3, (4, 3))
        state = np.column_stack([rho, rho[:, None] * vel, pressure / .4 + .5 * rho * (vel * vel).sum(axis=1)])
        frame = velocity.mean(axis=0)
        shifted = galilean(state, frame)
        contour = sum(flux(state[i], mean[i], 1.4) - (frame @ mean[i]) * state[i] for i in range(4)) / 3
        face_total = np.zeros(5)
        for s, weight in zip(TIME, WEIGHT):
            ns = area_vectors(x + s * displacement)
            for face in range(4):
                ids = [i for i in range(4) if i != face]
                face_total -= weight * np.mean([flux(state[i], ns[face], 1.4) - (frame @ ns[face]) * state[i] for i in ids], axis=0)
        worst['contour'] = max(worst['contour'], np.max(abs(contour - face_total)) / max(1., abs(contour).max()))
        shifted_total = sum(flux(shifted[i], mean[i], 1.4) for i in range(4)) / 3
        worst['galilean'] = max(worst['galilean'], np.max(abs(galilean(contour, frame) - shifted_total)) / max(1., abs(shifted_total).max()))

        # Fixed Eulerian affine density: nodal values vary along trajectories.
        gradient = rng.uniform(-.1, .1, 3)
        density = lambda s: 2 + (x + s * displacement) @ gradient
        qdelta = volume(x + displacement) * density(1).mean() - volume(x) * density(0).mean()
        exact_affine = dt * sum(weight * boundary_transport(x + s * displacement, velocity, density(s)[:, None])[0]
                                for s, weight in zip(TIME, WEIGHT))
        worst['affine_reynolds'] = max(worst['affine_reynolds'], abs(qdelta - exact_affine) / (2 * scale))

        parts = np.zeros_like(mean)
        for a, b in ((0., .17), (.17, .63), (.63, 1.)):
            parts += (b - a) * average_vectors(x + a * displacement, (b - a) * displacement)
        worst['partition'] = max(worst['partition'], np.max(abs(mean - parts)) / np.linalg.norm(mean))
        # A conservative upper bound from quadratic Bernstein control vectors.
        n0, nh, n1 = [area_vectors(x + s * displacement) for s in (0., .5, 1.)]
        controls = (n0, 2 * nh - .5 * (n0 + n1), n1)
        relative, sound = rng.normal(size=3), rng.uniform(.3, 2.)
        bound = max(alpha(ns, relative, sound) for ns in controls)
        sampled = max(alpha(area_vectors(x + s * displacement), relative, sound) for s in np.linspace(0, 1, 41))
        worst['cfl_bound'] = max(worst['cfl_bound'], max(0., sampled - bound) / bound)
    assert max(worst.values()) < 2e-12, worst
    return dict(cases=300, max_normalized_defects=worst)


def spectral(x, state, positive):
    """Independent complex-step Euler Jacobian and spectral polynomials."""
    ns = area_vectors(x)
    rho, vel = state[0], state[1:4] / state[0]
    p = .4 * (state[4] - .5 * rho * (vel @ vel))
    c = np.sqrt(1.4 * p / rho)
    out = []
    for nn in ns:
        area = np.linalg.norm(nn)
        unit = nn / area
        eye = np.eye(5)
        jac = np.column_stack([np.imag(flux(state.astype(complex) + 1e-30j * eye[k], unit, 1.4)) / 1e-30 for k in range(5)])
        if not positive:
            out.append(area / 3 * jac)
            continue
        b = (jac - (vel @ unit) * eye) / c
        projectors = (.5 * (b @ b + b), .5 * (b @ b - b), eye - b @ b)
        lambdas = (vel @ unit + c, vel @ unit - c, vel @ unit)
        out.append(area / 3 * sum(max(0., ell) * pp for ell, pp in zip(lambdas, projectors)))
    return np.array(out)


def check_negative_controls():
    # Expansion has cubic volume and quadratic normals. All values are exact
    # rational formulas before numerical evaluation, avoiding random examples.
    exact_volume = volume(2 * UNIT) - volume(UNIT)
    mid_volume = boundary_transport(1.5 * UNIT, UNIT, np.ones((4, 1)))[0]
    assert abs(exact_volume - mid_volume) > .04
    density = lambda s: 1 + ((1 + s) * UNIT) @ np.array([.2, -.1, .3])
    expected = volume(2 * UNIT) * density(1).mean() - volume(UNIT) * density(0).mean()
    true_flux, midpoint_flux, average_frozen_flux = 0., 0., 0.
    averaged = average_vectors(UNIT, UNIT)
    for s, weight in zip(TIME, WEIGHT):
        true_flux += weight * boundary_transport((1 + s) * UNIT, UNIT, density(s)[:, None])[0]
        for face in range(4):
            ids = [i for i in range(4) if i != face]
            wq = FACE_BARY @ UNIT[ids]
            uq = FACE_BARY @ density(s)[ids]
            midpoint_flux -= weight * np.mean(uq * (wq @ area_vectors(1.5 * UNIT)[face]))
            average_frozen_flux -= weight * np.mean((FACE_BARY @ density(.5)[ids]) * (wq @ averaged[face]))
    assert abs(true_flux - expected) < 1e-14
    assert abs(midpoint_flux - expected) > .03
    # Time-varying nodal state and time-varying geometry have a correlation;
    # even exact mean normals times midpoint states do not integrate it.
    assert abs(average_frozen_flux - expected) > .005

    x = UNIT * np.array([-.18, -.32, 1.])
    displacement = UNIT * np.array([1., 1., .1])
    coeff = volume_polynomial(x, displacement)
    samples = [volume(x + s * displacement) for s in (0., .5, 1.)]
    tmin, vmin = volume_minimum(coeff)
    assert min(samples) > 0 and .18 < tmin < .32 and vmin < 0
    # Static / affine / quadratic / repeated stationary root cases.
    for c, want_s, want_v in (([1., 0., 0., 0.], 0., 1.),
                              ([1., -1., 0., 0.], 1., 0.),
                              ([.25, -1., 1., 0.], .5, 0.),
                              ([.875, .75, -1.5, 1.], 0., .875)):
        s, v = volume_minimum(np.array(c))
        assert abs(s - want_s) < 1e-14 and abs(v - want_v) < 1e-14

    displacement = 2 * np.array([[.2, -.1, .05], [.6, .2, -.1], [.1, -.2, .3], [-.2, .2, .5]])
    averaged = average_vectors(UNIT, displacement)
    # Use flux derivatives directly for the mean-normal operator; no claim
    # that the mean vectors describe the midpoint tetrahedron is needed.
    state = np.array([1., 0., 0., 0., 2.5])
    def from_vectors(ns, positive):
        # Reuse the spectral oracle by constructing a directional derivative.
        result = []
        for nn in ns:
            a = np.linalg.norm(nn); unit = nn / a; eye = np.eye(5)
            jac = np.column_stack([np.imag(flux(state.astype(complex) + 1e-30j * eye[k], unit, 1.4)) / 1e-30 for k in range(5)])
            if positive:
                b = jac / np.sqrt(1.4)
                jac = np.sqrt(1.4) * .5 * (b @ b + b)
            result.append(a / 3 * jac)
        return np.array(result)
    nodes, weights = np.polynomial.legendre.leggauss(48)
    plus_integral = sum(w / 2 * spectral(UNIT + (s + 1) / 2 * displacement, state, True) for s, w in zip(nodes, weights))
    full_integral = sum(w / 2 * spectral(UNIT + (s + 1) / 2 * displacement, state, False) for s, w in zip(nodes, weights))
    full_defect = np.max(abs(full_integral - from_vectors(averaged, False)))
    split_defect = np.max(abs(plus_integral - from_vectors(averaged, True)))
    assert full_defect < 1e-14 and split_defect > 1e-3
    mean_alpha = alpha(averaged, np.zeros(3), np.sqrt(1.4))
    maximum_alpha = max(alpha(area_vectors(UNIT + s * displacement), np.zeros(3), np.sqrt(1.4)) for s in np.linspace(0, 1, 101))
    assert maximum_alpha > 1.1 * mean_alpha
    return dict(expansion=dict(exact_volume_change=exact_volume, midpoint_volume_change=mid_volume,
                               affine_exact_change=expected, affine_gauss2=true_flux,
                               affine_midpoint_normals=midpoint_flux, affine_mean_normals_frozen_state=average_frozen_flux),
                hidden_inversion=dict(coefficients=coeff.tolist(), endpoint_midpoint_volumes=samples,
                                      argmin=tmin, minimum=vmin),
                spectral=dict(full_K_mean_defect=full_defect, split_K_mean_defect=split_defect,
                              mean_alpha=mean_alpha, maximum_alpha=maximum_alpha))


def check_campoli(rng):
    """A periodic 3^3-node, 162-tetra ledger with conservative model splits.

    Tests the complete equal-step mass algebra, independently of any N/LDA
    characteristic distribution. A midpoint-normal control uses the same
    endpoint masses and deliberately fails nonuniform global conservation.
    """
    cells, dt = 3, .02
    count = cells ** 3
    velocity = rng.uniform(-.4, .4, (count, 3))
    rho, pressure = rng.uniform(.8, 1.2, (2, count))
    vel = rng.uniform(-.2, .2, (count, 3))
    initial = np.column_stack([rho, rho[:, None] * vel, pressure / .4 + .5 * rho * (vel * vel).sum(axis=1)])
    elements = []
    m0, m1 = np.zeros(count), np.zeros(count)
    for cell in np.ndindex(cells, cells, cells):
        for order in permutations(range(3)):
            corners = [np.zeros(3, dtype=int)]
            for axis in order:
                corner = corners[-1].copy(); corner[axis] += 1
                corners.append(corner)
            integer = np.array(cell) + corners
            ids = np.ravel_multi_index((integer % cells).T, (cells, cells, cells))
            x = integer / cells
            if volume(x) < 0:
                ids[[0, 1]] = ids[[1, 0]]; x[[0, 1]] = x[[1, 0]]
            w = velocity[ids]
            old, new = volume(x), volume(x + dt * w)
            assert volume_minimum(volume_polynomial(x, dt * w))[1] > 0
            m0[ids] += old / 4; m1[ids] += new / 4
            elements.append((ids, average_vectors(x, dt * w), area_vectors(x + dt * w / 2), w.mean(axis=0), (old + new) / 2))
    assert abs(m0.sum() - 1) < 1e-14 and abs(m1.sum() - 1) < 1e-14

    def spatial(u, ids, ns, frame):
        total = sum(flux(u[i], nn, 1.4) - (frame @ nn) * u[i] for i, nn in zip(ids, ns)) / 3
        # Noncentral zero-sum part, to test independence from the split.
        return total / 4 + .003 * (u[ids] - u[ids].mean(axis=0))

    records = []
    for uniform in (False, True):
        u0 = initial if not uniform else np.tile([1., .1, -.2, .3, 2.6], (count, 1))
        for f1 in (False, True):
            for midpoint in (False, True):
                predictor = np.zeros_like(u0)
                for ids, mean, mid, frame, mass in elements:
                    predictor[ids] += spatial(u0, ids, mid if midpoint else mean, frame)
                du = -dt * predictor / m1[:, None]
                star = u0 + du
                assert np.all(star[:, 0] > 0) and np.all(internal(star) > 0)
                # The corrector starts from Q*, then adds the local +1/2 dQ*.
                qnew = m1[:, None] * star + .5 * m1[:, None] * du
                for ids, mean, mid, frame, mass in elements:
                    temporal = mass / 4 * du[ids] / dt
                    if f1:
                        target = temporal.sum(axis=0)
                        temporal = np.array([.1, .2, .3, .4])[:, None] * target
                    qnew[ids] -= dt * (temporal + .5 * spatial(star, ids, mid if midpoint else mean, frame))
                qold = m0[:, None] * u0
                defect = np.max(abs(qnew.sum(axis=0) - qold.sum(axis=0))) / np.sum(abs(qold))
                uniform_error = np.max(abs(qnew / m1[:, None] - u0)) if uniform else None
                if not midpoint or uniform:
                    assert defect < 2e-13
                else:
                    assert defect > 1e-10, 'midpoint control did not expose the cubic geometry error'
                if uniform:
                    assert uniform_error < 2e-13
                records.append(dict(uniform=uniform, f1_model=f1, midpoint_control=midpoint,
                                    conservation_defect=defect, uniform_error=uniform_error))
    return dict(primary_nodes=count, tetrahedra=len(elements), dt=dt, cases=records,
                scope='complete Campoli ledger with model conservative splits, not production N/LDA')


def positive_tets(x, tets):
    out = np.array(tets, dtype=int).copy()
    for tet in out:
        if volume(x[tet]) < 0:
            tet[0], tet[1] = tet[1], tet[0]
    return out


def nodal_mass(x, tets):
    mass = np.zeros(len(x))
    for tet in sorted(tets, key=lambda t: tuple(sorted(t))):
        assert volume(x[tet]) > 1e-13, 'inverted/degenerate cavity tetra at the common comparison time'
        # Canonical vertex and summation order for unchanged-outside checks.
        canonical = positive_tets(x, [sorted(tet)])[0]
        v = volume(x[canonical])
        mass[tet] += v / 4
    return mass


def internal(u):
    return u[:, 4] - (u[:, 1:4] ** 2).sum(axis=1) / (2 * u[:, 0])


def transfer_model(g, dm, u, mode):
    """Model the published donor/receiver construction with five components."""
    new = g + dm
    donors, receivers = dm < 0, dm > 0
    assert np.all(new > 0)
    donor_mass, receiver_mass = -dm[donors].sum(), dm[receivers].sum()
    assert abs(donor_mass - receiver_mass) < 1e-13 * g.sum()
    if donor_mass == 0:
        return u.copy(), 1.
    ud = (-dm[donors]) @ u[donors] / donor_mass
    ur = dm[receivers] @ u[receivers] / receiver_mass
    low = u.copy()
    low[receivers] = (g[receivers, None] * u[receivers] + dm[receivers, None] * ud) / new[receivers, None]
    high = u.copy()
    if mode == 0:
        high -= (dm @ u) / new.sum()
    else:
        high[receivers] += dm[receivers, None] / new[receivers, None] * (ud - ur)
    floors = .5 * np.array([u[:, 0].min(), internal(u).min()])
    def blend(theta):
        if theta == 1:
            return high.copy()
        return np.where(low == high, low, (1 - theta) * low + theta * high)
    def ok(value):
        return np.isfinite(value).all() and np.all(value[:, 0] > floors[0]) and np.all(internal(value) > floors[1])
    assert ok(low)
    theta = 1.
    if not ok(high):
        lo, hi = 0., 1.
        for _ in range(60):
            mid = (lo + hi) / 2
            if ok(blend(mid)):
                lo = mid
            else:
                hi = mid
        theta = lo
    out = blend(theta)
    assert ok(out)
    if mode == 1:
        np.testing.assert_array_equal(out[donors], u[donors])
    return out, theta


def changed_cavities(old, new):
    oldkeys, newkeys = {tuple(sorted(t)) for t in old}, {tuple(sorted(t)) for t in new}
    removed, inserted = oldkeys - newkeys, newkeys - oldkeys
    components = []
    for tet in sorted(removed | inserted):
        vertices = set(tet)
        touching = [group for group in components if group & vertices]
        for group in touching:
            vertices |= group
            components.remove(group)
        components.append(vertices)
    return [(sorted(group), [t for t in sorted(removed) if set(t) <= group],
             [t for t in sorted(inserted) if set(t) <= group]) for group in components]


def check_cavities(rng):
    bipyramid = np.array([[0, 0, 0], [1, 0, 0], [.5, np.sqrt(3) / 2, 0], [.5, .25, 1], [.5, .25, -.7]])
    two = [[0, 1, 2, 3], [0, 2, 1, 4]]
    three = [[3, 4, 0, 1], [3, 4, 1, 2], [3, 4, 2, 0]]
    octahedron = np.array([[1, 0, 0], [0, 1, 0], [-1, 0, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1.]])
    four_z = [[4, 5, i, (i + 1) % 4] for i in range(4)]
    ring = [1, 4, 3, 5]
    four_x = [[0, 2, ring[i], ring[(i + 1) % 4]] for i in range(4)]
    instances = []
    for _ in range(50):
        q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
        if np.linalg.det(q) < 0:
            q[:, 0] *= -1
        transform = q @ np.diag(rng.uniform(.5, 1.5, 3))
        offset = rng.uniform(-1, 1, 3)
        for x, old, new, kind in ((bipyramid, two, three, '2-3'), (bipyramid, three, two, '3-2'),
                                  (octahedron, four_z, four_x, '4-4')):
            x = x @ transform.T + offset
            instances.append((x, positive_tets(x, old), positive_tets(x, new), kind))
    # Fixed triangular hull, moving interior vertices; compare both valid
    # triangulations at x_new. This measures synthetic cavities, not AREPO.
    attempts, large_sets = 0, 0
    while large_sets < 20 and attempts < 300:
        attempts += 1
        interior = rng.normal(size=(14, 3))
        interior *= rng.uniform(.05, .65, (14, 1)) / np.sum(abs(interior), axis=1)[:, None]
        oldx = np.vstack([octahedron, interior])
        newx = oldx.copy(); newx[6:] += rng.normal(size=(14, 3)) * .015
        old = positive_tets(oldx, Delaunay(oldx).simplices)
        new = positive_tets(newx, Delaunay(newx).simplices)
        if min(volume(newx[t]) for t in old) <= 1e-10:
            continue  # Invalid pullbacks are not transfer cases; M2 records them.
        if not changed_cavities(old, new):
            continue
        instances.append((newx, old, new, 'Delaunay'))
        large_sets += 1
    assert large_sets == 20
    worst = dict(volume=0., first_moment=0., conservation=0., uniform=0., affine=0.)
    count, limited, max_vertices = 0, 0, 0
    kinds = {}
    for x, old, new, kind in instances:
        a, b = nodal_mass(x, old), nodal_mass(x, new)
        components = changed_cavities(old, new)
        used = set()
        accumulated_dm = np.zeros(len(x))
        for ids, removed, inserted in components:
            used |= set(ids)
            am = nodal_mass(x, positive_tets(x, removed))
            bm = nodal_mass(x, positive_tets(x, inserted))
            dm = bm - am
            accumulated_dm += dm
            worst['volume'] = max(worst['volume'], abs(dm.sum()) / am.sum())
            worst['first_moment'] = max(worst['first_moment'], np.max(abs(dm @ x)) / (am.sum() * max(1., abs(x).max())))
            if len(components) == 1:
                np.testing.assert_allclose(dm, b - a, atol=1e-14)
            ids = np.array(ids)
            # Full star mass includes unchanged tetra plus a positive exterior.
            g = a[ids] + rng.uniform(.02, .2, len(ids)) * a.sum()
            dm = dm[ids]; xx = x[ids]
            rho = 10 ** rng.uniform(-2, 2, len(ids))
            vel = rng.uniform(-3, 3, (len(ids), 3))
            pressure = 10 ** rng.uniform(-3, 5, len(ids))
            u = np.column_stack([rho, rho[:, None] * vel, pressure / .4 + .5 * rho * (vel * vel).sum(axis=1)])
            contrast = np.zeros_like(u); contrast[:, 0] = 1; contrast[:, 4] = .0025
            contrast[0, 4] = 250000.  # Exact input energy contrast 1e8.
            beams = np.zeros_like(u); beams[:, 0] = 1
            beams[:, 1:4] = np.where((np.arange(len(ids)) % 2)[:, None] == 0, 1., -1.) * np.array([10., -20., 30.])
            beams[:, 4] = .025 + (beams[:, 1:4] ** 2).sum(axis=1) / 2
            for mode in (0, 1):
                for field in (u, contrast, beams):
                    out, theta = transfer_model(g, dm, field, mode)
                    # Components identically zero use the density scale.
                    scales = np.maximum(g @ abs(field), (g @ field[:, 0]) * np.finfo(float).eps)
                    error = np.max(abs((g + dm) @ out - g @ field) / scales)
                    worst['conservation'] = max(worst['conservation'], error)
                    limited += theta < 1
                    count += 1
                for field, key in ((np.tile([1., .1, -.2, .3, 10.], (len(ids), 1)), 'uniform'),
                                   (np.tile([1., .1, -.2, .3, 10.], (len(ids), 1)) + xx @ rng.uniform(-.001, .001, (3, 5)), 'affine')):
                    mapped, t = transfer_model(g, dm, field, mode)
                    assert t == 1
                    worst[key] = max(worst[key], np.max(abs(mapped - field)) / abs(field).max())
            max_vertices = max(max_vertices, len(ids))
            kinds[kind] = kinds.get(kind, 0) + 1
        outside = [i for i in range(len(x)) if i not in used]
        np.testing.assert_array_equal(a[outside], b[outside])
        np.testing.assert_allclose(accumulated_dm, b - a, atol=1e-14)
    assert max(worst.values()) < 2e-12, worst
    assert max_vertices > 6
    return dict(cavities_by_family=kinds, transfer_cases=count, limited=int(limited),
                max_vertices=max_vertices, delaunay_attempts=attempts,
                max_normalized_defects=worst)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='new JSON result path (never overwrite)')
    args = parser.parse_args()
    rng = np.random.default_rng(20261011)
    result = dict(seed=20261011, geometry=check_geometry(rng),
                  negative_controls=check_negative_controls(), campoli=check_campoli(rng), cavities=check_cavities(rng),
                  scope='independent geometry/transfer model; no production moving solver or nodal affine RK2 proof')
    payload = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as handle:
            handle.write(payload)
    print(payload, end='')
    print('PASS: moving-tetra identities and explicit negative controls; model only')


if __name__ == '__main__':
    main()
