# Experimental moving LDA/F1 + edge-HLLC limited blend: Sedov test

Author: Claude Code (Opus 5.5), 2026-09-30. User request: experiment with
LDA+HLLC on the moving mesh and run Sedov first, with 21-point and single-point
injection. The thesis's LDA Gauss3 formulation is not changed.

This is an experimental research option, not the thesis baseline. It follows
the design in [HLLC report §5.6](RD_SEDOV_HLLC_LOW_ORDER_20260930.md). The
thesis, default Config and the static blend are unchanged; nothing is
committed or pushed.

## 1. Scheme

In every RK2 stage and every triangle, the stage contribution is

    phi_i^T = phi_i^{L,T} + ell_T (phi_i^{LDA,T} - phi_i^{L,T}),   0 <= ell_T <= 1.

* **High order.** The existing moving LDA/F1 RK2 path (`LDA_SCHEME`,
  `RD_ALE_EQUALSTEP`, `RD_ALE_CONTOUR_RESIDUAL`, `RD_ALE_CONTOUR_GAUSS=3`)
  is used unchanged.
* **Low order.** Edge HLLC (`rd_hllc_residual`) plus
  `rd_hllc_gauss_edge_split`. The split adds each edge's Gauss3-minus-trapezoid
  physical-flux term, half to each endpoint.
  * Element totals then equal LDA's Φ_G, checked per element (abort if they
    differ by more than 1e−10 of the assembly scale).
  * The adjacent triangle carries the opposite edge term, so each node's
    assembled low-order update is unchanged up to roundoff.
* **Stage contributions.**
  * Predictor: spatial residuals.
  * Corrector: lumped midpoint temporal term plus ½φ^L(U*) versus F1 plus
    ½φ^LDA(U*).
  * The existing ½D_i dU local kick is common to both.
* **Low-stage checks.** The assembled low stage must be admissible. The ALE
  corrector form (a_i−½)Uⁿ + b_i[U* − dt/(2b_i)S̄⁻¹Σφ^L(U*)] requires
  0<b_i≤1 and the HLLC stage CFL divided by 2b_i to be ≤1. Any violation
  aborts; no floors are applied.
* **Limiter.** One ℓ_T per element for all vertices and components, as in the
  static blend. The test is Q_i^L + d_i ℓ_T C_i^T admissible, which makes the
  update a convex average over incident elements and keeps it conservative.
  * `RD_BLEND_LOCAL_BOUNDS` additionally requires ρ_i ∈ [min, max] and
    K_i=p/ρ^γ ≥ min over the node's element stencil.
  * The stencil states are the stage-opening Uⁿ, the predictor U* (at the
    corrector) and the assembled low-order state.
  * The bounds are Zalesak-type and are not relaxed for smooth extrema.
  * The constraint sets are convex, so bisection finds the maximal ℓ.
    A final back-off step keeps the returned ℓ itself inside the bounds
    despite roundoff at the active boundary.

Options, all explicit: `RD_LDA_RUSANOV_BLEND=1/0` (limited / ℓ=0 low-order
control), `RD_BLEND_LOW_HLLC` (moving HLLC low order),
`RD_BLEND_LOCAL_BOUNDS`. The existing static LDA/Rusanov blend is unchanged
when `RD_BLEND_LOW_HLLC` is absent.

## 2. Verification before the Sedov runs

* `tests/rd/test_lda_hllc_blend.py` (new, compiled headers):
  * 60 jittered periodic meshes with strong contrasts and moving frames:
    element totals match an independent Gauss3 ALE contour to 3.2e−16, and
    the edge terms cancel at every node to 1.2e−16;
  * 3000 bounds-limiter cases: ℓ ∈ [0,1], bounds hold at ℓ, and ℓ is
    maximal to 1e−7.
  * Two harness issues were fixed by the back-off: returning left·(1−1e−12)
    could sit inside the roundoff band, and halving was non-maximal for tiny ℓ.
* `test_hllc_positivity.py` and all five `make check_rd` programs pass.
* Native gates (`../local_runs/sedov_lda_hllc_20260930_v1/`):
  * uniform defects 6.66e−16 (three moving builds) and 5.55e−16 (static blend);
  * the flag-absent static LDA/Rusanov blend replay on its archived 16² contact
    is **bitwise identical** to the archive at all 5 snapshots.

## 3. Native Sedov campaign

**Setup.**

* Archive `../local_runs/sedov_lda_hllc_20260930_v1/`; runner
  `examples/Sedov_2d/run_lda_hllc.py`, analysis `analyze_lda_hllc.py`.
* Configs `Config_LDA_HLLC_{bounds,pos,low}_moving.sh`: the archived moving
  LDA Sedov Config (`sedov_2d_20260929_v1/artifacts/LDA_moving_lab`), minus
  the report-only `RD_ALE_CFL_DIAGNOSTIC`, plus the blend options.
* Source frozen from HEAD `2858d43` + patch + untracked files; independent
  BUILD_DIRs.
* Binaries (SHA256):

  | Build | Binary |
  |---|---|
  | bounds | `8aab2e1a…e343` |
  | pos | `9997fd98…be66` |
  | low | `915d476b…419c` |
  | static regression | `b15bdc01…7efb` |

* ICs are byte-identical to the HLLC and Rusanov campaigns (glass128²,
  nearest21 or nearest1, median-dual hot-energy normalization), with the same
  parameter template. γ=5/3, p0=1e−6, E_hot=1, CFL .1, cap .01, equal
  adaptive steps, lab frame, one rank. At most 4 solvers ran concurrently.

**ℓ=0 control.** LDAHLLC_low takes the LDA path with the HLLC+split low order
and ℓ=0. It reproduces the standalone edge-HLLC run
(`sedov_hllc_20260930_v1`) to ≤6.1e−12 relative in ρ, p and positions at all
5 snapshots, with the same 2443 steps and identical budgets. The edge split
therefore cancels at the nodes in a full moving run, and the ALE a_i/b_i
checks are wired correctly.

**Stage checks (bounds runs).**

* Every accepted stage is admissible: 5376 stages (21 points) and 8036
  (1 point).
* Maximum low-stage CFL .109; minimum b .4933.
* Maximum limited-correction budget defect 9.0e−15.
* Mean limited fraction: .7% of elements in the predictor, 4.7% in the
  corrector (8.2% at the end). Accepted/requested correction norm .83
  (predictor) and .28 (corrector), so most limiting acts on the corrector.

### 3.1 Results at t=.05 (21 hot points)

| Method | raw ρ max | mean ρ peak (r) | ρ̄ r<.05 | ρ̄ r<.1 | p̄ r<.05 | v_r detrended RMS .05–.22 | v_t RMS .05–.22 | ΔM | ΔE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **LDA/HLLC bounds** | 3.797 | 2.889 (.2525) | .0293 | .0263 | 1.653 | .0846 | .0656 | −.452% | −.963% |
| HLLC low order (= ℓ=0 control) | 3.413 | 2.980 (.2475) | .0276 | .0289 | 1.714 | .0287 | .0309 | −.329% | +.698% |
| MMFV 1st order | 3.434 | 3.099 (.2525) | .0276 | .0321 | 1.670 | .0180 | .0121 | 0 | 0 |
| MMFV 2nd order | 3.971 | 3.302 (.2575) | .0300 | .0306 | 1.596 | .0487 | .0277 | 0 | 0 |

Analytic values: core p 1.605, area-mean ρ .0043 (r<.05) and .0345 (r<.1).
The roughness metrics are area-weighted RMS in .05≤r<.22: v_r after a
quadratic-in-r fit, and the tangential velocity v_t. None of the runs shows
a density undershoot ahead of the shock (binned minimum 1.0000), and none
has K below its initial minimum (bounds K_min/K0 = 1−3e−10).

### 3.2 Results at t=.05 (single hot node)

| Method | raw ρ max | mean ρ peak | ρ̄ r<.05 (n=1) | ρ̄ r<.1 | p̄ r<.05 | v_r RMS / v_t RMS | ΔM | ΔE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **LDA/HLLC bounds** | 3.861 | 2.925 | .0044 | .0214 | 1.595 | .0950 / .0674 | −.490% | **−6.40%** |
| HLLC low order | 3.402 | 2.999 | .0033 | .0250 | 1.654 | .0305 / .0323 | −.335% | −1.61% |

Figures (visually checked), final versions in `analysis/`:

* `lda_hllc_nearest21_profiles.png`
* `lda_hllc_nearest1_profiles.png`
* `lda_hllc_budgets.png`

### 3.3 Interpretation and limits

**What the limited LDA correction adds.**

* The shock is sharper: raw ρ max 3.80/3.86, against 3.41 for HLLC and 3.97
  for second-order MMFV.
* The core pressure moves toward analytic (21 points 1.653; 1 point 1.595),
  against 1.714/1.654 for HLLC and 1.670/1.596 for first-/second-order MMFV.
* The single-hot-node core density .0044 matches the analytic area mean
  .0043. That is a single sample, so it is suggestive only.

**What it costs.**

* Angular and velocity noise grows: v_r RMS about 3× HLLC and 1.7× MMFV2;
  v_t about 2× HLLC and 2.4× MMFV2.
* The noise lowers the binned mean density peak (2.89 versus HLLC 2.98),
  although the raw maximum is higher.
* The local bounds keep the noise bounded. They prevent the undershoot and
  entropy violations of the positivity-only static blend (§§167–168), but
  they do not remove it.

**Positivity-only comparison (interim, common saved state t=.025, 21 points).**

| Run | ρ min | T=p/ρ max | nodes with K < initial minimum | v_t RMS |
|---|---:|---:|---:|---:|
| Positivity-only | .0015 | 2059 | 411 (K_min/K0 9.5e−7) | .355 |
| Bounds | .036 | 95 | 0 | .105 |
| HLLC | .043 | 82 | 0 | .064 |

* This timestep collapses to 6.1e−6.
* Its first segments stopped at the 0.85·TimeLimitCPU=1530 s AREPO limit, at
  t=.0235 (21 points) and .0171 (1 point). This is a setup limit, not a
  numerical failure.
* The runs were resumed from restart files with TimeLimitCPU 14400. The
  resume action is recorded in `run_resume_status.json` and
  `run_lda_hllc_with_resume.py`.
* Local bounds are therefore necessary, not optional.

**Conservation.**

* Moving budgets remain non-conservative. Nearly all of the drift is in the
  logged step-opening/temporary ledger term, which contains the connectivity
  rebase; the endpoint conversion contributes ≤.016%.
* That term is larger with sharper profiles near the early hot spot. The
  bounds runs reach −2.69% (21 points) and −7.49% (1 point) energy by
  t=.0125, against −.25% / −2.54% for HLLC; they end at −.96% and −6.40%.
* The conservative positive flip remap (step 3) is therefore now the
  limiting issue for a thesis-quality moving Sedov, especially with point
  injection.

**Other limits.**

* Local bounds are not relaxed, so smooth-flow accuracy will clip extrema.
  No smooth/Yee order test has been run with this blend yet.
* Single runs; five snapshots.
* No MPI, hierarchy or repair.

### 3.4 Positivity-only runs completed (final)

Both resumed runs reached t=.05. The 21-point run took 8156 steps in total
(1530 s + 586 s); the single-point run took 9951 steps (1530 s + 1270 s).

* All 16312 / 19902 stages were admissible.
* Minimum stage density 7.9e−5 / 5.5e−5 (near vacuum).
* Maximum low-stage CFL .128 / .141; minimum b .4935 / .4958.
* Limited fraction: .01% (predictor) and about 2% (corrector). Positivity
  rarely binds, so LDA runs almost unlimited.

| t=.05 | raw ρ max | mean ρ peak | p̄ r<.05 | v_r / v_t RMS | nodes K < initial minimum (K_min/K0) | ΔM | ΔE |
|---|---:|---:|---:|---:|---:|---:|---:|
| positivity-only, 21 | 4.809 | 2.683 | 1.562 | .194 / .162 | 503 (1.4e−5) | −.041% | +1.46% |
| bounds, 21 | 3.797 | 2.889 | 1.653 | .085 / .066 | 0 | −.452% | −.96% |
| positivity-only, 1 | 5.349 | 2.618 | 1.571 | .164 / .142 | 528 (2.6e−6) | +.035% | +2.81% |
| bounds, 1 | 3.861 | 2.925 | 1.595 | .095 / .067 | 0 | −.490% | −6.40% |

Without local bounds, the scheme:

* overshoots the analytic shock jump (4);
* produces about 5× the HLLC velocity noise, with negative v_r in the core;
* undershoots the entropy minimum by up to five decades;
* has a broader, noisier front and a slightly undershooting ahead-of-shock
  density (single point: binned minimum .991).

Its budget drift has a different sign and size. That is not an
improvement: the same connectivity term acts on very different profiles.

The final figures in `analysis/` include these runs; `analysis_preliminary_bounds_only/`
is kept as the earlier interim analysis. Limiter statistics cover both run
segments.

## 4. Where the scatter comes from (user question, same day)

Read-only audit: `analysis/scatter_origin_audit.py` / `.txt`. It measures the
area-weighted tangential-velocity RMS inside r<.9R_s and in the shock band
.9–1.1R_s (R_s=.258√(t/.05)). It also measures front corrugation: the std
of the density-peak radius over 36 angular sectors at t=.05.

| Run | inner v_t RMS, t=.0125 / .025 / .05 | front v_t RMS, t=.0125 / .025 / .05 | peak-radius std |
|---|---|---|---:|
| HLLC | .065 / .046 / .031 | .161 / .101 / .062 | .0025 |
| LDA/HLLC bounds | .144 / .106 / .065 | .212 / .128 / .094 | .0041 |
| LDA/HLLC positivity-only | 1.070 / .476 / .170 | .292 / .280 / .214 | .0049 |
| MMFV 2nd order | .073 / .048 / .027 | .084 / .055 / .028 | .0011 |

Interpretation (mechanism inferred from these measurements; not isolated by
controlled ablation):

* **Where it is.** Noise is largest in the shock band. Every Sedov fluid
  element passes through the shock, and the quasi-Lagrangian mesh leaves the
  shock-generated perturbations in the post-shock material. They then decay
  as the flow expands.
* **Front corrugation.** With LDA the front is angularly wrinkled (std .0041
  versus .0025 for HLLC and .0011 for MMFV2). This lowers the binned mean
  peak even though the raw maximum is higher.
* **Why LDA adds noise.** LDA is linear and second order, so it is not
  monotone (Godunov); captured shocks produce oscillations. Its
  element-geometry-dependent upwind split on a glass gives non-radial
  (tangential) perturbations, and it removes HLLC's sound-speed-scaled
  dissipation that damps them.
* **Why the bounds do not remove it.**
  * The limiter bounds only ρ and K, over generous stencils that include
    across-shock and U^n/U*/U^L states.
  * Velocity is not bounded at all.
  * A single ℓ_T that switches from element to element near the shock can
    itself add roughness.
* **Positivity-only.** Early interior noise (1.07) comes from hot
  near-vacuum core nodes. The bounds remove most of it.
* **Not only LDA.** HLLC's front noise is still about 2× MMFV2's, so glass,
  median-dual and flip effects give a baseline that LDA amplifies.

Possible later remedies (not attempted):

* bounds or synchronized limiting on velocity/momentum;
* a smoothness/shock sensor that keeps a low-order band around the shock;
* stabilization of LDA (e.g. jump terms);
* characteristic PSI-type limiting.

**User decision (2026-09-30):** the LDA/HLLC blend is not yet mature. The
thesis should favour the edge-HLLC (first-order, FV-RD form) moving Sedov
result. The blend stays an experimental development record.
