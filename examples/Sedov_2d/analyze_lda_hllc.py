#!/usr/bin/env python3
"""Verify and compare the moving LDA/HLLC blend Sedov campaign."""
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

HLLC = REPO.parent/'local_runs/sedov_hllc_20260930_v1'
MMFV1 = REPO.parent/'local_runs/sedov_mmfv_first_order_20260930_v1'
MMFV2 = REPO.parent/'local_runs/sedov_mmfv_20260929_v1'
BLEND = REPO.parent/'local_runs/sedov_lda_rusanov_20260929_v1'
LR = re.compile(r'RD-LR time=(\S+) stage=(\d) elements=(\d+) limited=(\d+) ell_mean=(\S+) ell_min=(\S+) '
                r'correction_norm=(\S+) accepted_norm=(\S+) rho_min=(\S+) internal_min=(\S+) CFL_max=(\S+) budget_defect=(\S+)')
LRH = re.compile(r'RD-LR-HLLC time=(\S+) stage=(\d) b_min=(\S+)')
GAMMA = 5/3


def limiter_stats(folder):
    # Include a restart segment (TimeLimitCPU resume) when present.
    text = ''.join((folder/name).read_text() for name in ('run.log', 'run_resume.log') if (folder/name).exists())
    a = np.array([[float(x) for x in m.groups()] for m in LR.finditer(text)])
    b = np.array([float(m.group(3)) for m in LRH.finditer(text)])
    out = dict(stages=len(a), budget_defect_max=float(a[:, 11].max()), cfl_max=float(a[:, 10].max()),
               rho_min=float(a[:, 8].min()), internal_min=float(a[:, 9].min()), b_min=float(b.min()) if len(b) else None)
    for stage in (0, 1):
        s = a[a[:, 1] == stage]
        out[f'stage{stage}'] = dict(limited_fraction_mean=float(np.mean(s[:, 3]/s[:, 2])),
                                    limited_fraction_last=float(s[-1, 3]/s[-1, 2]), ell_mean=float(np.mean(s[:, 4])),
                                    accepted_over_correction=float(np.sum(s[:, 7])/max(np.sum(s[:, 6]), 1e-300)))
    return out


def roughness(s, t0_min_k=1e-6):
    """Angular/velocity noise and front undershoot diagnostics on one final state."""
    d = s['xy'] - s['center']; d = (d+.5) % 1-.5; r = np.linalg.norm(d, axis=1)
    er = d/np.maximum(r, 1e-30)[:, None]; vt = er[:, 0]*s['v'][:, 1]-er[:, 1]*s['v'][:, 0]
    w = s['w']; out = {}
    for lo, hi in ((.05, .15), (.15, .22), (.05, .22)):
        m = (r >= lo) & (r < hi)
        if m.sum() < 6:
            out[f'{lo:g}:{hi:g}'] = dict(n=int(m.sum())); continue
        x = r[m]-r[m].mean(); A = np.column_stack((np.ones(m.sum()), x, x*x))
        beta = np.linalg.lstsq(A*np.sqrt(w[m, None]), s['vr'][m]*np.sqrt(w[m]), rcond=None)[0]
        res = s['vr'][m]-A@beta
        out[f'{lo:g}:{hi:g}'] = dict(n=int(m.sum()), vr_detrended_rms=float(np.sqrt(np.average(res**2, weights=w[m]))),
                                     vt_rms=float(np.sqrt(np.average(vt[m]**2, weights=w[m]))))
    ahead = r > .27
    means = binned_statistic(r, s['rho'], statistic='mean', bins=np.arange(.26, .3601, .005))[0]
    k = s['p']/s['rho']**GAMMA
    out['ahead_min_binned_rho'] = float(np.nanmin(means))
    out['ahead_fraction_rho_below_0.95'] = float(np.mean(s['rho'][ahead] < .95))
    out['K_below_initial_min'] = int(np.sum(k < t0_min_k*(1-1e-8)))
    out['K_min_over_initial'] = float(k.min()/t0_min_k)
    return out


def main(root, outname='analysis', skip=()):
    out = root/outname; out.mkdir(exist_ok=False)
    for path in (__file__, HERE/'analyze_mmfv.py', HERE/'analyze_mmfv_first_order.py',
                 HERE/'analyze_swift_default.py', HERE/'audit_reference_scales.py'):
        shutil.copy2(path, out/Path(path).name)
    exact = dense_reference(); campaign = json.loads((root/'campaign.json').read_text())
    source = json.loads((root/'source_provenance.json').read_text())
    assert sha(root/'source.tar') == source['source_tar_sha256'] == campaign['source_tar_sha256']
    for c in campaign['cases']:
        assert sha(c['ic']) == c['ic_sha256'] and sha(root/'runs'/c['name']/'param.txt') == c['param_sha256']
        assert sha(c['param_template']) == c['param_template_sha256']
    uniform = {}
    for method in campaign['methods']:
        snaps = sorted((root/'runs'/f'uniform_{method}'/'output').glob('snap_*.hdf5'))
        a, b = state(snaps[0]), state(snaps[-1])
        uniform[method] = max(float(np.max(abs(b[k]-a[k]))) for k in ('rho', 'p', 'v'))
        assert uniform[method] < 1e-12

    # Static LDA/Rusanov blend replay: bitwise against the archive.
    new = sorted((root/'runs/contact16_LR_blend_static/output').glob('snap_*.hdf5'))
    old = sorted((BLEND/'runs/contact16_LR_blend/output').glob('snap_*.hdf5'))
    assert len(new) == len(old) and len(new) > 0
    static_regression = [dict(time=state(p)['time'], identical={k: bool(np.array_equal(state(p)[k], state(q)[k]))
                         for k in ('id', 'xy', 'rho', 'p', 'v', 'mass')}) for p, q in zip(new, old)]

    dual = np.load(root/'inputs/median_dual_area.npy')
    ic21 = root/'inputs/sedov_nearest21.hdf5'; ic1 = root/'inputs/sedov_nearest1.hdf5'
    runs, meta, origins, stats = {}, {}, {}, {}
    for key, method, group, ic in (('LDA/HLLC bounds', 'LDAHLLC_bounds', 'nearest21', ic21),
                                   ('LDA/HLLC positivity', 'LDAHLLC_pos', 'nearest21', ic21),
                                   ('LDA/HLLC low (ell=0)', 'LDAHLLC_low', 'nearest21', ic21),
                                   ('LDA/HLLC bounds, 1 hot node', 'LDAHLLC_bounds', 'nearest1', ic1),
                                   ('LDA/HLLC positivity, 1 hot node', 'LDAHLLC_pos', 'nearest1', ic1)):
        folder = root/'runs'/f'{group}_{method}'
        if key in skip:
            meta[key] = dict(skipped=True); continue
        if json.loads((folder/'run_status.json').read_text())['returncode'] != 0:
            meta[key] = dict(failed=True, log_tail=(folder/'run.log').read_text()[-2000:]); continue
        runs[key], meta[key] = verify_native(root, method, folder, state)
        origins[key] = center(ic, dual); stats[key] = limiter_stats(folder)
    for key, archive, method, folder, ic in (
            ('HLLC moving', HLLC, 'HLLC_moving', HLLC/'runs/nearest21_HLLC_moving', ic21),
            ('HLLC moving, 1 hot node', HLLC, 'HLLC_moving', HLLC/'runs/nearest1_HLLC_moving', ic1)):
        runs[key], meta[key] = verify_native(archive, method, folder, state)
        origins[key] = center(ic, dual)
    for key, archive, method, folder in (('MMFV 1st order', MMFV1, 'MMFV_1st_exact', MMFV1/'runs/nearest21_MMFV_1st_exact'),
                                         ('MMFV 2nd order', MMFV2, 'MMFV_moving', MMFV2/'runs/nearest21')):
        runs[key], meta[key] = verify_native(archive, method, folder, fv_state)
        s0 = runs[key][0]; hot = s0['u'] > 2e-6
        origins[key] = np.average(s0['xy'][hot], axis=0, weights=s0['mass'][hot]*(s0['u'][hot]-1.5e-6))

    control = None
    if 'LDA/HLLC low (ell=0)' in runs:
        a, b = runs['LDA/HLLC low (ell=0)'], runs['HLLC moving']
        control = [dict(time=x['time'], max_rel={k: float(np.max(abs(x[k]-y[k]))/max(np.max(abs(y[k])), 1e-300))
                                                   for k in ('rho', 'p', 'xy')}) for x, y in zip(a, b)]

    final, metrics = {}, {}
    for key, seq in runs.items():
        s = radial(seq[-1], origins[key]); final[key] = s
        m = describe(s, seq[0], exact); m['core'] = core_rows(s); m['roughness'] = roughness(s)
        means, edges, _ = binned_statistic(s['r'], s['rho'], statistic='mean', bins=np.arange(0, .4001, .005))
        j = int(np.nanargmax(means)); m['binned_density_peak'] = float(means[j])
        m['binned_peak_radius'] = float((edges[j]+edges[j+1])/2)
        m['history'] = [[a['time'], *a['totals'].tolist()] for a in seq]
        metrics[key] = m
    write(out/'verification.json', dict(metrics=metrics, metadata=meta, limiter=stats, uniform_defects=uniform,
        static_blend_regression=static_regression, low_control_vs_hllc=control, source_provenance=source,
        analysis_sha256=sha(__file__), analytic_shock_radius=exact['shock'],
        method='RD at nodes, FV at centroids; radius from initial injected-excess-energy centroid; roughness: '
               'area-weighted quadratic-in-r detrended v_r RMS and tangential v RMS in radial bands.'))

    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    panels = (('lda_hllc_nearest21_profiles', '21 heated points',
               [('LDA/HLLC bounds', '#c0392b', '-'), ('LDA/HLLC positivity', '#8e44ad', '--'),
                ('HLLC moving', '#7f8c8d', '-.'), ('MMFV 1st order', '#2a9d8f', ':'), ('MMFV 2nd order', '#376db1', '-')]),
              ('lda_hllc_nearest1_profiles', '1 heated point',
               [('LDA/HLLC bounds, 1 hot node', '#c0392b', '-'), ('LDA/HLLC positivity, 1 hot node', '#8e44ad', '--'),
                ('HLLC moving, 1 hot node', '#7f8c8d', '-.'), ('MMFV 2nd order', '#376db1', '-')]))
    for filename, title, keys in panels:
        keys = [k for k in keys if k[0] in final]
        fig, axes = plt.subplots(2, 3, figsize=(12.8, 7.1), layout='constrained')
        for row, rmax in enumerate((.4, .15)):
            bins = np.arange(0, rmax+.0001, .005); mid = (bins[1:]+bins[:-1])/2
            for ax, field, label, exterior in zip(axes[row], ('rho', 'vr', 'p'), ('$\\rho$', '$v_r$', '$p$'), (1., 0., 1e-6)):
                for key, color, ls in keys:
                    s = final[key]; take = s['r'] < rmax
                    ax.scatter(s['r'][take], s[field][take], s=2 if row == 0 else 7,
                               alpha=.03 if row == 0 else .15, color=color, rasterized=True)
                    ax.plot(mid, binned_statistic(s['r'], s[field], statistic='mean', bins=bins)[0], color=color, ls=ls,
                            lw=1.6, label=key)
                ax.plot(np.r_[exact['r'], exact['shock'], .45], np.r_[exact[field], exterior, exterior], 'k--', lw=1.2,
                        label='2D Sedov')
                values = np.concatenate([final[k][field][final[k]['r'] < rmax] for k, _, _ in keys])
                lo = min(0., float(values.min())); hi = max(float(values.max()), float(np.max(exact[field][exact['r'] < rmax])))
                pad = (hi-lo)*.06
                ax.set(xlim=(0, rmax), ylim=(lo-pad, hi+pad), xlabel='Radius from injection centroid', ylabel=label)
                ax.grid(alpha=.15)
        axes[0, 0].legend(fontsize=8)
        fig.suptitle(f'Sedov blast, glass $128^2$, {title}, $t=0.05$, moving meshes\n'
                     'Experimental limited LDA/F1 + edge-HLLC RD; lower row: core detail')
        fig.savefig(out/f'{filename}.png', dpi=300); fig.savefig(out/f'{filename}.pdf'); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), layout='constrained')
    for key, color, ls in (('LDA/HLLC bounds', '#c0392b', '-'), ('LDA/HLLC positivity', '#8e44ad', '--'),
                           ('HLLC moving', '#7f8c8d', '-.'), ('LDA/HLLC bounds, 1 hot node', '#922b21', ':')):
        if key not in metrics: continue
        a = np.array(metrics[key]['history'])
        for ax, col in zip(axes, (1, 4)):
            ax.plot(a[:, 0], 100*(a[:, col]/a[0, col]-1), color=color, ls=ls, marker='o', ms=3, label=key)
    for ax, label in zip(axes, ('Mass change [%]', 'Energy change [%]')):
        ax.set(xlim=(0, .05), xlabel='Time', ylabel=label); ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    fig.suptitle('Budgets relative to the saved initial state')
    fig.savefig(out/'lda_hllc_budgets.png', dpi=300); plt.close(fig)

    summary = {k: dict(rho_max=v['density_max'], rho_min=v['density_min'], mean_peak=v['binned_density_peak'],
                       peak_r=v['binned_peak_radius'], core05=v['core']['0.05']['mean_density_by_area'],
                       core10=v['core']['0.1']['mean_density_by_area'], p_core=v['annuli'][0]['p'],
                       dM=v['mass_relative'], dE=v['energy_relative'], rough=v['roughness']) for k, v in metrics.items()}
    print(json.dumps(dict(summary=summary, limiter=stats, uniform=uniform, static_regression=static_regression,
                          control=control[-1] if control else None,
                          failed=[k for k, v in meta.items() if isinstance(v, dict) and v.get('failed')]), indent=1))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('root', type=Path)
    p.add_argument('--out', default='analysis'); p.add_argument('--skip', nargs='*', default=[])
    a = p.parse_args(); main(a.root.resolve(), a.out, tuple(a.skip))
