# Review of Codex's 3D extension (LDA/F1, MPI, static hierarchy, SWIFT-family tests) and 2D audit

- **Author:** Claude Code (Opus 5.5), for Zhenyu Wu. Written 2026-10-10.
- **Reviewed:** commits `5ec257b`, `512abb9`, `ce0433d`, `6762f4b` and `9ae1043` (log3 §§233–237).
- **Codex documents:**
  - [2D reproducibility audit](RD_2D_REFACTOR_REPRODUCIBILITY_AUDIT_20261010.md);
  - [3D features and benchmarks](RD_3D_FEATURES_AND_BENCHMARKS_20261010.md).
- **My evidence:** `../local_runs/claude_3d_review2_20261010_v1/` (see its `README.txt`).
- No repository solver, test, thesis or Codex file was changed. The scaled solve in §4 is a prototype in a separate source copy.

## 1. Verdict

These four milestones are correct as far as I can check:
- the static 3D LDA/F1 scheme;
- distributed CFL with MPI for N and LDA;
- the five-component static hierarchy;
- the reduced SWIFT-family benchmarks.

Their scope is stated honestly, and the results are reproducible:
- **Hierarchy runs.** A fresh build of `9ae1043` reproduces Codex's mixed-bin LDA runs (`pressure_patch_8_LDA_hier_natural`) on 1 and 2 ranks. Every particle dataset in every snapshot is byte-identical after sorting by ID.
- **Cold Sedov.** The same build reproduces Codex's stop exactly: same tetrahedron, same defects.

The main new result of this review is the **root cause of that cold Sedov stop** (§4):
- It is not a K error, and not a genuine incompatibility of the system.
- The cold gas makes the upwind matrix badly scaled. An unscaled solve then leaves a residual at the solver's normwise backward-error level, which the componentwise audit rejects.
- A diagonal similarity scaling by the natural units removes it.
- Once the false abort is gone, N and LDA fail by **negative pressure**, as they did in 2D (log3 §156). So 3D Sedov needs a positivity-preserving scheme, i.e. a 3D port of HLLC-RD.

## 2. 2D reproducibility audit (`5ec257b`)

I accept Codex's audit and its corrections to my previous review (§232):
- **Localisation.** Restoring only the two original 2D K construction blocks reproduces my old-source LDA/B runs byte for byte. Replaying the new binary reproduces my new-source runs byte for byte. This localises the trajectory change to the K extraction, which is stronger than my evidence.
- **My count.** "123/119" counts steps that contain flips, not cavities. The cavity totals are 249 and 244.
- **My explanations.** The exponential growth law and the off-diagonal attribution are hypotheses, not established results.
- **Scope.** 1e-6 to 1e-4 is the range observed in two cases, not a bound for all pre-`dd7a31b` archives. The HLLC Sedov21 control covers only that control.

The user has deferred the 2D compatibility fix. Note that the scaling recommended in §4 would change 2D trajectories again if it were applied there. Either keep it 3D-only, or make one 2D arithmetic decision that covers both changes.

## 3. LDA/F1, MPI and hierarchy (`512abb9`, `ce0433d`, `6762f4b`)

**LDA/F1 algebra.**
- **Spatial LDA:**
  - S⁻x = Φ and φ_i = −K_i⁺x.
  - Since ΣK_i = 0 (Σ a_i n_i = 0), ΣK⁺ = −S⁻ and Σφ_i = Φ.
  - At rest, Φ lies in range(S⁻), so the rank-4 SVD case is compatible. The test suite covers this case.
- **F1:**
  - the same β operator acts on t = (V/4)ΣdU/h, so ΣT_i = t;
  - if the rank is deficient, the code uses a lumped fallback, which is conservative;
  - the code checks `RD_NVAR` against the rank of the *spatial* solve, and the F1 solve itself must also be full rank.
- **Equal-step update:**
  - the corrector deposit is −h[T_i + ½φ_i(W*)], plus the local +½(Q* − Qⁿ);
  - this gives Qⁿ⁺¹ = Qⁿ − (h/2)(φⁿ + φ*) − hΣ_T(T − lumped);
  - with lumping this is Heun, and it matches the 2D adapter's "mixed-β" structure.
- **Hierarchy update:**
  - both calls use h_T/2;
  - the closing flux φ* + 2(T − lumped) gives (h/2)(φⁿ + φ*) + h(T − lumped);
  - with equal bins this is the same identity as the equal-step update, consistent with the 8.9e-15 degeneration difference.
- **New stage-sum assertion.** It checks Σ_j Flux_RD[k][j] against Φ (hierarchy) or Φ/2 + t (equal step), with a scale that includes the temporal terms. This is a useful guard.

**MPI CFL** (`rd_timestep.c`):
- Remote vertices are read through `PrimExch[dp->index]`, after `exchange_primitive_variables()`.
- Deposits go to `originalindex` on the owner, via the standard hypercube `MPI_Sendrecv` pattern.
- The minimum-ID element ownership counts each tetra once globally.
- MINLOC and the global stage reductions are correct.
- Field differences across rank counts of ≤1.2e-14 are expected from summation order; equal step sequences are the right acceptance test.

**Hierarchy port.**
- The changes I read are the `RD_NVAR` loops, the z-momentum in W* and in the predictor pressure, `dPredictor[RD_NVAR]`, and box-volume coverage.
- I checked for leftover hard-coded 4-component loops by preprocessing the solver with the 3D LDA hierarchy configuration.
  - The only `< 4` loops left are the tetra-vertex loop and three static 2D helpers: `rd_build_characteristic_matrices`, `rd_check_conservation` and `rd_assert_K_sum_vanishes`.
  - The 3D build never calls these helpers, and they are absent from the object file.
- The method remains the experimental frozen-dU hierarchy, as Codex says. Mixed bins are tested at a maximum ratio of 2 on 8³ only.

**Benchmark caveats** (agreed with Codex's report):
- **Sod (LDA):** density undershoots to 0.062 (right state 0.125) and pressure falls to 0.019 (right state 0.1). Shocks in 3D need B, a blend, or HLLC-RD.
- **Gresho:** a z-independent cylinder, so it exercises tetra assembly but not fully 3D dynamics.
- **Resolution:** 16³ results are functional checks, not convergence evidence.

## 4. Cold Sedov: root cause and a tested remedy

### 4.1 The failing element

The run stops at tetra 47980, stage 0, second step:
- **Shape:** a **sliver**. All four face normals lie within 1.1° of the y axis. V/(ΣA)^{3/2} = 7.9e-4, against 6.8e-3 for a regular tetrahedron.
- **State:** the gas is **at rest and uniform to round-off**:
  - velocity |v| ≈ 4e-26;
  - ρ = 1 ± 6e-16, p = 1e-6;
  - |Φ|/(ΣA c) ≈ 2e-20.

  The residual is noise.

### 4.2 Singular values (60 digits, `analyse_sedov_element.py`)

| | σ₁ | σ₂ | σ₃ | σ₄ | σ₅ |
|---|---|---|---|---|---|
| S⁻ as assembled | 5.7e-1 | 1.4e-6 | 7.5e-11 | 5.7e-11 | 1e-34 |
| D⁻¹S⁻D, D = diag(1, c, c, c, c²) | 1.7e-6 | 1.4e-6 | 7.5e-11 | 5.7e-11 | 3e-29 |

- **Why σ₁ is so large.** It is the (ρ, E) entry, ≈ (a/3)(γ−1)λ⁻/(2c²) ∝ 1/c. With c = 1.3e-3, it is ~10⁵ times larger than the physically comparable entries.
- **Range of entries.** The matrix spans 11 orders of magnitude only because of units: ρ ~ 1 but E ~ ρc² ~ 1e-6.

### 4.3 What the numbers show

- **The system is compatible.** The exact projection of the double-precision rhs onto the discarded left singular vector is **2e-44**.
- **Where the defect comes from.**
  - The production residual is 1.72e-33.
  - DGELSD's normwise backward error is ε σ₁ |y| = 1.44e-33.
  - The audit tolerance is 4096 ε × componentwise scale = 4096 ε × 1.8e-21 = 1.65e-33.
  - The defect is therefore the solver's normwise error, measured against a componentwise tolerance. The two disagree by a factor of ~3500 here.
- **Accuracy of y.** The production y has a relative error of 3e-11.
- **With scaling.** The scaled solve leaves a residual of 1.2e-38, five orders below the tolerance.

### 4.4 Frequency of the failure (`sweep_cold_states.py`)

Near-uniform states at rest, 400 random round-off perturbations per row, production kernel vs scaled prototype:

| Tetra | p | production failures | scaled failures |
|---|---|---|---|
| this sliver | 1, 1e-3 | 0 | 0 |
| this sliver | 1e-6 | 6–43 /400 | 0 |
| this sliver | 1e-9 | 321–341 /400 | 0 |
| regular | 1e-9 | 1–31 /400 | 0 |
| random | 1e-9 | 31–74 /400 | 0 |

- No case fails at velocity 1e-3 c.
- Where both kernels pass, their residuals agree to ≤3e-11 of the audit scale. The production solve is the less accurate of the two in this regime.

### 4.5 Native check with the scaled prototype

The prototype is `scaled_prototype.patch`. It scales both the spatial and the F1 solve, and every check still uses the unscaled S and rhs.

- **Sedov N:** the audit no longer stops it. It runs 51 steps, then stops at t = 0.00167 with **negative pressure** at the evacuated centre (ρ = 0.0048, p = −4.3).
- **Sedov LDA:** stops with negative pressure in the first corrector (ρ = 1.19, p = −0.12).
- **2D comparison (log3 §156):** the 21-point N and LDA runs failed by negative pressure or mass on both meshes. Only HLLC-RD completed Sedov.
- **Sod N and Gresho N** (16³): differences from Codex's production results are ≤1.7e-14 at every snapshot, and conservation is ≤4.3e-15.

### 4.6 Recommendations

1. **Scale the 3D upwind solves**, both the spatial and the F1 temporal solve:
   - use the natural units D = diag(1, c, …, c, c²) from the Roe sound speed;
   - keep the unscaled audits;
   - the scaling also makes the LU pivot-ratio and SVD rank decisions physically meaningful;
   - gate it with the existing 3D suites plus a cold-at-rest kernel test like `sweep_cold_states.py`.

   Widening the tolerance with a normwise term ε‖S‖‖y‖ is the weaker alternative: it accepts a y that is less accurate, rather than computing an accurate one.
2. **For 3D shock benchmarks, port HLLC-RD** (or the LDA/HLLC blend) **to tetrahedra** before treating cold Sedov as a target. N and LDA are not positive for this problem in 2D either.
3. **Keep the same tolerance policy in 2D for now.** Applying the scaling in 2D is part of the deferred 2D arithmetic decision (§2).

## 5. Smaller comments

- **README and context.** `examples/rd_3d/README.md` and `context.md` correctly limit the claims: static meshes, small gates, no moving 3D, no B, and no restart from an open stage.
- **Cluster use.** The Mac `otool` provenance helper must be adapted before the COSMA/Cuillin runs that the user directed there.
- **Coverage.** The equal-bin and mixed-bin hierarchy and MPI gates use 8³ for t ≤ 1/32. Longer runs, more than two bin levels, and convergence should run on the cluster with frozen provenance, as planned.
- **Process.** Failures (`lda_v1`, `mpi_v1`, `natural_v1`, `swift_v1`, cold Sedov) are kept and not relabelled, and the CLI exits 2 when a benchmark fails. This follows `AGENTS.md`.
