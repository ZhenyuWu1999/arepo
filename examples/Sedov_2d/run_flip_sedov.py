#!/usr/bin/env python3
"""Sedov gate for the flip-element transfer: positivity and round-off conservation.

Moving equal-step lab-frame RD, gamma 5/3, one rank, Campoli mass, with and
without RD_ALE_FLIP_TRANSFER:
  HLLC_*            edge-HLLC FV-RD (Config_HLLC_moving.sh)
  LDAHLLC_pos_*     LDA/HLLC blend, positivity limiting (Config_LDA_HLLC_pos_moving.sh)
  LDAHLLC_bounds_flip  LDA/HLLC blend with local rho/K bounds (Config_LDA_HLLC_bounds_moving.sh)
The thesis runs (Arpaia, no topology treatment) are the references:
sedov_hllc_20260930_v1 and sedov_lda_hllc_20260930_v1.  Same ICs (verified
hashes) and the same parameter rewrite rule; only TimeLimitCPU is raised so
that a loaded host cannot stop a run early.
Groups: uniform (t=.001, must stay uniform), nearest21 and nearest1 (t=.05).
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tests/rd'))
sys.path.insert(0, str(HERE))
from run_n_gauss3_split import ENV, sha, write, rewrite, build, state   # noqa: E402
from run_hllc import freeze                                              # noqa: E402
from flip_campaign_checks import check_configs                           # noqa: E402

RUNS = REPO.parent / 'local_runs'
HLLC_REF = RUNS / 'sedov_hllc_20260930_v1'
BLEND_REF = RUNS / 'sedov_lda_hllc_20260930_v1'
BASE = {'HLLC': HERE / 'Config_HLLC_moving.sh', 'LDAHLLC_pos': HERE / 'Config_LDA_HLLC_pos_moving.sh',
        'LDAHLLC_bounds': HERE / 'Config_LDA_HLLC_bounds_moving.sh'}
METHODS = {'HLLC_campoli': ('HLLC', ['RD_ALE_CAMPOLI_MASS']),
           'HLLC_flip': ('HLLC', ['RD_ALE_CAMPOLI_MASS', 'RD_ALE_FLIP_TRANSFER', 'RD_FLIP_HIGH_MODE=0']),
           'LDAHLLC_pos_campoli': ('LDAHLLC_pos', ['RD_ALE_CAMPOLI_MASS']),
           'LDAHLLC_pos_flip': ('LDAHLLC_pos', ['RD_ALE_CAMPOLI_MASS', 'RD_ALE_FLIP_TRANSFER', 'RD_FLIP_HIGH_MODE=0']),
           'LDAHLLC_bounds_flip': ('LDAHLLC_bounds', ['RD_ALE_CAMPOLI_MASS', 'RD_ALE_FLIP_TRANSFER', 'RD_FLIP_HIGH_MODE=0'])}
REFERENCE = {'HLLC': (HLLC_REF, 'HLLC_moving'), 'LDAHLLC_pos': (BLEND_REF, 'LDAHLLC_pos'),
             'LDAHLLC_bounds': (BLEND_REF, 'LDAHLLC_bounds')}


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    freeze(root)
    for folder in ('configs', 'artifacts', 'runs', 'inputs'):
        (root / folder).mkdir()
    ref = {c['name']: c for c in json.loads((HLLC_REF / 'campaign.json').read_text())['cases']}
    for name in ('uniform.hdf5', 'sedov_nearest21.hdf5', 'sedov_nearest1.hdf5', 'median_dual_area.npy'):
        shutil.copy2(HLLC_REF / 'inputs' / name, root / 'inputs' / name)
    for group in ('uniform', 'nearest21', 'nearest1'):
        ic = root / 'inputs' / ('uniform.hdf5' if group == 'uniform' else f'sedov_{group}.hdf5')
        assert sha(ic) == ref[f'{group}_HLLC_moving']['ic_sha256'], group
    template_path = HLLC_REF / 'runs/nearest21_HLLC_moving/param.txt'
    template = template_path.read_text()
    texts = {method: '# Sedov flip-transfer gate; see campaign.json.\n' + BASE[base].read_text().rstrip('\n') + '\n'
                     + ''.join(f'{flag}\n' for flag in extra) for method, (base, extra) in METHODS.items()}
    check_configs(texts)
    for method, text in texts.items():
        (root / 'configs' / f'{method}.sh').write_text(text)
    cases = []
    for group in ('uniform', 'nearest21', 'nearest1'):
        end = .001 if group == 'uniform' else .05
        ic = root / 'inputs' / ('uniform.hdf5' if group == 'uniform' else f'sedov_{group}.hdf5')
        for method, (base, extra) in METHODS.items():
            name = f'{group}_{method}'; folder = root / 'runs' / name; folder.mkdir()
            param = rewrite(template, dict(InitCondFile=ic.with_suffix(''), OutputDir=str(folder / 'output') + '/',
                                           TimeMax=end, TimeBetSnapshot=end / 4, TimeBetStatistics=end / 4,
                                           MaxSizeTimestep=min(.01, end / 4), TimeLimitCPU=400000))
            (folder / 'param.txt').write_text(param)
            refdir, refmethod = REFERENCE[base]
            cases.append(dict(name=name, group=group, method=method, base=base, flags=extra, end=end,
                              reference=str(refdir / 'runs' / f'{group}_{refmethod}'), ic=str(ic), ic_sha256=sha(ic),
                              param_sha256=sha(folder / 'param.txt'), param_template=str(template_path),
                              param_template_sha256=sha(template_path), ranks=1))
    write(root / 'campaign.json', dict(test='Sedov_2d_flip_transfer_gate', methods=list(METHODS), cases=cases,
                                       description=__doc__))
    shutil.copy2(__file__, root / Path(__file__).name)
    print('Prepared', len(cases), 'cases.', flush=True)


def run(root, group, workers, selected):
    campaign = json.loads((root / 'campaign.json').read_text())
    cases = [c for c in campaign['cases'] if c['group'] == group and (not selected or c['method'] in selected)]
    dual = np.load(root / 'inputs/median_dual_area.npy')
    if group != 'uniform':
        for method in {c['method'] for c in cases}:
            gate = root / 'runs' / f'uniform_{method}'
            assert json.loads((gate / 'run_status.json').read_text())['returncode'] == 0, method
            snaps = sorted((gate / 'output').glob('snap_*.hdf5'))
            a, b = state(snaps[0]), state(snaps[-1])
            assert max(float(abs(b[k] - a[k]).max()) for k in ('rho', 'p', 'v')) < 1e-12, method
            assert float(abs(a['w'] - dual).max()) < 1e-12, method

    def one(c):
        folder = root / 'runs' / c['name']; artifact = root / 'artifacts' / c['method']
        assert not (folder / 'run.log').exists(), c['name']
        meta = json.loads((artifact / 'provenance.json').read_text())
        assert sha(artifact / 'Arepo') == meta['binary_sha256']
        assert sha(c['ic']) == c['ic_sha256'] and sha(folder / 'param.txt') == c['param_sha256']
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
    p.add_argument('--group', choices=('uniform', 'nearest21', 'nearest1'), default='uniform')
    p.add_argument('--workers', type=int, default=3)
    p.add_argument('--select', nargs='+')
    a = p.parse_args(); root = a.root.resolve()
    if a.action == 'prepare':
        prepare(root)
    elif a.action == 'build':
        build(root, a.select)
    else:
        run(root, a.group, a.workers, a.select)
