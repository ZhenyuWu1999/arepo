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
