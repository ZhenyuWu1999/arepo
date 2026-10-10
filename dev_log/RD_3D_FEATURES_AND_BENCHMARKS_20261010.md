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
This covers the shared hierarchy edits; it does not resolve the deferred
moving LDA/B K-refactor reproducibility issue. Full-mesh support is explicit;
active-only 3D mesh reconstruction and checkpointing an open RK stage remain
unsupported. No large-grid scaling or long-time convergence claim is made.
