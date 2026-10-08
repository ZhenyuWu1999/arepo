#!/usr/bin/env python3
"""Morton et al. (2023, Fig. 13)-style 2D density maps of the Sedov blast at t=0.05.

RD nodal states are drawn with their exact P1 interpolant on the periodic Delaunay
triangulation (linear interpolation of the vertex values). MMFV cell averages are
drawn as piecewise-constant Voronoi cells (nearest generator). Linear 'plasma'
colour scale 0-4 with one shared colour bar, full unit box. Preview only.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/'tests/rd'))
sys.path.insert(0, str(HERE))
from run_n_gauss3_split import state, sha, write
from analyze_mmfv import fv_state, verify_native

L = REPO.parent/'local_runs'
NGRID = 900
EDGES = (np.arange(NGRID)+.5)/NGRID


def tiled(xy, values, margin=.06):
    """Periodic images within `margin` of the box so interpolation is seamless."""
    pts, vals = [xy], [values]
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == dy == 0: continue
            shifted = xy + (dx, dy)
            keep = np.all((shifted > -margin) & (shifted < 1+margin), axis=1)
            pts.append(shifted[keep]); vals.append(values[keep])
    return np.concatenate(pts), np.concatenate(vals)


def rd_map(s):
    pts, vals = tiled(s['xy'] % 1, s['rho'])
    X, Y = np.meshgrid(EDGES, EDGES)
    return LinearNDInterpolator(pts, vals)(X, Y)


def fv_map(s):
    pts, vals = tiled(s['generator'] % 1, s['rho'])
    X, Y = np.meshgrid(EDGES, EDGES)
    return vals[cKDTree(pts).query(np.column_stack((X.ravel(), Y.ravel())))[1]].reshape(X.shape)


def load_rd(archive, method, group):
    seq = verify_native(archive, method, archive/'runs'/f'{group}_{method}', state)[0]
    assert abs(seq[-1]['time']-.05) < 1e-12
    return seq[-1]


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    H = L/'sedov_hllc_20260930_v1'; H1 = L/'sedov_hllc_nearest1_static_20260930_v1'; M = L/'sedov_mmfv_20260929_v1'
    mm = verify_native(M, 'MMFV_moving', M/'runs/nearest21', fv_state)[0][-1]
    figures = {
        'sedov_maps_21': [('HLLC-RD, static mesh', rd_map(load_rd(H, 'HLLC_static', 'nearest21'))),
                          ('HLLC-RD, moving mesh', rd_map(load_rd(H, 'HLLC_moving', 'nearest21'))),
                          ('AREPO MMFV', fv_map(mm))],
        'sedov_maps_1node': [('HLLC-RD, moving mesh', rd_map(load_rd(H, 'HLLC_moving', 'nearest1')))]}
    static1 = H1/'runs/nearest1_HLLC_static/run_status.json'
    if static1.exists() and json.loads(static1.read_text())['returncode'] == 0:
        figures['sedov_maps_1node'].insert(0, ('HLLC-RD, static mesh', rd_map(load_rd(H1, 'HLLC_static', 'nearest1'))))
    single = L/'sedov_mmfv_single_20261001_v1'
    status = single/'runs/nearest1_MMFV/run_status.json'
    if status.exists() and json.loads(status.read_text())['returncode'] == 0:
        camp = json.loads((single/'campaign.json').read_text())
        assert sha(single/'artifacts/MMFV_moving/Arepo') == camp['binary_sha256']
        last = sorted((single/'runs/nearest1_MMFV/output').glob('snap_*.hdf5'))[-1]
        mm1 = fv_state(last); assert abs(mm1['time']-.05) < 1e-12
        figures['sedov_maps_1node'].append(('AREPO MMFV', fv_map(mm1)))
    meta = {}
    for name, panels in figures.items():
        fig, axes = plt.subplots(1, len(panels), figsize=(3.4*len(panels)+.9, 3.55), layout='constrained',
                                 sharey=True)
        for ax, (title, field) in zip(np.atleast_1d(axes), panels):
            im = ax.imshow(field, origin='lower', extent=(0, 1, 0, 1), cmap='plasma', vmin=0, vmax=4,
                           interpolation='nearest')
            ax.set_title(title, fontsize=10); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_yticks([0, .25, .5, .75, 1])
            ax.tick_params(direction='in', labelsize=9)
            meta[f'{name}/{title}'] = dict(field_min=float(np.nanmin(field)), field_max=float(np.nanmax(field)),
                                           nan_pixels=int(np.isnan(field).sum()))
        np.atleast_1d(axes)[0].set_ylabel('$y$')
        for ax in np.atleast_1d(axes): ax.set_xlabel('$x$')
        fig.colorbar(im, ax=axes, label='$\\rho$', shrink=.95, pad=.01)
        fig.savefig(out/f'{name}.png', dpi=300); fig.savefig(out/f'{name}.pdf'); plt.close(fig)
    write(out/'maps_meta.json', dict(script_sha256=sha(__file__), grid=NGRID, panels=meta,
        note='Preview only. RD: linear (P1) interpolation of nodal values; MMFV: nearest-generator (Voronoi) cells. '
             'Colour scale clipped to [0,4]; raw maxima are listed per panel.'))
    print(json.dumps(meta, indent=1))


def swift_map(path):
    """SPH particle densities, drawn with the same linear interpolation as RD (visual only)."""
    from analyze_swift_default import swift_state
    s = swift_state(path); assert abs(s['time']-.05) < 1e-9
    pts, vals = tiled(s['xy'] % 1, s['rho'])
    X, Y = np.meshgrid(EDGES, EDGES)
    return LinearNDInterpolator(pts, vals)(X, Y)


def main_grid(out):
    """Rows: 21 hot points (SWIFT default) and a single hot point (same particle ID 8256)."""
    out.mkdir(parents=True, exist_ok=False)
    H = L/'sedov_hllc_20260930_v1'; H1 = L/'sedov_hllc_nearest1_static_20260930_v1'
    M = L/'sedov_mmfv_20260929_v1'; M1 = L/'sedov_mmfv_single_20261001_v1'
    W = L/'swift_sedov_default_20260929_v1'; W1 = L/'swift_sedov_single_20261001_v1'
    for root in (W, W1):
        meta = json.loads((root/'artifact/provenance.json').read_text())
        assert sha(root/'artifact/swift') == meta['binary_sha256']
    camp = json.loads((M1/'campaign.json').read_text())
    assert sha(M1/'artifacts/MMFV_moving/Arepo') == camp['binary_sha256']
    mm1 = fv_state(sorted((M1/'runs/nearest1_MMFV/output').glob('snap_*.hdf5'))[-1]); assert abs(mm1['time']-.05) < 1e-12
    rows = [('21 hot points', [rd_map(load_rd(H, 'HLLC_static', 'nearest21')), rd_map(load_rd(H, 'HLLC_moving', 'nearest21')),
                                fv_map(verify_native(M, 'MMFV_moving', M/'runs/nearest21', fv_state)[0][-1]),
                                swift_map(W/'run/sedov_0005.hdf5')]),
            ('1 hot point', [rd_map(load_rd(H1, 'HLLC_static', 'nearest1')), rd_map(load_rd(H, 'HLLC_moving', 'nearest1')),
                              fv_map(mm1), swift_map(W1/'run/sedov_0005.hdf5')])]
    cols = ['HLLC-RD, static mesh', 'HLLC-RD, moving mesh', 'AREPO MMFV', 'SWIFT SPHENIX']
    fig, axes = plt.subplots(2, 4, figsize=(14.2, 7.0), layout='constrained', sharex=True, sharey=True)
    meta = {}
    for r, (label, fields) in enumerate(rows):
        for c, field in enumerate(fields):
            ax = axes[r, c]
            im = ax.imshow(field, origin='lower', extent=(0, 1, 0, 1), cmap='plasma', vmin=0, vmax=4, interpolation='nearest')
            ax.tick_params(direction='in', labelsize=9); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_yticks([0, .25, .5, .75, 1])
            if r == 0: ax.set_title(cols[c], fontsize=11)
            if r == 1: ax.set_xlabel('$x$')
            if c == 0: ax.set_ylabel(f'{label}\n$y$')
            meta[f'{label}/{cols[c]}'] = dict(field_min=float(np.nanmin(field)), field_max=float(np.nanmax(field)),
                                             nan_pixels=int(np.isnan(field).sum()))
    fig.colorbar(im, ax=axes, label='$\\rho$', shrink=.9, pad=.01)
    fig.savefig(out/'sedov_maps_grid.png', dpi=300); fig.savefig(out/'sedov_maps_grid.pdf'); plt.close(fig)
    write(out/'maps_meta.json', dict(script_sha256=sha(__file__), grid=NGRID, panels=meta,
        note='Preview only. RD and SWIFT: linear interpolation of node/particle densities; MMFV: Voronoi cells. '
             'Colour scale clipped to [0,4]; raw maxima listed. t=0.05 for all.'))
    print(json.dumps(meta, indent=1))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('out', type=Path)
    p.add_argument('--grid', action='store_true')
    a = p.parse_args()
    (main_grid if a.grid else main)(a.out.resolve())
