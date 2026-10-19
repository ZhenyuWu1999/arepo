# Moving 3D RD: review of Claude's comments and current progress

- **Author:** Codex (GPT-6), with Zhenyu Wu; 2026-10-18.
- **Execution host:** local Apple Silicon Mac, OMP/BLAS threads = 1.
- **Repository:** `feature/3d-moving-mesh`, HEAD `3d72127`.
- **Native diagnostic source:** frozen `57e1ae3`, reused without rebuilding.
- **Status:** review completed; two algebra tests, an independent offline face
  audit and two short native FV controls completed. No production solver,
  Config, thesis, cluster checkout or job was changed. M3 was not implemented.
- **Evidence:** `../local_runs/codex_3d_progress_review_20261018_v1/`.
  The pre-existing uncommitted Claude entry 5 was preserved and archived before
  editing this log. This review does not commit or publish that author's work.

## 1. Assessment

The static 3D foundation, M1 geometry/ledger models and M2 native FV diagnostic
are established within their recorded scopes. There is still **no native
moving-mesh 3D RD fluid update**. The main outstanding work is the M3 adapter,
followed by a five-component reconnection transfer with explicit geometry and
positivity policies. Static MPI/hierarchy success does not validate moving
MPI/hierarchy, and model transfer success does not validate native transfer.

Claude's latest correction is accepted: a 1599-vertex **vertex-connected**
change group does not demonstrate one intrinsically large face-connected
reconnection. Independent checks below confirm the much smaller face regions.
The shared-node coupling remains, however, so this is a useful geometric
decomposition rather than a finished transfer algorithm.

The new multi-step control also confirms Claude's warning about extrapolating
one safe frozen step: at a timestep ceiling of `2^-12`, random 16³ still has
two old-forward and one new-pullback inversions later in the run. This control
does not evaluate a dynamically recomputed moving-RD spectral bound.

## 2. What Claude found, and what follows

| Review | Supported findings | Consequence |
|---|---|---|
| [Static integration review, October 10](RD_3D_INTEGRATION_CLAUDE_REVIEW_20261010.md) | Static tetrahedral N mathematics and small native tests agree. Shared Euler-K extraction changes long 2D LDA/B trajectories, although short tests passed. | Accept the compatibility finding. The follow-up isolated the old 2D K blocks as the cause. Keep the user-approved deferral; do not describe the refactor as universally trajectory preserving. |
| [Static extension review, October 10](RD_3D_EXTENSION_CLAUDE_REVIEW_20261010.md) | Static LDA/F1, distributed CFL and frozen-dU hierarchy agree in tested small cases. Cold near-rest compatible solves are badly scaled; an independently scaled prototype subsequently develops negative pressure. | Distinguish linear-system scaling from shock positivity. Neither production cold Sedov nor a robust 3D shock scheme has passed. Production remains unscaled by user choice. |
| [Shared-log entry 5, October 18](dev_log_3D_moving_mesh.md#5-2026-10-18-claude-review-of-entries-14-and-face-connected-cavities) | M1 identities, C registry formulas, reported algebra results and Git facts check out. Vertex merging exaggerates elementary reconnection size. The smaller-CFL evidence covered only one frozen step. Random startup dominates the original hazards. | Accept the geometry and evidence-scope corrections; independently verify them below. Use face regions in the next M2 analysis, with a shared-node mass ledger, and measure full trajectories before making safety claims. |

The earlier 2D long-Yee comparison found maximum density differences of about
`1.323e-6` (LDA) and `6.453e-5` (B) at `t=1`. Same-new-binary replays were
reproducible; restoring only the old 2D K blocks restored the historical fields
byte for byte. This is a real regression in arithmetic compatibility, not
evidence of a demonstrated 3D mathematical error. Short smoke tests were not an
adequate regression gate for that refactor.

Two details in the latest recommendations need qualification:

1. **M3.4 must use the corrected gate.** The original plan asks for exact nodal
   affine-density preservation to `1e-12`. [M1's corrections](RD_3D_MOVING_GEOMETRY_MATHEMATICS_20261011.md#1-decision-on-scaling-and-corrections-to-the-proposed-gates)
   already explain why frozen-state geometry does not prove that property for
   the nonlinear RK2 update. Keep the analytic affine Reynolds identity and
   use native affine evolution as an accuracy/convergence diagnostic. Do not
   impose or promise an unsupported exactness assertion.
2. **The latest minimal 2D matrix is incomplete, rather than all 2D hierarchy
   evidence being absent.** The [October 9 report](RD_FLIP_HIERARCHY_REPORT_20261009.md)
   records equal-bin, mixed-bin and no-transfer controls, mainly for the older
   mode-0 matrix, with selected mode-1 lazy gates. These do not establish the
   complete B1.3/B1.4/B1.7 matrix subsequently requested for the current mode-1
   baseline. M0.2 also has only selected current LDA/B bytewise replays.

The regular-tetra quality value in the M1 note is corrected in this review to
`q = sqrt(2)/(12*3^(3/4)) = 0.05170027...`. Its former `.0068` value was wrong
under its stated definition. Claude-authored historical reports are preserved.
The original Chinese M2 report predates the English-log rule; shared-log entry
1 already supplies an English evidence summary, now supplemented here.

## 3. Independent checks in this review

### 3.1 M1 and registry checks

The two existing tests passed with OMP/BLAS threads = 1:

- `test_moving_tetrahedra.py`: 300 geometry cases and 1026 five-component
  transfer cases, 748 limited; maximum transfer conservation defect
  `6.083e-16`. The complete Campoli model and negative controls also pass.
- `test_simplex_registry.py`: 800 intervals and 35 cavity models; maximum
  interval error `4.469e-15`, cavity defect `2.578e-16`.

These reproduce Claude's numbers. The full `make check_rd` suite was not rerun
in this review. The registry test compiles its temporary C shared library;
there was no AREPO rebuild. These remain model/kernel checks, not a native
moving-RD test.

### 3.2 Face regions: confirmed, with a remaining transfer coupling

New read-only [audit script](../tests/rd/audit_3d_face_components.py) uses
face-incidence breadth-first search, rather than Claude's union-find, and
checks **exact integer cancellation of every oriented boundary face**. A
second BFS assigns integer periodic-image potentials and detects winding
cycles, rather than choosing minimum images relative to a reference point.
Signed volumes and first moments are then evaluated at both time levels.

All 11 archived first pairs, including the separate small probe, pass. Counts,
largest regions and vertex multiplicities agree with Claude's archive, whose
script and input hashes were also verified. Six pairs contain reconnection:

| First-step run | Native vertex groups / largest vertices | Face regions / largest vertices |
|---|---:|---:|
| Random, CFL .1 | 136 / 110 | 332 / 10 |
| Random, CFL .3 | 57 / 1599 | 543 / 13 |
| Gresho, CFL .1 | 56 / 36 | 81 / 10 |
| Gresho, CFL .3 | 66 / 99 | 159 / 10 |
| Shear, CFL .1 | 55 / 26 | 92 / 8 |
| Shear, CFL .3 | 42 / 488 | 278 / 20 |

Every face region has zero integer signed boundary and no winding cycle.
Maximum normalized volume and first-moment closure defects are `1.108e-15`
and `1.063e-15`; coordinate consistency is `3.331e-16`. Different unfolding
origins/order explain the small difference from Claude's round-off values.
The region mass changes sum to the full-star old/new mass difference with a
maximum defect `8.755e-16`, normalized by the maximum old nodal star mass.

For random CFL .3, **643 of 2221 changed vertices belong to multiple face
regions**, with maximum membership five; 338 vertices donate mass in one
region and receive in another. Connecting these regions through shared nodes
recovers exactly the original 57 vertex groups, including the 1599-vertex
group. Thus geometric locality is established for these first pairs, while
state/limiter coupling through shared degrees of freedom remains.

Each region can satisfy the signed volume/moment identities without being a
positive tiling throughout the interval. Those identities do not prove
positivity of a nonlinear transfer. In particular, do not reuse the original
full `g_i` independently for every region's positivity assertion and assume
the sum is admissible. A partitioned mass budget or a deterministic sequential
update must account for all region-specific `delta m_i`; the corresponding
five-component conservation/uniform-state/positivity claims need new tests.
For illustration only, the largest summed negative region mass change in
random CFL .3 is 0.4382 of its old full-star mass. That scalar observation is
not a conservative-state positivity proof.

Only first pairs were saved. This confirms that the three first-step native
winding groups disappear under face partitioning; the two later step-2 winding
groups and later face-region statistics remain unmeasured. The registry's
production diagnostic still implements the vertex rule; this review does not
change it or claim a full face-connected M2 rerun.

### 3.3 New timestep-capped native controls

Reused frozen M2 binary SHA256
`41d22fe6e4c4a44ab8cb0d6ff9733f62f20fae741591d593b47ee4855f7ee1c7`.
Config/header/linkage/build provenance, unchanged ICs, edited parameters, run
logs and status/hashes are archived. The only numerical parameter change from
the original CFL .3 cases is `MaxSizeTimestep = 0.000244140625`; IC/output paths
point to isolated review directories. Both runs use a periodic unit box,
4096 generators, one rank, standard moving Voronoi FV, full equal steps,
sound-speed mesh regularization with `CellShapingSpeed=.5`.

| Run | End time | Actual steps / h | Old-forward invalid records | New-pullback invalid records | Final minimum FV volume |
|---|---:|---:|---:|---:|---:|
| Random | .015625 | 64 / 2^-12 | 2 | 1 | 4.813e-5 |
| Shear | .03125 | 128 / 2^-12 | 0 | 0 | 1.929e-4 |

Both completed, in about 15.9 and 26.6 seconds respectively, with no uncertain
volume classifications and no nonpositive nodal temporal mass. The random
events occur in steps 35 and 38 (old forward), and 63 (new pullback). A direct
60-digit Decimal determinant check confirms all three sign changes, with
negative magnitudes exceeding the diagnostic uncertainty estimate by
`4.24e8` to `3.35e9`. The zero-crossing times are `.0084371184057`,
`.0092424762708` and `.0151907842943`. The new-pullback event has
`V(0)/V(1)=-.28453`; its endpoint-average element temporal volume is positive.

The earlier random CFL .3 trajectory had 16/15 old/new invalid records in
eight larger steps. The capped trajectory has 2/1 over the same end time;
reducing the ceiling substantially reduces but does not eliminate these
events on this IC. The trajectories are different; this is not a same-velocity
oracle beyond the first step. All saved Voronoi snapshot volumes are positive.

**Interpretation:** the initial RD-sized reference step was not an interval
positivity guarantee for the subsequent native FV trajectory. This test still
uses a fixed ceiling plus FV timestep selection. It neither implements nor
disproves a dynamically recomputed moving-RD spectral bound. A geometric bound
using the actual assigned velocity, and an invalid-interval policy, remain
separate requirements. The proposed M3 guard should fail before an invalid
geometry is used, with enough data to reproduce the interval.

## 4. Implementation audit and remaining milestones

| Stage | Actual state | Main remaining boundary |
|---|---|---|
| Static 3D N/LDA | Implemented; 50 small 8³/16³ feature gates, including 1/2/4 ranks and frozen-dU hierarchy, plus reduced Sod/Gresho evidence | Cold Sedov/shock positivity unvalidated; these results do not extend to moving geometry |
| M0 baseline | Current arithmetic/user choices recorded; selected diagnostic-OFF/ON 2D replays match bytewise | Complete the explicitly chosen current 2D gate matrix before shared numerical changes; old K compatibility repair stays deferred |
| M1 | Reviewed moving-tetra identities, CFL majorant and independent complete Campoli/transfer models | Nonlinear native RK2 accuracy and transfer positivity are separate gates |
| M2 | Native FV registry/interval diagnostic and original 134-step campaign complete; cause/CFL audits and this 192-step supplement complete | Native face partitioning and later-step region/winding statistics; relaxed/glass comparison; dynamically updated RD bounds |
| M3 | **Not implemented** | Controlled fixed-connectivity N adapter, mean normals and temporal masses, actual-velocity timestep/interval checks, revised gates |
| M4 | **Not implemented** | Native five-component transfer, shared-node accounting, invalid-interval and winding policies |
| M5/M6 and moving parallel features | **Not implemented** | Moving LDA/B, tetrahedral HLLC/positivity, then moving hierarchy/MPI/lazy/restart |

The source confirms the boundary: the non-2D branch in
`src/hydro/residual_distribution_solver.c` requires `RD_3D_STATIC` with
`VORONOI_STATIC_MESH`; the diagnostic flag in
`src/mesh/rd_3d_geometry_diagnostics.c` excludes RD entirely. Native
`src/hydro/rd_flip_transfer.h` still has four-component state arrays. The
five-component Python cases therefore cannot be reported as an implemented
native reconnection transfer.

The original random IC accounts for 19/20 new-pullback and all 23 old-interval
records in the M2 campaign; only one new-pullback record comes from the
jittered-lattice shear cases. Random startup and later behaviour should be
reported separately. No relaxed/glass comparison has been run here; it would
test representativeness rather than invalidate the observed stress-test events.

## 5. Recommended next work

1. Prepare M3 on fixed connectivity: periodic, one rank, equal steps, N first,
   warm/smooth states, lazy OFF, unchanged production scaling. Reject topology
   changes and nonpositive/uncertain intervals explicitly. Run zero-velocity,
   translation and verified no-flip deformation gates; use the corrected
   affine accuracy diagnostic. This does not require a completed M4 policy.
2. Extend the diagnostic registry with face regions while retaining the vertex
   comparison. On Cuillin, archive enough later pairs to measure region sizes,
   winding and shared-node coupling through complete trajectories; compare
   random startup against relaxed/glass ICs and record the actual moving-RD
   timestep reference from assigned mesh velocities. The small capped control
   requested by Claude is now complete and need not be repeated unchanged.
3. Before M4, choose invalid-interval handling and a shared-node transfer mass
   ledger. First verify overlapping face-region model transfers; then generalize
   the native kernel to five components with the frozen 2D arithmetic gates.
   Decisions on winding and exceptional geometry must follow the expanded M2
   evidence, not the old 1599-vertex statistic alone.

Cuillin adaptation and actual cluster runs are still pending. GitHub branch
publication at `3d72127` is a source handoff, not evidence of a cluster checkout
update, native moving-RD support, convergence order or production readiness.
