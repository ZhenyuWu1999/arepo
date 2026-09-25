# Paardekooper's LDA beta time level: paper and public-source audit

Date: 2026-09-17. Author: Codex. Requested by Zhenyu to identify direct
support for stage-dependent beta, rather than the general RK-RD framework.
Read-only numerical-method audit; no thesis or solver changes, builds or runs.

## Finding

Paardekooper's public ASTRIX v1.1.0 uses the **old-state LDA distribution
matrix throughout the corrector**, including the F1 temporal contribution.
It does compute the new spatial total residual from the predictor state.
These are different choices: updating the total residual does not require
updating the matrix used to distribute that residual.

The paper's Eq. (63) has a single, unindexed beta multiplying the sum of the
two spatial residuals. Eq. (65) uses that beta for F1. The displayed equations
alone do not identify its state; the author's source resolves this ambiguity.

Source: S.-J. Paardekooper (2017), MNRAS 469, 4306--4340,
[DOI 10.1093/mnras/stx1083](https://academic.oup.com/mnras/article/469/4/4306/3798772),
Sections 3.4 and 4.2.1, especially Eqs. (60)--(65).

## Version and call-chain evidence

Public repository: <https://github.com/SijmeJan/Astrix>.
Inspected v1.1.0, commit `b8dc85a569d8aa87166af2d8f7903dbaa5b2dae1`,
dated 2017-05-18. Also checked the same old-state switch in v1.0.0,
commit `d5e7309dc1f8f94194b1f35ddeeb8aab3ddcf810`, dated 2017-02-10.
This establishes the convention in contemporary public releases, without
claiming a recovered binary for the paper's individual simulations.

Paths below are within that public repository, with v1.1.0 line numbers:

1. `src/astrix/Simulation/timeloop.cpp:188--203`: copy the initial state to
   `vertexStateOld`, form its parameter vector, calculate spatial residuals,
   then update the current state to the predictor.
2. `timeloop.cpp:245--252`: `CalculateParameterVector(0)` uses the current
   predictor state; `CalcTotalResNtot(dt)` constructs the new N spatial
   contribution and the combined element total residual.
3. **`timeloop.cpp:254--264`: `CalculateParameterVector(1)` explicitly switches
   to the OLD state before `CalcTotalResLDA()`.** The old-state array is only
   overwritten afterwards, at line 273.
4. `param.cu:118--137` confirms flag 1 reads `vertexStateOld`, while flag 0
   reads `vertexState`; `param.cu:39--59` constructs the Euler Roe parameter
   vector from that selected conserved state.
5. `totalresNtot.cu:90--136,218--293`: the total combines the old spatial
   residual, the predictor-state spatial residual, and the summed nodal
   state difference. Its factor of two in the temporal accumulation is
   cancelled by the final factor of one half.
6. `totalresLDA.cu:87--112,132--229,269--340,913--944`: the old parameter vector
   determines the averaged Euler state and K matrices; the inverse of the
   summed negative K matrix is applied to the ENTIRE combined residual,
   then multiplied by negative K-plus. Edge-length factors are restored by
   the residual accumulation convention; they do not change the beta state.

Decisive permalink:
<https://github.com/SijmeJan/Astrix/blob/b8dc85a569d8aa87166af2d8f7903dbaa5b2dae1/src/astrix/Simulation/timeloop.cpp#L245-L264>.

Local read-only clone and provenance archive:
`../../local_runs/paardekooper_stage_beta_audit_20260917_v1/`.

## Translation to the thesis notation

Use U for conserved density, U* for the predictor, delta U_j = U_j* - U_j^n,
and phi^{T,s} for the undistributed spatial residual of triangle T at state s.
Let beta_i^{T,n} and beta_i^{T,*} be the LDA matrices evaluated from those
respective states. Paardekooper calls the conserved state W; this report
translates it to the thesis U. The star is an end-of-step prediction, not a
physical midpoint state or the final corrected U^{n+1}.

For F1 and global lumping, the public ASTRIX LDA candidate corrector residual is

\[
\Phi_{i,\mathrm{ASTRIX}}^{T,\mathrm{LDA}}
=\beta_i^{T,n}\left[
\frac{|T|}{3}\sum_{j\in T}\frac{\delta U_j}{\Delta t}
+\frac12\left(\phi^{T,n}+\phi^{T,*}\right)\right].
\]

This is the LDA candidate before any N blending or unphysical-state fallback
in `UpdateState`; those safeguards do not change how its beta was constructed.

Current standard static AREPO-RD (full-rank F1, excluding experimental
four-pass rate-Heun and the hierarchical live/frozen extension) instead uses

\[
\Phi_{i,\mathrm{AREPO-RD}}^{T,\mathrm{LDA}}
=\frac{|T|}{3}\beta_i^{T,*}\sum_{j\in T}\frac{\delta U_j}{\Delta t}
+\frac12\left(\beta_i^{T,n}\phi^{T,n}
+\beta_i^{T,*}\phi^{T,*}\right).
\]

The old spatial half is retained implicitly through the predictor increment
and the local half-increment in `rd_rk2_prepare_corrector()`; it is not
redistributed with beta*. Current source anchors are
`src/hydro/residual_distribution_solver.c:3568--3574,3638--3643,5280--5317,5524--5526`.
Rank-deficient F1 has a separate lumped fallback.

For identical predictor, geometry and spatial-total-residual definitions,
the difference of these two corrector residuals is

\[
(\beta_i^{T,*}-\beta_i^{T,n})
\left[\frac{|T|}{3}\sum_j\frac{\delta U_j}{\Delta t}
+\frac12\phi^{T,*}\right].
\]

This is an algebraic comparison of beta conventions, not a claim that every
other numerical choice in the two codes agrees. In particular it does not
establish accuracy, positivity, or equivalence of the two nonlinear methods.

## What can be attributed to the literature

- For N, Paardekooper Eq. (62) explicitly averages separately evaluated
  nodal N residuals at the old and predictor states, with a lumped temporal
  term. The public code also rebuilds the N calculation from the predictor
  state. There is no analogous explicit Euler beta_N matrix in our code.
- For LDA, Paardekooper is **not** direct support for the current mixed
  beta_n/beta_* convention; the public implementation uses beta_n in all
  three corrector contributions.
- The already checked Ricchiuto & Abgrall (2010) and Arpaia et al. (2015)
  establish the consistent-mass/explicit-RD framework, but no direct
  endorsement of our exact mixed convention was located in this audit.
  This is a bounded literature finding, not a claim that no RD paper can
  support any stage-dependent distribution.
- The historical three-convention Yee comparison in log1 (2026-08-01,
  starting at line 4923; recovered in log3 section 70) remains experimental
  evidence for that setup only. Its coherent-old convention corresponds
  to the beta timing identified here; this does not make the entire solver
  identical to ASTRIX. It was not an F1-only substitution test.

Thesis implication: keep citations for the framework, identify mixed stage
beta as the implementation's choice, and do not use Paardekooper to claim
that this particular choice is prescribed or accuracy-equivalent. No thesis
wording was changed in this question-only turn.

## Follow-up: earlier RK2-RD papers and whether to change the baseline

Zhenyu subsequently asked whether earlier RK2-RD always freezes beta, whether
the literature is underspecified, and whether our implementation should use
beta_n throughout. This remains a research/recommendation request, not an
instruction to change the solver or thesis.

Two assertions must be distinguished:

1. One common beta distributes the temporal contribution and both spatial
   contributions within the corrector.
2. The predictor and corrector use the identical old-state beta_n.

The first is explicit in the core LDA/F1 formulas. An unindexed beta in those
formulas does not, by itself, establish the second for nonlinear Euler.

Further primary-source checks:

- Ricchiuto & Abgrall (2010), Eqs. (13), (36), (42), (51)--(53),
  Proposition 4.3 and Remark 4.4. The corrector uses one beta multiplying the
  combined RK spatial residual, and F1 uses the same beta in its mass. The
  LDA beta definition uses the element average state but does not specify
  old versus predicted state with a stage index. The initial consistent-mass
  discussion starts with constant linear advection; in that LDA setting beta
  is independent of the evolving solution on a fixed mesh. The accuracy
  argument requires a bounded bubble/distribution and residual consistency;
  it is not a theorem prescribing beta_n for every nonlinear implementation.
  [Author manuscript](https://www.researchgate.net/publication/223033482_Explicit_Runge-Kutta_Residual_Distribution_schemes_for_Time_Dependent_Problems_second_order_case).
- Arpaia, Ricchiuto & Abgrall (2015), published pp. 508--509 and 512--513,
  Eqs. (28), (49)--(53): same common-beta structure; no explicit nonlinear
  beta_n/beta_* choice located there. The constant-advection starting point
  is explicit in the footnote to Eq. (26), with nonlinear extension discussed
  in Section 3.3.1. Local PDF remains the verified source from section 70.
- Warzynski, Hubbard & Ricchiuto (2015), *Runge--Kutta Residual Distribution
  Schemes*, DOI 10.1007/s10915-014-9879-0, Section 4 Eq. (8), and Section 5
  Eqs. (12)--(16), likewise use common unindexed distribution/test functions.
  Their main method solves global consistent-mass linear systems, distinct
  from the explicit shifted/global-lumped comparator. It cannot be used as
  blanket justification for our two-pass mixed F1 method.
  [Institutional PDF](https://nottingham-repository.worktribe.com/file/746355/1/WHR_JSC14.pdf).
- There is a concrete counterexample to saying ALL explicit RK2-RD freezes
  its coefficients: Ricchiuto (2015), *An explicit residual based approach
  for shallow water flows*, JCP 280:306--344, DOI 10.1016/j.jcp.2014.09.027.
  Section 4.3 constructs LLF limiting/distribution coefficients from the
  predictor spatial residuals, and from the corrector total residuals in the
  corrector, explicitly distinguishing both cases in the projection and
  limiting steps around Eqs. (43)--(47). These coefficients can differ.
  This is nonlinear LLF distribution, NOT Euler LDA beta evaluated at U*;
  it does not directly endorse our mixed LDA spatial/temporal convention.
  [Author PDF](https://www.math.u-bordeaux.fr/~mricchiu/exp-sw-revised.pdf).

Thus the precise literature statement is: common total-residual distribution
is clear in the checked LDA/F1 constructions, while its nonlinear state
evaluation is often omitted; broader nonlinear RK-RD permits stage-dependent
distribution. Do not infer deliberate evasiveness or a universal old-beta rule.

### Structural reason to prefer a common beta

Define the element total residual (conserved-density notation as above):

\[
\Phi^T=\frac{|T|}{3}\sum_j\frac{\delta U_j}{\Delta t}
+\frac12(\phi^{T,n}+\phi^{T,*}).
\]

Our mixed LDA candidate can be rewritten exactly as

\[
\Phi_{i,\mathrm{mixed}}^T
=\beta_i^{T,*}\Phi^T
+\frac12(\beta_i^{T,n}-\beta_i^{T,*})\phi^{T,n}.
\]

The second term sums to zero over the triangle when each stage satisfies
sum_i beta_i=I. It redistributes the update without changing its element
total, but is absent in a common-beta discretization. This makes a common
beta formulation closer to the published total-residual construction. It
does NOT prove that our mixed scheme is inaccurate, that beta_n outperforms
beta_*, or that either method inherits every convergence theorem unchanged.

Recommendation (Codex judgment, not an implemented/user-approved change):
prefer a coherent beta_n candidate when settling the static LDA/F1 thesis
baseline, because it matches the verified ASTRIX convention and removes an
unnecessary distribution choice lacking a demonstrated benefit. Do not
silently replace the current baseline or treat this as an urgent numerical
bug fix. Run a bounded comparison on the CURRENT Gauss3/glass equal-step
configuration first; the old Roe/jittered Yee experiment is not its substitute.

The old three-way experiment found ~0.13% changes in the density L1 error
scalar at dt=1/256, with all conventions giving fixed-mesh temporal orders
~0.993--0.997 and round-off conservation. It does not establish that coherent
beta_n repairs time order or improves robustness. Joint spatial/time
refinement and fixed-mesh temporal order are separate questions.

For implementation, new phi(U*) must still be computed from U*; only the
distribution and F1 operator would use old-state beta. This requires separating
the residual state from the distribution state, not freezing all of the
second sweep. There is no numerical requirement to add a mesh construction
or physical residual sweep. Any actual change must preserve rank-deficient
fallback, conservation, and MPI behavior. Hierarchy needs a precise local
interval-opening meaning of n; a shared nodal timebin or last primitive update
is not automatically that meaning. Moving geometry/topology is a separate
extension. Reusing beta_n does not remove frozen-node F1 behavior.
