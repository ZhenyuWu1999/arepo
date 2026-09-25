#!/usr/bin/env python3
"""Experimental old/new-connectivity GL/F1 with a derived patch balance term.

If the first residual is assembled on old forward geometry and the second
residual/mass on new backward geometry, the extensive total defect is

 E = sum_i 0.5*(S_new_at_start-S_old_at_start
                + S_new_at_end-S_old_at_end)_i * Uold_i.

Subtract that component vector within each changed cavity using weights that
sum to one. This establishes conservation and uniform-state preservation;
it does NOT establish stability, positivity, F1 consistency or time order.
No extra hydrodynamic sweep is used. This is a newly derived experiment,
not the published Campoli scheme across a topology change.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

import numpy as np
import explore_true_ale_split as base
import explore_true_ale_split_euler as euler


def cavities(old,new):
    a={tuple(sorted(row)):i for i,row in enumerate(old.ids)}
    b={tuple(sorted(row)):i for i,row in enumerate(new.ids)}
    gone=[a[k] for k in a.keys()-b.keys()]
    born=[b[k] for k in b.keys()-a.keys()]
    parent=np.arange(old.n)
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]]; i=parent[i]
        return int(i)
    for row in np.concatenate((old.ids[gone],new.ids[born])):
        for j in row[1:]:
            parent[find(j)]=find(row[0])
    groups={}
    for i in set(old.ids[gone].ravel()) | set(new.ids[born].ravel()):
        groups.setdefault(find(i),[]).append(int(i))
    return list(groups.values()),len(gone)


def balance(old0,old1,new0,new1,u0,trial):
    n=old0.n
    old_u=u0.reshape(n,-1)
    q=new1.mass[:,None]*trial.reshape(n,-1)
    d0=new0.mass-old0.mass
    d1=new1.mass-old1.mass
    expected=np.sum(.5*(d0+d1)[:,None]*old_u,axis=0)
    old_total=np.sum(old0.mass[:,None]*old_u,axis=0)
    measured=q.sum(axis=0)-old_total
    defect_error=float(np.max(abs(measured-expected)))
    assert defect_error < 2e-12*max(1.,float(abs(old_total).max())), (measured,expected)
    groups,removed=cavities(old0,new1)
    for group in groups:
        idx=np.array(group)
        assert abs(d0[idx].sum())<3e-14 and abs(d1[idx].sum())<3e-14
        mass=new1.mass[idx]
        local=np.sum(.5*(d0+d1)[idx,None]*old_u[idx],axis=0)
        q[idx]-=(mass/mass.sum())[:,None]*local
    error=float(np.max(abs(q.sum(axis=0)-old_total)))
    assert error < 2e-12*max(1.,float(abs(old_total).max())),error
    return (q/new1.mass[:,None]).reshape(trial.shape),dict(
        removed=removed,patches=len(groups),max_patch=max(map(len,groups),default=0),
        measured_defect=float(np.max(abs(measured))),formula_error=defect_error,
        corrected_defect=error)


def run(n,steps,tend,method,problem,system='scalar',apply_balance=True):
    labels=base.points(n); v=base.velocities(labels,'deform')
    mesh=base.triangulate(labels)
    def initial(x,t):
        return euler.exact(x,t,problem) if system=='euler' else base.exact(x,t,problem=='uniform')
    u=initial(labels,0); old_total=np.sum(mesh.mass[:,None]*u.reshape(mesh.n,-1),axis=0)
    scale=np.array([old_total[0]]*3+[old_total[3]]) if system=='euler' else old_total
    maxcons=maxuniform=maxformula=maxraw=0.; minimum=1e99; minp=1e99
    events=[]
    dt=tend/steps
    for step in range(steps):
        s0=base.slab(mesh,v,dt)
        if system=='euler':
            r0,_,_=euler.operator(s0,u,v,method)
            star=u-dt*r0/s0.m1[:,None]
        else:
            r0=base.residual(s0,u,method)
            star=u-dt*r0/s0.m1
        # True predictor above; exactly one new mesh below.
        x=(labels+(step+1)*dt*v)%1
        new=base.triangulate(x)
        oldend=base.Mesh(mesh.ids,s0.p1,mesh.n)
        back=base.Mesh(new.ids,new.p-dt*v[new.ids],new.n)
        s1=base.slab(back,v,dt)
        if system=='euler':
            r1,m,_=euler.operator(s1,star,v,method,star-u)
            trial=star-(m+.5*dt*(r0+r1))/s1.m1[:,None]
        else:
            trial=base.end((s0,u,star,r0),method,s1)
        if apply_balance:
            final,event=balance(mesh,oldend,back,new,u,trial)
        else:
            final=trial
            groups,removed=cavities(mesh,new)
            event=dict(removed=removed,formula_error=0.,measured_defect=0.,max_patch=max(map(len,groups),default=0))
        events.append(event)
        if system=='euler':
            minimum=min(minimum,float(star[:,0].min()),float(final[:,0].min()))
            minp=min(minp,float(euler.pressure(star).min()),float(euler.pressure(final).min()))
        else:
            minimum=min(minimum,float(star.min()),float(final.min()))
        u,mesh=final,new
        current=np.sum(mesh.mass[:,None]*u.reshape(mesh.n,-1),axis=0)
        maxcons=max(maxcons,float(np.max(abs(current-old_total)/scale)))
        if problem=='uniform':
            maxuniform=max(maxuniform,float(np.max(abs(u-initial(x,0)))))
        maxformula=max(maxformula,event['formula_error']); maxraw=max(maxraw,event['measured_defect'])
    target=initial(x,tend)
    component=abs(u[:,0]-target[:,0]) if system=='euler' else abs(u-target)
    result=dict(system=system,method=method,problem=problem,balanced=apply_balance,n=n,nodes=n*n,
                steps=steps,end=tend,dt=dt,relative_conservation=maxcons,formula_error=maxformula,
                max_uncorrected_step_defect=maxraw,uniform_error=maxuniform if problem=='uniform' else None,
                min_density_or_scalar=minimum,min_pressure=minp if system=='euler' else None,
                L1=float(mesh.mass@component),flip_steps=sum(e['removed']>0 for e in events),
                removed_triangles=sum(e['removed'] for e in events),max_patch=max(e['max_patch'] for e in events),
                mesh_builds=steps+1,predictor_sweeps=steps,corrector_sweeps=steps)
    if apply_balance:
        assert maxcons<3e-12 and minimum>0,result
        if system=='euler': assert minp>0,result
        if problem=='uniform': assert maxuniform<3e-12,result
    return result,dict(u=u,x=x,mass=mesh.mass)


def main(output):
    output.mkdir(parents=True,exist_ok=False)
    sources=[Path(__file__).resolve(),Path(base.__file__).resolve(),Path(euler.__file__).resolve()]
    for p in sources: shutil.copy2(p,output/p.name)
    (output/'provenance.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
    result=dict(cases=[],time_ladders=[]); started=time.monotonic()
    for method in ('n','lda_f1'):
        for system in ('scalar','euler'):
            for problem in (('uniform','smooth') if system=='scalar' else ('uniform','entropy','vortex')):
                r,s=run(16,64,.25,method,problem,system)
                result['cases'].append(r)
                np.savez_compressed(output/f'case_{len(result["cases"]):02d}.npz',**s)
                print(json.dumps(r),flush=True)
        states=[]; rows=[]
        for steps in (64,128,256,512,2048):
            r,s=run(12,steps,.5,method,'smooth')
            rows.append(r);states.append(s)
        ref=states[-1]
        for i in range(len(rows)-1):
            error=float(ref['mass']@abs(states[i]['u']-ref['u']))
            rows[i]['L1_to_2048_steps']=error
            rows[i]['observed_p']=float(np.log2(rows[i-1]['L1_to_2048_steps']/error)) if i else None
        result['time_ladders'].append(dict(method=method,cases=rows))
        print(json.dumps(result['time_ladders'][-1]),flush=True)
    result['elapsed_seconds']=time.monotonic()-started
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    main(parser.parse_args().output.resolve())
