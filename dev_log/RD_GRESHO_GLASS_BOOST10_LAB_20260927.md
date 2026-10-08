# Gresho glass48, boost10: laboratory-frame static/moving comparison

2026-09-27. Author: Codex. User requested genuine glass ICs, lab frame only,
comparison with static mesh, and boost10 first; boost0/3 were not launched.

## Setup and reproducibility

Archive: `../../local_runs/gresho_glass_boost10_lab_20260927_v1/`.
Source frozen from local `2858d43` plus the existing working tree. No numerical
source or default Config was edited. The frozen source, working-tree patch,
tracked-file hashes and source tar hash are archived. Four independently built
LocalMac executables each retain their Config, generated header, build log,
binary hash, version and dynamic linkage. Both OMP and OpenBLAS threads were1;
each case used one MPI rank, with at most four cases concurrent.

- N/Roe + lumped time mass and LDA/Gauss3 + default mixed-stage F1.
- Each has static and moving controls, all with **lab-frame evaluation**;
  `RD_ELEMENT_COMOVING_FRAME` is absent in all four generated headers.
- Moving: current one-rebuild begin/end hooks, Arpaia modified coefficients,
  standard mesh regularization, RD spectral CFL bound, no topology repair.
  N moving enables the existing split mesh-velocity correction.
- Unit periodic box, gamma5/3, boost(10,0),2304 nodes, analytical Gresho IC.
  Source is `lda_baseline_glass_20260911/inputs/glassPlane_48.hdf5`, SHA256
  `157e1a4767f4678df4cd80d2df9aa248fa520899e12e777a448e17f31e47d88f`.
  One coordinate component slightly beyond1 is wrapped modulo1 before state
  evaluation. These are genuine glass positions, not jittered lattice points.
- CFL.3, common timestep cap1/4096, min_dt1e-8. All four science runs actually
  use4096 equal steps to t1; Systemstep is constant and agrees with1/4096 at
  the printed precision. The four t0 snapshots are bitwise identical by ID
  in coordinates, rho, velocity, pressure and mass. Static positions remain
  bitwise fixed. Science outputs are t0,.5,1.

Uniform controls and short Gresho pilots run to .03125,128 steps each. All four
uniform controls pass the existing absolute1e-12 criterion for rho, velocity
and pressure. Maximum changes over those fields are2.043e-13 (N static),
3.331e-13 (N moving),1.874e-13 (LDA static),2.363e-13 (LDA moving). All four
pilots and all four science runs exit normally, retain finite positive rho
and pressure at every stored snapshot, and trigger no native assertion.
No tolerance was relaxed. All12 new cases are complete; none remain running.

## Results at t=1

The profile uses the known periodic center (0.5+10t,0.5), with (10,0) removed
from the velocity. It plots every native node, with no fitted center, binning,
interpolation or subsampling. The displayed error is
`sum_i m_i(t) abs(vphi_i - vphi_exact(r_i)) / sum_i m_i(t)` over all2304 nodes.
The archive also stores the separate median-dual-area weighted norm and the
mass-weighted Euclidean velocity-vector error.

| Scheme | Mesh | Mass-weighted vphi L1 | Peak vphi | Relative mass drift |
|---|---|---:|---:|---:|
| N/Roe | static |0.23996020|0.153450|−3.33e−16|
| N/Roe | moving |0.01890833|0.853379|+3.70739e−5|
| LDA/Gauss3 | static |0.16350141|0.852928|−1.11e−16|
| LDA/Gauss3 | moving |0.00717532|0.953356|+4.13801e−5|

Moving/static L1 ratios are0.07880 (N) and0.04389 (LDA), approximately12.7x
and22.8x lower errors. Static N is strongly diffused; static LDA retains a
substantial peak but has a broad distorted profile, including negative vphi.
Moving LDA tracks the analytic triangular profile more closely than moving N.
The final figure includes the full negative static-LDA tail (minimum−0.38245).

Relative total-energy drift is+2.71762e−5 (N moving) and+2.48148e−5 (LDA moving),
versus roundoff for static controls. Small global drift remains despite local
residual assertions passing. This experiment alone does not separate topology
transfer from endpoint-weight conversion contributions. Existing SVD fallback
and F1 lumped fallback are active where triggered; no new regularization is
introduced. Raw diagnostic extrema remain in `summary.json`.

This supports omitting boost3 if the purpose is a compact illustration of
moving versus static mesh at strong bulk advection. A single boost/resolution
does **not** establish Galilean invariance or convergence order. A matched
glass boost0 control would serve the former question if later requested.

## Deliverables and checks

- `output/pdf/gresho_glass_boost10_lab_static_moving.pdf`: two panels N/LDA,
  each showing static/moving and analytic profiles, all lab frame.
- `figures/gresho_glass_boost10_lab_static_moving.png`: display version.
- `summary.json`, `analysis_provenance.json`, gate/status files and all raw
  inputs/snapshots/logs: numerical and provenance records.
- Repo helpers: `tests/rd/run_gresho_glass_boost_lab.py` and
  `tests/rd/analyze_gresho_glass_boost_lab.py`.

The PDF was rendered and visually checked for labels, legend, full data range
and clipping. The first draft clipped33 negative static-LDA nodes; the final
axis limits were expanded to include all nodes. Gate reporting was also
corrected to use printed Systemstep rather than differences of rounded Time
strings; this is a reporting change, with no rerun or timestep change. The
original frozen runner remains in the archive and the updated gate-audit helper
is preserved separately. Production hashes match the pre-build source manifest.
No boost3 run, thesis edit, commit, push or COSMA operation in this experiment.
