# Phase-B fixed-mesh hierarchical timestep prototype

Date: 2026-08-02

Author: Codex (GPT-5)

Status: experimental implementation and controlled tests completed; not yet a
general RD timestep implementation

## 1. Outcome

The first fixed-mesh hierarchical RD prototype was implemented for
`N_SCHEME + RD_RK2_TOTAL_RESIDUAL`; a controlled frozen-stage
`LDA_SCHEME + F1` extension has subsequently been implemented and tested. Its
code structure is the anticipated hybrid:

- it restores AREPO's original two hydro call sites, with
  `find_next_sync_point()` between them;
- it retains the validated concentrated RD RK2 predictor rather than the old
  primitive-gradient/Taylor predictor;
- conserved variables remain the persistent ledger, while primitive variables
  are recovered only for vertices active at their own interval endpoint.

The controlled tests establish five distinct facts.

1. With all bins equal, the two-call implementation reproduces the concentrated
   `N + RK2` implementation to round-off and retains second-order temporal
   self-convergence.
2. With a fixed 2:1 bin interface, the code schedules the intended hierarchy,
   is conservative to round-off, preserves positive predictor states, and is
   MPI-decomposition independent to round-off.
3. The vertex-star minimum must be formed from the globally unique owned
   physical triangle set. Neither a local-primary complete-star assumption nor
   a reduction over every local ghost triangle is decomposition independent.
4. The present frozen-star Construction A is first order in time at fixed
   spatial mesh. This is an interface-semantic error, not an RK2 or beta error.
5. `CREATE_FULL_MESH` is not required on the fixed geometry. Rebuilding a
   genuinely active-only static tessellation at every partial synchronization
   reproduces the full-mesh result to round-off on one and four ranks, including
   after real particle migration during domain decomposition.

The implementation is therefore a valid conservation and scheduling prototype,
but the fixed-mesh Richardson result prevents calling it a globally
second-order hierarchical integrator.

## 2. Implemented scope and guards

The new compile-time switch is `RD_HIERARCHICAL_TIMESTEPS`. The prototype
requires:

- `VORONOI_STATIC_MESH`;
- either `N_SCHEME`, or the experimental frozen-stage `LDA_SCHEME` path;
- `RD_RK2_TOTAL_RESIDUAL`;

It has now been tested in two fixed-geometry mesh modes:

- a persistent complete mesh, with or without `CREATE_FULL_MESH` (removing the
  macro alone does not make a mesh built at the all-active initial point
  partial); and
- a genuine active-only mesh, without `CREATE_FULL_MESH` and with
  `VORONOI_STATIC_MESH_DO_DOMAIN_DECOMPOSITION`, which rebuilds the
  tessellation around active primaries at partial synchronization points.

The controlled two-level test uses `RD_HIERARCHICAL_TEST_PATTERN`, which makes
the vertices with `x < BoxSize/2` one timebin finer than the fresh CFL candidate.
This flag is testing apparatus, not a proposed production bin criterion.

The prototype deliberately does not enable LDA/F1, beta variants, gamma,
Galerkin mass, moving mesh, or a new rank API. Static domain decomposition is
now covered; vertex coordinates remain fixed throughout.

## 3. Discrete update

For triangle `T`, let

\[
  b_T=\min_{i\in T}b_i,\qquad
  h_T=2^{b_T}\,\Delta t_{\rm base}.
\]

For vertex `i`, form the complete star minimum

\[
  b_i^{\rm star}=\min_{T\ni i}b_T.
\]

The vertex is stage-live iff `b_i^star = b_i`. Otherwise it has one frozen
synchronised state for its whole star and `RD_dU=0`. There is never a different
state for the same vertex on different triangle edges.

At the opening hydro call for every due triangle,

\[
  Q_i \mathrel{-}= \frac{h_T}{2}\,\phi_i(U^{(0)}),
\]

and each stage-live vertex separately accumulates the full intensive predictor

\[
  RD\_dU_i=-\frac{1}{|S_i|}\sum_{T\ni i}h_T\phi_i(U^{(0)}).
\]

At the closing call, a stage-live vertex supplies
`U^(1)=U^sync+RD_dU`; a frozen vertex supplies `U^sync`. The due triangles then
apply

\[
  Q_i \mathrel{-}= \frac{h_T}{2}\,\phi_i(U^{(1)}).
\]

AREPO's existing active list subsequently recovers primitives only for vertices
whose own interval ends at that synchronization point. Inactive vertices keep
accepting distributed residuals in `Mass`, `Momentum`, and `Energy` without a
premature primitive recovery.

When every bin is equal, every vertex is stage-live and the formula reduces
exactly to the existing concentrated explicit-trapezoidal/Heun RD step.

## 4. Code mapping

| Area | Prototype change |
| --- | --- |
| `src/main/run.c` | opening and closing calls select predictor/corrector RD stages |
| `src/hydro/residual_distribution_solver.c` | due-triangle classification, full/active-only ownership, persistent static dual areas, vertex-star reduction, half-ledger updates, full predictor assembly, stage-state selection, assertions and diagnostics |
| `src/main/allvars.h`, `src/mesh/mesh.h` | persistent/local and exchanged `RD_StarTimeBin`, `RD_PredictorEnd` |
| `src/mesh/voronoi/voronoi_exchange.c` | exchange star bin, predictor endpoint, and existing `RD_dU` |
| `src/time_integration/timestep.c` | optional controlled 2:1 test pattern derived from the fresh CFL candidate |
| `defines_extra`, `Template-Config.sh` | legal and documented switches |
| `examples/yee_2d/Config_RD_RK2_N_{INTERNAL,HIER_EQUAL,HIER_2LEVEL}.sh` | reference, equal-bin, and full-mesh two-level test configurations |
| `examples/yee_2d/Config_RD_RK2_N_HIER_{NOFULL_PERSISTENT,ACTIVE_STATIC}.sh` | no-macro persistent-mesh control and true active-only static rebuild configuration |

The predictor endpoint is stored as an integer timeline value and asserted at
the closing stage. This prevents a stale `RD_dU` from a different vertex
interval from being consumed silently.

## 5. MPI star construction and rejected assumptions

The final algorithm constructs the star from exactly the physical triangles
claimed by `rd_simplex_claimed()`, the same global minimum-ID ownership rule
used by the residual ledger. Each triangle owner sends its `b_T` candidate to
remote primary vertices; primary owners take the minimum and exchange the
completed result through `PrimExch`.

Two intermediate implementations were rejected by tests:

1. **Local-primary complete-star assumption.** Scanning only triangles held on
   the primary vertex's task produced 132 frozen vertices on one rank but 128
   on four ranks. `CREATE_FULL_MESH` makes every cell participate, but does not
   make every task's local triangulation a complete global simplicial complex.
2. **All local physical ghost triangles.** Reducing candidates from every task's
   local ghost triangulation produced 132 frozen vertices on one rank and 155
   on four ranks. Partition-boundary ghost geometry can include additional
   locally valid simplices not selected by the global ownership set.

Using only globally owned triangles gives 3968 stage-live and 128 frozen
vertices on both one and four ranks. This is also the mathematically correct
definition: the star clock is derived from exactly the triangles whose
residuals enter the ledger.

The ownership key needs one precise adaptation for a genuinely active-only
mesh. A persistent/full mesh can use the minimum `(ParticleID, task)` over all
three vertices. On a partial rebuild, that minimum vertex might be inactive and
its primary star absent. The owner is therefore the minimum key among vertices
in the triangle's finest bin `b_T`. At least one such vertex is active whenever
the triangle is due, all ranks see the same live timebins, and exactly one
primary instance claims the triangle. The same owned set defines the residual
ledger and the vertex-star reduction.

`DualArea` follows different semantics: it is initialized once from the
all-active static tessellation, then persists and migrates as part of `SphP`.
Recomputing it from a fine-only mesh would replace a complete median-dual cell
by an incomplete active-star fragment. Debug builds check both local positivity
and the invariant global coverage `sum_i DualArea_i = BoxSize_X BoxSize_Y`
after active-only domain decompositions.

The controlled test scheduler initially had a separate ratchet error: it
subtracted one bin after AREPO's old-bin synchronization check, so a fine
vertex became finer on every activation. The corrected code refines the fresh
CFL candidate before validity/synchronization checks. The final runs remain at
bins 27/26 and `max_ratio=2` throughout.

## 6. Immutable artifacts and jobs

### Equal-bin round-off reference

- concentrated internal-loop binary:
  `build_artifacts/phaseb-n-internal-reference/1133814b4a72-4a2a6eee510b8570/Arepo`
- SHA256:
  `932b3abd49ad62ac29805b43b38a9af2e5158b646848a006db88b2b49e1a2c46`
- two-call equal-bin binary:
  `build_artifacts/phaseb-n-two-call-equal/1133814b4a72-ef21c5e3b3a40e3c/Arepo`
- SHA256:
  `92918c5e83973e312cda9e3897371e957cbc6377fcd6c119e0a86647ee067d3a`
- jobs: `10357897` and `10357898`, both `COMPLETED`, exit `0:0`.

### Final two-level implementation

- binary:
  `build_artifacts/phaseb-n-two-level-ownedstar/1133814b4a72-e10e46e7f9941054/Arepo`
- SHA256:
  `8113a62758df026d0510a9e2782d4dd0df6fe35e66ad3f9020fc247066ec8317`
- one/four-rank short jobs: `10357908`, `10357909`, both `COMPLETED`, exit
  `0:0`.
- hierarchy ladder jobs: `10357915`, `10357914`, `10357916`, `10357917`, all
  `COMPLETED`, exit `0:0`.

### Active-only static-mesh extension

- no-`CREATE_FULL_MESH`, persistent-mesh control binary:
  `build_artifacts/phaseb-n-nofull-persistent/45abb3a5d266-f30ade81f1a0d6ae/Arepo`
- SHA256:
  `95e573691b228c004e7bd21bf1a86d5f42dd85363edf53784a6df41ad4f1575d`
- true active-only static-rebuild binary:
  `build_artifacts/phaseb-n-active-static/45abb3a5d266-714851c5abfbfb2a/Arepo`
- SHA256:
  `9f83eee8772603fa501505ff074984a345514311874e03ecd8efcbfb39304a0f`
- no-macro persistent one/four-rank jobs: `10357925`, `10357924`;
- active-only short one/four-rank jobs: `10357926`, `10357927`;
- active-only `TimeMax=1` one/four-rank jobs: `10357928`, `10357929`.

All eight builds/runs listed in this subsection completed with exit `0:0`.

After adding the persistent-area coverage assertion, the final audit artifact
is
`build_artifacts/phaseb-n-active-static-audit/45abb3a5d266-b86d353b5bdba274/Arepo`
with SHA256
`13f3f340cd56db4548c62a9e0deba5c4188a2d847b4b358ccc0042e3e8298494`.
Build job `10357930` and short one/four-rank jobs `10357931`, `10357932` all
completed with exit `0:0`; the assertion remains satisfied on every rebuild.
The audit one-rank snapshot is bitwise identical to the pre-assertion result,
and its one/four-rank differences reproduce the table in Section 7.6.

The committed-source rebuild uses commit `7e6f12213bf8` and artifact
`build_artifacts/phaseb-n-active-static-final/7e6f12213bf8-0fd030bf7b8c29f5/Arepo`,
SHA256
`0d7cbcaeb4b562a0c7187c91344ab2c57221b0388b9b589e8c1444165d8eaffa`.
Build job `10357933` and short one/four-rank jobs `10357934`, `10357935` all
completed with exit `0:0`. The committed binary again gives a bitwise-identical
one-rank result and the same round-off MPI differences.

The campaign root is
`/home/zwu/Hydro_data_analysis/Data_arepo_RD/yee_boost/phaseb_hierarchy_v1`.
Every output directory contains the parameter file, build manifest, binary
checksum, source status/patch, rank count, host, and exit status under a
timestamped `provenance-*` directory.

## 7. Test results

All tests use the same jittered Yee `n=64`, boost `+1` initial condition and a
fixed mesh.

### 7.1 Equal-bin algebraic regression

At `TimeMax=1/64`, `dt=1/256`, the concentrated internal-loop and two-call
solutions, matched by ParticleID, differ by:

| Field | maximum absolute difference |
| --- | ---: |
| density | `2.22e-15` |
| velocity | `2.89e-15` |
| internal energy | `6.66e-15` |
| mass | `7.63e-17` |
| pressure | `2.22e-15` |

Coordinates and hydro timebins are bitwise identical. Predictor minima at each
step also agree.

### 7.2 Equal-bin Richardson ladder

The ladder uses `TimeMax=1` and `dt=1/256, 1/512, 1/1024, 1/2048`. For

\[
 U=(\rho,\rho v_x,\rho v_y,\rho E),
\]

solutions are matched by ParticleID and the norm uses one common static
DualArea weight. The adjacent differences are:

| Difference | L1 | L2 | Linf |
| --- | ---: | ---: | ---: |
| D0, 1/256 - 1/512 | `6.33249e-7` | `1.42180e-6` | `1.01170e-5` |
| D1, 1/512 - 1/1024 | `1.58356e-7` | `3.55423e-7` | `2.52180e-6` |
| D2, 1/1024 - 1/2048 | `3.95055e-8` | `8.86254e-8` | `6.28220e-7` |

The adjacent orders `p=log2(Dk/Dk+1)` are:

| Norm | p0 | p1 |
| --- | ---: | ---: |
| L1 | `1.99960` | `2.00305` |
| L2 | `2.00011` | `2.00375` |
| Linf | `2.00425` | `2.00512` |

This directly satisfies Claude's mandatory regression: the two-call hybrid is
temporally second order when it degenerates to equal bins.

### 7.3 Fixed 2:1 scheduling and MPI invariance

For coarse `dt=1/256` and fine `dt=1/512`, `TimeMax=1/64`:

- sync points alternate 2048 fine active vertices and all 4096 vertices;
- due triangle counts alternate 4224 and 8192;
- both one and four ranks report 3968 stage-live and 128 frozen vertices;
- `max_ratio=2` throughout;
- final one/four-rank fields agree to round-off: density `6.66e-16`, velocity
  `1.11e-15`, internal energy `2.66e-15`, mass `2.78e-17`, and pressure
  `1.33e-15` in maximum absolute difference.

### 7.4 Two-level Richardson ladder

Here the listed `dt` is the coarse timestep; the left half uses `dt/2`.
`TimeMax=1`.

| Difference | L1 | L2 | Linf |
| --- | ---: | ---: | ---: |
| D0, 1/256 - 1/512 | `1.59281e-5` | `7.92697e-5` | `1.61795e-3` |
| D1, 1/512 - 1/1024 | `8.03741e-6` | `3.97335e-5` | `8.08647e-4` |
| D2, 1/1024 - 1/2048 | `4.03905e-6` | `1.98939e-5` | `4.04237e-4` |

| Norm | p0 | p1 |
| --- | ---: | ---: |
| L1 | `0.98677` | `0.99271` |
| L2 | `0.99641` | `0.99803` |
| Linf | `1.00059` | `1.00031` |

The hierarchy-minus-equal solution difference halves with orders
`0.9986..0.9994` in L1, `0.9990..0.9997` in L2, and
`1.0001..1.0004` in Linf. Thus the first-order term is introduced specifically
by the frozen hierarchy interface.

### 7.5 Runtime validity, positivity, and conservation

Across all equal and hierarchy ladder cases:

- actual sync counts are exactly 256/512/1024/2048 for the equal ladder and
  512/1024/2048/4096 for the two-level ladder;
- every run exits zero and every Slurm state is `COMPLETED`;
- `f1_lumped=0` everywhere;
- minimum assembled predictor density is at least `0.4976801`;
- minimum assembled predictor pressure is at least `0.3764782`;
- maximum element distribution conservation defect is below `1.84e-15`;
- snapshot total mass changes are at round-off (`<=5.69e-14` absolute);
- total energy changes are at round-off (`<=5.69e-14` absolute);
- momentum changes are reduction-order round-off (`<=6.40e-13` absolute).

No energy floor, negative-mass termination, predictor endpoint mismatch,
coverage assertion, or non-finite value occurred.

The analytic Yee errors remain spatial-error dominated at this fixed mesh. For
example, hierarchy density L1 changes from `0.00332602` to `0.00332541` over
the ladder, which is why temporal order is correctly measured from adjacent
numerical solutions rather than from analytic errors.

### 7.6 Genuine active-only static mesh

Removing `CREATE_FULL_MESH` while retaining the initial static tessellation is
an important negative control, not an active-only implementation. At `t=0` all
particles are active, so that mesh remains complete. This control agrees with
the original full-mesh result to at most `1.8e-15` in the primitive fields.

The true active-only configuration additionally enables static domain
decomposition and reconstructs the mesh at every synchronization point because
`ActivePartFracForNewDomainDecomp=0.01`. At fine-only points the one-rank mesh
contains about 2242 local/periodic points, versus about 4354 at full
synchronization. Nevertheless the globally owned due triangle counts remain
exactly 4224/8192, and stage-live/frozen counts remain 3968/128.

For the short `TimeMax=1/64` test, active-only one-rank versus four-rank maximum
field differences are:

| Field | maximum absolute difference |
| --- | ---: |
| density | `7.77e-16` |
| velocity | `1.11e-15` |
| internal energy | `2.66e-15` |
| mass | `2.08e-17` |
| pressure | `1.11e-15` |

The one-rank active-only result versus the original full-mesh result differs by
at most `1.8e-15` in primitive fields. Over the long `TimeMax=1` run (512 sync
points and 514 mesh constructions), active-only one/four-rank differences stay
at accumulated round-off: density `3.11e-15`, velocity `4.00e-15`, internal
energy `7.99e-15`, mass `9.71e-17`, and pressure `3.89e-15`. The active-only
one-rank result versus the full-mesh hierarchy reference is similarly within
`8.44e-15` in every primitive field.

This test genuinely exercises migration. The four-rank log records 1792
particles exchanged at the first fine-only domain decomposition and about 2176
at later decompositions. Thus persistent `DualArea`, `RD_dU`, star-bin, and
predictor-endpoint fields crossed task boundaries rather than merely surviving
an empty rebuild. Both long runs finish with `f1_lumped=0`, minimum predictor
density/pressure `0.4978825/0.3767499`, maximum distribution conservation
defect below `1.82e-15`, and globally conserved quantities changing only at
floating-point reduction round-off.

## 8. Interpretation

The conservation concern is resolved for this construction: an inactive
vertex can safely accept residuals in its conserved ledger, exactly as an
inactive FV cell accepts flux, provided each globally owned triangle is
evaluated once when due and primitive recovery waits for the vertex endpoint.
There is no need to reinterpret RD as pairwise face-flux exchange.

The active-only experiment strengthens this conclusion. A complete
tessellation need not remain resident between synchronization points. It is
sufficient that every due triangle is discoverable from at least one active
finest-bin primary, ownership is defined within that active subset, and
geometry-dependent control volumes persist independently of the partial mesh.
This is the fixed-geometry RD analogue of AREPO's conserved-variable flux
ledger, without invoking moving-mesh geometry.

The accuracy concern is not resolved. A coarse-side vertex touching a fine
triangle is frozen for its entire star. Triangles using that vertex therefore
do not all receive a genuine second-stage value. The 128-vertex interface layer
creates a first-order temporal term even though the 3968 remaining vertices
use the correct RK2 stage.

This does not yet determine the order under a coupled spatial/CFL refinement.
If the first-order error remains confined to a one-vertex-thick interface, its
fraction is `O(dx)`; an `O(dt)` pointwise error could therefore contribute
`O(dx*dt)=O(dx^2)` to an L1 norm when `dt proportional to dx`. L2 and Linf do
not receive the same codimension-one factor, and advection may spread the
interface error. A joint `n`/`dt` ladder and an error-versus-distance profile
are required before making a thesis-level convergence claim.

The result also shows why beta work should remain paused: the equal-bin N/lumped
RK2 path is demonstrably second order, and the hierarchy-induced defect is
present without F1 or beta. Changing stage-2 distribution coefficients cannot
provide the missing time state at frozen vertices.

## 9. Recommended next experiments

1. Measure the two-level error by distance from the bin interface and separate
   frozen vertices, adjacent live vertices, and the interior.
2. Run a coupled fixed-mesh sequence such as `n=32,64,128` with coarse
   `dt proportional to dx`, reporting L1/L2/Linf separately.
3. Run the accepted shock-tube test with the shock crossing a bin interface,
   checking stale-state CFL margin and positivity.
4. If fixed-mesh second-order time accuracy is required, implement a shared
   vertex-time interpolant/composite quadrature or a persistent subcycled
   predictor ledger. Either replacement must still provide one state per
   vertex per absolute time for the complete star.
5. Test restarts and arbitrary multi-level ratios on the now-validated static
   active-only path. Only after the time-state issue is resolved should the
   method extend beyond N/lumped or address moving meshes.

The present prototype should be retained as the conservative baseline and as a
diagnostic control for any higher-order interface construction.

## 10. Frozen-stage hierarchical LDA+F1 experiment

### 10.1 Time semantics

The experiment deliberately does not invent dense output for an inactive
coarse vertex. In the Figure-17-style example with fine yellow triangle `KML`,
coarse blue triangle `JKL`, fine step `h`, and coarse step `H=4h`, the state
timeline is:

```text
time              0          h          2h         3h          H
                  |----------|----------|----------|-----------|
yellow KML        open-close open-close open-close open-close
M primitive       U_M^0      U_M^1      U_M^2      U_M^3       U_M^4
K,L primitive     U_KL^0 ------------------------------------- U_KL^H
K,L RK dU         0          0          0          0
K,L ledger Q      Q^0 --+dQ0--+dQ1------+dQ2-------+dQ3------- Q^H
blue JKL          open----------------------------------------close
```

`RD_dU` means the RK stage increment, not the unsynchronised difference
`Q(t)/DualArea-U_sync`. The latter contains incomplete contributions from the
whole vertex star and cannot be inserted retroactively into the last fine
substep. Construction A therefore sets `dU=0` for K and L in every fine
corrector and recovers their primitives only after all contributions at `H`
have closed.

### 10.2 Element corrector

For a due triangle `T`, let `dU_i=U_i^*-U_i^n` for a stage-live vertex and zero
for a frozen vertex. The mixed-beta F1 target at the closing state is

\[
 G_T={|T|\over 3h_T}\sum_{j\in T}dU_j,
 \qquad T_{i,T}=\beta_{i,T}^*G_T.
\]

The opening call remains

\[
 \Delta Q_{i,T}^{(0)}=-{h_T\over2}\phi_{i,T}(U^n),
\]

and assembles the full predictor. The closing ledger contribution is

\[
 \Delta Q_{i,T}^{(1)}={|T|\over3}dU_i-h_TT_{i,T}
                       -{h_T\over2}\phi_{i,T}(U^*).
\]

The implementation retains the common `-h_T/2` ledger multiplier by replacing
the closing residual with

\[
 \phi_{i,T}^{close}=\phi_{i,T}(U^*)
   +2\left(T_{i,T}-{|T|\over3h_T}dU_i\right).
\]

Because `sum_i beta_i=I`, the two temporal terms cancel after summing the three
vertex contributions. Thus the correction is conservative element by element,
including when some `dU_i` are zero. For the N/lumped temporal mass,
`T_i=|T|dU_i/(3h_T)` and the correction vanishes identically, recovering the
previous N hierarchy. Rank-deficient `S^-` retains the existing conservative
lumped F1 fallback and increments `f1_lumped`.

Only the existing mixed stage-beta convention is enabled. Coherent beta paths
would require persistent triangle identification across the two call sites and
active-only mesh reconstruction; the earlier three-way experiment gives no
accuracy reason to add that state now.

### 10.3 Acceptance results

All tests use the same jittered Yee `n=64`, boost-one IC.

The equal-bin two-call path reproduces the concentrated mixed LDA+F1 path to
round-off at `TimeMax=1/64`, `dt=1/256`: maximum differences are density
`2.55e-15`, velocity `2.89e-15`, internal energy `7.11e-15`, and mass
`6.94e-17`. Predictor minima agree step by step and `f1_lumped=0` in both.

The 2:1 short full-mesh one/four-rank comparison differs by at most
`8.88e-16` in density, `1.55e-15` in velocity, `2.66e-15` in internal energy,
`3.47e-17` in mass, and `1.11e-15` in pressure. It retains 3968 stage-live and
128 frozen vertices, due-element counts 4224/8192, `f1_lumped=0`, positive
predictors, and element conservation defects below `5.56e-17`.

The active-only short result agrees with the full mesh and between one/four
ranks at round-off. A four-rank active-only `TimeMax=1` run completes 512 sync
points while repeatedly exchanging 1792/2176 particles. It agrees with the
full-mesh result to at most `8.44e-15`, has `f1_lumped=0`, minimum predictor
density/pressure `0.4948897/0.3730988`, and maximum element conservation defect
`6.25e-17`.

The full-mesh hierarchy timestep ladder uses coarse
`dt=1/256,1/512,1/1024,1/2048`, fine `dt/2`, and `TimeMax=1`. For
`U=(rho,rho vx,rho vy,rho E)`, matched by ParticleID with common static
DualArea weights:

| Difference | L1 | L2 | Linf |
| --- | ---: | ---: | ---: |
| D0 | `5.49367e-5` | `1.44466e-4` | `1.79425e-3` |
| D1 | `2.75787e-5` | `7.24613e-5` | `8.96042e-4` |
| D2 | `1.38177e-5` | `3.62882e-5` | `4.47745e-4` |

| Norm | p0 | p1 |
| --- | ---: | ---: |
| L1 | `0.99421` | `0.99704` |
| L2 | `0.99545` | `0.99771` |
| Linf | `1.00174` | `1.00089` |

All ladder jobs exit zero with exactly 512/1024/2048/4096 synchronization
events, `f1_lumped=0`, predictor density/pressure above
`0.4948897/0.3730988`, and maximum element conservation defect below
`7.29e-17`. The result is stable and cleanly first order. Its difference norms
are also larger than the N/lumped hierarchy, so frozen-dU F1 does not improve
the known interface accuracy defect.

### 10.4 Artifacts and jobs

| configuration | binary SHA256 | build job |
| --- | --- | ---: |
| concentrated mixed LDA+F1 | `f03ff08c534694212ad782bfb0d1c07b9fe81b2f52a44f1df73940569c641848` | `10358281` |
| hierarchical equal-bin | `5a3d0c64435f4f17c4e19c99950f00016194ff7f1ae526fbd61ab1241d6c7549` | `10358282` |
| hierarchical 2:1 full mesh | `476ec4b6eaccc4762e8e2b00c71663689ff9fcba7d679e41f3c0cc2833645081` | `10358286` |
| hierarchical 2:1 active-only | `dfa3babb19278c097f3755b02d0b22a54f13b47e838d0045f5d22052ff93a673` | `10358287` |

Equal-bin run jobs are `10358283,10358284`; short full-mesh jobs
`10358288,10358289`; short active-only jobs `10358347,10358348`; ladder jobs
`10358349--10358352`; and the long four-rank active-only job is `10358353`.
Every listed job completed with exit `0:0`.

After committing the implementation as `80482861a9f9`, a clean-source rebuild
produced immutable artifact
`lda-f1-hier-active-final/80482861a9f9-b1ef14b3b8a1b177/Arepo`, SHA256
`25340756c1836a401efcddc006aa7ba8105250e4b8621c8638394fa1a35aa0c3`.
Build job `10358354` and final short one/four-rank jobs `10358355,10358356`
all completed with exit `0:0`. Each final snapshot is bitwise identical to
the corresponding pre-commit active-only result. The final one/four-rank
differences remain density `6.66e-16`, velocity `1.11e-15`, internal energy
`2.66e-15`, mass `3.47e-17`, and pressure `9.99e-16`; coordinates and time
bins are bitwise identical. Both runs retain 3968 live/128 frozen vertices,
the expected 4224/8192 due-element alternation, `f1_lumped=0`, positive
predictors, and element conservation defects no larger than `5.56e-17`.

This experiment demonstrates that frozen `dU=0` is a coherent conservative
baseline, but not a second-order multirate LDA+F1 construction. Dense output or
another coarse-vertex trajectory should be considered only if later evidence
justifies the additional shared time trace and composite quadrature.
