#!/usr/bin/env python3
"""Compare the default moving-N Sod result on glass48 and tiled glass96."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from plot_glass_sod_kh import load, sod_exact
from plot_sod_n_factorial import extended_metrics, geometry_metrics, snapshot_at
from plot_sod_n_mesh_motion import binned_volume_statistics


FIELDS = (
    ("rho", r"density $\rho$", 0),
    ("vx", r"longitudinal velocity $v_x$", 1),
    ("pressure", r"pressure $p$", 2),
    ("vy", r"transverse velocity $v_y$", None),
)


def field(data: dict[str, object], name: str) -> np.ndarray:
    if name == "vx":
        return np.asarray(data["velocity"])[:, 0]
    if name == "vy":
        return np.asarray(data["velocity"])[:, 1]
    return np.asarray(data[name])


def time_series(output: Path) -> list[dict[str, float]]:
    return [extended_metrics(path) for path in sorted(output.glob("snap_*.hdf5"))]


def endpoint_metrics(path: Path) -> dict[str, float]:
    result = extended_metrics(path)
    data = load(path, 2.0)
    absolute_vy = np.abs(np.asarray(data["velocity"])[:, 1])
    result.update(
        max_abs_transverse_velocity=float(absolute_vy.max()),
        p99_abs_transverse_velocity=float(np.quantile(absolute_vy, 0.99)),
    )
    return result


def analyse(high_root: Path, low_output: Path) -> dict[str, object]:
    manifest = json.loads((high_root / "campaign.json").read_text())
    high_output = Path(manifest["output"])
    levels = []
    for resolution, label, output in (
        (48, "relaxed glass48", low_output),
        (96, "tiled relaxed glass96", high_output),
    ):
        endpoint = snapshot_at(output, 0.2)
        levels.append(
            {
                "resolution": resolution,
                "label": label,
                "cells": resolution * resolution,
                "output": str(output),
                "endpoint": str(endpoint),
                "metrics": endpoint_metrics(endpoint),
                "geometry": geometry_metrics(output),
                "time_series": time_series(output),
            }
        )
    low, high = levels
    ratio_keys = (
        "density_l1",
        "velocity_l1",
        "pressure_l1",
        "transverse_velocity_rms",
        "raw_transverse_velocity_rms",
        "mass_transverse_velocity_rms",
        "max_abs_transverse_velocity",
        "p99_abs_transverse_velocity",
    )
    ratios = {
        key: high["metrics"][key] / low["metrics"][key]
        for key in ratio_keys
    }
    return {
        "campaign": str(high_root),
        "default_form": "N + RK2; contour residual; element comoving frame; Arpaia ALE mass",
        "levels": levels,
        "glass96_over_glass48": ratios,
        "formal_convergence_order_claimed": False,
        "reason": "glass96 periodically tiles glass48 and is not an independent relaxed glass realization",
    }


def plot_profiles(analysis: dict[str, object], figure_dir: Path) -> None:
    exact_x = np.linspace(0.0, 2.0, 4000, endpoint=False)
    exact = sod_exact(exact_x, 0.2)
    colors = ("#2563a6", "#d97706")
    fig, axes = plt.subplots(2, 4, figsize=(15.7, 7.2), sharex=True, sharey="col")
    for row, (level, color) in enumerate(zip(analysis["levels"], colors)):
        data = load(Path(level["endpoint"]), 2.0)
        x = np.asarray(data["position"])[:, 0]
        volume = np.asarray(data["volume"])
        bins = np.linspace(0.0, 2.0, 193)
        for column, (name, ylabel, exact_column) in enumerate(FIELDS):
            axis = axes[row, column]
            values = field(data, name)
            centre, mean, std = binned_volume_statistics(x, values, volume, bins)
            axis.scatter(x, values, s=1.5 if row else 2.3, alpha=0.17, color="0.30",
                         linewidths=0, rasterized=True)
            axis.fill_between(centre, mean - std, mean + std, color=color, alpha=0.22, linewidth=0)
            axis.plot(centre, mean, color=color, lw=1.15)
            if exact_column is not None:
                axis.plot(exact_x, exact[:, exact_column], color="black", lw=1.0)
            else:
                axis.axhline(0.0, color="black", lw=0.8)
            axis.grid(alpha=0.13)
            if row == 0:
                axis.set_title(ylabel, fontsize=10.5)
            if row == 1:
                axis.set_xlabel("x")
        metric = level["metrics"]
        axes[row, 0].set_ylabel(
            f"{level['label']}\nAREPO cell value",
            fontsize=9.2,
        )
        axes[row, 0].text(
            0.02,
            0.04,
            rf"$L_1(\rho)={metric['density_l1']:.4f}$",
            transform=axes[row, 0].transAxes,
            fontsize=8.0,
        )
        axes[row, 3].text(
            0.02,
            0.04,
            rf"RMS $v_y={metric['transverse_velocity_rms']:.3e}$",
            transform=axes[row, 3].transAxes,
            fontsize=8.0,
        )
    fig.suptitle(
        "Moving N-RK2 Sod at t=0.2 · contour residual · comoving frame · Arpaia mass",
        fontsize=14.5,
    )
    fig.text(
        0.5,
        0.012,
        "grey: individual AREPO cells · colour: volume-weighted 192-bin mean ±1σ · glass96 is a periodic tiling of glass48",
        ha="center",
        fontsize=8.5,
    )
    fig.tight_layout(rect=(0.015, 0.04, 1, 0.94))
    fig.savefig(figure_dir / "sod-n-default-glass48-glass96-profiles.png", dpi=220, bbox_inches="tight")
    fig.savefig(figure_dir / "sod-n-default-glass48-glass96-profiles.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_evolution(analysis: dict[str, object], figure_dir: Path) -> None:
    colors = ("#2563a6", "#d97706")
    fig, axes = plt.subplots(1, 3, figsize=(13.7, 4.3))
    keys = (
        ("density_l1", r"volume-weighted $L_1(\rho)$", "Density error"),
        ("pressure_l1", r"volume-weighted $L_1(p)$", "Pressure error"),
        ("transverse_velocity_rms", r"volume-weighted RMS $v_y$", "Transverse noise"),
    )
    for level, color in zip(analysis["levels"], colors):
        series = level["time_series"]
        time = [entry["time"] for entry in series]
        for axis, (key, ylabel, title) in zip(axes, keys):
            axis.plot(time, [entry[key] for entry in series], color=color, lw=1.5,
                      marker="o", ms=2.6, label=level["label"])
            axis.set(xlabel="time", ylabel=ylabel, title=title)
            axis.grid(alpha=0.14)
    axes[0].legend(frameon=False, fontsize=8.5)
    fig.suptitle("Resolution dependence of the default moving-N Sod result", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(figure_dir / "sod-n-default-glass48-glass96-evolution.png", dpi=220, bbox_inches="tight")
    fig.savefig(figure_dir / "sod-n-default-glass48-glass96-evolution.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--low-output", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    figure_dir = root / "figures"
    figure_dir.mkdir(exist_ok=True)
    analysis = analyse(root, args.low_output.resolve())
    (root / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n")
    plot_profiles(analysis, figure_dir)
    plot_evolution(analysis, figure_dir)
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
