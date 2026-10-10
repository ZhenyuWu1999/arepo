#!/usr/bin/env python3
"""Freeze/build/run/analyse initial native AREPO 3D static N gates.

One rank; periodic unit cube; deterministic 8^3/16^3 jittered grids (seed 912+n,
jitter +/-0.12 spacing per axis); gamma 1.4; N/lumped RK2. These are initial
integration gates, not a complete convergence or positivity campaign.
"""
import argparse
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time

import h5py
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'examples/Sedov_2d'))
from run_hllc import freeze
from run_n_gauss3_split import ENV, sha, write, rewrite, build

VELOCITY = np.array([.3, -.2, .4])


def density(x):
    return 1+.1*np.prod(np.sin(2*np.pi*x), axis=1)


def initial_conditions(path, n, problem):
    rng = np.random.default_rng(912+n)
    x = (np.stack(np.meshgrid(*([np.arange(n)]*3), indexing='ij'), axis=-1).reshape(-1, 3)+.5)/n
    x += rng.uniform(-.12, .12, x.shape)/n
    count = len(x)
    rho, p = np.ones(count), np.ones(count)
    v = np.tile(VELOCITY, (count, 1))
    if problem == 'rest':
        v[:] = 0
    elif problem == 'pressure_rest':
        v[:] = 0
        p += .01*np.prod(np.cos(2*np.pi*x), axis=1)
    elif problem == 'advection':
        rho = density(x)
    elif problem != 'uniform':
        raise ValueError(problem)
    with h5py.File(path, 'w') as f:
        header = f.create_group('Header'); gas = f.create_group('PartType0')
        counts = np.array([count, 0, 0, 0, 0, 0], dtype=np.uint32)
        attrs = dict(NumPart_ThisFile=counts, NumPart_Total=counts, NumPart_Total_HighWord=np.zeros(6, np.uint32),
                     MassTable=np.zeros(6), Time=0., Redshift=0., BoxSize=1., NumFilesPerSnapshot=1,
                     Omega0=0., OmegaB=0., OmegaLambda=0., HubbleParam=1., Flag_Sfr=0, Flag_Cooling=0,
                     Flag_StellarAge=0, Flag_Metals=0, Flag_Feedback=0, Flag_DoublePrecision=1)
        for key, value in attrs.items():
            header.attrs[key] = value
        for key, value in dict(Coordinates=x, Velocities=v, Masses=rho, InternalEnergy=p/(.4*rho),
                               ParticleIDs=np.arange(1, count+1, dtype=np.uint64)).items():
            gas.create_dataset(key, data=value)


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    freeze(root)
    for folder in ('configs', 'inputs', 'runs', 'artifacts'):
        (root/folder).mkdir()
    config = (REPO/'examples/rd_3d/Config_N_static.sh').read_text()
    configs = dict(N=config, N_svd=config+'\nRD_ALWAYS_PSEUDOINVERSE\n')
    for method, cfg in configs.items():
        (root/'configs'/f'{method}.sh').write_text(cfg)
        for header in (root/'source/src').rglob('*.h'):
            (root/'build'/method/header.relative_to(root/'source/src').parent).mkdir(parents=True, exist_ok=True)
    specs = [(8, 'rest', 'N', 1/512), (8, 'uniform', 'N', 1/512),
             (8, 'pressure_rest', 'N', 1/512), (8, 'advection', 'N', 1/512),
             (16, 'advection', 'N', 1/512), (16, 'advection', 'N', 1/4096),
             (8, 'advection', 'N_svd', 1/512)]
    cases = []
    for n, problem, method, cap in specs:
        name = f'{problem}_{n}_{method}_dt{round(1/cap)}'
        folder = root/'runs'/name; folder.mkdir()
        ic = root/'inputs'/f'{problem}_{n}.hdf5'
        if not ic.exists():
            initial_conditions(ic, n, problem)
        param = rewrite((REPO/'examples/rd_3d/param.txt').read_text(),
                        dict(InitCondFile=ic.with_suffix(''), OutputDir=str(folder/'output')+'/', MaxSizeTimestep=cap))
        (folder/'param.txt').write_text(param)
        cases.append(dict(name=name, method=method, problem=problem, n=n, cap=cap, end=.03125,
                          ic=str(ic), ic_sha256=sha(ic), param_sha256=sha(folder/'param.txt')))
    write(root/'campaign.json', dict(description=__doc__, methods=list(configs), cases=cases,
                                   gamma=1.4, ranks=1, velocity=VELOCITY.tolist()))


def run(root, selected):
    for case in json.loads((root/'campaign.json').read_text())['cases']:
        if selected and case['name'] not in selected:
            continue
        folder = root/'runs'/case['name']; artifact = root/'artifacts'/case['method']
        assert not (folder/'run_status.json').exists(), 'Use a new archive for reruns'
        provenance = json.loads((artifact/'provenance.json').read_text())
        assert sha(artifact/'Arepo') == provenance['binary_sha256']
        assert sha(case['ic']) == case['ic_sha256']
        assert sha(folder/'param.txt') == case['param_sha256']
        print('RUN', case['name'], flush=True)
        start = time.monotonic()
        command = [str(artifact/'Arepo'), 'param.txt']
        with (folder/'run.log').open('w') as log:
            result = subprocess.run(command, cwd=folder, env=ENV, stdout=log, stderr=subprocess.STDOUT)
        write(folder/'run_status.json', dict(returncode=result.returncode, seconds=time.monotonic()-start,
                                            command=command, threads={k: ENV[k] for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS')}))
        assert result.returncode == 0, folder


def state(path):
    with h5py.File(path) as f:
        g = f['PartType0']; ids = g['ParticleIDs'][:]; order = np.argsort(ids)
        mass, rho = g['Masses'][:][order], g['Density'][:][order]
        v, internal = g['Velocities'][:][order], g['InternalEnergy'][:][order]
        q = np.column_stack([mass, mass[:, None]*v, mass*(internal+.5*(v*v).sum(axis=1))])
        return dict(time=float(f['Header'].attrs['Time']), id=ids[order], x=g['Coordinates'][:][order],
                    mass=mass, rho=rho, v=v, p=g['Pressure'][:][order], dual=mass/rho, q=q)


def analyse(root, selected):
    results = []
    final = {}
    steps = {}
    for case in json.loads((root/'campaign.json').read_text())['cases']:
        if selected and case['name'] not in selected:
            continue
        folder = root/'runs'/case['name']
        assert json.loads((folder/'run_status.json').read_text())['returncode'] == 0
        snapshots = sorted((folder/'output').glob('snap_*.hdf5'))
        log = (folder/'run.log').read_text()
        endpoints = np.array([float(t) for t in re.findall(r'RD-3D-STAGE time=(\S+) stage=1', log)])
        assert len(endpoints) > 0 and endpoints[-1] == case['end']
        dt = np.diff(np.r_[0., endpoints])
        assert np.all(dt > 0)
        steps[case['name']] = dt
        states = [state(p) for p in snapshots]; a, b = states[0], states[-1]
        assert a['time'] == 0. and b['time'] == case['end'], (case['name'], b['time'])
        scale = np.abs(a['q']).sum(axis=0)
        # Use total mass as the absolute momentum scale when momentum is zero.
        scale[1:4] = np.maximum(scale[1:4], scale[0])
        conservation = max(float(np.max(abs(s['q'].sum(axis=0)-a['q'].sum(axis=0))/scale)) for s in states)
        coverage = max(float(abs(s['dual'].sum()-1)) for s in states)
        assert conservation < 1e-12 and coverage < 1e-12, (case['name'], conservation, coverage)
        for s in states:
            assert all(np.isfinite(s[k]).all() for k in ('rho', 'p', 'v', 'q'))
            assert np.all(s['rho'] > 0) and np.all(s['p'] > 0)
            np.testing.assert_array_equal(s['x'], a['x'])
        r = dict(case=case['name'], end=b['time'], snapshots=len(states), conservation=conservation,
                 coverage=coverage, rho_min=float(b['rho'].min()), p_min=float(b['p'].min()),
                 steps=len(dt), actual_dt_min=float(dt.min()), actual_dt_max=float(dt.max()),
                 tetra_counts=sorted(set(int(n) for n in re.findall(r'RD-3D-STAGE .*? tetra=(\d+)', log))))
        if case['problem'] in ('rest', 'uniform'):
            r['uniform_defect'] = max(float(abs(s[k]-a[k]).max()) for s in states for k in ('rho', 'p', 'v'))
            assert r['uniform_defect'] < 1e-12, r
        if case['problem'] == 'advection':
            exact = density(b['x']-VELOCITY*b['time'])
            r['density_L1'] = float(np.sum(b['dual']*abs(b['rho']-exact)))
            r['density_L2'] = float(np.sqrt(np.sum(b['dual']*(b['rho']-exact)**2)))
        final[case['name']] = b
        results.append(r)
        print(r)
    if not selected:
        results_by_name = {r['case']: r for r in results}
        coarse = results_by_name['advection_8_N_dt512']['density_L1']
        fine = results_by_name['advection_16_N_dt512']['density_L1']
        assert fine < coarse, (coarse, fine)
        base = final['advection_8_N_dt512']; svd = final['advection_8_N_svd_dt512']
        difference = max(float(np.max(abs(base[k]-svd[k]))) for k in ('rho', 'v', 'p'))
        assert difference < 1e-10, difference
        base_dt = steps['advection_16_N_dt512']
        half_dt = steps['advection_16_N_dt4096']
        # Caps alone are insufficient: require the ACTUAL timestep to halve.
        assert len(half_dt) == 2*len(base_dt)
        np.testing.assert_allclose(half_dt, np.repeat(base_dt/2, 2), rtol=0, atol=1e-14)
        write(root/'comparisons.json', dict(coarse_to_fine_L1_ratio=coarse/fine,
              observed_two_grid_order=float(np.log2(coarse/fine)), LU_vs_SVD_max=difference,
              dt_sensitivity={k: float(np.max(abs(final['advection_16_N_dt512'][k]-final['advection_16_N_dt4096'][k])))
                              for k in ('rho', 'v', 'p')},
              caveat='Two jittered grids and two caps are initial trends, not a formal convergence proof.'))
    write(root/('results_selected.json' if selected else 'results.json'), results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'build', 'run', 'analyse', 'all'])
    parser.add_argument('root', type=Path)
    parser.add_argument('--select', nargs='+')
    args = parser.parse_args(); root = args.root.resolve()
    if args.action in ('prepare', 'all'):
        prepare(root)
    if args.action in ('build', 'all'):
        build(root, args.select)
    if args.action in ('run', 'all'):
        run(root, args.select)
    if args.action in ('analyse', 'all'):
        analyse(root, args.select)
