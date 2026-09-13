# First-order local nodal closure reference

This is a bounded scalar reference for the `test/colombo-re-explicit-hierarchy`
investigation. It tests physical-time coupling independently of the topology
operator. The transfer currently used is the existing full-patch convex low
map, not Colombo--Re's swept-geometry construction. No production C, Euler,
moving geometry, MPI, changing bins, or second-order result is claimed.

Reproduction:

```sh
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/audit_cr_local_closure.py
```

The development run's complete JSON is `/tmp/rd_cr_local_closure_full.json`;
the parent task can preserve it in its campaign directory. This agent wrote
only this note and `tests/rd/audit_cr_local_closure.py`.

## The difference from the earlier frozen-outflow proposal

Earlier event closure integrated the dying triangles and transferred full-patch
Q, but left inactive cavity U frozen until its original endpoint. That can
reduce a node's Q while leaving its subsequent old-U outflow unchanged.

The new reference actually ends the cavity vertices' current trace intervals:

1. At the requested flip time t, find the four cavity vertices P.
2. Integrate **every old triangle incident to any vertex in P** from its stored
   last-integrated time to t. Add the ordinary naturally due triangles to the
   same sweep, without integrating any triangle twice.
3. Recover U=Q/g for naturally active nodes and all nodes in P. All their
   incident triangles now end at t. Record t as the trace epoch of those nodes.
4. Apply the conservative positive cavity transfer; recover the four affected
   U values again using the new masses.
5. Delete the two old triangles only after their intervals end; create the two
   new triangles with birth=last=t. Untouched triangle timestamps are retained.

Other nodes can receive Q through step 2 but their U is not changed unless
they are naturally active. Their incident triangles outside the closure set
are not recursively flushed. Original bins and natural node endpoints are
unchanged. Early closure shortens the current trace interval, and the next
natural update closes the shorter remainder to the old scheduled endpoint.

The reference uses first-order scalar N increments over each triangle's actual
outstanding interval. It has no RK predictor, corrector, or frozen-until latch.
The persistent records are triangle `last`/`birth` and node `trace_epoch`.

## Why one star closure does not recurse in this reference

Before changing U_i, all triangles containing i have been integrated to the
same event. Consequently no later triangle interval can cross this change of
trace unnoticed. The script asserts `max(trace_epoch[triangle]) <= last[triangle]`
before every integration and verifies all incident triangles ended before each
natural or forced nodal refresh.

The boundary of the union of cavity-vertex stars contains only vertices whose
U was not forcibly changed: a boundary edge containing a changed cavity vertex
would have both incident triangles inside the star union. An outside triangle
can therefore retain its old interval and constant trace. Receiving Q does not
itself change that trace. This is why physical contributions reach 14 vertices
in the regular-grid example while only the four cavity vertices are refreshed.

At a natural dyadic nodal endpoint, every incident triangle's minimum vertex
period also divides that endpoint. Each incident triangle is therefore due,
even if an earlier event shortened its current actual interval. This maintains
the same trace condition without promoting additional nodes or altering bins.

For static linear advection, the scalar N residual has non-negative inflow
weights and outflow k_iT^+ U_i. Between two trace refreshes, topology cannot
change a triangle incident to i without triggering another closure of i. Thus
its coefficients remain fixed, and the cumulative outgoing coefficient is at
most `(t-trace_epoch_i) sum_T k_iT^+`. Since a refresh resets Q_i=g_i U_i and
the remaining time to the original own endpoint is at most the own step h_i,
the ordinary bound `h_i sum_T k_iT^+ <= g_i` is sufficient for the scalar
non-negative update. All inflow comes from non-negative traces. The positive
same-time remap restarts this argument with the new g and U.

This proof uses **scalar, static coefficients and first-order frozen traces**.
It does not turn Euler matrix-N splitting into scalar non-negative weights,
and it does not cover changing mesh velocities or the RK predictor history.
For prescribed old/new static triangulations the script bounds every unchanged
own step against both old and new nodal CFL bounds; the maximum is 0.95 in all
reported cases. Merely retaining an old CFL bound after arbitrary new geometry
would not be justified.

## Measurements

Thirty cases use a peak of 1 over background 0.01, a smooth positive field,
and a uniform field. They include fixed-connectivity and deliberately unsafe
controls, repeated flips, 4x4/8x8/16x16 vertex meshes, and 1:8 plus 1:1024
hierarchies. A second fine cavity vertex gives an additional 1:2:1024 case.

Matched 4x4, one flip at tick 1, coarse CFL=0.95:

| Strategy | Minimum trace U | Coarse-end total mass error | Crossed trace intervals |
|---|---:|---:|---:|
| Fixed old connectivity | 0.01 | 0 | 0 |
| Flush dying triangles; positive full-patch ledger map; keep coarse U frozen | -0.03427622768 | 0 | 0 |
| Close incident stars and refresh cavity U | 0.01 | 0 | 0 |
| Refresh cavity U but flush only dying triangles | 0.01 | 0.001554985207 | 10 |

The last control also attempts three nodal refreshes with incomplete incident
stars. It establishes that the extra closure is necessary; assigning a new
trace epoch without computing the owed contributions is not sufficient.
The first-order negative ledger control is distinct from the previous RK test,
whose minimum was -0.03443564406.

Across the 21 safe local-closure cases:

- Maximum common-endpoint total mass error: `2.45e-15`.
- Maximum virtually completed total mass error: `2.45e-15`.
- Maximum transfer-only total mass error: `2.23e-16`.
- Uniform-state error: `1.12e-16`.
- No crossed trace intervals, incomplete refreshed stars, orphan intervals,
  or pre-birth intervals. Birth/death counts match twice the flip count.
- All Q and U remain positive; initial scalar bounds are respected to roundoff.

On a regular-grid cavity every event refreshes four vertices. Its old star
union contains 16 triangles and 14 vertices; at a tick with one naturally fine
vertex, 10 triangles and three refreshed vertices are additional work. For a
16x16 grid this is 16 of 512 triangles. The count does not grow with bin depth.

The deep 8x8 case performs six flips at ticks 1, 3, 511, 1025, 1027, 1535.
Its 1:1024 variant integrates 11,572 triangles in total, including 63 forced
non-due integrations, or 4.414% of a global fine-step sweep. The 1:2:1024
variant uses 6.169%. These are logical triangle-update counts, not runtime
speedups; detecting cavities, storing history, or MPI communication is not
benchmarked. Repeated shallow tests perform sixteen flips within four coarse
cycles, including several flips before a coarse node's natural endpoint.

The completed-mass check evaluates outstanding first-order contributions as a
read-only diagnostic. It never commits those contributions or refreshes their
nodes, and those evaluations are not counted as physical triangle updates.

## Connection point for the geometry operator

`run(..., transfer_callback=callback)` accepts

```python
callback(q_patch, g_patch, x_patch, old_tris_local, new_tris_local)
```

The four q/g entries are full nodal quantities at the closure time, coordinates
use one consistent periodic image, and triangles use local indices 0..3. Return
the four new q values, optionally with JSON-compatible metadata as
`(q_new, metadata)`. The callback must conserve their sum. The driver recovers
the affected states and retains the physical closure/timestamp rules.

This keeps a later Colombo-inspired geometry operator separate from the
hierarchy question. The currently supported conclusion is that **complete
incident-star closure plus actual cavity-state refresh is a simpler successful
first-order scalar reference than a future-outflow reserve**. Whether it can
provide a practical moving Euler implementation remains the next question.

AREPO integration must give the early hydro-state refresh its own explicit
meaning. It cannot silently mark a particle globally active and thereby rerun
gravity/source updates, nor reuse an RK predictor formed over the old interval.
Those production scheduling issues are intentionally absent from this model.
