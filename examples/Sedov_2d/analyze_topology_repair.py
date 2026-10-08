#!/usr/bin/env python3
"""Compare archived Rusanov Sedov budgets with the unlimited topology repair.

Reports failed repair states separately from accepted hydrodynamic stages.
The square-flip example is an algebra audit, not a native positivity limiter.
"""
import argparse
import json
from pathlib import Path
import re
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tests/rd'))
from run_n_gauss3_split import sha, state, write


def audit(root, method):
    campaign = json.loads((root / 'campaign.json').read_text())
    artifact = root / 'artifacts' / method
    provenance = json.loads((artifact / 'provenance.json').read_text())
    assert sha(artifact / 'Arepo') == provenance['binary_sha256']
    assert sha(artifact / 'Config.sh') == provenance['config_sha256']
    source_tar = root / 'sources' / method / 'source.tar'
    if not source_tar.exists():
        source_tar = root / 'source.tar'
    assert sha(source_tar) == provenance['source_tar_sha256']
    rows, histories = [], {}
    for c in campaign['cases']:
        if c['method'] != method:
            continue
        folder = root / 'runs' / c['name']
        status = json.loads((folder / 'run_status.json').read_text())
        assert sha(c['ic']) == c['ic_sha256']
        assert sha(folder / 'param.txt') == c['param_sha256']
        log = (folder / 'run.log').read_text(errors='replace')
        snapshots = sorted((folder / 'output').glob('snap_*.hdf5'))
        initial = state(snapshots[0])
        snap_rows = []
        for path in snapshots:
            s = state(path)
            assert np.array_equal(initial['id'], s['id'])
            assert all(np.all(np.isfinite(s[k])) for k in ('rho', 'p', 'v', 'mass', 'xy'))
            assert all(np.all(s[k] > 0) for k in ('rho', 'p', 'mass'))
            snap_rows.append(dict(path=str(path), sha256=sha(path), time=s['time'],
                rho_min=float(s['rho'].min()), rho_max=float(s['rho'].max()),
                p_min=float(s['p'].min()), totals=s['totals'].tolist()))
        stages = np.array([[float(x) for x in m] for m in re.findall(
            r'RD-RUSANOV time=(\S+) stage=(\d) rho_min=(\S+) internal_min=(\S+) CFL_max=(\S+) b_min=(\S+)', log)])
        assert len(stages) and np.all(np.isfinite(stages))
        assert np.all(stages[:, 2:4] > 0) and np.all(stages[:, 4] <= 1)
        assert np.all((stages[:, 5] > 0) & (stages[:, 5] <= 1))
        history = [[0., *initial['totals']]]
        for m in re.finditer(r'RD-ALE-FINISH time=(\S+).*? totals=\[([^\]]+)\]', log):
            history.append([float(m[1]), *map(float, m[2].split(','))])
        h = np.array(history)
        histories[c['group']] = h
        repaired = np.array([[float(x) for x in m.split()] for m in re.findall(r' repaired=\[([^\]]+)\]', log)])
        nonzero = [line for line in log.splitlines() if line.startswith('RD-TOPO-REPAIR') and 'affected=0 ' not in line]
        row = dict(name=c['name'], group=c['group'], method=method,
            returncode=status['returncode'], seconds=status['seconds'],
            completed=status['returncode'] == 0 and abs(s['time'] - c['end']) < 1e-12,
            last_accepted_time=float(h[-1, 0]), accepted_steps=len(h) - 1,
            mass_relative=float(h[-1, 1] / h[0, 1] - 1),
            energy_relative=float(h[-1, 4] / h[0, 4] - 1),
            stages=len(stages), stage_rho_min=float(stages[:, 2].min()),
            stage_internal_min=float(stages[:, 3].min()), CFL_max=float(stages[:, 4].max()),
            b_min=float(stages[:, 5].min()), successful_nonzero_repair_steps=len(nonzero),
            max_reported_repair_defect=float(np.max(abs(repaired))) if repaired.size else None,
            failed_repair_states=[line for line in log.splitlines() if line.startswith('RD-TOPO-BAD')],
            termination=[line for line in log.splitlines() if 'TERMINATE:' in line], snapshots=snap_rows)
        if c['group'] == 'uniform':
            row['uniform_error'] = max(float(np.max(abs(s[k] - initial[k]))) for k in ('rho', 'p', 'v'))
            assert row['uniform_error'] < 1e-12
        rows.append(row)
    return rows, histories


def square_flip():
    # Unit square, old diagonal (0,2), new diagonal (1,3), no exterior area.
    old = np.array([2., 1., 2., 1.]) / 6
    new = np.array([1., 2., 1., 2.]) / 6
    u = np.zeros((4, 4)); u[:, 0] = 1.; u[:, 3] = 1e-6
    u[1, 3] = 100.
    q0 = old[:, None] * u
    defect = ((new - old)[:, None] * u).sum(axis=0)
    high = u - defect / new.sum()
    mean = q0.sum(axis=0) / new.sum()
    low = np.tile(mean, (4, 1))
    for candidate in (high, low):
        assert np.max(abs((new[:, None] * candidate).sum(axis=0) - q0.sum(axis=0))) < 1e-13
    assert high[:, 3].min() < 0 and low[:, 3].min() > 0
    return dict(old_area=old.tolist(), new_area=new.tolist(), old_U=u.tolist(),
        high_U=high.tolist(), low_patch_mean_U=low.tolist(),
        meaning='An actual square diagonal flip: the existing conservative high map makes cold-node internal energy negative; a patch-mean low map is positive but diffusive. No native limiter implemented.')


def main(root, baseline):
    out = root / 'analysis'; out.mkdir(exist_ok=True)
    rows, repaired = audit(root, 'Rusanov_moving_repair')
    base_rows, original = audit(baseline, 'Rusanov_moving')
    matched = {}
    for group in ('nearest21', 'disk005'):
        a = {float(h[0]): h for h in original[group]}
        b = {float(h[0]): h for h in repaired[group]}
        t = max(a.keys() & b.keys())
        matched[group] = dict(time=t,
            no_repair_mass_relative=float(a[t][1] / original[group][0, 1] - 1),
            repair_mass_relative=float(b[t][1] / repaired[group][0, 1] - 1),
            no_repair_energy_relative=float(a[t][4] / original[group][0, 4] - 1),
            repair_energy_relative=float(b[t][4] / repaired[group][0, 4] - 1))
    write(out / 'verification.json', dict(repair=rows, baseline=base_rows,
        matched_endpoint=matched, square_flip=square_flip(), analyzer_sha256=sha(Path(__file__))))
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.5), layout='constrained')
    for col, group in enumerate(('nearest21', 'disk005')):
        for history, label, color in ((original[group], 'No repair', '#d38532'),
                                      (repaired[group], 'Original repair + consistent predictor', '#267eb0')):
            for row, k in enumerate((1, 4)):
                drift = 100 * (history[:, k] / history[0, k] - 1)
                axes[row, col].plot(history[:, 0], drift, label=label, color=color, lw=1.5)
        result = next(r for r in rows if r['group'] == group)
        if not result['completed']:
            for row in range(2):
                axes[row, col].axvline(result['last_accepted_time'], color='#267eb0', ls=':', lw=1)
            axes[0, col].text(.04, .94, 'Repair run terminated early', transform=axes[0, col].transAxes,
                              va='top', color='#267eb0')
        axes[0, col].set_title('21 heated nodes' if group == 'nearest21' else '130 heated nodes')
        for row, field in enumerate(('Mass', 'Energy')):
            axes[row, col].set(xlabel='Time', ylabel=f'{field} change (%)')
            axes[row, col].grid(alpha=.15)
    axes[1, 0].legend(fontsize=8)
    fig.suptitle('Moving Sedov, Rusanov RD, glass $128^2$; topology repair control')
    fig.savefig(out / 'conservation_comparison.png', dpi=250)
    plt.close(fig)
    for row in rows:
        print({k: row[k] for k in ('name', 'completed', 'last_accepted_time', 'mass_relative', 'energy_relative', 'failed_repair_states')})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path); p.add_argument('baseline', type=Path)
    a = p.parse_args(); main(a.root.resolve(), a.baseline.resolve())
