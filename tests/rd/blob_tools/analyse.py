#!/usr/bin/env python3
"""Stream Blob HDF5 snapshots into cloud-mass/conservation CSV and JSON.

Accept a portable bundle root, or a directory containing snap_*.hdf5.
NumPy/h5py are required; --plot additionally uses Matplotlib. No AREPO imports.
"""
import argparse
import csv
import json
from pathlib import Path

import h5py
import numpy as np

TCR = 2*np.sqrt(10)/(1.5*4.1)


def state(path):
    with h5py.File(path) as f:
        g = f['PartType0']
        ids = g['ParticleIDs'][:]
        order = np.argsort(ids)
        assert len(np.unique(ids)) == len(ids), 'Duplicate particle IDs'
        mass, rho = g['Masses'][:][order], g['Density'][:][order]
        v, u = g['Velocities'][:][order], g['InternalEnergy'][:][order]
        pressure = g['Pressure'][:][order]
        assert all(np.isfinite(a).all() for a in (mass, rho, v, u, pressure))
        assert min(mass.min(), rho.min(), pressure.min()) > 0, path
        q = np.column_stack((mass, mass[:, None]*v,
                             mass*(u+.5*np.sum(v*v, axis=1))))
        x = g['Coordinates'][:][order]
        assert np.isfinite(x).all()
        return dict(time=float(f['Header'].attrs['Time']), ids=ids[order],
                    x=x, mass=mass, rho=rho, pressure=pressure, q=q,
                    dual=mass/rho, box=float(f['Header'].attrs['BoxSize']))


def analyse_case(folder, name, tcr, expected_end=None, returncode=None):
    paths = sorted(folder.glob('snap_*.hdf5'))
    if not paths:
        raise FileNotFoundError(f'No snap_*.hdf5 in {folder}')
    a = state(paths[0])
    assert a['time'] == 0, 'Initial snapshot is required'
    initial_total = a['q'].sum(axis=0)
    scale = np.abs(a['q']).sum(axis=0)
    scale[1:4] = np.maximum(scale[1:4], scale[0])
    rows = []
    initial_cloud_mass = None
    for path in paths:
        s = state(path)
        np.testing.assert_array_equal(s['ids'], a['ids'])
        np.testing.assert_array_equal(s['x'], a['x'])
        assert s['box'] == a['box']
        if rows:
            assert s['time'] > rows[-1]['time']
        conservation = float(np.max(np.abs(s['q'].sum(axis=0)-initial_total)/scale))
        coverage = abs(float(s['dual'].sum())/s['box']**3-1)
        assert conservation < 1e-12 and coverage < 1e-12, (path, conservation, coverage)
        selected = (s['rho'] > 64) & (s['pressure']/s['rho'] < 9)
        cloud_mass = float(s['mass'][selected].sum())
        if initial_cloud_mass is None:
            initial_cloud_mass = cloud_mass
            assert initial_cloud_mass > 0
        rows.append(dict(snapshot=path.name, time=s['time'], t_over_tcr=s['time']/tcr,
            cloud_mass=cloud_mass, cloud_mass_fraction=cloud_mass/initial_cloud_mass,
            rho_min=float(s['rho'].min()), pressure_min=float(s['pressure'].min()),
            conservation=conservation, coverage=coverage))
    end_matches = None if expected_end is None else abs(rows[-1]['time']-expected_end) < 1e-14
    if returncode == 0 and expected_end is not None:
        assert end_matches, f'{name}: successful solver status but missing endpoint'
    summary = dict(case=name, nodes=len(a['ids']), snapshots=len(rows),
        solver_returncode=returncode, solver_status=('completed' if returncode == 0 else
            'failed' if returncode is not None else 'unknown'),
        saved_snapshot_checks_passed=True, expected_end=expected_end,
        saved_end_matches_target=end_matches, end=rows[-1]['time'],
        end_t_over_tcr=rows[-1]['t_over_tcr'],
        initial_cloud_mass=initial_cloud_mass,
        cloud_mass_fraction=rows[-1]['cloud_mass_fraction'],
        conservation=max(r['conservation'] for r in rows),
        coverage=max(r['coverage'] for r in rows),
        final_rho_min=rows[-1]['rho_min'], final_pressure_min=rows[-1]['pressure_min'])
    return summary, rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--tcr', type=float, default=TCR)
    p.add_argument('--plot', action='store_true')
    a = p.parse_args()
    assert a.tcr > 0
    root = a.input.resolve()
    manifest = root/'bundle.json'
    if manifest.exists():
        bundle = json.loads(manifest.read_text())
        tcr = bundle['tcr']
        cases = [(c['name'], root/c['snapshots'], c['expected_end'], c['returncode'])
                 for c in bundle['cases']]
    else:
        tcr = a.tcr
        cases = [(root.name, root, None, None)]
    a.out.mkdir(parents=True, exist_ok=True)
    summaries, histories = [], {}
    for name, folder, end, code in cases:
        summary, rows = analyse_case(folder, name, tcr, end, code)
        output = a.out/f'{name}.csv'
        with output.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        summaries.append(summary)
        histories[name] = rows
        print(name, summary['solver_status'], len(rows), 'snapshots;',
              'end/t_cr=', summary['end_t_over_tcr'], flush=True)
    result = dict(tcr=tcr, norms='extensive mass/three momenta/energy; median-dual Masses/Density; momentum scale floor=total initial mass',
        cloud_selection='rho>64 and p/rho<9; no material tracer', cases=summaries)
    (a.out/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    if a.plot:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 4))
        for name, rows in histories.items():
            if len(rows) > 1:
                ax.plot([r['t_over_tcr'] for r in rows],
                        [r['cloud_mass_fraction'] for r in rows], label=name)
        ax.set(xlabel=r'$t/t_{cr}$', ylabel=r'$M_{cloud}/M_{cloud,0}$', ylim=(0, 1.05))
        ax.legend(frameon=False)
        fig.tight_layout()
        for ext in ('png', 'pdf'):
            fig.savefig(a.out/f'cloud_mass.{ext}', dpi=180)
        plt.close(fig)


if __name__ == '__main__':
    main()
