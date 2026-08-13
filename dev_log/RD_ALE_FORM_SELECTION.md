# Choosing the default ALE-RD form

- Opened 2026-08-13. Author of this document: `Claude Code Opus 5`.
- Companion to `RD_DEVELOPMENT_LOG_2.md`; section numbers below refer to that
  log unless stated otherwise.
- **Status: a recommendation, not a change.** `Template-Config.sh` and the
  production Configs are untouched. The decision is Zhenyu's.

---

## 1. Purpose and scope

The moving-mesh phase accumulated five compile-time switches, each introduced to
repair one specific defect and each validated only against that defect. None is
a default. The evidence they produced is contradictory: on Gresho the contour
residual is 21 per cent worse in `L1` (section 30.2), on the smooth Yee it is
6 to 18 per cent better but converges more slowly (section 31.2). Neither
problem contains a genuine discontinuity, which is where the two candidate
residuals differ most and which had never been run.

This campaign varies them against one another on one protocol and recommends a
default.

**In scope:** the spatial residual, the element frame, the mass/divisor pair,
the timestep criterion, for the equal-step, one-rank, periodic, two-dimensional
LDA and N prototype.

**Out of scope:** B and any nonlinear sensor (excluded from the whole ALE phase
by section 4), hierarchical timesteps, refinement, three dimensions, MPI rank
invariance (the prototype is guarded to one rank).

---

## 2. The switches

### 2.1 `RD_ALE_SPLIT_MESH_VELOCITY` — introduced in section 18

The endpoint median-dual ledger stores `Q_i = m_i U_i` and the geometric term of
the update is

```
sum_i (m_new - m_old)_i U_i^n = dt * integral U_h div sigma_h,
```

which must cancel against the mesh-velocity part of the flux,
`-dt * integral sigma_h . grad(.)`. The cancellation is the divergence theorem
and it closes **only if both use the same interpolant**. The Roe residual is
assembled as `sum_j K_j Uhat_j` where

```
Uhat_j = (dU/dZ)|_{Z_avg} Z_j
```

is the parameter-vector linearisation, not the conservative nodal state. The
switch adds

```
C_T = -1/2 sum_j |n_j| (sigma_bar . n_hat_j) (U_j - Uhat_j)
```

to the element total, distributed with the row sum of the mass matrix: `1/3`
for N's lumped mass, `beta_i` for LDA's F1, which LDA obtains automatically
because `rhs[k][0] = Phi[k]` is what its solve consumes.

### 2.2 `RD_LDA_COMOVING_FRAME` — introduced in section 27

With a quasi-Lagrangian mesh `sigma` is approximately `u`, the two advective
eigenvalues `u.n - sigma.n` vanish, and `S^-` is nearly rank deficient. The
switch applies the element-local Galilean transform

```
U' = G(b_T) U,     b_T = (1/3) sum_{j in T} sigma_j,

G = [[1,          0,    0,   0],
     [-b_x,       1,    0,   0],
     [-b_y,       0,    1,   0],
     [|b|^2 / 2, -b_x, -b_y, 1]]
```

and rebuilds `K_i^+`, `K_i^-` and `S^-` from `u' = u - b_T`, solving and
distributing there and mapping each completed nodal residual back by `G^{-1}`.
Section 27.2 measured `cond_2(S^-)` falling from `4.6e16` to `2.0e12`.

It is a **similarity transform**: in exact arithmetic it changes nothing.
Section 27.2 also found that forming `G S G^{-1}` from the already-assembled
laboratory matrix does *not* work — the matrices differ by `6e-14` relative,
enough to spoil a nearly singular identity — so the assembly itself must happen
in the primed variables.

### 2.3 `RD_ALE_CONTOUR_RESIDUAL` — introduced in section 28

The correction of 2.1 contains `sigma_bar` explicitly. Under an additional
uniform boost `B` the mesh velocity becomes `sigma_bar + B` and the correction
leaves

```
-1/2 sum_j |n_j| (B . n_hat_j) G(B) (U_j - Uhat_j),
```

which does not vanish, because `sum_j n_j = 0` removes only a term common to all
`j` and `U_j - Uhat_j` is not. The switch removes the mismatch at its root by
building the element total from nodal conservative states,

```
Phi'_T = 1/2 sum_j |n_j| [ F(U'_j) . n_hat_j - (b_T . n_hat_j) U'_j ],
```

the contour quadrature of the interpolated physical flux. The total and the
ledger then share one interpolant and no correction is needed. The Roe matrices
still define the multidimensional upwind distribution; they no longer define the
element total. This is a **different RD spatial residual**, not an algebraic
rewrite.

### 2.4 `RD_ALE_CAMPOLI_MASS` — section 24

The two published RK2 forms differ by

```
delta_T = (A_old + A_new)/2 - A_mid = (dt^2/8) (sigma_1 - sigma_0) x (sigma_2 - sigma_0)
```

added to **both** the element mass coefficient and the nodal divisor:

| | element mass | nodal divisor |
| --- | --- | --- |
| Arpaia et al. (2015) Prop. 4.1 | `A_mid` | `sum_T [A_mid + (A_new-A_old)/2]/3` |
| Campoli et al. (2017) sect. 2.2 | `(A_old+A_new)/2` | `sum_T A_new/3` |

### 2.5 `RD_ALE_CFL_TIMESTEP` — section 27.4

AREPO's criterion is `R/(c + |v - sigma|)` on the Voronoi cell radius; the RD
condition is `CFL min_i |S_i| / sum_K alpha^K` with `alpha^K = max_j |k_j|` on
the median-dual star. The switch takes the minimum of the two.

---

## 3. The mathematics the campaign tests

### 3.1 One defect, two currencies

The `U` against `Uhat` mismatch is a single defect that can be paid for in
either of two currencies, and the choice of switch decides which:

| | conservation | discrete covariance |
| --- | --- | --- |
| no split correction (section 17) | **broken**, `3.9e-8` in `px` over 16 flip-free steps | broken |
| split correction (sections 18-25) | **repaired** to `2.3e-13` | **broken**, linear in boost |
| contour residual (section 28) | repaired | **repaired** |

Adding the correction moves the defect from the ledger into the frame; removing
the mismatch itself pays neither.

### 3.2 Why the contour form is covariant and the Roe form is not

The contour residual is built from **pointwise nodal values of the ALE flux**.
Under a boost, `U_j -> G(B) U_j` exactly — the map is linear — and the
combination `F(U) - (b_T . n) U` transforms covariantly at each node. The whole
residual therefore transforms exactly.

The Roe residual linearises about the **element mean of the parameter vector**
`Z = sqrt(rho) (1, u, v, H)`, which is a nonlinear function of the state. A
boost changes `Z` nonlinearly, so the `P^1` interpolant of the boosted `Z` is
not the boost of the interpolant, and `U_h(Z'_h) != G(B) U_h(Z_h)`. The element
mean about which the linearisation is taken is itself frame dependent.

Both are consistent and converge to the same Galilean-invariant PDE, so the Roe
form's frame dependence vanishes with `h`. It is a discrete property, not a
modelling error — which is why sections 23 and 25 saw a flat `L1` under boost
while section 28.1 measured a defect. Those measure different things: the
discretisation error is `8e-3` and the frame dependence `1e-5`.

### 3.3 Why `G` cannot change the answer

`G(b_T)` is a similarity applied to the operator and the states of one element
and undone before the nodal residual enters the ledger. In exact arithmetic the
scheme is unchanged. Anything it does is conditioning. Section 4.2 below is the
measurement of that claim.

---

## 4. Results

Eight builds. Core two-by-two `{Roe+split, contour} x {laboratory, co-moving}`,
two single-axis confirmations, and laboratory-frame N duplicates of both
residuals for the discontinuous tier. All carry `RD_DEBUG_ASSERTS` and the
geometry diagnostic with the connectivity hash;
`RD_DIFFERENCE_RESIDUAL` is off throughout.

Extending the contour residual to N required a construction, not a guard
relaxation: N does not distribute `Phi`, its nodal flux is `K_i^+(U_i - U_in)`
and `sum_i phi_i^N = sum_j K_j Uhat_j` holds by construction of the inflow
state. The contour total is a different quantity, so the difference is
distributed with N's lumped row sum,

```
phi_i^N += (Phi_contour - sum_i phi_i^N) / 3.
```

This is conservative by construction and inert where the two totals agree, but
it is a scheme design choice and its properties are among what is measured here.

### 4.1 Tier A: algebraic and particle-level gates

**All eight builds pass** the `sigma = 0` bitwise-collapse assertion, the
uniform-state free-stream gate through 784 flips (`max|dv| <= 1.1e-14`,
conservation at round-off), and the flip-free endpoint conservation gate. The
new N-contour distribution passes each of them.

One unexpected detail. On the flip-free gate the Arpaia builds conserve to
`1.5e-12` and the Campoli build to `2.2e-16`, four orders better. The reason is
structural: **Campoli's divisor is the plain new median dual, which is also the
storage area**, so the final `Q_bar -> Q_new` rebase is the identity and costs
nothing. Arpaia divides by `m_bar` and multiplies by `m_new`, and `1.5e-12` over
five steps is exactly that accumulation.

### 4.2 Tier A: discrete Galilean covariance, at `t = 0.02`

The only metric that can see covariance; an integral metric is three orders too
coarse.

| build | boost | velocity `L1` | velocity `Linf` | connectivity |
| --- | ---: | ---: | ---: | --- |
| Roe, laboratory | 3 | 1.895e-5 | 2.204e-4 | identical |
| Roe, laboratory | 10 | **run fails** | | |
| Roe, co-moving | 3 | **1.895e-5** | **2.204e-4** | identical |
| Roe, co-moving | 10 | 6.345e-5 | 7.160e-4 | branches at record 62 |
| contour, laboratory | 3 | 2.373e-15 | 1.608e-14 | identical |
| contour, laboratory | 10 | 8.343e-13 | 3.240e-11 | identical |
| **contour, co-moving** | 3 | **2.363e-15** | 1.810e-14 | identical |
| **contour, co-moving** | 10 | **9.721e-15** | 5.285e-14 | identical |
| contour, co-moving, Campoli | 10 | 9.216e-15 | 5.490e-14 | identical |
| contour, co-moving, AREPO `dt` | 10 | 6.762e-15 | 4.086e-14 | identical |

Four readings.

**The Roe form is not discretely covariant, and the defect is linear in boost**:
`1.895e-5` at boost 3 against `6.345e-5` at boost 10, a ratio of 3.35 for a
boost ratio of 3.33. Section 3.2's argument is confirmed quantitatively.

**`G` is exactly a similarity.** Laboratory and co-moving agree **to every
printed digit** at boost 3, for the Roe form. It does not change the answer.

**`G` is only conditioning, and the conditioning is real.** At boost 10 the
laboratory Roe build fails outright while the co-moving one runs; and the
contour form, which is covariant in both frames, still loses two orders in the
laboratory frame — `8.3e-13` against `9.7e-15` — purely to conditioning.

**The contour form is covariant to round-off**, in both frames and at both
boosts, and neither the mass pair nor the timestep policy affects that.

### 4.3 Tier B: smooth accuracy, Yee vortex

Density `L1` against the analytic steady state, boost 0, `t = 1`:

| build | `n=32` | `n=64` | `n=128` | order 32-64 | order 64-128 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Roe, laboratory | 2.7731e-3 | 8.2376e-4 | 2.4023e-4 | 1.75 | 1.78 |
| Roe, co-moving | **2.7731e-3** | **8.2376e-4** | **2.4023e-4** | 1.75 | 1.78 |
| contour, laboratory | 2.2901e-3 | 7.3562e-4 | 2.2522e-4 | 1.64 | 1.71 |
| contour, co-moving | **2.2901e-3** | **7.3562e-4** | **2.2522e-4** | 1.64 | 1.71 |

The laboratory and co-moving rows are **bit-identical at every resolution**,
which is the strongest available confirmation of section 3.3. The Roe form is
closer to second order, the contour form is more accurate at every resolution
tested but converges more slowly, reproducing section 31.2 under a different
timestep policy.

### 4.4 Tier C: discontinuous, the discriminator

| build | Sod, `t = 0.2` | KH, `t = 2` |
| --- | --- | --- |
| Roe + LDA, laboratory | **completes** | fails at `t = 2.4e-4`, assertion A2 |
| Roe + LDA, co-moving | **completes** | reaches `t = 0.98`, then negative mass |
| contour + LDA, laboratory | **fails at `t = 0.139`**, non-physical predictor | fails at `t = 0.326`, timestep collapse |
| contour + LDA, co-moving | **fails at `t = 0.139`** | fails at `t = 0.326` |
| Roe + N | completes | **completes** |
| contour + N | completes | **completes** |

This is the decisive tier, and it separates the two failure mechanisms exactly
as tier A did.

**Roe's discontinuous failures are conditioning.** On KH the laboratory build
dies at the first step on the conservation identity; the co-moving build reaches
`t = 0.98`, four thousand times further, and then dies of negative mass, which
is LDA's non-monotonicity at the roll-up rather than a linear-algebra failure.
KH is a shear layer with a Lagrangian mesh, so `sigma` is approximately `u`
everywhere and `S^-` degenerates for the same reason as at boost 10. **The
degeneracy is not a high-boost curiosity; it is generic in shear.**

**The contour form's failures are not conditioning.** Laboratory and co-moving
fail at **identical times to six digits**, `t = 0.139453` and `t = 0.325768`.
`G` changes nothing, so this is a property of the residual.

Sod profile quality where a comparison exists, 200-bin density profile:

| build | total variation | max `rho` | min `rho` |
| --- | ---: | ---: | ---: |
| Roe + LDA (both frames, identical) | 1.9360 | 0.9069 | 0.2322 |
| Roe + N | 1.5413 | 0.8300 | 0.3208 |
| contour + N | **1.5222** | 0.8308 | 0.3233 |

Under N, where both residuals are robust, the contour form is marginally the
less oscillatory of the two.

---

## 5. Recommendation

### 5.1 Adopt `RD_LDA_COMOVING_FRAME` as the default

It is a similarity transform: sections 4.2 and 4.3 show it changes the answer in
no digit, on any test. It strictly improves conditioning, and that conditioning
decides whether real problems run — boost 10, and KH from `t = 2.4e-4` to
`t = 0.98`. There is no measured cost and no case where it hurts.

Two caveats. It is currently guarded to LDA; N would need its own derivation,
and the guard added in this campaign says so. And section 27.2's finding stands:
the transform must be applied at assembly, not as an after-the-fact similarity.

### 5.2 Keep the Roe residual as the default; do not adopt the contour form

The contour form buys exact discrete Galilean covariance, `2.4e-15` against
`1.9e-5`. What it costs is robustness at a discontinuity: it fails on Sod where
the Roe form completes, and `G` does not help, so the failure is intrinsic.

The trade is unfavourable for a production astrophysics code because **the
property it buys is invisible where it matters and the property it costs is
not**. Sections 23 and 25 already showed that the Roe form's `L1`, peak
amplitude, convergence order and timestep are all flat across boosts 0 to 3 —
the frame dependence is three orders below the discretisation error, and it
converges away with `h`. A scheme that instead stops running on a shock tube
cannot be a default.

The contour form should be **retained as an experiment**, for three reasons: it
is the only discretely covariant form available; it is more accurate on smooth
flow at accessible resolutions; and under N it is robust and marginally less
oscillatory than the Roe form. `contour + N` in particular is a viable
combination that this campaign found no fault with.

### 5.3 Leave the mass pair and the timestep as they are

Arpaia stays the default: it carries the published analysis and every gate of
sections 17 to 25 was run on it. Campoli remains the verification path and the
positive-divisor fallback, with one property worth remembering — its divisor
coincides with the storage area, so it needs no endpoint rebase and conserves
four orders better on a flip-free interval (section 4.1). If the endpoint rebase
ever becomes a limiting error, that is the reason to switch.

`RD_ALE_CFL_TIMESTEP` is defensible on its own terms and costs 0.8 per cent of
`L1` for a factor of two in steps (section 30.2). It should not become a default
until the unresolved point of section 27.4 is closed: the Arpaia midpoint mass
depends on the future geometry, so the current-mesh predictor is explicit rather
than a proof of the implicit bound.

---

## 6. What would overturn this

- **A positivity or limiting mechanism for the contour form.** Its Sod failure
  is a non-physical predictor, which is the kind of thing a limiter addresses.
  If the contour form could be made as robust as the Roe form, its exact
  covariance and smooth-flow accuracy would make it the better default.
- **A regime where the frame dependence is not negligible.** All of section 5.2
  rests on the frame dependence being three orders below the discretisation
  error. A problem with a much larger bulk velocity relative to its internal
  structure, or a much better-resolved one, could invert that.
- **Three dimensions or multiple ranks.** Both are outside this prototype. The
  rank-invariance half of the `S^-` degeneracy argument (section 3.5) has never
  been testable, and it is the same degeneracy that section 4.4 shows is generic
  in shear.
- **B.** Excluded from the whole phase. The blend coefficient is built from the
  total residual, so the choice of residual form enters it directly and this
  campaign says nothing about that.

## 7. Reproducibility

- Initial conditions: `examples/gresho_2d/create_mmrd_ics.py`, which gained the
  Sod and KH families for this campaign; `--verify` checks the tree against
  `MMRD_ICS.sha256`.
- Configs: `examples/gresho_2d/Config_F_*.sh`, `Config_FY_*.sh` (Yee, `gamma`
  1.4), `Config_FS_*.sh` (Sod and KH, `gamma` 1.4).
- Parameter files: `examples/gresho_2d/param_F_*.txt`.
- Output and provenance: `/home/zwu/Hydro_data_analysis/Data_MMRD_debug/output_F_*`.
- All builds through `build_case.sbatch`, all runs through `run_case.sbatch`,
  on Slurm compute nodes with MKL and immutable artifacts.
