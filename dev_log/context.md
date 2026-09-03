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
- **Chapter 4 is currently a mathematical working draft, not polished or final
  thesis prose.** Its present purpose is to formulate and discuss moving-mesh
  ALE-RD, DGCL, changing Delaunay topology, and hierarchical-timestep questions
  before the engineering implementation is chosen. Equations, alternatives,
  objections, and explicitly unresolved points may be recorded there.
- Do not silently promote Chapter 4's current formulas into settled design or
  formal thesis claims. Distinguish derivations that have been established from
  proposed formulations that still require review by Zhenyu, Claude, or Kimi.
- Outside an explicitly requested Chapter 4 mathematics update, do not modify
  the local thesis files. In particular, do not polish Chapter 4 into formal
  narrative or propagate its draft statements into Chapters 1--3 without an
  explicit instruction.

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

3. **Still open.** We have only implemented 2D RD in AREPO. The 3D code is still in /home/zwu/rdsolver/rd. Ideally, there should be a unified interface for both 2D and 3D. 3-D is explicitly out of scope for the moving-mesh phase.

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
    arepo/dev_log/RD_DEVELOPMENT_LOG_2.md           (ACTIVE main log: moving mesh)
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

**Start a new session by reading `RD_DEVELOPMENT_LOG_2.md` section 1**, which
carries forward everything settled, deferred and still open at the end of
volume 1. Volume 1 is 9000 lines and does not need to be read in full; it is
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
