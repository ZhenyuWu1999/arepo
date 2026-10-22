#!/usr/bin/env python3
"""Independently analyse the portable COSMA Blob bundle (no AREPO execution).

Dependencies: numpy, scipy, h5py, matplotlib. Output files must not exist.
Use extensive snapshot Masses, and Masses/Density as the fixed median dual.
The Volume dataset is a different, Voronoi, diagnostic. No material tracer
exists. Equal/hierarchy fields are compared exactly only at common times;
other comparisons explicitly interpolate extensive states in time.
"""
import argparse
import csv
import gzip
import hashlib
import json
import re
import subprocess
from pathlib import Path

import h5py
import numpy as np

GAMMA = 5 / 3
WIND = 1.5 * 4.1
TCR = 2 * np.sqrt(10) / WIND


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def write_csv(path, rows):
    with path.open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_state(path):
    with h5py.File(path) as f:
        gas = f['PartType0']
        order = np.argsort(gas['ParticleIDs'][:])
        s = {k: gas[k][:][order] for k in gas}
        s['time'] = float(f['Header'].attrs['Time'])
        s['box'] = float(f['Header'].attrs['BoxSize'])
    assert len(np.unique(s['ParticleIDs'])) == len(order)
    for k, a in s.items():
        assert np.isfinite(a).all(), (path, k)
    m, v = s['Masses'], s['Velocities']
    assert min(m.min(), s['Density'].min(), s['Pressure'].min(),
               s['InternalEnergy'].min(), s['Volume'].min()) > 0
    s['dual'] = m / s['Density']
    s['q'] = np.column_stack((m, m[:, None] * v,
                             m * (s['InternalEnergy'] + .5 * (v*v).sum(axis=1))))
    return s


def analyse_case(root, case, out):
    folder = root / 'cases' / case['name']
    states = [read_state(p) for p in sorted((root / case['snapshots']).glob('snap_*.hdf5'))]
    initial = states[0]
    assert initial['time'] == 0 and len(states) == case['included_snapshots']
    q0 = initial['q'].sum(axis=0)
    scale = np.abs(initial['q']).sum(axis=0)
    scale[1:4] = np.maximum(scale[1:4], scale[0])
    history = []
    all_min = np.full(3, np.inf)
    for i, s in enumerate(states):
        assert s['box'] == 10
        np.testing.assert_array_equal(s['Coordinates'], initial['Coordinates'])
        np.testing.assert_array_equal(s['ParticleIDs'], initial['ParticleIDs'])
        if i:
            assert s['time'] > states[i-1]['time']
        rho, p, m, vol = s['Density'], s['Pressure'], s['Masses'], s['dual']
        dense, cold = rho > 64, p/rho < 9
        cloud = dense & cold
        drift = (s['q'].sum(axis=0)-q0)/scale
        eos = np.max(np.abs(p-(GAMMA-1)*rho*s['InternalEnergy']) / p)
        dual_change = np.max(np.abs(vol/initial['dual']-1))
        coverage = abs(vol.sum()/1000-1)
        assert eos < 1e-12 and dual_change < 1e-12 and coverage < 1e-12
        assert np.max(np.abs(drift)) < 1e-12
        row = dict(snapshot=f'snap_{i:03d}.hdf5', time=s['time'], tau=s['time']/TCR,
                   cloud_mass=float(m[cloud].sum()), cloud_nodes=int(cloud.sum()),
                   dense_mass=float(m[dense].sum()), cold_mass=float(m[cold].sum()),
                   rho_min=float(rho.min()), rho_max=float(rho.max()),
                   p_min=float(p.min()), p_max=float(p.max()),
                   u_min=float(s['InternalEnergy'].min()), coverage=float(coverage),
                   dual_max_relative_change=float(dual_change), eos_relative_defect=float(eos),
                   cloud_vx=float(np.average(s['Velocities'][cloud, 0], weights=m[cloud]))
                   if cloud.any() else None,
                   cloud_x=float(np.average(s['Coordinates'][cloud, 0], weights=m[cloud]))
                   if cloud.any() else None)
        row.update({f'drift_{k}': float(v) for k, v in zip(['mass', 'px', 'py', 'pz', 'energy'], drift)})
        all_min = np.minimum(all_min, [rho.min(), p.min(), s['InternalEnergy'].min()])
        history.append(row)
    m0 = history[0]['cloud_mass']
    for r in history:
        r['cloud_fraction'] = r['cloud_mass']/m0
    status = json.loads((folder/'run_status.json').read_text())
    assert status['returncode'] == case['returncode']
    assert status['binary_sha256'] == case['source_binary_sha256']
    hashes = []
    for p in (folder/'provenance').rglob('binary.sha256'):
        hashes.append(p.read_text().split()[0])
    hashes += [(folder/'provenance/build_binary.sha256').read_text().split()[0]]
    assert all(h == case['source_binary_sha256'] for h in hashes)
    assert (folder/'param.txt').read_bytes() == next((folder/'provenance').glob('provenance-*/param.used')).read_bytes()
    build = json.loads((folder/'provenance/build_provenance.json').read_text())
    assert sha((folder/'provenance/build_Config.used').read_bytes()) == build['config_sha256']
    assert sha((folder/'provenance/build_arepoconfig.h.used').read_bytes()) == build['header_sha256']
    assert (root/'configs'/f"{case['method']}.sh").read_bytes() == (folder/'provenance/build_Config.used').read_bytes()
    runtime = next((folder/'provenance').glob('provenance-*'))
    assert (runtime/'Config.used').read_bytes() == (folder/'provenance/build_Config.used').read_bytes()
    assert (runtime/'arepoconfig.h.used').read_bytes() == (folder/'provenance/build_arepoconfig.h.used').read_bytes()
    assert int((runtime/'exit_status.txt').read_text().strip()) == status['returncode']
    if status['returncode'] == 0:
        assert states[-1]['time'] == case['expected_end']
    supplied = list(csv.DictReader((root/'analysis'/f"{case['name']}.csv").open()))
    assert len(supplied) == len(history)
    for r, old in zip(history, supplied):
        for k, old_k in [('time', 'time'), ('cloud_mass', 'cloud_mass')]:
            np.testing.assert_allclose(r[k], float(old[old_k]), rtol=1e-13, atol=1e-13)
    summary = dict(case=case['name'], nodes=len(initial['ParticleIDs']), snapshots=len(states),
                   returncode=status['returncode'], job=status['slurm_job_id'], host=status['host'],
                   wall_seconds=status['seconds'], end_tau=history[-1]['tau'],
                   initial_totals=q0.tolist(), normalization=scale.tolist(),
                   max_abs_normalized_drift={k: max(abs(r[f'drift_{k}']) for r in history)
                       for k in ['mass', 'px', 'py', 'pz', 'energy']},
                   all_saved_minimum=dict(zip(['rho', 'pressure', 'specific_internal_energy'], all_min.tolist())),
                   max_coverage=max(r['coverage'] for r in history),
                   max_dual_change=max(r['dual_max_relative_change'] for r in history),
                   max_eos_defect=max(r['eos_relative_defect'] for r in history),
                   dense_mass_equals_cloud_mass=all(r['dense_mass'] == r['cloud_mass'] for r in history),
                   initial_cloud_mass=m0, final_cloud_fraction=history[-1]['cloud_fraction'],
                   final_rho_max=history[-1]['rho_max'], thresholds={})
    for label, fraction in [('half', .5), ('ten_percent', .1), ('one_percent', .01), ('zero', 0)]:
        indices = [i for i, r in enumerate(history) if r['cloud_fraction'] <= fraction]
        if indices:
            i = indices[0]
            lo, hi = history[i-1], history[i]
            crossing = dict(bracket_tau=[lo['tau'], hi['tau']])
            if fraction:
                crossing['linear_scalar_curve_estimate_tau'] = lo['tau'] + (hi['tau']-lo['tau']) * (
                    lo['cloud_fraction']-fraction)/(lo['cloud_fraction']-hi['cloud_fraction'])
            summary['thresholds'][label] = crossing
    if case['scheme'] == 'N':
        summary['provided_native_log_aggregate'] = json.loads((folder/'native_analysis.json').read_text())['runs'][0]
        summary['provided_native_log_aggregate'].pop('cloud_history')
    else:
        failure = json.loads((folder/'failure.json').read_text())
        raw = gzip.decompress((folder/'native_failure.log.gz').read_bytes())
        assert sha(raw) == failure['original_log_sha256']
        log = raw.decode(errors='replace')
        matches = re.findall(r'RD tetra stage inadmissible: stage=(\d+) ID=(\d+) rho=(\S+) p=(\S+)', log)
        stage, node, rho, p = matches[-1]
        sync = re.findall(r'Sync-Point (\d+), Time: ([^,\s]+), Systemstep: ([^,\s]+)', log)[-1]
        cfl = re.findall(r'RD-CFL-SELECT time=(\S+) current_mesh_raw=(\S+) courant_limit=(\S+) limiting_id=(\d+)', log)[-1]
        summary['failure'] = dict(stage=int(stage), node=int(node), rho=float(rho), pressure=float(p),
            sync=int(sync[0]), printed_time=float(sync[1]), printed_dt=float(sync[2]),
            last_courant_limit=float(cfl[2]), last_cfl_limiting_id=int(cfl[3]),
            failure_tau_inferred_from_tick=int(sync[0])*1.5/131072,
            uncompressed_log_sha256=sha(raw), last_diagnostic=re.findall(r'RD-DIAG[^\n]+', log)[-1])
    write_csv(out/f"{case['name']}.csv", history)
    return summary, history, states


def field_difference(q, reference, dual, cloud_excess):
    # q values are extensive. The fixed initial dual is used for both states.
    def primitive(a):
        rho = a[:, 0]/dual
        v = a[:, 1:4]/a[:, 0, None]
        p = (GAMMA-1)*(a[:, 4]/dual-.5*rho*(v*v).sum(axis=1))
        return rho, v, p
    r, v, p = primitive(q)
    rr, vv, pp = primitive(reference)
    dr = np.sum(dual*np.abs(r-rr))
    return dict(rho_relative_volume_L1=float(dr/np.sum(dual*rr)),
                rho_L1_per_initial_cloud_excess=float(dr/cloud_excess),
                rho_Linf_over_initial_cloud_density=float(np.max(np.abs(r-rr))/100),
                pressure_relative_volume_L1=float(np.sum(dual*np.abs(p-pp))/np.sum(dual*pp)),
                velocity_volume_RMS_over_wind=float(np.sqrt(np.sum(dual*np.sum((v-vv)**2, axis=1))/dual.sum())/WIND))


def source_audit(root):
    repo = Path(__file__).resolve().parents[2]
    result = {}
    for method in ['N', 'LDA']:
        provenance = json.loads((root/'provenance'/method/'source_provenance.json').read_text())
        differences, count = [], 0
        for p, h in provenance['tracked_and_untracked_hashes'].items():
            if p.startswith('src/') or p in ['Makefile', 'defines_extra']:
                r = subprocess.run(['git', 'show', provenance['base_commit']+':'+p],
                                   cwd=repo, capture_output=True)
                count += 1
                if r.returncode or sha(r.stdout) != h:
                    differences.append(p)
        assert not differences, differences
        result[method] = dict(base_commit=provenance['base_commit'],
            frozen_source_tar_sha256=provenance['source_tar_sha256'],
            source_build_files_checked=count, differences_from_base_commit=differences)
    return result


def plots(out, histories, states, comparison):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    from scipy.spatial import cKDTree
    plt.rcParams.update({'font.size': 10, 'axes.grid': False, 'svg.fonttype': 'none'})
    names = ['N_equal_np8', 'N_hier_np8']
    labels = ['Equal timesteps', 'Hierarchical timesteps']
    colors = ['#2468a0', '#d66625']
    def save(fig, name):
        for ext in ['png', 'svg']:
            path = out/f'{name}.{ext}'
            assert not path.exists()
            fig.savefig(path, dpi=190)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.3, 4.8), layout='constrained')
    for n, label, c, style in zip(names, labels, colors, ['-', '--']):
        h = histories[n]
        ax.plot([r['tau'] for r in h], [r['cloud_fraction'] for r in h], style,
                color=c, lw=2, label=label)
        ax.scatter([r['tau'] for r in h], [r['cloud_fraction'] for r in h], s=12,
                   color=c, marker='o' if n == names[0] else 'x')
    ax.axhline(.5, color='.65', lw=.8, ls=':')
    ax.set(xlim=(0, 1.5), ylim=(-.02, 1.04), xlabel=r'$t/t_{\rm cr}$',
           ylabel=r'$M_{\rm cloud}/M_{\rm cloud,0}$', title='COSMA static 3D Blob: N/RK2, 32³ vertices, 8 MPI ranks')
    secondary = ax.secondary_xaxis('top', functions=(lambda x: x/1.6, lambda x: x*1.6))
    secondary.set_xlabel(r'$t/t_{\rm KH}$, with $t_{\rm KH}=1.6t_{\rm cr}$')
    ax.legend(frameon=False, loc='upper right')
    ax.text(.98, .65, r'$\rho>64$ and $p/\rho<9$'+'\n140 initial cloud vertices\nNo material tracer',
            transform=ax.transAxes, ha='right', va='top', color='.3')
    save(fig, 'cloud_mass')

    fig, axes = plt.subplots(2, 2, figsize=(10, 6.8), layout='constrained')
    for n, label, c in zip(names, labels, colors):
        h = histories[n]; t = [r['tau'] for r in h]
        for k, style in [('mass', '-'), ('energy', '--')]:
            axes[0, 0].plot(t, [abs(r[f'drift_{k}']) for r in h], style, color=c, label=f'{label}: {k}')
        axes[0, 1].plot(t, [r['rho_max'] for r in h], color=c, ls='-' if n == names[0] else '--', label=label)
        axes[1, 0].plot(t, [r['cloud_vx'] if r['cloud_vx'] is not None else np.nan for r in h],
                        color=c, ls='-' if n == names[0] else '--')
    axes[0, 0].set_yscale('symlog', linthresh=1e-16)
    axes[0, 0].set(ylabel='Absolute normalized total drift', xlabel=r'$t/t_{\rm cr}$')
    axes[0, 0].legend(frameon=False, fontsize=8)
    axes[0, 1].axhline(64, color='.5', ls=':', lw=1)
    axes[0, 1].set(ylabel='Maximum nodal density', xlabel=r'$t/t_{\rm cr}$')
    axes[0, 1].legend(frameon=False, fontsize=8)
    axes[1, 0].set(ylabel='Threshold-selected gas: mean $v_x$', xlabel=r'$t/t_{\rm cr}$')
    axes[1, 0].text(.04, .94, 'Curve ends when selection becomes empty', transform=axes[1, 0].transAxes, va='top', fontsize=8)
    interp = comparison['time_interpolated']
    exact = comparison['exact_common_times']
    for key, label in [('rho_relative_volume_L1', r'$\rho$: relative $L_1$'),
                       ('pressure_relative_volume_L1', r'$p$: relative $L_1$'),
                       ('velocity_volume_RMS_over_wind', r'$v$: RMS / $v_{\rm wind}$')]:
        line, = axes[1, 1].semilogy([r['tau'] for r in interp if r['tau'] > 0],
                                   [r[key] for r in interp if r['tau'] > 0], label=label)
        axes[1, 1].scatter([r['tau'] for r in exact if r['tau'] > 0],
                           [r[key] for r in exact if r['tau'] > 0], s=24, marker='s', color=line.get_color())
    axes[1, 1].set(xlabel=r'$t/t_{\rm cr}$', ylabel='Hierarchy vs equal: volume-weighted difference')
    axes[1, 1].set_ylim(1e-6, 4e-5)
    axes[1, 1].legend(frameon=False, fontsize=8, loc='lower right')
    axes[1, 1].text(.04, .95, 'Lines: time interpolation of extensive Q\nSquares: exact common snapshot times',
                    transform=axes[1, 1].transAxes, va='top', fontsize=8)
    save(fig, 'diagnostics')

    initial = states[names[0]][0]
    tree = cKDTree(initial['Coordinates'], boxsize=10)
    grid = (np.arange(360)+.5)*10/360
    aa, bb = np.meshgrid(grid, grid)
    # Nearest-node rasters: no smoothed or reconstructed sub-grid structure.
    def indices(plane, coordinate):
        points = np.empty((aa.size, 3))
        dims, fixed = {'xy': ((0, 1), 2), 'xz': ((0, 2), 1), 'yz': ((1, 2), 0)}[plane]
        points[:, dims[0]], points[:, dims[1]] = aa.ravel(), bb.ravel()
        points[:, fixed] = coordinate
        return tree.query(points)[1].reshape(aa.shape)
    norm = LogNorm(7, 150)
    xy = indices('xy', 5.)
    fig, axes = plt.subplots(2, 4, figsize=(13, 6.7), layout='constrained')
    for row, name in enumerate(names):
        for col, i in enumerate([0, 10, 20, 30]):
            s = states[name][i]; ax = axes[row, col]
            im = ax.imshow(s['Density'][xy], origin='lower', extent=[0, 10, 0, 10],
                           norm=norm, cmap='magma', interpolation='nearest')
            ax.set_title(r'$t/t_{\rm cr}=$'+f"{s['time']/TCR:.6f}", fontsize=10)
            ax.set(xlabel='$x$', xticks=[0, 5, 10], yticks=[0, 5, 10])
            if col == 0:
                ax.set_ylabel(labels[row]+'\n$y$')
    fig.colorbar(im, ax=axes, label='Nodal density (periodic nearest-node raster)', shrink=.85)
    fig.suptitle('N/RK2 static 3D Blob: central XY plane, z = 5; shared density scale')
    save(fig, 'density_evolution')

    fig, axes = plt.subplots(3, 3, figsize=(9.5, 9.8), layout='constrained')
    for col, i in enumerate([10, 20, 30]):
        s = states[names[0]][i]
        peak_x = s['Coordinates'][s['Density'].argmax(), 0]
        for row, (plane, val, dims) in enumerate([('xy', 5., ('x', 'y')), ('xz', 5., ('x', 'z')), ('yz', peak_x, ('y', 'z'))]):
            ax = axes[row, col]
            im = ax.imshow(s['Density'][indices(plane, val)], origin='lower', extent=[0, 10, 0, 10],
                           norm=norm, cmap='magma', interpolation='nearest')
            fixed = {'xy': 'z', 'xz': 'y', 'yz': 'x'}[plane]
            ax.set_title(f'{plane.upper()}, {fixed}={val:.3f}', fontsize=9)
            ax.set(xlabel=f'${dims[0]}$', ylabel=f'${dims[1]}$', xticks=[0, 5, 10], yticks=[0, 5, 10])
            if row == 0:
                ax.text(.5, 1.18, r'$t/t_{\rm cr}=$'+f"{s['time']/TCR:.6f}", transform=ax.transAxes, ha='center')
    fig.colorbar(im, ax=axes, label='Nodal density (periodic nearest-node raster)', shrink=.85)
    fig.suptitle('Equal-timestep N/RK2: three planes\nYZ plane follows the x coordinate of the density maximum')
    save(fig, 'density_planes')

    fig, axes = plt.subplots(2, 3, figsize=(10.8, 7.2), layout='constrained')
    fields = [('Density', 'Density', norm, 'magma'),
              ('Pressure', 'Pressure', plt.Normalize(30, 360), 'viridis'),
              ('Mach', r'Local speed / sound speed', plt.Normalize(0, 2.5), 'cividis')]
    for col, (field, label, scale, cmap) in enumerate(fields):
        for row, i in enumerate([5, 15]):
            s = states[names[0]][i]
            value = (np.linalg.norm(s['Velocities'], axis=1) /
                     np.sqrt(GAMMA*s['Pressure']/s['Density'])) if field == 'Mach' else s[field]
            ax = axes[row, col]
            im = ax.imshow(value[xy], origin='lower', extent=[0, 10, 0, 10],
                           norm=scale, cmap=cmap, interpolation='nearest')
            ax.set(xlabel='$x$', ylabel='$y$', xticks=[0, 5, 10], yticks=[0, 5, 10])
            ax.set_title(r'$t/t_{\rm cr}=$'+f"{s['time']/TCR:.6f}")
        fig.colorbar(im, ax=axes[:, col], label=label, orientation='horizontal', shrink=.9)
    fig.suptitle('Equal-timestep N/RK2: wind-cloud interaction, XY plane at z = 5\nPeriodic nearest-node rasters; no spatial smoothing')
    save(fig, 'flow_structure')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root, out = args.bundle.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((root/'bundle.json').read_text())
    assert manifest['tcr'] == TCR and manifest['gamma'] == GAMMA
    summaries, histories, states = {}, {}, {}
    for case in manifest['cases']:
        n = case['name']
        summaries[n], histories[n], states[n] = analyse_case(root, case, out)
    equal, hier = states['N_equal_np8'], states['N_hier_np8']
    initial = equal[0]
    for seq in states.values():
        for k in ['Coordinates', 'Density', 'Pressure', 'Masses', 'Velocities', 'InternalEnergy', 'ParticleIDs']:
            np.testing.assert_array_equal(seq[0][k], initial[k])
    with h5py.File(root/'inputs/blob32.hdf5') as f:
        gas = f['PartType0']; o = np.argsort(gas['ParticleIDs'][:])
        x, rho = gas['Coordinates'][:][o], gas['Masses'][:][o]
        expected = np.random.default_rng(68315).uniform(0, 10, (32**3, 3))
        np.testing.assert_array_equal(x, expected)
        np.testing.assert_array_equal(initial['Coordinates'], x)
        np.testing.assert_allclose(initial['Density'], rho, rtol=1e-15)
        assert np.count_nonzero(rho == 100) == 140
    dual = initial['dual']
    excess = np.sum(dual*(initial['Density']-10))
    et = np.array([s['time'] for s in equal])
    comparison = dict(exact_common_times=[], time_interpolated=[])
    for s in hier:
        t = s['time']
        exact = np.where(et == t)[0]
        if len(exact):
            q = equal[exact[0]]['q']
            comparison['exact_common_times'].append(dict(tau=t/TCR,
                **field_difference(s['q'], q, dual, excess)))
        else:
            j = int(np.searchsorted(et, t))
            f = (t-et[j-1])/(et[j]-et[j-1])
            q = (1-f)*equal[j-1]['q']+f*equal[j]['q']
        comparison['time_interpolated'].append(dict(tau=t/TCR,
            **field_difference(s['q'], q, dual, excess)))
    comparison['max_same_index_time_offset_over_tcr'] = max(abs(a['time']-b['time'])/TCR for a, b in zip(equal, hier))
    comparison['max_same_index_cloud_fraction_difference'] = max(abs(a['cloud_fraction']-b['cloud_fraction'])
        for a, b in zip(histories['N_equal_np8'], histories['N_hier_np8']))
    result = dict(tcr=TCR, tkh=1.6*TCR, setup=dict(box=10, seed=68315,
        initial_cloud_nodes=140, nominal_diameter_in_mean_spacings=2/(10/32),
        wind=WIND, wind_mach=WIND/np.sqrt(GAMMA*100/10),
        initial_cloud_mass=histories['N_equal_np8'][0]['cloud_mass'],
        analytic_cloud_mass=100*4*np.pi/3, initial_density_excess_mass=float(excess),
        dual_to_voronoi_ratio_percentiles=np.percentile(dual/initial['Volume'], [0, 5, 50, 95, 100]).tolist()),
        source_audit=source_audit(root), cases=summaries, comparison=comparison,
        observed_equal_to_hier_wall_ratio=summaries['N_equal_np8']['wall_seconds']/summaries['N_hier_np8']['wall_seconds'],
        caveats=['No material tracer; cloud is rho>64 and p/rho<9.',
                 'Only saved N states independently establish positivity/conservation here; full native N logs are absent.',
                 'Non-common output times require interpolation, not an exact solver comparison.',
                 'One resolution and one MPI rank count for the full Blob do not establish convergence or MPI scaling.',
                 'Binaries and frozen source tar bytes are absent; source audit checks supplied file hashes against Git.'])
    write_json(out/'independent_analysis.json', result)
    write_csv(out/'exact_common_times.csv', comparison['exact_common_times'])
    write_csv(out/'time_interpolated_comparison.csv', comparison['time_interpolated'])
    plots(out, histories, states, comparison)
    print(json.dumps({k: {q: v for q, v in s.items() if q in ['end_tau', 'all_saved_minimum',
        'max_abs_normalized_drift', 'thresholds', 'failure']} for k, s in summaries.items()}, indent=2))


if __name__ == '__main__':
    main()
