#!/usr/bin/env python3
"""Same-source static counterparts and first-order LDA controls for Sod review."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from run_n_gauss3_split import REPO, ENV, sha, write, rewrite, build, run


def prepare(root, control):
    root.mkdir(parents=True, exist_ok=False)
    for name in ('source','configs','inputs','runs','artifacts'):
        (root/name).mkdir()
    provenance=json.loads((control/'source_provenance.json').read_text())
    assert sha(control/'source.tar')==provenance['source_tar_sha256']
    checked=[]
    for name,expected in provenance['tracked_hashes'].items():
        if name.startswith('src/') or name in ('Makefile','defines_extra'):
            assert sha(REPO/name)==expected,name
            checked.append(name)
    shutil.copy2(control/'source.tar',root/'source.tar')
    shutil.copy2(control/'source_provenance.json',root/'source_provenance.json')
    subprocess.run(['tar','-xf',str(root/'source.tar'),'-C',str(root/'source')],check=True)
    old=json.loads((control/'campaign.json').read_text())
    choices=[('N_roe_rk2_static','N','roe_split','lumped RK2'),
             ('LDA_gauss3_f1_static','LDA','gauss3','mixed-stage F1'),
             ('LDA_gauss3_fe_static','LDA','gauss3','forward Euler'),
             ('LDA_roe_fe_static','LDA','roe_split','forward Euler')]
    remove={'REGULARIZE_MESH_CM_DRIFT','REGULARIZE_MESH_CM_DRIFT_USE_SOUNDSPEED',
            'REGULARIZE_MESH_FACE_ANGLE','RD_ALE_EQUALSTEP',
            'RD_RK2_SPLIT_STAGES','RD_ALE_SPLIT_MESH_VELOCITY'}
    cases=[]
    for method,scheme,residual,temporal in choices:
        refmethod='N_roe_split_sod_lab' if scheme=='N' else 'LDA_gauss3_sod_lab'
        config=(control/'configs'/f'{refmethod}.sh').read_text()
        lines=[line for line in config.splitlines()
               if line.strip() and not line.startswith('#') and line not in remove]
        lines.append('VORONOI_STATIC_MESH')
        if residual=='roe_split':
            lines=[line for line in lines if not line.startswith('RD_ALE_CONTOUR')]
        if temporal=='forward Euler':
            # Stop after the full predictor; simply dropping RK2 would enter
            # the legacy two-call path, not this forward-Euler control.
            lines.append('RD_DIAG_PREDICTOR_ONLY')
        (root/'configs'/f'{method}.sh').write_text(
            '# Frozen same-source Sod static comparison; diagnostic FE only where explicit.\n'
            +'\n'.join(lines)+'\n')
        for problem in ('uniform','sod'):
            ref=next(c for c in old['cases'] if c['method']==refmethod and c['problem']==problem)
            inp=Path(ref['ic']);assert sha(inp)==ref['ic_sha256']
            target=root/'inputs'/inp.name
            if not target.exists():shutil.copy2(inp,target)
            name=f'{problem}_{method}';folder=root/'runs'/name;folder.mkdir()
            param=rewrite((control/'runs'/ref['name']/'param.txt').read_text(),
                dict(InitCondFile=target.with_suffix(''),OutputDir=str(folder/'output')+'/'))
            param='\n'.join(line for line in param.splitlines()
                if not line.startswith(('CellShapingSpeed','CellMaxAngleFactor')))+'\n'
            (folder/'param.txt').write_text(param)
            cases.append(dict(name=name,method=method,scheme=scheme,residual=residual,
                temporal=temporal,mesh='static',frame='lab',problem=problem,
                end=ref['end'],ranks=1,ic=str(target),ic_sha256=sha(target),
                param_sha256=sha(folder/'param.txt'),control_name=ref['name'],
                control_dir=str(control/'runs'/ref['name'])))
    write(root/'campaign.json',dict(methods=[c[0] for c in choices],cases=cases,
        control_archive=str(control),same_source=True,current_source_files_checked=checked,
        source_tar_sha256=provenance['source_tar_sha256'],environment={k:ENV[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')},
        setup='Glass128^2, effective tube Nx64, gamma1.4, rawt0.08/tau0.16, CFL0.08, cap1/3000; native static equal-step path, no new solver changes.',
        limits='Static and moving use the same CFL/cap but adaptive timestep histories may differ. FE controls isolate first-order updates; neither reproduces all Morton2023 settings.'))
    for name in (Path(__file__).name,'run_n_gauss3_split.py'):
        shutil.copy2(REPO/'tests/rd'/name,root/name)
    print('Prepared four static builds and eight runs (four uniform gates).',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('prepare','build','uniform','science'))
    p.add_argument('root',type=Path)
    p.add_argument('--control',type=Path,default=REPO.parent/'local_runs/sod_kh_lab_frame_20260924_v1')
    a=p.parse_args();root=a.root.resolve()
    if a.action=='prepare':prepare(root,a.control.resolve())
    elif a.action=='build':build(root,None)
    else:run(root,a.action,None,4)
