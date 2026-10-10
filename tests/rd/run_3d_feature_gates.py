#!/usr/bin/env python3
"""Immutable native 3D static N/LDA, hierarchy and MPI integration gates.

Unit cube, gamma 1.4, jittered grids from run_3d_static_gates. Each case records
ranks, timestep cap and scheme; mass/three momenta/energy, full stage positivity,
fixed coordinates and equal-bin degeneration are checked independently.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time

import h5py
import numpy as np
from run_3d_static_gates import REPO, initial_conditions, density, VELOCITY, state, freeze
from run_n_gauss3_split import ENV, write, rewrite, sha, build


def feature_ic(path, n, problem):
    if problem != 'pressure_patch':
        return initial_conditions(path, n, problem)
    initial_conditions(path, n, 'uniform')
    with h5py.File(path, 'r+') as f:
        x = f['PartType0/Coordinates'][:]
        pressure = 1 + 8*np.exp(-np.sum((x-.5)**2, axis=1)/.12**2)
        f['PartType0/InternalEnergy'][:] = pressure/.4


def prepare(root, suite):
    root.mkdir(parents=True, exist_ok=False); freeze(root)
    for name in ('configs', 'inputs', 'runs', 'artifacts'):
        (root/name).mkdir()
    ncfg = (REPO/'examples/rd_3d/Config_N_static.sh').read_text()
    lcfg = (REPO/'examples/rd_3d/Config_LDA_static.sh').read_text()
    configs = {'N': ncfg, 'LDA': lcfg, 'LDA_svd': lcfg+'\nRD_ALWAYS_PSEUDOINVERSE\n'}
    if suite in ('features','natural'):
        for scheme, cfg in [('N', ncfg), ('LDA', lcfg)]:
            configs[scheme+'_hier_equal'] = cfg+'\nRD_HIERARCHICAL_TIMESTEPS\n'
            configs[scheme+'_hier_pattern'] = cfg.replace('FORCE_EQUAL_TIMESTEPS\n', '')+'\nRD_HIERARCHICAL_TIMESTEPS\nRD_HIERARCHICAL_TEST_PATTERN\n'
            configs[scheme+'_hier_natural'] = cfg.replace('FORCE_EQUAL_TIMESTEPS\n', '')+'\nRD_HIERARCHICAL_TIMESTEPS\n'
    specs = [(8,p,m,1/512,1) for m in ('LDA','LDA_svd') for p in ('rest','uniform','pressure_rest','advection')]
    specs += [(16,'advection',m,1/512,1) for m in ('N','LDA')]+[(16,'advection','LDA',1/4096,1), (8,'advection','N',1/512,1)]
    if suite != 'lda':
        specs += [(8,p,m,1/512,r) for m in ('N','LDA') for r in (2,4) for p in ('uniform','advection')]
    if suite == 'features':
        specs += [(8,p,m,1/512,r) for scheme in ('N','LDA') for m in (scheme+'_hier_equal',scheme+'_hier_pattern') for r in (1,2,4) for p in ('uniform','advection')]
        specs += [(8,'pressure_patch',m,1/64,r) for m in ('N_hier_natural','LDA_hier_natural') for r in (1,2,4)]
    if suite == 'natural':
        specs = [(8,'pressure_patch',m,1/64,r) for m in ('N_hier_natural','LDA_hier_natural') for r in (1,2,4)]
    used = sorted(set(x[2] for x in specs))
    for method in used:
        (root/'configs'/f'{method}.sh').write_text(configs[method])
        for header in (root/'source/src').rglob('*.h'):
            (root/'build'/method/header.relative_to(root/'source/src').parent).mkdir(parents=True,exist_ok=True)
    cases=[]
    for n,problem,method,cap,ranks in specs:
        name=f'{problem}_{n}_{method}_dt{round(1/cap)}_np{ranks}'; folder=root/'runs'/name; folder.mkdir()
        ic=root/'inputs'/f'{problem}_{n}.hdf5'
        if not ic.exists(): feature_ic(ic,n,problem)
        param=rewrite((REPO/'examples/rd_3d/param.txt').read_text(),dict(InitCondFile=ic.with_suffix(''),OutputDir=str(folder/'output')+'/',MaxSizeTimestep=cap))
        (folder/'param.txt').write_text(param)
        cases.append(dict(name=name,n=n,problem=problem,method=method,ranks=ranks,cap=cap,end=.03125,ic=str(ic),ic_sha256=sha(ic),param_sha256=sha(folder/'param.txt')))
    write(root/'campaign.json',dict(description=__doc__,suite=suite,methods=used,cases=cases,gamma=1.4,velocity=VELOCITY.tolist()))


def run(root, selected):
    for case in json.loads((root/'campaign.json').read_text())['cases']:
        if selected and case['name'] not in selected: continue
        folder=root/'runs'/case['name']; artifact=root/'artifacts'/case['method']
        assert not (folder/'run_status.json').exists(), 'Use a new archive for reruns'
        provenance=json.loads((artifact/'provenance.json').read_text())
        assert sha(artifact/'Arepo')==provenance['binary_sha256']
        assert sha(case['ic'])==case['ic_sha256'] and sha(folder/'param.txt')==case['param_sha256']
        command=[str(artifact/'Arepo'),'param.txt']
        if case['ranks']>1: command=['mpiexec','-np',str(case['ranks'])]+command
        start=time.monotonic(); print('RUN',case['name'],flush=True)
        with (folder/'run.log').open('w') as log:
            result=subprocess.run(command,cwd=folder,env=ENV,stdout=log,stderr=subprocess.STDOUT)
        write(folder/'run_status.json',dict(returncode=result.returncode,seconds=time.monotonic()-start,command=command))
        assert result.returncode==0,folder


def analyse(root, selected):
    results=[]; finals={}; steps={}
    for case in json.loads((root/'campaign.json').read_text())['cases']:
        name=case['name']; folder=root/'runs'/name
        if selected and name not in selected: continue
        assert json.loads((folder/'run_status.json').read_text())['returncode']==0
        states=[state(p) for p in sorted((folder/'output').glob('snap_*.hdf5'))]
        a,b=states[0],states[-1]; assert a['time']==0 and b['time']==case['end']
        scale=np.abs(a['q']).sum(axis=0); scale[1:4]=np.maximum(scale[1:4],scale[0])
        conservation=max(float(np.max(abs(s['q'].sum(axis=0)-a['q'].sum(axis=0))/scale)) for s in states)
        coverage=max(float(abs(s['dual'].sum()-1)) for s in states)
        assert conservation<1e-12 and coverage<1e-12,(name,conservation,coverage)
        for s in states:
            assert all(np.isfinite(s[k]).all() for k in ('rho','p','v','q')) and np.all(s['rho']>0) and np.all(s['p']>0)
            np.testing.assert_array_equal(s['x'],a['x'])
        log=(folder/'run.log').read_text()
        endpoints=np.array([float(t) for t in re.findall(r'RD-3D-STAGE time=(\S+) stage=1',log)])
        assert len(endpoints)>0 and endpoints[-1]==case['end']
        dt=np.diff(np.r_[0.,endpoints]); assert np.all(dt>0); steps[name]=dt
        r=dict(case=name,conservation=conservation,coverage=coverage,steps=len(dt),actual_dt_min=float(dt.min()),actual_dt_max=float(dt.max()),rho_min=float(b['rho'].min()),p_min=float(b['p'].min()))
        if case['problem'] in ('rest','uniform'):
            r['uniform_defect']=max(float(abs(s[k]-a[k]).max()) for s in states for k in ('rho','p','v'))
            assert r['uniform_defect']<1e-12,r
        if case['problem']=='advection':
            exact=density(b['x']-VELOCITY*b['time']); r['density_L1']=float(np.sum(b['dual']*abs(b['rho']-exact)))
            r['density_L2']=float(np.sqrt(np.sum(b['dual']*(b['rho']-exact)**2)))
        r['max_bin_ratio']=max([int(x) for x in re.findall(r'max_ratio=(\d+)',log)] or [1])
        if 'pattern' in case['method'] or case['problem']=='pressure_patch': assert r['max_bin_ratio']>=2,r
        results.append(r); finals[name]=b; print(r,flush=True)
    comparisons={}
    if not selected:
        for name,b in finals.items():
            reference=name
            if '_hier_equal_' in name: reference=reference.replace('_hier_equal_','_')
            if name.endswith('_np2') or name.endswith('_np4'): reference=reference[:-1]+'1'
            if reference!=name and reference in finals:
                diff=max(float(abs(b[k]-finals[reference][k]).max()) for k in ('rho','p','v','q','dual'))
                assert diff<1e-10,(name,reference,diff)
                np.testing.assert_array_equal(steps[name],steps[reference])
                comparisons[name]=dict(reference=reference,max_field_difference=diff)
        byname={r['case']:r for r in results}
        if 'advection_8_LDA_dt512_np1' in byname:
            coarse=byname['advection_8_LDA_dt512_np1']['density_L1']; fine=byname['advection_16_LDA_dt512_np1']['density_L1']
            assert fine<coarse
            comparisons['LDA_two_grid']=dict(coarse_L1=coarse,fine_L1=fine,observed_order=float(np.log2(coarse/fine)),caveat='Initial trend only, not an asymptotic-order proof.')
            np.testing.assert_array_equal(steps['advection_16_LDA_dt4096_np1'],np.repeat(steps['advection_16_LDA_dt512_np1']/2,2))
            comparisons['LDA_dt_difference']={k:float(abs(finals['advection_16_LDA_dt4096_np1'][k]-finals['advection_16_LDA_dt512_np1'][k]).max()) for k in ('rho','p','v')}
            for p in ('rest','uniform','pressure_rest','advection'):
                diff=max(float(abs(finals[f'{p}_8_LDA_dt512_np1'][k]-finals[f'{p}_8_LDA_svd_dt512_np1'][k]).max()) for k in ('rho','p','v'))
                assert diff<1e-10; comparisons[p+'_LU_SVD']=diff
        write(root/'comparisons.json',comparisons)
    write(root/('results_selected.json' if selected else 'results.json'),results)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','build','run','analyse','all']); parser.add_argument('root',type=Path)
    parser.add_argument('--suite',choices=['lda','mpi','features','natural'],default='features'); parser.add_argument('--select',nargs='+')
    args=parser.parse_args(); root=args.root.resolve()
    if args.action in ('prepare','all'): prepare(root,args.suite)
    if args.action in ('build','all'): build(root,args.select)
    if args.action in ('run','all'): run(root,args.select)
    if args.action in ('analyse','all'): analyse(root,args.select)
