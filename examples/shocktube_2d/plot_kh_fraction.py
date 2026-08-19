#!/usr/bin/env python3
"""KH: the Lagrangian fraction f, its threshold, and the long-time test.

f now scales the fluid-following part of VelVertex only, before mesh
regularisation, so it is exactly "the fraction of the fluid velocity the mesh
follows" and regularisation keeps full strength at every f.
"""
import glob, os
import numpy as np, h5py
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation

GAM = 1.4
L = "/home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_FracLong_20260819"
S = "/home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_EntropySweep_20260819"
R = "/home/zwu/Hydro_data_analysis/Data_MMRD_debug/LDA_KH_static_moving_20260818"
OUT = os.path.join(L, "figures")

def snaps(run):
    d = {}
    for s in sorted(glob.glob(f"{run}/output/snap_*.hdf5")):
        with h5py.File(s) as f:
            d[round(float(f["Header"].attrs["Time"]), 2)] = s
    return d

def panel(ax, path):
    with h5py.File(path) as f:
        g = f["PartType0"]
        xy = np.asarray(g["Coordinates"])[:, :2]
        rho = np.asarray(g["Density"])
        box = float(f["Header"].attrs["BoxSize"])
    ax.tripcolor(Triangulation(xy[:, 0], xy[:, 1]), rho, shading="gouraud",
                 cmap="RdBu_r", vmin=0.85, vmax=2.15)
    ax.set_xlim(0, box); ax.set_ylim(0, box); ax.set_aspect("equal")

def grid(arms, times, fname, title, sub):
    fig, axes = plt.subplots(len(arms), len(times),
                             figsize=(2.9 * len(times), 2.85 * len(arms)), squeeze=False)
    for r, (label, run) in enumerate(arms):
        sn = snaps(run); last = max(sn) if sn else 0
        for c, t in enumerate(times):
            ax = axes[r][c]; ax.set_xticks([]); ax.set_yticks([])
            if t in sn:
                panel(ax, sn[t])
            else:
                ax.text(0.5, 0.5, f"failed\nby t={t:g}", ha="center", va="center",
                        transform=ax.transAxes, fontsize=10.5, color="0.35")
                ax.set_facecolor("0.94")
            if r == 0: ax.set_title(f"t = {t:g}", fontsize=12)
            if c == 0: ax.set_ylabel(label, fontsize=10.5)
        if last < max(times):
            axes[r][-1].text(0.5, 0.1, f"last t = {last:g}", ha="center",
                             transform=axes[r][-1].transAxes, fontsize=9, color="0.35")
    fig.suptitle(title, fontsize=14, y=0.995)
    fig.text(0.5, 0.006, sub, ha="center", fontsize=10, color="0.3")
    fig.tight_layout(rect=[0, 0.018, 1, 0.982])
    for e in ("png", "pdf"): fig.savefig(f"{OUT}/{fname}.{e}", dpi=130)
    plt.close(fig)

def main():
    os.makedirs(OUT, exist_ok=True)
    grid([("static LDA", f"{R}/static_LDA_Roe_RK2"),
          ("f = 1.00", f"{S}/eps0"),
          ("f = 1.00, ShapeSpeed 2.0", f"{L}/f100_shape2"),
          ("f = 0.95", f"{L}/f095"),
          ("f = 0.90", f"{L}/f090"),
          ("f = 0.75", f"{L}/f075_long")],
         [0.8, 1.2, 1.6, 2.0],
         "kh-fraction-threshold",
         "KH: where the Lagrangian fraction stops rescuing moving LDA",
         "density, matched IC and colour scale. f scales the fluid-following "
         "velocity only; mesh regularisation is at full strength in every row.")

    grid([("f = 0.75", f"{L}/f075_long")],
         [2.0, 4.0, 6.0, 8.0, 10.0],
         "kh-fraction-long",
         "KH at f = 0.75 run to t = 10: is the rescue real or only delayed?",
         "density. Minimum cell mass stays at 1.0-1.2e-4 against an initial "
         "1.106e-4, and the entropy excursion decays to zero.")
    print(f"figures written to {OUT}")

main()
