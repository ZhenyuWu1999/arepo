#!/usr/bin/env python3
"""Native-node Yee density profiles and radial error budgets, no interpolation."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from run_n_gauss3_split import state,sha,write

def exact_density(r):
    return (1-.4*25/(8*np.pi**2*1.4)*np.exp(1-r*r))**2.5

def main(root):
    summary=json.loads((root/'summary.json').read_text())
    records=[];data={};bins=np.arange(0,7.10001,.05)
    for mesh in ('static','moving'):
        case=next(c for c in summary['cases'] if c['method']=='LDA_'+mesh and c['n']==384 and c['problem']=='yee')
        folder=Path(case['directory']);status=json.loads((folder/'run_status.json').read_text())
        assert status['returncode']==0 and case['complete']
        path=sorted((folder/'output').glob('snap_*.hdf5'))[-1]
        s=state(path);assert abs(s['time']-1)<1e-12 and len(s['rho'])==384**2
        center=np.array([5+case['boost']*s['time'],5])
        xy=(s['xy']-center+5)%10-5;r=np.linalg.norm(xy,axis=1)
        e=s['rho']-exact_density(r);w=s['w'];total=w@abs(e)
        assert np.isclose(total/w.sum(),case['rho_l1'],rtol=1e-12,atol=1e-16)
        binid=np.searchsorted(bins,r,side='right')-1
        rad=[]
        for k in range(len(bins)-1):
            m=binid==k
            if not m.any():continue
            weights=w[m];err=e[m];area=weights.sum()
            rad.append(dict(r=float(weights@r[m]/area),count=int(m.sum()),area=float(area),
                mean_error=float(weights@err/area),mean_absolute_error=float(weights@abs(err)/area)))
        shells=[]
        for lo,hi in [(0,1),(1,2),(2,3),(3,4),(4,float(np.sqrt(50)+1e-6))]:
            m=(r>=lo)&(r<hi);area=w[m].sum();absolute=w[m]@abs(e[m])
            shells.append(dict(r0=lo,r1=hi,area=float(area),mean_error=float(w[m]@e[m]/area),
                mean_absolute_error=float(absolute/area),fraction_of_global_l1=float(absolute/total),
                contribution_to_global_l1=float(absolute/w.sum())))
        assert np.isclose(sum(x['contribution_to_global_l1'] for x in shells),case['rho_l1'],rtol=1e-12)
        records.append(dict(mesh=mesh,snapshot=str(path),snapshot_sha256=sha(path),
            time=s['time'],center=center.tolist(),n_nodes=len(r),rho_l1=float(total/w.sum()),
            minimum_signed_error=float(e.min()),maximum_signed_error=float(e.max()),shells=shells,radial_bins=rad))
        data[mesh]=(r,s['rho'],e,rad)
    write(root/'density_profiles.json',dict(method='LDA/Gauss3 mixed F1, lab frame, boost=(1,0), t=1, 384^2 nodes.',
        radial_definition='Periodic minimum-image distance from analytic center (6,5). No numerical recentering.',
        binning='Width 0.05. Area=m/rho weights. Error evaluated against exact density at each node before binning. No profile interpolation; raw markers include every node within plotted range.',
        summary_sha256=sha(root/'summary.json'),profiles=records))
    colors={'static':'#1676b7','moving':'#d75b28'}
    fig,axs=plt.subplots(3,1,figsize=(9,10),sharex=True,layout='constrained',gridspec_kw={'height_ratios':[1.15,1,1]})
    rr=np.linspace(0,4.5,700)
    visible_mae=[]
    for mesh,(r,rho,e,rad) in data.items():
        color=colors[mesh];mask=r<=4.5
        axs[0].scatter(r[mask],rho[mask],s=1,alpha=.2,c=color,edgecolors='none',rasterized=True)
        axs[1].scatter(r[mask],e[mask],s=1,alpha=.10,c=color,edgecolors='none',rasterized=True)
        bx=np.array([b['r'] for b in rad]);mean=np.array([b['mean_error'] for b in rad]);mae=np.array([b['mean_absolute_error'] for b in rad])
        axs[1].plot(bx,mean,color=color,lw=1.8,label=f'{mesh}: annular mean')
        axs[2].semilogy(bx,mae,color=color,lw=1.8,label=f'LDA {mesh}')
        visible_mae.extend(mae[bx<=4.5])
    axs[0].plot(rr,exact_density(rr),'k--',lw=1.4)
    axs[0].legend(handles=[Line2D([],[],color='k',ls='--',label='Analytic'),
        *[Line2D([],[],color=colors[m],ls='none',marker='.',label=f'LDA {m}: native nodes') for m in data]],fontsize=9)
    axs[0].set(ylabel=r'Density $\rho$',ylim=(.46,1.025),title='Density profile: the two solutions almost overlap')
    axs[1].axhline(0,color='.35',lw=.7)
    ymax=max(abs(x) for rec in records for x in [rec['minimum_signed_error'],rec['maximum_signed_error']])*1.1
    axs[1].set(ylabel=r'$\rho-\rho_{\rm exact}(r)$',ylim=(-ymax,ymax),title='Signed error: native nodes and area-weighted annular means')
    axs[1].ticklabel_format(axis='y',style='sci',scilimits=(0,0));axs[1].legend(fontsize=9)
    axs[2].set(ylabel=r'Annular mean $|\rho-\rho_{\rm exact}|$',xlabel=r'Radius from advected center $r$',title='Absolute error: evaluated at each node before annular averaging')
    axs[2].legend(fontsize=9)
    axs[2].set_ylim(min(visible_mae)*.5,max(visible_mae)*2)
    for ax in axs:ax.set_xlim(0,4.5);ax.grid(alpha=.18)
    fig.suptitle(r'Yee density: $384^2$, boost $(1,0)$, $t=1$; LDA/Gauss3, lab frame',fontsize=13)
    for ext in ('png','pdf'):fig.savefig(root/'figures'/f'yee_lda_density_profile_384.{ext}',dpi=180)
    plt.close(fig)
    # Separate error maps use equal axes and color scales; no regridding or
    # interpolation can manufacture a difference between the two meshes.
    fig,axes=plt.subplots(1,2,figsize=(10,4.7),layout='constrained')
    bound=max(abs(x) for rec in records for x in [rec['minimum_signed_error'],rec['maximum_signed_error']])
    for ax,rec in zip(axes,records):
        s=state(rec['snapshot']);xy=(s['xy']-rec['center']+5)%10-5
        e=s['rho']-exact_density(np.linalg.norm(xy,axis=1));m=np.max(abs(xy),axis=1)<2.5
        sc=ax.scatter(xy[m,0],xy[m,1],c=e[m],s=2.3,marker='s',cmap='RdBu_r',vmin=-bound,vmax=bound,edgecolors='none',rasterized=True)
        ax.set(title=f'LDA {rec["mesh"]}',xlabel=r'$x-x_c$',ylabel=r'$y-y_c$',xlim=(-2.5,2.5),ylim=(-2.5,2.5),aspect='equal')
    fig.colorbar(sc,ax=axes,label=r'$\rho-\rho_{\rm exact}$',shrink=.83)
    fig.suptitle(r'Density error at native nodes: $384^2$, boost $(1,0)$, $t=1$',fontsize=12)
    for ext in ('png','pdf'):fig.savefig(root/'figures'/f'yee_lda_density_error_map_384.{ext}',dpi=180)
    plt.close(fig)
    for rec in records:
        print(rec['mesh'],rec['rho_l1'],rec['shells'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    main(p.parse_args().root.resolve())
