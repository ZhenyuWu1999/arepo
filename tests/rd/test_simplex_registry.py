#!/usr/bin/env python3
"""Independent checks for the pure C moving-tetra registry (no solver state)."""
import ctypes as C
import json
from pathlib import Path
import subprocess
import tempfile
import numpy as np
from scipy.spatial import Delaunay
from test_moving_tetrahedra import volume_polynomial, volume_minimum

REPO=Path(__file__).resolve().parents[2]
class Record(C.Structure):
    _fields_=[('id',C.c_uint64*4),('image',(C.c_int32*3)*4),('orientation',C.c_int32),
              ('x',(C.c_double*3)*4),('w',(C.c_double*3)*4)]
class Metric(C.Structure):
    _fields_=[(k,C.c_double) for k in ('v0','vmid','v1','vmin','smin','error','q0','qmid','q1','ratio','midpoint_defect','gcl_defect','mean_normal_correction')]+[(k,C.c_int) for k in ('negative0','negative1','negative_interval','uncertain','changed')]
class Cavity(C.Structure):
    _fields_=[('min_id',C.c_uint64)]+[(k,C.c_int) for k in ('vertices','removed','inserted','winding','invalid_old','invalid_new')]+[(k,C.c_double) for k in ('volume_defect0','volume_defect1','moment_defect0','moment_defect1')]
class Summary(C.Structure):
    _fields_=[(k,C.c_int) for k in ('old_count','new_count','removed','inserted','cavities','changed_vertices','max_vertices','winding_cavities','id_alias_old','id_alias_new','reversed_common','old_endpoint_negative','old_interval_negative','old_uncertain','new_pullback_negative','new_mid_negative','new_interval_negative','new_uncertain')]+[(k,C.c_double) for k in ('coverage0','coverage1','old_forward_coverage','new_pullback_coverage','min_old_interval','min_new_interval','min_pullback_ratio','min_q0','min_qmid','min_q1','max_cavity_volume_defect','max_cavity_moment_defect','max_midpoint_gcl_defect','max_gauss_gcl_defect','max_mean_normal_correction')]
BOX=(C.c_double*3)(1,1,1)
def library(folder):
    p=Path(folder)/'registry.so'
    subprocess.run(['cc','-O2','-std=c99','-shared','-fPIC',str(REPO/'src/mesh/rd_simplex_registry.c'),'-lm','-o',str(p)],check=True)
    lib=C.CDLL(str(p))
    lib.rd_tetra_canonicalize.argtypes=[C.POINTER(Record),C.POINTER(C.c_double)]
    lib.rd_tetra_interval.argtypes=[C.POINTER(Record),C.c_double,C.c_int,C.POINTER(Metric)]
    lib.rd_registry_prepare.argtypes=[C.POINTER(Record),C.c_int,C.POINTER(C.c_int)]
    lib.rd_registry_compare.argtypes=[C.POINTER(Record),C.c_int,C.POINTER(Record),C.c_int,C.c_double,C.POINTER(C.c_double),C.POINTER(Summary),C.POINTER(Metric),C.POINTER(Metric),C.POINTER(Cavity)]
    return lib

def record(lib,ids,x,w=None,images=None):
    r=Record();np.ctypeslib.as_array(r.id)[:]=ids
    np.ctypeslib.as_array(r.x)[:]=x
    if w is not None: np.ctypeslib.as_array(r.w)[:]=w
    if images is not None: np.ctypeslib.as_array(r.image)[:]=images
    lib.rd_tetra_canonicalize(C.byref(r),BOX)
    return r

def compare(lib,old,new,h):
    a=(Record*len(old))(*old);b=(Record*len(new))(*new);aliases=C.c_int()
    assert lib.rd_registry_prepare(a,len(a),C.byref(aliases))==0
    assert lib.rd_registry_prepare(b,len(b),C.byref(aliases))==0
    s=Summary();om=(Metric*len(a))();nm=(Metric*len(b))();c=(Cavity*(len(a)+len(b)))()
    assert lib.rd_registry_compare(a,len(a),b,len(b),h,BOX,C.byref(s),om,nm,c)==0
    return s,om,nm,list(c)[:s.cavities]

def independent_interval(r,h,closing):
    x=np.ctypeslib.as_array(r.x).copy();w=np.ctypeslib.as_array(r.w).copy()
    if closing: x-=h*w
    coeff=r.orientation*volume_polynomial(x,h*w)
    smin,vmin=volume_minimum(coeff)
    return coeff,vmin,smin

def main():
    rng=np.random.default_rng(20261011);maxerr=0.;cases=0
    with tempfile.TemporaryDirectory() as folder:
        lib=library(folder)
        for _ in range(400):
            x=rng.uniform(.1,.9,(4,3));w=rng.normal(0,.4,(4,3));h=.07
            for closing in (0,1):
                r=record(lib,[19,2,41,7],x+closing*h*w,w);m=Metric()
                lib.rd_tetra_interval(C.byref(r),h,closing,C.byref(m))
                coeff,minimum,where=independent_interval(r,h,closing)
                scale=max(np.max(np.abs(coeff)),1e-9)
                err=max(abs(m.vmin-minimum),abs(m.v0-coeff[0]),abs(m.v1-coeff.sum()))/scale
                maxerr=max(maxerr,err);assert err<3e-12,(err,m.vmin,minimum)
                assert abs(m.gcl_defect)<3e-13,m.gcl_defect
                assert m.negative_interval==(minimum < -m.error)
                cases+=1
        # Two roots between the probes: old/mid/new positive but hidden inversion.
        x=np.array([[0.,0,0],[1,0,0],[0,-.2001,0],[0,0,-.3003]])
        w=np.array([[0.,0,0],[0,0,0],[0,1,0],[0,0,1]])
        r=record(lib,[1,2,3,4],x,w);m=Metric();lib.rd_tetra_interval(C.byref(r),1.,0,C.byref(m))
        assert min(m.v0,m.vmid,m.v1)>0 and m.negative_interval and .2<m.smin<.31
        # Same trajectory crossing the periodic boundary has the same full key.
        x=np.array([[.98,.1,.1],[1.02,.1,.1],[.98,.2,.1],[.98,.1,.2]])
        images=np.array([[0,0,0],[1,0,0],[0,0,0],[0,0,0]])
        w=np.tile([.2,0,0],(4,1));a=record(lib,[1,2,3,4],x,w,images)
        b=record(lib,[1,2,3,4],x+.1*w,w,images)
        s,*_=compare(lib,[a],[b],.1);assert s.removed==s.inserted==s.cavities==0
        # Whole-box copies canonicalize identically; ID-only aliases remain distinct.
        copy=record(lib,[1,2,3,4],x+1,w,images+1)
        assert list(a.id)==list(copy.id) and np.array_equal(a.image,copy.image)
        np.testing.assert_allclose(a.x,copy.x,rtol=0,atol=3e-16)
        alt=record(lib,[1,2,3,4],x+np.array([[0,0,0],[0,1,0],[0,0,0],[0,0,0]]),w,images+np.array([[0,0,0],[0,1,0],[0,0,0],[0,0,0]]))
        arr=(Record*2)(a,alt);alias=C.c_int();assert lib.rd_registry_prepare(arr,2,C.byref(alias))==0 and alias.value==1
        dup=(Record*2)(a,a);assert lib.rd_registry_prepare(dup,2,C.byref(alias))==-2
        # Fixed hull, moving interior points: independent Delaunay symmetric diff.
        hull=np.array(np.meshgrid([.05,.95],[.05,.95],[.05,.95])).reshape(3,-1).T
        defects=[];sizes=[]
        for _ in range(35):
            x=np.vstack([hull,rng.uniform(.2,.8,(12,3))]);d=np.vstack([np.zeros((8,3)),rng.normal(0,.025,(12,3))]);h=.1
            ta=Delaunay(x).simplices;tb=Delaunay(x+d).simplices
            old=[record(lib,t+1,x[t],d[t]/h) for t in ta];new=[record(lib,t+1,(x+d)[t],d[t]/h) for t in tb]
            s,om,nm,c=compare(lib,old,new,h)
            ka={tuple(sorted(t)) for t in ta};kb={tuple(sorted(t)) for t in tb}
            orient_a={tuple(r.id):r.orientation for r in old};orient_b={tuple(r.id):r.orientation for r in new}
            reversed_keys={tuple(i-1 for i in k) for k in orient_a.keys() & orient_b.keys() if orient_a[k]!=orient_b[k]}
            assert s.reversed_common==len(reversed_keys)
            assert s.removed==len(ka-kb)+len(reversed_keys) and s.inserted==len(kb-ka)+len(reversed_keys)
            changed=(ka^kb)|reversed_keys;groups=[]
            while changed:
                t=changed.pop();g=set(t)
                while True:
                    touch={u for u in changed if g.intersection(u)}
                    if not touch: break
                    for u in touch: g.update(u)
                    changed-=touch
                groups.append(len(g))
            assert sorted(groups)==sorted(z.vertices for z in c)
            assert s.winding_cavities==0
            assert abs(s.coverage0-.9**3)<1e-13 and abs(s.coverage1-.9**3)<1e-13
            defects.append(max(s.max_cavity_volume_defect,s.max_cavity_moment_defect));sizes.extend(groups)
        assert max(defects)<1e-12,max(defects)
        print(json.dumps(dict(interval_cases=cases,max_interval_error=maxerr,cavity_models=35,max_cavity_defect=max(defects),max_vertices=max(sizes),hidden_inversion_min=m.vmin,record_bytes=C.sizeof(Record))))
if __name__=='__main__': main()
