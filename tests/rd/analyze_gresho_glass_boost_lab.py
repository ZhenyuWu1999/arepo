#!/usr/bin/env python3
"""Audit and plot a matched lab-frame glass Gresho static/moving campaign."""
import argparse
import json
from pathlib import Path
import re
import shutil

import h5py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from run_n_gauss3_split import state, sha, write


def profile(s, boost):
    d = s['xy'].copy()
    d[:, 0] -= boost * s['time']
    d = (d - .5 + .5) % 1. - .5
    radius = np.linalg.norm(d, axis=1)
    velocity = s['v'] - [boost, 0.]
    vphi = (-d[:, 1]*velocity[:, 0] + d[:, 0]*velocity[:, 1]) / np.maximum(radius, 1e-100)
    exact = np.where(radius < .2, 5*radius, np.where(radius < .4, 2-5*radius, 0.))
    return radius, vphi, exact


def analyze(root):
    campaign = json.loads((root / 'campaign.json').read_text())
    boost = float(campaign['setup']['boost'][0])
    end = float(next(c['end'] for c in campaign['cases'] if c['horizon'] == 'science'))
    expected_outputs = campaign['setup'].get('science_output_times', [0., .5, 1.])
    stem = f'gresho_glass_boost{boost:g}' + (f'_t{end:g}' if end != 1. else '') + '_lab_static_moving'
    provenance = json.loads((root / 'source_provenance.json').read_text())
    assert sha(root / 'source.tar') == provenance['source_tar_sha256']
    rows, final_states, initial_states, step_sequences = [], {}, [], []
    for case in campaign['cases']:
        if case['horizon'] != 'science':
            continue
        folder = root / 'runs' / case['name']
        status = json.loads((folder / 'run_status.json').read_text())
        assert status['returncode'] == 0
        artifact = root / 'artifacts' / case['method']
        binary_meta = json.loads((artifact / 'provenance.json').read_text())
        assert sha(artifact / 'Arepo') == status['binary_sha256'] == binary_meta['binary_sha256']
        assert sha(artifact / 'Config.sh') == sha(root / 'configs' / (case['method']+'.sh')) == binary_meta['config_sha256']
        assert sha(case['ic']) == case['ic_sha256']
        assert sha(folder / 'param.txt') == case['param_sha256']
        header = (artifact / 'arepoconfig.h').read_text()
        assert '#define RD_ELEMENT_COMOVING_FRAME' not in header
        assert '#define RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC' not in header
        log = (folder / 'run.log').read_text(errors='replace')
        assert 'bye!' in log and 'TERMINATE:' not in log
        paths = sorted((folder / 'output').glob('snap_*.hdf5'))
        snapshots = [state(p) for p in paths]
        assert [s['time'] for s in snapshots] == expected_outputs
        opening = snapshots[0]
        initial_states.append(opening)
        sync = re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*([\deE.+-]+),\s+Systemstep:\s*([\deE.+-]+)', log)
        printed_steps = sorted(set(float(s[2]) for s in sync[1:]))
        assert int(sync[-1][0]) == len(sync)-1
        step_sequences.append([s[2] for s in sync[1:]])
        actual_dt = end/int(sync[-1][0]) if len(printed_steps) == 1 else None
        if actual_dt is not None:
            assert abs(printed_steps[0]-actual_dt) < 5e-10
            assert actual_dt <= campaign['setup']['cap'] * (1+1e-12)
        history = []
        for path, s in zip(paths, snapshots):
            assert np.array_equal(s['id'], opening['id'])
            assert all(np.isfinite(s[k]).all() for k in ('xy', 'v', 'rho', 'p', 'mass'))
            assert s['rho'].min() > 0 and s['p'].min() > 0 and s['mass'].min() > 0
            if case['mesh'] == 'static':
                assert np.array_equal(s['xy'], opening['xy'])
            radius, vp, exact = profile(s, case['boost'])
            mass_weight = s['mass'] / s['mass'].sum()
            area_weight = s['w'] / s['w'].sum()
            d = (s['xy'] - [case['boost']*s['time'], 0.]) % 1. - .5
            v_exact = np.column_stack((-d[:, 1], d[:, 0])) * (exact/np.maximum(radius, 1e-100))[:, None]
            hist = dict(time=s['time'], snapshot_sha256=sha(path),
                vphi_l1_mass=float(mass_weight @ abs(vp-exact)),
                vphi_l1_area=float(area_weight @ abs(vp-exact)),
                velocity_l1_mass=float(mass_weight @ np.linalg.norm(s['v']-[case['boost'], 0.]-v_exact, axis=1)),
                vphi_peak=float(vp.max()), rho_min=float(s['rho'].min()), p_min=float(s['p'].min()),
                mass_relative_drift=float((s['totals'][0]-opening['totals'][0])/opening['totals'][0]),
                energy_relative_drift=float((s['totals'][3]-opening['totals'][3])/opening['totals'][3]),
                momentum_absolute_drift=(s['totals'][1:3]-opening['totals'][1:3]).tolist())
            history.append(hist)
        diag = {}
        for key in ('min_pivot_ratio', 'cons_defect_abs', 'cons_defect_rel', 'svd_fallback', 'f1_lumped'):
            values = [float(v) for v in re.findall(r'\b'+key+r'=([+\-\deE.]+)', log)]
            if values:
                diag[key] = dict(min=min(values), max=max(values), last=values[-1])
        rows.append(dict(method=case['method'], scheme=case['scheme'], mesh=case['mesh'],
            complete=True, steps=int(sync[-1][0]), actual_dt=actual_dt, printed_systemsteps=printed_steps,
            seconds=status['seconds'], history=history, final=history[-1], diagnostics=diag))
        final_states[case['method']] = snapshots[-1]
    assert len(rows) == 4
    assert all(seq == step_sequences[0] for seq in step_sequences[1:]), 'Actual timestep histories differ; review comparison.'
    for s in initial_states[1:]:
        for k in ('id', 'xy', 'rho', 'v', 'p', 'mass'):
            assert np.array_equal(s[k], initial_states[0][k]), k
    by = {r['method']: r for r in rows}
    ratios = {scheme: by[f'{scheme}_moving_lab']['final']['vphi_l1_mass'] /
              by[f'{scheme}_static_lab']['final']['vphi_l1_mass'] for scheme in ('N', 'LDA')}
    uniform = json.loads((root / 'gate_uniform.json').read_text())
    pilot = json.loads((root / 'gate_pilot.json').read_text())
    assert all(r['passed'] for r in uniform + pilot)
    summary = dict(setup=campaign['setup'], cases=rows, moving_static_vphi_l1_ratios=ratios,
        initial_snapshots_identical=True, actual_timestep_histories_identical=True,
        uniform_gates=uniform, pilot_gates=pilot,
        norm='Sum_i m_i(t)*abs(vphi_i-exact(r_i))/sum_i m_i(t), all 2304 native nodes; separate m/rho area norm also stored.',
        recentering=f'Known analytic periodic center (0.5+{boost:g}*t,0.5); subtract ({boost:g},0) from velocity. No fitted center, regridding or binning.',
        limitations='Single resolution, endpoint and boost. Does not establish convergence, Galilean invariance or exact moving global conservation.')
    write(root / 'summary.json', summary)
    out = root / 'output/pdf'
    out.mkdir(parents=True, exist_ok=True)
    preview = root / 'figures'
    preview.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11, 'axes.spines.top':False,
                         'axes.spines.right':False, 'pdf.fonttype':42})
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 5.2), sharex=True, sharey=True, layout='constrained')
    rr = np.linspace(0, .71, 1000)
    all_velocities = np.concatenate([profile(s, boost)[1] for s in final_states.values()])
    ymin = min(-.05, float(all_velocities.min()) - .04)
    ymax = max(1.14, float(all_velocities.max()) + .04)
    for ax, scheme, color in zip(axes, ('N', 'LDA'), ('#278449', '#2672b5')):
        for mesh in ('static', 'moving'):
            method = f'{scheme}_{mesh}_lab'
            radius, vp, _ = profile(final_states[method], boost)
            error = by[method]['final']['vphi_l1_mass']
            ax.scatter(radius, vp, marker='x' if mesh=='static' else '.',
                       s=9 if mesh=='static' else 12, linewidths=.55,
                       color='#707070' if mesh=='static' else color,
                       alpha=.40 if mesh=='static' else .48, rasterized=True,
                       label=f'{mesh.capitalize()} mesh: $L_1={error:.4f}$')
        ax.plot(rr, np.where(rr<.2, 5*rr, np.where(rr<.4, 2-5*rr, 0)), 'k--', lw=1.4, label='Analytic')
        ax.set(title=f'{scheme} / '+('Roe' if scheme=='N' else 'Gauss3'),
               xlabel=r'Radius $r$', xlim=(0,.71), ylim=(ymin,ymax))
        ax.set_xticks([0,.2,.4,.6])
        ax.grid(alpha=.15)
        ax.legend(loc='upper center', bbox_to_anchor=(.5,-.18), fontsize=9,
                  frameon=False, markerscale=1.8)
    axes[0].set_ylabel(r'Azimuthal velocity $v_\varphi$')
    fig.suptitle(rf'Gresho: glass $48^2$, boost $({boost:g},0)$, $t={end:g}$'+'\nLaboratory-frame solver; bulk translation removed from profiles', fontsize=12)
    fig.savefig(out / (stem+'.pdf'), dpi=300)
    fig.savefig(preview / (stem+'.png'), dpi=180)
    plt.close(fig)
    shutil.copy2(__file__, root / Path(__file__).name)
    write(root / 'analysis_provenance.json', dict(script_sha256=sha(__file__),
        summary_sha256=sha(root / 'summary.json'), pdf_sha256=sha(out / (stem+'.pdf'))))
    for row in rows:
        print(row['method'], json.dumps(row['final']))
    print('moving/static L1', ratios)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    analyze(parser.parse_args().root.resolve())
