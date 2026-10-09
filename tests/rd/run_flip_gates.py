#!/usr/bin/env python3
"""Phase-1 native gates for the flip-element transfer (RD_ALE_FLIP_TRANSFER).

Equal-step moving RD, one rank, gamma 1.4, Campoli mass for every method, so
that with fixed connectivity the update telescopes and the edge flips are the
only remaining conservation loss.  Each scheme runs without and with the
transfer:
  (since 2026-10-09 every transfer Config states RD_FLIP_HIGH_MODE; *_flip is mode 0)
  N, LDA, B  examples/gresho_2d/Config_FS_con_cm{_N,,_B}.sh (contour residual,
             element co-moving frame, face-angle regularisation)
  HLLC       examples/Sedov_2d/Config_HLLC_moving.sh with GAMMA=1.4 (edge-HLLC
             FV-RD, lab frame, lumped RK2)
  N_flip_h1  N with RD_FLIP_HIGH_MODE=1 (receiver-weighted high endpoint)
Problems reuse archived ICs and parameter files:
  uniform  glass48, t=1/32, and uniform_random: the same state on 2304 uniform
           random points (seed 20261009), t=1/4, where regularisation drives
           ~1300 flip cavities (state must be unchanged to 1e-12)
  sod      glass Nx64 tube in the unit periodic box, CFL .08, t=.08
  yee      boost-1 isentropic vortex, glass48/96, CFL .2, dt caps 1/256, 1/512, t=1
  kh       smoothed KH glass48 (kh_state width .025), t=10, as in the KH
           repair/refresh campaign (param_KH_N_glass48_toporepair_t10.txt)
Groups: uniform, science (sod + yee), kh.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import h5py
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / 'examples/Sedov_2d'))
from run_n_gauss3_split import ENV, sha, write, rewrite, build, state   # noqa: E402
from run_hllc import freeze                                              # noqa: E402
from flip_campaign_checks import check_configs                           # noqa: E402

RUNS = REPO.parent / 'local_runs'
LEGACY = RUNS / 'legacy_split_20260912'
YEE = RUNS / 'yee_frame_convergence_20260924_v1'
INPUTS = {'uniform': (LEGACY / 'inputs/uniform_glass48.hdf5', 'cb1cf268c2f77e34'),
          'sod': (LEGACY / 'inputs/sod_glass_nx64.hdf5', None),
          'kh': (RUNS / 'sod_kh_lab_frame_20260924_v1/inputs/kh_smooth.hdf5', '0204ab34a5d3d048'),
          'yee48': (YEE / 'inputs/yee_glass48.hdf5', None), 'yee96': (YEE / 'inputs/yee_glass96.hdf5', None)}
BASES = {'N': REPO / 'examples/gresho_2d/Config_FS_con_cm_N.sh', 'LDA': REPO / 'examples/gresho_2d/Config_FS_con_cm.sh',
         'B': REPO / 'examples/gresho_2d/Config_FS_con_cm_B.sh', 'HLLC': REPO / 'examples/Sedov_2d/Config_HLLC_moving.sh'}


def methods():
    out = {}
    for scheme in BASES:
        out[f'{scheme}_campoli'] = (scheme, ['RD_ALE_CAMPOLI_MASS'])
        out[f'{scheme}_flip'] = (scheme, ['RD_ALE_CAMPOLI_MASS', 'RD_ALE_FLIP_TRANSFER', 'RD_FLIP_HIGH_MODE=0'])
    out['N_flip_h1'] = ('N', ['RD_ALE_CAMPOLI_MASS', 'RD_ALE_FLIP_TRANSFER', 'RD_FLIP_HIGH_MODE=1'])
    return out


def config_text(scheme, extra):
    text = BASES[scheme].read_text()
    if scheme == 'HLLC':
        assert text.count('GAMMA=(5.0/3.0)') == 1
        text = text.replace('GAMMA=(5.0/3.0)', 'GAMMA=1.4')
    assert 'GAMMA=1.4\n' in text
    return ('# Flip-transfer gate; see campaign.json.\n' + text.rstrip('\n') + '\n'
            + ''.join(f'{flag}\n' for flag in extra))


def problems():
    yee = (RUNS / 'moving_equal_split_stages_20260914_v4/runs/yee_lda_split/param.txt').read_text()
    return {
        'uniform': ('uniform', (LEGACY / 'runs/uniform_split_frame/param.txt').read_text(), {}, 1 / 32),
        'uniform_random': ('uniform', (LEGACY / 'runs/uniform_split_frame/param.txt').read_text(),
                           dict(TimeMax=.25, TimeBetSnapshot=.125), .25),
        'sod': ('science', (LEGACY / 'runs/sod_split_frame/param.txt').read_text(), {}, .08),
        'yee48': ('science', yee, dict(TimeMax=1, TimeBetSnapshot=.5, TimeBetStatistics=.5, MaxSizeTimestep=1 / 256), 1.),
        'yee96': ('science', yee, dict(TimeMax=1, TimeBetSnapshot=.5, TimeBetStatistics=.5, MaxSizeTimestep=1 / 512), 1.),
        'kh': ('kh', (REPO / 'examples/gresho_2d/param_KH_N_glass48_toporepair_t10.txt').read_text(),
               dict(TimeMax=10, TimeLimitCPU=200000, MaxMemSize=1500), 10.)}


def uniform_random(target, seed=20261009):
    glass = INPUTS['uniform'][0]
    with h5py.File(glass) as src, h5py.File(target, 'w') as f:
        header = f.create_group('Header')
        for k, v in src['Header'].attrs.items():
            if not k.startswith('Yee'):
                header.attrs[k] = v
        header.attrs['GateRandomSeed'] = seed
        n = len(src['PartType0/ParticleIDs']); rng = np.random.default_rng(seed)
        x = np.zeros((n, 3)); x[:, :2] = rng.uniform(0, float(src['Header'].attrs['BoxSize']), (n, 2))
        g = f.create_group('PartType0')
        g['Coordinates'] = x; g['ParticleIDs'] = src['PartType0/ParticleIDs'][:]
        for k in ('InternalEnergy', 'Masses', 'Velocities'):
            v = src['PartType0'][k][:]
            assert np.all(v == v[0]), k
            g[k] = v


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    freeze(root)
    for folder in ('configs', 'artifacts', 'runs', 'inputs'):
        (root / folder).mkdir()
    for problem, (path, prefix) in INPUTS.items():
        if prefix:
            assert sha(path).startswith(prefix), (problem, sha(path))
        shutil.copy2(path, root / 'inputs' / path.name)
    uniform_random(root / 'inputs/uniform_random48.hdf5')
    table = methods()
    modes = check_configs({m: config_text(s, e) for m, (s, e) in table.items()})
    for method, (scheme, extra) in table.items():
        (root / 'configs' / f'{method}.sh').write_text(config_text(scheme, extra))
    cases = []
    for problem, (group, template, updates, end) in problems().items():
        ic = root / 'inputs' / (INPUTS[problem][0].name if problem in INPUTS else f'{problem}48.hdf5')
        for method, (scheme, extra) in table.items():
            name = f'{problem}_{method}'; folder = root / 'runs' / name; folder.mkdir()
            param = rewrite(template, dict(InitCondFile=ic.with_suffix(''), OutputDir=str(folder / 'output') + '/', **updates))
            (folder / 'param.txt').write_text(param)
            cases.append(dict(name=name, method=method, scheme=scheme, flags=extra, flip_high_mode=modes[method],
                              problem=problem, group=group, end=end,
                              ic=str(ic), ic_sha256=sha(ic), param_sha256=sha(folder / 'param.txt'), ranks=1))
    write(root / 'campaign.json', dict(test='flip_transfer_phase1_gates', methods=list(table), cases=cases,
                                       description=__doc__))
    shutil.copy2(__file__, root / Path(__file__).name)
    print('Prepared', len(cases), 'cases and', len(table), 'builds.', flush=True)


def run(root, group, selected, workers):
    campaign = json.loads((root / 'campaign.json').read_text())
    cases = [c for c in campaign['cases'] if c['group'] == group and (not selected or c['name'] in selected)]
    if group != 'uniform':
        for method in {c['method'] for c in cases}:
            for gate in ('uniform', 'uniform_random'):
                folder = root / 'runs' / f'{gate}_{method}'
                assert json.loads((folder / 'run_status.json').read_text())['returncode'] == 0, (gate, method)
                snaps = sorted((folder / 'output').glob('snap_*.hdf5'))
                a, b = state(snaps[0]), state(snaps[-1])
                defect = max(float(abs(b[k] - a[k]).max()) for k in ('rho', 'v', 'p'))
                assert defect < 1e-12, (gate, method, defect)

    def one(c):
        folder = root / 'runs' / c['name']; artifact = root / 'artifacts' / c['method']
        assert not (folder / 'run.log').exists(), c['name']
        meta = json.loads((artifact / 'provenance.json').read_text())
        assert sha(artifact / 'Arepo') == meta['binary_sha256']
        assert sha(folder / 'param.txt') == c['param_sha256'] and sha(c['ic']) == c['ic_sha256']
        cmd = [str(artifact / 'Arepo'), 'param.txt']; start = time.monotonic()
        print('START', c['name'], flush=True)
        with (folder / 'run.log').open('w') as stream:
            code = subprocess.run(cmd, cwd=folder, env=ENV, stdout=stream, stderr=subprocess.STDOUT).returncode
        result = dict(name=c['name'], returncode=code, seconds=time.monotonic() - start,
                      binary_sha256=meta['binary_sha256'], command=cmd)
        write(folder / 'run_status.json', result)
        print('DONE', c['name'], code, flush=True)
        return result

    with ThreadPoolExecutor(workers) as pool:
        rows = list(pool.map(one, cases))
    write(root / f'status_{group}.json', rows)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('action', choices=('prepare', 'build', 'run'))
    p.add_argument('root', type=Path)
    p.add_argument('--group', choices=('uniform', 'science', 'kh'), default='uniform')
    p.add_argument('--select', nargs='+')
    p.add_argument('--workers', type=int, default=4)
    a = p.parse_args(); root = a.root.resolve()
    if a.action == 'prepare':
        prepare(root)
    elif a.action == 'build':
        build(root, a.select)
    else:
        run(root, a.group, a.select, a.workers)
