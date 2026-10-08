#!/usr/bin/env python3
"""Freeze/build/run the experimental moving LDA/HLLC blend on the archived Sedov ICs.

Moving methods (RD_LDA_RUSANOV_BLEND + RD_BLEND_LOW_HLLC):
  LDAHLLC_bounds  limited LDA/F1 correction, local rho and K=p/rho^gamma bounds;
  LDAHLLC_pos     limited LDA/F1 correction, positivity only;
  LDAHLLC_low     ell=0 control: must reproduce the edge-HLLC low-order RD.
Regression: LR_blend_static, the archived static LDA/Rusanov blend Config,
replayed on its archived 16^2 smooth contact and compared bitwise.
Groups: uniform (t=.001), nearest21 (t=.05), nearest1 (t=.05; bounds/pos), contact16.
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
from run_hllc import freeze

RUSANOV = REPO.parent / 'local_runs/sedov_positivity_20260929_v2'
SWEEP = REPO.parent / 'local_runs/sedov_injection_sweep_20260929_v1'
BLEND = REPO.parent / 'local_runs/sedov_lda_rusanov_20260929_v1'
CONFIGS = {'LDAHLLC_bounds': HERE / 'Config_LDA_HLLC_bounds_moving.sh',
           'LDAHLLC_pos': HERE / 'Config_LDA_HLLC_pos_moving.sh',
           'LDAHLLC_low': HERE / 'Config_LDA_HLLC_low_moving.sh',
           'LR_blend_static': BLEND / 'configs/LR_blend.sh'}


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    freeze(root)
    for folder in ('configs', 'artifacts', 'runs', 'inputs'):
        (root/folder).mkdir()
    old = json.loads((RUSANOV/'campaign.json').read_text())
    sweep = json.loads((SWEEP/'campaign.json').read_text())
    blend = json.loads((BLEND/'campaign.json').read_text())
    known = {c['name']: c for c in old['cases']}
    contact = next(c for c in blend['cases'] if c['name'] == 'contact16_LR_blend')
    for name in ('uniform.hdf5', 'sedov_nearest21.hdf5', 'median_dual_area.npy'):
        shutil.copy2(RUSANOV/'inputs'/name, root/'inputs'/name)
    shutil.copy2(SWEEP/'inputs/sedov_nearest1.hdf5', root/'inputs/sedov_nearest1.hdf5')
    shutil.copy2(contact['ic'], root/'inputs/contact16.hdf5')
    assert sha(root/'inputs/uniform.hdf5') == known['uniform_Rusanov_moving']['ic_sha256']
    assert sha(root/'inputs/sedov_nearest21.hdf5') == known['nearest21_Rusanov_moving']['ic_sha256']
    assert sha(root/'inputs/sedov_nearest1.hdf5') == next(
        c['ic_sha256'] for c in sweep['cases'] if c['name'] == 'nearest1_Rusanov_moving')
    assert sha(root/'inputs/contact16.hdf5') == contact['ic_sha256']
    for method, config in CONFIGS.items():
        shutil.copy2(config, root/'configs'/f'{method}.sh')
    cases = []
    moving = [m for m in CONFIGS if m.startswith('LDAHLLC')]
    plan = ([('uniform', m) for m in CONFIGS] + [('nearest21', m) for m in moving] +
            [('nearest1', 'LDAHLLC_bounds'), ('nearest1', 'LDAHLLC_pos'), ('contact16', 'LR_blend_static')])
    for group, method in plan:
        name = f'{group}_{method}'; folder = root/'runs'/name; folder.mkdir()
        if group == 'contact16':
            template = BLEND/'runs/contact16_LR_blend/param.txt'
            assert sha(template) == contact['param_sha256']
            ic = root/'inputs/contact16.hdf5'
            param = rewrite(template.read_text(), dict(InitCondFile=ic.with_suffix(''), OutputDir=str(folder/'output')+'/'))
            end, mesh = .1, 'static'
        else:
            mesh = 'static' if method.endswith('static') else 'moving'
            template = RUSANOV/'runs'/f'nearest21_Rusanov_{mesh}'/'param.txt'
            end = .001 if group == 'uniform' else .05
            ic = root/'inputs'/('uniform.hdf5' if group == 'uniform' else f'sedov_{group}.hdf5')
            param = rewrite(template.read_text(), dict(InitCondFile=ic.with_suffix(''), OutputDir=str(folder/'output')+'/',
                TimeMax=end, TimeBetSnapshot=end/4, TimeBetStatistics=end/4, MaxSizeTimestep=min(.01, end/4)))
        (folder/'param.txt').write_text(param)
        cases.append(dict(name=name, group=group, method=method, mesh=mesh, end=end, frame='lab',
            ic=str(ic), ic_sha256=sha(ic), param_sha256=sha(folder/'param.txt'),
            param_template=str(template), param_template_sha256=sha(template)))
    campaign = dict(test='Sedov_2d_lda_hllc_blend', methods=list(CONFIGS), cases=cases, source_archive=str(root),
        source_tar_sha256=sha(root/'source.tar'), description=__doc__,
        limits='Experimental: one rank, equal steps, periodic, lab frame, moving ALE. Local bounds are not relaxed '
               'for smooth extrema. Connectivity/endpoint conservation unchanged.')
    write(root/'campaign.json', campaign)
    for script in ('run.py', 'run_hllc.py', 'run_lda_hllc.py'):
        shutil.copy2(HERE/script, root/script)
    shutil.copy2(REPO/'tests/rd/run_n_gauss3_split.py', root/'run_n_gauss3_split.py')
    print(f'Prepared {len(CONFIGS)} builds and {len(cases)} runs.', flush=True)


def resume(root, name, cpu_limit):
    """Continue a run that stopped at 0.85*TimeLimitCPU from its restart files.

    Only TimeLimitCPU changes; the same frozen binary and OutputDir are used and
    the segment is logged separately. Restart mode is AREPO flag 1."""
    import time
    campaign = json.loads((root/'campaign.json').read_text())
    case = next(c for c in campaign['cases'] if c['name'] == name)
    folder = root/'runs'/name; binary = root/'artifacts'/case['method']/'Arepo'
    meta = json.loads((root/'artifacts'/case['method']/'provenance.json').read_text())
    assert sha(binary) == meta['binary_sha256'] and sha(folder/'param.txt') == case['param_sha256']
    assert json.loads((folder/'run_status.json').read_text())['returncode'] == 0
    assert (folder/'output/restartfiles').is_dir() and not (folder/'run_resume.log').exists()
    param = rewrite((folder/'param.txt').read_text(), dict(TimeLimitCPU=cpu_limit))
    (folder/'param_resume.txt').write_text(param)
    start = time.monotonic(); cmd = [str(binary), 'param_resume.txt', '1']
    with (folder/'run_resume.log').open('w') as stream:
        code = subprocess.run(cmd, cwd=folder, env=ENV, stdout=stream, stderr=subprocess.STDOUT).returncode
    status = dict(name=name, returncode=code, seconds=time.monotonic()-start, command=cmd,
                  binary_sha256=meta['binary_sha256'], param_resume_sha256=sha(folder/'param_resume.txt'),
                  reason=f'first segment stopped at 0.85*TimeLimitCPU; resumed with TimeLimitCPU {cpu_limit}')
    write(folder/'run_resume_status.json', status); print(json.dumps(status), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'build', 'run', 'resume'))
    parser.add_argument('--case')
    parser.add_argument('--cpu-limit', type=float, default=14400)
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
            assert '#define RD_LDA_RUSANOV_BLEND' in header
            assert ('#define RD_BLEND_LOW_HLLC' in header) == method.startswith('LDAHLLC')
            assert ('#define RD_BLEND_LOCAL_BOUNDS' in header) == method.endswith('bounds')
            assert ('#define VORONOI_STATIC_MESH' in header) == method.endswith('static')
    elif args.action == 'resume':
        resume(root, args.case, args.cpu_limit)
    else:
        execute(root, args.group, args.select)
