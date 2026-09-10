#!/usr/bin/env python3
"""Representation and scalar flux-lifting audit, not an Euler/ALE integrator.

Shows a P1 mass jump versus continuous true Voronoi areas on a perturbed
square, and checks that scalar N corner contributions can be represented by
one common flux vector when the three corner normals close and have rank 2.
Requires NumPy. Optional scientific plot requires Matplotlib.
"""
import argparse
import json
from pathlib import Path
import numpy as np


def area(p):
    return .5*np.sum(p[:, 0]*np.roll(p[:, 1], -1)-p[:, 1]*np.roll(p[:, 0], -1))


def clip(p, normal, offset):
    result = []
    for a, b in zip(p, np.roll(p, -1, axis=0)):
        fa, fb = a @ normal-offset, b @ normal-offset
        ia, ib = fa <= 0., fb <= 0.
        if ia:
            result.append(a)
        if ia != ib:
            result.append(a+(b-a)*fa/(fa-fb))
    return np.asarray(result)


def square(epsilon, diagonal=None):
    x = np.array([[0., 0.], [1., 0.], [1., 1.+epsilon], [0., 1.]])
    if diagonal is None:
        diagonal = 'ac' if epsilon < 0 else 'bd'
    triangles = [(0, 1, 2), (0, 2, 3)] if diagonal == 'ac' else [(0, 1, 3), (1, 2, 3)]
    mass = np.zeros(4)
    for t in triangles:
        mass[list(t)] += area(x[list(t)])/3
    voronoi = np.zeros(4)
    for i in range(4):
        cell = x.copy()
        for j in range(4):
            if i != j:
                cell = clip(cell, 2*(x[j]-x[i]), x[j] @ x[j]-x[i] @ x[i])
        voronoi[i] = area(cell)
    assert abs(mass.sum()-area(x)) < 1e-14
    assert abs(voronoi.sum()-area(x)) < 1e-14
    return mass, voronoi


def audit():
    old, v = square(0., 'ac')
    new, _ = square(0., 'bd')
    jump = new-old
    u = np.array([2., 1., 1., 1.])
    assert np.max(np.abs(jump-np.array([-1., 1., -1., 1.])/6)) < 1e-15
    assert abs(jump @ u+1/6) < 1e-15
    assert np.max(abs(v-.25)) < 1e-15
    continuity = []
    for eps in (1e-2, 1e-4, 1e-6, 1e-8):
        mm, vm = square(-eps)
        mp, vp = square(eps)
        dv = float(np.max(abs(vp-vm)))
        assert dv < 2*eps
        continuity.append(dict(epsilon=eps, max_P1_mass_difference=float(np.max(abs(mp-mm))),
                               max_Voronoi_volume_difference=dv))
    rng = np.random.default_rng(20260909)
    worst_sum = worst_lift = worst_uniform = 0.
    for _ in range(1000):
        theta = rng.uniform(-np.pi, np.pi)
        rotation = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
        transform = rotation @ np.diag(rng.uniform(.5, 2., 2))
        # Outward corner vectors, summing to zero; not physical Delaunay
        # triangle normals taken from AREPO, which cannot be substituted blindly.
        normal = np.array([[1., 0.], [-.4, .8], [-.6, -.8]]) @ transform.T
        relative = rng.uniform(-1., 1., 2)
        values = rng.uniform(.2, 2., 3)
        k = -normal @ relative
        kp, km = np.maximum(k, 0), np.minimum(k, 0)
        incoming = (km @ values)/km.sum()
        phi = kp*(values-incoming)
        corner_flux = -k*values+phi
        lifted, _, rank, _ = np.linalg.lstsq(normal, corner_flux, rcond=None)
        assert rank == 2
        worst_sum = max(worst_sum, abs(float(corner_flux.sum())))
        worst_lift = max(worst_lift, float(np.max(abs(normal @ lifted-corner_flux))))
        # A uniform state has zero N fluctuation and the physical ALE flux.
        uniform_flux = -k*1.3
        uniform_lift, *_ = np.linalg.lstsq(normal, uniform_flux, rcond=None)
        worst_uniform = max(worst_uniform, float(np.max(abs(uniform_lift-1.3*relative))))
    assert max(worst_sum, worst_lift, worst_uniform) < 1e-13
    return dict(square_P1_old=old.tolist(), square_P1_new=new.tolist(),
                square_Voronoi=v.tolist(), unchanged_nodal_scalar_integral_jump=float(jump @ u),
                continuity=continuity, scalar_corner_cases=1000,
                max_corner_flux_sum=worst_sum, max_flux_lifting_error=worst_lift,
                max_uniform_flux_lifting_error=worst_uniform,
                scope='Local representation and scalar algebra only; no full Euler, moving-step GCL, LTS accuracy or MPI test')


def plot(path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), layout='constrained')
    for eps in (np.linspace(-.08, -1e-9, 120), np.linspace(1e-9, .08, 120)):
        values = np.array([square(e) for e in eps])
        axes[0].plot(eps, values[:, 0, 0], color='#b94b38', lw=2.3)
        axes[0].plot(eps, values[:, 1, 0], color='#24749b', lw=2.3)
    axes[0].plot([], [], color='#b94b38', lw=2.3, label='P1 mass coefficient at A')
    axes[0].plot([], [], color='#24749b', lw=2.3, label='True Voronoi area at A')
    axes[0].axvline(0, color='0.55', lw=.8, ls='--')
    axes[0].set(xlabel='Vertical displacement of C', ylabel='Area within quadrilateral',
                title='Same moving points, different representation')
    axes[0].legend(frameon=False, fontsize=9)
    for shift, diagonal, label in [(0., 'ac', 'Before: diagonal AC'), (1.55, 'bd', 'After: diagonal BD')]:
        x = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])+[shift, 0]
        axes[1].plot(*np.vstack((x, x[:1])).T, color='0.25')
        pair = [0, 2] if diagonal == 'ac' else [1, 3]
        axes[1].plot(*x[pair].T, color='#b94b38', lw=2)
        m, _ = square(0., diagonal)
        for i, p in enumerate(x):
            axes[1].scatter(*p, s=18, color='0.25')
            offset = [-.05, -.15] if i < 2 else [-.05, .10]
            axes[1].text(*(p+offset), f'{"ABCD"[i]}: {m[i]:.3f}', ha='center', fontsize=9)
        axes[1].text(shift+.5, -.45, label, ha='center', fontsize=9)
    axes[1].set(title='At the exact cocircular event', aspect='equal', xlim=(-.4, 3.), ylim=(-.65, 1.35))
    axes[1].axis('off')
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plot')
    args = parser.parse_args()
    print(json.dumps(audit(), indent=2))
    if args.plot:
        plot(args.plot)
