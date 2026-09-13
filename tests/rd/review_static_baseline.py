#!/usr/bin/env python3
"""Selective develop-branch port: frozen native comparisons and static KH probes.

Stages preserve clean-build provenance and never overwrite a native run.
Requires retained local IC/reference archives; no CR Python imports or solver.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import h5py
import numpy as np

REPO=Path(__file__).resolve().parents[2]
DATA=REPO.parent/'local_runs'
OLD=DATA/'static_gauss_hierarchy_mpi_20260912'
ENV=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def rewrite(s,updates):
    for key,value in updates.items():
        s,n=re.subn(r'^'+re.escape(key)+r'\s+.*$',key+' '+str(value),s,flags=re.M)
        assert n==1,(key,n)
    return s

def prepare(root):
    (root/'configs').mkdir(exist_ok=False)
    (root/'inputs').mkdir();(root/'runs').mkdir()
    equal=(REPO/'examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_EQUAL.sh').read_text()
    hierarchy=(REPO/'examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_HIER.sh').read_text()
    configs=dict(g3_equal=equal,g3_hier_equal=hierarchy+'\nFORCE_EQUAL_TIMESTEPS\n',
                 g3_hier_two=hierarchy+'\nRD_HIERARCHICAL_TEST_PATTERN\n',g3_hier_natural=hierarchy,
                 g5_hier_two=hierarchy.replace('RD_ALE_CONTOUR_GAUSS=3','RD_ALE_CONTOUR_GAUSS=5')+'\nRD_HIERARCHICAL_TEST_PATTERN\n')
    for name,value in configs.items():(root/'configs'/f'{name}.sh').write_text(value)
    old=json.loads((OLD/'campaign.json').read_text());cases=[]
    for c in old['cases']:
        if c['ranks'] not in (1,4):continue
        take=(c['problem']=='uniform' or
              c['problem']=='yee' and c['nodes']==48**2 and c['denominator']==256 or
              c['problem']=='sod' and c['method']=='g3_hier_natural')
        if not take:continue
        ic=root/'inputs'/Path(c['ic']).name
        if not ic.exists():shutil.copy2(c['ic'],ic)
        folder=root/'runs'/c['name'];folder.mkdir()
        param=rewrite((OLD/'runs'/c['name']/'param.txt').read_text(),
                      {'InitCondFile':ic.with_suffix(''),'OutputDir':str(folder/'output')+'/'})
        (folder/'param.txt').write_text(param)
        cases.append({**c,'ic':str(ic),'reference':str(OLD/'runs'/c['name']),'param_sha256':sha(folder/'param.txt')})
    for profile,end in [('smooth',2.),('sharp',.05)]:
        ic=root/'inputs'/f'kh_{profile}.hdf5';shutil.copy2(DATA/'kh_gauss_20260912/inputs'/ic.name,ic)
        template=(DATA/'kh_gauss_20260912/runs'/f'{profile}_kh_gauss3'/'param.txt').read_text()
        # Mesh regularization parameters are absent from the static build.
        template=re.sub(r'^(CellShapingSpeed|CellMaxAngleFactor)\s+.*\n','',template,flags=re.M)
        for method in ['g3_equal','g3_hier_natural']:
            for ranks in (1,4):
                name=f'kh_{profile}_{method}_r{ranks}';folder=root/'runs'/name;folder.mkdir()
                param=rewrite(template,{'InitCondFile':ic.with_suffix(''),'OutputDir':str(folder/'output')+'/',
                                       'TimeMax':end,'TimeBetSnapshot':end/10,'TimeBetStatistics':end/10})
                (folder/'param.txt').write_text(param)
                cases.append(dict(name=name,problem='kh_'+profile,method=method,ranks=ranks,end=end,
                                  ic=str(ic),ic_sha256=sha(ic),param_sha256=sha(folder/'param.txt')))
    (root/'campaign.json').write_text(json.dumps(dict(methods=list(configs),cases=cases),indent=2)+'\n')
    print('Prepared',len(cases),'native cases.',flush=True)

def build(root):
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True),'Commit before build.'
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    subprocess.run(['git','archive','--format=tar','-o',str(root/'source.tar'),'HEAD'],cwd=REPO,check=True)
    for method in json.loads((root/'campaign.json').read_text())['methods']:
        target=root/'build_artifacts'/method;target.mkdir(parents=True,exist_ok=False)
        builddir=root/'build'/method;config=root/'configs'/f'{method}.sh'
        cmd=['make',f'CONFIG={config}',f'BUILD_DIR={builddir}',f'EXEC={builddir}/Arepo','-j4']
        with (target/'build.log').open('w') as log:r=subprocess.run(cmd,cwd=REPO,env=ENV,stdout=log,stderr=subprocess.STDOUT)
        assert r.returncode==0,str(target/'build.log')
        for src,name in [(builddir/'Arepo','Arepo'),(builddir/'arepoconfig.h','arepoconfig.h'),
                         (builddir/'version.c','version.c'),(config,'Config.sh'),(REPO/'Makefile.systype','Makefile.systype')]:
            shutil.copy2(src,target/name)
        (target/'Arepo').chmod(0o555)
        row=dict(source_commit=commit,binary_sha256=sha(target/'Arepo'),config_sha256=sha(config),command=cmd)
        (target/'provenance.json').write_text(json.dumps(row,indent=2)+'\n')
        (target/'linkage.txt').write_text(subprocess.check_output(['otool','-L',str(target/'Arepo')],text=True))
        print('Built',method,commit,flush=True)
    (root/'toolchain.txt').write_text(subprocess.check_output(['/opt/homebrew/bin/mpicc','--version'],text=True)+
                                     subprocess.check_output(['/opt/homebrew/bin/mpiexec','--version'],text=True))

def spatial(root):
    """Add t=1 Gauss h refinement; old Roe t=1 evidence is not interchangeable."""
    path=root/'campaign.json';campaign=json.loads(path.read_text())
    for n,denom in [(48,256),(96,512),(192,1024)]:
        ic=root/'inputs'/f'yee_glass{n}_boost1.hdf5'
        if not ic.exists():shutil.copy2(DATA/'lda_baseline_glass_20260911/inputs'/ic.name,ic)
        for method in ['g3_equal','g3_hier_two']:
            name=f'yee_t1_n{n}_{method}_r4';folder=root/'runs'/name;folder.mkdir(exist_ok=False)
            template=(OLD/'runs'/f'yee_{method}_r4_dt256'/'param.txt').read_text()
            param=rewrite(template,{'InitCondFile':ic.with_suffix(''),'OutputDir':str(folder/'output')+'/',
                                   'TimeMax':1.,'TimeBetSnapshot':.25,'TimeBetStatistics':.25,'MaxSizeTimestep':1/denom})
            (folder/'param.txt').write_text(param)
            campaign['cases'].append(dict(name=name,problem='yee_spatial',method=method,ranks=4,end=1.,n=n,
                                         denominator=denom,ic=str(ic),ic_sha256=sha(ic),param_sha256=sha(folder/'param.txt')))
    path.write_text(json.dumps(campaign,indent=2)+'\n');print('Added six t=1 Yee cases.',flush=True)

def run(root):
    for c in json.loads((root/'campaign.json').read_text())['cases']:
        folder=root/'runs'/c['name']
        if (folder/'run.log').exists():
            print('Preserve existing run',c['name'],flush=True);continue
        assert sha(c['ic'])==c['ic_sha256'] and sha(folder/'param.txt')==c['param_sha256']
        binary=root/'build_artifacts'/c['method']/'Arepo';start=time.monotonic()
        cmd=['/opt/homebrew/bin/mpiexec','-n',str(c['ranks']),str(binary),'param.txt']
        print('START',c['name'],flush=True)
        with (folder/'run.log').open('w') as log:r=subprocess.run(cmd,cwd=folder,env=ENV,stdout=log,stderr=subprocess.STDOUT)
        row=dict(returncode=r.returncode,seconds=time.monotonic()-start,command=cmd,binary_sha256=sha(binary))
        (folder/'run_status.json').write_text(json.dumps(row,indent=2)+'\n')
        print('END',c['name'],row['returncode'],round(row['seconds'],2),flush=True)

def snapshot(path):
    with h5py.File(path) as f:
        p=f['PartType0'];order=np.argsort(p['ParticleIDs'][:]);rho=p['Density'][:][order];v=p['Velocities'][:][order,:2]
        e=p['InternalEnergy'][:][order];mass=p['Masses'][:][order]
        u=np.column_stack((rho,rho[:,None]*v,rho*(e+.5*np.sum(v*v,axis=1))))
        return dict(id=p['ParticleIDs'][:][order],x=p['Coordinates'][:][order],w=p['VertexVelocity'][:][order],
                    u=u,g=mass/rho,p=.4*rho*e,bins=p['TimebinHydro'][:][order],time=float(f['Header'].attrs['Time']),
                    total=np.sum((mass/rho)[:,None]*u,axis=0))

def analyze(root):
    rows=[];states={};checks=[]
    for c in json.loads((root/'campaign.json').read_text())['cases']:
        folder=root/'runs'/c['name'];status=json.loads((folder/'run_status.json').read_text());log=(folder/'run.log').read_text()
        row={**c,**status,'completed':status['returncode']==0 and 'bye!' in log}
        if not row['completed']:
            row['failure']=[l for l in log.splitlines() if any(s in l.lower() for s in ['terminate:','error','negative','failed','a2'])][-15:]
            rows.append(row);continue
        files=sorted((folder/'output').glob('snap_*.hdf5'));initial=snapshot(files[0]);final=snapshot(files[-1]);states[c['name']]=final
        scale=np.array([initial['total'][0]]*3+[initial['total'][3]])
        saved=[snapshot(f) for f in files]
        row.update(max_conservation=max(float(np.max(abs(s['total']-initial['total'])/scale)) for s in saved),
                   min_rho=min(float(s['u'][:,0].min()) for s in saved),min_pressure=min(float(s['p'].min()) for s in saved),
                   max_coordinate_change=max(float(np.max(abs(s['x']-initial['x']))) for s in saved),
                   max_mesh_velocity=max(float(np.max(abs(s['w']))) for s in saved),
                   max_area_change=max(float(np.max(abs(s['g']-initial['g']))) for s in saved),
                   distinct_final_bins=list(map(int,np.unique(final['bins']))))
        counts=re.findall(r'live_vertices=(\d+) frozen_vertices=(\d+) max_ratio=(\d+)',log)
        row['max_frozen_vertices']=max((int(v[1]) for v in counts),default=0)
        row['max_star_ratio']=max((int(v[2]) for v in counts),default=1)
        if c['problem']=='uniform':
            row['uniform_max_U_difference']=float(np.max(abs(final['u']-initial['u'])))
            assert row['uniform_max_U_difference']<1e-12
        if 'hier' in c['method'] and not c['method'].endswith('equal'):
            assert row['max_frozen_vertices']>0 and row['max_star_ratio']>=2
        assert np.array_equal(initial['id'],final['id']) and abs(final['time']-c['end'])<1e-10
        assert row['min_rho']>0 and row['min_pressure']>0 and row['max_conservation']<1e-11
        assert row['max_coordinate_change']==0 and row['max_mesh_velocity']==0 and row['max_area_change']<1e-12
        if 'reference' in c:
            ref=snapshot(sorted((Path(c['reference'])/'output').glob('snap_*.hdf5'))[-1])
            assert np.array_equal(ref['id'],final['id'])
            row['test_branch_max_U_difference']=float(np.max(abs(ref['u']-final['u'])))
            assert row['test_branch_max_U_difference']<1e-11
        if c['problem']=='yee_spatial':
            xy=(final['x'][:,:2]-np.array([6.,5.])+5)%10-5;r2=np.sum(xy*xy,axis=1)
            temperature=1-.4*25/(8*np.pi**2*1.4)*np.exp(1-r2);rho=temperature**2.5
            factor=2.5/np.pi*np.exp(.5*(1-r2));vel=np.column_stack((1-xy[:,1]*factor,xy[:,0]*factor))
            w=final['g']/final['g'].sum()
            row['rho_l1']=float(w@abs(final['u'][:,0]-rho))
            row['velocity_l1']=float(w@np.linalg.norm(final['u'][:,1:3]/final['u'][:,0,None]-vel,axis=1))
        rows.append(row)
    for row in rows:
        if not row['completed'] or row['ranks']!=1:continue
        name=row['name'];other=name.replace('_r1','_r4')
        if other in states:
            difference=float(np.max(abs(states[name]['u']-states[other]['u'])))
            checks.append(dict(left=name,right=other,max_U_difference=difference))
            # Long KH can amplify rounding; report separately from exact replay gates.
            if not name.startswith('kh_'):assert difference<1e-11
    for rank in (1,4):
        eq=states[f'yee_g3_equal_r{rank}_dt256'];hier=states[f'yee_g3_hier_equal_r{rank}_dt256']
        difference=float(np.max(abs(eq['u']-hier['u'])))
        checks.append(dict(left='equal',right='hier_equal',rank=rank,max_U_difference=difference));assert difference<1e-11
    refinement=[]
    for method in ['g3_equal','g3_hier_two']:
        chosen=sorted([r for r in rows if r['completed'] and r['problem']=='yee_spatial' and r['method']==method],key=lambda r:r['n'])
        if chosen:
            refinement.append(dict(method=method,n=[r['n'] for r in chosen],rho_l1=[r['rho_l1'] for r in chosen],
                                   rho_orders=np.log2(np.array([r['rho_l1'] for r in chosen[:-1]])/np.array([r['rho_l1'] for r in chosen[1:]])).tolist(),
                                   velocity_l1=[r['velocity_l1'] for r in chosen],
                                   velocity_orders=np.log2(np.array([r['velocity_l1'] for r in chosen[:-1]])/np.array([r['velocity_l1'] for r in chosen[1:]])).tolist()))
    (root/'summary.json').write_text(json.dumps(dict(cases=rows,comparisons=checks,refinement=refinement),indent=2)+'\n')
    if len(refinement)==2:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.ticker import NullLocator
        figs=root/'figures';figs.mkdir(exist_ok=True)
        fig,axes=plt.subplots(1,2,figsize=(9.4,4.1),layout='constrained')
        for r,label in zip(refinement,['Equal-step Gauss3/F1','Frozen-star Gauss3/F1 hierarchy']):
            for ax,key in zip(axes,['rho_l1','velocity_l1']):ax.loglog(r['n'],r[key],'o-',label=label)
        for ax,label in zip(axes,[r'Density $L_1$',r'Velocity-vector $L_1$']):
            ax.set(xlabel='Full-box resolution per axis',ylabel=label,xticks=[48,96,192],xticklabels=['48','96','192'])
            ax.xaxis.set_minor_locator(NullLocator())
            ax.grid(alpha=.2);ax.legend(fontsize=8)
        fig.suptitle('Static glass advected Yee, t=1 — native develop-branch baseline\nSpatial refinement with timestep caps 1/256, 1/512, 1/1024')
        for ext in ['png','pdf']:fig.savefig(figs/f'yee_t1_spatial.{ext}',dpi=180)
        plt.close(fig)
    print(json.dumps(dict(completed=sum(r['completed'] for r in rows),failed=sum(not r['completed'] for r in rows),
                         max_test_branch_difference=max(r.get('test_branch_max_U_difference',0) for r in rows),
                         comparisons=checks,refinement=refinement),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','build','spatial','run','analyze']);p.add_argument('root',type=Path)
    a=p.parse_args();globals()[a.action](a.root.resolve())
