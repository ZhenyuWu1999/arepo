# Sedov core profiles and reference scales, 2026-09-29

Author: Codex. Read-only follow-up to the fewer-injection-points experiment.
No new hydrodynamics runs, solver changes or thesis changes.

## Conclusions

The matched-time repair control in log3 §159 strongly supports connectivity
changes as the dominant source of the observed **global conservation loss**:
at t=0.00545654, the 21-node energy error changes from −1.2498% without repair
to −0.0001046% with repair. The next remap fails positivity. This evidence does
not establish that connectivity loss dominates every pointwise profile error.

The inner density excess also occurs in the static Rusanov run, which conserves
mass and energy to roundoff. Low-order diffusion and poor sampling of the
evacuated moving core are supported explanations. The moving pressure and
velocity errors have not been uniquely separated into diffusion, geometry and
remapping contributions. Do not present that causal decomposition as measured.

## Inner-region audit

All four runs are glass128², L=1, rho0=1, gamma=5/3, background pressure 1e−6,
hot-region energy 1, equal adaptive timesteps (CFL .1, cap .01), low-order
Rusanov spatial residual with lumped RK2 temporal update. Moving runs have
standard mesh regularization and **no topology repair**. The static/moving
21-node pair shares identical initial states. Each radial coordinate is
centered on that run's initial injected-excess-energy centroid; the single
hot node is slightly off box center. All final snapshot headers give t=.05.

| Run | Nodes r<.05 | Nodes r<.1 | Nodes r<.15 | Mean rho, r<.05 | Mean p, r<.05 |
|---|---:|---:|---:|---:|---:|
| Moving, 1 hot node |1|7|78|.195762|1.781136|
| Moving, 7 hot nodes |2|10|74|.199248|1.769720|
| Moving, 21 hot nodes |3|12|72|.197759|1.721285|
| Static, 21 hot nodes |130|516|1158|.135951|1.444316|

These are unweighted means of actual nodal values, not spatial integrals. In
r<.05, the mean sqrt(median-dual area) is .0624/.0601/.0522/.00781 respectively.
Thus the moving core has much coarser effective sampling than the initial or
static mesh. Blank radial bins contain no nodes; the new plot does not bridge
them with an interpolated hydro profile. The older 2D density map does involve
spatial interpolation, which should not be mistaken for additional resolution.

The cylindrical Sedov reference at t=.05 has rho→0 and vr→0 at the origin,
but finite pressure p(0)=1.604968. Representative point values:

| r | rho | vr | p |
|---|---:|---:|---:|
| .025 | .001343 | .150000 | 1.604982 |
| .05 | .010745 | .300024 | 1.605419 |
| .10 | .086604 | .601542 | 1.619499 |
| .15 | .307786 | .917549 | 1.720094 |

The central numerical plateau near rho=.2 is not an imposed density floor.
The low-order residual smooths the shell/interior structure and under-resolves
the deep central rarefaction; the lower shell peak and excess interior density
are consistent with that diffusion. Moving mesh expansion further depletes the
core sampling. A single heated node still has finite P1 support on adjacent
triangles and is not a continuum delta-function source. However, the very
similar 1/7/21-node profiles show that injection count is not the main observed
sensitivity at this resolution. A spatial-order/resolution comparison would
be needed for a stronger causal claim.

The static 21-node run's central density is also high while pressure is below
the reference, so density and pressure errors should not be conflated. Moving
single-node central pressure is about 11% high. Replacing E by the measured
final-energy fraction .9742368 in an otherwise exact 2D similarity solution
would change shock radius by E^(1/4), only −.65%, and central pressure by
E^(1/2), approximately −1.30%. This is a scale estimate, not an exact solution
for time-dependent numerical energy loss; it cannot explain the sign and size
of the moving central pressure excess.

### Analytic sampling check

The old reference uses SWIFT's formulas sampled uniformly in similarity
variable v (20,000 samples). Its first positive radius is .0344663, making
linear interpolation inaccurate for the very small density near the origin.
The new diagnostic samples the same equations logarithmically near v_min
(50,000 samples), retaining the exact origin limits. All values are finite;
the integrated energy is 1.000000024, the shock density is 4, and shock radius
.257994631 differs from the old reference by only 7.27e−8 fractionally. The
refinement makes the tiny central analytic density lower, not closer to the
numerical plateau. Original hydro snapshots and previous plots are unchanged.

## Morton (2023), original source and rescaling

The [paper §5.2.3](https://arxiv.org/html/2204.01757v2#S5.SS2.SSS3) shows the
Sedov result at t=.01, using circular injection and random vertices, with
64²/128²/256² comparisons. N1 is used for the displayed solution; N2 is reported
as essentially identical, and LDA unstable. Dimensional setup values below
come from the associated standalone source, not all from the paper prose.

The inspected repository is `/Users/zhenyuwu/Desktop/PhD/rdsolver_Ben/rdsolver`.
Its current setup file has local edits and its active constants file is
untracked, so this audit freezes the **committed** `rd/main.cpp`,
`rd/setup2D.cpp`, and `rd/constants.h.TEMPLATE` at revision
`ba336488cc1b2d0c8301d05e230694c72a6c3272` instead. These files are available in
the [source repository](https://github.com/StevenWu1999/rdsolver/tree/ba336488cc1b2d0c8301d05e230694c72a6c3272/rd).
The template is not proof of the exact compiled flags used for every paper
figure; this is a source-based setup comparison, not a reproduced paper run.

The Sedov block specifies L=10, gamma=5/3, rho0=1, background pressure 100,
injection radius .25, final time .01 and CFL .2. Crucially, **after mesh
construction main.cpp normalizes the hot-region energy to 300,000**, setting
p_hot=(gamma−1)*300000/sum(hot dual areas). A continuous disk estimate gives
p_hot≈1.019e6, but the actual value depends on the discrete hot area. The
earlier pilot report's provisional hot pressure 1e6 was insufficient to
describe this final initialization. Hot-region energy is not total box energy:
the cold region adds approximately 1.497e4 for a continuous radius-.25 disk.
Likewise, explosion excess energy differs slightly from the overwritten hot
energy; this is about a 1e−4 relative correction for the Morton disk estimate.

For 2D cylindrical flow, using L, rho0 and explosion energy per transverse
length E as reference scales gives

    x_hat = x/L
    rho_hat = rho/rho0
    v_hat = v L sqrt(rho0/E)
    t_hat = t sqrt(E/rho0)/L²
    p_hat = p L²/E
    R = beta (E t²/rho0)^(1/4).

The table uses the specified hot-region E as the scale; the small background
subtraction above does not materially affect these comparisons.

| Quantity | Morton source units | Morton normalized to L=rho0=E=1 | Current RD / SWIFT physical setup |
|---|---:|---:|---:|
| Box side |10|1|1|
| Ambient density |1|1|1|
| Hot-region energy |300000|1|1|
| Background pressure |100|.0333333|1e−6|
| Injection radius |.25|.025|Nearest1/7/21 nodes; RD21 outer node radius .0195966|
| Display/final time |.01|.0547723|.05|
| Gamma |5/3|5/3|5/3|

Morton .01 is therefore close to, but not exactly, our .05. Our .05 corresponds
to .00912871 in those Morton units. Background pressure is the larger physical
difference: ours is 33,333 times smaller after normalization. Both are strong
blast regimes, but a pure units transformation does not make their initial
conditions identical. Both nominal128² meshes have h/L≈1/128; using L=1
instead of10 does not itself reduce relative resolution. The random/static
Morton mesh and glass/moving RD mesh, injection support and spatial schemes
also differ. CFL numbers should not be treated as identical step sizes across
different solvers.

## SWIFT time and numerical-result provenance

The local [SWIFT parameter file](https://raw.githubusercontent.com/SWIFTSIM/SWIFT/master/examples/HydroTests/SedovBlast_2D/sedov.yml)
sets `time_end=5e-2`, snapshot `time_first=0`, `delta_time=1e-2`, so its intended
snapshot sequence is 0,.01,.02,.03,.04,.05. Its plotting script reads the
actual snapshot Header.Time and calls the analytic solution with dimension2.
Our final snapshot is **exactly .05** and matches that configured final time.
Our intermediate requested cadence is .0125 and is not the SWIFT cadence.

No SWIFT hydrodynamics run was made. The comparison curve is the analytic
Sedov solution computed with SWIFT's reference formulas, not a measured SWIFT
numerical result. SWIFT's example heats the nearest21 equal-mass particles,
not one; the RD variants normalize energy with actual dual-cell masses.

### Explicit three-way comparison (follow-up, log3 §162)

User requested SWIFT as a separate column. Parameters are from the local and
current upstream `makeIC.py`, `sedov.yml`, and `run.sh`; this is a setup
comparison, not a new SWIFT numerical result.

| Quantity | SWIFT SedovBlast_2D | Current RD | Morton source / paper |
|---|---|---|---|
| Dimension |2|2|2|
| Box side |1|1|10|
| Boundary |Periodic|Periodic|Periodic in inspected source template|
| Gamma |5/3|5/3|5/3|
| Ambient density |1|1|1|
| Ambient pressure |1e−6|1e−6|100|
| Initial velocity |0|0|Approximately zero (1e−8 components in source)|
| Hot-region energy |1|1|300000 after area normalization|
| Positions |glassPlane_128, 16384 particles|Same glass, 16384 nodes|Random vertices; paper64²/128²/256²|
| Heated set |Nearest21 particles|Nearest21 reference; additional1/7 variants|All vertices inside radius .25|
| Outer heated-node radius |.01959655049|Same for21-node reference|Selection radius .25|
| Mass assignment |Equal mass, 1/16384|rho0 times actual median-dual area|rho0 times actual dual area|
| Final/display time |.05|.05|.01|
| Snapshot interval |.01|Requested .0125|Not compared here|
| CFL parameter |.1|.1|.2|
| Maximum timestep |.01|.01|Not compared here|
| Method |SPH; particular formulation depends on build|Rusanov spatial RD, lumped RK2; static/moving|Displayed N1, static mesh; N2 reported similar|

The cached source glass is `../local_runs/swift_glass/glassPlane_128.hdf5`,
not inside the SWIFT example directory. Direct comparison confirms exact
equality of RD coordinates with the source glass after periodic modulo1:
7 coordinate components cross the box boundary in the source; all periodic
differences are exactly zero. The nearest21 hot IDs are identical. Thus the
21-node RD reference uses the same point distribution and heated set, not
merely another glass at the same nominal resolution.

SWIFT assigns u_hot=1/(21/16384)=780.1904762, giving nominal p_hot=520.1269841
at target rho0=1. The RD hot mass is .001279853512 and p_hot=520.8929463,
approximately .147% higher because the actual hot dual area differs slightly
from 21/16384. The formulas describe prescribed IC values before output float
rounding; SPH's kernel-estimated density can differ from target rho0. Both
overwrite hot specific energy to give hot energy1 rather than adding1 on top
of the pre-existing hot background. The untouched cold gas adds about1.5e−6
to box energy.

SWIFT's run script explicitly enables `--limiter`; this is its timestep limiter,
not our connectivity-repair positivity limiter. SPH resolution_eta=1.2348 is
specified, and the IC generator rescales the imported smoothing lengths by.3.
An exact SPH formulation/kernel or artificial-viscosity configuration cannot
be inferred from this YAML alone without checking its compiled executable.
Matching particle counts and positions does not make SPH kernel resolution
identical to RD triangle/dual-cell resolution; matching CFL numbers does not
make actual timesteps identical.

After the earlier Morton normalization, L=rho0=E=1, pbg=.0333333, injection
radius=.025 and display time=.0547723. SWIFT and current RD share pbg1e−6 and
time.05: the background is 33333 times colder in these normalized pressure
units. For21-node injection, nominal hot/cold pressure contrast is about5.2e8
in SWIFT/RD, versus about1.0e4 in Morton's continuous-disk estimate. Thus the
stronger contrast is inherited from the SWIFT physical setup, and is not
introduced by the current1-point variant (which increases it further).

## Reproducibility

Analysis script: `examples/Sedov_2d/audit_reference_scales.py`.
Archive: `../local_runs/sedov_core_reference_audit_20260929_v1/`.
It preserves the inspector, committed Morton sources and local SWIFT files;
`audit.json` includes hashes, all annular statistics and conversion factors.
The four existing native runs' successful statuses, binary/config hashes and
actual snapshot times are verified. `core_sampling.png` was visually checked.
No native calculations, compilation, default configuration changes, thesis
edits, COSMA operations, commits or pushes were performed.
