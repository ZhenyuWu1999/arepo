#!/usr/bin/env python3
"""Gate for the enforced frozen-vertex CFL ledger (Codex review R2, 2026-10-09).

HLLC-RD, interval hierarchy, natural bins, RD_FLIP_HIGH_MODE=1, Sedov 21-point
(archived IC), t = 0.005, one rank:
  default     RD_CFL_LEDGER_LIMIT = 1 (the sufficient positivity condition);
              must complete (Sedov ledger maxima so far 0.11-0.13).
  overrun     RD_CFL_LEDGER_LIMIT = 0.05; must TERMINATE with the frozen-vertex
              ledger message (controlled-overrun negative test of the check).
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
from run_n_gauss3_split import ENV, sha, write, rewrite, build   # noqa: E402
from run_hllc import freeze                                       # noqa: E402
import run_interval_hierarchy_gates as G                          # noqa: E402
from flip_campaign_checks import check_configs                    # noqa: E402

METHODS = {'default': [], 'overrun': ['RD_CFL_LEDGER_LIMIT=0.05']}
EXPECT = {'default': 'complete', 'overrun': 'frozen-vertex CFL ledger'}


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    freeze(root)
    for folder in ('configs', 'artifacts', 'runs', 'inputs'):
        (root / folder).mkdir()
    ic_src = G.INPUTS['sedov21']
    ref = {Path(c['ic']).name: c['ic_sha256'] for c in json.loads((G.SEDOV / 'campaign.json').read_text())['cases']}
    assert sha(ic_src) == ref[ic_src.name]
    ic = root / 'inputs' / ic_src.name
    shutil.copy2(ic_src, ic)
    texts = {m: G.config('HLLC', 'ih_natural', mode=1).rstrip('\n') + '\n' + ''.join(f'{f}\n' for f in extra)
             for m, extra in METHODS.items()}
    check_configs(texts)
    template = (G.SEDOV / 'runs/nearest21_HLLC_flip/param.txt').read_text()
    cases = []
    for m, text in texts.items():
        (root / 'configs' / f'{m}.sh').write_text(text)
        folder = root / 'runs' / m; folder.mkdir()
        param = rewrite(template, dict(InitCondFile=ic.with_suffix(''), OutputDir=str(folder / 'output') + '/',
                                       TimeMax=.005, TimeBetSnapshot=.00125, TimeBetStatistics=.00125, MaxSizeTimestep=.001))
        (folder / 'param.txt').write_text(param)
        cases.append(dict(name=m, method=m, expect=EXPECT[m], ic=str(ic), ic_sha256=sha(ic),
                          param_sha256=sha(folder / 'param.txt'), ranks=1))
    write(root / 'campaign.json', dict(test='cfl_ledger_enforcement', methods=list(METHODS), cases=cases, description=__doc__))
    shutil.copy2(__file__, root / Path(__file__).name)


def run(root):
    cases = json.loads((root / 'campaign.json').read_text())['cases']

    def one(c):
        folder = root / 'runs' / c['name']; artifact = root / 'artifacts' / c['method']
        meta = json.loads((artifact / 'provenance.json').read_text())
        assert sha(artifact / 'Arepo') == meta['binary_sha256'] and sha(folder / 'param.txt') == c['param_sha256']
        start = time.monotonic(); cmd = [str(artifact / 'Arepo'), 'param.txt']
        with (folder / 'run.log').open('w') as stream:
            code = subprocess.run(cmd, cwd=folder, env=ENV, stdout=stream, stderr=subprocess.STDOUT).returncode
        log = (folder / 'run.log').read_text()
        ok = (code == 0) if c['expect'] == 'complete' else (code != 0 and c['expect'] in log)
        write(folder / 'run_status.json', dict(name=c['name'], returncode=code, seconds=time.monotonic() - start,
                                               expected=c['expect'], gate_passed=ok, binary_sha256=meta['binary_sha256']))
        print('DONE', c['name'], code, 'gate_passed' if ok else 'GATE_FAILED', flush=True)
        return ok

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(one, cases))
    assert all(results), results


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('root', type=Path)
    a = p.parse_args(); root = a.root.resolve()
    prepare(root); build(root, None); run(root)
