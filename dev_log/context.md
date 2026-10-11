Agent entry point: [AGENTS.md](../AGENTS.md) contains stable working rules and
the reading order. This file retains project background and detailed conventions;
read the latest development-log entries for evolving scientific conclusions.

This directory (/home/zwu/arepo_rd) contains the public version of the state-of-art astrophysics code AREPO. We aim to implement a new hydrodynamics solver based on the Residual Distribution (RD) method to test how it can improve the performance of the existing solver.

## useful links:
/home/zwu/arepo_rd/arepo contains the source code and some documentation

/home/zwu/arepo_rd/Hydro_data_analysis is a soft link pointing to /home/zwu/Hydro_data_analysis, which contains the standard hydro test problems and the output results for data analysis. Its `Analysis/` subdirectories hold the campaign tooling: `yee_boost/` (IC generation, dt ladders, order analysis), `shocktube_2d/` (the periodic 2-D Sod), and `moving_mesh/` (offline ALE feasibility measurements that need no build, no cluster and no solver).

/home/zwu/pdf_documents/Thesis_BenMorton_Final.pdf (or https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q=New+residual+distribution+hydrodynamics+solver+for+galaxy+formation+simulations&btnG=) is the thesis of the previous student in our group. His work involves the preliminary tests of the RD solver, while my work focuses on improving the solver and implementing the solver in AREPO.

https://academic.oup.com/mnras/article/518/3/4401/6847219 is the published paper by our group, first author is Ben Morton, and I'm a co-author.

/home/zwu/MyThesis/Zhenyu-PhDThesis is the draft of my thesis in preparation. Chapter 1 introduces the background of the hydro solvers. Chapter 3 is a brief introduction to the mathematics of the RD solver and the hydro tests done by me. I mainly use Overleaf to modify the thesis and sync it to GitHub.

### thesis editing boundary

- **Do not modify Chapters 1--3 unless I explicitly request a change to those
  chapters.** They are existing thesis material, not a general scratch space for
  the moving-mesh development. Reading and citing their notation is encouraged;
  rewriting, reorganising, or opportunistic cleanup is not.
- **Chapter 4's overall structure is established (user decision, 2026-09-29).**
  Section 4.3.2 may gain further numerical results, such as Sedov blast tests.
  Connectivity changes and moving hierarchical timesteps remain ongoing work
  in Section 4.3.3; the detailed red implementation drafts and alternatives
  are no longer intended for the thesis. Keep those details in development
  notes and history instead of restoring them to the chapter.
- This editorial decision does not validate unfinished numerical methods.
  Distinguish established derivations and presented test results from proposed
  repairs and extensions that still require implementation or validation.
- Do not modify local thesis files or propagate statements between chapters
  without an explicit request covering the affected material.

https://team.inria.fr/cardamom/files/2019/10/deconinck-ricchiuto2017.pdf is a very useful review paper on residual distribution, written by the core mathematicians working in the CFD field.

https://academic.oup.com/mnras/article/469/4/4306/3798772 (2017 Paardekooper) is the first work to test RD in astrophysics code, which inspires our work. The mathematic details in the paper may not be as rigorous as in my thesis though.

/home/zwu/MyThesis/useful_resources/RD_schemes_notes.md contains some useful mathematical derivations related to RD.

/home/zwu/MyThesis/useful_resources/ also holds the two 2015 Arpaia papers on ALE residual distribution:

- `2015_Arpaia_An_ALE_Formulation_for_Explicit_Runge–Kutta_Residual_Distribution.pdf` (J. Sci. Comput., 10.1007/s10915-014-9910-5). This is the reference formulation for the moving-mesh target. It is an explicit two-step Runge-Kutta method, not a space-time discretisation, so the static-mesh RK2-RD is its sigma=0 special case. See `dev_log/RK2_timestep_movingmesh_analysis.md` section 7.
- `2015_Arpaia_Ricchiuto_Mesh_adaptation_by_continuous_deformation_Basics_accuracy_efficiency_well_balancedness.pdf`, on mesh adaptation by continuous deformation.

The full ALE-RD and DGCL bibliography for the moving-mesh phase, with verified
citations and DOIs, is in `dev_log/RD_DEVELOPMENT_LOG_2.md` section 2. Two
gaps recorded there are worth carrying in mind whenever the literature is
invoked as authority:

- every Arpaia-Ricchiuto work is a **continuous-deformation, fixed-connectivity**
  framework, because r-adaptation moves nodes without reconnecting them, whereas
  AREPO's Delaunay triangulation reconnects whenever the generators move. Only
  Isola & Guardone (2022) and Guardone et al. (2011) treat topology change;
- in all of that literature the mesh velocity is an adaptation or shock-fitting
  velocity, explicitly not the fluid velocity. **No ALE-RD paper operates at
  AREPO's design point, sigma approximately u.**

Note that the CFD residual-distribution literature uses a single global timestep throughout. Hierarchical/local time stepping is an astrophysics requirement with no counterpart there, so it has no reference solution to port.

/home/zwu/rdsolver/rd is the source code developed by Ben Morton, which is a standalone code apart from AREPO.

/home/zwu/arepo_dev is the development version of AREPO in Springel's group. It is much more powerful than the public version because it includes Grackle cooling and chemistry library and many subgrid physics models.

## current status

**2026-10-11 addition:** moving 3D preparation has an independent geometry and
Campoli-ledger proof/oracle, documented in
`RD_3D_MOVING_GEOMETRY_MATHEMATICS_20261011.md` (log3 §240). Production remains
unscaled per the user's preference not to make rescaling a prerequisite.
The complete fixed-connectivity periodic model conserves to round-off with
exact mean face vectors; midpoint normals fail the nonuniform control.
Five-component transfer models now include 4-4/larger cavities. Native moving
3D is still unsupported; next is diagnostic-only simplex registry/FV geometry.
Claude's cold-Sedov root-cause/prototype evidence is in log3 §238; it does not
make the current unscaled cold-Sedov benchmark or strong-shock positivity pass.

**2026-10-10 addition:** native **static 3D N/LDA** now supports periodic
gas-only full meshes, equal steps or the experimental frozen-dU hierarchy,
with small double-precision 1/2/4-rank MPI gates. Fifty final 8³/16³ gates
pass, including actual natural mixed bins and equal-bin degeneration. See
`RD_3D_FEATURES_AND_BENCHMARKS_20261010.md`, `examples/rd_3d/README.md` and log3
§§234–237. SWIFT-inspired 16³ Sod/Gresho tests complete; cold Sedov stops at
the solve-compatibility audit and remains unvalidated. Moving 3D, B,
active-only 3D rebuild and open-stage restart remain unsupported. User deferred
the 2D K-refactor trajectory-compatibility fix. Local work is limited to simple
checks; larger convergence/stability/scaling runs belong on COSMA/Cuillin.
The following historical completion statements concern **2D**, not all dimensions.

*(This section was written on 2026-07-27 and revised on 2026-08-05. The
authoritative running record is the development log; this is only an
orientation for a new session.)*

The static-mesh phase is complete. N, LDA and B all run in 2-D on the public
AREPO with the conservative parameter-vector linearisation and the median-dual
control area; LDA converges at order 1.88/1.74 on the advected Yee vortex,
hierarchical timesteps are validated for N and LDA, and conservation is exact
to round-off and invariant under 1/4/16 MPI ranks. **The active phase is now
moving mesh (ALE).** Details, gates and the phase plan are in
`dev_log/RD_DEVELOPMENT_LOG_2.md`.

Of the five items originally listed here:

1. **Still open.** The derivation of RD usually uses a median dual cell, i.e., 1/3 |T| allocated to each vertex in 2D. While we can use the Delaunay triangulation, this median dual cell is not the same as Voronoi cell. In the code, we still need to test this issue because a more natural choice is that we use the Voronoi diagram in AREPO. However, this may lead to mathematical errors especially for moving mesh. It seems that most previous RD papers are based on median cell. (also see my thesis section 3.2.2. Residual Distribution in 2D and 3D, Note for Chapter 4 marked in red color) — the question is sharper on a moving mesh than on a static one and is carried as an open question of the ALE phase.

2. **Resolved.** The time integration is no longer AREPO's MUSCL-Hancock scheme. `RD_RK2_TOTAL_RESIDUAL` implements the Arpaia & Ricchiuto two-step explicit RK with the F1 mass matrix, with both stages inside a single solver call. Production LDA uses standard GL+F1; a rate-consistent Heun variant exists as a thesis discussion topic only. See `dev_log/LDA_F1_Heun_vs_standard_LDA_RK2.md`.

3. **Partly implemented.** Static 3D N/LDA and small hierarchy/MPI gates are now available; moving 3D remains open. The standalone 3D code is in `/Users/zhenyuwu/rdsolver/rd` on this Mac (historical cluster path `/home/zwu/rdsolver/rd`). The earlier exclusion of 3D from the moving-mesh phase was **superseded by the user on 2026-10-10**: include early 3D feasibility/testing now, with a dimension-aware interface. See [3D feasibility](RD_3D_FEASIBILITY_20261010.md), log3 §228. Subsequent static implementation and validation are documented in log3 §§230–237; this does not establish moving tetra support.

4. **Largely resolved.** MPI rank invariance by particle ID is established for the static equal-timestep and hierarchical cases. The remaining risk is that a round-off-sensitive branch could make results depend on the domain decomposition; one such branch is identified in `RD_DEVELOPMENT_LOG_2.md` §3.4.

5. **Now the active phase, not a distant goal.** Three prerequisites once thought outstanding are already satisfied: the main loop is in the required single-call structure, the old vertex configuration is recoverable for free because the drift is exactly linear in `VelVertex`, and B is closed. See `dev_log/RD_DEVELOPMENT_LOG_2.md` §3.

## workflow
I use multiple agents like CodeX, Kimi and Claude Code for coding and research. When requested, it is desirable to use a log file in /home/zwu/arepo_rd to document the the updates.

### development notes live in the repository

`/home/zwu/arepo_rd` is not a git repository; `/home/zwu/arepo_rd/arepo` is.
The development notes therefore live in `arepo/dev_log/` so that they are
version controlled together with the code:

    arepo/dev_log/context.md                        (this file)
    arepo/dev_log/context_localMac.md               (Apple Silicon environment)
    arepo/dev_log/context_cosma.md                  (COSMA environment)
    arepo/dev_log/RD_DEVELOPMENT_LOG_3_localMac.md (CURRENT log: local development)
    arepo/dev_log/RD_DEVELOPMENT_LOG_2.md           (historical moving-mesh record)
    arepo/dev_log/RD_DEVELOPMENT_LOG_4_cosma.md     (COSMA setup and validation)
    arepo/dev_log/RD_DEVELOPMENT_LOG.md             (volume 1, closed 2026-08-05)
    arepo/dev_log/B_scheme_complete_mathematics.md
    arepo/dev_log/LDA_F1_Heun_vs_standard_LDA_RK2.md
    arepo/dev_log/mass_matrix_order_analysis.md
    arepo/dev_log/RD_hierarchical_timestep_conservation_design.md
    arepo/dev_log/RD_hierarchical_timestep_phaseb_prototype.md
    arepo/dev_log/RD_RT_FIXED_BUFFER_REPORT.md
    arepo/dev_log/AREPO_FV_RD_comparison.md
    arepo/dev_log/regularize_matrix_debug_report.md
    arepo/dev_log/RK2_timestep_movingmesh_analysis.md

**Current logging convention, confirmed 2026-09-10:** append current work to
`RD_DEVELOPMENT_LOG_3_localMac.md`; do not append new entries to volume 2.
Start a new local session with `context_localMac.md` and the latest entries in
volume 3. Read `RD_DEVELOPMENT_LOG_2.md` section 1 as needed for the historical
handover from volume 1. Volume 1 is 9000 lines and does not need to be read in full; it is
the archive of the static-mesh phase and is still authoritative for anything
section 1 points into. The companion documents above remain live references for
both volumes.

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

This section describes Cuillin. For the current COSMA module stack, dine2
partition/account settings, batch wrappers and validated smoke test, read
`dev_log/context_cosma.md`.

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

    # build on a compute node; formal baselines should require a clean tree
    sbatch build_case.sbatch \
        --config examples/yee_2d/Config_RD.sh \
        --name yee-lda-lumped \
        --require-clean

    # use the immutable artifact path printed by the completed build
    sbatch --ntasks=N run_case.sbatch \
        --binary build_artifacts/yee-lda-lumped/<artifact-id>/Arepo \
        --param <param.txt>

`build_case.sh` serialises compilation with a repository-wide `flock`, builds
in an isolated temporary `BUILD_DIR`, and publishes an immutable bundle
containing `Arepo`, the exact Config snapshot, generated `arepoconfig.h`,
binary checksum, linkage, build log, and a manifest. Its fingerprint includes
the Git commit, tracked diff, Config contents, `Makefile.systype`, compiler
wrapper and LAPACK backend. Identical inputs reuse the existing bundle.

`run_case.sbatch` requires `--param` and `--binary`; `--ntasks` comes from the
`sbatch` command line. It delegates to `run_case.sh`, which verifies the binary
checksum and copies the matching build provenance into a timestamped directory
under the simulation output. `run_case.sh` is the direct non-Slurm launcher and
should only be used on an interactive compute node.

For interactive work use `cnode`, or `ssh zwu@fcfs1` (an FCFS node), then
`module load openmpi hdf5-openmpi mkl/latest` before `./build_case.sh`.

### Always verify which Config a binary was actually built with

The former hardcoded `#include "./../../build/arepoconfig.h"` has been replaced
by `#include <arepoconfig.h>`, resolved through `-I$(BUILD_DIR)`. This makes the
temporary build directory real isolation rather than cosmetic isolation.
Concurrent submissions still serialise because full Config changes rebuild
nearly every object and parallel compilation offers little benefit at this
stage; the isolation prevents shared state, while the lock limits resource use
and protects legacy tooling.

Do not use the repository-root `Arepo`, `build/arepoconfig.h`, or
`Config.current.build` for validation runs. They are legacy mutable files and
need not describe the same build. The immutable artifact manifest and checksum
are authoritative.
