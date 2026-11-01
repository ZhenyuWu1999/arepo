#!/usr/bin/env python3
"""Plot hierarchical Blob density slices and a Morton-selected mass comparison.

Use the validated periodic tetrahedron/slice caches from blob_n1_diagnosis.
No hydrodynamic evolution or fitted time rescaling is performed. The mass
panel includes the user's explicitly requested half-timescale reference.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import h5py
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np

TCC = np.sqrt(10) / 6.15
SVG_SHA256 = '94755056a56524a5e41e4cad0db226d1073a2e0043bb38796adbaa9389ade17a'
CASES = ('N_equal_np8', 'N_hier_np8')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_snapshot(path):
    with h5py.File(path, 'r') as f:
        g = f['PartType0']
        order = np.argsort(g['ParticleIDs'][:])
        result = {k: g[k][:][order] for k in
                  ('ParticleIDs', 'Coordinates', 'Masses', 'Density', 'Pressure')}
        result['time'] = float(f['Header'].attrs['Time'])
    assert all(np.isfinite(result[k]).all() for k in result)
    assert min(result[k].min() for k in ('Masses', 'Density', 'Pressure')) > 0
    return result


def write_csv(path, rows):
    with path.open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def extract_morton(svg):
    assert sha256(svg) == SVG_SHA256, 'Axis calibration is for the inspected primary SVG only.'
    root = ET.parse(svg).getroot()
    candidates = [p for p in root.findall('.//{http://www.w3.org/2000/svg}path')
                  if p.get('stroke') == '#d62728' and len(p.get('d', '')) > 150
                  and not p.get('stroke-dasharray')]
    assert len(candidates) == 1
    path = candidates[0].get('d')
    assert set(re.findall('[A-DF-Za-df-z]', path)) <= {'M', 'H'}
    before, after = path.split('H', 1)
    numbers = lambda text: np.array([float(x) for x in re.findall(
        r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?', text)])
    xy = numbers(before).reshape(-1, 2)
    xy = np.vstack((xy, np.column_stack((numbers(after), np.repeat(xy[-1, 1], len(numbers(after)))))))
    tkh = (xy[:, 0] - 55.77597) / (2 * (103.87942 - 55.77597))
    mass = (xy[:, 1] - 53.586877) / (280.38688 - 53.586877)
    assert np.all(np.diff(tkh) > 0)
    np.testing.assert_allclose([tkh[0], mass[0]], [0, 1], atol=1e-12)
    assert mass.min() >= -1e-10 and mass.max() <= 1 + 1e-10
    rows = [dict(t_over_tKH_as_published=float(t), t_over_tcc=float(3.2 * t),
                 cloud_fraction=float(m), svg_x=float(x), svg_y=float(y))
            for t, m, (x, y) in zip(tkh, mass, xy)]
    return tkh, mass, rows


def save(fig, out, name):
    for ext in ('png', 'pdf'):
        fig.savefig(out / f'{name}.{ext}', dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--audit-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New directory, never overwrite.')
    args = parser.parse_args()
    bundle, audit, out = args.bundle.resolve(), args.audit_root.resolve(), args.output.resolve()
    assert not out.exists(), out
    first = bundle / 'cases/N_equal_np8/snapshots/snap_000.hdf5'
    initial = read_snapshot(first)
    assert len(initial['ParticleIDs']) == 32**3 and initial['time'] == 0
    cache = audit / 'slice_weights.npz'
    mesh_path = audit / 'periodic_mesh.npz'
    with np.load(cache) as f:
        grid, ids, weights = f['grid'], f['ids'], f['weights']
    assert ids.shape == weights.shape == (len(grid)**2, 4)
    np.testing.assert_allclose(weights.sum(axis=1), 1, atol=1e-12)
    assert weights.min() > -1e-10 and ids.min() >= 0 and ids.max() < len(initial['ParticleIDs'])
    xx, yy = np.meshgrid(grid, grid)
    query = np.column_stack((xx.ravel(), yy.ravel(), np.full(xx.size, 5.)))
    delta = initial['Coordinates'][ids] - query[:, None, :]
    delta -= 10 * np.rint(delta / 10)
    reconstruction_error = float(np.max(np.abs(np.sum(weights[:, :, None] * delta, axis=1))))
    assert reconstruction_error < 1e-10
    dual = initial['Masses'] / initial['Density']
    with np.load(mesh_path) as f:
        np.testing.assert_allclose(f['dual'], dual, rtol=1e-10, atol=1e-13)
        assert abs(f['volume'].sum() - 1000) < 1e-9
        tetrahedra = len(f['volume'])
    tkh, reference_mass, reference_rows = extract_morton(audit / 'reference_cloudMass.svg')
    out.mkdir(parents=True)
    write_csv(out / 'morton_fig20_N32_digitized.csv', reference_rows)
    write_csv(out / 'morton_display_coordinates.csv', [
        dict(published_t_over_tKH=float(t),
             morton_display_t_over_tcc=float(t * 1.6 * 2),
             artificial_halt_display_t_over_tcc=float(t * 1.6),
             cloud_fraction=float(m)) for t, m in zip(tkh, reference_mass)])

    histories, slices, provenance = {}, {}, []
    for case in CASES:
        rows = []
        paths = sorted((bundle / 'cases' / case / 'snapshots').glob('snap_*.hdf5'))
        assert len(paths) == 31
        for i, path in enumerate(paths):
            s = read_snapshot(path)
            np.testing.assert_array_equal(s['ParticleIDs'], initial['ParticleIDs'])
            np.testing.assert_array_equal(s['Coordinates'], initial['Coordinates'])
            rho, pressure, mass = s['Density'], s['Pressure'], s['Masses']
            morton = (rho > 64) & (pressure / rho < 9)
            rows.append(dict(snapshot=path.name, time=s['time'], t_over_tcc=s['time'] / TCC,
                             t_over_tKH=s['time'] / (3.2 * TCC),
                             mass_morton_cut=float(mass[morton].sum())))
            if case == 'N_hier_np8' and i in (0, 10, 20, 30):
                # P1-Z density evaluated at the actual plane; no projection or z averaging.
                rho_slice = np.sum(weights * np.sqrt(rho[ids]), axis=1)**2
                slices[case, i] = dict(time=s['time'], rho=rho_slice.reshape(xx.shape))
            provenance.append(dict(path=str(path), sha256=sha256(path)))
        for row in rows:
            row['fraction_morton_cut'] = row['mass_morton_cut'] / rows[0]['mass_morton_cut']
        histories[case] = rows
        write_csv(out / f'{case}_cloud_mass.csv', rows)

    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 4, figsize=(13.6, 4.4), layout='constrained')
    fig.get_layout_engine().set(rect=(0, .085, 1, .915))
    for ax, i in zip(axes, (0, 10, 20, 30)):
        s = slices['N_hier_np8', i]
        im = ax.imshow(s['rho'] / 10, extent=(0, 10, 0, 10), origin='lower',
                       norm=LogNorm(1, 10, clip=True), cmap='Spectral_r', interpolation='nearest')
        ax.set(title=r'$t/t_{\rm cc}=$' + f"{s['time']/TCC:.6f}",
               xlabel='$x$', xticks=[0, 5, 10], yticks=[0, 5, 10])
    axes[0].set_ylabel('$y$')
    cbar = fig.colorbar(im, ax=axes, label=r'$\rho/\rho_{\rm wind,0}$', shrink=.55,
                        orientation='horizontal', ticks=[1, 3, 10], aspect=65, pad=.045)
    cbar.minorticks_off()
    cbar.ax.set_xticklabels(['1', '3', '10'])
    fig.suptitle(r'3D Blob density slices at $z=5$: N/RK2, hierarchical timesteps' '\n'
                 r'$\chi=10$; $32^3$ generators; 8 MPI ranks; 140 initial cloud nodes', fontsize=13)
    fig.text(.5, .024, 'Central xy plane: 3D tetrahedral P1-Z reconstruction, no line-of-sight averaging. '
             'Shared logarithmic scale; colours clipped to initial wind/cloud densities.',
             ha='center', fontsize=9)
    save(fig, out, 'blob_density_slices_z5')

    fig, ax = plt.subplots(figsize=(8.4, 6.0), layout='constrained')
    for case, color, style, marker, label in (
            ('N_equal_np8', '#2468a0', '-', 'o', 'Current N/RK2, equal'),
            ('N_hier_np8', '#d68b22', '--', None, 'Current N/RK2, hierarchy')):
        rows = histories[case]
        time = [r['t_over_tcc'] for r in rows]
        ax.plot(time, [r['fraction_morton_cut'] for r in rows], color=color, ls=style,
                marker=marker, ms=3, lw=1.8, label=label)
    ax.plot(3.2 * tkh, reference_mass, 's-', color='#b33939', ms=4, mfc='white', lw=1.7,
            label=r'Morton (2023) N1, $32^3$: Fig. 20 digitized')
    artificial_label = 'Morton with artificial halt timescale'
    ax.plot(1.6 * tkh, reference_mass, 's--', color='#76549b', ms=4, mfc='white', lw=1.7,
            label=artificial_label)
    assert len(fig.axes) == 1 and len(ax.lines) == 4
    ax.set(xlim=(0, 6.5), ylabel=r'$M_{\rm selected}(t)/M_{\rm selected}(0)$')
    ax.text(.97, .52, r'Current units: $\rho>64$, $p/\rho<9$', ha='right',
            transform=ax.transAxes, fontsize=9)
    ax.set(xlabel=r'$t/t_{\rm cc}$, $t_{\rm cc}=R\sqrt{\chi}/v_{\rm wind}$', ylim=(-.025, 1.055))
    ax.grid(alpha=.2)
    ax.legend(loc='upper right', fontsize=8, frameon=True)
    fig.suptitle(r'3D Blob cloud mass: $\chi=10$, $32^3$ generators, 8 MPI ranks' '\n'
                 r'$\rho>0.64\rho_{\rm cl,0}$ and $T<0.9T_{\rm wind,0}$ (Morton selection)', fontsize=13)
    save(fig, out, 'blob_cloud_mass_morton_overlay')

    metadata = dict(
        script_sha256=sha256(Path(__file__).resolve()), input_snapshots=provenance,
        reference=dict(url='https://arxiv.org/html/2204.01757v2/cloudMass.svg', sha256=SVG_SHA256,
                       extraction='Red solid 32^3 N1 path; exclude legend; inspect tick/glyph calibration.',
                       axis_calibration=dict(x_t0=55.77597, x_tKH_half=103.87942,
                                             y_mass0=53.586877, y_mass1=280.38688),
                       vector_points=len(reference_rows), tKH_over_tcc=3.2,
                       original_snapshots=False, fitted_time_rescaling=False,
                       user_requested_display_multipliers=[1.6 * 2, 1.6]),
        mass_panel=dict(panel_count=1, curve_count=4,
                        current_cases=list(CASES), current_time_mapping='native time / radius-based t_cc; unchanged.',
                        reference_original_clock='published t/t_KH coordinate * 1.6 * 2',
                        reference_artificial_clock='published t/t_KH coordinate * 1.6',
                        artificial_label=artificial_label, fitted_parameters=False,
                        footer_text=False),
        slice=dict(plane='z=5, full xy domain [0,10]^2', method='rho=(sum(lambda_i sqrt(rho_i)))^2',
                   grid_shape=list(xx.shape), line_of_sight_average=False, tetrahedra=tetrahedra,
                   cache_path=str(cache), cache_sha256=sha256(cache),
                   mesh_path=str(mesh_path), mesh_sha256=sha256(mesh_path),
                   cache_coordinate_reconstruction_max_error=reconstruction_error,
                   cases=['N_hier_np8'], color_map='Spectral_r',
                   color_reference='Braspenning (2023) Figure 1, chi=10: purple/blue to red ramp and horizontal colourbar.',
                   color_normalization='Logarithmic rho/rho_wind,0 in [1,10], clipped.',
                   panel_times={'N_hier_np8': [slices['N_hier_np8', i]['time']/TCC for i in (0, 10, 20, 30)]}),
        criteria=dict(morton='rho>64 AND p/rho<9',
                      mass='Sum of native snapshot Masses, not input density or Voronoi volume.',
                      normalization='Initial mass passing the same criterion in that run.',
                      interpretation='Eulerian selected mass; no material tracer.'),
        comparison=dict(equal_vs_hierarchy='Identical initial native states and geometry.',
                        morton='Available BLOB setup matches; current N/RK2 versus published N1. Original publication-run configuration unavailable.',
                        braspenning_mass_comparison=False),
        tcc=TCC, setup='Current Morton-inspired 10^3 cube, not a matched Braspenning reproduction.',
        figures={p.name: sha256(p) for p in sorted(out.glob('*')) if p.suffix in ('.png', '.pdf')})
    (out / 'plot_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(dict(output=str(out), reference_points=len(reference_rows),
                          cached_slice_coordinate_error=reconstruction_error), indent=2))


if __name__ == '__main__':
    main()
