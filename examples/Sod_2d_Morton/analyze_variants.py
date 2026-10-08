#!/usr/bin/env python3
"""Verify the matched Morton campaign, including failures, and plot raw nodes."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys

import h5py
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'tests/rd'))
if (HERE / 'run_n_gauss3_split.py').exists():
    sys.path.insert(0, str(HERE))
from run_n_gauss3_split import sha, state, write


def analyze(root):
    campaign = json.loads((root / 'campaign.json').read_text())
    hashes = {}
    def check(path, expected=None):
        path = Path(path)
        value = sha(path)
        if expected is not None:
            assert value == expected, str(path)
        hashes[str(path)] = value
    check(root / 'campaign.json')
    check(root / 'source.tar', campaign['source_tar_sha256'])
    check(root / 'source_provenance.json')
    prov = json.loads((root / 'source_provenance.json').read_text())
    rf = root / 'source/examples/shocktube_1d/Riemann.py'
    check(rf, prov['tracked_hashes']['examples/shocktube_1d/Riemann.py'])
    spec = importlib.util.spec_from_file_location('frozen_riemann', rf)
    riemann = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(riemann)
    gamma = campaign['gamma']
    def exact(x, t=.2):
        _, q, waves = riemann.RiemannProblem(np.asarray(x).copy(), 1.5,
            np.array([1., 0., 1.]), np.array([.125, 0., .1]), gamma, t)
        return np.column_stack((q, q[:, 2] / ((gamma-1)*q[:, 0]))), 1.5+waves

    rows, gates, curves, initials = [], [], {}, {}
    for c in campaign['reused_cases'] + campaign['cases']:
        run = Path(c['archive']) / 'runs' / c['name']
        art = Path(c['archive']) / 'artifacts' / c['method']
        check(run / 'run_status.json')
        status = json.loads((run / 'run_status.json').read_text())
        row = {k: c[k] for k in ('name', 'method', 'scheme', 'temporal', 'residual',
            'mesh', 'effective_Nx', 'reused', 'frame')}
        row.update(returncode=status.get('returncode'), elapsed_seconds=status.get('seconds'))
        if status.get('status') == 'blocked_by_uniform_gate':
            row.update(complete=False, failure='blocked_by_uniform_gate')
            rows.append(row)
            continue
        check(art / 'provenance.json')
        meta = json.loads((art / 'provenance.json').read_text())
        assert status['binary_sha256'] == meta['binary_sha256']
        assert meta['source_tar_sha256'] == campaign['source_tar_sha256']
        for p, h in ((art/'Arepo', meta['binary_sha256']), (art/'Config.sh', meta['config_sha256']),
                     (run/'param.txt', c['param_sha256']), (c['ic'], c['ic_sha256'])):
            check(p, h)
        cfg = (art / 'Config.sh').read_text().splitlines()
        for flag in ('GAMMA=(5.0/3.0)', 'RD_RK2_TOTAL_RESIDUAL', 'CREATE_FULL_MESH',
                     'FORCE_EQUAL_TIMESTEPS', c['scheme']+'_SCHEME'):
            assert flag in cfg, (c['name'], flag)
        assert ('RD_DIAG_PREDICTOR_ONLY' in cfg) == (c['temporal'] == 'Euler')
        assert ('VORONOI_STATIC_MESH' in cfg) == (c['mesh'] == 'static')
        assert ('RD_ALE_CONTOUR_GAUSS=3' in cfg) == (c['residual'].lower() == 'gauss3')
        assert ('RD_RK2_SPLIT_STAGES' in cfg) == (c['mesh'] == 'moving')
        assert 'RD_ELEMENT_COMOVING_FRAME' not in cfg
        check(run / 'run.log')
        log = (run / 'run.log').read_text()
        sync = re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*([\deE.+-]+),\s+Systemstep:\s*([\deE.+-]+)', log)
        dt = np.array([float(z[2]) for z in sync if float(z[2]) > 0])
        history = []
        for file in sorted((run / 'output').glob('snap_*.hdf5')):
            check(file)
            s = state(file)
            with h5py.File(file) as f:
                g = f['PartType0']; order = np.argsort(g['ParticleIDs'][:])
                s['e'] = g['InternalEnergy'][:][order]
                s['vertex_speed_max'] = float(np.max(np.linalg.norm(g['VertexVelocity'][:, :2], axis=1)))
            assert all(np.isfinite(s[k]).all() for k in ('xy', 'rho', 'v', 'p', 'e', 'mass', 'w'))
            assert min(s['rho'].min(), s['p'].min(), s['mass'].min()) > 0
            np.testing.assert_allclose(s['p'], (gamma-1)*s['rho']*s['e'], rtol=1e-12, atol=1e-14)
            if history:
                assert np.array_equal(s['id'], history[0]['id'])
            if c['mesh'] == 'static':
                assert s['vertex_speed_max'] == 0
                if history:
                    assert np.array_equal(s['xy'], history[0]['xy'])
            s['snapshot'] = str(file); history.append(s)
        complete = (status['returncode'] == 0 and 'bye!' in log and len(history) == 5
                    and history[-1]['time'] == c['end'])
        row.update(complete=complete, last_snapshot_time=history[-1]['time'] if history else None,
            steps=int(sync[-1][0]) if sync else None,
            last_logged_time=float(sync[-1][1]) if sync else None,
            dt_min=float(dt.min()) if len(dt) else None, dt_max=float(dt.max()) if len(dt) else None,
            steps_at_max_timestep=int(np.count_nonzero(dt >= campaign['max_timestep']*(1-1e-6))),
            f1_lumped_sum=sum(map(int, re.findall(r'f1_lumped=(\d+)', log))))
        if not complete:
            row['failure'] = '\n'.join(log.splitlines()[-25:])
        else:
            np.testing.assert_allclose([s['time'] for s in history], np.linspace(0, c['end'], 5), rtol=0, atol=2e-15)
            assert 'RD-CKSUM stage=0' in log
            assert ('RD-CKSUM stage=1' in log) == (c['temporal'] != 'Euler')
            assert not any(z in log for z in ('TERMINATE:', 'RD assertion', 'very bad...', 'invalid geometry:'))
        if not history:
            rows.append(row); continue
        a, s = history[0], history[-1]
        if c['problem'] == 'uniform':
            defect = max(float(np.max(abs(h[k]-a[k]))) for h in history for k in ('rho', 'p', 'v'))
            row.update(max_change=defect, passed=complete and defect < 1e-12)
            gates.append(row); continue
        nx = c['effective_Nx']
        assert len(a['id']) == (2*nx)**2
        high = (a['xy'][:, 0] > .5) & (a['xy'][:, 0] < 1.5)
        np.testing.assert_allclose(a['rho'], np.where(high, 1., .125), rtol=0, atol=1e-14)
        np.testing.assert_allclose(a['p'], np.where(high, 1., .1), rtol=0, atol=1e-14)
        assert np.count_nonzero(a['v']) == 0
        if nx in initials:
            for k in ('id', 'xy', 'rho', 'p', 'v', 'mass', 'e'):
                np.testing.assert_allclose(a[k], initials[nx][k], rtol=0, atol=2e-14, err_msg=(c['name'], k))
        else:
            initials[nx] = a
        histories = []
        for h in history:
            drift = (h['totals']-a['totals']) / a['totals'][[0, 0, 0, 3]]
            delta = (h['xy']-a['xy']+1) % 2 - 1
            histories.append(dict(time=h['time'], normalized_conserved_drift=drift.tolist(),
                min_rho=float(h['rho'].min()), min_p=float(h['p'].min()),
                vertex_speed_max=h['vertex_speed_max'], displacement_max=float(np.linalg.norm(delta, axis=1).max())))
        row.update(full_box_nodes=len(a['id']), history=histories,
            max_mass_relative_drift=max(abs(h['normalized_conserved_drift'][0]) for h in histories),
            max_energy_relative_drift=max(abs(h['normalized_conserved_drift'][3]) for h in histories))
        if c['mesh'] == 'moving':
            for kind in ('temporary_change', 'rebase_change', 'endpoint_change'):
                values = re.findall(kind+r'=\[([^\]]+)\]', log)
                row['ale_'+kind+'_sum'] = np.array([[float(v) for v in line.split(',')]
                    for line in values]).sum(axis=0).tolist() if values else None
            if complete:
                assert histories[-1]['displacement_max'] > 0
                assert histories[-1]['vertex_speed_max'] > 0
        if complete:
            mask = (s['xy'][:, 0] > 1) & (s['xy'][:, 0] < 2)
            x = s['xy'][mask, 0]-1
            q = np.column_stack((s['rho'][mask], s['v'][mask, 0], s['p'][mask], s['e'][mask]))
            ref, _ = exact(x+1, s['time'])
            w = s['w'][mask]/s['w'][mask].sum()
            error = w @ abs(q-ref)
            edges = np.linspace(0, 1, 129); ib = np.digitize(x, edges)-1
            counts = np.bincount(ib, minlength=128)
            assert len(counts) == 128 and counts.sum() == len(x)
            means = np.array([q[ib == j].mean(axis=0) if counts[j] else np.full(4, np.nan) for j in range(128)])
            bx = (edges[1:]+edges[:-1])/2
            curves[(c['method'], nx)] = (x, q, bx, means)
            row.update(tube_nodes=len(x), end_time=s['time'], snapshot=s['snapshot'],
                vy_rms=float(np.sqrt(w @ (s['v'][mask, 1]**2))),
                vx_mean_min=float(np.nanmin(means[:, 1])), vx_mean_max=float(np.nanmax(means[:, 1])),
                negative_vx_area_fraction=float(w[q[:, 1] < -.05].sum()),
                mean_negative_vx=float(w @ np.maximum(-q[:, 1], 0)),
                xi_at_vx_min=float(x[np.argmin(q[:, 1])]))
            for j, field in enumerate(('rho', 'vx', 'p', 'e')):
                row.update({field+'_l1': float(error[j]), field+'_min': float(q[:, j].min()), field+'_max': float(q[:, j].max())})
            np.savetxt(root/(c['name']+'_bin_means.csv'), np.column_stack((bx, means, counts)), delimiter=',',
                header='xi,rho,vx,p,e,node_count', comments='')
        rows.append(row)
    _, waves = exact(np.linspace(1, 2, 1001))
    summary = dict(cases=rows, uniform_gates=gates, gamma=gamma, final_time=.2,
        coordinates='xi=x-1; tau=t', initial_states_match_atol=2e-14,
        all_saved_states_positive=True, wave_positions_xi=(waves-1).tolist(),
        mean='128 equal xi bins; unweighted node means; all tube nodes retained in scatter.',
        error_norm='Normalized current median-dual area m/rho on raw tube nodes, not on bin means.',
        limits=campaign['limits'], input_hashes=hashes)
    write(root/'summary.json', summary)
    pages = make_plots(root, curves, exact)
    for path, value in hashes.items():
        assert sha(path) == value, path
    if Path(__file__).resolve() != root/'analyze_variants.py':
        shutil.copy2(__file__, root/'analyze_variants.py')
    write(root/'verification.json', dict(all_input_hashes_unchanged=True,
        science_completed=sum(c['complete'] for c in rows), science_total=len(rows),
        uniform_passed=sum(g['passed'] for g in gates), uniform_total=len(gates),
        all_saved_states_positive=True, all_raw_tube_nodes_retained=True,
        expected_pdf_pages=pages, visual_review='pending'))
    print(json.dumps([{k: v for k, v in r.items() if k in ('method', 'effective_Nx', 'complete',
        'rho_l1', 'vx_min', 'vx_max', 'max_mass_relative_drift', 'max_energy_relative_drift', 'steps')} for r in rows], indent=2))


def make_plots(root, curves, exact, resolutions=(128, 64)):
    figures = root/'figures'; figures.mkdir(exist_ok=True)
    output = root/'output/pdf'; output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.linewidth': .8,
        'xtick.direction': 'in', 'ytick.direction': 'in', 'xtick.top': True, 'ytick.right': True, 'pdf.fonttype': 42})
    xx = np.linspace(0, 1, 3001); reference, _ = exact(xx+1)
    labels = [r'Density $\rho$', r'Velocity $v_x$', r'Pressure $p$', r'Specific internal energy $e$']
    groups = [
        ('mesh', 'Static and moving meshes', [
            ('N / Roe / RK2', [('N_rk2_roe_static', 'Static'), ('N_rk2_roe_moving', 'Moving')]),
            ('LDA / Gauss3 / F1', [('LDA_f1_gauss3_static', 'Static'), ('LDA_f1_gauss3_moving', 'Moving')])]),
        ('time', 'Static mesh: time updates', [
            ('N / Roe', [('N1_roe_static', 'Euler'), ('N_rk2_roe_static', 'RK2')]),
            ('LDA / Roe', [('LDA1_roe_static', 'Euler'), ('LDA_f1_roe_static', 'F1')]),
            ('LDA / Gauss3', [('LDA_fe_gauss3_static', 'Euler'), ('LDA_f1_gauss3_static', 'F1')])]),
        ('residual', 'LDA / F1: residuals', [
            ('Static mesh', [('LDA_f1_roe_static', 'Roe'), ('LDA_f1_gauss3_static', 'Gauss3')]),
            ('Moving mesh', [('LDA_f1_roe_moving', 'Roe + mesh split'), ('LDA_f1_gauss3_moving', 'Gauss3')])])]
    pages = 0
    with PdfPages(output/'Sod_2d_Morton_variants_review.pdf') as pdf:
        # Put the higher-resolution direct static/moving comparison first.
        for tag, title, columns in groups:
            for nx in resolutions:
                fig, axs = plt.subplots(4, len(columns), figsize=(10.8 if len(columns)==3 else 9.5, 10.3),
                    sharex=True, sharey='row', layout='constrained')
                for j, (subtitle, series) in enumerate(columns):
                    for k in range(4):
                        ax = axs[k, j]
                        for i, (method, label) in enumerate(series):
                            color = ('#2878af', '#cb7629')[i]
                            if (method, nx) not in curves:
                                ax.text(.03, .08+.08*i, label+': incomplete', transform=ax.transAxes, color=color, fontsize=8)
                                continue
                            x, q, bx, means = curves[(method, nx)]
                            ax.scatter(x, q[:, k], s=2.4, color=color, alpha=.085, edgecolors='none', rasterized=True, zorder=1)
                            ax.plot(bx, means[:, k], c=color, ls=('-', '--')[i], lw=1.35, label=label, zorder=3)
                            if q[:, k].max() > 3*reference[:, k].max():
                                extreme = int(np.argmax(q[:, k]))
                                ax.scatter(x[extreme], q[extreme, k], s=26, facecolors='none', edgecolors=color, zorder=5)
                                ax.annotate(f'{label} raw max: {q[extreme, k]:.2f}',
                                    xy=(x[extreme], q[extreme, k]), xytext=(.06, .84),
                                    textcoords='axes fraction', fontsize=8, color=color,
                                    arrowprops=dict(arrowstyle='-', color=color, lw=.7))
                        ax.plot(xx, reference[:, k], color='black', lw=1.05, label='Exact', zorder=4)
                        ax.set_xlim(0, 1); ax.grid(color='.90', lw=.5)
                        if j == 0: ax.set_ylabel(labels[k])
                    axs[0, j].set_title(subtitle, fontsize=10)
                    axs[0, j].legend(loc='upper right', fontsize=8, framealpha=.94)
                    # Display x = X - 1 for the raw right-hand tube 1 < X < 2.
                    axs[-1, j].set_xlabel(r'$x$')
                fig.suptitle(title+rf' | $N_x\simeq{nx}$, $\gamma=5/3$, $t=0.2$', fontsize=12)
                fig.supxlabel('Sod_2d_Morton | glass IC | all-node scatter + 128-bin means | lab frame', fontsize=8)
                fig.savefig(figures/f'Sod_2d_Morton_{tag}_Nx{nx}.png', dpi=180)
                pdf.savefig(fig); plt.close(fig); pages += 1
    return pages


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    analyze(parser.parse_args().root.resolve())
