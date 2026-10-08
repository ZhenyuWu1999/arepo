#!/usr/bin/env python3
"""Local Sod figure review from retained lab-frame N/Roe and LDA/Gauss3 runs."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil

import h5py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.tri as mtri
import numpy as np

from run_n_gauss3_split import sha, state, write

COLORS = {'N': '#278449', 'LDA': '#2672b5'}
EDGES = np.linspace(0., 1., 129)
LABELS = (r'Density $\rho$', r'Velocity $v_x$', r'Pressure $p$',
          r'Specific internal energy $e$')


def means(x, fields):
    index = np.digitize(x, EDGES) - 1
    counts = np.array([np.count_nonzero(index == k) for k in range(128)])
    out = np.full((128, 4), np.nan)
    for k, count in enumerate(counts):
        if count:
            out[k] = fields[index == k].mean(axis=0)
    return .5 * (EDGES[:-1] + EDGES[1:]), out, counts


def plot(source, output):
    output.mkdir(parents=True, exist_ok=False)
    pdfdir, pngdir = output/'output/pdf', output/'figures'
    pdfdir.mkdir(parents=True)
    pngdir.mkdir()
    inputs = {}

    def remember(path, expected=None):
        actual = sha(path)
        if expected is not None:
            assert actual == expected, str(path)
        inputs[str(path)] = actual

    for name in ('campaign.json', 'summary.json', 'source_provenance.json'):
        remember(source/name)
    campaign = json.loads((source/'campaign.json').read_text())
    previous = json.loads((source/'summary.json').read_text())
    provenance = json.loads((source/'source_provenance.json').read_text())
    remember(source/'source.tar', campaign['source_tar_sha256'])
    riemann = source/'source/examples/shocktube_1d/Riemann.py'
    remember(riemann, provenance['tracked_hashes']['examples/shocktube_1d/Riemann.py'])
    spec = importlib.util.spec_from_file_location('archived_riemann', riemann)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def exact(x, time):
        _, q, waves = module.RiemannProblem(np.asarray(x).copy(), .5,
            np.array([1., 0., 1.]), np.array([.125, 0., .1]), 1.4, time)
        return np.column_stack((q, q[:, 2]/(.4*q[:, 0]))), .5+waves

    curves, histories, rows = {}, {}, []
    for scheme in ('N', 'LDA'):
        case, = [c for c in campaign['cases']
                 if c['problem'] == 'sod' and c['scheme'] == scheme]
        saved, = [c for c in previous['cases']
                  if c['name'] == case['name'] and c['frame'] == 'lab']
        assert case['frame'] == 'lab' and case['ranks'] == 1
        folder = source/'runs'/case['name']
        artifact = source/'artifacts'/case['method']
        meta = json.loads((artifact/'provenance.json').read_text())
        status = json.loads((folder/'run_status.json').read_text())
        assert status['returncode'] == 0 and saved['complete']
        assert status['binary_sha256'] == meta['binary_sha256']
        assert meta['source_tar_sha256'] == campaign['source_tar_sha256']
        remember(artifact/'Arepo', meta['binary_sha256'])
        remember(artifact/'Config.sh', meta['config_sha256'])
        remember(source/'configs'/f"{case['method']}.sh", meta['config_sha256'])
        remember(folder/'param.txt', case['param_sha256'])
        remember(Path(case['ic']), case['ic_sha256'])
        for path in (artifact/'provenance.json', folder/'run_status.json', folder/'run.log'):
            remember(path)
        config = (artifact/'Config.sh').read_text().splitlines()
        assert 'RD_ALE_EQUALSTEP' in config and 'FORCE_EQUAL_TIMESTEPS' in config
        assert 'RD_ELEMENT_COMOVING_FRAME' not in config
        assert 'GAMMA=1.4' in config
        if scheme == 'N':
            assert 'N_SCHEME' in config and 'RD_ALE_SPLIT_MESH_VELOCITY' in config
            assert 'RD_ALE_CONTOUR_RESIDUAL' not in config
        else:
            assert 'LDA_SCHEME' in config and 'RD_ALE_CONTOUR_GAUSS=3' in config
        history = []
        for path in sorted((folder/'output').glob('snap_*.hdf5')):
            remember(path)
            s = state(path)
            with h5py.File(path) as f:
                order = np.argsort(f['PartType0/ParticleIDs'][:])
                s['e'] = f['PartType0/InternalEnergy'][:][order]
            assert len(s['id']) == 128**2
            assert all(np.isfinite(s[k]).all() for k in ('rho','v','p','e'))
            assert s['rho'].min() > 0 and s['p'].min() > 0
            np.testing.assert_allclose(s['p'], .4*s['rho']*s['e'], rtol=1e-12)
            s['snapshot'] = str(path)
            history.append(s)
        assert [s['time'] for s in history] == [0., .02, .04, .06, .08]
        histories[scheme] = history
        s = history[-1]
        selected = (s['xy'][:, 0] > .25) & (s['xy'][:, 0] < .75)
        x = 2*(s['xy'][selected, 0]-.25)
        q = np.column_stack((s['rho'][selected], s['v'][selected,0],
                             s['p'][selected], s['e'][selected]))
        ex, waves = exact(s['xy'][selected,0], s['time'])
        weights = s['w'][selected]/s['w'][selected].sum()
        errors = weights @ abs(q-ex)
        np.testing.assert_allclose(errors[:3],
            [saved[k] for k in ('rho_l1','vx_l1','p_l1')], rtol=0., atol=1e-14)
        bx, bq, count = means(x, q)
        assert count.sum() == len(x)
        np.savetxt(output/f'{scheme}_profiles.csv',
                   np.column_stack((x, q, weights)), delimiter=',',
                   header='xi,rho,vx,p,specific_internal_energy,normalized_dual_area', comments='')
        np.savetxt(output/f'{scheme}_bin_means.csv',
                   np.column_stack((bx, bq, count)), delimiter=',',
                   header='xi,rho,vx,p,specific_internal_energy,node_count', comments='')
        curves[scheme] = (x, q, bx, bq)
        rows.append(dict(scheme=scheme, residual=case['residual'], frame='lab',
            final_snapshot=s['snapshot'], final_snapshot_sha256=sha(s['snapshot']),
            total_nodes=len(s['id']), tube_nodes=len(x), time=s['time'], tube_time=2*s['time'],
            steps=saved['steps'], rho_l1=errors[0], vx_l1=errors[1], p_l1=errors[2],
            e_l1=errors[3], vx_min=float(q[:,1].min()), vx_max=float(q[:,1].max()),
            mass_relative_drift=saved['final']['mass_relative_drift'],
            energy_relative_drift=saved['final']['energy_relative_drift']))
    for field in ('id','xy','rho','p','v','mass','e'):
        assert np.array_equal(histories['N'][0][field], histories['LDA'][0][field])

    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
        'axes.linewidth':.8,'xtick.direction':'in','ytick.direction':'in',
        'xtick.top':True,'ytick.right':True,'pdf.fonttype':42})
    rawx = np.linspace(.25,.75,2401)
    ex, wave_x = exact(rawx,.08)
    exx = 2*(rawx-.25)
    contact, shock = 2*(wave_x[[2,4]]-.25)
    figures = []

    def panel(ax, field, xlim, ylim=None, wave_markers=False):
        for scheme in ('N','LDA'):
            x,q,bx,bq = curves[scheme]
            ax.scatter(x,q[:,field],s=3,alpha=.12,color=COLORS[scheme],
                       edgecolors='none',rasterized=True,zorder=1)
            ax.plot(bx,bq[:,field],color=COLORS[scheme],lw=1.4,
                    label=scheme,ls='-' if scheme=='N' else '-.',zorder=3)
        ax.plot(exx,ex[:,field],color='black',ls='--',lw=1.3,label='Analytic',zorder=4)
        ax.set(xlim=xlim,xlabel=r'Tube coordinate $\xi$',ylabel=LABELS[field])
        if ylim is not None:
            ax.set_ylim(ylim)
        ax.grid(color='.9',lw=.5)
        if wave_markers:
            for location in (contact,shock):
                if xlim[0] < location < xlim[1]:
                    ax.axvline(location,color='.6',lw=.7,ls=':',zorder=0)

    fig, axes = plt.subplots(2,2,figsize=(9.4,6.8),layout='constrained')
    for i,ax in enumerate(axes.flat):
        panel(ax,i,(0.,1.))
    axes[0,0].legend(loc='upper right',frameon=False,fontsize=9)
    fig.suptitle(r'Sod, moving glass, $N_x\simeq64$, $\tau=0.16$',fontsize=12)
    figures.append(('sod_profiles',fig))

    fig, axes = plt.subplots(2,2,figsize=(9.4,6.8),layout='constrained')
    regions=[(0,(.56,.71),(.22,.49),'Contact: density'),
             (0,(.70,.87),(.035,.31),'Shock: density'),
             (1,(.70,.87),(-.80,1.13),'Shock: velocity'),
             (2,(.70,.87),(.015,.345),'Shock: pressure')]
    for ax,(field,xlim,ylim,title) in zip(axes.flat,regions):
        panel(ax,field,xlim,ylim,wave_markers=True)
        ax.set_title(title,fontsize=10)
    axes[0,0].legend(loc='upper right',frameon=False,fontsize=8.5)
    fig.suptitle(r'Sod: contact and shock, $\tau=0.16$',fontsize=12)
    figures.append(('sod_contact_shock',fig))

    fig, axes = plt.subplots(2,3,figsize=(10,4.4),sharex=True,sharey=True,
                             layout='compressed')
    density_min = min(s['rho'].min() for h in histories.values() for s in h)
    density_max = max(s['rho'].max() for h in histories.values() for s in h)
    assert 0. < density_min < density_max < 1.1
    for row,scheme in enumerate(('N','LDA')):
        for col,index in enumerate((0,2,4)):
            ax=axes[row,col];s=histories[scheme][index]
            tri=mtri.Triangulation(s['xy'][:,0],s['xy'][:,1])
            im=ax.tripcolor(tri,s['rho'],shading='gouraud',cmap='viridis',
                            vmin=0.,vmax=1.1,rasterized=True)
            ax.set(xlim=(.25,.75),ylim=(.35,.65),aspect='equal',
                   xticks=(.25,.5,.75),yticks=(.35,.5,.65))
            ax.tick_params(labelsize=8)
            if row==0:
                ax.set_title(rf'$\tau={2*s["time"]:g}$',fontsize=10)
            if row==1:
                ax.set_xlabel(r'$x$')
            if col==0:
                ax.set_ylabel(scheme+'\n'+r'$y$')
    fig.colorbar(im,ax=axes.ravel().tolist(),fraction=.025,pad=.02,label=r'Density $\rho$')
    fig.suptitle(r'Sod: density evolution, moving glass $128^2$',fontsize=12)
    figures.append(('sod_density_evolution',fig))

    review=pdfdir/'sod_review.pdf'
    with PdfPages(review) as book:
        for stem,fig in figures:
            fig.savefig(pdfdir/f'{stem}.pdf',dpi=300)
            fig.savefig(pngdir/f'{stem}.png',dpi=190)
            book.savefig(fig,dpi=300)
            plt.close(fig)
    for path,expected in inputs.items():
        assert sha(path)==expected,path
    for file in (Path(__file__),Path(__file__).parent/'run_n_gauss3_split.py',riemann):
        shutil.copy2(file,output/file.name)
    summary=dict(source=str(source),source_base_commit=provenance['base_commit'],
        input_hashes=inputs,source_files_unchanged=True,cases=rows,
        initial_state_identical=True,all_saved_states_positive=True,
        gamma=1.4,left_state=[1.,0.,1.],right_state=[.125,0.,.1],
        coordinates='xi=2(x-0.25), tau=2t; profiles use all nodes with 0.25<x<0.75, full y extent.',
        resolution='Unit periodic box, 16384 initial glass nodes; h=1/128; tube length 0.5, effective initial Nx=64.',
        timestep='Common step within each run, CFL 0.08, dt cap 1/3000; N and LDA have different adaptive histories.',
        mean_definition='128 uniform bins on [0,1); unweighted node means, no smoothing. Faint scatter retains all selected nodes.',
        error_norm='Normalized current median-dual area (mass/rho), evaluated on individual nodes; not binned means.',
        analytic_wave_xi=dict(contact=float(contact),shock=float(shock)),
        density_map='Central strip x=[0.25,0.75], y=[0.35,0.65] of the periodic box. Gouraud interpolation on a Delaunay triangulation reconstructed from snapshot positions; not a native connectivity diagnostic. Fixed density scale [0,1.1].',
        limitations='One retained resolution/time, moving mesh only, lab-frame evaluation. No new solver runs or formal convergence study. LDA velocity undershoot and global conservation drift remain visible/in diagnostics.',
        review_pdf=str(review),review_pdf_sha256=sha(review),script_sha256=sha(__file__))
    write(output/'summary.json',summary)
    print(json.dumps(dict(output=str(output),cases=rows),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    plot(args.source.resolve(),args.output.resolve())
