#!/usr/bin/env python3
"""Plot archived independent scalar experiments; no native solver claims."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter, NullFormatter


def main(root, stem):
    fixed = json.loads((root/'true_ale_split_order_20260914_v1/summary.json').read_text())
    balance = json.loads((root/'true_ale_split_balance_20260914_v1/summary.json').read_text())
    checks = json.loads((root/'true_ale_split_balance_checks_20260914_v1/summary.json').read_text())
    outputs = [stem.with_suffix(ext) for ext in ('.png', '.svg')]
    assert not any(p.exists() for p in outputs), 'Refuse to replace existing figures'
    colors = {'n': '#17668a', 'lda_f1': '#bd4d28'}
    names = {'n': 'N / lumped', 'lda_f1': 'LDA / F1'}
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'figure.facecolor': 'white'})
    fig, axes = plt.subplots(1, 3, figsize=(14.4, 4.7))
    for row in fixed['fixed']:
        if row['motion'] != 'deform':
            continue
        cases, method = row['rows'], row['method']
        axes[0].loglog([r['dt'] for r in cases], [r['L1_to_ODE'] for r in cases], 'o-',
            color=colors[method], label=f"{names[method]}: p = {cases[-1]['observed_p']:.2f}")
    for row in balance['time_ladders']:
        cases, method = row['cases'][:-1], row['method']
        axes[1].loglog([r['dt'] for r in cases], [r['L1_to_2048_steps'] for r in cases], 'o-',
            color=colors[method], label=f"{names[method]}: last p = {cases[-1]['observed_p']:.2f}")
    for row in checks['spatial']:
        cases, method = row['cases'], row['method']
        axes[2].loglog([1/r['n'] for r in cases], [r['L1'] for r in cases], 'o-',
            color=colors[method], label=f"{names[method]}: {cases[1]['observed_h_slope']:.2f}, {cases[2]['observed_h_slope']:.2f}")
    axes[0].set_title('Fixed connectivity: time integration\nMoving nodes; DOP853 reference', fontsize=11)
    axes[1].set_title('Old/new split + local balance: time\nWith flips; 2048-step reference', fontsize=11)
    axes[2].set_title('Old/new split + local balance: space\nWith flips; h and dt refined together', fontsize=11)
    for ax in axes:
        ax.grid(True, which='both', alpha=.18)
        ax.legend(frameon=False, fontsize=9, loc='upper left')
    axes[0].set_xlabel(r'$\Delta t$ (144 nodes, final time 0.25)')
    axes[1].set_xlabel(r'$\Delta t$ (144 nodes, final time 0.5)')
    axes[2].set_xlabel(r'$h=1/n$ (64, 256, 1024 nodes; final time 0.5)')
    axes[0].set_ylabel(r'Area-weighted $L_1$ error to limiting ODE')
    axes[1].set_ylabel(r'Area-weighted $L_1$ difference to fine run')
    axes[2].set_ylabel(r'Area-weighted $L_1$ error to exact advection')
    for ax, denoms in zip(axes, ((2048, 512, 128), (1024, 512, 256, 128), (32, 16, 8))):
        ax.xaxis.set_major_locator(FixedLocator([1/d for d in denoms]))
        ax.xaxis.set_major_formatter(FixedFormatter([f'1/{d}' for d in denoms]))
        ax.xaxis.set_minor_formatter(NullFormatter())
    fig.suptitle('Two-stage ALE-RD exploration: conservation does not establish time order', fontsize=14, y=.99)
    fig.text(.5, .018, 'Independent scalar model; prescribed linear node paths, periodic jittered meshes. '
             'These are not native AREPO or formal asymptotic-order results.', ha='center', fontsize=9, color='#444444')
    fig.tight_layout(rect=(0, .06, 1, .94), w_pad=2.5)
    stem.parent.mkdir(parents=True, exist_ok=True)
    for p in outputs:
        fig.savefig(p, dpi=180, facecolor='white')
    plt.close(fig)
    print('\n'.join(map(str, outputs)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive_root', type=Path)
    parser.add_argument('output_stem', type=Path)
    args = parser.parse_args()
    main(args.archive_root.resolve(), args.output_stem.resolve())
