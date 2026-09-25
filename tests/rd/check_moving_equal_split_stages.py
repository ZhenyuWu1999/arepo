#!/usr/bin/env python3
"""Frozen equal-ALE begin/end controls: one mesh rebuild and two sweeps per step.

The retained `_split` case/flag names now mean common main-loop hooks; moving
predictor and corrector both run in the end hook. Old preview drivers remain
in the immutable v1-v4 archives.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

import numpy as np

from check_equal_split_stages import build, run, rewrite, sha, state, write_json

REPO = Path(__file__).resolve().parents[2]
OLD = REPO.parent / "local_runs/lda_moving_baseline_glass_20260911"


def prepare(root):
    root.mkdir(exist_ok=False)
    source = root / "source"
    source.mkdir()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    subprocess.run(["git", "archive", "-o", str(root / "base.tar"), commit], cwd=REPO, check=True)
    subprocess.run(["tar", "-xf", str(root / "base.tar"), "-C", str(source)], check=True)
    paths = ["src", "Template-Config.sh", "defines_extra"]
    (root / "source.patch").write_bytes(subprocess.check_output(["git", "diff", "--binary", "HEAD", "--", *paths], cwd=REPO))
    changed = subprocess.check_output(["git", "diff", "--name-only", "HEAD", "--", *paths], cwd=REPO, text=True)
    for name in changed.splitlines():
        shutil.copy2(REPO / name, source / name)
    shutil.copy2(REPO / "Makefile.systype", source / "Makefile.systype")
    for name in ("check_equal_split_stages.py", "check_moving_equal_split_stages.py"):
        shutil.copy2(Path(__file__).with_name(name), root / name)
    subprocess.run(["tar", "-cf", str(root / "source.tar"), "-C", str(source), "."], check=True)
    write_json(root / "source_provenance.json", dict(base_commit=commit, patch_sha256=sha(root / "source.patch"),
               source_tar_sha256=sha(root / "source.tar"),
               environment=dict(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")))
    base = (REPO / "examples/yee_2d/Config_RD_ALE_N_ARPAIA_equalstep_ref.sh").read_text()
    lda = base.replace("N_SCHEME", "LDA_SCHEME") + "\nRD_ALE_CONTOUR_GAUSS=3\n"
    variants = dict(lda=lda, n=base, zero=lda + "\nRD_ALE_TEST_ZERO_MESH_VELOCITY\n",
                    campoli=lda + "\nRD_ALE_CAMPOLI_MASS\n",
                    repair=lda + "\nRD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC\nRD_ALE_EXACT_PATCH_DIAGNOSTIC\n")
    configs = {f"{name}_{kind}": config + ("\nRD_RK2_SPLIT_STAGES\n" if kind == "split" else "")
               for name, config in variants.items() for kind in ("internal", "split")}
    for directory in ("configs", "runs", "inputs"):
        (root / directory).mkdir()
    for name, config in configs.items():
        (root / "configs" / f"{name}.sh").write_text(config)
    for problem in ("yee", "uniform"):
        shutil.copy2(OLD / "inputs" / f"{problem}_glass48.hdf5", root / "inputs" / f"{problem}.hdf5")
    template = (OLD / "runs/probe_moving_glf1/param.txt").read_text()
    cases = []

    def add(name, method, problem="yee", mode="normal", end=.125, **overrides):
        folder = root / "runs" / name
        folder.mkdir()
        ic = root / "inputs" / f"{problem}.hdf5"
        updates = dict(InitCondFile=ic.with_suffix(""), OutputDir=str(folder / "output") + "/",
                       TimeMax=end, TimeBetSnapshot=end / 2, TimeBetStatistics=end / 2,
                       MaxSizeTimestep=1 / 256, **overrides)
        (folder / "param.txt").write_text(rewrite(template, updates))
        cases.append(dict(name=name, method=method, ranks=1, mode=mode, problem=problem, end=end,
                          ic=str(ic), ic_sha256=sha(ic), param_sha256=sha(folder / "param.txt")))

    for method in configs:
        add("yee_" + method, method)
        if method.startswith(("lda_", "n_")):
            add("uniform_" + method, method, "uniform")
    add("restart_lda", "lda_split", mode="restart")
    add("extend_lda", "lda_split", mode="extend")
    add("pending_extend_lda", "lda_split", mode="restart_extend")
    add("long_lda_split", "lda_split", end=.25)
    add("long_lda_internal", "lda_internal", end=.25)
    write_json(root / "campaign.json", dict(methods=list(configs), cases=cases))
    print("Prepared", len(cases), "cases", flush=True)
    add_topology_cases(root)


def add_topology_cases(root):
    """Extend short stage/restart gates to actual changes of connectivity."""
    campaign = json.loads((root / "campaign.json").read_text())
    assert not any(c["name"].startswith("topology_") for c in campaign["cases"])
    shutil.copy2(root / "campaign.json", root / "campaign.short.json")
    for method in ("lda_internal", "lda_split", "campoli_internal", "campoli_split",
                   "repair_internal", "repair_split"):
        name = "topology_" + method
        folder = root / "runs" / name
        folder.mkdir()
        original = next(c for c in campaign["cases"] if c["name"] == "yee_" + method)
        param = rewrite((root / "runs" / original["name"] / "param.txt").read_text(),
                        dict(OutputDir=str(folder / "output") + "/", TimeMax=1,
                             TimeBetSnapshot=.25, TimeBetStatistics=.25))
        (folder / "param.txt").write_text(param)
        campaign["cases"].append(dict(original, name=name, end=1,
                                     param_sha256=sha(folder / "param.txt")))
    write_json(root / "campaign.json", campaign)
    shutil.copy2(__file__, root / "check_moving_equal_split_stages.final.py")
    print("Added six t=1 topology controls", flush=True)


def analyze(root):
    cases = json.loads((root / "campaign.json").read_text())["cases"]
    states, rows, comparisons, failures = {}, [], [], []
    for case in cases:
        folder = root / "runs" / case["name"]
        if not (folder / "run_status.json").exists():
            continue
        status = json.loads((folder / "run_status.json").read_text())
        if not all(r["returncode"] == 0 for r in status):
            rows.append(dict(name=case["name"], failed=True))
            failures.append(case["name"] + ": native run failed")
            continue
        files = sorted((folder / "output").glob("snap_*.hdf5"))
        snapshots = [state(p) for p in files]
        first, last = snapshots[0], snapshots[-1]
        assert min(s["pressure"].min() for s in snapshots) > 0
        assert min(s["u"][:, 0].min() for s in snapshots) > 0
        expected = .25 if case["mode"] in ("extend", "restart_extend") else case["end"]
        assert abs(last["time"] - expected) < 1e-12
        scale = np.array([first["total"][0]] * 3 + [first["total"][3]])
        drift = max(float(np.max(abs(s["total"] - first["total"]) / scale)) for s in snapshots)
        logs = "\n".join(p.read_text() for p in sorted(folder.glob("run*.log")))
        assert "RD-ALE-SPLIT" not in logs, "Preview-based stepping must be removed"
        changes = [int(v) > 0 for v in re.findall(r"RD-TOPO-EXACT time=.*? removed=(\d+)", logs)]
        if case["name"].startswith("topology_repair"):
            assert sum(changes) > 0, "Exact-patch controls must exercise changing connectivity"
        step_count = logs.count("RD-ALE-PREP time=")
        meshes = logs.count("VORONOI: create delaunay mesh")
        assert step_count == round(expected * 256)
        assert logs.count("RD-CKSUM stage=0") == step_count
        assert logs.count("RD-CKSUM stage=1") == step_count
        # Two initial setup meshes; a closed checkpoint needs one opening mesh
        # on resume. Neither is a main-loop endpoint rebuild.
        setup_meshes = 2 + (case["mode"] == "extend")
        assert meshes == step_count + setup_meshes, (case["name"], meshes, step_count, setup_meshes)
        if case["method"].endswith("_split"):
            intervals = re.findall(r"RD-STEP [^\n]*hook=begin.*?RD-STEP [^\n]*hook=end[^\n]*", logs, re.S)
            assert len(intervals) == step_count
            for interval in intervals:
                assert interval.count("VORONOI: create delaunay mesh") == 1
                assert interval.count("RD-ALE-PREP time=") == 1
                assert interval.count("RD-CKSUM stage=0") == interval.count("RD-CKSUM stage=1") == 1
        if case["problem"] == "uniform":
            assert np.max(abs(last["u"] - first["u"])) < 1e-10
            assert drift < 1e-11
        rows.append(dict(name=case["name"], time=last["time"], max_conservation=drift,
                         steps=step_count, mesh_builds=meshes, setup_meshes=setup_meshes,
                         topology_change_steps=sum(changes) if changes else None,
                         max_periodic_displacement=float(np.max(abs((last["x"] - first["x"] + 5) % 10 - 5))),
                         min_density=min(float(s["u"][:, 0].min()) for s in snapshots),
                         min_pressure=min(float(s["pressure"].min()) for s in snapshots),
                         max_uniform_error=(float(np.max(abs(last["u"] - first["u"])))
                                            if case["problem"] == "uniform" else None),
                         final_sha256=sha(files[-1]), seconds=sum(s["seconds"] for s in status)))
        states[case["name"]] = last
        if case["method"].endswith("_internal"):
            previous = root.parent / "moving_equal_split_stages_20260914_v4/runs" / case["name"] / "output"
            old = state(sorted(previous.glob("snap_*.hdf5"))[-1])
            assert all(np.array_equal(last[k], old[k]) for k in ("ids", "u", "x", "area", "bins")), case["name"]
    pairs = []
    for name in states:
        if name.endswith("_split") and name[:-6] + "_internal" in states:
            pairs.append((name, name[:-6] + "_internal"))
    pairs += [("restart_lda", "yee_lda_split"), ("extend_lda", "long_lda_split"),
              ("pending_extend_lda", "long_lda_split")]
    for left, right in pairs:
        if left not in states or right not in states:
            continue
        a, b = states[left], states[right]
        assert np.array_equal(a["ids"], b["ids"]) and a["time"] == b["time"]
        du = float(np.max(abs(a["u"] - b["u"])))
        dx = float(np.max(abs(a["x"] - b["x"])))
        scale = max(1., float(np.max(abs(b["u"]))))
        comparisons.append(dict(left=left, right=right, max_du=du, max_dx=dx,
                                max_area_difference=float(np.max(abs(a["area"] - b["area"]))),
                                same_bins=bool(np.array_equal(a["bins"], b["bins"])) ))
        comparisons[-1]["passed"] = du / scale < 1e-10 and dx < 1e-10 and comparisons[-1]["same_bins"]
        if not comparisons[-1]["passed"]:
            failures.append(left + " vs " + right + ": pointwise equivalence failed")
    summary = dict(cases=rows, comparisons=comparisons, failures=failures,
                   completed_cases=len(rows), planned_cases=len(cases))
    write_json(root / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    assert not failures, failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("action", choices=("prepare", "add-topology", "build", "run", "analyze"))
    parser.add_argument("--select", nargs="*")
    args = parser.parse_args()
    if args.action == "prepare": prepare(args.root.resolve())
    elif args.action == "add-topology": add_topology_cases(args.root.resolve())
    elif args.action == "build": build(args.root.resolve(), args.select)
    elif args.action == "run": run(args.root.resolve(), args.select)
    else: analyze(args.root.resolve())
