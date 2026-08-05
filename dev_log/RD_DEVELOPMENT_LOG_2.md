# AREPO Residual Distribution Development Log, volume 2: moving mesh

This is the **active** development log. It succeeds
`dev_log/RD_DEVELOPMENT_LOG.md`, which is closed at its final entry of
2026-08-04 and kept as the record of the static-mesh phase.

- Opened: 2026-08-05.
- Time zone: Europe/London.
- Scope: the ALE / moving-mesh phase, and anything else that arises from here
  on. Volume 1 is not reopened; corrections to it are recorded here with a
  pointer, so that the two read as one chronology.

Why a new volume: volume 1 reached 8971 lines and no longer fits comfortably in
an agent context window, which had begun to cost re-derivation of settled
facts. The split is administrative. Nothing in volume 1 is retracted by it.

---

## 1. State at handover

### 1.1 What is settled and must not be reopened without cause

- **Spatial schemes.** N, LDA and B all run on the static mesh with the
  conservative parameter-vector (Roe) linearisation and the median-dual control
  area `|S_i| = sum_{T in i} |T|/3`.
- **Time integration.** `RD_RK2_TOTAL_RESIDUAL` implements the Arpaia &
  Ricchiuto two-step explicit RK with the F1 mass matrix. Production LDA uses
  standard GL+F1; the rate-consistent Heun variant is retained as a thesis
  discussion topic only, not as production. See
  `dev_log/LDA_F1_Heun_vs_standard_LDA_RK2.md`.
- **Order.** Advected Yee on the glass, joint `(dx, dt)` refinement, analytic
  density L1: LDA 1.879 / 1.737, N 0.939 / 0.995, B (total, frozen)
  1.421 / 1.064. The earlier apparent order loss at large `n` was the mesh
  family, not the scheme: `E = A/n^2 + B/n` with `B` proportional to the
  median-dual asymmetry `|g|/h`. See `dev_log/mass_matrix_order_analysis.md`.
- **B scheme.** Frozen total-residual `Theta` is the accepted static
  equal-timestep shock candidate. Frozen and unfrozen agree to within 0.4 per
  cent, so the simpler frozen form is adopted; the temporal term in `Theta`,
  by contrast, matters by a factor of 4.3 at `n=192`. Complete mathematics in
  `dev_log/B_scheme_complete_mathematics.md`. Committed as `89b23e0`.
- **Hierarchical timesteps.** N and LDA are validated, using Construction A and
  the frozen vertex-star contract. Design in
  `dev_log/RD_hierarchical_timestep_conservation_design.md`, prototype in
  `dev_log/RD_hierarchical_timestep_phaseb_prototype.md`.
- **Conservation and MPI.** Round-off element and global conservation, and
  invariance between 1, 4 and 16 ranks by particle ID, are established for the
  static cases above.

### 1.2 What is deferred, and by whose decision

- **B hierarchical timesteps** — deferred by Zhenyu's sequencing decision
  recorded in volume 1, 2026-08-04. It would add an execution mode to the
  least accurate smooth-flow candidate without improving the method. A
  spatial-`Theta` fallback spike is specified in
  `B_scheme_complete_mathematics.md` §8.1 if thesis completeness later demands
  it.
- **The contact-discontinuity defect** — shelved with conditions. The defect
  has a closed form, `Delta p / p = (sqrt(rho_L) - sqrt(rho_R))^2 /
  (4 sqrt(rho_L rho_R))`, depends only on the density ratio and not on `h`, and
  repairing it is out of thesis scope. It is documented as an RD limitation.
- **A new shock or smoothness sensor, MOOD-like fallback, 3-D, gravity,
  refinement** — future work.

### 1.3 Conventions carried over from volume 1

- Do not build or run on the login node `cuillin`; submit through Slurm. MKL
  exists only on the compute nodes, so always check `ldd` for `libmkl_rt`
  before trusting a binary.
- The immutable build artifact manifest and checksum are authoritative. Do not
  validate against the repository-root `Arepo`, `build/arepoconfig.h` or
  `Config.current.build`.
- Every new config macro must be declared in `Template-Config.sh` and
  `defines_extra`, or `check.py` fails the build.
- Commit authorship is passed per commit, never set repository-wide:
  `git -c user.name="Zhenyu Wu and Claude Code (Opus 5)" -c
  user.email="2756679409@qq.com" commit ...`, keeping the `Co-Authored-By:`
  trailer, and naming whichever agent produced the content.
- Do not commit without being asked.

### 1.4 Open questions inherited from volume 1

1. **Why the mean `Theta` does not predict the order**, and why the direction is
   counter-intuitive: at `boost=0` the mean `Theta` is larger (0.41-0.43, flat
   in `h`) yet the order is better (1.83/1.30), while at `boost=1` it is smaller
   (0.09-0.24) and the order worse (1.42/1.06). The spatial distribution of
   `Theta` relative to the local error is the likely explanation and has not
   been measured. Awaiting Codex's review. As of 2026-08-05 an uncommitted
   working-tree change adds `RD_DIAG_THETA_MAP`, a final-step per-element map
   of `Theta` and the B-minus-LDA correction, which is exactly the measurement
   this question needs; it is another agent's work in progress and is not part
   of the moving-mesh phase.
2. The `t = 0.511` advected-contact failure on the regular triangular lattice,
   which the vertex-alignment hypothesis did not explain.
3. Restart across an open RK stage.

---

## 2. Reference literature for this phase

Volume 1 established the primary formulation. Kimi contributed the lineage
below on 2026-08-05; the bibliographic data have been verified independently,
but note that most of the URLs Kimi supplied point to *papers that cite* the
work rather than to the work itself, so DOIs are given here instead.

### 2.1 ALE residual distribution

| work | what it gives us |
| --- | --- |
| **Michler, De Sterck & Deconinck (2003)**, *An arbitrary Lagrangian Eulerian formulation for residual distribution schemes on moving grids*, Comput. Fluids **32**, 59-71, `10.1016/S0045-7930(01)00095-0` | the earliest moving-grid RD ALE formulation, including the geometric source terms for deforming meshes |
| **Arpaia, Ricchiuto & Abgrall (2015)**, *An ALE formulation for explicit Runge-Kutta residual distribution*, J. Sci. Comput. **63**(2), 502-547, `10.1007/s10915-014-9910-5` | **the reference formulation.** Explicit two-step RK, second order in space and time, fully conservative, DGCL-compliant. The static RK2-RD already implemented is its `sigma = 0` special case. Local copies: `MyThesis/useful_resources/2015_Arpaia_An_ALE_Formulation_for_Explicit_Runge–Kutta_Residual_Distribution.pdf`, preprint at `https://inria.hal.science/hal-00863154`. Equations transcribed in `RK2_timestep_movingmesh_analysis.md` §7.2 |
| **Arpaia & Ricchiuto (2018)**, *r-adaptation for shallow water flows: conservation, well balancedness, efficiency*, Comput. Fluids **160**, 175-203 | r-adaptation application of the same ALE-RD machinery |
| **Arpaia & Ricchiuto (2020)**, *Well balanced residual distribution for the ALE spherical shallow water equations on moving adaptive meshes*, JCP **405**, 109173 | as above, on the sphere |
| **Campoli, Quemar, Bonfiglioli & Ricchiuto**, *Shock-fitting and predictor-corrector explicit ALE residual distribution* | independent confirmation of the two-step explicit structure |
| **Isola, Guardone et al. (2022)**, *An ALE residual distribution scheme for the unsteady Euler equations over triangular grids with local mesh adaptation*, Comput. Fluids, `10.1016/j.compfluid.2022.105414`, building on **Guardone, Isola & Quaranta (2011)**, JCP **230**, `10.1016/j.jcp.2011.06.026` | **the only RD treatment of topology change.** Edge swap, node insertion and node deletion are interpreted as a series of fictitious continuous deformations of the dual mesh, which enforces the GCL by construction and needs no interpolation between connectivities |

**Kimi's key observation, which this project must not lose:** every one of the
Arpaia-Ricchiuto works is a *continuous-deformation, fixed-connectivity*
framework — the whole point of r-adaptation is to move nodes without
reconnecting. AREPO's Delaunay triangulation reconnects whenever the generators
move. So the reference formulation covers our geometry but not our
connectivity; only Isola-Guardone covers the latter, and it does so for
adaptation-driven swaps rather than for the continual reconnection of a
Lagrangian mesh.

**A second gap, identified here:** in all of this literature the mesh velocity
is an adaptation or shock-fitting velocity, explicitly *not* the fluid
velocity. **No ALE-RD paper operates at AREPO's design point, `sigma`
approximately `u`.** Section 4.3 below is the first measurement of what happens
there.

### 2.2 The geometric conservation law

| work | what it gives us |
| --- | --- |
| **Thomas & Lombard (1979)**, *Geometric conservation law and its application to flow computations on moving grids*, AIAA J. **17**(10), 1030-1037, `10.2514/3.61273` | the original GCL |
| **Lesoinne & Farhat (1996)**, CMAME **134**, 71-90, `10.1016/0045-7825(96)01028-6` | a unified derivation of GCLs across ALE finite volume, finite element and space-time formulations |
| **Guillard & Farhat (2000)**, *On the significance of the geometric conservation law for flow computations on moving meshes*, CMAME **190**, 1467-1482, `10.1016/S0045-7825(00)00173-0` | GCL violation is not always fatal, but free-stream preservation is the safe design criterion |
| **Farhat, Geuzaine & Grandmont (2001)**, JCP **174**, 669-694, `10.1006/jcph.2001.6932` | DGCL compliance is necessary and sufficient for nonlinear stability of sample ALE schemes, and preserves the fixed-grid order of time accuracy |

The last of these is why the DGCL is verified **per element** in the gates
below, rather than only through a global free-stream test: a global test can
pass while individual elements violate it with compensating errors.

### 2.3 Adjacent, for orientation rather than for porting

- **Gaburro, Boscheri, Chiocchetti, Klingenberg, Springel & Dumbser (2020)**,
  *High order direct ALE schemes on moving Voronoi meshes with topology
  changes*, JCP, `arXiv:1905.00967` — a finite-volume, not RD, treatment, but
  the closest published work to AREPO's actual mesh.
- **Abgrall & Tokareva (2017)**, *Staggered grid residual distribution scheme
  for Lagrangian hydrodynamics*, SIAM J. Sci. Comput. **39**, A2345-A2364 —
  RD taken to the fully Lagrangian limit, where they move to a staggered
  discretisation. Worth understanding before assuming a collocated RD must
  degrade there; §4.3 below suggests it need not.

---

## 3. 2026-08-05: feasibility assessment, and the decision to start

- Author: `Claude Code Opus 5`, at Zhenyu's request to review progress, judge
  whether moving mesh can start, and assess mathematical and engineering
  feasibility.
- **No solver source was changed in this entry.** Everything below is either a
  code audit or an offline measurement.
- Measurement code: `Hydro_data_analysis/Analysis/moving_mesh/ale_feasibility.py`.
  It needs no build, no cluster and no solver; it evaluates geometric and
  linear-algebra properties directly from the production mesh families and the
  analytic states, and reproduces every number quoted here.

### 3.1 Verdict

**Moving mesh can start.** Three structural prerequisites that earlier entries
listed as outstanding turn out to be already satisfied, and the two risks that
were rated highest are now measured rather than assumed.

### 3.2 The three prerequisites, audited

**(a) The main loop is already in the structure ALE requires.**
`RK2_timestep_movingmesh_analysis.md` §7.5 concluded that ALE needs "option A",
both RK stages inside a single `compute_residuals` call, because AREPO rebuilds
the mesh between the two call sites and the ALE residual needs `K^n`,
`K^{n+1/2}` and `K^{n+1}` within one evaluation. That restructuring was
completed as a side effect of `RD_RK2_TOTAL_RESIDUAL`:
`residual_distribution_solver.c:1352` loops over all stages inside one call and
the first call site at `run.c:230` is a documented no-op. **The largest
structural change ALE was thought to need is done.**

**(b) The old configuration is free.** `predict.c:383` drifts with
`P[i].Pos[j] += SphP[i].VelVertex[j] * dt_drift` — exactly linear. Hence
`x^n = x^{n+1} - VelVertex * dt` and `x^{n+1/2} = x^{n+1} - VelVertex * dt/2`
can be formed in the corrector without storing old coordinates and without a
second mesh construction. `set_vertex_velocities()` is called before the drift
and not again before the corrector, so the `VelVertex` seen by the corrector is
the one that produced the drift. The DGCL's half-time configuration therefore
costs nothing beyond evaluating existing geometry at shifted coordinates.
(This holds only while `FORCE_EQUAL_TIMESTEPS` is on, since with a hierarchy
only active cells drift. That restriction is already in the phase scope.)

**(c) Nothing is left blocking.** B is committed and closed; B hierarchy is
deferred by decision, not by obstruction.

### 3.3 Risk 1, topology change: measured, and largely dissolved

The concern was that AREPO's Delaunay connectivity changes between `t^n` and
`t^{n+1}`, so the element `K^n` required by the ALE residual may not exist.
Volume 1 rated this the dominant uncertainty of phase M2 at 2-4 weeks.

**The observation that changes the estimate.** A Delaunay flip is triggered by
four points becoming *co-circular*, not co-linear. The post-flip diagonal is
therefore normally still a valid, merely non-Delaunay, triangulation of the
*pre-flip* vertex positions, and the two triangulations cover exactly the same
quadrilateral. If the ALE residual is assembled on the **new connectivity** with
geometry evaluated separately at `x^n`, `x^{n+1/2}` and `x^{n+1}`, both
configurations tile the domain exactly and no interpolation, remapping or
fictitious deformation is needed. The construction fails only where an element
of the new connectivity is **inverted** at the old positions, which happens when
the quadrilateral was non-convex at `t^n` or when flips cascade within one step.
Detection is free: the sign of `|T^n|`.

**Measurement** (glass IC, Lagrangian vertex motion, periodic Delaunay, 30
steps):

| problem | CFL | elements inverted at `t^n` | worst step | signed-area tiling defect |
| --- | ---: | ---: | ---: | ---: |
| Yee vortex, `n=48` | 0.03 / 0.3 / 0.8 | **0 / 0 / 0** | 0 | 0 |
| Yee vortex, `n=96` | 0.03 / 0.3 / 0.8 | **0 / 0 / 0** | 0 | 0 |
| KH shear, `n=48` | 0.3 / 0.8 | 0.271% / 0.696% | 24 / 49 | 0 / 1.1e-16 |
| KH shear, `n=96` | 0.3 / 0.8 | 0.138% / 0.339% | 43 / 83 | 0 / 0 |

For contrast, the rate at which connectivity changes *at all*:

| problem | production `dt = 0.25/n` | CFL ~ 0.3 |
| --- | ---: | ---: |
| Yee, glass `n=48` | 0.0014%, 1 step in 30 | 0.639%, 27 steps in 30 |
| Yee, glass `n=96` | 0.0007%, 2 steps in 30 | 0.228%, 28 steps in 30 |
| KH, glass `n=48` | — | 0.690%, 28 steps in 30 |

Three conclusions:

1. **Connectivity change is common at production CFL and rare only because the
   Yee campaign's `dt = 0.25/n` corresponds to CFL ~ 0.03.** At CFL 0.3 both
   the smooth vortex and the shear layer reconnect on essentially every step.
   The distinction between the two problems is not how often they flip but
   whether the flips are benign.
2. **On smooth problems the flips are entirely benign** — zero inverted
   elements up to CFL 0.8. The whole M1/M2 accuracy programme (Yee, Gresho,
   free-stream, DGCL, convergence) can therefore be run with the plain
   new-connectivity construction and no topology machinery at all.
3. **Under shear, 0.14 to 0.70 per cent of elements per step need a fallback.**
   Note that the **signed**-area sum stays exactly the box area even on steps
   containing inverted elements: the negative areas cancel the doubly covered
   region. So conservation survives a flip; what an inverted element breaks is
   the sign of the normals, hence upwinding and positivity. This is a stability
   problem, not a conservation problem, which is the easier of the two to
   contain.

### 3.4 Risk 2, the Lagrangian limit: real, bounded, and it exposes a code defect

The ALE flux Jacobian is `A(n) - (sigma.n) I`, so at `sigma = u` the advective
eigenvalues vanish, every `K_j^-` falls to rank one and `S^- = sum_j K_j^-` is
singular with rank at most 3. LDA needs `(S^-)^{-1}`. Volume 1 §7.5 already
noted that the stagnation degeneracy "becomes generic rather than exceptional"
under ALE; this quantifies it.

The right parameter is `w = |u - sigma| / c`, because
`REGULARIZE_MESH_CM_DRIFT_USE_SOUNDSPEED` caps the regularisation drift as a
fraction of the sound speed. Glass `n=48`, Yee, 400 elements, drift direction
randomised per element:

| `w` | takes the SVD path | median LU pivot ratio | `norm(beta)` median / p99 | `norm(sum_i beta_i - I)` | conservation defect, median |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1e-1 | 0% | 6.5e-2 | 2.19 / 2.88 | 1.1e-15 | 5.3e-16 |
| 1e-3 | 0% | 8.6e-4 | 2.22 / 3.55 | 1.9e-15 | 7.6e-16 |
| 1e-6 | 0% | 1.0e-4 | 2.22 / 3.57 | 8.8e-13 | 7.5e-14 |
| 1e-10 | 0% | 1.9e-6 | 2.22 / 3.57 | 2.2e-07 | 7.6e-10 |
| **0** | **46.2%** | **2.3e-12** | 2.21 / 3.57 | **1.0** | 2.5e-15 |

**The LDA coefficients stay bounded.** Median `norm(beta) = 2.2`, p99 3.6,
unchanged across ten decades of `w` including the exact Lagrangian limit. The
reason is structural: the near-null direction of `S^-` is the vanishing
advective eigenvector, and `K_i^+` annihilates the same direction, so the
singularity of the product `-K_i^+ (S^-)^{-1}` is **removable**. Linearity
preservation depends on `beta` being bounded, and that survives. This is the
first evidence that a collocated RD need not degrade in the Lagrangian limit
the way Abgrall & Tokareva's move to a staggered grid might suggest.

**What does degrade is the algebraic identity.** At `w = 0` the pseudo-inverse
gives `sum_i beta_i = S^- (S^-)^+`, a rank-3 projector, so
`norm(sum beta - I) = 1`. Conservation nevertheless holds to 2.5e-15, because
the element residual `Phi` turns out to lie in `range(S^-)`. **That is an
empirical observation on a smooth solution, not a proof** — the maximum defect
over the 400 sampled elements is 2.5e-12, three orders above the median, and
nothing has been checked at a shock. Verifying it on the Sod is an M1 gate.

**And it exposes a defect in the existing code.**
`residual_distribution_solver.c:17` sets `RD_LU_FALLBACK_PIVOT_RATIO = 1e-12`.
The pivot ratio falls roughly like `sqrt(w)`, so at `w = 1e-10` it is still
1.9e-6, far above the trigger; the SVD path never fires for any `w > 0`. At
`w = 0` exactly the *median* pivot ratio is 2.3e-12 — pure round-off — and sits
directly **on** the threshold, so 46 per cent of elements take the SVD path and
54 per cent take LU. (§3.5 shows the distribution behind that median is smeared
right across the threshold, which makes the conclusion stronger and the
proposed remedy wrong.) On the LU path at `w = 0` the coefficients reach p99 `1.3e6`,
which is the result of inverting round-off. This matters because
`set_vertex_velocities.c:166` switches the regularisation drift off entirely
once a cell is round enough, so on a moving mesh `sigma = u` holds *exactly* on
a large fraction of cells — the degenerate case is the common case, not an edge
case. Worse, which branch an element takes would then depend on round-off, and
therefore on the domain decomposition, breaking MPI rank invariance.

**Proposed action, since withdrawn -- see §3.5.** The first version of this
entry proposed raising `RD_LU_FALLBACK_PIVOT_RATIO` to `1e-8`, on the grounds
that the median pivot ratio is above `1.9e-6` for every `w >= 1e-10`, so no
working case would change branch. Zhenyu asked what the evidence for `1e-8`
was. It does not survive the check.

### 3.5 The pivot threshold: the proposed fix withdrawn, and the actual one

Zhenyu asked what the evidence for `1e-8` was. The answer is that there was
none worth the name: the number came from medians. Measuring the **whole
distribution** over complete production configurations
(`Analysis/moving_mesh/pivot_threshold_evidence.py`; the solver logs only
`min_pivot_ratio`, which cannot answer this) rejects it on two independent
grounds.

| configuration | min | median | SVD at `1e-12` | SVD at `1e-8` | elements that change branch |
| --- | ---: | ---: | ---: | ---: | ---: |
| Yee `boost=1`, static | 3.1e-3 | 3.5e-1 | 0 | 0 | **0** |
| Yee `boost=0`, static | 3.5e-10 | 1.1e-3 | 0 | 85 (1.85%) | **85** |
| Sod, `t=0`, static | 0 | 0 | 100% | 100% | 0 |
| Yee `boost=0`, Lagrangian | 0 | 1.8e-12 | 46.9% | 86.5% | 1814 |
| Yee `boost=1`, Lagrangian | 0 | 4.8e-16 | 100% | 100% | 0 |

**First: it would silently alter an accepted result.** 85 elements (1.85 per
cent) of the static `boost=0` Yee lie in `[1e-10, 1e-8)`. That is the very
campaign used for the Morton cross-check of 2026-08-04, whose LDA orders
2.043/2.076 are already recorded and cited. Raising the threshold moves those
elements to a different solver for no benefit on that case, and the recorded
numbers would have to be re-earned.

**Second, and decisive: it does not fix the mechanism.** On the Lagrangian
mesh the pivot ratio is not smeared *near* the threshold, it is smeared
*across* it — a continuous distribution from 0 to 1e-2 with median 1.8e-12.
No threshold separates the populations. A cut at `1e-8` still leaves 13.5 per
cent of elements on the LU path carrying pivot ratios between `1e-8` and
`1e-2`, even though `sigma = u` holds exactly there and the true singular-value
ratio is around 1e-18 (§3.4). **The LU pivot spread is not a monotone proxy for
degeneracy once the mesh moves with the fluid**, which is what the code comment
at line 15 says in the first place. Moving the cut only relocates an arbitrary
line.

What survives is the concern, in stronger form: since the distribution straddles
the threshold, which branch an element takes is decided by round-off, hence
potentially by the domain decomposition, which threatens MPI rank invariance.

**Revised action.** Leave `RD_LU_FALLBACK_PIVOT_RATIO` alone — the static path
is cleanly separated (`boost=1` minimum 3.1e-3, four orders clear) and does not
need it. Instead make the **ALE compile path bypass the trigger entirely**, by
requiring the existing `RD_ALWAYS_PSEUDOINVERSE`, whose comment at
`residual_distribution_solver.c:564` already states the property needed here:
"free of the pivot-ratio branch, so the result is independent of the domain
decomposition". Decomposition independence then holds by construction rather
than by a threshold argument.

On cost, one piece of evidence exists already: at `t = 0` the Sod tube has
`u = 0` in both undisturbed states, so the pivot ratio is exactly zero for
100 per cent of elements and the case runs entirely on the SVD path — and it is
among the solver's better results. That is a `t = 0` snapshot and the fraction
falls once the waves develop, so it bounds nothing precisely. The real
comparison is one case run with and without `RD_ALWAYS_PSEUDOINVERSE`, which is
cheap and belongs in M1.

### 3.6 What these measurements do not cover

- They use prescribed Lagrangian motion of an analytic velocity field on a
  glass — no regularisation, no feedback from the solution. Regularisation
  reduces distortion and should reduce flips, so the topology numbers are
  believed conservative, but this is not verified.
- `Phi in range(S^-)` is checked only on a smooth solution.
- The "new connectivity is valid at old positions" argument fails exactly on
  the measured 0.14-0.70 per cent, i.e. non-convex quadrilaterals at `t^n` and
  cascading flips. No treatment of those is proposed here beyond detection.

---

## 4. The phase plan

This revises the M0-M3 sequence proposed by Codex in volume 1, 2026-08-04. The
skeleton and all of its gates are retained; the weights change because of
§3.3 and §3.4.

**Scope exclusions for the whole phase** (unchanged): hierarchical time bins
stay off, B and every nonlinear sensor stay out, no gravity, no
refinement/derefinement, no source terms, 2-D only.

### M0 — derivation and data-lifetime audit, 3-5 days

Write the discrete update the code will implement and map every term to
Arpaia-Ricchiuto; specify ownership and lifetime of the vertex coordinates at
`n` and `n+1`, the half-time normals and areas, the old and new median-dual
areas, element correspondence, and stage state under MPI. Distinguish the
predictor's geometrically non-conservative residual from the corrector's
conservative one.

Shorter than Codex's 5-10 day estimate because the main-loop restructuring is
already done and `x^n` needs no storage design. Two additions to the
deliverable:

- adopt the **new-connectivity-at-both-times** construction of §3.3 as the
  baseline, and state its validity condition explicitly;
- make `|T^n| <= 0` an explicit, counted gate from the first prototype, rather
  than something discovered in M2.

**M0 gate:** a reviewed algebraic element and vertex identity proving global
conservation and the DGCL, before any physics code changes.

### M1 — prescribed motion, N only, DGCL, 5-8 days

Codex's six gates are retained verbatim: `v_mesh = 0` collapse to the static N
result; free-stream preservation under a non-trivial periodic deformation;
per-element DGCL `|T^{n+1}| - |T^n| = dt * integral over boundary of
T^{n+1/2} of sigma_h.n`; `sum_i DualArea_i` constant with each nodal area
evolving consistently with `Q_i = DualArea_i * U_i`; round-off conservation of
mass, momentum and energy; invariance between 1 and 4 ranks by particle ID.

Two gates added from §3.4:

- rank invariance on a case containing exactly-Lagrangian elements, with the
  ALE path built on `RD_ALWAYS_PSEUDOINVERSE` per §3.5, plus the cost
  comparison against the LU/pivot-trigger path on the same case;
- `Phi in range(S^-)` verified on the Sod, not only on smooth flow.

### M2 — real AREPO mesh motion and topology, 1-2 weeks

Revised down from 2-4 weeks. Justification: the smooth deliverables need no
topology machinery at all (§3.3, zero inversions up to CFL 0.8), so the
accuracy programme is not gated on the hard part. Order the work so that the
publishable result lands first:

1. `sigma` = fluid velocity, no regularisation, translating uniform flow;
2. moving-mesh Yee and Gresho against the static N controls, joint `(dx, dt)`
   convergence — **this is the minimum defensible thesis deliverable, and it is
   reachable without any flip treatment**;
3. enable regularisation; re-verify free stream and DGCL;
4. Sod and a shear case, where the `|T^n| <= 0` counter becomes non-zero. The
   minimum acceptable fallback is to demote inverted elements to N/lumped for
   that step and account for them; the Isola-Guardone continuous-deformation
   interpretation is the principled alternative and is only worth implementing
   if the demotion measurably damages the solution;
5. 1-vs-4 rank invariance through repeated rebuilds.

**M2 gate:** free-stream, DGCL and conservation hold across at least one real
connectivity change, and the inverted-element count is reported for every run.

### M3 — LDA and GL/F1 on the accepted N geometry, 1 week

The temporal term must use the geometry-dependent mass matrices,
`sum_j [ m_ij^{T^{n+1}} U_j^* - m_ij^{T^n} U_j^n ] / dt`, not the static
`m_ij (U_j^* - U_j^n) / dt` shortcut. Gates: zero-motion collapse to static
LDA+GL/F1; the same free-stream, DGCL and MPI tests as N; positive predictors
and `f1_lumped = 0` on the smooth production glass; joint `(dx, dt)`
convergence on the moving Yee with N as the first-order control; Sod robustness
against moving N and static LDA.

Reduced from Codex's 1-2 weeks because §3.4 has already established that the
F1 SVD policy does not need redesign — `beta` is bounded at every `w` — only
revalidation under the new threshold.

**Total: about 5 to 7 weeks**, with a thesis-usable result available part way
through M2 rather than only at its end.

---

## 5. Open questions for this phase

1. Does `Phi in range(S^-)` survive a shock? If not, the exactly-Lagrangian
   element loses conservation on the LDA path and needs an explicit remedy.
2. Is demoting inverted elements to N/lumped acceptable, or does it degrade the
   shear cases enough to force the Isola-Guardone construction?
3. Do AREPO's regularisation drift and the RD solution feedback change the
   measured flip and inversion rates materially?
4. Should the median-dual control volume be revisited against the Voronoi cell
   under mesh motion? `context.md` has flagged this since the start, and the
   ALE literature is uniformly median-dual, but the question is sharper on a
   moving mesh than on a static one.
5. Volume 1's open question on `Theta` versus order remains open and is
   independent of this phase.
