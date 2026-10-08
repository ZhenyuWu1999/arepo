#!/usr/bin/env python3
"""Freeze/build/run the optional Rusanov RD experiment on the original Sedov ICs."""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tests/rd'))
from run_n_gauss3_split import ENV, sha, write, rewrite, build, state
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run import execute

BASE = REPO.parent / 'local_runs/sedov_2d_20260929_v1'


def prepare(root, topology_repair=False):
    root.mkdir(parents=True, exist_ok=False)
    source = root / 'source'; source.mkdir()
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    subprocess.run(['git', 'archive', '-o', str(root/'base.tar'), commit], cwd=REPO, check=True)
    subprocess.run(['tar', '-xf', str(root/'base.tar'), '-C', str(source)], check=True)
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=REPO).decode().split('\0')
    names += ['src/hydro/rd_rusanov.h', 'tests/rd/test_rusanov_positivity.py',
              'examples/Sedov_2d/run_positivity.py', 'examples/Sedov_2d/analyze_positivity.py',
              'examples/Sedov_2d/analyze_topology_repair.py',
              'examples/Sedov_2d/run.py', 'examples/Sedov_2d/analyze.py',
              'examples/Sedov_2d/Config_Rusanov_static.sh', 'examples/Sedov_2d/Config_Rusanov_moving.sh']
    hashes = {}
    for name in names:
        if name and (REPO/name).is_file():
            (source/name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO/name, source/name); hashes[name] = sha(REPO/name)
    shutil.copy2(REPO/'Makefile.systype', source/'Makefile.systype')
    (root/'working_tree.patch').write_bytes(subprocess.check_output(['git', 'diff', '--binary', 'HEAD'], cwd=REPO))
    subprocess.run(['tar', '-cf', str(root/'source.tar'), '-C', str(source), '.'], check=True)
    write(root/'source_provenance.json', dict(base_commit=commit, source_tar_sha256=sha(root/'source.tar'),
        tracked_and_new_hashes=hashes, environment={k: ENV[k] for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS')}))
    for folder in ('configs', 'artifacts', 'runs'):
        (root/folder).mkdir()
    shutil.copytree(BASE/'inputs', root/'inputs')
    shutil.copytree(BASE/'reference', root/'reference')
    campaign = json.loads((BASE/'campaign.json').read_text())
    methods = ['Rusanov_moving_repair'] if topology_repair else ['Rusanov_static', 'Rusanov_moving', 'baseline_static']
    campaign.update(methods=methods, cases=[],
        description=__doc__, source_tar_sha256=sha(root/'source.tar'), source_archive=str(root),
        limits='Experimental spatial first-order RD, existing lumped RK2. Stage CFL/positivity verified before primitive recovery. ALE endpoint conservation remains separate.')
    if topology_repair:
        campaign['topology_repair'] = 'Existing unlimited support-patch map, with predictor primitives refreshed to the repaired state. Aborts if repair loses admissibility; no remap limiter.'
    for method in campaign['methods']:
        mesh = 'moving' if 'moving' in method else 'static'
        base_method = f'N_{mesh}_lab'
        cfg = (BASE/'artifacts'/base_method/'Config.sh').read_text()
        cfg = re.sub(r'^# Gresho.*$', '# Sedov positivity experiment; method: '+method, cfg, flags=re.M)
        if method.startswith('Rusanov'):
            cfg = re.sub(r'^RD_ALE_(SPLIT_MESH_VELOCITY|CFL_DIAGNOSTIC)\s*$', '', cfg, flags=re.M)
            cfg += '\nRD_RUSANOV_LOW_ORDER\n'
        if topology_repair:
            cfg += '\nRD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC\n'
        (root/'configs'/f'{method}.sh').write_text(cfg)
        for group in ('uniform', 'nearest21', 'disk005'):
            if method.startswith('baseline') and group == 'disk005':
                continue
            name = f'{group}_{method}'; folder = root/'runs'/name; folder.mkdir()
            ic_name = {'uniform':'uniform.hdf5', 'nearest21':'sedov_nearest21.hdf5', 'disk005':'sedov_disk005.hdf5'}[group]
            ic = root/'inputs'/ic_name
            end = .001 if group == 'uniform' or method.startswith('baseline') else .05
            template = BASE/'runs'/f'nearest21_{base_method}'/'param.txt'
            param = rewrite(template.read_text(), dict(InitCondFile=ic.with_suffix(''), OutputDir=str(folder/'output')+'/',
                TimeMax=end, TimeBetSnapshot=end/4, TimeBetStatistics=end/4, MaxSizeTimestep=min(.01, end/4)))
            (folder/'param.txt').write_text(param)
            campaign['cases'].append(dict(name=name, group=group, method=method, scheme=method.split('_')[0], mesh=mesh,
                frame='lab', end=end, cfl=.1, temporal='lumped RK2', ic=str(ic), ic_sha256=sha(ic),
                param_sha256=sha(folder/'param.txt')))
    write(root/'campaign.json', campaign)
    for name in ('run.py', 'run_positivity.py', 'analyze.py'):
        shutil.copy2(Path(__file__).parent/name, root/name)
    shutil.copy2(REPO/'tests/rd/run_n_gauss3_split.py', root/'run_n_gauss3_split.py')
    print(f'Prepared {len(campaign["methods"])} builds and {len(campaign["cases"])} runs.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'build', 'run'))
    parser.add_argument('root', type=Path)
    parser.add_argument('--group', default='uniform')
    parser.add_argument('--select', nargs='+')
    parser.add_argument('--topology-repair', action='store_true', help='Prepare only moving Rusanov with the existing unlimited repair and consistent predictor primitives.')
    args = parser.parse_args(); root = args.root.resolve()
    if args.action == 'prepare':
        prepare(root, args.topology_repair)
    elif args.action == 'build':
        # Legacy header check rules do not create nested directories themselves.
        methods = args.select or json.loads((root/'campaign.json').read_text())['methods']
        for method in methods:
            for header in (root/'source/src').rglob('*.h'):
                (root/'build'/method/header.relative_to(root/'source/src').parent).mkdir(parents=True, exist_ok=True)
        build(root, args.select)
    else:
        execute(root, args.group, args.select)
