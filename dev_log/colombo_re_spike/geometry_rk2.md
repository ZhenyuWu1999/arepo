# Does RK2 remove the CR-inspired topology diffusion?

No. For the particular monotone geometry operator implemented in this
branch, RK2 reduces artificial-time integration error but converges to the
**same diffusive geometry ODE**. This audit concerns that newly derived
explicit low operator, not a reproduction of the published Colombo--Re
BDF scheme and not a comparison of physical Euler time integrators.

The artificial geometry coordinate is `s in [0,1]`, with

\[
\frac{dQ}{ds}=-L U,\qquad
U_i=\frac{Q_i}{g_i(s)},\qquad
g(s)=g^0+s\,\delta m.
\]

The complete old/new geometric records determine `L`. Its identities are
`1^T L=0`, `L 1=-dm`, with nonpositive off-diagonal entries. Both endpoints
of `g(s)` are positive. This audit compares forward Euler, explicit
midpoint RK2 and Heun RK2 using exactly the same `L`, `g(s)` and initial
data. RK2 stages use the mass at the actual midpoint/end coordinate;
freezing stage masses would define a different discretization.

## Exact scalar mixing identity

There is a direct reason why increasing the temporal order cannot eliminate
this operator's mixing. The total mass and total scalar are constant, so

\[
c=\frac{\sum_iQ_i}{\sum_i g_i}
\]

is constant. Define the **lumped nodal** weighted variance

\[
V=\sum_i g_i(U_i-c)^2,\qquad w_i=U_i-c.
\]

Let `a_ij=-L_ij>=0` for `i!=j`. Using the column balance and the GCL row
identity,

\[
\begin{aligned}
\frac{dV}{ds}
&=-2w^TLw-\sum_i\delta m_i w_i^2\\
&=-\sum_{i\ne j}a_{ij}(w_i-w_j)^2\leq0.
\end{aligned}
\]

This loss exists in the exact continuous ODE, before choosing FE or RK2.
It is not a theorem about Euler entropy or an exact continuum `L2` norm:
the weights here are lumped P1 nodal masses. A flip followed by its reverse
returns the masses to their initial values, making the residual scalar
variance loss a particularly direct diagnostic of topology mixing.

For reverse topology, the low operator must be reassembled from the reversed
old/new geometry. It is another monotone operator; it is **not** `-L`,
because reversing the dissipative term would destroy its monotone signs.
Consequently the reverse event dissipates again. Both facts are implemented
explicitly in the audit.

## Numerical experiment

`tests/rd/audit_cr_geometry_rk2.py` uses a unit square with full nodal masses
`g=(1,1,1,1)` and six random convex quadrilaterals with unequal positive
exterior masses. Both `spectral` and `graph_minimal` coefficients are
tested. Each FE/midpoint/Heun run uses 4, 8, 16, 32 or 64 fixed substeps,
then repeats the event in reverse with the new full masses. The independent
reference is SciPy DOP853 with `rtol=1e-13` and mass-scaled `atol=1e-14`.

The transfer matrix is integrated directly. Thus the convergence error
tests the operator on all initial components, rather than relying on a
single scalar field with a potentially fortuitous cancellation.

```sh
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python \
  tests/rd/audit_cr_geometry_rk2.py --random-cavities 6 --seed 20260911 \
  > /Users/zhenyuwu/arepo_rd/local_runs/colombo_re_hydro_20260911/geometry_rk2.json
```

All 14 geometry/coefficient configurations pass. At the final refinement
from 32 to 64 substeps, observed operator convergence orders are:

| Integrator | Minimum order | Maximum order |
|---|---:|---:|
| FE | 1.0048 | 1.0105 |
| Midpoint RK2 | 2.0058 | 2.0416 |
| Heun RK2 | 2.0077 | 2.0365 |

The maximum relative conservation and constant-state errors are both
`8.89e-16`. The independent algebraic check of the variance identity gives
maximum relative discrepancy `5.85e-16`.

For the unit square, use the affine scalar `1+.2*x-.1*y` to measure the
largest nodal change after one forward flip, and the nonaffine scalar
`[1,4,2,.3]` to measure variance retained after one flip/reverse pair.
These are **different fields**, so the two columns below describe separate
diagnostics.

| Coefficient / integrator | Affine nodal defect | Flip/reverse variance fraction |
|---|---:|---:|
| Spectral, FE with 4 substeps | 0.0909710 | 0.0650896 |
| Spectral, Heun with 4 substeps | 0.0855045 | 0.0829119 |
| Spectral, Heun with 64 substeps | 0.0857476 | 0.0819779 |
| Spectral, DOP853 reference | **0.0857484** | **0.0819746** |
| Graph-minimal, FE with 4 substeps | 0.0491647 | 0.2724892 |
| Graph-minimal, Heun with 4 substeps | 0.0479632 | 0.2862502 |
| Graph-minimal, Heun with 64 substeps | 0.0479708 | 0.2858853 |
| Graph-minimal, DOP853 reference | **0.0479708** | **0.2858840** |

RK2 noticeably improves approximation to the ODE. For example, the
graph-minimal operator error with four substeps decreases from `0.00720`
with FE to `0.000353` with Heun. Nevertheless, the accurately integrated
graph-minimal ODE still loses about **71.4%** of this scalar's variance over
one flip/reverse pair, and still changes the affine field. RK2 therefore
removes additional FE integration error without restoring an undiffused
topology transfer.

## Positivity observations and scope

The fixed-step trajectories also apply the same transfer matrices to two
Euler examples: counterstreaming states and a high density/pressure contrast
case. Across the forward/reverse integrations and recorded RK stages,
35,560 state-array checks find no nonpositive density or internal energy.
These are repeated stage checks in this bounded campaign, not 35,560
independent flow tests. They do not establish an SSP theorem or positivity
for arbitrary substeps, stars, Euler fluxes or hierarchical schedules.

The relevant implementation distinction is between improving physical
Euler time integration and improving artificial geometry subcycling.
Neither change alone removes the diffusion built into this particular
`L`. A lower-diffusion high endpoint or a different geometric residual is a
separate mathematical change. This result does not rule out better
Colombo--Re-inspired formulations; it identifies the limitation of the
specific monotone low operator currently under test.
