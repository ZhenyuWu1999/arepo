#!/usr/bin/env python3
"""Restyle retained glass48/t3 Gresho runs without changing the source archive."""
import argparse
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from run_n_gauss3_split import state, sha, write
from analyze_gresho_glass_boost_lab import profile


BINS = np.linspace(0., .7, 36)


def radial_mean(radius, velocity):
    """Match Chapter 3: 35 uniform bins, unweighted node means, no smoothing."""
    index = np.digitize(radius, BINS) - 1
    centers = .5 * (BINS[:-1] + BINS[1:])
    mean = np.full(35, np.nan)
    counts = np.zeros(35, dtype=int)
    for k in range(35):
        selected = index == k
        counts[k] = np.count_nonzero(selected)
        if counts[k]:
            mean[k] = np.mean(velocity[selected])
    return centers, mean, counts


def plot(source, output):
    output.mkdir(parents=True, exist_ok=True)
    figures = output/'figures'
    pdfdir = output/'output/pdf'
    figures.mkdir(exist_ok=True)
    pdfdir.mkdir(parents=True, exist_ok=True)
    saved = json.loads((source/'summary.json').read_text())
    saved_prov = json.loads((source/'analysis_provenance.json').read_text())
    assert sha(source/'summary.json') == saved_prov['summary_sha256']
    source_pdf = source/'output/pdf/gresho_glass48_t3_moving_boost0_10_static0.pdf'
    assert sha(source_pdf) == saved_prov['pdf_sha256']
    inputs_before = {str(source/'summary.json'): sha(source/'summary.json'),
                     str(source_pdf): sha(source_pdf)}
    curves, records = {}, []
    for prov in saved['provenance']:
        archive = Path(prov['archive'])
        campaign = json.loads((archive/'campaign.json').read_text())
        case, = [c for c in campaign['cases']
                 if c['horizon'] == 'science' and c['method'] == prov['method']]
        assert case['frame'] == 'lab' and case['end'] == 3.
        path = sorted((archive/'runs'/case['name']/'output').glob('snap_*.hdf5'))[-1]
        key = (case['scheme'], case['mesh'], case['boost'])
        previous, = [r for r in saved['cases']
                     if (r['scheme'], r['mesh'], r['boost']) == key]
        assert sha(path) == previous['final']['snapshot_sha256']
        inputs_before[str(path)] = sha(path)
        s = state(path)
        assert s['time'] == 3. and len(s['id']) == 48**2
        radius, velocity, exact = profile(s, case['boost'])
        assert np.isfinite(radius).all() and np.isfinite(velocity).all()
        error = float(s['mass'] / s['mass'].sum() @ abs(velocity-exact))
        assert np.isclose(error, previous['final']['vphi_l1_mass'], rtol=0., atol=1e-15)
        centers, mean, counts = radial_mean(radius, velocity)
        curves[key] = (radius, velocity, centers, mean, counts)
        records.append(dict(scheme=key[0], mesh=key[1], boost=key[2],
                            snapshot=str(path), snapshot_sha256=sha(path),
                            raw_nodes=len(radius), binned_nodes=int(counts.sum()),
                            nodes_outside_mean_bins=int(len(radius)-counts.sum()),
                            vphi_l1_mass=error,
                            binned_peak=float(np.nanmax(mean))))
        np.savetxt(output/f'{key[0]}_{key[1]}_boost{key[2]}_radial_mean.csv',
                   np.column_stack((centers, mean, counts)), delimiter=',',
                   header='radius_center,unweighted_mean_vphi,node_count', comments='')
    assert set(curves) == {('N', 'static', 0), ('N', 'moving', 0),
                          ('N', 'moving', 10), ('LDA', 'moving', 0), ('LDA', 'moving', 10)}
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.linewidth': .8, 'xtick.direction': 'in',
                         'ytick.direction': 'in', 'xtick.top': True,
                         'ytick.right': True, 'pdf.fonttype': 42})
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.1), sharex=True,
                             sharey=True, layout='constrained')
    boost0_colors = {'N': '#d17a19', 'LDA': '#9467bd'}
    styles = {
        ('static', 0): dict(color='#777777', marker='s', ls='-',
                            label='Static, boost 0', markevery=(0, 3)),
        ('moving', 0): dict(color='#d17a19', marker='o', ls='-',
                            label='Moving, boost 0', markevery=(0, 3)),
        ('moving', 10): dict(marker='D', ls=(0, (4, 2.6)),
                             label='Moving, boost 10', markevery=(1, 3)),
    }
    all_velocity = np.concatenate([c[1] for c in curves.values()])
    ylim = (min(-.06, float(all_velocity.min())-.02),
            max(1.07, float(all_velocity.max())+.02))
    legends = []
    for ax, scheme, color in zip(axes, ('N', 'LDA'), ('#278449', '#2672b5')):
        ax.plot([0., .2, .4, .71], [0., 1., 0., 0.], color='black',
                ls='--', lw=1.5, label='Analytic', zorder=5)
        for mesh, boost in [('static', 0), ('moving', 0), ('moving', 10)]:
            key = (scheme, mesh, boost)
            if key not in curves:
                continue
            radius, velocity, centers, mean, counts = curves[key]
            style = dict(styles[(mesh, boost)])
            curve_color = style.pop('color', color)
            if mesh == 'moving' and boost == 0:
                curve_color = boost0_colors[scheme]
            ax.scatter(radius, velocity, s=3., color=curve_color, alpha=.09,
                       linewidths=0., rasterized=True, zorder=1)
            # Keep NaNs in empty bins to avoid bridging unsampled intervals.
            ax.plot(centers, mean, color=curve_color, lw=1.5,
                    markersize=3.2, markerfacecolor='white',
                    markeredgewidth=.9, zorder=3, **style)
        ax.set(title=scheme, xlabel=r'Radius $r$', xlim=(0., .71), ylim=ylim)
        ax.set_xticks(np.arange(0., .71, .1))
        for radius in (.2, .4):
            ax.axvline(radius, color='.65', lw=.7, ls=':', zorder=0)
        ax.grid(color='.9', lw=.55, alpha=.75)
        legends.append(ax.legend(loc='upper right', frameon=False,
                                 fontsize=8.7, handlelength=2.8))
    axes[0].set_ylabel(r'Azimuthal velocity $v_\varphi$')
    fig.suptitle(r'Gresho, glass $48^2$, $t=3$', fontsize=12)
    fig.canvas.draw()
    for ax, legend in zip(axes, legends):
        bounds = legend.get_window_extent().transformed(ax.transAxes.inverted())
        assert 0 <= bounds.x0 < bounds.x1 <= 1 and 0 <= bounds.y0 < bounds.y1 <= 1
    stem = 'gresho_glass48_t3_boost_profiles_mean'
    pdf, png = pdfdir/f'{stem}.pdf', figures/f'{stem}.png'
    fig.savefig(pdf, dpi=300)
    fig.savefig(png, dpi=220)
    plt.close(fig)
    for path, expected in inputs_before.items():
        assert sha(path) == expected
    style_source = Path('/Users/zhenyuwu/Hydro_data_analysis/Analysis/gresho_2d/plot_thesis_comparison.py')
    for name in (Path(__file__).name, 'run_n_gauss3_split.py', 'analyze_gresho_glass_boost_lab.py'):
        shutil.copy2(Path(__file__).parent/name, output/name)
    shutil.copy2(style_source, output/'chapter3_style_reference.py')
    result = dict(source=str(source), input_hashes=inputs_before,
                  source_archive_unchanged=True, cases=records,
                  mean_definition='35 uniform radial bins over [0,0.7); arithmetic mean of nodal vphi, no fitting or smoothing; raw points outside this range remain visible.',
                  bin_edges=BINS.tolist(), scatter_alpha=.09, scatter_size=3.,
                  moving_boost0_colors=boost0_colors,
                  plot_xlim=[0.,.71], plot_ylim=ylim,
                  data_frame='Laboratory-frame solver; subtract imposed boost and use the analytic periodic vortex center.',
                  diagnostic_norm='Unchanged mass-weighted L1 over all 2304 nodes; not recomputed from binned means.',
                  legend_location='inside upper right; all legend bounds checked',
                  pdf=str(pdf), pdf_sha256=sha(pdf), png=str(png),
                  script_sha256=sha(__file__),
                  chapter3_style_reference_sha256=sha(style_source))
    write(output/'summary.json', result)
    print(json.dumps(dict(pdf=str(pdf), png=str(png), cases=records), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    plot(args.source.resolve(), args.output.resolve())
