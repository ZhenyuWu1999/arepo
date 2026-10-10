# Static tetra LDA, hierarchy, MPI and benchmark integration

Author: Codex, 2026-10-10. User requested continuing 3D LDA, hierarchical
stepping and MPI, deferring the separately documented 2D floating-point
compatibility issue. No thesis edits or standalone-rdsolver edits.

## 1. LDA/F1 convention

Use the inward **unit** normal and opposite triangular face area A_i:
K_i = (A_i/3) A_Euler(n_i). Both shear modes have the repeated advective
eigenvalue. The static element total is the exact divergence integral of the
P1 Roe-parameter field, Phi = sum K_i Uhat_i. With Sminus = sum K_i^-:

- spatial LDA solves Sminus x = Phi and distributes phi_i = -K_i^+ x;
- the corrector temporal target is t = (V/4) sum dU_i/h;
- full-rank F1 solves Sminus z = t and distributes T_i = -K_i^+ z;
- deficient-rank F1 uses T_i = (V/4)dU_i/h. An arbitrary temporal target need
  not belong to the range of Sminus; a bare pseudoinverse does not establish
  conservation. Spatial solve compatibility and raw element conservation
  remain mandatory even when SVD is used.

Equal-step predictor uses the full h spatial update. Corrector preparation
recovers W* without primitive floors, adds the local half dU, then deposits
-h[T_i + phi_i(W*)/2]. Therefore sum T_i = t is essential. N uses the same
lumped temporal target. No positivity limiter or conservation repair is added.
`rd_euler.c` shares the Roe assembly with N; the pre-existing N arithmetic
sequence is retained. The two-dimensional adapter keeps its existing code.

The independent algebra test forms Euler Jacobians by complex step and
spectral projectors by matrix polynomials. It checks LDA against the independent
operator, F1 against a full-rank solve, deficient-rank zero output (caller must
lump), and the total against exact face Gaussian quadrature. It covers 700
random triangle/tetra states, gamma 1.4 and 5/3, including nonzero residuals at
zero mean velocity. Native evidence is archived under
`../local_runs/rd_3d_extension_20261010_v1/`.

## 2. Benchmark reference scope

Reference setups are pinned to SWIFT **v2026.04**, with fetched source files
preserved in `references/` in the archive:

- [SodShock_3D](https://github.com/SWIFTSIM/SWIFT/blob/v2026.04/examples/HydroTests/SodShock_3D/makeIC.py):
  gamma 5/3, (rho,p,vx) left=(1,1,0), right=(.125,.1,0); periodic box
  2 x .5 x .5, contact at x=1, different left/right glass sampling.
- [SedovBlast_3D](https://github.com/SWIFTSIM/SWIFT/blob/v2026.04/examples/HydroTests/SedovBlast_3D/makeIC.py):
  gamma 5/3, unit cube, rho=1, p=1e-6, E=1 replacing internal energy of
  the nearest 15 equal-mass particles in a 64-cubed glass.
- [GreshoVortex_3D](https://github.com/SWIFTSIM/SWIFT/blob/v2026.04/examples/HydroTests/GreshoVortex_3D/makeIC.py):
  gamma 5/3, rho=1, cylindrical stationary vortex independent of z; standard
  piecewise azimuthal velocity and pressure with added pressure P0=0.

AREPO adaptations must record their actual coordinates, median-dual masses,
resolution, box and injection normalization. They are benchmark-family
references, not comparisons against an executed SWIFT binary. A 3D mesh with
an extruded flow tests tetra assembly but alone does not exercise arbitrary
3D dynamics; the oblique smooth advection and spherical blast complement it.

## 3. LDA milestone evidence

`lda_v2/`: 12 native cases, 8³/16³, t=1/32, equal steps and one rank.
Rest, advecting uniform state, stationary pressure perturbation, smooth
oblique density advection, always-SVD and **actual** halved-dt checks pass.
LDA 8³/16³ density L1 and timestep sensitivity are recorded in the machine
readable `results.json`/`comparisons.json`. N8/N16 final fields remain
byte-identical to `native_static_v3`. Full `make check_rd` passes.
`lda_v1/` preserves the initial compile failure (equal-step stage enum was
only declared for the split/hierarchy hooks); corrected to the existing
0/1 stage convention before `lda_v2/` was frozen. No failed numerical gate
was reclassified as a pass.

## 4. MPI milestone

The minimum-ID primary-copy ownership rule was already dimension-generic.
The new `rd_timestep.c` assembles median mass and spectral sums on that same
complete owned tetra set, reads current ghost primitives, and exports each
remote vertex contribution to its primary. Global minimum CFL diagnostics use
MINLOC; stage totals, minima and tetra counts now use global reductions.
Flux and dual-volume exchanges retain the existing AREPO ownership machinery.
No global particle replication or matrix inverse is introduced.

`mpi_v2/`: 20 native cases pass, including the previous one-rank suite and
N/LDA uniform/advection on 2 and 4 ranks. Step sequences are identical and
maximum matched-ID field/dual-volume differences are below 3e-15. Conservation
is below 3e-15. `mpi_v1/` preserves the build-check failure from the new header
guard missing in `defines_extra`; that registration was fixed before v2.
This establishes small periodic full-mesh static MPI gates, not moving-MPI or
large-scale efficiency. Domain decomposition is enabled in the native run.

## 5. Static hierarchical milestone

The tetra adapter now uses the existing static finest-element-bin clock and
complete-star predictor policy for **all five** conserved components. Vertex
predictors and remote predictor deposits use RD_NVAR. Corrector primitives
include z momentum/kinetic energy. Persistent median-dual coverage includes
boxSize_Z. Opening/closing endpoint checks and star-bin exports are inherited
from the existing static hierarchy.

For a tetra clock h_T, both calls carry h_T/2. N uses the two spatial residuals;
LDA closing adds 2(T_F1 - V dU_i/(4 h_T)). Its element sum is zero, and equal
bins reduce to the concentrated equal-step F1 update. Vertices with a faster
incident star stay frozen in the stage state; their integrated conserved
ledger still receives all deposits. This is the existing **experimental
frozen-dU hierarchy**, not a new proof of multirate convergence order. The
actual final stage residual sum is now checked independently against Phi
(hierarchy), or Phi/2 + temporal target (equal-step corrector).

`hierarchy_final/`: **50 cases** pass. N/LDA equal-bin degeneration, controlled
one-level refinement and an actually mixed natural-bin pressure patch each
run on 1/2/4 ranks. All five totals at saved common endpoints are conserved to
<=2.443e-15; uniform defect <=6.662e-16; maximum MPI/equal-bin field difference
8.882e-15 and step sequences match. The natural patch uses rho=1,
p=1+8 exp(-|x-.5|²/.12²), v=(.3,-.2,.4), 8³, cap=1/64, CFL=.2,
t=1/32. Its actual finest dt=1/1024 and max star ratio=2, proving the cap
did not merely force equal bins. Controlled split uses x<.5 with cap=1/512.

`hierarchy_v1/` also passed 56 cases, but its natural advection/uniform setups
remained equal-bin. `natural_v1/` preserves a deliberately failed **test
coverage assertion**: increasing the cap alone still produced one bin on
those 8³ fields. No solver error or assertion loosening was used; the pressure
patch supplies genuine different CFL clocks in the final campaign.

`regression2d_before/after/`: frozen ce0433d versus the final hierarchy source,
N/LDA static controlled two-bin Yee48 and uniform random, t=1/32, two ranks.
All four final primitive/mass/coordinate/total comparisons are byte-identical.
An additional audit verifies **every PartType0 dataset in all 12 saved
snapshots** byte-for-byte after ID sorting; see
`regression2d_particle_dataset_audit.json`.
This covers the shared hierarchy edits; it does not resolve the deferred
moving LDA/B K-refactor reproducibility issue. Full-mesh support is explicit;
active-only 3D mesh reconstruction and checkpointing an open RK stage remain
unsupported. No large-grid scaling or long-time convergence claim is made.

## 6. Reduced SWIFT-family results and unresolved cold-blast diagnostic

`swift_v2/` contains 11 attempted cases: 8 complete (including uniform volume
probe) and 3 cold Sedov attempts stop. These are **16³ jittered unit-cube
adaptations**, not SWIFT runs or equal-resolution solver comparisons. The
same deterministic seed928 coordinates are used for all families; gamma5/3,
CFL=.1, cap=1/2048. Injection replaces the internal energy of 15 nearest
vertices with constant specific energy E0/sum_hot_dual_volume. Measured hot
volume=.0035820883858286557, u_hot=279.16675756973734; removed background
energy=5.3731325787e-9. Initial total energy=1.0000014946268678. The frozen
uniform probe establishes the dual volumes and preserves all node IDs.

| Completed one-rank test | End | Steps | Weighted error | Min rho / p |
|---|---:|---:|---|---|
| Sod N | .08 | 256 | central-half L1 rho .07759, vx .19136, p .10178 | .17851 / .19014 |
| Sod LDA | .08 | 256 | central-half L1 rho .06481, vx .23676, p .06847 | .06217 / .01875 |
| Gresho N | .1 | 512 | vector-velocity L1 .04436, pressure L1 .03666 | .99403 / 5.21497 |
| Gresho LDA | .1 | 512 | vector-velocity L1 .01614, pressure L1 .01323 | .99689 / 5.06408 |

Errors use median-dual volumes. Sod's central-half window excludes the
periodic seam wave, which has not reached it at .08; its reference is the
repository's analytic gamma5/3 Riemann solver in **actual unit-box coordinates**.
The box differs from SWIFT's 2 x .5 x .5, and sampling differs on both sides.
LDA's lower rho/p errors do not imply uniformly better shock quality: vx error
is larger and density undershoots the right-state .125. Positivity on this
coarse case is not a monotonicity or general positivity proof. Gresho's radial
reference is stationary and cylindrical; it alone is not a fully 3D flow.

Completed-case normalized conserved-total drift <=4.542e-15. N one/two-rank
field differences are 5.441e-15 (Sod) and 1.244e-14 (Gresho). Actual equal timesteps are .08/256 for Sod and .1/512 for Gresho,
rather than the nominal cap. The two-rank N
Sod hierarchy remains equal-bin because the cap controls the clock: this is
another degeneration check, not mixed-bin shock validation.

Cold Sedov **does not pass**:

- N, one rank: stops at the second endpoint t=.0001171875, stage0;
  solve defect=1.7196068e-33, conservation defect=1.7195162e-33,
  absolute-product scale=1.8192238e-21.
- LDA, one rank: stops at t=.00005859375, stage1;
  solve defect=8.2850358e-34, conservation defect=8.2850017e-34,
  scale=7.9781740e-22.
- N, two ranks: stops at that first endpoint, stage1;
  solve defect=1.3961782e-33, conservation defect=1.3961817e-33,
  scale=7.5974487e-22.

The successful preceding predictor/stage has positive rho and p>=1e-6. These
failures are the pure-kernel **raw solve/distribution audit**, not a detected
negative-pressure or mass failure, nor sufficient evidence of an incorrect
K formula. Their defects are close to or above the existing 4096 epsilon
product-scale limit despite extremely small absolute values. Singular-value
selection and the appropriateness of that product-scale bound for a cold,
strongly scaled Euler SVD need a focused follow-up with captured element
inputs. The inputs/rank spectra were not captured here, so no dominant cause
is claimed. Different ranks stopping on different elements do not establish
large physical MPI error. No threshold, floor, conservation repair or timestep
acceptance policy was changed to make this benchmark pass.

`swift_v1/` preserves the parameter-setup rejection: the volume probe's cap
exceeded its total runtime. v2 fixes only that cap. Initial v2 analysis products
are retained; `analysis_v2/` contains the corrected dense analytic profiles,
explicit failed-Sedov panel, JSON summary and final analysis script. The CLI
now exits **2** after saving results when any benchmark fails; the independent
analysis returned that expected failure status. Archived numerical runs used
the hierarchy source before the additional adapter stage-sum assertion; all
shared Euler/CFL/state modules and hierarchy update algebra are identical.
The definitive final feature suite and 2D regression use the final assertion.
`final_source_audit.json` records source-file comparison for each archive.

Only small local functional checks were run. Per user's steering, larger
resolution sequences, long integrations and MPI performance studies belong
on COSMA/Cuillin. The Mac drivers preserve frozen inputs/configs/source but
still use the local `otool` build helper; Linux provenance/linkage adaptation
and the host's documented SYSTYPE are required before cluster builds.
