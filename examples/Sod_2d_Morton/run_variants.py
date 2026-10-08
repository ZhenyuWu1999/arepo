#!/usr/bin/env python3
"""Extend frozen Morton glass ICs to current static/ALE RK2 methods."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(REPO/'tests/rd'))
if (HERE/'run_n_gauss3_split.py').exists():sys.path.insert(0,str(HERE))
from run_n_gauss3_split import ENV,sha,write,rewrite,build,state

METHODS=[('N_rk2_roe_static','N','RK2','Roe','static'),
         ('LDA_fe_gauss3_static','LDA','Euler','Gauss3','static'),
         ('LDA_f1_roe_static','LDA','F1','Roe','static'),
         ('LDA_f1_gauss3_static','LDA','F1','Gauss3','static'),
         ('N_rk2_roe_moving','N','RK2','Roe','moving'),
         ('LDA_f1_roe_moving','LDA','F1','Roe','moving'),
         ('LDA_f1_gauss3_moving','LDA','F1','Gauss3','moving')]


def prepare(root,control):
    root.mkdir(parents=True,exist_ok=False)
    for d in ('source','inputs','configs','runs','artifacts'):(root/d).mkdir()
    prov=json.loads((control/'source_provenance.json').read_text())
    assert sha(control/'source.tar')==prov['source_tar_sha256']
    checked=[]
    for p,h in prov['tracked_hashes'].items():
        if p.startswith('src/') or p in ('Makefile','defines_extra'):
            assert sha(REPO/p)==h,p;checked.append(p)
    for name in ('source.tar','source_provenance.json'):shutil.copy2(control/name,root/name)
    subprocess.run(['tar','-xf',str(root/'source.tar'),'-C',str(root/'source')],check=True)
    old=json.loads((control/'campaign.json').read_text())
    for c in old['cases']:
        p=Path(c['ic']);assert sha(p)==c['ic_sha256']
        target=root/'inputs'/p.name
        if not target.exists():shutil.copy2(p,target)
    base=(control/'configs/LDA1_roe_static.sh').read_text()
    cases=[]
    for method,scheme,temporal,residual,mesh in METHODS:
        lines=[s for s in base.splitlines() if s.strip() and not s.startswith('#')]
        lines=[scheme+'_SCHEME' if s=='LDA_SCHEME' else s for s in lines]
        if temporal!='Euler':lines.remove('RD_DIAG_PREDICTOR_ONLY')
        if residual=='Gauss3':lines+=['RD_ALE_CONTOUR_RESIDUAL','RD_ALE_CONTOUR_GAUSS=3']
        if mesh=='moving':
            lines.remove('VORONOI_STATIC_MESH')
            lines+=['REGULARIZE_MESH_CM_DRIFT','REGULARIZE_MESH_CM_DRIFT_USE_SOUNDSPEED',
                    'REGULARIZE_MESH_FACE_ANGLE','RD_ALE_EQUALSTEP','RD_RK2_SPLIT_STAGES']
            if residual=='Roe':lines.append('RD_ALE_SPLIT_MESH_VELOCITY')
        assert len(lines)==len(set(lines))
        (root/'configs'/f'{method}.sh').write_text('# Sod_2d_Morton matched-IC variants; lab frame.\n'+'\n'.join(lines)+'\n')
        for nx in (0,64,128):
            ref=next(c for c in old['cases'] if c['scheme']==scheme and c['effective_Nx']==nx)
            problem=ref['problem'];name=f'uniform_{method}' if nx==0 else f'Sod_2d_Morton_Nx{nx}_{method}'
            folder=root/'runs'/name;folder.mkdir()
            target=root/'inputs'/Path(ref['ic']).name
            template=(control/'runs'/ref['name']/'param.txt').read_text()
            param=rewrite(template,dict(InitCondFile=target.with_suffix(''),OutputDir=str(folder/'output')+'/'))
            if mesh=='moving':param+='\nCellShapingSpeed 0.5\nCellMaxAngleFactor 1.5\n'
            (folder/'param.txt').write_text(param)
            cases.append(dict(ref,name=name,method=method,temporal=temporal,residual=residual,mesh=mesh,
                frame='lab',archive=str(root),ic=str(target),ic_sha256=sha(target),
                param_sha256=sha(folder/'param.txt'),reused=False))
    reused=[]
    for c in old['cases']:
        run=control/'runs'/c['name'];art=control/'artifacts'/c['method']
        meta=json.loads((art/'provenance.json').read_text())
        assert sha(art/'Arepo')==meta['binary_sha256']
        assert meta['source_tar_sha256']==prov['source_tar_sha256']
        assert sha(run/'param.txt')==c['param_sha256']
        assert json.loads((run/'run_status.json').read_text())['returncode']==0
        reused.append(dict(c,archive=str(control),frame='lab',temporal='Euler',mesh='static',reused=True))
    metadata={k:old[k] for k in ('test_name','gamma','box_size','left_state','right_state','high_density_interval','tube_interval','coordinates','courant','max_timestep','final_time','glass_source','glass_sha256')}
    metadata.update(methods=[m[0] for m in METHODS],cases=cases,reused_cases=reused,control_archive=str(control),
        source_tar_sha256=prov['source_tar_sha256'],source_files_checked=checked,workers=2,
        environment={k:ENV[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')},
        setup='Same exact Morton glass ICs, gamma5/3, box2, CFL.4, cap.02, t.2, Nx64/128; equal steps within each run, laboratory frame.',
        limits='Moving predictor-only is prohibited by the existing split-stage guard and is not run. No guard changes. N uses Roe/lumped RK2; LDA uses mixed-stage F1 with Roe or Gauss3. Static Euler references retained. Adaptive timestep histories differ, despite the same CFL/cap. No limiter or solver changes.')
    write(root/'campaign.json',metadata)
    for n in ('run_variants.py','analyze_variants.py'):
        if (HERE/n).exists():shutil.copy2(HERE/n,root/n)
    shutil.copy2(REPO/'tests/rd/run_n_gauss3_split.py',root/'run_n_gauss3_split.py')
    print('Prepared 7 new builds, 7 uniform gates and 14 Sod runs; reuse 4 completed Euler controls.',flush=True)


def execute(root,group,selected=None):
    campaign=json.loads((root/'campaign.json').read_text())
    cases=[c for c in campaign['cases'] if (c['problem']=='uniform')==(group=='uniform')]
    if selected:cases=[c for c in cases if c['method'] in selected]
    def one(c):
        run=root/'runs'/c['name']
        if group=='science':
            gate=root/'runs'/f'uniform_{c["method"]}'
            status=json.loads((gate/'run_status.json').read_text())
            snaps=sorted((gate/'output').glob('snap_*.hdf5'))
            defect=None
            if status['returncode']==0 and len(snaps)>1:
                a,b=state(snaps[0]),state(snaps[-1])
                defect=max(float(np.max(abs(b[k]-a[k]))) for k in ('rho','p','v'))
            if defect is None or defect>=1e-12:
                result=dict(name=c['name'],status='blocked_by_uniform_gate',returncode=None,uniform_defect=defect)
                write(run/'run_status.json',result);print(json.dumps(result),flush=True);return result
        assert not (run/'run.log').exists(),c['name']
        art=root/'artifacts'/c['method'];meta=json.loads((art/'provenance.json').read_text())
        assert sha(art/'Arepo')==meta['binary_sha256']
        assert sha(c['ic'])==c['ic_sha256'] and sha(run/'param.txt')==c['param_sha256']
        start=time.monotonic();cmd=[str(art/'Arepo'),'param.txt']
        print('START',c['name'],flush=True)
        with (run/'run.log').open('w') as f:
            out=subprocess.run(cmd,cwd=run,env=ENV,stdout=f,stderr=subprocess.STDOUT)
        result=dict(name=c['name'],returncode=out.returncode,seconds=time.monotonic()-start,
                    binary_sha256=meta['binary_sha256'],command=cmd)
        write(run/'run_status.json',result);print(json.dumps(result),flush=True);return result
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(one,cases))
    suffix='' if not selected else '_'+str(int(time.time()))
    write(root/f'status_{group}{suffix}.json',results)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('prepare','build','uniform','science'))
    p.add_argument('root',type=Path)
    p.add_argument('--control',type=Path,default=Path('/Users/zhenyuwu/arepo_rd/local_runs/Sod_2d_Morton/20260928_v1'))
    p.add_argument('--select',nargs='+')
    a=p.parse_args();root=a.root.resolve()
    if a.action=='prepare':prepare(root,a.control.resolve())
    elif a.action=='build':build(root,a.select)
    else:execute(root,a.action,a.select)
