#!/usr/bin/env python3
"""LDA wrapper for the shared glass48 Sod shear-floor analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import plot_sod_n_shear_floor as common


common.LABELS = {
    "static": "static LDA-RK2\nK-matrix total",
    "moving": "moving LDA-RK2\ncontour · co-moving · Arpaia · $\\epsilon_s=0$",
    "floor": "moving LDA-RK2\ncontour · co-moving · Arpaia · shear floor $\\epsilon_s=0.45$",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--static", required=True, type=Path)
    parser.add_argument("--moving", required=True, type=Path)
    parser.add_argument("--floor", required=True, type=Path)
    parser.add_argument("--figure-dir", required=True, type=Path)
    parser.add_argument("--bins", type=int, default=96)
    args = parser.parse_args()

    figure_dir = args.figure_dir.resolve()
    figure_dir.mkdir(parents=True, exist_ok=True)
    analysis = common.analyse(
        {
            "static": args.static.resolve(),
            "moving": args.moving.resolve(),
            "floor": args.floor.resolve(),
        }
    )
    (figure_dir.parent / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n")
    common.plot_profiles(
        analysis, figure_dir / "sod-lda-shear-floor-profiles.png", args.bins
    )
    common.plot_evolution(
        analysis, figure_dir / "sod-lda-shear-floor-evolution.png"
    )
    print(
        json.dumps(
            [
                {
                    "variant": case["variant"],
                    **case["endpoint"],
                    **case["geometry"],
                    **case["diagnostics"],
                }
                for case in analysis["cases"]
            ],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
