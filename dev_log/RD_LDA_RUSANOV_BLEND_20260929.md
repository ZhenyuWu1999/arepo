# Static LDA/F1 + Rusanov: conservative positivity-limited prototype

Author: Codex, 2026-09-29. Zhenyu Wu requested investigation of LDA+Rusanov
in the existing code. This is an explicitly selected research branch inside
the solver, not a replacement of default LDA or N. No thesis changes.

## Scope and relation to the literature

The prototype uses the existing LDA/Gauss3 spatial operator and F1 corrector.
It constructs a common-Gauss low-order distribution, then limits the complete
element correction to an admissible low-order stage. This is our adaptation
of conservative convex limiting ideas; it is not a reproduction of SGH RD,
MARS or the MOOD paper's discretization. See the
[literature audit](RD_SEDOV_RUSANOV_LITERATURE_AUDIT_20260929.md).

This first experiment supports static, full, periodic 2-D meshes, equal
timesteps and one rank, without gravity, refinement, comoving integration or
source terms. It uses both RK sweeps in one solver call. Moving geometry,
MPI, hierarchy and topology remap remain outside this validation.

## Common-total low-order update

The old experimental Rusanov used a trapezoidal total. Mixing it directly
with LDA/Gauss3 using different element weights would not preserve shared-edge
flux cancellation. Instead both distributions now use the same Gauss3 total
Phi_G, retaining the existing LDA quadrature and Roe upwind directions.

For each triangle T:

    Ubar = (U0+U1+U2)/3,
    Uin = Ubar - Phi_G/(3 alpha_T),
    phi_i^low = alpha_T (U_i-Uin)
              = Phi_G/3 + alpha_T (U_i-Ubar).

Alpha starts from half the maximum endpoint normal acoustic/advection bound
over all vertices and opposite normals. It is doubled until Uin is finite
and belongs to G={rho>0, E-|m|²/(2rho)>0}; at most64 attempts are allowed.
The viscosity is evaluated with differences to preserve uniform data.
Unlike the prior trapezoidal operator, this baseline's proof uses one
admissible inflow state per element, not pair LF split states.

For the actual nodal area S_i, a sufficient forward-step restriction is

    C_i = dt sum_{T contains i} alpha_T / S_i <= 1.

The timestep selector includes this bound before Courant scaling/dyadic
rounding. Both actual stage bounds are checked again. Inflow construction
does not license exceeding CFL; a violated stage bound aborts. No pressure,
density or energy clipping is used, and MinGasTemp remains zero.

## Complete RK-stage correction

The common stage opening has valid U^n; the predictor is limited before
primitive recovery. Denote its accepted result U* and dU=U*-U^n.
The existing corrector starts from U*+dU/2 and subtracts the element total
residual. The two candidates are

    R_i^H = T_i^F1(dU) + 1/2 phi_i^LDA(U*),
    R_i^L = |T| dU_i/(3 dt) + 1/2 phi_i^low(U*).

Their element sums agree. After global assembly, the low candidate is

    U_low^{n+1} = 1/2 U^n + 1/2 [U* - dt S^-1 sum_T phi^low(U*)].

Thus both constituents are admissible under the checked static CFL. The
F1/lumped difference is included in the limited correction; merely mixing
spatial residuals would not provide this result. With no limiting in either
stage the scheme recovers the existing LDA/F1 update up to roundoff.

## Element limiting

Let C_i^T=-dt(R_i^H-R_i^L), or the analogous spatial correction at predictor
stage. Sum_i C_i^T=0. Numerical closure is enforced at roundoff level.
Let d_i count incident triangles, and Q_i^L=S_i U_i^L denote the fully
assembled low-order extensive state. Choose one coefficient ell_T for all
four components and all three vertices, so that for every i in T

    Q_i^L + d_i ell_T C_i^T is admissible,    0<=ell_T<=1.

The final update is Q_i=Q_i^L+sum_T ell_T C_i^T. It is the average of the d_i
admissible trial states, and the element corrections sum to zero. Hence the
limiter preserves both admissibility and conservation. Bisection enforces
density/internal-energy bounds of 1e-12 times their low-state values, with
a further small coefficient safety margin. These are correction constraints,
not modifications of stored density/pressure. The limiter does not enforce
entropy or exclude positive overshoots.

This element-based convex decomposition is deliberately simple and may
reject more correction than a better pairwise/iterated limiter. Its number
of limited elements is a fraction of the whole box, not just the shock.
The logged correction-weighted acceptance uses a sum over conserved
components in these code units; it is a diagnostic, not a physical norm.

## Code, frozen provenance and tests

- `src/hydro/rd_lda_rusanov.h`: common-total fallback and segment limiter.
- `src/hydro/residual_distribution_solver.c`: guarded stage assembly and
  conservative element limiting, with per-stage bounds and budget checks.
- `src/time_integration/timestep.c`, `src/main/proto.h`, `defines_extra`:
  explicit option plumbing. No default Config change.
- `RD_LDA_RUSANOV_BLEND=1`: limited LDA/F1 high-order correction.
- `RD_LDA_RUSANOV_BLEND=0`: common-Gauss low-order control; still computes the
  LDA candidate, so timings are not an optimized low-order cost comparison.
- Option absent: existing LDA reference.
- Runner: `examples/Sedov_2d/run_blend.py`; analysis: `analyze_blend.py`.

Frozen archive: `../local_runs/sedov_lda_rusanov_20260929_v1/`. It contains
the actual dirty-tree source snapshot and patch, per-file hashes, independent
builds/configs/binaries/linkage, initial conditions and run metadata. The
analysis script was added after source freeze and is archived separately
with the figures. OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1; at most4 independent
single-rank solvers, with at most2 of the 128² Sedov runs together.

The new compiled helper test passed2000 randomized strong-contrast cases:
independent Gauss boundary integration, common-total closure, admissible
near-CFL updates, exact uniform residuals and conservative limited patch
assembly. All5 existing algebra targets passed. The first unqualified
`make check_rd` invocation used system Python without NumPy and failed at
import; rerunning with the documented21cmfast Python passed. This was a
test-environment failure, not a solver failure.

Native campaign: three uniform gates, two glass128² nearest21 Sedov cases
(t=.05, gamma5/3, rho1, pbg1e-6, Ehot1, CFL.1, adaptive equal steps, cap.01),
and seven smooth density-advection checks. Sedov ICs are byte-identical to
the previous static/moving comparison, including hot IDs and dual-mass
energy normalization. The smooth problem is a constant-pressure advected
contact with rho=1+.2sin(2pi(x+y)), v=(.37,-.21), p=1, gamma5/3, unit periodic
box, regular staggered rows16²/32²/64², t=.1 and cap1/8192. It is not a Yee
vortex test.

## Completed results

All12 native attempts completed successfully; all60 new saved states are
finite, positive and on unchanged coordinates. Three uniform defects are
5.55e-16. EOS consistency is exact in the saved fields. No solver remains
running. Both scientific runs reached t=.05 with the original ICs:

| Static method | Steps | rho_min | raw rho_max | radial-mean rho peak, dr=.005 | final dE/E |
|---|---:|---:|---:|---:|---:|
| LDA/F1 + limited common-Gauss Rusanov | 4689 | .01911264 | 3.791111 | 2.798253 | -2.22e-16 |
| Common-Gauss Rusanov only | 2476 | .12461361 | 2.006290 | 1.961227 | +6.66e-16 |
| Previous trapezoidal Rusanov, archived | 3051 | .12483651 | 2.002159 | 1.957390 | -2.22e-16 |

For r<.05 (130 nodes), the mixed density mean is .027686 versus .135722 for
the new low-order control and .004353 for the analytic values sampled at
those same nodes. The mixed pressure mean is1.607414, versus1.443428 for low
order and1.605099 analytically. Thus core pressure and density improve, but
core density remains too high. The mixture's radial density profile is
sharper; raw peak3.79 must not be mistaken for the radial-mean peak2.80.
Changing quadrature alone leaves the low-order profiles nearly unchanged.

The improvement has a clear limit: the mixture has a substantial density
undershoot ahead of the shock (radial mean around.6 where the background is1)
and much larger radial-velocity scatter, including negative central samples.
Final minimum pressure is5.03e-12 despite pbg1e-6. The ideal-gas entropy proxy
K=p/rho^(5/3) falls to3.47e-5 of the initial minimum, with527 nodes below
that minimum by more than relative1e-8; the common-Gauss low control has none.
This demonstrates why positivity alone is insufficient. This is a useful
conservative positive prototype, not a finished non-oscillatory Sedov method.

All9378 mixed and4952 low-order scientific stage checks pass. The maximum
actual CFL sums are.100857/.099992; their sufficient bound is1, not the
opening selector's Courant factor. The mixed minimum internal-energy density
over stages is2.86e-12. Its largest limited-correction global budget defect
is8.44e-15; saved mass/energy changes are at roundoff. Averaged over both
stages/time,1.12% of all-box elements are limited; most limiting occurs in
the corrector, rising to roughly3.4% at the end. The all-component correction
acceptance diagnostic averages.566. This is not a spatial shock-only statistic.

Smooth contact density L1 errors for N=16,32,64 are
2.7978823e-4,6.4517329e-5,1.5767725e-5: orders2.1166 and2.0327. The mixed and
unlimited LDA reference fields differ by at most2.45e-14. This demonstrates
recovery of existing LDA on this smooth test, not general Euler/Yee or
irregular-mesh convergence. At N32, the low-order error is.0308811.

Native runtimes are705.06s mixed and388.58s low-control; different adaptive
step counts and unnecessary high-candidate work in the control preclude
interpreting this as an optimized method cost comparison. Binary SHA256:

- mixed: `3f857323e8efa066db77ee0be5e345a45ea151b9593df5e770e05b29a2fea186`
- low: `5ed7db7fb24f8323245fe5c553916af642b51692a95e16c0b705907d2f6c7906`
- LDA reference: `a43f1c249b469eeaa6b60fb668f9f4277ae9d0e452e9681d5fe4182becf75cd1`

Figures were visually inspected; axes include the undershoots and velocity
scatter rather than concealing them:

- `../local_runs/sedov_lda_rusanov_20260929_v1/analysis/lda_rusanov_profiles.png`
  and matching PDF: full profiles plus core zoom, means and faint scatter.
- `../local_runs/sedov_lda_rusanov_20260929_v1/analysis/lda_rusanov_diagnostics.png`:
  energy budgets and stage-specific limiter activity.
- `analysis/verification.json`: hashes,60 snapshot checks, stage statistics,
  entropy diagnostic, convergence and sampled analytic comparisons.

The next research step is an entropy-minimum and/or justified oscillation
constraint on the correction, ensuring that the low-order endpoint satisfies
the selected bounds too. Neither is supplied by this positivity-only test.
After that, moving geometry and conservative positive remapping require
their own validation. No moving version has been implemented or tested here.

## Follow-up: why the mixed result has much greater scatter

Read-only audit, Codex, 2026-09-29 (log3 §168). The user asked why the LDA
scatter exceeds Rusanov. The plotted blue result is the positivity-limited
LDA/F1 + Rusanov mixture, not an unlimited pure-LDA Sedov run. Both compared
runs have static, identical glass coordinates; connectivity change cannot
explain their difference. Final snapshot hashes were checked against the
original verification record, and median dual areas agree to <1e-15.

The archived `analysis/scatter_audit.py` writes `scatter_audit.json`. It uses
the same initial energy centroid (0.5006033128, 0.4999065174), volume weights
S=mass/rho, and removes a weighted linear radial trend separately in bins of
width .005. The residual RMS measures scatter rather than the smooth radial
slope; it is not an error norm against the analytic solution. Tangential
velocity is projected directly from the Cartesian velocity, without binning.

For .05 <= r < .10, t=.05, 386 identical nodes, well inside the analytic
shock radius .257995:

| Diagnostic | LDA/F1 + limited Rusanov | Common-Gauss Rusanov |
|---|---:|---:|
| Mean radial velocity | .468728 | .476766 |
| Detrended radial velocity RMS | .158645 | .00460087 |
| Tangential velocity RMS | .0655025 | .00374668 |
| Mean density | .0525804 | .185905 |
| Detrended radial momentum-density RMS | .00701744 | .00130639 |
| Detrended pressure RMS | .00935031 | .00176026 |

Thus the radial scatter ratio is34.48 and tangential RMS ratio17.48. A change
of origin to the nominal box centre gives tangential RMS .065954/.005599;
the conclusion survives this centring sensitivity. Over the larger interior
.025 <= r < .2, radial scatter is .125685/.0043824 and tangential RMS is
.057891/.0037052. This rules out interpreting all scatter as shock-position
smearing in radial bins. The near-front density spread may still include
angular front displacement; this audit does not separate that component.

The numerical interpretation is lower damping combined with a positivity-only
constraint. Rusanov's alpha(U_i-Ubar) damps local conserved-variable differences,
including momentum, whereas the LDA/F1 correction cancels much of this damping
without imposing monotonicity. Irregular glass geometry and finite-node energy
injection provide possible angular perturbations; their individual causal
contributions are not isolated here. Morton et al. §2.2.3 explicitly discusses
LDA's non-TVD behavior and shock oscillations:
https://arxiv.org/html/2204.01757v2 .

The current admissibility region only imposes positive rho and internal-energy
density. Positive oscillations, entropy-minimum violations and nonradial velocity
are allowed. Lower central density also increases velocity sensitivity:
delta v ~= (delta m - v delta rho)/rho. Momentum scatter itself is greater too,
so dividing by lower density is not the sole explanation. The observed entropy
violations establish a missing constraint, not a proof that entropy limiting
alone would remove velocity noise. F1-specific effects and shock-generated
versus locally generated perturbations require additional controlled tests.
No solver changes, new hydro runs, thesis edits or Git-history operations were
performed in this follow-up.
