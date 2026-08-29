#!/usr/bin/env python3
"""Plot matched glass48 moving-mesh KH evolution for B and N schemes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np


SCHEMES = {
    "component": {
        "label": "component-wise B",
        "detail": r"$\theta_{T,k}$ · frozen total residual",
    },
    "scalar": {
        "label": "scalar B",
        "detail": r"$\theta_T=\max_k\theta_{T,k}$ · frozen total residual",
    },
    "n": {
        "label": "N scheme",
        "detail": "lumped temporal mass",
    },
}
COMMON_FORM = (
    r"smoothed KH ($w=0.025$) · glass $48^2$ · moving mesh $f=1$ · "
    r"$P^1(U)$ contour total · "
    r"element-comoving frame $b_T=\bar{\sigma}_T$ · Arpaia equal-step RK2"
)


def load(path: Path) -> dict[str, np.ndarray | float]:
    with h5py.File(path, "r") as handle:
        gas = handle["PartType0"]
        rho = np.asarray(gas["Density"])
        mass = np.asarray(gas["Masses"])
        pressure = (
            np.asarray(gas["Pressure"])
            if "Pressure" in gas
            else 0.4 * rho * np.asarray(gas["InternalEnergy"])
        )
        return {
            "path": str(path),
            "time": float(np.atleast_1d(handle["Header"].attrs["Time"])[0]),
            "position": np.asarray(gas["Coordinates"])[:, :2] % 1.0,
            "velocity": np.asarray(gas["Velocities"]),
            "rho": rho,
            "mass": mass,
            "pressure": pressure,
        }


def load_series(root: Path) -> list[dict[str, np.ndarray | float]]:
    return [load(path) for path in sorted(root.glob("snap_*.hdf5"))]


def nearest(series: list[dict[str, np.ndarray | float]], target: float,
            tolerance: float = 0.025) -> dict[str, np.ndarray | float] | None:
    if not series:
        return None
    candidate = min(series, key=lambda item: abs(float(item["time"]) - target))
    return candidate if abs(float(candidate["time"]) - target) <= tolerance else None


def triangulation(position: np.ndarray) -> mtri.Triangulation:
    tri = mtri.Triangulation(position[:, 0], position[:, 1])
    points = position[tri.triangles]
    tri.set_mask(
        (np.ptp(points[:, :, 0], axis=1) > 0.15)
        | (np.ptp(points[:, :, 1], axis=1) > 0.15)
    )
    return tri


def panel(ax: plt.Axes, data: dict[str, np.ndarray | float] | None,
          target: float, vmin: float, vmax: float, failed: bool = False):
    if data is None:
        ax.set(aspect="equal", xlim=(0, 1), ylim=(0, 1), xticks=[], yticks=[])
        ax.text(
            0.5,
            0.5,
            "FAILED\n" + r"$t=0.873680$" if failed else "snapshot unavailable",
            ha="center",
            va="center",
            color="#a32f2f",
            weight="bold",
            transform=ax.transAxes,
        )
        ax.set_title(fr"requested $t={target:g}$")
        return None
    position = np.asarray(data["position"])
    artist = ax.tripcolor(
        triangulation(position),
        np.asarray(data["rho"]),
        shading="gouraud",
        cmap="viridis",
        vmin=vmin,
        vmax=vmax,
    )
    ax.set(
        aspect="equal",
        xlim=(0, 1),
        ylim=(0, 1),
        xticks=(0, 0.5, 1),
        yticks=(0, 0.5, 1),
        title=fr"$t={float(data['time']):.3f}$",
    )
    return artist


def diagnostics(data: dict[str, np.ndarray | float]) -> dict[str, float | str]:
    mass = np.asarray(data["mass"])
    velocity = np.asarray(data["velocity"])
    rho = np.asarray(data["rho"])
    return {
        "path": str(data["path"]),
        "time": float(data["time"]),
        "rho_min": float(np.min(rho)),
        "rho_max": float(np.max(rho)),
        "pressure_min": float(np.min(data["pressure"])),
        "transverse_kinetic_energy": float(0.5 * np.sum(mass * velocity[:, 1] ** 2)),
        "density_standard_deviation": float(np.std(rho)),
    }


def save(fig: plt.Figure, output: Path, stem: str) -> None:
    fig.savefig(output / f"{stem}.png", dpi=220, bbox_inches="tight")
    fig.savefig(output / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_matched(series: dict[str, list[dict[str, np.ndarray | float]]], output: Path) -> None:
    times = (0.0, 0.2, 0.4, 0.6, 0.8)
    fig, axes = plt.subplots(3, len(times), figsize=(14.2, 8.8), sharex=True, sharey=True)
    artist = None
    for row, key in enumerate(("component", "scalar", "n")):
        for col, target in enumerate(times):
            artist = panel(axes[row, col], nearest(series[key], target), target, 0.85, 2.15) or artist
        axes[row, 0].set_ylabel(
            SCHEMES[key]["label"] + "\n" + SCHEMES[key]["detail"] + "\ny",
            fontsize=9,
        )
    for ax in axes[-1, :]:
        ax.set_xlabel("x")
    colorbar_axis = fig.add_axes((0.925, 0.15, 0.014, 0.69))
    fig.colorbar(artist, cax=colorbar_axis, label=r"density $\rho$")
    fig.suptitle("Matched moving-mesh Kelvin–Helmholtz evolution", fontsize=16, weight="bold")
    fig.text(0.5, 0.025, COMMON_FORM, ha="center", fontsize=8.5)
    fig.subplots_adjust(left=0.105, right=0.90, bottom=0.09, top=0.90, wspace=0.12, hspace=0.25)
    save(fig, output, "kh-b-n-density-matched-t0-t08")


def plot_long(series: dict[str, list[dict[str, np.ndarray | float]]], output: Path) -> None:
    times = (1.0, 2.0, 4.0, 6.0, 8.0, 10.0)
    fig, axes = plt.subplots(3, len(times), figsize=(16.5, 8.8), sharex=True, sharey=True)
    artist = None
    for row, key in enumerate(("component", "scalar", "n")):
        for col, target in enumerate(times):
            data = nearest(series[key], target)
            artist = panel(
                axes[row, col], data, target, 0.85, 2.15,
                failed=(key == "component" and target > 0.87368011),
            ) or artist
        axes[row, 0].set_ylabel(
            SCHEMES[key]["label"] + "\n" + SCHEMES[key]["detail"] + "\ny",
            fontsize=9,
        )
    for ax in axes[-1, :]:
        ax.set_xlabel("x")
    colorbar_axis = fig.add_axes((0.93, 0.15, 0.012, 0.69))
    fig.colorbar(artist, cax=colorbar_axis, label=r"density $\rho$")
    fig.suptitle("Long-time KH solution quality and component-B failure", fontsize=16, weight="bold")
    fig.text(0.5, 0.025, COMMON_FORM, ha="center", fontsize=8.5)
    fig.subplots_adjust(left=0.10, right=0.91, bottom=0.09, top=0.90, wspace=0.10, hspace=0.25)
    save(fig, output, "kh-b-n-density-long-t1-t10")


def plot_metrics(series: dict[str, list[dict[str, np.ndarray | float]]], output: Path) -> list[dict]:
    rows = []
    colors = {"component": "#9b4b6b", "scalar": "#287c71", "n": "#2c64a0"}
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.2))
    for key in ("component", "scalar", "n"):
        values = [diagnostics(data) for data in series[key]]
        for value in values:
            rows.append({"scheme": key, **value})
        time = [float(value["time"]) for value in values]
        axes[0].plot(time, [float(value["rho_min"]) for value in values], "o-", ms=3,
                     color=colors[key], label=SCHEMES[key]["label"])
        axes[1].plot(time, [float(value["transverse_kinetic_energy"]) for value in values], "o-", ms=3,
                     color=colors[key], label=SCHEMES[key]["label"])
        axes[2].plot(time, [float(value["density_standard_deviation"]) for value in values], "o-", ms=3,
                     color=colors[key], label=SCHEMES[key]["label"])
    axes[0].set(xlabel="time", ylabel=r"minimum density $\rho_{\min}$", yscale="log")
    axes[1].set(xlabel="time", ylabel=r"transverse kinetic energy $E_{k,y}$")
    axes[2].set(xlabel="time", ylabel=r"density standard deviation $\sigma_\rho$")
    for ax in axes:
        ax.grid(alpha=0.18)
    axes[0].legend(frameon=False, fontsize=8)
    fig.suptitle("KH robustness and resolved growth diagnostics", fontsize=15, weight="bold")
    fig.text(0.5, 0.02, COMMON_FORM, ha="center", fontsize=8.5)
    fig.tight_layout(rect=(0, 0.06, 1, 0.92))
    save(fig, output, "kh-b-n-diagnostics")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--component", type=Path, required=True)
    parser.add_argument("--scalar", type=Path, required=True)
    parser.add_argument("--n", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    series = {
        "component": load_series(args.component.resolve()),
        "scalar": load_series(args.scalar.resolve()),
        "n": load_series(args.n.resolve()),
    }
    plot_matched(series, output)
    plot_long(series, output)
    rows = plot_metrics(series, output)
    (output / "kh-b-n-diagnostics.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(json.dumps({key: [float(item["time"]) for item in values] for key, values in series.items()}, indent=2))


if __name__ == "__main__":
    main()
