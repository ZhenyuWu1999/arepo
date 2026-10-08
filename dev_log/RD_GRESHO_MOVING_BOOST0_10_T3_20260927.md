# Moving Gresho glass48 at t3: N/LDA, boosts0 and10

2026-09-27. Author: Codex. User selected genuine glass48, time3, moving mesh
N and LDA at boosts0/10, then explicitly requested a standalone preview before
any thesis insertion. Laboratory-frame evaluation is retained.

## Setup

Archive: `../../local_runs/gresho_glass_moving_boost0_10_t3_lab_20260927_v1/`.
The `boost0` and `boost10` subdirectories each contain N/Roe+lumped and
LDA/Gauss3+default mixed-stage F1, copied from the same frozen binaries used
in log3 §128. The two boosts use identical binaries for each scheme. Config,
generated header, version, build logs, linkage and source hashes are retained.
No rebuild, solver change, element co-moving evaluation or topology repair.

All inputs use the same2304-node SWIFT glass in a unit periodic box, gamma5/3.
The boost0 IC differs from the original boost10 IC only by subtracting10
from vx; other datasets are identical. Arpaia modified coefficients, mesh
regularization and the current one-rebuild ALE hooks remain unchanged.

Common cap1/4096, TimeMax3: expected dyadic step3/16384. Short uniform and
Gresho pilots end at .046875,256 steps. Science outputs are0,.75,1.5,2.25,3.
Each run is one MPI rank with OMP/BLAS threads1, maximum four simultaneous
solver workers. `pipeline.py` runs the two boost groups through their existing
strict uniform, pilot and science gates; all failed outputs would be retained.

## Completed results

All four uniform and four pilot gates pass without changing tolerances, and
all four science runs complete normally to t3 with no native assertion failure.
All12 native runs are complete. Every science run uses16384 constant steps,
actual dt3/16384; the complete timestep sequences are identical. All20 science
snapshots contain finite states and positive rho, pressure and mass. No active
solver workers remain. The152 checked production/build file hashes still
match the original frozen source. The initial boost pair has exactly matching
coordinates, IDs and masses, deboosted velocity differences at most1.78e-15
and pressure differences2.13e-14 after primitive recovery.

Final azimuthal velocity errors use final mass weights over all2304 nodes:

| Scheme | Boost | vphi L1 | Peak vphi | Relative total-mass drift |
|---|---:|---:|---:|---:|
| N/Roe |0|0.04724472|0.735437|+1.51896e-4|
| N/Roe |10|0.04707784|0.741639|+1.59239e-4|
| LDA/Gauss3 |0|0.01252980|0.897588|+1.76925e-4|
| LDA/Gauss3 |10|0.01249125|0.893963|+1.71012e-4|

The boost10/0 error ratios are0.996468 (N) and0.996924 (LDA). Thus the absolute
relative differences in this analytic-error metric are0.3532% and0.3076%.
The two radial profiles overlap closely; moving LDA retains a sharper/higher
peak than N. These percentages describe differences between error metrics,
not pointwise differences between the two numerical solutions.

The particle-ID boost-pair audit at t3 finds joint mesh/state differences:

| Scheme | Position RMS | Position max | Deboosted velocity-vector L1 | Velocity max |
|---|---:|---:|---:|---:|
| N |0.0472334|0.354547|0.0448393|0.867165|
| LDA |0.00957318|0.104736|0.0104613|0.244915|

The weights here are the boost0 final masses. Node trajectories diverge,
so the paired states are sampled at different coordinates; these numbers
must not be presented as common-position Eulerian field errors. Close radial
profiles do not demonstrate exact invariance of the complete mesh/state
trajectory. No mechanism-isolation test was run, and the finite differences
are not simply labelled roundoff. The supported claim is weak bulk-boost
sensitivity of the displayed radial profiles/errors in this experiment.

Global moving conservation remains approximate: total-energy relative drifts
are−2.08683e-4/+1.05382e-4 for N at boosts0/10 and−3.34731e-4/+1.08552e-4
for LDA. The lab-frame energy totals have different bulk kinetic contributions;
their relative drift percentages are not a boost-invariant error norm.

## Preview figure

Separate N and LDA panels overlay boosts0/10 and the analytic triangular
azimuthal-velocity profile at t3. Subtract the known bulk translation and
velocity, using the analytic center, all native points, no fitted center,
interpolation or radial binning. Errors use final mass weights; area-weighted
errors are stored separately. Boost-pair diagnostics compare particle IDs
and include both state and mesh-trajectory differences, not a common-grid
Eulerian field norm. Similar analytic error norms do not prove exact Galilean
invariance. The final PDF is
`output/pdf/gresho_glass48_t3_moving_boost0_10.pdf`; the display PNG is
`figures/gresho_glass48_t3_moving_boost0_10.png`. The PDF was rendered and
visually checked: legends are below the axes, all native points are within
the axis limits, labels are readable and nothing is clipped. One premature
render inspection occurred while analysis was still running; inspection was
repeated successfully after completion, without rerunning hydrodynamics.

The generic runner now accepts a selected-method list, so this campaign runs
only moving N/LDA. The new analyzer is
`tests/rd/analyze_gresho_moving_boost_pair.py`. Earlier result archives and
figures remain unchanged. No thesis edit, commit, push or COSMA operation.
