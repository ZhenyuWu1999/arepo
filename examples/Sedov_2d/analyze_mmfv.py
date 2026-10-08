#!/usr/bin/env python3
"""Compare identical-seed MMFV, moving/static Rusanov RD and stock SWIFT."""
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
from run_n_gauss3_split import state,sha,write
from analyze_swift_default import swift_state,center,radial,describe
from audit_reference_scales import dense_reference

RD=REPO.parent/'local_runs/sedov_positivity_20260929_v2'
SPH=REPO.parent/'local_runs/swift_sedov_default_20260929_v1'


def fv_state(path):
    s=state(path)
    with h5py.File(path) as f:
        g=f['PartType0'];order=np.argsort(g['ParticleIDs'][:])
        s['generator']=s['xy'].copy()
        s['xy']=g['CenterOfMass'][:][order,:2]%1
        s['u']=g['InternalEnergy'][:][order]
    return s


def verify_native(archive,method,folder,loader):
    artifact=archive/'artifacts'/method
    meta=json.loads((artifact/'provenance.json').read_text())
    for name,key in (('Arepo','binary_sha256'),('Config.sh','config_sha256')):
        assert sha(artifact/name)==meta[key]
    assert json.loads((folder/'run_status.json').read_text())['returncode']==0
    paths=sorted((folder/'output').glob('snap_*.hdf5'));states=[loader(p) for p in paths]
    assert len(states)==5 and states[-1]['time']==.05
    audit=[]
    for p,s in zip(paths,states):
        assert np.array_equal(s['id'],states[0]['id'])
        assert all(np.all(np.isfinite(s[k])) for k in ('rho','p','v','mass','xy'))
        assert all(np.all(s[k]>0) for k in ('rho','p','mass'))
        if 'static' in method:assert np.array_equal(s['xy'],states[0]['xy'])
        audit.append(dict(path=str(p),sha256=sha(p),time=s['time'],totals=s['totals'].tolist(),
            rho_min=float(s['rho'].min()),rho_max=float(s['rho'].max()),p_min=float(s['p'].min())))
    return states,dict(provenance=meta,snapshots=audit)


def main(root):
    out=root/'analysis';out.mkdir(exist_ok=False)
    for path in (__file__,HERE/'analyze_swift_default.py',HERE/'audit_reference_scales.py'):
        shutil.copy2(path,out/Path(path).name)
    exact=dense_reference();cases={};history={};metadata={};origins={}
    fv,metadata['MMFV']=verify_native(root,'MMFV_moving',root/'runs/nearest21',fv_state)
    campaign=json.loads((root/'campaign.json').read_text())
    for c in campaign['cases']:
        assert sha(c['ic'])==c['ic_sha256']
        assert sha(root/'runs'/c['group']/'param.txt')==c['param_sha256']
    source=json.loads((root/'source_provenance.json').read_text())
    assert sha(root/'source.tar')==source['source_tar_sha256']
    assert abs(fv[0]['totals'][3]-campaign['initial_energy'])<1e-11
    hot=fv[0]['u']>2e-6
    origins['MMFV']=np.average(fv[0]['xy'][hot],axis=0,weights=fv[0]['mass'][hot]*(fv[0]['u'][hot]-1.5e-6))
    cases['MMFV']=fv
    for key,mesh in (('RD_moving','moving'),('RD_static','static')):
        method='Rusanov_'+mesh
        seq,metadata[key]=verify_native(RD,method,RD/'runs'/f'nearest21_{method}',state)
        cases[key]=seq
        origins[key]=center(RD/'inputs/sedov_nearest21.hdf5',np.load(RD/'inputs/median_dual_area.npy'))
    sphmeta=json.loads((SPH/'analysis/verification.json').read_text())
    assert sha(SPH/'artifact/swift')==sphmeta['swift_provenance']['binary_sha256']
    seq=[]
    for row in sphmeta['snapshots']:
        assert sha(row['path'])==row['sha256']
        seq.append(swift_state(Path(row['path'])))
    cases['SWIFT']=seq
    origins['SWIFT']=np.array(sphmeta['profiles']['SWIFT_21']['center'])
    metadata['SWIFT']=dict(verification_path=str(SPH/'analysis/verification.json'),
                          verification_sha256=sha(SPH/'analysis/verification.json'))
    final={};metrics={}
    for key,seq in cases.items():
        s=radial(seq[-1],origins[key]);final[key]=s
        metrics[key]=describe(s,seq[0],exact)
        baseline=sphmeta['ic_energy'] if key=='SWIFT' else seq[0]['totals'][3]
        metrics[key]['energy_relative_to_ic']=float(s['totals'][3]/baseline-1)
        metrics[key]['energy_ic_baseline']=float(baseline)
        history[key]=np.array([[a['time'],a['totals'][0],a['totals'][3]] for a in seq])
        means,edges,_=binned_statistic(s['r'],s['rho'],statistic='mean',bins=np.arange(0,.4001,.005))
        j=int(np.nanargmax(means));metrics[key]['binned_density_peak']=float(means[j])
        metrics[key]['binned_peak_radius']=float((edges[j]+edges[j+1])/2)
    write(out/'verification.json',dict(metrics=metrics,metadata=metadata,
        method='MMFV uses cell-centroid sample locations and initial energy centroid; RD uses nodes; SPH uses particles.',
        source_provenance=source,uniform_defect=campaign['uniform_defect'],
        analytic_shock_radius=exact['shock'],analysis_sha256=sha(__file__),
        limits='All cases nearest21; finite heated supports differ with discretization. Scalar Rusanov RD is low spatial order; SPH uses individual steps, FV/RD use equal adaptive steps. Saved-state positivity only for FV/SPH.'))
    styles=[('MMFV','AREPO MMFV','#376db1','-'),('RD_moving','Moving Rusanov RD','#d1812d','--'),
            ('RD_static','Static Rusanov RD','#9855a5','-.'),('SWIFT','SWIFT SPHENIX','#369779',':')]
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,3,figsize=(12.8,7.1),layout='constrained')
    for row,rmax in enumerate((.4,.15)):
        bins=np.arange(0,rmax+.0001,.005);mid=(bins[1:]+bins[:-1])/2
        for ax,field,label,exterior in zip(axes[row],('rho','vr','p'),('$\\rho$','$v_r$','$p$'),(1.,0.,1e-6)):
            for key,title,color,ls in styles:
                s=final[key];take=s['r']<rmax
                ax.scatter(s['r'][take],s[field][take],s=2 if row==0 else 7,
                           alpha=.035 if row==0 else .15,color=color,rasterized=True)
                mean=binned_statistic(s['r'],s[field],statistic='mean',bins=bins)[0]
                ax.plot(mid,mean,color=color,ls=ls,lw=1.6,label=title)
            ax.plot(np.r_[exact['r'],exact['shock'],.45],np.r_[exact[field],exterior,exterior],
                    'k--',lw=1.3,label='2D Sedov')
            values=np.concatenate([s[field][s['r']<rmax] for s in final.values()])
            lo=min(0.,float(values.min()));hi=max(float(values.max()),float(np.max(exact[field][exact['r']<rmax])))
            pad=(hi-lo)*.06
            ax.set(xlim=(0,rmax),ylim=(lo-pad,hi+pad),xlabel='Radius from injection centroid',ylabel=label)
            ax.grid(alpha=.15)
    axes[0,0].legend(fontsize=8)
    fig.suptitle('Sedov blast, glass $128^2$, 21 heated points, $t=0.05$\nMoving / static RD and moving finite volume; lower row: core detail')
    fig.savefig(out/'mmfv_rd_swift_profiles.png',dpi=300);fig.savefig(out/'mmfv_rd_swift_profiles.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,3.6),layout='constrained')
    for key,title,color,ls in styles:
        a=history[key]
        for ax,col in zip(axes,(1,2)):
            base=a[0,col] if col==1 else metrics[key]['energy_ic_baseline']
            ax.plot(a[:,0],100*(a[:,col]/base-1),color=color,ls=ls,marker='o',ms=3,label=title)
    for ax,label in zip(axes,('Mass change [%]','Energy change [%]')):
        ax.set(xlim=(0,.05),xlabel='Time',ylabel=label);ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    fig.suptitle('Budgets relative to input ICs; all cases use 21 heated points')
    fig.savefig(out/'mmfv_rd_swift_budgets.png',dpi=300);plt.close(fig)
    print(json.dumps(metrics,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    main(p.parse_args().root.resolve())
