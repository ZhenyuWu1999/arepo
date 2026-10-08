#!/usr/bin/env python3
"""Audit all accepted stages and endpoint budgets of the optional Rusanov runs."""
import argparse
import json
from pathlib import Path
import re
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import binned_statistic

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/'tests/rd'))
from run_n_gauss3_split import sha, write, state
from analyze import similarity


def analyze(root):
    cases = json.loads((root/'campaign.json').read_text())['cases']
    output = root/'analysis'; output.mkdir(exist_ok=True)
    rows, final = [], {}
    for c in cases:
        folder = root/'runs'/c['name']
        if not (folder/'run_status.json').exists():
            continue
        artifact = root/'artifacts'/c['method']
        meta = json.loads((artifact/'provenance.json').read_text())
        assert sha(artifact/'Arepo') == meta['binary_sha256']
        assert sha(artifact/'Config.sh') == meta['config_sha256']
        assert sha(c['ic']) == c['ic_sha256'] and sha(folder/'param.txt') == c['param_sha256']
        if c['method'] != 'baseline_reference':
            assert meta['source_tar_sha256'] == sha(root/'source.tar')
        status = json.loads((folder/'run_status.json').read_text())
        log = (folder/'run.log').read_text(errors='replace')
        stages = np.array([[float(x) for x in match] for match in re.findall(
            r'RD-RUSANOV time=(\S+) stage=(\d) rho_min=(\S+) internal_min=(\S+) CFL_max=(\S+) b_min=(\S+)', log)])
        row = dict(name=c['name'], returncode=status['returncode'], method=c['method'], group=c['group'],
                   failures=[line for line in log.splitlines() if 'TERMINATE' in line], snapshots=[])
        if len(stages):
            assert np.all(np.isfinite(stages)) and np.all(stages[:,2:4]>0)
            assert np.all(stages[:,4]<=1) and np.all((stages[:,5]>0)&(stages[:,5]<=1))
            row.update(stages=len(stages), stage_rho_min=float(stages[:,2].min()),
                stage_internal_min=float(stages[:,3].min()), CFL_max=float(stages[:,4].max()),
                b_min=float(stages[:,5].min()), last_checked_time=float(stages[-1,0]))
        snaps = sorted((folder/'output').glob('snap_*.hdf5'))
        a = state(snaps[0])
        for snap in snaps:
            b = state(snap)
            assert np.array_equal(a['id'], b['id'])
            assert all(np.all(np.isfinite(b[k])) for k in ('rho','p','v','mass','xy'))
            assert all(np.all(b[k]>0) for k in ('rho','p','mass'))
            if c['mesh'] == 'static':
                assert np.array_equal(a['xy'], b['xy'])
            row['snapshots'].append(dict(file=str(snap), sha256=sha(snap), time=b['time'],
                rho_min=float(b['rho'].min()), rho_max=float(b['rho'].max()), p_min=float(b['p'].min()),
                mass_relative=float(b['totals'][0]/a['totals'][0]-1),
                energy_relative=float(b['totals'][3]/a['totals'][3]-1),
                momentum_absolute=(b['totals'][1:3]-a['totals'][1:3]).tolist()))
        row['completed'] = status['returncode']==0 and abs(b['time']-c['end'])<1e-12
        if row['completed'] and c['method'].startswith('Rusanov') and c['group']!='uniform':
            final[c['name']] = b
        rows.append(row)
    write(output/'verification.json', dict(cases=rows, unique_snapshots=len({s['file'] for r in rows for s in r['snapshots']})))
    for r in rows:
        print(r['name'], r['completed'], {k:r['snapshots'][-1][k] for k in ('time','rho_min','rho_max','energy_relative','mass_relative')})
    plt.rcParams.update({'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False})
    reference = similarity(root, .05)
    for group in ('nearest21','disk005'):
        if not any(name.startswith(group) for name in final):
            continue
        fig, axes = plt.subplots(1,3, figsize=(12,3.9), layout='constrained')
        bins=np.linspace(0,.45,91); mid=(bins[1:]+bins[:-1])/2
        for mesh,color in [('static','#c66b37'),('moving','#287bad')]:
            name=f'{group}_Rusanov_{mesh}'
            if name not in final: continue
            s=final[name]; delta=(s['xy']-.5+.5)%1-.5; radius=np.linalg.norm(delta,axis=1)
            vr=np.sum(delta*s['v'],axis=1)/np.maximum(radius,1e-30)
            for ax,key,values,label in zip(axes,('rho','vr','p'),(s['rho'],vr,s['p']),('$\\rho$','$v_r$','$p$')):
                ax.scatter(radius,values,s=2,alpha=.055,color=color,rasterized=True)
                means=binned_statistic(radius,values,statistic='mean',bins=bins)[0]
                ax.plot(mid,means,color=color,lw=1.5,ls='-' if mesh=='moving' else '--',label=mesh.capitalize())
                ax.set(xlim=(0,.4),xlabel='Radius',ylabel=label); ax.grid(alpha=.15)
        for ax,key,exterior in zip(axes,('rho','vr','p'),(1.,0.,1e-6)):
            ax.plot(np.r_[reference['r'],reference['shock'],.45],np.r_[reference[key],exterior,exterior],
                    color='black',ls=':',lw=1.5,label='2D Sedov')
        axes[0].legend(fontsize=9)
        seed='21 heated nodes' if group=='nearest21' else '130 heated nodes, $r_\\mathrm{inj}=0.05$'
        fig.suptitle('Sedov blast: Rusanov RD, glass $128^2$, $t=0.05$\n'+seed)
        fig.savefig(output/f'{group}_profiles.png',dpi=350);plt.close(fig)
        fig, axes=plt.subplots(1,2,figsize=(9,4.4),layout='constrained')
        for ax,mesh in zip(axes,('static','moving')):
            name=f'{group}_Rusanov_{mesh}'
            if name not in final: ax.set_visible(False);continue
            s=final[name]
            im=ax.tripcolor(s['xy'][:,0],s['xy'][:,1],s['rho'],shading='gouraud',cmap='magma',vmin=0,vmax=4)
            ax.add_patch(plt.Circle((.5,.5),reference['shock'],fill=False,color='cyan',lw=.9,ls='--'))
            ax.set(xlim=(.12,.88),ylim=(.12,.88),xlabel='x',ylabel='y',aspect='equal',title=mesh.capitalize())
        fig.colorbar(im,ax=axes.tolist(),shrink=.85,label='$\\rho$')
        fig.suptitle('Rusanov RD, $t=0.05$; '+seed+'\nDashed circle: cylindrical similarity shock')
        fig.savefig(output/f'{group}_density.png',dpi=300);plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
    analyze(parser.parse_args().root.resolve())
