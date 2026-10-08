# Sod: static versus moving, with first-order LDA controls

2026-09-28, Codex. User asked whether the visible Sod oscillations disappear on
a static mesh, as they expected from Morton et al. (2023). Local figure review
only; no thesis edits or production solver changes.

## Result

**Static mesh does not remove the large undershoot of the current LDA/F1
method.** At the same resolution and time, static LDA/Gauss3/F1 gives
minimum vx=-0.729293, compared with -0.737816 for the retained moving case.
Their shock profiles are close. Static N is smoother but more diffuse.

Replacing the static LDA F1 update by its full forward-Euler predictor removes
the large negative-velocity trough with either Gauss3 or Roe residuals.
There is still a positive velocity overshoot, so these controls are not
oscillation-free or generally monotone. The comparison points to the temporal
update/mass choice as a follow-up, and establishes that movement and edge flips
are not necessary for this large undershoot. It does not prove an F1 coding
error or isolate each term of the F1 update. Adaptive timestep histories differ.

## Matched setup and provenance

New archive: `../../local_runs/sod_static_matched_20260928_v1/`.
Reused moving archive: `../../local_runs/sod_kh_lab_frame_20260924_v1/`.

- Same frozen source tar as the moving runs, base adc424ba93f8cb98ff494dd8e98b41fafcd2e98b;
  current solver source/Makefile/defines_extra hashes still match it.
  Four isolated native static builds, each with binary/header/Config/linkage/logs.
- Glass128^2, 16384 nodes in a unit periodic square. The displayed half-box tube
  has effective initial Nx=64, with all 8187 nodes at raw x in (0.25,0.75).
  Left/right (rho,vx,p)=(1,0,1)/(0.125,0,0.1), gamma=1.4.
- xi=2(x-0.25), tau=2t; final rawt=0.08 corresponds to tau=0.16.
  All five snapshots at rawt=0,0.02,0.04,0.06,0.08 retained.
- Same physical parameters as moving controls: CFL0.08, cap1/3000, lab frame.
  Static runs remove mesh regularisation/ALE flags and select the normal static
  full-mesh, internal equal-step path; N retains lumped RK2, LDA retains mixed F1.
  Unused mesh-shaping parameters are removed; all other physical parameters match.
- Forward-Euler controls retain RD_RK2_TOTAL_RESIDUAL with the existing
  RD_DIAG_PREDICTOR_ONLY guard. This applies one full predictor and stops before
  the F1 corrector. It is not the legacy two-call path selected by dropping RK2.
  Native logs confirm stage0 and no stage1. The FE Gauss/Roe pair differs only
  in residual selection, and F1/FE Gauss differs only by the predictor-only flag.
- One MPI rank per case, OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1, at most four
  concurrent cases. Four uniform gates precede four new Sod runs; two moving
  results are reused, not newly run. The longest new Sod run took about102s.

## Final diagnostics

L1 uses normalized current median-dual area m/rho over raw nodes in the tube.
Minima/maxima retain every selected node. Curves use 128 uniform xi-bin means
for display; all selected nodes remain visible as faint scatter.

| Case | Steps | Density L1 | Velocity L1 | Pressure L1 | vx min | vx max |
|---|---:|---:|---:|---:|---:|---:|
| Static N/Roe, lumped RK2 | 512 | .023940782 | .054246347 | .023726125 | -2.127e-8 | .955527 |
| Moving N/Roe, lumped RK2 | 917 | .023602714 | .055143007 | .026777762 | -2.164e-8 | 1.010871 |
| Static LDA/Gauss3, F1 | 873 | .015722189 | .039171070 | .014947339 | -.729293 | 1.042155 |
| Moving LDA/Gauss3, F1 | 970 | .016941941 | .044340574 | .018065938 | -.737816 | 1.059127 |
| Static LDA/Gauss3, Euler | 512 | .023236284 | .054966856 | .022895714 | -1.604e-8 | 1.169484 |
| Static LDA/Roe, Euler | 512 | .023150062 | .054639549 | .022799144 | -1.710e-8 | 1.138474 |

Static N and both FE controls use constant actualdt0.00015625. Static F1 and
both moving runs use dt0.000078125--0.00015625. Equal timesteps means common to
all nodes within a run, not identical histories between cases.

All static saved coordinates remain bitwise fixed and vertex velocities zero.
Initial states match the moving controls to1e-14. Source/config/IC/parameter/
binary hashes verified; four uniform gates pass at <1e-12. All saved states
remain positive and finite. Moving errors reproduce the retained summary to
1e-14. Static final mass/energy changes are within4e-16, while the original
moving conservation drifts are unchanged and retained in summary.json.
Smaller F1 L1 errors are not evidence of monotonicity or absence of overshoots.

## Morton 2023 comparison

Checked the original §5.1.1 and Figure7 in the
[author manuscript](https://www.pure.ed.ac.uk/ws/portalfiles/portal/327346950/2204.01757v2.pdf).
The paper uses first-order temporal LDA1/N1, gamma5/3, CFL0.4 and a regular
Cartesian point distribution with alternate rows offset by half a spacing.
It explicitly reports LDA1 oscillations near x=0.5 that decrease with resolution;
N has smoother, more diffuse transitions. Thus the paper does not claim LDA1 is
entirely free of oscillations. The severe negative shock-front trough in the
current F1 curves is distinct from that statement.

Our new FE controls keep glass/gamma1.4/CFL0.08 to isolate changes within the
current setup. They are not a reproduction of Morton Figure7; regular geometry,
EOS, CFL and the original solver remain unmatched. Final time is not specified
in that section/caption, so no paper-matched final time is asserted.

## Figures and files

`output/pdf/sod_static_review.pdf` has three pages, each also a native PNG/PDF:

1. Four physical-variable profiles, N and LDA columns, static/moving overlaid.
2. Contact/shock density and velocity zoom, same comparison.
3. Static LDA F1/Gauss3 versus forward Euler with Gauss3 and Roe.

All pages rendered and visually checked. Scripts are
`tests/rd/run_sod_static_preview.py` and `tests/rd/analyze_sod_static_preview.py`;
archive copies and dependencies, bin CSVs, summary/provenance and verification
are retained. No solver/default-config changes, thesis edits, commit/push or
COSMA operations.
