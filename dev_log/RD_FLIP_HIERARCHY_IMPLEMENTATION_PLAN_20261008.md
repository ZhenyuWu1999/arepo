# Detailed implementation plan: flip element and moving-mesh hierarchy

Author: Claude Code (Opus 5.5) planning agent, 2026-10-08, for Zhenyu Wu. Saved verbatim as the
working reference for the approved plan (~/.claude/plans/i-have-already-submitted-tender-spindle.md)
and RD_FLIP_ELEMENT_AND_MOVING_HIERARCHY_DESIGN_20261008.md. Line numbers refer to develop_pureC_RD
snapshot eacc3f9.

# Staged plan: conservative and positive edge flips, then hierarchical timesteps, on the moving-mesh RD solver (one MPI rank)

## Main design decisions

These come from reading the current code and the prototype branch `test/colombo-re-explicit-hierarchy`.

1. **A flip is a degenerate space-time RD element.** For each connected changed cavity P:
   - The residual is D_P = Σ_i dm_i U_i = ∫(U_h^new − U_h^old), with dm_i = b_i − a_i.
   - The high-order distribution is the uniform shift, β_i = g_i⁺/Σg⁺. It is linearity preserving.
   - The low-order distribution is "minimal transport". It is N-like, with coefficients c_ij ≥ 0 and no CFL condition.
   - The two are blended with one θ for the whole cavity, chosen from convex invariant-domain bounds. This reuses the structure of B and of the LDA/HLLC blend that already exist in the code.
2. **Campoli becomes the only conservative ALE baseline.** I checked the algebra:
   - For lumped N, F1/LDA and the B blend, the RK2 total satisfies Σ_i Q_i^{n+1} = Σ_i ĝ_i Û_i exactly. Here ĝ_i is the pullback nodal mass and Û_i the opening state.
   - The step uses the per-triangle Campoli mass M_T = (A0+A1)/2 and divisor D_i = Σ A1/3 = S_i^{n+1}.
   - So the temporary ledger is already the endpoint storage, and the endpoint conversion can be skipped entirely. Loss (b) is then exactly zero, not just zero to round-off.
   - With Arpaia the same computation leaves Σ(D^A − S^{n+1} + ĝ)Û, which is loss (b).
3. **Triangle identity does not depend on storage indices.** A triangle is identified by its three particle IDs, stored counter-clockwise starting from the smallest ID; the comparison key is the sorted triple. Coordinates are rebuilt each step as the minimal image relative to the smallest-ID vertex. The code aborts if any edge is ≥ L/2 or a key is duplicated. This is exact for any realistic box and avoids storing periodic offsets.
4. **No stored geometry is needed.** One invariant makes this work: a vertex's mesh velocity or state trace changes only when the vertex is refreshed, and a refresh first closes every incident interval. So every open triangle moves linearly over [s_T, t]. The existing `rd_ale_triangle_geometry_build(x(t), VelVertex, h_T)` then reproduces its whole interval.
5. **There are two transfer conventions, and both use the same kernel.**
   - Convention A, the current equal-step path: integrate the new connectivity, and transfer at t^n on pulled-back positions.
   - Convention B, required for the hierarchy: integrate the old (registry) connectivity over [s_T, t], then transfer at t on actual positions.
   - Phase 1 keeps A, which is the smallest change. Phase 2 needs B. Whether equal-step should also move to B is a decision point (D4).
6. **The hierarchy reuses the existing concentrated moving hierarchy.** The `RD_ALE_HIERARCHICAL` Campoli N path already implements the per-interval deposit (ΔA/3)U_i + (ΔA/6)dU_i − (h/2)(φ⁰+φ¹):
   - The `dg` step at about line 3048 of the solver.
   - The `area_gap` step at lines 5958–5980.
   - The static-hierarchy LDA corrector at lines 5894–5956 already supplies (M/3)(dU_i − β Σ_j dU_j).

   What is missing:
   - actual intervals instead of 2^bin;
   - a closure set taken from the registry;
   - the actual-interval live mask;
   - an exact geometric ledger instead of the non-conservative closing correction at lines 3079–3100;
   - the endpoint transfer.

---

## Phase 0 — Branch, provenance, literature and math report

**Goal:** a clean, reproducible starting point, and written proofs before any native code.

### Uncommitted work

The working tree on `develop_pureC_RD` holds the HLLC-RD, Rusanov and LDA/HLLC blend code that thesis results depend on:
- `/Users/zhenyuwu/arepo_rd/arepo/src/hydro/residual_distribution_solver.c` (+486 lines)
- The untracked headers `/Users/zhenyuwu/arepo_rd/arepo/src/hydro/rd_hllc.h`, `/Users/zhenyuwu/arepo_rd/arepo/src/hydro/rd_rusanov.h` and `/Users/zhenyuwu/arepo_rd/arepo/src/hydro/rd_lda_rusanov.h` (`rd_rusanov.h` and `rd_lda_rusanov.h` are untracked too, not only `rd_hllc.h`).
- Edits to `Makefile`, `defines_extra`, `proto.h` and `timestep.c`.
- The untracked `tests/rd/test_*` files and `examples/Sedov_2d/`, `examples/Sod_2d_Morton/`.

**Recommendation:** with the user's explicit approval, and using the commit convention in `dev_log/context.md`, commit this on `develop_pureC_RD` in three separate commits:
1. solver, headers, tests, Makefile, `defines_extra`, `proto.h`, `timestep.c`;
2. the two example directories (check them for large outputs first);
3. the dev_log documents.

Then create the new branch from that commit, for example `dev/flip-element-hierarchy`.

Do not try to carry an uncommitted diff into a new branch: the thesis Sedov/HLLC results currently cite source that is not in git history.

### Housekeeping in the first branch commit

- Add `test_hllc_positivity.py`, `test_lda_rusanov.py` and `test_lda_hllc_blend.py` to `check_rd` (only `test_rusanov_positivity.py` is listed now).
- Add `rd_hllc.h` and `rd_lda_rusanov.h` to `INCL`.
- Bring only the needed oracle files from the prototype branch with `git checkout test/colombo-re-explicit-hierarchy -- <path>`: `tests/rd/audit_euler_flip_closure.py`, `colombo_re_limited.py`, `euler_flip_closure_cases.json`, and `dev_log/colombo_re_spike/{euler_flip_closure,limited_operator}.md`. Do not merge the branch; its merge base, 315bece, is old.

### Frozen baselines

Before any edit:
- Record HEAD.
- Run `PYTHON=/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python make check_rd`.
- Build and hash about six reference binaries: Gresho N Campoli equal-step, Gresho LDA Campoli, KH B, Sedov HLLC (Arpaia), the Sedov LDA/HLLC blend, and Yee `RD_ALE_HIER_N_twobin`.
- Archive short runs under `../local_runs/flipdev_baseline_<date>/`.

These give the **flags-off bitwise gate**: with no new flags, every later commit must reproduce these logs and snapshots bitwise.

### Math report: `dev_log/RD_FLIP_ELEMENT_MATH_<date>.md`

Link it from log 3. It must prove:

- **P1 Defect identity.** D_P = Σ dm_i U_i = ∫(U_h^new − U_h^old). D_P = 0 for affine conserved fields. For a 2–2 flip it is the signed graph-tetrahedron volume, with dm = (−|bcd|, +|acd|, −|abd|, +|abc|)/3. Σ_P dm = 0 and Σ_P dm_i x_i = 0.
- **P2 Campoli budget identity.** Use Σ_T Φ_T(U) = Σ_T (ΔA_T/Δt) Ū_T, which follows from ΔA = Δt A_m div σ_h and Σ_T ∮U_hσ·n = 0, and holds for the Gauss3 contour, the N-reconciled contour and the HLLC/Rusanov trapezoid totals. From it derive Σ Q^{n+1} = Σ ĝ Û for both RK2 stages; this uses M_i = (ĝ_i + D_i)/2. Then conservation ⇔ Σ ĝ Û = Σ Q^n. Also derive the Arpaia residual term.
- **P3 High endpoint (uniform shift).**
  - It conserves, preserves uniform states, and is exact for affine fields.
  - It is the unique minimiser of Σ g⁺|ΔU|² subject to Σ g⁺ΔU = −D.
  - It attains the minimax bound |D|/Σ g⁺.
  - It is exactly invertible for a flip followed by its reverse at fixed positions: D_rev = −D, and G is unchanged.
  - **Lemma:** it lies inside the patch density hull relaxed by r_P = M_P/G, where M_P = Σ_receivers dm. So density positivity is automatic when ρ_max/ρ_min < 1 + 1/r_P. Pressure is the real risk; cite `/Users/zhenyuwu/arepo_rd/arepo/tests/rd/audit_flip_transfer_positivity.py`.
- **P4 Low endpoint (minimal transport).**
  - Donors keep their state.
  - Receivers become U_i + (dm_i/g_i⁺)(Ū_D − U_i), with Ū_D the |dm|-weighted donor average.
  - Distributed form: φ_i^L = dm_i(Ū_D − U_i), with Σφ^L = −D.
  - It conserves, keeps density inside the hull, keeps specific entropy ≥ the patch minimum (quasi-concavity), and is positive with no condition. It does not need g − a ≥ 0, which matters for vertices whose whole star changes.
  - The `full_patch` alternative from the prototype needs (g − a) clamped at round-off.
- **P5 Common-θ limiter.**
  - Admissible set: ρ ≥ κρ_min^P and ρe(U) ≥ κ(ρe)_min^P (concave), optionally K ≥ (1 − r_K)K_min^P. All three are convex.
  - The low endpoint satisfies them for κ ≤ 1.
  - So the accepted θ form an interval [0, θ*]. A per-node bisection with back-off, taking the minimum over nodes and then verifying all nodes, is valid.
  - Conservation holds for every θ.
  - Inputs that already satisfy the bounds give θ = 1, which keeps the affine-exactness.
- **P6 Campoli convex weights for lumped HLLC/Rusanov RD.**
  - a_i = M_i/D_i = ½ + Ŝ_i/(2S_i^{n+1}), b_i = 1 − Ŝ_i/(2S_i^{n+1}).
  - Positivity of the predictor needs Δt Σc_i ≤ S_i^{n+1}.
  - Positivity of the corrector needs Ŝ_i < 2S_i^{n+1} and Δt Σc_i ≤ 2S_i^{n+1} − Ŝ_i.
  - The same holds for the LDA/HLLC blend's low-order state.
- **P7–P9 (for Phase 2).**
  - The interval deposit reduces to equal-step.
  - Conservation at global synchronisation needs four conditions: time coverage; no trace or velocity change inside an open interval; the actual-interval live mask; and the edge argument (states constant and normals linear in time, so the midpoint rule is exact).
  - Positivity of interrupted lumped HLLC intervals follows from a per-vertex sub-interval CFL ledger, Σ_{T,k} h_k c_iT^k ≤ D_i, plus the (a, b) conditions for live vertices.
  - The geometric ledger at refresh equals Σ_star A_T(t)/3 exactly.

### Literature section

Cite only after checking each reference:
- Arpaia–Ricchiuto(–Abgrall) ALE RK-RD; Campoli et al. 2017, as cited in the code; Ricchiuto & Abgrall 2010 on explicit RK RD.
- Guardone/Isola/Quaranta/Re on edge swapping as fictitious-time deformation, and the Colombo–Re work used in the prototype.
- Loubère et al. 2010 (ReALE); Margolin & Shashkov and Kucharik & Shashkov on remapping.
- Zalesak and Kuzmin (FCT); Guermond–Nazarov–Popov–Tomas 2018 (convex limiting); Tadmor 1986 (minimum entropy principle).
- Osher–Sanders 1983, Dawson–Kirby 2001 and Krivodonova 2010 (conservative local time stepping); Springel 2010 (AREPO).
- Guibas kinetic Delaunay, for Phase 3.

**Gate:** the report is reviewed, the new flags are listed in a planning section of log 3, and `check_rd` passes.

---

## Phase 1 — Equal-step: Campoli baseline, exact cavities, flip transfer, primitive fix

### 1A. Pure kernels and Python tests first (no AREPO dependency)

**New `/Users/zhenyuwu/arepo_rd/arepo/src/hydro/rd_flip_transfer.h`** (header guard `RD_FLIP_TRANSFER_H`; includes `rd_rusanov.h`):
```c
struct rd_flip_options { double gamma, floor_fraction, entropy_relax; int low_endpoint, entropy_bound; };
struct rd_flip_report  { double theta, defect[4], max_dU, min_rho, min_internal; int high_ok, low_ok, backoffs; };
static int rd_flip_transfer(int n, const double *g, const double *dm, const double *a /*full_patch only*/,
                            double (*q)[4], const struct rd_flip_options *, struct rd_flip_report *);
```
- Internal pieces: `rd_flip_high`, `rd_flip_low_minimal`, `rd_flip_low_full_patch`, `rd_flip_point_ok`, `rd_flip_common_theta`.
- `rd_flip_common_theta` uses the same bisection, geometric back-off and final verification as `rd_lr_limit_bounds`, but with κ floors and an internal-energy-density floor.
- Return codes: imbalance (|Σdm| > tolerance), inadmissible input, non-finite values.

**New `/Users/zhenyuwu/arepo_rd/arepo/src/hydro/rd_topology_core.h`** (pure):
- Key construction and comparison: CCW storage, sorted comparison key.
- Union-find over local vertex indices.
- Per-cavity accumulation of (node, a, b) in CSR form from coordinates in a cavity-local embedding: anchor = the cavity's smallest-ID vertex, others at anchor + nearest-image offset. Both the old and new triangle areas are computed from these same coordinates, so Σ_P dm = 0 to area-formula round-off.

**Tests** (ctypes pattern from `/Users/zhenyuwu/arepo_rd/arepo/tests/rd/test_hllc_positivity.py`, all added to `check_rd`):

`tests/rd/test_flip_transfer.py`:
- An independent NumPy oracle.
- Conservation ≤ 1e-15 relative.
- Uniform states unchanged; affine fields give θ = 1 and identity.
- Flip/reverse invertibility when θ = 1 both ways.
- Minimax equality.
- Low-endpoint properties: donors fixed; receivers in the convex hull; K ≥ min.
- Random adversarial cases: contrasts up to 1e4, |v| up to 20, near vacuum.
- The square-diagonal hot/cold counterexample from log §159: the high endpoint is inadmissible, θ < 1, and the output is admissible.
- k-gon cavities, zero-dm nodes, and cavities merged at a shared vertex.
- The one-ulp back-off case from the prototype.

`tests/rd/test_flip_cavity.py`:
- SciPy periodic Delaunay before and after random motion.
- Cavities agree with a brute-force symmetric difference.
- Σdm = 0 and Σdm·x = 0.
- Every vertex with nonzero dm lies in some cavity.
- The edge ≥ L/2 and duplicate-key guards fire on a tiny box.

`tests/rd/test_campoli_lumped_positivity.py`:
- The P6 weights and the convex corrector decomposition, compiled against `rd_hllc.h` and `rd_rusanov.h` on random moving triangles.
- An algebraic check of the P2 identity in a small P1 model with a flip, for lumped, F1-like (zero-sum) and B temporal terms.

### 1B. Campoli for all schemes, plus the primitive-refresh fix

These are two separate commits.

**Guards in `/Users/zhenyuwu/arepo_rd/arepo/src/hydro/residual_distribution_solver.c`:**
- Remove `RD_ALE_CAMPOLI_MASS` from the `RD_RUSANOV_LOW_ORDER` exclusion (lines 62–68).
- Remove it from the `RD_BLEND_LOW_HLLC` exclusion (lines 101–108). Replace the `RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC` exclusion there with "allowed only with `RD_ALE_FLIP_TRANSFER`".
- No kernel change is needed. The existing `a = rd_rus_coeff[NumGas+i]/DualArea`, `b = 1.5 − a` checks (lines 6312–6339) and the `rd_lr_mass` checks (6178–6188) already become the Campoli weights once `tri_normals_list.area = (A0+A1)/2` (line 2703) and `DualArea = Σ A_new/3`.
- Add `a`, `b` and margin statistics to the `RD-RUSANOV` line.

**`rd_ale_finish_step`** (lines 2797–2852): under Campoli, assert `ale_divisor[i] == ale_endpoint_area[i]` bitwise and skip the Q rebase. `rebase_change` is then identically 0.

**Primitive-refresh bug:** generalise the Rusanov-only block at lines 2760–2777 into `static void rd_refresh_primitives_from_u(int i, const double u[4])`. It sets Density, Vel, Utherm, Pressure and Csnd, applies no floors, terminates on an inadmissible state, and leaves VelVertex alone. Call it for every changed node in every scheme. Under `RD_DEBUG_ASSERTS`, add a stage-0 check that |Q/DualArea − U(primitives)| is at round-off for all nodes; this catches this class of bug.

**Cheap, high-value early experiment:** re-run the old KH repair (log §21–23) with only the refresh fix. The −20.6% E_ky change was measured with predictor primitives that did not match `RD_Ustage0`, so part of it may be this bug and not the repair itself.

**Gates:**
- Flags-off runs bitwise equal the Phase 0 binaries.
- σ = 0 runs still give `static_bit_mismatch = 0`.
- Campoli vs Arpaia (no flip handling) on Yee, Gresho and Sod for N, LDA and B: differences are O(Δt²), and conservation is at round-off whenever no flips occur.
- HLLC-RD Sedov and the LDA/HLLC blend under Campoli pass every stage CFL, a and b check.

### 1C. Exact cavities, detection only

**New `/Users/zhenyuwu/arepo_rd/arepo/src/hydro/rd_topology.c` and `rd_topology.h`:**
- `rd_topology_capture(tessellation *T)` stores owned triangles as CCW ID triples with plain `malloc`, since the store persists outside the mymalloc stack.
- `rd_topology_diff(tessellation *T, double pullback_dt, struct rd_cavity_set *out)` does an O(n log n) sort-merge, unions vertices of changed triangles, and accumulates cavity a/b at pulled-back coordinates.
- `rd_cavity_set_free()`.
- It replaces the O(changed²) pairwise unions and the O(patch × NumGas) arrays of `rd_ale_exact_patch_diagnostic` (lines 1918–2260). Leave that old diagnostic frozen for provenance.

**Hook in `/Users/zhenyuwu/arepo_rd/arepo/src/main/run.c` (lines 278–283):** call the capture under `RD_ALE_EXACT_PATCH_DIAGNOSTIC || RD_ALE_FLIP_TRANSFER`. Declare it in `/Users/zhenyuwu/arepo_rd/arepo/src/main/cpp_functions.h`.

**Integrity checks logged per step:**
- Each cavity has ≥ 1 removed and ≥ 1 inserted triangle.
- |Σ_P dm| and |Σ_P dm·x| at round-off.
- Completeness: max over non-cavity vertices of |ĝ_i − g_i|/g_i is at round-off.
- A histogram of cavity sizes: 4 nodes means an isolated 2–2 flip; more means a cascade.

**Gate:** zero integrity failures on Gresho, KH, Sod and Sedov runs; report how the exact cavities map onto the old support patches.

### 1D. Applying the transfer

In `rd_ale_prepare_step`, replace the call at lines 2758–2778 with `rd_ale_apply_flip_transfer(T, set)`:
1. g = `DualArea`, q = g·`ale_uold`, dm from the cavity.
2. Run the kernel per cavity.
3. Set `ale_uold` = q′/(g + dm).
4. Call `rd_refresh_primitives_from_u` for cavity nodes.
5. The existing loop then sets Q := divisor·`ale_uold`.

**Budget line** `RD-FLIP time= cavities= max_nodes= removed= inserted= D_total=[4] theta_min/mean limited= low_used= transfer_change=[4] pullback_roundoff=[4]`, where pullback_roundoff = Σ(ĝ^pb_i − g⁺_i)Û_i.

**Extend `RD-ALE-FINISH`** with `sweep_identity = ΣQ^{n+1} − Σĝ^pb Û`. The step's total change must equal transfer + pullback_roundoff + sweep_identity, and every term must be at round-off.

**First run high-only** (`RD_FLIP_LIMITER=0`: abort if the high endpoint is inadmissible), then enable the limiter.

### 1E. Native gates

Each gate uses frozen source, its own `BUILD_DIR`, executable and `OutputDir`, `OMP_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1`, and is archived under `local_runs`.

- **N1 compile matrix:** Campoli × {N, LDA, B, HLLC, LDA/HLLC blend} × `FLIP_TRANSFER` all build. Illegal combinations fail to compile: Arpaia + transfer; transfer + old repair; transfer with more than one rank (runtime check).
- **N2 uniform state with flips:** the Gresho `uniform_flip_cam` parameters from the prototype branch, plus a new test policy `RD_ALE_TEST_MESH_MOTION` in `/Users/zhenyuwu/arepo_rd/arepo/src/mesh/set_vertex_velocities.c`, next to `RD_ALE_TEST_ZERO_MESH_VELOCITY`. Modes: (1) oscillating shear that flips and then un-flips; (2) small jitter giving isolated flips; (3) large jitter giving cascades. Pass: max_dU ≤ 1e-14, conservation ≤ 1e-14, events > 0.
- **N3 stationary contact** (pressure equilibrium, zero velocity) under motion modes 1 and 3: an exact steady state, so any change is error. Compare transfer, no transfer and the old repair; report conservation, positivity, and the drift norm after one mesh period.
- **N4 Yee:** glass48, glass96 and, if affordable, glass192. Report L1 errors, θ statistics and event counts. The transfer-minus-no-transfer difference should scale as about h² (P1 argument: per-event perturbation O(h²) at O(1) events per vertex per unit time).
- **N5 Gresho and Sod (Morton glass):** profile L1 errors, conservation, positivity.
- **N6 KH to t = 10, glass48 and glass96:** mass and energy drift at round-off (was 2.5e-3 without repair, 6.9e-6 with the old Arpaia repair); E_ky growth; entropy excursion. Show how the E_ky change scales with resolution.
- **N7 Sedov** (21-point and 130-point; HLLC-RD Campoli and the LDA/HLLC blend Campoli; both failed with the old repair): must reach t = 0.05 with conservation at round-off and positivity; report θ<1 counts; compare profiles with no-repair Arpaia.

**Decision D2 (limiter defaults):** start with κ = 0.5 and the entropy bound off. Record sensitivity for κ ∈ {1e-12, 0.1, 0.5} and with the entropy bound on.
- Risk: in the isentropic Yee vortex, a hard K bound would activate on almost every flip.
- Turn the entropy bound on by default only if the KH entropy excursions require it and the Yee L1 cost is negligible.

---

## Phase 2 — Moving hierarchy with actual-interval closure (convention B)

### 2A. Persistent registry as the RD element set, no events yet (N only)

**Registry record:** CCW IDs; `integertime birth, s_T`; a flags byte. It lives in a sorted array with `malloc`/`realloc`.

**New functions in `rd_topology.c`:**
- `rd_registry_init(tessellation*)`: called after the setup `create_mesh` in `run.c` (about lines 108–118), with s_T = birth = Ti_Current.
- `rd_registry_view(...)`: builds a **synthetic tessellation** (DP = three points per triangle with x, y, ID, task = ThisTask, index = originalindex = local index; DT.p). `compute_residuals`, `rd_build_element_set`, `rd_simplex_claimed` and `triangle_get_normals_area` then run unchanged; the latter reads only DP.x and DP.y.
- `rd_registry_star_csr(...)`: vertex → triangle adjacency.

**New flag `RD_ALE_INTERVAL_HIERARCHY`.** It requires `RD_HIERARCHICAL_TIMESTEPS`, `RD_RK2_TOTAL_RESIDUAL`, `CREATE_FULL_MESH` and `RD_ALE_CAMPOLI_MASS`. It excludes `RD_ALE_HIERARCHICAL`, `RD_ALE_EQUALSTEP` and `RD_ALE_HIERARCHICAL_ARPAIA`. Schemes are enabled one sub-phase at a time behind `#error`.

**Changes to the existing concentrated path:**
- `set.active` = membership of the closure set C.
- Per-element `h_T = (Ti_Current − s_T)·Timebase_interval`, carried in `set`, replacing `2^bin` at lines 4245 and 2996.
- Live mask `SphP.RD_PredictorLive` (new field, mirrored in PrimExch in `/Users/zhenyuwu/arepo_rd/arepo/src/mesh/mesh.h` and in the exchange at `/Users/zhenyuwu/arepo_rd/arepo/src/mesh/voronoi/voronoi_exchange.c` lines 294–299 and 413–418). It replaces `rd_point_stage_live` and the `RD_StarTimeBin` star context (lines 492–619). Rule: P_i = [every old-star triangle is in C] ∧ [all have equal s_T].
- Predictor normalisation by m_i(t) = Σ_star A1/3, replacing `DualArea` at line 6367.
- `RD_GeoLedger` becomes the exact running ledger.
- **Delete the closing correction** at lines 3079–3100 (it is not conservative). At refresh, assert instead that |RD_GeoLedger − Σ_star A_T(t)/3| ≤ 1e-12 relative, then set DualArea := ledger.
- New fields `RD_LastRefresh` (integertime) and `RD_CFLLedger`.

**Invariants asserted:**
- s_T ≥ birth.
- s_T ≥ the last refresh of each of the triangle's vertices.
- At a refresh, every star triangle has s_T == t.
- All gas particles have Ti_Current == All.Ti_Current.
- Signed area stays positive over the whole quadratic trajectory on [s_T, t].
- At global synchronisation: ΣQ equals the initial total, and Σ g equals the box area.

**Gates:**
- **H1:** with `FORCE_EQUAL_TIMESTEPS` and no flips, results match `/Users/zhenyuwu/arepo_rd/arepo/examples/yee_2d/Config_RD_ALE_N_CAMPOLI_equalstep_ref.sh` to ≤ 1e-13 relative. This is not bitwise, because coordinates are minimal-image instead of DP images and the summation order differs.
- **H2:** two bins with σ = 0 match the static N hierarchy to round-off.
- **H3:** the two-bin `RD_HIERARCHICAL_TEST_PATTERN` Yee case with motion but no flips conserves to ≤ 1e-14 at global synchronisations.

### 2B. Events with forced closure and the endpoint transfer (N)

All of this happens in `rd_step_end` at a fine synchronisation time t:
1. Diff the registry against the new DT to get retained, dying and newborn triangles and the cavities.
2. C = naturally due triangles (min-bin synchronised) ∪ the entire old star of every cavity vertex.
3. Live mask; predictor and corrector sweeps over the synthetic view; set s_T = t on C.
4. Refresh set R = naturally synchronised vertices ∪ cavity vertices. Assert coverage and that the ledger is exact.
5. Same-time transfer per cavity: g = old-star area at t; dm from current positions; kernel from Phase 1.
6. Assert g⁺ equals the new-star area; update traces.
7. Commit the registry: remove dying triangles; insert newborn ones with s_T = birth = t.
8. Side-effect-free primitive refresh for forced vertices, which are not in AREPO's active list. Their timebin and VelVertex do **not** change, so no change to AREPO's timestep machinery is needed.

**Negative controls** must fail their assertions, as in the Python campaign (`RD_ALE_INTERVAL_NEGCTRL=1`, `2`, `3`): close only dying triangles; use the bin-live rule; make every fully closed vertex live.

**Gates:**
- **H4:** uniform state under motion modes 1–3 with 3–7 bins, exact.
- **H5:** Yee, Gresho, Sod and KH with the test pattern and with natural tree-based bins:
  - conservation at global synchronisations ≤ 1e-14;
  - element-work counts compared with all-fine stepping;
  - L1 errors compared with equal-step at the same finest Δt.
- **H6:** native vs oracle replay on a 16² jittered mesh with the ported `audit_euler_flip_closure.py`, a few steps, agreement ≤ 1e-12.

### 2C. LDA (F1 interval algebra)

Reuse the frozen-dU F1 corrector (lines 5894–5956) with per-element h_T and M_T = (A0+A1)/2; the rank-deficient case falls back to lumped. Remove the N-only `#error` for LDA.

**Gates:** equal bins reproduce equal-step-B; σ = 0 two-bin matches the static LDA hierarchy; Yee convergence with the known frozen-F1 limitation from log §33 reported, not hidden.

**Decision D5:** if accuracy degrades at bin interfaces, the thesis claims the moving hierarchy for N, B and HLLC, and states LDA as a limitation.

### 2D. B scheme

Per-element θ from the interval total residual. The concentrated closure means stage-0 N and LDA are both available inside the same call, so no persistent per-triangle storage is needed. Conservation holds for any θ.

Lift the `#error` at lines 332–334 only for `RD_ALE_INTERVAL_HIERARCHY`.

### 2E. HLLC-RD (lumped)

Same N deposit with the HLLC kernel. Add the per-vertex `RD_CFLLedger` = Σ h_k·coeff_iT, checked ≤ D_i at refresh, plus the (a, b) checks for live vertices (proof P8). Gate on Sedov with the test pattern.

**Stretch / out of scope:** the LDA/HLLC blend inside the hierarchy. Its limiter needs refresh-time states, which partial ledgers do not provide.

### 2F. Decision D4: unify the conventions

Should the thesis equal-step path become the interval hierarchy with `FORCE_EQUAL_TIMESTEPS` (one code path, bitwise equal-bin gate)? Decide by comparing A and B on N4–N7: conservation must hold for both, and the difference should shrink with resolution.

---

## Phase 3 — Lazy flipping (scoped experiment)

**Start only if** one of these holds after Phases 1 and 2:
- the E_ky change or the stationary-contact drift does not shrink from glass48 to glass96;
- θ < 1 occurs often in smooth flows;
- forced closures add more than about 50% extra element work.

**Method: cavity-selective adoption.** Keep the registry as the RD triangulation. Adopt a cavity from the diff against the DT only if:
- an old triangle in it would invert, or fall below a quality threshold, within the next step; or
- its Delaunay violation (opposite-angle sum − π) exceeds δ.

Unadopted cavities keep the old connectivity. This is valid because cavities are disjoint polygons with unchanged boundaries. No Lawson-flip code is needed, and flip/unflip flicker on near-cocircular quads, such as jittered Cartesian ICs, simply disappears.

The RD CFL must then be computed from the registry view rather than the DT.

**Success criteria:** at least 3× fewer events, with accuracy no worse and the minimum triangle quality bounded.

---

## Decision points

- **D1:** commit the HLLC work first (recommended).
- **D2:** limiter defaults.
- **D3:** if the transfer effect does not converge with resolution, try a 1-ring halo for the high endpoint (`RD_FLIP_HIGH_HALO`): it reduces the L∞ change while keeping the L1 change at |D|. Otherwise go to Phase 3.
- **D4:** convention unification.
- **D5:** scope of the LDA hierarchy claim.
- **D6:** Phase 3 go or no-go.

## Main risks

- **Inverted triangles.** Pulled-back triangles (A) or pushed-forward ones (B) can invert; coarse intervals make B worse. Check positivity over the whole interval, abort with a diagnostic, and never extrapolate.
- **Periodic images.** Handled by the edge < L/2 and duplicate-key aborts.
- **Domain decomposition reorders particles on one rank.** The registry depends only on IDs; rebuild the ID → index map every step.
- **Forced refresh does not wake coarse bins.** Positivity is checked through the CFL ledger, with no bin changes.
- **Exact cocircularity on lattice ICs** causes flicker.
- **Restarts happen mid-step** (between the begin and end hooks). Terminate if `RestartFlag` is set with the new flags; registry restart is out of scope.
- **mymalloc LIFO discipline** for per-step scratch arrays.
- **The frozen F1 operator** limits LDA accuracy in the hierarchy.
- **Positivity proofs cover only lumped low-order kernels.** For N, LDA and B, positivity is checked at runtime only and must not be claimed.

## Out of scope

MPI; refinement and derefinement (insertion and deletion would be other degenerate-element types); 3D; gravity; reflective boundaries; restarts; the LDA/HLLC blend in the hierarchy; exact continuous event times; redesigning mesh regularisation; wall-clock speed-up claims (report element-work counts only); thesis edits unless requested.

## Rough effort for one developer

| Phase | Estimate |
|---|---|
| 0 | 1–2 days |
| 1 | 2–3 weeks |
| 2 (N, 2A–2B) | about 3 weeks |
| 2C–2E | 2–3 weeks |
| 3 | 1–2 weeks |

### Critical Files for Implementation
- /Users/zhenyuwu/arepo_rd/arepo/src/hydro/residual_distribution_solver.c (guards 55–129 and 183–334; `rd_ale_prepare_step`/repair call 2563–2793; `rd_ale_finish_step` 2797–2852; `rd_ale_hierarchical_prepare` 2952–3163; hierarchy paths in `compute_residuals` 4027–4039, 4456–4492, 5894–5980, 6111–6124, 6353–6403)
- /Users/zhenyuwu/arepo_rd/arepo/src/main/run.c (capture hook 278–283, rebuild 342–349, `rd_step_end` 365–371, setup mesh about 108–118)
- /Users/zhenyuwu/arepo_rd/arepo/src/hydro/rd_lda_rusanov.h and /Users/zhenyuwu/arepo_rd/arepo/src/hydro/rd_rusanov.h (bisection, back-off and admissibility patterns to reuse in the new `rd_flip_transfer.h`)
- /Users/zhenyuwu/arepo_rd/arepo/src/main/allvars.h (SphP RD fields 1349–1370) with /Users/zhenyuwu/arepo_rd/arepo/src/mesh/mesh.h and /Users/zhenyuwu/arepo_rd/arepo/src/mesh/voronoi/voronoi_exchange.c (PrimExch mirrors)
- /Users/zhenyuwu/arepo_rd/arepo/Makefile and /Users/zhenyuwu/arepo_rd/arepo/defines_extra (new objects and headers, `check_rd` tests, flag and header-guard registration)

New files to create: `/Users/zhenyuwu/arepo_rd/arepo/src/hydro/rd_flip_transfer.h`, `/Users/zhenyuwu/arepo_rd/arepo/src/hydro/rd_topology_core.h`, `/Users/zhenyuwu/arepo_rd/arepo/src/hydro/rd_topology.c` and `rd_topology.h`, and `/Users/zhenyuwu/arepo_rd/arepo/tests/rd/test_flip_transfer.py`, `test_flip_cavity.py` and `test_campoli_lumped_positivity.py`.
