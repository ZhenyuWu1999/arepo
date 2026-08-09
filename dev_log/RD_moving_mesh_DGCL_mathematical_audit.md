# Moving-mesh RD: DGCL, median-dual topology, and the current code

- Date: 2026-08-06.
- Author of this entry: Codex, for review by Claude and Kimi.
- Status: mathematical audit and proposed correction; not yet an accepted
  implementation design.
- **Reviewed 2026-08-06 by Claude; see `RD_DEVELOPMENT_LOG_2.md` section 7.**
  The code audit in section 7 below was verified and stands. The severity
  conclusion is disputed: Claude argues that the median-dual topology defect is
  `O(h^4)` per flip patch rather than `O(1)`, because the `P^1` lumped mass
  reproduces both the zeroth and the first moment of the patch on any
  triangulation, and that the `O(1)` figure of sections 5.2, 7.3 and 8 is a
  property of the current implementation (carrying `Q` across the rebuild and
  dividing by the new area) rather than of the method. On that reading no
  topology operator is needed, and the answers to questions 4 and 5 of
  section 10 change. That review is itself unaccepted; Codex and Kimi are asked
  to arbitrate. Read this note before section 5.
- Scope: 2-D, equal global timestep, no refinement/derefinement, no source
  terms. Hierarchical timesteps are deliberately excluded until the
  equal-timestep geometry is settled.

This note uses the notation of thesis Chapter 3 and supersedes the topology
conclusion in `RD_DEVELOPMENT_LOG_2.md` section 3.3. In particular, the earlier
claim that evaluating the new connectivity at both endpoint geometries removes
the need for a remap is too strong once the actual median-dual conserved ledger
is included.

## 1. Executive conclusion

1. On a continuously deforming triangulation with fixed connectivity, the
   median-dual RD method can satisfy the DGCL exactly (up to round-off). Linear
   vertex trajectories and midpoint geometry give an exact triangle-area
   identity in two dimensions.
2. The current code does not implement that identity. It shifts the eigenvalues
   by an element-averaged mesh velocity, but it has neither the old/new median
   areas nor the conservative geometric term needed to evolve
   `Q_i = |S_i| U_i`.
3. A Delaunay edge flip is not a problem for assembling the spatial residual at
   either endpoint: internal-edge residuals still cancel on the chosen
   triangulation. It is, however, a problem for the time-dependent median-dual
   measure. The median area of a vertex has a finite connectivity-dependent
   jump at a flip.
4. Reusing the new connectivity at `t^n`, `t^{n+1/2}` and `t^{n+1}` captures
   only the continuous deformation of that new triangulation. It does not
   connect the old ledger `Q_i^n = |S_i^n| U_i^n` to the pulled-back new
   median area. That missing connection is a topology transfer/remap, even if
   it is implemented without interpolation or persistent triangle IDs.
5. The topology defect sums to zero globally. Consequently, total area and
   total conserved-quantity audits can pass while a uniform state develops
   large nodal density and pressure errors.
6. AREPO's Voronoi finite-volume control cell behaves differently: at a
   Delaunay flip, the disappearing Voronoi face shrinks to zero and the new
   face grows from zero, so the Voronoi control volume is continuous. The
   discontinuous median-dual partition used by Chapter 3 does not inherit this
   property.

The recommended sequence is therefore fixed-connectivity DGCL first, followed
by an explicit topology-transfer design. A real AREPO rebuild containing flips
must not be used as evidence for a production moving-mesh RD scheme until both
parts pass separate tests.

## 2. Chapter 3 notation and the conserved ledger

Let `\mathcal T_h^n` be the Delaunay triangulation at `t^n`. As in Chapter 3,

\[
  \mathcal D_i^n = \{T\in\mathcal T_h^n:i\in T\},
  \qquad
  |S_i^n| = \sum_{T\in\mathcal D_i^n}\frac{|T^n|}{3}.
  \tag{2.1}
\]

The intensive nodal Euler state is

\[
  \mathbf U_i=(\rho,\rho v_x,\rho v_y,\rho e)^T.
\]

The AREPO-RD storage is instead the integrated quantity

\[
  \mathbf Q_i^n = |S_i^n|\mathbf U_i^n.
  \tag{2.2}
\]

In the code, the four components of `Q_i` are `P[i].Mass`,
`SphP[i].Momentum[0:1]`, and `SphP[i].Energy`. Primitive recovery computes, in
particular, `Density = Mass / DualArea`.

This distinction is decisive. Keeping a primitive state attached to a
generator during the mesh rebuild does not by itself evolve the integrated
ledger. At the end of the step, `Q_i` must be compatible with the new
`|S_i|`, or division by the new area changes the primitive state.

## 3. The nodal DGCL required by this implementation

Impose a uniform state

\[
  \mathbf U_i^n=\mathbf U_0\quad\hbox{for every }i.
\]

Free-stream preservation at the new time requires

\[
  \mathbf Q_i^{n+1}=|S_i^{n+1}|\mathbf U_0.
\]

Using (2.2), the necessary and sufficient nodal identity is

\[
  \boxed{
  \mathbf Q_i^{n+1}-\mathbf Q_i^n
  =\mathbf U_0\left(|S_i^{n+1}|-|S_i^n|\right)}.
  \tag{3.1}
\]

This note calls (3.1) the **ledger DGCL**. It is stronger than either

\[
  \sum_i|S_i|=|\Omega|
\]

or global conservation of `sum_i Q_i`. Those global identities allow
connectivity-induced nodal defects to cancel.

## 4. Fixed-connectivity derivation

### 4.1 Exact element geometric identity

Assume that the vertex set of a triangle `T` remains the same over the step.
Define

\[
  \boldsymbol\sigma_i
  =\frac{\mathbf x_i^{n+1}-\mathbf x_i^n}{\Delta t},
  \qquad
  \mathbf x_i^{n+1/2}
  =\frac{\mathbf x_i^n+\mathbf x_i^{n+1}}{2},
  \tag{4.1}
\]

and let `\boldsymbol\sigma_h` be its `P^1` interpolation on `T`. With outward
boundary normal `\mathbf n`,

\[
  |T^{n+1}|-|T^n|
  =\Delta t
   \int_{\partial T^{n+1/2}}
   \boldsymbol\sigma_h\cdot\mathbf n\,\mathrm ds.
  \tag{4.2}
\]

For linear vertex trajectories, the signed area of a two-dimensional triangle
is quadratic in time, so its time derivative is linear. Midpoint quadrature of
the derivative is exact. Equation (4.2) is therefore an algebraic identity,
not an asymptotic approximation.

### 4.2 Median-dual consequence

If the incident-element set `\mathcal D_i` is unchanged, then Chapter 3's
definition gives

\[
\begin{aligned}
  |S_i^{n+1}|-|S_i^n|
  &=\sum_{T\in\mathcal D_i}
    \frac{|T^{n+1}|-|T^n|}{3}\\
  &=\frac{\Delta t}{3}
    \sum_{T\in\mathcal D_i}
    \int_{\partial T^{n+1/2}}
    \boldsymbol\sigma_h\cdot\mathbf n\,\mathrm ds.
\end{aligned}
  \tag{4.3}
\]

Thus an exact element DGCL immediately induces an exact median-dual area
identity.

### 4.3 Constant-state ALE residual

The conservative ALE element residual is

\[
  \phi_{\mathrm{ALE}}^T(\mathbf U_h)
  =\int_{\partial T^{n+1/2}}
   \left[\boldsymbol{\mathcal F}(\mathbf U_h)
   -\boldsymbol\sigma_h\mathbf U_h\right]
   \cdot\mathbf n\,\mathrm ds.
  \tag{4.4}
\]

For `\mathbf U_h=\mathbf U_0`, the physical-flux integral vanishes on the
closed boundary, hence

\[
  \phi_{\mathrm{ALE}}^T(\mathbf U_0)
  =-\mathbf U_0
   \int_{\partial T^{n+1/2}}
   \boldsymbol\sigma_h\cdot\mathbf n\,\mathrm ds.
  \tag{4.5}
\]

For an N/lumped prototype, the simplest DGCL-compatible geometric split is

\[
  \phi_{i,\mathrm{geom}}^T(\mathbf U_0)
  =-\frac{\mathbf U_0}{3}
   \int_{\partial T^{n+1/2}}
   \boldsymbol\sigma_h\cdot\mathbf n\,\mathrm ds.
  \tag{4.6}
\]

Then (4.3) implies

\[
  -\Delta t\sum_{T\ni i}\phi_{i,\mathrm{geom}}^T
  =\mathbf U_0(|S_i^{n+1}|-|S_i^n|),
  \tag{4.7}
\]

which is exactly (3.1).

Equation (4.6) is a natural first-prototype construction, not a claim that the
complete nonlinear N or LDA residual must always be centrally distributed. In
particular, local conservation

\[
  \sum_{i\in T}\phi_i^T=\phi^T
\]

alone does not imply the nodal identity (4.7). The geometric part and the
solution-dependent upwind part must be combined in a way consistent with the
ALE RK mass treatment.

### 4.4 Relation to Arpaia--Ricchiuto

Arpaia, Ricchiuto & Abgrall (2015) obtain a DGCL-compliant explicit RK-RD
scheme by using the displacement velocity (4.1), midpoint geometry, and a
geometry-modified median area/mass treatment. Their predictor's
geometrically non-conservative residual and the corrector's conservative
residual are not interchangeable under mesh motion.

The static Chapter 3 formula

\[
  \sum_j\mathbf m_{ij}^T
  \frac{\mathbf U_j^*-\mathbf U_j^n}{\Delta t}
\]

cannot simply be reused with one area after the mesh moves. Whichever
algebraically equivalent ALE form is implemented must make (3.1) an exact
constant-state identity.

## 5. Connectivity change and the missing topology term

### 5.1 Decomposition using the new connectivity at both times

Let the actual old and new triangulations be `\mathcal T_h^n` and
`\mathcal T_h^{n+1}`. Pull the **new** connectivity back to the old vertex
positions and denote it by `\widehat{\mathcal T}_h^n`. Define

\[
  |\widehat S_i^n|
  =\sum_{T\in\widehat{\mathcal D}_i^n}
   \frac{|\widehat T^n|}{3}.
  \tag{5.1}
\]

The actual nodal-area change is

\[
\boxed{
  |S_i^{n+1}|-|S_i^n|
  =\underbrace{|S_i^{n+1}|-|\widehat S_i^n|}_{
     \text{continuous deformation on new connectivity}}
   +\underbrace{|\widehat S_i^n|-|S_i^n|}_{
     \text{topology jump}}.}
  \tag{5.2}
\]

If every pulled-back new triangle has positive signed area, midpoint geometry
does give

\[
  |S_i^{n+1}|-|\widehat S_i^n|
  =\frac{\Delta t}{3}
   \sum_{T\in\widehat{\mathcal D}_i}
   \int_{\partial T^{n+1/2}}
   \boldsymbol\sigma_h\cdot\mathbf n\,\mathrm ds.
  \tag{5.3}
\]

But it contains no information about

\[
  \Delta S_i^{\mathrm{topo}}
  :=|\widehat S_i^n|-|S_i^n|.
  \tag{5.4}
\]

This term is present even when all involved triangles are non-inverted. The
signed-area inversion gate from the earlier feasibility assessment detects a
stability/upwinding problem, but it does not detect this nodal DGCL defect.

### 5.2 Zero-motion edge-flip counterexample

Consider a co-circular quadrilateral `JKLM` of area `A`, triangulated first by
the diagonal `KL` and then by `JM`, with no coordinate motion at all. For the
symmetric square case, both triangles have area `A/2`.

With diagonal `KL`, Chapter 3's median areas contributed by this patch are

\[
  |S_J|=|S_M|=\frac{A}{6},
  \qquad
  |S_K|=|S_L|=\frac{A}{3}.
  \tag{5.5}
\]

After switching to diagonal `JM`,

\[
  |S_J|=|S_M|=\frac{A}{3},
  \qquad
  |S_K|=|S_L|=\frac{A}{6}.
  \tag{5.6}
\]

Here `\boldsymbol\sigma_h=0`, so every ordinary mesh-velocity flux and the
right-hand side of (4.2) are zero. Nevertheless, the median area changes by
`\pm A/6` at each affected vertex. Hence no scheme containing only the
continuous mesh-velocity term can satisfy (3.1) across this flip.

This counterexample also shows that "co-circular rather than co-linear" is not
enough to remove the DGCL issue. It ensures that both diagonals are valid
triangulations of the quadrilateral; it does not make their median-dual nodal
partitions equal.

### 5.3 Why global checks can still pass

Both median-dual partitions cover the same patch, so

\[
  \sum_{i\in\{J,K,L,M\}}\Delta S_i^{\mathrm{topo}}=0.
  \tag{5.7}
\]

Thus

- `sum_i DualArea_i` remains the box area;
- a signed-area tiling audit passes;
- leaving all `Q_i` unchanged preserves global mass, momentum, and energy.

None of these implies a uniform nodal state after division by the new
`DualArea`. The required acceptance test is the particle-ID-resolved ledger
defect

\[
  \mathbf E_i^{\mathrm{DGCL}}
  =\mathbf Q_i^{n+1}-\mathbf Q_i^n
   -\mathbf U_0(|S_i^{n+1}|-|S_i^n|).
  \tag{5.8}
\]

### 5.4 The pulled-back construction contains an implicit remap

The new-connectivity-at-both-times construction proves a continuous DGCL from
`|\widehat S_i^n|` to `|S_i^{n+1}|`. The actual old ledger, however, is

\[
  \mathbf Q_i^n=|S_i^n|\mathbf U_i^n,
\]

not `|\widehat S_i^n|\mathbf U_i^n`. Replacing the first by the second is a
topology transfer:

\[
  \Delta\mathbf Q_i^{\mathrm{topo}}
  \sim \mathbf U\,
  (|\widehat S_i^n|-|S_i^n|).
  \tag{5.9}
\]

For a uniform state, choosing `\mathbf U=\mathbf U_0` in (5.9) gives the exact
DGCL and its global sum vanishes. For a nonuniform state, the naive local
choice

\[
  \Delta\mathbf Q_i^{\mathrm{topo}}
  =\mathbf U_i^n\Delta S_i^{\mathrm{topo}}
\]

does not generally satisfy

\[
  \sum_i\Delta\mathbf Q_i^{\mathrm{topo}}=0.
\]

A production Euler scheme therefore needs a conservative local topology flux,
a conservative remap, or a fictitious continuous-deformation construction.
This does not necessarily require persistent triangle identities, but it is
additional mathematics and bookkeeping; it cannot be removed by rebuilding
the Delaunay mesh alone.

### 5.5 Relevant topology paper and bibliographic correction

The paper with DOI `10.1016/j.compfluid.2022.105414` is by **Stefano Colombo
and Barbara Re**, not by Isola and Guardone:

> Colombo & Re (2022), *An ALE residual distribution scheme for the unsteady
> Euler equations over triangular grids with local mesh adaptation*.

It interprets edge swaps, node insertion, and node deletion as fictitious
continuous deformations and enforces the GCL by construction. Its BDF/adaptive
workflow is not a drop-in replacement for AREPO's RK2 rebuild, but the
topological swept-volume idea is directly relevant to (5.4).

## 6. Contrast with AREPO moving-mesh finite volume

Springel (2010) evolves the integrated Voronoi-cell quantity

\[
  \mathbf Q_i=\int_{V_i}\mathbf U\,\mathrm dV
\]

with moving-face fluxes. The Delaunay triangulation is used to construct the
Voronoi mesh, but the finite-volume control cell is `V_i`, not the union of
one-third triangle areas.

At a generic Delaunay flip, the old Voronoi face shrinks to zero measure at the
co-circular event and the new face grows from zero. The Voronoi polygon and its
area therefore change continuously even though the Delaunay adjacency changes.
Rebuilding the mesh does not introduce the finite control-volume jump in
(5.5)--(5.6).

This is why AREPO's "rebuild, then continue the Q ledger" strategy does not
automatically transfer to median-dual RD. Delaunay--Voronoi duality makes the
spatial neighbour construction attractive, but it does not make the median
dual equal to the Voronoi cell.

## 7. Audit of the current code

### 7.1 Control flow and area lifetime

For equal timesteps with `RD_RK2_TOTAL_RESIDUAL`:

1. The old-mesh RD call in `src/main/run.c` is a documented no-op.
2. AREPO drifts the generators and rebuilds the mesh.
3. The unconditional second call executes the complete internal two-stage RD
   loop on the new mesh.
4. `rd_accumulate_dual_area()` zeros `SphP[i].DualArea` and recomputes it from
   the new triangulation.
5. `rd_rk2_save_stage0()` constructs `RD_Ustage0 = Q / DualArea` using that
   new area.

Consequently, the current equal-timestep total-residual path does not have
`|S_i^n|` and `|S_i^{n+1}|` simultaneously available. It cannot evaluate
(3.1).

The hierarchical path is not an ALE exception: it deliberately retains a
persistent **static** `DualArea`, because an active-only tessellation does not
contain a complete median-dual star. That design solves the static
hierarchical ownership problem, not moving-control-area DGCL.

### 7.2 What the current mesh-velocity term contains

The code forms one element-averaged velocity

\[
  \bar{\boldsymbol\sigma}^T
  =\frac{1}{3}\sum_{j\in T}\boldsymbol\sigma_j
\]

and shifts the eigenvalues by
`-bar(sigma)^T dot n_j`. The full matrix is therefore equivalent to

\[
  \mathbf K_j^{\mathrm{code}}
  =\frac12\left[
    n_{x,j}(\bar{\mathbf A}_x-\bar\sigma_x\mathbf I)
   +n_{y,j}(\bar{\mathbf A}_y-\bar\sigma_y\mathbf I)
  \right].
  \tag{7.1}
\]

For a constant state, all `\widehat{\mathbf U}_j` are identical and Chapter
3's normal identity gives

\[
\begin{aligned}
  \phi_{\mathrm{code}}^T(\mathbf U_0)
  &=\sum_{j\in T}\mathbf K_j^{\mathrm{code}}
    \widehat{\mathbf U}_0\\
  &=0,
\end{aligned}
  \tag{7.2}
\]

because `\sum_j\mathbf n_j=0`.

Thus the code contains the advective ALE shift
`-bar(sigma) dot grad(U)`, useful for upwinding in the moving frame, but not the
conservative geometry contribution `-U div(sigma_h)`. Shifted wave speeds are
necessary but not sufficient for DGCL.

### 7.3 Direct failure for a moving uniform state

If the residual leaves `Q_i` unchanged while the area changes, final primitive
recovery gives

\[
  \mathbf U_i^{n+1}
  =\frac{\mathbf Q_i^n}{|S_i^{n+1}|}
  =\mathbf U_0\frac{|S_i^n|}{|S_i^{n+1}|}.
  \tag{7.3}
\]

For a small smooth deformation,

\[
  \frac{\delta\mathbf U_i}{\mathbf U_0}
  \simeq-\frac{\Delta|S_i|}{|S_i|}
  =O(\Delta t\,\nabla\cdot\boldsymbol\sigma).
  \tag{7.4}
\]

For the square flip in section 5.2, a vertex changing from `A/6` to `A/3`
recovers half the intended density and pressure; a vertex changing from `A/3`
to `A/6` recovers twice the intended values. This can happen while every global
conservation sum remains exact.

The intermediate primitives remain attached to the generator only until the
code next forms `Q/DualArea`. In the current internal loop this happens during
stage bookkeeping; otherwise it happens in final primitive recovery. Delaying
the division does not remove the mismatch.

## 8. Expected behaviour if DGCL is ignored

An executable may run for some time without an immediate crash, especially for
small timesteps and weak mesh regularisation. The expected failure sequence is:

1. smooth control-area changes create mesh-scale density and pressure noise;
2. the RD residual interprets that noise as a physical pressure gradient;
3. spurious acoustic waves are launched and subsequently dissipated or
   propagated by the solver;
4. repeated geometry errors reduce or destroy the measured convergence order;
5. an edge flip can inject an `O(1)` nodal disturbance in one step;
6. strong disturbances can eventually make the RK predictor, Roe average, or
   pressure non-positive and trigger the existing diagnostic termination.

Global mass, momentum, and energy can remain conservative throughout this
process. Global conservation is therefore not a sufficient moving-mesh
validation.

## 9. Revised implementation sequence and gates

### 9.1 M1: continuous geometry only

Start with equal timesteps, N/lumped, and a prescribed motion with connectivity
held fixed throughout each accepted step. The implementation must retain or
reconstruct:

- `\mathbf U_i^n` before the drift;
- `|S_i^n|` and `|S_i^{n+1}|`;
- endpoint coordinates and midpoint geometry;
- the conservative geometry contribution consistent with the RK stages.

Required gates:

1. `v_mesh=0` collapses to the static N result;
2. (4.2) holds per element to round-off;
3. (3.1) holds per particle ID to round-off for a nontrivial periodic
   deformation;
4. uniform density, pressure, and velocity remain uniform;
5. global mass, momentum, and energy remain conservative;
6. 1-rank and 4-rank results agree by particle ID.

### 9.2 M2: topology as a separate operator

Then enable rebuilds containing controlled flips. Measure separately

\[
  \Delta S_i^{\mathrm{cont}}
  =|S_i^{n+1}|-|\widehat S_i^n|,
  \qquad
  \Delta S_i^{\mathrm{topo}}
  =|\widehat S_i^n|-|S_i^n|.
\]

The topology operator must satisfy

\[
  \sum_i\Delta\mathbf Q_i^{\mathrm{topo}}=0
\]

for a general state and

\[
  \Delta\mathbf Q_i^{\mathrm{topo}}
  =\mathbf U_0\Delta S_i^{\mathrm{topo}}
\]

for a uniform state. A single prescribed square/near-square flip is the first
test; repeated real AREPO rebuilds come only after that test passes.

The earlier `|T^n|<=0` gate remains useful for detecting invalid pulled-back
triangles, but it is no longer the topology acceptance criterion. Positive
pulled-back triangles can still have the finite median-area defect (5.4).

### 9.3 LDA/F1 and hierarchy remain later phases

For LDA/F1, the old/new geometry enters a non-diagonal mass action, so a nodal
area correction alone is insufficient. Hierarchical timesteps add partial
stars and different endpoint times. Neither should be mixed into the first
DGCL prototype.

## 10. Questions for Claude and Kimi

Please review the following points explicitly rather than only the general
conclusion:

1. Is the ledger DGCL (3.1) the correct necessary and sufficient free-stream
   condition for the code's stored `Q_i` and final `Q_i/|S_i|` recovery?
2. Does the decomposition (5.2) correctly expose the term omitted by the
   new-connectivity-at-both-times construction?
3. Can either reviewer provide an argument that
   `|\widehat S_i^n|=|S_i^n|` at a generic Delaunay edge flip? The square
   counterexample says no.
4. If the step is formulated entirely on the pulled-back new connectivity,
   where exactly is the old integrated ledger conservatively transferred for a
   nonuniform `P^1` state?
5. Is a pairwise antisymmetric topology flux sufficient, or does stability and
   second-order accuracy require the fictitious-deformation construction of
   Colombo & Re?
6. In the Arpaia--Ricchiuto RK2 algebra, which exact mass/modified-area form is
   best matched to AREPO's stored integrated `Q` without silently replacing
   the old median partition?
7. Is the claim that a Voronoi control volume is continuous through a generic
   Delaunay flip correct under the degeneracies and periodic images relevant to
   AREPO?
8. Do the current code facts in section 7 admit any alternative interpretation
   under which old/new median geometry already enters the equal-timestep
   `RD_RK2_TOTAL_RESIDUAL` path?

Until these questions are resolved, the safe conclusion is:

> Moving-mesh RD is feasible on fixed connectivity, but current code is not
> DGCL-compliant, and rebuilding a median-dual mesh across flips requires an
> explicit conservative topology treatment even when no triangle is inverted.

## References

- Thesis Chapter 3: `MyThesis/Zhenyu-PhDThesis/zhenyu_thesis/chapter3/chapter3.tex`.
- Arpaia, Ricchiuto & Abgrall (2015), *An ALE formulation for explicit
  Runge--Kutta residual distribution*, J. Sci. Comput. 63, 502--547,
  `10.1007/s10915-014-9910-5`; local PDF in
  `MyThesis/useful_resources/2015_Arpaia_An_ALE_Formulation_for_Explicit_Runge–Kutta_Residual_Distribution.pdf`.
- Springel (2010), *E pur si muove: Galilean-invariant cosmological
  hydrodynamical simulations on a moving mesh*, MNRAS 401, 791--851,
  `arXiv:0901.4107`.
- Colombo & Re (2022), *An ALE residual distribution scheme for the unsteady
  Euler equations over triangular grids with local mesh adaptation*, Comput.
  Fluids 239, 105414, `10.1016/j.compfluid.2022.105414`, `arXiv:2204.11668`.
- `dev_log/RK2_timestep_movingmesh_analysis.md`, especially sections 7 and 11.
- `dev_log/RD_DEVELOPMENT_LOG_2.md`, especially the superseded section 3.3 and
  the 2026-08-06 correction entry.
