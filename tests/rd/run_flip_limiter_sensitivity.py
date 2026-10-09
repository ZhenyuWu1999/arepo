#!/usr/bin/env python3
"""Flip-transfer limiter sensitivity (decision D2 of the implementation plan).

Defaults (floor kappa = 0.5, no density hull, no entropy bound, high mode 0)
are the N_flip / HLLC_flip runs of flip_gates_20261009_v1 and
sedov_flip_gate_20261009_v1.  Variants, one rank, equal-step, Campoli + flip:
  KH glass48 t=10, N (Config_FS_con_cm_N.sh, gamma 1.4):
    kh_entropy        RD_FLIP_ENTROPY_BOUND=1
    kh_dmp0           RD_FLIP_DMP_RELAX=0.0 (density within the cavity hull)
    kh_entropy_dmp0   both
  Sedov 21-point t=0.05, HLLC-RD (Config_HLLC_moving.sh, gamma 5/3):
    sedov_kappa1e-12  RD_FLIP_FLOOR_FRACTION=1e-12 (positivity only)
    sedov_kappa0.1    RD_FLIP_FLOOR_FRACTION=0.1
    sedov_entropy     RD_FLIP_ENTROPY_BOUND=1
    sedov_dmp0        RD_FLIP_DMP_RELAX=0.0
  Receiver-only high endpoint on Sedov (HLLC-RD, 21- and 1-point):
    sedov_h1, sedov1_h1   RD_FLIP_HIGH_MODE=1
Use --only to freeze a subset of variants in a new archive.
Same ICs (hash-checked) and parameter files as the default gates.
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
from run_n_gauss3_split import ENV, sha, write, build   # noqa: E402
from run_hllc import freeze                              # noqa: E402

RUNS = REPO.parent / 'local_runs'
KH = RUNS / 'flip_gates_20261009_v1'
SEDOV = RUNS / 'sedov_flip_gate_20261009_v1'
VARIANTS = {
    'kh_entropy': ('kh', ['RD_FLIP_ENTROPY_BOUND=1']),
    'kh_dmp0': ('kh', ['RD_FLIP_DMP_RELAX=0.0']),
    'kh_entropy_dmp0': ('kh', ['RD_FLIP_ENTROPY_BOUND=1', 'RD_FLIP_DMP_RELAX=0.0']),
    'sedov_kappa1e-12': ('sedov', ['RD_FLIP_FLOOR_FRACTION=1e-12']),
    'sedov_kappa0.1': ('sedov', ['RD_FLIP_FLOOR_FRACTION=0.1']),
    'sedov_entropy': ('sedov', ['RD_FLIP_ENTROPY_BOUND=1']),
    'sedov_dmp0': ('sedov', ['RD_FLIP_DMP_RELAX=0.0']),
    'sedov_h1': ('sedov', ['RD_FLIP_HIGH_MODE=1']),
    'sedov1_h1': ('sedov1', ['RD_FLIP_HIGH_MODE=1'])}
DEFAULT = {'kh': (KH, 'N_flip', 'kh_N_flip'), 'sedov': (SEDOV, 'HLLC_flip', 'nearest21_HLLC_flip'),
           'sedov1': (SEDOV, 'HLLC_flip', 'nearest1_HLLC_flip')}


def prepare(root, only=None):
    root.mkdir(parents=True, exist_ok=False)
    freeze(root)
    for folder in ('configs', 'artifacts', 'runs', 'inputs'):
        (root / folder).mkdir()
    cases = []
    variants = {k: v for k, v in VARIANTS.items() if not only or k in only}
    for method, (problem, extra) in variants.items():
        archive, default_method, default_case = DEFAULT[problem]
        base = (archive / 'configs' / f'{default_method}.sh').read_text()
        assert 'RD_ALE_FLIP_TRANSFER' in base and 'RD_ALE_CAMPOLI_MASS' in base
        # The archived default runs used the old default mode 0; keep that explicit unless the variant sets it.
        if not any(f.startswith('RD_FLIP_HIGH_MODE') for f in extra) and 'RD_FLIP_HIGH_MODE' not in base:
            extra = extra + ['RD_FLIP_HIGH_MODE=0']
        (root / 'configs' / f'{method}.sh').write_text(base.rstrip('\n') + '\n' + ''.join(f'{f}\n' for f in extra))
        ref = next(c for c in json.loads((archive / 'campaign.json').read_text())['cases'] if c['name'] == default_case)
        ic = root / 'inputs' / Path(ref['ic']).name
        if not ic.exists():
            shutil.copy2(ref['ic'], ic)
        assert sha(ic) == ref['ic_sha256']
        folder = root / 'runs' / method; folder.mkdir()
        param = (archive / 'runs' / default_case / 'param.txt').read_text()
        assert sha(archive / 'runs' / default_case / 'param.txt') == ref['param_sha256']
        param = param.replace(str(Path(ref['ic']).with_suffix('')), str(ic.with_suffix('')))
        param = param.replace(str(archive / 'runs' / default_case / 'output'), str(folder / 'output'))
        assert str(folder / 'output') in param and str(ic.with_suffix('')) in param
        (folder / 'param.txt').write_text(param)
        cases.append(dict(name=method, method=method, problem=problem, flags=extra, default=str(archive / 'runs' / default_case),
                          end=ref['end'], ic=str(ic), ic_sha256=sha(ic), param_sha256=sha(folder / 'param.txt'), ranks=1))
    write(root / 'campaign.json', dict(test='flip_limiter_sensitivity', methods=list(variants), cases=cases, description=__doc__))
    shutil.copy2(__file__, root / Path(__file__).name)
    print('Prepared', len(cases), 'cases.', flush=True)


def run(root, workers):
    cases = json.loads((root / 'campaign.json').read_text())['cases']

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
    p.add_argument('--workers', type=int, default=2)
    p.add_argument('--only', nargs='+', choices=list(VARIANTS))
    a = p.parse_args(); root = a.root.resolve()
    if a.action == 'prepare':
        prepare(root, a.only)
    elif a.action == 'build':
        build(root, None)
    else:
        run(root, a.workers)
