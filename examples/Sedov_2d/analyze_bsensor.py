#!/usr/bin/env python3
"""Verify and compare the RD B/Bmax transplant with archived positive/low controls."""
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
from analyze_blend import stage_rows
from analyze_swift_default import radial,describe
from audit_reference_scales import dense_reference


def scatter(s,lo=.05,hi=.1):
    take=(s['r']>=lo)&(s['r']<hi)
    r,w,v=s['r'][take],s['w'][take],s['vr'][take]
    residual=np.zeros(len(r));bins=np.floor((r-lo)/.005).astype(int)
    for b in np.unique(bins):
        m=bins==b;assert m.sum()>=3
        x=np.column_stack((np.ones(m.sum()),r[m]-r[m].mean()))
        coeff=np.linalg.lstsq(x*np.sqrt(w[m,None]),v[m]*np.sqrt(w[m]),rcond=None)[0]
        residual[m]=v[m]-x@coeff
    d=s['xy'][take]-s['center'];er=d/r[:,None]
    vt=er[:,0]*s['v'][take,1]-er[:,1]*s['v'][take,0]
    return dict(n=int(take.sum()),vr_mean=float(np.average(v,weights=w)),
        vr_detrended_rms=float(np.sqrt(np.average(residual**2,weights=w))),
        vt_rms=float(np.sqrt(np.average(vt**2,weights=w))))


def main(root):
    out=root/'analysis';out.mkdir(exist_ok=False)
    shutil.copy2(__file__,out/Path(__file__).name)
    campaign=json.loads((root/'campaign.json').read_text())
    provenance=json.loads((root/'source_provenance.json').read_text())
    assert sha(root/'source.tar')==provenance['source_tar_sha256']
    audits={};contacts={};final={};seqs={}
    for case in campaign['cases']:
        folder=root/'runs'/case['name'];art=root/'artifacts'/case['method']
        meta=json.loads((art/'provenance.json').read_text())
        assert sha(art/'Arepo')==meta['binary_sha256']
        assert sha(art/'Config.sh')==meta['config_sha256']
        assert sha(case['ic'])==case['ic_sha256'] and sha(folder/'param.txt')==case['param_sha256']
        status=json.loads((folder/'run_status.json').read_text());assert status['returncode']==0,status
        paths=sorted((folder/'output').glob('snap_*.hdf5'));states=[state(p) for p in paths]
        assert len(states)==5 and states[-1]['time']==case['end']
        records=[]
        for path,s in zip(paths,states):
            assert np.array_equal(s['id'],states[0]['id']) and np.array_equal(s['xy'],states[0]['xy'])
            assert all(np.all(np.isfinite(s[k])) for k in ('rho','p','mass','v'))
            assert all(np.all(s[k]>0) for k in ('rho','p','mass'))
            with h5py.File(path) as f:
                order=np.argsort(f['PartType0/ParticleIDs'][:]);ei=f['PartType0/InternalEnergy'][:][order]
            assert np.max(abs((5/3-1)*s['rho']*ei-s['p'])/s['p'])<1e-12
            k=s['p']/s['rho']**(5/3)
            records.append(dict(path=str(path),sha256=sha(path),time=s['time'],
                rho_min=float(s['rho'].min()),p_min=float(s['p'].min()),K_min=float(k.min()),totals=s['totals'].tolist()))
        totals=np.array([s['totals'] for s in states]);drift=np.max(abs(totals-totals[0]),axis=0)
        assert max(drift)<1e-10*max(1,abs(totals[0]).max())
        rows=stage_rows(folder/'run.log')
        assert rows and all(r['rho_min']>0 and r['internal_min']>0 and r['CFL_max']<=1 for r in rows)
        audit=dict(provenance=meta,status=status,snapshots=records,budget_max_absolute=drift.tolist(),
            stages=len(rows),max_CFL=max(r['CFL_max'] for r in rows),
            mean_limited_fraction=float(np.mean([r['limited']/r['elements'] for r in rows])))
        sensors=[]
        for line in (folder/'run.log').read_text().splitlines():
            if line.startswith('RD-LR-B '):
                sensors.append({k:float(v) for k,v in re.findall(r'(\w+)=([-+.0-9eE]+)',line)})
        assert len(sensors)==len(rows)
        audit['sensor_stage_means']={str(stage):{k:float(np.mean([r[k] for r in sensors if r['stage']==stage]))
            for k in ('theta_rho','theta_mx','theta_my','theta_E')} for stage in (0,1)}
        if case['group']=='uniform':
            defect=max(float(np.max(abs(states[-1][k]-states[0][k]))) for k in ('rho','p','v'))
            assert defect<1e-12;audit['uniform_defect']=defect
        elif case['group'].startswith('contact'):
            s=states[-1];n=int(case['group'][7:]);exact=1+.2*np.sin(2*np.pi*(s['xy'].sum(axis=1)-(.37-.21)*s['time']))
            error=float(np.average(abs(s['rho']-exact),weights=s['w']))
            contacts.setdefault(case['method'],{})[n]=error;audit['density_L1']=error
        else:
            seqs[case['method']]=states
        audits[case['name']]=audit
    old=REPO.parent/'local_runs/sedov_lda_rusanov_20260929_v1'
    previous=json.loads((old/'analysis/verification.json').read_text())
    for method in ('LR_blend','LR_low'):
        records=previous['audits']['nearest21_'+method]['snapshots']
        for r in records: assert sha(r['path'])==r['sha256']
        seqs[method]=[state(r['path']) for r in records]
    exact=dense_reference();origin=np.array(previous['reference']['origin'])
    metrics={}
    for method,seq in seqs.items():
        s=radial(seq[-1],origin);s['center']=origin;final[method]=s
        ref=seqs['LR_low'][-1]
        assert np.array_equal(s['id'],ref['id']) and np.array_equal(s['xy'],ref['xy'])
        assert np.max(abs(s['w']-ref['w']))<1e-15
        m=describe(s,seq[0],exact)
        mean=binned_statistic(s['r'],s['rho'],statistic='mean',bins=np.arange(0,.4001,.005))[0]
        k=s['p']/s['rho']**(5/3);k0=float(np.min(seq[0]['p']/seq[0]['rho']**(5/3)))
        m.update(mean_rho_peak=float(np.nanmax(mean)),scatter=scatter(s),
            K_min=float(k.min()),K_min_ratio=float(k.min()/k0),K_violations=int(np.sum(k<k0*(1-1e-8))),
            energy_drift=float(s['totals'][3]/seq[0]['totals'][3]-1))
        metrics[method]=m
    convergence={method:dict(n=sorted(values),L1=[values[n] for n in sorted(values)],
        orders=np.log2(np.array([values[n] for n in sorted(values)[:-1]])/
                       np.array([values[n] for n in sorted(values)[1:]])).tolist())
        for method,values in contacts.items()}
    styles=[('LR_blend','Positivity only','#3977ad',':'),('LR_B','RD B sensor','#29936c','-'),
            ('LR_Bmax','RD Bmax sensor','#b45671','-.'),('LR_low','Rusanov','#c48c31','--')]
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,3,figsize=(12.6,7),layout='constrained')
    for row,rmax in enumerate((.4,.15)):
        bins=np.arange(0,rmax+.0001,.005);mid=(bins[1:]+bins[:-1])/2
        for ax,key,label,exterior in zip(axes[row],('rho','vr','p'),('$\\rho$','$v_r$','$p$'),(1,0,1e-6)):
            for method,title,color,ls in styles:
                s=final[method];mask=s['r']<rmax
                ax.scatter(s['r'][mask],s[key][mask],s=2 if row==0 else 4,alpha=.035 if row==0 else .08,
                           color=color,rasterized=True)
                avg=binned_statistic(s['r'],s[key],statistic='mean',bins=bins)[0]
                ax.plot(mid,avg,color=color,ls=ls,lw=1.5,label=title)
            ax.plot(np.r_[exact['r'],exact['shock'],.45],np.r_[exact[key],exterior,exterior],'k--',lw=1.1,label='2D Sedov')
            values=np.concatenate([s[key][s['r']<rmax] for s in final.values()])
            lo=min(0,float(values.min()));hi=max(float(values.max()),float(np.max(exact[key][exact['r']<rmax])))
            pad=.05*(hi-lo);ax.set(xlim=(0,rmax),ylim=(lo-pad,hi+pad),xlabel='Radius',ylabel=label);ax.grid(alpha=.15)
    axes[0,0].legend(fontsize=8)
    fig.suptitle('Sedov blast, static glass $128^2$, 21 heated points, $\\gamma=5/3$, $t=0.05$\nRD residual-ratio sensors with LDA/Rusanov; lower row: core detail')
    fig.savefig(out/'rd_bsensor_profiles.png',dpi=300);fig.savefig(out/'rd_bsensor_profiles.pdf');plt.close(fig)
    result=dict(audits=audits,metrics=metrics,convergence=convergence,origin=origin.tolist(),
        analysis_sha256=sha(__file__),baseline_verification_sha256=sha(old/'analysis/verification.json'),
        limitations='B/Bmax sensor transplant; common-Gauss Rusanov replaces N. No characteristic projection or entropy constraint. Static only.')
    write(out/'verification.json',result)
    print(json.dumps(dict(metrics=metrics,convergence=convergence),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    main(p.parse_args().root.resolve())
