#!/usr/bin/env python3
"""Prepare portable, hash-verified Yee boost cases; never build or launch jobs.

Input HDF5 files are transferred separately from the Mac archive. All paths in
parameters refer to the destination, so run this after transfer on COSMA.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[2]
EXAMPLE = REPO / 'examples/yee_2d'
DATA = EXAMPLE / 'boost_comparison'
CONFIGS = {
    'LDA_static_lab': 'Config_RD_RK2_LDA_GAUSS3_EQUAL_SPLIT.sh',
    'LDA_moving_comoving': 'Config_RD_ALE_LDA_GAUSS3_EQUAL_SPLIT.sh',
    'LDA_moving_lab': 'Config_RD_ALE_LDA_GAUSS3_EQUAL_SPLIT_LAB.sh',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rewrite(text, changes):
    for key, value in changes.items():
        text, count = re.subn(r'^' + re.escape(key) + r'\s+.*$',
                             lambda match: f'{key} {value}', text, flags=re.M)
        if count != 1:
            raise ValueError(f'Expected exactly one {key}, found {count}')
    return text


def prepare(root, inputs, include_lab):
    manifest = json.loads((DATA / 'inputs_manifest.json').read_text())
    for name, entry in manifest['files'].items():
        path = inputs / name
        if not path.is_file() or sha(path) != entry['sha256']:
            raise ValueError(f'Missing or changed input: {path}')
    # AREPO parameter parsing uses whitespace-delimited paths.
    if any(c.isspace() for c in str(root) + str(inputs)):
        raise ValueError('Choose paths without whitespace for AREPO parameters')
    root.mkdir(parents=True, exist_ok=False)
    (root / 'configs').mkdir()
    (root / 'runs').mkdir()
    shutil.copy2(DATA / 'inputs_manifest.json', root / 'inputs_manifest.json')
    template = (DATA / 'param.template').read_text()
    methods = list(CONFIGS) if include_lab else list(CONFIGS)[:2]
    cases = []
    for method in methods:
        config = root / 'configs' / f'{method}.sh'
        shutil.copy2(EXAMPLE / CONFIGS[method], config)
        mesh = 'static' if method == 'LDA_static_lab' else 'moving'
        frame = 'comoving' if method.endswith('comoving') else 'lab'
        for boost in (1, 10):
            specs = [('uniform', 48, 0.03125)]
            if boost == 10:
                specs.append(('pilot', 192, 0.0078125))
            specs.extend(('yee', n, 1.0) for n in (48, 96, 192))
            for phase, n, end in specs:
                name = f'{phase}_{method}_b{boost}_n{n}'
                folder = root / 'runs' / name
                folder.mkdir()
                filename = f'uniform_b{boost}.hdf5' if phase == 'uniform' else f'yee_n{n}_b{boost}.hdf5'
                ic = inputs / filename
                denominator = 1024 * n // 48
                param = folder / 'param.txt'
                param.write_text(rewrite(template, {
                    'InitCondFile': ic.with_suffix(''),
                    'OutputDir': str(folder / 'output') + '/',
                    'TimeMax': end,
                    'TimeBetSnapshot': 0.5 if phase == 'yee' else end,
                    'TimeBetStatistics': 0.5 if phase == 'yee' else end,
                    'MaxSizeTimestep': 1 / denominator,
                }))
                cases.append(dict(name=name, method=method, mesh=mesh, frame=frame,
                                  phase=phase, n=n, boost=boost, end=end, ranks=1,
                                  dt_denominator=denominator, expected_steps=round(end * denominator),
                                  config=str(config), config_sha256=sha(config),
                                  param=str(param), param_sha256=sha(param),
                                  ic=str(ic), ic_sha256=sha(ic)))
    campaign = dict(cases=cases, methods=methods,
                    prepared_from_commit=subprocess.check_output(
                        ['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
                    prepared_worktree_status=subprocess.check_output(
                        ['git', 'status', '--short'], cwd=REPO, text=True),
                    instructions='Build only on compute nodes using managed artifacts. '
                    'Run/check uniform gates before pilots/science; all runs one MPI rank. '
                    'Use separate Slurm jobs for independent cases. No jobs submitted by preparation.')
    (root / 'campaign.json').write_text(json.dumps(campaign, indent=2) + '\n')
    columns = ('name', 'method', 'phase', 'n', 'boost', 'frame', 'param')
    (root / 'cases.tsv').write_text('\t'.join(columns) + '\n' + ''.join(
        '\t'.join(str(case[k]) for k in columns) + '\n' for case in cases))
    print(f'Prepared {len(cases)} cases in {root}; no jobs submitted.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--inputs', required=True, type=Path)
    parser.add_argument('--include-lab', action='store_true',
                        help='Add separate moving lab controls; do not mix frames in fits')
    args = parser.parse_args()
    prepare(args.root.resolve(), args.inputs.resolve(), args.include_lab)
