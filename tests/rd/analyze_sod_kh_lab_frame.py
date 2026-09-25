#!/usr/bin/env python3
"""Compare lab-frame runs with exact-source archived co-moving controls."""
import argparse,json,re,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from run_n_gauss3_split import state,write

def analyze(root,partial=False):
    campaign=json.loads((root/'campaign.json').read_text());sys.path.insert(0,str(root/'source/examples/shocktube_1d'))
    from Riemann import RiemannProblem
    def exact(x,t):return RiemannProblem(x.copy(),.5,np.array([1.,0.,1.]),np.array([.125,0.,.1]),1.4,t)[1]
    rows=[];data={};pairs=[]
    for c in campaign['cases']:
      for frame,folder in [('lab',root/'runs'/c['name']),('comoving',Path(c['control_dir']))]:
        statusfile=folder/'run_status.json'
        if not statusfile.exists() and not partial:raise RuntimeError(f'{c["name"]} is still running')
        status=json.loads(statusfile.read_text()) if statusfile.exists() else None
        if not (folder/'run.log').exists():continue
        log=(folder/'run.log').read_text();complete=status is not None and status['returncode']==0 and 'bye!' in log
        ss=[]
        for file in sorted((folder/'output').glob('snap_*.hdf5')):
          try:ss.append(state(file))
          except OSError:
            if not partial:raise
        if not ss:continue
        a=ss[0];hist=[]
        for s in ss:
          assert np.array_equal(s['id'],a['id'])
          assert all(np.all(np.isfinite(s[k])) for k in ('rho','p','v','mass'))
          d=s['totals']-a['totals']
          hist.append(dict(time=s['time'],rho_min=float(s['rho'].min()),rho_max=float(s['rho'].max()),p_min=float(s['p'].min()),mass_min=float(s['mass'].min()),mass_relative_drift=float(d[0]/a['totals'][0]),energy_relative_drift=float(d[3]/a['totals'][3]),kinetic_y=float(.5*np.sum(s['mass']*s['v'][:,1]**2))))
        sync=re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*([\deE.+-]+)',log)
        row=dict(name=c['name'] if frame=='lab' else c['control_name'],scheme=c['scheme'],residual=c['residual'],problem=c['problem'],frame=frame,folder=str(folder),complete=complete,running=status is None,status=status,last_log_time=float(sync[-1][1]) if sync else None,steps=int(sync[-1][0]) if sync else None,history=hist,final=hist[-1],failures=[l for l in log.splitlines() if any(z in l for z in ('TERMINATE:','RD assertion','very bad...','invalid geometry:'))])
        if complete:
          assert abs(ss[-1]['time']-c['end'])<1e-10
          assert min(h['rho_min'] for h in hist)>0 and min(h['p_min'] for h in hist)>0
        if c['problem']=='uniform':
          row['uniform_max_change']=max(float(np.max(abs(ss[-1][k]-a[k]))) for k in ('rho','v','p'))
          row['uniform_pass_absolute_1e_12']=complete and row['uniform_max_change']<1e-12
        if c['problem']=='sod':
          s=ss[-1];sel=(s['xy'][:,0]>.25)&(s['xy'][:,0]<.75);w=s['w'][sel];w=w/w.sum();ex=exact(s['xy'][sel,0],s['time'])
          row.update(rho_l1=float(w@abs(s['rho'][sel]-ex[:,0])),vx_l1=float(w@abs(s['v'][sel,0]-ex[:,1])),p_l1=float(w@abs(s['p'][sel]-ex[:,2])),vx_min=float(s['v'][sel,0].min()),vx_max=float(s['v'][sel,0].max()))
          x=2*(s['xy'][:,0]-.25);sel=(x>=.70)&(x<=.76);w=s['w'][sel];w=w/w.sum();v=s['v'][sel,0]
          row['plateau_std_vx']=float(np.sqrt(w@((v-w@v)**2)))
        rows.append(row);data[(c['name'],frame)]=ss
      if (c['name'],'lab') not in data or (c['name'],'comoving') not in data:continue
      lab,frame=data[(c['name'],'lab')],data[(c['name'],'comoving')]
      for k in ('id','xy','rho','p','v','mass'):assert np.array_equal(lab[0][k],frame[0][k]),(c['name'],k)
      matches=[]
      for a in lab:
        b=min(frame,key=lambda q:abs(q['time']-a['time']))
        if abs(a['time']-b['time'])>1e-12:continue
        vals={}
        for k in ('xy','rho','p','v','mass'):
          d=a[k]-b[k]
          if k=='xy':d=(d+.5)%1-.5
          vals[k]=dict(mean_absolute=float(np.mean(abs(d))),max_absolute=float(np.max(abs(d))))
        matches.append(dict(time=a['time'],fields=vals))
      pairs.append(dict(lab_name=c['name'],control_name=c['control_name'],problem=c['problem'],scheme=c['scheme'],matched_snapshots=matches,lab_snapshot_count=len(lab),control_snapshot_count=len(frame),note='Only exactly coincident output times compared by ID. Coordinates use shortest periodic difference. No interpolation or extrapolation.'))
    result=dict(cases=rows,pairs=pairs,settings=campaign['settings'],same_source=True,matched_initial_snapshots=True,limits='Co-moving controls reused. Completion and field positivity are distinct from accuracy/global conservation. Long KH pointwise differences may grow with changing geometry/topology. A2 is evaluated in different coordinates across frames.')
    write(root/('summary_partial.json' if partial else 'summary.json'),result)
    for row in rows:
      if row['problem']!='uniform' and row['frame']=='lab':print(row['name'],'complete',row['complete'],'logtime',row['last_log_time'],'saved',row['final'], 'rhoL1',row.get('rho_l1'))
    if partial:return
    figs=root/'figures';figs.mkdir(exist_ok=True);plt.rcParams.update({'font.size':10})
    combinations=[('N','lab'),('N','comoving'),('LDA','lab'),('LDA','comoving')]
    def get(problem,scheme,frame):
      c=next(c for c in campaign['cases'] if c['problem']==problem and c['scheme']==scheme)
      row=next(row for row in rows if row['problem']==problem and row['scheme']==scheme and row['frame']==frame)
      return data[c['name'],frame],row
    fig,axes=plt.subplots(3,4,figsize=(14,8),sharex=True,sharey='row',layout='constrained')
    for j,(scheme,frame) in enumerate(combinations):
      ss,row=get('sod',scheme,frame);s=ss[-1];axes[0,j].set_title(f'{scheme} / {"Roe split" if scheme=="N" else "Gauss3"}\n{frame}')
      if not row['complete']:
       for ax in axes[:,j]:ax.text(.5,.5,f'Stopped at t={row["last_log_time"]}',transform=ax.transAxes,ha='center')
       continue
      sel=(s['xy'][:,0]>.25)&(s['xy'][:,0]<.75);x=2*(s['xy'][sel,0]-.25);xx=np.linspace(.25,.75,1000);ex=exact(xx,s['time'])
      for i,(key,vals) in enumerate([('Density',s['rho']),('Velocity x',s['v'][:,0]),('Pressure',s['p'])]):
       ax=axes[i,j];ax.scatter(x,vals[sel],s=2,alpha=.25,color='#087e8b' if frame=='lab' else '#ba5b23',edgecolors='none');ax.plot(2*(xx-.25),ex[:,i],'k--',lw=1);ax.set_xlim(0,1);ax.grid(alpha=.15)
       if j==0:ax.set_ylabel(key)
      axes[2,j].set_xlabel('Tube coordinate')
    fig.suptitle('Moving Sod: lab vs co-moving; effective initial Nx=64, raw t=.08 (tube time .16)')
    fig.savefig(figs/'sod_frame_profiles.png',dpi=170);plt.close(fig)
    fig,axes=plt.subplots(4,4,figsize=(12,11),layout='constrained');times=[.8,2,5,10];im=None
    for i,(scheme,frame) in enumerate(combinations):
      ss,row=get('kh',scheme,frame)
      for j,t in enumerate(times):
       ax=axes[i,j];ax.set_aspect('equal');ax.set_xlim(0,1);ax.set_ylim(0,1);ax.set_xticks([]);ax.set_yticks([])
       if j==0:ax.set_ylabel(f'{scheme} / {"Roe split" if scheme=="N" else "Gauss3"}\n{frame}')
       if i==0:ax.set_title(f't={t:g}')
       if ss[-1]['time']<t-.01:
        ax.text(.5,.5,f'Stopped at t={row["last_log_time"]}',transform=ax.transAxes,ha='center',color='firebrick');continue
       s=min(ss,key=lambda x:abs(x['time']-t));tri=mtri.Triangulation(s['xy'][:,0],s['xy'][:,1]);im=ax.tripcolor(tri,s['rho'],shading='gouraud',vmin=.75,vmax=2.25,cmap='viridis')
       ax.text(.015,.02,f'actual t={s["time"]:.5g}\nrho {s["rho"].min():.3f}–{s["rho"].max():.3f}',color='white',fontsize=7,transform=ax.transAxes,bbox=dict(facecolor='black',alpha=.45,pad=1))
    if im is not None:fig.colorbar(im,ax=axes.ravel().tolist(),shrink=.52,label='Density (fixed scale)')
    fig.suptitle('Smooth moving KH: lab vs co-moving; glass48², gamma1.4, CFL.3')
    fig.savefig(figs/'kh_frame_evolution.png',dpi=170,bbox_inches='tight',pad_inches=.12);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(14,4),layout='constrained')
    for scheme,frame in combinations:
      _,row=get('kh',scheme,frame);h=row['history'];t=[x['time'] for x in h];col='#027b9b' if scheme=='N' else '#b64b2e';style='-' if frame=='lab' else '--'
      for ax,key in zip(axes,('rho_min','mass_relative_drift','kinetic_y')):ax.plot(t,[x[key] for x in h],style,color=col,label=f'{scheme} {frame}');ax.set(xlabel='Time',ylabel=key);ax.grid(alpha=.15)
    axes[0].legend(fontsize=8)
    for ax,label in zip(axes,('Minimum density','Relative total-mass drift','Transverse kinetic energy')):ax.set_ylabel(label)
    fig.suptitle('Smooth KH: lab-frame and co-moving diagnostics')
    fig.savefig(figs/'kh_frame_diagnostics.png',dpi=170);plt.close(fig)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--partial',action='store_true');a=p.parse_args();analyze(a.root.resolve(),a.partial)
