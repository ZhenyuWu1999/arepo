#!/usr/bin/env python3
"""Analyze the matched boost1/10 LDA campaign without assuming invariance."""
import argparse,json,re
from pathlib import Path
import numpy as np
import h5py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator
from run_n_gauss3_split import state,sha,write

def exact(xy,t,boost):
    q=(xy-[5+boost*t,5]+5)%10-5;r2=np.sum(q*q,axis=1)
    temp=1-.4*25/(8*np.pi**2*1.4)*np.exp(1-r2)
    f=2.5/np.pi*np.exp(.5*(1-r2))
    return np.sqrt(r2),temp**2.5,np.column_stack((boost-q[:,1]*f,q[:,0]*f))

def analyze(root,partial=False):
    c=json.loads((root/'campaign.json').read_text());rows=[];states={};initial={};gates=[]
    for case in c['cases']:
        d=root/'runs'/case['name'];status=d/'run_status.json'
        if not status.exists():
            assert partial,case['name'];continue
        status=json.loads(status.read_text());meta=json.loads((root/'artifacts'/case['method']/'provenance.json').read_text())
        assert sha(root/'artifacts'/case['method']/'Arepo')==status['binary_sha256']==meta['binary_sha256']
        assert sha(root/'artifacts'/case['method']/'Config.sh')==meta['config_sha256']
        assert meta['source_tar_sha256']==c['source_tar_sha256']
        assert sha(case['ic'])==case['ic_sha256'] and sha(d/'param.txt')==case['param_sha256']
        log=(d/'run.log').read_text()
        if status['returncode']!=0:
            sync=re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*([\deE.+-]+)',log)
            rows.append(dict(**case,complete=False,seconds=status['seconds'],returncode=status['returncode'],
                last_step=int(sync[-1][0]) if sync else None,last_time=float(sync[-1][1]) if sync else None,
                failure_lines=[x for x in log.splitlines() if 'RD assertion' in x or 'TERMINATE:' in x]))
            continue
        assert 'bye!' in log,case['name']
        assert not any(x in log for x in ['TERMINATE:','RD assertion','very bad...'])
        snaps=sorted((d/'output').glob('snap_*.hdf5'));ss=[state(p) for p in snaps];a,b=ss[0],ss[-1]
        assert abs(b['time']-case['end'])<1e-12
        for s in ss:
            assert np.array_equal(s['id'],a['id'])
            for k in ('rho','p','mass','w'):assert np.isfinite(s[k]).all() and np.min(s[k])>0
            for k in ('xy','v'):assert np.isfinite(s[k]).all()
        if case['mesh']=='static':
            assert all(np.array_equal(a['xy'],s['xy']) for s in ss)
            assert max(np.max(abs(a['w']-s['w'])) for s in ss)<1e-12
            for snap in snaps:
                with h5py.File(snap) as f:assert np.max(abs(f['PartType0/VertexVelocity'][:]))==0
        sync=re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*([\deE.+-]+)',log);steps=int(sync[-1][0])
        assert steps==round(case['end']*case['dt_denominator']),(case['name'],steps)
        mins={}
        for key in ('predictor_min_rho','predictor_min_press'):
            vals=[float(x) for x in re.findall(key+r'=([\deE.+-]+)',log)]
            assert vals and min(vals)>0;mins[key]=min(vals)
        row=dict(**case,seconds=status['seconds'],steps=steps,complete=True,
            snapshot=str(snaps[-1]),snapshot_sha256=sha(snaps[-1]),
            mass_relative_drift=float((b['mass'].sum()-a['mass'].sum())/a['mass'].sum()),**mins)
        if case['phase']=='uniform':
            defect=max(float(np.max(abs(a[k]-b[k]))) for k in ('rho','v','p'));assert defect<1e-12
            gates.append(dict(method=case['method'],defect=defect))
        elif case['phase']=='yee':
            assert len(b['rho'])==case['n']**2
            r,rho,v=exact(b['xy'],b['time'],case['boost']);w=b['w']/b['w'].sum()
            row.update(rho_l1=float(w@abs(b['rho']-rho)),velocity_l1=float(w@np.linalg.norm(b['v']-v,axis=1)),
                f1_lumped_sum=sum(map(int,re.findall(r'f1_lumped=(\d+)',log))))
            states[(case['mesh'],case['boost'],case['n'])]=b;initial[(case['mesh'],case['boost'],case['n'])]=a
        rows.append(row)
    science=[r for r in rows if r['phase']=='yee' and r['complete']];fits=[];by={(r['mesh'],r['boost'],r['n']):r for r in science}
    for method in c['methods']:
        g=sorted((r for r in science if r['method']==method),key=lambda r:r['n'])
        if len(g)!=3:continue
        for key in ('rho_l1','velocity_l1'):
            x=np.log(10./np.array([r['n'] for r in g]));y=np.log([r[key] for r in g]);p,a=np.polyfit(x,y,1)
            fits.append(dict(method=method,field=key,n=[r['n'] for r in g],order=float(p),log_C=float(a),
                r_squared=float(1-np.sum((y-a-p*x)**2)/np.sum((y-y.mean())**2))))
    pairs=[];boost_pairs=[]
    for n in (48,96,192):
        for boost in (1,10):
            keys=[(m,boost,n) for m in ('static','moving')]
            if not all(k in by for k in keys):continue
            a,b=[initial[k] for k in keys]
            for k in ('id','xy'):assert np.array_equal(a[k],b[k])
            assert max(np.max(abs(a[k]-b[k])) for k in ('rho','v','p','mass','w'))<1e-12
            a,b=[by[k] for k in keys]
            assert a['steps']==b['steps']
            pairs.append(dict(n=n,boost=boost,rho_moving_over_static=b['rho_l1']/a['rho_l1'],velocity_moving_over_static=b['velocity_l1']/a['velocity_l1']))
        for mesh in ('static','moving'):
            keys=[(mesh,b,n) for b in (1,10)]
            if not all(k in by for k in keys):continue
            a,b=[initial[k] for k in keys]
            for k in ('id','xy'):assert np.array_equal(a[k],b[k])
            assert max(np.max(abs(a[k]-b[k])) for k in ('rho','p','mass','w'))<1e-12
            assert np.max(abs(b['v']-a['v']-[9,0]))<2e-14
            a,b=[by[k] for k in keys];assert a['steps']==b['steps']
            boost_pairs.append(dict(n=n,mesh=mesh,rho_boost10_over_1=b['rho_l1']/a['rho_l1'],velocity_boost10_over_1=b['velocity_l1']/a['velocity_l1']))
    old=json.loads((Path(c['baseline'])/'summary.json').read_text());dt_pairs=[]
    for r in science:
        if r['boost']!=1:continue
        ref=next(x for x in old['cases'] if x['method']=='LDA_'+r['mesh'] and x['n']==r['n'] and x['problem']=='yee')
        dt_pairs.append(dict(n=r['n'],mesh=r['mesh'],rho_fine_dt_over_previous=r['rho_l1']/ref['rho_l1'],velocity_fine_dt_over_previous=r['velocity_l1']/ref['velocity_l1']))
    result=dict(cases=rows,fits=fits,mesh_pairs=pairs,boost_pairs=boost_pairs,dt_pairs=dt_pairs,uniform_gates=gates,
        norms='Final median-dual area-weighted L1 at actual generator positions; velocity is 2D Euclidean vector error. Analytic center follows each boost with periodic wrapping.',
        fitting='Equal-weight log(E)=log(C)+p log(h), h=10/Nx, using all three points, no adjacent slopes as primary orders.',
        limitations='Matched finite-resolution boost sensitivity, not proof of exact Galilean invariance or an error floor. h and dt refined together; no causal attribution to topology/contour/F1 without ablation.')
    write(root/('summary_partial.json' if partial else 'summary.json'),result)
    if partial:return
    assert len(rows)==18 and len(gates)==4
    failures=[r for r in rows if not r['complete']]
    assert len(science)+sum(r['phase']=='yee' for r in failures)==12
    colors={'static':'#1776b6','moving':'#d45b2a'}
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
    for method in c['methods']:
        group=sorted((r for r in science if r['method']==method),key=lambda r:r['n'])
        if not group:continue
        mesh=group[0]['mesh'];boost=group[0]['boost']
        for ax,key,title in zip(axes,('rho_l1','velocity_l1'),('Density','Velocity')):
            f=next((f for f in fits if f['method']==method and f['field']==key),None);xx=np.geomspace(48,192,100)
            if f:ax.loglog(xx,np.exp(f['log_C'])*(10./xx)**f['order'],color=colors[mesh],ls='-' if boost==1 else '--',label=f'{mesh}, boost {boost}: p={f["order"]:.2f}')
            ax.loglog([r['n'] for r in group],[r[key] for r in group],ls='none',marker='o' if boost==1 else 's',fillstyle='none',ms=7,color=colors[mesh],label=None if f else f'{mesh}, boost {boost}: incomplete series')
            ax.set(xlabel=r'$N_x$ ($N_x^2$ vertices)',ylabel=title+' area-weighted L1 error',xticks=[48,96,192]);ax.set_xticklabels(['48','96','192']);ax.xaxis.set_minor_locator(NullLocator());ax.grid(alpha=.2,which='both')
    for ax in axes:ax.legend(fontsize=8)
    fig.suptitle('Yee LDA/Gauss3, lab frame, t=1: boost sensitivity\n'+('Failed runs excluded; fits only for complete three-point series' if failures else 'Matched ICs and actual timesteps; lines: all-three-point fits'),fontsize=12)
    for ext in ('png','pdf'):fig.savefig(root/'figures'/f'yee_lda_boost_sensitivity.{ext}',dpi=180)
    plt.close(fig)
    fig,axes=plt.subplots(2,3,figsize=(13,7),layout='constrained',sharex=True,sharey='row')
    radial={}
    for col,n in enumerate((48,96,192)):
        rr=np.linspace(0,4,400);_,rho,_=exact(np.column_stack((rr+5,np.full_like(rr,5))),0,0)
        axes[0,col].plot(rr,rho,'k:',label='Analytic')
        for mesh in ('static','moving'):
            for boost in (1,10):
                if (mesh,boost,n) not in states:continue
                s=states[(mesh,boost,n)];r,rho,_=exact(s['xy'],1,boost);error=s['rho']-rho;w=s['w'];m=r<4
                axes[0,col].scatter(r[m],s['rho'][m],s=2.5,alpha=.3,edgecolors='none',color=colors[mesh],marker='o' if boost==1 else 's',rasterized=True)
                edges=np.arange(0,4.0001,.1);bx=[];by=[]
                for lo,hi in zip(edges,edges[1:]):
                    m=(r>=lo)&(r<hi)
                    if m.any():bx.append(float(w[m]@r[m]/w[m].sum()));by.append(float(w[m]@abs(error[m])/w[m].sum()))
                radial[f'{mesh}_b{boost}_n{n}']=dict(radius=bx,mean_absolute_error=by)
                axes[1,col].semilogy(bx,by,color=colors[mesh],ls='-' if boost==1 else '--',label=f'{mesh}, boost {boost}')
        missing=[f"{r['mesh']} boost{r['boost']} failed" for r in failures if r['phase']=='yee' and r['n']==n]
        axes[0,col].set(title=f'{n}²'+('\n'+', '.join(missing) if missing else ''),xlim=(0,4));axes[1,col].set(xlabel='Radius from analytic center',xlim=(0,4))
    axes[0,0].set_ylabel('Density');axes[1,0].set_ylabel('Annular mean absolute density error')
    handles={}
    for ax in axes[1]:
        hh,ll=ax.get_legend_handles_labels()
        handles.update(zip(ll,hh))
    axes[1,0].legend(handles.values(),handles.keys(),fontsize=8)
    for ax in axes.flat:ax.grid(alpha=.2)
    fig.suptitle('LDA density profiles: native nodes and area-weighted radial errors\nBlue: static; orange: moving; circles/solid: boost1; squares/dashed: boost10',fontsize=12)
    for ext in ('png','pdf'):fig.savefig(root/'figures'/f'yee_lda_boost_profiles.{ext}',dpi=180)
    plt.close(fig);write(root/'radial_profiles.json',radial)
    write(root/'verification.json',dict(all18_runs_accounted_for=True,all18_runs_complete=not failures,failed_runs=[r['name'] for r in failures],matched_initial_conditions_for_completed_pairs=True,matched_actual_steps_for_completed_runs=True,all_completed_saved_states_and_logged_predictors_positive=True,all_completed_static_coordinates_and_areas_fixed=True,uniform_gates=gates,figures_visually_checked=[]))
    lines=['# Yee LDA: boost1/10 matched static/moving comparison','','All cases use lab-frame Gauss3 mixed-F1 LDA, box10, gamma1.4, beta5, t1, same tiled glass48 family. Four uniform gates and two short192 pilots precede12 science runs. No solver/default/thesis changes.','',
        'Shared timestep caps48/96/192: 1/1024,1/2048,1/4096. Actual steps of completed runs are checked to match across meshes and boosts. Prior boost1 runs used4×larger caps, so they are kept only as a separate timestep-sensitivity comparison.','',
        '## Norms and whole-range fits','','| mesh | boost | Nx | rho L1 | velocity L1 | mass drift |','|---|---:|---:|---:|---:|---:|']
    for r in sorted(science,key=lambda r:(r['mesh'],r['boost'],r['n'])):lines.append(f"| {r['mesh']} | {r['boost']} | {r['n']} | {r['rho_l1']:.9g} | {r['velocity_l1']:.9g} | {r['mass_relative_drift']:.6g} |")
    if failures:
        lines+=['','## Failed runs: no t=1 error assigned','']
        for r in failures:lines.append(f"- {r['name']}: stopped at t={r['last_time']}, step={r['last_step']}. "+' '.join(r['failure_lines']))
    lines+=['','| method | field | fitted p | log-space R² |','|---|---|---:|---:|']
    for f in fits:lines.append(f"| {f['method']} | {f['field']} | {f['order']:.4f} | {f['r_squared']:.6f} |")
    lines+=['',f'![Fits]({root}/figures/yee_lda_boost_sensitivity.png)','','## Boost10 / boost1 error ratios','','| mesh | Nx | rho ratio | velocity ratio |','|---|---:|---:|---:|']
    for r in boost_pairs:lines.append(f"| {r['mesh']} | {r['n']} | {r['rho_boost10_over_1']:.6f} | {r['velocity_boost10_over_1']:.6f} |")
    lines+=['',f'![Profiles]({root}/figures/yee_lda_boost_profiles.png)','','## Limits','',''+result['norms'],result['fitting'],result['limitations'],'',
        'Exact Galilean invariance cannot be inferred simply from moving mesh. A lower but resolution-dependent error is not evidence of a floor; contour/geometry/edge-flip/F1 attribution requires separate tests. No384/768 runs were added.','',
        'All source/binary/input hashes are retained in campaign/provenance and all outputs remain in separate directories. Failed runs are preserved and excluded from t=1 comparisons, not counted as successful. Checks on completed runs passed; visual QA and final interpretation are separate.']
    (root/'report.md').write_text('\n'.join(lines)+'\n')
    print('Completed matched boost analysis. Figures await visual QA.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--partial',action='store_true')
    a=p.parse_args();analyze(a.root.resolve(),a.partial)
