#!/usr/bin/env python3
"""Analyse and plot the Morton et al. (2023) pseudo-1D Sod benchmark."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1] / "shocktube_1d"))
from Riemann import RiemannProblem  # noqa: E402


GAMMA = 5.0 / 3.0
LEFT = np.array([1.0, 0.0, 1.0])
RIGHT = np.array([0.125, 0.0, 0.1])
VARIANTS = {
    "static_LDA1": ("static LDA1 (Morton form)", "#2463a6", "o"),
    "static_N1": ("static N1 (Morton form)", "#db7b2b", "s"),
    "moving_LDA_contour_cm_RK2": ("moving LDA RK2", "#7b4fa3", "^"),
    "moving_N_contour_cm_RK2": ("moving N RK2", "#20866a", "D"),
}
STATIC_FORM = "Published controls: VORONOI_STATIC_MESH · first-order LDA/N · K-matrix residual"
ALE_FORM = (
    "ALE extension: Arpaia modified-midpoint mass · P¹(U) contour total · "
    "element frame b_T = σ̄_T · jitter = 10⁻⁶ h"
)
ALE_SWITCHES = (
    "RD_RK2_TOTAL_RESIDUAL · RD_ALE_EQUALSTEP · RD_ALE_CONTOUR_RESIDUAL · "
    "RD_ELEMENT_COMOVING_FRAME · RD_ALE_CFL_TIMESTEP"
)


def load(path: Path) -> dict[str, np.ndarray | float]:
    with h5py.File(path, "r") as data:
        gas = data["PartType0"]
        result = {
            "time": float(np.atleast_1d(data["Header"].attrs["Time"])[0]),
            "x": np.asarray(gas["Coordinates"])[:, 0],
            "velocity": np.asarray(gas["Velocities"]),
            "rho": np.asarray(gas["Density"]),
            "pressure": np.asarray(gas["Pressure"]),
            "mass": np.asarray(gas["Masses"]),
        }
        result["volume"] = (
            np.asarray(gas["Volume"]) if "Volume" in gas else result["mass"] / result["rho"]
        )
    return result


def exact(x: np.ndarray, time: float) -> np.ndarray:
    x = np.asarray(x)
    result = np.empty((len(x), 3), dtype=np.float64)
    low = x < 1.0
    if np.any(low):
        _, state, _ = RiemannProblem(x[low], 0.5, RIGHT, LEFT, GAMMA, time)
        result[low] = state
    if np.any(~low):
        _, state, _ = RiemannProblem(x[~low], 1.5, LEFT, RIGHT, GAMMA, time)
        result[~low] = state
    return result


def binned(data: dict[str, np.ndarray | float], value: np.ndarray, bins: int = 512):
    edges = np.linspace(0.0, 2.0, bins + 1)
    index = np.clip(np.digitize(data["x"], edges) - 1, 0, bins - 1)
    weight = np.asarray(data["volume"])
    total = np.bincount(index, weights=weight, minlength=bins)
    summed = np.bincount(index, weights=weight * value, minlength=bins)
    valid = total > 0.0
    return 0.5 * (edges[:-1] + edges[1:])[valid], (summed / np.maximum(total, 1e-300))[valid]


def metrics(data: dict[str, np.ndarray | float]) -> dict[str, float]:
    analytic = exact(np.asarray(data["x"]), float(data["time"]))
    volume = np.asarray(data["volume"])
    weight = volume / volume.sum()
    numerical = np.column_stack((data["rho"], data["velocity"][:, 0], data["pressure"]))
    error = np.sum(weight[:, None] * np.abs(numerical - analytic), axis=0)
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


def footer(fig: plt.Figure) -> None:
    fig.text(0.5, 0.066, STATIC_FORM, ha="center", fontsize=8.8, weight="semibold")
    fig.text(0.5, 0.042, ALE_FORM, ha="center", fontsize=8.6, weight="semibold")
    fig.text(0.5, 0.019, ALE_SWITCHES, ha="center", fontsize=7.4, color="#4a5568")


def save(fig: plt.Figure, output: Path, stem: str) -> None:
    fig.savefig(output / f"{stem}.png", dpi=220, bbox_inches="tight")
    fig.savefig(output / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = root / "figures"
    output.mkdir(exist_ok=True)
    all_data = {}
    rows = []
    for variant in VARIANTS:
        for resolution in (64, 128):
            path = root / "runs" / variant / f"n{resolution:04d}" / "output" / "snap_001.hdf5"
            data = load(path)
            all_data[variant, resolution] = data
            rows.append({"variant": variant, "resolution": resolution, **metrics(data)})

    with (root / "analysis.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (root / "analysis.json").write_text(json.dumps(rows, indent=2) + "\n")

    x_exact = np.linspace(0.0, 2.0, 4000, endpoint=False)
    exact_state = exact(x_exact, 0.2)
    fields = (("rho", 0, r"density $\rho$"), ("vx", 1, r"velocity $v_x$"),
              ("pressure", 2, r"pressure $p$"))
    fig, axes = plt.subplots(3, 2, figsize=(11.5, 10.0), sharex="col")
    for row_index, (field, column, ylabel) in enumerate(fields):
        ax, residual = axes[row_index]
        ax.plot(x_exact, exact_state[:, column], color="black", lw=2, label="exact")
        for variant, (label, color, marker) in VARIANTS.items():
            data = all_data[variant, 128]
            value = data["velocity"][:, 0] if field == "vx" else data[field]
            x_bin, profile = binned(data, np.asarray(value))
            ax.plot(x_bin, profile, color=color, lw=1.35, label=label)
            exact_bin = exact(x_bin, 0.2)[:, column]
            residual.plot(x_bin, profile - exact_bin, color=color, lw=1.1)
        ax.set_ylabel(ylabel)
        residual.set_ylabel("numerical − exact")
        ax.grid(alpha=0.16)
        residual.grid(alpha=0.16)
    axes[-1, 0].set_xlabel("x")
    axes[-1, 1].set_xlabel("x")
    axes[0, 0].legend(frameon=False, fontsize=8, ncol=2)
    fig.suptitle("Morton et al. (2023) Sod benchmark · n=128 · t=0.2", fontsize=15, weight="bold")
    fig.tight_layout(rect=(0, 0.10, 1, 0.95))
    footer(fig)
    save(fig, output, "morton2023-sod-profiles-n128")

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.7))
    for variant, (label, color, marker) in VARIANTS.items():
        selected = [next(r for r in rows if r["variant"] == variant and r["resolution"] == n)
                    for n in (64, 128)]
        axes[0].loglog((64, 128), [r["density_l1"] for r in selected], marker=marker,
                       color=color, lw=1.8, label=label)
        axes[1].semilogy((64, 128), [max(r["transverse_velocity_rms"], 1e-20) for r in selected],
                         marker=marker, color=color, lw=1.8, label=label)
    axes[0].set(xlabel="vertices in x", ylabel=r"volume-weighted density $L_1$",
                title="Exact-profile error")
    axes[1].set(xlabel="vertices in x", ylabel=r"RMS $v_y$", title="Pseudo-1D symmetry noise")
    for ax in axes:
        ax.set_xticks((64, 128), labels=("64", "128"))
        ax.grid(alpha=0.18, which="both")
    axes[0].legend(frameon=False, fontsize=8)
    fig.suptitle("Morton Sod: published static controls and ALE extension", fontsize=14, weight="bold")
    fig.tight_layout(rect=(0, 0.14, 1, 0.92))
    footer(fig)
    save(fig, output, "morton2023-sod-errors")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
