#!/usr/bin/env python3
"""Reuse frozen N/LDA lab binaries for a matched glass Gresho boost/end-time pair."""
import argparse
import json
from pathlib import Path
import shutil

import h5py
import numpy as np

from run_n_gauss3_split import ENV, sha, write, rewrite, run
from run_gresho_glass_boost_lab import gate


def prepare(root, base, boost, end, selected_methods=None):
    assert np.isfinite(boost) and np.isfinite(end) and end > 0
    root.mkdir(parents=True, exist_ok=False)
    for name in ('artifacts', 'configs', 'inputs', 'runs'):
        (root / name).mkdir()
    old = json.loads((base / 'campaign.json').read_text())
    source_prov = json.loads((base / 'source_provenance.json').read_text())
    assert sha(base / 'source.tar') == source_prov['source_tar_sha256']
    (root / 'source').symlink_to(base / 'source', target_is_directory=True)
    (root / 'source.tar').symlink_to(base / 'source.tar')
    shutil.copy2(base / 'source_provenance.json', root / 'source_provenance.json')
    for name in ('run_n_gauss3_split.py', 'run_gresho_glass_boost_lab.py', Path(__file__).name):
        shutil.copy2(Path(__file__).parent / name, root / name)
    inputs = []
    original_boost = old['setup']['boost'][0]
    for problem in ('gresho', 'uniform'):
        source = Path(next(c['ic'] for c in old['cases'] if c['problem'] == problem))
        target = root / 'inputs' / f'{problem}_b{boost:g}.hdf5'
        shutil.copy2(source, target)
        with h5py.File(target, 'r+') as f:
            velocity = f['PartType0/Velocities'][:]
            velocity[:, 0] += boost - original_boost
            f['PartType0/Velocities'][:] = velocity
        with h5py.File(source) as a, h5py.File(target) as b:
            for key in a['PartType0']:
                if key == 'Velocities':
                    delta = b['PartType0'][key][:] - a['PartType0'][key][:]
                    assert np.max(abs(delta - [boost-original_boost, 0., 0.])) < 1e-14
                else:
                    assert np.array_equal(a['PartType0'][key][:], b['PartType0'][key][:]), key
        inputs.append(dict(problem=problem, source=str(source), source_sha256=sha(source),
                           target=str(target), target_sha256=sha(target)))
    methods = old['methods'] if selected_methods is None else selected_methods
    assert methods and len(set(methods)) == len(methods)
    assert all(method in old['methods'] for method in methods)
    cases, binaries = [], []
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
        if old_case['method'] not in methods:
            continue
        c = dict(old_case, boost=boost)
        horizon = c['horizon']
        c['end'] = end if horizon == 'science' else end/64
        inp = root / 'inputs' / f'{c["problem"]}_b{boost:g}.hdf5'
        folder = root / 'runs' / c['name']
        folder.mkdir()
        template = (base / 'runs' / c['name'] / 'param.txt').read_text()
        param = rewrite(template, dict(InitCondFile=inp.with_suffix(''), OutputDir=str(folder / 'output')+'/',
            TimeMax=c['end'], TimeBetSnapshot=end/4 if horizon=='science' else c['end']))
        (folder / 'param.txt').write_text(param)
        c.update(ic=str(inp), ic_sha256=sha(inp), param_sha256=sha(folder / 'param.txt'))
        cases.append(c)
    setup = dict(old['setup'], boost=[boost, 0.], end=end,
                 science_output_times=[end*i/4 for i in range(5)])
    write(root / 'campaign.json', dict(methods=methods, cases=cases, setup=setup, scope=__doc__,
        limits='Selected frozen lab binaries. Actual dyadic steps measured from logs, not inferred from timestep cap.'))
    write(root / 'reuse_provenance.json', dict(base_archive=str(base),
        base_source_tar_sha256=source_prov['source_tar_sha256'], binaries=binaries, inputs=inputs,
        runner_sha256=sha(__file__), environment={k:ENV[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')}))
    print(f'Prepared {len(cases)} cases, boost={boost:g}, end={end:g}, cap={setup["cap"]:.12g}.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'uniform', 'pilot', 'science'))
    parser.add_argument('root', type=Path)
    parser.add_argument('--base', type=Path)
    parser.add_argument('--boost', type=float)
    parser.add_argument('--end', type=float)
    parser.add_argument('--methods', nargs='+')
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action == 'prepare':
        prepare(root, args.base.resolve(), args.boost, args.end, args.methods)
    else:
        if args.action != 'uniform':
            assert gate(root, 'uniform'), 'Uniform gate failed; preserve for inspection.'
        if args.action == 'science':
            assert gate(root, 'pilot'), 'Pilot failed; preserve for inspection.'
        selected = [c['name'] for c in json.loads((root / 'campaign.json').read_text())['cases']
                    if c['horizon'] == args.action]
        run(root, 'uniform' if args.action == 'uniform' else 'science', selected, 4)
        assert gate(root, args.action)
