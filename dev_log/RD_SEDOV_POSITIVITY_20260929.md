# Sedov and Euler positivity in RD: literature, derivation and native prototype

Author: Codex, 2026-09-29. Requested by Zhenyu Wu. This is solver research;
no thesis changes or default-scheme replacement are authorized by this report.

**Provenance clarification (same-day follow-up, log3 §165):** The implemented
low-order Rusanov kernel is a local prototype, not a reproduction of the
published second-order SGH RD/MARS Sedov scheme. The MOOD paper supports a
fallback architecture but contains no Sedov test. See the
[source and blending audit](RD_SEDOV_RUSANOV_LITERATURE_AUDIT_20260929.md)
for the differences and the assessment of LDA+N versus LDA+Rusanov.

## What earlier work actually establishes

1. **Morton, Khochfar & Wu (2023), §5.2.3.** Their Sedov calculation uses a
   circular injection region on a random point distribution. N1 succeeds;
   N2 is nearly identical, and blending strongly favours N. Pure LDA1/LDA2
   are unstable. The stated reason for spreading the injection is directional
   asymmetry from a single vertex's few connections. This is a successful RD
   Sedov example, not a general Euler positivity theorem for Roe N.
   [Primary text](https://arxiv.org/html/2204.01757v2#S5.SS2.SSS3).

2. **Abgrall, Lipnikov, Morgan & Tokareva (2020), SGH RD, §8.3.** A genuinely
   Lagrangian, staggered-grid RD method computes Sedov with MARS artificial
   viscosity. Their gamma=1.4 example obtains density peaks 4.908 and 5.459
   on 16² and 32² cells, compared with the jump 6. This is a different
   discretization: velocity/position and thermodynamics occupy different
   finite-element spaces; it has its own energy-conservation construction.
   MARS cannot simply be inserted into our collocated conservative LDA/N.
   [Primary manuscript](https://arxiv.org/html/1811.00057v1#S8.SS3).

3. **Bacigaluppi, Abgrall & Tokareva (2023), MOOD RD.** High-order candidate
   updates are recomputed with a cascade ending in classical Rusanov, rather
   than assuming that N is a universally safe fallback. Density/internal
   energy are checked. §4.1.2 and Appendix A discuss dissipation and CFL;
   the accessible v2 Appendix A also explicitly qualifies the status of the
   full formal argument. Do not cite it as a proof of our ALE/F1 algorithm.
   It supports the fallback architecture; no Sedov example was found in this
   text. [Primary text](https://arxiv.org/html/1902.07773v2#S4.SS1.SSS2).

4. **Guermond, Nazarov, Popov & Tomas (2018).** Graph viscosity supplies an
   invariant-domain low-order Euler update; convex limiting controls
   conservative high-order corrections. This separates the low-order
   guarantee from the high-order accuracy mechanism.
   [Primary paper](https://arxiv.org/abs/1710.00417).

5. **Guermond, Popov & Saavedra (2020; Euler study published online 2021,
   volume 2023).** ALE graph viscosity and convex limiting update the nodal
   masses consistently with geometry. The Euler study explicitly assumes a
   time-independent connectivity array (§3.1); mesh smoothing maintains that
   connectivity. Therefore it is not already a solution for AREPO's flips.
   [Euler study](https://doi.org/10.1007/s42967-021-00165-y),
   [general ALE method](https://doi.org/10.1016/j.jcp.2019.108927).

The scalar RD use of “positive/monotone” must not be substituted for the Euler
admissible set G = {rho>0, E-|m|²/(2rho)>0}. Our own failed N Sedov runs in
log3 §156 demonstrate why that distinction matters in this implementation.

## Implemented experiment: Rusanov, with the existing lumped RK stages

`RD_RUSANOV_LOW_ORDER` explicitly selects a new spatial distribution while
using the existing N/lumped temporal branch. It is **not Roe N**, not LDA,
and not a high-order limiter. The flag requires equal timesteps, full mesh,
tree timesteps and a single MPI rank; this experiment covers periodic 2D
hydro in the lab frame, static or the current Arpaia ALE geometry. Default
N, LDA/Gauss3/F1 and B behavior is unchanged when the flag is absent.

For each triangle T let n_j be its inward length-weighted opposite normal,
and w_T the mean mesh velocity. Define G_j=F(U_j)-U_j tensor w_T. Set

    Phi_T = 1/2 sum_j G_j . n_j,
    Ubar = (U_0+U_1+U_2)/3,
    phi_i = Phi_T/3 + alpha_T (U_i-Ubar),
    alpha_T >= 1/2 max_{j,k} [ |(v_j-w_T).n_k| + c_j |n_k| ].

This uses trapezoidal physical fluxes. It deliberately does not silently
change the existing LDA Gauss3 residual. The scalar dissipation has no
matrix inverse and bounds every vertex state, rather than just a Roe state.
The implementation evaluates the equivalent difference form

    phi_i = sum_{j!=i} [(G_j-G_i).n_j/6 + alpha_T (U_i-U_j)/3],

which gives exactly zero for identical input states. The sum is Phi_T, so
the spatial update is conservative on a static periodic mesh.

### Sufficient positive-state decomposition

Let d_T=alpha_T/3, c_j=n_j/6 and

    Ubar_ij^T = (U_i+U_j)/2 - (G_j-G_i).c_j/(2 d_T).

The speed a=d_T/|c_j|=2 alpha_T/|n_j| exceeds the two endpoint
|v-w_T| normal wave-speed bounds. The bar is the average of the two
Lax–Friedrichs split states, hence belongs to the convex Euler admissible
set for admissible endpoint states. An Euler step with positive nodal
coefficient S_i can be written

    U_i^FE = (1 - 2dt sum_{T,j!=i} d_T/S_i) U_i
             + sum_{T,j!=i} (2dt d_T/S_i) Ubar_ij^T.

There are two neighbours in each triangle. A sufficient CFL condition is

    C_i = (dt/S_i) sum_{T contains i} 4 alpha_T/3 <= 1.

The native timestep selector adds this current-mesh bound to the tree bound;
CourantFac and dyadic rounding remain active. Both physical sweeps also
check the **actual** stage bound, all pair bars, density and internal-energy
density before primitive recovery. The checks abort rather than clipping or
relaxing the conditions. No positive-pressure floor or energy injection was
added. An opening-mesh estimate by itself does not guarantee the future
midpoint/predictor bound; automatic rollback/retry is not implemented.

### The moving corrector needs a separate weight check

Write S_i for the actual modified dual-area coefficient and
M_i=sum_T |T_mid|/3. With a_i=M_i/S_i and b_i=3/2-a_i, the existing lumped
corrector is algebraically

    U_i^{n+1} = (a_i-1/2) U_i^n
                 + b_i [U_i* + dt/(2 b_i) L_i(U*)].

Static mesh has a_i=1 and b_i=1/2 (SSP RK2). For moving geometry we check
0<b_i<=1 and the second Euler-like step's CFL, C_i*/(2 b_i)<=1.
The positive endpoint/divisor rescaling leaves U unchanged. These checks
make the positivity argument applicable to the accepted temporary stages;
they do **not** establish conservation through reconnecting geometry.

## How to recover high-order LDA accuracy after the fallback is validated

Do not blend each conserved component independently. Use a common scalar
coefficient for each conservative correction. In physical endpoint Q,
the desired form is

    Q_i = Q_i^L + sum_j ell_ij A_ij,
    A_ji=-A_ij,  ell_ji=ell_ij,  0<=ell_ij<=1.

With positive weights lambda_ij summing to one, enforce for every pair

    Q_i^L + ell_ij A_ij/lambda_ij in G,
    Q_j^L - ell_ij A_ij/lambda_ji in G.

The assembled update is a convex combination; opposite pair corrections
cancel exactly. Density supplies a linear bound on ell; internal energy
uses its concavity along the conservative-state segment (a bracketed scalar
solve is sufficient). Predictor and corrector, including F1 temporal
antidiffusion, both need this treatment before the candidate is consumed.

Two integration details must be resolved first:

* Our new low-order total uses trapezoidal flux; LDA uses Gauss3. Thus their
  element correction does not sum to zero. One must construct a common-total
  positive fallback (with an admissible element inflow state and its CFL), or
  distribute the quadrature difference as paired shared-edge flux corrections.
  Simply blending element residuals with unrelated local ell is insufficient.
  One concrete common-total candidate is

      U_in^T = Ubar^T - Phi_G^T/(3 alpha_T),
      phi_i^L = alpha_T (U_i-U_in^T).

  Here sum_i phi_i^L=Phi_G exactly. Increase alpha_T until U_in^T is
  admissible; for admissible Ubar this is possible in exact arithmetic as
  alpha tends to infinity. Then dt sum_T alpha_T/S_i<=1 makes the predictor
  a convex combination of U_i and the element inflow states. The actual
  corrector weights and updated alpha must still satisfy their own CFL.
  This is a useful route to retaining the Gauss3 total in a future limiter;
  it has not been substituted into the native trapezoidal tests here.
* Both endpoint candidates must conserve the **same physical Q** on the new
  geometry. The current divisor conversion and flip handling do not ensure
  that for general nonuniform states. A conservative positivity-preserving
  remap of old/new median-dual volumes is a separate requirement; a flux
  limiter cannot repair a nonconservative baseline merely by preserving it.

This high-order limiter is a concrete next design, **not yet implemented**.
The old MOOD LDA-to-N debug option remains shelved (log3 §17.5).

## Validation and artifacts

The compiled C kernel passed 5,000 randomized tests, covering admissible
strong-contrast states, arbitrary triangle normals and ALE velocities,
near-bound CFL steps, zero uniform residual, and independent boundary-flux
consistency/conservation. Worst normalized flux defect: 1.764e-16.
All five `make check_rd` programs passed. Native results are recorded below.

* `../local_runs/sedov_positivity_20260929_v1`: preserved setup/build failure
  (new header-guard macro initially missing from the option whitelist).
* `../local_runs/sedov_positivity_20260929_v2`: corrected frozen source,
  independent build/header/binary provenance, original byte-identical ICs.
* Campaign runner: `examples/Sedov_2d/run_positivity.py`.
* Spatial kernel: `src/hydro/rd_rusanov.h`.

Original settings: unit periodic box, SWIFT glass128², gamma5/3, rho1,
P_background=1e-6, hot energy1, nearest21 nodes or radius.05/130 nodes,
targett=.05, CourantFac=.1, cap.01, adaptive equal dyadic steps. All runs
use one MPI rank, OMP/BLAS1, at most four simultaneous solvers. No IC
smoothing, reduced pressure contrast or enlarged injection region was used
to rescue an already failing case.

## Completed native results

All **nine** native attempts completed: three uniform gates, four full Sedov
runs, and two matched short baseline replays. No solver remains running.
The early build-whitelist failure in v1 was a setup failure, not a numerical
failure. The corrected v2 source was frozen before building; all current
production-file hashes still match that archive.

| Seed | Mesh | Steps to t=.05 | Final rho_min | Final rho_max | Delta M/M | Delta E/E |
|---|---|---:|---:|---:|---:|---:|
| 21 nodes | static | 3051 | .12483651 | 2.00215852 | -3.33e-16 | -2.22e-16 |
| 21 nodes | moving | 3118 | .19600852 | 2.63043575 | -.0023970673 | -.0241469964 |
| 130 nodes, r=.05 | static | 2780 | .12687864 | 2.00651253 | -3.33e-16 | +2.22e-16 |
| 130 nodes, r=.05 | moving | 2762 | .17086387 | 2.63380608 | -.0023576918 | -.0131544695 |

All four maintain final p_min approximately 1e-6. Across **23,422 science
stage checks**, internal-energy density remains at least 1.5e-6 (roundoff
aside). Maximum checked dimensionless CFL coefficients are .09998565,
.10427703, .09994040, .10556576 respectively in table order; the sufficient
bound is 1, not the requested CourantFac=.1, which acts on the opening-mesh
estimate. Minimum moving corrector weights b are .49735979 and .49731476;
the coefficients stay in the required convex range.

The old moving Roe-N runs failed at t=.00226440 and .00828857. Both new
moving cases reach .05 with the **same original ICs**, so the change has a
real native robustness benefit. It does not establish that unlimited LDA
is now positive; this experiment replaces the spatial operator entirely.

Static mass, both momentum components and energy are conserved to roundoff.
Moving energy deficits are **2.4147%** (21 nodes) and **1.3154%** (130 nodes);
mass deficits are **.2397%** and **.2358%**. Moving endpoint momentum errors
are (1.56088e-4,4.97310e-4) and (1.43034e-4,6.04378e-4).
The existing geometry/ledger treatment was retained. These numbers expose a
remaining conservation issue, not a conservative Sedov validation, and do
not isolate its cause to flips alone.

The moving shell is narrower than the static Rusanov shell, with peak
density about2.63 versus2.00; both remain below the exact jump4. The central
moving samples are sparse, producing gaps in some radial-bin means. The
finite seed and numerical diffusion also affect the profiles. The earlier
static N/130-node solution reached a higher peak (2.42) than static
Rusanov: robustness was gained with additional diffusion, not uniformly
improved accuracy.

Uniform-state maximum component error is 1.11e-15. With the new flag absent,
all five snapshots of the short t=.001, 21-node N calculation are bitwise
identical by particle ID to the original archived binary (density, pressure,
velocity, mass, coordinates and totals). This regression is a static N
check; it is not a new MPI, LDA-convergence or hierarchy validation.

`analysis/verification.json` verifies all nine cases and **45 unique saved
snapshots**, inputs/config/binary hashes and every emitted stage bound.
`baseline_replay.json`, `uniform_verification.json` and
`source_integrity.json` retain the independent gates. Final figures:

* `analysis/nearest21_profiles.png` and `nearest21_density.png`;
* `analysis/disk005_profiles.png` and `disk005_density.png`.

The 21-node profiles and density map were visually inspected. The native
physics sources, all failed/successful artifacts and logs are retained.
No default Config, thesis file, commit, push or COSMA state was changed.
