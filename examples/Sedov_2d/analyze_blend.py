#!/usr/bin/env python3
"""Audit the static LDA/Rusanov experiment and produce local review figures."""
import argparse
import json
from pathlib import Path
import re
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
from run_n_gauss3_split import state,sha,write
from analyze_swift_default import center,radial,describe
from audit_reference_scales import dense_reference


def stage_rows(path):
    rows=[]
    for line in path.read_text().splitlines():
        if line.startswith('RD-LR '):
            rows.append({k:float(v) for k,v in re.findall(r'(\w+)=([-+.0-9eE]+)',line)})
    return rows


def main(root):
    out=root/'analysis';out.mkdir(exist_ok=False)
    shutil.copy2(__file__,out/Path(__file__).name)
    campaign=json.loads((root/'campaign.json').read_text())
    provenance=json.loads((root/'source_provenance.json').read_text())
    assert sha(root/'source.tar')==provenance['source_tar_sha256']
    audits={}; contact={}; cases={}; diagnostics={}
    for c in campaign['cases']:
        folder=root/'runs'/c['name']; artifact=root/'artifacts'/c['method']
        meta=json.loads((artifact/'provenance.json').read_text())
        assert sha(artifact/'Arepo')==meta['binary_sha256']
        assert sha(artifact/'Config.sh')==meta['config_sha256']
        assert sha(c['ic'])==c['ic_sha256'] and sha(folder/'param.txt')==c['param_sha256']
        status=json.loads((folder/'run_status.json').read_text());assert status['returncode']==0,(c['name'],status)
        paths=sorted((folder/'output').glob('snap_*.hdf5')); seq=[state(p) for p in paths]
        assert len(seq)==5 and seq[-1]['time']==c['end'],c['name']
        snapshots=[]; max_eos=0
        for p,s in zip(paths,seq):
            assert np.array_equal(s['id'],seq[0]['id']) and np.array_equal(s['xy'],seq[0]['xy'])
            assert all(np.all(np.isfinite(s[k])) for k in ('rho','p','v','mass','xy'))
            assert all(np.all(s[k]>0) for k in ('rho','p','mass'))
            with h5py.File(p) as f:
                order=np.argsort(f['PartType0/ParticleIDs'][:]); ei=f['PartType0/InternalEnergy'][:][order]
            eos=(5/3-1)*s['rho']*ei
            max_eos=max(max_eos,float(np.max(abs(eos-s['p'])/s['p'])))
            snapshots.append(dict(path=str(p),sha256=sha(p),time=s['time'],totals=s['totals'].tolist(),
                rho_min=float(s['rho'].min()),rho_max=float(s['rho'].max()),p_min=float(s['p'].min()),p_max=float(s['p'].max())))
        totals=np.array([s['totals'] for s in seq]); drift=np.max(abs(totals-totals[0]),axis=0)
        assert drift[0]<1e-10 and drift[3]<1e-10*max(1,totals[0,3])
        audit=dict(run=status,provenance=meta,snapshots=snapshots,max_eos_relative=max_eos,max_absolute_budget_drift=drift.tolist())
        k_initial=float(np.min(seq[0]['p']/seq[0]['rho']**(5/3)))
        k_final=seq[-1]['p']/seq[-1]['rho']**(5/3)
        audit['entropy_proxy']=dict(initial_min=k_initial,final_min=float(k_final.min()),
            final_min_ratio=float(k_final.min()/k_initial),
            nodes_below_initial_min=int(np.sum(k_final<k_initial*(1-1e-8))))
        rows=stage_rows(folder/'run.log')
        if c['method']!='LDA_reference':
            assert len(rows)>0 and all(r['rho_min']>0 and r['internal_min']>0 and r['CFL_max']<=1 for r in rows)
            audit['stages']=dict(count=len(rows),max_CFL=max(r['CFL_max'] for r in rows),
                min_internal=min(r['internal_min'] for r in rows),min_density=min(r['rho_min'] for r in rows),
                min_ell=min(r['ell_min'] for r in rows),mean_limited_fraction=np.mean([r['limited']/r['elements'] for r in rows]),
                max_budget_defect=max(r['budget_defect'] for r in rows),
                correction_weighted_accepted_fraction=sum(r['accepted_norm'] for r in rows)/max(1e-300,sum(r['correction_norm'] for r in rows)))
        if c['group']=='uniform':
            defect=max(float(np.max(abs(seq[-1][k]-seq[0][k]))) for k in ('rho','p','v'))
            assert defect<1e-12; audit['uniform_defect']=defect
        elif c['group'].startswith('contact'):
            s=seq[-1]; n=int(c['group'][7:]); exact=1+.2*np.sin(2*np.pi*(s['xy'].sum(axis=1)-(.37-.21)*s['time']))
            error=float(s['w']@abs(s['rho']-exact)/s['w'].sum())
            contact.setdefault(c['method'],{})[n]=dict(L1=error,state=s)
            audit['density_L1']=error
        else:
            cases[c['method']]=seq; diagnostics[c['method']]=rows
        audits[c['name']]=audit
    convergence={}
    for method,measurements in contact.items():
        nn=sorted(measurements); errors=[measurements[n]['L1'] for n in nn]
        convergence[method]=dict(n=nn,errors=errors,orders=(np.log2(np.array(errors[:-1])/errors[1:])).tolist())
    differences={}
    for n in (16,32,64):
        a=contact['LR_blend'][n]['state'];b=contact['LDA_reference'][n]['state']
        differences[n]=max(float(np.max(abs(a[k]-b[k]))) for k in ('rho','p','v'))
    exact=dense_reference()
    origin=center(root/'inputs/sedov_nearest21.hdf5',np.load(root/'inputs/median_dual_area.npy'))
    old=REPO.parent/'local_runs/sedov_positivity_20260929_v2'
    oldpaths=sorted((old/'runs/nearest21_Rusanov_static/output').glob('snap_*.hdf5'))
    oldmeta=json.loads((old/'artifacts/Rusanov_static/provenance.json').read_text())
    assert sha(old/'artifacts/Rusanov_static/Arepo')==oldmeta['binary_sha256']
    assert sha(old/'inputs/sedov_nearest21.hdf5')==sha(root/'inputs/sedov_nearest21.hdf5')
    cases['Rusanov_trap']=[state(p) for p in oldpaths]
    final={}; metrics={}
    for method,seq in cases.items():
        s=radial(seq[-1],origin); final[method]=s; metrics[method]=describe(s,seq[0],exact)
        mean,edges,_=binned_statistic(s['r'],s['rho'],statistic='mean',bins=np.arange(0,.4001,.005))
        metrics[method]['binned_density_peak']=float(np.nanmax(mean))
        metrics[method]['energy_drift']=float(s['totals'][3]/seq[0]['totals'][3]-1)
        metrics[method]['mass_drift']=float(s['totals'][0]/seq[0]['totals'][0]-1)
    styles=[('LR_blend','LDA + Rusanov (positivity)','#3275ac','-'),
            ('LR_low','Rusanov, common Gauss3','#d28a2e','--'),
            ('Rusanov_trap','Previous Rusanov, trapezoidal','#8a699c',':')]
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,3,figsize=(12.6,7),layout='constrained')
    for row,rmax in enumerate((.4,.15)):
        bins=np.arange(0,rmax+.0001,.005);mid=(bins[1:]+bins[:-1])/2
        for ax,field,label,exterior in zip(axes[row],('rho','vr','p'),('$\\rho$','$v_r$','$p$'),(1,0,1e-6)):
            for method,title,color,ls in styles:
                s=final[method];mask=s['r']<rmax
                ax.scatter(s['r'][mask],s[field][mask],s=2 if row==0 else 4,alpha=.035 if row==0 else .08,
                           color=color,rasterized=True)
                mean=binned_statistic(s['r'],s[field],statistic='mean',bins=bins)[0]
                ax.plot(mid,mean,color=color,ls=ls,lw=1.6,label=title)
            ax.plot(np.r_[exact['r'],exact['shock'],.45],np.r_[exact[field],exterior,exterior],'k--',lw=1.2,label='2D Sedov')
            values=np.concatenate([s[field][s['r']<rmax] for s in final.values()])
            lo=min(0,float(values.min())); hi=max(float(values.max()),float(np.max(exact[field][exact['r']<rmax])))
            pad=.05*(hi-lo); ax.set(xlim=(0,rmax),ylim=(lo-pad,hi+pad),xlabel='Radius',ylabel=label); ax.grid(alpha=.15)
    axes[0,0].legend(fontsize=8)
    fig.suptitle('Sedov blast, static glass $128^2$, 21 heated points, $\\gamma=5/3$, $t=0.05$\nLDA/Rusanov research prototype; lower row: core detail')
    fig.savefig(out/'lda_rusanov_profiles.png',dpi=300);fig.savefig(out/'lda_rusanov_profiles.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(12.3,3.6),layout='constrained')
    for method,title,color,ls in styles[:2]:
        seq=cases[method]; times=[s['time'] for s in seq]
        axes[0].plot(times,[s['totals'][3]/seq[0]['totals'][3]-1 for s in seq],color=color,ls=ls,marker='o',label=title)
    rows=diagnostics['LR_blend']
    for stage,ls in ((0,'-'),(1,'--')):
        rr=[r for r in rows if r['stage']==stage]
        axes[1].plot([r['time'] for r in rr],[100*r['limited']/r['elements'] for r in rr],ls=ls,label=f'RK stage {stage+1}')
        axes[2].plot([r['time'] for r in rr],[r['accepted_norm']/max(1e-300,r['correction_norm']) for r in rr],ls=ls,label=f'RK stage {stage+1}')
    for ax,label in zip(axes,('Relative energy change','Limited elements [%]','Accepted correction fraction')):
        ax.set(xlabel='Time',ylabel=label);ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.savefig(out/'lda_rusanov_diagnostics.png',dpi=240);plt.close(fig)
    result=dict(audits=audits,convergence=convergence,blend_vs_LDA_max_differences=differences,metrics=metrics,
                analysis_sha256=sha(__file__),
                reference=dict(origin=origin.tolist(),shock_radius=exact['shock']),
                previous_static_reference=dict(provenance=oldmeta,snapshots=[dict(path=str(p),sha256=sha(p)) for p in oldpaths]),
                limitations='Static single-rank positivity-only prototype; no oscillation control, remap, MPI or moving validation. Smooth test is advected contact, not Yee vortex.')
    write(out/'verification.json',result)
    print(json.dumps(dict(convergence=convergence,differences=differences,metrics=metrics),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    main(p.parse_args().root.resolve())
