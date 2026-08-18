#!/usr/bin/env python3
"""Analyse the matched relaxed-glass Sod and KH RD/ALE campaign."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1] / "shocktube_1d"))
from Riemann import RiemannProblem  # noqa: E402


SOD_GAMMA = 5.0 / 3.0
LEFT = np.array([1.0, 0.0, 1.0])
RIGHT = np.array([0.125, 0.0, 0.1])
SOD_LABELS = {
    "static_LDA1": "static LDA1 · K-matrix total",
    "static_N1": "static N1 · K-matrix total",
    "moving_LDA_contour_cm_RK2": "moving LDA RK2 · contour + frame",
    "moving_N_contour_cm_RK2": "moving N RK2 · contour + frame",
}
KH_LABELS = {
    "static_LDA_RK2": "static LDA RK2 · K-matrix total",
    "moving_LDA_roe_cm_RK2": "moving LDA RK2 · Roe + split + frame",
    "moving_LDA_contour_cm_RK2": "moving LDA RK2 · contour + frame",
    "moving_N_contour_cm_RK2": "moving N RK2 · contour + frame",
}
COLORS = ("#2463a6", "#db7b2b", "#7b4fa3", "#20866a")
GLASS_FOOTER = (
    "relaxed periodic SWIFT glass48 · 2304 matched generators/IDs in every variant · "
    "no lattice jitter"
)
ALE_FOOTER = "moving: Arpaia modified-midpoint mass · b_T=σ̄_T · RD_ALE_EQUALSTEP"


def load(path: Path, box: float) -> dict[str, np.ndarray | float]:
    with h5py.File(path, "r") as data:
        gas = data["PartType0"]
        rho = np.asarray(gas["Density"])
        mass = np.asarray(gas["Masses"])
        pressure = (
            np.asarray(gas["Pressure"])
            if "Pressure" in gas
            else (0.4 if box == 1.0 else 2.0 / 3.0)
            * rho
            * np.asarray(gas["InternalEnergy"])
        )
        return {
            "time": float(np.atleast_1d(data["Header"].attrs["Time"])[0]),
            "position": np.asarray(gas["Coordinates"])[:, :2] % box,
            "velocity": np.asarray(gas["Velocities"]),
            "rho": rho,
            "pressure": pressure,
            "mass": mass,
            "volume": np.asarray(gas["Volume"]) if "Volume" in gas else mass / rho,
        }


def snapshots(output: Path, box: float) -> list[dict[str, np.ndarray | float]]:
    return [load(path, box) for path in sorted(output.glob("snap_*.hdf5"))]


def sod_exact(x: np.ndarray, time: float) -> np.ndarray:
    result = np.empty((len(x), 3), dtype=np.float64)
    low = x < 1.0
    if np.any(low):
        _, state, _ = RiemannProblem(x[low], 0.5, RIGHT, LEFT, SOD_GAMMA, time)
        result[low] = state
    if np.any(~low):
        _, state, _ = RiemannProblem(x[~low], 1.5, LEFT, RIGHT, SOD_GAMMA, time)
        result[~low] = state
    return result


def sod_metrics(data: dict[str, np.ndarray | float]) -> dict[str, float]:
    x = np.asarray(data["position"])[:, 0]
    exact = sod_exact(x, float(data["time"]))
    numerical = np.column_stack((data["rho"], np.asarray(data["velocity"])[:, 0], data["pressure"]))
    weight = np.asarray(data["volume"]).copy()
    weight /= weight.sum()
    error = np.sum(weight[:, None] * np.abs(numerical - exact), axis=0)
    vy_rms = np.sqrt(np.sum(weight * np.asarray(data["velocity"])[:, 1] ** 2))
    return {
        "time": float(data["time"]),
        "density_l1": float(error[0]),
        "velocity_l1": float(error[1]),
        "pressure_l1": float(error[2]),
        "rho_min": float(np.min(data["rho"])),
        "rho_max": float(np.max(data["rho"])),
        "pressure_min": float(np.min(data["pressure"])),
        "pressure_max": float(np.max(data["pressure"])),
        "transverse_velocity_rms": float(vy_rms),
    }


def kh_metrics(data: dict[str, np.ndarray | float]) -> dict[str, float]:
    rho = np.asarray(data["rho"])
    pressure = np.asarray(data["pressure"])
    mass = np.asarray(data["mass"])
    velocity = np.asarray(data["velocity"])
    return {
        "time": float(data["time"]),
        "rho_min": float(rho.min()),
        "rho_max": float(rho.max()),
        "pressure_min": float(pressure.min()),
        "pressure_max": float(pressure.max()),
        "rho_standard_deviation": float(rho.std()),
        "vertical_kinetic_energy": float(0.5 * np.sum(mass * velocity[:, 1] ** 2)),
    }


def triangulation(position: np.ndarray) -> mtri.Triangulation:
    tri = mtri.Triangulation(position[:, 0], position[:, 1])
    points = position[tri.triangles]
    bad = (np.ptp(points[:, :, 0], axis=1) > 0.15) | (np.ptp(points[:, :, 1], axis=1) > 0.15)
    tri.set_mask(bad)
    return tri


def run_outcome(output: Path, target_time: float) -> dict[str, object]:
    logs = sorted(output.glob("arepo-*.log"))
    last_sync_time = 0.0
    terminated = False
    reason = ""
    if logs:
        with logs[-1].open(errors="replace") as stream:
            for line in stream:
                match = re.search(r"Sync-Point \d+, Time: ([0-9.eE+-]+)", line)
                if match:
                    last_sync_time = float(match.group(1))
                if "very bad" in line:
                    reason = "negative endpoint mass"
                elif "RD predictor state invalid" in line:
                    reason = "non-physical RK predictor"
                if "TERMINATE:" in line:
                    terminated = True
    return {
        "outcome": "failed" if terminated else "completed" if last_sync_time >= target_time else "incomplete",
        "run_time": last_sync_time,
        "reason": reason,
    }


def save(fig: plt.Figure, directory: Path, stem: str) -> None:
    fig.savefig(directory / f"{stem}.png", dpi=220, bbox_inches="tight")
    fig.savefig(directory / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_sod(root: Path, figure_dir: Path) -> list[dict[str, object]]:
    x_exact = np.linspace(0.0, 2.0, 4000, endpoint=False)
    exact = sod_exact(x_exact, 0.2)
    rows = []
    data_by_variant = {}
    for variant in SOD_LABELS:
        data = load(root / "sod" / "runs" / variant / "output" / "snap_001.hdf5", 2.0)
        data_by_variant[variant] = data
        rows.append({"problem": "sod", "variant": variant, **sod_metrics(data)})

    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.5), sharex=True, sharey=True)
    for ax, (variant, label), color in zip(axes.flat, SOD_LABELS.items(), COLORS):
        data = data_by_variant[variant]
        metric = next(row for row in rows if row["variant"] == variant)
        ax.plot(x_exact, exact[:, 0], color="black", lw=1.8, label="exact")
        ax.scatter(np.asarray(data["position"])[:, 0], data["rho"], s=3.0, alpha=0.42,
                   color=color, linewidths=0, label=label)
        ax.set_title(label, fontsize=10)
        ax.text(0.02, 0.04,
                rf"$\rho_{{min}}={metric['rho_min']:.4f}$; RMS $v_y={metric['transverse_velocity_rms']:.3e}$",
                transform=ax.transAxes, fontsize=8)
        ax.grid(alpha=0.14)
    for ax in axes[:, 0]:
        ax.set_ylabel(r"density $\rho$")
    for ax in axes[-1]:
        ax.set_xlabel("x")
    fig.suptitle("Sod on one matched relaxed glass · t=0.2", fontsize=15, weight="bold")
    fig.text(0.5, 0.045, GLASS_FOOTER, ha="center", fontsize=8.5, weight="semibold")
    fig.text(0.5, 0.021, ALE_FOOTER, ha="center", fontsize=8.2)
    fig.tight_layout(rect=(0, 0.075, 1, 0.94))
    save(fig, figure_dir, "glass-sod-density-scatter")
    return rows


def plot_kh(root: Path, figure_dir: Path) -> list[dict[str, object]]:
    all_series = {
        variant: snapshots(root / "kh" / "runs" / variant / "output", 1.0)
        for variant in KH_LABELS
    }
    rows = []
    common = {}
    latest = {}
    outcomes = {}
    for variant, series in all_series.items():
        output = root / "kh" / "runs" / variant / "output"
        outcomes[variant] = run_outcome(output, 2.0)
        common[variant] = min(series, key=lambda data: abs(float(data["time"]) - 0.2))
        latest[variant] = series[-1]
        for stage, data in (("common_t0.2", common[variant]), ("latest_available", latest[variant])):
            rows.append({"problem": "kh", "stage": stage, "variant": variant,
                         **kh_metrics(data), **outcomes[variant]})

    fig, axes = plt.subplots(2, 4, figsize=(15.8, 7.7))
    image = None
    for column, ((variant, label), color) in enumerate(zip(KH_LABELS.items(), COLORS)):
        for row, data in enumerate((common[variant], latest[variant])):
            image = axes[row, column].tripcolor(
                triangulation(np.asarray(data["position"])), data["rho"], shading="gouraud",
                cmap="viridis", vmin=0.85, vmax=2.20,
            )
            axes[row, column].set(
                aspect="equal", xlim=(0, 1), ylim=(0, 1), xlabel="x", ylabel="y",
                title=f"{label}\nt={float(data['time']):g}",
            )
    axes[0, 0].text(-0.29, 0.5, "nearest t=0.2", transform=axes[0, 0].transAxes,
                    rotation=90, va="center", weight="bold")
    axes[1, 0].text(-0.29, 0.5, "latest available", transform=axes[1, 0].transAxes,
                    rotation=90, va="center", weight="bold")
    colorbar_axis = fig.add_axes((0.925, 0.16, 0.014, 0.68))
    fig.colorbar(image, cax=colorbar_axis, label=r"density $\rho$")
    fig.suptitle("Kelvin–Helmholtz on one matched relaxed glass", fontsize=15, weight="bold")
    fig.text(0.5, 0.047, GLASS_FOOTER, ha="center", fontsize=8.5, weight="semibold")
    fig.text(0.5, 0.023, ALE_FOOTER, ha="center", fontsize=8.2)
    failures = [
        f"{variant.replace('_', ' ')}: t={outcome['run_time']:.6g}, {outcome['reason']}"
        for variant, outcome in outcomes.items() if outcome["outcome"] == "failed"
    ]
    if failures:
        fig.text(0.5, 0.004, "terminated · " + "; ".join(failures), ha="center",
                 fontsize=7.8, color="#8b2f2f")
    fig.subplots_adjust(left=0.065, right=0.90, bottom=0.11, top=0.86, wspace=0.25, hspace=0.38)
    save(fig, figure_dir, "glass-kh-static-moving-density")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    figure_dir = root / "figures"
    figure_dir.mkdir(exist_ok=True)
    rows = plot_sod(root, figure_dir) + plot_kh(root, figure_dir)
    (root / "analysis.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
