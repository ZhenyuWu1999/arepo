# Moving-N Sod 2x2x2 factorial, 2026-08-18

- **Author:** Codex (GPT-5)
- **Question:** Is the excess transverse noise of moving-mesh N caused by the
  element frame, the element-total residual, or the time-dependent dual mass?
- **Campaign:**
  `/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_N_Factorial_20260818`
- **IC:** the same relaxed periodic SWIFT glass48 and 2304 ParticleIDs used by
  the earlier matched Sod controls.
- **Common method:** moving N scheme, total-residual RK2, equal timesteps,
  ALE-RD CFL, face-angle mesh regularisation, one MPI rank, outputs every 0.01
  through `t=0.2`.

## 1. Factor matrix

The campaign runs every combination of:

1. `Roe + split` versus the conservative-state `contour` element total;
2. laboratory versus element co-moving algebraic coordinates;
3. the Arpaia versus Campoli moving nodal mass.

The generated Configs differ only by
`RD_ALE_SPLIT_MESH_VELOCITY`/`RD_ALE_CONTOUR_RESIDUAL`,
`RD_ELEMENT_COMOVING_FRAME`, and `RD_ALE_CAMPOLI_MASS`. Runtime parameters,
IC, mesh regularisation, and output times are matched. All eight cases reached
`t=0.2` after 122 sync steps and wrote 21 snapshots.

## 2. A real frame-coordinate bug found by the matrix

The first `Roe + split + co-moving + Arpaia` run passed its stationary opening
step and failed conservation assertion A2 at `t=0.00625`, before any flip:

```text
triangle=22 defect=4.78350849978295e-05
tolerance=1.6877550206794655e-13
```

The co-moving element total contained the transformed split correction

\[
C'_T=G(b_T)C_T,
\]

but the N nodal residuals, which were still in primed coordinates, received
the laboratory correction `C_T/3`. This is invisible while `sigma=0`; it
appears as soon as the grid begins moving. The fix stores the correction in
primed variables and distributes `C'_T/3`, then maps the complete nodal
residual back with `G^{-1}`. The failed output is preserved as
`output_failed_before_framefix1`. Both corrected co-moving Roe cases then ran
to `t=0.2` with A2 active.

This was an implementation error in a previously untested combination, not a
physical instability. It is also a useful regression: a non-uniform moving
state is required because uniform-state gates make `U-Uhat`, and hence the
split correction, vanish.

## 3. Endpoint results

All norms are volume weighted except the column explicitly labelled raw.

| total | frame | mass | L1(rho) | L1(vx) | L1(p) | RMS(vy) | raw RMS(vy) | flips |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Roe+split | lab | Arpaia | 3.89549e-2 | 1.10352e-1 | 5.49663e-2 | 1.40984e-2 | 1.52350e-2 | 324 |
| Roe+split | lab | Campoli | 3.89549e-2 | 1.10352e-1 | 5.49664e-2 | 1.40984e-2 | 1.52351e-2 | 324 |
| Roe+split | co-moving | Arpaia | 3.89549e-2 | 1.10352e-1 | 5.49663e-2 | 1.40984e-2 | 1.52350e-2 | 324 |
| Roe+split | co-moving | Campoli | 3.89549e-2 | 1.10352e-1 | 5.49664e-2 | 1.40984e-2 | 1.52351e-2 | 324 |
| contour | lab | Arpaia | 3.88588e-2 | 1.10329e-1 | 5.47217e-2 | 1.42445e-2 | 1.53230e-2 | 332 |
| contour | lab | Campoli | 3.88588e-2 | 1.10329e-1 | 5.47217e-2 | 1.42445e-2 | 1.53230e-2 | 332 |
| contour | co-moving | Arpaia | 3.88588e-2 | 1.10329e-1 | 5.47217e-2 | 1.42445e-2 | 1.53230e-2 | 332 |
| contour | co-moving | Campoli | 3.88588e-2 | 1.10329e-1 | 5.47217e-2 | 1.42445e-2 | 1.53230e-2 | 332 |

## 4. Factor isolation

### 4.1 Frame

After the correction fix, laboratory and co-moving solutions agree at
round-off for every residual/mass pair. At `t=0.2`, the ParticleID-aligned RMS
frame contrast in `(rho,vx,vy,p)` is about

```text
(1.2e-15, 8e-16, 4e-16, 3e-16).
```

The same result holds before flips. Therefore the element frame is an
algebraic coordinate choice, as derived, and is not the source of moving-N
noise. The co-moving form remains preferable for boost conditioning.

### 4.2 Mass

Arpaia and Campoli are nearly indistinguishable. At `t=0.2`, their
ParticleID-aligned RMS contrast is only approximately

```text
(1.5e-7, 4.6e-7, 3.3e-7, 6e-8),
```

with identical sync-step and flip histories within each residual form. This
is consistent with their formally second-order-small area difference. The Sod
noise does not select between them; the mature Arpaia form remains the default.

### 4.3 Element total

Contour and Roe+split differ measurably before the first flip: at the snapshot
nearest `t=0.02`, their ParticleID-aligned RMS difference is

```text
(rho,vx,vy,p) = (5.67e-4, 5.02e-3, 1.05e-3, 1.08e-3).
```

At `t=0.2`, contour has about 0.25% lower density L1 and 0.45% lower pressure
L1, while its volume-weighted transverse RMS is about 1.04% higher. It also
has 332 versus 324 cumulative edge replacements, with first flips at 0.025
versus 0.0234375. These are real scheme differences, but much smaller than the
common moving/static noise gap.

## 5. Conclusion for the moving-N defect

The prior controls gave

```text
static N-RK2       volume RMS(vy) = 8.487e-3
zero-mesh ALE N    volume RMS(vy) = 8.574e-3
moving Roe+split N volume RMS(vy) = 1.410e-2
moving contour N   volume RMS(vy) = 1.424e-2
```

Thus neither the frame, the mass form, nor the contour reconciliation is the
primary cause. Roe+split reduces the transverse floor slightly but does not
restore the static/zero-mesh result. The remaining common mechanism is actual
mesh motion coupled to the N characteristic distribution and evolving
geometry, including the reduction of contact/shear dissipation as
`u_n-sigma_n` approaches zero.

The factorial therefore supports the provisional defaults independently:

- **element frame:** co-moving;
- **ALE mass:** Arpaia;
- **element total:** Sod N does not decide it. Contour is slightly more accurate
  in density/pressure, Roe+split slightly quieter in `vy`; the larger KH entropy
  and contour-quadrature audits remain the discriminators.

The next clean test is a full-code mesh-speed-fraction sweep on the same glass,
with the same early snapshots, rather than another offline damping surrogate.

## 6. Reproduction

- Campaign preparation:
  `examples/shocktube_2d/prepare_sod_n_factorial.py`
- Analysis and plots:
  `examples/shocktube_2d/plot_sod_n_factorial.py`
- Machine-readable metrics:
  `Sod_N_Factorial_20260818/analysis.json`
- Figures:
  `figures/sod-n-factorial-profiles.{png,pdf}` and
  `figures/sod-n-factorial-time-series.{png,pdf}`.
