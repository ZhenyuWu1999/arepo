#!/usr/bin/env python3
"""KH glass48 t=10: does the old topology repair still move the solution once
the predictor uses the repaired primitives?

Three frozen builds from one source snapshot (equal-step moving N, contour,
co-moving frame, Arpaia; examples/gresho_2d/Config_FS_con_cm_N*.sh):
  control  no repair (Config_FS_con_cm_N.sh)
  stale    old repair, predictor primitives NOT refreshed (pre-2026-10-09 N/LDA/B
           behaviour; RD_ALE_REPAIR_STALE_PRIMITIVES)
  refresh  old repair with the all-scheme primitive refresh (new default)
Parameters: param_KH_N_glass48_toporepair_t10.txt, with the local smoothed KH
glass48 IC (kh_state, width .025, gamma 1.4; archived kh_smooth.hdf5).
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
sys.path.insert(0, str(REPO / 'tests/rd'))
sys.path.insert(0, str(REPO / 'examples/Sedov_2d'))
from run_n_gauss3_split import ENV, sha, write, rewrite, build   # noqa: E402
from run_hllc import freeze                                       # noqa: E402

IC = REPO.parent / 'local_runs/sod_kh_lab_frame_20260924_v1/inputs/kh_smooth.hdf5'
IC_SHA = '0204ab34a5d3d048'
METHODS = {'control': ('Config_FS_con_cm_N.sh', []),
           'stale': ('Config_FS_con_cm_N_toporepair.sh', ['RD_ALE_REPAIR_STALE_PRIMITIVES']),
           'refresh': ('Config_FS_con_cm_N_toporepair.sh', [])}


def prepare(root, tmax):
    root.mkdir(parents=True, exist_ok=False)
    freeze(root)
    for folder in ('configs', 'artifacts', 'runs', 'inputs'):
        (root / folder).mkdir()
    assert sha(IC).startswith(IC_SHA), sha(IC)
    shutil.copy2(IC, root / 'inputs/kh_glass48.hdf5')
    template = (HERE / 'param_KH_N_glass48_toporepair_t10.txt').read_text()
    cases = []
    for method, (config, extra) in METHODS.items():
        text = (HERE / config).read_text().rstrip('\n') + '\n' + ''.join(f'{flag}\n' for flag in extra)
        (root / 'configs' / f'{method}.sh').write_text(text)
        folder = root / 'runs' / method; folder.mkdir()
        param = rewrite(template, dict(InitCondFile=root / 'inputs/kh_glass48', OutputDir=str(folder / 'output') + '/',
                                       TimeMax=tmax, TimeLimitCPU=200000, MaxMemSize=1500))
        (folder / 'param.txt').write_text(param)
        cases.append(dict(name=method, method=method, param_sha256=sha(folder / 'param.txt'),
                          ic=str(root / 'inputs/kh_glass48.hdf5'), ic_sha256=sha(root / 'inputs/kh_glass48.hdf5')))
    write(root / 'campaign.json', dict(test='KH_glass48_repair_primitive_refresh', tmax=tmax, methods=list(METHODS),
                                       cases=cases, description=__doc__))
    shutil.copy2(__file__, root / Path(__file__).name)


def run(root):
    campaign = json.loads((root / 'campaign.json').read_text())

    def one(case):
        folder = root / 'runs' / case['name']; artifact = root / 'artifacts' / case['method']
        assert sha(artifact / 'Arepo') == json.loads((artifact / 'provenance.json').read_text())['binary_sha256']
        assert sha(folder / 'param.txt') == case['param_sha256'] and sha(case['ic']) == case['ic_sha256']
        start = time.monotonic(); cmd = [str(artifact / 'Arepo'), 'param.txt']
        with (folder / 'run.log').open('w') as stream:
            code = subprocess.run(cmd, cwd=folder, env=ENV, stdout=stream, stderr=subprocess.STDOUT).returncode
        write(folder / 'run_status.json', dict(command=cmd, returncode=code, seconds=time.monotonic() - start))
        print('DONE', case['name'], code, flush=True)
        return code

    with ThreadPoolExecutor(len(campaign['cases'])) as pool:
        codes = list(pool.map(one, campaign['cases']))
    assert all(c == 0 for c in codes), codes


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path); p.add_argument('--tmax', type=float, default=10.0)
    p.add_argument('--stage', choices=('prepare', 'build', 'run', 'all'), default='all')
    a = p.parse_args(); root = a.root.resolve()
    if a.stage in ('prepare', 'all'):
        prepare(root, a.tmax)
    if a.stage in ('build', 'all'):
        build(root, None)
    if a.stage in ('run', 'all'):
        run(root)
