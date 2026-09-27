# Roe/Gauss residuals at zero velocity and what Arpaia specifies

Author: Codex, 2026-09-26. Follow-up to log 3 sections 115–116.
This is an independent mathematical clarification, not a thesis edit or a native
hydrodynamics validation. It distinguishes zero Roe mean velocity from zero
velocity at every node. Earlier counterexamples use the former.

## 1. Two residual definitions, before any matrix inversion

Set the mesh velocity to zero for this section. Let

\[
U_h=\sum_i\psi_iU_i,\qquad Z_h=\sum_i\psi_i Z_i,
\quad Z=\sqrt\rho(1,v_x,v_y,H)^T.
\]

The current Gauss residual quadratures the nonlinear flux of the P1 conservative
state. The conservative Roe construction instead has the identity

\[
\Phi_{G,\mathrm{exact}}=\oint_{\partial T}\mathcal F(U_h)\cdot n\,ds,
\qquad
\Phi_{\mathrm{Roe}}=\sum_iK_i\widehat U_i
=\oint_{\partial T}\mathcal F(U(Z_h))\cdot n\,ds,
\quad \widehat U_i=B(\bar Z)Z_i.
\]

Although both reconstructions interpolate the same nodes, U(Z_h) is generally
quadratic and differs from U_h. The Roe flux is quadratic in Z, so the latter
integral is exact for this reconstruction. Roe here is not merely a truncated
Taylor approximation to the same P1-U integral. Three-point Gauss quadrature is
not generally exact for P1-U Euler flux because of divisions by density.

Thus their difference exists independently of the invertibility of Sminus.
For full rank, LDA distributes whichever residual is supplied and its node sum
equals that residual. Differences can be higher order in smooth small-variation
limits, but need not be uniformly small for arbitrary element data.

## 2. Explicit matrices at zero Roe mean velocity

Assume a nondegenerate two-dimensional triangle, ideal-gas gamma > 1,
positive density/pressure, zero mesh velocity and

\[
\bar v=\bar Z_{2:3}/\bar Z_1=0,\quad
h=\bar H=\bar Z_4/\bar Z_1>0,\quad c^2=(\gamma-1)h.
\]

Write q=gamma-1. Nodal normals n_i point inward and have opposite-edge lengths.
The boundary normal in contour integrals points outward. Then

\[
K_i={1\over2}\begin{pmatrix}
0&n_{xi}&n_{yi}&0\\
0&0&0&q n_{xi}\\
0&0&0&q n_{yi}\\
0&h n_{xi}&h n_{yi}&0
\end{pmatrix}.
\]

Its eigenvalues are -c|n_i|/2, 0, 0, c|n_i|/2. Consequently
|K_i|=K_i^2/(c|n_i|/2). Since sum K_i=0,

\[
S^-:=\sum_iK_i^-=-{1\over2}\sum_i|K_i|.
\]

Let L=sum_i |n_i| and G=sum_i n_i n_i^T/|n_i|. G is positive definite.

\[
S^-=-{1\over4}\begin{pmatrix}
0&0&0&cL/h\\
0&cG_{xx}&cG_{xy}&0\\
0&cG_{xy}&cG_{yy}&0\\
0&0&0&cL
\end{pmatrix}.
\]

Hence rank(Sminus)=3, its right kernel is spanned by e_rho=(1,0,0,0)^T,
and its left kernel is spanned by ell=(-h,0,0,1)^T. The necessary and sufficient
condition for Sminus*x=b is

\[
b_E=h b_\rho.
\]

This constrains the algebraic right-hand side, not the physical state.

## 3. Roe and Gauss at zero mean velocity

For Roe, multiplication of the explicit K matrix gives

\[
\Phi_R=\begin{pmatrix}r_R\\\mathbf q_R\\h r_R\end{pmatrix},
\quad r_R={1\over2}\sum_i n_i\cdot\widehat{\mathbf m}_i,
\quad \mathbf q_R={\gamma-1\over2}\sum_i n_i\widehat E_i,
\]

where mhat_i=barZ1*(Zi2,Zi3) and
Ehat_i=(barZ4*Zi1+barZ1*Zi4)/gamma. Thus the Roe RHS is always compatible
under the assumptions of section 2.

For Gauss, with m_h the P1 conservative momentum, define

\[
p_h=(\gamma-1)\left(E_h-{|\mathbf m_h|^2\over2\rho_h}\right),
\quad H_h={E_h+p_h\over\rho_h}.
\]

The exact contour residual is

\[
\Phi_G=\oint_{\partial T}
\begin{pmatrix}
\mathbf m_h\cdot n\\
(\mathbf m_h\mathbf m_h^T/\rho_h+p_h I)n\\
H_h\mathbf m_h\cdot n
\end{pmatrix}ds.
\]

Every statement below also holds for the actual quadrature if each contour
integral is replaced by the same quadrature sum. Its compatibility defect is

\[
d=\Phi_{G,E}-h\Phi_{G,\rho}
=\oint_{\partial T}(H_h-h)\mathbf m_h\cdot n\,ds.
\]

Zero Roe mean velocity does not force this integral to vanish. In particular,
it neither forces the local momentum to vanish nor the local enthalpy to equal h.

## 4. What the Moore–Penrose pseudoinverse does

For the LDA formula used in this comparison,

\[
\phi_i=-K_i^+(S^-)^\dagger\Phi,
\quad \sum_i\phi_i=P\Phi,
\quad P=S^-(S^-)^\dagger
=I-{\ell\ell^T\over1+h^2}.
\]

The last expression uses the Euclidean norm in the chosen numerical conservative
coordinates. In physical units it must be interpreted after a variable scaling;
changing the relative scaling changes the least-squares projection of an
incompatible RHS. Compatibility itself does not change under an invertible
change of coordinates.

Writing d=Phi_E-h*Phi_rho,

\[
P\Phi=\begin{pmatrix}
\Phi_\rho+{h d\over1+h^2}\\
\Phi_{m_x}\\\Phi_{m_y}\\
\Phi_E-{d\over1+h^2}
\end{pmatrix}.
\]

Thus an incompatible Gauss residual changes both the mass and energy residual
in these coordinates, while retaining both momentum residuals. It is not
equivalent to replacing Gauss by Roe: compatible parts of their difference
remain. If Phi_G=Phi_R+delta, then P*Phi_G=Phi_R+P*delta.

For a compatible RHS, the inverse ambiguity is harmless. Any solution is
x=x0+alpha*e_rho, and every Kplus_i annihilates e_rho. The pseudoinverse chooses
one solution, leaving the distributed residual independent of alpha.

For completeness, put rstar=(b_rho+h*b_E)/(1+h^2). The explicit pseudoinverse is

\[
x_\rho=0,\quad \mathbf x_m=-{4\over c}G^{-1}\mathbf b_m,
\quad x_E=-{4h\over cL}r_*.
\]

The first component belongs to an intermediate algebraic vector; it is not a
claim that physical density vanishes. The corresponding node residual is

\[
\phi_{i,\rho}={|n_i|\over L}r_*+{1\over c}n_i^TG^{-1}\mathbf b_m,
\]
\[
\boldsymbol\phi_{i,m}={c\over L}n_i r_*+
{n_i n_i^T\over|n_i|}G^{-1}\mathbf b_m,
\quad \phi_{i,E}=h\phi_{i,\rho}.
\]

For the conventional Roe N scheme at this stagnation point, its inflow RHS
sum Kminus_i*Uhat_i is likewise compatible; the same right-kernel ambiguity
is annihilated by Kplus_i. N and LDA need not have the same individual node
residuals, but each sums to Phi_R.

## 5. All nodal velocities zero is a stronger condition

If every v_i=0 and the mesh is stationary, m_h=0 and p_h=(gamma-1)*E_h is P1.
The Gauss integral is exact and

\[
\Phi_G=\begin{pmatrix}
0\\ {1\over2}\sum_i p_i n_i\\0
\end{pmatrix},
\quad
\Phi_R=\begin{pmatrix}
0\\{\gamma-1\over2}\sum_i\widehat E_i n_i\\0
\end{pmatrix}.
\]

Both RHSs are compatible and a pseudoinverse loses neither total residual.
The pressure residuals can still differ due to their different reconstructions.
For triangle (0,0),(1,0),(0,1), gamma=7/5, rho=(1,4,9), p=(1,1,1), all v_i=0:

\[
\Phi_G=0,\qquad \Phi_R=(0,-7/36,-1/18,0)^T.
\]

The P1-U pressure is constant, whereas the P1-Z pressure is not constant within
this triangle. This example concerns the stated reconstructions, not all
possible Roe-family methods. If density is also constant, these pressure
residuals agree even when the nodal pressures differ.

By contrast, the earlier example has only mean velocity zero:
rho_i=p_i=1, v_i=(1,0),(0,1),(-1,-1). It gives h=25/6,

\[
\Phi_R=(-1,0,1/14,-25/6)^T,\quad
\Phi_G=(-1,0,1/10,-257/60)^T,\quad d=-7/60.
\]

Here three-point Gauss is already exact. Its projected sum is approximately
(-1.026475037821483,0,0.1,-4.276979324256178), which differs from both targets.

For moving meshes, the relevant characteristic stagnation is barv-barsigma=0.
Physical barv=0 alone does not imply that ALE Sminus has the matrix above.
The mixed-reconstruction Roe correction C=-int sigma_h dot grad(U_h-Uhat_h)
also remains separate: adding C to an LDA target can destroy compatibility.
See the previous report for the explicit moving counterexample and N's
outside-the-solve C/3 contribution. These spatial statements do not settle the
separate temporal mass-matrix RHS compatibility problem.

## 6. Arpaia: evidence and the limit of what can be inferred

Primary source: Arpaia & Ricchiuto, J. Sci. Comput. 63, 502–547 (2015),
DOI 10.1007/s10915-014-9910-5; local final journal PDF in MyThesis/useful_resources.

- Section 3.3.1, printed pp. 508–509, Eq. (30), allows direct nonlinear contour
  integration or an exact mean-Jacobian representation. Its main derivation
  here is scalar. The paragraph after Eq. (33) explicitly adopts the locally
  linearized representation for subsequent analysis without specifying that
  every implementation must obtain it through exact Jacobian integration.
- Section 6.1, printed pp. 533–534, describes a formal systems extension,
  matrix upwind parameters, eigenvalue splitting, and characteristic limiting.
  It refers to [14,24,35,36] for further implementation details. It does not
  specify Euler volume-Jacobian quadrature, a Gauss rule for the spatial
  residual, or our P1-U/P1-Z mixed reconstruction and correction.
- Section 6.2 actually solves the full nonlinear Euler system. This does not
  establish an absence of local linearization for upwinding.

An additional primary source is the author-uploaded public manuscript of their
reference [14], Ricchiuto & Abgrall, *Explicit Runge–Kutta residual distribution
schemes for time dependent problems: second order case* (2010). Section 5.1,
Eqs. (51)–(52), explicitly evaluates the upwind Jacobian at the arithmetic
average of nodal states, with matrix signs computed by eigendecomposition.
This is not the exact element integral of the Euler Jacobian for P1-U data.
It supports separating residual evaluation from upwind-matrix construction;
it does not by itself establish the exact 2015 Euler implementation choices.

Author-uploaded manuscript inspected at:
https://www.researchgate.net/publication/223033482_Explicit_Runge-Kutta_Residual_Distribution_schemes_for_Time_Dependent_Problems_second_order_case

Chapter 3's pre-Roe identity remains mathematically correct:

\[
\oint_{\partial T}\mathcal F(U_h)\cdot n\,ds
=|T|(\langle A_x(U_h)\rangle\partial_xU_h+
\langle A_y(U_h)\rangle\partial_yU_h).
\]

It is not necessary to compute either average matrix to obtain the left-hand
side: integrate the nonlinear edge flux directly. Nor is a single-state
Jacobian generally equal to that exact average. Therefore the supported
description is that Arpaia permits nonlinear residual evaluation and uses
local characteristic matrices for distribution. The claim that Arpaia
actually integrates exact Euler Jacobian matrices and does no linearization
is not supported by the inspected paper.

## 7. Verification and scope

Archive: ../local_runs/chapter4_2_zero_velocity_20260926_v1/.
The independent NumPy script checks the explicit Sminus matrix, projector,
pseudoinverse solution, each node residual, Roe N closure, and equality between
the Roe algebra and contour integration of P1-Z for three cases. All algebraic
checks pass at 2e-14 absolute tolerance; Roe/P1-Z contour discrepancies are
at most 8.89e-16. The first script invocation reached all three case checks
but failed in a final assertion wrapper because abs() received a Python list;
converting it to an array fixed the harness, without changing any formulas.

No hydro tests, solver edits, thesis edits, compilation, commit, or sync.
Chapter4.tex SHA256 remains
b3d3e7209a4d7e166c85452f2e4d8f55ead12cc3c0aabbc8fcb65152f939f64b.
