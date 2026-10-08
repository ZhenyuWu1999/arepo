#!/usr/bin/env python3
"""Mass-weighted radial profiles of the 8 Sedov runs with every sample as a faint point.

Same runs, origins, bins and mass-weighted means as plot_sedov_profiles_mw.py
(reused, not copied). Added: each vertex (RD), cell centroid (MMFV) or particle
(SWIFT) as a faint point; y-axes shared per column so the analytic curve has the
same scale in both rows. Samples outside the common y-range are marked at the
panel edge and listed in the metadata, not dropped silently.

--min-count N (default 0, i.e. v1 behaviour): draw each mean line only from the
innermost radius beyond which every bin of that run has at least N samples.
The same rule applies to every method; the faint points are always all shown.
--rmin R (default 0): additionally start every mean line at bin left edge >= R.
--no-offscale-marker: do not draw off-scale samples at the panel edge (still listed in the metadata).
"""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
from plot_sedov_profiles_mw import BINS, MID, mass_weighted, load_all, dense_reference, sha, write

STYLES = {'SWIFT SPHENIX': ('#2a9d8f', ':', 1.9), 'HLLC-RD, static mesh': ('#e08e3c', '--', 1.6),
          'AREPO MMFV': ('#376db1', '-.', 1.6), 'HLLC-RD, moving mesh': ('#c0392b', '-', 2.0)}
FIELDS = (('rho', r'$\rho$', 1., (-.15, 4.45)), ('vr', r'$v_r$', 0., (-.5, 2.3)), ('p', r'$p$', 1e-6, (-.25, 5.6)))


def line_start(s, min_count):
    """Index of the innermost bin beyond which every bin has >= min_count samples."""
    bad = np.flatnonzero(np.histogram(s['r'], BINS)[0] < min_count)
    return int(bad.max()) + 1 if bad.size else 0


def main(out, min_count=0, label_offscale=True, rmin=0., mark_offscale=True):
    out.mkdir(parents=True, exist_ok=False)
    exact = dense_reference(); runs = load_all()
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(2, 3, figsize=(12.8, 7.2), layout='constrained', sharex=True, sharey='col')
    offscale, starts = [], {}
    for r, (row, label) in enumerate((('21', '21 hot points'), ('1', '1 hot point'))):
        for c, (field, ylab, exterior, ylim) in enumerate(FIELDS):
            ax = axes[r, c]
            for key in STYLES:                       # faint samples first, lines on top
                s = runs[row][key]; color = STYLES[key][0]
                ax.scatter(s['r'], s[field], s=1.3, color=color, alpha=.12, lw=0, rasterized=True, zorder=1)
                hi = (s[field] > ylim[1]) & (s['r'] < .4)
                for rr, q in zip(s['r'][hi], s[field][hi]):
                    offscale.append(dict(row=label, method=key, field=field, r=float(rr), value=float(q)))
                    if mark_offscale:
                        ax.plot(rr, ylim[1] - .02 * (ylim[1] - ylim[0]), marker='^', ms=6, color=color, mec='k',
                                mew=.5, clip_on=False, zorder=5)
                    if label_offscale:
                        ax.annotate(f'{key.split()[0]} hot particle: {field} = {q:.1f}', xy=(rr, ylim[1]),
                                    xytext=(.035, ylim[1] - .09 * (ylim[1] - ylim[0])), fontsize=8, color=color,
                                    va='top')
            for key, (color, ls, lw) in STYLES.items():
                prof = mass_weighted(runs[row][key], field)
                k = max(line_start(runs[row][key], min_count), int(np.searchsorted(BINS[:-1], rmin - 1e-12)))
                prof[:k] = np.nan
                starts[f'{label}/{key}'] = float(BINS[k])
                stroke = [pe.Stroke(linewidth=lw + 1.6, foreground='white', alpha=.8), pe.Normal()]
                ax.plot(MID, prof, color=color, ls=ls, lw=lw, label=key, zorder=3, path_effects=stroke)
                finite = np.isfinite(prof)
                isolated = finite & ~np.r_[False, finite[:-1]] & ~np.r_[finite[1:], False]
                ax.plot(MID[isolated], prof[isolated], 'o', color=color, ms=3.2, ls='none', zorder=3)
            ax.plot(np.r_[exact['r'], exact['shock'], .45], np.r_[exact[field], exterior, exterior], 'k--', lw=1.1,
                    label='Analytic (point source)', zorder=4)
            ax.set(xlim=(0, .4), ylim=ylim, ylabel=ylab); ax.grid(alpha=.15)
            if r == 1: ax.set_xlabel('$r$')
            if c == 0: ax.text(.02, .95, label, transform=ax.transAxes, va='top', fontsize=10)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    order = [labels.index(k) for k in ('HLLC-RD, static mesh', 'HLLC-RD, moving mesh', 'AREPO MMFV', 'SWIFT SPHENIX',
                                       'Analytic (point source)')]
    axes[0, 0].legend([handles[i] for i in order], [labels[i] for i in order], fontsize=8.5, frameon=False,
                      loc='center left')
    fig.savefig(out/'sedov_profiles_mass_weighted_points.png', dpi=300)
    fig.savefig(out/'sedov_profiles_mass_weighted_points.pdf', dpi=300)
    plt.close(fig)
    write(out/'profiles_meta.json', dict(script_sha256=sha(__file__), base_script_sha256=sha(Path(__file__).with_name(
        'plot_sedov_profiles_mw.py')), bins='width .005, 0-.4', min_count=min_count, rmin=rmin, offscale_marked=mark_offscale, line_start_radius=starts, y_limits={f: list(l) for f, _, _, l in FIELDS},
        offscale_samples=offscale, analytic=dict(shock=exact['shock'], p_max=float(exact['p'].max()),
        p_centre=float(exact['p'][np.argmin(exact['r'])]), same_curve_in_both_rows=True),
        note='Preview only. Lines: mass-weighted means sum(m q)/sum(m) in bins of .005 (as v1). Points: every '
             'RD vertex, MMFV cell centroid and SWIFT particle at t=0.05; alpha .12, rasterized in the PDF.'))
    print(json.dumps(offscale, indent=1))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('out', type=Path)
    p.add_argument('--min-count', type=int, default=0)
    p.add_argument('--no-offscale-label', action='store_true')
    p.add_argument('--rmin', type=float, default=0.)
    p.add_argument('--no-offscale-marker', action='store_true')
    a = p.parse_args()
    main(a.out.resolve(), a.min_count, not a.no_offscale_label, a.rmin, not a.no_offscale_marker)
