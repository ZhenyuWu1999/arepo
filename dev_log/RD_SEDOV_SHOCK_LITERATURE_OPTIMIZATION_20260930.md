# Moving-mesh RD Sedov: shock treatments in the RD literature and optimization options

Author: Claude Code (Opus 5.5), 2026-09-30. Requested by Zhenyu Wu for a
possible Sedov result in thesis §4.3.2. The user judges the existing RD
result worse than AREPO MMFV and SWIFT, and notes that MMFV runs even
with all energy in one cell. This report contains a literature audit, a
diagnosis and one new diagnostic native experiment (first-order MMFV).
No RD solver change, thesis edit, commit or push.

## 1. What the existing moving RD result actually is

The existing **moving** RD Sedov result (log3 §§158, 164) is pure
first-order `RD_RUSANOV_LOW_ORDER` (trapezoidal fluxes, element scalar
Rusanov dissipation) with the lumped RK2 stages. LDA+Rusanov
(`RD_LDA_RUSANOV_BLEND`) and B/Bmax (`RD_LDA_RUSANOV_B_SENSOR`) were run
only on a **static** mesh (§§167, 170). No LDA-based moving Sedov exists.

| t=.05, glass128², 21 hot points | raw ρ max | radial-mean ρ peak | ρ min | ΔE/E |
|---|---:|---:|---:|---:|
| MMFV moving (2nd order, exact Riemann) | 3.971 | 3.302 | .0284 | roundoff |
| SWIFT SPHENIX | 3.604 | 2.995 | .0369 | +.040% |
| RD moving Rusanov (1st order) | 2.630 | 2.428 | .1960 | −2.415% |
| RD static Rusanov (1st order) | 2.002 | 1.957 | .1248 | roundoff |
| RD static LDA/F1+Rusanov, positivity only | 3.791 | 2.798 | .0191 | roundoff |
| RD static Bmax (LDA/Rusanov) | 2.179 | 2.147 | — | roundoff |

Numbers are copied from the archived reports (MMFV comparison, blend and
B-sensor reports); analytic shock density is 4.

## 2. Why MMFV survives a single hot cell while RD N/LDA do not

AREPO MMFV's first-order building block is a one-dimensional Riemann
problem per face, solved exactly (vacuum-capable). A first-order Godunov
update is positivity preserving under a CFL condition. Around it, the
native code has two safeguards (`src/hydro/finite_volume_solver.c`):

* `face_add_extrapolations` (line 1323) drops the MUSCL-Hancock space/time
  extrapolation at a face whenever it would give negative ρ or p, so that
  face reverts to first order;
* `face_limit_fluxes` (line 1649) caps the mass flux at 0.9 of the upwind
  cell mass.

Einfeldt, Munz, Roe & Sjögreen (1991, JCP 92:273) showed that
linearized (Roe-type) Riemann solvers are not positively conservative
near low densities; Godunov and HLLE are. RD N and LDA use a Roe
parameter-vector linearization over each triangle, and LDA is linear,
hence not positive (Godunov's theorem). Our strong-Sedov N/LDA failures
(§156), Morton et al. (2023 §5.2.3: LDA1/LDA2 unstable, blending
reduces to N) and Paardekooper (2017, next section) are consistent with
this. Rusanov (a Lax–Friedrichs/HLLE-type dissipation) restores
positivity, which is why every Rusanov case, including 1- and 7-point
injection (§160), completes.

## 3. How RD papers treat shocks and blast waves

| Source | Shock treatment | Blast/strong-shock evidence |
|---|---|---|
| Deconinck & Ricchiuto review, §§3.6.7, 5.1.2 | Blended LDA/N, Θ=\|Φ_E\|/Σ\|φ_j^N\|; or limited (PSI) schemes. Systems: characteristic decomposition along a direction ξ; limit each wave; project back. | Limited N on double Mach reflection sharper than a 2nd-order Roe FV. States that limited schemes are "not entirely satisfactory in smooth regions". |
| Dobeš & Deconinck (2008, JCAM 215) "Bx" | Scalar θ=s²h, s=(−L∇·v/(\|v\|max−\|v\|min))⁺: nonzero only under compression (as summarized in Paardekooper 2017, Eqs. 54–56). | Steady/unsteady aerodynamic shocks; no blast. |
| Abgrall (2006, JCP 214); Abgrall, Bacigaluppi & Tokareva (2019, CAMWA; arXiv 1806.03986) | Rusanov (LxF) residual, PSI-limited in characteristic variables (Eqs. 33–38, direction = mean velocity); blend with LxF using Θ=\|φ̂_K\|/Σ\|φ̂_σ^LxF\| (Eq. 37); Burman jump stabilization added after limiting (Eq. 39). Near-zero pressure: component-wise limiting (Remark 2). | Sod, 1D Woodward–Colella blast, Shu–Osher, 2D Sod, Mach-3 step. No Sedov. |
| Bacigaluppi, Abgrall & Tokareva (MOOD RD) | A-posteriori cascade Galerkin+jump → Rusanov-PSI+jump → classical Rusanov. | No Sedov (log3 §165). |
| Paardekooper (2017, MNRAS 469:4306), §§3.3.3, 5.2 | B, Bmax, Bmin, Bx blends of LDA and N. | Noh: "less diffusive blended schemes either fail on this problem, or need backup fluxes produced by the N scheme". Cylindrical blast (Gaussian pressure over ≈2.5h): N ≈ HLL; B has larger errors. |
| Morton, Khochfar & Wu (2023), §5.2.3 | N, LDA, per-component blend. | Sedov: LDA1/LDA2 unstable; blend strongly favours N. |
| Campoli, Quemar, Bonfiglioli & Ricchiuto (2017), ALE RD shock fitting | Arpaia ALE-RK RD; N, LDA, LDAN, SU, and SU blended with limited LxF (Bc). | Captured shocks with LDA/LDAN give wiggles and non-smooth downstream contours; fitting removes them. Only weak interactions. |
| Abgrall, Lipnikov, Morgan & Tokareva (2020, SISC) | Staggered Lagrangian RD + MARS viscosity. | Sedov peaks 4.908/5.459 (16²/32², γ=1.4, exact 6). Different state layout; not transplantable (log3 §166). |
| Guermond, Popov & Saavedra (2020, JCP 401:108927), ALE P1 continuous FE | Low order GMS-GV1: edge graph viscosity from a guaranteed maximum wave speed of each local Riemann pair. High order: entropy-viscosity. Convex limiting on density and specific entropy with relaxed local bounds (§4.4, Eqs. 4.8–4.10). | Noh, γ=5/3, p0=1e−15, h=1/120: max ρ 14.59 (low order) vs 16.29 (limited), exact 16. Woodward–Colella, Leblanc, Saltzman. Connectivity fixed. |
| Deconinck & Ricchiuto §3.6.1 (Eq. 57); Abgrall (2017, arXiv 1708.03108) | A median-dual FV with any conservative flux is an RD scheme; its element residuals sum to the trapezoidal Φ_T. | Allows a Riemann-solver flux as RD low-order scheme. |

Batten, Clarke, Lambert & Causon (1997, SIAM J. Sci. Comput. 18) give HLLC
wave-speed choices that keep HLLC positively conservative.

Three lessons for our problem:

1. No RD paper found has a second-order collocated (LDA/limited) Sedov on a
   reconnecting moving mesh. The only successful RD Sedov papers are
   first-order N (Morton; Paardekooper's blast) and staggered Lagrangian
   RD with artificial viscosity.
2. The RD shock-capturing mainstream (limited LxF in characteristic
   variables + stabilization) is designed for monotone shocks, not for
   positivity in near-vacuum. Positivity is supplied separately (MOOD
   fallback, or convex limiting).
3. The closest analogue to our P1 median-dual ALE scheme is the
   Guermond–Popov–Saavedra ALE method. Its ingredients are an edge-local
   low-order viscosity and convex limiting with *local* density and
   specific-entropy bounds, not only positivity.

## 4. Diagnosis of the moving RD result

### 4.1 First order everywhere

The moving run contains no high-order correction. The static evidence shows
what a correction buys: static Rusanov raw peak 2.00 → blend 3.79, core
ρ .136 → .028.

### 4.2 Rusanov dissipation cancels the Lagrangian advantage for density

The element dissipation in `src/hydro/rd_rusanov.h` is

    alpha_T = 1/2 max_{j,k} ( |(v_j - w_T).n_k| + c_j |n_k| ),
    phi_i  += alpha_T (U_i - U_j)/3 for every pair,

applied identically to ρ, m and E. On a quasi-Lagrangian mesh |v−w_T|≈0,
yet alpha_T ≈ c ℓ/2 remains. The mass-diffusion rate is therefore set by
the sound speed, not the relative velocity. A contact-resolving Riemann
solver (exact, HLLC) instead gives a mass flux ∝ (u−w)·n, which is nearly
zero on this mesh. Worse, alpha_T scales with edge length ℓ, which grows as
cells expand. The moving core has typical √S≈.062 against .0078 static
(§161). The hot, rarefied core (large c, large ℓ) is where this diffusion is
strongest. This explains the ordering of the central density plateau:
moving Rusanov .196 > static Rusanov .125 > MMFV .028.

### 4.3 Global conservation

Moving Rusanov loses 2.41% energy and .24% mass through connectivity
changes (§§158–159). By the 2D similarity law R ∝ E^{1/4}, that shifts the
shock radius by only ~.6%. This is visible in a budget panel but does not
explain the profile shape. The positive conservative remap remains a
separate task (§159).

## 5. First-order MMFV diagnostic (new native runs)

Purpose: separate spatial order from the form of the low-order dissipation.
MMFV with face extrapolation disabled is first order but keeps a
contact-resolving Riemann flux on the moving mesh.

* Archive `../local_runs/sedov_mmfv_first_order_20260930_v1/`; runner
  `examples/Sedov_2d/run_mmfv_first_order.py`; analysis
  `examples/Sedov_2d/analyze_mmfv_first_order.py`.
* Configs `Config_MMFV_moving_first_order.sh` and `..._hllc.sh` are exactly
  `Config_MMFV_moving.sh` plus `DISABLE_SPATIAL_EXTRAPOLATION` and
  `DISABLE_TIME_EXTRAPOLATION` (plus `RIEMANN_HLLC`); both are diagnostic only.
* Source frozen from HEAD `2858d43` + working-tree patch + untracked files;
  independent BUILD_DIRs. Binary SHA256: exact
  `f9f9a95737080d9e9b161cb868657318cb217ae9db39e1eb0578e2dff1299f49`, HLLC
  `a0dbb46fe69e8bba05f96d142f5bdb0f20dc499b80b7036455f80a49124812ae`.
* Identical hash-checked IC (`5d0be3bb…`, Voronoi hot-energy normalization)
  and parameters as the second-order MMFV run; only paths differ. CFL .1,
  equal adaptive steps, one rank, OMP/BLAS 1.
* Uniform gates: 2.05e−13 for both. Science runs: 970/961 steps, 126/118 s.
  All saved states positive and finite, mass/energy conserved to roundoff.

| t=.05 | raw ρ max | mean ρ peak (r) | ρ min | ρ̄ r<.05 (n) | ρ̄ r<.1 (n) | p̄ r<.05 | ΔE/E |
|---|---:|---:|---:|---:|---:|---:|---:|
| MMFV 2nd order, exact | 3.971 | 3.302 (.2575) | .0284 | .0300 (4) | .0306 (25) | 1.596 | 4e−16 |
| MMFV 1st order, exact | 3.434 | 3.099 (.2525) | .0275 | .0276 (4) | .0321 (19) | 1.670 | 2e−16 |
| MMFV 1st order, HLLC | 3.427 | 3.070 (.2475) | .0275 | .0280 (3) | .0319 (13) | 1.687 | 2e−16 |
| RD moving Rusanov, 1st order | 2.630 | 2.428 (.2425) | .1960 | .1977 (3) | .2115 (12) | 1.721 | −2.415% |

ρ̄ is sample mass divided by sample area inside r (Voronoi volume for FV,
median-dual area for RD). The analytic area means are .0043 and .0345. p̄ is
the unweighted sample mean; the analytic value is 1.605. Radial means use
bins of .005. Figure: `analysis/mmfv_first_order_profiles.png` (visually checked).

Interpretation:

* From moving Rusanov RD to first-order MMFV, both first order with the same
  core sampling (3–4 samples inside r<.05), the mean peak rises from 2.43 to
  3.07–3.10. The core density falls sevenfold, from .198 to .028.
* From first- to second-order MMFV the gain is much smaller: mean peak
  3.10→3.30, core pressure 1.67→1.60.
* HLLC and exact Riemann are practically identical at first order.
* Conclusion: the main deficiency of the moving RD result is the
  **form of the low-order dissipation**. The missing second order and the
  sparse core sampling are secondary.
* The core-pressure excess (+4–5% in first-order MMFV, +7% in RD) is
  largely a first-order effect.

Limits: this is not a controlled flux-only ablation. The runs also differ in
Voronoi versus median-dual control volumes, forward-Euler versus lumped RK2
stages, and exact FV conservation through reconnection versus RD's −2.4%.
These differences were not isolated. Their plausible effect is much smaller
than the observed factor 7 in core density, but that remains an inference.
All MMFV samples (first and second order) are plotted at cell centroids via
the same `fv_state` loader as the earlier MMFV comparison; RD at nodes.


## 6. Recommended optimization order (proposals, not implemented)

### 6.1 Replace the low-order dissipation with an edge Riemann (HLLC) flux (first priority)

**Follow-up, same day (Claude Code, Opus 5.5).** Implemented as
`RD_LOW_ORDER_HLLC` and tested natively; see
[RD_SEDOV_HLLC_LOW_ORDER_20260930.md](RD_SEDOV_HLLC_LOW_ORDER_20260930.md).
The moving 21-point results were:

* mean ρ peak 2.98, core ρ .0276, which reaches first-order MMFV
  (3.10 / .0276);
* single-hot-node injection completes;
* the flag-absent Rusanov replay is bitwise identical to the archive;
* the moving budget drift remains (mass −.33%, energy +.70%).

The text below is the original proposal.

For triangle T and vertices i≠j, let ν_ij^T be the scaled normal of the
median-dual segment inside T (edge midpoint to centroid), oriented from i to
j. Let G(U)=F(U)−U⊗w_T, as in the current kernel. Define

    phi_i^T = sum_{j in T, j != i} [ Ghat_HLLC(U_i, U_j; nu_ij^T, w_T) - G(U_i).nu_ij^T ].

The flux is conservative, and the median-dual identities hold
(Deconinck & Ricchiuto Eqs. 55, 57). Hence sum_i phi_i^T =
1/2 sum_j G(U_j).n_j. Signs are written in the kernel's inward-normal
convention and must be rechecked in an implementation. This is the same trapezoidal ALE total as the present
Rusanov kernel. The existing geometry, lumped RK2 stages, b_i checks and
uniform-state preservation therefore carry over unchanged. The scheme is
still an RD scheme in the fluctuation-splitting sense (FV-RD), not a return
to AREPO's cell-centred FV.

* Solve HLLC in the frame moving with w_T. The structure of
  `src/hydro/riemann_hllc.c` can be reused. Its Davis speeds
  min(u_L−c_L, u_R−c_R) are not guaranteed bounds. For positivity use
  Einfeldt/Batten speeds or a guaranteed maximum-speed estimate
  (Guermond & Popov 2016, JCP 321).
* Derive the stage CFL from the one-sided pair Riemann updates
  (Perthame–Shu-type convex decomposition). Keep fail-hard checks of the
  HLLC star states, density and internal energy, like the current pair-bar
  checks. No clipping or floors.
* Keep classical Rusanov as an explicit last-resort fallback option,
  MOOD-style, rather than deleting it.
* Expectation (to be tested, not a result): moving RD approaches first-order
  MMFV, i.e. mean peak ≈3 and core ρ ≈.03.
* Validation: uniform gate; 1D-in-2D Sod contact; static/moving Sedov with 21
  and 1 hot node; budgets.

An edge-local Rusanov (pair wave speed, GMS-GV1-like) is cheaper. It reduces
alpha but keeps mass diffusion ∝ c, so it should not cure the core. It is
therefore only a possible control.

### 6.2 Then add a limited high-order correction on the moving mesh

* Port the static convex-limited LDA/F1 correction (`RD_LDA_RUSANOV_BLEND`)
  to ALE, with the §6.1 flux as low-order endpoint.
* Use the actual ALE stage weights (modified S_i, b_i) in the convex
  decomposition.
* Represent the Gauss3−trapezoid total difference as antisymmetric
  shared-edge corrections.
* Add **local** bounds from the low-order states, not positivity alone:
  density min/max and a specific-entropy minimum. Relax them in smooth
  regions as in Guermond–Popov–Saavedra Eqs. 4.8–4.10; see also the existing
  design `RD_LDA_RUSANOV_CONSTRAINT_DESIGN_20260929.md`.
* Why local bounds are needed:
  * positivity-only static blending left 34× larger interior v_r scatter
    (§168);
  * Campoli et al. report the same post-shock roughness for captured LDA/LDAN
    shocks in ALE RD.
* Expected gain beyond §6.1 is of the size MMFV gains from first to second
  order: mean peak 3.1→3.3, core p 1.67→1.60.
* Smooth-order gates (contact, Yee) must show that the limiter relaxes.

Alternative high-order candidate, lower priority: Rusanov/HLLC-PSI in
characteristic variables with Θ blending and jump stabilization
(Abgrall–Bacigaluppi–Tokareva), tested inside the same convex limiter. It
has no Sedov evidence and no positivity guarantee of its own.

### 6.3 Conservation across reconnection

The −2.4% energy / −.24% mass come from connectivity change, independent of
§§6.1–6.2. A conservative positive patch remap (convex low/high blend within
the patch, §159) is needed before the thesis can claim conservation for a
moving Sedov. Otherwise report the budget honestly.

### 6.4 Not recommended

* Tuning Θ/B/Bmax/Bx alone:
  * static Bmax peak 2.15 is below moving Rusanov's 2.63;
  * Paardekooper found blended schemes fail or need N backup on Noh, and
    worse errors on the cylindrical blast.
* Treating N as the safe endpoint: Roe linearization is not positively
  conservative (Einfeldt 1991), and it failed natively (§156).
* Enlarging the injection or smoothing the IC: no improvement (§160).
* Clipping ρ or p.

### 6.5 Thesis implication

The current moving RD Sedov figure reflects the Rusanov dissipation choice,
not the attainable quality of RD on a moving mesh. If time is short, §6.1
alone should give a robust, contact-preserving first-order moving RD. It
would be comparable to first-order MMFV and should be presented with its
order stated. §6.2 is needed to approach second-order MMFV. No thesis text
has been changed.

## Sources

* Deconinck & Ricchiuto, *Residual Distribution Schemes: Foundations and
  Analysis* (review), local text
  `../local_runs/thesis_ch3_rednotes_20260927_235021/sources/deconinck_review.txt`.
* Abgrall, Bacigaluppi & Tokareva, [arXiv:1806.03986](https://arxiv.org/abs/1806.03986).
* Paardekooper 2017, [arXiv:1705.02028](https://arxiv.org/abs/1705.02028).
* Morton, Khochfar & Wu 2023, [arXiv:2204.01757](https://arxiv.org/abs/2204.01757).
* Guermond, Popov & Saavedra 2020, [JCP 401:108927](https://people.tamu.edu/~guermond/PUBLICATIONS/guermond_popov_Saavedra_JCP_2020.pdf).
* Guermond, Nazarov, Popov & Tomas 2018, [arXiv:1710.00417](https://arxiv.org/abs/1710.00417).
* Campoli, Quemar, Bonfiglioli & Ricchiuto 2017, [draft](https://www.math.u-bordeaux.fr/~mricchiu/sf-draft.pdf).
* Abgrall, Lipnikov, Morgan & Tokareva 2020, [arXiv:1811.00057](https://arxiv.org/abs/1811.00057).
* Abgrall 2017, [arXiv:1708.03108](https://arxiv.org/abs/1708.03108).
* Dobeš & Deconinck 2008, [JCAM 215](https://doi.org/10.1016/j.cam.2006.03.046)
  (formula taken from Paardekooper's summary; the original was not read here).
* Einfeldt, Munz, Roe & Sjögreen 1991, JCP 92:273; Batten, Clarke, Lambert &
  Causon 1997, SIAM J. Sci. Comput. 18:1553 (cited from standard knowledge;
  not re-read in this session).
* Ricchiuto & Abgrall 2010 (JCP 229:5653) and the Arpaia–Ricchiuto–Abgrall
  ALE report could not be downloaded here (publisher/HAL access blocked);
  their shock-capturing details are therefore not claimed in this report.

