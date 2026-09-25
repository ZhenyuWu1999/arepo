# AREPO-RD local macOS context

Agent entry point: [AGENTS.md](../AGENTS.md). Keep stable working rules there;
this file holds local paths, toolchains and the evolving handoff.

Updated: 2026-09-25

**STOPPED for COSMA migration (2026-09-25, log3 §113):** User explicitly
terminated all local hydro tests. Both launchd jobs removed and all six solver
workers verified absent. Earlier RUNNING entries below describe historical states.
Partial outputs preserved with user_stopped/not_started records, no t1 error
assigned. Detailed tasks and executable preparation steps:
[COSMA Yee handoff](RD_COSMA_YEE_HANDOFF_20260925.md). Exact termination times/hashes:
[YEE_LOCAL_TERMINATION_20260925.json](YEE_LOCAL_TERMINATION_20260925.json).
Transfer bundle: `../local_runs/cosma_handoff_20260925/yee_inputs/` (eight original
HDF5 inputs,7.4MB; hashes tracked). Portable preparer accepts destination input
paths and creates18 primary or27 including-lab cases; no remote jobs submitted.
Moving comparisons use co-moving; thesis reference stays lab, A2 factor4096
unchanged. COSMA moving still one rank, parallelize independent cases. Four algebra
tests and preparation/hash/config checks pass;152 production hashes unchanged.
User requested code/log commit and GitHub push. Unrelated diagrams remain local.

**User choice / co-moving campaign (2026-09-25, log3 §112):** Enable co-moving
for current moving comparisons; thesis default remains lab and mechanism unresolved.
`../local_runs/yee_boost10_comoving_20260925_v1/` uses moving co-moving at boost1/10
and48/96/192, static lab controls reused from recovery. Existing lab runs continue
separately. Reuses48boost10 co-moving diagnostic; new boost1 uniform, boost10 pilot
and five science runs. Two extra workers (at most6 total), OMP/BLAS1. One-shot
launchd label com.zhenyuwu.codex.yee-comoving-20260925-v1. Check launchd.out/err,
progress.py, pipeline_status.json; final visual QA pending. No solver/default/
thesis changes. A2 tolerance is4096 eps times pre-cancellation scale; failure is
2.265×threshold, normalized2.06e-12. Possible bound underestimate vs rank/split
errors remains unresolved; do not loosen tolerance based on this alone. Audit:
[criterion and run choice](RD_YEE_A2_TOLERANCE_AUDIT_20260925.md).

**RUNNING recovery (2026-09-25, log3 §111 follow-up):** At13:59CST the four192
runs and old parent/watcher were absent; logs last advanced2026-09-24 23:36.
Original session5902/94005 no longer live. Exact cause unknown; previous assurance
of background continuity was incorrect. No192 restart checkpoints. Preserved all
original outputs and reran ONLY four192 cases from ICs in
`../local_runs/yee_boost10_static_moving_20260925_recovery_v1/`. Existing successes
and48failure reused for analysis by symlink, no tolerance/source changes.
Independent one-shot launchd job `com.zhenyuwu.codex.yee-boost10-recovery-20260925-v1`
started and verified parentPID30904,PPID1 with advancing solver logs. Four workers,
OMP/BLAS1. New pipeline analyzes all18 cases after completion despite48failure.
Check progress.py, launchd.out/err, pipeline_status.json/error.txt; final QA pending.
No new convergence results yet. Completed48co-moving diagnostic remains separate.

**Previous interrupted attempt: Yee boost10 sensitivity (2026-09-24, log3 §111):** LDA/Gauss3 lab
static/moving, boost1/10 at48/96/192², matched dt1/1024,1/2048,1/4096. Four
uniform gates and two192 pilots pass; seven science complete,48movingboost10
fails A2 raw residual conservation at t≈.237305 (4.88e-12 >2.16e-12), four192
science runs continue. Native main session5902; independent analyzer94005.
Main parent will assert after all jobs finish due to retained failure; independent
watcher still produces final report/figures. See archive README/progress.py at
`../local_runs/yee_boost10_static_moving_20260924_v2/`.96 density boost10/1:
static10.9609,moving1.000441; boost10 moving/static=.157665. Preliminary96 plot
visually checked. Separate48co-moving diagnostic passes to t1 with unchanged
IC/dt/tolerance; only frame flag differs. Do not substitute it for failed lab point.
No floor or unique causal attribution established. Fits use full three-point
series only. No solver/default/thesis edits, no commits. Final analysis/visual QA
and context/report update remain. Report: [boost sensitivity](RD_YEE_BOOST10_SENSITIVITY_20260924.md).


**Yee density profile (2026-09-24, log3 §110):** Postprocessed existing384²
LDA lab/Gauss3 static/moving snapshots, no new runs. Profiles almost coincide;
moving density error is concentrated at r<2 (87.79% of its global L1), with a
slightly elevated core. Outer shell errors are lower than static. This locates
error, not its cause. Boost1 is comparable to vortex vmax .7958; mesh follows
local flow/pressure predictor/regularization rather than rigid translation.
Report: [density profiles](RD_YEE_DENSITY_PROFILES_20260924.md). Original nodes,
analytic center(6,5), no regridding; global norms match§107. Four-point fit
interpretation from§109 retained; no persistent order-reduction claim.


**Thesis distribution cleanup (2026-09-24, log3 §108):** Explicit user authorization
for a Chapter 3 pseudoinverse paragraph and a shorter Chapter 4.2 distribution
subsubsection. Installed only those two TeX files. Exactness scoped to compatible
Roe stagnation systems, not arbitrary contour targets. All equations/labels kept;
Chapter4.3 and 4.2 outside distribution unchanged. Partial Chapter3/4.2 previews
33/20 pages, no unresolved refs, edited-page visual QA passed. Full master.pdf
not rebuilt/replaced. Archive `../local_runs/chapter3_4_distribution_20260924_v1/`.


**Completed Yee384/static comparison (2026-09-24, log3 §107):** All12 new
runs complete plus6 archived controls. Both background sessions have exited.
Four resolutions48/96/192/384², boost1,t1,lab only, matched ICs and dt caps.
384 moving/static rho/velocity L1 ratios: N .875/.565; LDA1.558/1.140.
LDA moving velocity error crosses above static at384. Per user correction
(log3 §109), primary convergence orders are whole-range four-point log-log
fits: N static rho/v .972/.928, moving .900/.904; LDA static1.687/1.774,
moving1.736/1.407. Adjacent slopes are diagnostics only; do not infer persistent
LDA order reduction from the final interval. User deferred768² due to time.
Discuss possible mechanisms without assigning causality or launching more runs.
All native/provenance/positivity checks passed and figures visually reviewed.
384 moving mass drift N−6.065e−7/LDA−2.870e−7, static machine precision.
LDA moving F1 fallback count increases to31898 (0.00528% of corrector element
updates), not a causal demonstration. No384 dt-half/frame ablation performed.
Report: [Yee384 comparison](RD_YEE_STATIC_MOVING_384_20260924.md).
Archive `../local_runs/yee_static_moving_384_20260924_v1/` contains final
summary/verification/native diagnostics, plots and full provenance.
No solver/default changes or further thesis edits in this numerical analysis.


**Thesis lab-frame reference confirmed (2026-09-24, log3 §106):** User accepted
lab as the thesis reference and authorized moving the entire co-moving section
into red to-delete alternatives. Local Chapter4 now does this in both theory
and implementation; main LDA/F1 uses unprimed lab quantities with mesh advection
retained. All co-moving theory/equations preserved in red. Existing example
Config still enables the optional frame and is described only in red; no code
or default Config changed. Chapter4.1/4.2.1 unchanged. Full compile251 pages,
zero unresolved/duplicate refs, Chapter4.2 preview21 pages; installed locally
only, no commit/push/Overleaf sync. Archive:
`../local_runs/chapter4_comoving_optional_20260924_v1/`.


**Yee/Gresho frame figures (2026-09-24, log3 §105):** 16 new current-source
moving Yee boost1 runs complete: N/Roe and LDA/Gauss3, lab/co-moving, glass
48/96/192 squared to t1 plus96 dt-halving controls. Density h-orders lab:
N .833/.902, LDA1.840/1.757; co-moving .833/.903 and1.840/1.760. LDA velocity
orders fall1.753→1.384 (co1.752→1.393), so do not claim strict second order
for all fields. Frame changes rho L1 by<.20%, velocity L1 by<.56%. Gresho
boost10 figures reuse §103 data; prior N/lab uniform1e−12 gate failure remains.
KH flip history supports topology as an important channel, but current drift
also admits Arpaia endpoint error; general moving hierarchy additionally needs
actual element lifetime coverage. Restricted N prototype already exists.
Evidence supports lab as reference and co-moving as optional optimization,
pending user's final review; no thesis/default/solver change. See
[the report](RD_YEE_GRESHO_FRAME_FIGURES_20260924.md), archive
`../local_runs/yee_frame_convergence_20260924_v1/`.

**Lab-frame Sod/KH extension (2026-09-24, log3 §104):** User prefers co-moving
as an optional optimization if lab results are acceptable. Matched N/Roe and
LDA/Gauss3 lab runs now complete Sod t=.08 and smooth KH t10; four uniform gates
pass. Only the frame flag differs from archived exact-source co-moving controls.
Sod density L1 changes <.04%, velocity L1 <.2%. KH t10 transverse energy is lower
by20.6% (N) /13.7% (LDA), so long trajectories are not equivalent. Both frames
retain ~1.2–1.4% global mass drift. Evidence supports optional frame status in
the current reference exposition, not complete moving-solver acceptance.
No thesis/default/production-code change yet. See
[the report](RD_SOD_KH_LAB_FRAME_20260924.md), archive
`../local_runs/sod_kh_lab_frame_20260924_v1/`.

**Current Gresho frame audit (2026-09-24, log3 §103):** N/Roe split and
LDA/Gauss3 both complete boosts0/10 in lab and element co-moving frames to t=1
(jitter48², gamma5/3, CFL.3). The old boost10 abort does not recur in these
current configurations. Co-moving still lowers the first-stage paired matrix
condition number by a median ~2.4e4 at boost10 on the stated nondegenerate subset.
N's residual boost dependence remains in both frames. Uniform N/lab narrowly
fails the existing absolute1e-12 gate (pressure1.182e-12), explicitly retained;
other three uniform gates pass. No solver/thesis/default changes. See
[the report](RD_GRESHO_FRAME_COMPARISON_20260924.md) and archive
`../local_runs/gresho_frame_20260924_v1/`. This is diagnostic evidence, not a
new baseline acceptance or proof of full-update conservation.

**Thesis N/Roe and LDA/contour distinction (2026-09-24, log3 §102):**
Chapter4.2 now presents N with the ALE Roe split plus its mesh correction,
followed by LDA's Gauss3 contour choice motivated by preliminary KH tests.
Distribution schemes retains ALE characteristic splits for both and explicitly
states LDA residual-sum conservation under the invertibility assumption.
The experimental N contour reconciliation is removed from this thesis exposition,
not from solver code. Local thesis and the 4.2 preview are compiled and updated;
no commit/push or Overleaf write. Archive:
`../local_runs/chapter4_n_split_lda_contour_20260924_v1/`.

**Experimental N/Gauss3 moving comparison (2026-09-24, log3 §101):**
Equal-step ALE N+Gauss3 is now explicitly permitted and tested using the existing
N equal-share residual reconciliation. This does not replace the LDA/F1 baseline.
Current matched smooth-KH glass48² runs: N/Roe, N/Gauss3 and LDA/Gauss3 reach t=10;
LDA/Roe fails with negative mass at t=1.0327148. The archived LDA/Roe binary also
reproduces its original t=.800476 failure exactly. All four Sod runs and eight
uniform gates pass. Completed current KH runs retain 1.19–1.38% final total-mass
drift, so full-update conservation remains unresolved. See
[the report](RD_N_GAUSS3_SPLIT_20260924.md) and
`../local_runs/n_gauss3_split_20260924_v1/` for frozen source, isolated binaries,
run logs, metrics and figures. No thesis edits or commits in this experiment.

**Static beta default reconciled with thesis (2026-09-19, log3 §79):**
standard static LDA/F1 again uses mixed stage beta_n/beta_* without a flag;
common opening beta_n is opt-in through `RD_LDA_COMMON_OPENING_BETA`. The
solver is byte-identical to the §76 frozen/replayed source and all four
`make check_rd` scripts pass. Chapter4.1 now labels its archived mixed KH
figure correctly as four-rank data and writes the edge contribution as an
explicit line integral. No other hierarchy/N-scheme prose changed. Thesis
compile checked; no commit/push.

**Moving Chapter4 baseline organisation (2026-09-18, log3 §78):** at the
user's explicit thesis-edit request, 4.2/4.3 now select the existing one-rank,
equal-step Arpaia midpoint/divisor + P1-U nonlinear Gauss3 contour + element
co-moving frame + mixed LDA/F1 reference. Both physical sweeps remain after
the normal single rebuild on NEW connectivity; begin records the interval.
No solver/Config/default change or new hydro run. Alternative formulations,
true old/new split stages, Voronoi storage and moving-hierarchy closures are
red end-of-section material marked `to delete`. Native Q/divisor lifecycle,
topology and endpoint weight defects, time-order and CFL limits are explicit.
4.1/other chapters/bib/figures are preserved. Full compile247 pages, resolved
references; printed153--177 reviewed, including red caption and colour scope.
Only local chapter4.tex installed, no commit/push; normal Overleaf sync pending.
Archive: `../local_runs/chapter4_moving_baseline_20260918_v1/`.


**Latest figure cleanup (log3 §77):** Chapter4 figure names now omit dates.
Hierarchy schematic bottom explanatory lines removed; nodal colour/ring legend
retained. All6 dated thesis figures renamed and4 LaTeX references updated;
old dated research artifacts remain archived. Full compile245 pages, all5 figure
pages checked. Archive: `../local_runs/chapter4_figures_clean_names_20260917_v1/`.
No solver change, commit or push.

**Current baseline restored (2026-09-17, log3 §76):** standard static LDA/F1
again uses mixed stage beta_n/beta_* by default. Common opening beta_n is now
explicitly opt-in via RD_LDA_COMMON_OPENING_BETA; RD_LDA_MIXED_STAGE_BETA is a
legacy explicit selection of the default. Four native rank4 replay cases match
all32 archived snapshots exactly, including the common-beta control. Algebra
gates pass. Chapter4 restores mixed equations and old rank4 KH data, retaining
compact Delta E/E0 [10^-16]; the common-beta_n/Paardekooper comparison is limited
to measured Yee errors. Full compile245 pages; only Chapter4/new figure installed.
See `RD_MIXED_BETA_BASELINE_RESTORED_20260917.md` and workspace
`local_runs/restore_mixed_baseline_20260917_v1/`. No commit/push. §73 below is a
superseded default trial; its singular spatial extension is retained opt-in.

**KH signed-energy audit (2026-09-17, log3 §74):** six exact-binary KH reruns
at ranks1/2/4 plus six read-only conserved-energy diagnostic runs complete.
All prior44 rank1/4 snapshots reproduce exactly; all66 diagnostic snapshots
match uninstrumented reruns. The ~1e-16 drift is already in stored Energy;
primitive reconstruction/plot arithmetic contribute only a few1e-18.
Equal-step t2 drift changes from negative at4ranks to positive at2ranks:
its sign is not an intrinsic dissipative property. See
`RD_KH_ENERGY_ROUNDOFF_AUDIT_20260917.md` and workspace
`local_runs/kh_roundoff_audit_20260917_v1/`. No production code/thesis changes.

**Historical common-beta default trial (2026-09-17, log3 §73; superseded by §76):** at the user's request,
the standard static path now uses common interval-opening beta_n for both
spatial halves and F1, including equal internal/split and hierarchy. The
explicit RD_LDA_MIXED_STAGE_BETA flag reproduces the former mixed method.
Native Sod gates exposed a singular old-matrix/new-target range mismatch;
the common spatial distribution now shares the unresolved component equally,
while the existing rank-deficient temporal lumped fallback remains. This is
an explicit numerical extension, with unchanged rank/conservation tolerances.
All17 final native cases and make check_rd pass; mixed controls exactly replay
the archived states. Report: `RD_COMMON_BETA_DEFAULT_20260917.md`; archive:
`../local_runs/common_beta_default_20260917_v1/` (`native` preserves the initial
two Sod failures, `native_final` the successful final implementation).
Chapter4 records the common default, singular exceptions and limited earlier
Yee three-way observation; its KH graph is regenerated from the new default.
Moving/N/B/four-pass rate-Heun policies are unchanged. No new convergence or
general positivity claim; code/thesis remain uncommitted and unpushed.

**RD stage equations (2026-09-17, log3 §69--70):** the user approved replacing
the long RD implementation paragraph with English stage notation and explicit
N/lumped and LDA/F1 corrector equations. Literature checked: Ricchiuto & Abgrall
2010, Arpaia et al. 2015, Paardekooper 2017. The text distinguishes the current
mixed spatial-stage convention from the common-beta form in Paardekooper Eq63.
Follow-up source audit (log3 §71) identifies that common beta as beta_n in
ASTRIX v1.0.0/v1.1.0, including F1; it is not direct support for our mixed
beta_n/beta_* choice. See `PAARDEKOOPER_STAGE_BETA_AUDIT_20260917.md`.
The old 2026-08-01 three-convention Yee experiment was recovered from log1;
its similar errors were not a mass-term-only beta test and all three had
roughly first-order temporal convergence. Source/experiment audit and current
review pages 143--144 are in
`../local_runs/chapter4_rd_stage_math_20260917_v1/` (SCIENCE_REVIEW.md and
`output/pdf/chapter4_rd_stage_math_review.pdf`). Full compile passes,245 pages;
only the RD paragraph changed. Thesis remains uncommitted and unpushed.

**FV notation correction (2026-09-17, log3 §67--68):** Zhenyu approved the
code-check findings. Chapter 4 now writes each FV hook as
`Q += -dt/2 sum(A F)` and consistently distinguishes primitive W, conserved
density U and integrated conserved Q. The primitive prediction W' and the
completed-Q synchronization are explicit. Only the FV description changed;
the comparison table, RD paragraph and later sections retain the §66 draft.
Full compile passes (245 pages, resolved references); review pages 142--143:
`../local_runs/chapter4_fv_notation_20260917_v1/output/pdf/chapter4_fv_update_review.pdf`.
Local thesis remains uncommitted and unpushed. The §66 PDF predates this edit.

**Latest thesis draft (2026-09-16, log3 §66):** local thesis/GitHub base
`fdb3db5`; Chapter 4.1.1 comparison preserved, F1 red placeholder checked
against the current code and completed. Hierarchy/MPI are now sections 4.2/4.3
in the local draft, with the existing A--E schematic, native MPI figures and
a new smooth-KH energy history from archived `943f7ae` glass2304 outputs.
Review and code/science notes are in
`../local_runs/chapter4_sections_draft_20260916_v1/`. Full thesis builds;
edits are **uncommitted and unpushed**, awaiting the user's review. The original
FV formula/notation issues identified at this stage were subsequently corrected
with the user's approval in §68 above. No solver/baseline change or new hydro
experiment in these thesis tasks.

This file records the local Apple Silicon development environment for small
two-dimensional AREPO residual-distribution tests. It supplements `context.md`;
the cluster development logs remain the scientific history of the project.

**Logging convention, confirmed 2026-09-10:** all current work continues in
`RD_DEVELOPMENT_LOG_3_localMac.md`. Keep volume 2 as the historical moving-mesh
record; do not append new local findings there. For the current scientific
status, read the latest volume-3 entries; the setup-era handoff below is historical.

**Current checkout/baseline (2026-09-13, log3 §36):** returned to
`develop_pureC_RD`; selective static contour/Gauss port build source943f7ae.
The experimental branch is preserved at53cb65a. Primary baseline/choice table:
`RD_STATIC_BASELINE_CHAPTER4.md`. Static is the sigma0 fixed-connectivity ALE
limit: Arpaia/Campoli geometry choices coincide and the implemented local
mesh frame is the identity; F1/lumped and P1-U/P1-Z flux choices still differ.
The named equal/hierarchy Gauss3 configs are qualified experimental baselines,
not a claim of problem-free or second-order multirate LDA. Default Config
and thesis are untouched. Details and latest measurements are appended below.

**Current code trial (2026-09-14, log3 §42):** opt-in
`RD_RK2_SPLIT_STAGES` moves static equal N/LDA predictor/corrector to the two
main-loop hydro hooks without changing the GL/F1 update. Named trial Config:
`examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_EQUAL_SPLIT.sh`. See
`RD_EQUAL_SPLIT_STAGES_20260914.md` for the frozen source,24 native cases,
restart/extension and actual1155-node MPI remapping gate. Same-rank reference
states match exactly; other comparisons are at roundoff. The original named
reference and default Config are retained. Trial source is currently an
uncommitted working change; no runtime-speed claim or hierarchy F1 change.

**Current common RD hooks (2026-09-14, log3 §47):** Zhenyu explicitly rejects
the §46 extra mesh build; that preview implementation has been removed.
The main loop calls rd_step_begin / rd_step_end. Static split still performs
predictor/corrector at those hooks; equal ALE begin only records the interval,
then end runs the original two sweeps on the single normally rebuilt mesh.
No node/DC/RNG rollback, extra tree build, per-node preview cache or duplicate
ALE geometry remains. Report: `RD_MOVING_SINGLE_MESH_HOOKS_20260914.md`;
archive: `../local_runs/moving_single_mesh_hooks_20260914_v1`.
All25 moving cases and14 comparisons pass, including exact t=1/restart
agreement;1216 hook intervals each have one mesh, one geometry preparation
and two sweeps. Named Config retains its historical SPLIT filename, with
updated semantics: `examples/yee_2d/Config_RD_ALE_LDA_GAUSS3_EQUAL_SPLIT.sh`.
Moving hierarchy's actual call order and the ALE conservation limitations
remain. The follow-up to Claude's review is log3 §50: an all-node equal-bin
check at the ALE opening hook is enabled only by RD_DEBUG_ASSERTS, with three
native regression cases identical to §47 and 20 compiled hook checks passing.
Updated common-hook figure (white, function names, blocks 1–14):
`figures/Arepo_flowchart_main_loop_RD_functions_reviewed_20260914.drawio`.
Its static and equal-ALE dispatch are explicit; the user's earlier draw.io is
preserved. Matching draw.io/PNG copies are in the thesis resource directory.
Review archive: `../local_runs/rd_review_polish_20260914_v1`.
Claude's §49/docs are committed at adc424b; source/Config and the §50 changes
remain uncommitted. No staged changes were present during this follow-up.

**New numerical exploration (2026-09-14, log3 §51):** Zhenyu asked whether
moving ALE-RD can genuinely place its predictor before the mesh change and
corrector after it with one new Delaunay build. An independent Campoli
endpoint-mass model now uses OLD connectivity for the first residual and NEW
connectivity/F1 mass for the second, plus a derived local cavity total-balance
term. Ten scalar/Euler main cases with flips conserve to 1.89e-15 and preserve
uniform states to 5.33e-15; still one build and two physical residual sweeps per
step. This is not a native implementation or a direct change to Arpaia.
The unrestricted correction has a documented positive-input/negative-output
counterexample. Fixed-connectivity time order remains N≈2 / F1≈1; with flips
the candidate does not demonstrate time order2. Smooth scalar h slopes are
1.78/1.89 for LDA, with h/dt refined together. Report:
`RD_TRUE_ALE_SPLIT_EXPLORATION_20260914.md`; scripts `tests/rd/explore_true_ale_split*.py`;
archives `../local_runs/true_ale_split_*_20260914_v1`.
No C, Config, existing flowchart or thesis changed. Current hooks retain the
§47/§50 behavior above. Next research gates are admissible local correction,
geometry validity, native state/cache/restart lifecycle and measured cost;
MPI/hierarchy and complete second-order time integration remain unvalidated.

**Arpaia clarification (log3 §52):** the true old/new stage structure also
admits Arpaia's internal mass/divisor pair, but the §51 topology-only correction
leaves an additional endpoint defect `sum d_i*(Utrial_i-Uold_i)`, where d is
new-connectivity endpoint area minus the Arpaia divisor. A proposed nodal Q
correction removes this term in addition to the cavity correction. Sixteen
independent one-step scalar/Euler pairs verify the identity to1.76e-15 and
corrected totals to2.22e-15; this is not original Arpaia unchanged and is not
identical to corrected Campoli. No multi-step accuracy/positivity/native claim.
Report: `RD_TRUE_ALE_SPLIT_ARPAIA_20260914.md`; archive:
`../local_runs/true_ale_split_arpaia_20260914_v1`. C and default settings unchanged.

**Current user direction / figure (log3 §§53–54):** defer further moving-mesh
numerical research and return to the main-loop figure. Latest editable copy:
`figures/Arepo_flowchart_main_loop_RD_FV_functions_20260915.drawio` and same-name
PNG, also delivered to the thesis Arepo_document resource directory. Generic
First/Second hydrodynamic stage headings replace begin/end wording, retaining
RD/FV function names and omitting static/ALE dispatch details; all14 numbered
boxes,15 edges, white background and manual gravity edits are preserved.
Original files are untouched. This is a main-loop interface figure; no solver
semantics changed. Latest record: `../local_runs/flowchart_rd_fv_stage_labels_20260915_v1`.

**Thesis insertion / pending table (2026-09-15, log3 §55):** the user finalised
`Arepo_flowchart_main_loop_RD_FV_functions.pdf` in the thesis Arepo_document
resource directory and explicitly authorised Section 4.1 edits. Synced the
thesis GitHub main (the documented Overleaf sync route) from0a27901 to162f9fc,
preserving the original141-line local Gauss addition and the incoming chapter
introduction without conflicts. The exact user PDF is now in
`/Users/zhenyuwu/Desktop/MyThesis/Zhenyu-PhDThesis/zhenyu_thesis/chapter4/figures/`;
the Section4.1 figure/reference compiles as Figure4.1 on printed page140.
Full232-page XeLaTeX build and page138–141 visual checks pass; function labels
are small at text width, with vector content retained. Archive and three-page
review PDF: `../local_runs/thesis_flowchart_20260915_v1/`.
The comparison draft `RD_FV_CHAPTER4_1_COMPARISON_DRAFT_20260915.md` was
revised in log3 §56 to an English property table: representation, conservation,
upwinding, spatial accuracy (reconstruction vs P1+LDA), positivity/oscillation
control (slope limiting vs N), and nonlinear accuracy–robustness balance
(limiting vs B blending). Implementation rows were removed at the user's request.
The user approved the table in log3 §57, adding a computational-elements row
(Voronoi cells / Delaunay triangles). It is now Table4.1 on printed page139.
Section4.1 is “Overview of AREPO-RD”, with 4.1.1 “Implementation of RD in
AREPO” (introduction, table and original Figure4.1) and 4.1.2 “Increasing
computational efficiency” (brief hierarchy and MPI overviews). The latter
starts on page141; Section4.2 starts on page143. Full235-page compilation
resolves all citations/labels. Current archive and five-page review:
`../local_runs/thesis_section41_table_20260915_v1/`.
No commit/push or solver/Config change; moving-mesh numerical research remains deferred.

**Current thesis figure layout (2026-09-15, log3 §58):** Figure4.1 now uses
`figures/Arepo_flowchart_main_loop_RD_FV_functions_landscape_20260915.drawio`
and its native vector PDF. This new copy reflows the user's final embedded
diagram into compact aligned columns, preserving all14 numbered boxes,
15 edges, labels and previous deletions. Originals remain unchanged; matching
draw.io/PDF copies are in the thesis Arepo_document resource directory, with
the new PDF also in thesis `chapter4/figures/`. A `pdflscape` page in the thesis
places Figure4.1 on printed page140 at roughly twice the previous label size
(function names3.38→6.80pt; descriptions3.95→8.75pt). The unchanged explanatory
paragraph follows the figure. Section4.1.2 still begins on141 and4.2 on143.
Full235-page compilation and visual checks pass. Archive and six-page review:
`../local_runs/thesis_flowchart_landscape_20260915_v1/`;
`chapter4_1_landscape_review.pdf`. Local edits await the normal Overleaf sync.

**Native MPI figure (2026-09-15, log3 §59):** the user is continuing Section4.1
text on Overleaf; do not assume the local narrative is now the latest version.
A separate four-rank illustration uses the real2304-node SWIFT glass and a
short static full-mesh equal-step Gauss3 LDA/F1 run. Native capture exports
all4608 physical triangles, primary-node ranks and actual MPI contribution
buffers. SciPy periodic topology matches every triangle; all owner/index
mappings and649 remote contributions per captured stage match exactly.
Capture on/off states are identical;1/4-rank states differ by at most2.665e-15.
The helper is injected only into an archived source copy; working solver and
thesis are untouched. Report: `RD_MPI_GLASS_OWNERSHIP_20260915.md`.
Figures: `figures/rd_mpi_glass_rank4_overview_20260915` and
`figures/rd_mpi_glass_rank4_boundary_20260915` (PDF/SVG/PNG), also in the
thesis Arepo_document resource subdirectory `RD_MPI_glass_rank4_20260915/`.
Archive: `../local_runs/mpi_glass_ownership_20260915_v1/` with raw geometry,
packet CSVs, audit results, source/build/run provenance and reproduction scripts.
This illustrates minimum-ID ownership for the full local mesh, not majority
voting or a measured MPI speedup. Active-only and moving-mesh scope is unchanged.

**Comparison prose/table completion (2026-09-15, log3 §60):** the local thesis
now includes Zhenyu's commits 6777107 (figure replacement) and b013be7
(comparison draft); HEAD and the cached origin/main both point to b013be7.
At Zhenyu's explicit request, completed only the comparison prose in 4.1.1
and replaced the computational-elements row with fluid-state storage,
control volume and flux/residual evaluation. The common storage row spans
both solver columns: Delaunay vertex / Voronoi generator, `P[i]` and
`SphP[i]`. The centroid distinction and mass-storage detail are explained.
The nine-row table retains spatial reconstruction/LDA, slope limiting/N,
conservation, upwinding and B blending. Existing Springel/Pakmor citations
are used; no bibliography or Chapters 1--3 edit. The user's introduction
and all material after the table are preserved, including the renamed
`Arepo_flowchart_main_loop_RD_FV_functions_landscape.pdf` asset.
Full XeLaTeX build: exit 0, 237 pages; table 141, figure 142, efficiency 143.
Six review pages rendered and inspected. Source backups, hashes, exact patch
and review PDF: `../local_runs/thesis_comparison_completion_20260915_v1/`.
Report: `RD_FV_CHAPTER4_1_COMPARISON_DRAFT_20260915.md`.
Only chapter4.tex changed in the thesis; local edits await normal sync.
No pull/commit/push, solver or Config change.

**MPI figures inserted (2026-09-15, log3 §61):** at Zhenyu's request,
created compact thesis copies of the two audited glass figures. The overview
omits its main heading and bottom total-count line. The detail omits its
heading, subtitle, complete right-hand (b) explanation panel and all footer
prose, retaining the mesh, A/B triangle labels, node annotations and Rank 0--3
legend. The original figures and native geometry are preserved. Reproduce
with `tests/rd/plot_mpi_mesh.py ARCHIVE --thesis --output-dir NEW_DIR`.
The new PDF/SVG/PNG names end `_thesis_20260915`, under `dev_log/figures/`
and the thesis Arepo_document `RD_MPI_glass_rank4_20260915/` resource folder.
Two PDFs are inserted in Chapter 4.1.2, with English captions and a short
MPI ownership/routing explanation. Figure 4.2 is landscape on page 145;
Figure 4.3 is portrait on page 146. All earlier thesis text is preserved,
including §60's comparison completion. Full XeLaTeX build: exit 0, 239 pages;
four-page review covers 143--146. Archive:
`../local_runs/thesis_mpi_figures_20260915_v1/`.
No native simulation rerun, solver or default Config change; no commit/push.

**Current thesis GitHub state (2026-09-16, log3 §64):** fetched the user's
Overleaf comparison revision 5a35005 and used it as the source of truth.
Preserved its table verbatim and its shortened prose, adding original method
and project references, the limited B-blending/slope-limiting analogy, and
the P1-triangle versus median-dual-area distinction. Kept -ization spelling;
Zhenyu prefers this British English variant, so do not convert it to -isation.
Two requested project author fields in the shared bibliography were corrected;
no Chapters 1--3 prose was edited. Included §61's two MPI PDFs and 50 lines
of discussion/captions. Full XeLaTeX build: 238 pages, all references resolved;
review of printed 138--145 and affected bibliography entries passed.
Committed and pushed thesis main as e26d5ab429e5f31355d39cf7fd9ebfd9bb63e2d0;
GitHub main independently verified. No tracked/staged thesis edits remain;
old untracked build/editor files are preserved. Original local MPI changes
remain backed up in stash 44b646cf and the archive below, already integrated.
Archive: `../local_runs/thesis_sync_citations_20260916_v1/`, final review
`output/pdf/chapter4_1_synced_review.pdf`. Overleaf itself was not operated.
The standalone hierarchy schematic below has still not been inserted.

**Current hierarchy schematic (2026-09-16, log3 §63):** revised §62's figure
at Zhenyu's request. Nodes are now A--E; A/B/C=4dt (blue), D=2dt (teal),
E=dt (orange). Every node retains its own timebin colour in every panel;
an outer ring separately indicates timebin synchronization. Triangle steps
are derived from the minimum of their three nodal steps. At t=dt, T3(CDE)
distributes to unsynchronized C/D as well as E. Rings do not encode stage-live:
the static whole-star criterion freezes B/C/D, including D when synchronized
at t=2dt. Geometry and schedule are unchanged and checked against §62.
Latest PDF/SVG/PNG: `figures/rd_hierarchical_timestep_schematic_20260916`;
same builder path as below. Archive with caption, schedule and original script:
`../local_runs/hierarchical_timestep_schematic_20260916_v1/`.
Seven resources copied to Arepo_document/RD_hierarchical_timestep_20260916.
PDF rendered and inspected. Old figures, thesis and solver remain unchanged;
no thesis insertion, native rerun, commit or push.

**Previous hierarchy schematic (2026-09-15, log3 §62):** Zhenyu requested
an AREPO-Figure-17-style illustration with fewer elements. A new static
schematic uses 5 vertices, 3 actual Delaunay triangles and four interval
openings at 0, dt, 2dt and 3dt. Node periods J/K/L=4dt, M=2dt, N=dt imply
triangle periods 4dt, 2dt and dt. Shading identifies triangles starting an
interval; arrows distribute to all vertices, including hollow unsynchronized
ones. Filled nodes encode timebin synchronization, not RK stage-live status.
Positions and bins remain fixed; two RK stages and moving flips are omitted.
PDF/SVG/PNG: `figures/rd_hierarchical_timestep_schematic_20260915`.
Builder: `figures/build_rd_hierarchical_timestep_schematic.py`; checks confirm
Delaunay connectivity and all due sets. The final PDF was rendered/inspected.
Archive: `../local_runs/hierarchical_timestep_schematic_20260915_v1/`, with
schedule JSON, caption, source/output hashes and notes. New resource copies
are in Arepo_document/RD_hierarchical_timestep_20260915. The old moving-mesh
timeline, thesis Chapter 4 and solver are untouched; this figure is a review
draft and is not inserted into the thesis. No native run, commit or push.

## Scope and data policy

- The immediate goal is to compile AREPO-RD natively and rerun inexpensive 2-D
  tests locally while the Cuillin connection is unreliable.
- Old debug campaigns, repeated snapshots, restart files, build artifacts and
  Slurm logs do not need to be copied. Initial conditions should be regenerated
  locally when practical.
- `/Users/zhenyuwu/Hydro_data_analysis` currently contains the analysis code and
  only a small subset of Enzo data. Empty `Data_*` directories are expected and
  are not evidence of an incomplete local environment.
- Cluster binaries are Linux x86-64 binaries and must not be used on this Mac.
  Every local executable must be rebuilt from source.
- Local results are for smoke tests, regression tests and small 2-D comparisons.
  Large formal campaigns may still be run on the cluster when it is available.

## Local path map

| Purpose | Local path |
| --- | --- |
| AREPO-RD workspace | `/Users/zhenyuwu/arepo_rd` |
| AREPO-RD Git repository | `/Users/zhenyuwu/arepo_rd/arepo` |
| Hydro analysis and selected data | `/Users/zhenyuwu/Hydro_data_analysis` |
| Development AREPO reference | `/Users/zhenyuwu/arepo-dev` |
| SWIFT reference | `/Users/zhenyuwu/SWIFT` |
| GIZMO reference | `/Users/zhenyuwu/gizmo-tmox` |
| Enzo reference | `/Users/zhenyuwu/enzo-dev` |
| Thesis repository | `/Users/zhenyuwu/Desktop/MyThesis/Zhenyu-PhDThesis` |
| Thesis resources | `/Users/zhenyuwu/Desktop/MyThesis/useful_resources` |

The old cluster roots `/home/zwu/...` are not valid local paths. In particular,
the local Enzo repository is named `enzo-dev`, not `enzo`.

## Source and documentation state

At the time this file was created:

- AREPO-RD branch: `develop_pureC_RD`.
- Commit: `6a92cd671366bfffd6040d33c1b6b6acb66831bf` (`rd: add ALE
  hierarchy and topology diagnostics`, committed 2026-08-29).
- The AREPO-RD working tree was clean and matched
  `origin/develop_pureC_RD`.
- `context.md` and `arepo/dev_log/context.md` are identical.
- Volume 1, `arepo/dev_log/RD_DEVELOPMENT_LOG.md`, is closed and remains the
  archive for the static-mesh phase.
- Volume 2, `arepo/dev_log/RD_DEVELOPMENT_LOG_2.md`, is the moving-mesh log but
  the local copy currently ends at section 73 (2026-08-25).
- Volume 3, `arepo/dev_log/RD_DEVELOPMENT_LOG_3_localMac.md`, records work
  performed on this Mac. Its exact chronological handover from volume 2 will
  be confirmed after the complete Cuillin copy of volume 2 is checked.
- `Aug26_update_bundle/Aug26_update.md` summarises later hierarchy work and
  refers to log sections through section 83. Those sections are not present in
  any currently available local Git ref. Treat the August 26 update as a
  necessary supplementary handoff until sections 74--83 can be recovered from
  Cuillin or another backup.

The setup-era handoff (superseded by current log3 audits) said that one-rank moving-mesh N hierarchy had passed
the existing equal-bin, two-bin, stationary-mesh, known-flip and KH gates for
both the Arpaia and Campoli temporal-mass forms. Arpaia remains the intended
Chapter 4/production form; Campoli is its endpoint-mass sibling and control.
Topology repair remains diagnostic rather than the production default. The
next scientific engineering target is moving-mesh MPI and rank-boundary
conservation, followed by hierarchical LDA/F1 after the N/MPI path is stable.

## Local machine and compiler stack

- Hardware: Apple M4 MacBook Pro, 10 CPU cores, 16 GB memory.
- Architecture: `arm64`.
- Operating system at setup: macOS 26.6.2.
- Apple Clang: 16.0.0.
- GNU Make: 3.81.
- Homebrew prefix: `/opt/homebrew`.
- Python environments are managed separately; do not copy a cluster Conda or
  virtual environment.

Homebrew libraries detected at setup:

| Dependency | Local version/backend |
| --- | --- |
| Open MPI | 5.0.7 |
| HDF5 | 1.14.6, parallel HDF5 enabled |
| GSL | 2.8 |
| GMP | 6.3.0 |
| FFTW | 3.3.10 |
| hwloc | 2.11.2 |
| BLAS/LAPACK/LAPACKE | OpenBLAS 0.3.29 |
| Autoconf | 2.73 |
| Automake | 1.18.1 |
| GNU libtool | 2.6.2 (`glibtool` on macOS) |

OpenBLAS supplies both `/opt/homebrew/opt/openblas/include/lapacke.h` and the
`LAPACKE_dgelsd` symbol required by the RD linear solves. Intel MKL is not the
native backend on Apple Silicon. A combined MPI/HDF5/GSL/FFTW/LAPACKE compile
and link smoke test passed when this file was created.

The local numerical stack differs from the Cuillin formal-build stack:

| Local Mac | Cuillin formal builds |
| --- | --- |
| Apple ARM64 | Linux x86-64 |
| Apple Clang | GCC |
| Open MPI 5 | Open MPI 4.1 |
| HDF5 1.14 | HDF5 1.10 |
| OpenBLAS/LAPACKE | Intel MKL |

Therefore compare conservation, diagnostic counters and error norms using
explicit tolerances. Do not require bitwise equality between local and cluster
binaries, especially on pseudo-inverse/LAPACK paths.

## AREPO machine configuration

`arepo/Makefile.systype` is a local ignored file selecting:

```make
SYSTYPE="LocalMac"
```

The tracked `LocalMac` block in `arepo/Makefile` uses `/opt/homebrew` and links
the RD LAPACKE calls through OpenBLAS. `Darwin` remains the legacy MacPorts
configuration. The former Intel-Homebrew `MacBookPro` block has been replaced
because that machine is no longer used.

On 2026-08-31 a complete direct build with
`examples/yee_2d/Config_RD.sh` succeeded in `build/local-yee-rd`. The output
was a native arm64 Mach-O executable linked to Homebrew Open MPI, parallel
HDF5, GSL, GMP and OpenBLAS. The build emitted existing source warnings and a
harmless duplicate `-lmpi` linker warning, but no missing-header, undefined-
symbol or unresolved-library error.

## Python analysis environment

The default Python installation does not currently contain the numerical
analysis packages. The existing environment
`/Users/zhenyuwu/miniconda3/envs/21cmfast` contains NumPy, SciPy, h5py,
Matplotlib, yt, mpi4py and pytest. It is the selected temporary local baseline.

A dedicated environment is preferable for reproducibility. A minimal local
environment needs NumPy, SciPy, h5py, Matplotlib and pytest. Add yt and Astropy
only for analyses that use them. Record the final package set after the first
validated simulation.

The following algebraic tests passed under the existing `21cmfast`
environment on 2026-08-31:

```text
tests/rd/test_lda_f1_rank_deficiency.py
tests/rd/test_n_frame_covariance.py
tests/rd/test_ale_shear_eigenvalue_floor.py
```

## Local build and run policy

Slurm files (`*.sbatch`) are not used locally. `build_case.sh` and
`run_case.sh` preserve valuable artifact/provenance behaviour, but they still
contain Linux-specific `flock`, `ldd` and GNU `readlink` assumptions. They are
optional for the first local smoke test and should not be used until made
portable.

The laptop can run several independent cases concurrently without Slurm, but
there is no scheduler to prevent oversubscription or output collisions. Every
Config must have a distinct `BUILD_DIR` and `EXEC`, and every run must have a
distinct working directory and `OutputDir`. Never run concurrent builds in the
same build directory or concurrent simulations in the same output directory.
On this 10-core/16-GB laptop, begin with no more than 6--8 total MPI ranks and
reduce that limit for larger meshes after measuring memory use. Set
both `OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1` for MPI and singleton
runs so that each rank does not create its own pool of BLAS threads.

**Verified 2026-09-11:** the Homebrew OpenBLAS 0.3.29 on this machine reports
`openblas_get_parallel()=2` (OpenMP). `OPENBLAS_NUM_THREADS=1` alone still
reports 10 BLAS threads; adding `OMP_NUM_THREADS=1` reports one. Sampling the
96² Sod run found substantial time in OpenMP barriers inside the tiny
`dgetrs` solves. Preserve both settings in run provenance; the earlier local
campaigns that recorded only the OpenBLAS variable did not enforce one thread.

Routine production and comparison runs should write only 3--5 snapshots in
total, normally including the initial and final states. Increase the output
cadence only for a declared time-evolution diagnostic, instability onset,
failure localization or other analysis that genuinely needs intermediate
states. This keeps local and cluster archives compact and avoids copying
redundant debug data.

For the initial direct build, work inside the AREPO repository and keep build
outputs out of the source tree where possible:

```bash
cd /Users/zhenyuwu/arepo_rd/arepo

make \
  CONFIG=examples/yee_2d/Config_RD.sh \
  BUILD_DIR=build/local-yee-rd \
  EXEC=build/local-yee-rd/Arepo \
  -j4
```

Inspect the executable with:

```bash
file build/local-yee-rd/Arepo
otool -L build/local-yee-rd/Arepo
```

The output must be an arm64 Mach-O binary linked to the `/opt/homebrew`
Open MPI, HDF5, GSL and OpenBLAS libraries. The repository-root `Arepo` and a
stale `build/arepoconfig.h` must not be used as evidence of which Config built
an executable.

## SWIFT and GIZMO Chapter 3 support

The local SWIFT repository has a reproducible Apple-Silicon build entry point:

```bash
cd /Users/zhenyuwu/SWIFT
./build_localmac_2d.sh
```

It creates `build-localmac/swift` and `build-localmac/swift_mpi` as native
arm64 binaries. This is deliberately a 2-D SPHENIX hydro-test build using MPI,
parallel HDF5 and `--disable-vec`; the latter is required because this SWIFT
version's handwritten vector abstraction is not implemented for Apple ARM64.
FFTW, GSL, METIS, NUMA and special allocators are disabled because the current
Gresho comparison is hydro-only. A separate build directory and configuration
must be used if later work needs 3-D or gravity.

The GIZMO repository now provides `SYSTYPE=LocalMac`, using Homebrew libraries
under `/opt/homebrew`. Its existing build wrapper is path-portable and defaults
to the MFV Gresho configuration:

```bash
cd /Users/zhenyuwu/gizmo-tmox
./build_gizmo.sh
```

`Makefile.systype` continues to select `cuillin` by default so the tracked
cluster workflow is not silently changed; `build_gizmo.sh` passes `LocalMac`
explicitly. The Gresho IC generator accepts `--glass` and `--output`, avoiding
the former `/home/zwu` dependency.

Official SWIFT `glassPlane_48.hdf5` and `glassPlane_128.hdf5` files are present
under `SWIFT/examples/HydroTests/GreshoVortex_2D`. They are shared inputs for
the SWIFT and GIZMO Gresho generators.

The current SWIFT release reports that `resolution_eta=1.2348` in its compiled
2-D SPHENIX mode corresponds to approximately 15.14 neighbours, despite the
example YAML comment stating 48. The Cuillin thesis comparison used a much
larger effective-neighbour case. Recover or re-derive the exact dimensionality,
kernel and `resolution_eta` before starting the formal comparison; do not label
the stock local run as the old `N_ngb~400` case.

The checked-in GIZMO MFV Config does not enable `DEVELOPER_MODE`. Consequently
the parameter reader ignores the optional `CourantFac`, `ErrTolIntAccuracy`,
`MaxRMSDisplacementFac` and SPH-only viscosity/conductivity entries in
`gresho48.params`; GIZMO uses its compiled defaults instead. This matches the
current Config/parameter pairing but must be documented or deliberately
changed before the thesis production run.

For direct local execution, run from the directory against which relative IC
and `OutputDir` paths in the parameter file are resolved. Begin with one MPI
rank in a normal Terminal, then repeat with two ranks. MPI launch tests from a
sandboxed agent process may fail because local socket binding is denied; that
does not by itself indicate a broken Open MPI installation.

## Initial local verification sequence

1. Run the three pure-Python RD algebraic tests.
2. Generate a small Yee IC locally rather than copying campaign output.
3. Build and complete a static N smoke test on one rank.
4. Build and complete a static LDA smoke test on one rank.
5. Run the same small case on two ranks and compare by ParticleID.
6. Run moving-mesh equal-step N.
7. Check the equal-bin degeneration of moving hierarchical N.
8. Run the small moving two-bin N gate.

For every binary record the Git commit, Config file, generated
`arepoconfig.h`, compiler version and `otool -L` result. For every run retain
the parameter file, stdout/stderr log and final diagnostic summary. Large
intermediate snapshots and restart files may be deleted after the test has
been accepted.

Minimum acceptance criteria are:

- all three RD algebraic tests pass;
- the executable is native arm64 and has no unresolved dynamic libraries;
- a small 2-D run finishes and writes readable HDF5 output;
- density and pressure remain positive and no element inversion is reported;
- conservation and DGCL diagnostics meet their established gates;
- equal-bin hierarchical execution degenerates to the equal-step result;
- one-rank and two-rank results agree by ParticleID within the established
  cross-platform tolerance.

### First native run, 2026-08-31

A short static N+RK2 Yee test was generated locally at 16 cells per dimension
(259 particles) and evolved to `t=0.02`. The runtime directories are outside
the Git repository:

```text
/Users/zhenyuwu/arepo_rd/local_runs/yee_static_n_smoke
/Users/zhenyuwu/arepo_rd/local_runs/yee_static_n_smoke_np2
```

Both the singleton and 2-rank runs completed, wrote readable HDF5 snapshots and
kept density and pressure positive. The maximum element conservation defect
was approximately `2e-15`. Comparison of the final snapshots after sorting by
ParticleID gave maximum absolute 1-rank/2-rank differences of `2.22e-16` in
velocity, `6.66e-16` in density, `8.88e-16` in pressure and `1.78e-15` in
internal energy. Coordinates and timestep bins were bitwise identical. This
establishes the initial local MPI and rank-invariance smoke gate.

The corresponding static LDA+GL/F1 RK2 case was then run in
`/Users/zhenyuwu/arepo_rd/local_runs/yee_static_lda_rk2_smoke` with the same
IC and end time. It completed on one rank with 259 finite particles; the final
minimum density and pressure were approximately `0.49366` and `0.37220`.
The maximum reported element conservation defect was `4.16e-17` (relative
`4.45e-16`), and `f1_lumped=0` at both steps. This passes the first static
LDA+GL/F1 smoke gate; moving-mesh validation remains deliberately later in the
sequence.

## Known follow-up work

- Recover or reconstruct moving-mesh log sections 74--83.
- Create and freeze a dedicated `arepo-local` Python environment.
- Decide whether to make `build_case.sh` and `run_case.sh` portable. This is
  useful for provenance but is not required to prove that direct local builds
  and small tests work.
- After the N path is stable locally, validate moving MPI before attempting
  hierarchical LDA/F1.

## Sod comparison conventions (user confirmed 2026-09-11)

- Use relaxed **glass IC** as the primary Sod comparison mesh. A jittered
  Cartesian lattice is a separate diagnostic, not a glass.
- Label the initial effective resolution of one shock tube as the main N_x.
  For the current unit-square periodic box, the comparison interval has
  length0.5, so full96² is actualNx48 and full128² is actualNx≈64. On glass use
  h=sqrt(A_box/N_total) and Nx=L_tube/h; there are no literal columns.
- Preserve full-box counts and old directory names as provenance, and state
  both counts in figures. Morton Figure7 uses first-order LDA/N, not GL/F1 RK2.
- See log3 section24 for matched glass controls isolating GL/F1 undershoot and
  contour-residual scatter even with sigma=0 and no flips. Do not attribute
  the previous static/moving difference entirely to movement or repair.

**Current priority (2026-09-12, log3 §§28–29):** pause new CR/basis-repair extensions
and recover the physical baseline first. Keep lumped LDA Heun, standard GL/F1,
and F1 rate-consistent Heun distinct; the latter was not rejected for failing
time order. Separate fixed-h temporal tests, smooth advected spatial tests,
and all-node glass Sod shock quality. See `colombo_re_spike/heun_baseline_history.md`.

The matched 48/96/192 static glass advected-Yee campaign is now complete:
lumped Heun gives density h-orders .902/1.001 despite time p≈2; standard
GL/F1 gives1.879/1.737 with fixed-h time p≈1; F1 rate-Heun gives1.881/1.741
with time p≈2. Halving the spatial-test dt changes density L1 by less than1%
at48/96. Rate-Heun retains the strong glass Sod undershoot (minvx=-.762 versus
-.777 for standard GL/F1). No default was changed, and this is not a proof of
asymptotic order2 on arbitrary glass; the older mass-order note records the
384 glass degradation. Full results: `colombo_re_spike/lda_baseline_convergence.md`.

The moving counterpart is complete (45 native runs, source `11d8abc`):
48/96/192 glass Yee density h-orders are .792/.886 for ALE lumped temporal
RK2, 1.816/1.763 for standard GL/F1, and 1.832/1.777 for a direct ALE
four-pass diagnostic. The last is **not a validated moving rate-Heun**:
its static proof does not transfer through the existing frozen ALE slab.
A derived endpoint defect, independent contour/algebra checks, and no-flip
Campoli controls demonstrate an extra conservation error. Moving Sod at
initial effective Nx≈64 gives relative mass drift 8.59e-5 for this diagnostic
versus 1.19e-9 for standard GL/F1. Do not promote it as a moving alternative.
Lumped Sod is smoother but more diffuse; GL/F1 retains severe vx scatter
(range −.672 to1.352), also with element frame. New frame Sod reproduces
the previous archive exactly. Roe zero-motion and deforming uniform-flow
gates pass; the earlier zero-motion **contour shock** problem remains open.
Main Yee dt halving changes density L1 by <.7%; moving matched-ID time
differences are not formal fixed-grid time orders. Only a protected lumped
diagnostic guard was extended; no default, CR/hierarchy, thesis or log1/log2
change. Full report: `colombo_re_spike/lda_moving_baseline.md`; data and
PNG/PDF figures: `local_runs/lda_moving_baseline_glass_20260911` under the
workspace root. Result/source commits and SHA256 provenance are archived.

**Latest targeted fix (log3 §28):** the user prioritised the large Sod
shock-plateau scatter at x_tube=.7–.8, accepting a static-like negative-vx
trough. Implemented the Gauss-on-P1-U physical-flux quadrature proposed in
log2 §36.4, retaining GL/F1, mesh transport and basis repair. Eleven new
native runs pass. At effective initial Nx≈64, moving plateau vx standard
deviation in [.70,.76] falls from .08256 to .02273 (Gauss3) / .02244 (Gauss5),
versus static Roe .02239; maxvx falls1.3655→1.0510. Density L1 changes
by only+.13%. Zero-motion contour scatter also shrinks substantially.
Moving mass drift remains≈1.5e-9, not the earlier four-pass defect. Yee48/96
density/velocity h-orders are1.874/1.763; no lumped-like order degradation.
Use `RD_ALE_CONTOUR_GAUSS=3` (or5 for integration accuracy control), a
guarded equal-step LDA option; default builds unchanged. This is a promising
physical baseline candidate, not validation for all flows or hierarchy.
Initial Gauss3 artifacts use source559f8a4 and its historical flag name;
Gauss5 usesa4d5a76. Full report: `colombo_re_spike/sod_contour_quadrature.md`.
Archive: workspace `local_runs/sod_contour_gauss3_20260912`.


**Latest KH/cost follow-up (log3 §29):** matched glass48² moving smooth KH
(tanh width .025, historical physical profile) now runs to t=10 with pure
LDA Gauss3 and Gauss5, as does current scalar B; old nodal LDA fails at
t=.444717 with negative mass. Mass/energy drift stays O(2e-8). Late Gauss
morphology, kinetic energy and entropy-proxy excursions differ from B and
between G3/G5; completion is not a long-time accuracy/positivity proof.
All four sharp-interface cases instead stop at the first-step A2 assertion,
before flips. Captured rank3 Sminus cannot represent the full contour Phi:
80-digit least squares and forced SVD confirm a genuine outside-range
residual (1.263e-11,129x A2 tolerance), also present with old nodal contour.
Keep guards intact; conservative spatial null-space completion is a separate
unresolved operator issue. Do not confuse it with the earlier F1 time-mass
problem or describe these sharp failures as late physical KH instability.
Eighteen serial,512-step timings measure G3/G5 CPU overhead about2.9%/4.0%
in early smooth KH (current diagnostic build; not a release/MPI prediction).
Report: `colombo_re_spike/kh_gauss_and_cost.md`; archive under workspace
`local_runs/kh_gauss_20260912`. Main source59b2161, capture source3d6eea9.


**Mathematical clarification and literature (log3 §30):** see
`colombo_re_spike/gauss_p1_ale_math_and_kh_literature.md` for the full ALE/P1
chain and primary-source comparisons. Mean-sigma contour spatial residual
must not be confused with the actual moving-control-volume flux: the latter
has a geometric volume term when related to the former. Gauss integrates
F(U_h) instead of I_hF, fully compatible with P1 but not a positivity proof.
SWIFT/SPHENIX reports highly mixed late KH; AREPO regularization studies also
show that mesh noise can create false secondary structures. Current48² KH
resolves each seeded wavelength with only24 initial spacings. Late disorder
alone neither invalidates nor validates our solution; no new native runs in
this literature/math follow-up.


**Latest old-form control / Chapter4 update (log3 §31):** explicit user
request added Gauss-versus-nodal/split equations to local Chapter4 math draft
(section label ALE_RD_Gauss_physical_flux), with isolated compile/visual QA;
no Overleaf sync or changes to Chapters1–3. Current-source legacy Roe-Uhat/U
split was re-enabled by config only and tested in lab/frame. Both smoothKH
runs fail at t=.800476 (same negative-mass particle), versus nodal.444717
and Gauss3/5 normal completion10. Both sharp controls first-step A2 fail.
Sod succeeds: old split plateau vx std≈.0230, almost Gauss3 .02273, versus
nodal .08256. Hence Gauss is not the only Sod fix; old split remains a useful
control but does not replace Gauss on smoothKH survival. Full report
`colombo_re_spike/legacy_split_kh_sod.md`; archive `local_runs/legacy_split_20260912`.
Eight new native starts, four normal/four diagnosed failures, seven reused
references; no C/default/hierarchy edits. Build sourcee33aea3.


**Legacy+Gauss identity (log3 §32):** Gauss on linear Roe Z already equals the
old physical residual (quadratic flux, Gauss2 exact). Adding the full edge
flux difference F(P1-U)-F(U(P1-Z)) to old split recovers existing Gauss-U,
not a distinct scheme. Include all4 components and consistent frame handling;
current nodal-to-Gauss helper cannot be pasted onto old split.200 random
triangle algebra checks pass≈1e-14; no new native fluid tests or thesis edit.
See `colombo_re_spike/legacy_split_gauss_identity.md`.


**Static Gauss hierarchy/MPI (log3 §33, 2026-09-12–13):** narrow guard
extension permits static full-mesh LDA/F1 contour Gauss3/5 with existing
hierarchy and MPI. Build source255046f;27 native glass uniform/Yee/Sod runs
all pass. Ranks1/2/4 agree by ID to1.36e-14; equal-bin hierarchy degenerates
to internal RK at1.29e-14. Final relative mass/energy drift≤1.45e-16/6.47e-16;
Sod natural CFL hierarchy reaches three bins, completes t=.08, actualNx≈64.
No new Gauss communication fields, limiter or loosened assertions.
Important accuracy qualification: both standard equal-step F1 and mixed-bin
F1 self-converge at fixed-h time order≈1 (equal-step limitation already known).
Frozen mask P changes the leading rate from v+(I-S^-1 M)v to
v+(I-S^-1 M)Pv; measured hierarchy-minus-equal difference plateaus as dt shrinks.
Thus this is a conservative parallel hierarchy baseline, not an equivalent
multirate realization of equal-step F1. Short t=.125 Yee48/96/192 errors fall
but show no stable second-order h convergence; hierarchy velocity error is
larger. Sod negative-vx trough is smaller in these hierarchy controls.
Moving LDA hierarchy/MPI, active-only reconstruction and domain migration
remain outside this validation; existing moving guards remain intact.
Report `colombo_re_spike/static_gauss_hierarchy_mpi.md`; reproducible Config
`examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_HIER.sh`; archive workspace
`local_runs/static_gauss_hierarchy_mpi_20260912`. No thesis/default change.

**Sod coordinate/clock clarification (log3 §34):** plotted xi=2(x-.25)
maps xi=.8 to raw x=.65, outside forced left-half refinement. Hierarchy
still applies globally. In the330 final vertices at xi∈[.78,.82), forced and
natural runs have131/129 reconstructed frozen vertices; their bins20/21 give
2–4 times the equal-run bin19 step. Frozen-F1 therefore acts near the shock
too. Independent periodic-star counts match native diagnostics; no new runs.
The unit-length tube also needs tau=2t, so current t=.08 corresponds to.16.
Morton2023 uses gamma5/3, CFL.4, first-order LDA/N and row-offset Cartesian,
not current gamma1.4/CFL.08/glass/F1. Paper §5.1.1/Fig7 do not specify final
time; tau≈.2 inferred from its wave positions is not an original-data check.
Current rescaling/actualNx is valid but does not make it a Morton reproduction.
Audit/figure under workspace local_runs/sod_coordinates_20260913.

**Moving Euler hierarchy retry (log3 §35, 2026-09-13):** new independent
Python P1/Gauss3/LDA/F1 experiment closes full old vertex stars and uses
actual triangle birth/last-integrated times before same-time basis repair.
Critical addition: a predictor is live only on complete stars whose actual
integration starts agree; equal bins alone fail after event truncation.
Conservative Campoli-endpoint two-stage deposits and zero-sum F1 action
then close Euler extensive conservation through real periodic Delaunay
changes. This is a new candidate, not an enabled native AREPO solver.
22 positive controls pass, three deliberately wrong rules fail (dying-only
geometric coverage; bin-live/all-closed-live conservation7.65e-7/2.47e-6).
Moving glass Sod t=.08, effectiveNx24:384 changed-cavity events, conservation
5.53e-15; moving glass KH t=.5:2092 events,4.44e-15, admissible checked
states. Uniform depth1024 error2.38e-14; seven populated bins1–64 also pass.
All remaps use theta1, i.e. original basis high, not CR low diffusion.
Static two-step native reference agrees2.665e-15; native binary reused from
source255046f, no production C/build/default changes. All failed exploratory
and setup attempts are retained separately. The source/analysis/case runners
are under tests/rd; report `colombo_re_spike/euler_flip_closure.md`, archive
workspace `local_runs/euler_flip_closure_20260913`.
Still missing: actual native triangle history and forced-refresh lifecycle,
changing CFL bins, moving MPI/migration/restart, geometric-step policy,
long-time stability and accuracy convergence. Frozen-F1 leading-operator
problem (§33) remains. Chapter4 static hierarchy/MPI → equal-step moving
extension is still recommended; this candidate can support an ongoing-work
subsection, not a completed moving-hierarchy claim. Thesis untouched.

**Static baseline review (log3 §36, 2026-09-13):** develop_pureC_RD now has
the selected Gauss helper/static LDA contour permissions; no CR, moving
Euler interval-closure or topology-refresh solver code was merged. Historical
log/report continuity was retained; old experimental scripts remain at their
referenced test-branch commits. Initial source484512a failed option registration
before evolution; corrected build source943f7ae passes standard make for5configs.
Two explicit examples/yee_2d configs: Config_RD_RK2_LDA_GAUSS3_EQUAL.sh and
Config_RD_RK2_LDA_GAUSS3_HIER.sh. Default Config unchanged.
26 new native runs all complete:12 replay gates exactly match archived test
branch U by ID;8 static KH (smooth t2, sharp t.05, equal/natural,1/4ranks)
pass, including actual mixed bins;6 Gauss Yee t1 h cases. Max conservation
2.06e-14; max rank-state difference3.96e-14; equal-bin degeneration1.29e-14.
Static sharp KH does not reproduce the moving sharp first-step A2 failure.
Gauss Yee t1 rho slopes equal1.873/1.710, hierarchy1.585/1.658; at192²,
hierarchy rho/velocity errors are2.22/1.75x equal. h/dt refined together;
no strict asymptotic second-order claim. make check_rd passes.
Persistent limits: GL/F1 fixed-h time1; frozen hierarchy changes leading
operator; shock undershoot/no general positivity; mid-stage hierarchy
restart rejected by existing guards; no active-only Gauss/migration/large-rank
or cosmological validation. Qualified Chapter4 experimental baseline only.
Chinese summary/table: RD_STATIC_BASELINE_CHAPTER4.md. Native archive:
workspace local_runs/static_baseline_review_20260913/native; source943f7ae,
tests/rd/review_static_baseline.py and Yee t1 PNG/PDF. Thesis untouched.
