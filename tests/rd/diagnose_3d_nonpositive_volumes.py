#!/usr/bin/env python3
"""Audit M2 signed-volume failures; optionally replay small regularization controls.

Uses an existing frozen native artifact, never rebuilds or modifies the solver.
The output directory must be new. OMP/BLAS threads are fixed to one for controls.
"""
import argparse
import csv
from decimal import Decimal, localcontext
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import time

import h5py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from analyse_3d_geometry_pilot import key, read_pair
from test_moving_tetrahedra import volume_polynomial

REPO = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def lines(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def decimal_volume(event, s):
    """Direct 60-digit determinant from the saved binary64 coordinates/velocities.

    No use of the C polynomial, its determinant routine, or its root solver.
    A closing record is evaluated at x_close + (s-1)*h*w without binary64
    reconstruction of x_old.
    """
    with localcontext() as ctx:
        ctx.prec = 60
        d = Decimal.from_float
        h, f = d(event['h']), d(float(s)) - Decimal(event['closing'])
        x = [[d(a) + f*h*d(b) for a, b in zip(xx, ww)]
             for xx, ww in zip(event['x'], event['w'])]
        a, b, c = [[x[i][j] - x[0][j] for j in range(3)] for i in range(1, 4)]
        det = (a[0]*(b[1]*c[2]-b[2]*c[1])
               - a[1]*(b[0]*c[2]-b[2]*c[0])
               + a[2]*(b[0]*c[1]-b[1]*c[0]))
        return float(Decimal(event['orientation'])*det/6)


def shape(x):
    edges = [np.linalg.norm(x[j]-x[i]) for i in range(4) for j in range(i+1, 4)]
    areas = []
    for i in range(4):
        f = np.delete(x, i, axis=0)
        areas.append(np.linalg.norm(np.cross(f[1]-f[0], f[2]-f[0]))/2)
    v = abs(np.linalg.det(x[1:]-x[0])/6)
    return dict(q=float(v/sum(areas)**1.5), min_altitude=float(3*v/max(areas)),
                min_edge=float(min(edges)), max_edge=float(max(edges)))


def event_audit(case, e):
    x, w, h = np.array(e['x']), np.array(e['w']), e['h']
    x0 = x-e['closing']*h*w
    coeff = e['orientation']*volume_polynomial(x0, h*w)
    roots = sorted(float(z.real) for z in np.polynomial.polynomial.polyroots(coeff)
                   if abs(z.imag) < 1e-10 and 0 < z.real < 1)
    assert len(roots) == 1, (case, e['step'], roots)
    # This is an observed property of this pilot, not a general cubic assumption.
    probes = sorted(set([0., .5, 1., e['smin'], roots[0]-1e-8, roots[0]+1e-8]))
    exact = [decimal_volume(e, s) for s in probes]
    poly = np.polynomial.polynomial.polyval(probes, coeff)
    error = float(np.max(np.abs(poly-exact))/max(np.max(np.abs(coeff)), 1e-30))
    assert error < 3e-12, (case, error)
    v0, vmid, v1 = [decimal_volume(e, s) for s in (0., .5, 1.)]
    assert (v0 < 0 < v1) if e['closing'] else (v0 > 0 > v1)
    before, after = [decimal_volume(e, roots[0]+sign*1e-8) for sign in (-1, 1)]
    assert before*after < 0, (case, e['step'], before, after)
    vmin = decimal_volume(e, e['smin'])
    assert vmin < -e['error'] and not e['uncertain']
    refshape = shape(x)  # native endpoint: old for opening, new for closing
    relative_drift = float(np.max(np.linalg.norm(h*(w-w.mean(axis=0)), axis=1)))
    rootshape = shape(x0+roots[0]*h*w)
    return dict(case=case, step=e['step'], side='new_pullback' if e['closing'] else 'old_forward',
                ids=e['id'], h=h, opening_time=e['time']-h, zero_fraction=roots[0],
                zero_time=e['time']-h+roots[0]*h, v0=v0, vmid=vmid, v1=v1,
                temporal_volume=(v0+v1)/2, v0_over_v1=v0/v1,
                negative_to_error=abs(vmin)/e['error'], decimal_polynomial_defect=error,
                relative_drift=relative_drift,
                relative_drift_over_altitude=relative_drift/refshape['min_altitude'],
                min_edge_at_zero=rootshape['min_edge'], **refshape)


def first_pair_audit(folder, steps, events):
    old, new, h = read_pair(folder/'output/geometry_first_pair.bin')
    a, b = {key(r): r for r in old}, {key(r): r for r in new}
    common = a.keys() & b.keys()
    reversed_keys = {k for k in common if a[k].orientation != b[k].orientation}
    changed = (a.keys() ^ b.keys()) | reversed_keys
    native_volumes = []
    for records in (old, new):
        coords = np.array([r.x for r in records])
        orientation = np.array([r.orientation for r in records])
        native_volumes.append(orientation*np.linalg.det(coords[:, 1:]-coords[:, :1])/6)
    # Positivity here is by canonical orientation at each native endpoint.
    # Independent periodic Delaunay validation is recorded in the original M2 audit.
    assert all(np.min(v) > 0 for v in native_volumes)
    first_events = [e for e in events if e['step'] == steps[0]['step']]
    classified = []
    for e in first_events:
        records = b if e['closing'] else a
        matching = [(k, r) for k, r in records.items() if tuple(r.id) == tuple(e['id'])]
        assert len(matching) == 1  # pilot has no ID-only aliases
        k, r = matching[0]
        np.testing.assert_allclose(r.x, e['x'], rtol=0, atol=1e-15)
        assert r.orientation == e['orientation'] and k in changed
        classified.append(dict(ids=e['id'], closing=e['closing'], reversed_common=k in reversed_keys))
    return dict(h=h, old_count=len(old), new_count=len(new), reversed_common=len(reversed_keys),
                invalid_records=len(first_events), all_invalid_in_changed_chain=True,
                native_canonical_min_volume=[float(np.min(v)) for v in native_volumes],
                events=classified)


def field_comparison(a, b):
    with h5py.File(a) as fa, h5py.File(b) as fb:
        ga, gb = fa['PartType0'], fb['PartType0']
        assert set(ga) == set(gb)
        oa, ob = np.argsort(ga['ParticleIDs'][:]), np.argsort(gb['ParticleIDs'][:])
        assert fa['Header'].attrs['Time'] == fb['Header'].attrs['Time']
        for name in ga:
            x, y = ga[name][:][oa], gb[name][:][ob]
            assert x.dtype == y.dtype and x.shape == y.shape and x.tobytes() == y.tobytes(), name
        return len(ga)


def controls(pilot, dest):
    artifact = pilot/'artifacts/diag'
    provenance = json.loads((artifact/'provenance.json').read_text())
    assert sha(artifact/'Arepo') == provenance['binary_sha256']
    published = dest/'artifact'; published.mkdir()
    for name in ('Arepo', 'provenance.json', 'arepoconfig.h', 'linkage.txt'):
        shutil.copy2(artifact/name, published/name)
    shutil.copy2(pilot/'configs/diag.sh', published/'Config.sh')
    ic = dest/'rest_random.hdf5'; shutil.copy2(pilot/'inputs/rest_random.hdf5', ic)
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    specs = [('rest_reg05_cfl03', .5, .3), ('rest_reg0_cfl03', 0., .3), ('rest_reg0_cfl01', 0., .1)]
    results = []
    for name, shaping, cfl in specs:
        folder = dest/name; folder.mkdir()
        param = (pilot/'runs/rest_random_cfl0.3_diag/param.txt').read_text()
        changes = dict(InitCondFile=str(ic.with_suffix('')), OutputDir=str(folder/'output')+'/',
                       CellShapingSpeed=shaping, CourantFac=cfl)
        for k, v in changes.items():
            param, n = re.subn(r'^'+re.escape(k)+r'\s+.*$', k+' '+str(v), param, flags=re.M)
            assert n == 1, k
        (folder/'param.txt').write_text(param)
        command = [str(published/'Arepo'), 'param.txt']; start = time.monotonic()
        print('CONTROL', name, flush=True)
        with (folder/'run.log').open('w') as f:
            r = subprocess.run(command, cwd=folder, env=env, stdout=f, stderr=subprocess.STDOUT)
        status = dict(returncode=r.returncode, seconds=time.monotonic()-start, command=command,
                      binary_sha256=sha(published/'Arepo'), ic_sha256=sha(ic),
                      param_sha256=sha(folder/'param.txt'), threads={k: env[k] for k in
                      ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')})
        write(folder/'run_status.json', status); assert r.returncode == 0, folder
        ss = lines(folder/'output/geometry_steps.jsonl')
        ee = lines(folder/'output/geometry_invalid.jsonl')
        snapshots = sorted((folder/'output').glob('snap_*.hdf5'))
        assert len(snapshots) == 3
        with h5py.File(snapshots[0]) as fa, h5py.File(snapshots[-1]) as fb:
            ga, gb = fa['PartType0'], fb['PartType0']
            oa, ob = np.argsort(ga['ParticleIDs'][:]), np.argsort(gb['ParticleIDs'][:])
            dx = gb['Coordinates'][:][ob]-ga['Coordinates'][:][oa]; dx -= np.round(dx)
            movement = float(np.max(np.linalg.norm(dx, axis=1)))
            final_time = float(fb['Header'].attrs['Time'])
            final_min_volume = float(np.min(gb['Volume'][:]))
            fluid_max = float(np.max(np.linalg.norm(gb['Velocities'][:], axis=1)))
        assert final_time == .015625 and final_min_volume > 0
        row = dict(name=name, shaping=shaping, cfl=cfl, completed=True, steps=len(ss),
                   dt_values=sorted({s['h'] for s in ss}), old_invalid=sum(s['old_interval_negative'] for s in ss),
                   new_invalid=sum(s['new_interval_negative'] for s in ss), invalid_records=len(ee),
                   removed=sum(s['removed'] for s in ss), inserted=sum(s['inserted'] for s in ss),
                   max_reg_rms=max(s['reg_rms'] for s in ss), max_mesh_rms=max(s['mesh_rms'] for s in ss),
                   nonpositive_nodal_temporal=sum(s['nonpositive_nodal_temporal'] for s in ss),
                   final_time=final_time, max_particle_movement=movement,
                   final_fluid_velocity_max=fluid_max, final_min_fv_volume=final_min_volume)
        if shaping:
            reference = pilot/'runs/rest_random_cfl0.3_diag/output'
            row['baseline_byte_equal_datasets'] = [field_comparison(p, reference/p.name) for p in snapshots]
        results.append(row)
        write(dest/'control_results.json', results)
    return results


def figure(pilot, dest, rows):
    old_first = [r for r in rows if r['case'] == 'rest_random_cfl0.3_diag'
                 and r['side'] == 'old_forward' and r['step'] == 1]
    examples = [min(old_first, key=lambda r: r['zero_time']),
                min((r for r in rows if r['side'] == 'new_pullback'), key=lambda r: r['v0_over_v1'])]
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), layout='constrained')
    for ax, r in zip(axes, examples):
        e = next(e for e in lines(pilot/'runs'/r['case']/'output/geometry_invalid.jsonl')
                 if e['step'] == r['step'] and e['id'] == r['ids']
                 and bool(e['closing']) == (r['side'] == 'new_pullback'))
        x, w = np.array(e['x']), np.array(e['w'])
        coeff = e['orientation']*volume_polynomial(x-e['closing']*e['h']*w, e['h']*w)
        s = np.linspace(0, 1, 401); reference = r['v1'] if e['closing'] else r['v0']
        v = np.polynomial.polynomial.polyval(s, coeff)/reference
        ax.plot(s, v, color='#2166ac', lw=2)
        ax.fill_between(s, v, 0, where=v < 0, color='#b2182b', alpha=.15)
        ax.axhline(0, color='black', lw=.8); ax.axvline(r['zero_fraction'], color='#b2182b', ls='--')
        ax.scatter([0, 1], [r['v0']/reference, r['v1']/reference], color='#2166ac', zorder=3)
        if e['closing']:
            ax.axhline(-1, color='gray', ls=':', label='Campoli opening-ratio threshold = -1')
            ax.legend(fontsize=9)
        ax.set(xlabel='Step fraction s', ylabel='Oriented volume / native-endpoint volume',
               title=f"{r['side'].replace('_', ' ').title()}, CFL {'.1' if '0.1_' in r['case'] else '.3'}, step {r['step']}")
        ax.text(.04 if e['closing'] else .35, .94, f"Zero at s = {r['zero_fraction']:.6f}\nEndpoint q = {r['q']:.3g}",
                transform=ax.transAxes, va='top')
        ax.grid(alpha=.2)
    fig.suptitle('Thin tetrahedra change orientation along the frozen vertex trajectories')
    for suffix in ('png', 'pdf'): fig.savefig(dest/f'volume_roots.{suffix}', dpi=180)
    plt.close(fig)


def main(pilot, dest, run_controls):
    dest.mkdir(parents=True, exist_ok=False)
    copied = dest/'diagnose_3d_nonpositive_volumes.py'; shutil.copy2(__file__, copied)
    versions = dict(python=platform.python_version(), numpy=np.__version__, h5py=h5py.__version__, matplotlib=matplotlib.__version__,
                    platform=platform.platform())
    write(dest/'provenance.json', dict(pilot=str(pilot), analysis_git_head=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(), script_sha256=sha(copied),
        analysis_working_tree_status=subprocess.check_output(['git', 'status', '--short'], cwd=REPO, text=True),
        dependency_hashes={name: sha(REPO/'tests/rd'/name) for name in
                           ('analyse_3d_geometry_pilot.py', 'test_simplex_registry.py', 'test_moving_tetrahedra.py')},
        native_source_audit=json.loads((pilot/'final_source_audit.json').read_text()), versions=versions))
    rows, cases, inputs, native_fv_minima = [], [], {}, []
    for folder in sorted((pilot/'runs').glob('*_diag')):
        if folder.name.startswith('probe'): continue
        for name in ('geometry_steps.jsonl', 'geometry_invalid.jsonl', 'geometry_first_pair.bin'):
            p = folder/'output'/name; inputs[str(p)] = sha(p)
        steps = lines(folder/'output/geometry_steps.jsonl'); events = lines(folder/'output/geometry_invalid.jsonl')
        assert all(s['id_alias_old'] == s['id_alias_new'] == 0 for s in steps)
        snapshots = sorted((folder/'output').glob('snap_*.hdf5'))
        assert len(snapshots) == 3
        for path in snapshots:
            inputs[str(path)] = sha(path)
            with h5py.File(path) as f:
                native_fv_minima.append(float(np.min(f['PartType0/Volume'][:])))
        assert min(native_fv_minima) > 0
        rows.extend(event_audit(folder.name, e) for e in events)
        cases.append(dict(case=folder.name, old_invalid=sum(s['old_interval_negative'] for s in steps),
                          new_invalid=sum(s['new_interval_negative'] for s in steps),
                          first_pair=first_pair_audit(folder, steps, events),
                          first_reg_rms=steps[0]['reg_rms'], first_mesh_rms=steps[0]['mesh_rms']))
    assert len(rows) == 43
    new = [r for r in rows if r['side'] == 'new_pullback']
    old = [r for r in rows if r['side'] == 'old_forward']
    nonpositive = [r for r in new if r['temporal_volume'] <= 0]
    assert len(old) == 23 and len(new) == 20 and len(nonpositive) == 5
    groups = {}
    for r in rows: groups.setdefault((r['case'], r['step'], tuple(r['ids'])), []).append(r)
    paired = [g for g in groups.values() if len(g) == 2]
    assert len(groups) == 40 and len(paired) == 3
    for g in paired:
        assert {r['side'] for r in g} == {'old_forward', 'new_pullback'}
        assert abs(g[0]['zero_time']-g[1]['zero_time']) < 1e-14
    first_a, _, _ = read_pair(pilot/'runs/rest_random_cfl0.1_diag/output/geometry_first_pair.bin')
    first_b, _, _ = read_pair(pilot/'runs/rest_random_cfl0.3_diag/output/geometry_first_pair.bin')
    xa, xb = np.array([r.x for r in first_a]), np.array([r.x for r in first_b])
    wa, wb = np.array([r.w for r in first_a]), np.array([r.w for r in first_b])
    assert xa.tobytes() == xb.tobytes()
    velocity_difference = float(np.max(np.abs(wa-wb)))
    assert velocity_difference < 3e-16
    summary = dict(events=len(rows), old_events=len(old), new_events=len(new),
                   unique_case_step_ids=len(groups), paired_orientation_reversals=len(paired),
                   native_fv_snapshots=len(native_fv_minima), min_native_fv_snapshot_volume=min(native_fv_minima),
                   random_first_coordinates_byte_equal=True, random_first_velocity_max_difference=velocity_difference,
                   new_nonpositive_temporal=len(nonpositive),
                   min_negative_to_error=min(r['negative_to_error'] for r in rows),
                   max_decimal_polynomial_defect=max(r['decimal_polynomial_defect'] for r in rows),
                   min_edge_at_zero=min(r['min_edge_at_zero'] for r in rows),
                   old_q_range=[min(r['q'] for r in old), max(r['q'] for r in old)],
                   new_q_range=[min(r['q'] for r in new), max(r['q'] for r in new)],
                   first_pair_invalid_records=sum(c['first_pair']['invalid_records'] for c in cases),
                   all_first_pair_invalid_in_changed_chain=True,
                   worst_pullback=min(new, key=lambda r: r['v0_over_v1']))
    write(dest/'input_hashes.json', inputs)
    write(dest/'events.json', rows); write(dest/'case_audit.json', cases); write(dest/'summary.json', summary)
    with (dest/'events.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    figure(pilot, dest, rows)
    if run_controls: controls(pilot, dest)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-controls', action='store_true')
    args = parser.parse_args()
    main(args.pilot.resolve(), args.output.resolve(), args.run_controls)
