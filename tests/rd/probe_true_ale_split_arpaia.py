#!/usr/bin/env python3
"""One-step algebra probes for Arpaia-based true old/new ALE stages.

For new connectivity let d=(S0+S1)/2-Smid. The endpoint total defect is
C_topology + sum_i d_i*(Utrial_i-Uold_i). An endpoint nodal correction
q_i -= d_i*(Utrial_i-Uold_i), followed by the previous topology correction,
cancels both. This is a proposed corrected variant, not original Arpaia,
and these checks establish neither positivity nor accuracy nor native gates.
"""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import explore_true_ale_split as base
import explore_true_ale_split_balance as topo
import explore_true_ale_split_euler as euler


def arpaia_slab(mesh, velocity, dt):
    s = base.slab(mesh, velocity, dt)
    amid = base.area((mesh.p+s.p1)/2)
    d = base.masses(mesh.ids, s.b-amid, mesh.n)
    divisor = s.m1-d
    assert divisor.min() > 0
    return replace(s, b=amid, m1=divisor), d


def step(mesh, new, velocity, dt, u, method, system, pairing):
    slab = arpaia_slab if pairing == 'arpaia' else lambda m,v,h: (base.slab(m,v,h), np.zeros(m.n))
    s0, _ = slab(mesh, velocity, dt)
    oldend = base.Mesh(mesh.ids, s0.p1, mesh.n)
    back = base.Mesh(new.ids, new.p-dt*velocity[new.ids], new.n)
    s1, d = slab(back, velocity, dt)
    if system == 'scalar':
        r0 = base.residual(s0, u, method)
        star = u-dt*r0/s0.m1
        trial = base.end((s0,u,star,r0), method, s1)
    else:
        r0,_,_ = euler.operator(s0, u, velocity, method)
        star = u-dt*r0/s0.m1[:,None]
        r1,m,_ = euler.operator(s1, star, velocity, method, star-u)
        trial = star-(m+.5*dt*(r0+r1))/s1.m1[:,None]
    old_u, trial_u = u.reshape(mesh.n,-1), trial.reshape(mesh.n,-1)
    old_total = np.sum(mesh.mass[:,None]*old_u, axis=0)
    qtrial = new.mass[:,None]*trial_u
    topology = np.sum(.5*(back.mass-mesh.mass+new.mass-oldend.mass)[:,None]*old_u, axis=0)
    nodal = d[:,None]*(trial_u-old_u)
    geometric = nodal.sum(axis=0)
    actual = qtrial.sum(axis=0)-old_total
    error = float(np.max(abs(actual-topology-geometric)))
    assert error < 2e-13*max(1., abs(old_total).max())
    # Independently apply only the previous topology correction.
    wrong = qtrial.copy()
    patches, removed = topo.cavities(mesh,new)
    for patch in patches:
        ids = np.array(patch)
        c = np.sum(.5*(back.mass-mesh.mass+new.mass-oldend.mass)[ids,None]*old_u[ids], axis=0)
        wrong[ids] -= (new.mass[ids]/new.mass[ids].sum())[:,None]*c
    remaining = wrong.sum(axis=0)-old_total
    assert np.max(abs(remaining-geometric)) < 2e-13*max(1.,abs(old_total).max())
    # This state now satisfies the existing topology-balance identity.
    geo_corrected = ((qtrial-nodal)/new.mass[:,None]).reshape(u.shape)
    final, event = topo.balance(mesh,oldend,back,new,u,geo_corrected)
    result = dict(pairing=pairing, topology_defect=topology.tolist(),
        geometric_defect=geometric.tolist(), measured_defect=actual.tolist(),
        formula_error=error, topology_only_remaining=remaining.tolist(),
        corrected_defect=event['corrected_defect'], removed_triangles=removed,
        max_nodal_geometry_gap=float(np.max(abs(d))),
        min_predictor=float(star.min()) if system=='scalar' else float(star[:,0].min()),
        min_final=float(final.min()) if system=='scalar' else float(final[:,0].min()))
    if system == 'euler':
        result['min_predictor_pressure'] = float(euler.pressure(star).min())
        result['min_final_pressure'] = float(euler.pressure(final).min())
    return result, final


def main(output):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(p).resolve() for p in (__file__,base.__file__,topo.__file__,euler.__file__)]
    for p in paths:
        shutil.copy2(p, output/p.name)
    (output/'provenance.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest()
        for p in paths},indent=2)+'\n')
    labels = base.points(12)
    velocity = base.velocities(labels,'deform')
    dt = 1/16
    old = base.triangulate(labels)
    fresh = base.triangulate((labels+dt*velocity)%1)
    retained = base.Mesh(old.ids,old.p+dt*velocity[old.ids],old.n)
    assert topo.cavities(old,fresh)[1] > 0
    results = []
    for method in ('n','lda_f1'):
        for system in ('scalar','euler'):
            for uniform in (False,True):
                u = base.exact(labels,0,uniform) if system=='scalar' else euler.exact(labels,0,'uniform' if uniform else 'vortex')
                for label,new in (('fixed_connectivity',retained),('changed_connectivity',fresh)):
                    a,ua = step(old,new,velocity,dt,u,method,system,'arpaia')
                    c,uc = step(old,new,velocity,dt,u,method,system,'campoli')
                    a.update(method=method,system=system,uniform=uniform,connectivity=label,
                        difference_to_corrected_campoli=float(np.max(abs(ua-uc))))
                    if uniform:
                        a['uniform_error'] = float(np.max(abs(ua-u)))
                        assert a['uniform_error'] < 2e-12
                    results.append(a)
                    np.savez_compressed(output/f'case_{len(results):02d}.npz', arpaia=ua,campoli=uc)
                    print(json.dumps(a),flush=True)
    assert max(abs(np.array(r['topology_only_remaining'])).max() for r in results
               if r['connectivity']=='fixed_connectivity' and not r['uniform']) > 1e-10
    result = dict(scope='Independent one-step identity check, not a stability or convergence campaign',
        nodes=144,triangles=288,dt=dt,cases=results)
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    main(parser.parse_args().output.resolve())
