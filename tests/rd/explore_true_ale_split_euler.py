#!/usr/bin/env python3
"""Standalone Euler checks for the retained-connectivity split proposal.

Not an AREPO binary or a port of its complete Roe/frame/limiter machinery.
Uses P1-U Gauss3 physical contour, average mesh advection, Roe spectral
matrices, N with contour reconciliation or LDA/F1. Smooth-test topology maps
use the existing unlimited affine-preserving conservative high endpoint.
Every predictor and accepted endpoint must have positive density/pressure.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

import numpy as np

import explore_true_ale_split as base

GAMMA = 1.4
FLOW = np.array([1., .4])


def pressure(u):
    return (GAMMA-1)*(u[...,3]-.5*np.sum(u[...,1:3]**2,axis=-1)/u[...,0])


def state(rho, vel, p):
    return np.concatenate((rho[...,None],rho[...,None]*vel,
                           (p/(GAMMA-1)+.5*rho*np.sum(vel**2,axis=-1))[...,None]),axis=-1)


def exact(x,t,problem):
    z = x-t*FLOW
    vel = np.broadcast_to(FLOW,x.shape).copy()
    rho,p = np.ones(len(x)),np.ones(len(x))
    if problem=='entropy':
        rho=base.exact(x,t)
    elif problem=='vortex':
        # Unit-box Yee vortex: core radius .07, beta=3. Periodic tail ~1e-10.
        r=((z-.5+.5)%1-.5)/.07
        radius2=np.sum(r*r,axis=1)
        vel+=3/(2*np.pi)*np.exp(.5*(1-radius2))[:,None]*np.column_stack((-r[:,1],r[:,0]))
        temp=1-(GAMMA-1)*9/(8*GAMMA*np.pi**2)*np.exp(1-radius2)
        rho=temp**(1/(GAMMA-1))
        p=rho**GAMMA
    return state(rho,vel,p)


def flux(u):
    p=pressure(u)
    vel=u[...,1:3]/u[...,0,None]
    f=u[...,None,:]*vel[..., :,None]
    f[...,0,1]+=p
    f[...,1,2]+=p
    f[..., :,3]+=p[...,None]*vel
    return f


def spectral(s,u,v):
    ids=s.mesh.ids
    q=u[ids]
    p=pressure(q)
    assert np.min(q[...,0])>0 and np.min(p)>0
    weight=np.sqrt(q[...,0])
    vel=q[...,1:3]/q[...,0,None]
    h=(q[...,3]+p)/q[...,0]
    rv=np.sum(weight[...,None]*vel,axis=1)/weight.sum(axis=1)[:,None]
    rh=np.sum(weight*h,axis=1)/weight.sum(axis=1)
    c=np.sqrt((GAMMA-1)*(rh-.5*np.sum(rv*rv,axis=1)))
    pm=(s.mesh.p+s.p1)/2
    edge=pm[:,[2,0,1]]-pm[:,[1,2,0]]
    length=np.linalg.norm(edge,axis=-1)
    normal=np.stack((-edge[...,1],edge[...,0]),axis=-1)/length[...,None]
    nx,ny=normal[...,0],normal[...,1]
    vx,vy=rv[:,0,None],rv[:,1,None]
    hh=rh[:,None]
    vn=vx*nx+vy*ny
    g=GAMMA-1
    q2=vx*vx+vy*vy
    A=np.zeros((len(ids),3,4,4))
    A[...,0,1]=nx; A[...,0,2]=ny
    A[...,1,0]=.5*g*q2*nx-vx*vn
    A[...,1,1]=vn-(GAMMA-2)*vx*nx
    A[...,1,2]=vx*ny-g*vy*nx; A[...,1,3]=g*nx
    A[...,2,0]=.5*g*q2*ny-vy*vn
    A[...,2,1]=vy*nx-g*vx*ny
    A[...,2,2]=vn-(GAMMA-2)*vy*ny; A[...,2,3]=g*ny
    A[...,3,0]=vn*(.5*g*q2-hh)
    A[...,3,1]=hh*nx-g*vx*vn
    A[...,3,2]=hh*ny-g*vy*vn; A[...,3,3]=GAMMA*vn
    I=np.eye(4)
    B=(A-vn[...,None,None]*I)/c[:,None,None,None]
    B2=B@B
    Pp=.5*(B2+B); Pm=.5*(B2-B); P0=I-B2
    sigma=v[ids].mean(axis=1)
    rel=vn-np.einsum('tij,tj->ti',normal,sigma)
    lp,lm=rel+c[:,None],rel-c[:,None]
    kp=.5*length[...,None,None]*(np.maximum(lp,0)[...,None,None]*Pp+
         np.maximum(lm,0)[...,None,None]*Pm+np.maximum(rel,0)[...,None,None]*P0)
    km=.5*length[...,None,None]*(np.minimum(lp,0)[...,None,None]*Pp+
         np.minimum(lm,0)[...,None,None]*Pm+np.minimum(rel,0)[...,None,None]*P0)
    return kp,km,normal,length,sigma


def operator(s,u,v,method,du=None):
    kp,km,normal,length,sigma=spectral(s,u,v)
    q=u[s.mesh.ids]
    phi=np.zeros((len(q),4))
    nodes,weights=np.polynomial.legendre.leggauss(3)
    for a in range(3):
        left,right=q[:,(a+1)%3],q[:,(a+2)%3]
        for z,w in zip(.5*(nodes+1),.5*weights):
            f=flux((1-z)*left+z*right)
            phi-=w*length[:,a,None]*np.einsum('tjk,tj->tk',f,normal[:,a])
    phi-=.5*np.einsum('ti,ti,tik->tk',length,np.einsum('tij,tj->ti',normal,sigma),q)
    sm=km.sum(axis=1)
    condition=np.linalg.cond(sm)
    assert np.max(condition)<1e10, 'This bounded prototype excludes singular Roe sums'
    if method=='lda_f1':
        rhs=phi[...,None]
        if du is not None:
            target=(s.b/3)[:,None]*du[s.mesh.ids].sum(axis=1)
            rhs=np.stack((phi,target),axis=-1)
        solved=np.linalg.solve(sm,rhs)
        distributed=-np.einsum('tijk,tkb->tijb',kp,solved)
        local=distributed[...,0]
        mass_local=distributed[...,1] if du is not None else None
    else:
        inflow=np.linalg.solve(sm,np.einsum('tijk,tik->tj',km,q)[...,None])[...,0]
        local=np.einsum('tijk,tik->tij',kp,q-inflow[:,None,:])
        local+=(phi-local.sum(axis=1))[:,None,:]/3
        mass_local=(s.b/3)[:,None,None]*du[s.mesh.ids] if du is not None else None
    assert np.max(abs(local.sum(axis=1)-phi))<2e-12
    r=base.scatter(s.mesh.ids,local,s.mesh.n)
    mass=base.scatter(s.mesh.ids,mass_local,s.mesh.n) if du is not None else None
    return r,mass,float(condition.max())


def simulate(n,steps,endtime,method,problem,variant='remap'):
    labels=base.points(n); v=base.velocities(labels,'deform')
    mesh=base.triangulate(labels); u=exact(labels,0,problem)
    initial=np.sum(mesh.mass[:,None]*u,axis=0)
    scale=np.array([initial[0]]*3+[initial[3]])
    dt=endtime/steps
    max_cons=max_uniform=max_cond=max_slab=0.
    minrho,minp=float(u[:,0].min()),float(pressure(u).min())
    events=[]
    for j in range(steps):
        s=base.slab(mesh,v,dt)
        r0,_,cond=operator(s,u,v,method)
        star=u-dt*r0/s.m1[:,None]
        assert np.min(star[:,0])>0 and np.min(pressure(star))>0
        # A true predictor exists before this one endpoint Delaunay build.
        x=(labels+(j+1)*dt*v)%1
        fresh=base.triangulate(x)
        r1,m,cond1=operator(s,star,v,method,star-u)
        final=star-(m+.5*dt*(r0+r1))/s.m1[:,None]
        retained=base.Mesh(mesh.ids,s.p1,mesh.n)
        slab_defect=np.sum(s.m1[:,None]*final-mesh.mass[:,None]*u,axis=0)
        max_slab=max(max_slab,float(np.max(abs(slab_defect)/scale)))
        if variant=='remap':
            # The tested smooth Euler cases must accept the unlimited high map.
            final,event=base.patch_transfer(retained,fresh,final,positive=False)
        else:
            oldkeys=set(map(tuple,np.sort(retained.ids,axis=1)))
            newkeys=set(map(tuple,np.sort(fresh.ids,axis=1)))
            event=dict(removed=len(oldkeys-newkeys))
        events.append(event)
        assert np.min(final[:,0])>0 and np.min(pressure(final))>0
        minrho=min(minrho,float(star[:,0].min()),float(final[:,0].min()))
        minp=min(minp,float(pressure(star).min()),float(pressure(final).min()))
        u,mesh=final,fresh
        max_cons=max(max_cons,float(np.max(abs(np.sum(mesh.mass[:,None]*u,axis=0)-initial)/scale)))
        if problem=='uniform':
            max_uniform=max(max_uniform,float(np.max(abs(u-exact(x,0,'uniform')))))
        max_cond=max(max_cond,cond,cond1)
    analytic=exact(x,endtime,problem)
    report=dict(n=n,nodes=n*n,method=method,problem=problem,variant=variant,steps=steps,end=endtime,dt=dt,
                relative_conservation=max_cons,slab_conservation=max_slab,uniform_error=max_uniform if problem=='uniform' else None,
                min_density=minrho,min_pressure=minp,maximum_condition=max_cond,
                density_L1=float(mesh.mass@abs(u[:,0]-analytic[:,0])),
                flip_steps=sum(e['removed']>0 for e in events),removed_triangles=sum(e['removed'] for e in events),
                max_patch=max((e.get('max_patch',0) for e in events),default=0),
                mesh_builds=steps+1,predictor_sweeps=steps,corrector_sweeps=steps)
    if variant=='remap':
        assert max_cons<3e-12 and max_slab<3e-12,report
        if problem=='uniform':
            assert max_uniform<3e-12,report
    return report,dict(u=u,x=x,mass=mesh.mass)


def main(output):
    output.mkdir(parents=True,exist_ok=False)
    sources=[Path(__file__).resolve(),Path(base.__file__).resolve()]
    for source in sources:
        shutil.copy2(source,output/source.name)
    (output/'provenance.json').write_text(json.dumps({source.name:hashlib.sha256(source.read_bytes()).hexdigest() for source in sources},indent=2)+'\n')
    rows=[]; start=time.monotonic()
    for method in ('n','lda_f1'):
        for problem,variant in [('uniform','remap'),('entropy','remap'),('vortex','remap'),('vortex','keep_u')]:
            row,fields=simulate(16,64,.25,method,problem,variant)
            rows.append(row)
            np.savez_compressed(output/f'case_{len(rows):02d}.npz',**fields)
            (output/'summary.partial.json').write_text(json.dumps(rows,indent=2)+'\n')
            print(json.dumps(row),flush=True)
    (output/'summary.json').write_text(json.dumps(dict(cases=rows,elapsed_seconds=time.monotonic()-start),indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    main(parser.parse_args().output.resolve())
