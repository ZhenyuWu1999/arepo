#!/usr/bin/env python3
"""Test Blob clock transformations against the unchanged published SVG trace.

The reference x remains its published t/t_KH coordinate. Transform current
native times as x=a*(t/t_cr), with the diameter-based t_cr. Alternatives to
a=1/1.6 are diagnostic hypotheses, not validated physical conversions.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

import h5py
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

TCR = 2 * np.sqrt(10) / 6.15
STATED_A = 1 / 1.6
CASES = ('N_equal_np8', 'N_hier_np8')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    with path.open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def git_text(root, *arguments):
    return subprocess.check_output(['git', *arguments], cwd=root, text=True).strip()


def audit_legacy(root):
    files = ('rd/main3D.cpp', 'rd/io3D.cpp', 'rd/constants3D.h.TEMPLATE')
    records = {name: {'path': str(root / name), 'sha256': sha256(root / name)} for name in files}
    assert 'T += DT;' in (root / files[0]).read_text()
    assert 'SNAPFILE << N_POINTS << "\\t" << T' in (root / files[1]).read_text()
    pattern = re.compile(r'\b(?:blob|cloud|t_?kh|t_?cr|t_?cc)\b|0\.64|1\.6', re.I)
    python_objects, matches = [], []
    for line in git_text(root, 'rev-list', '--all', '--objects').splitlines():
        parts = line.split(' ', 1)
        if len(parts) == 2 and parts[1].endswith('.py'):
            python_objects.append(parts)
            body = subprocess.check_output(['git', 'cat-file', 'blob', parts[0]], cwd=root).decode(errors='replace')
            found = [f'{i}: {text.strip()}' for i, text in enumerate(body.splitlines(), 1) if pattern.search(text)]
            if found:
                matches.append({'path': parts[1], 'blob': parts[0], 'lines': found})
    return dict(head=git_text(root, 'rev-parse', 'HEAD'),
                status=git_text(root, 'status', '--short'), source_files=records,
                raw_output_clock='main3D increments T by DT; io3D writes T directly to snapshot header and log.',
                historical_python_blobs_scanned=len(python_objects),
                search_pattern=pattern.pattern, historical_python_matches=matches,
                limitation='No Figure 20 normalization script recovered from this available checkout/history; no original publication-run snapshots.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True, help='Verified Morton-selection CSV/metadata directory.')
    p.add_argument('--bundle', type=Path, required=True, help='Downloaded native snapshots for header-time checks.')
    p.add_argument('--legacy-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True, help='New directory; never overwrite.')
    args = p.parse_args()
    source, bundle = args.input.resolve(), args.bundle.resolve()
    out = args.output.resolve()
    assert not out.exists(), out
    verification = json.loads((source / 'verification.json').read_text())
    paths = [source / f'{case}_cloud_mass.csv' for case in CASES]
    paths.append(source / 'morton_fig20_N32_digitized.csv')
    for path in paths:
        assert sha256(path) == verification['artifact_sha256'][path.name]
    ref = read_csv(paths[-1])
    rx = np.array([float(r['t_over_tKH_as_published']) for r in ref])
    rm = np.array([float(r['cloud_fraction']) for r in ref])
    assert np.all(np.diff(rx) > 0) and np.all(np.diff(rm) <= 1e-12)
    levels = np.linspace(.05, .95, 19)
    reference_crossings = np.interp(levels, rm[::-1], rx[::-1])
    reference_half = float(np.interp(.5, rm[::-1], rx[::-1]))
    histories, fits, comparisons, crossings, native_headers = {}, {}, [], [], []
    for case, path in zip(CASES, paths):
        rows = read_csv(path)
        time = np.array([float(r['time']) for r in rows])
        mass = np.array([float(r['fraction_morton_cut']) for r in rows])
        tau = time / TCR
        assert len(rows) == 31 and time[0] == 0 and mass[0] == 1
        assert np.all(np.diff(time) > 0) and np.all(np.diff(mass) <= 1e-12)
        np.testing.assert_allclose(tau, [float(r['t_over_tcc']) / 2 for r in rows], rtol=1e-14)
        np.testing.assert_allclose(tau / 1.6, [float(r['t_over_tKH']) for r in rows], rtol=1e-14)
        for row in rows:
            native = bundle / 'cases' / case / 'snapshots' / row['snapshot']
            with h5py.File(native, 'r') as f:
                assert float(f['Header'].attrs['Time']) == float(row['time'])
            native_headers.append(dict(path=str(native), time=float(row['time']), sha256=sha256(native)))
        current_crossings = np.interp(levels, mass[::-1], tau[::-1])
        current_half = float(np.interp(.5, mass[::-1], tau[::-1]))
        best = float(np.dot(current_crossings, reference_crossings) / np.dot(current_crossings, current_crossings))
        fits[case] = dict(a=best, relative_to_stated_KH_coordinate=best / STATED_A,
                          current_half_t_over_tcr=current_half, half_only_a=reference_half / current_half)
        hypotheses = [('stated_formula', STATED_A), ('previous_display_divided_by_1p6', STATED_A / 1.6),
                      ('current_tau_halved', .5), ('previous_display_times_1p6_or_raw_tau', 1.),
                      ('previous_display_times_2', 1.25), ('multiply_raw_tau_by_1p6', 1.6),
                      ('multiply_raw_tau_by_2', 2.), ('multiply_raw_tau_by_3p2', 3.2),
                      ('fitted_to_19_mass_levels', best)]
        for label, a in hypotheses:
            error = a * current_crossings - reference_crossings
            comparisons.append(dict(case=case, hypothesis=label, a=a,
                                    relative_to_stated_KH_coordinate=a / STATED_A,
                                    current_half_display_x=a * current_half,
                                    reference_half_display_x=reference_half,
                                    half_fractional_time_offset=(a * current_half / reference_half - 1),
                                    crossing_time_RMS=float(np.sqrt(np.mean(error**2))),
                                    crossing_time_Linf=float(np.max(np.abs(error)))))
        for fraction, current, reference in zip(levels, current_crossings, reference_crossings):
            crossings.append(dict(case=case, mass_fraction=float(fraction),
                                  current_t_over_tcr=float(current), reference_published_t_over_tKH=float(reference),
                                  pointwise_required_a=float(reference / current)))
        histories[case] = (tau, mass)
    out.mkdir(parents=True)
    write_csv(out / 'time_hypotheses.csv', comparisons)
    write_csv(out / 'mass_level_crossings.csv', crossings)
    inputs = out / 'inputs'
    inputs.mkdir()
    for path in paths:
        (inputs / path.name).write_bytes(path.read_bytes())
    legacy = audit_legacy(args.legacy_root.resolve())
    (out / 'legacy_source_audit.json').write_text(json.dumps(legacy, indent=2) + '\n')

    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(2, 2, figsize=(11.6, 8.3), sharex=True, sharey=True, layout='constrained')
    fig.get_layout_engine().set(rect=(0, .10, 1, .90))
    choices = [(STATED_A, '(a) Stated conversion: divide by 1.6'),
               (1., '(b) Previous displayed time multiplied by 1.6'),
               (1.6, '(c) Raw t/t_cr multiplied by 1.6'),
               (fits['N_equal_np8']['a'], '(d) Empirical fit to the full decay')]
    for ax, (a, title) in zip(axes.flat, choices):
        ax.plot(rx, rm, 's-', color='#b33939', ms=3, mfc='white', lw=1.5,
                label='Morton N1: published SVG coordinates')
        for case, label, color, style, marker in (
                ('N_equal_np8', 'Current N/RK2, equal', '#2468a0', '-', 'o'),
                ('N_hier_np8', 'Current N/RK2, hierarchy', '#d68b22', '--', None)):
            tau, mass = histories[case]
            plot_a = fits[case]['a'] if title.startswith('(d)') else a
            ax.plot(plot_a * tau, mass, color=color, ls=style, marker=marker, ms=2.5, lw=1.7, label=label)
        half = a * fits['N_equal_np8']['current_half_t_over_tcr']
        rms = float(np.sqrt(np.mean((a * np.array([r['current_t_over_tcr'] for r in crossings
                                                    if r['case'] == 'N_equal_np8']) - reference_crossings)**2)))
        ax.set(title=title + '\n' + rf'$x_{{\rm current}}=a(t/t_{{\rm cr}}),\quad a={a:.4f}$',
               xlim=(0, 2.2), ylim=(-.025, 1.045), xlabel='Displayed coordinate x')
        ax.axhline(.5, color='.6', ls=':', lw=.8)
        ax.grid(alpha=.18)
        ax.text(.97, .68, f'Half-mass x: current {half:.4f}; Morton {reference_half:.4f}\n'
                + rf'RMS $\Delta x$ at 5--95% mass: {rms:.4f}',
                transform=ax.transAxes, va='top', ha='right', fontsize=9)
    for ax in axes[:, 0]:
        ax.set_ylabel(r'$M_{\rm selected}/M_{\rm selected}(0)$')
    axes[0, 0].legend(loc='upper right', fontsize=8)
    fig.suptitle('3D Blob time-normalization hypotheses (diagnostic only)\n'
                 + r'Morton retains $x=t/t_{\rm KH}$; current uses $x=a(t/t_{\rm cr})$, '
                 + r'$t_{\rm cr}=2R\sqrt{\chi}/v_{\rm wind}$', fontsize=12)
    fig.text(.5, .056, 'Same Morton mass criterion in all panels. Transform current time only; no mass rescaling or time offset.',
             ha='center', fontsize=9)
    fig.text(.5, .020, 'Panel (c) shifts the previous current coordinate by 2.56, not 1.6. Alternative a values are unverified clock hypotheses.',
             ha='center', fontsize=9)
    for ext in ('png', 'pdf'):
        fig.savefig(out / f'blob_time_normalization_hypotheses.{ext}', dpi=180)
    plt.close(fig)
    summary = dict(script_sha256=sha256(Path(__file__).resolve()), tcr=TCR,
                   coordinate_definitions=dict(reference='Unchanged published Figure 20 t/t_KH coordinates.',
                                               current='x=a*(native Header.Time/t_cr), t_cr=2R*sqrt(chi)/v_wind.',
                                               stated_a=STATED_A,
                                               multiplication_hypothesis_a=1.6,
                                               multiplication_hypothesis_shift_vs_previous=1.6**2),
                   mass_selection='rho>64 AND p/rho<9; extensive native mass; initial selected-mass normalization.',
                   inputs=[dict(path=str(p), sha256=sha256(p)) for p in paths], native_headers=native_headers,
                   fits=fits, reference_half_published_t_over_tKH=reference_half,
                   fit_definition='Least squares through the origin in crossing times at 19 equally spaced mass fractions 0.05..0.95; piecewise-linear interpolation.',
                   uncertainty='Published vector-path vertices and 31 saved current states; no original reference samples or uncertainty model.',
                   inference='Multiplying raw t/t_cr by 1.6 substantially improves overlap, but is not exact. Source of remaining or original discrepancy is not established.',
                   legacy_source_audit='legacy_source_audit.json',
                   figures={p.name: sha256(p) for p in out.iterdir() if p.suffix in ('.png', '.pdf')})
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(dict(output=str(out), fits=fits, reference_half=reference_half), indent=2))


if __name__ == '__main__':
    main()
