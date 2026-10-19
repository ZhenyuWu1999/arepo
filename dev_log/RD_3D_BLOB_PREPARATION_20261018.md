# 3D tests for the mesh/hierarchy/MPI phase, and Blob preparation

Codex (GPT-6), with Zhenyu Wu; 2026-10-18, local Apple Silicon Mac.
Source HEAD `3d72127`, branch `feature/3d-moving-mesh`. No solver or thesis edit.
The user prioritizes the 3D mesh/moving-RD, hierarchical timestep and MPI
workflow; HLLC-RD and strong-shock remedies remain deferred.

## Test choices

| Test | Purpose in this phase | Useful checks |
|---|---|---|
| Oblique 3D entropy/density advection | Lowest-cost quantitative check of all three flux directions and periodic/rank crossings | Exact density translation, five-component conservation, fixed-mesh errors, equal-/mixed-bin and rank comparisons |
| Smooth shear with explicitly z-dependent perturbations | Exercise genuinely 3D shear evolution beyond the existing z-invariant Gresho/shear ICs | Transverse kinetic energy, spectra, conservation and resolution dependence; no exact nonlinear reference |
| Pressure-balanced Blob in a wind | Integrated cloud acceleration, contact/shear and bow-shock test | Three orthogonal slices, threshold-defined cloud mass, conserved totals, bin occupancy and rank agreement |

The first test can use the existing positive profile
`rho=1+.1 product_k sin(2*pi*x_k)` in a periodic unit cube, constant pressure
and velocity `(.3,-.2,.4)`. Its exact solution is the same density evaluated
at `x-v*t`. It offers a direct error norm before adding nonlinear mixing.
The current static test suite already has this family; use it to validate
new moving/hierarchy/MPI paths rather than treating previous static success
as validation of those paths.

## Blob sources and parameter reconciliation

Primary reference: [Morton, Khochfar & Wu (2023), section 5.3.1 and Figures
18–20](https://arxiv.org/html/2204.01757v2#S5.SS3.SSS1).
The published comparison uses N1, random vertices and resolutions starting
at 32³. Define `t_cr=2 R sqrt(chi)/v_wind` and `t_KH=1.6 t_cr`; count cloud
mass where `rho>.64 rho_cloud` and `T<.9 T_wind,initial`.

The checked-out predecessor supplies additional concrete IC constants in
`/Users/zhenyuwu/rdsolver/rd/setup3D.cpp` (BLOB block) and
`constants3D.h.TEMPLATE`:

| Parameter | Prepared value |
|---|---:|
| Periodic cube side | 10 |
| Cloud centre | (2.5,5,5) |
| Cloud radius | 1 |
| Cloud / wind density | 100 / 10 |
| Uniform pressure | 100 |
| Gamma | 5/3 |
| Wind x speed | 1.5*4.1 = 6.15 |
| Cloud x speed | 1e-8 |
| Both transverse speeds | 1e-7 |
| CFL in the predecessor's Blob template | .01 |

There is an inconsistency in the paper's numerical paragraph: it gives the
same density for cloud and background, while the preceding definition says
the contrast is ten. The local BLOB code uses 100/10, which is adopted here.
The paper rounds the wind speed to 6.2; the checked code's 6.15 is used
explicitly. With the prepared EOS, the actual Mach number is 1.5064 and
`t_cr=1.0283829789`. These choices must remain visible in any comparison.
The NumPy random seed is 68315; this does not reproduce the original CGAL
mesh/seed realization.

## What is supported now

Current AREPO 3D RD supports static periodic full-mesh N/lumped or LDA/F1
with `RD_RK2_TOTAL_RESIDUAL`, equal steps and the experimental frozen-dU
hierarchy, with small 1/2/4-rank evidence. It rejects the predictor-only
diagnostic and requires the RK2 path. Passive scalars and moving 3D RD also
remain excluded. Consequently this preparation uses **N/RK2**, not N1, and
the threshold cloud-mass definition does not track original cloud material.
It is a physical-setup adaptation until the update method and remaining
settings match. No compiler guard was removed to make the test run.

The new [driver](../tests/rd/run_3d_blob_pilot.py) prepares independent source,
Config/build/run directories, IC and parameter hashes. It supplies equal-step
N on one rank and natural-hierarchy N on one and two ranks. Source and
numerical assertions are unchanged; numerical failures remain nonzero exits.
Median-dual weights are `Masses/Density`; the IC `Masses` stores density under
`READ_MASS_AS_DENSITY_IN_INPUT`.

A 16³ random IC has only 14 cloud nodes, radius 1.6 mean spacings; this is a
workflow check. A separately prepared 32³ candidate has 140 cloud nodes and
radius 3.2 mean spacings. The latter IC has not been evolved or submitted to
a cluster. Larger/full-duration work belongs on Cuillin/COSMA with Linux
build/linkage provenance and the usual scheduler rules.

## Evidence and intended next use

- `../local_runs/rd_3d_blob_20261018_v1/`: initial 0.1 t_cr local attempt,
  CFL .01. The equal-step run was deliberately interrupted for scope/runtime
  after reaching approximately .01569; no numerical failure is claimed.
  Hierarchy cases were not launched. Original output and interruption reason
  remain archived.
- `../local_runs/rd_3d_blob_20261018_v2/`: shortened 0.01 t_cr workflow check,
  same IC/CFL/algorithm. Reuses the frozen v1 binaries after source/Config
  hash comparison, preserving `binary_source.tar` and reuse metadata.
  Consult `run_status.json` and `results.json` for actual status/results.

All three v2 runs completed to `t=.010283829789165462 = .01 t_cr` and the
analysis passed. Each saved three snapshots and reported 512 stage-1 records.
The equal-step h is `2.0085605057e-5`; its min/max differ only through subtraction
round-off. Coordinates stay fixed and the measured dual volume sums to 1000.

| Case | Maximum normalized conservation defect | Final min rho / p | Maximum bin ratio |
|---|---:|---:|---:|
| Equal-step N, 1 rank | 6.061e-15 | 9.61214 / 93.7874 | 1 |
| Natural hierarchy N, 1 rank | 3.614e-15 | 9.61127 / 93.7784 | 4 |
| Natural hierarchy N, 2 ranks | 3.614e-15 | 9.61127 / 93.7784 | 4 |

Between hierarchy 1/2-rank runs, every matched-ID primitive, extensive state
and dual-volume component agrees within `3.411e-15`, using
`abs(value_2-value_1)/max(1,abs(value_1))`; stage-1 times agree exactly.
The two hierarchy runs have identical threshold cloud mass histories, ending
at `.99070635` of initial measured cloud mass `450.43409`; equal steps end
at `.99070226`. No equality of the equal-step and mixed-bin trajectories is
asserted. These fractions are implementation diagnostics, not a cloud-lifetime
measurement. Saved states are positive and no raw-state assertion fired.

Sequential wall times were 68.9, 30.8 and 16.1 seconds; these small checks
are not a scaling or efficiency study. No full algebra suite was repeated;
only the test driver and documentation were added, with no production change.

The short check cannot measure disruption, KH/RT growth or convergence.
For a later matched physical comparison, start with 32³ and explicitly record
the method difference from N1. Save common normalized times, e.g. .5, 1 and
1.5 t_cr, and compare density slices and `M_cloud(t)/M_cloud(0)`. First establish
a static equal-step baseline, then add hierarchy and MPI separately. Moving
Blob follows the simpler moving uniform/advection geometry gates; it does
not replace those gates or require a new HLLC implementation.
