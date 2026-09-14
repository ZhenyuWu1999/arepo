# Bounded C interface and AREPO integration audit

Date: 2026-09-10. This note concerns the current P1 median-dual RD code, not
a native finite-volume alternative. No production `src/` file was changed.

## Result and scope

The explicit, same-time geometry operator now has a standalone C99 interface:

- `tests/rd/colombo_re_topology_kernel.c`
- `tests/rd/audit_cr_c_kernel.py`

It is a candidate numerical-kernel boundary, not an AREPO implementation or
a reproduction of Colombo--Re's implicit physical-time method. Geometry
records and their completeness checks remain in the independently developed
Python modules. The C kernel receives the assembled operator rather than
discovering flips or computing swept areas.

Run from the repository with:

```sh
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/audit_cr_c_kernel.py --samples 64
```

The audit compiles with `/usr/bin/cc`, C99, `-O2 -Wall -Wextra -Werror
-pedantic`, into an automatically removed temporary directory. It passed:

| Check | Measured result |
|---|---:|
| Random Euler inputs, two alpha rules and two geometric CFLs | 256 / 256 admissible |
| C versus Python maximum normalized state discrepancy | 4.35e-16 |
| Maximum relative conserved-sum discrepancy | 6.43e-16 |
| Maximum constant-field error | 1.55e-15 |
| Minimum tested one-substep convex coefficient | 1.31e-4 |
| Maximum substeps in those random cases | 11 |
| Invalid-input families rejected without output | 8 |

An independent DOP853 solution of `dQ/ds=-L Q/g(s)` verifies convergence to
the intended ODE rather than just agreement between two implementations:

| Geometric CFL | C substeps | Maximum error against ODE |
|---|---:|---:|
| 0.8 | 3 | 2.5488e-2 |
| 0.2 | 11 | 8.5018e-3 |
| 0.05 | 40 | 2.1444e-3 |
| 0.0125 | 159 | 5.3945e-4 |

This is first-order refinement in fictitious time. Reducing this error does
not remove the dissipation of the limiting LF homotopy ODE itself.

The C kernel also replaced the Python map through the existing callback of
`audit_cr_local_closure.py`: six scalar cases (depth 8 and 64, peak/uniform/
smooth data, mixed patch bins) passed. Their maximum common-completion and
macro-sync conserved-sum errors were 2.22e-16. No triangle interval crossed a
changed trace, preceded birth, or remained orphaned at death. The number of
triangle integrations was respectively 19.7% and 7.93% of evaluating the
whole mesh every fine step. These are work counts, not wall-clock speedups.
They validate a first-order scalar local-closure call boundary; they do not
validate moving Euler dynamics, current AREPO RK2, or MPI.

## Kernel contract

Input arrays refer to one complete same-time cavity, using one ordering of
its persistent vertex IDs:

\[
L,\quad g^->0,\quad\delta=g^+-g^-,\quad g^+>0,\quad Q^-.
\]

The required identities are `1^T L=0`, `L 1=-delta`, and nonpositive
off-diagonals. Every row of `Q` contains extensive conserved quantities;
`g` is the **full** nodal mass, including the unaffected exterior star. It is
neither one triangle's mass nor a temporarily rebased Arpaia divisor.

At each fictitious substep:

\[
A=\operatorname{diag}(g(s))-\Delta s L,\qquad
Q^{new}=A\operatorname{diag}(g(s))^{-1}Q,
\quad g^{new}=g(s)+\Delta s\delta.
\]

The diagonal CFL makes `A` nonnegative. Its row sums are `g_new`, giving a
convex update of intensive states, while its column sums equal `g(s)`, giving
extensive conservation. Therefore admissible Euler input stays admissible
in exact arithmetic, without a component-specific operation. The C audit
checks pressure separately. The kernel deliberately does not claim that an
arbitrary partial physical-time ledger is an admissible same-time input.

The text interface is bounded to 64 nodes and 8 components and checks finite
inputs, dimensions, positive endpoint masses, operator balance, and monotone
signs. It returns final `Q`, `g`, substep count, CFL, and coefficient/conservation
diagnostics. It has no persistent state. A production function should expose
caller-owned arrays and a status return, retaining the same numerical
contract, instead of using standard input/output and process exit.

## Exact current-source integration obstacles

Line numbers refer to the source inspected on 2026-09-10.

| Current location | Meaning for the proposed integration |
|---|---|
| `src/main/run.c:267` | Existing diagnostic old-mesh capture sits before `find_next_sync_point` and mesh destruction; use this lifecycle position to preserve a real RD topology/history store. |
| `src/main/run.c:280` | The old tessellation is freed. `DT` indices/pointers cannot identify persistent elements or retain dead-element data. |
| `src/main/run.c:309` | Domain decomposition can occur before the rebuilt mesh; persistent records must survive changed rank and local array index. |
| `src/main/run.c:329` | `create_mesh` constructs new connectivity. Same-time old/new cavity comparison belongs after construction, using retained old IDs and current coordinates. |
| `src/main/run.c:356` | Current moving hierarchy calls predictor then corrector on the new mesh. A topology transaction cannot be dropped between these stages without redefining their temporal states. |
| `src/hydro/residual_distribution_solver.c:1459` | Activity is inferred from the current minimum bin. The experiment needs a separate forced-closure mask as well as natural activity. |
| `src/hydro/residual_distribution_solver.c:2811` | Geometry uses one full current-bin interval. Replace this in the new path with each retained element's actual `[last_integrated,event]` interval. |
| `src/hydro/residual_distribution_solver.c:2901` | Existing keep-U ledger closure can change Q. Applying it again after the explicit topology map would double-count a basis change. |
| `src/hydro/residual_distribution_solver.c:3870` | Physical residual weights also use the full current-bin interval; fixing geometry alone leaves the orphan/pre-birth integration bug. |
| `src/hydro/residual_distribution_solver.c:3883` | Current code applies a half-weight for its two-call method. A first-order closure needs its full interval exactly once. |
| `src/hydro/residual_distribution_solver.c:5455` | The moving N corrector adds a mass-gap times `RD_dU` contribution. It is part of the current two-stage algebra, not part of the standalone first-order closure. |
| `src/hydro/residual_distribution_solver.c:5577` | All imported extensive contributions must have arrived before forming same-time patch states. |
| `src/hydro/update_primitive_variables.c:78` | The normal primitive loop visits natural active particles only. The four extra patch refreshes need an explicit list and common-time validity checks; changing their bins is unnecessary. |
| `src/hydro/update_primitive_variables.c:193` | RD primitive density uses `Q/DualArea`, confirming the required full physical-mass denominator. |

The current compile-time moving-hierarchy guard also selects the N/two-stage
configuration. A first-order experiment needs a clearly separate integration
path and guard; simply calling the existing predictor once gives the wrong
weights and leaves stale predictor/ledger meanings.

## Persistent state actually needed

1. **Per retained triangle:** canonical oriented vertex IDs plus relative
   periodic image shifts; birth epoch; last integrated integer time;
   physical/topology epoch; current owner; its frozen trace epochs; sufficient
   old geometry to evaluate its actual outstanding interval. Preserve dying
   elements until their final contribution has been committed. Retained
   elements keep their old timestamp; new elements start at the event.
2. **Per vertex:** physical extensive ledger `Q`; full geometric mass or a
   precisely defined geometric ledger; frozen intensive trace and its epoch;
   natural bin; explicit refresh flag; topology epoch. Existing `P.Mass`,
   `SphP.Momentum/Energy`, and `DualArea` cover some values, but current
   `RD_PredictorEnd` is not a trace-start or triangle-integration timestamp.
3. **Per event:** complete old/new cavity records in one periodic embedding,
   ordered geometry records, signed mass delta, closure set, canonical event
   ID, pending/committed state, and the deterministic owner. In a cluster,
   serialize overlapping transactions or build a complete combined cavity;
   an intermediate triangle can be born and die at one physical time.
4. **Mesh-motion history:** if a vertex velocity changes within an outstanding
   triangle interval, store its pieces or close every affected interval at
   that change. Current endpoint position and latest `VelVertex` alone cannot
   reconstruct a general piecewise trajectory. The existing scalar closure
   experiment has zero mesh velocity and proves no such moving-geometry rule.

`RD_Ustage0`, `RD_dU`, `RD_StarTimeBin`, and `RD_PredictorEnd` live at
`src/main/allvars.h:1356` and are ghosted through
`src/mesh/mesh.h:127` and `src/mesh/voronoi/voronoi_exchange.c:296,415`.
Changing the interpretation requires updating both exchange paths.

Particle-local additions migrate with the full SphP record
(`src/domain/domain_exchange.c:193,271`). Raw binary restart also writes the
whole SphP array (`src/io/restart.c:1201`), despite the nearby allvars comment
calling RK data excluded from snapshot/restart IO. A separate triangle/event
table will not be saved or migrated automatically. It needs explicit restart
serialization/versioning and owner reassignment, or an initial test guard
that only permits restart at a completely drained common synchronization.

## Local closure and stage/reset rules

For the **first-order** path, process an event as follows:

1. Identify four changed vertices and all old triangles incident to any of
   them. In the bounded square experiment this is 16 triangles, not merely
   the two dying triangles and not the whole mesh.
2. Finish those triangles' outstanding physical intervals once, with the old
   frozen traces. Apply contributions to every recipient, including exterior
   vertices whose own traces remain frozen. Finish geometry over the same
   actual intervals. Wait for all MPI imports if applicable.
3. Refresh only the patch vertices and naturally due vertices whose complete
   stars are closed. This gives the common-time inputs for the same-time
   geometry operator. A recipient of an extra residual is not automatically
   a trace-refresh target; this is why closure need not propagate globally.
4. Execute the explicit geometry map once. Set patch physical mass and Q to
   the returned values; refresh those traces; mark the topology event
   committed. Do not perform the existing keep-U topology compensation again.
5. Advance retained element timestamps, retire dead records, and assign new
   elements birth/last times equal to the event. Leave natural bins unchanged.
   Exchange changed traces and epochs before any residual that consumes them.

Current `rd_open_vertex_predictors` (`residual_distribution_solver.c:452`)
resets by natural synchronization and current star bin. It does not represent
this additional topology-driven trace epoch. In the first-order experimental
path, keep RK scratch out of the transaction entirely. If a later design
shares structs with RK2, invalidate the touched predictor epoch and clear
`RD_dU`, but only after all dependent contributions have been settled;
clearing a predictor while retaining an already-booked stage contribution is
unsafe. The current moving hierarchy executes predictor/corrector consecutively
at one event; do not attribute the static split-call path's possible outstanding
half-step automatically to that moving path.

The present RK2 path requires more than these resets. Its two quadrature
states, predictor validity interval, midpoint geometry, and mass-gap term
must belong to the same surviving element interval. At a topology event it
must either finish and restart an admissible local RK interval or define a
dense-output/subinterval integration that accounts for every previously
booked contribution. Frozen-trace first-order conservation does not prove
that this is a second-order method. Nor does scalar physical-flux positivity
plus same-time Euler geometry positivity prove moving Euler positivity.

## MPI scope and minimal next step

The same-time C kernel needs no MPI. A single owner can gather a complete
cavity, execute all fictitious substeps locally, and scatter one set of final
extensive increments. No MPI round trip per fictitious substep is necessary.

The difficult distributed boundary is the **physical interval closure**:
gather a complete old star, let each retained triangle owner integrate once,
deliver all increments, then authorize the patch owner to form common-time
states. `apply_FluxRD_list` (`residual_distribution_solver.c:5877`) already
transports extensive increments, but has no event key, interval coverage,
trace epoch, or exactly-once transaction semantics. Old owners cannot simply
be rediscovered from a new mesh. Repartitioning needs an explicit commit
boundary and ID-to-current-owner remapping.

The smallest meaningful next AREPO experiment is a one-rank, periodic 2D,
prescribed single-cavity **first-order** path with retained element IDs and
timestamps. First run with zero mesh velocity and a prescribed legal flip,
printing the precise 16-triangle closure and four-node refresh. Require the
C callback's scalar results to reproduce the Python control before adding
piecewise mesh motion or Euler physical residuals. Then separately enable
full moving geometry and Euler, measuring physical CFL and positivity.
Only after those gates should this new lifecycle be combined with current
Campoli RK2 and the existing MPI geometry prototype. This is a real local
redesign, but does not require abandoning hierarchical bins or immediately
replacing the entire hydrodynamics solver.
