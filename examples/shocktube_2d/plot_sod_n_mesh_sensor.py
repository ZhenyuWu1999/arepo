#!/usr/bin/env python3
"""Analyse and plot the low-resolution moving-N Sod mesh-sensor experiment."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import numpy as np

from plot_glass_sod_kh import load, sod_exact
from plot_sod_n_factorial import extended_metrics, geometry_metrics, snapshot_at
from plot_sod_n_mesh_motion import binned_volume_statistics


LABELS = {
    "baseline": "baseline quasi-Lagrangian",
    "shock_a05": r"shock sensor, $\alpha=0.5$",
    "allwaves_a05": r"all-wave sensor, $\alpha=0.5$",
}
COLORS = {"baseline": "#2563a6", "shock_a05": "#d97706", "allwaves_a05": "#20866a"}
SENSOR_PATTERN = re.compile(
    r"RD_ALE_MESH_SENSOR: time=(?P<time>[0-9.eE+-]+).*?"
    r"active_fraction=(?P<active>[0-9.eE+-]+).*?mean_sensor=(?P<mean>[0-9.eE+-]+).*?"
    r"corr_rms=(?P<corr>[0-9.eE+-]+).*?corr_max=(?P<corrmax>[0-9.eE+-]+).*?"
    r"rel_rms_before=(?P<before>[0-9.eE+-]+).*?rel_rms_after=(?P<after>[0-9.eE+-]+)"
)


def sensor_series(output: Path) -> list[dict[str, float]]:
    logs = sorted(output.glob("arepo-*.log"))
    if not logs:
        return []
    rows = []
    for line in logs[-1].read_text(errors="replace").splitlines():
        match = SENSOR_PATTERN.search(line)
        if match:
            rows.append({name: float(value) for name, value in match.groupdict().items()})
    return rows


def extra_endpoint_metrics(path: Path) -> dict[str, float]:
    result = extended_metrics(path)
    data = load(path, 2.0)
    vy = np.abs(np.asarray(data["velocity"])[:, 1])
    volume = np.asarray(data["volume"])
    order = np.argsort(vy)
    cumulative = np.cumsum(volume[order]) / volume.sum()
    result["transverse_velocity_p99_volume"] = float(vy[order[np.searchsorted(cumulative, 0.99)]])
    result["transverse_velocity_max"] = float(vy.max())
    with h5py.File(path, "r") as handle:
        gas = handle["PartType0"]
        if "VertexVelocity" in gas:
            slip = np.asarray(gas["Velocities"])[:, :2] - np.asarray(gas["VertexVelocity"])[:, :2]
            result["fluid_mesh_slip_rms"] = float(np.sqrt(np.sum(volume * np.sum(slip**2, axis=1)) / volume.sum()))
    return result


def analyse(root: Path) -> dict[str, object]:
    manifest = json.loads((root / "campaign.json").read_text())
    cases = [
        {
            "variant": "baseline",
            "output": manifest["baseline_output"],
            "sensor": "none",
            "alpha": 0.0,
        }
    ] + manifest["cases"]
    rows = []
    for original in cases:
        case = dict(original)
        output = Path(case["output"])
        snapshots = []
        for path in sorted(output.glob("snap_*.hdf5")):
            snapshots.append(extra_endpoint_metrics(path))
        endpoint_path = snapshot_at(output, 0.2)
        case.update(
            label=LABELS[case["variant"]],
            endpoint_snapshot=str(endpoint_path),
            endpoint=extra_endpoint_metrics(endpoint_path),
            geometry=geometry_metrics(output),
            time_series=snapshots,
            sensor_series=sensor_series(output),
        )
        rows.append(case)
    return {"campaign": str(root), "cases": rows}


def plot_profiles(analysis: dict[str, object], figure_dir: Path) -> None:
    x_exact = np.linspace(0.0, 2.0, 4000, endpoint=False)
    exact = sod_exact(x_exact, 0.2)
    edges = np.linspace(0.0, 2.0, 97)
    quantities = (
        ("rho", r"density $\rho$", exact[:, 0]),
        ("pressure", r"pressure $p$", exact[:, 2]),
        ("vy", r"transverse velocity $v_y$", np.zeros_like(x_exact)),
    )
    fig, axes = plt.subplots(3, 3, figsize=(14.2, 9.8), sharex=True, sharey="row")
    for column, case in enumerate(analysis["cases"]):
        data = load(Path(case["endpoint_snapshot"]), 2.0)
        x = np.asarray(data["position"])[:, 0]
        volume = np.asarray(data["volume"])
        values = {
            "rho": np.asarray(data["rho"]),
            "pressure": np.asarray(data["pressure"]),
            "vy": np.asarray(data["velocity"])[:, 1],
        }
        for row, (key, ylabel, reference) in enumerate(quantities):
            axis = axes[row, column]
            centre, mean, std = binned_volume_statistics(x, values[key], volume, edges)
            axis.scatter(x, values[key], s=2.6, alpha=0.22, color="0.35", linewidths=0, rasterized=True)
            axis.fill_between(centre, mean - std, mean + std, color=COLORS[case["variant"]], alpha=0.20, linewidth=0)
            axis.plot(centre, mean, color=COLORS[case["variant"]], lw=1.4)
            axis.plot(x_exact, reference, color="black", lw=1.1)
            axis.grid(alpha=0.13)
            if column == 0:
                axis.set_ylabel(ylabel)
            if row == 0:
                axis.set_title(case["label"], fontsize=10.5)
            if row == 2:
                axis.set_xlabel("x")
        metric = case["endpoint"]
        axes[0, column].text(0.02, 0.04, rf"$L_1(\rho)={metric['density_l1']:.4f}$", transform=axes[0, column].transAxes, fontsize=8.5)
        axes[1, column].text(0.02, 0.04, rf"$L_1(p)={metric['pressure_l1']:.4f}$", transform=axes[1, column].transAxes, fontsize=8.5)
        axes[2, column].text(0.02, 0.04, rf"RMS $v_y={metric['transverse_velocity_rms']:.3e}$", transform=axes[2, column].transAxes, fontsize=8.5)
    fig.suptitle("Moving N-RK2 Sod: sensor-controlled mesh velocity · t=0.2", fontsize=15)
    fig.text(0.5, 0.018, "matched relaxed periodic glass48 · contour + comoving frame + Arpaia · grey cells · colour: volume-weighted mean ±1σ", ha="center", fontsize=8.3)
    fig.tight_layout(rect=(0.035, 0.045, 0.995, 0.94))
    fig.savefig(figure_dir / "sod-n-mesh-sensor-profiles.png", dpi=220, bbox_inches="tight")
    fig.savefig(figure_dir / "sod-n-mesh-sensor-profiles.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_evolution(analysis: dict[str, object], figure_dir: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14.0, 4.5))
    for case in analysis["cases"]:
        series = case["time_series"]
        time = np.asarray([row["time"] for row in series])
        axes[0].plot(time, [row["transverse_velocity_rms"] for row in series], color=COLORS[case["variant"]], lw=1.5, marker="o", markersize=2.8, label=case["label"])
        axes[1].plot(time, [row["density_l1"] for row in series], color=COLORS[case["variant"]], lw=1.5, marker="o", markersize=2.8)
        sensor = case["sensor_series"]
        if sensor:
            axes[2].plot([row["time"] for row in sensor], [row["active"] for row in sensor], color=COLORS[case["variant"]], lw=1.25)
    axes[0].set(xlabel="time", ylabel=r"volume-weighted RMS $v_y$", title="Transverse noise")
    axes[1].set(xlabel="time", ylabel=r"volume-weighted $L_1(\rho)$", title="Density error")
    axes[2].set(xlabel="time", ylabel="active cell fraction", title="Mesh-motion sensor support")
    for axis in axes:
        axis.grid(alpha=0.14)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, fontsize=8.5)
    fig.suptitle("Moving-N Sod sensor evolution", fontsize=14)
    fig.tight_layout(rect=(0, 0.13, 1, 0.93))
    fig.savefig(figure_dir / "sod-n-mesh-sensor-evolution.png", dpi=220, bbox_inches="tight")
    fig.savefig(figure_dir / "sod-n-mesh-sensor-evolution.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    figure_dir = root / "figures"
    figure_dir.mkdir(exist_ok=True)
    analysis = analyse(root)
    (root / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n")
    plot_profiles(analysis, figure_dir)
    plot_evolution(analysis, figure_dir)
    print(json.dumps([{"variant": case["variant"], **case["endpoint"], **case["geometry"]} for case in analysis["cases"]], indent=2))


if __name__ == "__main__":
    main()
