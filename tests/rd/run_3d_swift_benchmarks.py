#!/usr/bin/env python3
"""Reduced AREPO tetra benchmarks using SWIFT v2026.04 physical test families.

16³ deterministic jittered unit cube; gamma 5/3. This changes SWIFT's glass
sampling/resolution and Sod box. Sedov replaces energy on the nearest 15 nodes,
normalized by measured AREPO median-dual volumes, not an assumed equal mass.
Strong-shock failures are retained and reported, never hidden by primitive floors.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import time

import h5py
import numpy as np
from run_3d_static_gates import REPO, initial_conditions, state, freeze
from run_n_gauss3_split import ENV, sha, write, rewrite, build

GAMMA=5/3
SOURCES={p:f'https://github.com/SWIFTSIM/SWIFT/blob/v2026.04/examples/HydroTests/{q}/makeIC.py' for p,q in [('sod','SodShock_3D'),('sedov','SedovBlast_3D'),('gresho','GreshoVortex_3D')]}


def gresho(x):
    dx=x[:,0]-.5; dy=x[:,1]-.5; r=np.hypot(dx,dy)
    vp=np.where(r<.2,5*r,np.where(r<.4,2-5*r,0.))
    p=np.where(r<.2,5+12.5*r*r,np.where(r<.4,9+12.5*r*r-20*r+4*np.log(np.maximum(r,1e-30)/.2),3+4*np.log(2)))
    v=np.column_stack([-vp*dy/np.maximum(r,1e-30),vp*dx/np.maximum(r,1e-30),np.zeros(len(r))])
    return v,p


def make_ic(path,problem):
    initial_conditions(path,16,'rest')
    with h5py.File(path,'r+') as f:
        g=f['PartType0']; x=g['Coordinates'][:]; rho=np.ones(len(x)); p=np.ones(len(x)); v=np.zeros_like(x)
        if problem=='sod':
            rho[x[:,0]>=.5]=.125; p[x[:,0]>=.5]=.1
        elif problem=='gresho': v,p=gresho(x)
        elif problem=='sedov': p[:]=1e-6
        elif problem!='probe': raise ValueError(problem)
        g['Masses'][:]=rho; g['Velocities'][:]=v; g['InternalEnergy'][:]=p/((GAMMA-1)*rho)


def prepare(root):
    root.mkdir(parents=True,exist_ok=False);freeze(root)
    for name in ('configs','inputs','runs','artifacts'): (root/name).mkdir()
    configs={m:(REPO/f'examples/rd_3d/Config_{m}_static.sh').read_text().replace('GAMMA=1.4','GAMMA=1.6666666666666667') for m in ('N','LDA')}
    configs['N_hier']=configs['N'].replace('FORCE_EQUAL_TIMESTEPS\n','')+'\nRD_HIERARCHICAL_TIMESTEPS\n'
    for method,cfg in configs.items():
        (root/'configs'/f'{method}.sh').write_text(cfg)
        for h in (root/'source/src').rglob('*.h'): (root/'build'/method/h.relative_to(root/'source/src').parent).mkdir(parents=True,exist_ok=True)
    for problem in ('probe','sod','sedov','gresho'): make_ic(root/'inputs'/f'{problem}.hdf5',problem)
    specs=[('probe','N',1,1/4096)]+[(p,m,1,dict(sod=.08,gresho=.1,sedov=.03)[p]) for p in ('sod','gresho','sedov') for m in ('N','LDA')]
    specs += [(p,'N',2,dict(sod=.08,gresho=.1,sedov=.03)[p]) for p in ('sod','gresho','sedov')]+[('sod','N_hier',2,.08)]
    cases=[]
    for problem,method,ranks,end in specs:
        name=f'{problem}_{method}_np{ranks}';folder=root/'runs'/name;folder.mkdir();ic=root/'inputs'/f'{problem}.hdf5'
        param=rewrite((REPO/'examples/rd_3d/param.txt').read_text(),dict(InitCondFile=ic.with_suffix(''),OutputDir=str(folder/'output')+'/',TimeMax=end,TimeBetSnapshot=end/4,TimeBetStatistics=end/4,MaxSizeTimestep=min(1/2048,end/2),CourantFac=.1))
        (folder/'param.txt').write_text(param)
        cases.append(dict(name=name,problem=problem,method=method,ranks=ranks,end=end,n=16,ic=str(ic),ic_sha256=sha(ic),param_sha256=sha(folder/'param.txt')))
    write(root/'campaign.json',dict(description=__doc__,methods=list(configs),cases=cases,source_urls=SOURCES,gamma=GAMMA,seed=928,jitter=.12,box=[1,1,1],cfl=.1))


def run(root):
    campaign=json.loads((root/'campaign.json').read_text())
    for c in campaign['cases']:
        folder=root/'runs'/c['name']; artifact=root/'artifacts'/c['method']
        assert not (folder/'run_status.json').exists(), 'Use a new archive for reruns'
        provenance=json.loads((artifact/'provenance.json').read_text()); assert sha(artifact/'Arepo')==provenance['binary_sha256']
        assert sha(c['ic'])==c['ic_sha256'] and sha(folder/'param.txt')==c['param_sha256']
        command=[str(artifact/'Arepo'),'param.txt']
        if c['ranks']>1: command=['mpiexec','-np',str(c['ranks'])]+command
        print('RUN',c['name'],flush=True);start=time.monotonic()
        with (folder/'run.log').open('w') as log:
            result=subprocess.run(command,cwd=folder,env=ENV,stdout=log,stderr=subprocess.STDOUT)
        write(folder/'run_status.json',dict(returncode=result.returncode,seconds=time.monotonic()-start,command=command,binary_sha256=provenance['binary_sha256']))
        if c['problem']=='probe':
            assert result.returncode==0,'Uniform volume probe must pass before Sedov injection'
            a=state(folder/'output/snap_000.hdf5'); hot=np.argsort(np.linalg.norm(a['x']-.5,axis=1))[:15];hotvolume=float(a['dual'][hot].sum())
            ic=root/'inputs/sedov.hdf5'
            with h5py.File(ic,'r+') as f:
                np.testing.assert_array_equal(f['PartType0/ParticleIDs'][:],a['id'])
                u=f['PartType0/InternalEnergy'][:];u[hot]=1/hotvolume;f['PartType0/InternalEnergy'][:]=u
            write(root/'sedov_injection.json',dict(hot_ids=a['id'][hot].tolist(),hot_dual_volume=hotvolume,specific_internal_energy=1/hotvolume,injected_hot_energy=1.,background_removed=hotvolume*1e-6/(GAMMA-1),probe_binary=provenance['binary_sha256']))
            for item in campaign['cases']:
                if item['problem']=='sedov': item['ic_sha256']=sha(ic)
            write(root/'campaign.json',campaign)


def analyse(root, output=None):
    output = output or root
    if output != root: output.mkdir(parents=True, exist_ok=False)
    spec=importlib.util.spec_from_file_location('frozen_riemann',root/'source/examples/shocktube_1d/Riemann.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    results=[];curves={};finals={}
    for c in json.loads((root/'campaign.json').read_text())['cases']:
        folder=root/'runs'/c['name'];status=json.loads((folder/'run_status.json').read_text());log=(folder/'run.log').read_text()
        row=dict(case=c['name'],returncode=status['returncode'],seconds=status['seconds'])
        if status['returncode']:
            row['failure_diagnostics']=[l for l in log.splitlines() if any(t in l for t in ('TERMINATE:','inadmissible','invalid','non-physical','RD tetra distribution failed'))][-12:]
            assert row['failure_diagnostics'],row
            results.append(row);print(row,flush=True);continue
        states=[state(p) for p in sorted((folder/'output').glob('snap_*.hdf5'))];a,b=states[0],states[-1]
        assert a['time']==0 and b['time']==c['end']
        scale=np.abs(a['q']).sum(axis=0);scale[1:4]=np.maximum(scale[1:4],scale[0])
        conservation=max(float(np.max(abs(s['q'].sum(axis=0)-a['q'].sum(axis=0))/scale)) for s in states)
        assert conservation<1e-12,(c['name'],conservation)
        for s in states:
            assert all(np.isfinite(s[k]).all() for k in ('rho','p','v','q')) and min(s['rho'].min(),s['p'].min())>0
            np.testing.assert_array_equal(s['x'],a['x']);assert abs(s['dual'].sum()-1)<1e-12
        row.update(conservation=conservation,rho_min=float(b['rho'].min()),p_min=float(b['p'].min()),end=b['time'],steps=len(re.findall(r'RD-3D-STAGE time=\S+ stage=1',log)),max_bin_ratio=max([int(x) for x in re.findall(r'max_ratio=(\d+)',log)] or [1]))
        if c['problem']=='sod':
            mask=(b['x'][:,0]>.25)&(b['x'][:,0]<.75)
            _,q,_=module.RiemannProblem(b['x'][mask,0].copy(),.5,np.array([1.,0.,1.]),np.array([.125,0.,.1]),GAMMA,b['time'])
            weights=b['dual'][mask];weights/=weights.sum()
            row['central_half_L1']=(weights@abs(np.column_stack([b['rho'][mask],b['v'][mask,0],b['p'][mask]])-q)).tolist()
            curves[c['name']]=(b['x'][mask,0],b['rho'][mask],q[:,0])
        elif c['problem']=='gresho':
            v,p=gresho(b['x']); row['velocity_L1']=float(np.sum(b['dual']*np.linalg.norm(b['v']-v,axis=1)))
            row['pressure_L1']=float(np.sum(b['dual']*abs(b['p']-p)))
            curves[c['name']]=(np.linalg.norm(b['x'][:,:2]-.5,axis=1),np.linalg.norm(b['v'][:,:2],axis=1),np.linalg.norm(v[:,:2],axis=1))
        elif c['problem']=='sedov':
            row['energy_initial']=float(a['q'][:,4].sum());row['energy_final']=float(b['q'][:,4].sum());r=np.linalg.norm(b['x']-.5,axis=1)
            curves[c['name']]=(r,b['rho'],np.ones(len(r)))
        results.append(row);finals[c['name']]=b;print(row,flush=True)
    comparisons={}
    for name,b in finals.items():
        if name.endswith('np2') and name.replace('np2','np1') in finals:
            a=finals[name.replace('np2','np1')];diff=max(float(abs(b[k]-a[k]).max()) for k in ('rho','p','v','q'))
            assert diff<1e-9,(name,diff);comparisons[name]=diff
    write(output/'results.json',results);write(output/'mpi_comparisons.json',comparisons)
    write(output/'summary.json',dict(passed=[r['case'] for r in results if r['returncode']==0],failed=[r['case'] for r in results if r['returncode']!=0],scope='Reduced benchmark adaptations; any failed case makes the CLI exit with status 2.'))
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(12,3.5))
    for ax,problem in zip(axes,('sod','gresho','sedov')):
        for name,(x,y,exact) in curves.items():
            if name.startswith(problem) and name.endswith('np1'):
                ax.scatter(x,y,s=1,alpha=.3,label=name)
        if problem=='sod':
            xx=np.linspace(.25,.75,1001)
            _,qq,_=module.RiemannProblem(xx.copy(),.5,np.array([1.,0.,1.]),np.array([.125,0.,.1]),GAMMA,.08)
            ax.plot(xx,qq[:,0],color='k',lw=1,label='analytic')
        elif problem=='gresho':
            rr=np.linspace(0,np.sqrt(.5),1001)
            vv,_=gresho(np.column_stack([.5+rr,np.full(len(rr),.5),np.full(len(rr),.5)]))
            ax.plot(rr,np.linalg.norm(vv,axis=1),color='k',lw=1,label='stationary analytic')
        elif not any(n.startswith('sedov') for n in curves):
            ax.set_axis_off()
            ax.text(.5,.5,'N/LDA stopped at the\nsolve-compatibility check.\nNo final Sedov profile.',ha='center',va='center',transform=ax.transAxes,color='darkred')
        ax.set_title(problem+' (16³)' + (' t=0.08' if problem=='sod' else ' t=0.1' if problem=='gresho' else ''));ax.set_xlabel('x' if problem=='sod' else 'radius');ax.set_ylabel('speed' if problem=='gresho' else 'density')
        if ax.get_legend_handles_labels()[0]:ax.legend(fontsize=7)
    fig.tight_layout();fig.savefig(output/'profiles.png',dpi=180);fig.savefig(output/'profiles.pdf');plt.close(fig)
    return any(r['returncode'] for r in results)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','build','run','analyse','all']);p.add_argument('root',type=Path);p.add_argument('--output',type=Path);args=p.parse_args();root=args.root.resolve()
    if args.action in ('prepare','all'):prepare(root)
    if args.action in ('build','all'):build(root,None)
    if args.action in ('run','all'):run(root)
    if args.action in ('analyse','all'):
        sys.exit(2 if analyse(root,args.output.resolve() if args.output else None) else 0)
