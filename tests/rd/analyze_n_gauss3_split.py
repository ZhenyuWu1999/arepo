#!/usr/bin/env python3
"""Analyze the matched current-source campaign, retaining all failed endpoints."""
import argparse
import json
from pathlib import Path
import re
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri

from run_n_gauss3_split import state, write, sha

def analyze(root):
    sys.path.insert(0, str(root / 'source/examples/shocktube_1d'))
    from Riemann import RiemannProblem
    def exact(x,t):
        return RiemannProblem(x.copy(),.5,np.array([1.,0.,1.]),np.array([.125,0.,.1]),1.4,t)[1]
    cases = json.loads((root / 'campaign.json').read_text())['cases']
    rows=[]; data={}; firsts={}
    for c in cases:
        folder=root/'runs'/c['name']
        status=json.loads((folder/'run_status.json').read_text())
        log=(folder/'run.log').read_text()
        sync=re.findall(r'Sync-Point\s+(\d+),(?:\s+TimeBin=\d+,)?\s+Time:\s*([\deE+.-]+),\s+Systemstep:\s*([\deE+.-]+)',log)
        series=[state(p) for p in sorted((folder/'output').glob('snap_*.hdf5'))]
        assert series, c['name']
        a=series[0]; firsts[c['name']]=a
        hist=[]
        for s in series:
            assert np.array_equal(s['id'],a['id'])
            assert all(np.all(np.isfinite(s[k])) for k in ('rho','v','p','mass'))
            delta=s['totals']-a['totals']
            hist.append(dict(time=s['time'],rho_min=float(s['rho'].min()),rho_max=float(s['rho'].max()),
                p_min=float(s['p'].min()),p_max=float(s['p'].max()),mass_min=float(s['mass'].min()),
                relative_mass_drift=float(abs(delta[0])/a['totals'][0]),
                relative_energy_drift=float(abs(delta[3])/abs(a['totals'][3])),
                kinetic_y=float(.5*np.sum(s['mass']*s['v'][:,1]**2))))
        fail=[l for l in log.splitlines() if any(x in l for x in ('very bad...','TERMINATE:','RD assertion A2 failed','invalid element:','invalid geometry:','invalid divisor:'))]
        rd=[l for l in log.splitlines() if l.startswith(('RD-RK2 time=','RD-ALE-FINISH time=','RD-ALE-PREP time='))]
        row=dict(**c,status=status,complete=status['returncode']==0 and 'bye!' in log,
                 last_log_time=float(sync[-1][1]) if sync else None,
                 steps=int(sync[-1][0]) if sync else None, failure_lines=fail,
                 final_diagnostics=rd[-3:],history=hist,last_saved=hist[-1],snapshots=len(series),
                 max_saved_mass_drift=max(h['relative_mass_drift'] for h in hist),
                 max_saved_energy_drift=max(h['relative_energy_drift'] for h in hist))
        if row['complete']:
            assert abs(hist[-1]['time']-c['end'])<1e-10
            assert min(h['rho_min'] for h in hist)>0 and min(h['p_min'] for h in hist)>0
        if c['problem']=='uniform':
            row['uniform_max_change']=max(float(np.max(abs(series[-1][k]-a[k]))) for k in ('rho','p','v'))
            assert row['complete'] and row['uniform_max_change']<1e-12
        if c['problem']=='sod' and row['complete']:
            s=series[-1];sel=(s['xy'][:,0]>.25)&(s['xy'][:,0]<.75)
            w=s['w'][sel];w=w/w.sum();ex=exact(s['xy'][sel,0],s['time'])
            row.update(rho_l1=float(w@abs(s['rho'][sel]-ex[:,0])),vx_l1=float(w@abs(s['v'][sel,0]-ex[:,1])),
                       p_l1=float(w@abs(s['p'][sel]-ex[:,2])),vx_min=float(s['v'][sel,0].min()),vx_max=float(s['v'][sel,0].max()))
            x=2*(s['xy'][:,0]-.25);sel=(x>=.70)&(x<=.76)
            w=s['w'][sel];w=w/w.sum();v=s['v'][sel,0]
            row['plateau_std_vx']=float(np.sqrt(w@((v-w@v)**2)))
        rows.append(row);data[c['name']]=series
    for problem in ('uniform','sod','kh'):
        names=[c['name'] for c in cases if c['problem']==problem]
        a=firsts[names[0]]
        for name in names[1:]:
            for k in ('id','xy','rho','p','v','w'):
                assert np.array_equal(a[k],firsts[name][k]),(problem,name,k)
    # The archived-binary replay must reproduce the same failure and saved states.
    old=root.parent/'legacy_split_20260912/runs/smooth_split_frame'
    replay=root/'legacy_replay';text=(replay/'run.log').read_text()
    historic=dict(status=json.loads((replay/'run_status.json').read_text()),
        failure_lines=[l for l in text.splitlines() if 'very bad...' in l or 'TERMINATE:' in l],
        expected_failure_time=.800476,expected_particle_id=923)
    assert 'ID=923 mass=-1.06377e-05' in text
    assert 'Time: 0.800476,' in text
    defects=[]
    for p in sorted((replay/'output').glob('snap_*.hdf5')):
        a,b=state(p),state(old/'output'/p.name)
        assert np.array_equal(a['id'],b['id'])
        defects.append(max(float(np.max(abs(a[k]-b[k]))) for k in ('xy','rho','v','p','mass')))
    historic['max_saved_state_difference']=max(defects)
    write(root/'summary.json',dict(cases=rows,historical_replay=historic,matched_initial_states=True,
        norm='Sod median-dual area normalized over raw x in (.25,.75), plateau xi=2(x-.25) in [.70,.76]',
        time='Raw box time t=.08 corresponds to tube-normalized tau=.16; KH unit box t10.',
        limits='Saved-state positivity and completion are not an accuracy or positivity proof; failures are not filled forward.'))
    figs=root/'figures';figs.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    combos=[('N','roe_split'),('N','gauss3'),('LDA','roe_split'),('LDA','gauss3')]
    labels=['N / Roe split','N / Gauss3','LDA / Roe split','LDA / Gauss3']
    colors=['#a6611a','#018571','#c51b7d','#2166ac']
    lookup={r['name']:r for r in rows}
    fig,axes=plt.subplots(3,4,figsize=(14,8),sharex=True,sharey='row',layout='constrained')
    for j,((scheme,res),label,color) in enumerate(zip(combos,labels,colors)):
        name=f'sod_{scheme}_{res}_sod';r=lookup[name]
        axes[0,j].set_title(label)
        if not r['complete']:
            for ax in axes[:,j]:ax.text(.5,.5,f"Stopped at t={r['last_log_time']}",transform=ax.transAxes,ha='center')
            continue
        s=data[name][-1];x=s['xy'][:,0];sel=(x>.25)&(x<.75)
        exx=np.linspace(.25,.75,1000);ex=exact(exx,s['time'])
        for i,(q,val) in enumerate([('rho',s['rho']),('vx',s['v'][:,0]),('p',s['p'])]):
            ax=axes[i,j];ax.scatter(2*(x[sel]-.25),val[sel],s=2,alpha=.25,color=color,edgecolors='none')
            ax.plot(2*(exx-.25),ex[:,i],'k--',lw=1.1);ax.grid(alpha=.15)
            ax.set_xlim(0,1)
            if j==0:ax.set_ylabel(q)
        axes[2,j].set_xlabel(r'$\xi=2(x-0.25)$')
    fig.suptitle('Current moving Sod: effective initial Nx=64, t=0.08 (tube time 0.16)\nDots: all nodes; dashed: exact. Same initial conditions and mesh settings.')
    fig.savefig(figs/'sod_profiles.png',dpi=170);plt.close(fig)
    targets=[.8,2.,5.,10.]
    fig,axes=plt.subplots(4,4,figsize=(12,11),layout='constrained')
    artist=None
    for i,((scheme,res),label) in enumerate(zip(combos,labels)):
        name=f'kh_{scheme}_{res}_kh';r=lookup[name]
        for j,t in enumerate(targets):
            ax=axes[i,j];ax.set(xlim=(0,1),ylim=(0,1),aspect='equal',xticks=[],yticks=[])
            if j==0:ax.set_ylabel(label)
            if i==0:ax.set_title(f't={t:g}')
            matches=[s for s in data[name] if abs(s['time']-t)<.01]
            if matches:
                s=min(matches,key=lambda a:abs(a['time']-t));xy=s['xy']
                tri=mtri.Triangulation(xy[:,0],xy[:,1])
                artist=ax.tripcolor(tri,s['rho'],shading='gouraud',cmap='viridis',vmin=.75,vmax=2.25)
                ax.text(.02,.02,f"actual t={s['time']:.4g}\nrho {s['rho'].min():.3f}--{s['rho'].max():.3f}",transform=ax.transAxes,
                    color='white',fontsize=7,bbox=dict(facecolor='black',alpha=.45,pad=1))
            else:
                ax.text(.5,.5,f"Stopped at t={r['last_log_time']:.5g}",transform=ax.transAxes,ha='center',color='#a22')
    if artist is not None:fig.colorbar(artist,ax=axes,shrink=.55,label='Density (fixed scale)')
    fig.suptitle('Current moving smooth KH: glass48², gamma=1.4, CFL=0.3\nSame Arpaia geometry and mesh settings; N/lumped vs LDA/F1.')
    fig.savefig(figs/'kh_evolution.png',dpi=170,bbox_inches='tight',pad_inches=.12);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(13,4),layout='constrained')
    for (scheme,res),label,color in zip(combos,labels,colors):
        r=lookup[f'kh_{scheme}_{res}_kh'];h=r['history'];t=[x['time'] for x in h]
        for ax,key in zip(axes,('rho_min','relative_mass_drift','relative_energy_drift')):
            y=np.array([x[key] for x in h]);ax.plot(t,y,label=label,color=color)
            ax.set(xlabel='Time',ylabel=key);ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    for ax in axes[1:]:ax.set_yscale('symlog',linthresh=1e-15)
    fig.suptitle('Saved-state diagnostics; failed curves stop at their last valid snapshot')
    fig.savefig(figs/'kh_diagnostics.png',dpi=170);plt.close(fig)
    for r in rows:
        if r['problem']!='uniform':
            print(json.dumps({k:r.get(k) for k in ('name','complete','last_log_time','rho_l1','plateau_std_vx','last_saved','failure_lines')}))
    print('Historical replay max saved-state difference:',historic['max_saved_state_difference'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    analyze(p.parse_args().root.resolve())
