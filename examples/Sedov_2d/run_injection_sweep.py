#!/usr/bin/env python3
"""One/seven-node Sedov injection controls using frozen moving Rusanov binaries."""
import argparse
import json
from pathlib import Path
import shutil
import sys

import h5py
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tests/rd'))
from run_n_gauss3_split import ENV, sha, write, rewrite
from run import write_ic, execute, SWIFT

ARCHIVES = {
    'Rusanov_moving': REPO.parent / 'local_runs/sedov_positivity_20260929_v2',
    'Rusanov_moving_repair': REPO.parent / 'local_runs/sedov_topology_repair_20260929_v1',
}


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    for name in ('inputs', 'artifacts', 'configs', 'runs', 'sources', 'scripts', 'reference'):
        (root / name).mkdir()
    base = ARCHIVES['Rusanov_moving']
    shutil.copy2(base / 'inputs/median_dual_area.npy', root / 'inputs/median_dual_area.npy')
    shutil.copy2(base / 'inputs/uniform.hdf5', root / 'inputs/uniform.hdf5')
    with h5py.File(base / 'inputs/sedov_nearest21.hdf5') as f:
        xy = f['PartType0/Coordinates'][:, :2]
    area = np.load(root / 'inputs/median_dual_area.npy')
    radius = np.linalg.norm(xy - .5, axis=1)
    ordered = np.argsort(radius)
    seeds = {}
    for count in (1, 7):
        hot = ordered[:count]
        u = np.full(len(xy), 1e-6 / (5/3 - 1))
        u[hot] = 1. / area[hot].sum()
        assert abs(area[hot] @ u[hot] - 1.) < 1e-14
        group = f'nearest{count}'
        write_ic(root / 'inputs' / f'sedov_{group}.hdf5', xy, u)
        seeds[group] = dict(count=count, ids=(hot+1).tolist(), radius=float(radius[hot].max()),
            hot_mass=float(area[hot].sum()), hot_specific_energy=float(u[hot][0]),
            hot_pressure=float((5/3-1)*u[hot][0]), total_energy=float(area @ u),
            mass_weighted_injection_center=np.average(xy[hot], weights=area[hot], axis=0).tolist())
    campaign = dict(test='Sedov_2d_injection_sweep', methods=list(ARCHIVES), cases=[], seeds=seeds,
        gamma=5/3, nodes=len(xy), nside=128, box_size=1., pressure0=1e-6, explosion_energy=1.,
        frame='lab', timestep='CFL0.1, cap0.01; adaptive synchronous dyadic steps',
        environment={k: ENV[k] for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS')},
        description=__doc__, limits='No solver change; reuse two separately frozen binaries. Original unlimited repair is not positivity preserving. No-repair runs retain known conservation drift.')
    for method, archive in ARCHIVES.items():
        artifact = archive / 'artifacts' / method
        meta = json.loads((artifact / 'provenance.json').read_text())
        assert sha(artifact / 'Arepo') == meta['binary_sha256']
        assert sha(artifact / 'Config.sh') == meta['config_sha256']
        assert sha(archive / 'source.tar') == meta['source_tar_sha256']
        shutil.copytree(artifact, root / 'artifacts' / method)
        shutil.copy2(artifact / 'Config.sh', root / 'configs' / f'{method}.sh')
        source = root / 'sources' / method; source.mkdir()
        for name in ('source.tar', 'source_provenance.json'):
            shutil.copy2(archive / name, source / name)
        write(source / 'reused_from.json', dict(archive=str(archive), binary_sha256=meta['binary_sha256']))
        template = (archive / 'runs' / f'nearest21_{method}' / 'param.txt').read_text()
        for group in ('uniform', 'nearest1', 'nearest7'):
            folder = root / 'runs' / f'{group}_{method}'; folder.mkdir()
            ic = root / 'inputs' / ('uniform.hdf5' if group == 'uniform' else f'sedov_{group}.hdf5')
            end = .001 if group == 'uniform' else .05
            param = rewrite(template, dict(InitCondFile=ic.with_suffix(''), OutputDir=str(folder / 'output')+'/',
                TimeMax=end, TimeBetSnapshot=end/4, TimeBetStatistics=end/4, MaxSizeTimestep=min(.01,end/4)))
            (folder / 'param.txt').write_text(param)
            campaign['cases'].append(dict(name=folder.name, group=group, method=method, scheme='Rusanov',
                mesh='moving', frame='lab', end=end, cfl=.1, temporal='lumped RK2', ic=str(ic),
                ic_sha256=sha(ic), param_sha256=sha(folder / 'param.txt')))
    for name in ('makeIC.py', 'sedov.yml', 'plotSolution.py'):
        shutil.copy2(SWIFT / name, root / 'reference' / name)
    # Freeze the actual driver and its imported helpers before any execution.
    scripts = [Path(__file__), HERE/'run.py', REPO/'tests/rd/run_n_gauss3_split.py']
    for path in scripts:
        shutil.copy2(path, root / 'scripts' / path.name)
    write(root / 'script_hashes.json', {p.name: sha(p) for p in scripts})
    write(root / 'campaign.json', campaign)
    print(json.dumps(seeds, indent=2), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('prepare', 'run')); p.add_argument('root', type=Path)
    p.add_argument('--group', default='uniform'); p.add_argument('--select', nargs='+')
    a = p.parse_args(); root = a.root.resolve()
    if a.action == 'prepare':
        prepare(root)
    else:
        for name, digest in json.loads((root / 'script_hashes.json').read_text()).items():
            path = REPO/'tests/rd'/name if name == 'run_n_gauss3_split.py' else HERE/name
            assert sha(path) == digest
        execute(root, a.group, a.select)
