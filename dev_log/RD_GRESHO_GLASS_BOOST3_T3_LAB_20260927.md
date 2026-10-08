# Gresho glass48, boost3, t3: N/LDA static versus moving

2026-09-27. Author: Codex. User requested an additional figure at boost velocity3
and time3, comparing N and LDA on moving and static meshes. Same glass and lab
frame as the preceding campaigns.

## Setup and provenance

Archive: `../../local_runs/gresho_glass_boost3_t3_lab_20260927_v1/`.
The four frozen LocalMac binaries from `gresho_glass_boost10_lab_20260927_v1`
are copied without rebuilding and verified against their recorded hashes.
Each retains its original Config, generated header, build log, version,
linkage and source provenance. `source` and `source.tar` reference the frozen
source archive. Config audit verifies static/moving, N/LDA, Gauss3 selection,
absence of element co-moving evaluation and absence of topology repair.

The original boost10 input is copied and only vx is reduced by7. Coordinates,
IDs, density and internal energy remain bitwise identical. All four methods
share this input: genuine SWIFT glass48 (2304 nodes), unit periodic box,
gamma5/3, boost(3,0). N uses Roe residuals/lumped mass, moving N retains its
split mesh-velocity correction; LDA uses Gauss3/default mixed-stage F1.
Moving cases retain current Arpaia weights and mesh regularization.

CFL.3 and MaxSizeTimestep1/4096 are unchanged. With TimeMax3, AREPO's physical
integer-timebase interval is3/TIMEBASE, so the cap rounds down to the dyadic
step3/16384, approximately1.83105e-4. This differs from1/4096 used at TimeMax1.
Report the measured actual timestep, not the cap. Planned outputs0,.75,1.5,
2.25,3 are aligned with these steps. One MPI rank per run, OMP/BLAS1, maximum
four workers; no production/default configuration changes.

Four uniform and four short Gresho pilot runs complete to .046875 in256 steps.
Uniform maximum rho/v/p differences are2.653e-15 (N static),1.039e-13 (N moving),
1.860e-15 (LDA static),3.461e-15 (LDA moving), all below the original1e-12
threshold. Pilot states remain finite with positive density and pressure.

## Completed results

All12 new cases have completed normally, with no native assertion failure.
All four science cases reach t3 in16384 steps, with identical complete timestep
histories and constant actual dt3/16384. Their initial snapshots are bitwise
identical by ID in coordinates, rho, velocities, pressure and mass. All20 stored
science snapshots have finite states and positive rho, pressure and mass.
Static coordinates remain bitwise fixed. No active solver workers remain.

Final errors are mass-weighted over all2304 native nodes after subtracting the
known boost from velocity and translating back the analytic periodic center.
No fitted center, interpolation, binning or subsampling is applied.

| Method | Mesh | vphi L1 | Peak vphi | Relative total-mass drift |
|---|---|---:|---:|---:|
| N/Roe | static |0.23991685|0.136456|−1.11e-16|
| N/Roe | moving |0.04720931|0.729197|+1.42443e-4|
| LDA/Gauss3 | static |0.22266181|0.898705|−2.22e-16|
| LDA/Gauss3 | moving |0.01260077|0.902427|+1.77547e-4|

Moving/static error ratios are0.196774 (N) and0.056592 (LDA), approximately
5.08x and17.67x lower error. Static N has strongly damped the vortex. Static
LDA retains a substantial peak, but the radial profile is broad and distorted,
with a minimum vphi of−0.69283. Moving LDA follows the analytic triangular
profile much more closely; its peak height alone does not distinguish it
well from static LDA, so the full profile/error comparison matters.

Moving total-energy relative drift is−7.6013e-5 (N) and−1.31865e-4 (LDA),
while static total-energy drift is zero at output precision. The small moving
global drift remains a limitation; no new conservation correction was enabled.
This is a single-resolution static/moving comparison. Do not combine the
boost3/t3 and earlier boost10/t1 results into a same-time boost-invariance test.

## Figure and checks

`output/pdf/gresho_glass_boost3_t3_lab_static_moving.pdf` and
`figures/gresho_glass_boost3_t3_lab_static_moving.png` use separate N/LDA panels,
static crosses, moving dots and a dashed analytic curve. Axes include every
native point, including the negative static-LDA tail. Legends sit below the
axes so they do not cover data. The final PDF was rendered and visually checked
for readable labels, full data bounds and overlap. `summary.json` preserves
all five times, both mass/area norms, vector-velocity errors, global totals
and native diagnostics. Binary/input/parameter/source hashes were rechecked.

The new reusable preparation helper is `tests/rd/run_gresho_glass_boost_controls.py`.
The existing plot analyzer now reads boost, endpoint and output times from
the campaign instead of hardcoding boost10/t1, and verifies full timestep
histories match. Earlier archived results and scripts are preserved. No thesis
change, commit, push or COSMA operation.
