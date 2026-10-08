#!/usr/bin/env python3
"""Frozen standard AREPO MMFV on the same Sedov glass and 21 heated IDs."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import h5py
import numpy as np

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(REPO/'tests/rd'))
from run_n_gauss3_split import ENV, sha, write, rewrite, state, build
from run import write_ic

BASE=REPO.parent/'local_runs/sedov_positivity_20260929_v2'
METHOD='MMFV_moving'


def add_case(root,group,ic,end):
    folder=root/'runs'/group;folder.mkdir()
    template=(BASE/'runs/nearest21_Rusanov_moving/param.txt').read_text()
    template=template[template.index('InitCondFile'):]
    text=rewrite(template,dict(InitCondFile=ic.with_suffix(''),OutputDir=str(folder/'output')+'/',
        TimeMax=end,TimeBetSnapshot=end/4,TimeBetStatistics=end/4,
        MaxSizeTimestep=min(.01,end/4),CourantFac=.1))
    (folder/'param.txt').write_text(text)
    return dict(group=group,ic=str(ic),ic_sha256=sha(ic),param_sha256=sha(folder/'param.txt'),end=end)


def execute(root,case):
    folder=root/'runs'/case['group'];binary=root/'artifacts'/METHOD/'Arepo'
    assert sha(Path(case['ic']))==case['ic_sha256']
    assert sha(folder/'param.txt')==case['param_sha256']
    start=time.monotonic()
    cmd=[str(binary),'param.txt']
    with (folder/'run.log').open('w') as f:
        r=subprocess.run(cmd,cwd=folder,env=ENV,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
    status=dict(returncode=r.returncode,seconds=time.monotonic()-start,command=cmd,binary_sha256=sha(binary))
    write(folder/'run_status.json',status);print(case['group'],json.dumps(status),flush=True)
    assert r.returncode==0,folder/'run.log'
    snapshots=sorted((folder/'output').glob('snap_*.hdf5'))
    assert abs(state(snapshots[-1])['time']-case['end'])<1e-12
    return snapshots


def main(root):
    root.mkdir(parents=True,exist_ok=False)
    source=root/'source';source.mkdir()
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    subprocess.run(['git','archive','-o',str(root/'base.tar'),commit],cwd=REPO,check=True)
    subprocess.run(['tar','-xf',str(root/'base.tar'),'-C',str(source)],check=True)
    names=subprocess.check_output(['git','ls-files','-z'],cwd=REPO).decode().split('\0')
    names += ['src/hydro/rd_rusanov.h','examples/Sedov_2d/run_mmfv.py','examples/Sedov_2d/Config_MMFV_moving.sh','examples/Sedov_2d/run.py']
    hashes={}
    for name in names:
        if not name:continue
        src=REPO/name;dst=source/name
        if src.is_file():
            dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);hashes[name]=sha(src)
        elif dst.is_file():dst.unlink()
    shutil.copy2(REPO/'Makefile.systype',source/'Makefile.systype')
    (root/'working_tree.patch').write_bytes(subprocess.check_output(['git','diff','--binary','HEAD'],cwd=REPO))
    subprocess.run(['tar','-cf',str(root/'source.tar'),'-C',str(source),'.'],check=True)
    write(root/'source_provenance.json',dict(base_commit=commit,source_tar_sha256=sha(root/'source.tar'),
        tracked_and_new_hashes=hashes,environment={k:ENV[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')}))
    for name in ('inputs','runs','configs','artifacts'):(root/name).mkdir()
    shutil.copy2(HERE/'Config_MMFV_moving.sh',root/'configs'/f'{METHOD}.sh')
    write(root/'campaign.json',dict(methods=[METHOD],cases=[],source_archive=str(root)))
    for header in (source/'src').rglob('*.h'):
        (root/'build'/METHOD/header.relative_to(source/'src').parent).mkdir(parents=True,exist_ok=True)
    build(root,None)
    header=(root/'artifacts'/METHOD/'arepoconfig.h').read_text()
    assert '#define RESIDUAL_DISTRIBUTION' not in header
    assert '#define VORONOI_STATIC_MESH' not in header
    assert '#define RIEMANN_HLLC' not in header
    shutil.copy2(BASE/'inputs/uniform.hdf5',root/'inputs/uniform.hdf5')
    uniform=add_case(root,'uniform',root/'inputs/uniform.hdf5',.001)
    execute(root,uniform)
    finish(root)


def finish(root):
    """Resume after the already successful uniform run without rebuilding it."""
    artifact=root/'artifacts'/METHOD
    provenance=json.loads((artifact/'provenance.json').read_text())
    assert sha(artifact/'Arepo')==provenance['binary_sha256']
    assert sha(artifact/'Config.sh')==provenance['config_sha256']
    assert sha(root/'source.tar')==provenance['source_tar_sha256']
    assert json.loads((root/'runs/uniform/run_status.json').read_text())['returncode']==0
    uniform=dict(group='uniform',ic=str(root/'inputs/uniform.hdf5'),
        ic_sha256=sha(root/'inputs/uniform.hdf5'),param_sha256=sha(root/'runs/uniform/param.txt'),end=.001)
    snaps=sorted((root/'runs/uniform/output').glob('snap_*.hdf5'))
    a,b=state(snaps[0]),state(snaps[-1])
    defect=max(float(np.max(abs(b[k]-a[k]))) for k in ('rho','p','v'))
    assert defect<1e-12,defect
    # Repeated Voronoi construction differs at roundoff. Apply the same
    # established 1e-12 uniform-state bound to initialization and evolution.
    initial_defect=float(np.max(abs(a['rho']-1)))
    assert initial_defect<1e-12
    with h5py.File(snaps[0]) as f:
        order=np.argsort(f['PartType0/ParticleIDs'][:])
        assert np.array_equal(a['rho'],a['mass']/f['PartType0/Volume'][:][order])
    area=a['w'];np.save(root/'inputs/voronoi_area.npy',area)
    assert abs(area.sum()-1)<1e-12 and np.all(area>0)
    with h5py.File(BASE/'inputs/sedov_nearest21.hdf5') as f:
        xy=f['PartType0/Coordinates'][:,:2];old_u=f['PartType0/InternalEnergy'][:]
    assert np.array_equal(xy,a['xy'])
    hot=old_u>2e-6
    assert hot.sum()==21
    u=np.full(len(xy),1.5e-6);u[hot]=1/area[hot].sum()
    ic=root/'inputs/sedov_nearest21.hdf5';write_ic(ic,xy,u)
    science=add_case(root,'nearest21',ic,.05)
    campaign=dict(methods=[METHOD],cases=[uniform,science],source_archive=str(root),
        gamma=5/3,rho0=1,pressure0=1e-6,energy_hot=1,box=1,nodes=len(xy),
        heated_ids=(np.flatnonzero(hot)+1).tolist(),hot_voronoi_area=float(area[hot].sum()),
        hot_u=float(u[hot][0]),hot_pressure=float(u[hot][0]*2/3),
        initial_energy=float(area@u),uniform_defect=defect,initial_uniform_density_defect=initial_defect,
        description='Standard moving Voronoi FV, exact Riemann, native reconstruction/limiting, no refinement; CFL .1, global equal adaptive steps, lab frame.',
        normalization='Same glass and heated IDs as RD21; hot energy normalized using actual native Voronoi volumes, not RD median-dual areas.')
    write(root/'campaign.json',campaign)
    shutil.copy2(__file__,root/'run_mmfv.py')
    snaps=execute(root,science);initial=state(snaps[0])
    assert np.max(abs(initial['w']-area))<1e-12
    assert abs(initial['totals'][3]-campaign['initial_energy'])<1e-11
    print('COMPLETE',json.dumps(campaign),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    p.add_argument('--resume-after-uniform',action='store_true')
    args=p.parse_args()
    (finish if args.resume_after_uniform else main)(args.root.resolve())
