#!/usr/bin/env python3
"""Final matched Sod comparison: control, shear floor, and entropy floor."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from plot_glass_sod_kh import LEFT, RIGHT, SOD_GAMMA, load, sod_exact
from plot_sod_n_factorial import extended_metrics, snapshot_at
from plot_sod_n_mesh_motion import binned_volume_statistics

sys.path.insert(0, str(Path(__file__).parents[1] / "shocktube_1d"))
from Riemann import RiemannProblem  # noqa: E402


VARIANTS = ("control", "shear", "entropy")
LABELS = {
    "control": "default moving",
    "shear": r"shear floor $\epsilon_s=0.45$",
    "entropy": r"entropy floor $\epsilon_e=0.27$",
}
COLORS = {"control": "#d97706", "shear": "#20866a", "entropy": "#7b4fa3"}


def volume_quantile(values: np.ndarray, volume: np.ndarray, quantile: float) -> float:
    order = np.argsort(values)
    cumulative = np.cumsum(volume[order]) / np.sum(volume)
    index = min(np.searchsorted(cumulative, quantile), len(order) - 1)
    return float(values[order[index]])


def fan_intervals(time: float) -> tuple[tuple[float, float], tuple[float, float]]:
    _, _, first = RiemannProblem(np.array([0.5]), 0.5, RIGHT, LEFT, SOD_GAMMA, time)
    _, _, second = RiemannProblem(np.array([1.5]), 1.5, LEFT, RIGHT, SOD_GAMMA, time)
    # The x=0.5 problem has a right rarefaction; x=1.5 has a left rarefaction.
    return ((0.5 + first[3], 0.5 + first[4]),
            (1.5 + second[0], 1.5 + second[1]))


def endpoint_metrics(snapshot: Path) -> dict[str, object]:
    result = extended_metrics(snapshot)
    data = load(snapshot, 2.0)
    x = np.asarray(data["position"])[:, 0]
    rho = np.asarray(data["rho"])
    velocity = np.asarray(data["velocity"])
    pressure = np.asarray(data["pressure"])
    volume = np.asarray(data["volume"])
    exact = sod_exact(x, float(data["time"]))
    entropy = np.log(pressure / rho**SOD_GAMMA)
    exact_entropy = np.log(exact[:, 2] / exact[:, 0]**SOD_GAMMA)
    intervals = fan_intervals(float(data["time"]))
    rarefaction = np.zeros(len(x), dtype=bool)
    for lower, upper in intervals:
        rarefaction |= (x >= lower) & (x <= upper)
    weight = volume[rarefaction]
    weight /= weight.sum()
    numerical = np.column_stack((rho, velocity[:, 0], pressure))
    error = np.abs(numerical[rarefaction] - exact[rarefaction])
    vy = np.abs(velocity[:, 1])
    result.update(
        transverse_velocity_p99_volume=volume_quantile(vy, volume, 0.99),
        transverse_velocity_max=float(np.max(vy)),
        entropy_l1_global=float(np.average(np.abs(entropy - exact_entropy), weights=volume)),
        rarefaction={
            "intervals": intervals,
            "density_l1": float(np.sum(weight * error[:, 0])),
            "velocity_l1": float(np.sum(weight * error[:, 1])),
            "pressure_l1": float(np.sum(weight * error[:, 2])),
            "entropy_l1": float(np.sum(weight * np.abs(entropy[rarefaction] - exact_entropy[rarefaction]))),
            "density_max_abs": float(np.max(error[:, 0])),
            "pressure_max_abs": float(np.max(error[:, 2])),
        },
    )
    return result


def diagnostics(output: Path) -> dict[str, object]:
    candidates = sorted(output.glob("arepo-*.log"))
    external = output.parent / "run.log"
    log = candidates[-1] if candidates else external
    text = log.read_text(errors="replace")
    flips = sum(int(match.group(1)) for match in re.finditer(r"replaced_edges=(\d+)/(\d+)", text))
    predictor = [(float(a), float(b)) for a, b in re.findall(
        r"predictor_min_rho=([0-9.eE+-]+) predictor_min_press=([0-9.eE+-]+)", text)]
    pivot = [float(value) for value in re.findall(r"min_pivot_ratio=([0-9.eE+-]+)", text)]
    conservation = [float(value) for value in re.findall(r"cons_defect_rel=([0-9.eE+-]+)", text)]
    lumped = [int(value) for value in re.findall(r"f1_lumped=(\d+)", text)]
    return {
        "log": str(log),
        "completed": "Final time=0.2 reached" in text,
        "flip_total": flips,
        "predictor_min_rho": min((pair[0] for pair in predictor), default=None),
        "predictor_min_pressure": min((pair[1] for pair in predictor), default=None),
        "min_sminus_pivot_ratio": min(pivot, default=None),
        "max_conservation_defect_relative": max(conservation, default=None),
        "max_f1_lumped": max(lumped, default=None),
    }


def analyse(paths: dict[str, dict[str, Path]]) -> dict[str, object]:
    result: dict[str, object] = {"schemes": {}}
    for scheme, variants in paths.items():
        entries = {}
        for variant, output in variants.items():
            snapshot = snapshot_at(output, 0.2)
            entries[variant] = {
                "output": str(output),
                "snapshot": str(snapshot),
                "endpoint": endpoint_metrics(snapshot),
                "diagnostics": diagnostics(output),
            }
        control = entries["control"]["endpoint"]
        for variant, entry in entries.items():
            endpoint = entry["endpoint"]
            endpoint["relative_to_control_percent"] = {
                key: 100.0 * (endpoint[key] / control[key] - 1.0)
                for key in ("density_l1", "velocity_l1", "pressure_l1",
                            "transverse_velocity_rms", "entropy_l1_global")
            }
            endpoint["rarefaction"]["relative_to_control_percent"] = {
                key: 100.0 * (endpoint["rarefaction"][key]
                              / control["rarefaction"][key] - 1.0)
                for key in ("density_l1", "velocity_l1", "pressure_l1", "entropy_l1")
            }
        result["schemes"][scheme] = entries
    return result


def plot_full_profiles(analysis: dict[str, object], output: Path, bins: int) -> None:
    x_exact = np.linspace(0.0, 2.0, 4000, endpoint=False)
    exact = sod_exact(x_exact, 0.2)
    edges = np.linspace(0.0, 2.0, bins + 1)
    intervals = fan_intervals(0.2)
    quantities = (("rho", r"density $\rho$", exact[:, 0]),
                  ("pressure", r"pressure $p$", exact[:, 2]),
                  ("vy", r"transverse velocity $v_y$", np.zeros_like(x_exact)))
    fig, axes = plt.subplots(2, 3, figsize=(15.0, 7.8), sharex=True, sharey="col")
    for row, scheme in enumerate(("N", "LDA")):
        for column, (key, ylabel, reference) in enumerate(quantities):
            axis = axes[row, column]
            axis.plot(x_exact, reference, color="black", lw=1.3, label="exact")
            for lower, upper in intervals:
                axis.axvspan(lower, upper, color="#d8b365", alpha=0.10, linewidth=0)
            for variant in VARIANTS:
                entry = analysis["schemes"][scheme][variant]
                data = load(Path(entry["snapshot"]), 2.0)
                x = np.asarray(data["position"])[:, 0]
                volume = np.asarray(data["volume"])
                values = {"rho": np.asarray(data["rho"]),
                          "pressure": np.asarray(data["pressure"]),
                          "vy": np.asarray(data["velocity"])[:, 1]}
                centre, mean, std = binned_volume_statistics(x, values[key], volume, edges)
                axis.plot(centre, mean, color=COLORS[variant], lw=1.45,
                          label=LABELS[variant])
                axis.fill_between(centre, mean - std, mean + std,
                                  color=COLORS[variant], alpha=0.075, linewidth=0)
            axis.grid(alpha=0.15)
            axis.set_xlabel("x")
            if column == 0:
                axis.set_ylabel(f"{scheme}: {ylabel}")
            if row == 0:
                axis.set_title(ylabel)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
    fig.suptitle("glass48 moving-mesh Sod at $t=0.2$: linearly-degenerate mode floors")
    fig.tight_layout(rect=(0, 0.07, 1, 0.96))
    fig.savefig(output, dpi=220)
    plt.close(fig)


def fan_phase(data: dict[str, np.ndarray | float]) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(data["position"])[:, 0]
    intervals = fan_intervals(float(data["time"]))
    first = (x >= intervals[0][0]) & (x <= intervals[0][1])
    second = (x >= intervals[1][0]) & (x <= intervals[1][1])
    selected = first | second
    phase = np.empty(np.sum(selected))
    phase[:np.sum(first)] = (x[first] - intervals[0][0]) / (intervals[0][1] - intervals[0][0])
    phase[np.sum(first):] = (intervals[1][1] - x[second]) / (intervals[1][1] - intervals[1][0])
    indices = np.concatenate((np.where(first)[0], np.where(second)[0]))
    return phase, indices


def plot_rarefaction(analysis: dict[str, object], output: Path, bins: int) -> None:
    phase_edges = np.linspace(0.0, 1.0, bins + 1)
    phase_exact = np.linspace(0.0, 1.0, 600)
    interval = fan_intervals(0.2)[0]
    x_exact = interval[0] + phase_exact * (interval[1] - interval[0])
    exact = sod_exact(x_exact, 0.2)
    exact_entropy = np.log(exact[:, 2] / exact[:, 0]**SOD_GAMMA)
    quantities = (("rho", r"density $\rho$", exact[:, 0]),
                  ("pressure", r"pressure $p$", exact[:, 2]),
                  ("entropy_error", r"$|\Delta\ln(p/\rho^\gamma)|$",
                   np.zeros_like(exact_entropy)))
    fig, axes = plt.subplots(2, 3, figsize=(14.5, 7.6), sharex=True, sharey="col")
    for row, scheme in enumerate(("N", "LDA")):
        for column, (key, ylabel, reference) in enumerate(quantities):
            axis = axes[row, column]
            axis.plot(phase_exact, reference, color="black", lw=1.3, label="exact")
            for variant in VARIANTS:
                entry = analysis["schemes"][scheme][variant]
                data = load(Path(entry["snapshot"]), 2.0)
                phase, indices = fan_phase(data)
                rho = np.asarray(data["rho"])[indices]
                pressure = np.asarray(data["pressure"])[indices]
                volume = np.asarray(data["volume"])[indices]
                if key == "rho":
                    values = rho
                elif key == "pressure":
                    values = pressure
                else:
                    positions = np.asarray(data["position"])[indices, 0]
                    local_exact = sod_exact(positions, 0.2)
                    values = np.abs(np.log(pressure / rho**SOD_GAMMA)
                                    - np.log(local_exact[:, 2] / local_exact[:, 0]**SOD_GAMMA))
                centre, mean, std = binned_volume_statistics(phase, values, volume, phase_edges)
                axis.plot(centre, mean, color=COLORS[variant], lw=1.55,
                          label=LABELS[variant])
                axis.fill_between(centre, np.maximum(0.0, mean - std), mean + std,
                                  color=COLORS[variant], alpha=0.09, linewidth=0)
            axis.grid(alpha=0.15)
            axis.set_xlabel("folded rarefaction coordinate")
            if column == 0:
                axis.set_ylabel(f"{scheme}: {ylabel}")
            if row == 0:
                axis.set_title(ylabel)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
    fig.suptitle("Sod rarefaction fans: control, shear floor, and entropy floor")
    fig.tight_layout(rect=(0, 0.07, 1, 0.96))
    fig.savefig(output, dpi=220)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    for scheme in ("n", "lda"):
        for variant in VARIANTS:
            parser.add_argument(f"--{scheme}-{variant}", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--bins", type=int, default=96)
    args = parser.parse_args()
    paths = {
        "N": {variant: getattr(args, f"n_{variant}").resolve() for variant in VARIANTS},
        "LDA": {variant: getattr(args, f"lda_{variant}").resolve() for variant in VARIANTS},
    }
    root = args.output_root.resolve()
    figures = root / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    analysis = analyse(paths)
    (root / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n")
    plot_full_profiles(analysis, figures / "sod-entropy-floor-full-profiles.png", args.bins)
    plot_rarefaction(analysis, figures / "sod-entropy-floor-rarefaction.png", 48)
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
