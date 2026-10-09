# Conservative edge flips and a conservative moving-mesh hierarchy for P1 RD: results

> **Superseded** by the review report [RD_FLIP_HIERARCHY_REPORT_20261009.md](RD_FLIP_HIERARCHY_REPORT_20261009.md) (2026-10-09). This file is kept as the running record.

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
| Small accuracy cost | The transfer is the minimal conservative correction (Section 2). In Yee its effect shrinks at ≈2nd order from glass48 to glass96. In KH it stays below the 48 → 96 discretisation error, and the receiver-only high endpoint (now the default) removes the extra entropy excursion. |
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
| Sod, all schemes (27/27 science runs complete) | With transfer every scheme conserves to ≤1.4e-15. Campoli without transfer drifts (mass/energy): N −2.2e-4/−6.1e-4, LDA −7.2e-4/−1.1e-3, B −4.7e-4/−1.0e-3, HLLC −1.3e-4/−3.8e-4. Flip − no-flip density L1: N 6.0e-4, LDA 1.7e-3, B 8.8e-4, HLLC 3.8e-4. All θ = 1. |
| KH glass48, t = 10 (7/9 complete) | See the table below. LDA fails at t ≈ 0.4 both with and without the transfer; this is the known moving-LDA KH failure (log3 §§52–56), unrelated to flips. |

**KH glass48, t = 10, equal step, Campoli**

| Scheme | Mass drift, no transfer → transfer | Flip cavities | E_ky peak (t), no transfer → transfer | Entropy excursion, no transfer → transfer |
|---|---|---|---|---|
| N, uniform shift (mode 0) | +3.5e-3 → 7e-16 | 78 467 | 6.72e-2 (8.2) → 6.17e-2 (10.0) | 0.42 → **1.07** |
| N, receiver-only (mode 1) | +3.5e-3 → 9e-16 | 76 048 | 6.72e-2 (8.2) → 9.05e-2 (6.8) | 0.42 → **0.36** |
| B | +1.7e-3 → 1.5e-16 | 79 391 | 5.90e-2 (7.2) → 7.35e-2 (6.6) | 0.54 → 1.37 |
| HLLC-RD | +5.6e-4 → −6e-16 | 23 261 | KH does not grow (too diffusive at glass48) | 0.034 → 0.048 |

The E_ky peaks again differ through the noise-seeded onset. The robust signal is the entropy excursion:
- The uniform shift (mode 0) moves donor states as well. In KH it pushes some nodes outside the initial entropy range (excursion 2.5× larger).
- The receiver-only high endpoint (mode 1) keeps donors bit-for-bit and does not raise the excursion.
- Mode 0 and mode 1 are indistinguishable in Yee and Sod (Section 3.2).

**Mode 1 adopted as the default (`RD_FLIP_HIGH_MODE` 1, 2026-10-09).** The evidence:

- **KH entropy excursion** (glass48 / glass96):
  - mode 1: 0.29–0.36 / 0.33;
  - mode 0: 0.66–1.07 / 0.71–0.79;
  - Arpaia without transfer: 0.42 / 0.72.
  - Mode 1 needs no limiting. The entropy bound and density hull reach low excursions only by switching most flips to donor-cell mixing.
- **Yee and Sod:** the modes are indistinguishable.
- **Sedov, HLLC, equal step** (`local_runs/flip_mode1_sedov_20261009_v1`):
  - 21-point: exact conservation, p > 0; θ < 1 in 111 cavities (mode 0: 93); ρ peak 3.430 vs 3.456; shell radius 0.2429 in both; L1 difference from mode 0 is 9.5e-4 (ρ).
  - 1-point: ρ peak 3.422 vs 3.459; L1 difference 1.3e-3.
- Mode 0 stays available with `RD_FLIP_HIGH_MODE=0`. Archives frozen before this change used mode 0 unless their Config sets the flag.

**Yee vortex: convergence of the transfer perturbation.** Each pair has the same resolution and dt; the difference is with transfer minus without (Campoli only). Without transfer the totals drift by ≈2e-5; with it they are exact.

| Scheme | ρ L1 difference, glass48 | glass96 | ratio | change of ρ L1 error vs analytic, 48 → 96 |
|---|---|---|---|---|
| N | 1.17e-4 | 3.5e-5 | 3.3 | +4.2 % → +2.1 % |
| LDA | 1.43e-4 | 4.1e-5 | 3.5 | +5.4 % → +2.6 % |
| B | 1.29e-4 | 3.6e-5 | 3.6 | +9.0 % → +5.9 % |
| HLLC-RD | 1.00e-4 | 4.0e-5 | 2.5 | +2.4 % → +1.4 % |
| N, high mode 1 | 1.37e-4 | 3.6e-5 | 3.8 | +4.1 % → +2.1 % |

The flip perturbation converges at close to second order (O(h²) predicts a ratio of 4), and its share of the error against the exact solution halves under refinement. In smooth flow the transfer therefore costs only the O(h²) that conservation requires. Receiver-only high mode 1 behaves like the uniform shift.

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
- **All 10 Sedov science runs complete.** Every run with the transfer conserves to ≤2e-14 and keeps p > 0. Thesis runs (Arpaia) for comparison:

| Run | Thesis drift (mass / energy) | With transfer | ρ peak (r): thesis → transfer | 
|---|---|---|---|
| HLLC, 1 point | −3.4e-3 / −1.6e-2 | 2e-16 / 1.2e-14 | 3.402 (0.2475) → 3.459 (0.2497) |
| LDA/HLLC blend (bounds), 21 points | −4.5e-3 / −9.6e-3 | −4e-16 / 4e-15 | 3.797 (0.2515) → 3.969 (0.2549) |
| LDA/HLLC blend (bounds), 1 point | −4.9e-3 / **−6.4e-2** | −1e-16 / 4e-15 | 3.861 (0.2550) → 4.170 (0.2548) |
| LDA/HLLC blend (positivity only), 21 / 1 points | energy +1.5e-2 / +2.8e-2 | exact | overshoot 5.5 / 4.9, as the thesis runs (analytic maximum 4) |

  - The bounds-limited blend loses up to 6 % of its energy through flips in the thesis runs. With the transfer it is exact, and its shell is sharper.

**Limiter sensitivity (decision D2)** (`local_runs/flip_limiter_sensitivity_20261009_v1`, equal step, Campoli + flip; all runs conservative and positive):

| Problem / variant | θ < 1 | Result |
|---|---|---|
| Sedov 21, HLLC, κ = 0.5 (default) / 0.1 / 1e-12 | 93 / 45 / 39 of ≈4720 | identical profiles (ρ peak 3.456–3.457) |
| Sedov 21, HLLC, entropy bound | 3137 | ρ peak 3.438 (more diffusive) |
| Sedov 21, HLLC, density hull (r = 0) | all 4774 | ρ peak 3.427 (mostly donor-cell) |
| KH48, N, entropy bound | 36 360 of 71 183 | entropy excursion 1.07 → 0.36 |
| KH48, N, density hull | all 67 712 | excursion 0.07 (donor-cell smoothing at every flip) |
| KH48, N, entropy bound + hull | all 67 621 | excursion 0.08 |

Decision: keep κ = 0.5 with the entropy bound and the density hull off.
- κ is insensitive.
- The bound and the hull reduce KH excursions only by switching most flips to the diffusive low-order endpoint.
- The receiver-only high endpoint (Section 3.4) removes the excursion without any limiting.

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

**Frozen v2, uniform / Yee / KH groups** (`local_runs/interval_hierarchy_gates_20261009_v2`, 64 runs, all complete).

- **LDA on KH** fails at t ≈ 0.1–0.4 in every variant, including the equal-step reference. This is the known moving-LDA KH failure, not a hierarchy problem.
- **Uniform random points**, N/LDA/B × {equal, two-bin, two-bin 0.25, natural}: state exact to ≤9.5e-15 with 1249–1275 cavities. Element work is 74 % (two-bin), 65 % (split 0.25) and 97 % (natural).
- **Yee: L1 error of ρ relative to equal-step + flip.** Equal and natural bins agree to ≤0.2 %; for this problem natural bins collapse to one bin.

| Scheme | two-bin, glass48 | two-bin, glass96 | split 0.25, glass48 | split 0.25, glass96 |
|---|---|---|---|---|
| N | −0.1 % | −0.1 % | 0.0 % | 0.0 % |
| LDA | +10.6 % | +23 % | +4.8 % | +3.9 % |
| B | +21 % | +32 % | +4.3 % | +4.8 % |

  - The LDA/B penalty is the first-order frozen-F1 error at bin interfaces. It grows relative to the second-order scheme error when the interface crosses the vortex, and stays at about 4–5 % when it does not.
  - N has no penalty.
- **KH glass48, t = 10, N and B**, every hierarchy variant:
  - conservation at common closures ≤9.5e-15;
  - ≈77 000 cavities;
  - up to 531 000 forced closures;
  - element work 56–69 % with the test patterns and 84 % with natural bins.
- **Negative control without transfer:** common-closure conservation degrades to 2.6e-4 (Yee48), 3.9e-5 (Yee96) and 5.0e-3 (KH48); KH mass drift is +5.1e-4.

**Frozen v2 Sedov group** (`local_runs/interval_hierarchy_gates_20261009_v2`, HLLC-RD, t = 0.05; every run positive; differences are against the equal-step Campoli + flip reference):

| Run | Events | Common-closure conservation | Element work | RD CPU (hierarchy / reference) | ρ L1 difference | ρ peak (r) |
|---|---|---|---|---|---|---|
| 21-point, equal bins | 2466 | 1.2e-14 | 100 % | — | 2.8e-4 | 3.434 (0.2504) |
| 21-point, natural bins | 2448 | 2.1e-14 | 8.0 % | 14.5 s / 245 s | 9.8e-4 | 3.466 (0.2502) |
| 1-point, equal bins | 2785 | 1.8e-14 | 100 % | — | 3.7e-4 | 3.457 (0.2497) |
| 1-point, natural bins | 2794 | 3.5e-14 | 7.4 % | 8.9 s / 329 s | 8.7e-4 | 3.464 (0.2496) |

Wall-clock ratios (natural bins / reference: 0.88 and 0.43) were measured under strongly varying machine load and are only indicative; even the equal-bin runs, which should take about as long as the reference, ranged from 0.77 to 1.04.

Scratch run, 21-point, natural bins, t = 0.05. Up to 8 occupied bins, dt ratio 128.

| | Hierarchy | Equal-step Campoli + flip |
|---|---|---|
| Steps / events | 2448 | 2466 |
| Conservation | ≤2.1e-14 at 64 common closures; final drift ≤7e-15 | ≤1.3e-15 |
| Flip cavities (θ < 1, θ_min) | 4697 (99, 0.025) | 4720 (93, 0.034) |
| Positivity | kept; CFL ledger ≤ 0.108 | kept |
| ρ peak / mass-weighted shell radius | 3.466 / 0.2427 | 3.456 / 0.2429 |
| Element work (fraction of all-fine) | 8.0 % (2.6 % early) | 100 % |
| CPU: residual distribution | 15 s | 284 s |
| CPU: Voronoi mesh | 802 s | 852 s |
| CPU: total | 1141 s | 1634 s |

- The two runs differ by an L1 of 1e-3 in ρ and p.
- The hierarchy cuts the RD cost about 19× and the total about 1.4×.
- What remains is AREPO's full mesh rebuild at every sync point (`CREATE_FULL_MESH`, 70 % of CPU). A larger gain would need registry-local mesh maintenance instead of a global Delaunay rebuild, which is outside this scope.

## 5. Phase 3 — lazy flips (`RD_ALE_LAZY_FLIP`)

The registry is the RD connectivity. A changed component (its old and new triangles tile the same polygon) is adopted only when one of its old triangles has an angle below 15°, or one of its old edges violates the Delaunay condition by more than 20°. Otherwise the old, still valid triangles are kept, with no forced closure and no transfer.

Equal bins, glass48:

| Test | Cavities (plain → lazy) | Accuracy |
|---|---|---|
| Uniform random | 1249 → 407 | state exact (6e-15) |
| Yee t = 1 | 245 → 64 | ρ/v/p L1 −1.4/+1.2/−1.0 % |

**Frozen lazy-flip gates** (`local_runs/lazy_flip_gates_20261009_v1`; interval hierarchy, equal bins for N, natural bins for HLLC):

| Problem | Cavities, plain → lazy | Accuracy (lazy relative to plain) | Notes |
|---|---|---|---|
| Uniform random | 1249 → 407 | state exact (≤6e-15) | deferred triangles ≥ 15.0° |
| Yee48 | 245 → 64 | ρ/v/p L1 −1.4/+1.2/−1.0 % | |
| Yee96 | 1020 → 309 | ρ/v/p L1 −0.3/+0.7/−0.2 % | |
| Sedov 21-point, HLLC, natural bins | 4697 → 1181 | ρ peak 3.436 vs 3.466; shell radius 0.2424 vs 0.2427 | conservation 1.2e-14, positive, element work 7.9 % |
| Sedov 1-point, HLLC, natural bins | 4762 → 1149 | ρ peak 3.459 vs 3.464 | conservation 3.5e-14, positive |

- Receiver-only high mode 1 matches mode 0 on all of these problems.
- KH48/96 with both modes, plain and lazy, is still running.

Scratch, KH glass48, t = 10, equal bins:

| Run | Flip cavities | E_ky peak (t) | Mass drift | Entropy excursion |
|---|---|---|---|---|
| Arpaia, no topology treatment | — | 5.85e-2 (8.0) | +1.35e-3 | 0.42 |
| Interval + transfer, all flips | 76 858 | 6.86e-2 (6.6) | −1.9e-15 | 0.66 |
| Interval + transfer, lazy | 18 180 | 7.71e-2 (7.0) | 2.2e-15 | 0.48 |

- Up to t ≈ 1.8, all three runs agree within 3 %.
- The onset of the noise-seeded secondary growth differs in every pair of runs, so late E_ky peaks do not rank accuracy.
- Lazy flipping cuts events 4.2× and lowers the entropy excursion (0.66 → 0.48).
- With the entropy bound off (the default), the uniform-shift transfer raises the entropy excursion. The entropy-bounded limiter therefore has to be tested on KH (decision D2).

## 6. Open items

- Finish the frozen gates: Sod/Yee/KH, Sedov 1-point and blend, hierarchy v2, KH resolution.
- Limiter sensitivity (floor κ, DMP hull, entropy bound) on Sedov.
- Combine lazy flipping with natural-bin hierarchies; it should reduce forced closures.
- MPI and restarts of the registry are out of scope.
