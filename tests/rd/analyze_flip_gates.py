#!/usr/bin/env python3
"""Metrics for run_flip_gates.py archives.

Per case: completion, steps, flip-transfer statistics (RD-FLIP lines), the
largest per-step endpoint conservation residual (RD-ALE-FINISH), totals drift
between the first and last snapshots, positivity minima, and per problem:
  uniform*  max |state(t_end) - state(0)| in rho, v, p
  yee*      area-weighted L1 errors against the moved analytic vortex
  sod       L1 density/pressure difference from the same scheme's Campoli run
  kh        E_ky peak and time, entropy excursion (analyze_kh_repair_refresh)
Writes <root>/analysis/metrics.json.
"""
import argparse
import json
from pathlib import Path
import re
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'examples/gresho_2d'))
from run_n_gauss3_split import state, sha, write          # noqa: E402
from analyze_kh_repair_refresh import snapshot as kh_snapshot   # noqa: E402

FLOAT = r'([-+0-9.eE]+|nan|inf)'


def flip_stats(log):
    rows = [dict(kv.split('=', 1) for kv in line.split()[1:]) for line in log.splitlines() if line.startswith('RD-FLIP ')]
    if not rows:
        return None
    cav = np.array([int(r['cavities']) for r in rows])
    theta_mean = np.array([float(r['theta_mean']) for r in rows])
    return dict(steps=len(rows), steps_with_flips=int((cav > 0).sum()), cavities=int(cav.sum()),
                removed=sum(int(r['removed']) for r in rows), limited=sum(int(r['limited']) for r in rows),
                low_only=sum(int(r['low_only']) for r in rows), theta_min=min(float(r['theta_min']) for r in rows),
                theta_mean=float((cav * theta_mean).sum() / max(cav.sum(), 1)),
                max_defect=max(float(r['max_defect']) for r in rows), max_dU=max(float(r['max_dU']) for r in rows),
                max_transfer_rel=max(float(r['transfer_rel']) for r in rows),
                max_outside_dm=max(float(r['outside_dm']) for r in rows))


def finish_stats(log):
    cons = [float(x) for x in re.findall(r'RD-ALE-FINISH .*?endpoint_cons=' + FLOAT, log)]
    return dict(steps=len(cons), max_endpoint_cons=max(cons)) if cons else None


def yee_errors(b):
    xy = (b['xy'] - np.array([5 + b['time'], 5]) + 5) % 10 - 5
    r2 = np.sum(xy * xy, axis=1); temperature = 1 - .4 * 25 / (8 * np.pi ** 2 * 1.4) * np.exp(1 - r2)
    rho = temperature ** 2.5; factor = 2.5 / np.pi * np.exp(.5 * (1 - r2))
    velocity = np.column_stack((1 - xy[:, 1] * factor, xy[:, 0] * factor))
    w = b['w'] / b['w'].sum()
    return dict(rho_l1=float(w @ abs(b['rho'] - rho)), velocity_l1=float(w @ np.linalg.norm(b['v'] - velocity, axis=1)),
                pressure_l1=float(w @ abs(b['p'] - rho ** 1.4)))


def analyze(root, partial):
    campaign = json.loads((root / 'campaign.json').read_text())
    rows, finals = {}, {}
    for c in campaign['cases']:
        folder = root / 'runs' / c['name']
        if not (folder / 'run_status.json').exists():
            assert partial, c['name']
            continue
        status = json.loads((folder / 'run_status.json').read_text())
        meta = json.loads((root / 'artifacts' / c['method'] / 'provenance.json').read_text())
        assert status['binary_sha256'] == meta['binary_sha256']
        assert sha(folder / 'param.txt') == c['param_sha256'] and sha(c['ic']) == c['ic_sha256']
        log = (folder / 'run.log').read_text()
        snaps = sorted((folder / 'output').glob('snap_*.hdf5'))
        ss = [state(p) for p in snaps]
        a, b = ss[0], ss[-1]
        sync = re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*' + FLOAT, log)
        scale = np.array([a['totals'][0], np.sum(a['mass'] * np.abs(a['v'][:, 0])) + 1e-300,
                          np.sum(a['mass'] * np.abs(a['v'][:, 1])) + 1e-300, a['totals'][3]])
        row = dict(name=c['name'], method=c['method'], scheme=c['scheme'], problem=c['problem'],
                   returncode=status['returncode'], seconds=status['seconds'],
                   complete=status['returncode'] == 0 and abs(b['time'] - c['end']) < 1e-9,
                   last_time=b['time'], steps=int(sync[-1][0]) if sync else None,
                   failures=[l for l in log.splitlines() if any(t in l for t in ('TERMINATE', 'RD assertion', 'inadmissible'))][:3],
                   totals_drift=((b['totals'] - a['totals']) / scale).tolist(),
                   rho_min=min(float(s['rho'].min()) for s in ss), p_min=min(float(s['p'].min()) for s in ss),
                   flip=flip_stats(log), finish=finish_stats(log))
        if c['problem'].startswith('uniform'):
            row['state_defect'] = max(float(abs(b[k] - a[k]).max()) for k in ('rho', 'v', 'p'))
        if c['problem'].startswith('yee') and row['complete']:
            row.update(yee_errors(b))
        if c['problem'] == 'kh':
            kh = [kh_snapshot(p) for p in snaps]
            e = np.array([r['eky'] for r in kh]); k = int(np.argmax(e)); s0 = kh[0]['s']; lo, hi = s0.min(), s0.max()
            row.update(eky_peak=float(e[k]), t_peak=kh[k]['t'],
                       entropy_exc_max=float(max(max(0, lo - r['s'].min(), r['s'].max() - hi) for r in kh) / (hi - lo)))
        rows[c['name']] = row; finals[c['name']] = b
    pairs = []
    for name, r in rows.items():
        if not r['method'].endswith(('_flip', '_flip_h1')):
            continue
        control = f"{r['problem']}_{r['scheme']}_campoli"
        if control not in rows:
            continue
        cr = rows[control]; pair = dict(case=name, control=control)
        if r['complete'] and cr['complete']:
            fa, fb = finals[name], finals[control]
            if np.array_equal(fa['id'], fb['id']):
                w = fb['w'] / fb['w'].sum()
                pair.update(rho_l1_diff=float(w @ abs(fa['rho'] - fb['rho'])), p_l1_diff=float(w @ abs(fa['p'] - fb['p'])),
                            v_l1_diff=float(w @ np.linalg.norm(fa['v'] - fb['v'], axis=1)))
        for key in ('rho_l1', 'velocity_l1', 'pressure_l1', 'eky_peak'):
            if key in r and key in cr:
                pair[key + '_change'] = r[key] / cr[key] - 1
        if 't_peak' in r and 't_peak' in cr:
            pair['t_peak_delay'] = r['t_peak'] - cr['t_peak']
        pair['drift_control'] = cr['totals_drift']; pair['drift_flip'] = r['totals_drift']
        pairs.append(pair)
    out = root / 'analysis'; out.mkdir(exist_ok=True)
    write(out / 'metrics.json', dict(cases=list(rows.values()), pairs=pairs))
    return rows, pairs


def table(rows, pairs):
    print(f"{'case':34s} {'ok':>3s} {'steps':>6s} {'cav':>6s} {'lim':>5s} {'thmin':>7s} {'fin_cons':>9s} "
          f"{'dM':>9s} {'dE':>9s} {'extra':s}")
    for r in rows.values():
        f = r['flip'] or {}; fin = r['finish'] or {}
        extra = ''
        if 'state_defect' in r: extra = f"defect={r['state_defect']:.1e}"
        if 'rho_l1' in r: extra = f"rhoL1={r['rho_l1']:.4e} vL1={r['velocity_l1']:.4e}"
        if 'eky_peak' in r: extra = f"Eky_pk={r['eky_peak']:.4e}@{r['t_peak']:.2f} sexc={r['entropy_exc_max']:.2e}"
        print(f"{r['name']:34s} {'Y' if r['complete'] else 'N':>3s} {r['steps'] or 0:6d} {f.get('cavities', 0):6d} "
              f"{f.get('limited', 0):5d} {f.get('theta_min', 1):7.3f} {fin.get('max_endpoint_cons', float('nan')):9.1e} "
              f"{r['totals_drift'][0]:9.1e} {r['totals_drift'][3]:9.1e} {extra}  {'; '.join(r['failures'])[:80]}")
    for p in pairs:
        print(json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in p.items()
                          if k not in ('drift_control', 'drift_flip')}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('root', type=Path)
    p.add_argument('--partial', action='store_true')
    a = p.parse_args()
    table(*analyze(a.root.resolve(), a.partial))
