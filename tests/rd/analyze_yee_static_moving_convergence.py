#!/usr/bin/env python3
"""Matched current-source static/moving Yee errors; keep archival provenance explicit."""
import argparse,json,re
from pathlib import Path
import h5py
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator
from run_n_gauss3_split import state,sha,write

def analyze(root,partial=False):
    campaign=json.loads((root/'campaign.json').read_text());rows=[];states={};initial={};gates={}
    cases=[dict(c,directory=str(root/'runs'/c['name']),new_run=True) for c in campaign['cases']]
    cases += [dict(c,new_run=False) for c in campaign['controls']]
    for c in cases:
        folder=Path(c['directory'])
        if not (folder/'run_status.json').exists():
            assert partial,c['name'];continue
        status=json.loads((folder/'run_status.json').read_text());artifact=root/'artifacts'/c['method']
        meta=json.loads((artifact/'provenance.json').read_text())
        assert sha(artifact/'Arepo')==meta['binary_sha256']==status['binary_sha256']
        assert sha(artifact/'Config.sh')==meta['config_sha256']
        assert meta['source_tar_sha256']==campaign['source_tar_sha256']
        assert sha(c['ic'])==c['ic_sha256'] and sha(folder/'param.txt')==c['param_sha256']
        files=sorted((folder/'output').glob('snap_*.hdf5'));ss=[state(p) for p in files]
        a,b=ss[0],ss[-1];log=(folder/'run.log').read_text()
        sync=re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*([\deE.+-]+)',log)
        complete=status['returncode']==0 and 'bye!' in log and abs(b['time']-c['end'])<1e-12
        row=dict(**c,status=status,complete=complete,last_time=b['time'],steps=int(sync[-1][0]) if sync else None,
          rho_min=min(float(s['rho'].min()) for s in ss),pressure_min=min(float(s['p'].min()) for s in ss),
          mass_relative_drift=float((b['mass'].sum()-a['mass'].sum())/a['mass'].sum()),
          max_coordinate_change=float(np.max(abs((b['xy']-a['xy']+5)%10-5))),
          failures=[s for s in log.splitlines() if any(t in s for t in ('TERMINATE:','RD assertion','very bad...','minimum timestep'))])
        if complete:
            assert all(np.array_equal(a['id'],s['id']) for s in ss)
            assert row['rho_min']>0 and row['pressure_min']>0
            assert all(np.all(s['mass']>0) and np.all(s['w']>0) for s in ss)
            assert all(np.all(np.isfinite(s[k])) for s in ss for k in ('xy','rho','v','p','mass','w'))
            if c['mesh']=='static':
                assert all(np.array_equal(a['xy'],s['xy']) for s in ss),c['name']
                row['max_vertex_velocity']=0.
                for file in files:
                    with h5py.File(file) as f:row['max_vertex_velocity']=max(row['max_vertex_velocity'],float(np.max(abs(f['PartType0/VertexVelocity'][:]))))
                assert row['max_vertex_velocity']==0
                row['max_area_change']=max(float(np.max(abs(s['w']-a['w']))) for s in ss)
                assert row['max_area_change']<1e-12
            if c['problem']=='uniform':
                defect=max(float(np.max(abs(b[k]-a[k]))) for k in ('rho','v','p'));assert defect<1e-12
                gates[c['method']]=defect
            else:
                assert len(b['rho'])==c['n']**2 and row['steps']==c['dt_denominator']
                xy=(b['xy']-np.array([5+c['boost']*b['time'],5])+5)%10-5;r2=np.sum(xy*xy,axis=1)
                temperature=1-.4*25/(8*np.pi**2*1.4)*np.exp(1-r2);rho=temperature**2.5
                factor=2.5/np.pi*np.exp(.5*(1-r2));velocity=np.column_stack((c['boost']-xy[:,1]*factor,xy[:,0]*factor))
                w=b['w']/b['w'].sum()
                row.update(rho_l1=float(w@abs(b['rho']-rho)),velocity_l1=float(w@np.linalg.norm(b['v']-velocity,axis=1)),area_sum=float(b['w'].sum()))
                states[(c['method'],c['n'])]=b;initial[(c['method'],c['n'])]=a
        rows.append(row)
    by={(r['method'],r['n']):r for r in rows if r['problem']=='yee' and r['complete']}
    pairs=[];orders=[]
    for scheme in ('N','LDA'):
        for n in (48,96,192,384):
            k1,k2=(scheme+'_static',n),(scheme+'_moving',n)
            if k1 not in states or k2 not in states:continue
            a,b=initial[k1],initial[k2]
            assert np.array_equal(a['id'],b['id']) and np.array_equal(a['xy'],b['xy'])
            differences={k:float(np.max(abs(a[k]-b[k]))) for k in ('rho','v','p','mass','w')}
            assert max(differences.values())<1e-12,(scheme,n,differences)
            assert sha(by[k1]['ic'])==sha(by[k2]['ic'])
            pairs.append(dict(scheme=scheme,n=n,initial_max_differences=differences,
                rho_moving_over_static=by[k2]['rho_l1']/by[k1]['rho_l1'],velocity_moving_over_static=by[k2]['velocity_l1']/by[k1]['velocity_l1']))
    for method in campaign['methods']:
        group=sorted((r for r in rows if r['method']==method and r['problem']=='yee' and r['complete']),key=lambda r:r['n'])
        for a,b in zip(group,group[1:]):
            orders.append(dict(method=method,n0=a['n'],n1=b['n'],rho_order=float(np.log(a['rho_l1']/b['rho_l1'])/np.log(b['n']/a['n'])),velocity_order=float(np.log(a['velocity_l1']/b['velocity_l1'])/np.log(b['n']/a['n']))))
    fits=[]
    for method in campaign['methods']:
        group=sorted((r for r in rows if r['method']==method and r['problem']=='yee' and r['complete']),key=lambda r:r['n'])
        if len(group)<2:continue
        h=10./np.array([r['n'] for r in group],dtype=float)
        for field,key in [('rho','rho_l1'),('velocity','velocity_l1')]:
            x=np.log(h);y=np.log([r[key] for r in group])
            order,intercept=np.polyfit(x,y,1)
            residual=y-(intercept+order*x)
            fits.append(dict(method=method,field=field,n=[r['n'] for r in group],
                order=float(order),log_C=float(intercept),
                r_squared=float(1-np.sum(residual**2)/np.sum((y-y.mean())**2)),
                log_residuals=residual.tolist()))
    result=dict(cases=rows,orders=orders,fits=fits,mesh_pairs=pairs,new_uniform_gates=gates,
          fit_method='Unweighted least squares of log(L1)=log(C)+p*log(h), h=10/Nx, using all four resolutions. Adjacent slopes are retained only as diagnostics.',
          norms='Analytic fields at actual final generator positions. Normalized final median-dual areas m/rho. Velocity L1 is Euclidean two-component error. Same initial glass and state for each static/moving pair.',
          limits='Four-point h/dt refinement, not fixed-h temporal order. Old moving48/96/192 controls verified and reused. Lab only; no topology repair. No assumption that moving must have smaller errors.')
    write(root/('summary_partial.json' if partial else 'summary.json'),result)
    for r in rows:
        print(r['name'],r['complete'],r.get('rho_l1'),r.get('velocity_l1'),r['steps'])
    if partial:return
    assert len(rows)==18 and all(r['complete'] for r in rows) and len(pairs)==8
    fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    for method in campaign['methods']:
        group=sorted((r for r in rows if r['method']==method and r['problem']=='yee'),key=lambda r:r['n'])
        scheme,mesh=method.split('_');color={'N':'#d15a32','LDA':'#007e99'}[scheme]
        for ax,key in zip(axes,('rho_l1','velocity_l1')):
            fit=next(f for f in fits if f['method']==method and f['field']==key.removesuffix('_l1'))
            nx=np.geomspace(48,384,150)
            fitted=np.exp(fit['log_C'])*(10./nx)**fit['order']
            ax.loglog(nx,fitted,color=color,ls='-' if mesh=='moving' else '--',label=f'{scheme} {mesh}: p={fit["order"]:.2f}')
            ax.loglog([r['n'] for r in group],[r[key] for r in group],color=color,ls='none',marker='o' if mesh=='moving' else 's',fillstyle='none',ms=7)
    for ax,key,title in zip(axes,('rho_l1','velocity_l1'),('Density','Velocity')):
        anchor=min(r[key] for r in rows if r['problem']=='yee' and r['n']==48)*.6
        ax.loglog([48,384],[anchor,anchor/64],':',color='.45',label=r'$N_x^{-2}$ reference')
        ax.set(xlabel=r'Initial resolution $N_x$ ($N_x^2$ vertices)',ylabel=f'{title} area-weighted L1 error',xticks=[48,96,192,384])
        ax.set_xticklabels(['48','96','192','384']);ax.xaxis.set_minor_locator(NullLocator());ax.grid(alpha=.2,which='both')
        ax.legend(fontsize=8,title='All four points: log-log least-squares fit',title_fontsize=8)
    fig.suptitle('Yee vortex, boost=(1,0), t=1; lab frame; N/Roe split and LDA/Gauss3\nMarkers: measured errors; lines: single power-law fits',fontsize=12)
    for ext in ('png','pdf'):fig.savefig(root/'figures'/f'yee_static_moving_convergence.{ext}',dpi=180)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for scheme in ('N','LDA'):
        group=sorted((p for p in pairs if p['scheme']==scheme),key=lambda p:p['n'])
        for ax,key in zip(axes,('rho_moving_over_static','velocity_moving_over_static')):
            ax.plot([p['n'] for p in group],[p[key] for p in group],'-o',label=scheme,color={'N':'#d15a32','LDA':'#007e99'}[scheme])
    for ax,title in zip(axes,('Density','Velocity')):
        ax.axhline(1,color='.3',ls='--');ax.set(xlabel=r'$N_x$',ylabel=f'{title} L1: moving / static',xticks=[48,96,192,384]);ax.grid(alpha=.2);ax.legend()
    fig.suptitle('Below 1: smaller moving-mesh error; above 1: smaller static-mesh error')
    for ext in ('png','pdf'):fig.savefig(root/'figures'/f'yee_static_moving_error_ratio.{ext}',dpi=180)
    plt.close(fig)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--partial',action='store_true')
    a=p.parse_args();analyze(a.root.resolve(),a.partial)
