#!/usr/bin/env python3
"""Compare matched static, zero-mesh ALE, and moving-mesh N-scheme Sod runs.

The points are the actual AREPO generators.  The coloured curves and bands are
volume-weighted x-bin means and standard deviations, so a non-uniform moving
point cloud cannot dominate the spatial comparison merely by oversampling.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from plot_glass_sod_kh import load, sod_exact, sod_metrics


LABELS = (
    "static N RK2 · K-matrix total",
    "zero-mesh ALE N RK2 · contour + element frame",
    "moving N RK2 · contour + element frame",
)
COLORS = ("#2463a6", "#7b4fa3", "#db7b2b")


def binned_volume_statistics(
    x: np.ndarray,
    value: np.ndarray,
    volume: np.ndarray,
    edges: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return bin centres and volume-weighted mean and standard deviation."""
    index = np.clip(np.digitize(x, edges) - 1, 0, len(edges) - 2)
    centre = 0.5 * (edges[:-1] + edges[1:])
    mean = np.full(len(centre), np.nan)
    std = np.full(len(centre), np.nan)
    for bin_index in range(len(centre)):
        mask = index == bin_index
        if not np.any(mask):
            continue
        weight = volume[mask]
        weight = weight / weight.sum()
        mean[bin_index] = np.sum(weight * value[mask])
        std[bin_index] = np.sqrt(np.sum(weight * (value[mask] - mean[bin_index]) ** 2))
    return centre, mean, std


def plot_comparison(paths: list[Path], output: Path, bins: int) -> list[dict[str, float | str]]:
    data = [load(path, 2.0) for path in paths]
    times = np.asarray([float(item["time"]) for item in data])
    if not np.allclose(times, times[0], rtol=0.0, atol=2.0e-6):
        raise ValueError(f"Snapshots are not time matched: {times}")

    x_exact = np.linspace(0.0, 2.0, 4000, endpoint=False)
    exact = sod_exact(x_exact, float(times.mean()))
    edges = np.linspace(0.0, 2.0, bins + 1)
    quantities = (
        ("rho", r"density $\rho$", exact[:, 0]),
        ("pressure", r"pressure $p$", exact[:, 2]),
        ("vy", r"transverse velocity $v_y$", np.zeros_like(x_exact)),
    )

    fig, axes = plt.subplots(3, 3, figsize=(14.6, 10.2), sharex=True, sharey="row")
    metrics: list[dict[str, float | str]] = []
    for column, (item, label, color) in enumerate(zip(data, LABELS, COLORS)):
        x = np.asarray(item["position"])[:, 0]
        volume = np.asarray(item["volume"])
        velocity = np.asarray(item["velocity"])
        values = {
            "rho": np.asarray(item["rho"]),
            "pressure": np.asarray(item["pressure"]),
            "vy": velocity[:, 1],
        }
        metric = {"variant": label, **sod_metrics(item)}
        metric["volume_max_over_min"] = float(volume.max() / volume.min())
        metrics.append(metric)

        for row, (key, ylabel, exact_value) in enumerate(quantities):
            axis = axes[row, column]
            centre, mean, std = binned_volume_statistics(x, values[key], volume, edges)
            axis.scatter(x, values[key], s=2.6, alpha=0.22, color="0.35", linewidths=0,
                         rasterized=True, label="AREPO cells")
            axis.fill_between(centre, mean - std, mean + std, color=color, alpha=0.20,
                              linewidth=0, label=r"volume-weighted $\pm1\sigma$")
            axis.plot(centre, mean, color=color, lw=1.4, label="volume-weighted bin mean")
            axis.plot(x_exact, exact_value, color="black", lw=1.15, label="exact")
            axis.grid(alpha=0.13)
            if column == 0:
                axis.set_ylabel(ylabel)
            if row == 0:
                axis.set_title(label, fontsize=10.5)
            if row == 2:
                axis.set_xlabel("x")

        axes[0, column].text(
            0.02,
            0.04,
            rf"$\rho_{{min}}={metric['rho_min']:.4f}$",
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
            rf"volume RMS $v_y={metric['transverse_velocity_rms']:.3e}$",
            transform=axes[2, column].transAxes,
            fontsize=8.5,
        )

    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", ncol=4, frameon=False,
               bbox_to_anchor=(0.5, 0.948), fontsize=8.5)
    fig.suptitle("Sod: isolating actual mesh motion in the N scheme", fontsize=15)
    fig.text(
        0.5,
        0.018,
        "matched relaxed periodic glass48 · 2304 generators · t=0.2 · "
        "moving uses Arpaia modified-midpoint mass and b_T=σ̄_T",
        ha="center",
        fontsize=8.5,
    )
    fig.tight_layout(rect=(0.035, 0.045, 0.995, 0.91))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220, bbox_inches="tight")
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    output.with_suffix(".json").write_text(json.dumps(metrics, indent=2) + "\n")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--static", required=True, type=Path)
    parser.add_argument("--zero-mesh", required=True, type=Path)
    parser.add_argument("--moving", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--bins", type=int, default=96)
    args = parser.parse_args()
    metrics = plot_comparison(
        [args.static.resolve(), args.zero_mesh.resolve(), args.moving.resolve()],
        args.output.resolve(),
        args.bins,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
