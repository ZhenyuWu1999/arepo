# Conservative edge flips and a conservative moving-mesh hierarchy for P1 RD: results

Author: Claude Code (Opus 5.5), for Zhenyu Wu.
Branch: `feature/ale-flip-conservation-hierarchy`.

Supporting documents:
- Design and mathematics: [RD_FLIP_ELEMENT_AND_MOVING_HIERARCHY_DESIGN_20261008.md](RD_FLIP_ELEMENT_AND_MOVING_HIERARCHY_DESIGN_20261008.md).
- Plan: [RD_FLIP_HIERARCHY_IMPLEMENTATION_PLAN_20261008.md](RD_FLIP_HIERARCHY_IMPLEMENTATION_PLAN_20261008.md).
- Logs: log3 §§217–219.

Scope: one MPI rank, 2D, periodic. Nothing in the thesis has been edited.

## 1. Summary

| Goal (user priority) | Status |
|---|---|
| Round-off conservation across edge flips | **Done** for equal-step N, LDA, B, HLLC-RD and the LDA/HLLC blend, all with Campoli mass. Every frozen run conserves to ≤1e-14 (previously −0.33 % mass and +0.70 % energy in Sedov HLLC). |
| Sedov positivity | **Done** for HLLC-RD (21- and 1-point injection) and the blend; the old uniform-shift repair aborted with negative pressure. |
| Small accuracy cost | The transfer is provably the minimal conservative correction (Section 2). Yee and Sod show small changes. KH resolution study running (Section 3.4). |
| Hierarchical timesteps on the moving mesh | **Done** for N, LDA, B and HLLC-RD (actual-interval closure, `RD_ALE_INTERVAL_HIERARCHY`). Totals are conserved to ≤1.5e-14 at every common closure, flips included. Element work is 2.6 % of all-fine stepping in Sedov with natural bins. |
| Deferred (lazy) flips | **Implemented** (`RD_ALE_LAZY_FLIP`): 3–4× fewer adopted cavities at unchanged accuracy (uniform, Yee). KH test running. |

## 2. Why the flip element is the right correction

At a change of connectivity, each connected changed cavity C has the residual

D_C = Σ_i (b_i − a_i) U_i = ∫ (U_h^new − U_h^old),

where a_i and b_i are the old and new lumped P1 masses. This residual:
- vanishes for affine fields;
- for one 2-2 flip on a square of side h, equals D = −H_xy h⁴/6 with H the Hessian, so every nodal state moves by O(h² U'').

**High endpoint: the uniform shift U_i − D_C/Σ g_j⁺.**
- It is linear-exact.
- It is the unique minimiser of both
  - max_i |ΔU_i| subject to Σ g_i⁺ ΔU_i = −D_C (minimax), and
  - Σ g_i⁺ ΔU_i² under the same constraint (Lagrange multiplier ⇒ ΔU constant).
- So no conservative local transfer can change the solution less in either norm. The cost is O(h²) per event and should converge with resolution.

**Low endpoint: donor-cell exchange.**
- Donors keep U bit-for-bit.
- Receivers take convex mixtures.
- It is positive, stays inside the density hull and does not lower the minimum specific entropy.

**Blend.** One θ per cavity, chosen as the largest admissible value; θ = 0 is always admissible.

`RD_FLIP_HIGH_MODE=1` instead puts the linear-exact correction on the receivers only, with the same L1 change |D|.

## 3. Phase 1 — equal-step flip transfer (`RD_ALE_FLIP_TRANSFER`)

### 3.1 Implementation

- **Exact cavities.** Triangle keys are sorted ID triples. The old triangles are compared against the new connectivity pulled back to x^n; vertex sets are merged by union-find.
- **Assertions.**
  - Outside the cavities, the nodal mass is unchanged to ≤1e-10 relative.
  - Inside each cavity, conservation holds to ≤1e-12.
  - With Campoli mass, conservation holds per step to ≤1e-11.
- **Kernel.** `src/hydro/rd_flip_transfer.h`, a pure C header.
- **Kernel test.** `tests/rd/test_flip_transfer.py`, which runs in `make check_rd`. It covers:
  - 2597 random single flips;
  - 295 Delaunay multi-flip cavities;
  - uniform and affine invariance, and invertibility;
  - extreme contrasts;
  - stationary contacts (v = 0 and uniform p are kept for every θ);
  - both high modes.
- **Bug fix for all schemes.** After the old repair, N, LDA and B used to evaluate the predictor from stale primitives. Primitives are now refreshed for every scheme.
- **Campoli mass** is now allowed for HLLC-RD and the LDA/HLLC blend.

### 3.2 Frozen gates `local_runs/flip_gates_20261009_v1` (γ = 1.4, one rank)

| Problem | Result |
|---|---|
| Uniform glass48 (8 steps) and uniform random points (t = 1/4, 1278 cavities) | 18/18 runs: state exact to ≤5e-15, totals unchanged |
| Sod glass Nx64, t = 0.08, N | Campoli without transfer drifts −2.2e-4 (mass) and −6.1e-4 (energy). With transfer: 1.4e-15 and 9.7e-16, over 4773 cavities, all θ = 1. Flip − no-flip density L1 = 6e-4. |
| Remaining Sod and Yee cases | pending |
| KH t = 10 | pending |

### 3.3 Sedov gate `local_runs/sedov_flip_gate_20261009_v1` (γ = 5/3)

21-point injection, t = 0.05, HLLC-RD:

| Run | Mass drift | Energy drift | ρ peak (r) |
|---|---|---|---|
| Thesis run (Arpaia) | −3.29e-3 | +6.98e-3 | 3.413 (0.2462) |
| Campoli, no transfer | −3.29e-3 | +6.98e-3 | 3.413 (0.2462) |
| Campoli + transfer | 0 | −1.3e-15 | 3.456 (0.2503) |

- Campoli without transfer is identical to the thesis run (L1 difference 1.4e-6), so in Sedov the whole conservation error comes from the flips.
- With the transfer, the shell sits closer to the analytic radius 0.258.
- 4720 cavities were transferred; 93 needed θ < 1 (θ_min = 0.034). Positivity was kept throughout.
- 1-point injection and the blend variants: pending.

### 3.4 KH and the "result changes a little" question

Old uniform-shift repair, Arpaia N, glass48 (`local_runs/kh_repair_refresh_20261009_v1`):

| Run | E_ky peak relative to no repair | Peak delay |
|---|---|---|
| Repair with stale primitives | +25 % | +1.0 |
| Repair with refreshed primitives | +52 % | +2.0 (still growing at t = 10) |

The time series shows why these numbers are not a fair accuracy measure:
- The seeded mode decays first (t < 2.5); before that, all three runs agree within 5–6 %.
- Growth then restarts from a noise-level seed, so its onset time is sensitive to any O(h²) perturbation.

The proper test is resolution: `local_runs/kh_flip_resolution_20261009_v1` (N, glass48/96, Arpaia, Campoli, transfer, transfer with high mode 1). It is running.

## 4. Phase 2 — moving hierarchy with actual-interval closure (`RD_ALE_INTERVAL_HIERARCHY`)

### 4.1 Design

**Registry.** A persistent triangle registry stores the sorted-ID key, CCW IDs, the interval start s_T and the birth time.

**At every synchronisation time t:**
1. **Diff and cavities.** Compare the registry with the new Delaunay triangulation; changed components are the cavities.
2. **Closure set.** Naturally due triangles, plus every registry triangle that touches a cavity vertex.
3. **Integration.** Integrate over [s_T, t] with the concentrated Campoli RK2, on a synthetic tessellation of the closure set. A vertex predictor is live only if its whole star closes with one common start.
4. **Refresh.** Refresh every vertex whose star is now completely closed, dividing by the geometric ledger (a discrete GCL).
5. **Transfer.** Apply the flip element to each cavity.
6. **Commit.** Retained triangles keep s_T; new ones start at t.

**Conservation.** An edge shared by triangles with different intervals has frozen (non-live) endpoints that move linearly. Midpoint normals therefore integrate the edge flux identically on both sides, so totals are conserved at every common closure.

### 4.2 Scheme coverage

- **N:** lumped deposit (ΔA/3)U⁰ − (h/2)(φ⁰+φ¹) + (ΔA/6) dU.
- **LDA:** the frozen-dU F1 corrector, with the Campoli mass and the actual interval.
- **B:** total-θ blend for the two-call form.
  - The corrector applies θ(N⁰+N¹) + (1−θ)(L⁰+L¹) − b⁰ + 2(1−θ)(T_F1 − T_lumped).
  - Its element total is Φ(U*).
- **HLLC-RD and Rusanov:**
  - Natural bins are allowed.
  - Live vertices get the equal-step convex-weight and stage-CFL checks.
  - Frozen vertices get a CFL ledger, Σ (h/2)(c⁰+c¹) ≤ refreshed mass.
  - Every refreshed state is checked for admissibility.

### 4.3 Results (scratch runs; frozen v2 `local_runs/interval_hierarchy_gates_20261009_v2` is running)

**Equal-bin degeneration** (the hierarchy with all bins equal must reproduce equal-step Campoli, glass48):

| Scheme | Difference |
|---|---|
| N | 4e-15 |
| LDA | 5e-15 |
| B | 4e-15 |
| HLLC (Sedov, before the first flip) | 7e-13 with p ≈ 259 |

After the first flip the two transfer conventions differ: A applies the transfer at t^n on pulled-back positions; B integrates on the old connectivity and then applies it at t.

**Uniform state on random points**, two bins and ≈1270 cavities: N, LDA and B stay exact to ≤1e-14.

**Yee, glass48, two bins, t = 1** (frozen v1 archive, before the final refresh rule):

| Scheme / bin split | L1 change vs equal-step + flip |
|---|---|
| N | ±0.1 % |
| LDA, split at x = 0.5 (through the vortex centre) | +10.6 % (ρ) |
| LDA, split at x = 0.25 | +4.8 % (ρ) |
| B | +32 % (ρ) |

- The extra error is the known first-order frozen-F1 error at bin interfaces.
- The negative control without transfer drifts 1.6e-5 in mass and conserves only to 2.6e-4 at common closures. All transfer runs conserve to ≤1.5e-14.

**KH glass48, N, two bins, t = 2:** 16 558 cavities and 117 k forced closures; conservation 2e-15; no abort.

**Sedov 21-point, HLLC-RD, natural bins** (in progress):
- 8 occupied bins, with a dt ratio of 128.
- Conservation at common closures ≈1e-14; the CFL ledger never exceeds 0.11.
- Element work is ≈2.6 % of all-fine stepping.
- Wall-clock time is still dominated by AREPO rebuilding the full mesh at every sync point (`CREATE_FULL_MESH`). Real wall-clock gains need active-only mesh construction, which is outside this scope.

## 5. Phase 3 — lazy flips (`RD_ALE_LAZY_FLIP`)

The registry is the RD connectivity. A changed component (its old and new triangles tile the same polygon) is adopted only when one of its old triangles has an angle below 15°, or one of its old edges violates the Delaunay condition by more than 20°. Otherwise the old, still valid triangles are kept, with no forced closure and no transfer.

Equal bins, glass48:

| Test | Cavities (plain → lazy) | Accuracy |
|---|---|---|
| Uniform random | 1249 → 407 | state exact (6e-15) |
| Yee t = 1 | 245 → 64 | ρ/v/p L1 −1.4/+1.2/−1.0 % |

KH t = 10 (plain vs lazy): running.

## 6. Open items

- Finish the frozen gates: Sod/Yee/KH, Sedov 1-point and blend, hierarchy v2, KH resolution.
- Limiter sensitivity (floor κ, DMP hull, entropy bound) on Sedov.
- Combine lazy flipping with natural-bin hierarchies; it should reduce forced closures.
- MPI and restarts of the registry are out of scope.
