# Conservative edge flips, a conservative moving-mesh hierarchy and lazy flips for P1 ALE residual distribution — progress report for review

- **Author:** Claude Code (Opus 5.5), for Zhenyu Wu.
- **Written:** 2026-10-09, for independent review (Codex).
- **Branch:** `feature/ale-flip-conservation-hierarchy`. Base `eacc3f9` (the committed `develop_pureC_RD` snapshot). Head at the time of writing: `8e325e9` plus this report.
- **Scope:** 2D, periodic, one MPI rank. The thesis has not been edited.
- **Companion documents:**
  - Design and mathematics notes: [RD_FLIP_ELEMENT_AND_MOVING_HIERARCHY_DESIGN_20261008.md](RD_FLIP_ELEMENT_AND_MOVING_HIERARCHY_DESIGN_20261008.md).
  - Implementation plan: [RD_FLIP_HIERARCHY_IMPLEMENTATION_PLAN_20261008.md](RD_FLIP_HIERARCHY_IMPLEMENTATION_PLAN_20261008.md).
  - Running results notes, superseded by this report: [RD_FLIP_HIERARCHY_RESULTS_20261009.md](RD_FLIP_HIERARCHY_RESULTS_20261009.md).
  - Log entries: log3 §§217–222.

This report is self-contained. Section 9 lists the points that most need an independent check.

---

## 1. Summary

The thesis moving-mesh RD (explicit ALE RK2 with Arpaia mass) loses conservation in two places:

1. **The edge-flip defect.** Between steps AREPO rebuilds the Delaunay mesh. A connectivity change alters the lumped P1 masses of the affected vertices while their nodal states are kept. The stored total therefore changes.
2. **The Arpaia endpoint conversion.** The RK2 update conserves Σ D_i U_i, where D is a temporary divisor. AREPO stores Q = S^{n+1}U, and S^{n+1} ≠ D.

In the thesis, the Sedov HLLC-RD run drifts by −0.33 % in mass and +0.70 % in energy. The bounds-limited LDA/HLLC blend loses up to 6.4 % of its energy. The old uniform-shift repair conserved, but it aborted on negative pressure in Sedov. In KH it changed the E_ky peak by tens of per cent, and it fed stale primitives to N/LDA/B.

What is now implemented:

| Feature | Flag | Schemes | Status |
|---|---|---|---|
| Campoli mass in every equal-step path | `RD_ALE_CAMPOLI_MASS` (existing flag; newly allowed for HLLC/Rusanov and the LDA/HLLC blend) | N, LDA, B, HLLC-RD, blend | done |
| Conservative, positivity-limited flip transfer | `RD_ALE_FLIP_TRANSFER` | same | done; frozen gates pass |
| Primitive refresh after topology changes | always on; `RD_ALE_REPAIR_STALE_PRIMITIVES` restores the old behaviour for comparison | N, LDA, B | bug fix |
| Moving-mesh hierarchy with actual-interval closure | `RD_ALE_INTERVAL_HIERARCHY` (requires `RD_ALE_HIERARCHICAL` and Campoli) | N, LDA, B, HLLC-RD | done; frozen gates pass |
| Lazy (cavity-selective) flips | `RD_ALE_LAZY_FLIP` (requires the interval hierarchy) | all of the above | done; frozen gates pass |
| Receiver-only high endpoint | `RD_FLIP_HIGH_MODE=1` | kernel option | **default since `8e325e9`** |

Main results (all frozen, one rank, `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1`):

- **Round-off conservation.** Every run with the transfer conserves mass, momentum and energy to ≤2e-14, for every scheme and problem: uniform, Sod, Yee 48/96, KH 48/96 and Sedov 1/21-point. This includes the hierarchy with mixed and natural bins and up to 4×10⁵ flip cavities. The same runs without the transfer drift by 1e-5 to 3.5e-3.
- **Sedov positivity.** HLLC-RD and both LDA/HLLC blends reach t = 0.05 with p > 0. The limiter acts (θ < 1) in about 2 % of cavities.
- **Accuracy cost.** In smooth flow (Yee) the transfer − no-transfer difference falls by 2.5–3.8× from glass48 to glass96, i.e. about second order. In KH at glass48/96 it stays below the discretisation error (§7.4).
  - The receiver-only high endpoint avoids the entropy excursion that the uniform shift creates in KH.
  - In Yee and Sod the two high endpoints are indistinguishable.
  - In Sedov the receiver-only endpoint gives a ≈1 % lower density peak at an unchanged shell radius.
- **Hierarchy.**
  - With equal bins it reproduces equal-step Campoli to ≈4e-15 for N, LDA and B (HLLC: before the first flip).
  - Sedov with natural bins (dt ratio up to 128): element work 7–8 % of all-fine stepping, RD CPU 17–37× lower, profiles within L1 ≈ 1e-3 of equal-step.
  - Wall-clock gain is only ≈1.4×, because AREPO rebuilds the full Delaunay mesh at every synchronisation.
  - Across bin interfaces LDA and B degrade to first order (+4–5 %, or +20–32 % when the interface crosses the vortex). N does not.
- **Lazy flips.** 3–4× fewer adopted cavities at unchanged accuracy, conservation and positivity. No deferred triangle went below 15°.

---

## 2. Background and literature (short)

Full survey: design notes §7. Points relevant here:

- **Conservative remap at topology changes.**
  - Swept-region or intersection remaps: Margolin & Shashkov; Kucharik et al.; Alauzet & Mehrenberger 2010.
  - Edge-flip-specific "volume inconsistency" corrections with donor states: Steinberg, Yalinewich & Sari 2016.
  - Bound-preserving and convex limiting: Zalesak; Kuzmin et al. 2010; Guermond et al.
- **Topology changes inside RD/ALE time stepping.**
  - Colombo & Re (2022): explicit/implicit ALE RD with local mesh adaptation (swap, insertion, collapse). Topology changes act through "ghost" elements carrying a pure volume-change residual. They use local adaptation of a continuously deforming mesh, not a full Delaunay rebuild.
  - Gaburro et al. (2020): high-order ALE on moving Voronoi meshes. Topology changes are handled by space-time "sliver" elements.
- **Space-time RD** (Csík & Deconinck; Ricchiuto, Csík & Deconinck; Hubbard, Ricchiuto & Sármány) handles moving meshes with fixed connectivity per slab, with implicit slab coupling. We judged it impractical for AREPO's explicit loop; the user agreed.
- **No published scheme was found that combines local time stepping with mid-step reconnection** on a moving Delaunay mesh. The interval hierarchy below is, to our knowledge, new.

The flip element of §3.3 is the explicit, same-time, zero-width limit of a space-time sliver or ghost element. Its residual is the defect D_C, distributed with an RD-style blend of a linear-exact and a positive scheme.

---

## 3. Mathematics

### 3.1 The ALE step on fixed connectivity: Arpaia and Campoli

**Setup.**
- Within a step [tⁿ, tⁿ⁺¹] the connectivity is fixed and each vertex moves linearly with its mesh velocity.
- Each node stores Q_i = S_i U_i, where S_i = Σ_{T∋i} |T|/3 is the median-dual (lumped P1) mass.
- A triangle's signed area is quadratic in time:

  A(s) = A_old + c₁ s + c₂ s², s ∈ [0, 1],

  with c₂ = Δt² · ½ (w₁ − w₀) × (w₂ − w₀).
- Fluxes use midpoint normals. Edge normals are linear in time under linear vertex motion, so midpoint normals integrate them exactly. This gives the discrete GCL: a uniform state is preserved.

The RK2 total-residual update uses two area weights per triangle: the temporal (mass-matrix) mass M_T and the divisor D_T. The divisor converts the accumulated extensive update back into U. D_i = Σ_{T∋i} D_T/3.

| | M_T | D_T |
|---|---|---|
| Arpaia (thesis default) | A_mid | A_mid + (A_new − A_old)/2 |
| Campoli (`RD_ALE_CAMPOLI_MASS`) | (A_old + A_new)/2 | A_new |

Since A_mid − (A_old + A_new)/2 = −c₂/4, the two variants differ only by replacing the midpoint area with the trapezoidal mean in both weights. D_T − M_T = (A_new − A_old)/2 is identical in both. Both are second order.

**Conservation.**
- *Campoli.* For a no-flip Campoli slab, the contour-residual and mass column sums satisfy 1ᵀR = aᵀU and 1ᵀM = bᵀ, with a = (s₁ − s₀)/h and b = (s₀ + s₁)/2. The two-pass RK2 endpoint balance then cancels exactly: Σ_i S_iⁿ⁺¹ U_iⁿ⁺¹ = Σ_i S_iⁿ U_iⁿ.
  - Derivation: log3 §27 and its linked report. It was verified on a 2304-node periodic mesh to 4.65e-14, and in every no-flip Campoli control.
  - Storage and divisor coincide, so nothing more happens at the end of the step.
- *Arpaia.* The update conserves Σ D_i U_iⁿ⁺¹. Converting to storage changes the total by Σ_i (S_iⁿ⁺¹ − D_i) U_iⁿ⁺¹, with D_T − A_new = −c₂/4. This term is non-zero whenever the flow is non-uniform and the mesh deforms.

**Why we switch to Campoli.**
1. It removes one of the two leaks, leaving flips as the only one.
2. Its per-interval geometric increments (A_new − A_old)/3 telescope exactly to the actual current dual area of a vertex once its star closes, however the intervals of its triangles are split. The hierarchy (§3.5) relies on this.
3. Accuracy is unchanged in every comparison. Sedov HLLC with Campoli and no transfer equals the thesis Arpaia run to L1 = 1.4e-6. So in Sedov the conversion leak is negligible and the flips cause the whole thesis drift.

The Arpaia form remains the standard published derivation. Campoli is an equivalent second-order choice of the two area weights.

### 3.2 The flip defect

Take a connected changed cavity C. It is a connected component of the vertices of triangles that appear in only one of the old and new triangulations, and may contain several flips. Let a_i and b_i be the old and new lumped masses of vertex i inside C, and δm_i = b_i − a_i. Keeping U_i unchanged changes the represented total by

  D_C = Σ_{i∈C} δm_i U_i = ∫_C (U_h^new − U_h^old) dA.

**Identities.** Both triangulations tile the same polygon and both P1 bases reproduce affine functions, so

  Σ δm_i = 0 and Σ δm_i x_i = 0.

Hence D_C = Σ δm_i (U_i − L(x_i)) for every affine L. D_C vanishes for affine fields and is O(Σ|δm| h² |∇²U|) otherwise.

**Single 2-2 flip.** In the quad abcd, diagonal ac becomes bd:
- δm = (−|bcd|, +|acd|, −|abd|, +|abc|)/3;
- D is the signed volume of the "flip tetrahedron" spanned by the points (x_i, U_i);
- on a square of side h with a quadratic field U = ½ xᵀHx, D = −H_xy h⁴/6.

So every nodal state of the cavity changes by O(h² U″). The number of flips per vertex per unit time in a shear flow does not depend on h, so the accumulated perturbation is O(h²).

### 3.3 The flip element (`src/hydro/rd_flip_transfer.h`)

**Notation.**
- g_i: full nodal mass before the change (`DualArea`).
- g_i⁺ = g_i + δm_i: full nodal mass after the change.
- Donors: δm_i < 0. Receivers: δm_i > 0.
- R = Σ_receivers δm_i = Σ_donors |δm_i|.

We seek U_i⁺ with Σ g_i⁺ U_i⁺ = Σ g_i U_i.

**High endpoint, mode 0 (uniform shift):** U_i^H = U_i − D_C / Σ_j g_j⁺.
- *Minimal max norm.* Any conservative ΔU has Σ g⁺ ΔU = −D_C, so max|ΔU| ≥ |D_C| / Σ g⁺, with equality only for the uniform shift.
- *Minimal lumped L2 norm.* Minimising Σ g⁺ ΔU² under the same constraint gives ΔU = const (Lagrange).
- Linear-exact, and invertible at fixed time.
- **Not** convex: it can be inadmissible at strong contrasts (for example, Sedov p = −0.019).

**High endpoint, mode 1 (receiver-only; default since `8e325e9`).**
- Donors keep U_i bit-for-bit.
- Receivers take Q_i⁺ = g_i U_i + δm_i (Ū_D + U_i − Ū_R), where Ū_D and Ū_R are the |δm|-weighted donor and receiver means.
- Equivalently ΔU_i = −(δm_i / g_i⁺)(D_C / R) on receivers.
- It conserves, since Σ_rec δm_i (Ū_D − Ū_R) = −D_C. It is linear-exact, because D_C = 0 implies Ū_D = Ū_R. Its extensive L1 change is |D_C|, the same as mode 0. It concentrates the change on the vertices that physically received area.

**Low endpoint (donor-cell, minimal mixing).**
- Donors keep U_i.
- Receivers take U_i^L = (g_i U_i + δm_i Ū_D) / g_i⁺.
- For one 2-2 flip this is exactly the edge donor-cell exchange along the quad edges (design notes §3). Properties:
  - it conserves;
  - each new state is a convex combination of old states, so it is admissible (the set {ρ > 0, e > 0} is convex);
  - density stays inside the cavity hull;
  - the specific entropy stays ≥ the input minimum (K = p/ρ^γ is quasi-concave in the conserved variables).

**Blend.**
- Q^θ = (1 − θ) Q^L + θ Q^H, with one θ ∈ [0, 1] per cavity for all components. This keeps conservation exact for every θ.
- θ is the largest value with every node satisfying:
  - ρ > κ min ρ and e > κ min e (floor fraction κ = `RD_FLIP_FLOOR_FRACTION`, default 0.5);
  - optionally, the relaxed density hull (`RD_FLIP_DMP_RELAX ≥ 0`; default off);
  - optionally, K ≥ min K (`RD_FLIP_ENTROPY_BOUND`; default off).
- The admissible θ form an interval [0, θ_max]. θ = 1 is tried first. Otherwise 60 bisection steps run on the actual floating-point states, keeping the last verified value.
- The low endpoint is checked first, positivity only. If it fails, the inputs are inconsistent and the code terminates (`RD_FLIP_BAD_LOW`); it never floors silently.
- Round-off allowance: the internal energy is known only to a few ulp of E, so the checks allow 8 ε|E|.

### 3.4 Where the transfer acts in the equal-step step ("convention A")

Implemented in `rd_ale_apply_flip_transfer`, called from `rd_ale_prepare_step`.

1. **Old triangles.** The owned triangles of the mesh at tⁿ are captured, with their keys, just before AREPO frees it (`rd_ale_topology_capture_old_mesh`, hook in `run.c`). A key is the sorted particle-ID triple.
2. **New triangles.** After the rebuild, the new triangles are pulled back to xⁿ along the step's linear trajectories, so that both triangulations are compared at the same positions.
3. **Cavities.** A sort-merge of the two key lists, followed by union-find over the vertices of changed triangles, gives the cavities. Outside them, |pullback mass − DualArea| ≤ 1e-10 relative is asserted.
4. **Transfer.** On each cavity, g = DualArea, δm = pullback − DualArea and U = `ale_uold` are passed to the kernel. The cavity totals must be conserved to ≤1e-12, which is asserted. Primitives are refreshed for every scheme.
5. **Step.** The Campoli RK2 step then runs on the new connectivity. With `RD_ALE_FLIP_TRANSFER` and Campoli, `rd_ale_finish_step` asserts per-step conservation (|endpoint change| ≤ 1e-11 relative).

### 3.5 The moving-mesh hierarchy with actual-interval closure ("convention B")

Implemented in the `RD_ALE_INTERVAL_HIERARCHY` block of `residual_distribution_solver.c`.

**State.**
- A persistent **registry** of the RD connectivity: for every triangle, its sorted key, CCW IDs, birth time and **s_T**, the end of its last integrated interval.
- The registry, not the current Delaunay mesh, is the element set of the residual sweeps.
- Per vertex: the geometric ledger `RD_GeoLedger` (initialised to `DualArea`) and, for HLLC/Rusanov, `RD_CFLLedger`.

**At every synchronisation time t** (`rd_ale_interval_event`, called from `rd_step_end` after AREPO builds the mesh at t):

1. **Diff.**
   - Compare the registry with the new Delaunay triangulation by key; union-find gives the cavities.
   - All vertices are at t: `CREATE_FULL_MESH`; asserted via `P[].Ti_Current`.
2. **Closure set C.**
   - Naturally due triangles: those whose finest-bin vertex is synchronised.
   - Plus every registry triangle that touches a cavity vertex. These forced closures split the triangle's interval at t, so intervals may be non-dyadic.
3. **Liveness.** A vertex is *live* iff its whole registry star is in C and all its star triangles share one start.
4. **Integration.**
   - The triangles of C are integrated over their own intervals [s_T, t], h_T = t − s_T, with the concentrated Campoli RK2: predictor and corrector are both evaluated at t on the geometry pulled back over h_T.
   - The existing `compute_residuals` is called twice on a **synthetic tessellation**: three private points per triangle in C, minimal-image coordinates, local indices. This reuses the N/LDA/B/HLLC code unchanged.
   - Per-element h_T replaces 2^bin. The live mask replaces the old star-bin rule.
   - The geometric deposit (A_new − A_old)/3 · U_i⁰ is added to Q_i and to the ledger.
   - The interval is positive-checked over its whole quadratic area trajectory.
5. **Close.** s_T = t for every triangle in C.
6. **Refresh** every vertex whose star is now completely closed. This set includes all active and all cavity vertices; it is asserted that none of these has an open star.
   - The ledger equals the star area to ≤1e-10, which is asserted.
   - The **ledger becomes the divisor**. This is a discrete GCL: Q was accumulated with the ledger, so a uniform state stays exactly uniform.
   - Each refreshed state is checked admissible.
   - Inactive refreshed vertices get their primitives set directly. They keep their timebin and mesh velocity, so AREPO's time integration is untouched. Active vertices go through `update_primitive_variables`.
7. **Transfer.** The flip element is applied to each cavity with g = ledger, δm = (new star area − old star area) at t, and U = Q/g.
8. **Commit.** Retained triangles keep s_T; new triangles start at t.
9. **Global check.** If every triangle was closed in this event, assert Σ Q = initial total (≤1e-12) and Σ ledger = box area (≤1e-12).

**Scheme deposits per closed interval.** These are lumped unless stated; dU is the live predictor increment, zero for frozen vertices.

- **N:** ΔQ_i = (ΔA/3) U_i⁰ − (h/2)(φ_i⁰ + φ_i¹) + (ΔA/6) dU_i.
  - The last term is (D_T − M_T) dU_i/3 with Campoli weights. It is identical for Arpaia (§3.1).
- **LDA:** the N deposit plus the frozen-dU F1 swap (M_T/3)(dU_i − β_i Σ_j dU_j), with M_T = (A_old + A_new)/2, as in the static LDA hierarchy. Rank-deficient elements fall back to lumped.
- **B (interval total θ):**
  - The predictor call stores the stage-0 N and LDA distributions N⁰ and L⁰, the applied stage-0 blend b⁰ and Φ⁰ for each synthetic element.
  - The corrector applies θ(N⁰ + N¹) + (1 − θ)(L⁰ + L¹) − b⁰ + 2(1 − θ)(T_F1 − T_lumped), with the multiplier −h/2.
  - Its element total is Φ(U*), so it conserves for every θ.
  - θ follows Arpaia & Ricchiuto (2015) eqs. 43–45 from the interval total residual T_target + Φ (frozen/scalar options as in equal-step B).
  - Bug found and fixed: after the upwind solve, rhs[·][2] holds the solution z, not the F1 target. T_target is recomputed.
- **HLLC-RD / Rusanov:** the N deposit with the HLLC kernel. Its trapezoidal edge-flux contour plays the role of the contour residual.

**Why the totals are conserved.**
- (i) Fixed-connectivity contributions telescope (§3.1), applied per closed interval.
- (ii) Consider an edge shared by triangles with *different* intervals. Its endpoints cannot be live, since a live vertex has one common start for its whole star. They are therefore frozen at their traces, and they move linearly.
  - The edge normal is linear in time, so the midpoint rule integrates the edge flux exactly on both sides, whether over one interval or several.
  - The shared-edge contributions therefore cancel. This is the per-edge version of the column-sum identity of §3.1.
- (iii) The ledger telescopes. Σ_k (A_new,k − A_old,k)/3 over a vertex's closed intervals equals its current star area minus its area at the last refresh.
- (iv) The transfer is exact.

Totals are therefore conserved exactly whenever all triangles are closed. They are *meaningful* only then, since partial ledgers are not states. The hard assertion is placed there.

**Positivity (lumped low-order only).** Since every closed star is refreshed, between two refreshes a vertex is:
- **live for exactly one RK2 interval.** The equal-step convex-weight and stage-CFL checks apply: a = Σ M_T/3 / D, b = 3/2 − a ∈ (0, 1], and stage CFL ≤ 1, with triangle_dt = h/2 in this two-call form; or
- **frozen in every interval since its last refresh.** Each deposit is then a nonnegative combination of U_i⁰ and admissible neighbour states. The refreshed state is admissible if Λ_i = Σ (h/2)(c⁰ + c¹) ≤ g_i at refresh. This is the CFL ledger `RD_CFLLedger`; it is reported, and the refreshed states are checked.

N, LDA and B have no positivity guarantee, here or in equal-step.

**Accuracy.** Frozen vertices make the predictor first order across bin interfaces. This is the same limitation as the existing static RD hierarchy, and it matters for LDA/B (F1 temporal term), not for N.

### 3.6 Lazy (cavity-selective) flips (`RD_ALE_LAZY_FLIP`)

- **Why it is valid.** P1 RD needs a valid triangulation, not a Delaunay one. A changed component's old and new triangles tile the same polygon, so each component can be adopted or kept independently.
- **Rule.** A component is adopted only if:
  - one of its old triangles has an angle < `RD_LAZY_MIN_ANGLE` (15°); or
  - one of its old interior edges has an opposite-angle sum exceeding π by more than `RD_LAZY_DELAUNAY_EXCESS` (20°).
- **Otherwise** its old triangles stay in the registry, with no forced closure and no transfer.
- New star masses and the committed registry come from the *next* registry, not from the Delaunay mesh. The debug check "registry = Delaunay at the opening hook" is disabled in lazy mode.

### 3.7 What is proved, what is verified, what is assumed

**Proved algebraically and checked numerically:**
- conservation and linear exactness of both high endpoints;
- conservation and convexity of the low endpoint and the blend;
- minimality of the uniform shift;
- Σδm = 0 and Σδm x = 0;
- Arpaia vs Campoli weight algebra (−c₂/4);
- B corrector element total = Φ(U*);
- ledger telescoping.

**Proved earlier and checked here:** Campoli fixed-connectivity telescoping (1ᵀR = aᵀU; log3 §27). In the native gates, equal bins match equal-step to ≈4e-15.

**Argued, not formally written out (see §9):**
- hierarchy conservation with the element co-moving frame and the contour residual on unequal intervals;
- sufficiency of the CFL ledger condition for frozen vertices when neighbour predictor states enter φ¹.

Both are verified numerically to round-off and at runtime respectively, over every frozen gate.

**Assumed (runtime-checked, abort on violation):**
- edges shorter than a quarter box (minimal-image keys);
- unique ID-only triangle keys;
- no triangle inversion within an interval;
- all vertices drifted to the current time.

---

## 4. Implementation map

Line numbers are for `8e325e9`.

**Files.**
- `src/hydro/rd_flip_transfer.h` (237 lines): kernel, options, diagnostics, status codes.
- `src/hydro/residual_distribution_solver.c` (8272 lines; +1694/−44 against base) holds everything else:
  - guards: lines ≈55–130 (Rusanov/HLLC/blend), ≈213–245 (flip transfer), ≈293–360 (hierarchy, interval, lazy);
  - live mask `rd_point_stage_live` at 542;
  - old-mesh capture `rd_ale_topology_capture_old_mesh` at 1886;
  - `rd_ale_refresh_primitives` at 1942;
  - `rd_ale_apply_flip_transfer` at 2743;
  - `rd_ale_prepare_step` at 2910;
  - `rd_ale_finish_step` at 3140, with the conservation assert at 3186;
  - interval-hierarchy block from ≈3640: `rd_reg_*` helpers, `rd_reg_collect_mesh` 3755, `rd_reg_init` 3813, `rd_ale_interval_prepare` 3882, `rd_lazy_edge_compare` 3980, `rd_ale_interval_event` 3992;
  - hooks `rd_step_begin` 5120 and `rd_step_end` 5157;
  - per-element h_T at 5524;
  - B interval corrector at 6829;
  - interval low-order stage checks at 7701.
- `src/main/allvars.h`: `SphP.RD_CFLLedger`.
- `src/main/run.c`, `src/main/cpp_functions.h`: capture hook guards.
- `defines_extra`: new macros registered.
- `Makefile`: `INCL` additions; `check_rd` extended.

**Defaults and guards.**
- `RD_FLIP_FLOOR_FRACTION` 0.5, `RD_FLIP_DMP_RELAX` −1 (off), `RD_FLIP_ENTROPY_BOUND` 0, `RD_FLIP_HIGH_MODE` 1.
- `RD_ALE_FLIP_TRANSFER` requires `RD_ALE_EQUALSTEP` and excludes the old diagnostic repair.
- `RD_ALE_INTERVAL_HIERARCHY` requires `RD_ALE_HIERARCHICAL` + Campoli, with N/LDA/B and a contour residual, or `RD_RUSANOV_LOW_ORDER`.
- One rank. No restarts: the registry is not stored in restart files, and the code terminates if Ti_Current ≠ 0 when the registry is created.

**Diagnostics lines.**

| Line | Contents |
|---|---|
| `RD-FLIP` | removed/inserted triangles, cavities, θ statistics, max defect, max ΔU, transfer_rel, outside_dm |
| `RD-ALE-FINISH` | per-step endpoint conservation |
| `RD-IHIER ... stage=event` | due/forced/non-dyadic counts, live, closed, refreshed, cavities, θ, ledger error, outside_dm, common-closure `cons` and `coverage`, CFL ledger, adopted/deferred (lazy), cumulative work counters |
| `RD-IHIER ... stage=prepare` | minimum interval area, geometric deposit totals |
| `RD-RUSANOV ... interval` | live-vertex CFL and b_min |

**Python tooling (`tests/rd/` and `examples/`).** These are campaign drivers and analysis scripts.

| Script | Purpose |
|---|---|
| `test_flip_transfer.py` | kernel test, in `check_rd` |
| `run_flip_gates.py` / `analyze_flip_gates.py` | Phase 1 gate campaign |
| `examples/Sedov_2d/run_flip_sedov.py` | Sedov flip gate |
| `run_flip_limiter_sensitivity.py` | limiter sensitivity |
| `run_interval_hierarchy_gates.py` / `analyze_interval_hierarchy_gates.py` | hierarchy gates |
| `run_lazy_flip_gates.py` | lazy-flip gates |
| `examples/gresho_2d/run_kh_flip_resolution.py` / `analyze_kh_flip_resolution.py` | KH resolution study |
| `examples/gresho_2d/run_kh_repair_refresh.py` / `analyze_kh_repair_refresh.py` | old repair with and without the primitive refresh |
| `examples/Sedov_2d/plot_flip_hierarchy_sedov.py` | Sedov preview figure |

---

## 5. Tests

**Kernel test.** `make check_rd` passes 12/12, run with the conda Python on `PATH`. `test_flip_transfer.py` runs both high modes and covers:
- 2597 random single flips;
- 295 cavities from real Delaunay rebuilds of moving jittered points, 156 with more than 4 nodes;
- conservation 6.2e-16, and agreement with an independent NumPy implementation to 6e-16;
- uniform/affine invariance with θ = 1;
- high-endpoint invertibility (mode 0);
- extreme contrasts (hot donor, hot receiver, counter-streaming);
- stationary contacts: v = 0 is kept exactly and p uniform to round-off for every θ.

The entropy check allows the round-off of the bound itself: for a cold node with e/E ≈ 6e-8, K_min is uncertain by about 2e-9.

**Native frozen campaigns.**
- Every campaign freezes its tracked and untracked source with SHA256 hashes, builds each Config in its own `BUILD_DIR`, and records binary, Config, IC and parameter hashes.
- Runs are one rank with `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1`, each in its own working directory.
- **Caveat:** on 2026-10-09 up to about 13 simulations plus builds ran concurrently, exceeding the 6–8 process budget in `context_localMac.md`. Numerical results are unaffected (independent runs), but **all wall-clock and CPU timings of that day are unreliable**. Only element-work counts and the RD/Voronoi CPU *shares* within one run are reported.

| Archive (`local_runs/`) | Contents | Establishes | Limits |
|---|---|---|---|
| `flip_gates_20261009_v1` | {N, LDA, B, HLLC} × {Campoli, Campoli + transfer} plus N mode 1; uniform glass and random points, Sod, Yee 48/96, KH48 | conservation, uniform-state exactness, size of the transfer effect and its convergence | mode 0 except N_flip_h1; LDA-KH fails (known) |
| `sedov_flip_gate_20261009_v1` | HLLC and LDA/HLLC blend (pos, bounds), Campoli with and without transfer, 1/21-point | Sedov conservation and positivity vs the thesis runs | mode 0 |
| `flip_limiter_sensitivity_20261009_v1` | κ, entropy bound, density hull (Sedov HLLC, KH N) | decision D2 | mode 0 |
| `flip_mode1_sedov_20261009_v1` | HLLC mode 1, 1/21-point | Sedov safety of the new default | equal step only |
| `kh_repair_refresh_20261009_v1` | old repair: Arpaia control / stale / refreshed primitives, KH48 | effect of the primitive bug | old repair (not the new transfer) |
| `kh_flip_resolution_20261009_v1` | N: Arpaia, Campoli, transfer mode 0 and mode 1; KH glass48/96 (96 = 2×2 tiled SWIFT glass; 48 regenerates the archived IC bit-for-bit) | KH accuracy relative to resolution | KH under-resolved (tanh width ≈1–2 cells) |
| `interval_hierarchy_gates_20261009_v1` | first hierarchy freeze | — | **stopped and superseded** (refresh rule changed); see `STOPPED.txt` |
| `interval_hierarchy_gates_20261009_v2` | N/LDA/B × {ref = equal-step + flip, equal, two-bin 0.5/0.25, natural} + N no-transfer control; HLLC × {ref, equal, natural} on Sedov; uniform random, Yee 48/96, KH48, Sedov 1/21 | hierarchy conservation, equal-bin degeneration, interface accuracy, work | mode 0; frozen before the lazy and default-mode commits |
| `lazy_flip_gates_20261009_v1` | interval equal-bin N: {plain, plain + mode 1, lazy, lazy + mode 1}; HLLC natural + lazy; uniform, Yee 48/96, KH 48/96, Sedov 1/21 | lazy flips, mode 1 in the hierarchy | — |

---

## 6. Results: Phase 1 (equal-step transfer)

### 6.1 Conservation

| Problem | Campoli without transfer, drift (mass / energy) | With transfer |
|---|---|---|
| Uniform glass / random points (1278 cavities) | 0 (no defect for a uniform state) | state exact ≤5e-15 |
| Sod, N / LDA / B / HLLC | −2.2e-4/−6.1e-4, −7.2e-4/−1.1e-3, −4.7e-4/−1.0e-3, −1.3e-4/−3.8e-4 | ≤1.4e-15 |
| Yee48, all schemes | ≈−2e-5 / −3.5e-5 | ≤3e-16 |
| KH48, N / B / HLLC | +3.5e-3, +1.7e-3, +5.6e-4 (mass) | ≤1e-15 |
| Sedov HLLC 21 / 1 (thesis Arpaia) | −3.3e-3/+7.0e-3, −3.4e-3/−1.6e-2 | ≤1.2e-14 |
| Sedov blend bounds 21 / 1 (thesis) | −4.5e-3/−9.6e-3, −4.9e-3/**−6.4e-2** | ≤4e-15 |
| Sedov blend pos 21 / 1 (thesis) | energy +1.5e-2, +2.8e-2 | ≤2e-14 |

In Sedov, Campoli without transfer equals the thesis Arpaia run to L1 = 1.4e-6 (21-point) and 2.9e-6 (1-point).

### 6.2 Sedov positivity and profiles (t = 0.05)

- Every Sedov run reaches t = 0.05 with p > 0.
- HLLC: 4720 cavities (21-point), 93 with θ < 1, θ_min = 0.034.
  - Density peak 3.456 at r = 0.2503, vs thesis 3.413 at 0.2462 (analytic shell radius 0.258).
  - Mass-weighted profiles are visually indistinguishable from the thesis (preview figure via `plot_flip_hierarchy_sedov.py`).
- The bounds-limited blend sharpens its shell: peak 3.80 → 3.97 (21-point) and 3.86 → 4.17 (1-point).
- The positivity-only blend overshoots (5.5 / 4.9 vs analytic maximum 4) both with and without the transfer.

### 6.3 Accuracy in smooth flow (Yee, transfer − no transfer, ρ L1)

| Scheme | glass48 | glass96 | ratio | change of ρ L1 error vs analytic, 48 → 96 |
|---|---|---|---|---|
| N | 1.17e-4 | 3.5e-5 | 3.3 | +4.2 % → +2.1 % |
| LDA | 1.43e-4 | 4.1e-5 | 3.5 | +5.4 % → +2.6 % |
| B | 1.29e-4 | 3.6e-5 | 3.6 | +9.0 % → +5.9 % |
| HLLC-RD | 1.00e-4 | 4.0e-5 | 2.5 | +2.4 % → +1.4 % |
| N, mode 1 | 1.37e-4 | 3.6e-5 | 3.8 | +4.1 % → +2.1 % |

The transfer perturbation converges at about second order, as §3.2 predicts.

### 6.4 Limiter sensitivity (decision D2)

| Variant | θ < 1 | Effect |
|---|---|---|
| Sedov21 HLLC, κ = 0.5 / 0.1 / 1e-12 | 93 / 45 / 39 of ≈4720 | identical (peak 3.456–3.457) |
| Sedov21 HLLC, entropy bound | 3137 | peak 3.438 |
| Sedov21 HLLC, density hull r = 0 | 4774 (all) | peak 3.427 |
| KH48 N, entropy bound | 36 360 / 71 183 | entropy excursion 1.07 → 0.36 |
| KH48 N, hull / hull + entropy | all | excursion 0.07 / 0.08 (donor-cell at every flip) |

Decision: κ = 0.5; entropy bound off; density hull off. The bound and the hull reduce artefacts only by making most flips low order, i.e. diffusive.

---

## 7. Results: KH and the choice of high endpoint

### 7.1 The old repair (Arpaia N, glass48)

| Run | E_ky peak vs no repair | Peak delay |
|---|---|---|
| Stale primitives | +25 % | +1.0 |
| Refreshed primitives | +52 % | +2.0 |

These peaks are not an accuracy ranking:
- The seeded mode first decays (t < 2.5); before that, all runs agree within 5–6 %.
- The secondary growth then starts from a noise-level seed. Its onset time reacts to any O(h²) perturbation.

### 7.2 Entropy excursion

The entropy excursion is the maximum distance of s = p/ρ^γ outside its initial range, normalised by that range. It is a robust local indicator of non-physical mixing.

| Run | glass48 | glass96 |
|---|---|---|
| Arpaia, no treatment (not conservative) | 0.42 | 0.72 |
| Campoli, no transfer (not conservative) | 0.42 | 0.36 |
| Transfer, mode 0 (equal step / interval) | 1.07 / 0.66 | 0.71 / 0.79 |
| Transfer, mode 1 (equal step / interval) | 0.36 / 0.29 | 0.32 / 0.33 |
| Interval, lazy, mode 0 / mode 1 | 0.48 / 0.26 | 0.52 / 0.48 |

The uniform shift also moves the donors, and in KH pushes a few nodes outside the initial entropy range. The receiver-only endpoint does not, and needs no limiting.

### 7.3 Distance to the finer solution

Density is binned on a 16×16 grid; the entries are mean |ρ48 − ρ96|.
- **Resolution gap.** Every glass48 run is at about the same distance from every glass96 run: ≈0.010 (t = 0.4), 0.036–0.046 (t = 1), 0.073–0.091 (t = 1.6), 0.074–0.096 (t = 2).
- **Transfer effect at the same resolution.** Transfer − no-transfer is 0.030 (glass48) and 0.015 (glass96) at t = 1. That is first order at these under-resolved scales, and smaller than the 48 → 96 gap.
- **Closest conservative run.** Among the conservative glass48 runs, mode 1 (interval) is consistently among the closest to the glass96 runs: 0.0367 at t = 1 and 0.0745 at t = 2. Its distance equals that of the non-conservative runs.

### 7.4 KH resolution study, complete (`kh_flip_resolution_20261009_v1`, equal step, N)

| Run | E_ky peak (t), 48 / 96 | Mass drift, 48 / 96 | Entropy excursion, 48 / 96 | Mean grid \|ρ − ρ_Campoli\| at t = 1 / 2 / 3, glass48 | same, glass96 |
|---|---|---|---|---|---|
| Arpaia | 5.85e-2 (8.0) / 7.13e-2 (10.0) | +1.3e-3 / +2.3e-3 | 0.42 / 0.72 | 0.000 / 0.015 / 0.046 | 0.003 / 0.030 / 0.047 |
| Campoli | 6.72e-2 (8.2) / 5.69e-2 (10.0) | +3.5e-3 / +7.6e-4 | 0.42 / 0.36 | — | — |
| Transfer, mode 0 | 6.17e-2 (10.0) / 8.53e-2 (8.6) | 0 / 0 | 1.07 / 0.71 | 0.030 / 0.089 / 0.103 | 0.015 / 0.063 / 0.073 |
| Transfer, mode 1 | 9.05e-2 (6.8) / 7.49e-2 (8.2) | 0 / 0 | **0.35 / 0.32** | 0.028 / 0.086 / 0.089 | 0.017 / 0.060 / 0.084 |

- Both transfer modes change the early fields by about the same amount. The glass48/glass96 ratio of that change is 2.0 (mode 0) and 1.6 (mode 1) at t = 1, falling to ≈1.4 by t = 2 as KH growth amplifies differences.
- At these resolutions KH is not in the asymptotic regime: the tanh width is ≈1–2 cells.
- With mode 1 the entropy excursion stays at or below the non-conservative runs at both resolutions. With mode 0 it is 2.5× (48) and 2× (96) larger.
- The late E_ky peaks have no consistent order between methods or resolutions (noise-seeded onset). Resolved KH runs (glass192+) would be needed for a convergence statement and were not done.

### 7.5 Decision

`RD_FLIP_HIGH_MODE=1` became the default:
- **KH:** lowest entropy excursion and as close as any run to the finer solution.
- **Yee and Sod:** indistinguishable from mode 0.
- **Sedov:** conservative and positive; θ < 1 in 111 (21-point) and 102 (1-point) cavities; peak about 1 % lower (3.430 vs 3.456) at the same shell radius (0.2429); L1 1e-3 from mode 0.

Archives frozen earlier used mode 0 unless their Config says otherwise.

---

## 8. Results: Phase 2 (hierarchy) and Phase 3 (lazy flips)

### 8.1 Equal-bin degeneration (H1)

Max |difference| against equal-step Campoli (+ transfer), Yee48, t = 0.05, before any flip:

| Scheme | Max difference |
|---|---|
| N | 4e-15 |
| LDA | 5e-15 |
| B | 4e-15 |
| HLLC, Sedov21 t = 6e-4 | 7e-13 with p ≈ 259 |

After flips the two conventions (A and B) differ at the size of the transfer itself.
- Yee: equal-bin interval runs match equal-step + transfer to ≤0.2 % in L1 error.
- Sedov HLLC: L1 3–4e-4.

### 8.2 Conservation and exactness

`interval_hierarchy_gates_20261009_v2`; all variants: equal, two-bin 0.5/0.25, natural.

| Problem | Result |
|---|---|
| Uniform random points, N/LDA/B | state exact ≤9.5e-15 with 1249–1275 cavities; up to 8149 forced closures |
| Yee48/96, N/LDA/B | common-closure conservation ≤1.5e-14 |
| KH48, N/B | ≤9.5e-15 with ≈77 000 cavities and up to 531 000 forced closures |
| Sedov21/1, HLLC | ≤3.5e-14, p > 0, CFL ledger ≤0.11 (never above 1) |
| No-transfer control (N two-bin) | common-closure conservation 2.6e-4 (Yee48), 3.9e-5 (Yee96), 5.0e-3 (KH48); KH mass drift +5.1e-4 |

### 8.3 Accuracy across bin interfaces (Yee, change of ρ L1 vs equal-step + transfer)

| Scheme | two-bin 48 | two-bin 96 | split-0.25 48 | split-0.25 96 |
|---|---|---|---|---|
| N | −0.1 % | −0.1 % | 0.0 % | 0.0 % |
| LDA | +10.6 % | +23 % | +4.8 % | +3.9 % |
| B | +21 % | +32 % | +4.3 % | +4.8 % |

The split at 0.5 crosses the vortex centre. The frozen-F1 interface error is first order, so it grows relative to the second-order scheme error under refinement. N has no penalty.

### 8.4 Work and cost

Sedov, HLLC, natural bins, t = 0.05 (up to 8 occupied bins, dt ratio 128):

| | 21-point | 1-point |
|---|---|---|
| Events (equal step: steps) | 2448 (2466) | 2794 (2786) |
| Element work / all-fine | 8.0 % | 7.4 % |
| RD CPU, hierarchy / equal step | 14.5 s / 245 s | 8.9 s / 329 s |
| ρ L1 vs equal step + transfer | 9.8e-4 | 8.7e-4 |
| ρ peak (r) | 3.466 (0.2502) vs 3.456 (0.2503) | 3.464 (0.2496) vs 3.459 (0.2497) |

- The Voronoi rebuild is ≈70 % of the hierarchy run's CPU, against ≈50 % for equal step. The overall gain is therefore ≈1.4× in a lightly loaded scratch run. The frozen timings are load-contaminated (§5).
- KH48 natural bins: element work 84 %.
- Uniform random natural bins: 97 %.
- Test-pattern two-bin runs: 56–76 %, but twice as many events.

### 8.5 Lazy flips

`lazy_flip_gates_20261009_v1`:

| Problem | Adopted cavities, plain → lazy | Accuracy (lazy vs plain) |
|---|---|---|
| Uniform random | 1249 → 407 | exact (≤6e-15) |
| Yee48 / Yee96 | 245 → 64 / 1020 → 309 | ρ L1 −1.4 % / −0.3 % |
| KH48 / KH96, N | 76 858 → 18 180 / 396 729 → 95 181 | conservation ≤2e-15; see §7 |
| Sedov21 / Sedov1, HLLC natural | 4697 → 1181 / 4762 → 1149 | peak 3.436 vs 3.466 / 3.459 vs 3.464; conservation ≤3.5e-14; p > 0 |

- Deferred triangles stayed ≥15.0° (uniform) and ≥17–28° (Yee, Sedov).
- Minimum interval triangle area in KH48: 4.0e-5 (lazy) vs 4.3e-5 (plain); mean 2.2e-4.

---

## 9. Known limitations, failures and review checklist

**Failures and limitations, all recorded.**
- **LDA on KH** aborts at t ≈ 0.1–0.4 in every variant, including the equal-step references with and without the transfer. This is the known moving-LDA KH failure (log3 §§52–56): a secular density decay, with no LDA positivity guarantee.
- **First order at bin interfaces** for LDA/B (§8.3).
- **Wall-clock gain limited** by `CREATE_FULL_MESH`. A real gain would need registry-local mesh maintenance instead of a global Delaunay rebuild.
- **One rank and no restarts** for both the transfer and the hierarchy. ID-only keys require edges shorter than L/4, which is asserted.
- **Two transfer conventions.** A (equal step, at tⁿ on pulled-back positions) and B (hierarchy, at t after integrating on the old connectivity) are not bitwise equal after the first flip. They differ by the transfer's own O(h²) size.
- **Convergence in KH.** The transfer's effect converges only at first order in under-resolved KH (tanh width ≈1–2 cells). Resolved runs (glass192+) were not done.
- **Superseded freeze.** The v1 hierarchy freeze was stopped and superseded. Mode-0 archives remain valid records of mode 0.

**Points for review, in priority order.**
1. **Hierarchy conservation proof** (§3.5): per-element column-sum identity with the element co-moving frame (`RD_ELEMENT_COMOVING_FRAME`) and the contour residual over unequal intervals. Check that the frame map, the mesh-velocity term and the (ΔA/3)U⁰ deposit combine into an exactly telescoping per-edge statement. Numerically, every common closure conserves to ≤3.5e-14.
2. **B two-call corrector** (§3.5, line 6829): algebra, θ definition (frozen vs trapezoid), and the frame of the stored stage-0 arrays (primed frame, identical in both calls).
3. **CFL-ledger sufficiency for frozen vertices** when live neighbours' predictor states enter φ¹, and whether forced refresh of inactive vertices with unchanged timebins can violate the HLLC stage bounds in harder problems than Sedov.
4. **Refresh-all-closed-stars rule.** This is a superset of the oracle's "active ∪ cavity". Check its effect on accuracy and on AREPO's bookkeeping for inactive cells: OldMass, TimeLastPrimUpdate and gradient fields are not touched.
5. **Divisor = ledger** (discrete GCL) vs the geometric star area. The ledger drifts from geometry by ≤2e-13 per long run; check whether a periodic re-anchoring is needed for very long runs.
6. **Lazy thresholds.** The inversion risk within one step for deferred 15° triangles under strong shear; and the interaction with AREPO regularisation, which still sees the Delaunay mesh.
7. **Receiver-only default.** Positivity margins under extreme contrasts. Its single-node change is larger than the uniform shift's (max ΔU 0.25–0.31 vs 0.18–0.20 in Sedov).
8. **Campoli vs Arpaia framing for the thesis.** The conversion leak was negligible in Sedov, but measurable in Sod/Yee controls before (log3 §27). Is the thesis statement "flips are the remaining leak with Campoli" correct for all schemes?

---

## 10. Three dimensions (outlook; not implemented)

Everything above is 2D: the RD solver itself is `TWODIMS`-only. What generalises directly:
- the flip defect and its identities (lumped mass |T|/4);
- both high endpoints and their minimality;
- the donor-cell low endpoint and the θ blend;
- cavities as connected components of changed tetrahedra (3D bistellar 2-3, 3-2 and 4-4 moves, or larger changes) with ID-quadruple keys;
- the registry, closure sets, live masks, ledger and refresh rules;
- lazy adoption, since old and new tetrahedra tile the same polyhedron.

What changes:
- **Time quadrature of the geometry.** Under linear vertex motion a tetrahedron's volume is cubic in time and face normals are quadratic. The midpoint rule no longer satisfies the discrete GCL. Exact time-integrated normals are needed, e.g. two-point Gauss or Simpson (Lesoinne & Farhat 1996; Farhat, Geuzaine & Grandmont 2001). The same exactness is what makes shared-face fluxes cancel across unequal intervals in the hierarchy. So Campoli-type weights and the conservation argument carry over only with this quadrature.
- **3D distribution schemes** (N/LDA/B on tetrahedra, 5×5 systems) and 3D HLLC-RD median-dual faces.
- **3D Delaunay cost and MPI.** Realistic 3D problems need MPI. Registry ownership across ranks becomes the main new design problem.

---

## 11. Reproduction

All commands run from `/Users/zhenyuwu/arepo_rd`, with `PY=/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python` and `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`.

```
$PY arepo/tests/rd/run_flip_gates.py {prepare|build|run --group uniform|science|kh} local_runs/<new_root>
$PY arepo/tests/rd/analyze_flip_gates.py local_runs/flip_gates_20261009_v1
$PY arepo/examples/Sedov_2d/run_flip_sedov.py {prepare|build|run --group uniform|nearest21|nearest1} local_runs/<new_root>
$PY arepo/tests/rd/run_flip_limiter_sensitivity.py {prepare [--only ...]|build|run} local_runs/<new_root>
$PY arepo/tests/rd/run_interval_hierarchy_gates.py {prepare|build|run --group uniform|yee|kh|sedov} local_runs/<new_root>
$PY arepo/tests/rd/analyze_interval_hierarchy_gates.py local_runs/interval_hierarchy_gates_20261009_v2
$PY arepo/tests/rd/run_lazy_flip_gates.py {prepare|build|run --group uniform|sedov|yee|kh} local_runs/<new_root>
$PY arepo/examples/gresho_2d/run_kh_flip_resolution.py local_runs/<new_root> --stage all
$PY arepo/examples/gresho_2d/analyze_kh_flip_resolution.py local_runs/kh_flip_resolution_20261009_v1
PATH=/Users/zhenyuwu/miniconda3/envs/21cmfast/bin:$PATH make -C arepo check_rd
```

Use at most 6–8 concurrent simulations on this machine.
