"""Check preservation of an isobaric contact and its P1-Z interpolant."""
import ctypes
import json
from pathlib import Path
import subprocess
import os
import numpy as np

ROOT=Path(os.environ['RD_BLOB_AUDIT_ROOT']).resolve()
lib=ctypes.CDLL(str(ROOT/'mesh_rhs.dylib'))
ptr=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
class Solve(ctypes.Structure):
    _fields_=[('rank',ctypes.c_int),('used_svd',ctypes.c_int),('exact_singular',ctypes.c_int),('pivot_ratio',ctypes.c_double)]
class Diagnostic(ctypes.Structure):
    _fields_=[('solve',Solve),('conservation_defect',ctypes.c_double),('solve_defect',ctypes.c_double),('roundoff_scale',ctypes.c_double),('max_phi',ctypes.c_double)]
lib.mesh_geometry.argtypes=[ctypes.c_int,ptr,ptr,ptr,ptr]
lib.rd_euler_n_residual.argtypes=[ctypes.c_int,ptr,ptr,ptr,ctypes.c_double,ctypes.c_double,ctypes.c_int,ptr,ptr,ctypes.POINTER(Diagnostic)]
x=np.array([[2.,2.,2.],[3.,2.,2.],[2.,3.,2.],[2.,2.,3.]])
normal=np.zeros((4,3));area=np.zeros(4);volume=np.zeros(1)
assert lib.mesh_geometry(1,x,normal,area,volume)==0
records=[];raw=[]
for high in [0,1,2,3,4]:
    for rest in [False,True]:
        rho=np.array([100.]*high+[10.]*(4-high));v=np.zeros((4,3))
        if not rest:v[:]=[1e-8,1e-7,1e-7]
        u=np.column_stack((rho,rho[:,None]*v,150.+.5*rho*np.sum(v*v,axis=1)))
        phi=np.zeros(5);r=np.zeros((4,5));d=Diagnostic()
        assert lib.rd_euler_n_residual(3,u,normal,area,5/3,-1,0,phi,r,ctypes.byref(d))==0
        records.append(dict(high_density_vertices=high,exact_rest=rest,total_residual=phi.tolist(),
            nodal_residuals=r.tolist(),max_mass_residual=float(abs(r[:,0]).max()),
            current_svd=bool(d.solve.used_svd),rank=d.solve.rank))
        if not rest:raw.append((x,u))
with (ROOT/'contact.input.bin').open('xb') as f:
    f.write(np.int32(len(raw)).tobytes())
    for xx,u in raw:f.write(xx.tobytes());f.write(u.tobytes())
with (ROOT/'contact_probe.log').open('x') as log:
    p=subprocess.run([str(ROOT/'kernel_probe'),str(ROOT/'contact.input.bin'),str(ROOT/'contact.output.bin')],stdout=log,stderr=subprocess.STDOUT,
        env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'))
assert p.returncode==0
a=np.fromfile(ROOT/'contact.output.bin').reshape(-1,55)
defect=float(np.max(abs(a[:,:20]-a[:,20:40])))
z0=.5*(np.sqrt(100)+np.sqrt(10));zh=.5*250*(1/np.sqrt(100)+1/np.sqrt(10))
result=dict(cases=records,predecessor_current_max_absolute_nodal_difference=defect,
    exact_stationary_Euler_contact_residual=0.,midpoint_pressure_same_velocity=.4*z0*zh,
    caveat='Nonzero contact response is shared by both implementations; this is not evidence of a new AREPO regression.')
(ROOT/'contact_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('same-velocity midpoint pressure',result['midpoint_pressure_same_velocity'],'vs nodal 100')
for r in records:print(r['high_density_vertices'],r['exact_rest'],r['max_mass_residual'],r['total_residual'])
print('old/current max abs difference',defect)
