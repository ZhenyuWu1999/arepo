#!/usr/bin/env python3
"""Prepare low-resolution moving-N Sod mesh-velocity sensor experiments."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from prepare_glass_sod_kh import render
from prepare_sod_n_factorial import config_text


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--ic", required=True, type=Path)
    parser.add_argument("--param-template", required=True, type=Path)
    parser.add_argument("--baseline-output", required=True, type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    source_ic = args.ic.resolve()
    template_path = args.param_template.resolve()
    baseline_output = args.baseline_output.resolve()
    if root.exists() and any(root.iterdir()):
        raise SystemExit(f"refusing to modify non-empty campaign root: {root}")
    if not source_ic.is_file() or not template_path.is_file():
        raise SystemExit("IC and parameter template must both exist")
    if not baseline_output.is_dir():
        raise SystemExit(f"baseline output does not exist: {baseline_output}")

    input_dir = root / "inputs"
    config_dir = root / "configs"
    runs_dir = root / "runs"
    input_dir.mkdir(parents=True)
    config_dir.mkdir()
    runs_dir.mkdir()

    target_ic = input_dir / "IC_sod_glass48.hdf5"
    shutil.copy2(source_ic, target_ic)
    template = template_path.read_text()

    common_config = config_text("contour", "comoving", "arpaia")
    variants = (
        ("shock_a05", ("RD_ALE_SENSOR_MESH_SMOOTHING=0.5",), "compression + pressure defect"),
        (
            "allwaves_a05",
            ("RD_ALE_SENSOR_MESH_SMOOTHING=0.5", "RD_ALE_SENSOR_ALL_WAVES"),
            "shock plus contact/rarefaction-edge reconstruction defects",
        ),
    )

    cases = []
    for variant, flags, sensor in variants:
        config = config_dir / f"Config_N_contour_cm_arpaia_{variant}.sh"
        config.write_text(common_config + "\n".join(flags) + "\n")

        case_dir = runs_dir / variant
        output_dir = case_dir / "output"
        output_dir.mkdir(parents=True)
        param = case_dir / "param.txt"
        param.write_text(
            render(
                template,
                {
                    "InitCondFile": str(target_ic.with_suffix("")),
                    "OutputDir": str(output_dir) + "/",
                    "BoxSize": "2",
                    "TimeOfFirstSnapshot": "0",
                    "TimeMax": "0.2",
                    "TimeBetSnapshot": "0.01",
                    "TimeBetStatistics": "0.01",
                    "MaxSizeTimestep": "0.02",
                    "MinSizeTimestep": "1e-8",
                    "CourantFac": "0.4",
                },
            )
        )
        cases.append(
            {
                "variant": variant,
                "sensor": sensor,
                "alpha": 0.5,
                "config": str(config),
                "config_sha256": digest(config),
                "param": str(param),
                "param_sha256": digest(param),
                "output": str(output_dir),
            }
        )

    manifest = {
        "description": "Moving N-RK2 Sod: sensor-controlled local mesh de-Lagrangianization",
        "date": "2026-08-19",
        "mesh_family": "relaxed periodic SWIFT glass48",
        "cells": 2304,
        "ic": str(target_ic),
        "ic_sha256": digest(target_ic),
        "common_method": "N + contour + element comoving frame + Arpaia mass + RK2",
        "baseline_output": str(baseline_output),
        "correction": "sigma_i = sigma_i^QL + alpha S_i (ubar_i-u_i), before standard mesh regularization",
        "cases": cases,
    }
    (root / "campaign.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"prepared {len(cases)} sensor cases under {root}")


if __name__ == "__main__":
    main()
