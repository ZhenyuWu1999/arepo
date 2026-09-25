#!/usr/bin/env python3
"""Analyze native frame tests without conflating coordinate and boost comparisons."""
import argparse,json,re,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from run_n_gauss3_split import state,write,sha

def numbers(log,key):
    return [float(x) for x in re.findall(r'\b'+re.escape(key)+r'=([+\-\deE.]+)',log)]

def analyze(root,partial=False):
    campaign=json.loads((root/'campaign.json').read_text());rows=[];states={};series={}
    for c in campaign['cases']:
        d=root/'runs'/c['name']
        if not (d/'run_status.json').exists():
            assert partial, c['name'];continue
        status=json.loads((d/'run_status.json').read_text());log=(d/'run.log').read_text()
        ss=[state(p) for p in sorted((d/'output').glob('snap_*.hdf5'))];a,b=ss[0],ss[-1]
        assert all(np.array_equal(s['id'],a['id']) for s in ss)
        complete=status['returncode']==0 and 'bye!' in log
        if complete:assert abs(b['time']-c['end'])<1e-10
        sync=re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*([\deE.+-]+)',log)
        hist=[]
        for s in ss:
            xy=s['xy'].copy();xy[:,0]=(xy[:,0]-c['boost']*s['time'])%1
            dx=(xy[:,0]-.5+.5)%1-.5;dy=(xy[:,1]-.5+.5)%1-.5;r=np.hypot(dx,dy)
            v=s['v'].copy();v[:,0]-=c['boost'];vp=(-dy*v[:,0]+dx*v[:,1])/np.maximum(r,1e-100)
            exact=np.where(r<.2,5*r,np.where(r<.4,2-5*r,0));w=s['w']/s['w'].sum()
            hist.append(dict(time=s['time'],vphi_l1_area=float(w@abs(vp-exact)),vphi_l1_number=float(np.mean(abs(vp-exact))),vphi_peak=float(vp.max()),rho_min=float(s['rho'].min()),p_min=float(s['p'].min()),mass_relative_drift=float((s['totals'][0]-a['totals'][0])/a['totals'][0]),energy_relative_drift=float((s['totals'][3]-a['totals'][3])/a['totals'][3])))
        diag={}
        for key in ('min_pivot_ratio','cons_defect_abs','cons_defect_rel','svd_fallback','f1_lumped','max_phi_covariance_relative','max_correction_covariance'):
            ns=numbers(log,key)
            if ns:diag[key]=dict(first=ns[0],min=min(ns),max=max(ns),last=ns[-1])
        row=dict(**c,status=status,complete=complete,last_log_time=float(sync[-1][1]) if sync else None,steps=int(sync[-1][0]) if sync else None,history=hist,final=hist[-1],diagnostics=diag,failures=[x for x in log.splitlines() if any(t in x for t in ('TERMINATE:','RD assertion','very bad...','minimum timestep'))])
        if c['problem']=='uniform':
            row['uniform_changes']={k:float(np.max(abs(b[k]-a[k]))) for k in ('rho','v','p')};row['uniform_pass_absolute_1e_12']=max(row['uniform_changes'].values())<1e-12
        rows.append(row);states[c['name']]=b;series[c['name']]=ss
    by={x['name']:x for x in rows};pairs=[]
    def compare(n1,n2,boostdiff):
        if n1 not in states or n2 not in states:return
        if not (by[n1]['complete'] and by[n2]['complete']):return
        a,b=states[n1],states[n2];assert a['time']==b['time'];assert np.array_equal(a['id'],b['id'])
        stats={}
        for k in ('xy','v','rho','p','mass'):
            delta=b[k]-a[k]
            if k=='xy':delta[:,0]-=boostdiff*b['time'];delta=(delta+.5)%1-.5
            if k=='v':delta[:,0]-=boostdiff
            stats[k]=dict(mean_absolute=float(np.mean(abs(delta))),max_absolute=float(np.max(abs(delta))))
        pairs.append(dict(reference=n1,candidate=n2,boost_removed=boostdiff,time=a['time'],fields=stats))
    for horizon in ('short','long'):
      for scheme in ('N','LDA'):
        for frame in ('lab','comoving'):compare(f'{horizon}_{scheme}_{frame}_b0',f'{horizon}_{scheme}_{frame}_b10',10)
        for boost in (0,10):compare(f'{horizon}_{scheme}_lab_b{boost}',f'{horizon}_{scheme}_comoving_b{boost}',0)
    diagnostic=[]
    for boost in (0,10):
        name=f'diagnostic_LDA_lab_b{boost}'
        if name not in states:continue
        log=(root/'runs'/name/'run.log').read_text()
        vals=[]
        for line in log.splitlines():
            if line.startswith('RD-COND-SUMMARY'):
                vals.append({k:float(v) for k,v in re.findall(r'(\w+)=([+\-\deE.]+|inf)',line)})
        baseline=series[f'short_LDA_lab_b{boost}'];candidate=series[name];assert len(baseline)==len(candidate)
        gap=max(float(np.max(abs(a[k]-b[k]))) for a,b in zip(baseline,candidate) for k in ('xy','v','rho','p','mass'))
        diagnostic.append(dict(boost=boost,summary=vals,snapshot_max_difference_vs_plain=gap,near_tolerance_lines=[l for l in log.splitlines() if l.startswith('RD-COND task=')]))
    result=dict(cases=rows,pairs=pairs,conditioning=diagnostic,comparison_conventions='ID-matched, periodic coordinate differences, velocity x component deboosted. Pair L1 is mean absolute over particles and components. Profile L1 separately area weighted by m/rho. A2 defects from production frame diagnostics use different coordinate scales.',scope='Historical jitter48 seed/settings on current source. Not exact old-binary replay. Uniform N/lab absolute gate retained as failed if >1e-12; Gresho runs are diagnostic comparisons, not baseline acceptance.')
    write(root/('summary_partial.json' if partial else 'summary.json'),result)
    if partial:
        for x in rows:print(x['name'],x['complete'],x['final'])
        return
    figs=root/'figures';figs.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':10})
    fig,axes=plt.subplots(2,2,figsize=(11,8),sharex=True,sharey=True,layout='constrained')
    for i,scheme in enumerate(('N','LDA')):
      for j,frame in enumerate(('lab','comoving')):
        ax=axes[i,j]
        for boost,col in ((0,'#006c91'),(10,'#d75e1d')):
          name=f'long_{scheme}_{frame}_b{boost}'
          if name not in states or not by[name]['complete']:
            ax.text(.5,.5,name+' incomplete',transform=ax.transAxes);continue
          s=states[name];xy=s['xy'].copy();xy[:,0]=(xy[:,0]-boost*s['time'])%1;d=(xy-.5+.5)%1-.5;r=np.linalg.norm(d,axis=1);v=s['v'].copy();v[:,0]-=boost;vp=(-d[:,1]*v[:,0]+d[:,0]*v[:,1])/np.maximum(r,1e-100)
          ax.scatter(r,vp,s=3,alpha=.22,color=col,label=f'boost {boost}; L1={by[name]["final"]["vphi_l1_area"]:.4g}')
        rr=np.linspace(0,.7,500);ax.plot(rr,np.where(rr<.2,5*rr,np.where(rr<.4,2-5*rr,0)),'k--',lw=1,label='exact')
        ax.set(title=f'{scheme} / {"Roe split" if scheme=="N" else "Gauss3"} / {frame}',xlabel='Radius after undoing translation',ylabel='Azimuthal velocity',xlim=(0,.65));ax.legend(fontsize=8);ax.grid(alpha=.15)
    fig.suptitle('Moving Gresho at t=1: current source, jitter48², gamma=5/3, CFL=0.3')
    fig.savefig(figs/'gresho_profiles.png',dpi=170);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for row in rows:
      if row['horizon']!='long':continue
      hist=row['history'];label=f'{row["scheme"]} {row["frame"]} b{row["boost"]}';t=[x['time'] for x in hist]
      axes[0].plot(t,[x['vphi_l1_area'] for x in hist],label=label)
      axes[1].plot(t,[abs(x['mass_relative_drift']) for x in hist],label=label)
    axes[0].set(xlabel='Time',ylabel='Area-weighted azimuthal velocity L1');axes[1].set(xlabel='Time',ylabel='Absolute relative total-mass drift',yscale='symlog');axes[1].set_yscale('symlog',linthresh=1e-14);axes[0].legend(fontsize=7,ncol=2)
    for ax in axes:ax.grid(alpha=.2)
    fig.savefig(figs/'gresho_histories.png',dpi=170);plt.close(fig)
    for x in rows:
        if x['horizon']=='long':print(x['name'],x['complete'],x['final'])
    for x in pairs:
        if x['time']==.02:print(x['reference'],'->',x['candidate'],x['fields']['v'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--partial',action='store_true');a=p.parse_args();analyze(a.root.resolve(),a.partial)
