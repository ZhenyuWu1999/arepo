#!/usr/bin/env python3
"""Short Morton-inspired Blob check for static tetrahedral RD scheduling/MPI.

Current N/lumped RK2, not the paper's N1 reproduction. The default 16^3 and
0.1 t_cr endpoint test the execution path, not cloud destruction. Larger runs
belong on a configured cluster. Never overwrite an existing run archive.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time

import h5py
import numpy as np
from run_3d_static_gates import REPO, initial_conditions, state, freeze
from run_n_gauss3_split import ENV, sha, write, rewrite, build

BOX=10.
GAMMA=5/3
WIND=1.5*4.1
TCR=2*np.sqrt(10)/WIND


def make_ic(path,n):
    initial_conditions(path,n,'rest')
    x=np.random.default_rng(68315).uniform(0,BOX,(n**3,3))
    inside=np.linalg.norm(x-[2.5,5.,5.],axis=1)<1.
    rho=np.where(inside,100.,10.)
    v=np.full_like(x,1e-7);v[:,0]=np.where(inside,1e-8,WIND)
    with h5py.File(path,'r+') as f:
        f['Header'].attrs['BoxSize']=BOX
        g=f['PartType0'];g['Coordinates'][:]=x;g['Masses'][:]=rho
        g['Velocities'][:]=v;g['InternalEnergy'][:]=100/((GAMMA-1)*rho)
    return int(inside.sum())


def prepare(root,n,fraction,cfl):
    root.mkdir(parents=True,exist_ok=False)
    freeze(root)
    for folder in ('configs','inputs','runs','artifacts'):(root/folder).mkdir()
    ic=root/'inputs'/f'blob_{n}.hdf5';cloud_nodes=make_ic(ic,n)
    end=fraction*TCR
    methods={'N_equal':'Config_N_static.sh','N_hier':'Config_N_hierarchical.sh'}
    for method,filename in methods.items():
        config=(REPO/'examples/rd_3d'/filename).read_text().replace('GAMMA=1.4','GAMMA=1.6666666666666667')
        (root/'configs'/(method+'.sh')).write_text(config)
        for header in (root/'source/src').rglob('*.h'):
            (root/'build'/method/header.relative_to(root/'source/src').parent).mkdir(parents=True,exist_ok=True)
    cases=[]
    for method,ranks in [('N_equal',1),('N_hier',1),('N_hier',2)]:
        name=f'{method}_np{ranks}';folder=root/'runs'/name;folder.mkdir()
        param=rewrite((REPO/'examples/rd_3d/param.txt').read_text(),dict(
            InitCondFile=ic.with_suffix(''),OutputDir=str(folder/'output')+'/',BoxSize=BOX,
            TimeMax=end,TimeBetSnapshot=end/2,TimeBetStatistics=end/2,
            MaxSizeTimestep=end/4,CourantFac=cfl))
        (folder/'param.txt').write_text(param)
        cases.append(dict(name=name,method=method,ranks=ranks,ic=str(ic),ic_sha256=sha(ic),param_sha256=sha(folder/'param.txt')))
    write(root/'campaign.json',dict(methods=list(methods),cases=cases,n=n,nodes=n**3,
        cloud_nodes=cloud_nodes,seed=68315,box=BOX,gamma=GAMMA,cloud_radius=1.,
        cloud_center=[2.5,5.,5.],rho_cloud=100.,rho_wind=10.,pressure=100.,
        wind_speed=WIND,actual_mach=WIND/np.sqrt(GAMMA*100/10),tcr=TCR,
        tkh=1.6*TCR,fraction_tcr=fraction,end=end,cfl=cfl,
        scope=__doc__,physical_reference='https://arxiv.org/html/2204.01757v2#S5.SS3.SSS1'))
    print('PREPARED',n**3,'nodes;',cloud_nodes,'cloud nodes; end',end,flush=True)


def run(root):
    failed=False
    for case in json.loads((root/'campaign.json').read_text())['cases']:
        folder=root/'runs'/case['name'];binary=root/'artifacts'/case['method']/'Arepo'
        assert not (folder/'run_status.json').exists()
        provenance=json.loads((binary.parent/'provenance.json').read_text())
        assert sha(binary)==provenance['binary_sha256']
        assert sha(case['ic'])==case['ic_sha256'] and sha(folder/'param.txt')==case['param_sha256']
        command=[str(binary),'param.txt']
        if case['ranks']>1:command=['mpiexec','-np',str(case['ranks'])]+command
        print('RUN',case['name'],flush=True);start=time.monotonic()
        with (folder/'run.log').open('w') as log:
            p=subprocess.run(command,cwd=folder,env=ENV,stdout=log,stderr=subprocess.STDOUT)
        write(folder/'run_status.json',dict(returncode=p.returncode,seconds=time.monotonic()-start,
              command=command,binary_sha256=sha(binary),threads={k:ENV[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')}))
        failed|=p.returncode!=0
        print('FINISHED',case['name'],p.returncode,flush=True)
    return failed


def analyse(root):
    campaign=json.loads((root/'campaign.json').read_text())
    results=[];finals={};times={}
    for case in campaign['cases']:
        folder=root/'runs'/case['name'];status=json.loads((folder/'run_status.json').read_text())
        log=(folder/'run.log').read_text()
        row=dict(case=case['name'],returncode=status['returncode'],seconds=status['seconds'])
        if status['returncode']:
            row['failure_diagnostics']=[s for s in log.splitlines() if 'TERMINATE:' in s or 'invalid' in s or 'inadmissible' in s][-12:]
            results.append(row);continue
        states=[state(p) for p in sorted((folder/'output').glob('snap_*.hdf5'))]
        a,b=states[0],states[-1]
        assert a['time']==0 and abs(b['time']-campaign['end'])<1e-14
        scale=np.abs(a['q']).sum(axis=0);scale[1:4]=np.maximum(scale[1:4],scale[0])
        cons=max(float(np.max(abs(s['q'].sum(axis=0)-a['q'].sum(axis=0))/scale)) for s in states)
        assert cons<1e-12
        cloud_history=[]
        for s in states:
            assert all(np.isfinite(s[k]).all() for k in ('rho','p','v','q'))
            assert min(s['rho'].min(),s['p'].min())>0
            np.testing.assert_array_equal(s['x'],a['x'])
            assert abs(s['dual'].sum()/BOX**3-1)<1e-12
            # Equal composition: temperature is proportional to p/rho.
            selected=(s['rho']>64.) & (s['p']/s['rho']<9.)
            cloud_history.append(dict(time=s['time'],mass=float(s['mass'][selected].sum())))
        endpoints=np.array([float(t) for t in re.findall(r'RD-3D-STAGE time=(\S+) stage=1',log)])
        assert len(endpoints)>0
        # Hierarchy endpoints need not all be global full-step times; record them as diagnostics.
        row.update(end=b['time'],conservation=cons,snapshots=len(states),
                   stage1_records=len(endpoints),rho_min=float(b['rho'].min()),p_min=float(b['p'].min()),
                   max_bin_ratio=max([int(v) for v in re.findall(r'max_ratio=(\d+)',log)] or [1]),
                   initial_cloud_mass=cloud_history[0]['mass'],cloud_mass_fraction=cloud_history[-1]['mass']/cloud_history[0]['mass'],
                   cloud_history=cloud_history)
        if case['method']=='N_equal':
            dt=np.diff(np.r_[0.,endpoints]);row.update(dt_min=float(min(dt)),dt_max=float(max(dt)))
        results.append(row);finals[case['name']]=b;times[case['name']]=endpoints
    comparison={}
    if all(name in finals for name in ('N_hier_np1','N_hier_np2')):
        a,b=finals['N_hier_np1'],finals['N_hier_np2']
        # Compare primitive fields relatively; extensive content is much larger in this box.
        differences={k:float(np.max(abs(b[k]-a[k])/np.maximum(1.,abs(a[k])))) for k in ('rho','p','v','q','dual')}
        assert max(differences.values())<1e-9,differences
        np.testing.assert_array_equal(times['N_hier_np1'],times['N_hier_np2'])
        comparison=dict(mpi_max_scaled_field_difference=differences,identical_stage1_times=True)
    write(root/'results.json',dict(runs=results,comparison=comparison))
    print(json.dumps(dict(runs=results,comparison=comparison),indent=2),flush=True)
    return any(r['returncode'] for r in results)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','build','run','analyse'])
    parser.add_argument('root',type=Path);parser.add_argument('--n',type=int,default=16)
    parser.add_argument('--fraction-tcr',type=float,default=.1);parser.add_argument('--cfl',type=float,default=.01)
    args=parser.parse_args();root=args.root.resolve()
    if args.action=='prepare':prepare(root,args.n,args.fraction_tcr,args.cfl)
    elif args.action=='build':build(root,None)
    elif args.action=='run':raise SystemExit(2 if run(root) else 0)
    elif args.action=='analyse':raise SystemExit(2 if analyse(root) else 0)
