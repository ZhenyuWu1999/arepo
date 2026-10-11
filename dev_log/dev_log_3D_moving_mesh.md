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
