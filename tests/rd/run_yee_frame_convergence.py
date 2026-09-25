#!/usr/bin/env python3
"""Paired current-source moving Yee convergence; reuse verified native binaries."""
import argparse, json, shutil
from pathlib import Path
import h5py
import numpy as np
from run_n_gauss3_split import REPO, sha, write, rewrite, run

def prepare(root):
    root.mkdir(exist_ok=False)
    archives = {'lab': REPO.parent/'local_runs/sod_kh_lab_frame_20260924_v1',
                'comoving': REPO.parent/'local_runs/n_gauss3_split_20260924_v1'}
    old = REPO.parent/'local_runs/lda_moving_baseline_glass_20260911'
    prov=json.loads((archives['lab']/'source_provenance.json').read_text())
    checked=0
    for f,h in prov['tracked_hashes'].items():
        if f.startswith('src/') or f in ('Makefile','defines_extra'):
            assert sha(REPO/f)==h, f
            checked+=1
    for folder in ('inputs','runs','artifacts','configs','figures'):
        (root/folder).mkdir()
    for f in ('source.tar','source_provenance.json'):
        shutil.copy2(archives['lab']/f,root/f)
    assert sha(root/'source.tar')==prov['source_tar_sha256']
    template=(REPO.parent/'local_runs/moving_equal_split_stages_20260914_v4/runs/yee_lda_split/param.txt').read_text()
    for n in (48,96,192):
        shutil.copy2(old/'inputs'/f'yee_glass{n}.hdf5',root/'inputs'/f'yee_glass{n}.hdf5')
        with h5py.File(root/'inputs'/f'yee_glass{n}.hdf5') as f:
            p=f['PartType0'];xy=p['Coordinates'][:,:2]-5;r2=(xy*xy).sum(axis=1)
            rho=(1-.4*25/(8*np.pi**2*1.4)*np.exp(1-r2))**2.5
            factor=2.5/np.pi*np.exp(.5*(1-r2))
            velocity=np.column_stack((1-xy[:,1]*factor,xy[:,0]*factor))
            assert len(rho)==n*n
            assert np.max(abs(p['Masses'][:]-rho))<1e-13
            assert np.max(abs(p['Velocities'][:,:2]-velocity))<1e-13
    cases=[];methods=[];uniforms={}
    for scheme,residual in (('N','roe_split'),('LDA','gauss3')):
      for frame,archive in archives.items():
        previous=f'{scheme}_{residual}_sod'+('_lab' if frame=='lab' else '')
        method=f'{scheme}_{frame}';methods.append(method)
        artifact=archive/'artifacts'/previous
        meta=json.loads((artifact/'provenance.json').read_text())
        assert meta['source_tar_sha256']==prov['source_tar_sha256']
        assert sha(artifact/'Arepo')==meta['binary_sha256']
        assert sha(artifact/'Config.sh')==meta['config_sha256']
        shutil.copytree(artifact,root/'artifacts'/method)
        shutil.copy2(artifact/'Config.sh',root/'configs'/f'{method}.sh')
        uniform=archive/'runs'/f'uniform_{previous}'
        shutil.copytree(uniform,root/'runs'/f'uniform_{method}')
        uniforms[method]=str(uniform)
        for n in (48,96,192):
          for factor in ((1,2) if n==96 else (1,)):
            denom=256*(n//48)*factor
            name=f'yee_{method}_n{n}_dt{denom}';folder=root/'runs'/name;folder.mkdir()
            ic=root/'inputs'/f'yee_glass{n}.hdf5'
            param=rewrite(template,dict(InitCondFile=ic.with_suffix(''),OutputDir=str(folder/'output')+'/',
                  TimeMax=1,TimeBetSnapshot=.5,TimeBetStatistics=.5,MaxSizeTimestep=1/denom))
            (folder/'param.txt').write_text(param)
            cases.append(dict(name=name,method=method,problem='yee',scheme=scheme,residual=residual,
                 frame=frame,n=n,dt_denominator=denom,refinement=factor,boost=1.,end=1.,
                 ic=str(ic),ic_sha256=sha(ic),param_sha256=sha(folder/'param.txt'),ranks=1))
    for scheme in ('N','LDA'):
        a=(root/'configs'/f'{scheme}_lab.sh').read_text()
        b=(root/'configs'/f'{scheme}_comoving.sh').read_text()
        assert a==b.replace('RD_ELEMENT_COMOVING_FRAME\n','')
    write(root/'campaign.json',dict(methods=methods,cases=cases,source_files_checked=checked,
          source_tar_sha256=prov['source_tar_sha256'],reused_uniform_controls=uniforms,
          settings='glass48/96/192 squared, box10, gamma1.4, beta5, boost=(1,0), t1, CFL.2, dt cap1/256,1/512,1/1024; n96 dt-halving controls. Current Arpaia, no topology repair, new-connectivity two sweeps. Final m/rho area weighted norms.',
          limits='Measured coupled h/dt convergence, not fixed-h time order. Reused immutable binaries and uniform gates, all Yee runs new.'))
    for f in (Path(__file__).name,'run_n_gauss3_split.py'):
        shutil.copy2(REPO/'tests/rd'/f,root/f)
    print('Prepared 16 new paired Yee runs with 4 verified binaries.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','run'))
    p.add_argument('root',type=Path);p.add_argument('--select',nargs='+');p.add_argument('--workers',type=int,default=4)
    a=p.parse_args();root=a.root.resolve()
    if a.action=='prepare':prepare(root)
    else:run(root,'science',a.select,a.workers)
