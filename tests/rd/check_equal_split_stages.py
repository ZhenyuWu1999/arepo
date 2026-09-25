#!/usr/bin/env python3
"""Native regression for splitting static equal RK2 across AREPO's hydro hooks.

Uses the retained September 13 IC archive. Freeze the working source without
committing unrelated changes; each configuration and run has its own directory.
Run with the local numerical Python and OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

import h5py
import numpy as np

REPO = Path(__file__).resolve().parents[2]
ARCHIVE = REPO.parent / "local_runs/static_baseline_review_20260913/native"
ENV = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def rewrite(text, updates):
    for key, value in updates.items():
        text, count = re.subn(r"^" + re.escape(key) + r"\s+.*$", f"{key} {value}", text, flags=re.M)
        assert count == 1, (key, count)
    return text


def prepare(root):
    root.mkdir(exist_ok=False)
    source = root / "source"
    source.mkdir()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    subprocess.run(["git", "archive", "-o", str(root / "base.tar"), commit], cwd=REPO, check=True)
    subprocess.run(["tar", "-xf", str(root / "base.tar"), "-C", str(source)], check=True)
    paths = ["src", "Template-Config.sh", "defines_extra"]
    patch = subprocess.check_output(["git", "diff", "--binary", "HEAD", "--", *paths], cwd=REPO)
    (root / "source.patch").write_bytes(patch)
    changed = subprocess.check_output(["git", "diff", "--name-only", "HEAD", "--", *paths], cwd=REPO, text=True)
    for name in changed.splitlines():
        shutil.copy2(REPO / name, source / name)
    shutil.copy2(REPO / "Makefile.systype", source / "Makefile.systype")
    shutil.copy2(__file__, root / "check_equal_split_stages.py")
    subprocess.run(["tar", "-cf", str(root / "source.tar"), "-C", str(source), "."], check=True)
    write_json(root / "source_provenance.json", dict(base_commit=commit, patch_sha256=sha(root / "source.patch"),
               source_tar_sha256=sha(root / "source.tar"), environment={k: ENV[k] for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")}))
    eq = (REPO / "examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_EQUAL.sh").read_text()
    split = (REPO / "examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_EQUAL_SPLIT.sh").read_text()
    n_eq = re.sub(r"^RD_ALE_CONTOUR.*\n", "", eq, flags=re.M).replace("LDA_SCHEME", "N_SCHEME")
    hier = (REPO / "examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_HIER.sh").read_text()
    configs = dict(internal=eq, split=split,
                   internal_migrate=eq + "\nVORONOI_STATIC_MESH_DO_DOMAIN_DECOMPOSITION\n",
                   split_migrate=split + "\nVORONOI_STATIC_MESH_DO_DOMAIN_DECOMPOSITION\n",
                   n_internal=n_eq, n_split=n_eq + "\nRD_RK2_SPLIT_STAGES\n",
                   hier_equal=hier + "\nFORCE_EQUAL_TIMESTEPS\n",
                   hier_two=hier + "\nRD_HIERARCHICAL_TEST_PATTERN\n")
    (root / "configs").mkdir()
    for name, config in configs.items():
        (root / "configs" / f"{name}.sh").write_text(config)
    (root / "runs").mkdir()
    (root / "inputs").mkdir()
    old = json.loads((ARCHIVE / "campaign.json").read_text())["cases"]
    by_name = {case["name"]: case for case in old}
    cases = []

    def add(name, method, template, ranks=4, mode="normal", **updates):
        original = by_name[template]
        ic = root / "inputs" / Path(original["ic"]).name
        if not ic.exists():
            shutil.copy2(original["ic"], ic)
        folder = root / "runs" / name
        folder.mkdir()
        param = rewrite((ARCHIVE / "runs" / template / "param.txt").read_text(),
                        dict(InitCondFile=ic.with_suffix(""), OutputDir=str(folder / "output") + "/", **updates))
        (folder / "param.txt").write_text(param)
        cases.append(dict(name=name, method=method, ranks=ranks, mode=mode, reference=template,
                          ic=str(ic), ic_sha256=sha(ic), param_sha256=sha(folder / "param.txt")))

    yee = "yee_g3_equal_r4_dt256"
    for ranks in (1, 2, 4):
        add(f"yee_split_r{ranks}", "split", yee, ranks)
    add("yee_internal_r4", "internal", yee)
    add("yee_hier_equal_r4", "hier_equal", yee)
    add("yee_hier_two_r4", "hier_two", "yee_g3_hier_two_r4_dt256")
    for method in ("internal", "split"):
        add("uniform_" + method, method, "uniform_g3_hier_two_r4_dt256")
        add("sod_" + method, method, "sod_g3_hier_natural_r4_dt100")
    for ranks in (1, 4):
        add(f"kh_split_r{ranks}", "split", f"kh_smooth_g3_equal_r{ranks}", ranks)
        add(f"restart_r{ranks}", "split", yee, ranks, "restart")
    for method in ("internal_migrate", "split_migrate", "n_internal", "n_split"):
        add("yee_" + method, method, yee)
    add("restart_migrate", "split_migrate", yee, mode="restart")
    add("restart_remap", "split_migrate", yee, mode="remap")
    add("extended_control", "split", yee, TimeMax=.25, TimeBetSnapshot=.125, TimeBetStatistics=.125)
    add("extended_restart", "split", yee, mode="extend")
    add("pending_extended_restart", "split", yee, mode="restart_extend")
    add("yee_t1_split", "split", "yee_t1_n96_g3_equal_r4")
    write_json(root / "campaign.json", dict(methods=list(configs), cases=cases))
    print("Prepared", len(cases), "cases", flush=True)


def build(root, selected):
    for method in json.loads((root / "campaign.json").read_text())["methods"]:
        if selected and method not in selected:
            continue
        artifact = root / "artifacts" / method
        artifact.mkdir(parents=True, exist_ok=False)
        build_dir = root / "build" / method
        config = root / "configs" / f"{method}.sh"
        command = ["make", f"CONFIG={config}", f"BUILD_DIR={build_dir}", f"EXEC={build_dir}/Arepo", "-j4"]
        print("BUILD", method, flush=True)
        with (artifact / "build.log").open("w") as log:
            result = subprocess.run(command, cwd=root / "source", env=ENV, stdout=log, stderr=subprocess.STDOUT)
        assert result.returncode == 0, artifact / "build.log"
        for path, name in [(build_dir / "Arepo", "Arepo"), (build_dir / "arepoconfig.h", "arepoconfig.h"),
                           (build_dir / "version.c", "version.c"), (config, "Config.sh")]:
            shutil.copy2(path, artifact / name)
        (artifact / "Arepo").chmod(0o555)
        write_json(artifact / "provenance.json", dict(command=command, config_sha256=sha(config),
                   binary_sha256=sha(artifact / "Arepo"), source_sha256=sha(root / "source.tar")))
        (artifact / "linkage.txt").write_text(subprocess.check_output(["otool", "-L", str(artifact / "Arepo")], text=True))
        print("BUILT", method, flush=True)


def run(root, selected):
    for case in json.loads((root / "campaign.json").read_text())["cases"]:
        name = case["name"]
        if selected and name not in selected:
            continue
        folder = root / "runs" / name
        assert not (folder / "run_status.json").exists(), name
        assert sha(case["ic"]) == case["ic_sha256"] and sha(folder / "param.txt") == case["param_sha256"]
        binary = root / "artifacts" / case["method"] / "Arepo"
        assert sha(binary) == json.loads((binary.parent / "provenance.json").read_text())["binary_sha256"]
        command = ["/opt/homebrew/bin/mpiexec", "-n", str(case["ranks"]), str(binary), "param.txt"]
        if case["mode"] in ("restart", "remap", "restart_extend"):
            (folder / "output").mkdir()
            (folder / "output/stop").touch()
        print("RUN", name, flush=True)
        results = []

        def launch(suffix, restart=False):
            start = time.monotonic()
            cmd = command + (["1"] if restart else [])
            with (folder / f"run{suffix}.log").open("w") as log:
                result = subprocess.run(cmd, cwd=folder, env=ENV, stdout=log, stderr=subprocess.STDOUT)
            results.append(dict(command=cmd, returncode=result.returncode, seconds=time.monotonic() - start))
            write_json(folder / "run_status.json", results)
            assert result.returncode == 0, folder / f"run{suffix}.log"

        launch("")
        if case["mode"] in ("restart", "remap", "extend", "restart_extend"):
            shutil.copytree(folder / "output/restartfiles", folder / "checkpoint")
            if case["mode"] in ("remap", "extend", "restart_extend"):
                shutil.copy2(folder / "param.txt", folder / "param.initial.txt")
                updates = (dict(MultipleDomains=4, TopNodeFactor=8) if case["mode"] == "remap" else
                           dict(TimeMax=.25, TimeBetSnapshot=.125, TimeBetStatistics=.125))
                (folder / "param.txt").write_text(rewrite((folder / "param.txt").read_text(),
                    updates))
            launch("_resumed", restart=True)
        print("DONE", name, flush=True)


def state(path):
    with h5py.File(path) as f:
        gas = f["PartType0"]
        order = np.argsort(gas["ParticleIDs"][:])
        rho = gas["Density"][:][order]
        velocity = gas["Velocities"][:][order]
        internal = gas["InternalEnergy"][:][order]
        mass = gas["Masses"][:][order]
        u = np.column_stack((rho, rho[:, None] * velocity[:, :2], rho * (internal + .5 * (velocity**2).sum(axis=1))))
        return dict(ids=gas["ParticleIDs"][:][order], u=u, x=gas["Coordinates"][:][order],
                    bins=gas["TimebinHydro"][:][order], area=mass/rho, pressure=.4*rho*internal,
                    total=((mass/rho)[:, None] * u).sum(axis=0), time=float(f["Header"].attrs["Time"]))


def analyze(root):
    rows, states, comparisons = [], {}, []
    cases = json.loads((root / "campaign.json").read_text())["cases"]
    for case in cases:
        folder = root / "runs" / case["name"]
        if not (folder / "run_status.json").exists():
            continue
        status = json.loads((folder / "run_status.json").read_text())
        assert all(item["returncode"] == 0 for item in status), case["name"]
        files = sorted((folder / "output").glob("snap_*.hdf5"))
        saved = [state(path) for path in files]
        first, last = saved[0], saved[-1]
        scale = np.array([first["total"][0]] * 3 + [first["total"][3]])
        drift = max(float(np.max(abs(s["total"] - first["total"]) / scale)) for s in saved)
        assert drift < 1e-11, (case["name"], drift)
        assert min(s["u"][:, 0].min() for s in saved) > 0 and min(s["pressure"].min() for s in saved) > 0
        assert np.array_equal(first["ids"], last["ids"]) and np.array_equal(first["x"], last["x"])
        if case["name"].startswith("uniform_"):
            assert np.max(abs(last["u"] - first["u"])) < 1e-12
        if case["mode"] == "remap":
            moved = [int(n) for n in re.findall(r"DOMAIN: exchange of (\d+) particles", (folder / "run_resumed.log").read_text())]
            assert moved and moved[0] > 0, "The saved predictor must actually migrate before its corrector."
        expected = .25 if case["mode"] == "extend" else float(re.search(r"^TimeMax\s+(\S+)", (folder / "param.txt").read_text(), re.M)[1])
        assert abs(last["time"] - expected) < 1e-12, (case["name"], last["time"], expected)
        states[case["name"]] = last
        rows.append(dict(name=case["name"], time=last["time"], max_conservation=drift,
                         final_sha256=sha(files[-1]), seconds=sum(s["seconds"] for s in status)))
    pairs = [(f"yee_split_r{rank}", "yee_internal_r4") for rank in (1, 2, 4)]
    pairs += [("yee_hier_equal_r4", "yee_split_r4"), ("uniform_internal", "uniform_split"),
              ("sod_internal", "sod_split"), ("yee_n_internal", "yee_n_split"),
              ("yee_internal_migrate", "yee_split_migrate"), ("yee_split_migrate", "yee_split_r4"),
              ("restart_r1", "yee_split_r1"), ("restart_r4", "yee_split_r4"),
              ("restart_migrate", "yee_split_migrate"), ("restart_remap", "yee_split_migrate"),
              ("extended_restart", "extended_control"), ("pending_extended_restart", "extended_control")]
    for left, right in pairs:
        if left not in states or right not in states:
            continue
        a, b = states[left], states[right]
        assert np.array_equal(a["ids"], b["ids"]) and abs(a["time"] - b["time"]) < 1e-12
        assert np.array_equal(a["bins"], b["bins"]), (left, right, "timebins")
        error = float(np.max(abs(a["u"] - b["u"])))
        comparisons.append(dict(left=left, right=right, max_U_difference=error))
        assert error < 1e-11, comparisons[-1]
    for name in ("kh_split_r1", "kh_split_r4", "yee_t1_split", "yee_internal_r4", "yee_hier_two_r4"):
        if name not in states:
            continue
        case = next(c for c in cases if c["name"] == name)
        ref = state(sorted((ARCHIVE / "runs" / case["reference"] / "output").glob("snap_*.hdf5"))[-1])
        error = float(np.max(abs(states[name]["u"] - ref["u"])))
        comparisons.append(dict(left=name, right="archive/" + case["reference"], max_U_difference=error))
        assert error < 1e-11, comparisons[-1]
    write_json(root / "summary.json", dict(cases=rows, comparisons=comparisons))
    print(json.dumps(dict(completed=len(rows), max_U_difference=max((r["max_U_difference"] for r in comparisons), default=0),
                         max_conservation=max((r["max_conservation"] for r in rows), default=0)), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "build", "run", "analyze"))
    parser.add_argument("root", type=Path)
    parser.add_argument("--only", nargs="+")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action in ("build", "run"):
        globals()[args.action](root, args.only)
    else:
        globals()[args.action](root)
