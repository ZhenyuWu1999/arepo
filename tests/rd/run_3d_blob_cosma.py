#!/usr/bin/env python3
"""Frozen COSMA static 3D Blob campaign: feature gates, timing and long runs.

Prepare/analyse are light Python tasks. Build/run require a Slurm compute node.
N/lumped and LDA/F1 use the current RK2 path and the same Morton-inspired IC.
Neither configuration reproduces the paper's N1 update.
Each group/case can run once; use a new campaign directory for failed retries.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time

import h5py
import numpy as np
from run_3d_blob_pilot import BOX, GAMMA, TCR, WIND, make_ic
from run_3d_static_gates import REPO, VELOCITY, density, freeze, initial_conditions, state
from run_n_gauss3_split import ENV, rewrite, sha, write

ENV.update(MKL_NUM_THREADS='1', OMPI_MCA_btl_vader_single_copy_mechanism='none')


def prepare(root, n, fraction, ranks, schemes):
    schemes = list(dict.fromkeys(schemes))
    if n < 16 or fraction <= 0 or ranks < 1:
        raise ValueError('Require n >= 16, positive duration and rank count')
    root.mkdir(parents=True, exist_ok=False)
    freeze(root)
    for folder in ('configs', 'inputs', 'runs', 'artifacts'):
        (root/folder).mkdir()
    methods = [scheme+'_'+stepping for scheme in schemes for stepping in ('equal', 'hier')]
    for method in methods:
        scheme, stepping = method.split('_')
        filename = f'Config_{scheme}_'+('static' if stepping == 'equal' else 'hierarchical')+'.sh'
        config = (REPO/'examples/rd_3d'/filename).read_text().replace('GAMMA=1.4', 'GAMMA=1.6666666666666667')
        (root/'configs'/f'{method}.sh').write_text(config)
        for header in (root/'source/src').rglob('*.h'):
            (root/'build'/method/header.relative_to(root/'source/src').parent).mkdir(parents=True, exist_ok=True)
    cases = []

    def add(group, family, resolution, problem, method, tasks, end, cap, cfl, snapshots):
        name = f'{group}_{problem}{resolution}_{method}_np{tasks}'
        folder = root/'runs'/name
        folder.mkdir()
        ic = root/'inputs'/f'{problem}{resolution}.hdf5'
        box = BOX if family == 'blob' else 1.
        param = rewrite((REPO/'examples/rd_3d/param.txt').read_text(), dict(
            InitCondFile=ic.with_suffix(''), OutputDir=str(folder/'output')+'/',
            BoxSize=box, TimeMax=end, MaxSizeTimestep=cap, CourantFac=cfl,
            TimeBetSnapshot=end/snapshots, TimeBetStatistics=end/snapshots,
            CpuTimeBetRestartFile=1e9, TimeLimitCPU=1e9, MaxMemSize=1024))
        (folder/'param.txt').write_text(param)
        cases.append(dict(name=name, group=group, family=family, n=resolution,
            nodes=resolution**3, problem=problem, method=method, ranks=tasks,
            box=box, gamma=GAMMA, end=end, cap=cap, cfl=cfl,
            ic=str(ic), ic_sha256=sha(ic), param_sha256=sha(folder/'param.txt')))

    for problem in ('uniform', 'advection', 'pressure_patch'):
        ic = root/'inputs'/f'{problem}8.hdf5'
        initial_conditions(ic, 8, 'uniform' if problem == 'pressure_patch' else problem)
        with h5py.File(ic, 'r+') as f:
            g = f['PartType0']
            pressure = np.ones(512)
            if problem == 'pressure_patch':
                pressure += 8*np.exp(-np.sum((g['Coordinates'][:]-.5)**2, axis=1)/.12**2)
            g['InternalEnergy'][:] = pressure/((GAMMA-1)*g['Masses'][:])
    # A small cap makes all bins equal for a direct hierarchy degeneration gate.
    for scheme in schemes:
        for problem in ('uniform', 'advection'):
            add('gates', 'control', 8, problem, scheme+'_equal', 1, 8/2**18, 1/2**18, .2, 2)
            for tasks in (1, 2, 4):
                add('gates', 'control', 8, problem, scheme+'_hier', tasks, 8/2**18, 1/2**18, .2, 2)
        for tasks in (1, 2, 4):
            add('gates', 'control', 8, 'pressure_patch', scheme+'_hier', tasks, .03125, 1/64, .2, 2)
    cloud_nodes = {}
    for resolution in sorted({16, n}):
        cloud_nodes[str(resolution)] = make_ic(root/'inputs'/f'blob{resolution}.hdf5', resolution)
    for scheme in schemes:
        equal, hier = scheme+'_equal', scheme+'_hier'
        for method, tasks in [(equal, 1), (hier, 1), (hier, 2), (hier, 4)]:
            add('gates', 'blob', 16, 'blob', method, tasks, .01*TCR, .01*TCR/4, .01, 2)
        for method, tasks in [(equal, 1), (hier, 1), (hier, 2), (hier, 4), (hier, ranks), (equal, ranks)]:
            name = f'calibration_blob{n}_{method}_np{tasks}'
            if not any(c['name'] == name for c in cases):
                add('calibration', 'blob', n, 'blob', method, tasks, .001*TCR, .001*TCR/4, .01, 2)
    for method in methods:
        add('full', 'blob', n, 'blob', method, ranks, fraction*TCR, fraction*TCR/4, .01, 30)
    write(root/'campaign.json', dict(description=__doc__, schemes=schemes, methods=methods, cases=cases,
        n=n, fraction_tcr=fraction, production_ranks=ranks, cloud_nodes=cloud_nodes,
        seed=68315, gamma=GAMMA, tcr=TCR, tkh=1.6*TCR, box=BOX,
        cloud_center=[2.5, 5., 5.], radius=1., rho_cloud=100., rho_wind=10.,
        pressure=100., wind_speed=WIND, actual_mach=WIND/np.sqrt(GAMMA*100/10),
        norm='Median-dual volume = Masses/Density; q = mass, three momenta, total energy',
        cloud_selection='rho > 64 and p/rho < 9; no passive material tracer',
        restart='No timed checkpoint/CPU stop: hierarchy may hold unfinished stages',
        python=dict(version=os.sys.version, numpy=np.__version__, h5py=h5py.__version__),
        host=socket.gethostname(), runner_repo=str(REPO),
        systype_sha256=sha(root/'source/Makefile.systype'),
        source_tar_sha256=sha(root/'source.tar')))
    print('Prepared', root, len(cases), 'cases; cloud nodes', cloud_nodes, flush=True)


def compute_node():
    if not os.environ.get('SLURM_JOB_ID') or socket.gethostname().startswith('login'):
        raise RuntimeError('Build/run must execute on a Slurm compute node')


def build(root, jobs):
    compute_node()
    campaign = json.loads((root/'campaign.json').read_text())
    source_meta = json.loads((root/'source_provenance.json').read_text())
    # Audit the frozen compilation inputs against the source archive manifest.
    for name, checksum in source_meta['tracked_and_untracked_hashes'].items():
        if name.startswith('src/') or name in ('Makefile', 'Template-Config.sh'):
            assert sha(root/'source'/name) == checksum, name
    assert sha(root/'source.tar') == campaign['source_tar_sha256']
    assert sha(root/'source/Makefile.systype') == campaign['systype_sha256']
    for method in campaign['methods']:
        artifact = root/'artifacts'/method
        artifact.mkdir(exist_ok=False)
        work = root/'build'/method
        config = root/'configs'/f'{method}.sh'
        command = ['make', f'CONFIG={config}', f'BUILD_DIR={work}', f'EXEC={work}/Arepo', f'-j{jobs}']
        start = time.monotonic()
        with (artifact/'build.log').open('x') as log:
            result = subprocess.run(command, cwd=root/'source', env=ENV, stdout=log, stderr=subprocess.STDOUT)
        meta = dict(command=command, returncode=result.returncode, seconds=time.monotonic()-start,
            host=socket.gethostname(), slurm_job_id=os.environ['SLURM_JOB_ID'])
        write(artifact/'build_status.json', meta)
        if result.returncode:
            raise RuntimeError(f'Build failed: {artifact}/build.log')
        for src, dest in [(work/'Arepo', 'Arepo'), (work/'arepoconfig.h', 'arepoconfig.h.used'),
                          (work/'version.c', 'version.c'), (config, 'Config.used')]:
            shutil.copy2(src, artifact/dest)
        (artifact/'Arepo').chmod(0o555)
        linkage = subprocess.check_output(['ldd', str(artifact/'Arepo')], text=True)
        (artifact/'binary.ldd.txt').write_text(linkage)
        assert 'not found' not in linkage and 'libmkl_rt' in linkage
        binary_hash = sha(artifact/'Arepo')
        (artifact/'binary.sha256').write_text(binary_hash+'  Arepo\n')
        meta.update(binary_sha256=binary_hash, config_sha256=sha(config),
            header_sha256=sha(artifact/'arepoconfig.h.used'), source_tar_sha256=sha(root/'source.tar'),
            compiler=subprocess.check_output(['mpicc', '-show'], text=True).strip())
        write(artifact/'provenance.json', meta)
        (artifact/'manifest.txt').write_text('\n'.join([
            f"git_commit={source_meta['base_commit']}", f'source_archive={root}/source.tar',
            f"source_tar_sha256={meta['source_tar_sha256']}", f'config_sha256={sha(config)}',
            'lapack_backend=mkl', f'build_host={socket.gethostname()}',
            f"slurm_job_id={os.environ['SLURM_JOB_ID']}", f"mpicc_show={meta['compiler']}"])+ '\n')
        print('BUILT', method, meta['seconds'], binary_hash, flush=True)


def selected_cases(root, group, selected):
    cases = [c for c in json.loads((root/'campaign.json').read_text())['cases'] if c['group'] == group]
    if selected:
        names = {c['name'] for c in cases}
        if not set(selected) <= names:
            raise ValueError(f'Unknown cases: {set(selected)-names}')
        cases = [c for c in cases if c['name'] in selected]
    return cases


def run(root, group, selected):
    compute_node()
    runner = Path(json.loads((root/'campaign.json').read_text())['runner_repo'])
    assert sha(runner/'run_case.sh') == sha(root/'source/run_case.sh')
    for prerequisite in (['gates'] if group == 'calibration' else ['gates', 'calibration'] if group == 'full' else []):
        assert json.loads((root/f'{prerequisite}_results.json').read_text())['passed'], prerequisite
    for case in selected_cases(root, group, selected):
        folder = root/'runs'/case['name']
        assert not (folder/'run.log').exists() and not (folder/'output').exists(), 'Use a new archive for retries'
        assert case['ranks'] <= int(os.environ['SLURM_NTASKS'])
        binary = root/'artifacts'/case['method']/'Arepo'
        provenance = json.loads((binary.parent/'provenance.json').read_text())
        assert sha(binary) == provenance['binary_sha256']
        assert sha(case['ic']) == case['ic_sha256'] and sha(folder/'param.txt') == case['param_sha256']
        # Use the managed Linux launcher and its per-output provenance records.
        command = [str(runner/'run_case.sh'), '--binary', str(binary), '--param', str(folder/'param.txt'), '--tasks', str(case['ranks'])]
        start = time.monotonic()
        print('RUN', case['name'], flush=True)
        with (folder/'run.log').open('x') as log:
            result = subprocess.run(command, cwd=runner, env=ENV, stdout=log, stderr=subprocess.STDOUT)
        write(folder/'run_status.json', dict(returncode=result.returncode, seconds=time.monotonic()-start,
            command=command, host=socket.gethostname(), slurm_job_id=os.environ['SLURM_JOB_ID'],
            binary_sha256=sha(binary), threads={k: ENV[k] for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')}))
        print('FINISHED', case['name'], result.returncode, time.monotonic()-start, flush=True)
        if result.returncode:
            raise RuntimeError(f"Numerical/setup failure: {folder}; preserved, remaining cases not launched")


def analyse(root, group, selected):
    campaign = json.loads((root/'campaign.json').read_text())
    rows, finals, endpoints = [], {}, {}
    for case in selected_cases(root, group, selected):
        folder = root/'runs'/case['name']
        status = json.loads((folder/'run_status.json').read_text())
        assert status['returncode'] == 0, case['name']
        states = [state(p) for p in sorted((folder/'output').glob('snap_*.hdf5'))]
        a, b = states[0], states[-1]
        assert a['time'] == 0 and abs(b['time']-case['end']) < 1e-14
        scale = np.abs(a['q']).sum(axis=0)
        scale[1:4] = np.maximum(scale[1:4], scale[0])
        conservation = max(float(np.max(abs(s['q'].sum(axis=0)-a['q'].sum(axis=0))/scale)) for s in states)
        coverage = max(float(abs(s['dual'].sum()/case['box']**3-1)) for s in states)
        assert conservation < 1e-12 and coverage < 1e-12, (case['name'], conservation, coverage)
        for s in states:
            assert all(np.isfinite(s[k]).all() for k in ('rho', 'p', 'v', 'q', 'dual'))
            assert min(s['rho'].min(), s['p'].min(), s['dual'].min()) > 0
            np.testing.assert_array_equal(s['id'], a['id'])
            np.testing.assert_array_equal(s['x'], a['x'])
        logs = sorted((folder/'output').glob('arepo-*.log'))
        assert len(logs) == 1
        log = logs[0].read_text()
        times = np.array([float(t) for t in re.findall(r'RD-3D-STAGE time=(\S+) stage=1', log)])
        assert len(times) and np.all(np.diff(times) > 0)
        ratio = max([int(x) for x in re.findall(r'max_ratio=(\d+)', log)] or [1])
        row = dict(case=case['name'], seconds=status['seconds'], end=b['time'],
            conservation=conservation, coverage=coverage, snapshots=len(states),
            stage1_records=len(times), max_bin_ratio=ratio,
            rho_min=float(b['rho'].min()), p_min=float(b['p'].min()))
        if case['problem'] == 'uniform':
            row['uniform_defect'] = max(float(np.max(abs(s[k]-a[k]))) for s in states for k in ('rho', 'p', 'v'))
            assert row['uniform_defect'] < 1e-12
        if case['problem'] == 'advection':
            exact = density(b['x']-VELOCITY*b['time'])
            row['density_L1'] = float(np.sum(b['dual']*abs(b['rho']-exact)))
        if case['problem'] == 'pressure_patch':
            assert ratio >= 2, (case['name'], 'Expected actual mixed bins')
        if case['family'] == 'blob':
            history = [dict(time=s['time'], t_over_tcr=s['time']/TCR,
                mass=float(s['mass'][(s['rho'] > 64) & (s['p']/s['rho'] < 9)].sum())) for s in states]
            assert history[0]['mass'] > 0
            row.update(cloud_history=history, cloud_mass_fraction=history[-1]['mass']/history[0]['mass'])
            if case['method'].endswith('_hier'):
                assert ratio >= 2, (case['name'], 'Expected actual mixed bins')
            if group == 'calibration':
                row['projected_full_hours'] = status['seconds']*campaign['fraction_tcr']/.001/3600
        if case['method'].endswith('equal'):
            dt = np.diff(np.r_[0., times])
            row.update(dt_min=float(dt.min()), dt_max=float(dt.max()))
        rows.append(row)
        finals[case['name']], endpoints[case['name']] = b, times
    comparisons = {}
    for case in selected_cases(root, group, selected):
        name = case['name']
        reference = re.sub(r'_np\d+$', '_np1', name)
        if case['family'] == 'control' and case['problem'] in ('uniform', 'advection'):
            reference = reference.replace('_hier_', '_equal_')
            assert next(r for r in rows if r['case'] == name)['max_bin_ratio'] == 1
        if reference == name or reference not in finals:
            continue
        a, b = finals[reference], finals[name]
        np.testing.assert_array_equal(a['id'], b['id'])
        np.testing.assert_array_equal(a['x'], b['x'])
        differences = {k: float(np.max(abs(b[k]-a[k])/np.maximum(1., abs(a[k])))) for k in ('rho', 'p', 'v', 'q', 'dual')}
        assert max(differences.values()) < 1e-9, (name, differences)
        np.testing.assert_array_equal(endpoints[name], endpoints[reference])
        comparisons[name] = dict(reference=reference, max_scaled_field_differences=differences, identical_stage1_times=True)
    # Concurrent full jobs must each retain their own analysis.
    destination = (root/'runs'/selected[0]/'analysis.json' if selected and len(selected) == 1
                   else root/(f'{group}_selected_results.json' if selected else f'{group}_results.json'))
    write(destination, dict(passed=True, runs=rows, comparisons=comparisons))
    print(json.dumps(dict(passed=True, runs=rows, comparisons=comparisons), indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'build', 'run', 'analyse'])
    parser.add_argument('root', type=Path)
    parser.add_argument('--n', type=int, default=32)
    parser.add_argument('--schemes', nargs='+', choices=['N', 'LDA'], default=['N', 'LDA'])
    parser.add_argument('--fraction-tcr', type=float, default=1.5)
    parser.add_argument('--ranks', type=int, default=8)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--group', choices=['gates', 'calibration', 'full'], default='gates')
    parser.add_argument('--select', nargs='+')
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action == 'prepare':
        prepare(root, args.n, args.fraction_tcr, args.ranks, args.schemes)
    elif args.action == 'build':
        build(root, args.jobs)
    elif args.action == 'run':
        run(root, args.group, args.select)
    else:
        analyse(root, args.group, args.select)
