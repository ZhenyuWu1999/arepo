# Sod_2d_Morton

Morton et al. (2023), §5.1.1 / Fig.7 primitive states, gamma5/3 and first-order
static LDA/N, using a relaxed glass instead of the paper's row-offset mesh.
This is an AREPO-RD comparison, not a bitwise reproduction of the original RD
program. No production solver/default configuration is changed.

- Periodic2×2 box; high state rho1,p1 in .5<X<1.5, low state rho.125,p.1
  outside; velocity initially zero, gamma5/3.
- Show the right-hand tube1<X<2, labelled x=X-1 (formerly xi), with time t. No factor2 in time for
  this box. Endt=.2 follows the local standalone SODX constants; the published
  Fig7 section/caption does not explicitly state its output time.
- Effective initial Nx64/128 means full box128²/256². Both use the same
  wrapped relaxed glass128; the finer cloud is periodic2×2 tiling scaled into
  the box. There are no literal glass columns.
- Both schemes use Roe parameter-vector residuals and a full forward-Euler
  update via the existing predictor-only guard. Merely dropping the RK2 flag
  would enter a different legacy update path.
- CourantFac=.4; timestep cap.02. AREPO's carrier/tree limit and dyadic rounding
  remain in use, not the standalone code's nodal RD CFL expression.
- Two uniform-state gates precede four Sod runs; one rank per run, at most2
  concurrent, OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1.
- Source/config/binary/IC/parameter hashes, build/linkage/run logs, five
  snapshots, all-node scatter and area-weighted errors are retained.

Run from the AREPO repository, using a fresh output directory:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
PY=/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python
$PY examples/Sod_2d_Morton/run.py prepare /absolute/new/archive
$PY examples/Sod_2d_Morton/run.py build /absolute/new/archive
$PY examples/Sod_2d_Morton/run.py uniform /absolute/new/archive
$PY examples/Sod_2d_Morton/run.py science /absolute/new/archive
$PY examples/Sod_2d_Morton/analyze.py /absolute/new/archive
```

Preparation deliberately verifies the current solver against the frozen
September28 static archive; it stops if the production source has changed.
`--control` and `--glass` override the corresponding archive/input paths.
New runs never overwrite existing run logs or build artifacts.

Initial campaign: `../../../local_runs/Sod_2d_Morton/20260928_v1/`.

## Matched moving-mesh and time-update variants

`run_variants.py` retains exactly the same ICs, gamma, physical box, output
times, CourantFac and timestep cap. It reuses the four completed Euler/Roe
controls after verifying provenance, and adds seven configurations at both
effective resolutions:

| Scheme | Update | Residual | Mesh |
|---|---|---|---|
| N | lumped RK2 | Roe | static / moving |
| LDA | Euler | Gauss3 | static |
| LDA | F1 | Roe | static / moving |
| LDA | F1 | Gauss3 | static / moving |

These are lab-frame, equal-timestep runs. Moving Roe uses the explicit mesh
velocity split; moving Gauss3 uses contour quadrature. The current native
split-stage entry rejects predictor-only diagnostics, so a moving Euler case
is not fabricated by combining incompatible flags. No solver guard is changed.
The existing first-order comparisons remain static controls. No hierarchy,
element co-moving residual evaluation, limiter, or N/Gauss experiment is added.

Each new binary first passes a moving/static uniform-state gate at gamma5/3.
The seven builds are isolated; the fourteen science runs use at most two
workers, one MPI rank each and both threading variables set to one. Adaptive
time histories are recorded individually: equal CFL does not mean equal dt.

```sh
$PY examples/Sod_2d_Morton/run_variants.py prepare /absolute/new/archive
$PY examples/Sod_2d_Morton/run_variants.py build /absolute/new/archive
$PY examples/Sod_2d_Morton/run_variants.py uniform /absolute/new/archive
$PY examples/Sod_2d_Morton/run_variants.py science /absolute/new/archive
$PY examples/Sod_2d_Morton/analyze_variants.py /absolute/new/archive
```

The default `--control` is the initial `20260928_v1` archive. The runner checks
the frozen source and IC hashes and refuses to overwrite run logs. Analysis
retains failure records and never labels a partial snapshot as a final result.
It verifies the complete configurations/stages, initial states, saved-state
positivity/EOS, conservation changes, static positions and actual motion.
Plots use all raw tube nodes and 128-bin means; L1 errors use normalized
current dual-area weights on raw nodes. Final profiles are grouped by mesh,
time update and LDA residual to keep each comparison readable.

Expanded campaign: `../../../local_runs/Sod_2d_Morton/20260928_full_v1/`.

## Display-coordinate convention (2026-09-28)

The user accepts t=.2 as the comparison output time for Morton. This is the
adopted comparison convention; the source-evidence qualifications above remain.
To simplify figures, write the raw simulation coordinate as X and label the
displayed coordinate x=X-1, over0<x<1, with time t unchanged. This x has exactly
the values previously called xi. The left tube0<X<1 carries the reversed
primitive-state pattern, so the raw X=0 and X=2 periodic boundaries have the
same low state. The selected right tube1<X<2 has its initial jump at x=.5.
This is a translation, not a length/time rescaling or a claim of exact mirror
placement of individual glass nodes. Existing IC/metadata/CSV xi keys remain
unchanged for provenance; the updated plotting labels are x and t.

Coordinate-label presentation review:
`../../../local_runs/Sod_2d_Morton/20260928_display_x_v1/`.

## Focused first-order / RK2 comparison (2026-09-28)

The main review now has three numerical curves per scheme: static first-order
RD, static RK2 and moving RK2. First-order RD is the full-dt predictor used as
the next state, with no corrector or F1 temporal mass term. The implementation
keeps `RD_RK2_TOTAL_RESIDUAL` and uses `RD_DIAG_PREDICTOR_ONLY` to exit after
stage0; simply removing the RK2 flag would select a different legacy path.

N uses Roe for all three curves, with mesh split when moving. LDA uses Roe for
the Morton-style first-order baseline and Gauss3 contour with F1 for both RK2
curves, following the thesis default. The LDA first-order/RK2 contrast thus
changes both time integration and residual; the static/moving RK2 pair uses
the same residual family. The other completed variants remain diagnostics.

```sh
$PY examples/Sod_2d_Morton/plot_main_comparison.py \
  /absolute/completed/full/archive /absolute/new/presentation/archive
```

This command verifies the final snapshots and existing bin means, checks input
hashes before and after plotting, and creates two pages (effective Nx128 then64)
without rerunning hydrodynamics. It retains every raw node and 128-bin means.
Latest local review: `../../../local_runs/Sod_2d_Morton/20260928_main_comparison_v3/`.
The v3 style displays only rho, vx and p, with distinct dashed numerical curves,
a solid exact solution, the title `Sod shock tube, Nx = ..., gamma = 5/3, t = 0.2`,
and no footer. PNG output and PDF scatter layers use600dpi; PDF lines/text stay
vector. Method metadata and lab-frame coordinates remain unchanged.
The previous v2 archive retains `audit_internal_energy.py` /
`internal_energy_audit.json`, which verify stored
specific internal energy against p/[(gamma-1)rho] at all final snapshot nodes
and record corresponding rho/p/e extrema near the contact and shock.
