# Targeted linearly-degenerate dissipation in quasi-Lagrangian ALE-RD

**Status:** mathematical and implementation note for the moving-mesh Sod
campaign.  The shear and entropy constructions are research switches, not the
default method.  They are tested separately.

## 1. Motivation

For the two-dimensional Euler equations, let

\[
\mathbf U=(\rho,\rho u,\rho v,E)^T
\]

and denote the element-average generator velocity by
\(\overline{\boldsymbol\sigma}_T\).  In the normal direction
\(\widehat{\mathbf n}\), the ALE Jacobian is

\[
\mathbf A_\sigma(\widehat{\mathbf n})
=
\mathbf A(\widehat{\mathbf n})
-
(\overline{\boldsymbol\sigma}_T\cdot\widehat{\mathbf n})\mathbf I.
\]

Its eigenvectors are the Euler eigenvectors and its eigenvalues are

\[
\lambda_- = w-c,\qquad
\lambda_e=\lambda_s=w,\qquad
\lambda_+=w+c,
\quad
w=(\mathbf u-\overline{\boldsymbol\sigma}_T)
\cdot\widehat{\mathbf n}.
\]

On a quasi-Lagrangian mesh,
\(\overline{\boldsymbol\sigma}_T\simeq\mathbf u\), so both linearly
degenerate eigenvalues approach zero.  The entropy eigenvector is common to
all face directions, while the shear eigenvector rotates with the face
tangent.  Consequently the entropy direction is an exact common kernel of
the element upwind operator in the Lagrangian limit, whereas the shear field
retains only the damping supplied by the other face directions.  The purpose
of the two constructions below is to restore selected missing dissipation
without changing the ALE flux or the element total residual.

## 2. Total residual and the unmodified split

For a P1 state on triangle \(T\), the selected contour total is

\[
\widetilde{\boldsymbol\Phi}^{T}
=
\frac12\sum_{j\in T}
\left[
\mathbf F(\mathbf U_j)\cdot\mathbf n_j
-
(\overline{\boldsymbol\sigma}_T\cdot\mathbf n_j)\mathbf U_j
\right],
\]

with the corresponding geometric/time terms added by the ALE-RK update.  The
discussion below applies equally to a Roe-linearised element total: write the
chosen total simply as \(\boldsymbol\Phi^T\).

The face matrices are

\[
\mathbf K_j
=
\frac{|\mathbf n_j|}{2}
\mathbf A_\sigma(\widehat{\mathbf n}_j)
=
\frac{|\mathbf n_j|}{2}
\mathbf R_j\boldsymbol\Lambda_j\mathbf L_j.
\]

With

\[
\lambda_k^\pm=\frac12(\lambda_k\pm|\lambda_k|),
\]

the standard split is

\[
\mathbf K_j^\pm
=
\frac{|\mathbf n_j|}{2}
\mathbf R_j\boldsymbol\Lambda_j^\pm\mathbf L_j,
\qquad
\mathbf K_j^++\mathbf K_j^-=\mathbf K_j.
\]

Because \(\sum_j\mathbf n_j=0\),

\[
\sum_j\mathbf K_j=0,
\qquad
\sum_j\mathbf K_j^+=-\sum_j\mathbf K_j^-.
\]

## 3. Shear eigenvalue-modulus floor

Let \(\mathbf t_j=(-n_{y,j},n_{x,j})\) be the unit tangent and define

\[
\mathbf r_{s,j}
=
(0,t_{x,j},t_{y,j},\mathbf u\cdot\mathbf t_j)^T,
\]

\[
\mathbf l_{s,j}^{T}
=
(-\mathbf u\cdot\mathbf t_j,t_{x,j},t_{y,j},0),
\qquad
\mathbf P_{s,j}=\mathbf r_{s,j}\mathbf l_{s,j}^{T}.
\]

The projector satisfies \(\mathbf P_{s,j}^2=\mathbf P_{s,j}\) and
annihilates the entropy and acoustic eigenvectors.  If

\[
|\mathbf u-\overline{\boldsymbol\sigma}_T|<\epsilon_s c,
\]

replace only the shear modulus by

\[
d_{s,j}=\max(|w_j|,\epsilon_s c),
\qquad
\lambda_{s,j}^{\pm,*}=\frac12(w_j\pm d_{s,j}).
\]

Equivalently,

\[
\mathbf K_j^{+,*}
=
\mathbf K_j^+
+
\frac{|\mathbf n_j|}{4}
(d_{s,j}-|w_j|)\mathbf P_{s,j},
\]

\[
\mathbf K_j^{-,*}
=
\mathbf K_j^-
-
\frac{|\mathbf n_j|}{4}
(d_{s,j}-|w_j|)\mathbf P_{s,j}.
\]

This construction targets transverse/shear noise.  It has no direct density
component and does not modify the acoustic rarefaction fields.

## 4. Entropy-mode dissipation

The entropy right and left eigenvectors are

\[
\mathbf r_e=(1,u,v,|\mathbf u|^2/2)^T,
\]

\[
\mathbf l_e^T
=
\left(
1-\frac{(\gamma-1)|\mathbf u|^2}{2c^2},
\frac{(\gamma-1)u}{c^2},
\frac{(\gamma-1)v}{c^2},
-\frac{\gamma-1}{c^2}
\right),
\]

normalised by \(\mathbf l_e^T\mathbf r_e=1\).  Hence

\[
\mathbf P_e=\mathbf r_e\mathbf l_e^T,
\qquad
\mathbf P_e^2=\mathbf P_e.
\]

Unlike the shear projector, \(\mathbf P_e\) is the same for all three face
directions.  Define the element-relative deficit

\[
\delta_e
=
\max\left(0,\epsilon_e c
-|\mathbf u-\overline{\boldsymbol\sigma}_T|\right),
\qquad
\eta_{e,j}=\frac{|\mathbf n_j|}{2}\delta_e.
\]

The implemented entropy correction is

\[
\mathbf K_j^{+,*}=\mathbf K_j^+ +\eta_{e,j}\mathbf P_e,
\qquad
\mathbf K_j^{-,*}=\mathbf K_j^- -\eta_{e,j}\mathbf P_e.
\]

This is an element-gated, rank-one Harten-type correction rather than the
per-face modulus replacement used for shear.  The element gate is essential:
a per-face gate would fire on ordinary static-mesh faces perpendicular to the
flow.  The entropy correction directly modifies density/contact content but
still annihilates both acoustic eigenvectors; it is therefore a diagnostic for
spurious entropy contamination, not a direct acoustic rarefaction limiter.

## 5. The element total is unchanged

For both constructions,

\[
\Delta\mathbf K_j^+ +\Delta\mathbf K_j^-=0,
\]

so

\[
\mathbf K_j^{+,*}+\mathbf K_j^{-,*}=\mathbf K_j.
\]

Therefore neither correction changes the physical/ALE flux, the contour
total, the Roe total, or the geometric conservation law.  It changes only the
nodal distribution of the already selected \(\boldsymbol\Phi^T\).

## 6. Entry into the LDA distribution

Define

\[
\mathbf S^{-,*}=\sum_j\mathbf K_j^{-,*}.
\]

The implementation does not form an inverse or a beta tensor.  It solves

\[
\mathbf S^{-,*}\mathbf x^*=\boldsymbol\Phi^T
\]

with the minimum-norm generalised inverse when required, and distributes

\[
\boxed{
\boldsymbol\Phi_i^{LDA,*}
=
-\mathbf K_i^{+,*}\mathbf x^*
=
-\mathbf K_i^{+,*}(\mathbf S^{-,*})^\dagger
\boldsymbol\Phi^T.
}
\]

Thus a correction changes both the upwind solve and the final left
multiplication.  Since

\[
\sum_i\mathbf K_i^{+,*}=-\mathbf S^{-,*},
\]

the consistent spatial solve gives

\[
\sum_i\boldsymbol\Phi_i^{LDA,*}=\boldsymbol\Phi^T.
\]

The entropy correction supplies a non-zero eigenvalue along the common
entropy kernel and can improve the rank/conditioning of \(\mathbf S^-\).  The
shear correction leaves that common entropy kernel untouched.

## 7. Entry into the N distribution

The modified inflow right-hand side and state are

\[
\mathbf b^*=\sum_j\mathbf K_j^{-,*}\widehat{\mathbf U}_j,
\qquad
\widehat{\mathbf U}_{in}^*
=(\mathbf S^{-,*})^\dagger\mathbf b^*.
\]

The raw N distribution is

\[
\boxed{
\boldsymbol\Phi_i^{N,*}
=
\mathbf K_i^{+,*}
(\widehat{\mathbf U}_i-\widehat{\mathbf U}_{in}^*).
}
\]

When the contour total is used, the raw N sum is reconciled with that total by

\[
\boldsymbol\Phi_i^{N,contour}
=
\boldsymbol\Phi_i^{N,*}
+\frac13
\left(
\boldsymbol\Phi^T-
\sum_j\boldsymbol\Phi_j^{N,*}
\right).
\]

The correction changes the raw N distribution and hence the reconciliation
amount, but the final nodal residuals still sum exactly to
\(\boldsymbol\Phi^T\).

## 8. Entry into the RK2 temporal distribution

For the LDA F1 temporal target \(\mathbf T^T\), the same corrected operator is
used:

\[
\mathbf S^{-,*}\mathbf z^*=\mathbf T^T,
\qquad
\mathbf T_i^{F1,*}=-\mathbf K_i^{+,*}\mathbf z^*.
\]

Thus the correction changes both the spatial and temporal nodal allocation,
while leaving their element sums fixed.  If \(\mathbf S^{-,*}\) is genuinely
rank deficient and the arbitrary temporal target is not in its range, the
current implementation uses the conservative lumped temporal fallback.

## 9. Conservation, covariance, accuracy, and limitations

The paired \(+/-\) construction preserves

1. the full ALE Jacobian and element total residual;
2. element conservation;
3. the LDA identity \(\sum_i\boldsymbol\beta_i=\mathbf I\) whenever the solve
   is consistent, hence formal linearity preservation;
4. Galilean covariance, because the relative velocity is invariant and each
   projector transforms by the same conservative-variable similarity as the
   ALE Jacobian.

These properties motivate a targeted spectral correction over scalar
artificial viscosity.  They do not prove positivity, entropy stability, or
nonlinear monotonicity.  Neither correction changes the acoustic eigenvalues,
so neither is a direct limiter for a genuinely acoustic rarefaction
oscillation.

## 10. Final Sod experiment

The matched relaxed-glass48 Sod comparison uses

- the already tested shear floor \(\epsilon_s=0.45\);
- a separate entropy correction \(\epsilon_e=0.27\), the previous Sod
  star-state estimate for restoring the entropy damping supplied by the
  static mesh;
- no combined shear+entropy arm and no parameter sweep.

The experiment is a mechanism test.  If the entropy arm changes density and
pressure without changing transverse noise, it confirms that the two
projectors act on distinct numerical errors.  If it does not materially
improve the rarefaction, the remaining oscillation should be treated as
acoustic LDA dispersion and moving-mesh resolution/geometry feedback rather
than missing entropy-mode dissipation.

## 11. Matched glass48 Sod result

The final experiment used the same 2304-generator relaxed periodic glass
(SHA256
8f8fc1d7557398643a9f35b1a0d18de1e5c6cb08d436fbe3f8dd02adc33103ea)
for all arms, \(\gamma=5/3\), contour total, element co-moving algebra,
Arpaia temporary mass, total-residual RK2, Courant factor 0.4 and
\(t_{\max}=0.2\).  The entropy value was the single motivated point
\(\epsilon_e=0.27\); it was not combined with the shear floor.

### 11.1 N distribution

| endpoint metric | control | shear \(\epsilon_s=0.45\) | entropy \(\epsilon_e=0.27\) |
| --- | ---: | ---: | ---: |
| global \(L_1(\rho)\) | 0.038859 | 0.039985 | **0.045040** |
| global \(L_1(v_x)\) | 0.110329 | 0.099765 | 0.107151 |
| global \(L_1(p)\) | 0.054722 | 0.054602 | 0.054674 |
| rarefaction \(L_1(\rho)\) | 0.058837 | 0.060913 | 0.057646 |
| rarefaction \(L_1(p)\) | 0.086234 | 0.089025 | 0.086966 |
| rarefaction entropy error | 0.024572 | 0.024832 | **0.030025** |
| volume RMS \(|v_y|\) | 0.014244 | **0.008146** | 0.011937 |
| volume p99 \(|v_y|\) | 0.061380 | **0.027392** | 0.050854 |
| \(\rho_{\min}\) | 0.139253 | 0.136442 | 0.137872 |
| \(p_{\min}\) | 0.120247 | 0.116121 | 0.118316 |
| edge flips | 332 | 273 | 282 |

The entropy arm reduces the rarefaction density L1 by only 2.0 per cent, while
the rarefaction pressure error rises by 0.8 per cent and its entropy error rises
by 22.2 per cent.  Globally it increases density L1 by 15.9 per cent.  Its
16.2 per cent transverse-RMS reduction is an indirect multidimensional effect
and is much weaker than the shear floor's 42.8 per cent reduction.

### 11.2 LDA distribution

| endpoint metric | control | shear \(\epsilon_s=0.45\) | entropy \(\epsilon_e=0.27\) |
| --- | ---: | ---: | ---: |
| global \(L_1(\rho)\) | 0.030156 | **0.024023** | 0.032667 |
| global \(L_1(v_x)\) | 0.090402 | **0.075481** | 0.091163 |
| global \(L_1(p)\) | 0.039872 | **0.032275** | 0.040294 |
| rarefaction \(L_1(\rho)\) | 0.047868 | **0.041175** | 0.045213 |
| rarefaction \(L_1(p)\) | 0.061642 | **0.053144** | 0.062042 |
| rarefaction entropy error | 0.007500 | **0.004431** | 0.006776 |
| volume RMS \(|v_y|\) | 0.020098 | 0.019239 | 0.020026 |
| volume p99 \(|v_y|\) | 0.075058 | 0.074514 | 0.075937 |
| \(\rho_{\min}\) | 0.076406 | **0.094886** | 0.072190 |
| \(p_{\min}\) | 0.040880 | **0.054042** | 0.039297 |
| edge flips | 589 | 589 | 572 |

The entropy arm reduces rarefaction density and entropy errors by 5.5 and
9.6 per cent, but rarefaction pressure error rises by 0.6 per cent.  The
global density, velocity and pressure errors rise by 8.3, 0.8 and 1.1 per
cent, the endpoint minima worsen, and transverse noise is unchanged.  The
shear arm remains clearly better on every principal LDA profile metric.

### 11.3 The operator acted as designed

This negative solution result is not caused by an inactive correction.

| diagnostic | N entropy | LDA entropy |
| --- | ---: | ---: |
| minimum \(S^-\) pivot ratio | 0.0999 | 0.1646 |
| maximum F1 lumped count | 0 | 0 |
| maximum relative conservation defect | \(3.79\times10^{-16}\) | \(9.68\times10^{-16}\) |
| completed \(t=0.2\) | yes | yes |

The matched controls and shear arms have minimum pivot ratio zero; the LDA
control and shear arms report up to 4027 rank-deficient F1 lumped events.
The entropy projector removes the common entropy kernel exactly as predicted
and eliminates the temporal fallback, while preserving element conservation.
It changes the intended operator and still does not cure the solution.

### 11.4 Decision

The entropy correction is rejected as a Sod rarefaction cure for both N and
LDA.  The small LDA rarefaction-density improvement is outweighed by worse
global errors, pressure, minima and unchanged transverse noise.  For N it
broadens the solution enough to make the global density error materially
worse.

The result separates the mechanisms:

- the shear projector is the effective treatment of excess transverse noise;
- the entropy kernel and LDA temporal rank deficiency are real and removable,
  but they are not the cause of the remaining rarefaction error;
- the residual error is consistent with acoustic LDA/N dispersion, reduced
  Eulerian sampling in the expanding quasi-Lagrangian fan, and
  solution--geometry feedback.

No further Sod operator tuning is planned.  The shear floor remains a useful
ongoing-optimisation result for the thesis, not a default.  The entropy
correction remains a mathematically clean diagnostic switch and a useful
negative result.

Machine-readable results and figures:

~~~text
/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_EntropyFloor_Final_20260823/analysis.json
/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_EntropyFloor_Final_20260823/figures/sod-entropy-floor-full-profiles.png
/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_EntropyFloor_Final_20260823/figures/sod-entropy-floor-rarefaction.png
~~~

Repository copies of the figures are in
useful_resources/shear_eigenvalue_floor/.
