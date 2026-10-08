# Edge-HLLC low-order RD for Sedov: thesis/code compatibility and first native test

Author: Claude Code (Opus 5.5), 2026-09-30. Requested by Zhenyu Wu after the
[shock literature/optimization report](RD_SEDOV_SHOCK_LITERATURE_OPTIMIZATION_20260930.md):
read the thesis (including the two "delete red text" commits), check whether
step 1 (edge HLLC low order) is compatible with the AREPO-RD code, then test it
if feasible. No thesis edit, default-Config change, commit or push.

## 1. What the thesis and its deleted red text constrain

Thesis repository `~/Desktop/MyThesis/Zhenyu-PhDThesis`, main `447c9a0`.
Read: Chapter 4 in full (§4.2 theory, §4.3 implementation/tests/ongoing work),
Chapter 5, and the Chapter 3 sections on distribution schemes and timesteps.
The two red-text deletions are `e4fcd84` (§4.2 alternatives, 538 lines) and
`beb977d` (chapter-end implementation block and alternatives, 432 lines).
Items relevant to a new low-order kernel:

| Thesis item | Status in text | Consequence for the HLLC kernel |
|---|---|---|
| Arpaia residual φ̃ = ∮F·n − ∫σ·∇U, evaluated with σ̄_T; ∇·σ absorbed into the modified divisor D_i (§4.2) | presented method | The kernel must keep the same element total ½Σ_j G_j·n_j with G=F−U⊗σ̄_T. It does. |
| Element co-moving frame, Galilean matrix G(b_T), ALE flux identity (e4fcd84; `RD_ELEMENT_COMOVING_FRAME`) | deleted alternative | HLLC is solved in the frame b_T=σ̄_T and mapped back by G(−σ̄_T). This uses the same identity inside the kernel. The Rusanov path still forbids the global option. |
| Storage Q=mU, divisor D_i, endpoint defect d_i and connectivity rebase defect (beb977d) | deleted detail; §4.3.3 prose | Unchanged. HLLC cannot remove the moving budget drift. |
| RD CFL Δt=C·D_i/Σα_T (beb977d) | deleted detail | Same structure. HLLC supplies per-vertex Σ\|ν_ij\|s_ij instead of Σ4α_T/3. |
| Campoli endpoint mass/divisor (e4fcd84) | deleted alternative | Not used; the Rusanov path forbids `RD_ALE_CAMPOLI_MASS`. |
| Voronoi-cell evolution with RD as corner fluxes (beb977d) | deleted alternative | Not this. Control volumes remain median-dual with Arpaia geometry. |
| Conservative topology operators, true predictor before rebuild, pending numerators, moving hierarchy (beb977d; §4.3.3) | unimplemented | Independent of the kernel. They remain open. |
| Chapter 3: Rusanov/LxF are RD-family members but not multidimensional-upwind | presented | The HLLC edge scheme is the FV-RD form (Deconinck & Ricchiuto §3.6.1). Present it as a positive low-order fallback, not a new MU scheme. |
| Chapter 5 future work: a more generally applicable blended scheme | presented | Step 2 (limited high-order correction) is where LDA returns. |

## 2. Compatibility with the code

`RD_RUSANOV_LOW_ORDER` already provides, independent of the element kernel:

* Arpaia midpoint geometry and divisor;
* the lumped N-path RK2 temporal terms;
* per-stage CFL and convex-weight checks (0<b_i≤1, C_i/(2b_i)≤1);
* admissibility checks before primitive recovery;
* the timestep selector hook.

It calls one kernel per triangle with the three conserved states, the
length-weighted inward normals and w_T=σ̄_T. It expects nodal residuals, the
element total and a stage coefficient. The new option therefore changes only:

* `src/hydro/rd_hllc.h` (new kernel);
* two call sites in `residual_distribution_solver.c`: the timestep
  selector and the stage assembly, both of which now accumulate a
  per-vertex coefficient;
* an include and a guard that `RD_LOW_ORDER_HLLC` requires `RD_RUSANOV_LOW_ORDER`;
* `defines_extra` (`RD_LOW_ORDER_HLLC`, `RD_HLLC_H`).

Inward normals are guaranteed by the A3 signed-area assertion in
`triangle_get_normals_area` and by the ALE geometry area checks. The kernel
also rejects clockwise input. A global sign flip of normals cannot be detected
from normals alone: it is the 180°-rotated triangle.

The option inherits the Rusanov restrictions: one rank, equal steps, periodic,
hydro only. Step 2 (LDA correction) will need the Gauss3–trapezoid total
difference as shared-edge corrections; the existing blend code is static-only.

## 3. Scheme

With n_j the inward normal opposite j, the median-dual face inside T between
i and j has scaled normal ν_ij=(n_j−n_i)/6, pointing from i to j. This was
checked on a right triangle: (2,1)/6 is normal to midpoint→centroid, with the
same length. Hence Σ_{j≠i}ν_ij=−n_i/2 and ν_ji=−ν_ij.

    phi_i^T = sum_{j != i} [ H(U_i, U_j; nu_ij) - G(U_i).nu_ij ],   G = F - U (x) w_T.

The sum over i is ½Σ_j G_j·n_j, the Rusanov kernel's trapezoidal ALE total.
Each pair is evaluated once. The left fluctuation comes from HLLC, and the
right one is (G_j−G_i)·ν_ij minus the left. Element conservation therefore
holds to roundoff, and bitwise-identical neighbours give exactly zero.

HLLC details:

* Frame moving with w_T.
* Wave speeds S_L=min(u_L−c_L, u_R−c_R, ũ−c̃) and S_R=max(u_L+c_L, u_R+c_R, ũ+c̃),
  with ũ, c̃ Roe averages (Einfeldt/Batten plus Davis).
* Toro's star states. Both star states are checked for positive density and
  internal energy, and S_L<S*<S_R is required. Otherwise the kernel returns
  failure and the solver aborts (no floors).

Positivity of one forward-Euler stage:

* For the one-sided HLLC Riemann average, U_L−(t/a)(Ĥ−F_L) is the mean of
  the HLLC fan over [−a,0], and U_R+(t/a)(Ĥ−F_R) the mean over [0,a], for
  a ≥ t·max(|S_L|,|S_R|).
* Writing the nodal update as a convex combination of these averages gives
  the sufficient condition C_i=(dt/S_i)Σ_{T,j}|ν_ij|s_ij ≤ 1.
* The existing stage checker applies it with S_i the Arpaia divisor, and the
  corrector adds the b_i scaling.

A contact at rest relative to w_T has zero HLLC residual. Rusanov instead
diffuses it at rate ∝c. This is the property the first-order MMFV diagnostic
identified as decisive.

## 4. Kernel verification

`tests/rd/test_hllc_positivity.py` compiles the real header and runs 4000
random CCW triangles with ρ∈[1e−3,1e3], p∈[1e−6,1e3], |v|,|w|~3, and γ=1.4 or 5/3:

| Check | Result |
|---|---|
| Conservation against an independent boundary quadrature | worst 3.8e−16 |
| Match to an independent Python HLLC (standard flux form, lab variables, face moving with w) | 2.7e−13 relative to flux scale |
| Coefficients | agree to rtol 1e−10; one trial differed by 1.1e−12 from the cancelling Roe sound speed |
| Galilean covariance (states and w shifted by b, residual maps by G(b)) | 4.3e−12 |
| Forward step at 0.01–0.999 of the coefficient bound | always admissible; minimum internal-energy ratio .196 |
| Uniform state | exact zero |
| Resting contact (v=w, equal p, density ratio 133) | zero to 1e−14·scale |
| Clockwise vertex order | rejected |

Two setup errors were fixed without changing the kernel:

* `-Werror` on the unused static Rusanov function in the test harness;
* an incorrect orientation test that negated normals (undetectable by
  construction; see §2).

All five existing `make check_rd` programs pass.

## 5. Native campaign

### 5.1 Setup and provenance

| Item | Value |
|---|---|
| Archive | `../local_runs/sedov_hllc_20260930_v1/` |
| Runner / analysis | `examples/Sedov_2d/run_hllc.py`, `analyze_hllc.py` |
| Configs | `Config_HLLC_{static,moving}.sh`: the archived Rusanov options plus `RD_LOW_ORDER_HLLC` |
| Source | HEAD `2858d43` + working-tree patch + untracked files, frozen; independent BUILD_DIRs |

Binaries (SHA256):

* HLLC_static `6d7f102e…d50402`
* HLLC_moving `fd312882…9883`
* Rusanov_moving (flag absent) `b8f058ff…1fd`

Build warnings are the same 18 pre-existing ones in all three builds.

Inputs and settings:

* ICs are byte-identical to the archived Rusanov campaign (glass128², nearest21,
  median-dual hot-energy normalization) and to the 1-node sweep IC.
* Parameters use the archived Rusanov templates with the same rewrite rule.
* γ=5/3, p0=1e−6, E_hot=1, CFL .1, cap .01, equal adaptive steps, lab frame,
  one rank, OMP/BLAS 1.

### 5.2 Gates

* **Uniform:** maximum defect 5.55e−16 (static), 6.66e−16 (moving),
  1.11e−15 (Rusanov).
* **Regression:** the flag-absent Rusanov moving binary, built from the new
  source, reproduces the archived moving Rusanov run **bitwise** in all 5
  snapshots (IDs, positions, ρ, p, v, masses). The edits leave the default
  path unchanged.
* **Science runs:** all 7 native runs return 0.
  * Accepted science stages: 8850 static, 4884 moving/21, 5716 moving/1. All
    passed the density, internal-energy, CFL and b checks with no
    aborts.
  * Maximum stage CFL .110 (bound 1); minimum b .4947; minimum internal
    energy density 1.5e−6 (the background).
* **Run times:**
  * static 408 s (4425 steps; archived Rusanov 216 s, 3051 steps);
  * moving/21 677 s (2442 steps; Rusanov 547 s, 3118 steps);
  * moving/1 713 s (2858 steps).

### 5.3 Results at t=.05

| Case | raw ρ max | mean ρ peak (r) | ρ min | ρ̄ r<.05 (n) | ρ̄ r<.1 | p̄ r<.05 | ΔM/M | ΔE/E |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **HLLC RD moving, 21** | 3.413 | 2.980 (.2475) | .0276 | .0276 (4) | .0289 | 1.714 | −.329% | +.698% |
| **HLLC RD static, 21** | 2.461 | 2.328 (.2525) | .0269 | .0309 (130) | .0628 | 1.531 | 0 | −2e−16 |
| **HLLC RD moving, 1** | 3.402 | 2.999 (.2475) | .0033 | .0033 (1) | .0250 | 1.654 | −.335% | −1.606% |
| Rusanov RD moving, 21 | 2.630 | 2.428 (.2425) | .1960 | .1977 (3) | .2115 | 1.721 | −.240% | −2.415% |
| Rusanov RD static, 21 | 2.002 | 1.957 (.2525) | .1248 | .1360 (130) | .1735 | 1.444 | roundoff | roundoff |
| Rusanov RD moving, 1 | 2.616 | 2.439 (.2425) | .1958 | .1958 (1) | .2065 | 1.781 | −.238% | −2.576% |
| MMFV 1st order, exact | 3.434 | 3.099 (.2525) | .0275 | .0276 (4) | .0321 | 1.670 | 0 | 2e−16 |
| MMFV 2nd order, exact | 3.971 | 3.302 (.2575) | .0284 | .0300 (4) | .0306 | 1.596 | 2e−16 | 4e−16 |

The analytic area-mean core density is .0043 (r<.05) / .0345 (r<.1), and the
analytic core p is 1.605. ΔM and ΔE are relative to the saved initial state.
Figures (visually checked):

* `analysis/hllc_nearest21_profiles.png`
* `analysis/hllc_nearest1_profiles.png`
* `analysis/hllc_budgets.png`

### 5.4 Interpretation and limits

**What changed on the moving mesh (21 points):**

* The central density drops sevenfold (.198→.028) and matches first-order
  MMFV exactly to three digits.
* The mean ρ peak rises from 2.43 to 2.98 (first-order MMFV 3.10), and the
  raw maximum from 2.63 to 3.41 (3.43).
* The prediction of the first-order MMFV diagnostic is therefore confirmed
  within RD: the Rusanov dissipation form, not the RD geometry, caused the
  core plateau.

**Static mesh.** HLLC lowers the core density fourfold (.136→.031) and raises
the peak (1.96→2.33), with conservation at roundoff. Mesh motion then gives
the additional shell sharpening.

**Robustness.** The single hot node runs to t=.05 without any repair or floor
(mean peak 3.00). This matches MMFV's tolerance of point injection. Rusanov
also survives it, but with the same .196 core plateau.

**Still open:**

* *Order.* Spatial first order. The remaining peak gap (2.98 vs
  second-order MMFV 3.30) and the core-pressure excess (+7%, also +4% in
  first-order MMFV) are first-order effects; they need step 2.
* *Conservation.* The moving budgets remain non-conservative: mass −.33%,
  energy +.70% (21 points) or −1.61% (1 point), with non-monotonic energy
  histories. The kernel does not touch the connectivity-rebase and
  endpoint-divisor terms (beb977d Eq. `ALE_RD_native_endpoint_balance`).
  Sharper profiles change the size and sign of those defects. The drift is
  not attributed to the kernel, and it is not claimed smaller in general.
* *Sampling.* Only five snapshots per run.
* *Not tested:* MPI, hierarchy and topology repair are not supported by
  this option. Smooth-flow accuracy (first order) and 2D Sod contacts were
  not run here.
* *Classification.* HLLC edge RD is not multidimensional-upwind. In thesis
  terms it is an FV-RD low-order scheme (Chapter 3 already classifies
  Rusanov/LxF the same way).

## 5.5 Naming and provenance (user question, same day)

No paper found proposes an "HLLC-RD" scheme; the label is shorthand for this
construction. The search was brief and not exhaustive.

What the literature does establish:

* Deconinck & Ricchiuto §3.6.1, Eqs. 55–57: a first-order median-dual FV
  scheme with any conservative numerical flux is a fluctuation-splitting/RD
  scheme, and its nodal residuals sum to the trapezoidal element residual.
* Abgrall (2017, arXiv 1708.03108) shows the converse: RD schemes admit flux
  forms.
* HLLC is due to Toro, Spruce & Speares (1994); the wave speeds follow
  Einfeldt (1988) and Batten et al. (1997).
* Vertex-centred FV with HLLC is common in unstructured CFD.

As RD, the scheme is:

* **Structurally RD.** Each triangle's residual Φ_T is split
  element-locally into φ_i^T with Σφ_i^T=Φ_T. The split uses the HLLC
  fluctuations A⁻ΔU/A⁺ΔU on the three median-dual segments inside T. This is
  the multi-dimensional analogue of 1D Roe fluctuation splitting (thesis
  Chapter 3, "From Roe's solver to RD").
* **Not a multidimensional-upwind or linearity-preserving RD scheme.** The
  split comes from three fixed-direction 1D Riemann problems, not from the
  element characteristic structure K_i^±. It is first order, with the same
  status as the Rusanov/LxF distribution.

Recommended wording: "a first-order positivity-preserving fallback in
fluctuation-splitting form, splitting each element residual along the
median-dual faces with HLLC fluctuations". Do not call it a new MU scheme.
The multidimensional RD character must come from the limited LDA correction
(step 2).

### What the code does, in terms of thesis Figure 4.2

The schematic `analysis/hllc_rd_schematic.png` is drawn by
`examples/Sedov_2d/plot_hllc_schematic.py`. It reuses the node layout of
Figure 4.2 (nodes A–E; triangles T1, T2, T3); the geometry is illustrative.

The loop runs over Delaunay triangles, as in Figure 4.2. AREPO still builds
its Voronoi tessellation, but the RD hydro never uses Voronoi faces. For
T3=CDE, the kernel does the following:

1. Take the nodal states U_C, U_D, U_E, the midpoint inward normals and
   w_T3.
2. Form Φ_T3=½ΣG_j·n_j. This is the same residual as the Rusanov RD.
3. Solve three first-order HLLC problems in the w_T3 frame, one on each
   median-dual segment G–m_CD, G–m_DE, G–m_EC, with normal ν_ij=(n_j−n_i)/6.
4. Give the left and right fluctuations to the two endpoint nodes:
   * φ_C = A⁻ΔU(C,D) + A⁺ΔU(E,C)
   * φ_D = A⁺ΔU(C,D) + A⁻ΔU(D,E)
   * φ_E = A⁺ΔU(D,E) + A⁻ΔU(E,C)

   Their sum is Φ_T3. These three shares are the arrows in Figure 4.2.

Each node then sums its shares from all incident triangles, divides by the
Arpaia divisor and runs the RK2 stages. Figure 4.2's triangle scheduling
therefore applies unchanged in principle; the option itself still requires
equal steps.

Compared with MMFV:

| | MMFV | Edge-HLLC RD |
|---|---|---|
| Loop | Voronoi faces | Triangles |
| Riemann problems | One per Voronoi face O₂O₃, the straight bisector of CD | Two per Delaunay edge CD: half faces m_CD–G₂ and m_CD–G₃, each in its own triangle frame |
| States | MUSCL-Hancock reconstructed face states | First-order nodal states |
| Update | Flux exchanged between Voronoi cells | Element residual shares |

The two face families coincide only when centroids and circumcentres
coincide (equilateral triangles); a glass mesh is close to that.

The existing Rusanov kernel is pairwise too: α_T(U_i−U_j)/3. Every
conservative RD distribution admits such a pairwise flux form (Abgrall 2017).
What changes is only the pair dissipation: a sound-speed scalar for Rusanov,
the HLLC wave model here.

### Two HLLC solves per Delaunay edge (user question)

Each interior Delaunay edge CD is solved twice, once in each adjacent
triangle. This is not double counting.

* **Weighting.** Each solve is weighted by its own half-face length |ν^T|.
  Together the two halves m_CD–G₂ and m_CD–G₃ form the single median-dual
  face between C and D.
* **Where the two solves differ.** They use the same nodal states but
  different normal directions (the face bends at m_CD) and different frame
  velocities w_T. The central part of the flux is linear in ν, so it equals
  that of one straight face. Only the dissipation differs:
  Σ_T |ν^T| s^T ≥ |Σ_T ν^T| s. A bent face is therefore slightly more
  dissipative than a straight one.

Measured with `analysis/halfface_audit.py` (output `analysis/halfface_audit.txt`)
on the actual glass (the IC) and on the final moving HLLC mesh at t=.05.
The mesh has 49152 edges (3 per node).

| Mesh | Σ\|ν^T\|/\|Σν^T\| median / 90% / 99% | bend angle median / 90% / 99% | half-face length / Voronoi face median / 90% / 99% |
|---|---|---|---|
| Glass, t=0 | 1.000 / 1.0014 / 1.027 | 0.4° / 6.0° / 26° | 0.999 / 1.06 / 1.51 |
| Moving HLLC, t=.05 | 1.000 / 1.0074 / 1.138 | 0.8° / 14° / 57° | 0.998 / 1.17 / 5.7 |

The largest ratios to the Voronoi face (up to about 10³) belong to nearly
cocircular pairs. There the Voronoi face shrinks towards zero before a flip,
while the median-dual face stays finite: the §4.3.3 contrast between
continuous Voronoi faces and jumping median duals.

Cost: 98304 HLLC solves per residual sweep, and two sweeps per RK2 step.
That is four solves per edge per step, against MMFV's one Riemann solve per
face per step.

Why the solves are not merged per edge:

* Element-local Σ_i φ_i^T=Φ_T is what the step-2 LDA limiter acts on.
* The same element-local structure underlies triangle scheduling
  (Figure 4.2) and triangle-owned MPI (Figures 4.4–4.5).
* The Arpaia frame w_T=σ̄_T is per element.

A possible later optimization is to compute one edge dissipation and share
it between the two triangles in proportion to |ν^T|. This would keep each
central part element-local. It has not been derived for the ALE frames or
tested.

## 5.6 Step-2 design: limited LDA/HLLC combination (proposal, not implemented)

**User decision (2026-09-30):** LDA keeps its Gauss3 contour unchanged.

The approach is not MUSCL-type face extrapolation. That would make HLLC
itself a second-order vertex-centred FV and replace LDA, the scheme's RD
character. The plan instead combines LDA and HLLC element by element in
each RK2 stage, like a blended scheme. The weight comes from admissibility
and local bounds, not from a residual-ratio sensor:

    phi_i^T = phi_i^{L,T} + ell_T (phi_i^{LDA,T} - phi_i^{L,T}),   0 <= ell_T <= 1,

The limiter acts on complete stage contributions, including the corrector's
F1-minus-lumped temporal difference. Where ell_T=1 the scheme is the existing
moving LDA/F1 RK2. Near shocks ell_T tends to 0 and the scheme reverts to the
HLLC low order. B/Bmax/Bx differ in how ell is chosen (a sensor instead of
bounds).

**Matching the Gauss3 total without touching LDA.**

* Φ_G^T = Φ_trap^T + Σ_e ΔΦ_e, where ΔΦ_e is the per-edge Gauss3−trapezoid
  physical-flux term of `rd_contour_gauss_correction`. The ALE mesh term is
  integrated exactly by both rules, so it does not enter ΔΦ_e.
* ΔΦ_e depends only on that edge's two nodal states and its midpoint normal.
  The adjacent triangle carries the opposite normal, so ΔΦ_e^T = −ΔΦ_e^{T'}.
* Add ½ΔΦ_e to each endpoint of each edge in the low-order distribution.
  Then:
  * every element low-order total equals Φ_G^T, so each correction sums to
    zero per element and a common ell_T conserves;
  * each node receives +½ΔΦ_e and −½ΔΦ_e from the two triangles, so the
    nodal low-order update is unchanged up to roundoff and its positivity
    argument still holds.
* The temporal parts already agree: F1 and lumped mass have the same element
  total, (|T|/3)Σ_j ΔU_j/Δt.

**Remaining implementation points.**

* Extend the static convex limiter in `rd_lda_rusanov.h` to ALE, with
  weights from the Arpaia divisor D_i and b_i.
* Blend complete old and new RK residuals (the B-sensor v1 lesson, §170).
* Add local ρ and specific-entropy bounds relaxed in smooth flow.
* Validate in order: moving Yee boost (limiter nearly inactive, LDA order
  recovered), Sod, then Sedov with 21 and 1 hot nodes.

**Alternative recorded for later, not selected:** give LDA the trapezoidal
nodal-flux contour (the red-text comparison in e4fcd84) so the two totals
coincide trivially.

## 6. Next steps (not started)

1. Step 2: port the convex-limited LDA/F1 correction to ALE with this HLLC
   low order.
   * Represent the Gauss3−trapezoid total difference by shared-edge
     antisymmetric corrections.
   * Use the ALE stage weights (D_i, b_i).
   * Add local ρ and specific-entropy bounds (Guermond–Popov–Saavedra;
     `RD_LDA_RUSANOV_CONSTRAINT_DESIGN_20260929.md`).
2. Step 3: a positive conservative remap of connectivity changes
   (patch-local low/high blend), needed before claiming Sedov conservation.
3. Optional checks for the thesis: moving 2D Sod contact with HLLC versus N,
   and a resolution pair (64²/256²) for the Sedov figure.


## 7. Matched 130-node comparison with the N scheme, and the core plateau (same day)

Requested by the user after previewing the results.

**Why 130 nodes.** With the 21-node injection N fails on both meshes (log3
§156). The only completed N Sedov is static N/RK2 with the 130-node (r=.05)
injection. For a matched comparison, the frozen HLLC_static and HLLC_moving
binaries were rerun on that byte-identical IC, without a rebuild
(`examples/Sedov_2d/run_hllc_disk005.py`). Archive
`../local_runs/sedov_hllc_disk005_20260930_v1/`; binary hashes are verified
against `sedov_hllc_20260930_v1`. Both runs returned 0 (272 s static, 614 s
moving).

**Results.** The static N run used an output list (7 snapshots); it is
verified separately (provenance, completion, positive and finite states).

| t=.05, 130 nodes | raw ρ max | binned peak | core ρ (r<.05) | core p | v_r / v_t RMS .05–.22 | ΔM / ΔE |
|---|---:|---:|---:|---:|---:|---:|
| N (RK2), static | 2.422 | 2.300 | .0851 | 1.559 | .191 / .088 | roundoff |
| HLLC-RD, static | 2.462 | 2.324 | .0857 | 1.552 | .024 / .006 | roundoff |
| HLLC-RD, moving | 3.390 | 2.943 | .0897 | 1.722 | .025 / .026 | −.27% / +2.10% |

* On the static mesh, N and HLLC-RD have almost identical mean profiles.
* N is far noisier: v_r RMS 8×, v_t 15×, interior ρ up to .65.
* Moving N fails with this injection (§156); moving HLLC-RD completes.
* Preview figure:
  `analysis/thesis_preview/hllc_n_sedov_disk005_preview.png`.

**Core plateau is the injected gas.** Estimate: ρ_c ≈ (p_c/K_inj)^{1/γ}, with
K_inj = p_hot/ρ0^γ from the IC.

| Injection | Run | measured ρ_c | adiabatic estimate |
|---|---|---:|---:|
| 21 nodes (p_hot 520.9) | MMFV2 | .0300 | .0310 |
| | MMFV1 | .0276 | .0319 |
| | HLLC moving | .0276 | .0324 |
| 130 nodes (p_hot 84.0) | HLLC moving | .0897 | .0970 |
| 1 node (p_hot 1.09e4) | HLLC moving | .0033 | .0051 |

* The central plateau is therefore the adiabatically expanded injected gas,
  retained by MMFV and moving HLLC.
* It is not numerical diffusion. Rusanov's ~.2 is numerical mixing.
* Measured values somewhat below the estimate imply some entropy increase of
  the injected gas.

**Thesis text.** Draft for review:
[RD_SEDOV_HLLC_THESIS_TEXT_DRAFT_20260930.md](RD_SEDOV_HLLC_THESIS_TEXT_DRAFT_20260930.md).
The thesis is not edited.

## 8. Injection-size effect, Morton-style maps and single-node feasibility (same day)

**Why the two preview figures differ in r<.15.**

* The 21-node and 130-node injections deposit masses .00128 and .00793.
* On the moving mesh the generators act as tracers. At t=.05 the heated
  vertices occupy r≤.106 (ρ≈.030) and r≤.160 (ρ≈.098), respectively.
* The point-source solution encloses those masses within r=.103 and .148,
  where its density has already risen to .096 and .296.
* The heated gas stays a uniform-entropy bubble, whose extent and density
  follow the injection (§7 adiabatic estimate). The point-source analytic
  profile does not apply inside it.
* The larger 130-node bubble therefore lies much further below the analytic
  curve. This is an IC effect, not a change in HLLC-RD. Static meshes mix the
  bubble into its surroundings.

**Morton et al. (2023, Fig. 13)-style maps.**

* Script `examples/Sedov_2d/plot_sedov_maps.py`: plasma colormap, linear
  0–4, full box, shared colour bar. RD is drawn as the P1 interpolant of the
  nodal values; MMFV as Voronoi (nearest-generator) cells.
* Output `analysis/maps_preview_v1/`: `sedov_maps_21.png` (HLLC static,
  HLLC moving, MMFV) and `sedov_maps_1node.png` (HLLC moving).
* Static HLLC gives a round but thick shell. MMFV gives a round, thin shell
  with fine radial striations from the glass.
* **Moving HLLC gives a thin but visibly faceted shell.**
  * Fourier modes of the density-peak radius (72 sectors) are dominated by
    m=5–6, with amplitude ≈.0018 (≈.7% of R). MMFV's largest mode is ≤.0008
    and static HLLC's ≤.0007.
  * The single-node moving shell is faceted similarly.
  * Plausible origin: the imprint of the discrete injection (a few, roughly
    hexagonally connected hot vertices). The low-dissipation moving mesh
    preserves it, while static first-order diffusion isotropizes it. Morton
    et al. give the same reason for spreading the injection. The cause is not
    isolated here.

**Single-node injection.**

* Moving HLLC-RD completes t=.05 without repair or floors: binned peak 3.00,
  raw 3.40, core ρ .0033 (adiabatic estimate .0051), ΔM −.34%, ΔE −1.61%.
* A static single-node HLLC-RD run (frozen binary, `run_hllc_reuse.py`,
  archive `sedov_hllc_nearest1_static_20260930_v1/`) was started. Its step
  size is about 3e−6 because the isolated hot node stays hot on the fixed
  mesh, so it will take long.

## 9. Single-point static HLLC-RD and the roundness question (2026-10-01)

**Static single-node HLLC-RD works.**

* Archive `sedov_hllc_nearest1_static_20260930_v1`; frozen binary,
  `run_hllc_reuse.py`.
* Reaches t=.05 in 11120 steps (764 s).
* All 22240 stages admissible (CFL ≤.1, b=.5); mass and energy conserved to
  roundoff.
* Binned peak 2.33, core ρ .024, core p 1.53.
* It is slow because the isolated hot node keeps the step near 3–6e−6.

**Single-cell AREPO MMFV** (`run_mmfv_single.py`, archive
`sedov_mmfv_single_20261001_v1`): frozen second-order MMFV binary, the same
hot ID 8256, energy normalized by that cell's Voronoi area. It completes in
1204 steps (145 s): peak 3.31, ρmax 3.98, core p 1.59, roundoff budgets,
positive states.

**Front asymmetry.** Largest Fourier amplitude of the density-peak radius in
72 sectors, divided by R:

| Run | t=.0125 | t=.025 | t=.0375 | t=.05 |
|---|---:|---:|---:|---:|
| HLLC-RD moving, 1 node | 1.63% | 1.29% | .97% | .71% |
| HLLC-RD moving, 21 nodes | 2.03% | 1.36% | .82% | .77% |
| HLLC-RD moving, 130 nodes | 1.10% | 1.18% | 1.04% | .79% |
| HLLC-RD static, 21 nodes | .80% | .48% | .25% | .29% |
| MMFV 2nd order, 21 cells | .94% | .71% | .41% | .32% |
| MMFV 1st order, 21 cells | 1.14% | .74% | .61% | .35% |
| MMFV 2nd order, 1 cell | .38% | .28% | .13% | .17% |

The dominant mode is mostly m=6, later m=5. Maps:
`sedov_hllc_20260930_v1/analysis/maps_preview_v2/` (21-node and 1-node rows,
with the static, moving and MMFV panels).

**What this establishes.**

* The faceting is specific to moving RD. It is absent in first- and
  second-order moving MMFV and in static RD.
* It is not set by injection size: final ≈.7–.8% of R for 1, 21 and 130
  nodes. With 130 nodes it does not decay.
* It is not caused by low spatial order, since first-order MMFV is round.
* Face-normal geometry differs little on the glass. The combined median-dual
  normal deviates from the generator direction (the Voronoi face normal) by a
  median 1.25° (99%: 12.8°; ≤2.8° on the 21-node injection boundary).
  That is unlikely to be the main cause alone.

**Leading hypothesis (not isolated).** The remaining structural difference is
the connectivity change.

* In MMFV the Voronoi faces vary continuously (a face shrinks to zero before
  a flip) and the flux exchange is exactly conservative.
* In moving RD the median-dual areas and P1 basis jump at a flip, and the
  nodal state is rebased non-conservatively (the logged step-opening term).
  This happens repeatedly in the compressed, sheared shell, where the flip
  pattern follows the local mesh orientation.
* Decisive test: a conservative positive flip remap (step 3). If the
  faceting drops toward the static/MMFV level, the hypothesis is confirmed.
  The existing unlimited repair is not positive (§159), so it cannot be used
  directly.

**Kernel-test geometry correction (no solver change).** The two kernel tests
had built normals with the opposite sign: outward for counter-clockwise
vertices, i.e. inward normals of the point-reflected triangle. That is
algebraically equivalent, and every reference used the same normals. They
now use the solver's exact formula n_0=(y1−y2, x2−x1). Both pass:

* HLLC: conservation 3.8e−16, independent HLLC 3.2e−13, Galilean 9.0e−12;
* blend helpers: Gauss3 total 3.3e−16, nodal cancellation 9.6e−17.

The earlier §4 statement "inward for CCW" applied to these corrected tests,
not the original construction.

## 10. SWIFT default (21) and single-particle injection; four-method map grid (2026-10-01)

**SWIFT runs.**

* The SWIFT default is the 21-particle injection: the stock
  `SedovBlast_2D/makeIC.py` sets `N_inject = 21` (archive
  `swift_sedov_default_20260929_v1`).
* Single-particle run (`examples/Sedov_2d/run_swift_single.py`, archive
  `swift_sedov_single_20261001_v1`):
  * reuses the frozen default binary, stock sedov.yml and glass (all
    hash-checked) and the same command line (`--hydro --limiter --threads=1`);
  * the only change is `N_inject = 21 → 1` in a copied makeIC script, with
    its diff saved;
  * the heated particle is ID 8256, the same as in the RD and MMFV
    single-point runs;
  * completed in 2.4 s.

**Single-particle SWIFT result at t=.05.**

* ρmax 4.27, above the analytic jump 4; binned peak 2.84.
* The single core particle keeps p≈11.8, against the analytic 1.6.
* v_t RMS (.05≤r<.22) .241; SWIFT default .176.

**Front asymmetry: largest Fourier mode of the density-peak radius divided by R.**
SWIFT outputs are at t=.01 intervals, the others at .0125.

| Run | early | t=.05 |
|---|---:|---:|
| HLLC-RD static, 21 / 1 | .80% / .64% (t=.0125) | .29% / .29% |
| HLLC-RD moving, 21 / 1 | 2.03% / 1.63% (t=.0125) | .77% / .71% |
| AREPO MMFV, 21 / 1 | .94% / .38% (t=.0125) | .32% / .17% |
| SWIFT SPHENIX, 21 / 1 | 3.73% / 5.61% (t=.01) | .58% / 1.87% |

SWIFT's density-peak radius includes particle noise, so its amplitude
includes a noise floor.

**Maps.** `analysis/maps_preview_v3/sedov_maps_grid.png` (2×4, Morton style):
rows are 21 and 1 hot points; columns are HLLC-RD static, HLLC-RD moving,
AREPO MMFV and SWIFT. RD and SWIFT are drawn by linear interpolation of
node/particle densities; MMFV as Voronoi cells.

**Revised interpretation.**

* SWIFT, which has no mesh or edge flips, is also faceted, and most strongly
  with a single particle. Faceting is therefore not unique to RD, and an
  edge-flip-only explanation is incomplete.
* MMFV is the roundest in both rows. Static HLLC-RD is round but thick.
* Moving HLLC-RD lies between MMFV and SWIFT at t=.05.
* The non-conservative flip rebase remains a plausible RD-specific
  contributor. The discrete Lagrangian imprint of the injection on a glass,
  which SPH shows too, may be another.
* The cause remains unisolated. The flip-remap test (step 3) is still the
  decisive RD-specific experiment.

## 11. Mass-weighted radial profiles of the 8 runs (2026-10-01)

**Method.** `examples/Sedov_2d/plot_sedov_profiles_mw.py` writes
`analysis/profiles_mass_weighted_v1/`.

* Rows: 21 and 1 hot points. Columns: ρ, v_r, p. All at t=.05.
* Each curve is Σ m q / Σ m in radial bins of .005, with radius measured from
  each run's initial injected-energy centroid.
* Masses: dual-cell mass for RD nodes, cell mass for MMFV (at centroids),
  particle mass for SWIFT.
* Empty bins are left blank. Isolated non-empty bins are drawn as dots, so
  sparse core samples (for example the single SWIFT core particle) stay
  visible.

**Mass-weighted density peak, peak radius and core (r<.05) mass-weighted
pressure (analytic 1.605):**

| Run | 21 hot points | 1 hot point |
|---|---|---|
| HLLC-RD static | 2.328 at .2525; p 1.53 (130 samples) | 2.329 at .2525; p 1.53 (129) |
| HLLC-RD moving | 2.982 at .2475; p 1.71 (4) | 3.000 at .2475; p 1.65 (1) |
| AREPO MMFV | 3.289 at .2575; p 1.60 (4) | 3.296 at .2575; p 1.59 (5) |
| SWIFT SPHENIX | 2.995 at .2525; p 2.38 (7) | 2.840 at .2575; p 11.8 (1) |

**Reading.**

* The profiles are nearly independent of injection for HLLC-RD and MMFV.
* For SWIFT the single-particle case degrades: the hot particle keeps p≈12
  and the peak drops.
* Moving HLLC-RD's peak sits slightly inside the shock (.2475 versus
  analytic .258), consistent with first-order smearing.
