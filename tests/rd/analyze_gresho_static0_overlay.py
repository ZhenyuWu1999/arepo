#!/usr/bin/env python3
"""Add an audited static N/boost0/t3 control to the moving Gresho preview."""
import argparse
import json
from pathlib import Path
import re
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from run_n_gauss3_split import state, sha, write
from analyze_gresho_glass_boost_lab import profile


def audit_case(archive, case, moving):
    folder = archive / 'runs' / case['name']
    artifact = archive / 'artifacts' / case['method']
    meta = json.loads((artifact / 'provenance.json').read_text())
    status = json.loads((folder / 'run_status.json').read_text())
    assert sha(artifact / 'Arepo') == meta['binary_sha256'] == status['binary_sha256']
    assert sha(artifact / 'Config.sh') == meta['config_sha256']
    assert sha(case['ic']) == case['ic_sha256']
    assert sha(folder / 'param.txt') == case['param_sha256']
    assert case['frame'] == 'lab' and case['end'] == 3.
    assert case['mesh'] == ('moving' if moving else 'static')
    header = (artifact / 'arepoconfig.h').read_text()
    assert '#define RD_ELEMENT_COMOVING_FRAME' not in header
    assert ('#define VORONOI_STATIC_MESH' not in header) == moving
    if moving:
        assert '#define RD_ALE_EQUALSTEP' in header
    log = (folder / 'run.log').read_text(errors='replace')
    assert status['returncode'] == 0 and 'bye!' in log and 'TERMINATE:' not in log
    sync = re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*([\deE.+-]+),\s+Systemstep:\s*([\deE.+-]+)', log)
    assert [int(s[0]) for s in sync] == list(range(16385))
    assert float(sync[-1][1]) == 3.
    assert {s[2] for s in sync[1:]} == {'0.000183105'}
    paths = sorted((folder / 'output').glob('snap_*.hdf5'))
    snapshots = [state(p) for p in paths]
    assert [s['time'] for s in snapshots] == [0., .75, 1.5, 2.25, 3.]
    opening = snapshots[0]
    assert len(opening['id']) == 2304
    history = []
    for s, path in zip(snapshots, paths):
        assert np.array_equal(s['id'], opening['id'])
        assert all(np.isfinite(s[k]).all() for k in ('xy', 'v', 'rho', 'p', 'mass'))
        assert min(s['rho'].min(), s['p'].min(), s['mass'].min()) > 0
        if not moving:
            assert np.array_equal(s['xy'], opening['xy'])
        radius, vp, exact = profile(s, case['boost'])
        w = s['mass'] / s['mass'].sum()
        wa = s['w'] / s['w'].sum()
        d = (s['xy'] - [case['boost']*s['time'], 0.]) % 1. - .5
        exact_v = np.column_stack((-d[:, 1], d[:, 0])) * (exact/np.maximum(radius, 1e-100))[:, None]
        history.append(dict(time=s['time'], snapshot_sha256=sha(path),
            vphi_l1_mass=float(w @ abs(vp-exact)), vphi_l1_area=float(wa @ abs(vp-exact)),
            velocity_l1_mass=float(w @ np.linalg.norm(s['v']-[case['boost'], 0.]-exact_v, axis=1)),
            vphi_peak=float(vp.max()), vphi_min=float(vp.min()),
            rho_min=float(s['rho'].min()), p_min=float(s['p'].min()),
            mass_relative_drift=float((s['totals'][0]-opening['totals'][0])/opening['totals'][0]),
            energy_relative_drift=float((s['totals'][3]-opening['totals'][3])/opening['totals'][3])))
    return snapshots, history, sync, dict(archive=str(archive), method=case['method'],
        binary_sha256=meta['binary_sha256'], config_sha256=meta['config_sha256'],
        input_sha256=case['ic_sha256'], param_sha256=case['param_sha256'],
        log_sha256=sha(folder/'run.log'))


def analyze(root, moving_root):
    old = json.loads((moving_root/'summary.json').read_text())
    old_prov = json.loads((moving_root/'analysis_provenance.json').read_text())
    assert sha(moving_root/'summary.json') == old_prov['summary_sha256']
    states, rows, sequences, provenance, sources, gates = {}, [], [], [], [], []
    for archive, moving in [(root, False), (moving_root/'boost0', True), (moving_root/'boost10', True)]:
        campaign = json.loads((archive/'campaign.json').read_text())
        source = json.loads((archive/'source_provenance.json').read_text())
        sources.append(sha(archive/'source.tar'))
        assert sources[-1] == source['source_tar_sha256']
        for phase in ('uniform', 'pilot'):
            results = json.loads((archive/f'gate_{phase}.json').read_text())
            assert len(results) == (2 if moving else 1) and all(r['passed'] for r in results)
            gates.extend([dict(r, archive=str(archive)) for r in results])
        for case in campaign['cases']:
            if case['horizon'] != 'science':
                continue
            assert case['boost'] in (0, 10)
            if not moving:
                assert case['scheme'] == 'N' and case['boost'] == 0
            snapshots, history, sequence, prov = audit_case(archive, case, moving)
            key = (case['scheme'], case['mesh'], case['boost'])
            states[key] = snapshots
            if moving:
                saved = next(r for r in old['cases'] if r['scheme'] == case['scheme'] and r['boost'] == case['boost'])
                for before, after in zip(saved['history'], history):
                    assert before['snapshot_sha256'] == after['snapshot_sha256']
                    for field, value in before.items():
                        assert value == after[field], (key, field, value, after[field])
            rows.append(dict(scheme=case['scheme'], mesh=case['mesh'], boost=case['boost'],
                steps=16384, actual_dt=3/16384, history=history, final=history[-1]))
            sequences.append(sequence)
            provenance.append(prov)
    assert len(rows) == 5 and len(set(sources)) == 1
    assert all(s == sequences[0] for s in sequences[1:])
    for key in ('id', 'xy', 'rho', 'v', 'p', 'mass'):
        assert np.array_equal(states[('N', 'static', 0)][0][key], states[('N', 'moving', 0)][0][key]), key
    by = {(r['scheme'], r['mesh'], r['boost']): r['final'] for r in rows}
    ratio = by[('N', 'moving', 0)]['vphi_l1_mass']/by[('N', 'static', 0)]['vphi_l1_mass']
    write(root/'summary.json', dict(cases=rows, gates=gates, provenance=provenance,
        source_sha256=sources[0], moving_reference=str(moving_root),
        moving_reference_summary_sha256=old_prov['summary_sha256'],
        initial_static0_moving0_fields_identical=True, all_timestep_histories_identical=True,
        N_moving0_over_static0_vphi_l1=ratio,
        norm='All 2304 native nodes, final-mass weighted azimuthal velocity absolute error.',
        recentering='Analytic periodic center (0.5+boost*t,0.5), subtract (boost,0); no fitted center, interpolation or binning.',
        limits='One resolution/endpoint. Less damping of the unboosted N vortex supports a local-flow benefit of mesh motion. Close boosted radial profiles alone do not prove exact invariance of mesh/state trajectories; see moving reference report.'))

    out = root/'output/pdf'; out.mkdir(parents=True, exist_ok=True)
    figs = root/'figures'; figs.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'pdf.fonttype': 42,
                         'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 5.5), sharex=True, sharey=True, layout='constrained')
    all_v = np.concatenate([profile(ss[-1], boost)[1] for (_, _, boost), ss in states.items()])
    ymin, ymax = min(-.05, float(all_v.min())-.03), max(1.08, float(all_v.max())+.03)
    rr = np.linspace(0, .71, 1000)
    for ax, scheme, color in zip(axes, ('N', 'LDA'), ('#278449', '#2672b5')):
        if scheme == 'N':
            radius, vp, _ = profile(states[('N', 'static', 0)][-1], 0)
            error = by[('N', 'static', 0)]['vphi_l1_mass']
            ax.scatter(radius, vp, s=7, marker='s', color='#777777', alpha=.35, linewidths=0,
                       rasterized=True, label=f'Static, boost 0: $L_1={error:.5f}$')
        for boost in (0, 10):
            radius, vp, _ = profile(states[(scheme, 'moving', boost)][-1], boost)
            error = by[(scheme, 'moving', boost)]['vphi_l1_mass']
            ax.scatter(radius, vp, s=10 if boost == 0 else 12, marker='x' if boost == 0 else '.',
                       color='#d17a19' if boost == 0 else color, alpha=.45, linewidths=.55,
                       rasterized=True, label=f'Moving, boost {boost}: $L_1={error:.5f}$')
        ax.plot(rr, np.where(rr < .2, 5*rr, np.where(rr < .4, 2-5*rr, 0)), 'k--', lw=1.3, label='Analytic')
        ax.set(title=scheme+' / '+('Roe' if scheme == 'N' else 'Gauss3'), xlabel=r'Radius $r$',
               xlim=(0, .71), ylim=(ymin, ymax))
        ax.set_xticks([0, .2, .4, .6]); ax.grid(alpha=.15)
        ax.legend(loc='upper center', bbox_to_anchor=(.5, -.18), fontsize=9, frameon=False, markerscale=1.8)
    axes[0].set_ylabel(r'Azimuthal velocity $v_\varphi$')
    fig.suptitle(r'Gresho: glass $48^2$, $t=3$'+'\nLaboratory-frame solver; bulk translation removed from profiles', fontsize=12)
    filename = 'gresho_glass48_t3_moving_boost0_10_static0'
    pdf = out/f'{filename}.pdf'
    fig.savefig(pdf, dpi=300); fig.savefig(figs/f'{filename}.png', dpi=180); plt.close(fig)
    for filename in (Path(__file__).name, 'analyze_gresho_glass_boost_lab.py', 'run_n_gauss3_split.py'):
        shutil.copy2(Path(__file__).parent/filename, root/filename)
    write(root/'analysis_provenance.json', dict(script_sha256=sha(__file__),
        profile_helper_sha256=sha(Path(__file__).parent/'analyze_gresho_glass_boost_lab.py'),
        summary_sha256=sha(root/'summary.json'), pdf_sha256=sha(pdf)))
    for row in rows:
        print(row['scheme'], row['mesh'], row['boost'], row['final'])
    print('N moving0/static0 error ratio:', ratio)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--moving', type=Path, required=True)
    args = parser.parse_args()
    analyze(args.root.resolve(), args.moving.resolve())
