# Static N boost0 control for the glass48/t3 moving Gresho preview

2026-09-27. Author: Codex. User requested adding static mesh, boost0, t3
to the left (N) panel of the existing standalone moving N/LDA boost0/10
figure. The purpose is to show the benefit for vortex rotation even without
bulk translation. Standalone preview remains the requested scope.

## Matched setup and checks

New archive:
`../../local_runs/gresho_glass_t3_static0_overlay_20260927_v1/`.
Reused four moving runs:
`../../local_runs/gresho_glass_moving_boost0_10_t3_lab_20260927_v1/`.

New static N/Roe+lumped run uses the exact frozen static binary from log3
section128, SHA256
`f1c101c4db55ed9c32dfe0b85e2bbcc8b5603c245f162fa572078ea7d7c1b8f5`.
The source tar, Config, generated header, linkage/build logs, parameters,
input and binary hashes are preserved. No rebuild or production-code change.
All155 audited source/build files still match the frozen archive. One rank,
OMP_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1; only one new solver at a time.

Same2304-node glass48, periodic unit box, gamma5/3, lab frame, CFL0.3,
cap1/4096 and endpoint3. Uniform and pilot runs complete at .046875 in256
steps; uniform max changes are rho7.55e-15, velocity6.08e-15, pressure2.49e-14,
below the original1e-12 gate. Science completes normally in201.91 seconds,
16384 steps with actual dt3/16384. All five displayed science cases have
identical full logged time/step histories. Static0 and moving0 N opening
snapshots have bitwise-identical IDs, positions, rho, velocity, pressure and
mass. Static coordinates remain bitwise fixed at all five saved times.
All25 science snapshots checked are finite with positive rho, pressure and
mass. The four moving results, their summary and original PDF are unchanged.

## Results and interpretation

Azimuthal-velocity L1 uses final mass weights over all2304 native nodes.
Profiles use the known analytic periodic center and subtract the imposed
velocity boost. No fitted center, binning or interpolation.

| Method | Boost | vphi L1 | Peak vphi |
|---|---:|---:|---:|
| N static |0|0.12085623|0.485980|
| N moving |0|0.04724472|0.735437|
| N moving |10|0.04707784|0.741639|
| LDA moving |0|0.01252980|0.897588|
| LDA moving |10|0.01249125|0.893963|

For N at boost0, moving/static L1=0.39091671, a60.91% reduction (factor2.558).
Area-weighted errors are0.12048805/0.04715843; velocity-vector mass-weighted
errors0.12831442/0.04903911. The lower/broader static peak and its wider outer
tail show stronger damping. Thus the figure supports reduced numerical
damping of the unboosted rotating vortex in this experiment. Local orbital
fluid motion remains nonzero even when the bulk boost is zero.

This is a matched test of two mesh evolutions; it does not isolate an
individual flux, regularization or connectivity mechanism. The original
boost0/10 near-overlap still supports weak sensitivity of these profiles to
bulk boost, rather than exact invariance of complete mesh/state trajectories.
See the [moving-pair report](RD_GRESHO_MOVING_BOOST0_10_T3_20260927.md) for
the measurable ID-paired mesh/state differences. Static total-mass relative
drift is-6.66e-16 and energy drift0 at t3; moving N0 remains+1.519e-4 in mass
and-2.087e-4 in total energy. Reduced profile damping and global conservation
are separate properties.

## Figure and delivery

`tests/rd/analyze_gresho_static0_overlay.py` audits all five cases, verifies
reused snapshot hashes and exact reproduction of their existing metrics,
and creates a separate revised figure. Gray squares add static N/boost0 on
the left. Moving boost0 orange crosses and boost10 green/blue dots remain;
the right LDA panel retains the same data. Shared axes include all points;
legends sit below the axes. The general title now includes both mesh modes.

PDF: `output/pdf/gresho_glass48_t3_moving_boost0_10_static0.pdf`.
Display PNG: `figures/gresho_glass48_t3_moving_boost0_10_static0.png`.
PDF SHA256:
`b5a7cca0dd9e7596272294c82a93e41bf04bbd99b6c9d07cab2f3548e305dd46`.
The final PDF was rendered and visually checked: aligned panels, readable
labels/legends, no clipped points or overlapping text. Summary, copied
analysis scripts and provenance, native gates, raw outputs and verification
are in the archive. All new runs have ended; no active solver remains.
No thesis edit, commit, push or COSMA operation.
