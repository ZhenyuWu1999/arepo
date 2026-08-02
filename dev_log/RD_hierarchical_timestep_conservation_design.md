# RD hierarchical timesteps on a fixed Delaunay mesh

## Conservation, vertex-ledger semantics, RK2 staging, and an AREPO code audit

- Date: 2026-08-02
- Author: Codex (GPT-5)
- Status: mathematical and engineering specification draft for discussion with
  Claude and Kimi.
- Scope: two-dimensional RD on a fixed Delaunay triangulation, initially the
  `N_SCHEME + RD_RK2_TOTAL_RESIDUAL` lumped-mass control. Moving mesh, ALE,
  refinement, F1, beta/gamma changes, and production MPI/domain-decomposition
  changes are not authorised by this document.
- Reference sketch:
  `/home/zwu/MyThesis/useful_resources/delaunay_abstract_labeled.png`. In the
  discussion below, blue `JKL` is a coarse triangle, yellow `KML` is a fine
  triangle, `KL` is their common edge, and the purple polygon illustrates the
  median-dual control volume of `L`.

## 1. Executive conclusion

The proposed hierarchy is feasible for fixed-mesh, pure-hydrodynamic,
lumped-mass N+RK2, and it aligns closely with AREPO's existing state machine:

1. a vertex owns one conserved median-dual ledger
   \(Q_i=|S_i|U_i\);
2. every due triangle distributes its residual increment to all three vertex
   ledgers, independent of vertex activity;
3. a vertex owns one synchronised primitive/nodal state and updates it only at
   its own power-of-two synchronisation point;
4. a vertex that participates in any triangle finer than its own timestep uses
   its synchronised state throughout its entire incident star during the open
   interval;
5. the two halves of N+RK2 should live at AREPO's existing two hydro call sites,
   with a persistent per-vertex predictor scratch between them;
6. the current RD element residual and N distribution remain element-wise; an
   edge decomposition is required for the conservation proof and its algebra
   test, not as the production state-storage model.

At the common parent-bin endpoint, global conservation follows if the current
Roe-parameter element residual is exactly the boundary integral it claims to
represent. Exact conservation at intermediate fine events is not required in
this first construction. Intermediate physical-ledger admissibility is,
however, an explicit acceptance gate.

The principal unresolved risk is not the macro conservation identity. It is
whether a coarse, frozen vertex can receive many fine distributed residuals
without its provisional ledger becoming non-physical, and whether the
first-order strip/island at timebin interfaces is acceptably accurate.

## 2. What the AREPO finite-volume code actually guarantees

The code audit confirms the user's intuitive model.

### 2.1 Power-of-two scheduling and active cells

`find_next_sync_point()` selects the earliest next occupied-bin event on the
integer timeline. `mark_active_timebins()` marks bin `b` synchronised when

\[
    \mathrm{Ti}_{\rm current}\bmod 2^b=0.
\]

`make_list_of_active_particles()` then constructs the hydro active list only
from those bins and drifts those particles to the current global event time.
Timestep increases are restricted to a time at which the proposed coarser bin
is synchronised.

Relevant code:

- `src/time_integration/predict.c`, `find_next_sync_point()` and
  `mark_active_timebins()`;
- `src/time_integration/predict.c`, `make_list_of_active_particles()`;
- `src/time_integration/timestep.c`,
  `timebins_get_bin_and_do_validity_checks()`.

### 2.2 Conserved-ledger/primitive-state separation

`compute_interface_fluxes()` treats a face whenever at least one adjacent cell
is active. The face timestep is the minimum of the two cell timesteps. The
resulting equal-and-opposite increments are applied to both conserved cell
states; the source comment explicitly says that a local point is updated
independent of whether it is active.

`update_primitive_variables()` subsequently loops only over
`TimeBinsHydro.ActiveParticleList`. Therefore an inactive FV cell may have a
new mass, momentum, and energy while its density, velocity, pressure, and
`TimeLastPrimUpdate` remain at its previous synchronisation point.

This is the exact storage discipline needed by hierarchical RD. The difference
is in the spatial conservation mechanism: an FV face event is independently
zero-sum, while one RD triangle residual is not.

### 2.3 Two hydro call sites

AREPO calls the hydro operator before `find_next_sync_point()` and again after
arrival at the new synchronisation point, immediately before primitive
recovery. The FV implementation multiplies each face contribution by `0.5`.
The two calls are therefore natural homes for the first and second RK stages.

The current total-residual RD path deliberately does not use the first call; it
runs both stages internally at the second call. That is appropriate for the
validated equal-timestep experiment but not for multiple simultaneously open
timebin intervals.

## 3. What the current RD code already provides

Several recent corrections are prerequisites for this design.

### 3.1 The ledger is the median-dual conserved quantity

The RD primitive recovery uses

\[
    \rho_i=P_i.\mathrm{Mass}/\mathrm{DualArea}_i,
\]

and momentum and energy are stored directly as median-dual integrated
quantities. The early hierarchical prototype's extra `Volume/DualArea` scaling
is no longer present.

### 3.2 Geometry is independent of activity

`rd_element_set` distinguishes the complete physical owned element set from
the active subset. `DualArea` is accumulated from the complete set, so an
inactive patch cannot shrink a vertex control volume. This was a necessary
precondition for local timebins.

### 3.3 One physical triangle has one owner

`rd_simplex_claimed()` assigns a fixed-mesh physical simplex to the task
holding the globally minimum `(ID, task)` vertex as a local primary copy. The
rule has already passed equal-step 1/4/16-rank tests. For a persistent full
static mesh, the owner itself need not be active: it can compute a due triangle
from local plus exchanged vertex data.

### 3.4 Remote vertex ledgers already accept increments

`FluxRD_list` exports a triangle's distributed increments by destination task
and original particle index, and `apply_FluxRD_list()` applies them to the
primary vertex's conserved arrays independent of activity. This is already the
required `Q`-ledger behaviour.

### 3.5 Vertex stage context survives migration and restart

`struct sph_particle_data` contains `RD_Ustage0` and `RD_dU`. Restart IO writes
the raw `SphP` array, and domain decomposition transports the complete `SphP`
record. A vertex-owned stage context can therefore survive the interval between
the two hydro call sites without a persistent per-element owner.

Ghost exchange already carries live `TimeBinHydro`, `TimeLastPrimUpdate`,
`VelVertex`, and `RD_dU`; the final specification may add an explicit stage
timestamp/frozen flag or reconstruct them from live bins.

## 4. Correct vertex and triangle clocks

Let vertex `i` have physical timestep

\[
    h_i=2^{b_i}\Delta t_{\rm base}.
\]

The triangle timestep is

\[
    h_T=\min_{i\in T}h_i,
    \qquad b_T=\min_{i\in T}b_i.
\]

A triangle is due at a global event exactly when

\[
    \mathrm{TimeBinSynchronized}[b_T]=1.
\]

This is preferable to the current active mask's implementation-specific test
for a synchronised local-original vertex. It is defined from all three live
vertex bins and remains valid when the triangle owner is not the task owning
the active driver vertex.

For every vertex `i` and incident triangle `T`,

\[
    h_T\le h_i.
\]

Consequently, at the endpoint of a vertex interval, every incident triangle
has completed an integer number of nested substeps. "Wait for the whole
triangle star" is therefore a hierarchy invariant, not an explicit runtime
barrier.

Only after all due triangle increments at that event have been applied locally
and remotely may an active vertex execute

\[
    U_i^{\rm sync}\leftarrow Q_i/|S_i|,
    \qquad \tau_i\leftarrow t.
\]

The existing order `compute hydro -> update_primitive_variables()` already
provides this closing barrier.

## 5. The freezing rule is vertex-star based, not edge-local

The production algorithm must never give one vertex different states on
different triangle edges. A triangle must continue to receive one coherent
state per vertex and construct one P1 state, one Roe average, one set of
`K_i`, and one N/LDA distribution.

Define the finest incident-element timestep of vertex `i`:

\[
    h_i^{\rm star}=\min_{T\ni i}h_T.

\]

Because `h_T <= h_i`, a vertex is RK-stage-live only if

\[
    h_i^{\rm star}=h_i,
\]

which is equivalent to every incident triangle having timestep `h_i`. If

\[
    h_i^{\rm star}<h_i,
\]

the vertex is frozen throughout its entire star:

\[
    U_i^{\rm stage}=U_i^{\rm sync},
    \qquad RD\_dU_i=0.
\]

This corrects the weaker statement "freeze vertices only where adjacent
triangle bins differ". A coarse vertex may be surrounded entirely by
triangles that all share the same finer bin; it must still be frozen because
its own primitive state is not due to advance.

Equivalently, a vertex is stage-live only when no vertex in its Delaunay
one-ring has a finer timestep. A stage-live vertex then has a complete,
synchronously due triangle star, so one assembled RD predictor is well
defined. A frozen vertex accepts final increments in `Q` but has no RK
predictor state during the open interval.

For MPI, `h_i^star` must be reduced over the complete incident star, including
triangles owned on remote tasks, and the resulting vertex-global freeze state
must be sent to all ghosts.

## 6. The `JKL/KML` example

Let

\[
    h_{JKL}=H,
    \qquad h_{KML}=h<H.
\]

Since `JKL` is coarse,

\[
    h_K\ge H,
    \qquad h_L\ge H.
\]

The fine timestep of `KML` must therefore be driven by `M`. During each fine
interval, `KML` evaluates its element residual from the unique triplet

\[
    \left(U_K^{\rm sync},
          U_M^{\rm stage},
          U_L^{\rm sync}\right)

\]

and distributes the final RK increment to `Q_K`, `Q_M`, and `Q_L`. `K` and `L`
do not recover primitive variables. `M` recovers them only if its own vertex
bin is active after every incident fine/finer triangle has closed at that
event.

At `K` or `L`'s own endpoint, all incident triangles have covered the complete
vertex interval. Only then is the purple median-dual ledger converted back to
the new synchronised state.

## 7. Proposed two-call N+RK2 update

The initial hierarchy should use the diagonal temporal mass of the N scheme.
It is algebraically the explicit trapezoidal/Heun update and can be staged
without the F1 total-residual coupling.

### 7.1 First hydro call: open due intervals

For every due triangle `T`, compute from the interval-start synchronised states

\[
    \phi_i^{T,(0)}=\phi_i^T(U^{\rm sync}).
\]

Apply the first half of the final quadrature to every vertex ledger:

\[
    Q_i\mathrel{+}=-\frac{h_T}{2}\phi_i^{T,(0)}.
\]

Separately accumulate a full-weight predictor scratch. For a stage-live vertex,
all incident elements have `h_T=h_i` and open together, so

\[
    RD\_dU_i
    =-\frac{h_i}{|S_i|}
      \sum_{T\ni i}\phi_i^{T,(0)}.
\]

For a frozen vertex, set `RD_dU_i=0`. This value belongs to the open vertex
interval and must not be globally reset by later events in finer bins.

The full predictor scratch requires an MPI accumulation analogous to
`FluxRD_list`, but it writes a transient vertex accumulator rather than the
conserved ledger. After the accumulation, exchange the vertex stage context
to ghosts.

### 7.2 Second hydro call: close due intervals

At the interval endpoint, evaluate each due triangle with

\[
    U_i^{\rm stage}=
    \begin{cases}
      U_i^{\rm sync}+RD\_dU_i,
        & h_i^{\rm star}=h_i,\\
      U_i^{\rm sync},
        & h_i^{\rm star}<h_i.
    \end{cases}
\]

Compute

\[
    \phi_i^{T,(1)}=\phi_i^T(U^{\rm stage})
\]

and apply

\[
    Q_i\mathrel{+}=-\frac{h_T}{2}\phi_i^{T,(1)}.
\]

The completed triangle contribution is therefore

\[
    \Delta Q_i^T
    =-\frac{h_T}{2}
      \left(\phi_i^{T,(0)}+\phi_i^{T,(1)}\right).
\]

After all local and imported contributions have been applied, the existing
active-particle primitive update closes the active vertex intervals.

### 7.3 Why this is preferable to the current internal stage loop

The current total-residual implementation temporarily uses the conserved
arrays as `Q*`, recovers `U*` for all gas cells, applies a vertex-local
`+dU/2`, and completes both stages in one solver call. That construction uses
one global `dt` and globally resets `RD_dU`; neither operation is valid with
several open bins.

The two-call form keeps distinct:

\[
    Q_i^{\rm ledger},
    \qquad U_i^{\rm sync},
    \qquad RD\_dU_i.
\]

It also avoids storing a per-element stage-0 residual: the first half has
already been applied, and only the vertex predictor is needed at the endpoint.

### 7.4 Restart and domain-decomposition implication

The first half changes `Q` before AREPO's interruption check. A restart must
therefore preserve `RD_dU` and the interval phase. Raw `SphP` restart storage
already preserves the vertex fields, and `RestartFlag == 1` skips the first
half on the resumed iteration, which is compatible with this staging. An
explicit phase/timestamp assertion should nevertheless be added to prevent a
stale scratch from being consumed.

Domain decomposition transports complete `P/SphP` records, so a vertex-owned
predictor can migrate without freezing a triangle owner. However, the static
mesh must be rebuilt as the complete physical tessellation rather than an
active-cell fragment. The first Phase-B prototype should disable runtime
domain decomposition; production support requires a separate full-mesh audit.

## 8. Macro-synchronised conservation proof

Local RD conservation at each stage gives

\[
    \sum_{i\in T}\phi_i^{T,(s)}=\Phi^{T,(s)},
    \qquad s\in\{0,1\}.
\]

Hence

\[
    \sum_{i\in T}\Delta Q_i^T
    =-\frac{h_T}{2}
      \left(\Phi^{T,(0)}+\Phi^{T,(1)}\right).
\]

For same-bin neighbouring triangles, both stages occur at the same absolute
times and both sides read the same vertex-owned endpoint states. Their common
mathematical boundary contribution cancels stage by stage.

For cross-bin neighbouring triangles, the common-edge vertices have timesteps
at least as coarse as the coarser triangle. Under the vertex-star rule they
remain synchronised/frozen throughout that coarse interval. The boundary
integrand is therefore constant at both RK stages. If `H=K h`, the fine side
accumulates

\[
    K\frac{h}{2}(B_e+B_e)=H B_e,
\]

while the coarse side accumulates `-H B_e`. They cancel at the coarse endpoint
at any power-of-two ratio.

The proof requires the current algebraic total residual to equal the exact
boundary integral of the continuous Roe-parameter P1 trace:

\[
    \sum_jK_j\widehat U_j
    \stackrel{?}{=}
    \oint_{\partial T}F(Z_h)\cdot n\,ds.
\]

This must be pinned by the standalone random-element algebra test before the
scheduler is changed. The production solver need not calculate edge fluxes if
the identity holds; the edge representation remains a proof device.

Intermediate fine events need not conserve physical `sum_i Q_i`, because one
side of a cross-bin pair has only partially completed the parent interval. The
audit point is after all due second halves at a parent/coarsest synchronisation
point and before the next first halves open new intervals.

## 9. A coarse triangle surrounded by fine triangles

This configuration is topologically and temporally possible. Let coarse
`ABC` have timestep `H`, while each of its three edge-neighbour triangles has
timestep `h<H`, driven by its own opposite vertex. Then

\[
    h_A,h_B,h_C\ge H,
\]

and all three coarse vertices are frozen.

### 9.1 Conservation

There is no additional macro-conservation obstruction. Every coarse boundary
edge has constant endpoint states, so its fine accumulated contribution and
coarse contribution cancel at `H` as in section 8.

### 9.2 Temporal accuracy

All three coarse stage states are frozen, so

\[
    \phi_i^{T,(1)}=\phi_i^{T,(0)}
\]

and the coarse triangle's Heun update reduces to

\[
    \Delta Q_i^T=-H\phi_i^T(U^n),
\]

which is forward Euler in time. A single isolated coarse triangle contributes
a local first-order error; a population of coarse islands can turn the
nominally codimension-one interface defect into a finite-area first-order
region.

### 9.3 Delayed response and positivity

The surrounding fine triangles repeatedly modify the coarse vertices'
ledgers, but the states used by every residual remain frozen until the vertex
endpoint. Waves crossing the timebin interface may therefore be delayed or
partially reflected.

This is also the strongest provisional-ledger positivity test. Before the
coarse correction has completed, a vertex may have received several outgoing
fine contributions without all compensating incident contributions. Both

\[
    Q_i^\rho>0
\]

and

\[
    Q_i^E-\frac{|\mathbf Q_i^m|^2}{2Q_i^\rho}>0
\]

must be audited after every event, not only when primitive variables are
recovered.

If this test fails, exact macro conservation is insufficient for a usable
scheme. Candidate responses are a conservative RD ledger limiter, an optional
neighbour-bin ratio bound, or a pending-increment/register construction.

## 10. Why LDA+F1 is excluded from the first hierarchy

The exclusion is specifically about the F1 temporal mass, not the LDA spatial
residual.

For the N scheme, the lumped temporal mass is diagonal:

\[
    m_{ij}^{N,T}=\frac{|T|}{3}\delta_{ij}I,
\]

so a frozen vertex has an unambiguous zero stage increment, and the method
reduces to the explicit trapezoidal update of section 7.

For LDA+F1, the temporal target couples all triangle vertices:

\[
    T_i^T
    =\beta_i^T\frac{|T|}{3}
      \sum_{j\in T}\frac{U_j^*-U_j^n}{h_T}.
\]

In fine `KML`, `M` has a fine predictor but `K,L` are coarse frozen vertices.
Their `Delta U/h` has no accepted meaning:

- zero is consistent with frozen residual evaluation but discards the actual
  non-diagonal F1 coupling;
- the provisional ledger difference is incomplete and changes every fine
  event;
- a fraction of a coarse predictor requires a new multirate dense-output
  derivation and a proof against double counting.

The current F1 corrector also relies on one global timestep to telescope the
element temporal terms against a vertex-local `+dU/2`. That identity does not
carry over automatically when incident triangles use different intervals.

Finally, fixed-mesh Richardson tests already show first-order temporal
convergence for current LDA+F1; mixed, coherent-beta-n, and coherent-beta-star
all retain the defect. Adding cross-bin coupling before that equal-bin defect
is understood would make the hierarchy experiment uninterpretable.

LDA spatial distribution may later be tested with a lumped/mixed temporal mass.
Full multirate F1 is a later mathematical phase.

## 11. MPI and ownership requirements

For a fixed persistent full mesh, retain the current minimum-global-ID simplex
owner initially. The owner does not need to be active; it needs the triangle
and live vertex/ghost context. Each first or second sweep independently
computes every due triangle exactly once, so domain migration between stages
does not require a frozen per-element owner.

Required changes and audits are:

1. replace the current local-original active test by
   `TimeBinSynchronized[b_T]` from all three live bins;
2. reduce `b_i^star=min_{T contains i} b_T` over complete local and remote
   incident stars;
3. accumulate full-weight stage-0 predictor increments to primary vertices by
   MPI without confusing them with half-weight ledger increments;
4. exchange the resulting `RD_dU`, freeze state, timestamp, and all primitive
   data used by the stage calculation;
5. apply final increments to primary `Q` independent of vertex activity;
6. audit exactly one triangle evaluation per stage and 1/4/16-rank
   decomposition invariance;
7. ensure deterministic/canonical accumulation order is sufficient for the
   desired round-off conservation threshold.

Runtime static-mesh domain decomposition remains out of the first prototype
because the current mesh rebuild path must be proved to reconstruct the full
physical tessellation under partial activation.

## 12. CFL and performance work not supplied by the scheduler

The AREPO timebin machinery can quantise and synchronise vertex timesteps, but
the current `get_timestep_hydro()` uses a Voronoi-cell radius. A production RD
hierarchy needs a median-dual/star CFL estimate such as

\[
    h_i\le C_{\rm CFL}
    \frac{2|S_i|}
         {\sum_{T\ni i}l_{\max}^T\lambda_{\max}^T}.
\]

The denominator must be accumulated over the complete MPI-distributed star at
the vertex's activation. Controlled Phase-B experiments should begin with an
externally prescribed two-zone bin map so scheduler correctness is not mixed
with a new CFL implementation.

The current solver rebuilds/scans the complete owned triangle set on every
call. That is acceptable for a correctness prototype but removes much of the
performance benefit of a hierarchy. A production path needs persistent
element-bin buckets or an incident-element update structure when active vertex
bins change.

## 13. Verification sequence and acceptance criteria

No hierarchy implementation should precede test 1.

1. **Element algebra test.** On random admissible triangles and states, compare
   `sum_j K_j Uhat_j` with an independently evaluated exact boundary integral
   of `F(Z_h).n`. Require a scale-aware round-off result.
2. **Equal-bin control.** Preserve the existing N+RK2 solution; preferably
   dispatch the all-equal case to the current path for bitwise identity.
3. **Two-triangle/two-bin test.** Use the labelled `JKL/KML` topology or a
   periodic analogue. Check stage ownership, frozen-state uniqueness, and
   conservation after the parent endpoint.
4. **Coarse-island test.** Surround one coarse triangle by fine neighbours at
   ratios 2, 4, 8, and 16. Record parent-sync conservation, intermediate
   imbalance, minimum ledger density/internal energy, and local error.
5. **Smooth transport.** Fixed Yee/advection problem with a stationary bin
   interface. Measure adjacent-solution Richardson differences separately in
   the uniform-bin regions and interface strip.
6. **Shock/bin-interface test.** Place a shock normal to a bin boundary. Check
   positivity, reflection, and whether a bin-ratio limiter is required.
7. **Morton Kelvin--Helmholtz comparison.** His conservation loss should fall
   to round-off at parent synchronisation, not merely become smaller.
8. **MPI matrix.** Repeat the conservation, state, and positivity audit at
   1/4/16 ranks.
9. **Restart test.** Restart between the first and second hydro calls and match
   an uninterrupted run.

At every test report:

- requested and realised vertex/triangle bins;
- number of stage-live and frozen vertices;
- number of due triangles per bin and exactly-once counts;
- conservation after every parent/coarsest close point;
- maximum intermediate physical-ledger imbalance;
- minimum predictor and ledger density/pressure/internal energy;
- equal-bin and MPI state differences by ParticleID.

## 14. Questions for Claude's review

1. Does the stronger vertex-star criterion
   `min_{T contains i} h_T < h_i -> frozen` close the edge-local/coherent-element
   ambiguity in Construction A?
2. Is the split Heun update -- first half applied at the opening call, full
   predictor kept in `RD_dU`, second half at the closing call -- algebraically
   the preferred N+lumped hierarchy, including the restart boundary?
3. Does any term in the current N total-residual formulation prevent replacing
   the internal `Q*`, `+dU/2`, and lumped temporal term by this explicit
   trapezoidal form on mixed bins?
4. Is minimum-global-ID simplex ownership sufficient on a persistent full
   static mesh when activity is derived from live `b_T`, or is there a static
   MPI counterexample requiring driver ownership?
5. Can the Roe-parameter edge identity be written as an independent exact
   quadrature suitable for test 1, including the current normal convention?
6. Does the scalar N convexity argument extend to a frozen vertex receiving a
   sequence of fine residuals over its own CFL interval, and what additional
   condition is needed for Euler admissibility of the provisional ledger?
7. Should a negative provisional ledger reject the construction immediately,
   or may unmatched increments be held outside physical `Q` until the parent
   close point?

## 15. Current decision boundary

The present result supports a Phase-B specification and standalone algebra
tests. It does not yet authorise removal of `FORCE_EQUAL_TIMESTEPS` or a solver
implementation.

The recommended first implementation target, after review, is narrowly:

\[
\boxed{
  \text{fixed mesh}
  +\text{prescribed two-level bins}
  +\text{N/lumped two-call RK2}
  +\text{vertex-star freezing}
}
\]

F1, beta/gamma changes, moving mesh, refinement, production domain
decomposition, and automatic RD CFL bins remain outside that first target.
