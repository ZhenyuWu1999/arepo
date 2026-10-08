#!/usr/bin/env python3
"""Read-only audit of Sedov core sampling, similarity reference and 2D scales."""
import argparse
import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys
import warnings

import h5py
import numpy as np
from scipy.special import gamma as Gamma
from scipy.stats import binned_statistic
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tests/rd'))
from run_n_gauss3_split import state, sha, write
from analyze import similarity

BASE = REPO.parent / 'local_runs/sedov_positivity_20260929_v2'
SWEEP = REPO.parent / 'local_runs/sedov_injection_sweep_20260929_v1'
SWIFT = Path('/Users/zhenyuwu/SWIFT/examples/HydroTests/SedovBlast_2D')
MORTON = Path('/Users/zhenyuwu/Desktop/PhD/rdsolver_Ben/rdsolver')
REV = 'ba336488cc1b2d0c8301d05e230694c72a6c3272'


def dense_reference(t=.05, energy=1.):
    """Same SWIFT formula; sample the similarity variable densely near its limit.

    A linear grid leaves the original first nonzero radius at .0345. No hydro
    values or archived plots are changed by this reference-only refinement.
    """
    path = SWIFT / 'plotSolution.py'
    tree = ast.parse(path.read_text())
    funcs = [x for x in tree.body if isinstance(x, ast.FunctionDef)
             and x.name in ('calc_a', 'calc_beta', 'sedov')]
    for f in funcs:
        if f.name != 'sedov': continue
        for i, node in enumerate(f.body):
            if isinstance(node, ast.Assign) and any(isinstance(v, ast.Name) and v.id == 'v' for v in node.targets):
                f.body[i] = ast.parse('v = concatenate(([v_min], unique(v_min + geomspace(8*finfo(float).eps, v_max-v_min, n-1))))').body[0]
    ns = dict(np.__dict__, Gamma=Gamma)
    exec(compile(ast.fix_missing_locations(ast.Module(body=funcs, type_ignores=[])), str(path), 'exec'), ns)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        r, p, rho, vr, shock, ps, rhos, vs, speed = ns['sedov'](t, energy, 1., 5/3, 50000, 2)
    assert np.all(np.isfinite([r, p, rho, vr]))
    integral = np.trapezoid((p/(2/3)+.5*rho*vr**2)*2*np.pi*r, r)
    assert abs(integral/energy-1) < 1e-6
    assert abs(rhos-4) < 1e-12 and abs(speed-.5*shock/t) < 1e-12
    return dict(r=r, p=p, rho=rho, vr=vr, shock=float(shock), integrated_energy=float(integral))


def main(root):
    root.mkdir(parents=True, exist_ok=False)
    (root/'reference').mkdir()
    shutil.copy2(__file__, root/'audit_reference_scales.py')
    for name in ('makeIC.py', 'sedov.yml', 'plotSolution.py'):
        shutil.copy2(SWIFT/name, root/'reference'/('SWIFT_'+name))
    for name in ('main.cpp', 'setup2D.cpp', 'constants.h.TEMPLATE'):
        content = subprocess.check_output(['git','show',f'{REV}:rd/{name}'], cwd=MORTON)
        (root/'reference'/('Morton_'+name)).write_bytes(content)
    exact = dense_reference()
    old = similarity(BASE, .05)
    assert abs(exact['shock']/old['shock']-1) < 1e-6
    table, plots = [], {}
    for count, mesh, archive in ((1,'moving',SWEEP),(7,'moving',SWEEP),(21,'moving',BASE),(21,'static',BASE)):
        key = f'{mesh}_{count}'
        method = f'Rusanov_{mesh}'
        artifact = archive/'artifacts'/method
        provenance = json.loads((artifact/'provenance.json').read_text())
        assert sha(artifact/'Arepo') == provenance['binary_sha256']
        assert sha(artifact/'Config.sh') == provenance['config_sha256']
        science = archive/'runs'/f'nearest{count}_{method}'
        status = json.loads((science/'run_status.json').read_text())
        assert status['returncode'] == 0
        path = science/'output/snap_004.hdf5'
        s = state(path)
        assert s['time'] == .05
        with h5py.File(archive/'inputs'/f'sedov_nearest{count}.hdf5') as f:
            xy = f['PartType0/Coordinates'][:,:2]; u = f['PartType0/InternalEnergy'][:]
        area = np.load(archive/'inputs/median_dual_area.npy')
        hot = u > 2e-6
        center = np.average(xy[hot], weights=area[hot]*(u[hot]-1.5e-6), axis=0)
        d = (s['xy']-center+.5)%1-.5
        r = np.linalg.norm(d, axis=1)
        vr = np.sum(d*s['v'], axis=1)/np.maximum(r,1e-30)
        rows = []
        for lo,hi in ((0,.05),(.05,.1),(.1,.15)):
            take = (r >= lo) & (r < hi)
            row = dict(lo=lo, hi=hi, count=int(take.sum()))
            for field, values in (('rho',s['rho']),('vr',vr),('p',s['p'])):
                row[field] = float(values[take].mean())
                row[field+'_exact_at_nodes'] = float(np.interp(r[take],exact['r'],exact[field]).mean())
            row['mean_sqrt_dual_area'] = float(np.sqrt(s['w'][take]).mean())
            rows.append(row)
        table.append(dict(case=key, snapshot=str(path), snapshot_sha256=sha(path),
            radius_min=float(r.min()), center=center.tolist(), annuli=rows,
            counts_inside={str(bound):int((r<bound).sum()) for bound in (.025,.05,.1,.15)},
            final_mass=float(s['totals'][0]), final_energy=float(s['totals'][3])))
        plots[key] = dict(r=r, rho=s['rho'], p=s['p'], vr=vr)
    # 2D: velocity scale sqrt(E/(rho L^2)); time scale L^2 sqrt(rho/E).
    L, E, rho, pbg, tm = 10., 3e5, 1., 100., .01
    scales = dict(morton_length=L, morton_hot_energy=E, morton_background_pressure=pbg,
        length_unit=L, time_unit=L**2*np.sqrt(rho/E), velocity_unit=np.sqrt(E/rho)/L,
        pressure_unit=E/L**2, morton_time_in_unit_box=tm*np.sqrt(E/rho)/L**2,
        morton_pressure_in_unit_box=pbg*L**2/E, morton_radius_in_unit_box=.25/L,
        our_time_in_morton_units=.05*L**2*np.sqrt(rho/E),
        our_pressure_in_morton_units=1e-6*E/L**2)
    energy_ratio = 1-.02576317487988644
    corrected = dense_reference(energy=energy_ratio)
    reference = dict(shock=exact['shock'], integrated_energy=exact['integrated_energy'],
        original_first_nonzero_radius=float(old['r'][1]),
        dense_first_nonzero_radius=float(exact['r'][1]),
        shock_change_relative=exact['shock']/old['shock']-1,
        energy_only_shock_ratio=corrected['shock']/exact['shock'],
        energy_only_center_pressure_ratio=corrected['p'][0]/exact['p'][0],
        values=[dict(r=rad, **{k:float(np.interp(rad,exact['r'],exact[k])) for k in ('rho','vr','p')})
                for rad in (0.,.025,.05,.1,.15)])
    write(root/'audit.json',dict(cases=table, scales=scales, reference=reference,
        source_hashes={p.name:sha(p) for p in (root/'reference').iterdir()},
        inspector_sha256=sha(Path(__file__)), morton_revision=REV,
        limit='Read-only diagnostic, no new native run. Diffusion and depleted core sampling are supported explanations, not a unique causal decomposition of pressure/velocity errors.'))
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig, axes = plt.subplots(2,2,figsize=(10,7),layout='constrained')
    bins = np.linspace(0,.16,33);mid=(bins[1:]+bins[:-1])/2
    styles=[('moving_1','Moving, 1 hot node','#3d6fad','-'),('moving_21','Moving, 21 hot nodes','#489071','-'),
            ('static_21','Static, 21 hot nodes','#bb6236','--')]
    for key,label,color,ls in styles:
        s=plots[key]
        for ax,field,ylabel in ((axes[0,0],'rho','$\\rho$'),(axes[0,1],'p','$p$'),(axes[1,0],'vr','$v_r$')):
            take=s['r']<.16
            ax.scatter(s['r'][take],s[field][take],s=8,alpha=.14,color=color)
            means=binned_statistic(s['r'],s[field],statistic='mean',bins=bins)[0]
            ax.plot(mid,means,color=color,ls=ls,lw=1.5,label=label)
            ax.set(xlim=(0,.16),xlabel='Radius',ylabel=ylabel);ax.grid(alpha=.15)
    for ax,field in ((axes[0,0],'rho'),(axes[0,1],'p'),(axes[1,0],'vr')):
        ax.plot(exact['r'],exact[field],'k:',lw=1.5,label='2D Sedov')
    axes[0,0].set_ylim(0,.55);axes[0,1].set_ylim(1.35,2.05);axes[1,0].set_ylim(0,1.2)
    axes[0,0].legend(fontsize=8)
    for key,label,color,ls in styles:
        edges=np.array([0,.05,.1,.15]);counts=np.histogram(plots[key]['r'],edges)[0]
        axes[1,1].plot((edges[1:]+edges[:-1])/2,counts,marker='o',color=color,ls=ls,label=label)
    axes[1,1].set(yscale='log',xlabel='Radial shell center (width 0.05)',ylabel='Number of nodes')
    axes[1,1].grid(alpha=.15);axes[1,1].legend(fontsize=8)
    fig.suptitle('Sedov core audit, $t=0.05$: Rusanov RD\nMoving cases have no connectivity repair; same original 21-node IC for static/moving')
    fig.savefig(root/'core_sampling.png',dpi=300);plt.close(fig)
    print(json.dumps(dict(scales=scales,reference=reference,cases=table),indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
    main(parser.parse_args().root.resolve())
