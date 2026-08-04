# The B scheme in AREPO-RD: from the thesis spatial blend to the multirate case

- Authors: `Zhenyu Wu and Claude Code (Opus 5)`
- Opened: 2026-08-04.
- Purpose: collect in one place the complete mathematics of the blended scheme
  as it now exists in the code, because the thesis contains only the **spatial**
  blend and everything the time-dependent and hierarchical cases require was
  added afterwards and is currently spread across a dozen log entries.

A note on register before anything else. The blend is a **limiter**, not a
scheme derived from an accuracy requirement. Its blending parameter is a
heuristic indicator, and several of the choices below are free parameters that
theory does not fix. This document marks each such choice explicitly, because
the useful discipline is to know which statements are derivations and which are
conventions to be settled by measurement.

---

## 1. What the thesis has, and what it does not

Chapter 3 defines the blend spatially only:

```
   phi_i^B = Theta phi_i^N + (1 - Theta) phi_i^LDA ,
   Theta   = min( 1 , |Phi^T| / sum_j |phi_j^N| )
```

with `Theta` taken per conserved component. That is the whole of the published
construction.

Everything else here is new: the time-dependent blend needs a **blended mass
matrix** and a `Theta` built from the **total** rather than the spatial
residual, and the multirate case needs a decision about *when* `Theta` is
evaluated that the equal-bin case does not force. These belong in Chapter 4.

---

## 2. The two ingredients

Both distributions act on the same element residual
`Phi^T = sum_j K_j U_j`, formed from the conservative parameter-vector
linearisation, and both satisfy the element conservation identity.

**N scheme.** With `S^- = sum_j K_j^-` and the inflow state

```
   Uhat_in = (S^-)^{-1} sum_j K_j^- U_j ,
   phi_i^N = K_i^+ ( U_i - Uhat_in ) .
```

Monotone and positivity preserving under a CFL condition; first order in space.
In the code `Uhat_in` is the second right-hand side of the upwind solve and
`phi_i^N` is `Flux_N`.

**LDA scheme.** With `beta_i = -K_i^+ (S^-)^{-1}`,

```
   phi_i^LDA = beta_i Phi^T ,     sum_i beta_i = I .
```

Linearity preserving, second order in space, and not positivity preserving --
on the Sod it undershoots the exact density minimum by 54 per cent.

**Both sum to the element residual**, `sum_i phi_i^N = sum_i phi_i^LDA = Phi^T`,
so for **any** `Theta`, including a different one per component,

```
   sum_i phi_i^B = Theta Phi^T + (1 - Theta) Phi^T = Phi^T .
```

Conservation of the blend is therefore free. This is the single most useful
structural property of the construction and it recurs at every extension below.

---

## 3. The spatial indicator, and why it does not survive unsteadiness

The rationale for `Theta = |Phi^T| / sum_j |phi_j^N|` is that on a smooth
**steady** solution the element residual tends to zero while the individual N
contributions do not, so `Theta -> 0` and the blend degenerates to LDA; near a
discontinuity the residual is large and comparable to the sum of absolute
contributions, so `Theta -> 1` and the blend degenerates to N.

Direct measurement shows the reasoning does not survive contact with either
regime as cleanly as it reads. Mean over all elements and components:

| problem | mean `Theta` | fraction below `1e-2` |
| --- | ---: | ---: |
| smooth Yee vortex, triangular `n=64` | 0.4591 | 0.016 |
| smooth Yee vortex, glass `n=48` | 0.5157 | 0.012 |
| Sod shock tube, triangular `n=64` | 0.6604 | 0.033 |

and on the glass family, at both boosts:

| `n` | `h` | `boost=0` | `boost=1` |
| ---: | ---: | ---: | ---: |
| 48 | 0.2083 | 0.5429 | 0.5466 |
| 96 | 0.1042 | 0.5047 | 0.4860 |
| 192 | 0.0521 | 0.4511 | 0.4607 |

**The spatial indicator is `O(1)` in both regimes.** It sits near 0.5 in a
perfectly smooth vortex whether that vortex is stationary or advected, a Sod
raises it only to 0.66, and a fourfold refinement lowers it by 17 per cent. It
does not satisfy the `O(h)` condition of eq. (41) anywhere we have measured.

This is a correction to an earlier reading in this project, which attributed
the failure to unsteadiness alone -- `Phi^T` is approximately
`-integral d_t u` and so vanishes nowhere for an unsteady problem, which is
true but is not the whole story, since the indicator is equally `O(1)` when the
solution is steady. What actually changes with the boost is the **total**
indicator of Section 4.2, which becomes small only when the solution is
genuinely unsteady, thereby opening a gap between the two.

---

## 4. The time-dependent blend

### 4.1 Blended mass matrix

Arpaia & Ricchiuto (2015) eqs. 43-44 require the mass matrix itself to blend:

```
   m_ij^B = (1 - l) m_ij^LDA + l (|T|/3) delta_ij .
```

On this code path the two halves already exist: the F1 term **is** `m^LDA`
(`m_ij^F1 = (|T|/3) beta_i`) and the lumped term **is** `m^N`
(`(|T|/3) delta_ij`). The blended temporal contribution is therefore a linear
combination of two quantities the corrector already computes:

```
   T_i^B = Theta T_i^lumped + (1 - Theta) T_i^F1 .
```

Column conservation holds for any `l`:

```
   sum_i m_ij^B = (1-l)(|T|/3) sum_i beta_i + l (|T|/3) I = (|T|/3) I .
```

### 4.2 The indicator must use the total residual

The same paper states that for a time-dependent problem the blending parameter
"should now include the whole residual". Section 3 is the measurement of why:
the spatial residual is not small on a smooth unsteady solution, but the
**total** residual is, because it approximates
`integral (d_t u + div f) = 0`.

Define the element total and the two total distributions over one step:

```
   R       = T_target + [ Phi(U^n) + Phi(U*) ] / 2 ,
   R_i^N   = T_i^lumped + [ phi_i^N(U^n)   + phi_i^N(U*)   ] / 2 ,
   R_i^LDA = T_i^F1     + [ phi_i^LDA(U^n) + phi_i^LDA(U*) ] / 2 ,
   Theta   = min( 1 , |R| / sum_i |R_i^N| ) ,
   R_i^B   = Theta R_i^N + (1 - Theta) R_i^LDA ,
```

with `T_target = (|T|/3) sum_j dU_j / dt`. Since `sum_i R_i^N = sum_i R_i^LDA =
R`, conservation again holds for every `Theta`, and this is what makes it safe
to blend the **total** residual rather than only its spatial part.

Measured on the glass family at fixed boost:

| `n` | `h` | `boost=0` | `boost=1` |
| ---: | ---: | ---: | ---: |
| 48 | 0.2083 | 0.4191 | 0.2445 |
| 96 | 0.1042 | 0.4265 | 0.1447 |
| 192 | 0.0521 | 0.4079 | 0.0948 |

The total indicator falls with `h` **only when the solution is unsteady**, and
then like `h^0.7` rather than `h` (measured slopes 0.76 and 0.61). For the
stationary vortex it is flat at about 0.42, no better than the spatial form.

This corrects an earlier claim in this project that the total indicator was
`O(h)` "verified on three points". Those three points were triangular `n=64`,
triangular `n=128` and glass `n=48`; the agreement of the last with the `h`
ratio of the first two was a coincidence across mesh families read as a
confirmation. Within one mesh family the exponent is 0.7, and at `boost=0`
there is no decrease at all. The indicator therefore satisfies the `O(h)`
condition of eq. (41) only approximately, and only for unsteady flow.

### 4.3 The dissipation cost this implies

`O(h)` at production resolution is 0.2 to 0.3. **The repaired blend therefore
runs as 20 to 30 per cent N in smooth flow**, where LDA alone would be second
order. This is the central B-versus-LDA trade and the number the thesis must
quote. It is not a defect of the repair: it is what an `O(h)` indicator does at
finite resolution.

### 4.4 One `Theta` must act on one complete residual

The first implementation formed `Theta` from the new stage while the old
spatial half had already been deposited by the vertex-local `+dU/2` shortcut
carrying the predictor's `Theta^n`. The scheme stayed conservative -- the
`+dU/2` part is separately conservative through the predictor identity
`sum_i |S_i| dU_i/2 = -(dt/2) sum_T Phi^T(U^n)` -- but two different blend
coefficients acted on the two halves of one residual. The repair stores
`Phi(U^n)`, `phi_i^N(U^n)` and `phi_i^LDA(U^n)` per owned element at the
predictor and suppresses the shortcut, so that a single `Theta` multiplies the
complete `R`.

---

## 5. Literature provenance, and the ambiguity the literature leaves open

Everything in Section 4 has a source, and the source is unusually explicit
about which parts are heuristic. Arpaia & Ricchiuto, *J. Sci. Comput.* **63**
(2015) 502-547, Sect. 3.4.3:

- **eq. (41)** is the steady blend `phi_i^B = (1-l) phi_i^HO + l phi_i^P`;
- the requirement on the coefficient is stated outright: `l(u_h)` "has to be of
  order **`O(h)` (or smaller) when the solution is smooth** and of order
  `l ~ 1` when the solution is discontinuous";
- **eq. (42)** is the heuristic `l = |phi^K| / sum_j |phi_j^P|`, attributed to
  Deconinck et al., with the remark that "several definitions of this
  coefficient are possible" and a reference to a thorough discussion of
  alternatives;
- **eq. (43)** is the blended mass matrix
  `m_ij^{LDA-N} = (1-l) m_ij^{LDA} + l (|K|/3) delta_ij`;
- **eqs. (44)-(45)** are the time-dependent parameter,
  `l = |Phi^K| / sum_j |Phi_j^N|` with
  `Phi^K = integral_K (d u_h/dt + div f(u_h)) dx` and
  `Phi_i^N = (|K|/3) du_i/dt + phi_i^N`.

Two of these settle questions this project reached independently.

**The `O(h)` requirement is the acceptance criterion for the indicator, and it
is the published one.** Measured against it (Sections 3 and 4.2), the spatial
form is `O(1)` in every case tried and fails the condition outright; the total
form satisfies it only approximately, decreasing like `h^0.7` for an unsteady
solution and not at all for a stationary one. Neither meets eq. (41) as
written. Having a published criterion to measure against is nevertheless what
makes the comparison meaningful, and it correctly ranks the two.

**The freedom in *when* to evaluate the temporal term is acknowledged in the
paper and never resolved.** Immediately after eq. (45):

> "Of course, the Eqs. (44)-(45) are somewhat unclear since the meaning of
> `d u_h / d t` needs to be made more precise to be able to evaluate the
> parameter `l`. This will be made more precise in Sect. 3.5."

Section 3.5 of that paper presents the SSP RK-RD marching procedure and the
SL/GL mass lumping (its eqs. 49-53) and does not return to the point. `l` and
"blending" do not reappear in a defining role anywhere later in the paper.

So the choice below is not an invention of this project. It is the ambiguity
the source flags and defers.

### 5.1 The two quadratures

`T_target = (|T|/3) sum_j dU_j/dt` is the discrete stand-in for
`(|K|/3) du_i/dt` in eq. (45). What is left open is which quadrature of the
interval residual `Theta` uses:

```
   unfrozen (trapezoid)  :  R = T_target + [ Phi(U^n) + Phi(U*) ] / 2
   frozen   (left end)   :  R = T_target +   Phi(U^n)
```

and correspondingly for `sum_i |R_i^N|`. Frozen uses the **whole** stage-0
residual, not half of it; both estimate the same interval integral.

**Everything else is identical.** `R_i^N` and `R_i^LDA` keep the full
trapezoid; the blend formula, the mass matrices, conservation and the
rank-deficient fallback do not change. The variants differ by exactly one
scalar per element per equation.

| | unfrozen | frozen |
| --- | --- | --- |
| estimator of the interval residual | `O(dt^2)` | `O(dt)` |
| depends on `dt` within the step | yes, through `U*` | no |
| state read near a discontinuity | includes the oscillatory predictor | the clean `U^n` |
| feature forming inside one step | detected in the corrector | detected one step late |
| computable at the opening call of the two-call hierarchy | **no** | yes |

As an estimator the unfrozen form is the more consistent one; freezing is a
deliberate first-order degradation traded for evaluating the detector on a
cleaner state. Measured on the Sod:

| | rho L1 `n=64` | `n=128` | overshoot | undershoot |
| --- | ---: | ---: | ---: | ---: |
| unfrozen | `2.337e-2` | `1.346e-2` | `8.72e-5` | `3.31e-4` |
| frozen | `2.351e-2` | `1.352e-2` | `2.2e-16` | **0** |

Unfrozen is 0.4 to 0.6 per cent more accurate, consistent with being the higher
order estimator. Frozen recovers strict monotonicity, which is the property the
blend exists to provide.

That the unfrozen form loses strict monotonicity is **expected from the
source**, not a symptom of a bug. The same paper records that "the heuristic
LDA-N blending procedure does not guarantee the maintenance of positivity",
because a sub-element LED condition imposes three constraints that "in general
cannot be satisfied by only one parameter". Both variants are therefore
heuristics with no positivity guarantee, and the difference between them is an
empirical question by construction.

### 5.2 Four combinations, all retained in the code

Because the two questions -- whether the temporal term enters, and which
quadrature -- are independent, the code carries them as two orthogonal
compile-time switches, giving the four combinations that span eqs. (42) and
(44):

| switches | indicator |
| --- | --- |
| neither | eq. (44), trapezoid |
| `RD_B_FROZEN_THETA` | eq. (44), left endpoint |
| `RD_B_SPATIAL_THETA` | eq. (42) in unsteady form, trapezoid |
| both | eq. (42) in unsteady form, left endpoint |

Conservation is unaffected in all four, since it holds for any `Theta`
(Section 2). The spatial pair is retained as the control that establishes the
Section 3 measurement rather than as a candidate.

## 6. What the construction deliberately does not contain

Worth stating plainly, because several apparent defects are consequences of
the blend being the simplest one rather than of an error.

- **No shock sensor and no smoothness detector** beyond `Theta` itself. A
  richer indicator would remove the `O(h)` smooth-flow N fraction of
  Section 4.3 and would also remove the freedom of Section 5.
- **No a posteriori limiting**, no MOOD-style detect-and-redo.
- **No fixed-mesh temporal order.** `Theta` contains an absolute value and a
  clip and is a state-dependent functional, so the switching set is not a
  smooth function of `dt`. Three constructions were laddered and none gave an
  order; freezing removes only the within-step dependence, not the dependence
  of the trajectory on `dt`. **This is expected for a limited scheme and is not
  a defect to be repaired.** The acceptance gate is joint `(dx, dt)`
  convergence to the exact solution.
- **No characteristic-variable decomposition.** The blend is applied
  component by component on the conserved variables. Arpaia & Ricchiuto also
  give the version in which the blend acts on the characteristic amplitudes,
  `Phi_i^{LDA-N} = sum_m alpha_m^{LDA-N} r_m` with `r_m` the eigenvectors of
  `K(u, uhat)` along the flow direction. That is a known strengthening this
  implementation does not have, and it is the natural next refinement if the
  component-wise indicator proves too blunt.
- **No repair of the contact defect.** The spurious pressure
  `dp/p = (sqrt(rho_L)-sqrt(rho_R))^2 / (4 sqrt(rho_L rho_R))` is a property of
  the parameter-vector formulation and is inherited unchanged; on the advected
  glass contact the blend in fact overshoots the exact density maximum by 16
  per cent, worse than N.

---

## 7. Rank deficiency

When `S^-` is singular, `beta_i` is undefined, so the LDA half of the blend
falls back to the lumped mass -- the same conservative choice the LDA path
makes -- and the blend remains defined rather than being switched off. The
event is counted in `f1_lumped`, which was zero in every smooth run reported so
far, so the published second-order-in-space results test the F1 path itself and
not the fallback.

---

## 8. The multirate extension: what still has to be decided

`B_SCHEME` with `RD_RK2_TOTAL_RESIDUAL` and `RD_HIERARCHICAL_TIMESTEPS` is
currently a compile-time error. Three questions have to be answered, and two of
them turn out to be already settled by the structure.

**(a) Does the blend disturb the hierarchy conservation proof? No.** That proof
concerns `Phi^T` and the cancellation of shared-edge contributions between
neighbouring elements. `Theta` acts only on the *distribution* of an element
residual, and conservation of the blend holds elementwise for any `Theta`
(Section 2). The blend is therefore orthogonal to Construction A.

**(b) Is `Theta` well defined for a cross-bin element? Yes.** Under the
vertex-star freezing rule an element evaluates its residual from a coherent
triple -- frozen `U^sync` at frozen vertices, stage state at live ones -- so
`R` and `R_i^N` are exactly the quantities the element actually distributes,
and `Theta` follows from them with no new ambiguity.

**(c) When is it evaluated? This one is forced, and it forces the choice of
Section 5.** In the two-call hierarchy the predictor call deposits
`-h_T phi_i^(0)/2` into the vertex ledgers immediately. If a single `Theta` is
to multiply the complete residual, it must therefore be known at the **opening**
call. The unfrozen quadrature needs `Phi(U*)`, which does not exist until the
closing call, by which time the first half has already been deposited.

There are only two ways out: use the frozen quadrature, which is computable at
the open; or defer the entire deposit to the closing call, which requires
storing per-element stage-0 residuals across an open interval and migrating
them under domain decomposition. The equal-bin coherent repair already does the
latter, but at equal bins the interval is one step and the storage is transient;
in a hierarchy a coarse element's interval spans many fine steps and several
possible domain decompositions.

**Conclusion: frozen `Theta` is the natural, and much the simpler, choice for
the hierarchy.** This is an argument from the code structure rather than from
accuracy, and it is worth recording as such -- but it does mean that if the
equal-bin acceptance campaign prefers the unfrozen variant, the two regimes
will disagree, and that disagreement should be an explicit decision rather than
a silent divergence.

Not new to B, but still open in the hierarchy: N's positivity holds under a
CFL condition, and a cross-bin element evaluates with stale states whose wave
speeds may exceed those used to set `h_T`. The blend leans on N's positivity,
so it inherits that question.

---

## 9. Where each piece is in the code

`src/hydro/residual_distribution_solver.c`:

- `Phi` -- the element residual, `sum_j K_j Uhat_j`;
- `Y_in` and `Bracket` -- the N inflow state and `U_i - Uhat_in`; `Flux_N`;
- `X_lda` and `Flux_LDA` -- the LDA solve and distribution;
- `Theta_E` -- the **spatial** blend of Section 3, used by the predictor stage
  and by the `"B"` conservation check;
- the `B_SCHEME` branch of the RK2 corrector -- `T_lumped`, `T_f1`, the
  total-residual `Theta`, and the blend of Section 4;
- `RD_B_FROZEN_THETA` -- the Section 5 choice, a compile-time switch with the
  unfrozen quadrature as the `#else` branch;
- `RD_DIAG_THETA` -- the histogram of both indicators that produced Section 3.

Every B configuration in `examples/` that uses RK2 currently defines
`RD_B_FROZEN_THETA`; the unfrozen path is retained as the control.

---

## 10. What has to be run

1. **Equal-bin acceptance.** Glass `n = 48, 96, 192`, `boost = 1`,
   `TimeMax = 1`, `dt = 0.25/n`, comparing LDA+F1 GL, N+RK2, and B with both
   `Theta` quadratures on the same IC. Report analytic `L1`, `L2`, `Linf`,
   joint orders, wall time, and the `Theta` histograms. The gate is
   monotonically decreasing error with a stable joint order, positive
   predictors, `f1_lumped = 0` and round-off conservation -- **not** a
   fixed-mesh temporal order.
2. **The dissipation number.** The accuracy loss of B against LDA on that same
   ladder, alongside the measured smooth-flow `Theta`. This is the quantity
   Section 4.3 predicts and the thesis has to quote.
3. **Contact regression.** One frozen-`Theta` run on the 8:1 advected glass
   contact, matched to the unfrozen baseline. Boundedness and positivity, not
   an attempt to remove the parameter-vector defect.
4. **Then the hierarchy**, on the Section 8(c) reading: frozen `Theta`, the
   compile gate lifted, and the existing N hierarchy gates repeated for B --
   equal-bin reduction, conservation at the coarsest bin, positivity, and
   decomposition invariance at 1, 4 and 16 ranks.

The governing principle for the remaining choices is the one that applies to
any heuristic limiter: run both, measure, and make the better one the default.
