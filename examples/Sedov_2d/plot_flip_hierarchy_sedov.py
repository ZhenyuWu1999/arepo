#!/usr/bin/env python3
"""Sedov t=0.05 with conservative flips and the moving hierarchy (preview, not in the thesis).

Runs (HLLC-RD, moving mesh, gamma 5/3, 21- and 1-point injection):
  thesis              sedov_hllc_20260930_v1 HLLC_moving (Arpaia, flips change totals)
  Campoli             sedov_flip_gate_20261009_v1 HLLC_campoli (no topology treatment)
  Campoli + flip      sedov_flip_gate_20261009_v1 HLLC_flip (RD_ALE_FLIP_TRANSFER)
  hierarchy           interval_hierarchy_gates_20261009_v2 HLLC_ih_natural (natural bins)
Figure 1: mass-weighted rho, v_r, p profiles against the analytic solution
(same bins and origin as the thesis profile figure).
Figure 2: relative mass and total-energy change versus time, from the snapshots.
Runs that are not complete are skipped and listed in the metadata.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tests/rd'))
sys.path.insert(0, str(HERE))
from run_n_gauss3_split import state, write                       # noqa: E402
from analyze_swift_default import center, radial                   # noqa: E402
from audit_reference_scales import dense_reference                 # noqa: E402
from plot_sedov_profiles_mw import mass_weighted, MID              # noqa: E402

L = REPO.parent / 'local_runs'
H = L / 'sedov_hllc_20260930_v1'
RUNS = {'thesis (Arpaia)': (H, 'HLLC_moving', '#7f7f7f', '-', 2.4),
        'Campoli': (L / 'sedov_flip_gate_20261009_v1', 'HLLC_campoli', '#e08e3c', '--', 1.6),
        'Campoli + flip transfer': (L / 'sedov_flip_gate_20261009_v1', 'HLLC_flip', '#c0392b', '-', 1.6),
        'hierarchy (natural bins)': (L / 'interval_hierarchy_gates_20261009_v2', 'HLLC_ih_natural', '#376db1', '-.', 1.6)}
GROUPS = {'21': ('nearest21', 'sedov21', '21 hot points'), '1': ('nearest1', 'sedov1', '1 hot point')}
FIELDS = (('rho', r'$\rho$'), ('vr', r'$v_r$'), ('p', r'$p$'))


def folder(root, method, group):
    tag = GROUPS[group][1] if 'interval_hierarchy' in root.name else GROUPS[group][0]
    return root / 'runs' / f'{tag}_{method}'


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    dual = np.load(H / 'inputs/median_dual_area.npy')
    exact = dense_reference()
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(2, 3, figsize=(12.8, 7.2), layout='constrained', sharex=True, sharey='col')
    fig2, axes2 = plt.subplots(2, 2, figsize=(10, 6.4), layout='constrained', sharex=True)
    meta = dict(skipped=[], runs={})
    for r, group in enumerate(GROUPS):
        origin = center(H / 'inputs' / f'sedov_{GROUPS[group][0]}.hdf5', dual)
        for label, (root, method, color, ls, lw) in RUNS.items():
            f = folder(root, method, group)
            status = f / 'run_status.json'
            if not status.exists() or json.loads(status.read_text())['returncode'] != 0:
                meta['skipped'].append(str(f)); continue
            snaps = sorted((f / 'output').glob('snap_*.hdf5'))
            ss = [state(p) for p in snaps]
            if abs(ss[-1]['time'] - .05) > 1e-9:
                meta['skipped'].append(str(f)); continue
            s = radial(ss[-1], origin)
            for c, (field, ylab) in enumerate(FIELDS):
                axes[r, c].plot(MID, mass_weighted(s, field), color=color, ls=ls, lw=lw, label=label)
            t = np.array([x['time'] for x in ss]); tot = np.array([x['totals'] for x in ss])
            for c, (k, name) in enumerate(((0, 'mass'), (3, 'energy'))):
                axes2[r, c].plot(t, tot[:, k] / tot[0, k] - 1, color=color, ls=ls, lw=lw, marker='o', ms=3, label=label)
            meta['runs'][f'{group}/{label}'] = dict(folder=str(f), snapshots=len(snaps),
                                                     drift=[float(tot[-1, k] / tot[0, k] - 1) for k in (0, 3)])
        for c, (field, ylab) in enumerate(FIELDS):
            ax = axes[r, c]
            ax.plot(exact['r'], exact[field], color='k', lw=1, label='analytic')
            ax.set(ylabel=ylab, xlim=(0, .4))
            ax.set_title(f'{GROUPS[group][2]}: {ylab}', fontsize=10)
        for c, name in enumerate(('mass', 'total energy')):
            axes2[r, c].set(ylabel=f'relative {name} change', title=f'{GROUPS[group][2]}: {name}')
            axes2[r, c].axhline(0, color='k', lw=.6)
    for ax in axes[-1]:
        ax.set_xlabel('r')
    for ax in axes2[-1]:
        ax.set_xlabel('t')
    axes[0, 0].legend(frameon=False, fontsize=8)
    axes2[0, 0].legend(frameon=False, fontsize=8)
    fig.savefig(out / 'sedov_flip_hierarchy_profiles.png', dpi=170)
    fig2.savefig(out / 'sedov_flip_hierarchy_conservation.png', dpi=170)
    write(out / 'metadata.json', meta)
    print(json.dumps(meta, indent=1))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('out', type=Path)
    main(p.parse_args().out.resolve())
