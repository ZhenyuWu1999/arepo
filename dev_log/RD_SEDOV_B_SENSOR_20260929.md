# Classical RD B/Bmax sensors in the LDA/Rusanov prototype

Author: Codex, 2026-09-29. User requested trying corrections already used in
RD, rather than first developing additional local state constraints.

## Literature and the specific experiment

The selected method is the classical RD residual-ratio B blending rule:

    theta_k = |sum_i D^L_{k,i}| / sum_i |D^L_{k,i}|,
    D^B_{k,i} = (1-theta_k) D^H_{k,i} + theta_k D^L_{k,i}.

Zero denominator gives theta=0. Bmax replaces all four theta_k by their maximum.
The ratio is evaluated in conserved components, matching the diagonal form
described in Morton et al., not a characteristic projection.

Sources checked in full relevant sections:

- Morton, Khochfar & Wu, *A New Residual Distribution Hydrodynamics Solver
  for Astrophysical Simulations*, §2.2.3, Eqs24–25 and the Bmax/Bmin discussion:
  https://arxiv.org/html/2204.01757v2 . Their low branch is N.
- Ricchiuto & Abgrall2010, *Explicit Runge-Kutta Residual Distribution schemes
  for Time Dependent Problems: second order case*, §5.2, Eq54: blend complete
  time-dependent residuals, including both mass/spatial contributions. Their
  Euler implementation uses characteristic projection, which this transplant
  does not reproduce. Author-uploaded full text:
  https://www.researchgate.net/publication/223033482_Explicit_Runge-Kutta_Residual_Distribution_schemes_for_Time_Dependent_Problems_second_order_case
  DOI:10.1016/j.jcp.2010.04.002.
- Bacigaluppi, Abgrall & Tokareva, *A Posteriori Limited High Order and Robust
  Schemes…*, §4, Eqs29–37,43–47:
  https://arxiv.org/html/1902.07773v2 . A separate RD route is Rusanov-PSI+jump
  with a MOOD cascade, not the B experiment implemented here. Their tests
  include Euler shock problems but not Sedov; no claim to reproduce that
  algorithm or its results is made.

This experiment transplants the published B/Bmax sensor and complete RK
mixing into our existing common-Gauss Rusanov/LDA branches. Rusanov replaces
the original N endpoint, and the existing coupled positivity guard remains
outside the candidate B update. Consequently it is not a verbatim reproduction
of published LDA/N, RPJ or MOOD. No bespoke entropy, density/velocity bound,
shock threshold, analytic Sedov information or tuning parameter is added.

## Complete RK update and the corrected first attempt

Write H0,L0 for old spatial LDA/Rusanov residuals and A0 for the actually
accepted predictor residual after both B mixing and positivity limiting.
The predictor satisfies S dU=-dt sum_T A0. In the corrector define

    Hnew_i = T_i^F1(dU) + .5 H_i(U*),
    Lnew_i = |T| dU_i/(3 dt) + .5 L_i(U*),
    D^L_i  = Lnew_i + .5 L0_i.

Use D^L to compute the total-residual theta (spatial residuals at predictor).
The desired full B residual is

    B_i = (1-theta)(Hnew_i+.5 H0_i) + theta(Lnew_i+.5 L0_i).

The local LDA engine starts the corrector from Q*+.5 S dU, whereas the full B
form starts from Q*. Therefore the residual for that engine is B_i-.5 A0_i.
Relative to the guaranteed-admissible SSP low candidate, the correction is

    C_i^T = -dt [(1-theta)(Hnew_i-Lnew_i)
                 + .5 ((1-theta)H0_i + theta L0_i - A0_i)].

Every conserved component has the same element sum in H0,L0,A0, and in
Hnew,Lnew. Hence sum_i C_i^T=0, also for component-wise theta. A common scalar
positivity factor ell_T then limits this complete correction at all vertices
and in every component, preserving the existing convex-assembly argument.
Without outer limiting this is the full B candidate; with limiting it is a
conservative, positive blend toward that candidate. No entropy theorem follows.

The first attempt, archive `../local_runs/sedov_rd_bsensor_20260929_v1/`,
multiplied only the previously existing high-minus-low correction by 1-theta.
It omitted replacement of the old accepted spatial half by the two raw old
branches. Smooth-contact errors were .00239354/.000960967/.000446276 at
16/32/64, orders1.31659/1.10655. This exposed a numerical implementation defect,
not an environment failure or evidence against the full B method. Both v1
Sedov runs were deliberately terminated after about212s (returncode-15), not
used as completed scientific comparisons. Their outputs/configs/source and
`attempt_note.json` are preserved. The corrected v2 source retains all three
old residuals and uses the expression above.

## Implementation, provenance and completed gates

Explicit option `RD_LDA_RUSANOV_B_SENSOR=1` selects component-wise B;
`=2` selects Bmax. It requires `RD_LDA_RUSANOV_BLEND=1`, inheriting the static,
periodic, full mesh, equal-step, single-rank, unsplit RK restrictions.
The option is absent from default Config. Existing source work is preserved.

- `src/hydro/rd_lda_rusanov.h`: ratio and complete-corrector helpers.
- `src/hydro/residual_distribution_solver.c`: old-branch retention, candidate
  correction, stage-specific sensor statistics.
- `tests/rd/test_lda_rusanov.py`: compiled checks against independent formulas.
- `examples/Sedov_2d/run_blend.py --b-sensor`: two-build comparison.
- `examples/Sedov_2d/analyze_bsensor.py`: provenance/positivity/budget/entropy
  verification, profiles and scatter/convergence measurements.

Frozen archive: `../local_runs/sedov_rd_bsensor_20260929_v2/` with dirty source,
source hashes, builds, configuration, header, native linkage, input hashes and
logs. Two singleton solvers at most; both OMP_NUM_THREADS and OPENBLAS_NUM_THREADS
are1. B binary SHA256 f5cc41f4ea893015bc487f0d0cb89373647674a0d7b523dca0db7480bdbb98de;
Bmax9ddfa0fdfea4e218bb38eaf0509dbbd4a2e89c9d8455121dc83cccc164bc4c0b.

Compiled checks pass2000 inflow/positive conservative patch cases,1000 B/Bmax
ratio/common-total/unit-rescaling cases, and1000 complete RK correctors compared
with an independently assembled full old/new B update. Both v2 uniform native
gates and six regular smooth-contact runs complete. Smooth test is the same
rho=1+.2sin(2pi(x+y)), v=(.37,-.21), p=1, gamma5/3, unit box, t=.1,
dt_cap=1/8192 as the original blend experiment, at16^2/32^2/64^2 nodes.

For B, density L1 errors are .00192428451/.000573971430/.000158526634,
orders1.74527/1.85625; Bmax agrees within1.6e-13 in these error values.
The trend is toward second order, with larger errors than the original
positivity-only/LDA contact result. It is not a Yee or glass convergence proof.

## Sedov comparison

V2 science uses byte-identical archived glass128^2 ICs,21 heated nodes, unit
periodic box, gamma5/3, rho1, background pressure1e-6, injected thermal energy1,
CFL.1, timestep cap.01, finalt=.05, five snapshots. Reference controls are the
original positivity-only LDA/Rusanov and common-Gauss Rusanov from
`../local_runs/sedov_lda_rusanov_20260929_v1/`; no new low endpoint is introduced.
All schemes use adaptive equal timesteps, so step counts can differ.

All10 v2 native runs completed;50 new saved states passed finite/positive
rho,p,mass, EOS, fixed coordinates/IDs and budget checks. Both uniform defects
are5.55e-16. The existing five `make check_rd` targets passed on final source;
the log is `algebra.log`. Production and kernel-test hashes match frozen v2.

| Method | Steps | rho_min | raw rho_max | dr=.005 radial mean rho peak | final dE/E |
|---|---:|---:|---:|---:|---:|
| Prior positivity-only blend | 4689 | .0191126 | 3.79111 | 2.79825 | -2.22e-16 |
| Component B | 3102 | .000651475 | 10.0045 | 2.37938 | -8.88e-16 |
| Bmax | 2559 | .0839697 | 2.17861 | 2.14706 | 0 |
| Common-Gauss Rusanov | 2476 | .124614 | 2.00629 | 1.96123 | +6.66e-16 |

At .05<=r<.1,386 identical nodes, weighting by median dual area, removing a
weighted linear radial trend separately in bins of width .005:

| Method | radial-velocity scatter RMS | tangential RMS | mean radial velocity |
|---|---:|---:|---:|
| Prior positivity-only blend | .158645 | .0655025 | .468728 |
| Component B | .0920415 | .0595461 | .514520 |
| Bmax | .00387403 | .00481091 | .461283 |
| Rusanov | .00460087 | .00374668 | .476766 |

Bmax reduces radial scatter by40.95 relative to the prior blend, while the
tangential RMS improves13.62 times. Rusanov itself is similarly smooth. Bmax
retains modestly sharper structure than pure low order, but remains much more
diffusive than the original blend near the front. Component B's enormous
density spread (raw peak10.0 versus mean peak2.38) makes it unsuitable despite
partial improvement in interior velocity scatter. Different component ratios
do not supply an oscillation guarantee for coupled Euler variables.

For r<.05,130 nodes, unweighted core means:

| Method | mean density | mean pressure |
|---|---:|---:|
| Prior positivity-only blend | .0276862 | 1.607414 |
| Component B | .0502072 | 1.573309 |
| Bmax | .0878259 | 1.548757 |
| Rusanov | .1357222 | 1.443428 |
| Analytic values at these nodes | .00435268 | 1.605099 |

Entropy is audited, not constrained. Relative to initial K_min=1e-6, final
minimum K ratios / counts below the initial bound by relative>1e-8 are:
prior blend3.47320e-5/527; component B .0688545/56; Bmax .999770/47; low1/0.
Bmax's largest global minimum deficit is .0230%, small but not roundoff or a
strict entropy guarantee. Its pressure minimum is9.999999999796e-7. Component
B pressure minimum is2.28108e-8. A minimum principle and a full discrete entropy
inequality remain distinct, neither being established by this sensor.

All6204 B and5118 Bmax stage checks pass; actual CFL sums max .0999850/.0998915
remain below the sufficient bound1. Saved maximum absolute energy drift is
1.11e-15/2.22e-16, mass1.11e-16/2.22e-16. Mean fractions of elements limited by
the outer positivity guard are .00308104/.0000195818. Bmax mean theta across
all box elements and all times is .984672 at predictor/.921883 at corrector;
these include quiescent elements and must not be presented as shock-only
fractions or physical viscosity norms. B component means are recorded in JSON.

Runtime B458.08s/Bmax378.64s with different step counts; no optimized performance
claim. All native processes have finished. No moving extension, thesis edit,
COSMA operation, commit or push was performed.

The four-method profile figure and the focused Bmax comparison were visually
checked. Full comparison includes every component-B outlier; the separate
focused plot explicitly omits that rejected candidate rather than clipping its
outliers to improve appearance. Outputs:

- `analysis/rd_bsensor_profiles.png` / `.pdf`: all four methods, full/core view.
- `analysis/rd_bmax_comparison.png` / `.pdf`: Bmax versus original blend/low.
- `analysis/verification.json`:50 new states, source/binary/IC/snapshot hashes,
  positive stages, budgets, entropy, scatter, smooth convergence.
- `analysis/plot_bmax_only.py`: archived producer for the focused figure.

Conclusion: the published RD sensor is useful here in its scalar Bmax form as
a conservative positive practical baseline with small scatter, but sacrifices
much of LDA's shock sharpness. It does not complete the Sedov research problem.
The next distinct literature route would be characteristic limiting/Rusanov-PSI
with appropriate stabilization and RD-MOOD, not claiming that the present
component-wise B transplant has reproduced those algorithms.
