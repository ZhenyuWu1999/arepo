# AREPO-RD 3D moving-mesh development log

This is the shared, English-language record for 3D moving-mesh preparation,
implementation, reviews and experiments on the local Mac, Cuillin, COSMA and
other execution hosts. It is organized by development topic rather than host.

- Opened: 2026-10-11, at Zhenyu Wu's request.
- Date/time convention: Asia/Shanghai unless an entry states another time zone.
- Repository path: `dev_log/dev_log_3D_moving_mesh.md` on every host.
- Working rules: [AGENTS.md](../AGENTS.md).
- Project and Cuillin workflow: [context.md](context.md).
- Host references: [local Mac](context_localMac.md), [COSMA](context_cosma.md).
- Earlier 3D preparation: [log 3](RD_DEVELOPMENT_LOG_3_localMac.md), §§228–241.

Append entries with the date, author/model, execution host, source revision,
configuration, actual job/test status, evidence location and remaining work.
Distinguish plans, submitted/running jobs, completed runs and verified results.
Keep long derivations and campaign analyses in focused reports linked here.
Preserve earlier entries and authorship; add corrections with references to the
affected entry. When synchronizing concurrent work through Git, retain both
hosts' entries and evidence rather than overwriting one copy with the other.
Earlier logs retain their original numbering and text; they are not duplicated
or renumbered here. Host setup files continue to describe their own environments.

## Index

| Entry | Date | Subject | Execution host |
|---|---|---|---|
| 1 | 2026-10-11 | Current implementation, validated geometry evidence and Cuillin handoff | Local Mac; cluster work planned |
| 2 | 2026-10-14 | Cause of nonpositive interval volumes; high-precision audit and regularization controls | Local Mac |
| 3 | 2026-10-14 | AREPO paper/code CFL comparison and scope correction for the geometry diagnosis | Local Mac; offline kinematics |
| 4 | 2026-10-18 | Integrate the development checkpoint and start the dedicated 3D moving-mesh branch | Local Mac; Git operations |
| 5 | 2026-10-18 | Claude review of entries 1–4; face-connected change regions on archived first steps | Local Mac; offline analysis |
| 6 | 2026-10-18 | Progress review; independent face audit and multi-step controls capped at 2^-12 | Local Mac; offline and short native runs |
| 7 | 2026-10-18 | Low-resolution static 3D Gresho N/LDA physical check before moving development | Local Mac; native runs completed |
| 8 | 2026-10-18 | Static 3D Sedov failures separated into cold-solve and raw-pressure limits; user prioritizes the moving/hierarchy/MPI pipeline | Local Mac; four failed native attempts archived |
| 9 | 2026-10-18 | Morton Blob preparation and short static N/hierarchy/MPI checks | Local Mac; three short runs completed; 32³ IC only |
| 10 | 2026-10-19 | Local Blob runtime estimate from measured 16³ short checks | Local Mac; arithmetic extrapolation, no new run |
| 11 | 2026-10-19 | Recommend cluster campaigns and prepare a COSMA source handoff | Local Mac; documentation/publication, no cluster job |

## 1. 2026-10-11: current state and handoff to Cuillin

- **Author:** Codex (GPT-6), with Zhenyu Wu.
- **Execution host of the evidence below:** local Apple Silicon Mac.
- **Branch checked at this handoff:** `feature/ale-flip-conservation-hierarchy`.
- **Implementation checkpoint:** `57e1ae3` (native moving-tetra geometry diagnostic).
- **Mathematics checkpoint:** `90624a4` (moving-tetra Campoli/geometry oracle).

**Status:** M1 mathematics and M2 local diagnostic are complete within their
stated scopes. Native moving 3D RD is not implemented. Zhenyu intends to extend
testing on Cuillin; no cluster build, job submission or live cluster inspection
was performed while opening this log.

### 1.1 Implemented and validated foundations

Milestone labels follow Claude Code's
[3D moving-mesh plan](RD_3D_MOVING_MESH_PLAN_FOR_CODEX_20261011.md).
The user decisions below and current AGENTS.md supersede its earlier scaling
prerequisite and log destination.

| Component | Current evidence | Boundary |
|---|---|---|
| Static tetrahedral N/LDA | Native periodic, gas-only full meshes; equal steps and experimental frozen-dU hierarchy; small 1/2/4-rank gates | Does not establish moving geometry, moving hierarchy or moving MPI |
| Moving-tetra mathematics (M1) | Independent geometry identities and complete fixed-connectivity Campoli ledger model; five-component cavity-transfer models | Model/oracle evidence, not a native moving-RD fluid update |
| Native geometry diagnostic (M2) | Read-only standard moving Voronoi FV trajectories; periodic tetra registry, interval-volume and cavity statistics | Fresh, noncomoving gas-only runs; full mesh, equal adaptive steps, one rank |
| Moving N adapter (M3) | Not implemented | Controlled fixed-connectivity integration is the next solver milestone |
| Native 3D cavity transfer (M4) | Not implemented | Inversion, large-cavity and periodic winding policies remain open |
| Moving LDA, tetra HLLC-RD (M5/M6) | Not implemented | Shock robustness/positivity remain separate requirements |
| Moving interval hierarchy, MPI, lazy/restart | Not implemented | Static and 2D results do not validate these paths |

Static 3D details are in
[features and benchmarks](RD_3D_FEATURES_AND_BENCHMARKS_20261010.md) and
[examples/rd_3d](../examples/rd_3d/README.md). The final static feature campaign
contains 50 small 8³/16³ gates, including actual mixed bins and equal-bin
degeneration. Reduced SWIFT-family Sod/Gresho runs complete. Production cold
Sedov stops at the raw solve-compatibility audit and is unvalidated.
[Claude's review](RD_3D_EXTENSION_CLAUDE_REVIEW_20261010.md) identifies a scaling
problem in cold compatible systems; its independently scaled prototype later
encounters negative pressure. It is not a passed production shock benchmark.

**User decisions retained:** similarity rescaling is not a prerequisite for
moving-mesh preparation; production Euler/linear solves remain unscaled.
The 2D K-refactor trajectory-compatibility repair remains deferred. Keep the
current 2D arithmetic and explicit lazy-OFF baseline. No audit threshold,
primitive floor or default Config was changed to obtain these results.

### 1.2 M1: established geometry and ledger mathematics

See [moving geometry mathematics](RD_3D_MOVING_GEOMETRY_MATHEMATICS_20261011.md)
and historical log 3 §240. Key results are:

- Linear vertex trajectories give quadratic oriented face area vectors and
  cubic signed tetra volumes. Interval positivity requires endpoints and every
  real stationary point in the interval; old/mid/new probes alone are inadequate.
- Endpoint volume differences provide the ledger geometry. The element
  mesh-gradient/contour term requires exact time-mean face vectors, with the
  3D `1/3` factor; Campoli temporal mass uses `(V_old + V_new)/2`.
- The complete two-sweep periodic fixed-connectivity model conserves to
  round-off with exact mean vectors. The 27-node/162-tetra oracle gives
  conservation defect at most `1.322e-16`; its nonuniform midpoint-normal
  control gives `3.114e-9`.
- The independent moving-tetra/transfer oracle covers 300 moving tetrahedra,
  a hidden interval inversion, Galilean transport and 1026 five-component
  transfer cases, including 4-4 and larger cavities. It is part of `check_rd`.
- Full K is linear in the face vector, but spectral splitting and N/LDA
  distribution generally do not commute with time averaging. Mean-vector
  alpha is not a bound on the entire step's CFL coefficient. Frozen-stage
  identities do not prove exact nodal affine preservation of native RK2.

Local evidence: `../local_runs/rd_3d_moving_math_20261011_v3/`, relative to the
repository root on the Mac. This path is an evidence locator, not proof that
the archive is already present on Cuillin.

### 1.3 M2: real native trajectories and geometry hazards

See [native geometry diagnostic report](RD_3D_MOVING_GEOMETRY_DIAGNOSTIC_20261011.md)
and historical log 3 §241. Relevant implementation and reproduction entries:

- `src/mesh/rd_simplex_registry.{c,h}`: pure geometry, oriented periodic keys,
  cubic interval checks and connected change cavities.
- `src/mesh/rd_3d_geometry_diagnostics.c`: read-only native FV hooks.
- [Config_FV_geometry.sh](../examples/rd_3d/Config_FV_geometry.sh): explicit
  `RD_3D_GEOMETRY_DIAGNOSTICS`; this is standard FV, not moving RD.
- [run_3d_geometry_pilot.py](../tests/rd/run_3d_geometry_pilot.py): freeze,
  prepare, build, run and analyze the local pilot.
- [analyse_3d_geometry_pilot.py](../tests/rd/analyse_3d_geometry_pilot.py):
  independent periodic Delaunay/graph checks and scientific figures.
- [test_simplex_registry.py](../tests/rd/test_simplex_registry.py): standalone
  C-kernel checks, included in `make check_rd`.

The local pilot uses 4096 generators, a periodic unit cube, gamma=5/3,
standard quasi-Lagrangian velocities and CM/soundspeed/face-angle regularization
(`CellShapingSpeed=.5`, `CellMaxAngleFactor=2.25`). It compares CFL=.1/.3 on
initially uniform gas at rest on random points, smooth oblique advection,
z-invariant Gresho, KH-like shear and very short FV Sedov. There are ten physics
diagnostics totaling 134 steps and 8274 connected change cavities, plus an
injection probe and three diagnostic-OFF controls. Durations, actual timesteps,
seed/coordinates and injection normalization are specified in the report;
these are short functional diagnostics, not convergence or scaling campaigns.

| Initial condition | End time | New-tetra pullback inversions, CFL .1 / .3 | Largest cavity vertices, CFL .1 / .3 |
|---|---:|---:|---:|
| Uniform at rest, random points | .015625 | 4 / 15 | 110 / 1599 |
| Smooth oblique advection | .015625 | 0 / 0 | 0 / 0 |
| Gresho | .03125 | 0 / 0 | 44 / 106 |
| KH-like shear | .03125 | 0 / 1 | 34 / 488 |
| FV Sedov | .001 | 0 / 0 | 9 / 13 |

Counts are **element-interval occurrences**, not necessarily distinct tetrahedra.
Connected change cavities can combine several flips sharing vertices; they are
not the individual operations of AREPO's insertion/retriangulation algorithm.

The main hazards and geometry checks are:

1. There are 20 new-tetra pullback inversions, 23 old-connectivity interval
   inversions and three common-key orientation reversals. CFL=.1 still gives
   inversions in the random case. The worst measured `V_old/V_new` is `-6.23813`.
2. Five new-element Campoli temporal volumes are nonpositive, while every
   observed nodal temporal mass is positive. A nodal positivity check cannot
   replace an element-interval geometry acceptance policy.
3. The largest cavity has 1599/4096 vertices (39.038%). Five cavities have
   periodic winding cycles: two in random CFL=.3 and three in shear CFL=.3.
   They have no single coherent Euclidean unfolding; ordinary affine
   first-moment correction cannot simply be assumed for them.
4. Exact mean face vectors differ from midpoint vectors by up to `.00377676`
   relative to the largest old/mid/new face area. This is a geometry correction,
   not an estimate of fluid error. Independent Gauss swept-face GCL defect is
   at most `5.971e-17`, versus `1.436e-5` for midpoint sweep, with the report's
   stated normalization.
5. Signed box coverage defect is at most `1.044e-14`; cavity volume and
   non-winding first-moment defects are at most `2.825e-15` / `2.903e-15`.
   These signed-chain identities can hold despite inversion and do not prove
   positive geometry or positive fluid states.

The sliver diagnostic is `q=V/(sum face area)^(3/2)`, whose regular-tetra value
is `.05170027`; do not reuse the inconsistent `.0068` value from the earlier
plan. New-endpoint minimum q is `3.48944e-5`. No uncertain or hidden-between-
probes inversion was observed in these native pilots, but the manufactured
hidden-inversion oracle still demonstrates why full cubic interval checks are
needed. Near-zero classification is a diagnostic error policy, not a certified
exact orientation predicate.

### 1.4 Validation, provenance and retained failures

Local final archive: `../local_runs/rd_3d_geometry_20261011_v4/`.
Its native source was frozen from `90624a4` plus the diagnostic changes later
committed as `57e1ae3`; `final_source_audit.json` confirms the native source
matches that checkpoint. Final analysis scripts and hashes are recorded
separately because enriched event classification followed the build freeze.
The bundle preserves source/Config/header/binary hashes, linkage, inputs,
parameters, logs, run status and geometry records. The archive is not part of
the Git checkout and has not been transferred to Cuillin in this handoff.

- Full frozen `make check_rd` passes. The added registry suite checks 800
  intervals and 35 cavity models against independent calculations.
- All 43 invalid old/new chain events are independently rechecked using NumPy
  determinant coefficients and polynomial roots.
- Random/advection first-step old/new complete periodic key sets match an
  independent 27-image SciPy Delaunay reconstruction exactly. Independent
  graph traversal checks cavity sizes and winding on four pilot cases.
- All 14 final native attempts complete. Random/Gresho/Sedov CFL=.3 ON/OFF
  controls have byte-identical particle fields after ID sorting in all three
  snapshots and all nine particle datasets. This tests non-invasiveness on
  those three trajectories.
- 2D LDA/B Yee48 replays, dt=1/256 through 256 steps to t=1, match the five
  archived reference snapshots and all eleven particle datasets byte for byte.
  This is not a rerun of the entire 2D N/HLLC/hierarchy campaign.

Earlier diagnostic attempts remain archived: v1 fails macro-guard registration,
v2 fails compilation because of a `Nodes` symbol collision, and v3 completes
FV runs but fails coverage because deleted tetra vertex slots were counted.
The v4 filter uses AREPO's actual `DT[t].t[0]` deletion marker and checks each
opening box coverage. The geometry threshold was not loosened. These are
diagnostic setup/implementation failures; v3 geometry statistics are excluded
from physical conclusions. Entry registry drafts remain preserved separately.

### 1.5 Cuillin handoff: pending work

Zhenyu intends to continue testing on Cuillin. The following is a handoff plan,
not a record of completed cluster validation:

1. **Check the actual Cuillin checkout and environment.** Preserve existing
   changes, confirm branch/revision and use that host's `Makefile.systype`.
   The documented Cuillin path/workflow is in [context.md](context.md); its
   scheduler/module details must be checked on the host. Compile and run on
   compute nodes. Use the Cuillin workflow rather than LocalMac or COSMA settings.
2. **Adapt or replace the Mac campaign driver before Linux builds.** The
   current driver imports a helper that calls `otool`; its source-freeze step
   also copies the caller's ignored `Makefile.systype`. A Cuillin build needs
   Linux linkage/provenance (`ldd`) and the correct host configuration. Existing
   `build_case.sh`/Slurm wrappers are the Linux artifact route, but a 3D geometry
   campaign integration with them has not yet been validated.
3. **Begin with a one-rank parity pilot.** Run `check_rd` with the intended
   compute-node compiler/Python environment, then the small diagnostic and
   corresponding OFF controls. Explicitly use `--ntasks=1`; the existing
   `run_case.sbatch` default is four ranks, whereas this diagnostic supports one.
   Keep OMP and the selected BLAS backend at one thread. Record compiler,
   MPI/HDF5/BLAS, Python versions, generated headers, binary/linkage hashes,
   job IDs, actual timesteps and final status in the next shared-log entry.
4. **Fix comparison provenance before extending the campaign.** Reuse frozen
   IC/parameter definitions where comparing with the Mac, and state whether
   Sedov injection reuses the archived IC or is recomputed from a new native
   Voronoi-volume probe. Its FV injection is not median-dual normalization.
   ARM/Clang versus Linux/compiler/backend runs need explicit tolerances;
   do not require cross-platform byte equality or silently relabel changed ICs.
   The first-pair binary is a native ABI artifact; check byte order/layout on
   the reader's host rather than assuming an interchangeable restart format.
5. **Extend geometry measurements once the Linux pilot is verified.** Larger
   resolutions, more seeds/CFL values and longer durations belong on the cluster.
   Preserve full interval minima, element and nodal temporal masses, cavity
   size/touched fractions, winding and sliver distributions. Increasing rank
   count is not a supported way to scale this one-rank diagnostic.
6. **Keep solver design decisions separate from measurement.** Determine how
   to accept/reject an element interval and how to handle large/winding cavities
   before moving-RD reconnection transfer. Do not use absolute volumes, skip
   inverted elements or impose an arbitrary cavity cap as an unreviewed repair.
   A controlled fixed-connectivity Campoli moving-N adapter is the next native
   solver milestone; native 3D transfer, LDA/HLLC, moving hierarchy/MPI and lazy
   support follow their own implementation and validation gates.

No thesis, standalone solver, production scaling or cluster job state is changed
by opening this log. Future 3D moving-mesh entries, whether measurements, code
changes or reviews, belong here; earlier reports remain linked source evidence.

## 2. 2026-10-14: cause of nonpositive 3D volumes

- **Author:** Codex (GPT-6), with Zhenyu Wu.
- **Execution host:** local Apple Silicon Mac; one rank, OMP/BLAS threads=1.
- **Branch / analysis starting revision:** `feature/ale-flip-conservation-hierarchy` / `cb504ac`.
- **Native source:** frozen `57e1ae3` diagnostic artifact; reused without rebuilding.
- **Request:** investigate the cause before advancing the moving 3D solver.
- **Status:** offline audit and three small native controls completed. No cluster
  job submitted or production solver modification made.

Full results: [cause report](RD_3D_NONPOSITIVE_VOLUME_CAUSE_20261014.md).
Reproduction: [diagnostic audit script](../tests/rd/diagnose_3d_nonpositive_volumes.py).

The failures are real orientation crossings of thin tetrahedral vertex tuples
under finite linear drift, seen when old connectivity is carried forward or
new connectivity is pulled back. The diagnostic field `old_endpoint_negative`
means the **old** tetra at the **closing** time; it does not mean a negative
opening native tetrahedron. These measurements do not establish negative
native Voronoi cell volumes.

All 43 side-specific invalid records pass an independent 60-digit determinant
audit and have one sign-changing root within their step. Their negative minima
are at least `6.11679e8` times the diagnostic error estimate. Three old/new
orientation-reversal pairs make 40 distinct case/step/ID-tuple combinations;
these are not counts of individual flips. All 17 invalid records in the saved
first full pairs belong to changed or orientation-reversed connectivity.
There is no hidden-between-probes inversion in this native pilot, while the
manufactured hidden-inversion oracle remains relevant.

The earliest random-case old tetra has minimum altitude `5.67933e-5`, versus
Voronoi radii `.0329531`--`.0476321`. It crosses zero at `t=.000320812720`:
before either actual first step (`.0009765625` at CFL=.1, `.001953125` at .3)
ends. The source CFL/regularization criteria use Voronoi geometry/signal scales,
not this tetrahedron's altitude or cubic zero time.

| Fresh random-gas control, end t=.015625 | Steps | Old/new invalid records |
|---|---:|---:|
| CellShapingSpeed=.5, CFL=.3 | 8 | 16 / 15 |
| CellShapingSpeed=0, CFL=.3 | 8 | 0 / 0 |
| CellShapingSpeed=0, CFL=.1 | 16 | 0 / 0 |

The .5/.3 replay is byte-identical to the original in all nine particle datasets
and three snapshots. The .3 OFF control has the same actual timestep sequence;
the .1 OFF control has a different later adaptive schedule. Both OFF controls
have no reconnection over this short run, though their evolved mesh velocities
are small rather than exactly zero. This isolates regularization as the dominant
driver for this random-gas pilot. The shear event at CFL=.3, step 8, has zero
regularization correction and still crosses orientation; removing regularization
is therefore not a validated general remedy.

For the worst new tetra, `V_old/V_new=-6.23813080`, so its Campoli endpoint mean
is `-2.90095125e-8`. The five nonpositive new-element temporal volumes follow
from negative pullbacks; they are not Euler-scaling or Campoli arithmetic
failures. Positive nodal masses and signed coverage can mask negative element
contributions through summation/cancellation. Native moving RD is still absent.

Evidence is local: native controls in
`../local_runs/rd_3d_nonpositive_audit_20261014_v1/`; final offline audit in
`../local_runs/rd_3d_nonpositive_audit_20261014_v3/`, including snapshot-volume
and first-velocity checks. Earlier offline versions remain archived; the three
native controls were not repeated. Original M2 data remain untouched.
The report includes a version-controlled PNG/PDF of representative volume roots.

Next design boundary: distinguish old-connectivity geometry limits from the
acceptance/transfer policy for newly connected tetrahedra whose pullbacks cross
zero. No absolute-volume replacement, mass clipping, velocity/timestep change
or assertion relaxation has been introduced. M3 and Cuillin campaign adaptation
remain pending.

## 3. 2026-10-14: CFL reference audit and correction to the diagnosis

- **Author:** Codex (GPT-6), with Zhenyu Wu.
- **Execution host / starting revision:** local Mac / `a93fb87`.
- **Request:** check the AREPO paper's CFL condition and distinguish the
  Voronoi FV and Delaunay-based RD geometry requirements.
- **Status:** publication/source review and six first-step kinematic mesh
  comparisons completed. No new native fluid run, build or cluster job.
- **Evidence:** `../local_runs/rd_3d_cfl_reference_20261014_v1/`;
  [reproducer](../tests/rd/audit_3d_cfl_reference.py).

**Correction to entry 2's interpretation:** M2 uses standard FV timestep
selection, not RD's own spectral condition. Its invalid-volume records prove
hazards on those FV trajectories; they do **not** prove that a moving-RD
scheme obeying its own stability/geometry bounds would reproduce those events.
The actual geometric sign changes and regularization-control results in entry 2
remain valid. More suitable first-step limits remove the observed first-step
inversions in a frozen-velocity oracle.

### Paper versus public-code timestep

[Springel (2010), §§7.1--7.2](https://arxiv.org/html/0901.4107#S7) gives the
local moving-frame condition (126),
`dt_i = C_CFL R_i / (c_i + |u_i-w_i|)`, and the signal-travel extension
(128)--(130), `dt_i = C_CFL min(local_i, min_j r_ij/vsig_ij)`.
The paper distinguishes the global minimum in (127) from individual-step
selection. The stricter signal extension here is a comparison, not a claim
that equation (126) is an invalid global FV prescription.

The public source used by M2 has `TREE_BASED_TIMESTEPS`. It initializes the
local moving-frame bound, then uses **`r_ij + R_i`** in the pair travel time,
with matching radius terms in the tree-opening checks. That radius addition
is intentional in the source comment to avoid very short steps for nearby
generators; it is not the literal distance in paper (130). It must be identified
before describing a run as a test of the strict published signal condition.
See [tree code](../src/time_integration/timestep_treebased.c) and
[timestep selection](../src/time_integration/timestep.c).

Also, the first saved `VertexVelocity` is zero, whereas the final first-drift
mesh RMS is `.4620527`. The loop selects a step, then calls
`set_vertex_velocities()` again, enabling regularization once the time bin is
nonzero. Evaluating local (126) with the final drift velocity gives raw minimum
`.00912258`, versus the snapshot-based `.01368387`. At CFL=.1 the original
first h=`.0009765625` is slightly above the final-velocity local limit
`.000912258`; at .3 the original h satisfies the final-velocity local limit.
This ordering matters for an audit; it does not explain every interval failure.

### First-state comparison, actual power-of-two steps

For the original 4096-point random IC, the strict signal minimum is
`.000955549053` (pair IDs 723/3694). Existing static tetra RD assembles
`m_i=sum_T V_T/4` and `alpha_i=sum_T max_j[A_Tj*c/3]` for uniform gas at rest;
its raw minimum `m_i/alpha_i` is `.00143439074`.

| First-state bound | CFL | Allowed dt before quantization | Selected power-of-two h | Old/new interval inversions in the frozen-velocity mesh oracle |
|---|---:|---:|---:|---:|
| Public FV tree, snapshot velocity | .3 | `.00308160` | `.001953125` | 7 / 5 |
| Local paper (126), final drift velocity | .1 | `.000912258` | `.00048828125` | 2 / 0 |
| Strict paper (129)--(130) | .3 | `.000286665` | `.000244140625` | 0 / 0 |
| Strict paper (129)--(130) | .1 | `.0000955549` | `.00006103515625` | 0 / 0 |
| Current static-RD spectral bound | .3 | `.000430317` | `.000244140625` | 0 / 0 |
| Current static-RD spectral bound | .1 | `.000143439` | `.0001220703125` | 0 / 0 |

These are **first-state kinematic comparisons**, with original drift velocities
held fixed and periodic closing meshes rebuilt independently by SciPy. The
original h reproduces the native first-pair tetra counts and 7/5 invalid counts;
all six tested h have signed box coverage defects <=`2.221e-16` and no uncertain
intervals. They are not native evolutions with alternative CFL rules, and the
static-RD calculation is not an implemented or validated moving-RD bound.
Full time-dependent RD geometry, Campoli masses and spectral envelopes still
require separate analysis. Original M2 flags do not compile `RD_3D_STATIC`,
`RD_ALE_CFL_TIMESTEP` or `RESIDUAL_DISTRIBUTION`.

### Why FV and this RD formulation still differ

[Springel (2010), §2.3](https://arxiv.org/html/0901.4107#S2.SS3) describes
Delaunay topology changes while the dual Voronoi geometry changes continuously,
with a changing neighbour relation's face reaching zero area.
From this and our implementation, the relevant distinction is:

- FV evolves conserved content in persistent generator-associated **Voronoi
  cells**, using face fluxes. It does not require a particular old/new Delaunay
  tetrahedron to remain a positive fluid element throughout the full step.
- Our RD residuals and median-dual masses use **Delaunay simplices**. Carrying
  their basis across time adds interval-element and reconnection-transfer
  requirements. This concerns this formulation, not every possible RD method;
  other moving-simplex discretizations can share the same issue.

The correct next step is therefore to use an RD-consistent fluid bound and the
actual assigned mesh velocity, then measure remaining geometry failures with
the proposed transfer policy. Do not infer either that all previous failures
are unavoidable RD geometry problems, or that strict FV CFL guarantees positive
transported tetrahedra in general. Source and numerical solver behavior remain
unchanged by this review.

## 4. 2026-10-18: development checkpoint and dedicated 3D branch

- **Author:** Codex (GPT-6), with Zhenyu Wu.
- **Execution host:** local Apple Silicon Mac.
- **Source checkpoint:** `44479a1` (CFL review at the end of entry 3).
- **Authorization:** Zhenyu approved the branch reorganization and GitHub push.
- **Status:** local fast-forward integration and branch creation completed;
  this entry and the context updates are the documentation-only handoff.

The worktree was clean. `develop_pureC_RD` at `eacc3f9` was an ancestor of
`feature/ale-flip-conservation-hierarchy` at `44479a1`, with 58 intervening
commits and no develop-only commits. The refreshed remote develop checkpoint
was `94cd37a`, another three commits behind the local develop branch.

The approved organization is:

| Branch | Role |
|---|---|
| `develop_pureC_RD` | Integrated development line, fast-forwarded to the source checkpoint plus this shared handoff documentation |
| `feature/3d-moving-mesh` | Current branch for subsequent 3D moving-mesh preparation and implementation, starting from the same integrated checkpoint |
| `feature/ale-flip-conservation-hierarchy` | Retained at `44479a1` as the previous development checkpoint |

The original commits and hashes are retained; integration uses fast-forward
operations. No rebase, squash or history rewrite is involved. Publication
targets all three named branches on `origin`
(`https://github.com/ZhenyuWu1999/arepo.git`); the push outcome and remote heads
are verified after committing the handoff. Future work continues in this same
English log on every host.

This is a development checkpoint, not a new numerical validation result.
The deferred 2D arithmetic-compatibility issue, unvalidated cold Sedov and
pending native moving-3D adapter/geometry policy remain as documented above.
There is no solver, Config or test-result change and no new build or simulation.
Local run archives remain outside Git. Publishing the source does not transfer
those archives or update a Cuillin/COSMA checkout; host adaptation and actual
cluster tests remain pending.

## 5. 2026-10-18: Claude review of entries 1–4 and face-connected cavities

- **Author:** Claude Code (Opus 5.5), with Zhenyu Wu.
- **Execution host:** local Apple Silicon Mac; one process, OMP/BLAS threads=1.
- **Branch / revision reviewed:** `feature/3d-moving-mesh` / `3d72127`.
- **Request:** review Codex's 3D moving-mesh progress through entry 4.
- **Status:** source/report review and an offline analysis of the archived M2
  first mesh pairs. No build, native run, solver/test/Config change or cluster job.
- **Evidence:** `../local_runs/claude_3d_review3_20261018_v1/` (script, results,
  input/script hashes, README).

### 5.1 Checked without finding an error

- **Entry 4 Git facts.** `eacc3f9..44479a1` has 58 commits; `94cd37a` is three
  commits behind `eacc3f9`. `origin/feature/3d-moving-mesh` and
  `origin/develop_pureC_RD` are at `3d72127`; `origin/feature/ale-flip-conservation-hierarchy`
  is at `44479a1`. This records the push outcome that entry 4 left pending.
- **M1 identities, re-derived by hand:** the Simpson mean area vector;
  `M_T-V(1/2)=a2/4+3a3/8` and `M_T-∫V=a2/6+a3/4`; `dV/dt=(1/3)ΣN_i·w_i`;
  transport identity (1); the Galilean map; the Bernstein bound on the CFL
  coefficient; mode-1 transfer conservation.
- **Registry kernel** ([rd_simplex_registry.c](../src/mesh/rd_simplex_registry.c)):
  cubic coefficients, stationary-point roots, midpoint GCL defect `c3/4`,
  mean-normal correction `δu×δv/24`, and the Gauss swept-face sign convention.
- **CFL audit (entry 3).** Its static-RD bound uses the element-maximum face
  area, as the solver does ([rd_timestep.c](../src/hydro/rd_timestep.c), lines 79–94).
- **Tests.** `test_moving_tetrahedra.py` and `test_simplex_registry.py` pass at
  `3d72127` and reproduce the reported values (1026 transfer cases, 748 limited,
  conservation 6.083e-16; interval error 4.469e-15; cavity defect 2.578e-16).
  The rest of `make check_rd` was not rerun.

### 5.2 Finding: the reported cavity size comes from the merge rule

The registry joins all four vertices of each changed tetrahedron
(`rd_registry_compare`), so two changed regions touching at one vertex become
one cavity. An alternative joins changed old/new tetrahedra only when they share
a periodic triangle key. For the changed signed chain C = new − old, ∂C = 0 because
both endpoint meshes tile the box and unchanged simplices cancel. A boundary
face of one face-connected component cannot appear in another component, or the
two would have been joined. Each component therefore has zero boundary, and
identity (4) holds component by component.

Results on the archived first pairs, `v4`; vertex-rule numbers equal the native
`geometry_cavities.csv` first-step count and maximum in every run:

| Run (first step) | Vertex rule: cavities / largest | Face rule: regions / largest / p99 |
|---|---:|---:|
| random, CFL .1 | 136 / 110 | 332 / 10 / 7.0 |
| random, CFL .3 | 57 / 1599 | 543 / 13 / 10.0 |
| Gresho, CFL .1 | 56 / 36 | 81 / 10 / 8.4 |
| Gresho, CFL .3 | 66 / 99 | 159 / 10 / 9.4 |
| shear, CFL .1 | 55 / 26 | 92 / 8 / 8.0 |
| shear, CFL .3 | 42 / 488 | 278 / 20 / 15.5 |

Advection and Sedov have no first-step reconnection. Every face-connected region
unfolds consistently by minimum image (largest distance from its reference
vertex .232) and closes to round-off. Signed volume closes to ≤2.844e-15 relative
to Σ|V| and first moment to ≤2.756e-15 relative to Σ|V|×box, at both time levels.

- **Consequence for the M2 conclusion:** the 39.038% percolating cavity is a
  property of the merge rule, not of the reconnection. Three of the five native
  winding cavities are in step 1 (random 1599; shear 480, 488), where no
  face-connected region winds. The plan's percolation trigger for §11.4 should
  be re-evaluated with face-connected regions.
- **Consequence for transfer design:** a vertex can belong to up to five regions
  (random CFL .3; 643 of 2221 changed vertices are shared). Each region's δm at
  such a vertex must be accounted separately. Either partition the star mass `g_i`
  or apply the regions sequentially, and restate the `g_i+δm_i>0` condition
  accordingly.
- **Limits:** only first steps were archived. The two step-2 winding cavities
  (random 1499, shear 469) and all later steps need a native rerun with a
  face-connected registry.

### 5.3 Finding: inversion evidence at RD-sized steps is one frozen step

Entry 3 correctly limits M2's inversions to FV timesteps. Its RD-sized evidence
is one first step with frozen velocities. With `REGULARIZE_MESH_CM_DRIFT_USE_SOUNDSPEED`,
the regularization speed is `CellShapingSpeed×c` whatever the step
([set_vertex_velocities.c](../src/mesh/set_vertex_velocities.c)). That makes the
frozen-velocity oracle fair for the first step. It also means that relative
vertex speeds do not shrink with h. Delaunay sliver heights have no lower bound in
3D, so a CFL factor can reduce but not exclude interval inversions. The earliest
crossing in entry 2 (`t=.000320812720`) is only 1.31 times the RD-sized
`h=.000244140625`.

A multi-step measurement is cheap. Rerun the random and shear diagnostics at 16³
with the step capped at `2^-12` (`MaxSizeTimestep`) to their original end times.
M3 needs an explicit invalid-interval policy (abort with diagnostic) in any case.

### 5.4 Finding: the random-point IC dominates the hazards

Random points give 19 of the 20 new-pullback records and all 23 old-interval
records; entry 2's regularization-off control removes them. Among the
jittered-lattice cases only shear CFL .3 has one record. In random CFL .3, the
vertex-rule cavity maximum falls from 1599/1499 (steps 1–2) to 75–226
(steps 3–8). Report this start-up relaxation separately from later behaviour.
A relaxed or glass IC would represent production meshes better.

### 5.5 Documentation corrections and open items

- [M1 note](RD_3D_MOVING_GEOMETRY_MATHEMATICS_20261011.md) §6 still gives
  `q≈.0068` for a regular tetrahedron. Under its own definition the value is
  `.05170027`, as entry 1 and the M2 report state. The note is left unchanged here.
- The canonical [M2 report](RD_3D_MOVING_GEOMETRY_DIAGNOSTIC_20261011.md) is in
  Chinese. It predates the English-log rule, but readers of this log need an
  English summary or translation.
- Plan M0.2 is partial: only the Yee48 LDA/B replay is byte-identical. M0.3
  (2D gates B1.3/B1.4/B1.7) has no record, and user decision §11.1 is still open.

### 5.6 Status and recommended order

M1, M2 and the cause/CFL audits are complete within their stated scopes. M3–M6
and the Cuillin adaptation have not started; no technical change followed entry 3.

1. Start M3. Gates M3.1–M3.4 use fixed connectivity and need only the abort
   policy, not the transfer or inversion decisions.
2. In parallel, add face-connected regions to the registry, keeping the vertex
   rule as a reported comparison, and rerun M2. Also run the step-capped
   diagnostic of §5.3.
3. Take decisions §11.3 (inversion) and §11.4 (cavity) on that evidence before M4.

## 6. 2026-10-18: progress review, independent face audit and capped native controls

- **Author:** Codex (GPT-6), with Zhenyu Wu.
- **Execution host:** local Apple Silicon Mac; one rank, OMP/BLAS threads = 1.
- **Branch / HEAD:** `feature/3d-moving-mesh` / `3d72127`.
- **Native binary:** frozen `57e1ae3` diagnostic, reused without rebuilding.
- **Status:** source/review audit, two algebra tests, independent first-pair
  face analysis and two short native FV controls completed. No production
  solver/Config, thesis or cluster change; no M3 implementation.
- **Evidence:** `../local_runs/codex_3d_progress_review_20261018_v1/`.
- **Report:** [English progress review](RD_3D_MOVING_PROGRESS_REVIEW_20261018.md).

Claude's entry 5 was already uncommitted at entry to this task. It is retained
verbatim, with the entry tree diff and log hash archived before this addition.
The report also summarizes Claude's October 10 integration/extension reviews:
their 2D long-trajectory compatibility finding is accepted and user-deferred;
cold-system scaling and subsequent negative pressure remain separate limits.

### 6.1 Face-region result independently confirmed, transfer still coupled

The new [read-only audit](../tests/rd/audit_3d_face_components.py) uses a
face-incidence BFS, exact integer oriented-boundary cancellation and integer
periodic-image potentials. All 11 archived first pairs pass. Region counts,
maxima and shared-node multiplicities agree with Claude. Random CFL .3 has
543 face regions, maximum 13 vertices, instead of 57 vertex groups with maximum
1599. Maximum normalized volume/moment closure defects are `1.108e-15` and
`1.063e-15`; every face boundary cancels exactly and no face region winds.

The geometric correction is accepted: the 1599 size does not establish one
intrinsically large reconnection. However, random CFL .3 still has 643 shared
vertices, membership up to five; 338 vertices donate in one region and receive
in another. Joining face regions through shared nodes recovers exactly the
original vertex groups, including 1599. A five-component transfer needs a
partitioned or sequential mass/state ledger; signed-chain identities alone
do not establish its positivity. Later-step face/winding statistics remain
unmeasured, and the C diagnostic still uses vertex-connected groups.

### 6.2 The multi-step small-ceiling control still has random inversions

Following entry 5.3, two standard moving-FV 16³ CFL .3 runs reuse the frozen
diagnostic binary and original ICs, with only `MaxSizeTimestep=2^-12` changed
apart from isolated input/output paths. Both completed at that actual timestep:

| Run | End time | Steps | Old-forward invalid | New-pullback invalid |
|---|---:|---:|---:|---:|
| Random | .015625 | 64 | 2 | 1 |
| Shear | .03125 | 128 | 0 | 0 |

Random events occur in steps 35, 38 and 63. Direct 60-digit Decimal determinants
confirm all three, with magnitudes `4.24e8`–`3.35e9` times the uncertainty
estimate. All saved FV snapshot volumes and nodal temporal masses stay positive.
The invalid counts are reduced from the original random run's 16/15 at eight
larger steps, but they are not eliminated over the same end time.

This strengthens the limitation on entry 3: a safe first frozen step is not a
full-trajectory interval-positivity guarantee. The control uses a fixed ceiling
and FV timestep selection; it does not implement or disprove a dynamically
updated moving-RD spectral bound. Actual-velocity geometric checks and an
explicit invalid-interval policy remain necessary parts of the M3 design.

### 6.3 Status and next gates

Both `test_moving_tetrahedra.py` and `test_simplex_registry.py` pass and reproduce
Claude's values: transfer conservation `6.083e-16`, registry interval error
`4.469e-15`, cavity defect `2.578e-16`. Full `make check_rd` was not rerun.

M1/M2 are complete within their scopes. Native moving RD, native five-component
transfer, moving LDA/HLLC, moving hierarchy/MPI and Cuillin adaptation are still
pending. Source guards still require static 3D RD; the native transfer header
still has four-component arrays. Model tests do not change those boundaries.

The next solver milestone is controlled fixed-connectivity M3 with explicit
topology/invalid-interval rejection. Carry forward M1's correction to the
original plan's M3.4: exact nodal affine RK2 preservation is not proved;
analytic affine Reynolds checks and native accuracy diagnostics are distinct.
The latest requested 2D baseline matrix remains incomplete, although older
equal-/mixed-bin and no-transfer evidence exists. The M1 note's incorrect
regular-tetra `q≈.0068` is corrected to `.05170027`; the M2 report gains an
English interpretation update. Context files point to these corrections.

## 7. 2026-10-18: low-resolution static 3D Gresho physical check

- **Author:** Codex (GPT-6), with Zhenyu Wu.
- **Execution host:** local Apple Silicon Mac; two concurrent singleton runs,
  each with `OMP_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1`.
- **Source:** `feature/3d-moving-mesh`, HEAD `3d72127`, frozen source archive
  including the recorded working files. Production `src/` has no working diff.
- **Request:** run a small actual static 3D problem, such as Gresho, before
  continuing moving-mesh development.
- **Status:** separate N and LDA builds and native runs completed with exit 0;
  analysis checks passed, PNG visually inspected, PDF exported. No solver,
  default Config or thesis change; no cluster job.
- **Evidence:** `../local_runs/rd_3d_static_gresho_20261018_v1/` contains the
  frozen source, configs, generated headers, binaries/linkage, compiler,
  hashes, parameters, IC, logs, five snapshots per run, analysis and driver.

### Setup and interpretation

This extends the earlier `t=.1` Gresho check to `t=.25` using the existing
repository IC: 4096 generators (`16³`), deterministic jittered lattice
(seed 928, ±.12 cell spacing per axis), periodic unit cube, gamma `5/3`,
rho=1, no bulk boost. The cylindrical vortex is independent of z and has
`v_phi=5r` for `r<.2`, `2-5r` for `.2<=r<.4`, and zero outside. It is evolved
with all five Euler components on the static 3D tetrahedral mesh; it is not
a test of arbitrary three-dimensional flow. The endpoint is about .20 of
one inner-core revolution.

N/lumped and LDA/F1 use `RD_RK2_TOTAL_RESIDUAL`, full meshes, equal adaptive
steps, `CourantFac=.1`, cap `1/2048`, unscaled production solves and existing
raw-state assertions. Both selected **2048 steps of `h=2^-13`**. Every snapshot
has unchanged coordinates and unit median-dual coverage; the reported tetra
count stays 28419. Each run saves t=0, .0625, .125, .1875 and .25.

### Results at t=.25

| Quantity | N | LDA/F1 |
|---|---:|---:|
| Volume-weighted full-vector velocity L1 | .0856480 | .0235345 |
| Volume-weighted pressure L1 | .0455891 | .0101242 |
| Volume-weighted density L1 | .00323056 | .00108099 |
| Kinetic energy / initial kinetic energy | .566279 | .975442 |
| Maximum normalized five-component conservation defect over saved states | 2.887e-15 | 1.998e-15 |
| Minimum density across reported stages | .992844 | .994448 |
| Minimum pressure across reported stages | 5.01560 | 5.00818 |
| Final maximum absolute z velocity (analytic value zero) | .030553 | .028665 |
| Wall time, seconds (concurrent runs; not a performance comparison) | 262.7 | 319.9 |

L1 weights are measured median-dual volumes `Masses/Density`, normalized by
their sum, and the reference is the stationary analytic state at each point.
Conservation covers mass, three momenta and total energy. Its component scale
is the initial sum of absolute conserved content, with at least total mass
for momentum components. All saved states and all reported stage minima have
positive density/pressure; no native numerical assertion fired. No positivity
theorem is inferred from this run.

LDA has about 3.64 times smaller velocity error and retains substantially more
vortex kinetic energy. N visibly broadens and damps the vortex; total energy
remains conserved as kinetic energy converts to internal energy. The nonzero
z velocity is a measured discretization error on the irregular 3D mesh and
must be retained in accuracy assessments. This is one low-resolution physical
check, not a convergence study or moving-mesh validation. No full algebra
suite was repeated because the numerical source was unchanged.

![Static 3D Gresho: initial, N and LDA slices, radial profile and error histories](figures/rd_3d_gresho_static_20261018/gresho_static_3d.png)

[PDF figure](figures/rd_3d_gresho_static_20261018/gresho_static_3d.pdf).
The xy panels linearly interpolate one nominal z plane (256 points); radial
profiles use all 4096 generators with volume-weighted bins. This figure does
not increase the simulation's spatial resolution. Native moving-3D M3/M4 and
Cuillin adaptation remain pending.

## 8. 2026-10-18: Sedov failure diagnosis and development priority

- **Author:** Codex (GPT-6), with Zhenyu Wu.
- **Execution host:** local Apple Silicon Mac; one rank, OMP/BLAS threads = 1.
- **Source / binaries:** `feature/3d-moving-mesh`, HEAD `3d72127`; reused the
  frozen N/LDA gamma5/3 builds of entry 7, with their source archive, headers,
  Config, linkage and hashes copied to the new evidence directory. Production
  source remains unchanged.
- **Status:** four native attempts executed and all failed diagnostically.
  The driver exits 2 for each failed two-case group; these are completed
  experiments, not passed Sedov simulations. No final blast profile exists.
- **Evidence:** `../local_runs/rd_3d_static_sedov_20261018_v1/`, including ICs,
  injection/verification metadata, parameters, stdout, return codes, native
  artifacts/source provenance, results and the archived driver.

### 8.1 Standard cold Sedov reproduces the solve-audit stop

Use the same 16³ jittered periodic unit cube as the prior benchmark and entry
7, gamma5/3, rho=1, velocity zero, ambient pressure `1e-6`, requested `t=.03`,
CFL .1 and cap `1/2048`. The nearest 15 vertices have constant specific
internal energy `279.16675756973734`. Their measured median-dual volume is
`.0035820883858286557`, giving hot-region energy exactly 1 to round-off.
Injection replaces their background energy; total initial energy is
`1.0000014946268676`. The IC file is identical to the archived October 10 IC.

| Method | Completed correctors | Last completed endpoint | Stop |
|---|---:|---:|---|
| N | 1 | 5.859375e-5 | Step 2, stage 0, tetra 47980, info=-3 |
| LDA | 0 | 0 | Step 1, stage 1, tetra 15669, info=-3 |

The tetra indices, stages, solve/conservation defects and product scales are
exactly equal to the October 10 native failures. N's solve defect is
`1.7196067948736992e-33` at scale `1.8192238353626902e-21`; LDA's is
`8.2850358085990926e-34` at scale `7.9781739900903924e-22`. In `rd_euler.c`,
info=-3 is the componentwise solve/conservation audit, not an invalid-state
return. All preceding reported stages have positive rho and pressure.
[Claude's earlier analysis](RD_3D_EXTENSION_CLAUDE_REVIEW_20261010.md#4-cold-sedov-root-cause-and-a-tested-remedy)
identifies poor scaling in these cold compatible systems; this replay confirms
the same native stop without changing scaling or tolerance.

### 8.2 A separately labelled ambient-pressure control exposes negative pressure

The additional control changes only the unheated ambient internal energy to
`p0/(gamma-1)` with `p0=1e-3`. Coordinates, density, zero velocity, heated IDs,
hot specific energy, algorithm, CFL and timestep cap are unchanged. The hot
energy remains 1 and total initial energy is `1.0014946268674`. This warmer
control is a different initial-value problem, not a repaired cold-Sedov pass.

| Method | Completed correctors | Last completed endpoint | First rejected raw state |
|---|---:|---:|---|
| N | 51 | .001669921875 | Next predictor, stage 0: ID 1673, rho=.00479701, p=-4.29021 |
| LDA | 0 | 0 | First corrector, stage 1: ID 1894, rho=1.19016, p=-.121931 |

The failing N step's printed sync time is `.00169922`; the LDA sync time is
`5.85937e-5`. Distinguish these from the last completed endpoints in the table.
N first selects `h=5.859375e-5` and later `2.9296875e-5`. The N failure is
at radius .09780, among the heated vertices; LDA fails at radius .19266.
`rd_static_validate_stage` rejects both directly from conserved content,
before primitive floors. The maximum normalized conservation defect across
the successfully reported stages is `5.100e-15`; this says nothing about the
admissibility of the subsequently rejected state. Only t=0 snapshots exist.

The cold-solve audit and strong-shock positivity are therefore distinct
observed limits. This test does not prove that HLLC is the only possible
remedy, nor does the 2D HLLC result validate an unimplemented 3D port. No
rescaling, tolerance relaxation, pressure floor or positivity repair was added.
No AREPO rebuild or repeated algebra suite was needed for these unchanged
binary runs.

### 8.3 User decision: finish the 3D mesh and execution pipeline first

After these tests, Zhenyu explicitly deferred 3D HLLC-RD and other shock
remedies. The development priority is mesh handling for moving RD, together
with hierarchical timesteps and MPI, so that the 3D workflow runs end to end.
Do not make cold Sedov success, HLLC-RD or solve rescaling a prerequisite for
that work. Keep the failed evidence as a known limitation.

Proceed through controlled fixed-connectivity moving N, reconnection geometry
and conservative five-component transfer, then moving hierarchical scheduling
and distributed mesh/ledger exchange. Use warm uniform states, smooth
advection and Gresho-style controls to check geometry, GCL, conservation,
equal-bin degeneration, mixed-bin behavior and 1/2/4-rank agreement. Existing
static hierarchy/MPI gates remain useful baselines but do not validate the
moving paths. Moving LDA and strong-shock improvements can be scheduled around
the pipeline work; the original plan's M6 HLLC stage does not block moving
hierarchy/MPI under this user decision. Cuillin adaptation remains pending.

## 9. 2026-10-18: Morton Blob preparation and short hierarchy/MPI checks

- **Author:** Codex (GPT-6), with Zhenyu Wu.
- **Execution host:** local Apple Silicon Mac; one or two MPI ranks,
  `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1`, cases run sequentially.
- **Source / branch:** frozen `3d72127` plus recorded working files,
  `feature/3d-moving-mesh`. No production numerical source change.
- **Request:** identify useful 3D tests, especially Morton 2023's Blob test.
- **Status:** primary-paper/local-predecessor review completed; a new
  [driver](../tests/rd/run_3d_blob_pilot.py) and 16³/32³ ICs prepared. Three
  shortened static N/RK2 runs completed and analysis passed. The 32³ IC has
  not been evolved, and no cluster job or full Blob reproduction was run.
- **Report:** [3D test choices and Blob preparation](RD_3D_BLOB_PREPARATION_20261018.md).
- **Evidence:** `../local_runs/rd_3d_blob_20261018_v1/` and `..._v2/`.

The [paper, section 5.3.1](https://arxiv.org/html/2204.01757v2#S5.SS3.SSS1)
uses random vertices and N1, starting at 32³. Current AREPO 3D RD requires
the N/RK2 path; predictor-only mode is guarded out. The prepared test is
therefore a physical-setup adaptation and execution check, not a matched N1
reproduction. The predecessor's BLOB block supplies a periodic side-10 cube,
centre (2.5,5,5), radius 1, densities 100/10, uniform pressure 100, gamma5/3
and wind 6.15. These also resolve an inconsistent background-density number
in the paper's prose. Exact choices and source limitations are in the report.

The 16³ random realization contains 14 cloud nodes; the prepared 32³ candidate
has 140. Quantitative cloud disruption must not be inferred from the 16³
workflow check. Use `t_cr=2 R sqrt(chi)/v_wind=1.0283829789`, retaining the
factor two, and the paper's density/temperature cloud-mass selection for a
later physical comparison.

The initial v1 attempt targeted .1 t_cr at the predecessor's CFL .01. Its
equal-step run was intentionally interrupted at approximately t=.01569 to
keep local work bounded; the other two cases were not launched. It is an
incomplete resource-interrupted attempt, not a numerical failure or success.
v2 shortens the target to .01 t_cr with unchanged IC/CFL/algorithm; binary
reuse is documented with source/Config hash comparison and the original
`binary_source.tar`.

All three v2 runs reach t=.010283829789165462:

| Case | Conservation defect | Final min rho / p | Maximum bin ratio |
|---|---:|---:|---:|
| N equal steps, 1 rank | 6.061e-15 | 9.61214 / 93.7874 | 1 |
| N natural hierarchy, 1 rank | 3.614e-15 | 9.61127 / 93.7784 | 4 |
| N natural hierarchy, 2 ranks | 3.614e-15 | 9.61127 / 93.7784 | 4 |

There are three saved snapshots per case and 512 stage-1 records; equal steps
use h=2.0085605057e-5. All saved states are positive, coordinates unchanged,
dual coverage correct, and raw-state assertions do not fire. Hierarchy 1/2-rank
times agree exactly; maximum matched-ID field difference is 3.411e-15 with
component scale `max(1,abs(reference))`. The measured initial cloud mass is
450.43409; its threshold-selected final fraction is .99070635 in both
hierarchy runs and .99070226 with equal steps. These are early diagnostics,
not mixing/lifetime or temporal-accuracy results. Full algebra tests were not
repeated because no solver changed.

For this development phase, retain oblique smooth density advection as the
analytic geometry/conservation/rank-crossing gate, add explicitly z-dependent
smooth shear for three-dimensional dynamics, and use Blob as an integrated
physical test. Full-duration 32³-and-up Blob comparisons belong on the cluster
after confirming the method/IC matching choices. Moving Blob follows the
controlled moving uniform/advection gates; HLLC-RD remains deferred.

## 10. 2026-10-19: local Blob runtime budget

- **Author:** Codex (GPT-6), with Zhenyu Wu.
- **Host:** local Apple Silicon Mac; source branch `feature/3d-moving-mesh`,
  HEAD `3d72127`.
- **Status:** timing-record inspection and arithmetic extrapolation only.
  No build, native simulation, cluster job or numerical change.
- **Evidence:** `../local_runs/rd_3d_blob_runtime_estimate_20261019_v1/estimate.json`,
  including the hashed input results and explicit assumptions.

The completed 16³ checks to .01 t_cr took 68.90 s for equal steps on one rank,
30.85 s for natural hierarchy on one rank and 16.09 s for hierarchy on two
ranks. At unchanged CFL .01, approximate cost as linear in physical duration
and proportional to n^4: n^3 work per step and approximately n steps at fixed
duration. This is a heuristic, not measured resolution scaling; random-mesh
extrema, late-time waves and bin occupancy may alter it substantially.

| Resolution | Hierarchy, 2 ranks: 1 t_cr | 1.5 t_cr | 5 t_cr |
|---|---:|---:|---:|
| 16³ | 27 min | 40 min | 2.2 h |
| 32³ | 7.2 h | 10.7 h | 35.8 h |
| 64³ | 4.8 days | 7.2 days | 23.8 days |

For 32³ to 1.5 t_cr, the same extrapolation gives 20.6 h with single-rank
hierarchy and 45.9 h with single-rank equal steps. These are conditional
runtime budgets if the simulation remains numerically admissible, not a
guarantee of completion or a validated MPI scaling curve. No 32³ or late-time
timing measurement exists yet. A short 32³ calibration should precede a
long-duration commitment. The 16³ cloud contains only 14 nodes and is useful
for workflow checks; 32³ has 140 cloud nodes. Keep full-duration/resolution
campaigns on the cluster under the existing resource policy.

## 11. 2026-10-19: cluster recommendation and COSMA handoff

- **Author:** Codex (GPT-6), with Zhenyu Wu.
- **Execution host:** local Mac.
- **Source baseline:** `3d72127` on `feature/3d-moving-mesh`, plus the reviews,
  diagnostic drivers, small native results and documentation in entries 5–10.
- **User request:** add the cluster recommendation, commit and push the work
  to GitHub. Zhenyu will log into COSMA to check whether resources are usable.
- **Status:** source/documentation handoff; no COSMA connection, module or
  allocation check, build, submission or simulation was performed here. The
  recommendation is not a claim that COSMA is currently ready or a job queued.

### Recommended allocation of work

Keep the Mac for inexpensive algebra, IC inspection and short workflow checks.
Run the full 32³-and-up Blob evolution, resolution comparisons, long stability
tests and MPI scaling on a compute cluster. Entry 10's local estimates are
extrapolations, not COSMA timing or allocation requests. First measure a short
32³ case on the actual compute node; then choose rank count and wall time.

COSMA is now the intended next host, subject to Zhenyu's resource check.
The [COSMA context](context_cosma.md) records the historical compiler/module
recipe and batch wrappers. Recheck the account, partition, limits, storage and
modules rather than assuming the September setup remains available. Compile
and run through Slurm on compute nodes. Keep large artifacts/snapshots out of
the small home quota; use an available campaign location and unique directories.

### Suggested COSMA sequence

1. Fetch `feature/3d-moving-mesh`, inspect the COSMA Git status and preserve
   any uncommitted host work before integrating. The new source is published
   on this feature branch; the older develop checkpoint need not be silently
   advanced. Consult the actual fetched commit rather than a historical hash.
2. Rebuild natively using `SYSTYPE="COSMA"`, the checked module environment,
   and the tracked `build_case_cosma.sbatch`/`run_case_cosma.sbatch` provenance
   workflow. Never copy a Mac executable. Preserve Config, generated header,
   source revision, compiler, linkage, binary hash and parameters per case.
3. Adapt the Python campaign helpers before using their build action on Linux:
   the current shared helper calls `otool -L`; COSMA needs Linux linkage
   capture or its existing managed build wrapper. Generate ICs with available
   NumPy/h5py and record their versions/hashes. Local `../local_runs/` archives
   and the prepared 32³ IC are outside Git and are not transferred by a pull.
4. Repeat the short static 3D N/LDA feature gates and the Blob workflow check.
   Check equal-bin degeneration, actual mixed bins, five-component conservation,
   positive states and 1/2/4-rank agreement where configured. Cross-host
   comparisons use explicit tolerances, not bitwise equality between MKL and
   OpenBLAS. Static hierarchy/MPI is available; moving 3D paths remain pending.
5. Calibrate a short 32³ Blob run, then establish an equal-step static baseline
   before separate hierarchy/MPI comparisons. Use the generated Blob configs
   with gamma5/3; the generic `examples/rd_3d/` configs default to gamma1.4.
   Retain CFL .01 for the documented setup unless a separate study changes it.
   Choose an explicit Slurm wall time: the existing run wrapper's 20-minute
   default is not a validated budget for a full Blob run.
6. For the first physical comparison, target common output times such as .5,
   1 and 1.5 t_cr, with three orthogonal slices and threshold cloud-mass curves.
   Report the N/RK2 versus published N1 difference and actual cloud-node count;
   a 32³ setup is not yet a matched paper reproduction. Full evolution and
   breakup have not been tested by the .01 t_cr pilot.

Append COSMA adaptation, job IDs, execution hosts, actual states and results
to this same English log. Keep HLLC-RD/cold Sedov remedies deferred and continue
the mesh/moving-RD, hierarchy and MPI development priority from entry 8.
