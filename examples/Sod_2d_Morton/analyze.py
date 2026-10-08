#!/usr/bin/env python3
"""Verify frozen Sod_2d_Morton results and make full-scatter review figures."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import h5py
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'tests/rd'))
if (HERE/'run_n_gauss3_split.py').exists():sys.path.insert(0,str(HERE))
from run_n_gauss3_split import sha,state,write


def analyze(root):
    campaign=json.loads((root/'campaign.json').read_text())
    inputs={}
    def check(p,expected=None):
        p=Path(p);h=sha(p)
        if expected is not None:assert h==expected,str(p)
        inputs[str(p)]=h
    check(root/'campaign.json')
    check(root/'source.tar',campaign['source_tar_sha256'])
    check(root/'source_provenance.json')
    prov=json.loads((root/'source_provenance.json').read_text())
    rf=root/'source/examples/shocktube_1d/Riemann.py'
    check(rf,prov['tracked_hashes']['examples/shocktube_1d/Riemann.py'])
    spec=importlib.util.spec_from_file_location('archived_riemann',rf)
    riemann=importlib.util.module_from_spec(spec);spec.loader.exec_module(riemann)
    gamma=campaign['gamma']
    def exact(x,t=.2):
        _,q,w=riemann.RiemannProblem(np.asarray(x).copy(),1.5,np.array([1.,0.,1.]),np.array([.125,0.,.1]),gamma,t)
        return np.column_stack((q,q[:,2]/((gamma-1)*q[:,0]))),1.5+w
    curves={};rows=[];gates=[];initial={}
    for c in campaign['cases']:
        run=root/'runs'/c['name'];art=root/'artifacts'/c['method']
        check(run/'run_status.json');check(art/'provenance.json')
        status=json.loads((run/'run_status.json').read_text())
        meta=json.loads((art/'provenance.json').read_text())
        assert status['returncode']==0,c['name']
        assert status['binary_sha256']==meta['binary_sha256']
        assert meta['source_tar_sha256']==campaign['source_tar_sha256']
        for p,h in ((art/'Arepo',meta['binary_sha256']),(art/'Config.sh',meta['config_sha256']),
                    (run/'param.txt',c['param_sha256']),(Path(c['ic']),c['ic_sha256'])):check(p,h)
        cfg=(art/'Config.sh').read_text().splitlines()
        for flag in ('GAMMA=(5.0/3.0)','RD_DIAG_PREDICTOR_ONLY','VORONOI_STATIC_MESH','CREATE_FULL_MESH',c['scheme']+'_SCHEME'):assert flag in cfg
        assert not any(l.startswith('RD_ALE_') or l=='RD_ELEMENT_COMOVING_FRAME' for l in cfg)
        check(run/'run.log');log=(run/'run.log').read_text()
        assert 'bye!' in log and 'RD-CKSUM stage=0' in log and 'RD-CKSUM stage=1' not in log
        assert not any(s in log for s in ('TERMINATE:','RD assertion','very bad...','invalid geometry:'))
        history=[]
        for file in sorted((run/'output').glob('snap_*.hdf5')):
            check(file);s=state(file)
            with h5py.File(file) as f:
                g=f['PartType0'];order=np.argsort(g['ParticleIDs'][:])
                s['e']=g['InternalEnergy'][:][order]
                assert np.count_nonzero(g['VertexVelocity'][:])==0
            assert all(np.isfinite(s[k]).all() for k in ('xy','rho','p','v','e','w','mass'))
            assert min(s['rho'].min(),s['p'].min(),s['mass'].min())>0
            np.testing.assert_allclose(s['p'],(gamma-1)*s['rho']*s['e'],rtol=1e-12,atol=1e-14)
            if history:
                assert np.array_equal(s['xy'],history[0]['xy'])
                assert np.array_equal(s['id'],history[0]['id'])
            s['snapshot']=str(file);history.append(s)
        assert len(history)==5
        np.testing.assert_allclose([s['time'] for s in history],np.linspace(0,c['end'],5),rtol=0,atol=2e-15)
        a,s=history[0],history[-1]
        assert s['time']==c['end']
        if c['problem']=='uniform':
            defect=max(float(np.max(abs(s[k]-a[k]))) for k in ('rho','p','v'))
            assert defect<1e-12
            gates.append(dict(method=c['method'],max_change=defect));continue
        nx=c['effective_Nx'];assert len(a['id'])==(2*nx)**2
        high=(a['xy'][:,0]>.5)&(a['xy'][:,0]<1.5)
        np.testing.assert_allclose(a['rho'],np.where(high,1.,.125),rtol=0,atol=1e-14)
        np.testing.assert_allclose(a['p'],np.where(high,1.,.1),rtol=0,atol=1e-14)
        assert np.count_nonzero(a['v'])==0
        if nx in initial:
            for k in ('id','xy','rho','p','v','mass','e'):assert np.array_equal(a[k],initial[nx][k]),(nx,k)
        else:initial[nx]=a
        mask=(s['xy'][:,0]>1)&(s['xy'][:,0]<2)
        x=s['xy'][mask,0]-1
        q=np.column_stack((s['rho'][mask],s['v'][mask,0],s['p'][mask],s['e'][mask]))
        ref,waves=exact(s['xy'][mask,0],s['time'])
        w=s['w'][mask]/s['w'][mask].sum();err=w@abs(q-ref)
        edges=np.linspace(0,1,129);ib=np.digitize(x,edges)-1
        count=np.bincount(ib,minlength=128)
        assert len(count)==128 and count.sum()==len(x) and count.min()>0
        means=np.array([q[ib==j].mean(axis=0) for j in range(128)])
        bx=(edges[1:]+edges[:-1])/2
        curves[(c['scheme'],nx)]=(x,q,bx,means)
        sync=re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*([\deE.+-]+),\s+Systemstep:\s*([\deE.+-]+)',log)
        dt=np.array([float(z[2]) for z in sync if float(z[2])>0])
        histories=[]
        for h in history:
            drift=(h['totals']-a['totals'])/np.array([a['totals'][0],a['totals'][0],a['totals'][0],a['totals'][3]])
            histories.append(dict(time=h['time'],normalized_conserved_drift=drift.tolist(),
                min_rho=float(h['rho'].min()),min_p=float(h['p'].min())))
        row=dict(scheme=c['scheme'],effective_Nx=nx,full_box_nodes=len(a['id']),tube_nodes=len(x),
            end_time=s['time'],rho_l1=float(err[0]),vx_l1=float(err[1]),p_l1=float(err[2]),e_l1=float(err[3]),
            vx_min=float(q[:,1].min()),vx_max=float(q[:,1].max()),rho_min=float(q[:,0].min()),rho_max=float(q[:,0].max()),
            p_min=float(q[:,2].min()),p_max=float(q[:,2].max()),vy_rms=float(np.sqrt(w@(s['v'][mask,1]**2))),
            steps=int(sync[-1][0]),dt_min=float(dt.min()),dt_max=float(dt.max()),
            steps_at_max_timestep=int(np.count_nonzero(dt>=campaign['max_timestep']*(1-1e-6))),
            max_mass_relative_drift=max(abs(z['normalized_conserved_drift'][0]) for z in histories),
            max_energy_relative_drift=max(abs(z['normalized_conserved_drift'][3]) for z in histories),
            history=histories,elapsed_seconds=status['seconds'],snapshot=s['snapshot'])
        rows.append(row)
        np.savetxt(root/f'{c["name"]}_bin_means.csv',np.column_stack((bx,means,count)),delimiter=',',
            header='xi,rho,vx,p,e,node_count',comments='')
    _,waves=exact(np.linspace(1,2,1001))
    summary=dict(test_name='Sod_2d_Morton',cases=rows,uniform_gates=gates,initial_states_matched=True,
        static_coordinates_unchanged=True,vertex_velocity_zero=True,forward_euler_stage_verified=True,
        gamma=gamma,final_time=.2,coordinates=campaign['coordinates'],wave_positions_xi=(waves-1).tolist(),
        first_mirror_collision_time=float(.5/((waves[-1]-1.5)/.2)),
        mean='128 equal xi bins; unweighted node mean; every tube node remains in scatter.',
        error_norm='Normalized median-dual area m/rho on original tube nodes; no binned errors.',
        limitations=campaign['limits'],input_hashes=inputs)
    write(root/'summary.json',summary)
    make_plots(root,curves,exact)
    for p,h in inputs.items():assert sha(p)==h,p
    if Path(__file__).resolve()!=root/'analyze.py':shutil.copy2(__file__,root/'analyze.py')
    write(root/'verification.json',dict(all_input_hashes_unchanged=True,uniform_gates=gates,
        all_six_runs_complete=True,all_saved_states_positive=True,all_raw_nodes_retained=True,
        expected_pdf_pages=2,visual_review='pending'))
    print(json.dumps([{k:v for k,v in row.items() if k not in ('history','snapshot')} for row in rows],indent=2))


def make_plots(root,curves,exact):
    figures=root/'figures';figures.mkdir(exist_ok=True)
    output=root/'output/pdf';output.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.linewidth':.8,
        'xtick.direction':'in','ytick.direction':'in','xtick.top':True,'ytick.right':True,'pdf.fonttype':42})
    raw=np.linspace(1,2,3001);reference,waves=exact(raw);xx=raw-1
    labels=[r'Density $\rho$',r'Velocity $v_x$',r'Pressure $p$',r'Specific internal energy $e$']
    styles={64:('#cc7a24','-'),128:('#2878af','--')}
    def panel(ax,scheme,field,xlim):
        for nx,(color,ls) in styles.items():
            x,q,bx,means=curves[(scheme,nx)]
            ax.scatter(x,q[:,field],s=3,color=color,alpha=.10,edgecolors='none',rasterized=True,zorder=1)
            ax.plot(bx,means[:,field],c=color,ls=ls,lw=1.45,label=rf'$N_x\simeq{nx}$',zorder=3)
        ax.plot(xx,reference[:,field],color='black',lw=1.15,label='Exact',zorder=4)
        ax.set(xlim=xlim,ylabel=labels[field]);ax.grid(color='.90',lw=.5)
        if xlim!=(0,1):
            values=[reference[(xx>=xlim[0])&(xx<=xlim[1]),field]]
            for nx in styles:
                x,q,_,_=curves[(scheme,nx)];values.append(q[(x>=xlim[0])&(x<=xlim[1]),field])
            low=min(v.min() for v in values);high=max(v.max() for v in values)
            pad=.07*(high-low);ax.set_ylim(low-pad,high+pad)
    figs=[]
    fig,axs=plt.subplots(4,2,figsize=(9.3,10.1),sharex=True,sharey='row',layout='constrained')
    for j,scheme in enumerate(('N','LDA')):
        for k in range(4):panel(axs[k,j],scheme,k,(0,1))
        axs[0,j].set_title(f'{scheme}, forward Euler',fontsize=11)
        axs[0,j].legend(loc='upper right',fontsize=9,framealpha=.9)
        axs[-1,j].set_xlabel(r'$x$')  # x = X - 1 for raw 1 < X < 2.
    fig.suptitle(r'Sod_2d_Morton: static glass, $\gamma=5/3$, $t=0.2$',fontsize=13)
    figs.append(('Sod_2d_Morton_profiles',fig))
    fig,axs=plt.subplots(2,2,figsize=(9.3,6.7),sharex=True,sharey='row',layout='constrained')
    for j,scheme in enumerate(('N','LDA')):
        for k in (0,1):
            panel(axs[k,j],scheme,k,(.43,.94))
            for wave in waves[[1,2,4]]-1:axs[k,j].axvline(wave,c='.6',ls=':',lw=.65,zorder=0)
        axs[0,j].set_title(scheme,fontsize=11)
        axs[0,j].legend(loc='upper right',fontsize=9,framealpha=.9)
        axs[1,j].set_xlabel(r'$x$')
    fig.suptitle(r'Sod_2d_Morton: contact and shock, $t=0.2$',fontsize=13)
    figs.append(('Sod_2d_Morton_zoom',fig))
    with PdfPages(output/'Sod_2d_Morton_review.pdf') as pdf:
        for name,fig in figs:
            fig.savefig(figures/f'{name}.png',dpi=180)
            pdf.savefig(fig)
            plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    analyze(p.parse_args().root.resolve())
