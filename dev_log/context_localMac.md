# AREPO-RD local macOS context

Agent entry point: [AGENTS.md](../AGENTS.md). Keep stable working rules there;
this file holds local paths, toolchains and the evolving handoff.

Updated: 2026-10-02

**Chapter3 wording correction (2026-10-02, log3 §210):**
User explicitly wants their original FV–RD sentences preserved; only typeset
math symbols, without unsolicited prose polishing. Restored the two original
paragraphs after §209, retaining its added derivation. Prose paragraphs and
caption now each occupy one source line; displayed equations retain line breaks.
Local three-page compile and visual check pass. Latest exact edit archive:
`../local_runs/thesis_ch3_fvrd_prose_restore_20261002_v1/`.

**Chapter3 static FV–RD introduction completed (2026-10-02, log3 §209):**
Restored the archived pre-ALE material into the user's new FV–RD subsection:
median-dual normals, FV update, flux-to-residual conversion, element sum and
pair fluctuations. Kept the original Deconinck–Ricchiuto figure and caption.
Notation follows Chapter3, with phi_FV^T for the nodal-flux/trapezoid total.
Only this subsection changed; three-page local compile and visual check pass.
ALE material stays in Chapter4 under the stated scope interpretation.
Archive: `../local_runs/thesis_ch3_fvrd_text_20261002_v1/`; uncommitted.

**Chapter3 FV–RD figure inserted (2026-10-02, log3 §208):**
User is introducing concise FV–RD material in Chapter3. Inserted the existing
`geometry_FV_RD_scheme.png` into the new subsection, with caption and the
previously empty cross-reference completed (`fig:RD_FV_geometry`, Figure3.3).
Only this figure insertion and reference changed; local subsection compile
and visual check passed. Uncommitted; normal Overleaf sync remains to follow.

**Chapter4 FV–RD notation and ALE clarification (2026-10-01, log3 §206):**
User-authorized edit of the new HLLC subsection only: pair fluctuations now
use phi and median-dual scaled normals use n_ij, including the figure.
Clarified that the moving-frame flux mapped back to laboratory conserved
variables already includes the negative mesh-advection term in the element
residual; relative wave speeds also affect its distribution. Local Chapter4
and schematic updated, uncommitted. Only the seven relevant pages (164–170)
were recompiled and visually checked; no whole-thesis build or solver run.
Latest preview and reproducible sources:
`../local_runs/thesis_ch4_fvrd_notation_20261001_v1/`.


**Consolidated comments and user position (2026-10-01, log3 §202):**
User accepts the present HLLC FV–RD construction as distinct from N/LDA
multidimensional upwinding, useful for strong shocks, with further moving-mesh
work worth pursuing. Consolidated review, citation scope and remaining limits
are in log3 §202. Previously verified schematic and generator now also live in
`dev_log/figures/riemann_flux_to_rd/` with byte-identical-copy provenance.
No thesis/solver changes, no new simulation or validation claims.


**Riemann-flux RD literature and figure (2026-10-01, log3 §201):**
Verified Deconinck–Ricchiuto2017 §4.1, equations55–59 (older text §3.6.1),
and Abgrall2018 §4.1 support median-dual FV-to-RD rewriting. Hu–Li–Tang2010
explicitly uses HLLC in a cell-centred steady RD-type method; related precedent,
not the same ALE implementation. Original two-panel vector diagram and full
qualification: `RD_RIEMANN_FLUX_RD_LITERATURE_20261001.md`, archive
`../local_runs/riemann_rd_schematic_20261001_v1/`. No thesis/solver changes.


**Independent HLLC-RD review (2026-10-01, log3 §200):**
Recomputed40 archived snapshots/eight cases and reran4000 tests on the frozen
native HLLC header; all pass. Improvement is real (moving peak2.428→2.980,
core.198→.028), but this is a median-dual FV fluctuation split in ALE-RD,
not N/LDA multidimensional upwinding; the branch bypasses K distribution.
Moving budgets remain−.329% mass/+.698% energy (21 hot),−1.606% energy (1 hot).
Do not conflate bin-number means with mass means, HLLC with Roe in1D, or the
whole temporary ledger with isolated flip error. The remaining MMFV gap is
not proved solely due to order. See `RD_HLLC_RD_REVIEW_20261001.md` and
`../local_runs/hllc_rd_review_20261001_v1/`. No thesis/solver edits or new
native hydrodynamic runs. Claude's existing notes retained unchanged.


**Chapter4 high-resolution Sod inserted (2026-10-01, log3 §198):**
User removed Chapter4 comments in e3ef001 and prefers minimal changes; defer
standard AREPO overlays for boosted vortices. Added the existing effective
Nx128 Sod figure (256² full-box nodes, gamma5/3, t=.2) from main_comparison_v3
page1, matching the Nx64 figure from page2. Brief cross-referenced caption;
text now cites high-res sharpening with similar overall behaviour and removes
"for clarity" omission. Only Chapter4.tex plus new figure; uncommitted. Figure
render and diff check pass; native chapter compile lacks master preamble.
Archive: `../local_runs/thesis_ch4_sod_highres_20261001_v1/`.


**Chapter3 nullspace calculation inserted (2026-10-01, log3 §197):**
User approved rank([Sminus|b])=rank(Sminus)<n without a separate compatibility
discussion. Edited only Chapter3 inverse matrix subsection: zero Roe mean velocity,
explicit Sminus*z using L/G, then z=z_rho*e_rho and spectral Kplus*z=0. Diff check
passes; uncommitted. Native chapter compile fails at the first chapter command
without master preamble; no alternate PDF or editor tab. Other thesis text kept.


**Chapter3 zero-velocity nullspace proof (2026-10-01, log3 §196):**
User has revised Chapter3 personally; unchanged Ben 3D implementation does not
need expansion. Discussion only: a half-page proof at zero Roe mean velocity
uses ker(Sminus)=span(e_rho), then spectral splitting gives Kplus_i e_rho=0.
Also state RHS compatibility (b_E=Hbar b_rho) before calling the pseudoinverse
an exact solution; the stated Roe N/LDA RHSs satisfy it. Algebra is already in
`RD_THESIS_42_ZERO_VELOCITY_DERIVATION_20260926.md` §§2–4. No thesis edits.

**Chapter3 scope discussion (2026-10-01, log3 §195):**
User requests discussion only and prefers minimal Chapter3 changes. Proposed
focus: identify personal contributions (C++→C preparation for AREPO, corrected
singular S⁻ solve, own tests/cross-code comparison) and distinguish them from
Ben's work and the2023 paper timeline. Current fixed-mesh RD should not claim
strict discrete Galilean invariance; leave ALE/boost discussion in Chapter4,
with only a short Chapter3 cross-reference if edited later. Boost tests are
numerical evidence, not a complete invariance proof. Thesis now `090740b`, tracked
tree clean; no thesis changes in this turn.


**Comoving equation / Abstract accepted (2026-10-01, log3 §194):**
Corrected extra v in Chapter1 comoving momentum flux and made divergence/dot
products explicit. Abstract Chapter4 now uses the approved concise integration,
moving-mesh tests and future-framework paragraph. User explicitly retains Morton
comparison wording: Chapter2 targets order-of-magnitude heating estimates.
Two-file change only; earlier edits preserved, unstaged/uncommitted. Native
chapter-only compile still lacks the master preamble; no separate PDF created.
Archive: `../local_runs/thesis_comoving_abstract_20261001_v1/`.


**User-confirmed thesis fixes (2026-10-01, log3 §193):**
Applied confirmed Chapter1 formula corrections and Figure1.4 caption; retained
Lambda convention, Chapter2 integral and SHMF/cooling normalization as requested.
Comoving equation, Abstract and Morton prose remain pending discussion. Merged
three duplicate bibliography groups (367→364); updated citation aliases, author
formats, missing publication fields and Wu2026 MNRAS551(2),stag1461. BibTeX and
all344 active citation keys pass; seven tracked files are unstaged/uncommitted.
The native editor cannot compile chapter1.tex alone (undefined chapter without
master preamble). No separate PDF or tab created; full PDF unverified this turn.
Archive: `../local_runs/thesis_confirmed_fixes_20261001_v1/`.


**Thesis front matter–Chapter2 review (2026-10-01, log3 §192):**
Read-only audit of `68399ec`, now equal to origin/main. Body red comments are
cleared; List of Figures xx still repeats three SK comments from Figures4.6–4.8.
Several definite formula typos and a wrong Figure1.4 caption remain. Chapter2
ln/lg SHMF and nH² cooling normalizations require checking against analysis
code before inferring any numerical error. Also review Abstract scope, Morton
comparison qualifications and bibliography entries. Full findings:
`../local_runs/thesis_front_ch2_review_20261001_v1/review.txt`. Isolated246-page
build passed; citations resolve and11 targeted pages were visually checked.
All tracked thesis hashes unchanged; no thesis/solver edits, commit or push.


**Thesis GitHub/Overleaf merge (2026-09-30, log3 §190):**
Merged remote04dcc4a (Sadegh Chapter4/5 comments) with local6e02014/447c9a0
(Chapter1/Abstract and equation punctuation) as68399ec. No conflicts;
comments and local revisions retained,30 untracked files unchanged.
Main is ahead of origin/main by3, tracked working tree clean; no push.
Comments remain for review; no PDF rebuild. Archive:
`../local_runs/thesis_github_merge_20260930_v1/`.


**Chapter1 follow-up wording restored/simplified (2026-09-30, log3 §188):**
Applied the user's precise revisions on top of §185: exact decaying-mode
sentence; original The current Gaussian paragraph with only the requested
phrase changed; shorter rotation and Schaye/Dalla Vecchia statements;
original Chapter2 outline and exact Ben Morton contribution sentence.
Confirmed Abstract line12 already has the new-mechanism wording in its
unstaged diff. Only Chapter1 changed this turn; earlier Abstract/bib edits
remain. Isolated245-page build and6-page visual check pass; references
resolve. Unstaged/uncommitted. Archive:
`../local_runs/thesis_ch1_followup_20260930_v1/`.


**User decision (2026-09-30):** LDA/HLLC blend not mature (scatter mainly
shock-generated; v_t ~2× HLLC, front corrugation 1.6×). The thesis
Sedov should favour the edge-HLLC moving result; the blend stays
experimental (report §4).

**Experimental moving LDA/F1 + edge-HLLC limited blend (2026-09-30, log3 §187):**
New opt-ins `RD_BLEND_LOW_HLLC` and `RD_BLEND_LOCAL_BOUNDS` under
`RD_LDA_RUSANOV_BLEND`. The low order is HLLC plus half-split Gauss3 edge
terms (common Φ_G, nodal cancellation), with ALE a_i/b_i checks and local
ρ/K bounds. Tests pass; the static blend replay is bitwise; the ℓ=0 control
reproduces HLLC to 6e−12.
Sedov 21-point bounds: raw ρmax 3.80, mean peak 2.89, p_core 1.653,
ΔE −.96%. Single point: p_core 1.595, ΔE −6.4%. Velocity scatter is about
3× HLLC.
Positivity-only (no bounds) was resumed after the AREPO CPU limit and
reached t=.05. It overshoots (ρmax 4.8/5.3), shows about 5× HLLC
velocity noise, and has about 500 nodes with K below the initial minimum. Flip/rebase conservation is now the bottleneck.
Archive `../local_runs/sedov_lda_hllc_20260930_v1/`,
[report](RD_SEDOV_LDA_HLLC_BLEND_20260930.md). Uncommitted.

**Codex review addressed (2026-10-09, log3 §224, commit 95a1a26):**
- R1: explicit flip modes plus `tests/rd/flip_campaign_checks.py`.
- R2: CFL ledger enforced (`RD_CFL_LEDGER_LIMIT`), gate `../local_runs/cfl_ledger_gate_20261009_v1` passes.
- R3: Arpaia defect corrected in the report.
- R4: matched-ID metric renamed; analytic-error increase added.

Next: a final-default full freeze (mode 1 + lazy + natural, Sedov to t=.05, N/LDA/B degeneration and controls),
then common-space Yee 48/96/192 with dt control.

**Independent Codex review (2026-10-09, log3 §223):**
Read `RD_FLIP_HIERARCHY_CODEX_REVIEW_20261009.md` alongside Claude's report below.
Reviewed `eacc3f9..9672ad7`; supports the 2D periodic one-rank conservation path.
Four P2 findings: current comparison drivers silently alias mode 0 to mode 1;
frozen-vertex CFL ledger overruns are counted, not enforced; Arpaia's complete
no-flip endpoint defect is `sum (Snew-D)*(Unew-Uold)` (the original report omitted
the initial rebase); matched-ID differences on different coordinates do not
establish Eulerian field convergence. Five frozen archives independently
verified: 156/163 cases complete, seven disclosed LDA-KH failures.
Current-HEAD mode1+lazy+natural confirmation passes uniform/N and Yee/N plus
Sedov/HLLC 1/21-point **only to t=.005**; not a full t=.05 confirmation.
Archive: `../local_runs/codex_flip_review_20261009_v1/`. No solver/thesis changes.
Next: fix experiment definitions/CFL enforcement, then final-default full gates
and spatial convergence controls before extending the scope to 3D.

**Claude handoff — flip element + moving hierarchy (2026-10-09, log3 §§217–222):**
Branch `feature/ale-flip-conservation-hierarchy`. **Review report:**
`RD_FLIP_HIERARCHY_REPORT_20261009.md`, prepared for the Codex review. It covers maths, the code map, all frozen archives,
results, limitations, the review checklist (§9) and the 3D outlook (§10).

All campaigns are complete. Implemented:
- `RD_ALE_FLIP_TRANSFER` (equal step);
- `RD_ALE_INTERVAL_HIERARCHY` (N/LDA/B/HLLC);
- `RD_ALE_LAZY_FLIP`.

The default is `RD_FLIP_HIGH_MODE=1` (receiver-only).

Suggested next steps:
- a confirmation freeze with the final defaults (mode 1 + lazy + natural bins);
- a Python 3D algebra check;
- thesis text suggestions, without editing the thesis.

Resource budget: at most 6–8 concurrent simulations; it was exceeded on 2026-10-09, so that day's timings are not reliable.
Python: 21cmfast env; OMP/BLAS=1. Wait on PIDs, not `pgrep -f`. Do not edit the thesis.

**Chapter4 Sedov figures inserted (2026-10-02, log3 §§212–213):** user moved the
FV-RD derivation to Chapter3 §3.2.5 (`section:FV_RD_schemes`, DR2017 Fig.2 copy)
and kept a short moving-mesh FV-RD paragraph in Chapter4; my §203 subsubsection
is gone. Figures 4.11/4.12 (`fig:ALE_RD_sedov_maps`, `fig:ALE_RD_sedov_profiles`)
added after the Sedov setup; base a376fb1; uncommitted. Open review items
(HLLC "in AREPO" wording, "only difference" vs MMFV, Springel eq. numbers,
closed-hull identity) listed in log3 §213. Figure fonts ~4 pt at \textwidth.

**Chapter4 HLLC FV-RD subsubsection inserted (2026-10-01, log3 §203):**
User-requested. After "Distribution schemes", new unnumbered subsubsection
`section:ALE_RD_HLLC_FVRD` (DR2017 §4.1 as main support; HLLC Toro, waves
LeVeque) plus original Figure 4.6 `chapter4/figures/rd_hllc_fvrd_schematic.pdf`
following DR2017 Fig.2 geometry. Only chapter4.tex + figure; base 5feca22;
uncommitted. Full master builds in scratch, no new overfull/undefined refs.
No Sedov results in thesis yet. Archive
`../local_runs/thesis_ch4_hllc_fvrd_20261001_v1/`.

**HLLC-RD consolidated write-up (2026-10-01, log3 §199):** idea origin,
math (ν_ij=(n_j−n_i)/6 FV-RD split, frame HLLC, positivity/ALE checks),
code map, 10 experiments with archive and figure links, main results
(incl. single-point, N comparison, MMFV/SWIFT faceting, blend verdict:
thesis favours HLLC-RD) in [summary](RD_HLLC_RD_SUMMARY_20261001.md).
Thesis untouched; source uncommitted.

**Edge-HLLC low-order RD implemented and tested (2026-09-30, log3 §186):**
New opt-in `RD_LOW_ORDER_HLLC` (requires `RD_RUSANOV_LOW_ORDER`;
`src/hydro/rd_hllc.h`, two call sites, defines_extra). Median-dual edge HLLC
in the w_T frame, same trapezoidal ALE total, per-vertex stage coefficient,
star-state checks, no floors. 4000 kernel tests plus 5 check_rd pass.
Moving 21-point Sedov t=.05: mean ρ peak 2.98, core ρ .0276, p_core 1.714.
That reaches first-order MMFV (3.10/.0276); Rusanov gave 2.43/.198.
Single-hot-node run completes (peak 3.00). Flag-absent Rusanov replay is
bitwise identical to the archive. Still first order; moving budgets drift
(mass −.33%, energy +.70%/−1.61%) because the connectivity/endpoint terms
are unchanged. Thesis also read, including red-text commits
e4fcd84/beb977d. Archive `../local_runs/sedov_hllc_20260930_v1/`,
[report](RD_SEDOV_HLLC_LOW_ORDER_20260930.md). Uncommitted; defaults and
thesis unchanged. Next: ALE convex-limited LDA correction, then positive
conservative flip remap.

**Chapter1/Abstract comments addressed (2026-09-30, log3 §185):**
User authorized ten specific edits. Thesis base `447c9a0` already commits
the punctuation pass and is ahead of origin/main by1. Changed only Chapter1,
the formal Abstract paragraph on DF heating, and chapter1bib-cosmology.bib.
Emphasized DF heating as a new mechanism affecting PopIII/DCBH formation;
revised decaying/Gaussian wording; removed the missing-satellite aside;
added Hubble1926 and ATLAS3D I/III citations; expanded the surface-density
versus local volume/pressure star-formation discussion using the existing
SchayeDallaVecchia2008 entry. Added the Chapter2 cross-reference and rewrote
the outline to match current Chapters2--5, retaining ongoing-work limits.
All10 addressed comments removed; equations, labels, Lay Summary and other
chapters unchanged. Full isolated246-page build and12-page visual review
pass; references resolve. Changes are unstaged/uncommitted for git diff;
no push or root master.pdf overwrite. Archive:
`../local_runs/thesis_ch1_comments_20260930_v1/`.

**Sedov RD shock literature + first-order MMFV diagnostic (2026-09-30, log3 §184):**
Existing moving RD Sedov is pure first-order Rusanov; LDA/Rusanov and Bmax
are static-only. New diagnostic first-order MMFV (face extrapolation off;
exact and HLLC) on identical ICs: mean ρ peak 3.10/3.07, core ρ .028,
roundoff budgets, versus moving Rusanov RD 2.43/.198 and second-order MMFV
3.30/.030. The main moving-RD deficit is the Rusanov dissipation form
(∝c on density), not missing second order. Proposed, not implemented:
(1) edge median-dual HLLC low order in the w_T frame; (2) ALE port of the
convex-limited LDA correction with local ρ/specific-entropy bounds;
(3) positive conservative remap at flips. Archive
`../local_runs/sedov_mmfv_first_order_20260930_v1/`,
[report](RD_SEDOV_SHOCK_LITERATURE_OPTIMIZATION_20260930.md). No RD solver,
default Config or thesis change; new configs/runner/analysis are untracked.

**Thesis equation punctuation audited (2026-09-30, log3 §183):**
User authorized a whole-thesis pass for SK's missing equation punctuation.
Starting thesis `99df79a` (main/origin-main) already includes the latest
Chapter4 wording and Chapter5. Checked all248 active display blocks;
93 changed across Chapters1--4 and Appendix1, mostly Chapters1--2.
Only punctuation/adjacent whitespace and one continuation `The`→`the`
changed; math, labels, comments and all other tracked files are preserved.
Full isolated245-page XeLaTeX build passes; references/citations resolve,
12 representative pages visually checked. Existing11 overfull locations
remain (two long Chapter1 equations gain2.61109pt from their full stops).
Uncommitted/unpushed; root master.pdf unchanged. Archive and checks:
`../local_runs/thesis_equation_punctuation_20260930_v1/`.

**Chapter4 overview transition simplified (2026-09-30, log3 §182):**
User synced §4.3.3 edits as thesis `12e9451` (main/origin-main). Only the
last §4.3.1 paragraph is now locally modified: introduce the numerical
tests and defer connectivity-conservation/hierarchy development to §4.3.3.
Text/diff checks passed; uncommitted, with no rebuild for this wording edit.

**Chapter4 hierarchy prose simplified (2026-09-30, log3 §181):**
Replaced only the last two §4.3.3 paragraphs with the timing problem caused
by flips and the candidate idea of completing old updates up to the flip,
conservatively transferring the state, then continuing on the new mesh.
Native validation/parallel work remains ongoing; presented moving tests
still use one timestep for all vertices. User has committed red-draft
removal as thesis `beb977d` (ahead1); connectivity and hierarchy edits remain
uncommitted. Text checks passed; no rebuild after this prose-only edit.
Archive: `../local_runs/thesis_hierarchy_prose_20260930_v1/`.

**Chapter4 connectivity prose polished locally (2026-09-30, log3 §180):**
Applied the user's pasted Overleaf wording and agreed edits to §4.3.3 on
thesis `8cfb119`: explain the Delaunay/Voronoi geometric distinction and
nonuniform-field integral change directly, replace the uniform-flow detour,
and omit the separate midpoint/endpoint discussion from this paragraph.
Equations, repair limitations, hierarchy and all other chapters unchanged.
Earlier red-draft removal remains; both edits are uncommitted/unpushed.
Isolated 242-page XeLaTeX build passes with resolved references; printed
pp.169--171 visually checked. Root master.pdf unchanged. Archive:
`../local_runs/thesis_connectivity_polish_20260930_v1/`.

**Chapter4 structure established; red drafts removed (2026-09-29, log3 §176):**
User considers the chapter structure settled; §4.3.2 may gain Sedov/other tests,
while connectivity changes stay concise ongoing work in §4.3.3. On thesis
`8cfb119` (main/origin-main; Lay Summary already synced by user), removed the
431-line red implementation/alternatives block only. Retained body/§4.3.3
unchanged,25 removed labels have no outside references. Full isolated242-page
XeLaTeX build succeeds with resolved references; chapter ending visually checked.
Uncommitted/unpushed; root master.pdf unchanged. Updated AGENTS/context scope;
this does not validate unfinished repairs/hierarchy. Review:
`../../output/pdf/chapter4_clean_review.pdf`; archive:
`../local_runs/thesis_ch4_remove_red_20260929_v1/`.

**Lay Summary lightly polished locally (2026-09-29, log3 §175):** On thesis
main `b6786ed`, revised only the Lay Summary in frontmatter/abstract.tex.
Preserved narrative/voice, corrected grammar, and explained DF/LW/bulk-motion
terms in plainer language. Formal Abstract and all other tracked thesis files
unchanged. Isolated two-page XeLaTeX preview compiled and visually checked;
full thesis PDF not rebuilt. Uncommitted/unpushed; normal Overleaf sync pending.
Review: `../../output/pdf/lay_summary_review.pdf`; archive:
`../local_runs/thesis_lay_summary_polish_20260929_v1/`.

**Thesis local merge completed (2026-09-29, log3 §174):** Fetched GitHub
`origin/main` at `9e428fd` (Lay Summary) and merged with local `c3aa858`
(4.3.3 Ongoing work), producing `b6786ed` on main without conflicts. Both
original commits retained; Chapter4 exactly matches the local commit and
abstract exactly matches the remote. Tracked tree clean; all30 untracked
files and both stashes preserved. Local main ahead2/behind0, not pushed;
Overleaf not operated directly. PDF not rebuilt for this Git-only sync.
Backup/checks: `../local_runs/thesis_merge_20260929_214454/`.

**Thesis 4.3.3 local draft awaiting review (2026-09-29, log3 §§172–173):**
Expanded the edge-flip explanation using old/new P1 basis functions and their
integrated-weight defect at identical coordinates/time. Describes the patch
repair as experimental and disabled in the presented tests. Retains repair
positivity limits, the endpoint-weight defect and actual-interval hierarchy.
No Sedov results. Distinguishes independent Euler conservation evidence from
unfinished native integration and accuracy/positivity/MPI validation. Thesis
base `1bb457f`; earlier velocity-error typo fix preserved. Full isolated build
passes with resolved references; current review covers printed pp.169–171 in
`../../output/pdf/chapter4_3_3_ongoing_work_review.pdf`. Local and unpushed.

**RD B/Bmax sensor transplant completed (2026-09-29, log3 §§170–171):**
The consolidated development record, comparisons and remaining limits are in
[log3 §171](RD_DEVELOPMENT_LOG_3_localMac.md#171-2026-09-29ldarusanov与bbmax改进的总开发记录).
User preferred
methods already used in RD. Added opt-in `RD_LDA_RUSANOV_B_SENSOR=1/2` for
component B/scalar Bmax on the existing static positive LDA/Rusanov branch.
Complete old/new RK residuals are mixed; N is replaced by common-Gauss Rusanov,
with the existing outer coupled positivity guard. This is not RPJ or MOOD.
All10 v2 native runs/50 snapshots pass; no active solver. B gives unacceptable
density outliers (raw peak10.0). Bmax lowers core radial-velocity scatter41x
(.158645->.00387403), but mean density peak2.147 is close to low1.961 versus
old blend2.798. Core pressure1.54876 improves on low1.44343 (exact1.60510).
Budgets at roundoff; Bmax entropy minimum still undershoots initial floor by
.023%, so no strict entropy claim. Contact16/32/64 orders1.745/1.856. v1 failed
the smooth-order check because of omitted old-branch correction; stopped v1
science and retained artifacts. Corrected frozen archive
`../local_runs/sedov_rd_bsensor_20260929_v2/`, [report](RD_SEDOV_B_SENSOR_20260929.md).
4000 kernel checks + existing5 algebra checks pass; default Config/thesis
unchanged, all source uncommitted. Next distinct RD route is characteristic
limiting/Rusanov-PSI with stabilization and/or MOOD, if pursued.

**LDA+Rusanov static prototype completed (2026-09-29, log3 §167):** New opt-in
`RD_LDA_RUSANOV_BLEND=1` limits complete LDA/Gauss3/F1 stage corrections to a
common-Gauss admissible Rusanov update;0 selects its low-only control. Static,
periodic,1rank,equal steps,unsplit RK only; defaults unchanged. All12 native
runs/60 snapshots pass, no active solver. Same glass128² nearest21 Sedov reaches
t.05 with positive stages and roundoff M/E conservation. Mixed raw/mean rho
peaks3.791/2.798 versus low2.006/1.961; core r<.05 meanp1.6074 vs exact1.6051,
meanrho.02769 vs exact.00435. Shock-front density undershoot (~.6 mean), large
vr scatter and entropy-minimum violations remain: positivity is insufficient
for a finished shock scheme. Next: entropy/oscillation bounds before moving
geometry/remap. Smooth contact16/32/64 orders2.1166/2.0327; fields agree with
LDA to2.45e-14.2000 new compiled cases + existing5 algebra tests pass.
Frozen archive `../local_runs/sedov_lda_rusanov_20260929_v1/`; figures verified.
[Report](RD_LDA_RUSANOV_BLEND_20260929.md). No moving tests, thesis, commit/push
or COSMA changes. New source remains uncommitted with existing work.

**Rusanov source/blending audit (2026-09-29, log3 §165):** User asked for actual
Sedov literature provenance and LDA+N/Rusanov blending. The successful SGH RD
Sedov paper uses second-order staggered Lagrangian RD, MARS viscosity and an
energy correction; it is not our global low-order Rusanov implementation.
MOOD RD uses local high-order/PSI/Rusanov fallback and contains no Sedov test.
Existing B is LDA+N; N is not a reliable positive endpoint for our strong
Sedov. Recommended research direction is LDA+Rusanov with conservative
coupled positivity limiting, common flux totals and complete RK temporal
corrections. Gauss3/trapezoidal mismatch and positive conservative remap
remain separate tasks. No implementation/run/thesis change this audit.
[Report](RD_SEDOV_RUSANOV_LITERATURE_AUDIT_20260929.md).

**MMFV Sedov comparison completed (2026-09-29, log3 §164):** New frozen standard
AREPO moving Voronoi FV, exact Euler Riemann/native reconstruction, same21 hot
IDs/glass128²/pbg1e−6/Ehot1/t.05; actual Voronoi hot-mass normalization gives
phot520.89115 vs RD520.89295. Equal adaptive CFL.1 steps match RD; no refinement.
Uniform defect2.05e−13; science finishes1179 steps/179.29s. Finalrho min/max
.02843/3.97057, centralp~1.596 vs analytic1.605, conserved M/E to roundoff.
Moving/static Rusanov RD raw peaks2.630/2.002, minima.1960/.1248; static budgets
roundoff, moving energy−2.4147%. MMFV has only4 corecells r<.05 yet much better
core profile, so sparse sampling alone cannot explain RD plateau. Existing
SWIFT21 also plotted; all cases same injection count. Raw maxima differ from
plotted radial means (MMFV meanpeak3.302). MMFV values plotted at cell centroids.
All10 new saved states positive/finite,2 successful native runs, no active solver.
Archive `../local_runs/sedov_mmfv_20260929_v1/`, frozen source/config/binary/inputs,
checked figures; [report](RD_SEDOV_MMFV_COMPARISON_20260929.md). Default/solver/thesis
unchanged. Initial wrapper's overstrict1e−14 density check stopped after a
successful uniform run; geometry roundoff6.24e−14 verified, existing1e−12 uniform
bound applied consistently, then resumed without native rerun (details report).

**SWIFT default Sedov completed (2026-09-29, log3 §163):** Fresh isolated build
from clean SWIFT8dc43c3c (old build7fbba7e0-dirty not reused), default SPHENIX2D/
cubic kernel, stock IC/YAML/run options, 1thread. Finishes t.05 in2.189s,396
steps,6 snapshots positive/finite with IDs/masses preserved. Default eta1.2348
actually means15.14 target neighbours in2D, not YAML comment48. Density min/max
.03687/3.60417 versus moving Rusanov RD21 .19601/2.63044; SWIFT's central p/vr
have substantial deviations/scatter, so it is not a uniformly better profile.
Final mass exact; energy +.04005% relative to input IC, or−.11274% relative to
savedt0. The latter has nonzero output velocities from the initialization/
leapfrog output convention (E0saved1.001531 vs IC1.0000015); budgets show IC
normalization explicitly. No solver/IC tuning or further SWIFT sweep.
Archive `../local_runs/swift_sedov_default_20260929_v1/`; full frozen source,
config/binary/input/logs and visually checked profile/budget figures.
[Report](RD_SEDOV_SWIFT_DEFAULT_20260929.md). No active hydro, thesis untouched.

**Sedov core/reference audit (2026-09-29, log3 §161):** Read-only; no new native
runs. Moving1 has only1/7 nodes inside r<.05/.1 at t.05, versus130/516 for
static21; typical central sqrt(dual area) .0624 vs .00781. Static Rusanov is
conservative yet also has excess central density, supporting low-order
diffusion plus sparse moving-core sampling rather than attributing all profile
error to connectivity loss. Pressure/velocity causes are not uniquely isolated.
Morton committed main.cpp normalizes hot energy to3e5, after setup pressure
assignment; prior pilot's provisional1e6 pressure was not the complete IC.
With L10/rho1/E3e5, Morton t.01 rescales to unit-box t.0547723 and pbg100 to
.0333333, versus our .05 and1e-6. SWIFT configured finalt.05 matches our actual
final snapshot; its cadence.01 differs from ours.0125. No SWIFT hydro result
exists here, only its analytic formula. Dense central sampling of that formula
passes energy/shock checks; center p1.604968 is finite while rho/vr tend0.
Archive `../local_runs/sedov_core_reference_audit_20260929_v1/`, core plot checked.
[Report](RD_SEDOV_CORE_REFERENCE_AUDIT_20260929.md). Solver/default/thesis unchanged.
Follow-up §162 separates SWIFT/RD/Morton in a full parameter table. RD21 uses
exactly the same cached SWIFT glass modulo periodic wrapping and the same21
hot IDs. Equal SPH masses versus actual RD dual masses produce nominal hot
pressures520.127/520.893, a .147% difference at fixed hot energy1. SWIFT run.sh
enables its timestep limiter; no SWIFT executable or hydro output was tested.

**Smaller Sedov injection completed (2026-09-29, log3 §160):** SWIFT's local
SedovBlast_2D makeIC.py matches current upstream bytewise and heats21 particles,
despite its singular detonation comment. New same-glass128² 1/7-node moving
Rusanov controls both reach t.05 without repair (3189/3142 steps); final rho
peaks2.61579/2.64780, energy drift−2.5763%/−2.6657%, mass−.2376%/−.2399%.
Profiles nearly overlap the21-node reference, with no clear narrowing of the
shock. Old repair fails at t.00506592/.00544434 with negative pressure in the
same IDs7932/7977 as21-node failure. All16156 accepted science stages passed
positivity checks. Six native attempts finished,22 saved states audited,
2 uniform gates1.11e-15, no active solvers. No solver/default/thesis changes.
Archive `../local_runs/sedov_injection_sweep_20260929_v1/`; frozen binaries
reused per-method with full source provenance. [Report](RD_SEDOV_FEWER_INJECTION_POINTS_20260929.md).
Profiles are centered on each initial injected-energy centroid; single hot
node is slightly off box center. This tests Rusanov, not LDA or SWIFT hydro.

**Connectivity repair retrial (2026-09-29, log3 §159):** On user request,
allowed the existing unlimited topology repair with experimental Rusanov;
this combination refreshes predictor primitives from repaired U while keeping
interval mesh velocities. Same glass128² strong Sedov ICs: both fail inside
repair, before RK, at t.00546875 (21 nodes, minimum p−.0190042) and t.00159912
(130 nodes, p−.000343358). All1836 preceding science stages passed positivity
and CFL checks. At the common21-node time t.00545654, energy drift improves
from−1.2498% to−.0001046%, but the next remap fails. The old map conserves
extensives yet is not positive. A conservative low/high remap limiter remains
needed; none was added in this retrial. Uniform error1.11e-15, all5 algebra
checks pass. Frozen archive `../local_runs/sedov_topology_repair_20260929_v1/`,
all3 attempts finished, no active solvers. [Report](RD_SEDOV_TOPOLOGY_REPAIR_20260929.md).
Optional `run_positivity.py prepare ARCHIVE --topology-repair` reproduces the
diagnostic, not a validated Sedov repair. Defaults/thesis unchanged.

**Rusanov positivity prototype finished (2026-09-29, log3 §158):** Added opt-in
`RD_RUSANOV_LOW_ORDER`: scalar Rusanov spatial RD with trapezoidal flux and
existing N/lumped RK2 temporal terms, one-rank/equal-step/periodic hydro only.
Both stage CFLs, pair bars, rho/internal energy and ALE convex weights are
checked; no clipping. All four original glass128² strong Sedov cases (21 or
130 heated nodes, static/moving) now reach t.05. This is low-order fallback
validation, not positivity-limited LDA. Static conservation is roundoff;
moving loses2.4147%/1.3154% energy and.2397%/.2358% mass, so general ALE
endpoint conservation remains unresolved. 5000 compiled-kernel tests and all
5 algebra targets pass;3 uniform gates <=1.11e-15. Flag-disabled static N
matches the original binary bitwise at5 snapshots. All9 native attempts and
45 snapshot audits finished, no active solvers. v1 preserves a header-option
build failure; successful frozen archive `../local_runs/sedov_positivity_20260929_v2/`.
[Report/next LDA limiter design](RD_SEDOV_POSITIVITY_20260929.md). Source edits
remain uncommitted; default Config and thesis unchanged. Use explicit
`examples/Sedov_2d/Config_Rusanov_*.sh`; do not call this method Roe N merely
because N_SCHEME selects its lumped temporal branch.

**Moving Sedov pilot finished (2026-09-29, log3 §156):** SWIFT physical setup,
glass128², unit periodic box, gamma5/3, rho1, P0=1e-6, Ehot1, targett.05,
lab frame, adaptive equal steps/CFL.1. Nearest21 seed: static/moving N/RK2
fail at .00672073/.00226440; LDA/Gauss3 fails almost immediately in both.
Radius.05 seed heats130 nodes: static N completes t.05, moving N fails at
.00828857 with negative mass after corrector. Halving CFL to.05 does not
rescue21-node N (static .00672493, moving .00296021); static first-order N
also fails (.00663452). Thus no validated moving Sedov result. Five uniform
gates pass (max8.88e-16); all18 native attempts finished, no active solvers.
Moving130-node saved state at .00500488 loses .65% energy; completed static
conserves mass/energy to roundoff. No solver or thesis edits, commit or push.
Archive `../local_runs/sedov_2d_20260929_v1/`; source/scripts/configs/failed
outputs preserved. [Report](RD_SEDOV_MOVING_PILOT_20260929.md). Early density
preview and completed static profiles in `analysis/disk005/`. Do not treat
the early moving map as a successful t.05 solution.

**User's boosted-vortex wording decision (2026-09-29, log3 §154):** Supersedes
the editorial recommendations in §152–153. Keep the current prose: no added
h=10/N or lab/comoving-frame explanation, retain Galilean invariance without
"approximate", and retain edge flips as a possible explanation. User explains
that static boost10 is omitted at t3 because it was already dissipated at t1;
this is their rationale, not a newly calculated t3 snapshot. Comoving frame is
an optional optimization, not a required/default mode; its necessity remains
unsettled (Gresho boost10 runs in the lab frame). Only thesis edit: corrected
the moving-LDA order1.401 label from density to velocity. No compilation or
GitHub/Overleaf sync in this turn.

**Boosted-vortex prose review (2026-09-29, log3 §152):** Reviewed the user's
thesis revision219853e without editing thesis. Yee side length10 is supported
by param.template BoxSize10, local handoff HDF5 Header/coordinates, and the
COSMA analysis period10/centre(5,5). Local handoff IC file hashes differ from
the later COSMA comparison hashes; this was not a byte-identical raw-COSMA IC
verification. Moving LDA order1.401 is velocity, not density (1.739); excluding
Nx384 gives velocity order1.554, so the reduced order is not solely that point.
Current matched Gresho archives contain static boost10 at t1 and boost3 at t3,
but no static boost10/t3 result supporting the new completely-dissipated claim.
Recommended separating empirical boost insensitivity from lower rotational
diffusion, retaining frame/time-refinement details, and leaving edge-flip
causation as untested. No thesis edits, compilation, new simulations or sync.

**Yee resolution clarification (log3 §153):** Static and moving both use
L=10 with periodic boundaries. N counts nominal nodes per box side, not per
unit length; Ntot=N² and h_nom=L/N=10/N. Local ICs48/96/192/384 confirm these
counts. For an unchanged physical vortex scale, enlarging L1 to10 at fixed N
makes the spacing ten times larger; consistently rescaling both box and vortex
does not change relative resolution. Fixed-L fits versus N remain valid.

**Sod Nx64 inserted into thesis (2026-09-28, log3 §151):** User chose the
clearer Nx64 display and authorized insertion with brief prose. Chapter4.3.2
now includes Sod shock tube and Figure4.9 (printed169; setup text166), using
`chapter4/figures/sod_glass_Nx64_t02_profiles.pdf`. This is page2 of the approved
v3 review, with vector content/600dpi scatter streams preserved exactly.
Two short paragraphs give the IC, effective resolution, lab/CFL setup and
observed sharper contact plus persistent LDA/RK2 oscillations; caption records
Roe first-order versus N/Roe and LDA/Gauss3/F1 RK2 choices and128-bin means.
Full250-page XeLaTeX build passed, no unresolved references; master.pdf/bbl
refreshed. Six nearby pages reviewed; all other tracked thesis files unchanged.
Review: `../local_runs/thesis_ch4_sod_20260928_v1/output/pdf/thesis_ch4_sod_review.pdf`.
No commit/push; local thesis changes still need the normal GitHub/Overleaf sync.

**Latest Sod preview: three fields / 600 dpi (2026-09-28, log3 §150):**
`../local_runs/Sod_2d_Morton/20260928_main_comparison_v3/output/pdf/Sod_2d_Morton_main_comparison.pdf`
shows only rho, vx and p in three rows, N/LDA in two columns, pages Nx128/64.
Title follows the user's correction: Sod shock tube, Nx=..., gamma=5/3, t=.2.
No footer; numerical curves remain distinct dashed styles. PNGs5700x4740 at
600dpi; PDF scatter layers confirmed600dpi, lines/text remain vector.
Both pages reviewed; scientific input/metadata unchanged. No hydro/thesis edit.

**Sod figure style / internal-energy audit (2026-09-28, log3 §149):**
Latest two-page review is
`../local_runs/Sod_2d_Morton/20260928_main_comparison_v2/output/pdf/Sod_2d_Morton_main_comparison.pdf`.
All three numerical means now use distinct dash lengths/phases, exact remains
solid; title is only Sod shock tube, Nx=128/64 and footer removed. Data and
method choices from §148 unchanged. Twelve final snapshots / 491520 nodes
satisfy stored e=p/[(gamma-1)rho] with max relative defect2.14e-16.
At x=.70907 in Nx128 static LDA/Gauss3/RK2, rho=.176757 vs exact.229806,
p=.293417 vs.293945, e=2.490006 vs1.918654: density undershoot explains the
large specific-energy overshoot algebraically. Shock-side e undershoot has
a larger fractional pressure drop than density drop. This validates the
plotted field relation, not the correctness/stability of the RK2/F1 solver.
Audit script/JSON saved alongside the reviewed PDF. No hydro/thesis edits.

**Sod main comparison and first-order meaning (2026-09-28, log3 §148):**
User reaffirmed the thesis LDA default is Gauss3 contour, and wants static
first-order RD plus static/moving RK2 as the main comparison. Predictor-only
uses the full dt RD predictor as U(n+1), skipping the corrector and F1 temporal
term; this is precisely the Chapter3 first-order update, not a half step.
New two-page review (Nx128 then64):
`../local_runs/Sod_2d_Morton/20260928_main_comparison_v1/output/pdf/Sod_2d_Morton_main_comparison.pdf`.
N uses Roe throughout (mesh split when moving). LDA first-order is Roe for the
Morton-style baseline; both RK2 curves are Gauss3/F1. Therefore the LDA
first-order/RK2 contrast also changes residual, while the RK2 mesh pair is
matched. All twelve selected raw curves/bin means and source hashes verified;
both pages rendered/reviewed. Main plot labels now say first-order RD.
No new hydro runs, solver/thesis changes, commit/push or COSMA operations.

**Sod display labels simplified (2026-09-28, log3 §147):** User accepts
t=.2 as the Morton comparison assumption. Figures now label x=X-1 on0<x<1
for raw tube1<X<2, and time t=.2; numerical values equal the earlier xi/tau.
Left tube0<X<1 has the reversed primitive-state pattern for periodic closure,
not an exact reflection of individual glass nodes. Presentation-only six-page
PDF at `../local_runs/Sod_2d_Morton/20260928_display_x_v1/output/pdf/Sod_2d_Morton_variants_review.pdf`.
All18 raw curves/bin means unchanged; six pages rendered/checked. Both plotting
entry points updated; original simulation archives and thesis untouched.

**Sod_2d_Morton full variants completed (2026-09-28, log3 §146):** User
clarified to run the current moving/RK2 variants on the same Morton setup.
Added7 isolated builds,7 uniform gates and14 science runs; together with the
previous4 Euler controls, all18 science cases reach t=.2 at effectiveNx64/128.
Same exact glass ICs, gamma5/3,2x2 box,xi=x-1,tau=t,CFL.4,cap.02,lab frame.
Static N/RK2, LDA/Euler/Gauss3, LDA/F1 Roe/Gauss3 and moving N/RK2/Roe,
LDA/F1 Roe-split/Gauss3 all complete. Existing guard forbids moving
predictor-only; no moving Euler construction, hierarchy or solver changes.
Nine total uniform gates pass (max2e-15); all135 saved states positive/finite.
LDA/F1 retains vx trough around-.59 in both meshes and residuals; static
Euler and N/RK2 have no comparable trough. Moving improves density L1/contact
sharpness but increases velocity/pressure L1 in these pairs. Moving Roe/F1
Nx128 has strong contact scatter (vx_max1.2009,e_max8.5319), Gauss3 .9917/2.3247.
Moving endpoint mass/energy drift reaches.0958%/.2112%; static stays round-off.
Adaptive dt histories differ; Roe/F1 movingNx128 reachesdt9.76562e-5.
Six-page local-only PDF, all raw nodes/128-bin means, verified and reviewed:
`../local_runs/Sod_2d_Morton/20260928_full_v1/output/pdf/Sod_2d_Morton_variants_review.pdf`.
[Full methods/results](RD_SOD_2D_MORTON_VARIANTS_20260928.md). Reproducible
`examples/Sod_2d_Morton/run_variants.py` and `analyze_variants.py`.
No running campaign remains; no thesis edit, commit/push or COSMA operation.

**Sod_2d_Morton completed (2026-09-28, log3 §145):** User named a new test
using Morton parameters but glass IC. Two uniform gates and four static
first-order Roe N/LDA runs completed at effectiveNx64/128 (full128²/256²).
gamma5/3,CFL.4,2×2 periodic box,central high state. Local standalone SODX
source supports endt=.2 and box2, without proving original Fig7 revision.
New coordinates xi=x-1 on1<x<2,tau=t; DO NOT apply the earlier2t scaling.
LDA vx_max.95593/.87979 versus exact.84119; large negative F1 trough absent,
but positive oscillations remain. N is smoother. All saved rho/p positive,
max mass/energy drift<8.1e-16. AREPO carrier/tree/dyadic timesteps retained;
same CFL parameter does not imply original nodal-RD timestep equivalence.
Example `examples/Sod_2d_Morton/`; archive
`../local_runs/Sod_2d_Morton/20260928_v1/output/pdf/Sod_2d_Morton_review.pdf`.
[Setup/results](RD_SOD_2D_MORTON_GLASS_20260928.md). No solver/thesis edits or push.

**Sod IC/Morton/SWIFT audit (2026-09-28, log3 §144):** Verified the actual
shared IC and six static/moving t0 snapshots. xi=2(x-.25),tau=2t is correct;
full128² gives initial effective tubeNx64, with8187 nodes in the half-box
window. Analytic raw/scaled solutions agree exactly; first continuum mirror
interaction is rawt.142681, after current.08. Morton uses the same primitive
states but gamma5/3 rather than1.4, structured row-offset points and first-order
LDA/N; its final time is not explicitly specified in §5.1.1/Fig7. SWIFT2D
defaults gamma5/3,rhoR.140625 and equal-mass two-glass sampling, not our IC.
Its displayed unit tube has nominal spacings1/256 left,1/96 right (ours1/64
both); defaultt.2 is later than ourtau.16. No new runs/IC/solver/thesis edits.
[Full comparison and evidence](RD_SOD_IC_MORTON_SWIFT_AUDIT_20260928.md).

**Chapter3 TODO / RT landscape (2026-09-28, log3 §143):** Removed the sole
remaining Chapter3 TODO beside the K matrix without changing the equations.
Figures3.8/3.9 now use upright landscape PDF pages (printed134/135,
PDF156/157), matching the Chapter2 table/flowchart style. Source figures and
captions unchanged. Full249-page XeLaTeX build passed; reviewed the matrix,
both figures and adjacent pages. master.pdf/master.bbl refreshed, now also
including the fetched Chapter1 edits. Review PDF:
`../local_runs/thesis_ch3_rt_landscape_20260928_v1/output/pdf/thesis_chapter3_rt_landscape.pdf`.
Only Chapter3 tex changed among tracked thesis files; no commit/push.

**Thesis figures pushed (2026-09-28, log3 §142):** User's existing figure-only
commit2efbebe contained two Yee PDFs and the approved Gresho PDF. Fetched
Overleaf Chapter1 updates through8f3d53f, rebased the unpublished image commit
without conflicts, and pushed aa3712a to thesis origin/main. Figure blobs
unchanged; remote Chapter1 text retained exactly. AREPO commits and local Sod
previews were not pushed. Existing master.pdf predates the newly fetched
Chapter1 edits; it was not rebuilt for this Git-only request.

**Matched static Sod review (2026-09-28, log3 §141):** Four new static Sod
runs plus four uniform gates use the same frozen source/IC/physical parameters
as September24 moving controls. Static LDA/Gauss3/F1 still has vx_min=-0.7293
(moving -0.7378); static N is smoother. Predictor-only first-order static LDA
has no large negative trough for Gauss3 or Roe, but vx_max=1.1695/1.1385 remains
above the analytic plateau. Morton2023 uses first-order, row-offset regular
mesh/gamma5/3 and explicitly notes LDA oscillations; our controls are not its
full reproduction. Three-page local-only review:
`../local_runs/sod_static_matched_20260928_v1/output/pdf/sod_static_review.pdf`.
[Setup and diagnostics](RD_SOD_STATIC_COMPARISON_20260928.md). No thesis edits.

**Gresho inserted / Sod local preview (2026-09-28, log3 §140):** Approved
Gresho colour figure is now Chapter4 Figure4.8 (printed168); one short paragraph
added under shared `Boosted vortex tests`. Full249-page thesis compiled and
master.pdf updated; retained red draft starts after all vortex figures.
Sod is still local-only: three-page review (full profiles, contact/shock zoom,
central-strip density evolution) in
`../local_runs/sod_thesis_preview_20260928_v2/output/pdf/sod_review.pdf`.
Reuses September24 lab-frame moving N/Roe and LDA/Gauss3, glass128² (tubeNx64),
rawt=.08/tau=.16; LDA vx undershoot -0.738 remains visible. No new solver runs.
[Settings and interpretation](RD_SOD_THESIS_PREVIEW_20260928.md).

**Gresho preview colour revision (2026-09-28, log3 §139):** Moving boost0 is
orange in N and purple in LDA, as requested. All data/means and other styling
unchanged. Latest standalone PDF/PNG:
`../local_runs/gresho_boost_color_preview_20260928_v1/` (output/pdf and figures).

**Gresho style preview (2026-09-28, log3 §138):** User proposed grouping Yee
and Gresho boost tests and requested mean lines/faint scatter/internal legends.
New standalone preview reuses §132 five glass48/t3 cases, adding35 uniform
unweighted radial means and alpha0.09 scatter, with short title/N-LDA panels.
Original inputs, old plot and thesis unchanged; no solver runs. New PDF/PNG:
`../local_runs/gresho_boost_style_preview_20260928_114134/` (output/pdf and figures).
[Style/section recommendation](RD_GRESHO_BOOST_STYLE_20260928.md).
Suggested shared heading: Boosted vortex tests; keep separate figure groups and
explicitly distinguish Yee element-co-moving evaluation from Gresho lab-frame
evaluation. Proposed caption saved, not inserted into thesis yet.

**Chapter2 Table2.1 landscape PDF (2026-09-28, log3 §137):** User requested
the same upright landscape reading orientation as the AREPO flowchart.
Converted sidewaystable to a landscape/table page; afterpage preserves original
placement. Only PDF page106 (printed84) gains Rotate90. All247 pages retain
identical extracted text and page numbers; table data/Chapter3/Chapter4 unchanged.
No unresolved refs or LaTeX errors; printed83--85 rendered and checked.
Updated master.pdf and review PDF at
`../local_runs/thesis_ch2_table_landscape_20260928_112503/output/pdf/thesis_chapter2_table_landscape.pdf`.
Local edits only; no commit/push.

**Chapter3 selected citations added (2026-09-28, log3 §136):** User selected
Roe/Sidilkover1992 for N, Struijs/Deconinck/Roe1991 for LDA, and van der
Weide/Deconinck1996 plus Abgrall/Barth2002 for the Euler matrix N form.
All four inserted directly into existing introductory sentences; three new
BibTeX entries added (Roe1992 already existed). Distribution `add ref` TODO
removed. No extra prose/formula changes; K region and Chapter4 unchanged.
Full247-page PDF compiled with no unresolved refs/citations; printed117--118
and new bibliography entries visually checked. `master.pdf`/`master.bbl` refreshed.
Archive `../local_runs/thesis_ch3_scheme_citations_20260928_111819/`, final
`output/pdf/thesis_chapter3_scheme_citations.pdf`. No commit/push.

**Chapter3 user correction (2026-09-28, log3 §135; supersedes §134 prose edits):**
K request meant checking the 16 entries only; Distribution Schemes needed early
N/LDA sources, not added review/application prose. Both regions restored exactly
to pre-edit/HEAD text, including original TODO markers; CGAL/Fabri2000 retained.
K elements remain verified correct. Research points to Roe1987 / Roe-Sidilkover1992
for scalar N, Struijs-Deconinck-Roe1991 for early LDA (explicit attribution in
Deconinck et al.1993 §3.1), and van der Weide-Deconinck1996 for system N.
1987/1991/1996 originals not retrieved; metadata/attributions cross-checked with
early primary papers and VKI catalogue. No new historical citations inserted.
Refreshed247-page PDF: `../local_runs/thesis_ch3_origins_20260928_105952/output/pdf/thesis_chapter3_restored.pdf`;
no unresolved citations/refs; pp.115--117 rendered. Chapter4 unchanged, no push.
[Restoration and source trail](RD_THESIS_CH3_LDA_N_ORIGINS_20260928.md).

**Chapter3 red notes resolved (2026-09-28, log3 §134):** User authorized
Chapter3 references/K review and PDF build. All3 TODOs removed; distribution
references and Fabri2000 CGAL citation added. Existing K entries are correct:
normal includes edge length, while both standalone and AREPO code store unit
normal and apply ell/2 separately. Symbolic16-entry and480 native-matrix
checks pass. Full247-page thesis PDF compiled, no undefined refs/citations;
review printed115--117 and123. master.pdf refreshed. Chapter4 unchanged;
no commit/push. Archive `../local_runs/thesis_ch3_rednotes_20260927_235021/`,
[audit/build report](RD_THESIS_CH3_REDNOTES_20260928.md). For isolated builds,
precreate include subdirectories and put fresh build bibliography first in
TEXINPUTS; root's old master.bbl otherwise masks new references.

**Thesis Overleaf sync (2026-09-27, log3 §133):** User requested GitHub pull,
especially Overleaf's4.3.1. Thesis main fast-forwarded from6af0539 to06c9647;
4.3.1 matches the remote exactly, remote removal of4.2.3 and Chapter1 edits
included. Local4.3.2 Yee text and its two PDFs preserved, still uncommitted.
All32 untracked files and both old stashes preserved. No new commit/push or
PDF compilation; the existing thesis PDF predates this sync. Backup and checks:
`../local_runs/thesis_overleaf_sync_20260927_234550/`.

**Current execution preference (2026-09-27): return to the local Mac.** The user
requests subsequent experiments locally; COSMA is not needed for the next phase.
The copied Yee boost10 comparison is in
`../cosma_runs/yee_n_boost10_20260926/comparison_latest/`.
See [local return and COSMA import](RD_LOCAL_RESUME_COSMA_IMPORT_20260927.md)
for Git-integration status and [file checks](COSMA_RESULT_IMPORT_20260927.json).
Use `LocalMac`, isolated build/run artifacts, and both `OMP_NUM_THREADS=1` and
`OPENBLAS_NUM_THREADS=1`; moving equal-step RD remains one MPI rank. Old
interrupted campaigns are not restarted.

**Latest Gresho preview adds static N0 at t3 (2026-09-27, log3 §132):**
The left N panel now also shows a new matched static boost0 run, glass48,
lab frame, t3. Uniform/pilot/science complete with original gates; all five
plotted cases have identical16384-step histories. Static0/moving0 N initial
fields match bitwise. Static0 L1 .120856 versus moving0 .0472447 (60.91%
reduction); peak .485980 versus .735437. Supports less damping of local vortex
rotation even without bulk boost. Original moving runs and figure preserved;
new PDF/PNG rendered and checked, standalone only, no thesis insertion.
Archive `../local_runs/gresho_glass_t3_static0_overlay_20260927_v1/`;
[static0 overlay report](RD_GRESHO_STATIC0_T3_OVERLAY_20260927.md).
No active solver workers.

**Completed moving Gresho boosts0/10 at t3 (2026-09-27, log3 §131):** Glass48,
moving N/LDA, lab only, standalone preview per user. All12 uniform/pilot/science
cases complete; science runs have identical16384-step histories, dt3/16384.
N boost0/10 vphi L1 .0472447/.0470778; LDA .0125298/.0124913. Analytic-error
metrics differ by .353%/.308%; radial profiles closely overlap. Joint mesh/state
ID differences are measurable (position RMS N .0472, LDA .00957 at t3), so do
not claim exact trajectory invariance. Moving mass drift remains ~1.5–1.8e-4.
Reviewed standalone PDF/PNG available; no running workers, no thesis insertion.
Archive `../local_runs/gresho_glass_moving_boost0_10_t3_lab_20260927_v1/`;
[boost0/10 t3 report](RD_GRESHO_MOVING_BOOST0_10_T3_20260927.md).

**Completed Gresho boost3/t3 (2026-09-27, log3 §130):** N/LDA static/moving,
boost(3,0), t3, genuine glass48, lab only; same four frozen §128 binaries.
All12 uniform/pilot/science runs complete. Science cases each take16384 steps,
actual dt3/16384 (common cap1/4096), identical complete timestep histories.
N static/moving vphi L1 .239917/.0472093; LDA .222662/.0126008. Moving mass
drift +1.424e-4/+1.775e-4 remains. Full-range two-panel PDF, including negative
static-LDA tail, is rendered and reviewed; no active workers. Outputs at
0,.75,1.5,2.25,3. Source/code/default/thesis unchanged. Archive:
`../local_runs/gresho_glass_boost3_t3_lab_20260927_v1/`; report:
[boost3/t3 comparison](RD_GRESHO_GLASS_BOOST3_T3_LAB_20260927.md).

**Completed N boost0 controls (2026-09-27, log3 §129):** Matched static0 and
moving0 N/Roe glass48 runs reuse the exact §128 binaries, t1/dt1/4096. Uniform
and pilot gates pass, all six new cases complete. vphi L1 static0 .0580965,
moving0 .0188867, versus moving10 .0189083. Thus moving10 is about3.07x better
than static0; moving boost0/10 analytic error norms differ by0.1144%. The full
mesh/state solutions have measurable differences (ID-matched velocity L1
.002388 and position RMS .002380 at t1), so this supports weak boost sensitivity,
not exact invariance. Static0 and quasi-Lagrangian moving10 are different mesh
motions even after a Galilean transform. Updated N-only figure is reviewed;
no running workers, LDA0 or boost3. Report:
[N boost0 controls](RD_GRESHO_N_BOOST0_CONTROLS_20260927.md), archive
`../local_runs/gresho_n_glass_boost0_controls_20260927_v1/`.

**Completed Gresho glass boost10 (2026-09-27, log3 §128):** User requested lab
only, genuine glass48, N/Roe and LDA/Gauss3 static/moving, boost10 first.
Four uniform gates, four short pilots and four t1 science runs all pass native
completion/positivity checks; uniform defects below existing1e-12 threshold.
All science cases take4096 matched steps. Moving/static mass-weighted vphi L1
ratios .07880 (N), .04389 (LDA); moving mass drift +3.707e-5/+4.138e-5 remains.
Two-panel lab-only profile PDF is complete and visually checked. No current
solver workers; no boost0/3 launched. This supports a compact static/moving
illustration, not convergence or strict boost invariance. Source/binaries/raw
outputs: `../local_runs/gresho_glass_boost10_lab_20260927_v1/`.
See [matched glass boost10 report](RD_GRESHO_GLASS_BOOST10_LAB_20260927.md).
No numerical/default Config/thesis changes or Git commit/push for this run.

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
