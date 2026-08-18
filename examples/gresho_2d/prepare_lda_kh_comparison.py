#!/usr/bin/env python3
"""Prepare a matched n=64 KH comparison for static and moving LDA forms."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


VARIANTS = (
    "static_LDA_Roe_RK2",
    "moving_LDA_Roe_comoving_RK2",
    "moving_LDA_contour_comoving_RK2",
)


def render(template: str, replacements: dict[str, str], drop: set[str] | None = None) -> str:
    drop = set() if drop is None else drop
    result = []
    seen = set()
    for line in template.splitlines():
        fields = line.split()
        key = fields[0] if fields and not fields[0].startswith("%") else ""
        if key in drop:
            continue
        if key in replacements:
            line = f"{key:<38}{replacements[key]}"
            seen.add(key)
        result.append(line)
    missing = set(replacements) - seen
    if missing:
        raise RuntimeError(f"parameter template lacks {sorted(missing)}")
    return "\n".join(result) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="new comparison archive directory")
    args = parser.parse_args()
    root = args.root.resolve()
    if root.exists() and any(root.iterdir()):
        raise SystemExit(f"refusing to modify non-empty root: {root}")
    root.mkdir(parents=True, exist_ok=True)

    here = Path(__file__).resolve().parent
    source_ic = here / "IC_khjit64.hdf5"
    template_path = here / "param_F_con_cm_C_kh.txt"
    ic = root / "IC_khjit64.hdf5"
    shutil.copy2(source_ic, ic)
    template = template_path.read_text()
    cases = []
    for variant in VARIANTS:
        case = root / variant
        output = case / "output"
        output.mkdir(parents=True)
        param = case / "param.txt"
        param.write_text(render(template, {
            "InitCondFile": str(ic.with_suffix("")),
            "OutputDir": str(output) + "/",
            "TimeMax": "2.0",
            "TimeBetSnapshot": "0.2",
            "TimeBetStatistics": "0.2",
            "MaxSizeTimestep": "0.02",
            "MinSizeTimestep": "1e-8",
            "CourantFac": "0.3",
        }, {"CellShapingSpeed", "CellMaxAngleFactor"} if variant.startswith("static_") else None))
        cases.append({"variant": variant, "param": str(param), "output": str(output)})
    (root / "campaign.json").write_text(json.dumps({
        "problem": "matched n=64 smooth-interface KH robustness comparison",
        "ic": str(ic),
        "ic_source": str(source_ic),
        "rho": "1 + band, band=tanh transition width 0.025",
        "vx": "-0.5 + band",
        "vy": "0.1 sin(4 pi x)",
        "pressure": 2.5,
        "gamma": 1.4,
        "time_max": 2.0,
        "cases": cases,
    }, indent=2) + "\n")
    print(f"prepared {len(cases)} cases under {root}")


if __name__ == "__main__":
    main()
