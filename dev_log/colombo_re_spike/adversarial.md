# Independent adversarial audit of first-order local topology closure

Date: 2026-09-10. This audit independently extends the static scalar model;
it does not alter `audit_cr_local_closure.py`, either Colombo-inspired module,
or the C solver. Reproduction:

```
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/audit_cr_adversarial.py --samples 24
```

The output used below is `/tmp/rd_cr_adversarial.json`. The script prints all
cases, seeds and a deliberately invalid negative control. No conclusion here
requires RK2 accuracy, which this explicitly first-order model does not claim.

## What was challenged

The original closure driver alternates the diagonal in one fixed square. The
new independent driver allows every square of a periodic 6x6 grid to flip. It
uses random fixed dyadic node bins up to ratios 8, 16 and 32; random positive
scalar fields spanning `exp(-6)` to `exp(2)`; uniform controls; adjacent cavities;
repeated flips; multiple sequential flips at one fine tick; and cavities across
the periodic boundary. Events include natural macro endpoints and their
immediate neighbors. All flips are legal cocircular square diagonal swaps.
The periodic embedding is known analytically, rather than inferred from IDs.

The topology operator is the candidate `geometry_records` plus adaptive
`topological_remap`. The physical operator is the original static scalar
first-order N residual. The driver closes all triangles incident to each
four-node cavity, refreshes only those nodes, and preserves all exterior
frozen traces. Zero-length same-time closures are skipped; new triangles have
birth time equal to the event time. Same-time adjacent events execute
sequentially and therefore see the previous event's new state and geometry.
This is a valid extension model, not a claim that the original driver's API
already supports arbitrary cavities.

The physical timestep is 0.99 times the exact worst scalar nodal CFL over all
16 possible diagonal configurations in a node's four surrounding squares.
The finest timestep is this bound divided by the largest allowed bin. We track
the cumulative self-outflow coefficient of each frozen nodal trace and reset
that budget only when the node's state is refreshed, never when an unrelated
incident triangle is merely integrated.

## Results

All 24 valid cases passed, including 1,769 flips, 846 second-or-later flips at
the same tick, and 514 periodic-boundary cavities. There were no intervals
crossing a changed trace, unclosed dying-element intervals, prebirth
intervals, or node refreshes with incomplete stars.

| Quantity | Observed bound |
| --- | ---: |
| Common-time completed-mass error | 2.00e-15 |
| Macro synchronization mass error | 2.00e-15 |
| Same-time topology transfer mass error | 4.44e-16 |
| Uniform-state error | 8.88e-16 |
| Maximum spent scalar self-outflow fraction | 0.9900000000000002 |
| Minimum stored extensive scalar value | 5.61e-5 |
| Minimum refreshed scalar value | 2.51e-3 |
| Scalar range violations | 0 |
| Triangle work / global finest-step work | 0.623 to 0.896 |

These frequent events and randomly widespread fine bins are deliberately
unfavorable for a large speedup. The work count establishes that the driver
did not secretly integrate the entire grid on every fine step; it is not a
parallel performance measurement.

The invalid control closes only the dying triangles and then refreshes all
four cavity states. It produced 189 intervals crossing a trace change, 152
incomplete star refreshes, and a macro mass error of 8.46e-3, despite zero
orphan/prebirth intervals and individually conservative topology transfers.
Thus lifetime accounting alone is insufficient: a changed trace requires
closing every residual interval that used it.

## Why the local closure need not recursively wake the whole mesh

For a triangle T, retain its last integrated time l_T and a trace constant
since that time. A node may change its trace only after every incident triangle
has reached the current time. Closing those triangles changes their other
vertices' extensive ledgers, but does not require changing those other
vertices' traces. Consequently the four cavity nodes can obtain complete
common-time states while exterior receivers remain inactive. An adjacent
cavity can later close its own star; shared triangles already at that time
contribute zero additional interval. This argument is valid for the stated
piecewise-constant first-order traces.

The scalar N residual has the form

```
r_iT = k_iT^+ (u_i - u_in,T),    u_in,T >= 0 for positive nodal traces.
```

During one frozen trace epoch, the self-outflow coefficient is the sum of
`(t_end - t_start) k_iT^+` over committed pieces. Repeated forced triangle
closures partition this budget; they must not restart it. Before a topology
change affecting node i, its incident geometry and mass are fixed. The nodal
CFL makes the budget at most its mass, so stored Q stays nonnegative. A full
star refresh then starts a new budget; its next natural bin endpoint is no
farther away than the original bin length. The topology map supplies a
positive new common-time state and mass. This explains why the audit can
pass arbitrarily repeated local events without globally refining node bins.

## The conservation diagnostic must include outstanding intervals

The raw sum of stored partial ledgers is not a synchronized physical integral:
it moved by as much as 4.86e-2 in valid runs. The conserved common-time scalar
quantity is instead

```
I(t) = sum_i Q_i - sum_T (t-l_T) sum_{i in T} r_iT(current frozen traces).
```

This is an evaluation of pending contributions, not their commitment and not a
hidden finest-step fluid update. Its conservation has an event-by-event proof:

- Between state/topology events, the complete periodic mesh has sum_T r_T=0.
- Committing a triangle interval moves exactly that contribution from the
  pending term into Q.
- Refreshing a node cannot change a pending term, because all incident
  triangles have zero pending interval at that instant.
- The dying triangles have no pending lifetime, the newborn ones start with
  zero pending lifetime, and the topology transfer preserves sum(Q).

At a common macro endpoint all pending terms vanish. This proves the intended
first-order accounting identity, not raw-ledger conservation at every fine
event. Production diagnostics/restarts would have to preserve or reconstruct
this meaning explicitly. An alternative face-paired extensive formulation
could have a different stored-total contract; it is not implemented here.

## Remaining limits and design constraints

This audit found no counterexample to the stated first-order static scalar
local-closure construction. It materially narrows the earlier concern that
closing a cavity necessarily cascades into a global synchronization: it does
not do so in this model. That positive result is limited to fixed bins, static
geometry and compatible constant traces. A changing physical velocity, moving
mass, variable Euler wavespeeds, or a higher-order stage history needs its own
interval and positivity argument. Uniform GCL of the same-time topology map
alone does not supply that argument.

The candidate explicit geometry operator is a positive conservative transfer
constructed from Colombo-inspired records. Its full-mass homotopy is a new
explicit construction, not literal fluid evolution through their zero-area
collapse. No affine accuracy or flip/reverse reversibility is asserted here.

Fixed-grid diagonal flips need no triangle-image reconciliation beyond the
known square embedding. Arbitrary Delaunay cavities, vertex insertion/removal,
moving geometry, dynamic bins, MPI ownership/migration, and simultaneous
nonserialized overlapping patches remain untested. Arbitrary same-tick
parallel patches need either disjoint state support or deterministic conflict
resolution. A same-time event may safely skip an already closed triangle;
reintegrating a full bin interval would be incorrect.
