# Sod_2d_Morton: matched static / moving time-update comparison

2026-09-28, Codex. The user clarified that the Morton physical configuration
should also be run with the current moving-mesh and RK2 methods. This extends
the first-order controls; it is not an attempt to call every variant a method
used in Morton et al. (2023).

## Shared setup and method matrix

Archive: `../../local_runs/Sod_2d_Morton/20260928_full_v1/`.
Reused controls: `../../local_runs/Sod_2d_Morton/20260928_v1/`.
Reproducible runner/analysis: `../examples/Sod_2d_Morton/`.
Physical setup and reference provenance are documented in
[the first-order report](RD_SOD_2D_MORTON_GLASS_20260928.md).

All runs use gamma5/3, rho/p=1/1 versus .125/.1, zero initial velocity, a
periodic2x2 box with the high state in .5<x<1.5, and endt=.2. The right-hand
tube1<x<2 uses xi=x-1 and tau=t. Effective Nx64/128 corresponds to full-box
128²/256² glass nodes, with initial spacing1/64 or1/128. The exact same HDF5
ICs from the first-order campaign are copied and hash-checked. The finer IC
is a2x2 periodic tiling of the same relaxed glass, not an independently
relaxed new cloud. No equal-mass density-dependent sampling is introduced.

| Scheme | Temporal update | Residual | Mesh | Runs |
|---|---|---|---|---:|
| N | forward Euler | Roe | static | 2 reused |
| LDA | forward Euler | Roe | static | 2 reused |
| N | lumped RK2 | Roe | static | 2 new |
| LDA | forward Euler | Gauss3 | static | 2 new |
| LDA | F1 | Roe | static | 2 new |
| LDA | F1 | Gauss3 | static | 2 new |
| N | lumped RK2 | Roe + mesh-velocity split | moving | 2 new |
| LDA | F1 | Roe + mesh-velocity split | moving | 2 new |
| LDA | F1 | Gauss3 contour | moving | 2 new |

Both stages use the current standard mixed-stage F1 policy for LDA; this is
not the rate-consistent Heun experiment. Existing rank-deficient-element
lumped temporal fallback remains enabled and is counted in the analysis.
There is no limiter or new positivity repair. Euler uses the existing
predictor-only guard on static meshes. The current moving split-stage entry
explicitly rejects that diagnostic, so a moving Euler method is not created
by combining incompatible flags or disabling the guard.

All methods evaluate in the laboratory frame and use equal timesteps within
each run, without hierarchical timesteps. Moving configurations use the
current one-rebuild split stages, mesh CM/sound-speed/face-angle regularization,
CellShapingSpeed=.5 and CellMaxAngleFactor=1.5. Roe adds
RD_ALE_SPLIT_MESH_VELOCITY; Gauss3 adds RD_ALE_CONTOUR_RESIDUAL and
RD_ALE_CONTOUR_GAUSS=3. Static configurations retain VORONOI_STATIC_MESH.

CourantFac=.4 and MaxSizeTimestep=.02 are identical across this campaign.
The AREPO carrier/tree signal-speed bound and dyadic rounding remain in use;
RD_ALE_CFL_TIMESTEP is not added. The carrier speed differs between static
and moving meshes, so the resulting adaptive histories are measured and
reported rather than described as identical dt. These timesteps are also not
the original standalone code's nodal RD formula. No CFL reduction is hidden
inside the comparison.

## Provenance and verification procedure

The source tar SHA256 is
`b2a915f657bfc46ae6cce1cc315ea3776fafb74e8cd3e8d08b6d7a43302dd9c6`,
identical to the first-order controls. Preparation checked152 current source,
Makefile and defines_extra hashes against that archive. Every new method has
a separate build directory, immutable copied binary, Config/generated header,
version, linkage/build logs and SHA256 provenance. ICs and parameter files
are also hashed. The seven native builds are unchanged production solver
code with explicit experimental configurations.

The seven new gamma5/3 uniform gates precede the fourteen new science runs.
Uniform flow uses the48² glass, rho=p=1 and velocity(.37,-.21), endt=.025.
Runs use one MPI rank, OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1, at most two
simultaneous cases and MaxMemSize1024 each. Runtimes include overlap and
are not efficiency benchmarks.

Analysis checks five snapshots per completed run, clean exits and native
stage0/stage1 evidence, initial piecewise states and cross-method agreement,
ID preservation, EOS, finite positive saved states, static fixed coordinates
and zero vertex velocities, actual motion in moving runs, and changes in
global physical mass/momenta/energy. Uniform-state preservation and physical
conservation are evaluated separately. No plot treats a partial output as a
completedt=.2 result. Hashes are rechecked after analysis.

All final tube nodes remain in the scatter. Curves use128 equal-width,
unweighted xi-bin means for display. L1 norms and transverse velocity RMS
use normalized current median-dual area m/rho on the raw tube nodes. The
unweighted mean curve is not used as an error estimator. Velocity extrema
likewise refer to raw nodes. Small negative tails are distinguished from
the O(1) trough through the area fraction with vx<-.05. Neither shock
convergence order nor MPI invariance is established by these two resolutions.

## Completed results

All18 science cases reachedt=.2 with clean exits:14 new runs and4 reused
Euler/Roe controls. All9 uniform gates pass (7 new,2 reused), with a largest
primitive-state change1.9984e-15 across saved outputs. All135 saved snapshots
are finite and have positive rho/p/mass. Initial arrays agree to the specified
2e-14 absolute tolerance; static positions remain bitwise fixed and moving
runs have nonzero displacement and vertex velocity. No numerical failure,
CFL retry, relaxed assertion or solver change occurred in this campaign.

| Method | Nx | rho L1 | vx L1 | p L1 | vx min | vx max |
|---|---:|---:|---:|---:|---:|---:|
| static/N/Euler/Roe | 64 | 0.0267720 | 0.0503412 | 0.0251176 | -0.0002101581 | 0.8673194 |
| static/N/Euler/Roe | 128 | 0.0180506 | 0.0298597 | 0.0155598 | -1.723346e-08 | 0.8562289 |
| static/LDA/Euler/Roe | 64 | 0.0259959 | 0.0506651 | 0.0241377 | -0.0002098823 | 0.9559331 |
| static/LDA/Euler/Roe | 128 | 0.0172551 | 0.0294214 | 0.0147248 | -1.787206e-08 | 0.8797909 |
| static/N/RK2/Roe | 64 | 0.0278728 | 0.0537158 | 0.0264358 | -0.0004188698 | 0.8684562 |
| static/N/RK2/Roe | 128 | 0.0187605 | 0.0318441 | 0.0163693 | -6.463479e-08 | 0.8564519 |
| static/LDA/Euler/Gauss3 | 64 | 0.0261292 | 0.0511300 | 0.0242770 | -0.0002125969 | 0.9776551 |
| static/LDA/Euler/Gauss3 | 128 | 0.0172780 | 0.0295564 | 0.0147439 | -1.775172e-08 | 0.8814513 |
| static/LDA/F1/Roe | 64 | 0.0171986 | 0.0353758 | 0.0152575 | -0.5987103 | 0.8899459 |
| static/LDA/F1/Roe | 128 | 0.0105958 | 0.0192019 | 0.0083454 | -0.5947701 | 0.8923505 |
| static/LDA/F1/Gauss3 | 64 | 0.0171570 | 0.0358646 | 0.0151755 | -0.5829534 | 0.9161166 |
| static/LDA/F1/Gauss3 | 128 | 0.0105588 | 0.0192230 | 0.0082971 | -0.5947402 | 0.8965165 |
| moving/N/RK2/Roe | 64 | 0.0245797 | 0.0552392 | 0.0303234 | -0.0001075081 | 0.9204880 |
| moving/N/RK2/Roe | 128 | 0.0166318 | 0.0336440 | 0.0191364 | -1.688125e-08 | 0.9571627 |
| moving/LDA/F1/Roe | 64 | 0.0168010 | 0.0408747 | 0.0185245 | -0.6003234 | 0.9693981 |
| moving/LDA/F1/Roe | 128 | 0.0098199 | 0.0224649 | 0.0099526 | -0.5959447 | 1.2008836 |
| moving/LDA/F1/Gauss3 | 64 | 0.0159468 | 0.0399808 | 0.0185326 | -0.586994 | 0.9930277 |
| moving/LDA/F1/Gauss3 | 128 | 0.0091485 | 0.0208827 | 0.0098324 | -0.5838125 | 0.9917461 |

The exact plateau velocity is.84119485. The principal observations are:

- The same Morton physical setup still produces a large negative velocity
  trough in LDA/F1 on static and moving meshes, with either residual. AtNx128
  the static/moving minima are-.594770/-.595945 for Roe and
  -.594740/-.583813 for Gauss3. Switching residuals or moving the mesh does
  not remove it. The corresponding LDA/Euler controls have minima close to
  zero, although positive overshoots remain. N/RK2 has no comparable negative
  trough. This identifies sensitivity to the current LDA/F1 combination,
  not a demonstrated failure of every RK2 method or a completed root-cause
  diagnosis. The actual timestep histories are not identical.
- Refinement narrows the static F1 trough without materially reducing its
  raw-node depth. For Roe, the current tube area fraction withvx<-.05 drops
  from.03116 to.01551; Gauss3 drops from.03092 to.01564. The integrated negative
  velocity approximately halves. Lower L1 errors therefore coexist with
  persistent local extrema; this is not a smooth-solution order measurement.
- Moving meshes sharpen the contact and lower the density L1 in all three
  RK2/F1 pairs at both resolutions. AtNx128 the static/moving density errors
  are.018761/.016632 for N, .010596/.009820 for LDA/Roe, and
  .010559/.009148 for LDA/Gauss3. However, velocity and pressure L1 errors are
  larger on the moving mesh in all these pairs. Do not call the moving result
  uniformly more accurate or infer monotonicity from its mean curve.
- The high-resolution moving Roe/F1 case has appreciable contact-region raw
  scatter: vx_max=1.200884 and specific e_max=8.531915, versus.991746 and
  2.324658 for moving Gauss3/F1. Their128-bin velocity mean maxima are only
  .841643 and.843450. A mean line alone conceals these excursions. The full
  raw energy range is retained and its largest Roe point is explicitly marked
  on the residual-comparison page. Both variants still have the shock trough.

## Actual timesteps and conservation

| Method | Nx | Steps | dt min | dt max | Runtime s |
|---|---:|---:|---:|---:|---:|
| static/N/Euler/Roe | 64 | 226 | 0.00078125 | 0.0015625 | 9.72 |
| static/N/Euler/Roe | 128 | 481 | 0.000390625 | 0.00078125 | 122.12 |
| static/LDA/Euler/Roe | 64 | 235 | 0.00078125 | 0.0015625 | 10.15 |
| static/LDA/Euler/Roe | 128 | 489 | 0.000390625 | 0.00078125 | 122.62 |
| static/N/RK2/Roe | 64 | 221 | 0.00078125 | 0.0015625 | 14.31 |
| static/N/RK2/Roe | 128 | 477 | 0.000390625 | 0.00078125 | 191.73 |
| static/LDA/Euler/Gauss3 | 64 | 244 | 0.00078125 | 0.0015625 | 10.76 |
| static/LDA/Euler/Gauss3 | 128 | 494 | 0.000390625 | 0.00078125 | 130.80 |
| static/LDA/F1/Roe | 64 | 249 | 0.00078125 | 0.0015625 | 16.82 |
| static/LDA/F1/Roe | 128 | 504 | 0.000390625 | 0.00078125 | 192.33 |
| static/LDA/F1/Gauss3 | 64 | 249 | 0.00078125 | 0.0015625 | 16.41 |
| static/LDA/F1/Gauss3 | 128 | 505 | 0.000390625 | 0.00078125 | 195.46 |
| moving/N/RK2/Roe | 64 | 237 | 0.00078125 | 0.0015625 | 43.24 |
| moving/N/RK2/Roe | 128 | 499 | 0.000390625 | 0.00078125 | 572.28 |
| moving/LDA/F1/Roe | 64 | 246 | 0.00078125 | 0.0015625 | 41.50 |
| moving/LDA/F1/Roe | 128 | 529 | 9.76562e-05 | 0.00078125 | 580.41 |
| moving/LDA/F1/Gauss3 | 64 | 246 | 0.00078125 | 0.0015625 | 39.18 |
| moving/LDA/F1/Gauss3 | 128 | 504 | 0.000390625 | 0.00078125 | 516.29 |

The.02 cap never binds. In particular, moving Roe/F1 atNx128 reaches a smaller
minimum dt than the otherNx128 cases. Equal CourantFac must not be interpreted
as an identical temporal discretization history or a pure residual-only
comparison at matched dt. Runtime differences are not controlled benchmarks.

Static mass/energy changes across saved outputs are at round-off:
max3.95e-16 and1.08e-15 relative. Moving physical endpoint totals drift:

| Moving method | Nx | Maximum saved mass drift (%) | Maximum saved energy drift (%) |
|---|---:|---:|---:|
| N/RK2/Roe | 64 | 0.02610 | 0.07553 |
| N/RK2/Roe | 128 | 0.02525 | 0.06183 |
| LDA/F1/Roe | 64 | 0.09583 | 0.21119 |
| LDA/F1/Roe | 128 | 0.09577 | 0.20748 |
| LDA/F1/Gauss3 | 64 | 0.06687 | 0.20210 |
| LDA/F1/Gauss3 | 128 | 0.07530 | 0.19382 |

These are maxima of absolute fractional changes fromt=0 over the five saved
outputs, not relative to a zero initial momentum. Momentum changes are
normalized by initial mass in the machine-readable history. All final moving
energies are below their initial totals. Uniform-state preservation does not
establish nonuniform physical endpoint conservation. The analysis also sums
native ALE temporary/rebase/endpoint changes; their totals agree with snapshot
changes up to printed-log precision. The finish-only rebase term does not
account for the entire drift. No correction is applied in postprocessing.

## Deliverables and limits

`summary.json` records per-case profiles/errors/extrema, transverse motion,
conservation histories, stage/fallback diagnostics, actual steps and input
hashes. `verification.json` records completed gates/cases and PDF inspection.
Every case has its own128-bin CSV; the raw HDF5 snapshots remain authoritative.

The six-page `output/pdf/Sod_2d_Morton_variants_review.pdf` contains:

1. Static versus moving N/RK2 and LDA/Gauss3/F1, Nx128.
2. The same mesh comparison, Nx64.
3. Static Euler versus RK2/F1 for N/Roe, LDA/Roe and LDA/Gauss3, Nx128.
4. The same temporal comparison, Nx64.
5. Roe versus Gauss3 in static/moving LDA/F1, Nx128.
6. The same residual comparison, Nx64.

Native180-dpi PNGs are under `figures/`. All six final PDF pages were rendered
and visually reviewed for labels, legends, full scatter ranges and clipping.
These are local review outputs. No thesis insertion, commit/push, COSMA work,
B scheme, moving Euler construction, hierarchical timestep or additional
co-moving-frame run was performed. The experiment does not establish strict
positivity for arbitrary data, convergence order, or MPI equivalence.

## Presentation update: simplified x/t labels

The user subsequently accepted t=.2 as the Morton output-time assumption for
this comparison. The display-only revision at
`../../local_runs/Sod_2d_Morton/20260928_display_x_v1/` labels the horizontal
axis x=X-1 over0<x<1, selecting the original right-hand tube1<X<2; t is
unchanged. The numerical x/t values equal the former xi/tau. All18 raw curves
and bin means are unchanged and source hashes rechecked. The six-page PDF
was regenerated and inspected. No simulation or original archive was changed.
