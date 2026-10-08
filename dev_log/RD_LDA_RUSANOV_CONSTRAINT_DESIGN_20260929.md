# Proposed entropy and oscillation constraints for the static blend

Author: Codex, 2026-09-29. User asked how to constrain the mixed correction and
check an entropy lower bound. This is a design/derivation, not an implemented
or native-validated extension. Source and default configurations are unchanged.
It builds on [the existing prototype](RD_LDA_RUSANOV_BLEND_20260929.md).

## Evidence from the archived run

Rechecked final snapshot SHA256 against `analysis/verification.json` in
`../local_runs/sedov_lda_rusanov_20260929_v1/`. Gamma=5/3, t=.05, static glass
128^2, nearest21 heating, initial minimum K=p/rho^gamma=1e-6. With relative
violation tolerance1e-8, all527 violating mixed nodes lie at radii
[.2776020557,.3123557137], outside the analytic shock radius .2579946312.
The mixed r<.1 region has K_min=89.3709842, median328.052186, max1178.02909;
the low control has K_min=18.0015514 there and no global violations anywhere.
Thus enforcing only the initial global minimum addresses exterior low-entropy
states but does not directly constrain the current noisy core. This does not
prove an entropy-limited evolution would leave the core unchanged.

## 1. Keep the existing conservative correction structure

Let U=(rho,mx,my,E), with E a total energy density, Q_i=S_i U_i and static
median dual area S_i>0. At either RK stage the current code supplies

    Q_i^accepted = Q_i^L + sum_{T contains i} ell_T C_i^T,
    sum_{i in T} C_i^T = 0,  0 <= ell_T <= 1.

The correction includes the F1 versus lumped temporal terms at the corrector;
it must not be replaced by limiting the spatial residual alone. A single
ell_T is shared by every vertex and conserved component in a triangle.

With d_i incident triangles, test the intensive segment

    V_i^T(ell) = (Q_i^L + d_i ell C_i^T)/S_i.

Take ell_T as the minimum accepted coefficient over its three nodes and all
constraints. The final U_i is the average of these d_i trial states. If every
node's allowed set is convex and contains U_i^L, that average remains allowed;
the triangle zero sum separately guarantees conservation. No pressure or
velocity clipping after the conservative update is required.

## 2. Entropy constraint and low-order endpoint

For a gamma-law ideal gas, specific entropy differs from c_v log K by a
constant. Impose K>=K_i^min, equivalently

    Psi_i(U) = E - |m|^2/(2 rho) - K_i^min rho^gamma/(gamma-1) >= 0.

For gamma>1 and K_i^min>0, Psi_i is concave on rho>0. Its nonnegative set is
convex. Check ell=1 first; when it fails, bisect the admissible segment from
ell=0 to obtain the largest accepted coefficient within numerical tolerance.
All density-positive conditions still apply. K_i^min is fixed during the line
search, not recomputed from each trial.

IMPORTANT implementation units: the current limiter receives extensive Q.
Either divide Q and its correction by S_i before evaluating Psi, or use

    Psi_i^Q(Q) = E_total - |P|^2/(2 M)
                - K_i^min S_i^(1-gamma) M^gamma/(gamma-1).

Positivity is homogeneous and did not require this area factor; the entropy
threshold does. Omitting S_i^(1-gamma) would impose a resolution-dependent
constraint unrelated to the physical specific entropy.

For the first diagnostic use the global initial K_min=1e-6 for this Sedov.
A stronger local bound uses the minimum over source-stage neighboring states.
At the corrector also include U_i^n because the low final state is a convex
combination involving both U^n and a forward step from U*. Do not require
K_i^{n+1}>=K_i^n at a fixed Eulerian node: entropy can advect through it.

The current Gauss-total low operator is only constructed to be positive.
Its observed lack of global violations is not a local entropy proof. Extend
the low-state construction before relying on an entropy limiter:

    Uin_T = Ubar_T - Phi_G/(3 alpha_T),
    K(Uin_T) >= min_{j in T} K(U_j^source).

Increase alpha_T until both positivity and this entropy condition hold.
The mean Ubar_T belongs to the same convex entropy set. For unequal states
with a strict entropy margin this supports the alpha->infinity construction;
uniform/equality cases require roundoff-aware treatment and explicit failure
handling. Do not assume a fixed iteration count always succeeds.

The forward low step is

    U_i^FE = (1-c_i) U_i^source + sum_T (dt alpha_T/S_i) Uin_T,
    c_i = dt sum_T alpha_T/S_i <= 1.

Hence source states and entropy-admissible Uin give the required local minimum.
The RK low corrector is .5 U_i^n + .5 FE_i(U*). Bounds must include all its
constituents. The timestep estimate must use the same increased alpha, and
actual stage CFL must be rechecked. A failed stage needs a smaller-step retry
or an explicit stop; increasing alpha after choosing dt does not waive CFL.
Always assert that the fully assembled U^L satisfies the selected bounds
before limiting. Do not quietly lower a failed entropy target to K(U^L).

## 3. Local bounds to control positive oscillations

Density and velocity do not obey an old-neighbor maximum principle for Euler.
Using only old density extrema would freeze an initially uniform density;
using only old velocity extrema would forbid acceleration from rest. Pressure
forces must be represented in the reference states used to choose bounds.

For a predictor, define B_i to contain U_i^source and the incident Uin_T;
optionally include neighboring source states to widen the bounds. At the
corrector include U_i^n as well. These are the constituents of U_i^L, so its
density is between their extrema, and its velocity is a density-weighted
average of their velocities. Candidate bounds are

    rho_i^min <= rho <= rho_i^max,
    v_{a,i}^min rho <= m_a <= v_{a,i}^max rho,   a=x,y,

where extrema are taken over B_i, with separately specified relaxation in
smooth regions. All these inequalities are affine in U. The velocity bounds
are our proposed additional numerical constraint, not a general Euler
maximum principle or a claim about the referenced method's implementation.
They may suppress physical extrema and introduce directional preferences;
their effect on smooth vortices needs its own validation. No knowledge of
the Sedov centre, analytic solution or expected v_t=0 belongs in the solver.

First compare density+entropy constraints, then add velocity bounds separately
if substantial radial/tangential scatter survives. Applying only a compression
sensor may miss noise persisting in the expanding post-shock interior.

## 4. Relaxation, diagnostics and validation

Strict local extrema and entropy bounds can damage accuracy in smooth regions.
Use geometry-aware smoothness/curvature estimates for an O(h^2) relaxation,
with positivity retained and shock regions constrained tightly. On irregular
glass, an unweighted neighbor Laplacian need not be O(h^2); use a reconstruction
that accounts for node positions and verify convergence. This relaxation is
not specified/validated here. If entropy is allowed below its selected minimum
by a tolerance, call the result a relaxed entropy bound; do not claim an exact
minimum principle. An additional strict global initial floor can itself limit
smooth isentropic tests and must not be assumed harmless to second order.

Per stage record separately for low, unlimited candidate and accepted states:
positive-state status; minimum log(K/K_bound); violation count and locations;
density/velocity bound violations; limiting fraction by active constraint;
and mass, momentum, energy budgets. Do not evaluate log K on invalid high
candidates. Validate the assembled accepted stage, not just trial segments.
Total physical entropy sum_i M_i log K_i is a useful periodic-domain diagnostic,
but neither its global sign nor an entropy minimum proves a discrete local
entropy inequality. Full entropy stability is a distinct property.

Proposed ablation order: existing positivity-only baseline; entropy-only;
entropy+density bounds; then add velocity bounds if needed. If the low operator
changes alpha for entropy, retain a matching low-only control and explicitly
separate that change from high-correction limiting. Use identical Sedov ICs,
CFL policy and final time; adaptive step counts can differ. Check r<.1/r<.2
velocity scatter, tangential RMS, shock density peak/width, exterior undershoot,
entropy violations, budgets and runtime. Retest uniform preservation, smooth
contact/Yee convergence and a boosted smooth case before considering moving
geometry. Fewer scatter points alone are not success if all sharper structure
has been diffused away.

## Source and status

Guermond, Nazarov, Popov & Tomas, *Second-order invariant domain preserving
approximation of the Euler equations using convex limiting*, §§4.1,4.6,4.7:
https://arxiv.org/html/1710.00417 . This supports auxiliary-state bounds,
concave entropy constraints and the need for relaxation. Their graph-based
low-order operator and pairwise correction are not our common-Gauss triangular
RD construction; the mapping above is a local derivation and proposal.

No new hydrodynamics run, compiled test or solver modification was performed
for this design. Only existing final snapshots were rechecked for the spatial
distribution of global entropy violations.
