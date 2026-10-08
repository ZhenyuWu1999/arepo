#!/usr/bin/env python3
"""AREPO MMFV with a single hot cell (same glass, same hot ID as the RD 1-node runs).

Reuses the frozen second-order MMFV binary and native Voronoi areas of
sedov_mmfv_20260929_v1 (no rebuild); the hot energy E=1 is normalized by the
hot cell's Voronoi area, exactly as for the 21-cell MMFV run.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import h5py
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/'tests/rd'))
sys.path.insert(0, str(HERE))
from run_n_gauss3_split import ENV, sha, write, rewrite
from run import write_ic

MMFV = REPO.parent/'local_runs/sedov_mmfv_20260929_v1'
SWEEP = REPO.parent/'local_runs/sedov_injection_sweep_20260929_v1'


def main(root):
    root.mkdir(parents=True, exist_ok=False)
    for name in ('artifacts', 'inputs', 'runs'): (root/name).mkdir()
    shutil.copytree(MMFV/'artifacts/MMFV_moving', root/'artifacts/MMFV_moving')
    meta = json.loads((root/'artifacts/MMFV_moving/provenance.json').read_text())
    assert sha(root/'artifacts/MMFV_moving/Arepo') == meta['binary_sha256']
    hot_ids = json.loads((SWEEP/'campaign.json').read_text())['seeds']['nearest1']['ids']
    area = np.load(MMFV/'inputs/voronoi_area.npy')
    with h5py.File(MMFV/'inputs/sedov_nearest21.hdf5') as f:
        xy = f['PartType0/Coordinates'][:, :2]; ids = f['PartType0/ParticleIDs'][:]
    assert np.array_equal(ids, np.arange(1, len(ids)+1))
    hot = np.isin(ids, hot_ids); assert hot.sum() == 1
    u = np.full(len(xy), 1.5e-6); u[hot] = 1/area[hot].sum()
    ic = root/'inputs/sedov_nearest1_voronoi.hdf5'; write_ic(ic, xy, u)
    folder = root/'runs/nearest1_MMFV'; folder.mkdir()
    template = (MMFV/'runs/nearest21/param.txt').read_text()
    (folder/'param.txt').write_text(rewrite(template, dict(InitCondFile=ic.with_suffix(''), OutputDir=str(folder/'output')+'/',
                                                           TimeLimitCPU=14400)))
    write(root/'campaign.json', dict(test='Sedov_2d_mmfv_single', hot_ids=hot_ids, hot_voronoi_area=float(area[hot].sum()),
        hot_u=float(u[hot][0]), ic_sha256=sha(ic), param_sha256=sha(folder/'param.txt'), binary_sha256=meta['binary_sha256'],
        binary_source=str(MMFV), description=__doc__))
    shutil.copy2(__file__, root/'run_mmfv_single.py')
    start = time.monotonic(); cmd = [str(root/'artifacts/MMFV_moving/Arepo'), 'param.txt']
    with (folder/'run.log').open('w') as f:
        code = subprocess.run(cmd, cwd=folder, env=ENV, stdout=f, stderr=subprocess.STDOUT).returncode
    status = dict(returncode=code, seconds=time.monotonic()-start, command=cmd, binary_sha256=meta['binary_sha256'])
    write(folder/'run_status.json', status); print(json.dumps(status), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('root', type=Path)
    main(p.parse_args().root.resolve())
