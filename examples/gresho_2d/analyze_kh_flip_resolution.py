#!/usr/bin/env python3
"""Analysis of run_kh_flip_resolution.py archives (KH glass48 vs glass96).

For each resolution and method: E_ky(t) peak and time, mass/energy drift,
entropy excursion (analyze_kh_repair_refresh.series).  The convergence test of
the flip transfer: mass-weighted rho, v_y and p binned on a common 32x32 grid,
and the L1 grid difference between each method and the Campoli run (same
resolution, no topology treatment) at t = 1, 2, 3.  If the transfer is an
O(h^2) perturbation, the glass96 differences are about 4 times smaller.
Writes <root>/analysis/metrics.json and kh_flip_resolution.png.
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
sys.path.insert(0, str(HERE))
from analyze_kh_repair_refresh import series   # noqa: E402

NG = 32
TIMES = (1.0, 2.0, 3.0)


def gridded(path):
    with h5py.File(path) as f:
        g = f['PartType0']; x = g['Coordinates'][:, :2] % 1.0; m = g['Masses'][:]
        rho = g['Density'][:]; vy = g['Velocities'][:, 1]; p = g['Pressure'][:]; t = float(f['Header'].attrs['Time'])
    ix = np.minimum((x * NG).astype(int), NG - 1); k = ix[:, 0] * NG + ix[:, 1]
    mass = np.bincount(k, m, NG * NG)
    out = {name: np.bincount(k, m * q, NG * NG) / np.maximum(mass, 1e-300) for name, q in (('rho', rho), ('vy', vy), ('p', p))}
    return t, out


def snapshot_at(folder, t):
    """Nearest snapshot within 0.01 (output times sit on the integer timeline)."""
    best, gap = None, 0.01
    for path in sorted((folder / 'output').glob('snap_*.hdf5')):
        with h5py.File(path) as f:
            d = abs(float(f['Header'].attrs['Time']) - t)
        if d < gap:
            best, gap = path, d
    return best


def main(root):
    root = root.resolve(); out = root / 'analysis'; out.mkdir(exist_ok=True)
    campaign = json.loads((root / 'campaign.json').read_text())
    done = {c['name']: c for c in campaign['cases']
            if (root / 'runs' / c['name'] / 'run_status.json').exists()
            and json.loads((root / 'runs' / c['name'] / 'run_status.json').read_text())['returncode'] == 0}
    metrics = {}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), layout='constrained', sharey=True)
    for name, c in done.items():
        rows = series(root / 'runs' / name)
        t = np.array([r['t'] for r in rows]); e = np.array([r['eky'] for r in rows]); k = int(np.argmax(e))
        metrics[name] = dict(n=c['n'], method=c['method'], eky_peak=float(e[k]), t_peak=float(t[k]),
                             mass_drift=rows[-1]['mass'] / rows[0]['mass'] - 1,
                             energy_drift=rows[-1]['energy'] / rows[0]['energy'] - 1,
                             entropy_exc_max=max(r['entropy_exc'] for r in rows))
        axes[0 if c['n'] == 48 else 1].plot(t, e, label=c['method'])
        control = f"kh{c['n']}_campoli"
        if c['method'] != 'campoli' and control in done:
            diffs = {}
            for tt in TIMES:
                a, b = snapshot_at(root / 'runs' / name, tt), snapshot_at(root / 'runs' / control, tt)
                if a is None or b is None:
                    continue
                _, ga = gridded(a); _, gb = gridded(b)
                diffs[str(tt)] = {q: float(np.mean(np.abs(ga[q] - gb[q]))) for q in ga}
            metrics[name]['diff_vs_campoli'] = diffs
    for ax, n in zip(axes, (48, 96)):
        ax.set(title=f'KH glass{n}', xlabel='t', ylabel=r'$E_{k,y}$'); ax.legend(frameon=False); ax.grid(alpha=.2)
    fig.savefig(out / 'kh_flip_resolution.png', dpi=150)
    ratios = {}
    for method in ('arpaia', 'flip', 'flip_h1'):
        a, b = metrics.get(f'kh48_{method}', {}), metrics.get(f'kh96_{method}', {})
        if 'diff_vs_campoli' in a and 'diff_vs_campoli' in b:
            ratios[method] = {tt: {q: a['diff_vs_campoli'][tt][q] / max(b['diff_vs_campoli'][tt][q], 1e-300)
                                   for q in a['diff_vs_campoli'][tt]}
                              for tt in a['diff_vs_campoli'] if tt in b['diff_vs_campoli']}
    result = dict(cases=metrics, ratio_48_over_96=ratios)
    (out / 'metrics.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=1))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('root', type=Path)
    main(p.parse_args().root)
