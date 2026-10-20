#!/usr/bin/env python3
"""Submit separate full Blob cases after successful native gates/calibration.

No solver executes here. Wall time is twice the same-method/rank short-run
projection plus 15 minutes, rounded up to five minutes. Refuse estimates above
the partition's three-day limit. Preserve partial submissions without duplicates.
"""
import argparse
import fcntl
import hashlib
import json
from math import ceil
from pathlib import Path
import subprocess


def submit(root):
    campaign = json.loads((root/'campaign.json').read_text())
    assert json.loads((root/'gates_results.json').read_text())['passed']
    calibration = json.loads((root/'calibration_results.json').read_text())
    assert calibration['passed']
    source_hash = hashlib.sha256((root/'source.tar').read_bytes()).hexdigest()
    assert source_hash == campaign['source_tar_sha256']
    runner = Path(campaign['runner_repo'])
    wrapper = root/'source/tests/rd/blob_cosma.sbatch'
    result_file = root/'full_submissions.json'
    with (root/'full_submission.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        results = json.loads(result_file.read_text()) if result_file.exists() else {}
        for case in (c for c in campaign['cases'] if c['group'] == 'full'):
            name = case['name']
            if name in results:
                print('ALREADY RECORDED', name, results[name], flush=True)
                continue
            short_name = name.replace('full_', 'calibration_', 1)
            short = next(row for row in calibration['runs'] if row['case'] == short_name)
            seconds = 300*ceil((2*short['projected_full_hours']*3600+900)/300)
            if seconds > 3*86400:
                results[name] = dict(submitted=False, required_wall_seconds=seconds,
                    reason='Conservative measured budget exceeds the dine2 three-day limit')
            else:
                hours, remainder = divmod(seconds, 3600)
                minutes = remainder//60
                wall = f'{hours:02d}:{minutes:02d}:00'
                command = ['sbatch', '--parsable', f'--job-name=Blob32{case["method"]}',
                    '--partition=dine2', '--account=do020', '--nodes=1',
                    f'--ntasks={case["ranks"]}', '--cpus-per-task=1', '--mem=16G',
                    f'--time={wall}', f'--output={root}/{name}-%j.log',
                    f'--export=ALL,AREPO_REPO_ROOT={runner}', str(wrapper), 'full', str(root), '--select', name]
                job = subprocess.check_output(command, cwd=runner, text=True).strip()
                results[name] = dict(submitted=True, job_id=job, wall_seconds=seconds,
                    calibration_seconds=short['seconds'],
                    projected_full_hours=short['projected_full_hours'], command=command)
            temporary = result_file.with_suffix('.tmp')
            temporary.write_text(json.dumps(results, indent=2)+'\n')
            temporary.replace(result_file)
            print(name, json.dumps(results[name]), flush=True)
    return all(row['submitted'] for row in results.values())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    raise SystemExit(0 if submit(args.root.resolve()) else 2)
