# HLLC-RD: origin, mathematics, implementation, experiments and results

Author: Claude Code (Opus 5.5), 2026-10-01, at the request of Zhenyu Wu.
This is a consolidated record of the work of 2026-09-30/10-01 (log3 §§184–191).
The detailed day-by-day reports remain authoritative for provenance:

* [shock literature and optimization](RD_SEDOV_SHOCK_LITERATURE_OPTIMIZATION_20260930.md);
* [HLLC low order](RD_SEDOV_HLLC_LOW_ORDER_20260930.md) (§§1–11);
* [experimental LDA/HLLC blend](RD_SEDOV_LDA_HLLC_BLEND_20260930.md);
* [thesis text draft](RD_SEDOV_HLLC_THESIS_TEXT_DRAFT_20260930.md).

No thesis file has been edited, and nothing has been committed.

Figure links below are relative to this file. The archives are in the
workspace `local_runs/` directory, so `../../local_runs/...` from
`arepo/dev_log/`.

---

## 1. How the idea came about

### 1.1 Starting point

The user wanted a moving-mesh RD Sedov blast for thesis §4.3.2. The existing
result looked worse than AREPO MMFV and SWIFT "despite using LDA+Rusanov".
Reading the logs showed that this description was inaccurate.

* The **moving** Sedov result (log3 §§158, 164) was pure first-order
  `RD_RUSANOV_LOW_ORDER`: scalar Rusanov/Lax–Friedrichs distribution,
  trapezoidal fluxes, lumped RK2.
* The LDA+Rusanov positivity blend (§167) and the B/Bmax variants (§170) had
  run on a **static** mesh only.
* LDA and N on their own fail on this strong Sedov problem (§156): N at
  t≈.0067 static and .0023 moving with 21 heated vertices, LDA within a few
  steps. Morton et al. (2023, §5.2.3) also report unstable LDA for Sedov.

### 1.2 Literature survey

See [the literature report](RD_SEDOV_SHOCK_LITERATURE_OPTIMIZATION_20260930.md).

* **RD shock capturing.**
  * Deconinck & Ricchiuto review: LDA/N blending and limited (PSI) schemes,
    with characteristic decomposition for systems.
  * Abgrall, Bacigaluppi & Tokareva (2019): PSI-limited Rusanov in
    characteristic variables, Θ blending and jump stabilization. Tested on
    Woodward–Colella blast waves, not Sedov.
  * The MOOD RD cascade ends in classical Rusanov.
* **RD blast results in astrophysics.**
  * Paardekooper (2017): on Noh, blended schemes fail or need N backup; on
    the cylindrical blast, N ≈ HLL and B is worse.
  * Morton (2023): Sedov only with N.
* **The closest analogue to our P1 ALE scheme.** Guermond, Popov & Saavedra
  (2020): edge-local graph viscosity plus convex limiting on density and
  specific entropy, with connectivity fixed.
* **The enabling fact.** Deconinck & Ricchiuto (2017 edition §4.1, Eqs. 55–57; §3.6.1 was an older text, corrected per Codex log3 §201): a
  first-order finite-volume scheme on the median dual, with *any*
  conservative numerical flux, is a fluctuation-splitting/RD scheme. Its
  nodal residuals sum to the trapezoidal element residual. Abgrall (2017)
  gives the converse, a flux form for RD. So a Riemann-solver flux can serve
  as an RD low-order distribution.

### 1.3 Diagnosis of the Rusanov result

The Rusanov element dissipation in `src/hydro/rd_rusanov.h` is

    alpha_T = 1/2 max_{j,k} ( |(v_j - w_T).n_k| + c_j |n_k| ),
    phi_i  += alpha_T (U_i - U_j)/3   for every vertex pair,

applied equally to ρ, m and E.

* On a quasi-Lagrangian mesh |v−w_T|≈0, but alpha_T≈cℓ/2 remains. Mass is
  therefore diffused at the **sound speed**, and more so in the hot,
  expanded core, where c and the cell size ℓ are largest.
* This predicts the observed central-density ordering: moving Rusanov .198 >
  static Rusanov .125 > MMFV .028.
* A contact-resolving Riemann solver has mass flux ∝ (u−w)·n, which is nearly
  zero on this mesh.

### 1.4 The discriminating experiment

AREPO MMFV with face extrapolation switched off is first order but keeps a
contact-resolving Riemann flux. It gave a mean density peak of 3.10 (exact
solver) or 3.07 (HLLC) and core ρ .028, against Rusanov RD 2.43 and .198.
Second-order MMFV reaches 3.30 and .030.

Hence most of the deficit came from the **form of the low-order
dissipation**, not from the missing second order. HLLC and the exact solver
were practically identical at first order. HLLC was chosen because it:

* resolves the contact;
* is positive with suitable wave speeds;
* is algebraically simple.

Figure: [first-order MMFV vs Rusanov RD](../../local_runs/sedov_mmfv_first_order_20260930_v1/analysis/mmfv_first_order_profiles.png).

---

## 2. Mathematics

### 2.1 Element residual (unchanged from the Arpaia ALE path)

For a triangle T of the midpoint geometry, with inward length-weighted normals
n_j (n_0=(y1−y2, x2−x1) cyclic, CCW vertices) and element-mean mesh velocity
σ̄_T=(σ_0+σ_1+σ_2)/3:

    Phi^T = 1/2 sum_j G(U_j).n_j,      G(U) = F(U) - U (x) sigma_bar_T .

This is the nodal-flux (trapezoidal) form of the Arpaia residual. The
divergence of σ is carried by the modified dual area, as in thesis §4.2.

### 2.2 Median-dual segments inside a triangle

The three segments joining the edge midpoints to the centroid split T into
the parts that belong to the median dual cells of its vertices. For vertices
i, j the segment between their parts has the scaled normal

    nu_ij = (n_j - n_i)/6 .

Its properties:

* **Orientation and length.** It points from i to j, and its magnitude is the
  segment length. Checked on (0,0),(1,0),(0,1): ν_01=(2,1)/6 is normal to
  midpoint→centroid and has the same length.
* **Closure.** Closing the boundary of C_i∩T gives
  ν_ij+ν_ik−n_k/2−n_j/2=0, hence Σ_{j≠i} ν_ij = −n_i/2.
* **Antisymmetry.** ν_ji = −ν_ij.

### 2.3 Distribution (the FV-RD split)

    phi_i^T = sum_{j in T, j != i} [ H(U_i, U_j; nu_ij) - G(U_i).nu_ij ] .

H is a conservative numerical flux, H(U_j,U_i;−ν) = −H(U_i,U_j;ν). The
H-terms therefore cancel in pairs, and Σ_i φ_i^T = −Σ_i G(U_i)·Σ_{j≠i}ν_ij
= Φ^T. The scheme is an element-local conservative split of the element
residual, i.e. an RD scheme.

Pair form, as computed:

* left fluctuation |ν|(H−G(U_i)·ν̂) = A⁻ΔU goes to i;
* right fluctuation (G_j−G_i)·ν − left = A⁺ΔU goes to j.

This is the multidimensional analogue of the 1D Roe fluctuation splitting in
thesis Chapter 3. It is **not** multidimensional upwind (the split uses three
fixed directions), and it is first order.

### 2.4 HLLC in the frame moving with σ̄_T

1. **Frame variables.** v' = v − σ̄_T. Normal and tangential components
   u_n = v'·ν̂, u_t = v'·t̂ with t̂ = (−ν̂_y, ν̂_x). The internal energy is frame
   invariant, and E' = p/(γ−1) + ½ρ|v'|².
2. **Wave speeds** (Einfeldt/Batten plus Davis, Roe averages in the frame):

       S_L = min(u_nL - c_L, u_nR - c_R, u~_n - c~),
       S_R = max(u_nL + c_L, u_nR + c_R, u~_n + c~).

3. **Contact speed.**

       S* = [p_R - p_L + rho_L u_L (S_L - u_L) - rho_R u_R (S_R - u_R)]
            / [rho_L (S_L - u_L) - rho_R (S_R - u_R)] .

4. **Star states** (Toro):

       U*_K = rho_K (S_K - u_K)/(S_K - S*) [1, S*, u_tK, E'_K/rho_K + (S* - u_K)(S* + p_K/(rho_K (S_K - u_K)))] .

   Both are checked for positive density and internal energy, and
   S_L<S*<S_R is required. Otherwise the kernel returns failure and the
   solver aborts.
5. **Left fluctuation f.**

   | Case | f |
   |---|---|
   | S_L ≥ 0 | 0 |
   | S_L < 0 ≤ S* | S_L(U*_L − U_L) |
   | S* < 0 < S_R | S_L(U*_L − U_L) + S*(U*_R − U*_L) |
   | S_R ≤ 0 | F(U_R) − F(U_L) |

6. **Back to the laboratory frame.** Rotate the momentum to x/y, then apply
   G(−σ̄_T):

       [f_rho, f_m + w f_rho, f_E + w.f_m + 1/2 |w|^2 f_rho] .

   This follows from the Galilean ALE-flux identity in the removed thesis red
   text (commit e4fcd84).
7. **Identical states.** Bitwise-identical neighbours return zero, so a
   uniform state is preserved exactly.

### 2.5 Positivity and the stage checks

Each pair term is a one-sided average of the HLLC fan:

* U_L − (t/a)(H−F_L) is the mean of the fan over [−a,0];
* U_R + (t/a)(H−F_R) is the mean over [0,a];

for a ≥ t·max(|S_L|,|S_R|). A forward-Euler stage is therefore a convex
combination of admissible states when

    C_i = (dt/S_i) sum_{T contains i} sum_{j != i} |nu_ij| s_ij <= 1,   s_ij = max(|S_L|, |S_R|),

with S_i the Arpaia divisor. The existing lumped ALE corrector can be written

    U^{n+1} = (a_i - 1/2) U^n + b_i [ U* - dt/(2 b_i) S_i^{-1} sum phi(U*) ],
    a_i = M_i/S_i,   b_i = 3/2 - a_i,

so 0<b_i≤1 and C_i/(2b_i)≤1 are also required. All of these, and the
admissibility of every assembled stage before primitive recovery, are checked
at every stage. There are no floors and no clipping.

### 2.6 Contact preservation

If the vertices of a triangle move with σ̄_T and share the same pressure, the
HLLC flux equals the physical flux and every fluctuation vanishes. No density
is exchanged between them. This is the property that Rusanov lacks on the
moving mesh.

### 2.7 Difference from AREPO's Riemann-solver FV

| | AREPO MMFV | HLLC-RD |
|---|---|---|
| Loop | Voronoi faces | Delaunay triangles |
| Riemann problems | One per Voronoi face | Three per triangle, on the median-dual segments, in that triangle's frame σ̄_T; two half-face problems per Delaunay edge |
| Face geometry | Through circumcentres | Through centroids; the two coincide only for equilateral triangles |
| States | MUSCL-Hancock reconstructed face states | First-order nodal states |
| Update | Flux exchanged between Voronoi cells | Conservative split of the element residual, integrated with the Arpaia RK2 and modified dual area |

On the glass:

* the half-face lengths sum to the Voronoi face length (median ratio .999);
* the two halves are nearly collinear (median bend .4°);
* the combined normal deviates from the generator direction by a median
  1.25° (99%: 12.8°).

[Schematic on the thesis Figure 4.2 node layout](../../local_runs/sedov_hllc_20260930_v1/analysis/hllc_rd_schematic.png);
[half-face audit](../../local_runs/sedov_hllc_20260930_v1/analysis/halfface_audit.txt).

---

## 3. Code implementation

**Kernel: `src/hydro/rd_hllc.h`** (new; includes `rd_rusanov.h` for the
admissibility helpers).

* `rd_hllc_pair(ul, ur, nu, w, gamma, out)`: one pair. It performs the frame
  transform, wave speeds, contact and star states with admissibility checks,
  the fluctuation cases, the rotation and the Galilean back-transform. It
  returns the HLLC signal speed, or −1 on failure.
* `rd_hllc_residual(u, n, w, gamma, phi, residual, coeff, scale)`: one
  element.
  1. Compute the lab ALE fluxes g_j.
  2. Reject clockwise input: requires cross(n_0, n_1) > 0, i.e. CCW vertices
     with the solver's normal formula.
  3. Compute Φ in difference form.
  4. Loop over the pairs (0,1), (1,2), (2,0) with ν=(n_j−n_i)/6. Accumulate
     the left/right fluctuations into `residual[k][i]` / `residual[k][j]`,
     and the per-vertex coefficients `coeff[i] += |ν| s_ij`.
  5. Return max(coeff), or −1.
* `rd_hllc_gauss_edge_split(...)`: used only by the experimental LDA/HLLC
  blend. It adds each edge's Gauss3-minus-trapezoid term half to each
  endpoint.

**Solver: `src/hydro/residual_distribution_solver.c`** (the option sits
inside the existing `RD_RUSANOV_LOW_ORDER` path).

* Include and guard: `RD_LOW_ORDER_HLLC` requires `RD_RUSANOV_LOW_ORDER`.
* Timestep selector `rd_apply_cfl_timestep_constraint`: calls
  `rd_hllc_residual` and adds `coeff[vertex]` (instead of 4α/3) to the nodal
  sum. The raw bound is DualArea/Σcoeff, scaled by CourantFac.
* Stage assembly in the triangle loop: calls `rd_hllc_residual` with the
  midpoint normals and `Velvertex_avg`, runs `rd_check_conservation(...,
  "HLLC")`, and accumulates `rd_rus_coeff[index] += dt*coeff[vertex]`.
* Reused unchanged from the Rusanov path:
  * Arpaia ALE geometry and divisor;
  * lumped RK2 temporal terms;
  * the per-stage CFL, b_i and admissibility checks
    (`RD-RUSANOV ... CFL_max b_min` log lines);
  * the timestep hook.

**Other files.**

* `defines_extra`: `RD_LOW_ORDER_HLLC` and `RD_HLLC_H`.
* Configs: `examples/Sedov_2d/Config_HLLC_{static,moving}.sh`, i.e. the
  archived Rusanov configs plus `RD_LOW_ORDER_HLLC`.

**Scope.** One MPI rank, global equal timesteps, periodic box, hydro only,
lab frame. No hierarchy and no topology repair.

**Tests.** `tests/rd/test_hllc_positivity.py` compiles the real header and runs
4000 random CCW triangles (ρ 1e−3–1e3, p 1e−6–1e3, |v|,|w|~3, γ 1.4 and 5/3).

| Check | Result |
|---|---|
| Conservation against an independent quadrature | 3.8e−16 |
| Match to an independent Python HLLC (standard flux form, lab variables) | 3.2e−13 |
| Coefficients | rtol 1e−10 |
| Galilean covariance | 9.0e−12 |
| CFL-limited forward step | admissible |
| Uniform state, resting contact | exact |
| Clockwise input | rejected |

The tests now use the solver's exact normal formula (§9 of the HLLC report).
All five existing `make check_rd` programs pass.

**Runners and analysis (`examples/Sedov_2d/`).**

| Purpose | Scripts |
|---|---|
| Main HLLC campaign | `run_hllc.py`, `analyze_hllc.py` |
| Reuse of frozen HLLC binaries on other ICs | `run_hllc_disk005.py`, `run_hllc_reuse.py` |
| First-order MMFV | `run_mmfv_first_order.py`, `analyze_mmfv_first_order.py` |
| Single-cell MMFV / single-particle SWIFT | `run_mmfv_single.py`, `run_swift_single.py` |
| Figures | `plot_hllc_thesis_preview.py`, `plot_sedov_maps.py`, `plot_sedov_profiles_mw.py`, `plot_hllc_schematic.py` |
| Experimental blend | `run_lda_hllc.py`, `analyze_lda_hllc.py` |

---

## 4. Experiments and figures

Common setup: SWIFT `SedovBlast_2D` physical setup. Periodic unit box, glass
128² (16384 points), ρ=1, v=0, p0=1e−6, γ=5/3, E=1 as thermal energy, t=.05
(analytic shock radius .258). RD and MMFV use one global adaptive step with
CFL .1 and cap .01, one rank, and OMP/BLAS 1. RD hot energy is normalized by
median-dual mass, MMFV by Voronoi volume, SWIFT by equal particle mass.

| # | Experiment | Archive (`local_runs/`) | Figures |
|---|---|---|---|
| 1 | First-order MMFV (exact, HLLC) vs Rusanov RD, 21 hot | `sedov_mmfv_first_order_20260930_v1` | [profiles](../../local_runs/sedov_mmfv_first_order_20260930_v1/analysis/mmfv_first_order_profiles.png) |
| 2 | HLLC-RD static/moving, 21 hot; moving, 1 hot; uniform gates; flag-absent Rusanov regression | `sedov_hllc_20260930_v1` | [21 hot](../../local_runs/sedov_hllc_20260930_v1/analysis/hllc_nearest21_profiles.png), [1 hot](../../local_runs/sedov_hllc_20260930_v1/analysis/hllc_nearest1_profiles.png), [budgets](../../local_runs/sedov_hllc_20260930_v1/analysis/hllc_budgets.png) |
| 3 | Thesis-style preview: HLLC-RD vs MMFV vs SWIFT, 21 hot | (same) | [preview](../../local_runs/sedov_hllc_20260930_v1/analysis/thesis_preview/hllc_sedov_thesis_preview.png) |
| 4 | 130-node (r=.05) injection: HLLC-RD static/moving vs static N (only completed N) | `sedov_hllc_disk005_20260930_v1`, N: `sedov_2d_20260929_v1` | [N vs HLLC](../../local_runs/sedov_hllc_disk005_20260930_v1/analysis/thesis_preview/hllc_n_sedov_disk005_preview.png) |
| 5 | Static HLLC-RD, 1 hot | `sedov_hllc_nearest1_static_20260930_v1` | in 7, 8 |
| 6 | MMFV 1 hot cell; SWIFT 1 hot particle (same ID 8256) | `sedov_mmfv_single_20261001_v1`, `swift_sedov_single_20261001_v1` | in 7, 8 |
| 7 | Morton-style 2D density maps (8 runs) | `sedov_hllc_20260930_v1/analysis/maps_preview_v3/` | [2×4 grid](../../local_runs/sedov_hllc_20260930_v1/analysis/maps_preview_v3/sedov_maps_grid.png) |
| 8 | Mass-weighted radial profiles (8 runs) | `sedov_hllc_20260930_v1/analysis/profiles_mass_weighted_v1/` | [profiles](../../local_runs/sedov_hllc_20260930_v1/analysis/profiles_mass_weighted_v1/sedov_profiles_mass_weighted.png) |
| 9 | Geometry: half-face vs Voronoi face audit; schematic | `sedov_hllc_20260930_v1/analysis/` | [schematic](../../local_runs/sedov_hllc_20260930_v1/analysis/hllc_rd_schematic.png), [audit](../../local_runs/sedov_hllc_20260930_v1/analysis/halfface_audit.txt) |
| 10 | Experimental LDA/F1 + HLLC limited blend (bounds / positivity / ℓ=0) | `sedov_lda_hllc_20260930_v1` | [21 hot](../../local_runs/sedov_lda_hllc_20260930_v1/analysis/lda_hllc_nearest21_profiles.png), [1 hot](../../local_runs/sedov_lda_hllc_20260930_v1/analysis/lda_hllc_nearest1_profiles.png), [budgets](../../local_runs/sedov_lda_hllc_20260930_v1/analysis/lda_hllc_budgets.png), [scatter audit](../../local_runs/sedov_lda_hllc_20260930_v1/analysis/scatter_origin_audit.txt) |

Every native run preserves its source, Config, binary hash, ICs, parameters,
logs and verification.

* Runs that reuse binaries verify their hashes against the original archive.
* All runs returned 0 and reached t=.05, with one exception: the two
  positivity-only blend runs first stopped at AREPO's 0.85·TimeLimitCPU.
  This was a setup limit; they were resumed from restart files and the
  resume is recorded separately.

---

## 5. Main results

### 5.1 HLLC-RD vs references, 21 hot vertices, t=.05

| Method | raw ρ max | binned/mass-weighted ρ peak | core ρ (r<.05) | core p (analytic 1.605) | ΔM / ΔE |
|---|---:|---:|---:|---:|---:|
| HLLC-RD moving | 3.41 | 2.98 | .028 | 1.71 | −.33% / +.70% |
| HLLC-RD static | 2.46 | 2.33 | .031 | 1.53 | roundoff |
| Rusanov RD moving (before) | 2.63 | 2.43 | .198 | 1.72 | −.24% / −2.41% |
| MMFV 1st order | 3.43 | 3.10 | .028 | 1.67 | roundoff |
| MMFV 2nd order | 3.97 | 3.30 | .030 | 1.60 | roundoff |
| SWIFT SPHENIX | 3.60 | 3.00 | — | 2.38 (7 particles) | ΔE +.04% |

### 5.2 Findings

1. **Low-order dissipation.** Replacing Rusanov with the HLLC split lowers the
   moving core density sevenfold, to first-order MMFV's value, and raises the
   peak from 2.43 to 2.98. The remaining gap to second-order MMFV (3.30) is
   the spatial order.
2. **Robustness.**
   * Single-point injection completes on both meshes, without repair or
     floors:
     * moving: peak 3.00, core p 1.65, ΔE −1.61%;
     * static: peak 2.33, core p 1.53, roundoff conservation, 11120 steps.
   * N fails for 21 and 1 hot vertices.
   * With 130 hot vertices, static N matches static HLLC-RD in the mean
     (peak 2.30 vs 2.32, core p 1.56 vs 1.55). It is much noisier: v_r RMS
     .19 vs .024, and interior ρ up to .65. Moving N fails there too, while
     moving HLLC-RD reaches 2.94.
3. **The core plateau is the injected gas.** MMFV and moving HLLC-RD keep the
   adiabatically expanded injected gas, ρ_c≈(p_c/K_inj)^{1/γ}:
   * estimate .031 for 21 hot (MMFV .030, HLLC .028);
   * .097 for 130 hot (HLLC .090);
   * .005 for 1 hot (HLLC .0033).

   The point-source solution does not apply inside the injected mass. This
   explains why the 130-node bubble lies further below the analytic curve.
   Rusanov's .2 is numerical mixing.
4. **Correctness gates.**
   * Uniform-state defects ≤1.1e−15.
   * The flag-absent Rusanov moving binary built from the new source
     reproduces the archive bitwise at all 5 snapshots.
   * The ℓ=0 control of the blend reproduces HLLC-RD to 6e−12.
5. **Remaining issues of moving HLLC-RD.**
   * **First order.**
   * **Budget drift.** Mass −.33% and energy +.70% (21 hot); energy −1.61%
     (1 hot). Almost entirely in the step-opening connectivity/rebase term.
   * **Faceted shock front.** At t=.05 the front has largest Fourier mode
     ≈.7–.8% of R (m=5–6) for 1, 21 and 130 hot vertices.

   | Run | 21 hot | 1 hot |
   |---|---:|---:|
   | MMFV | .32% | .17% |
   | HLLC-RD static | .29% | .29% |
   | SWIFT | .58% | 1.87% |

   * Faceting is not caused by injection size or by low order (first-order
     MMFV is round).
   * SWIFT, which has no flips, is faceted too. A non-conservative flip
     rebase is therefore a plausible RD-specific contributor but not the
     whole story. The cause is not isolated.
6. **The experimental LDA/F1 + HLLC limited blend is not mature.**
   * With local ρ and K bounds it sharpens the shock (raw ρ 3.80) and improves
     core p (1.65), but has about 3× the HLLC velocity scatter.
   * Without bounds it overshoots (ρ 4.8), violates entropy at about 500
     nodes and collapses the timestep.
   * **User decision:** the thesis should favour the HLLC-RD result.

### 5.3 Status and next steps

* HLLC-RD is an opt-in research option (`RD_LOW_ORDER_HLLC`). Its source is
  uncommitted, and no thesis edit has been made. A draft text for §4.3.2 is
  awaiting review.
* Next steps:
  * a conservative positive remap at connectivity changes, which is also the
    decisive test for the faceting;
  * possibly a later, more robust high-order correction.
