# The entropy mode on a Lagrangian mesh, and a targeted dissipation for it

Claude Code (Opus 5), 2026-08-19. Companion to sections 44 to 46 of
`RD_DEVELOPMENT_LOG_2.md`. Nothing here is implemented; this is the derivation
to be reviewed before any code is written.

---

## 1. The ALE eigenstructure, and the one vector that does not rotate

Write the two-dimensional conservative state and the ALE normal flux as

```
U = (rho, rho u, rho v, E)^T ,     F_sigma,n(U) = F(U).n - (sigma.n) U ,
```

so the ALE normal Jacobian is

```
A_sigma(n) = A(n) - (sigma.n) I ,     A(n) = d(F.n)/dU .
```

Because the two differ by a multiple of the identity, **they have exactly the
same eigenvectors**, and the eigenvalues are shifted by `sigma.n`. With

```
w = (u - sigma).n            the relative normal velocity
c                            the sound speed
t = (-n_y, n_x)              the unit tangent
H                            total enthalpy
```

the spectrum of `A_sigma(n)` is

| eigenvalue | right eigenvector | name |
| --- | --- | --- |
| `w - c` | `(1, u - c n_x, v - c n_y, H - c u.n)` | acoustic minus |
| `w` | `r_e = (1, u, v, \|q\|^2/2)` | **entropy** |
| `w` | `r_s = (0, t_x, t_y, u.t)` | **shear** |
| `w + c` | `(1, u + c n_x, v + c n_y, H + c u.n)` | acoustic plus |

The single structural fact this document rests on:

> **`r_e` does not depend on `n`. `r_s` does.**

The entropy eigenvector is built from `u`, `v` and `|q|^2` alone; the shear
eigenvector is built from the tangent, so it rotates as the face normal
rotates.

## 2. What a Lagrangian mesh does to the upwind operator

The RD element matrices are

```
K_j = (1/2) |n_j| A_sigma(nhat_j) ,      K_j^+- = R_j Lambda_j^+- R_j^-1 ,
S^- = sum_j K_j^- .
```

Set `sigma = u`, the Lagrangian limit. Then `w = 0` on every face and the
spectrum of each `K_j` is `(-c, 0, 0, +c)` scaled by `|n_j|/2`. Hence

```
ker K_j = span{ r_e , r_s(nhat_j) } .
```

`r_e` is common to all three faces and `r_s` is not, so for a nondegenerate
triangle

```
   intersection over j of ker K_j  =  span{ r_e }  ,   exactly.
```

Direct check on one element of the Sod star state, comparing `|K_j r_e|`
against the static-mesh value `1.795e-2`:

```
static      |K_j r_e| = 1.795e-02   1.795e-02   8.674e-19
Lagrangian  |K_j r_e| = 2.491e-18   2.491e-18   8.674e-19
```

Three consequences follow immediately, since `K_j^+-` share the eigenvectors:

1. `K_j^+ r_e = 0` for every `j`: **the entropy mode receives no upwind
   dissipation at all**;
2. `S^- r_e = 0`: **`S^-` is singular in the entropy direction**, which is the
   same degeneracy behind the pseudo-inverse branch and the rank-deficient F1
   fallback;
3. `Phi = sum_j K_j Uhat_j` is blind to the entropy content of the state.

Point 3 is *not* an error. A contact discontinuity co-moving with the mesh is
an exact steady solution of the Euler equations, so `Phi = 0` is the right
answer. The defect is point 1: the scheme also has no mechanism to **remove**
spurious entropy content generated elsewhere -- by the changing mass matrix,
by the nodal-flux quadrature, by connectivity changes, by mesh irregularity.
On a static mesh that content is damped at rate `|u.n|`. On a Lagrangian mesh
it is a neutral mode and accumulates.

Section 45 is the measurement of exactly this: on the matched glass KH, in
units of the initial entropy span, the excursion beyond the exact invariant
range is bounded for static LDA (0.42 at `t=2`), bounded for moving N (0.24),
and unbounded for moving LDA (5.10 at `t=1.0`, then failure).

## 3. Measured damping, and why the mesh-velocity route cannot work

Sweeping the frame velocity, damping normalised to the static mesh:

| `sigma/u` | entropy | shear | acoustic minus | acoustic plus |
| ---: | ---: | ---: | ---: | ---: |
| 0.00 | 1.000 | 1.000 | 1.000 | 1.000 |
| 0.50 | 0.500 | 0.777 | 1.372 | 0.816 |
| 0.90 | 0.100 | 0.599 | 1.671 | 0.669 |
| 1.00 | **0.000** | **0.554** | 1.745 | 0.632 |

Entropy damping is exactly linear in `1 - sigma/u` and reaches zero. Shear
damping falls only to 0.554, because the three face kernels do not coincide,
so shear keeps whatever the other two faces supply.

Two separate observables follow, and they must not be conflated:

- **Transverse velocity noise** is the shear mode. Predicted amplification
  `1/0.554 = 1.81`; measured on the glass Sod, moving N against static N,
  **1.80**. This is what section 46's mesh-velocity sensor tried and failed to
  remove.
- **Entropy error** is the entropy mode. Undamped, and it is what diverges in
  KH.

Section 46 changed `sigma` and moved neither. That is expected: the only way a
`sigma` change helps is by making the mesh less Lagrangian, which surrenders
the property the moving mesh exists for. The Gresho-plus-boost results are the
direct evidence that this trade is bad.

## 4. The proposed term

Leave the mesh alone and restore the dissipation where it was lost, in the
operator, and **only in the direction that lost it**.

Let `l_e` be the left entropy eigenvector, whose amplitude is the standard
entropy characteristic `d rho - dp/c^2`. In conservative variables

```
l_e = ( 1 - (gamma-1)|q|^2 / (2 c^2) ,
        (gamma-1) u / c^2 ,
        (gamma-1) v / c^2 ,
       -(gamma-1) / c^2 ) ,
```

normalised so that `l_e . r_e = 1`, which is verified by direct expansion.
Then

```
P_e = r_e l_e^T ,      P_e^2 = P_e
```

is the spectral projector onto the entropy mode. Like `r_e`, it does not
depend on `n`, so it is computed **once per element**, not once per face.

Verified numerically on the Sod star state:

```text
l_e . r_e                                    = 1.000000000000000
|| P_e^2 - P_e ||                            = 5.55e-17
max |A(n) r_e - (u.n) r_e| over 500 normals  = 7.77e-16
max |l_e A(n) - (u.n) l_e| over 500 normals  = 3.89e-16
```

The last two lines are the content of section 1: `r_e` and `l_e` are the right
and left entropy eigenvectors *for every direction simultaneously*, which is
what makes a single element-local projector legitimate.

The proposal is, per face,

```
K_j^+  <-  K_j^+ + eta_j P_e ,
K_j^-  <-  K_j^- - eta_j P_e ,
eta_j  =  (1/2) |n_j| * max(0, delta - |w_j|) ,      delta = epsilon * c .
```

`epsilon = 0` recovers the present scheme exactly.

The `max(0, delta - |w_j|)` factor is the Harten-Hyman idea restricted to one
direction: the term is **inert wherever the entropy eigenvalue is already well
separated from zero**, so a static mesh away from stagnation is untouched, and
it switches on smoothly as the mesh becomes Lagrangian.

## 5. The four properties that make this the right shape

### 5.1 Conservation is exact and untouched

`K_j^+ + K_j^- = K_j` is preserved by construction: the same `eta_j P_e` is
added to one and subtracted from the other. Nothing in `Phi = sum_j K_j Uhat_j`
changes, and the nodal identity `sum_i phi_i = Phi` holds exactly as before.
**The term modifies the dissipation, never the flux.**

### 5.2 Galilean covariance is exact

The eigenvalues `w_j` are frame-invariant, since `u' - sigma' = u - sigma`.
The entropy eigenvector is exactly covariant, `r_e(u - b) = G(b) r_e(u)`,
checked over 2000 random `(u, b)` pairs to `2.8e-14`; and `l_e` transforms as
`l_e G^-1`, since `rho` and `p` are frame-invariant and `l_e . r_e = 1` must
hold in both frames. Hence

```
P_e' = G P_e G^-1 ,      K_j'^+- = G K_j^+- G^-1
```

still holds with the added term, and the element covariance of section 44.2
survives unchanged.

### 5.3 LDA stays linearity-preserving, so its formal order survives

This is the property that distinguishes the proposal from adding artificial
viscosity. The LDA distribution needs `sum_i K_i^+ = -S^-`. With the term,

```
sum_i K_i^{+,new} = -S^- + (sum_i eta_i) P_e  ,
S^{-,new}         =  S^- - (sum_i eta_i) P_e  ,
```

so `sum_i K_i^{+,new} = -S^{-,new}` still holds, and therefore

```
sum_i beta_i = -( sum_i K_i^{+,new} ) (S^{-,new})^-1 = I ,   exactly.
```

**LDA remains linearity-preserving for any `epsilon`, hence formally second
order on smooth solutions.** A scalar artificial viscosity would not have this
property. This is the strongest argument for the rank-1 form over a general
Harten fix, which perturbs the acoustic branches as well (the sweep shows
acoustic-minus damping falling from 1.745 to 1.589 at `delta = c`).

### 5.4 It removes the `S^-` rank deficiency as a side effect

At `sigma = u`, `S^- r_e = 0`. With the term,

```
S^{-,new} r_e = -( sum_i eta_i ) r_e   !=  0 .
```

The entropy direction is no longer in the kernel. This is the same degeneracy
that forces the minimum-norm SVD branch and the rank-deficient F1 fallback, so
the term should improve conditioning as well. Whether it removes the F1
fallback entirely is a measurement, not a claim: section 44.3 shows that
fallback also fires on a static mesh at `t=0` from `u = 0`, which this term
does not address.

## 6. What it costs, and the open questions

**A co-moving contact stops being an exact steady state.** It acquires
diffusion at rate `delta`. That is the intended effect, but it is a real cost
and it is why `epsilon` must be as small as the KH result allows.

Three things this derivation does **not** settle:

1. **The value of `epsilon`.** It has to come from the KH entropy curve. The
   design target is the smallest `epsilon` that turns the moving-LDA excursion
   from divergent to saturating.
2. **Whether second order survives in practice.** Section 5.3 proves
   linearity preservation, which is the standard sufficient condition, but the
   constant may still degrade. The Yee order ladder is the check.
3. **The shear mode is untouched, deliberately.** This term does nothing for
   the factor 1.80 in transverse velocity on Sod. Section 3 argues that factor
   is not curable by any targeted dissipation, so it should be accepted and
   reported rather than tuned.

## 7. Relation to the literature

The `max(0, delta - |lambda|)` shape is Harten's entropy fix, standard for
upwind schemes at sonic and stagnation points. What is unusual here is that
the degeneracy is not confined to isolated points: on a Lagrangian mesh the
entropy and shear eigenvalues vanish **everywhere and identically**, so the fix
is not a local repair but a structural component.

That is also why the published ALE-RD literature does not report this. Arpaia
and Ricchiuto's ALE-RD work is r-adaptation, which moves nodes to equidistribute
a monitor function and deliberately does not follow the fluid: `u - sigma` stays
O(1) there and the degeneracy never appears. The Lagrangian limit is outside
the regime those papers test.
