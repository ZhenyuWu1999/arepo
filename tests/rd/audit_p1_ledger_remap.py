#!/usr/bin/env python3
"""Algebraic P1 transfer audit using the actual asynchronous Q,g ledger.

No Euler PDE is advanced here. Conditional positivity of one remap is distinct
from positivity of the remaining frozen-state transport. Earlier audit files
are left unchanged. NumPy is the only dependency.
"""
from fractions import Fraction as F
import json
import numpy as np


def admissible(w):
    if not np.all(np.isfinite(w)) or np.any(w[:, 0] <= 0):
        return False
    if w.shape[1] == 1:
        return True
    internal = w[:, 3] - np.sum(w[:, 1:3]**2, axis=1)/(2*w[:, 0])
    return bool(np.all(internal > 0))


def remap_ledger(q, g, a, b, variant='limited', relax=None):
    """a,b: same-time old/new changed-patch masses; g: actual geometric ledger.

    g-a contains untouched triangle masses at their own last-integrated times.
    Every correction acts on Q. This function does not overwrite frozen U;
    callers recover U only for vertices whose own interval is complete.
    Optional relaxed component bounds refer to W=Q/g, not pressure/entropy.
    """
    assert variant in ('high', 'low', 'limited')
    assert np.all(g > 0) and np.all(a >= 0) and np.all(b >= 0)
    outside = g-a
    assert np.all(outside >= 0)
    assert abs(a.sum()-b.sum()) < 1e-13*max(1., a.sum())
    gp = outside+b
    assert np.all(gp > 0)
    w = q/g[:, None]
    assert admissible(w), 'Remap positivity assumes an admissible incoming ledger'
    defect = (b-a) @ w
    high = gp[:, None]*(w-defect/gp.sum())
    average = (a @ w)/a.sum()
    low = outside[:, None]*w+b[:, None]*average
    assert admissible(low/gp[:, None])
    old_min, old_max = w.min(axis=0), w.max(axis=0)
    tolerance = ((relax or 0.)*(old_max-old_min)
                 + 128*np.finfo(float).eps*np.maximum(1., np.abs(w).max(axis=0)))

    def accepted(candidate):
        state = candidate/gp[:, None]
        return admissible(state) and (relax is None or
                bool(np.all(state >= old_min-tolerance) and np.all(state <= old_max+tolerance)))

    assert accepted(low)
    alpha = 1.
    if variant == 'low':
        alpha = 0.
    elif variant == 'limited' and not accepted(high):
        left, right = 0., 1.
        for _ in range(60):
            trial = (left+right)/2
            if accepted(low+trial*(high-low)):
                left = trial
            else:
                right = trial
        alpha = left*(1.-1e-12)
    result = low+alpha*(high-low)
    if variant != 'high':
        assert accepted(result)
    err = float(np.max(np.abs(result.sum(axis=0)-q.sum(axis=0))))
    return result, gp, dict(alpha=alpha, absolute_conservation_error=err,
                           high_admissible=admissible(high/gp[:, None]))


def exact_counterexamples():
    a = [F(1,3), F(1,6), F(1,3), F(1,6)]
    b = [F(1,6), F(1,3), F(1,6), F(1,3)]
    outside = [F(2,3), F(5,6), F(2,3), F(5,6)]
    old = [x+y for x,y in zip(outside,a)]
    new = [x+y for x,y in zip(outside,b)]
    rho = [F(1), F(8), F(1), F(8)]
    active_target = sum(m*r for m,r in zip(old,rho))-sum(new[i]*rho[i] for i in (1,3))
    assert active_target == F(-2,3)
    # Unit density and pressure do not protect the unlimited Euler high map.
    energy = F(21,2)
    velocity = [F(4), F(-4), F(4), F(-4)]
    dmomentum = sum((bp-ap)*v for bp,ap,v in zip(b,a,velocity))
    vhigh = [v-dmomentum/sum(new) for v in velocity]
    phigh = [F(2,5)*(energy-v*v/2) for v in vhigh]
    assert phigh[0] == F(-7,45)
    vavg = sum(ap*v for ap,v in zip(a,velocity))/sum(a)
    vlow = [(o*v+bp*vavg)/m for o,v,bp,m in zip(outside,velocity,b,new)]
    plow = [F(2,5)*(energy-v*v/2) for v in vlow]
    assert min(plow) > 1  # conserved-state convexity does not cap pressure/entropy.

    aa, bb = np.array(a,dtype=float), np.array(b,dtype=float)
    g = np.ones(4)
    q = np.array([.1,1.9,1.,1.])[:,None]
    frozen_u = np.ones((4,1))
    delta = bb-aa
    simple_increment = q+delta[:,None]*frozen_u  # D=0 for frozen uniform U.
    assert simple_increment[0,0] < 0
    mapped, gp, diag = remap_ledger(q,g,aa,bb,'limited',relax=.02)
    assert admissible(mapped/gp[:,None])
    # The missing asynchronous remainder is not numerically small by identity.
    omitted = (g+delta)[:,None]*frozen_u
    missing_remainder_error = float(np.max(np.abs(simple_increment-omitted)))
    assert missing_remainder_error > .8
    return dict(regular_star_active_only_target=str(active_target),
                regular_star_high_pressure=[str(x) for x in phigh],
                regular_star_low_pressure=[str(x) for x in plow],
                asynchronous_frozen_u_increment_min_q=float(simple_increment.min()),
                actual_ledger_remap_min_w=float((mapped/gp[:,None]).min()),
                omitted_history_error=missing_remainder_error,
                scope='Exact patch/algebra examples; asynchronous input reachability is not claimed')


def random_euler_audit(samples=2000):
    rng = np.random.default_rng(20260910)
    maximum_error = max_uniform_error = 0.
    limited = high_bad = 0
    min_alpha = 1.
    for _ in range(samples):
        xy = np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])+rng.uniform(-.12,.12,(4,2))
        def patch_mass(triangles):
            ans = np.zeros(4)
            for tri in triangles:
                i,j,k = tri
                v,z = xy[j]-xy[i],xy[k]-xy[i]
                ar = (v[0]*z[1]-v[1]*z[0])/2
                assert ar > 0
                ans[list(tri)] += ar/3
            return ans
        a = patch_mass(((0,1,2),(0,2,3)))
        b = patch_mass(((0,1,3),(1,2,3)))
        outside = 10**rng.uniform(-1.5,.5,4)
        g = outside+a
        rho,p = 10**rng.uniform(-2,2,(2,4))
        velocity = rng.normal(0,3,(4,2))
        w = np.column_stack((rho,rho[:,None]*velocity,
                             p/.4+.5*rho*np.sum(velocity**2,axis=1)))
        q = g[:,None]*w
        qp,gp,diag = remap_ledger(q,g,a,b,'limited',relax=.02)
        assert admissible(qp/gp[:,None])
        scale = max(1.,float(np.abs(q).sum()))
        maximum_error = max(maximum_error,diag['absolute_conservation_error']/scale)
        limited += diag['alpha'] < 1
        high_bad += not diag['high_admissible']
        min_alpha = min(min_alpha,diag['alpha'])
        constant = np.broadcast_to(w[0],w.shape)
        qc,gc,_ = remap_ledger(g[:,None]*constant,g,a,b,'limited',relax=.02)
        max_uniform_error = max(max_uniform_error,float(np.max(np.abs(qc/gc[:,None]-constant)))/max(1.,float(np.abs(constant).max())))
    assert maximum_error < 1e-13 and max_uniform_error < 1e-13
    return dict(samples=samples,high_inadmissible=high_bad,limited=limited,
                min_alpha=min_alpha,max_relative_conservation_error=maximum_error,
                max_relative_uniform_error=max_uniform_error,
                scope='Positive remap conditional on admissible incoming Q/g; no later-transport proof')


if __name__ == '__main__':
    print(json.dumps(dict(counterexamples=exact_counterexamples(),
                         euler_ledger_transfer=random_euler_audit()),indent=2))
