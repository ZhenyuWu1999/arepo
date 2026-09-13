# Phase 2 review: equal-step production hook for an explicit CR-inspired transfer

Date: 2026-09-11. Read-only audit of the production C path; this note is the
only new file written for this review. Source line numbers below refer to the
pre-phase-2 version inspected. Proposed implementation belongs to root.

## Decision and timing

The exact-patch hook can support a sound restricted equal-step experiment.
The operation must be explicitly described as a same-time representation
transfer at the OLD physical time t_n:

```
actual old triangulation at x(t_n)
    -> current connectivity pulled back to the same x(t_n)
    -> ordinary equal-step ALE evolution of that connectivity to t_(n+1).
```

It is not an instantaneous physical-time sequence of the actual Delaunay
flips, and it does not reconstruct their event order. This composition is an
acceptable controlled experiment provided every pulled-back new triangle is
valid, which `rd_ale_prepare_step` already checks at lines 2483–2487.

The available insertion point is within `rd_ale_exact_patch_diagnostic`, after
all geometry/identity audits and before freeing `changed`, `changed_parent`,
`root_to_exact`, `id_map`, and exact old/new patch masses (currently lines
2077–2089). Critically, its existing `integrity_fail` abort is currently AFTER
those frees at 2091: the new branch must check failure BEFORE any mutation.
After a successful new operator, `rd_ale_apply_topology_repair` must free its
support scratch and return immediately. It must not also apply the old support
correction at 2264–2338. The no-old-snapshot case must be a hard unsupported
case for the new operator, not a silent fallback to the original correction.

## What is actually retained

`rd_ale_topology_capture_old_mesh` (1610–1636), called in `run.c:263–268`
before the old mesh is freed, retains sorted three-ParticleID keys and positive
area/3. These records do not retain orientation, coordinates, periodic shifts,
or fluid states. Duplicate ID-only physical keys are already rejected.

At the new mesh, the exact diagnostic constructs the second sorted key/area
list from the new connectivity at pulled-back OLD coordinates (1764–1769).
The symmetric difference marks removed records with side -1 and inserted
records with side +1. Changed triangles are grouped by shared edges using the
union of old and new changed sets (1840–1843). This is better support than
joining every nonzero-dm node through the full current mesh.

The fresh complete common-time state is available as

```
Uold_i = particle_Q_i / SphP[i].DualArea
```

in `set->ale_uold` (2431–2445), before any predictor. Its old physical total
is saved in `set->ale_old_total`. The target OLD-time mass is
`set->ale_pullback_area`; neither the endpoint area nor the temporary Arpaia
or Campoli divisor is the target mass for this representation transfer.

Coordinates can be reconstructed as `P.Pos - ale_dt * VelVertex` (the existing
diagnostic does so at1972–1986), with an explicit consistent periodic chart.
Sorted IDs must then be reoriented CCW from those coordinates. Verify each
reconstructed absolute area against the stored old/new area, and verify the
sum of old incident contributions against the original full masses before
using the geometry. A label/area list alone is insufficient for signed
semi-edge sweeps.

## General changed components and their limits

A general component need not be a convex four-node cavity. A common homothety
`x_i(s)=c+(1-s)(x_i-c)` scales every triangle's signed area by `(1-s)^2`,
regardless of polygon convexity. Old triangles collapse and new triangles
expand, all with the same vertex paths in a component. Internal oriented
semi-edges cancel; matching external old/new boundary chains cancel on the
round trip. Therefore the algebraic LF record construction extends to more
than two old and two new triangles if these gates are satisfied:

1. Both oriented triangle sets are genuine positive partitions in one chart.
2. Their oriented boundary-edge chains agree, including any hole boundaries.
3. Every node's sum of old/new signed swept coefficients is zero.
4. Element summed swept coefficients equal signed element area changes.
5. The assembled nodal mass delta matches the exact old/new patch masses.
6. The assembled operator satisfies column sums zero and `L 1 = -dm`, with
   the signs needed for its explicit positive low update.

This uses a deliberately chosen direct component path. It is not the
historical sequence of elementary flips and need not give the same dissipation
or high-order transfer as that sequence. The old geometry tests already show
that discarding intermediate records changes the chosen path. That distinction
must remain visible in the experiment description.

The common centroid need not lie in every triangle. The full-mass explicit
operator never marches the fluid through zero-area triangles; the collapsed
geometry supplies signed coefficients. It would be unjustified to infer from
this algebra that the patch and all its unchanged exterior form a valid
physical tessellation throughout the fictitious collapse.

The ID-only snapshot cannot handle a component winding around the periodic
box or an ambiguous embedding. A first diagnostic should reject such cases.
A conservative sufficient restriction is a small contractible component with
one consistent chart, all edge embeddings agreeing with the expected local
periodic geometry, and all reconstructed triangle areas matching records.
Independent nearest-image wrapping around one anchor is not a general chart
algorithm. A large/ambiguous case should fail with its IDs and geometry; do not
quietly substitute a different remap.

## Shared vertices and sequential full masses

Edge-disconnected exact components can share a vertex. They then share a fluid
DoF even though they do not share triangles. Execute them in a deterministic
sequence. Initialize a scratch full mass `g_i = SphP[i].DualArea` and extensive
state `q_i = g_i * ale_uold_i`. For each component p:

```
(q_patch, g_patch) -> CR transfer with dm_p
write updated q and g for all its nodes
```

The next component must read those updated full masses AND updated states.
After all components, require `g == ale_pullback_area` to roundoff and set
`ale_uold = q/g`. Each intermediate full mass is the sum over a valid hybrid
of the processed new patches, unprocessed old patches, and unchanged exterior.
Do not use original `g`, final global pullback `g`, or independently accumulated
intensive corrections for each shared-vertex component.

Changed components must not be skipped merely because their individual or net
nodal dm is zero. Signed records may define a nontrivial transfer even when
endpoint nodal masses cancel. The new branch should be reached before the
old support `patch_count == 0` return (2189). Record the new path and its
artificial diffusion rather than attributing every change to mass correction.

## Essential stage-state consistency finding

The current support repair changes `set->ale_uold` but does not visibly refresh
all primitive fields before the first spatial residual. `rd_ale_prepare_step`
writes the remapped U into Q at2598, and `rd_rk2_save_stage0` saves Q/DualArea
at3425. However, the predictor's vertex state is read from SphP.Density,
SphP.Pressure and P.Vel at3923–3927; Csnd is read at3987. Merely writing the
new `ale_uold` therefore mixes remapped temporal state with stale spatial
stage-0 state.

For the new experimental branch restore density, velocity, pressure, Utherm,
and Csnd consistently from the transferred conservative U before predictor
assembly. Keep the selected VelVertex unchanged, since the mesh has already
moved along that trajectory. The existing `rd_aposteriori_restore_trial`
(3253–3278) provides a suitable field-by-field pattern. Its macro itself is
B-only; do not enable it merely to access the helper. Avoid the generic
primitive update if it may inject an energy floor or mutate the conserved
state. A debug assertion should compare the stage-0 primitive reconstruction
against `RD_Ustage0` to catch this exact mismatch.

The physical timestep was selected before remapping. A positive representation
transfer can alter Euler wave speeds and does not prove the old dt still meets
the physical-step CFL. Use a conservative Courant factor initially and record
`RD-CFL`'s post-remap stage-0 `rd_midpoint_limit/selected_dt`; an excessive
value of selected dt needs rejection or a separately designed step retry.
This is distinct from the pure-geometry substep CFL of the remap.

## Guards and conservation measurements

For the first actual-hydro campaign use a NEW opt-in flag, requiring
`RD_ALE_EXACT_PATCH_DIAGNOSTIC`, `RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC`,
`RD_ALE_EQUALSTEP`, `FORCE_EQUAL_TIMESTEPS`, `RD_RK2_TOTAL_RESIDUAL`,
`N_SCHEME`, and initially `RD_ALE_CAMPOLI_MASS`. Retain one-rank,
periodic-2D, no-gravity, no-comoving, no-refinement restrictions. Restart without
the old exact snapshot is unsupported. The existing equal-step guards already
exclude hierarchy. Use contour residual plus element comoving frame, matching
the preceding ALE reference; do not simultaneously change spatial solvers.

Measure four totals before transfer, after transfer, and after the physical
corrector/endpoint commit. The transfer target is
`sum_i pullback_area_i * ale_uold_i == ale_old_total`. The temporary
`sum_i divisor_i * ale_uold_i` immediately after prepare need not equal it:
that storage includes the physical ALE geometric term. Global physical
conservation belongs at the final endpoint after the RK step.

Keep geometry errors, raw uncorrected representation jump, limited fraction,
minimum transfer density/pressure, transfer correction norm, patch sizes, and
physical-step drift separate. A positive transfer alone proves neither the N
Euler predictor nor the whole ALE step positive. Campoli isolates this from
the known independent current Arpaia divisor issue.

## Two small existing hydro tests

1. **Yee isentropic vortex, deterministic jittered 32x32 points, box 10,
   gamma1.4, final t=0.2 then t=1 if healthy.** Use
   `examples/yee_2d/Config_RD_ALE_N_CAMPOLI_equalstep_ref.sh` as the physical
   reference and `examples/yee_2d/param.txt` as the parameter template; add
   the topology diagnostics/new operator and the existing ALE CFL option.
   Deterministic state/point formulas are in
   `examples/gresho_2d/create_mmrd_ics.py` (`yee_state` and the Yee generation
   block). This avoids the unseeded random ring angles in the other create.py.
   Compare weighted density/velocity/pressure error against the analytic
   vortex at current generator positions, conservation, and transfer-induced
   smooth-field diffusion. At least one nonzero changed-component count is
   required for a topology test; a no-flip run is only a degeneration control.

2. **Smoothed KH, jittered 32x32 smoke then 64x64, box1, gamma1.4, t=0.2.**
   `kh_state` in `examples/gresho_2d/create_mmrd_ics.py` supplies the existing
   tanh-width0.025, density1-to2, vx=-0.5-to0.5, pressure2.5 family.
   Use `examples/gresho_2d/Config_KH_N_con_cm_campoli_release.sh` as the
   physics baseline and the `param_KH_N_glass48_toporepair_t02.txt` template
   with explicit NEW local IC/output paths. The old template's /home/zwu
   inputs are cluster paths and should not be used on the Mac. Report
   conservation, pressure/density extrema, transverse kinetic-energy change,
   transfer limiting/correction statistics, and matched-time field differences.
   Its t=0.2 result is a robustness/topology test, not a developed-KH benchmark.

The generic `write_ic` helper uses the module's default GAMMA=5/3; the existing
Yee/shock blocks correctly write1.4 separately. A small custom wrapper must
explicitly use1.4 in InternalEnergy, not blindly call the default writer.
Use3–5 snapshots. First compare against no-repair and old support-repair
controls with the same IC/config except the transfer mode; strong nonlinear
trajectory divergence is not by itself evidence of an erroneous transfer.

Use the local native Makefile `SYSTYPE=LocalMac`, separate BUILD_DIR and EXEC,
Homebrew MPI/HDF5/OpenBLAS, and `OPENBLAS_NUM_THREADS=1`; start at one rank
(the only supported equal-step topology setting). Python with numpy/scipy/h5py
is `/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python`. The user has authorized
local simulations; this audit ran no fluid simulation or build.

## Correction to the earlier RK2 warning

`run.c:233–236` excludes RD_ALE_HIERARCHICAL from the old-mesh predictor call.
`run.c:352–357` executes its predictor and corrector consecutively after the new
mesh rebuild. Therefore the warning about a coarse RK interval's previously
committed opening half applies to the static split-call hierarchy. It must not
be presented as an unavoidable prepayment in the current concentrated moving
hierarchy. The present phase-2 hook is equal-step and neither integration path
is being changed by this review.

## Review of root's first guarded C implementation

The first `src/hydro/rd_cr_topology.h` version and solver hooks were reviewed
read-only after the preceding recommendations. The hook now checks
`integrity_fail` before transfer, rejects missing old snapshots, returns before
the old support correction, maintains sequential full masses/states, and
restores the first-stage primitive fields. Those changes address the principal
integration issues identified above.

The signed coefficient implementation is correct for its chosen homothety.
For an oriented edge i->j and collapse point c, each half-edge has swept area
`side * cross(x_i-c,x_j-c)/4`, with side -1 for old contraction and +1 for new
expansion. Assigning this to both edge endpoints yields sum(nu)=side*A for
each triangle. For the unit-square center-collapse it reproduces the previously
independent coefficients, including old triangle012's `[-1/8,-1/4,-1/8]`.

The graph-minimal choice `alpha=max(0,-min_j nu_j)` makes off-diagonal entries
of each local `L_ij=-nu_j/3+alpha*(delta_ij-1/3)` nonpositive. A local record's
diagonal can be negative, which is not itself a defect: after assembly of the
complete cavity, column sums zero and nonpositive off-diagonals imply
nonnegative global diagonals. The implementation assembles before subcycling,
which is essential. It would not be valid to infer the same timestep bound for
independent old/new record-by-record fluid updates.

Row sums give `L 1=-dm`; column sums vanish if the complete per-node signed
sweeps cancel. With `g(s)=g0+s*dm`, the update

```
Q_next = [diag(g(s)) - ds L] diag(g(s))^-1 Q
```

has nonnegative entries under the assembled diagonal CFL, and its intensive
rows sum to1 after division by `g(s+ds)`. Thus the pure geometry low update is
conservative, uniform-state preserving, and a convex combination of Euler
states. Root's adaptive ds=0.9*min(g_i/L_ii) follows this argument.

The high state `Uhigh_i=Uold_i-(sum_j dm_j Uold_j)/sum_j gnew_j` is the prior
full-mass-weight conservative transfer. One common theta over the entire
component and all four conserved components preserves total conservation.
Bisection for density/internal-energy admissibility uses the convex Euler
admissible set. Mode3 adds a density-range bound only; it does not constrain
pressure, velocity or entropy. The low endpoint supplies an admissible theta0.
After each component, the next component correctly reads updated `ale_uold`
and updated full mass, including shared vertices.

Remaining recommendations for this implementation:

- Add the explicit oriented boundary-chain check before transfer, as root has
  proposed. The nodal sweep/mass identities alone are weaker than verifying
  the intended old/new patch connectivity and periodic chart.
- Report and assert the GLOBAL transfer total using the actual target
  `set->ale_pullback_area * ale_uold` against `ale_old_total` after every
  component has committed. Per-patch conservation against reconstructed
  `mass` plus a final mass-match tolerance of1e-9 does not itself establish
  roundoff conservation using the actual masses later consumed by prepare.
  Typically discrepancies are merely roundoff, but this needs measurement.
- Retain the separate post-remap physical-CFL and physical-step admissibility
  checks. A positive remap does not repair an insufficient hydrodynamic dt.
- For mode3, an explicit final density-bound diagnostic would make its
  numerical claim reviewable; checking final Euler admissibility alone does
  not report the range condition. The exact low convexity ensures a feasible
  interval, while a finite tolerance should account for floating-point error.
- The new primitive restoration sets v_z=0 while the historical storage helper
  can preserve passive nonzero third momentum. Restrict this experiment's ICs
  to exactly zero third velocity/momentum, matching its four-component Euler
  algebra; do not imply a general2.5D transfer.

The geometry and new transfer modes remain experimental extensions, even
though the C code now uses production hydrodynamic timestepping. Agreement
with independently replayed event dumps plus physical endpoint conservation is
the appropriate next evidence. It would not by itself establish the paper's
implicit BDF method, hierarchical production integration, or spatial order.

## Resolution after the reviewed implementation

Root implemented the oriented boundary-chain gate, global actual-pullback-mass
total audit, and final mode-3 density-range check before the final native builds.
The runs retain physical CFL diagnostics and exactly zero initial third velocity.
Twenty equal-step Euler runs completed; 104 dumped events were independently
replayed. The native components reached six nodes, while the sampled replay
events were all four-node components. The remaining Arpaia physical-total drift
reproduces log 3 section 10; matched Campoli runs reach roundoff conservation.
The separate stage-0 primitive refresh control isolates an additional existing
repair consistency issue. Results and qualifications are in [phase2_hydro.md](phase2_hydro.md).
