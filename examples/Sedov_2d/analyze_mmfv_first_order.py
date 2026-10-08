#!/usr/bin/env python3
"""Compare first-order MMFV (exact/HLLC), second-order MMFV and moving Rusanov RD."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import numpy as np
from scipy.stats import binned_statistic
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(REPO/'tests/rd'))
sys.path.insert(0,str(HERE))
from run_n_gauss3_split import state,sha,write
from analyze_swift_default import center,radial,describe
from analyze_mmfv import fv_state,verify_native
from audit_reference_scales import dense_reference

MMFV=REPO.parent/'local_runs/sedov_mmfv_20260929_v1'
RD=REPO.parent/'local_runs/sedov_positivity_20260929_v2'


def core_rows(s):
    """Mass-weighted density and sample counts in the evacuated core."""
    rows={}
    for rmax in (.05,.1,.15):
        take=s['r']<rmax
        rows[str(rmax)]=dict(count=int(take.sum()),mass=float(s['mass'][take].sum()),
                             area=float(s['w'][take].sum()),
                             mean_density_by_area=float(s['mass'][take].sum()/s['w'][take].sum()) if take.any() else None)
    return rows


def main(root):
    out=root/'analysis';out.mkdir(exist_ok=False)
    for path in (__file__,HERE/'analyze_mmfv.py',HERE/'analyze_swift_default.py',HERE/'audit_reference_scales.py'):
        shutil.copy2(path,out/Path(path).name)
    exact=dense_reference();campaign=json.loads((root/'campaign.json').read_text())
    source=json.loads((root/'source_provenance.json').read_text())
    assert sha(root/'source.tar')==source['source_tar_sha256']
    cases={};metadata={};origins={}
    for c in campaign['cases']:
        assert sha(c['ic'])==c['ic_sha256'] and sha(Path(c['folder'])/'param.txt')==c['param_sha256']
    for method in campaign['methods']:
        folder=root/'runs'/f'nearest21_{method}'
        cases[method],metadata[method]=verify_native(root,method,folder,fv_state)
    cases['MMFV_2nd_exact'],metadata['MMFV_2nd_exact']=verify_native(MMFV,'MMFV_moving',MMFV/'runs/nearest21',fv_state)
    cases['RD_Rusanov_moving'],metadata['RD_Rusanov_moving']=verify_native(
        RD,'Rusanov_moving',RD/'runs/nearest21_Rusanov_moving',state)
    for key,seq in cases.items():
        if key.startswith('MMFV'):
            s0=seq[0];hot=s0['u']>2e-6;assert hot.sum()==21
            origins[key]=np.average(s0['xy'][hot],axis=0,weights=s0['mass'][hot]*(s0['u'][hot]-1.5e-6))
        else:
            origins[key]=center(RD/'inputs/sedov_nearest21.hdf5',np.load(RD/'inputs/median_dual_area.npy'))
    final={};metrics={}
    for key,seq in cases.items():
        s=radial(seq[-1],origins[key]);final[key]=s
        metrics[key]=describe(s,seq[0],exact);metrics[key]['core']=core_rows(s)
        means,edges,_=binned_statistic(s['r'],s['rho'],statistic='mean',bins=np.arange(0,.4001,.005))
        j=int(np.nanargmax(means));metrics[key]['binned_density_peak']=float(means[j])
        metrics[key]['binned_peak_radius']=float((edges[j]+edges[j+1])/2)
        metrics[key]['history']=[[a['time'],*a['totals'].tolist()] for a in seq]
    analytic_core={str(r):float(np.trapezoid(np.where(exact['r']<r,exact['rho'],0)*2*np.pi*exact['r'],exact['r'])/(np.pi*r*r))
                   for r in (.05,.1,.15)}
    write(out/'verification.json',dict(metrics=metrics,metadata=metadata,analytic_mean_core_density=analytic_core,
        analytic_shock_radius=exact['shock'],source_provenance=source,analysis_sha256=sha(__file__),
        method='FV states at cell centroids, RD at nodes; radius from each initial injected-excess-energy centroid; '
               'core density = sample mass / sample area inside r (Voronoi volume for FV, median-dual area for RD).',
        limits='First-order MMFV disables face extrapolation only; it is not a controlled flux-only ablation of RD '
               '(Voronoi versus median-dual cells, forward-Euler versus RK2 stages, exact FV conservation through reconnection).'))
    styles=[('MMFV_2nd_exact','MMFV 2nd order, exact','#376db1','-'),
            ('MMFV_1st_exact','MMFV 1st order, exact','#2a9d8f','--'),
            ('MMFV_1st_hllc','MMFV 1st order, HLLC','#8a5cc2',':'),
            ('RD_Rusanov_moving','Moving Rusanov RD (1st order)','#d1812d','-.')]
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,3,figsize=(12.8,7.1),layout='constrained')
    for row,rmax in enumerate((.4,.15)):
        bins=np.arange(0,rmax+.0001,.005);mid=(bins[1:]+bins[:-1])/2
        for ax,field,label,exterior in zip(axes[row],('rho','vr','p'),('$\\rho$','$v_r$','$p$'),(1.,0.,1e-6)):
            for key,title,color,ls in styles:
                s=final[key];take=s['r']<rmax
                ax.scatter(s['r'][take],s[field][take],s=2 if row==0 else 7,
                           alpha=.03 if row==0 else .15,color=color,rasterized=True)
                mean=binned_statistic(s['r'],s[field],statistic='mean',bins=bins)[0]
                ax.plot(mid,mean,color=color,ls=ls,lw=1.6,label=title)
            ax.plot(np.r_[exact['r'],exact['shock'],.45],np.r_[exact[field],exterior,exterior],'k--',lw=1.2,label='2D Sedov')
            values=np.concatenate([s[field][s['r']<rmax] for s in final.values()])
            lo=min(0.,float(values.min()));hi=max(float(values.max()),float(np.max(exact[field][exact['r']<rmax])))
            pad=(hi-lo)*.06
            ax.set(xlim=(0,rmax),ylim=(lo-pad,hi+pad),xlabel='Radius from injection centroid',ylabel=label)
            ax.grid(alpha=.15)
    axes[0,0].legend(fontsize=8)
    fig.suptitle('Sedov blast, glass $128^2$, 21 heated points, $t=0.05$, moving meshes\n'
                 'First- versus second-order MMFV and first-order Rusanov RD; lower row: core detail')
    fig.savefig(out/'mmfv_first_order_profiles.png',dpi=300);fig.savefig(out/'mmfv_first_order_profiles.pdf');plt.close(fig)
    print(json.dumps({k:dict(rho_min=v['density_min'],rho_max=v['density_max'],mean_peak=v['binned_density_peak'],
        peak_r=v['binned_peak_radius'],dM=v['mass_relative'],dE=v['energy_relative'],
        core={r:v['core'][r]['mean_density_by_area'] for r in v['core']},
        p_core=v['annuli'][0]['p'],p_core_exact=v['annuli'][0]['p_analytic']) for k,v in metrics.items()},indent=1))
    print('analytic mean core density',analytic_core)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    main(p.parse_args().root.resolve())
