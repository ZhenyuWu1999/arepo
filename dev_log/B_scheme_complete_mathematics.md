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

### 4.5 The local blend correction, not mean `Theta`, predicts the error

A final-corrector element map on the tiled glass (`n=48,96`, `boost=0,1`)
settled the counter-intuitive mean-`Theta` result. For density, the diagnostic
records

    C_T = dt Theta_T sum_i |R_i^N - R_i^LDA| / |T|

and compares it with the mean analytic density error at the triangle vertices.
`Theta_rho` alone has essentially no positive rank correlation with error:
Spearman coefficients are `+0.061,-0.244` at boost zero and
`-0.244,-0.239` at boost one for `n=48,96`. In contrast, `C_T` has Spearman
coefficients `0.943,0.940` and `0.915,0.928`, respectively. Thus the relevant
quantity in

    R^B - R^LDA = Theta (R^N - R^LDA)

is the complete product, not the unweighted mean of its first factor.

The spatial concentration also differs by regime. The vortex core (`r<1`)
contains only about 3.1 per cent of the triangles. It receives 9.5 and 8.8 per
cent of the density blend correction at boost zero, but 21.4 and 21.3 per cent
at boost one. The top 10 per cent of triangles ranked by local error receive
39.4 and 35.9 per cent of the correction at boost zero versus 42.2 and 45.7 per
cent at boost one. The increasing concentration under refinement in the
advected case is consistent with its observed drift toward first order.

This is a final-step correlation with a cumulative solution error, so it is
evidence rather than a causality proof. It does, however, rule out mean
`Theta` as an adequate accuracy diagnostic and explains how boost zero can
have the larger mean indicator but the smaller error.

### 4.6 AREPO shock-sensor source audit and scope decision

Two different mechanisms exist in the local AREPO sources and should not be
conflated.

The present RD repository contains only
`NO_RECONSTRUCTION_AT_STRONG_SHOCKS` in
`src/hydro/finite_volume_solver.c`. On an FV face it disables MUSCL spatial
reconstruction when the larger pressure exceeds the smaller by a factor 100.
This is a blunt emergency flattening rule, not a smooth `O(h)` sensor and not
directly meaningful for an element residual with three vertices.

The development tree `/home/zwu/arepo_dev/arepo` contains Kevin Schaal's full
AREPO shock finder (`src/shock_finder/`, about 5650 lines; Schaal et al. 2015,
2016). Its local shock-zone prefilter requires compression,

    div(v) < 0,

aligned temperature and density gradients,

    grad(T) dot grad(rho) > 0,

and a pressure/temperature/entropy jump consistent with a configurable minimum
Mach number (default `MachMin=1.3`). The full module then traces rays across
Voronoi neighbours, communicates them across MPI ranks, locates pre- and
post-shock states, and computes Mach number, surface area and dissipated energy.
In continuous mode it runs at the end of every local timestep and has special
full/active-mesh and time-bin handling.

That module is a diagnostic and subgrid-physics service, not the FV
reconstruction limiter and not a B coefficient. Porting it wholesale would
bring ray storage, MPI migration, output fields, runtime parameters and mesh
policy into RD without solving the mathematical `Theta=O(h)` requirement.
It is therefore not an appropriate thesis-path dependency.

The useful reusable idea is only the **local shock-zone predicate**. A future
experiment could build an element sensor `s_T` from the three vertex states and
already available AREPO gradients, then use

    Theta_eff = s_T Theta_B,

with `s_T -> 0` at least as `O(h)` in smooth flow and `s_T -> 1` in a shock
zone. Any elementwise `Theta_eff` preserves conservation, but positivity and
monotonicity do not follow: a false negative exposes LDA at a shock. A one-ring
shock buffer and an a-posteriori admissibility fallback to N/B would therefore
be part of a credible implementation. A pressure-based sensor also deliberately
does not detect a pure contact and cannot repair the parameter-vector contact
defect.

Focused-engineering estimates from the current code are:

| scope | estimate | result quality |
| --- | ---: | --- |
| binary local sensor prototype on equal-bin B | 2--4 working days | diagnostic only; no general guarantee |
| thesis-quality sensor with smooth-order, Sod/contact/KH, MPI and hierarchy gates | 2--4 weeks | defensible new B variant |
| wholesale Schaal shock-finder port and coupling | 4--8 weeks | unnecessary diagnostic infrastructure |

The cost is therefore large relative to the present thesis critical path. The
recommended decision is to record the selective sensor as future work, keep
the accepted frozen-total B as the documented production candidate, and move
next to B hierarchical timesteps. A sensor should be revisited only after the
static hierarchy and moving-mesh architecture are stable, so that it is not
validated twice against two changing time/geometry implementations.

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
concerns the sum of element total residuals and the nodal conserved ledgers;
RD does not exchange a separate FV-like flux across each shared edge.
`Theta` acts only on the *distribution* of an element residual, and
conservation of the blend holds elementwise for any `Theta` (Section 2). The
blend is therefore orthogonal to Construction A.

**(b) Is `Theta` well defined for a cross-bin element? Yes.** Under the
vertex-star freezing rule an element evaluates its residual from a coherent
triple -- frozen `U^sync` at frozen vertices, stage state at live ones -- so
`R` and `R_i^N` are exactly the quantities the element actually distributes,
and `Theta` follows from them with no new ambiguity.

**(c) When is it evaluated? Frozen is necessary but not by itself sufficient.**
In the two-call hierarchy the predictor call currently deposits
`-h_T phi_i^(0)/2` into the vertex ledgers immediately. The unfrozen
quadrature needs `Phi(U*)`, which does not exist until the closing call, so it
cannot multiply that opening contribution coherently.

The frozen-total numerator nevertheless contains the temporal target

    T_target = (|T|/3h_T) sum_j dU_j,

and each `dU_j` is complete only after the whole vertex star has been assembled
and exchanged. It is therefore **not known when the first individual triangle
is visited in the opening sweep**. The earlier shorthand "frozen is computable
at the open" means computable within the opening *call after star assembly*,
not in the present one-pass deposit loop.

A correct implementation must consequently use one of three architectures:

1. a two-pass opening call: assemble/exchange the complete nodal predictor,
   then revisit elements to compute frozen-total `Theta` and the opening
   ledger;
2. make the present spatial-B opening deposit provisional, then apply an exact
   closing correction using persisted stage-0 N/LDA branch data;
3. defer the complete B deposit to closing and persist/migrate all required
   stage-0 element history.

Option 1 is the cleanest static-mesh prototype, but the fixed `Theta` or the
stage-0 branch data still has to survive a coarse interval and domain
decomposition. Frozen remains much simpler than unfrozen and is selected by
the equal-bin acceptance tests, but lifting the compile guard is a small
multirate data-lifetime project rather than a local formula insertion.

### 8.1 Reserved fallback: a bounded spatial-Theta hierarchy experiment

If hierarchical B is later needed mainly for feature coverage, the
**spatial-Theta** variant has a substantially cheaper construction. Define at
the opening state

    Theta_T^n = min(1, |Phi_T(U^n)| / sum_i |phi_i^N(U^n)|),

then hold this coefficient over the element subinterval and distribute

    T_i^B = Theta_T^n T_i^lumped + (1-Theta_T^n) T_i^F1,

    R_i^B = T_i^B
            + 0.5 phi_i^B(U^n; Theta_T^n)
            + 0.5 phi_i^B(U*; Theta_T^n).

Unlike frozen-total `Theta`, `Theta_T^n` needs neither `T_target` nor a
star-complete predictor increment. It is available on the first opening visit.
The opening call may immediately deposit the old spatial half. At closing, the
same coefficient can be recomputed from the still-unsynchronised committed
`U^n` vertex states before applying `dU`; on the static mesh the canonical
three vertex IDs reconstruct the same physical triangle after domain
decomposition. This avoids persistent element-local N/LDA branch history.

Conservation remains elementwise because both temporal branches sum to the
same `T_target`, both spatial branches sum to their element residual, and a
convex blend preserves each sum. This construction must nevertheless retain
one opening coefficient over all three terms. Using `Theta(U^n)` for the old
half and `Theta(U*)` for the new half would define a different stagewise
limited method and would not collapse to the existing equal-bin frozen-spatial
control.

This route is reserved as an **experimental compatibility variant**, not a
replacement for accepted frozen-total B. Its measured quality is weak:

- advected glass Yee gives joint orders `0.898,0.864`, slightly below N at the
  highest measured pair;
- triangular Sod gives order about `0.56`, against about `0.80` for
  frozen-total B;
- the spatial indicator remains `O(1)` in smooth flow and has no second-order
  guarantee.

If resumed, the work is a bounded spike:

1. implement only static-mesh, hierarchical, frozen-spatial B;
2. require exact equal-bin collapse to `RD_B_SPATIAL_THETA +
   RD_B_FROZEN_THETA`;
3. run two-level Yee with alternative interface placement;
4. run Sod crossing the bin interface and the coarse-island geometry;
5. require positivity, round-off conservation and one/four-rank particle-ID
   agreement;
6. stop immediately if recomputation does not reproduce the opening
   coefficient after rebuild or if the hierarchy enlarges the existing
   spatial-B error pathologically.

Estimated focused effort is `3--6` working days. The deliverable would be
labelled `experimental spatial-Theta B hierarchy`; it would add a supported
execution mode but would not improve B accuracy. The current project decision
is **not to run this spike now**: moving-mesh N, then LDA, has priority. This
section exists so the cheaper construction is not lost if later thesis or
review requirements demand a hierarchical B entry.

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
- `RD_DIAG_THETA_MAP` -- the final-corrector element map used in Section 4.5;
  it records already computed quantities and does not alter the update.

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
