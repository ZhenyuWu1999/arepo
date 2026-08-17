#!/usr/bin/env python3
"""Plot the t=1 moving-mesh ALE-RD Gresho boost ladder."""
from pathlib import Path
import h5py
import matplotlib.pyplot as plt
import numpy as np

BASE = Path("/home/zwu/Hydro_data_analysis/Data_MMRD_debug")
BOOSTS = (0, 1, 3, 10)
COLORS = ("#285f82", "#d97928", "#3c8d60", "#9b55a3")

def load(boost):
    path = BASE / f"output_gal3_contour_long_n48_b{boost}" / "snap_001.hdf5"
    with h5py.File(path, "r") as f:
        gas = f["PartType0"]
        x = np.asarray(gas["Coordinates"], dtype=float)
        v = np.asarray(gas["Velocities"], dtype=float)
        vol = np.asarray(gas["Volume"], dtype=float)
        ids = np.asarray(gas["ParticleIDs"])
        t = float(np.atleast_1d(f["Header"].attrs["Time"])[0])
    order = np.argsort(ids)
    x, v, vol = x[order], v[order], vol[order]
    x[:, 0] = (x[:, 0] - boost * t) % 1.0
    v[:, 0] -= boost
    dx = (x[:, 0] - 0.5 + 0.5) % 1.0 - 0.5
    dy = (x[:, 1] - 0.5 + 0.5) % 1.0 - 0.5
    r = np.hypot(dx, dy)
    vphi = np.divide(-v[:, 0] * dy + v[:, 1] * dx, r, out=np.zeros_like(r), where=r > 0)
    exact = np.where(r < 0.2, 5*r, np.where(r < 0.4, 2-5*r, 0.0))
    return x, v, vol, r, vphi, exact

runs = {b: load(b) for b in BOOSTS}
fig, (ax, ae) = plt.subplots(1, 2, figsize=(13.2, 5.2), constrained_layout=True)
rr = np.linspace(0, 0.5, 501)
vv = np.where(rr < 0.2, 5*rr, np.where(rr < 0.4, 2-5*rr, 0.0))
ax.plot(rr, vv, color="black", lw=1.8, label="exact initial profile", zorder=5)
for b, color in zip(BOOSTS, COLORS):
    _, _, vol, r, vphi, exact = runs[b]
    ax.scatter(r, vphi, s=5, alpha=0.30, color=color, edgecolors="none", label=f"boost {b}")
ax.set(xlim=(0, 0.5), ylim=(-0.08, 1.06), xlabel=r"radius $r$", ylabel=r"azimuthal velocity $v_\phi$")
ax.set_title(r"De-boosted Gresho profiles at $t=1$")
ax.grid(alpha=0.18)
ax.legend(frameon=False, fontsize=9, ncol=2, loc="upper right")

l1_profile=[]; peak=[]
for b in BOOSTS:
    _, _, vol, r, vphi, exact = runs[b]
    l1_profile.append(np.sum(vol*np.abs(vphi-exact))/np.sum(vol))
    peak.append(vphi.max())
ae.plot(BOOSTS, l1_profile, "o-", color="#285f82", lw=1.8, label=r"volume-weighted $L_1(v_\phi)$")
ae.set(xlabel="uniform x-boost", ylabel=r"$L_1(v_\phi)$", xticks=BOOSTS)
ae.ticklabel_format(axis="y", style="plain", useOffset=False)
ae.grid(alpha=0.18)
ap = ae.twinx()
ap.plot(BOOSTS, peak, "s--", color="#d97928", lw=1.8, label=r"peak $v_\phi$")
ap.set_ylabel(r"peak $v_\phi$")
lines = ae.lines + ap.lines
labels = [line.get_label() for line in lines]
ae.legend(lines, labels, frameon=False, fontsize=9, loc="lower right")
ae.set_title("Integral accuracy is flat through boost 10")
fig.suptitle("Moving-mesh ALE–RD with conservative-state contour residual", fontsize=14)
out = BASE / "gresho_galilean_boost10_contour.png"
fig.savefig(out, dpi=180)
print(out)
for b,e,pv in zip(BOOSTS,l1_profile,peak): print(b,e,pv)
