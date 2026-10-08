#!/usr/bin/env python3
"""Audit the stock SWIFT run and compare matching-time Sedov RD profiles."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import h5py
import numpy as np
from scipy.stats import binned_statistic
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(REPO/'tests/rd'))
from run_n_gauss3_split import state, sha, write
from audit_reference_scales import dense_reference, SWIFT

BASE=REPO.parent/'local_runs/sedov_positivity_20260929_v2'
SWEEP=REPO.parent/'local_runs/sedov_injection_sweep_20260929_v1'


def swift_state(path):
    with h5py.File(path) as f:
        g=f['PartType0']; order=np.argsort(g['ParticleIDs'][:])
        def data(key): return np.asarray(g[key][:][order],dtype=float)
        mass=data('Masses'); v=data('Velocities')[:,:2]; u=data('InternalEnergies')
        rho=data('Densities'); pressure=data('Pressures')
        assert all(np.all(np.isfinite(a)) for a in (mass,v,u,rho,pressure))
        assert min(mass.min(),u.min(),rho.min(),pressure.min())>0
        return dict(id=g['ParticleIDs'][:][order],xy=data('Coordinates')[:,:2],mass=mass,
            v=v,u=u,rho=rho,p=pressure,w=mass/rho,h=data('SmoothingLengths'),
            time=float(np.asarray(f['Header'].attrs['Time']).item()),
            totals=np.array([mass.sum(),np.sum(mass*v[:,0]),np.sum(mass*v[:,1]),np.sum(mass*(u+.5*np.sum(v*v,axis=1)))]))


def center(ic, mass):
    with h5py.File(ic) as f:
        g=f['PartType0'];xy=g['Coordinates'][:,:2];u=g['InternalEnergy'][:]
    hot=u>2e-6
    return np.average(xy[hot],axis=0,weights=mass[hot]*(u[hot]-1.5e-6))


def radial(s, origin):
    d=(s['xy']-origin+.5)%1-.5
    s['r']=np.linalg.norm(d,axis=1)
    s['vr']=np.sum(d*s['v'],axis=1)/np.maximum(s['r'],1e-30)
    s['center']=origin
    return s


def describe(s, initial, exact):
    rows=[]
    for lo,hi in ((0,.05),(.05,.1),(.1,.15)):
        take=(s['r']>=lo)&(s['r']<hi)
        rows.append(dict(lo=lo,hi=hi,count=int(take.sum()),
            **{k:float(s[k][take].mean()) if take.any() else None for k in ('rho','p','vr')},
            **{k+'_analytic':float(np.interp(s['r'][take],exact['r'],exact[k]).mean()) if take.any() else None for k in ('rho','p','vr')}))
    return dict(time=s['time'],center=s['center'].tolist(),density_min=float(s['rho'].min()),
        density_max=float(s['rho'].max()),pressure_min=float(s['p'].min()),pressure_max=float(s['p'].max()),
        mass_relative=float(s['totals'][0]/initial['totals'][0]-1),
        energy_relative=float(s['totals'][3]/initial['totals'][3]-1),
        final_totals=s['totals'].tolist(),counts_inside={str(r):int((s['r']<r).sum()) for r in (.05,.1,.15)},
        annuli=rows)


def main(root):
    out=root/'analysis';out.mkdir(exist_ok=False)
    for script in (__file__,HERE/'audit_reference_scales.py'):
        shutil.copy2(script,out/Path(script).name)
    meta=json.loads((root/'artifact/provenance.json').read_text())
    assert sha(root/'artifact/swift')==meta['binary_sha256']
    assert sha(root/'artifact/config.h')==meta['config_sha256']
    assert sha(root/'source.tar')==meta['source_sha256']
    assert sha(root/'run/plotSolution.py')==sha(SWIFT/'plotSolution.py')
    assert json.loads((root/'run/run_status.json').read_text())['returncode']==0
    inputs=json.loads((root/'run/inputs.json').read_text())
    for name,digest in inputs.items(): assert sha(root/'run'/name)==digest
    paths=sorted((root/'run').glob('sedov_[0-9][0-9][0-9][0-9].hdf5'))
    assert len(paths)==6
    states=[swift_state(p) for p in paths]
    assert np.allclose([s['time'] for s in states],np.arange(6)*.01,rtol=0,atol=1e-14)
    assert all(np.array_equal(s['id'],states[0]['id']) for s in states)
    assert all(np.array_equal(s['mass'],states[0]['mass']) for s in states)
    with h5py.File(root/'run/sedov.hdf5') as f:
        mass=np.asarray(f['PartType0/Masses'][:],dtype=float)
        ic_u=np.asarray(f['PartType0/InternalEnergy'][:],dtype=float)
    ic_energy=float(np.sum(mass*ic_u))
    origin=center(root/'run/sedov.hdf5',mass)
    exact=dense_reference()
    complete={'SWIFT_21':radial(states[-1],origin)}
    initial={'SWIFT_21':states[0]}
    histories={'SWIFT_21':[(s['time'],s['totals'][0],s['totals'][3]) for s in states]}
    snapshot_audit=[dict(path=str(p),sha256=sha(p),time=s['time'],rho_min=float(s['rho'].min()),
        u_min=float(s['u'].min()),p_min=float(s['p'].min()),totals=s['totals'].tolist()) for p,s in zip(paths,states)]
    rd_provenance={}
    for count,archive in ((21,BASE),(1,SWEEP)):
        method='Rusanov_moving'; artifact=archive/'artifacts'/method
        provenance=json.loads((artifact/'provenance.json').read_text())
        assert sha(artifact/'Arepo')==provenance['binary_sha256']
        assert sha(artifact/'Config.sh')==provenance['config_sha256']
        run=archive/'runs'/f'nearest{count}_{method}'
        assert json.loads((run/'run_status.json').read_text())['returncode']==0
        snapshots=sorted((run/'output').glob('snap_*.hdf5'));seq=[state(p) for p in snapshots]
        assert seq[-1]['time']==.05
        key=f'RD_{count}';initial[key]=seq[0]
        origin=center(archive/'inputs'/f'sedov_nearest{count}.hdf5',np.load(archive/'inputs/median_dual_area.npy'))
        complete[key]=radial(seq[-1],origin)
        histories[key]=[(s['time'],s['totals'][0],s['totals'][3]) for s in seq]
        rd_provenance[key]=dict(binary_sha256=provenance['binary_sha256'],
            snapshots={str(p):sha(p) for p in snapshots})
    rows={key:describe(s,initial[key],exact) for key,s in complete.items()}
    energy_baselines={key:float(initial[key]['totals'][3]) for key in complete}
    energy_baselines['SWIFT_21']=ic_energy
    for key in rows:
        rows[key]['energy_relative_to_ic']=float(complete[key]['totals'][3]/energy_baselines[key]-1)
    with h5py.File(paths[-1]) as f:
        hydro={key:np.asarray(value).tolist() for key,value in f['HydroScheme'].attrs.items()}
    def safe(value):
        if isinstance(value,bytes): return value.decode()
        if isinstance(value,dict): return {k:safe(v) for k,v in value.items()}
        if isinstance(value,list): return [safe(v) for v in value]
        return value
    stats=np.loadtxt(root/'run/statistics.txt')
    estat=stats[:,13]+stats[:,14]
    statistics=dict(first_time=float(stats[0,1]),last_time=float(stats[-1,1]),
        energy_relative=float(estat[-1]/estat[0]-1),mass_relative=float(stats[-1,4]/stats[0,4]-1),
        energy_relative_to_ic=float(estat[-1]/ic_energy-1),
        initial_snapshot_energy_relative_to_ic=float(states[0]['totals'][3]/ic_energy-1),
        initial_snapshot_max_abs_velocity=float(np.max(abs(states[0]['v']))),
        max_abs_energy_relative=float(np.max(abs(estat/estat[0]-1))))
    write(out/'verification.json',dict(profiles=rows,snapshots=snapshot_audit,hydro_scheme=safe(hydro),
        statistics=statistics,ic_energy=ic_energy,swift_provenance=meta,
        rd_provenance=rd_provenance,analysis_sha256=sha(__file__),
        analytic_energy_integral=exact['integrated_energy'],shock_radius=exact['shock'],
        limits='Saved states checked, not every internal SWIFT stage. Nodal means are unweighted; SPH density is a kernel estimate. Each radius uses its initial energy centroid.'))
    styles=[('SWIFT_21','SWIFT SPHENIX, 21 particles','#278c6a','-'),
            ('RD_21','Moving RD, 21 nodes','#cf7c29','--'),('RD_1','Moving RD, 1 node','#426eae','-.')]
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,3,figsize=(12.5,7),layout='constrained')
    for row,rmax in enumerate((.4,.15)):
        bins=np.arange(0,rmax+.0001,.005);mid=(bins[1:]+bins[:-1])/2
        for ax,field,label,ext in zip(axes[row],('rho','vr','p'),('$\\rho$','$v_r$','$p$'),(1.,0.,1e-6)):
            for key,title,color,ls in styles:
                s=complete[key];take=s['r']<rmax
                ax.scatter(s['r'][take],s[field][take],s=3 if row==0 else 8,alpha=.06 if row==0 else .25,color=color,rasterized=True)
                means=binned_statistic(s['r'],s[field],statistic='mean',bins=bins)[0]
                ax.plot(mid,means,color=color,ls=ls,lw=1.6,label=title)
            ax.plot(np.r_[exact['r'],exact['shock'],.45],np.r_[exact[field],ext,ext],'k:',lw=1.5,label='2D Sedov')
            ax.set(xlim=(0,rmax),xlabel='Radius from injection centroid',ylabel=label);ax.grid(alpha=.15)
    axes[0,0].legend(fontsize=8)
    axes[0,0].set_ylim(0,4.8);axes[0,1].set_ylim(-.5,2.8);axes[0,2].set_ylim(-.2,6.5)
    axes[1,0].set_ylim(0,.5);axes[1,1].set_ylim(-.5,1.4);axes[1,2].set_ylim(.7,3.5)
    fig.suptitle('Sedov blast, glass $128^2$, $t=0.05$\nSWIFT default example; moving Rusanov RD without connectivity repair')
    fig.savefig(out/'swift_rd_profiles.png',dpi=300);fig.savefig(out/'swift_rd_profiles.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,3.6),layout='constrained')
    for key,title,color,ls in styles:
        history=np.asarray(histories[key]);time=history[:,0]
        for ax,col in zip(axes,(1,2)):
            baseline=history[0,col] if col==1 else energy_baselines[key]
            ax.plot(time,100*(history[:,col]/baseline-1),marker='o',ms=3,color=color,ls=ls,label=title)
    axes[1].plot(stats[:,1],100*(estat/ic_energy-1),color=styles[0][2],alpha=.45,lw=1,label='SWIFT statistics')
    for ax,label in zip(axes,('Mass change [%]','Energy change [%]')):
        ax.set(xlabel='Time',ylabel=label,xlim=(0,.05));ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    fig.suptitle('Budgets relative to input ICs; SWIFT time-zero output includes a velocity kick/extrapolation')
    fig.savefig(out/'swift_rd_budgets.png',dpi=300);plt.close(fig)
    print(json.dumps(dict(profiles=rows,hydro_scheme=safe(hydro),statistics=statistics),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
    main(parser.parse_args().root.resolve())
