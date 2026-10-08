# Gresho boost profile style preview

2026-09-28, Codex. The user proposed grouping the Yee and Gresho boost tests
in §4.3.2 and asked for Chapter-3-style mean curves, fainter scatter, internal
legends, and shorter titles. The current response provides a standalone figure
preview and a structural recommendation; no thesis text was changed.

## Retained data

Exactly the five cases used in log3 §132: glass48, 2304 nodes, t=3,
moving N/LDA with boost0 and10, plus static N/boost0 in the left panel.
All use laboratory-frame evaluation, with the imposed translation removed
for plotting relative to the analytic periodic vortex centre. No fitted
centre or new simulation. Matched 16384-step histories and the native gates
are recorded in [the original report](RD_GRESHO_STATIC0_T3_OVERLAY_20260927.md).

The source summary, five final-snapshot hashes, and old PDF hash were checked.
Mass-weighted L1 errors reproduce the retained summary to 1e-15 absolute
tolerance. Raw data, original figure and thesis sources remain unchanged.

## Plot changes

- Match the Chapter 3 plotting script: 35 uniform radial bins over [0,0.7),
  unweighted nodal means. All2304 nodes fall in these bins in each case.
- Show all raw points, with alpha0.09 and size3. No subsampling, interpolation
  or smoothing. Empty bins would remain NaN rather than being bridged.
- Keep both mean profiles legible when they overlap: moving0 solid orange,
  moving10 dashed green (N) or blue (LDA), with staggered hollow markers.
  Static N0 remains grey. The analytic profile remains black dashed.
- Put legends in the upper-right corners; remove numerical L1 values from
  legend text. Full diagnostics remain in the JSON record and are not computed
  from the bin averages.
- Title: `Gresho, glass 48^2, t=3`. Panel titles: `N`, `LDA`.

The new binned peaks are 0.448264 static N0, 0.703767/0.705309 moving N0/10,
and 0.874671/0.872432 moving LDA0/10. These are binned means, distinct from
the pointwise peaks in the original report. The original mass-weighted L1
values remain0.12085623,0.04724472/0.04707784,0.01252980/0.01249125.

## Proposed section organisation

Use one subsubsection, `Boosted vortex tests`, with successive Yee and Gresho
discussions. Yee establishes the observed convergence and static/moving
comparison; Gresho complements it with rotational-profile preservation and
boost0/10 sensitivity. Retain the two Yee figures and this separate Gresho
figure. Close radial-profile agreement is not a proof of exact invariance of
the entire mesh/state; see the original experiments' limitations.

When actually merging the prose, keep the frame settings explicit: the current
Yee moving data use element co-moving evaluation, while these Gresho cases use
laboratory-frame evaluation. The existing sentence `For these boosted tests`
in the Yee subsection should be narrowed to the Yee cases if the heading is
broadened. This is a proposed edit, not an edit made in this preview task.

## Artifacts

Archive: `../../local_runs/gresho_boost_style_preview_20260928_114134/`.
PDF: `output/pdf/gresho_glass48_t3_boost_profiles_mean.pdf`.
PNG: `figures/gresho_glass48_t3_boost_profiles_mean.png`.
PDF rendered and inspected; legends/labels readable, no clipping. Five CSVs
store bin centres, means and counts. Summary and verification preserve hashes,
style choices and diagnostics. A proposed caption is also saved in the archive.
Reusable plot script: `tests/rd/plot_gresho_boost_preview.py`; the archive holds
a copy and its dependencies, including the Chapter3 style reference.

No thesis insertion, commit/push, solver build/run or COSMA operation.
