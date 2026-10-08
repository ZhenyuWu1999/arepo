# Gresho figure readiness for Chapter 4.3.2

**Latest standalone preview (log3 §132):** Added static N, boost0, t3 to
the left panel, using a new matched glass48 run. Static0 L1 .120856 versus
moving0 .0472447, a60.91% reduction; static/moving peaks .485980/.735437.
All five cases use identical timestep histories and the initial N0 fields
match bitwise. This supports less damping of the vortex's own rotation.
The original moving profiles remain unchanged; PDF visually checked. See
[static0/t3 overlay report](RD_GRESHO_STATIC0_T3_OVERLAY_20260927.md).
Still a separate preview, with no thesis insertion.

**Current user-selected standalone preview (log3 §131):** Glass48, t3, moving
N/LDA at boosts0/10 is complete. User explicitly chose to preview separately,
so no thesis insertion yet. Two-panel PDF compares the boosts within each
scheme; N errors .0472447/.0470778, LDA .0125298/.0124913. Profiles overlap
closely, while mesh/state trajectories retain measurable differences. See
[the selected boost0/10 t3 report](RD_GRESHO_MOVING_BOOST0_10_T3_20260927.md).

**New requested boost3/t3 figure (log3 §130):** Four N/LDA static/moving cases
now complete on the same glass48, lab frame, all16384 steps to t3. Profile PDF
is ready; N static/moving errors .239917/.0472093, LDA .222662/.0126008. See
[the boost3/t3 report](RD_GRESHO_GLASS_BOOST3_T3_LAB_20260927.md). This supersedes
the earlier decision to defer boost3. It has a different endpoint from the
boost0/10 t1 figures, so it is not a same-time boost-invariance control.

**Additional N boost0 controls (log3 §129):** Static0 and moving0 now complete
on the same glass, binaries and time steps as boost10. New N-only boost0/10
figure compares both mesh modes. Moving10 is better than static0; moving0/10
vphi error norms differ by0.1144%, but the mesh/state are not identical. See
[the N boost comparison](RD_GRESHO_N_BOOST0_CONTROLS_20260927.md). LDA0 remains
unrun; do not extend the N boost-sensitivity conclusion to LDA.

**Superseding user choice and completed work (2026-09-27, log3 §128):** Use
genuine glass48, laboratory frame only, with matched static/moving controls;
do boost10 first and defer boost3. The new four-case t1 comparison is complete
with passing uniform/pilot gates, matching4096 steps and a reviewed two-panel
PDF. See [the glass boost10 report](RD_GRESHO_GLASS_BOOST10_LAB_20260927.md).
The jitter campaign and proposed boost0/3/10 layout below are historical
readiness notes, not the current figure plan.

2026-09-27. Author: Codex. Requested: inspect the local boosted Gresho figures
and prepare a boost0/3/10 comparison after inserting the two Yee figures.

## Existing current-source results

The September24 archive is
`../../local_runs/gresho_frame_20260924_v1/`.
It contains eight completed moving-mesh cases: N/Roe+lumped and
LDA/Gauss3+F1, laboratory/co-moving evaluation, boost0/10. Each final HDF5
snapshot was reopened: t=1,2304 nodes,4096 steps per run. All153 recorded
production/build-file hashes agree with the current local repository.
The setup uses jitter48 squared, seed20260811, gamma5/3 and a periodic unit
box. No new simulation was launched during this audit.

- `figures/gresho_profiles.png`: four panels, N/LDA by row and lab/co-moving
  by column; each overlays boost0 and10 after removing the boost.
- `../yee_frame_convergence_20260924_v1/figures/gresho_boost10_frames.png`:
  de-boosted node maps and radial profiles for boost10, comparing both frames.
  This figure also has a PDF.
- LDA peak azimuthal velocity is about0.9391 for both boosts/frames, versus
  analytic1. N peaks are0.8524 at boost0 and0.8590 at boost10. The plots show
  near-overlap under the boost, with a visibly broader/lower N peak.
- The displayed old profile L1 annotations are median-dual-area weighted;
  a final figure using mass weighting like the new Yee figure must recompute
  those metrics from the available snapshots and label the definition.

The original report preserves the N/lab uniform-gate pressure discrepancy
(1.1822e-12 against the original1e-12 absolute threshold). Completion and
similar plotted profiles do not erase that failed gate or establish exact
Galilean invariance or global conservation.

## Missing matched comparisons

| Proposed arm | boost0 | boost3 | boost10 |
|---|---|---|---|
| N moving, co-moving evaluation | available | missing | available |
| LDA moving, co-moving evaluation | available | missing | available |
| N static, laboratory evaluation | new matched control needed | new matched control needed | new matched control needed |
| LDA static, laboratory evaluation | new matched control needed | new matched control needed | new matched control needed |

The Chapter3 static controls are glass48 at t3; these are not the jitter48/t1
controls for the current moving set. Historical boost0/3/10 images do exist
at `../useful_resources/KH_moving_mesh/gresho-boost-fraction-profiles.png`,
but log2 section57.1 identifies that earlier section49 experiment as jitter,
gamma1.4 and LDA/Roe+split, with varied Lagrangian fraction. Do not combine
its boost3 panel with the current LDA/Gauss3 data.

For a static/moving figure, a possible layout is three columns for boost0/3/10,
with N and LDA in two rows; static crosses and moving dots share the analytic
curve and fixed axes. Keep N green and LDA blue to match Yee. If only moving
mesh is desired, plot the two schemes in each of three boost panels instead.
This is a layout proposal; no assumption about the user's final choice or
new-run authorization is made. Matched future controls should share the same
IC coordinates, endpoint and actual timestep (1/4096 for the archived moving
runs). The TeX source reserves the Gresho insertion point as comments.

Audit and snapshot hashes:
`../../local_runs/chapter4_3_2_yee_figures_20260927_v1/gresho_readiness.json`.
