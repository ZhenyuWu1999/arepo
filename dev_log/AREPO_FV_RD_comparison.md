# AREPO Finite Volume and Residual Distribution: Spatial Reconstruction, Time Evolution, and Data Interpretation

- Status: working technical note for the AREPO--RD implementation and a future
  Chapter 4 draft
- Author: Zhenyu Wu and Codex (GPT-5)
- Last updated: 2026-08-01

## Status and scope

This note compares the finite-volume (FV) hydrodynamics solver in AREPO with
the two-dimensional residual-distribution (RD) solver currently implemented in
this repository. Its immediate purpose is to answer a specific question:

> Does the RD implementation contain the spatial and temporal interpolation
> performed by AREPO's MUSCL--Hancock finite-volume method when states are
> extrapolated from cell centres to Voronoi faces?

The short answer is:

> **RD contains spatial representation and time evolution, but not in the form
> of MUSCL--Hancock centre-to-face reconstruction.** The FV solver reconstructs
> left and right states at each Voronoi face and solves a one-dimensional
> Riemann problem there. RD instead assumes a piecewise-linear nodal field on
> each Delaunay simplex, integrates a multidimensional residual over the whole
> simplex, and distributes that residual to its vertices. The current
> `RD_RK2_TOTAL_RESIDUAL` path then advances those nodal states with an explicit
> two-stage RD predictor/corrector, not a Hancock half-step face predictor.

The absence of a Voronoi-face reconstruction is therefore not by itself a
missing piece of the RD method. A separate and important interface question
does remain: AREPO normally interprets its hydrodynamic data as finite-volume
cell averages associated with Voronoi cells, whereas nodal RD interprets its
degrees of freedom as point values at Delaunay vertices and evolves them with a
median-dual measure. The present static-mesh implementation adopts the latter
interpretation, but a fully consistent mapping between these interpretations
has not yet been derived for an irregular moving mesh.

This note describes the current source after commit `348b766`. It is an audit
and mathematical comparison, not a proposal to add MUSCL reconstruction to RD.

## 1. Shared objective, different discrete operators

Both methods approximate the conservation law

\[
  \partial_t \mathbf U + \nabla\!\cdot\boldsymbol{\mathcal F}(\mathbf U)=0,
\]

and both must provide:

1. a spatial representation of the state;
2. an upwind approximation to hydrodynamic information transport;
3. a conservative spatial operator;
4. sufficient time centring for the desired temporal order; and
5. nonlinear stabilisation near discontinuities.

They place these ingredients in different parts of the algorithm.

### 1.1 Direct conceptual correspondence

| Numerical role | AREPO finite volume / MUSCL--Hancock | Residual distribution |
| --- | --- | --- |
| Stored degrees of freedom | Conserved averages over Voronoi cells | Nodal states associated with Delaunay vertices and median-dual control volumes |
| Local mesh object | A Voronoi face shared by two cells | A complete Delaunay triangle in 2-D, or tetrahedron in 3-D |
| Spatial variation | Limited gradient reconstructed from a cell centre to a face | Continuous `P1` interpolation over the simplex, determined by its nodal values and basis functions |
| State evaluation point | Two one-sided states at the common face | One set of nodal states defining a field throughout the element |
| Spatial operator | Numerical flux through each face | Integrated flux-divergence residual over each simplex |
| Upwinding | One-dimensional Riemann solver normal to the face | Multidimensional characteristic splitting through the element matrices `K_i^+` and `K_i^-` |
| Conservation statement | The same face flux enters the two neighbouring cells with opposite signs | The nodal residuals satisfy `sum_i phi_i^T = phi^T` in every element |
| Second-order time mechanism | Hancock/Taylor prediction to the time-centred face state | Explicit RD predictor `U*` followed by a total-residual corrector |
| Smooth-flow high-order mechanism | Linear reconstruction plus time centring | Linearity-preserving residual distribution plus a consistent temporal mass treatment |
| Nonlinear shock control | Slope limiting and choice of Riemann solver | A monotone distribution such as N, or nonlinear blending between N and a high-order distribution such as LDA |
| Moving-mesh term | Flux solved in the moving face frame, with face velocity included | ALE element residual, changing nodal/control volumes, and a discrete geometric conservation law are required |

The analogy is consequently at the level of **numerical roles**, not at the
level of identical operations. In particular, the RD equivalent of MUSCL's
spatial accuracy is not another reconstruction to a Voronoi face: it is the
piecewise-linear simplex field together with a linearity-preserving residual
distribution.

## 2. AREPO finite volume: explicit centre-to-face reconstruction

For the finite-volume solver, the primitive variables stored for a gas cell are
treated as the state at the cell centre for reconstruction purposes. For a
face with centroid `x_f`, AREPO constructs the displacement from the Voronoi
cell centre `x_c`, for example

```text
dx = x_f - x_c.
```

This is implemented in `face_get_state()` in
`src/hydro/finite_volume_solver.c`: `VF[i].c*` supplies the face centroid and
`SphP[particle].Center` supplies the Voronoi cell centre.

The piecewise-linear reconstruction has the familiar form

\[
  \mathbf W_{i,f}
  = \mathbf W_i
  + \left(\nabla\mathbf W\right)_i\!\cdot
    \left(\mathbf x_f-\mathbf x_{c,i}\right),
\]

with limited gradients calculated from neighbouring cells. The current source
performs the following sequence in `compute_interface_fluxes()`:

```c
state_L = state_center_L;
state_R = state_center_R;

face_do_time_extrapolation(&delta_time_L, &state_center_L, atime);
face_do_time_extrapolation(&delta_time_R, &state_center_R, atime);

face_do_spatial_extrapolation(&delta_space_L, &state_center_L, &state_center_R);
face_do_spatial_extrapolation(&delta_space_R, &state_center_R, &state_center_L);

face_add_extrapolations(&state_L, &delta_time_L, &delta_space_L, &stat);
face_add_extrapolations(&state_R, &delta_time_R, &delta_space_R, &stat);
```

For each primitive quantity, the spatial increment ultimately reduces to

```c
delta = grad[0] * dx[0] + grad[1] * dx[1] + grad[2] * dx[2];
```

The time increment is obtained by using the primitive-variable Euler equations
to replace time derivatives by spatial derivatives. In schematic form,

\[
  \mathbf W_{i,f}^{n+1/2}
  = \mathbf W_i^n
  + \nabla\mathbf W_i\cdot(\mathbf x_f-\mathbf x_{c,i})
  + \frac{\Delta t}{2}\,\partial_t\mathbf W_i.
\]

The left and right extrapolated states define a one-dimensional Riemann problem
normal to the face. Its numerical flux is multiplied by the face area and
applied with opposite signs to the neighbouring conserved cell quantities.

This is the reconstruction described in Chapter 1 of the thesis: spatial
reconstruction, time evolution, and a Riemann solver are three identifiable
components of the Godunov-type finite-volume method.

## 3. RD spatial representation: simplex interpolation instead of face reconstruction

### 3.1 Mathematical representation

In nodal RD, the solution in a triangle `T` is not assumed to be piecewise
constant. For a generic interpolation variable it is represented by

\[
  \mathbf U_h(\mathbf x,t)
  = \sum_{i\in T}\mathbf U_i(t)\,\psi_i(\mathbf x),
\]

where `psi_i` are the `P1` Lagrange basis functions. In two dimensions,

\[
  \nabla\psi_i = \frac{\mathbf n_i}{2|T|},
\]

where `n_i` is the inward normal to the edge opposite vertex `i`, with
magnitude equal to the length of that edge. Hence

\[
  \nabla\mathbf U_h
  = \frac{1}{2|T|}\sum_{i\in T}\mathbf n_i\mathbf U_i
\]

is already determined by the nodal states and element geometry. No separate
least-squares or Green--Gauss gradient is required to define this field inside
the triangle.

For the nonlinear Euler equations, the implemented linear interpolation is
applied to the Roe parameter vector

\[
  \mathbf Z = \sqrt{\rho}\,(1,v_x,v_y,H)^T,
\]

rather than directly to `U`. The code constructs `Z_Roe[j]` at all three
vertices, calculates an element average `Z_avg`, and forms the modified states
`U_hat[j]` used by the conservative Roe linearisation.

### 3.2 Element residual

The RD spatial operator is the integrated flux divergence over the triangle,

\[
  \boldsymbol\phi^T
  = \int_T \nabla\!\cdot
      \boldsymbol{\mathcal F}(\mathbf U_h)\,\mathrm dA.
\]

After element-wise Roe linearisation, this is represented as

\[
  \boldsymbol\phi^T
  = \sum_{i\in T}\mathbf K_i\widehat{\mathbf U}_i,
  \qquad
  \mathbf K_i
  = \frac12\left(n_{x,i}\bar{\mathbf A}_x
                        +n_{y,i}\bar{\mathbf A}_y\right).
\]

In `src/hydro/residual_distribution_solver.c`, the nodal normals and element
Roe state are used to construct `Kmatrix`. The total residual is then assembled
directly as

```c
Phi += Kmatrix[j][K_full] * U_hat[j];
```

schematically, with the full component contractions written explicitly in the
source.

There is no invocation of `face_do_spatial_extrapolation()`, no evaluation at
`VF[i].cx`, no construction of two states on a Voronoi face, and no face
Riemann solve in the RD branch.

### 3.3 Distribution and multidimensional upwinding

The total residual is distributed among the element vertices:

\[
  \boldsymbol\phi_i^T
  = \boldsymbol\beta_i^T\boldsymbol\phi^T,
  \qquad
  \sum_{i\in T}\boldsymbol\phi_i^T=\boldsymbol\phi^T.
\]

The matrices `K_i^+` and `K_i^-` split characteristic information according
to its direction relative to all nodal normals of the simplex. This is the RD
upwind mechanism. It treats the complete multidimensional element rather than
assembling the result from independent one-dimensional, face-normal Riemann
problems.

For smooth solutions, LDA is the linearity-preserving distribution. The N
scheme supplies the more dissipative monotone/positive distribution. A blended
scheme is the RD analogue of nonlinear high-resolution stabilisation, although
it is not algebraically the same as a MUSCL slope limiter. The current
total-residual RK2 path intentionally rejects `B_SCHEME` at compile time until
the blended temporal mass matrix and total-residual blending coefficient have
been derived.

## 4. Time evolution: Hancock prediction versus RD predictor/corrector

### 4.1 MUSCL--Hancock

The Hancock step predicts a state at the appropriate intermediate face time,
using spatial gradients and the governing equations. The predicted and
spatially reconstructed left/right states are then passed to the Riemann
solver. Space and time reconstruction are therefore combined before the face
flux is evaluated.

### 4.2 Current total-residual RD path

With `RD_RK2_TOTAL_RESIDUAL`, the RD solver instead performs the two-stage
update

\[
  \mathbf U_i^*
  = \mathbf U_i^n
  - \frac{\Delta t}{|S_i|}
    \sum_{T\ni i}\boldsymbol\phi_i^T(\mathbf U^n),
\]

followed by a corrector that distributes a total space--time residual
containing the new spatial residual and the chosen temporal mass term. The
predictor reaches the full-step stage `U*`; the final combination supplies the
second-order time centring. It is not a prediction of a face state at
`n+1/2`.

The current source makes the distinction explicit:

```c
/* The stage states are exact: W^n before the predictor, the
 * recovered W* before the corrector. No Taylor extrapolation. */
(void)grad;
```

Thus AREPO still calls `calculate_gradients()` and exchanges the gradient
structure in the shared main-loop plumbing, but those gradients are not used
to form the hydrodynamic RD residual in this path. On a moving mesh they may
still influence other operations, such as the choice or regularisation of
mesh-generator velocities; that is distinct from centre-to-face fluid-state
reconstruction.

The N+RK2 fixed-mesh control measured temporal order `2.009`, showing that the
two-stage driver itself can be second order. LDA+RK2 remains first order in
time because of a defect in the current F1 temporal-mass path. The three-way
mixed/coherent-`beta^n`/coherent-`beta*` experiment showed that merely making
the stage beta convention coherent does not repair that defect.

### 4.3 Legacy RD path

Without `RD_RK2_TOTAL_RESIDUAL`, the older RD branch calls
`triangle_vertex_do_time_extrapolation()`. That routine uses AREPO's primitive
gradients and a Taylor expansion analogous to the temporal part of the FV
predictor. It then evaluates the element residual twice with half weight.

This older path still performs no spatial extrapolation to a Voronoi face. It
also lacks the complete RD total temporal residual and scheme-dependent mass
matrix. It should therefore not be described as a complete MUSCL--Hancock
scheme or as the canonical second-order LDA RD formulation.

## 5. The important AREPO--RD interface question

The key unresolved issue is not whether RD should reconstruct to a Voronoi
face. It is the meaning and location of the stored degree of freedom.

Three geometrical positions must be distinguished:

\[
  \mathbf x_{c,i}
  = \text{Voronoi cell centre of mass},\qquad
  \mathbf x_{g,i}
  = \text{mesh generator / Delaunay vertex},\qquad
  \mathbf x_f
  = \text{Voronoi face centroid}.
\]

The finite-volume reconstruction uses

\[
  \bar{\mathbf U}_i
  \longrightarrow
  \mathbf U_{i,f}
  \simeq \bar{\mathbf U}_i
  + \nabla\mathbf U_i\cdot(\mathbf x_f-\mathbf x_{c,i}).
\]

Nodal RD assumes that `U_i` is already the value at `x_g,i` and uses it in the
simplex interpolation. If the data entering RD are instead interpreted as
Voronoi cell averages, a possible consistency conversion would begin with

\[
  \mathbf U_i(\mathbf x_{g,i})
  \simeq \bar{\mathbf U}_i
  + \nabla\mathbf U_i\cdot
    (\mathbf x_{g,i}-\mathbf x_{c,i}),
\]

but adding this formula alone would not solve the coupling problem. A complete
formulation must also specify what quantity is evolved, which control volume
defines it, how conservation is maintained, and how it changes when the mesh
moves.

### 5.1 What the present code does

The RD solver reads `SphP.Density`, `P.Vel`, and `SphP.Pressure` directly as
the states of the Delaunay triangle vertices. Its geometric residual uses
Delaunay normals derived from the mesh-generator positions. It does not use
`SphP.Center` and does not apply a `Center -> P.Pos` correction.

For the RD update, the intensive state is reconstructed from the conserved
quantity divided by

\[
  |S_i|=\sum_{T\ni i}\frac{|T|}{3},
\]

the median-dual area stored as `SphP[i].DualArea`, rather than by the Voronoi
cell volume. In this sense, once the RD path is active, the implementation is
deliberately closer to a nodal median-dual method than to the usual AREPO
finite-volume interpretation.

The fixed-mesh validation campaigns use generator-sampled initial conditions,
which align with this nodal interpretation. They do not establish consistency
for data supplied as Voronoi cell averages on an irregular moving mesh.

### 5.2 Why moving meshes make the distinction unavoidable

On a regular centroidal mesh, `x_c` and `x_g` can coincide or differ only
slightly. On an irregular moving mesh their difference is generally `O(h)`.
Treating a cell average at `x_c` as a point value at `x_g` can therefore
introduce a leading spatial consistency error.

Moreover, a moving-mesh formulation must account simultaneously for:

- the motion of the Delaunay simplex and its nodal normals;
- the mesh-velocity contribution to the ALE residual;
- the time dependence of the median-dual or Voronoi control volume;
- conservation of the integrated state;
- a discrete geometric conservation law;
- asynchronous participation under AREPO's hierarchical timebins; and
- the interpretation of states exchanged with non-RD AREPO modules.

Consequently, copying AREPO's centre-to-face MUSCL reconstruction into RD would
not by itself resolve the actual interface problem.

## 6. Two coherent mathematical interpretations for future work

The following are alternatives to be derived and tested, not decisions already
made.

### 6.1 Pure nodal RD interpretation

Treat the mesh generators as genuine nodal degrees of freedom and evolve

\[
  \mathbf Q_i=|S_i|\mathbf U_i
\]

on the moving median dual. This is closest to the standard simplex-based RD
literature and the current static implementation. It requires a complete ALE
RD update, including the time-dependent mass matrix and geometric conservation
law. Coupling to AREPO modules that expect Voronoi cell averages must be made
explicit.

### 6.2 Voronoi finite-volume / multidimensional corner-flux interpretation

Retain AREPO's conserved quantities as Voronoi cell integrals and reinterpret
the Delaunay-element residual contributions as conservative multidimensional
corner fluxes into the surrounding Voronoi cells. This may provide a more
natural interface to the existing code, but the exact equivalence, quadrature,
moving-volume terms, and nonlinear stabilisation must be derived rather than
assumed.

The recent finite-volume/RD equivalence literature on polygonal meshes may be
useful for this interpretation. It should not be reduced to replacing the
median-dual area by the Voronoi volume in an otherwise unchanged nodal formula;
that substitution changes the discrete mass and conservation structure.

## 7. Consequences for the development phases

### Phase A: fixed-mesh solver

- The lack of Voronoi-face reconstruction is not a defect of the RD spatial
  operator.
- LDA's second-order convergence on the regular triangular mesh demonstrates
  that explicit MUSCL face reconstruction is not required for smooth spatial
  second order.
- The remaining first-order temporal error is in the F1 temporal-mass path,
  not in a missing centre-to-face reconstruction.
- B+RK2 remains excluded until its total-residual mass/blending formulation is
  available; therefore the current LDA RK2 path is not yet a complete
  shock-capturing production solver.

### Phase B: hierarchical timesteps

- Time interpolation for inactive/cross-bin vertices must be derived from the
  RD stage and mass formulation, not inherited automatically from the Hancock
  face predictor.
- A stored step context must distinguish `U^n`, stage states, increments,
  participating elements, and the time at which each state is valid.
- The unresolved F1 temporal order should not be hidden inside asynchronous
  interpolation.

### Phase C: moving mesh and integration with AREPO

- The cell-average versus nodal-value interpretation becomes a first-order
  design decision.
- ALE residuals, moving control volumes, and the geometric conservation law
  must be derived together.
- Only after choosing the evolved measure and state interpretation can one
  decide whether a gradient-based `x_c -> x_g` conversion is required.

## 8. Thesis-ready summary

The following paragraph can serve as a starting point for Chapter 4 after the
moving-mesh formulation has been completed and the unresolved statements above
have been replaced by final design choices:

> AREPO's standard hydrodynamics solver and the residual-distribution solver
> achieve spatial accuracy through different discrete constructions. In the
> finite-volume method, limited gradients reconstruct cell-averaged primitive
> variables from the centre of each Voronoi cell to a common face. A Hancock
> prediction advances the reconstructed states to the appropriate intermediate
> time, after which a one-dimensional Riemann problem supplies the conservative
> face flux. The RD method does not construct left and right states at Voronoi
> faces. Instead, the states associated with the vertices of each Delaunay
> simplex define a continuous piecewise-linear field within that element. The
> divergence of the multidimensional flux is integrated over the simplex to
> form a total residual, whose characteristic components are distributed
> conservatively among the vertices. Temporal centring is supplied by an
> explicit RD predictor/corrector and its scheme-dependent temporal mass
> residual. Thus, MUSCL reconstruction and RD interpolation play analogous
> roles in representing sub-element spatial variation, but they are not the
> same operation: one reconstructs states to codimension-one interfaces,
> whereas the other constructs and distributes a multidimensional element
> residual.

A second paragraph will be required to document the final AREPO coupling:

> A subtlety arises because AREPO naturally stores conserved averages over
> Voronoi cells, while the classical RD derivation assumes pointwise nodal
> degrees of freedom associated with a simplicial mesh and median-dual control
> volumes. On a centroidal static mesh these interpretations may be close, but
> on an irregular moving mesh the Voronoi centre, mesh generator, and Delaunay
> vertex need not coincide. A consistent moving-mesh implementation must
> therefore define the evolved integral measure, the mapping between cell
> averages and nodal states, the ALE mesh-velocity residual, and the discrete
> geometric conservation law as one coupled formulation.

## 9. Source map

### AREPO finite volume

- `src/main/run.c`
  - calls `calculate_gradients()` and exchanges primitive variables and
    gradients;
  - selects `compute_interface_fluxes()` when `RESIDUAL_DISTRIBUTION` is not
    enabled.
- `src/hydro/finite_volume_solver.c`
  - `face_get_state()`: obtains cell states and `x_face - x_cell-centre`;
  - `face_do_time_extrapolation()`: primitive-equation time prediction;
  - `face_do_spatial_extrapolation()`: gradient reconstruction to the face;
  - `compute_interface_fluxes()`: constructs left/right face states and invokes
    the face-flux machinery.

### Residual distribution

- `src/hydro/residual_distribution_solver.c`
  - reads the three vertex states of each Delaunay triangle;
  - constructs `Z_Roe`, `Z_avg`, `U_hat`, eigenvalue splits, and `Kmatrix`;
  - assembles `Phi = sum_i K_i U_hat_i`;
  - distributes the residual using LDA, N, or the legacy B blend;
  - under `RD_RK2_TOTAL_RESIDUAL`, advances `U^n -> U*` and applies the
    total-residual corrector without Taylor/gradient extrapolation;
  - without that switch, retains the legacy gradient-based time extrapolation.
- `src/hydro/update_primitive_variables.c`
  - under `RESIDUAL_DISTRIBUTION`, reconstructs density as
    `Mass / DualArea`, confirming the median-dual state interpretation.

### Thesis material

- `/home/zwu/MyThesis/Zhenyu-PhDThesis/zhenyu_thesis/chapter1/chapter1.tex`
  - Godunov-type methods and MUSCL--Hancock reconstruction.
- `/home/zwu/MyThesis/Zhenyu-PhDThesis/zhenyu_thesis/chapter3/chapter3.tex`
  - `P1` simplex interpolation, Roe-variable linearisation, element residuals,
    median-dual updates, and the open Voronoi-average/nodal-value note.

## 10. References for later Chapter 4 development

- Springel (2010): moving Voronoi finite-volume formulation in AREPO.
- Pakmor et al. (2016): time integration and gradient treatment used by the
  modern AREPO finite-volume solver.
- Deconinck and Ricchiuto (2017): residual-distribution review.
- Arpaia et al. (2015): explicit Runge--Kutta ALE residual distribution.
- Morton et al. (2023): the astrophysical RD implementation preceding the
  current AREPO integration.
- Gaburro, Ricchiuto, and Dumbser (2025 preprint): relation between
  multidimensional finite-volume corner fluxes and residual distribution on
  polygonal meshes.
