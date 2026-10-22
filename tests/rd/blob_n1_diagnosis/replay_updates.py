"""Replay FE/N1 and lumped Heun on the independently reconstructed 32^3 mesh."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

import h5py
import numpy as np

ROOT=Path(os.environ['RD_BLOB_AUDIT_ROOT']).resolve()
BUNDLE=Path(os.environ['RD_BLOB_BUNDLE']).resolve()
ptr=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
iptr=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS')
lib=ctypes.CDLL(str(ROOT/'mesh_rhs.dylib'))
lib.mesh_geometry.argtypes=[ctypes.c_int,ptr,ptr,ptr,ptr]
lib.mesh_rhs.argtypes=[ctypes.c_int,ctypes.c_int,iptr,ptr,ptr,ptr,ptr,ptr]
mesh=np.load(ROOT/'periodic_mesh.npz')
ids=np.ascontiguousarray(mesh['ids'],dtype=np.int32);nt=len(ids)
normals=np.zeros((nt,4,3));areas=np.zeros((nt,4));vol=np.zeros(nt)
assert lib.mesh_geometry(nt,mesh['x'],normals,areas,vol)==0


def state(path):
    with h5py.File(path) as f:
        g=f['PartType0'];o=np.argsort(g['ParticleIDs'][:]);r=g['Density'][:][o]
        v=g['Velocities'][:][o];u=g['InternalEnergy'][:][o]
        q=np.column_stack((r,r[:,None]*v,r*(u+.5*(v*v).sum(axis=1))))
        return float(f['Header'].attrs['Time']),q,g['Masses'][:][o]/r,g['Coordinates'][:][o]


_,initial,dual,x=state(BUNDLE/'cases/N_equal_np8/snapshots/snap_000.hdf5')
dt=1.5425744683748193/131072
svd_counts=[]
def rhs(u):
    r=np.zeros_like(u);svd=np.zeros(1)
    status=lib.mesh_rhs(len(u),nt,ids,normals,areas,u,r,svd)
    assert status==0,('invalid state or solve',status)
    svd_counts.append(int(svd[0]))
    return r/dual[:,None]


def norms(a,b):
    return dict(density_volume_relative_L1=float(np.sum(dual*np.abs(a[:,0]-b[:,0]))/np.sum(dual*b[:,0])),
                max_scaled_conserved=float(np.max(np.abs(a-b)/np.array([100,615,615,615,1000]))))


results={}
for method in ['N1_FE','N_RK2']:
    for half in [False,True]:
        u=initial.copy();nstep=8 if half else 4;h=dt/2 if half else dt
        history=[u.copy()];start=time.monotonic()
        for i in range(nstep):
            r=rhs(u);star=u+h*r
            if method=='N1_FE':u=star
            else:u=.5*(u+star+h*rhs(star))
            history.append(u.copy())
        name=method+('_half_dt' if half else '')
        np.savez_compressed(ROOT/f'{name}.npz',u=u,history=np.array(history))
        results[name]=dict(steps=nstep,dt=h,end=nstep*h,seconds=time.monotonic()-start)
        print(name,results[name],flush=True)
fe=np.load(ROOT/'N1_FE.npz')['u'];rk=np.load(ROOT/'N_RK2.npz')['u']
results['FE_vs_RK2']=norms(fe,rk)
results['FE_dt_vs_half_dt']=norms(fe,np.load(ROOT/'N1_FE_half_dt.npz')['u'])
results['RK2_dt_vs_half_dt']=norms(rk,np.load(ROOT/'N_RK2_half_dt.npz')['u'])

# Exact IC check against the actual predecessor setup function on all vertices.
with (ROOT/'ic.input.bin').open('xb') as f:
    f.write(np.int32(len(x)).tobytes());f.write(x.tobytes())
subprocess.run([str(ROOT/'ic_probe'),str(ROOT/'ic.input.bin'),str(ROOT/'ic.output.bin')],check=True,
               env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'))
old_ic=np.fromfile(ROOT/'ic.output.bin').reshape(-1,5)
results['predecessor_ic']=norms(old_ic,initial)
results['predecessor_ic']['max_absolute_difference_per_component']=np.max(np.abs(old_ic-initial),axis=0).tolist()
assert results['predecessor_ic']['max_scaled_conserved']<1e-14

# Recompute both the old isotropic and current directional CFL selectors.
rho=initial[:,0];velocity=initial[:,1:4]/rho[:,None]
pressure=(5/3-1)*(initial[:,4]-.5*rho*(velocity*velocity).sum(axis=1))
cs=np.sqrt((5/3)*pressure/rho)
old_alpha=areas.max(axis=1)*np.max(np.linalg.norm(velocity[ids],axis=2)+cs[ids],axis=1)/3
old_sum=np.bincount(ids.ravel(),weights=np.repeat(old_alpha,4),minlength=len(rho))
root=np.sqrt(rho[ids]);weight=root.sum(axis=1)
vroe=np.sum(root[:,:,None]*velocity[ids],axis=1)/weight[:,None]
h=(initial[:,4]+pressure)/rho
hroe=np.sum(root*h[ids],axis=1)/weight
croe=np.sqrt((5/3-1)*(hroe-.5*(vroe*vroe).sum(axis=1)))
vn=np.sum(normals*vroe[:,None,:],axis=2)
alpha=np.max(areas/3*(croe[:,None]+abs(vn)),axis=1)
alpha_sum=np.bincount(ids.ravel(),weights=np.repeat(alpha,4),minlength=len(rho))
old_dt=.01*dual/old_sum;new_dt=.01*dual/alpha_sum
results['initial_cfl']=dict(current_global_limit=float(new_dt.min()),
    current_limiting_id=int(new_dt.argmin()+1),old_global_limit=float(old_dt.min()),
    old_limiting_id=int(old_dt.argmin()+1),old_last_vertex_limit=float(old_dt[-1]),
    current_dt=dt,old_last_over_global_min=float(old_dt[-1]/old_dt.min()))

# Optionally compare saved short native outputs; this script never launches AREPO.
if os.environ.get('RD_BLOB_NATIVE_RUN'):
    native_run=Path(os.environ['RD_BLOB_NATIVE_RUN'])
    log=(native_run/'run.log').read_text()
    assert 'Code run for' in log and 'endrun called' in log,log[-300:]
    native=[];history=np.load(ROOT/'N_RK2.npz')['history']
    for path in sorted((native_run/'output').glob('snap_*.hdf5')):
        t,u,_,_=state(path);step=int(round(t/dt))
        assert abs(t-step*dt)<1e-18 and 0<=step<=4
        native.append(dict(snapshot=path.name,time=t,step=step,**norms(u,history[step])))
    assert len(native)>=2 and native[-1]['step']==4
    results['native_vs_independent_Heun']=native
else:
    results['native_vs_independent_Heun']='not requested; requires a separately completed native control'
results['svd_counts']=svd_counts
(ROOT/'update_audit.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2),flush=True)
