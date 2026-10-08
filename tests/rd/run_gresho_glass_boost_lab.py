#!/usr/bin/env python3
"""Matched glass48 Gresho boost10, lab-frame N/LDA static/moving comparison.

Freeze the working source and build four independent native binaries. Uniform
and short Gresho gates precede t=1 science; no solver tolerances are changed.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess

import h5py
import numpy as np

from run_n_gauss3_split import REPO, ENV, sha, write, rewrite, build, run, state


def prepare(root, glass):
    root.mkdir(parents=True, exist_ok=False)
    source = root / 'source'
    source.mkdir()
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    subprocess.run(['git', 'archive', '-o', str(root / 'base.tar'), commit], cwd=REPO, check=True)
    subprocess.run(['tar', '-xf', str(root / 'base.tar'), '-C', str(source)], check=True)
    hashes = {}
    for name in subprocess.check_output(['git', 'ls-files', '-z'], cwd=REPO).decode().split('\0'):
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
    for name in ('run_n_gauss3_split.py', Path(__file__).name):
        shutil.copy2(REPO / 'tests/rd' / name, root / name)
        shutil.copy2(REPO / 'tests/rd' / name, source / 'tests/rd' / name)
    (root / 'working_tree.patch').write_bytes(subprocess.check_output(['git', 'diff', '--binary', 'HEAD'], cwd=REPO))
    subprocess.run(['tar', '-cf', str(root / 'source.tar'), '-C', str(source), '.'], check=True)
    write(root / 'source_provenance.json', dict(base_commit=commit,
        source_tar_sha256=sha(root / 'source.tar'), tracked_hashes=hashes,
        local_systype_sha256=sha(source / 'Makefile.systype'),
        runner_sha256=sha(root / Path(__file__).name),
        environment={k: ENV[k] for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS')}))
    for d in ('configs', 'inputs', 'runs', 'artifacts'):
        (root / d).mkdir()
    shutil.copy2(glass, root / 'inputs/glassPlane_48_source.hdf5')
    with h5py.File(glass) as f:
        assert np.all(np.asarray(f['Header'].attrs['BoxSize']) == 1.)
        raw = f['PartType0/Coordinates'][:, :2]
    xy = raw % 1.
    assert xy.shape == (2304, 2) and len(np.unique(xy, axis=0)) == 2304
    spec = importlib.util.spec_from_file_location('ic', source / 'examples/gresho_2d/create_mmrd_ics.py')
    ic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ic)
    rho, vx, vy, p = ic.gresho_state(xy)
    ic.write_ic(root / 'inputs/gresho_b10.hdf5', xy, rho, vx + 10., vy, p)
    ic.write_ic(root / 'inputs/uniform_b10.hdf5', xy, rho, np.full(len(xy), 10.), np.zeros(len(xy)), 5.)
    template = (source / 'examples/gresho_2d/param_F_con_cm_A4b10.txt').read_text()
    methods, cases = [], []
    for scheme in ('N', 'LDA'):
        for mesh in ('static', 'moving'):
            method = f'{scheme}_{mesh}_lab'
            methods.append(method)
            template_name = ('Config_RD_RK2_LDA_GAUSS3_EQUAL_SPLIT.sh' if mesh == 'static'
                             else 'Config_RD_ALE_LDA_GAUSS3_EQUAL_SPLIT_LAB.sh')
            cfg = (source / 'examples/yee_2d' / template_name).read_text()
            cfg = '\n'.join(line for line in cfg.splitlines() if not line.startswith('#'))
            cfg = '# Gresho glass48 boost10; lab frame; see campaign.json.\n' + cfg + '\n'
            cfg = cfg.replace('GAMMA=1.4', 'GAMMA=(5.0/3.0)').replace('LDA_SCHEME', scheme + '_SCHEME')
            if scheme == 'N':
                cfg = re.sub(r'^RD_ALE_CONTOUR.*\n', '', cfg, flags=re.M)
                if mesh == 'moving':
                    cfg += '\nRD_ALE_SPLIT_MESH_VELOCITY\n'
            if mesh == 'moving':
                cfg += '\nRD_ALE_CFL_TIMESTEP\nRD_ALE_CFL_DIAGNOSTIC\n'
            assert 'RD_ELEMENT_COMOVING_FRAME' not in cfg
            (root / 'configs' / f'{method}.sh').write_text(cfg)
            for horizon, end in (('uniform', .03125), ('pilot', .03125), ('science', 1.)):
                name = f'{horizon}_{method}'
                folder = root / 'runs' / name
                folder.mkdir()
                inp = root / 'inputs' / ('uniform_b10.hdf5' if horizon == 'uniform' else 'gresho_b10.hdf5')
                param = rewrite(template, dict(InitCondFile=inp.with_suffix(''), OutputDir=str(folder / 'output') + '/',
                    TimeMax=end, TimeBetSnapshot=.5 if horizon == 'science' else end,
                    MaxSizeTimestep=1/4096, MinSizeTimestep=1e-8, MaxMemSize=512))
                if mesh == 'static':
                    param = re.sub(r'^(CellShapingSpeed|CellMaxAngleFactor)\s+.*\n', '', param, flags=re.M)
                (folder / 'param.txt').write_text(param)
                cases.append(dict(name=name, method=method, scheme=scheme, mesh=mesh, frame='lab',
                    residual='Roe split' if scheme == 'N' else 'Gauss3', boost=10.,
                    problem='uniform' if horizon == 'uniform' else 'gresho', horizon=horizon, end=end,
                    ic=str(inp), ic_sha256=sha(inp), param_sha256=sha(folder / 'param.txt'), ranks=1))
    write(root / 'campaign.json', dict(methods=methods, cases=cases, scope=__doc__, setup=dict(
        n=48, nodes=len(xy), box=1., gamma=5/3, boost=[10., 0.], CFL=.3, cap=1/4096,
        min_dt=1e-8, glass_source=str(glass), glass_sha256=sha(glass),
        wrapped_coordinate_components=int(np.count_nonzero(raw != xy)),
        topology='Current one-rebuild ALE hooks, Arpaia weights; no topology repair',
        time_mass='N lumped; LDA default mixed-stage F1'),
        limits='Single resolution and boost; no convergence or boost-invariance claim. Strict existing 1e-12 uniform gate.'))
    print('Prepared 12 cases and four independent configurations.', flush=True)


def gate(root, horizon):
    rows = []
    for c in json.loads((root / 'campaign.json').read_text())['cases']:
        if c['horizon'] != horizon:
            continue
        folder = root / 'runs' / c['name']
        meta = json.loads((folder / 'run_status.json').read_text())
        log = (folder / 'run.log').read_text(errors='replace')
        snapshots = sorted((folder / 'output').glob('snap_*.hdf5'))
        row = dict(name=c['name'], returncode=meta['returncode'], passed=False)
        if snapshots:
            a, b = state(snapshots[0]), state(snapshots[-1])
            assert np.array_equal(a['id'], b['id'])
            finite = all(np.isfinite(b[k]).all() for k in ('rho', 'p', 'v', 'mass', 'xy'))
            sync = re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*([\deE.+-]+),\s+Systemstep:\s*([\deE.+-]+)', log)
            printed_dt = [float(s[2]) for s in sync[1:]]
            row.update(time=b['time'], finite=finite, rho_min=float(b['rho'].min()), p_min=float(b['p'].min()),
                       steps=int(sync[-1][0]) if sync else None,
                       printed_systemstep_min=min(printed_dt) if printed_dt else None,
                       printed_systemstep_max=max(printed_dt) if printed_dt else None)
            row['passed'] = bool(meta['returncode'] == 0 and 'bye!' in log and finite and
                                 abs(b['time']-c['end']) < 1e-12 and row['rho_min']>0 and row['p_min']>0)
            if horizon == 'uniform':
                defects = {k: float(np.max(abs(b[k]-a[k]))) for k in ('rho', 'v', 'p')}
                row.update(defects=defects, threshold=1e-12)
                row['passed'] &= max(defects.values()) < 1e-12
        rows.append(row)
    write(root / f'gate_{horizon}.json', rows)
    print(json.dumps(rows, indent=2), flush=True)
    return all(r['passed'] for r in rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'build', 'uniform', 'pilot', 'science', 'gate'))
    parser.add_argument('root', type=Path)
    parser.add_argument('--glass', type=Path)
    parser.add_argument('--horizon', choices=('uniform', 'pilot', 'science'), default='uniform')
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action == 'prepare':
        prepare(root, args.glass.resolve())
    elif args.action == 'build':
        build(root, None)
    elif args.action == 'gate':
        raise SystemExit(0 if gate(root, args.horizon) else 1)
    else:
        if args.action != 'uniform':
            assert gate(root, 'uniform'), 'Uniform gate failed; inspect preserved results before further runs.'
        if args.action == 'science':
            assert gate(root, 'pilot'), 'Pilot gate failed; preserve and inspect.'
        selected = [c['name'] for c in json.loads((root / 'campaign.json').read_text())['cases']
                    if c['horizon'] == args.action]
        run(root, 'uniform' if args.action == 'uniform' else 'science', selected, 4)
        raise SystemExit(0 if gate(root, args.action) else 1)
