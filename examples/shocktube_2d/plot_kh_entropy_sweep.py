#!/usr/bin/env python3
"""Two-dimensional density maps and entropy curves for the KH sweep.

Arms: eps = 0, 0.1, 0.2, 0.3 (the targeted entropy dissipation of
dev_log/RD_ALE_entropy_dissipation.md) and sigma-fraction f = 0.5, 0.75 (the
independent control, which changes the mesh trajectory instead of the
operator).  Static LDA and moving N from the section-42 glass campaign are
included as the two references that complete.

The density panels are what the eye judges; the entropy panel is the exact
invariant of section 45, so the two are read together.
"""
import glob, os
import numpy as np
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation

GAM = 1.4
SWEEP = "/home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_EntropySweep_20260819"
REF = "/home/zwu/Hydro_data_analysis/Data_MMRD_debug/LDA_KH_static_moving_20260818"
GLASS = "/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Glass_Sod_KH_ALE_20260818/kh/runs"
OUT = os.path.join(SWEEP, "figures")

ARMS = [
    ("static LDA (reference)",      f"{REF}/static_LDA_Roe_RK2"),
    ("moving LDA, eps=0",           f"{SWEEP}/eps0"),
    ("moving LDA, eps=0.1",         f"{SWEEP}/eps010"),
    ("moving LDA, eps=0.3",         f"{SWEEP}/eps030"),
    ("moving LDA, sigma f=0.5",     f"{SWEEP}/sig050"),
    ("moving LDA, sigma f=0.75",    f"{SWEEP}/sig075"),
]


def snaps(run):
    out = {}
    for s in sorted(glob.glob(f"{run}/output/snap_*.hdf5")):
        with h5py.File(s) as f:
            out[round(float(f["Header"].attrs["Time"]), 2)] = s
    return out


def field(path):
    with h5py.File(path) as f:
        g = f["PartType0"]
        xy = np.asarray(g["Coordinates"])[:, :2]
        rho = np.asarray(g["Density"])
        box = float(f["Header"].attrs["BoxSize"])
    return xy, rho, box


def entropy_curve(run, lo, hi):
    ts, es = [], []
    for t, s in sorted(snaps(run).items()):
        with h5py.File(s) as f:
            g = f["PartType0"]
            rho = np.asarray(g["Density"])
            p = (GAM - 1.0) * rho * np.asarray(g["InternalEnergy"])
            sv = p / rho**GAM
        ts.append(t)
        es.append((np.maximum(lo - sv, 0) + np.maximum(sv - hi, 0)).max() / (hi - lo))
    return np.array(ts), np.array(es)


def main():
    os.makedirs(OUT, exist_ok=True)
    with h5py.File(snaps(ARMS[1][1])[0.0]) as f:
        g = f["PartType0"]
        rho0 = np.asarray(g["Density"])
        s0 = (GAM - 1.0) * rho0 * np.asarray(g["InternalEnergy"]) / rho0**GAM
    lo, hi = s0.min(), s0.max()

    times = [0.4, 0.8, 1.2, 2.0]
    fig, axes = plt.subplots(len(ARMS), len(times),
                             figsize=(3.0 * len(times), 2.9 * len(ARMS)))
    for r, (label, run) in enumerate(ARMS):
        sn = snaps(run)
        last = max(sn) if sn else None
        for c, t in enumerate(times):
            ax = axes[r, c]
            ax.set_xticks([]); ax.set_yticks([])
            key = t if t in sn else None
            if key is None:
                ax.text(0.5, 0.5, f"failed\nbefore t={t:g}", ha="center", va="center",
                        transform=ax.transAxes, fontsize=11, color="0.35")
                ax.set_facecolor("0.94")
            else:
                xy, rho, box = field(sn[key])
                tri = Triangulation(xy[:, 0], xy[:, 1])
                ax.tripcolor(tri, rho, shading="gouraud", cmap="RdBu_r", vmin=0.85, vmax=2.15)
                ax.set_xlim(0, box); ax.set_ylim(0, box); ax.set_aspect("equal")
            if r == 0:
                ax.set_title(f"t = {t:g}", fontsize=12)
            if c == 0:
                ax.set_ylabel(label, fontsize=10.5)
        if last is not None and last < max(times):
            axes[r, -1].text(0.5, 0.12, f"last t = {last:g}", ha="center",
                             transform=axes[r, -1].transAxes, fontsize=9, color="0.35")
    fig.suptitle("Kelvin--Helmholtz on the moving mesh: targeted entropy dissipation "
                 "against the sigma-fraction control", fontsize=14, y=0.995)
    fig.text(0.5, 0.005, "density, matched IC and matched colour scale; grey panels are runs "
             "that had already failed", ha="center", fontsize=10, color="0.3")
    fig.tight_layout(rect=[0, 0.015, 1, 0.985])
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/kh-entropy-sweep-density.{ext}", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    for label, run in ARMS:
        ts, es = entropy_curve(run, lo, hi)
        if len(ts):
            ax.semilogy(ts, np.maximum(es, 1e-6), marker="o", ms=4, label=label)
    ax.axhline(1.0, color="0.6", lw=1, ls="--")
    ax.text(0.02, 1.15, "one full physical entropy span", fontsize=9, color="0.45")
    ax.set_xlabel("t"); ax.set_ylabel("max entropy excursion / initial span")
    ax.set_title("Numerical entropy production: exact invariant of ideal Euler")
    ax.legend(fontsize=9); ax.grid(alpha=0.3)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/kh-entropy-sweep-curves.{ext}", dpi=130)
    print(f"figures written to {OUT}")


if __name__ == "__main__":
    main()
