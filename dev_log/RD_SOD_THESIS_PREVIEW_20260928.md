# Sod figures for local thesis review

2026-09-28, Codex. User requested inserting the approved Gresho colour revision
into Chapter 4.3.2 with little prose, then preparing a more substantial set of
Sod figures for local review. The Sod figures have not been inserted into the
thesis. No new hydrodynamics runs were needed.

## Figure set

Latest archive: `../../local_runs/sod_thesis_preview_20260928_v2/`.
The three-page `output/pdf/sod_review.pdf` contains:

1. **Full profiles**: density, x velocity, pressure and specific internal energy
   at final time, comparing moving N and LDA with the exact Riemann solution.
2. **Contact and shock**: contact density and shock density/velocity/pressure
   at the same time, with common scales between methods. Dotted vertical lines
   mark the analytic contact and shock locations.
3. **Density evolution**: N/LDA rows at tube times 0, 0.08 and 0.16, showing
   the central strip of the periodic box with one common density scale.

Each page also has a separate PDF and native PNG. Version 1 is retained as an
intermediate layout; version 2 reduces empty space between the density maps.
Use `tests/rd/plot_sod_thesis_preview.py` to reproduce from retained snapshots.

## Data and plotting conventions

Source: `../../local_runs/sod_kh_lab_frame_20260924_v1/`, specifically the
`sod_N_roe_split_sod_lab` and `sod_LDA_gauss3_sod_lab` runs. The current-source
lab-frame experiment and its limitations are recorded in
[the September 24 report](RD_SOD_KH_LAB_FRAME_20260924.md).

- Periodic unit square, relaxed glass with 128^2 = 16384 initial nodes;
  the displayed tube is raw x in (0.25,0.75), full transverse extent for profiles.
  Thus h=1/128 and effective initial tube Nx=0.5/h=64; this is not 64 literal
  columns on an irregular mesh. Both final profiles select 8187 nodes.
- Left (rho,vx,p)=(1,0,1), right=(0.125,0,0.1), gamma=1.4.
  The tube coordinate is xi=2(x-0.25); tube time tau=2t. Final raw t=0.08
  therefore corresponds to tau=0.16, not 0.08.
- Moving equal-step, laboratory-frame residual evaluation, one MPI rank.
  N uses Roe split with the complete mesh correction and lumped temporal mass;
  LDA uses Gauss3 and the existing F1 temporal update. The two runs have the
  same CFL=0.08 and timestep cap=1/3000, but distinct adaptive histories
  (917 N steps, 970 LDA steps). No claim of matched per-step timesteps.
- All selected nodal values are shown as faint scatter. Lines are arithmetic
  means in 128 uniform xi bins, with no fitting or smoothing. Errors use the
  individual nodes and normalized current median-dual area m/rho, not the bins.
- Specific internal energy comes from the snapshot and is checked against
  p/[(gamma-1)rho]. The analytic solution uses the retained AREPO Riemann solver
  at the same physical coordinates and raw time.
- Density maps show raw x in [0.25,0.75], y in [0.35,0.65], at raw t=0,0.04,0.08.
  They use Gouraud interpolation on a Delaunay triangulation reconstructed from
  saved coordinates, not a diagnostic of the native mesh connectivity.
  One fixed colour range [0,1.1] contains all saved density values.

## Checks and observed limitations

Source archive, source Riemann solver, binary, Config, IC and parameter hashes
were checked against retained provenance; snapshot and input hashes are saved
in the new summary and rechecked after plotting. Initial N/LDA states match
exactly. All five saved times in each run retain positive density and pressure.
The three original final L1 metrics reproduce to absolute tolerance 1e-14.
Both final PDFs and native PNGs were reviewed visually.

| Quantity | N | LDA |
|---|---:|---:|
| Density L1, dual-area weighted | 0.023602714 | 0.016941941 |
| x-velocity L1 | 0.055143007 | 0.044340574 |
| Pressure L1 | 0.026777762 | 0.018065938 |
| Specific internal-energy L1 | 0.069177668 | 0.057356349 |
| Minimum x velocity, selected tube | -2.1643e-8 | -0.73781636 |
| Relative total-mass change, full box | -1.85026e-4 | -7.81142e-4 |
| Relative total-energy change, full box | -6.10914e-4 | -1.44364e-3 |

N is visibly more diffuse; LDA resolves sharper fronts but retains substantial
velocity/density/pressure undershoots. LDA's smaller L1 error does not establish
monotonicity or absence of oscillations. These are one-resolution moving runs,
not a static/moving comparison or a convergence study. The conservation drifts
remain part of the diagnostic record. No limiter, solver, threshold or data
selection was changed to improve appearances.

## Gresho insertion

Chapter 4.3.2 now uses the shared heading `Boosted vortex tests`. The approved
Gresho figure is Figure 4.8, with one short paragraph and a descriptive caption.
The Yee co-moving-frame statement is explicitly limited to Yee; Gresho is
identified as lab-frame. A page break flushes the three vortex figures before
the retained red implementation draft, whose text is unchanged.

Thesis archive: `../../local_runs/thesis_gresho_sod_preview_20260928_v1/`.
The compiled thesis has 249 pages; Figure 4.8 is on printed page 168 (PDF page
190). The numerical-test text is on printed page 165. Existing Chapters 1--3,
the implementation overview, derivations, and retained red draft were not
edited. No unresolved references or LaTeX errors. Local `master.pdf` is updated.
No Git commit/push or Overleaf/COSMA operation.
