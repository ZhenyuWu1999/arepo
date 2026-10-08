#!/usr/bin/env python3
"""Morton Sod states and first-order schemes on a static periodic glass."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/'tests/rd'))
if (HERE/'run_n_gauss3_split.py').exists():
    sys.path.insert(0, str(HERE))
from run_n_gauss3_split import ENV, sha, write, rewrite, build, run
import h5py
import numpy as np

GAMMA = 5./3.


def write_ic(path, xy, uniform=False):
    n = len(xy)
    xyz = np.zeros((n,3)); xyz[:,:2] = xy
    high = (xy[:,0]>.5)&(xy[:,0]<1.5)
    rho = np.ones(n) if uniform else np.where(high,1.,.125)
    p = np.ones(n) if uniform else np.where(high,1.,.1)
    v = np.zeros((n,3))
    if uniform:
        v[:,:2] = [.37,-.21]
    with h5py.File(path,'w') as f:
        h=f.create_group('Header');g=f.create_group('PartType0')
        count=np.array([n,0,0,0,0,0],dtype=np.uint32)
        for k in ('NumPart_ThisFile','NumPart_Total'): h.attrs[k]=count
        h.attrs['NumPart_Total_HighWord']=np.zeros(6,dtype=np.uint32)
        h.attrs['MassTable']=np.zeros(6)
        h.attrs['BoxSize']=2.;h.attrs['Time']=0.;h.attrs['Redshift']=0.
        h.attrs['NumFilesPerSnapshot']=1;h.attrs['HubbleParam']=1.
        for k in ('Omega0','OmegaB','OmegaLambda','Flag_Sfr','Flag_Cooling','Flag_StellarAge','Flag_Metals','Flag_Feedback'):h.attrs[k]=0
        h.attrs['Flag_DoublePrecision']=1;h.attrs['Gamma']=GAMMA
        h.attrs['TestName']='Sod_2d_Morton'
        h.attrs['EffectiveSodResolutionX']=np.sqrt(n)/2
        h.attrs['FullBoxNside']=int(round(np.sqrt(n)))
        h.attrs['Coordinates']='xi=x-1 for 1<x<2; tau=t'
        for k,a in dict(Coordinates=xyz,Masses=rho,InternalEnergy=p/((GAMMA-1)*rho),Velocities=v,ParticleIDs=np.arange(1,n+1,dtype=np.uint64)).items():g.create_dataset(k,data=a)


def prepare(root,control,glass):
    root.mkdir(parents=True,exist_ok=False)
    for d in ('source','configs','inputs','runs','artifacts','reference'): (root/d).mkdir()
    prov=json.loads((control/'source_provenance.json').read_text())
    assert sha(control/'source.tar')==prov['source_tar_sha256']
    checked=[]
    for name,h in prov['tracked_hashes'].items():
        if name.startswith('src/') or name in ('Makefile','defines_extra'):
            assert sha(REPO/name)==h,name
            checked.append(name)
    shutil.copy2(control/'source.tar',root/'source.tar')
    shutil.copy2(control/'source_provenance.json',root/'source_provenance.json')
    subprocess.run(['tar','-xf',str(root/'source.tar'),'-C',str(root/'source')],check=True)
    with h5py.File(glass) as f:
        xy=np.mod(f['PartType0/Coordinates'][:,:2],1.)
    assert len(xy)==128**2
    inputs={}
    for nx,tile in ((64,1),(128,2)):
        pos=np.concatenate([2*(xy+[i,j])/tile for i in range(tile) for j in range(tile)])
        assert len(pos)==(2*nx)**2
        path=root/'inputs'/f'Sod_2d_Morton_Nx{nx}.hdf5'
        write_ic(path,pos)
        inputs[nx]=path
    uniform_source=control/'inputs/uniform_glass48.hdf5'
    with h5py.File(uniform_source) as f: uxy=2*np.mod(f['PartType0/Coordinates'][:,:2],1.)
    uniform=root/'inputs/uniform_gamma53.hdf5';write_ic(uniform,uxy,True)
    template=(control/'runs/sod_LDA_roe_fe_static/param.txt').read_text()
    config=(control/'configs/LDA_roe_fe_static.sh').read_text()
    assert 'RD_DIAG_PREDICTOR_ONLY' in config
    methods=['N1_roe_static','LDA1_roe_static'];cases=[]
    for method in methods:
        scheme='N' if method.startswith('N1') else 'LDA'
        cfg=config.replace('GAMMA=1.4','GAMMA=(5.0/3.0)').replace('LDA_SCHEME',scheme+'_SCHEME')
        cfg='# Sod_2d_Morton: static glass; full forward-Euler predictor; Roe residual.\n'+'\n'.join(l for l in cfg.splitlines() if not l.startswith('#'))+'\n'
        (root/'configs'/f'{method}.sh').write_text(cfg)
        for nx in (0,64,128):
            problem='uniform' if nx==0 else 'sod'
            name=f'uniform_{method}' if nx==0 else f'Sod_2d_Morton_Nx{nx}_{method}'
            folder=root/'runs'/name;folder.mkdir()
            ic=uniform if nx==0 else inputs[nx]
            end=.025 if nx==0 else .2
            updates=dict(InitCondFile=ic.with_suffix(''),OutputDir=str(folder/'output')+'/',BoxSize=2.,TimeMax=end,
                TimeBetSnapshot=end/4,TimeBetStatistics=end/4,MaxSizeTimestep=.02,CourantFac=.4,MaxMemSize=1024)
            param=rewrite(template,updates)
            (folder/'param.txt').write_text(param)
            cases.append(dict(name=name,method=method,scheme=scheme,problem=problem,effective_Nx=nx,
                full_box_nside=48 if nx==0 else 2*nx,end=end,ranks=1,ic=str(ic),ic_sha256=sha(ic),
                param_sha256=sha(folder/'param.txt'),temporal='forward Euler',residual='Roe',mesh='static glass'))
    refs={}
    for name in ('constants.h','setup2D.cpp','vertex2D.h'):
        path=Path('/Users/zhenyuwu/Desktop/RD/src')/name
        shutil.copy2(path,root/'reference'/name);refs[str(path)]=sha(path)
    for name in ('run.py','analyze.py'):
        if (HERE/name).exists():shutil.copy2(HERE/name,root/name)
    shutil.copy2(REPO/'tests/rd/run_n_gauss3_split.py',root/'run_n_gauss3_split.py')
    write(root/'campaign.json',dict(test_name='Sod_2d_Morton',methods=methods,cases=cases,
        source_tar_sha256=prov['source_tar_sha256'],source_files_checked=len(checked),source_archive=str(control),
        gamma=GAMMA,box_size=2.,left_state=[1.,0.,1.],right_state=[.125,0.,.1],
        high_density_interval=[.5,1.5],tube_interval=[1.,2.],coordinates='xi=x-1; tau=t',
        courant=.4,max_timestep=.02,final_time=.2,mesh='Wrapped relaxed SWIFT glass128; Nx128 uses periodic 2x2 tiling, scaled to a box of side2.',
        glass_source=str(glass),glass_sha256=sha(glass),uniform_source=str(uniform_source),uniform_source_sha256=sha(uniform_source),
        environment={k:ENV[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')},
        references=refs,workers=2,
        limits='Morton primitive states/gamma/CFL/first-order Roe LDA/N, with glass. Time=.2 and box2 follow the local standalone SODX source, not verified original Fig7 metadata. AREPO carrier/tree timestep and power-of-two rounding differ from original nodal RD CFL; no claim of identical timestep histories. No new limiter or floor.'))
    print('Prepared Sod_2d_Morton: two builds, two uniform gates, four science runs.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('prepare','build','uniform','science'))
    p.add_argument('root',type=Path)
    p.add_argument('--control',type=Path,default=Path('/Users/zhenyuwu/arepo_rd/local_runs/sod_static_matched_20260928_v1'))
    p.add_argument('--glass',type=Path,default=Path('/Users/zhenyuwu/SWIFT/examples/HydroTests/GreshoVortex_2D/glassPlane_128.hdf5'))
    a=p.parse_args();root=a.root.resolve()
    if a.action=='prepare':prepare(root,a.control.resolve(),a.glass.resolve())
    elif a.action=='build':build(root,None)
    else:run(root,a.action,None,2)
