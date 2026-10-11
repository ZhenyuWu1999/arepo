# Moving tetrahedra: geometry, Campoli conservation and reconnection

Author: Codex for Zhenyu Wu, 2026-10-11. Starting commit: `530543b`.
This is the first preparation milestone for moving 3D, reviewing Claude's
[plan](RD_3D_MOVING_MESH_PLAN_FOR_CODEX_20261011.md), especially M0/M1.
The production Euler/linear solve and the native ALE adapter are unchanged.
The tests below are independent mathematical models, not native moving-RD runs.

## 1. Decision on scaling and corrections to the proposed gates

The user prefers not to make rescaling a prerequisite. We retain the current
unscaled solver for this preparation and the initial warm/smooth moving gates.
Claude's [cold-Sedov review](RD_3D_EXTENSION_CLAUDE_REVIEW_20261010.md) supplies
good evidence for a separate conditioning improvement: the captured compatible
system has an unscaled residual of 1.72e-33, just above the 1.65e-33 audit
tolerance; similarity scaling reduces it to 1.2e-38. That improvement does not
establish geometric conservation, cure a sliver inversion or enforce positive
pressure. His scaled N/LDA native runs subsequently stop at negative pressure.
The cold unscaled failure remains a recorded limitation. An initial moving
gate encountering the same failure must be diagnosed, not passed by loosening
the audit. No scaling or 2D arithmetic decision is made here.

For full-rank systems, `D^-1 S D z = D^-1 b`, `y = D z`, is an equivalent
linear system. For a singular compatible system, a Euclidean minimum-norm
solution in scaled coordinates need not map to the unscaled minimum-norm
solution. Exact nodal products can nevertheless be independent of this choice
when the null space is annihilated by every K_i^+. Numerical SVD cutoffs are
also not invariant under a nonorthogonal similarity: exact rank is unchanged,
but computed rank, the LU pivot ratio and the F1 fallback can change. Thus
"physically meaningful rank" needs a stated norm/unit convention and tests;
it is not an automatic consequence of scaling.

Three changes to M1 are needed:

1. The **full directional K** and the frozen-stage **contour total** are linear
   in the area vectors. K^+/K^- and the N/LDA distributions generally are not.
   Computing them once from mean vectors is a conservative scheme choice,
   not exact quadrature of the time-varying distributed residual.
2. A fixed Eulerian affine density has time-varying values at moving nodes.
   Frozen-state geometry alone cannot prove exact nodal preservation by the
   complete nonlinear N/LDA RK2 method. We verify the exact affine Reynolds
   transport identity, and retain a native affine accuracy check for later;
   we do not promise unconditional nodewise error <=1e-12.
3. A wave coefficient evaluated with mean vectors can underestimate the
   largest coefficient during the step. It is not by itself a safe moving CFL
   upper bound. Section 5 gives a conservative geometric bound.

## 2. Conventions and time polynomials

Work on one coherently unfolded, fixed-connectivity tetrahedron with linear
trajectories `x_i(s)=x_i^0+s d_i`, `d_i=h w_i`, `s in [0,1]`. Require positive
signed volume throughout. No absolute value is used to hide an inversion.
Let N_i(s) be the **inward area vector** opposite vertex i, including the
triangle's area (half a cross product). Then

\[
 V(s)=\frac{\det(x_1-x_0,x_2-x_0,x_3-x_0)}6,\quad
 \nabla\lambda_i=\frac{N_i}{3V},\quad
 \sum_iN_i=0,\quad \sum_i x_i\otimes N_i=3V I.
\]

These definitions match `rd_simplex_geometry`: unit normal `N_i/|N_i|`, face
area `|N_i|`, K multiplier `|N_i|/3`, and P1 lumped mass `V/4`. The gradient
divisor 3 and mass divisor 4 must remain distinct. AREPO's legacy
`calculate_tetra_volume` returns 6V, not this V.

Cross products give quadratic N_i(s); determinant multilinearity gives
`V(s)=a0+a1 s+a2 s^2+a3 s^3`. Hence

\[
 \overline N_i=\int_0^1N_i(s)ds
 =N_i(1/2)+\frac{N_i(0)-2N_i(1/2)+N_i(1)}6.
\]

Simpson or two-point Gauss is exact for these area vectors. Use the norm of
the **mean vector**, not the mean face area, when constructing a directional
operator from it. If a mean vector is zero, the proposed normalized interface
cannot be used and must report that case. The correction is zero for static
geometry; native bitwise collapse will additionally require reusing the same
production geometry arithmetic and bypassing a normalize/reconstruct cycle.
The Python check proves bitwise collapse only of its own area-vector formula.

The Campoli temporal mass remains the endpoint trapezoid, not the true mean V:

\[
 M_T=\tfrac12(V_0+V_1),\quad
 M_T-V(1/2)=a_2/4+3a_3/8,\quad
 M_T-\int_0^1V(s)ds=a_2/6+a_3/4.
\]

Replacing this mass by a Gauss volume average would change the time scheme.
The old 2D `delta_area` velocity-cross-product check is not the 3D identity.
Its replacement can use the determinant coefficients above.

## 3. Endpoint ledger, mesh transport and contour total

`sigma_h=sum_i lambda_i w_i` is P1 in space; its divergence is spatially
constant on a tetrahedron at each time, but generally **not constant in time**.
With face mean velocity `w_face,i=(sum_{j!=i} w_j)/3`,

\[
 \dot V=V\nabla\cdot\sigma_h
 =-\sum_iN_i\cdot w_{face,i}
 =\tfrac13\sum_iN_i\cdot w_i.
\]

For nodal conserved values frozen within a stage, set
`U_h=sum lambda_i U_i`, `Ubar=sum U_i/4`, `wbar=sum w_i/4`. The exact identity is

\[
 \int_0^h\!\int_T\nabla\cdot(\sigma_h U_h)\,dxdt
 =(V_1-V_0)\overline U
 +\frac h3\sum_i(\overline w\cdot\overline N_i)U_i. \tag{1}
\]

The first term uses **endpoint volumes only**. The second is the exact integral
of `sigma_h.grad U_h`, since the spatial mean of sigma_h is wbar. An independent
quadratic triangle-face rule for the product sigma_h U_h, followed by two-point
time Gauss, checks (1). This is more than checking volume change alone.

The current baseline's contour residual uses **P1 interpolation of nodal
physical fluxes**. It is not the integral of `F(P1 U)` and not the P1-Z Roe
total. In laboratory variables its mean advective ALE total is

\[
 \Phi(U)=\frac13\sum_i\sum_a\overline N_{i,a}
             [F_a(U_i)-\overline w_a U_i]. \tag{2}
\]

It is linear in N for frozen U. The divergence theorem expresses its physical
part through each face's average of the three nodal F values. Those face
contributions cancel between adjacent tetrahedra; periodic images must use
the same states, generator velocities and coherent face geometry. The mesh
term by itself is not a shared-face flux: combine it with the endpoint ledger
using (1). Only that combination telescopes.

For the comoving solve, use the five-component Galilean transformation

\[
 G_bU=(\rho,m-\rho b,E-b\cdot m+\tfrac12\rho|b|^2),\qquad b=\overline w.
\]

Pressure and internal energy are invariant, and
`G_b F_a(U)-b_a G_b U = F_a(G_b U)`. Thus the contour total in the element
frame maps back to (2), with all three momenta included. Reconcile a raw N
distribution with this target by adding `(Phi_contour-sum phi_N)/4` to each
vertex, as the current 2D baseline does with divisor 3. This is a declared
distribution choice. If using a Roe total instead, the mesh-interpolation
correction is `-sum_i (wbar.N_i)(U_i-Uhat_i)/3`; the contour baseline already
replaces that total and must not add this correction again.

## 4. Complete Campoli equal-step conservation

This section includes both RK sweeps, not just a geometric flux. On fixed
connectivity define nodal masses `m_i^0=sum_T V_T^0/4`, `m_i^1=sum_T V_T^1/4`.
Prepare the ledger on `m^1 U^0`. Let predictor residuals satisfy
`sum_i phi_i^{T,0}=Phi_T(U^0)`, and define

\[
 \delta U_i=-h\sum_{T\ni i}\phi_i^{T,0}/m_i^1,\qquad U_i^*=U_i^0+\delta U_i.
\]

The corrector starts from **Q*=m^1 U***, adds the local `+m^1 deltaU/2`, and
deposits `-h(T_i^T+phi_i^{T,*}/2)`. A lumped or F1 temporal distribution must
have the same element sum

\[
 \sum_iT_i^T=\frac{M_T}{4h}\sum_{i\in T}\delta U_i,\quad
 M_T=(V_T^0+V_T^1)/2.
\]

Summing the update and using the predictor relation gives

\[
 \sum_i(Q_i^1-Q_i^0)
 =\sum_i(m_i^1-m_i^0)U_i^{mid}
 -\frac h2\sum_T[\Phi_T(U^0)+\Phi_T(U^*)],\quad
 U^{mid}=U^0+\delta U/2. \tag{3}
\]

The physical face totals in the second term cancel separately at each stage.
The mesh part is linear in U, so (1) applied to the frozen nodal values U_mid
turns the remainder into a sum of time-integrated shared-face transport fluxes,
which cancels too. Therefore (3) is **exact global conservation** on a periodic
fixed-connectivity mesh, regardless of the spatial distribution or an F1/lumped
choice, provided their declared element sums hold. It does not require
`average K^+=K^+(average N)`.

For a uniform state the contour and consistent raw spatial residuals vanish,
`deltaU=0`, and the endpoint-divisor ledger preserves U pointwise. Static
geometry has `m^0=m^1=M` and recovers the existing static RK2 mass algebra.
The existing static 3D Roe total can still differ from the contour total for
nonuniform states: native sigma=0 field equality is not implied.

The oracle runs a periodic 3^3-node/162-tetra model with arbitrary conservative
spatial splits and either lumped or nonuniform conservative temporal splits.
It also uses midpoint vectors with the same endpoint masses as a negative
control. Uniform preservation alone cannot detect this error: the nonuniform
conservation control is needed.

For a fixed Eulerian affine density `rho(x)=a+g.x`, nodal values satisfy
`rho_i(s)=a+g.x_i(s)` and are not frozen. The exact Reynolds flux has the product
of quadratic N(s) and linear rho_i(s), so time Gauss2 integrates it exactly.
Mean N times midpoint rho omits their correlation. For the unit tetra expanding
as x(s)=(1+s)x(0), with g=(.2,-.1,.3), the exact integral is 17/12 while this
product gives 1.4. This is a counterexample to that quadrature claim; it is
**not** a counterexample to the full Campoli RK2 method. Its nodal affine
accuracy still needs a scheme-specific proof or native measurement.

## 5. Split K and moving CFL

For frozen Roe state/frame, the full matrix is
`K_i=(sum_a N_{i,a}(A_a-wbar_a I))/3`. It commutes with time averaging.
Splitting eigenvalues introduces `|N|`, eigenvectors depending on N/|N|, and
`max/min(v_rel.N +/- c|N|,0)`. Consequently K^+, K^- and their solves need not
commute with averaging. The complex-step/spectral-polynomial oracle constructs
a positive-volume deformation where the full K difference is round-off but
the K^+ difference is about 3.9e-3. Mean-vector upwinding remains a viable
conservative baseline by (3); nonlinear accuracy/positivity are separate gates.

The usual tetra coefficient
`alpha_i(N)=(|v_rel.N_i|+c|N_i|)/3` is convex in N. Its value on mean N generally
underestimates the maximum during the interval. Write a quadratic face vector
in Bernstein form with controls

\[
 B_0=N(0),\quad B_1=2N(1/2)-(N(0)+N(1))/2,\quad B_2=N(1).
\]

N(s) is a convex combination of these controls, so
`max_{i,k} alpha_i(B_k)` bounds every instantaneous face coefficient for a
frozen Roe state. This is a geometric upper bound, not a proof of a full
nonlinear RK stability condition. A native CFL policy must also bound the
relevant nodal masses and states. Do not silently use mean-vector alpha as
the stepwise maximum.

## 6. Inversions and slivers

The minimum of cubic V on [0,1] occurs at an endpoint or a real root of its
quadratic derivative. Handle lower degree, repeated roots, and endpoints.
Old/mid/new checks are insufficient: the oracle has
`V(s)=(s-.18)(s-.32)(1+.1s)/6`, positive at all three of those samples but
negative in between. For each newly selected tetra, M2 should record both
its pulled-back V0 and this interval minimum, using consistent orientation
chosen at the new time. Campoli mass positivity alone is insufficient.

The future diagnostic must distinguish a robustly negative minimum from a
value indistinguishable from zero under determinant/coefficient round-off.
The present Python root logic is not a certified near-zero geometry predicate.
For this milestone it is tested on random well-separated positive volumes and
explicit lower-degree/repeated-root/hidden-inversion cases. Record
`q=V/(sum_i |N_i|)^(3/2)` at each geometry time; a regular tetra has q≈.0068.
Scaling the Euler solve does not improve this geometric quality.

## 7. Cavities at a common time and five-component transfer

Compare old and new connectivities at **the same positions/time**. Positive
tetrahedra must tile the same cavity with the same boundary/domain; deleting
and inserting points is excluded. A cavity is a connected component of the
vertex unions of removed/inserted tetrahedra. Let `a_i=sum_old V/4`,
`b_i=sum_new V/4`, `delta m_i=b_i-a_i`. Exact integration of 1 and x gives

\[
 \sum_i\delta m_i=0,\qquad \sum_i\delta m_i x_i=0. \tag{4}
\]

This holds independently of the flip type. Unchanged tetrahedra outside the
cavities contribute identical masses. Summing every component's delta m must
reproduce the full old/new mass difference. An ID-only sorted quadruple is
usable only while periodic geometry is uniquely represented; duplicates are
a diagnostic failure, not permission to merge different periodic images.
Invalid pulled-back tessellations are not covered by (4).

For full old nodal star mass g_i, `g_i+delta m_i>0`, and five-component states,
`D=sum_i delta m_i U_i` is the P1 integral defect. Donors have delta m<0,
receivers have delta m>0, with equal transferred mass r. Let U_D and U_R be
their respective |delta m|/delta m weighted averages. Low order copies donors
and sets receiver Q to `g_i U_i+delta m_i U_D`; it is a convex state mixture
on the new positive mass and conserves all components. High modes are

- mode 0: `U_i^H=U_i-D/sum_j(g_j+delta m_j)`;
- mode 1: donors unchanged, receiver
  `U_i^H=U_i+delta m_i(U_D-U_R)/(g_i+delta m_i)`.

Since `r(U_R-U_D)=D`, mode 1 conserves too. Equation (4) makes D=0 for constant
or spatially affine conserved fields; both high modes then reproduce them.
Use one cavity theta for all five components. Internal energy is
`e=E-(mx^2+my^2+mz^2)/(2rho)`. It is concave on rho>0, so convex low-order
mixtures retain positive density/internal energy and the fractional input-min
bounds. A convex blend with the largest admissible theta preserves conservation;
no clipping of U or E is involved. Optional density hull/entropy bounds can
restrict theta further. The baseline leaves those two options off.

The oracle checks 2-3, 3-2, 4-4 and larger SciPy Delaunay changes with a fixed
triangular hull and moved interior points. Both triangulations are evaluated
at x_new, rejecting inverted old pullbacks. This is synthetic connectivity
evidence, not AREPO cavity statistics or periodic registry validation.

## 8. Evidence and implementation handoff

Reproduction: `tests/rd/test_moving_tetrahedra.py`, included in `make check_rd`.
Requires NumPy/SciPy, using the existing local `21cmfast` Python environment.
Run with `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1`; `--output` creates a new
JSON file and refuses overwrite. Archives are under
`../local_runs/rd_3d_moving_math_20261011_v*/` with frozen source/provenance.
Detailed measurements and failed setup attempts are recorded in log3 §240.

Final independent results (`v3/results.json`):

| Check | Evidence |
|---|---|
| 300 moving tetrahedra: geometry, GCL, frozen transport, affine Reynolds, Galilean map | all normalized defects <=1.666e-15 |
| Periodic complete Campoli model, exact mean vectors | conservation <=1.322e-16, uniform error exactly zero in this model |
| Same model, midpoint-vector nonuniform control | conservation defect 3.114e-9 |
| Full / positive-split K averaging control | 7.772e-16 / 3.922e-3 |
| Hidden interval inversion | old/mid/new all positive; minimum -8.371e-4 at s=.250239 |
| 171 cavities, 1026 transfer cases | five-component conservation <=6.083e-16, 748 limited cases |
| Cavity coverage | 50 each of 2-3, 3-2, 4-4; 21 cavities from 20 Delaunay pairs, up to 20 vertices |

Transfer states include random pressure over eight decades, an exact 1e8 input
energy contrast, and counter-streaming three-component momenta. Uniform/affine
high transfers have theta=1 and normalized changes <=1.777e-16. Full frozen
`make check_rd` passes. No native hydro run is claimed for this milestone.
The periodic ledger uses a unit cube, 3 cells per axis with six Freudenthal
tetrahedra per cube, random periodic generator velocities, h=.02 and gamma=1.4.
Its reported conservation defect is `max_k |sum_i(Qnew-Qold)_k| /
sum_{i,k}|Qold_ik|`; uniform error is the largest absolute conserved-density
change. Transfer conservation is normalized separately per component by
`sum_i g_i|U_ik|`, with `eps*sum_i g_i rho_i` only for a zero/tiny component.
Geometry denominators are the appropriate volume/area/product scales stated
in the oracle; the split-K control reports absolute matrix-entry differences.

`v1` preserves a failed manufactured-control magnitude check: the deformation
gave a split-K difference .0007685, smaller than the specified .001 gate.
Doubling that deformation gives .003922 without reducing the gate, and its
volume stays positive. `v2` preserves a model implementation failure: the
corrector started from Q^0 rather than Q*, omitting the predictor ledger. This
was corrected against `rd_state.c`; it was not a production solver failure.
`v3` freezes the final executable tests/Makefile/solver before running them;
this report and handoff notes were added afterwards.

The next implementation boundary is M2's standalone simplex registry and
diagnostic-only native FV mesh run. Record cavities, periodic key duplication,
pulled-back/interval inversions and sliver measures before selecting their
policy. M3 can use mean-vector N upwinding, contour totals and endpoint Campoli
masses, with (1)--(3) as conservation gates. Moving hierarchy, cross-rank
cavities, strong-shock positivity and the full 2D campaign remain separate work.
Local tests stay small; substantial native campaigns belong on COSMA/Cuillin.

The mathematical oracle above is the evidence for these new deductions. The
time-scheme context is the project's existing
[ALE form selection](RD_ALE_FORM_SELECTION.md) and
[DGCL audit](RD_moving_mesh_DGCL_mathematical_audit.md). The author-hosted
[Campoli et al. chapter](https://www.math.u-bordeaux.fr/~mricchiu/sf-draft.pdf)
is the primary reference for the predictor/corrector formulation; its 2D
formula is not treated as a proof of the new tetra identities or native code.
Published equations (5)--(8), p.116, were cross-checked in the user's
local `2017_Book_ShockFitting.pdf`; the equation pages were rendered for visual
inspection and stored in `v3/references/`. The new proofs use no quoted text.
The trailing `=0` printed in its equation (7) cannot hold for a general
volume-changing element; our uniform-expansion example has delta V=7/6. We
use the endpoint-volume/swept-flux equality, not that extra zero, and replace
the 2D midpoint geometry by the exact mean vectors in the new 3D derivation.
