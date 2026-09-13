# Moving Euler hierarchy: actual-interval closure retry

Date: 2026-09-13. Branch `test/colombo-re-explicit-hierarchy`, source base
`d79e68f`. This is an independent Python algorithm experiment, not a newly
enabled AREPO moving-LDA hierarchy. No production C, default configuration,
thesis, log1 or log2 was changed.

## Decision

There is now a constructive candidate for **conservative P1 Euler transport
with real Delaunay changes and hierarchical element clocks**. The important
addition to log3 §20 is an actual-interval criterion for the two-stage
predictor, together with a conservative changing-area F1 interval update.
Merely combining full-star closure with the old timebin criterion fails.

This removes one mathematical obstruction; it does not complete the native
AREPO implementation, establish time/spatial convergence, or prove physical
transport positivity. The defensible Chapter 4 structure remains static
hierarchy/MPI results followed by the validated equal-step moving extension,
with the new moving-hierarchy candidate presented as ongoing work. It would
be inaccurate either to call moving hierarchy solved in AREPO or to conclude
that edge flips make it mathematically impossible.

## State and event contract

For every retained triangle store its persistent identity, periodic image
offsets, birth time and last completed integration time `s_T`. For each
vertex retain an extensive ledger `Q_i`, geometric ledger `g_i`, frozen
primitive/conservative trace `U_i`, and trace/mesh-velocity epochs. A natural
timebin is a scheduling interval, not the actual integration interval after
an event has shortened it.

At a fine-step endpoint `t`:

1. Drift with the stored vertex velocities and compare old/new periodic
   Delaunay connectivity. Group intersecting changed cavities.
2. Add the **entire old incident star of every changed-cavity vertex** to
   the naturally due triangles. Integrate each selected triangle once over
   its own `[s_T,t]`; do not integrate a newborn triangle before its birth.
3. Refresh naturally active vertices and cavity vertices only after all
   their incident intervals have been closed. Other vertices may receive
   ledger deposits while retaining their frozen traces.
4. Apply a same-time conservative P1 basis map to the cavity. Retained
   triangles keep their actual clocks; new triangles start at `t`; dying
   triangles have no outstanding interval.
5. Update mesh velocity on refreshed vertices only. Their old incident
   intervals have already closed, so no pending triangle crosses a trace
   or velocity change.

This does not wait for the largest timebin. Closing triangles in the outer
part of a star does not require refreshing all their other vertices, so the
closure does not recursively synchronize the whole mesh. Deep hierarchies
can still lose efficiency if events repeatedly force large closures.

The prototype finds events at discrete fine-step endpoints, not their exact
continuous circumcircle-crossing times. It checks positive signed area over
each entire quadratic old-triangle trajectory. An interval inversion is a
failure, not permission to extrapolate an invalid mesh. Production code
needs a geometric timestep/event policy for this case.

## Why the predictor must use actual intervals

For the set of triangles due at `t`, set a vertex predictor live only if

\[
 P_i=1 \iff \bigl[\forall T\ni i:\ T\text{ is due}\bigr]
 \land\bigl[\forall T,T'\ni i:\ s_T=s_{T'}\bigr].
\]

Then form

\[
 dU_i=-\frac{P_i}{m_i(t)}\sum_{T\ni i}h_T\phi_{iT}(U),
 \qquad h_T=t-s_T.
\]

Here `m_i(t)` is the full old-connectivity nodal area at the event endpoint.
All triangles use the same vertex predictor. When two adjacent triangles
have different actual intervals, both shared-edge endpoints are frozen.
When an endpoint is live, both triangles share that actual interval.
Equal natural bins alone no longer imply this after an early closure.

In the same smooth Euler, prescribed-motion, depth-8 control:

| Rule | Outcome |
|---|---|
| Close dying triangles only | Geometric coverage incomplete at refreshed vertex |
| Full star, old bin-live criterion | Common-endpoint conservation error `7.65239e-7` |
| Full star, make every fully closed vertex live | Conservation error `2.46771e-6` |
| Full star, equal **actual** interval criterion | Maximum error `3.02e-15` through t=.1 |

These failures are retained in `campaign_v2`, not silently replaced by
passing reruns. They identify a necessary compatibility condition for this
particular shared-trace two-stage construction, not a no-go theorem for
other multirate schemes.

## Conservative moving F1 interval algebra

Let a triangle move linearly over `[s_T,t]`. Write `A_0,A_1` for its endpoint
areas, `A_m` for its midpoint-geometry area, `Delta A=A_1-A_0`, and
`M=(A_0+A_1)/2`. In general `M` and `A_m` differ; do not interchange them.
Let `phi_i^0` and `phi_i^1` be its midpoint-geometry Gauss3 LDA residuals
evaluated at `U` and `U+dU`. Let `beta_i^1` be the second-stage distribution
operator, with sum_i beta_i^1=I on its admissible residual range. Deposit

\[
\boxed{\begin{aligned}
 \Delta Q_{iT}={}&\frac{\Delta A}{3}U_i
 -\frac{h_T}{2}(\phi_i^0+\phi_i^1)
 +\frac{\Delta A}{6}dU_i\\
 &+\frac{M}{3}\left(dU_i-\beta_i^1\sum_{j\in T}dU_j\right),\\
 \Delta g_{iT}={}&\frac{\Delta A}{3}.
\end{aligned}}
\]

The last line of the Q update is zero-sum within each triangle. For a
rank-deficient temporal operator it is omitted, retaining a conservative
lumped temporal fallback. The coefficient of the local `dU_i` term in the
full-rank expression is `Delta A/6+M/3=A_1/3`, consistent with the endpoint
physical storage in the equal-step Campoli variant. This does not use the
Arpaia temporary-divisor rebase of extensive Q.

At fixed geometry and equal steps, the independent kernel reproduces the
existing native Gauss3 LDA/F1 solver after two steps to `2.665e-15` in all
four conservative densities. This checks signs, distribution and temporal
mass action in that limit; it is not a moving native equivalence check.

To see the conservation mechanism, define the triangle total

\[
 \Phi(U)=\oint_{\partial T_m}F(U_h)\cdot n\,ds
 -A_m\bar\sigma\cdot\nabla U_h.
\]

For affine mesh motion, `Delta A=h_T A_m div(sigma_h)`. Summing the boxed
update, using the product rule and `integral_T U_h=A_m sum_i U_i/3`, gives

\[
 \sum_i\Delta Q_{iT}=-\frac{h_T}{2}
 \oint_{\partial T_m}\left[
 F(U_h)+F(U_h+dU_h)-(2U_h+dU_h)\sigma_h
 \right]\cdot n\,ds.
\]

Use matching quadrature on both orientations of a shared edge. For equal
intervals these terms cancel. For unequal intervals the shared-edge traces
are frozen by the actual-interval criterion. With constant endpoint states
and constant vertex velocities, the flux-normal product is linear in time;
midpoint time integration is additive over a subdivision of that interval.
Closing every incident interval before changing a trace/velocity preserves
this partition argument. Consequently the whole-domain extensive sum closes
at common endpoints. The partial ledger sum at an intermediate asynchronous
tick need not equal the initial physical total; this is not used as a
spurious per-tick conservation assertion.

For uniform Euler states `dU=0`; the geometric deposition and ALE term give
`Delta Q_i=U Delta g_i`. The same-time topology map below also preserves
uniform states. This supplies the uniform-state/GCL argument, subject to
complete geometric coverage and non-inverted intervals.

These identities establish conservation compatibility of this construction.
They do **not** establish that it is an accurate second-order discretization
of the intended PDE. The frozen-F1 leading-operator issue in log3 §33 still
applies and may become more pronounced when event closures freeze stars.

## Same-time map: existing basis repair, not a new CR method

Let `a_i,b_i` be old/new changed-cavity P1 nodal masses, `g_i` the full
old nodal masses after closure, and `g_i^+=g_i+b_i-a_i`. The high endpoint is
the existing uniform-shift basis repair:

\[
 D=\sum_i(b_i-a_i)U_i,\quad
 Q_i^H=g_i^+\left(U_i-\frac{D}{\sum_jg_j^+}\right).
\]

The positive low endpoint only mixes the changed cavity:

\[
 \bar U_a=\frac{\sum_i a_i U_i}{\sum_i a_i},\qquad
 Q_i^L=(g_i-a_i)U_i+b_i\bar U_a.
\]

Both conserve the full cavity extensive sum and preserve uniform states.
The low endpoint has a convex-state interpretation when the full exterior
weights are nonnegative. A common theta for all vertices and Euler
components blends these endpoints if the high endpoint is inadmissible.
Code reuses `colombo_re_limited.limited_remap(low_endpoint='full_patch')`;
it does not invoke CR swept-area graph evolution or the published implicit
BDF method. All successful main/follow-up cases used theta=1, so their
result is the original high basis map, not extra low-order remap diffusion.

This same-time positivity statement is conditional on admissible input.
An early physical-time closure can already produce negative density/pressure
before remapping. The prototype checks that input, predictor states and
partial ledgers and fails if necessary. No LDA transport positivity or N
scheme positivity theorem follows from the successful tests.

## Numerical evidence and scope

Archive: `/Users/zhenyuwu/arepo_rd/local_runs/euler_flip_closure_20260913`.
All Euler tests use gamma1.4. `campaign_v2` has 15 positive controls and
three deliberately incorrect closure/predictor controls. It uses periodic
jittered Cartesian meshes, genuine SciPy Delaunay rebuilds, and fixed
natural periods. `followup_v2` adds seven populated periods 1/2/4/.../64
and glass coordinates from the retained native uniform glass48 IC.

| Successful control | Changed-cavity events | Maximum normalized conserved-sum error |
|---|---:|---:|
| Uniform, prescribed motion, depth8, t=.1 | 21 | 2.55e-15 |
| Uniform, prescribed motion, depth1024, t=.01 | 3 | 5.62e-14 |
| Smooth Euler, fluid motion, depth64, t=.1 | 9 | 3.49e-15 |
| Smooth KH, 16² jittered, fluid motion, depth8, t=.2 | 110 | 1.67e-15 |
| Smooth Euler, seven bin bands, fluid motion, t=.04 | 16 | 1.43e-15 |
| Uniform, seven bin bands, prescribed motion, t=.04 | 28 | 8.22e-15 |
| Glass48 Sod, fluid motion, depth8, t=.04 | 66 | 5.13e-15 |
| Glass48 smooth KH, fluid motion, depth8, t=.04 | 4 | 3.85e-15 |
| Glass48 Sod, fluid motion, equal step, t=.08 | 413 | 5.92e-15 |
| Glass48 Sod, fluid motion, depth8, t=.08 | 384 | 5.53e-15 |
| Glass48 smooth KH, fluid motion, depth8, t=.5 | 2092 | 4.44e-15 |

An event is a connected component of changed old/new triangles; multiple
edge flips may merge into one component. For example the glass Sod row
changes272 triangle records across66 components. Do not rename every
component a single 2–2 flip. Depth1024 has uniform-state error2.38e-14.
Errors above normalize mass and both momentum components by initial mass,
and energy by initial energy, avoiding division by initially zero momentum.

The seven-bin smooth run performs37.3% of the element updates of a full-mesh
fine-step run; the early glass cases perform58.2%. Extra event-induced
element closures are151 and836 respectively. These are counts, not native
wall-clock speedups. Half the split-grid vertices already occupy the finest
bin; these numbers are not a realistic cosmological cost estimate.

Glass48 denotes2304 generators in the full periodic square. Its single
half-box Sod tube has effective x-resolution **24**, not48. The small
jittered tests and early KH controls are algorithm checks, not a new
Morton comparison, convergence campaign or long-time KH validation.

The final three `hydro` runs bring the main validated collection to **22
successful controls plus three deliberate negative controls**. The glass
KH t=.5 run changes8526 triangle records, with4161 early vertex refreshes
and15670 extra triangle closures. Its minimum observed ledger density and
pressure are1.00160 and2.48689. It uses58.7% of full fine-step element work;
this endpoint is still far short of the prior KH t=10 target.

The final glass Sod profiles retain appreciable LDA undershoot. Equal versus
mixed has minimum central-tube vx=-.629/-.459, density L1=.03277/.03467,
and vx L1=.09886/.09094. No overall accuracy win follows. The compared
natural steps are .001 everywhere versus .000125/.001; they are **not**
equal-cost or equal-finest-step controls. Across the entire evolution,
minimum ledger pressure is .03020/.04863, and every checked RK/closure
state is admissible. Neither a positive run nor a smaller negative velocity
trough proves positivity or monotonicity of the scheme.

Figures (all-node Sod scatter is retained, with area-weighted mean curves):

- [Closure controls](../../../local_runs/euler_flip_closure_20260913/figures/closure_controls.png)
- [Glass Sod profiles, actual Nx24](../../../local_runs/euler_flip_closure_20260913/figures/glass_sod_profiles.png)

`tests/rd/analyze_euler_flip_closure.py` writes the combined25-case analysis
and PNG/PDF figures. The failure-control plot compares identical smooth
Euler initial data and depth8; its right panel records the shorter t=.01
endpoint of the depth1024 stress test explicitly.

## Numerical implementation and retained failed attempts

The initial laboratory-frame implementation explicitly formed beta matrices.
It hit roundoff conservation/range assertions in near-comoving Euler cases
(`campaign`, retained). The corrected implementation solves directly for
each residual RHS in the element-comoving frame and transforms vectors
back, as in the already validated native contour approach. The scaled
conservation tolerance was not relaxed. Rank detection uses singular values
and a1e-12 relative cutoff; a rank-deficient target uses a checked
pseudoinverse. This independent rank policy is not a claim of bitwise
equivalence with native rank handling.

The final kernel was rerun against the saved native two-step static result
and still agrees to2.665e-15. The one successful native run reused the
source255046f immutable binary from the static hierarchy campaign; no new
native build was made. An earlier incomplete HDF5 header was rejected before
evolution and is retained in `native_static`. The first follow-up launcher
omitted an imported Python dependency and failed before evolution; all four
setup failures remain in `followup`, with corrected standalone source
bundles in `followup_v2`.

## Remaining AREPO work and acceptance boundary

Current source remains guarded to moving N/total-residual two-stage,
full-mesh, one-rank operation. The tested Python route instead requires:

| Native boundary | Required change |
|---|---|
| `run.c`: old capture → mesh free → drift/domain exchange → rebuild | Persistent old triangles identified by generator IDs and periodic offsets; retain their geometry and clocks across mesh lifetime |
| `rd_ale_hierarchical_prepare` and residual dt weights | Actual per-triangle `[s_T,t]`, including early closures and births, replacing inference from current min bin |
| Predictor assembly | Due-star completeness and equal actual starts, with the same predicate on every rank |
| Primitive and mesh-velocity update loops | Explicit forced-refresh list in addition to normal active particles; settle all incident contributions before refresh |
| Geometric closure and topology repair | One conservative transaction; do not also apply the old keep-U mass-gap correction/rebase |
| Migration/restart/MPI | Ownership of retained/dead triangle histories, complete cavity/star exchange and exactly-once deposits; particle-ledger migration alone is insufficient |

This is more than inserting a corrected four-vertex remap. Conversely,
there is no need in this candidate to abandon P1 or implement native FV+RD.
The scheduling changes can be isolated behind a new experimental mode, but
the current N-only guard cannot responsibly be removed as a shortcut.

Still unvalidated: changing CFL-selected bins, native predictor/corrector
lifecycle, restart and domain migration, moving MPI, moving-mesh
regularization, geometric step rejection, strong shocks/near-vacuum,
long-time KH and spatial/time convergence of this new closure. The Python
mesh uses linear between-refresh trajectories and fluid velocity refreshed
on every forced vertex; it is not the existing AREPO mesh regularizer.

For Chapter4, make the established static hierarchy/MPI and equal-step
moving results the main evidence, retaining the accuracy qualification from
§33. A bounded ongoing-work subsection can now present the actual-interval
closure condition, conservation identities, negative controls and Euler
examples. Promotion to a completed moving-hierarchy result should wait for
a native one-rank implementation with equal-bin, uniform, flip, hydro and
convergence gates; MPI follows that verified lifecycle.

## Reproduction

`tests/rd/audit_euler_flip_closure.py` runs one case. The campaign runner
copies all required local Python modules before running the JSON cases:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python \
tests/rd/run_euler_flip_closure_campaign.py \
tests/rd/euler_flip_closure_cases.json \
/private/tmp/euler_flip_closure_replay
```

The destination must be fresh. The runner records source hashes, arguments,
per-case logs, failed assertions and successful NPZ states. The three named
negative controls are expected to fail their mathematical guards. No source
or tolerance should be changed to make those controls pass.
