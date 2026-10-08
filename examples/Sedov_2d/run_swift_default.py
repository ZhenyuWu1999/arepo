#!/usr/bin/env python3
"""Freeze, build and run the unchanged SWIFT SedovBlast_2D example locally."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time

SWIFT = Path('/Users/zhenyuwu/SWIFT')
GLASS = Path('/Users/zhenyuwu/arepo_rd/local_runs/swift_glass/glassPlane_128.hdf5')
ENV = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def invoke(argv, cwd, log):
    start = time.time()
    with open(log, 'w') as stream:
        result = subprocess.run(argv, cwd=cwd, env=ENV, stdout=stream, stderr=subprocess.STDOUT)
    status = dict(argv=list(map(str, argv)), cwd=str(cwd), returncode=result.returncode,
                  elapsed_seconds=time.time()-start)
    write(str(log)+'.json', status)
    print(json.dumps(status), flush=True)
    if result.returncode:
        raise RuntimeError(f'Command failed; see {log}')
    return status


def main(root):
    root.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, root/'run_swift_default.py')
    revision = subprocess.check_output(['git','rev-parse','HEAD'], cwd=SWIFT, text=True).strip()
    status = subprocess.check_output(['git','status','--porcelain'], cwd=SWIFT, text=True)
    if status.strip():
        raise RuntimeError('SWIFT tracked/untracked work needs explicit source snapshot handling')
    subprocess.run(['git','archive','--format=tar',f'--output={root}/source.tar',revision], cwd=SWIFT, check=True)
    source=root/'source'; source.mkdir()
    with tarfile.open(root/'source.tar') as archive:
        archive.extractall(source, filter='data')
    write(root/'source_provenance.json',dict(repository=str(SWIFT), revision=revision,
        git_status=status, source_sha256=sha(root/'source.tar'),
        runner_sha256=sha(__file__), glass_source=str(GLASS), glass_sha256=sha(GLASS),
        environment={key:ENV[key] for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')},
        note='Fresh isolated build from exact git archive. No hydro source edits.'))
    invoke(['sh','autogen.sh'], source, root/'autogen.log')
    build=root/'build'; build.mkdir()
    argv=[str(source/'configure'),'CC=clang','MPICC=mpicc','--enable-mpi',
        '--disable-compiler-warnings','--disable-vec','--with-hdf5=/opt/homebrew/bin/h5pcc',
        '--with-hydro=sphenix','--with-hydro-dimension=2','--without-fftw','--without-gsl',
        '--without-metis','--without-parmetis','--without-jemalloc','--without-tbbmalloc','--without-numa']
    invoke(argv, build, root/'configure.log')
    invoke(['make','-j6'], build, root/'build.log')
    artifact=root/'artifact'; artifact.mkdir()
    for name in ('swift','config.h','config.log','config.status'):
        shutil.copy2(build/name, artifact/name)
    invoke(['otool','-L',str(artifact/'swift')], root, artifact/'linkage.log')
    invoke([str(artifact/'swift'),'--help'], root, artifact/'help.log')
    write(artifact/'provenance.json',dict(source_revision=revision, source_sha256=sha(root/'source.tar'),
        binary_sha256=sha(artifact/'swift'), config_sha256=sha(artifact/'config.h'),
        configure_command=argv, metadata_note='Archive build has no .git; source revision is recorded here.'))
    run=root/'run'; run.mkdir()
    example=source/'examples/HydroTests/SedovBlast_2D'
    for name in ('makeIC.py','sedov.yml','run.sh','plotSolution.py','getGlass.sh'):
        shutil.copy2(example/name, run/name)
    shutil.copy2(GLASS, run/'glassPlane_128.hdf5')
    invoke([sys.executable,'makeIC.py'], run, run/'make_ic.log')
    write(run/'inputs.json',{name:sha(run/name) for name in ('sedov.yml','makeIC.py','sedov.hdf5','glassPlane_128.hdf5')})
    result=invoke([str(artifact/'swift'),'--hydro','--limiter','--threads=1','sedov.yml'],run,run/'output.log')
    write(run/'run_status.json',result)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    main(parser.parse_args().root.resolve())
