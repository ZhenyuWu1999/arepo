#!/usr/bin/env python3
"""Independent Euler/P1 Gauss-LDA retry with real Delaunay changes and clocks.

This is not a new AREPO solver. It tests complete local interval closure,
Campoli endpoint storage, and a zero-sum F1 extension. Predictors are live only
on complete equal-actual-interval stars. Same-time transfer reuses the existing
limited basis high/full-patch low map. Native static comparison is separate.
"""
import argparse
import json
from pathlib import Path
import time
import traceback
import numpy as np
from scipy.spatial import Delaunay
from colombo_re_limited import limited_remap

GAMMA=1.4
CURRENT_CONTEXT={}


def area(x):
    a=x[:,1]-x[:,0];b=x[:,2]-x[:,0]
    return .5*(a[:,0]*b[:,1]-a[:,1]*b[:,0])


def scatter(ids,values,n):
    values=np.broadcast_to(values,ids.shape+values.shape[2:])
    result=np.zeros((n,)+values.shape[2:])
    np.add.at(result,ids.ravel(),values.reshape((-1,)+values.shape[2:]))
    return result


def primitive(u):
    rho=u[...,0];v=u[...,1:3]/rho[...,None]
    p=.4*(u[...,3]-.5*rho*np.sum(v*v,axis=-1))
    return rho,v,p


def admissible(u,where):
    rho,v,p=primitive(u)
    if not np.all(np.isfinite(u)) or min(rho.min(),p.min())<=0:
        raise FloatingPointError(f'{where}: rho={rho.min():.9g}, p={p.min():.9g}')
    return float(rho.min()),float(p.min())


def flux(u):
    rho,v,p=primitive(u);f=np.zeros(u.shape[:-1]+(2,4))
    for d in (0,1):
        f[...,d,0]=u[...,d+1]
        f[...,d,1:3]=u[...,1:3]*v[...,d,None]
        f[...,d,d+1]+=p
        f[...,d,3]=(u[...,3]+p)*v[...,d]
    return f


def boost(u,b):
    out=u.copy();out[...,1:3]-=u[...,0,None]*b
    out[...,3]+=-np.sum(u[...,1:3]*b,axis=-1)+.5*u[...,0]*np.sum(b*b,axis=-1)
    return out


def apply_beta(operator,target):
    kp,sm,full,b=operator
    local=boost(target,b);z=np.zeros_like(local)
    z[full]=np.linalg.solve(sm[full],local[full,...,None])[...,0]
    z[~full]=np.einsum('tij,tj->ti',np.linalg.pinv(sm[~full],rcond=1e-12),local[~full])
    return boost(-np.einsum('tjik,tk->tji',kp,z),-b[:,None,:])


def spatial(x,sigma,u):
    """Conservative P1-U Gauss3 total and independent Roe spectral LDA beta."""
    admissible(u,'spatial input')
    # As in the current native contour path: solve in the element frame, then
    # transform extensive/residual vectors back. Avoid forming beta explicitly.
    frame=sigma.mean(axis=1);u=boost(u,frame[:,None,:]);sigma=sigma-frame[:,None,:]
    edge=np.roll(x,-1,axis=1)-np.roll(x,-2,axis=1)
    inward=np.stack((edge[:,:,1],-edge[:,:,0]),axis=-1)
    mag=np.linalg.norm(inward,axis=-1);normal=inward/mag[:,:,None]
    rho,v,p=primitive(u);sqrt=np.sqrt(rho)
    velocity=np.sum(sqrt[:,:,None]*v,axis=1)/sqrt.sum(axis=1)[:,None]
    enthalpy=np.sum(sqrt*(u[:,:,3]+p)/rho,axis=1)/sqrt.sum(axis=1)
    c=np.sqrt(.4*(enthalpy-.5*np.sum(velocity**2,axis=-1)))
    un=np.einsum('tjd,td->tj',normal,velocity)
    sn=np.einsum('tjd,td->tj',normal,sigma.mean(axis=1))
    R=np.zeros((len(x),3,4,4))
    for col,sign in ((0,-1),(1,1)):
        R[:,:,0,col]=1
        R[:,:,1:3,col]=velocity[:,None,:]+sign*c[:,None,None]*normal
        R[:,:,3,col]=enthalpy[:,None]+sign*c[:,None]*un
    R[:,:,0,2]=1;R[:,:,1:3,2]=velocity[:,None,:]
    R[:,:,3,2]=.5*np.sum(velocity**2,axis=-1)[:,None]
    R[:,:,1,3]=-normal[:,:,1];R[:,:,2,3]=normal[:,:,0]
    R[:,:,3,3]=-velocity[:,0,None]*normal[:,:,1]+velocity[:,1,None]*normal[:,:,0]
    lam=np.stack((un-sn-c[:,None],un-sn+c[:,None],un-sn,un-sn),axis=-1)
    invR=np.linalg.inv(R)
    kp=((R*np.maximum(lam,0)[:,:,None,:])@invR)*(.5*mag[:,:,None,None])
    km=((R*np.minimum(lam,0)[:,:,None,:])@invR)*(.5*mag[:,:,None,None])
    sm=km.sum(axis=1);sing=np.linalg.svd(sm,compute_uv=False)
    full=sing[:,-1]>1e-12*sing[:,0]
    nodes=np.array([.5-np.sqrt(15)/10,.5,.5+np.sqrt(15)/10]);weights=np.array([5/18,4/9,5/18])
    physical=np.zeros((len(x),4));scale=np.zeros(len(x))
    for j in range(3):
        a,b=(j+1)%3,(j+2)%3
        for s,w in zip(nodes,weights):
            fq=flux((1-s)*u[:,a]+s*u[:,b])
            term=-w*np.einsum('td,tdk->tk',inward[:,j],fq)
            physical+=term;scale+=np.sum(abs(term),axis=1)
    mesh=.5*np.einsum('tjd,td,tjk->tk',inward,sigma.mean(axis=1),u)
    phi=physical-mesh
    operator=(kp,sm,full,frame)
    distributed=apply_beta(operator,boost(phi,-frame))
    local_distributed=boost(distributed,frame[:,None,:])
    defect=np.max(abs(local_distributed.sum(axis=1)-phi),axis=1)
    tolerance=2048*np.finfo(float).eps*(scale+np.sum(abs(distributed),axis=(1,2)))
    if np.any(defect>tolerance):
        j=int(np.argmax(defect/np.maximum(tolerance,1e-300)))
        raise ArithmeticError(f'LDA range/conservation: defect={defect[j]:.4e}, tol={tolerance[j]:.4e}, rankfull={full[j]}')
    return distributed,operator,full


def triangulate(x):
    wrapped=x%1;shifts=np.array([(i,j) for i in (-1,0,1) for j in (-1,0,1)])
    tiled=(wrapped[None,:,:]+shifts[:,None,:]).reshape(-1,2)
    triangles=Delaunay(tiled).simplices;centres=tiled[triangles].mean(axis=1)
    triangles=triangles[np.all((centres>=0)&(centres<1),axis=1)]
    out={}
    for t in triangles:
        ids=t%len(x);xp=tiled[t]
        if area(xp[None])[0]<0:ids=ids[[0,2,1]];xp=xp[[0,2,1]]
        key=tuple(sorted(map(int,ids)));offset=np.rint(xp-x[ids])
        out[key]=(ids.copy(),offset)
    assert len(out)==2*len(x)
    return out


def arrays(records,x):
    ids=np.array([v[0] for v in records.values()]);offset=np.array([v[1] for v in records.values()])
    return ids,x[ids]+offset


def components(old,new):
    changed=list(set(old)^set(new));groups=[]
    while changed:
        vertices=set(changed.pop());again=True
        while again:
            again=False
            for key in changed[:]:
                if vertices.intersection(key):vertices.update(key);changed.remove(key);again=True
        groups.append(sorted(vertices))
    return groups


def update(records,last,x,velocity,u,g,epoch,vel_epoch,tick,h,due,f1,mode,periods):
    keys=list(records);ids,xend=arrays(records,x);start=np.array([last[k] for k in keys])
    ii=ids[due];starts=start[due];dt=(tick-starts)*h
    if not len(ii):return np.zeros_like(u),np.zeros_like(g),dict(live=0,range_calls=0)
    if np.any(np.maximum(epoch[ii].max(axis=1),vel_epoch[ii].max(axis=1))>starts):
        raise AssertionError('interval crosses a trace or mesh-velocity change')
    xn=xend[due];xo=xn-dt[:,None,None]*velocity[ii];xm=.5*(xo+xn)
    ao,am,an=area(xo),area(xm),area(xn)
    # Check positive signed area over the full quadratic trajectory interval.
    c2=2*(an+ao-2*am);c1=an-ao-c2
    stationary=np.divide(-c1,2*c2,out=np.zeros_like(c1),where=c2>0)
    minimum=np.minimum(ao,an);mask=(c2>0)&(stationary>0)&(stationary<1)
    minimum[mask]=np.minimum(minimum[mask],ao[mask]+c1[mask]*stationary[mask]+c2[mask]*stationary[mask]**2)
    if minimum.min()<=0:raise ArithmeticError('old interval triangle inverted')
    r0,_,_=spatial(xm,velocity[ii],u[ii])
    dg=scatter(ii,((an-ao)/3)[:,None],len(u))
    endpoint=scatter(ids,area(xend)[:,None]/3,len(u))
    degree=np.bincount(ids.ravel(),minlength=len(u));closed=np.bincount(ii.ravel(),minlength=len(u))
    earliest=np.full(len(u),tick);latest=np.zeros(len(u),dtype=int)
    np.minimum.at(earliest,ids.ravel(),np.repeat(start,3));np.maximum.at(latest,ids.ravel(),np.repeat(start,3))
    live=(degree==closed)&(earliest==latest)
    if mode=='unsafe_live':live=(degree==closed)
    if mode=='bin_live':
        star=periods.copy();np.minimum.at(star,ids.ravel(),np.repeat(periods[ids].min(axis=1),3))
        live=(degree==closed)&(periods==star)
    du=-scatter(ii,dt[:,None,None]*r0,len(u))/endpoint[:,None]
    du[~live]=0
    admissible(u+du,'RK predictor')
    r1,beta,full=spatial(xm,velocity[ii],(u+du)[ii])
    deposits=(an-ao)[:,None,None]*u[ii]/3-dt[:,None,None]*(r0+r1)/2+(an-ao)[:,None,None]*du[ii]/6
    if f1:
        mass=(ao+an)/2
        correction=mass[:,None,None]/3*(du[ii]-apply_beta(beta,du[ii].sum(axis=1)))
        correction[~full]=0 # existing conservative lumped temporal fallback
        deposits+=correction
    return scatter(ii,deposits,len(u)),dg,dict(live=int(live.sum()),range_calls=len(ii)*2,
                                              mismatch_frozen=int(np.sum((degree==closed)&(earliest!=latest))),
                                              minimum_interval_area=float(minimum.min()))


def initial(n,state,mesh_ic=None):
    rng=np.random.default_rng(913);xy=(np.indices((n,n)).reshape(2,-1).T+.5+rng.uniform(-.17,.17,(n*n,2)))/n
    if mesh_ic is not None:
        import h5py
        with h5py.File(mesh_ic) as source:
            xy=source['PartType0/Coordinates'][:,:2]/float(source['Header'].attrs['BoxSize'])
    x,y=xy.T
    rho=np.ones(len(x));p=np.ones(len(x));v=np.tile([.7,.3],(len(x),1))
    if state=='entropy':rho+=.15*np.sin(2*np.pi*x)*np.cos(2*np.pi*y)
    elif state=='smooth':
        rho+=.12*np.sin(2*np.pi*x)*np.cos(2*np.pi*y)
        p+=.08*np.cos(2*np.pi*(x+y));v[:,0]+=.15*np.sin(2*np.pi*y);v[:,1]+=.1*np.sin(2*np.pi*x)
    elif state=='kh':
        band=.5*(np.tanh((y-.25)/.08)-np.tanh((y-.75)/.08))
        rho=1+band;p[:]=2.5;v[:,0]=.5-band;v[:,1]=.01*np.sin(4*np.pi*x)
    elif state=='sod':rho=np.where(x<.5,1.,.125);p=np.where(x<.5,1.,.1);v[:]=0
    elif state!='uniform':raise ValueError(state)
    return xy,np.column_stack((rho,rho[:,None]*v,p/.4+.5*rho*np.sum(v*v,axis=1)))


def run(n=8,depth=8,state='smooth',motion='prescribed',f1=True,mode='closure',end=.1,H=.005,
        mesh_ic=None,bin_pattern='split'):
    global CURRENT_CONTEXT
    assert depth>=1 and depth&(depth-1)==0,'Depth must be dyadic.'
    x,u=initial(n,state,mesh_ic);xinitial=x.copy();uinitial=u.copy();count=len(u)
    velocity=.35*np.column_stack((np.sin(2*np.pi*x[:,1]),np.cos(2*np.pi*x[:,0])))
    if motion=='fluid':velocity=u[:,1:3]/u[:,0,None]
    elif motion=='static':velocity[:]=0
    periods=np.where(x[:,0]<.5,1,depth)
    if bin_pattern=='bands':
        levels=int(np.log2(depth))+1
        periods=2**np.minimum((x[:,0]*levels).astype(int),levels-1)
    h=H/depth;ntick=round(end/h)
    assert abs(ntick*h-end)<1e-12
    assert ntick%depth==0,'End at a common synchronization time.'
    records=triangulate(x);ids,xtri=arrays(records,x)
    g=scatter(ids,area(xtri)[:,None]/3,count);q=g[:,None]*u;total=q.sum(axis=0)
    last=dict.fromkeys(records,0);birth=last.copy();epoch=np.zeros(count,dtype=int);vel_epoch=epoch.copy()
    stats=dict(events=0,changed_triangles=0,extra_elements=0,element_updates=0,early_refreshes=0,
               non_dyadic_closures=0,mismatch_frozen=0,min_theta=1.,max_mass_geometry_gap=0.,max_common_conservation=0.,
               min_rho=float(u[:,0].min()),min_pressure=float(primitive(u)[2].min()),max_uniform_error=0.)
    history=[];start_wall=time.monotonic()
    for tick in range(1,ntick+1):
        x+=h*velocity
        new=triangulate(x) if motion!='static' else records
        patches=components(records,new);patch=set(v for group in patches for v in group)
        keys=list(records);ids,xtri=arrays(records,x)
        active=tick%periods==0;natural=tick%periods[ids].min(axis=1)==0
        due=natural.copy()
        if patch:
            if mode=='dying_only':due|=np.array([k not in new for k in keys])
            else:due|=np.any(np.isin(ids,list(patch)),axis=1)
        starts=np.array([last[k] for k in keys]);assert np.all(starts>=np.array([birth[k] for k in keys]))
        CURRENT_CONTEXT={'tick':tick,'time':tick*h,'state':state,'motion':motion,'mode':mode,
                         'patch_vertices':len(patch),'stats':stats}
        stats['non_dyadic_closures']+=int(np.sum(due&((tick-starts)!=periods[ids].min(axis=1))))
        dq,dg,diag=update(records,last,x,velocity,u,g,epoch,vel_epoch,tick,h,due,f1,mode,periods)
        q+=dq;g+=dg
        stats['mismatch_frozen']+=diag.get('mismatch_frozen',0)
        for k in np.array(keys,dtype=object)[due]:last[tuple(k)]=tick
        stats['element_updates']+=int(due.sum());stats['extra_elements']+=int((due&~natural).sum())
        refresh=active.copy()
        if patch:refresh[list(patch)]=True
        endpoint=scatter(ids,area(xtri)[:,None]/3,count)
        gap=float(np.max(abs(g[refresh]-endpoint[refresh]),initial=0));stats['max_mass_geometry_gap']=max(stats['max_mass_geometry_gap'],gap)
        if gap>2e-12:raise AssertionError('geometric coverage incomplete at refreshed vertex')
        unclosed=np.array([last[k]!=tick for k in keys])
        incomplete=np.bincount(ids[unclosed].ravel(),minlength=count)>0
        if np.any(refresh&incomplete):raise AssertionError('refresh before full incident-star closure')
        # Check both partial extensive ledgers and refreshed states before remap.
        admissible(q/g[:,None],'pre-remap ledger')
        u[refresh]=q[refresh]/g[refresh,None];admissible(u,'pre-remap trace')
        epoch[refresh]=tick
        ni,nx=arrays(new,x);old_areas=area(xtri);new_areas=area(nx)
        for group in patches:
            selected=np.array(group);oldmask=np.array([k not in new and set(k)<=set(group) for k in keys])
            newmask=np.array([k not in records and set(k)<=set(group) for k in new])
            a=scatter(ids[oldmask],old_areas[oldmask,None]/3,count)[selected]
            b=scatter(ni[newmask],new_areas[newmask,None]/3,count)[selected]
            geometry={'node_ids':list(range(len(group))),'old_mass':a,'new_mass':b,'mass_delta':b-a}
            qnew,gnew,info=limited_remap(q[selected],g[selected],geometry,low_endpoint='full_patch')
            q[selected]=qnew;g[selected]=gnew;u[selected]=qnew/gnew[:,None]
            stats['min_theta']=min(stats['min_theta'],info['theta'])
        if patch:
            stats['events']+=len(patches);stats['changed_triangles']+=len(set(records)^set(new))
            stats['early_refreshes']+=int(np.sum(refresh&~active))
        last={k:last[k] if k in last else tick for k in new};birth={k:birth[k] if k in birth else tick for k in new}
        records=new
        if motion=='fluid':velocity[refresh]=u[refresh,1:3]/u[refresh,0,None];vel_epoch[refresh]=tick
        rmin,pmin=admissible(q/g[:,None],'post-remap ledger');stats['min_rho']=min(stats['min_rho'],rmin);stats['min_pressure']=min(stats['min_pressure'],pmin)
        if state=='uniform':stats['max_uniform_error']=max(stats['max_uniform_error'],float(np.max(abs(u-uinitial))))
        if tick%depth==0:
            error=float(np.max(abs(q.sum(axis=0)-total)/np.array([total[0],total[0],total[0],total[3]])))
            stats['max_common_conservation']=max(stats['max_common_conservation'],error)
            history.append({'time':tick*h,'conservation':error,'events':stats['events']})
            if error>2e-11:raise AssertionError(f'common-endpoint conservation {error:.5e}')
        if tick%max(1,ntick//5)==0:print(f'progress {state}/{motion}/{depth}/{mode}: {tick}/{ntick}, events={stats["events"]}',flush=True)
    if state=='uniform' and stats['max_uniform_error']>3e-11:raise AssertionError('uniform-state drift')
    result=dict(n=n,node_count=count,mesh_ic=str(mesh_ic) if mesh_ic else None,bin_pattern=bin_pattern,
                period_counts={str(v):int(np.sum(periods==v)) for v in np.unique(periods)},
                depth=depth,state=state,motion=motion,f1=f1,mode=mode,end=end,H=H,stats=stats,history=history,
                seconds=time.monotonic()-start_wall,work_fraction=stats['element_updates']/(ntick*2*count))
    return result,dict(x=x,u=u,q=q,g=g,initial_x=xinitial,initial_u=uinitial,periods=periods)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('out',type=Path)
    p.add_argument('--n',type=int,default=8);p.add_argument('--depth',type=int,default=8)
    p.add_argument('--state',choices=['uniform','entropy','smooth','kh','sod'],default='smooth')
    p.add_argument('--motion',choices=['prescribed','fluid','static'],default='prescribed')
    p.add_argument('--mode',choices=['closure','dying_only','unsafe_live','bin_live'],default='closure')
    p.add_argument('--no-f1',action='store_true');p.add_argument('--end',type=float,default=.1);p.add_argument('--H',type=float,default=.005)
    p.add_argument('--mesh-ic',type=Path);p.add_argument('--bin-pattern',choices=['split','bands'],default='split')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    assert not (a.out/'result.json').exists(),'Use a fresh result directory.'
    try:
        result,arrays_out=run(a.n,a.depth,a.state,a.motion,not a.no_f1,a.mode,a.end,a.H,a.mesh_ic,a.bin_pattern)
        result['success']=True;np.savez(a.out/'state.npz',**arrays_out)
    except Exception as e:
        result={'success':False,'error':str(e),'context':CURRENT_CONTEXT,'arguments':{k:str(v) if isinstance(v,Path) else v for k,v in vars(a).items()},'traceback':traceback.format_exc()}
    (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
