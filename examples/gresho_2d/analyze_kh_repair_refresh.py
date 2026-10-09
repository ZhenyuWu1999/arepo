#!/usr/bin/env python3
"""Metrics for run_kh_repair_refresh.py archives (definitions of log2 §71.4).

E_ky = 1/2 sum_i m_i v_y,i^2; sigma_rho = unweighted nodal density std;
entropy excursion = max distance of s = p/rho^gamma outside its initial range,
divided by that range; mass/energy drift relative to the first snapshot.
Writes metrics.json and kh_repair_refresh.png into <root>/analysis/.
"""
import argparse
import json
from pathlib import Path
import h5py
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

GAMMA = 1.4


def snapshot(path):
    with h5py.File(path) as f:
        g = f['PartType0']; t = float(f['Header'].attrs['Time'])
        m = g['Masses'][:]; v = g['Velocities'][:, :2]; rho = g['Density'][:]; p = g['Pressure'][:]
        vol = g['Volume'][:] if 'Volume' in g else m / rho
        e_int = g['InternalEnergy'][:]
    return dict(t=t, eky=.5 * np.sum(m * v[:, 1] ** 2), sig=float(np.std(rho)), s=p / rho ** GAMMA,
                mass=float(m.sum()), energy=float(np.sum(m * (e_int + .5 * (v ** 2).sum(1)))),
                rho_min=float(rho.min()), p_min=float(p.min()))


def series(folder):
    snaps = sorted((folder / 'output').glob('snap_*.hdf5'))
    rows = [snapshot(s) for s in snaps]
    s0 = rows[0]['s']; lo, hi = s0.min(), s0.max(); width = hi - lo
    for r in rows:
        r['entropy_exc'] = float(max(0.0, lo - r['s'].min(), r['s'].max() - hi) / width)
        del r['s']
    return rows


def main(root):
    root = root.resolve(); out = root / 'analysis'; out.mkdir(exist_ok=True)
    data = {m: series(root / 'runs' / m) for m in ('control', 'stale', 'refresh')
            if (root / 'runs' / m / 'output').exists()}
    metrics = {}
    for m, rows in data.items():
        t = np.array([r['t'] for r in rows]); e = np.array([r['eky'] for r in rows]); k = int(np.argmax(e))
        metrics[m] = dict(t_end=float(t[-1]), eky_peak=float(e[k]), t_peak=float(t[k]),
                          mass_drift=rows[-1]['mass'] / rows[0]['mass'] - 1, energy_drift=rows[-1]['energy'] / rows[0]['energy'] - 1,
                          entropy_exc_t2=next((r['entropy_exc'] for r in rows if abs(r['t'] - 2) < 1e-3), None),
                          entropy_exc_max=max(r['entropy_exc'] for r in rows),
                          rho_min=min(r['rho_min'] for r in rows), p_min=min(r['p_min'] for r in rows))
    if 'control' in metrics:
        c = metrics['control']
        for m in metrics:
            metrics[m]['peak_change_vs_control'] = metrics[m]['eky_peak'] / c['eky_peak'] - 1
            metrics[m]['peak_delay_vs_control'] = metrics[m]['t_peak'] - c['t_peak']
    (out / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.6), layout='constrained')
    for m, rows in data.items():
        t = [r['t'] for r in rows]
        ax[0].plot(t, [r['eky'] for r in rows], label=m)
        ax[1].plot(t, [r['sig'] for r in rows], label=m)
        ax[2].plot(t, [r['entropy_exc'] for r in rows], label=m)
    for a, lab in zip(ax, (r'$E_{k,y}$', r'$\sigma_\rho$', 'entropy excursion')):
        a.set(xlabel='t', ylabel=lab); a.grid(alpha=.2)
    ax[0].legend(frameon=False)
    fig.savefig(out / 'kh_repair_refresh.png', dpi=150)
    print(json.dumps(metrics, indent=1))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('root', type=Path)
    main(p.parse_args().root)
