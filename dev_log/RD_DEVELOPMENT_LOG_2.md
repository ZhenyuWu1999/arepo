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
>
> **Latest implementation status, 2026-08-10:** section 10 records the first
> diagnostic-only Stage 0 implementation inside AREPO and a real Gresho
> regularisation on/off comparison.  The element DGCL and area identities hold
> to round-off.  Regularisation did not materially reduce the number of edge
> flips per unit physical time, but it prevented the severe mesh degradation
> and space-time triangle inversions seen without regularisation.  No ALE-RD
> fluid update has been implemented yet.  The immediate test order and the
> mesh-velocity-predictor question are fixed in section 10.6.

- Opened: 2026-08-05.
- Time zone: Europe/London.
- Scope: the ALE / moving-mesh phase, and anything else that arises from here
  on. Volume 1 is not reopened; corrections to it are recorded here with a
  pointer, so that the two read as one chronology.

Why a new volume: volume 1 reached 8971 lines and no longer fits comfortably in
an agent context window, which had begun to cost re-derivation of settled
facts. The split is administrative. Nothing in volume 1 is retracted by it.

---

## Index of sections

Written so that a reference like "section 20" carries its subject without
opening the file. Sections 11 to 14 are Codex's, written concurrently with 7
to 10 and renumbered without moving text; their dates therefore interleave.

| # | subject in one line |
| --- | --- |
| 1-5 | handover state, literature, feasibility, phase plan, open questions |
| 6 | Codex: the median-dual area jumps at a Delaunay flip, so the DGCL may fail |
| 7 | that jump is second order, not O(1); keep the median dual, not Voronoi |
| 8 | the working RK2 form is Campoli's, not Arpaia's; the two are one scheme |
| 9 | the flip defect measured offline on real cascading connectivity changes |
| 10 | Stage 0: a geometry-only diagnostic inside AREPO, driven by the FV solver |
| 11-13 | Codex: write the maths first; mesh-only reference tests; Stage 0 and regularisation |
| 14 | Codex: audit of Stage 0, and the decision to start the fluid prototype |
| 15 | the flip first moment and the drift reconstruction verified inside AREPO |
| 16 | Codex: frozen interface for the first fluid slice |
| 17 | Codex: first fluid-coupled ALE-RD slice; a conservation defect appears |
| 18 | that defect is two mechanisms: interpolation (fixed) and topology (not) |
| 19 | regression gates for the interpolation fix, and the topology order |
| 20 | the remaining defect is purely topological and converges at fourth order |
| 21 | LDA enabled on the moving mesh; the pseudo-inverse switch costs 87% for nothing |
| 22 | what sigma is made of, and the reproducibility cleanup |
| 23 | Galilean invariance: the first physics result of the phase |
| 24 | Arpaia against Campoli, verified numerically inside the solver |
| 25 | the quantitative boost and resolution study, and the boost-10 failure |
| 26 | boost 10 is a conditioning problem, not a CFL one |
| 27 | Codex: boost 10 recovered by an element co-moving frame; an RD CFL limiter |
| 28 | Codex: the co-moving fix had dropped a term; a contour residual instead |
| 29 | Codex: Chapter 4 reorganised around the contour residual |
| 30 | the contour and timestep effects separated; connectivity hashes date the flips |
| 31 | Yee decides the contour residual; the horizon of particlewise comparison |

The form-selection campaign that follows section 31 has its own document,
`dev_log/RD_ALE_FORM_SELECTION.md`: it states the five compile switches and
their derivations, then decides a recommended default from an eight-build
campaign over particle-level, smooth and discontinuous tests.

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

1. ~~**Is `sum_i Delta m_i^topo x_i = 0` correct?**~~ **Measured; see section 9.1.
   Confirmed to round-off on real connectivity changes including cascades.**
   The argument is that `sum_i m_i x_i = sum_T |T| g_T = integral x dx` over the
   patch, identical for both triangulations because both tile it. This was the
   load-bearing step; it holds.
2. **Is it legitimate to treat `U_i` as a point value carried through the
   flip?** In `P^1` Lagrange terms it is by definition. A reviewer could argue
   that the converged RD solution's `U_i` is only a point value to `O(h^2)`, and
   that this weakens 7.3(a).
3. **Does the leak accumulate coherently?** **Partly answered; see section 9.4.**
   No drift is detectable at 400 steps, and for Lagrangian motion the per-step
   defects are serially uncorrelated, so the random walk is the right model. A
   weak drift below the detection threshold is not excluded, and settling that
   requires a long run on a mesh that stays healthy, which requires AREPO's
   regularisation. Carried into the implementation as a standing diagnostic.
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

## 9. 2026-08-07: the topology defect measured on real connectivity changes

- Author: `Claude Code Opus 5`, at Zhenyu's request, before any AREPO change.
- **No solver source was changed.** Mesh-only measurement, no build, no cluster.
- New code: `Hydro_data_analysis/Analysis/moving_mesh/ale_topology_defect.py`,
  `python ale_topology_defect.py --steps 40 --long-steps 400`.
- Complements Codex's `ale_geometry_identities.py` of 2026-08-06, which was run
  and independently reproduces every claim of section 8.7: `delta_T` vanishes for
  rigid translation, matches the closed form
  `(dt^2/8)(sigma_1-sigma_0) x (sigma_2-sigma_0)` to round-off, and the mass and
  divisor pair identities `Campoli - Arpaia = delta_T` hold in both places.
  226 checks, all passing. It also reproduces section 7.3: the unrebased `Q`
  gives `max|dU| = 2.1`, an `O(1)` jump, while the rebase preserves `U` exactly.

### 9.1 The moment identities hold on real, cascading flips

`ale_geometry_identities.py` verifies the moment identities on **one symmetric
unit square**, which is the easiest instance, and obtains the `O(h^4)` order by
scaling that one patch. This entry measures the same quantities on the
connectivity changes that actually occur under Lagrangian motion, grouping the
symmetric difference of the two triangulations into connected patches.

40 steps at CFL 0.3, relative errors normalised by the patch weight and by the
patch diameter:

| case | changed | patches | **cascades** | rel abs zeroth | rel abs first |
| --- | ---: | ---: | ---: | ---: | ---: |
| jittered n=24 yee | 883 | 306 | **93** | 9.6e-16 | 4.4e-16 |
| jittered n=24 kh | 832 | 325 | **71** | 1.2e-15 | 7.2e-16 |
| jittered n=48 yee | 1727 | 719 | **110** | 1.1e-15 | 8.2e-16 |
| jittered n=48 kh | 1631 | 689 | **106** | 2.3e-15 | 1.2e-15 |
| swift48 n=48 yee | 1433 | 520 | **134** | 1.5e-15 | 7.8e-16 |
| swift48 n=48 kh | 1352 | 432 | **137** | 1.5e-15 | 1.0e-15 |

6462 checks, all passing. The cascade column counts patches with more than two
triangles on one side, that is, not isolated 2-2 flips: between 71 and 137 per
case. **Section 7.9 item 1, the load-bearing step of section 7, is confirmed**,
and so is section 8.3's generalisation that the identities need no
isolated-flip hypothesis and hold for any two triangulations of the same point
set.

### 9.2 The periodic boundary is a real trap, and AREPO inherits it

This deserves emphasis, because it was a genuine failure before it was
understood, and the same trap exists in the AREPO implementation.

The first run of the patch moment test **failed on four patches**, with relative
first-moment errors of 0.15 to 0.41 — `O(1)`, not round-off. All four straddled
the periodic boundary. The cause is not mathematical. `periodic_triangulation`
keeps the image whose lowest-index vertex lies in the central copy; when the
connectivity changes, the lowest-index vertex of a boundary-straddling patch can
change, so **the same physical point is represented by different periodic images
in the old and the new triangulation**. The first moment then differs by a
lattice vector times the patch area, which is exactly the observed magnitude.
Minimal-imaging each patch against an anchor before taking any moment removes it
completely, and is unambiguous because a patch is `O(h)` across while the box is
`O(1)`.

**The AREPO consequence.** The same reconstruction is required there:
`x^n = x^{n+1} - VelVertex * dt` must be formed for ghost points as well as
local ones, and **the image chosen for a ghost point must be the one consistent
with the element that uses it**, not an independently chosen minimal image.
`DP[].x` already carries the resolved image for the current configuration, and
subtracting `VelVertex * dt` preserves it, so the natural implementation is
correct — but only if `VelVertex` for the ghost is fetched through the same
`PrimExch` indexing that the residual loop already uses at
`residual_distribution_solver.c:1581`, and never recomputed from a wrapped
position. A per-patch first-moment check belongs in the Stage 0 diagnostics from
the start, rather than being reached for after a symptom appears.

### 9.3 The `O(h^4)` order, on hundreds of real patches

Per-patch defect `|sum_{i in P} dm_i U_i|` for a smooth periodic field, jittered
family, 40 steps:

| motion | n | patches | mean | order | median | order | worst | order |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| yee | 24 | 306 | 5.216e-4 | | 3.419e-4 | | 4.264e-3 | |
| yee | 48 | 719 | 2.600e-5 | **4.33** | 1.642e-5 | **4.38** | 1.525e-4 | 4.81 |
| kh | 24 | 325 | 8.025e-4 | | 6.558e-4 | | 5.702e-3 | |
| kh | 48 | 689 | 4.645e-5 | **4.11** | 3.861e-5 | **4.09** | 3.463e-4 | 4.04 |

The mean and the median are the meaningful statistics; the worst is an extreme
value over a few hundred samples. All six orders bracket 4. **Section 7.3's
`O(h^4)` per patch is confirmed on real flips.** The accumulated defect follows:
over the same 40 steps, `sum |D_n|` falls from 5.00e-2 at n=24 to 4.49e-3 at
n=48, a factor 11.1, or `h^3.5`, consistent with `h^4` per patch against a
roughly doubled patch count.

### 9.4 Accumulation: no drift detected, and the offline ceiling

The question of section 7.9 item 3 is whether the per-step defects add
coherently, giving a systematic drift `~ N mu`, or random-walk, giving bounded
noise `~ sqrt(N) s`. An earlier version of this script fitted a slope to
`|cumsum D|` on one realisation and returned exponents from -0.96 to 2.19,
including negative ones, which is the signature of an estimator measuring noise.
That approach is abandoned. The decomposition

```
sum_{n<=N} D_n = N mu + fluctuation of size ~ sqrt(N) s,   mu = mean(D), s = std(D)
```

is exact and needs no ensemble: `t = |mu| sqrt(N) / s` tests whether any drift
exists, and `N* = (s/mu)^2` is where a drift would overtake the walk.

400 steps, n=24, CFL 0.3. `map` is the Arpaia section 6.2.1 prescribed mapping,
whose displacement vanishes on the box boundary and returns to the identity each
period:

| motion | flips/step | **min\|T\|/mean\|T\|** | field | mu | s | **t** | **lag-1** |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| **map** | 51.7 | **1.6e-1** | trig | -1.21e-4 | 1.13e-2 | **0.21** | +0.889 |
| **map** | 51.7 | **1.6e-1** | bump | +1.82e-4 | 3.91e-3 | **0.93** | +0.629 |
| yee | 20.6 | 5.8e-3 | trig | +1.74e-4 | 3.34e-3 | 1.04 | -0.024 |
| yee | 20.6 | 5.8e-3 | bump | +3.10e-4 | 5.89e-3 | 1.05 | -0.021 |
| kh | 23.2 | **3.4e-4** | trig | +1.43e-4 | 5.17e-3 | 0.55 | +0.000 |
| kh | 23.2 | **3.4e-4** | bump | +6.84e-5 | 6.89e-3 | 0.20 | -0.019 |

**No `t` exceeds 1.05, so no statistically significant drift is present at 400
steps in any case or either field.** The lag-1 autocorrelation separates the two
kinds of motion: for Lagrangian motion it is essentially zero, so the per-step
defects are serially uncorrelated and **the random walk is the correct model**;
for the prescribed map it is 0.63 to 0.89, which is expected because the map is
smooth in time, and means the fluctuation grows faster than `sqrt(N)` at first
while still carrying no drift.

**The offline measurement has reached its ceiling, and the reason is the missing
regularisation.** The `min|T|/mean|T|` column is a mesh-quality monitor. After
400 unregularised Lagrangian steps the shear case has fallen to 3.4e-4, that is,
near-degenerate slivers, and the vortex to 5.8e-3. Those two rows are therefore
partly measuring a pathological mesh. The `map` row, whose mesh quality stays
bounded at 0.163 for the whole run while carrying the **highest** flip rate of
the three, is the trustworthy one, and it shows no drift.

Extrapolating at n=24 and CFL 0.3, which is the worst combination tested, with
`mu` taken at face value even though it is not significant:

| | N = 1e3 | N = 1e4 |
| --- | ---: | ---: |
| drift, one-sigma upper bound | 0.7-3.1e-3 | 0.7-3.1e-2 |
| random walk | 1.0-3.6e-3 | 0.3-1.1e-2 |

This is not negligible at that resolution and CFL, which corrects an earlier
verbal characterisation of the question as academic. It converges rapidly,
however: `h^3.5` in the accumulated defect from 9.3, and the production Yee
campaign runs at CFL 0.03, where 9.5 shows the flip rate is five times lower
again.

### 9.5 The dt sweep: `delta_T` grows as `dt^2`, and both hazards stay empty

Jittered n=48, single step, per CFL:

| CFL | changed (yee) | max `delta_T`/\|T\| (yee) | max (kh) | inverted pullback | **non-positive Arpaia divisor** |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.03 | 14 | 1.36e-5 | 1.06e-7 | 0 | **0** |
| 0.10 | 32 | 1.51e-4 | 1.17e-6 | 0 | **0** |
| 0.30 | 78 | 1.35e-3 | 1.04e-5 | 0 | **0** |
| 0.80 | 172 | 9.32e-3 | 7.41e-5 | 0 | **0** |
| 1.50 | 282 | 3.00e-2 | 2.60e-4 | 0 | **0** |
| 3.00 | 416 | 8.83e-2 | 1.04e-3 | 0 | **0** |

Three results:

1. **`delta_T` scales exactly as `dt^2`** — a tenfold CFL increase multiplies it
   by 99 — confirming the closed form of section 8.7 numerically.
2. **The caveat Arpaia--Ricchiuto raise against their own scheme never fires.**
   The modified median dual `|Sbar_i^{n+1/2}|` stays positive at every CFL up to
   3.0, and no pulled-back element inverts either. Their argument that the
   correction is `O(h^2)` for `O(h)` displacements survives at the
   quasi-Lagrangian design point, at least without regularisation.
3. **The choice of formulation is numerically almost immaterial.** At the
   production CFL of 0.3 the two forms' mass coefficients differ by 0.14 per
   cent on the vortex and 0.001 per cent on the shear layer. This is direct
   support for section 8.7's recommendation to implement the common structure
   and select the pair of scalars at compile time. The difference reaches only
   9 per cent even at CFL 3.

Note also that at CFL 0.03, which is what the Yee campaign's `dt = 0.25/n`
corresponds to, only 14 triangles change per step out of the whole mesh. **On
the thesis convergence runs the topology defect is close to absent.**

### 9.6 What this closes, and what must move into AREPO

Closed offline:

- the moment identities on real cascading flips (7.9 item 1);
- the `O(h^4)` per-patch order, on hundreds of samples rather than one square;
- `delta_T = O(dt^2)` and the equivalence of section 8.7, independently
  reproduced by Codex's script;
- the Arpaia positivity caveat, empty to CFL 3;
- the periodic-image trap, understood and fixed, with the AREPO requirement
  stated in 9.2.

Cannot be closed offline, and should be carried as Stage 0 diagnostics rather
than as separate experiments:

1. **Mesh regularisation.** Springel (2010)'s drift toward the cell centroid is
   not modelled here. It should reduce distortion and therefore the flip rate,
   which would make these numbers conservative, but that is an assumption. It
   also cannot be imitated by an analytic velocity field, because
   `set_vertex_velocities.c:166` switches the correction off entirely once a
   cell is round enough, so the real `sigma` carries a spatially discontinuous
   component.
2. **The residual weak drift.** Excluding a drift below `t = 1` needs a long run
   on a mesh that stays healthy, which is precisely what regularisation
   provides. A per-step `D_n = sum_i dm_i^topo U_i` output makes the answer a
   by-product of the real runs.
3. **Ghost and periodic image consistency**, per 9.2.

**Recommendation: proceed to the Stage 0 implementation**, which is the
diagnostic-only geometry layer, with the per-patch first moment and the per-step
`D_n` among its outputs from the first commit.

---

## 10. 2026-08-10: Stage 0 in AREPO — the instrument, and what it measured

- Stage 0 instrument: **Codex**, `src/mesh/rd_ale_geometry_diagnostics.c`, with
  `examples/gresho_2d/Config_ALE_Geometry_Stage0{,_NoReg}.sh` and matching
  parameter files. Hooked at `run.c:118` and `run.c:324`, and around
  `set_vertex_velocities`.
- Free-stream gate, per-generator diagnostic, CFL sweep, glass comparison and
  the two build-tooling fixes: **Claude Code Opus 5**.
- **The RD solver was not touched.** Every run below is a plain finite-volume
  AREPO run; the diagnostic only observes.

### 10.1 The design, and why it is the right Stage 0

Codex's decision is better than the Stage 0 proposed in section 9.6: **let the
finite-volume solver drive the mesh and have the diagnostic only observe.** That
buys the real quasi-Lagrangian `sigma`, the real regularisation and the real
Delaunay rebuild without a line of ALE-RD code and without any change to solver
behaviour. The paired regularisation-on/off Configs then answer 9.6 item 1
directly.

The section 9.2 periodic-image trap turns out to be **structurally absent** in
AREPO, which is worth recording because section 9 flagged it as a risk.
`rd_ale_point_velocity` maps a ghost back to its primary only to read
`VelVertex`, while the position stays `dp->x`, which already carries the
resolved image. `x^n = dp->x - dt * VelVertex` therefore preserves the image by
construction. The trap was real in the Python tiling and is not real here.

### 10.2 Codex's Gresho runs, and the section 8.7 identity inside AREPO

Gresho on `IC_gresho_v0_random48`, to `t = 0.5`:

| | regularisation on | regularisation off |
| --- | ---: | ---: |
| steps | 1222 | 2404 |
| edge flips per unit time | 9043 | 8847 |
| `max_delta_identity` | **6.5e-18** | **7.0e-18** |
| `max delta_T / \|T\|` | 7.8e-3 | 1.9e-2 |
| inverted pulled-back elements | **0** | **4** |
| non-positive Arpaia divisor | **0** | **0** |
| `min\|T\|/mean\|T\|`, final (worst) | 9.5e-2 | 2.6e-3 (7.5e-5) |
| `D_trig`: `t` statistic / lag-1 | 1.10 / +0.046 | 0.27 / -0.005 |
| `\|cumulative D_trig\|` | 4.9e-5 | 1.8e-5 |

Three results:

1. **The section 8.7 closed form for `delta_T` holds inside AREPO to 6.5e-18**,
   with real regularisation, real rebuilds and real quasi-Lagrangian motion.
   `delta_from_area` and `delta_from_velocity` are computed independently and
   agree at round-off. This is the strongest confirmation the equivalence of the
   two candidate formulations will get short of running them.
2. **Regularisation eliminates pulled-back inversions** (0 against 4) and keeps
   the mesh about a thousand times healthier by minimum area. It does not change
   the flip rate per unit time, which is the same to two per cent; what it
   changes is the step count, because a healthy mesh admits a larger timestep.
3. **The Arpaia positivity caveat never fires**, over 1222 and 2404 real steps.
4. No drift is detectable: `t <= 1.10`, lag-1 essentially zero, consistent with
   section 9.4.

### 10.3 Gate zero: the free stream, and the validation of the instrument

Section 9.6 asked for a case with an a-priori known answer. A uniform state with
uniform velocity and **regularisation off** gives one: `VelVertex` is then
exactly the fluid velocity, the mesh translates rigidly, the periodic Delaunay
triangulation is translation invariant, and
`delta_T = (dt^2/8)(sigma_1-sigma_0) x (sigma_2-sigma_0)` vanishes identically
because `sigma` is uniform. Every geometric diagnostic must therefore be exactly
zero. Initial conditions: the `random48` Gresho point cloud with
`rho = p = 1`, `v = (1, 0.5)`, in
`examples/gresho_2d/IC_freestream_random48.hdf5`.

1024 steps to `t = 0.5`:

| quantity | required | measured |
| --- | ---: | ---: |
| edge flips, total | 0 | **0** |
| `max delta_T / \|T\|` | 0 | **7.0e-13** |
| `max_delta_identity` | 0 | 3.8e-18 |
| pulled-back area coverage | 0 | 5.1e-15 |
| inverted, non-positive divisor | 0 | 0, 0 |
| `max \|D_n\|` per step | 0 | **7.6e-16** |
| `\|cumulative D\|` | 0 | **9.1e-15** |
| `min\|T\|/mean\|T\|` | constant | 4.1490e-3 for all 1024 steps |

**Every quantity that must vanish sits at round-off. The instrument is
validated.**

### 10.4 A per-generator ledger diagnostic, and what it shows

The aggregate probe defect is built from spatially periodic functions and is
therefore blind to a whole-lattice-vector image error, and it can hide a large
nodal error behind a cancellation. Added to the instrument: a median-dual nodal
mass snapshot **keyed by particle ID** — index keying would be wrong, because
the domain decomposition reorders `P` and `SphP` even on one rank — with four
new columns, `dm_signed_sum`, `dm_abs_sum`, `dm_abs_max`, `dm_touched_nodes`.

Its first result is the important one: across every run below,
`|sum_i dm_i|` stays at **4e-17 to 6e-17 per step**. **The zeroth-moment
identity of section 7.3, the load-bearing step of section 7, now holds inside
AREPO and not only in the offline Python.**

### 10.5 CFL sweep, with regularisation on

Gresho `random48`, regularisation on, to `t = 0.1`:

| CFL | steps | flips per unit time | `max delta_T/\|T\|` | inverted | non-pos `Sbar` | `\|sum dm\|` max | `max\|dm_i\|` | touched per step | `\|cum D\|` |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.05 | 2072 | 16470 | 3.09e-4 | 0 | 0 | 6.2e-17 | 6.142e-4 | 3.2 | 1.68e-5 |
| 0.10 | 1036 | 16540 | 1.10e-3 | 0 | 0 | 4.7e-17 | 6.150e-4 | 6.3 | 1.80e-5 |
| 0.30 | 265 | 16420 | 1.06e-2 | 0 | 0 | 5.4e-17 | 6.219e-4 | 24.3 | 1.97e-5 |
| 0.60 | 133 | 16480 | 2.75e-2 | 0 | 0 | 4.2e-17 | 6.255e-4 | 47.7 | 1.60e-5 |

Five results, of which the last has a direct design consequence:

1. `delta_T` grows as `dt^2` — CFL 0.1 to 0.3 multiplies it by 9.6 against a
   predicted 9 — confirming section 8.7's closed form under regularisation.
2. **The flip rate per unit time is independent of the timestep**, 16420 to
   16540 across a twelvefold range of `dt`. Connectivity change is a property of
   the flow and the regularisation, not of the discretisation.
3. **`max|dm_i|` is likewise independent of `dt`**, 6.14e-4 to 6.26e-4, as it
   must be: the nodal mass jump at a flip is a geometric quantity. Consistently,
   the number of nodes touched per step grows linearly with `dt`.
4. Neither hazard fires at any CFL up to 0.6.
5. **The accumulated ledger defect is independent of CFL**, 1.6e-5 to 2.0e-5.
   **Refining the timestep does not reduce the topology defect**, exactly as the
   theory says, because it is a topology effect and not a time-discretisation
   effect. The only lever is spatial resolution, where section 9.3 measured
   `h^3.5`. Any future claim that the defect has been controlled must therefore
   cite a resolution, never a timestep.

### 10.6 Glass against random: regularisation contributes nothing to a relaxed mesh

The free-stream run **with** regularisation on the `random48` cloud produces
1060 flips and a cumulative defect of 4.3e-5 — comparable to the full Gresho
vortex — even though the fluid state is uniform and there is no shear at all.
That invited the reading that regularisation is the dominant source of topology
change. **It is not.** The falling `regularisation_active_fraction`, 0.729 to
0.061, says the flips are a relaxation transient of an unrelaxed initial mesh,
and repeating the free stream on the glass confirms it:

| free stream, regularisation on | steps | flips per unit time | `reg_active` | `min\|T\|/mean\|T\|` | `\|cum D\|` | `max\|dm_i\|` |
| --- | ---: | ---: | --- | --- | ---: | ---: |
| `glass48` | 256 | **0** | 0.000 to 0.000 | 0.8747, constant | **1.1e-15** | **2.8e-18** |
| `random48` | 522 | 2120 | 0.729 to 0.061 | 1.40e-2 to 8.33e-2 | 4.3e-5 | — |

**On a mesh already near a centroidal tessellation, regularisation is inert: no
flips, no ledger defect, mesh quality unchanged to round-off.** The correct
statement of 9.6 item 1 is therefore that regularisation drives a substantial
relaxation transient on an unrelaxed mesh and contributes nothing once relaxed.

The operational consequence is concrete: **production moving-mesh runs should
start from a glass.** The first several hundred steps of a `random48` run
measure mesh relaxation, not physics, and any convergence study started from
such an initial condition is contaminated by it. This also applies to the
existing `random48` Gresho runs of 10.2.

### 10.7 Two defects in the build tooling

1. **Fixed.** `build_case.sh` required `libmkl_rt` in `ldd` whenever `MKLROOT`
   was set, but only `RESIDUAL_DISTRIBUTION` links LAPACKE. A diagnostic-only
   Stage 0 build correctly has no MKL and was refused publication, which is why
   the first Stage 0 runs bypassed the immutable artifact system and used a
   local `build_ale_stage0/`. The check is now conditional on the Config
   enabling `RESIDUAL_DISTRIBUTION`, with a reverse check that a Config without
   it must not link MKL either. All binaries here went through the normal
   artifact path.
2. **Not fixed, and more serious.** The build fingerprint is
   `git commit + tracked diff + Config + toolchain`. `rd_ale_geometry_diagnostics.c`
   is currently **untracked**, so editing it leaves `build_fingerprint` and
   `artifact_id` unchanged: rebuilding after the section 10.4 change produced the
   identical id `bb3059da014d-15fc659e04b2ad93`. Nothing went wrong here only
   because the build name differed, so a fresh bundle was compiled; the binary
   was verified to contain the new symbols. **A rebuild under the same name
   would have silently reused the stale binary**, which is precisely what the
   provenance system exists to prevent. The fix is to place the new sources under
   version control — `rd_ale_geometry_diagnostics.c`, the two Configs and the
   parameter files — so the diff hash covers them. Not done here, because it is a
   commit decision.

### 10.8 Status

Answered in AREPO:

- the section 8.7 `delta_T` identity, to 6.5e-18, under real regularisation;
- the zeroth-moment identity per generator, to 6e-17 per step;
- the instrument itself, by a free-stream gate in which every quantity that must
  vanish does;
- the effect of regularisation: it removes pulled-back inversions and keeps the
  mesh healthy, is inert on a relaxed mesh, and does not change the flip rate per
  unit time;
- the `dt` dependence: `delta_T ~ dt^2`, but flip rate, `max|dm_i|` and the
  accumulated defect are all `dt`-independent;
- the Arpaia positivity caveat, empty at every CFL up to 0.6.

Not done:

- **Yee.** `examples/yee_2d/` contains no initial condition and no generator;
  its `param.txt` points at a relative `./IC`. Running it needs an HDF5 writer
  built on the `Analysis/yee_boost` tooling. Its value is a direct comparison
  against the offline flip rates of section 3.3, which is now a cross-check
  rather than an open question.
- The first-moment identity per patch inside AREPO. The zeroth moment is
  covered by 10.4; the first moment would need patch assembly in C and is
  confirmed offline in 9.1.
- MPI rank invariance: the instrument is guarded to one rank.
- The section 8.8 round-off cross-check between the two formulations, which
  needs the flux and belongs to Stage 2.

---

---

> **Editorial note, 2026-08-11 (Claude).** Sections 11 to 14 were written by
> Codex concurrently with sections 7 to 10, and both authors numbered from 8.
> The file therefore carried two sections 8, two 9 and two 10; Codex's section
> 14.2 noticed the collision at section 10 only. The duplicates are resolved
> here by renumbering Codex's four sections to 11-14 **without moving any text**,
> so the reading order still matches the order in which each author wrote. Their
> dates consequently interleave with sections 7-10 rather than following them,
> and section 11 is dated earlier than section 7. Cross-references inside the
> renumbered sections were updated only where they pointed at Codex's own
> sections; references to sections 6, 7, 9.3-9.4 and 10 point at Claude's and
> are unchanged.
>
> **Attribution correction.** Commit `c742da4`, whose author line names Claude,
> also contains Codex's sections 11, 12 and 13. They were swept in because the
> whole log file was staged after checking only the diff statistics, not the
> diff itself, while Codex was editing the same file. The history is left as it
> stands and the error is recorded here instead. Sections 11-14 are Codex's work.

## 11. 2026-08-06 (later): write the ALE-RD mathematics before changing the solver

- Decision: Zhenyu, following the section 6/7 discussion.
- Draft written by: Codex.
- Solver source changed: **no**.
- Thesis files changed:
  `MyThesis/Zhenyu-PhDThesis/zhenyu_thesis/chapter4/chapter4.tex`,
  `chapter4/chapter4bib.bib`, and
  `chapter4/figures/delaunay-rd-moving-mesh-timeline.png`.
- Validation: `pdflatex -interaction=nonstopmode -halt-on-error master.tex`
  completed and produced the thesis PDF with the new Chapter 4 and figure.

### 11.1 Why the sequence changes

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

### 11.2 Mathematics now drafted

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

### 11.3 Direct `Delta U` is clean, but not universal

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

### 11.4 What the new timeline establishes

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

### 11.5 Geometric activity contract

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

### 11.6 Work blocked on mathematical review, not code

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

## 12. 2026-08-10: mesh-only reference tests for the common ALE geometry

- Author: `Codex`, following Zhenyu's decision to test the geometry before
  changing the AREPO solver.
- New reference test:
  `/home/zwu/Hydro_data_analysis/Analysis/moving_mesh/ale_geometry_identities.py`.
- Corrected feasibility tool:
  `/home/zwu/Hydro_data_analysis/Analysis/moving_mesh/ale_feasibility.py`.
- **No AREPO solver source was changed in this entry.**

### 12.1 Common geometry tested

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

### 12.2 Results

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

### 12.3 Correction: the earlier KH pulled-back inversions were false positives

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

### 12.4 What this establishes, and what it does not

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

## 13. 2026-08-10: Stage 0 in AREPO, regularisation, and the next test order

- Author: `Codex`, following Zhenyu's decision to exercise the real AREPO mesh
  before changing the RD fluid update.
- Status: **working tree only; not committed.**  This entry does not claim that
  ALE-RD is implemented.
- Scope of the completed runs: 2-D, periodic, equal timesteps, no refinement,
  one MPI rank.  Ordinary AREPO finite-volume hydrodynamics supplies the
  physical state and mesh motion; the new code observes geometry only.

### 13.1 Diagnostic-only C layer

The compile-time option `RD_ALE_GEOMETRY_DIAGNOSTICS` adds
`src/mesh/rd_ale_geometry_diagnostics.c`.  It is called after the initial mesh
and after every real AREPO mesh rebuild.  On the post-rebuild connectivity it
forms the continuous periodic trajectory

```
x_old = x_new - drift_dt VelVertex
x_mid = x_new - (drift_dt/2) VelVertex
```

using the periodic image already resolved for each Delaunay element.  It does
not construct an old or midpoint Delaunay mesh.  Its CSV records:

- actual-old, pulled-old, midpoint and new area coverage;
- removed and added edges by sorted particle ID;
- `A_old`, `A_mid`, `A_new`, `delta_T`, the element area/mesh-flux identity,
  Arpaia and Campoli nodal divisors, and inversion/positivity counters;
- two smooth manufactured topology defects and their cumulative sums;
- current minimum angle, minimum area ratio, generator-centroid offset;
- total mesh velocity and the regularisation correction isolated around the
  second loop of `set_vertex_velocities()`.

The latest source also records the quasi-Lagrangian velocity before
regularisation as a separate column.  The long runs below predate that final
column, but the subsequent short smoke run checked the updated 36-column CSV.

Four submitted jobs failed first for cluster/configuration reasons (missing
`liblapacke` in a non-RD FV build, an unavailable Slurm PMI interface, and then
missing parsed regularisation parameters in the no-regularisation parameter
file).  The Makefile and submission scripts were corrected without running a
build on the login node.  These failures occurred outside the diagnostic
algebra.  The short and long compute-node runs then completed.

### 13.2 Algebraic gate on the real rebuild

The short Gresho smoke run reached `t=0.05` in 137 global steps.  On the real
AREPO triangulations and periodic images it gave:

- maximum area-coverage error `4.9e-15`;
- maximum element area/mesh-flux identity error `6.2e-18`;
- zero pulled-back inversions, zero non-positive midpoint triangles, and zero
  non-positive Arpaia nodal divisors;
- 1265 removed and 1265 added edges.

Thus the Python common-geometry construction has survived its first direct C
translation and actual AREPO topology changes.  This is a geometry result, not
yet a free-stream test of the RD update.

### 13.3 Long Gresho regularisation on/off comparison

Both cases start from the same irregular `48 x 48` Gresho particle set and run
the actual FV problem to the same physical time `t=0.5`.

| quantity | regularisation on | regularisation off |
| --- | ---: | ---: |
| global steps | 1222 | 2404 |
| removed edges | 4525 | 4415 |
| removed edges per unit physical time | 9050 | 8830 |
| final `min(A_new)/mean(A_new)` | `9.47e-2` | `2.64e-3` |
| worst `min(A_new)/mean(A_new)` | `9.96e-3` | `7.54e-5` |
| final minimum angle | `0.3236` rad | `0.00372` rad |
| worst minimum angle | `0.0158` rad | `9.34e-5` rad |
| pulled-back inverted triangles | 0 | 4 |
| non-positive midpoint triangles | 0 | 3 |
| non-positive Arpaia nodal divisors | 0 | 0 |
| sum of absolute trigonometric topology defects | `1.01e-3` | `1.65e-3` |
| sum of absolute wave topology defects | `1.35e-3` | `1.76e-3` |

Coverage remains within `6.6e-15` and the element area identity within
`7.0e-18` in both cases.  The no-regularisation hazards occur at:

```
step 1700, t=0.328125:       2 pulled inversions, 1 midpoint failure
step 2201, t=0.450439453125: 2 pulled inversions, 2 midpoint failures
```

At both times the rebuilt new triangles are still positive.  The failure is in
the continuous space-time trajectory of the pulled-back new connectivity, not
in the Delaunay rebuild itself.  A positive summed Arpaia nodal divisor does
not rescue an individually inverted element.

### 13.4 Interpretation of regularisation and topology noise

The earlier expectation that regularisation should reduce the flip rate is
withdrawn.  In this run the two cases have essentially the same number of
flips per unit physical time.  Regularisation instead keeps the **point set and
the space-time elements healthy**.  Without it, sliver triangles shrink the
hydrodynamic timestep, nearly doubling the number of global steps, and finally
invalidate the linear pulled-back element trajectory.  This is compatible with
the fact that a Delaunay triangulation is optimal only relative to its given
point set; it cannot make a badly distributed point set quasi-uniform.

For both manufactured fields the signed cumulative topology defect is much
smaller than the sum of absolute increments.  A mean-drift test gives no
significant drift in either run (all available `t` statistics are below 1.11).
The result is compatible with weakly correlated/random-walk accumulation, but
one realisation is not evidence for a universal stochastic law.  The standing
diagnostic therefore remains the complete increment time series, its mean,
variance, lag correlation, signed sum and sum of absolute values.

### 13.5 What mesh velocity Stage 0 is actually testing

For ordinary pure hydrodynamics the present public AREPO path uses

```
sigma_i = v_i - (dt_i/(2 rho_i)) Grad(p)_i + v_reg_i,
```

with gravity already half-kicked into `P[i].Vel` when gravity is enabled and a
Lorentz acceleration added under MHD.  The pressure gradient is produced by
AREPO's Voronoi least-squares finite-volume gradient estimator.  Hence the
completed Stage 0 runs test the real current AREPO policy, including its
half-step estimate of the interval-average fluid velocity.

This does not make that finite-volume gradient part of the ALE-RD mathematics.
The ALE mesh velocity is arbitrary: conservation and DGCL require only that the
same `sigma_i` be used consistently in the point drift, pulled-back/midpoint
geometry and ALE residual.  The half-acceleration term improves the physical
trajectory from

```
x_new = x_old + dt v_old                         (first-order trajectory)
```

to

```
x_new = x_old + dt v_old + (dt^2/2) a_old        (second-order predictor),
```

but is not required for an admissible ALE update.  The regularisation drift
has a different purpose and direction, and can be exactly zero in already
round cells, so it does not replace the acceleration predictor.

There is also a semantic mismatch to resolve before the production RD path:
the FV least-squares estimator treats primitive data as Voronoi-cell averages
located at cell centroids, whereas RD stores nodal values at the Delaunay
generators.  The natural RD-native comparison is the lumped projection

```
grad(p)|_T = sum_(j in T) p_j grad(phi_j),
grad(p)_i^RD = (1/m_i) sum_(T contains i) (|T|/3) grad(p)|_T,
m_i = sum_(T contains i) |T|/3.
```

No choice between these predictors is needed to continue the geometry tests.
They should be retained as explicitly labelled experimental modes rather than
silently identifying the FV estimator with the RD spatial operator.

### 13.6 Prioritised test plan and handoff

The next tests are ordered by dependency.  Items 1--4 remain diagnostic-only
and can be performed before any ALE-RD fluid update.  Zhenyu intends to hand
this part to Claude first.

1. **Uniform flow plus uniform boost, highest priority.**  Use the same
   irregular periodic point set at boost zero and at one non-zero constant
   boost, each with regularisation off and on.  With regularisation off this is
   exact rigid translation: pressure acceleration, relative point motion,
   genuine flips and topology defect should vanish.  With regularisation on,
   the two boosted runs must have the same relative geometry, edge history and
   regularisation correction to round-off.  This isolates Galilean covariance
   and periodic-image bookkeeping from all fluid dynamics.

2. **Expose and compare the acceleration predictor.**  Extend the diagnostic
   decomposition to output separately `v_i`, the half-pressure acceleration
   correction, and `v_i^reg`.  Provide two controlled mesh-motion policies:

   ```
   sigma = v + v_reg
   sigma = v + (dt/2) a_pressure_FV + v_reg.
   ```

   Compare them first on Gresho, where the pressure acceleration is the
   centripetal correction that turns a tangent Euler drift into a second-order
   approximation to a circular trajectory.  Record trajectory/centroid
   offsets, mesh quality, timestep history, flips, inversions and topology
   defects.  Do not interpret either policy as a DGCL requirement.

3. **Smooth vortex boost matrix.**  Run Yee at boost 0 and 1, with
   regularisation on and off; repeat the most informative cases with the
   pressure predictor disabled.  This tests a smooth analytic accelerating
   flow and checks that adding a bulk velocity does not alter relative mesh
   geometry or the regularisation correction.  Gresho plus boost is the second
   vortex check; its unboosted regularisation pair is already complete.

4. **Long smooth-shear stress test.**  Run a smoothed KH/shear case with
   regularisation on and off.  Its purpose is not yet shock accuracy, but the
   onset of slivers, timestep collapse, pulled/midpoint inversion and possible
   coherent accumulation under persistent differential motion.

5. **First ALE-RD solver gate, only after the common geometry is connected.**
   Use a uniform conservative state under prescribed non-rigid mesh motion.
   Require static-mesh collapse, particle-wise free-stream preservation,
   element DGCL, global conservation, and agreement of the Arpaia midpoint and
   Campoli endpoint scalar-pair implementations to their expected algebraic
   difference.  Test N/lumped first, including its endpoint central geometric
   share.  Repeat on one rank and then multiple ranks before a non-uniform
   fluid problem.

6. **RD-native pressure predictor comparison.**  After item 5, add
   `grad(p)^RD` as a third labelled policy and compare it with no acceleration
   and AREPO FV-LSF acceleration on Yee and Gresho.  The acceptance criterion
   is solution and mesh convergence, not equality of the three trajectories.

7. **Physical RD tests last.**  Proceed through Yee plus boost, Gresho plus
   boost, then contact/Sod and finally shear.  Discontinuities are where the
   `O(h^4)` smooth flip argument no longer applies and where the pressure
   predictor may need limiting.  Hierarchical timesteps, refinement, 3-D and
   gravity remain later phases.

The immediate stop condition is therefore clear: Claude can complete items
1--4 without changing `residual_distribution_solver.c`.  An ALE-RD fluid test
should not be started until item 5 has a reviewed common-geometry interface and
a uniform-state/DGCL acceptance test.

## 14. 2026-08-10: audit of the extended Stage 0 campaign, and decision to advance the fluid prototype

- Reviewer: `Codex`, at Zhenyu's request after Claude's free-stream, nodal
  ledger, CFL and glass/random tests in section 10 above.
- Decision: Zhenyu proposes bringing the real ALE-RD fluid prototype forward,
  so that subsequent mesh-motion experiments measure their effect on the RD
  solution rather than geometry alone.  The review agrees, subject to the
  deliberately narrow vertical slice in section 14.4.
- No solver or diagnostic source is changed in this entry.  The unrelated
  uncommitted B-scheme diagnostic work in
  `residual_distribution_solver.c` must not be folded accidentally into the
  ALE implementation.
- This section supersedes the final sequencing sentence of section 13.6: the
  entire FV-only matrix in items 1--4 is no longer a prerequisite for beginning
  the uniform-state ALE-RD gate.

### 14.1 Stage 0 results accepted by the review

The following results survive code and output inspection and are sufficient to
close the question whether the common geometry can be evaluated on a real
AREPO rebuild:

1. The independent area and velocity expressions for
   `delta_T = (A_old+A_new)/2-A_mid` agree to approximately `7e-18` under real
   quasi-Lagrangian motion, regularisation and topology changes.
2. The rigid free-stream, regularisation-off run has no changed edge and keeps
   every quantity that must vanish at round-off.  This validates the Stage 0
   instrument and its periodic pulled-back construction.
3. The CFL sweep supports `delta_T = O(dt^2)`.  At fixed physical end time the
   observed flip rate, the largest nodal topology jump and the accumulated
   smooth-probe defect change little across the tested CFL range.  This is
   evidence that the latter quantities are primarily spatial/topological, not
   a time-quadrature error.
4. Regularisation keeps the actual point set and the pulled-back space-time
   triangles healthy.  It is inert on the relaxed `glass48` free stream, while
   the same option drives a large initial relaxation transient on `random48`.
   Delaunay optimality cannot repair a badly distributed generator set by
   itself.
5. `rd_ale_geometry_diagnostics.c`, its Configs and parameter files are now
   tracked in commit `24fb409`, so the immediate stale-artifact risk described
   before that commit no longer applies to this source.
6. The change in `build_case.sh` that requires MKL/LAPACKE only for a Config
   containing `RESIDUAL_DISTRIBUTION` is correct for the present source tree:
   the only LAPACKE calls are in `residual_distribution_solver.c`.

These are geometry and infrastructure results.  They do not establish
free-stream preservation, conservation or convergence of an ALE-RD fluid
update, because no such update exists yet.

### 14.2 Corrections and qualifications to Claude's section 10

The technical campaign is sound overall, but the following statements must be
corrected before its text is treated as a final report.

**The nodal ledger does not yet test the first moment.**  The C diagnostic
correctly constructs

```
dm_i = mhat_i^n - m_i^n
```

by particle ID and records `sum dm_i`, `sum |dm_i|`, `max |dm_i|` and the number
of touched nodes.  It does not compute

```
sum_i dm_i x_i
```

and it does not assemble changed patches or compare the touched-node set with
the changed edge/star set.  The comment at
`rd_ale_geometry_diagnostics.c:617` therefore overstates the implemented
checks.  What has been confirmed inside AREPO is the zeroth-moment sum and the
availability of every individual `dm_i`; the first-moment identity remains the
offline Python result.

**The accumulation language remains too strong.**  The data show no
statistically significant signed drift in the runs examined and are compatible
with weakly correlated or random-walk-like accumulation.  One realisation and
two principal spatial resolutions cannot establish a universal stochastic
model.  In particular, the statements in sections 9.3--9.4 that the
fixed-time accumulated defect has order `h^3.5` and that a random walk is
"the correct model" must be downgraded.  `O(h^4)` is the supported local
smooth-patch statement; the accumulated order requires a controlled
fixed-physical-time resolution ensemble on healthy meshes.

**Two numerical summaries are inaccurate.**  Directly summing the long Gresho
CSVs gives

```
regularisation on:  4525 removed edges / 0.5 = 9050 per unit time
regularisation off: 4415 removed edges / 0.5 = 8830 per unit time,
```

not 9043 and 8847.  The final minimum-area ratio improves by about `36x`, and
the worst value by about `132x`; the phrase "about a thousand times healthier
by minimum area" is not supported by the table.  The qualitative conclusion
is unchanged: regularisation prevents severe slivers and pulled-back
inversions without materially reducing the physical-time flip rate.

**The glass recommendation is problem dependent.**  A relaxed glass is the
right baseline for the present periodic, nearly uniform-resolution tests and
avoids measuring an artificial relaxation transient.  A general production
run with non-uniform target mass or resolution requires a generator set
relaxed against that target measure, not necessarily a uniform glass.

**The committed test description is not yet portable.**  The parameter files
contain absolute `/home/zwu/...` paths and depend on HDF5 initial conditions
that are neither tracked nor regenerated by a committed script.  The numerical
outputs can be audited on the current machine, but another checkout cannot
reproduce them from the commit alone.  Replace absolute paths and provide an IC
generator or a documented immutable IC checksum before calling the campaign a
reproducible test suite.

**The generic fingerprint hole remains.**  Tracking this particular new C file
fixed its fingerprint, but `build_case.sh` still hashes `git diff HEAD` and
ignores untracked files.  A future untracked source, Config include or generated
header can again be invisible.  The robust policy is to reject a build when a
relevant untracked file exists, or include such files in the fingerprint and
artifact manifest.

**The log needs an editorial pass.**  It currently contains two sections
numbered 10 with overlapping Stage 0 summaries and slightly different tables.
They are retained for development provenance here, but should later be merged
without erasing the chronology.

None of these corrections invalidates the element geometry or blocks the
restricted ALE-RD prototype.

### 14.3 Why the fluid prototype should now move forward

Further FV-only runs cannot answer the main remaining questions:

- whether topology quadrature defects actually enter density, momentum and
  energy at a measurable level;
- whether regularisation decreases solution error by maintaining good
  elements or increases it through additional mesh noise;
- whether moving LDA/F1 retains the static scheme's smooth-flow order;
- whether the complete RD update, rather than geometry alone, remains
  Galilean invariant;
- whether the AREPO FV pressure predictor in `sigma` has any measurable effect
  on an RD solution.

Those questions require a fluid update.  It is therefore inefficient to make
the full FV-only Yee/Gresho/KH and pressure-predictor matrix a gate.  The
pressure predictor is not part of the DGCL: `sigma` is arbitrary provided the
same displacement velocity enters the point drift, reconstructed geometry and
ALE residual.  The first prototype may retain AREPO's existing FV-LSF pressure
predictor and regularisation, and compare no-acceleration and RD-native
predictors only after the RD update runs.

### 14.4 Restricted ALE-RD vertical slice

Introduce one explicit experimental compile path, provisionally
`RD_ALE_EQUALSTEP`, with hard guards:

```
TWODIMS
periodic boundaries
FORCE_EQUAL_TIMESTEPS
one MPI rank
no refinement/derefinement
no hierarchical timesteps
no gravity or MHD
```

Do not implement it by merely removing the current
`VORONOI_STATIC_MESH` error.  Four static assumptions must be replaced:

1. `rd_accumulate_dual_area()` currently accumulates only the rebuilt new
   triangle area.
2. `rd_rk2_save_stage0()` currently reconstructs `U^n` by dividing the carried
   old `Q` by that newly accumulated area, which is the `O(1)` storage error
   identified in section 7.
3. `tri_normals_list` currently contains new-mesh normals and areas, and the
   same values enter both spatial stages and every F1/lumped temporal term.
4. The existing `Velvertex_avg` shift already supplies the ALE characteristic
   displacement in `K`, but it supplies only the geometrically
   non-conservative residual `phi_tilde`; it does not by itself supply the
   moving mass coefficients.

Build one production geometry object per owned post-rebuild element, sharing
the Stage 0 construction:

```
x_old, x_mid, x_new, sigma_i,
A_old, A_mid, A_new, delta_T,
midpoint normals,
pulled-old, modified-midpoint and new nodal masses.
```

The states entering this object are keyed by persistent particle IDs and use
the periodic image already resolved by `DP[].x`.  The stage-zero intensive
state must be taken from the carried nodal `U^n` (or equivalently obtained by an
explicit rebase), never by dividing unre-based old `Q` by a new divisor.

The recommended implementation order has two short vertical slices:

1. **Correctness slice: Arpaia midpoint N/lumped.**  It uses midpoint normals
   and element mass together with the modified midpoint nodal divisor.  It
   avoids the separate endpoint N geometric-source branch and gives the
   cleanest non-rigid uniform-state DGCL test.
2. **Research slice: LDA/F1 on the same common geometry.**  Add the midpoint
   Arpaia scalar pair and the endpoint/Campoli pair as labelled compile-time
   alternatives.  The endpoint divisor is the ordinary new median dual and
   maps naturally to the present `Q=mU` storage; its F1 coefficient is
   `(A_old+A_new)/2`.  The Arpaia coefficient is `A_mid` and its divisor is the
   modified midpoint dual.  Their difference `delta_T` remains a standing
   diagnostic.  Do not add B, shocks or hierarchy in this slice.

Every temporary stage accumulator must state which divisor it uses.  Before
the ordinary `update_primitive_variables()` call, `P.Mass`, momentum and energy
must once again represent the declared endpoint `Q`, and `DualArea` must be the
matching divisor.  Global conservation must be audited before and after any
rebase; preserving nodal `U` alone is not a substitute for that audit.

### 14.5 Revised experiment order

The new order is:

1. **Static collapse:** `sigma=0` must reproduce the existing static N result
   before topology or regularisation is used.
2. **Non-rigid uniform state:** use regularisation on an irregular periodic
   point set to obtain real deformation and flips while keeping the Euler state
   uniform.  Require particle-wise `U=U_0`, the scheme's declared global
   conserved totals, element DGCL, positive pulled/midpoint geometry and
   positive nodal divisor to round-off.
3. **Uniform boost pair:** repeat the successful uniform gate with a constant
   boost and compare by particle ID and relative geometry.
4. **Short Gresho on a relaxed mesh:** compare moving RD, static RD and AREPO FV
   using the same generators.  This is the first direct measurement of the
   effect of real regularisation and topology on the RD solution.
5. **Yee, boost 0 and 1:** perform a small resolution sequence before a large
   campaign.  This is the first order and Galilean-invariance gate for moving
   LDA/F1.
6. **Only then vary mesh policy:** compare
   `sigma=v+v_reg`, AREPO's FV-LSF half-acceleration predictor, and an
   RD-native pressure-gradient predictor.  The criterion is solution and mesh
   convergence, not identical trajectories.
7. **Discontinuities and long shear later:** contact/Sod, KH, B, MPI,
   hierarchy, refinement, 3-D and gravity stay outside the first vertical
   slice.

The practical change from section 13.6 is therefore limited but important:
stop expanding Stage 0 after reproducibility cleanup, connect the already
validated common geometry to a uniform-state ALE-RD update, and bring Gresho
and Yee forward immediately after that gate.  This exposes the actual
moving-mesh behaviour sooner without using complex fluid tests as a substitute
for DGCL validation.

---

## 15. 2026-08-10: the first moment inside AREPO, and the drift reconstruction verified

- Author: `Claude Code Opus 5`, closing items T1 and T2 agreed with Zhenyu after
  Codex's audit in section 14, and performing the editorial pass recorded in the
  note before section 11.
- Changes: `src/mesh/rd_ale_geometry_diagnostics.c` only. No solver source.

### 15.1 Codex's corrections, accepted and adjudicated

Section 14.2 is upheld on every numerical point, and two of its corrections are
of my errors:

- **The first moment was not implemented.** The comment claiming that "both
  moment identities are tested here" overstated what the code did. Corrected in
  15.2, both in the comment and in the code.
- **"About a thousand times healthier by minimum area" is wrong.** Recomputing:
  the final minimum-area ratio improves by **36x** and the worst value by
  **132x**. My figure came from dividing the regularised run's *final* value by
  the unregularised run's *worst* value, which is not a comparison. Codex's
  numbers are right; section 10.2's phrasing should be read as corrected here.
- **The flip rates were 9050 and 8830 per unit time**, not 9043 and 8847. Mine
  were computed from a rounded mean times the step count rather than by summing
  the column. Codex is right; the conclusion is unaffected.
- **The glass recommendation is problem dependent.** Accepted. A relaxed glass
  is right for these periodic near-uniform tests; a production run with a
  non-uniform target resolution needs generators relaxed against *that* measure.
- **Reproducibility and the general fingerprint hole.** Both accepted and open,
  carried as P3 and P4 in the plan agreed with Zhenyu.

One qualification remains. Section 14.2 asks that the claim "a random walk is
the correct model" be downgraded. The `h^3.5` accumulated order rests on two
resolutions and is only a two-point measurement. Over 400 steps of Lagrangian
motion the lag-1 autocorrelations of `D_n` were -0.024, -0.021, +0.000 and
-0.019. This is direct evidence of no lag-1 correlation, but it does not by
itself establish independent or identically distributed increments, absence
of higher-lag correlation, or stationarity. The supported wording is therefore
"no drift is detected and the increments are consistent with random-walk-like
accumulation". `O(h^4)` remains the local smooth-patch statement; a stochastic
model and accumulated spatial order require a fixed-physical-time resolution
ensemble on healthy meshes.

### 15.2 The first moment is now measured in AREPO

Added to the instrument: each snapshot node carries its primary position, and
the comparison reports `dm_first_moment_x`, `dm_first_moment_y` and
`max_pullback_position_error`.

The first moment is evaluated against the **stored** old primary positions,
which need no image resolution because they were recorded before the rebuild.
A flip patch that straddles the periodic boundary has its nodes on opposite
sides of the box, so its contribution is displaced by a lattice vector and the
sum then carries a term of order `boxsize * h^2`. The diagnostic is therefore
binary rather than continuous, and it is reported rather than asserted.

| | free stream, regularisation off | Gresho, regularisation on, CFL 0.3 |
| --- | ---: | ---: |
| steps | 1024 | 265 |
| edge flips, total | 0 | 1642 |
| `\|sum dm_i\|`, max | 2.9e-17 | 5.4e-17 |
| **`\|sum dm_i x_i\|`, median** | **4.9e-18** | **1.0e-17** |
| `\|sum dm_i x_i\|`, max | 2.6e-17 | 2.8e-4 |
| steps above 1e-12 | **0 of 1024** | **37 of 265** |

Of the 265 steps, 257 contain at least one changed edge. **On 220 of those 257
flip-containing steps the first-moment identity holds to round-off inside
AREPO.** The eight no-flip steps are also at round-off, giving 228 of 265 total.
The remaining 37 are consistent with the boundary-straddling artifact predicted
above: their magnitude, 2.8e-4, matches
`L h^2 = 1 x (1/48)^2 = 4.3e-4` to the expected order. Section 9.1's offline
result therefore now has an in-code counterpart, and Codex's correction is
answered rather than merely acknowledged.

Making the remaining 37 steps into a hard gate, or proving that each is a
boundary event, needs patch assembly with a coherent periodic image in C. That
is not done and is not on the critical path: the identity is confirmed offline
for cascades, and the primary-coordinate diagnostic is at round-off on 86 per
cent of the flip-containing AREPO steps.

### 15.3 The drift reconstruction is verified, not assumed

`x^n = x^{n+1} - dt * VelVertex` has been assumed since section 3.2(b) on the
grounds that `predict.c:383` is exactly linear. The new
`max_pullback_position_error` compares the reconstruction against the position
actually recorded at the previous synchronisation point, by particle ID:

```
free stream, regularisation off, 1024 steps : 1.110e-16
Gresho, regularisation on,        265 steps : 1.110e-16
```

**Round-off, including with regularisation active and topology changing.** The
identity on which the whole pulled-back construction rests is now measured
inside AREPO rather than argued from the source.

### 15.4 A side confirmation of the fingerprint fix

Rebuilding after this change produced artifact ids
`c742da4b77e5-e9b503aba2cb9994` and `c742da4b77e5-803c71ec9c938969`, different
from the previous build. Before commit `24fb409` placed the diagnostic source
under version control, an equivalent edit left the id unchanged (section 10.7).
The specific hole is closed; the general one described in 14.2 is not.

### 15.5 Where this leaves the fluid prototype

Zhenyu's decision to bring the ALE-RD fluid slice forward, and Codex's section
14 plan for it, are agreed. Of the prerequisites settled with Zhenyu, T1 and T2
are done here. The remainder, in risk order:

1. **P1, closed in `8f04faa`.** The B-scheme element-map diagnostic and its
   documentation have landed independently. The ALE slice now starts without
   an overlapping tracked edit in `residual_distribution_solver.c`.
2. **T3/T4, specified in section 16.** Freeze both the shared geometry object
   and the state/mass/rebase lifecycle before editing the solver. These are the
   actual implementation prerequisites.
3. **P3, closed in section 16.** The Stage-0 parameters use paths relative to
   their working directory and the three local IC identities are recorded.
4. **P4, closed in section 16.** The managed builder refuses relevant untracked
   source/build inputs before compilation and checks again before publication.

Three additions to section 14.5's experiment order:

- with identical element ordering, the `sigma = 0` geometry coefficients and
  element residual must be bit-identical to the current static expressions.
  The end-to-end particle-ID solution and conserved totals need only agree to
  round-off, because a rebuild may change triangle and summation order;
- the section 8.8 cross-check belongs in the first slice, but it has two
  distinct tolerances. Two assemblies using the same `U_h` interpolant must
  agree to round-off. The production Roe `Zhat_h` path versus an arithmetic-`U`
  geometric term has a real interpolation defect; record its magnitude and
  resolution scaling rather than treating it as a DGCL failure;
- section 10.5 measured the two candidate formulations' mass coefficients as
  differing by about one per cent at production CFL, so starting from the
  Arpaia midpoint pair alone is safe and the compile-time switch can wait.

## 16. 2026-08-10: final cleanup and frozen interface for the first ALE-RD slice

- Author: `Codex`, after reviewing Claude's section 15 additions at Zhenyu's
  request.
- Solver change: none. The Stage-0 terminal diagnostic, provenance tooling,
  portable parameter paths and implementation contract are cleaned here.

### 16.1 Corrections closed

The preceding section now distinguishes total steps from flip-containing
steps, treats the 37 large first moments as boundary-compatible rather than
proved boundary patches, and downgrades the stochastic language to what the
measured lag-1 correlations support. The terminal `mpi_printf` now has format
slots for all three quantities already written to the CSV.

The production residual cross-check also follows the Chapter 4 distinction:
same-interpolant assemblies are a round-off identity test; the Roe-`Zhat_h`
versus arithmetic-`U` path is a measured interpolation defect. Static collapse
is bitwise only at the element level under an identical traversal, and
round-off by particle ID for an end-to-end rebuild.

The Stage-0 parameter paths are relative to the parameter directory and
`ALE_STAGE0_ICS.sha256` records the three local HDF5 identities. The normal
`run_case.sh` path sets that directory as the run working directory. The ICs
remain local data rather than Git objects.

`build_case.sh` now refuses untracked inputs under `src/` and the root build
control files, both before compilation and before artifact publication. The
explicit Config is independently copied and hashed, so it may still be supplied
from another path. This closes the stale-source hole without rejecting local
ICs, plots or run output.

### 16.2 Frozen interface for the first Arpaia ALE-RD slice

The first implementation is deliberately restricted to
`RD_ALE_EQUALSTEP`: two dimensions, periodic boundaries, equal timesteps, one
MPI rank, and no refinement, gravity or MHD. It uses the post-rebuild Delaunay
connectivity throughout the step and does not retain triangle history across a
flip.

At the opening synchronization point, before any rebuilt area overwrites the
old divisor, save by persistent particle ID:

```
U_old[i], m_old[i], x_old_primary[i], sigma[i].
```

`U_old` is the intensive nodal state. It must never be reconstructed by
dividing an unre-based old `Q` by a new dual area. `sigma` is frozen for the
linear drift interval used by this slice.

After the AREPO rebuild, one common helper constructs every owned new-
connectivity element. Its production object contains:

```
vertex particle IDs and local indices,
x_old[3], x_mid[3], x_new[3], sigma[3],
A_old, A_mid, A_new, delta_T,
midpoint normals,
M_arpaia = A_mid,
D_arpaia = A_mid + (A_new - A_old)/2.
```

The periodic images come from the coherent `DP[]` triangle at the new time;
the old and midpoint images are pulled back with the same vertex velocity.
Both the Stage-0 diagnostic and the solver must call this helper rather than
copying its formulas. The nodal endpoint mass and modified Arpaia divisor are

```
m_new[i] = sum_{T contains i} A_new(T)/3,
m_bar[i] = sum_{T contains i} D_arpaia(T)/3.
```

The RK accumulator for this slice is explicitly an `m_bar` accumulator. It may
be represented either as direct increments

```
Delta U_i = -dt R_i / m_bar[i]
```

or as temporary `Q_bar = m_bar U`; it is not the physical endpoint `Q`.
Immediately after obtaining `U_new`, rebase the AREPO storage exactly once:

```
Q_endpoint[i] = m_new[i] U_new[i],     DualArea[i] = m_new[i].
```

Only this matched endpoint pair may enter `update_primitive_variables()`. The
conservation audit is not equality of the temporary and endpoint ledgers. It is
the declared ALE balance

```
sum_i (m_new[i] U_new[i] - m_old[i] U_old[i])
  + dt sum_T Phi_ALE(T) = 0,
```

with periodic boundary cancellation and the separately reported topology
quadrature defect. A uniform-state test additionally requires every particle's
`U_new` to equal `U_old` to round-off under non-rigid motion and real flips.

The first acceptance sequence is therefore fixed:

1. static element coefficients/residuals with `A_old=A_mid=A_new` and
   `sigma=0`;
2. non-rigid uniform state with regularisation and flips;
3. matched-`U_h` explicit-versus-rewritten residual identity;
4. production `Zhat_h`--versus--`U_h` defect measurement;
5. endpoint conservation before Gresho or Yee.

Patch assembly for the periodic first-moment diagnostic, Campoli, LDA/B, MPI
and hierarchical timesteps are not prerequisites for this first correctness
slice.

### 16.3 Validation

- `git diff --check`: pass.
- `bash -n build_case.sh`: pass.
- all three entries in `ALE_STAGE0_ICS.sha256`: pass.
- all tracked Stage-0 parameter files resolve an existing local IC from their
  parameter directory and contain no `/home/zwu` path.
- Stage-0 diagnostic build: pass, artifact
  `8f04faafa192-ebf4e30865122aec` (dirty-source validation build).
- B total-frozen element-map build: pass, artifact
  `8f04faafa192-8bfb2120260d48fb` (dirty-source validation build).
- negative provenance test: a temporary untracked file under `src/` is listed
  by name and refused with exit status 5; the probe file was then removed.

The validation builds deliberately used the local system LAPACKE allowance.
The Stage-0 binary does not link LAPACKE; the B binary does and is a compile
check only, not a compute-node campaign artifact.

## 17. 2026-08-10: the first fluid-coupled ALE-RD slice and its first blocking result

The deliberately restricted Arpaia midpoint/N slice described in Section 16
has now been connected to the real AREPO mesh-motion and RD update path. This
is the first test in this project in which mesh motion changes the coefficients
used by the fluid residual rather than being observed by a geometry-only
diagnostic.

### 17.1 Implemented lifecycle

The build switch is `RD_ALE_EQUALSTEP`. The present prototype requires 2D
periodic geometry, equal timesteps, one MPI rank, `RD_RK2_TOTAL_RESIDUAL`, and
the N distribution; unsupported combinations fail at compile or run time. It
does not yet claim support for hierarchical timesteps, refinement, MHD,
gravity, passive scalars or other RD distributions.

After the AREPO mesh rebuild, the production solver and the Stage-0 diagnostic
call the same geometry helper. On the new connectivity it pulls every vertex
back from `x_new` with the frozen mesh velocity, constructs old, midpoint and
new element geometry, and supplies

```
A_old, A_mid, A_new,
delta_T = (A_old + A_new)/2 - A_mid,
D_arpaia = A_mid + (A_new - A_old)/2,
midpoint normals.
```

Before replacing the old dual-area divisor, the solver saves
`U_old = Q_old/m_old`. It assembles

```
m_new[i] = sum_T A_new(T)/3,
m_bar[i] = sum_T D_arpaia(T)/3,
```

rebases the temporary accumulator to `Q_bar=m_bar U_old`, and runs the existing
two-stage N total-residual update with midpoint normals and the midpoint lumped
mass `A_mid/3`. It then recovers `U_new=Q_bar/m_bar` and performs the endpoint
storage rebase `Q_new=m_new U_new`, `DualArea=m_new`. Thus the temporary Arpaia
ledger and the physical endpoint ledger are explicitly distinguished.

Every step checks positive old/midpoint/new triangle area, positive `m_bar`,
periodic area coverage, and the exact two-dimensional area identity. A
test-only zero-mesh-velocity switch exercises precisely the moving-mesh call
path while requiring its coefficients to collapse bitwise to the static ones.

### 17.2 Compute-node campaign

All cases below reached `TimeMax=0.02` without an inverted triangle,
non-positive modified divisor or fluid positivity failure.

| case | steps / flips | principal result |
| --- | ---: | --- |
| uniform, forced `sigma=0` | 64 / 0 | static coefficients bitwise identical at all 4610 triangles per step; `max |Delta U|=4.44e-16`; endpoint conservation exactly zero |
| uniform, rigid Lagrangian translation | 64 / 0 | `max |Delta U|=1.33e-15`; endpoint conservation `1.33e-15` |
| uniform, regularisation on | 33 / 788 | real deformation and flips; `max |Delta U|=1.33e-15`; endpoint conservation `8.44e-15`; final state differs from the initial state only at round-off |
| Gresho, forced `sigma=0` | 128 / 0 | static moving-path control is stable; global changes `(mass,px,py,E)=(0,6.94e-18,0,-1.78e-15)` |
| Gresho, regularisation on | 70 / 1036 | stable with flips on every step, but endpoint conservation is **not** at round-off |

For all moving cases the element area identity is at round-off; the largest
observed defect was about `5.9e-18`. The static RD configuration also compiles
from the same source, so sharing the geometry object has not broken the
non-ALE build.

Representative Slurm jobs were `10382438` (stationary uniform), `10382439`
(regularised uniform), `10382446` (stationary Gresho), `10382447`
(regularised Gresho with ledger split), and `10382448` (static RD compile
regression). Reproducible binaries are retained under `build_artifacts/`, in
particular

```
ale-rd-n-zero-mesh/ffeca740c8bf-c7ec2a1b78562bf6/Arepo
ale-rd-n-regularized/ffeca740c8bf-df121ee0b4664487/Arepo
rd-static-regression/ffeca740c8bf-681c66c492fd885a/Arepo
```

The corresponding IC files remain local run inputs and are covered by the
tracked `ALE_STAGE0_ICS.sha256` manifest; run output is not part of this
commit.

### 17.3 The regularised Gresho conservation defect

The final regularised Gresho snapshot changed its global endpoint ledger by

```
Delta(mass, px, py, E)
  = (-2.5059849e-6, -2.0924436e-5, -4.7642059e-5, +6.5222761e-9).
```

The largest single-step endpoint defect was `4.99312e-5`. This is much larger
than round-off and therefore the Gresho case is a diagnostic smoke run, not an
accepted ALE-RD result.

To localise the defect, the code now prints three distinct changes:

```
temporary_change = sum Q_bar(after update) - sum Q_old(physical),
rebase_change    = sum Q_endpoint - sum Q_bar(after update),
endpoint_change  = sum Q_endpoint - sum Q_old(physical).
```

Over this run, the component-wise maxima were

| ledger change | mass | px | py | energy |
| --- | ---: | ---: | ---: | ---: |
| temporary | `1.263453e-6` | `2.084930e-5` | `4.993151e-5` | `4.419537e-5` |
| rebase | `3.111423e-10` | `9.990617e-9` | `5.823788e-9` | `5.451558e-8` |
| endpoint | `1.263379e-6` | `2.085005e-5` | `4.993120e-5` | `4.424252e-5` |

Therefore the final `m_bar -> m_new` storage rebase is not the leading source.
The defect is already present in the modified-mass update. The uniform-state
result shows that the discrete geometric conservation law itself is working;
the non-uniform conservation identity is the unresolved part.

The leading hypothesis is the interpolation distinction already recorded in
Chapter 4: the production spatial residual uses Roe `Zhat_h`, whereas the
geometric/mass cancellation is written for an arithmetic nodal `U_h`.
Arpaia's same-interpolant algebra does not by itself establish exact endpoint
conservation for that mixed choice. This is a diagnosis to test, not yet a
conclusion. Since the regularised Gresho run flipped on every step, these data
also cannot yet separate continuous-deformation error from a topology-change
contribution.

### 17.4 Revised next acceptance gates

The implementation is far enough advanced to expose the real fluid-level
question, but not far enough for long Gresho/Yee accuracy campaigns. The next
tests are now:

1. assemble the explicit and rewritten ALE residual with the same arithmetic
   `U_h` interpolation and require a round-off identity element by element;
2. replace only that interpolation by the production Roe `Zhat_h` path and
   measure the predicted `Z`--`U` defect separately;
3. construct a non-rigid but no-flip interval to distinguish continuous mesh
   deformation from topology change;
4. make endpoint conservation a hard acceptance gate before comparing Gresho,
   boosted Gresho, Yee or mesh-velocity policies;
5. only after these gates, extend beyond the current one-rank/equal-step/N
   prototype.

The first ALE-RD slice has therefore passed its static-collapse, geometry and
free-stream gates. Its first non-uniform moving-fluid run has done the useful
thing a prototype should do: identify a conservation question before a larger
engineering integration hides it.

---

## 18. 2026-08-11: the ALE-RD conservation defect resolved into two mechanisms

- Author: `Claude Code Opus 5`, auditing Codex's first fluid slice (section 17)
  at Zhenyu's request.
- Changes: `src/hydro/residual_distribution_solver.c` gains one experimental
  compile flag, `RD_ALE_SPLIT_MESH_VELOCITY`. Codex's slice is otherwise
  untouched.
- Result: the defect of section 17.3 is **two** superposed mechanisms. Codex's
  hypothesis is correct and now fixed; it is however the **subdominant** term.
  The dominant one is the median-dual topology defect predicted in section 7.

### 18.1 Why the endpoint ledger should balance, and where it does not

Write the endpoint change as

```
dQ = sum_i m_new,i U_i^{n+1} - sum_i m_old,i U_i^n
   = sum_i m_new,i dU_i + sum_i (m_new - m_old)_i U_i^n.
```

The second term is exactly computable. With the 2-D area identity
`A_new - A_old = dt A_mid div sigma_h`,

```
sum_i (m_new - m_old)_i U_i^n = sum_T (A_new - A_old) Ubar_T = dt * integral U_h div sigma_h.   (1)
```

The mesh-velocity part of the flux, using the shifted `K` and the state the
residual actually multiplies, is

```
sum_T phi_tilde^T |mesh part = - integral sigma_h . grad (that state).                          (2)
```

If (1) and (2) use the same interpolant their sum is
`dt * integral div(U_h sigma_h) = 0` on a periodic domain, and the endpoint
ledger is exactly conserved. **Conservation therefore hinges on the two terms
sharing one interpolant.**

### 18.2 The code fact

`Phi[k]` is assembled as `Kmatrix[...][kfull] * U_hat[p][j]`, and `U_hat` is
**not** the conservative nodal state. It is the parameter-vector linearisation

```
U_hat[.][j] = (dU/dZ)|_{Z_avg} Z_j,
```

which differs from `U_fluid[j]` at second order in `Z_j - Z_avg`. That
linearisation is exactly what makes the physical part
`sum_j K_j U_hat_j = boundary integral of F` hold, so it must stay. But the
mesh-velocity part rides on the same `U_hat` because the shift is fused into
the eigenvalues, `Lambda = u.n +- c - sigma.n`, so (2) uses `U_hat` while (1)
uses `U`. **Codex's hypothesis in 17.3 is confirmed at the level of the source,
not merely inferred from the numbers.** An earlier guess of mine that the
residual multiplies `U_fluid` was wrong.

### 18.3 The timestep sweep says the leading term is not this

A smooth periodic non-uniform initial condition was built for this test,
`IC_smooth_random48` and `IC_smooth_glass48`: `rho = 1 + 0.3 sin(kx) cos(ky)`,
uniform pressure, `v = (0.6 + 0.2 sin(ky), 0.4 + 0.2 sin(kx))`. Gresho is a poor
probe here because its azimuthal velocity is piecewise linear, so `grad^2 U` is
singular at `r = 0.2` and `r = 0.4`, which is exactly where the interpolation
mechanism is largest.

Regularised, `TimeMax = 0.02`, `n = 48`:

| CFL | steps | flips | `d(mass)` | `d(px)` |
| ---: | ---: | ---: | ---: | ---: |
| 0.05 | 184 | 797 | -1.551e-5 | -1.032e-5 |
| 0.10 | 92 | 797 | -1.544e-5 | -1.012e-5 |
| 0.20 | 46 | 798 | -1.635e-5 | -1.077e-5 |
| 0.40 | 24 | 787 | -1.198e-5 | -0.933e-5 |

**Over an eightfold range of `dt` the accumulated defect is unchanged**, so it is
not a time-quadrature error. The flip count per unit time is also unchanged,
797/797/798/787, which is the section 10.5 result reappearing. The defect tracks
the flips, not the timestep.

### 18.4 The discriminating experiment: a flip-free non-uniform run

Regularisation off, smooth state, `TimeMax = 0.005`, `CourantFac = 0.1`:

| initial condition | steps | flips | `d(mass)` | `d(px)` | `d(E)` |
| --- | ---: | ---: | ---: | ---: | ---: |
| glass | 16 | **0** | -3.05e-10 | -3.93e-8 | -2.36e-8 |
| random | 32 | **12** | -1.13e-6 | -2.33e-6 | -9.04e-7 |

Per step the mass defect is 1.9e-11 with no flips against 3.5e-8 with flips, a
factor of about 1800. **The dominant mechanism is topological.** It is the
defect derived in section 7 and measured there and in sections 9 and 10 as the
proxy `sum_i dm_i U_i`; this is the first time it appears in the fluid
solution rather than in a geometry diagnostic. Its `dt` independence follows
from the `dt` independence of the flip rate, which is why 18.3 looks the way it
does.

A smaller non-topological defect survives at zero flips, visibly in momentum and
energy. That is the interpolation term.

### 18.5 The split, and the measurement that closes 17.3

`RD_ALE_SPLIT_MESH_VELOCITY` assembles the mesh-velocity part of the element
residual on the conservative nodal state while the physical part keeps `U_hat`:

```
correction = - (1/2) sum_j |n_j| (sigma_bar . n_hat_j) (U_fluid[j] - U_hat[.][j]),
```

added to the element total `Phi` and distributed to the three vertices with
weight `1/3`, the row sum of the N mass matrix. It is conservative by
construction and vanishes identically for a uniform state, so no free-stream or
DGCL property is disturbed.

| case | flips | `d(mass)` | `d(px)` | `d(py)` | `d(E)` |
| --- | ---: | ---: | ---: | ---: | ---: |
| glass, original | 0 | -3.05e-10 | -3.93e-8 | -5.46e-10 | -2.36e-8 |
| **glass, split** | 0 | **-3.74e-13** | **-2.27e-13** | **-1.50e-13** | **-1.04e-12** |
| random, original | 12 | -1.13e-6 | -2.33e-6 | -4.00e-7 | -9.04e-7 |
| random, split | 12 | -1.13e-6 | -2.24e-6 | -4.01e-7 | -8.50e-7 |

**With no flips the split takes the defect to round-off**, improving momentum by
a factor of 170000 and mass by 800. **With flips it changes essentially
nothing**, as it must, because the topology defect is a different mechanism.

The two error sources are therefore cleanly separated, and section 17.3's
question is answered: the interpolation mismatch is real, is exactly Codex's
diagnosis, and is now fixed; what remains is the topology defect that section 7
predicted.

### 18.6 A note on the assertion suite

The first version of the split placed its application loop inside the enclosing
component loop and reused `k`, terminating that loop after the first component.
The existing `rd_check_conservation` assertion A2 caught it on the first
timestep with a printout naming the failing component and the exact residual
imbalance. That is worth recording as evidence that the static-era assertion
suite is still doing useful work on the ALE path.

### 18.7 What this changes about the plan

- Section 17.4's gates 1 and 2 address the interpolation term. It is now
  measured and fixed, so those gates can be reduced to a regression check that
  the flip-free case stays at round-off.
- **Gate 3, the no-flip interval, is the one that mattered** and is done here.
  Its outcome promotes the topology defect from a predicted geometry effect to
  the leading fluid-level error.
- **Endpoint conservation cannot become a hard round-off gate while flips
  occur**, because the topology defect is `O(h^4)` per patch and not zero. The
  honest gate is: round-off on any flip-free interval, and a reported,
  resolution-converging defect otherwise. Section 9.3 measured that convergence
  offline as roughly `h^3.5`; it should now be measured in the fluid.
- The split should not be adopted as default on one test case. It needs the
  uniform-state, static-collapse and free-stream gates re-run, all of which it
  should pass trivially since the correction vanishes for uniform states.
- The topology question returns to the options of section 7: accept a
  converging defect, or implement the conservative topology operator whose
  antisymmetric-flux form is given there.

---

## 19. 2026-08-11: split regression gates, and the topology defect's convergence in the fluid

- Author: `Claude Code Opus 5`. No source change; these are runs of the section
  18 code.

### 19.1 The three regression gates for `RD_ALE_SPLIT_MESH_VELOCITY`

Section 18.7 required the split to be re-gated before it could be considered for
adoption, since it had been validated on one test case.

**A. Static collapse, `sigma = 0`.** Split against unsplit, same initial
condition, compared particle by particle after sorting by ID:

```
max|dMass| = 0        max|dVelocity| = 0        max|dInternalEnergy| = 0
bitwise identical     : true
```

Exactly as the construction requires: with `sigma_bar = 0` the correction is
identically zero, so the static path is untouched to the last bit.

**B. Uniform state with regularisation**, 788 edge flips over the run:

```
max|dv| = 5.77e-15    max|du_therm| = 7.77e-15
d(mass, px, py, E) = (0, 0, 0, +4.44e-16)
```

Mass and both momentum components are conserved **exactly**, energy to one unit
in the last place. Free-stream preservation survives 788 flips. This is the
expected behaviour: the correction is proportional to
`sum_j (sigma_bar . n_j)(U_j - U_hat_j)`, and for a uniform state the bracket is
a constant vector while `sum_j n_j = 0`, so the correction vanishes without any
appeal to `U_hat = U` — which is false even for a uniform state, since `U_hat`
is the derivative of a quadratic map and carries a factor of two.

**C. Rigid free stream** is covered by the section 18.5 glass row, which is the
same configuration with zero flips and reached round-off.

The split therefore passes every gate that the unsplit path passed, and takes
the flip-free non-uniform case to round-off, which the unsplit path did not.

> **Corrected in section 20.** The two-point "orders" in 19.2 are not a
> convergence measurement, because the defect is a fluctuating quantity whose
> sign changes between the two runs, and the "energy floor" of 19.3 does not
> exist: a four-seed ensemble in section 20.4 shows energy converging at the
> same order as everything else. Read 19.2 and 19.3 only as the raw
> single-realisation data.

### 19.2 The topology defect converges rapidly in `h`

With the split enabled the interpolation term is removed, so what remains in a
flipping run is the topology defect alone. A matched pair of jittered lattices
was generated at `n = 48` and `n = 96` with the same relative jitter and the same
smooth state, run with regularisation to `t = 0.01`. `MaxSizeTimestep` binds
before the Courant condition in both, so **both runs take 16 steps at the same
`dt`** and the comparison isolates `h`.

| `n` | steps | flips | `d(mass)` | `d(px)` | `d(E)` |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 48 | 16 | 55 | -8.798e-7 | -3.192e-7 | 5.728e-8 |
| 96 | 16 | 220 | +3.711e-8 | +2.233e-8 | 5.317e-8 |

| | mass | px | py | energy |
| --- | ---: | ---: | ---: | ---: |
| ratio 48/96 | 23.7 | 14.3 | 78.8 | 1.08 |
| implied order | **4.57** | **3.84** | 6.30 | **0.11** |

Mass and momentum converge at roughly fourth order while the flip count
quadruples, which is consistent with the `O(h^4)`-per-patch estimate of
section 7.3 and with the `h^3.5` accumulated behaviour measured offline in
section 9.3. **The topology defect is controllable by spatial resolution**, and
at `n = 96` it is already at the `4e-8` level over this interval.

### 19.3 An unexplained energy floor

Energy does **not** converge: `5.73e-8` at `n = 48` against `5.32e-8` at
`n = 96`, a ratio of 1.08. Mass falls by 24 over the same refinement, so at
`n = 96` the energy defect exceeds the mass defect and is evidently a different,
non-topological, non-converging contribution at about `5e-8` absolute, or `3e-8`
relative to the total energy of about 1.8.

This is not round-off, which would be `1e-16`, and it is not the interpolation
term, which the split removes and which gate B shows reaching `4e-16` on a
uniform state. There is no energy floor active: `MinEgySpec` is zero in these
parameter files. It is recorded here as an open item rather than explained.
Candidates worth eliminating in order: the `Q_bar -> Q_new` endpoint rebase
acting differently on the energy component, the primitive recovery in
`update_primitive_variables`, and any energy-specific handling in the RK2
corrector's positivity path. A cheap first discriminator is to repeat the pair
with `sigma = 0` forced, where the topology and geometry terms both vanish: if
the `5e-8` energy defect survives there, it is not an ALE effect at all.

### 19.4 Status

The section 17 slice, with the section 18 split, now has:

- bitwise static collapse;
- exact free-stream preservation through hundreds of flips;
- round-off endpoint conservation on flip-free non-uniform intervals;
- a topology defect that converges at roughly fourth order in `h`;
- one unexplained non-converging energy defect at `5e-8`.

The first four are what the phase needed in order to move from geometry to
accuracy. The fifth should be closed before any convergence campaign, because a
non-converging energy error would contaminate an order measurement long before
it becomes visible in the solution.

---

## 20. 2026-08-11: the defect is entirely ALE-topological, and it converges at fourth order

- Author: `Claude Code Opus 5`. No source change; runs of the section 18 code.
- This section **corrects two conclusions of section 19**.

### 20.1 The `sigma = 0` discriminator: the defect is ALE-specific

Section 19.3 proposed forcing `sigma = 0` to separate an ALE cause from an
unrelated one. Same initial conditions, same times, same binary but with
`RD_ALE_TEST_ZERO_MESH_VELOCITY`:

| case | flips | `d(mass)` | `d(px)` | `d(py)` | `d(E)` |
| --- | ---: | ---: | ---: | ---: | ---: |
| moving, n=48 | 55 | -8.798e-7 | -3.192e-7 | -2.864e-7 | +5.728e-8 |
| moving, n=96 | 220 | +3.711e-8 | +2.233e-8 | -3.633e-9 | +5.317e-8 |
| **`sigma=0`, n=48** | **0** | **0.000e+0** | -1.110e-16 | +5.551e-17 | -2.220e-16 |
| **`sigma=0`, n=96** | **0** | +2.220e-16 | 0.000e+0 | +5.551e-17 | 0.000e+0 |

With the mesh frozen every component is conserved to round-off or exactly.
**The entire defect, energy included, is an ALE effect**; nothing in the RD
solver, the primitive recovery or the RK2 positivity path contributes.

### 20.2 With the split on, the defect is independent of the timestep

Fixed initial condition and end time, varying only `MaxSizeTimestep`:

| `dt_max` | steps | flips | `d(mass)` | `d(px)` | `d(E)` |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1.0e-3 | 16 | 55 | -8.798e-7 | -3.192e-7 | +5.728e-8 |
| 5.0e-4 | 32 | 55 | -8.697e-7 | -3.185e-7 | +5.775e-8 |
| 2.5e-4 | 64 | 55 | -8.704e-7 | -3.188e-7 | +5.776e-8 |

The flip count is **identical** at 55, so this is a controlled comparison of the
same physical evolution at three timesteps, and every component agrees to
within one per cent. The defect is therefore not a time-quadrature error, which
rules out the `O(dt^2)`-per-step stage-mismatch term as well as the
interpolation term the split already removed. What remains is topology.

### 20.3 Correction: section 19's orders were not a convergence measurement

Section 19.2 reported orders of 4.57 and 3.84 for mass and momentum from a
single pair of runs, and section 19.3 reported a non-converging "energy floor"
from the same pair. Both readings are wrong, for one reason.

Extending the pair in time exposes it:

| `TimeMax` | steps | flips | `d(mass)` | `d(px)` | `d(E)` |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.01 | 16 | 55 | -8.798e-7 | -3.192e-7 | +5.728e-8 |
| 0.02 | 32 | 103 | -2.566e-6 | -1.294e-6 | +4.727e-8 |
| 0.04 | 64 | 198 | -2.102e-6 | -5.687e-7 | +1.374e-6 |

The defect is not monotone in time. Looking back at 19.2 with that in mind, the
mass and `px` defects **change sign** between `n = 48` and `n = 96`. A quantity
that changes sign under refinement is a sample of a fluctuating variable, not a
converging error, so a ratio of two such samples is not an order. The energy
"floor" was the same artifact seen from the other side: two samples that
happened to be close.

Codex's section 14.2 warned about exactly this — "one realisation and two
principal spatial resolutions cannot establish a universal stochastic model" —
and section 19 repeated the mistake it was warning about. The correct
instrument is an ensemble.

### 20.4 The ensemble: all four components converge at fourth order

Four jitter seeds at each resolution, identical smooth state, identical times,
regularisation on, split on:

| `n` | flips per seed | | RMS `d(mass)` | RMS `d(px)` | RMS `d(py)` | RMS `d(E)` |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 48 | 47, 58, 47, 46 | | 2.105e-6 | 1.158e-6 | 1.110e-6 | 6.077e-7 |
| 96 | 221, 216, 204, 246 | | 1.203e-7 | 6.294e-8 | 7.223e-8 | 3.373e-8 |
| | | **ratio** | **17.50** | **18.40** | **15.36** | **18.02** |
| | | **order** | **4.13** | **4.20** | **3.94** | **4.17** |

Within each ensemble the individual samples change sign, which is the direct
confirmation that a two-point comparison could not have worked. The RMS,
however, is clean:

**All four conserved components converge at order 4.0 to 4.2, energy
included.** That matches the `O(h^4)`-per-patch estimate of section 7.3, now
measured in the fluid rather than in a geometry proxy, and it disposes of the
energy anomaly of 19.3, which does not exist.

### 20.5 Status, and what is now established

The ALE-RD slice of section 17, with the mesh-velocity split of section 18,
has:

- bitwise collapse to the static scheme at `sigma = 0`, and round-off
  conservation there in every component;
- exact free-stream preservation through hundreds of flips;
- round-off endpoint conservation on flip-free non-uniform intervals;
- a single remaining conservation defect which is entirely topological, is
  independent of the timestep, and converges at **fourth order in `h`**.

That last point is the one the phase needed. The topology defect predicted in
section 7, measured offline in sections 9 and 10, and first seen in the fluid in
section 18, is now characterised: it is real, it is the only remaining
conservation error, and **it is controlled by spatial resolution at fourth
order**, so it cannot masquerade as a second-order solution error in a
convergence campaign.

Two consequences for the plan:

- **Endpoint conservation should be gated as: round-off on any flip-free
  interval, and fourth-order convergent otherwise**, reported per run. A
  round-off gate in the presence of flips would be unsatisfiable and would
  wrongly block the phase.
- The conservative topology operator of section 7 is **not** required for the
  accuracy programme. It remains the principled option if a future application
  needs machine-precision conservation with a moving, reconnecting mesh.

The methodological lesson is recorded deliberately: two-point ratios of a
fluctuating quantity produced a plausible but meaningless order in section 19,
and only an ensemble settled it. Any future order claim about a
topology-driven quantity in this project should use one.

---

## 21. 2026-08-11: LDA on the moving mesh, and the pseudo-inverse switch measured

- Author: `Claude Code Opus 5`.
- Source change: one guard in `residual_distribution_solver.c`. Nothing else.

### 21.1 LDA needed one line

The `RD_ALE_EQUALSTEP` guard required `N_SCHEME`. Opening it to `LDA_SCHEME`
was the only code change, for two reasons that were not obvious until the
source was read:

- **The mass coefficient was already correct.** Line 1123 assigns
  `set->normals[slot] = geometry->normals[RD_ALE_MID]`, replacing the whole
  structure, so `tri_normals_list[i].area` is `A_mid` everywhere it is used,
  including the F1 temporal target. The Arpaia midpoint mass therefore reaches
  LDA without any further change, which is what section 8.4 predicted would be
  a one-line edit and turns out to be a zero-line one.
- **The mesh-velocity split needed nothing either.** The section 18 correction
  is added to `Phi[k]`, and `rhs[k][0] = Phi[k]` is exactly what the LDA solve
  consumes, so LDA distributes the correction with `beta_i` automatically. That
  is the correct weight: the row sum of `m_ij^{LDA} = (|T|/3) beta_i` is
  `beta_i |T|`. The explicit `1/3` loop written for N is inside the
  `N_SCHEME || B_SCHEME` block and compiles out under LDA, which is also
  correct, since `1/3` is the row sum of N's lumped mass.

B remains excluded, now by an explicit message rather than by omission.

### 21.2 The LDA gates

| gate | flips | `d(mass, px, py, E)` |
| --- | ---: | --- |
| `sigma = 0` | 0 | `-2.2e-16, -1.1e-16, +5.6e-17, -4.4e-16` |
| uniform state, regularisation on | **609** | `0, 0, 0, +4.4e-16` |

The zero-mesh run also exercises the internal bitwise-collapse assertion at
`residual_distribution_solver.c:1161`, which passed. On the uniform state,
`max|dv| = 4.4e-16` and `max|du| = 1.8e-15`: **LDA preserves the free stream
exactly through 609 connectivity changes.** Both gates match what N achieved in
sections 17 and 19, so moving to a second-order distribution has cost nothing
in the geometric properties.

### 21.3 The pseudo-inverse switch: cost measured, benefit absent

Section 3.5 decided that the ALE path should require `RD_ALWAYS_PSEUDOINVERSE`,
because at `sigma = u` the advective eigenvalues vanish, `S^-` becomes
singular, and the pivot-ratio branch at `RD_LU_FALLBACK_PIVOT_RATIO = 1e-12`
would then be decided by round-off and hence by the domain decomposition. That
decision was never implemented. It is now measured instead.

**Cost**, `n = 96`, `t = 0.04`, identical 64 steps and 829 flips in both runs:

| solver | wall | CPU from `cpu.txt` |
| --- | ---: | ---: |
| LU with pivot fallback | 16 s | **15.40 s** |
| always pseudo-inverse | 30 s | **28.76 s** |

**The pseudo-inverse costs 87 per cent more.**

**Benefit**, same pair, and a second pair on a glass:

| case | conservation, LU | conservation, pseudo-inverse | `max\|dVel\|` between them |
| --- | --- | --- | ---: |
| n=96 jittered, 829 flips | `+3.3273e-7, +3.6508e-7, +2.0977e-9, +5.5714e-7` | **identical to all digits** | 2.4e-13 |
| n=48 glass, 2 flips | `+3.8517e-7, +3.1164e-7, +1.1550e-7, +1.5427e-7` | **identical to all digits** | 7.4e-15 |

The two solvers agree to `8e-14` relative in mass and give bitwise-identical
conserved totals. There is no benefit to buy.

**Why the section 3.4 concern does not materialise.** The solver reports
`min_pivot_ratio` per step. In these runs it is `5e-7` to `1.4e-6`, **five to
six orders above the `1e-12` fallback threshold**, so the SVD path never fires
at all. That holds even on the glass, where the geometry diagnostic reports
`regularisation_active_fraction = 0` from the first step to the last and
`reg_rms = 0`, that is, where the centroid drift is switched off entirely and
`sigma` is the fluid velocity.

Section 3.4 measured the degeneracy on **prescribed** pure-Lagrangian motion of
an analytic velocity field, with `sigma` set exactly equal to `u`. AREPO's
`VelVertex` is never exactly `u`: even with the centroid regularisation
inactive it carries the finite-volume half-acceleration predictor, which keeps
`w = |u - sigma|/c` away from zero. The offline model that produced the concern
does not describe the code's actual mesh velocity.

**Revised recommendation, superseding section 3.5.** Do not require
`RD_ALWAYS_PSEUDOINVERSE` on the ALE path. It doubles the solver cost and
changes nothing measurable. Keep it as what its own comment says it is, a
reference path for confirming the fast path, and re-check `min_pivot_ratio` on
any new flow class. Two caveats stand:

- the degeneracy is a property of **stagnation**, `u = sigma = 0`, not of the
  Lagrangian limit as such. Section 3.5 recorded that the Sod at `t = 0` runs
  100 per cent on the SVD path because `u = 0` in both states. A shock tube or
  any flow with a stagnation region will still exercise it, and should be
  re-measured when it is reached;
- the rank-invariance half of the argument cannot be tested at all yet, because
  the ALE prototype is guarded to one MPI rank. It must be revisited when the
  prototype goes multi-rank, and `min_pivot_ratio` is the quantity to watch.

### 21.4 Status and next

LDA now has, on the moving mesh: bitwise static collapse, exact free-stream
preservation through 609 flips, and the same conservation behaviour as N. With
section 20's result that the remaining defect is purely topological and
fourth-order convergent, **the accuracy programme is unblocked**: the moving
Yee and Gresho convergence campaign, which is the minimum defensible thesis
deliverable of section 4, can now be run with a second-order scheme.

The one item that should precede it is reproducibility, carried as P3 since
section 15.5 and now overdue: the parameter files contain absolute
`/home/zwu/...` paths, and the initial conditions are untracked HDF5 with no
committed generator. Roughly thirty parameter files and eight initial
conditions have accumulated over sections 18 to 21. The campaign about to be
run is the one whose numbers will be cited, so it should be the first one a
fresh checkout can reproduce.

---

## 22. 2026-08-11: what `sigma` actually is, and the reproducibility cleanup

### 22.1 The three components of the mesh velocity

`set_vertex_velocities.c` builds `VelVertex` in three stages:

```
VelVertex = P[i].Vel                          fluid velocity                (:83)
          + 0.5 * dt * (-grad p / rho)        half-step acceleration    (:100-114)
          + regularisation drift              centroid and face angle   (:150-250)
```

`SphP[i].Grad.dpress` is AREPO's finite-volume least-squares gradient, computed
by `calculate_gradients()` at `run.c:214`, immediately before
`set_vertex_velocities()` at `run.c:220`. The half-step acceleration is the
Pakmor et al. (2016) device; under MHD it also picks up the Lorentz term.

Three observations.

**It does not threaten the DGCL.** `sigma` is arbitrary provided the same
displacement velocity enters the point drift, the reconstructed geometry and the
ALE residual, and it does: `predict.c:383` drifts with `VelVertex` and the
geometry helper reconstructs from the same field.

**It is, however, doing unnoticed protective work.** Section 21.3 found
`min_pivot_ratio` never approaching the fallback threshold, even on a glass
where the geometry diagnostic reports the centroid regularisation completely
inactive. The reason is this term: it keeps `w = |u - sigma| / c` away from
zero, so `S^-` never becomes the near-singular matrix that section 3.4 measured
on prescribed pure-Lagrangian motion. **Replacing `sigma` by a pure Lagrangian
velocity would move the solver back into the regime section 3.4 warned about.**
That coupling between the mesh-velocity policy and the upwind matrices' rank was
not previously noticed, and it should be checked whenever the policy changes —
which section 14.5 item 6 plans to do.

Codex's observation that RD could build its own pressure gradient stands: the
natural RD object is the `P^1` element gradient
`grad p_h = sum_j p_j n_j / (2|T|)` on the Delaunay element, rather than the
finite-volume least-squares gradient on the Voronoi cell. That is a mesh-policy
comparison for section 14.5 item 6, not a correctness question.

**A correction to section 10.** `rd_ale_geometry_velocity_begin()` is called
after the acceleration loop, so `RdAleQuasiLagrangianRms` already includes
`u + (dt/2) a` and only `RdAleRegularisation*` isolates the regularisation. The
section 10 description of the bracketing is otherwise accurate, and this is
exactly why the glass runs show zero regularisation activity yet a non-zero
mesh velocity.

### 22.2 Reproducibility, carried as P3 since section 15.5

Done, as a cleanup before the accuracy campaign rather than after it.

**Initial conditions.** `examples/gresho_2d/create_mmrd_ics.py` regenerates
every initial condition the moving-mesh campaign used, and writes
`MMRD_ICS.sha256`. The self-contained families, the `smoothjit` resolution pair
and the eight `ens` members, are built from fixed seeds; the `freestream` and
`smooth` families reuse an existing Gresho point set and overwrite only the
fluid state, so a comparison against the Gresho runs varies the state and not
the generators. Running it reproduced the four spot-checked initial conditions
**bit for bit** against the files the campaign actually used, so sections 18 to
21 are now reproducible from the repository. `--verify` checksums what is on
disk.

**Parameter files.** Fifty-one moving-mesh parameter files had an output path
inside the working tree. They now point at the results location below. The three
remaining absolute `/home/zwu/...` paths are in `param_StaticMesh.txt`,
`param_RD.txt` and `param_MM.txt`, which predate this phase and are left alone.

**Run output.** Fifty-two `output_*` directories, 384 MB, and 303 batch logs
have been moved out of the repository to

```
/home/zwu/Hydro_data_analysis/Data_MMRD_debug/
```

with a `README.md` recording that nothing there is tracked, nothing there is an
input, and each directory is reproducible from its like-named parameter file,
the generator above and the immutable artifact named in its `provenance-*`
directory. Batch logs are under `_slurm_logs/`.

P4, the general build-fingerprint hole for untracked sources, remains open and
is now the only outstanding item from section 14.2.

---

## 23. 2026-08-11: Galilean invariance — the first result the moving mesh was built for

- Author: `Claude Code Opus 5`, at Zhenyu's request. No source change.
- Figure: `Hydro_data_analysis/Data_MMRD_debug/gresho_galilean_boost.png`.

### 23.1 The test

The Gresho vortex of `IC_gresho_v0_random48` has peak `v_phi = 1.0` at
`r = 0.2` and sound speed about 2.9. Adding a uniform `v_x = 3` is a Galilean
boost of three times the vortex's own peak velocity, bulk Mach 1.0, generated
by `create_mmrd_ics.py` so the boosted and unboosted initial conditions share
their generators exactly. Four runs to `t = 1`, `n = 48`, LDA, CFL 0.3:
static mesh and moving mesh, each at boost 0 and boost 3. The parameter files
are identical apart from the two mesh-regularisation entries, which a
`VORONOI_STATIC_MESH` build refuses to read, and the statistics output
interval.

Profiles are compared after removing the bulk translation and the advected
vortex centre, against the exact `v_phi(r)`.

### 23.2 Result

| case | `L1` against exact | scatter, `0.15 < r < 0.25` |
| --- | ---: | ---: |
| static, boost 0 | 0.01200 | 0.03653 |
| **static, boost 3** | **0.16965** | **0.09176** |
| moving, boost 0 | 0.00848 | 0.03120 |
| **moving, boost 3** | **0.00858** | **0.03189** |

**Boosting degrades the static mesh by a factor of 14 in `L1`, and the moving
mesh by 1.2 per cent.** The boosted moving-mesh result is twenty times more
accurate than the boosted static one. The figure shows why: at boost 3 the
static-mesh vortex has been smeared from a peak of 1.0 down to about 0.4 with
scatter across the whole profile, while the moving-mesh profile at boost 3 is
visually indistinguishable from its own boost-0 panel.

A secondary result worth keeping: **the moving mesh is already better
unboosted**, `L1` 0.00848 against 0.01200, a thirty per cent improvement with
no boost at all.

### 23.3 What "invariant" does and does not mean here

The moving-mesh solution is not bitwise invariant: comparing the two runs
particle by particle gives `mean |v_phi(3) - v_phi(0)| = 0.037`, against 0.169
for the static pair. Exact invariance is not expected and would be the wrong
thing to test for. The generators follow different trajectories in the two
runs, the regularisation therefore acts differently, and the Delaunay
connectivity differs. What is invariant is the **accuracy** of the solution,
which is the physically meaningful statement and the one the table makes:
`L1` is unchanged to 1.2 per cent while the static scheme loses an order of
magnitude.

### 23.4 Caveats before this goes in the thesis

- One resolution, one boost, one final time. A boost sequence, say 0, 1, 3, 10,
  and a resolution pair would make the claim quantitative rather than
  illustrative.
- The `L1` for the static boosted case is dominated by a genuine physical
  failure, not by scatter alone: the vortex has lost amplitude. Reporting both
  `L1` and the peak `v_phi` would separate diffusion from noise.
- Both runs use the same LDA distribution and the same regularisation policy
  where it applies, so the comparison isolates the mesh motion, but it does not
  isolate the mesh-velocity policy of section 22.1. The
  `sigma = v + v_reg` against alternative predictors comparison of section 14.5
  item 6 is still outstanding.

Nothing here depends on the topology defect of sections 18 to 20: at `L1` of
`8.5e-3` the fourth-order-convergent conservation error of `1e-7` is five
orders below the solution error and cannot be influencing this result.

### 23.5 Status

This is the first result in the moving-mesh phase that is a physics result
rather than a verification result, and it is the one the phase existed to
produce. Section 4's minimum defensible thesis deliverable was joint `(dx, dt)`
convergence on the moving Yee and Gresho; this is the complementary half, and
arguably the more persuasive one, because it is the property a static mesh
cannot have at any resolution.

---

## 24. 2026-08-11: Arpaia against Campoli, verified inside the fluid solver

- Author: `Claude Code Opus 5`. New compile switch `RD_ALE_CAMPOLI_MASS`.
- This closes the comparison proposed in section 14.4 and derived in
  section 8.7, and it is done before the boost sequence because the
  mathematical form should be settled before accuracy numbers are produced
  against it.

### 24.1 What was implemented

Section 8.7 showed the two published forms are one scheme, related by adding

```
delta_T = (A_old + A_new)/2 - A_mid = (dt^2/8) (sigma_1 - sigma_0) x (sigma_2 - sigma_0)
```

to **both** the element mass coefficient and the nodal divisor:

| | element mass | nodal divisor |
| --- | --- | --- |
| Arpaia et al. (2015), Prop. 4.1 | `A_mid` | `sum_T [A_mid + (A_new-A_old)/2]/3` |
| Campoli et al. (2017), sect. 2.2 | `(A_old+A_new)/2` | `sum_T A_new/3`, the plain new median dual |

The prototype implemented only the first. Adding the second needed the element
`area` to be decoupled from the element `normals`, because both forms evaluate
the flux on `T^{n+1/2}` and differ only in the mass. That decoupling is safe:
auditing every use of `tri_normals_list[i].area` shows it feeds only the lumped
and F1 temporal mass and is never the `|T|` of a gradient reconstruction. The
change is about twenty lines behind `RD_ALE_CAMPOLI_MASS`.

### 24.2 Three verifications

**1. At `sigma = 0` the two forms must be the same scheme**, because `delta_T`
is proportional to differences of the vertex velocities and vanishes for
uniform `sigma`. Measured, LDA, same initial condition:

```
max|dMass| = 0    max|dVelocity| = 0    max|dInternalEnergy| = 0
bitwise identical : true
```

**2. Both must preserve a uniform state.** With regularisation active:

```
Arpaia : d(mass, px, py, E) = 0, 0, 0, +4.441e-16
Campoli: d(mass, px, py, E) = 0, 0, 0, +4.441e-16
```

Identical, and exact in the first three components.

**3. On a non-uniform moving flow the two must differ by `O(delta_T)`, hence by
`O(dt^2)`.** Same initial condition, three timesteps:

| `dt_max` | `max\|dVelocity\|` between the forms | `max\|dMass\|` | ratio per halving |
| ---: | ---: | ---: | ---: |
| 1.0e-3 | 2.2154e-10 | 1.8749e-13 | |
| 5.0e-4 | 5.3235e-11 | 4.2510e-14 | **4.16** |
| 2.5e-4 | 1.3051e-11 | 1.0164e-14 | **4.08** |

**The difference falls by a factor of four per halving of the timestep**, which
is the `dt^2` of the closed form. Section 8.7's algebra is therefore confirmed
numerically through the complete fluid solver, not only in the geometry
diagnostic of section 10.5.

### 24.3 The forms are closer than `delta_T` alone suggests

Section 10.5 measured `max delta_T/|T|` at about `1e-2` at production CFL, yet
the two schemes' solutions here differ by `2e-10` in velocity, eight orders
smaller. The reason is structural and worth recording: `delta_T` is added to
the mass coefficient **and** to the divisor, and the nodal update balances one
against the other, so the leading contribution cancels. What survives scales as
`delta_T` still, hence the clean `dt^2`, but with a very small prefactor.

**The choice of form is therefore numerically immaterial at any timestep of
practical interest**, which is the strongest possible version of section 8.7's
conclusion.

### 24.4 Recommendation

Keep **Arpaia as the default**. It is the form with a published second-order,
conservation and DGCL analysis attached to it, and the prototype has been gated
on it throughout sections 17 to 23. Keep `RD_ALE_CAMPOLI_MASS` as a verification
path, in the same role `RD_ALWAYS_PSEUDOINVERSE` now occupies after
section 21.3: a reference implementation used to confirm the production one, not
a production alternative.

One asymmetry favours Campoli and should be remembered if the Arpaia divisor
ever misbehaves: its divisor is the plain new median dual and is positive
whenever the mesh is, whereas the Arpaia modified divisor can in principle go
non-positive under strong compression, which is the caveat Arpaia et al. state
themselves. Sections 10.5 and 21 measured that it never fires, up to CFL 3, but
if it ever does, the Campoli divisor is the immediate fallback and now exists.

The mathematical form of the moving-mesh scheme is, with this, settled. The
boost sequence and resolution study of section 23.4 can proceed against a form
that will not be revisited.

---

## 25. 2026-08-11: the quantitative Galilean study, and the boost limit it found

- Author: `Claude Code Opus 5`. New compile switch `RD_DIFFERENCE_RESIDUAL`.
- Section 23 was one boost at one resolution. This is the boost sequence and
  resolution study it asked for, run against the form settled in section 24.
- Initial conditions: `create_mmrd_ics.py` gained a self-contained Gresho
  generator, so every member of the boost sequence shares its generator lattice
  at a given resolution and a comparison across boosts varies only the frame.

### 25.1 The boost sequence

Gresho, LDA, `t = 1`, `n = 48`, CFL 0.3. Peak `v_phi` is reported alongside
`L1` because section 23.4 asked for diffusion and noise to be separated:

| boost | static `L1` | static peak | moving `L1` | moving peak | `L1` ratio |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.00752 | 0.9463 | 0.00784 | 0.9340 | 1.0 |
| 1 | 0.05768 | 0.8052 | **0.00771** | **0.9330** | 7.5 |
| 3 | 0.16400 | 0.4568 | **0.00785** | **0.9366** | **20.9** |
| 10 | 0.20263 | 0.3620 | *fails, see 25.4* | | |

**The moving-mesh error is flat: 0.00784, 0.00771, 0.00785 across boosts 0 to 3,
a spread of 1.8 per cent.** The peak is equally flat, 0.934 to 0.937. The static
mesh degrades monotonically by a factor of 22 in `L1`, and the peak collapses
from 0.95 to 0.46: **the static failure mode is diffusion, not noise**, which is
what reporting the peak was meant to establish.

### 25.2 It is also cheaper, for the same reason

Steps to `t = 1` at fixed CFL:

| | boost 0 | boost 1 | boost 3 | boost 10 |
| --- | ---: | ---: | ---: | ---: |
| static, `n=48` | 2049 | 2049 | 4097 | 8193 |
| **moving, `n=48`** | **2049** | **2049** | **2049** | — |
| static, `n=96` | 4097 | | >5505, unfinished | |
| **moving, `n=96`** | **4097** | | **4097** | |

A static mesh has its timestep set by `|v| + c` in the lab frame, so boosting
throttles it; a moving mesh sees `|v - sigma| + c` and is unaffected. **The
moving-mesh step count is identical across boosts at both resolutions.** At
boost 3 and `n = 48` the moving mesh is therefore twenty-one times more accurate
**and** twice as cheap; the static `n = 96` boost-3 run did not finish in the
standard job allocation while its moving counterpart did.

### 25.3 Resolution, and the invariance of the order itself

| case | `n=48` `L1` | `n=96` `L1` | order |
| --- | ---: | ---: | ---: |
| static, boost 0 | 0.00752 | 0.00281 | 1.42 |
| **static, boost 3** | 0.16400 | 0.12428 | **0.40** |
| moving, boost 0 | 0.00784 | 0.00258 | **1.60** |
| **moving, boost 3** | 0.00785 | 0.00258 | **1.60** |

Two statements, and the second is the stronger.

**The convergence order is itself Galilean invariant on a moving mesh**: boost 3
reproduces boost 0 to four digits at both resolutions. An order is a property of
the scheme rather than of one run, so this is a stronger claim than the `L1`
table alone.

**Under boost the static mesh does not merely lose accuracy, it loses
convergence.** Its order falls from 1.42 to 0.40, and refining from `n=48` to
`n=96` buys a factor of 1.3 where the unboosted case buys 2.7. The boosted
static error is dominated by advection error that resolution does not remove at
the scheme's own rate. **That is the property a static mesh cannot recover at
any resolution**, and it is the sharpest form of the case for moving mesh.

The order is 1.4 to 1.6 rather than 2. That is expected and not an ALE effect:
the Gresho velocity profile is only `C^0`, with kinks at `r = 0.2` and
`r = 0.4`, and the static LDA campaign of volume 1 reached 1.879 on the smooth
Yee vortex for the same reason inverted. Yee is the right problem for an order
claim; Gresho is the right problem for an invariance claim.

### 25.4 Boost 10 on a moving mesh: a real limit, and what it is not

At boost 10 the moving-mesh run fails on the first step, on the existing
conservation assertion:

```
RD assertion A2: raw sum_i phi_i != phi^T within round-off
defect = 3.01e-10   tolerance = 3.41e-11   roundoff_scale = 37.54   |phi^T|max = 4.69e-4
```

The static boost-10 run passes cleanly. The diagnosis:

- `min_pivot_ratio` on the moving mesh degrades systematically with boost:
  **6.2e-6 at boost 0, 5.1e-8 at boost 1, 2.3e-9 at boost 3**, against
  **3.8e-4** for static boost 10. On a moving mesh `sigma` is approximately `u`,
  so the two advective eigenvalues `u.n - sigma.n` vanish and `S^-` is nearly
  rank deficient; on a static mesh they are `O(|v|)` and it is well conditioned.
- Meanwhile the entries of `K` grow like the square of the bulk velocity through
  `velx_c = velx_avg / c`, while the residual stays the size of the physical
  imbalance. At boost 10 the intermediate terms are `O(37)` and the answer is
  `O(5e-4)`: five orders of cancellation.

**This is section 3.4's concern finally materialising.** Section 21.3 withdrew
the requirement for `RD_ALWAYS_PSEUDOINVERSE` on the evidence that
`min_pivot_ratio` never approached the threshold — but that evidence was
collected **at boost 0 only**, and does not extend. The withdrawal stands for a
different reason than the one given: **the pseudo-inverse does not fix boost 10
either.** It was tried and fails identically, because the loss is in the
near-singular round trip `S^- (S^-)^+ phi`, which a minimum-norm solve cannot
recover.

`RD_DIFFERENCE_RESIDUAL` was added and tested on the same hypothesis. Since
`sum_j K_j = 0`, the element residual is unchanged by subtracting the element
mean before multiplying, which removes the common `O(b)` part in one exact
subtraction instead of in the accumulation. It is better conditioned and it
passes boosts 0 and 3, **but it does not fix boost 10 either**, which localises
the remaining loss to the LDA solve rather than to the residual assembly. The
switch is kept, off by default, since it is harmless and the diagnosis is worth
preserving in code.

What this is **not**: a failure of the ALE geometry, of the DGCL, or of the
conservation of the scheme. The defect is `6e-7` relative to the residual, and
the run fails only because assertion A2 is a strict round-off gate written for
the static regime. Whether to relax it on the ALE path with a documented,
conditioning-aware tolerance, or to record boost 3 as the validated range, is a
decision for Zhenyu; relaxing a conservation assertion is not something to do
silently.

### 25.5 Status

The claim of section 23 is now quantitative: **the moving mesh holds `L1`, the
peak amplitude, the convergence order and the timestep constant under boosts up
to three times the vortex's own peak velocity, where a static mesh loses a
factor of 22 in `L1`, half its peak amplitude and half its timestep.** The
validated boost range is 0 to 3; boost 10 is a known limit with an understood
mechanism.

Remaining from section 23.4: the mesh-velocity policy comparison of
section 14.5 item 6 is still outstanding, and Yee rather than Gresho is the
right vehicle for an order claim.

---

## 26. 2026-08-11: the boost-10 failure is conditioning, and a separate real defect in the timestep

- Author: `Claude Code Opus 5`, answering Zhenyu's question of whether section
  25.4 is a near-singular matrix or a CFL problem. It is the first; but the
  question exposed a genuine, independent defect in the second.

### 26.1 Boost 10 is conditioning, not CFL

Four independent arguments, the last decisive:

1. **Assertion A2 contains no timestep.** It compares `Phi = sum_j K_j Uhat_j`
   against `sum_i phi_i = sum_i (-K_i^+)(S^-)^{-1} Phi = S^-(S^-)^{-1}Phi`.
   Both sides are evaluated inside one residual assembly at one instant. No
   `dt` appears anywhere in the identity.
2. **The static boost-10 run has a stricter CFL and passes.** It needs 8193
   steps against the moving mesh's 2049, so its timestep is four times smaller,
   and it is clean.
3. **`min_pivot_ratio` degrades monotonically with boost on a moving mesh** —
   6.2e-6, 5.1e-8, 2.3e-9 at boosts 0, 1, 3 — while static boost 10 sits at
   3.8e-4. That is a property of `S^-`, not of `dt`.
4. **A hundredfold smaller timestep does not fix it.** Re-run at
   `MaxSizeTimestep = 1e-5` and `CourantFac = 0.01`:

   ```
   defect = 1.30e-9   tolerance = 4.12e-11     still fails
   ```

   The defect is if anything larger, which is element-to-element noise; the
   conditioning is unchanged.

The mechanism is the one section 25.4 described: on a moving mesh `sigma` is
approximately `u`, the two advective eigenvalues `u.n - sigma.n` vanish and
`S^-` is nearly rank deficient, while the entries of `K` grow like the square of
the bulk velocity through `velx_c = velx_avg/c`. The inversion of a
near-singular matrix whose entries carry five orders of cancellation is what
loses the precision.

### 26.2 The timestep criterion is nevertheless wrong for RD

Zhenyu's question was well aimed even though the answer is no, because looking
at `get_timestep_hydro` in `timestep.c:392` shows the moving-mesh criterion is
not the RD one:

```
csnd = c
#if defined(VORONOI_STATIC_MESH)
  csnd += |v|                     /* lab-frame speed, static mesh only */
#endif
dt = CourantFac * get_cell_radius(p) / csnd
```

Two gaps for the ALE-RD path.

**The advective term is dropped entirely on the moving path.** AREPO adds `|v|`
only under `VORONOI_STATIC_MESH`; on a moving mesh it assumes the quasi-
Lagrangian frame makes the advective speed negligible and uses `dt ~ R/c`. That
is AREPO's finite-volume assumption. The quantity that should appear is
`|v - sigma|`, and section 22.1 established that `sigma` is not `v`: it carries
the half-step acceleration and the regularisation drift. Measured on the moving
Gresho runs, `regularisation_velocity_rms` is 0.0318 on average and 0.0626 at
worst, **identical at boost 0 and boost 3** as a frame-independent quantity must
be, against a sound speed of about 2.9. **The omitted term is therefore about
one per cent of `c` on this problem**, so the criterion is accurate here by
accident of the mesh-velocity policy rather than by construction.

**The length scale is the wrong one.** `get_cell_radius` is the Voronoi cell
radius. The RD stability condition of Arpaia et al. equation (85) is

```
dt = CFL * min_i |S_i| / sum_{K in D_i} alpha^K,      alpha^K = max_j |k_j|
```

which uses the median-dual control area, and on a moving mesh the modified
midpoint area `|Sbar_i^{n+1/2}|` that section 24 settled. It also uses the
upwind parameters `k_j` themselves, which the solver already computes as its
eigenvalues, rather than a separately estimated sound speed.

**So the RD path has been running on a finite-volume timestep criterion
throughout**, including in volume 1's validated static campaign. That was safe
there because `dt ~ R/(c+|v|)` is strictly more conservative than the RD
condition in the static case. On the moving path it is no longer obviously
conservative, because the advective term is simply absent.

### 26.3 What to do

Not urgent, but it should be closed before the mesh-velocity policy comparison
of section 14.5 item 6, because that comparison **changes exactly the quantity
the criterion silently assumes to be zero**. A non-Lagrangian `sigma`, or
dropping the pressure predictor, would make `|v - sigma|` large while the
timestep criterion continued to ignore it.

The natural fix is cheap: the solver already forms `k_j` per element, so
`alpha^K = max_j |k_j|` can be accumulated during the residual sweep and
exported as a per-node stability limit, giving the Arpaia criterion directly. It
should be added as a **diagnostic first** — report `dt_RD / dt_AREPO` per step —
so the size of the discrepancy is known before anything is allowed to change the
timestep a validated campaign was run with.

### 26.4 On assertion A2 and the boost range

Since the failure is conditioning rather than a scheme defect, and the defect is
`6e-7` relative to the residual, there are two honest options and the choice is
Zhenyu's:

- record boost 3 as the validated range and boost 10 as a known limit, which is
  what section 25 does; or
- give assertion A2 a conditioning-aware tolerance on the ALE path, scaled by
  the measured `min_pivot_ratio` rather than by a fixed multiple of the
  round-off scale.

The second is defensible — the assertion's fixed `4096 * eps * scale` was
calibrated for a static regime where `S^-` is well conditioned — but relaxing a
conservation assertion is not something to do without an explicit decision.

## 27. 2026-08-11: boost 10 is recovered by direct element co-moving algebra; RD CFL is now an experimental limiter

This section supersedes two claims in section 26.2 and closes the immediate
boost-10 diagnosis.  All new paths remain compile-time experiments and are
off in `Template-Config.sh`.

### 27.1 Corrections to section 26.2

Section 26.2 overlooked the active `TREE_BASED_TIMESTEPS` path.  In the moving
case, `timestep_treebased.c` initialises

```
CurrentMaxTiStep = R / (c + |v - sigma|)
```

and propagates non-local signal restrictions; `get_timestep_hydro()` then
takes the minimum of its local `R/c` estimate and `CurrentMaxTiStep`.  Thus the
relative advective speed was **not absent**.  The genuine mismatch was the
finite-volume/Voronoi length scale versus the RD element-star bound.  The
statement that the static FV condition is always more conservative than the RD
condition was also too strong; even a regular equilateral example reverses the
ordering.  Previous successful static campaigns remain empirical validation,
not a general inequality between the two criteria.

### 27.2 A condition number, not the LU pivot proxy

`RD_ALE_CONDITION_DIAGNOSTIC` now evaluates the actual singular values,
numerical rank and normwise backward error of the failing LDA system.  On the
first boost-10 step (triangle 1096 in the CFL-limited run):

| quantity | laboratory conservative variables | element co-moving variables |
|---|---:|---:|
| singular values | `[7.886, 3.039e-2, 9.663e-3, 1.699e-16]` | `[4.477e-2, 3.241e-2, 1.225e-2, 2.203e-14]` |
| `cond_2(S^-)` | `4.64e16` | `2.03e12` |
| normalised backward error | `6.25e-8` | `2.08e-23` |
| A2 defect | `3.01e-10` | `5.42e-20` in-frame; `1.08e-19` after mapping back |
| A2 tolerance | `3.41e-11` | same laboratory audit scale |

The first attempt formed `G S G^{-1}` from the laboratory matrix.  It improved
the solve but retained an A2 defect of order `1e-10`--`1e-11`, because it asked
floating-point arithmetic to cancel the large boosted entries after they had
already been assembled.  Directly rebuilding `K_i^+`, `K_i^-` and `S^-` from

```
u' = u - b_T,       sigma' = sigma - b_T,       b_T = mean_T(sigma)
```

removed that defect.  The similarity-transformed and directly built matrices
differed by `5.97e-14` relative on the failing element, already enough to spoil
the nearly singular identity.  This is why forcing DGELSD on the laboratory
matrix did not help: the SVD was solving the poorly represented coordinates it
was given.

The remaining `cond_2 ~ 2e12` is real near-degeneracy from `u approximately
sigma`; the coordinate change does not pretend otherwise.  DGELSD handles its
consistent right-hand side with a tiny backward error.  A2 was **not relaxed**.

### 27.3 Experimental element co-moving LDA/F1 path

`RD_LDA_COMOVING_FRAME` implements the following element-local change of
conservative coordinates:

```
U' = G(b_T) U
G = [[1, 0, 0, 0],
     [-bx, 1, 0, 0],
     [-by, 0, 1, 0],
     [|b|^2/2, -bx, -by, 1]] .
```

The operator, Roe-state spatial residual and F1 temporal right-hand side are
assembled in the primed frame; LDA solves and distributes there; each completed
nodal residual is transformed once by `G^{-1}` before entering AREPO's
laboratory `Q` ledger.  It is not a different flux.  The compile-time guard
currently restricts it to the equal-step, two-pass LDA/F1 ALE prototype; N, B,
the hierarchy and the coherent-beta/rate-consistent experiments are excluded
until separately derived.

The important negative control was retaining the laboratory assembly of
`Phi^T` and transforming it only afterward.  That version ran boost 10, but at
`t=0.02` still differed from the de-boosted boost-0 solution by `8.12e-5` in
density L1 and `1.02e-4` in pressure L1.  Once `Phi^T` was also assembled
directly in the element frame, the same ID-matched comparison became:

| field after undoing the boost/translation | L1 | Linf |
|---|---:|---:|
| generator coordinates | `1.18e-16` | `1.44e-15` |
| velocity | `6.30e-15` | `4.89e-14` |
| density | `1.13e-14` | `4.91e-14` |
| pressure | `3.44e-14` | `1.54e-13` |
| internal energy | `1.05e-13` | `5.06e-13` |
| stored mass | `5.21e-18` | `2.67e-17` |
| output Voronoi volume | `7.59e-18` | `6.78e-17` |

Both boost 0 and boost 10 completed to `t=0.02` with every assertion active.
Adding `RD_DIFFERENCE_RESIDUAL` changed none of these figures materially: once
the complete residual is assembled in the small-velocity frame, subtracting a
common Roe state is no longer needed for boost conditioning.  It remains an
independent round-off experiment, not a prerequisite of the co-moving path.

One diagnostic is not bitwise boost invariant even though the solution is:
on the first step the boost-0/10 runs reported 1759/1698 rank-deficient F1
fallbacks, and different counts of exactly singular LU pivots.  These are
borderline rank decisions after subtracting two nearly equal velocities.  They
were dynamically invisible here because the paired fields still agree at
round-off, but the branch should be monitored on non-uniform and discontinuous
tests rather than declared harmless in general.

This is a short `n=48` Gresho gate, not yet a production validation.  The next
required tests are the previous `t=1` boost ladder, resolution comparison,
Campoli-versus-Arpaia comparison in the same coordinates, and eventually the
Yee, Sod, KH/RT and Sedov cases.

### 27.4 RD CFL diagnostic and limiter

The Arpaia-style scalar used here is

```
dt_i = CFL * m_i / sum_{T contains i} alpha_T,
alpha_T = max_{j,q} 0.5 * |n_j| * |lambda_jq| .
```

The first non-invasive measurement gave

```
selected AREPO dt       = 6.25e-4
realised midpoint RD dt = 3.8284255e-4
```

so the existing step was 1.63 times the proposed RD bound.  This is not the
cause of the boost-10 A2 failure (A2 is a same-element algebraic identity and
smaller timesteps had already failed), but it is a separate mathematical gap.

`RD_ALE_CFL_TIMESTEP` now runs after `tree_based_timesteps()` and before time-bin
quantisation.  It accumulates the current-mesh endpoint median mass and the
element spectral radii, then takes the minimum with AREPO's already propagated
tree bound through `CurrentMaxTiStep`.  On the `n=48` Gresho runs:

```
current-mesh RD candidate = 3.8284255e-4
quantised accepted dt     = 3.1250000e-4
realised midpoint bound   = 3.8284255e-4 initially
```

The accepted step therefore has a factor `1.225` margin.  Through `t=0.02`,
the current-mesh predictor and realised midpoint bound agreed to about `2e-7`
relative on this mildly deforming mesh.  The implementation deliberately
combines the RD and tree/FV restrictions; it does not delete the non-local
AREPO safeguard.

There is one unresolved mathematical detail: the Arpaia midpoint mass depends
on the future geometry and hence on the timestep being selected.  The current
endpoint mass is an explicit predictor, not a proof of the implicit midpoint
bound on arbitrary severe deformation.  The realised post-drift diagnostic is
therefore retained.  A production version should either establish a safe
geometric estimate or iterate/clip when the realised bound is smaller.

### 27.5 Reproducibility

- condition diagnostic build: job `10383632`, artifact
  `build_artifacts/ale-lda-boostdiag-direct/05ea49c2fd28-9fae11c9217d8f3f/Arepo`;
- direct co-moving residual build without the difference-residual switch: job
  `10383680`, artifact
  `build_artifacts/ale-lda-comoving-directphi-nodiff/05ea49c2fd28-c7d0207c0f1d2e2f/Arepo`;
- short boost-0/10 runs: jobs `10383681` and `10383682`;
- ID-matched analysis: `examples/gresho_2d/analyze_galilean_pair.py`;
- all builds used MKL on Slurm compute nodes and immutable build provenance.


## 28. 2026-08-12: the `U-Uhat` audit changes the boost-10 interpretation; a conservative-state contour residual passes the first long Galilean gate

This section supersedes one important interpretation in section 27.3. The
direct element-frame Roe residual was well conditioned and Galilean invariant,
but it had silently omitted the `U-Uhat` term required by
`RD_ALE_SPLIT_MESH_VELOCITY`. Restoring that term exposes an interpolation
compatibility issue rather than another linear-solver issue. All new choices
below remain compile-time experiments; no default has changed.

### 28.1 What happens when the omitted split term is restored

The laboratory split residual is

```
Phi_T = sum_j K_j(Uhat_j) + C_T,
C_T   = -1/2 sum_j |n_j| (sigma_bar . n_j) (U_j - Uhat_j).
```

In an element frame `b_T = sigma_bar`, the correction must be transformed as

```
C'_T = G(b_T) C_T
     = -1/2 sum_j |n_j| (sigma_bar . n_j) G(b_T)(U_j-Uhat_j).
```

The code now constructs this quantity both ways. Their maximum difference was
`O(1e-17)` at boost 0 and `O(1e-15)` at boost 10, so the implementation of the
change of conservative coordinates is correct.

That identity is not, however, Galilean covariance between two independently
boosted simulations. Under an additional uniform boost `B`, the absolute mesh
velocity in the correction changes from `sigma_bar` to `sigma_bar+B`, leaving

```
-1/2 sum_j |n_j| (B . n_j) G(B)(U_j-Uhat_j),
```

which is not discretely zero because the physical Roe residual uses the
parameter-vector interpolant `Uhat` while the moving median-dual ledger uses the
P1 conservative interpolant `U`. The short `t=0.02`, `n=48` Gresho comparison
therefore degraded from round-off and scaled approximately linearly with boost:

| boost | velocity L1 | density L1 | pressure L1 | internal-energy L1 |
|---:|---:|---:|---:|---:|
| 3  | `1.263e-5` | `2.442e-5` | `3.044e-5` | `2.114e-4` |
| 10 | `4.230e-5` | `8.119e-5` | `1.019e-4` | `7.026e-4` |

Thus the first direct-frame result in section 27.3 solved the conditioning
problem but obtained exact invariance partly by dropping a required term. A
consistent residual must use one interpolant for both physical and geometric
parts; transforming the split correction cannot repair the mismatch.

### 28.2 Conservative-state contour residual

`RD_ALE_CONTOUR_RESIDUAL` tests the smallest consistent alternative. In the
`b_T=sigma_bar` element frame it forms the total from nodal conservative states,

```
Phi'_T = 1/2 sum_j |n_j| [n_jx F_x(U'_j) + n_jy F_y(U'_j)].
```

The Roe matrices still define the multidimensional LDA distribution; they no
longer define the element total. The total residual and the moving median-dual
ledger now use the same P1 `U`, so no `U-Uhat` correction is needed. This is a
different RD spatial residual, not a purely algebraic rewrite of the old one.

At `t=0.02`, boost 0 against boost 10 after undoing translation and boost gave

| field | L1 | Linf |
|---|---:|---:|
| coordinates | `1.202e-16` | `1.554e-15` |
| velocity | `6.348e-15` | `5.157e-14` |
| density | `1.150e-14` | `5.129e-14` |
| pressure | `3.535e-14` | `1.563e-13` |
| internal energy | `1.060e-13` | `4.583e-13` |

Three reverse gates passed:

1. A smooth no-flip endpoint test ran 16 steps; its cumulative endpoint
   conservation defect reached `1.255e-13`, consistent with round-off
   accumulation.
2. The non-rigid uniform-state regularisation test recorded 784 removed and
   784 added edges over 90 geometry records (flips in every record), while
   `max|dU|=4.441e-16` and the largest endpoint defect was `9.326e-15`.
3. Campoli's mass pair passed the same uniform test; velocity and density were
   bitwise identical to Arpaia at the final snapshot.

The negative control matters: at boost 0 and `t=0.02`, the corrected split and
contour solutions already differ by velocity L1 `3.241e-4`, density L1
`6.408e-5` and pressure L1 `4.163e-4`. The contour choice must therefore earn
its own consistency, accuracy and shock results before it can become a default.

### 28.3 Full `t=1` boost ladder

The contour experiment completed the formerly failing boost 10 case with the
new RD CFL limiter. The integral Gresho profile is almost boost independent:

| boost | volume-weighted `v_phi` L1 | peak `v_phi` | velocity L1 against de-boosted boost 0 | density L1 | pressure L1 |
|---:|---:|---:|---:|---:|---:|
| 0  | `9.384016e-3` | `0.9614260` | -- | -- | -- |
| 1  | `9.384143e-3` | `0.9614260` | `2.054e-6` | `6.684e-7` | `5.310e-6` |
| 3  | `9.379595e-3` | `0.9611953` | `5.257e-5` | `1.208e-5` | `9.693e-5` |
| 10 | `9.384214e-3` | `0.9614263` | `4.844e-6` | `1.711e-6` | `1.125e-5` |

Boost 3 has a much larger particlewise Linf (`4.41e-2` in velocity) than boost
10 even though its integral profile remains on the same plateau. This
non-monotonicity is evidence for a local topology-branch difference, not a
smooth boost-dependent truncation error. Exact short-time covariance therefore
becomes statistical/physical covariance after thousands of rebuilds: the mesh
can take different but nearly equivalent flip branches after round-off-size
perturbations.

Relative to section 25's Roe-state residual, the contour residual retains a
higher peak (`0.961` rather than about `0.934`) but has a slightly larger profile
L1 (`0.00938` rather than about `0.0078`). The likely interpretation is less
dissipation with more local scatter. A spatial-resolution ladder and a smooth
Yee test are needed before calling this an accuracy improvement.

### 28.4 Arpaia versus Campoli inside the contour formulation

Campoli independently reproduces boost-10 covariance at `t=0.02`: velocity L1
`6.257e-15`, density L1 `1.122e-14` and pressure L1 `3.333e-14`. The choice of
mass scalar pair is therefore separate from the boost fix.

On the smooth moving test the two forms retained the predicted second-order
difference when the actual quantised timestep was halved:

| actual `dt` | velocity L1 difference | density L1 difference | pressure L1 difference |
|---:|---:|---:|---:|
| `1.5625e-4` | `1.556e-13` | `5.412e-13` | `6.729e-13` |
| `7.8125e-5` | `3.870e-14` | `1.349e-13` | `1.681e-13` |
| `3.90625e-5` | `9.823e-15` | `3.406e-14` | `4.207e-14` |

The velocity ratios are `4.02` and `3.94`; the other fields give the same
factor-four behaviour. This confirms the section 8.7 algebra in the new
residual coordinates as well.

At `t=1`, however, the two mesh trajectories no longer remain particlewise
close: velocity L1/Linf are `5.043e-5/4.060e-2`. The profile metrics remain
close (`0.0093840`, peak `0.961426` for Arpaia; `0.0093951`, peak `0.961444`
for Campoli). The first logged `minA` difference above `1e-4` relative appears
near `t=0.57666`, and an abrupt 15.6 per cent difference appears near
`t=0.984375`, consistent with different near-cocircular flip choices. The
current log lacks a connectivity hash, so this is strong geometric evidence,
not yet an exact first-flip timestamp.

Section 24.3 must therefore be read narrowly: the forms are immaterial for
bulk accuracy here and differ by `O(dt^2)` before topology branching, but their
long particlewise mesh histories need not remain close. Keep **Arpaia as the
default mass/divisor pair** because its analysis is the primary reference, and
keep Campoli as the positive-divisor verification/fallback. The residual
default is not yet settled: the contour experiment needs Yee convergence and
Sod/KH/RT/Sedov tests, especially across discontinuous flips.

### 28.5 Reproducibility

- corrected split build: job `10384065`, artifact
  `build_artifacts/ale-lda-comoving-split-corrected/05ea49c2fd28-496eec351044de41/Arepo`;
- Arpaia contour build: job `10384071`, artifact
  `build_artifacts/ale-lda-comoving-contour/05ea49c2fd28-dbf5f9ae27385311/Arepo`;
- Campoli contour build: job `10384078`, artifact
  `build_artifacts/ale-lda-comoving-contour-campoli/05ea49c2fd28-9017afac5d15d026/Arepo`;
- short boost and reverse gates: jobs `10384072`--`10384081`;
- Arpaia/Campoli timestep ladder: jobs `10384083`--`10384088`;
- full Arpaia boost ladder: jobs `10384090`--`10384093`;
- long Campoli comparison: job `10384094`;
- all outputs and provenance are under
  `/home/zwu/Hydro_data_analysis/Data_MMRD_debug/output_gal3_*`.

## 29. 2026-08-13: Chapter 4 is reorganised around Arpaia, the conservative-state contour residual, and the AREPO realisation

The moving-mesh draft in the thesis has been substantially reorganised after
the boost study in sections 25--28. This is primarily a clarification of the
mathematical contract; it does not make the experimental contour path a code
default. Only Chapter 4 was changed. Chapters 1--3, including the static RD
notation and derivation, were left untouched.

### 29.1 Why the thesis needed to change

The former Chapter 4 began with the endpoint-mass/Campoli representation and
introduced the Arpaia midpoint form only later as a comparison. That order no
longer matched either the literature or the implementation work:

- Arpaia et al. (2015) is the primary published ALE-RD analysis;
- the midpoint form treats N, LDA and B through one common construction,
  whereas endpoint N needs an explicit centre-distributed geometric share;
- the current fluid prototype has mainly followed the Arpaia mass/divisor
  pair; and
- sections 24 and 28 found no clear accuracy or performance advantage that
  would justify making Campoli the principal form. Before topology branches,
  their measured difference follows the predicted second-order scaling; after
  many rebuilds, small differences can select different near-cocircular flip
  histories without materially changing the bulk Gresho profile.

More importantly, the boost-10 investigation changed the spatial-residual
question. The old Roe construction used the parameter-vector-linearised state
`Uhat` for the physical residual while the moving-mass and mesh-advection
parts referred to the nodal conservative state `U`. Restoring the omitted
`U-Uhat` split correction showed that this mixed interpolation is not
Galilean covariant: the short-time error grew approximately linearly with the
boost. Direct co-moving algebra fixed the conditioning problem, but it could
not make two different interpolants covariant.

The conservative-state contour experiment instead constructs the element
total from one nodal `P1-U` representation. It reached round-off agreement
between boost 0 and boost 10 at `t=0.02`, completed the full boost-10 run, and
kept the long-time integral Gresho profiles almost boost independent. The
long-time particlewise differences are non-monotone in boost and correlate
with different topology branches, so they are not evidence for a remaining
smooth boost-dependent truncation term. These results motivate the new
mathematical organisation, while the nonzero difference between the Roe and
contour solutions remains the reason not to promote the contour residual
without convergence and shock tests.

### 29.2 New black main line in Chapter 4

The moving-mesh material is now split into two explicit levels.

1. **ALE-RD theory on a moving triangulation.** This part defines the moving
   P1 basis, the intensive nodal degree of freedom U_i, the continuous ALE
   equations, the non-conservative Arpaia residual, the midpoint DGCL, and the
   two-stage Arpaia RK method. The Arpaia modified median-dual mass is the
   reference divisor and the free-stream argument is manifest for N, LDA and
   B.
2. **Realisation in AREPO.** Only this part introduces Q_i=m_i U_i as a
   storage ledger, the rebase operation, pulled-back new connectivity,
   topology-change moments, active/inactive generators, pending residuals,
   hierarchical clocks, MPI ownership, and the RD timestep diagnostic.

This separation removes the previous ambiguity in which Q_i could look like
the physical unknown or a material median-dual control volume. The
mathematical unknown is U_i; Q_i is an AREPO storage convention whose weight
must match the RD mass operator whenever raw residual numerators are
accumulated.

The Arpaia midpoint equations are now black thesis text rather than a red
review correction. Campoli has its own comparison subsection. The retained
derivation records that, for a frozen F1/LDA distribution matrix, the endpoint
and midpoint forms differ by the same element scalar delta_T in the temporal
coefficient and nodal divisor. The equivalence is explicitly restricted to
the F1 family. Endpoint N, and the N fraction of B, still require the separate
geometric share. Arpaia is therefore the default mathematical form; Campoli
remains a comparison and a possible positive-divisor fallback under strong
compression.

### 29.3 What P1-U means, and which residual it discretises

The thesis now defines

~~~
I_h F(U) = sum_j psi_j F(U_j),
b_T      = |T|^{-1} integral_T sigma_h dA
         = (sigma_1 + sigma_2 + sigma_3)/3.
~~~

Because U_h is linear on a triangle, its gradient is constant. Hence

~~~
integral_T sigma_h . grad(U_h) dA
  = |T| b_T . grad(U_h)
  = integral_boundaryT (b_T . n) U_h ds.
~~~

The contour total

~~~
Phi_tilde_T^(P1-U)
  = integral_boundaryT [I_h F(U).n - (b_T.n) U_h] ds
~~~

therefore discretises the **geometrically non-conservative Arpaia residual**

~~~
integral_boundaryT F.n ds - integral_T sigma_h.grad(U_h) dA,
~~~

not the complete conservative ALE residual. A red terminology note was added
to prevent the central ambiguity: using the conservative Euler state U does
not make an expression a conservative ALE residual. The latter differs by

~~~
- integral_T U_h div(sigma_h) dA,
~~~

and Arpaia deliberately absorbs this geometric source into the modified
midpoint mass. The contour total and the mass correction therefore do not
double count the same term.

The inward nodal-normal convention and factor 1/2 are explicitly tied back to
Chapter 3 through grad(psi_j)=n_j/(2|T|). The Roe state is not removed from the
method: it still constructs K_i^+, K_i^-, S^- and the N/LDA/B distribution
operators. It no longer defines the element total in the new candidate
formulation.

### 29.4 Element-local co-moving coordinates

The Galilean map U'=G(b_T)U is now part of the black theoretical line. The
Euler flux identity

~~~
F_n(G U) = G [F_n(U) - (b_T.n) U]
~~~

shows that the laboratory P1-U non-conservative residual and the element
frame residual transform covariantly. Since
sigma'_h=sigma_h-b_T has zero element mean,

~~~
integral_T sigma'_h . grad(U'_h) dA = 0,
~~~

so the spatial total in the element frame is only the contour integral of the
physical flux evaluated from U'_j. This is the clean ALE analogue of AREPO's
co-moving Riemann solve and explains the boost-10 improvement: powers of the
bulk velocity are removed before the nearly Lagrangian upwind matrix is
formed.

Only the mean translation disappears. Mesh deformation remains in
div(sigma_h), the modified Arpaia mass, the midpoint geometry, and eventual
connectivity changes. The transformation also does not cure a genuine rank
deficiency when u-sigma=0; it separates that physical degeneracy from
avoidable laboratory-coordinate conditioning.

### 29.5 Red comments retained as research notes

The new chapter has a black mathematical narrative, while red text is used
for qualifications that are still implementation- or evidence-dependent:

- the distinction between conservative variables and a conservative ALE
  residual;
- the relation to the earlier U-Uhat split correction and its N/LDA
  distribution weights;
- the boost-10 motivation and the remaining full-RK covariance gate;
- the possible loss of positivity of the modified Arpaia divisor;
- the AREPO mesh lifetime and absence of an explicitly built midpoint mesh;
- edge-flip moment identities and the smooth O(h^4) versus discontinuous
  topology defect;
- the mildly implicit nature of an RD CFL bound based on future midpoint
  geometry; and
- unresolved interruption of an open RK interval by a topology/clock change.

Two pdflatex passes completed without a LaTeX error. After the second pass,
Chapter 4 had no unresolved internal equation or section references. The
remaining undefined citations are the repository's normal no-BibTeX build
state. The generated PDF and auxiliary files were removed afterwards, so the
thesis worktree contains only the Chapter 4 source modification.

### 29.6 Recommended next priorities

The next work should test the new mathematical contract before cleaning it
into a production code path.

1. **Close the elemental algebra first.** Verify the volume/mean-velocity and
   contour assemblies to round-off, verify laboratory/co-moving covariance of
   the element total and nodal distribution, and extend the check through both
   complete Arpaia RK stages including their temporal mass terms. Keep the
   legacy Roe-Uhat result as a method comparison, not as an algebraic gate.
2. **Establish smooth consistency and order.** Run the moving Yee vortex with
   a resolution ladder and controlled mesh motion. This is the decisive test
   of replacing the Roe-defined element total by I_h F(U). Compare static,
   laboratory contour, co-moving contour, and the corrected split path at the
   same RD timestep.
3. **Instrument topology branching before long campaigns.** Record a
   connectivity hash, first differing flip, flip count, and the topology
   contribution to each conserved component. This is needed to distinguish
   truncation error from the random-walk-like divergence of near-cocircular
   mesh histories.
4. **Test discontinuities, where the topology estimate is weakest.** Use Sod
   first, followed by KH, RT and Sedov. Measure the flip-associated defect,
   positivity, shock stability, and conservation separately. Repeat the key
   cases with mesh regularisation on and off.
5. **Keep Arpaia as the default mathematical pair during these tests.**
   Retain Campoli as a compiled comparison and exercise it on strong
   compression, where the Arpaia modified divisor is most likely to approach
   zero. Do not generalise the F1 equivalence to N.
6. **Finish the RD CFL contract.** The current endpoint predictor plus
   realised-midpoint audit is adequate for experiments, but production use
   needs either a safe deformation bound or an iterate/clip rule when the
   realised midpoint limit is smaller.
7. **Defer hierarchical moving connectivity.** Equal-timestep fluid tests
   should mature before defining how an open element RK interval survives a
   flip or a triangle-clock change.

The immediate priority is therefore not another large Gresho campaign. It is
the elemental/full-RK covariance proof followed by the moving Yee convergence
test. If those pass, the discontinuous topology campaign becomes the next
decision gate for whether the conservative-state contour residual can replace
the legacy Roe-defined element total.

---

## 30. 2026-08-13: the contour and timestep effects separated, and connectivity hashes date the flip branches

- Author: `Claude Code Opus 5`, acting on two criticisms of sections 27 and 28
  (Codex's element co-moving frame, and the conservative-state contour
  residual that replaced it).
- Source change: a connectivity hash in the geometry diagnostic. Nothing else.

### 30.1 Codex's correction of section 26 is upheld; I was wrong

Section 26.2 claimed the moving-mesh timestep drops the advective term. It does
not. `timestep_treebased.c:476-485` computes

```
#ifdef VORONOI_STATIC_MESH
  csnd += |v|
#else
  csnd += |v - VelVertex|          <-- present on the moving path
#endif
CurrentMaxTiStep = rad / csnd
```

and `get_timestep_hydro` takes the minimum with it. `TREE_BASED_TIMESTEPS` is
enabled in every Config here, so the relative advective speed was always
included. I read only `get_timestep_hydro` and missed it, and the "about one per
cent of `c`" estimate built on that reading is void. Section 26.2's other
over-statement, that the static finite-volume condition is always more
conservative than the RD condition, is also withdrawn on Codex's counterexample.
What survives of section 26.2 is the length scale only: `get_cell_radius` is the
Voronoi radius rather than the RD median-dual star bound.

### 30.2 Separating the contour residual from the RD CFL limiter

Section 28.3 compared its `t = 1` boost ladder against section 25's and
attributed the difference to the contour residual. But that ladder changed three
switches at once — `RD_LDA_COMOVING_FRAME`, `RD_ALE_CONTOUR_RESIDUAL` and
`RD_ALE_CFL_TIMESTEP` — against section 25's single one. A two-by-two on the
identical initial condition, Gresho boost 0, `n = 48`, `t = 1`:

| | AREPO timestep, 2049 steps | RD-CFL timestep, 4097 steps |
| --- | --- | --- |
| Roe-state residual | `L1 = 0.00784`, peak 0.9340 | `L1 = 0.00778`, peak 0.9294 |
| contour residual | `L1 = 0.00950`, peak 0.9474 | `L1 = 0.00940`, peak 0.9614 |

Reading the margins:

- **The RD CFL limiter halves the timestep and changes `L1` by 0.8 per cent.**
  The solution was already timestep converged, so `L1` here measures spatial
  error. That is reassuring for the limiter: it costs a factor of two in steps
  and changes nothing it should not.
- **The contour residual is responsible for the whole `L1` increase**, 0.00784
  to 0.00950, twenty-one per cent worse at matched timestep.
- **The peak is a genuine interaction and section 28.3's attribution is half
  right.** Of the reported rise from 0.934 to 0.961, the residual contributes
  0.934 to 0.947 and the timestep the remaining 0.947 to 0.961. Under the Roe
  residual the same halving moves the peak the other way, 0.9340 to 0.9294.

So at boost 0 the contour residual is **not** an accuracy improvement on this
problem: it buys 1.4 per cent of peak amplitude for 21 per cent of `L1`. That is
consistent with section 28.2's own reading of less dissipation with more local
scatter, and it reinforces the conclusion there that the contour residual must
earn its default through Yee convergence and the discontinuous tests, not
through this comparison.

### 30.3 Connectivity hashes: the flip branches now have timestamps

Sections 28.3 and 28.4 attributed two observations to Delaunay branch
differences — boost 3 having a larger particlewise `Linf` than boost 10, and
Arpaia and Campoli separating by `t = 1` — and recorded honestly that the log
"lacks a connectivity hash, so this is strong geometric evidence, not yet an
exact first-flip timestamp".

The diagnostic now emits one. The edge set is already sorted by particle ID and
deduplicated, so an FNV-1a over it is a rank-independent fingerprint of the
connectivity, and two runs of the same problem can be compared record by record.
Contour residual with the RD CFL limiter, `n = 48`, `t = 1`, each boost against
boost 0:

| comparison | records with identical connectivity | first divergence |
| --- | ---: | ---: |
| boost 3 against boost 0 | 1624 of 4096 | **`t = 0.396729`** |
| boost 10 against boost 0 | 2288 of 4096 | **`t = 0.558838`** |

Two results.

**The covariance is exact, not approximate, and it is exact in the mesh as well
as in the solution.** Under boosts of three and ten times the vortex's own peak
velocity, the Delaunay connectivity is bit-for-bit the same for 1624 and 2288
consecutive rebuilds. That is a stronger statement than any field comparison,
because connectivity is a discrete quantity that cannot be close: it either
matches or it does not.

**Section 28.3's non-monotonicity is explained exactly.** Boost 3 branches at
`t = 0.397` and boost 10 only at `t = 0.559`, so boost 3 has forty per cent
longer to accumulate a different mesh history. Its larger particlewise `Linf`
therefore has nothing to do with the size of the boost. Codex's inference was
right and is now a measurement.

The hash should be used the same way for the Arpaia against Campoli separation
of section 28.4, where the same explanation is offered on the same kind of
evidence.

### 30.4 An index

Section references throughout this log now resolve through an index at the top,
one line per section, so that a reference such as "section 20" carries its
subject without opening the file.

---

## 31. 2026-08-13: Yee decides the contour residual, and particlewise comparison has a horizon

- Author: `Claude Code Opus 5`, closing the two items left by section 30 (the
  two-by-two that separated the contour residual from the CFL limiter, and the
  connectivity hash).
- Source change: none. `create_mmrd_ics.py` gains a self-contained Yee vortex.

### 31.1 Why Yee was needed

Section 30.2 (the two-by-two disentangling the contour residual from the RD CFL
limiter) found the contour residual twenty-one per cent worse in `L1` on Gresho.
That could not settle anything, because the Gresho velocity profile is only
`C^0` and caps the observed order near 1.6, as section 25 (the quantitative
boost and resolution study) already showed. The Yee vortex is smooth and is an
exact steady solution in its own frame, so at boost zero every deviation is
scheme error. Its constants match
`Analysis/yee_boost/yee_boost_common.py`, against which volume 1's static LDA
order of 1.879 was measured; note that `gamma` is 1.4 there and 5/3 in the
Gresho cases.

### 31.2 Both residuals converge; the ranking reverses

Boost 0, `t = 1`, density `L1` against the analytic steady state, identical
timestep policy and initial conditions:

| residual | `n=32` | `n=64` | `n=128` | order 32-64 | order 64-128 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Roe-state | 2.558e-3 | 7.361e-4 | 2.163e-4 | **1.80** | **1.77** |
| contour | 2.092e-3 | 6.617e-4 | 2.026e-4 | **1.66** | **1.71** |

Two things, and they do not point the same way.

**The moving-mesh Roe path converges at 1.80 and 1.77**, consistent with volume
1's static 1.879 on the same vortex. That is the first confirmation that moving
mesh has not cost the scheme its order on a smooth problem, and it is the
result section 4's phase plan called the minimum defensible deliverable.

**The contour residual is more accurate at every resolution but converges more
slowly**: 6 to 18 per cent lower `L1`, at order 1.66 to 1.71 against 1.77 to
1.80. Extrapolating the two fits, the Roe form overtakes it somewhere around
`n` of several hundred.

**This reverses the Gresho reading of section 30.2.** There the contour residual
was 21 per cent worse; here it is 6 to 18 per cent better. The two problems
differ in exactly the way that should matter: Gresho's kinks at `r = 0.2` and
`r = 0.4` are where the `P^1`-in-flux and quadratic-in-`Z` interpolants disagree
most, and Yee has no such feature. So the contour residual is neither uniformly
better nor uniformly worse; it is better on smooth flow at accessible
resolutions and worse at a kink.

**Neither result justifies changing the default.** The discriminating tests are
now the discontinuous ones, Sod and KH, where the `C^0` behaviour is the whole
question and where the contour form's handling of a kink is the property under
test rather than an incidental one.

### 31.3 Particlewise comparison has a horizon of about two thousand steps

Section 28.4 (Arpaia against Campoli inside the contour formulation) attributed
their separation at `t = 1` to different Delaunay branches, on geometric
evidence. The connectivity hash added in section 30.3 dates it. All three
comparisons are the same problem, `n = 48` Gresho, `t = 1`, 4096 records:

| comparison | records with identical connectivity | first divergence |
| --- | ---: | ---: |
| Campoli against Arpaia | 1386 | `t = 0.338623` |
| boost 3 against boost 0 | 1624 | `t = 0.396729` |
| boost 10 against boost 0 | 2288 | `t = 0.558838` |

Section 28.4's inference is therefore confirmed and dated: the two mass forms
produce bit-identical connectivity for 1386 consecutive rebuilds and only then
branch.

The comparison between rows is the more useful result. A Galilean boost is, in
exact arithmetic, **no perturbation at all**, so the boost rows branch purely
through floating-point asymmetry. The Campoli row is a genuine `O(dt^2)` scheme
difference. They branch at comparable times, and the genuine difference branches
**earlier** than a boost of three. Near-cocircular decisions are therefore about
as easily flipped by round-off as by a real second-order change in the scheme.

**The rule this implies should be applied to every comparison in this phase:**
particlewise or `Linf` agreement between two variants of this scheme has a
horizon of roughly one to two thousand steps at `n = 48`, after which only
integral or statistical metrics mean anything. Section 28.3's non-monotonic
`Linf` across boosts, and section 28.4's particlewise separation, are both this
effect and neither is evidence about the schemes being compared. Short-time
covariance gates — the `t = 0.02` comparisons of sections 27 and 28 — remain
valid precisely because they sit well inside the horizon.

### 31.4 What is now settled and what is next

Settled: the moving-mesh Roe path is second order on a smooth problem, at 1.80
and 1.77 against volume 1's static 1.879. The contour residual is a real
alternative with a different error profile rather than an improvement. The two
mass forms and the boost ladder are exactly covariant in the mesh until a
near-cocircular event, and their later divergence is not evidence.

Next, in order: Sod and KH for the contour residual, since that is where its
kink behaviour decides; the mesh-velocity policy comparison of section 14.5 item
6, which section 22.1 showed is coupled to the upwind matrix conditioning; and
P4, the build-fingerprint hole for untracked sources, still the only open item
from section 14.2.
