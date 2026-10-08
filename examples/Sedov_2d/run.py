#!/usr/bin/env python3
"""Local Sedov pilots with frozen current N/Roe and LDA/Gauss3 binaries."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

import h5py
import numpy as np
from scipy.spatial import Delaunay

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tests/rd'))
if (HERE / 'run_n_gauss3_split.py').exists():
    sys.path.insert(0, str(HERE))
from run_n_gauss3_split import ENV, sha, write, rewrite, state

BASE = Path('/Users/zhenyuwu/arepo_rd/local_runs/gresho_glass_boost10_lab_20260927_v1')
GLASS = Path('/Users/zhenyuwu/arepo_rd/local_runs/swift_glass/glassPlane_128.hdf5')
SWIFT = Path('/Users/zhenyuwu/SWIFT/examples/HydroTests/SedovBlast_2D')
GAMMA = 5 / 3
METHODS = ['N_static_lab', 'N_moving_lab', 'LDA_static_lab', 'LDA_moving_lab']


def periodic_areas(xy):
    """Median-dual areas from a periodic Delaunay triangulation; native-checked."""
    n = len(xy)
    tiled = np.concatenate([xy + [i, j] for i in (-1, 0, 1) for j in (-1, 0, 1)])
    tri = Delaunay(tiled).simplices
    vertices = tiled[tri]
    centroids = vertices.mean(axis=1)
    keep = np.all((centroids >= 0) & (centroids < 1), axis=1)
    tri, vertices = tri[keep], vertices[keep]
    a, b = vertices[:, 1] - vertices[:, 0], vertices[:, 2] - vertices[:, 0]
    areas = np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]) / 2
    dual = np.bincount((tri % n).ravel(), weights=np.repeat(areas / 3, 3), minlength=n)
    assert len(tri) == 2 * n and abs(dual.sum() - 1) < 1e-12 and np.all(dual > 0)
    return dual


def write_ic(path, xy, u, uniform=False):
    n = len(xy)
    xyz = np.zeros((n, 3)); xyz[:, :2] = xy
    velocity = np.zeros_like(xyz)
    if uniform:
        velocity[:, :2] = [.37, -.21]
    with h5py.File(path, 'w') as f:
        h = f.create_group('Header'); g = f.create_group('PartType0')
        counts = np.array([n, 0, 0, 0, 0, 0], dtype=np.uint32)
        for key in ('NumPart_ThisFile', 'NumPart_Total'):
            h.attrs[key] = counts
        h.attrs['NumPart_Total_HighWord'] = np.zeros(6, dtype=np.uint32)
        h.attrs['MassTable'] = np.zeros(6)
        for key, value in dict(BoxSize=1., Time=0., Redshift=0., NumFilesPerSnapshot=1,
                               HubbleParam=1., Flag_DoublePrecision=1, Gamma=GAMMA).items():
            h.attrs[key] = value
        for key in ('Omega0', 'OmegaB', 'OmegaLambda', 'Flag_Sfr', 'Flag_Cooling',
                    'Flag_StellarAge', 'Flag_Metals', 'Flag_Feedback'):
            h.attrs[key] = 0
        h.attrs['TestName'] = 'Sedov_2d'
        # READ_MASS_AS_DENSITY_IN_INPUT converts density to native dual-cell mass.
        for key, value in dict(Coordinates=xyz, Masses=np.ones(n), InternalEnergy=u,
                               Velocities=velocity, ParticleIDs=np.arange(1, n+1, dtype=np.uint64)).items():
            g.create_dataset(key, data=value)


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    for folder in ('configs', 'artifacts', 'inputs', 'runs', 'reference'):
        (root / folder).mkdir()
    prov = json.loads((BASE / 'source_provenance.json').read_text())
    assert sha(BASE / 'source.tar') == prov['source_tar_sha256']
    checked = []
    for name, digest in prov['tracked_hashes'].items():
        if name.startswith('src/') or name in ('Makefile', 'defines_extra'):
            assert sha(REPO / name) == digest, name
            checked.append(name)
    for name in ('source.tar', 'source_provenance.json'):
        shutil.copy2(BASE / name, root / name)
    for method in METHODS:
        artifact = BASE / 'artifacts' / method
        meta = json.loads((artifact / 'provenance.json').read_text())
        assert sha(artifact / 'Arepo') == meta['binary_sha256']
        assert sha(artifact / 'Config.sh') == meta['config_sha256']
        assert meta['source_tar_sha256'] == prov['source_tar_sha256']
        shutil.copytree(artifact, root / 'artifacts' / method)
        shutil.copy2(artifact / 'Config.sh', root / 'configs' / (method + '.sh'))
    with h5py.File(GLASS) as f:
        xy = f['PartType0/Coordinates'][:, :2] % 1
    assert xy.shape == (128**2, 2)
    dual = periodic_areas(xy)
    np.save(root / 'inputs/median_dual_area.npy', dual)
    write_ic(root / 'inputs/uniform.hdf5', xy, np.full(len(xy), 1/(GAMMA-1)), True)
    radius = np.linalg.norm(xy - .5, axis=1)
    hot = np.argsort(radius)[:21]
    u = np.full(len(xy), 1e-6 / (GAMMA-1))
    u[hot] = 1 / dual[hot].sum()
    write_ic(root / 'inputs/sedov_nearest21.hdf5', xy, u)
    refs = {}
    for name in ('makeIC.py', 'sedov.yml', 'plotSolution.py', 'getGlass.sh'):
        shutil.copy2(SWIFT / name, root / 'reference' / name)
        refs[str(SWIFT / name)] = sha(SWIFT / name)
    write(root / 'campaign.json', dict(test='Sedov_2d', methods=METHODS, cases=[],
        gamma=GAMMA, rho0=1., pressure0=1e-6, box_size=1., end=.05, explosion_energy=1.,
        mesh='SWIFT glass128', nodes=len(xy), nside=128,
        injection='Uniform specific internal energy in nearest21 nodes, normalized by RD median-dual mass.',
        injection_count=len(hot), hot_ids=(hot+1).tolist(), injection_radius=float(radius[hot].max()),
        hot_dual_area=float(dual[hot].sum()), initial_total_energy=float(dual @ u),
        glass_source=str(GLASS), glass_sha256=sha(GLASS), reference_hashes=refs,
        source_archive=str(BASE), source_tar_sha256=prov['source_tar_sha256'],
        source_files_checked=checked, environment={k: ENV[k] for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS')},
        workers=2, frame='lab', timestep='CFL0.1, cap0.01; global equal adaptive dyadic steps',
        limits='No new limiter, floor or solver change. SWIFT physical setup, not identical SPH particle masses. Finite injection radius differs from point-source similarity solution.'))
    for method in METHODS:
        add_case(root, 'uniform', method, 'uniform.hdf5', .001, .1)
        add_case(root, 'nearest21', method, 'sedov_nearest21.hdf5', .05, .1)
    shutil.copy2(__file__, root / 'run.py')
    shutil.copy2(REPO / 'tests/rd/run_n_gauss3_split.py', root / 'run_n_gauss3_split.py')
    print('Prepared 4 reused binaries, 4 uniform gates, 4 Sedov pilots.', flush=True)


def add_case(root, group, method, ic_name, end, cfl):
    campaign = json.loads((root / 'campaign.json').read_text())
    name = f'{group}_{method}'
    folder = root / 'runs' / name; folder.mkdir(exist_ok=False)
    ic = root / 'inputs' / ic_name
    template_method = 'N_static_lab' if method == 'N_static_firstorder' else method
    template = (BASE / 'runs' / f'science_{template_method}' / 'param.txt').read_text()
    param = rewrite(template, dict(InitCondFile=ic.with_suffix(''), OutputDir=str(folder / 'output')+'/',
        TimeMax=end, TimeBetSnapshot=end/4, TimeBetStatistics=end/4, MaxSizeTimestep=min(.01, end/4),
        CourantFac=cfl, MinSizeTimestep=1e-12, MaxMemSize=1024, TimeLimitCPU=1800,
        InitGasTemp=0., MinGasTemp=0., MinEgySpec=0., MinimumDensityOnStartUp=0.))
    (folder / 'param.txt').write_text(param)
    campaign['cases'].append(dict(name=name, group=group, method=method, scheme=method.split('_')[0],
        mesh='moving' if 'moving' in method else 'static', frame='lab', end=end, cfl=cfl,
        temporal='first-order' if 'firstorder' in method else 'RK2',
        ic=str(ic), ic_sha256=sha(ic), param_sha256=sha(folder / 'param.txt')))
    write(root / 'campaign.json', campaign)


def execute(root, group, selected=None):
    campaign = json.loads((root / 'campaign.json').read_text())
    cases = [c for c in campaign['cases'] if c['group'] == group and (not selected or c['method'] in selected)]
    dual = np.load(root / 'inputs/median_dual_area.npy')
    def one(c):
        method = c['method']; folder = root / 'runs' / c['name']
        if group != 'uniform':
            gate = root / 'runs' / f'uniform_{method}'
            assert json.loads((gate / 'run_status.json').read_text())['returncode'] == 0
            snaps = sorted((gate / 'output').glob('snap_*.hdf5'))
            a, b = state(snaps[0]), state(snaps[-1])
            defect = max(float(np.max(abs(b[k]-a[k]))) for k in ('rho', 'p', 'v'))
            assert defect < 1e-12, (method, defect)
            assert np.max(abs(a['w']-dual)) < 1e-12
        assert not (folder / 'run.log').exists()
        artifact = root / 'artifacts' / method
        meta = json.loads((artifact / 'provenance.json').read_text())
        assert sha(artifact / 'Arepo') == meta['binary_sha256']
        assert sha(c['ic']) == c['ic_sha256'] and sha(folder / 'param.txt') == c['param_sha256']
        start = time.monotonic(); cmd = [str(artifact / 'Arepo'), 'param.txt']
        print('START', c['name'], flush=True)
        with (folder / 'run.log').open('w') as stream:
            try:
                result = subprocess.run(cmd, cwd=folder, env=ENV, stdout=stream, stderr=subprocess.STDOUT, timeout=1800)
                code = result.returncode
            except subprocess.TimeoutExpired:
                code = 'timeout1800'
        out = dict(name=c['name'], returncode=code, seconds=time.monotonic()-start,
                   binary_sha256=meta['binary_sha256'], command=cmd)
        write(folder / 'run_status.json', out)
        print(json.dumps(out), flush=True)
        return out
    with ThreadPoolExecutor(max_workers=2) as pool:
        result = list(pool.map(one, cases))
    write(root / f'status_{group}.json', result)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('prepare', 'run'))
    p.add_argument('root', type=Path)
    p.add_argument('--group', default='uniform')
    p.add_argument('--select', nargs='+')
    a = p.parse_args()
    if a.action == 'prepare':
        prepare(a.root.resolve())
    else:
        execute(a.root.resolve(), a.group, a.select)
