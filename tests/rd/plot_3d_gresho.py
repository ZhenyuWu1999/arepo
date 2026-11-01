#!/usr/bin/env python3
"""Split the archived static 16^3 Gresho figure into layer maps and a profile.

Read native snapshots only. Preserve the original projected-layer interpolation
and all-z median-dual radial averaging; do not rerun or overwrite the campaign.
"""
import argparse
import hashlib
import json
from pathlib import Path

import h5py
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np
from scipy.interpolate import griddata


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(path):
    with h5py.File(path, 'r') as f:
        gas = f['PartType0']
        order = np.argsort(gas['ParticleIDs'][:])
        result = dict(time=float(f['Header'].attrs['Time']),
                      ids=gas['ParticleIDs'][:][order],
                      x=gas['Coordinates'][:][order],
                      v=gas['Velocities'][:][order],
                      dual=gas['Masses'][:][order] / gas['Density'][:][order])
    assert all(np.isfinite(result[k]).all() for k in ('x', 'v', 'dual'))
    assert np.all(result['dual'] > 0)
    return result


def tangential_velocity(s):
    d = s['x'][:, :2] - .5
    r = np.linalg.norm(d, axis=1)
    numerator = -d[:, 1] * s['v'][:, 0] + d[:, 0] * s['v'][:, 1]
    return r, np.divide(numerator, r, out=np.zeros_like(r), where=r > 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True,
                        help='New directory; an existing output is never overwritten.')
    args = parser.parse_args()
    root, output = args.run_root.resolve(), args.output.resolve()
    assert not output.exists(), output
    paths = {name: root / 'runs' / method / 'output' / filename
             for name, method, filename in (
                 ('initial', 'N', 'snap_000.hdf5'),
                 ('N', 'N', 'snap_004.hdf5'),
                 ('LDA', 'LDA', 'snap_004.hdf5'))}
    states = {name: snapshot(path) for name, path in paths.items()}
    initial = states['initial']
    assert initial['time'] == 0 and len(initial['ids']) == 16**3
    for name in ('N', 'LDA'):
        s = states[name]
        assert s['time'] == .25
        np.testing.assert_array_equal(s['ids'], initial['ids'])
        np.testing.assert_array_equal(s['x'], initial['x'])
    x = initial['x']
    center, half_width = .5 + .5 / 16, .45 / 16
    layer = np.abs(x[:, 2] - center) < half_width
    assert layer.sum() == 256
    zmin, zmax = x[layer, 2].min(), x[layer, 2].max()
    output.mkdir(parents=True)
    plt.rcParams.update({'font.size': 11, 'axes.spines.top': False,
                         'axes.spines.right': False})

    fig, axes = plt.subplots(1, 3, figsize=(12, 4.6), layout='constrained')
    fig.get_layout_engine().set(rect=(0, .075, 1, .925))
    xx, yy = np.meshgrid(np.linspace(0, 1, 220), np.linspace(0, 1, 220))
    for ax, name, title in zip(axes, ('initial', 'N', 'LDA'),
                               ('Initial, $t=0$', 'N, $t=0.25$', 'LDA/F1, $t=0.25$')):
        _, tang = tangential_velocity(states[name])
        values = griddata(x[layer, :2], tang[layer], (xx, yy), method='linear')
        im = ax.pcolormesh(xx, yy, values, cmap='viridis', norm=Normalize(0, 1),
                           shading='auto', rasterized=True)
        ax.contour(xx, yy, np.hypot(xx - .5, yy - .5), levels=[.2, .4],
                   colors='white', linewidths=.5, alpha=.5)
        ax.set(xlabel='$x$', ylabel='$y$', title=title, aspect='equal',
               xlim=(0, 1), ylim=(0, 1))
    fig.colorbar(im, ax=list(axes), label=r'Tangential velocity $v_\phi$', shrink=.86)
    fig.suptitle(r'Static 3D Gresho: $16^3$ generators' '\n'
                 r'Slice plot at $z\approx0.53125$ (one jittered layer projected onto $xy$)',
                 fontsize=13)
    fig.text(.5, .027, f'Selected nodes: {zmin:.5f} <= z <= {zmax:.5f}; '
             '256 nodes; linear interpolation in xy.', ha='center', fontsize=10)
    slice_name = 'gresho_3d_vphi_slice_z0p53125'
    for extension in ('png', 'pdf'):
        fig.savefig(output / f'{slice_name}.{extension}', dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.8, 4.6), layout='constrained')
    rr = np.linspace(0, np.sqrt(.5), 500)
    exact = np.where(rr < .2, 5 * rr, np.where(rr < .4, 2 - 5 * rr, 0.))
    ax.plot(rr, exact, color='black', lw=1.5, label='Stationary analytic')
    edges = np.linspace(0, np.sqrt(.5), 25)
    colors = dict(N='#3268a8', LDA='#c7522a')
    profiles = {}
    for name, label in (('N', 'N'), ('LDA', 'LDA/F1')):
        s = states[name]
        radius, tang = tangential_velocity(s)
        bins = np.digitize(radius, edges) - 1
        centers, means = [], []
        for k in range(len(edges) - 1):
            selected = bins == k
            if selected.any():
                centers.append(float(np.average(radius[selected], weights=s['dual'][selected])))
                means.append(float(np.average(tang[selected], weights=s['dual'][selected])))
        ax.scatter(radius[::4], tang[::4], s=2, alpha=.08, color=colors[name], rasterized=True)
        ax.plot(centers, means, 'o-', ms=3, color=colors[name], label=label)
        profiles[name] = dict(mean_radius=centers, mean_vphi=means)
    ax.set(xlabel='Cylindrical radius $r$', ylabel=r'Tangential velocity $v_\phi$',
           title='All z: volume-weighted radial profile', xlim=(0, .65))
    ax.legend(fontsize=10)
    ax.grid(alpha=.2)
    fig.suptitle(r'Static 3D Gresho: $16^3$ generators, $t=0.25$', fontsize=13)
    profile_name = 'gresho_3d_vphi_profile_all_z'
    for extension in ('png', 'pdf'):
        fig.savefig(output / f'{profile_name}.{extension}', dpi=180)
    plt.close(fig)

    metadata = dict(
        run_root=str(root), plotting_script_sha256=sha256(Path(__file__).resolve()),
        inputs={name: dict(path=str(path), sha256=sha256(path), time=states[name]['time'])
                for name, path in paths.items()},
        slice=dict(nominal_z=center, selection_half_width=half_width,
                   selection_bounds=[center - half_width, center + half_width],
                   actual_z_range=[float(zmin), float(zmax)], selected_nodes=int(layer.sum()),
                   method='Project selected layer onto xy; scipy griddata linear, 220x220 grid.',
                   weighting='No mass/volume averaging; no all-z averaging.',
                   convex_hull_exterior='NaN, without extrapolation or periodic padding.',
                   color_range=[0, 1]),
        radial_profile=dict(nodes=len(x), weights='Median-dual volume = Masses/Density.',
                            radial_edges=edges.tolist(), profiles=profiles,
                            displayed_scatter='Every fourth ID-sorted node, as in the original figure.'),
        outputs={p.name: sha256(p) for p in sorted(output.iterdir()) if p.is_file()})
    (output / 'plot_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'figures': [slice_name, profile_name],
                      'selected_nodes': int(layer.sum()), 'z_range': [float(zmin), float(zmax)]}, indent=2))


if __name__ == '__main__':
    main()
