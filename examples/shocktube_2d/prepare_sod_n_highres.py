#!/usr/bin/env python3
"""Prepare one high-resolution moving-N Sod case with the default ALE form.

The default tested here is contour total residual, element co-moving algebra,
Arpaia temporary nodal mass, N distribution, and the two-stage RD RK update.
The input HDF5 file supplies only the normalized glass generators and IDs; the
Morton-style periodic Sod state is reconstructed by ``write_ic``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from prepare_glass_sod_kh import digest, render, write_ic
from prepare_sod_n_factorial import config_text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--glass-source", required=True, type=Path)
    parser.add_argument("--param-template", required=True, type=Path)
    parser.add_argument(
        "--mesh-label",
        default="swift48_tiled_glass96",
        help="provenance label; this script does not infer glass independence",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    source = args.glass_source.resolve()
    template_path = args.param_template.resolve()
    if root.exists() and any(root.iterdir()):
        raise SystemExit(f"refusing to modify non-empty campaign root: {root}")
    if not source.is_file() or not template_path.is_file():
        raise SystemExit("glass source and parameter template must exist")

    inputs = root / "inputs"
    configs = root / "configs"
    run = root / "run"
    output = run / "output"
    for directory in (inputs, configs, output):
        directory.mkdir(parents=True, exist_ok=True)

    ic = inputs / "IC_sod_glass96.hdf5"
    ic_info = write_ic(source, ic, "sod")
    config = configs / "Config_N_contour_comoving_arpaia.sh"
    config.write_text(config_text("contour", "comoving", "arpaia"))

    replacements = {
        "InitCondFile": str(ic.with_suffix("")),
        "OutputDir": str(output) + "/",
        "BoxSize": "2",
        "TimeOfFirstSnapshot": "0",
        "TimeMax": "0.2",
        "TimeBetSnapshot": "0.01",
        "TimeBetStatistics": "0.01",
        "MaxSizeTimestep": "0.02",
        "MinSizeTimestep": "1e-8",
        "CourantFac": "0.4",
    }
    param = run / "param.txt"
    param.write_text(render(template_path.read_text(), replacements))

    manifest = {
        "description": "High-resolution moving-N Sod with the selected default ALE mathematics",
        "scheme": "N + RK2",
        "residual": "contour",
        "frame": "element_comoving",
        "ale_mass": "Arpaia",
        "mesh_label": args.mesh_label,
        "mesh_caveat": (
            "The n=96 generators are a periodic tiling of the relaxed SWIFT glass48; "
            "this is a high-resolution diagnostic, not an independent-glass convergence level."
        ),
        "glass_source": str(source),
        "glass_source_sha256": digest(source),
        "ic": ic_info,
        "config": str(config),
        "config_sha256": digest(config),
        "param": str(param),
        "param_sha256": digest(param),
        "output": str(output),
        "time_max": 0.2,
        "snapshot_interval": 0.01,
    }
    (root / "campaign.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
