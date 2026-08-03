# Mathematical comparison of the current LDA+F1 Heun method and the Chapter-3 LDA RK2 formulation

## 1. Purpose and terminology

This note explains the equal-timestep method selected by
`RD_RK2_RATE_CONSISTENT_HEUN` and compares it with the LDA RK2 construction in
the thesis Chapter 3 subsection *Timestep condition and time integration*.
The comparison follows the notation and derivation order of Chapter 3,
especially equations

- `eq:RK2_first_step` and `eq:RK2_second_step`;
- `eq:RD_RK2_predictor`;
- `eq:RD_RK2_total_element_residual` and
  `eq:RD_RK2_total_nodal_residual`;
- `eq:RD_RK2_corrector`;
- `eq:RD_RK2_mass_choices` and `eq:RD_RK2_N_Heun`.

The phrase **standard LDA RK2** is potentially ambiguous. Three different
methods must be distinguished:

1. ordinary Heun applied to the spatial LDA residual with a diagonal lumped
   temporal mass;
2. the Chapter-3 Global-Lumping plus F1 (`GL+F1`) RK-RD
   predictor/corrector;
3. the current AREPO method, which first defines the approximate
   semi-discrete `GL+F1` rate and then applies ordinary Heun to that rate.

The current method is **not algebraically identical at finite timestep** to
method 2, and it is not method 1. Its most precise name is

> rate-consistent GL+F1 operator advanced by Heun.

It retains the LDA spatial residual and F1 temporal distribution, but changes
how they are organized in time.

## 2. Chapter-3 notation in assembled form

Let the nodal conserved state be `U`, and define the block-diagonal median-dual
matrix

$$
S = \operatorname{diag}(|S_i|I_m),
$$

where `m` is the number of conservation laws. For LDA, Chapter 3 gives

$$
\phi_i^{\mathrm{LDA},T}(U)
=\beta_i^T(U)\phi^T(U),
\qquad
\sum_{i\in T}\beta_i^T=I_m.
$$

Assemble the nodal spatial residual

$$
R_i(U)=\sum_{T\ni i}\phi_i^{\mathrm{LDA},T}(U),
$$

and define the first-order lumped LDA rate

$$
v(U)=-S^{-1}R(U).
\tag{1}
$$

With this notation, the Chapter-3 predictor
`eq:RD_RK2_predictor` is simply

$$
U^*=U^n+\Delta t\,v(U^n).
\tag{2}
$$

For the F1 mass choice in `eq:RD_RK2_mass_choices`,

$$
m_{ij}^{F1,T}(U)=\frac{|T|}{3}\beta_i^T(U),
\qquad j\in T.
$$

Therefore the assembled F1 mass operator acting on an arbitrary nodal vector
`w` is

$$
[M(U)w]_i
=
\sum_{T\ni i}
\beta_i^T(U)\frac{|T|}{3}
\sum_{j\in T}w_j.
\tag{3}
$$

It is useful to introduce the dimensionless operator

$$
C(U)=S^{-1}M(U).
\tag{4}
$$

For a diagonal lumped mass, `M=S` and hence `C=I`. For F1, `C` is generally
not the identity: it couples the rates at the three vertices of each triangle.

## 3. The Chapter-3 GL+F1 predictor/corrector

The nodal total residual in `eq:RD_RK2_total_nodal_residual` is

$$
\Phi_i^T
=
\sum_{j\in T}m_{ij}^T
\frac{U_j^*-U_j^n}{\Delta t}
+\frac{1}{2}
\left[
\phi_i^T(U^n)+\phi_i^T(U^*)
\right].
\tag{5}
$$

The Chapter-3 corrector `eq:RD_RK2_corrector` is

$$
U^{n+1}=U^*-\Delta t\,S^{-1}\Phi.
\tag{6}
$$

Let $M^\dagger$ denote the stage convention chosen for the F1 matrix in the
corrector. Chapter 3 does not put an explicit RK-stage superscript on `m_ij`;
the former AREPO path normally recomputed it from the predictor state, while
the earlier beta experiments tested other conventions. The main conclusion
below does not depend on which consistent convention is chosen.

Substituting equation (2) into equations (5)--(6) gives

$$
\begin{aligned}
U^{n+1}_{\mathrm{GL+F1}}
={}&U^*
-S^{-1}M^\dagger(U^*-U^n)
-\frac{\Delta t}{2}S^{-1}
\left[R(U^n)+R(U^*)\right] \\
={}&U^n+\Delta t
\left[
\frac{3}{2}v^n
+\frac{1}{2}v^*
-C^\dagger v^n
\right],
\end{aligned}
\tag{7}
$$

where

$$
v^n=v(U^n),
\qquad
v^*=v(U^n+\Delta t\,v^n).
$$

Equation (7) is the finite-step map implied by the Chapter-3 formula as it was
previously plumbed in AREPO.

### 3.1 Why the N or lumped-mass case becomes ordinary Heun

If `M=S`, then `C=I`, and equation (7) reduces exactly to

$$
U^{n+1}
=U^n+\frac{\Delta t}{2}(v^n+v^*),
\tag{8}
$$

which is `eq:RD_RK2_N_Heun` in Chapter 3. This is why the N scheme, and an LDA
control using a diagonal temporal mass, show second-order time convergence
with the original two-stage driver.

For F1, `C` is not the identity. The cancellation that produces equation (8)
does not occur.

## 4. The semi-discrete rate contained in GL+F1

Take the limit of equation (7) at fixed mesh as $\Delta t\to0$. Then
$v^*\to v$ and $C^\dagger\to C$, so

$$
\frac{U^{n+1}_{\mathrm{GL+F1}}-U^n}{\Delta t}
=2v(U^n)-C(U^n)v(U^n)+O(\Delta t).
$$

This identifies the approximate GL+F1 semi-discrete rate

$$
G(U)=2v(U)-S^{-1}M(U)v(U).
\tag{9}
$$

The current implementation starts from equation (9). It does not use the
lumped predictor in equation (2) as the physical RK predictor. Instead, it
first completes the whole rate `G(U^n)`.

### 4.1 Relation to the consistent-mass equation

The fully consistent semi-discrete equation would be

$$
M(U)\dot U+R(U)=0.
$$

Because `R=-Sv`, its exact rate is

$$
\dot U=M^{-1}Sv.
\tag{10}
$$

Write

$$
M=S(I+X).
$$

Then equation (10) gives

$$
\dot U_{\mathrm{consistent}}
=(I+X)^{-1}v
=v-Xv+X^2v-\cdots.
\tag{11}
$$

Equation (9), on the other hand, gives

$$
G=(I-X)v.
\tag{12}
$$

Thus GL+F1 is the first Neumann approximation to the consistent-mass inverse.
The new implementation does **not** solve the full consistent mass matrix. It
integrates the approximate rate `(I-X)v` consistently in time.

This also distinguishes it from plain LDA plus lumped-mass Heun, whose rate is
simply `v`.

## 5. The current rate-consistent Heun method

The current method applies the standard Chapter-3 Heun formulas
`eq:RK2_first_step` and `eq:RK2_second_step` to `G`, not to `v`:

$$
U^{(1)}=U^n+\Delta t\,G(U^n),
\tag{13}
$$

$$
U^{n+1}
=U^n+\frac{\Delta t}{2}
\left[G(U^n)+G(U^{(1)})\right].
\tag{14}
$$

This is an ordinary explicit two-stage RK2 method for the fixed-mesh ODE

$$
\dot U=G(U).
$$

Provided $G$ is sufficiently regular over the step, equations (13)--(14) have
local truncation error $O(\Delta t^3)$ and global temporal error
$O(\Delta t^2)$.

The important distinction is therefore:

$$
\boxed{
\text{Chapter-3 GL+F1: predictor with }v\text{, then one total-residual correction}
}
$$

versus

$$
\boxed{
\text{current method: construct }G\text{ at each physical stage, then apply Heun to }G
}.
$$

## 6. Why the two finite-step maps have different temporal order

Both methods have the same leading rate $G$ as $\Delta t\to0$, but this does
not make their finite-step maps equal.

For illustration, suppose `C` is locally constant. Expanding the Chapter-3 map
in equation (7) gives

$$
U^{n+1}_{\mathrm{GL+F1}}
=U^n+\Delta t\,G(U^n)
+\frac{\Delta t^2}{2}v'(U^n)v(U^n)
+O(\Delta t^3).
\tag{15}
$$

Heun applied to `G` gives instead

$$
U^{n+1}_{\mathrm{rate\text{-}Heun}}
=U^n+\Delta t\,G(U^n)
+\frac{\Delta t^2}{2}G'(U^n)G(U^n)
+O(\Delta t^3).
\tag{16}
$$

Since `G=(2I-C)v`, the second-order coefficients in equations (15) and (16)
are not equal in general. If `C` depends on `U`, derivatives of `C(U)` add
further unmatched terms. They coincide automatically in the lumped case
`C=I`, where `G=v`, but not for a general F1 mass operator.

Consequently, relative to the fixed-mesh ODE $\dot U=G(U)$, the former GL+F1
staging can have an $O(\Delta t^2)$ local defect and hence an
$O(\Delta t)$ global temporal error. The current method removes that mismatch
by evaluating the same complete operator `G` at both Heun stages.

This statement concerns **fixed-mesh temporal order**. The RK-RD literature
often discusses combined space-time consistency with $\Delta t$ scaled with
$h$; that is not identical to a method-of-lines timestep ladder at fixed $h$.
The AREPO Richardson experiment measures the latter.

## 7. Why four residual sweeps are still only two RK stages

AREPO stores integrated conserved quantities

$$
Q_i=|S_i|U_i.
$$

Each evaluation of `G(U)` is split into a spatial LDA sweep and an F1
mass-application sweep. Therefore two physical Heun stages require four
element sweeps.

| sweep | primitive state used | accumulator operation | meaning |
| --- | --- | --- | --- |
| 0 | $U^n$ | $Q\leftarrow Q^n+2\Delta t\,Sv^n$ | spatial part of $G(U^n)$ |
| 1 | still $U^n$ | $Q\leftarrow Q-\Delta t\,M^nv^n$ | closes $Q^*=Q^n+\Delta t\,SG^n$ |
| 2 | $U^*$ | start from $(Q^n+Q^*)/2$, then add $\Delta t\,Sv^*$ | spatial part of one-half $G(U^*)$ |
| 3 | still $U^*$ | subtract $(\Delta t/2)M^*v^*$ | closes the Heun average |

Algebraically,

$$
Q^*
=Q^n+2\Delta t\,Sv^n-\Delta t\,M^n v^n
=Q^n+\Delta t\,S G^n,
$$

and

$$
\begin{aligned}
Q^{n+1}
&=\frac{Q^n+Q^*}{2}
+\Delta t\,Sv^*
-\frac{\Delta t}{2}M^*v^* \\
&=Q^n+\frac{\Delta t}{2}S(G^n+G^*).
\end{aligned}
$$

The states after sweeps 0 and 2 are only algebraic accumulators. They are not
additional RK stages and are not converted into physical primitive states.
The two physical states are `U^n` and `U*`.

## 8. Conservation and constant-state preservation

F1 satisfies the elementwise column-conservation identity

$$
\sum_{i\in T}m_{ij}^{F1,T}=\frac{|T|}{3}I_m.
$$

After assembly this implies

$$
\mathbf{1}^T Mv=\mathbf{1}^T Sv.
$$

Therefore

$$
\mathbf{1}^T SG
=2\mathbf{1}^T Sv-\mathbf{1}^T Mv
=\mathbf{1}^T Sv.
$$

The new operator has the same global conserved rate as the original spatial
LDA update, including the appropriate boundary residual. Heun preserves this
linear conservation identity stage by stage. For a constant state, `R=0`, so
`v=0` and `G=0`; constant-state preservation is unchanged.

## 9. What changed and what did not

| property | Chapter-3 GL+F1 predictor/corrector | current LDA+F1 rate-Heun |
| --- | --- | --- |
| Spatial distribution | LDA | LDA |
| Temporal distribution | F1 | F1 |
| First physical predictor | $U^n+\Delta t\,v^n$ | $U^n+\Delta t\,G^n$ |
| F1 application | in the corrector | once in each evaluation of `G` |
| Operator sampled at both RK stages | no, unless `M=S` | yes |
| Number of physical RK stages | 2 | 2 |
| Number of element sweeps | 2 | 4 |
| Equivalent to ordinary Heun when `M=S` | yes | yes |
| Full consistent-mass solve | no | no |
| Fixed-mesh measured temporal order with F1 | approximately 1 in the old ladder | approximately 2 in both triangular and glass ladders |

The change fixes temporal integration of the chosen approximate operator. It
does not by itself change the spatial truncation error of `(I-X)v`, make LDA
positive near shocks, solve the exact consistent mass matrix, or define an
asynchronous multirate version.

## 10. Code correspondence

The mathematical pieces appear in
`src/hydro/residual_distribution_solver.c` as follows:

- `rd_rate_consistent_prepare_pass()` states equation (9), recovers `v`, forms
  the physical predictor, and resets the midpoint accumulator;
- `rd_pass_weight = {2,1,1,1/2}` supplies the four weights in Section 7;
- the third upwind right-hand side constructs
  `(|T|/3) sum_j v_j` for the F1 operation;
- the `LDA-F1-mass-apply` branch applies `M(U)v` with the same Roe/LDA state as
  the corresponding spatial sweep;
- `RD_RK2_RATE_CONSISTENT_HEUN` is rejected when hierarchical timesteps are
  enabled, because equations (13)--(14) currently require two synchronized
  global stage states.

The implementation also retains the rank-deficient conservative fallback. If
the F1 matrix is undefined on an element, its mass application is replaced by
the diagonal lumped form and counted in `f1_lumped`. The reported smooth
timestep ladders had `f1_lumped=0`, so their second-order result tests the F1
path itself rather than the fallback.

## 11. Suggested thesis presentation

Chapter 3 can retain equations `eq:RD_RK2_predictor` through
`eq:RD_RK2_corrector` as the published GL+F1 RK-RD construction. To describe
the current AREPO implementation accurately, Chapter 4 should then add:

1. the assembled definitions of `v`, `M`, and `G` in equations (1), (3), and
   (9);
2. the statement that AREPO advances $\dot U=G(U)$ with equations
   `eq:RK2_first_step` and `eq:RK2_second_step`;
3. the four-sweep realization in Section 7;
4. the fixed-mesh Richardson evidence that this reorganization restores
   second-order temporal convergence;
5. the caveat that `G=(I-X)v` remains a first Neumann approximation to the
   fully consistent rate `(I+X)^{-1}v`.

This wording avoids calling the current code merely "standard LDA RK2", which
would conceal both the F1 mass correction and the finite-step difference from
the Chapter-3 predictor/corrector.
