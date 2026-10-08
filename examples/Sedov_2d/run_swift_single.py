#!/usr/bin/env python3
"""SWIFT SPHENIX Sedov with a single injected particle, using the frozen default build.

Reuses swift_sedov_default_20260929_v1 (binary, stock sedov.yml, glass, makeIC.py;
all hash-checked). The only change is N_inject = 21 -> 1 in a copied makeIC script,
whose diff is recorded. Same command line as the default run.
"""
import argparse
import difflib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import h5py
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DEFAULT = REPO.parent/'local_runs/swift_sedov_default_20260929_v1'
SWEEP = REPO.parent/'local_runs/sedov_injection_sweep_20260929_v1'
ENV = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')


def sha(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n')


def main(root):
    root.mkdir(parents=True, exist_ok=False)
    shutil.copytree(DEFAULT/'artifact', root/'artifact')
    meta = json.loads((DEFAULT/'artifact/provenance.json').read_text())
    assert sha(root/'artifact/swift') == meta['binary_sha256']
    run = root/'run'; run.mkdir()
    expected = json.loads((DEFAULT/'run/inputs.json').read_text())
    for name in ('sedov.yml', 'makeIC.py', 'glassPlane_128.hdf5'):
        shutil.copy2(DEFAULT/'run'/name, run/name); assert sha(run/name) == expected[name]
    stock = (run/'makeIC.py').read_text()
    assert stock.count('N_inject = 21') == 1
    single = stock.replace('N_inject = 21', 'N_inject = 1')
    (run/'makeIC_single.py').write_text(single)
    (run/'makeIC_single.diff').write_text(''.join(difflib.unified_diff(
        stock.splitlines(True), single.splitlines(True), 'makeIC.py', 'makeIC_single.py')))
    def invoke(argv, log):
        start = time.monotonic()
        with (run/log).open('w') as stream:
            code = subprocess.run(argv, cwd=run, env=ENV, stdout=stream, stderr=subprocess.STDOUT).returncode
        return dict(argv=list(map(str, argv)), returncode=code, seconds=time.monotonic()-start)
    ic_status = invoke([sys.executable, 'makeIC_single.py'], 'make_ic.log')
    assert ic_status['returncode'] == 0
    with h5py.File(run/'sedov.hdf5') as f:
        ids = f['PartType0/ParticleIDs'][:]; u = f['PartType0/InternalEnergy'][:]
    hot_ids = ids[u > 1e-3].astype(int).tolist()
    rd_ids = json.loads((SWEEP/'campaign.json').read_text())['seeds']['nearest1']['ids']
    status = invoke([str(root/'artifact/swift'), '--hydro', '--limiter', '--threads=1', 'sedov.yml'], 'output.log')
    write(root/'run/run_status.json', dict(make_ic=ic_status, swift=status, binary_sha256=meta['binary_sha256'],
        inputs={name: sha(run/name) for name in ('sedov.yml', 'makeIC_single.py', 'sedov.hdf5', 'glassPlane_128.hdf5')},
        hot_ids=hot_ids, rd_single_hot_ids=rd_ids, same_hot_particle_as_rd=hot_ids == rd_ids))
    shutil.copy2(__file__, root/'run_swift_single.py')
    print(json.dumps(dict(returncode=status['returncode'], seconds=status['seconds'], hot_ids=hot_ids, rd=rd_ids)))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('root', type=Path)
    main(p.parse_args().root.resolve())
