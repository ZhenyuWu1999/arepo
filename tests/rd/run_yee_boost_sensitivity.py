#!/usr/bin/env python3
"""Matched LDA boost1/10 static/moving Yee, 48/96/192, shared timestep caps."""
import argparse,json,re,shutil,subprocess,os
from pathlib import Path
import h5py
import numpy as np
from run_n_gauss3_split import REPO,sha,write,rewrite,run,state

BASE=REPO.parent/'local_runs/yee_static_moving_384_20260924_v1'

def prepare(root):
    root.mkdir(exist_ok=False)
    for d in ('artifacts','configs','runs','inputs','figures'):(root/d).mkdir()
    prov=json.loads((BASE/'source_provenance.json').read_text())
    for f,h in prov['tracked_hashes'].items():
        if f.startswith('src/') or f in ('Makefile','defines_extra'):assert sha(REPO/f)==h,f
    for f in ('source.tar','source_provenance.json'):shutil.copy2(BASE/f,root/f)
    assert sha(root/'source.tar')==prov['source_tar_sha256']
    for n in (48,96,192):
        for boost in (1,10):
            p=root/'inputs'/f'yee_n{n}_b{boost}.hdf5';shutil.copy2(BASE/'inputs'/f'yee_glass{n}.hdf5',p)
            with h5py.File(p,'r+') as f:
                v=f['PartType0/Velocities'][:];v[:,0]+=boost-1;f['PartType0/Velocities'][:]=v
                f['Header'].attrs['YeeBoostVelocity']=[float(boost),0.,0.]
            with h5py.File(p) as f,h5py.File(BASE/'inputs'/f'yee_glass{n}.hdf5') as old:
                for key in ('Coordinates','Masses','InternalEnergy','ParticleIDs'):assert np.array_equal(f['PartType0'][key][:],old['PartType0'][key][:])
                dv=f['PartType0/Velocities'][:]-old['PartType0/Velocities'][:]
                assert np.max(abs(dv-np.array([boost-1,0,0])))<2e-15
    for boost in (1,10):
        p=root/'inputs'/f'uniform_b{boost}.hdf5';shutil.copy2(root/'inputs'/f'yee_n48_b{boost}.hdf5',p)
        with h5py.File(p,'r+') as f:
            g=f['PartType0'];g['Masses'][:]=1.;g['InternalEnergy'][:]=2.5
            v=g['Velocities'][:];v[:]=[boost,0,0];g['Velocities'][:]=v
            f['Header'].attrs['DiagnosticUniformState']=1
    cases=[];methods=[]
    for mesh in ('static','moving'):
        artifact=BASE/'artifacts'/f'LDA_{mesh}';meta=json.loads((artifact/'provenance.json').read_text())
        assert sha(artifact/'Arepo')==meta['binary_sha256'] and sha(artifact/'Config.sh')==meta['config_sha256']
        assert meta['source_tar_sha256']==prov['source_tar_sha256']
        reference=next(c for c in json.loads((BASE/'summary.json').read_text())['cases']
            if c['method']==f'LDA_{mesh}' and c['problem']=='yee' and c['n']==48)
        template=(Path(reference['directory'])/'param.txt').read_text()
        for boost in (1,10):
            method=f'LDA_{mesh}_b{boost}';methods.append(method)
            shutil.copytree(artifact,root/'artifacts'/method);shutil.copy2(artifact/'Config.sh',root/'configs'/f'{method}.sh')
            def add(n,phase,end):
                den=1024*n//48
                name=f'uniform_{method}' if phase=='uniform' else f'{phase}_{method}_n{n}'
                folder=root/'runs'/name;folder.mkdir()
                ic=root/'inputs'/(f'uniform_b{boost}.hdf5' if phase=='uniform' else f'yee_n{n}_b{boost}.hdf5')
                p=rewrite(template,dict(InitCondFile=ic.with_suffix(''),OutputDir=str(folder/'output')+'/',
                    TimeMax=end,TimeBetSnapshot=.5 if phase=='yee' else end,TimeBetStatistics=.5 if phase=='yee' else end,
                    MaxSizeTimestep=1/den,MaxMemSize=512))
                (folder/'param.txt').write_text(p)
                cases.append(dict(name=name,method=method,phase=phase,problem='uniform' if phase=='uniform' else 'yee',scheme='LDA',residual='gauss3',frame='lab',mesh=mesh,boost=boost,n=n,dt_denominator=den,end=end,ic=str(ic),ic_sha256=sha(ic),param_sha256=sha(folder/'param.txt'),ranks=1))
            add(48,'uniform',.03125)
            if boost==10:add(192,'pilot',.0078125)
            for n in (48,96,192):add(n,'yee',1.)
    # Start the two expensive moving192 cases first, leaving two workers for
    # all shorter cases. No more than four native single-thread processes.
    cases.sort(key=lambda c:(c['phase'],not(c['mesh']=='moving' and c['n']==192),c['n'],c['mesh'],c['boost']))
    write(root/'campaign.json',dict(methods=methods,cases=cases,source_tar_sha256=prov['source_tar_sha256'],baseline=str(BASE),
        scope=__doc__,settings='gamma1.4 beta5 box10 t1 CFL.2; same glass48 family and IC fields except boost; cap1/1024,1/2048,1/4096 for all four methods; lab only, Gauss3 mixed F1, current Arpaia geometry and regularization, no topology repair.',
        resource='4 singleton workers maximum; OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1, MaxMemSize512MiB.',
        limits='Not a strict proof of Galilean invariance or an error floor. Keep all points; report whole-range log-log fits. No384/768 runs; no new source build or changes to tolerances.'))
    for f in (Path(__file__).name,'run_n_gauss3_split.py'):shutil.copy2(REPO/'tests/rd'/f,root/f)
    print('Prepared4 uniform gates,2 short192 pilots,12 matched science runs. Reused two verified binaries.',flush=True)

def pipeline(root):
    campaign=json.loads((root/'campaign.json').read_text())
    run(root,'uniform',None,4)
    for c in campaign['cases']:
        if c['phase']!='uniform':continue
        p=root/'runs'/c['name'];r=json.loads((p/'run_status.json').read_text());assert r['returncode']==0,c['name']
        files=sorted((p/'output').glob('snap_*.hdf5'));a,b=state(files[0]),state(files[-1])
        defect=max(float(np.max(abs(a[k]-b[k]))) for k in ('rho','v','p'))
        assert abs(b['time']-c['end'])<1e-12 and defect<1e-12,(c['name'],defect)
        print('GATE',c['name'],'max_defect',defect,flush=True)
    pilots=[c['name'] for c in campaign['cases'] if c['phase']=='pilot'];run(root,'science',pilots,2)
    (root/'status_science.json').rename(root/'status_pilot.json')
    for c in campaign['cases']:
        if c['phase']!='pilot':continue
        p=root/'runs'/c['name'];status=json.loads((p/'run_status.json').read_text());assert status['returncode']==0,c['name']
        log=(p/'run.log').read_text();steps=re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*([\deE.+-]+)',log)
        assert int(steps[-1][0])==int(c['end']*c['dt_denominator']),(c['name'],steps[-1])
        s=state(sorted((p/'output').glob('snap_*.hdf5'))[-1]);assert np.min(s['rho'])>0 and np.min(s['p'])>0
        print('PILOT PASS',c['name'],steps[-1],flush=True)
    science=[c['name'] for c in campaign['cases'] if c['phase']=='yee'];run(root,'science',science,4)
    # A failed science case is a result to preserve, not a reason to skip the
    # successful cases' analysis. Uniform/pilot gates above still fail closed.
    analyzer=REPO/'tests/rd/analyze_yee_boost_sensitivity.py'
    subprocess.run([os.sys.executable,str(analyzer),str(root)],check=True,env=dict(os.environ,MPLCONFIGDIR='/private/tmp/rd-mpl',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'))
    print('Science and automatic analysis complete; visual QA and final interpretation remain.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','pipeline'));p.add_argument('root',type=Path)
    a=p.parse_args();(prepare if a.action=='prepare' else pipeline)(a.root.resolve())
