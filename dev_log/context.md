This directory (/home/zwu/arepo_rd) contains the public version of the state-of-art astrophysics code AREPO. We aim to implement a new hydrodynamics solver based on the Residual Distribution (RD) method to test how it can improve the performance of the existing solver.

## useful links:
/home/zwu/arepo_rd/arepo contains the source code and some documentation

/home/zwu/arepo_rd/Hydro_data_analysis is a soft link pointing to /home/zwu/Hydro_data_analysis, which contains the standard hydro test problems and the output results for data analysis.

/home/zwu/pdf_documents/Thesis_BenMorton_Final.pdf (or https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q=New+residual+distribution+hydrodynamics+solver+for+galaxy+formation+simulations&btnG=) is the thesis of the previous student in our group. His work involves the preliminary tests of the RD solver, while my work focuses on improving the solver and implementing the solver in AREPO.

https://academic.oup.com/mnras/article/518/3/4401/6847219 is the published paper by our group, first author is Ben Morton, and I'm a co-author.

/home/zwu/MyThesis/Zhenyu-PhDThesis is the draft of my thesis in preparation. Chapter 1 introduces the background of the hydro solvers. Chapter 3 is a brief introduction to the mathematics of the RD solver and the hydro tests done by me. Chapter 4 is the implementation of RD in AREPO (still empty now). I mainly use overleaf to modify the thesis and sync it to github. Unless requested, do not modify the local files here.

https://team.inria.fr/cardamom/files/2019/10/deconinck-ricchiuto2017.pdf is a very useful review paper on residual distribution, written by the core mathematicians working in the CFD field.

https://academic.oup.com/mnras/article/469/4/4306/3798772 (2017 Paardekooper) is the first work to test RD in astrophysics code, which inspires our work. The mathematic details in the paper may not be as rigorous as in my thesis though.

/home/zwu/MyThesis/useful_resources/RD_schemes_notes.md contains some useful mathematical derivations related to RD.

/home/zwu/rdsolver/rd is the source code developed by Ben Morton, which is a standalone code apart from AREPO.

/home/zwu/arepo_dev is the development version of AREPO in Springel's group. It is much more powerful than the public version because it includes Grackle cooling and chemistry library and many subgrid physics models.

## current status
The current implementation of RD in AREPO is still experimental. It can produce correct results for some 2D hydro test problems (using static mesh and the public AREPO), but there are some bugs to correct and further steps to take.

1. The derivation of RD usually uses a median dual cell, i.e., 1/3 |T| allocated to each vertex in 2D. While we can use the Delaunay triangulation, this median dual cell is not the same as Voronoi cell. In the code, we still need to test this issue because a more natural choice is that we use the Voronoi diagram in AREPO. However, this may lead to mathematical errors especially for moving mesh. It seems that most previous RD papers are based on median cell. (also see my thesis section 3.2.2. Residual Distribution in 2D and 3D, Note for Chapter 4 marked in red color)

2. The time integration in AREPO is based on Pakmor 2016 paper, using an MUSCL-Hancock scheme (also see Springel 2010). This may be different from the RK2 scheme for RD. We haven't really tested the consistency of the time integration in AREPO-RD.

3. We have only implemented 2D RD in AREPO. The 3D code is still in /home/zwu/rdsolver/rd. Ideally, there should be a unified interface for both 2D and 3D.

4. The MPI parallelization needs to be examined. The current 2D mesh uses a complicated way to distribute the workload of RD calculation, and occasionally some mesh leads to the termination of the simulation.

5. The ultimate goal is to run moving-mesh RD in the development version of AREPO. Previous works have studied the ALE formulation of RD (e.g. 2015 Arpaia et al DOI 10.1007/s10915-014-9910-5, Arpaia & Ricchiuto https://inria.hal.science/hal-01102124). However, how to implement this in the moving-mesh AREPO code self-consistently needs to be studied.

## workflow
I use multiple agents like CodeX, Kimi and Claude Code for coding and research. When requested, it is desirable to use a log file in /home/zwu/arepo_rd to document the the updates.

### development notes live in the repository

`/home/zwu/arepo_rd` is not a git repository; `/home/zwu/arepo_rd/arepo` is.
The development notes therefore live in `arepo/dev_log/` so that they are
version controlled together with the code:

    arepo/dev_log/context.md                        (this file)
    arepo/dev_log/RD_DEVELOPMENT_LOG.md
    arepo/dev_log/regularize_matrix_debug_report.md

The old paths `/home/zwu/arepo_rd/*.md` are symlinks into that directory, so
anything that refers to them keeps working. Edit either path; they are the same
file.

### git commit authorship

Commits produced in a session with an agent should name both the human and the
agent, with the model, for example:

    git -c user.name="Zhenyu Wu and Claude Code (Opus 5)" \
        -c user.email="2756679409@qq.com" commit ...

Do **not** set this as a repository-level `user.name`, or solo commits will be
misattributed too. Pass it per commit. Keep the `Co-Authored-By:` trailer as
well. Commits whose content came from a different agent should carry that
agent's name instead.

for python data analysis, there is an existing environment yt: source ~/.bashrc   tmox2024    conda activate yt

## cluster (Slurm) — read this before building or running

The machine you land on, `cuillin`, is the **login node**. Do not build or run
simulations there. Slurm is available: partition `all` (35 nodes, 24+ cores
each, 10-day limit) and `GPU` (2 nodes).

**MKL exists only on the compute nodes.** `/usr/local/oneapi` is listed in
`MODULEPATH` on the login node but does not exist on disk there, so
`module load mkl/latest` silently fails and the build falls back to the system
LAPACKE. The resulting binary then dies on a compute node with

    error while loading shared libraries: liblapacke.so.3: cannot open shared object file

which is a real failure recorded in
`Hydro_data_analysis/Data_arepo_RD/gresho_2d/LDA_ring48/`. Always check the
`ldd` output for `libmkl_rt` before trusting a binary.

Normal workflow:

    # build on a compute node (prints ldd linkage so a silent fallback is visible)
    sbatch build_case.sbatch --config examples/gresho_2d/Config_RD.sh
    sbatch build_case.sbatch --config <cfg> --exec <path>     # side-by-side binary

    # run
    sbatch --ntasks=N run_case.sbatch --param <param.txt> --binary <binary>

`run_case.sbatch` takes `--param` and `--binary`; `--ntasks` comes from the
`sbatch` command line. `run_case.sh` is the direct (non-Slurm) launcher and
should only be used on an interactive compute node.

For interactive work use `cnode`, or `ssh zwu@fcfs1` (an FCFS node), then
`module load openmpi hdf5-openmpi mkl/latest` before `./build_case.sh`.

### Always verify which Config a binary was actually built with

When a human edits Config.sh and rebuilds one case at a time, this never goes
wrong. When an agent builds several variants and launches a batch of runs, it
does, and the failure is silent — the jobs complete, the numbers look plausible,
and they are all from the wrong binary. Two real instances of this:

1. **Concurrent builds corrupt each other.** Two `build_case.sbatch` jobs
   submitted at the same time share `./build`, `make clean` each other's
   objects, and relink whatever is left. Result: two binaries with identical
   md5. `build_case.sbatch` now takes an `flock` so submissions serialise.

2. **`BUILD_DIR` does not isolate a build.** `src/main/allvars.h:44` has
   `#include "./../../build/arepoconfig.h"` with the path hardcoded, so
   overriding `BUILD_DIR` writes the generated config to the new directory while
   every compilation unit keeps reading the stale `./build/arepoconfig.h`. This
   is worse than the first failure, because it looks like isolation. Do not use
   `BUILD_DIR`; serialise instead.

Cheap checks, worth doing before trusting any batch of results:

    grep _SCHEME build/arepoconfig.h                  # what the last build saw
    md5sum <binaries>                                 # must differ
    nm -S <binary> | grep -w compute_residuals        # size differs per scheme
    grep '^Binary' <outputdir>/slurm-*.log            # what each run actually ran

A scheme comparison in which two schemes agree to more than a few digits is
almost certainly a build accident, not a physics result.


