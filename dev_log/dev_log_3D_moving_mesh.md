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
