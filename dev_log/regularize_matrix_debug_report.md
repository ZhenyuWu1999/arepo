# `regularize_matrix()`: diagnosis and removal

- Author: `Claude Code Opus5`
- Repository: `/home/zwu/arepo_rd/arepo`
- Baseline commit analysed: `ebe1be2` ("Stabilize synchronized residual-distribution baseline")
- Scope: `src/hydro/residual_distribution_solver.c`

This report records why the matrix regularisation in the residual-distribution
solver was wrong, why the singularity it was meant to work around does not in
fact require any regularisation, and what was changed in the code.

Notation follows the thesis (`Zhenyu-PhDThesis/zhenyu_thesis/chapter3/chapter3.tex`).

**Symbols that look alike but are not:**

| symbol | meaning | source |
| --- | --- | --- |
| `S^±` (bold, superscript ±) | `sum_{j in T} K_j^±`, a 4x4 matrix | thesis ch. 3 |
| `\|S_i\|` (scalar, subscript i) | median dual control area of vertex `i` | thesis notes, sec. 10 |
| `(S^-)^dagger` | Moore-Penrose pseudo-inverse — deliberately `dagger`, not `+`, to avoid colliding with `S^+` | this report |

Superscript `T` always denotes the element `T`, never a transpose.

**Index correspondence between thesis and code:**

```
    thesis  i in T   vertex           <->   code  j = 0,1,2      (DT[..].p[j])
    thesis  j in T   summation index  <->   code  j
    thesis  T        element          <->   code  i  ->  thistask_triangles[i]
```

---

## 1. Notation and the identities the scheme relies on

Geometry (`src/mesh/voronoi/voronoi.c:1153-1160`): `n_i` is the inward normal
of the edge opposite vertex `i`, with `|n_i|` equal to that edge length.

```
(G)         sum_{i in T}  n_i  =  0
```

Inflow matrices (thesis ch. 3; code `residual_distribution_solver.c:721-759`),
evaluated at the Roe parameter-vector average `Zbar^T = (1/3) sum_i Z_i`:

```
            K_i  =  (1/2) ( n_{x,i} Abar_x  +  n_{y,i} Abar_y )

            K_i    =  R_i  Lambda_i    R_i^{-1}
            K_i^±  =  R_i  Lambda_i^±  R_i^{-1} ,   Lambda_i^± = (1/2)(Lambda_i ± |Lambda_i|)

            Lambda_i = diag( u_n + c - v_n ,  u_n - c - v_n ,  u_n - v_n ,  u_n - v_n )
                            \___acoustic__/   \___acoustic__/  \_entropy_/  \_shear__/

            u_n = ubar . nhat_i ,   v_n = vbar_mesh . nhat_i     (static mesh: v_n = 0)
```

Write `r_{p,i}` for column `p` of `R_i` and `(R_i^{-1})_p` for row `p` of
`R_i^{-1}`. Define

```
            S^±  :=  sum_{j in T}  K_j^±
```

Three identities hold to round-off, because every entry of `Kmatrix` is a
*linear* function of `Value1..Value4`:

```
(I1)        K_i^+  +  K_i^-  =  K_i                       for each i

(I2)        sum_{i in T} K_i  =  (1/2) A( sum_i n_i )  =  0        by (G)

(I3)        S^+  =  - S^-                                          by (I1)+(I2)
```

Element residual (code `:765-773`):

```
            phi^T  =  sum_{i in T}  K_i( Zbar^T )  Uhat_i
```

Distributions (code `:811-898` before the change):

```
  LDA     beta_i^{LDA,T}  =  K_i^+ (S^+)^{-1}  =  - K_i^+ (S^-)^{-1}
          phi_i^{LDA,T}   =  beta_i^{LDA,T} phi^T

  N       Uhat_in^T   =  (S^-)^{-1} sum_{j in T} K_j^- Uhat_j
          phi_i^{N,T} =  K_i^+ ( Uhat_i - Uhat_in^T )

  B       phi_i^{B,T}  =  Theta^T phi_i^{N,T}  +  ( I - Theta^T ) phi_i^{LDA,T}
          Theta^T_kk   =  min( 1 , |phi^T_k| / sum_j |phi^{N,T}_{j,k}| )
```

Conservation follows from (I3) and (I1):

```
  LDA:   sum_i beta_i^{LDA,T}  =  ( sum_i K_i^+ ) (S^+)^{-1}  =  S^+ (S^+)^{-1}  =  I     OK

  N:     sum_i phi_i^{N,T}  =  sum_i K_i^+ Uhat_i  -  S^+ Uhat_in^T
                            =  sum_i K_i^+ Uhat_i  +  S^- (S^-)^{-1} sum_j K_j^- Uhat_j   by (I3)
                            =  sum_i ( K_i^+ + K_i^- ) Uhat_i                             by (I1)
                            =  phi^T                                                      OK

  B:     conservative for any Theta^T, provided N and LDA already are.
```

> Conservation rests entirely on (I3), and the `S^±` appearing inside
> `(S^±)^{-1}` must be the *same* matrix as the one in (I3).

---

## 2. What the code did, and the two defects

Baseline code (`ebe1be2`, `residual_distribution_solver.c:775-796`):

```
     S^- <- sum_j K_j^-
     if  min_{k,p} |S^-_{kp}| < THRESHOLD (= 1e-15):     S^- <- S^- + eps I,  eps = 1e-10
     S^- <- (S^-)^{-1}   via dgetrf + dgetri
```

Writing `S^-_eps := S^- + eps I`, the code uses `(S^-_eps)^{-1}` while (I3) still
refers to the unperturbed `S^-`. Therefore

```
     sum_i beta_i^{LDA,T}  =  S^- (S^-_eps)^{-1}  =  I  -  eps (S^-_eps)^{-1}   !=  I
```

In the spectral decomposition of `S^-` with eigenvalues `sigma_p`:

```
     ( sum_i beta_i )_pp  =  sigma_p / (sigma_p + eps)

     conservation loss per mode  =  eps / (sigma_p + eps)

         sigma_p >> eps   ->  loss ~ eps/sigma_p        harmless
         sigma_p  = 0     ->  loss = 1                  that mode of phi^T is discarded entirely
```

The N scheme has the same structure, with defect `- eps (S^-_eps)^{-1} b`.

Measured (gamma = 5/3, one representative triangle):

| state | singular values of `S^-` | `\|\|sum_i beta_i - I\|\|_inf` |
| --- | --- | --- |
| `u = 0` | `[2.24, 1.31, 0.92, 0]`, exactly singular | **1.0** |
| `u = 1e-8` | `sigma_min ~ 8e-9`, `kappa ~ 3e8` | **1.3e-2** |
| `u = 0.5` | `kappa ~ 9` | `3e-10` |
| `u = 3` | `kappa ~ 76` | `5e-10` |

**How to read this table.** These are *per-element relative* defects. The
resulting global drift is proportional to `phi^T` in the affected elements, and
a stagnant region is typically also a nearly uniform one, where `phi^T` is close
to zero. The measured global effect is therefore far smaller than the worst-case
relative figure; see section 7. What the table does establish is that the
identity `sum_i beta_i = I` is not merely inaccurate but *structurally broken*,
by an amount that is bounded only by how small `phi^T` happens to be. It is not
a bound that the scheme controls.

The two defects are independent:

**D1, dimensional.** `THRESHOLD` and `eps` are absolute constants, whereas
`[S^-] = [velocity] x [length]`. In AREPO's arbitrary unit system they carry no
invariant meaning. More fundamentally, *the minimum entry magnitude of a matrix
has nothing to do with its conditioning*: a matrix can be exactly singular with
all entries `O(1)` (never triggers), or perfectly conditioned with one zero
entry (always triggers). The test is not a singularity test.

**D2, conservation.** The expression above.

A caution about attribution: it is tempting to connect this to the gas-mass
changes of 1.00037 / 1.00208 / 1.00975 recorded earlier in
`RD_DEVELOPMENT_LOG.md` (same directory), and an earlier draft of this report did so. That
connection is **not supported**. Those runs predate the `ebe1be2` fixes
(sentinel handling, `DualArea` completeness, the extrapolation condition), and
the measurement in section 7 shows the regularisation alone accounts for a drift
of order `1e-14`, not `1e-2`, in this configuration. The historical drift was
almost certainly caused by the bugs CodeX fixed, not by `regularize_matrix()`.

### Why `S^-` is singular in the first place

At `u_n = v_n`:

```
     Lambda_i    =  ( c , -c , 0 , 0 )
     Lambda_i^-  =  diag( 0 , -c , 0 , 0 )

 =>  K_i^-  =  -(c/2) |n_i| r_{2,i} (R_i^{-1})_2            rank 1
     K_i^+  =  +(c/2) |n_i| r_{1,i} (R_i^{-1})_1            rank 1

 =>  rank(S^-)  =  rank( sum of three rank-1 matrices )  <=  3  <  4
```

This is structural, not an accident of round-off.

> **Consequence for moving mesh.** The degeneracy condition is `u_n = v_n`,
> i.e. *the mesh moving with the fluid*. On a Lagrangian moving mesh that is the
> normal state of every element, not an exception. The change described here is
> therefore a prerequisite for ALE-RD, not only a fix for the stagnant outer
> region of the Gresho vortex.

---

## 3. The singularity is removable

### Lemma 1 (consistency)

> When `u_n = v_n`, `phi^T` always lies in `range(S^-)`.

```
Proof.  By (I1),  phi^T = sum_i ( K_i^+ + K_i^- ) Uhat_i, and at stagnation both
        K_i^± are rank 1, so

            phi^T  in  span{ r_{1,i} , r_{2,i} }_{i in T}.

        At stagnation the acoustic right eigenvectors are

            r_{1,2}(nhat)  =  ( 1 ,  ± c nhat_x ,  ± c nhat_y ,  H )^transpose,

        and since the three nhat_i span R^2, both families span the same
        three-dimensional subspace

            V  =  span{ (1,0,0,H) , (0,1,0,0) , (0,0,1,0) }.

        But range(S^-) = span{ r_{2,i} }_{i in T} = V as well, hence
        phi^T in V = range(S^-).                                              []
```

So `S^- x = phi^T` is **consistent**; only its solution is non-unique. The null
space follows analytically:

```
     S^- z = 0   <=>   (R_i^{-1})_2 . z = 0  for all i in T
                 =>    null(S^-) = span{ (1,0,0,0)^transpose }
```

which matches the numerical result. Physically this is an isobaric density
perturbation of a fluid at rest (`rho` varies, momentum `= 0`,
`E = p/(gamma-1)` fixed): an exact equilibrium that carries no flux. The null
space is the stationary entropy wave.

### Lemma 2 (gauge invariance)

> The distributed residuals do not depend on which solution of `S^- x = phi^T`
> is selected.

```
Proof.  Let z in null(S^-).  By (I3), z in null(S^+), i.e.

            (c/2) sum_{i in T} |n_i| r_{1,i} ( (R_i^{-1})_1 . z )  =  0.

        The three r_{1,i} are linearly independent, so

            (R_i^{-1})_1 . z  =  0    for each i separately
        =>  K_i^+ z  =  0             for each i separately.

        Hence phi_i^{LDA,T} = -K_i^+ x is unchanged under x -> x + z, and
        phi_i^{N,T} = K_i^+ (Uhat_i - y) is unchanged under y -> y + z.       []
```

Numerical check on one triangle (same element as the table above):

```
  min-norm x    phi_0 = [-0.00578418  0.01307327  0.0101681  -0.07113387]   ||sum phi_i - phi^T|| = 4.5e-16
  x + 1e3 z     phi_0 = [-0.00578418  0.01307327  0.0101681  -0.07113387]   ||sum phi_i - phi^T|| = 4.5e-16
  x - 7 z       phi_0 = [-0.00578418  0.01307327  0.0101681  -0.07113387]   ||sum phi_i - phi^T|| = 4.5e-16
```

Every significant digit agrees.

### Corollary

> At stagnation the LDA and N distributions are well defined and unique. The
> only object that fails to exist is `(S^-)^{-1}`. No regularisation is
> mathematically required.

---

## 4. The change

### 4.1 Solve instead of invert

```
     x  :=  (S^-)^dagger phi^T                                  for LDA
     y  :=  (S^-)^dagger b ,   b := sum_{j in T} K_j^- Uhat_j   for N

     (S^-)^dagger :   LU solution when S^- is non-singular
                      minimum-norm least-squares solution when it is rank deficient
                      (valid by Lemma 2)

     phi_i^{LDA,T}  =  - K_i^+ x
     phi_i^{N,T}    =    K_i^+ ( Uhat_i - y )
```

Both right-hand sides share the same matrix, so a single factorisation serves
both. This is also cheaper than the previous code path, which formed the
explicit inverse and then built the full `BetaLDA[4][4][3]` tensor.

Implementation (`rd_solve_upwind_system()`):

1. `LAPACKE_dgetrf` on a copy of `S^-`.
2. If `info != 0`, or if `min|diag(U)| / max|diag(U)|` falls below
   `RD_LU_FALLBACK_PIVOT_RATIO` (`1e-12`), fall back to `LAPACKE_dgelsd`.
   The pivot ratio is only a cheap trigger, not a condition-number estimate.
3. `DGELSD` uses `rcond = -1`, its machine-precision cutoff, and makes the
   authoritative numerical-rank decision.
4. Otherwise `LAPACKE_dgetrs` with `nrhs = 2`.

The LU trigger and the SVD cutoff intentionally answer different questions.
The former asks when LU should be replaced by a more reliable solver; it does
not declare the matrix rank deficient. The latter asks whether a singular
direction is numerically resolvable. A controlled `rcond` scan (section 7)
showed that forcing both thresholds to `1e-12` truncates resolvable fourth
singular values, changes `S^- x = rhs` into a non-zero-residual least-squares
problem, and enlarges the raw conservation defect by one to two orders of
magnitude. Switching from LU to SVD is therefore not a no-op even when DGELSD
reports full rank.

`RD_SVD_RCOND` can be overridden at compile time for sensitivity tests; its
production default is `-1.0`. A direct condition estimator such as `dgecon`
would be stronger than the pivot heuristic and remains a possible later
refinement.

### 4.2 Raw conservation assertion; no rebalance

The LDA and N conservation identities in section 1 are exact properties of the
distribution. B is conservative because it blends two distributions whose
vertex sums are both `phi^T`. No correction belongs in the scheme.

`rd_enforce_conservation()` was therefore replaced by
`rd_check_conservation()`. It computes and records the raw defect

```
     delta = max_k |phi_k^T - sum_i phi_{i,k}^T|
```

and never modifies a distributed residual. Under `RD_DEBUG_ASSERTS`, A2
terminates if this raw defect exceeds a forward round-off bound. The bound is
based on the absolute matrix-vector products *before* cancellation:

```
     scale_LDA = max_k ( |phi_k^T| + sum_{i,l} |K^+_{kli}| |x_l| )
     scale_N   = max_k ( |phi_k^T| + sum_{i,l} |K^+_{kli}| (|U_{l,i}|+|y_l|) )
     tolerance = 4096 eps_machine scale
```

Using `|U|+|y|`, rather than the already-cancelled `|U-y|`, is essential in
quiet elements: `U-y` can be at machine epsilon even though it was formed by
subtracting two order-unity states. The B check also includes the LDA and N
operation scales plus the absolute blend operands.

This makes A2 an independent assertion again. A broken solve, distribution,
index or MPI path now terminates instead of being silently repaired.

### 4.3 Code changes in `src/hydro/residual_distribution_solver.c`

| change | detail |
| --- | --- |
| removed | `needs_regularization()`, `regularize_matrix()`, `THRESHOLD`, `REGULARIZATION_CONSTANT`, and the `regularize_matrix()` + `mat_inv()` call site |
| added | `rd_solve_upwind_system()` — LU with a `1e-12` pivot-ratio solver-selection trigger, then `dgelsd` with its machine-precision numerical-rank cutoff, `nrhs = 2` |
| added | `rd_check_conservation()` — measures and asserts the raw conservation defect without modifying the distribution |
| rewrote | LDA branch: `phi_i = -K_i^+ x` directly; the `BetaLDA[4][4][3]` tensor is gone |
| rewrote | N branch: `Bracket[k][j] = Uhat[k][j] - y[k]`; `KU_Sum` folded into the shared right-hand side |
| added | `rd_assert_K_sum_vanishes()` (assertion A1) and the in-loop conservation assertion A2, both under `RD_DEBUG_ASSERTS` |
| added | per-call solver statistics (`RD-DIAG` line, item A4) under `RD_DEBUG_ASSERTS` |
| kept | `mat_inv()` and `solve_system()`, now unused, as debugging utilities |

Other files:

- `Template-Config.sh`: registered `RD_DEBUG_ASSERTS`.
- `examples/gresho_2d/Config_RD.sh`, `examples/yee_2d/Config_RD.sh`: enabled
  `RD_DEBUG_ASSERTS`, since these are the validation configurations.

The previous behaviour remains reproducible by checking out `ebe1be2`.

---

## 5. Assertions and instrumentation

An **assertion** here means a runtime check of an invariant that must hold
mathematically. It is evaluated inside the solver for every element and every
stage, and terminates with context if violated. This differs from a test, which
runs a whole case and compares the final result.

Assertions matter for this solver specifically because its intermediate
quantities — `K_i^±`, `S^-`, `beta_i` — have no physical counterpart that could
be inspected in a snapshot. They are the only way to catch an error where it
happens. All of them compile out unless `RD_DEBUG_ASSERTS` is set.

| id | check | catches | kind |
| --- | --- | --- | --- |
| A1 | `\|\|sum_i K_i\|\|_inf <= tau max_i \|\|K_i\|\|_inf` | flipped triangle orientation, inconsistent normal/magnitude convention, faulty eigenvalue splitting | assertion |
| A2 | raw `\|\|sum_i phi_i^T - phi^T\|\|` bounded by a pre-cancellation floating-point scale | any break in the solve or distribution chain; no correction is applied | assertion |
| A3 | signed area `> 0` | triangle orientation, the precondition for `K_i` using inward normals | assertion |
| A4 | SVD-fallback count, exact-singular count, SVD rank histogram, `rcond`, `min_pivot_ratio`, raw conservation defect | separates “LU was not trusted” from “SVD found a deficient rank” | instrumentation, not a pass/fail check |

A4 emits one line per `compute_residuals()` call:

```
RD-DIAG time=... elements=... svd_fallback=... exact_singular=...
        svd_rcond=... rank_counts=[n0,n1,n2,n3,n4] min_svd_rank=...
        min_pivot_ratio=... cons_defect_abs=...
```

`cons_defect_abs` is the unmodified raw defect and is the direct measure of
whether the mathematical conservation identity still holds numerically.

---

## 6. What this change does not address

1. **Accuracy of the split when `S^-` is near-singular but not singular.**
   At `|u_n - v_n| / c ~ 1e-8`, `kappa(S^-) ~ 1e8` and `x` loses roughly eight
   significant digits. A2 now exposes any resulting conservation defect
   directly; what may also degrade is the *accuracy* of the split. Since `phi^T -> 0`
   as the element state becomes uniform, the absolute error stays bounded. This
   belongs to A4 measurement, not to a fix.

2. **Low-Mach-number accuracy.** Untouched by design. The upwind dissipation of
   Godunov- and Roe-type operators scales like `1/M` relative to the physical
   pressure fluctuations. AREPO's own finite-volume solver has the same property
   and carries no low-Mach correction either, so treating only the RD path would
   bias the RD-versus-FV comparison. Recorded as an open question in
   `RD_DEVELOPMENT_LOG.md` (same directory).

3. **Mass-matrix / unsteady linearity preservation.** Orthogonal to this change.
   The lumped-mass two-stage update is a separate question, to be answered by an
   advected (not stationary) smooth vortex test.

4. **Well-balancing under gravity.** With self-gravity, `u = 0` but
   `grad p = -rho grad Phi_grav != 0`, so `phi^T != 0` must be cancelled by the
   source term. The current Strang-split source treatment is not well balanced.
   Separate issue, separate open question.

---

## 7. Verification

Build: the Gresho `Config_RD.sh` configuration compiles with GCC/OpenMPI. No new
compiler warnings; the six remaining warnings in this file (`Ndp`, `p`,
`PrimExch_index`, `Value4`, `rho_avg`) are all pre-existing.

### Runtime A/B against `ebe1be2`

Both binaries were built from the same `Config_RD.sh` (LDA, static mesh, equal
timesteps, double precision) with system LAPACKE, and run on one rank on
`IC_gresho_v1e-8_random48`. Totals were recomputed from the snapshots, because
`energy.txt` is written with `%g` and only carries six significant digits.

| | `ebe1be2` (regularised inverse) | `07f264a` (solve + historical rebalance) |
| --- | --- | --- |
| gas-mass drift at `t = 0.5` | `-2.198e-14` | `-2.220e-16` |
| gas-mass drift at `t = 1.0` | `-2.276e-14` | `-8.882e-16` |
| total-energy drift at `t = 0.5` | `0.0` | `+2.062e-16` |
| total-energy drift at `t = 1.0` | `-2.062e-16` | `-2.062e-16` |
| `min(rho)` at `t = 0.5` / `t = 1.0` | `0.997078` / `0.995596` | `0.997078` / `0.995596` |

So the mass drift improves by about two orders of magnitude, to the level of
accumulated round-off. It does **not** improve by the twelve orders of magnitude
that the per-element table in section 2 might suggest, for the reason given
there: in this problem the degenerate elements are also the nearly uniform ones,
where `phi^T` is almost zero.

The baseline drift is also essentially *not accumulating*: `-2.198e-14` at
`t = 0.5` against `-2.276e-14` at `t = 1.0`. It is incurred during the early,
maximally stagnant phase and then frozen, which is consistent with the observed
rise of the minimum pivot ratio from `4.3e-10` at `t = 0` to `2.8e-5` by
`t ~ 0.96` as the vortex spins up and the elements move away from stagnation.
`min(rho)` agrees between the two runs to all six printed digits at both times,
so the solutions themselves are not measurably different here.

`RD-DIAG` statistics over the full run (26322 calls, `t = 0` to `t > 1.1`):

```
    calls needing the pseudo-inverse        : 0
    global minimum pivot ratio              : 8.05e-12       (kappa ~ 1.2e11)
    global maximum pre-rebalance defect     : 1.64e-14
```

The LU path was therefore always taken here, and it already conserved to
machine precision on its own. This historical measurement was one reason the
later review removed the redundant rebalance.

### Exercising the rank-deficient path

The `v1e-8` initial conditions never reach exact singularity. Repeating on
`IC_gresho_v0_random48`, where the outer region is at rest exactly:

```
RD-DIAG time=0 elements=4610 pseudo_inverse=2108 (45.7%) min_pivot_ratio=7.72e-05 max_cons_defect=2.77e-14
...
    512 calls, 29821 pseudo-inverse solves out of 2360320 element solves
    global minimum pivot ratio          : 3.13e-20     (singular to machine precision)
    global maximum pre-rebalance defect : 2.95e-14
    gas-mass drift at t = 0.05          : -2.220e-16
    total-energy drift at t = 0.05      : +2.061e-16
```

**45.7 per cent of the elements are rank deficient at `t = 0`.** This is the
strongest single result here. Nearly half the mesh was previously being handled
by an arbitrary diagonal shift, with `sum_i beta_i - I = 1` in the null
direction; those elements are now solved correctly, and conservation stays at
machine precision throughout.

Note also what the drift metric does *not* capture. In those 45.7 per cent of
elements the baseline computed `beta_i^{LDA}` from a perturbed matrix, so the
*distribution* was wrong even where the *sum* happened to be nearly right. That
is an accuracy effect, invisible to a conservation check, and it is a further
reason why convergence orders measured while the regularisation was active
cannot be trusted.

### Multi-rank invariance

`t = 0.1` on `IC_gresho_v{0,1e-8}_random48`, 1 / 2 / 4 ranks, snapshots matched
by particle ID. Errors are relative to the maximum of the 1-rank field.

| IC | ranks | Masses | Density | Velocities | InternalEnergy |
| --- | --- | --- | --- | --- | --- |
| `v1e-8` | 2 | `2.76e-15` | `9.41e-15` | `2.80e-15` | `9.64e-15` |
| `v1e-8` | 4 | `2.21e-15` | `6.09e-15` | `4.25e-15` | `6.15e-15` |
| `v0` | 2 | `1.70e-15` | `5.98e-15` | `4.93e-15` | `5.74e-15` |
| `v0` | 4 | `1.53e-15` | `5.98e-15` | `5.29e-15` | `6.15e-15` |

The number of element solves is *identical* across rank counts (4720640 for
`v0`, 9441280 for `v1e-8`), so the triangle ownership and duplicate-removal
rules reproduce exactly the same global element set under every decomposition.

One caveat, found by this test. The pseudo-inverse fallback count is
`29821` on 1 rank against `29820` on 2 and 4 ranks — **the branch decision is
marginally rank dependent**. One element in roughly 4.7 million solves lands on
the other side of the `1e-12` pivot threshold, because a boundary triangle's
ghost coordinates come from a periodic image and its `S^-` differs in the last
bits. By Lemma 2 both branches yield the same distributed residuals, and the
field comparison above confirms agreement at `1e-14`, so this is harmless — but
the solve path is not bit-deterministic across decompositions and should not be
relied on to be.

### Triangle area: cross product instead of Heron

`triangle_get_normals_area()` in `src/mesh/voronoi/voronoi.c` now computes

```
    signed_area = 0.5 * ( (x1-x0)(y2-y0) - (x2-x0)(y1-y0) )
```

and terminates if it is not positive (assertion A3).

**Honest assessment of the benefit.** On the meshes actually in use this fixes
nothing. Measuring both formulas on the periodic Delaunay triangulation of
`IC_gresho_v0_random48` (9959 triangles, worst edge-length aspect ratio 139):

```
    Heron negative-radicand (NaN) cases  : 0
    max relative area error of Heron     : 1.75e-14   (median 3.6e-16)
    triangles with relative error > 1e-12: 0
```

and the resulting solution change is `~1e-14` in every field. So the earlier
suggestion in this report's planning notes that Heron could explain the
occasional run termination in `context.md` item 4 is **not supported**. Heron's
catastrophic cancellation needs far worse conditioning than these meshes
produce.

What the change is actually worth:

- assertion A3, which is free with the cross product and guards the most
  dangerous silent failure mode in the solver — a flipped triangle orientation
  would negate all three normals, exchange `K^+` and `K^-`, and turn the scheme
  anti-diffusive without any error being raised. A3 did not fire in any run;
  AREPO's orientation guarantee holds, and now the RD path checks it rather
  than assuming it;
- removal of a latent NaN path that would activate on more degenerate meshes,
  in particular near-cocircular point sets and the distorted configurations a
  moving mesh will eventually produce;
- marginally cheaper.

### Uniform static medium: the floor test

New case `examples/uniform_static_2d/`, periodic unit box, irregular seeded
point distribution, 32^2 cells, `rho = p = 1`, `u = 0`. Since all vertex states
coincide, `phi^T = (sum_i K_i) Uhat = 0` identically, so nothing may change.

```
    uniform, 1 rank,  t=0.50 : max|drho|/rho = 1.11e-15   max|v| = 5.16e-15   mass drift = 0
    uniform, 4 ranks, t=0.50 : max|drho|/rho = 6.66e-16   max|v| = 6.10e-15   mass drift = 0
```

This is also the maximally degenerate configuration for the solve:

```
RD-DIAG time=0 elements=2048 pseudo_inverse=2048 (100%) min_pivot_ratio=1.000e+00 max_cons_defect=1.53e-14
    whole run: 2097152 / 2097152 element solves used the pseudo-inverse (100.0%)
```

Every element in every step is rank deficient, the minimum-norm path is taken
throughout, and the state is preserved to round-off.

### Perturbed uniform medium: the discriminating test

As predicted, the uniform case does not distinguish the two code versions, since
`phi^T = 0` makes any broken `sum_i beta_i` irrelevant. The `perturbed` mode adds
a smooth periodic pressure ripple of relative amplitude `1e-3` while keeping
`u = 0`, so every element stays at the stagnation point but `phi^T` is now
non-zero and driven by `grad p`.

Pre-fix (`ebe1be2`) against post-fix, 1 rank:

| | `t = 0.25` | `t = 0.50` |
| --- | --- | --- |
| Density, `max\|old-new\| / max\|old\|` | `1.08e-14` | `2.96e-14` |
| InternalEnergy | `1.18e-14` | `2.93e-14` |
| **Velocities** | **`1.47e-10`** | **`1.66e-10`** |

The difference is concentrated in the velocity field and is `~1e-10` — that is,
**numerically equal to `REGULARIZATION_CONSTANT`**. This is exactly what the
analysis predicts, and it is worth spelling out because it also explains why the
old code never blew up:

- at `u = 0` the flux reduces to `F = (0, p, 0, 0)` and `(0, 0, p, 0)`, so
  `phi^T` has only momentum components. The damage therefore appears in the
  velocity, not in the density — as observed;
- the `O(1)` loss occurs only along `null(S^-) = span{(1,0,0,0)}`, the density
  direction, and by Lemma 1 `phi^T` has *exactly zero* component there. The
  catastrophic term multiplies a strictly vanishing quantity;
- what survives is the benign `eps/sigma_p` perturbation on the well-conditioned
  modes, and with `sigma_p = O(1)` in these code units that is precisely `eps`.

So Lemma 1 is not merely a technical step in the proof: it is the reason the
regularisation was survivable. It is also the reason the error level is set
directly by an absolute constant. Here `K` entries are `O(1)` and `eps = 1e-10`
buys a `1e-10` error; in a unit system where the `K` entries are `1e-6`, the same
constant would produce an `O(1)` error. Defect D1 and defect D2 are the same
defect seen from two directions.

Both rank counts of the perturbed case agree to every printed digit, so rank
invariance also holds in the fully degenerate configuration.

### N and B schemes

Both were built and run through the same battery. Results at `t = 0.1`
(Gresho `v1e-8`) and `t = 0.5` (uniform), MKL binaries, compute nodes:

| test | LDA | N | B |
| --- | --- | --- | --- |
| uniform floor, `max\|drho\|/rho`, 1 rank | `1.11e-15` | `1.93e-14` | `1.11e-15` |
| uniform floor, mass drift | `0` | `0` | `0` |
| Gresho rank invariance, 4 ranks | `8.2e-15` | `8.8e-15` | `5.1e-15` |
| Gresho rank invariance, 16 ranks | `6.6e-15` | `1.1e-14` | `7.2e-15` |

The schemes are genuinely distinct and B sits where it should. On Gresho:

```
    B vs LDA = 3.74e-2        B is much closer to LDA
    B vs N   = 1.21e-1
    N vs LDA = 1.49e-1        the two pure schemes are furthest apart
```

which is the expected behaviour of the blend in a smooth flow, where `Theta`
should be small and B should approach LDA.

### A false alarm from the conservation metric, and its fix

The first version of `rd_enforce_conservation()` returned the defect normalised
by *the element's own* magnitude:

```
    defect = max_k |phi^T_k - sum_j phi_{j,k}|
    scale  = max over k,j of ( |phi^T_k| , |phi_{j,k}| )
    return defect / scale
```

For the N and B schemes this reported values of `3.8` to `3.9`, against `1e-14`
for LDA. Since the algebraic maximum of that ratio is `4`, it looked as though
the N distribution was as non-conservative as it is possible to be, and that the
rebalance was silently doing `O(1)` work rather than absorbing round-off.

It was an artefact of the metric. Adding the absolute figure settles it:

| case | scheme | absolute defect | `max\|phi^T\|` | ratio |
| --- | --- | --- | --- | --- |
| Gresho | LDA | `1.39e-17` | `3.34e-02` | `6.6e-16` |
| Gresho | N | `1.85e-15` | `3.34e-02` | `1.6e-13` |
| Gresho | B | `1.82e-15` | `3.34e-02` | `2.5e-13` |
| uniform | N | `2.13e-15` | `7.95e-16` | — |

and the dump of the worst-scoring element confirms it directly:

```
RD-WORST task=0 N triangle=1079 rel=3.767e+00 abs=2.360e-16 scale=6.265e-17 |phi^T|max=6.265e-17
   k=0  phi^T= 4.341283e-18  phi_0= 2.559535e-18  phi_1=-3.936963e-18  phi_2=-3.954122e-18
   k=3  phi^T= 6.265111e-17  phi_0=-5.950391e-17  phi_1=-5.681617e-17  phi_2=-5.706379e-17
```

Every quantity is between `1e-18` and `1e-16`, while the run's largest element
residual is `3.3e-2`. The offending element is a quiet one in the outer Gresho
region where the exact answer is `phi^T = 0`; the metric was dividing round-off
by round-off.

Why the two schemes differ at all in this respect is nevertheless real, and
worth recording:

```
  LDA:  sum_i phi_i = -(sum_i K_i^+) x = S^- x = phi^T
        conservation IS the residual of the linear solve. One step.
        When phi^T = 0 exactly, x = 0 exactly and every phi_i is exactly 0.

  N:    sum_i phi_i = sum_i K_i^+ Uhat_i - (sum_i K_i^+) y = sum_i K_i^+ Uhat_i + S^- y
        needs the solve residual small AND the identity sum_i K_i^+ = -S^- to hold
        to high relative accuracy against ||y||. When phi^T = 0, y differs from
        Uhat by a null-space component, so phi_i = K_i^+ z is zero only in exact
        arithmetic (Lemma 2).
```

So N is structurally more delicate than LDA at the same conditioning, and its
absolute defect is about a hundred times larger — `1.8e-15` against `1.4e-17`.
Both are machine noise. This is why the later review removed the rebalance:
the raw defect is the useful diagnostic, while correcting it only weakens A2.

The metric was changed accordingly. `RD-DIAG` now reports `cons_defect_abs`
together with `max_phi` from the same call, and derives the relative figure as
`cons_defect_abs / max_phi`, which is scale-free without being fooled by quiet
elements. `RD-WORST` now triggers on the absolute defect. Note that in the
uniform case the relative figure is still meaningless, because `max_phi` is
itself machine zero there — read the absolute number for that test.

### 2026-07-29 verification after removing rebalance (provisional `rcond = 1e-12`)

All LDA, N and B configurations compile against system LAPACKE. A B-scheme
Gresho `v0_random48` run exercises both pure distributions and the blend:

- one rank and four ranks both reach `t = 0.01` without A2 firing;
- at `t = 0`, 2108/4610 elements use DGELSD, all with numerical rank 3;
- the run subsequently traverses pivot ratios from below machine precision
  through the previously uncovered `2e-16`--`1e-12` band;
- raw conservation defects peak around `1.2e-13` in this short run and remain
  within the pre-cancellation forward-error bound;
- snapshot mass drift at `t = 0.01` is `-4.77e-15`, momentum drift is below
  `1.5e-16`, and total-energy drift is zero at printed double precision;
- matching one- and four-rank snapshots by particle ID gives maximum relative
  field differences of `2.7e-15` or smaller.

A 256-cell uniform static B run reaches `t = 0.005` with every solve taking
DGELSD at rank 3. With no residual correction:

```
mass change             = 0
max density change      = 8.88e-16
max velocity magnitude  = 6.29e-17
max internal-U change   = 0
```

The raw `cons_defect_abs/max_phi` diagnostic is deliberately large in this
case because both quantities are numerical zero. A2 instead uses the absolute
pre-cancellation operation scale and correctly accepts defects of order
`1e-15` without modifying the residual.

### 2026-07-29 DGELSD cutoff sensitivity

The preceding run established that the implementation survived
`rcond = 1e-12`; it did not establish that this was the correct cutoff. A
controlled scan held the LU fallback trigger at `1e-12` and varied only
DGELSD's `rcond` over `-1`, `1e-14`, `1e-12`, and `1e-10`. Each one-rank
B-scheme Gresho `v0_random48` run contained 128 residual calls and 590080
element solves:

| `rcond` | DGELSD rank 3 | DGELSD rank 4 | max raw defect | mass drift |
| --- | ---: | ---: | ---: | ---: |
| `-1` | 18996 | 15676 | `5.25e-15` | `-1.11e-16` |
| `1e-14` | 25331 | 9341 | `7.87e-15` | `-1.11e-16` |
| `1e-12` | 34672 | 0 | `1.19e-13` | `-4.77e-15` |
| `1e-10` | 34672 | 0 | `1.19e-13` | `-4.77e-15` |

A second initial condition with a uniform `vx += 1e-11` boost directly places
full-rank systems below the LU pivot trigger. Its 620 SVD calls all return rank
4 for `rcond = -1` and `1e-14`, and all return rank 3 for `1e-12` and `1e-10`.
The maximum raw defect rises from `1.69e-15` to `9.72e-14` when the fourth
direction is truncated. A proposed `vx += 1e-5` test was also run, but its
minimum pivot ratio is about `6e-8`; it correctly serves only as a no-fallback
control.

Four-rank repetitions reproduce the same distinction. For `v0`, the maximum
raw defect is `6.17e-15` with DGELSD's default and `1.19e-13` with
`rcond = 1e-12`; the two final internal-energy fields differ by `1.52e-12`.
For `vx += 1e-11`, the corresponding defects are `2.23e-15` and `9.72e-14`.

The conclusion is mathematical as well as empirical. For a near-singular but
full-rank consistent system, imposing an unnecessarily large SVD cutoff
changes an exact solve into a least-squares solve with a residual. Since the
LDA conservation identity is the residual equation itself,

```
sum_i phi_i = S^- x = phi^T,
```

the resulting `O(rcond)` defect is expected, not round-off. The current policy
therefore uses `1e-12` only to select SVD over LU and leaves the authoritative
DGELSD rank cutoff at its machine-precision default (`rcond = -1`). Full
details and field comparisons are in the development-log entry at
2026-07-29 11:53:15 BST.

### Not yet verified
- Behaviour with MKL rather than system LAPACKE. MKL was unavailable on the
  machine used, so `build_case.sh` was bypassed and `make` was invoked directly.
- Odd rank counts (3), and long runs to `TimeMax = 3.0` under the final code.

Planned follow-ups, in order:

1. A4 statistics over the standard Gresho and Yee cases, to quantify how much of
   the mesh is actually in the near-stagnant regime.
2. Uniform static medium retention test: a periodic box with uniform `rho`, `p`
   and `u = 0` must be preserved to machine precision, since `phi^T = 0`
   identically. This is the cheapest decisive check and should be added to the
   test suite.
3. Heron-to-cross-product change for the triangle area, plus assertion A3.
4. Re-measurement of the Gresho and Yee convergence orders, which could not be
   trusted while the regularisation was active.
