#!/usr/bin/env python3
"""Frozen gates for lazy flipping (RD_ALE_LAZY_FLIP) and the receiver-only high mode.

Interval hierarchy, equal bins (= equal-step Campoli with transfer convention
B), N, one rank, gamma 1.4 (configs from run_interval_hierarchy_gates.py):
  N_plain        every Delaunay change adopted, uniform-shift high endpoint
  N_plain_h1     ... with RD_FLIP_HIGH_MODE=1 (receivers only)
  N_lazy         RD_ALE_LAZY_FLIP (15 deg / 20 deg defaults)
  N_lazy_h1      lazy + RD_FLIP_HIGH_MODE=1
on uniform_random (t=1/4), yee48/yee96 (t=1) and kh48/kh96 (t=10; kh96 is the
2x2-tiled glass of kh_flip_resolution_20261009_v1).
HLLC-RD, natural bins, gamma 5/3:
  HLLC_natural_lazy   interval hierarchy + RD_ALE_LAZY_FLIP on sedov21, sedov1
(the non-lazy natural-bin runs are in interval_hierarchy_gates_20261009_v2).
Groups: uniform, yee, kh, sedov.
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
import run_interval_hierarchy_gates as G                                 # noqa: E402

KH96 = G.RUNS / 'kh_flip_resolution_20261009_v1/inputs/kh_glass96.hdf5'
METHODS = {'N_plain': ('N', []), 'N_plain_h1': ('N', ['RD_FLIP_HIGH_MODE=1']),
           'N_lazy': ('N', ['RD_ALE_LAZY_FLIP']), 'N_lazy_h1': ('N', ['RD_ALE_LAZY_FLIP', 'RD_FLIP_HIGH_MODE=1']),
           'HLLC_natural_lazy': ('HLLC', ['RD_ALE_LAZY_FLIP'])}


def config(scheme, extra):
    text = G.config(scheme, 'ih_natural' if scheme == 'HLLC' else 'ih_equal')
    return text.rstrip('\n') + '\n' + ''.join(f'{f}\n' for f in extra)


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    freeze(root)
    for folder in ('configs', 'artifacts', 'runs', 'inputs'):
        (root / folder).mkdir()
    gates = {Path(c['ic']).name: c['ic_sha256'] for c in json.loads((G.GATES / 'campaign.json').read_text())['cases']}
    gates.update({Path(c['ic']).name: c['ic_sha256'] for c in json.loads((G.SEDOV / 'campaign.json').read_text())['cases']})
    gates.update({Path(c['ic']).name: c['ic_sha256'] for c in
                  json.loads((KH96.parents[1] / 'campaign.json').read_text())['cases']})
    inputs = dict(G.INPUTS, kh96=KH96)
    for path in inputs.values():
        assert sha(path) == gates[path.name], path
        shutil.copy2(path, root / 'inputs' / path.name)
    for method, (scheme, extra) in METHODS.items():
        (root / 'configs' / f'{method}.sh').write_text(config(scheme, extra))
    probs = G.problems()
    probs['kh96'] = ('kh',) + probs['kh48'][1:]
    cases = []
    for problem, (group, template, updates, end) in probs.items():
        ic = root / 'inputs' / inputs[problem].name
        for method, (scheme, extra) in METHODS.items():
            if (scheme == 'HLLC') != (group == 'sedov'):
                continue
            name = f'{problem}_{method}'; folder = root / 'runs' / name; folder.mkdir()
            param = rewrite(template, dict(InitCondFile=ic.with_suffix(''), OutputDir=str(folder / 'output') + '/', **updates))
            (folder / 'param.txt').write_text(param)
            cases.append(dict(name=name, method=method, scheme=scheme, variant=method.split('_', 1)[1], problem=problem,
                              group=group, end=end, ic=str(ic), ic_sha256=sha(ic),
                              param_sha256=sha(folder / 'param.txt'), ranks=1))
    write(root / 'campaign.json', dict(test='lazy_flip_gates', methods=list(METHODS), cases=cases, description=__doc__))
    shutil.copy2(__file__, root / Path(__file__).name)
    print('Prepared', len(cases), 'cases and', len(METHODS), 'builds.', flush=True)


def run(root, group, workers):
    cases = [c for c in json.loads((root / 'campaign.json').read_text())['cases'] if c['group'] == group]
    cases.sort(key=lambda c: -('96' in c['problem']))  # long runs first

    def one(c):
        folder = root / 'runs' / c['name']; artifact = root / 'artifacts' / c['method']
        assert not (folder / 'run.log').exists()
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
        list(pool.map(one, cases))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('action', choices=('prepare', 'build', 'run'))
    p.add_argument('root', type=Path)
    p.add_argument('--group', choices=('uniform', 'yee', 'kh', 'sedov'), default='uniform')
    p.add_argument('--workers', type=int, default=3)
    a = p.parse_args(); root = a.root.resolve()
    if a.action == 'prepare':
        prepare(root)
    elif a.action == 'build':
        build(root, None)
    else:
        run(root, a.group, a.workers)
