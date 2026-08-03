# Fixed-buffer Rayleigh--Taylor experiment

Date: 2026-08-03  
Authors: Zhenyu Wu and Codex (GPT-5)

## 1. Motivation and decision

The first direct RT port used reflective top and bottom boundaries. It failed
the RD dual-area coverage audit because reflected ghost triangles were counted
as physical elements. The subsequent fully periodic, two-interface pilot was a
useful source-coupling stress test, but it was not the classical single-interface
RT morphology shown in the GIZMO tests.

The replacement follows the fixed-particle idea used by the GIZMO/Abel RT test
and the injection region in development AREPO's
`WINDTUNNEL_FIXVARIABLESININJECTIONREGION`. Geometry remains periodic, but a
thick layer at each y seam is prescribed boundary data. This avoids reflective
ghost elements and does not require periodically replicating the physical RT
problem several times.

## 2. Problem definition

The pilot uses a static `0.5 x 1.5` glass with 6912 vertices (`n=96` per unit
length), periodic topology, `gamma=1.4`, and constant `g_y=-0.5`. The unstable
interface is at `y_0=0.75`. With `Delta=0.025`,

```text
rho(y) = 1 + 1 / (1 + exp(-(y-y_0)/Delta)),
dP/dy = rho g_y,
P(y_0) = 10/7.
```

The GIZMO-localized seed is shifted to the new interface:

```text
v_y = 0.025 [1 + cos(8 pi (x+1/4))]
             [1 + cos(5 pi (y-y_0))],     abs(y-y_0) < 0.2,
```

and zero outside its vertical support. Its actual maximum is approximately
`0.1`. The initial pressure remains positive over the taller domain.

Vertices in

```text
B = { y < 0.15 } union { y >= 1.35 }
```

are fixed. The buffer is about fourteen point spacings thick, so every triangle
that crosses the periodic y seam contains only fixed vertices. Dynamic vertices
cannot see the discontinuous top-to-bottom periodic image directly.

## 3. RD boundary construction

For every triangle, the element residual is still evaluated from all three
vertex states. If vertex `i` lies in `B`, however, every hydrodynamic stage
increment assigned to that vertex is rejected,

```text
Q_i^(s+1) = Q_i^(s),     i in B,
```

and its external-gravity kick is zero. Thus the boundary states used by the N,
LDA+F1, and B predictor/corrector stages are the same prescribed states. This is
stronger and cleaner for the concentrated RD RK2 implementation than resetting
primitive variables only after a complete step: a post-step reset would let a
contaminated boundary predictor enter the second residual evaluation.

Triangles that straddle `y=0.15` or `1.35` distribute their dynamic part to the
interior vertices and their boundary part to the reservoir. This is a practical
Dirichlet/reservoir boundary, not a new characteristic boundary derivation.

The implementation is opt-in through `RD_RT_FIXED_BOUNDARY` and is confined to
the RT configurations. It remains a static-mesh experiment.

## 4. Conservation meaning and RK diagnostic correction

The fixed layer makes the simulated domain open. Whole-box mass, momentum, and
energy are therefore not expected to remain constant. Element residuals remain
conservative before boundary rejection, but the rejected contribution is an
exchange with an external reservoir.

The first logger summed every suppressed RK stage increment. That quantity is
useful for measuring boundary activity, but it is not the committed reservoir
budget: the N/B two-stage and LDA four-pass accumulators contain temporary
predictor states and resets. Commit `94843f9` therefore distinguishes

```text
exchange = Q_before - Q_after
stage_suppressed = signed sum of all rejected trial-stage increments
stage_abs = absolute sum of all rejected trial-stage increments.
```

`exchange` closes the stored hydrodynamic conserved variables scheme
independently. In the corrected N `t=0.02` gate (job `10359791`), the cumulative
mass exchange was `+6.44009360e-5`, the snapshot mass change was
`-6.44009349e-5`, and the closure error was `1.05e-12`.

## 5. Hydrostatic gates

Single-rank, zero-seed runs to `t=0.2` completed for N (`10359782`), B
(`10359786`), and LDA+rate-Heun (`10359787`). All fixed vertices retained zero
velocity exactly; their density and internal-energy changes were at most
roundoff. Predictor states remained positive.

At `t=0.2`, the unseeded background was:

| scheme | max abs(vy) | non-mode RMS vy | density L1 drift |
| --- | ---: | ---: | ---: |
| N | `2.012e-3` | `3.108e-4` | `8.948e-4` |
| B | `2.781e-3` | `5.583e-4` | `6.843e-4` |
| LDA+F1 | `3.276e-3` | `7.667e-4` | `7.530e-4` |

The noise is well below the seeded peak velocity `0.1`; the familiar ordering
N < B < LDA is already visible.

## 6. Seeded N morphology and boundary reach

The N production run `10359783` used a single MPI rank and exactly 8192 equal
steps of `dt=5/8192=0.0006103515625` to `t=5`. It completed with exit code zero,
`f1_lumped=0`, minimum predictor `(rho,p)=(0.84548,0.687267)`, and maximum
element conservation defect `1.324e-16` absolute (`1.464e-14` relative). Every
fixed vertex remained unchanged (velocity and internal energy exactly; density
to `4.44e-16`).

The density field now has the expected classical topology. A central light
bubble rises, heavy spikes fall on its sides, and a mushroom cap develops. It
is symmetric and seed-dominated through the early nonlinear phase; this is not
the two-interface periodic pattern of the rejected pilot.

The `1.5`-high box is adequate through approximately `t=4`, but not for an
unqualified `t=5` endpoint. The active layer next to the fixed boundary has
`max abs(vy)=0.0617` at `t=4`, `0.1014` at `t=4.5`, and `0.2165` at `t=5`.
Reservoir mass exchange reaches 6.53%, 8.40%, and 10.29% at those times. The
last two frames therefore include boundary interaction. For a clean `t=5`
morphology, increase the height to about `2.0` (with the interface recentered)
rather than tiling the RT problem periodically.

The matched zero-seed N control (`10359792`) confirms that the coherent primary
mushrooms are seed-driven. The adjacent particle-ID differences give
`Delta a_mode = 0.0422, 0.0686, 0.0762, 0.0196` at `t=2,3,4,5`. At `t=4`,
the seeded/control non-mode RMS velocities are `0.1084/0.01734`; the control
does develop many small glass/contact-seeded fingers, but not the large imposed
mode. At `t=5` the seeded/control reservoir mass exchanges are `10.29%/3.27%`.
The primary result is therefore credible, while late small-scale structure and
the final boundary-adjacent cap are not quantitative validation data.

The corrected control log also closes over the complete run: cumulative
reservoir mass exchange `+0.036731640572` versus snapshot mass change
`-0.036731640597`, a residual of `-2.54e-11`.

## 7. Scheme comparison

B+RK2 job `10359789` completed to `t=5` in 12223 nonzero steps, using both
binary timestep values `0.000610352` and `0.000305176`. It remained positive,
with minimum predictor
`(rho,p)=(0.77505,0.687267)` and maximum element conservation defect
`1.324e-16` absolute. B forms recognizable mushrooms but develops narrow cap
spikes and secondary fingers earlier than N. The distinction is qualitatively
consistent with lower B dissipation and the known contact/glass defect; without
a full B zero-seed control, those small scales are not validated physical
roll-up. Its boundary interaction has the same late-time limitation as N:
reservoir mass exchange is `6.20%` at `t=4` and `9.84%` at `t=5`.

LDA+F1 rate-Heun job `10359788` also completed with exit code zero. It used
12483 nonzero steps with the same two timestep values. The minimum predictor
state was `(rho,p)=(0.49955,0.687267)`, and the maximum element conservation
defect was `5.204e-18` absolute (`5.758e-16` relative). LDA retains the primary
mushrooms through roughly `t=2.5`, then develops substantially more small-scale
interpenetration than B or N. This is a stable run of the implementation, not
evidence that the late LDA pattern is a converged RT solution. Its reservoir
mass exchange is `6.61%` at `t=4` and `9.62%` at `t=5`; the adjacent active
layer reaches `max abs(vy)=0.218` at the endpoint.

Thus all three schemes run this fixed-buffer problem and preserve positivity,
but the scientifically defensible comparison is limited to the primary
morphology before boundary contact: N is smoothest, B is intermediate, and LDA
admits the most contact/glass-seeded secondary structure. A taller box and
matched full-time B/LDA zero-seed controls are required before comparing late
roll-up quantitatively.

## 8. Reproducibility

Solver commits:

- `3837390`: fixed boundary and N/LDA/B RT configurations.
- `94843f9`: committed-exchange logger correction (no solution change).

Analysis commits:

- `9337990`, `79b9062`: fixed-buffer IC and provenance.
- `1c9c2df`, `fefea93`, `5f46f89`, `99ea9e1`: fixed-domain plots,
  boundary-interaction metrics, partial-run status, and final figure naming.

The N production campaign and morphology figure are under
`Hydro_data_analysis/Data_arepo_RD/rt_2d/gizmo_fixed_buffer_n96_d0025_seed0025_v2`.
The B/LDA production campaign is
`gizmo_fixed_buffer_lda_b_n96_d0025_seed0025_v1`; the complete matched N
control is `gizmo_fixed_buffer_n96_d0025_control_t5_v1`. Short N/B/LDA gates are
under the corresponding `control_t02` campaign directories. Every run output
contains the immutable build manifest, binary checksum, parameter file, source
status, rank count, and exit status.

The problem parameters follow the GIZMO methods paper, section 4.4.2:
<https://www.tapir.caltech.edu/~phopkins/Site/GIZMO_files/gizmo.pdf>.
