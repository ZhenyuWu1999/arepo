"""Compare actual predecessor/current N residuals on every initial tetra."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import h5py
import numpy as np

root=Path(os.environ['RD_BLOB_AUDIT_ROOT']).resolve()
bundle=Path(os.environ['RD_BLOB_BUNDLE']).resolve()
mesh=np.load(root/'periodic_mesh.npz');ids=mesh['ids'];count=len(ids)
with h5py.File(bundle/'cases/N_equal_np8/snapshots/snap_000.hdf5') as f:
    g=f['PartType0'];o=np.argsort(g['ParticleIDs'][:]);rho=g['Density'][:][o]
    v=g['Velocities'][:][o];p=g['Pressure'][:][o]
u=np.column_stack((rho,rho[:,None]*v,p/(5/3-1)+.5*rho*np.sum(v*v,axis=1)))
body=np.column_stack((mesh['x'].reshape(count,12),u[ids].reshape(count,20)))
source=root/'full_initial.input.bin';dest=root/'full_initial.output.bin'
assert not dest.exists()
with source.open('xb') as f:
    f.write(np.int32(count).tobytes());f.write(body.tobytes())
command=[str(root/'kernel_probe'),str(source),str(dest)];start=time.monotonic()
with (root/'full_initial.log').open('x') as log:
    status=subprocess.run(command,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),
        stdout=log,stderr=subprocess.STDOUT,timeout=90)
assert status.returncode==0 and dest.stat().st_size==count*55*8
a=np.fromfile(dest).reshape(count,55)
d=np.max(abs(a[:,:20]-a[:,20:40]),axis=1)/np.maximum(1,np.max(abs(a[:,20:40]),axis=1))
result=dict(count=count,returncode=status.returncode,seconds=time.monotonic()-start,
    max_scaled_nodal_difference=float(d.max()),worst_index=int(d.argmax()),
    max_volume_defect=float(a[:,50].max()),max_MAG_defect=float(a[:,51].max()),
    max_normal_difference=float(a[:,52].max()),current_svd_count=int(a[:,53].sum()),
    input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    output_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),command=command)
assert result['max_normal_difference']<1e-12
assert result['max_MAG_defect']<1e-12
assert result['max_volume_defect']<1e-12
assert result['max_scaled_nodal_difference']<1e-10
(root/'full_initial_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
