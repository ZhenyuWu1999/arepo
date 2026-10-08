#!/usr/bin/env python3
"""Verify and compare the edge-HLLC low-order RD Sedov campaign."""
import argparse
import json
import re
from pathlib import Path
import shutil
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
from analyze_swift_default import center, radial, describe
from analyze_mmfv import fv_state, verify_native
from analyze_mmfv_first_order import core_rows
from audit_reference_scales import dense_reference

RUSANOV = REPO.parent/'local_runs/sedov_positivity_20260929_v2'
SWEEP = REPO.parent/'local_runs/sedov_injection_sweep_20260929_v1'
MMFV1 = REPO.parent/'local_runs/sedov_mmfv_first_order_20260930_v1'
MMFV2 = REPO.parent/'local_runs/sedov_mmfv_20260929_v1'
STAGE = re.compile(r'RD-RUSANOV time=(\S+) stage=(\d) rho_min=(\S+) internal_min=(\S+) CFL_max=(\S+) b_min=(\S+)')


def stages(folder):
    rows = [tuple(map(float, m.groups())) for m in STAGE.finditer((folder/'run.log').read_text())]
    a = np.array(rows)
    return dict(count=len(rows), rho_min=float(a[:, 2].min()), internal_min=float(a[:, 3].min()),
                cfl_max=float(a[:, 4].max()), b_min=float(a[:, 5].min()))


def fv_origin(seq):
    s0 = seq[0]; hot = s0['u'] > 2e-6
    return np.average(s0['xy'][hot], axis=0, weights=s0['mass'][hot]*(s0['u'][hot]-1.5e-6))


def main(root):
    out = root/'analysis'; out.mkdir(exist_ok=False)
    for path in (__file__, HERE/'analyze_mmfv.py', HERE/'analyze_mmfv_first_order.py',
                 HERE/'analyze_swift_default.py', HERE/'audit_reference_scales.py'):
        shutil.copy2(path, out/Path(path).name)
    exact = dense_reference(); campaign = json.loads((root/'campaign.json').read_text())
    source = json.loads((root/'source_provenance.json').read_text())
    assert sha(root/'source.tar') == source['source_tar_sha256'] == campaign['source_tar_sha256']
    for c in campaign['cases']:
        assert sha(c['ic']) == c['ic_sha256'] and sha(root/'runs'/c['name']/'param.txt') == c['param_sha256']
        assert sha(c['param_template']) == c['param_template_sha256']
    dual = np.load(root/'inputs/median_dual_area.npy')
    uniform = {}
    for method in campaign['methods']:
        snaps = sorted((root/'runs'/f'uniform_{method}'/'output').glob('snap_*.hdf5'))
        a, b = state(snaps[0]), state(snaps[-1])
        uniform[method] = max(float(np.max(abs(b[k]-a[k]))) for k in ('rho', 'p', 'v'))
        assert uniform[method] < 1e-12

    # Flag-absent regression: every saved state must equal the archived run bitwise.
    new = sorted((root/'runs/nearest21_Rusanov_moving/output').glob('snap_*.hdf5'))
    old = sorted((RUSANOV/'runs/nearest21_Rusanov_moving/output').glob('snap_*.hdf5'))
    assert len(new) == len(old) == 5
    regression = []
    for p, q in zip(new, old):
        a, b = state(p), state(q)
        same = {k: bool(np.array_equal(a[k], b[k])) for k in ('id', 'xy', 'rho', 'p', 'v', 'mass')}
        regression.append(dict(new=str(p), old=str(q), time=a['time'], identical=same))
    regression_ok = all(all(r['identical'].values()) for r in regression)

    runs, meta, origins, stage_checks = {}, {}, {}, {}
    ic21 = root/'inputs/sedov_nearest21.hdf5'; ic1 = root/'inputs/sedov_nearest1.hdf5'
    for key, method, group, ic in (('HLLC moving', 'HLLC_moving', 'nearest21', ic21),
                                   ('HLLC static', 'HLLC_static', 'nearest21', ic21),
                                   ('HLLC moving, 1 hot node', 'HLLC_moving', 'nearest1', ic1)):
        folder = root/'runs'/f'{group}_{method}'
        runs[key], meta[key] = verify_native(root, method, folder, state)
        origins[key] = center(ic, dual); stage_checks[key] = stages(folder)
    for key, archive, method, folder, ic in (
            ('Rusanov moving', RUSANOV, 'Rusanov_moving', RUSANOV/'runs/nearest21_Rusanov_moving', ic21),
            ('Rusanov static', RUSANOV, 'Rusanov_static', RUSANOV/'runs/nearest21_Rusanov_static', ic21),
            ('Rusanov moving, 1 hot node', SWEEP, 'Rusanov_moving', SWEEP/'runs/nearest1_Rusanov_moving', ic1)):
        runs[key], meta[key] = verify_native(archive, method, folder, state)
        origins[key] = center(ic, dual)
    for key, archive, method, folder in (('MMFV 1st order', MMFV1, 'MMFV_1st_exact', MMFV1/'runs/nearest21_MMFV_1st_exact'),
                                         ('MMFV 2nd order', MMFV2, 'MMFV_moving', MMFV2/'runs/nearest21')):
        runs[key], meta[key] = verify_native(archive, method, folder, fv_state)
        origins[key] = fv_origin(runs[key])

    final, metrics = {}, {}
    for key, seq in runs.items():
        s = radial(seq[-1], origins[key]); final[key] = s
        m = describe(s, seq[0], exact); m['core'] = core_rows(s)
        means, edges, _ = binned_statistic(s['r'], s['rho'], statistic='mean', bins=np.arange(0, .4001, .005))
        j = int(np.nanargmax(means)); m['binned_density_peak'] = float(means[j])
        m['binned_peak_radius'] = float((edges[j]+edges[j+1])/2)
        m['history'] = [[a['time'], *a['totals'].tolist()] for a in seq]
        metrics[key] = m
    write(out/'verification.json', dict(metrics=metrics, metadata=meta, stage_checks=stage_checks,
        uniform_defects=uniform, regression_identical=regression_ok, regression=regression,
        source_provenance=source, analysis_sha256=sha(__file__), analytic_shock_radius=exact['shock'],
        method='RD at nodes, FV at cell centroids; radius from each initial injected-excess-energy centroid; '
               'core density = sample mass / sample area inside r.'))

    styles = [('HLLC moving', '#c0392b', '-'), ('HLLC static', '#e59866', '--'),
              ('Rusanov moving', '#7f8c8d', '-.'), ('MMFV 1st order', '#2a9d8f', ':'),
              ('MMFV 2nd order', '#376db1', '-')]
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    for filename, keys, title in (
            ('hllc_nearest21_profiles', styles, '21 heated points'),
            ('hllc_nearest1_profiles', [('HLLC moving, 1 hot node', '#c0392b', '-'),
                                        ('Rusanov moving, 1 hot node', '#7f8c8d', '-.'),
                                        ('HLLC moving', '#f1948a', ':')], '1 heated point (21-point HLLC dotted)')):
        fig, axes = plt.subplots(2, 3, figsize=(12.8, 7.1), layout='constrained')
        for row, rmax in enumerate((.4, .15)):
            bins = np.arange(0, rmax+.0001, .005); mid = (bins[1:]+bins[:-1])/2
            for ax, field, label, exterior in zip(axes[row], ('rho', 'vr', 'p'), ('$\\rho$', '$v_r$', '$p$'), (1., 0., 1e-6)):
                for key, color, ls in keys:
                    s = final[key]; take = s['r'] < rmax
                    ax.scatter(s['r'][take], s[field][take], s=2 if row == 0 else 7,
                               alpha=.03 if row == 0 else .15, color=color, rasterized=True)
                    mean = binned_statistic(s['r'], s[field], statistic='mean', bins=bins)[0]
                    ax.plot(mid, mean, color=color, ls=ls, lw=1.6, label=key)
                ax.plot(np.r_[exact['r'], exact['shock'], .45], np.r_[exact[field], exterior, exterior], 'k--', lw=1.2,
                        label='2D Sedov')
                values = np.concatenate([final[k][field][final[k]['r'] < rmax] for k, _, _ in keys])
                lo = min(0., float(values.min())); hi = max(float(values.max()), float(np.max(exact[field][exact['r'] < rmax])))
                pad = (hi-lo)*.06
                ax.set(xlim=(0, rmax), ylim=(lo-pad, hi+pad), xlabel='Radius from injection centroid', ylabel=label)
                ax.grid(alpha=.15)
        axes[0, 0].legend(fontsize=8)
        fig.suptitle(f'Sedov blast, glass $128^2$, {title}, $t=0.05$\nEdge-HLLC low-order RD; lower row: core detail')
        fig.savefig(out/f'{filename}.png', dpi=300); fig.savefig(out/f'{filename}.pdf'); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), layout='constrained')
    for key, color, ls in styles[:3] + [('HLLC moving, 1 hot node', '#922b21', '--')]:
        a = np.array(metrics[key]['history'])
        for ax, col in zip(axes, (1, 4)):
            ax.plot(a[:, 0], 100*(a[:, col]/a[0, col]-1), color=color, ls=ls, marker='o', ms=3, label=key)
    for ax, label in zip(axes, ('Mass change [%]', 'Energy change [%]')):
        ax.set(xlim=(0, .05), xlabel='Time', ylabel=label); ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    fig.suptitle('Budgets relative to the saved initial state')
    fig.savefig(out/'hllc_budgets.png', dpi=300); plt.close(fig)

    summary = {k: dict(rho_min=v['density_min'], rho_max=v['density_max'], mean_peak=v['binned_density_peak'],
                       peak_r=v['binned_peak_radius'], dM=v['mass_relative'], dE=v['energy_relative'],
                       core05=v['core']['0.05']['mean_density_by_area'], n05=v['core']['0.05']['count'],
                       core10=v['core']['0.1']['mean_density_by_area'],
                       p_core=v['annuli'][0]['p'], p_core_exact=v['annuli'][0]['p_analytic']) for k, v in metrics.items()}
    print(json.dumps(dict(summary=summary, stages=stage_checks, uniform=uniform, regression_identical=regression_ok), indent=1))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('root', type=Path)
    main(p.parse_args().root.resolve())
