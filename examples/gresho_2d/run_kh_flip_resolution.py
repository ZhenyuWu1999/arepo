#!/usr/bin/env python3
"""KH glass48 vs glass96: does the flip-transfer perturbation shrink with resolution?

Equal-step moving N (contour residual, element co-moving frame,
examples/gresho_2d/Config_FS_con_cm_N.sh), one rank:
  arpaia    no topology treatment, Arpaia mass (not conservative)
  campoli   Campoli mass, no topology treatment (flips still change totals)
  flip      Campoli + RD_ALE_FLIP_TRANSFER (uniform-shift high endpoint)
  flip_h1   Campoli + RD_ALE_FLIP_TRANSFER, RD_FLIP_HIGH_MODE=1 (receivers only)
ICs: the smoothed KH state (rho 1/2, vx -/+.5, tanh width .025 at y=.25,.75,
vy=.1 sin(4 pi x), p=2.5, gamma 1.4) on the SWIFT glassPlane_48 (n=48; the
archived kh_smooth.hdf5 is regenerated bit-for-bit) and on its 2x2 tiling
(n=96, IDs 1..9216).  Parameters: param_KH_N_glass48_toporepair_t10.txt
(CFL .3, dt cap .02, snapshots every .2, t=10).
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
import subprocess
import time
import h5py
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tests/rd'))
sys.path.insert(0, str(REPO / 'examples/Sedov_2d'))
from run_n_gauss3_split import ENV, sha, write, rewrite, build   # noqa: E402
from run_hllc import freeze                                       # noqa: E402
from flip_campaign_checks import check_configs                    # noqa: E402

RUNS = REPO.parent / 'local_runs'
GLASS = RUNS / 'lda_baseline_glass_20260911/inputs/glassPlane_48.hdf5'
GLASS_SHA = '157e1a4767f4678d'
ARCHIVED = RUNS / 'sod_kh_lab_frame_20260924_v1/inputs/kh_smooth.hdf5'
ARCHIVED_SHA = '0204ab34a5d3d048'
METHODS = {'arpaia': [], 'campoli': ['RD_ALE_CAMPOLI_MASS'],
           'flip': ['RD_ALE_CAMPOLI_MASS', 'RD_ALE_FLIP_TRANSFER', 'RD_FLIP_HIGH_MODE=0'],
           'flip_h1': ['RD_ALE_CAMPOLI_MASS', 'RD_ALE_FLIP_TRANSFER', 'RD_FLIP_HIGH_MODE=1']}
RESOLUTIONS = (48, 96)


def kh_ic(target, n):
    tile = n // 48
    with h5py.File(GLASS) as g:
        xg = g['PartType0/Coordinates'][:, :2] % 1.0
        gid = g['PartType0/ParticleIDs'][:]
    x = np.concatenate([(xg + [i, j]) / tile for j in range(tile) for i in range(tile)]) if tile > 1 else xg
    ids = gid if tile == 1 else np.arange(1, len(x) + 1, dtype=gid.dtype)
    prof = .5 * (np.tanh((x[:, 1] - .25) / .025) - np.tanh((x[:, 1] - .75) / .025))
    rho = 1 + prof
    vel = np.zeros((len(x), 3)); vel[:, 0] = -.5 + prof; vel[:, 1] = .1 * np.sin(4 * np.pi * x[:, 0])
    with h5py.File(ARCHIVED) as src, h5py.File(target, 'w') as f:
        h = f.create_group('Header')
        for k, v in src['Header'].attrs.items():
            h.attrs[k] = v
        count = np.zeros(6, dtype=np.int32); count[0] = len(x)
        h.attrs['NumPart_ThisFile'] = count; h.attrs['NumPart_Total'] = count; h.attrs['KHMeshN'] = n
        p = f.create_group('PartType0')
        coords = np.zeros((len(x), 3)); coords[:, :2] = x
        p['Coordinates'] = coords; p['InternalEnergy'] = 2.5 / (.4 * rho); p['Masses'] = rho
        p['ParticleIDs'] = ids; p['Velocities'] = vel
    if n == 48:   # the generator must reproduce the archived IC exactly
        with h5py.File(ARCHIVED) as a, h5py.File(target) as b:
            for k in ('Coordinates', 'InternalEnergy', 'Masses', 'ParticleIDs', 'Velocities'):
                assert np.array_equal(a['PartType0'][k][:], b['PartType0'][k][:]), k


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    freeze(root)
    for folder in ('configs', 'artifacts', 'runs', 'inputs'):
        (root / folder).mkdir()
    assert sha(GLASS).startswith(GLASS_SHA) and sha(ARCHIVED).startswith(ARCHIVED_SHA)
    for n in RESOLUTIONS:
        kh_ic(root / 'inputs' / f'kh_glass{n}.hdf5', n)
    base = (HERE / 'Config_FS_con_cm_N.sh').read_text().rstrip('\n') + '\n'
    template = (HERE / 'param_KH_N_glass48_toporepair_t10.txt').read_text()
    cases = []
    texts = {m: '# KH flip resolution study; see campaign.json.\n' + base + ''.join(f'{flag}\n' for flag in extra)
             for m, extra in METHODS.items()}
    check_configs(texts)
    for method, extra in METHODS.items():
        (root / 'configs' / f'{method}.sh').write_text(texts[method])
        for n in RESOLUTIONS:
            name = f'kh{n}_{method}'; folder = root / 'runs' / name; folder.mkdir()
            ic = root / 'inputs' / f'kh_glass{n}.hdf5'
            param = rewrite(template, dict(InitCondFile=ic.with_suffix(''), OutputDir=str(folder / 'output') + '/',
                                           TimeMax=10, TimeLimitCPU=400000, MaxMemSize=2500))
            (folder / 'param.txt').write_text(param)
            cases.append(dict(name=name, method=method, flags=extra, n=n, end=10., ic=str(ic), ic_sha256=sha(ic),
                              param_sha256=sha(folder / 'param.txt'), ranks=1))
    write(root / 'campaign.json', dict(test='KH_flip_transfer_resolution', methods=list(METHODS), cases=cases,
                                       description=__doc__))
    shutil.copy2(__file__, root / Path(__file__).name)
    print('Prepared', len(cases), 'cases.', flush=True)


def run(root, workers, selected):
    campaign = json.loads((root / 'campaign.json').read_text())
    # glass96 first: they are the long ones
    cases = sorted((c for c in campaign['cases'] if not selected or c['name'] in selected), key=lambda c: -c['n'])

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
        write(folder / 'run_status.json', dict(command=cmd, returncode=code, seconds=time.monotonic() - start,
                                               binary_sha256=meta['binary_sha256']))
        print('DONE', c['name'], code, flush=True)
        return code

    with ThreadPoolExecutor(workers) as pool:
        codes = list(pool.map(one, cases))
    assert all(c == 0 for c in codes), codes


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('root', type=Path)
    p.add_argument('--stage', choices=('prepare', 'build', 'run', 'all'), default='all')
    p.add_argument('--workers', type=int, default=4)
    p.add_argument('--select', nargs='+')
    a = p.parse_args(); root = a.root.resolve()
    if a.stage in ('prepare', 'all'):
        prepare(root)
    if a.stage in ('build', 'all'):
        build(root, None)
    if a.stage in ('run', 'all'):
        run(root, a.workers, a.select)
