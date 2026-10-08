# Sedov: AREPO MMFV versus moving/static RD, 2026-09-29

Author: Codex. User requested a local AREPO moving-mesh finite-volume run and
comparison with moving/static RD. ENZO was mentioned as context, not run.

## Outcome

Standard AREPO moving Voronoi FV completed t=.05 in179.293 s,1179 steps. A
separate uniform-flow gate completed in1.315 s. The MMFV profile has a sharper
shock, much lower central density, and central pressure/velocity much closer
to the cylindrical analytic solution than the present low-order Rusanov RD.
Mass and energy are conserved to roundoff. Existing moving/static RD21 and
SWIFT21 outputs were reused with verified provenance; no RD or SWIFT rerun.

All cases have glass128² positions, periodic unit square, gamma5/3, rho0=1,
pbg1e−6, initial velocity0, Ehot1, the **same nearest21 heated IDs**, and t=.05.
The new MMFV uses Voronoi cell masses; RD uses median-dual nodal masses; SWIFT
uses equal particle masses. MMFV's hot area is.001279857917756399, with
u_hot781.3367297465393 and p_hot520.8911531643595. RD21 p_hot520.8929463 differs
by only.000344%. Each method's hot energy is normalized separately to1.
The cold region contributes about1.5e−6 to total box energy.

## Method and reproducibility

Archive: `../local_runs/sedov_mmfv_20260929_v1/`.
The current AREPO working tree was frozen before compilation, preserving the
existing dirty edits and the new untracked Rusanov header. This is an MMFV
build with RESIDUAL_DISTRIBUTION absent, not a different RD residual option.

- Config: `examples/Sedov_2d/Config_MMFV_moving.sh`.
- Standard exact ideal-gas Riemann solver (`godunov_flux_3d`), native spatial
  and temporal extrapolation, native reconstruction limiting; no refinement.
- Standard center-of-mass/face-angle regularization, CellShapingSpeed.5 and
  CellMaxAngleFactor2.25, matching the RD setup.
- TREE_BASED_TIMESTEPS and FORCE_EQUAL_TIMESTEPS: global adaptive steps,
  CourantFac.1, requested cap.01, lab frame. This deliberately matches the
  equal-step RD comparison, rather than using individual MMFV time bins.
- No added pressure/internal-energy floor; original parameters MinEgySpec0,
  MinGasTemp0, MinimumDensityOnStartUp0 retained.
- One MPI rank, OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1; full double precision.
- Frozen binary SHA256:
  `198b64f36c0fbed9454493a4798513a320a72334ea81f3cb7c56a2b880bed915`.
- Source tar, working-tree diff, source hashes, Config/generated header,
  binary/linkage, inputs/parameters, build and native logs are preserved.

Runner: `examples/Sedov_2d/run_mmfv.py`.
Analysis: `examples/Sedov_2d/analyze_mmfv.py`.

The initial uniform run establishes native Voronoi volumes for hot-energy
normalization and verifies constant-state preservation. Its maximum evolution
defect is2.054e−13. A wrapper initially stopped because it imposed a separate,
overly strict1e−14 initial-density bound: initial rho differs from1 by6.239e−14
after repeated Voronoi construction. We checked that rho equals mass/Volume
exactly and both total volume and mass equal1, then applied the established
uniform-state1e−12 bound consistently to initialization and evolution.
The already successful native gate was reused; no solver changes or native
rerun were made. Original wrapper is in frozen source.tar, resumed wrapper is
saved at archive root, and `native_audit.json` records the setup interruption.

## Quantitative comparison

Point/cell maxima and radial-bin maxima are different quantities. The plotted
means are unweighted in bins of width.005. In particular MMFV's raw maximum
3.97 should not be mistaken for its plotted mean peak3.30. Analytic shock
density is4 and shock radius is.257994631.

| t=.05 diagnostic | MMFV moving | Rusanov RD moving | Rusanov RD static | SWIFT SPHENIX |
|---|---:|---:|---:|---:|
| Minimum density |.028431|.196009|.124837|.036866|
| Raw maximum density |3.97057|2.63044|2.00216|3.60417|
| Radial-mean density peak |3.30243|2.42802|1.95739|2.99524|
| Mean-peak radial bin center |.2575|.2425|.2525|.2525|
| Relative mass change |−2.22e−16|−.239707%|−3.33e−16|0|
| Relative energy change vs IC |−4.44e−16|−2.414700%|−2.22e−16|+.0400534%|
| Samples inside r<.05 |4|3|130|7|
| Samples inside r<.1 |25|12|516|21|

Roundoff entries are dimensionless relative errors; entries carrying percent
signs are percentages. Across all five MMFV science snapshots, maximum
relative mass/energy errors are2.22e−16/6.66e−16. SWIFT's energy normalization
uses its original zero-velocity IC, not its t0 output with a leapfrog velocity
export offset; details remain in the SWIFT report.

For MMFV, actual cells within r<.05 have meanp1.59613 versus analytic pressure
at those cell centroids1.60505. The next two annuli .05–.1/.1–.15 have meanp
1.60324/1.64970 versus1.61063/1.67138. Its core pressure follows the expected
plateau; there remains a finite density plateau near.03 and an underdense
region at roughlyr.05–.1. It is a finite-support, finite-resolution result,
not an exact point-source solution.

The moving RD shell is better resolved than the static RD shell: raw peak
2.63 versus2.00 and a narrower density transition. Static RD nevertheless has
better global conservation and a lower innermost density plateau. The two RD
runs share the same low-order residual, but mesh evolution changes sampling,
geometry and update terms; do not describe every difference as a measured
change in one scalar diffusion coefficient.

The MMFV core has only4 samples inside r<.05 yet accurately reproduces central
pressure and a much lower density than RD. Thus sparse central sampling is
relevant but cannot by itself explain the large RD plateau. Spatial treatment
and ALE conservation/remapping remain separate issues. MMFV versus RD is not
a controlled reconstruction-only ablation, so it does not isolate their
individual contributions. Likewise no result here establishes an ENZO ranking.

## Plot coordinates and checks

MMFV states are cell averages plotted at **cell centroids**, RD states at
nodes, and SPH states at particles. Radius is measured from the corresponding
initial injected-excess-energy centroid. The MMFV centroid is
(.5006050852,.4999067435), only~1.8e−6 from RD21's. Hot selection still uses the
same original generator IDs. No arbitrary final-state recentering was used.

All10 new snapshots (5uniform+5Sedov) have positive finite rho/p/u/mass.
Pressure agrees with(gamma−1)rho*u to4.42e−16 relative. Every science snapshot
has a single time bin; final time is exactly.05 and IDs are preserved.
2358 logged flux exchanges contain zero mass-flux reductions; this does not
mean the standard reconstruction limiter was inactive. No negative-state or
termination diagnostic occurred. These checks establish the saved-state
properties and native completion, not a general positivity theorem.

`analysis/verification.json` stores metrics, provenance and snapshot hashes.
`native_audit.json` stores the additional new-run state and log audit.
Figures were visually checked:

- `analysis/mmfv_rd_swift_profiles.png` and `.pdf`: full rho/vr/p profiles and
  core detail,300dpi PNG, with raw samples and radial means.
- `analysis/mmfv_rd_swift_budgets.png`: mass and energy relative to input ICs.

All2 native attempts succeeded; no active solver remains. No production solver,
default Config, original SWIFT checkout, thesis, COSMA, commit or push changed.
