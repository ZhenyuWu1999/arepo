#!/usr/bin/env python3
"""Frozen gates for the moving-mesh interval hierarchy (RD_ALE_INTERVAL_HIERARCHY).

One rank, gamma 1.4, Campoli mass, contour residual, element co-moving frame,
CREATE_FULL_MESH (examples/yee_2d/Config_RD_ALE_HIER_N_equal.sh and
Config_RD_ALE_N_CAMPOLI_equalstep_ref.sh), for N, LDA and B (frozen scalar
total theta, as Config_FS_con_cm_B.sh):
  ref_flip            equal-step + RD_ALE_FLIP_TRANSFER (conservative reference)
  ih_equal            interval hierarchy, FORCE_EQUAL_TIMESTEPS (must match ref
                      until the first flip, then differ only by the flip convention)
  ih_twobin           RD_HIERARCHICAL_TEST_PATTERN, x < 0.5 L one level finer
  ih_twobin25         the same with the split at x < 0.25 L
  ih_natural          natural tree-based CFL bins
  ih_twobin_notransfer  negative control (N only): flips keep U, totals drift
HLLC-RD (examples/Sedov_2d/Config_HLLC_moving.sh, gamma 5/3, lab frame):
  HLLC_ref_flip       equal-step + Campoli + RD_ALE_FLIP_TRANSFER
  HLLC_ih_equal       interval hierarchy, equal bins
  HLLC_ih_natural     interval hierarchy, natural CFL bins (the speed-up case)
Problems (archived ICs, copied and hashed):
  uniform_random  2304 uniform random points, uniform state, t=1/4 (exact)
  yee48, yee96    boost-1 Yee vortex, CFL .2, dt caps 1/256 and 1/512, t=1
  kh48            smoothed KH (width .025), CFL .3, cap .02, t=10
  sedov21, sedov1 Sedov 21- and 1-point injection (HLLC only), CFL .1, cap .001, t=.05
Groups: uniform, yee, kh (N/LDA/B) and sedov (HLLC).
"""
import argparse
import json
from pathlib import Path

import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / 'examples/Sedov_2d'))
from run_n_gauss3_split import ENV, sha, write, rewrite, build, state   # noqa: E402
from run_hllc import freeze                                              # noqa: E402

RUNS = REPO.parent / 'local_runs'
GATES = RUNS / 'flip_gates_20261009_v1'
INPUTS = {'uniform_random': GATES / 'inputs/uniform_random48.hdf5', 'yee48': GATES / 'inputs/yee_glass48.hdf5',
          'yee96': GATES / 'inputs/yee_glass96.hdf5', 'kh48': GATES / 'inputs/kh_smooth.hdf5'}
SEDOV = RUNS / 'sedov_flip_gate_20261009_v1'
INPUTS.update({'sedov21': SEDOV / 'inputs/sedov_nearest21.hdf5', 'sedov1': SEDOV / 'inputs/sedov_nearest1.hdf5'})
HIER = REPO / 'examples/yee_2d/Config_RD_ALE_HIER_N_equal.sh'
HLLC = REPO / 'examples/Sedov_2d/Config_HLLC_moving.sh'
REF = REPO / 'examples/yee_2d/Config_RD_ALE_N_CAMPOLI_equalstep_ref.sh'


def config_hllc(variant):
    lines = HLLC.read_text().splitlines() + ['RD_ALE_CAMPOLI_MASS']
    if variant == 'ref_flip':
        lines += ['RD_ALE_FLIP_TRANSFER']
    else:
        for drop in ('RD_ALE_EQUALSTEP', 'RD_RK2_SPLIT_STAGES', 'RD_ALE_CFL_TIMESTEP'):
            assert lines.count(drop) == 1, drop
            lines.remove(drop)
        lines += ['RD_HIERARCHICAL_TIMESTEPS', 'RD_ALE_HIERARCHICAL', 'RD_ALE_INTERVAL_HIERARCHY']
        if variant == 'ih_natural':
            lines.remove('FORCE_EQUAL_TIMESTEPS')
    return '# Interval-hierarchy gate; see campaign.json.\n' + '\n'.join(lines) + '\n'


def config(scheme, variant):
    if scheme == 'HLLC':
        return config_hllc(variant)
    if variant == 'ref_flip':
        lines = REF.read_text().splitlines() + ['RD_ALE_FLIP_TRANSFER']
    else:
        lines = HIER.read_text().splitlines() + ['RD_ALE_INTERVAL_HIERARCHY']
        if variant != 'ih_equal':
            assert lines.count('FORCE_EQUAL_TIMESTEPS') == 1
            lines.remove('FORCE_EQUAL_TIMESTEPS')
        if variant.startswith('ih_twobin'):
            split = '0.25' if variant == 'ih_twobin25' else '0.5'
            lines += ['RD_HIERARCHICAL_TEST_PATTERN', f'RD_HIER_TEST_SPLIT_FRAC={split}']
        if variant.endswith('notransfer'):
            lines += ['RD_ALE_INTERVAL_NO_TRANSFER']
    assert lines.count('N_SCHEME') == 1 and 'GAMMA=1.4' in lines
    if scheme == 'LDA':
        lines[lines.index('N_SCHEME')] = 'LDA_SCHEME'
    if scheme == 'B':
        k = lines.index('N_SCHEME')
        lines[k:k + 1] = ['B_SCHEME', 'RD_B_FROZEN_THETA', 'RD_B_SCALAR_THETA']
    return '# Interval-hierarchy gate; see campaign.json.\n' + '\n'.join(lines) + '\n'


def methods():
    out = {}
    for scheme in ('N', 'LDA', 'B'):
        for variant in ('ref_flip', 'ih_equal', 'ih_twobin', 'ih_twobin25', 'ih_natural'):
            out[f'{scheme}_{variant}'] = (scheme, variant)
    out['N_ih_twobin_notransfer'] = ('N', 'ih_twobin_notransfer')
    for variant in ('ref_flip', 'ih_equal', 'ih_natural'):
        out[f'HLLC_{variant}'] = ('HLLC', variant)
    return out


def problems():
    yee = (RUNS / 'moving_equal_split_stages_20260914_v4/runs/yee_lda_split/param.txt').read_text()
    sedov = (SEDOV / 'runs/nearest21_HLLC_flip/param.txt').read_text()   # TimeLimitCPU 400000, t=.05
    return {
        'uniform_random': ('uniform', (RUNS / 'legacy_split_20260912/runs/uniform_split_frame/param.txt').read_text(),
                           dict(TimeMax=.25, TimeBetSnapshot=.125), .25),
        'yee48': ('yee', yee, dict(TimeMax=1, TimeBetSnapshot=.25, TimeBetStatistics=.25, MaxSizeTimestep=1 / 256), 1.),
        'yee96': ('yee', yee, dict(TimeMax=1, TimeBetSnapshot=.25, TimeBetStatistics=.25, MaxSizeTimestep=1 / 512), 1.),
        'kh48': ('kh', (REPO / 'examples/gresho_2d/param_KH_N_glass48_toporepair_t10.txt').read_text(),
                 dict(TimeMax=10, TimeLimitCPU=400000, MaxMemSize=1500), 10.),
        'sedov21': ('sedov', sedov, dict(MaxSizeTimestep=.001), .05),
        'sedov1': ('sedov', sedov, dict(MaxSizeTimestep=.001), .05)}


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    freeze(root)
    for folder in ('configs', 'artifacts', 'runs', 'inputs'):
        (root / folder).mkdir()
    gates = {Path(c['ic']).name: c['ic_sha256'] for c in json.loads((GATES / 'campaign.json').read_text())['cases']}
    gates.update({Path(c['ic']).name: c['ic_sha256'] for c in json.loads((SEDOV / 'campaign.json').read_text())['cases']})
    for path in INPUTS.values():
        assert sha(path) == gates[path.name], path
        shutil.copy2(path, root / 'inputs' / path.name)
    table = methods()
    for method, (scheme, variant) in table.items():
        (root / 'configs' / f'{method}.sh').write_text(config(scheme, variant))
    cases = []
    for problem, (group, template, updates, end) in problems().items():
        ic = root / 'inputs' / INPUTS[problem].name
        for method, (scheme, variant) in table.items():
            if (scheme == 'HLLC') != (group == 'sedov'):
                continue
            name = f'{problem}_{method}'; folder = root / 'runs' / name; folder.mkdir()
            param = rewrite(template, dict(InitCondFile=ic.with_suffix(''), OutputDir=str(folder / 'output') + '/', **updates))
            (folder / 'param.txt').write_text(param)
            cases.append(dict(name=name, method=method, scheme=scheme, variant=variant, problem=problem, group=group,
                              end=end, ic=str(ic), ic_sha256=sha(ic), param_sha256=sha(folder / 'param.txt'), ranks=1))
    write(root / 'campaign.json', dict(test='interval_hierarchy_gates', methods=list(table), cases=cases,
                                       description=__doc__))
    shutil.copy2(__file__, root / Path(__file__).name)
    print('Prepared', len(cases), 'cases and', len(table), 'builds.', flush=True)


def run(root, group, workers, selected):
    campaign = json.loads((root / 'campaign.json').read_text())
    cases = [c for c in campaign['cases'] if c['group'] == group and (not selected or c['name'] in selected)]
    if group not in ('uniform', 'sedov'):
        for method in {c['method'] for c in cases}:
            folder = root / 'runs' / f'uniform_random_{method}'
            assert json.loads((folder / 'run_status.json').read_text())['returncode'] == 0, method
            snaps = sorted((folder / 'output').glob('snap_*.hdf5'))
            a, b = state(snaps[0]), state(snaps[-1])
            assert max(float(abs(b[k] - a[k]).max()) for k in ('rho', 'v', 'p')) < 1e-12, method

    def one(c):
        folder = root / 'runs' / c['name']; artifact = root / 'artifacts' / c['method']
        assert not (folder / 'run.log').exists(), c['name']
        meta = json.loads((artifact / 'provenance.json').read_text())
        assert sha(artifact / 'Arepo') == meta['binary_sha256']
        assert sha(folder / 'param.txt') == c['param_sha256'] and sha(c['ic']) == c['ic_sha256']
        start = time.monotonic(); cmd = [str(artifact / 'Arepo'), 'param.txt']
        print('START', c['name'], flush=True)
        with (folder / 'run.log').open('w') as stream:
            code = subprocess.run(cmd, cwd=folder, env=ENV, stdout=stream, stderr=subprocess.STDOUT).returncode
        write(folder / 'run_status.json', dict(name=c['name'], returncode=code, seconds=time.monotonic() - start,
                                               binary_sha256=meta['binary_sha256'], command=cmd))
        print('DONE', c['name'], code, flush=True)
        return code

    with ThreadPoolExecutor(workers) as pool:
        codes = list(pool.map(one, cases))
    write(root / f'status_{group}.json', codes)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('action', choices=('prepare', 'build', 'run'))
    p.add_argument('root', type=Path)
    p.add_argument('--group', choices=('uniform', 'yee', 'kh', 'sedov'), default='uniform')
    p.add_argument('--workers', type=int, default=3)
    p.add_argument('--select', nargs='+')
    a = p.parse_args(); root = a.root.resolve()
    if a.action == 'prepare':
        prepare(root)
    elif a.action == 'build':
        build(root, a.select)
    else:
        run(root, a.group, a.workers, a.select)
