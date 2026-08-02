# Phase-B fixed-mesh hierarchical timestep prototype

Date: 2026-08-02

Author: Codex (GPT-5)

Status: experimental implementation and controlled tests completed; not yet a
general RD timestep implementation

## 1. Outcome

The first fixed-mesh hierarchical RD prototype is implemented for
`N_SCHEME + RD_RK2_TOTAL_RESIDUAL`.  Its code structure is the anticipated
hybrid:

- it restores AREPO's original two hydro call sites, with
  `find_next_sync_point()` between them;
- it retains the validated concentrated RD RK2 predictor rather than the old
  primitive-gradient/Taylor predictor;
- conserved variables remain the persistent ledger, while primitive variables
  are recovered only for vertices active at their own interval endpoint.

The controlled tests establish four distinct facts.

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

The implementation is therefore a valid conservation and scheduling prototype,
but the fixed-mesh Richardson result prevents calling it a globally
second-order hierarchical integrator.

## 2. Implemented scope and guards

The new compile-time switch is `RD_HIERARCHICAL_TIMESTEPS`. The prototype
requires:

- `VORONOI_STATIC_MESH`;
- `CREATE_FULL_MESH`;
- `N_SCHEME`;
- `RD_RK2_TOTAL_RESIDUAL`;
- no `VORONOI_STATIC_MESH_DO_DOMAIN_DECOMPOSITION`.

The controlled two-level test uses `RD_HIERARCHICAL_TEST_PATTERN`, which makes
the vertices with `x < BoxSize/2` one timebin finer than the fresh CFL candidate.
This flag is testing apparatus, not a proposed production bin criterion.

The prototype deliberately does not enable LDA/F1, beta variants, gamma,
Galerkin mass, moving mesh, runtime domain decomposition, or a new rank API.

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
| `src/hydro/residual_distribution_solver.c` | due-triangle classification, vertex-star reduction, half-ledger updates, full predictor assembly, stage-state selection, assertions and diagnostics |
| `src/main/allvars.h`, `src/mesh/mesh.h` | persistent/local and exchanged `RD_StarTimeBin`, `RD_PredictorEnd` |
| `src/mesh/voronoi/voronoi_exchange.c` | exchange star bin, predictor endpoint, and existing `RD_dU` |
| `src/time_integration/timestep.c` | optional controlled 2:1 test pattern derived from the fresh CFL candidate |
| `defines_extra`, `Template-Config.sh` | legal and documented switches |
| `examples/yee_2d/Config_RD_RK2_N_{INTERNAL,HIER_EQUAL,HIER_2LEVEL}.sh` | reference, equal-bin, and two-level test configurations |

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

## 8. Interpretation

The conservation concern is resolved for this construction: an inactive
vertex can safely accept residuals in its conserved ledger, exactly as an
inactive FV cell accepts flux, provided each globally owned triangle is
evaluated once when due and primitive recovery waits for the vertex endpoint.
There is no need to reinterpret RD as pairwise face-flux exchange.

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
5. Only after the time-state issue is resolved, extend beyond N/lumped and test
   restarts, arbitrary multi-level ratios, runtime domain decomposition, and
   moving meshes.

The present prototype should be retained as the conservative baseline and as a
diagnostic control for any higher-order interface construction.
