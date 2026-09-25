#!/usr/bin/env python3
"""Yee analytic error at moved coordinates, with provenance and frame comparison."""
import argparse,json,re
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator
from run_n_gauss3_split import state,sha,write

def analyze(root,partial=False):
    campaign=json.loads((root/'campaign.json').read_text());rows=[];states={}
    for c in campaign['cases']:
        folder=root/'runs'/c['name']
        if not (folder/'run_status.json').exists():
            assert partial,c['name']
            continue
        status=json.loads((folder/'run_status.json').read_text())
        artifact=root/'artifacts'/c['method'];meta=json.loads((artifact/'provenance.json').read_text())
        assert sha(artifact/'Arepo')==status['binary_sha256']==meta['binary_sha256']
        assert sha(artifact/'Config.sh')==meta['config_sha256']
        assert meta['source_tar_sha256']==campaign['source_tar_sha256']
        assert sha(c['ic'])==c['ic_sha256'] and sha(folder/'param.txt')==c['param_sha256']
        ss=[state(p) for p in sorted((folder/'output').glob('snap_*.hdf5'))];a,b=ss[0],ss[-1]
        log=(folder/'run.log').read_text();sync=re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*([\deE.+-]+)',log)
        complete=status['returncode']==0 and 'bye!' in log and abs(b['time']-1)<1e-12
        row=dict(**c,status=status,complete=complete,last_time=b['time'],
                 steps=int(sync[-1][0]) if sync else None,rho_min=min(s['rho'].min().item() for s in ss),
                 pressure_min=min(s['p'].min().item() for s in ss),mass_relative_drift=float((b['mass'].sum()-a['mass'].sum())/a['mass'].sum()),
                 failures=[line for line in log.splitlines() if any(t in line for t in ('TERMINATE:','RD assertion','very bad...','minimum timestep'))])
        if complete:
            assert all(np.array_equal(a['id'],s['id']) for s in ss)
            assert row['rho_min']>0 and row['pressure_min']>0
            xy=(b['xy']-np.array([5+c['boost']*b['time'],5])+5)%10-5
            r2=np.sum(xy*xy,axis=1);temperature=1-.4*25/(8*np.pi**2*1.4)*np.exp(1-r2)
            rho=temperature**2.5;factor=2.5/np.pi*np.exp(.5*(1-r2))
            velocity=np.column_stack((c['boost']-xy[:,1]*factor,xy[:,0]*factor))
            w=b['w']/b['w'].sum()
            row.update(rho_l1=float(w@abs(b['rho']-rho)),velocity_l1=float(w@np.linalg.norm(b['v']-velocity,axis=1)),
                       particles=len(b['rho']),area_sum=float(b['w'].sum()))
            states[c['name']]=(a,b)
        rows.append(row)
    pairs=[];by={r['name']:r for r in rows};orders=[];dt_controls=[]
    for r in rows:
        if not r['complete']:continue
        if r['frame']=='lab':
            other=r['name'].replace('_lab_','_comoving_')
            if other in states:
                (ai,a),(bi,b)=states[r['name']],states[other]
                assert all(np.array_equal(ai[k],bi[k]) for k in ('id','xy','rho','v','p','mass'))
                assert a['time']==b['time'] and np.array_equal(a['id'],b['id'])
                pairs.append(dict(lab=r['name'],comoving=other,rho_error_relative_change=by[other]['rho_l1']/r['rho_l1']-1,
                                  velocity_error_relative_change=by[other]['velocity_l1']/r['velocity_l1']-1,
                                  max_velocity_difference=float(np.max(abs(a['v']-b['v'])))))
        if r['refinement']==2:
            other=r['name'].replace('_dt1024','_dt512')
            if other in states:
                dt_controls.append(dict(method=r['method'],rho_l1_relative_change=r['rho_l1']/by[other]['rho_l1']-1,
                                        velocity_l1_relative_change=r['velocity_l1']/by[other]['velocity_l1']-1))
    for method in campaign['methods']:
        group=sorted((r for r in rows if r['method']==method and r['refinement']==1 and r['complete']),key=lambda x:x['n'])
        for a,b in zip(group,group[1:]):
            orders.append(dict(method=method,n0=a['n'],n1=b['n'],rho_order=float(np.log(a['rho_l1']/b['rho_l1'])/np.log(b['n']/a['n'])),
                               velocity_order=float(np.log(a['velocity_l1']/b['velocity_l1'])/np.log(b['n']/a['n']))))
    result=dict(cases=rows,orders=orders,frame_pairs=pairs,dt_controls=dt_controls,
                norms='Final median-dual-area m/rho weights normalized by sum; analytic fields at actual final moved positions. Velocity L1 uses Euclidean two-component error.',
                limits=campaign['limits'])
    write(root/('summary_partial.json' if partial else 'summary.json'),result)
    for r in rows:print(r['name'],r['complete'],r.get('rho_l1'),r.get('velocity_l1'),r['steps'])
    if partial:return
    assert len(rows)==len(campaign['cases']) and all(r['complete'] for r in rows)
    assert all(r['steps']==r['dt_denominator'] for r in rows),'Actual timestep is not the intended cap'
    fig,axes=plt.subplots(1,2,figsize=(11,4.8),layout='constrained')
    for method in campaign['methods']:
        group=sorted((r for r in rows if r['method']==method and r['refinement']==1),key=lambda x:x['n'])
        scheme,frame=method.split('_');col={'N':'#d15a32','LDA':'#007e99'}[scheme]
        for ax,key in zip(axes,('rho_l1','velocity_l1')):
            slopes=[np.log(a[key]/b[key])/np.log(b['n']/a['n']) for a,b in zip(group,group[1:])]
            label=f'{scheme} {frame}: p={slopes[0]:.3f}, {slopes[1]:.3f}'
            ax.loglog([r['n'] for r in group],[r[key] for r in group],color=col,
                      ls='-' if frame=='lab' else '--',marker='o' if frame=='lab' else 'x',
                      fillstyle='none',ms=8,lw=1.5,label=label)
    for ax,key,title in zip(axes,('rho_l1','velocity_l1'),('Density','Velocity')):
        anchor=min(r[key] for r in rows if r['n']==48 and r['refinement']==1)*.6
        ax.loglog([48,192],[anchor,anchor/16],':',color='.4',label=r'$N_x^{-2}$ reference')
        ax.set(xlabel=r'Initial resolution $N_x$ ($N_x^2$ vertices)',ylabel=f'{title} area-weighted L1 error',xticks=[48,96,192])
        ax.set_xticklabels(['48','96','192']);ax.xaxis.set_minor_locator(NullLocator());ax.grid(alpha=.2,which='both')
    for ax in axes:ax.legend(fontsize=8,title='Orders: 48→96, 96→192',title_fontsize=8)
    fig.suptitle('Moving Yee vortex, boost=(1,0), t=1; N/Roe split and LDA/Gauss3\nMatched lab / co-moving frames; current source, no topology repair',fontsize=12)
    for ext in ('png','pdf'):fig.savefig(root/'figures'/f'yee_frame_convergence.{ext}',dpi=180)
    plt.close(fig)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--partial',action='store_true')
    a=p.parse_args();analyze(a.root.resolve(),a.partial)
