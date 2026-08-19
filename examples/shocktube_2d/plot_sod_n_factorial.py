#!/usr/bin/env python3
"""Analyse and plot the moving-N Sod residual x frame x mass campaign."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import numpy as np

from plot_glass_sod_kh import load, sod_exact, sod_metrics
from plot_sod_n_mesh_motion import binned_volume_statistics


COLORS = {"roe_split": "#d97706", "contour": "#2563a6"}
LINESTYLES = {"lab": "--", "comoving": "-"}
MARKERS = {"arpaia": "o", "campoli": "s"}


def snapshot_at(output: Path, requested_time: float) -> Path:
    candidates = sorted(output.glob("snap_*.hdf5"))
    if not candidates:
        raise RuntimeError(f"no snapshots in {output}")
    times = []
    for path in candidates:
        with h5py.File(path, "r") as data:
            times.append(float(np.atleast_1d(data["Header"].attrs["Time"])[0]))
    index = int(np.argmin(np.abs(np.asarray(times) - requested_time)))
    if abs(times[index] - requested_time) > 2.0e-3:
        raise RuntimeError(f"{output}: nearest time to {requested_time} is {times[index]}")
    return candidates[index]


def extended_metrics(path: Path) -> dict[str, float]:
    data = load(path, 2.0)
    velocity = np.asarray(data["velocity"])
    mass = np.asarray(data["mass"])
    volume = np.asarray(data["volume"])
    result = sod_metrics(data)
    result.update(
        raw_transverse_velocity_rms=float(np.sqrt(np.mean(velocity[:, 1] ** 2))),
        mass_transverse_velocity_rms=float(np.sqrt(np.sum(mass * velocity[:, 1] ** 2) / mass.sum())),
        volume_max_over_min=float(volume.max() / volume.min()),
    )
    return result


def id_state(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with h5py.File(path, "r") as data:
        gas = data["PartType0"]
        particle_id = np.asarray(gas["ParticleIDs"])
        rho = np.asarray(gas["Density"])
        velocity = np.asarray(gas["Velocities"])
        pressure = np.asarray(gas["Pressure"])
    order = np.argsort(particle_id)
    return particle_id[order], np.column_stack((rho, velocity[:, 0], velocity[:, 1], pressure))[order]


def state_contrast(first: Path, second: Path) -> dict[str, list[float]]:
    first_id, first_state = id_state(first)
    second_id, second_state = id_state(second)
    if not np.array_equal(first_id, second_id):
        raise RuntimeError("factorial cases no longer have identical ParticleIDs")
    difference = second_state - first_state
    return {
        "rms_rho_vx_vy_p": np.sqrt(np.mean(difference**2, axis=0)).tolist(),
        "max_abs_rho_vx_vy_p": np.max(np.abs(difference), axis=0).tolist(),
    }


def geometry_metrics(output: Path) -> dict[str, float | int | None]:
    logs = sorted(output.glob("arepo-*.log"))
    if not logs:
        return {"flip_total": 0, "first_flip_time": None, "sync_steps": 0}
    current_time = 0.0
    first_flip = None
    flip_total = 0
    sync_steps = 0
    pattern = re.compile(r"replaced_edges=(\d+)/(\d+)")
    for line in logs[-1].read_text(errors="replace").splitlines():
        match = re.search(r"Sync-Point (\d+), Time: ([0-9.eE+-]+)", line)
        if match:
            sync_steps = max(sync_steps, int(match.group(1)))
            current_time = float(match.group(2))
        match = pattern.search(line)
        if match:
            replacements = int(match.group(1))
            flip_total += replacements
            if replacements and first_flip is None:
                first_flip = current_time
    return {"flip_total": flip_total, "first_flip_time": first_flip, "sync_steps": sync_steps}


def case_label(case: dict[str, str]) -> str:
    residual = "Roe+split" if case["residual"] == "roe_split" else "contour"
    frame = "CM" if case["frame"] == "comoving" else "lab"
    mass = "Arpaia" if case["mass"] == "arpaia" else "Campoli"
    return f"{residual} · {frame} · {mass}"


def analyse(root: Path) -> dict[str, object]:
    manifest = json.loads((root / "campaign.json").read_text())
    cases = []
    by_factors = {}
    for original in manifest["cases"]:
        case = dict(original)
        output = Path(case["output"])
        case["label"] = case_label(case)
        case["geometry"] = geometry_metrics(output)
        case["snapshots"] = {}
        for time in (0.02, 0.03, 0.2):
            path = snapshot_at(output, time)
            case["snapshots"][f"{time:g}"] = {"path": str(path), **extended_metrics(path)}
        cases.append(case)
        by_factors[(case["residual"], case["frame"], case["mass"])] = case

    contrasts = []
    for factor, first_value, second_value, other_axes in (
        ("frame", "lab", "comoving", ("residual", "mass")),
        ("mass", "arpaia", "campoli", ("residual", "frame")),
        ("residual", "roe_split", "contour", ("frame", "mass")),
    ):
        values = {axis: sorted({case[axis] for case in cases}) for axis in other_axes}
        for combination in __import__("itertools").product(*(values[axis] for axis in other_axes)):
            selection = dict(zip(other_axes, combination))
            first_key = (
                first_value if factor == "residual" else selection["residual"],
                first_value if factor == "frame" else selection["frame"],
                first_value if factor == "mass" else selection["mass"],
            )
            second_key = (
                second_value if factor == "residual" else selection["residual"],
                second_value if factor == "frame" else selection["frame"],
                second_value if factor == "mass" else selection["mass"],
            )
            item = {"factor": factor, "from": first_value, "to": second_value, **selection, "times": {}}
            for time in (0.02, 0.03, 0.2):
                first = Path(by_factors[first_key]["snapshots"][f"{time:g}"]["path"])
                second = Path(by_factors[second_key]["snapshots"][f"{time:g}"]["path"])
                item["times"][f"{time:g}"] = state_contrast(first, second)
            contrasts.append(item)
    return {"campaign": str(root), "cases": cases, "contrasts": contrasts}


def plot_profiles(analysis: dict[str, object], figure_dir: Path) -> None:
    cases = analysis["cases"]
    order = [
        ("roe_split", "lab", "arpaia"), ("roe_split", "comoving", "arpaia"),
        ("roe_split", "lab", "campoli"), ("roe_split", "comoving", "campoli"),
        ("contour", "lab", "arpaia"), ("contour", "comoving", "arpaia"),
        ("contour", "lab", "campoli"), ("contour", "comoving", "campoli"),
    ]
    lookup = {(c["residual"], c["frame"], c["mass"]): c for c in cases}
    x_exact = np.linspace(0.0, 2.0, 4000, endpoint=False)
    exact = sod_exact(x_exact, 0.2)
    edges = np.linspace(0.0, 2.0, 97)
    fig, axes = plt.subplots(2, 4, figsize=(15.2, 7.2), sharex=True, sharey=True)
    for axis, key in zip(axes.flat, order):
        case = lookup[key]
        snapshot = Path(case["snapshots"]["0.2"]["path"])
        data = load(snapshot, 2.0)
        x = np.asarray(data["position"])[:, 0]
        rho = np.asarray(data["rho"])
        centre, mean, std = binned_volume_statistics(x, rho, np.asarray(data["volume"]), edges)
        color = COLORS[case["residual"]]
        axis.scatter(x, rho, s=2.2, alpha=0.20, color="0.35", linewidths=0, rasterized=True)
        axis.fill_between(centre, mean - std, mean + std, color=color, alpha=0.18, linewidth=0)
        axis.plot(centre, mean, color=color, lw=1.25)
        axis.plot(x_exact, exact[:, 0], color="black", lw=1.0)
        metric = case["snapshots"]["0.2"]
        axis.set_title(case["label"], fontsize=9.5)
        axis.text(0.02, 0.04, rf"$L_1(\rho)={metric['density_l1']:.4f}$; RMS $v_y={metric['transverse_velocity_rms']:.3e}$",
                  transform=axis.transAxes, fontsize=7.7)
        axis.grid(alpha=0.12)
    for axis in axes[:, 0]:
        axis.set_ylabel(r"density $\rho$")
    for axis in axes[-1]:
        axis.set_xlabel("x")
    fig.suptitle("Moving N-RK2 Sod: residual × frame × ALE mass · t=0.2", fontsize=15)
    fig.text(0.5, 0.018, "matched relaxed glass48 · grey: AREPO cells · colour: volume-weighted 96-bin mean ±1σ",
             ha="center", fontsize=8.5)
    fig.tight_layout(rect=(0.02, 0.04, 1, 0.94))
    fig.savefig(figure_dir / "sod-n-factorial-profiles.png", dpi=220, bbox_inches="tight")
    fig.savefig(figure_dir / "sod-n-factorial-profiles.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_time_series(analysis: dict[str, object], root: Path, figure_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.7))
    for case in analysis["cases"]:
        output = Path(case["output"])
        series = []
        for path in sorted(output.glob("snap_*.hdf5")):
            metric = extended_metrics(path)
            series.append((metric["time"], metric["transverse_velocity_rms"], metric["density_l1"]))
        series = np.asarray(series)
        label = case["label"]
        style = dict(color=COLORS[case["residual"]], linestyle=LINESTYLES[case["frame"]],
                     marker=MARKERS[case["mass"]], markersize=3.0, markevery=2, lw=1.15)
        axes[0].plot(series[:, 0], series[:, 1], label=label, **style)
        axes[1].plot(series[:, 0], series[:, 2], label=label, **style)
    axes[0].set(xlabel="time", ylabel=r"volume-weighted RMS $v_y$", title="Transverse noise")
    axes[1].set(xlabel="time", ylabel=r"volume-weighted $L_1(\rho)$", title="Density error")
    for axis in axes:
        axis.grid(alpha=0.14)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, fontsize=7.4)
    fig.suptitle("Moving N-RK2 Sod factor evolution", fontsize=14)
    fig.tight_layout(rect=(0, 0.18, 1, 0.93))
    fig.savefig(figure_dir / "sod-n-factorial-time-series.png", dpi=220, bbox_inches="tight")
    fig.savefig(figure_dir / "sod-n-factorial-time-series.pdf", bbox_inches="tight")
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
    plot_time_series(analysis, root, figure_dir)
    endpoint = [{"variant": case["variant"], **case["snapshots"]["0.2"], **case["geometry"]}
                for case in analysis["cases"]]
    print(json.dumps(endpoint, indent=2))


if __name__ == "__main__":
    main()
