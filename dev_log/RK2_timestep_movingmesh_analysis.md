# RK2, hierarchical timesteps and moving mesh: structural analysis

- Author: `Claude Code Opus5`
- Started: 2026-07-29
- Status: analysis only. No implementation decision has been taken.
- Scope: `src/hydro/residual_distribution_solver.c`, `src/main/run.c`, and the
  interaction of the residual-distribution time integration with AREPO's
  timebin and mesh machinery.

**Design constraint set by Zhenyu.** A space-time residual-distribution rewrite
is out of scope: it is too expensive. The target is to reuse AREPO's existing
Voronoi/Delaunay construction, timebin hierarchy, domain decomposition and MPI
ghost exchange, and to change only what the mathematics forces us to change.
Everything below is evaluated against that constraint.

Notation follows the thesis, `chapter3/chapter3.tex` sections
`eq:RD_RK2_predictor` through `eq:RD_RK2_mass_choices`. `i`, `j` index the
`d+1` vertices of an element `T`; superscript `T` denotes the element, never a
transpose.

---

## 1. What the thesis specifies

```
predictor        U*_i = U^n_i − (Δt/|S_i|) Σ_{T∋i} φ_i^T(U^n)

total element    Φ^T  = (|T|/3) Σ_{j∈T} (U*_j − U^n_j)/Δt
residual                + ½ [ φ^T(U^n) + φ^T(U*) ]

total nodal      Φ_i^T = Σ_{j∈T} m_ij^T (U*_j − U^n_j)/Δt
residual                 + ½ [ φ_i^T(U^n) + φ_i^T(U*) ]

corrector        U^{n+1}_i = U*_i − (Δt/|S_i|) Σ_{T∋i} Φ_i^T

mass matrices    m_ij^{N}   = (|T|/3) δ_ij I
                 m_ij^{LDA} = (|T|/3) β_i^{LDA}

conservation     Σ_{i∈T} m_ij^T = (|T|/3) I     for every j
```

Two points that matter later:

- the predictor is a **first-order RD update**, not a Taylor extrapolation;
- with the N mass matrix the corrector collapses to the Heun form, and this
  collapse is *identical for any* `U*`, because the `U*` terms cancel:

```
   Σ_T Φ_i^T = |S_i|(U*_i − U^n_i)/Δt + ½ Σ_T [...]        (Σ_{T∋i}|T|/3 = |S_i|)
   U^{n+1}_i = U*_i − (U*_i − U^n_i) − (Δt/2|S_i|) Σ_T [...]
             = U^n_i − (Δt/2|S_i|) Σ_T [ φ_i(U^n) + φ_i(U*) ]
```

So the predictor choice does not change the *structure* for N; it only enters
through `φ_i(U*)`. For LDA the collapse does not happen and the general
corrector must be used.

---

## 2. What the code implements, and the gap

`compute_residuals()` is called twice per step, at `run.c:229` with
`dt_Extrapolation = 0` and at `run.c:324` with `dt_Extrapolation = dt`, each
applying `dt/2`. Confirmed at runtime: over a whole Gresho run the
`RD-DIAG dt_extrap` field takes exactly two values, `[0,0]` and `[dt,dt]`, in
strict alternation. The net update is

```
   U^{n+1}_i = U^n_i − (Δt/2|S_i|) Σ_T [ φ_i(W^n) + φ_i(W^n + Δt ∂_t W) ]
```

This is precisely `eq:RD_RK2_N_Heun` — **the N-scheme special case, applied to
all three schemes**. Concretely, the code contains:

- no `U*` (only a Taylor extrapolation `W*` of the primitive variables);
- no temporal defect term `Σ_j m_ij (U*_j − U^n_j)/Δt`;
- no total residual `Φ_i^T`, only the spatial residual `φ_i^T`;
- no mass matrix at all.

> The one scheme for which the implemented form is correct, N, is the one scheme
> that does not benefit from the second-order machinery.

### Why LDA degrades to first order under advection

Substituting the exact solution into the lumped semi-discrete scheme
`|S_i| dU_i/dt + Σ_{T∋i} β_i^T φ^T = 0`, using
`φ^T ≈ |T|(∇·F)|_T` and the PDE `∇·F = −∂_t U`:

```
   |S_i| ∂_t U|_i + Σ_T β_i^T |T| (∇·F)|_T
 ≈ [ |S_i| − Σ_T β_i^T |T| ] ∂_t U|_i
 = Σ_{T∋i} ( 1/3 − β_i^T ) |T| · ∂_t U|_i          since |S_i| = Σ_{T∋i}|T|/3
```

This vanishes if and only if `β_i^T = 1/3` (the centred scheme, which is not
upwind and is unstable) or `∂_t U = 0` (steady). The mechanism is therefore:

> **the temporal term is distributed with weight `1/3`, the spatial term with
> weight `β_i`. The mismatch is the entire defect.**

The consistent mass matrix removes it exactly: with
`m_ij = (|T|/3)β_i` the temporal term becomes `β_i^T |T| ∂_t U|_T`, matching
the spatial weighting, and the two combine into
`Σ_T β_i^T |T| [∂_t U + ∇·F] = 0`.

This accounts quantitatively for the measured convergence table (Codex,
campaigns `nodal_v1_dth` and `glass_v2_nodal_dth`):

| observation | explained by |
| --- | --- |
| LDA boost 0 → 1.95 / 1.97 | `∂_t U = 0`, mismatch term vanishes |
| LDA boost 1 → 0.94 / 0.95 | `β^LDA ≠ 1/3`, mismatch survives |
| N unchanged at ≈ 1 | N is not LP anyway; the extra term does not change its order |
| B follows LDA | B contains the LDA branch |
| both mesh families agree | the mismatch depends on `β`, not on mesh regularity |
| stationary velocity ≈ 1.7 while density/pressure ≈ 2.0 | **not explained; still open** |

---

## 3. Index verification: the thesis versus Ben Morton's code

`/home/zwu/rdsolver/rd` implements the thesis scheme, and was checked because it
is the natural thing to port. Index conventions in `triangle2D.h`:
`BETA[i][j][m]` has `i, j` variable indices and `m` the vertex index, confirmed
by `FLUC_LDA[i][m] = Σ_j BETA[i][j][m] PHI[j] = (β_m Φ)_i`.

**N scheme (`triangle2D.h:905-916`) — matches the thesis.**

```c
AREA_DIFF[i][m]     = AREA*(U_HALF[i][m] - U_N[i][m])/3.0;   // (|T|/3) ΔU_m, diagonal
SECOND_FLUC_N[i][m] = AREA_DIFF[i][m]/DT + 0.5*(FLUC_N[i][m] + FLUC_HALF_N[i][m]);
```

**LDA scheme (`triangle2D.h:803-859`) — does not match.**

```c
MASS[i][j][m]         = AREA * BETA[i][j][m]/3.0;            // (|T|/3)(β_m)_ij
MASS_DIFF[i][m]       = Σ_j MASS[i][j][m] * DIFF[j][m];      // (|T|/3) β_m ΔU_m, same vertex
SUM_MASS[i]           = Σ_m MASS_DIFF[i][m]/DT;              // sum over vertices, 4-vector
SECOND_FLUC_LDA[i][m] = SUM_MASS[i] + 0.5*(...);             // broadcast to all three vertices
```

The implied mass matrix is `m_{i,j} = (|T|/3) β_j`, indexed by the **source**
vertex, whereas the thesis has `m_{i,j} = (|T|/3) β_i`, indexed by the
**target**. The conservation condition then fails:

```
   thesis:  Σ_i m_ij = (|T|/3) Σ_i β_i = (|T|/3) I     OK
   Ben:     Σ_i m_ij = 3 · (|T|/3) β_j = |T| β_j       not (|T|/3) I
```

Numerical check with genuine LDA matrices from a real element
(`‖Σ_m β_m − I‖ = 6.6e-15`), random per-vertex `ΔU`:

| form | `Σ_i Φ_i` temporal part | defect against `Φ^T` |
| --- | --- | --- |
| thesis `m_ij = (\|T\|/3)β_i` | `[-0.01374, -0.01278, 0.01629, 0.01348]` | `1.8e-16` |
| Ben, `SUM_MASS` broadcast | `[-0.02596, -0.01215, 0.00093, -0.03302]` | `4.65e-02` |
| required `(\|T\|/3) Σ_j ΔU_j` | `[-0.01374, -0.01278, 0.01629, 0.01348]` | — |

Relative size of the defect is about 285 per cent. With `ΔU` uniform over the
element the defect drops to `6.5e-16`, i.e. Ben's form is correct to `O(h)`.

**Consequence for this project: implement the thesis form; do not port the LDA
branch of the standalone code.**

A further observation, recorded because it bears on how to read the historical
results but which is a matter for Zhenyu to judge. Ben's temporal contribution
is identical for the three vertices, i.e. distributed as `1/3` each. By the
argument of section 2 his LDA therefore carries the same `1/3` versus `β`
mismatch, and would also be first order for advected problems. That is
consistent with the previously recorded convergence orders having been measured
on the *stationary* Yee vortex.

---

## 4. An algebraic simplification worth having

`Σ_T φ_i^{n,T}` appears in the corrector and looks as though it must be stored
per element from stage 1. It need not be. From the predictor definition,

```
   Σ_{T∋i} φ_i^{n,T} = − |S_i| (U*_i − U^n_i) / Δt
   ⟹  −(Δt/2|S_i|) Σ_T φ_i^{n,T} = + ½ (U*_i − U^n_i)
```

so the corrector becomes

```
┌──────────────────────────────────────────────────────────────────────────┐
│ U^{n+1}_i = U*_i + ½(U*_i − U^n_i)                                       │
│             − (Δt/|S_i|) Σ_T [ Σ_j m_ij (U*_j − U^n_j)/Δt + ½ φ_i^T(U*) ]│
└──────────────────────────────────────────────────────────────────────────┘
```

Stage 2 then needs **one** residual sweep, evaluated at `U*`, and no per-element
storage. The only new persistent data is `U^n_i` per vertex, four doubles, which
the mass-matrix term requires anyway. Ghost vertices need `U^n_j` (equivalently
`ΔU_j`) exchanged, which is one new field in the primitive exchange.

---

## 5. Restructuring the main loop

Between the two call sites `run.c` performs: `find_next_sync_point()` (time
advance), `make_list_of_active_particles()`, conditionally a domain
decomposition and mesh rebuild, and `exchange_primitive_variables_and_gradients()`.
Under the present `VORONOI_STATIC_MESH` + `FORCE_EQUAL_TIMESTEPS` guards the
mesh and the active set do not change, so only the time advance and the exchange
actually occur.

### Option A — both stages inside one call

```
compute_residuals():
    save U^n
    sweep 1 → distribute → apply_FluxRD_list       ⟹ U*
    local primitive recovery
    exchange primitives and ΔU
    sweep 2 → assemble Φ_i^T → distribute → apply_FluxRD_list   ⟹ U^{n+1}
```

- Mathematically clean; nothing can occur between the stages.
- The only structure compatible with a moving mesh, where a rebuild between the
  stages would leave predictor and corrector on different element sets.
- Removes the need for `calculate_gradients()` on the RD path: the RD predictor
  is an RD update, and the `P1` element representation is the reconstruction.
- Costs: the second call site must become a no-op without disturbing
  `find_next_sync_point()`; an in-solver primitive recovery overwrites
  `TimeLastPrimUpdate`, though that variable becomes unnecessary once the Taylor
  extrapolation is gone.

### Option B — stage 1 in call 1, stage 2 in call 2

- Smallest change, maps onto AREPO's existing placement, reuses the exchange at
  `run.c:321`.
- Needs an extra `update_primitive_variables()` before that exchange, because
  after stage 1 the conserved variables hold `U*` while the primitives are still
  `W^n`.
- Correctness rests on the implicit premise that nothing happens between the two
  calls. That premise is currently maintained by the compile-time guards, not by
  the code structure, and it fails as soon as the mesh moves.

### Option C — keep the present structure, add only the mass-matrix term

Rejected. The term `Σ_j m_ij (U*_j − U^n_j)/Δt` requires `U*` to be the RD
predictor. Substituting the existing Taylor extrapolation of the primitives
yields neither the thesis scheme nor any other known second-order scheme.

### Option D — space-time RD

Out of scope by the stated constraint. Recorded only so that the reason is on
the record: it would make varying `Δt` and mesh motion natural, at the cost of
replacing rather than reusing AREPO's mesh and timestep machinery.

---

## 6. Hierarchical timesteps: a provable tension

The consistent mass matrix makes the update **non-local within the element**:

```
   Φ_i^T = (|T|/3) β_i · Σ_{j∈T} (U*_j − U^n_j)/Δt + ½[φ_i^n + φ_i^*]
                          └──────── all vertices of T ────────┘
```

With the lumped mass, `Σ_j m_ij ΔU_j = (|T|/3) ΔU_i` and only the vertex's own
increment is needed. This is exactly the locality that a timebin hierarchy
relies on.

### The tension is not an implementation difficulty

> **Claim.** If `m_ij^T` satisfies local conservation
> `Σ_{i∈T} m_ij^T = (|T|/(d+1)) I` for every `j`, and is element-local,
> `m_ij^T = 0` for `i ≠ j`, then `m_ij^T = (|T|/(d+1)) δ_ij I`.
>
> **Proof.** Locality leaves a single term in the conservation sum, namely
> `i = j`, hence `m_jj^T = (|T|/(d+1)) I`. ∎

So the *only* conservative element-local mass matrix is the lumped one, and its
temporal weights are `1/(d+1)`, independent of `β`. The mismatch of section 2 is
therefore unavoidable for any conservative, element-local scheme with
`β ≠ 1/(d+1)`.

This closes off the option of looking for a modified `β̃` that would restore
consistency while keeping locality: any such `β̃` would have to satisfy the star
condition `Σ_{T∋i} β̃_i^T |T| = |S_i|`, which couples the elements around a
vertex and is therefore not element-local either.

### Practical consequences

Three concrete obstacles, beyond the structural one:

1. **Which `Δt`?** `(U*_j − U^n_j)/Δt` needs one `Δt` per element while the
   vertices may sit in different bins.
2. **`U*_j` is undefined for an inactive vertex**, since the predictor requires
   every element around `j` to have been evaluated.
3. **Setting `ΔU_j = 0` for inactive vertices is wrong**: it discards a real
   contribution and breaks conservation.

Options, given that space-time RD is excluded:

- **(a) force all vertices of an active element to be active.** The constraint
  propagates along Delaunay edges and degenerates to a global timestep. Not
  viable.
- **(b) reconstruct `ΔU_j` for inactive vertices**, e.g. by
  `(Δt_small/Δt_large) ΔU_j^{large}`. AREPO already smooths timebins between
  neighbours, and the three vertices of a Delaunay triangle are mutual
  neighbours, so within one element `Δt` differs by at most a factor of two.
  That bounds the reconstruction error. Whether second order and conservation
  survive needs derivation; this is essentially a rigorous version of Ben's
  `DRIFT` heuristic.
- **(c) mixed mass matrix.** Use the consistent mass matrix on elements whose
  vertices share a bin, and the lumped one on elements that straddle a bin
  boundary. Both are conservative, so conservation is exact everywhere; the
  scheme is second order except on the set of straddling elements, which is a
  codimension-one subset of the mesh. This reuses AREPO's timebin machinery
  unchanged and requires no new derivation to be *safe*, only to quantify the
  accuracy loss.
- **(d) global timestep for RD.** The present baseline. Correct, and severely
  expensive for the eventual galaxy-formation application.

Option (c) is the one that best fits the stated constraint and deserves the
first look.

### What the standalone code does

Ben's `timestep.cpp` offers two adaptive schemes, both **element-based**
(`RAND_MESH[j].get_tbin()`), both behind `#ifdef`, with the globally
synchronised path as the default:

- `DRIFT`: recompute the element residual every `TBIN` steps but apply the
  stored residual every step;
- `JUMP`: compute once per element cycle and apply it in one go with a scaled
  `2·DT`, `4·DT`, `8·DT`.

Neither is derived, and neither addresses the mass-matrix coupling. There is no
ready-made solution to port.

---

## 7. Moving mesh: the ALE-RD formulation

### 7.1 It is explicit Runge–Kutta, not space-time

Confirmed from Campoli, Quemar, Bonfiglioli & Ricchiuto, *Shock-fitting and
predictor-corrector explicit ALE Residual Distribution*, section 2.2, which uses
the scheme of Arpaia & Ricchiuto (`10.1007/s10915-014-9910-5`) and describes it
as a "two-step explicit Residual Distribution method". The Springer title of the
source paper is itself explicit: *An ALE Formulation for Explicit Runge–Kutta
Residual Distribution*.

**This settles the strategic question. Option A is a stepping stone, not a dead
end, and the space-time rewrite excluded by the design constraint is not needed
for a moving mesh.**

### 7.2 The equations

Euler in ALE compact form, with `J` the determinant of the Jacobian between
reference and actual frame and `σ` the local mesh deformation velocity:

```
(1)   ∂_t (J w) + J ∇·( f(w) − σ w ) = 0
```

Two-step explicit RD update, and the first-order predictor:

```
(2)   |C_i^{n+1}| w_i^{n+1} = |C_i^{n+1}| w_i^*  − Δt Σ_{K∋i} Φ_i^K(w_h^n, w_h^*)

(5)   |C_i^{n+1}| w_i^*     = |C_i^{n+1}| w_i^n  − Δt Σ_{K∋i} Φ̃_i^K(w_h^n)
```

Total element residual and the two steady residuals:

```
(3)   Φ^K  = (1/Δt) ( ∫_{K^{n+1}} w_h^*  −  ∫_{K^n} w_h^n )
             + ½ Φ^K(w_h^n) + ½ Φ^K(w_h^*)

(4)   Φ^K  = ∫_{∂K^{n+1/2}} ( f(w_h) − σ_h w_h ) · n ds

(6)   Φ̃^K = ∫_{∂K^{n+1/2}} f(w_h) · n ds  −  ∫_{K^{n+1/2}} σ_h · ∇w_h dx
```

Nodal split with the mass matrix:

```
(8)   Φ_i^K = Σ_{j∈K} [ m_ij^{K^{n+1}} w_j^*  −  m_ij^{K^n} w_j^n ] / Δt
              + ½ Φ_i^K(w_h^n) + ½ Φ_i^K(w_h^*)
```

with the `β_j` "uniformly bounded w.r.t. the cell residuals" and the `m_ij^K`
"mass matrix entries **consistent with the definition of the spatial
distribution**". The paper states that these definitions give a scheme "formally
second order accurate in space and time, fully conservative, and verifying the
DGCL".

Discrete geometric conservation law, satisfied by evaluating essentially all
geometric quantities on the **half-time averaged configuration** `K^{n+1/2}`:

```
(7)   |K^{n+1}| − |K^n| = Δt ∫_{∂K^{n+1/2}} σ_h · n ds
```

### 7.3 Why this is favourable for AREPO-RD

**The static-mesh scheme is the special case, not throwaway work.** Comparing
the temporal terms:

```
   thesis, static mesh :  Σ_j m_ij ( w_j^* − w_j^n ) / Δt
   ALE                 :  Σ_j [ m_ij^{K^{n+1}} w_j^* − m_ij^{K^n} w_j^n ] / Δt
```

When the mesh does not move, `m^{K^{n+1}} = m^{K^n}` and the second reduces to
the first. Implementing the thesis form now is therefore the first half of the
ALE implementation, not a detour.

**The `|C_i| w_i` bookkeeping already matches AREPO.** Equation (2) updates the
product of control volume and state, and AREPO already evolves `P[i].Mass`,
`SphP[i].Momentum` and `SphP[i].Energy` and recovers `Density = Mass/DualArea`.
The current code is already using the right variables; what is missing is that
the control volume is not updated in time.

**The DGCL prescription is cheap.** The half-time configuration is obtained from
averaged vertex positions, `x^{n+1/2} = (x^n + x^{n+1})/2`, with normals and
areas evaluated there. No additional mesh construction is required, only
geometry evaluated at averaged coordinates. AREPO's drift already provides
`x^n` and `x^{n+1}`.

**The mesh-motion term is already present in the K matrices.**
`residual_distribution_solver.c` builds the eigenvalues as
`u·n̂ ± c − v_mesh·n̂` from `Velvertex_avg`, which is the `−σ w` contribution of
equation (1) at the level of the flux Jacobian. What is missing is the geometry,
not the wave speeds.

### 7.4 What must not be overlooked

- **The predictor and the corrector use different steady residuals.** `Φ̃` in
  (6) is described as *geometrically non-conservative* and differs from `Φ` in
  (4) by the GCL term. Using the same routine for both stages would be wrong
  under mesh motion, though it is harmless while `σ = 0`.
- **`|C_i|` is taken at `n+1` on both sides of (2) and (5).** The control volume
  used to divide is the new one, not the old one and not an average.
- **The element integrals in (3) are over `K^{n+1}` and `K^n` separately**, not
  over a single configuration. This is what makes the temporal term consistent
  with the DGCL.

### 7.5 Structural consequence for the main loop

Option B is not a route to a moving mesh. AREPO rebuilds the mesh between the
two call sites, so predictor and corrector would see different element sets. The
ALE scheme moreover needs `K^n`, `K^{n+1/2}` and `K^{n+1}` available within a
single evaluation, which cannot be arranged across two call sites separated by a
mesh rebuild. **If ALE is a firm goal, restructure the main loop once, to option
A.**

Note also that under ALE the stagnation degeneracy of `S^-` becomes generic
rather than exceptional: the degeneracy condition is `u_n = v_n`, which is the
normal state of a Lagrangian mesh. The direct-solve work already committed in
`07f264a` is a prerequisite for moving mesh, not only a fix for quiet regions.

### 7.6 The gap the literature does not close

The CFD residual-distribution literature solves the moving-mesh problem and does
**not** address hierarchical time stepping. Arpaia & Ricchiuto, and the
shock-fitting work built on it, all use a single global `Δt`. Local time
stepping is an astrophysics requirement that arises from the dynamic range of
galaxy formation, and it has no counterpart in the applications these schemes
were developed for.

Consequently:

- for the moving mesh there is a derived, published formulation to follow;
- for hierarchical time steps there is **no reference solution to port**, and
  section 6 shows the obstruction is structural rather than incidental.

These two goals should therefore be treated differently. ALE is an
implementation task against a known target. Hierarchical time stepping is a
research question, and the mixed mass matrix of section 6 is a pragmatic
compromise rather than a known-correct scheme.

---

## 8. Where this leaves us

Established:

1. The code implements the N-scheme special case for all three schemes; the
   total residual, the mass matrix and the RD predictor are all absent.
2. The `1/3` versus `β` mismatch accounts quantitatively for the measured
   stationary-to-advected order transition.
3. The thesis indexing is correct; the standalone code's LDA branch is not, and
   should not be ported.
4. Any conservative, element-local mass matrix is the lumped one. Locality and
   `β`-weighted temporal distribution are mutually exclusive.
5. ALE-RD is an explicit two-step Runge–Kutta method, not a space-time
   discretisation. The static-mesh scheme is its `σ = 0` special case, so
   implementing the thesis form now is the first half of the ALE work.
6. Only option A survives if the moving mesh is a firm goal, both because AREPO
   rebuilds the mesh between the two call sites and because ALE needs `K^n`,
   `K^{n+1/2}` and `K^{n+1}` within one evaluation.
7. The two remaining goals are of different kinds. Moving mesh is an
   implementation task against a published formulation. Hierarchical time
   stepping has no counterpart in the CFD literature, which uses a single global
   `Δt` throughout, and section 6 shows the obstruction is structural.

Open, in the order they need deciding:

- whether the accuracy loss of option (c), the mixed mass matrix, is acceptable;
  this needs a quantitative estimate, not only the observation that it is
  conservative. This is the one genuinely open research question of the three.
- the unexplained stationary velocity order of about 1.7 against 2.0 for
  density, pressure and internal energy. This should be understood before the
  boosted numbers carry full weight.
- how to treat the predictor: the thesis's RD predictor removes the dependence
  on AREPO's least-squares gradients entirely, which is a simplification, but it
  changes the scheme's behaviour near discontinuities where those gradients are
  currently limited.
- the explicit construction of `m_ij^K` in Arpaia & Ricchiuto. The secondary
  source states only that it is "consistent with the definition of the spatial
  distribution". For the static-mesh implementation the thesis form
  `m_ij = (|T|/3) β_i` is sufficient; the ALE extension will need the primary
  paper.

### Sources consulted

- Campoli, Quemar, Bonfiglioli & Ricchiuto, *Shock-fitting and predictor-corrector
  explicit ALE Residual Distribution*, section 2.2, equations (1)-(8):
  https://www.math.u-bordeaux.fr/~mricchiu/sf-draft.pdf
- Arpaia & Ricchiuto, *An ALE Formulation for Explicit Runge-Kutta Residual
  Distribution*, J. Sci. Comput. (2015), 10.1007/s10915-014-9910-5:
  https://link.springer.com/article/10.1007/s10915-014-9910-5
- Ricchiuto & Abgrall, *Explicit Runge-Kutta residual distribution schemes for
  time dependent problems: Second order case*, JCP 229 (2010):
  https://dl.acm.org/doi/10.1016/j.jcp.2010.04.002

---

## 9. Primary source: Arpaia & Ricchiuto (2015), exact formulation

`MyThesis/useful_resources/2015_Arpaia_An_ALE_Formulation_for_Explicit_Runge–Kutta_Residual_Distribution.pdf`,
J. Sci. Comput. 63:502-547. Section 3 supplies the definitions that section 1
above quotes from the thesis, and closes the remaining gap.

### 9.1 The mass matrix has two admissible forms

The time-dependent generalisation of RD, equation (27):

```
   Σ_{K∈D_i} Σ_{j∈K} m_ij^K du_j/dt  +  Σ_{K∈D_i} β_i^K φ^K = 0
```

with `m_ij^K = ∫_K φ_j w_i dx` and the Petrov-Galerkin test function
`w_i = φ_i + γ_i`. Equation (28) gives two choices:

```
   m_ij^{F1} = (|K|/3) β_i^K                              = |K| m̂_ij^{F1}

   m_ij^{F2} = (|K|/3) ( δ_ij/4 + β_i^K − 1/12 )          = |K| m̂_ij^{F2}
```

Both satisfy local conservation:

```
   Σ_i m_ij^{F1} = (|K|/3) Σ_i β_i             = (|K|/3) I     OK
   Σ_i m_ij^{F2} = (|K|/3) ( 1/4 + I − 3/12 )  = (|K|/3) I     OK
```

**`F1` is the thesis's choice.** `F2` is an alternative that has not been
considered here and may be worth testing later.

### 9.2 What the code currently implements has a name

Equation (29). Row-wise mass lumping of *either* formulation gives the median
dual cell `|S_i| = Σ_{K∈D_i} |K|/3` and the **Mass Lumped (ML) formulation**:

```
   |S_i| du_i/dt  +  Σ_{K∈D_i} φ_i^K = 0
```

This is exactly what `residual_distribution_solver.c` implements. The paper
introduces it as the starting point *before* the time-dependent machinery is
added.

### 9.3 Why the predictor-corrector structure exists at all

Section 3.5, quoted:

> "Due to the presence of the mass matrix, the use of the general prototype (27)
> leads inevitably to schemes requiring the solution of a **nonlinear system of
> algebraic equations**, even if explicit time integration techniques are used.
> For this reason, time dependent implementations of RD always feature some form
> of implicit time integration, or a fully coupled space-time formulation."
>
> "The explicit RK-RD formulation of [Ricchiuto & Abgrall 2010] provides one
> possible solution to this flaw, allowing **genuinely explicit time marching**."

So the two-stage structure is not merely a way of reaching second order in time.
It is the device that avoids an implicit solve while keeping the mass matrix.
This strengthens the case for option A: the two stages are meant to act
together as one algebraic object, and separating them across a mesh rebuild or a
time advance is contrary to their purpose.

### 9.4 The thesis scheme is the Global Lumping variant

Equations (49)-(53). With stage-shifted increments `Δũ^1 = 0`,
`Δũ^2 = u^1 − u^n`, and

```
   R_i^{K(k)} = Σ_{j∈K} m_ij^K (Δũ^k_j/Δt) + β_i^K φ^{K(k)}
```

the paper offers two lumping choices:

```
   (52) Selective Lumping (SL)   |S_i| Δu^k_i/Δt = − Σ_K [ R_i^{K(k)} − Σ_j m_ij^G Δũ^k_j/Δt ]
   (53) Global Lumping (GL)      |S_i| ( Δu^k_i − Δũ^k_i )/Δt = − Σ_K R_i^{K(k)}
```

Expanding GL reproduces the thesis exactly. Stage 1, with `Δũ^1 = 0`:

```
   |S_i| Δu^1_i/Δt = −Σ_K β_i φ^K(u^n)
   ⟹  u^1_i = u^n_i − (Δt/|S_i|) Σ_K φ_i^K(u^n)          = eq:RD_RK2_predictor
```

Stage 2, with `Δũ^2 = u^1 − u^n` and `φ^{K(2)} = ½[φ^K(u^n) + φ^K(u^1)]`:

```
   u^{n+1}_i = u^1_i − (Δt/|S_i|) Σ_K [ Σ_j m_ij (u^1_j − u^n_j)/Δt
                                        + ½ β_i ( φ^K(u^n) + φ^K(u^1) ) ]
                                                          = eq:RD_RK2_corrector
```

**The thesis scheme is `GL` + `F1`.** `SL`, which retains the Galerkin mass
matrix `m_ij^G` on the new-value term, is a documented alternative.

### 9.5 The blended scheme blends the mass matrices too

Equations (43)-(44):

```
   m_ij^{LDA-N} = ( 1 − l(u_h) ) m_ij^{LDA}  +  l(u_h) (|K|/3) δ_ij

   l = |Φ^K| / Σ_j |Φ_j^N|
```

with the paper stating that in the time-dependent case the blending parameter
"should now include the whole residual". So for B the *mass matrix itself* is
blended, and `Θ` must be computed from the total space-time residual, not the
spatial one. The current code blends only the spatial residuals and has no mass
matrix, so both halves of this are missing.

### 9.6 Consequences for the implementation plan

1. `m_ij = (|T|/3) β_i` is confirmed as a published, conservative choice, and is
   `F1`. The thesis indexing is right; the standalone code's LDA branch remains
   the outlier.
2. The static-mesh target is fully specified: `GL` + `F1`, equations (50)-(53)
   with `σ = 0`.
3. `F2` and `SL` are documented alternatives, available if `GL`+`F1` proves
   unsatisfactory.
4. For the B scheme, blending the mass matrix and using the total residual in
   `Θ` are part of the specification, not refinements.
5. The predictor-corrector exists to avoid an implicit solve. Any restructuring
   that separates the stages works against the reason the scheme has that shape.

---

## 10. Proposed implementation: static-mesh `GL + F1`, option A

Concrete change list for review by Codex and Kimi. Target is the scheme
established in sections 1 and 9: **Global Lumping with the `F1` mass matrix,
`σ = 0`**. Everything is behind one compile switch so the current lumped path
stays reproducible.

### 10.1 Switch and scope

```
RD_RK2_TOTAL_RESIDUAL     new Config option, registered in Template-Config.sh
```

Off: current behaviour, bit-identical. On: the scheme below. Both must build.
The existing lumped campaigns and artifacts remain the comparison baseline and
must not be regenerated.

`RD_RK2_TOTAL_RESIDUAL` implies the option-A main loop; it is not compatible
with the current two-half-step placement, so the two are mutually exclusive by
construction rather than by convention.

### 10.2 Main loop, `src/main/run.c`

```
:229   compute_residuals(&Mesh)          →  becomes a no-op under the switch
:324   compute_residuals(&Mesh)          →  performs the complete RK2 step
```

The whole step is applied at the second site, where `All.Time = t^{n+1}` and
`update_primitive_variables()` follows immediately at `:329`. Nothing else in
`run.c` moves. Rationale for choosing the second site rather than the first:
the primitive recovery that must follow the corrector is already there.

Point to confirm during review: that `find_next_sync_point()` and the timebin
bookkeeping are indifferent to which of the two sites does the work, given
`FORCE_EQUAL_TIMESTEPS`.

### 10.3 Solver restructuring, `residual_distribution_solver.c`

`compute_residuals()` currently runs 507-1275 as a single function that
classifies elements, computes geometry, sweeps residuals, and exports. Split it:

```
rd_build_element_set(T, ...)        element classification, ownership, dedup,
                                    triangle_get_normals_area  — runs ONCE per step,
                                    result reused by both stages
rd_residual_sweep(T, set, stage)    the existing per-element body: Roe average,
                                    K matrices, Phi, solve, distribution
rd_apply_and_exchange(...)          existing FluxRD_list build + apply_FluxRD_list
```

The element set, normals and areas are identical in both stages on a static
mesh, so building them once removes a duplicated classification, an extra
`reset_dualarea()` and its MPI collective. This is a net simplification even
before the new scheme is switched on.

`rd_residual_sweep` needs a stage argument because stage 1 evaluates `φ^K(U^n)`
and stage 2 evaluates `φ^K(U*)` and additionally assembles the mass-matrix term.

### 10.4 New data

Per local gas cell, four doubles holding `U^n`:

```
   SphP[i].RD_Un[4]        mass, momentum x, momentum y, energy at t^n
```

Nothing else is needed: by section 4, `Σ_T φ_i^{n,T} = −|S_i|(U*_i − U^n_i)/Δt`,
so the stage-1 nodal residual is recoverable from `U^n` and the current state
and does not have to be stored per element.

For ghost vertices, one new block in `struct primexch`, alongside the existing
`#ifdef RESIDUAL_DISTRIBUTION` entry for `Energy`:

```
   MyFloat RD_dU[4];       U*_j − U^n_j for the mass-matrix term
```

`mesh.h:124-126` already establishes the pattern for RD-only fields.

### 10.5 Sequence inside the single call

```
 1  rd_build_element_set(T)                          once; also fills DualArea
 2  save SphP[i].RD_Un from the current conserved state
 3  rd_residual_sweep(stage = PREDICTOR)             φ_i^K(U^n), distributed with β_i
 4  rd_apply_and_exchange()                          ⟹ conserved variables now hold U*
 5  update_primitive_variables()                     local; recover W* from U*
 6  exchange_primitive_variables()  + RD_dU          ghosts get W* and ΔU
 7  rd_residual_sweep(stage = CORRECTOR)             φ_i^K(U*) and Σ_j m_ij ΔU_j/Δt
 8  rd_apply_and_exchange()                          ⟹ U^{n+1}
```

Step 5 must not stamp `TimeLastPrimUpdate`, or must be made to stamp it
harmlessly: under this scheme the Taylor extrapolation is gone and
`dt_Extrapolation` is unused, so the cleanest resolution is to drop the
extrapolation call from the RD path entirely under the switch.

MPI cost per step: two flux exchanges and one primitive exchange, against two
flux exchanges and two primitive exchanges now. Not a regression.

### 10.6 Corrector arithmetic

Using the section 4 identity, stage 2 computes per element

```
   T_i   = (|T|/3) β_i^{LDA} Σ_{j∈T} ΔU_j / Δt              F1 mass matrix
   Φ_i^T = T_i + ½ φ_i^T(U*)                                 φ^n folded in below
```

and the nodal update is

```
   U^{n+1}_i = U*_i + ½ ΔU*_i − (Δt/|S_i|) Σ_T Φ_i^T
```

where `ΔU*_i = U*_i − U^n_i` is available locally. `β_i^{LDA}` is already
computed in the existing LDA branch as `−K_i^+ (S^-)^†`; the new work is one
`4×4` times `4` product per vertex.

For N, `m_ij = (|T|/3) δ_ij` and the same expression reduces to the existing
Heun form, which is a useful internal check: **with the switch on, the N scheme
must reproduce the switch-off result to round-off.** That is the cheapest
possible regression test of the new machinery and should be the first thing run.

For B, section 9.5 requires blending the mass matrices and computing `Θ` from
the total residual. Proposed staging: implement LDA and N first, leave B on the
lumped path initially, and add the blended mass matrix as a second step.

### 10.7 What must be preserved

- assertions A1, A2, A3 and the `RD-DIAG` instrumentation, with A2 extended to
  the total residual `Σ_i Φ_i^T = Φ^T`;
- the direct solve and rank policy of `e95dc5d`, untouched;
- the uniform static medium floor test, which must still pass exactly: with
  `U* = U^n` the mass-matrix term vanishes identically and the scheme must
  reduce to doing nothing;
- rank invariance at 1 / 4 / 16 ranks.

### 10.8 Test sequence

```
 1  N scheme, switch on vs off                 must agree to round-off
 2  uniform static medium floor test           must still be exact
 3  rank invariance 1/4/16                     unchanged tolerances
 4  advected Yee ladder, LDA, boosts 0 and 1   the decisive measurement
 5  stationary Yee ladder                      must not regress from ~1.95
```

Item 4 is the point of the exercise: **boosted LDA should recover approximately
second order.** If it does not, the mass matrix is not the whole story and the
predictor/extrapolation must be examined next, as recorded in the earlier
review.

Item 1 deserves emphasis because it tests the new code path against an
independent implementation of the same mathematics, using only the fact that
`GL + m^N` collapses to Heun.

### 10.9 Deliberately out of scope for this change

- ALE geometry: `|T|(t)`, `|S_i|(t)`, the half-time configuration `K^{n+1/2}`,
  and the distinction between `Φ̃` and `Φ`. Section 7 is the specification when
  that work starts.
- Hierarchical timesteps. The switch requires `FORCE_EQUAL_TIMESTEPS`, as the
  current baseline already does. Section 6 is the standing analysis.
- `F2` and Selective Lumping. Documented alternatives, not first choices.

### 10.10 Open questions for the reviewers

1. Is moving the entire step to the second call site acceptable, or is there a
   reason internal to AREPO's timebin bookkeeping to prefer the first?
2. Is adding `SphP[i].RD_Un[4]` and `primexch.RD_dU[4]` the right way to carry
   the new state, or is there an existing mechanism that should be reused?
3. Does `update_primitive_variables()` have side effects beyond
   `TimeLastPrimUpdate` that make it unsafe to call from inside the solver?
4. Should the element-set refactor of 10.3 be a separate, earlier commit? It is
   a simplification of the current code independent of the new scheme, and
   separating it would keep the scheme commit smaller.

## 11. Codex audit: implementation gates and corrections to section 10

- Authors: `Zhenyu Wu and Codex (gpt-5.6-sol high)`
- Audit recorded: 2026-07-29 17:42:56 BST (+0100).
- Scope: sections 1--10 of this document, Kimi's decision response in the
  development log, the current `run.c`, `residual_distribution_solver.c`,
  `update_primitive_variables.c`, the AREPO timebin logic, and the
  Arpaia--Ricchiuto (2015) primary-source formulation.

### 11.1 Overall verdict

The central diagnosis and the static-mesh target are accepted:

- the current AREPO-RD path is a Heun-like pair of spatial-residual updates
  whose intermediate state comes from AREPO's MUSCL--Hancock/Taylor
  extrapolation;
- it does not assemble the time-dependent RD **total residual**, because the
  temporal defect and the RD mass matrix are absent;
- this explains why the stationary LDA result can appear second order while
  the boosted result falls to approximately first order;
- synchronized static-mesh `GL + F1` is the correct first implementation
  target, and it must be established before ALE or hierarchical timesteps are
  attempted.

Kimi's following amendments are also accepted:

1. N with the new RD predictor need not agree with the current
   Taylor-predictor path to round-off. At a fixed physical end time their
   difference should converge at the expected truncation order in a
   controlled `dt` ladder.
2. The F1 temporal contribution can reuse the current upwind-system solve by
   adding a third right-hand side. This is preferable to materialising a
   `beta` tensor and preserves the existing rank policy.
3. Predictor density and pressure must be monitored.
4. Under the initial equal-timestep restrictions, placing the complete
   predictor/corrector in the unconditional second call site removes the
   current restart asymmetry.

The plan is therefore approved in direction, but it is **not ready to
implement literally as section 10 is currently written**. The binding
corrections below supersede conflicting statements in sections 10.3--10.8 and
in Kimi's response.

### 11.2 P0: distinguish nodal state `U` from integrated conserved state `Q`

The proposed field

```
SphP[i].RD_Un[4] = {mass, momentum x, momentum y, energy}
```

is dimensionally ambiguous. AREPO stores the integrated control-volume
quantities

```
Q_i = {M_i, P_x,i, P_y,i, E_i} = |S_i| U_i,
```

whereas the F1 mass matrix multiplies the increment of the intensive nodal
Euler state

```
U_i = {rho_i, rho_i v_x,i, rho_i v_y,i, rho_i e_i}.
```

For the first static-mesh implementation, either:

- store `RD_Ustage0[4]` and later `RD_dUstate[4]` explicitly as nodal states;
  or
- store `Q^n`, `Q*` and the associated dual areas, then perform the explicit
  conversion `U = Q / DualArea` before assembling the temporal residual.

The first option is clearer and is recommended. Field names and comments
must state their units and whether they are intensive or integrated. The
ghost exchange must carry `Delta U`, not an undocumented `Delta Q`.

This distinction becomes essential for ALE. On a moving mesh,
`Q*/|S^{n+1}| - Q^n/|S^n|` cannot be replaced by
`(Q* - Q^n)/|S|`, and the element time term uses old/new geometric mass
matrices. A static shortcut must not be embedded in an API intended for the
later ALE path.

### 11.3 P0: use side-effect-free intermediate primitive recovery

Section 10.5 step 5 must not call the generic
`update_primitive_variables()` unchanged. That routine does more than
convert conserved variables to primitives:

- it stamps `OldMass` and `TimeLastPrimUpdate`;
- `update_internal_energy()` may impose a floor and rewrite the conserved
  energy and `EgyInjection`;
- validity handling is designed for a completed AREPO step, not for a
  mathematical RK stage.

Changing `Q*` during primitive recovery would mean that the corrector no
longer uses the predictor defined by the RD equations. It could also hide
the exact positivity failure that must be diagnosed.

Add a dedicated routine such as

```
rd_recover_stage_primitives()
```

with the following contract:

- recover `rho`, velocity, pressure/internal energy and sound speed needed by
  the corrector;
- perform no MPI collective, time stamping, accounting, floor injection or
  mutation of the conserved stage;
- check every recovered quantity for finiteness;
- record global/local minima of predictor `rho` and `p`;
- terminate diagnostically on non-positive predictor `rho` or `p` in the
  initial LDA/N implementation.

Positivity limiting for the later B predictor must be designed as part of the
scheme; the normal AREPO energy floor is not a substitute for it.

### 11.4 P0: use the full step, once

The current code multiplies the triangle timestep by `0.5` because
`compute_residuals()` is called twice. In option A, predictor and corrector
belong to one GL step and both use the same **full** `Delta t`.

The new path must therefore remove the hidden half-step convention. Use an
explicitly named `stage_dt`/`full_dt`, pass it into both sweeps and assert that
the old `*= 0.5` path is unreachable under `RD_RK2_TOTAL_RESIDUAL`.

### 11.5 Preserve two different element sets

The element-set refactor remains a good separate first commit, but it must not
collapse two concepts:

1. the complete set of physical Delaunay elements required to construct
   `DualArea` and geometry; and
2. the subset of elements whose residual is advanced on the current active
   step and whose MPI ownership has been assigned.

These sets coincide in much of the initial static,
`FORCE_EQUAL_TIMESTEPS` configuration, but they will not coincide under
hierarchical activation. The refactored data structure should retain the
full physical set plus an active/owned mask or active index list. Otherwise a
performance refactor made now would silently build the wrong dual volume for
the later timebin extension.

### 11.6 The ALE extension has a topology problem in addition to geometry

Option A is a useful control-flow foundation, but it is not by itself an ALE
implementation. ALE GL+F1 needs at least:

- the old, half-time and new element configurations;
- the corresponding geometric/mass terms and a discrete geometric
  conservation-law check;
- a defined relation between the stage states and the moving dual volumes.

AREPO may rebuild the Delaunay triangulation and change connectivity between
the two configurations. The cited ALE-RD derivation treats a continuously
deforming element; it does not automatically prescribe what to do when an
edge flips or an element disappears. Before the ALE coding phase, the design
must choose and test one of:

- retaining old connectivity through the RK step;
- constructing a conservative correspondence/remap between old and new
  elements; or
- constraining topology changes during the stage and rebuilding afterwards.

This is an explicit research/design gate, not an implementation detail.

### 11.7 Hierarchical timesteps remain an unproven research extension

The mixed-mass proposal is a useful hypothesis for a falsification
experiment, not yet an approved algorithm. In particular:

- no checked code path currently guarantees that all adjacent Delaunay
  vertices differ by at most a factor of two in timebin;
- the claim that the straddling region is always a one-element-thick boundary
  layer has not been established;
- elementwise conservative distributions do not by themselves prove global
  conservation when vertices are updated asynchronously;
- an inactive vertex has no naturally defined RD predictor `U*`, even though
  the current exported residual mechanism may change its integrated
  conserved quantities.

Before selecting an asynchronous algorithm, instrument representative runs
to measure neighbour-bin ratios, the fraction and location of straddling
elements, inactive-vertex updates, and the conservation balance per sync
point. The proposed two-zone, factor-two Yee experiment should then decide
whether mixed mass is viable. A subcycling or flux/residual-register
formulation remains an alternative if it is not.

### 11.8 MPI ownership and main-loop scope

The current MPI rule should not be described as the proposed
minimum-active-ID rule. The code currently combines local active-vertex
selection with a majority-rank responsibility decision. Its coverage and
uniqueness have not been proved for partial activation and must be redesigned
before hierarchical timebins.

For the initial total-residual implementation, retain strict compile-time or
startup guards for:

- static mesh;
- `FORCE_EQUAL_TIMESTEPS`;
- the supported non-cosmological mode;
- no refinement or derefinement during the hydro step.

Using the second call site is accepted within this scope. With refinement
enabled, moving the whole update there changes the ordering between hydro,
mesh reconstruction and refinement operations, so that configuration must
remain unsupported until explicitly analysed.

### 11.9 Wording correction for the mismatch argument

The elementwise defect

```
sum_T (1/3 - beta_i^T) |T| d_t U
```

generically disappears when `beta_i^T = 1/3` or for a steady state. These are
sufficient elementwise conditions, but not a strict global “if and only if”:
special solutions or patchwise cancellations can also make the assembled
defect vanish. This wording correction does not change the diagnosis from
the two independent Yee mesh families.

### 11.10 Revised implementation and verification order

1. Amend the design and data contract as above: `U` versus `Q`, full
   `Delta t`, stage recovery without side effects, and strict supported-mode
   guards.
2. Commit the element-set refactor separately, preserving the complete
   physical set and a distinct active/owned subset.
3. Implement static, equal-timestep LDA and N `GL + F1` behind
   `RD_RK2_TOTAL_RESIDUAL`; use the third-right-hand-side solve for F1.
4. Add small algebraic tests:
   - single-triangle total-residual conservation;
   - explicit dual-area/unit scaling;
   - random `Delta U_j` comparison against the row-indexed F1 formula;
   - uniform-state exact preservation.
5. Compare N old/new paths over a fixed-grid `dt` ladder at a fixed physical
   end time. Expect truncation-order convergence, not round-off agreement.
6. Repeat 1/4/16-rank invariance and monitor predictor minimum density and
   pressure.
7. Re-run stationary and boosted Yee ladders on both formal mesh families.
   The decisive target is recovery of approximately second-order boosted LDA
   without degrading stationary LDA.
8. If the target is missed, separate temporal-mass, predictor and spatial
   residual effects before changing the formulation again.
9. Implement B only with its blended mass matrix and total-residual `Theta`
   treated consistently; do not combine a new spatial blend with the old
   lumped time term.
10. Start ALE and hierarchical-timebin work only after this synchronized
    baseline is established. Handle ALE topology/DGCL and asynchronous
    ownership/coverage as separate design problems.

This ordering keeps the immediate experiment small and falsifiable while
leaving the necessary interfaces explicit for moving meshes, MPI ownership
and hierarchical timebins.

---

## 12. Response to the Codex and Kimi reviews, and a literature check

- Author: `Claude Code Opus5`
- Responds to section 11 (Codex) and the Kimi decision entry in the development
  log.

### 12.1 Corrections accepted

All of the following are accepted; sections 10.3-10.8 are superseded by section
11.10 where they conflict.

| section 10 said | correction | raised by |
| --- | --- | --- |
| N on/off must agree to round-off | wrong: the baseline uses the Taylor predictor, the new path the RD predictor; the difference is truncation-level `O(dt^2)` | Kimi |
| "`beta_i` is already computed" | wrong: my own earlier change removed the `BetaLDA` tensor; the code forms `phi_i = -K_i^+ x` directly | Kimi |
| `RD_Un[4] = {mass, momentum, energy}` | dimensionally wrong: that is the integrated `Q = \|S_i\| U`, while `F1` multiplies the intensive nodal `U` | Codex |
| `update_primitive_variables()` may be called mid-solver | wrong, see 12.2 | Codex |
| (silent on `dt`) | omission: both stages use the **full** `Delta t`; the existing `triangle_dt *= 0.5` must be unreachable under the switch | Codex |
| build the element set once | incomplete: the complete physical set and the active/owned subset must stay distinct | Codex |
| "vanishes if and only if" | too strong: sufficient elementwise conditions, not a global equivalence | Codex |
| "AREPO already smooths timebins between neighbours" | **wrong, verified**: the public version has no neighbour timebin constraint. Only `FORCE_EQUAL_TIMESTEPS` and `TREE_BASED_TIMESTEPS` exist, and the latter is a signal-speed criterion that does not bound the ratio | Codex |

The last one matters beyond bookkeeping: the factor-of-two bound was the *only*
argument bounding the reconstruction error in the mixed-mass-matrix proposal of
section 6. That proposal now rests on nothing until the bin-ratio distribution
is measured, exactly as section 11.7 requires.

### 12.2 The one point where the reviews disagree

Codex says `update_primitive_variables()` is unsafe to call between stages;
Kimi read it as safe. **Codex is right**, and the evidence is
`update_primitive_variables.c:269-293`:

```c
   ulimit = All.MinEgySpec;
   if(localSphP[i].Utherm < ulimit) {
       EgyInjection -= localSphP[i].Energy;
       localSphP[i].Utherm = ulimit;
       localSphP[i].Energy = ...;          /* rewrites the conserved energy */
       EgyInjection += localSphP[i].Energy;
   }
```

When the floor triggers it **mutates `Q*`**, so the corrector would no longer
use the predictor defined by the RD equations, and it corrupts the global
`EgyInjection` accumulator with a stage quantity.

Worth stating explicitly: the current test problems run `MinEgySpec = 0`, so the
floor never fires and calling the routine would appear to work. It would pass
every test now in the suite and fail silently, in cold regions only, once a
floor is enabled for a production run. A dedicated side-effect-free
`rd_recover_stage_primitives()` is the right answer.

### 12.3 A P0 neither review raised: `F1` is undefined where `S^-` is singular

Kimi's `nrhs = 3` route is the right implementation technique and should be
adopted. Since `beta_i = -K_i^+ (S^-)^{-1}` only ever multiplies a vector,

```
   T_i = (|T|/3) beta_i v = -K_i^+ z ,     S^- z = (|T|/3) v ,   v = sum_j dU_j/dt
```

so a third right-hand side replaces the `beta` tensor entirely, inherits the
rank policy, and costs one extra back-substitution.

**But the conservation argument has a gap.** `sum_i T_i = -S^+ z = S^- z` equals
the target only if the solve is *exact*, which requires the target to lie in
`range(S^-)`. The three right-hand sides are not equally protected:

```
   rhs 0 = phi^T                   in range(S^-)     Lemma 1
   rhs 1 = sum_m K_m^- Uhat_m      in range(S^-)     rank-1 structure at stagnation
   rhs 2 = (|T|/3) sum_j dU_j/dt   NOT protected
```

Measured on one element with random per-vertex `dU`:

| state | `rank(S^-)` | `‖S z − target‖/‖target‖` | `sum_i T_i` defect |
| --- | --- | --- | --- |
| `u = 0.55` subsonic | 4 | `1.4e-15` | `9.6e-15` |
| `u = 0` stagnant | 3 | `4.7e-01` | **`5.9e-01`** |

The root cause is deeper than the solve method: **`beta_i` itself is undefined
where `S^-` is singular.** Lemma 2 guarantees only that `beta_i phi^T` is well
defined, because `phi^T` lies in the range; it says nothing about `beta_i`
applied to an arbitrary vector, and `sum_j dU_j` is arbitrary.

This is not a corner case. It occurs in quiet regions, which the uniform and
perturbed floor tests deliberately exercise at 100 per cent rank deficiency, and
by section 7.5 it is the *generic* state of a Lagrangian moving mesh.

`F1` therefore needs a defined behaviour when `S^-` is rank deficient. Options,
in order of increasing ambition:

- fall back to the lumped `m_ij = (|T|/3) delta_ij` on rank-deficient elements,
  which is conservative and reduces to the current scheme exactly where the
  temporal mismatch is in any case multiplied by a vanishing `phi^T`;
- project the target onto `range(S^-)` and distribute the remainder centrally,
  which needs an argument that the discarded part is genuinely negligible;
- use `F2` instead, whose `delta_ij/4` part is not degenerate, though its
  `beta_i` part has the same problem.

The first is recommended for the initial implementation, with the rank-deficient
element count already reported by `RD-DIAG` so its frequency is visible. **This
must be settled before coding, since the floor tests will hit it immediately.**

### 12.4 Literature check

Three items found that bear on the open problems. None was in the earlier
reading.

**(a) The ALE topology gate of section 11.6 has a published solution, for RD
specifically.**

> *An ALE residual distribution scheme for the unsteady Euler equations over
> triangular grids with local mesh adaptation*, Computers & Fluids (2022),
> `S0045793022000810`.

From the abstract and secondary descriptions: an interpolation-free mesh
adaptation technique for the Euler equations in the ALE framework using a
residual distribution spatial discretisation. **Mesh connectivity changes are
interpreted as a series of fictitious continuous deformations**, implemented as
collapse and expansion operations on the affected elements, which enforces the
geometric conservation law **by construction** and avoids explicit interpolation
of the solution between grids, thereby preserving the conservativeness and
stability of the underlying fixed-connectivity scheme. The compact stencil of RD
is described as simplifying the derivation.

This is directly the problem Codex identified as a research gate: AREPO rebuilds
the Delaunay triangulation every step under mesh motion, so edge flips are the
norm rather than an exception. The technique reframes a connectivity change as a
degenerate limit of the continuous deformation the ALE-RD derivation already
handles. **The gate should be re-scoped from "unknown" to "read and adapt a
published technique".** Full text not accessible from here; the paper should be
obtained.

**(b) A different route past the mass matrix, in the Lagrangian setting.**

> Abgrall, Lipnikov, Morgan & Tokareva, *Multidimensional staggered grid residual
> distribution scheme for Lagrangian hydrodynamics*, arXiv:1811.00057, SIAM J.
> Sci. Comput. (2020).

Second-order staggered-grid RD for Lagrangian hydrodynamics. The relevant
feature: **Bernstein polynomials as finite element shape functions give a
natural mass matrix diagonalisation**, avoiding the solution of linear systems
with global sparse mass matrices while retaining the accuracy, coupled with
deferred-correction timestepping. Exact conservation of mass, momentum and total
energy for the Lagrangian formulation in non-conservative form.

This is a genuinely different answer to the same difficulty the `GL + F1`
predictor-corrector exists to solve, and it is posed in the Lagrangian regime
that a moving-mesh AREPO occupies. It changes the basis rather than the time
integration, so it is not a small modification, and the obstruction theorem of
section 6 would need re-examining in that setting rather than simply carrying
over. Recorded as a lead, not a proposal.

**(c) A current review covering exactly the framing question of `context.md`
item 1.**

> Abgrall, Maire & Ricchiuto, *Embedding General Conservation Constraints in
> Discretizations of Hyperbolic Systems on Arbitrary Meshes: A Multidimensional
> Framework*, arXiv:2509.25967, September 2025.

A review of discrete conservation for hyperbolic systems on **arbitrary meshes**,
covering both Eulerian and Lagrangian forms, and contrasting two notions of local
conservation: the **numerical flux** notion defined on element faces, and the
**residual** notion attached to elements and their degrees of freedom. The
authors describe these as equivalent in a sense, with the residual formulation
offering more flexibility when additional algebraic constraints must be
satisfied. Staggered meshes are treated and the dual mesh appears in the graph
construction.

This is the most recent authoritative statement from the group whose formulation
we are following, and the flux-versus-residual contrast is precisely the
Voronoi-versus-median-dual question of `context.md` item 1. It should be read
before that item is revisited.

### 12.5 Net effect on the plan

The direction is unchanged and now has three-way agreement. The revised order of
section 11.10 is adopted, with one addition: **settle the rank-deficient `F1`
definition of 12.3 before coding**, since the floor tests exercise it at 100 per
cent immediately.

Two of the four things previously listed as open research questions have moved:

- ALE topology: from an unknown gate to a published technique to be obtained and
  adapted, item (a);
- hierarchical timesteps: unchanged as a research question, but the factor-of-two
  argument underpinning the mixed-mass proposal is withdrawn until measured.
