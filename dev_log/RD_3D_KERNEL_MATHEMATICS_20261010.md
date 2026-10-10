# 2D/3D Euler kernel: conventions and independent checks

Author: Codex, 2026-10-10. User authorised incremental 3D integration and
commits at validated milestones. No thesis edits.

## 1. Sources and the convention that the code must enforce

Read the current thesis `zhenyu_thesis/chapter3/chapter3.tex`, especially
`eq:RD_3D_K_matrix`, `eq:RD_linearised_conserved_state`, and the stagnation
nullspace discussion. Compare [Paardekooper 2017](https://arxiv.org/abs/1705.02028),
§3.2 equations 35–39 and Appendix A (arXiv PDF pp.10,34–35), and
[Morton et al. 2023](https://arxiv.org/abs/2204.01757), Appendices A3 and B
(arXiv v2 PDF pp.20–21; published DOI 10.1093/mnras/stac3427). The matrix
appendix pages were also rendered and inspected. Copies and rendered pages:
`../local_runs/rd_3d_integration_20261010_v1/references/`.

Use three distinct geometric quantities on a d-simplex T:

\[
 \widehat n_i = \text{unit normal pointing into T from its opposite face},\qquad
 a_i = |\text{opposite face}|,\qquad n_i=a_i\widehat n_i.
\]

Then

\[
 \nabla\psi_i=\frac{n_i}{d|T|},\quad
 K_i=\frac{a_i}{d}A(\widehat n_i;\bar Z),\quad
 m_i^T=\frac{|T|}{d+1}.
\]

The **3D coefficients are face area/3 and volume/4**, respectively. Cross
products of two face edges have magnitude **twice** the triangular face area;
the tetra determinant is **six** times the volume. AREPO's function named
`calculate_tetra_volume` returns this determinant, so its name alone is not
a unit convention. The thesis's scaled normals are unambiguous here.

Paardekooper's appendix eigenvalues `w±c` and component formula require unit
normals; geometric scaling belongs outside that directional matrix. Morton's
Appendix B explicitly calls the normal a unit vector, but omits the face-area
factor in its initial K definition and the overall geometric factor in the
displayed entries. Interpret those entries as the directional spectral matrix,
then multiply by `a_i/3`. The old standalone `triangle3D.h` does precisely this
with `NORM * MAG[m]`, `NORM=1/3`. Copying just the paper's printed entries into
an element residual would give the wrong physical dimensions and mesh scaling.

There is also a notation inconsistency in both appendices: if R contains
right eigenvectors as **columns**, the diagonalisation is `A=R Λ R^{-1}`.
The reversed product printed in the prose is not that convention. The code
uses verified spectral functions, without explicitly forming an inverse of R.
Morton's repeated `lambda_1` label for the negative acoustic branch is likewise
read as the second acoustic eigenvalue. These are source-reading corrections,
not evidence that the standalone component formula is wrong.

## 2. Dimension-independent directional algebra

Order the conserved state as `rho, rho*v[0:d], E`; energy has index `d+1`.
Let `g=gamma-1`, `q=v·v/2`, `w=v·nhat`, `alpha=g*q`, and
`c²=g*(H-q)`. Direct differentiation of the Euler flux gives

\[
 A(\widehat n)=
 \begin{pmatrix}
 0 & \widehat n^T & 0\\
 \alpha\widehat n-wv & wI+v\widehat n^T-g\widehat n v^T & g\widehat n\\
 (\alpha-H)w & H\widehat n^T-gwv^T & \gamma w
 \end{pmatrix}.
\]

Its acoustic speeds are `w+c,w-c`; the repeated speed `w` represents entropy
plus **d−1 shear modes**. Reusing the two-dimensional single-tangent eigenbasis
in 3D would miss one shear mode. The component formula now in `rd_euler.c`
includes the full momentum block, so it needs no chosen tangent basis.

For constant element mesh velocity sigma, `A_sigma=A−(sigma·nhat)I` has the
same projectors. Only the eigenvalues are shifted; the eigenvectors still
depend on the fluid velocity in the selected frame. With
`B=(A−wI)/c`, independent projectors are

\[
 P_+=\tfrac12(B^2+B),\quad P_-=\tfrac12(B^2-B),\quad P_0=I-B^2.
\]

Thus `K^±=(a/d) sum_r max/min(lambda_r,0) P_r`. This gives an independent
oracle for all 4×4/5×5 component entries, including moving-frame shifts.
It checks `K+ + K− = K`, geometric scaling and rotational covariance without
copying the production formula into Python. Validating this directional ALE
algebra does **not** validate moving tetra time integration or remapping.

## 3. Roe linearisation and residual assembly

Use `Z=(sqrt(rho),sqrt(rho)*v,sqrt(rho)*H)` and the arithmetic mean of Z
over **d+1 vertices**. The Roe velocity and enthalpy are `Zbar_m/Zbar_0`
and `Zbar_E/Zbar_0`. The linearised conserved state is `Uhat_i=Bbar Z_i`:

\[
 \widehat U_{i,\rho}=2\bar Z_0 Z_{i,0},\qquad
 \widehat U_{i,m_a}=\bar Z_{m_a}Z_{i,0}+\bar Z_0Z_{i,m_a},
\]
\[
 \widehat U_{i,E}=\frac{\bar Z_EZ_{i,0}+\bar Z_0Z_{i,E}
       +(\gamma-1)\sum_a\bar Z_{m_a}Z_{i,m_a}}{\gamma}.
\]

`Phi=sum_i K_i Uhat_i` is the exact integrated Euler residual of a **P1 Z**
field, because the flux is quadratic in Z. It is not generally the contour
flux of P1 U. In 3D a triangular-face quadrature exact for degree two provides
an independent integral check. `Uhat` is not the original nodal state;
for a uniform state it is `2U`. Do not insert another factor 1/2 in Phi or
the N distribution to compensate for this: the geometric gradient and
quadratic flux derivative already fix the coefficient.

For N, `Sminus=sum_i K_i^-`, `b=sum_i K_i^- Uhat_i`, solve `Sminus*y=b`,
and distribute `phi_i=K_i^+(Uhat_i−y)`. A common shift of every Uhat can be
subtracted before assembly, using `sum_i K_i=0`; this makes uniform states
exactly quiet without altering the mathematical residual. The standalone
stage's `0.5` multiplier belongs to its time-integration convention; it is
not part of the spatial K or N definition.

## 4. Singular solves and verification boundaries

`rd_linalg.c` extracts the existing LU/DGELSD policy and accepts dimension
4 or 5. The pivot spread threshold `1e-12` chooses the solver, while
`RD_SVD_RCOND=-1` leaves numerical rank to LAPACK's machine-precision default.
No diagonal shift, explicit inverse, state clipping or successful exit on
failure is imported from the standalone code.

At zero fluid velocity on a nondegenerate tetrahedron the common nullspace
is the density direction; Sminus has rank four, not two. Although each face
has three stationary fields, their shear nullspaces do not coincide over
all face directions. A least-squares return code alone does not prove that
`Sminus*y=b` is consistent: verify its residual and the uncorrected element
conservation identity. An incompatible manufactured RHS is a negative test.

Milestone 1 algebra: `tests/rd/test_euler_dimensions.py` compiles the actual
C kernels and tests 800 states in 2D/3D, gamma 1.4 and 5/3, all three spectral
choices, zero and finite velocities, ALE shifts, random rotations, face
scaling, planar reduction and 4/5-component LU/SVD solves with several RHSs.
Largest normalized K defect against the independent flux-derivative oracle:
**1.903e-15**. Existing `make check_rd` tests also passed after extraction.
Native regressions and later integration milestones are recorded in log 3.

## 5. Native tetra integration and module boundaries

Milestone 1 is commit `dd7a31b`. Milestone 2 adds explicit `RD_3D_STATIC` and
the following modules, retaining the common AREPO stage orchestration:

- `src/hydro/rd_euler.c`: dimension-aware directional K and a pure static N
  element distribution, without AREPO storage or a time-step factor.
- `src/hydro/rd_linalg.c`: four/five-component LU and rank-revealing SVD.
- `src/mesh/rd_simplex_geometry.c`: signed simplex measure, inward unit face
  normals and face measures; accepts already-unfolded periodic coordinates.
- `src/hydro/rd_state.c`: common equal-step stage snapshots, primitive
  recovery and corrector preparation. No primitive floor is applied here.
- `src/hydro/rd_dimensions.h`: storage dimensions available before AREPO's
  `voronoi.h` defines DIMS. Spatial dimension, number of vertices, number of
  equations and energy index are separate quantities.

The native adapter uses AREPO's DP coordinates, including their periodic
images, and requires positive tetra orientation. A triangle routine must not
be made three-dimensional just by extending its loop limits. In particular,
AREPO's deleted 3D tetra slots have `DT[i].t[0] < 0` but may retain stale
vertex indices; they must be excluded from physical element enumeration.
Coverage and uniform-state tests catch the consequent duplicate-volume risk.

The first supported path is periodic, source-free, gas-only, non-comoving,
one rank, static full mesh, equal steps, N with the lumped RK2 mass. Its
corrector element term is

\[
  \frac{|T|}{4}\frac{U_i^*-U_i^n}{\Delta t}
  +\frac12\phi_i^T(U^*).
\]

Together with the existing local `+1/2 (Q*−Qn)` preparation, this is the
two-stage lumped update, without importing the standalone half-step convention.
All three momenta participate in storage, stage recovery and final updates.
The three-dimensional CFL additionally bounds each nodal step by
`CourantFac * M_i / sum_{T incident on i} max_j[(a_j/3)(c+|v·nhat_j|)]`, using
the same Roe element state and `M_i=sum_T |T|/4`. It supplements AREPO's
Voronoi/tree restriction. These mild gates do not establish positivity for
arbitrary N-scheme data or distorted meshes.

`test_simplex_kernels.py` compiles the production C kernels and checks 700
random triangles/tetrahedra, both orientations and gamma=1.4/5/3. The total
P1-Z residual is compared with independent exact face quadrature (two-point
Gauss on an edge, degree-two three-point quadrature on a triangle). Largest
normalized defects: closure 1.763e-16, linear-gradient identity 4.582e-15,
integrated residual 4.441e-15, raw N conservation 6.715e-17 and solve
compatibility 7.630e-17. Seventy nonuniform zero-velocity cases exercise ranks
three/four in 2D/3D. Uniform residuals are exactly zero in the pure kernel.

## 6. Native evidence, provenance and limitations

Final numerical campaign: `../local_runs/rd_3d_integration_20261010_v1/native_static_v3/`.
Reproducer and configuration: [3D example README](../examples/rd_3d/README.md),
`tests/rd/run_3d_static_gates.py` and `examples/rd_3d/Config_N_static.sh`.
The unit cube has gamma=1.4, periodic boundaries, one rank and double precision.
Each n³ Cartesian grid is jittered by ±0.12/n in each coordinate using seed
912+n; n=8 gives 512 nodes/3552 tetrahedra, n=16 gives 4096/28419. Every case
reaches t=1/32 with snapshots at 0, 1/64 and 1/32. Both thread limits are one.

Advection uses `rho=1+0.1 product_a sin(2 pi x_a)`, p=1 and v=(.3,−.2,.4),
compared with the exact translated density at the actual final coordinates
and time. Pressure-rest uses rho=1, v=0 and
`p=1+0.01 product_a cos(2 pi x_a)`; it is a nonuniform dynamical test, not a
steady solution. Its first predictor triggers 3552 rank-four SVD solves.

| Case | Actual dt / number of steps | Maximum normalized global conservation defect | Density L1 |
| --- | --- | --- | --- |
| 8³ uniform rest | 1/512 / 16 | 6.509e-19 | — |
| 8³ uniform flow | 1/512 / 16 | 0 | — |
| 8³ pressure perturbation, initial v=0 | 1/512 / 16 | 1.111e-15 | — |
| 8³ density advection | 1/512 / 16 | 6.662e-16 | 2.054116219e-3 |
| 16³ density advection | 1/2048 / 64 | 1.444e-15 | 1.222963234e-3 |
| 16³ density advection, smaller cap | 1/4096 / 128 | 2.015e-15 | 1.222963308e-3 |
| 8³ advection, always SVD | 1/512 / 16 | 4.441e-16 | 2.054116219e-3 |

Conservation is measured for `(M,Px,Py,Pz,E)` over all saved snapshots, relative
to the initial sum of absolute nodal amounts; momentum denominators are at
least the total mass so a zero momentum has a meaningful absolute scale.
Density L1 is `sum_i Mdual_i |rho_i-rho_exact_i|` (box volume is one); L2 uses
the same volume weights. Global median-dual coverage differs from unity by
at most 1.111e-16. Uniform rho/v/p defects are at most 5.552e-16. All recorded
states and both RK stages stay positive and finite, and coordinates stay fixed.

LU/fallback versus always-SVD fields agree within 8.882e-16. Halving the actual
16³ timestep changes rho/v/p by at most 2.696e-8 / 6.555e-10 / 1.460e-9.
The two-grid L1 ratio is 1.6796 (an apparent exponent 0.7481); this is an initial
decreasing-error trend on two jittered grids, **not** a measured asymptotic
convergence order. N is the spatial first-order baseline.

The final two-dimensional regression (`regression2d_final/`) compares against
the frozen pre-integration commit `4b40f75`: static N/LDA and moving N
equal/natural, each on uniform random and Yee48 with 2304 nodes to t=.015625.
All eight candidate runs pass. Maximum matched rho/v/p difference is
2.443e-15, coordinate difference 4.441e-16 and integrated total difference
4.441e-16. Moving configurations retain high transfer mode 1 with lazy off.
The full final `make check_rd` also passes (`check_rd_final.log`). This is a
short regression, not a revalidation of every historical 2D configuration.

Failed/setup attempts are preserved: `native_static_v1` failed compilation
because mesh storage referenced DIMS before its definition; the dedicated
dimension header fixes that include-order issue. `native_static_v2` ran seven
cases, but its two nominal timestep caps were both overridden by the same
CFL limit. Those identical timelines supply no timestep-sensitivity evidence.
Version 3 lowers the second cap and asserts the **actual** factor-two step
change. Final cleanup only changed comments/formatting and removed unreachable
3D fragments inside guarded 2D ALE functions. `final_source/equivalence.json`
verifies identical preprocessed numerical code against the frozen native
binaries for all six configurations; only diagnostic `__LINE__` values and
whitespace are neutralized. The final frozen sources and hashes are archived.

This completes an initial **static** three-dimensional N integration. Moving
3D conservation transfer, GCL/time-integrated tetra geometry, LDA/B, hierarchical
time stepping, MPI agreement, strong shocks and long-run stability remain
unimplemented or unvalidated on this path. A cubic-in-time tetra volume cannot
reuse a 2D endpoint-average mesh-flux formula; the next moving gate needs a
consistent time quadrature and full conservative reconnection-cavity transfer.
The earlier feasibility report's model evidence is not native 3D evidence.
