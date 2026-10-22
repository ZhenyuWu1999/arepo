"""Diagnostic 2D sections and alternative cloud criteria from the COSMA data."""
import csv
import json
from pathlib import Path
import os

import h5py
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

ROOT=Path(os.environ['RD_BLOB_AUDIT_ROOT']).resolve()
BUNDLE=Path(os.environ['RD_BLOB_BUNDLE']).resolve()
OUT=ROOT/'plots';OUT.mkdir(exist_ok=False)
TCR=2*np.sqrt(10)/6.15
weights=np.load(ROOT/'slice_weights.npz')
grid=weights['grid'];line=weights['line']
plt.rcParams.update({'font.size':10,'svg.fonttype':'none'})


def state(path):
    with h5py.File(path) as f:
        g=f['PartType0'];o=np.argsort(g['ParticleIDs'][:]);s={k:g[k][:][o] for k in g}
        s['tau']=float(f['Header'].attrs['Time'])/TCR
    return s


def p1z(s,ids,w):
    rho=s['Density'];v=s['Velocities'];p=s['Pressure'];z=np.sqrt(rho)
    enthalpy=(5/3)/(5/3-1)*p/rho+.5*(v*v).sum(axis=1)
    values=np.column_stack((z,z[:,None]*v,z*enthalpy))
    interp=np.sum(w[:,:,None]*values[ids],axis=1)
    r=interp[:,0]**2;vel=interp[:,1:4]/interp[:,0,None]
    press=(5/3-1)/(5/3)*(interp[:,0]*interp[:,4]-.5*(interp[:,1:4]**2).sum(axis=1))
    return r,press,vel[:,0]


def save(fig,name):
    for ext in ['png','svg']:fig.savefig(OUT/f'{name}.{ext}',dpi=190)
    plt.close(fig)


histories={};stored={}
for case in ['N_equal_np8','N_hier_np8']:
    rows=[]
    for path in sorted((BUNDLE/'cases'/case/'snapshots').glob('*.hdf5')):
        s=state(path);r,p,m=s['Density'],s['Pressure'],s['Masses'];temp=p/r
        row=dict(tau=s['tau'],t_over_tcc=2*s['tau'],snapshot=path.name,
            M64_T9=float(m[(r>64)&(temp<9)].sum()),M64=float(m[r>64].sum()),
            M33=float(m[r>100/3].sum()),M33_T9=float(m[(r>100/3)&(temp<9)].sum()),
            M20=float(m[r>20].sum()),max_density=float(r.max()))
        rows.append(row)
        if case=='N_equal_np8':stored[int(path.stem.split('_')[-1])]=s
    histories[case]=rows
    with (OUT/f'{case}_thresholds.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
colors=['#2468a0','#d66625','#488346']
for case,style in [('N_equal_np8','-'),('N_hier_np8','--')]:
    rows=histories[case];m0=rows[0]['M64_T9']
    for key,label,c in zip(['M64_T9','M33','M20'],
        [r'$\rho>0.64\rho_{\rm cl}$ and $T<0.9T_{\rm w}$',r'$\rho>\rho_{\rm cl}/3$',r'$\rho>0.2\rho_{\rm cl}$'],colors):
        axes[0].plot([r['t_over_tcc'] for r in rows],[r[key]/m0 for r in rows],style,color=c,
                      label=label if style=='-' else None,lw=2)
    axes[1].plot([r['t_over_tcc'] for r in rows],[r['max_density']/100 for r in rows],style,color=colors[0])
axes[0].legend(frameon=False,fontsize=9)
axes[0].set(xlabel=r'$t/t_{\rm cc}$, $t_{\rm cc}=R\sqrt{\chi}/v=\frac{1}{2}t_{\rm cr}$',
            ylabel='Selected mass / initial cloud mass',ylim=(-.02,1.3),xlim=(0,3))
axes[1].axhline(.64,color=colors[0],ls=':',label=r'$0.64\rho_{\rm cl}$')
axes[1].axhline(1/3,color=colors[1],ls=':',label=r'$\rho_{\rm cl}/3$')
axes[1].set(xlabel=r'$t/t_{\rm cc}$',ylabel=r'$\rho_{\max}/\rho_{\rm cl}$',xlim=(0,3))
axes[1].legend(frameon=False)
fig.suptitle('Threshold and time conventions materially change the apparent cloud lifetime')
fig.supxlabel('Solid: equal timesteps; dashed: hierarchy. All curves use the same simulations.',fontsize=9)
save(fig,'threshold_sensitivity')

fig,axes=plt.subplots(3,4,figsize=(13.8,8.2),layout='constrained')
scales=[LogNorm(7,150),plt.Normalize(30,360),plt.Normalize(0,6.5)]
cmaps=['magma','viridis','cividis'];labels=[r'$\rho(Z)$',r'$p(Z)$',r'$v_x(Z)$']
initial_pressure_max=0.
for col,i in enumerate([0,1,5,10]):
    s=stored[i];fields=p1z(s,weights['ids'],weights['weights'])
    if i==0:initial_pressure_max=float(fields[1].max())
    for row,(value,scale,cmap) in enumerate(zip(fields,scales,cmaps)):
        ax=axes[row,col];im=ax.imshow(value.reshape(len(grid),len(grid)),origin='lower',
            extent=[0,10,0,10],norm=scale,cmap=cmap,interpolation='nearest',aspect='equal')
        ax.set(xlim=(.5,6.5),ylim=(3,7),xlabel='$x$',ylabel='$y$')
        if row==0:ax.set_title(r'$t/t_{\rm cr}=$'+f"{s['tau']:.6f}")
        if col==3:fig.colorbar(im,ax=axes[row,:],label=labels[row],shrink=.85)
fig.suptitle('3D N/RK2: central XY sections (z=5), P1-Z flux reconstruction\nAt t=0 the nodal pressure is uniform; reconstructed pressure need not be uniform')
save(fig,'early_2d_sections')

fig,axes=plt.subplots(3,1,figsize=(9,8.5),sharex=True,layout='constrained')
for i in [0,1,5,10,20,30]:
    s=stored[i];fields=p1z(s,weights['line_ids'],weights['line_weights'])
    for ax,value in zip(axes,fields):
        ax.plot(line,value,lw=1.5,label=f"{s['tau']:.3f}")
for ax,label in zip(axes,labels):ax.set_ylabel(label)
axes[0].axhline(64,color='.5',lw=.8,ls=':');axes[0].axhline(100/3,color='.5',lw=.8,ls='--')
axes[0].legend(title=r'$t/t_{\rm cr}$',frameon=False,ncol=3,fontsize=9)
axes[-1].set(xlabel='$x$ (line y=z=5)',xlim=(.5,7.5))
fig.suptitle('Longitudinal profiles through the 3D cloud; P1-Z reconstruction')
save(fig,'longitudinal_profiles')

summary=dict(initial_p1z_pressure_max_on_xy_slice=initial_pressure_max,
    initial_nodal_pressure_range=[float(stored[0]['Pressure'].min()),float(stored[0]['Pressure'].max())],
    threshold_histories=histories)
for case,rows in histories.items():
    summary[case]={}
    for criterion in ['M64_T9','M33','M20']:
        m0=rows[0][criterion];cross=[i for i,r in enumerate(rows) if r[criterion]<=m0/2]
        zero=[i for i,r in enumerate(rows) if r[criterion]==0]
        value={}
        if cross:
            j=cross[0];a,b=rows[j-1],rows[j];value['half_bracket_tcr']=[a['tau'],b['tau']]
            value['half_linear_tcr']=a['tau']+(b['tau']-a['tau'])*(a[criterion]-.5*m0)/(a[criterion]-b[criterion])
        if zero:
            j=zero[0];value['zero_bracket_tcr']=[rows[j-1]['tau'],rows[j]['tau']]
        value['final_fraction']=rows[-1][criterion]/m0
        summary[case][criterion]=value
(OUT/'diagnostic_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='threshold_histories'},indent=2))
