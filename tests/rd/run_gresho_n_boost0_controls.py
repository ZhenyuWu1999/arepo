#!/usr/bin/env python3
"""Add matched N/static and N/moving boost0 controls to a frozen boost10 run."""
import argparse
import json
from pathlib import Path
import shutil

import h5py
import numpy as np

from run_n_gauss3_split import ENV, sha, write, rewrite, run
from run_gresho_glass_boost_lab import gate


def prepare(root, base):
    root.mkdir(parents=True, exist_ok=False)
    for name in ('artifacts', 'configs', 'inputs', 'runs'):
        (root / name).mkdir()
    old = json.loads((base / 'campaign.json').read_text())
    old_prov = json.loads((base / 'source_provenance.json').read_text())
    assert sha(base / 'source.tar') == old_prov['source_tar_sha256']
    (root / 'source').symlink_to(base / 'source', target_is_directory=True)
    shutil.copy2(base / 'source_provenance.json', root / 'source_provenance.json')
    for name in ('run_n_gauss3_split.py', 'run_gresho_glass_boost_lab.py', Path(__file__).name):
        shutil.copy2(Path(__file__).parent / name, root / name)
    inputs = []
    for problem in ('gresho', 'uniform'):
        source = base / 'inputs' / f'{problem}_b10.hdf5'
        target = root / 'inputs' / f'{problem}_b0.hdf5'
        shutil.copy2(source, target)
        with h5py.File(target, 'r+') as f:
            velocity = f['PartType0/Velocities'][:]
            velocity[:, 0] -= 10.
            f['PartType0/Velocities'][:] = velocity
        with h5py.File(source) as a, h5py.File(target) as b:
            for key in a['PartType0']:
                if key == 'Velocities':
                    delta = a['PartType0'][key][:] - b['PartType0'][key][:]
                    assert np.max(abs(delta - [10., 0., 0.])) == 0.
                else:
                    assert np.array_equal(a['PartType0'][key][:], b['PartType0'][key][:]), key
        inputs.append(dict(problem=problem, source=str(source), source_sha256=sha(source),
                           target=str(target), target_sha256=sha(target)))
    cases, binaries = [], []
    methods = ['N_static_lab', 'N_moving_lab']
    for method in methods:
        source = base / 'artifacts' / method
        meta = json.loads((source / 'provenance.json').read_text())
        assert sha(source / 'Arepo') == meta['binary_sha256']
        assert sha(source / 'Config.sh') == meta['config_sha256']
        shutil.copytree(source, root / 'artifacts' / method)
        shutil.copy2(source / 'Config.sh', root / 'configs' / (method + '.sh'))
        binaries.append(dict(method=method, reused_artifact=str(source),
                             binary_sha256=meta['binary_sha256'], config_sha256=meta['config_sha256']))
        for old_case in old['cases']:
            if old_case['method'] != method:
                continue
            c = dict(old_case)
            c['boost'] = 0.
            inp = root / 'inputs' / ('uniform_b0.hdf5' if c['problem']=='uniform' else 'gresho_b0.hdf5')
            folder = root / 'runs' / c['name']
            folder.mkdir()
            template = (base / 'runs' / c['name'] / 'param.txt').read_text()
            param = rewrite(template, dict(InitCondFile=inp.with_suffix(''), OutputDir=str(folder / 'output') + '/'))
            (folder / 'param.txt').write_text(param)
            c.update(ic=str(inp), ic_sha256=sha(inp), param_sha256=sha(folder / 'param.txt'))
            cases.append(c)
    setup = dict(old['setup'], boost=[0., 0.], time_mass='N lumped')
    write(root / 'campaign.json', dict(methods=methods, cases=cases, setup=setup, scope=__doc__,
        limits='Two new zero-boost N controls. Existing boost10 controls reused; no rebuild, solver edit or relaxed threshold.'))
    write(root / 'reuse_provenance.json', dict(base_archive=str(base),
        base_source_tar_sha256=old_prov['source_tar_sha256'], binaries=binaries, inputs=inputs,
        runner_sha256=sha(__file__), environment={k:ENV[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')}))
    print('Prepared six runs with two unchanged, hash-verified N binaries.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'uniform', 'pilot', 'science'))
    parser.add_argument('root', type=Path)
    parser.add_argument('--base', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action == 'prepare':
        prepare(root, args.base.resolve())
    else:
        if args.action != 'uniform':
            assert gate(root, 'uniform'), 'Uniform gate failed; preserve for inspection.'
        if args.action == 'science':
            assert gate(root, 'pilot'), 'Pilot failed; preserve for inspection.'
        selected = [c['name'] for c in json.loads((root / 'campaign.json').read_text())['cases']
                    if c['horizon'] == args.action]
        run(root, 'uniform' if args.action == 'uniform' else 'science', selected, 2)
        assert gate(root, args.action)
