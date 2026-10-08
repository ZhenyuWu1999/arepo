# Sedov: Rusanov literature provenance and LDA blending assessment

Author: Codex, 2026-09-29. Requested by Zhenyu Wu: identify what the cited
authors actually did, then assess LDA+N and LDA+Rusanov blending. Literature
and current-code audit only; no new solver, native run or thesis edit.

## Sources and limits of the evidence

- [Abgrall, Lipnikov, Morgan & Tokareva, *Multidimensional staggered grid
  residual distribution scheme for Lagrangian hydrodynamics*](https://arxiv.org/html/1811.00057v1):
  §§5–8 use second-order staggered Lagrangian RD, quadratic Bernstein
  kinematics, linear thermodynamics, MARS directional viscosity, and an
  internal-energy residual correction enforcing total-energy conservation.
  §8.3 deposits energy in the origin cell; gamma=1.4, background pressure
  1e-6. Sedov density peaks are 4.908/5.459 on 16²/32² cells, versus exact6.
  These are MARS results, not globally applied first-order Rusanov results.
  Cell counts and gamma differ from our full-domain nodal experiment.
- [Bacigaluppi, Abgrall & Tokareva, *“A Posteriori” Limited High Order and
  Robust … Schemes for … Gas Dynamics*](https://arxiv.org/html/1902.07773v2):
  §4.1 uses the local cascade Galerkin+jump → Rusanov-PSI+jump → classical
  Rusanov, recomputing rejected candidates from valid old data. Eq.32 blends
  limited and low-order residuals in characteristic variables. Bernstein
  representation and deferred correction supply high order. No Sedov test
  appears in §5. Appendix A explicitly leaves the full framework's formal
  positivity proof open. Eq.35 has a Galerkin weak residual plus viscosity;
  it is not verbatim our Phi/3 kernel.
- [Guermond, Nazarov, Popov & Tomas, *Second-order invariant domain preserving
  approximation of the Euler equations using convex limiting*](https://arxiv.org/html/1710.00417):
  §4 limits antisymmetric high-order corrections to an admissible low-order
  graph-viscosity update using symmetric pair coefficients. This is relevant
  to conservative positivity limiting, not direct evidence for our ALE
  discretization or its changing connectivity. No Sedov test was found.
- [Morton, Khochfar & Wu, §5.2.3](https://arxiv.org/html/2204.01757v2#S5.SS2.SSS3):
  LDA Sedov is unstable; their blend heavily favours N and gives essentially
  the N result. Thus LDA+N is already tested there, without improved Sedov
  profiles from blending.

The earlier local experiment is a **locally constructed low-order Rusanov
prototype**, guided by fallback/invariant-domain ideas. It is not a
reproduction of the successful SGH RD Sedov algorithm. Any earlier shorthand
that equated these two should be corrected accordingly. The cited SGH work
also does not validate AREPO-style edge flips or our topology repair.

## What is in our code

`src/hydro/rd_rusanov.h` applies, on every triangle,

    phi_i^R = Phi_trap/3 + alpha_T (U_i-Ubar),

with endpoint ALE wave-speed bounds, pair-state admissibility checks, and
the CFL/stage conditions recorded in `RD_SEDOV_POSITIVITY_20260929.md`.
It does not contain PSI redistribution, MARS viscosity, a MOOD cascade or
limited high-order corrections. RK2 time integration does not remove the
first-order spatial diffusion of this distribution.

The existing `B_SCHEME` in `residual_distribution_solver.c` already blends
LDA and N; its equal-step corrector includes F1/lumped temporal blending.
Its classical sensor uses residual ratios, not an Euler admissibility
constraint. `RD_B_SCALAR_THETA` uses one scalar for all four components but
does not by itself make the assembled update positive. The old B mathematics
note's unqualified description of N as positivity preserving must not be
read as a theorem for the current nonlinear Euler/ALE implementation.
Native strong-Sedov N failures are contrary evidence for using it as a safe
fallback here. No legacy mathematical note or thesis text was rewritten.

## Assessment of the two blends

Writing theta for the low-order fraction,

    phi_i^B = (1-theta_T) phi_i^LDA + theta_T phi_i^low,
    0 <= theta_T <= 1,

does not by itself guarantee positivity. The high-order endpoint can be
inadmissible; a shock sensor is not a bound on density/internal energy.
LDA+N may improve moderate problems but has no reliable safe endpoint in
the present strong-Sedov experiment. LDA+Rusanov has a tested admissible
low-order endpoint and is therefore the better starting point for limiting.

For conservative state U=(rho,mx,my,E), use the coupled admissible set

    G = { rho>0, I(U)=E-(mx^2+my^2)/(2rho)>0 }.

At a fixed positive volume, the segment from an admissible low-order update
toward a finite high-order candidate always has an admissible initial
portion. Density gives a linear bound; I is concave and can be bounded with
a bracketed scalar solve. This explains why adaptive blending can work;
it does NOT justify choosing an independent nodal coefficient, which can
destroy global conservation, or accepting a nonfinite high-order candidate.

### Conservation and quadrature

For elementwise blending to retain a common total, both distributions must
sum to the same Phi_T and use the same element coefficient for all vertices.
Our LDA default uses Gauss3, while the new Rusanov uses trapezoidal fluxes.
With different local weights, blending these different totals need not
cancel contributions on a shared edge. Either construct a positive
low-order operator with the common Gauss3 total, or represent the quadrature
difference using conservative shared-edge corrections. The common-total
inflow-state construction in the earlier positivity report is a proposed
route, not an already validated replacement.

For example, if complete stage corrections C_i^T sum to zero on a triangle,
they can be decomposed into pairs A_ij^T=(C_i^T-C_j^T)/3. Then
sum_j A_ij^T=C_i^T and A_ji^T=-A_ij^T. On a fixed mesh, with Q_i=S_i U_i,
the target form is

    Q_i^new = Q_i^low + sum_j ell_ij A_ij,
    ell_ij = ell_ji in [0,1].

Use positive weights lambda_ij summing to one over the corrections at i.
Require U_i^low+ell_ij A_ij/(S_i lambda_ij) in G at both pair endpoints;
then their convex assembly stays in G and the extensive pair changes
cancel. A common scalar must act on density, momentum and energy for this
convex-state argument. This is a design for adapting limiting to our
operator, not a claim that our present code implements the cited algorithm.

### Time integration, oscillations and mesh reconnection

LDA's F1 temporal terms differ from the Rusanov/lumped terms. Limit complete
stage corrections, including temporal differences, before either RK stage
is consumed. Blending only the final spatial residual cannot inherit the
low-order stage argument. Moving geometry also needs the actual modified
dual-area weights and their convexity/CFL checks.

Positivity alone permits large positive overshoots. Add a justified local
oscillation/entropy criterion if needed, while checking that it relaxes on
smooth solutions; otherwise the blend can remain needlessly diffusive.
Do not claim recovered second order without a smooth convergence test.

Flux blending does not fix the existing topology conservation defect.
The moving Rusanov21 experiment loses 2.4147% energy; the old conservative
repair then fails with negative pressure. A conservative, positive remap
is separately required. Applying a limiter after a nonconservative baseline
only preserves that baseline's budget, not the correct old physical total.

## Recommended next experiment, not yet performed

First establish static-mesh LDA+Rusanov with common conservative totals,
coupled positivity limiting and complete RK stage treatment. Use the same
glass128²/21-hot-node Sedov parameters as the archived comparison. Measure
radial profiles, conservation, positivity, and where/how much the limiter
activates, alongside a smooth-flow accuracy gate. Then extend to moving
geometry, auditing flux and remap contributions separately. An LDA→N→Rusanov
cascade is possible, but N can only be an optional intermediate candidate,
not the final admissible fallback. No performance gain is yet demonstrated.

## Follow-up: mesh motion versus our AREPO ALE mesh (log3 §166)

The SGH paper's §3 explicitly assumes a bijective material mapping and leaves
remapping outside its scope. Position and velocity share continuous kinematic
basis functions; dx_a/dt=u_a. Eq.35c uses two-stage position integration.
Thermodynamics uses a discontinuous element-local space; density follows
rho J=rho_initial. This is a material-mesh formulation, not a reconnecting
Delaunay mesh. The Gresho example (§8.2) illustrates distortion at t=.65.
[Primary sections 2–3 and Eq.35](https://arxiv.org/html/1811.00057v1).

Our current source instead sets generator velocity in
`src/mesh/set_vertex_velocities.c`: fluid velocity plus a half-step pressure
acceleration predictor, then optional regularization. The current moving
Sedov Config enables centroid drift, sound-speed scaling and face-angle
regularization. `src/time_integration/predict.c` drifts the generators with
the stored interval velocity. Thus describing this particular configuration
as exactly w=u is inaccurate; it is quasi-Lagrangian. The reconstruction of
Delaunay connectivity can exchange neighbours. Our conservative variables
(rho,rho vx,rho vy,E) share nodal locations and the physical extensive
bookkeeping uses median-dual areas, not the native Voronoi FV volumes.

Even setting the generator velocity to the local fluid velocity would not
make a changing median-dual star a persistent material control volume.
Reconnection changes its membership independently of continuous particle
motion. Consequently the SGH density/Jacobian relation and energy correction
cannot be transplanted to repair our flips. Borrowing reduced dissipation or
high/low limiting ideas is feasible research; adopting its full staggered
framework would require a different state layout, geometry and evolution
operator. No claim is made that their benchmark isolates the effect of mesh
motion alone, or that t=.65 is a measured failure time. No code/run changes.
