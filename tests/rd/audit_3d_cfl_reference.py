#!/usr/bin/env python3
"""Compare native FV, Springel (2010) and current static-RD first-step bounds.

Counterfactual meshes use frozen opening generator velocities and SciPy.
They are kinematic geometry oracles, not alternative native fluid trajectories.
"""
import argparse
import hashlib
from itertools import product
import json
from pathlib import Path
import shutil
import subprocess

import h5py
import numpy as np
import scipy
from scipy.spatial import Delaunay

from analyse_3d_geometry_pilot import read_pair

REPO = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def intervals(x0, w, h, orientation):
    e = x0[:, 1:]-x0[:, :1]
    d = h*(w[:, 1:]-w[:, :1])
    coeff = np.zeros((len(x0), 4))
    for mask in range(8):
        a, b, c = [d[:, i] if mask & (1 << i) else e[:, i] for i in range(3)]
        coeff[:, mask.bit_count()] += orientation*np.einsum('ij,ij->i', a, np.cross(b, c))/6
    v0, v1 = coeff[:, 0], coeff.sum(axis=1)
    minimum = np.minimum(v0, v1)
    a, b, c = 3*coeff[:, 3], 2*coeff[:, 2], coeff[:, 1]
    discriminant = b*b-4*a*c
    with np.errstate(divide='ignore', invalid='ignore'):
        q = -.5*(b+np.copysign(np.sqrt(np.maximum(discriminant, 0)), b))
        roots = [q/a, c/q, -c/b]
    for k, r in enumerate(roots):
        valid = ((a != 0) & (discriminant >= 0)) if k < 2 else ((a == 0) & (b != 0))
        valid &= (r > 0) & (r < 1) & np.isfinite(r)
        rv = r[valid]; cc = coeff[valid]
        value = ((cc[:, 3]*rv+cc[:, 2])*rv+cc[:, 1])*rv+cc[:, 0]
        minimum[valid] = np.minimum(minimum[valid], value)
    span = np.max(np.abs(e)+np.abs(d), axis=(1, 2))
    error = 256*np.finfo(float).eps*span**3
    return dict(tetrahedra=len(x0), coverage0=float(v0.sum()), coverage1=float(v1.sum()),
                negative0=int(np.sum(v0 < -error)), negative1=int(np.sum(v1 < -error)),
                negative_interval=int(np.sum(minimum < -error)),
                uncertain=int(np.sum(np.abs(minimum) <= error)),
                nonpositive_temporal=int(np.sum((v0+v1)/2 <= 0)))


def closing_mesh(x, w, h):
    wrapped = (x+h*w) % 1
    tiles = np.array(list(product([-1, 0, 1], repeat=3)))
    coords = (wrapped[None, :, :]+tiles[:, None, :]).reshape(-1, 3)
    t = Delaunay(coords).simplices
    ids, images = t % len(x), tiles[t//len(x)]
    order = np.argsort(ids, axis=1)
    t = np.take_along_axis(t, order, axis=1)
    ids = np.take_along_axis(ids, order, axis=1)
    images = np.take_along_axis(images, order[:, :, None], axis=1)
    keep = np.all(images[:, 0] == 0, axis=1)
    xx, ww = coords[t[keep]], w[ids[keep]]
    determinant = np.linalg.det(xx[:, 1:]-xx[:, :1])
    assert np.all(determinant != 0)
    return xx-h*ww, ww, np.sign(determinant)


def main(pilot, dest):
    dest.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, dest/Path(__file__).name)
    pair = pilot/'runs/rest_random_cfl0.3_diag/output/geometry_first_pair.bin'
    snap = pair.parent/'snap_000.hdf5'
    old, new, native_h = read_pair(pair)
    with h5py.File(snap) as f:
        g = f['PartType0']; order = np.argsort(g['ParticleIDs'][:])
        ids = g['ParticleIDs'][:][order]
        x, u, snapshot_w = [g[name][:][order] for name in ('Coordinates', 'Velocities', 'VertexVelocity')]
        rho, p, volume = [g[name][:][order] for name in ('Density', 'Pressure', 'Volume')]
    assert np.array_equal(ids, np.arange(1, len(ids)+1))
    assert np.max(np.abs(u)) == 0
    w = np.empty_like(x); seen = set()
    for r in old:
        for i in range(4):
            j = int(r.id[i])-1
            w[j] = r.w[i]; seen.add(j)
    assert len(seen) == len(ids)
    c = np.sqrt((5/3)*p/rho); radius = (3*volume/(4*np.pi))**(1/3)
    local_snapshot = radius/(c+np.linalg.norm(u-snapshot_w, axis=1))
    local_drift = radius/(c+np.linalg.norm(u-w, axis=1))
    tau, padded_tau = np.empty(len(x)), np.empty(len(x))
    limiting = (float('inf'), 0, 0)
    for lo in range(0, len(x), 128):
        hi = min(lo+128, len(x)); r = x[None, :, :]-x[lo:hi, None, :]; r -= np.round(r)
        distance = np.linalg.norm(r, axis=2)
        dv = u[None, :, :]-u[lo:hi, None, :]
        with np.errstate(divide='ignore', invalid='ignore'):
            signal = c[lo:hi, None]+c[None, :]-np.sum(dv*r, axis=2)/distance
            travel = distance/signal
            padded = (distance+radius[lo:hi, None])/signal
        valid = (distance > 0) & (signal > 0)
        travel[~valid] = padded[~valid] = np.inf
        tau[lo:hi], padded_tau[lo:hi] = travel.min(axis=1), padded.min(axis=1)
        i, j = np.unravel_index(travel.argmin(), travel.shape)
        if travel[i, j] < limiting[0]: limiting = (float(travel[i, j]), lo+i, j)
    xt = np.array([r.x for r in old]); wt = np.array([r.w for r in old])
    orient = np.array([r.orientation for r in old]); tid = np.array([r.id for r in old], dtype=int)-1
    vt = orient*np.linalg.det(xt[:, 1:]-xt[:, :1])/6
    face_areas = np.array([np.linalg.norm(np.cross(xt[:, f[1]]-xt[:, f[0]], xt[:, f[2]]-xt[:, f[0]]), axis=1)/2
                          for f in ([j for j in range(4) if j != k] for k in range(4))]).T
    # Exact reconstruction of the existing *static* uniform-at-rest RD bound.
    alpha = face_areas.max(axis=1)*np.sqrt(5/3)/3
    mass, rates = np.zeros(len(x)), np.zeros(len(x))
    np.add.at(mass, tid.ravel(), np.repeat(vt/4, 4))
    np.add.at(rates, tid.ravel(), np.repeat(alpha, 4))
    raw = dict(native_snapshot=float(np.minimum(local_snapshot, padded_tau).min()),
               local_final_drift=float(local_drift.min()),
               paper129_final_drift=float(np.minimum(local_drift, tau).min()),
               current_static_rd=float(np.min(mass/rates)))
    bounds = []
    for name, value in raw.items():
        for cfl in (.1, .3):
            candidate = cfl*value
            bounds.append(dict(condition=name, cfl=cfl, limit=candidate,
                               quantized_h=float(2.**np.floor(np.log2(candidate)))))
    assert next(b['quantized_h'] for b in bounds if b['condition']=='native_snapshot' and b['cfl']==.3) == native_h
    native_new_x = np.array([r.x for r in new]); native_new_w = np.array([r.w for r in new])
    native_old = intervals(xt, wt, native_h, orient)
    native_new = intervals(native_new_x-native_h*native_new_w, native_new_w, native_h,
                           np.array([r.orientation for r in new]))
    assert native_old['negative_interval'] == 7 and native_new['negative_interval'] == 5
    mesh_results = []
    for h in sorted({b['quantized_h'] for b in bounds}):
        print('KINEMATIC', h, flush=True)
        x0, ww, orientation = closing_mesh(x, w, h)
        a, b = intervals(xt, wt, h, orient), intervals(x0, ww, h, orientation)
        assert abs(a['coverage0']-1) < 2e-12 and abs(a['coverage1']-1) < 2e-12
        assert abs(b['coverage0']-1) < 2e-12 and abs(b['coverage1']-1) < 2e-12
        if h == native_h:
            assert b['tetrahedra'] == native_new['tetrahedra']
            assert b['negative_interval'] == native_new['negative_interval']
        mesh_results.append(dict(h=h, old=a, new=b))
        dump(dest/'kinematic_meshes.json', mesh_results)
    result = dict(raw_bounds=raw, selected_bounds=bounds, native_h=native_h,
                  nearest_signal_pair_ids=[int(ids[limiting[1]]), int(ids[limiting[2]])],
                  nearest_signal_tau=limiting[0], snapshot_mesh_rms=float(np.sqrt(np.mean(np.sum(snapshot_w**2, axis=1)))),
                  drift_mesh_rms=float(np.sqrt(np.mean(np.sum(w**2, axis=1)))),
                  bounds_scope='First opening state only. Static-RD bound is not a moving-RD or positivity proof.',
                  geometry_scope='Frozen drift velocities, independent periodic Delaunay; no fluid update.')
    dump(dest/'summary.json', result)
    dump(dest/'provenance.json', dict(analysis_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
         script_sha256=sha(Path(__file__)), input_hashes={str(p):sha(p) for p in (pair,snap)},
         numpy=np.__version__, scipy=scipy.__version__, h5py=h5py.__version__,
         paper='https://arxiv.org/html/0901.4107', equations=[126,129,130],
         dependency_hashes={name:sha(REPO/'tests/rd'/name) for name in
                            ('analyse_3d_geometry_pilot.py','test_simplex_registry.py','test_moving_tetrahedra.py')}))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args(); main(args.pilot.resolve(), args.output.resolve())
