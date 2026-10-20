#!/usr/bin/env python3
"""Export a small, relocatable Blob analysis bundle; preserve full originals."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

TOOLS = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def export(nroot, lroot, destination, scripts_only):
    originals = [nroot.resolve(), lroot.resolve()]
    destination = destination.resolve()
    if any(destination == p or p in destination.parents for p in originals):
        raise ValueError('Write a separate bundle outside the original archives')
    destination.mkdir(parents=True, exist_ok=False)
    origins = {}

    def copy(source, relative):
        target = destination/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        assert sha(target) == sha(source)
        origins[str(relative)] = str(source)

    for name in ('make_ic.py', 'analyse.py'):
        copy(TOOLS/name, Path('scripts')/name)
    copy(TOOLS/'README.md', Path('README.md'))
    copy(TOOLS/'requirements.txt', Path('requirements.txt'))
    cases = []
    campaigns = []
    for scheme, root in zip(('N', 'LDA'), originals):
        campaign = json.loads((root/'campaign.json').read_text())
        campaigns.append(dict(scheme=scheme, original_root=str(root),
                              source_tar_sha256=campaign['source_tar_sha256']))
        for name in ('campaign.json', 'source_provenance.json', 'full_submissions.json',
                     'gates_results.json', 'calibration_results.json'):
            copy(root/name, Path('provenance')/scheme/name)
        for stepping in ('equal', 'hier'):
            method = scheme+'_'+stepping
            case = next(c for c in campaign['cases'] if c['group'] == 'full' and c['method'] == method)
            folder = root/'runs'/case['name']
            label = method+'_np'+str(case['ranks'])
            relative = Path('cases')/label
            status = json.loads((folder/'run_status.json').read_text())
            for name in ('param.txt', 'run_status.json'):
                copy(folder/name, relative/name)
            if (folder/'analysis.json').exists():
                copy(folder/'analysis.json', relative/'native_analysis.json')
            copy(root/'configs'/f'{method}.sh', Path('configs')/f'{method}.sh')
            artifact = root/'artifacts'/method
            for name in ('Config.used', 'arepoconfig.h.used', 'manifest.txt',
                         'binary.sha256', 'binary.ldd.txt', 'provenance.json'):
                copy(artifact/name, relative/'provenance'/('build_'+name))
            for directory in (folder/'output').glob('provenance-*'):
                for source in directory.iterdir():
                    if source.is_file():
                        copy(source, relative/'provenance'/directory.name/source.name)
            failure = None
            if status['returncode']:
                log = next((folder/'output').glob('arepo-*.log'))
                last_sync = last_stage = None
                for line in log.open(errors='replace'):
                    if line.startswith('Sync-Point '):
                        last_sync = line.strip()
                    if line.startswith('RD-3D-STAGE') and 'stage=1' in line:
                        last_stage = line.strip()
                    if 'TERMINATE:' in line:
                        failure = dict(message=line.strip(), last_sync=last_sync,
                            last_reported_stage1=last_stage, original_log=str(log),
                            original_log_sha256=sha(log))
                assert failure, 'Keep unexplained failures visible rather than inventing a cause'
                (destination/relative/'failure.json').write_text(json.dumps(failure, indent=2)+'\n')
                if not scripts_only:
                    target = destination/relative/'native_failure.log.gz'
                    with log.open('rb') as inp, gzip.open(target, 'wb', compresslevel=6) as out:
                        shutil.copyfileobj(inp, out)
                    origins[str(relative/'native_failure.log.gz')] = str(log)
            snapshots = sorted((folder/'output').glob('snap_*.hdf5'))
            if not scripts_only:
                for path in snapshots:
                    copy(path, relative/'snapshots'/path.name)
            cases.append(dict(name=label, scheme=scheme, method=method, ranks=case['ranks'],
                source_job=status['slurm_job_id'], source_binary_sha256=status['binary_sha256'],
                snapshots=str(relative/'snapshots'), original_snapshots=len(snapshots),
                included_snapshots=0 if scripts_only else len(snapshots),
                expected_end=case['end'], returncode=status['returncode'],
                failure=failure, original_case=str(folder)))
    if not scripts_only:
        copy(originals[0]/'inputs/blob32.hdf5', Path('inputs/blob32.hdf5'))
    metadata = dict(format_version=1, kind='scripts_only' if scripts_only else 'data_and_scripts',
        tcr=campaign['tcr'], box=10., gamma=5/3, n=32, cloud_nodes=140,
        cloud_selection='rho>64 and p/rho<9; no material tracer',
        campaigns=campaigns, cases=cases,
        originals_preserved=True, snapshot_weights='Masses/Density; median-dual volume')
    (destination/'bundle.json').write_text(json.dumps(metadata, indent=2)+'\n')
    if scripts_only:
        with (destination/'README.md').open('a') as f:
            f.write('\nThis is the scripts-only package: snapshots and IC data are omitted.\n'
                    'Generate an IC with make_ic.py or supply a downloaded snapshot folder\n'
                    'to analyse.py. Running bundle-root analysis requires the data package.\n')
    else:
        command = [sys.executable, str(destination/'scripts/analyse.py'), str(destination),
                   '--out', str(destination/'analysis')]
        completed = subprocess.run(command, text=True, capture_output=True)
        if completed.returncode:
            raise RuntimeError(completed.stdout+completed.stderr)
        print(completed.stdout, end='')
    inventory = []
    for path in sorted(destination.rglob('*')):
        if path.is_file():
            relative = str(path.relative_to(destination))
            inventory.append(dict(path=relative, bytes=path.stat().st_size,
                sha256=sha(path), origin=origins.get(relative, 'bundle metadata/derived portable analysis')))
    (destination/'inventory.json').write_text(json.dumps(inventory, indent=2)+'\n')
    with (destination/'SHA256SUMS').open('w') as f:
        for path in sorted(destination.rglob('*')):
            if path.is_file() and path.name != 'SHA256SUMS':
                f.write(sha(path)+'  '+str(path.relative_to(destination))+'\n')
    archive = destination.with_name(destination.name+'.tar.gz')
    with archive.open('xb') as raw:
        with tarfile.open(fileobj=raw, mode='w:gz', compresslevel=6) as tar:
            tar.add(destination, arcname=destination.name, filter=lambda info:
                    None if '__pycache__' in Path(info.name).parts else info)
    checksum = sha(archive)
    archive.with_name(archive.name+'.sha256').write_text(checksum+'  '+archive.name+'\n')
    print(json.dumps(dict(bundle=str(destination), files=len(inventory)+2,
        unpacked_bytes=sum(p.stat().st_size for p in destination.rglob('*') if p.is_file()),
        archive=str(archive), archive_bytes=archive.stat().st_size, archive_sha256=checksum), indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--n-root', required=True, type=Path)
    p.add_argument('--lda-root', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--scripts-only', action='store_true')
    a = p.parse_args()
    export(a.n_root, a.lda_root, a.out, a.scripts_only)
