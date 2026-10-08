#!/usr/bin/env python3
"""Freeze/build/run the optional edge-HLLC low-order RD on the archived Sedov ICs.

Methods:
  HLLC_static, HLLC_moving  RD_RUSANOV_LOW_ORDER + RD_LOW_ORDER_HLLC (kernel swap only);
  Rusanov_moving            flag-absent regression, replayed against the archived
                            moving Rusanov run with byte-identical IC and parameters.
Groups: uniform (t=.001), nearest21 (t=.05), nearest1 (moving HLLC, t=.05).
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tests/rd'))
from run_n_gauss3_split import ENV, sha, write, rewrite, build
sys.path.insert(0, str(HERE))
from run import execute

RUSANOV = REPO.parent / 'local_runs/sedov_positivity_20260929_v2'
SWEEP = REPO.parent / 'local_runs/sedov_injection_sweep_20260929_v1'
CONFIGS = {'HLLC_static': HERE / 'Config_HLLC_static.sh', 'HLLC_moving': HERE / 'Config_HLLC_moving.sh',
           'Rusanov_moving': RUSANOV / 'configs/Rusanov_moving.sh'}


def freeze(root):
    source = root / 'source'; source.mkdir()
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    subprocess.run(['git', 'archive', '-o', str(root/'base.tar'), commit], cwd=REPO, check=True)
    subprocess.run(['tar', '-xf', str(root/'base.tar'), '-C', str(source)], check=True)
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=REPO).decode().split('\0')
    untracked = subprocess.check_output(['git', 'ls-files', '-z', '--others', '--exclude-standard'], cwd=REPO).decode().split('\0')
    hashes = {}
    for name in tracked + untracked:
        if not name: continue
        src, dst = REPO/name, source/name
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst); hashes[name] = sha(src)
        elif dst.is_file():
            dst.unlink()
    shutil.copy2(REPO/'Makefile.systype', source/'Makefile.systype')
    (root/'working_tree.patch').write_bytes(subprocess.check_output(['git', 'diff', '--binary', 'HEAD'], cwd=REPO))
    subprocess.run(['tar', '-cf', str(root/'source.tar'), '-C', str(source), '.'], check=True)
    write(root/'source_provenance.json', dict(base_commit=commit, source_tar_sha256=sha(root/'source.tar'),
        tracked_and_untracked_hashes=hashes, environment={k: ENV[k] for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS')}))


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    freeze(root)
    for folder in ('configs', 'artifacts', 'runs', 'inputs'):
        (root/folder).mkdir()
    old = json.loads((RUSANOV/'campaign.json').read_text())
    sweep = json.loads((SWEEP/'campaign.json').read_text())
    known = {c['name']: c for c in old['cases']}
    for name in ('uniform.hdf5', 'sedov_nearest21.hdf5', 'median_dual_area.npy'):
        shutil.copy2(RUSANOV/'inputs'/name, root/'inputs'/name)
    shutil.copy2(SWEEP/'inputs/sedov_nearest1.hdf5', root/'inputs/sedov_nearest1.hdf5')
    assert sha(root/'inputs/median_dual_area.npy') == sha(SWEEP/'inputs/median_dual_area.npy')
    assert sha(root/'inputs/uniform.hdf5') == known['uniform_Rusanov_moving']['ic_sha256']
    assert sha(root/'inputs/sedov_nearest21.hdf5') == known['nearest21_Rusanov_moving']['ic_sha256']
    assert sha(root/'inputs/sedov_nearest1.hdf5') == next(
        c['ic_sha256'] for c in sweep['cases'] if c['name'] == 'nearest1_Rusanov_moving')
    for method, config in CONFIGS.items():
        shutil.copy2(config, root/'configs'/f'{method}.sh')
    cases = []
    plan = [('uniform', m) for m in CONFIGS] + [('nearest21', m) for m in CONFIGS] + [('nearest1', 'HLLC_moving')]
    for group, method in plan:
        mesh = 'moving' if 'moving' in method else 'static'
        template = RUSANOV/'runs'/f'nearest21_Rusanov_{mesh}'/'param.txt'
        end = .001 if group == 'uniform' else .05
        ic = root/'inputs'/('uniform.hdf5' if group == 'uniform' else f'sedov_{group}.hdf5')
        name = f'{group}_{method}'; folder = root/'runs'/name; folder.mkdir()
        # Identical rewrite rule to the archived Rusanov campaign, so the flag-absent
        # replay has the same timeline and output times.
        param = rewrite(template.read_text(), dict(InitCondFile=ic.with_suffix(''), OutputDir=str(folder/'output')+'/',
            TimeMax=end, TimeBetSnapshot=end/4, TimeBetStatistics=end/4, MaxSizeTimestep=min(.01, end/4)))
        (folder/'param.txt').write_text(param)
        cases.append(dict(name=name, group=group, method=method, mesh=mesh, end=end, cfl=.1, frame='lab',
            temporal='lumped RK2', ic=str(ic), ic_sha256=sha(ic), param_sha256=sha(folder/'param.txt'),
            param_template=str(template), param_template_sha256=sha(template)))
    campaign = dict(test='Sedov_2d_hllc_low_order', methods=list(CONFIGS), cases=cases, source_archive=str(root),
        source_tar_sha256=sha(root/'source.tar'), description=__doc__,
        gamma=old.get('gamma'), pressure0=old.get('pressure0'), nodes=old.get('nodes'),
        seeds=dict(nearest21=old.get('seeds', {}).get('nearest21'), nearest1=sweep['seeds']['nearest1']),
        limits='Spatial first order (FV-RD edge HLLC) with the existing lumped RK2 and stage checks; one rank, '
               'equal steps, periodic. Connectivity/endpoint conservation unchanged from the Rusanov path.')
    write(root/'campaign.json', campaign)
    for script in ('run.py', 'run_hllc.py'):
        shutil.copy2(HERE/script, root/script)
    shutil.copy2(REPO/'tests/rd/run_n_gauss3_split.py', root/'run_n_gauss3_split.py')
    print(f'Prepared {len(CONFIGS)} builds and {len(cases)} runs.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'build', 'run'))
    parser.add_argument('root', type=Path)
    parser.add_argument('--group', default='uniform')
    parser.add_argument('--select', nargs='+')
    args = parser.parse_args(); root = args.root.resolve()
    if args.action == 'prepare':
        prepare(root)
    elif args.action == 'build':
        methods = args.select or json.loads((root/'campaign.json').read_text())['methods']
        for method in methods:
            for header in (root/'source/src').rglob('*.h'):
                (root/'build'/method/header.relative_to(root/'source/src').parent).mkdir(parents=True, exist_ok=True)
        build(root, args.select)
        for method in methods:
            header = (root/'artifacts'/method/'arepoconfig.h').read_text()
            assert '#define RD_RUSANOV_LOW_ORDER' in header
            assert ('#define RD_LOW_ORDER_HLLC' in header) == method.startswith('HLLC')
            assert ('#define VORONOI_STATIC_MESH' in header) == method.endswith('static')
    else:
        execute(root, args.group, args.select)
