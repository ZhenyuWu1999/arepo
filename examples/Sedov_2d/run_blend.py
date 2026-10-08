#!/usr/bin/env python3
"""Freeze a static LDA/F1 + common-Gauss Rusanov positivity experiment."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import h5py
import numpy as np

REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'tests/rd'))
from run_n_gauss3_split import ENV,sha,write,rewrite,build
from run import execute,write_ic
BASE=REPO.parent/'local_runs/sedov_2d_20260929_v1'


def prepare(root, b_sensor=False):
    root.mkdir(parents=True,exist_ok=False)
    source=root/'source'; source.mkdir()
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    subprocess.run(['git','archive','-o',str(root/'base.tar'),commit],cwd=REPO,check=True)
    subprocess.run(['tar','-xf',str(root/'base.tar'),'-C',str(source)],check=True)
    names=subprocess.check_output(['git','ls-files','-z'],cwd=REPO).decode().split('\0')
    names += ['src/hydro/rd_rusanov.h','src/hydro/rd_lda_rusanov.h','tests/rd/test_lda_rusanov.py']
    names += [str(p.relative_to(REPO)) for p in (REPO/'examples/Sedov_2d').glob('*.py')]
    hashes={}
    for name in names:
        if name and (REPO/name).is_file():
            target=source/name; target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(REPO/name,target); hashes[name]=sha(REPO/name)
    shutil.copy2(REPO/'Makefile.systype',source/'Makefile.systype')
    (root/'working_tree.patch').write_bytes(subprocess.check_output(['git','diff','--binary','HEAD'],cwd=REPO))
    subprocess.run(['tar','-cf',str(root/'source.tar'),'-C',str(source),'.'],check=True)
    write(root/'source_provenance.json',dict(base_commit=commit,source_tar_sha256=sha(root/'source.tar'),
          hashes=hashes,environment={k:ENV[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')}))
    for d in ('configs','artifacts','runs'): (root/d).mkdir()
    shutil.copytree(BASE/'inputs',root/'inputs'); shutil.copytree(BASE/'reference',root/'reference')
    methods=['LR_B','LR_Bmax'] if b_sensor else ['LR_blend','LR_low','LDA_reference']
    campaign=json.loads((BASE/'campaign.json').read_text())
    campaign.update(methods=methods,cases=[],source_archive=str(root),source_tar_sha256=sha(root/'source.tar'),
                    description=__doc__,limits='Static, single rank, equal steps; positivity only. No oscillation limiter or remap.')
    if b_sensor:
        campaign.update(description='Classical RD B/Bmax residual-ratio sensors transplanted to LDA/F1 + common-Gauss Rusanov.',
                        limits='Static, single rank, two-stage RK; positive coupled outer guard. No entropy constraint, characteristic projection or remap.')
    for n in (16,32,64):
        iy,ix=np.mgrid[:n,:n]
        xy=np.column_stack((((ix+.5*(iy%2)+.25)/n).ravel()%1,((iy+.25)/n).ravel()))
        rho=1+.2*np.sin(2*np.pi*xy.sum(axis=1))
        path=root/'inputs'/f'contact{n}.hdf5'
        write_ic(path,xy,1/((5/3-1)*rho),True)
        with h5py.File(path,'r+') as f: f['PartType0/Masses'][:]=rho
    template=(BASE/'runs/nearest21_LDA_static_lab/param.txt').read_text()
    cfg=(BASE/'artifacts/LDA_static_lab/Config.sh').read_text()
    cfg=re.sub(r'^RD_RK2_SPLIT_STAGES\s*$','',cfg,flags=re.M)
    cfg=re.sub(r'^# Gresho.*$','# Static LDA/Rusanov Sedov research; see campaign.json.',cfg,flags=re.M)
    for method in methods:
        text=cfg
        if method!='LDA_reference': text+=f'\nRD_LDA_RUSANOV_BLEND={int(method!="LR_low")}\n'
        if b_sensor: text+=f'RD_LDA_RUSANOV_B_SENSOR={1 if method=="LR_B" else 2}\n'
        (root/'configs'/f'{method}.sh').write_text(text)
        groups=['uniform','nearest21'] if method!='LDA_reference' else ['uniform']
        groups += ['contact16','contact32','contact64'] if method!='LR_low' else ['contact32']
        for group in groups:
            name=f'{group}_{method}'; folder=root/'runs'/name; folder.mkdir()
            icname='sedov_nearest21' if group=='nearest21' else group
            ic=root/'inputs'/f'{icname}.hdf5'
            end=.001 if group=='uniform' else (.05 if group=='nearest21' else .1)
            cap=min(.01,end/4) if not group.startswith('contact') else 1/8192
            param=rewrite(template,dict(InitCondFile=ic.with_suffix(''),OutputDir=str(folder/'output')+'/',
                          TimeMax=end,TimeBetSnapshot=end/4,TimeBetStatistics=end/4,MaxSizeTimestep=cap))
            (folder/'param.txt').write_text(param)
            campaign['cases'].append(dict(name=name,group=group,method=method,mesh='static',frame='lab',
                end=end,cfl=.1,temporal='complete F1/lumped RK2 stage corrections',ic=str(ic),
                ic_sha256=sha(ic),param_sha256=sha(folder/'param.txt')))
    write(root/'campaign.json',campaign)
    print('Prepared',len(campaign['cases']),'runs and',len(methods),'builds.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('prepare','build','run')); p.add_argument('root',type=Path)
    p.add_argument('--group',default='uniform'); p.add_argument('--select',nargs='+')
    p.add_argument('--b-sensor',action='store_true',help='Prepare the RD B and Bmax sensor comparison.')
    a=p.parse_args(); root=a.root.resolve()
    if a.action=='prepare': prepare(root,a.b_sensor)
    elif a.action=='build':
        for method in a.select or json.loads((root/'campaign.json').read_text())['methods']:
            for h in (root/'source/src').rglob('*.h'):
                (root/'build'/method/h.relative_to(root/'source/src').parent).mkdir(parents=True,exist_ok=True)
        build(root,a.select)
    else: execute(root,a.group,a.select)
