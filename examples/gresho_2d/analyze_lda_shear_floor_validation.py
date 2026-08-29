#!/usr/bin/env python3
"""Analyse the LDA ALE shear-floor Gresho and Yee validation campaign."""

import argparse
import json
from pathlib import Path

import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def gresho_exact(radius):
    return np.where(radius < 0.2, 5.0 * radius,
                    np.where(radius < 0.4, 2.0 - 5.0 * radius, 0.0))


def load_gresho(snapshot, boost):
    with h5py.File(snapshot, "r") as handle:
        gas = handle["PartType0"]
        xy = gas["Coordinates"][:, :2]
        velocity = gas["Velocities"][:, :2]
        mass = gas["Masses"][:]
        time = float(handle["Header"].attrs["Time"])
    displacement = xy - 0.5
    displacement -= np.round(displacement)
    radius = np.linalg.norm(displacement, axis=1)
    velocity = velocity.copy()
    velocity[:, 0] -= boost
    vphi = np.divide(-velocity[:, 0] * displacement[:, 1]
                     + velocity[:, 1] * displacement[:, 0], radius,
                     out=np.zeros_like(radius), where=radius > 0.0)
    error = float(np.average(np.abs(vphi - gresho_exact(radius)), weights=mass))
    return time, radius, vphi, error


def load_yee(snapshot):
    gamma = 1.4
    with h5py.File(snapshot, "r") as handle:
        gas = handle["PartType0"]
        xy = gas["Coordinates"][:, :2]
        density = gas["Density"][:]
        volume = gas["Volume"][:]
        time = float(handle["Header"].attrs["Time"])
    displacement = xy - 5.0
    displacement -= 10.0 * np.round(displacement / 10.0)
    radius2 = np.sum(displacement * displacement, axis=1)
    temperature = (1.0 - (gamma - 1.0) * 25.0
                   / (8.0 * np.pi**2 * gamma) * np.exp(1.0 - radius2))
    exact = temperature ** (1.0 / (gamma - 1.0))
    error = float(np.average(np.abs(density - exact), weights=volume))
    return time, error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--gresho-control-root", type=Path, required=True)
    args = parser.parse_args()
    campaign = args.campaign.resolve()
    figures = campaign / "figures"
    figures.mkdir(exist_ok=True)

    gresho_paths = {
        "control": {
            0: args.gresho_control_root / "lda_gresho_b0/output_rank1/snap_001.hdf5",
            10: args.gresho_control_root / "lda_gresho_b10/output_rank1/snap_001.hdf5",
        },
        "floor045": {
            0: campaign / "gresho_floor045_b0/output_quiet/snap_001.hdf5",
            10: campaign / "gresho_floor045_b10/output_quiet/snap_001.hdf5",
        },
    }
    gresho = {arm: {boost: load_gresho(path, boost)
                    for boost, path in paths.items()}
               for arm, paths in gresho_paths.items()}

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.3), sharex=True, sharey=True)
    rr = np.linspace(0.0, 0.5, 600)
    colours = {"control": "#2369a1", "floor045": "#d84a3a"}
    labels = {"control": "LDA control", "floor045": r"LDA shear floor $\epsilon=0.45$"}
    for axis, boost in zip(axes, (0, 10)):
        axis.plot(rr, gresho_exact(rr), color="black", lw=1.7, label="analytic")
        for arm in ("control", "floor045"):
            _, radius, vphi, error = gresho[arm][boost]
            axis.scatter(radius, vphi, s=4, alpha=0.20, linewidths=0,
                         rasterized=True, color=colours[arm],
                         label=f"{labels[arm]} (L1={error:.3e})")
        axis.set_title(f"Gresho glass $48^2$, boost={boost}, $t=1$")
        axis.set_xlabel("radius")
        axis.grid(alpha=0.18)
    axes[0].set_ylabel(r"de-boosted $v_\phi$")
    axes[0].legend(fontsize=8, loc="upper right")
    axes[1].legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(figures / "gresho-lda-shear-floor-boost-pair.png", dpi=220)
    plt.close(fig)

    resolutions = (32, 64)
    yee = {}
    for arm in ("control", "floor045"):
        yee[arm] = {}
        for resolution in resolutions:
            snapshot = campaign / f"yee_{arm}_n{resolution}/output/snap_001.hdf5"
            time, error = load_yee(snapshot)
            yee[arm][resolution] = {"time": time, "L1_density": error}
        e32 = yee[arm][32]["L1_density"]
        e64 = yee[arm][64]["L1_density"]
        yee[arm]["order_32_64"] = float(np.log(e32 / e64) / np.log(2.0))

    fig, axis = plt.subplots(figsize=(6.3, 4.7))
    for arm, marker in (("control", "o"), ("floor045", "s")):
        errors = [yee[arm][n]["L1_density"] for n in resolutions]
        order = yee[arm]["order_32_64"]
        axis.loglog(resolutions, errors, marker=marker, lw=1.8,
                    color=colours[arm], label=f"{labels[arm]} (p={order:.2f})")
    axis.set_xticks(resolutions, labels=[str(n) for n in resolutions])
    axis.set_xlabel("linear resolution N")
    axis.set_ylabel(r"volume-weighted $L_1(\rho)$")
    axis.set_title("Yee vortex moving-LDA resolution pair, $t=1$")
    axis.grid(which="both", alpha=0.22)
    axis.legend()
    fig.tight_layout()
    fig.savefig(figures / "yee-lda-shear-floor-resolution-pair.png", dpi=220)
    plt.close(fig)

    result = {
        "gresho": {
            arm: {str(boost): {"time": values[0], "L1_vphi_mass_weighted": values[3]}
                  for boost, values in boosts.items()}
            for arm, boosts in gresho.items()
        },
        "yee": yee,
    }
    (campaign / "analysis.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
