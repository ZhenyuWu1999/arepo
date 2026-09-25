#!/usr/bin/env python3
"""Compile the production K-construction block and check stage separation.

The unsplit matrix must remain the predicted-state Euler flux Jacobian,
while the LDA split pair must be the opening-state pair. Compare the former
against complex-step derivatives of the physical Euler flux, and test the
common-beta total-residual identity. No MPI executable is needed.
"""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import numpy as np

REPO = Path(__file__).resolve().parents[2]
GAMMA = 1.4


def flux(u, normal):
    rho, mx, my, energy = u
    vx, vy = mx/rho, my/rho
    pressure = (GAMMA-1)*(energy-.5*(mx*mx+my*my)/rho)
    vn = vx*normal[0]+vy*normal[1]
    return np.array([rho*vn, mx*vn+pressure*normal[0], my*vn+pressure*normal[1], (energy+pressure)*vn])


def main():
    source = (REPO/'src/hydro/residual_distribution_solver.c').read_text()
    start = source.index('      // compute residual: Reassign variables to local equivalents')
    stop = source.index('\n#ifdef RD_ALE_CFL_DIAGNOSTIC', start)
    block = source[start:stop]
    helper_start = source.index('static void rd_common_beta_unresolved(')
    helper_end = source.index('\n}\n', helper_start)+3
    helper = source[helper_start:helper_end].replace('static void', 'void', 1)
    wrapper = r'''
#include <math.h>
#include <string.h>
#define GAMMA 1.4
#define GAMMA_MINUS1 (GAMMA-1.0)
#define RD_LDA_COMMON_BETA
#define dmax(a,b) ((a)>(b)?(a):(b))
#define dmin(a,b) ((a)<(b)?(a):(b))
void build(double *rd_stage_average, double *rd_beta_average,
           double *N_X, double *N_Y, double *Mag, double *out) {
 int j,k,p;
 double velx_avg=rd_stage_average[0], vely_avg=rd_stage_average[1];
 double h_avg=rd_stage_average[2], Cs_avg=rd_stage_average[3];
 double Velvertex_avg[3]={0,0,0};
''' + block + '\nmemcpy(out,Kmatrix,sizeof(Kmatrix));\n}\n' + helper
    with tempfile.TemporaryDirectory(prefix='rd_common_beta_') as tmp:
        tmp = Path(tmp)
        (tmp/'probe.c').write_text(wrapper)
        subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC',str(tmp/'probe.c'),'-o',str(tmp/'probe.so')],check=True)
        lib = ctypes.CDLL(str(tmp/'probe.so'))
        ptr = np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
        lib.build.argtypes = [ptr]*6
        lib.build.restype = None
        lib.rd_common_beta_unresolved.argtypes = [ptr]*5
        lib.rd_common_beta_unresolved.restype = None
        normals = np.array([[1.,0.],[-.5,np.sqrt(3)/2],[-.5,-np.sqrt(3)/2]])
        nx,ny = np.ascontiguousarray(normals[:,0]),np.ascontiguousarray(normals[:,1])
        mag = np.ones(3)
        def matrix(stage, opening):
            out = np.empty((4,4,3,3))
            lib.build(stage,opening,nx,ny,mag,out)
            return out.transpose(2,3,0,1)
        def average(v):
            vx,vy,pressure = v
            h=GAMMA/(GAMMA-1)*pressure+.5*(vx*vx+vy*vy)
            return np.array([vx,vy,h,np.sqrt(GAMMA*pressure)])
        rng=np.random.default_rng(173)
        worst_jac=worst_total=0.; changed=0
        for _ in range(300):
            old=average([*rng.uniform(-1.2,1.2,2),rng.uniform(.6,2.)])
            new=average([*(old[:2]+rng.uniform(-.15,.15,2)),rng.uniform(.6,2.)])
            got=matrix(new,old); old_k=matrix(old,old); new_k=matrix(new,new)
            np.testing.assert_array_equal(got[:,:2],old_k[:,:2])
            np.testing.assert_array_equal(got[:,2],new_k[:,2])
            changed += int(np.max(abs(got[:,:2]-new_k[:,:2]))>1e-7)
            vx,vy,h,cs=new
            pressure=cs*cs/GAMMA
            u=np.array([1.,vx,vy,pressure/(GAMMA-1)+.5*(vx*vx+vy*vy)])
            for j in range(3):
                jac=np.column_stack([np.imag(flux(u.astype(complex)+1e-30j*np.eye(4)[k],normals[j]))/1e-30 for k in range(4)])
                worst_jac=max(worst_jac,float(np.max(abs(got[j,2]-.5*jac))))
                np.testing.assert_allclose(got[j,2],.5*jac,rtol=2e-13,atol=2e-13)
            sm=got[:,1].sum(axis=0)
            if np.linalg.cond(sm)>1e8:
                continue
            beta=np.array([-kp@np.linalg.inv(sm) for kp in got[:,0]])
            np.testing.assert_allclose(beta.sum(axis=0),np.eye(4),atol=2e-11)
            temporal,phi_n,phi_star=rng.normal(size=(3,4))
            total=temporal+.5*(phi_n+phi_star)
            combined=np.einsum('iab,b->ia',beta,total)
            separated=np.einsum('iab,b->ia',beta,temporal)+.5*(np.einsum('iab,b->ia',beta,phi_n)+np.einsum('iab,b->ia',beta,phi_star))
            worst_total=max(worst_total,float(np.max(abs(combined-separated))))
            np.testing.assert_allclose(combined,separated,atol=2e-12)
            np.testing.assert_allclose(combined.sum(axis=0),total,atol=2e-11)
        assert changed==300
        # A resting Euler average has an unresolved contact direction. An
        # opening-state solve can therefore lose part of a new-stage target.
        rest=average([0.,0.,1.]); kr=matrix(rest,rest); sm=np.ascontiguousarray(kr[:,1].sum(axis=0))
        assert np.linalg.matrix_rank(sm)==3
        pinv=np.linalg.pinv(sm)
        completed=[]; missing=0.
        for target in np.eye(4):
            x=np.ascontiguousarray(pinv@target)
            projected=np.empty(4); share=np.empty(4)
            lib.rd_common_beta_unresolved(sm,x,target,projected,share)
            raw=-np.einsum('iab,b->ia',kr[:,0],x)
            np.testing.assert_allclose(raw.sum(axis=0),projected,atol=3e-14)
            missing=max(missing,float(np.max(abs(raw.sum(axis=0)-target))))
            completed.append(raw+share)
        beta=np.array(completed).transpose(1,2,0)
        assert missing>.1, 'This test must exercise an incompatible target.'
        np.testing.assert_allclose(beta.sum(axis=0),np.eye(4),atol=3e-14)
        for _ in range(100):
            target=sm@rng.normal(size=4)  # compatible target must be unchanged
            old=-np.einsum('iab,b->ia',kr[:,0],pinv@target)
            np.testing.assert_allclose(np.einsum('iab,b->ia',beta,target),old,atol=3e-14)
        print(f'PASS: 300 compiled production stage splits; Euler Jacobian defect={worst_jac:.3e}; common-total identity={worst_total:.3e}; singular partition of unity and 100 compatible targets')


if __name__=='__main__':
    main()
