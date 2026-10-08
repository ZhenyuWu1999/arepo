#!/usr/bin/env python3
"""Mass-weighted radial profiles of the 8 Sedov runs at t=0.05 (preview, not in the thesis).

Rows: 21 hot points (SWIFT default) and a single hot point (particle ID 8256).
Columns: rho, v_r, p. Each curve is sum(m q)/sum(m) in radial bins of width .005,
radius from each run's initial injected-energy centroid. Empty bins are left blank; isolated non-empty bins are drawn as dots.
Methods: HLLC-RD static/moving, AREPO MMFV (cell centroids), SWIFT SPHENIX.
"""
import argparse
import json
from pathlib import Path
import sys
import h5py
import numpy as np
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
BINS = np.arange(0, .4001, .005)
MID = .5*(BINS[1:]+BINS[:-1])


def mass_weighted(s, field):
    m = np.histogram(s['r'], BINS, weights=s['mass'])[0]
    q = np.histogram(s['r'], BINS, weights=s['mass']*s[field])[0]
    out = np.full(len(MID), np.nan); out[m > 0] = q[m > 0]/m[m > 0]
    return out


def fv_origin(s0):
    hot = s0['u'] > 2e-6
    return np.average(s0['xy'][hot], axis=0, weights=s0['mass'][hot]*(s0['u'][hot]-1.5e-6))


def swift_origin(ic):
    with h5py.File(ic) as f:
        g = f['PartType0']; xy = g['Coordinates'][:, :2]; u = g['InternalEnergy'][:]; m = g['Masses'][:]
    hot = u > 1e-3
    return np.average(xy[hot], axis=0, weights=m[hot]*u[hot])


def load_all():
    H = L/'sedov_hllc_20260930_v1'; H1 = L/'sedov_hllc_nearest1_static_20260930_v1'
    M = L/'sedov_mmfv_20260929_v1'; M1 = L/'sedov_mmfv_single_20261001_v1'
    W = L/'swift_sedov_default_20260929_v1'; W1 = L/'swift_sedov_single_20261001_v1'
    dual = np.load(H/'inputs/median_dual_area.npy')
    ic21, ic1 = H/'inputs/sedov_nearest21.hdf5', H/'inputs/sedov_nearest1.hdf5'
    rd = lambda root, method, group: verify_native(root, method, root/'runs'/f'{group}_{method}', state)[0][-1]
    for root in (W, W1):
        assert sha(root/'artifact/swift') == json.loads((root/'artifact/provenance.json').read_text())['binary_sha256']
    camp = json.loads((M1/'campaign.json').read_text())
    assert sha(M1/'artifacts/MMFV_moving/Arepo') == camp['binary_sha256']
    mm = verify_native(M, 'MMFV_moving', M/'runs/nearest21', fv_state)[0]
    mm1 = [fv_state(p) for p in sorted((M1/'runs/nearest1_MMFV/output').glob('snap_*.hdf5'))]
    runs = {
        '21': {'HLLC-RD, static mesh': radial(rd(H, 'HLLC_static', 'nearest21'), center(ic21, dual)),
               'HLLC-RD, moving mesh': radial(rd(H, 'HLLC_moving', 'nearest21'), center(ic21, dual)),
               'AREPO MMFV': radial(mm[-1], fv_origin(mm[0])),
               'SWIFT SPHENIX': radial(swift_state(W/'run/sedov_0005.hdf5'), swift_origin(W/'run/sedov.hdf5'))},
        '1': {'HLLC-RD, static mesh': radial(rd(H1, 'HLLC_static', 'nearest1'), center(ic1, dual)),
              'HLLC-RD, moving mesh': radial(rd(H, 'HLLC_moving', 'nearest1'), center(ic1, dual)),
              'AREPO MMFV': radial(mm1[-1], fv_origin(mm1[0])),
              'SWIFT SPHENIX': radial(swift_state(W1/'run/sedov_0005.hdf5'), swift_origin(W1/'run/sedov.hdf5'))}}
    for row in runs.values():
        for key, s in row.items():
            assert abs(s['time']-.05) < 1e-9, (key, s['time'])
    return runs


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    exact = dense_reference(); runs = load_all()
    styles = {'HLLC-RD, static mesh': ('#e08e3c', '--', 1.6), 'HLLC-RD, moving mesh': ('#c0392b', '-', 2.0),
              'AREPO MMFV': ('#376db1', '-.', 1.6), 'SWIFT SPHENIX': ('#2a9d8f', ':', 1.9)}
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(2, 3, figsize=(12.8, 7.2), layout='constrained', sharex=True)
    metrics = {}
    for r, (row, label) in enumerate((('21', '21 hot points'), ('1', '1 hot point'))):
        for c, (field, ylab, exterior) in enumerate((('rho', '$\\rho$', 1.), ('vr', '$v_r$', 0.), ('p', '$p$', 1e-6))):
            ax = axes[r, c]
            for key, s in runs[row].items():
                color, ls, lw = styles[key]
                prof = mass_weighted(s, field)
                ax.plot(MID, prof, color=color, ls=ls, lw=lw, label=key)
                # A non-empty bin between empty bins draws no segment: mark it explicitly.
                finite = np.isfinite(prof)
                isolated = finite & ~np.r_[False, finite[:-1]] & ~np.r_[finite[1:], False]
                ax.plot(MID[isolated], prof[isolated], 'o', color=color, ms=3.2, ls='none')
                if field == 'rho':
                    j = int(np.nanargmax(prof))
                    core = s['r'] < .05
                    metrics[f'{label}/{key}'] = dict(mw_density_peak=float(prof[j]), peak_radius=float(MID[j]),
                        core_mass_weighted_p=float(np.sum(s['mass'][core]*s['p'][core])/np.sum(s['mass'][core])),
                        core_samples=int(core.sum()))
            ax.plot(np.r_[exact['r'], exact['shock'], .45], np.r_[exact[field], exterior, exterior], 'k--', lw=1.1,
                    label='Analytic (point source)')
            ax.set(xlim=(0, .4), ylabel=ylab); ax.grid(alpha=.15)
            if r == 1: ax.set_xlabel('$r$')
            if c == 0: ax.text(.02, .95, label, transform=ax.transAxes, va='top', fontsize=10)
    axes[0, 0].legend(fontsize=8.5, frameon=False, loc='center left')
    fig.savefig(out/'sedov_profiles_mass_weighted.png', dpi=300); fig.savefig(out/'sedov_profiles_mass_weighted.pdf')
    plt.close(fig)
    write(out/'profiles_meta.json', dict(script_sha256=sha(__file__), bins='width .005, 0-.4', metrics=metrics,
        note='Preview only. Mass-weighted means sum(m q)/sum(m); RD at nodes (dual-cell mass), MMFV at cell '
             'centroids (cell mass), SWIFT at particles. t=0.05 for all; single point = particle ID 8256.'))
    print(json.dumps(metrics, indent=1))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('out', type=Path)
    main(p.parse_args().out.resolve())
