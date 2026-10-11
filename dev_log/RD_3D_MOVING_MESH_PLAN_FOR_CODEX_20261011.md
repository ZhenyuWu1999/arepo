# Plan for 3D moving-mesh RD (handoff to Codex)

- **Author:** Claude Code (Opus 5.5), at the user's request, 2026-10-11.
- **Branch:** `feature/ale-flip-conservation-hierarchy`. **HEAD when written:** `179c7bd`.
- **Status:** plan only. No code was changed. The user decides the points in §11 before the stages that depend on them.
- **Audience:** Codex. Read this together with:
  - [3D feasibility](RD_3D_FEASIBILITY_20261010.md), especially §§3.3–3.4, 4 and 5. This plan builds on it rather than repeating it.
  - [3D kernel mathematics](RD_3D_KERNEL_MATHEMATICS_20261010.md) and [3D features and benchmarks](RD_3D_FEATURES_AND_BENCHMARKS_20261010.md).
  - My reviews: [first](RD_3D_INTEGRATION_CLAUDE_REVIEW_20261010.md) and [second](RD_3D_EXTENSION_CLAUDE_REVIEW_20261010.md). §4 of the second has the cold-gas scaling result.
  - The 2D foundation:
    - [flip element and hierarchy design](RD_FLIP_ELEMENT_AND_MOVING_HIERARCHY_DESIGN_20261008.md);
    - [progress report](RD_FLIP_HIERARCHY_REPORT_20261009.md);
    - [DGCL audit](RD_moving_mesh_DGCL_mathematical_audit.md);
    - [ALE form selection](RD_ALE_FORM_SELECTION.md);
    - `examples/rd_moving_baseline/README.md`.
  - The 2D test plan [B-gates](RD_FLIP_HIERARCHY_TEST_PLAN_FOR_CODEX_20261009.md), **as corrected by Codex in log3 §226**.

## 0. Summary

The static 3D base is ready for this work: N/LDA, the hierarchy, MPI, the simplex geometry and the five-component state. The 3D moving mesh adds problems that static 3D never met:
- **Geometry in time.** Face area vectors are quadratic in time and volumes are cubic.
- **Slivers.** 3D Delaunay meshes contain slivers, which can invert during a step, or when pulled back to the old positions.
- **Reconnection.** Topology changes are 2-3, 3-2, 4-4 flips and larger cavities.
- **Shocks.** Shock problems need a positivity-preserving tetra scheme (HLLC-RD).

The plan therefore front-loads the two biggest unknowns: a mathematical note (M1), and a **geometry-only dry run** inside AREPO (M2). It does both before writing the moving fluid solver. Stages:

| Stage | Content | Native solver code? |
|---|---|---|
| M0 | Preconditions: cold-gas scaling (3D only), freeze a 2D bitwise reference, minimal 2D gates (user decision) | small |
| M1 | 3D moving-geometry mathematics note and Python oracle | no |
| M2 | Geometry dry run: tetra registry and cavity statistics on AREPO 3D moving meshes | diagnostic only |
| M3 | Moving 3D N, equal step, Campoli: fixed-connectivity gates, then flips without transfer (measured defect) | yes |
| M4 | 3D cavity transfer (five components) | yes |
| M5 | Moving flows: N, then LDA (B later) | yes |
| M6 | HLLC-RD on tetrahedra, static then moving; Sod/Sedov | yes |
| Later | Interval hierarchy, MPI for the moving path, lazy flips (if at all) | yes |

Each stage ends with frozen evidence, a dev_log report or log3 entry, and a commit. After **M1** and after **M3/M4**, stop for a review by the user, who may route it to Claude.

## 1. Ground rules

1. **Rules.** Follow `AGENTS.md`:
   - frozen source, Config, binary and IC provenance;
   - keep failed attempts and do not relabel them;
   - no floors, clipping or loosened audits to make a gate pass;
   - log3 entries; no thesis edits; no push unless asked.
2. **Resources.**
   - Single rank first. `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1`, and at most 6–8 concurrent local solver processes.
   - Local runs stay at 8³–16³, or short 24³ runs. Convergence, long-time and scaling runs go to COSMA/Cuillin, after the Linux adaptation of the provenance helper (it uses `otool` today).
3. **2D must not change silently.** Every commit that touches shared code passes the frozen 2D reference of M0.2 **bitwise**, unless the user has approved a 2D arithmetic change.
4. **3D ports only the current 2D baseline.** It is defined by `examples/rd_moving_baseline/`:
   - Campoli mass, `RD_ALE_CONTOUR_RESIDUAL` and `RD_ELEMENT_COMOVING_FRAME`;
   - `RD_ALE_FLIP_TRANSFER` with mode 1, floor 0.5, hull and entropy bounds off;
   - no lazy flips.

   Do **not** port to 3D:
   - the Arpaia form, `RD_ALE_HIERARCHICAL` (old basis closure) or `RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC`;
   - `RD_ALE_SPLIT_MESH_VELOCITY`, entropy dissipation, shear floor, or `RD_RK2_RATE_CONSISTENT_HEUN`.

   Keep these excluded by the existing 3D `#error` list.

## 2. Starting point

| Component | State | 3D moving work needed |
|---|---|---|
| Euler K, LU/SVD (`rd_euler.c`, `rd_linalg.c`) | dimension-generic; eigenvalue-shift capable | comoving-frame states; contour total; reconciliation; cold-gas scaling (M0.1) |
| Simplex geometry (`rd_simplex_geometry.c`) | static triangle/tetra; signed volume | time levels and time-averaged area vectors, i.e. the 3D analogue of `rd_ale_geometry.c`, which is triangle-only today |
| ALE prepare/finish (`rd_ale_prepare_step`, `rd_ale_finish_step`) | 2D: midpoint normals, `delta_area` 2D identity, box *area* coverage | dimension-generic rewrite (M3) |
| Old/new snapshot and cavity diff (`rd_ale_topology_capture_old_mesh`, `rd_ale_apply_flip_transfer`) | 2D: 3-ID keys, 4-component states, one rank | 4-ID keys, `RD_NVAR` (M2/M4) |
| Transfer kernel (`rd_flip_transfer.h`) | `double (*)[4]` throughout | `RD_NVAR`; kinetic energy with three momenta (M4) |
| Interval registry/hierarchy (`rd_reg_*`, `rd_ale_interval_*`) | 2D, one rank | later stage |
| HLLC-RD/Rusanov (`rd_hllc.h`, `rd_rusanov.h`) | 2D, 4 components | M6 |
| Mesh-velocity test policies (`RD_ALE_TEST_ZERO_MESH_VELOCITY`, `RD_ALE_MESH_VELOCITY_FRACTION`) | allowed only for 2D ALE paths | enable for 3D tests |

## 3. M0: preconditions

**M0.1 Cold-gas scaling (3D only).**
- Adopt the similarity-scaled upwind solves from my second review §4: D = diag(1, c, …, c, c²) from the Roe sound speed.
  - Apply it to both the spatial solve and the F1 temporal solve.
  - Keep all audits on the unscaled S and rhs.
- The prototype patch is `../local_runs/claude_3d_review2_20261010_v1/scaled_prototype.patch`. Re-implement it cleanly; do not copy the review harness.
- **Gates:**
  - add a cold-at-rest kernel test to `check_rd`, like `sweep_cold_states.py`. Production failed up to 341/400 at p = 1e-9; the scaled solve must give 0 failures;
  - existing 3D suites: conservation unchanged, and field differences at round-off;
  - the 2D reference (M0.2) stays bitwise.

  Moving meshes produce slivers, so this must precede M3.

**M0.2 Frozen 2D reference.**
- Archive a bitwise reference set at the commit that precedes 3D moving work:
  - moving equal-step N, LDA, B and HLLC (`rd_moving_baseline` equal Configs);
  - LDA/B/N on Yee48 to t = 1 (256 steps), HLLC on Sedov21 to t = 0.005;
  - optionally one natural-bin interval-hierarchy run.
- **Gate:** every later commit reproduces all saved particle datasets byte-for-byte after sorting by ID, using the method of Codex's `verify_particles.py`.

**M0.3 Minimal 2D gates (user decision, §11.1).** The 2D campaign of the test plan (log3 §225, corrected in §226) has not been run. Recommended minimum before porting: B1.3 (equal-bin degeneration), B1.4 (uniform state with flips and mixed bins) and B1.7 (no-transfer negative control). They are cheap and confirm that the 2D scheme being ported conserves as claimed.

## 4. M1: mathematics note and Python oracle (no AREPO code)

Write `dev_log/RD_3D_MOVING_GEOMETRY_MATHEMATICS_<date>.md` and an independent Python oracle under `tests/rd/`, extending the feasibility probe. The note must settle the following points.

**D1 Time integration of the geometry.**
- **The exact claims.** With linear vertex trajectories:
  - the face area vector N_j(t) = A_j n_j (inward, opposite vertex j) is quadratic in t;
  - V_T(t) is cubic in t;
  - ∇·σ_h is constant on T(t).
- **Ledger term (verify).** The 2D code splits mesh transport into two pieces:
  - the endpoint-ledger term Σ_i (m_new − m_old)_i U_i^n, which equals Δt ∫U_h ∇·σ_h because V_T ∇·σ_h = dV_T/dt;
  - an element term σ̄·∫V_T ∇U_h dt = σ̄·Σ_j (∫N_j dt) U_j / d.

  I believe the ledger identity holds in any dimension with **endpoint volumes only**. Verify this.
- **Element terms (verify).** For states frozen within a stage, every geometric factor in the element residual is linear in N_j: the physical flux total, the comoving-frame shift, and the Roe K. So the exact time integral should need only the **time-averaged area vectors** N̄_j = (1/Δt)∫N_j dt. Simpson is exact for these. If this holds, the residual is evaluated once per element and stage, with N̄_j, rather than at two Gauss points.
- **Recommended form:** N̄_j = N_j(½) + [N_j(0) − 2N_j(½) + N_j(1)]/6.
  - The correction vanishes exactly for a static mesh, so the 2D σ = 0 "collapses bitwise to static" check survives.
  - In 2D the correction is zero in exact arithmetic.
- **K and CFL coefficients.** Build K from |N̄_j| and n̄_j = N̄_j/|N̄_j|, and terminate if |N̄_j| = 0.
- **Identities to prove and test** (fixed connectivity, Campoli: temporal mass (V_old+V_new)/2, divisor V_new):
  - (i) conservation telescopes;
  - (ii) a uniform state is preserved;
  - (iii) **an affine density field at rest with uniform pressure** is preserved at every node on a deforming mesh;
  - (iv) shared-face contributions cancel;
  - (v) σ = 0 reduces exactly to static.

  Also show that the midpoint area vector violates (iii) at O(Δt³) per step. That is the negative control for M3.
- Replace the 2D-only `delta_area = dt²/8 (Δv₁₀ × Δv₂₀)` check with its 3D counterpart, or drop it. Campoli does not need it.

**D2 Comoving frame and contour residual in 3D.**
- **Port these 2D constructions with general d** (factor 1/d on N_j; lumped row sum 1/(d+1)):
  - the frame shift by σ̄ (mean of the four vertex velocities);
  - the contour total Φ = Σ_j (N̄_j/d)·F_j;
  - the N/B reconciliation with the lumped row sum;
  - the frame split correction.
- **3D contour Gauss correction.** `rd_contour_quadrature.h` uses Gauss points on edges; in 3D the faces are triangles.
  - The baseline Configs do not set `RD_ALE_CONTOUR_GAUSS`, so port only the trapezoid/P1 total first.
  - If a Gauss correction is wanted later, it needs a triangle-face rule (see feasibility §4.3).

**D3 Volume positivity over a step.**
- V_T(t) is cubic. Its minimum on [0, Δt] is at an endpoint or at a real root of the quadratic V_T′. Checking old, midpoint and new values is not enough (feasibility §4.6).
- Define the checks needed for:
  - every **new** tetra on [t^n, t^{n+1}], including the pulled-back old volume;
  - the positivity of the Campoli temporal mass (V_old + V_new)/2 and of the nodal divisors.
- Define a sliver quality measure (V/(ΣA)^{3/2}; 6.8e-3 for a regular tetra, 7.9e-4 for the failing Sedov element) to record in M2.

**D4 Cavities in 3D.**
- Cavities are the vertex union of the symmetric difference of old and new tetra key sets, as in 2D.
- Prove that Σδm = 0 and Σδm x = 0 per cavity, with P1 masses V/4, and that masses outside every cavity are unchanged.
- Keys: start with ID-only 4-tuples plus the duplicate-key abort, as in 2D. Add periodic offsets only if a gate hits the abort.

**D5 Positivity of the five-component transfer.** Extend the transfer derivation to RD_NVAR:
- donor-cell low order, uniform-shift and receiver-only high modes, the θ blend, floors;
- internal energy using three momenta.

Codex's feasibility probe covered 2↔3. Add 4-4 and larger cavities from SciPy Delaunay of perturbed point sets.

**M1 gate:** the oracle passes (i)–(v), with the midpoint control failing visibly, and verifies the D3 root logic and the D4/D5 identities on random cavities. Stop for review.

## 5. M2: geometry dry run on real AREPO 3D moving meshes

**Purpose.** Measure, before any moving RD code exists:
- how often 3D reconnection happens;
- how large the cavities become;
- how often pulled-back new tetrahedra invert.

These numbers decide the inversion policy and whether the cavity transfer stays local.

**How.**
- Implement the 3D simplex registry and cavity diff as a **standalone module**, needed in M4 anyway, for example `src/mesh/rd_simplex_registry.{c,h}`. It builds sorted keys, pulls back to old positions, finds union-find cavities and accumulates statistics.
- Call it from a **diagnostic-only** hook that cannot change the solution.
- Move the mesh with AREPO's standard 3D finite-volume hydro (Lagrangian velocity plus `REGULARIZE_MESH_CM_DRIFT`/`_USE_SOUNDSPEED`/`REGULARIZE_MESH_FACE_ANGLE`, as in the 2D baseline). This gives realistic trajectories independent of RD.
- Single rank, 16³.

**Cases.**
- **Uniform gas at rest, random or jittered points.** Regularisation alone moves the mesh. This is the 3D counterpart of 2D `uniform_random48`.
- **3D Gresho** (z-invariant) and **oblique smooth advection** at the SWIFT-family settings.
- **Short 3D KH-like shear.**
- **Sedov** with the FV solver, for mesh statistics only.
- Two CFL values, e.g. 0.3 and 0.1.

**Record per step:**
- removed and inserted tets, and the number of cavities;
- cavity vertex count (max, 99th percentile), and the fraction of vertices inside cavities;
- pulled-back inversions (V_old ≤ 0 for new tets), and min V_old/V_new;
- the in-step minimum volume from D3, and the sliver-quality distribution;
- duplicate keys.

Compare with the 2D numbers (Yee48: 249 cavities in 256 steps).

**Gate.**
- The report is the deliverable; there is no pass/fail.
- Stop for the user's decision on the inversion policy (§11.3) and the cavity policy (§11.4) **if any** of the following happen:
  - pulled-back inversions occur at the chosen CFL;
  - cavities percolate, e.g. a cavity spans more than ~1 % of all vertices.

## 6. M3: moving 3D N, equal step, Campoli

- **Geometry and step.**
  - Implement the dimension-generic ALE geometry: the 3D extension of `rd_ale_geometry`, using D1/D3.
  - Implement prepare/finish (coverage of the box *volume*, divisors, positivity checks).
  - The element residual uses the comoving frame and contour total from D2, with N̄_j.
- **Guards.**
  - Allow a new `RD_3D_MOVING` path (or equivalent) only with `RD_ALE_EQUALSTEP`, `RD_ALE_CAMPOLI_MASS`, `N_SCHEME`, `FORCE_EQUAL_TIMESTEPS`, `CREATE_FULL_MESH` and one rank. Every other ALE option stays an `#error`.
  - Start with **no transfer**: topology changes are detected and reported, not repaired.
- **Gates:**

| Gate | Setup | Pass criterion |
|---|---|---|
| M3.1 | `RD_ALE_TEST_ZERO_MESH_VELOCITY` | geometry collapses bitwise to static coefficients; conservation round-off; differences from static 3D N reported and explained (contour vs Roe total) |
| M3.2 | uniform flow, uniform mesh velocity (pure translation, so Delaunay does not change) | zero changed tets; state defect ≤ 1e-12; conservation ≤ 1e-13 |
| M3.3 | uniform gas, small regularisation motion on a near-lattice, short enough that **zero** tets change (verify) | state defect ≤ 1e-12; conservation ≤ 1e-13 |
| M3.4 | affine density at rest, uniform p, same deforming mesh as M3.3 | preserved ≤ 1e-12 with N̄_j; a midpoint-normal control build fails visibly (record the size) |
| M3.5 | uniform gas with real reconnection (M2 uniform case) | uniform preserved (the flip defect vanishes for affine fields); conservation of non-uniform runs **violated** by the measured flip defect, recorded per step — the expected negative result, the 3D analogue of the 2D motivation |
| M3.6 | oblique smooth advection 8³/16³, short | completes, positive, error vs exact recorded; conservation loss equals the summed flip defects to round-off (accounting check) |

Stop for review after M3.

## 7. M4: cavity transfer in 3D

- **Kernel.** Generalise `rd_flip_transfer.h` to `RD_NVAR` without changing 2D arithmetic. 2D stays bitwise (M0.2).
- **Unit tests.** Extend `test_flip_transfer.py` with 3D cavities: 2-3, 3-2, 4-4, and larger SciPy cavities. Include extreme contrast (Sedov-like 1e8 energy ratio) and counter-streaming states. Check:
  - conservation ≤ 1e-14;
  - uniform states exact, affine states unchanged with θ = 1;
  - mode-1 donors bitwise unchanged;
  - bounds hold.
- **Native.**
  - Wire `RD_ALE_FLIP_TRANSFER` into the 3D path, before the divisor rebase, refreshing primitives for all schemes as in 2D.
  - Make `RD-ALE-FINISH` a hard round-off conservation assert, as in 2D.
- **Gates:**
  - M3.5 and M3.6 now conserve to ≤ 1e-13;
  - uniform with reconnection stays exact;
  - record θ < 1 counts, cavity sizes and maximum nodal change;
  - a negative control without transfer reproduces the M3.5 loss.

Stop for review after M4.

## 8. M5: moving flows

- **N first:** oblique advection, 3D Gresho (z-invariant; also a version rotated off the axes), and a short KH-like shear.
- **Then LDA,** with the F1 temporal mass (V_old+V_new)/2.
- **Metrics.** Use own-coordinate analytic errors and conservation, as in 2D. Do not use matched-ID differences as Eulerian distances.
- **Local versus cluster.** Locally, only short 8³/16³ runs are functional checks. Convergence (16³/24³/32³ or larger) and long runs go to the cluster.
- **B comes after LDA.** It needs the 3D θ (`RD_B_SCALAR_THETA`/`FROZEN_THETA`) and its Roe/contour reconciliation.

## 9. M6: HLLC-RD on tetrahedra

- **Port** `rd_hllc.h` and `rd_rusanov.h` to `RD_NVAR` and to tetra faces. Re-derive the stage convexity weights and the CFL in 3D (the 2D code uses a_i = temporal mass/divisor and b_i = 3/2 − a_i).
- **Static first:**
  - Sod along an axis and obliquely;
  - the SWIFT-family cold Sedov, which N and LDA cannot pass (my second review §4.5; log3 §156 for 2D).
- **Then moving,** with the 3D transfer: Sedov (positivity, conservation, shell radius against analytic), using the 2D thesis protocol adapted to 3D.

## 10. Later

- **Interval hierarchy in 3D.**
  - Registry with s_T; closure of complete stars; synthetic tessellation; ledger divisor; CFL ledger.
  - Re-derive the shared-face cancellation for quadratic face vectors integrated over unequal intervals. The feasibility probe found interval additivity at 1.4e-16.
- **MPI for the moving path.** The registry, cavities and transfer are one-rank today. Cavities that cross rank boundaries need a design note before any code.
- **Lazy flips** are not part of the baseline (user decision, §228). Do not port them unless asked.

## 11. Decisions for the user

1. **2D campaign versus 3D.** Run the minimal 2D gates (M0.3) or the full corrected 2D campaign before or alongside 3D? The final thesis version depends on 2D.
2. **2D arithmetic.** Keep the K-refactor and scaling changes 3D-only, or make one combined 2D compatibility decision (restore the old order or accept a new one)?
3. **Inversion policy (after M2).** If pulled-back or in-step inversions occur, the options are:
   - abort with a diagnostic;
   - a geometric timestep limit, i.e. predictive, from the previous mesh;
   - reconnecting at an event time within the step;
   - stronger regularisation.
4. **Cavity policy (after M2).** If cavities percolate: accept large cavities (the transfer stays conservative but less local), or split by time or event.
5. **Order of M5 versus M6.** Shocks (HLLC-RD) before or after smooth LDA/B?

## 12. Main risks

- **Slivers.** Delaunay does not exclude them in 3D. They drive pulled-back or in-step inversion, near-singular S⁻, and tiny temporal masses.
- **Cavity size.** It may grow far beyond 2D, making the transfer less local.
- **Hidden 2D identities.** The 2D code relies on midpoint normals being exact and on the 2D `delta_area` identity. Every such place must be found (D1).
- **Positivity of LDA.** LDA is not positive for strong shocks, so N/LDA results on shocks are not a target.
- **Cost.** A full mesh rebuild every step, plus registry diffs. Measure it in M2; performance is not a goal before MPI.

## 13. Deliverables per stage

For each stage, deliver:
- code with guards;
- unit and native tests with explicit pass criteria;
- a frozen archive under `../local_runs/`;
- a report or log3 entry stating the scope, failures and what is **not** established;
- the M0.2 2D bitwise check;
- a commit under "Zhenyu Wu and Codex (GPT-6)".

Mark every result as one of: functional check, conservation/identity gate, or accuracy evidence.
