# Sensor-controlled mesh velocity on moving-N Sod, 2026-08-19

- **Author:** Codex (GPT-5)
- **Question:** Can a discontinuity sensor locally make the mesh less
  Lagrangian and reduce the moving-N transverse oscillation without applying a
  global characteristic-speed floor?
- **Campaign:**
  `/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_N_MeshSensor_20260819`
- **IC:** the same relaxed periodic glass48, 2304 cells, and ParticleIDs as the
  moving-N factorial.
- **Common solver:** N scheme, contour element total, element co-moving frame,
  Arpaia ALE mass, total-residual RK2, equal timesteps, face-angle mesh
  regularisation, and `t=0.2`.

## 1. Experimental mesh policy

Before the ordinary AREPO mesh-regularisation correction, the experiment uses

\[
\boldsymbol\sigma_i
=
\boldsymbol\sigma_i^{\rm QL}
+\alpha S_i(\overline{\boldsymbol u}_i-\boldsymbol u_i),
\qquad \alpha=0.5,
\]

where `ubar_i` is the Voronoi-face-area-weighted velocity of the neighbouring
cells. The difference `ubar_i-u_i` is unchanged by a uniform boost. The
modified `VelVertex` is the single velocity subsequently used by the generator
drift, midpoint geometry, contour residual, K matrices, Arpaia mass, and ALE
CFL calculation.

Two sensors were tested:

1. **shock-only:** compression multiplied by a pressure reconstruction defect;
2. **all-wave:** the shock sensor plus density, pressure, and velocity
   reconstruction defects. Defects below 0.02 are treated as smooth and 0.20
   gives full activation. This branch is intended to include contacts and
   rarefaction edges.

This is a new ALE mesh-motion experiment motivated by Paardekooper's shock
sensor. It is **not** the published Paardekooper B/Bx distribution.

The implementation is disabled unless
`RD_ALE_SENSOR_MESH_SMOOTHING=<alpha>` is defined. The all-wave branch also
requires `RD_ALE_SENSOR_ALL_WAVES`. Each call reports sensor support, mean
strength, mesh-velocity correction, and pre/post-correction fluid--mesh slip.

## 2. Completion and endpoint result

Both sensor runs completed to `t=0.2`, passed the ALE geometry/conservation
assertions, and wrote 21 finite snapshots.

| policy | L1(rho) | L1(vx) | L1(p) | volume RMS(vy) | raw RMS(vy) | max abs(vy) | flips |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 3.88588e-2 | 1.10329e-1 | 5.47217e-2 | 1.42445e-2 | 1.53230e-2 | 1.29075e-1 | 332 |
| shock, alpha=0.5 | 3.88656e-2 | 1.10328e-1 | 5.47190e-2 | 1.42697e-2 | 1.53545e-2 | 1.29319e-1 | 329 |
| all-wave, alpha=0.5 | 4.29629e-2 | 1.08717e-1 | 5.48327e-2 | 1.42763e-2 | 1.47760e-2 | 1.12383e-1 | 280 |

Relative to baseline:

- shock-only changes volume RMS(vy) by **+0.18%** and L1(rho) by **+0.02%**;
- all-wave changes volume RMS(vy) by **+0.22%**, mass-weighted RMS(vy) by
  **+3.4%**, and L1(rho) by **+10.6%**;
- all-wave lowers the single largest `abs(vy)` by **12.9%** and raw RMS(vy) by
  **3.6%**, but does not lower the spatially or mass-weighted noise floor;
- the all-wave value remains `1.68` times the matched static-N value
  `8.49e-3`, essentially the same ratio as the baseline.

The result is therefore not a hidden improvement obscured by one norm. It
clips a few extreme cells while redistributing the transverse error and
diffusing the longitudinal Sod profile.

## 3. Was the mesh velocity changed enough?

Yes for the all-wave case; no for the shock-only case.

At the final pre-regularisation velocity assignment:

| policy | active fraction | mean sensor | correction RMS | correction max |
| --- | ---: | ---: | ---: | ---: |
| shock-only | 0.379 | 3.67e-3 | 6.53e-5 | 7.48e-4 |
| all-wave | 0.548 | 1.08e-1 | 6.86e-3 | 7.37e-2 |

At `t approximately 0.02`, the all-wave correction is stronger still: RMS
`3.12e-2` and maximum `2.02e-1`. It also changes the topology history (280
instead of 332 flips), reduces the endpoint cell-volume contrast from 5.14 to
4.56, and changes one global timestep. Thus its null result cannot be blamed
on an inactive implementation. The shock-only sensor, by contrast, becomes
numerically tiny after the initial transient and reproduces the baseline.

The all-wave sensor supports more than half of the cells at late times. That
is already too broad to satisfy the intended "local discontinuity treatment"
criterion, even before considering its increased density error.

## 4. Interpretation

The user's prior doubt is supported: **reactive neighbour smoothing of the
mesh velocity does not restore moving-N Sod to the static-mesh noise level.**

There is a structural reason for caution. At an exact initial contact or shock
with uniform velocity, `ubar_i-u_i=0`; the sensor can be fully active but the
correction is exactly zero. It reacts only after a velocity difference has
developed. The first non-zero Sod snapshot already contains the transverse
noise, and the all-wave run is marginally noisier from that point onward.

This experiment does not rule out every solution-dependent mesh policy. In
particular, a prescribed sensor-normal drift could act at `t=0` even when the
fluid velocity is uniform. But that is a more invasive method: it chooses a
direction and speed not contained in the local fluid velocity, smears a
contact deliberately, and starts to resemble adding dissipation through the
ALE characteristic speeds. It should not be attempted before the cleaner
`sigma`-fraction/K-dissipation studies requested by the KH entropy evidence.

Decision: keep the implementation as an off-by-default research switch and
do **not** promote either sensor policy. No Gresho boost campaign is warranted
for this version because it already fails the primary Sod acceptance test and
the all-wave branch pays a clear accuracy cost.

## 5. Reproduction

- Preparation: `examples/shocktube_2d/prepare_sod_n_mesh_sensor.py`
- Analysis/plots: `examples/shocktube_2d/plot_sod_n_mesh_sensor.py`
- Machine-readable analysis: `Sod_N_MeshSensor_20260819/analysis.json`
- Figures:
  `figures/sod-n-mesh-sensor-profiles.{png,pdf}` and
  `figures/sod-n-mesh-sensor-evolution.{png,pdf}`
- Shock binary:
  `build_artifacts/sod-n-meshsensor-shock-a05/f59c95837eda-d8f760dabac4ce8e/Arepo`
- All-wave binary:
  `build_artifacts/sod-n-meshsensor-allwaves-a05/f59c95837eda-eca3f1b27fc0c624/Arepo`
