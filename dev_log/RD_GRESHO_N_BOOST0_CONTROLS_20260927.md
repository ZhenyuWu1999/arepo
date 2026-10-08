# N-scheme Gresho: matched zero-boost controls and boost sensitivity

2026-09-27. Author: Codex. Follow-up to log3 §128. User asked whether moving
N at boost10 really outperforms static N at boost0, requested the static0
control, and asked how this relates to Galilean invariance. A matching moving0
control was also run to separate mesh choice from boost dependence.

## Experiment

Archive: `../../local_runs/gresho_n_glass_boost0_controls_20260927_v1/`.
The two N binaries from `gresho_glass_boost10_lab_20260927_v1` were copied and
hash-verified, together with their Configs, headers, build logs and linkage.
Frozen source and build provenance point to that existing immutable archive;
there was no rebuild or solver/default configuration change. All152 production
and build-file hashes checked still match the original frozen source manifest.

The zero-boost HDF5 inputs are copies of the original boost10 inputs with only
10 subtracted from vx; every other input dataset is bitwise unchanged. Thus
the same genuine glass48 coordinates, particle IDs, rho and internal energy
are used. Initial output coordinates/masses match exactly; deboosted velocity
differs by at most1.78e-15 and pressure by2.13e-14 after primitive recovery.

Both static and moving N use lab evaluation, gamma5/3,2304 nodes, unit periodic
box, CFL.3, cap1/4096, t1, outputs at0,.5,1. Both take exactly4096 equal steps,
matching boost10. Native runs are single rank, OMP/BLAS threads1, two workers.
Two uniform controls and two pilots first reach .03125 in128 steps. Uniform
rho/v/p maximum defects are1.60e-14 (static) and7.99e-15 (moving), passing the
unchanged1e-12 threshold. Both pilots and science runs finish normally with
positive finite states in stored outputs and no native assertion failure.
All six new runs are complete. No boost3, LDA0 or additional resolution runs.

## Measured results at t=1

Same norm as §128: final-mass weighted absolute azimuthal velocity error over
all native nodes, known analytic center and bulk velocity subtracted; no
interpolation, binning or fitted center.

| Mesh | Boost | vphi L1 | Peak vphi | Relative total-mass drift |
|---|---:|---:|---:|---:|
| Static |0|0.05809649|0.663473|+2.22e-16|
| Static |10|0.23996020|0.153450|−3.33e-16|
| Moving |0|0.01888672|0.851676|+3.93020e-5|
| Moving |10|0.01890833|0.853379|+3.70739e-5|

Moving10/static0 error ratio is0.32546: the user's impression is confirmed,
with about3.07 times lower error. Static10/static0 is4.13037. Moving10/moving0
is1.001144, a0.1144% increase in this error metric. This is not a claim that
the two numerical solutions differ everywhere by0.1144%.

## Why the static0 result can be worse

Zero bulk boost leaves the local Gresho rotation intact. Static mesh sets
sigma=0, while the actual moving prescription starts from the local fluid
velocity, adds a half-step pressure predictor and mesh regularization
(`src/mesh/set_vertex_velocities.c:264,282,316,470`). The characteristic split
uses `(u_Roe-sigma_bar).n` and its acoustic shifts by +/-c
(`src/hydro/residual_distribution_solver.c:4444`). It is therefore reasonable
for local transport-related diffusion to differ even at zero bulk boost;
the acoustic terms and geometric errors do not disappear.

In particular, with constant bulk b and local rotational velocity u_rot,
the quasi-Lagrangian moving case has approximately
`u=b+u_rot`, `sigma=b+u_rot+regularization/predictor corrections`.
Removing b gives a mesh that still follows local rotation. It does not give
the static0 mesh with sigma=0. Only a rigidly translating mesh with sigma=b
would transform into a static mesh. Galilean invariance places no requirement
that quasi-Lagrangian moving10 and static0 have identical discretization errors.

This interpretation is consistent with the measured final mass-weighted mean
fluid-mesh relative speeds: static0 .22400, moving0 .007261, moving10 .006514.
These are supporting diagnostics, not a controlled decomposition of the total
error into advection, changing mesh geometry, remapping and residual choices.

## What the boost comparison establishes

The relevant test is moving0 versus moving10 after undoing the global shift
of both coordinates and velocities. This is the same comparison principle
used for Gresho in [Springel2010, §8.5](https://academic.oup.com/mnras/article/401/2/791/1147356);
§3.4 describes the covariance criterion. Its proof for AREPO's finite-volume
scheme is not a proof for the present RD implementation.

The profiles and analytic error norms here show weak boost sensitivity, but
the result is not identical to roundoff. With matching particle IDs and
boost0 final masses as weights, the moving pair at t1 has:

- Deboosted velocity-vector L1 difference .00238766 and maximum .133680.
- Position RMS difference .00238050 and maximum .0388953 in the unit box.
- Azimuthal velocity pair L1 difference .00149903, evaluated at each node's
  own radius; pressure maximum difference .0560504.

Since the node locations also diverge, these are joint mesh/state covariance
diagnostics, not norms of two Eulerian fields at identical sampling points.
At the short pilot endpoint .03125, position maximum difference is1.4501e-6
and velocity maximum difference9.0841e-5. The source retains the N Roe/U split
correction, singular-solve branches and changing connectivity; this experiment
does not isolate which mechanisms cause the finite differences. Do not assign
them all to roundoff or declare exact Galilean invariance.

Suitable conclusion: **moving N is much less sensitive to the imposed bulk
boost in this test, while retaining measurable differences in the full
numerical solution and mesh trajectory**. Boost3 is not required to make that
limited point. LDA would need its own matched zero-boost result for the same
claim; the historical jitter0 result is not a replacement.

## Artifacts and verification

`output/pdf/gresho_n_glass_boost0_10_static_moving.pdf` and its PNG show static
and moving panels, each with boosts0/10. PDF rendered and visually checked;
all native points lie within the plotted bounds. `summary.json` preserves
all times, norms and boost-pair diagnostics; `reuse_provenance.json` and
`analysis_provenance.json` preserve source/binary/input/analysis hashes.
Repo helpers are `tests/rd/run_gresho_n_boost0_controls.py` and
`tests/rd/analyze_gresho_n_boost0_controls.py`. No thesis change, commit or push.
