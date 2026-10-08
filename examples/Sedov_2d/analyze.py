#!/usr/bin/env python3
"""Audit native Sedov snapshots and plot against SWIFT's 2D similarity solution."""
import argparse
import ast
import json
from pathlib import Path
import re
import sys
import warnings

import h5py
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.special import gamma as Gamma
from scipy.stats import binned_statistic

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tests/rd'))
if (HERE / 'run_n_gauss3_split.py').exists():
    sys.path.insert(0, str(HERE))
from run_n_gauss3_split import sha, write, state


def similarity(root, t, energy=1.):
    # Load only the three analytic functions, without the SWIFT I/O/plot code.
    path = root / 'reference/plotSolution.py'
    tree = ast.parse(path.read_text())
    funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name in ('calc_a', 'calc_beta', 'sedov')]
    assert len(funcs) == 3
    namespace = dict(np.__dict__, Gamma=Gamma)
    exec(compile(ast.Module(body=funcs, type_ignores=[]), str(path), 'exec'), namespace)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        result = namespace['sedov'](t, energy, 1., 5/3, 20000, 2)
    r, p, rho, vr, shock, ps, rhos, vs, speed = result
    assert np.all(np.isfinite([r, p, rho, vr]))
    integral = np.trapezoid((p/(5/3-1) + .5*rho*vr**2)*2*np.pi*r, r)
    assert abs(integral/energy-1) < 1e-5
    assert abs(rhos-4) < 1e-12 and abs(speed - .5*shock/t) < 1e-12
    return dict(r=r, p=p, rho=rho, vr=vr, shock=shock, energy=integral, speed=speed)


def early_density(root):
    """Matched saved states before failure, explicitly not a completed result."""
    out = root / 'analysis/disk005'; out.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), layout='constrained')
    records = []
    for ax, mesh in zip(axes, ('static', 'moving')):
        folder = root / 'runs' / f'disk005_N_{mesh}_lab'
        states = [(p, state(p)) for p in sorted((folder / 'output').glob('snap_*.hdf5'))]
        path, s = min(states, key=lambda item: abs(item[1]['time']-.005))
        assert abs(s['time']-.005) < 1e-4
        im = ax.tripcolor(s['xy'][:,0], s['xy'][:,1], s['rho'], shading='gouraud',
                         cmap='magma', vmin=0, vmax=3)
        ax.add_patch(plt.Circle((.5,.5), .05, fill=False, color='cyan', lw=.9, ls='--'))
        ax.set(xlim=(.32,.68), ylim=(.32,.68), aspect='equal', xlabel='x', ylabel='y',
               title=mesh.capitalize()+' mesh')
        records.append(dict(file=str(path), sha256=sha(path), time=s['time']))
    assert records[0]['time'] == records[1]['time']
    fig.colorbar(im, ax=axes.tolist(), label=r'$\rho$', shrink=.8)
    fig.suptitle(f'Sedov pilot: N / RK2, glass $128^2$, t = {records[0]["time"]:.6f}\n'
                 'Early state before moving-mesh failure; dashed circle: injection radius')
    fig.savefig(out / 'early_density.png', dpi=300); plt.close(fig)
    write(out / 'early_density_inputs.json', records)


def analyze(root, group):
    campaign = json.loads((root / 'campaign.json').read_text())
    area = np.load(root / 'inputs/median_dual_area.npy')
    rows, completed = [], []
    for c in campaign['cases']:
        if c['group'] not in ('uniform', group):
            continue
        folder = root / 'runs' / c['name']
        status_path = folder / 'run_status.json'
        if not status_path.exists():
            continue
        meta = json.loads((root / 'artifacts' / c['method'] / 'provenance.json').read_text())
        assert sha(root / 'artifacts' / c['method'] / 'Arepo') == meta['binary_sha256']
        assert sha(c['ic']) == c['ic_sha256'] and sha(folder / 'param.txt') == c['param_sha256']
        status = json.loads(status_path.read_text())
        text = (folder / 'run.log').read_text(errors='replace')
        times = re.findall(r'Sync-Point\s+(\d+),.*?Time:\s*([0-9.eE+-]+),\s*Systemstep:\s*([0-9.eE+-]+)', text)
        failures = [line for line in text.splitlines() if re.search(r'TERMINATE|non-physical|invalid|Assertion|failed|BAD|very bad|mass=-', line)]
        snaps = sorted((folder / 'output').glob('snap_*.hdf5'))
        records = []; initial = None; final = None
        for snap in snaps:
            s = state(snap)
            finite = all(np.all(np.isfinite(s[k])) for k in ('xy', 'rho', 'p', 'v', 'mass'))
            positive = all(np.all(s[k] > 0) for k in ('rho', 'p', 'mass'))
            assert finite and positive, snap
            if initial is None:
                initial = s
                assert s['time'] == 0.
                assert np.max(abs(s['w']-area)) < 1e-12
                assert np.max(abs(s['rho']-1)) < 1e-12
                with h5py.File(c['ic']) as f:
                    u0 = f['PartType0/InternalEnergy'][:]
                    v0 = f['PartType0/Velocities'][:, :2]
                expected = area @ (u0+.5*np.sum(v0**2, axis=1))
                assert abs(s['totals'][3]-expected) < 1e-11
            final = s
            change = s['totals'] - initial['totals']
            displacement = (s['xy']-initial['xy']+.5) % 1 - .5
            if c['mesh'] == 'static':
                assert np.max(abs(displacement)) < 1e-12
            records.append(dict(file=str(snap), sha256=sha(snap), time=s['time'],
                min_rho=float(s['rho'].min()), min_p=float(s['p'].min()), max_rho=float(s['rho'].max()),
                mass_relative_drift=float(change[0]/initial['totals'][0]),
                energy_relative_drift=float(change[3]/initial['totals'][3]),
                momentum_change=change[1:3].tolist(),
                displacement_rms=float(np.sqrt(np.mean(np.sum(displacement**2, axis=1))))))
        ok = status['returncode'] == 0 and final is not None and abs(final['time']-c['end']) < 1e-12
        row = dict(c, status=status, completed=ok, snapshots=records, failure_lines=failures[-10:],
            last_step=int(times[-1][0]) if times else None,
            last_logged_time=float(times[-1][1]) if times else None,
            dt_min=min((float(v[2]) for v in times if float(v[2])>0), default=None),
            dt_max=max((float(v[2]) for v in times if float(v[2])>0), default=None))
        ratios = [float(x) for x in re.findall(r'rd_over_selected=([0-9.eE+-]+)', text)]
        row['min_midpoint_cfl_ratio'] = min(ratios) if ratios else None
        if c['group'] == 'uniform' and ok:
            row['uniform_defect'] = max(float(np.max(abs(final[k]-initial[k]))) for k in ('rho', 'p', 'v'))
            assert row['uniform_defect'] < 1e-12
        if c['group'] == group and ok:
            completed.append((c, final))
        rows.append(row)
    out = root / 'analysis' / group; out.mkdir(parents=True, exist_ok=True)
    analytic = similarity(root, .05)
    write(out / 'summary.json', dict(cases=rows, reference_2d_shock_radius=float(analytic['shock']),
        analytic_energy_integral=float(analytic['energy']),
        reference_note='2D cylindrical point-source similarity: R proportional to t^(1/2). Finite 21-node seed is not the same exact initial condition.'))
    for row in rows:
        print(row['name'], 'COMPLETE' if row['completed'] else 'FAILED',
              't=',row['last_logged_time'], 'steps=', row['last_step'], flush=True)
        if row['failure_lines']:
            print('\n'.join(row['failure_lines'][-2:]), flush=True)
    if not completed:
        return
    plt.rcParams.update({'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False})
    schemes = sorted(set(c['scheme'] for c, s in completed), key=lambda x: x != 'N')
    fig, axes = plt.subplots(3, len(schemes), figsize=(5.5*len(schemes),8), squeeze=False, sharex=True)
    bins = np.linspace(0,.45,91); mid = .5*(bins[:-1]+bins[1:])
    fields = [('rho', r'$\rho$'), ('vr', r'$v_r$'), ('p', r'$p$')]
    for column, scheme in enumerate(schemes):
        for c, s in completed:
            if c['scheme'] != scheme:
                continue
            delta = (s['xy']-.5+.5)%1-.5
            radius = np.linalg.norm(delta, axis=1)
            vr = np.sum(delta*s['v'],axis=1)/np.maximum(radius,1e-30)
            values = dict(rho=s['rho'],p=s['p'],vr=vr)
            color = '#2d78b7' if c['mesh']=='moving' else '#bf6a36'
            for row,(key,label) in enumerate(fields):
                ax=axes[row,column]; val=values[key]
                ax.scatter(radius,val,s=2,color=color,alpha=.10,rasterized=True)
                mean=binned_statistic(radius,val,statistic='mean',bins=bins)[0]
                ax.plot(mid,mean,color=color,lw=1.5,ls='--' if c['mesh']=='static' else '-',label=c['mesh']+' '+c.get('temporal','RK2'))
                ax.set_ylabel(label); ax.set_xlim(0,.45); ax.grid(alpha=.15)
        for row,(key,label) in enumerate(fields):
            ax=axes[row,column]
            exterior=dict(rho=1.,p=1e-6,vr=0.)[key]
            ax.plot(np.r_[analytic['r'],analytic['shock'],.45],np.r_[analytic[key],exterior,exterior],
                    color='black',ls=':',lw=1.5,label='2D Sedov')
        axes[0,column].set_title(scheme)
        axes[0,column].legend(fontsize=9)
        axes[2,column].set_xlabel('Radius')
    seed_label = r'$r_{\rm inj}=0.05$ (130 nodes)' if group == 'disk005' else '21-node injection'
    fig.suptitle(r'Sedov blast, glass $128^2$, $\gamma=5/3$, $t=0.05$'+'\n'+seed_label,fontsize=13)
    fig.tight_layout(rect=(0,0,1,.97))
    fig.savefig(out/'profiles.png',dpi=350);plt.close(fig)
    ncases=[(c,s) for c,s in completed if c['scheme']=='N']
    if ncases:
        fig,axs=plt.subplots(1,len(ncases),figsize=(5*len(ncases),4.7),squeeze=False,layout='constrained')
        for ax,(c,s) in zip(axs[0],ncases):
            image=ax.tripcolor(s['xy'][:,0],s['xy'][:,1],s['rho'],shading='gouraud',cmap='magma',vmin=0,vmax=4)
            ax.add_patch(plt.Circle((.5,.5),analytic['shock'],fill=False,color='cyan',ls='--',lw=.9))
            ax.set(xlim=(.1,.9),ylim=(.1,.9),xlabel='x',ylabel='y',title='N / '+c['mesh'],aspect='equal')
        fig.colorbar(image,ax=axs[0].tolist(),label=r'$\rho$',shrink=.85)
        fig.suptitle('Sedov blast, t = 0.05; dashed circle: 2D similarity radius')
        fig.savefig(out/'density.png',dpi=300);plt.close(fig)
    if group == 'disk005':
        early_density(root)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    parser.add_argument('--group',default='nearest21')
    args=parser.parse_args();analyze(args.root.resolve(),args.group)
