#!/usr/bin/env python3
"""Current N/Roe and LDA/Gauss3 moving Gresho, lab versus element frame.

Uses the historical deterministic jitter48 generator, gamma5/3 and boosts0/10.
Freezes current source; builds independent binaries. No solver modifications.
"""
import argparse, importlib.util, json, re, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from run_n_gauss3_split import REPO, ENV, sha, write, rewrite, build, run

def prepare(root):
    root.mkdir(parents=True,exist_ok=True);source=root/'source';source.mkdir(exist_ok=False)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    subprocess.run(['git','archive','-o',str(root/'base.tar'),commit],cwd=REPO,check=True)
    subprocess.run(['tar','-xf',str(root/'base.tar'),'-C',str(source)],check=True)
    hashes={}
    for name in subprocess.check_output(['git','ls-files','-z'],cwd=REPO).decode().split('\0'):
        if not name:continue
        p=REPO/name
        if p.is_file():
            (source/name).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,source/name);hashes[name]=sha(p)
        elif (source/name).is_file():(source/name).unlink()
    shutil.copy2(REPO/'Makefile.systype',source/'Makefile.systype')
    for name in ('run_n_gauss3_split.py',Path(__file__).name):shutil.copy2(REPO/'tests/rd'/name,root/name)
    (root/'working_tree.patch').write_bytes(subprocess.check_output(['git','diff','--binary','HEAD'],cwd=REPO))
    subprocess.run(['tar','-cf',str(root/'source.tar'),'-C',str(source),'.'],check=True)
    write(root/'source_provenance.json',dict(base_commit=commit,source_tar_sha256=sha(root/'source.tar'),tracked_hashes=hashes,environment={k:ENV[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')}))
    for d in ('configs','inputs','runs','artifacts'):(root/d).mkdir()
    spec=importlib.util.spec_from_file_location('ic',source/'examples/gresho_2d/create_mmrd_ics.py');ic=importlib.util.module_from_spec(spec);spec.loader.exec_module(ic)
    xy=ic.jittered_lattice(48,ic.BASE_SEED);rho,vx,vy,p=ic.gresho_state(xy)
    for boost in (0,10):ic.write_ic(root/'inputs'/f'gresho_b{boost}.hdf5',xy,rho,vx+boost,vy,p)
    ic.write_ic(root/'inputs/uniform.hdf5',xy,np.ones(len(xy)),np.full(len(xy),10.),np.zeros(len(xy)),5.)
    base=(REPO/'examples/yee_2d/Config_RD_ALE_LDA_GAUSS3_EQUAL_SPLIT.sh').read_text().replace('GAMMA=1.4','GAMMA=(5.0/3.0)')
    base+='\nRD_ALE_CFL_TIMESTEP\nRD_ALE_CFL_DIAGNOSTIC\nRD_ALE_GEOMETRY_DIAGNOSTICS\n'
    template=(source/'examples/gresho_2d/param_F_con_cm_A4b10.txt').read_text()
    methods=[];cases=[]
    for scheme in ('N','LDA'):
      for frame in ('lab','comoving'):
        method=f'{scheme}_{frame}';methods.append(method);cfg=base.replace('LDA_SCHEME',scheme+'_SCHEME')
        if scheme=='N':cfg=re.sub(r'^RD_ALE_CONTOUR.*\n','',cfg,flags=re.M)+'\nRD_ALE_SPLIT_MESH_VELOCITY\n'
        if frame=='lab':cfg=cfg.replace('RD_ELEMENT_COMOVING_FRAME\n','')
        (root/'configs'/f'{method}.sh').write_text(cfg)
        for horizon,end in (('uniform',.02),('short',.02),('long',1.)):
          for boost in ((10,) if horizon=='uniform' else (0,10)):
            name=f'uniform_{method}' if horizon=='uniform' else f'{horizon}_{method}_b{boost}'
            folder=root/'runs'/name;folder.mkdir();inp=root/'inputs'/('uniform.hdf5' if horizon=='uniform' else f'gresho_b{boost}.hdf5')
            param=rewrite(template,dict(InitCondFile=inp.with_suffix(''),OutputDir=str(folder/'output')+'/',TimeMax=end,TimeBetSnapshot=.1 if horizon=='long' else .02))
            (folder/'param.txt').write_text(param)
            cases.append(dict(name=name,method=method,scheme=scheme,frame=frame,residual='roe_split' if scheme=='N' else 'gauss3',problem='uniform' if horizon=='uniform' else 'gresho',horizon=horizon,boost=boost,end=end,ic=str(inp),ic_sha256=sha(inp),param_sha256=sha(folder/'param.txt'),ranks=1))
    write(root/'campaign.json',dict(methods=methods,cases=cases,scope=__doc__,setup=dict(n=48,seed=ic.BASE_SEED,jitter=ic.JITTER,gamma=ic.GAMMA,CFL=.3,cap=.01,min_dt=1e-5,box=1.,topology='current common begin/end hooks; both ALE sweeps on new connectivity'),limits='Historical setup on current source, not an exact replay of the August binary. Keep failed attempts. No positivity/tolerance changes.'))
    print('Prepared',len(cases),'runs,',len(methods),'binaries',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','build','run'));p.add_argument('root',type=Path);p.add_argument('--select',nargs='+');p.add_argument('--group',choices=('all','uniform','science'),default='uniform');p.add_argument('--workers',type=int,choices=(1,2,3,4),default=4)
    a=p.parse_args();root=a.root.resolve()
    if a.action=='prepare':prepare(root)
    elif a.action=='build':build(root,a.select)
    else:run(root,a.group,a.select,a.workers)
