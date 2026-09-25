#!/usr/bin/env python3
"""Roundoff-sensitivity diagnostic; does not relax the split equivalence gate."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil

import h5py
import numpy as np

from check_equal_split_stages import run, rewrite, sha, state, write_json


def prepare(parent):
    root = parent / "sensitivity"
    root.mkdir()
    (root / "inputs").mkdir()
    (root / "runs").mkdir()
    (root / "artifacts").symlink_to(parent / "artifacts", target_is_directory=True)
    shutil.copy2(__file__, root / Path(__file__).name)
    helper = parent.parent / "sod_contour_gauss3_20260912/source_helpers/yee_boost_common.py"
    shutil.copy2(helper, root / "yee_boost_common.py")
    cases = []
    for ulps in (1, 8):
        name = f"ulp{ulps}_internal"
        ic = root / "inputs" / (name + ".hdf5")
        shutil.copy2(parent / "inputs/yee.hdf5", ic)
        with h5py.File(ic, "r+") as f:
            old = f["PartType0/Coordinates"][:]
            new = old.copy()
            for _ in range(ulps):
                new[:, :2] = np.nextafter(new[:, :2], np.inf)
            f["PartType0/Coordinates"][:] = new
        folder = root / "runs" / name
        folder.mkdir()
        template = (parent / "runs/topology_lda_internal/param.txt").read_text()
        (folder / "param.txt").write_text(rewrite(template,
            dict(InitCondFile=ic.with_suffix(""), OutputDir=str(folder / "output") + "/")))
        cases.append(dict(name=name, method="lda_internal", ranks=1, mode="normal",
                          ic=str(ic), ic_sha256=sha(ic), param_sha256=sha(folder / "param.txt"),
                          initial_coordinate_max_difference=float(np.max(abs(new - old)))))
    write_json(root / "campaign.json", dict(cases=cases, parent=str(parent),
        purpose="Perturb original internal-loop IC coordinates only; no pass threshold or solver change"))


def analyze(parent):
    root = parent / "sensitivity"
    spec = importlib.util.spec_from_file_location("yee_exact", root / "yee_boost_common.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    paths = dict(internal=parent / "runs/topology_lda_internal", split=parent / "runs/topology_lda_split",
                 ulp1=root / "runs/ulp1_internal", ulp8=root / "runs/ulp8_internal")
    records, states = {}, {}
    for name, folder in paths.items():
        states[name] = [state(p) for p in sorted((folder / "output").glob("snap_*.hdf5"))]
        s = states[name][-1]
        assert s["time"] == 1
        exact = helper.analytic_state(s["x"], s["time"], 1)
        rho = s["u"][:, 0]
        velocity = s["u"][:, 1:3] / rho[:, None]
        errors = dict(rho=abs(rho - exact["density"]), p=abs(s["pressure"] - exact["pressure"]),
                      v=np.linalg.norm(velocity - exact["velocity"][:, :2], axis=1))
        records[name] = dict(analytic_L1={k: float(np.average(v, weights=s["area"])) for k, v in errors.items()})
    for name in ("split", "ulp1", "ulp8"):
        records[name]["difference_from_internal"] = [dict(time=a["time"],
            max_U=float(np.max(abs(a["u"] - b["u"]))),
            max_periodic_position=float(np.max(abs((a["x"] - b["x"] + 5) % 10 - 5))))
            for a, b in zip(states[name], states["internal"])]
    write_json(root / "summary.json", records)
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("parent", type=Path)
    p.add_argument("action", choices=("prepare", "run", "analyze"))
    a = p.parse_args()
    if a.action == "prepare": prepare(a.parent.resolve())
    elif a.action == "run": run(a.parent.resolve() / "sensitivity", None)
    else: analyze(a.parent.resolve())
