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
