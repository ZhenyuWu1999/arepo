#!/usr/bin/env python3
"""Plot the matched static/moving LDA KH comparison and N context."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np


LABELS = {
    "static": "static LDA RK2 · K-matrix total",
    "roe": "moving LDA RK2 · Roe + mesh split · b_T=σ̄_T",
    "contour": "moving LDA RK2 · P¹(U) contour · b_T=σ̄_T",
    "n": "moving N RK2 · P¹(U) contour · b_T=σ̄_T",
}
PLOT_TITLES = {
    "static": "static LDA RK2\nK-matrix total",
    "roe": "moving LDA RK2\n" + r"Roe + mesh split; $b_T=\bar{\sigma}_T$",
    "contour": "moving LDA RK2\n" + r"$P^1(U)$ contour; $b_T=\bar{\sigma}_T$",
    "n": "moving N RK2\n" + r"$P^1(U)$ contour; $b_T=\bar{\sigma}_T$",
}
FOOTER = "Moving cases: Arpaia modified-midpoint mass · RD_ALE_EQUALSTEP · RD_ALE_CFL_TIMESTEP"


def periodic_nearest(position: np.ndarray, query: np.ndarray,
                     chunk_size: int = 256) -> tuple[np.ndarray, np.ndarray]:
    """Return exact nearest neighbours on the unit periodic square.

    The chunked NumPy implementation keeps this diagnostic independent of
    SciPy, whose binary wheels are not always compatible with AREPO's analysis
    environment.
    """
    distance = np.empty(len(query))
    index = np.empty(len(query), dtype=np.intp)
    for first in range(0, len(query), chunk_size):
        last = min(first + chunk_size, len(query))
        delta = np.abs(query[first:last, None, :] - position[None, :, :])
        delta = np.minimum(delta, 1.0 - delta)
        distance_squared = np.sum(delta * delta, axis=2)
        nearest = np.argmin(distance_squared, axis=1)
        index[first:last] = nearest
        distance[first:last] = np.sqrt(distance_squared[np.arange(last - first), nearest])
    return distance, index


def load(path: Path) -> dict[str, np.ndarray | float]:
    with h5py.File(path, "r") as data:
        gas = data["PartType0"]
        result = {
            "time": float(np.atleast_1d(data["Header"].attrs["Time"])[0]),
            "position": np.asarray(gas["Coordinates"])[:, :2] % 1.0,
            "velocity": np.asarray(gas["Velocities"]),
            "rho": np.asarray(gas["Density"]),
            "mass": np.asarray(gas["Masses"]),
        }
        result["pressure"] = (
            np.asarray(gas["Pressure"])
            if "Pressure" in gas
            else 0.4 * result["rho"] * np.asarray(gas["InternalEnergy"])
        )
        result["volume"] = (
            np.asarray(gas["Volume"]) if "Volume" in gas else result["mass"] / result["rho"]
        )
    return result


def snapshots(output: Path) -> list[dict[str, np.ndarray | float]]:
    return [load(path) for path in sorted(output.glob("snap_*.hdf5"))]


def triangulation(position: np.ndarray) -> mtri.Triangulation:
    tri = mtri.Triangulation(position[:, 0], position[:, 1])
    points = position[tri.triangles]
    bad = (np.ptp(points[:, :, 0], axis=1) > 0.15) | (np.ptp(points[:, :, 1], axis=1) > 0.15)
    tri.set_mask(bad)
    return tri


def diagnostics(data: dict[str, np.ndarray | float]) -> dict[str, float]:
    position = np.asarray(data["position"])
    rho = np.asarray(data["rho"])
    mass = np.asarray(data["mass"])
    velocity = np.asarray(data["velocity"])
    reflected = np.column_stack((position[:, 0], (-position[:, 1]) % 1.0))
    distance, index = periodic_nearest(position, reflected)
    symmetry = np.average(np.abs(rho - rho[index]), weights=mass) / np.average(rho, weights=mass)
    return {
        "time": float(data["time"]),
        "rho_min": float(rho.min()),
        "rho_max": float(rho.max()),
        "pressure_min": float(np.min(data["pressure"])),
        "pressure_max": float(np.max(data["pressure"])),
        "vertical_kinetic_energy": float(0.5 * np.sum(mass * velocity[:, 1] ** 2)),
        "rho_standard_deviation": float(np.std(rho)),
        "reflection_density_l1": float(symmetry),
        "reflection_nearest_distance_rms": float(np.sqrt(np.mean(distance ** 2))),
    }


def panel(ax: plt.Axes, data: dict[str, np.ndarray | float], title: str, vmin: float, vmax: float):
    image = ax.tripcolor(triangulation(np.asarray(data["position"])), data["rho"],
                         shading="gouraud", cmap="viridis", vmin=vmin, vmax=vmax)
    ax.set(aspect="equal", xlim=(0, 1), ylim=(0, 1), xlabel="x", ylabel="y",
           title=f"{title}\nt={float(data['time']):g}")
    return image


def save(fig: plt.Figure, output: Path, stem: str) -> None:
    fig.savefig(output / f"{stem}.png", dpi=220, bbox_inches="tight")
    fig.savefig(output / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="LDA KH comparison root")
    parser.add_argument("--n-root", type=Path, required=True, help="completed moving-N campaign root")
    args = parser.parse_args()
    root = args.root.resolve()
    n_root = args.n_root.resolve()
    figure_dir = root / "figures"
    figure_dir.mkdir(exist_ok=True)

    series = {
        "static": snapshots(root / "static_LDA_Roe_RK2" / "output"),
        "roe": snapshots(root / "moving_LDA_Roe_comoving_RK2" / "output"),
        "contour": snapshots(root / "moving_LDA_contour_comoving_RK2" / "output"),
        "n_short": snapshots(n_root / "output_kh_t02"),
        "n_long": snapshots(n_root / "long" / "output_kh"),
    }
    common = {
        "static": series["static"][1],
        "roe": series["roe"][1],
        "contour": series["contour"][1],
        "n": series["n_short"][-1],
    }
    latest = {
        "static": series["static"][-1],
        "roe": series["roe"][-1],
        "contour": series["contour"][-1],
        "n": series["n_long"][-1],
    }

    rows = []
    for stage, collection in (("common_t0.2", common), ("latest_available", latest)):
        for key, data in collection.items():
            rows.append({"stage": stage, "case": key, "label": LABELS[key], **diagnostics(data)})
    rows.extend((
        {"stage": "termination", "case": "contour", "time": 0.32582092,
         "reason": "negative endpoint mass"},
        {"stage": "termination", "case": "roe", "time": 1.0079346,
         "reason": "negative endpoint mass"},
        {"stage": "completion", "case": "static", "time": 2.0, "reason": "completed"},
        {"stage": "completion", "case": "n", "time": 2.0, "reason": "completed"},
    ))
    (root / "analysis.json").write_text(json.dumps(rows, indent=2) + "\n")

    fig, axes = plt.subplots(2, 4, figsize=(16.4, 7.8))
    image = None
    for col, key in enumerate(("static", "roe", "contour", "n")):
        image = panel(axes[0, col], common[key], PLOT_TITLES[key], 0.85, 2.20)
        image = panel(axes[1, col], latest[key], PLOT_TITLES[key], 0.85, 2.20)
    axes[0, 0].text(-0.30, 0.5, "matched t=0.2", transform=axes[0, 0].transAxes,
                    rotation=90, va="center", weight="bold")
    axes[1, 0].text(-0.30, 0.5, "latest available", transform=axes[1, 0].transAxes,
                    rotation=90, va="center", weight="bold")
    colorbar_axis = fig.add_axes((0.925, 0.16, 0.014, 0.68))
    fig.colorbar(image, cax=colorbar_axis, label=r"density $\rho$")
    fig.suptitle("Kelvin–Helmholtz n=64: static versus moving LDA", fontsize=16, weight="bold")
    fig.text(0.5, 0.047, FOOTER, ha="center", fontsize=8.6, weight="semibold")
    fig.text(0.5, 0.022,
             "LDA termination: contour t=0.32582; Roe+split t=1.00793 (negative endpoint mass)",
             ha="center", fontsize=8.2, color="#8b2f2f")
    fig.subplots_adjust(left=0.065, right=0.90, bottom=0.115, top=0.86,
                        wspace=0.24, hspace=0.38)
    save(fig, figure_dir, "kh-lda-static-moving-density")

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.6))
    colors = {"static": "#2463a6", "roe": "#db7b2b", "contour": "#7b4fa3", "n": "#20866a"}
    energy_series = {
        "static": series["static"],
        "roe": series["roe"],
        "contour": series["contour"],
        "n": [series["n_short"][0], series["n_short"][-1], series["n_long"][-1]],
    }
    for key, values in energy_series.items():
        diag = [diagnostics(data) for data in values]
        axes[0].plot([d["time"] for d in diag], [d["vertical_kinetic_energy"] for d in diag],
                     "o-", color=colors[key], label=LABELS[key])
    for key, data in latest.items():
        d = diagnostics(data)
        axes[1].scatter(d["reflection_nearest_distance_rms"], d["reflection_density_l1"],
                        s=60, color=colors[key], label=f"{key}, t={d['time']:g}")
    axes[0].set(xlabel="time", ylabel=r"transverse kinetic energy $E_{k,y}$",
                title="Available evolution before completion/failure")
    axes[1].set(xlabel="RMS distance to reflected nearest generator",
                ylabel=r"reflected density $L_1 / \langle\rho\rangle$",
                title="Reflection symmetry at latest snapshot")
    axes[0].legend(frameon=False, fontsize=7.5)
    axes[1].legend(frameon=False, fontsize=7.5)
    for ax in axes:
        ax.grid(alpha=0.18)
    fig.suptitle("KH growth and symmetry diagnostics", fontsize=14, weight="bold")
    fig.text(0.5, 0.025, FOOTER, ha="center", fontsize=8.6, weight="semibold")
    fig.tight_layout(rect=(0, 0.07, 1, 0.92))
    save(fig, figure_dir, "kh-lda-energy-symmetry")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
