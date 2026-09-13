# Explicit same-time topology transfer on full P1 nodal masses

Status: bounded Python operator experiment, 2026-09-10. No production solver
changes. This is a **new explicit construction inspired by Colombo & Re**,
not their published BDF algorithm and not a proof of hierarchical-time Euler
positivity. Implementation: `tests/rd/colombo_re_explicit.py`.

## What comes from the paper, and what is new

Colombo & Re use P1 nodes and triangle nodal area `|K|/3` in the basic temporal
residual (§2.2, §2.4 Eq.18). Signed semi-edge swept areas generate geometric
interface velocities (§2.5 Eqs.20–22). On a topology change, old triangles
become ghosts and new triangles have zero past area (§3.1); both contribute
to the assembled system. Their physical update is implicit BDF with a
common physical time step (§4). Collapse/expand computes geometry; it is
not an explicit fluid integration through zero-area triangles.

Source: [Colombo & Re, 2022](https://arxiv.org/html/2204.11668v1).

Here we retain their signed old/new geometry records, combine their
pure-geometry LF residuals, and integrate a new positive **full nodal mass
homotopy**. The independent variable `s` below is an algebraic transfer
parameter. It is neither physical time nor the paper's literal collapse
trajectory. In particular, no actual flow state is assigned to a collapsed
triangle.

## Data and essential balance checks

At one physical time, let the old and new triangulations cover the same
closed cavity and have identical boundary vertices and coordinates. Let
`m_i^-`, `m_i^+` denote their **full** lumped P1 nodal masses, including
unchanged exterior support. Thus

    dm_i = m_i^+ - m_i^- = sum_{r containing i} Delta A_r / 3.

Each record `r` is an old triangle collapsed to a common cavity point, or
a new triangle expanded from it. Its three signed integrated swept areas
are `nu_ri`; these are areas, not velocities. Geometry must supply

    sum_{i in r} nu_ri = Delta A_r,
    sum_{r containing i} nu_ri = 0  for EACH node i.

The second identity follows from signed internal-edge cancellation and the
round trip of the common cavity boundary. The code checks it explicitly.
Checking only `sum_r Delta A_r = 0` is insufficient: a state-weighted sum
contains different `U_i`. The audit rejects an incomplete old/new pair that
has zero total area change but nonzero nodal swept balance.

All records at a geometry substep use the same current nodal state `U_i(s)`.
The cancellation is not assumed valid if different records use different
temporal states at their shared node.

## The assembled scalar generator

For every conserved component, use the same scalar coefficients:

    phi_r(U) = -sum_j nu_rj U_j,
    R_ri(U) = phi_r(U)/3 + alpha_r (U_i - Ubar_r),
    Ubar_r = sum_{j in r} U_j / 3.

The local matrix and assembled matrix are

    L_r = -1 nu_r^T / 3 + alpha_r (I - 11^T/3),
    L   = sum_r scatter(L_r).

For complete records,

    1^T L = 0,                 conservation,
    L 1   = -dm.               geometric conservation

Two coefficient choices are implemented:

1. `spectral`: `alpha_r = max_j |nu_rj|`. This parallels the paper's
   pure-ALE LF coefficient and is the default baseline.
2. `graph_minimal`: `alpha_r = max(0, -min_j nu_rj)`. This is a **new
   pure-geometry graph choice**, not the paper's Euler spectral-radius
   prescription. It is the smallest nonnegative recordwise coefficient
   that guarantees every off-diagonal entry `-(nu_rj+alpha_r)/3 <= 0`.
   The assembled zero column sums then give `L_ii >= 0`. It need not be the
   smallest viscosity achievable by an arbitrary globally assembled graph.

Multiplying either coefficient by `alpha_factor >= 1` is supported. These
scalar graph conditions must not be transferred to the physical Euler flux
Jacobian without a separate analysis.

## Explicit homotopy and the actual Euler positivity proof

Set

    g_i(s) = (1-s)m_i^- + s m_i^+,       0 <= s <= 1,
    dQ/ds = -L U,                       U_i = Q_i/g_i(s).

Both endpoint masses must be strictly positive, so the entire homotopy is
positive. This remains true even though an individual old ghost's formal
area goes to zero: no division by that element area is performed.

One explicit Euler transfer step is

    Q_next = [diag(g) - ds L] U,
    g_next = g + ds dm.

When

    ds L_ii <= g_i  for every i,

the coefficient matrix `A = diag(g)-ds L` is entrywise nonnegative. In
addition,

    sum_j A_ij = g_i + ds dm_i = g_next_i.

Therefore `U_next_i = sum_j (A_ij/g_next_i) U_j` is a convex combination
of old nodal **conservative Euler vectors**, with identical nonnegative
weights for density, both momenta, and energy. For ideal-gas Euler, the
set

    rho > 0,   E - |momentum|^2/(2 rho) > 0

is convex: the kinetic-energy perspective is convex, so internal-energy
surplus is concave. This proves positive density and pressure after every
accepted substep from admissible input, in exact arithmetic. It is stronger
and more specific than citing an LF eigenvalue condition alone.

The same update conserves all component totals because

    1^T Q_next = 1^T diag(g) U - ds 1^T L U = 1^T Q.

For uniform `U`, `Q_next = g_next U`, proving GCL and uniform preservation.
Repeated safe substeps compose these properties. Neither maximum pressure
nor maximum specific entropy is guaranteed by convex mixing of conserved
variables.

`mode='adaptive'` chooses `ds <= cfl * min_i g_i/L_ii`, with `0<cfl<=1`, and
shortens the final step to end at `s=1`. `once` and `fixed` are comparison
modes: they report violated geometric CFL or negative transfer coefficients
rather than claiming positivity. This geometric CFL does not change the
physical timestep or complete outstanding hydrodynamic intervals.

## Independent unit-square result and limitations

For `AC -> BD` with the collapse point at the square center, the four
records have integrated swept areas

    ABC old: (-1/8, -1/4, -1/8),
    ACD old: (-1/8, -1/8, -1/4),
    ABD new: ( 1/4,  1/8,  1/8),
    BCD new: ( 1/8,  1/4,  1/8).

The hand-built records match the independent geometry module exactly.
With the spectral coefficient, `L_ii=1/2` for every node. A regular old
six-triangle star has full nodal masses `(1,1,1,1)`, making a single step
safe with geometric CFL `1/2`. With no exterior support, the initial maximum
CFL is `3`; a single explicit step is unsafe, while the adaptive `.9` rule
uses three safe substeps. Exterior mass `1/12` needs two.

With `graph_minimal`, old records retain `alpha=1/4` but new records have
`alpha=0`. The diagonal becomes `(1/3,1/6,1/3,1/6)`: a single unit-square
step is exactly at geometric CFL one even without exterior support. The
default `.9` safety factor may still subdivide it. This improvement follows
from the assembled pure-geometry signs, not from an Euler-flux claim.

**Linear exactness is not obtained.** For the regular star and affine scalar
field `U=1+.2x+.3y`, the spectral single-flip maximum state change is `.125`.
A flip/reverse pair changes the state by up to `.2395833333`; the scalar
range becomes `1/24` of its initial value. These are deliberately prominent
negative findings. Refining the artificial `s` integration approaches this
generator's solution, not an exact affine remap. Subcycling controls
positivity and integration error; it does not remove the generator's spatial
diffusion. For geometrically similar patches with fixed exterior-mass ratio,
an affine gradient yields local state error proportional to patch size.

The parent comparison harness separately studies both coefficient choices,
ODE-reference agreement, affine/smooth errors, and repeated reversals. A
low-order positive endpoint is established here, not a thesis-ready high-order
topology update.

## Boundary of the hierarchical claim

The proof assumes `Q/g` is the state used at every substep of this same-time
transfer. An asynchronous implementation can algebraically apply the map to
positive current ledgers, but this does not identify them as common-time
physical states and does not settle the hydrodynamic work still owed by
coarse elements. If later increments keep using an older frozen primitive,
they can still spend mass or internal energy already changed by this remap.

Consequently this operator does **not** prove full hierarchical positivity,
second-order time accuracy, or cosmological applicability. The open temporal
problem is separate from the established geometric convex-combination proof.

## Reproduction and API

```sh
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python \
  tests/rd/colombo_re_explicit.py --samples 512 --seed 20260910
```

The command emits bounded JSON, checks both coefficient rules on admissible
Euler states, checks random convex cavities and collapse points against the
independent geometry implementation, and checks rejection of incomplete
records. No physical PDE simulation or MPI launch is performed.

```python
L, checks = assemble_lf_operator(geometry, alpha_rule="spectral")
q_new, g_new, checks = topological_remap(
    q, full_old_mass, geometry, mode="adaptive", cfl=.9,
    alpha_rule="graph_minimal")
```

`geometry` supplies `records`, `node_ids`, and `mass_delta`; nodewise arrays
follow `node_ids`. Each record supplies `ids` and `integrated_nu` in matching
order. `q` may be scalar `(n,)` or multicomponent `(n,ncomp)`. Full old masses
must include exterior support. Both calls preserve their inputs.
