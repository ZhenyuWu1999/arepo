#!/usr/bin/env python3
"""Independent scalar ALE-RD feasibility experiment, NOT the native Euler solver.

Begin: predict on the old connectivity with forward-computed slab geometry.
Between hooks: move nodes and construct exactly one periodic Delaunay mesh.
End: correct on the retained, deformed old triangles; optionally transfer to
the new P1 basis using the previously documented conservative patch map.

The Campoli endpoint mass pair is used, with scalar N/lumped or LDA/F1.
The unsafe controls keep nodal U, keep extensive Q, or switch the corrector's
element set without a consistent transfer. All use the same prescribed paths.
"""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np
from scipy.spatial import Delaunay

ADVECTION = np.array([1.0, 0.4])


def area(p):
    a, b = p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]
    return 0.5 * (a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0])


def scatter(ids, value, n):
    out = np.zeros((n,) + value.shape[2:])
    np.add.at(out, ids.ravel(), value.reshape((-1,) + value.shape[2:]))
    return out


def masses(ids, areas, n):
    return np.bincount(ids.ravel(), weights=np.repeat(areas / 3, 3), minlength=n)


@dataclass
class Mesh:
    ids: np.ndarray
    p: np.ndarray
    n: int

    @property
    def mass(self):
        return masses(self.ids, area(self.p), self.n)


def triangulate(x):
    """One Qhull call; coherent periodic images, selected by triangle centroid."""
    shifts = np.array([(i, j) for i in (-1, 0, 1) for j in (-1, 0, 1)])
    tiled = (x[None, :, :] + shifts[:, None, :]).reshape(-1, 2)
    tri = Delaunay(tiled).simplices
    centre = tiled[tri].mean(axis=1)
    tri = tri[np.all((centre >= 0) & (centre < 1), axis=1)]
    p = tiled[tri]
    reverse = area(p) < 0
    tri[reverse] = tri[reverse][:, [0, 2, 1]]
    mesh = Mesh(tri % len(x), tiled[tri], len(x))
    assert len(tri) == 2 * len(x)
    assert len(set(map(tuple, np.sort(mesh.ids, axis=1)))) == len(tri)
    assert np.min(area(mesh.p)) > 0
    assert abs(mesh.mass.sum() - 1) < 2e-13
    return mesh


def points(n):
    rng = np.random.default_rng(20260914 + n)
    x, y = np.meshgrid((np.arange(n) + 0.5) / n, (np.arange(n) + 0.5) / n)
    return (np.column_stack((x.ravel(), y.ravel())) + rng.uniform(-0.18, 0.18, (n*n, 2)) / n) % 1


def velocities(x, motion):
    v = np.tile([0.3, 0.1], (len(x), 1))
    if motion == 'deform':
        v += np.column_stack((0.15*np.sin(2*np.pi*x[:, 1]), 0.10*np.sin(2*np.pi*x[:, 0])))
    return v


def exact(x, t, uniform=False):
    if uniform:
        return np.ones(len(x))
    z = x - t * ADVECTION
    return 1 + .2*np.sin(2*np.pi*z[:, 0]) + .1*np.cos(2*np.pi*z[:, 1])


@dataclass
class Slab:
    mesh: Mesh
    dt: float
    m0: np.ndarray
    m1: np.ndarray
    b: np.ndarray
    k: np.ndarray
    beta: np.ndarray
    p1: np.ndarray


def slab(mesh, v, dt):
    p0 = mesh.p
    p1 = p0 + dt*v[mesh.ids]
    pm = (p0 + p1) / 2
    a0, a1 = area(p0), area(p1)
    assert np.min(a0) > 0 and np.min(a1) > 0 and np.min(area(pm)) > 0, 'retained triangle inversion'
    edge = pm[:, [2, 0, 1]] - pm[:, [1, 2, 0]]
    inward = np.stack((-edge[:, :, 1], edge[:, :, 0]), axis=-1)
    relative = ADVECTION - v[mesh.ids].mean(axis=1)
    k = .5*np.einsum('tij,tj->ti', inward, relative)
    assert np.max(abs(k.sum(axis=1))) < 2e-15
    kp = np.maximum(k, 0)
    denom = kp.sum(axis=1)
    beta = np.divide(kp, denom[:, None], out=np.full_like(kp, 1/3), where=denom[:, None] > 1e-30)
    return Slab(mesh, dt, masses(mesh.ids, a0, mesh.n), masses(mesh.ids, a1, mesh.n),
                .5*(a0+a1), k, beta, p1)


def residual(s, u, method):
    q = u[s.mesh.ids]
    if method == 'lda_f1':
        element = s.beta * np.sum(s.k*q, axis=1)[:, None]
    else:
        km = np.minimum(s.k, 0)
        denom = km.sum(axis=1)
        inflow = np.divide(np.sum(km*q, axis=1), denom, out=q.mean(axis=1), where=abs(denom)>1e-30)
        element = np.maximum(s.k, 0) * (q-inflow[:, None])
    return scatter(s.mesh.ids, element, s.mesh.n)


def mass_action(s, du, method):
    d = du[s.mesh.ids]
    if method == 'lda_f1':
        local = (s.b/3)[:, None] * s.beta * d.sum(axis=1)[:, None]
    else:
        local = (s.b/3)[:, None] * d
    return scatter(s.mesh.ids, local, s.mesh.n)


def begin(mesh, v, u, dt, method):
    s = slab(mesh, v, dt)
    r0 = residual(s, u, method)
    star = u - dt*r0/s.m1
    return s, u.copy(), star, r0


def end(saved, method, switched_slab=None):
    s, u0, star, r0 = saved
    if switched_slab is not None:
        s = switched_slab
    r1 = residual(s, star, method)
    return star - (mass_action(s, star-u0, method) + .5*s.dt*(r0+r1))/s.m1


def patch_transfer(old, new, u, positive=True):
    """Same-time full-nodal high/low map; disjoint connected changed cavities.

    High = new_mass*U - new_mass*sum(dm*U)/sum(new_mass).
    Low replaces only changed-patch support with its old patch mean.
    One common theta per entire cavity (and all components) conserves totals.
    This is the existing full-patch construction, not a new remap invention.
    """
    keys0 = {tuple(sorted(row)): i for i, row in enumerate(old.ids)}
    keys1 = {tuple(sorted(row)): i for i, row in enumerate(new.ids)}
    removed = [keys0[k] for k in keys0.keys()-keys1.keys()]
    added = [keys1[k] for k in keys1.keys()-keys0.keys()]
    q = old.mass[:, None]*np.atleast_2d(u).reshape(old.n, -1)
    U = q / old.mass[:, None]
    parent = np.arange(old.n)
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return int(i)
    for ids in (old.ids[removed], new.ids[added]):
        for row in ids:
            for j in row[1:]:
                parent[find(j)] = find(row[0])
    groups = {}
    touched = set(old.ids[removed].ravel()) | set(new.ids[added].ravel())
    for i in touched:
        groups.setdefault(find(i), []).append(i)
    a = masses(old.ids[removed], area(old.p)[removed], old.n)
    b = masses(new.ids[added], area(new.p)[added], new.n)
    assert np.max(abs(new.mass-old.mass-(b-a))) < 3e-14
    limited = 0
    for nodes in groups.values():
        idx = np.array(nodes)
        assert abs((b-a)[idx].sum()) < 3e-14
        dm, mnew = (b-a)[idx], new.mass[idx]
        defect = np.sum(dm[:, None]*U[idx], axis=0)
        high = mnew[:, None]*(U[idx] - defect/mnew.sum())
        average = np.sum(a[idx, None]*U[idx], axis=0)/b[idx].sum()
        low = (old.mass[idx]-a[idx])[:, None]*U[idx] + b[idx, None]*average
        assert np.max(abs(high.sum(axis=0)-q[idx].sum(axis=0))) < 1e-12*max(1., abs(q[idx]).sum())
        theta = 1.0
        if positive:
            # A scalar positivity condition; Euler transfer is checked separately.
            floor = 1e-12 * np.min(U[idx])
            loU, hiU = low/mnew[:, None], high/mnew[:, None]
            bad = hiU < floor
            if np.any(bad):
                assert np.min(loU) >= floor
                theta = min(1., float(np.min(((loU-floor)/(loU-hiU))[bad]))) * (1-1e-12)
                limited += 1
        q[idx] = high if theta == 1 else low + theta*(high-low)
    result = q/new.mass[:, None]
    return result.reshape(u.shape), dict(removed=len(removed), patches=len(groups), touched=len(touched),
                                        max_patch=max(map(len, groups.values()), default=0), limited=limited)


def simulate(n, steps, endtime, method, variant, motion='deform', uniform=False):
    labels = points(n)
    v = velocities(labels, motion)
    mesh = triangulate(labels)
    u = exact(labels, 0, uniform)
    total0 = float(mesh.mass@u)
    dt = endtime/steps
    events = []
    max_cons = max_uniform = max_slab_cons = 0.
    min_u = float(u.min())
    build_count = 1
    began, ended = 0, 0
    for step in range(steps):
        saved = begin(mesh, v, u, dt, method)
        began += 1
        xnew = (labels+(step+1)*dt*v) % 1
        # This is the only mesh construction between actual predictor/corrector.
        fresh = triangulate(xnew)
        build_count += 1
        retained = Mesh(mesh.ids, saved[0].p1, mesh.n)
        if variant == 'switch':
            back = Mesh(fresh.ids, fresh.p-dt*v[fresh.ids], fresh.n)
            u1 = end(saved, method, slab(back, v, dt))
        else:
            u1 = end(saved, method)
            max_slab_cons = max(max_slab_cons, abs(retained.mass@u1-mesh.mass@u))
        ended += 1
        if variant == 'remap':
            u, event = patch_transfer(retained, fresh, u1)
        else:
            keys0 = set(map(tuple, np.sort(retained.ids, axis=1)))
            keys1 = set(map(tuple, np.sort(fresh.ids, axis=1)))
            event = dict(removed=len(keys0-keys1))
            u = u1*retained.mass/fresh.mass if variant == 'keep_q' else u1
        events.append(event)
        mesh = fresh
        max_cons = max(max_cons, abs(mesh.mass@u-total0)/abs(total0))
        max_uniform = max(max_uniform, float(np.max(abs(u-1))))
        min_u = min(min_u, float(u.min()), float(saved[2].min()))
        assert np.all(np.isfinite(u))
    err = abs(u-exact(xnew, endtime, uniform))
    result = dict(n=n, nodes=n*n, steps=steps, end=endtime, dt=dt, method=method, variant=variant,
                  motion=motion, uniform=uniform, mesh_builds=build_count,
                  predictor_sweeps=began, corrector_sweeps=ended,
                  relative_conservation=max_cons, max_slab_conservation=max_slab_cons,
                  uniform_error=max_uniform if uniform else None, min_stage_or_final_u=min_u,
                  L1=float(mesh.mass@err), Linf=float(err.max()),
                  flip_steps=sum(e['removed']>0 for e in events), removed_triangles=sum(e['removed'] for e in events),
                  max_touched=max((e.get('touched',0) for e in events), default=0),
                  max_patch=max((e.get('max_patch',0) for e in events), default=0),
                  limited_patches=sum(e.get('limited',0) for e in events))
    assert began == ended == steps and build_count == steps+1
    if variant == 'remap':
        assert max_cons < 2e-12 and max_slab_cons < 2e-12, result
        if uniform:
            assert max_uniform < 2e-12, result
    return result, dict(u=u, x=xnew, mass=mesh.mass)


def scalar_patch_checks():
    xy = np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
    i0, i1 = np.array([[0,1,2],[0,2,3]]), np.array([[0,1,3],[1,2,3]])
    old, new = Mesh(i0,xy[i0],4), Mesh(i1,xy[i1],4)
    affine = 1+.2*xy[:,0]-.1*xy[:,1]
    after, event = patch_transfer(old,new,affine)
    assert np.max(abs(after-affine)) < 1e-14
    keep_q = old.mass/new.mass
    assert abs(new.mass@keep_q-old.mass.sum()) < 1e-14
    assert np.max(abs(keep_q-1)) > .4
    nonaffine = np.array([1.,4.,2.,.3])
    kept_mass_defect = float((new.mass-old.mass)@nonaffine)
    assert abs(kept_mass_defect) > .1
    return dict(affine_error=float(np.max(abs(after-affine))), keep_q_uniform_error=float(np.max(abs(keep_q-1))),
                keep_u_nonuniform_mass_defect=kept_mass_defect, cavity=event)


def main(output):
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve()
    shutil.copy2(source, output/source.name)
    provenance = dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                      base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source.parents[2],text=True).strip(),
                      numpy=np.__version__, physical_model='periodic scalar constant-coefficient advection',
                      box=[0,1], advection=ADVECTION.tolist(), initial='1+.2*sin(2*pi*x)+.1*cos(2*pi*y)',
                      mesh='jittered Cartesian; 3x3 periodic tiling; centroid-selected Qhull triangles',
                      flags='Campoli endpoint masses; N/lumped or scalar LDA/F1; prescribed linear node paths')
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    rows=[]
    start=time.monotonic()
    plan=[]
    for method in ('n','lda_f1'):
        for uniform in (True,False):
            for variant in ('remap','keep_u','keep_q','switch'):
                plan.append(dict(n=12,steps=64,endtime=.5,method=method,variant=variant,uniform=uniform))
        for n in (8,16,32):
            plan.append(dict(n=n,steps=8*n,endtime=.5,method=method,variant='remap'))
        for variant in ('remap','switch'):
            plan.append(dict(n=12,steps=64,endtime=.5,method=method,variant=variant,motion='translation'))
    for case in plan:
        row, state=simulate(**case)
        rows.append(row)
        np.savez_compressed(output/f'case_{len(rows):02d}.npz',**state)
        (output/'summary.partial.json').write_text(json.dumps(rows,indent=2)+'\n')
        print(json.dumps(row),flush=True)
    result=dict(cases=rows,scalar_patch=scalar_patch_checks(),elapsed_seconds=time.monotonic()-start)
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    main(parser.parse_args().output.resolve())
