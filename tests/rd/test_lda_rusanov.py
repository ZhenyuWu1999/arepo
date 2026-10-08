#!/usr/bin/env python3
"""Compile production helpers; independently check flux, positivity and assembly."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import numpy as np

REPO = Path(__file__).resolve().parents[2]


def main():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p/'kernel.c').write_text('#include "rd_lda_rusanov.h"\n'
            'double low(double *u,double *n,double g,double *p,double *r) '
            '{return rd_lr_low((const double (*)[4])u,(const double (*)[2])n,g,p,(double (*)[3])r);}\n'
            'double limit(double *q,double *d){return rd_lr_limit(q,d);}\n'
            'void sensor(double *r,int mode,double *t){rd_lr_b_sensor((const double (*)[3])r,mode,t);}\n'
            'double difference(double h,double l,double oh,double ol,double oa,double t)'
            '{return rd_lr_b_difference(h,l,oh,ol,oa,t);}\n')
        subprocess.run(['cc','-shared','-fPIC','-O2','-std=c11','-I'+str(REPO/'src/hydro'),
                        str(p/'kernel.c'),'-o',str(p/'kernel.so'),'-lm'],check=True)
        lib = ctypes.CDLL(str(p/'kernel.so'))
        ptr = np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
        lib.low.argtypes=[ptr,ptr,ctypes.c_double,ptr,ptr]; lib.low.restype=ctypes.c_double
        lib.limit.argtypes=[ptr,ptr]; lib.limit.restype=ctypes.c_double
        lib.sensor.argtypes=[ptr,ctypes.c_int,ptr]; lib.sensor.restype=None
        lib.difference.argtypes=[ctypes.c_double]*6; lib.difference.restype=ctypes.c_double
        rng=np.random.default_rng(20260930)
        def internal(u): return u[...,3]-.5*np.sum(u[...,1:3]**2,axis=-1)/u[...,0]
        def flux(u,g):
            v=u[...,1:3]/u[...,0,None]; pressure=(g-1)*internal(u)
            f=v[..., :,None]*u[...,None,:]
            f[...,0,1]+=pressure; f[...,1,2]+=pressure; f[...,:,3]+=pressure[...,None]*v
            return f
        for trial in range(2000):
            rho=10.**rng.uniform(-3,3,3); pressure=10.**rng.uniform(-6,3,3)
            v=rng.normal(size=(3,2)); g=5/3
            u=np.column_stack((rho,rho[:,None]*v,pressure/(g-1)+.5*rho*np.sum(v*v,axis=1)))
            xy=rng.normal(size=(3,2)); e=np.roll(xy,-1,axis=0)-np.roll(xy,-2,axis=0)
            n=np.ascontiguousarray(np.column_stack((-e[:,1],e[:,0])))
            if trial%10==0: u[:]=u[0]
            x,w=np.polynomial.legendre.leggauss(3); x=(x+1)/2; w=w/2
            phi=np.zeros(4)
            for edge in range(3):
                states=(1-x[:,None])*u[(edge+1)%3]+x[:,None]*u[(edge+2)%3]
                phi-=np.einsum('q,qdk,d->k',w,flux(states,g),n[edge])
            if trial%10==0: phi[:]=0
            residual=np.zeros((4,3)); alpha=lib.low(u,n,g,phi,residual)
            assert alpha>0,trial
            assert np.max(abs(residual.sum(axis=1)-phi)) < 1e-12*max(1,np.max(abs(residual)))
            dt=rng.uniform(.01,.999)/alpha
            result=u-dt*residual.T
            assert np.all(result[:,0]>0) and np.all(internal(result)>0),trial
            if trial%10==0: assert np.array_equal(residual,np.zeros_like(residual))
            # Artificial closed three-element patch: every node has degree3.
            base=np.ascontiguousarray(result)
            corrections=rng.normal(size=(3,3,4))*np.maximum(abs(base),1)
            corrections-=corrections.mean(axis=1,keepdims=True)
            assembled=base.copy()
            for c in corrections:
                ell=min(lib.limit(base[i],np.ascontiguousarray(3*c[i])) for i in range(3))
                assert 0<=ell<=1
                assembled+=ell*c
            assert np.all(assembled[:,0]>0) and np.all(internal(assembled)>0),trial
            assert np.max(abs(assembled.sum(axis=0)-base.sum(axis=0))) < 1e-11*max(1,np.max(abs(base)))
        print('PASS: 2000 common-Gauss inflow/CFL cases and conservative limited patch assemblies; exact uniform residual.')
        # Compare the C sensor to an independent direct formula, including
        # cancellation, one-sign and zero residuals; verify component units
        # do not change the ratios and both blends retain the common total.
        for trial in range(1000):
            low=rng.normal(size=(4,3))
            if trial%4==0: low[0]=0
            if trial%4==1: low[1]=[1,-1,0]
            if trial%4==2: low[2]=abs(low[2])
            high=low+rng.normal(size=(4,3))
            high-=(high.sum(axis=1)-low.sum(axis=1))[:,None]/3
            denom=abs(low).sum(axis=1)
            expected=np.divide(abs(low.sum(axis=1)),denom,out=np.zeros(4),where=denom>0)
            for mode in (1,2):
                theta=np.zeros(4);lib.sensor(low,mode,theta)
                target=expected if mode==1 else np.full(4,expected.max())
                assert np.max(abs(theta-target))<1e-14
                scaled=np.ascontiguousarray(low*10.**rng.uniform(-100,100,(4,1)))
                check=np.zeros(4);lib.sensor(scaled,mode,check)
                assert np.max(abs(check-theta))<1e-14
                blended=low+(1-theta[:,None])*(high-low)
                assert np.max(abs(blended.sum(axis=1)-low.sum(axis=1)))<1e-13
        print('PASS: 1000 RD B/Bmax sensor cases, scale invariance, common-total blending.')
        # Independently compare an explicit full old/new B update with the
        # production correction added to the SSP low candidate. Allow an
        # arbitrary accepted predictor, including a positivity-limited one.
        for trial in range(1000):
            un,oldh,oldl,olda,newh,newl,tf1=rng.normal(size=7)
            dt=.01;area=.7;theta=rng.uniform()
            star=un-dt*olda/area;du=star-un;lumped=area*du/dt
            high=tf1+.5*newh;low=lumped+.5*newl
            expected=star-dt/area*((1-theta)*(tf1+.5*(oldh+newh))+theta*(lumped+.5*(oldl+newl)))
            safe=.5*un+.5*(star-dt*newl/area)
            actual=safe-dt/area*lib.difference(high,low,oldh,oldl,olda,theta)
            assert abs(actual-expected)<1e-13
        print('PASS: 1000 complete B RK correctors match independent full-branch updates.')


if __name__=='__main__': main()
