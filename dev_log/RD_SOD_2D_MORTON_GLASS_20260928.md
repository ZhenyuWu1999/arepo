# Sod_2d_Morton: static first-order glass results

2026-09-28, Codex. User requested Morton2023 settings with glass ICs and named
the test `Sod_2d_Morton`. All two uniform gates and four science runs completed.

## Setup and provenance

Example: `../examples/Sod_2d_Morton/`.
Archive: `../../local_runs/Sod_2d_Morton/20260928_v1/`.

Morton et al.2023 §5.1.1/Fig7 specifies gamma5/3, rhoL/pL=1/1,
rhoR/pR=.125/.1, zero velocity, CFL.4 and first-order LDA/N at longitudinal
N64/128. We replace its row-offset mesh by a relaxed glass. Both methods use
the Roe parameter-vector residual, with the complete forward-Euler update
provided by the existing `RD_DIAG_PREDICTOR_ONLY` path. Native logs contain
stage0 and no stage1. Dropping the RK2 flag into the older two-call path would
not be the same temporal update, so old Morton-labelled Configs were not reused.

New evidence for time/box: the user's local standalone RD source,
`/Users/zhenyuwu/Desktop/RD/src/constants.h:109`, has SODX with CFL.4,
T_TOT=.2, gamma5/3 and box2×2. `setup2D.cpp:33` puts the high state in
.5<x<1.5. Copies/hashes are archived. This local copy has no Git metadata and
cannot establish the exact revision behind published Figure7. Its tiny1e-9
velocity seed is not copied; the paper's explicitly zero initial velocity is
used. The local original's density/energy floors are not imported.

The present2×2 periodic box follows that layout. Display the right-hand tube
1<x<2, retaining the full y range, with xi=x-1 and tau=t. Initial specific
energies are1.5 and1.2. Final rawt=tau=.2, with five snapshots at0,.05,.1,.15,.2.
First continuum mirror shock collision is at t=.27108009, beyond this output.
This differs from the previous unit-box convention xi=2(x-.25),tau=2t;
do not apply the old factor2 to this new archive.

| Initial effective Nx | Full box | Tube nodes | Nominal spacing |
|---|---:|---:|---:|
| 64 | 128²=16384 | 8194 | 1/64 |
| 128 | 256²=65536 | 32768 | 1/128 |

Both use the wrapped relaxed SWIFT glassPlane_128. Nx64 scales it to side2;
Nx128 tiles2×2 and scales into the same box. This retains a relaxed periodic
glass pattern, not new random jitter or density-dependent equal-mass sampling.
All case names explicitly use effective initial tubeNx, not full-box nside.

Solver source is frozen from the September28 static archive, whose source tar
matches the September24 comparison source. Current src/Makefile/defines_extra
hashes were checked against that archive before building. Two isolated native
builds preserve Config, generated header, compiler logs, version and linkage.
Full source tar, IC/parameter/binary hashes, run logs/status and five snapshots
per case are retained. Single rank; OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1;
maximum2 concurrent cases, MaxMemSize1024 each. No solver/default changes.

## Time-step qualification

CourantFac=.4 and MaxSizeTimestep=.02. The cap never binds. AREPO still uses
its carrier radius/signal-speed and tree limit, with power-of-two rounding;
the standalone code uses a nodal `CFL*2*DUAL/LEN_VEL_SUM` bound. These are not
claimed to generate the same timesteps. This is the paper's physical state
and first-order method family on glass inside AREPO, not a full original-code
reproduction with only one implementation difference.

| Scheme | Nx | Steps | Actual dt range | Runtime s |
|---|---:|---:|---:|---:|
| N1/Roe | 64 | 226 | .00078125–.0015625 | 9.72 |
| N1/Roe | 128 | 481 | .000390625–.00078125 | 122.12 |
| LDA1/Roe | 64 | 235 | .00078125–.0015625 | 10.15 |
| LDA1/Roe | 128 | 489 | .000390625–.00078125 | 122.62 |

Different adaptive histories between schemes are retained, not called an
identical-dt comparison. Runtimes include overlap with other cases and are
not efficiency benchmarks.

## Results

Error norms use normalized median-dual area m/rho on all original nodes in
the selected tube. Extrema include every such node. Figures overlay faint
all-node scatter and128 equal-width, unweighted bin means. Binning is display
only and does not change the error norm or physical Nx.

| Scheme | Nx | rho L1 | vx L1 | p L1 | vx min | vx max | vy RMS |
|---|---:|---:|---:|---:|---:|---:|---:|
| N1/Roe | 64 | .02677204 | .05034115 | .02511757 | -.00021016 | .86731936 | .00467278 |
| N1/Roe | 128 | .01805056 | .02985973 | .01555982 | -1.72e-8 | .85622888 | .00126632 |
| LDA1/Roe | 64 | .02599585 | .05066510 | .02413768 | -.00020988 | .95593310 | .00523558 |
| LDA1/Roe | 128 | .01725514 | .02942144 | .01472481 | -1.79e-8 | .87979085 | .00170709 |

Exact plateau vx=.84119485. LDA's maximum raw-node overshoot is approximately
13.6% atNx64 and4.6% atNx128; the binned velocity maxima are.890103/.865061.
N is smoother, with smaller positive excursions, but diffuses transitions.
LDA has a visible local oscillation near the rarefaction tail and some scatter
on the plateau. Its extrema and transverse velocity decrease under this
refinement. Neither method is described as strictly monotone or free of all
overshoots, and two resolutions alone are not a smooth-solution convergence
order measurement.

The severe negative trough of the previous gamma1.4/F1 results is absent from
these first-order gamma5/3 curves. Since EOS, temporal method, CFL, end time and
glass alignment also differ from that earlier campaign, this observation does
not isolate gamma or prove that every RK2 formulation is responsible. The
previous matched-IC F1/FE controls remain the appropriate evidence for the
temporal/mass-form sensitivity.

## Verification and review

- Both gamma5/3 uniform gates pass: max changes9.44e-16 (N),7.77e-16 (LDA).
- All six runs reach their requested endpoints with clean exits. All saved
  rho/p/mass are positive and finite; EOS and initial piecewise states checked.
- N/LDA initial state and mass arrays match bit for bit at each resolution.
- All saved coordinates remain bitwise unchanged; VertexVelocity is zero.
- Largest mass drift3.95e-16; largest energy drift8.08e-16 across all saved
  science snapshots. No floors/limiters or relaxed assertions were introduced.
- Source/config/IC/parameter/binary/snapshot hashes checked and rechecked.
- Native PNGs and two-page PDF show full profiles and contact/shock zoom.
  Both PDF pages rendered and visually reviewed, with legible legends and no
  clipping. All node scatter retained; PDF has no rasterized-text artifacts.

Review: `output/pdf/Sod_2d_Morton_review.pdf` in the archive. Native figures:
`figures/Sod_2d_Morton_profiles.png` and `figures/Sod_2d_Morton_zoom.png`.
No thesis insertion, Git commit/push, COSMA operation or additional RK2/moving
run in this task.

Primary reference: [Morton et al.2023](https://www.pure.ed.ac.uk/ws/portalfiles/portal/327346950/2204.01757v2.pdf).
