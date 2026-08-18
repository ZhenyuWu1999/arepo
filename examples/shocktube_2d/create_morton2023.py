#!/usr/bin/env python3
"""Prepare the pseudo-1D Sod benchmark of Morton et al. (2023), Fig. 7.

Published setup: a periodic 2-D box of side 2, gamma=5/3, zero velocity,
(rho,p)_L=(1,1), (rho,p)_R=(0.125,0.1), a row-offset uniform vertex mesh,
N=64 and 128 vertices in x, CFL=0.4, and output at t=0.2. Periodicity
places the left state in the central half and creates two mirror Riemann fans.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np


BOX = 2.0
GAMMA = 5.0 / 3.0
LEFT = (1.0, 0.0, 1.0)
RIGHT = (0.125, 0.0, 0.1)
TIME_MAX = 0.2
COURANT = 0.4
MOVING_JITTER_FRACTION = 1.0e-6
VARIANTS = (
    "static_LDA1",
    "static_N1",
    "moving_LDA_contour_cm_RK2",
    "moving_N_contour_cm_RK2",
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def mesh(resolution: int, jitter_fraction: float = 0.0) -> np.ndarray:
    """Morton's uniform n^2 row-offset vertices, optionally de-degenerated."""
    ix, iy = np.meshgrid(
        np.arange(resolution, dtype=np.float64),
        np.arange(resolution, dtype=np.float64),
        indexing="ij",
    )
    positions = np.zeros((resolution * resolution, 3), dtype=np.float64)
    positions[:, 0] = BOX * ((ix + 0.5 * (iy % 2.0)) / resolution).ravel() % BOX
    positions[:, 1] = BOX * (iy / resolution).ravel()
    if jitter_fraction:
        rng = np.random.default_rng(20230818 + resolution)
        amplitude = jitter_fraction * BOX / resolution
        positions[:, :2] = (positions[:, :2] + rng.uniform(
            -amplitude, amplitude, size=(len(positions), 2)
        )) % BOX
    return positions


def write_ic(path: Path, resolution: int, jitter_fraction: float = 0.0) -> str:
    positions = mesh(resolution, jitter_fraction)
    central = (positions[:, 0] > 0.25 * BOX) & (positions[:, 0] < 0.75 * BOX)
    rho = np.where(central, LEFT[0], RIGHT[0])
    pressure = np.where(central, LEFT[2], RIGHT[2])
    internal_energy = pressure / ((GAMMA - 1.0) * rho)
    number = np.array([len(positions), 0, 0, 0, 0, 0], dtype=np.int32)

    with h5py.File(path, "w") as data:
        header = data.create_group("Header")
        gas = data.create_group("PartType0")
        header.attrs["NumPart_ThisFile"] = number
        header.attrs["NumPart_Total"] = number
        header.attrs["NumPart_Total_HighWord"] = np.zeros(6, dtype=np.int32)
        header.attrs["MassTable"] = np.zeros(6, dtype=np.float64)
        header.attrs["Time"] = 0.0
        header.attrs["Redshift"] = 0.0
        header.attrs["BoxSize"] = BOX
        header.attrs["NumFilesPerSnapshot"] = 1
        header.attrs["Omega0"] = 0.0
        header.attrs["OmegaB"] = 0.0
        header.attrs["OmegaLambda"] = 0.0
        header.attrs["HubbleParam"] = 1.0
        header.attrs["Flag_DoublePrecision"] = 1
        for key in ("Flag_Sfr", "Flag_Cooling", "Flag_StellarAge", "Flag_Metals", "Flag_Feedback"):
            header.attrs[key] = 0
        header.attrs["Morton2023Gamma"] = GAMMA
        header.attrs["Morton2023LeftState"] = LEFT
        header.attrs["Morton2023RightState"] = RIGHT
        header.attrs["Morton2023Resolution"] = resolution
        header.attrs["Morton2023MeshJitterFractionOfDx"] = jitter_fraction
        header.attrs["Morton2023Reference"] = "MNRAS 518, 4401, section 5.1.1 and figure 7"

        gas.create_dataset("ParticleIDs", data=np.arange(1, len(positions) + 1, dtype=np.uint64))
        gas.create_dataset("Coordinates", data=positions)
        gas.create_dataset("Masses", data=rho)
        gas.create_dataset("Velocities", data=np.zeros_like(positions))
        gas.create_dataset("InternalEnergy", data=internal_energy)
    return digest(path)


def render_param(
    template: str, replacements: dict[str, str], drop: set[str] | None = None
) -> str:
    drop = set() if drop is None else drop
    lines = []
    seen = set()
    for line in template.splitlines():
        fields = line.split()
        key = fields[0] if fields and not fields[0].startswith("%") else ""
        if key in drop:
            continue
        if key in replacements:
            line = f"{key:<38}{replacements[key]}"
            seen.add(key)
        lines.append(line)
    missing = set(replacements) - seen
    if missing:
        raise RuntimeError(f"parameter template lacks {sorted(missing)}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="new campaign archive directory")
    parser.add_argument("--resolutions", type=int, nargs="+", default=(64, 128))
    args = parser.parse_args()
    root = args.root.resolve()
    if root.exists() and any(root.iterdir()):
        raise SystemExit(f"refusing to modify non-empty campaign root: {root}")
    root.mkdir(parents=True, exist_ok=True)

    template_path = Path(__file__).parents[1] / "gresho_2d" / "param_F_con_cm_C_sod.txt"
    template = template_path.read_text()
    manifest = {
        "problem": "Morton et al. (2023) pseudo-1D Sod shock tube",
        "reference": "https://doi.org/10.1093/mnras/stac3427, section 5.1.1, figure 7",
        "box_size": BOX,
        "gamma": GAMMA,
        "left_state_rho_v_p": LEFT,
        "right_state_rho_v_p": RIGHT,
        "time_max": TIME_MAX,
        "courant": COURANT,
        "mesh": "n by n row-offset uniform vertices",
        "moving_mesh_jitter_fraction_of_dx": MOVING_JITTER_FRACTION,
        "parameter_template": str(template_path.resolve()),
        "cases": [],
    }

    for resolution in args.resolutions:
        input_dir = root / "inputs" / f"n{resolution:04d}"
        input_dir.mkdir(parents=True)
        regular_ic = input_dir / "IC_regular.hdf5"
        moving_ic = input_dir / "IC_moving_jitter1e-6.hdf5"
        regular_sha = write_ic(regular_ic, resolution)
        moving_sha = write_ic(moving_ic, resolution, MOVING_JITTER_FRACTION)
        for variant in VARIANTS:
            moving = variant.startswith("moving_")
            ic = moving_ic if moving else regular_ic
            ic_sha = moving_sha if moving else regular_sha
            case = root / "runs" / variant / f"n{resolution:04d}"
            output = case / "output"
            output.mkdir(parents=True)
            replacements = {
                "InitCondFile": str(ic.with_suffix("")),
                "OutputDir": str(output) + "/",
                "BoxSize": f"{BOX:.17g}",
                "TimeMax": f"{TIME_MAX:.17g}",
                "TimeBetSnapshot": f"{TIME_MAX:.17g}",
                "TimeBetStatistics": f"{TIME_MAX:.17g}",
                "MaxSizeTimestep": "0.02",
                "MinSizeTimestep": "1e-8",
                "CourantFac": f"{COURANT:.17g}",
            }
            param = case / "param.txt"
            drop = {"CellShapingSpeed", "CellMaxAngleFactor"} if variant.startswith("static_") else None
            param.write_text(render_param(template, replacements, drop))
            manifest["cases"].append({
                "variant": variant,
                "resolution": resolution,
                "cells": resolution * resolution,
                "ic": str(ic),
                "ic_sha256": ic_sha,
                "param": str(param),
                "output": str(output),
            })
    (root / "campaign.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"prepared {len(manifest['cases'])} cases under {root}")


if __name__ == "__main__":
    main()
