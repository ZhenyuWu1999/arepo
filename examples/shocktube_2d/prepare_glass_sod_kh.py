#!/usr/bin/env python3
"""Prepare matched glass-mesh Sod and KH static/moving RD comparisons.

The input is an already relaxed periodic glass.  Sod and KH use the same
generator IDs and normalized positions in every numerical variant; only the
fluid state, box scaling, and compile-time RD/ALE method differ.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np


SOD_VARIANTS = (
    "static_LDA1",
    "static_N1",
    "static_N_RK2",
    "zero_mesh_N_contour_RK2",
    "moving_N_contour_cm_RK2_noreg",
    "moving_LDA_contour_cm_RK2",
    "moving_N_contour_cm_RK2",
    "moving_B_contour_cm_RK2",
    "moving_Bscalar_contour_cm_RK2",
)
KH_VARIANTS = (
    "static_LDA_RK2",
    "moving_LDA_roe_cm_RK2",
    "moving_LDA_contour_cm_RK2",
    "moving_N_contour_cm_RK2",
    "moving_B_contour_cm_RK2",
    "moving_Bscalar_contour_cm_RK2",
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def normalized_glass(source: Path) -> tuple[np.ndarray, np.ndarray]:
    with h5py.File(source, "r") as data:
        coordinates = np.asarray(data["PartType0/Coordinates"], dtype=np.float64)
        particle_ids = np.asarray(data["PartType0/ParticleIDs"])
        source_box = float(np.atleast_1d(data["Header"].attrs["BoxSize"])[0])
    if coordinates.ndim != 2 or coordinates.shape[1] < 2 or source_box <= 0.0:
        raise ValueError(f"invalid periodic glass: {source}")
    xy = np.mod(coordinates[:, :2] / source_box, 1.0)
    return xy, particle_ids


def write_ic(source: Path, target: Path, problem: str) -> dict[str, object]:
    xy, particle_ids = normalized_glass(source)
    count = len(xy)
    effective_n = int(round(np.sqrt(count)))
    if effective_n * effective_n != count:
        raise ValueError(f"glass particle count {count} is not a square")

    if problem == "sod":
        box = 2.0
        gamma = 5.0 / 3.0
        coordinates = box * xy
        high = (coordinates[:, 0] > 0.25 * box) & (coordinates[:, 0] < 0.75 * box)
        rho = np.where(high, 1.0, 0.125)
        pressure = np.where(high, 1.0, 0.1)
        vx = np.zeros(count)
        vy = np.zeros(count)
    elif problem == "kh":
        box = 1.0
        gamma = 1.4
        coordinates = xy
        width = 0.025
        band = 0.5 * (
            np.tanh((coordinates[:, 1] - 0.25) / width)
            - np.tanh((coordinates[:, 1] - 0.75) / width)
        )
        rho = 1.0 + band
        pressure = np.full(count, 2.5)
        vx = -0.5 + band
        vy = 0.1 * np.sin(4.0 * np.pi * coordinates[:, 0])
    else:
        raise ValueError(problem)

    target.parent.mkdir(parents=True, exist_ok=True)
    number = np.array([count, 0, 0, 0, 0, 0], dtype=np.int32)
    xyz = np.zeros((count, 3), dtype=np.float64)
    xyz[:, :2] = coordinates
    velocity = np.zeros_like(xyz)
    velocity[:, 0] = vx
    velocity[:, 1] = vy
    with h5py.File(target, "w") as data:
        header = data.create_group("Header")
        header.attrs["NumPart_ThisFile"] = number
        header.attrs["NumPart_Total"] = number
        header.attrs["NumPart_Total_HighWord"] = np.zeros(6, dtype=np.int32)
        header.attrs["MassTable"] = np.zeros(6, dtype=np.float64)
        header.attrs["Time"] = 0.0
        header.attrs["Redshift"] = 0.0
        header.attrs["BoxSize"] = box
        header.attrs["NumFilesPerSnapshot"] = 1
        header.attrs["Omega0"] = 0.0
        header.attrs["OmegaB"] = 0.0
        header.attrs["OmegaLambda"] = 0.0
        header.attrs["HubbleParam"] = 1.0
        header.attrs["Flag_DoublePrecision"] = 1
        for key in ("Flag_Sfr", "Flag_Cooling", "Flag_StellarAge", "Flag_Metals", "Flag_Feedback"):
            header.attrs[key] = 0
        header.attrs["GlassSourceSHA256"] = digest(source)
        header.attrs["GlassEffectiveResolution"] = effective_n
        header.attrs["GlassProblem"] = problem
        header.attrs["Gamma"] = gamma
        gas = data.create_group("PartType0")
        gas.create_dataset("ParticleIDs", data=particle_ids)
        gas.create_dataset("Coordinates", data=xyz)
        gas.create_dataset("Masses", data=rho)
        gas.create_dataset("Velocities", data=velocity)
        gas.create_dataset("InternalEnergy", data=pressure / ((gamma - 1.0) * rho))
    return {
        "path": str(target),
        "sha256": digest(target),
        "cells": count,
        "effective_resolution": effective_n,
        "box_size": box,
        "gamma": gamma,
    }


def render(template: str, replacements: dict[str, str], drop: set[str] | None = None) -> str:
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


def prepare_problem(
    root: Path,
    problem: str,
    ic: Path,
    variants: tuple[str, ...],
    template_path: Path,
    requested_time_max: float | None = None,
) -> list[dict[str, str]]:
    template = template_path.read_text()
    box = 2.0 if problem == "sod" else 1.0
    time_max = requested_time_max if requested_time_max is not None else (0.2 if problem == "sod" else 2.0)
    courant = 0.4 if problem == "sod" else 0.3
    cases = []
    for variant in variants:
        case = root / problem / "runs" / variant
        output = case / "output"
        output.mkdir(parents=True)
        param = case / "param.txt"
        replacements = {
            "InitCondFile": str(ic.with_suffix("")),
            "OutputDir": str(output) + "/",
            "BoxSize": f"{box:.17g}",
            "TimeMax": f"{time_max:.17g}",
            "TimeBetSnapshot": "0.2",
            "TimeBetStatistics": "0.2",
            "MaxSizeTimestep": f"{min(0.02, 0.5 * time_max):.17g}",
            "MinSizeTimestep": "1e-8",
            "CourantFac": f"{courant:.17g}",
        }
        if variant.endswith("_noreg"):
            replacements["CellShapingSpeed"] = "0"
        param.write_text(render(template, replacements,
                                {"CellShapingSpeed", "CellMaxAngleFactor"}
                                if variant.startswith("static_") else None))
        cases.append({"variant": variant, "param": str(param), "output": str(output)})
    return cases


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="new glass campaign archive")
    parser.add_argument("--glass-file", type=Path, required=True)
    parser.add_argument("--sod-time", type=float, default=0.2)
    args = parser.parse_args()
    root = args.root.resolve()
    glass = args.glass_file.resolve()
    if root.exists() and any(root.iterdir()):
        raise SystemExit(f"refusing to modify non-empty campaign root: {root}")
    if not glass.is_file():
        raise SystemExit(f"glass file not found: {glass}")
    root.mkdir(parents=True, exist_ok=True)

    here = Path(__file__).resolve().parent
    gresho = here.parent / "gresho_2d"
    sod_ic = root / "inputs" / "IC_sod_glass48.hdf5"
    kh_ic = root / "inputs" / "IC_kh_glass48.hdf5"
    sod_info = write_ic(glass, sod_ic, "sod")
    kh_info = write_ic(glass, kh_ic, "kh")
    sod_cases = prepare_problem(
        root, "sod", sod_ic, SOD_VARIANTS, gresho / "param_F_con_cm_C_sod.txt", args.sod_time
    )
    kh_cases = prepare_problem(
        root, "kh", kh_ic, KH_VARIANTS, gresho / "param_F_con_cm_C_kh.txt"
    )
    manifest = {
        "mesh_family": "relaxed periodic SWIFT glass",
        "glass_source": str(glass),
        "glass_source_sha256": digest(glass),
        "matched_generators_and_ids_across_variants": True,
        "sod": {
            "description": "Morton-2023 fluid states on a glass; not the published regular geometry",
            "ic": sod_info,
            "cases": sod_cases,
        },
        "kh": {
            "description": "smooth-interface KH on the identical normalized glass",
            "ic": kh_info,
            "cases": kh_cases,
        },
    }
    (root / "campaign.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"prepared {len(sod_cases) + len(kh_cases)} matched glass cases under {root}")


if __name__ == "__main__":
    main()
