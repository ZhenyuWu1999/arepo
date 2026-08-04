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
\tag{1}
$$

where `m` is the number of conservation laws. For LDA, Chapter 3 gives

$$
\phi_i^{\mathrm{LDA},T}(U)
=\beta_i^T(U)\phi^T(U),
\qquad
\sum_{i\in T}\beta_i^T=I_m.
\tag{2}
$$

Assemble the nodal spatial residual

$$
R_i(U)=\sum_{T\ni i}\phi_i^{\mathrm{LDA},T}(U),
\tag{3}
$$

and define the first-order lumped LDA rate

$$
v(U)=-S^{-1}R(U).
\tag{4}
$$

With this notation, the Chapter-3 predictor
`eq:RD_RK2_predictor` is simply

$$
U^*=U^n+\Delta t\,v(U^n).
\tag{5}
$$

For the F1 mass choice in `eq:RD_RK2_mass_choices`,

$$
m_{ij}^{F1,T}(U)=\frac{|T|}{3}\beta_i^T(U),
\qquad j\in T.
\tag{6}
$$

Therefore the assembled F1 mass operator acting on an arbitrary nodal vector
`w` is

$$
[M(U)w]_i
=
\sum_{T\ni i}
\beta_i^T(U)\frac{|T|}{3}
\sum_{j\in T}w_j.
\tag{7}
$$

It is useful to introduce the dimensionless operator

$$
C(U)=S^{-1}M(U).
\tag{8}
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
\tag{9}
$$

The Chapter-3 corrector `eq:RD_RK2_corrector` is

$$
U^{n+1}=U^*-\Delta t\,S^{-1}\Phi.
\tag{10}
$$

Let $M^\dagger$ denote the stage convention chosen for the F1 matrix in the
corrector. Chapter 3 does not put an explicit RK-stage superscript on `m_ij`;
the former AREPO path normally recomputed it from the predictor state, while
the earlier beta experiments tested other conventions. The main conclusion
below does not depend on which consistent convention is chosen.

Substituting equation (5) into equations (9)--(10) gives

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
\tag{11}
$$

where

$$
v^n=v(U^n),
\qquad
v^*=v(U^n+\Delta t\,v^n).
\tag{12}
$$

Equation (11) is the finite-step map implied by the Chapter-3 formula as it was
previously plumbed in AREPO.

### 3.1 Why the N or lumped-mass case becomes ordinary Heun

If `M=S`, then `C=I`, and equation (11) reduces exactly to

$$
U^{n+1}
=U^n+\frac{\Delta t}{2}(v^n+v^*),
\tag{13}
$$

which is `eq:RD_RK2_N_Heun` in Chapter 3. This is why the N scheme, and an LDA
control using a diagonal temporal mass, show second-order time convergence
with the original two-stage driver.

For F1, `C` is not the identity. The cancellation that produces equation (13)
does not occur.

## 4. The semi-discrete rate contained in GL+F1

Take the limit of equation (11) at fixed mesh as $\Delta t\to0$. Then
$v^*\to v$ and $C^\dagger\to C$, so

$$
\frac{U^{n+1}_{\mathrm{GL+F1}}-U^n}{\Delta t}
=2v(U^n)-C(U^n)v(U^n)+O(\Delta t).
\tag{14}
$$

This identifies the approximate GL+F1 semi-discrete rate

$$
G(U)=2v(U)-S^{-1}M(U)v(U).
\tag{15}
$$

The current implementation starts from equation (15). It does not use the
lumped predictor in equation (5) as the physical RK predictor. Instead, it
first completes the whole rate `G(U^n)`.

### 4.1 Relation to the consistent-mass equation

The fully consistent semi-discrete equation would be

$$
M(U)\dot U+R(U)=0.
\tag{16}
$$

Because `R=-Sv`, its exact rate is

$$
\dot U=M^{-1}Sv.
\tag{17}
$$

Write

$$
M=S(I+X).
\tag{18}
$$

Then equation (17) gives

$$
\dot U_{\mathrm{consistent}}
=(I+X)^{-1}v
=v-Xv+X^2v-\cdots.
\tag{19}
$$

Equation (15), on the other hand, gives

$$
G=(I-X)v.
\tag{20}
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
U^{(4)}=U^n+\Delta t\,G(U^n),
\tag{21}
$$

$$
U^{n+1}
=U^n+\frac{\Delta t}{2}
\left[G(U^n)+G(U^{(4)})\right].
\tag{22}
$$

This is an ordinary explicit two-stage RK2 method for the fixed-mesh ODE

$$
\dot U=G(U).
\tag{23}
$$

Provided $G$ is sufficiently regular over the step, equations (21)--(22) have
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
in equation (11) gives

$$
U^{n+1}_{\mathrm{GL+F1}}
=U^n+\Delta t\,G(U^n)
+\frac{\Delta t^2}{2}v'(U^n)v(U^n)
+O(\Delta t^3).
\tag{24}
$$

Heun applied to `G` gives instead

$$
U^{n+1}_{\mathrm{rate\text{-}Heun}}
=U^n+\Delta t\,G(U^n)
+\frac{\Delta t^2}{2}G'(U^n)G(U^n)
+O(\Delta t^3).
\tag{25}
$$

The exact solution of the same ODE expands as

$$
U(t^n+\Delta t)
=U^n+\Delta t\,G(U^n)
+\frac{\Delta t^2}{2}G'(U^n)G(U^n)
+O(\Delta t^3).
\tag{26}
$$

Comparing term by term is what decides the order, and this is where the two
maps separate. **Writing an expansion to $O(\Delta t^3)$ is not the same as
being second-order accurate.** Second order requires the $\Delta t^2$
coefficient to equal the one in the exact expansion. Equation (25) matches it
identically. Equation (24) does not, so its local truncation error is

$$
\tau
=\frac{\Delta t^2}{2}
\left[v'(U^n)v(U^n)-G'(U^n)G(U^n)\right]
=O(\Delta t^2),
\tag{27}
$$

which is one power short of the $O(\Delta t^3)$ that a second-order method
requires. A local defect of $O(\Delta t^2)$ accumulated over $O(1/\Delta t)$
steps gives a global error of $O(\Delta t)$: the measured first order.

To leading order in `X`,
$v'v-G'G=Xv'v+v'Xv+O(\lVert X\rVert^2)$. The defect therefore vanishes
**identically** when `X=0`, which is the lumped or N case, and otherwise
carries a coefficient proportional to $\lVert X\rVert$. It is small, not
absent, for a mass operator close to diagonal. Both statements are confirmed
numerically in Section 12.

Since `G=(2I-C)v`, the second-order coefficients in equations (24) and (25)
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
\tag{28}
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
\tag{29}
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
\tag{30}
$$

The states after sweeps 0 and 2 are only algebraic accumulators. They are not
additional RK stages and are not converted into physical primitive states.
The two physical states are `U^n` and `U*`.

## 8. Conservation and constant-state preservation

F1 satisfies the elementwise column-conservation identity

$$
\sum_{i\in T}m_{ij}^{F1,T}=\frac{|T|}{3}I_m.
\tag{31}
$$

After assembly this implies

$$
\mathbf{1}^T Mv=\mathbf{1}^T Sv.
\tag{32}
$$

Therefore

$$
\mathbf{1}^T SG
=2\mathbf{1}^T Sv-\mathbf{1}^T Mv
=\mathbf{1}^T Sv.
\tag{33}
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

- `rd_rate_consistent_prepare_pass()` states equation (15), recovers `v`, forms
  the physical predictor, and resets the midpoint accumulator;
- `rd_pass_weight = {2,1,1,1/2}` supplies the four weights in Section 7;
- the third upwind right-hand side constructs
  `(|T|/3) sum_j v_j` for the F1 operation;
- the `LDA-F1-mass-apply` branch applies `M(U)v` with the same Roe/LDA state as
  the corresponding spatial sweep;
- `RD_RK2_RATE_CONSISTENT_HEUN` is rejected when hierarchical timesteps are
  enabled, because equations (21)--(22) currently require two synchronized
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

1. the assembled definitions of `v`, `M`, and `G` in equations (4), (7), and
   (15);
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

## 12. How the temporal order was measured, and what came out

### 12.1 The fixed-mesh Richardson procedure

The order in Section 6 is a **method-of-lines temporal order**: the mesh is
held fixed and only $\Delta t$ varies.

1. One mesh, one initial condition, one final time. The advected Yee vortex
   with `boost = 1` and `TimeMax = 1`, on a regular triangular lattice at
   `n = 64` and on a tiled Swift glass at `n = 48`.
2. Four runs with `MaxSizeTimestep = 1/256, 1/512, 1/1024, 1/2048`. That the
   requested step actually binds is checked rather than assumed: each run must
   take exactly 256, 512, 1024 or 2048 steps. If `MaxSizeTimestep` sits above
   the CFL limit the ladder silently becomes four copies of the same run.
3. Final states matched by `ParticleIDs`, never by storage order. The compared
   state is $U=(\rho,\rho v_x,\rho v_y,\rho E)$ under one common `DualArea`
   weight for the whole ladder.
4. Adjacent differences
   $D_0=\lVert U_{1/256}-U_{1/512}\rVert$,
   $D_1=\lVert U_{1/512}-U_{1/1024}\rVert$,
   $D_2=\lVert U_{1/1024}-U_{1/2048}\rVert$.
5. Observed order $p_k=\log_2\!\left(D_k/D_{k+1}\right)$.

Adjacent differences are used rather than an error against a reference because
at fixed mesh the $\Delta t\to0$ limit is the *semi-discrete* solution, which is
not available in closed form. The construction cancels it: if
$E(\Delta t)=E_\infty+C\,\Delta t^p$ then
$D_k=C\,\Delta t_k^p\,(1-2^{-p})$, so $D_k/D_{k+1}=2^p$ regardless of
$E_\infty$.

Each run additionally reports `f1_lumped`, the predictor density and pressure
minima, and the element conservation defect, so that a clean order cannot be
claimed from a run that silently fell back to the lumped mass or lost
positivity. In every ladder quoted below `f1_lumped = 0`, predictors stayed
positive, and global mass and energy drift stayed at round-off.

### 12.2 Solver results

| method | mass operator | mesh | $p_0$ | $p_1$ |
| --- | --- | --- | ---: | ---: |
| Chapter-3 GL+F1, equation (11) | F1 | triangular `n=64` | 0.987 | 0.994 |
| | F1 | glass `n=48` | 0.983 | 0.991 |
| | F1 | jittered `n=64` | 0.993 | 0.997 |
| N / lumped, equation (13) | `M=S` | jittered `n=64` | 1.9996 | 2.0031 |
| rate-consistent Heun, equations (21)--(22) | F1 | triangular `n=64` | 2.000448 | 2.000294 |
| | F1 | glass `n=48` | 2.000116 | 2.000304 |

Three readings. The GL+F1 staging is first order on every mesh family tried,
and the value is **mesh independent**, which distinguishes this defect from the
spatial mass-matrix ceiling whose coefficient scales with the median-dual patch
asymmetry. The lumped case is second order, as equation (27) requires with
`X=0`. The rate-consistent form recovers second order to four decimal places on
both a regular lattice and the thesis-relevant glass.

Changing which stage $\beta$ is evaluated at does not affect this. Three
conventions -- mixed, coherent $\beta^n$ and coherent $\beta^*$ -- were built
and laddered separately and all returned $p\approx0.993$, which is expected
from Section 6: the mismatch is between $v$ and $(I-X)v$, not between
$\beta^n$ and $\beta^*$.

### 12.3 Minimal-ODE confirmation

Before the solver change, the same statement was gated on a one-dimensional
analogue of the element structure: two nodes per element,
$m_{ij}=(h/2)\beta_i^e$ independent of $j$ so that the column sum is
$(h/2)I$, $S_i=h$, element residual $\Phi^e=f(U_{i+1})-f(U_i)$ distributed as
$\phi_i^e=\beta_i^e\Phi^e$. The map of equation (11) and Heun applied to `G`
were both integrated against a reference solution of $\dot U=G(U)$.

| $\beta$ | $\lVert X\rVert$ | equation (11) | Heun on `G` |
| --- | ---: | --- | --- |
| $1/2$, centred | 0.0028 | 1.015, 1.003, 1.001 | 2.000, 2.000, 2.000 |
| $0.8$, upwind biased | 0.0131 | 0.977, 0.989, 0.994 | 2.000, 2.000, 2.000 |
| $1$, full upwind | 0.0216 | 0.988, 0.994, 0.997 | 2.000, 2.000, 2.000 |

Two conclusions that the solver ladders alone do not give. The defect appears
for a **centred** $\beta$ as well, so it is not a consequence of upwind bias:
any non-lumped mass operator under this staging is first order in time, and
$\lVert X\rVert$ sets only the coefficient. And the error magnitude grows with
$\lVert X\rVert$ -- at 500 steps it is `4.8e-4`, `1.9e-3`, `3.1e-3` down the
table, against `7.2e-5` for the rate-consistent form throughout -- exactly as
equation (27) predicts.

### 12.4 Why this does not contradict the published construction

The measurement is a fixed-mesh temporal order. The RK-RD literature presents
combined space-time convergence with $\Delta t$ scaled to $h$, and in that
presentation the defect is nearly invisible.

Measured in the production ladder ($\Delta t=0.25/n$), the GL+F1 temporal
contribution was 1 to 2 per cent of the total error and behaved like
$h^{1.75}$ rather than $h$, because its coefficient $C(h)$ itself shrinks
roughly like $h^{0.75}$. Removing it by extrapolating each rung to
$\Delta t\to0$ changed the measured spatial order by less than 0.01.

So the published GL+F1 construction is not wrong as presented. What is true is
narrower and worth stating precisely: **its fixed-mesh temporal order is one,
and the usual $\Delta t\propto h$ presentation does not test that.** The
distinction stops being cosmetic as soon as $\Delta t$ is decoupled from $h$,
which is exactly what hierarchical timesteps do -- and that is why the
rate-consistent operator was settled before the multirate work rather than
after it.

### 12.5 Which path should be used, measured

Second-order temporal convergence is a property, not by itself a reason to
ship. The two paths were therefore compared directly at the production
timestep on the meshes and problems that matter, with both binaries built from
the same source and run back to back on the same node.

**Accuracy.** Advected Yee vortex, tiled Swift glass, `dt = 0.25/n`,
`boost = 1`, `t = 1`, analytic density L1:

| `n` | cells | GL+F1 | rate-Heun | difference |
| ---: | ---: | ---: | ---: | ---: |
| 48 | 2304 | `6.430158e-4` | `6.551337e-4` | +1.885 % |
| 96 | 9216 | `1.748167e-4` | `1.778519e-4` | +1.736 % |
| 192 | 36864 | `5.245707e-5` | `5.319881e-5` | +1.414 % |

The observed spatial orders are indistinguishable: 1.879 and 1.737 for GL+F1
against 1.881 and 1.741 for rate-Heun.

**This is the result that decides the question.** The first-order-in-$\Delta t$
term of GL+F1 is not a disadvantage when $\Delta t\propto h$: the two maps
differ in their $\Delta t^2$ coefficient, and on this problem the GL+F1
coefficient happens to lie slightly closer to the truth, so GL+F1 is about
1.5 per cent *more* accurate. Neither is systematically better; the difference
is simply the 1 to 2 per cent temporal term of Section 12.4, with a sign that
depends on the problem.

**Cost.** Same runs, same node, four ranks:

| `n` | GL+F1 | rate-Heun | ratio |
| ---: | ---: | ---: | ---: |
| 96 | 7 s | 11 s | 1.57 |
| 192 | 47 s | 83 s | 1.77 |

The ratio approaches the 4:2 sweep count as the problem grows and residual
work dominates the fixed overhead.

**Shock robustness.** On the Sod, rate-Heun terminates after two steps on an
`RD_DEBUG_ASSERTS` A2 failure, reporting

```
   defect = 8.9e-37    roundoff_scale = 1.1e-35    tolerance = 1.0e-47
```

Those magnitudes are numerically zero. The `LDA-F1-mass-apply` A2 scale is
built from `|K_i^+| |z|`, and on a quiescent element `sum_j v_j` underflows to
nothing, so the bound collapses and the assertion fires on floating-point
noise. This is the same failure mode the N scheme showed on a quiet Gresho
element. With assertions disabled the run completes normally and conserves
mass to `5e-15`; the scheme is not at fault, the diagnostic's scale is.
An absolute floor on that tolerance is a separate small repair.

Sod accuracy is also marginally worse for rate-Heun: density L1
`2.6855e-2` against `2.6261e-2` at `n = 64`, and `1.6232e-2` against
`1.5926e-2` at `n = 128`.

**Decision.** `GL+F1` remains the production path. `rate-Heun` costs 1.6 to
1.8 times as much, is 1.4 to 2.3 per cent less accurate on both test problems
at the production timestep, and currently trips a diagnostic on shocks. Its one
established advantage, fixed-mesh second-order time, is not observable in the
$\Delta t\propto h$ regime and does not convert into accuracy there.

`rate-Heun` is nevertheless retained in the source tree and belongs in the
thesis as an analysis topic rather than as a method. Without a working,
validated fix, the statement that the published GL+F1 staging has fixed-mesh
temporal order one would be an assertion; with it, the diagnosis is complete
and the cost of the alternative is quantified. The honest summary is that the
defect is real, understood, repairable, and not worth repairing at the
timesteps this solver actually uses.

Two consequences follow. The four-sweep operator does **not** need to be
derived for asynchronous triangles, since the multirate path will use GL+F1.
And the earlier argument that hierarchical timesteps would expose the temporal
defect by decoupling $\Delta t$ from $h$ was wrong: in a CFL-limited hierarchy
each bin still satisfies $\Delta t_T\propto h_T/(|u|+c)$ locally, so the
suppression of Section 12.4 continues to apply. A genuine decoupling requires
a timestep set by something other than the local CFL.

### 12.6 Both paths are retained in the code

`RD_RK2_RATE_CONSISTENT_HEUN` selects between them at compile time; it does not
replace the Chapter-3 staging. With the switch absent, the original GL+F1
corrector of equation (11) is still compiled, and it is what every production
and hierarchy configuration uses. The switch is present so that the measurement
of Section 12.2 can be reproduced and so that the comparison of Section 12.5
can be repeated if the timestep regime ever changes.
