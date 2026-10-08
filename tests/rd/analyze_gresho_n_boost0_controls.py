#!/usr/bin/env python3
"""Compare matched static/moving N at boosts0/10 and audit boost sensitivity."""
import argparse
import json
from pathlib import Path
import re
import shutil

import h5py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from run_n_gauss3_split import state, sha, write
from analyze_gresho_glass_boost_lab import profile


def analyze(root):
    reuse = json.loads((root / 'reuse_provenance.json').read_text())
    base = Path(reuse['base_archive'])
    states, rows = {}, []
    for boost, archive in ((0, root), (10, base)):
        campaign = json.loads((archive / 'campaign.json').read_text())
        for case in campaign['cases']:
            if case['scheme'] != 'N' or case['horizon'] != 'science':
                continue
            method = case['method']
            folder = archive / 'runs' / case['name']
            status = json.loads((folder / 'run_status.json').read_text())
            artifact = archive / 'artifacts' / method
            assert status['returncode'] == 0 and sha(artifact / 'Arepo') == status['binary_sha256']
            assert sha(artifact / 'Arepo') == sha(base / 'artifacts' / method / 'Arepo')
            assert sha(folder / 'param.txt') == case['param_sha256'] and sha(case['ic']) == case['ic_sha256']
            log = (folder / 'run.log').read_text(errors='replace')
            assert 'bye!' in log and 'TERMINATE:' not in log
            sync = re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*([\deE.+-]+),\s+Systemstep:\s*([\deE.+-]+)', log)
            assert int(sync[-1][0]) == 4096
            assert set(s[2] for s in sync[1:]) == {'0.000244141'}
            paths = sorted((folder / 'output').glob('snap_*.hdf5'))
            snapshots = [state(p) for p in paths]
            assert [s['time'] for s in snapshots] == [0., .5, 1.]
            history = []
            for s, path in zip(snapshots, paths):
                assert np.array_equal(s['id'], snapshots[0]['id'])
                assert all(np.isfinite(s[k]).all() for k in ('xy','rho','p','v','mass'))
                assert min(s['rho'].min(), s['p'].min(), s['mass'].min()) > 0
                if case['mesh'] == 'static':
                    assert np.array_equal(s['xy'], snapshots[0]['xy'])
                radius, vp, exact = profile(s, boost)
                w = s['mass'] / s['mass'].sum()
                wa = s['w'] / s['w'].sum()
                with h5py.File(path) as f:
                    order = np.argsort(f['PartType0/ParticleIDs'][:])
                    s['vertex_velocity'] = f['PartType0/VertexVelocity'][:][order, :2]
                d = (s['xy'] - [boost*s['time'], 0.]) % 1. - .5
                exact_v = np.column_stack((-d[:,1],d[:,0])) * (exact/np.maximum(radius,1e-100))[:,None]
                history.append(dict(time=s['time'], snapshot_sha256=sha(path),
                    vphi_l1_mass=float(w@abs(vp-exact)), vphi_l1_area=float(wa@abs(vp-exact)),
                    velocity_l1_mass=float(w@np.linalg.norm(s['v']-[boost,0.]-exact_v,axis=1)),
                    vphi_peak=float(vp.max()), rho_min=float(s['rho'].min()), p_min=float(s['p'].min()),
                    mass_relative_drift=float((s['totals'][0]-snapshots[0]['totals'][0])/snapshots[0]['totals'][0]),
                    energy_relative_drift=float((s['totals'][3]-snapshots[0]['totals'][3])/snapshots[0]['totals'][3]),
                    mean_fluid_mesh_relative_speed=float(w@np.linalg.norm(s['v']-s['vertex_velocity'],axis=1))))
            states[(case['mesh'], boost)] = snapshots
            rows.append(dict(mesh=case['mesh'], boost=boost, actual_dt=1/4096, steps=4096,
                             archive=str(archive), binary_sha256=status['binary_sha256'], history=history,
                             final=history[-1]))
    pairs = []
    for mesh in ('static', 'moving'):
        for a, b in zip(states[(mesh,0)], states[(mesh,10)]):
            assert a['time'] == b['time'] and np.array_equal(a['id'],b['id'])
            w = a['mass']/a['mass'].sum()
            dx = (b['xy']-a['xy']-[10*a['time'],0.]+.5)%1.-.5
            dv = b['v']-a['v']-[10.,0.]
            dra = profile(a,0)[1]
            drb = profile(b,10)[1]
            result = dict(mesh=mesh,time=a['time'],
                position_rms=float(np.sqrt(w@np.sum(dx**2,axis=1))),
                position_max=float(np.linalg.norm(dx,axis=1).max()),
                velocity_l1=float(w@np.linalg.norm(dv,axis=1)),
                velocity_max=float(np.linalg.norm(dv,axis=1).max()),
                vphi_l1=float(w@abs(dra-drb)),
                rho_max=float(abs(b['rho']-a['rho']).max()), p_max=float(abs(b['p']-a['p']).max()),
                mass_max=float(abs(b['mass']-a['mass']).max()),
                vertex_velocity_max_after_boost=float(np.linalg.norm(b['vertex_velocity']-a['vertex_velocity']-[10,0],axis=1).max()))
            pairs.append(result)
            if a['time'] == 0:
                assert result['position_max'] == 0 and result['velocity_max'] < 1e-13
                assert result['rho_max'] < 1e-13 and result['p_max'] < 1e-12
    by = {(r['mesh'],r['boost']):r['final'] for r in rows}
    ratios = dict(moving10_over_static0=by[('moving',10)]['vphi_l1_mass']/by[('static',0)]['vphi_l1_mass'],
                  moving10_over_moving0=by[('moving',10)]['vphi_l1_mass']/by[('moving',0)]['vphi_l1_mass'],
                  static10_over_static0=by[('static',10)]['vphi_l1_mass']/by[('static',0)]['vphi_l1_mass'])
    write(root/'summary.json',dict(cases=rows,boost_pairs=pairs,ratios=ratios,
        norm='All native nodes, final mass weights for analytic error; boost-pair norms use boost0 masses and particle IDs.',
        pair_scope='Moving ID pairs also have small coordinate differences: joint mesh/state covariance test, not a field norm at identical spatial sample points.',
        invariance_test='Compare moving0 against moving10 after subtracting 10*t from x and 10 from vx; also compare mesh trajectories. Static0 and moving10 have different mesh-relative flows.',
        limits='No convergence test, temporal refinement or mechanism isolation. No claim of strict invariance from similar profile errors.'))
    out=root/'output/pdf';out.mkdir(parents=True,exist_ok=True)
    figs=root/'figures';figs.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'pdf.fonttype':42,
                         'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(10.6,4.5),sharex=True,sharey=True,layout='constrained')
    rr=np.linspace(0,.71,1000)
    for ax,mesh in zip(axes,('static','moving')):
        for boost,color,marker in ((0,'#d17a19','x'),(10,'#278449','.')):
            r,vp,_=profile(states[(mesh,boost)][-1],boost)
            error=by[(mesh,boost)]['vphi_l1_mass']
            ax.scatter(r,vp,s=10 if boost==0 else 12,marker=marker,color=color,
                       alpha=.45,linewidths=.55,rasterized=True,
                       label=f'Boost {boost}: $L_1={error:.5f}$')
        ax.plot(rr,np.where(rr<.2,5*rr,np.where(rr<.4,2-5*rr,0)),'k--',lw=1.3,label='Analytic')
        ax.set(title=mesh.capitalize()+' mesh',xlabel=r'Radius $r$',xlim=(0,.71),ylim=(-.06,1.14))
        ax.set_xticks([0,.2,.4,.6]);ax.grid(alpha=.15)
        ax.legend(loc='upper right',fontsize=9,markerscale=1.8)
    axes[0].set_ylabel(r'Azimuthal velocity $v_\varphi$')
    fig.suptitle(r'N / Roe: Gresho glass $48^2$, $t=1$, matched $\Delta t=1/4096$'+'\nLaboratory-frame solver; bulk translation removed from profiles',fontsize=12)
    pdf=out/'gresho_n_glass_boost0_10_static_moving.pdf'
    fig.savefig(pdf,dpi=300);fig.savefig(figs/'gresho_n_glass_boost0_10_static_moving.png',dpi=180);plt.close(fig)
    for filename in (Path(__file__).name,'analyze_gresho_glass_boost_lab.py'):
        shutil.copy2(Path(__file__).parent/filename,root/filename)
    write(root/'analysis_provenance.json',dict(script_sha256=sha(__file__),
        profile_helper_sha256=sha(Path(__file__).parent/'analyze_gresho_glass_boost_lab.py'),
        summary_sha256=sha(root/'summary.json'),pdf_sha256=sha(pdf)))
    for row in rows:print(row['mesh'],row['boost'],row['final'])
    print('Ratios',ratios)
    print('Moving boost-pair',next(p for p in pairs if p['mesh']=='moving' and p['time']==1))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
    analyze(parser.parse_args().root.resolve())
