# Why GL+F1 loses second order on irregular meshes

- Authors: `Zhenyu Wu and Claude Code (Opus 5)`
- Opened: 2026-08-01, from the campaigns recorded in the development-log entries
  of the same date.
- Status: analysis and measurement complete; **no implementation is proposed for
  the current milestone.** A glass mesh is good enough at the resolutions in use.
  This document exists so the result does not have to be rediscovered.

This is split out of `RD_DEVELOPMENT_LOG.md` because it is a standing property of
the scheme rather than a dated development step. The log entries of 2026-08-01
record the experiments; this records what they mean.

---

## 1. One-paragraph summary

`GL + F1` reaches clean second order on the advected Yee vortex on a regular
triangular lattice, and is asymptotically **first** order on any mesh whose
Delaunay connectivity is rough. Global Lumping is the first Neumann truncation of
the mass-matrix inverse, and the truncated term is `O(h)` rather than `O(h^2)`
exactly when the median-dual patch asymmetry varies on the mesh scale. The
first-order coefficient is proportional to that asymmetry, with the same constant
across unrelated mesh families. A SWIFT glass has an asymmetry ten times smaller
than a jittered Cartesian mesh, which buys about a factor of eight in resolution
before the first-order term takes over; measured, that crossover is near
`n = 350-450` in 2-D.

## 2. The algebra

The RD nodal equation with a consistent mass matrix is

```
   M u_dot = -L(u),     M_ij = sum_T m_ij^T,     L(u)_i = sum_T phi_i^T
```

which is implicit: `M` is not diagonal. Split it with the lumped (median dual)
diagonal `S = diag(|S_i|)`:

```
   M = S (I + X),     X := S^{-1}(M - S),     v := S^{-1}(-L)
```

`v` is the "lumped rate" -- the answer you get by ignoring the off-diagonal mass.
The exact solve is a Neumann series in `X`:

```
   u_dot = (I + X)^{-1} v = v - X v + X^2 v - X^3 v + ...
```

and the three formulations are successive truncations of it:

| formulation | `u_dot` | dropped term |
| --- | --- | --- |
| Mass Lumped (ML) | `v` | `-X v` |
| **Global Lumping + F1 (implemented)** | `(I - X) v` | `+X^2 v` |
| consistent mass | `(I + X)^{-1} v` | none |

Global Lumping is literally "keep one term of the Neumann series for `M^{-1}`".
That is not a defect: it is the device that keeps the scheme explicit, which is
the stated purpose of the RK-RD construction (Arpaia & Ricchiuto 2015, sec. 3.5).

The `|S_i| v_i` terms cancel identically in the `Delta t -> 0` limit of the
implemented corrector, which is what makes the identification exact rather than
approximate. Verified against `residual_distribution_solver.c` line by line.

## 3. What `X` is

With `F1`, `m_ij^T = beta_i^T |T| / 3` independent of `j`. Expanding and
splitting `sum_j w_j = 3 w_i + sum_j (w_j - w_i)`:

```
   (X w)_i = (1/|S_i|) sum_T (|T|/3) [ (3 beta_i - 1) w_i + beta_i sum_j (w_j - w_i) ]
```

For a smooth `w`, `sum_j (w_j - w_i) ~= 3 grad(w) . (x_c^T - x_i)`, so

```
   (X w)_i  ~=  grad(w) . d_i  +  (gamma_i - 1) w_i

   d_i    = (1/|S_i|) sum_{T in i} beta_i^T |T| (x_c^T - x_i)      [length, O(h)]
   gamma_i = (1/|S_i|) sum_{T in i} beta_i^T |T|
```

`d_i` is the `beta`-weighted mean of the vectors from node `i` to the centroids of
its surrounding triangles. Its meaning is geometric:

> the mass matrix, seen from node `i`, is not centred on node `i`; its centre of
> mass sits at `x_i + d_i`.

So `X` is, to leading order, a **discrete displacement operator of size `O(h)`**:
it evaluates the field a distance `d_i` away from the node. A symmetric patch
with equal weights gives `d_i = 0` exactly. Two independent things break that:
geometric asymmetry of the triangle patch, and the upwind bias of `beta`. A
centred distribution (`beta = I/3`) on a symmetric patch cancels both, which is
why lumping a *Galerkin* mass matrix in FEM costs only `O(h^2)`.

`gamma_i` is the row-sum condition Kimi proposed in the 2026-07-30 review. It is
the second, subdominant piece of `X` -- it is not a consistency requirement (see
the 2026-08-01 review entry), but it is not irrelevant either: it is part of the
operator whose square is the GL truncation error.

## 4. Why roughness, not size, sets the order

- **ML** drops `X v` outright. The error is `grad(v) . d_i = O(h)|grad v|`:
  **first order on any mesh** whenever `v != 0`, i.e. whenever the solution is
  unsteady. Measured 0.947/0.970 on the regular lattice and 0.93/0.95 on the
  jittered family -- the regular mesh does not rescue it.
- **GL+F1** drops `X^2 v`. Now `X` acts twice. The intermediate field
  `w := X v ~= grad(v) . d_i` has size `O(h)`.
  - If `d_i` varies **smoothly** across the mesh, `w` is a smooth `O(h)` field,
    its gradient is `O(h)/L`, and `X^2 v = O(h^2)`: **second order**.
  - If `d_i` is **mesh-scale rough**, the discrete gradient of `w` is `O(h)/h =
    O(1)` and `X^2 v = O(h)`: **first order**, with a coefficient set by the
    roughness amplitude.
- **`boost = 0`**: `v ~= 0`, so `X v` and `X^2 v` both vanish and every
  combination is second order. This is why the defect stayed invisible through
  every stationary test.

## 5. Measurements

Advected Yee vortex, `boost = 1`, LDA, density L1, `dt = 0.25/n`, all against one
immutable binary with no source change.

| family | orders |
| --- | --- |
| GL+F1, regular triangular lattice | 2.029, 2.011, 2.011 (to `n = 256`) |
| GL+F1, SWIFT glass (48 tiled) | 1.879, 1.737, 1.481 (to `n = 384`) |
| GL+F1, jittered Cartesian | 1.551, 1.312, 0.990 (to `n = 256`) |
| ML, regular triangular lattice | 0.947, 0.970 |

The last line is the control that makes the rest conclusive: the regular lattice
does not cancel errors generically, it specifically repairs `GL+F1`.

Fitting `E = A/n^2 + B/n` and measuring the *purely geometric* surrogate of `d_i`
(`beta` replaced by `I/3`, so it needs only the mesh),

```
   g_i = (1/|S_i|) sum_{T in i} (|T|/3) (x_c^T - x_i)
```

| family | `|g|/h` | `A` | `B` | `B / (|g|/h)` | `n* = A/B` |
| --- | ---: | ---: | ---: | ---: | ---: |
| triangular | `0.00000` | 1.275 | `-0.0006` | -- | infinite |
| glass (48 tiled) | `0.01704` | 1.264 | `0.00361` | 0.212 | 350 |
| jittered 0.20 | `0.16685` | 1.184 | `0.02375` | 0.142 | 50 |

`A` agrees across families to seven per cent, `B` vanishes on the lattice, and
`B` tracks the patch asymmetry to about +/- 20 per cent across a tenfold range.
An independent check: the Neumann contraction measured as `B_GL / B_ML = 0.147`
matches the jittered `|g|/h = 0.167`, as it must if `X` is the displacement
operator above.

**The observed order is not a property of the scheme.** It is the local slope of
a two-term error, `p(n) = (2 + n/n*) / (1 + n/n*)`, sliding from 2 to 1 as `n`
crosses `n* = A/B`. That two-parameter model reproduces all three sequences.

## 6. What does and does not fix it

**Does not:**

- *Reducing the mesh perturbation.* The roughness of `d_i` comes from the
  triangulation connectivity, not from the point displacement. On a near-Cartesian
  point set the two candidate Delaunay diagonals of each quad differ by under one
  per cent while the in-circle test still picks between them 50/50, so `|g|/h`
  stays at 0.15 for any jitter amplitude. Measured.
- *Refining harder.* The mesh families are self-similar, so `|g|/h` is
  resolution-independent and `B` is a constant. Refinement reveals the term, it
  does not remove it.
- *`F2`.* Its offset is `|T|(beta_i - 1/12)(x_c - x_i)`: a constant shift of
  `beta`, with no reason to make `d_i` smooth.
- *Fixing the stage-`beta` mixture.* That is a different, temporal term worth
  2-4 per cent of the error, scaling as `h^1.75` in the production ladder.

**Does:** carry the Neumann series further. Because `S`-preconditioned Richardson
iteration on `M u_dot = -L` *is* this Neumann series, "iterate the mass-matrix
solve" and "keep more terms" are the same change, and the current code is already
its `k = 1` member (`ML` is `k = 0`).

Two versions that look like the same code but are different algorithms:

```
   fixed k terms         error O(h),  n* multiplied by ~7 per term
   iterate to tolerance  error = the tolerance, independent of h
```

Only the second removes the `h^1` term. Its cost is bounded and does not grow
with resolution: `||X||` is a property of the mesh family, not of `h`, so the
iteration count for a fixed tolerance is `h`-independent -- about 15 iterations
for `1e-12` at `||X|| = 0.15`. Each iteration is one element loop accumulating
`beta_i (|T|/3) sum_j w_j` plus one ghost exchange; `beta` and the `K` matrices
are already available from the residual sweep. Conservation holds at every
iteration count, since each term is a distribution obeying `sum_i beta_i = I`.

Extrapolating from the measured contraction `||X|| = 0.147`:

| terms `k` | jittered `n*` | glass `n*` |
| ---: | ---: | ---: |
| 0 (ML) | -- | 66 |
| **1 (implemented)** | **50** | **450** |
| 2 | 339 | 3062 |
| 3 | 2309 | 20842 |

## 7. Open points, if this is ever taken up

1. **Untested assumption.** That the *converged* consistent-mass scheme is
   exactly second order on a rough mesh is the RD theory's claim, not our
   measurement. Supporting evidence: the stationary jittered ladder is 2.01/2.07,
   so the spatial operator is second order on a rough mesh, and the mass matrix
   was the only mesh-roughness-sensitive piece in the analysis. The cheap test is
   to implement the tolerance-based iteration and rerun the *jittered* ladder --
   the harshest case. If `n = 256` moves from 0.990 to near 2, the question is
   closed.
2. **Convergence guard.** The iteration needs `||X|| < 1`. Measured 0.147 on the
   jittered family, so it is safe there, but near stagnation and under ALE `S^-`
   becomes rank deficient, `beta` ill-defined, and `||X||` could approach 1. A
   divergence guard falling back to `k = 1` or to ML, with a counter, is required.
   This is coupled to the rank contract of `rd_solve_upwind_system()`.
3. **The RK algebra changes with `k`.** The corrector's `+dU/2` substitution is
   exact only in the `k = 1` form, because `dU/2` equals
   `-(Delta t/|S_i|) (1/2) sum_T phi_i^n` identically. A different `k` needs that
   identity rederived and conservation rechecked. This is a derivation plus about
   thirty lines, not an edit.
4. **Selective Lumping** (Arpaia & Ricchiuto eq. 52) is a different splitting
   whose truncation has not been derived here. Do not assume it fixes this;
   derive its error term first. Its Galerkin mass matrix has its own geometric
   offset `(3/4) g_i`, which is not obviously better.

## 8. Consequence for the test methodology

**A jittered Cartesian point set is not a valid mesh family for measuring
unsteady RD accuracy.** Its near-degenerate Delaunay makes it a worst case that
no amount of refinement or de-jittering escapes, and it caused a correct scheme
to be measured at order 1.3. Future convergence work should use the regular
triangular lattice as a control (`mesh_family = triangular` in
`Hydro_data_analysis/Analysis/yee_boost/yee_boost_common.py`) and a glass as the
realistic case.

Related: the Voronoi centroid offset `|CoM - x|/h` available in the snapshots is
**not** a usable regularity measure for this purpose -- it falls eightfold between
jitter 0.20 and 0.025 while the order does not move. The quantity that matters
lives on the Delaunay connectivity. This is a direct answer to open question 1 of
`context.md`: the choice is not "median dual versus Voronoi volume" but the
asymmetry of the median-dual patch, and it is the Delaunay that sets it.
