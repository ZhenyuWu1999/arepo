#!/usr/bin/env python3
"""Extend verified lab-frame Yee to384² and match static N/Roe,LDA/Gauss3."""
import argparse,importlib.util,json,re,shutil,subprocess
from pathlib import Path
import h5py
import numpy as np
from run_n_gauss3_split import REPO,sha,write,rewrite,build,run

CONTROL=REPO.parent/'local_runs/yee_frame_convergence_20260924_v1'

def prepare(root):
    root.mkdir(exist_ok=False)
    for d in ('source','artifacts','configs','runs','inputs','figures'):(root/d).mkdir()
    prov=json.loads((CONTROL/'source_provenance.json').read_text());checked=0
    for f,h in prov['tracked_hashes'].items():
        if f.startswith('src/') or f in ('Makefile','defines_extra'):
            assert sha(REPO/f)==h,f;checked+=1
    for f in ('source.tar','source_provenance.json'):shutil.copy2(CONTROL/f,root/f)
    assert sha(root/'source.tar')==prov['source_tar_sha256']
    subprocess.run(['tar','-xf',str(root/'source.tar'),'-C',str(root/'source')],check=True)
    oldhelper=REPO.parent/'local_runs/lda_baseline_glass_20260911/source_helpers/yee_boost_common.py'
    shutil.copy2(oldhelper,root/'yee_boost_common.py')
    spec=importlib.util.spec_from_file_location('yee_common',root/'yee_boost_common.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    glass=Path('/Users/zhenyuwu/SWIFT/examples/HydroTests/GreshoVortex_2D/glassPlane_48.hdf5')
    shutil.copy2(glass,root/'inputs/glassPlane_48.hdf5');helper.SWIFT_GLASS_48=root/'inputs/glassPlane_48.hdf5'
    for n in (48,96,192):
        old=CONTROL/'inputs'/f'yee_glass{n}.hdf5';shutil.copy2(old,root/'inputs'/old.name)
        positions,_=helper.swift48_tiled_mesh(n)
        with h5py.File(old) as f:
            assert np.array_equal(f['PartType0/Coordinates'][:],positions)
            state=helper.analytic_state(positions,0,1)
            for key,field in [('Masses','density'),('Velocities','velocity'),('InternalEnergy','internal_energy')]:
                assert np.array_equal(f['PartType0'][key][:],state[field]),(n,key)
    positions,meta=helper.swift48_tiled_mesh(384)
    helper.write_initial_conditions(root/'inputs/yee_glass384.hdf5',positions,'swift48_tiled',384,0,0,1,meta)
    with h5py.File(root/'inputs/yee_glass384.hdf5') as f:
        assert len(f['PartType0/Coordinates'])==384**2
        assert len(np.unique(f['PartType0/Coordinates'][:,:2],axis=0))==384**2
    oldcampaign=json.loads((CONTROL/'campaign.json').read_text());cases=[];controls=[];methods=[]
    oldtemplate=(CONTROL/'runs/yee_LDA_lab_n48_dt256/param.txt').read_text()
    for scheme,residual in (('N','roe_split'),('LDA','gauss3')):
        moving=f'{scheme}_moving';static=f'{scheme}_static';methods.extend([static,moving])
        oldartifact=CONTROL/'artifacts'/f'{scheme}_lab'
        m=json.loads((oldartifact/'provenance.json').read_text())
        assert sha(oldartifact/'Arepo')==m['binary_sha256'] and sha(oldartifact/'Config.sh')==m['config_sha256']
        assert m['source_tar_sha256']==prov['source_tar_sha256']
        shutil.copytree(oldartifact,root/'artifacts'/moving)
        moving_cfg=(oldartifact/'Config.sh').read_text()
        (root/'configs'/f'{moving}.sh').write_text(moving_cfg)
        static_cfg=re.sub(r'^(RD_ALE_EQUALSTEP|RD_ALE_SPLIT_MESH_VELOCITY|REGULARIZE_MESH_[A-Z_]+)\n','',moving_cfg,flags=re.M)
        static_cfg=re.sub(r'^#.*\n','',static_cfg,flags=re.M)
        static_cfg='# Matched static control: N/Roe or LDA/Gauss3, same temporal choice.\n'+static_cfg+'\nVORONOI_STATIC_MESH\n'
        (root/'configs'/f'{static}.sh').write_text(static_cfg)
        uniform_old=CONTROL/'runs'/f'uniform_{scheme}_lab'
        shutil.copytree(uniform_old,root/'runs'/f'uniform_{moving}')
        uniform_params=(uniform_old/'param.txt').read_text();oldic=Path(re.search(r'^InitCondFile\s+(.*)$',uniform_params,re.M).group(1)+'.hdf5')
        uniform_ic=root/'inputs'/oldic.name
        if not uniform_ic.exists():shutil.copy2(oldic,uniform_ic)
        def add(method,n,problem='yee',denom=None,end=1):
            mesh='static' if method.endswith('_static') else 'moving'
            name=f'yee_{method}_n{n}_dt{denom}' if problem=='yee' else f'uniform_{method}'
            folder=root/'runs'/name;folder.mkdir()
            ic=root/'inputs'/f'yee_glass{n}.hdf5' if problem=='yee' else uniform_ic
            text=oldtemplate if problem=='yee' else uniform_params
            updates=dict(InitCondFile=ic.with_suffix(''),OutputDir=str(folder/'output')+'/')
            if problem=='yee':updates.update(TimeMax=end,TimeBetSnapshot=.5,TimeBetStatistics=.5,MaxSizeTimestep=1/denom,MaxMemSize=1024 if n==384 else 512)
            text=rewrite(text,updates)
            if mesh=='static':text=re.sub(r'^(CellShapingSpeed|CellMaxAngleFactor)\s+.*\n','',text,flags=re.M)
            (folder/'param.txt').write_text(text)
            cases.append(dict(name=name,method=method,scheme=scheme,residual=residual,mesh=mesh,frame='lab',problem=problem,n=n,
                dt_denominator=denom,boost=1.,end=end,ic=str(ic),ic_sha256=sha(ic),param_sha256=sha(folder/'param.txt'),ranks=1))
        add(static,48,'uniform',end=.03125)
        add(moving,384,denom=2048)
        for n in (48,96,192,384):add(static,n,denom=256*n//48)
        for c in oldcampaign['cases']:
            if c['scheme']==scheme and c['frame']=='lab' and c['refinement']==1:
                olddir=CONTROL/'runs'/c['name']
                controls.append(dict(c,method=moving,mesh='moving',directory=str(olddir),binary_sha256=m['binary_sha256']))
    # Start the two moving384 cases first; use remaining slots for static work.
    cases.sort(key=lambda c:(c['problem']!='uniform',c['mesh']!='moving',c['n'],c['scheme']))
    write(root/'campaign.json',dict(methods=methods,cases=cases,controls=controls,source_files_checked=checked,
          source_tar_sha256=prov['source_tar_sha256'],scope=__doc__,mesh_family='Same SWIFT glass48 tiled1,2,4,8 times per dimension. Independent glass realizations are not used.',
          settings='boost1, t1, box10, gamma1.4, beta5, lab only. Matched Nx48/96/192/384, dt caps1/256,1/512,1/1024,1/2048, CFL.2. N/Roe+lumped, LDA/Gauss3+mixed F1. Moving uses existing regularization, Arpaia, no topology repair.',
          resource='At most4 singleton processes, one OMP/BLAS thread each; memory cap1024MiB for384 and512MiB otherwise.',
          limits='Six moving48/96/192 science controls reused, not rerun. Two moving384, eight static science, two static uniform runs new. Moving/static compares complete implementations; global conservation and fixed-h temporal order remain separate.'))
    for file in (Path(__file__).name,'run_n_gauss3_split.py'):shutil.copy2(REPO/'tests/rd'/file,root/file)
    print('Prepared12 new runs,2 new static builds and6 verified archived moving controls.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','build','run'));p.add_argument('root',type=Path)
    p.add_argument('--group',choices=('uniform','science','all'),default='uniform');p.add_argument('--select',nargs='+');p.add_argument('--workers',type=int,choices=(1,2,3,4),default=4)
    a=p.parse_args();root=a.root.resolve()
    if a.action=='prepare':prepare(root)
    elif a.action=='build':build(root,a.select or ['N_static','LDA_static'])
    else:run(root,a.group,a.select,a.workers)
