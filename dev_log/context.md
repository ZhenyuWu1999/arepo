Agent entry point: [AGENTS.md](../AGENTS.md) contains stable working rules and
the reading order. This file retains project background and detailed conventions;
read the latest development-log entries for evolving scientific conclusions.

For 3D moving-mesh work on every host, use the shared English-language
[dev_log_3D_moving_mesh.md](dev_log_3D_moving_mesh.md). Its first entry records
the 2026-10-11 implementation state, geometry evidence and pending Cuillin
handoff. Earlier preparation remains in log 3; host contexts describe their
own environments, while subsequent 3D moving-mesh work is recorded together.

**Branch organization (2026-10-18):** ongoing 3D work uses
`feature/3d-moving-mesh`. `develop_pureC_RD` integrates the previous feature
history through source checkpoint `44479a1` and the shared handoff documentation.
`feature/ale-flip-conservation-hierarchy` is retained at that source checkpoint.
See [shared log entry 4](dev_log_3D_moving_mesh.md#4-2026-10-18-development-checkpoint-and-dedicated-3d-branch).
This integration preserves the existing numerical limitations; it does not
establish native moving-3D support. All three branches are the authorized
GitHub publication targets. Check the actual checkout and remote refs before
continuing on another host.

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

**Cross-host publication checkpoint (2026-10-22):**
The Mac integrates published COSMA commit `37f320b` before publishing its
interface/Blob work. Interface commit `7ab92cd` matches the previously
validated numerical source. Shared-log COSMA entries 12--17 are retained;
Mac entries are now 18--25, with links updated. See
[publication record](dev_log_3D_moving_mesh.md#26-2026-10-22-synchronize-cosma-history-and-publish-the-mac-checkpoint).
The next proposed COSMA study remains a plan, not an executed campaign.

**Proposed COSMA mesh/resolution study (2026-10-22):**
Zhenyu requests a future Braspenning comparison, explicit mesh-shape and
resolution sensitivity, and numerical handoff tables. See
[entry 25](dev_log_3D_moving_mesh.md#25-2026-10-22-proposed-cosma-blob-comparison-and-mesh-convergence-study)
and [the staged plan](RD_3D_BLOB_COSMA_PLAN_20261022.md). Reference IC/loading,
long-box gates and cost calibration precede full jobs. Native N1 and the
long-box Blob driver still need adaptation; no new run/submission. The plan
separates method/diagnostic-dependent convergence from universal non-convergence
and preserves moving-3D/hierarchy/MPI priorities.

**Blob reference setups checked (2026-10-22):**
Current IC thermal balance is correct and follows the available Morton
source, including actual Mach 1.506436. SWIFT has a dedicated
`BlobTest_Braspenning2022` reproduction directory; its generic `BlobTest_3D`
generator must not substitute for the paper IC. Braspenning differs in
domain aspect ratio, cloud sampling, mass threshold and clock. Official
HDF5 access timed out locally, so its cloud counts remain estimates.
See [comparison](RD_3D_BLOB_REFERENCE_SETUPS_20261022.md) and
[entry 24](dev_log_3D_moving_mesh.md#24-2026-10-22-compare-the-rd-blob-setup-with-swift-and-both-papers).
No solver/IC change or new hydrodynamic run; the Morton lifetime gap remains.

**Blob N1 diagnosis (2026-10-20, follow-up):**
The actual predecessor BLOB function matches all 32768 initial states; its
spatial N kernel matches the port on all 221713 initial tetrahedra to
1.790e-12 scaled residual difference. A four-step native 32³ control matches
independent Heun at roundoff. No new spatial viscosity or update multiplier
error is identified. P1-Z fails to preserve general isobaric contacts, but
the predecessor shares this response. The published lifetime gap remains
unexplained; do not equate it with demonstrated extra port dissipation.
Fig. 20 curve shapes are close after an empirical time stretch 2.867, which
is not a validated unit conversion. Braspenning uses different cloud sampling,
threshold and crushing-time conventions. See [entry 22](dev_log_3D_moving_mesh.md#22-2026-10-20-blob-n1-implementation-and-initial-condition-diagnosis)
and [diagnosis](RD_3D_BLOB_N1_DIAGNOSIS_20261020.md). No production solver edit.

**COSMA Blob results analysed on the Mac (2026-10-20):**
Downloaded 32³/eight-rank N equal/hierarchy runs both complete 1.5 t_cr.
Independent saved-state conservation is <=8.430e-14/3.681e-14, with positive
states and fixed coordinates/median duals. At the exact endpoint, the relative
volume-weighted density L1 difference is 8.265e-6. Recorded wall times are
5.178/2.832 h (observed ratio 1.828, not MPI scaling). However, threshold cloud
mass halves near .404 t_cr and reaches zero between 1 and 1.05 t_cr, much
earlier than the intended Morton N1 comparison. This is current N/lumped RK2
at very low cloud resolution (140 nodes), not a quantitative N1 reproduction
or physical convergence result. Both LDA/F1 runs fail with negative pressure
at ID14151 near .02142 t_cr, including equal steps below the last reported
CFL limit. Source/build file hashes match base `35ecccd16083`; these runs
predate the uncommitted shared-interface changes below. See
[entry 21](dev_log_3D_moving_mesh.md#21-2026-10-20-independent-analysis-of-the-downloaded-cosma-blob-results)
and the [analysis report](RD_3D_BLOB_COSMA_ANALYSIS_20261020.md).
Raw downloads stay outside Git; compact figures/data and a reproducible
snapshot-analysis script are retained in the repository. No cluster query,
new simulation, solver change or thesis edit accompanies this analysis.

**Shared element interfaces (2026-10-19):**
Zhenyu authorized the first consolidation from shared-log entry 19. The
`rd_element.h` geometry/state/output/stage-flux contracts now connect native
2D/3D evaluation with a common local/remote `rd_deposit_element()` ledger
boundary. A static P1-Z/Roe adapter preserves the pure Euler kernels and
converts vertex-first results to component-first stage layout. Legacy 2D
Gauss/ALE/B/HLLC numerical assembly remains explicit. Full `make check_rd`
passes; 62 frozen before/after native pairs (12 2D, 50 3D), 200 snapshot pairs
and 1726 particle arrays match byte-for-byte after ID sorting, with identical
logged timelines. The 3D hierarchy/MPI suite retains its previous bounds.
See [interface report](RD_ELEMENT_INTERFACE_20261019.md) and
[entry 20](dev_log_3D_moving_mesh.md#20-2026-10-19-first-native-integration-of-shared-element-interfaces).
This is an interface change, not a new residual/time method or moving-3D
implementation. The older moving HLLC Sedov control's 3.095e-3 total drift
is reproduced unchanged and is not reclassified as a conservative blast pass.

**Final-thesis supplement and COSMA update (2026-10-19):**
Zhenyu reports that COSMA Blob tests for N and LDA have been submitted; no
results are available yet. This is a user-reported status, not a live scheduler
inspection. Job IDs, actual resolution/ranks/time integration, source revision
and completion status still need to accompany the results. Do not infer a
completed Blob validation from submission or from the local N-only pilot.

At the user's request, prepare English mathematical review documents for the
final thesis under the Mac path
`/Users/zhenyuwu/Desktop/MyThesis/supplementary_doc/`. The first is
`static_3d_rd.tex` (compiled review PDF alongside), covering tetra geometry,
Roe N/LDA, temporal mass, equal-step conservation, the experimental static
hierarchy, CFL and MPI. It tracks source `35ecccd16083` and follows the thesis
style. This is a separate draft awaiting Zhenyu's review; it does not authorize
edits to existing thesis chapters or establish new numerical results. See
[shared-log entry 18](dev_log_3D_moving_mesh.md#18-2026-10-19-static-3d-mathematical-supplement-for-final-thesis-review).
The supplementary directory is outside this repository and is not transferred
to clusters by Git. Future mathematical revisions and numerical evidence
should be reconciled before any explicitly requested thesis integration.

The following COSMA-side handoff records are retained with their original dates; later Mac analyses and proposals above supersede their transfer/pending-status statements where applicable.

**Portable Blob analysis packages (2026-10-20):**
[Shared-log entry 16](dev_log_3D_moving_mesh.md#16-2026-10-20-standalone-initializationanalysis-scripts-and-compact-mac-bundles)
records two standalone NumPy/h5py scripts and validated compact Mac downloads:
156.4 KiB for tools/configs/provenance,162.2 MiB including full snapshots/IC.
Download archives and checksum sidecars are in `/cosma/home/do020/dc-wu8/arepo_rd/cosma_runs/`;
no Mac transfer occurred. Original N/LDA apps archives and failed evidence
are preserved. See the campaign report for
paths/checksums and actual completed/failed outcomes.


**COSMA Blob outcomes audited (2026-10-20):**
[Shared-log entry 14](dev_log_3D_moving_mesh.md#14-2026-10-20-cosma-execution-audit--n-completes-lda-stops-at-negative-pressure)
records actual execution on gc001. N equal12187329 and hierarchy12187330
completed 32³/8-rank evolutions to 1.5 t_cr, with passing analysis and snapshot
conservation 8.43e-14/3.68e-14. LDA equal12187332 and hierarchy12187333 passed
preparation but both failed raw negative-pressure checks at .02142334 t_cr,
stage 1, ID 14151. No jobs remain queued/running. Failed evidence is preserved;
there was no rerun, repair or new numerical-source change. Read the latest
COSMA context/report; the pending handoffs below are historical. Static N
completion does not validate LDA long-time positivity or moving 3D support.


**Both Blob schemes required (2026-10-19):**
The user's correction is implemented in
[shared-log entry 13](dev_log_3D_moving_mesh.md#13-2026-10-19-user-correction--test-blob-with-both-n-and-lda).
N retains pending jobs 12187116–12187119; independent LDA Blob jobs
12187273–12187276 are also pending. Each scheme targets32³ equal/hierarchy,
eight ranks, gamma 5/3, CFL.01,1.5 t_cr, with its own successful native gates
and timing required before long submission. The previous N campaign's LDA
cases were only warm controls. Exact Blob IC arrays and solver source match
across the two campaigns; native results remain unmeasured. Read the COSMA
context and campaign report before submitting duplicates.


**COSMA static Blob queued (2026-10-19):**
Live COSMA environment inspection and a frozen Linux campaign are recorded in
[shared-log entry 12](dev_log_3D_moving_mesh.md#12-2026-10-19-cosma-static-3d-blob-preparation-and-dependent-submissions)
and the [COSMA Blob report](RD_3D_BLOB_COSMA_20261019.md). Base source `35ecccd`
is unchanged. Build/gate/calibration/conditional-submit jobs
12187116/12187117/12187118/12187119 are **pending**, with the scheduler initially
estimating a 09:00 Europe/London build start after a reservation ends. The
32³, 1.5 t_cr N/RK2 equal/hierarchy inputs use eight ranks, gamma 5/3 and CFL .01;
long jobs require successful native checks and measured wall budgets. Evidence
is in apps storage `.../arepo-rd/rd_3d_blob_20261019_v2/`. No new COSMA numerical
success, moving-3D support or paper N1 reproduction is claimed. Read the COSMA
context before submitting another job; this chain is already queued.


**COSMA source handoff (2026-10-19):**
Zhenyu will check COSMA access/resources. [Shared-log entry 11](dev_log_3D_moving_mesh.md#11-2026-10-19-cluster-recommendation-and-cosma-handoff)
recommends cluster compute nodes for full 32³+ Blob, long stability/convergence
and MPI scaling. Local work stays short. Fetch `feature/3d-moving-mesh`,
preserve host changes, verify the historical COSMA environment, rebuild under
Slurm and run short feature/Blob calibration gates before committing to a
long job. See [COSMA context](context_cosma.md) for the batch/provenance recipe;
the Mac campaign helpers' `otool` step needs Linux adaptation. No COSMA state
or available allocation was checked in this local handoff. Local binary/IC
archives are not included in a Git pull.

**Blob preparation and execution check (2026-10-18):**
[Entry 9](dev_log_3D_moving_mesh.md#9-2026-10-18-morton-blob-preparation-and-short-hierarchympi-checks)
and the [test report](RD_3D_BLOB_PREPARATION_20261018.md) record a Morton-inspired
static 16³ N/RK2 check to .01 cloud-crushing times. Equal steps and natural
hierarchy on 1/2 ranks complete with positive states, conservation <6.062e-15,
actual bin ratio 4 and rank field differences <3.411e-15. There are only 14
cloud nodes. A 32³ IC with 140 cloud nodes is prepared but not evolved; a full
N1 paper reproduction and moving Blob remain pending. Continue the simpler
analytic advection/geometry gates for moving-path development.

**User priority after Sedov (2026-10-18):**
Complete the 3D mesh/moving-RD workflow, hierarchical timesteps and MPI before
3D HLLC-RD or other strong-shock remedies. Cold Sedov success and solve
rescaling are not prerequisites. Use warm uniform/smooth/Gresho controls for
the pipeline gates; preserve the shock failures as limitations. Static
hierarchy/MPI has small validated gates; moving hierarchy/MPI still needs its
own implementation and checks. [Shared-log entry 8](dev_log_3D_moving_mesh.md#8-2026-10-18-sedov-failure-diagnosis-and-development-priority)
records this decision and four failed 16³ Sedov attempts: cold N/LDA reproduce
the solve-audit stop; a separately labelled p0=1e-3 control reaches raw negative
pressure (N after 51 correctors, LDA in the first corrector). No 3D HLLC or
production scaling change was made.

**Low-resolution static 3D Gresho check (2026-10-18):**
[Shared-log entry 7](dev_log_3D_moving_mesh.md#7-2026-10-18-low-resolution-static-3d-gresho-physical-check)
records completed 16³ N/LDA runs to t=.25 on the static periodic tetrahedral
mesh. Both use 2048 equal steps; velocity L1 is .085648/.0235345 and retained
kinetic energy is 56.63%/97.54%, with conservation below 2.887e-15 and positive
states. The IC is z-invariant; final spurious z speeds reach about .03. This
is a low-resolution physical check, not convergence or moving-RD validation.

**3D progress review and new controls (2026-10-18):**
Read [shared-log entries 5–6](dev_log_3D_moving_mesh.md#5-2026-10-18-claude-review-of-entries-14-and-face-connected-cavities)
and the [English review](RD_3D_MOVING_PROGRESS_REVIEW_20261018.md) before using
the older cavity or CFL conclusions. Claude's face partition is independently
confirmed: random CFL .3's first-step 1599-vertex group becomes 543 face regions,
largest 13; shared nodes still couple transfers. First-pair face regions have
zero integer boundary and no winding; later winding cases remain unmeasured.
Two short native FV runs at a fixed `2^-12` timestep ceiling complete: random
64 steps has 2/1 old/new invalid intervals, shear 128 steps has 0/0. This is not
a dynamically recomputed moving-RD CFL test. M1/M2 are complete within their
scopes, native moving 3D RD remains unimplemented, and Cuillin work is pending.
Next is controlled fixed-connectivity M3 with fail-fast geometry/topology guards;
the original exact-affine M3.4 requirement is superseded by M1's correction.
Keep production unscaled and the user-deferred 2D compatibility issue recorded.

**CFL interpretation corrected (2026-10-14):**
Read [shared log entry 3](dev_log_3D_moving_mesh.md#3-2026-10-14-cfl-reference-audit-and-correction-to-the-diagnosis)
before extrapolating M2 failures to RD. M2 uses public FV CFL, with an `r_ij+R_i`
tree travel distance, not the literal paper (130) or RD spectral condition.
Strict published-signal and current static-RD first-state reference bounds give
smaller steps; frozen-velocity periodic mesh oracles have zero old/new inversions
at those steps. The loop's first mesh-velocity reassignment also matters.
These are offline first-state comparisons, not validated moving-RD evolutions.
Voronoi FV and Delaunay-based RD retain distinct geometry/transfer requirements.

**Nonpositive-volume cause audit (2026-10-14):**
[Shared log entry 2](dev_log_3D_moving_mesh.md#2-2026-10-14-cause-of-nonpositive-3d-volumes)
and the [cause report](RD_3D_NONPOSITIVE_VOLUME_CAUSE_20261014.md) distinguish
native endpoint geometry from old-forward/new-pullback signed volumes.
All 43 invalid records survive a 60-digit determinant audit. Thin tetrahedra
cross orientation under finite relative motion; the current Voronoi CFL does
not enforce interval tetra positivity. Three small local native controls reuse
the frozen `57e1ae3` binary: random CFL=.3 reproduces 16/15 old/new inversions
with regularization and gives 0/0 without it, at the same eight timesteps.
A shear event with zero correction shows this is not solely a regularization
issue. Five negative new-element Campoli means follow from negative pullbacks.
No production geometry/velocity/timestep/scaling change or cluster run was made;
M3 and the inversion/transfer policy remain pending.

**Current 3D moving-mesh handoff (2026-10-11):**
Read [shared log entry 1](dev_log_3D_moving_mesh.md#1-2026-10-11-current-state-and-handoff-to-cuillin)
for the status and evidence at implementation checkpoint `57e1ae3`.
M1 mathematics and the M2 read-only native FV geometry diagnostic are complete
within their stated scopes. The short local pilots expose interval inversions,
nonpositive element temporal volumes and large/winding cavities; native moving
3D RD and a transfer acceptance policy remain unimplemented. The next solver
milestone is a controlled fixed-connectivity M3 adapter. Zhenyu plans further
Cuillin tests; Linux campaign adaptation and one-rank parity checks are pending.
No cluster build, submission or live host inspection occurred in this handoff.
Keep production Euler unscaled and the current 2D arithmetic/lazy-OFF baseline.
Large campaigns belong on clusters; record all 3D moving-mesh work in the shared
log, including host, revision, artifact location and actual job status.


**Earlier M1 checkpoint (2026-10-11):** moving 3D preparation has an independent
geometry and Campoli-ledger proof/oracle, documented in
`RD_3D_MOVING_GEOMETRY_MATHEMATICS_20261011.md` (log3 §240). Production remains
unscaled per the user's preference not to make rescaling a prerequisite.
The complete fixed-connectivity periodic model conserves to round-off with
exact mean face vectors; midpoint normals fail the nonuniform control.
Five-component transfer models now include 4-4/larger cavities. Native moving
3D is still unsupported. The subsequent M2 diagnostic is complete locally;
see the shared log for its evidence and the current next milestone.
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
    arepo/dev_log/dev_log_3D_moving_mesh.md           (CURRENT shared 3D moving-mesh log)
    arepo/dev_log/RD_DEVELOPMENT_LOG_3_localMac.md (other local work; earlier 3D preparation)
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

**Current logging convention, confirmed 2026-10-11:** write development logs
in English. Append all 3D moving-mesh preparation, implementation, reviews and
tests to `dev_log_3D_moving_mesh.md`, whether on the Mac, Cuillin, COSMA or another
host. Synchronize this version-controlled file through Git; merging concurrent
entries must preserve both authors' records. Include the execution host,
revision, evidence location and actual job/test status. The local archives
referenced by an entry are not automatically shared with the Git checkout.

Other local work continues in `RD_DEVELOPMENT_LOG_3_localMac.md`; volumes 1 and 2
are historical. The former 2026-09-10 convention of putting all local work in
volume 3 is superseded for the 3D moving-mesh topic. Start with the applicable
host context and latest shared-log entries; follow earlier log 3 references
when needed. Read `RD_DEVELOPMENT_LOG_2.md` section 1 as needed for the historical
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
