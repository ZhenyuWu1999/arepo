#!/usr/bin/env python3
"""Audit and plot new static Sod runs alongside retained moving controls."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import shutil

import h5py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

from run_n_gauss3_split import sha, state, write
from plot_sod_thesis_preview import means, LABELS


def analyze(root):
    campaign=json.loads((root/'campaign.json').read_text())
    control=Path(campaign['control_archive'])
    old=json.loads((control/'campaign.json').read_text())
    old_summary=json.loads((control/'summary.json').read_text())
    remember={}

    def check(path,expected=None):
        actual=sha(path)
        if expected is not None:assert actual==expected,str(path)
        remember[str(path)]=actual

    for archive in (root,control):
        check(archive/'campaign.json')
        check(archive/'source_provenance.json')
        check(archive/'source.tar',campaign['source_tar_sha256'])
    check(control/'summary.json')
    exactfile=root/'source/examples/shocktube_1d/Riemann.py'
    check(exactfile,json.loads((root/'source_provenance.json').read_text())['tracked_hashes']['examples/shocktube_1d/Riemann.py'])
    spec=importlib.util.spec_from_file_location('frozen_riemann',exactfile)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

    def exact(x,t):
        _,q,waves=module.RiemannProblem(np.asarray(x).copy(),.5,np.array([1.,0.,1.]),
                                       np.array([.125,0.,.1]),1.4,t)
        return np.column_stack((q,q[:,2]/(.4*q[:,0]))),.5+waves

    selected=[(root,c) for c in campaign['cases']]
    for c in old['cases']:
        if c['problem']=='sod':
            selected.append((control,dict(c,mesh='moving',
                temporal='lumped RK2' if c['scheme']=='N' else 'mixed-stage F1')))
    curves,initial,rows,gates={},{},[],[]
    for archive,c in selected:
        folder=archive/'runs'/c['name'];artifact=archive/'artifacts'/c['method']
        meta=json.loads((artifact/'provenance.json').read_text())
        status=json.loads((folder/'run_status.json').read_text())
        assert status['returncode']==0 and status['binary_sha256']==meta['binary_sha256']
        assert meta['source_tar_sha256']==campaign['source_tar_sha256']
        for p,expected in ((artifact/'Arepo',meta['binary_sha256']),
                           (artifact/'Config.sh',meta['config_sha256']),
                           (folder/'param.txt',c['param_sha256']),
                           (Path(c['ic']),c['ic_sha256'])):check(p,expected)
        for p in (artifact/'provenance.json',folder/'run_status.json',folder/'run.log'):check(p)
        config=(artifact/'Config.sh').read_text().splitlines()
        if c['mesh']=='static':
            assert 'VORONOI_STATIC_MESH' in config
            assert 'RD_ALE_EQUALSTEP' not in config
            assert ('RD_DIAG_PREDICTOR_ONLY' in config)==(c['temporal']=='forward Euler')
        log=(folder/'run.log').read_text();assert 'bye!' in log
        failures=[l for l in log.splitlines() if any(k in l for k in ('TERMINATE:','RD assertion','very bad...','invalid geometry:'))]
        assert not failures,failures
        if c['mesh']=='static' and c['temporal']=='forward Euler':
            assert 'RD-CKSUM stage=0' in log and 'RD-CKSUM stage=1' not in log
        history=[]
        for file in sorted((folder/'output').glob('snap_*.hdf5')):
            check(file);s=state(file)
            with h5py.File(file) as f:
                order=np.argsort(f['PartType0/ParticleIDs'][:])
                s['e']=f['PartType0/InternalEnergy'][:][order]
                if c['mesh']=='static':assert np.max(abs(f['PartType0/VertexVelocity'][:]))==0.
            assert all(np.isfinite(s[k]).all() for k in ('rho','p','v','mass','xy','e'))
            assert min(s['rho'].min(),s['p'].min(),s['mass'].min())>0.
            np.testing.assert_allclose(s['p'],.4*s['rho']*s['e'],rtol=1e-12)
            if history:
                assert np.array_equal(s['id'],history[0]['id'])
                if c['mesh']=='static':assert np.array_equal(s['xy'],history[0]['xy'])
            s['snapshot']=str(file);history.append(s)
        a,s=history[0],history[-1]
        assert s['time']==c['end']
        if c['problem']=='uniform':
            defect=max(float(np.max(abs(s[k]-a[k]))) for k in ('rho','p','v'))
            assert defect<1e-12
            gates.append(dict(method=c['method'],max_change=defect));continue
        assert len(s['id'])==128**2
        assert [h['time'] for h in history]==[0.,.02,.04,.06,.08]
        initial[c['method']]=a
        mask=(s['xy'][:,0]>.25)&(s['xy'][:,0]<.75)
        x=2*(s['xy'][mask,0]-.25)
        q=np.column_stack((s['rho'][mask],s['v'][mask,0],s['p'][mask],s['e'][mask]))
        weights=s['w'][mask]/s['w'][mask].sum()
        ex,waves=exact(s['xy'][mask,0],s['time'])
        error=weights@abs(q-ex)
        bx,bq,counts=means(x,q);assert counts.sum()==len(x)
        curves[c['method']]=(x,q,bx,bq)
        plateau=(x>=.7)&(x<=.76);wp=weights[plateau]/weights[plateau].sum()
        std=float(np.sqrt(wp@((q[plateau,1]-wp@q[plateau,1])**2)))
        sync=re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*([\deE.+-]+),\s+Systemstep:\s*([\deE.+-]+)',log)
        dt=[float(z[2]) for z in sync if float(z[2])>0]
        row=dict(method=c['method'],scheme=c['scheme'],mesh=c['mesh'],temporal=c['temporal'],
            residual=c['residual'],frame='lab',tube_nodes=len(x),snapshot=s['snapshot'],
            snapshot_sha256=sha(s['snapshot']),rho_l1=float(error[0]),vx_l1=float(error[1]),
            p_l1=float(error[2]),e_l1=float(error[3]),vx_min=float(q[:,1].min()),
            vx_max=float(q[:,1].max()),rho_min=float(q[:,0].min()),p_min=float(q[:,2].min()),
            plateau_vx_std=std,steps=int(sync[-1][0]),step_min=min(dt),step_max=max(dt),
            time=s['time'],tube_time=2*s['time'],
            mass_relative_drift=float((s['totals'][0]-a['totals'][0])/a['totals'][0]),
            energy_relative_drift=float((s['totals'][3]-a['totals'][3])/a['totals'][3]))
        if c['mesh']=='moving':
            saved=next(z for z in old_summary['cases'] if z['name']==c['name'])
            for k in ('rho_l1','vx_l1','p_l1','vx_min','vx_max'):
                assert np.isclose(row[k],saved[k],atol=1e-14,rtol=0),(c['name'],k)
        rows.append(row)
        np.savetxt(root/f'{c["method"]}_bin_means.csv',np.column_stack((bx,bq,counts)),
                   delimiter=',',header='xi,rho,vx,p,specific_internal_energy,count',comments='')
    for a in initial.values():
        ref=next(iter(initial.values()))
        for k in ('id','xy','rho','p','v','mass'):
            np.testing.assert_allclose(a[k],ref[k],rtol=0,atol=1e-14)
    write(root/'summary.json',dict(cases=rows,uniform_gates=gates,
        input_hashes=remember,initial_states_matched=True,
        physical_parameters_matched=True,static_coordinates_bitwise_unchanged=True,
        static_vertex_velocity_zero=True,
        coordinates='xi=2(x-.25), tau=2t; full y range, raw x in (.25,.75).',
        mean='128 uniform xi bins, unweighted node means; all nodes remain in scatter.',
        norm='Current median-dual area mass/rho, normalized within the tube; evaluated on raw nodes.',
        limits=campaign['limits']))
    make_plots(root,curves,exact)
    for path,expected in remember.items():assert sha(path)==expected,path
    for name in (Path(__file__).name,'run_sod_static_preview.py','run_n_gauss3_split.py','plot_sod_thesis_preview.py'):
        shutil.copy2(Path(__file__).parent/name,root/name)
    shutil.copy2(exactfile,root/'Riemann.py')
    print(json.dumps(rows,indent=2))


def make_plots(root,curves,exact):
    figures=root/'figures';figures.mkdir(exist_ok=True)
    pdfs=root/'output/pdf';pdfs.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.linewidth':.8,
        'xtick.direction':'in','ytick.direction':'in','xtick.top':True,'ytick.right':True,'pdf.fonttype':42})
    xx=np.linspace(.25,.75,2401);ex,waves=exact(xx,.08);xx=2*(xx-.25)
    groups={
        'N':[('N_roe_rk2_static','#c77b1a','-','Static'),
             ('N_roe_split_sod_lab','#278449','-.','Moving')],
        'LDA':[('LDA_gauss3_f1_static','#9467bd','-','Static'),
               ('LDA_gauss3_sod_lab','#2672b5','-.','Moving')],
        'temporal':[('LDA_gauss3_f1_static','#9467bd','-','F1, Gauss3'),
                    ('LDA_gauss3_fe_static','#16877d','--','Euler, Gauss3'),
                    ('LDA_roe_fe_static','#c77b1a','-.','Euler, Roe')]}

    def panel(ax,group,field,xlim=(0,1),ylim=None):
        for method,color,style,label in groups[group]:
            x,q,bx,bq=curves[method]
            ax.scatter(x,q[:,field],s=3,color=color,alpha=.12,edgecolors='none',rasterized=True,zorder=1)
            ax.plot(bx,bq[:,field],color=color,lw=1.35,ls=style,label=label,zorder=3)
        ax.plot(xx,ex[:,field],color='black',ls='--',lw=1.25,label='Analytic',zorder=4)
        ax.set(xlim=xlim,ylabel=LABELS[field]);ax.grid(color='.9',lw=.5)
        if ylim:ax.set_ylim(ylim)

    figs=[]
    fig,axes=plt.subplots(4,2,figsize=(9.4,10.1),sharex=True,sharey='row',layout='constrained')
    for j,scheme in enumerate(('N','LDA')):
        for i in range(4):panel(axes[i,j],scheme,i)
        axes[0,j].set_title('N / lumped RK2' if scheme=='N' else 'LDA / F1')
        axes[0,j].legend(loc='upper right',frameon=False,fontsize=8.5)
        axes[-1,j].set_xlabel(r'Tube coordinate $\xi$')
    fig.suptitle(r'Sod: static and moving, $N_x\simeq64$, $\tau=0.16$',fontsize=12)
    figs.append(('sod_static_moving_profiles',fig))

    fig,axes=plt.subplots(2,2,figsize=(9.4,6.8),sharex=True,sharey='row',layout='constrained')
    for j,scheme in enumerate(('N','LDA')):
        panel(axes[0,j],scheme,0,(.57,.87),(.03,.49))
        panel(axes[1,j],scheme,1,(.57,.87),(-.82,1.14))
        axes[0,j].set_title(scheme);axes[0,j].legend(loc='upper right',frameon=False,fontsize=8.5)
        axes[1,j].set_xlabel(r'Tube coordinate $\xi$')
        for ax in axes[:,j]:
            for x in 2*(waves[[2,4]]-.25):ax.axvline(x,color='.65',ls=':',lw=.7,zorder=0)
    fig.suptitle(r'Sod: contact and shock, static vs moving',fontsize=12)
    figs.append(('sod_static_moving_zoom',fig))

    fig,axes=plt.subplots(2,2,figsize=(9.4,6.8),layout='constrained')
    for i,ax in enumerate(axes.flat):
        panel(ax,'temporal',i);ax.set_xlabel(r'Tube coordinate $\xi$')
    axes[0,0].legend(loc='upper right',frameon=False,fontsize=8.5)
    fig.suptitle(r'Static LDA: F1 and first-order controls, $\tau=0.16$',fontsize=12)
    figs.append(('sod_static_lda_temporal',fig))
    with PdfPages(pdfs/'sod_static_review.pdf') as book:
        for stem,fig in figs:
            fig.savefig(figures/f'{stem}.png',dpi=190)
            fig.savefig(pdfs/f'{stem}.pdf',dpi=300);book.savefig(fig,dpi=300)
            plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    a=p.parse_args();analyze(a.root.resolve())
