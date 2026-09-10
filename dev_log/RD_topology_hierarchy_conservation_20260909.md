# Edge flips, hierarchical time intervals and MPI: conservation follow-up

Date: 2026-09-09, local Mac. Baseline: `75c3d6ac65b8edce2741a372fc9507dacf22151e`.
This follows the user's request to distinguish *additional* hierarchy/MPI
errors from the known topology error, and to consider a complete remedy.
It supplements `RD_moving_hierarchy_MPI_audit_20260908.md` and log 3 §10.
Tracked solver C and thesis files remain unchanged. Experiments use an
isolated copy of the preceding MPI prototype, with diagnostic overrides.

**Design follow-up:**
[`RD_moving_representation_design_20260909.md`](RD_moving_representation_design_20260909.md)
examines alternatives and actual AREPO reuse. In particular, the macro-epoch
construction below is a conditional mathematical reference, not a claim that
persistent old RD connectivity is automatically the lowest-cost engineering
route. Native FV updates with RD-derived multidimensional fluxes are a bounded
alternative worth testing; their full Euler/ALE implementation is not complete.

## 1. Findings and a necessary revision of the earlier conclusion

Simultaneous moving mesh, hierarchy and MPI remains feasible. However, the
earlier two-bin topology window was insufficient to test a crucial case:
**a flip that changes which triangles belong to a fine/coarse time interval.**
The current endpoint-connectivity scheduler then lacks the lifetime history
needed for a general conservation identity. This is an additional *coupling*
problem between topology and hierarchy, distinct from same-time mass remapping.
It is not a mathematical impossibility of local time stepping.

Three different issues must now be kept separate:

| Channel | Exists without a flip? | Exists with equal timesteps? | Evidence |
| --- | --- | --- | --- |
| Keeping nodal U while changing lumped basis masses | No | Yes | Log 2 §§68–73 and both local campaigns |
| Current Arpaia physical-to-divisor-to-physical rebase | Yes | Yes | Previous scalar and unchanged Euler tests |
| Missing/overlapping element time intervals when a flip changes the local clock | Requires a topology/clock event in this audit | Equal-clock control cancels | New exact frozen-scalar discriminator and targeted Euler tests |

MPI is a fourth, implementation-dependent source of possible error: duplicate
ownership, missing remote geometry, stale predictors, or repeated commits.
It does not add a mathematical nonconservation term if those contracts are
correct. The isolated port passes all 32 new 1/4-rank cases to round-off.
This is bounded evidence, not proof of every decomposition or restart case.

**Do not use `physical drift minus logged basis` as a pure physical error
attribution under arbitrary hierarchical flips.** The logged basis close is
itself contaminated by temporal geometry coverage in the new counterexample.
The previous result that this subtraction vanished remains correct for its
specific runs; generalizing it to all flips would be incorrect.

## 2. What the current code actually integrates

In `src/hydro/residual_distribution_solver.c`,
`rd_ale_hierarchical_prepare` starts from *current* triangles. For a due
triangle T it obtains the minimum current vertex bin, sets its full interval
length h_T, and reconstructs

\[
 x_i^- = x_i(t)-h_T\sigma_i,\qquad
 x_i^{1/2}=x_i(t)-\tfrac12h_T\sigma_i.
\]

The current source has no persistent birth/death time for a triangle. Positive
old/mid/new areas only establish valid geometry for that hypothetical
pullback; they do not establish that the triangle actually existed then.
Similarly, complete coverage of the periodic box by the endpoint mesh does
not establish complete coverage of the space-time interval.

For Campoli N, write the due-element increments as

\[
 G_{iT}=\frac{\Delta A_T}{3}U_i^n,\qquad
 L_{iT}=-\frac{h_T}{2}(\phi_{iT}^n+\phi_{iT}^{*})
         +\frac{\Delta A_T}{6}\delta U_i.
\tag{1}
\]

The synchronized-node close is

\[
 c_i=m_i^{\rm current}-g_i,\qquad B_i=c_iU_i^{\rm sync}.
\tag{2}
\]

These equations describe extensive ledgers; a partial inactive ledger must
not be interpreted as a complete instantaneous physical state.
Over a common synchronization interval, the exact accounting identity is

\[
 \Delta Q_{\rm total}=B_{\rm accumulated}+E_{\rm nonclosure},\qquad
 E_{\rm nonclosure}=\sum_{\text{due }(T,I)}\sum_{i\in T}(G_{iT}+L_{iT}).
\tag{3}
\]

For the contour residual, this has a useful boundary interpretation. With
P1 nodal U, affine mesh velocity and linear generator trajectories, the
nonconservative ALE triangle residual can be written

\[
 R_T(U)=C_T(U)+\frac{\Delta A_T}{3h_T}\sum_iU_i,
 \quad C_T(U)=\oint_{\partial T_{1/2}}
                   [I_1F(U)-\sigma_h U_h]\cdot n\,ds.
\]

Using \(\sum_i\phi_{iT}=R_T\), the volume terms in (1) cancel and
\(\sum_i(G_{iT}+L_{iT})=-h_T[C_T(U^n)+C_T(U^*)]/2\).
Thus (3) also tests cancellation of the time-integrated triangle boundaries.

On fixed connectivity with fixed compatible bins and linear trajectories,
the frozen-star interface states make the coarse midpoint contribution equal
to the composite fine contributions on the same edge. This gives cancellation
at the common synchronization time. It does not require total Q to be a
synchronized physical integral at every fine event.

When topology changes, the collection of intervals in (3) can omit part of a
dying coarse triangle and extend a newly born triangle backwards before its
birth. There is then no general pairing identity. A spatial conservation
assertion within each individual triangle cannot detect this failure.

## 3. A discriminator with zero mesh velocity

`tests/rd/audit_flip_time_coverage.py` removes all moving-geometry ambiguity:

- 16 nodes on a periodic 4×4 square grid, constant scalar advection velocity;
- a prescribed frozen nonuniform P1 scalar, whose residual is integrated
  exactly on every triangle;
- zero generator velocity and one legal diagonal swap in a cocircular square;
- H=0.08, h=0.01, topology changes at t=0.03; one corner has the fine step;
- old and new complete meshes each have spatial residual sum below `1.3e-17`.

The frozen field makes this a test of the time quadrature/ownership identity,
not a full scalar PDE simulation. In particular, no geometric or nodal mass
transfer is performed in this calculation; it isolates the residual integral.

| Integration rule | Absolute integrated global residual |
| --- | ---: |
| Fixed connectivity, mixed bins | `<1.6e-18` |
| Flip, equal fine bins | `<6.3e-19` |
| Flip, current-connectivity/full-bin interval rule | `1.23e-4` |
| Flip, actual lifetime partition on atomic slabs | `<6.3e-19` |

Choosing each of the four corners in turn changes the sign, but not the
magnitude, of the mixed-clock defect. This proves that the scheduling rule
lacks a general zero-sum identity independently of a spatial remap defect.
The atomic-slab calculation is a conservative *reference integral*, not a
claim that evaluating every triangle on every fine slab is efficient LTS.
Persistent interval registers can accumulate the same lifetime coverage
without interpreting nonexistent old elements as physical histories.

For example, an old coarse triangle disappears after 3h but before H. Its
first scheduled endpoint at H never arrives. Conversely, a new coarse
triangle born after 3h would first be charged a full H under the current
rule. A new fine triangle may replace just part of this history. Evaluating
the complete current mesh correctly at each individual time does not repair
these integrated lifetime weights.

## 4. Targeted Euler/MPI experiment

Campaign: `/Users/zhenyuwu/arepo_rd/local_runs/topology_hierarchy_audit_20260909`.

The 64-node periodic Euler IC and Campoli N/MPI prototype come from the
preceding audit. The velocity of each generator is overridden by a fixed
per-ID value, independent of the fluid update and rank count:

\[
 \sigma_x=.19\sin(2\pi y_{\rm ID})+.11\cos(2\pi x_{\rm ID}),\quad
 \sigma_y=.13\sin(2\pi x_{\rm ID})+.07\cos(2\pi y_{\rm ID}).
\]

Here the ID reference coordinates are the unjittered 8×8 grid; the actual
initial positions retain their jitter. This is a prescribed ALE test, not a
production mesh-motion prescription. All runs have the same continuous
generator trajectories to `1.11e-14`. Connectivity is sampled at the events
of each clock schedule; equal-step runs do not resolve every fine flip time.

H=0.004 and final time 0.128. We run smooth and uniform fluid states, each
with eight bin patterns, on one and four ranks: 32 cases in total.

Patterns: equal bins; a 2:1 spatial split; fixed-ID and spatial 8:4:2:1
stripes; and four cases in which only one vertex of the first flipping
quadrilateral receives H/8. The first detected change on the h=0.0005
geometry sampling is t=0.0115:

- removed zero-based triangles: `(34,35,42)`, `(35,42,43)`;
- added: `(34,35,43)`, `(34,42,43)`;
- selected fine ParticleIDs: 35, 36, 43, 44.

These are discrete detection times, not exact incircle-root times. The
geometry record has 16 sampling times with changed keys; this is not a
certified count of elementary flips. The spatial stripes do not change bin
membership in this window, so their agreement with fixed-ID stripes is not
a dynamic-bin transition test.

At common full synchronization times the measured E in (3) is:

| Smooth-flow bin pattern | max component of \(|E_{\rm nonclosure}|\), 1 rank |
| --- | ---: |
| Equal | `2.02e-15` |
| 2:1 split | `7.48e-15` |
| 8:4:2:1 stripes | `1.07e-14` |
| Only ParticleID 35 fine | `5.57062e-6` |
| Only ParticleID 36 fine | `1.18359e-5` |
| Only ParticleID 43 fine | `2.35124e-6` |
| Only ParticleID 44 fine | `5.70896e-6` |

The targeted single-fine-vertex cases develop their first nonzero balance
at the first synchronization after that flip. Before flips, every pattern
passes the same balance test to round-off. In the ID 36 case, at t=0.012,

\[
 E_{\rm nonclosure}=
 (-3.6778241,\;2.8370041,\;-3.3227896,\;-11.4461237)\,10^{-6}
\]

for mass, x momentum, y momentum and energy. The total physical mass change
at that time is `-9.72178338e-5`; the basis diagnostic is `-9.35400097e-5`.
The nonclosure balance is not the whole physical error.

The uniform controls are essential. Their final physical totals change by
at most `1.34e-15` and all inspected primitive-field errors are below
`2.40e-14`, yet targeted single-fine cases also have nonzero E. For ID 35,
at t=0.012 its mass component is about `-2.74296e-6`, canceled by the basis
close. With constant U, the latter compensates the incorrectly covered
geometric interval. Hence B is not a pure same-time basis change here.
Free-stream preservation alone misses the time-coverage problem.

Across all 16 comparisons, the largest 1-versus-4-rank particle-field
difference is `1.244e-14`; timebins are identical. For smooth states alone
the largest difference is `8.44e-15`. Density and pressure stay positive in
every case. The hierarchy/topology signal is reproduced on both rank counts;
there is no detected additional MPI signal at this scale.

No large KH run is needed to establish this missing identity. Long nonlinear
trajectories mix interpolation, limiting, instability growth and changing
flip histories; they would be a weaker first discriminator. They remain
necessary later for accuracy and robustness of an actual remedy.

## 5. The spatial flip problem does have an exact local remedy

This is a continuation of log 2 §68, not a replacement of its derivation.
At a *common physical time*, use the same coordinates for old/new triangles
and a consistent periodic embedding. Let m_i^- and m_i^+ be full nodal
lumped masses, and delta m_i their difference on a complete changed patch P.
Exterior triangle contributions cancel. Geometry gives

\[
 \sum_{i\in P}\delta m_i=0,\qquad
 \sum_{i\in P}\delta m_i x_i=0.
\tag{4}
\]

Keeping U causes the integral jump

\[
 D_P=\sum_{i\in P}\delta m_i U_i^-.
\tag{5}
\]

The first identity makes uniform states harmless, and the second makes
affine states harmless. A general non-affine field has D_P nonzero. An
exactly cocircular flip does not make individual median-dual masses
continuous: e.g. a square changes the incident triangle count of its diagonal
vertices. Detecting the exact geometric event time cannot by itself remove
(5). Nor does merely storing Q eliminate the issue: holding every Q_i fixed
across a changed m_i destroys a uniform U field.

Choose nonnegative weights summing to one and set

\[
 Q_i^{H,+}=m_i^+U_i^- - w_iD_P,
 \quad\text{or}\quad
 \Delta Q_i^H=\delta m_i U_i^- -w_iD_P.
\tag{6}
\]

Then the patch sum of delta Q is exactly zero. This preserves uniform and
affine nodal fields. It conserves mass, both momenta and total energy with
the same geometry weights. It is a representation transfer, not a global
post-step correction to an unexplained hydrodynamic error.

### 5.1 Full nodal-mass weights and reversibility

The full-new-mass weight family was already identified in log 2 §68.3.
It has a useful explicit property that deserves testing:

\[
 w_i=\frac{m_i^+}{M},\quad M=\sum_{i\in P}m_i^+=\sum_{i\in P}m_i^-,
 \qquad U_i^{H,+}=U_i^- -\frac{D_P}{M}.
\tag{7}
\]

For one conserved component, this is the linear map
\(T=I-\boldsymbol1\delta m^T/M\). Because
\(\delta m^T\boldsymbol1=0\), its inverse is
\(I+\boldsymbol1\delta m^T/M\). Thus an immediate flip and reverse flip,
at identical coordinates and with the same affected-node set/exterior
masses, is exactly reversible in exact arithmetic if no limiter acts.
This does not imply reversibility of motion, RK evolution, changed patch
grouping, or a positivity-limited transfer.

The weights also attain the componentwise minimax bound

\[
 \max_i|U_i^+-U_i^-|\ \ge\ \frac{|D_P|}{\sum_{i\in P}m_i^+}.
\tag{8}
\]

Indeed conservation requires \(\sum_i m_i^+(U_i^+-U_i^-)=-D_P\);
the triangle inequality proves (8), and (7) attains equality. This says
nothing about Euler admissibility or optimal error in the whole reconstructed
field. In particular, it does not imply the new scheme must reproduce the
old keep-U KH trajectory. Log 2 §73 and the August 26 update already show
that a finite correction can be unavoidable at an under-resolved interface.

### 5.2 A positive conservative fallback

Split m_i^± into unchanged exterior mass m_i,out and changed-patch mass
m_i,P^±. For admissible common-time old nodal states, define

\[
 \bar U_P=\frac{\sum_i m_{i,P}^- U_i^-}{\sum_i m_{i,P}^-},\qquad
 Q_i^{L,+}=m_{i,\rm out}U_i^-+m_{i,P}^+\bar U_P.
\tag{9}
\]

This conserves the patch integral. Its primitive conservative state is a
convex combination of admissible Euler states. Use one patch-common scalar
alpha for all affected vertices and all conserved components:

\[
 Q_i^+=Q_i^{L,+}+\alpha(Q_i^{H,+}-Q_i^{L,+}),\quad 0\le\alpha\le1.
\tag{10}
\]

Choosing the largest alpha satisfying positive density and internal energy
preserves both conservation and admissibility of the transfer. Independent
vertex/component limiting would generally destroy conservation. Affine
preservation holds when the admissible high state is accepted; the fallback
need not preserve every nonconstant affine field.

The new algebra test applied (7)–(10) to 1,000 randomized admissible Euler
patches with strong state contrasts: 774 required limiting, 226 did not.
Maximum patch conservation error and unlimited flip/reverse error were both
`7.11e-15`; affine preservation error was `4.44e-16`. The limited fraction
belongs to these deliberately extreme random samples, not a flow benchmark.
This verifies the isolated transfer, not the complete ALE timestep's positivity.

### 5.3 Other spatial transfers

The exact overlap projection in log 2 §68.7.4 remains a useful diagnostic.
With old/new P1 patch bases and unchanged exterior lumping, one may solve

\[
 [M_{\rm consistent,P}^{+}+\operatorname{diag}(m_{\rm out})]U^+
   =[C_{P}^{+,-}+\operatorname{diag}(m_{\rm out})]U^-,
\]

where C integrates products of new and old basis functions on their overlap.
Partition of unity gives conservation and affine exactness. The consistent
inverse need not preserve positivity; a lumped nonnegative-overlap version
can supply a low-order endpoint for convex limiting. This introduces exact
polygon intersections and small patch solves, and cannot evade bound (8).
It is not necessary merely to prove that a local conservative transfer exists.

## 6. Why a correct patch formula is not yet a complete hierarchical fix

At an arbitrary fine event, four flip vertices can have different state
times; their stored Q can contain different fractions of incident residuals.
Substituting these ledgers into (9) does not provide its admissible
common-time operands. Updating Q/g algebraically on those vertices also
does not reconstruct the missing lifetime of old triangles in §3.

There are therefore two independent obligations:

1. **Spatial representation:** a same-time old-to-new map such as (6)–(10).
2. **Temporal coverage:** every real element/edge interval is integrated once,
   with compatible traces and paired boundary contributions.

Correcting one cannot substitute for correcting the other. In particular,
subtracting the logged basis B or distributing the measured E globally would
mix errors whose cancellation currently protects uniform flow.

Two designs make both obligations concrete.

### 6.1 A conservative reference with macrostep topology epochs

Use Campoli endpoint storage. At a common macro time t_n, retain a persistent
RD triangulation with global vertex IDs and periodic image offsets. Freeze
its connectivity **for hydrodynamic integration over that macrostep**, while
the generators move. Also freeze each generator's mesh velocity over the
macrostep so the fixed-connectivity temporal cancellation assumptions apply.

Select dyadic H and its local substeps with both hydrodynamic restrictions and
positive signed triangle area throughout the interval. With linear
trajectories, area is quadratic: test endpoints and any interior quadratic
minimum, rather than only old/mid/new samples. The old triangulation may
temporarily cease to be Delaunay while remaining a valid oriented mesh.

Within the epoch, use the existing frozen-star hierarchy and the MPI geometry
reductions/ghost refresh, evaluated on the *persistent* RD elements. At t_n+H
all ledgers have closed to physical endpoint masses. Build the new Delaunay
connectivity there and perform conservative same-time transfers on the
complete changed patches. Start the next epoch from the resulting states.

This gives a composition of conservative fixed-connectivity macro evolution
and conservative topology transfer. It keeps real local substeps and permits
MPI; it does not require all fluid updates to use the finest step. It avoids
birth/death events inside open macro intervals by construction.

This is an implementable reference *design*, not an already completed Euler
implementation or a proof of second-order multirate accuracy. Engineering
requires a persistent RD element/halo layer separate from the scratch Delaunay
mesh, an inversion bound, and a topology transfer at synchronization. Simply
turning off a Delaunay flip flag would not implement it. Freezing velocities
and delaying the hydrodynamic connectivity update alter the original
mesh-motion/integration policy and must be measured for accuracy and cost.

### 6.2 Immediate flips with persistent space-time intervals

If instantaneous Delaunay connectivity is required at every fine event, a
more general implementation must retain interval history. A minimum contract is:

- Persistent element identity: canonical global IDs, periodic image offsets,
  topology epoch, birth/death times, last integrated endpoint and bin interval.
- A dying element is closed only over its actual remaining lifetime. A new
  element starts at its birth time, not at t minus its full current bin.
- Split intervals at topology events, incompatible bin changes and changes
  in the velocity history used for pullback. Preserve compatible stage traces
  on the resulting shared space-time boundaries.
- Use edge/interval registers or equivalent common space-time fluxes. A
  fine/coarse interface uses the same integrated flux with opposite signs;
  replacing a provisional coarse contribution must subtract it before adding
  the accepted composite value. Registers are part of the conservation total.
- Establish complete patch states at a specified time before applying (9).
  Closing a patch may require incident-star boundary fluxes. Waking just four
  vertices can miss these or propagate a synchronization cascade; its locality
  cannot be assumed without a written closure algorithm.
- Commit the transfer once and install a new epoch. No old contribution is
  replayed under the new connectivity. Store committed states and pending
  increments separately so their physical meanings are explicit.

For higher temporal order, coarse states need a compatible dense prediction
or a conservative multirate coupling with its own order conditions. The
present frozen-star construction measured first-order convergence across bin
interfaces in the earlier static tests. Extra RK stages alone do not fix that.

These conditions explain the extra design work; they are not a complete
derived second-order event-driven RD integrator. The epoch reference above
is the smaller conservative target to implement first.

## 7. MPI contract for either conservative design

The preceding prototype already supplies uniquely owned physical triangles,
remote geometry accumulation, vertex-star bin reduction, extensive residual
exports and predictor-to-corrector primitive exchange. Topology adds:

1. One canonical patch owner, using globally identified changed triangles.
   Gather a consistent periodic embedding, old/new masses and state versions.
   Do not enlarge a changed patch by indiscriminately traversing unchanged
   triangles; the earlier log 2 patch-support issue still applies.
2. Validate the same-time area/moment identities, compute D and one common
   alpha, then export extensive delta Q and geometric state changes to vertex
   primaries. All ghost copies receive the committed version before use.
3. Assign each interval/patch transaction a unique epoch and sequence key.
   Contributions are accepted once. Independent patches can run concurrently;
   overlapping patches need a deterministic order or a correctly merged event.
4. Migration/restart carries committed Q, g, timestamps, persistent geometry
   ownership and all pending registers. Migration occurs at a completed
   transaction boundary or uses an explicit transfer of unfinished ownership.

MPI reductions are not the mathematical obstacle. A missing interval on one
rank remains missing after an Allreduce. Conversely, a correct conservative
patch/interval operator can be distributed through extensive additive records.
The full-mesh correctness prototype is not a demonstrated scaling solution.

## 8. Connection to published topology-aware ALE methods

Colombo and Re (2022) explicitly interpret connectivity changes as fictitious
continuous deformations in an ALE residual-distribution method, using this
construction to enforce GCL and retain the underlying scheme's conservation.
That is a relevant route for a more integrated RD treatment; it does not
provide the present code's hierarchical MPI transaction algorithm ready-made.
[Paper and primary-source abstract](https://arxiv.org/abs/2204.11668).

Gaburro et al. (2019) construct closed space-time control volumes for changing
Voronoi meshes, including degenerate sliver elements that fill topology-induced
space-time holes. Conservation and GCL follow from that space-time formulation.
This directly motivates checking complete space-time coverage, but the paper's
FV/DG formulation cannot simply be substituted for RD median-dual masses.
[Paper and primary-source abstract](https://arxiv.org/abs/1905.00967).

Neither citation is used as a proof of the new scalar result or as evidence
that the local code already implements these algorithms. Equations (1)–(10)
are the present audit's algebra, building on the existing log 2 transfer.

## 9. Recommended implementation and thesis decision

For the immediate mathematical baseline, choose physical endpoint Q and the
Campoli contour N residual. Keep the current Arpaia rebase's independent
defect visible: if B_i is its pre-rebase physical ledger and L_i the residual
increment, its commit is B_i+(m_i^+/D_i)L_i, giving an additional
\((m_i^+/D_i-1)L_i\). Topology work does not remove this term. A divisor-only
predictor with direct endpoint commit is a different candidate update; only
the independent scalar version was validated in the preceding audit.

Implement conservative topology first at a genuinely synchronized epoch
boundary, where (4)–(10) have well-defined operands. Validate uniform/affine
fields, isolated and cascading flips, positive states, flip/reverse, and
1/2/4-rank equivalence. Then combine it with persistent fixed-connectivity
hierarchical epochs, retaining actual subcycling. This supplies a complete
conservation target against which immediate-flip interval work can be checked.

If Chapter 4 requires ordinary fine-event Delaunay updates, the persistent
interval/trace problem must be solved before describing the combined scheme
as conservative. A successful spatial remap or 1-versus-4-rank equality is
insufficient. If the chapter claims second-order time accuracy, a separate
multirate convergence result is also required. Once those contracts are met,
smooth moving-vortex convergence and KH/shock robustness tests become useful
acceptance gates; matching the nonconservative keep-U trajectory is not one.

## 10. Reproduction and limits

Versionable algebra discriminator:
`tests/rd/audit_flip_time_coverage.py`; run with Python and NumPy. Its output
is retained as `algebra_summary.json` in the campaign. It contains assertions
for the mixed-clock failure, corrected lifetime integral, exact patch
conservation, admissibility, affine preservation and unlimited reversibility.

The isolated Euler campaign retains `Config.sh`, `src/`, `build/Arepo`,
`build.log`, `instrument.py`, `diagnostic_increment.patch`, `campaign.py`,
`rank_log.py`, `verify_campaign.py`, both ICs, three snapshots per case,
rank-local logs, `summary_np1.json`, `summary_np4.json`, `geometry_events.json`
and `provenance.json`. `campaign.py --run --ranks 1` and `--ranks 4` launch
the cases; omitting `--run` only reanalyzes their logs. `verify_campaign.py`
checks the discriminating balances and rank/trajectory/constant-state gates.

The machine-readable field is named `nonclosure_balance`, explicitly not
`physical_conservation_error`. Independent MPI stdout streams initially
interleaved inside numeric vectors, and Open MPI output-file options failed
locally. Final four-rank measurements were regenerated using a small wrapper
that redirects each rank's own stdout/stderr before exec. Mixed stdout was
not used for the final numerical conclusions.

Scope: periodic 2-D N, prescribed linear generator trajectories, bounded
state contrasts, small rank counts, no gravity or sources. No production
mesh-velocity policy, dynamic-bin transition, positivity proof for the entire
step, scaling, restart of persistent topology, moving LDA/F1 or long-time
nonlinear accuracy claim has been established by these tests. Those are
separate gates, not reasons to discard the conservation counterexample.
