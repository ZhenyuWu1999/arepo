#!/usr/bin/env python3
"""Compare static, default moving, and shear-floored moving N-Sod on glass48."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from plot_glass_sod_kh import load, sod_exact
from plot_sod_n_factorial import extended_metrics, geometry_metrics, snapshot_at
from plot_sod_n_mesh_motion import binned_volume_statistics


LABELS = {
    "static": "static N-RK2\nK-matrix total",
    "moving": "moving N-RK2\ncontour · co-moving · Arpaia · $\\epsilon_s=0$",
    "floor": "moving N-RK2\ncontour · co-moving · Arpaia · shear floor $\\epsilon_s=0.45$",
}
COLORS = {"static": "#2563a6", "moving": "#d97706", "floor": "#20866a"}


def volume_quantile(values: np.ndarray, volume: np.ndarray, quantile: float) -> float:
    order = np.argsort(values)
    cumulative = np.cumsum(volume[order]) / np.sum(volume)
    return float(values[order[min(np.searchsorted(cumulative, quantile), len(order) - 1)]])


def snapshot_metrics(path: Path) -> dict[str, float]:
    result = extended_metrics(path)
    data = load(path, 2.0)
    vy = np.abs(np.asarray(data["velocity"])[:, 1])
    volume = np.asarray(data["volume"])
    result.update(
        transverse_velocity_p99_volume=volume_quantile(vy, volume, 0.99),
        transverse_velocity_max=float(np.max(vy)),
    )
    return result


def log_diagnostics(output: Path) -> dict[str, float | None]:
    logs = sorted(output.glob("arepo-*.log"))
    result: dict[str, float | None] = {
        "predictor_min_rho": None,
        "predictor_min_pressure": None,
        "max_element_conservation_defect_relative": None,
        "min_sminus_pivot_ratio": None,
        "min_cfl_margin_over_selected": None,
        "max_midpoint_endpoint_conservation_norm": None,
    }
    if not logs:
        return result

    predictor_rho: list[float] = []
    predictor_pressure: list[float] = []
    conservation: list[float] = []
    pivot: list[float] = []
    cfl_margin: list[float] = []
    endpoint_conservation: list[float] = []
    for line in logs[-1].read_text(errors="replace").splitlines():
        match = re.search(
            r"predictor_min_rho=([0-9.eE+-]+) predictor_min_press=([0-9.eE+-]+)",
            line,
        )
        if match:
            predictor_rho.append(float(match.group(1)))
            predictor_pressure.append(float(match.group(2)))
        match = re.search(
            r"min_pivot_ratio=([0-9.eE+-]+).*cons_defect_rel=([0-9.eE+-]+)",
            line,
        )
        if match:
            pivot.append(float(match.group(1)))
            conservation.append(float(match.group(2)))
        match = re.search(r"rd_over_selected=([0-9.eE+-]+)", line)
        if match:
            cfl_margin.append(float(match.group(1)))
        match = re.search(r"endpoint_cons=([0-9.eE+-]+)", line)
        if match:
            endpoint_conservation.append(float(match.group(1)))

    if predictor_rho:
        result["predictor_min_rho"] = min(predictor_rho)
        result["predictor_min_pressure"] = min(predictor_pressure)
    if conservation:
        result["max_element_conservation_defect_relative"] = max(conservation)
    if pivot:
        result["min_sminus_pivot_ratio"] = min(pivot)
    if cfl_margin:
        result["min_cfl_margin_over_selected"] = min(cfl_margin)
    if endpoint_conservation:
        result["max_midpoint_endpoint_conservation_norm"] = max(endpoint_conservation)
    return result


def analyse(paths: dict[str, Path]) -> dict[str, object]:
    cases = []
    for variant, output in paths.items():
        snapshots = []
        for path in sorted(output.glob("snap_*.hdf5")):
            snapshots.append(snapshot_metrics(path))
        endpoint = snapshot_at(output, 0.2)
        cases.append(
            {
                "variant": variant,
                "label": LABELS[variant],
                "output": str(output),
                "endpoint_snapshot": str(endpoint),
                "endpoint": snapshot_metrics(endpoint),
                "time_series": snapshots,
                "geometry": geometry_metrics(output),
                "diagnostics": log_diagnostics(output),
            }
        )

    static_rms = cases[0]["endpoint"]["transverse_velocity_rms"]
    for case in cases:
        case["endpoint"]["rms_vy_over_static"] = (
            case["endpoint"]["transverse_velocity_rms"] / static_rms
        )
    return {"cases": cases}


def plot_profiles(analysis: dict[str, object], output: Path, bins: int) -> None:
    x_exact = np.linspace(0.0, 2.0, 4000, endpoint=False)
    exact = sod_exact(x_exact, 0.2)
    edges = np.linspace(0.0, 2.0, bins + 1)
    quantities = (
        ("rho", r"density $\rho$", exact[:, 0]),
        ("pressure", r"pressure $p$", exact[:, 2]),
        ("vy", r"transverse velocity $v_y$", np.zeros_like(x_exact)),
    )
    fig, axes = plt.subplots(3, 3, figsize=(15.0, 10.0), sharex=True, sharey="row")
    for column, case in enumerate(analysis["cases"]):
        variant = case["variant"]
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
            axis.scatter(
                x,
                values[key],
                s=2.6,
                alpha=0.20,
                color="0.35",
                linewidths=0,
                rasterized=True,
            )
            axis.fill_between(
                centre,
                mean - std,
                mean + std,
                color=COLORS[variant],
                alpha=0.20,
                linewidth=0,
            )
            axis.plot(centre, mean, color=COLORS[variant], lw=1.4)
            axis.plot(x_exact, reference, color="black", lw=1.1)
            axis.grid(alpha=0.13)
            if column == 0:
                axis.set_ylabel(ylabel)
            if row == 0:
                axis.set_title(case["label"], fontsize=10.0)
            if row == 2:
                axis.set_xlabel("x")

        metric = case["endpoint"]
        axes[0, column].text(
            0.02,
            0.04,
            rf"$L_1(\rho)={metric['density_l1']:.4f}$",
            transform=axes[0, column].transAxes,
            fontsize=8.5,
        )
        axes[1, column].text(
            0.02,
            0.04,
            rf"$p_{{min}}={metric['pressure_min']:.4f}$",
            transform=axes[1, column].transAxes,
            fontsize=8.5,
        )
        axes[2, column].text(
            0.02,
            0.04,
            "RMS $v_y$="
            f"{metric['transverse_velocity_rms']:.3e}\n"
            f"ratio/static={metric['rms_vy_over_static']:.3f}",
            transform=axes[2, column].transAxes,
            fontsize=8.5,
        )

    fig.suptitle("glass48 Sod at $t=0.2$: online ALE shear-eigenvalue-floor check", fontsize=15)
    fig.text(
        0.5,
        0.014,
        "2304 identical relaxed-glass generators/IDs · $\\gamma=5/3$ · grey: cells · "
        "colour: volume-weighted 96-bin mean $\\pm1\\sigma$ · black: exact solution",
        ha="center",
        fontsize=8.5,
    )
    fig.tight_layout(rect=(0.035, 0.04, 0.995, 0.94))
    fig.savefig(output, dpi=220, bbox_inches="tight")
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def plot_evolution(analysis: dict[str, object], output: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.6))
    for case in analysis["cases"]:
        series = case["time_series"]
        time = np.asarray([row["time"] for row in series])
        color = COLORS[case["variant"]]
        axes[0].plot(
            time,
            [row["transverse_velocity_rms"] for row in series],
            color=color,
            marker="o",
            markersize=2.5,
            lw=1.4,
            label=case["label"].replace("\n", " · "),
        )
        axes[1].plot(
            time,
            [row["density_l1"] for row in series],
            color=color,
            marker="o",
            markersize=2.5,
            lw=1.4,
        )
        axes[2].plot(
            time,
            [row["pressure_min"] for row in series],
            color=color,
            marker="o",
            markersize=2.5,
            lw=1.4,
        )
    axes[0].set(xlabel="time", ylabel=r"volume-weighted RMS $v_y$", title="Transverse noise")
    axes[1].set(xlabel="time", ylabel=r"volume-weighted $L_1(\rho)$", title="Density error")
    axes[2].set(xlabel="time", ylabel=r"minimum $p$", title="Endpoint positivity margin")
    for axis in axes:
        axis.grid(alpha=0.14)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=1, frameon=False, fontsize=8.4)
    fig.suptitle("glass48 Sod evolution: static, default moving, and shear floor", fontsize=14)
    fig.tight_layout(rect=(0, 0.22, 1, 0.93))
    fig.savefig(output, dpi=220, bbox_inches="tight")
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--static", required=True, type=Path)
    parser.add_argument("--moving", required=True, type=Path)
    parser.add_argument("--floor", required=True, type=Path)
    parser.add_argument("--figure-dir", required=True, type=Path)
    parser.add_argument("--bins", type=int, default=96)
    args = parser.parse_args()

    figure_dir = args.figure_dir.resolve()
    figure_dir.mkdir(parents=True, exist_ok=True)
    analysis = analyse(
        {
            "static": args.static.resolve(),
            "moving": args.moving.resolve(),
            "floor": args.floor.resolve(),
        }
    )
    (figure_dir.parent / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n")
    plot_profiles(analysis, figure_dir / "sod-n-shear-floor-profiles.png", args.bins)
    plot_evolution(analysis, figure_dir / "sod-n-shear-floor-evolution.png")
    print(
        json.dumps(
            [
                {
                    "variant": case["variant"],
                    **case["endpoint"],
                    **case["geometry"],
                    **case["diagnostics"],
                }
                for case in analysis["cases"]
            ],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
