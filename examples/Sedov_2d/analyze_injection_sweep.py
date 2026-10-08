#!/usr/bin/env python3
"""Verify 1/7-node controls and compare completed moving profiles to 21 nodes."""
import argparse
import json
from pathlib import Path
import sys

import h5py
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import binned_statistic

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tests/rd'))
from run_n_gauss3_split import sha, write, state
from analyze import similarity
from analyze_topology_repair import audit


def main(root, baseline):
    out = root / 'analysis'; out.mkdir(exist_ok=True)
    cases = json.loads((root / 'campaign.json').read_text())['cases']
    area = np.load(root / 'inputs/median_dual_area.npy')
    checks = []
    for c in cases:
        with h5py.File(c['ic']) as f:
            u = f['PartType0/InternalEnergy'][:]
            v = f['PartType0/Velocities'][:, :2]
            xy = f['PartType0/Coordinates'][:, :2]
        s = state(sorted((root / 'runs' / c['name'] / 'output').glob('snap_*.hdf5'))[0])
        assert np.max(abs(s['w'] - area)) < 1e-12
        # AREPO initializes momentum=m*v, then recovers v=momentum/m.
        # Check that round trip exactly (uniform nonzero v differs by one ulp).
        expected_v = s['mass'][:, None] * v / s['mass'][:, None]
        assert np.array_equal(s['xy'], xy) and np.array_equal(s['v'], expected_v)
        expected = area @ (u + .5*np.sum(v*v, axis=1))
        assert abs(s['totals'][3] - expected) < 1e-11
        checks.append(dict(name=c['name'], expected_energy=float(expected),
                           native_initial_energy=float(s['totals'][3])))
    rows, histories = audit(root, 'Rusanov_moving')
    repair_rows, repair_histories = audit(root, 'Rusanov_moving_repair')
    base_rows, base_histories = audit(baseline, 'Rusanov_moving')
    reference = similarity(root, .05)
    complete, profile_metrics = {}, []
    for count, archive, candidates in ((1, root, rows), (7, root, rows), (21, baseline, base_rows)):
        result = next(r for r in candidates if r['group'] == f'nearest{count}')
        if not result['completed']:
            continue
        s = state(Path(result['snapshots'][-1]['path']))
        with h5py.File(archive / 'inputs' / f'sedov_nearest{count}.hdf5') as f:
            xy = f['PartType0/Coordinates'][:, :2]
            u = f['PartType0/InternalEnergy'][:]
        hot = u > 2e-6
        center = np.average(xy[hot], axis=0, weights=area[hot]*(u[hot]-1.5e-6))
        delta = (s['xy'] - center + .5) % 1 - .5
        radius = np.linalg.norm(delta, axis=1)
        vr = np.sum(delta * s['v'], axis=1) / np.maximum(radius, 1e-30)
        s.update(radius=radius, vr=vr, center=center)
        complete[count] = s
        exact_rho = np.interp(radius, reference['r'], reference['rho'], left=reference['rho'][0], right=1.)
        exact_p = np.interp(radius, reference['r'], reference['p'], left=reference['p'][0], right=1e-6)
        profile_metrics.append(dict(count=count, time=s['time'], radial_center=center.tolist(),
            rho_min=float(s['rho'].min()), rho_max=float(s['rho'].max()), p_min=float(s['p'].min()),
            density_area_L1=float(np.average(abs(s['rho']-exact_rho), weights=s['w'])),
            pressure_area_L1=float(np.average(abs(s['p']-exact_p), weights=s['w'])),
            shock_reference=float(reference['shock']),
            mass_relative=result['mass_relative'], energy_relative=result['energy_relative']))
    write(out / 'verification.json', dict(cases=rows+repair_rows, baseline=base_rows,
        initial_energy_checks=checks, profile_metrics=profile_metrics,
        plot_center='Initial excess-energy centroid for each seed; 1-node injection is not exactly at box center.',
        source_hashes={p.name:sha(p) for p in (Path(__file__), HERE/'analyze_topology_repair.py', HERE/'analyze.py')}))
    colors = {1:'#3d6fad', 7:'#bb6236', 21:'#489071'}
    plt.rcParams.update({'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False})
    if complete:
        fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.1), layout='constrained')
        bins = np.linspace(0, .45, 91); mids = (bins[1:]+bins[:-1])/2
        for count, s in complete.items():
            for ax, key, label in zip(axes, ('rho', 'vr', 'p'), ('$\\rho$', '$v_r$', '$p$')):
                ax.scatter(s['radius'], s[key], s=2, alpha=.04, color=colors[count], rasterized=True)
                means = binned_statistic(s['radius'], s[key], statistic='mean', bins=bins)[0]
                ax.plot(mids, means, color=colors[count], lw=1.5, label=f'{count} heated node'+('s' if count!=1 else ''))
                ax.set(xlim=(0,.4), xlabel='Radius from injection centroid', ylabel=label)
                ax.grid(alpha=.15)
        for ax, key, exterior in zip(axes, ('rho','vr','p'), (1.,0.,1e-6)):
            ax.plot(np.r_[reference['r'],reference['shock'],.45],np.r_[reference[key],exterior,exterior],
                    'k:',lw=1.4,label='2D Sedov')
        axes[0].legend(fontsize=8)
        fig.suptitle('Moving Sedov: Rusanov RD, glass $128^2$, $t=0.05$\nNo connectivity repair')
        fig.savefig(out / 'injection_profiles.png', dpi=350); plt.close(fig)
        fig, axes = plt.subplots(1,len(complete),figsize=(4.1*len(complete),4.5),layout='constrained',squeeze=False)
        for ax, (count,s) in zip(axes[0],complete.items()):
            im=ax.tripcolor(s['xy'][:,0],s['xy'][:,1],s['rho'],shading='gouraud',cmap='magma',vmin=0,vmax=4)
            ax.add_patch(plt.Circle(s['center'],reference['shock'],fill=False,color='cyan',lw=.8,ls='--'))
            ax.set(xlim=(.12,.88),ylim=(.12,.88),aspect='equal',xlabel='x',ylabel='y',title=f'{count} heated node'+('s' if count!=1 else ''))
        fig.colorbar(im,ax=axes[0].tolist(),label='$\\rho$',shrink=.85)
        fig.suptitle('Moving Rusanov RD, $t=0.05$; no connectivity repair\nDashed circle: 2D Sedov shock centered on injected energy')
        fig.savefig(out / 'injection_density.png', dpi=300); plt.close(fig)
    fig, axes=plt.subplots(1,2,figsize=(10,3.8),layout='constrained')
    for count in (1,7,21):
        h=(base_histories if count==21 else histories)[f'nearest{count}']
        for ax,k in zip(axes,(1,4)):
            ax.plot(h[:,0],100*(h[:,k]/h[0,k]-1),color=colors[count],label=f'{count} nodes, no repair')
            if count in (1,7):
                hr=repair_histories[f'nearest{count}']
                rr=next(r for r in repair_rows if r['group']==f'nearest{count}')
                suffix='' if rr['completed'] else ' (failed)'
                ax.plot(hr[:,0],100*(hr[:,k]/hr[0,k]-1),color=colors[count],ls=':',lw=2,label=f'{count} nodes, old repair'+suffix)
    for ax,label in zip(axes,('Mass change (%)','Energy change (%)')):
        ax.set(xlabel='Time',ylabel=label);ax.grid(alpha=.15)
    axes[0].legend(fontsize=7)
    fig.suptitle('Moving Rusanov Sedov: injection count and conservation')
    fig.savefig(out / 'injection_budgets.png', dpi=250);plt.close(fig)
    for row in rows+repair_rows:
        print({k:row[k] for k in ('name','completed','last_accepted_time','mass_relative','energy_relative','failed_repair_states')})
    print('PROFILE METRICS',profile_metrics)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',type=Path);p.add_argument('baseline',type=Path)
    a=p.parse_args();main(a.root.resolve(),a.baseline.resolve())
