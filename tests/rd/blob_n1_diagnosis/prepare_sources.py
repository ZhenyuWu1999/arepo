#!/usr/bin/env python3
"""Freeze/build read-only Blob comparison sources; never run a full Blob.

The AREPO revision comes from the supplied COSMA provenance. The predecessor
revision is explicit. Generated files belong in a fresh external directory.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--predecessor',type=Path,required=True,help='rdsolver Git root')
    p.add_argument('--predecessor-ref',default='adfbe55586fc926f1911dbecfbdb915c8f667c11')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--reference-svg',type=Path,required=True,help='primary cloudMass.svg saved for numerical tracing')
    a=p.parse_args();root=a.out.resolve();root.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parents[3]
    source=json.loads((a.bundle/'provenance/N/source_provenance.json').read_text())
    ref=source['base_commit'];env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    subprocess.run(['git','archive','--format=tar','-o',str(root/'standalone.tar'),a.predecessor_ref],cwd=a.predecessor,check=True)
    (root/'standalone').mkdir()
    with tarfile.open(root/'standalone.tar') as tar:tar.extractall(root/'standalone',filter='data')
    (root/'current').mkdir()
    names=['src/hydro/rd_euler.c','src/hydro/rd_euler.h','src/hydro/rd_linalg.c',
           'src/hydro/rd_linalg.h','src/mesh/rd_simplex_geometry.c','src/mesh/rd_simplex_geometry.h',
           'src/hydro/rd_state.c','src/hydro/residual_distribution_solver.c']
    for name in names:
        raw=subprocess.check_output(['git','show',ref+':'+name],cwd=repo)
        assert hashlib.sha256(raw).hexdigest()==source['tracked_and_untracked_hashes'][name]
        (root/'current'/Path(name).name).write_bytes(raw)
    before={str(f.relative_to(root)):sha(f) for folder in ['standalone','current']
            for f in (root/folder).rglob('*') if f.is_file()}
    old=root/'standalone/rd'
    template=(old/'constants3D.h.TEMPLATE').read_text()
    config=template.replace('#define SEDOV3D','// #define SEDOV3D').replace('// #define BLOB','#define BLOB')
    config=config.replace('#define DRIFT','// #define DRIFT').replace('// #define FIRST_ORDER','#define FIRST_ORDER')
    (old/'constants3D.h').write_text(config)
    for name in ['kernel_probe.cpp','ic_probe.cpp','mesh_rhs.c']:
        shutil.copy2(Path(__file__).with_name(name),root/name)
    shutil.copy2(a.reference_svg,root/'reference_cloudMass.svg')
    includes=['-I'+str(old),'-I'+str(root/'current')]
    blas=Path('/opt/homebrew/opt/openblas')
    if blas.exists():
        includes+=['-I'+str(blas/'include')];libs=['-L'+str(blas/'lib'),'-lopenblas']
    else:libs=['-llapacke','-llapack','-lblas']
    cc=os.environ.get('CC','cc');cxx=os.environ.get('CXX','c++');commands=[]
    for name,out in [('rd_euler','rd_euler'),('rd_linalg','rd_linalg'),('rd_simplex_geometry','rd_geometry')]:
        commands.append([cc,'-std=c99','-O2','-fPIC',*includes,'-c',str(root/'current'/f'{name}.c'),'-o',str(root/f'{out}.o')])
    objects=[str(root/f'{n}.o') for n in ['rd_euler','rd_linalg','rd_geometry']]
    commands += [[cxx,'-std=c++14','-O2',str(root/'kernel_probe.cpp'),str(old/'inverse.cpp'),*objects,*includes,*libs,'-o',str(root/'kernel_probe')],
                 [cxx,'-std=c++14','-O2',str(root/'ic_probe.cpp'),str(old/'setup3D.cpp'),*includes,'-o',str(root/'ic_probe')],
                 [cc,'-std=c99','-O2','-shared','-fPIC',str(root/'mesh_rhs.c'),*objects,*includes,*libs,'-o',str(root/'mesh_rhs.dylib')]]
    for i,command in enumerate(commands):
        with (root/f'build_{i}.log').open('x') as log:
            subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    result=dict(arepo_ref=ref,predecessor_ref=a.predecessor_ref,source_hashes_before_config=before,
        configuration_changes=['BLOB, FIRST_ORDER, no DRIFT in frozen copy only'],
        config_sha256=sha(old/'constants3D.h'),commands=commands,
        binary_hashes={n:sha(root/n) for n in ['kernel_probe','ic_probe','mesh_rhs.dylib']},
        reference_svg_sha256=sha(root/'reference_cloudMass.svg'),threads={'OMP_NUM_THREADS':1,'OPENBLAS_NUM_THREADS':1})
    (root/'prepared_sources.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Prepared',root,'; no hydrodynamic run was launched.')


if __name__=='__main__':main()
