#!/usr/bin/env python3
"""Four-panel t=1 Gresho comparison: lab versus element co-moving coordinates."""
from pathlib import Path
import h5py
import matplotlib.pyplot as plt
import numpy as np

BASE = Path("/home/zwu/Hydro_data_analysis/Data_MMRD_debug")
BOOSTS = (0, 1, 3, 10)

def load(kind, boost):
    stem = "output_gal3_contour_long_n48_b" if kind == "comoving" else "output_gal4_lab_contour_long_n48_b"
    path = BASE / f"{stem}{boost}" / "snap_001.hdf5"
    with h5py.File(path, "r") as f:
        g=f["PartType0"]; ids=np.asarray(g["ParticleIDs"]); order=np.argsort(ids)
        x=np.asarray(g["Coordinates"],float)[order]; v=np.asarray(g["Velocities"],float)[order]
        vol=np.asarray(g["Volume"],float)[order]; t=float(np.atleast_1d(f["Header"].attrs["Time"])[0])
    x[:,0]=(x[:,0]-boost*t)%1.; v[:,0]-=boost
    dx=(x[:,0]-.5+.5)%1.-.5; dy=(x[:,1]-.5+.5)%1.-.5; r=np.hypot(dx,dy)
    vp=np.divide(-v[:,0]*dy+v[:,1]*dx,r,out=np.zeros_like(r),where=r>0)
    exact=np.where(r<.2,5*r,np.where(r<.4,2-5*r,0.))
    return r,vp,vol

def profile(r,v,w,edges):
    center=.5*(edges[:-1]+edges[1:]); mean=np.full(len(center),np.nan)
    lo=np.full(len(center),np.nan); hi=np.full(len(center),np.nan)
    for i,(a,b) in enumerate(zip(edges[:-1],edges[1:])):
        q=(r>=a)&(r<b)
        if q.any():
            mean[i]=np.average(v[q],weights=w[q]); lo[i],hi[i]=np.quantile(v[q],[.16,.84])
    return center,mean,lo,hi

fig,axs=plt.subplots(2,2,figsize=(12.8,9.4),sharex=True,sharey=True,constrained_layout=True)
rr=np.linspace(0,.5,501); exact=np.where(rr<.2,5*rr,np.where(rr<.4,2-5*rr,0.)); edges=np.linspace(0,.5,42)
for ax,b in zip(axs.flat,BOOSTS):
    rc,vc,wc=load("comoving",b); rl,vl,wl=load("lab",b)
    c,mc,lc,hc=profile(rc,vc,wc,edges); _,ml,ll,hl=profile(rl,vl,wl,edges)
    ax.fill_between(c,lc,hc,color="#2d6f9f",alpha=.13,lw=0)
    ax.fill_between(c,ll,hl,color="#d5762c",alpha=.11,lw=0)
    ax.plot(rr,exact,color="black",lw=1.6,label="exact initial")
    ax.plot(c,mc,"o-",ms=2.6,lw=1.25,color="#2d6f9f",label="element co-moving")
    ax.plot(c,ml,"s--",ms=2.3,lw=1.15,color="#d5762c",label="laboratory")
    l1c=np.sum(wc*np.abs(vc-np.where(rc<.2,5*rc,np.where(rc<.4,2-5*rc,0))))/wc.sum()
    l1l=np.sum(wl*np.abs(vl-np.where(rl<.2,5*rl,np.where(rl<.4,2-5*rl,0))))/wl.sum()
    gap=np.mean(np.abs(vl-vc))
    ax.text(.025,.965,f"profile L1: co {l1c:.5f} | lab {l1l:.5f}\nmean |Δvφ| = {gap:.2e}",transform=ax.transAxes,va="top",fontsize=9)
    ax.set_title(f"boost = {b}",fontweight="bold"); ax.grid(alpha=.18); ax.set_xlim(0,.5); ax.set_ylim(-.08,1.08)
for ax in axs[:,0]: ax.set_ylabel(r"azimuthal velocity $v_\phi$")
for ax in axs[1,:]: ax.set_xlabel(r"radius $r$")
handles,labels=axs[0,0].get_legend_handles_labels(); fig.legend(handles,labels,loc="upper center",ncol=3,frameon=False,bbox_to_anchor=(.5,1.015))
fig.suptitle("Moving-mesh ALE–RD: identical P1-U contour residual in two conservative coordinate systems",fontsize=14,y=1.035)
out=BASE/"gresho_galilean_coordinate_panels.png"; fig.savefig(out,dpi=180,bbox_inches="tight"); print(out)
