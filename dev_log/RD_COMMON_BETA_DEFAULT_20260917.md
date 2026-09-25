# Static LDA/F1: common opening-state beta as the default

Author: Codex. Date: 2026-09-17. Requested by Zhenyu Wu.

The user approved changing the default to a common beta and stating in
Chapter 4 that earlier beta_n/beta_* comparisons gave very similar errors.
This report records the actual implementation, a singular-matrix issue found
in the native gates, its explicit numerical treatment, and the validation.

## Scope and formula

The standard **static LDA/F1** path now defaults to the distribution evaluated
at the opening of the interval. This includes internal equal stepping, the
split main-loop hooks, and the static hierarchy. `RD_LDA_MIXED_STAGE_BETA`
is an opt-in comparison flag restoring the former implementation. It is
registered in `Template-Config.sh`; the derived `RD_LDA_COMMON_BETA` is internal.
No root `Config.sh` was changed. N, B, moving ALE and the four-pass
`RD_RK2_RATE_CONSISTENT_HEUN` experiment retain their previous conventions.

With nodal conserved densities U, predictor increment delta U = U* - U_n,
element area |T| and interval h_T, the full-rank default corrector is

\[
\Phi_i^T=\beta_i^{T,n}\left[
\frac{|T|}{3h_T}\sum_{j\in T}\delta U_j
+\frac12\bigl(\phi^T(U_h^n)+\phi^T(U_h^*)\bigr)\right].
\]

The new spatial residual is still evaluated from the predicted state.
Only its distribution and the F1 distribution use the opening-state beta.
The old spatial half is already represented by the existing predictor
increment/ledger; it requires no new stored triangle residual or beta tensor.

In `residual_distribution_solver.c`, `U_beta` is captured before the
hierarchy adds live-node predictors. Its primitive base states remain frozen
until each node's own interval closes. Thus a coarse frozen vertex need not
be physically extrapolated to the fine interval opening: n denotes the
states supplied at that opening. For equal stepping, the already exchanged
predictor increment is subtracted from the stage-1 conserved density to
recover the opening state, including ghosts. This recovery is subject to
ordinary floating-point round-off.

The unsplit K matrix retains the current-stage Roe average for the spatial
residual. The split K+/K- pair uses the opening-state Roe average. The same
old split pair solves and distributes the new spatial and F1 targets.
Consequently individual stored Kfull and K+ + K- belong to different states
in the corrector; their element sums still vanish separately. This distinction
is intentional, and is covered by a compiled production-block test against
complex-step derivatives of the physical Euler flux.

There is no additional mesh construction, element sweep, factorization or
MPI payload. There is additional per-element opening-average arithmetic;
no runtime-speed claim is made from these diagnostic builds.

## The singular case is an additional numerical choice

The first implementation only froze beta and retained the old generalized
inverse treatment. It completed 15 native cases but failed **both Sod gates**
at the first corrector. For equal stepping, one raw element conservation
defect was 2.6479027007763757e-6, versus a 2.260687332075268e-15 tolerance.
This is a numerical failure, not MPI setup noise or rounding.

Let S = sum_j K_j^- be the old inflow matrix. A resting Euler state can give
rank(S)=3. Although phi_n belongs to its range, phi_* need not. Merely using
x=S^dagger phi_* then distributes S S^dagger phi_*, losing the complement.
Freezing beta therefore requires a definition on this missing direction.

For the common-beta **spatial** distribution we now define, on elements
reported rank deficient by the existing DGELSD policy,

\[
\widetilde\beta_i=-K_i^+S^\dagger
+\frac13\left(I-SS^\dagger\right).
\]

Since sum_i K_i^+ = -S, sum_i tilde beta_i = I. The range contribution is
unchanged; the unresolved part is shared equally. This is a design choice,
not a unique extension, a positivity proof, or a direction-independent
limit of beta as velocity tends to zero. The existing algebra test already
demonstrates direction-dependent near-stagnation limits.

`rd_common_beta_unresolved()` forms S x and the complement using the
existing solve, without another factorization. The raw range contribution
is independently checked against S x **before** the complement is added;
the full distributed residual is then checked against phi. Thus a broken
K split still fails A2. Full-rank elements receive no completion, and no
rank, SVD or conservation tolerance was changed.

For rank-deficient elements the **temporal** term retains the existing
node-lumped fallback |T| delta U_i/(3 h_T). Therefore the displayed common
F1 formula is explicitly a full-rank formula. Chapter 4's footnote states
both the spatial extension and temporal exception. This extension is our
implementation choice; it is not attributed to Paardekooper's paper.

## Frozen source and native evidence

Workspace archive: `../local_runs/common_beta_default_20260917_v1/`
(relative to the solver repository's parent workspace; actual absolute root
`/Users/zhenyuwu/arepo_rd/local_runs/common_beta_default_20260917_v1/`).

- `native/`: first frozen implementation, including the two failed Sod runs.
- `failed_setup/`: initial Open MPI sandbox socket-bind failure, before
  evolution; the successful local runs used the authorized native environment.
- `native_final/`: final numerical implementation, 17/17 cases completed.
- Base commit: `adc424ba93f8cb98ff494dd8e98b41fafcd2e98b` plus the saved working diff.
- Final source tar SHA256:
  `2ca8059f1e5de15b2d02889bbbff26e9ef31c1dc0e4bd350372268ac27bf4c06`.
- Each of seven configurations has separate frozen Config/header, native
  arm64 executable/hash, build log and dynamic linkage. Each run has its
  own immutable input provenance, parameters, logs and output directory.
- `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`; at most eight MPI ranks
  running concurrently. Debug conservation assertions remained enabled.

`make check_rd` passes all four scripts. The new
`tests/rd/test_lda_common_beta.py` compiles the production K-construction and
singular-complement helpers. Across 300 state pairs the Euler Jacobian defect
is 2.665e-15 and common-total identity defect is 3.553e-15. The exact resting
rank-3 case tests partition of unity for all four basis targets, and 100
compatible targets retain their original upwind contributions.

The native cases include:

| Gate | Actual setup | Result |
|---|---|---|
| Yee | 2304 glass nodes, static periodic box 10, boost (1,0), t=1; gamma=1.4, CFL .2, max dt=1/256; Gauss3 equal/split/equal-bin hierarchy and legacy Roe, ranks4 | All complete; positive saved states |
| Smooth KH | 2304 glass nodes, periodic unit square, t=2; gamma=1.4, CFL .3; equal dt1/1024, natural hierarchy dt1/1024 and1/512; ranks1/4 | All complete; actual two-bin hierarchy with frozen vertices |
| Uniform flow | 2304 nodes, t=1/32, equal/hierarchy, ranks4 | Zero change in saved conserved densities |
| Sod | 16384 nodes, t=.08, equal/natural hierarchy, ranks4 | Both complete after explicit singular extension; hierarchy final bins19/20/21 |
| Pending-stage restart | 2304-node Yee, split equal, t=.125, ranks4 | Exact agreement with uninterrupted control |
| Mixed flag replay | Current Gauss3 Yee and equal/hierarchical KH, ranks4 | All three final states exactly reproduce their archived former-method outputs |

Maximum normalized global mass/momentum/energy drift in ordinary snapshot
summation is 1.48065e-14 across all 17 cases. The conserved densities are
compared after sorting by persistent ID. Equal internal versus split hooks
and restarted versus uninterrupted runs match exactly; equal-bin hierarchy
differs by at most 2.88658e-14. The rank1/rank4 KH differences are
3.26406e-14 (equal) and 1.28786e-14 (hierarchy).

The Sod minimum saved densities are .05365/.08032 and pressures
.02794/.05487 for equal/hierarchy. There are substantial undershoots;
successful evolution and positivity of these saved outputs do not establish
a positivity-preserving Euler method. Sod exercises the rank fallback;
Yee and KH report no F1 rank-lumped calls. Exact case-level statistics are
in `native_final/beta_summary.json`, including bins, area/coordinate
invariance, output hashes and elapsed times.

## What “very similar errors” means

Current glass2304 Gauss3 Yee, static boost1 to t=1, median-dual-area weighted
errors against the analytic advected vortex:

| Convention | Density L1 | Velocity-vector L1 |
|---|---:|---:|
| Common beta_n (new default) | 6.1417994083e-4 | 2.3644560289e-3 |
| Mixed beta_n/beta_* | 6.1530423075e-4 | 2.3645025509e-3 |

The density-error scalar changes by about -0.183%; the velocity-error
scalar by about -0.0020%. The maximum componentwise final-state difference
is nevertheless 2.61491e-4: the solutions are not identical. KH final-state
differences versus mixed are 4.82669e-4 (equal) and 1.07096e-3 (hierarchy),
without an exact KH reference to rank their errors.

The previous three-way test of common beta_n, common beta_* and mixed is
the 2026-08-01 Roe/jittered Yee experiment recovered in log3 sections70-72
and `PAARDEKOOPER_STAGE_BETA_AUDIT_20260917.md`. It found density L1 scalar
differences around .13% and fixed-h time orders around1 for all three.
Common beta_* was **not** rerun in the present Gauss3 campaign. Chapter 4
therefore says “Earlier ... tests” for the three-way observation, limits
the statement to those tests, and explicitly says the choices are not
algebraically equivalent. Changing beta does not establish second-order
temporal convergence or remove the frozen-star F1 hierarchy limitation.

## Thesis and KH figure

The Chapter 4 default formula, N/LDA stage distinction, and hierarchy's
interval-opening meaning were updated. The comparison/FV text, Chapters1-3,
the bibliography and MPI draft were preserved. Both singular exceptions
are stated in the footnote rather than hidden in a general common-beta claim.

The old mixed-beta KH figure is preserved. A new figure uses final native
common-beta runs, with eleven double-precision snapshots to t=2 and
compensated sums of per-node energy differences. Four-rank maximum absolute
delta E/E0 is 2.80230e-16 (equal) and 2.91439e-16 (hierarchy). The one-rank
controls give 1.05204e-16 and 3.85570e-16. These are round-off-level changes,
not an accuracy ranking or a timing benchmark. The plot's vertical bounds
cover the actual data; an initial plot-only bound check requested a larger
range before the figure was rendered. No simulation threshold was changed.

Reproduction scripts, thesis before/source/diff, build and PDF QA files,
`kh_energy_history.csv`, and `kh_energy_audit.json` accompany the archive.
Thesis edits and solver changes are uncommitted and unpushed for review.

The final full thesis compiles to 246 pages with zero unresolved references.
All seven review pages (printed143-149) and the standalone KH plot were
rendered and visually inspected. Installation checked all126 previously
tracked thesis files; only chapter4.tex changed, plus the new KH PDF.
Chapter4 SHA256: b2d59518ff5e2bb5310d491b7727c35bb75288c934d1c679f3bb60f574bad38d.
