#!/usr/bin/env python3
"""Diagnostic first-order AREPO MMFV Sedov runs (exact Riemann and HLLC).

Separates spatial order from the form of the low-order dissipation: moving
Rusanov RD is first order with sound-speed dissipation on every wave, whereas
these runs are first-order Godunov/HLLC updates that resolve the contact.
Reuses the hash-checked ICs and parameters of the second-order MMFV archive.
"""
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
from run_n_gauss3_split import ENV, sha, write, rewrite, state, build

MMFV=REPO.parent/'local_runs/sedov_mmfv_20260929_v1'
METHODS={'MMFV_1st_exact':'Config_MMFV_moving_first_order.sh',
         'MMFV_1st_hllc':'Config_MMFV_moving_first_order_hllc.sh'}


def freeze(root):
    source=root/'source';source.mkdir()
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    subprocess.run(['git','archive','-o',str(root/'base.tar'),commit],cwd=REPO,check=True)
    subprocess.run(['tar','-xf',str(root/'base.tar'),'-C',str(source)],check=True)
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=REPO).decode().split('\0')
    untracked=subprocess.check_output(['git','ls-files','-z','--others','--exclude-standard'],cwd=REPO).decode().split('\0')
    hashes={}
    for name in tracked+untracked:
        if not name:continue
        src=REPO/name;dst=source/name
        if src.is_file():
            dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);hashes[name]=sha(src)
        elif dst.is_file():dst.unlink()
    shutil.copy2(REPO/'Makefile.systype',source/'Makefile.systype')
    (root/'working_tree.patch').write_bytes(subprocess.check_output(['git','diff','--binary','HEAD'],cwd=REPO))
    subprocess.run(['tar','-cf',str(root/'source.tar'),'-C',str(source),'.'],check=True)
    write(root/'source_provenance.json',dict(base_commit=commit,source_tar_sha256=sha(root/'source.tar'),
        tracked_and_untracked_hashes=hashes,environment={k:ENV[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')}))


def add_case(root,method,group,ic,end,template):
    folder=root/'runs'/f'{group}_{method}';folder.mkdir(parents=True)
    text=rewrite(template,dict(InitCondFile=ic.with_suffix(''),OutputDir=str(folder/'output')+'/',
        TimeMax=end,TimeBetSnapshot=end/4,TimeBetStatistics=end/4,MaxSizeTimestep=min(.01,end/4)))
    (folder/'param.txt').write_text(text)
    return dict(method=method,group=group,folder=str(folder),ic=str(ic),ic_sha256=sha(ic),
                param_sha256=sha(folder/'param.txt'),end=end)


def execute(root,case):
    folder=Path(case['folder']);binary=root/'artifacts'/case['method']/'Arepo'
    assert sha(case['ic'])==case['ic_sha256'] and sha(folder/'param.txt')==case['param_sha256']
    start=time.monotonic();cmd=[str(binary),'param.txt']
    with (folder/'run.log').open('w') as f:
        r=subprocess.run(cmd,cwd=folder,env=ENV,stdout=f,stderr=subprocess.STDOUT,timeout=3600)
    status=dict(returncode=r.returncode,seconds=time.monotonic()-start,command=cmd,binary_sha256=sha(binary))
    write(folder/'run_status.json',status);print(folder.name,json.dumps(status),flush=True)
    return status


def main(root):
    root.mkdir(parents=True,exist_ok=False)
    reference=json.loads((MMFV/'campaign.json').read_text())
    inputs={c['group']:c for c in reference['cases']}
    for c in inputs.values():
        assert sha(c['ic'])==c['ic_sha256']
        assert sha(MMFV/'runs'/c['group']/'param.txt')==c['param_sha256']
    freeze(root)
    for name in ('inputs','configs','artifacts','runs'):(root/name).mkdir()
    for method,config in METHODS.items():shutil.copy2(HERE/config,root/'configs'/f'{method}.sh')
    shutil.copy2(__file__,root/'run_mmfv_first_order.py')
    write(root/'campaign.json',dict(methods=list(METHODS),cases=[],source_archive=str(root)))
    for method in METHODS:
        for header in (root/'source/src').rglob('*.h'):
            (root/'build'/method/header.relative_to(root/'source/src').parent).mkdir(parents=True,exist_ok=True)
    build(root,None)
    for method in METHODS:
        header=(root/'artifacts'/method/'arepoconfig.h').read_text()
        assert '#define RESIDUAL_DISTRIBUTION' not in header and '#define VORONOI_STATIC_MESH' not in header
        assert '#define DISABLE_SPATIAL_EXTRAPOLATION' in header and '#define DISABLE_TIME_EXTRAPOLATION' in header
        assert ('#define RIEMANN_HLLC' in header)==method.endswith('hllc')
    ics={}
    for group in ('uniform','nearest21'):
        ics[group]=root/'inputs'/Path(inputs[group]['ic']).name
        shutil.copy2(inputs[group]['ic'],ics[group]);assert sha(ics[group])==inputs[group]['ic_sha256']
    template=(MMFV/'runs/nearest21/param.txt').read_text()
    cases=[add_case(root,m,'uniform',ics['uniform'],.001,template) for m in METHODS]
    cases+=[add_case(root,m,'nearest21',ics['nearest21'],.05,template) for m in METHODS]
    campaign=dict(methods=list(METHODS),cases=cases,source_archive=str(root),reference_archive=str(MMFV),
        reference_campaign_sha256=sha(MMFV/'campaign.json'),
        **{k:reference[k] for k in ('gamma','rho0','pressure0','energy_hot','box','nodes','hot_voronoi_area',
                                     'hot_u','hot_pressure','initial_energy','heated_ids')},
        description='Diagnostic first-order moving Voronoi FV: face extrapolation disabled; exact Riemann or native HLLC; '
                    'same glass, 21 heated IDs, Voronoi hot-energy normalization, CFL .1, equal adaptive steps, lab frame.')
    write(root/'campaign.json',campaign)
    with ThreadPoolExecutor(2) as pool:
        uniform=list(pool.map(lambda c:execute(root,c),cases[:2]))
    assert all(s['returncode']==0 for s in uniform)
    for c in cases[:2]:
        snaps=sorted((Path(c['folder'])/'output').glob('snap_*.hdf5'));a,b=state(snaps[0]),state(snaps[-1])
        defect=max(float(np.max(abs(b[k]-a[k]))) for k in ('rho','p','v'))
        c['uniform_defect']=defect;assert defect<1e-12,(c['method'],defect)
    write(root/'campaign.json',campaign)
    with ThreadPoolExecutor(2) as pool:
        science=list(pool.map(lambda c:execute(root,c),cases[2:]))
    for c,s in zip(cases[2:],science):
        c['returncode']=s['returncode']
        if s['returncode']!=0:continue
        snaps=sorted((Path(c['folder'])/'output').glob('snap_*.hdf5'));first,last=state(snaps[0]),state(snaps[-1])
        assert abs(last['time']-.05)<1e-12 and abs(first['totals'][3]-campaign['initial_energy'])<1e-11
        c['final']=dict(rho_min=float(last['rho'].min()),rho_max=float(last['rho'].max()),p_min=float(last['p'].min()),
                        mass_relative=float(last['totals'][0]/first['totals'][0]-1),
                        energy_relative=float(last['totals'][3]/first['totals'][3]-1))
    write(root/'campaign.json',campaign)
    print('COMPLETE',json.dumps([c.get('final',c.get('returncode')) for c in cases[2:]]),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    main(p.parse_args().root.resolve())
