# A limited explicit topology transfer, 2026-09-11

This is a same-time transfer experiment. It does not advance the Euler PDE,
implement RK2 local interval closure, or establish convergence order for the
moving hydrodynamic solver. The positive low endpoint is the previously
derived explicit Colombo--Re-inspired geometric operator. The high endpoint
is the **existing full-patch uniform-shift correction** from
`tests/rd/audit_p1_ledger_remap.py`; neither that correction nor this limiter is
claimed to be a result of Colombo & Re.

The new files owned by this investigation are:

- `tests/rd/colombo_re_limited.py`: scalar/Euler transfer API.
- `tests/rd/audit_cr_limited.py`: random, affine, contrast, counterstreaming,
  repeated-topology and floor-sensitivity checks.
- This report.

## Algebra and conditional proof

Let the same-time full nodal mass be `g`, the old/new changed-patch masses be
`a,b`, and `dm=b-a`, with `sum(dm)=0`. Untouched nodal contributions satisfy
`g-a>=0`; `gnew=g+dm>0`. Define `U=Q/g` componentwise and

\[
D=\sum_i\delta m_i U_i,\qquad M=\sum_i g_i^{\rm new},\qquad
Q_i^H=g_i^{\rm new}\left(U_i-D/M\right).
\]

This is the previous high endpoint. Its component totals equal those of `Q`.
For any spatially affine conserved-density field, both triangulations
integrate the same affine P1 field exactly, so `D=0` and the nodal state is
unchanged. Affine **primitive variables** do not in general imply affine
Euler conserved densities, and are not covered by this statement.

The low endpoint `Q^L` can be any of the following, with the same `gnew`:

1. `cr_spectral`: the explicit geometric LF operator with `max(abs(nu))`.
2. `cr_graph_minimal`: the pure-geometry monotone coefficient
   `max(0,-min(nu))`.
3. `full_patch`: the existing low endpoint
   `(g-a)*U + b*(sum(a*U)/sum(a))`, retained as a control.

For either CR option, all old/new geometric records are assembled before
substepping; the balanced nodal swept-area and geometric CFL requirements
from `explicit_operator.md` remain mandatory. A total cavity area balance
alone is insufficient. The limiter itself is independent of the number of
nodes, but the present geometry test generator covers convex 2-to-2 flips.

The output is one common convex blend over the **whole cavity and all
conserved components**:

\[
Q_i^\theta=(1-\theta)Q_i^L+\theta Q_i^H,\qquad 0\leq\theta\leq1.
\]

Each endpoint has the same total, so every common-theta blend conserves it.
Separate theta values at different nodes would generally break this
argument; separate component values would also invalidate the Euler convex
admissibility argument used here.

For Euler, accepted states satisfy

\[
\rho>\rho_*,\qquad
e(U)=E-\frac{|\boldsymbol m|^2}{2\rho}>e_*.
\]

`e(U)` is concave for positive density. Hence its strict superlevel set,
together with the density half-space, is convex. The positive low endpoint
lies inside it if input states are admissible and the requested floors are
below their respective minima. Along the low-to-high segment, accepted theta
values form an interval starting at zero. The implementation first accepts
an admissible high endpoint directly; otherwise it uses 60 bisections, a
relative `1e-12` retreat, and an explicit check on the actual returned
floating-point values. If rounding defeats this recomputation, the final
implementation returns the stored accepted bisection candidate and its
matching theta. It does not halve theta: a Yee48 replay showed that a one-ulp
DMP predicate discrepancy could otherwise add a macroscopic change to the
accepted transfer. `test_cr_limiter_roundoff.py` retains that native event.

The default floors are `1e-12*min(input rho)` and
`1e-12*min(input internal_energy_density)`. These are mathematical
admissibility margins, not a demonstrated robust choice for the physical
RK2 solver. They can leave the output close to vacuum or zero pressure.

For a positive scalar the same procedure uses scalar positivity. Optional
`dmp_relax=r` restricts that scalar, or **density only** in Euler, to

\[
[U_{\min}-r(U_{\max}-U_{\min}),
 U_{\max}+r(U_{\max}-U_{\min})],
\]

with a relative roundoff tolerance. These are affine bounds and preserve
convexity. They do not restrict Euler momentum, pressure or entropy, and
must not be described as a full Euler maximum principle.

If the high endpoint is accepted, it is returned directly and no CR low
diffusion is applied. If the input conserved field is affine and admissible,
the unchanged high state satisfies all requested bounds and `theta=1`.
This is affine preservation of the instantaneous topology operation, not a
global high-order convergence result.

## API

```python
qp, gp, diagnostics = limited_remap(
    q, g, geometry,
    low_endpoint='cr_graph_minimal',
    dmp_relax=None,
    floor_fraction=1e-12,
    cfl=0.9,
)
```

`q` accepts a scalar vector `(n,)`, scalar column `(n,1)`, or Euler states
`(n,4)`/`(n,5)` ordered as density, all momentum components, total energy.
`q` is extensive; division by the full mass `g` gives conservative density.
The Euler five-component API check does not constitute a three-dimensional
mesh test. Arrays follow `geometry['node_ids']`. `old_mass`, `new_mass` and
`mass_delta` must be present. The function returns new arrays and does not
modify frozen predictor states or physical-time ledgers.

Diagnostics include `theta`, `high_positive`, `high_accepted`, `low_steps`,
the actual positivity floors, final minimum density/internal energy, and
relative component conservation error. `max_density_dmp_violation` reports
the chosen density range violation even when a DMP is not enforced; a
positive value with `dmp_relax=None` is therefore not a failed assertion.

## Reproducible audit and results

```sh
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python \
  tests/rd/audit_cr_limited.py --samples 512 --repeats 64 --seed 20260911 \
  > /Users/zhenyuwu/arepo_rd/local_runs/colombo_re_hydro_20260911/limited.json
```

The completed audit uses 512 jittered strictly convex quadrilaterals, random
collapse points, zero or unequal exterior nodal masses, densities and
pressures in `[1e-4,1e4]`, and velocity components in `[-20,20]`. Every
geometry/state is tested with three low endpoints and three density-bound
choices (`None`, `0.02`, `0`): **4608 random Euler transfers**, all with
positive output density and internal energy.

- Maximum relative component conservation error: `8.49e-16`.
- Maximum affine scalar error across random geometry: `4.44e-16`.
- Maximum relative uniform-state error: `5.42e-16`.
- The unlimited high endpoint is inadmissible in `418/512` samples.
- Positivity alone limits those 418 samples; relaxed density bounds with
  `r=.02` limit 504; hard bounds limit all 512. These counts are identical
  across low-endpoint choices because the high endpoint is identical.
- Named affine scalar and affine conservative Euler states retain
  `theta=1` for all low and bound choices.
- Forty-eight repeated-topology configurations each use 128 flips, with
  positivity and total conservation checked throughout. They include
  affine/nonaffine scalars, density contrast and counterstreaming Euler
  states. They advance **no hydrodynamic time**.

There is no evidence here that selecting the CR low endpoint improves the
limited result over the existing full-patch low endpoint. The low-to-high
segment changes, so different low endpoints can produce different limited
outputs. Theta values cannot be directly compared as a dissipation measure:
their zero endpoints are different. Symmetric contrast/counterstreaming
examples produce nearly identical final limited states with substantially
different theta values.

## A useful result, and a real tradeoff

For the nonaffine scalar `[1,4,2,.3]` on the unit cavity with full old masses
`g=(1,1,1,1)`, 64 flip/reverse pairs give:

| Method, graph-minimal low endpoint | Final / initial scalar variance |
|---|---:|
| Pure CR low | `3.81e-32` |
| Limited, positivity only | `1.0` |
| Limited, density relaxation `.02` | `1.0` |
| Limited, hard density bounds | `0.001255` |

The accepted high correction is exactly invertible for a flip followed by
its reverse on the same fixed cavity, in exact arithmetic. Indeed, it is a
spatially uniform state shift and `sum(dm)=0`, so the reverse shift cancels
the first. This explains the topology-only test; it is not a physical
accuracy result and does not apply to arbitrary interacting limited
cavities.

Hard density bounds reject every nonzero high density shift: a negative
shift lowers the old minimum, and a positive shift raises the old maximum.
They can therefore restore severe topology diffusion even when the high
state is physically admissible. A small relaxed DMP is a compromise, not a
general solution.

Conversely, positivity-only limiting permits near-boundary states. For
`rho=[.01,1,.01,1]`, zero velocity and pressure one, the graph-minimal limited
output has minimum density `1.19e-13`. A `.02` density relaxation changes
nothing because its allowed extension `.0198` exceeds the original minimum
density. Hard density bounds maintain minimum density `.01`, with stronger
limiting.

For counterstreaming states `rho=1`, `p=1`, `vx=[4,-4,4,-4]`, the default
floor produces a minimum internal energy density about `8.84e-12`.
Increasing `floor_fraction` to `.01` or `.1` instead gives minima `.025` or
`.25`. Density bounds do not help this equal-density example. No optimal
floor or relaxation has been identified; the physical hydro campaign must
measure accuracy and failures, rather than treating positivity alone as a
robustness guarantee.

## Consequences for the AREPO experiment

1. The large diffusion observed with the pure explicit CR low operator can
   be avoided on accepted high states while retaining a conditional
   same-time positivity fallback.
2. This construction still uses the earlier basis/volume correction as its
   high endpoint. It does not replace that engineering mechanism with a
   wholly native Colombo--Re explicit discretization.
3. Keep the existing full-patch low endpoint as a comparison. The present
   evidence does not justify claiming a superior limited scheme solely
   because the low endpoint comes from CR swept geometry.
4. The incoming state must be admissible and expressed at the event time.
   Applying this map to a partially completed hierarchical ledger does not
   prove either the unfinished transport or the next RK2 stage admissible.
5. Equal-step physical hydro tests can now assess limiter incidence,
   near-vacuum states, errors and sensitivity to floors. Hierarchical
   physical-time closure remains a separate implementation obligation.

## Independent replay of actual AREPO events

`tests/rd/audit_cr_arepo_events.py` reconstructs the geometry and state
transfer from complete `RD-CR-EVENT` JSON lines in actual AREPO run logs. It
does not use a dumped C matrix. Its public `general_geometry_records`
constructor normalizes triangle orientation, checks manifold incidence and
exact equality of old/new oriented boundary chains, and integrates each
moving half-edge with independent two-by-two Gauss quadrature. It uses the
common mean of the supplied physical coordinates as the collapse point,
then checks element GCL, per-node swept-area balance, and the assembled
operator row/column identities.

Unlike the original convex quadrilateral constructor, this replay
constructor can handle an arbitrary balanced triangle component on a fixed
node set. Manufactured polygon-fan checks use 4, 5, 7 and 12 nodes; an
incomplete boundary is explicitly rejected. This does not detect arbitrary
triangle overlaps or validate the upstream periodic embedding.

Modes are replayed using the previously tested Python APIs: mode 1 uses
pure CR graph-minimal low; mode 2 uses positivity-limited high; mode 3 uses
hard density DMP. Input `g,u` give `Q=g*u`, and geometry independently gives
the final mass. Conservation is checked for both dumped C output and
Python output. Only the first eight dumped events per run are available;
the remainder of each physical simulation is not replayed.

```sh
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python \
  tests/rd/audit_cr_arepo_events.py \
  /Users/zhenyuwu/arepo_rd/local_runs/colombo_re_hydro_20260911 \
  > /Users/zhenyuwu/arepo_rd/local_runs/colombo_re_hydro_20260911/arepo_event_replay.json
```

The script discovers new `run.log` files recursively, skips incomplete JSON
lines, and excludes archived `smoke_prechecks`. It can therefore be rerun
after subsequent resolution tests without editing the source. At this
section's initial completion it replayed **48 events** from the three CR
modes of `yee_n24` and `sod_n32`; all dumped cavities had four nodes.

- Maximum state-norm-relative C/Python difference: `1.80e-13`.
- Maximum absolute component difference: `4.44e-13`.
- Maximum relative C-output component conservation error: `3.02e-16`.
- Maximum relative Python-output component conservation error: `3.68e-16`.
- Maximum nodal/element GCL error relative to total record area:
  `3.99e-17` / `7.72e-17`.

The asserted state error is
`max(abs(U_python-U_C))/max(max(abs(U_input)),max(abs(U_C))) <= 1e-10`.
The output also retains the stricter componentwise-relative diagnostic,
whose maximum is `5.63e-8` in an almost-zero transverse momentum component;
this is not concealed by the state-norm check. In that near-constant-density
hard-DMP event, theta differs by `2.05e-7`, while the absolute state
difference remains tiny. A DMP boundary divides density-roundoff differences
by a small density variation, so its theta is ill-conditioned near a
constant state. The independent Gauss geometry and the closed C formula
also accumulate last-bit differences differently. The state comparison,
conservation and GCL checks pass, but bit-identical theta is neither
observed nor claimed.

This replay validates the recorded same-time topology operation inside
actual hydro runs. It does not independently validate physical residuals,
RK2, timestep selection, undumped topology events, or hierarchical coupling.

Final campaign update: 104 dumps now pass after the Yee48, half-dt Sod and
Campoli controls. Maximum state-norm-relative/absolute errors remain
1.80e-13/4.44e-13; C and Python conservation are each at most 4.22e-16.
The componentwise-relative maximum is 1.63e-7 and theta difference 5.94e-7.
Yee48 exposed an additional Python reference bug: recomputing a slightly
retreated endpoint could fail its density predicate by roundoff and invoke
a fallback that halved theta. The reference now retains the actual last
accepted bisection candidate; the native C map was unchanged. The captured
event is stored in `cr_limiter_roundoff_event.json` and checked by
`test_cr_limiter_roundoff.py`. Random, repeated-transfer, scalar-hierarchy and
native-replay audits were rerun after the fix. See [phase2_hydro.md](phase2_hydro.md)
for the final results and the distinction between native six-node components
and the four-node components present in these sampled dumps.
