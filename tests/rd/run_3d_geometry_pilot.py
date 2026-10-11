#!/usr/bin/env python3
"""M2: short, single-rank 16^3 native FV geometry diagnostics, CFL .1/.3.

Uses no moving-RD adapter. Gamma5/3, unit periodic cube, equal adaptive steps,
standard quasi-Lagrangian velocity with CM/face-angle regularization (.5/2.25).
Archives source/build/IC/parameters. Geometry hazards are results, not failed
hydrodynamic gates. The off control verifies all particle datasets by ID.
"""
import argparse
import csv
import ctypes as C
import json
from pathlib import Path
import subprocess
import tempfile
import time
import h5py
import numpy as np
from run_3d_static_gates import REPO, initial_conditions, freeze, state
from run_3d_swift_benchmarks import gresho
from run_n_gauss3_split import ENV, sha, write, rewrite, build
from test_simplex_registry import Record, Metric, Summary, Cavity, BOX, library, independent_interval
GAMMA=5/3

def ic(path,problem,n=16):
    initial_conditions(path,n,'rest')
    with h5py.File(path,'r+') as f:
        g=f['PartType0'];x=g['Coordinates'][:];rho=np.ones(len(x));p=np.ones(len(x));v=np.zeros_like(x)
        if problem=='rest_random':
            x=np.random.default_rng(20261011).uniform(0,1,x.shape);g['Coordinates'][:]=x
        elif problem=='advection':
            rho+=.1*np.prod(np.sin(2*np.pi*x),axis=1);v[:]=[.3,-.2,.4]
        elif problem=='gresho': v,p=gresho(x)
        elif problem=='shear':
            profile=.5*(np.tanh((x[:,1]-.25)/.025)-np.tanh((x[:,1]-.75)/.025))
            rho=1+profile;v[:,0]=profile-.5;v[:,1]=.05*np.sin(4*np.pi*x[:,0]);p[:]=2.5
        elif problem=='sedov': p[:]=1e-6
        elif problem!='probe': raise ValueError(problem)
        g['Masses'][:]=rho;g['Velocities'][:]=v;g['InternalEnergy'][:]=p/((GAMMA-1)*rho)

def prepare(root):
    root.mkdir(parents=True,exist_ok=False);freeze(root)
    for d in ('configs','inputs','runs','artifacts'): (root/d).mkdir()
    cfg=(REPO/'examples/rd_3d/Config_FV_geometry.sh').read_text()
    for method,config in [('diag',cfg),('off',cfg.replace('RD_3D_GEOMETRY_DIAGNOSTICS\n',''))]:
        (root/'configs'/f'{method}.sh').write_text(config)
        for header in (root/'source/src').rglob('*.h'): (root/'build'/method/header.relative_to(root/'source/src').parent).mkdir(parents=True,exist_ok=True)
    problems=['rest_random','advection','gresho','shear','sedov','probe']
    for problem in problems: ic(root/'inputs'/f'{problem}.hdf5',problem)
    specs=[('probe',.3,'diag',1/65536)]
    specs += [(p,cfl,'diag',dict(rest_random=.015625,advection=.015625,gresho=.03125,shear=.03125,sedov=.001)[p]) for p in problems[:-1] for cfl in (.1,.3)]
    specs += [(p,.3,'off',dict(rest_random=.015625,gresho=.03125,sedov=.001)[p]) for p in ('rest_random','gresho','sedov')]
    cases=[]
    for problem,cfl,method,end in specs:
        name=f'{problem}_cfl{cfl}_{method}';folder=root/'runs'/name;folder.mkdir();path=root/'inputs'/f'{problem}.hdf5'
        param=rewrite((REPO/'examples/rd_3d/param.txt').read_text(),dict(InitCondFile=path.with_suffix(''),OutputDir=str(folder/'output')+'/',TimeMax=end,TimeBetSnapshot=end/2,TimeBetStatistics=end/2,MaxSizeTimestep=min(.02,end/2),CourantFac=cfl))
        param+='\nCellShapingSpeed .5\nCellMaxAngleFactor 2.25\n'
        (folder/'param.txt').write_text(param)
        cases.append(dict(name=name,problem=problem,cfl=cfl,method=method,end=end,n=16,ic=str(path),ic_sha256=sha(path),param_sha256=sha(folder/'param.txt')))
    write(root/'campaign.json',dict(scope=__doc__,methods=['diag','off'],cases=cases,gamma=GAMMA,box=[1,1,1],seed_jitter=928,seed_random=20261011,regularization=dict(CellShapingSpeed=.5,CellMaxAngleFactor=2.25),ranks=1))

def run(root,selected):
    campaign=json.loads((root/'campaign.json').read_text())
    for c in campaign['cases']:
        if selected and c['name'] not in selected: continue
        folder=root/'runs'/c['name'];artifact=root/'artifacts'/c['method'];binary=artifact/'Arepo'
        assert not (folder/'run_status.json').exists(),'Use a fresh archive for reruns'
        provenance=json.loads((artifact/'provenance.json').read_text());assert sha(binary)==provenance['binary_sha256']
        assert sha(c['ic'])==c['ic_sha256'] and sha(folder/'param.txt')==c['param_sha256']
        print('RUN',c['name'],flush=True);command=[str(binary),'param.txt'];start=time.monotonic()
        with (folder/'run.log').open('w') as f:
            result=subprocess.run(command,cwd=folder,env=ENV,stdout=f,stderr=subprocess.STDOUT)
        write(folder/'run_status.json',dict(returncode=result.returncode,seconds=time.monotonic()-start,command=command))
        assert result.returncode==0,folder
        if c['problem']=='probe':
            a=state(folder/'output/snap_000.hdf5');hot=np.argsort(np.linalg.norm(a['x']-.5,axis=1))[:15];hotvolume=float(a['dual'][hot].sum())
            path=root/'inputs/sedov.hdf5'
            with h5py.File(path,'r+') as f:
                assert np.array_equal(f['PartType0/ParticleIDs'][:],a['id'])
                u=f['PartType0/InternalEnergy'][:];u[hot]=1/hotvolume;f['PartType0/InternalEnergy'][:]=u
            write(root/'sedov_injection.json',dict(hot_ids=a['id'][hot].tolist(),hot_voronoi_volume=hotvolume,hot_energy=1.,background_removed=hotvolume*1e-6/(GAMMA-1),normalization='Native FV Voronoi mass at rho=1, not median dual.'))
            for item in campaign['cases']:
                if item['problem']=='sedov': item['ic_sha256']=sha(path)
            write(root/'campaign.json',campaign)

def audit_pair(output,lib):
    with (output/'geometry_first_pair.bin').open('rb') as f:
        no,nn,size=np.frombuffer(f.read(12),dtype='<u4');h=float(np.frombuffer(f.read(8),dtype='<f8')[0]);assert size==C.sizeof(Record)
        a=(Record*int(no)).from_buffer_copy(f.read(int(no*size)));b=(Record*int(nn)).from_buffer_copy(f.read(int(nn*size)));assert not f.read(1)
    s=Summary();om=(Metric*int(no))();nm=(Metric*int(nn))();c=(Cavity*int(no+nn))()
    assert lib.rd_registry_compare(a,int(no),b,int(nn),h,BOX,C.byref(s),om,nm,c)==0
    first=json.loads((output/'geometry_steps.jsonl').read_text().splitlines()[0])
    for k,_ in Summary._fields_:
        if k in first: np.testing.assert_allclose(first[k],getattr(s,k),rtol=1e-12,atol=2e-15)
    # Separate NumPy determinant coefficients + polynomial root solver; sample
    # both chains, all invalid events are audited separately below.
    errors=[]
    for closing,records,metrics in [(0,a,om),(1,b,nm)]:
        for i in np.linspace(0,len(records)-1,150,dtype=int):
            coeff,minimum,where=independent_interval(records[i],h,closing);m=metrics[i]
            scale=max(abs(coeff).max(),1e-30);errors.append(abs(m.vmin-minimum)/scale)
            assert abs(m.vmin-minimum)<3e-12*scale
    max_event_error=0.;events=0
    for line in (output/'geometry_invalid.jsonl').read_text().splitlines():
        e=json.loads(line);r=Record();r.orientation=e['orientation'];np.ctypeslib.as_array(r.x)[:]=e['x'];np.ctypeslib.as_array(r.w)[:]=e['w']
        coeff,minimum,where=independent_interval(r,e['h'],e['closing']);scale=max(abs(coeff).max(),1e-30)
        max_event_error=max(max_event_error,abs(minimum-e['vmin'])/scale);assert abs(minimum-e['vmin'])<3e-12*scale
        assert minimum<0 or e['uncertain'];events+=1
    return dict(first_pair_samples=len(errors),max_sample_relative_error=max(errors),invalid_events=events,max_event_relative_error=max_event_error)

def particles_equal(a,b):
    with h5py.File(a) as fa,h5py.File(b) as fb:
        ga,gb=fa['PartType0'],fb['PartType0'];assert set(ga)==set(gb)
        oa=np.argsort(ga['ParticleIDs'][:]);ob=np.argsort(gb['ParticleIDs'][:])
        for k in ga:
            x,y=ga[k][:][oa],gb[k][:][ob];assert x.dtype==y.dtype and x.shape==y.shape and x.tobytes()==y.tobytes(),k
        assert fa['Header'].attrs['Time']==fb['Header'].attrs['Time']
        return len(ga.keys())

def analyse(root,selected):
    results=[];cases=json.loads((root/'campaign.json').read_text())['cases'];comparisons={}
    with tempfile.TemporaryDirectory() as tmp:
        lib=library(tmp)
        for c in cases:
            if selected and c['name'] not in selected: continue
            folder=root/'runs'/c['name'];assert json.loads((folder/'run_status.json').read_text())['returncode']==0
            states=[state(p) for p in sorted((folder/'output').glob('snap_*.hdf5'))];a,b=states[0],states[-1]
            assert a['time']==0 and b['time']==c['end'];assert all(np.isfinite(s['q']).all() and s['rho'].min()>0 and s['p'].min()>0 for s in states)
            r=dict(case=c['name'],end=c['end'],rho_min=float(b['rho'].min()),p_min=float(b['p'].min()))
            if c['method']=='diag':
                steps=[json.loads(l) for l in (folder/'output/geometry_steps.jsonl').read_text().splitlines()]
                assert steps and steps[-1]['time']==c['end']
                assert abs(sum(s['h'] for s in steps)-c['end'])<1e-14
                with (folder/'output/geometry_cavities.csv').open() as f: cavities=list(csv.DictReader(f))
                sizes=np.array([int(z['vertices']) for z in cavities]);invalid=[json.loads(l) for l in (folder/'output/geometry_invalid.jsonl').read_text().splitlines()]
                r.update(steps=len(steps),dt_min=min(s['h'] for s in steps),dt_max=max(s['h'] for s in steps),tetra_min=min(s['old_count'] for s in steps),tetra_max=max(s['new_count'] for s in steps),removed=sum(s['removed'] for s in steps),inserted=sum(s['inserted'] for s in steps),cavities=len(cavities),max_vertices=int(sizes.max()) if len(sizes) else 0,p99_vertices=float(np.percentile(sizes,99)) if len(sizes) else 0,changed_fraction_max=max(s['changed_vertices']/s['nodes'] for s in steps),winding=sum(s['winding_cavities'] for s in steps),reversed_common=sum(s['reversed_common'] for s in steps),aliases=max(s['id_alias_old']+s['id_alias_new'] for s in steps),old_interval_negative=sum(s['old_interval_negative'] for s in steps),new_pullback_negative=sum(s['new_pullback_negative'] for s in steps),new_interval_negative=sum(s['new_interval_negative'] for s in steps),new_mid_negative=sum(s['new_mid_negative'] for s in steps),uncertain=sum(s['old_uncertain']+s['new_uncertain'] for s in steps),min_pullback_ratio=min(s['min_pullback_ratio'] for s in steps),min_new_interval=min(s['min_new_interval'] for s in steps),min_q_new=min(s['q_new'][0] for s in steps),q_new_p01_min=min(s['q_new'][1] for s in steps),max_cavity_volume_defect=max(s['max_cavity_volume_defect'] for s in steps),max_cavity_moment_defect=max(s['max_cavity_moment_defect'] for s in steps),max_midpoint_gcl_defect=max(s['max_midpoint_gcl_defect'] for s in steps),max_gauss_gcl_defect=max(s['max_gauss_gcl_defect'] for s in steps),max_mean_normal_correction=max(s['max_mean_normal_correction'] for s in steps),max_dm_l1=max(s['dm_l1'] for s in steps),max_dm_sum=max(abs(s['dm_sum']) for s in steps),min_nodal_temporal=min(s['min_nodal_temporal'] for s in steps),nonpositive_nodal_temporal=sum(s['nonpositive_nodal_temporal'] for s in steps),reg_rms_max=max(s['reg_rms'] for s in steps),coverage_defect=max(abs(s[k]-1) for s in steps for k in ('coverage0','coverage1','old_forward_coverage','new_pullback_coverage')))
                r['interior_old_min_events']=sum(z['closing']==0 and 0<z['smin']<1 for z in invalid)
                hidden=[0,0];nonpositive_elements=0;min_element_temporal=None
                for z in invalid:
                    rec=Record();rec.orientation=z['orientation'];np.ctypeslib.as_array(rec.x)[:]=z['x'];np.ctypeslib.as_array(rec.w)[:]=z['w']
                    coeff,minimum,where=independent_interval(rec,z['h'],z['closing'])
                    if z['closing']:
                        temporal=(coeff[0]+coeff.sum())/2;nonpositive_elements+=temporal<=0
                        min_element_temporal=temporal if min_element_temporal is None else min(min_element_temporal,temporal)
                    if np.polynomial.polynomial.polyval([0,.5,1],coeff).min()>z['error'] and minimum < -z['error']: hidden[z['closing']]+=1
                r['hidden_old_events'],r['hidden_new_events']=hidden
                r['nonpositive_element_temporal']=int(nonpositive_elements);r['min_element_temporal_in_invalid']=min_element_temporal
                r['independent_audit']=audit_pair(folder/'output',lib)
                assert r['coverage_defect']<1e-11 and r['max_cavity_volume_defect']<1e-11 and r['max_cavity_moment_defect']<1e-11,r
                assert len(cavities)==sum(s['cavities'] for s in steps)
                counts={}
                for z in cavities:
                    key=f"{z['vertices']}:{z['removed']}->{z['inserted']}";counts[key]=counts.get(key,0)+1
                r['cavity_histogram']=counts
            else:
                reference=root/'runs'/c['name'].replace('_off','_diag')/'output';snapshots=sorted((folder/'output').glob('snap_*.hdf5'))
                assert len(snapshots)==len(list(reference.glob('snap_*.hdf5')))
                counts=[particles_equal(p,reference/p.name) for p in snapshots];comparisons[c['name']]=dict(byte_identical=True,snapshots=len(counts),datasets=counts)
            results.append(r);print(c['name'],{k:v for k,v in r.items() if k not in ('cavity_histogram','independent_audit')},flush=True)
    write(root/'results.json',results);write(root/'nonmutation.json',comparisons)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','build','run','analyse','all']);p.add_argument('root',type=Path);p.add_argument('--select',nargs='+');args=p.parse_args();root=args.root.resolve()
    if args.action in ('prepare','all'): prepare(root)
    if args.action in ('build','all'): build(root,args.select)
    if args.action in ('run','all'): run(root,args.select)
    if args.action in ('analyse','all'): analyse(root,args.select)
