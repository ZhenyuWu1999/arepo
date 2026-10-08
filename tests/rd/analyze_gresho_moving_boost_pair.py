#!/usr/bin/env python3
"""Audit and plot N/LDA moving glass Gresho at matched boosts0/10 and t3."""
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
    states, rows, sequences, gates = {}, [], [], []
    provenance = []
    for boost in (0, 10):
        archive = root / f'boost{boost}'
        campaign = json.loads((archive / 'campaign.json').read_text())
        source = json.loads((archive / 'source_provenance.json').read_text())
        assert sha(archive / 'source.tar') == source['source_tar_sha256']
        for phase in ('uniform', 'pilot'):
            results = json.loads((archive / f'gate_{phase}.json').read_text())
            assert len(results) == 2 and all(r['passed'] for r in results)
            gates.extend([dict(r,boost=boost) for r in results])
        for case in campaign['cases']:
            if case['horizon'] != 'science':
                continue
            assert case['mesh'] == 'moving' and case['frame'] == 'lab'
            assert case['end'] == 3. and case['boost'] == boost
            method, scheme = case['method'], case['scheme']
            folder = archive / 'runs' / case['name']
            artifact = archive / 'artifacts' / method
            meta = json.loads((artifact / 'provenance.json').read_text())
            status = json.loads((folder / 'run_status.json').read_text())
            assert sha(artifact / 'Arepo') == meta['binary_sha256'] == status['binary_sha256']
            assert sha(artifact / 'Config.sh') == meta['config_sha256']
            assert sha(case['ic']) == case['ic_sha256'] and sha(folder / 'param.txt') == case['param_sha256']
            header = (artifact / 'arepoconfig.h').read_text()
            assert '#define RD_ELEMENT_COMOVING_FRAME' not in header
            assert '#define VORONOI_STATIC_MESH' not in header
            assert '#define RD_ALE_EQUALSTEP' in header
            assert '#define RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC' not in header
            log = (folder / 'run.log').read_text(errors='replace')
            assert status['returncode'] == 0 and 'bye!' in log and 'TERMINATE:' not in log
            sync = re.findall(r'Sync-Point\s+(\d+),\s+Time:\s*([\deE.+-]+),\s+Systemstep:\s*([\deE.+-]+)', log)
            assert int(sync[-1][0]) == 16384 and len(sync) == 16385
            sequence = [s[2] for s in sync[1:]]
            assert set(sequence) == {'0.000183105'}
            sequences.append(sequence)
            paths = sorted((folder / 'output').glob('snap_*.hdf5'))
            snapshots = [state(p) for p in paths]
            assert [s['time'] for s in snapshots] == [0., .75, 1.5, 2.25, 3.]
            opening = snapshots[0]
            history = []
            for s, path in zip(snapshots, paths):
                assert np.array_equal(s['id'], opening['id'])
                assert all(np.isfinite(s[k]).all() for k in ('xy', 'v', 'rho', 'p', 'mass'))
                assert min(s['rho'].min(), s['p'].min(), s['mass'].min()) > 0
                with h5py.File(path) as f:
                    order = np.argsort(f['PartType0/ParticleIDs'][:])
                    s['vertex_velocity'] = f['PartType0/VertexVelocity'][:][order, :2]
                radius, vphi, exact = profile(s, boost)
                w = s['mass']/s['mass'].sum()
                wa = s['w']/s['w'].sum()
                d = (s['xy']-[boost*s['time'],0.]) % 1. - .5
                exact_v = np.column_stack((-d[:,1],d[:,0])) * (exact/np.maximum(radius,1e-100))[:,None]
                history.append(dict(time=s['time'], snapshot_sha256=sha(path),
                    vphi_l1_mass=float(w@abs(vphi-exact)), vphi_l1_area=float(wa@abs(vphi-exact)),
                    velocity_l1_mass=float(w@np.linalg.norm(s['v']-[boost,0.]-exact_v,axis=1)),
                    vphi_peak=float(vphi.max()), rho_min=float(s['rho'].min()), p_min=float(s['p'].min()),
                    mass_relative_drift=float((s['totals'][0]-opening['totals'][0])/opening['totals'][0]),
                    energy_relative_drift=float((s['totals'][3]-opening['totals'][3])/opening['totals'][3])))
            diagnostics = {}
            for key in ('min_pivot_ratio','cons_defect_abs','cons_defect_rel','svd_fallback','f1_lumped'):
                values = [float(v) for v in re.findall(r'\b'+key+r'=([+\-\deE.]+)',log)]
                if values:
                    diagnostics[key] = dict(min=min(values),max=max(values),last=values[-1])
            states[(scheme,boost)] = snapshots
            rows.append(dict(scheme=scheme,boost=boost,complete=True,steps=16384,actual_dt=3/16384,
                             history=history,final=history[-1],diagnostics=diagnostics))
            provenance.append(dict(scheme=scheme,boost=boost,archive=str(archive),
                                   binary_sha256=meta['binary_sha256'],source_sha256=source['source_tar_sha256']))
    assert len(rows) == 4 and all(s==sequences[0] for s in sequences[1:])
    assert len({p['source_sha256'] for p in provenance}) == 1
    for scheme in ('N','LDA'):
        assert len({p['binary_sha256'] for p in provenance if p['scheme']==scheme}) == 1
    pairs = []
    for scheme in ('N','LDA'):
        for a,b in zip(states[(scheme,0)],states[(scheme,10)]):
            assert a['time']==b['time'] and np.array_equal(a['id'],b['id'])
            w = a['mass']/a['mass'].sum()
            dx = (b['xy']-a['xy']-[10*a['time'],0.]+.5)%1.-.5
            dv = b['v']-a['v']-[10.,0.]
            row = dict(scheme=scheme,time=a['time'],
                position_rms=float(np.sqrt(w@np.sum(dx**2,axis=1))),
                position_max=float(np.linalg.norm(dx,axis=1).max()),
                velocity_l1=float(w@np.linalg.norm(dv,axis=1)),
                velocity_max=float(np.linalg.norm(dv,axis=1).max()),
                vphi_l1=float(w@abs(profile(b,10)[1]-profile(a,0)[1])),
                rho_max=float(abs(b['rho']-a['rho']).max()),p_max=float(abs(b['p']-a['p']).max()),
                vertex_velocity_max_after_boost=float(np.linalg.norm(b['vertex_velocity']-a['vertex_velocity']-[10.,0.],axis=1).max()))
            pairs.append(row)
            if a['time']==0:
                assert row['position_max']==0 and row['velocity_max']<1e-13
                assert row['rho_max']<1e-13 and row['p_max']<1e-12
    for boost in (0,10):
        for key in ('id','xy','rho','v','p','mass'):
            assert np.array_equal(states[('N',boost)][0][key],states[('LDA',boost)][0][key])
    by = {(r['scheme'],r['boost']):r['final'] for r in rows}
    ratios = {scheme:by[(scheme,10)]['vphi_l1_mass']/by[(scheme,0)]['vphi_l1_mass'] for scheme in ('N','LDA')}
    write(root/'summary.json',dict(cases=rows,boost_pairs=pairs,boost10_over_boost0_error=ratios,
        gates=gates,provenance=provenance,actual_timestep_histories_identical=True,
        norm='All 2304 native nodes, final-mass weighted absolute azimuthal velocity error; separate area-weighted and vector velocity norms also saved.',
        recentering='Analytic periodic center (0.5+boost*t,0.5), subtract (boost,0) from velocity; no interpolation, fitted center or binning.',
        pair_scope='ID-matched boost-pair differences compare both mesh trajectory and fluid state; nodes do not remain at identical coordinates. Not an Eulerian field norm on common sample points.',
        limits='One resolution and endpoint; similar profile errors alone do not prove exact Galilean invariance.'))
    out = root/'output/pdf';out.mkdir(parents=True,exist_ok=True)
    figs = root/'figures';figs.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'pdf.fonttype':42,
                         'axes.spines.top':False,'axes.spines.right':False})
    fig,axes = plt.subplots(1,2,figsize=(10.6,5.2),sharex=True,sharey=True,layout='constrained')
    all_v = np.concatenate([profile(ss[-1],boost)[1] for (_,boost),ss in states.items()])
    ymin,ymax = min(-.05,float(all_v.min())-.03),max(1.08,float(all_v.max())+.03)
    rr = np.linspace(0,.71,1000)
    for ax,scheme,color in zip(axes,('N','LDA'),('#278449','#2672b5')):
        for boost in (0,10):
            r,vphi,_ = profile(states[(scheme,boost)][-1],boost)
            error = by[(scheme,boost)]['vphi_l1_mass']
            ax.scatter(r,vphi,s=10 if boost==0 else 12,marker='x' if boost==0 else '.',
                       color='#d17a19' if boost==0 else color,alpha=.45,linewidths=.55,rasterized=True,
                       label=f'Boost {boost}: $L_1={error:.5f}$')
        ax.plot(rr,np.where(rr<.2,5*rr,np.where(rr<.4,2-5*rr,0)),'k--',lw=1.3,label='Analytic')
        ax.set(title=scheme+' / '+('Roe' if scheme=='N' else 'Gauss3'),xlabel=r'Radius $r$',
               xlim=(0,.71),ylim=(ymin,ymax))
        ax.set_xticks([0,.2,.4,.6]);ax.grid(alpha=.15)
        ax.legend(loc='upper center',bbox_to_anchor=(.5,-.18),fontsize=9,frameon=False,markerscale=1.8)
    axes[0].set_ylabel(r'Azimuthal velocity $v_\varphi$')
    fig.suptitle(r'Moving-mesh Gresho: glass $48^2$, $t=3$'+'\nLaboratory-frame solver; bulk translation removed from profiles',fontsize=12)
    pdf = out/'gresho_glass48_t3_moving_boost0_10.pdf'
    fig.savefig(pdf,dpi=300);fig.savefig(figs/'gresho_glass48_t3_moving_boost0_10.png',dpi=180);plt.close(fig)
    for filename in (Path(__file__).name,'analyze_gresho_glass_boost_lab.py','run_n_gauss3_split.py'):
        shutil.copy2(Path(__file__).parent/filename,root/filename)
    write(root/'analysis_provenance.json',dict(script_sha256=sha(__file__),
        profile_helper_sha256=sha(Path(__file__).parent/'analyze_gresho_glass_boost_lab.py'),
        summary_sha256=sha(root/'summary.json'),pdf_sha256=sha(pdf)))
    for row in rows:print(row['scheme'],row['boost'],row['final'])
    print('Error ratios boost10/0:',ratios)
    for row in pairs:
        if row['time']==3:print('Boost-pair:',row)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
    analyze(parser.parse_args().root.resolve())
