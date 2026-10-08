#!/usr/bin/env python3
"""Edge-HLLC RD on the 130-node (r=.05) Sedov injection, for a matched comparison
with the only completed N-scheme Sedov run (static N, log3 §156).

Reuses the frozen, hash-verified HLLC_static/HLLC_moving binaries of
sedov_hllc_20260930_v1 (no rebuild) and the byte-identical disk005 IC and
parameter template of the archived Rusanov campaign. 21-node N fails
(static N/RK2 at t=.00672, first-order at .00663), so no 21-node N exists.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/'tests/rd'))
from run_n_gauss3_split import ENV, sha, write, rewrite

HLLC = REPO.parent/'local_runs/sedov_hllc_20260930_v1'
RUSANOV = REPO.parent/'local_runs/sedov_positivity_20260929_v2'
BASE = REPO.parent/'local_runs/sedov_2d_20260929_v1'


def main(root):
    root.mkdir(parents=True, exist_ok=False)
    for name in ('artifacts', 'inputs', 'runs'): (root/name).mkdir()
    base = {c['name']: c for c in json.loads((BASE/'campaign.json').read_text())['cases']}
    ic = root/'inputs/sedov_disk005.hdf5'
    shutil.copy2(RUSANOV/'inputs/sedov_disk005.hdf5', ic)
    assert sha(ic) == base['disk005_N_static_lab']['ic_sha256']
    shutil.copy2(RUSANOV/'inputs/median_dual_area.npy', root/'inputs/median_dual_area.npy')
    cases = []
    for method in ('HLLC_static', 'HLLC_moving'):
        src = HLLC/'artifacts'/method; dst = root/'artifacts'/method
        shutil.copytree(src, dst)
        meta = json.loads((dst/'provenance.json').read_text())
        assert sha(dst/'Arepo') == meta['binary_sha256'] and sha(dst/'Config.sh') == meta['config_sha256']
        mesh = method.split('_')[1]
        template = RUSANOV/'runs'/f'nearest21_Rusanov_{mesh}'/'param.txt'
        folder = root/'runs'/f'disk005_{method}'; folder.mkdir()
        (folder/'param.txt').write_text(rewrite(template.read_text(), dict(InitCondFile=ic.with_suffix(''),
            OutputDir=str(folder/'output')+'/', TimeMax=.05, TimeBetSnapshot=.0125, TimeBetStatistics=.0125,
            MaxSizeTimestep=.01)))
        cases.append(dict(name=folder.name, method=method, binary_sha256=meta['binary_sha256'], ic=str(ic),
                          ic_sha256=sha(ic), param_sha256=sha(folder/'param.txt'), param_template_sha256=sha(template)))
    write(root/'campaign.json', dict(test='Sedov_2d_hllc_disk005', cases=cases,
        binary_source_archive=str(HLLC), binary_source_tar_sha256=sha(HLLC/'source.tar'), description=__doc__))
    shutil.copy2(__file__, root/'run_hllc_disk005.py')

    def one(c):
        folder = root/'runs'/c['name']; cmd = [str(root/'artifacts'/c['method']/'Arepo'), 'param.txt']
        start = time.monotonic()
        with (folder/'run.log').open('w') as f:
            code = subprocess.run(cmd, cwd=folder, env=ENV, stdout=f, stderr=subprocess.STDOUT).returncode
        status = dict(name=c['name'], returncode=code, seconds=time.monotonic()-start, command=cmd,
                      binary_sha256=c['binary_sha256'])
        write(folder/'run_status.json', status); print(json.dumps(status), flush=True)
    with ThreadPoolExecutor(2) as pool:
        list(pool.map(one, cases))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('root', type=Path)
    main(p.parse_args().root.resolve())
