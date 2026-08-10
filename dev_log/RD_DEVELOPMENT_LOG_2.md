# AREPO Residual Distribution Development Log, volume 2: moving mesh

This is the **active** development log. It succeeds
`dev_log/RD_DEVELOPMENT_LOG.md`, which is closed at its final entry of
2026-08-04 and kept as the record of the static-mesh phase.

> **Latest mathematical correction, 2026-08-06:** section 6 and
> `dev_log/RD_moving_mesh_DGCL_mathematical_audit.md` supersede section 3.3's
> conclusion that the new-connectivity-at-both-times construction needs no
> topology transfer, and the corresponding no-topology parts of the M0/M2 plan
> in section 4. The earlier text is retained as development history, not as the
> current implementation prescription.
>
> **Section 7, added later the same day, partially reverses section 6 again.**
> Claude's review concludes that the median-dual topology defect is second
> order rather than `O(1)`, that section 6's `O(1)` figure is an artifact of
> treating the stored `Q` as the carried variable, and that no topology
> operator is needed. Section 6's code audit stands unchanged. Section 7 is
> Claude's review deliverable and is itself **not yet accepted**; Codex and
> Kimi are asked to audit it against section 6.
>
> **Section 8, 2026-08-07, is the more consequential correction.** Checked
> against the primary source, the endpoint-mass two-stage form in the Chapter 4
> draft — and in `RK2_timestep_movingmesh_analysis.md` §7.2, and in the
> reference table of section 2.1 below — is **not** the scheme of
> Arpaia, Ricchiuto & Abgrall (2015). The published scheme is their
> Proposition 4.1, which uses one modified midpoint median-dual area, one
> midpoint mass matrix, and no geometric source term in the distributed
> residual. **Section 8.7 then corrects this**: the endpoint-mass form is
> published, in Campoli et al. (2017), and the two forms differ by a single
> `O(dt^2)`-small term added to both the mass coefficient and the nodal divisor.
> They are the same scheme, and the choice between them is a compile-time switch
> rather than a gating decision.
>
> **Section 8 records the resulting sequencing decision:** stop choosing code
> structures until the ALE-RD equations are explicit in thesis Chapter 4. A
> first mathematical draft and a hierarchical flip timeline now exist. This
> accepts `U` as the RD degree of freedom and `Q=mU` as storage, but deliberately
> leaves the exact endpoint-mass/modified-midpoint equivalence and an
> interrupted hierarchical flip interval open for review.

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
| **Arpaia, Ricchiuto & Abgrall (2015)**, *An ALE formulation for explicit Runge-Kutta residual distribution*, J. Sci. Comput. **63**(2), 502-547, `10.1007/s10915-014-9910-5` | **the reference formulation.** Explicit two-step RK, second order in space and time, fully conservative, DGCL-compliant. The static RK2-RD already implemented is its `sigma = 0` special case. Local copies: `MyThesis/useful_resources/2015_Arpaia_An_ALE_Formulation_for_Explicit_Runge–Kutta_Residual_Distribution.pdf`, preprint at `https://inria.hal.science/hal-00863154`. **Its own scheme is Proposition 4.1, equations (82)-(84), with the modified midpoint median dual (77); the equations in `RK2_timestep_movingmesh_analysis.md` §7.2 are Campoli et al.'s rendering, not this paper's. See section 8** |
| **Arpaia & Ricchiuto (2018)**, *r-adaptation for shallow water flows: conservation, well balancedness, efficiency*, Comput. Fluids **160**, 175-203 | r-adaptation application of the same ALE-RD machinery |
| **Arpaia & Ricchiuto (2020)**, *Well balanced residual distribution for the ALE spherical shallow water equations on moving adaptive meshes*, JCP **405**, 109173 | as above, on the sphere |
| **Campoli, Quemar, Bonfiglioli & Ricchiuto (2017)**, *Shock-Fitting and Predictor-Corrector Explicit ALE Residual Distribution*, in *Shock Fitting: Classical Techniques, Recent Developments, and Memoirs of Gino Moretti*, Shock Wave and High Pressure Phenomena, Springer, 95-116, `10.1007/978-3-319-68427-7_5`; author draft `math.u-bordeaux.fr/~mricchiu/sf-draft.pdf`, HAL `hal-01625413` | **the actual source of the endpoint-mass equations** transcribed in `RK2_timestep_movingmesh_analysis.md` §7.2, whose numbering (1)-(8) is this chapter's, not Arpaia's. Section 8.7 shows it is Arpaia's scheme plus one `O(dt^2)` term |
| **Colombo & Re (2022)**, *An ALE residual distribution scheme for the unsteady Euler equations over triangular grids with local mesh adaptation*, Comput. Fluids **239**, 105414, `10.1016/j.compfluid.2022.105414`, `arXiv:2204.11668`, building on earlier interpolation-free ALE adaptation work including **Guardone, Isola & Quaranta (2011)**, JCP **230**, `10.1016/j.jcp.2011.06.026` | **the only identified RD treatment of topology change.** Edge swap, node insertion and node deletion are interpreted as a series of fictitious continuous deformations of the dual mesh, which enforces the GCL by construction and needs no explicit interpolation between connectivities |

**Kimi's key observation, which this project must not lose:** every one of the
Arpaia-Ricchiuto works is a *continuous-deformation, fixed-connectivity*
framework — the whole point of r-adaptation is to move nodes without
reconnecting. AREPO's Delaunay triangulation reconnects whenever the generators
move. So the reference formulation covers our geometry but not our
connectivity; only Colombo--Re covers the latter, and it does so for
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

> **Superseded on 2026-08-06 and corrected on 2026-08-10.** The topology-change
> rates below remain valid, but the non-zero KH inversion rates do not. They
> came from applying new periodic image offsets to separately wrapped old
> coordinates. Continuous backward trajectories give zero inversions in all
> listed Yee and KH cases; see section 9.3. Independently, the inference that a
> positive pulled-back new triangulation removes the median-dual topology
> quadrature defect remains false for the reason established in section 7.

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

**Historical measurement, with the KH inversion rows withdrawn** (glass IC,
Lagrangian vertex motion, periodic Delaunay, 30 steps):

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
3. **The earlier claim that 0.14 to 0.70 per cent of shear elements need a
   fallback is withdrawn.** With continuous periodic unwrapping the corrected
   30-step survey found zero inverted elements for KH at CFL 0.3 and 0.8 at
   both `n=48` and `n=96`. The signed-area counter remains a required defensive
   diagnostic for larger displacement or pathological meshes, but these data
   no longer provide evidence that a routine shear fallback is needed.

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
4. Sod and a shear case, while monitoring the `|T^n| <= 0` counter. The
   corrected offline survey does not make it non-zero, so no fallback is on the
   critical path. If a genuine inversion is later observed, demotion to
   N/lumped and the Colombo--Re continuous-deformation interpretation remain
   candidate responses which must be assessed from that actual case;
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
   shear cases enough to force the Colombo--Re construction?
3. Do AREPO's regularisation drift and the RD solution feedback change the
   measured flip and inversion rates materially?
4. Should the median-dual control volume be revisited against the Voronoi cell
   under mesh motion? `context.md` has flagged this since the start, and the
   ALE literature is uniformly median-dual, but the question is sharper on a
   moving mesh than on a static one.
5. Volume 1's open question on `Theta` versus order remains open and is
   independent of this phase.

---

## 6. 2026-08-06: DGCL re-derivation exposes a median-dual topology defect

### 6.1 Status and full derivation

The full thesis-notation derivation, code audit, forced-run failure analysis,
revised gates, and questions for reviewers are in:

`dev_log/RD_moving_mesh_DGCL_mathematical_audit.md`.

This entry records only the decision-level correction. It has not yet been
accepted by Claude or Kimi.

### 6.2 Corrected conclusion

For Chapter 3's median dual,

```
|S_i^n| = sum_{T in D_i^n} |T^n|/3,
Q_i^n   = |S_i^n| U_i^n.
```

A uniform state is preserved if and only if the stored ledger satisfies

```
Q_i^{n+1} - Q_i^n = U_0 (|S_i^{n+1}| - |S_i^n|)
```

by particle ID. Fixed-connectivity linear vertex motion can satisfy this
exactly: midpoint geometry gives the per-element area identity, and summing one
third of that identity over the vertex star gives the median-dual identity.

Across a connectivity change, let `|S_hat_i^n|` be the median area obtained by
evaluating the **new** connectivity at the old coordinates. Then

```
|S_i^{n+1}| - |S_i^n|
  = (|S_i^{n+1}| - |S_hat_i^n|)   continuous deformation
  + (|S_hat_i^n| - |S_i^n|)       topology jump.
```

Section 3.3's midpoint construction captures only the first line. The second
line is generally finite even when every pulled-back triangle has positive
area. A stationary co-circular square whose diagonal is swapped is the exact
counterexample: the incident median areas change between `A/6` and `A/3` while
the mesh velocity is zero.

The topology jumps sum to zero, so global area and global conservation audits
can pass while nodal free-stream preservation fails. For a nonuniform state,
locally multiplying the topology area jump by `U_i` is not generally globally
conservative; a conservative topology flux/remap or fictitious deformation is
needed.

### 6.3 Code consequence

The current equal-timestep `RD_RK2_TOTAL_RESIDUAL` path is not DGCL-compliant:

- the first, old-mesh call in `run.c` is a no-op;
- `rd_accumulate_dual_area()` replaces `DualArea` with the new median area;
- both internal RK stages run on that new geometry;
- the shifted eigenvalues include an element-averaged moving-frame velocity,
  but not the conservative `-U div(sigma_h)` geometry contribution;
- the path never has both `|S_i^n|` and `|S_i^{n+1}|` available to verify or
  enforce the ledger identity.

If forced to run, unchanged `Q_i` followed by recovery with the new area gives

```
U_i^{n+1} = U_0 |S_i^n| / |S_i^{n+1}|.
```

Smooth deformation therefore injects mesh-scale density/pressure noise, and a
single median-dual flip can inject an order-unity nodal disturbance while
global mass, momentum, and energy remain exactly conservative.

### 6.4 Effect on the phase plan

The M1 fixed-connectivity N/DGCL prototype remains the correct next
implementation target. The following earlier claims are suspended pending
review:

- M0's adoption of new connectivity at both times as a no-remap baseline;
- M2's claim that smooth flips need no topology machinery when pulled-back
  elements remain positive;
- demotion of only inverted elements as a sufficient topology fallback.

The revised sequence is:

1. prove and implement continuous fixed-connectivity DGCL;
2. test a prescribed zero-motion diagonal swap and measure the nodal topology
   defect separately;
3. design a conservative topology operator;
4. only then enable repeated real AREPO rebuilds;
5. postpone LDA/F1 and hierarchical timesteps until the N geometry is closed.

### 6.5 Bibliographic correction

The topology-change RD paper with DOI
`10.1016/j.compfluid.2022.105414` is by **Stefano Colombo and Barbara Re**,
not Isola and Guardone. The table in section 2.1 has been corrected. The paper
is still relevant as the published fictitious-deformation treatment of edge
swaps, but its BDF/local-adaptation workflow is not a drop-in AREPO RK2 method.

### 6.6 Review request

Claude and Kimi are asked to audit especially:

1. the necessary-and-sufficient ledger DGCL;
2. the continuous/topological decomposition above;
3. whether any conservative nonuniform-state transfer is already hidden in
   the new-connectivity construction;
4. the interpretation of Arpaia--Ricchiuto's modified median area and mass
   terms in an implementation that stores integrated `Q`;
5. the claim that AREPO's Voronoi volume is continuous at a generic Delaunay
   flip whereas the median-dual area is not;
6. the current-code audit and whether any old geometry has been overlooked.

---

## 7. 2026-08-06 (later): Claude's review — the topology defect is second order, and the control volume must not change

- Author: `Claude Code Opus 5`, answering the review request of section 6.6 and
  section 10 of `dev_log/RD_moving_mesh_DGCL_mathematical_audit.md`.
- **No solver source was changed in this entry.** It is a review plus a code
  audit.
- Status: **not accepted.** Zhenyu has explicitly recorded that he is not
  confident in the conclusion, and has asked Codex and Kimi to audit it. The
  entry is written as a chronology — first position, objections, revised
  position — so that reviewers can see which step they disagree with rather
  than only the endpoint. Section 7.9 lists what is genuinely uncertain.

### 7.1 First position: agreement with section 6, plus two additions

Claude's first pass verified section 6's code audit line by line and found it
accurate in every particular (details in 7.5). It then **agreed with the `O(1)`
severity assessment** and went further in two directions, both of which are now
withdrawn:

1. **A conservative topology operator was designed.** Since
   `sum_i Delta S_i^topo = 0` with support confined to the flip patch, an
   antisymmetric flow `a_ij = -a_ji` on the patch with
   `sum_j a_ij = Delta S_i^topo` and
   `Delta Q_i^topo = sum_j a_ij (U_i + U_j)/2` is conservative by construction
   and exact for a uniform state, answering audit question 5 in the
   affirmative. Closed form on an isolated 4-node patch; a local graph-Laplacian
   flow on cascades, with an MPI rank-invariance caveat because an iterative
   solve would depend on the decomposition.
2. **A move to the Voronoi control volume was proposed**, on the strength of
   section 6's own observation that `|V_i|` is continuous through a flip, with
   the added argument that AREPO's regularisation drives the mesh toward a CVT
   and would therefore reduce the `|g|/h` asymmetry identified in
   `mass_matrix_order_analysis.md` as the source of the `B/n` term.

Claude also produced a quantitative severity estimate that appeared to confirm
section 6: carrying `Q` unchanged gives an `O(1)` nodal error at each flipped
node; carrying the intensive state instead gives a conservation leak estimated
at `O(h^3)` per flip patch, accumulating to roughly `f T / CFL ~ 2%` at the
measured flip fraction. Both were presented as unacceptable, which made a
topology operator look mandatory.

### 7.2 Zhenyu's three objections

1. **`Q` is an accumulator.** In AREPO the conserved fields only receive flux;
   the primitive state is recovered at the end of the step, and under a time-bin
   hierarchy `Q` deliberately accumulates fine-bin contributions before any
   primitive update. Analysing the instantaneous "exactness" of `Q` does not
   match what the variable is for.
2. **The Voronoi volume also changes as the generators move**, exactly as the
   median-dual area does. So the question is not *whether* the control measure
   changes but specifically *what the co-circular jump does*, and that had been
   asserted rather than analysed.
3. **The median dual is derived from the `P^1` basis** (thesis Chapter 3,
   `|S_i| = sum_{T in D_i} |T|/(d+1)`, described there as the row-sum lumped
   mass of a piecewise-linear approximation). Replacing it with the Voronoi
   volume may therefore not be admissible at all. Zhenyu also pointed at
   Gaburro, Ricchiuto & Dumbser (2025) as looking complicated.

Objection 3 is decisive and objection 2 is the right question. Objection 1 is
the reason the first position went wrong.

### 7.3 The corrected analysis

**The carried degree of freedom is `U_i`, not `Q_i`.** RD is a Petrov--Galerkin
finite element method. The unknowns are the coefficients of the `P^1` expansion
`U_h = sum_j U_j psi_j`, and

```
m_i = integral psi_i = |S_i| = sum_{T in D_i} |T|/3
```

is a **lumped mass-matrix coefficient, not a container of material**.
`Q_i = m_i U_i` is a storage convention that reuses AREPO's `Mass`,
`Momentum` and `Energy` fields. Section 6 and Claude's first position both read
`Q_i` as a finite-volume cell integral and then asked where its contents go at a
flip. That question does not arise for a mass-matrix coefficient.

**What a flip actually changes is the basis.** At the co-circular event the
functions `psi_i` change because the triangulation changes. The nodal values
`U_i` need not change at all. Hence:

**(a) The discrete solution.** `U_h` changes from the `P^1` interpolant of the
same nodal data on `T_h^n` to its interpolant on `T_hat_h^n`. The two agree at
all four nodes of the quadrilateral and differ only inside it, by
`O(h^2 |grad^2 U|)`. **For a linear field the two interpolants are identical.**

**(b) The lumped mass jumps, but with structure.** Both triangulations tile the
same quadrilateral, so `sum_i Delta m_i = 0`. Less obviously, the first moment
is also preserved. Because `P^1` reproduces linear functions exactly,
`sum_i x_i psi_i(x) = x` on any triangulation, and integrating gives

```
sum_i m_i x_i = sum_T |T| g_T = integral x dx,
```

with `g_T` the element centroid. Both triangulations of the patch give the same
`integral x dx` over it, and triangles outside the patch are untouched, so

```
  sum_i Delta m_i^topo     = 0        (both partitions tile the patch)
  sum_i Delta m_i^topo x_i = 0        (P^1 linearity, exact on any triangulation)
```

**(c) The leak is therefore fourth order per patch.** Expanding `U` about any
point `x_0` in the patch, the constant term is annihilated by the first
identity and the linear term by the second:

```
leak = sum_i Delta m_i^topo U_i
     = (1/2) sum_i Delta m_i^topo (x_i-x_0)^T H (x_i-x_0) + O(h^5)
     = O(h^4 |grad^2 U|),
```

since `|Delta m_i| = O(h^2)` and `|x_i - x_0| = O(h)`. Claude's first estimate
lost the second identity and therefore gave `O(h^3)`, one order too pessimistic.

**Consequences.**

- **A flip is exactly invisible to a linear field.** Linearity preservation, the
  property RD's second order rests on, survives connectivity change untouched.
- With the flip fraction `f` and `Delta t ~ CFL * h`, the cumulative relative
  conservation error to time `T` is `~ f h T |grad^2 U| / CFL`, i.e.
  `O(h)` — about `2e-4` at `n=96` with `f = 0.6%` and `CFL = 0.3`, and
  converging. If the per-flip signs are uncorrelated the random walk makes it
  smaller still.
- **The `O(1)` figure of section 6.3 and 7.3 of the audit is real, but it is a
  property of the current implementation, not of the method.** It is what you
  get by carrying `Q` across the rebuild and dividing by the new area. It
  disappears once the accumulator is rebased.

**Therefore no topology operator is required**, and the antisymmetric flux of
7.1 item 1 is withdrawn from the critical path. It remains available, and it
would restore round-off conservation across flips, if 7.9 item 4 turns out to
matter.

### 7.4 What this means for the DGCL bar

Reading the AREPO flow chart (`MyThesis/useful_resources/Arepo_flowchart.pdf`),
the FV path applies `Q^n - (Delta t/2) sum F^n(W^n)` on the old mesh, drifts and
rebuilds, then applies the second half on the new mesh. For a uniform state
`sum A F(W_0).n = 0` exactly on a closed polygon, so free-stream preservation
requires

```
|V_i^{n+1}| - |V_i^n| = (Delta t/2) [ (sum A w.n)^n + (sum A w.n)^{n+1} ],
```

a **trapezoidal rule for the volume change**. A Voronoi volume under linear
generator motion is a piecewise-rational function of time, not a polynomial, so
this identity is second-order accurate and **not exact**. AREPO therefore runs
with a DGCL error at its own scheme order and no special treatment anywhere.

This matters because both section 6 (4.1: "an algebraic identity, not an
asymptotic approximation") and Claude's first position treated exact-to-round-off
DGCL as the acceptance bar. It is a nice-to-have. Guillard & Farhat (2000),
already cited in section 2.2, says exactly this: GCL violation is not always
fatal, and free-stream preservation is the safe design criterion. **The M1 gate
should be free-stream error at scheme order, with the error reported, not
round-off.**

### 7.5 What the current code actually lacks

Section 6.3 and audit section 7 were verified and are accurate:
`run.c:233-239` first call is a no-op; `run.c:294` drift, `run.c:316`
`create_mesh()`, `run.c:337` the unconditional two-stage call;
`residual_distribution_solver.c:943` zeroes and rebuilds `DualArea` from the new
triangulation; `:1029` and `:1157` both divide by that new area;
`:1758-1766` shifts the eigenvalues by an element-averaged `sigma` only, and
since `sum_j |n_j| n_hat_j = 0` the element residual of a constant state is
identically zero — the conservative geometry contribution is genuinely absent.
No alternative interpretation was found (audit question 8).

Two corrections to the audit's supporting detail:

- `drift_particle` is called for every particle inside `create_mesh()`
  (`voronoi.c:152`), so the linear-drift recovery `x^n = x^{n+1} - VelVertex dt`
  of section 3.2(b) does not depend on the domain-decomposition branch at
  `run.c:294`. It holds unconditionally.
- `|S_i^n|` costs one `SphP` field. At entry to `compute_residuals` the
  `DualArea` field still holds the previous step's value; saving it before
  `rd_accumulate_dual_area()` is two lines, and `SphP` migrates through domain
  decomposition, which the hierarchical path already relies on.

The complete list of missing pieces is then:

1. **Rebase the accumulator after the rebuild:**
   `Q_i <- Q_i * |S_i^{n+1}| / |S_i^n|`. This is what puts `|C_i^{n+1}|` on both
   sides of Arpaia--Ricchiuto (2) and (5). AREPO's FV needs no equivalent
   because its `|V_i|` is continuous and the ratio is `1 + O(Delta t)`, supplied
   by the ALE flux itself; the median dual has a jump, so the ratio must be
   applied explicitly. **This single line is the entire "topology treatment".**
2. **Add the geometric residual** `-integral_{boundary K^{n+1/2}} sigma_h.n` to
   `Phi`. This is missing outright and is independent of the control-volume
   question. It must be distributed with the row-sum weights of the mass matrix,
   i.e. `sum_j m_ij^K / |K|` — `1/3` for N/lumped, which is the audit's (4.6),
   and `beta_i` for LDA and B, which generalises it.
3. **The F1 temporal target becomes ALE.** The code's F1 action is
   `T_i = beta_i [(|T|/3) sum_j dU_j/dt]` (`:1926` builds the target, `:2296`
   applies `-K_i^+ z`), so it already satisfies `sum_j m_ij^K = beta_i |K|`,
   which is precisely Arpaia--Ricchiuto's "mass matrix entries consistent with
   the definition of the spatial distribution". With that property the
   constant-state cancellation between the mass term and the geometric flux is
   exact **for any `beta`**:

   ```
   mass:  beta_i U_0 (|K^{n+1}| - |K^n|)/Delta t
   geom:  beta_i Phi^K(U_0) = -beta_i U_0 (|K^{n+1}| - |K^n|)/Delta t
   sum :  0                                        for N, LDA and B alike
   ```

   So `rhs[k][2]` changes from `(|T|/3) sum_j dU_j` to
   `[(|T^{n+1}|/3) sum_j U_j^* - (|T^n|/3) sum_j U_j^n]/Delta t`, one line, with
   the `beta` application untouched. **Audit section 9.3's deferral of LDA/F1 to
   a later phase is therefore withdrawn:** the F1 mass matrix needs no redesign
   and LDA/B should be done alongside N in M1. Only hierarchical timesteps stay
   deferred.
4. **The predictor must use the geometrically non-conservative `Phi_tilde`** of
   (6), not the corrector's `Phi`. Already flagged in
   `RK2_timestep_movingmesh_analysis.md` 7.4; still true.

Note also that the old geometry the residual needs is the **pulled-back** new
connectivity `|K_hat^n|`, never the actual old `|S_i^n|` star. `|S_i^n|` is
needed only for the rebase in item 1.

### 7.6 The control volume must stay median-dual

Zhenyu's objection 3 is decisive, and it can be made quantitative by the same
identity used in 7.3. What makes `m_i = integral psi_i` a second-order mass
lumping is

```
sum_i m_i x_i = integral x dx     exactly, on any triangulation.
```

The Voronoi volume satisfies `sum_i |V_i| x_i = integral x dx` **only if
`x_i = centroid(V_i)`**, that is only on a centroidal tessellation. On a general
mesh it is a first-order quadrature.

So the property that would be destroyed by moving to `|V_i|` is exactly the
property that makes a flip harmless in 7.3. Swapping the control volume to
remove the topology jump would convert a fourth-order-per-patch leak into a
second-order one. **The Voronoi proposal of 7.1 item 2 is withdrawn.**

This also explains why the hybrid noted in thesis Chapter 3 near the Chapter 4
red note — Paardekooper (2017) uses the Voronoi volume `V_i` in the nodal update
while keeping `|T|/(d+1)` in the temporal residual and mass matrices — is not
self-consistent: the two are then different lumpings of the same `P^1` space.

Open question 4 of section 5, and item 1 of `context.md`'s current status, can
accordingly be closed in favour of the median dual, on the `P^1` first-moment
argument rather than on the appeal to literature convention — **subject to
review, since this is the conclusion Zhenyu is least sure of.**

### 7.7 Gaburro, Ricchiuto & Dumbser (2025): what it is and is not

Checked directly. `arXiv:2506.00207`, `inria.hal.science/hal-05124553`:

> Elena Gaburro, Mario Ricchiuto, Michael Dumbser, *On general and complete
> multidimensional Riemann solvers for nonlinear systems of hyperbolic
> conservation laws*.

It builds a multidimensional Osher--Solomon solver and a genuinely
multidimensional upwind flux on unstructured **Voronoi-like polygonal**
tessellations, and establishes an equivalence between a fluctuation form of
finite volume with corner fluxes and residual distribution, extended to fourth
order with CWENO reconstruction and ADER time stepping.

**It is a static-mesh paper. It does not treat moving meshes, ALE, or topology
changes.** It is therefore the right long-term framework for the question the
Chapter 4 red note raises — what the AREPO-RD hybrid *is* mathematically, if the
evolved variables are ever to be read as Voronoi cell averages — but it is not a
route to the moving mesh and not a shortcut. Zhenyu's reading is confirmed.

### 7.8 Revised phase plan

M1, with connectivity free to change from the start:

- implement 7.5 items 1--4;
- **keep the median dual; add no topology operator; change no control volume.**

Gates, replacing the audit's 9.1:

1. `v_mesh = 0` collapses to the static N, LDA and B results;
2. per-element `(4.2)` to round-off on fixed connectivity;
3. free-stream preserved **at scheme order**, with the defect reported per
   particle ID, not required to be round-off;
4. global conservation drift reported per step together with the flip count and
   the measured `sum_i Delta m_i^topo U_i`, so that 7.3's `O(h^4)` estimate
   becomes evidence rather than an argument;
5. joint `(dx, dt)` convergence on the moving Yee and Gresho — the minimum
   defensible thesis deliverable;
6. 1-vs-4 rank invariance by particle ID through repeated rebuilds.

The `|T_hat^n| <= 0` counter is retained: it is the condition for `|K_hat^n|` to
be *definable*, and remains a stability/upwinding gate. It is not a topology
acceptance criterion, which section 6 got right.

The audit's staged sequence — fixed connectivity, then a prescribed zero-motion
flip test, then a topology operator, then real rebuilds — collapses to a single
stage if 7.3 holds. The prescribed zero-motion flip test is still worth keeping
as a cheap direct check of 7.3(a) and (b).

### 7.9 What is not certain, and what Codex and Kimi are asked to audit

Zhenyu has recorded that he is not fully convinced. The specific soft points:

1. **Is `sum_i Delta m_i^topo x_i = 0` correct?** The argument is that
   `sum_i m_i x_i = sum_T |T| g_T = integral x dx` over the patch, identical for
   both triangulations because both tile it. This is the load-bearing step; if it
   fails the leak returns to `O(h^3)` and the case for a topology operator is
   reopened.
2. **Is it legitimate to treat `U_i` as a point value carried through the
   flip?** In `P^1` Lagrange terms it is by definition. A reviewer could argue
   that the converged RD solution's `U_i` is only a point value to `O(h^2)`, and
   that this weakens 7.3(a).
3. **Does the leak accumulate coherently?** The `O(h)` cumulative estimate
   assumes `Delta m_i^topo` has no systematic correlation with the local
   Hessian. Under shear, flips may have a preferred orientation relative to the
   flow, in which case the errors could add rather than random-walk. Not
   measured.
4. **Smoothness is assumed.** At a shock the two interpolants differ by
   `O(jump)` and the leak is `O(h^2 * jump)`, not `O(h^4)`. Whether that is
   tolerable on the Sod and shear cases is untested, and is the situation in
   which the withdrawn antisymmetric flux would be brought back.
5. **Is the accumulator rebase `Q <- Q |S^{n+1}|/|S^n|` genuinely complete?**
   The claim is that the actual old star `|S_i^n|` then appears nowhere else,
   because the residual uses the pulled-back `|K_hat^n|`. Worth checking against
   the two-step algebra, which gives
   `sum_i m_i^{n+1} U_i^{n+1} = sum_i m_hat_i^n U_i^n` for the whole step.
6. **Is the trapezoidal reading of AREPO's own GCL right?** It is derived here
   from the flow chart structure rather than from the FV source. If AREPO turns
   out to enforce something stronger, the argument in 7.4 for relaxing the M1
   gate weakens.
7. **Section 6's `O(1)` claim is not withdrawn as a statement about the current
   code** — only as a statement about the method. Reviewers should say
   explicitly which of the two they are disputing, if either.

---

## 8. 2026-08-07: review of the Chapter 4 draft against the primary source

- Author: `Claude Code Opus 5`, at Zhenyu's request to audit Codex's
  moving-mesh mathematics in
  `MyThesis/Zhenyu-PhDThesis/zhenyu_thesis/chapter4/chapter4.tex`.
- **No solver source was changed.** The deliverable is a set of `\red{}`
  additions to Chapter 4, made under the thesis editing boundary Codex added to
  `context.md` on 2026-08-06, which permits an explicitly requested Chapter 4
  mathematics update.
- Primary source consulted directly:
  `MyThesis/useful_resources/2015_Arpaia_An_ALE_Formulation_for_Explicit_Runge–Kutta_Residual_Distribution.pdf`,
  pages 507--523 (sections 3, 4, 5.1). Section 6, on the Euler system, and the
  Appendix proof were not read.

> **8.1 and 8.4 were corrected later the same day; see 8.7.** The endpoint-mass
> form *is* published — in Campoli, Quemar, Bonfiglioli & Ricchiuto (2017) —
> and it differs from Arpaia's Proposition 4.1 by a single, exhibitable,
> `O(dt^2)`-small term. The description of it below as an unpublished variant is
> wrong, and two of the four reasons given in 8.4 for preferring the Arpaia form
> do not survive. The rest of section 8 stands.

### 8.1 Headline finding: the working formulation is not the published one

Chapter 4's equations `ALE_RD_predictor_working`,
`ALE_RD_total_nodal_working` and `ALE_RD_corrector_working` — the endpoint-mass
two-stage form — are **not** the scheme of Arpaia, Ricchiuto & Abgrall (2015).
Codex flagged this as needing an algebraic check; the check has now been done
against the paper and the answer is that it is a different, and as far as can be
established unpublished, variant.

The published scheme is their **Proposition 4.1**, equations (82)--(84), in the
Global Lumping form that corresponds to the project's production GL+F1:

```
|Sbar_i^{n+1/2}| (U_i^*   - U_i^n)/dt = - sum_{T in i} Phi_i^{RK(1)}
|Sbar_i^{n+1/2}| (U_i^{n+1} - U_i^*)/dt = - sum_{T in i} Phi_i^{RK(2)}

Phi_i^{RK(1)} = phi_i^T(U^n)
Phi_i^{RK(2)} = sum_j m_ij^T (U_j^* - U_j^n)/dt
                + 1/2 [ phi_i^T(U^*) + phi_i^T(U^n) ]
```

with every integral, including the single mass matrix, on the **midpoint**
configuration `T^{n+1/2}`, with `phi^T` the geometrically **non-conservative**
residual, and with the nodal coefficient the **modified** median dual, their
equation (77):

```
|Sbar_i^{n+1/2}| = sum_{T in D_i} (1 + (dt/2) div sigma_h) |T^{n+1/2}|/3
                 = sum_{T in D_i} [ |T^{n+1/2}| + (|T^{n+1}|-|T^n|)/2 ] / 3
```

the second form following from the element DGCL identity and the constancy of
`div sigma_h` on a `P^1` element.

Three linked differences from Chapter 4's working form:

| | published (82)--(84) | Chapter 4 endpoint-mass form |
| --- | --- | --- |
| nodal coefficient | one modified midpoint area, shared by both stages | the new median dual `m_i^{n+1}` |
| mass matrix | one, on `T^{n+1/2}`, acting on the stage increment | two endpoint matrices `m_ij^{T,n}`, `m_ij^{T,n+1}` |
| geometric source term | absorbed into the modified area; the distributed residual is `phi_tilde` | carried inside the distributed residual `phi_ALE` |

**Both satisfy the acceptance condition** — the endpoint cancellation is exact,
as verified in 8.2 — and the nodal coefficients differ at `O(dt)`, so the
updates differ at `O(dt^2)` locally, within the scheme's order. They are
nevertheless different schemes.

Directly related: Arpaia--Ricchiuto never distribute the conservative residual
`phi_ALE`. Their equation (69) is the non-conservative form, their (59) is the
ALE upwind parameter `k_i = (1/2)(abar - sigmabar).n_i` that realises it, and
the difference between the two residuals — which they name the **geometric
source term** in their section 4.2 — is absorbed into (77). Both residual forms
appear in the paper, but not on an equal footing, which answers Zhenyu's first
question.

**Bibliographic consequence.** `RK2_timestep_movingmesh_analysis.md` §7.2
presents the endpoint-mass equations numbered (1)--(8); the paper's RK2 section
is numbered (78)--(84) and has a different structure. §7.1 of that document
records that the confirmation came from Campoli, Quemar, Bonfiglioli &
Ricchiuto §2.2. The endpoint-mass form therefore appears to descend from
**Campoli et al., not from Arpaia--Ricchiuto--Abgrall 2015**. The reference
table in section 2.1 above attributes it to the latter and should be corrected
once someone has checked the Campoli paper directly. Nobody has.

### 8.2 What was verified as correct

Every one of the following was checked by hand against the draft:

- the ALE conservative form and its reduction to the intensive form via the
  Euler expansion `dJ/dt = J div sigma`, using
  `U div sigma - div(U tensor sigma) = -(sigma.grad)U`;
- `phi_ALE = phi_tilde - integral_T U_h div sigma_h`, by the divergence theorem;
- the element DGCL as an exact algebraic identity in 2-D for linear vertex
  trajectories, since the signed area is quadratic in time;
- `phi_tilde(U_0) = 0` and `phi_ALE(U_0) = -U_0 integral sigma_h.n`;
- the column-sum condition `sum_i m_ij^{T,s} = (|T^s|/3) I` giving local
  conservation, and the static N and LDA mass choices satisfying it;
- that `m_ij^{LDA,T} = (|T|/3) beta_i` is independent of `j` and therefore
  matches the code's F1 action at `residual_distribution_solver.c:1926` and
  `:2296`. This is confirmed by the paper's own equation (28),
  `m_ij^{F1} = (|K|/3) beta_i`;
- the endpoint-form nodal DGCL cancellation, exactly, for arbitrary bounded
  `beta_i`;
- the two moment identities and the resulting `O(h^4)` flip defect.

The code audit of section 6 also remains verified; nothing in 8.1 disturbs it.

### 8.3 Findings recorded in Chapter 4 as `\red{}` additions

All additions are marked in red and none change an existing equation number;
new display mathematics is unnumbered, and the new subsection
`section:ALE_RD_two_forms` uses unnumbered equations for the same reason.
References below are by `\label`, not by number.

1. After `eq:ALE_RD_residual_difference` — that Arpaia--Ricchiuto never
   distribute `phi_ALE`, and where the geometric source term goes instead.
2. After `eq:ALE_RD_linear_trajectory` — **the midpoint configuration is now
   defined explicitly**, which the draft never did although the whole DGCL rests
   on it. With two riders: the 2-D degeneracy that makes midpoint and
   trapezoidal evaluation equivalent does not survive to 3-D; and in AREPO the
   midpoint configuration is not any tessellation the code builds, only one
   tessellation exists at a time, the old **connectivity** is genuinely
   unavailable, and any formulation requiring `T_h^n` itself is not
   implementable. This answers Zhenyu's second question.
3. After `eq:ALE_RD_median_DGCL` — that it is a corollary for the `Q`-storage
   reading, not a step in the free-stream chain, since the corrector divides by
   `m_i^{n+1}` on both sides and `m_i^n` never enters.
4. After `eq:ALE_RD_nodal_DGCL_condition` — the derivation chain
   `element_DGCL -> uniform_residuals -> nodal_DGCL_condition ->
   freestream_definition`, including the step, previously unstated, that
   `phi_tilde^T = 0` implies the nodal shares vanish individually for both N and
   LDA. Plus two properties: the condition is per element and therefore
   sufficient but not necessary, the necessary one being only that the star sum
   vanish; and it holds **only** if the same `beta_i` appears in both mass
   matrices and both nodal residuals, and both residuals are on the same
   configuration. The frozen-`beta` convention is thus a requirement, not a
   convenience — which closes the draft's own open remark that the evaluation
   stage of the distribution matrices "is not merely a coding choice". This
   answers Zhenyu's fourth question.
5. New subsection `section:ALE_RD_two_forms` — the comparison of 8.1, the table,
   the recommendation of 8.4, and the positivity caveat on
   `|Sbar_i^{n+1/2}|`.
6. In `section:ALE_RD_topology` — the `m_i` in the unnumbered moment identity is
   now restricted to triangles inside the patch, without which the identity as
   written is false (the difference identity survives regardless, because the
   outside contributions are common and cancel); the three-line elementary
   derivation, plus the `P^1` linear-reproduction argument that explains it;
   the generalisation that both moment identities hold **globally and exactly
   for any two triangulations of the same point set**, so the isolated-flip and
   quadrilateral-patch hypotheses are unnecessary and cascades are covered, the
   only real hypothesis being an unchanged point set, i.e. no
   refinement/derefinement; and the observation that free-stream preservation is
   round-off exact **across** a connectivity change, so the flip perturbs only
   the conserved integral. This answers Zhenyu's third question.

### 8.4 Recommendation on the form, and its implementation consequence

**Adopt the published Proposition 4.1 form**, unless a specific advantage of the
endpoint-mass variant is identified:

- its second-order accuracy, conservation and DGCL compliance are proved, not
  assumed;
- it needs no quantity evaluated on the old connectivity, which finding 8.3.2
  shows is unavailable in AREPO;
- both stages share one nodal coefficient, so there is no intra-step rebase;
- its ALE upwind parameter (59) is **exactly** the shifted eigenvalue already
  implemented at `residual_distribution_solver.c:1758-1766`, including the
  element-averaged `sigmabar`, which the paper confirms is the `P^1` element
  average.

The endpoint-mass form's one advantage is that its divisor is the plain new
median dual, so `Q_i = m_i U_i` keeps its usual meaning against AREPO's storage.
That is a storage-layer convenience and is outweighed by having to re-derive
truncation error and positivity for an unpublished variant.

**This changes the implementation estimate of section 7.5.** Under the published
form the change set becomes smaller, not larger:

1. evaluate element geometry at `x^{n+1/2}` instead of `x^{n+1}`
   (`triangle_get_normals_area` takes coordinates rather than reading `DP`);
2. replace `DualArea` by `|Sbar_i^{n+1/2}|`, computed from `|T^n|`,
   `|T^{n+1/2}|` and `|T^{n+1}|`;
3. replace `tri_normals_list[i].area` by `|T^{n+1/2}|` in the F1 target;
4. carry `U`, with one rebase per step, or accumulate increments directly;
5. **the geometric residual term recommended in section 7.5 item 2 is
   withdrawn** — it belongs to the endpoint-mass variant only. Under the
   published form there is no geometric source term in the distributed residual
   at all.

The K-matrix path needs no change beyond which coordinates its normals come
from. `|S_i^n|` is not needed.

New gate, from the paper's own caveat: `|Sbar_i^{n+1/2}|` can become negative
under strong compression, invalidating the positive-coefficient analysis.
Arpaia--Ricchiuto argue it is `O(h^2)` when the per-step displacement is `O(h)`
and report that it never occurred; at AREPO's quasi-Lagrangian design point that
is not evidence, so a non-positive count must be a standing diagnostic.

### 8.5 Correction to section 7.4

Section 7.4 argued, from AREPO's finite-volume trapezoidal GCL, that the M1
free-stream gate should be relaxed from round-off to scheme order. **That was
too loose.** Because the 2-D area identity is exact for linear trajectories, both
candidate formulations preserve free-stream to round-off, on fixed connectivity
and across a flip alike (8.3.6). What is not round-off is only the conserved
integral across a flip, at `O(h^4)` per patch. The two should not have been
combined. Section 7.8 gate 3 should read round-off; gate 4 remains as written.

### 8.6 Still open

1. **The choice of form is Zhenyu's to make** and is the gating decision; every
   other item in 8.4 follows from it.
2. Campoli et al. has not been checked directly, so the provenance of the
   endpoint-mass form is inferred, not established.
3. ~~Section 6 of the Arpaia paper was not read.~~ **Read; see 8.8.** The
   extension to systems is formal and changes nothing in the ALE structure. The
   parameter-vector question is not settled by it and is restated in 8.8 with a
   concrete round-off acceptance test.
4. Everything in section 7 that Codex and Kimi were asked to arbitrate remains
   open; nothing here supersedes it.

### 8.7 Correction: the two forms are the same scheme up to one exhibitable term

Zhenyu asked which paper "Campoli et al." is. Checking it changes 8.1 and 8.4.

**The reference.** L. Campoli, P. Quemar, A. Bonfiglioli & M. Ricchiuto,
*Shock-Fitting and Predictor-Corrector Explicit ALE Residual Distribution*, in
*Shock Fitting: Classical Techniques, Recent Developments, and Memoirs of Gino
Moretti*, Shock Wave and High Pressure Phenomena, Springer, 2017, pp. 95-116,
`10.1007/978-3-319-68427-7_5`. Author draft:
`https://www.math.u-bordeaux.fr/~mricchiu/sf-draft.pdf`; HAL `hal-01625413`.
Added to `chapter4bib.bib` as `Campoli_ShockFitting_2017`.

Its section 2.2 equations (1)-(8) match `RK2_timestep_movingmesh_analysis.md`
§7.2 term by term and number by number; that transcription is faithful. So the
endpoint-mass form **is published**, and 8.1's "unpublished variant" is
withdrawn. Campoli et al. moreover introduce it as "the two-step explicit
Residual Distribution (RD) method developed in [16, 4, 15]", and Ricchiuto is an
author of both papers, so the two are presented in the literature as one method.
What remains true in 8.1 is only the narrower point that the reference table in
section 2.1 attributes the endpoint-mass equations to the wrong paper.

**Why they are the same, which was not obvious.** Under the two hypotheses
already established in 8.2 — F1 mass matrices `m_ij^{T,s} = (|T^s|/3) beta_i`,
and `beta_i` frozen across the stages — the endpoint form collapses. Writing
`Dw = w^* - w^n`, an overbar for the element mean (so that
`integral_{T^s} v_h = |T^s| vbar` for a `P^1` field) and `D|T| = |T^{n+1}| - |T^n|`:

1. split the mass term,
   `sum_j [m_ij^{n+1} w_j^* - m_ij^n w_j^n]/dt
      = beta_i |T^{n+1}| Dwbar/dt + beta_i (D|T|/dt) wbar^n`;
2. eliminate the conservative residual using
   `phi_ALE = phi_tilde - (D|T|/dt) wbar`, which follows from
   `div sigma_h` being constant on a `P^1` element together with
   `D|T| = dt |T^{n+1/2}| div sigma_h`;
3. hence
   `(1/2)[phi_i(w^n) + phi_i(w^*)]
      = (beta_i/2)[phi_tilde(w^n) + phi_tilde(w^*)]
        - beta_i (D|T|/dt)(wbar^n + wbar^*)/2`;
4. the two terms in `D|T|` collect to `- beta_i (D|T|/dt) Dwbar/2`, which is
   again proportional to `Dwbar` and merges with step 1, giving
   `beta_i (Dwbar/dt) [ |T^{n+1}| - D|T|/2 ]
      = beta_i (Dwbar/dt) (|T^n| + |T^{n+1}|)/2`.

So the endpoint-mass nodal residual is *identically*

```
Phi_i^T = beta_i { (Dwbar/dt) (|T^n|+|T^{n+1}|)/2 + (1/2)[phi_tilde(w^n)+phi_tilde(w^*)] }
```

against Arpaia's

```
Phi_i^RK2 = beta_i { (Dwbar/dt) |T^{n+1/2}|        + (1/2)[phi_tilde(w^n)+phi_tilde(w^*)] }.
```

The residual parts are now literally identical and the geometric source term has
vanished from both. What is left is one scalar per element and one per node.

**The difference is one term, the same in both places.** The signed area is
quadratic in `t` for linear vertex trajectories, so
`|T^{n+1/2}| = (|T^n|+|T^{n+1}|)/2 - (1/8) dt^2 A''`. With
`delta_T = (1/8) dt^2 A'' = (dt^2/8)(sigma_1-sigma_0) x (sigma_2-sigma_0)`:

```
(|T^n|+|T^{n+1}|)/2 = |T^{n+1/2}| + delta_T                          (mass)
|T^{n+1}|           = [|T^{n+1/2}| + (|T^{n+1}|-|T^n|)/2] + delta_T  (divisor)
```

the bracket being exactly the element contribution to `|Sbar_i^{n+1/2}|`. **The
endpoint-mass form is Arpaia's form with the same `delta_T` added to both the
mass coefficient and the nodal divisor.** Since
`delta_T/|T| = O((dt |grad sigma|)^2)`, this is a second-order-small relative
modification; the updates agree to `O(dt^3)` locally, at the scheme's own
truncation level. 8.1's estimate of `O(dt)` was one order too pessimistic.
`delta_T` vanishes for uniform mesh velocity over the element, in particular for
rigid translation; for a linear velocity field
`sigma = M x + c` it is `(dt^2/4) |T^n| det M`.

**Two by-products of the rewriting, both useful.**

- The DGCL becomes **manifest** rather than a cancellation: for a uniform state
  `Dwbar = 0` and `phi_tilde(U_0) = 0`, so `Phi_i^T = 0` identically, whatever
  the divisor. This is the form in which condition
  `eq:ALE_RD_nodal_DGCL_condition` should be tested.
- **Neither form ever assembles the conservative residual.** In both, the
  geometric source term is absorbed into the coefficient of `Dwbar`, and the
  only distributed residual is `phi_tilde`, whose discrete realisation is the
  shifted upwind parameter already in the code.

**Corrections to 8.4.** Of the four reasons given there for preferring the
Arpaia form:

| reason | status |
| --- | --- |
| published accuracy/DGCL analysis | weakened — both are published; Arpaia's is the more explicit analysis |
| needs no old-connectivity quantity | **withdrawn** — `\|Sbar^{n+1/2}\|` also needs `\|T^n\|`; both need only pulled-back geometry, neither needs `T_h^n` |
| one divisor shared by both stages | **withdrawn** — Campoli's (2) and (5) also carry `\|C_i^{n+1}\|` on both sides |
| upwind parameter is the existing eigenvalue shift | stands, and now applies to **both** forms |

Against that, the endpoint form's divisor summed over the star is the plain
median dual AREPO already accumulates, so `Q_i = m_i U_i` keeps its usual
meaning, whereas `|Sbar_i^{n+1/2}|` needs a separate accumulation.

**Revised recommendation.** Do not choose in advance. Implement the common
structure — `phi_tilde`, one element mass coefficient, one nodal divisor — and
select the pair of scalars at compile time. The choice then becomes a cheap
numerical experiment. Item 5 of 8.4, withdrawing the separate geometric residual
term, stands and now applies to both forms.

The corresponding Chapter 4 subsection `section:ALE_RD_two_forms` has been
rewritten to carry this derivation in full, since the equivalence is not
apparent from the two published presentations.

### 8.8 Arpaia section 6, the Euler system: what it does and does not settle

Read to close item 3 of 8.6. Paper pages 533-535.

**The extension to systems is formal.** Section 6.1 states that the schemes of
their section 4.5 "extend formally to hyperbolic systems of conservation laws,
without any obvious change in dimensions for the residuals", the upwind
parameters becoming matrices `k_i = K(u, n_i)/2`. The sign and `(.)^+` operators
are computed by standard eigenvalue decomposition; nonlinear schemes are applied
through a characteristic decomposition, with the blended scheme projected onto
the eigenvectors of `K(u, uhat)` and the LLxF-SUPG smoothness sensor built from
an entropy residual `phi_s^K = l_s . Phi^K / dt`.

**Nothing in the ALE structure changes for systems.** The modified median dual,
the midpoint configuration, the mass matrices and the DGCL argument are carried
over unaltered. That is a positive result for this project: the section 8.7
equivalence, derived for a scalar, needs no system-specific amendment, because
it is pure algebra in the mass coefficients and never touches the eigenstructure.

**What it does not settle, and this remains open.** The paper does not say which
of the two conservation routes of its own section 3.3.1 it uses for the Euler
system — contour integration of `phi^K = integral_{dK} f(u_h).n ds`, or an exact
Jacobian mean-value linearisation. The project's code uses the latter, the Roe
parameter-vector linearisation, and section 7.9 item 3 flagged that the code's
mesh-velocity term is then
`integral sigma_h . grad Zhat_h` rather than
`integral sigma_h . grad U_h`.

After the 8.7 rewriting this concern becomes sharper and also more testable.
Conservation of the scheme rests on the conservative residual `phi_ALE` being a
pure boundary flux, which telescopes. In the rewritten form `phi_ALE` is never
assembled: it is split into the distributed `phi_tilde` and the geometric part
folded into the coefficient of `Dwbar`. The split is exact in the continuum,

```
- boundary-integral (sigma_h.n) w_h  =  - integral sigma_h.grad w_h
                                        - integral w_h div sigma_h,
```

but it is only exact **discretely** if both pieces use the same interpolant. If
the first is built on the parameter-vector interpolant `Zhat_h` while `wbar` in
the second is the arithmetic mean of the conservative nodal states, the two do
not reconstruct the boundary flux and conservation leaks at the level of the
discrepancy.

**Concrete acceptance test.** Implement both routes and require them to agree to
round-off: the original Campoli form, which assembles `phi_ALE` explicitly and
whose conservation is manifest by telescoping, against the rewritten form of
8.7. Disagreement beyond round-off localises the broken discrete identity
exactly. This is cheap, needs no analytic solution, and should be an M1 gate.

**A ready-made M1 test case.** Section 6.2.1 is directly reusable and is a
better first target than anything invented here:

- advection of a constant-density vortex, freestream velocity `(6, 0)`,
  `rho_0 = 1.4`, maximum Mach `0.8`, on `[0,1]^2` to `t_max = 1/6`, with
  `h` in `{1/40, 1/80, 1/160, 1/320}`;
- prescribed mesh motion
  `x = X + 0.1 sin(2 pi X) sin(2 pi Y) sin(2 pi t / t_max)`, and likewise for
  `y`, which **returns to the identity at `t_max`**, so the ALE and Eulerian
  solutions are directly comparable on the same nodes;
- `dt = CFL min_i |S_i| / sum_K alpha^K` with `CFL = 0.8`;
- published outcome: second order in the ALE framework for both the lumped and
  the selective formulation, with LDA-N dropping to 1.5 because it switches to N
  in the strong-gradient region.

This gives M1 a prescribed-motion, fixed-connectivity, published-order target
before any AREPO-specific mesh motion is enabled, and its periodic mapping is
exactly the "non-trivial periodic deformation" the free-stream gate has been
asking for since section 4.

**Not read.** The Appendix proof of Proposition 4.1, and sections 6.2.2-6.2.3
(the 2-D Riemann problem and the moving-boundary application).

---

## 8. 2026-08-06 (later): write the ALE-RD mathematics before changing the solver

- Decision: Zhenyu, following the section 6/7 discussion.
- Draft written by: Codex.
- Solver source changed: **no**.
- Thesis files changed:
  `MyThesis/Zhenyu-PhDThesis/zhenyu_thesis/chapter4/chapter4.tex`,
  `chapter4/chapter4bib.bib`, and
  `chapter4/figures/delaunay-rd-moving-mesh-timeline.png`.
- Validation: `pdflatex -interaction=nonstopmode -halt-on-error master.tex`
  completed and produced the thesis PDF with the new Chapter 4 and figure.

### 8.1 Why the sequence changes

Static implementation work could be checked directly against the equations in
thesis Chapter 3. Moving-mesh discussions had instead begun to choose storage,
rebase, topology, and hierarchical mechanisms before Chapter 4 contained a
mathematical method. The disagreement between sections 6 and 7 is largely a
symptom of this inversion: `Q_i=m_i U_i` was first read as a finite-volume cell
integral and later as the storage representation of a nodal finite-element
degree of freedom.

The binding interpretation in the Chapter 4 draft is now:

```
U_i             intensive nodal conserved state; the RD degree of freedom
m_i = |S_i|     P1 row-sum lumped mass / median-dual coefficient
Q_i = m_i U_i   optional AREPO storage and residual-accumulation representation
```

An individual `Q_i` is not treated as material in a median-dual finite-volume
cell. The global sum `sum_i m_i U_i` remains the discrete integral of the P1
field and is the relevant conservation quantity.

### 8.2 Mathematics now drafted

Chapter 4 now contains, using Chapter 3 notation:

1. the moving `P1` basis and nodal mesh-velocity interpolation;
2. conservative and intensive ALE forms of the Euler equations;
3. the conservative residual `phi_ALE` and the geometrically
   non-conservative predictor residual `phi_tilde`;
4. the exact midpoint triangle-area identity for linear vertex trajectories;
5. free-stream preservation as the DGCL definition;
6. an endpoint-mass two-stage RK-RD **working formulation**;
7. local mass-matrix conservation and nodal DGCL compatibility conditions;
8. direct `Delta U` accumulation and `Q` rebase as alternative storage
   realisations;
9. the pulled-back-new-connectivity construction for equal timesteps;
10. the zeroth- and first-moment identities of an edge flip and the smooth
    `O(h^4)` patch defect;
11. a separate hierarchical subsection and explicit acceptance gates.

The endpoint-mass formulation is intentionally labelled a working
specification. Its algebraic equivalence to the modified-midpoint-mass form of
Arpaia, Ricchiuto & Abgrall must be checked before it is treated as final.

### 8.3 Direct `Delta U` is clean, but not universal

For static N/lumped RD,

```
m_i Delta U_i = -Delta t sum_T phi_i^T
```

can be implemented by accumulating the intensive increment directly. This
avoids carrying an old `Q=m_old U` through a rebuild and dividing it by a new
mass. For equal timesteps this is the clearest first prototype.

It is not a universal replacement for a residual ledger:

- LDA/F1 has a non-diagonal element mass action;
- an ALE corrector contains old/new endpoint mass terms, not always one scalar
  `m_i Delta U_i`;
- an inactive hierarchical vertex can receive contributions before the mass
  operator for its closing endpoint is known.

The draft therefore distinguishes a committed nodal state from

```
L_i^pending = -sum_events Delta t_T phi_i^T,
```

an integrated residual numerator which is converted to `Delta U` only when the
relevant interval closes. This preserves the useful additive/MPI-ledger
property without assigning finite-volume meaning to `Q`.

### 8.4 What the new timeline establishes

The new figure uses the patch `J,K,L,M` and the flip `KL -> JM`:

- `M` is the active fine generator;
- `J,K,L` are inactive coarse generators, but all four have mesh velocities
  and are drifted to every common geometry time;
- before the flip, `KML` is fine/due and `JKL` is coarse/not due;
- after the flip, both `JKM` and `JML` contain `M` and are fine/due.

The drawn flip occurs at `2 Delta t`, exactly the endpoint of the old `JKL`
coarse clock. This is a clean sufficient case: close the old interval first,
rebuild, then open the new fine intervals. No element identity needs to cross
the flip, and nodal `U` passes through unchanged.

The unresolved case is a flip at a fine synchronization point strictly inside
an old coarse interval. Then an element can disappear after its opening RK
contribution but before its closing contribution, while the new elements have
no corresponding predictor history. Direct `Delta U` solves the spatial state
transfer but not this interrupted time quadrature.

### 8.5 Geometric activity contract

Inactive does not mean stationary. Every vertex of a due triangle needs

```
x_i(t_stage), sigma_i(t_stage), U_i(t_stage)
```

at one common absolute stage time. An active generator may receive a newly
computed mesh velocity; an inactive generator continues on its stored drift
trajectory. Setting inactive mesh velocities to zero would corrupt midpoint
geometry, `div(sigma_h)`, area change, and the predicted flip time.

The triangle mesh velocity is the P1 interpolant of all three nodal velocities.
The current element-average `Velvertex_avg` may shift characteristic speeds,
but it is not enough to construct the geometric source or DGCL.

### 8.6 Work blocked on mathematical review, not code

Before solver changes, review must settle:

1. the endpoint-mass versus modified-midpoint-mass RK2 equivalence;
2. the exact stage geometry and distribution matrix used in each mass term;
3. whether the pulled-back-new-connectivity smooth flip defect preserves the
   desired global convergence order in repeated flips;
4. the shock-case acceptance threshold for the topology quadrature defect;
5. whether hierarchy initially restricts flips to closed affected stars,
   locally synchronises a flip patch, or adopts a vertex/event-based time
   quadrature.

Until these are explicit, implementation estimates such as "one-line rebase"
or "no topology treatment" are hypotheses rather than specifications.

## 9. 2026-08-10: mesh-only reference tests for the common ALE geometry

- Author: `Codex`, following Zhenyu's decision to test the geometry before
  changing the AREPO solver.
- New reference test:
  `/home/zwu/Hydro_data_analysis/Analysis/moving_mesh/ale_geometry_identities.py`.
- Corrected feasibility tool:
  `/home/zwu/Hydro_data_analysis/Analysis/moving_mesh/ale_feasibility.py`.
- **No AREPO solver source was changed in this entry.**

### 9.1 Common geometry tested

The test constructs the Delaunay triangulation only at the new point positions.
For every triangle of that post-rebuild connectivity it evaluates the virtual
configurations

```
x_old = x_new - dt sigma
x_mid = x_new - (dt/2) sigma
x_new
```

and returns `A_old`, `A_mid`, `A_new`, the midpoint boundary mesh flux, and

```
delta_T = (A_old + A_new)/2 - A_mid.
```

Both candidate scalar pairs are generated from the same data:

```
Arpaia: M_T = A_mid,                 D_T = A_mid + (A_new-A_old)/2
Campoli: M_T = (A_old+A_new)/2,      D_T = A_new
```

The test requires, element by element,

```
A_new-A_old = dt integral_boundary(T_mid) sigma_h.n ds
M_C-M_A = D_C-D_A = delta_T
delta_T = (dt^2/8) (sigma_1-sigma_0) cross (sigma_2-sigma_0)
```

to round-off. It also tests the explicit centre-distributed geometric
cancellation required by endpoint N/lumped. These are hard pass/fail checks;
an inverted pulled-back triangle is counted as a geometric hazard instead of
being confused with an algebraic failure.

### 9.2 Results

The 30-step run

```
python Analysis/moving_mesh/ale_geometry_identities.py --steps 30
```

passed all **754** algebraic checks.

- Four analytic single-triangle motions (translation, expansion, shear and a
  general affine motion) gave a maximum DGCL residual of `2.1e-16`.
- Rigid translation gave `delta_T = 0` exactly. The other motions agreed with
  the analytic cross-product formula to round-off.
- The square edge-flip patch reproduced the median-mass jump
  `(1/3,1/6,1/3,1/6) <-> (1/6,1/3,1/6,1/3)`. Its zeroth and first moment
  defects were exactly zero. Carrying unre-based `Q` produced a large nodal
  state jump in the deliberately arbitrary test state, while
  `Q <- Q m_new/m_old` preserved every `U_i` to round-off.
- Scaling the patch through six factors of two gave the quadratic-state flip
  defect orders `(4,4,4,4,4)` exactly.
- Periodic jittered `n=24` and SWIFT-glass `n=48` meshes were evolved for 30
  steps under both Yee and KH prescribed velocities. Topology changed hundreds
  of times in every case. The largest element DGCL residual was `6.87e-16`,
  the largest `delta_T` identity error was `8.85e-16`, new and modified-dual
  area coverage differed from the box by at most `1.42e-14`, and no modified
  nodal divisor was non-positive.
- Adding the constant velocity `(0.73,-0.41)` to every generator on the
  jittered mesh changed no triangle key. The maximum difference among
  `A_old`, `A_mid`, `A_new` and `delta_T` was `1.21e-15`.

### 9.3 Correction: the earlier KH pulled-back inversions were false positives

The original `ale_feasibility.py::old_position_validity` separately wrapped
the old coordinates and then applied the periodic image offsets selected by the
new triangulation. When a generator crossed a periodic boundary, this moved its
old image by one full box length relative to the other two vertices and created
a spurious negative signed area.

The corrected construction starts from the unwrapped new triangle and follows
the continuous trajectory backward:

```
new_points = wrapped_new[indices] + new_image_offsets
old_points = new_points - dt velocity[indices].
```

After this correction, 30-step surveys at `n=48` and `n=96` found **zero**
pulled-back inversions and zero near-degenerate triangles for Yee at CFL 0.8
and KH at CFL 0.3 and 0.8. The maximum old-geometry tiling defect was
`2.22e-16`. The earlier non-zero KH inversion counts in the feasibility output
are therefore withdrawn; they measured a periodic-unwrapping bug, not a
failure of pulled-back-new connectivity.

### 9.4 What this establishes, and what it does not

The mesh-only reference now supports one common geometry layer for both scalar
pairs without constructing an old or midpoint Delaunay mesh. It tests exactly
the quantities a later C structure must expose:

```
A_old, A_mid, A_new, midpoint normals, sigma_i, delta_T,
new median dual, modified midpoint dual, inversion/positivity counters.
```

This is sufficient to begin a C geometry implementation when desired, with
Python-versus-C comparison by sorted particle IDs and triangle keys as the next
gate. It does **not** yet test the Roe-parameter-vector interpolation defect,
Euler conservation, a uniform-state solver update, MPI ownership, pathological
large-displacement meshes, hierarchical timesteps, or 3-D. Fluid tests should
follow in the order uniform state, Yee plus boost, Gresho plus boost, and only
then shock/shear cases.
