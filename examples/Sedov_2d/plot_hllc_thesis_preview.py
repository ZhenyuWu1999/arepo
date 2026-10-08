#!/usr/bin/env python3
"""Thesis-style preview (not inserted in the thesis): HLLC-RD Sedov versus MMFV and SWIFT.

Same glass 128^2, 21 heated points, t=0.05. Loads the archived, hash-verified
runs through the existing verification helpers; writes only into the HLLC
archive's analysis/thesis_preview directory.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from scipy.stats import binned_statistic
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/'tests/rd'))
sys.path.insert(0, str(HERE))
from run_n_gauss3_split import state, sha, write
from analyze_swift_default import swift_state, center, radial
from analyze_mmfv import fv_state, verify_native
from audit_reference_scales import dense_reference

L = REPO.parent/'local_runs'
HLLC = L/'sedov_hllc_20260930_v1'
MMFV = L/'sedov_mmfv_20260929_v1'
SPH = L/'swift_sedov_default_20260929_v1'


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    exact = dense_reference(); runs = {}; origin = {}
    dual = np.load(HLLC/'inputs/median_dual_area.npy'); ic = HLLC/'inputs/sedov_nearest21.hdf5'
    for key, method in (('HLLC-RD, moving mesh', 'HLLC_moving'), ('HLLC-RD, static mesh', 'HLLC_static')):
        runs[key] = verify_native(HLLC, method, HLLC/'runs'/f'nearest21_{method}', state)[0]
        origin[key] = center(ic, dual)
    runs['AREPO MMFV'] = verify_native(MMFV, 'MMFV_moving', MMFV/'runs/nearest21', fv_state)[0]
    s0 = runs['AREPO MMFV'][0]; hot = s0['u'] > 2e-6
    origin['AREPO MMFV'] = np.average(s0['xy'][hot], axis=0, weights=s0['mass'][hot]*(s0['u'][hot]-1.5e-6))
    meta = json.loads((SPH/'analysis/verification.json').read_text())
    assert sha(SPH/'artifact/swift') == meta['swift_provenance']['binary_sha256']
    row = meta['snapshots'][-1]; assert sha(row['path']) == row['sha256']
    runs['SWIFT SPHENIX'] = [swift_state(Path(row['path']))]
    origin['SWIFT SPHENIX'] = np.array(meta['profiles']['SWIFT_21']['center'])
    final = {k: radial(v[-1], origin[k]) for k, v in runs.items()}
    for k, s in final.items():
        assert abs(s['time'] - .05) < 1e-9, (k, s['time'])

    styles = [('HLLC-RD, moving mesh', '#c0392b', '-', 2.0), ('HLLC-RD, static mesh', '#e08e3c', '--', 1.6),
              ('AREPO MMFV', '#376db1', '-.', 1.6), ('SWIFT SPHENIX', '#2a9d8f', ':', 1.8)]
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(2, 3, figsize=(12.8, 7.2), layout='constrained')
    for row_i, rmax in enumerate((.4, .15)):
        bins = np.arange(0, rmax+1e-4, .005); mid = (bins[1:]+bins[:-1])/2
        for ax, field, label, exterior in zip(axes[row_i], ('rho', 'vr', 'p'), ('$\\rho$', '$v_r$', '$p$'), (1., 0., 1e-6)):
            for key, color, ls, lw in styles:
                s = final[key]; take = s['r'] < rmax
                ax.scatter(s['r'][take], s[field][take], s=2 if row_i == 0 else 6,
                           alpha=.03 if row_i == 0 else .12, color=color, rasterized=True, lw=0)
                ax.plot(mid, binned_statistic(s['r'], s[field], statistic='mean', bins=bins)[0],
                        color=color, ls=ls, lw=lw, label=key)
            ax.plot(np.r_[exact['r'], exact['shock'], .45], np.r_[exact[field], exterior, exterior], 'k--', lw=1.1,
                    label='Analytic')
            # Data-driven limits: every plotted sample stays visible (no clipping).
            values = np.concatenate([final[k][field][final[k]['r'] < rmax] for k, _, _, _ in styles])
            lo = min(0., float(values.min())); hi = max(float(values.max()), float(np.max(exact[field][exact['r'] < rmax])))
            pad = .05*(hi-lo)
            ax.set(xlim=(0, rmax), ylim=(lo-pad, hi+pad), xlabel='$r$', ylabel=label)
            ax.grid(alpha=.15)
    axes[0, 0].legend(fontsize=8.5, frameon=False)
    fig.savefig(out/'hllc_sedov_thesis_preview.png', dpi=300); fig.savefig(out/'hllc_sedov_thesis_preview.pdf')
    plt.close(fig)
    write(out/'preview_meta.json', dict(script_sha256=sha(__file__), times={k: s['time'] for k, s in final.items()},
        note='Preview only; not inserted in the thesis. Axis limits include every sample. SWIFT uses individual '
             'timesteps; RD/MMFV equal adaptive steps. Radius from each initial injected-energy centroid.'))


def n_static_run(base):
    """Archived static N/RK2 (log3 §156) used an output list (7 snapshots), so the
    5-snapshot verifier does not apply; check provenance, completion and states."""
    artifact = base/'artifacts/N_static_lab'; folder = base/'runs/disk005_N_static_lab'
    meta = json.loads((artifact/'provenance.json').read_text())
    assert sha(artifact/'Arepo') == meta['binary_sha256']
    status = json.loads((folder/'run_status.json').read_text())
    assert status['returncode'] == 0 and status['binary_sha256'] == meta['binary_sha256']
    seq = [state(p) for p in sorted((folder/'output').glob('snap_*.hdf5'))]
    assert abs(seq[-1]['time'] - .05) < 1e-12
    for s in seq:
        assert all(np.all(np.isfinite(s[k])) for k in ('rho', 'p', 'v', 'mass')) and s['rho'].min() > 0 and s['p'].min() > 0
        assert np.array_equal(s['xy'], seq[0]['xy'])
    return seq


def main_disk005(out):
    """Matched 130-node (r=.05) injection: the only completed N-scheme Sedov (static)."""
    base = L/'sedov_2d_20260929_v1'; disk = L/'sedov_hllc_disk005_20260930_v1'
    out.mkdir(parents=True, exist_ok=False)
    exact = dense_reference(); dual = np.load(disk/'inputs/median_dual_area.npy'); ic = disk/'inputs/sedov_disk005.hdf5'
    runs = {'HLLC-RD, moving mesh': verify_native(disk, 'HLLC_moving', disk/'runs/disk005_HLLC_moving', state)[0],
            'HLLC-RD, static mesh': verify_native(disk, 'HLLC_static', disk/'runs/disk005_HLLC_static', state)[0],
            'N scheme (RK2), static mesh': n_static_run(base)}
    origin = center(ic, dual)
    final = {k: radial(v[-1], origin) for k, v in runs.items()}
    for k, s in final.items():
        assert abs(s['time'] - .05) < 1e-9, (k, s['time'])
    styles = [('HLLC-RD, moving mesh', '#c0392b', '-', 2.0), ('HLLC-RD, static mesh', '#e08e3c', '--', 1.6),
              ('N scheme (RK2), static mesh', '#6c7a89', '-.', 1.6)]
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(2, 3, figsize=(12.8, 7.2), layout='constrained')
    for row_i, rmax in enumerate((.4, .15)):
        bins = np.arange(0, rmax+1e-4, .005); mid = (bins[1:]+bins[:-1])/2
        for ax, field, label, exterior in zip(axes[row_i], ('rho', 'vr', 'p'), ('$\\rho$', '$v_r$', '$p$'), (1., 0., 1e-6)):
            for key, color, ls, lw in styles:
                s = final[key]; take = s['r'] < rmax
                ax.scatter(s['r'][take], s[field][take], s=2 if row_i == 0 else 6,
                           alpha=.03 if row_i == 0 else .12, color=color, rasterized=True, lw=0)
                ax.plot(mid, binned_statistic(s['r'], s[field], statistic='mean', bins=bins)[0],
                        color=color, ls=ls, lw=lw, label=key)
            ax.plot(np.r_[exact['r'], exact['shock'], .45], np.r_[exact[field], exterior, exterior], 'k--', lw=1.1,
                    label='Analytic (point source)')
            values = np.concatenate([final[k][field][final[k]['r'] < rmax] for k, _, _, _ in styles])
            lo = min(0., float(values.min())); hi = max(float(values.max()), float(np.max(exact[field][exact['r'] < rmax])))
            pad = .05*(hi-lo)
            ax.set(xlim=(0, rmax), ylim=(lo-pad, hi+pad), xlabel='$r$', ylabel=label)
            ax.grid(alpha=.15)
    axes[0, 0].legend(fontsize=8.5, frameon=False)
    fig.savefig(out/'hllc_n_sedov_disk005_preview.png', dpi=300); fig.savefig(out/'hllc_n_sedov_disk005_preview.pdf')
    plt.close(fig)
    metrics = {}
    for k, s in final.items():
        means = binned_statistic(s['r'], s['rho'], statistic='mean', bins=np.arange(0, .4001, .005))[0]
        core = s['r'] < .05
        metrics[k] = dict(rho_max=float(s['rho'].max()), rho_min=float(s['rho'].min()), mean_peak=float(np.nanmax(means)),
                          core_rho_area=float(s['mass'][core].sum()/s['w'][core].sum()), core_n=int(core.sum()),
                          core_p=float(s['p'][core].mean()),
                          dM=float(s['totals'][0]/runs[k][0]['totals'][0]-1), dE=float(s['totals'][3]/runs[k][0]['totals'][3]-1))
    write(out/'preview_meta.json', dict(script_sha256=sha(__file__), metrics=metrics,
        note='Preview only; 130-node r=.05 injection (21-node N fails). Axis limits include every sample.'))
    print(json.dumps(metrics, indent=1))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('out', type=Path)
    p.add_argument('--disk005', action='store_true')
    a = p.parse_args()
    (main_disk005 if a.disk005 else main)(a.out.resolve())
