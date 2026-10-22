"""Actual predecessor N1 kernel vs frozen AREPO N on identical tetrahedra."""
import hashlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import time

import h5py
import numpy as np
from scipy.spatial import Delaunay

ROOT = Path(os.environ['RD_BLOB_AUDIT_ROOT']).resolve()
BUNDLE = Path(os.environ['RD_BLOB_BUNDLE']).resolve()
ENV = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
rng = np.random.default_rng(20261020)


def conserved(rho, vel, p):
    return np.column_stack((rho, rho[:, None]*vel, p/(5/3-1)+.5*rho*np.sum(vel*vel, axis=1)))


def probe(name, x, u):
    start = time.monotonic()
    assert x.shape[0] == u.shape[0]
    source = ROOT/f'{name}.input.bin'
    with source.open('xb') as f:
        f.write(np.int32(len(x)).tobytes())
        for xx, uu in zip(x, u):
            f.write(np.asarray(xx, dtype=np.float64).tobytes())
            f.write(np.asarray(uu, dtype=np.float64).tobytes())
    dest = ROOT/f'{name}.output.bin'
    command = [str(ROOT/'kernel_probe'), str(source), str(dest)]
    with (ROOT/f'{name}.log').open('x') as log:
        result = subprocess.run(command, env=ENV, stdout=log, stderr=subprocess.STDOUT, timeout=90)
    assert result.returncode == 0 and dest.stat().st_size == len(x)*55*8, name
    a = np.fromfile(dest, dtype=np.float64).reshape(-1, 55)
    old, new = a[:, :20], a[:, 20:40]
    scale = np.maximum(np.abs(new).max(axis=1), 1.)
    diff = np.abs(old-new).max(axis=1)/scale
    summary = dict(count=len(x), seconds=time.monotonic()-start,
        max_nodal_difference_scaled=float(diff.max()),
        difference_quantiles=np.percentile(diff,[0,50,90,99,100]).tolist(),
        max_total_difference_scaled=float(np.max(np.abs(a[:,40:45]-a[:,45:50])/scale[:,None])),
        max_geometry_volume_defect=float(a[:,50].max()),
        max_MAG_over_two_area_defect=float(a[:,51].max()),
        max_normal_difference=float(a[:,52].max()),
        current_svd_count=int(a[:,53].sum()), worst_index=int(diff.argmax()),
        input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        output_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(), command=command)
    np.savez(ROOT/f'{name}.differences.npz', difference=diff)
    return summary


# Random states avoid the original inverse's known exactly-zero-velocity stop.
xs, us = [], []
for i in range(1200):
    x = rng.uniform(2, 3, (4,3))
    while abs(np.linalg.det(x[1:]-x[0])) < .015:
        x = rng.uniform(2, 3, (4,3))
    rho = rng.uniform(5, 110, 4)
    v = rng.uniform(-2, 5, (4,3))
    p = rng.uniform(50, 200, 4)
    xs.append(x); us.append(conserved(rho,v,p))
results = {'random':probe('random',np.array(xs),np.array(us))}
print(json.dumps(results),flush=True)

with h5py.File(BUNDLE/'cases/N_equal_np8/snapshots/snap_000.hdf5') as f:
    g=f['PartType0']; order=np.argsort(g['ParticleIDs'][:])
    initial={k:g[k][:][order] for k in g}
x=initial['Coordinates'];rho=initial['Density'];vel=initial['Velocities'];p=initial['Pressure']
u=conserved(rho,vel,p)

# A padded periodic Qhull reconstruction; validate it against native duals.
padding=1.5
points=[]; ids=[]
for shift in itertools.product([-10.,0.,10.],repeat=3):
    y=x+shift; selected=np.all((y>=-padding)&(y<=10+padding),axis=1)
    points.append(y[selected]);ids.append(np.flatnonzero(selected))
points=np.vstack(points);ids=np.concatenate(ids)
start=time.monotonic();tri=Delaunay(points)
tetra=tri.simplices
center=points[tetra].mean(axis=1)
selected=np.all((center>=0)&(center<10),axis=1)
tetra=tetra[selected];tx=points[tetra];ti=ids[tetra]
vol=np.abs(np.linalg.det(tx[:,1:]-tx[:,0,None]))/6
dual=np.bincount(ti.ravel(),weights=np.repeat(vol/4,4),minlength=len(x))
native_dual=initial['Masses']/rho
mesh=dict(vertices=len(x),tetrahedra=len(tetra),padding=padding,
    volume=float(vol.sum()),dual_max_relative_error=float(np.max(abs(dual/native_dual-1))),
    triangulation_seconds=time.monotonic()-start)
assert mesh['dual_max_relative_error']<1e-10,mesh
np.savez_compressed(ROOT/'periodic_mesh.npz',x=tx,ids=ti,dual=dual,volume=vol)
results['mesh']=mesh
print(json.dumps(mesh),flush=True)

# Every non-uniform initial tetra, plus an independent random sample of uniform
# tetrahedra. No reconstructed/perturbed hydro state is supplied to the probe.
cloud_count=(rho[ti]>64).sum(axis=1)
mixed=np.flatnonzero((cloud_count>0)&(cloud_count<4))
uniform=np.flatnonzero((cloud_count==0)|(cloud_count==4))
selected=np.r_[mixed,rng.choice(uniform,1000,replace=False)]
results['initial_blob']=probe('initial_blob',tx[selected],u[ti[selected]])
results['initial_blob']['mixed_tetra_count']=len(mixed)
print(json.dumps(results['initial_blob']),flush=True)

# Compare actual evolved states, where the velocity no longer nearly vanishes.
for snapshot in [1,5,10,20]:
    with h5py.File(BUNDLE/f'cases/N_equal_np8/snapshots/snap_{snapshot:03d}.hdf5') as f:
        g=f['PartType0'];o=np.argsort(g['ParticleIDs'][:]);r=g['Density'][:][o]
        v=g['Velocities'][:][o];p=g['Pressure'][:][o];uu=conserved(r,v,p)
    selection=np.r_[mixed,rng.choice(uniform,300,replace=False)]
    results[f'blob_snapshot_{snapshot:03d}']=probe(f'blob_snapshot_{snapshot:03d}',tx[selection],uu[ti[selection]])
    print(snapshot,results[f'blob_snapshot_{snapshot:03d}']['max_nodal_difference_scaled'],flush=True)

# Slice weights and longitudinal/transverse line weights from the same 3D mesh.
def weights(points_on_slice):
    cells=tri.find_simplex(points_on_slice)
    assert np.all(cells>=0)
    transform=tri.transform[cells]
    first=np.einsum('nij,nj->ni',transform[:,:3],points_on_slice-transform[:,3])
    w=np.column_stack((first,1-first.sum(axis=1)))
    assert w.min()>-1e-10
    return ids[tri.simplices[cells]],w

grid=np.linspace(0,10,501)
aa,bb=np.meshgrid(grid,grid)
slice_points=np.column_stack((aa.ravel(),bb.ravel(),np.full(aa.size,5.)))
si,sw=weights(slice_points)
line=np.linspace(0,10,1201)
li,lw=weights(np.column_stack((line,np.full(len(line),5.),np.full(len(line),5.))))
np.savez_compressed(ROOT/'slice_weights.npz',grid=grid,ids=si,weights=sw,line=line,line_ids=li,line_weights=lw)
(ROOT/'kernel_audit.json').write_text(json.dumps(results,indent=2)+'\n')
