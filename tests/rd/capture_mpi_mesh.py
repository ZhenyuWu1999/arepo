#!/usr/bin/env python3
"""Freeze, instrument and run a genuine 4-rank glass case for the MPI figure.

Instrumentation modifies only an isolated source copy. The working solver and
thesis are untouched. Use --prepare, --build, then --run as separate steps.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[2]
WORKSPACE = REPO.parent
ENV = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
SOLVER = Path("src/hydro/residual_distribution_solver.c")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def prepare(root):
    root.mkdir(exist_ok=False)
    source = root / "source"
    source.mkdir()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    subprocess.run(["git", "archive", "-o", str(root / "base.tar"), head], cwd=REPO, check=True)
    subprocess.run(["tar", "-xf", str(root / "base.tar"), "-C", str(source)], check=True)
    tracked = ["src", "Template-Config.sh", "defines_extra"]
    patch = subprocess.check_output(["git", "diff", "--binary", "HEAD", "--", *tracked], cwd=REPO)
    (root / "working_source.patch").write_bytes(patch)
    changed = subprocess.check_output(["git", "diff", "--name-only", "HEAD", "--", *tracked], cwd=REPO, text=True)
    for rel in changed.splitlines():
        shutil.copy2(REPO / rel, source / rel)
    shutil.copy2(REPO / "Makefile.systype", source / "Makefile.systype")
    original = (source / SOLVER).read_text()
    (root / "solver_before_capture.c").write_text(original)
    edits = [
        ("#ifdef RD_HIERARCHICAL_TIMESTEPS\nvoid compute_residuals", '#include "mpi_mesh_capture.h"\n\n#ifdef RD_HIERARCHICAL_TIMESTEPS\nvoid compute_residuals'),
        ("  rd_build_element_set(T, &set, 1);", "  rd_build_element_set(T, &set, 1);\n  rd_capture_begin(T, &set);"),
        ("      /*use residuals to update fluid state of local points or export to other tasks*/", "      rd_capture_element(T, thistask_triangles[i], i, rd_stage, triangle_dt, Flux_RD);\n\n      /*use residuals to update fluid state of local points or export to other tasks*/"),
        ("  apply_FluxRD_list();", "  rd_capture_exports();\n  apply_FluxRD_list();"),
        ("  /* apply the fluxes */", "  rd_capture_imports(FluxListGet);\n\n  /* apply the fluxes */"),
    ]
    edited = original
    for old, new in edits:
        assert edited.count(old) == 1, old
        edited = edited.replace(old, new)
    (source / SOLVER).write_text(edited)
    shutil.copy2(Path(__file__).with_name("mpi_mesh_capture.h"), source / "src/hydro/mpi_mesh_capture.h")
    shutil.copy2(__file__, root / Path(__file__).name)
    shutil.copy2(REPO / "examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_EQUAL_SPLIT.sh", root / "Config.sh")
    inputs = root / "inputs"
    inputs.mkdir()
    glass = WORKSPACE / "local_runs/lda_baseline_glass_20260911/inputs/glassPlane_48.hdf5"
    ic = WORKSPACE / "local_runs/static_baseline_review_20260913/inputs/yee_glass48.hdf5"
    assert sha(glass) == "157e1a4767f4678df4cd80d2df9aa248fa520899e12e777a448e17f31e47d88f"
    for src in (glass, ic):
        shutil.copy2(src, inputs / src.name)
    template = (WORKSPACE / "local_runs/static_baseline_review_20260913/native/runs/uniform_g3_hier_two_r4_dt256/param.txt").read_text()
    cases = [("rank4_capture", 4, True), ("rank4_control", 4, False), ("rank1_capture", 1, True)]
    for name, ranks, capture in cases:
        run = root / "runs" / name
        (run / "output/mpi_mesh").mkdir(parents=True)
        params = template
        updates = dict(InitCondFile=inputs / "yee_glass48", OutputDir=str(run / "output") + "/",
                       TimeMax="0.00390625", MaxSizeTimestep="0.001953125", TimeBetSnapshot="0.00390625",
                       TimeBetStatistics="0.00390625", TimeLimitCPU="600")
        for key, value in updates.items():
            params, n = re.subn(r"^" + key + r"\s+.*$", f"{key} {value}", params, flags=re.M)
            assert n == 1, key
        (run / "param.txt").write_text(params)
        save(run / "case.json", dict(ranks=ranks, capture=capture, param_sha256=sha(run / "param.txt")))
    subprocess.run(["tar", "-cf", str(root / "source.tar"), "-C", str(source), "."], check=True)
    save(root / "provenance.json", dict(base_commit=head, original_solver_sha256=sha(REPO / SOLVER),
         source_tar_sha256=sha(root / "source.tar"), config_sha256=sha(root / "Config.sh"),
         glass_sha256=sha(glass), ic_sha256=sha(ic), helper_sha256=sha(source / "src/hydro/mpi_mesh_capture.h"),
         environment={k: ENV[k] for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")}))
    print("Prepared", root, flush=True)


def build(root):
    (root / "artifact").mkdir()
    cmd = ["make", f"CONFIG={root / 'Config.sh'}", f"BUILD_DIR={root / 'build'}", f"EXEC={root / 'build/Arepo'}", "-j4"]
    with (root / "artifact/build.log").open("w") as log:
        result = subprocess.run(cmd, cwd=root / "source", env=ENV, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(root / "artifact/build.log")
    for name in ("Arepo", "arepoconfig.h", "version.c"):
        shutil.copy2(root / "build" / name, root / "artifact" / name)
    (root / "artifact/Arepo").chmod(0o555)
    (root / "artifact/linkage.txt").write_text(subprocess.check_output(["otool", "-L", str(root / "artifact/Arepo")], text=True))
    save(root / "artifact/build.json", dict(command=cmd, exit_code=0, binary_sha256=sha(root / "artifact/Arepo")))
    print("Built", root / "artifact/Arepo", flush=True)


def run(root):
    binary = root / "artifact/Arepo"
    assert sha(binary) == json.loads((root / "artifact/build.json").read_text())["binary_sha256"]
    for name in ("rank4_capture", "rank4_control", "rank1_capture"):
        folder = root / "runs" / name
        assert not (folder / "run.json").exists(), folder
        case = json.loads((folder / "case.json").read_text())
        cmd = ["/opt/homebrew/bin/mpiexec", "-n", str(case["ranks"]), str(binary), "param.txt"]
        print("Running", name, flush=True)
        with (folder / "run.log").open("w") as log:
            result = subprocess.run(cmd, cwd=folder, env=dict(ENV, RD_MPI_MESH_DUMP="1" if case["capture"] else "0"),
                                    stdout=log, stderr=subprocess.STDOUT, timeout=600)
        save(folder / "run.json", dict(command=cmd, exit_code=result.returncode))
        assert result.returncode == 0, folder / "run.log"
    print("All runs completed", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("action", choices=("prepare", "build", "run"))
    args = p.parse_args()
    globals()[args.action](args.root.resolve())
