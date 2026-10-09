#!/usr/bin/env python3
"""Metrics for run_interval_hierarchy_gates.py archives.

Per case: completion, run time, totals drift (first to last snapshot), and
  uniform_random  max |state(t_end) - state(0)|
  yee48, yee96    area-weighted L1 errors against the moved analytic vortex
  kh48            E_ky peak, its time, entropy excursion (analyze_kh_repair_refresh)
  sedov21, sedov1 density peak and its radius, mass-weighted shock radius of
                  the shell (rho > 1.5), positivity minima
Hierarchy runs also report their RD-IHIER event statistics: events, flip
cavities, forced and non-dyadic closures, the worst common-closure
conservation, the CFL ledger, and the element work relative to all-fine
stepping (events x triangles).  Each ih_* case is compared with the ref_flip
case of the same scheme and problem.  Writes <root>/analysis/metrics.json.
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
from analyze_flip_gates import yee_errors, flip_stats       # noqa: E402
from analyze_kh_repair_refresh import snapshot as kh_snapshot   # noqa: E402

FLOAT = r'([-+0-9.eE]+|nan|inf)'


def hierarchy_stats(log):
    rows = [dict(kv.split('=', 1) for kv in line.split()[2:] if '=' in kv)
            for line in log.splitlines() if line.startswith('RD-IHIER ') and 'stage=event' in line]
    if not rows:
        return None
    cons = [float(r['cons']) for r in rows if r['cons'] != 'nan']
    work = [int(x) for x in rows[-1]['work'].strip('[]').split(',')]
    triangles = int(rows[-1]['triangles'])
    return dict(events=len(rows), common_closures=len(cons), max_common_cons=max(cons) if cons else None,
                cavities=sum(int(r['cavities']) for r in rows), limited=sum(int(r['limited']) for r in rows),
                theta_min=min(float(r['theta_min']) for r in rows), forced=work[1], nondyadic=work[2],
                element_updates=work[0], work_fraction=work[0] / (len(rows) * triangles),
                forced_refresh=sum(int(r['forced_refresh']) for r in rows),
                max_ledger=max(float(r['max_ledger']) for r in rows),
                cfl_ledger_max=max((float(r['cfl_ledger_max']) for r in rows if 'cfl_ledger_max' in r), default=None),
                cfl_ledger_over=sum(int(r.get('cfl_ledger_over', 0)) for r in rows))


def sedov_metrics(b):
    r = np.hypot(*(b['xy'] - .5).T); k = int(np.argmax(b['rho'])); shell = b['rho'] > 1.5
    return dict(rho_peak=float(b['rho'][k]), r_peak=float(r[k]),
                r_shell=float(np.sum(b['mass'][shell] * r[shell]) / np.sum(b['mass'][shell])) if shell.any() else None)


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
        scale = np.array([a['totals'][0], np.sum(a['mass'] * np.abs(a['v'][:, 0])) + 1e-300,
                          np.sum(a['mass'] * np.abs(a['v'][:, 1])) + 1e-300, a['totals'][3]])
        sync = re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*' + FLOAT, log)
        row = dict(name=c['name'], method=c['method'], scheme=c['scheme'], variant=c['variant'], problem=c['problem'],
                   returncode=status['returncode'], seconds=status['seconds'],
                   complete=status['returncode'] == 0 and abs(b['time'] - c['end']) < 1e-9, last_time=b['time'],
                   sync_points=int(sync[-1][0]) if sync else None,
                   failures=[l for l in log.splitlines() if 'TERMINATE' in l][:2],
                   totals_drift=((b['totals'] - a['totals']) / scale).tolist(),
                   rho_min=min(float(s['rho'].min()) for s in ss), p_min=min(float(s['p'].min()) for s in ss),
                   hierarchy=hierarchy_stats(log), flip=flip_stats(log))
        if c['problem'] == 'uniform_random':
            row['state_defect'] = max(float(abs(b[k] - a[k]).max()) for k in ('rho', 'v', 'p'))
        if c['problem'].startswith('yee') and row['complete']:
            row.update(yee_errors(b))
        if c['problem'] == 'kh48' and row['complete']:
            kh = [kh_snapshot(p) for p in snaps]
            e = np.array([r['eky'] for r in kh]); k = int(np.argmax(e)); s0 = kh[0]['s']; lo, hi = s0.min(), s0.max()
            row.update(eky_peak=float(e[k]), t_peak=kh[k]['t'],
                       entropy_exc_max=float(max(max(0, lo - r['s'].min(), r['s'].max() - hi) for r in kh) / (hi - lo)))
        if c['problem'].startswith('sedov') and row['complete']:
            row.update(sedov_metrics(b))
        rows[c['name']] = row; finals[c['name']] = b
    pairs = []
    for name, r in rows.items():
        if not r['variant'].startswith('ih_'):
            continue
        ref = f"{r['problem']}_{r['scheme']}_ref_flip"
        if ref not in rows or not (r['complete'] and rows[ref]['complete']):
            continue
        pair = dict(case=name, reference=ref, seconds_ratio=r['seconds'] / rows[ref]['seconds'])
        for key in ('rho_l1', 'velocity_l1', 'pressure_l1', 'eky_peak', 'rho_peak', 'r_shell'):
            if key in r and key in rows[ref] and r[key] is not None and rows[ref][key]:
                pair[key + '_change'] = r[key] / rows[ref][key] - 1
        fa, fb = finals[name], finals[ref]
        if np.array_equal(fa['id'], fb['id']):
            w = fb['w'] / fb['w'].sum()
            pair['rho_l1_diff'] = float(w @ abs(fa['rho'] - fb['rho']))
        pairs.append(pair)
    out = root / 'analysis'; out.mkdir(exist_ok=True)
    write(out / 'metrics.json', dict(cases=list(rows.values()), pairs=pairs))
    return rows, pairs


def table(rows, pairs):
    for r in rows.values():
        h = r['hierarchy'] or {}
        extra = ''
        if 'state_defect' in r: extra = f"defect={r['state_defect']:.1e}"
        if 'rho_l1' in r: extra = f"rhoL1={r['rho_l1']:.4e} vL1={r['velocity_l1']:.4e}"
        if 'eky_peak' in r: extra = f"Eky={r['eky_peak']:.4e}@{r['t_peak']:.2f}"
        if 'rho_peak' in r: extra = f"peak={r['rho_peak']:.3f}@{r['r_peak']:.4f} r_shell={r['r_shell']:.4f} pmin={r['p_min']:.2g}"
        hs = (f"ev={h['events']} cav={h['cavities']} forced={h['forced']} work={h['work_fraction']:.3f} "
              f"cons={h['max_common_cons']:.1e}" if h else '')
        print(f"{r['name']:34s} {'Y' if r['complete'] else 'N'} {r['seconds']:7.0f}s dM={r['totals_drift'][0]:+.1e} "
              f"dE={r['totals_drift'][3]:+.1e} {extra} {hs} {'; '.join(r['failures'])[:60]}")
    for p in pairs:
        print(json.dumps({k: (round(v, 5) if isinstance(v, float) else v) for k, v in p.items()}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('root', type=Path)
    p.add_argument('--partial', action='store_true')
    a = p.parse_args()
    table(*analyze(a.root.resolve(), a.partial))
