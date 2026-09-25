#!/usr/bin/env python3
"""Separate fixed-connectivity time order from endpoint remeshing errors.

Reference for fixed connectivity: DOP853 on the independently defined limiting
ODE G=(2I-D^-1 M)(-D^-1 R). This is v for the N/lumped choice.
Reference with remeshing: the same candidate at 2048 steps, with identical
prescribed endpoint coordinates. These comparisons do not prove asymptotic
order across discontinuous topology changes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

import numpy as np
from scipy.integrate import solve_ivp
import explore_true_ale_split as base


def fixed_connection(method,motion):
    x=base.points(12); mesh=base.triangulate(x)
    v=base.velocities(x,motion); u0=base.exact(x,0)
    tend=.25
    def current(t):
        return base.Mesh(mesh.ids,mesh.p+t*v[mesh.ids],mesh.n)
    def rhs(t,u):
        s=base.slab(current(t),v,0.)
        rate=-base.residual(s,u,method)/s.m1
        return 2*rate-base.mass_action(s,rate,method)/s.m1
    reference=solve_ivp(rhs,[0,tend],u0,method='DOP853',rtol=1e-12,atol=1e-13)
    assert reference.success
    w=current(tend).mass
    rows=[]
    for steps in (32,64,128,256,512):
        u=u0.copy(); dt=tend/steps
        for step in range(steps):
            u=base.end(base.begin(current(step*dt),v,u,dt,method),method)
        error=float(w@abs(u-reference.y[:,-1]))
        rows.append(dict(steps=steps,dt=dt,L1_to_ODE=error,
                         observed_p=float(np.log2(rows[-1]['L1_to_ODE']/error)) if rows else None))
    return dict(method=method,motion=motion,reference_evaluations=reference.nfev,rows=rows)


def remeshing(method):
    cases=[]; states=[]
    for steps in (64,128,256,512,2048):
        row,state=base.simulate(12,steps,.5,method,'remap')
        cases.append(row); states.append(state)
    reference=states[-1]
    assert all(np.max(abs(s['x']-reference['x']))<1e-14 for s in states)
    errors=[float(reference['mass']@abs(s['u']-reference['u'])) for s in states[:-1]]
    for i,row in enumerate(cases[:-1]):
        row['L1_to_2048_steps']=errors[i]
        row['observed_p']=float(np.log2(errors[i-1]/errors[i])) if i else None
    return dict(method=method,reference_steps=2048,cases=cases)


def main(output):
    output.mkdir(parents=True,exist_ok=False)
    sources=[Path(__file__).resolve(),Path(base.__file__).resolve()]
    for source in sources:
        shutil.copy2(source,output/source.name)
    (output/'provenance.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
    result=dict(fixed=[],remeshed=[]); start=time.monotonic()
    for method in ('n','lda_f1'):
        for motion in ('translation','deform'):
            row=fixed_connection(method,motion)
            result['fixed'].append(row)
            print(json.dumps(row),flush=True)
        row=remeshing(method)
        result['remeshed'].append(row)
        print(json.dumps(row),flush=True)
    result['elapsed_seconds']=time.monotonic()-start
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    main(parser.parse_args().output.resolve())
