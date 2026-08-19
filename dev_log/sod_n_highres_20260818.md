# High-resolution moving-N Sod test with the selected default ALE form

Date: 2026-08-18

## 1. Question and numerical form

The preceding residual x frame x mass factorial showed only small differences
between the eight moving-N combinations, while every moving combination had
more transverse noise than its static/zero-mesh controls.  This test asks
whether that defect remains visually and quantitatively important at higher
resolution when the intended default mathematics is used:

- N distribution with the two-stage RD RK update;
- contour-integral element total residual;
- element co-moving algebraic frame;
- Arpaia temporary ALE nodal mass;
- equal timesteps, CFL 0.4, mesh regularisation enabled;
- all RD debug assertions and Stage-0 ALE geometry diagnostics enabled.

The run reaches t=0.2 with the same periodic Morton-style Sod states and
gamma=5/3 as the glass48 factorial.

## 2. Mesh and resolution caveat

The high-resolution IC has 9216 generators (effective n=96).  It uses the
previously validated `swift48_tiled` geometry from the hierarchy campaign and
reconstructs the current 2 x 2 Sod state from its normalized coordinates.
It is therefore a relaxed-glass high-resolution diagnostic, not an independent
glass realization: the n=96 point set periodically tiles the glass48 pattern.
The comparison is sufficient to test whether the observed oscillation persists
when h is halved, but it must not be quoted as a formal independent-family
convergence order.

## 3. Robustness result

The one-rank run completed normally:

- 250 synchronized updates and 21 snapshots through t=0.2;
- 2042 actual edge flips, first appearing at t=0.0125;
- zero inverted cells and zero non-positive temporary masses;
- no SVD fallback or exactly singular element at the endpoint;
- endpoint RK predictor minima rho=0.12597 and p=0.10130;
- no hidden termination or non-finite output.

An initial four-rank launch stopped at t=0 before a physical update because
`RD_ALE_GEOMETRY_DIAGNOSTICS` Stage 0 deliberately rejects more than one MPI
rank.  Its output is preserved as `output_failed_np4_diagnostic_guard`.  This
was a diagnostic configuration guard, not a numerical failure.

## 4. glass48 versus glass96 at t=0.2

| metric | glass48, 2304 cells | tiled glass96, 9216 cells | n96/n48 |
| --- | ---: | ---: | ---: |
| L1(rho) | 3.88588e-2 | 2.83690e-2 | 0.730 |
| L1(vx) | 1.10329e-1 | 7.00237e-2 | 0.635 |
| L1(p) | 5.47217e-2 | 3.63345e-2 | 0.664 |
| volume-weighted RMS(vy) | 1.42445e-2 | 8.15891e-3 | 0.573 |
| 99th percentile abs(vy) | 6.22297e-2 | 3.56823e-2 | 0.573 |
| max abs(vy) | 1.29075e-1 | 8.77901e-2 | 0.680 |
| rho range | 0.13925--0.99243 | 0.12597--0.99940 | -- |
| pressure range | 0.12025--0.98743 | 0.10130--0.99901 | -- |

All three one-dimensional solution errors improve, and the transverse noise
falls by about 43 per cent in both its RMS and 99th-percentile measures.  The
global density and pressure ranges also approach the physical extrema without
overshooting them.

The defect is nevertheless still visible.  Individual cells retain localized
density/velocity spikes near the contact and rarefaction-tail regions, and the
transverse-velocity cloud has a maximum magnitude 0.0878.  The solution is much
cleaner than glass48 but is not one-dimensional to truncation noise.  The
appropriate verdict is therefore:

> The default moving-N construction is robust and shows substantial
> resolution improvement, but the moving-mesh-generated transverse/contact
> noise has not disappeared and remains a real accuracy problem.

This supports the selected contour + co-moving + Arpaia default as a stable
research baseline.  It does not explain the common ALE noise, and it does not
remove the need for the planned mesh-velocity-fraction and contact-preservation
diagnostics.  A future formal convergence study should use independently
relaxed glass96/glass192 point sets rather than periodic tilings.

## 5. Reproduction and artifacts

- Preparation: `examples/shocktube_2d/prepare_sod_n_highres.py`
- Analysis and figures: `examples/shocktube_2d/plot_sod_n_highres.py`
- Campaign archive:
  `/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_N_Default_HighRes_20260818`
- Managed binary:
  `build_artifacts/sod-n-default-highres/f59c95837eda-454f6e3d93ee0d42/Arepo`
- Machine-readable result: `analysis.json`
- Profile figure: `figures/sod-n-default-glass48-glass96-profiles.{png,pdf}`
- Evolution figure: `figures/sod-n-default-glass48-glass96-evolution.{png,pdf}`
