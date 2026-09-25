#!/usr/bin/env python3
"""Frozen current-source moving N/LDA x Gauss3/Roe-split Sod/KH comparison.

Reuse September 12 ICs and physical parameters, but use current one-rebuild
ALE hooks. The historical refreshed-basis implementation is a separate replay.
All native runs are single rank, with one OpenMP/BLAS thread, max four at once.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

import h5py
import numpy as np

REPO = Path(__file__).resolve().parents[2]
OLD = REPO.parent / 'local_runs/legacy_split_20260912'
ENV = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p, x):
    Path(p).write_text(json.dumps(x, indent=2) + '\n')

def rewrite(s, updates):
    for k, v in updates.items():
        s, n = re.subn(r'^' + re.escape(k) + r'\s+.*$', k + ' ' + str(v), s, flags=re.M)
        assert n == 1, (k, n)
    return s

def prepare(root):
    root.mkdir(parents=True, exist_ok=True)
    source = root / 'source'
    source.mkdir(exist_ok=False)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    subprocess.run(['git', 'archive', '-o', str(root / 'base.tar'), commit], cwd=REPO, check=True)
    subprocess.run(['tar', '-xf', str(root / 'base.tar'), '-C', str(source)], check=True)
    # Copy every current tracked source file, including pre-existing user edits.
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=REPO).decode().split('\0')
    hashes = {}
    for name in tracked:
        if not name:
            continue
        p = REPO / name
        if p.is_file():
            (source / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, source / name)
            hashes[name] = sha(p)
        elif (source / name).is_file():
            (source / name).unlink()
    shutil.copy2(REPO / 'Makefile.systype', source / 'Makefile.systype')
    shutil.copy2(__file__, root / Path(__file__).name)
    (root / 'working_tree.patch').write_bytes(subprocess.check_output(['git', 'diff', '--binary', 'HEAD'], cwd=REPO))
    subprocess.run(['tar', '-cf', str(root / 'source.tar'), '-C', str(source), '.'], check=True)
    write(root / 'source_provenance.json', dict(base_commit=commit, source_tar_sha256=sha(root / 'source.tar'),
        tracked_hashes=hashes, environment={k: ENV[k] for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS')}))
    for d in ('configs', 'inputs', 'runs', 'artifacts'):
        (root / d).mkdir()
    for name in ('kh_smooth.hdf5', 'sod_glass_nx64.hdf5', 'uniform_glass48.hdf5'):
        shutil.copy2(OLD / 'inputs' / name, root / 'inputs' / name)
    base = (REPO / 'examples/yee_2d/Config_RD_ALE_LDA_GAUSS3_EQUAL_SPLIT.sh').read_text()
    cases = []
    methods = []
    templates = dict(kh='smooth_split_frame', sod='sod_split_frame', uniform='uniform_split_frame')
    for scheme in ('N', 'LDA'):
        for residual in ('gauss3', 'roe_split'):
            for family in ('kh', 'sod'):
                method = f'{scheme}_{residual}_{family}'
                methods.append(method)
                text = base.replace('LDA_SCHEME', scheme + '_SCHEME')
                if residual == 'roe_split':
                    text = re.sub(r'^RD_ALE_CONTOUR.*\n', '', text, flags=re.M) + '\nRD_ALE_SPLIT_MESH_VELOCITY\n'
                if family == 'kh':
                    text += '\nRD_ALE_CFL_TIMESTEP\n'
                text = '# Experimental matched residual comparison; see campaign.json.\n' + text
                (root / 'configs' / (method + '.sh')).write_text(text)
                for problem in ('uniform', family):
                    name = f'{problem}_{method}'
                    folder = root / 'runs' / name
                    folder.mkdir()
                    icname = dict(kh='kh_smooth', sod='sod_glass_nx64', uniform='uniform_glass48')[problem]
                    ic = root / 'inputs' / (icname + '.hdf5')
                    template = OLD / 'runs' / templates[problem] / 'param.txt'
                    param = rewrite(template.read_text(), dict(InitCondFile=ic.with_suffix(''),
                        OutputDir=str(folder / 'output') + '/'))
                    (folder / 'param.txt').write_text(param)
                    cases.append(dict(name=name, method=method, problem=problem, scheme=scheme,
                        residual=residual, end=dict(kh=10., sod=.08, uniform=.03125)[problem],
                        ic=str(ic), ic_sha256=sha(ic), param_sha256=sha(folder / 'param.txt'), ranks=1))
    write(root / 'campaign.json', dict(methods=methods, cases=cases, scope=__doc__,
        geometry='Current one-rebuild ALE begin/end hooks, both sweeps on new connectivity; Arpaia mass',
        kh='glass48², gamma1.4, rho1/2, p2.5, vx±.5, vy=.1sin(4pi x), tanh width .025, CFL.3, cap.02, t10',
        sod='box128², effective initial tube Nx64, gamma1.4, CFL.08, cap1/3000, t.08',
        frame='element mean mesh velocity', limits='No positivity limiter or timestep-acceptance repair added.'))
    print('Prepared', len(cases), 'cases and', len(methods), 'builds.', flush=True)

def build(root, selected):
    methods = json.loads((root / 'campaign.json').read_text())['methods']
    for method in methods:
        if selected and method not in selected:
            continue
        target = root / 'artifacts' / method
        target.mkdir(exist_ok=False)
        b = root / 'build' / method
        cfg = root / 'configs' / (method + '.sh')
        cmd = ['make', f'CONFIG={cfg}', f'BUILD_DIR={b}', f'EXEC={b}/Arepo', '-j4']
        print('BUILD', method, flush=True)
        start = time.monotonic()
        with (target / 'build.log').open('w') as f:
            r = subprocess.run(cmd, cwd=root / 'source', env=ENV, stdout=f, stderr=subprocess.STDOUT)
        meta = dict(command=cmd, returncode=r.returncode, seconds=time.monotonic()-start)
        write(target / 'build_status.json', meta)
        assert r.returncode == 0, str(target / 'build.log')
        for p in (b / 'Arepo', b / 'arepoconfig.h', b / 'version.c'):
            shutil.copy2(p, target / p.name)
        shutil.copy2(cfg, target / 'Config.sh')
        (target / 'Arepo').chmod(0o555)
        meta.update(binary_sha256=sha(target / 'Arepo'), config_sha256=sha(cfg),
                    source_tar_sha256=sha(root / 'source.tar'))
        write(target / 'provenance.json', meta)
        (target / 'linkage.txt').write_text(subprocess.check_output(['otool', '-L', str(target / 'Arepo')], text=True))
        print('BUILT', method, flush=True)

def state(path):
    with h5py.File(path) as f:
        p = f['PartType0']; ids = p['ParticleIDs'][:]; order = np.argsort(ids)
        rho = p['Density'][:][order]; mass = p['Masses'][:][order]
        vel = p['Velocities'][:][order, :2]; ei = p['InternalEnergy'][:][order]
        return dict(id=ids[order], xy=p['Coordinates'][:][order,:2], rho=rho, v=vel,
            p=p['Pressure'][:][order], mass=mass, w=mass/rho, time=float(f['Header'].attrs['Time']),
            totals=np.array([mass.sum(), np.sum(mass*vel[:,0]), np.sum(mass*vel[:,1]),
                             np.sum(mass*(ei+.5*np.sum(vel**2,axis=1)))]))

def run(root, group, selected, workers):
    cases = json.loads((root / 'campaign.json').read_text())['cases']
    cases = [c for c in cases if (group=='all' or (c['problem']=='uniform')==(group=='uniform'))
             and (not selected or c['name'] in selected)]
    if group == 'science':
        for method in {c['method'] for c in cases}:
            p = root / 'runs' / ('uniform_' + method)
            assert json.loads((p / 'run_status.json').read_text())['returncode'] == 0
            snapshots = sorted((p / 'output').glob('snap_*.hdf5'))
            a, b = state(snapshots[0]), state(snapshots[-1])
            defect = max(float(np.max(abs(b[k]-a[k]))) for k in ('rho','v','p'))
            assert defect < 1e-12, (method, defect)
    def one(c):
        p = root / 'runs' / c['name']
        assert not (p / 'run.log').exists(), c['name']
        binary = root / 'artifacts' / c['method'] / 'Arepo'
        meta = json.loads((binary.parent / 'provenance.json').read_text())
        assert sha(binary) == meta['binary_sha256']
        assert sha(c['ic']) == c['ic_sha256'] and sha(p / 'param.txt') == c['param_sha256']
        cmd = [str(binary), 'param.txt']; start = time.monotonic()
        print('START', c['name'], flush=True)
        with (p / 'run.log').open('w') as f:
            r = subprocess.run(cmd, cwd=p, env=ENV, stdout=f, stderr=subprocess.STDOUT)
        result = dict(name=c['name'], returncode=r.returncode, seconds=time.monotonic()-start,
                      binary_sha256=meta['binary_sha256'], command=cmd)
        write(p / 'run_status.json', result)
        print(json.dumps(result), flush=True)
        return result
    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(one, cases))
    write(root / ('status_' + group + '.json'), rows)

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('prepare','build','run'))
    p.add_argument('root', type=Path)
    p.add_argument('--select', nargs='+')
    p.add_argument('--group', choices=('all','uniform','science'), default='uniform')
    p.add_argument('--workers', type=int, choices=(1,2,3,4), default=4)
    a = p.parse_args(); root = a.root.resolve()
    if a.action == 'prepare': prepare(root)
    elif a.action == 'build': build(root,a.select)
    else: run(root,a.group,a.select,a.workers)
