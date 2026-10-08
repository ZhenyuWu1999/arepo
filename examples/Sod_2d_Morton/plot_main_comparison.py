#!/usr/bin/env python3
"""Plot the requested first-order static / RK2 static / RK2 moving comparison."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import h5py
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]/'tests/rd'))
if (HERE/'run_n_gauss3_split.py').exists():
    sys.path.insert(0, str(HERE))
from run_n_gauss3_split import sha, state, write

METHODS = {
    'N': ('N1_roe_static', 'N_rk2_roe_static', 'N_rk2_roe_moving'),
    'LDA': ('LDA1_roe_static', 'LDA_f1_gauss3_static', 'LDA_f1_gauss3_moving'),
}


def main(source, output):
    output.mkdir(parents=True, exist_ok=False)
    (output/'figures').mkdir(); (output/'output/pdf').mkdir(parents=True)
    summary = json.loads((source/'summary.json').read_text())
    inputs = {str(source/'summary.json'): sha(source/'summary.json')}
    curves, selected = {}, []
    for c in summary['cases']:
        if c['method'] not in METHODS[c['scheme']]:
            continue
        assert c['complete'] and c['end_time'] == .2
        path = Path(c['snapshot'])
        inputs[str(path)] = sha(path)
        assert inputs[str(path)] == summary['input_hashes'][str(path)]
        s = state(path)
        with h5py.File(path) as f:
            g = f['PartType0']; order = np.argsort(g['ParticleIDs'][:])
            energy = g['InternalEnergy'][:][order]
        mask = (s['xy'][:, 0] > 1) & (s['xy'][:, 0] < 2)
        x = s['xy'][mask, 0]-1
        q = np.column_stack((s['rho'][mask], s['v'][mask, 0], s['p'][mask], energy[mask]))
        csv = source/(c['name']+'_bin_means.csv')
        inputs[str(csv)] = sha(csv)
        b = np.loadtxt(csv, delimiter=',', skiprows=1)
        ib = np.digitize(x, np.linspace(0, 1, 129))-1
        np.testing.assert_array_equal(b[:, 5], np.bincount(ib, minlength=128))
        np.testing.assert_array_equal(b[:, 1:5], np.array([q[ib == k].mean(axis=0) for k in range(128)]))
        assert len(x) == c['tube_nodes']
        curves[(c['method'], c['effective_Nx'])] = (x, q, b[:, 0], b[:, 1:5])
        selected.append(c)
    assert len(curves) == 12
    rf = source/'source/examples/shocktube_1d/Riemann.py'
    inputs[str(rf)] = sha(rf)
    assert inputs[str(rf)] == summary['input_hashes'][str(rf)]
    spec = importlib.util.spec_from_file_location('frozen_riemann', rf)
    riemann = importlib.util.module_from_spec(spec); spec.loader.exec_module(riemann)
    xx = np.linspace(0, 1, 3001)
    _, reference, _ = riemann.RiemannProblem(xx+1, 1.5, np.array([1., 0., 1.]),
        np.array([.125, 0., .1]), 5/3, .2)
    reference = np.column_stack((reference, reference[:, 2]/((5/3-1)*reference[:, 0])))
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.linewidth': .8,
        'xtick.direction': 'in', 'ytick.direction': 'in', 'xtick.top': True, 'ytick.right': True,
        'pdf.fonttype': 42})
    labels = [r'Density $\rho$', r'Velocity $v_x$', r'Pressure $p$']
    styles = [('Static, first-order RD', '#55865a', (0, (1.5, 1.8))),
              ('Static, RK2', '#2878af', (1.5, (4, 2.5))),
              ('Moving, RK2', '#cb7629', (3, (7, 3.5)))]
    pdfpath = output/'output/pdf/Sod_2d_Morton_main_comparison.pdf'
    with PdfPages(pdfpath) as pdf:
        for nx in (128, 64):
            fig, axes = plt.subplots(3, 2, figsize=(9.5, 7.9), sharex=True,
                sharey='row', layout='constrained')
            for j, (scheme, methods) in enumerate(METHODS.items()):
                for k in range(3):
                    ax = axes[k, j]
                    for method, (label, color, ls) in zip(methods, styles):
                        x, q, bx, mean = curves[(method, nx)]
                        ax.scatter(x, q[:, k], s=2.4, color=color, alpha=.085,
                            edgecolors='none', rasterized=True, zorder=1)
                        ax.plot(bx, mean[:, k], color=color, ls=ls, lw=1.35, label=label, zorder=3)
                    ax.plot(xx, reference[:, k], color='black', lw=1.05, label='Exact', zorder=4)
                    ax.set_xlim(0, 1); ax.grid(color='.90', lw=.5)
                    if j == 0:
                        ax.set_ylabel(labels[k])
                axes[0, j].set_title(scheme, fontsize=11)
                axes[0, j].legend(loc='upper right', fontsize=8, framealpha=.94)
                axes[-1, j].set_xlabel(r'$x$')
            fig.suptitle(rf'Sod shock tube, $N_x = {nx}$, $\gamma = 5/3$, $t = 0.2$', fontsize=12)
            fig.savefig(output/f'figures/Sod_2d_Morton_main_Nx{nx}.png', dpi=600)
            pdf.savefig(fig, dpi=600); plt.close(fig)
    assert all(sha(p) == h for p, h in inputs.items())
    shutil.copy2(__file__, output/'plot_main_comparison.py')
    shutil.copy2(HERE.parents[1]/'tests/rd/run_n_gauss3_split.py' if not (HERE/'run_n_gauss3_split.py').exists()
        else HERE/'run_n_gauss3_split.py', output/'run_n_gauss3_split.py')
    write(output/'comparison.json', dict(source=str(source), methods=METHODS, selected_cases=selected,
        first_order='Full-step lumped RD predictor, U(n+1)=U*, with no corrector or F1 temporal term.',
        first_order_residual='Roe for N and LDA, following the Morton-style first-order baseline.',
        rk2_residual='N: Roe (mesh split when moving). LDA: Gauss3 contour, F1 temporal mass.',
        interpretation='Static/moving RK2 pairs use the same residual family. The LDA first-order-to-RK2 comparison also changes Roe to Gauss3 and does not isolate time integration alone.',
        coordinates='x=X-1 on the raw right tube 1<X<2; t=.2, unchanged.',
        input_hashes=inputs))
    write(output/'verification.json', dict(source_inputs_unchanged=True, selected_curves=12,
        raw_nodes_and_bin_means_unchanged=True, new_hydrodynamic_runs=0,
        expected_pdf_pages=2, visual_review='pending'))
    print('Created two-page comparison from twelve verified existing cases.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    main(args.source.resolve(), args.output.resolve())
