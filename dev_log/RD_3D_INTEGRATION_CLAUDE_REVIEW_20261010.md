# Review of Codex's 3D RD integration (static N) and the related 2D refactor

- **Author:** Claude Code (Opus 5.5), for Zhenyu Wu. Written 2026-10-10.
- **Reviewed:** `feature/ale-flip-conservation-hierarchy`, the commits since `7c2d949`:
  - `69eb3aa`: Codex's review of my test plan;
  - `4b40f75`: no-lazy baseline Configs and the 3D feasibility report;
  - `dd7a31b`: shared Euler K / LU-SVD kernels;
  - `632a401`: guarded native 3D static N.
- **Codex documents:** [3D kernel mathematics](RD_3D_KERNEL_MATHEMATICS_20261010.md), [3D feasibility](RD_3D_FEASIBILITY_20261010.md), log3 §§226–231.
- **My evidence:** `../local_runs/claude_3d_review_20261010_v1/`, with scripts, Configs, logs, outputs and binary hashes.
- No solver, thesis or Codex file was changed by this review.

## 1. Verdict

This is a sound, conservative first step into 3D:
- The conventions are right, and the implementation matches them.
- The new path is fenced off by compile-time guards. It is periodic, static, equal-step N with lumped RK2, and one rank only.
- The evidence is reproducible.

I found no correctness error in the 3D path.

One finding concerns the shared 2D refactor (§4). It is not bitwise-equivalent for 2D LDA/B moving runs. Round-off differences grow to 1e-6 (LDA) and 6.5e-5 (B) in ρ over a Yee48 run to t = 1. Accuracy is unchanged to 5–6 significant digits, and conservation and flip events are identical. This is a reproducibility caveat, not a numerical defect. It should be recorded, because Codex's 4-step regression could not detect it.

## 2. Mathematics and code

I checked the following against the code and agree with them:
- **K matrix.** K_i = (a_i/d) A(n̂_i), with n̂_i the inward unit normal of the face opposite i and a_i the face measure. Lumped mass |T|/(d+1); ∇ψ_i = n_i/(d|T|).
- **Spectral matrix.** `rd_euler_spectral_matrix` is f(A) = λ₂I + ½(λ₀−λ₁)B + ½(λ₀+λ₁−2λ₂)B², with B = (A − wI)/c, times a/d.
  - This needs no tangent basis, so all d − 1 shear modes are kept in 3D.
  - Mesh-velocity shifts enter only through λ, which is correct, since the projectors do not change.
- **Roe linearisation** with d+1 vertex means. Û = 2U for a uniform state. The common reference shift Û_i − Û_0 leaves Φ, the solve and the N distribution invariant; it is applied in descending vertex order, so it is correct.
- **N distribution and checks.** φ_i = K_i⁺(Û_i − y), S⁻y = ΣK⁻Û. Both the solve residual and element conservation are checked against a round-off scale. There is no repair, floor or clipping.
- **Geometry** (`rd_simplex_geometry`):
  - 2D normal: the rotated edge, magnitude the edge length.
  - 3D normal: half the cross product, magnitude the triangle area.
  - Both oriented toward the opposite vertex; signed volume det/6.
- **Native adapter.**
  - It uses AREPO's unfolded periodic DP coordinates and requires positive volume.
  - It skips deleted tetrahedra (`t[0] < 0`). This is correct, and needed only in 3D: AREPO's 2D Delaunay code never marks deletions; `voronoi_3d.c:1797` does.
  - The dual mass uses volume/(DIMS+1), and the coverage check uses the box volume.
- **Corrector.** Flux_RD = (|T|/4) dU/Δt + ½φ(U*), with the local +½(Q* − Qⁿ). Together these give Qⁿ⁺¹ = Qⁿ + ½ΔQ* − (Δt/2)Σφ(U*), the lumped Heun update. z-momentum is carried in storage, export lists, stage recovery and the stage validation.
- **Shared structures.** `RD_Ustage0`/`RD_dU` are sized `RD_NVAR`, and the PrimExch mirror and the exchange loops match. `triangle_normals` still holds unit normals plus measures in 2D.
- **Guards.** Unsupported combinations fail at compile time. One rank, gas only and non-comoving are checked at run time.

## 3. Independent checks (my own, not Codex's tests)

| Check | Method | Result |
|---|---|---|
| `make check_rd` | unchanged target, conda Python | all PASS, including the new `test_euler_dimensions.py` (1.903e-15) and `test_simplex_kernels.py` |
| 3D spectral matrix | compiled C kernel vs an **eigenvector-free** reference: f(A) as a polynomial in B, with A from a central-difference flux Jacobian; 300 random 3D states (γ = 1.4, 5/3), full/positive/negative splits, random ALE shifts | max relative defect 2.1e-8 (finite-difference limited) |
| — | numerical eigendecomposition reference | **unusable**: the advective eigenvalue is triple, so `numpy.linalg.eig` returns nearly defective bases (cond(R) up to 3.9e19) and a spurious defect of 2.0. Testers should not use eigendecomposition here; Codex's projector oracle and my polynomial reference are the right tools |
| 3D N residual | 300 random tetrahedra and states; independent P1-Z residual via a degree-2 four-point volume quadrature of div F(Z) | Σφ_i = Φ to 5.8e-15; residual vs quadrature 1.5e-9 (FD-limited); uniform state gives exactly 0 |
| Native reproduction | fresh build of `632a401` with Codex's `Config_N_static`; 8³ advection, t = 1/32 | **bitwise identical** to Codex's archived snapshots (every field difference 0.0) |
| Native, longer runs | 8³ (512 nodes, 3552 tetrahedra), dt = 1/512, **t = 0.5 (256 steps, 16× Codex's gates)** | see below |

Longer 3D runs (all to t = 0.5, no termination; conservation is relative to the initial sum of absolute amounts):

| Case | Conservation | Other |
|---|---|---|
| Uniform flow | exact (0) | state defect 5.6e-16 |
| Pressure perturbation, v = 0 | 2.2e-16 | p_min 0.9916 (initial minimum 0.99); kinetic energy 5.3e-7 → 1.5e-9 (acoustic waves damped) |
| Density advection | 3.4e-16 | L1(ρ) against the exact translated profile: 7.1e-3 (t = 0.125), 1.2e-2, 1.6e-2, 1.8e-2 (t = 0.5) |

- The advection error grows smoothly. That is first-order N diffusion at 8 points per wavelength; by t = 0.5 most of the wave amplitude has been lost.
- The contact develops spurious |Δv| ≤ 3e-5 and |Δp| ≤ 6e-5 for a density amplitude of 0.1. System N does not preserve contacts exactly.
- These are characteristics of the scheme, not defects.

## 4. Finding: the 2D refactor is not bitwise-equivalent for LDA/B (P2, reproducibility)

`dd7a31b` routes the 2D Roe-matrix paths through `rd_euler_spectral_matrix`. Off-diagonal entries are assembled in a different floating-point order, as the code comment acknowledges.

Codex's regression covered static N/LDA and moving N on Yee48 and uniform states for **4–8 steps** (t = 0.015625) and found ≤2.4e-15. I extended it:
- old source `e1b1aa9` (before Codex's changes) vs new `632a401`;
- Codex's explicit no-lazy mode-1 equal-step Configs (`examples/rd_moving_baseline/Config_{LDA,B,HLLC}_equal.sh`);
- Yee48 to **t = 1 (256 steps)** for LDA and B; Sedov21 to t = 0.005 (613 steps) for HLLC.

| Scheme | max \|ρ_old − ρ_new\| at t = 0.25 / 0.5 / 0.75 / 1 | Flip events | Totals | ρ / v / p L1 error vs analytic, old → new |
|---|---|---|---|---|
| LDA | 9.3e-15 / 9.8e-12 / 1.0e-6 / 1.3e-6 | identical (123) | both conserve; difference ≤1.4e-14 | 1.074417e-3 → 1.074417e-3; 1.467787e-3 → 1.467786e-3; 1.337014e-3 → 1.337015e-3 |
| B | 5.2e-15 / 4.6e-12 / 4.5e-7 / 6.5e-5 | identical (119) | same | 1.281194e-3 → 1.281194e-3; 2.398368e-3 → 2.398389e-3; 1.778974e-3 → 1.778977e-3 |
| HLLC | **bitwise identical** | identical | same | (does not use the refactored K) |

Interpretation:
- The refactor changes round-off at the 1e-15 level from the first steps.
- Over a few hundred steps these differences are amplified roughly exponentially, ~3 orders per 0.25 time units, to 1e-6 (LDA) and 1e-4 (B, whose scalar θ uses max/min).
- There are no discrete flip differences. Accuracy and conservation are unchanged.

Consequences and recommendations:
1. Record that archives made before `dd7a31b` (including every 2026-10-09 campaign) are **not bitwise reproducible** for LDA/B moving runs beyond short times with the current source. Reproduction holds only to ≈1e-6–1e-4 locally, with identical integral metrics.
2. If bitwise reproduction of the thesis/2D archives matters, keep the exact pre-refactor 2D arithmetic (e.g. a 2D-specific branch inside the shared kernel). Otherwise accept and document the change.
3. Regression gates for future refactors should run at least a few hundred steps, and should compare integral metrics as well as field differences.

## 5. Further comments and suggestions

1. **Gate length.** Codex's native gates end at t = 1/32 (16–128 steps). My t = 0.5 runs add stability evidence. Before any robustness claim, add longer runs and a 3D shock test; N in 3D has no positivity guarantee for systems.
2. **Convergence.** The two-grid advection ratio at t = 1/32 is correctly labelled as a trend, not an order. A useful next step: 8³/16³/32³ at a fixed, longer time (e.g. t = 0.25), with dt control. N should be first order, so this mainly confirms consistency.
3. **Cross-code validation.** Run the standalone `rdsolver` (Morton et al.) and AREPO on the same point set and initial condition, with N and lumped RK2 in both. Agreement to round-off, or an explained difference, would be strong evidence that the port is faithful. The feasibility report found the standalone tetra kernel hits singular inverses at zero velocity, so compare only where it is well posed.
4. **Naming.** `triangle_normals.area` now stores tetra volume, and `rd_triangle_is_physical` handles tetrahedra. Renaming later (`simplex_geometry.measure`, `rd_simplex_is_physical`) would prevent misuse. Not urgent.
5. **Next 3D steps**, which Codex already plans:
   - moving tetrahedra need exactly time-integrated face normals (quadratic in time; two-point Gauss) for the GCL and for shared-face cancellation in any hierarchy;
   - 3D flip cavities (2-3/3-2/4-4) can reuse the dimension-independent transfer kernel, after extending it from 4 to 5 components;
   - realistic 3D work needs MPI. All current RD paths are single-rank.
6. **Provenance and process.** Codex's archives record source, binaries, Configs, inputs and parameters with hashes, and keep failed attempts (`native_static_v1/v2`). It also verified preprocessed-code equivalence after cleanup. This follows `AGENTS.md` well.

## 6. Codex's review of my test plan (log3 §226)

I accept its three P2 findings and its minor items:
- **B2.2 error-field difference.** My claim "ρ_A − ρ_B = e_A − e_B pointwise" was wrong away from the nodes. I_X e_X = ρ_h^X − I_X ρ_exact, so I_A e_A − I_B e_B = (ρ_h^A − ρ_h^B) − (I_A − I_B)ρ_exact. The last term is O(h²ρ″), exactly the size I wanted to remove. The metric is usable only as an "analytic-baseline-corrected" difference, named as such.
- **Lazy runs.** Lazy runs use registry connectivity. Re-triangulating final coordinates does not reproduce their P1 basis.
- **B1.8 cannot force a failure.** The 0.5°/179° lazy thresholds do not guarantee an inversion. A deterministic manufactured trajectory, with a matching valid-trajectory control, is needed for that gate.
- **CFL ledger maximum.** I quoted 0.103 for the CFL gate. That was the last event's value; the maximum over the run is 0.116.
- **Minor items.**
  - `flip_campaign_checks` accepts `RD_FLIP_HIGH_MODE=2`.
  - The new mean-displacement diagnostic does not use the periodic minimal image.
  - A live vertex's ledger ratio must not be gated at ≤1.
  - An error-norm increase is not a distance between solutions.
  - A single dt halving is a sensitivity check, not a time-convergence test.

All are correct. The two code items are small fixes in my scripts, which I can make whenever convenient (not done in this review, to avoid touching files Codex may be editing).
