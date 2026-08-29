#!/usr/bin/env python3
"""Plot the glass48 KH a-posteriori LDA-to-N diagnostic campaign."""
from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import numpy as np

GAMMA = 1.4
TITLE = "glass48 KH; Arpaia ALE; co-moving Roe+split; RK2+F1; mesh f=1"

REJECT = re.compile(
    r"RD-APOSTERIORI-REJECT time=(?P<time>\S+) attempt=(?P<attempt>\d+) "
    r"stage=(?P<stage>\S+) bad_nodes=(?P<bad>\d+) hard_bad_nodes=(?P<hard>\d+) "
    r"worst_id=(?P<id>\d+) min_rho=(?P<rho>\S+) min_press=(?P<press>\S+) "
    r"min_rho_ratio=(?P<ratio>\S+) added_elements=(?P<added>\d+) "
    r"masked=(?P<masked>\d+)/(?P<total>\d+)"
)
HALO = re.compile(
    r"RD-APOSTERIORI-HALO time=(?P<time>\S+) attempt=(?P<attempt>\d+) "
    r"added_elements=(?P<added>\d+) masked=(?P<masked>\d+)/(?P<total>\d+)"
)


def load_snapshot(path: Path) -> dict:
    with h5py.File(path) as data:
        gas = data["PartType0"]
        rho = np.asarray(gas["Density"])
        pressure = np.asarray(gas["Pressure"]) if "Pressure" in gas else (
            (GAMMA - 1.0) * rho * np.asarray(gas["InternalEnergy"])
        )
        return {
            "time": float(np.atleast_1d(data["Header"].attrs["Time"])[0]),
            "position": np.asarray(gas["Coordinates"]),
            "rho": rho,
            "pressure": pressure,
        }


def load_series(output: Path) -> list[dict]:
    return [load_snapshot(Path(path)) for path in sorted(glob.glob(str(output / "snap_*.hdf5")))]


def nearest(series: list[dict], time: float) -> dict:
    return min(series, key=lambda item: abs(item["time"] - time))


def fallback_events(path: Path) -> tuple[list[dict], list[dict]]:
    rejects, halos = [], []
    for line in path.read_text(errors="replace").splitlines():
        match = REJECT.search(line)
        if match:
            row = match.groupdict()
            rejects.append({
                "time": float(row["time"]),
                "attempt": int(row["attempt"]),
                "stage": row["stage"],
                "bad_nodes": int(row["bad"]),
                "hard_bad_nodes": int(row["hard"]),
                "worst_id": int(row["id"]),
                "min_rho": float(row["rho"]),
                "min_press": float(row["press"]),
                "min_rho_ratio": float(row["ratio"]),
                "added": int(row["added"]),
                "masked": int(row["masked"]),
                "total": int(row["total"]),
            })
            continue
        match = HALO.search(line)
        if match:
            row = match.groupdict()
            halos.append({
                "time": float(row["time"]),
                "attempt": int(row["attempt"]),
                "added": int(row["added"]),
                "masked": int(row["masked"]),
                "total": int(row["total"]),
            })
    return rejects, halos


def density_panels(cases: list[tuple[str, list[dict]]], output: Path) -> None:
    targets = (0.4, 0.8, 1.0)
    fig, axes = plt.subplots(
        len(cases), len(targets), figsize=(9.0, 7.7), squeeze=False, constrained_layout=True
    )
    image = None
    for row, (label, series) in enumerate(cases):
        for col, target in enumerate(targets):
            snap = nearest(series, target)
            image = axes[row, col].scatter(
                snap["position"][:, 0], snap["position"][:, 1], c=snap["rho"],
                s=5, linewidths=0, cmap="viridis", vmin=0.5, vmax=2.1
            )
            axes[row, col].set(
                aspect="equal", xlim=(0, 1), ylim=(0, 1),
                title=f"t={snap['time']:.2f}"
            )
            if col == 0:
                axes[row, col].set_ylabel(label)
            else:
                axes[row, col].set_yticklabels([])
            if row != len(cases) - 1:
                axes[row, col].set_xticklabels([])
    fig.colorbar(image, ax=axes.ravel().tolist(), label=r"$\rho$", shrink=0.84)
    fig.suptitle(TITLE + "\nDensity comparison before the moving-LDA failure")
    fig.savefig(output / "kh_aposteriori_density_comparison.png", dpi=190)
    plt.close(fig)


def extrema_plot(cases: list[tuple[str, list[dict]]], rejects: list[dict], output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0), constrained_layout=True)
    for label, series in cases:
        time = [snap["time"] for snap in series]
        axes[0].plot(time, [snap["rho"].min() for snap in series], marker="o", ms=3, label=label)
        axes[1].plot(time, [snap["pressure"].min() for snap in series], marker="o", ms=3, label=label)
    if rejects:
        failure_time = max(row["time"] for row in rejects)
        final = [row for row in rejects if row["time"] == failure_time][-1]
        axes[0].scatter([failure_time], [final["min_rho"]], marker="x", s=70, color="crimson", zorder=5)
        for axis in axes:
            axis.axvline(failure_time, color="crimson", ls="--", lw=1, alpha=0.7)
    axes[0].set(xlabel="time", ylabel=r"$\min(\rho)$", title="Density floor")
    axes[1].set(xlabel="time", ylabel=r"$\min(p)$", title="Pressure floor")
    for axis in axes:
        axis.grid(alpha=0.25)
        axis.legend(fontsize=8)
    fig.suptitle(TITLE)
    fig.savefig(output / "kh_aposteriori_minima_history.png", dpi=190)
    plt.close(fig)


def mask_plot(rejects: list[dict], halos: list[dict], output: Path) -> None:
    if not rejects:
        return
    failure_time = max(row["time"] for row in rejects)
    rows = [row for row in rejects if row["time"] == failure_time]
    halo_rows = [row for row in halos if row["time"] == failure_time]
    mask_after = {row["attempt"]: 100.0 * row["masked"] / row["total"] for row in halo_rows}
    attempts = [row["attempt"] for row in rows]
    masked = [mask_after.get(row["attempt"], 100.0 * row["masked"] / row["total"]) for row in rows]
    rho = [row["min_rho"] for row in rows]

    fig, axis = plt.subplots(figsize=(7.0, 4.2), constrained_layout=True)
    other = axis.twinx()
    axis.plot(attempts, masked, marker="o", color="tab:blue", label="N-patch after expansion")
    other.plot(attempts, rho, marker="s", color="crimson", label=r"trial $\min(\rho)$")
    axis.set(xlabel="retry attempt", ylabel="N-masked triangles [%]", title=f"Failure trial at t={failure_time:.6f}")
    other.set_ylabel(r"trial $\min(\rho)$")
    axis.grid(alpha=0.25)
    lines = axis.lines + other.lines
    axis.legend(lines, [line.get_label() for line in lines], loc="center right")
    fig.suptitle(TITLE)
    fig.savefig(output / "kh_aposteriori_halo_growth.png", dpi=190)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fallback-output", type=Path, required=True)
    parser.add_argument("--fallback-log", type=Path, required=True)
    parser.add_argument("--global-n-output", type=Path, required=True)
    parser.add_argument("--static-lda-output", type=Path, required=True)
    parser.add_argument("--figure-dir", type=Path, required=True)
    args = parser.parse_args()
    args.figure_dir.mkdir(parents=True, exist_ok=True)

    cases = [
        ("static LDA", load_series(args.static_lda_output)),
        ("moving global N", load_series(args.global_n_output)),
        ("moving LDA -> local N", load_series(args.fallback_output)),
    ]
    rejects, halos = fallback_events(args.fallback_log)
    density_panels(cases, args.figure_dir)
    extrema_plot(cases, rejects, args.figure_dir)
    mask_plot(rejects, halos, args.figure_dir)

    summary = {
        "title": TITLE,
        "cases": {label: {"snapshots": len(series), "last_time": series[-1]["time"]} for label, series in cases},
        "reject_events": len(rejects),
        "halo_events": len(halos),
        "failure_time": max((row["time"] for row in rejects), default=None),
        "max_masked_fraction": max((row["masked"] / row["total"] for row in halos), default=0.0),
        "last_reject": rejects[-1] if rejects else None,
    }
    (args.figure_dir / "kh_aposteriori_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
