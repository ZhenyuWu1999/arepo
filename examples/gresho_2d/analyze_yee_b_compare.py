#!/usr/bin/env python3
"""Compare moving-mesh LDA, component-wise B, and scalar-B on Yee.

All arms use the P1(U) contour total, the element co-moving frame, Arpaia
equal-step RK2, the ALE-RD CFL bound, and f=1.  Both B arms use the frozen
complete-residual sensor; they differ only by RD_B_SCALAR_THETA.
"""

import json
import re
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import numpy as np


RESOLUTIONS = (32, 64, 128)
GAMMA = 1.4
BOX = 10.0
SCALAR_ROOT = Path(
    "/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Yee_ScalarB_20260820"
)
COMPONENT_ROOT = Path(
    "/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Yee_Bcomponent_20260820"
)


def yee_density_error(snapshot: Path) -> tuple[float, float]:
    with h5py.File(snapshot, "r") as handle:
        time = float(handle["Header"].attrs["Time"])
        gas = handle["PartType0"]
        coordinates = gas["Coordinates"][:, :2]
        density = gas["Density"][:]
        volume = gas["Volume"][:]
    displacement = coordinates - 5.0
    displacement -= BOX * np.round(displacement / BOX)
    radius_squared = np.sum(displacement * displacement, axis=1)
    temperature = (
        1.0
        - (GAMMA - 1.0)
        * 25.0
        / (8.0 * np.pi**2 * GAMMA)
        * np.exp(1.0 - radius_squared)
    )
    exact_density = temperature ** (1.0 / (GAMMA - 1.0))
    error = np.average(np.abs(density - exact_density), weights=volume)
    return time, float(error)


def final_theta(log_path: Path) -> dict:
    pattern = re.compile(
        r"RD-THETA time=(\S+) kind=(\w+) n=(\d+) "
        r"mean=(\S+) max=(\S+) hist=\[([^\]]*)\]"
    )
    latest = {}
    for line in log_path.read_text(errors="replace").splitlines():
        match = pattern.search(line)
        if match:
            latest[match.group(2)] = {
                "time": float(match.group(1)),
                "n": int(match.group(3)),
                "mean": float(match.group(4)),
                "max": float(match.group(5)),
                "hist": [float(value) for value in match.group(6).split(",")],
            }
    return latest


def measure_arm(root: Path, prefix: str) -> dict:
    measurements = {}
    for resolution in RESOLUTIONS:
        output = root / f"output_{prefix}_n{resolution}"
        time, error = yee_density_error(output / "snap_001.hdf5")
        entry = {"time": time, "L1_density": error}
        logs = sorted(output.glob("arepo-*.log"))
        if logs:
            entry["theta_final"] = final_theta(logs[-1])
        measurements[resolution] = entry
    errors = [measurements[n]["L1_density"] for n in RESOLUTIONS]
    orders = [
        float(np.log(errors[index] / errors[index + 1]) / np.log(2.0))
        for index in range(len(errors) - 1)
    ]
    return {"measurements": measurements, "orders": orders}


def main() -> None:
    result = {
        "metric": "volume-weighted density L1 vs analytic Yee vortex at t=1",
        "common_method": (
            "moving mesh; P1(U) contour total; element co-moving frame; "
            "Arpaia equal-step RK2; ALE-RD CFL; f=1"
        ),
        "arms": {
            "LDA": measure_arm(SCALAR_ROOT, "lda"),
            "component-wise B": measure_arm(COMPONENT_ROOT, "bcomponent"),
            "scalar B": measure_arm(SCALAR_ROOT, "b"),
        },
    }

    COMPONENT_ROOT.mkdir(parents=True, exist_ok=True)
    json_path = COMPONENT_ROOT / "yee_b_comparison.json"
    json_path.write_text(json.dumps(result, indent=2))

    styles = {
        "LDA": dict(color="black", marker="o"),
        "component-wise B": dict(color="#1677ff", marker="s"),
        "scalar B": dict(color="#d4380d", marker="^"),
    }
    figure, axis = plt.subplots(figsize=(7.4, 5.6))
    for name, arm in result["arms"].items():
        errors = [arm["measurements"][n]["L1_density"] for n in RESOLUTIONS]
        p0, p1 = arm["orders"]
        axis.loglog(
            RESOLUTIONS,
            errors,
            linewidth=1.8,
            markersize=7,
            label=f"{name} (p={p0:.2f}, {p1:.2f})",
            **styles[name],
        )
    axis.set_xticks(RESOLUTIONS, labels=[str(n) for n in RESOLUTIONS])
    axis.set_xlabel("Resolution $N$ per dimension")
    axis.set_ylabel(r"Volume-weighted $L_1(\rho)$ at $t=1$")
    axis.grid(True, which="both", alpha=0.25)
    axis.legend(frameon=False)
    axis.set_title("Yee vortex: component-wise B versus scalar B")
    figure.text(
        0.5,
        0.015,
        "Moving mesh; contour P1(U); co-moving frame; Arpaia RK2; "
        "frozen full-residual B; f=1",
        ha="center",
        fontsize=8.5,
    )
    figure.tight_layout(rect=(0, 0.04, 1, 1))
    for suffix in ("png", "pdf"):
        figure.savefig(
            COMPONENT_ROOT / f"yee-component-vs-scalar-B.{suffix}",
            dpi=220,
            bbox_inches="tight",
        )
    plt.close(figure)

    for name, arm in result["arms"].items():
        errors = [arm["measurements"][n]["L1_density"] for n in RESOLUTIONS]
        print(
            f"{name:16s}: "
            + " ".join(f"{value:.8e}" for value in errors)
            + "  p="
            + ", ".join(f"{value:.3f}" for value in arm["orders"])
        )
    print(f"wrote {json_path}")


if __name__ == "__main__":
    main()
