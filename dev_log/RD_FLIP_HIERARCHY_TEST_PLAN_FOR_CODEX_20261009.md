# Comments on the Codex review and test specification for the next round

- **Author:** Claude Code (Opus 5.5), for Zhenyu Wu and Codex. Written 2026-10-09.
- **Branch:** `feature/ale-flip-conservation-hierarchy`, HEAD `e1b1aa9`.
- **Reads with:**
  - [Codex review](RD_FLIP_HIERARCHY_CODEX_REVIEW_20261009.md) (log3 §223);
  - my [review report](RD_FLIP_HIERARCHY_REPORT_20261009.md), now carrying the errata;
  - log3 §224 (the fixes).

The user has asked Codex to run the next tests. Part A gives my comments on the review. Part B specifies the tests: what to run, how to measure, and what counts as passing. Part C lists the practical pitfalls I hit.

---

## A. Comments on the review

I accept all four findings and the smaller wording corrections. They are fixed in `95a1a26` (code, drivers, report errata) and recorded in log3 §224. Further comments:

1. **R1 (mode aliasing).**
   - Every driver now states `RD_FLIP_HIGH_MODE`.
   - `tests/rd/flip_campaign_checks.check_configs` makes `prepare` fail if a transfer Config lacks an explicit mode, or if two methods have identical Configs. New drivers should call it.
   - The archived results were never affected: each archive froze its own source, in which the default was 0.

2. **R2 (CFL ledger).**
   - The condition is now enforced: a frozen-vertex ratio above `RD_CFL_LEDGER_LIMIT` (default 1), or a non-finite ratio, terminates the run.
   - `local_runs/cfl_ledger_gate_20261009_v1` verifies the check works:
     - Sedov21, HLLC, natural bins, mode 1, t = 0.005;
     - the default limit completes with a maximum ratio of 0.103;
     - a limit of 0.05 terminates as intended (ratio 0.069).
   - A termination is a correct refusal, not a fix. If a future run terminates here, the conservative remedy is *early closure*: when a frozen vertex's ratio passes, say, 0.8, force-close its whole star at the next event and refresh it. This is the same mechanism as for cavity vertices, so conservation is unchanged. Not implemented; only worth doing if a real run needs it.

3. **R3 (Arpaia defect).** Agreed: the full no-flip defect per step is Σ ε(Uⁿ⁺¹ − Uⁿ), O(Δt³). Over a fixed time interval it therefore accumulates to O(Δt²). The Arpaia path is second-order consistent but not exactly conservative. That is the thesis-relevant formulation.

4. **R4 (matched-ID metric).** Agreed. The analytic-error increase (each run's error against the exact solution, at its own coordinates) is the valid two-resolution indicator. For a genuine Eulerian difference, see B2.2 for a method that avoids interpolating ρ itself.

5. **Points of the review I would emphasise for the thesis.**
   - Keep conservation, positivity, accuracy and efficiency as separate claims.
   - Wall-clock figures from 2026-10-09 are not citable. Only element-work fractions may be quoted, with the caveat that the full mesh is still rebuilt.
   - LDA-KH fails in every variant and must stay listed as a limitation.

6. **Changes since the frozen archives.** These do not invalidate earlier archives but should be kept in mind when comparing:
   - mode 1 became the default at `8e325e9`;
   - the blend copies values where both endpoints agree, at `95a1a26`, which can change mode-1 donors by an ulp relative to earlier binaries;
   - the CFL ledger became a hard check at `95a1a26`.

---

## B. Test specification

General rules:
- Freeze the source of the commit being tested and record the hash. Use one `BUILD_DIR`, binary and `OutputDir` per Config, and one rank.
- Set `OMP_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1`.
- **Run at most 6 simulations concurrently** (budget in `context_localMac.md`).
- Every transfer Config must state `RD_FLIP_HIGH_MODE` explicitly; call `check_configs`.
- Record for each run: actual particle count, dt cap and actual steps/events, end time, and all flags.

**Final default ("FD").**
- `RD_ALE_CAMPOLI_MASS`;
- transfer with `RD_FLIP_HIGH_MODE=1`, κ = 0.5, entropy bound and density hull off;
- `RD_CFL_LEDGER_LIMIT` = 1;
- for the hierarchy: `RD_ALE_INTERVAL_HIERARCHY` + `RD_ALE_LAZY_FLIP` (15°/20°) + natural bins.

Configs come from `tests/rd/run_interval_hierarchy_gates.config(scheme, variant, mode)`. Add `RD_ALE_LAZY_FLIP` where stated. A new driver `run_final_default_gates.py` that reuses these functions is the simplest route.

### B1. Final-default validation (conservation, positivity, degeneration, controls)

| ID | Problem | Methods (all mode 1 unless stated) | Purpose | Pass criteria |
|---|---|---|---|---|
| B1.1 | Sedov 21 and 1-point, HLLC-RD, γ = 5/3, t = 0.05 (IC and parameters as `interval_hierarchy_gates_20261009_v2` sedov group: CFL 0.1, dt cap 0.001) | (a) equal-step Campoli + transfer; (b) interval natural; (c) interval natural + lazy (**FD**) | long-run safety of the final default; isolate lazy | all complete; p > 0, ρ > 0; common-closure conservation ≤1e-13 relative; CFL ledger ≤ 1 (enforced); report θ < 1 counts, cavities, element work, ρ peak, shell radius, mass-weighted profiles against analytic (same bins as the thesis figure, `plot_flip_hierarchy_sedov.py`) |
| B1.2 | Sedov 21 and 1-point, equal step | LDA/HLLC blend, bounds variant, mode 1 | earlier blend gates used mode 0 | complete; p > 0; conservation ≤1e-13 |
| B1.3 | Yee48, t = 0.05 (no flip by then) | N, LDA, B: equal-step ref + transfer vs interval equal bins (no lazy) | H1 degeneration with mode 1 | max \|Δ\| in ρ, v, p ≤ 1e-13 |
| B1.4 | Uniform state on random points (`uniform_random48`, t = 0.25) | N, LDA, B: interval {equal, two-bin 0.5, two-bin 0.25, natural} × {plain, lazy} | exactness with flips and mixed bins | state defect ≤ 1e-12; totals exact; report cavities and forced closures |
| B1.5 | Yee48/96, t = 1 | N, LDA, B: equal-step ref + transfer; interval two-bin 0.25; interval two-bin 0.25 + lazy | mixed bins and lazy, mode 1 | conservation ≤1e-13; report the change in analytic error against the ref (expected: N ≈ 0, LDA/B ≈ +4–5 %) |
| B1.6 | KH48, t = 10 | N, B: interval natural; natural + lazy. LDA expected to fail (known): run once, record, do not repeat | long shear run | conservation ≤1e-13; report entropy excursion, cavities, forced closures. Do **not** rank by late E_ky |
| B1.7 | Negative control: Yee48, N, interval two-bin, `RD_ALE_INTERVAL_NO_TRANSFER` | — | the transfer is necessary | common-closure conservation must be **visibly** violated (about 1e-4 expected) |
| B1.8 | Geometry-failure gate: KH48 or uniform random, interval equal + lazy with `RD_LAZY_MIN_ANGLE=0.5` and `RD_LAZY_DELAUNAY_EXCESS=179` | N | deferring flips until triangles invert must be **caught** | the run terminates with "a triangle inverts within its interval" (or the registry-inversion message), never silently. Record the time of failure |
| B1.9 | CFL ledger gate | done: `cfl_ledger_gate_20261009_v1` | — | — |

Estimated runtimes, single process on a lightly loaded machine: Yee96 ≈ 80 s; KH48 ≈ 4 min; KH96 ≈ 35 min; Sedov (16 384 points) ≈ 7–20 min.

### B2. Accuracy and convergence in smooth flow (Yee vortex)

**Inputs** (verified hashes in `local_runs/yee_frame_convergence_20260924_v1/campaign.json`):
- `yee_glass48.hdf5` (91e64bee…), `yee_glass96.hdf5` (01e685a9…), `yee_glass192.hdf5` (ffea225d…), all in `yee_frame_convergence_20260924_v1/inputs/`.
- Boost (1, 0), box 10, γ = 1.4, t = 1. Parameter template: `moving_equal_split_stages_20260914_v4/runs/yee_lda_split/param.txt`, as in `run_flip_gates.problems()`.

**Resolution and dt ladder** (dt coupled to h):

| Particles | dt cap |
|---|---|
| 48² | 1/256 |
| 96² | 1/512 |
| 96² (dt-halving control) | 1/1024 |
| 192² | 1/1024 |

**Methods:** N, LDA and B (HLLC optional), each as:
- (i) Campoli without transfer (not conservative; reference for the transfer's cost);
- (ii) Campoli + transfer, mode 1;
- (iii) interval equal + lazy, mode 1.

Mode 0 is optional, for completeness.

**B2.1 Error against the exact solution** (already valid; Codex confirmed). Area-weighted L1 of ρ, v and p against the analytic vortex at each run's own final coordinates, with weights m/ρ; reuse `analyze_flip_gates.yee_errors`. Report:
- observed orders 48 → 96 → 192 for each method;
- the analytic-error increase E_(ii) − E_(i) and E_(iii) − E_(i) at all three resolutions, with the orders of that increase.

The dt-halving control at 96 separates time error from mesh error.

**B2.2 Eulerian difference between two runs.** Directly interpolating ρ_A at x_B carries P1 interpolation error of order h²ρ″. At glass48 that is about 1e-3, ten times the signal. Interpolate the *error fields* instead:
1. For each run X, compute the nodal error e_X = ρ_X − ρ_exact(x_X) at its own final nodes.
2. Build the periodic Delaunay triangulation of X's final points (3×3 tiling; `scipy.spatial.Delaunay` with `LinearNDInterpolator`, or barycentric weights from `find_simplex`). Interpolate e_X linearly onto a common uniform grid, e.g. 256² over the box.
3. Since ρ_A − ρ_B = e_A − e_B pointwise, the Eulerian difference is ‖I e_A − I e_B‖₁ on the grid (cell-area weights).
   - The interpolation error is now O(h² e″) with e ≈ 1e-3, much smaller than the signal.
   - Check this by interpolating each run's own e onto its own nodes; the result must be exact.
4. Report the difference (ii) − (i), and (iii) − (ii), at 48/96/192, with observed orders.
5. Also report the same quantity for a pure grid-convergence pair (48 vs 96 of the same method). This puts the transfer's effect in proportion.

**Claims that B2 would support.** If the increase and the Eulerian difference decrease consistently over three resolutions, and the dt control shows time error is not dominant, then an order may be stated for these runs. Otherwise report the numbers without an order.

### B3. Optional, only after B1 and B2

- **KH at glass192**, N, mode 1, equal step, transfer vs no transfer.
  - Cost: about 8× glass96 (~5 h per run single process).
  - Purpose: a first resolved case for the KH entropy and distance comparisons.
  - Compare with the error-field method only if an analytic or reference solution is available. Otherwise report 96 → 192 self-differences at the 16×16 scale, labelled as sensitivity.
- **A long-run ledger drift monitor:** KH48 N interval natural, t = 50, recording `max_ledger`. This decides whether ledger re-anchoring is ever needed (Codex review §3).

---

## C. Practical notes

- **Python.** `/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python`. `make check_rd` needs that environment first on `PATH`: `PATH=/Users/zhenyuwu/miniconda3/envs/21cmfast/bin:$PATH make check_rd`.
- **Build.** Codex found that conda's `mpicc` earlier in `PATH` breaks the AREPO build. Build with Homebrew first on `PATH`. Running `check_rd` and building therefore need different `PATH` orders.
- **Queuing jobs.** Do not wait with `pgrep -f "<pattern>"` inside the same shell command. The waiting shell's own command line matches the pattern, so it waits forever; this happened twice on 2026-10-09. Wait on PIDs (`while kill -0 PID`) or run groups in sequence in one driver.
- **Expected failures** (record, don't retry): LDA on moving KH (log3 §§52–56).
- **Metrics not to use as accuracy rankings:**
  - late-time KH E_ky peaks (noise-seeded onset);
  - matched-ID differences;
  - wall-clock or CPU numbers from a loaded machine.
- **Existing analysis to reuse:**
  - `tests/rd/analyze_flip_gates.py` (`yee_errors`, `flip_stats`, analytic-error increase);
  - `tests/rd/analyze_interval_hierarchy_gates.py` (`hierarchy_stats`: events, cavities, forced, work, common-closure conservation, CFL ledger);
  - `examples/gresho_2d/analyze_kh_repair_refresh.series` (KH E_ky, entropy excursion);
  - `examples/Sedov_2d/plot_flip_hierarchy_sedov.py` (Sedov profiles and conservation figure; add the FD runs to its `RUNS` table).
- **Diagnostics in `run.log`:**
  - `RD-FLIP` (equal-step transfer);
  - `RD-ALE-FINISH` (per-step conservation, asserted with Campoli + transfer);
  - `RD-IHIER ... stage=event`, whose fields include:
    - `cons`, `coverage` (only meaningful when every triangle closed);
    - `cfl_ledger_max`, `adopted`, `deferred`, `deferred_min_angle`;
    - cumulative `work=[element updates, forced, non-dyadic, cavities]`.
- **Code locations** (as of `e1b1aa9`; see report §4): transfer kernel `src/hydro/rd_flip_transfer.h`; registry and event `rd_ale_interval_event` in `residual_distribution_solver.c`.
