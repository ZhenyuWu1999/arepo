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
| 32 | the form-selection campaign, and the stress test that weakened it |
| 33 | Codex audit: contour remains the provisional mathematical default, not Roe + split |
| 34 | the audit verified; extensibility becomes the criterion and the frame becomes a parameter |
| 35 | Codex: Arpaia + contour in a parameterised frame; Chapter 4 derives the frame map |
| 36 | review of the rewritten Chapter 4: six defects and a patch list |
| 37 | the implementation pass: guards, deletions, and three misreadings |
| 38-43 | Codex: cleanup safeguards, moving-mesh N and B campaigns, ALE isolation |
| 44 | the Sod defect is mostly time integration; the N part is real and quantified |
| 45 | numerical entropy production separates every KH outcome |
| 46 | Codex: mesh-velocity smoothing does not cure the moving-N Sod noise |
| 47 | the entropy term is refuted; the sigma fraction rescues KH completely |
| 48 | the Lagrangian-fraction threshold, the t=10 test, and regularisation's failure |
| 49 | what the Lagrangian fraction costs on Gresho with boost: too much |
| 50 | status: the failure is a three-way intersection, and which side to attack |
| 51 | Kimi: proposed shear-mode floor for Sod, and discriminators for the KH failure |
| 52 | Codex: the MOOD fallback fires too late; local N cannot repair the precursor |
| 53 | the three-day stopping-rule sprint: LF control, Bmax, Bx |
| 54 | review of that plan: two gaps; scalar-B boost first, eigenvalue floor second |
| 55 | Kimi: reading of 52-54, ranked low-cost candidates, restart calibration idea |
| 56 | Codex: accepted sprint order, corrections to 54/55, scalar-B acceptance gates |
| 57 | Codex: scalar-B sprint -- Gresho boost-invariant, KH to t=10, measured cost |
| 58 | Codex: Chapter 4 distribution derivation; component-B is the accuracy control |
| 59 | Codex: matched pure-N KH control; the time term belongs to the B blend |
| 60 | KH consolidated: scalar B is the temporary f=1 solution; visualisation audit |
| 61 | offline shear-floor check: mechanics verified, eps ~= 0.45 prediction refuted |
| 62 | Codex: Sermeus-Deconinck and ALE-DG precedents for the eigenvalue fix |
| 63 | Codex: online shear floor restores moving-N Sod transverse noise to static |
| 64 | Codex: LDA floor extension; Gresho/Yee rejection tests pass; rarefaction reading |
| 65 | Codex: entropy-mode floor is a decisive negative; Sod operator tuning closed |
| 66 | Kimi: close the testing phase; one discriminator; two notes for the next phase |
| 67 | phase-entry assessment: concur on closure, plus the conservation-drift prerequisite |
| 68 | Codex: local conservative topology-transfer operator proposed, with fallback |
| 69 | Codex: offline flip-patch audit passes — O(h^2), cascades, periodic seams |
| 70 | Codex: online repair slice — uniform flow exact, short-KH drift down x4400 |
| 71 | Codex: KH t=10 — conservation passes, the KH trajectory moves materially |
| 72 | Codex: plan for exact triangle-key patches and non-invasive dual diagnostics |
| 73 | review of 68-72: maths verified, second hypothesis added, plan approved amended |
| 68 | Codex: topology-conservation repair proposed for review; local high-order patch correction with an admissible fallback |
| 69 | Codex: conservative flip-patch repair passes the offline go/no-go audit |
| 70 | Codex: one-rank equal-step online repair passes uniform flow and matched short-KH gates |
| 71 | Codex: KH t=10 repair is robust and conservative, but provisional support patches materially shift the solution |
| 72 | review plan: exact old/new triangle-key patches, non-invasive dual diagnostics and cost gates |

Section 32's campaign has its own document,
`dev_log/RD_ALE_FORM_SELECTION.md`: it states the five compile switches and
their derivations, then decides a recommended default from an eight-build
campaign over particle-level, smooth and discontinuous tests. Section 32
summarises it and records the stress test that partially retracted its
residual recommendation.

Section 33 is Codex's independent audit of that recommendation. It accepts the
Arpaia modified-midpoint mass pair and element co-moving conservative
coordinates, but does not accept the campaign's argument for promoting
Roe-`Uhat` + split over the contour residual. This is a provisional
mathematical recommendation only: Zhenyu agrees with the direction on first
inspection but has not completed the detailed review, and no production Config
is changed.

Section 34 verifies section 33's factual corrections against the raw output,
adds a fourth the audit understated, and then moves the criterion: with B
descoped and LDA and N both mandatory, the compile guards make the co-moving
frame the narrow choice and the residual form the portable one. It records
Zhenyu's frame parameterisation, in which the laboratory frame is the
zero-velocity case of the co-moving one, and the selections that follow.

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

> **Section 32 runs those tests**, as part of a campaign over the whole switch
> matrix, and finds that the discontinuous tier separates LDA from N far more
> sharply than it separates the two residuals.

---

## 32. 2026-08-13: the form-selection campaign, and the stress test that weakened its own recommendation

Section 31.4 listed Sod and KH as the next tests, because that is where the
contour residual's kink behaviour decides. Rather than run them alone, the whole
switch matrix was run against one protocol, because the five switches had
reached a state where each was validated only against the defect it was
introduced for and none was a default.

**The campaign has its own document, `dev_log/RD_ALE_FORM_SELECTION.md`**, which
states the switches and their derivations before the results. It is standalone
so that it can be read as the argument for a default without reading four
thousand lines of chronology. This section records what it found and what
happened afterwards; it does not duplicate it.

### 32.1 The one piece of new mathematics

Extending `RD_ALE_CONTOUR_RESIDUAL` to N was not a guard relaxation. N never
distributes `Phi`: its nodal flux is `K_i^+(U_i - U_in)` and the identity
`sum_i phi_i^N = sum_j K_j Uhat_j` holds by construction of the inflow state, so
substituting a different element total makes assertion A2 fail at the first
step. The difference is instead distributed with N's lumped row sum,

```
phi_i^N += (Phi_contour - sum_i phi_i^N) / 3,
```

which is the same construction used for the section 18 split correction under N
and for the geometric residual of section 7.5. It is conservative by
construction and inert where the two totals agree. It passed every tier-A gate,
but it is a scheme design choice rather than a validated scheme and is recorded
as one.

### 32.2 What the campaign established

Eight builds, `{Roe+split, contour} x {laboratory, co-moving}` plus two
single-axis confirmations and N duplicates of both residuals. All eight pass the
`sigma = 0` bitwise collapse, the 784-flip free-stream gate, and flip-free
endpoint conservation.

**`G(b_T)` is exactly a similarity, and it is worth having anyway.** Laboratory
and co-moving agree to every printed digit on the boost-3 covariance gate and
are **bit-identical** at all three Yee resolutions. It changes no answer. But it
decides whether real problems run: laboratory Roe cannot do boost 10 at all, and
on KH it dies at `t = 2.4e-4` on the conservation identity where the co-moving
build reaches `t = 0.98`, four thousand times further.

**KH generalises the boost-10 finding.** A shear layer on a quasi-Lagrangian
mesh has `sigma` approximately `u` *everywhere*, so `S^-` degenerates for
precisely the reason section 27 identified at high boost. The degeneracy is not
a curiosity of an artificial test; it is generic in shear, which is most of
astrophysical hydrodynamics.

**The Roe form is not discretely covariant and its defect is linear in boost**:
`1.895e-5` at boost 3 against `6.345e-5` at boost 10, a ratio of 3.35 against a
boost ratio of 3.33, confirming the section 28 argument quantitatively. The
contour form is covariant to round-off, `2.4e-15`, in both frames and at both
boosts.

**On Yee the two residuals trade**: Roe is closer to second order, 1.75 and 1.78;
the contour form is more accurate at every resolution tested but converges more
slowly, 1.64 and 1.71. This reproduces section 31.2 under a different timestep
policy, which is worth noting because it was the one result the harness change
could have contaminated.

**Campoli conserves four orders better on a flip-free interval**, `2.2e-16`
against Arpaia's `1.5e-12`, for a structural reason worth remembering: Campoli's
divisor is the plain new median dual, which is also the storage area, so the
final `Q_bar -> Q_new` rebase is the identity. Arpaia divides by `m_bar` and
multiplies by `m_new`, and the figure is exactly that accumulation over five
steps. This does not make Campoli the better default today, but it names the
condition under which it would become one.

### 32.3 The recommendation, and the stress test that weakened it

The campaign recommended adopting `RD_LDA_COMOVING_FRAME` and **keeping Roe as
the default residual**, the second resting substantially on one measurement: the
contour form fails on Sod at `t = 0.139` where the Roe form completes, and `G`
does not change the failure time in any digit, so the failure is intrinsic to
the residual rather than to conditioning.

That measurement was taken at one Courant number and one resolution, and it
carried most of the weight of the recommendation, so it was re-run across both.
The result is section 8 of the campaign document and it is a **partial
retraction**:

| build | CFL 0.30, `n=64` | CFL 0.10 | CFL 0.03 | CFL 0.30, `n=128` |
| --- | --- | --- | --- | --- |
| contour + LDA | fails `t=0.139` | fails `t=0.140` | fails `t=0.132` | **fails `t=0.056`** |
| Roe + LDA | completes | completes | *wall clock, no failure* | **fails `t=0.149`** |

The contour failure is confirmed intrinsic: a negative pressure at the shock
front, `rho = 0.0966`, `press = -0.0111`, with `rd_over_selected = 1.27` showing
the step was already inside the RD limit, and a tenfold reduction in timestep
moves the failure time by under six per cent. Refinement makes it *worse*, which
is what a less dissipative scheme should do — more resolution sharpens the shock
and enlarges the overshoot.

**But the Roe form fails at `n = 128` too**, with a negative *density*, a worse
failure mode than the contour form's negative pressure. Its completion at
`n = 64` is a property of that resolution, not of the scheme. The CFL 0.03 Roe
run produced no assertion and no termination and was killed by the job time
limit after ten times as many steps; it is recorded as inconclusive rather than
as a pass, which is the discipline section 14.2 asked for and which was violated
in section 19.

The premise therefore survives only in weakened form: **the contour residual is
less robust than the Roe residual on Sod, but neither is a defensible default
for shock problems under LDA.** The only builds that complete both discontinuous
tests at every setting are the **N** variants, of both residuals. The
discontinuous tier separates LDA from N far more sharply than it separates the
two residuals, so it cannot settle the residual question, and the choice falls
back on the smooth and covariance evidence — where the contour form is exactly
covariant and more accurate at accessible resolutions, and the Roe form is
closer to second order and inherits Arpaia's published analysis.

### 32.4 What this leaves

Section 5.1 of the campaign document is untouched by the stress test:
`RD_LDA_COMOVING_FRAME` should be the default, on evidence that is a similarity
measurement plus a conditioning measurement, neither of which the Sod result
touches. **This is a recommendation, not a change**; `Template-Config.sh` and the
production Configs are untouched and the decision is Zhenyu's.

Section 5.2 stands in direction but not in strength, and the campaign document
says so in place rather than by silent edit.

The methodological point is the one worth carrying forward. A recommendation
that rests on a single run at a single operating point is not a result, and this
one was published before being stress-tested. It took two extra jobs to find
that the load-bearing measurement was resolution-dependent. **The cost of
testing one's own conclusion is far below the cost of a default chosen on one
data point**, and the campaign's own horizon rule of section 31.3 — that only
integral metrics mean anything past one to two thousand steps — is the same
lesson in a different variable.

Next, in order: a positivity or limiting mechanism, which is now the gating item
for both residuals rather than an improvement to one of them, and which section
6 of the campaign document names as the thing that would overturn the residual
recommendation outright; the mesh-velocity policy comparison of section 14.5
item 6; and P4, the build-fingerprint hole for untracked sources, still the only
open item from section 14.2.

---

## 33. 2026-08-13: Codex audit — keep contour as the provisional mathematical default, not Roe + split

- **Reviewer:** Codex.
- **Scope:** the mathematical default requested in
  `dev_log/RD_ALE_FORM_SELECTION.md`, checked against Chapter 4, the latest
  logs, and the raw output used by the campaign.
- **Source change:** this log entry only. Chapter 4, code, compile switches and
  production Configs are unchanged.
- **Status:** provisional. Zhenyu agrees with the direction on first inspection,
  especially with formulating the residual in the new co-moving frame, but has
  not yet audited the details.

### 33.1 Decision in one line

The cleanest canonical mathematical tuple is

```text
Arpaia modified-midpoint RK2
+ conservative-state P1-U contour total residual
+ element-local co-moving conservative coordinates
```

Here “contour” selects the element total residual. It does **not** remove the
Roe matrices from LDA: the matrices still define `K_i^+`, `S^-`, and the
upwind distribution of that total. Roe-`Uhat` + split should remain available
as a legacy/control formulation, not lead the Chapter 4 derivation.

This separation is the main reason contour is the more natural default. In a
co-moving frame the conservation law is already expressed through the moving
space-time boundary. A contour total is therefore the direct discrete object;
reconstructing a Roe mean state and then adding a separate mesh-velocity split
is an extra algebraic factorisation whose covariance has to be recovered by
careful cancellation.

### 33.2 Evidence from the campaign that survives audit

The raw Yee snapshots reproduce the campaign values:

| residual | L1 at 32 | L1 at 64 | L1 at 128 | observed orders |
| --- | ---: | ---: | ---: | ---: |
| Roe + split | `2.773120116e-3` | `8.237560548e-4` | `2.402256079e-4` | 1.75, 1.78 |
| contour | `2.290109722e-3` | `7.356192296e-4` | `2.252200434e-4` | 1.64, 1.71 |

Thus contour is 17.4%, 10.7% and 6.2% lower in L1 at the three tested
resolutions, while Roe has the better measured asymptotic slope. The current
data do not prove that contour has the better asymptotic scheme, but they do
show that choosing Roe as the mathematical default on accuracy grounds is not
justified.

The boost campaign is more decisive about form: Roe + split has a covariance
defect linear in the boost, whereas the contour total is covariant to
round-off. The element co-moving implementation also removes the large
absolute-velocity conditioning problem without changing the intended
conservative operator.

The five-step flip-free comparison confirms a real storage/rebase advantage for
Campoli: total-energy drift is round-off rather than about `4e-12`. That is
useful evidence for a future implementation choice, but it is not enough to
replace Arpaia as the formal time/geometry default. Keep Campoli as the
comparison/fallback form.

### 33.3 Corrections to the latest campaign report

Four qualifications materially weaken its recommendation for Roe:

1. The Roe, `n=64`, `CFL=0.03` Sod run was not inconclusive. Its raw log
   reaches `Final time=0.2` and exits normally. The correct table says Roe
   completes at `n=64` for CFL 0.30, 0.10 and 0.03, but fails at `n=128`,
   CFL 0.30, at `t=0.149`. Contour fails the three `n=64` runs and the
   `n=128` run.
2. Lab-frame and co-moving Yee results are not bit-identical. After ParticleID
   alignment, the largest Roe `n=128` differences are about `1.08e-10` in
   density and `6.57e-9` in position; contour's density difference is about
   `8.79e-13`. Connectivity hashes agree. The defensible statement is
   “equivalent far below truncation error,” not “bit-identical.”
3. The `n=128` Sod IC is untracked and absent from the campaign checksum
   manifest. Independent regeneration reproduces it exactly, so there is no
   evidence of contamination, but the generator and manifest must be completed
   before these runs become thesis evidence.
4. “Refinement makes contour worse because lower dissipation sharpens the
   shock” is a plausible hypothesis, not a demonstrated mechanism. The
   `n=64` failure is negative predictor pressure, the `n=128` failure is
   negative stored mass, and only one jitter realisation was tested.

The discontinuous tests therefore establish that bare LDA needs a positivity or
limiting mechanism. They do not select the element residual. Completion of the
N variants also does not prove that the equal-correction N-contour construction
is the desired positivity mechanism; that construction is itself a scheme
choice.

### 33.4 Published analysis does not uniquely select Roe + split

The campaign's remaining argument is that Roe should lead because it “inherits
Arpaia's published analysis.” This conflates two independent choices:

- Arpaia's modified-midpoint mass/time construction; and
- the spatial representation of the element total residual.

Arpaia's conservation argument permits obtaining the total through direct
contour integration or through an exact mean-value Jacobian linearisation.
Published authority therefore supports the time/mass structure, but does not
uniquely promote the present Roe-`Uhat` + split discretisation over contour.

There is still a real burden on the current contour formula: Chapter 4 uses a
specified nodal-flux quadrature, not the exact nonlinear boundary flux of
`F(U_h)`. It must earn its accuracy and robustness numerically. That is a
reason to keep the decision provisional, not a reason to make Roe + split the
canonical derivation.

### 33.5 Mathematical default versus production default

For the thesis derivation and future implementation work, use the contour form
as the provisional mathematical default, in element-local co-moving
coordinates, with Roe matrices retained only in the LDA distribution. Keep:

- Arpaia as the time/geometry default and Campoli as the explicit comparison;
- Roe-`Uhat` + split as a regression/control path;
- the ordinary timestep selector as default until the RD-CFL proposal has an
  independent benefit;
- production Configs unchanged until the remaining gates pass.

Before switching a production default, require three controlled results:

1. prescribed *identical* mesh motion for Yee at `n=256` and `n=512`, to
   separate spatial convergence from different mesh trajectories;
2. a B/positivity implementation followed by Sod and Kelvin–Helmholtz tests, so
   shock robustness is judged with the intended stabilisation rather than bare
   LDA;
3. an element-level full-RK covariance check including the temporal `F1`
   terms, not only the spatial total.

### 33.6 Current switch policy

| choice | mathematical default | production default now |
| --- | --- | --- |
| time/mass | Arpaia modified midpoint | unchanged |
| element total | **contour, provisional** | unchanged |
| algebraic frame | **element co-moving** | unchanged |
| LDA distribution | Roe matrices `K_i^+`, `S^-` | unchanged |
| shock stabilisation | B/positivity is the next gate | no new default |
| timestep | ordinary selector | unchanged |

The resulting position is deliberately narrower than “contour wins.” Contour
is the better organising mathematics, especially in the new co-moving frame;
Roe + split remains an essential control and may still prove numerically
superior in an asymptotic or stabilised regime. The default should change in
code only after those regimes are tested.

---

## 34. 2026-08-16: the audit verified, and the selection criterion moves to extensibility

- **Author:** Claude Code (Opus 5), from Zhenyu's review of section 33.
- **Scope:** independent verification of section 33's factual corrections; a
  fourth correction it understated; what the compile guards imply for the
  choice of default; Zhenyu's frame parameterisation and the scope decisions
  that follow from it.
- **Source change:** this log entry, plus a corrective note in
  `dev_log/RD_ALE_FORM_SELECTION.md` section 8.2. No solver change, no compile
  switch change, no production Config change.
- **Status:** recommendations, for Codex's review. Nothing here has been
  implemented.

### 34.1 Section 33's three factual corrections are confirmed

All three were re-measured from the raw output rather than accepted, and all
three reproduce Codex's numbers.

**Correction 1 — the Roe, `n=64`, CFL 0.03 Sod run completed.** From the run's
own records:

```text
arepo log :  Final time=0.2 reached. Simulation ends.
             endrun called, calling MPI_Finalize()
provenance:  exit_status.txt = 0
directory :  end present, snap_001.hdf5 written
```

Section 8.2 of the campaign document reports it as killed by the job time
limit at `t = 0.121` and records it as inconclusive. That is wrong. The
corrected row is that **Roe completes all three `n=64` Courant numbers** and
fails only at `n=128`.

**Correction 2 — laboratory and co-moving are not bit-identical.** After
ParticleID alignment, maximum absolute differences at `t = 1`:

| build | field | `n=32` | `n=64` | `n=128` |
| --- | --- | ---: | ---: | ---: |
| Roe | Density | 6.44e-15 | 1.09e-13 | **1.077e-10** |
| Roe | Coordinates | 7.99e-15 | 1.33e-12 | **6.568e-9** |
| contour | Density | 6.22e-15 | 2.63e-13 | 8.794e-13 |
| contour | Coordinates | 6.22e-15 | 4.74e-12 | 5.631e-12 |

No resolution is bit-identical; the divergence grows with step count. The
campaign's claim of bit-identity was inferred from `L1` agreeing to the printed
digits, which is true and much weaker — `1e-10` sits far below `L1 = 2.4e-4`.
The defensible statement is "equivalent far below truncation error."

The table carries information the campaign missed. **Roe's laboratory/co-moving
divergence is two orders larger than contour's**, which is an independent
confirmation of the conditioning argument of section 4.2 of the campaign
document, obtained from data already in hand.

**Correction 3 — the `n=128` Sod initial condition is outside the manifest.**
`MMRD_ICS.sha256` lists only `IC_khjit64.hdf5` and `IC_sodjit64.hdf5`, and the
generator hard-codes the resolution:

```python
# examples/gresho_2d/create_mmrd_ics.py:289
for name, state, n in (("sod", sod_state, 64), ("kh", kh_state, 64)):
```

`IC_sodjit128.hdf5` exists on disk but is produced by neither. Codex treats this
as a provenance defect with no evidence of contamination, which is correct as
far as it goes, but understates the consequence: **that initial condition
carries the entire partial retraction of section 8**. The retraction's whole
case is the single `n=128` run. Combined with correction 1, which restores a
Roe pass, the retraction is now weaker than when it was written and rests on
one run built from an unmanaged artifact. Until the generator gains a
resolution parameter and the manifest is completed, section 8 is not citable.

### 34.2 A fourth correction, understated: the `n=128` contour failure is a degenerate cell

Codex's item 4 calls the mechanism "refinement sharpens the shock and enlarges
the overshoot" a plausible hypothesis rather than a demonstrated one. The raw
termination records show it is not merely undemonstrated; **it is the wrong
mechanism.**

```text
contour, n=128, t=0.0556:
  very bad...i=6183 ID=3426 mass=-7.88e-09 oldMass=3.06e-08 utherm=1561.86

Roe,     n=128, t=0.1488:
  RD predictor state invalid: ID=3748 rho=-0.000452688 press=2.48913
```

The Sod `n=128` initial condition has density between 0.125 and 1.0 on 16384
cells in a unit box, so a typical cell mass is about `3.4e-5` and the smallest
plausible one about `7.6e-6`. The failing cell holds `oldMass = 3.06e-8`, some
250 times below that floor. **It is a sliver, not a shock front.**

For contrast, all three contour failures at `n=64` are a healthy density with a
negative pressure at `x` near the shock —

```text
CFL 0.30: rho=0.0966  press=-0.0111   x=0.987
CFL 0.10: rho=0.1347  press=-0.000326 x=0.990
CFL 0.03: rho=0.0883  press=-0.000141 x=0.00084
```

— which is a genuine overshoot. The two contour failures therefore have
different mechanisms, and section 8.3 of the campaign document treats them as
one mechanism intensifying with resolution. That reading is withdrawn.

Two consequences:

1. **The `n=128` row has no discriminating power.** Roe fails there on the
   scheme (a negative predictor density at a shock); contour fails on the
   geometry. They are not comparable, and the retraction of section 8 rested
   on comparing them.
2. The claim is not that contour is exonerated. Mesh motion is driven by
   `VelVertex`, which contains the solved fluid velocity, so "the residual
   produced the sliver" cannot be excluded. The honest statement is that
   **the proximate trigger is a degenerate cell, and whether the residual
   caused it is unmeasured.**

### 34.3 The guard matrix inverts the priority

The compile guards at the top of `src/hydro/residual_distribution_solver.c`
decide what each switch can be combined with:

```c
:82   RD_LDA_COMOVING_FRAME    excludes N_SCHEME, B_SCHEME, RD_HIERARCHICAL_TIMESTEPS
:91   RD_ALE_CONTOUR_RESIDUAL  excludes B_SCHEME
:95   RD_ALE_CONTOUR_RESIDUAL + N_SCHEME + RD_LDA_COMOVING_FRAME  is an error
```

| | LDA | N | B | hierarchical |
| --- | :-: | :-: | :-: | :-: |
| `RD_ALE_CONTOUR_RESIDUAL` | yes | yes | no | no |
| `RD_LDA_COMOVING_FRAME` | yes | **no** | no | **no** |

**The residual form, argued over for two rounds, is the portable choice. The
co-moving frame, which neither the campaign nor the audit disputed, is the
narrow one** — it excludes N, B and the timestep hierarchy, which is every
direction the work is going.

Once extensibility is admitted as a selection criterion, it therefore does not
first judge Roe against contour. It judges the frame and the mass pair. This
criterion is also cheap: it is a derivation exercise, not machine time.

### 34.4 The frame is a parameter, not a switch

**Zhenyu's proposal**, and it is correct: the co-moving frame contains the
laboratory frame as the zero-velocity case, so the two need not be separate
compile branches.

The implementation is already most of the way there. From line 2926:

```c
double b0 = Velvertex_avg[0], b1 = Velvertex_avg[1], b2 = b0*b0 + b1*b1;
double G_local[4][4]    = {{1,0,0,0}, {-b0,1,0,0}, {-b1,0,1,0}, {0.5*b2,-b0,-b1,1}};
double velx_shift = velx_avg - b0, vely_shift = vely_avg - b1;
double h_shift    = h_avg - b0*velx_avg - b1*vely_avg + 0.5*b2;
rd_build_characteristic_matrices(velx_shift, vely_shift, h_shift, Cs_avg, 0.0, 0.0, ...);
```

At `b = 0` the matrices are exactly the identity and the shifted states reduce
exactly to the unshifted ones — these are additions and subtractions of exact
zeros, so the reduction is bitwise, not approximate.

One correction is needed before the unification is real. The call above
**hard-codes `sigma' = 0`**, which is the `b_T = sigma_bar` special case rather
than the general one. The correct parameterisation carries `b_T` as a free
element-local frame velocity and assembles

```text
u'      = u      - b_T
sigma'  = sigma  - b_T
```

so that

- `b_T = 0` gives `u' = u`, `sigma' = sigma`: **the laboratory frame**;
- `b_T = sigma_bar` gives `sigma' = 0`: **the present co-moving build**.

The two builds become two values of one parameter in one derivation, and one
axis of the switch matrix disappears.

**Three acceptance gates follow, and all three are bitwise**, because the
reductions above are exact arithmetic rather than small differences:

1. `b_T = 0` reproduces the laboratory build **bitwise**;
2. `b_T = sigma_bar` reproduces the present co-moving build **bitwise**;
3. `b_T` set to a single constant over the whole mesh gives **exactly** the
   Galilean transform of the `b_T = 0` result.

Gate 3 is the one worth having. It turns discrete covariance from a comparison
across two binaries into an identity inside one, which is precisely the
measurement that produced the false bit-identity claim of correction 2.

### 34.5 N in the co-moving frame: the derivation is three lines

> **Half of this subsection is wrong; corrected in section 37.1.** The
> mathematics below is right and the guards were removed on it. But the claim
> that the guards recorded *only* a missing derivation is not: one of them was
> also holding back a genuine implementation defect, and removing it on the
> strength of the derivation alone would have produced a wrong answer instead
> of a compile error.

The guards of section 34.3 look like mathematical obstacles and are not; they
record what has not yet been derived. N reuses the same similarity that section
4.2 of the campaign document already verified for LDA:

```text
K'_j = G K_j G^-1   =>   S'^- = G S^- G^-1   =>   Uhat'_in = G Uhat_in
phi'^N_i = K'^+_i (U'_i - Uhat'_in)
         = G K^+_i G^-1 G (U_i - Uhat_in)
         = G phi^N_i
```

The contour extension to N passes as well. Its lumped correction is
`phi_i^N += (Phi_contour - sum_i phi_i^N)/3`; `G` is linear, both terms
transform under `G`, so their difference does, and division by three commutes
with `G`. **`contour + N + co-moving` has no mathematical obstruction**, and
the guard at line 95 should be removable with the derivation written down.

One expectation should be set correctly. `G` will probably buy **less** for N
than for LDA. Section 4.4 of the campaign document has `LDA + laboratory` dying
on KH at `t = 2.4e-4` on the conservation identity while `N + laboratory`
completes the run; N is markedly less sensitive to the `S^-` degeneracy that
`G` exists to condition. Implementing it for N is for uniformity of the
derivation, not to rescue N.

### 34.6 Scope decisions

**Zhenyu's, recorded as decisions rather than as findings:**

1. **B is descoped as a completion requirement.** It is not mature enough to
   gate this phase. One weak requirement survives: the derivation must not be
   written in a form that excludes B, since B's blend coefficient is built from
   the total residual. This immediately removes the guard at line 91 as an
   obstacle, since what it excludes is B.
2. **LDA and N must both run.** Every retained form must work for both. This
   makes the line 82 and line 95 guards the only remaining blockers, and
   section 34.5 shows they are removable.
3. **Switches of the Arpaia/Campoli and Roe/contour kind are to be decided, not
   exhaustively tested.** Pick the better one and move on.

On the third: **pick and delete, do not pick and retain as a fallback.** The
five surviving switches, each validated only against the defect it was
introduced for, are exactly what produced an eight-build matrix and a
recommendation whose load-bearing measurement was wrong. A compile branch
nobody builds decays. The proposal for a discarded form is to keep its
derivation in the documentation plus one frozen regression Config, and remove
it from the scheme matrix.

### 34.7 The selections

**Element total: contour.** Portable across LDA and N, excluding only the now
descoped B; covariant to round-off where the Roe defect is linear in boost; and
under the frame parameterisation of section 34.4 it is the direct discrete form
of a space-time boundary flux, whereas the Roe mean-value identity presumes
three nodes on one interpolant at one time — which is exactly what a timestep
hierarchy breaks. Its one unpaid debt is real and belongs in the derivation:
Chapter 4 specifies a nodal-flux quadrature, not the exact
`contour integral of (F(U_h) - (sigma.n) U_h)`, and that gap is the common
suspect for both the order deficit (1.64/1.71 against 1.75/1.78) and the Sod
negative pressure. **This agrees with section 33 and adds portability and the
hierarchy argument to its reasons.**

**Frame: parameterised per section 34.4**, laboratory retained as `b_T = 0`.

**Mass pair: Campoli is favoured, less firmly, pending one derivation check.**
Section 4.1 of the campaign document found Campoli's divisor is the plain new
median dual, which is also the storage area, so the endpoint rebase is the
identity and conservation is `2.2e-16` against Arpaia's `1.5e-12`. Under a
timestep hierarchy the geometry changes per bin and the ledger migrates between
ranks, so a ledger permanently denominated in the storage area is worth much
more than it is today, while Arpaia's `m_bar -> m_new` multiplies by changing
geometry at every bin. **The check to run first, on paper**: does Campoli's
mass form still satisfy the DGCL and free-stream preservation under
**non-uniform time slabs**? The equal-step comparison against Arpaia is already
done, in commit `93229c0`.

### 34.8 What the hierarchy and MPI actually constrain

Read against `RD_hierarchical_timestep_conservation_design.md` and
`RD_hierarchical_timestep_phaseb_prototype.md`, both from volume 1.

**The hierarchy constrains the temporal mass, not the spatial residual.**
Section 10 of the design document excludes LDA+F1 from the first hierarchy
because the F1 temporal mass couples all three vertices,
`T_i^T = beta_i^T (|T|/3) sum_j (U_j* - U_j^n)/h_T`, so a frozen vertex has no
accepted `dU/h`; N's lumped mass is diagonal, `(|T|/3) delta_ij`, and a frozen
vertex is unambiguous. This axis separates **N from LDA+F1** far more sharply
than it separates the two residuals.

**The residual form still enters, at derivation level.** Roe's conservative
linearisation identity holds for one interpolant at one time; a hierarchy is a
non-uniform space-time slab decomposition, which is what a contour integral
over a moving boundary already describes. This should be settled on paper, not
by runs.

**The unwritten collision.** Section 5 of the phase-B prototype records that
`DualArea` is initialised once from the all-active static tessellation and then
persists and migrates as part of `SphP`. On a moving mesh it changes every
step, and the Arpaia pair additionally needs the half-time geometry `m_bar` and
the new geometry `m_new`. **Hierarchical timesteps on a moving mesh therefore
need geometry at several time levels per bin**, which no document covers. This
is the real integration risk of the phase, and it is also the reason section
34.7 favours the mass form that needs no endpoint rebase.

**MPI is close to neutral on the residual choice.** Phase-B already solved the
hard part on a fixed mesh: the global minimum-ID simplex ownership rule, the
star construction, and 1/4/16-rank invariance, together with two intermediate
implementations its tests rejected. Two properties transfer for free and are
further reasons to adopt the frame parameterisation: `G(b_T)` is element-local,
and the LU-against-SVD branch is a per-element pivot ratio, so **both are
decomposition-invariant by construction**. What is not bitwise is the
accumulation order of `sum over T containing i` across ranks, already named as
item 7 of section 11 of the design document, and it affects both residuals
equally. One thing does need redoing: the ownership key depends on `b_T`, and a
moving mesh rebuilds the triangle set every step, so "exactly one owner per
triangle" must be re-established after every rebuild.

### 34.9 The KH question, and the experiment volume 1 already designed

Zhenyu's question — Kelvin-Helmholtz behaves poorly on the static mesh, so does
the moving mesh improve it? — has a sharper form than it appears, because
volume 1 already measured the obstacle.

The 2026-08-03 KH pilot in volume 1 found that **the seeded signal lies below
the static mesh's own noise floor.** Zero-perturbation controls at `t = 0.2`:

| background | LDA | N | B |
| --- | ---: | ---: | ---: |
| smooth uniform, zero-seed `E_ky` | 9.50e-5 | 4.84e-5 | 6.65e-5 |
| sharp Morton, zero-seed `E_ky` | 9.97e-4 | 3.67e-4 | 6.23e-4 |

Its conclusion was that any exponential slope fitted to the total transverse
kinetic energy is **not** a growth-rate measurement, and it attributed the noise
to the P1-Roe/contact defect on an irregular fixed mesh.

**Advecting a contact through an irregular fixed mesh is the one mechanism a
Lagrangian mesh certainly removes** — at `sigma` approximately `u` the contact
does not traverse the mesh at all. This yields a specific falsifiable
prediction:

> On the moving mesh, the **zero-seed control's** `E_ky` should fall by orders
> of magnitude.

The measurement needs **only the control** — no seeded run, no exact
eigenmode, no B, and no positivity mechanism — and both `Roe + N` and
`contour + N` already complete KH on the moving mesh, so it is runnable now and
doubles as a residual comparison on a metric with physical meaning.

Two prerequisites, both cheap:

1. Volume 1's pilot used the `Analysis/kh_2d` manager on a glass `48^2` mesh;
   the campaign uses `IC_khjit64`. **Different initial conditions and
   resolutions, so the published numbers above cannot be compared directly.**
   The static baseline must be re-run on the campaign's initial condition, which
   is the cheap half of the comparison.
2. The campaign's KH carries a global `vy = 0.1 sin(4 pi x / L)`, an amplitude
   larger than volume 1's sharp Morton case (0.05) and two orders above its
   smooth cases (`5e-4`, `1e-3`). **It is a robustness test, not a growth-rate
   test**, and the noise floor never arises on it. A zero-seed variant of the
   generator is needed, which is one line.

### 34.10 Revised order

**On paper, no machine time, and each item gates what follows:**

1. The `b_T` parameterisation of section 34.4 — `u' = u - b_T`,
   `sigma' = sigma - b_T` — including the N similarity of section 34.5 and the
   covariance of the contour lumped correction. **One derivation covering
   LDA and N across laboratory and co-moving.**
2. The contour form's nodal-flux quadrature against the exact boundary integral
   (section 34.7). Required before the form is declared final.
3. Campoli under non-uniform time slabs (section 34.7).

**Implementation and cheap machine time:**

4. Remove the guards at lines 82 and 95 and add the three bitwise gates of
   section 34.4. On completion, "LDA and N both run" holds for every retained
   form.
5. The KH zero-seed noise floor, static against moving, under N, on one shared
   initial condition (section 34.9).
6. Add a resolution parameter to `create_mmrd_ics.py`, complete
   `MMRD_ICS.sha256`, and re-run the `n=128` Sod (corrections 3 and section
   34.2).

**Afterwards:** the per-bin geometry problem of section 34.8, which is the
phase's real integration risk.

### 34.11 What this section does not do

No source file, compile switch or production Config is changed. Section 33
remains provisional; this section verifies its factual claims and accepts its
direction on the residual, but the reasons given here for contour are
portability and the hierarchy, which are not the reasons section 33 gave. The
selections of section 34.7 are recommendations for Codex's review and for
Zhenyu's decision, not adopted defaults.

---

## 35. 2026-08-17: the mathematical default is Arpaia + contour in a parameterised frame, and Chapter 4 now derives the frame map

- **Author:** Codex, recording Zhenyu's decisions and the subsequent
  Chapter 4 mathematics review.
- **Scope:** documentation only. The edited thesis source is
  MyThesis/Zhenyu-PhDThesis/zhenyu_thesis/chapter4/chapter4.tex. No AREPO
  source, compile switch, production Config or result is changed here.
- **Status:** the mass-form decision below is adopted as the working default;
  contour is the preferred mathematical spatial form while its quadrature and
  frame derivation continue to be audited.

### 35.1 Decisions, including one correction to section 34

Zhenyu adopts the following order of work:

1. **Use the Arpaia temporal-mass form as the default.** It is the mature,
   published ALE-RD construction and is the safer thesis baseline. Campoli
   remains a useful comparison, but section 34.7's tentative preference for
   Campoli is not adopted.
2. **Prefer the conservative-state contour residual over Roe + split** as the
   mathematical spatial default. It is the more natural expression in the
   element co-moving frame and does not make a mean-value linearisation part of
   the definition of the total residual.
3. **Do not run another broad Roe + split campaign.** Existing results did not
   logically eliminate that branch, but they are sufficient to retain it only
   as a frozen diagnostic/reference form. A new Roe run is warranted only if
   it isolates a specific contour or frame defect.
4. **Finish the equal-step mathematics and small physical tests before the
   hierarchy.** Sod and Kelvin--Helmholtz tests are useful method-development
   probes and need not wait for the final campaign.
5. **Defer the hierarchical geometry ledger.** Arpaia's use of intermediate
   and endpoint dual areas makes asynchronous time bins and MPI migration a
   real design problem, but that uncertainty is not a reason to replace the
   default equal-step method now.

Thus the working combination is **Arpaia + conservative-state contour +
parameterised element frame**, with the frame and contour mathematics still
subject to explicit checks rather than treated as settled by experiment alone.

### 35.2 The notation is now separated

The thesis no longer uses one symbol for two different roles:

- \(\boldsymbol{\sigma}_h(\mathbf{x},t)\) is the physical mesh-velocity field
  used by AREPO;
- \(\overline{\boldsymbol{\sigma}}_T
  =\frac13\sum_{i\in T}\boldsymbol{\sigma}_i\) is its element mean;
- \(\mathbf b_T\) is a freely selected, constant Galilean-frame velocity for
  one element residual/RK evaluation.

Therefore \(\mathbf b_T=0\) is the laboratory representation, while
\(\mathbf b_T=\overline{\boldsymbol{\sigma}}_T\) is the element co-moving
representation. This removes the earlier ambiguity in which \(\mathbf b_T\)
could be read as if it were itself the mesh velocity.

### 35.3 Where the matrix \(G(\mathbf b_T)\) comes from

The frame map is now derived rather than introduced as an algebraic device.
For

\[
 t'=t,\qquad
 \mathbf x'=\mathbf x-\mathbf b_T t,\qquad
 \mathbf u'=\mathbf u-\mathbf b_T,
\]

write the two-dimensional Euler state as

\[
 \mathbf U=(\rho,m_x,m_y,E)^T,\qquad
 \mathbf m=\rho\mathbf u,\qquad
 E=\rho e+\tfrac12\rho|\mathbf u|^2 .
\]

Direct substitution gives

\[
 \rho'=\rho,\qquad
 \mathbf m'=\mathbf m-\rho\mathbf b_T,\qquad
 E'=E-\mathbf b_T\!\cdot\!\mathbf m
       +\tfrac12\rho|\mathbf b_T|^2 .
\]

Because \(\mathbf b_T\) is fixed during this element evaluation, every
right-hand side is linear in the conservative components. Hence
\(\mathbf U'=\mathbf G(\mathbf b_T)\mathbf U\), with

\[
\mathbf G(\mathbf b_T)=
\begin{pmatrix}
1&0&0&0\\
-b_{T,x}&1&0&0\\
-b_{T,y}&0&1&0\\
\tfrac12|\mathbf b_T|^2&-b_{T,x}&-b_{T,y}&1
\end{pmatrix}.
\]

The thesis also records
\(\mathbf G^{-1}(\mathbf b_T)=\mathbf G(-\mathbf b_T)\) and
\(\mathbf G(\mathbf b_1)\mathbf G(\mathbf b_2)
=\mathbf G(\mathbf b_1+\mathbf b_2)\). The thermal energy
\(E-|\mathbf m|^2/(2\rho)\), and therefore pressure and sound speed, are
unchanged. \(G\) is consequently the conservative-variable representation of
a Galilean coordinate change, not a new stabilisation or distribution matrix.

### 35.4 Physical flux, ALE flux and the contour residual

For a unit normal \(\mathbf n\), direct substitution into the Euler normal
flux gives

\[
 \mathcal F_n(\mathbf G\mathbf U)
 =
 \mathbf G\left[
 \mathcal F_n(\mathbf U)
 -(\mathbf b_T\!\cdot\!\mathbf n)\mathbf U
 \right].
\]

The mesh velocity transforms with the coordinates,
\(\boldsymbol{\sigma}'_h=\boldsymbol{\sigma}_h-\mathbf b_T\). Defining

\[
 \mathcal F_{\boldsymbol{\sigma},n}(\mathbf U)
 =
 \mathcal F_n(\mathbf U)
 -(\boldsymbol{\sigma}_h\!\cdot\!\mathbf n)\mathbf U
\]

then yields the central covariance identity

\[
 \mathcal F_{\boldsymbol{\sigma}',n}(\mathbf U')
 =
 \mathbf G(\mathbf b_T)
 \mathcal F_{\boldsymbol{\sigma},n}(\mathbf U).
\]

Equivalently, \(\mathbf u'-\boldsymbol{\sigma}'
=\mathbf u-\boldsymbol{\sigma}\): the physical relative velocity has not
changed. For \(\mathbf b_T=\overline{\boldsymbol{\sigma}}_T\), the primed mesh
velocity has zero element mean. With \(P^1\) states this removes the mean
translation term from the element spatial residual, leaving the explicit
basis-function contour form

\[
\widetilde{\Phi}^{\prime T}
=
\int_{\partial T}\sum_{j\in T}\psi_j
  \mathcal F(\mathbf U'_j)\!\cdot\!\mathbf n\,{\rm d}s
=
\frac12\sum_{j\in T}
  \mathcal F(\mathbf U'_j)\!\cdot\!\mathbf n_j .
\]

The disappearance of the explicit volume mesh-advection term does **not**
remove mesh deformation from the scheme: the modified Arpaia mass still
contains the geometric evolution, and the midpoint and endpoint dual areas
remain time dependent.

### 35.5 This does not conflict with the Chapter 3 linearised RD theory

The contour construction defines the **total element residual** directly from
conservative nodal fluxes. The \(K_i\) matrices are still required to
**distribute** that total residual among the vertices. Differentiating the ALE
flux covariance gives

\[
 \mathbf K_i'
 =\mathbf G\mathbf K_i\mathbf G^{-1},\qquad
 \mathbf K_i^{\prime\pm}
 =\mathbf G\mathbf K_i^\pm\mathbf G^{-1},
\]

and hence
\(\widetilde{\Phi}^{\prime T}
=\mathbf G\widetilde{\Phi}^{T}\). Thus \(G\) does not replace \(K\), and using
the contour form does not reject the Chapter 3 linearised distribution
framework. It changes how the total residual is evaluated; the characteristic
linearisation remains in the distribution step.

### 35.6 Connectivity changes and the future ledger

For an equal-step RK2 update across a flip, the current mathematical storage
procedure remains:

1. save \(U_i^n=Q_i^n/m_i^n\) before the connectivity change;
2. on the new connectivity construct Arpaia's temporary mass \(\bar m_i\);
3. rebase the temporary storage to \(\bar Q_i=\bar m_iU_i^n\);
4. perform the RK2 update using the new connectivity;
5. write endpoint storage
   \(Q_i^{n+1}=m_i^{n+1}U_i^{n+1}\).

The implementation should detect whether the simplex star actually changed;
the rebase is a topology-transition operation, not an unconditional extra
fluid update. Under the present global timestep the mass/storage value can be
changed directly because every vertex crosses the same time slab together.
That argument will not survive hierarchical bins. The hierarchical extension
needs an explicit pending conservative ledger (the proposed L_pending or an
equivalent object), together with per-bin geometry time levels and MPI
migration rules, so that an inactive vertex does not silently absorb a dual
area jump.

### 35.7 Verification and next work

The expanded Chapter 4 source passes git diff --check and a full
pdflatex -halt-on-error build. The build reports the thesis's existing
undefined citation/reference warnings but no error from these equations.

The next work is:

1. audit the contour nodal-flux quadrature against the exact moving-boundary
   integral and the primary Arpaia derivation;
2. use small Sod and KH/zero-seed tests during the audit, rather than postponing
   all physical experiments;
3. diagnose the \(n=128\) contour sliver as a geometry/degenerate-cell event;
4. keep Roe + split only as a targeted diagnostic;
5. design the hierarchical pending ledger only after the equal-step default is
   mathematically and experimentally stable.

---

## 36. 2026-08-17: review of the rewritten Chapter 4, and a patch list

- **Author:** Claude Code (Opus 5), reviewing section 35 and the Chapter 4
  source at `MyThesis/Zhenyu-PhDThesis/zhenyu_thesis/chapter4/chapter4.tex`.
- **Scope:** verification of the new mathematics, then six defects with a
  per-item patch list. Chapter 4 itself is **not** edited here; the thesis tree
  is Zhenyu's and the patches below are for Codex to apply or reject.
- **Source change:** this log entry only.

### 36.1 The Campoli preference of section 34.7 is withdrawn, on a better argument

Section 34.7 preferred Campoli on two grounds: its divisor is the storage area,
so the endpoint rebase is the identity, and conservation over a flip-free
interval is `2.2e-16` against Arpaia's `1.5e-12`.

Chapter 4 lines 825-842 give a stronger argument the other way, and it runs on
the **extensibility criterion of section 34.6 item 2** rather than against it.
For the diagonal N mass the endpoint form produces

```text
(|T^{n+1}| U_i^* - |T^n| U_i^n) / (3 dt)
    = (|T^{n+1}|/3)(dU_i/dt) + ((|T^{n+1}| - |T^n|)/(3 dt)) U_i^n
```

whose last term requires an explicit centre-distributed geometric
contribution. The Arpaia midpoint form contains only
`|T^{n+1/2}| dU_i / (3 dt)` and needs no such term. Since N is mandatory, the
form that needs no special N branch wins on the criterion this log adopted two
sections ago. **Weighting a round-off constant above the structure of the N
branch was the wrong call, and section 34.7's mass-pair preference is
withdrawn.** Section 35.1 item 1 stands as the decision.

The hierarchical concern of section 34.8 is not withdrawn; it is deferred, and
section 35.6 records it correctly as the pending-ledger problem.

### 36.2 What was verified

Checked by hand against the source, not accepted from the summary:

| claim | result |
| --- | --- |
| element covariance `Phi'^T = G Phi^T` | holds; the `b_T` terms from the physical flux and from the mesh term cancel exactly |
| `b_T = sigma_bar` removes the mesh term | holds; `sigma'_h` has zero element mean and `grad U'_h` is constant on `T` |
| the contour constant, `(1/2) sum_j F(U'_j).n_j` | consistent with `grad psi_j = n_j/(2|T|)` and `contour of psi_j n_out ds = n_j/2` |
| `K'_i = G K_i G^-1`, and the same for `K^+-` | holds |
| the Arpaia/Campoli scalar pair and `delta_T` | **both lines exact.** With `|T(t)| = A + Bt + Ct^2` and `C = (1/2)(sigma_1 - sigma_0) x (sigma_2 - sigma_0)`, the midpoint/trapezoid gap is `C dt^2/4`, which is `delta_T`; and `|T^{n+1}|` equals the Arpaia coefficient plus `delta_T` |
| "coincide exactly for a rigid translation" | holds; rigid translation gives `delta_sigma = 0` |
| the predictor/corrector arrangement | holds. The reviewer first read `+ (1/2) phi(U^n)` as a sign error. It is not: the temporal mass term is what rebases the left-hand side from `U^*` to `U^n`, and for N on a static mesh the pair collapses exactly to the trapezoidal rule |

Section 35's mathematics is sound. The six items below are gaps, not errors.

### 36.3 Defect 1: free-stream preservation is vacuous with respect to the mass

`Phi_{P1-U}(U_0) = (1/2) sum_j [ F(U_0).n_j - (sigma_bar.n_j) U_0 ]`, and a
closed triangle has `sum_j n_j = 0`, so **the residual vanishes identically —
for any geometry, any mesh velocity, and any mass**. The predictor then gives
`U^* = U_0`, the temporal term vanishes, and `U^{n+1} = U_0` follows for **any
non-zero divisor, including a wrong one**.

Chapter 4 lines 625-632 nevertheless *define* the discrete geometric
conservation law to be exactly this free-stream property, and acceptance
condition 3 tests only it. The chapter's DGCL clause therefore has no content
for the residual the chapter selects. All of the geometric content lives in the
modified mass, which free-stream cannot see, and equation
`ALE_RD_median_DGCL` — the identity that *can* see it — is demoted to a
corollary at lines 603-609.

This is the Farhat, Geuzaine & Grandmont (2001) point already in the volume 2
literature section: DGCL compliance has to be checked element by element rather
than inferred from a uniform state.

**Patch.** Split acceptance condition 3 into 3a and 3b. Keep free-stream as 3a,
annotated as necessary but nearly trivial for this residual and explicitly not
a test of the divisor. Add 3b: on a **non-uniform** state over a prescribed
deforming mesh, the stored ledger `sum_i m_i U_i` must be conserved to
round-off, with `ALE_RD_median_DGCL` restored from corollary to tested
condition.

### 36.4 Defect 2: the quadrature debt is stated but not in the acceptance list

Lines 262-264 state plainly that `I_h F` is a specified nodal interpolation and
not `F(U_h)` evaluated exactly. Acceptance condition 6 then asks that "the
volume and contour forms of `Phi_{P1-U}` agree to round-off" — but those are two
writings of the **same** quantity. Nothing in the list compares either of them
with the exact moving-boundary integral.

The structure of the gap, computed for this review: on an edge of length `l`
the linear-interpolation error integrates to `(l^3/12) g''`, with
`g'' = F''(U_h)[t_e.grad U, t_e.grad U]` because `U_h` is linear along the edge.
Hence

- the error is **`O(h^3)` per element, the same order as the P1 interpolation
  error that RD already tolerates**; but its tensor structure,
  `sum_e l_e^3 n_e F''[t_e.grad u, t_e.grad u]`, is different, so the
  cancellation over a vertex star that gives P1-RD its second order is not
  automatic. This is consistent with losing a fraction of an order rather than
  a whole one — 1.64/1.71 against 1.78;
- it **cannot break conservation**: on an interior edge both triangles use the
  same nodal values with opposite normals, so the error cancels edgewise in
  `sum_T Phi^T`. It does not cancel in the nodal distribution.

That pattern — exact conservation, depressed order, negative pressure at a
shock — is exactly what the campaign measured, which makes the quadrature the
leading suspect for both remaining contour defects.

**Patch.** Add an acceptance condition comparing `Phi_{P1-U}` against a
high-order evaluation of `contour of [F(U_h).n - (sigma_bar.n) U_h] ds`, and
report the ratio against `Phi` itself across a refinement ladder. If it
confirms, the fix is cheap and preserves both properties that matter: replace
the two-point trapezoid on each edge with a three-point Gauss rule on
`F(U_h(s))`. `U_h` is linear along the edge so the integrand is well defined;
covariance survives because `U_h(s) -> G U_h(s)` pointwise; telescoping survives
because both triangles use the same edge and the same quadrature points. The
cost is three flux evaluations per edge instead of one.

### 36.5 Defect 3: acceptance condition 9 is not achievable as written

> "results are invariant under MPI decomposition when compared by generator ID"

Item 7 of section 11 of `RD_hierarchical_timestep_conservation_design.md`
already records that the nodal accumulation `sum over T containing i` changes
order with the decomposition, so bitwise invariance does not hold. As written
the condition will fail and will read as a bug.

**Patch.** Either state a tolerance tied to the conservation threshold, or
require a canonical accumulation order and then claim bitwise. Naming which one
is intended is the point; both are defensible, silence is not.

### 36.6 Defect 4: N is mandatory but under-covered

Section 34.6 made N a completion requirement. In Chapter 4:

- the co-moving section never states that the frame map applies to N;
- none of the eleven acceptance conditions mentions N;
- the N-contour construction used throughout the campaign,
  `phi_i^N += (Phi_contour - sum_i phi_i^N)/3`, **does not appear in the
  chapter at all**. It is a scheme design choice, not a derived result, and it
  is currently documented only in section 4.1 of the campaign document and
  section 32.1 of this log.

**Patch.** Add the three-line N covariance from section 34.5 —
`K'_j = G K_j G^-1` gives `S'^- = G S^- G^-1` gives `Uhat'_in = G Uhat_in`
gives `phi'^N_i = G phi^N_i`, and the lumped correction commutes with `G`
because it is linear — and state the N-contour construction with its
justification and its status as a choice.

### 36.7 Defect 5: `b_T` denotes two different things

`\mathbf{b}_T` is the frame velocity throughout the co-moving subsection, and
`b_T` is the triangle timebin clock at equation `ALE_RD_triangle_clock`,
`b_T = min_{i in T} b_i`. Only boldface separates them, they share the
subscript, and both appear in the hierarchical subsection. Section 35.2 took
care to separate the two roles of `sigma`; this collision was introduced in the
same pass.

**Patch.** Rename one. The timebin clock is the more local usage; `k_T` or
`b^{\mathrm{bin}}_T` would do.

### 36.8 Defect 6: two small ones

- Lines 526-528 justify `K'^+- = G K^+- G^-1` by the eigenvalues being
  unchanged. That is necessary but not sufficient; the argument needs the
  eigenvector map `R' = G R`. One clause fixes it.
- Acceptance condition 11 counts "pulled-back new triangles with non-positive
  signed area". Section 34.2's failure was a median-dual mass of `3.06e-8`,
  some 250 times below the lightest plausible cell, on a triangle that need not
  have inverted. **A small-area/small-mass floor should be counted as well as a
  sign change**, otherwise the diagnostic misses the failure that actually
  occurred.

### 36.9 Summary for Codex

Nothing in section 35 needs to be retracted. Defects 1 and 2 are the ones that
change what gets tested: as the acceptance list stands, a wrong modified mass
and a quadrature-limited residual would both pass it. Defect 4 is scope
compliance with section 34.6. Defects 3, 5 and 6 are editorial.

---

## 37. 2026-08-17: the implementation pass, and three misreadings it exposed

- **Author:** Claude Code (Opus 5).
- **Scope:** repository cleanup, the co-moving frame extended to N, and the
  deletion of the two coherent stage-beta experiments. Commits `8d00fdf`,
  `d8e74c5`, `4a495ec`, `da5fbe8`, `bdb8283`.
- **Status:** done and verified. No production default is changed; section
  35.1's position that production Configs wait for the remaining gates is
  intact.

### 37.1 The N guard was not only a missing derivation

Section 34.5 argued that the guards excluding N from `RD_LDA_COMOVING_FRAME`
recorded what had not been derived rather than something impossible, and gave
the three-line similarity. That mathematics is correct and the guards are gone.

The characterisation was still half wrong. Reading the code the guard protects
showed a real defect. The co-moving block rebases `Kmatrix`, `rhs` and the
nodal states, and `Y_in` is solved from the shifted right-hand side, so `Y_in`
is in the element frame. N forms its inflow bracket *outside* that block, where
`U_hat_shift` is out of scope:

```c
Bracket[k][j] = U_hat[k][j] - Y_in[k];   /* unprimed U_hat, primed Y_in */
```

Enabling N by deleting the guard alone would have subtracted a primed inflow
state from an unprimed nodal state, giving a quantity that is neither frame's N
flux — **and it compiles**. The fix is one line inside the block, in the same
style the block already uses for `Kmatrix` and `rhs`:

```c
memcpy(U_hat, U_hat_shift, sizeof(U_hat));
```

`U_hat` is read downstream only at two sites, both inside
`#if defined(N_SCHEME) || defined(B_SCHEME)`, so in an LDA build the rebase is
not merely harmless but absent from the translation unit.

**The general lesson is about what a guard records.** A `#error` can encode a
missing derivation, a known-wrong code path, or both, and the text rarely says
which. Deriving the mathematics is necessary and is not sufficient; the code
the guard protects has to be read.

### 37.2 Two kinds of change, two strengths of proof

The deletion of `RD_RK2_COHERENT_BETA_N` and `_STAR` was verified by running
the real C preprocessor over the solver, with `#include` lines stripped so no
headers are needed, once per tracked Config that activates
`RESIDUAL_DISTRIBUTION`, before and after. **All 109 retained configurations
expand to byte-identical text.**

That is a proof for a deletion, because the removed branches were already
disabled in every retained Config. It is *not* available for enabling a
combination, where the expansion changes by construction. Section 37.1 is the
demonstration: the N path's expansion was perfectly legal and semantically
wrong. The two halves of this pass happen to sit on either side of that line,
which is worth remembering when the `b_T` work starts — that will be an
enabling change, so the preprocessor gives it nothing.

### 37.3 The deletion list was wrong on its largest item

Section 34 and the cleanup survey proposed six switches for deletion. Checked
one at a time against their own records rather than against a summary, four
survive:

| switch | verdict |
| --- | --- |
| `RD_RK2_COHERENT_BETA_N`, `_STAR` | deleted; all three beta conventions returned `p ~ 0.993` |
| `RD_RK2_RATE_CONSISTENT_HEUN` | **kept — it is the fix, not the failure** |
| `RD_DIFFERENCE_RESIDUAL` | kept; section 27 records an explicit decision to keep it |
| `RD_ALE_CONDITION_DIAGNOSTIC` | kept; a live diagnostic on the actual singular values |
| `RD_OUTPUT_DIAGNOSTICS` | kept; three print sites in `run.c`, outside this region |

`RD_RK2_RATE_CONSISTENT_HEUN` is the serious one. Section 12.2 of
`dev_log/LDA_F1_Heun_vs_standard_LDA_RK2.md` measures the Chapter-3 GL+F1
staging at `p ~ 0.99` on triangular, glass and jittered meshes and the
rate-consistent form at `p ~ 2.0003` on both a lattice and a glass. It carries
9 Configs across five test problems. **It was on the deletion list because the
hierarchical design document's phrase "mixed, coherent-beta-n, and
coherent-beta-star all retain the defect" was read as covering it. That
sentence is about the three beta conventions; the rate-consistent form is what
repaired the defect they failed to repair.**

### 37.4 An incident, and what it cost

Regenerating the initial conditions to add `IC_sodjit128` to the manifest
overwrote every family in place with no backup. Eight came back with different
bytes: `IC_greshojit48_b{0,1,3,10}`, `IC_khjit64`, `IC_yeejit{32,64,128}`. The
files had matched the committed manifest exactly beforehand, so this was not
pre-existing drift.

The generator is deterministic run to run and not reproducible across
environments. The split is clean: every family whose state uses transcendental
functions moved, every family built from arithmetic and comparisons alone
reproduced exactly. The cause is the last bit of `exp`, `sin` and `tanh` under
numpy 2.3.5. The originals are unrecoverable; the previous checksums survive in
the `MMRD_ICS.sha256` of commit `d8e74c5`.

The difference is about one unit in the last place, below every tolerance in
use, but it is not bitwise: any Yee, KH or Gresho case re-run now starts from a
slightly different initial condition, and the horizon rule of section 31.3
applies to particlewise comparison across that boundary.

Two changes so it cannot recur: the generator refuses to overwrite without
`--force`, and the manifest carries an environment stamp that `--verify`
reports on.

`IC_sodjit128` reproduced byte for byte, `51a5412f5bc9...`, which confirms
section 33.3's claim that the file was never contaminated.

### 37.5 What the cleanup actually found

Untracked entries fell from 112 to 7 and 332 MB was recovered, but the number
that matters is different. **P4, open since section 14.2, is closed**: the
entire Galilean campaign of sections 23, 25, 27, 28 and 30 had been run from
Configs and parameter files that existed only in one working tree, and an
actual regression test, `tests/rd/test_lda_f1_rank_deficiency.py`, was
untracked and so could not have been run by anyone but its author.

Six initial conditions remain outside any manifest, all from `create.py`, whose
parameters are module-level globals. Two of them, `IC_gresho_v0_glass48` and
`IC_gresho_v1e-8_ring48`, are referenced by `param_RD.txt` and
`param_StaticMesh.txt` and still need coverage.

### 37.6 The pattern

Three of the errors in this pass — overwriting a tracked `.gitignore` instead
of extending it, overwriting the initial conditions without a backup, and
putting the temporal-order fix on a deletion list — are one mistake: **acting
on a summary without opening the thing being changed.** The first two had
already been paid for by the time they were noticed. The third was caught only
because the switch had its own analysis document and it was opened first.

The `b_T` parameterisation of section 34.4 is an enabling change, so section
37.2 says the preprocessor will certify nothing about it, and section 37.1 says
the derivation will not either. The derivation should be written and reviewed
before the code is touched, not alongside it.

---

## 38. 2026-08-17: completion of the cleanup safeguards

- **Author:** Codex, continuing the section 37 implementation review.
- **Scope:** make the Gresho IC workflow reproducible and auditable, make the
  co-moving switch scheme-neutral, and add the missing N-frame regression.
- **Status:** implemented and locally verified in the working tree; not yet
  committed. No numerical default or production Config choice is changed.

### 38.1 IC generation and manifests are now fail-closed

`examples/gresho_2d/create.py` is now a command-line generator rather than a
file of module-level choices. Ring remains the default, but mesh family,
resolution, bulk velocity, output directory and the glass input are explicit.
The non-portable SWIFT glass path is gone: glass generation requires
`--glass-file` or `GRESHO_GLASS_FILE`. Existing HDF5 files are protected unless
`--force` is supplied, and plotting can be disabled with `--no-plot` so the
generation path has no matplotlib dependency.

The eight legacy `create.py` files that section 37.5 left outside the MMRD
manifest are covered by `GRESHO_LEGACY_ICS.sha256`. Two representative
reproductions were checked in a temporary directory: the default
`IC_gresho_v1e-8_ring48.hdf5` and the externally seeded
`IC_gresho_v0_glass48.hdf5` both reproduced their stored hashes exactly.

`create_mmrd_ics.py --verify` now checks every `*_ICS.sha256` in the example
directory and also scans in the reverse direction: an `IC_*.hdf5` with no
manifest entry is an error. A temporary unmanifested probe was detected with a
non-zero exit status. Manifest replacement is separate from generation behind
`--update-manifest`, which refuses an incomplete generated set. The environment
stamp is explicitly diagnostic; it is not presented as a portability
guarantee for transcendental initial conditions.

### 38.2 The frame switch now names the operation rather than one scheme

`RD_LDA_COMOVING_FRAME` is renamed to `RD_ELEMENT_COMOVING_FRAME` in the live
source, option lists and retained example Configs. The old name no longer
occurs in live build inputs. This is a naming correction only: section 37.1's
N-state rebase remains the substantive enabling change, and no production
default has been selected by the rename.

### 38.3 N plus contour has an algebraic Galilean regression

`tests/rd/test_n_frame_covariance.py` exercises a non-uniform positive Euler
state with non-zero mesh and unrelated frame velocities. It checks the
similarity of both split K matrices, the N inflow state, the raw N
distribution, the ALE contour total, and the reconciled distribution

    phi_i = phi_i^N + (Phi_contour - sum_j phi_j^N) / 3.

The test deliberately requires a non-zero reconciliation correction, so it
cannot pass by exercising only a uniform or already-conservative special case.
All covariance and conservation defects are at `O(10^-15)`. `make check_rd`
now runs this test after the existing LDA/F1 rank-deficiency regression and
does not require a generated `Config.sh` merely to run the Python checks.

### 38.4 Verification boundary

Both the N and LDA variants of `residual_distribution_solver.c` compile to an
object with the locally installed LAPACKE-compatible Eigen header. The normal
full build on this host still stops at `<lapacke.h>` because the system
LAPACKE development header is absent; therefore no successful full link is
claimed. Independently, both Config branches pass `make check`, their relevant
preprocessed branches are valid, all IC manifests verify, Python files compile,
the two RD algebraic tests pass, and `git diff --check` is clean.

The seven unrelated untracked files present at the start of this pass were
left untouched.

---

## 39. 2026-08-17: small moving-mesh N campaign

- **Author:** Codex, at Zhenyu's request.
- **Question:** can the final N combination reproduce the useful parts of the
  earlier LDA campaign without repeating the full option matrix?
- **Candidate:** Arpaia modified mass + conservative-state contour total +
  element co-moving frame + N distribution, equal timesteps.
- **Scope:** one rank; Gresho through boost 10, Sod, a shortened KH, and the
  complete (32,64,128) Yee ladder. This is deliberately not a new
  Roe/contour/Campoli matrix.
- **Archive:** `Hydro_data_analysis/Data_MMRD_debug/N_contour_cm_small_20260817`.

Two MKL-linked immutable binaries were used. The gamma-(5/3) artifact has
SHA256 `a52ba897f7d5...`; the gamma-1.4 artifact has
`a296a54031aa...`. The latter is defined reproducibly by the new
`examples/gresho_2d/Config_FS_con_cm_N.sh`; it differs from the retained
gamma-1.4 LDA candidate only by selecting N.

### 39.1 Gresho: the LDA boost-10 result transfers to N

The short (n=48, t=0.02) gate completed at boosts 0, 3 and 10. Against the
de-boosted boost-0 result, boost 10 gives

| field | L1 | Linf |
| --- | ---: | ---: |
| coordinates | (1.09e-16) | (1.55e-15) |
| velocity | (5.12e-15) | (4.90e-14) |
| density | (8.01e-15) | (3.95e-14) |
| pressure | (2.93e-14) | (1.38e-13) |
| internal energy | (8.52e-14) | (4.57e-13) |

This matches the scale of section 27.3's LDA result and independently exercises
the N state rebase whose omission section 37.1 found.

The same three cases were extended to (t=0.1). Every run used exactly 512
steps and 526 edge flips. All three give the same particle-level
volume-weighted azimuthal-velocity error, (3.593461342e-3), and the same peak,
(0.9754431137), to every printed digit. At boost 10 the de-boosted velocity
difference from boost 0 remains (L1=2.03e-14), (Linf=5.67e-12).

The laboratory conserved-ledger changes appear boost dependent, as they must
when a common mass defect is multiplied by the boost. Transforming them back
to the vortex frame gives the same vector for all three runs:

    d(M, px, py, E)' =
      (1.067046e-6, -3.310821e-5, 3.166655e-6, -1.022188e-4).

Thus the residual and its topology error are Galilean covariant; the non-zero
ledger change is not a frame defect.

### 39.2 Sod and KH: N retains the robustness that LDA lacks

Sod (n=64) completed to (t=0.2), through 658 steps and 4667 flips. Minimum
((m,rho,p,u)) was
((9.97e-6,0.3233,0.3049,1.705)); no pulled-back inversion, non-positive
midpoint, or non-positive Arpaia divisor occurred. Its 200-bin density total
variation is (1.5268046), against (1.5268044) in the old laboratory-frame
contour-N run. Particle differences are small in the mean
((L1(rho)=9.6e-8)) but not bitwise after thousands of topology decisions.

KH (n=64) was deliberately shortened from (t=2) to (t=0.2). It completed
512 steps and 2507 flips with minimum
((m,rho,p,u)=(1.11e-4,0.9853,2.370,3.102)) and the same clean geometry
counters. This is already about 800 times beyond the (t=2.4e-4) failure of
laboratory-frame LDA and confirms that the newly enabled co-moving N path did
not lose N's robustness. It is not a replacement for the old full-(t=2) N
result.

The endpoint ledger is not round-off on these discontinuous, heavily flipping
meshes:

| case | dM | dpx | dpy | dE |
| --- | ---: | ---: | ---: | ---: |
| Sod, (t=0.2) | (-4.82e-4) | (-4.17e-6) | (1.64e-5) | (-1.06e-3) |
| KH, (t=0.2) | (1.49e-4) | (3.87e-5) | (-3.59e-6) | (4.33e-4) |

This is the section 20 topology ledger defect amplified by discontinuities.
Completion and positivity must not be reported as exact conservation.

### 39.3 Yee: the expected boundary between N and LDA

At (t=1), using the same volume-weighted density error against the analytic
steady vortex:

| scheme | n=32 | n=64 | n=128 | orders |
| --- | ---: | ---: | ---: | --- |
| N, contour + co-moving | (4.118e-3) | (2.441e-3) | (1.372e-3) | 0.75, 0.83 |
| LDA campaign, section 33.2 | (2.290e-3) | (7.356e-4) | (2.252e-4) | 1.64, 1.71 |

All N runs complete with positive density and pressure. N is 1.8, 3.3 and 6.1
times less accurate as the grid is refined. That is not a regression: it is the
expected first-order character of the monotone N distribution. N reproduces
LDA's moving-mesh geometry, boost-10 covariance and discontinuous robustness
gates, but it cannot reproduce LDA's smooth-flow order and should remain the
robust control rather than the accuracy default.

The Yee endpoint ledger also remains topology limited; for example
(dM=(-2.93e-3,2.81e-4,8.10e-5)) at (n=(32,64,128)). The signs fluctuate, so
these three deterministic samples are not a new convergence-order estimate.

### 39.4 Decision from the small campaign

No new option matrix is justified. The final N combination is now end-to-end
validated for the role assigned to it:

1. a frame-covariant boost-10 control;
2. a positive/robust Sod and KH control;
3. a first-order smooth-flow baseline for LDA.

The useful next N experiment is the previously designed zero-seed KH
static-versus-moving noise-floor test. Full (t=1) Gresho, full (t=2) KH,
MPI, and a second boost ladder are not required before that targeted test.

## 40. 2026-08-17: long N runs and visual solution-quality audit

The short campaign in section 39 was deliberately extended after visual
solution quality was judged more informative than another broad switch
matrix.  Every plot and run in this section uses the same moving-mesh form:

    N_SCHEME + RD_ALE_EQUALSTEP + RD_ALE_CONTOUR_RESIDUAL
             + RD_ELEMENT_COMOVING_FRAME + RD_ALE_CFL_TIMESTEP,

with Arpaia's modified-midpoint mass and the P1(U) contour total in the
element frame,

    Phi^T = 1/2 sum_j [ F(U_j).n_j - (sigma_bar_T.n_j) U_j ],
    phi_i = phi_i^N + (Phi^T - sum_j phi_j^N)/3.

The gamma-5/3 and gamma-1.4 binaries are the same immutable artifacts used in
section 39.  The complete archive is
`/home/zwu/Hydro_data_analysis/Data_MMRD_debug/N_contour_cm_small_20260817`.

### 40.1 Gresho to t=1: strong boost invariance, visible N diffusion

The n=48 boost-0, boost-3, and boost-10 runs all reached t=1 in exactly 4096
steps and 6836 edge flips.  No pulled-back inversion, non-positive midpoint,
or non-positive Arpaia divisor was reported.  Their volume-weighted azimuthal
velocity errors are

| boost | L1(v_phi) | peak v_phi |
| ---: | ---: | ---: |
| 0 | 1.980441224e-2 | 0.8557168 |
| 3 | 1.980445436e-2 | 0.8557168 |
| 10 | 1.980430118e-2 | 0.8557168 |

The three profiles are visually indistinguishable, and their L1 errors vary
by less than 1e-5 relatively.  Thus boost 10 remains successful over a long
run, not merely at the section-39 short gate.  Particle-ID equality is no
longer at round-off because nearly seven thousand flip decisions amplify tiny
trajectory differences.  After de-boosting, boost 10 versus boost 0 gives

| field | L1 | Linf |
| --- | ---: | ---: |
| coordinates | 7.884e-8 | 1.211e-5 |
| velocity | 8.033e-7 | 2.023e-4 |
| density | 2.428e-7 | 7.511e-5 |
| pressure | 2.049e-6 | 6.928e-4 |

This is topology-sensitive trajectory branching, not a visible failure of
the Galilean profile.  The frame-transformed endpoint ledgers are also close;
for boost 0 and boost 10 respectively,

    dQ'_b0  = (4.73561e-5, -8.08133e-6, 1.98958e-5, -9.25894e-4),
    dQ'_b10 = (4.73687e-5, -8.01827e-6, 1.98636e-5, -9.25809e-4).

The solution-quality verdict is less favourable.  The peak has fallen to
about 0.856, while the previous long LDA run had L1 about 7.84e-3 and peak
about 0.934.  N therefore preserves the boost behaviour but not LDA's lower
diffusion.

### 40.2 KH to t=2: robust completion with a thickened interface

The n=64 KH run reached t=2 in 8192 steps and 33444 edge flips, safely past
the co-moving LDA failure near t=0.98.  It retained positive geometry and
thermodynamics throughout.  At the endpoint,

    min(m,rho,p,u) = (9.2928e-5, 0.88798, 2.34028, 2.98554),
    max(rho,p)     = (2.11694, 2.64664),
    dQ             = (6.1126e-4, 6.8368e-4, 3.1817e-4, 3.3153e-4).

The transverse kinetic energy grows from 3.74988e-3 to 4.40126e-3, so the
perturbation does develop.  The density image contains rolled-up, multiscale
structure, but the shear layers are visibly broad; density standard deviation
falls from 0.47431 to 0.39953.  N is a robust control here, not evidence for
LDA-level resolution.

Against the old laboratory-frame contour-N t=2 snapshot, the new co-moving
run differs materially (L1 velocity 1.122e-2 and L1 density 2.444e-2).  This
late-time chaotic/topology-sensitive comparison is not a clean frame-
covariance test and should not be interpreted as one.  The short Gresho
boost ladder remains the controlled covariance diagnostic.

### 40.3 Figures and revised conclusion

The reproducible plotting script is
`examples/gresho_2d/plot_n_moving_campaign.py`.  It writes both PNG and PDF
versions of the summary and the individual Gresho, Sod, KH, and Yee figures
under the archive's `figures/` directory.  Every figure labels both the
mathematical ALE form and the exact compile switches, avoiding an ambiguous
generic "moving mesh" caption.

The long visual audit sharpens, rather than changes, section 39's decision:

1. contour + element co-moving frame + Arpaia mass is a successful boost-10
   and long-time robustness configuration for N;
2. N does not reproduce LDA's Gresho or Yee accuracy and is substantially
   more diffusive, as expected for the first-order monotone distribution;
3. the non-round-off topology ledger defect remains present and must not be
   hidden by the successful completion;
4. N should be kept as the robust first-order control.  Arpaia remains the
   moving-mesh default, while accuracy work should continue on the
   contour/frame mathematics and LDA rather than tuning N to imitate LDA.

## 41. 2026-08-18: matched LDA KH audit and Morton-2023 Sod benchmark

The visual interpretation of section 40 is accepted: the long N Gresho result
is consistent with the known first-order N dissipation even at boost zero and
on a static mesh.  It is better than a heavily diffusive particle method but is
not expected to match LDA or AREPO's MMFV result.  The KH run is correspondingly
blurred, although its large-scale symmetry remains reasonable.  The useful
question is therefore not whether N can be tuned to look like LDA, but whether
moving LDA can retain its accuracy advantage in a matched long calculation.

The archives for this section are

    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/LDA_KH_static_moving_20260818
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/Morton2023_Sod_ALE_20260818

### 41.1 Matched n=64 LDA KH: moving is not yet a long-time improvement

All three LDA runs use the same smooth-interface IC, gamma=1.4 and RK2.  The
static control uses the K-matrix total; the moving cases use Arpaia's
modified-midpoint mass, the element co-moving frame and either the Roe-plus-
mesh-split total or the P1(U) contour total.  The completed co-moving contour-N
run from section 40 is included as a robustness reference.

At the matched t=0.2 snapshot the four calculations are nearly
indistinguishable in global KH amplitude:

| case | E_kin,y | reflected density L1 | rho range |
| --- | ---: | ---: | ---: |
| static LDA, K-matrix total | 2.7649e-3 | 4.4949e-2 | 0.9826--2.0434 |
| moving LDA, Roe + mesh split | 2.7888e-3 | 4.3897e-2 | 0.9824--2.0428 |
| moving LDA, P1(U) contour | 2.8008e-3 | 4.4871e-2 | 0.9715--2.0433 |
| moving N, P1(U) contour | 2.7998e-3 | 4.0746e-2 | 0.9853--2.0462 |

These small differences do not establish a moving-mesh accuracy advantage.
The contour-LDA interface is already slightly more mesh-ragged at the common
time.  More importantly, the long-time outcomes are qualitatively different:

| case | last saved time | endpoint | rho range at last snapshot |
| --- | ---: | --- | ---: |
| static LDA | 2.0 | completed | 0.8605--2.3433 |
| moving LDA, Roe + mesh split | 1.0 | negative endpoint mass at 1.0079346 | 0.1923--4.0795 |
| moving LDA, P1(U) contour | 0.2002 | negative endpoint mass at 0.32582092 | 0.9715--2.0433 |
| moving N, P1(U) contour | 2.0 | completed | 0.8880--2.1169 |

The static LDA run develops clean large vortices and completes.  The moving
Roe-LDA solution has severe mesh-scale extrema before it fails, while the
contour-LDA run fails too early for a nonlinear-stage comparison.  The moving
N run completes but its interface is thick and fragmented, as expected from
the monotone first-order distribution.  At t=2 the reflected-density metric is
0.131 for static LDA and 0.162 for moving N; this approximate nearest-generator
diagnostic gives no evidence that moving N is more symmetric at late time.

Thus the answer to "is long-time moving LDA better than static LDA?" is
currently no: not because the moving formulation is demonstrably more
diffusive, but because its topology/Arpaia endpoint-mass failure prevents the
comparison.  The Roe-plus-split branch does not rescue the result, so no more
parameter sweep of that branch is warranted.  The next focused KH test should
be the already proposed zero-seed static-versus-moving noise-floor comparison,
followed by a positivity/topology diagnosis for LDA rather than N tuning.

### 41.2 Morton et al. (2023) Sod protocol reproduced

The previous gamma=1.4, unit-box moving-N Sod run was a robustness smoke test,
not a reproduction of Morton et al. (2023), section 5.1.1 and figure 7.  The new
published controls use the actual pseudo-1D protocol:

1. periodic 2 x 2 box with an n x n row-offset uniform generator lattice;
2. (rho,v,p)_L=(1,0,1), (rho,v,p)_R=(0.125,0,0.1), gamma=5/3;
3. central high-state slab, giving the two periodic Riemann fans in the paper;
4. Courant factor 0.4, endpoint t=0.2, and n=64 and 128;
5. first-order static LDA and N distributions with the K-matrix total.

Both published controls complete and retain pseudo-1D symmetry at round-off.
Their profiles reproduce the expected first-order smeared shock/contact and
the close LDA1/N1 agreement.  The volume-weighted errors against the exact
periodic Riemann solution are

| scheme | L1(rho), n=64 | L1(rho), n=128 | two-level order | L1(vx), n=128 | L1(p), n=128 | RMS(vy), n=128 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| static LDA1, Morton form | 3.7653e-2 | 2.5843e-2 | 0.543 | 5.0003e-2 | 2.3176e-2 | 1.45e-16 |
| static N1, Morton form | 3.8303e-2 | 2.6710e-2 | 0.520 | 5.0861e-2 | 2.4433e-2 | 1.68e-16 |
| moving LDA RK2, contour + co-moving | 2.5546e-2 | 1.8622e-2 | 0.456 | 8.5572e-2 | 2.2640e-2 | 2.86e-2 |
| moving N RK2, contour + co-moving | 3.3132e-2 | 2.4169e-2 | 0.455 | 5.5973e-2 | 2.9284e-2 | 5.29e-3 |

The moving rows are an ALE extension, not part of Morton's published figure.
An exactly regular moving lattice is massively co-circular and failed at the
second AREPO triangulation with an invalid coordinate range.  The preserved
failure is under `output_regular_mesh_failure`.  A deterministic 1e-6 h
coordinate jitter was therefore applied only to the moving extension; the
published static controls retain the exact regular lattice.

All four moving runs then complete, but their interpretation differs.  Moving
N remains bounded: at n=128, min(rho,p)=(0.12508,0.10011), and its transverse
noise decreases from 1.06e-2 to 5.29e-3 as resolution doubles.  It is a useful
robust ALE shock control, although not uniformly more accurate than static N.

Moving LDA's smaller density L1 is misleading.  At n=128 it produces
min(rho,p)=(0.01487,0.04582), rho_max=1.0291, RMS(vy)=2.86e-2, and its velocity
L1 worsens slightly from n=64 to n=128.  The profile contains strong dispersive
ringing around the shocks and contacts.  This is the expected lack of a
monotonicity/positivity mechanism in pure LDA, not an accuracy win for the ALE
form.  A blended/limited distribution will eventually be required for shocks;
the present result should first remain a diagnostic of the unmodified schemes.

### 41.3 Priority defect: moving-mesh oscillation amplification and loss of the static-LDA robustness envelope

The Sod result must not be dismissed as the familiar statement that pure LDA
is non-monotone.  Earlier static-mesh Sod calculations did show an LDA1
oscillation, but it was localized mainly near the rarefaction/contact region,
was much less prominent in the Morton-2023 presentation, and was removed in
the experimental Bx1 calculation by the shock-sensor blend.  That historical
result establishes the expected baseline: a limited local LDA defect for which
the existing Bx mechanism is effective.

The present ALE behaviour is qualitatively more severe:

1. moving contour-LDA at n=128 reaches rho_min=0.01487 from a physical minimum
   of 0.125, develops large ringing in density, velocity and pressure, and has
   transverse RMS velocity 2.86e-2;
2. moving N also develops visible discontinuity-correlated and transverse
   oscillation even though the corresponding static N result is essentially
   one-dimensional and monotone; its bounded extrema therefore do not make the
   oscillation expected or acceptable;
3. the effect is shared by two distributions with very different monotonicity
   properties, so it cannot be attributed to the LDA distribution alone;
4. in KH, both moving Roe-plus-split LDA and moving contour-LDA terminate with
   negative endpoint mass, whereas the matched static LDA calculation reaches
   t=2.  The contour formulation fails earlier, but the Roe branch failing as
   well shows that this is not merely one contour-quadrature pathology.

This is now a **priority moving-mesh defect**, not a secondary limiter-tuning
issue.  LDA is not required to be as robust or as monotone as N, but mesh motion
must not move a problem outside the established static-LDA robustness envelope
without a diagnosed mathematical reason.  In particular, a test that static
LDA completes must not fail solely after enabling the ALE residual, co-moving
frame and Arpaia mass update.

The investigation should isolate the common ALE machinery before applying Bx,
because an early blend could hide rather than explain the defect.  The focused
diagnostics are:

1. locate the first departure from the static Sod profile and correlate it
   element-by-element with edge flips, temporary/endpoint mass ratios, and the
   Arpaia Q-to-U storage rewrites;
2. separate continuous generator motion from topological change using a
   short-time fixed-connectivity or no-flip diagnostic, then re-enable flips at
   the same state;
3. compare static and moving N at every RK stage.  Since N should supply the
   monotone control, its first oscillatory stage is the cleanest indicator of a
   contour total, frame transform, geometric-conservation, mass-ledger or time-
   integration error shared with LDA;
4. repeat the earliest failing window with Euler versus RK2 and a small CFL
   ladder, recording whether the disturbance is temporal, topological, or
   approximately step-size independent;
5. only after the common ALE contribution is understood, restore Bx and verify
   that the shock sensor removes the residual local LDA ringing without being
   asked to stabilize an underlying mesh/ledger defect.

Minimum acceptance criteria are correspondingly stronger than completion:

- moving N Sod must remain bounded and approach the static-N pseudo-1D profile,
  with transverse noise decreasing under refinement and without O(1) spikes;
- moving LDA may retain its known local rarefaction/contact ringing, but it must
  not create near-vacuum states or materially amplify the static-LDA extrema;
- both moving LDA residual forms must carry the matched KH test at least through
  the time interval completed by static LDA, unless a separately justified
  positivity limiter is triggered rather than an endpoint-mass termination;
- Bx is evaluated only after these ALE baselines pass, and is not counted as a
  cure if it merely masks mass/topology inconsistency.

This defect takes priority over the zero-seed KH noise-floor experiment and
over further Roe-versus-contour parameter sweeps.  The latter become meaningful
again only after the shared moving-Sod oscillation and KH endpoint-mass failure
have been localized.

### 41.4 Reproducibility and decision

The preparation and plotting entry points are

    examples/gresho_2d/prepare_lda_kh_comparison.py
    examples/gresho_2d/plot_lda_kh_comparison.py
    examples/shocktube_2d/create_morton2023.py
    examples/shocktube_2d/plot_morton2023.py

The figures explicitly distinguish the published static Morton controls from
the Arpaia + P1(U) contour + element-frame ALE extension.  The combined verdict
is:

1. keep Arpaia + contour + co-moving frame as the intended moving-mesh default;
2. keep N as the robust first-order discontinuous-flow control;
3. do not infer ALE-LDA improvement from density L1 alone, because the Sod
   extrema and transverse noise expose a non-monotone solution;
4. resolve the LDA endpoint-mass/topology failure before claiming that moving
   LDA improves long-time KH over static LDA;
5. use Morton's static first-order LDA/N profiles as the published regression
   baseline and label every ALE result explicitly as an extension.

## 42. 2026-08-18: glass rerun supersedes jittered meshes for the ALE verdict

Section 41 used Morton's regular row-offset mesh for the published static
controls and a 1e-6 h jitter of that lattice for the ALE extension.  That was
not an appropriate production moving-mesh comparison.  An infinitesimal jitter
removes exact co-circularity but preserves a highly structured, nearly
degenerate Delaunay topology.  It is useful as a geometry stress test, not as a
proxy for the meshes used in astrophysical simulations.

The rule from this point forward is:

1. relaxed periodic glass is the default IC geometry for physical moving-mesh
   tests and static-versus-moving decisions;
2. static and moving variants use exactly the same normalized generators and
   ParticleIDs;
3. regular, row-offset and jittered lattices are retained only for published
   reproduction or explicitly labelled geometry stress tests;
4. conclusions from section 41 that depend on the magnitude of lattice/jitter
   oscillations are superseded by this section.  Morton's regular static result
   remains a valid reproduction of the paper, but its jittered ALE extension is
   not the astrophysical-mesh baseline.

### 42.1 Matched glass construction

The rerun uses the manifest-covered relaxed SWIFT glass
`IC_gresho_v0_glass48.hdf5`: 2304 generators, effective n=48, source SHA256

    da76535f6f6366fa8d9b43d3e27f0f8b1bdfb461eead3c2d80aed401c935df64.

For Sod the normalized points are scaled to a periodic 2 x 2 box; for KH they
remain in the unit box.  Every scheme for a given problem uses identical
coordinates and IDs.  No random displacement or lattice jitter is added.

The campaign archive is

    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/Glass_Sod_KH_ALE_20260818

and the reproducible entry points are

    examples/shocktube_2d/prepare_glass_sod_kh.py
    examples/shocktube_2d/plot_glass_sod_kh.py

### 42.2 Sod on glass: the lattice amplified the defect, but did not create all of it

All four glass Sod cases reach t=0.2.  The exact Morton fluid states, gamma=5/3
and CFL=0.4 are retained, but this is explicitly a glass extension rather than
Morton's published regular geometry.

| scheme | L1(rho) | L1(vx) | L1(p) | rho range | p range | RMS(vy) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| static LDA1 | 4.6435e-2 | 1.0382e-1 | 4.9790e-2 | 0.1486--0.9948 | 0.1348--0.9913 | 1.096e-2 |
| static N1 | 4.6588e-2 | 1.0198e-1 | 5.1054e-2 | 0.1486--0.9944 | 0.1350--0.9907 | 8.490e-3 |
| moving LDA, contour + frame | 3.0156e-2 | 9.0402e-2 | 3.9872e-2 | 0.0764--1.0294 | 0.0409--1.0496 | 2.010e-2 |
| moving N, contour + frame | 3.8859e-2 | 1.1033e-1 | 5.4722e-2 | 0.1393--0.9924 | 0.1202--0.9874 | 1.424e-2 |

The interpretation is more precise than section 41's jitter result:

- moving N is bounded on the glass and its point cloud is much closer to the
  expected monotone control.  The very strong lattice-jitter spikes must not be
  generalized to production meshes;
- nevertheless, moving N has 1.68 times the transverse RMS velocity of static
  N on the identical glass, so a smaller shared ALE noise increment remains;
- moving LDA is also substantially improved relative to the jittered n=128
  stress test, but still undershoots the physical minimum 0.125 to 0.0764 and
  pressure to 0.0409.  Its transverse RMS is 1.83 times static LDA and the
  density/pressure profiles retain visible dispersive extrema;
- therefore the extreme rho_min=0.0149 of section 41 was partly a structured-
  mesh artifact, while the moving-LDA amplification relative to its matched
  static glass control is real.

Glass itself is not pseudo-one-dimensional, so non-zero static RMS(vy) is an
expected geometry noise floor.  The relevant diagnostic is the moving/static
increment on the same glass, not comparison with round-off symmetry on a
regular lattice.  Higher-resolution glass families are required before quoting
a convergence rate for that increment.

### 42.3 KH on glass: both moving-LDA failures persist

The n=48-equivalent glass KH rerun gives an unambiguous robustness result:

| scheme | outcome | failure/endpoint detail | latest saved rho range |
| --- | --- | --- | ---: |
| static LDA RK2 | completed t=2 | reference completes | 0.8415--2.7684 at t=2 |
| moving LDA, Roe + split + frame | failed t=1.15515 | RK predictor rho=-0.01790 | 0.3060--2.3033 at t=1 |
| moving LDA, contour + frame | failed t=0.46442 | negative endpoint mass; predictor rho approached 1.84e-5 | 0.4080--2.1331 at t=0.4001 |
| moving N, contour + frame | completed t=2 | bounded robust control | 0.9090--2.0796 at t=2 |

At the matched t=0.2 snapshot, static LDA and moving Roe-LDA remain close:
their rho minima are 0.9688 and 0.9817.  Contour-LDA is already less controlled,
with rho_min=0.8574, while moving N has rho_min=0.9856.  The contour failure is
therefore preceded by a visible early extremum, not a purely silent bookkeeping
termination.

The glass improves both LDA failure horizons compared with the jittered
campaign, but does not change the scientific verdict.  Static LDA completes;
both moving LDA totals fail; moving N completes.  The contour failure is an
endpoint-mass event, while the Roe failure is a non-physical RK predictor, so
the common concern is broader than contour quadrature alone.  Because the
result persists on a relaxed production-style glass, it is a genuine ALE
robustness regression and remains the highest-priority defect.

### 42.4 Revised work order

1. Use the glass Sod campaign to locate the first moving/static departure,
   including the smaller but measurable N noise increment.
2. Correlate the glass contour-KH failure with temporary and endpoint masses,
   topology changes, and the element that reaches near-vacuum.
3. Diagnose Roe-KH separately at the RK predictor, since its glass failure is
   not an endpoint-mass check.
4. Do not use Bx to mask either common ALE defect.  Once N and the mass/frame
   machinery pass, Bx can be restored for the residual local LDA oscillation.
5. Acquire or generate relaxed glass96/glass128 families before drawing
   resolution-scaling conclusions.  Do not substitute jittered lattices for
   those missing glass resolutions.

## 43. 2026-08-18: robustness limiter and first ALE-isolation controls

The immediate engineering priority is now to keep the moving solver running,
but the scientific priority is to distinguish an LDA monotonicity defect from
an error in the moving-mesh construction.  A B/Bx-style blend is analogous to
the limiter used by a moving-mesh finite-volume method: it may make an
otherwise correct high-order update admissible, but success after limiting is
not evidence that the unlimited ALE operator is correct.

### 43.1 Classical component-wise B is not a positivity mechanism

The existing conservative N/LDA B implementation was enabled experimentally
for `RD_ALE_EQUALSTEP + RD_ALE_CONTOUR_RESIDUAL +
RD_ELEMENT_COMOVING_FRAME`.  Both branches are built and reconciled to the
same contour total in the element frame and mapped back only after blending.
This is an experimental diagnostic path, not the default scheme and not the
historical shock-sensor Bx.

On glass KH, the component-wise B scheme delayed the contour-LDA negative-mass
failure from t=0.46442 to t=0.81845, but still terminated with one negative
endpoint mass.  Immediately beforehand the RK predictor remained positive
(rho_min=1.12e-4, p_min=2.171), while the final stored mass of ID 971 became
-2.53e-8.  The mean total-residual theta was only 0.2649 and 2.94% of the
component samples were in the theta=1 histogram bin.  Component-wise B can mix
density from one branch with momentum and energy from another and therefore
has no invariant-domain interpretation.

`RD_B_SCALAR_THETA` was added as a stricter diagnostic: each element uses

    theta_T = max_k theta_{T,k}

for all conserved components in both the predictor and the coherent RK2 total
residual.  This retains element conservation and the full state-vector
coupling.  It completed glass KH to t=2, with rho=0.8344--2.1331 and
p=2.3443--2.6148.  However, mean theta_T rose to 0.761 at t=2, with 38.4% of
samples in the theta=1 bin.  The run survives primarily by becoming strongly
N-like; scalar B is a useful robustness safety path, not an explanation of the
underlying failure.

Glass Sod at t=0.2 gives the same distinction:

| scheme | L1(rho) | L1(vx) | L1(p) | rho range | p range | RMS(vy) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| moving component-B | 2.5595e-2 | 6.4524e-2 | 3.1839e-2 | 0.1253--1.0000 | 0.1004--1.0000 | 1.865e-2 |
| moving scalar-B | 2.7064e-2 | 7.2935e-2 | 3.5515e-2 | 0.1255--0.9999 | 0.1007--0.9998 | 1.472e-2 |

Both B variants remove the large LDA undershoot, but their non-zero transverse
noise remains comparable to the moving-N floor.  This is limiter evidence, not
an ALE validation.

### 43.2 Zero-mesh ALE separates storage from actual mesh motion

The first isolation test uses identical glass Sod ICs and N-RK2 in two forms:

1. a true static mesh;
2. mesh velocity forced to zero while retaining `RD_ALE_EQUALSTEP`, Arpaia
   modified-midpoint dual masses, contour residual and endpoint storage.

At t=0.2 the results are close:

| control | L1(rho) | L1(vx) | L1(p) | RMS(vy) |
| --- | ---: | ---: | ---: | ---: |
| static N-RK2 | 4.6794e-2 | 1.0149e-1 | 5.1082e-2 | 8.487e-3 |
| zero-mesh ALE N-RK2 | 4.6602e-2 | 1.0101e-1 | 5.0788e-2 | 8.574e-3 |
| moving ALE N-RK2 | 3.8859e-2 | 1.1033e-1 | 5.4722e-2 | 1.424e-2 |

The stationary ALE/storage path does not reproduce the moving-N noise.  The
small zero/static difference is consistent with their different contour versus
static K-matrix spatial totals and is far below the actual moving/static
increment.

Setting `CellShapingSpeed=0` while retaining the normal quasi-Lagrangian mesh
velocity gives L1=(3.8659e-2, 1.1051e-1, 5.4693e-2) and RMS(vy)=1.444e-2,
essentially the regularised moving result.  By t=0.2 the regularised and
speed-zero runs have 332 and 329 replaced edges respectively.  Face-angle
regularisation velocity is therefore not the main cause.

### 43.3 Flip timing: topology is not the sole initiating mechanism

In the normal moving-N Sod run, the first edge replacement occurs at t=0.025.
Matched short controls were therefore stopped at t=0.02 (zero flips) and
t=0.03 (two flips).  Before any flip, moving versus zero-mesh RMS state
differences by ParticleID are already

    (rho, vx, vy, p) = (1.02e-2, 1.56e-2, 1.98e-3, 8.73e-3).

After two flips they grow to

    (rho, vx, vy, p) = (1.68e-2, 2.45e-2, 2.89e-3, 1.36e-2).

Part of a per-ID difference is expected because moving generators sample a
different material/spatial trajectory.  The symmetry diagnostic is more
direct: RMS(vy) is 1.841e-2 moving versus 1.820e-2 zero-mesh at t=0.02, and
1.951e-2 versus 1.904e-2 at t=0.03.  Thus smooth geometry motion changes the
solution before topology changes, while the two early flips do not create a
single discontinuous failure.  Flips may still amplify the late-time defect,
but they are not its sole origin.

### 43.4 Current conclusion and next discriminator

The evidence no longer supports treating this as only an LDA problem.  Static
LDA completes KH, moving N has excess Sod noise, stationary ALE N is close to
static N, and disabling regularisation does not remove the moving result.  The
remaining common suspect is the coupling among actual geometry motion,
time-dependent dual masses and the ALE residual/update.  The next tests should
be, in order:

1. a prescribed rigid translating glass with unchanged connectivity, which
   exercises non-zero b_T and the frame/contour algebra without dual-area
   deformation;
2. a smooth prescribed deforming velocity field stopped before the first flip,
   to test the Arpaia mass identity independently of topology;
3. per-step tracking of the worst Sod/KH cell, including m_i^n, bar m_i,
   m_i^{n+1}, contour correction and adjacent flip patches;
4. only after these controls pass, design a conservative a-posteriori
   positivity limiter (or shock-sensor Bx) for the residual LDA oscillation.

---

## 44. 2026-08-18: the Sod "moving-mesh defect" is mostly the time integration; the N part is real and quantified

- **Author:** Claude Code (Opus 5), reviewing sections 38-43.
- **Scope:** an offline calculation of how upwind dissipation depends on the
  mesh velocity, plus four new matched controls on the glass Sod.
- **Source change:** three Configs under `examples/shocktube_2d/`, one analysis
  script. No solver change.
- **Status:** sections 41.3 and 42 need revising; the work order changes.

### 44.1 The controls that were missing

Sections 41 and 42 compare `static LDA1` and `static N1` against
`moving LDA RK2` and `moving N RK2`. The published static controls are
**first order**: their Configs carry no `RD_RK2_TOTAL_RESIDUAL`. The moving
runs carry RK2+F1, the contour total, the element frame and the ALE mass. Three
things change at once, and the conclusion "mesh motion moved the problem
outside the static-LDA envelope" was drawn from that comparison.

Four controls close the gap, all on the identical glass, the identical IC and
2304 matched ParticleIDs:

| | `rho_min` | `RMS(v_y)` | x previous |
| --- | ---: | ---: | ---: |
| static LDA1, first order | 0.1486 | 1.0966e-2 | |
| **static LDA, RK2+F1** | **0.0711** | 1.9426e-2 | **1.77** |
| **zero-mesh ALE, RK2+F1** | 0.0740 | 2.0389e-2 | 1.05 |
| moving ALE, RK2+F1 | 0.0764 | 2.3514e-2 | 1.15 |
| static N1, first order | 0.1486 | 8.4938e-3 | |
| **static N, RK2** | 0.1497 | 8.4907e-3 | **1.00** |
| moving N, RK2 | 0.1393 | 1.5323e-2 | **1.80** |

The physical minimum density is 0.125.

**The LDA density undershoot is a static-mesh result.** RK2+F1 on a stationary
mesh reaches `rho_min = 0.0711`, a 43 per cent undershoot, which is *worse*
than the moving run. Mesh motion contributes a factor 1.15 in transverse noise
and slightly *improves* the minimum density. The ALE storage machinery with the
mesh held still contributes 1.05. **Section 41.3's first bullet, the
`rho_min = 0.01487` undershoot presented as an ALE defect, is a defect of
LDA+F1 RK2 that the first-order control could not show.**

**The N result is the opposite, and it is entirely mesh motion.** RK2 costs N
nothing at all -- 8.4907e-3 against 8.4938e-3, and `rho_min` even improves --
so the whole 1.80 is the moving mesh. Section 41.3's second bullet stands, and
Zhenyu's reading of the figures was right: moving N really does oscillate more
than static N, and it is not an LDA problem.

### 44.2 Where the N factor of 1.80 comes from

The ALE Jacobian is `A(n) - (sigma.n)I`, with eigenvalues
`u.n - sigma.n` twice (entropy and shear) and `u.n - sigma.n +- c`. At
`sigma = u` the first two vanish. Measured on one element of the Sod star
state, sweeping the frame velocity:

| `sigma/u` | entropy damping | shear damping |
| ---: | ---: | ---: |
| 0.00 | 1.000 | 1.000 |
| 0.50 | 0.500 | 0.777 |
| 0.90 | 0.100 | 0.599 |
| 1.00 | **0.000** | **0.554** |

The entropy vector `r = (1, u, v, |q|^2/2)` is the same for every direction, so
at `sigma = u` it lies in the kernel of **every** `K_j` of the element; direct
check gives `|K_j r|` of 2.5e-18, 2.5e-18, 8.7e-19 against 1.8e-2 on the static
mesh. The shear eigenvector rotates with `n`, so the three edge kernels do not
coincide and shear keeps 55 per cent of its damping.

**Predicted transverse-noise amplification is therefore `1/0.554 = 1.81`, and
the measured moving/static ratio for N is 1.80.**

The entropy annihilation is *not* an error and does no harm here: a contact
co-moving with the mesh is an exact steady state, so `Phi = 0` is correct. The
thermodynamic scatter confirms it. In the two star regions, where `p` and `u`
are constant, the moving mesh is *cleaner* than the static one:

| | pressure scatter (acoustic) | `p/rho^gamma` scatter (entropy) |
| --- | ---: | ---: |
| moving N / static N | x0.74 | x0.70 |
| moving LDA / static LDA | x0.52 | x0.68 |

The excess is confined to the transverse velocity, which is the shear mode.
An earlier draft of this analysis attributed the observable to the entropy
mode; the measurement above refuted that and is why it is recorded here.

Script: `Hydro_data_analysis/Analysis/moving_mesh/shear_mode_damping.py`.

### 44.3 The F1 rank-deficiency avalanche is not mesh-related

Section 43 did not examine `f1_lumped`, the count of elements whose F1 temporal
mass falls back to the lumped mass on a rank-deficient `S^-`. On the moving LDA
Sod it fires enormously in the first six steps -- 4027 elements out of roughly
4600 -- decaying to zero by `t = 0.019`, and the predictor minimum density drops
below the physical 0.125 inside exactly that window. That looked like the
mechanism.

It is not. The three runs give **identical counts**:

```
static LDA RK2    4027 3251 2477 1695 919 163   total 12532
zero-mesh ALE     4027 3251 2477 1695 919 163   total 12532
moving ALE        4027 3251 2477 1695 919 163   total 12532
```

The cause is the Sod initial condition: at `t = 0` the fluid is at rest, so the
Jacobian eigenvalues are `0, 0, +-c` and `S^-` is rank deficient by
construction, on any mesh. The avalanche is a startup transient of the test
problem, not a property of the ALE path. It remains worth attention as a
*static-mesh* LDA+F1 issue, and it is a candidate cause of the 0.0711
undershoot, but it is not evidence about mesh motion.

### 44.4 Kelvin--Helmholtz is properly controlled, and the finding stands

Unlike Sod, the KH controls of section 41.1 all carry `RD_RK2_TOTAL_RESIDUAL`,
so static and moving differ only in the mesh. The static run's generators were
checked directly and do not move: maximum displacement between the first and
last snapshot is exactly zero. Therefore

> static LDA RK2+F1 completes to `t = 2`, while moving LDA RK2+F1 fails at
> `t = 1.008` (Roe + split) and `t = 0.326` (contour),

**is a genuine moving-mesh result and is now the only one.** It is also not
explained by the factor of 1.8 above, which is far too small to turn a
completed run into a negative mass.

### 44.5 Revised reading, and the work order

Section 41.3 declared a "priority moving-mesh defect" on four bullets. After
these controls:

| bullet | status |
| --- | --- |
| 1. moving contour-LDA `rho_min = 0.01487`, large ringing | **reattributed**: static LDA RK2+F1 is worse |
| 2. moving N oscillates where static N does not | **stands**, x1.80, quantitatively explained by shear-mode damping |
| 3. shared by two distributions, so not LDA alone | **stands**, and 44.2 gives the shared mechanism |
| 4. both moving LDA branches fail KH where static completes | **stands**, and is now the priority |

The single defect therefore splits into three items with different owners:

1. **KH moving-LDA failure.** The real moving-mesh defect. Both residual forms
   fail, so it is not a contour-quadrature pathology.
2. **LDA+F1 RK2 positivity on a *static* mesh.** `rho_min` 0.1486 to 0.0711 at
   fixed mesh. This predates the ALE work and was hidden by comparing against a
   first-order control. The `f1_lumped` avalanche of 44.3 is the first suspect.
3. **The intrinsic Lagrangian shear-damping loss.** A factor 1.8 in transverse
   noise for any scheme, understood and quantified. The remedy is a floor on
   `|u - sigma|/c`; AREPO's `CellShapingSpeed` is exactly that knob and is
   currently switched off on round cells, which is where the loss is largest.

The `sigma`-fraction sweep proposed earlier is still the right next
measurement, because item 3 predicts a specific monotone curve while item 1
does not. But it should now be run on KH, not Sod, since Sod has turned out to
be dominated by item 2.

Every published number in sections 41 and 42 that compares a moving RK2 run
against a first-order static control needs the matched control before it is
cited. The controls added here cover the glass Sod only.

---

## 45. 2026-08-18: numerical entropy production separates every KH outcome

- **Author:** Claude Code (Opus 5).
- **Scope:** one diagnostic applied to the matched glass KH runs. No solver
  change, no new run: this uses snapshots already on disk.
- **Status:** it resolves section 44.5's item 1 and it bears directly on the
  residual-form decision of section 35.1.

### 45.1 An exact invariant, and why KH admits it

Section 44.6 localises the moving-mesh Sod excess to the contact and predicts
the entropy mode is responsible. Kelvin--Helmholtz can test that without any
profile fit, interface tracking or tunable window.

Its initial pressure is uniform and the flow is subsonic and shock-free, so the
specific entropy `s = p/rho^gamma` is materially conserved by the exact Euler
equations. **Its range over the domain is therefore an exact invariant**: no
fluid element may acquire an `s` outside `[min s(0), max s(0)]`. Any excursion
is purely numerical, is defined identically on a static and a moving mesh, and
has no free parameter.

Measured on the matched glass KH of section 42, in units of the initial
entropy span, with `[0.9473, 2.5000]`:

| `t` | static LDA | moving N | moving B-scalar | moving LDA Roe | moving LDA contour |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.20 | 2.920e-2 | 7.179e-5 | 3.180e-5 | 2.603e-5 | **3.113e-1** |
| 0.40 | 1.402e-1 | 2.909e-4 | 2.714e-3 | 6.703e-2 | **4.271e+0** |
| 0.60 | | 1.341e-2 | 5.086e-2 | 2.930e-1 | dead |
| 0.80 | | 3.745e-2 | 1.530e-1 | **1.796e+0** | dead |
| 1.00 | 3.398e-1 | 4.212e-2 | 5.451e-1 | **5.099e+0** | dead |
| 1.40 | 4.614e-1 | 2.219e-1 | 3.445e-1 | dead | dead |
| 2.00 | 4.246e-1 | 2.365e-1 | 5.036e-1 | dead | dead |

Script: `Hydro_data_analysis/Analysis/moving_mesh/kh_entropy_drift.py`.

### 45.2 What bounds the entropy error, and what does not

The columns separate into bounded and unbounded, and the split is not
static-against-moving:

- **static LDA is bounded.** It has the *largest* early error of the
  non-contour runs, `2.9e-2` at `t=0.2`, a thousand times moving LDA's, but it
  saturates near 0.4 and stays there to `t=2`.
- **moving N is bounded**, and is better than static LDA at every time,
  0.237 against 0.425 at `t=2`.
- **moving B-scalar is bounded**, 0.50 at `t=2`.
- **moving LDA runs away.** Roe + split starts a thousand times *below* static
  LDA and overtakes it by `t=0.6`: 2.6e-5, 6.7e-2, 0.293, 1.80, 5.10, then
  negative mass at `t=1.008`. Five times the entire physical entropy span.

That gives the mechanism its final form. On a Lagrangian mesh the entropy
vector lies in the kernel of every `K_j` (section 44.2), so the upwind
dissipation that bounds entropy error on a static mesh is gone. **Whatever
bounds it must then come from the distribution itself.** N is monotone and
supplies that bound; LDA is not and does not; B supplies it by blending toward
N. On a static mesh `K^+` supplies it for both, which is exactly why static LDA
saturates while moving LDA does not.

This also explains section 43.1's observation that scalar B "survives primarily
by becoming N-like", with mean theta rising to 0.761. That is not a
disappointing accident of the limiter. Once the entropy dissipation is gone,
becoming N-like is the *only* remaining mechanism, so any limiter that works
must do it.

### 45.3 The contour residual is a large entropy source

The contour column is not a variant of the Roe column. At `t = 0.2`, on the
same mesh at the same time,

```text
moving LDA, Roe + split      2.603e-05
moving LDA, contour          3.113e-01     12000 times larger
static LDA (K-matrix)        2.920e-02
```

The contour form produces more numerical entropy in one fifth of the run than
static LDA accumulates in all of it, and reaches four times the physical
entropy span by `t = 0.4` before dying at `t = 0.326`.

This is new evidence and it did not exist when the mathematical default was
chosen. The form-selection campaign of section 32 measured `L1`, covariance,
conservation and completion, but never entropy production. Section 36.4 gave
the mechanism in advance without knowing this number: the contour total uses a
specified nodal-flux quadrature rather than the exact boundary integral, its
error is `O(h^3)` with a tensor structure that does not cancel over a vertex
star, and it cannot break conservation but can only damage accuracy and
positivity. An `O(h^3)` residual error that is not annihilated for the entropy
mode, on a mesh whose entropy dissipation is exactly zero, accumulates without
any mechanism to remove it.

**Section 35.1 item 2 makes contour the provisional mathematical default. This
measurement is the strongest evidence against it so far**, and unlike the Sod
robustness argument of section 8, it is not confounded by a first-order
control: both moving columns here are the same scheme, the same mass, the same
frame and the same mesh, differing only in the element total. The acceptance
condition proposed in section 36.4, comparing the nodal quadrature against a
high-order evaluation of the boundary integral, should now be run before
contour is carried further.

### 45.4 What this settles and what it leaves

Settled: section 44.5's item 1, the KH moving-LDA failure, is entropy runaway
caused by the loss of `K^+` entropy dissipation on a Lagrangian mesh combined
with a non-monotone distribution. It is not a topology or storage defect, which
is consistent with section 43's isolation controls finding neither.

Consequences for the work order:

1. The `sigma`-fraction sweep is still worth running on KH, and now has a
   sharper prediction: the entropy excursion at fixed `t` should rise
   monotonically with the Lagrangian fraction, and moving LDA should recover
   boundedness below some threshold. That threshold is the design number for
   any `|u - sigma|/c` floor.
2. The contour-versus-Roe entropy gap needs the quadrature audit of section
   36.4 before the residual form is settled.
3. Moving LDA needs either a positivity mechanism or a floor on
   `|u - sigma|/c`. Section 43.1 already shows the limiter route works by
   becoming N-like, so the frame-velocity floor is the option that might
   preserve LDA's accuracy, and it is untested.

Not settled: whether the entropy runaway and the small-cell signature are the
same event. Both KH failures occur on very light cells, `oldMass` 4.7e-6 and
4.5e-8, the same signature as the `n=128` Sod sliver of section 34.2.

---

## 46. 2026-08-19: discontinuity-controlled mesh-velocity smoothing does not cure moving-N Sod

- **Author:** Codex (GPT-5).
- **Detailed report:** `dev_log/sod_n_mesh_sensor_20260819.md`.
- **Campaign:**
  `/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_N_MeshSensor_20260819`.
- **Profile figure:**
  `/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_N_MeshSensor_20260819/figures/sod-n-mesh-sensor-profiles.png`
  (PDF with the same stem is stored beside it).
- **Evolution figure:**
  `/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_N_MeshSensor_20260819/figures/sod-n-mesh-sensor-evolution.png`
  (PDF with the same stem is stored beside it).
- **Machine-readable metrics:**
  `/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_N_MeshSensor_20260819/analysis.json`.

Zhenyu proposed using a shock/contact/rarefaction sensor to change the mesh
velocity itself rather than modifying the N/LDA distribution. The tested,
Galilean-covariant policy is

\[
\boldsymbol\sigma_i=\boldsymbol\sigma_i^{\rm QL}
+\alpha S_i(\overline{\boldsymbol u}_i-\boldsymbol u_i),\qquad\alpha=0.5,
\]

with a face-area-weighted neighbour velocity. The final `VelVertex` remains
the unique velocity used everywhere in the ALE step. One variant uses
compression times a pressure reconstruction defect; the other also activates
on density, pressure and velocity reconstruction defects to include contacts
and rarefaction edges. This is an ALE extension inspired by Paardekooper's
sensor, not Paardekooper's published Bx formula.

Matched glass48 moving-N results at `t=0.2` are:

| policy | L1(rho) | volume RMS(vy) | raw RMS(vy) | max abs(vy) | flips |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 3.88588e-2 | 1.42445e-2 | 1.53230e-2 | 1.29075e-1 | 332 |
| shock, alpha=0.5 | 3.88656e-2 | 1.42697e-2 | 1.53545e-2 | 1.29319e-1 | 329 |
| all-wave, alpha=0.5 | 4.29629e-2 | 1.42763e-2 | 1.47760e-2 | 1.12383e-1 | 280 |

The shock sensor is effectively inert after the opening transient. The
all-wave policy is not: around `t=0.02` its velocity correction has RMS
`3.12e-2`, maximum `2.02e-1`; at the endpoint it still activates 54.8 per
cent of the cells and changes the topology/step history. Nevertheless it does
not reduce the volume- or mass-weighted transverse noise. It only reduces a
few extremes while increasing L1(rho) by 10.6 per cent. Its RMS(vy) remains
1.68 times the matched static-N value, the same gap as baseline.

This supports Zhenyu's doubt. Reactive neighbour smoothing cannot act at the
initial discontinuity because `ubar-u=0` while the initial fluid velocity is
uniform; it responds only after noise exists. A prescribed sensor-normal
drift could act earlier, but is a materially more invasive dissipation model
and should not be conflated with this test.

Decision: retain the compiled-out research switch for reproducibility, but do
not adopt it and do not spend a Gresho boost campaign on this version. The KH
entropy result of section 45 makes the controlled `sigma`-fraction/K-mode
dissipation study the cleaner next experiment. Before starting it, review any
alternative mechanism proposed by Claude Code against the matched static-N
target and these figures. If no mechanism has a clearer mathematical basis
than reactive mesh-velocity smoothing, stop tuning Sod and proceed to the KH
instability campaign.

---

## 47. 2026-08-19: the entropy term is refuted; the sigma fraction rescues KH completely

- **Author:** Claude Code (Opus 5).
- **Campaign:** `/home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_EntropySweep_20260819`.
- **Figures:** `figures/kh-entropy-sweep-density.{png,pdf}` (2-D density, six arms
  x four times) and `figures/kh-entropy-sweep-curves.{png,pdf}`.
- **Status:** the mechanism proposed in `dev_log/RD_ALE_entropy_dissipation.md`
  is **not** the cause of the KH failure. That document's algebra stands; its
  causal claim does not.

### 47.1 The two switches

`RD_ALE_ENTROPY_DISSIPATION=eps` implements the term of the derivation:
`K_j^+ += eta_j P_e`, `K_j^- -= eta_j P_e`, with the element-level gate
`eta_j = (1/2)|n_j| max(0, eps c - |u - sigmabar_T|)`.
`RD_ALE_MESH_VELOCITY_FRACTION=f` scales `VelVertex` by `f`, so `f=1` is
quasi-Lagrangian and `f=0` reproduces the existing zero-mesh test.

Six arms on the section-41 KH, all else matched: `eps` = 0, 0.1, 0.2, 0.3 and
`f` = 0.5, 0.75.

### 47.2 Result

| arm | outcome | entropy excursion at `t=0.8` | min cell mass at `t=1.0` |
| --- | --- | ---: | ---: |
| `eps = 0` (baseline) | fails `t=1.008` | 1.015 | 5.46e-5 |
| `eps = 0.1` | fails `t=1.084` | 0.661 | 5.54e-5 |
| `eps = 0.2` | fails `t=0.978` | 3.937 | -- |
| `eps = 0.3` | fails `t=1.022` | 1.421 | 3.46e-5 |
| **`f = 0.5`** | **completes `t=2`** | **0.188** | 8.50e-5 |
| **`f = 0.75`** | **completes `t=2`** | **0.114** | 8.61e-5 |

The initial minimum cell mass is `1.106e-4`.

**The entropy term does act, and it does not matter.** At `t=0.4` it reduces
the entropy excursion sixfold, `4.35e-2` to `6.26e-3`, so the implementation is
not inert and the entropy mode really is what it targets. But the failure time
moves by less than ten per cent and is not monotone in `eps`, the 2-D density
maps at `t=0.8` are indistinguishable between `eps=0`, `0.1` and `0.3` -- all
three show the roll-ups disintegrating into mesh-scale fragments -- and every
arm dies near `t=1`.

**The sigma fraction rescues it completely.** Both `f=0.5` and `f=0.75` produce
clean cat's-eye vortices at `t=0.8` and `t=1.2` and run to `t=2`. Their entropy
stays bounded at 0.36 and 0.22, comparable to static LDA's 0.42. A 25 per cent
reduction in how Lagrangian the mesh is turns a run that dies at `t=1` into one
that completes.

### 47.3 What actually fails

The minimum cell mass separates the arms where nothing else does. Every `eps`
arm collapses from `1.1e-4` to `3.5-5.5e-5` by `t=1.0` and then loses a cell
entirely within a few steps -- the failing cell has `oldMass = 4.7e-6`, an
order of magnitude below the last recorded minimum, so the collapse is abrupt
rather than gradual. Both `f` arms stay at `8.5-10.4e-5` through `t=2` and
never form such a cell.

So the causal chain is **Lagrangian mesh, plus KH shear, produces mesh
distortion and cell collapse, which produces the negative mass.** The entropy
runaway measured in section 45 is real, and it is a co-symptom of the same mesh
degradation rather than its cause. That is why restoring entropy dissipation
without touching the mesh changes the entropy number and nothing else.

Section 45.4 listed as unsettled "whether the entropy runaway and the
small-cell signature are the same event". They are not, and the small-cell
signature is the one that matters.

### 47.4 What this costs the earlier reasoning

Sections 44 to 46 and the derivation document argued that changing `sigma` was
the wrong route because it surrenders the Lagrangian property the moving mesh
exists for, and that an operator-side fix was preferable because it leaves the
mesh alone. **The operator-side fix was implemented, is provably correct in the
sense the derivation claims, measurably does what it was designed to do, and
does not solve the problem.** The route argued against is the one that works.

The derivation is not retracted. Its algebra is verified and its account of the
Sod transverse noise stands. What is retracted is section 3's implication that
the mesh-velocity route only helps by surrendering something valuable: at
`f=0.75` the surrender is 25 per cent, and the Galilean advantage at that value
is now a measurement to be made rather than an assumption. Section 46's
negative result also reads differently now: Codex's sensor failed because it
was reactive, not because the mesh-velocity axis is the wrong one.

### 47.5 Next

1. **Measure what `f` costs.** The Gresho boost-3 and boost-10 covariance
   study at `f = 0.75` and `f = 0.5`, against `f = 1`. If the boost-10
   advantage largely survives at `f=0.75`, that is the practical default.
2. **Find the threshold.** `f = 0.9` and `f = 0.95` on KH, to locate where the
   rescue stops working; the useful default is the largest `f` that completes.
3. **Confirm the mechanism directly** by recording cell aspect ratio or minimum
   dual area against `f`, rather than inferring it from the failure signature.
4. Keep `RD_ALE_ENTROPY_DISSIPATION` compiled out. It is a working
   implementation of a correct piece of mathematics that addresses a real but
   non-fatal defect, and it should not be adopted on the strength of that.

---

## 48. 2026-08-19: the Lagrangian-fraction threshold, the long-time test, and regularisation does not help

- **Author:** Claude Code (Opus 5).
- **Campaign:** `/home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_FracLong_20260819`.
- **Figures:** `figures/kh-fraction-threshold.{png,pdf}` and
  `figures/kh-fraction-long.{png,pdf}`.

### 48.1 The switch was confounded and is now clean

`RD_ALE_MESH_VELOCITY_FRACTION` originally scaled the final `VelVertex`, which
also scaled the regularisation drift, so section 47's `f` mixed two effects. It
now multiplies the fluid-following assignment `VelVertex = P[i].Vel` **before**
the `REGULARIZE_MESH_CM_DRIFT` loop. `f` is therefore exactly the fraction of
the fluid velocity the mesh follows, and mesh regularisation keeps its full
configured strength at every `f`. All results below use the corrected switch.

### 48.2 Results

| arm | outcome | entropy excursion | min cell mass |
| --- | --- | ---: | ---: |
| `f = 1.00` | fails `t=1.008` | 1.02 at `t=0.8` | 1.12e-4 at `t=0.8` |
| `f = 1.00`, `CellShapingSpeed = 2.0` | **fails `t=1.064`** | 1.67 at `t=0.8` | **6.59e-5** at `t=0.8` |
| `f = 0.95` | **fails `t=1.687`** | 4.54 at `t=1.6` | 6.57e-5 at `t=1.6` |
| `f = 0.90` | completes `t=2` | 0.12 at `t=2` | 1.04e-4 |
| **`f = 0.75`** | **completes `t=10`** | 0.20 at `t=2`, 0.00 at `t=8` | 9.9e-5 to 1.24e-4 throughout |
| static LDA | completes `t=2` | 0.37 at `t=2` | 1.04e-4 |

Initial minimum cell mass is `1.106e-4`.

**The threshold lies between 0.90 and 0.95.** Zhenyu's concern is correct at
`f = 0.95`: it does not fix anything, it postpones. The run survives to
`t=1.69` instead of `t=1.01` and then produces exactly the same failure, with a
full entropy runaway to 4.5 entropy spans and the same collapse of the minimum
cell mass to `6.6e-5`.

**At `f = 0.75` it is not a postponement.** Ten seconds of evolution, five
times the baseline failure time, with the failure indicator flat: the minimum
cell mass ends at `1.24e-4`, *above* its initial value, and never approaches
the `4.7e-6` of a failing cell. The collapse mechanism is not operating slowly;
it is not operating.

### 48.3 Mesh regularisation does not rescue it, at any strength tested

`CellShapingSpeed = 0.5` is the value every parameter file in the repository
uses, so the failing runs were already at the AREPO default. Raising it to
`2.0` at `f = 1` **fails at `t = 1.064` against the baseline `t = 1.008`** --
within six per cent -- and makes the minimum cell mass *worse* at `t=0.8`,
`6.59e-5` against `1.12e-4`.

This matters beyond the negative result. Zhenyu's stated requirement was that
the scheme should not depend on a narrow parameter window, and the regularisation
knob turns out not to open one at all: four times the default strength moves the
failure time by six per cent. Together with section 46's sensor result, two
independent attempts to fix this from the mesh-velocity *correction* side have
now failed, while scaling the fluid-following *fraction* works. The distinction
is that regularisation and the sensor are both reactive -- they respond to
distortion after it exists -- whereas `f` reduces the rate at which the mesh is
dragged into the shear layer in the first place.

### 48.4 A caveat on the entropy metric

The `f = 0.75` entropy excursion falls to `0.000` at `t = 8` and `t = 10`. That
must not be read as accuracy. The metric is **one-sided**: it detects states
outside the initial entropy range and is blind to diffusion inside it. By
`t = 10` the density contrast has decayed substantially,

```
t        rho range        std(rho)   |grad rho| p95
0.0    [1.000, 2.000]      0.4743         1.0000
2.0    [0.921, 2.210]      0.3783         1.0089
6.0    [1.087, 2.174]      0.2301         0.5790
10.0   [1.103, 1.849]      0.1609         0.4514
```

so the excursion vanishes because the solution has moved inside the bounds, not
because it is converged. Whether that decay is physical mixing of a fully
nonlinear KH or numerical diffusion is **not decided by any measurement here**
and needs a resolution study.

### 48.5 Where this leaves the moving mesh

The honest summary is narrower than "f = 0.75 fixes it":

- moving LDA fails on KH for every `f` above about 0.9, including at `f = 1`;
- it survives to `t = 10` at `f = 0.75` with a flat failure indicator;
- neither mesh regularisation nor a discontinuity sensor changes this;
- the price of `f = 0.75` in Galilean invariance has still not been measured,
  and that measurement is now the deciding one. Section 47.5 item 1 stands and
  should be run before `f` is proposed as anything.

An `f` of 0.75 means the mesh follows three quarters of the fluid velocity. That
is no longer a quasi-Lagrangian scheme, and calling it one would be misleading;
what it costs on Gresho with boost is the number that decides whether it is a
moving-mesh method worth having.

---

## 49. 2026-08-19: what the Lagrangian fraction costs, measured on Gresho with boost

- **Author:** Claude Code (Opus 5).
- **Campaign:** `/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Gresho_Boost_Fraction_20260819`.
- **Figure:** `figures/gresho-boost-fraction-profiles.{png,pdf}`, a 3x3 grid of
  azimuthal-velocity profiles, rows the Lagrangian fraction and columns the
  boost. Script `examples/gresho_2d/plot_gresho_boost_fraction.py`.
- **Status:** this is the deciding measurement section 48.5 asked for. It
  decides against `f = 0.75`.

### 49.1 The measurement

Nine runs, Gresho vortex at `n=48` to `t=1` on the moving mesh with LDA, at
boosts 0, 3 and 10 and Lagrangian fractions 1.00, 0.90 and 0.75. All nine
complete. The metric is the mass-weighted `L1` of the azimuthal velocity against
the analytic Gresho profile, evaluated in the vortex frame, so a perfectly
Galilean-invariant scheme returns the same number at every boost.

| | boost 0 | boost 3 | boost 10 | `b3/b0` | `b10/b0` |
| --- | ---: | ---: | ---: | ---: | ---: |
| `f = 1.00` | 9.3116e-3 | 9.4464e-3 | 9.7385e-3 | **1.01** | **1.05** |
| `f = 0.90` | 9.1088e-3 | 1.0516e-2 | 2.0735e-2 | 1.15 | **2.28** |
| `f = 0.75` | 9.0706e-3 | 1.5841e-2 | 7.1418e-2 | 1.75 | **7.87** |

Section 25 records the static mesh losing a factor of about 14 over the same
range, which is the other end of the scale.

The ratio columns are the quantity the figure annotates as "x N vs boost 0":
each panel's `L1` divided by the `L1` of the **boost-zero panel in its own
row**. Since the boost is subtracted before the azimuthal velocity is formed,
and a boosted Gresho vortex is the same vortex, that ratio is the frame
dependence with the ordinary discretisation error divided out. The first column
is 1.00 by construction, and the three rows share a denominator to within two
per cent, so the ratios are comparable across rows as well as along them.

The figure makes the same point without the numbers. Along the top row the
three panels are indistinguishable. At `f = 0.90` the boost-10 panel visibly
broadens at the peak and develops structure in the `r > 0.4` region that should
be exactly at rest. At `f = 0.75` and boost 10 the Gresho profile is no longer
recognisable: the peak is flattened and displaced inward, the scatter runs from
`r = 0` to `r = 0.65`, and a clear negative-velocity band appears beyond
`r = 0.4`.

### 49.2 Reading

**At boost zero the three are indistinguishable**, 9.07e-3 to 9.31e-3. Lowering
`f` costs nothing when there is no bulk motion. Everything below is purely the
loss of Galilean invariance, which is exactly the property the moving mesh
exists to provide.

**`f = 1.00` is essentially Galilean invariant**: 1.05 at boost 10.

**`f = 0.75` surrenders most of the advantage.** Measured logarithmically
between the moving-mesh value 1.05 and the static-mesh value 14, `f = 0.90`
gives up about 30 per cent of the advantage and `f = 0.75` about 78 per cent.
A method that keeps 22 per cent of its Galilean advantage is not a
quasi-Lagrangian method with a small correction; it is most of the way back to
a static mesh, while still paying the whole cost of moving-mesh machinery.

### 49.3 The trade, stated plainly

`f = 0.90` was subsequently run to `t = 10` as well, and completes. Its health
indicators are not marginal, and on the entropy metric it is **better** than
`f = 0.75`:

| `t` | min cell mass, `f=0.90` | entropy, `f=0.90` | entropy, `f=0.75` |
| ---: | ---: | ---: | ---: |
| 1.0 | 8.31e-5 | 0.082 | 0.140 |
| 2.0 | 1.01e-4 | 0.134 | 0.204 |
| 4.0 | 8.49e-5 | 0.081 | 0.311 |
| 10.0 | 1.11e-4 | 0.000 | 0.000 |

against an initial minimum cell mass of `1.106e-4`. The complete trade:

| `f` | KH outcome | boost-10 `L1` penalty | advantage retained |
| ---: | --- | ---: | ---: |
| 1.00 | fails `t=1.008` | 1.05 | 100% |
| 0.95 | **fails `t=1.687`** | not measured | -- |
| **0.90** | **completes `t=10`** | **2.28** | **~70%** |
| 0.75 | completes `t=10` | 7.87 | ~22% |
| static | completes `t=2` | ~14 | 0% |

So `f = 0.90` is a materially better operating point than `f = 0.75`: it keeps
about seventy per cent of the Galilean advantage, survives ten seconds, and
carries less entropy error. An earlier draft of this section concluded that no
`f` was both robust and Galilean invariant; with the long `f = 0.90` run that
statement is too strong and is withdrawn.

**The qualitative verdict does not change, for a different reason.** `f = 0.90`
sits 0.05 away from `f = 0.95`, which fails at `t = 1.687` with a full entropy
runaway. A parameter that works at 0.90 and fails catastrophically at 0.95 is
exactly the narrow operating window Zhenyu asked the scheme not to depend on,
and nothing in this data says where the cliff sits for a different problem,
resolution, or Mach number. `f` remains a diagnostic that has told us something
real about the failure, not a solution.

Zhenyu's judgement on first seeing the section 48 result -- that `f = 0.75` is
a temporary workaround, that it is unlikely to be a universal constant, and
that it probably weakens the quasi-Lagrangian advantage -- is confirmed on all
three counts by this table.

### 49.4 What is actually established

Six sections of work reduce to a short list.

**Established:**

1. Moving LDA fails on KH by cell collapse under Lagrangian shear, at every
   `f` above about 0.9 (sections 47, 48).
2. The failure is not the entropy mode. A correct, targeted, conservation- and
   covariance-exact entropy dissipation was implemented, demonstrably acts, and
   does not change the outcome (section 47).
3. It is not mesh regularisation either, at four times the default strength
   (section 48.3), and not a discontinuity-driven mesh-velocity sensor
   (section 46).
4. Reducing how far the mesh follows the fluid does prevent it, and the price
   in Galilean invariance is now quantified and is too high (this section).
5. N and B do not fail on KH at all. The problem is specific to LDA's
   non-monotone distribution on a Lagrangian mesh.

**Not established:** any mechanism that keeps `f = 1` and prevents the
collapse. That is the open problem, and the evidence now points at it being a
property of the LDA distribution rather than of the ALE construction, since
every ALE-side intervention has failed while changing the distribution (to N,
or to B, or blending toward N) works.

### 49.5 Next

The remaining untried direction is the one section 43.1 already showed works
empirically without understanding why: a limiter that makes LDA locally
N-like where the mesh is about to degenerate. Section 43.1 found scalar B
completing KH with mean `theta` rising to 0.761, which was read there as B
"surviving by becoming N-like" and treated as disappointing. In light of
sections 47 to 49 it should be read as the only intervention that has worked
while keeping `f = 1`, and it deserves the Gresho boost measurement that `f`
has just been given. If scalar B holds `b10/b0` near 1.05 while completing KH,
it is the answer and `f` can be retired to a diagnostic.

---

## 50. 2026-08-19: status of the moving-mesh LDA problem

A consolidation, not new work. Sections 44 to 49 spent six campaigns on one
failure, and the useful output is a sharp statement of what the failure needs.

### 50.1 The failure is a three-way intersection

Moving LDA fails on long-time KH only when **all three** of the following hold.
Removing any one of them gives a run that completes:

| drop this | result | price |
| --- | --- | --- |
| `f = 1` becomes `f <= 0.90` | completes `t = 10` | 30 to 78 per cent of the Galilean advantage (section 49) |
| LDA becomes N or B | completes `t = 2` | first-order dissipation, or a blend that becomes N-like |
| long-time shear becomes Sod, Gresho or Yee | completes | none; `f = 1` with LDA is fine on all of them |

So this is not "the moving mesh has a problem" -- static LDA fails nothing here
and moving N and B fail nothing here -- and it is not "KH is hard", since static
LDA completes it. It is the intersection.

### 50.2 Which side the evidence points at

| intervention | side | `f = 1` kept | works |
| --- | --- | :-: | :-: |
| targeted entropy dissipation (section 47) | ALE | yes | **no** |
| mesh regularisation, 4x default (section 48.3) | ALE | yes | **no** |
| discontinuity mesh-velocity sensor (section 46) | ALE | yes | **no** |
| Lagrangian fraction `f` (sections 47--49) | ALE | **no** | yes, too expensively |
| N instead of LDA (section 40) | distribution | yes | yes |
| component-wise B (section 43.1) | distribution | yes | partly |
| scalar-theta B (section 43.1) | distribution | yes | yes |

**Every ALE-side intervention that preserves `f = 1` has failed, and every
distribution-side intervention has worked.** Four attempts against three. That
is the clearest signal in the whole phase, and it says the remedy is a property
of the distribution, not of the ALE construction.

### 50.3 The one option nobody has tried

The failure is extraordinarily localised. At the moment of death a **single**
cell has collapsed to `oldMass = 4.7e-6` against a typical `1.1e-4`, a factor
of 24, while the several thousand others are healthy; the last recorded
snapshot minimum, one or two steps earlier, is still `5.5e-5`.

The only intervention that currently works at `f = 1` answers that single cell
by making the **entire domain** N-like: section 43.1 measures scalar B's mean
`theta` rising to 0.761 with 38 per cent of samples fully N.

An a-posteriori fallback triggered only on cells that are actually degenerating
would leave the LDA distribution untouched in the other 99.9 per cent of the
domain, and so should cost almost nothing in accuracy or in Galilean
invariance. Codex listed this as item 4 of section 43.4 and it has never been
built. It is a different object from B, which acts globally through a smooth
`theta`, and it is the outstanding candidate.

### 50.4 Recorded position

`f = 1` remains the right default: it is the only value at which the moving
mesh delivers what it exists for, `1.05` against a static mesh's `14` at boost
10. The cost of that choice is that long-time shear with LDA is currently
unavailable, and that limitation should be stated rather than papered over with
a parameter that works at 0.90 and fails at 0.95.


---

## 51. 2026-08-19: review of the two open moving-mesh problems, with proposed next experiments

- **Author:** Kimi (K3).
- **Scope:** review of sections 41-50 and of the current solver code, at
  Zhenyu's request for recommendations on (1) the moving-N Sod discontinuity
  oscillation and (2) the moving-LDA KH long-time failure. No code change, no
  new run: this section records proposed experiments and their quantitative
  predictions, not results.
- **Status:** advisory. Every item below is a proposal to be reviewed by
  Zhenyu before any campaign is launched.

### 51.1 Sod: extend the existing dissipation floor from the entropy mode to the full linearly degenerate subspace

Section 44.2 localised the moving-N transverse-noise excess to the shear mode
(0.554 residual damping at `sigma = u`, predicting 1/0.554 = 1.81 against the
measured 1.80), and showed the entropy-mode annihilation is benign. Section 47
built `RD_ALE_ENTROPY_DISSIPATION`, which adds `eta_j P_e` to `K_j^+` and
subtracts it from `K_j^-`, and proved it acts (sixfold entropy-excursion
reduction) -- but it projects onto the entropy mode only, while the Sod excess
lives in the shear mode.

The proposed change is to add the shear projector `P_s` alongside `P_e` in the
same construction (`rd_add_entropy_dissipation`,
`src/hydro/residual_distribution_solver.c:716`), i.e.
`K^+ += eta (P_e + P_s)`, `K^- -= eta (P_e + P_s)`, with the existing
element-level gate `eta_j = (1/2)|n_j| max(0, eps c - |u - sigmabar_T|)`
unchanged. The three properties proved in the derivation carry over unchanged,
because they depend only on the term being a symmetric `K^+/K^-` pair built
from spectral projectors:

1. `K^+ + K^- = K` is untouched, so conservation is exact;
2. `sum_i K_i^+ = -S^-` survives, so LDA stays linearity-preserving;
3. the construction is Galilean covariant.

A fourth property is the one that matters for Sod: a steady contact and a
steady shear layer co-moving with the mesh both have `Phi = 0`, so the added
dissipation acts only on non-zero residuals -- it damps the noise without
diffusing the exact steady states.

**Quantitative prediction, to be verified offline before any run.** Extending
`shear_mode_damping.py` to the modified `K` should show the shear damping
rising from 0.554 toward 1 as `eps` approaches `1 - 0.554 = 0.446`, so
`eps ~= 0.45` should bring the moving/static `RMS(v_y)` ratio from 1.80 back
to about 1.0. The simulation campaign should only be launched after this
offline check passes.

Physical reading: this is not a patch but a floor -- it restores, for the
linearly degenerate modes on a near-Lagrangian mesh, the dissipation those
modes have on a static mesh through `|u.n|`. The cost is confined to
`|u - sigma| < eps c` and is of exactly the magnitude a static mesh would
have paid there.

Independently of whether the fix is adopted, a glass64/96 resolution sequence
for the moving/static `RMS(v_y)` ratio should be run: the factor 1.80 is an
eigenvalue property and is predicted to be resolution-independent. Confirming
that converts the defect from an open problem into a bounded, explained and
optionally repairable one that can be stated in the thesis as such.

### 51.2 KH: a decisive diagnostic before any further fix is built

Sections 47-49 eliminated the entropy mode, mesh regularisation and the
discontinuity sensor as causes, and section 50.3 identified the a-posteriori
fallback as the outstanding candidate. Before building it, one cheap
discriminator should decide between the two remaining causal families, because
they imply different remedies.

**Geometry-first versus solution-first.** Track the worst cell step by step
(section 43.4 item 3, apparently never executed): record its dual area
`A_i(t)`, its mass `m_i(t)`, and the purely geometric predicted area obtained
from the vertex-drift trajectory alone, independently of the solution update.

- If the dual area collapses first, the root cause is the mesh motion: LDA's
  dispersive velocity noise pollutes `P[i].Vel`, and the vertices are dragged
  into a sliver. The supporting observation is that moving N completes the
  same KH under the same mesh-motion rule, differing only in the smoothness
  of the velocity field. The remedy must then act on the mesh velocity --
  and since both reactive corrections (sections 46, 48.3) failed, it would
  need to be a stronger constraint, e.g. a direct limit on the vertex
  displacement relative to its star.
- If the area stays healthy while the mass goes negative, it is a positivity
  failure of the distribution/update, and the a-posteriori fallback below is
  exactly the right remedy.

**Timestep check.** The failure is abrupt -- one cell drops from `5.5e-5` to
`4.7e-6` within a few steps -- which is the signature of a local CFL violation
on a collapsing cell. Whether the RD timestep uses a length scale based on the
median-dual area and the ALE signal speed `|u - sigma| + c`, or a Voronoi-based
or otherwise less local scale, should be checked in the code. If the latter,
adding `min(h_dual / (|u - sigma| + c))` to the timestep is a principled fix
that keeps `f = 1` and keeps LDA everywhere, and it should be tested before
any limiter work.

### 51.3 KH: design notes for the a-posteriori (MOOD-type) fallback

Section 50.3 identified this as the one option nobody has tried. Design
details to be settled before implementation:

1. **Detector.** After the RK predictor, flag a vertex if its update gives
   density or pressure below a small multiple of the physical floor, or if
   the predicted dual mass satisfies `m_i^{n+1} < delta m_i^n` with
   `delta ~ 0.5`. Cascade the flag to the star neighbours, since a degenerate
   vertex receives residuals from every element of its star.
2. **Fallback.** Recompute the distribution of every element in the flagged
   stars with the N distribution (`theta_T = 1`), consistently in both RK
   stages. N is element-conservative, so global conservation is preserved
   exactly.
3. **Cost control.** Section 50.3 records that the failure involves one cell
   in several thousand, so the expected accuracy and Galilean-invariance cost
   is negligible. But the fraction of flagged elements per step must be
   logged; if it settles above a few per cent, the scheme has effectively
   become N and that must be reported rather than presented as LDA.
4. **Acceptance test.** The fallback must reproduce the section-43.1
   scalar-B completion of KH to `t = 2` while keeping the flagged fraction at
   the per-mille level, and then pass the section-49 Gresho boost measurement
   with `b10/b0` near 1.05. Only then is it a solution rather than a
   global-limiter in disguise.

### 51.4 A mathematical check available offline: the conditioning of `S^-`

LDA requires solving `S^- x = phi`; the code already handles the singular case
with the minimum-norm pseudo-inverse (`rd_solve_upwind_system`,
`src/hydro/residual_distribution_solver.c:773`), and the
`RD_ALE_CONDITION_DIAGNOSTIC` switch already exists. On a Lagrangian mesh
`S^-` loses rank in the linearly degenerate subspace, so the minimum-norm
solution discards information along exactly those directions. The proposal is
to instrument a failing KH run to record, for the few steps before failure,
the numerical rank and condition number of `S^-` per element. If the
collapsing cell correlates with ill-conditioning, "fall back to N when `S^-`
is ill-conditioned" is a local trigger with a mathematical basis, and it
fires earlier than any mass-based detector. This is a diagnosis first; it
becomes a remedy only if the correlation is found.

### 51.5 Position on the Lagrangian fraction

Section 50.4 is endorsed: `f = 1` remains the default, the `f` sweep has
completed its diagnostic mission, and `f = 0.90` is not a solution -- a
parameter that works at 0.90 and fails catastrophically at 0.95 is the narrow
operating window Zhenyu explicitly asked the scheme not to depend on, and
nothing says where the cliff sits for a different problem, resolution or Mach
number.

### 51.6 Suggested order of work

The shear-projector extension for Sod (51.1, offline prediction first) and
the geometry-first versus solution-first discriminator for KH (51.2) are
independent, both are about a day of work each, and each directly decides the
next investment: 51.1 either retires the Sod-N defect or bounds it as a
known constant, and 51.2 selects between a mesh-velocity remedy and the MOOD
fallback (51.3), with the timestep check (51.2) and the `S^-` conditioning
audit (51.4) as near-free additions to the same instrumented run.
---

## 52. 2026-08-20: a-posteriori local LDA-to-N fallback on glass48 KH

- **Author:** Codex.
- **Purpose:** execute the section-51.3 MOOD-type proposal: keep the full
  f=1 moving-LDA candidate, reject a bad RK trial, and recompute only the
  flagged element star with the N branch.
- **Status:** diagnostic prototype built and exercised. The retry mechanism
  works, but the mass/positivity detector does **not** pass the KH acceptance
  test. It fires after a slowly accumulated LDA undershoot has already
  contaminated the state; local N rescues two steps but cannot repair that
  history on the third.

### 52.1 Configuration and implementation boundary

True glass48 KH IC:

    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/Glass_Sod_KH_ALE_20260818/inputs/IC_kh_glass48

Switches: Arpaia equal-step ALE, full mesh velocity f=1, co-moving element
frame, Roe residual plus split mesh-velocity term, internal two-pass RK2+F1
total residual, RD CFL selection, one MPI rank, snapshots every 0.2, and
requested TimeMax=2.

Experimental switch:

    RD_ALE_APOSTERIORI_FALLBACK=0.5

Relevant source/configuration files:

    src/hydro/residual_distribution_solver.c
    defines_extra
    examples/shocktube_2d/Config_KH_APOSTERIORI_f050.sh
    examples/shocktube_2d/param_KH_APOSTERIORI_glass48.txt

The ordinary B sensor is bypassed. The coherent B implementation is used only
as a two-branch engine: mask 0 is LDA and mask 1 is N/lumped. Each timestep
freezes the same mesh velocity, geometry and connectivity, saves the Arpaia
stage-0 state, tries both RK stages with LDA, inspects predictor and endpoint
candidates, restores Q and primitives on rejection, marks every element
incident on a bad vertex, and retries both stages.

A density ratio below 0.5 is a soft detector. Once that vertex star has
switched to N, the low-order candidate is judged only by hard density/pressure
positivity; the arbitrary 0.5 warning threshold is not treated as an
admissibility theorem. If a complete N star is still non-physical, a second
diagnostic variant expands the N patch by successive element rings.

This is intentionally a global algebraic retry on one rank. It is compiled out
by default and is **not** the future pending-ledger/MPI/hierarchical design.

### 52.2 Empty-mask validation

At time 0.2001953125, the new path was compared by ParticleID with the earlier
glass48 moving Roe-LDA snapshot. IDs and times are identical.

| field | maximum absolute difference | mean absolute difference |
| --- | ---: | ---: |
| coordinates | 2.80e-11 | 1.81e-14 |
| density | 1.62e-10 | 4.37e-13 |
| pressure | 2.12e-11 | 1.49e-13 |
| velocity | 7.48e-11 | 1.17e-13 |
| stored mass | 3.67e-13 | 1.19e-15 |
| volume | 3.11e-13 | 9.35e-16 |

An empty fallback mask therefore introduces no hidden B/N dissipation. The
differences are floating-point ordering only.

### 52.3 Failure sequence

The pure-LDA history contains a long precursor that the per-step 0.5 ratio test
does not detect:

| snapshot time | min density | max density | min pressure |
| ---: | ---: | ---: | ---: |
| 0.0000 | 1.0000 | 2.0000 | 2.5000 |
| 0.2002 | 0.9817 | 2.0430 | 2.3754 |
| 0.4004 | 0.9425 | 2.0517 | 2.2659 |
| 0.6001 | 0.8398 | 2.0529 | 2.1929 |
| 0.8003 | 0.5250 | 2.1405 | 2.1096 |
| 1.0000 | 0.3060 | 2.3033 | 1.9852 |

The detector finally acts at ID 1837:

1. At time 1.1550293, the endpoint test gives min density 5.75e-3 and
   rho(new)/rho(old)=0.146. Six of 4608 triangles (0.1302 per cent) switch
   to N and the retry is accepted.
2. At time 1.1552734, the predictor test gives min density 6.30e-3 and ratio
   0.231. The same six-triangle star switches to N and is accepted.
3. At time 1.1555176, the LDA predictor is negative at -1.34e-2. The complete
   six-element N star gives endpoint min density -1.0836e-2, so hard
   positivity fails.

Eleven halo retries grow the N patch from 6 to 1128 of 4608 triangles
(24.48 per cent), while the bad density remains -1.083637e-2 to printed
precision. A larger fallback ring therefore does not repair the already
contaminated nodal history once every element incident on ID 1837 is N.

The final step is not an invalid-mesh event in the global diagnostics:
min triangle area / mean area = 0.2617, minimum triangle angle = 0.3498 rad,
inverted=0, nonpos_Sbar=0, ALE coverage differs from one by about 1e-15, and
pullback error is 8.7e-19. This rules out a sliver, inverted triangle, or
negative endpoint dual area as the immediate cause. It does not replace
Kimi's requested per-ID history of dual area and mass, which is still needed
to establish which quantity began drifting first.

The selected timestep had already halved to 2.4414e-4. On the first complete
N-star retry, the reported RD midpoint limit was 2.4954e-4, so the existing RD
CFL condition was nominally satisfied, although only marginally.

### 52.4 Matched global-N control

A global N_SCHEME control used the same IC and the same moving Roe+split,
co-moving, Arpaia, RK2+F1, RD-CFL and f=1 switches:

    examples/shocktube_2d/Config_KH_GLOBAL_N_ROE_RK2.sh

It completes to time 2. At the local-LDA failure time it remains healthy
(min density about 0.87 and min pressure about 2.21). At time 2:

    density range = [0.87375, 2.22331]
    pressure range = [2.37266, 2.63436]

Static LDA also completes to time 2, with density range
[0.84152, 2.76838] and min pressure 2.06468.

N can therefore prevent the moving-LDA runaway when present from a clean
history. It cannot reconstruct the lost state when introduced only after the
density has drifted from 1 to order 1e-2. The result is not “moving N fails”
and not “fallback wiring is inert”; it is “the proposed mass-ratio/positivity
detector fires too late.”

### 52.5 Archives and figures

Reproducible analysis:

    examples/shocktube_2d/analyze_kh_aposteriori.py

Fallback halo build and run:

    artifact: build_artifacts/KH_APOSTERIORI_f050_halo/8e0a7715111f-02d4f4982ad31dfe
    binary SHA256: 4f6c793235b69440e4b54aaef5ad41de4b926837daee49ad83dccf647f5eca3d
    run: /home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_Aposteriori_20260820/glass48_roe_f050_halo_v3/output
    log: /home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_Aposteriori_20260820/glass48_roe_f050_halo_v3/output/arepo-20260820T101548Z.1391307.log

Matched global-N build and run:

    artifact: build_artifacts/KH_GLOBAL_N_ROE_RK2/8e0a7715111f-8f8353f628323874
    binary SHA256: c446c56bbf0d387550ad9e5e769803f6bf3b5dabe57e78675e43de954ffa5da8
    run: /home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_Aposteriori_20260820/glass48_global_N_roe_RK2/output
    log: /home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_Aposteriori_20260820/glass48_global_N_roe_RK2/output/arepo-20260820T102150Z.1395014.log

Generated figures, all labelled “glass48 KH; Arpaia ALE; co-moving
Roe+split; RK2+F1; mesh f=1”:

    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_Aposteriori_20260820/figures/kh_aposteriori_density_comparison.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_Aposteriori_20260820/figures/kh_aposteriori_minima_history.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_Aposteriori_20260820/figures/kh_aposteriori_halo_growth.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_Aposteriori_20260820/figures/kh_aposteriori_summary.json

Earlier diagnostic archives are preserved separately. The first identified the
mistaken treatment of the 0.5 warning ratio as a hard N condition; the second
demonstrated the two accepted six-element retries before the hard failure.
Neither is used as the reported final result.

### 52.6 Decision and next experiment

The section-51.3 acceptance criterion is not met: the run stops at 1.15552,
and enlarging the fallback patch to 24.5 per cent does not change the bad
value. This implementation remains a debug-only switch and must not become the
default or be translated into a production pending ledger.

If the a-posteriori direction continues, the detector must act on the
precursor, not only final positivity. The most informative candidate is a
relaxed local discrete-maximum/entropy test or the proposed S-minus
conditioning trigger, followed by a persistent local N/B state over several
steps. It should begin acting while the density floor is about 0.9--0.8
(time 0.4--0.6 here), not after it reaches 1e-2. The flagged fraction and
Gresho boost penalty would decide whether this is genuinely local or merely
B/N under another name.

Independently, record the stepwise m_i, temporary Arpaia mass, dual area and
mesh trajectory for ID 1837. The present global geometry diagnostics establish
that the terminal mesh is admissible, but only that per-cell record can close
Kimi's geometry-first versus solution-first question.

## 53. Three-day stopping-rule experiment for alternative distributions

### 53.1 Scope and decision rule

The remaining distribution-scheme investigation is time-boxed to three working
days. It is a small-cost diagnostic sprint, not the start of a new open-ended
stabilisation project. The reference mathematical configuration is held fixed:

    Arpaia ALE time form
    contour element residual
    co-moving frame
    mesh-velocity factor f = 1
    glass initial conditions
    low resolution

No broad switch matrix or parameter scan is permitted. The objective is to
answer two questions:

1. Does a clean low-order ALE distribution remain admissible on the same moving
   geometry?
2. Can a cheap nonlinear LDA blend act early enough to prevent the precursor
   without destroying the quasi-Lagrangian Gresho advantage?

If no candidate produces a material improvement within three days, freeze the
current Arpaia + contour + co-moving baseline and move development effort to
moving-mesh hierarchical timestepping and MPI parallelisation. Sensor tuning,
SUPG variants and rigorous convex limiting are then deferred.

### 53.2 Attempt 1: local ALE Lax--Friedrichs control

The first and most decisive experiment is a globally applied, globally lumped
local-LF distribution of the same contour residual,

\[
  \Phi_{i,T}^{\rm LF}
  =
  \frac{1}{3}\widetilde\Phi^T
  +\alpha_T\left(U_i-\overline U_T\right),
\]

with

\[
  \alpha_T \geq
  \max_{j\in T}\rho\!\left(K_j^{\rm ALE}\right).
\]

This requires no new Roe inverse or SUPG parameter and uses the already
available ALE-relative spectral information. Accuracy is not the purpose of
this control.

- If local LF fails at the same time and place, stop distribution tuning: the
  leading suspect becomes moving mass, RK geometry/GCL or connectivity change.
- If LF survives while the current N branch shows anomalous behaviour, the
  present N implementation is not an adequate moving low-order floor.
- If LF survives, it may also replace N as the low-order side of one subsequent
  blend.

### 53.3 Attempt 2: full residual-ratio Bmax

The cheapest all-wave nonlinear candidate is the full residual-based LDA--N
blend,

\[
  \Phi_{i,T}^{B}
  =
  \Theta_T\Phi_{i,T}^{N}
  +(I-\Theta_T)\Phi_{i,T}^{\rm LDA},
\]

\[
  (\Theta_T)_{kk}
  =
  \frac{|\Phi^T_k|}
       {\sum_i|\Phi^N_{i,k}|+\epsilon},
  \qquad
  \theta_T^{B\max}=\max_k(\Theta_T)_{kk}.
\]

Use the scalar Bmax value for all equations. Unlike a compression-only sensor,
this construction can respond to shock, contact, rarefaction and non-compressive
moving-mesh residual noise. It must blend the complete RK residual and the
associated mass treatment, not only the spatial fluctuation:

\[
  m_{ij}^{B\max}
  =
  (1-\theta_T)m_{ij}^{\rm LDA,ALE}
  +\theta_T\,\bar m_{i,T}\delta_{ij}.
\]

### 53.4 Attempt 3: Dobeš--Deconinck Bx

The pressure-sensor Bx scheme from the Dobeš--Deconinck 2005 work (published
in its final forms in 2008, including DOI 10.1007/978-3-540-75712-2_44) is

\[
  \Phi_{i,T}^{Bx}
  =
  \theta_T\Phi_{i,T}^{N}
  +(1-\theta_T)\Phi_{i,T}^{\rm LDA},
  \qquad
  \theta_T=\min(1,h_Ts_T^2).
\]

For an unsteady ALE computation, the intended pressure sensor is based on the
physical material derivative,

\[
  s_T\propto
  \left[
    \left.\frac{\partial p}{\partial t}\right|_{\chi}
    +(v-\sigma)\cdot\nabla p
  \right]^+.
\]

If the RK-stage pressure derivative is not already cheap to expose, the
three-day diagnostic may use the smooth-Euler identity

\[
  \frac{Dp}{Dt}=-\gamma p\,\nabla\cdot v
\]

as a clearly labelled simplified sensor. Only one normalisation and at most
one factor-of-four variation are allowed; do not begin a sensor parameter scan.
As in the original unsteady construction, Bx must blend the LDA consistent/ALE
mass contribution with the N lumped contribution. A spatial-residual-only
blend is not a faithful test.

Expected interpretation:

- Gresho and smooth vortical flow should have \(\theta_T\simeq0\), retaining
  LDA accuracy.
- Sod shocks should activate N, but an isobaric contact and the expansion side
  of a rarefaction normally do not.
- Smooth KH is nearly isobaric. Bx can help only if the moving-LDA precursor
  develops a spurious pressure-compression signal before failure. Failure to
  activate is therefore informative rather than a reason to tune indefinitely.

### 53.5 Three-day execution schedule

Day 1:

1. At the first bad candidate, dump density and pressure minima, endpoint and
   temporary Arpaia mass ratios, dual-area ratio, triangle area/minimum angle,
   local CFL, current/previous-step flip count and Bx sensor value.
2. Run one lower-CFL reference; do not perform a CFL scan.
3. Implement and run the pure ALE local-LF control on low-resolution Sod and
   glass KH.

Day 2:

1. If LF survives, implement full Bmax with complete residual/mass blending and
   run static/moving Sod plus moving KH.
2. If LF fails, do not spend the day on Bmax. Run a fixed-connectivity/no-flip
   control if an existing low-cost switch permits it, and determine whether the
   failure follows a flip or mass jump.

Day 3:

1. Implement or port the Dobeš--Deconinck Bx experiment.
2. Run Gresho boost 10, Sod and KH with the fixed reference switches.
3. Generate labelled plots and archive exact configurations and paths in this
   log. Do not add another distribution or sensor variant.

### 53.6 Acceptance and stopping criteria

Continue the robustness direction only if at least two of the following are
met:

1. Moving KH at \(f=1\) passes at least twice the previous failure time.
2. Moving Sod oscillations become visibly and quantitatively comparable to the
   static control.
3. Gresho boost-10 error increases by no more than approximately 10--20 per cent
   relative to moving LDA.
4. The experiment identifies a reproducible causal separation between a
   distribution failure and a flip/mass/GCL failure.

The following do not count as progress: substantially reducing \(f\), requiring
an extremely small CFL, postponing failure only briefly, eliminating a negative
state while retaining the KH runaway, or requiring a sensor sweep.

Within this sprint do not implement pure SUPG, LLxF--SUPG, a system PSI scheme,
convex limiting, a new mesh-velocity shock modification, space--time positive RD
or another a-posteriori rollback. They either have a lower probability of
answering the immediate question or exceed the three-day budget.

If the stopping criterion is reached, preserve all diagnostics and proceed in
this engineering order:

1. moving equal-step MPI;
2. moving hierarchical ledger on one MPI rank;
3. combined hierarchical timestepping and MPI;
4. return later to high-order moving-RD robustness.

---

## 54. 2026-08-20: review of the three-day plan — two gaps, and the recommended order

- **Author:** Claude Code (Fable 5), at Zhenyu's request.
- **Scope:** advisory review of sections 41-53 before the section-53 sprint
  starts. No code change, no new run.
- **Status:** proposals for Zhenyu to accept or strike. Where this section
  conflicts with section 53, section 53's stopping rule still governs the
  budget: nothing below extends the three days.

### 54.1 Gap 1: no section-53 attempt addresses the diagnosed Sod mechanism

Section 44.2 attributed the moving-N Sod transverse noise to the loss of
shear-mode damping at `sigma = u`: residual damping 0.554, predicted
amplification 1/0.554 = 1.81 against the measured 1.80. That is an eigenvalue
property of `K^{ALE}`, independent of the distribution. The section-43.1 data
already confirm the independence: moving scalar-B has `RMS(v_y) = 1.472e-2`
against moving N's `1.424e-2` and static N's `8.49e-3` — the blend keeps the
noise. **A blend cannot fix problem 1, because N is already its robust end.**
LF, Bmax and Bx are all blends or low-order controls, so section 53 as written
can at best *diagnose* the Sod defect, never meet its own acceptance criterion
53.6(2).

The only mechanism-grounded fix on the table is Kimi's section-51.1 shear
projector, with its falsifiable offline prediction (`eps ~= 0.45` restores the
ratio to ~1.0). As far as this log records, not even the offline check has
been executed.

### 54.2 Gap 2: scalar-theta B already completes KH at `f = 1`, and its deciding measurement was never run

Section 43.1's scalar-B run completes glass KH to `t = 2` with `f = 1`, and
section 49.5 named its Gresho boost measurement as the decision: "if scalar B
holds `b10/b0` near 1.05 while completing KH, it is the answer and `f` can be
retired to a diagnostic." That measurement has not been made. It requires no
code at all.

The objection on record — mean `theta = 0.761`, 38 per cent of samples fully
N, "survives by becoming N-like" — was measured **on KH**, where LDA is
failing anyway; theta statistics are problem-dependent, and on the smooth
Gresho vortex theta should stay near zero with LDA accuracy retained. That
expectation is exactly what the measurement tests, and it is the cheapest
possibly-decisive experiment in the whole candidate set.

### 54.3 Recommended additions, ranked

**A. Day 1, before building anything new: the scalar-B campaign.** Gresho
boost 0/3/10 under the section-49 protocol, plus one KH long run to `t = 10`,
all under the section-53.1 reference switches. Pass condition: `b10/b0` in
1.05-1.2 meets criteria 53.6(1) and 53.6(3) simultaneously, and problem 2 is
closed at the engineering level — the blend is the production scheme, and pure
LDA's long-time-shear limitation is recorded rather than fixed. Per-arm theta
statistics must be published with the result either way.

**B. The eigenvalue floor on the full linearly degenerate subspace.** Extend
`rd_add_entropy_dissipation` from `P_e` alone to `P_e + P_s` — or,
equivalently and more simply, apply a Harten-type fix
`|lambda| -> max(|lambda|, eps c)` to the two degenerate eigenvalues inside
the `K^+/K^-` construction, which needs no explicit projectors. One change,
both problems:

- **Sod:** run section 51.1's offline check first, by extending
  `shear_mode_damping.py` to the modified `K`; prediction: damping rises from
  0.554 toward 1 as `eps` approaches 0.446, so the moving/static `RMS(v_y)`
  ratio falls from 1.80 to ~1.0. This is the only candidate that can meet
  criterion 53.6(2).
- **KH:** section 47 tested the floor on the entropy mode only. The shear
  mode — the one KH drives — was never tested, so section 47's "operator-side
  fixes fail" must not be extrapolated to it. The floor also makes `S^-`
  uniformly invertible, bounding LDA's `beta = K^+ (S^-)^{-1}` and retiring
  the pseudo-inverse branch, which is precisely section 51.4's conditioning
  suspicion.
- **Risk to measure, not assume:** the floor adds dissipation to the shear
  mode, and Gresho's azimuthal profile *is* a shear structure. The mitigation
  is that the term acts only on non-zero residuals, so exact co-moving steady
  states (`Phi = 0`) are untouched; how much a resolved vortex pays is an
  open number. The run set must therefore include Gresho boost-0 with the
  floor on and off, against the `9.3116e-3` baseline of section 49.1.

**C. One amendment to the LF control (53.2).** If LF fails under the contour
total, add a single Roe+split LF run before concluding "moving mass, RK
geometry/GCL or connectivity": section 45.3's factor-12000 contour entropy
source is a confounder for exactly that inference.

**D. Near-free instrumentation to piggyback on the day-1 runs.**

1. per-ID stepwise `m_i`, Arpaia temporary mass, dual area and vertex
   trajectory for the worst cell (section 52.6's outstanding request; closes
   section 51.2's geometry-first versus solution-first question);
2. per-element `S^-` numerical rank and condition number near failure
   (section 51.4; the diagnostic switch already exists);
3. one half-CFL KH reference — section 52.3 found the RD limit only
   marginally satisfied at the death of ID 1837, and one run separates the
   abrupt terminal failure from the slow precursor.

**E. Conditional demotion of attempts 2 and 3.** If A passes, Bmax (53.3) is
an accuracy refinement rather than a rescue and may be compressed or skipped;
Bx (53.4) stays capped at one day, with non-activation on the nearly isobaric
KH treated as information, per section 53.4's own reading.

### 54.4 Post-sprint candidates, recorded so they are not relitigated

If the stopping rule fires, these are the candidates worth carrying to the
"return later" item, in order:

1. **FCT/Zalesak limiting** of the `(LDA - N)` antidiffusive part under
   relaxed local bounds — the principled version of the early-acting detector
   section 52.6 asked for, acting at the `rho ~ 0.9-0.8` precursor rather
   than at positivity failure; both branches already exist in the B engine.
2. **MOOD with a relaxed DMP-plus-persistence detector** (section 52.6).
3. **Space-time RD / Guardone-Isola topology-change formalism** —
   thesis-scale, not a sprint item.
4. **The section-36.4 contour quadrature audit**: offline, decides the
   residual-form default independently of robustness, and worth an evening
   whenever one is free.

### 54.5 Probability assessment

Problem 1 is likely solvable within the budget: the mechanism is
quantitatively understood and the fix has a falsifiable offline prediction.
Its floor outcome is also acceptable — a resolution-independent, explained
factor 1.80 (to be confirmed on glass64/96) statable in the thesis as a
bounded property rather than an open defect.

Problem 2's honest bet is scalar B: it is the only intervention that has
worked at `f = 1`, and its single unknown — the Gresho boost cost — is
obtainable in a day. If A and B both pass, both problems close inside the
sprint. If only one does, the stopping rule still hands hierarchical
timestepping and MPI a baseline whose limitation is recorded rather than
papered over.


---

## 55. 2026-08-20: Kimi's review of sections 52-54 — updated reading and low-cost candidates

- **Author:** Kimi (K3), at Zhenyu's request.
- **Scope:** review of sections 52-54; proposals only. No code change. One
  numerical experiment (the scalar-B Yee convergence study) is launched from
  this session and will be reported in its own section.
- **Status:** advisory, subject to the section-53 stopping rule.

### 55.1 What section 52 changes

Two points from the a-posteriori experiment deserve a sharper reading than
they have received.

1. **The geometry-first hypothesis is now largely excluded, at least at the
   terminal event.** Section 52.3 records a healthy mesh at the moment of
   death: minimum triangle area / mean area = 0.2617, minimum angle 0.3498
   rad, no inverted triangles, no non-positive endpoint dual areas, pullback
   error 8.7e-19. What collapses is the *mass* (`4.7e-6` against a typical
   `1.1e-4`), not the *area*. The section-51.2 discriminator is therefore
   already answered for the terminal event in favour of solution-first. What
   remains open is only whether the slow precursor (density floor drifting
   1.0 to 0.31 over `t = 0.2` to `1.0`) is *driven* by noisy vertex motion.
2. **The precursor is secular, monotone and single-signed** (minimum density
   0.98, 0.94, 0.84, 0.53, 0.31 at `t = 0.2` to `1.0`). That is the
   signature of a systematic error of fixed sign being amplified by LDA's
   non-monotonicity, not of an oscillatory instability. A per-step density
   *ratio* detector (the section-52 trigger) is structurally blind to such a
   drift, which is exactly why it fired too late. One further observation:
   the bad value being unchanged to printed precision while the halo grows
   from 6 to 1128 triangles is *expected*, not a bug — an RD vertex update
   depends only on its own star, which the first halo ring already covers.
   The informative fact is instead that the complete N-star update *computed
   from the contaminated star state* is itself negative.

### 55.2 Low-cost candidates, ranked

**1. The scalar-B Gresho boost campaign (zero code, run first).** Section
54.2's gap: scalar B already completes KH at `f = 1`, and its deciding
measurement — Gresho boost 0/3/10 under the section-49 protocol, with
per-arm theta statistics published — was never run. The recorded objection
(mean theta 0.761) was measured on KH, where LDA is failing anyway; theta
is problem-dependent and should stay near zero on smooth flow. If `b10/b0`
stays in 1.05-1.2, problem 2 is closed at the engineering level and pure
LDA's long-time-shear limitation is recorded as a known restriction.

**2. The eigenvalue floor on the full linearly degenerate subspace (offline
prediction, then 3-4 runs).** Section 51.1's shear projector, in section
54.3-B's simpler Harten form `|lambda| -> max(|lambda|, eps c)` applied to
the two degenerate eigenvalues inside the `K^+/K^-` construction: no explicit
projectors, `K^+ + K^- = K` preserved, and `S^-` becomes uniformly
invertible, retiring the pseudo-inverse branch (the section-51.4 suspicion).
Section 47 refuted the entropy-mode floor only; the shear mode — the one KH
drives — has never been tested, so "operator-side fixes fail" must not be
extrapolated to it. Risk to measure: Gresho's azimuthal profile *is* a shear
structure, so the run set must include boost-0 with the floor on and off
against the `9.3116e-3` baseline. This is the only candidate that addresses
both open problems at once, and the only one that can meet criterion
53.6(2).

**3. Restart-from-snapshot calibration of the point of no return (near-zero
code).** Section 52.6's open question is *when* the detector must act. Take
the pure-LDA snapshots at `t = 0.4, 0.6, 0.8, 1.0` (density floors 0.94,
0.84, 0.53, 0.31), convert them to ICs with the existing glass tooling, and
restart the global-N control from each. If N recovers the run from `t = 0.8`,
the a-posteriori direction is alive and needs only an earlier, persistent
trigger. If N cannot recover even from `t = 0.6`, the precursor is already
fatal while the density floor looks benign, the a-posteriori route is
effectively dead, and the blend/floor routes become the only ones. This is
an afternoon of post-processing plus four short runs, and it decides whether
any further MOOD investment is justified at all.

**4. Free post-processing on existing snapshots (no runs).**

- **Where the drained mass goes.** Element conservation is exact, so the
  mass lost by the failing cell reappears somewhere. Mapping the per-cell
  mass anomaly at `t = 0.6, 0.8` distinguishes two regimes: if the lost mass
  sits in the immediate star (undershoot beside overshoot), the mechanism is
  anti-diffusive pairwise exchange and local dissipation (candidate 2) is
  the right fix; if it is transported coherently along the shear layer, the
  mechanism is an advection bias and candidate 2 will not help.
- **Per-element histogram of `|u - sigma|/c`** on the KH and Sod snapshots:
  measures what fraction of the domain sits in the low-damping regime and
  sizes the `eps` of candidate 2.
- **Drain location versus the shear-rate field:** whether the density drain
  is locked to the braids where the Lagrangian shear is maximal.

**5. A rigorous, parameter-free early trigger for KH, if MOOD survives
candidate 3.** Section 45.1 established that the specific-entropy range
`[0.9473, 2.5]` is an *exact invariant* of this problem. A local
entropy-bounds DMP detector needs no tuning and, per section 45's table,
already separates moving LDA from moving N at `t = 0.4` (6.7e-2 against
2.9e-4) while the density floor is still benign. Note that section 47
refuted entropy *dissipation as a fix*; it says nothing against entropy
*excursion as a detector*.

**6. Endorsed piggyback items:** section 54.3-D's per-ID stepwise history
for the failing cell and the single half-CFL reference; and section
54.4(4)'s contour quadrature audit as an offline evening task, since it
decides the residual-form default independently of the robustness question.

**Not worth further spending:** any reactive mesh-velocity correction
(sections 46 and 48.3 are two independent failures of that idea), further
`f` sweeps (the narrow-window verdict is final), and starting Bmax/Bx before
candidates 1 and 2 report — if scalar B passes, they are accuracy
refinements rather than rescues.

### 55.3 Overall assessment

Problem 1 is likely to close inside candidate 2, with the acceptable floor
outcome being a resolution-independent, explained factor 1.80 (to be
confirmed on glass64/96). Problem 2's honest bet remains scalar B
(candidate 1); candidate 3 decides whether MOOD survives as a long-term
direction or is written off. Candidates 1 and 2 are independent and together
cost about a day.

---

## 56. 2026-08-20: accepted sprint order and corrections to the section-54/55 reviews

- **Author:** Codex, after discussion with Zhenyu.
- **Decision:** start the scalar-B campaign immediately. Scalar B may become a
  temporary engineering solution if it keeps the fully quasi-Lagrangian
  (`f = 1`) moving mesh robust without materially degrading smooth-flow
  accuracy or Galilean invariance. This would close the immediate production
  problem, but would not explain or repair pure moving-LDA's KH failure.
- **User expectation:** scalar B should not strongly change boost-10 Gresho
  because a smooth vortex ought to activate little N blending. The more
  credible cost is a lower Yee convergence order than pure LDA. Both are
  hypotheses to measure, not acceptance assumptions.

### 56.1 Corrections carried into the experiment plan

1. **Local ALE-LF is not merely another N/B blend.** It adds acoustic-scale
   dissipation to all components and remains a useful low-order diagnostic.
   If contour-LF fails, run one Roe+split LF control before blaming moving
   storage, RK geometry/GCL or connectivity, because the contour KH entropy
   source is a known confounder.
2. A future linearly-degenerate eigenvalue floor must retain the existing
   **element-relative-motion gate**. A direct per-face replacement

       |lambda| -> max(|lambda|, eps c)

   would also fire on some static-mesh faces and change the static baseline.
   Inside the element gate, use the conservative split

       lambda_eps^+ = 0.5 [lambda + max(|lambda|, eps c)],
       lambda_eps^- = 0.5 [lambda - max(|lambda|, eps c)].

   Test the shear mode before flooring the full repeated subspace: the entropy
   mode was already ineffective on KH, while Sod identified shear as the
   under-damped mode.
3. A floor may improve the numerical rank of `S^-`, but uniform conditioning
   on arbitrary triangles is unproved. Do not retire the pseudo-inverse without
   singular-value and triangle-quality data. Nor does it leave every exact
   co-moving contact/shear untouched: N uses `K^+` and `K^-` separately even
   if the full element residual is zero. Contact width, density L1 and
   transverse-velocity RMS remain mandatory diagnostics.
4. Global minimum-density history does not prove a monotone, single-signed
   drift of one cell; a per-ID history is required. Mapping where drained mass
   reappears is correlation evidence, not unique proof of pairwise
   antidiffusion.
5. Restarting N from LDA snapshots is useful as a recoverability check, but is
   not an exact point-of-no-return calibration because reconnect/rebuild, RK
   history and endpoint-storage semantics differ.
6. The KH entropy range is a strong early-warning diagnostic with a numerical
   tolerance; for discrete nodal conservative averages it is not yet a
   rigorously parameter-free invariant-domain theorem.

### 56.2 Scalar-B campaign and acceptance criteria

Use the already validated moving-mesh form:

    B_SCHEME + RD_B_SCALAR_THETA + RD_B_FROZEN_THETA
    + RD_RK2_TOTAL_RESIDUAL + RD_ALE_EQUALSTEP
    + RD_ALE_CONTOUR_RESIDUAL + RD_ELEMENT_COMOVING_FRAME
    + RD_ALE_CFL_TIMESTEP,

with Arpaia modified-midpoint mass, `f = 1`, equal timesteps and the same
glass/boosted IC family as section 49. The first run set is:

1. Gresho `n = 48`, `t = 1`, boosts 0, 3 and 10;
2. smoothed glass48 KH (tanh transition width 0.025) to `t = 10`;
3. retain scalar-B versus LDA Yee `n = 32,64,128` as a separate smooth-
   accuracy measurement.

Scalar B passes Gresho only if **both** relative and absolute accuracy survive:

- `L1(b10)/L1(b0) <= 1.2` (the moving-LDA `f = 1` reference is 1.05);
- boost-0 and boost-10 absolute `L1(v_phi)` remain within roughly 10--20 per
  cent of the matching moving-LDA values in section 49, rather than merely
  becoming boost-invariant through diffusion;
- publish mean theta, its histogram and the `theta = 1` fraction for every arm.

The KH gate is completion to `t = 10` with positive mass, density and
pressure, healthy mesh diagnostics, entropy-range history and the full theta
history. Completion by becoming locally N-like is acceptable as a temporary
robust scheme, but must be reported and is not a cure for pure LDA.

Yee answers a different question: whether scalar limiting damages smooth-flow
order or its error constant. It cannot replace the Gresho boost or KH gates.
If scalar B passes KH and Gresho but lowers Yee order, it can still serve as a
temporary production baseline; Bmax/Bx or another distribution then becomes
an accuracy refinement rather than an emergency rescue.

---

## 57. 2026-08-20: scalar-B sprint — glass Gresho and KH complete with a measured accuracy cost

- **Author:** Codex.
- **Campaign root:**
  `/home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820`.
- **Status:** Gresho, Yee, matched moving-LDA controls and glass KH to `t = 10` are complete.

### 57.1 Reproducibility and a correction to the historical comparison

Current-source immutable builds are

    gamma=5/3 scalar B:
    /home/zwu/arepo_rd/arepo/build_artifacts/scalarb-sprint-g53/000cdaaee46f-65076a7882697285/Arepo

    gamma=1.4 scalar B:
    /home/zwu/arepo_rd/arepo/build_artifacts/scalarb-sprint-g14/000cdaaee46f-13d8f6f4c5faf23b/Arepo

    gamma=5/3 matched LDA:
    /home/zwu/arepo_rd/arepo/build_artifacts/lda-glass-control-g53/000cdaaee46f-a89df8b022b6bab4/Arepo

All use Arpaia modified-midpoint mass, the P1(U) contour total, the element
co-moving frame, `f = 1`, equal timesteps and the ALE-RD CFL bound. The B
arms additionally use scalar and frozen theta with coherent RK2 total
residuals.

The three Gresho ICs use the same 2304 relaxed glass generators and IDs.
Coordinates, density and internal energy are bitwise identical; only `v_x`
is increased by exactly 3 or 10. The boost-zero IC reproduces the established
glass hash exactly:

    da76535f6f6366fa8d9b43d3e27f0f8b1bdfb461eead3c2d80aed401c935df64.

The first submissions (jobs 10407658, 10407659, 10407660 and 10407662) used
two ranks and stopped before the first update because
`RD_ALE_GEOMETRY_DIAGNOSTICS` Stage 0 is deliberately single-rank. This is
an orchestration error, not a physical failure. Their provenance is preserved
under `output/`. The corrected one-rank runs use `output_rank1/`; hence
this campaign is not an MPI validation.

Section 49 is not a matched absolute-error reference. Its provenance shows a
jitter IC, gamma 1.4 and Roe+split LDA. The present default-mathematics,
gamma-5/3 glass comparison therefore required new LDA boost-0/10 controls.

### 57.2 Glass48 Gresho at t=1

The metric is mass-weighted `L1(v_phi)` in the de-boosted vortex frame.

| scheme | boost 0 | boost 3 | boost 10 | b10/b0 |
| --- | ---: | ---: | ---: | ---: |
| scalar B | 9.338108e-3 | 9.337138e-3 | 9.337807e-3 | **0.99997** |
| matched LDA | 7.795319e-3 | -- | 7.795328e-3 | **1.00000** |

Scalar B therefore passes the Galilean gate decisively. Against the matched
glass LDA control its absolute error is higher by 19.79 per cent at boost zero
and 19.79 per cent at boost ten, just inside the pre-declared 10--20 per-cent
acceptance band. The peak `v_phi` falls from about 0.96844 for LDA to
0.92686/0.92682 for scalar B, so the cost is visible diffusion rather than
noise in the scalar metric.

Contrary to the hypothesis that a smooth vortex would activate little
limiting, final total-theta is nearly identical in all three scalar-B arms:

| boost | mean total theta | theta=1 histogram bin |
| ---: | ---: | ---: |
| 0 | 0.71871 | 46.40% |
| 3 | 0.71867 | 46.48% |
| 10 | 0.71884 | 46.40% |

The spatial-theta mean is about 0.978. Scalar B preserves this Gresho result
despite being strongly N-like locally; it is not an almost-pure-LDA result.

Generated figures and metrics:

    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/figures/scalarb-gresho-glass-boosts.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/figures/scalarb-gresho-glass-boosts.pdf
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/figures/scalarb-vs-lda-gresho-glass.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/figures/scalarb-vs-lda-gresho-glass.pdf
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/gresho_scalarb_metrics.json
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/gresho_matched_metrics.json

Every figure labels scalar B, Arpaia ALE, the P1(U) contour total, the
co-moving frame, `f = 1` and coherent equal-step RK2.

### 57.3 Yee convergence: the expected order loss is real

Kimi's six Yee runs had all completed successfully, but the first analysis
failed on an integer/string dictionary-key mismatch. After that was fixed,
the script still reported a non-convergent `O(1.76e-2)` error already at
`t=0`: it subtracted 5 from all three coordinate columns and thus inserted
the spurious term `(z-5)^2=25` into `r^2`. Restricting the analytic radius
to x and y reproduces the earlier LDA reference and gives

| scheme | n=32 | n=64 | n=128 | observed orders |
| --- | ---: | ---: | ---: | --- |
| LDA | 2.277399e-3 | 7.347788e-4 | 2.247805e-4 | 1.63, 1.71 |
| scalar B | 2.363198e-3 | 8.900692e-4 | 3.373608e-4 | **1.41, 1.40** |

Thus Zhenyu's anticipated trade is confirmed: scalar B retains better than
first-order convergence here, but lowers both measured orders and raises the
fine-grid error (by 50 per cent at n=128). Its final mean total theta is
0.659, 0.626 and 0.669 for n=32,64,128, with 24--33 per cent in the
theta=1 bin.

Corrected analysis and figure:

    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/Yee_ScalarB_20260820/analyze_yee_scalarb.py
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/Yee_ScalarB_20260820/analysis.json
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/figures/scalarb-yee-convergence.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/figures/scalarb-yee-convergence.pdf

### 57.4 KH long-run status at the time of this entry

Corrected job 10407671 uses the unchanged true glass48 KH IC (SHA256
`e2db4f6f1b3682029f13f93bafd2e1f89dc4b8e6ad0920203d564123b1e47888`),
gamma 1.4 and the scalar-B form above. The IC has the standard tanh shear
transition of width 0.025 but no additional runtime boundary-layer smoothing.

At the latest check it has passed `t = 5.69`, well beyond the old `t = 2`
short run and pure moving-LDA failure, without negative mass or
thermodynamics. At `t ~= 4`, min cell mass is `1.52e-4`,
rho is 0.915--2.086 and pressure is 2.349--2.671. The entropy excursion was
about 0.81 near `t = 1` and 0.25 near `t = 4`: current evidence is robust
completion, not a cure for the contour entropy-quality defect.

Run and log directory:

    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/kh_t10/output_rank1

A final health table, theta history and labelled KH density figure will be
added only after the run reaches `t = 10`.

### 57.5 KH reaches t=10: the robustness gate passes

Job 10407671 completed normally in 20:42 with Slurm state `COMPLETED` and
exit code `0:0`. The final snapshot is `snap_050.hdf5` at exactly
`t = 10`. No negative mass, density or pressure, inverted element,
non-positive Arpaia midpoint mass, or pullback failure occurred.

| time | rho range | pressure range | min cell mass | entropy excursion |
| ---: | --- | --- | ---: | ---: |
| 0 | 1.000--2.000 | 2.500--2.500 | 3.456e-4 | 0 |
| 2 | 0.896--2.087 | 2.320--2.651 | 1.542e-4 | 0.301 |
| 4 | 0.915--2.086 | 2.349--2.671 | 1.520e-4 | 0.246 |
| 6 | 0.881--2.135 | 2.246--2.759 | 1.931e-4 | 0.306 |
| 8 | 0.927--2.099 | 2.272--2.753 | 1.619e-4 | 0.0568 |
| 10 | 0.934--1.996 | 2.302--2.703 | 1.832e-4 | 0.0452 |

The endpoint mesh is healthy: minimum triangle area / mean area is 0.2866,
minimum angle is 0.3849 rad, with zero inverted elements and zero non-positive
`Sbar`; the final pullback error is `1.11e-16`.

Limiter activity decreases rather than approaching a late global-N collapse:

| time | mean total theta | theta=1 histogram bin |
| ---: | ---: | ---: |
| first reported step | 0.983 | 89.65% |
| 2 | 0.761 | 36.72% |
| 4 | 0.731 | 31.18% |
| 6 | 0.588 | 16.97% |
| 8 | 0.552 | 14.71% |
| 10 | **0.466** | **8.44%** |

Scalar B therefore passes the immediate engineering robustness gate at
`f = 1`: it completes the glass KH problem on which pure moving LDA fails,
without reducing the mesh velocity. Together with the Gresho result, it is a
credible temporary production baseline. The qualification remains important:

1. it costs 19.8 per cent in matched Gresho L1 and lowers Yee order from about
   1.6--1.7 to about 1.4;
2. the large intermediate entropy excursion shows that it does not repair the
   contour-total entropy defect;
3. classical scalar B is not an invariant-domain proof and has not been
   validated with hierarchical timesteps or MPI;
4. the late KH density field is visibly mixed, so completion alone is not an
   accuracy endorsement.

The bounded-sprint decision is therefore to keep scalar B as the current
robust `f = 1` fallback/baseline, while pure LDA remains the smooth-accuracy
reference. A less dissipative Bmax/Bx or shear-floor refinement is now an
accuracy project, not a prerequisite for starting hierarchical-timestep and
MPI work.

Final data and generated figures:

    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/kh_scalarb_metrics.json
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/figures/scalarb-kh-density-t0-t10.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/figures/scalarb-kh-density-t0-t10.pdf
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/figures/scalarb-kh-theta-history.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/figures/scalarb-kh-theta-history.pdf

---

## 58. 2026-08-20: Chapter 4 distribution derivation and matched component-wise B Yee control

- **Author:** Codex.
- **Thesis file:**
  `/home/zwu/MyThesis/Zhenyu-PhDThesis/zhenyu_thesis/chapter4/chapter4.tex`.
- **Component-B campaign:**
  `/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Yee_Bcomponent_20260820`.

### 58.1 Mathematics added to Chapter 4

Chapter 4 now separates four operations previously compressed into the phrase
"use the N/LDA/B distribution":

1. ALE upwind matrices are assembled in the element co-moving frame, with
   characteristic speeds based on the relative velocity `u-sigma_bar_T`;
2. Roe N constructs `phi_i^{N,Roe}=K_i^+(Uhat_i-Uhat_in)`, which sums to the
   Roe-parameter-vector total, not in general to the P1(U) contour total;
3. moving contour-N is defined by
   `phi_i^N=phi_i^{N,Roe}+(Phi_contour-sum_j phi_j^{N,Roe})/3`;
4. LDA distributes `Phi_contour` directly with `beta_i`, while B blends the
   resulting contour-conservative N and LDA branches.

Step 3 is explicitly marked as a scheme-design choice rather than an algebraic
identity. The centred defect gives exact element conservation, but the
monotonicity/positivity proof for unmodified N does not automatically carry
over. This qualification is relevant to the moving-N Sod oscillations.

For Euler, component-wise B uses a diagonal matrix of four sensors. Scalar B
is now defined by `theta_T=max_l theta_{T,l}` acting on the complete
conservative residual vector. Chapter 4 also distinguishes the predictor's
spatial theta from the corrector's frozen complete-residual theta. The latter
blends the complete N/lumped and LDA/F1 RK2 branches, not only their spatial
terms. Both branches sum to the same Arpaia element residual, so the blend is
conservative for any theta.

The terminology is qualified: the original scalar-conservation-law B scheme
already has one scalar coefficient. "Scalar B" here names this project's
state-coherent Euler-system extension. It is not an invariant-domain proof or
an accuracy claim. The full thesis compiled successfully with `pdflatex`;
only pre-existing cross-reference/citation and box warnings were emitted.

### 58.2 Matched component-wise B Yee ladder

The control removes only `RD_B_SCALAR_THETA` from the scalar-B Config. Both B
arms otherwise use gamma 1.4, identical ICs, moving mesh with `f=1`, P1(U)
contour total, element co-moving frame, Arpaia modified-midpoint mass, frozen
complete-residual theta, equal timesteps and the ALE-RD CFL bound.

Reproducibility:

    Config: examples/gresho_2d/Config_YEE_con_cm_Bcomponent.sh
    Parameters:
    examples/gresho_2d/param_YEE_bcomponent_n32.txt
    examples/gresho_2d/param_YEE_bcomponent_n64.txt
    examples/gresho_2d/param_YEE_bcomponent_n128.txt

    Immutable binary:
    /home/zwu/arepo_rd/arepo/build_artifacts/yee-bcomponent-g14/000cdaaee46f-d7bee2ec1c577b8d/Arepo

    Build job: 10410470 (COMPLETED, MKL)
    Run jobs: 10410476, 10410478, 10410477 (all COMPLETED, exit 0:0)

The volume-weighted density error against the analytic Yee vortex at `t=1` is

| scheme | n=32 | n=64 | n=128 | observed orders |
| --- | ---: | ---: | ---: | --- |
| LDA | 2.277399e-3 | 7.347788e-4 | 2.247805e-4 | 1.632, 1.709 |
| component-wise B | **2.060269e-3** | **7.770489e-4** | **2.841136e-4** | **1.407, 1.452** |
| scalar B | 2.363198e-3 | 8.900692e-4 | 3.373608e-4 | 1.409, 1.400 |

Component-wise and scalar B share the same broad finite-resolution order loss
relative to LDA, but they are not numerically redundant. At `n=128`, the
component-wise error is 15.8 per cent below scalar B; relative to LDA it is
26.4 per cent higher, versus 50.1 per cent for scalar B. Component-wise B's
second interval order is also modestly better, 1.452 versus 1.400.

Final component-averaged total-theta means are 0.4780, 0.4439 and 0.4305 for
`n=32,64,128`, compared with scalar-B means 0.6589, 0.6256 and 0.6689. The
scalar maximum therefore activates substantially more N dissipation.

### 58.3 Decision

The Yee result does not justify scalar B as an accuracy variant:
component-wise B is consistently more accurate. Scalar B remains a distinct
robustness variant because it is one convex blend of the complete Euler
residual vector and, unlike component-wise B, has already completed glass48
KH to `t=10` at `f=1`. Whether that advantage warrants a separate thesis
method now depends on a matched component-wise KH long run, not another Yee
ladder. Until then, Chapter 4 should present scalar B as robustness motivated
and component-wise B as its accuracy control.

Analysis and labelled figures:

    examples/gresho_2d/analyze_yee_b_compare.py
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/Yee_Bcomponent_20260820/yee_b_comparison.json
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/Yee_Bcomponent_20260820/yee-component-vs-scalar-B.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/Yee_Bcomponent_20260820/yee-component-vs-scalar-B.pdf

### 58.4 Current-source matched KH resolves whether scalar B is redundant

The earlier section-43 component-wise KH failure was rerun with the immutable
binary built for section 58.2, removing code-version ambiguity. The input is
the identical smoothed glass48 KH IC (tanh transition width 0.025) used by the scalar-B `t=10` run:

    SHA256 e2db4f6f1b3682029f13f93bafd2e1f89dc4b8e6ad0920203d564123b1e47888

The component-wise run used the same gamma 1.4, `f=1`, contour P1(U) total,
element co-moving frame, Arpaia mass, frozen complete-residual B and ALE-RD
CFL choices; the only B-definition difference is the absence of
`RD_B_SCALAR_THETA`.

    Parameter: examples/gresho_2d/param_KH_Bcomponent_glass48_t10.txt
    Job: 10410514
    State: FAILED, exit 1:0, elapsed 00:01:04
    Final time reached: 0.87368011
    Log:
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/Yee_Bcomponent_20260820/kh_component_t10/arepo-20260820T204049Z.1013238.log

At failure, ID 297 had endpoint mass `-1.62954e-7`, from old mass
`1.84353e-7`. The predictor still had positive minimum density
`7.054506e-5` and pressure `2.176415`; the mesh had
`min(A)/mean(A)=0.3335`, minimum angle 0.4015 rad, zero inverted elements,
zero non-positive Arpaia masses and zero pullback error. The final mean
component-wise total theta was 0.2786, with 2.94 per cent of component samples
in the theta=1 bin. This reproduces the historical failure at 0.81845 to the
same qualitative state, with the small time difference attributable to the
later code and timestep history.

The redundancy question is therefore resolved more strongly than the Yee
ladder alone could resolve it. Component-wise B is the more accurate smooth
scheme, but it does not supply the nonlinear robustness needed by this KH
problem. Scalar B completes the identical IC to `t=10` because the maximum
sensor keeps the whole Euler residual vector on one, substantially more
N-like, blend. Scalar B should remain a separately defined
robustness-oriented method in Chapter 4; component-wise B remains the
less-diffusive accuracy control and the natural starting point for future
characteristic/Bx refinements.

---

## 59. 2026-08-21: matched pure-N glass48 KH control and time-dependent B interpretation

- **Author:** Codex.
- **Purpose:** test whether the robust N branch itself completes the identical
  smoothed glass48 KH problem (tanh transition width 0.025), and compare actual solution morphology rather
  than completion flags alone.

### 59.1 Why the time term belongs to the B blend

For an unsteady RD method the object distributed at the corrector is the
complete space-time residual, not only the spatial flux residual. In the
current equal-step RK2 notation the two branches have the form

    R_i^N   = T_i^lumped + 0.5 (phi_i^{N,n}   + phi_i^{N,*}),
    R_i^LDA = T_i^F1     + 0.5 (phi_i^{LDA,n} + phi_i^{LDA,*}).

The time-dependent B update is therefore

    R_i^B = theta_T R_i^N + (1-theta_T) R_i^LDA.

Scalarising the Euler sensor changes only how `theta_T` is selected:
`theta_T=max_k theta_{T,k}`. It does not remove the temporal residual. If B
mixed only the spatial distributions while always retaining the F1/LDA mass
matrix, `theta_T=1` would still not recover the full N update; the temporal
distribution that can drive a non-admissible state would remain. The frozen
complete-residual sensor reads the left endpoint to define `theta_T`, then
uses that same scalar for the N/lumped and LDA/F1 temporal branches and for
the old/new spatial branches. A spatial-only *sensor* remains a possible
control, but the temporal branches must still be blended if the N limit is to
be genuine.

### 59.2 Strict matched diagnostic run

The exact IC is the same one used by both B runs:

    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/inputs/IC_kh_glass48.hdf5
    SHA256 e2db4f6f1b3682029f13f93bafd2e1f89dc4b8e6ad0920203d564123b1e47888

Mathematical switches are `N_SCHEME`, `RD_RK2_TOTAL_RESIDUAL`,
`RD_ALE_EQUALSTEP`, `RD_ALE_CONTOUR_RESIDUAL`,
`RD_ELEMENT_COMOVING_FRAME`, and `RD_ALE_CFL_TIMESTEP`, with gamma 1.4,
moving-mesh fraction `f=1`, one rank, and the standard smoothed KH IC with
tanh transition width 0.025.

    Config: examples/gresho_2d/Config_FS_con_cm_N.sh
    Parameter: examples/gresho_2d/param_KH_N_glass48_t10.txt
    Binary:
    /home/zwu/arepo_rd/arepo/build_artifacts/kh-glass48-n-contour-cm-g14/000cdaaee46f-8cdf6a17f6581e7c/Arepo
    Output:
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/N_Glass48_ContourCM_20260820/kh_n_t10

This fully instrumented run was intentionally stopped after reaching
`t=2.099`. It had already passed the component-B failure time by more than a
factor of two; at `t=2.09869` the predictor minimum density and pressure were
`0.942818` and `2.40518`, respectively.

### 59.3 Long quality run to t=10

The long build removes only per-step diagnostic/assertion output. At the
common `t=0.400390625` snapshot it is bitwise identical to the fully
instrumented build: the maximum difference in coordinates, velocities,
masses, density, pressure and internal energy is exactly zero.

    Config: examples/gresho_2d/Config_KH_N_con_cm_release.sh
    Parameter: examples/gresho_2d/param_KH_N_glass48_release_t10.txt
    Binary:
    /home/zwu/arepo_rd/arepo/build_artifacts/kh-glass48-n-contour-cm-release-g14/000cdaaee46f-38be559cc4d50aa6/Arepo
    Output:
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/N_Glass48_ContourCM_20260820/kh_n_release_t10
    Log:
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/N_Glass48_ContourCM_20260820/kh_n_release_t10/arepo-20260820T224745Z.1554461.log
    Exit status: 0; final time: 10; wall time: 2189.38 s.

At the last common pre-failure snapshot:

| scheme | time | rho_min | rho_max | p_min | E_ky |
| --- | ---: | ---: | ---: | ---: | ---: |
| component B | 0.800171 | 0.570005 | 2.13759 | 2.16736 | 1.00670e-2 |
| scalar B | 0.800171 | 0.877703 | 2.09636 | 2.21323 | 9.11778e-3 |
| N | 0.800171 | 0.962999 | 2.08678 | 2.23068 | 8.26161e-3 |

The pure-N density channel is therefore already much better protected before
component B fails. Scalar B is intermediate, consistent with its use of the
maximum component sensor to move the whole Euler vector toward N.

Pure N and scalar B remain visually close throughout the nonlinear KH
evolution, but are not identical. Scalar B reaches a transverse-kinetic-energy
peak `0.07155` at `t=6.8002`; N peaks later at `t=7.8003` with `0.06795`.
At `t=10`:

| scheme | rho_min | rho_max | p_min | E_ky | sigma_rho |
| --- | ---: | ---: | ---: | ---: | ---: |
| scalar B | 0.934375 | 1.99647 | 2.30195 | 0.0331321 | 0.198061 |
| N | 1.09597 | 1.95863 | 2.37114 | 0.0320329 | 0.181239 |

Thus N is the robust limiting branch and is modestly more dissipative: its
peak KH growth is about 5 per cent lower and delayed by about one time unit,
and its final density standard deviation is 8.5 per cent below scalar B.
Scalar B retains a visible accuracy/resolution advantage over pure N while
recovering its long-time robustness. Component-wise B instead follows a less
protected trajectory and loses local positive mass at `t=0.873680`.

One qualification should remain visible. From snapshot sums, scalar B's total
mass changes by `+1.94e-3` fractionally through `t=10`, while N changes by
`+2.52e-3`; the corresponding total-energy changes are `-2.98e-4` and
`-4.88e-4`. These are small compared with the local component-B failure but
are not roundoff and belong to the remaining ALE endpoint/rebase conservation
audit.

The attempted four-rank acceleration terminates immediately by design at
`rd_apply_cfl_timestep_constraint()`: the current `RD_ALE_CFL_TIMESTEP`
prototype explicitly supports one rank only. This is a present implementation
limit, not a KH instability.

Analysis and labelled figures (all panels use real AREPO snapshots and one
common density colour scale):

    examples/gresho_2d/plot_kh_b_n_comparison.py
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/N_Glass48_ContourCM_20260820/figures/kh-b-n-density-matched-t0-t08.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/N_Glass48_ContourCM_20260820/figures/kh-b-n-density-matched-t0-t08.pdf
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/N_Glass48_ContourCM_20260820/figures/kh-b-n-density-long-t1-t10.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/N_Glass48_ContourCM_20260820/figures/kh-b-n-density-long-t1-t10.pdf
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/N_Glass48_ContourCM_20260820/figures/kh-b-n-diagnostics.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/N_Glass48_ContourCM_20260820/figures/kh-b-n-diagnostics.pdf
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/N_Glass48_ContourCM_20260820/figures/kh-b-n-diagnostics.json
## 60. 2026-08-21: KH investigation consolidated; scalar B is the temporary f=1 solution

- **Purpose:** consolidate the KH work in sections 39--59, record the temporary
  engineering decision, and audit what the density figures actually render.
- **Deciding test:** smoothed relaxed-glass48 KH (tanh transition width 0.025),
  gamma 1.4, Arpaia equal-step
  ALE, P1(U) contour total, element-comoving frame, full quasi-Lagrangian mesh
  velocity `f=1`, coherent RK2 total residual, one rank.
- **Current decision:** scalar B is the temporary robust moving-mesh KH method;
  pure N is its robust and more dissipative control; pure LDA remains the
  smooth-accuracy reference but is unavailable for long-time moving KH.

This is a temporary solution in the precise sense that it closes the immediate
completion/robustness requirement without claiming an invariant-domain proof,
without explaining pure LDA's secular precursor, and without yet validating
hierarchical timesteps or MPI. It is nevertheless a real `f=1` solution: it
does not obtain robustness by slowing the mesh or adding boundary-layer
smoothing.

### 60.1 What was tried, in chronological order

| attempt | matched observation | decision |
| --- | --- | --- |
| Moving N, contour + comoving + Arpaia, `f=1` (sections 39--40) | completed KH to `t=2`; the later matched glass48 run completed to `t=10` | robust low-order control, visibly diffusive |
| Static versus moving LDA, Roe+split and contour (sections 41--42) | on the production-style glass, static LDA completed `t=2`; moving Roe-LDA failed at `t=1.15515` in the RK predictor and moving contour-LDA failed at `t=0.46442` through endpoint mass loss; moving N completed | genuine long-time moving-LDA regression, not a jitter-only or contour-only effect |
| Jittered versus relaxed-glass geometry (section 42) | jitter strongly amplified Sod/ALE noise, but both moving-LDA KH failures persisted on the glass | physical conclusions now use glass; jitter is only a geometry stress test |
| Component-wise B (sections 43 and 58) | delayed the failure; the final current-source matched run failed at `t=0.873680` while mixing Euler components with different theta values | more accurate than scalar B on Yee, but not a KH robustness method |
| Scalar-theta B (sections 43 and 57) | completed the identical smoothed glass48 KH to `t=10` at `f=1`; theta activity decreased from 0.983 initially to 0.466 at `t=10` | accepted temporary robustness baseline |
| Zero-velocity ALE and no-regularisation controls (section 43) | zero-mesh ALE stayed close to static N; actual motion changed the solution before the first edge flip; disabling ordinary regularisation did not remove the increment | storage alone, regularisation alone and the first flip are not sufficient explanations |
| Entropy-range diagnostic (section 45) | moving LDA developed large entropy excursions while N/scalar B stayed bounded | useful early quality symptom, but its causal interpretation was superseded by section 47 |
| Targeted entropy dissipation (section 47) | reduced the entropy excursion but did not materially change the KH failure time | refuted as the cure; entropy runaway is not the terminal cause |
| Discontinuity-driven mesh-velocity smoothing and stronger regularisation (sections 46 and 48) | reactive corrections changed trajectories/topology but did not rescue the baseline | rejected; they act after the damaging state has formed |
| Uniform fluid-following fraction `f` (sections 47--49) | `f=0.90` completed to `t=10`, while `f=0.95` still failed; Gresho boost-10 error rose by a factor 2.28 at `f=0.90` and 7.87 at `f=0.75` | decisive diagnostic, not an acceptable default: narrow robustness cliff and loss of quasi-Lagrangian advantage |
| Local a-posteriori LDA-to-N retry (section 52) | a six-triangle N star rescued two steps, then failed because the incoming LDA state was already contaminated; expanding to 24.5 per cent of all triangles did not change the bad nodal value; global N from a clean history completed | useful debug tool, but the positivity/mass-ratio detector fires too late; not a production fallback |
| Pure N versus both B forms (sections 58--59) | component B failed at `t=0.873680`; scalar B and N both completed `t=10`; N had a roughly 5 per-cent lower and one-time-unit later transverse-energy peak, and 8.5 per-cent lower final density standard deviation | scalar B is not redundant: it retains more resolved structure than N while inheriting enough N-like robustness |

Local LF, full residual-ratio Bmax, Dobeš--Deconinck Bx, SUPG variants and a
shear-eigenvalue floor were discussed in sections 53--56 but were not executed
as KH production candidates before scalar B passed the bounded sprint. They
remain future accuracy/robustness refinements, not completed attempts and not
prerequisites for beginning timestep/MPI work.

The consolidated scientific reading is deliberately narrower than several
intermediate explanations. The terminal section-52 mesh was globally healthy,
so the recorded failure was not an already inverted or sliver Delaunay mesh.
However, noisy solution-dependent vertex motion may still drive the secular
precursor; that geometry-versus-solution feedback is not fully closed. What is
established is that the full ALE construction can carry the same moving KH with
N and scalar B, while pure LDA and component-wise B cannot. The immediate
remedy therefore belongs on the distribution side, even though later causal
analysis may involve both the solution and its induced geometry.

### 60.2 Comparison-figure index

The most useful summary figures, in reading order, are:

    # Static LDA, moving Roe-LDA, moving contour-LDA and moving N
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/Glass_Sod_KH_ALE_20260818/figures/glass-kh-static-moving-density.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/Glass_Sod_KH_ALE_20260818/figures/glass-kh-static-moving-density.pdf

    # Entropy-floor and mesh-fraction investigations
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_EntropySweep_20260819/figures/kh-entropy-sweep-density.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_EntropySweep_20260819/figures/kh-entropy-sweep-curves.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_FracLong_20260819/figures/kh-fraction-threshold.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_FracLong_20260819/figures/kh-fraction-long.png

    # A-posteriori retry: morphology, precursor and retry-patch growth
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_Aposteriori_20260820/figures/kh_aposteriori_density_comparison.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_Aposteriori_20260820/figures/kh_aposteriori_minima_history.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/KH_Aposteriori_20260820/figures/kh_aposteriori_halo_growth.png

    # Scalar-B long run and limiter activity
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/figures/scalarb-kh-density-t0-t10.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ScalarB_Glass_Sprint_20260820/figures/scalarb-kh-theta-history.png

    # Final matched component-B / scalar-B / pure-N comparison
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/N_Glass48_ContourCM_20260820/figures/kh-b-n-density-matched-t0-t08.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/N_Glass48_ContourCM_20260820/figures/kh-b-n-density-long-t1-t10.png
    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/N_Glass48_ContourCM_20260820/figures/kh-b-n-diagnostics.png

PDF files with the same stems are retained beside all principal density and
diagnostic figures except the three debug-only a-posteriori PNGs.

### 60.3 What the current KH density plot maps to the page

The final comparison is generated by
`examples/gresho_2d/plot_kh_b_n_comparison.py`. It is not a particle scatter
plot. For every snapshot it:

1. reads generator coordinates `x_i` and nodal densities `rho_i` from HDF5
   and reduces coordinates modulo the periodic unit box;
2. constructs a new `matplotlib.tri.Triangulation(x_i,y_i)`;
3. masks triangles whose coordinate span exceeds 0.15 in either direction, as
   a simple way to suppress non-periodic edges drawn across the box seam;
4. calls `tripcolor(..., shading="gouraud")`, which displays

       rho_plot(x)|_T = sum_{a=1}^3 rho_{i_a} phi_a^T(x)

   on every triangle of the plotting triangulation.

The renderer is therefore already P1 in the mathematical sense: Gouraud
shading is barycentric interpolation of the three nodal values. The fragmented
appearance is partly physical/numerical -- a low-resolution glass has irregular
triangles and node-to-node variation -- and partly a presentation issue caused
by many small panels. It is not caused by a nearest-particle or pixel-bin map.

It is not, however, an exact rendering of the RD finite-element field. The
plotting triangulation is reconstructed offline and does not consume AREPO's
actual `DT[i].p[]` connectivity. Near periodic seams and nearly cocircular
point sets, its diagonal/tie choice may differ from the solver's. Masking the
seam deletes cross-periodic elements instead of unwrapping them. The current
plot therefore represents

    P1(snapshot nodal data, reconstructed plotting triangulation),

not a certified

    P1(snapshot nodal data, solver Delaunay triangulation).

The existing `write_only_delaunay_triangulation()` routine can dump `DP`, `DT`
and Voronoi-face data when `RD_OUTPUT_DIAGNOSTICS` is enabled, but the recent KH
runs did not enable it. It also writes only diagnostic sync points, uses
internal point indices and periodic images, and is not aligned with every HDF5
snapshot. Exact historical connectivity cannot be recovered with certainty
from the current snapshots alone.

### 60.4 Recommended exact P1/Delaunay visualisation

Use two levels, with the first available immediately and the second as the
thesis-quality default:

1. **Improved offline reconstruction, no rerun:** tile the generators over a
   3-by-3 periodic image, triangulate the tiled set, retain triangles whose
   barycentres lie in the central box, and rasterise the barycentric P1 field
   before clipping to `[0,1]^2`. This removes seam deletion and is more
   faithful than the present span mask. It still cannot guarantee AREPO's
   diagonal for a degenerate/cocircular quartet.
2. **Exact solver-connected output:** at each requested snapshot, write a
   compact companion connectivity dataset whose vertices are
   `(ParticleID, periodic image offset)` rather than transient `DP` indices.
   Plot those explicit triangles and evaluate
   `U_h|_T=sum_a U_{i_a} phi_a^T` with barycentric coordinates. This
   reproduces the same P1 basis and Delaunay elements used by the residual
   calculation, including periodic boundaries.

For thesis figures, show the exact P1 density without edges in the main time
sequence, plus one selected-time enlarged panel with thin Delaunay edges and
generator points. A separate piecewise-constant Voronoi-cell view can explain
dual storage, but must be labelled as a storage/mesh view rather than the RD P1
solution. Drawing all edges on every small panel would make the current
fragmentation worse rather than clarify it.

This visualisation improvement does not change any completion or scalar-B/N
comparison above. It is needed to make local mesh-scale claims -- slivers,
edge-flip patches, precursor localisation and exact P1 morphology -- directly
auditable from figures.
### 60.5 Boundary-smoothing clarification and the executed non-solutions

The phrase "unsmoothed KH" in earlier entries is retired. Every reported final
glass48 comparison is the **smoothed KH** problem, using

    band(y) = 1/2 [tanh((y-0.25)/0.025) - tanh((y-0.75)/0.025)],

for both density and streamwise velocity. No additional runtime filter or
damping layer is applied. The source and scalar-B IC copies are byte-identical:

    SHA256 e2db4f6f1b3682029f13f93bafd2e1f89dc4b8e6ad0920203d564123b1e47888

Thus the static/moving LDA/N glass figure, the scalar-B long figure, the
component/scalar/N matched figures and the scalar-B theta history all have the
same initial transition width and no additional smoothing during evolution.

For avoidance of ambiguity, the executed remedies that did not become the
solution are:

| intervention | author/campaign | outcome |
| --- | --- | --- |
| change the LDA element total from contour to Roe+split | matched LDA campaigns | both moving forms failed, at different times and through different final checks |
| switch jittered geometry to relaxed glass | section 42 | delayed and reduced artefacts but did not remove either moving-LDA failure |
| component-wise B | sections 43 and 58 | delayed failure to the current matched `t=0.873680`; did not ensure coupled-state admissibility |
| targeted entropy-mode dissipation, `eps=0.1--0.3` | Claude, sections 45--47 | changed entropy excursion but not the order-one failure time |
| shock/all-wave sensor correction to mesh velocity | Codex, section 46, moving-N Sod discriminator | shock arm was nearly inert; active all-wave arm changed topology and extremes but not transverse noise; it was not a direct KH cure |
| stronger ordinary mesh regularisation, up to four times default | Claude, sections 47--48 | `f=1` KH still failed at `t=1.064`, close to the baseline |
| reduce the fluid-following mesh fraction | Claude, sections 47--49 | `f=0.95` still failed; `f=0.90` and 0.75 survived but were rejected as defaults because of a narrow cliff and measured boost/Galilean cost |
| per-step a-posteriori rollback and local LDA-to-N recomputation | Codex, section 52 | two rejected LDA steps were restored and accepted after an N-star retry; the third could not be repaired even after the patch grew to 24.5 per cent because the incoming state was already contaminated |
| enlarge the rollback patch by successive element halos | Codex, section 52 | no change in the bad nodal value once the complete vertex star was covered |
| disable regularisation, zero mesh velocity and inspect first-flip timing | section 43 controls | useful isolation diagnostics, but none supplied a `f=1` LDA remedy |

The local rollback is therefore not a successful solver option. It proved that
state restoration and coherent RK-stage recomputation work, while also proving
that a positivity/mass-ratio trigger acts too late for this secular precursor.
Scalar B is the first executed intervention that both keeps `f=1` and carries
the matched smoothed KH problem to `t=10`.

Local LF, Bmax, Dobeš--Deconinck Bx, SUPG and the shear-eigenvalue floor remain
proposals only. They must not be listed among failed numerical experiments.

---

## 61. 2026-08-21: the offline shear-floor check — the mechanics verified, the `eps ~= 0.45` prediction refuted

- **Author:** Claude Code (Fable 5).
- **Scope:** the offline verification that section 51.1 required to pass
  *before* any simulation campaign, in the section-56.1 gated conservative-split
  form. No build, no cluster, no solver change.
- **Script:** `Hydro_data_analysis/Analysis/moving_mesh/shear_floor_verification.py`
  (pure numpy; reuses `ale_feasibility.py` and the section-44.2 element/state).
- **Verdict:** every structural property claimed for the floor is verified
  exactly, but the quantitative prediction fails: `eps ~= 0.45` recovers only
  about half of the missing shear damping, full recovery needs `eps ~= 0.8`
  (single element) to `1.2` (ensemble), and at those values the floor's cost on
  resolved co-moving shear structures reaches or exceeds what a *static* mesh
  would charge at low Mach. The campaign the prediction was meant to authorise
  should not be launched on its strength.

### 61.1 What is implemented

The section-56.1 form, analytically: per edge,
`lambda_eps^+- = 0.5 [lambda +- max(|lambda|, eps c)]` applied inside the
`K^+/K^-` construction to a selected subset of the degenerate modes, under the
element-level gate `|u - sigma_bar_T| < eps c`. The eigendecomposition is
analytic so that the repeated eigenvalue's subspace can be split into its
entropy and shear directions — a numeric `eig` cannot do that, which is also
why the production implementation will need the analytic form. Two variants:
shear-only (`P_s`) and both degenerate modes (`P_e + P_s`).

### 61.2 Structural properties: all pass, at round-off

| check | result |
| --- | --- |
| E1 reproduce section 44.2 (`eps = 0`) | entropy 0.0000, shear 0.5540 at `sigma = u`; analytic vs numeric `K^+` split max diff 1.7e-17 |
| E3 element gate | static mesh at `eps = 0.45`: `max |K_eps - K| = 0.0` exactly (`|u-sigma|/c = 0.93` > eps, gate off) |
| E4 conservation | per-edge `K^+ + K^- - K = 0.0`; `K` itself unchanged by the floor (1.7e-18); `sum_j K_j = 6.9e-18`; `sum K^+ = -S^-` exactly |
| E5 Galilean covariance | the boost is *linear* on conservative variables, `U' = T U`; `K^{+-}(boosted) = T K^{+-} T^{-1}` to 3.9e-16 against matrix scale 0.35, with and without the floor, at `sigma/u` = 0, 0.6, 1 |

One structural bonus: at `eps = eps*` the shear damping ratio to static is
1.0000 across the *entire* sigma sweep, not only at `sigma = u`, because at
`|w| < c` the acoustic pickup `|w.n - c| + |w.n + c| = 2c` is
sigma-independent and the floored shear eigenvalue is the constant `eps c`.
There is no kink at the gate threshold for this element.

### 61.3 The quantitative prediction fails

On the section-44.2 element and Sod star state, the measured law is exactly

    shear damping ratio(eps) = 0.554 (1 + eps),

so the ratio reaches 1 at `eps* = 1/0.554 - 1 = 0.805`, not at
`1 - 0.554 = 0.446`. Kimi's heuristic assumed the floor's contribution adds
with unit slope; it adds with slope 0.554. Consequences, as predicted
moving/static `RMS(v_y)` amplification (measured value 1.80):

| | `eps = 0` | `eps = 0.446` | `eps = 0.805` | `eps*` |
| --- | ---: | ---: | ---: | ---: |
| section-44.2 element | 1.805 | 1.248 | 1.000 | 0.805 |
| 501-element random ensemble (E9) | 1.971 | 1.511 | 1.228 | **1.210** |

The ensemble row is the design number, since the domain RMS tracks the
ensemble damping: full restoration needs a floor *above the sound speed*.
`eps*` is also strongly element-dependent (E8): rotations of the reference
element give 0.775–0.805, but random glass-like shapes spread 0.53 to beyond
1.5, with 22 per cent having no root below 1.5 at all. A single global `eps`
cannot restore static damping per element; only the ensemble target is
meaningful, and it sits at 1.21.

### 61.4 The cost, measured on exact co-moving states (E7)

N-scheme nodal residual norms for linear co-moving contact and shear
profiles, as a fraction of the same profile's *static-mesh* dissipation:

| profile, state | `eps=0` | shear-only 0.45 | shear-only 0.805 | both 0.45 |
| --- | ---: | ---: | ---: | ---: |
| contact, Sod star (`u/c=0.93`) | 0 | **0** (1e-12) | **0** (1.7e-12) | 0.198 |
| shear, Sod star | 1e-4 | 0.312 | 0.457 | 0.312 |
| contact, Gresho-like (`u/c=0.38`) | 0 | **0** | **0** | 0.486 |
| shear, Gresho-like | 1e-4 | 0.767 | **1.107** | 0.767 |

Three readings:

1. **Shear-only flooring leaves co-moving contacts at machine zero.** The
   moving mesh's contact advantage survives the floor exactly, which both-mode
   flooring destroys (20–49 per cent of the static rate). Combined with
   section 47's result that entropy flooring does nothing for KH, shear-only
   is unambiguously the right variant *if* a floor is used at all.
2. **The floor is `c`-scaled and therefore Mach-blind.** At the Sod state the
   cost on a resolved co-moving shear is 31–46 per cent of static; at a
   Gresho-like `u/c = 0.38` it is 77 per cent at `eps = 0.45` and **111 per
   cent — more diffusive than a static mesh — at `eps = 0.805`**. Since
   ensemble restoration needs `eps ~= 1.2`, fully repairing Sod's transverse
   noise means surrendering the quasi-Lagrangian shear advantage at low Mach,
   mode-selectively but everywhere the gate is open. This is section 54.3-B's
   flagged risk, now quantified: Gresho *is* a shear structure, and a
   boost-0 Gresho arm would be expected to degrade toward or below the static
   result at the `eps` values that actually fix Sod.
3. **The `S^-` claim splits by variant (E6).** Shear-only flooring does *not*
   repair `S^-`: the entropy direction stays in its kernel (worst minimum
   singular value 5e-22, as without the floor). Both-mode flooring makes
   `S^-` uniformly invertible over all 501 test elements (worst minimum
   singular value 3.2e-3, worst condition number 3.5). So retiring the LDA
   pseudo-inverse requires flooring the entropy mode too — at the measured
   contact-diffusion price. Section 56.1's refusal to accept the conditioning
   claim without singular-value data was correct.

### 61.5 Decision recommended to Zhenyu

1. **Do not launch the `eps ~= 0.45` Sod campaign on the section-51.1
   prediction; the prediction is refuted offline.** The floor works exactly as
   designed mechanically, but at affordable `eps` it is a partial mitigation
   (1.97 to ~1.5 ensemble amplification at `eps = 0.45`), not a cure, and the
   curative `eps` costs more on resolved shear than a static mesh charges.
2. The primary Sod path becomes the bounding one already named in sections
   51.1 and 55.3: confirm on glass64/96 that the factor ~1.8 is
   resolution-independent, then state it in the thesis as an explained,
   bounded eigenvalue property of the `sigma = u` design point, with scalar B
   available where the LDA undershoot (a static-mesh defect, section 44.1)
   needs suppressing.
3. If an online data point is still wanted inside the sprint budget, it is
   *one* diagnostic run — glass Sod, shear-only, `eps = 0.45` — to validate
   the offline-to-online mapping against the predicted ensemble ratio ~1.5.
   It should be labelled a mapping check, not a candidate fix, and no `eps`
   sweep should follow it.
4. Any genuine repair needs a *scale-aware* floor — for example scaled by the
   element's own velocity variation `max_ij |u_i - u_j|` (Galilean covariant,
   vanishes on uniform flow, targets mesh-scale shear noise) instead of by
   `c`. That is a new design outside sections 51/56, belongs after the sprint,
   and should inherit this script as its offline gate before any run.

---

## 62. 2026-08-22: published precedents for an RD eigenvalue fix and the space--time ALE alternative

- **Author:** Codex, after a literature audit requested by Zhenyu.
- **Scope:** literature and architecture review only; no new solver build or online shear-floor run.
- **Decision:** the conservative eigenvalue modification has a direct RD precedent and a close nearly-Lagrangian ALE precedent. This justifies one bounded experiment, but not yet a production scheme or positivity claim.

### 62.1 Direct RD precedent

K. Sermeus and H. Deconinck, *An entropy fix for multi-dimensional upwind residual distribution schemes*, Computers & Fluids 34 (2005), 617--640, doi `10.1016/j.compfluid.2003.09.006`, modify the RD upwind matrices as

\[
K_i^{\pm *}=\frac12\left(K_i\pm |K_i|_*\right),
\qquad |K_i|_*=R_i|\Lambda_i|_*R_i^{-1},
\]

with a floor on small acoustic eigenvalue moduli. This is the same operator-level construction as the section-56/61 conservative split and preserves `K_i^{+*}+K_i^{-*}=K_i`. They apply it to multidimensional upwind RD, including N, and remove oblique expansion shocks.

The difference is essential. Their field is genuinely nonlinear, the threshold is derived from a continuous sonic expansion, and the activation is tied to an expansion-shock direction. The ALE entropy and shear fields are linearly degenerate and their zero speed at `sigma=u` is physical. The current candidate is therefore best described as a Sermeus--Deconinck/Harten-type modification extended experimentally to a linearly-degenerate ALE field, not as an established entropy fix or a new formal RD scheme.

### 62.2 Close ALE mechanism precedent

J. Badwaik, P. Chandrashekar and C. Klingenberg, *Single-Step Arbitrary Lagrangian--Eulerian Discontinuous Galerkin Method for 1-D Euler Equations*, Communications on Applied Mathematics and Computation 2 (2020), 541--579, doi `10.1007/s42967-019-00054-5`, identify the closely related mechanism `lambda_c=v-w ~= 0` on a nearly Lagrangian mesh. Spurious contact content generated during strong dynamics then has almost no dissipation and persists. They regularise the contact eigenvalue with a Harten-style scale `delta=alpha c`, using `alpha=0.1`, and remove spurious contact structures in a Shu--Osher calculation while retaining the moving-mesh accuracy advantage.

This is 1-D ALE-DG rather than RD, but directly supports the physical motivation for regularising a linearly-degenerate eigenvalue lost in a nearly Lagrangian frame. Its positivity analysis is for a first-order Rusanov scheme; it does not prove positivity of its modified Roe flux or of the present matrix-N update.

### 62.3 What positivity would require here

For `d >= |lambda|`, the conservative split retains `lambda^{+*} >= 0`, `lambda^{-*} <= 0`, and the scalar N sign structure. The CFL must nevertheless be recomputed with the modified positive eigenvalues. Increasing `K^+` while retaining the old physical ALE signal-speed timestep invalidates the positive-coefficient argument.

For Euler this is not a proof of `rho>0` and `p>0`: matrix-N positivity is characteristic and CFL-conditional, while the current update also contains RK2/F1, Arpaia temporary mass and changing connectivity. Section 61 also proves that shear-only flooring leaves the entropy direction in `ker S^-`; both-mode flooring repairs the sampled ranks but diffuses co-moving contacts. Online runs can test empirical robustness, not establish an invariant-domain theorem.

### 62.4 Space--time positive ALE-RD is structurally different

J. Dobeš and H. Deconinck, *A second order unconditionally positive space-time residual distribution method for solving compressible flows on moving meshes* (PANM 13, 2006, pp. 60--66), obtain positivity with P1 space/linear time space--time elements, two layers `n -> n+1/2 -> n+1`, a Crank--Nicolson-like lower-layer N residual, an upper-layer residual distributed to midpoint and endpoint nodes, implicit relaxation, positive bounded characteristic distribution coefficients, and GCL by construction.

This is not a limiter insertable into the present explicit RK2 + F1 + Arpaia temporary-mass update; it replaces the temporal scheme. Its slabs also require a coherent element connection through time. AREPO rebuilds Delaunay connectivity and flips edges, so a full port needs topology-change space--time elements or a formal remap. Hierarchical timesteps and MPI add asynchronous slab ownership.

Space--time ALE-RD is therefore a valuable long-term reference and possible future replacement, but not a short-term alternative. A fixed-connectivity prototype would not validate the production path with flips, Arpaia mass, hierarchical timesteps and MPI.

### 62.5 Bounded next experiment and status

The short path remains one entropy-fix-style operator experiment: implement a compile-time shear-only split at `eps=0.45`; include modified `lambda^{+*}` in the N CFL; first run a random-positive-state/random-triangle one-step falsification; then, only if it passes, run matched low-resolution static and moving glass Sod. Measure predictor/endpoint `rho_min,p_min`, CFL margin, `S^-` rank, conservation, contact width and RMS/99th-percentile/max `|v_y|`. Stop after this value. A new positivity failure, material static-mesh change or much weaker-than-predicted noise reduction rejects the candidate.

At this entry **no online shear-floor result exists**. Section 61 is offline algebra. Section 47's online entropy-projector experiment was moving-LDA KH, changed the entropy diagnostic, and still failed near `t=1` for all tested eps; it does not answer the shear-only moving-N Sod question. The unmodified high-resolution moving-N Sod remains positive and improves with resolution, but retains visible transverse noise.
---

## 63. 2026-08-23: online shear-only ALE eigenvalue floor on glass48 moving-N Sod

- **Author:** Codex (GPT-5).
- **Status:** implementation and one bounded online mapping check completed.
- **Decision:** the single \(\epsilon_s=0.45\) point is substantially more effective online than the section-61 offline estimate, and restores the transverse-noise statistic to the static-N level. It is promising enough for the next validation gate, but it is not yet a production default or a positivity result.

### 63.1 Implemented operator

The compile-time switch is:

~~~text
RD_ALE_SHEAR_EIGENVALUE_FLOOR=0.45
~~~

It is deliberately restricted to moving, equal-step, N-scheme builds with the ALE-RD CFL selector. It cannot be combined with the earlier entropy-projector experiment.

For face \(j\),

\[
\lambda_{s,j}
=
(\boldsymbol u-\bar{\boldsymbol\sigma}_T)\cdot\hat{\boldsymbol n}_j .
\]

Only when the element gate
\(\lvert\boldsymbol u-\bar{\boldsymbol\sigma}_T\rvert<\epsilon_s c\)
is open, the shear modulus is replaced by

\[
d_{s,j}=\max(\lvert\lambda_{s,j}\rvert,\epsilon_s c),
\qquad
\lambda_{s,j}^{\pm *}=\frac12(\lambda_{s,j}\pm d_{s,j}).
\]

With \(\boldsymbol t_j=(-n_{y,j},n_{x,j})\),

\[
r_{s,j}=(0,t_x,t_y,\boldsymbol u\cdot\boldsymbol t_j)^T,
\qquad
l_{s,j}=(-\boldsymbol u\cdot\boldsymbol t_j,t_x,t_y,0),
\qquad
P_{s,j}=r_{s,j}l_{s,j}^T ,
\]

and the already assembled matrices receive

\[
K_j^{+*}
=
K_j^+
+
\frac{|\boldsymbol n_j|}{4}
(d_{s,j}-|\lambda_{s,j}|)P_{s,j},
\qquad
K_j^{-*}
=
K_j^-
-
\frac{|\boldsymbol n_j|}{4}
(d_{s,j}-|\lambda_{s,j}|)P_{s,j}.
\]

Therefore \(K_j^{+*}+K_j^{-*}=K_j\) exactly. The complete ALE Jacobian and contour total are unchanged; only the N distribution's shear dissipation changes. The implementation is present in both laboratory and element co-moving algebra. In the latter, the laboratory matrices are replaced before use and the correction is reconstructed directly in the shifted variables.

The N CFL code explicitly maximises its existing acoustic bound against
\(\lambda_{s,j}^{+*}\). For \(0<\epsilon_s<1\),

\[
\lambda_{s,j}^{+*}\le c+|\lambda_{s,j}|,
\]

so this check does not tighten the validated acoustic timestep bound. It prevents a future change of scaling from silently omitting the modified eigenvalue.

### 63.2 Offline falsification and build verification

The new regression is tests/rd/test_ale_shear_eigenvalue_floor.py and is registered in make check_rd.

Across 1000 random positive Euler states and random non-degenerate triangles:

| identity | maximum defect |
| --- | ---: |
| \(K^{+*}+K^{-*}=K\), dimensionless backward error | \(4.36\times10^{-16}\) |
| requested shear split eigenvalues | \(1.33\times10^{-13}\) |
| projector identities and acoustic/entropy annihilation | \(6.05\times10^{-16}\) |
| Galilean covariance | \(3.55\times10^{-14}\) |

The complete make check_rd suite passes. The managed shear-floor build completed with MKL and no new compiler warning attributable to the implementation.

Shear-floor artifact:

~~~text
/home/zwu/arepo_rd/arepo/build_artifacts/sod-n-shear-floor-045/000cdaaee46f-7a53c6a0c87cd539/Arepo
SHA256 cefcc51d6a2ebf8b9fde5d8033dbdb3da326cb379a0ed93c976d6ac8419db86a
~~~

Current-source no-floor control:

~~~text
/home/zwu/arepo_rd/arepo/build_artifacts/sod-n-default-moving-current/000cdaaee46f-e5e929a2bcec43ef/Arepo
SHA256 3b169e49377a2fb25513500c251e60c0a849c564f244ee3065c0203daa9edb76
~~~

The current-source control and the stored section-32 default baseline agree exactly at \(t=0.2\): the ID-matched RMS and maximum differences in \((\rho,v_x,v_y,p)\) are all zero. The intervening cleanup therefore does not explain the result below.

### 63.3 Matched online experiment

All moving arms use the same relaxed periodic glass48 IC: 2304 generators, SHA256
8f8fc1d7557398643a9f35b1a0d18de1e5c6cb08d436fbe3f8dd02adc33103ea. They use \(\gamma=5/3\), contour total, element co-moving frame, Arpaia temporary mass, N distribution, total-residual RK2, Courant factor 0.4 and \(t_{\max}=0.2\). The only compile-time difference between the two current-source moving artifacts is the shear floor.

Campaign root:

~~~text
/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_N_ShearFloor_20260823
~~~

Machine-readable analysis:

~~~text
/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_N_ShearFloor_20260823/analysis.json
SHA256 837364296f4fa80b5664bf471846353710df0909643da9cea4226a9e3dddc92f
~~~

Endpoint results:

| quantity at \(t=0.2\) | static N | moving N, \(\epsilon_s=0\) | moving N, shear floor \(0.45\) |
| --- | ---: | ---: | ---: |
| \(L_1(\rho)\) | 0.046588 | 0.038859 | 0.039985 |
| \(L_1(v_x)\) | 0.101982 | 0.110329 | 0.099765 |
| \(L_1(p)\) | 0.051054 | 0.054722 | 0.054602 |
| volume RMS \(|v_y|\) | 0.008490 | 0.014244 | **0.008146** |
| RMS \(v_y\) / static | 1.000 | 1.678 | **0.960** |
| volume-weighted 99th percentile \(|v_y|\) | 0.026593 | 0.061380 | **0.027392** |
| maximum \(|v_y|\) | 0.040527 | 0.129075 | **0.049842** |
| endpoint \(\rho_{\min}\) | 0.148625 | 0.139253 | 0.136442 |
| endpoint \(p_{\min}\) | 0.134974 | 0.120247 | 0.116121 |
| maximum/minimum cell volume | 1.170 | 5.144 | 4.571 |
| total edge flips | 0 | 332 | 273 |

Both moving runs complete. For the floored run, the minimum logged RK predictor values are \(\rho=0.125\), \(p=0.1\); the largest element distribution conservation defect is \(3.72\times10^{-16}\); and the minimum RD-CFL-limit/selected-step ratio is 1.034. The minimum pivot ratio remains zero, as expected: a shear-only floor leaves the entropy direction in \(\ker S^-\) and does not retire the pseudo-inverse path.

The result is stronger than section 61's fixed-geometry offline estimate. The direct dissipation reduces the final volume RMS \(v_y\) by 42.8 per cent and the 99th percentile by 55.4 per cent relative to the matched moving baseline. The online mesh responds as well: flips fall by 17.8 per cent and the volume ratio improves, providing a nonlinear geometry feedback absent from the offline ensemble model. This likely explains why the online RMS reaches the static level rather than the predicted ratio near 1.5.

The cost is visible but modest in this case. Relative to default moving N, \(L_1(\rho)\) rises by 2.9 per cent, while \(L_1(v_x)\) improves and \(L_1(p)\) is unchanged. The floor does **not** improve the endpoint density or pressure minima, so this is not evidence for positivity. It suppresses the transverse linearly-degenerate noise that motivated it.

### 63.4 Figures and interpretation

Profile comparison:

~~~text
/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_N_ShearFloor_20260823/figures/sod-n-shear-floor-profiles.png
SHA256 52480d89be1962c84f06c4aa692d85cfbf94bb00e20553827fc5cd3bc9c9b851
~~~

Evolution:

~~~text
/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_N_ShearFloor_20260823/figures/sod-n-shear-floor-evolution.png
SHA256 f6533452dc5b27a40597d1c1873a9a581b0f1abc16925fa3f61d04670032d563
~~~

Repository copies:

~~~text
useful_resources/moving_mesh_sod/sod-n-shear-floor-eps045-profiles.png
useful_resources/moving_mesh_sod/sod-n-shear-floor-eps045-evolution.png
~~~

The plots show that the floor removes the large asymmetric transverse spikes around the two contact regions and returns the scatter envelope close to static N. The density and pressure profiles remain those of the moving method; the shock/contact locations and overall broadening are not artificially changed into a static-mesh solution.

This one result changes the recommendation from “likely only partial mitigation” to “credible diagnostic candidate”. It still needs two cheap rejection tests before thesis/default consideration:

1. Gresho at boost 0 and 10, because section 61 predicts an \(\epsilon_s c\) floor can damage resolved low-Mach shear;
2. one Yee resolution pair, to detect a loss of the smooth convergence behaviour.

Do not start an epsilon sweep yet. If either rejection test shows material degradation, retain this as an analysis experiment rather than a production scheme. Even if both pass, describe it as a Sermeus--Deconinck/Harten-type ALE shear regularisation with empirical robustness evidence, not as a proved positive RD scheme.

## 64. LDA extension and Gresho/Yee rejection tests (2026-08-23)

The section-63 shear eigenvalue floor was enabled for moving LDA with the same modified \(K_j^\pm\) split; the contour total is unchanged. The tested form is contour + element co-moving frame + Arpaia temporary mass + total-residual RK2 with \(\epsilon_s=0.45\).

### 64.1 Moving-LDA relaxed-glass Sod

| quantity at \(t=0.2\) | static LDA | moving control | moving floor |
| --- | ---: | ---: | ---: |
| \(L_1(\rho)\) | 0.046435 | 0.030156 | **0.024023** |
| \(L_1(v_x)\) | 0.103824 | 0.090402 | **0.075481** |
| \(L_1(p)\) | 0.049790 | 0.039872 | **0.032275** |
| volume RMS \(|v_y|\) | 0.010963 | 0.020098 | 0.019239 |
| volume p99 \(|v_y|\) | 0.039906 | 0.075058 | 0.074514 |
| maximum \(|v_y|\) | 0.066206 | 0.128146 | 0.134812 |
| \(\rho_{\min}\) | 0.148557 | 0.076406 | **0.094886** |
| \(p_{\min}\) | 0.134847 | 0.040880 | **0.054042** |

The floor reduces the three principal errors by 20.3, 16.5 and 19.1 per cent and reduces undershoot. Unlike N, transverse RMS improves by only 4.3 per cent, p99 is unchanged and the maximum is slightly worse. It helps LDA but does not return transverse noise to the static level and is not a positivity result.

~~~text
campaign: /home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_LDA_ShearFloor_20260823
analysis: /home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_LDA_ShearFloor_20260823/analysis.json
figures: /home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_LDA_ShearFloor_20260823/figures/
~~~

### 64.2 Gresho relaxed glass \(48^2\), boost 0/10

The controls are the accepted section-57 endpoints and the floor arms are new endpoint runs. This is not a bitwise current-source Gresho-control rerun: two redundant current controls were stopped early after terminal I/O caused severe slowdown. The compile-off path is supported by the fully matched current-source LDA Sod control above and the earlier exact N-control reproduction.

| mass-weighted \(L_1(v_\phi)\), \(t=1\) | boost 0 | boost 10 |
| --- | ---: | ---: |
| LDA control | \(7.795319\times10^{-3}\) | \(7.795328\times10^{-3}\) |
| LDA floor | **\(7.386879\times10^{-3}\)** | **\(7.386932\times10^{-3}\)** |

The floor improves the error by 5.24 per cent. The floor boost-pair difference is \(5.34\times10^{-8}\), with visually identical de-boosted envelopes. No loss of the boost-10/quasi-Lagrangian advantage is seen.

~~~text
/home/zwu/Hydro_data_analysis/Data_MMRD_debug/ShearFloor_Gresho_Yee_20260823/figures/gresho-lda-shear-floor-boost-pair.png
SHA256 2c62d52d40aa0a8632adef964ca96decd3566ff333b6000cad2abe45fe3fe7c3
~~~

### 64.3 Yee \(32^2/64^2\) pair

These four arms are current-source and switch-for-switch matched.

| moving-LDA arm | \(32^2\) | \(64^2\) | order |
| --- | ---: | ---: | ---: |
| control | \(2.277399\times10^{-3}\) | \(7.347788\times10^{-4}\) | 1.632 |
| floor | **\(1.537984\times10^{-3}\)** | **\(4.781233\times10^{-4}\)** | **1.686** |

The floor reduces the errors by 32.5 and 34.9 per cent without lowering pairwise order. Two resolutions do not prove asymptotic order, but reject immediate first-order degradation.

~~~text
campaign: /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ShearFloor_Gresho_Yee_20260823
analysis: /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ShearFloor_Gresho_Yee_20260823/analysis.json
SHA256 d951b2bede4da40272caa5c5af027566f71657dfe0165e056aca708654b0c239
figure: /home/zwu/Hydro_data_analysis/Data_MMRD_debug/ShearFloor_Gresho_Yee_20260823/figures/yee-lda-shear-floor-resolution-pair.png
~~~

Repository copies of all four figures are in useful_resources/shear_eigenvalue_floor/. The reusable analysis driver is examples/gresho_2d/analyze_lda_shear_floor_validation.py.

### 64.4 Decision

The focused 1000-state/triangle test, make check_rd and git diff --check pass. Both rejection tests pass: the floor preserves boost covariance, does not damage Gresho and does not lower the Yee pairwise order. Retain it as a serious diagnostic/thesis candidate, not an ad-hoc plot fix.

Do not make it the production default yet: positivity is unproved, moving-LDA Sod remains noisier transversely than static LDA, and only one epsilon and one Yee pair were tested. The next low-cost discriminator is long-time smoothed KH with LDA; perform a small epsilon sensitivity check only if needed.

Thesis positioning: present this as an ongoing ALE-RD optimisation with a clear mathematical motivation, successful N-Sod suppression, partial LDA-Sod improvement, and passing smooth-test rejection checks. State explicitly that it is not the default method and that KH robustness, positivity and parameter sensitivity remain open. This gives the result analytical value without overstating its production readiness.

The LDA Sod profile and evolution plots are also copied to:

~~~text
useful_resources/shear_eigenvalue_floor/sod-lda-shear-floor-profiles.png
useful_resources/shear_eigenvalue_floor/sod-lda-shear-floor-evolution.png
~~~

### 64.5 Why moving LDA amplifies the rarefaction oscillation

The larger moving-mesh oscillation in the Sod rarefaction is most plausibly an amplification of LDA's existing dispersive error, not a new failure attributable to one ALE formula.

1. In the expanding fan, a quasi-Lagrangian generator field also expands. The physical node spacing and triangle areas grow, so the fan has lower Eulerian spatial resolution than on the fixed mesh. Glass-scale two-dimensional irregularity is then sampled by fewer triangles.
2. The ALE spectrum is
   \[
   \lambda_\pm=(\boldsymbol u-\boldsymbol\sigma_T)\cdot\widehat{\boldsymbol n}\pm c,
   \qquad
   \lambda_0=(\boldsymbol u-\boldsymbol\sigma_T)\cdot\widehat{\boldsymbol n}.
   \]
   Near the Lagrangian limit, \(\lambda_0\) approaches zero and \(S^-=\sum_jK_j^-\) becomes singular or ill-conditioned in its linearly-degenerate fields. The implemented LDA action,
   \[
   S^-x=\Phi^T,\qquad \Phi_i^{LDA}=-K_i^+x,
   \]
   remains conservative and well defined through the generalized inverse, but its nodal distribution is sensitive to small changes of relative velocity, normals and Roe averages.
3. The nodal storage uses \(Q_i=m_iU_i\). Arpaia re-basing and the topology ledger preserve conservation when \(m_i\) changes, but they do not impose a local maximum principle on \(U_i=Q_i/m_i\). Smooth area evolution, and occasionally flips, can therefore feed a small distribution error back into density and pressure.
4. LDA is linearity preserving rather than monotone. It has no N/B-like nonlinear limiter to remove alternating error at the head and tail of a steep rarefaction.
5. The shear floor cannot directly cure this acoustic feature: its projector annihilates both acoustic eigenvectors and the entropy eigenvector. The observed density/pressure improvement is indirect, through reduced transverse noise and solution--geometry feedback. This explains why improvement is visible but the moving rarefaction remains more oscillatory than static LDA.

The weak dependence on contour versus Roe+split, Arpaia versus Campoli and laboratory versus element co-moving algebra, together with successful Gresho/Yee and conservation/GCL checks, argues against a gross error in one mathematical ALE form. It does not yet distinguish resolution loss from near-singular LDA sensitivity; local plots of error against triangle area, relative Mach number, \(S^-\) conditioning and flip history would do so.

There is currently no credible low-cost production fix. The cheap options are diagnostics or deliberately limited experiments:

- halve the CFL number once to reject a mainly temporal origin;
- use the existing entropy-mode floor in one matched Sod run, which directly tests the missing near-Lagrangian entropy dissipation but cannot stabilize the acoustic fields;
- correlate rarefaction error with area, relative speed, conditioning and flips;
- try scalar-B only as a diagnostic local limiter near the fan edges;
- reduce mesh velocity in expansion only as a diagnostic, since it trades away the quasi-Lagrangian advantage.

A production treatment that preserves smooth LDA accuracy probably needs a principled nonlinear distribution/entropy-stable ALE construction, not parameter tuning. Unless one of the existing low-cost operators gives a decisive result, defer that redesign while proceeding with hierarchical timesteps and MPI parallelisation, and present the present floor study in the thesis as ongoing optimisation.

## 65. Final Sod operator experiment: entropy-mode floor (2026-08-23)

The complete mathematics, motivation, distribution formulas and full result
tables are recorded separately in:

~~~text
dev_log/RD_ALE_LINEARLY_DEGENERATE_DISSIPATION.md
~~~

This campaign is the final Sod tuning attempt.  It compares the accepted
moving N/LDA controls and shear-floor arms against the already implemented
rank-one entropy correction

\[
K_j^+\leftarrow K_j^++\eta_{e,j}P_e,\qquad
K_j^-\leftarrow K_j^--\eta_{e,j}P_e,
\]

with the single motivated value \(\epsilon_e=0.27\).  All arms use the same
relaxed glass48 IC (SHA256
8f8fc1d7557398643a9f35b1a0d18de1e5c6cb08d436fbe3f8dd02adc33103ea),
contour total, element co-moving frame, Arpaia mass and total-residual RK2.
The entropy and shear corrections are tested separately.

### 65.1 Endpoint result

| scheme and metric | control | shear 0.45 | entropy 0.27 |
| --- | ---: | ---: | ---: |
| N global \(L_1(\rho)\) | 0.038859 | 0.039985 | **0.045040** |
| N rarefaction \(L_1(\rho)\) | 0.058837 | 0.060913 | 0.057646 |
| N rarefaction entropy error | 0.024572 | 0.024832 | **0.030025** |
| N RMS \(|v_y|\) | 0.014244 | **0.008146** | 0.011937 |
| LDA global \(L_1(\rho)\) | 0.030156 | **0.024023** | 0.032667 |
| LDA rarefaction \(L_1(\rho)\) | 0.047868 | **0.041175** | 0.045213 |
| LDA rarefaction entropy error | 0.007500 | **0.004431** | 0.006776 |
| LDA RMS \(|v_y|\) | 0.020098 | 0.019239 | 0.020026 |
| LDA \(\rho_{\min}\) | 0.076406 | **0.094886** | 0.072190 |
| LDA \(p_{\min}\) | 0.040880 | **0.054042** | 0.039297 |

For N, the entropy arm makes global density error 15.9 per cent worse and
rarefaction entropy error 22.2 per cent worse.  It reduces transverse RMS by
16.2 per cent, but the shear floor reduces it by 42.8 per cent.

For LDA, the entropy arm gives small rarefaction-density and entropy-error
reductions of 5.5 and 9.6 per cent, but global density/velocity/pressure errors
rise by 8.3/0.8/1.1 per cent, the minima worsen and transverse noise is
unchanged.  The shear arm remains substantially better.

### 65.2 The negative result is mechanistically decisive

Both entropy runs complete and preserve element conservation.  More
importantly, the correction removes the algebraic defect it was designed to
remove:

| diagnostic | N entropy | LDA entropy |
| --- | ---: | ---: |
| minimum \(S^-\) pivot ratio | 0.0999 | 0.1646 |
| maximum F1 lumped count | 0 | 0 |
| maximum relative conservation defect | \(3.79\times10^{-16}\) | \(9.68\times10^{-16}\) |

The matched LDA control and shear arms have zero minimum pivot ratio and up to
4027 rank-deficient F1 lumped events.  Hence the entropy projector is active,
removes the common entropy kernel and eliminates the temporal fallback, yet
does not improve the solution.  Missing entropy-mode dissipation is not the
cause of the remaining moving-mesh rarefaction error.

The remaining evidence points to acoustic LDA/N dispersion, lower Eulerian
sampling in the expanding quasi-Lagrangian fan, and solution--geometry
feedback.  No further Sod operator tuning is planned.  Retain the shear floor
as a non-default ongoing-optimisation result for the thesis; retain the
entropy correction as a mathematically clean diagnostic and negative result.

### 65.3 Reproducibility

~~~text
campaign:
/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_EntropyFloor_Final_20260823
analysis:
/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_EntropyFloor_Final_20260823/analysis.json
SHA256 cf814cd7898ac3c0134e88b7ad7695dfe5d13b597df99ce50dea02e53e875e5f

N entropy binary:
/home/zwu/arepo_rd/arepo/build_artifacts/sod-n-entropy-floor-027-g53/000cdaaee46f-53d8f3ddc58c398a/Arepo
SHA256 04a294f335329ffe5f3d1a10775aa713566da4fa30ceb0c7a2416337304a70fa

LDA entropy binary:
/home/zwu/arepo_rd/arepo/build_artifacts/sod-lda-entropy-floor-027-g53/000cdaaee46f-f2fbbb85ede47a9b/Arepo
SHA256 c8317e47fb317d2e9a8818f05fcbc98f05545ba938dcbbe8b5b41dbb162b3f7e

figures:
/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_EntropyFloor_Final_20260823/figures/sod-entropy-floor-full-profiles.png
SHA256 cdd546e43be9901a1fb28fe75aa9a04fb2da59013804d6b61eb0d71380e506d2
/home/zwu/Hydro_data_analysis/Data_MMRD_debug/Sod_EntropyFloor_Final_20260823/figures/sod-entropy-floor-rarefaction.png
SHA256 03b123a3e5a8fd14550814c7dd90b3e450f91c51099b168ef37f800dbb87ffef
~~~

Repository figure copies are in
useful_resources/shear_eigenvalue_floor/.


---

## 66. 2026-08-23: Kimi's review of sections 56-65 — close the testing phase, with one pre-closure discriminator and two technical notes for the next phase

- **Author:** Kimi (K3), at Zhenyu's request.
- **Scope:** review of sections 56-65 (the scalar-B sprint, the component-B
  controls, the KH consolidation, and the shear/entropy eigenvalue-floor
  campaigns). Advisory only; no code change, no new run.
- **Status:** recommendations for Zhenyu.

### 66.1 Both open problems are now in "explained plus engineering baseline" state

Problem 1 (moving-N Sod transverse oscillation): the mechanism is
quantitatively explained (section 44.2: shear-mode damping 0.554 at
`sigma = u`, predicting and matching the factor 1.80), and the section-63/64
shear eigenvalue floor at `eps_s = 0.45` restores the transverse statistic to
0.96 of static N while passing both rejection tests (Gresho boost covariance
preserved; Yee pairwise order 1.69, not degraded). Section 65 has closed Sod
operator tuning with the decisive entropy-floor negative result.

Problem 2 (moving-LDA KH long-time failure): scalar B completes the matched
smoothed glass48 KH to `t = 10` at `f = 1` with limiter activity *decaying*
(mean total theta 0.983 to 0.466), passes the Galilean gate decisively
(`b10/b0 = 0.99997`), and pays a measured accuracy cost: +19.8 per cent on
matched Gresho `L1(v_phi)` and Yee orders 1.41/1.40 against LDA's 1.63/1.71
(section 57). Component-wise B is not redundant (more accurate on Yee, fails
KH at `t = 0.87`; section 58.4). The section-53.6 stopping rule is met.

**Recommendation: the testing phase can be closed.** Both problems have a
recorded mechanism or a recorded limitation plus a working `f = 1`
configuration, which is exactly the state the section-53.6 stopping rule was
designed to produce. Development effort should move to the section-53.6
engineering order: moving equal-step MPI, then the moving hierarchical
ledger on one rank, then the combination.

### 66.2 One pre-closure discriminator still worth its single run

Section 64.4 already named it: **long-time smoothed KH with moving LDA plus
the shear floor.** It is decision-relevant for what the hierarchical/MPI
phase should treat as the production scheme:

- If LDA + floor survives to `t = 10`, the accuracy-optimal default becomes
  LDA + shear floor (Yee order 1.69, Gresho boost covariance exact, no
  N-blending cost), and scalar B is demoted to the robustness fallback.
- If it fails, scalar B's position as the temporary production baseline is
  final, and the remaining pure-LDA shear limitation is a thesis statement.

One run, one rank, existing binaries; it should not grow into a sweep. This
is a cheaper and more informative closure experiment than the glass64/96
resolution check of the factor 1.80 (section 61.5 item 2), which the shear
floor has largely superseded and which can be deferred to thesis-writeup
time.

### 66.3 Technical notes for the hierarchical-timestep phase

1. **The B scheme is currently excluded from hierarchical timesteps by
   construction.** The compile-time guard in
   `src/hydro/residual_distribution_solver.c` ("RD_RK2_TOTAL_RESIDUAL with
   B_SCHEME is an equal-bin experiment; the hierarchy has only been derived
   for the N and LDA temporal terms") means that if scalar B is the
   production robustness scheme, the hierarchical phase must first define
   what the frozen total-residual theta means across time bins: whether
   theta is computed per bin from the local residual ratio, frozen at the
   coarse-bin level, or blended separately per bin. This is a derivation
   task before it is an implementation task, and it is the strongest argument
   for running the section-66.2 discriminator first — LDA + floor needs no
   such derivation, since the LDA hierarchy already exists.
2. **Two MPI obstacles are already on record.** (a)
   `RD_ALE_GEOMETRY_DIAGNOSTICS` Stage 0 is deliberately single-rank; the
   section-57.1 two-rank startup failure was this switch, not a physics
   failure, and MPI validation runs must build without it (or guard it).
   (b) The LU-pivot-ratio branch selecting the pseudo-inverse path
   (`rd_solve_upwind_system`) is round-off-sensitive and therefore a
   candidate source of domain-decomposition dependence (section 1, item 4 /
   section 3.4 of the carried-forward list). One MPI-invariance control
   should be run with `RD_ALWAYS_PSEUDOINVERSE` to separate that branch from
   any observed rank-count dependence, before rank-dependent results are
   attributed to the exchange logic.

### 66.4 Standing qualifications to carry into the thesis text

- Scalar B is a temporary engineering baseline: it has no invariant-domain
  proof, its KH entropy excursion peaks at 0.8 (the contour-total entropy
  quality defect of section 45.3 is not repaired), and the late-time KH field
  is visibly mixed — completion is not an accuracy endorsement.
- The shear floor is a Sermeus--Deconinck/Harten-type regularisation with
  empirical evidence at one `eps_s` and one mesh family; it is not the
  default and is not a positivity mechanism (section 63.4).
- The geometry-versus-solution feedback question for the LDA precursor
  (section 60.1) remains formally open; the terminal event is solution-first,
  but the driver of the secular drift is not closed.

---

## 67. 2026-08-23: phase-entry assessment — concur on closure, with one added prerequisite

- **Author:** Claude Code (Fable 5), at Zhenyu's request.
- **Scope:** review of sections 62-66 and the decision whether the moving-mesh
  hierarchical-timestep / MPI phase can start. Advisory; no code change, no
  new run.
- **Verdict:** yes. The section-53.6 stopping rule is met, section 66.1's
  closure recommendation is endorsed, and the engineering order stands:
  moving equal-step MPI, then the hierarchical ledger on one rank, then the
  combination. Two things should happen at the front of that phase: the
  section-66.2 discriminator run, and a conservation-drift attribution that
  Kimi's checklist does not contain.

### 67.1 A correction to section 61's expectation, recorded honestly

Section 61 predicted that `eps_s = 0.45` would be a partial mitigation only
(ensemble RMS amplification ~1.5 against the measured 1.68-1.80). The online
result of section 63 is 0.960 — better than static. The offline ensemble
model missed the nonlinear solution-geometry feedback that section 63.4
identifies: once the transverse noise is damped, the mesh itself improves
(17.8 per cent fewer flips, better volume ratio), which further reduces the
noise source. The offline gate did its intended job — it rejected the false
`eps* = 0.446` full-restoration prediction and forced the shear-only variant
that leaves contacts untouched — but as an estimate of online effectiveness
it was conservative, and the record should say so. The same feedback blindness
cuts both ways and is why offline models in this project bound mechanisms, not
outcomes.

### 67.2 Why the section-66.2 discriminator should run before, not after

The KH run of moving LDA + shear floor to `t = 10` is not merely a nice-to-have
closure experiment; it selects how much derivation work the hierarchical phase
contains. The compile-time guard in `residual_distribution_solver.c` excludes
`B_SCHEME` from `RD_RK2_TOTAL_RESIDUAL` hierarchical bins because the
frozen total-residual theta has no defined meaning across time bins. So:

- LDA + floor survives KH: the production scheme for the hierarchical phase
  is LDA (+ floor as a non-default option), whose hierarchy already exists
  from the static phase; scalar B remains the equal-step robustness fallback
  and the theta-across-bins derivation is deferred indefinitely.
- LDA + floor fails KH: scalar B's baseline status is final, and the
  hierarchical phase begins with a derivation task (per-bin versus
  coarse-bin-frozen theta), which must then be budgeted rather than
  discovered mid-implementation.

One run, one rank, existing binaries; it can run while the MPI groundwork
below is prepared, but its answer is needed before the hierarchical ledger
work is scoped.

### 67.3 Added prerequisite: attribute the section-59.3 conservation drift

Section 59.3 records fractional total-mass changes through the KH `t = 10`
runs of `+1.94e-3` (scalar B) and `+2.52e-3` (N), explicitly "not roundoff",
assigned to the outstanding ALE endpoint/rebase conservation audit and left
open. For the robustness discussion that was acceptable. For the next phase
it is not: the static phase's primary validation gates were conservation
exact to round-off and rank invariance by ParticleID, and those are precisely
the gates the equal-step MPI work will need. A single-rank equal-step
baseline that drifts at `2e-3` makes the most sensitive MPI gate unusable.

The attribution has two branches with very different costs:

1. a diagnostic artifact — snapshot sums formed from density times Voronoi
   volume rather than the stored dual masses `Q_i`/`m_i`, which the ALE
   storage does not require to agree at the `1e-3` level. Half a day: rerun
   the sums on the stored masses and on the conservation ledger the solver
   already logs (section 63.3 records element conservation defects at
   `1e-16`, which makes this branch likely);
2. a real solver drift in the endpoint/rebase path, in which case it must be
   found and fixed before MPI validation begins, because every subsequent
   gate inherits it.

Either way the audit is short, and it converts the strongest validation
instrument of the static phase back into a usable gate. It should be the
first task of the engineering phase, alongside the discriminator run.

### 67.4 Known obstacles carried into the phase, consolidated

From sections 57, 59, 63 and 66.3, with one addition:

1. `RD_ALE_CFL_TIMESTEP` is by design single-rank and terminates multi-rank
   runs at `rd_apply_cfl_timestep_constraint()` (section 59.3). Making its
   reduction MPI-aware is the natural first implementation task of the
   equal-step MPI step.
2. `RD_ALE_GEOMETRY_DIAGNOSTICS` Stage 0 is deliberately single-rank
   (section 57.1's two-rank startup failure); MPI builds must omit or guard
   it.
3. The LU-pivot-ratio branch selecting the pseudo-inverse is
   round-off-sensitive and a candidate source of domain-decomposition
   dependence; run one MPI-invariance control with `RD_ALWAYS_PSEUDOINVERSE`
   before attributing any rank dependence to the exchange logic
   (section 66.3, carrying section 3.4).
4. The shear floor itself is element-local with no communication footprint
   and adds no MPI obstacle; its CFL contribution is already bounded by the
   acoustic limit (section 63.1).
5. Deferred by agreement: the glass64/96 resolution check of the factor 1.80
   (to thesis-writeup time, per section 66.2), and any epsilon sensitivity
   study (single value `eps_s = 0.45` stands until the discriminator and the
   engineering phase say otherwise).

### 67.5 Recorded position

The testing phase closes with both problems in the state the stopping rule
required: Sod explained and instrumented (sections 44, 63-65), KH carried by
scalar B at `f = 1` with its costs measured (sections 57-60). The moving
hierarchical-timestep / MPI phase starts with, in order: the section-59.3
conservation attribution, the section-66.2 LDA-plus-floor KH discriminator,
then moving equal-step MPI per section 53.6.

## 68. Topology-change conservation repair proposed for review (2026-08-24)

**Author:** Codex
**Scope:** mathematics and algorithmic contract only; no source change and no new
production run in this section.
**Status:** proposal for Claude review before implementation.

### 68.1 Why formal order is not a sufficient answer to the observed drift

Let the globally summed discrete conserved state after step \(n\) be
\(\mathcal Q^n=\sum_i Q_i^n\), and let a topology event introduce the defect

\[
  \delta^n = \mathcal Q^{n+1}-\mathcal Q^n .
\]

After \(N\) events,

\[
  \mathcal Q^N-\mathcal Q^0 = \sum_{n=0}^{N-1}\delta^n.
\]

A local defect of formal size \(O(h^p)\) does not imply a small long-time
invariant error.  If the event defects have a non-zero signed mean, they add as
\(N_{\rm flip}O(h^p)\), rather than cancelling statistically as
\(\sqrt{N_{\rm flip}}O(h^p)\).  Moreover, the number of topology events itself
can grow as the resolution is increased, and a sharp layer only supplies a
local estimate such as \(O(h^2[U])\), not the smooth-solution estimate.

This separates two requirements which should not be conflated:

1. the LDA/N update may retain its designed order for the solution norm;
2. the global invariants should nevertheless be preserved by an algebraic
   identity, to roundoff, at every topology transfer.

The current scalar-B fixed-grid/moving-grid diagnostic makes the distinction
visible.  In the recorded run,

\[
\begin{aligned}
 M(0) &= 1.4999719023504383,\\
 M(T) &= 1.5028869545126289,\\
 \frac{M(T)-M(0)}{M(0)} &= 1.94\times10^{-3},
\end{aligned}
\]

while the N result reaches \(2.52\times10^{-3}\).  For scalar B there are
\(30055\) measured steps: \(2659\) without flips and \(27396\) with flips.
The no-flip median and maximum endpoint defects are approximately
\(2.72\times10^{-13}\) and \(5.77\times10^{-11}\); the flip-step values are
\(2.05\times10^{-5}\) and \(3.45\times10^{-4}\).  The signed cumulative
contributions are approximately

\[
  \sum_{\rm no\ flip}\delta M=-2.37\times10^{-9},\qquad
  \sum_{\rm flip}\delta M=+2.915054\times10^{-3}.
\]

Thus the typical signed contribution per flip step is only
\(1.06\times10^{-7}\), but it is biased.  The temporary trajectory reaches
roughly \(+3.1825\times10^{-3}\), followed by a final rebase contribution of
about \(-2.6744\times10^{-4}\).  The final \(10^{-3}\) error is therefore a
long accumulation of small topology-correlated defects, not a single failed
hydrodynamic step.

**Decision:** formal accuracy remains a necessary consistency check, but it is
not an acceptance criterion for a conservation invariant.

### 68.2 Transfer problem and required identities

Consider one connected retriangulation patch \(P\), the symmetric difference
between the old and new triangulations at the same physical time.  Decompose
the lumped basis mass of each affected vertex into the unchanged exterior part
and the patch part:

\[
  m_i^\pm = m_{i,\mathrm{out}} + m_{i,P}^\pm,\qquad
  \Delta m_i = m_{i,P}^+ - m_{i,P}^- .
\]

Here \(-\) and \(+\) denote the old and new connectivity, pulled back to the
same physical time and periodic image.  For a \(P_1\) basis on the same patch
domain, partition of unity and linear reproduction give

\[
  \sum_{i\in P}\Delta m_i=0,\qquad
  \sum_{i\in P}\Delta m_i\,\boldsymbol x_i=\boldsymbol 0.
  \tag{68.1}
\]

Let \(\boldsymbol U_i=(\rho,\rho\boldsymbol v,E,\ldots)_i\), and let
\(\boldsymbol Q_i=m_i\boldsymbol U_i\) be the lumped nodal conserved state.
The topology operator \(\mathcal T_P\) should satisfy:

\[
\begin{array}{ll}
\text{patch conservation:}&
 \displaystyle\sum_{i\in P}\boldsymbol Q_i^+
 =\sum_{i\in P}\boldsymbol Q_i^-,\\[1ex]
\text{uniform-state/GCL exactness:}&
 \boldsymbol U_i^-=\boldsymbol U_0
 \Longrightarrow \boldsymbol U_i^+=\boldsymbol U_0,\\[1ex]
\text{linear exactness:}&
 \boldsymbol U(\boldsymbol x)=\boldsymbol a+B\boldsymbol x
 \Longrightarrow \boldsymbol U_i^+=\boldsymbol U(\boldsymbol x_i),\\[1ex]
\text{locality:}&
 \boldsymbol Q_i^+=\boldsymbol Q_i^-\quad(i\notin P),\\[1ex]
\text{admissibility:}&
 \rho_i^+>0,\quad
 e_i^+=E_i^+-\frac{|\boldsymbol m_i^+|^2}{2\rho_i^+}>0.
\end{array}
\tag{68.2}
\]

The operator must be independent of whether the subsequent residual
distribution is LDA, N, or scalar B.  It repairs a change of representation,
not the PDE residual.

### 68.3 Method to advance: local conservative high-order patch correction

If the nodal primitive/conservative values are simply retained while the basis
masses jump, the provisional new state is
\(\widetilde{\boldsymbol Q}_i^+=m_i^+\boldsymbol U_i^-\).  Its patch defect is

\[
  \boldsymbol D_P
  =\sum_{i\in P}\Delta m_i\,\boldsymbol U_i^-.
  \tag{68.3}
\]

Choose non-negative local weights with

\[
  w_i\ge0,\qquad \sum_{i\in P}w_i=1.
\]

The initial choice proposed for testing is the new patch-mass fraction

\[
  w_i=\frac{m_{i,P}^+}{M_P},\qquad
  M_P=\sum_{j\in P}m_{j,P}^+.
  \tag{68.4}
\]

Define the high-order topology increment and transferred state by

\[
\boxed{
  \Delta\boldsymbol Q_i^H
   =\Delta m_i\,\boldsymbol U_i^- - w_i\boldsymbol D_P,
  \qquad
  \boldsymbol Q_i^{H,+}
   =\boldsymbol Q_i^-+\Delta\boldsymbol Q_i^H .
}
\tag{68.5}
\]

This construction has the following exact properties.

**Patch conservation.**  From (68.3)-(68.5),

\[
  \sum_{i\in P}\Delta\boldsymbol Q_i^H
  =\boldsymbol D_P-\boldsymbol D_P=0.
  \tag{68.6}
\]

**Uniform-state exactness.**  If
\(\boldsymbol U_i^-=\boldsymbol U_0\), then by (68.1)

\[
  \boldsymbol D_P
  =\boldsymbol U_0\sum_i\Delta m_i=\boldsymbol0,
\]

and hence
\(\boldsymbol Q_i^{H,+}=m_i^+\boldsymbol U_0\).

**Linear exactness.**  If
\(\boldsymbol U_i^-=\boldsymbol a+B\boldsymbol x_i\), then (68.1) gives

\[
 \boldsymbol D_P
 =\boldsymbol a\sum_i\Delta m_i
  +B\sum_i\Delta m_i\boldsymbol x_i
 =\boldsymbol0.
 \tag{68.7}
\]

The nodal linear state is therefore unchanged by the transfer.  For a smooth
state, Taylor expansion about a patch point and the cancellation of constant
and linear terms give

\[
  \boldsymbol D_P=O(M_P h_P^2\|\nabla^2\boldsymbol U\|),
  \qquad
  \frac{w_i\boldsymbol D_P}{m_i^+}
  =O(h_P^2\|\nabla^2\boldsymbol U\|).
  \tag{68.8}
\]

Thus the correction is second-order small in a smooth region while making
conservation exact.  At a discontinuity it is not assumed to be high order;
that case is delegated to the admissible fallback below.

Equation (68.5) is also the solution of a simple constrained least-change
problem.  Writing the corrective redistribution as
\(\boldsymbol c_i=-w_i\boldsymbol D_P\), it minimizes, component by component,

\[
  \min_{\{\boldsymbol c_i\}}
  \frac12\sum_{i\in P}\frac{\|\boldsymbol c_i\|^2}{w_i}
  \quad\text{subject to}\quad
  \sum_{i\in P}\boldsymbol c_i=-\boldsymbol D_P.
  \tag{68.9}
\]

This interpretation makes the unresolved design choice explicit: whether
\(w_i\) should use new patch masses, full new lumped masses, or a
geometry/conditioning-aware metric.  New patch mass is the proposed first
choice because it is local to the changed basis and has a direct low-order
interpretation.

### 68.4 Method to advance: admissible low-order fallback and convex limiting

For robustness near a shock or a contact, decompose only the changed patch
contribution.  Define its old conservative average

\[
  \overline{\boldsymbol U}_P
  =\frac{\sum_{j\in P}m_{j,P}^-\boldsymbol U_j^-}
         {M_P},
  \qquad
  M_P=\sum_jm_{j,P}^-=\sum_jm_{j,P}^+.
  \tag{68.10}
\]

The low-order remap replaces the old patch contribution by the same admissible
average on the new patch masses:

\[
\boxed{
  \Delta\boldsymbol Q_i^L
   =m_{i,P}^+\overline{\boldsymbol U}_P
    -m_{i,P}^-\boldsymbol U_i^- .
}
\tag{68.11}
\]

It is conservative because

\[
  \sum_i\Delta\boldsymbol Q_i^L
  =M_P\overline{\boldsymbol U}_P
   -\sum_i m_{i,P}^-\boldsymbol U_i^-=\boldsymbol0.
  \tag{68.12}
\]

If all \(m_{i,P}^\pm\) are non-negative and the old states are admissible, then
\(\overline{\boldsymbol U}_P\) lies in the convex Euler admissible set

\[
  \mathcal G_\epsilon
  =\left\{\boldsymbol U:
    \rho\ge\epsilon_\rho,\quad
    E-\frac{|\boldsymbol m|^2}{2\rho}\ge\epsilon_e
   \right\}.
  \tag{68.13}
\]

The exterior contribution is left untouched.  A common scalar limiter for the
whole conserved vector is then used:

\[
  \boldsymbol Q_i^+(\alpha)
   =\boldsymbol Q_i^{L,+}
    +\alpha\left(
       \boldsymbol Q_i^{H,+}-\boldsymbol Q_i^{L,+}
     \right),
  \qquad 0\le\alpha\le1.
  \tag{68.14}
\]

Choose the largest patch-common \(\alpha\) for which every affected nodal state
belongs to \(\mathcal G_\epsilon\).  Both endpoints are conservative and the
same \(\alpha\) is used for all nodes and conserved components, so (68.14)
remains exactly conservative.  Convexity supplies the admissibility argument.

This is deliberately a topology-transfer limiter only.  It does not claim an
invariant-domain proof for the complete RK2 RD update.  Diagnostics must record
the number of limited patches, the distribution of \(\alpha\), and the
low-order fraction of the total transferred mass/energy.  If limiting is
frequent away from discontinuities, the transfer or its mass decomposition is
wrong rather than merely under-limited.

### 68.5 Required placement in the time integrator

The intended factorization of one moving-mesh step is

\[
  \underbrace{
    (\boldsymbol Q^-,m^-,\mathcal T^-)
    \xrightarrow{\ \mathcal T_{\rm topo}\ }
    (\widehat{\boldsymbol Q},m^+,\mathcal T^+)
  }_{\text{same physical time}}
  \xrightarrow{\ \mathcal A_{\rm ALE,RK2}\ }
  (\boldsymbol Q^{n+1},m^{n+1},\mathcal T^{n+1}).
  \tag{68.15}
\]

The topology transfer must use the state saved before drift and the actual old
basis/connectivity.  It must not be applied after RK2 as a global repair,
because that would mix representation error with physical ALE evolution.
Arpaia preparation should receive \((\widehat{\boldsymbol Q},m^+)\), not a
state that silently combines old nodal values with new masses.

Implementation therefore needs, for each topology event or connected event
cluster:

- old and new patch connectivity long enough to evaluate
  \(m_{i,P}^-\) and \(m_{i,P}^+\);
- a coherent periodic image for all moment checks;
- one transfer per topology change, before the continuous ALE residual;
- per-component checks of (68.1), (68.6), positivity, and finite values;
- scheme-independent application before LDA/N/scalar-B branching.

For later hierarchical timesteps, the algebraic transfer is still local, but
the event time and ownership must be defined separately: active and inactive
vertices cannot each apply a partial version of the same patch transfer.  That
is an MPI/hierarchy integration question, not a reason to weaken (68.6).

### 68.6 Earlier antisymmetric graph operator: retain as an alternative, not the first implementation

The previously discussed graph construction seeks coefficients

\[
  a_{ij}=-a_{ji},\qquad
  \sum_j a_{ij}=\Delta m_i,
  \tag{68.16}
\]

and defines

\[
  \Delta\boldsymbol Q_i^A
  =\sum_j a_{ij}
     \frac{\boldsymbol U_i^-+\boldsymbol U_j^-}{2}.
  \tag{68.17}
\]

Antisymmetry makes global conservation exact, and (68.16) makes a uniform state
exact.  However, for a linear field,

\[
  \Delta\boldsymbol Q_i^A-\Delta m_i\boldsymbol U_i^-
  =\frac12 B\sum_j a_{ij}
       (\boldsymbol x_j-\boldsymbol x_i).
  \tag{68.18}
\]

Linear exactness therefore requires the additional vector constraints

\[
  \sum_j a_{ij}(\boldsymbol x_j-\boldsymbol x_i)=\boldsymbol0
  \quad\text{for every }i.
  \tag{68.19}
\]

Those constraints are not implied by antisymmetry and the row sums.  Solving a
constrained graph-flow problem may be worthwhile later, but signs,
conditioning, solvability on small flip graphs, and positivity then become
non-trivial.  The unaugmented antisymmetric form should not be promoted as the
primary repair.  Equation (68.5) obtains conservation plus linear exactness
with a smaller first implementation and a transparent limiter path.

### 68.7 Methods not proposed for the first repair

#### 68.7.1 Global post-step renormalization

For example,

\[
  \boldsymbol Q_i\leftarrow
  \boldsymbol Q_i
  -\omega_i\left(
    \sum_j\boldsymbol Q_j-\boldsymbol{\mathcal Q}_0
   \right)
\]

can force a global sum to match its initial value.  It is useful as a
diagnostic: if it alone cures the long-time drift, the attribution is
confirmed.  It is not proposed as the solution because it is non-local,
changes cells unrelated to the flip, obscures the responsible lifecycle
stage, can violate positivity, and does not define a consistent transfer for
momentum and energy.  A component-wise multiplicative rescaling has the same
objections and additionally changes velocity or thermodynamics unless all
components use a physically unjustified common factor.

#### 68.7.2 Replacing Galerkin/lumped basis masses by Voronoi volumes

A Voronoi volume is geometrically continuous under a Delaunay flip, but the RD
mass and residual are derived from the simplicial \(P_1\) basis.  Substituting a
different control volume in only the time derivative changes the semidiscrete
method and its GCL/order analysis.  It may define another valid scheme, but it
is not a local repair of the present one.

#### 68.7.3 Suppressing flips, reducing the mesh-motion factor, or over-regularizing

These can reduce the event count,

\[
  |\mathcal Q^N-\mathcal Q^0|
  \lesssim N_{\rm flip}\max_n|\delta^n|,
\]

but do not make \(\delta^n=0\).  They trade the symptom against mesh quality and
do not survive general moving meshes.  Fixed-connectivity and no-flip runs
remain controls, not production remedies.

#### 68.7.4 Exact old/new overlap projection

A full conservative remap can be written schematically as

\[
  M^+\boldsymbol U^+
   =C^{+,-}\boldsymbol U^-,
  \qquad
  C_{ij}^{+,-}=\int_{\Omega}
       \phi_i^+(\boldsymbol x)\phi_j^-(\boldsymbol x)\,d\boldsymbol x.
  \tag{68.20}
\]

With exact overlap integration it offers a principled projection and can be
made constant/linear exact.  It is not proposed first because it requires
robust intersections of old and new simplices, periodic bookkeeping, a
consistent choice of lumped versus consistent mass matrices, and a positivity
strategy.  It is the clean fallback if the local patch formula fails the
verification gates.

#### 68.7.5 Fictitious continuous deformation and swept topology flux

One may connect the old and new triangulations through a fictitious
space-time deformation and integrate a conservative swept-volume flux so that
the discrete geometric conservation law holds through the connectivity
change.  This is the strongest geometric interpretation and is related to
published conservative ALE remapping across topology changes.  It is not the
first implementation because the present evidence points to a correctable
local basis jump, while a swept construction requires robust space-time
polytope geometry, event ordering, degeneracy handling, and substantially
more code.

#### 68.7.6 Full space-time ALE residual distribution

Treating flips as faces of a space-time tessellation can unify mesh motion,
topology change, and conservation in one formulation.  It is a research
programme rather than a thesis-scale closing fix, and it would delay the
hierarchical-timestep/MPI work.  It should remain future work unless both the
local transfer and exact overlap remap fail.

### 68.8 Verification gates before production use

The proposed transfer should not be accepted from the KH mass curve alone.

1. **Stationary isolated flip.**  No physical time advance; prescribe constant,
   linear, and quadratic fields.  Constant and linear errors and every global
   conserved component must be at roundoff.
2. **Smooth scaling.**  On geometrically similar patches, the quadratic-state
   nodal change from the high-order correction must scale as \(h^2\).
3. **Flip cascades and periodic boundaries.**  Check connected event clusters,
   alternate diagonals repeatedly, and translations across the periodic seam.
4. **Discontinuous states.**  Exercise density/pressure jumps and near-vacuum
   states; verify positivity and limiter statistics.
5. **Lifecycle controls.**  Uniform moving flow and a no-flip run must remain
   unchanged; transfer must fire exactly once per connectivity change.
6. **Scheme independence.**  Repeat the conservation audit with LDA, N, and
   scalar B.  The topology defect should be roundoff in all three.
7. **Fluid regressions.**  Re-run the existing moving Gresho/Sod diagnostics and
   the KH discriminator; conservation repair must not erase their established
   conclusions.
8. **MPI/hierarchy gate, later.**  Patch ownership must be deterministic
   (for example, the minimum persistent vertex ID), ghost contributions must be
   accumulated once, and the serial/equal-step MPI result must agree to
   roundoff before asynchronous activation is enabled.

Acceptance for the topology operator is stricter than solution accuracy:

\[
 \frac{\left|\sum_i\boldsymbol Q_i^+
             -\sum_i\boldsymbol Q_i^-\right|}
      {\max(1,\left|\sum_i\boldsymbol Q_i^-\right|)}
 \lesssim C\,\epsilon_{\rm mach}
 \tag{68.21}
\]

per event cluster, apart from explicitly documented parallel reduction order.

### 68.9 Questions for Claude's review

1. Is the decomposition into non-negative old/new patch basis masses well
   defined with the current mass-lumping convention for every 2-D flip cluster?
2. Does the implementation retain enough pre-drift connectivity to evaluate
   both patch mass sets at one physical time, or is an explicit old-patch
   snapshot required?
3. Are the two moment identities in (68.1) exact for the actual periodic
   coordinate unwrapping and boundary treatment?
4. Is the new patch-mass weight (68.4) preferable to a full-mass or
   condition-number-weighted minimum-norm correction?
5. Can the low-order decomposition (68.11) be guaranteed non-negative, or can
   a lumped vertex receive signed patch contributions in the existing code?
6. Is the Euler admissible-set limiter in (68.14) sufficient for all advected
   fields, or do scalar bounds/species constraints require additional common
   restrictions on \(\alpha\)?
7. Is there any RK2 stage in which the code currently combines
   \(\boldsymbol U^-\) with \(m^+\) before the proposed transfer point?
8. Should connected simultaneous flips be treated as one patch to preserve the
   moment identities, rather than corrected one edge flip at a time?
9. Does the constrained antisymmetric graph operator have an implementation
   advantage in the present data structures large enough to justify solving
   (68.19), or should it remain an alternative?

### 68.10 Proposed position pending review

Advance (68.5) as the high-order local topology transfer, with (68.11)-(68.14)
as its conservative admissible fallback.  Require roundoff patch conservation,
uniform-state exactness, and linear exactness before any KH production run.
Keep the antisymmetric graph construction only as a constrained alternative.
Use global renormalization solely as an attribution experiment.  Do not advance
Voronoi substitution, flip suppression, exact overlap projection, fictitious
swept remap, or a full space-time ALE formulation unless the local method fails
a stated verification gate.

## 69. Conservative flip-patch repair passes the offline go/no-go audit (2026-08-24)

**Author:** Codex
**Scope:** two-dimensional offline geometry and state-transfer tests only; no
AREPO source change, no MPI, no hierarchical timestep, and no hydrodynamic
production run.
**Decision:** pass the offline gate and advance to a minimal one-rank
equal-step online prototype. Do not yet claim that the production KH drift is
fixed.

### 69.1 Artifacts and exact commands

The existing topology audit was extended, without changing its previous test
logic, to expose the full old/new lumped masses and the old/new contribution of
each connected symmetric-difference patch:

- `/home/zwu/Hydro_data_analysis/Analysis/moving_mesh/ale_topology_defect.py`
- SHA256:
  `0084f8c947c3db77a0c9114c93f7fe2e23d170432c2d74636040f2dea7541494`

A separate repair audit was added:

- `/home/zwu/Hydro_data_analysis/Analysis/moving_mesh/ale_topology_repair.py`
- SHA256:
  `f1bbabb7489a4ddaee2efac5779477fedf7888fe18ffb4aa9406226735ed7559`

The full repair command was

```text
python3 Analysis/moving_mesh/ale_topology_repair.py \
  --steps 12 \
  --long-steps 80 \
  --trials-per-patch 40 \
  --max-adversarial-patches 60
```

The independent regression command was

```text
python3 Analysis/moving_mesh/ale_topology_defect.py \
  --steps 12 \
  --long-steps 0
```

Both scripts also passed `python3 -m py_compile`.

The repair audit reported

```text
PASS: all 11164 checks passed
```

and the original moment/defect audit reported

```text
PASS: all 1512 algebraic checks passed
```

### 69.2 Operator actually tested

For each connected component \(P\) of the old/new triangle symmetric
difference, the audit constructs non-negative old and new patch masses

\[
  m_{i,P}^-,\qquad m_{i,P}^+,
\]

their difference

\[
  \Delta m_i=m_{i,P}^+-m_{i,P}^-,
\]

and the raw topology defect

\[
  \boldsymbol D_P
  =\sum_{i\in P}\Delta m_i\boldsymbol U_i^-.
\]

The high-order candidate is exactly section 68's proposal,

\[
  \boldsymbol Q_i^{H,+}
  =\boldsymbol Q_i^-
   +\Delta m_i\boldsymbol U_i^-
   -w_i\boldsymbol D_P,
  \qquad
  w_i=\frac{m_{i,P}^+}{\sum_jm_{j,P}^+}.
  \tag{69.1}
\]

The low-order endpoint is

\[
  \overline{\boldsymbol U}_P
   =\frac{\sum_jm_{j,P}^-\boldsymbol U_j^-}
          {\sum_jm_{j,P}^+},
\]

\[
  \boldsymbol Q_i^{L,+}
  =\boldsymbol Q_i^-
   +m_{i,P}^+\overline{\boldsymbol U}_P
   -m_{i,P}^-\boldsymbol U_i^-.
  \tag{69.2}
\]

Using the new patch mass in the denominator of
\(\overline{\boldsymbol U}_P\) makes (69.2) conservative even when the two
floating-point evaluations of the common patch area differ by roundoff. In
exact arithmetic it is the same convex old-patch average because

\[
  \sum_i m_{i,P}^-=\sum_i m_{i,P}^+.
\]

When (69.1) is inadmissible, the audit finds the largest patch-common
\(\alpha\) by bisection such that

\[
  \boldsymbol Q_i^+(\alpha)
   =\boldsymbol Q_i^{L,+}
    +\alpha\left(
       \boldsymbol Q_i^{H,+}-\boldsymbol Q_i^{L,+}
     \right)
\]

has positive density and internal energy at every patch vertex.

### 69.3 Isolated flip: exactness and scaling

A non-symmetric convex quadrilateral was triangulated with each of its two
diagonals. The test verified to roundoff:

- patch zeroth moment;
- patch first moment;
- constant-state preservation;
- patch conservation;
- linear-state preservation.

For the quadratic scalar field used by the audit, the maximum nodal change was

| \(h\) | \(\max_i|U_i^+-U_i^-|\) |
| ---: | ---: |
| 1 | \(1.572378\times10^{-2}\) |
| 1/2 | \(3.930945\times10^{-3}\) |
| 1/4 | \(9.827362\times10^{-4}\) |
| 1/8 | \(2.456840\times10^{-4}\) |

Every measured refinement order was `2.000000`. This directly verifies

\[
  U_i^+-U_i^-=O(h^2)
\]

for a smooth non-linear field while the conserved patch sum is exact.

### 69.4 Real topology patches, including cascades and periodic seams

The full sample used jittered \(24^2\) and \(48^2\) point sets under Yee and KH
motions, plus the tiled Swift \(48^2\) set under KH motion. Twelve steps were
run for each case at `CFL = 0.3`.

The combined repair sample contained

\[
  647\ \text{connected patches},
  \qquad
  123\ \text{cascade patches},
  \qquad
  4\ \text{periodic-seam patches}.
\]

Every patch passed the constant and linear identities, including the four
periodic cases after patch-local unwrapping.

Using a smooth positive Euler state, the accumulated raw mass defect over this
mixed sample was

\[
  \sum\delta M_{\rm raw}
   =-1.3344191653175130\times10^{-4},
\]

whereas the accumulated repaired value was

\[
  \sum\delta M_{\rm repaired}
   =+2.7000623958883807\times10^{-13}.
\]

Across all four conserved components and all sampled steps,

\[
  \max
  \frac{|\delta\boldsymbol{\mathcal Q}_{\rm raw}|}
       {\max(1,\sum_i|\boldsymbol Q_i|)}
  =7.167376\times10^{-4},
\]

\[
  \max
  \frac{|\delta\boldsymbol{\mathcal Q}_{\rm repaired}|}
       {\max(1,\sum_i|\boldsymbol Q_i|)}
  =1.243451\times10^{-15}.
\]

The largest smooth-state nodal correction in this deliberately short mixed
sample was

\[
  \max_{i,k}|U_{i,k}^+-U_{i,k}^-|
  =3.105727\times10^{-3}.
\]

No high-order candidate lost admissibility for either the smooth Euler field or
the discontinuous KH-like density/velocity field:

```text
high-order bad nodes = smooth:0 KH:0
```

This is encouraging but is not a production positivity result; the states are
synthetic rather than states evolved by the RD solver.

### 69.5 The fallback was exercised, not merely checked symbolically

To force difficult transfers, 2400 random patch states were generated over 60
real patches. Density and pressure spanned several decades and velocities
spanned three decades. Every old state was admissible.

The high-order candidate produced 6552 inadmissible nodal instances. The
patch-common limiter activated in

\[
  1899/2400
\]

trials, with

\[
  \alpha_{\min}=0.3108191.
\]

The low-order endpoint produced zero inadmissible nodes, and every blended
state was both conservative to roundoff and admissible:

```text
high-order bad nodes = 6552
limited trials       = 1899
minimum alpha        = 3.108191e-01
low-order bad nodes  = 0
```

The large limited fraction is not a prediction for a fluid run: this ensemble
was intentionally extreme. It establishes that the fallback path is reachable
and that its two required invariants survive when it is used.

### 69.6 Bounded long-motion accumulation

An 80-step prescribed periodic mesh deformation generated 1557 topology
patches without allowing unbounded mesh degradation. For a smooth Euler field,
the raw accumulated conserved-component defects were

\[
 (-2.157909,\,-0.7450805,\,+0.4334343,\,-4.317037)
 \times10^{-2},
\]

while the repaired accumulation was

\[
 (+2.842171,\,-32.68497,\,0,\,-5.684342)
 \times10^{-14}.
\]

The latter is floating-point summation noise; every individual step also
passed the roundoff conservation check.

### 69.7 What this result establishes and what it does not

The offline result establishes:

1. equation (69.1) is conservative on isolated, cascading and
   periodic-boundary flip patches;
2. uniform and linear fields are preserved to roundoff;
3. the smooth nodal correction has the expected \(O(h^2)\) scaling;
4. the proposed low-order endpoint is admissible for the tested positive
   states;
5. a single patch-common convex limiter preserves conservation when the
   high-order candidate fails;
6. long accumulation of the topology defect is removed algebraically rather
   than made statistically smaller.

It does **not** yet establish:

1. that the online lifecycle forms exactly the same old/new patch masses;
2. that the observed production scalar-B/N drift is entirely removed;
3. that a real RD state never needs stronger scalar/species constraints;
4. that old triangle records survive mesh free/domain decomposition correctly;
5. that MPI patch ownership is unique;
6. that physical, stage-0 and predictor ledgers are transferred coherently
   under hierarchical timesteps;
7. that the repair leaves the established Gresho, Sod, Yee and KH solution
   metrics unchanged.

### 69.8 Go/no-go decision and next implementation slice

The proposal passes the offline go/no-go gate.

The next slice should remain deliberately smaller than the full section-68
design:

1. one rank and equal timesteps only;
2. accumulate the pulled-back new-connectivity nodal mass inside
   `rd_ale_prepare_step`;
3. construct connected affected support from \(\Delta m_i\) for the first
   diagnostic implementation;
4. apply the high-order operator (69.1) before the continuous ALE mass rebase;
5. abort and report the patch if the candidate is inadmissible, rather than
   immediately integrating the full fallback;
6. verify isolated flip, uniform flow and short KH;
7. only then run the existing long KH conservation audit.

If this removes the endpoint drift to roundoff without moving the accepted
fluid metrics, add exact old/new triangle-key patch reconstruction and the
tested fallback. MPI and hierarchical stage transfer remain subsequent,
separate gates.

---

## 70. One-rank equal-step online topology repair: uniform flow and matched short KH (2026-08-24)

### 70.1 Scope and implemented operator

Section 69 authorised only the smallest online slice. It is compiled by
`RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC`, is guarded by `RD_ALE_EQUALSTEP`, and
the existing equal-step path still aborts for `NTask != 1`. This is not yet
an MPI or hierarchical-timestep implementation.

After the new-connectivity triangles have been pulled back to time level
\(n\), define

\[
  m_i^- = |S_i^n|,\qquad
  \widehat m_i = \sum_{T^{n+1}\ni i}\frac{|T^n_{\rm pullback}|}{3},
  \qquad \Delta m_i=\widehat m_i-m_i^- .
\]

Nodes with numerically non-zero \(\Delta m_i\) are joined through the new
triangulation. Each connected component is a provisional topology patch
\(P\). The code checks the patch zeroth moment,

\[
  \left|\sum_{i\in P}\Delta m_i\right|
  \le 65536\,\epsilon_{\rm mach}
     \max\!\left(\overline m,\sum_{i\in P}|\Delta m_i|\right),
\]

and aborts if it fails. The repair is

\[
  \boldsymbol D_P=\sum_{i\in P}\Delta m_i\boldsymbol U_i^-,
  \qquad
  w_i=\frac{\widehat m_i}{\sum_{j\in P}\widehat m_j},
\]

\[
  \widehat{\boldsymbol Q}_i
    =m_i^-\boldsymbol U_i^-+\Delta m_i\boldsymbol U_i^-
       -w_i\boldsymbol D_P,
  \qquad
  \boldsymbol U_i^+=\frac{\widehat{\boldsymbol Q}_i}{\widehat m_i}.
\]

All non-anchor weights are evaluated first. The anchor receives the exact
floating-point remainder

\[
  w_{\rm anchor}=1-\sum_{i\ne {\rm anchor}}w_i,
\]

so the correction weights sum to exactly one. Patch and global conserved sums
are then audited to roundoff. Density and pressure are checked at every
corrected node. In this first online slice an inadmissible candidate aborts
with `RD-TOPO-BAD`; the section-69 low-order endpoint and patch-common limiter
are not yet connected to the fluid lifecycle.

The implementation is local to
`src/hydro/residual_distribution_solver.c`, with the flag registered in
`Template-Config.sh` and `defines_extra`. No production Config was changed.

### 70.2 Reproducible builds and isolated runs

Repair build:

```text
config   examples/gresho_2d/Config_FS_con_cm_N_toporepair.sh
artifact build_artifacts/toporepair-n-debug/000cdaaee46f-f959f4d1978f8243/Arepo
sha256   026ce4206c2199a35a852b3c020a2d6c6ea6a25a23437ff5432ca0c5b2eed277
```

Matched no-repair control:

```text
config   examples/gresho_2d/Config_FS_con_cm_N_topobaseline.sh
artifact build_artifacts/topobaseline-n-debug/000cdaaee46f-77b22b004eceb4c1/Arepo
sha256   c19099f5bc55ccd84c1426239e6609445a8efa10e75dd21972cb72f5b87cce65
```

The builds have the same source state and options except for the repair flag.
All runs used one rank, forced equal timesteps, N distribution, contour
residual, the element co-moving frame and the Arpaia modified-midpoint mass
pair. Outputs are isolated under

```text
/home/zwu/Hydro_data_analysis/Data_MMRD_debug/TopologyRepair_20260824/
```

### 70.3 Uniform-flow gate

The random-48 uniform IC was evolved to \(t=0.02\). This was a real topology
test, not a no-flip pass:

```text
ALE/repair steps                  73
affected-node instances        2724   (maximum 86 in one step)
provisional patch instances     639   (maximum 20 in one step)
maximum patch zeroth residual   6.924e-15
maximum repair |Delta U|         6.217e-15
maximum finished-state |Delta U|8.882e-16
maximum endpoint defect         7.994e-15
```

The state remained uniform to roundoff. There were no inverted pulled-back
triangles, non-positive states or failed conservation assertions. The
free-stream and online-lifecycle gate passes.

### 70.4 Matched short-KH gate

The smoothed glass-48 KH IC was evolved to \(t=0.2\). The repair run contained
432 repair calls, 3761 affected-node instances and 886 provisional patches.
The new mesh changed connectivity on 369 of 433 geometry observations, with
965 replaced edges in total.

Summing the counterfactual uncorrected topology defect along the repair
trajectory gave

\[
 \sum_n\boldsymbol D_{\rm raw}=
 (2.2376833,\;5.4298655,\;0.27259883,\;5.6172490)\times10^{-4},
\]

whereas the topology-stage audit after repair gave

\[
 \sum_n\Delta\boldsymbol{\mathcal Q}_{\rm repaired}=
 (-2.6645,\;0.83267,\;0.085869,\;10.658)\times10^{-14}.
\]

The stronger end-to-end comparison comes from initial and final HDF5
snapshots. In conserved-component order \((M,P_x,P_y,E)\), the matched
no-repair run drifted by

\[
 \Delta\boldsymbol{\mathcal Q}_{\rm control}=
 (2.0269585\times10^{-4},\;
  4.6343221\times10^{-4},\;
  2.9981906\times10^{-5},\;
  5.4657728\times10^{-4}),
\]

whereas the repair run drifted by

\[
 \Delta\boldsymbol{\mathcal Q}_{\rm repair}=
 (-4.1741273\times10^{-8},\;
  -1.0634096\times10^{-7},\;
  -7.1723652\times10^{-9},\;
  -1.1273872\times10^{-7}).
\]

The absolute improvement factors are:

```text
mass 4856.0   x-momentum 4358.0   y-momentum 4180.2   energy 4848.2
```

The largest single-step endpoint defects fell from

\[
 (4.3503,\;5.0735,\;1.4808,\;1.7707)\times10^{-5}
\]

to

\[
 (1.2376,\;1.2849,\;0.36861,\;0.97904)\times10^{-8}.
\]

Thus the worrying \(10^{-3}\)-scale long accumulation is already visible in
the control's \(t=0.2\) trend, and the repair removes its dominant
topology-driven part by roughly four orders of magnitude.

The maximum nodal conserved-state change made by one repair was

\[
  \max_{i,k}|U_{i,k}^+-U_{i,k}^-|=1.940\times10^{-2}
\]

at \(t=0.18046875\). Relative to the approximately 6.4 energy-density scale
of this KH problem this is 0.3 per cent. It did not trigger the positivity
abort: the minimum RK2 predictor density and pressure were 0.9799744 and
2.357655, and the final snapshot minima were 0.9841669 and 2.3707735.

The repair run took 41.34 s versus 39.84 s for the matched control, an
indicative 3.8 per cent overhead. This is one noisy debug pair with extensive
geometry output, not a production performance measurement.

### 70.5 Decision and remaining gates

The first online gate passes:

1. real topology changes are detected in the fluid lifecycle;
2. uniform flow remains exact to roundoff;
3. a real non-uniform RD state remains admissible;
4. the matched control reproduces the accumulated drift;
5. end-to-end mass, momentum and energy drift fall by
   \(4.2\)--\(4.9\times10^3\), not merely in an internal patch audit;
6. the measured one-rank debug cost is small enough to justify the next gate.

This does not authorise a production or thesis-default switch. The next gates
are:

1. run the existing longer KH conservation audit and compare accepted fluid
   metrics, not only global ledgers;
2. replace provisional \(\Delta m\) support components with exact old/new
   triangle-key flip patches and verify that the two constructions agree
   online;
3. connect and deliberately exercise the section-69 admissible fallback;
4. define one-owner patch assembly and ghost exchange for MPI;
5. define which physical, stage-0 and predictor ledgers are repaired when a
   flip occurs inside a hierarchical interval, then test equal-step reduction
   before enabling local timesteps.

The compile guard deliberately prevents item 5 from being bypassed: the
current repair cannot be enabled without `RD_ALE_EQUALSTEP`.
---

## 71. KH to \(t=10\): conservation/robustness pass, solution-invariance fail (2026-08-24)

### 71.1 Runs and control equivalence

The section-70 repair binary was run unchanged:

    parameter examples/gresho_2d/param_KH_N_glass48_toporepair_t10.txt
    output    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/TopologyRepair_20260824/kh_n_t10/output
    binary    build_artifacts/toporepair-n-debug/000cdaaee46f-f959f4d1978f8243/Arepo
    sha256    026ce4206c2199a35a852b3c020a2d6c6ea6a25a23437ff5432ca0c5b2eed277

It completed normally at exactly \(t=10\), with no RD-TOPO-BAD,
termination, negative predictor state, inverted pulled-back element or
non-positive midpoint mass. The instrumented run took 3430.36 s; it shared
the node with a duplicate control during its early part, so this wall time is
not a repair-overhead measurement.

A current-source no-repair control was initially run in parallel. At the common
snapshot time \(t=0.2001953125\), it was compared by particle ID with the
already complete section-59 release-N \(t=10\) control. The maximum difference
was exactly zero for every common output field:

    Coordinates, CenterOfMass, Velocities, VertexVelocity,
    Masses, Density, Pressure, InternalEnergy, Volume,
    ParticleIDs and TimebinHydro.

The duplicate control was therefore stopped after \(t\simeq1.67\), preserving
its partial output, and the bitwise-equivalent complete section-59 run was used
for the long comparison:

    /home/zwu/Hydro_data_analysis/Data_MMRD_debug/N_Glass48_ContourCM_20260820/kh_n_release_t10

Both complete series contain 51 snapshots. Corresponding output times differ
by at most one timebase increment, \(3.0517578125\times10^{-4}\).

### 71.2 Online topology and health audit

The repair lifecycle executed:

    repair calls                    31502
    affected-node instances        315005   (maximum 46 per step)
    provisional patch instances     77496   (maximum 11 per step)
    geometry observations           31502
    observations with flips          28600
    replaced edges                   79033   (maximum 12 per step)
    maximum patch zeroth residual   2.278e-14
    maximum nodal |Delta U|          1.065e-01

The signed accumulated counterfactual topology defect was

\[
 \sum_n\boldsymbol D_{\rm raw}
 = (4.09625\times10^{-3},\;
    1.37666\times10^{-3},\;
   -2.29166\times10^{-3},\;
   -1.40980\times10^{-2}),
\]

while the same sum after repair was

\[
 (2.62\times10^{-14},\;-6.55\times10^{-15},
  -4.30\times10^{-15},\;5.51\times10^{-14}).
\]

The raw absolute, rather than signed, accumulated mass defect was 1.09924.
Large cancellation therefore hides the total transfer activity; the repair
audit remained at floating-point summation error through all 31502 calls.

The maximum local correction rose from \(1.94\times10^{-2}\) in the
\(t=0.2\) test to \(1.065\times10^{-1}\), but reached that value before
\(t=3\) and did not continue growing. The minimum RK2 predictor density and
pressure were

\[
 \rho_{\min}=0.7351733,\qquad p_{\min}=2.202427.
\]

The mesh also remained healthy:

    minimum triangle area / mean area   0.1416
    minimum angle                       0.2882 rad
    inverted elements                   0
    non-positive Sbar                   0
    final area / mean area              0.2295
    final minimum angle                 0.3549 rad
    final pullback error                1.221e-17

Thus the long robustness and online admissibility gates pass.

### 71.3 End-to-end conservation

From the initial and final HDF5 snapshots, the no-repair control changed
\((M,P_x,P_y,E)\) by

\[
 (3.7842509\times10^{-3},\;
  1.9809978\times10^{-3},\;
  1.8052846\times10^{-4},\;
 -3.1368937\times10^{-3}).
\]

The repaired run changed the same totals by

\[
 (-1.0383736\times10^{-5},\;
  -8.2594560\times10^{-7},\;
  -1.5981326\times10^{-7},\;
  -7.1096403\times10^{-7}).
\]

The absolute improvement factors are:

    mass 364.4   x-momentum 2398.5   y-momentum 1129.6   energy 4412.2

The fractional mass drift fell from \(2.523\times10^{-3}\) to
\(6.923\times10^{-6}\), and the fractional energy drift from
\(4.884\times10^{-4}\) to \(1.107\times10^{-7}\).

The topology stage itself is conservative to roundoff. The remaining
\(1.04\times10^{-5}\) mass drift is the accumulated non-topology endpoint
defect; its largest single-step component was \(2.43\times10^{-7}\).
Consequently this prototype removes the dominant topology-driven drift but
does not make the complete ALE-RD update globally roundoff conservative.

### 71.4 KH solution metrics move materially

The established section-59 diagnostics were recomputed with identical
definitions. Here \(E_{k,y}=\frac12\sum_i m_i v_{y,i}^2\),
\(\sigma_\rho\) is the unweighted nodal density standard deviation, and the
entropy excursion is the maximum distance of \(s=p/\rho^\gamma\) outside its
initial range, divided by that range.

| \(t\) | \(E_{k,y}\) control | \(E_{k,y}\) repair | \(\sigma_\rho\) control | \(\sigma_\rho\) repair | entropy control | entropy repair |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 0.003353 | 0.004156 | 0.40657 | 0.42348 | 0.183 | 0.655 |
| 4 | 0.005970 | 0.007249 | 0.34180 | 0.35120 | 0.0649 | 0.240 |
| 6 | 0.044236 | 0.033868 | 0.30439 | 0.31247 | 0.0238 | 0.128 |
| 8 | 0.067100 | 0.052622 | 0.22700 | 0.24344 | 0.0141 | 0.0855 |
| 10 | 0.032033 | 0.044804 | 0.18124 | 0.18965 | 0 | 0.0383 |

The control peak is

\[
 E_{k,y}^{\max}=0.0679545\quad\hbox{at}\quad t=7.80029,
\]

whereas the repaired run peaks at

\[
 E_{k,y}^{\max}=0.0539425\quad\hbox{at}\quad t=8.60016.
\]

The peak is 20.6 per cent lower and delayed by 0.8 time units. At \(t=10\),
the two solutions are on different parts of the nonlinear oscillation and
\(E_{k,y}\) differs by 39.9 per cent. The final density standard deviation is
4.64 per cent larger with repair.

Both final states are physically healthy:

| case | density range | pressure range | minimum cell mass |
| --- | --- | --- | ---: |
| control | 1.09597--1.95863 | 2.37114--2.70053 | \(1.613\times10^{-4}\) |
| repair | 1.04517--2.17184 | 2.35381--2.70217 | \(1.922\times10^{-4}\) |

Nevertheless, the section-69 requirement that accepted fluid metrics should
not move materially is not met.

### 71.5 Interpretation and decision

The long test has a split verdict:

1. **robustness: pass** -- it reaches \(t=10\) with substantial positivity and
   mesh-quality margins;
2. **topology conservation: pass** -- the patch operator remains conservative
   to roundoff over 31502 calls;
3. **end-to-end conservation: strong pass for the intended defect** -- global
   drift improves by \(3.6\times10^2\) to \(4.4\times10^3\);
4. **solution invariance: fail** -- KH growth, phase and entropy excursion move
   materially.

The leading implementation-level explanation is the provisional patch
detector, but this is an inference rather than a demonstrated cause. A
connected non-zero-\(\Delta m\) support component never splits an exact flip
patch in the section-69 audit, but it can merge adjacent independent flips.
Conservation survives such merging; locality does not. Distributing one
combined defect over an over-connected component can create a larger and more
diffusive state transfer. The growth of the maximum correction from 0.0194 to
0.1065 and the increased entropy excursion are consistent with that mechanism.

Therefore the current \(\Delta m\)-support implementation remains a diagnostic
prototype and must not become a thesis or production default. The next action
is not another long run. It is to implement exact old/new triangle-key patch
reconstruction alongside the provisional detector, log the merge relation and
patch diameters, and compare both correction candidates online without first
applying the exact candidate. Only if exact patches reduce the local correction
and restore the accepted KH metrics should the admissible fallback, MPI
ownership and hierarchical-timestep ledger transfer proceed.

---

## 72. Plan for review: exact triangle-key topology patches before further long runs (2026-08-25)

### 72.1 Motivation and status

Section 71 gives a split result. The provisional online repair is robust and
removes the dominant global conservation drift, but it materially changes the
long-time KH trajectory. The leading implementation hypothesis is that the
current non-zero-\(\Delta m\) support detector merges nearby independent
topology events. This is consistent with the larger nodal correction and
entropy excursion, but it is not yet a demonstrated cause.

This section is a review plan, not an implementation record. No solver change
is authorised by it. Its purpose is to give Claude an explicit object to audit
before the next coding slice.

### 72.2 What the exact reconstruction must identify

Let \(\mathcal T^-\) and \(\mathcal T^+\) denote the actual old and final new
Delaunay triangle sets at the two sides of one mesh rebuild. Each physical
triangle is represented by a canonical key \(K_T\). Define

\[
 \mathcal R=\mathcal T^-\setminus\mathcal T^+,\qquad
 \mathcal A=\mathcal T^+\setminus\mathcal T^-,
\]

where \(\mathcal R\) contains removed triangles and \(\mathcal A\) contains
inserted triangles. The exact changed region is the symmetric difference

\[
 \mathcal C=\mathcal T^-\triangle\mathcal T^+
            =\mathcal R\cup\mathcal A.
\]

An unchanged key is continuous ALE geometry and must not enter the topology
repair. Connected components of the changed-triangle incidence graph define
the exact net topology patches. An isolated two-dimensional \(2\to2\) flip
must produce the two removed and two inserted triangles on its four physical
vertices. A cascade may produce a larger component.

This identifies the net old/new connectivity change exactly. It is not
required to reconstruct a unique chronological flip sequence inside the
Delaunay build. Such a sequence can be non-unique, and transient internal
flips that leave no net connectivity change do not enter the endpoint
transfer.

### 72.3 Canonical triangle key

For the present one-rank, non-refining two-dimensional slice, the non-periodic
part begins with the sorted global particle IDs,

\[
 K_T^{\rm ID}=\operatorname{sort}(ID_a,ID_b,ID_c).
\]

IDs, not local point indices, are mandatory because local indices can change
under particle rearrangement or future domain decomposition. Orientation is
not part of identity.

Sorted IDs alone are insufficient at a periodic seam. A proposed periodic key
is:

1. choose a deterministic anchor vertex, initially the smallest global ID;
2. express the other two vertices' integer periodic-image offsets relative to
   the anchor;
3. translate all three offsets by a common integer vector so that the anchor
   offset is zero;
4. sort the two non-anchor \((ID,\Delta{\boldsymbol n}_{\rm image})\) pairs
   lexicographically;
5. include dimension and any particle-generation/refinement tag needed to
   exclude an ID-reuse collision.

Claude is asked to audit whether anchor-by-smallest-ID is sufficient for every
periodic triangle represented by AREPO ghosts, or whether a minimum over all
three translated/rotated representations is required.

MPI is deliberately not part of the first slice. The eventual key must admit
ghost deduplication and a unique owner, for example the task owning the
lexicographically smallest canonical vertex/key. Refinement and derefinement
must later be classified separately from ordinary Delaunay flips.

### 72.4 Exact patch graph and the locality distinction

The changed-triangle graph must be defined from \(\mathcal C\), not from all
new triangles. Two changed triangles are adjacent only under the selected
physical incidence rule. The review must decide whether shared edge is
sufficient or whether shared physical vertex is required to obtain patches
that individually satisfy the zeroth and first moment identities.

This choice matters. For two truly independent exact patches \(A\) and \(B\),

\[
 \boldsymbol D_A=\sum_{i\in A}\Delta m_i^A\boldsymbol U_i,\qquad
 \boldsymbol D_B=\sum_{i\in B}\Delta m_i^B\boldsymbol U_i,
\]

the intended operator conserves \(A\) and \(B\) separately. If the provisional
detector merges them into \(P=A\cup B\), it instead distributes

\[
 \boldsymbol D_P=\boldsymbol D_A+\boldsymbol D_B
\]

with weights normalised over all of \(P\). Only \(P\) is then guaranteed to
conserve. In general,

\[
 \Delta\boldsymbol{\mathcal Q}_A
 =\boldsymbol D_A-W_A(\boldsymbol D_A+\boldsymbol D_B)\ne0,
 \qquad W_A=\sum_{i\in A}w_i^P.
\]

This is the precise sense in which global/merged-patch conservation can survive
while topology-event locality is lost. Calling the resulting change
"dissipative" is only a numerical hypothesis; the exchange can have either
sign.

### 72.5 First implementation slice: non-invasive dual diagnostics

The first implementation must not apply the exact candidate to the fluid
state. It should preserve the section-71 trajectory and calculate two patch
descriptions side by side:

1. current non-zero-\(\Delta m\) support components;
2. exact old/new triangle-key components.

The required lifecycle is:

1. immediately before the old tessellation/connectivity is discarded, capture
   canonical old triangle records and the old geometric contributions needed
   for nodal mass;
2. after the new tessellation exists, construct the corresponding canonical
   new records and pulled-back old-time geometry;
3. hash-match equal keys and form \(\mathcal R\), \(\mathcal A\), and exact
   components;
4. compute \(\Delta m_i^P\), \(\boldsymbol D_P\), weights and the exact
   candidate correction without writing it to particle storage;
5. retain the existing support repair as the only applied operator during this
   diagnostic comparison.

For every rebuild, log compact aggregate data:

- old/new/unchanged/removed/inserted triangle counts;
- exact and support patch counts;
- for each support component, how many exact components it contains;
- exact/support node counts and physical diameters;
- whether any exact component is split across support components;
- zeroth and first moment residuals for each exact component;
- \(\|\boldsymbol D_P\|\), maximum candidate
  \(|\Delta\boldsymbol U|\), and the ID/component producing the maximum;
- candidate density and pressure minima;
- whether the section-71 maximum 0.1065 belongs to a one-to-many merge.

Detailed per-patch output should be emitted only for the largest corrections,
periodic seams, failed identities or an explicit debug flag. Full per-step
patch dumps would reproduce the section-71 I/O problem.

### 72.6 Correctness gates before any exact repair is applied

The dual diagnostic passes only if all of the following hold:

1. every physical old/new triangle has one canonical key after local
   deduplication;
2. unchanged keys cancel exactly and do not enter a topology patch;
3. reconstructed counts agree with the independent replaced-edge/connectivity
   diagnostics;
4. each exact patch satisfies
   \(\sum_i\Delta m_i^P=0\) to roundoff;
5. its periodic-unwrapped first moment satisfies
   \(\sum_i\Delta m_i^P\boldsymbol x_i=0\) to roundoff;
6. no exact patch is split between two support components;
7. isolated flips, cascades and periodic seams reproduce the accepted
   section-69 offline patches;
8. a no-flip continuously moving mesh produces an empty exact changed set;
9. repeated domain/local-index rearrangement does not change the key set in
   the future MPI preparation test.

Failure of item 6 would invalidate the previous assumption that the support
detector is conservative over complete exact events. Failure of items 4 or 5
would mean the triangle component rule or periodic canonicalisation is wrong.

### 72.7 Hypothesis and solution-quality discriminator

The merge hypothesis is supported only if the diagnostic shows that:

1. the large support components are one-to-many unions of exact components;
2. exact-patch candidate corrections are materially smaller or more local than
   the support candidate;
3. the 0.1065 maximum and the large entropy-excursion regions correlate with
   those unions.

If exact patches are almost always identical to support patches, or if their
candidate correction remains near 0.1065, the detector is not the explanation.
The next audit would then move to the transfer weights/operator itself rather
than applying exact patches and repeating a long run.

Only after the hypothesis passes should a second build apply the exact
candidate. Its test order is:

1. isolated real flip and periodic-seam replay;
2. uniform moving flow;
3. matched KH to \(t=0.2\);
4. matched KH to \(t=2\), including entropy and \(E_{k,y}\);
5. \(t=10\) only if the short fluid metrics return close to the accepted
   no-repair N trajectory.

The section-69 admissible fallback is connected only after the exact high-order
patch path passes these gates.

### 72.8 Cost model and acceptance budget

For glass48,

\[
 N_{\rm gas}=2305,\qquad N_{\rm tri}\simeq4610.
\]

Three implementation levels are distinguished.

**Full sorting.** Saving and sorting both triangle-key sets costs

\[
 O(N_{\rm tri}\log N_{\rm tri})
\]

per rebuild. It is useful only as a simple reference and is not the desired
production path.

**Full hash comparison.** Hash insertion/lookup of all old/new keys is expected
\(O(N_{\rm tri})\). At 48 squared resolution this is roughly 9000 key
operations per rebuild. A 48--64 byte triangle record gives about
0.4--0.6 MB for two dense key arrays; including hash slack and geometry should
remain of order 1--2 MB.

**Incremental change list.** Recording triangles at the existing Delaunay
create/delete points costs \(O(N_{\rm changed})\). Section 71 observed 79033
replaced edges in 31502 rebuilds, only 2.51 per rebuild on average. This is the
preferred eventual path, but it is more invasive and should follow, not
precede, validation of the key semantics.

The first diagnostic uses full hashing, preferably piggybacking on triangle
loops that already exist. Cost is measured with per-patch text output disabled
and a matched release build:

- below 5 per cent total overhead: accept full hashing for the next slice;
- 5--10 per cent: optimise traversal/hash storage before a long run;
- above 10 per cent: stop and move to an incremental create/delete list.

These are engineering gates, not measured predictions. The section-70 3.8 per
cent short-debug repair overhead and section-71 shared-node wall time must not
be used as the exact-key cost measurement.

For hierarchical timesteps a naive full global key scan at every fine substep
would be unacceptable even if the equal-step cost passes. The eventual design
must maintain persistent keys or restrict comparison to the locally rebuilt
active/ghost region. Exact keys nevertheless help the MPI/hierarchical design
because they provide stable event identity and an ownership object.

### 72.9 Questions explicitly sent to Claude

Claude is asked to review the following before implementation:

1. Does old/new triangle-set symmetric difference contain exactly the
   information needed for endpoint topology transfer, without chronological
   flip reconstruction?
2. Is the proposed periodic key canonical for AREPO's image/ghost
   representation, or must all anchor/orientation representations be minimised?
3. Should changed-triangle components use shared vertices, shared edges, or a
   bipartite old/new incidence construction to guarantee patch moment
   identities?
4. At which precise lifecycle points can old records be captured and new
   pulled-back records formed without crossing mesh free, particle reorder or
   domain decomposition?
5. Is separate zeroth and first moment conservation on every reconstructed
   component the correct completeness criterion?
6. Can two exact net topology events legitimately share a vertex while
   remaining separately conservative, making component decomposition
   non-unique?
7. Is the non-invasive candidate comparison sufficient to test the merge
   hypothesis before changing the fluid trajectory?
8. Are the 5/10 per cent cost gates reasonable given the subsequent MPI and
   hierarchical-timestep requirements?
9. Does exact event identity suggest a better future MPI owner than the
   lexicographically smallest canonical key/vertex?
10. Is any additional conserved ledger beyond physical
    \(\boldsymbol Q\), stage-0 and predictor state required to be represented
    already in the key-record interface?

Until this review is resolved, no exact-key implementation, MPI extension or
hierarchical transfer change is approved.

---

## 73. 2026-08-25: review of sections 68-72 — mathematics verified, a second hypothesis added, the plan approved with amendments

- **Author:** Claude Code (Fable 5), answering sections 68.9 and 72.9.
- **Scope:** independent verification of the section-68 operator, a source
  reading of the section-70 implementation
  (`rd_ale_apply_topology_repair`, `residual_distribution_solver.c`), a
  reinterpretation of the section-71 split verdict, and answers to all
  nineteen review questions. No code change.
- **Verdict:** the operator mathematics is correct and the offline audit is
  exemplary. The section-72 plan is approved with amendments. The single
  most important amendment: the section-71 "solution-invariance fail" admits
  **two** hypotheses, not one, and the dual diagnostic must be designed so
  that it can distinguish them — otherwise a null merge result will be
  misread as an operator defect.

### 73.1 The section-68 mathematics, verified independently

The moment identities (68.1) are exact geometric facts of P1 lumping: for
either triangulation of the patch region, `sum_i m_{i,P} = |patch|` and
`sum_i m_{i,P} x_i = integral of x over the patch`, because each triangle
contributes `|T|/3` at its three vertices and `(|T|/3)(x_a+x_b+x_c) =
|T| x_centroid = integral over T of x`. Both sides tile the same region, so
the differences vanish. Conservation, uniform exactness and linear exactness
of (68.5) follow as stated; the least-change interpretation (68.9) is
correct; the fallback (68.11) is conservative and admissible by convexity
since every `m_{i,P}^{+-}` is a sum of positive triangle thirds
(section 68.9 question 5: signed lumped patch contributions cannot arise in
2-D P1 lumping).

One reformulation makes the rest of this review transparent. In nodal form
the high-order transfer is exactly

    U_i^+ = U_i^- - w_i D_P / mhat_i,

so the entire solution perturbation of one event is the defect `D_P` spread
by the weights. Linear exactness means `D_P = sum_i dm_i (U_i - L(x_i))` for
any linear `L`, so on a patch of diameter `h_P`:

- smooth region: `D_P = O(sum|dm| h_P^2 |grad^2 U|)`, the verified `O(h^2)`;
- an interface of width comparable to `h` (this KH: tanh width 0.025 against
  `h ~ 0.021`): no linear fit removes the variation, so
  `D_P = O(sum|dm| [U])`, and with per-flip `|dm_i|/m_i` of order the
  inverse vertex valence — a 2-to-2 flip moves `|T|/3`-sized thirds — nodal
  corrections of order `0.1 [U]` are **intrinsic to any conservative local
  transfer at an under-resolved interface**, exact patches or not.

That last line is the second hypothesis for section 71.4.

### 73.2 Answers to section 68.9

1. Yes; non-negative by construction under `|T|/3` lumping, for every 2-D
   cluster.
2. The `dm` evaluation needs no old triangle list (section 70's
   `DualArea` against pulled-back new-connectivity mass is sufficient), but
   the **exact patch identification does**: an explicit old-record snapshot
   (canonical key plus per-vertex-ID old-time area thirds) captured while
   the old tessellation still exists.
3. Yes, provided all patch coordinates are unwrapped to one anchor image;
   the four periodic-seam patches of section 69 confirm it.
4. New patch-mass weight is the right first choice; the weight only decides
   where the `O(h^2)` (or interface-scale) correction lands. Note the
   implemented slice does **not** use it — see 73.4.
5. Yes, guaranteed non-negative (see 73.1).
6. Sufficient for pure Euler. Passive scalars/species would need the same
   patch-common `alpha` restricted further by scalar min/max bounds; not
   needed in the current 2-D code.
7. That silent combination — `m^+ U^-` — *was* the pre-repair code, i.e. the
   defect itself; the section-70 placement before Arpaia preparation is the
   correct factorization (68.15).
8. Yes: one transfer per connected component of the *changed set* at the
   rebuild endpoint. Chronological per-flip correction is unnecessary and
   worse (transient intermediate triangulations never carry the state).
9. No implementation advantage; keep (68.16)-(68.19) as a documented
   alternative only.

### 73.3 Section 71 reinterpreted: two hypotheses, and what discriminates them

**Hypothesis A (Codex's, section 71.5): over-merged support components make
the transfer non-local.** Confirmed as a real mechanism by the source: the
union loop runs over **all** new physical triangles, so two affected
vertices are joined whenever they co-occur in *any* triangle, including
unchanged ones. Two independent flips separated by one unchanged triangle
merge; along a flip-dense shear layer the merge radius chains. The code
comment already concedes the related second deviation (73.4). Merging
preserves both moment identities (a support component is a union of exact
patches — a split would trip the per-component zeroth-moment abort, which
never fired in 31502 calls), so conservation survives while locality does
not, exactly as section 72.4 states.

**Hypothesis B (this review): the correction magnitude at the interface is
intrinsic.** By 73.1, even exact single-flip patches at a `[rho] ~ 1`
interface of width `~h` produce `D_P` of interface scale, and nodal kicks
of order `0.1` are then expected occasionally regardless of the detector.
If B dominates, exact patches will improve locality statistics but leave
`max |Delta U|` near 0.1065 and the KH trajectory shift largely in place —
and that outcome would **not** indict the operator or its weights. It would
mean a conservative representation transfer at an under-resolved interface
has an irreducible local price, and the acceptance criterion, not the
scheme, needs revision.

Section 72.7 already provides for the null result but routes it to "audit
the transfer weights/operator". The right arbiter is different: compute the
**exact overlap L2 projection (68.20) diagnostically on the recorded worst
patches** (offline, from the dual-diagnostic logs — no solver change). If
the projection's nodal changes are comparable to the patch operator's, the
price is intrinsic (hypothesis B) and no weight tuning will remove it; only
if the projection is materially smaller is the operator/weight family the
problem.

**The acceptance criterion itself must change before the next long run.**
"Repair must not move accepted fluid metrics" (section 69.7 item 7) is
well-posed for smooth problems, where corrections are `O(h^2)`; it is not
well-posed for a chaotic KH at `t = 10` on `n = 48`, where the no-repair
control is itself a non-conservative trajectory, not truth — its
`+2.5e-3` biased mass creation concentrated at the interface is a solution
defect too, merely a less visible one. Proposed replacement gates:

1. smooth regressions (moving Gresho, Sod, Yee) with the repair applied:
   metrics within about one per cent, corrections `O(h^2)` — these
   section-69.7 items have **not yet been run** and cost an afternoon;
2. matched KH to `t = 2`: entropy excursion within a factor about 2 of
   control, `E_{k,y}` within a few per cent;
3. long-time: do not require trajectory coincidence at `t = 10`; require
   instead that the repair-control divergence *shrinks with resolution*
   (one glass96 short pair), or that the repair tracks the overlap-projection
   reference at least as closely as it tracks the control.

### 73.4 Two recorded deviations of the implemented slice from section 68

1. **Weights.** The code uses full pulled-back nodal masses
   (`ale_pullback_area / patch_weight`), not the proposed new *patch*-mass
   fraction (68.4); the source comment calls it a diagnostic substitute.
   Conservation needs only `sum w = 1`, but full-mass weighting pushes
   corrections toward large-dual-area vertices and, combined with merging,
   further delocalises the transfer. The exact-key slice gets
   `m_{i,P}^+` for free and should log both weightings in the comparison.
2. **Detector graph.** Support components connect through unchanged
   triangles (73.3). The section-72.4 changed-set rule removes this.

Both deviations must be reconciled — or their effect measured — before any
conclusion about "the operator" is drawn from the dual diagnostic.

### 73.5 Answers to section 72.9

1. **Yes.** The endpoint symmetric difference carries exactly the
   information the transfer needs; net-zero transient flips never touch the
   state. Chronological reconstruction would add nothing and is non-unique.
2. **Canonical, with two provisos.** Smallest-ID anchor plus per-vertex
   integer periodic-image offsets *relative to the anchor* (translated so
   the anchor offset is zero), non-anchor pairs sorted lexicographically,
   is a true canonical form — relative offsets quotient out the image
   ambiguity, so no minimisation over representations is needed. Provisos:
   (a) assert the three IDs are distinct (a triangle containing the same
   particle through two periodic images is geometrically possible only in
   boxes a few cells wide — assert, do not handle); (b) recover offsets as
   exact integers from coordinate differences divided by the box size,
   never from floating-point geometry comparisons.
3. **Edge-sharing on the union of removed and inserted triangles** (old-old
   via old edges, new-new via new edges, old-new via shared edges — a 2-to-2
   flip is connected through its retained boundary edges). This equals
   interior-connectivity of the changed region, which is precisely the
   granularity at which both moment identities hold: each interior-connected
   component is tiled by its own `R` and `A` subsets. Vertex-sharing
   over-merges pinched ("bowtie") events that conserve separately.
4. Capture old records **while the previous step's tessellation is still
   live** — the natural point is where the old element set is already being
   traversed (end of the previous RD solve or immediately before mesh
   free), storing `(canonical key, per-ID area thirds)` keyed by particle
   ID. IDs, never indices: Peano reordering and any future domain
   decomposition sit between capture and use. Pulled-back new records form
   after the rebuild exactly as `ale_pullback_area` does now.
5. **Yes, as the primary criterion** — zeroth plus first moment per
   component, given that each component's old/new subsets tile the same
   region, is exactly what uniform and linear exactness require. Keep the
   independent count cross-check (gate 3): a mis-reconstruction could
   accidentally satisfy moments.
6. **Yes** — two events touching at one vertex conserve separately, and the
   decomposition is non-unique only there. Choose maximal locality (the
   edge rule keeps them separate); record the rule; either choice is
   mathematically valid.
7. **Yes for hypothesis A — but only with the 73.3 arbiter added** so that
   the null result discriminates A from B instead of defaulting to a weight
   audit. Add to the logged aggregates: the per-step *non-topology* endpoint
   defect against flip count. Section 71.3's residual `1.04e-5` drift has a
   largest single step of `2.43e-7`, far above the no-flip envelope
   (`5.8e-11`, section 68.1), so the residual is itself flip-correlated and
   currently unattributed — the same diagnostic run can localise it.
8. **Yes**, with the release-build, unshared-node measurement discipline
   section 72.8 already states. The incremental create/delete list is the
   only plausible hierarchical-phase path (2.51 replaced edges per rebuild
   makes `O(N_changed)` overwhelmingly cheaper), so treat full hashing as
   scaffolding.
9. Owner = task owning the anchor (smallest canonical ID) vertex is fine
   and deterministic. The real MPI constraint is that the *whole* patch
   must be resident on the owner: patches are small (section 71 maximum 11
   per step), so one ghost ring usually suffices, but a cascade can exceed
   it — the design needs a patch-diameter cap with an explicit abort, not
   silent truncation.
10. Equal-step: physical `Q` only — stage-0 and predictor states are
    constructed after the transfer point, so nothing else exists to
    transfer. Hierarchical: the same patch operator must be applied to
    every persistent per-vertex conserved array (inactive-bin endpoint
    states, the pending ledger of the hierarchical conservation design), so
    design the transfer as an operator over a *list* of conserved arrays
    now, rather than hard-coding `Q` — the key-record interface itself
    needs nothing extra.

### 73.6 Approval and amended order

Sections 68-70 are accepted as recorded; section 71's split verdict stands
with the reinterpretation of 73.3. The section-72 dual-diagnostic slice is
**approved with these amendments**:

1. run the smooth regressions (73.3 gate 1) with the existing applied
   support repair *now* — cheap, decisive for implementation errors, and
   independent of the exact-key work;
2. log both weightings (patch-mass and full-mass) in the exact-key
   comparison (73.4);
3. add the overlap-projection arbiter on the recorded worst patches before
   concluding anything from a null merge result (73.3);
4. add the per-step non-topology endpoint defect to the aggregates (73.5
   item 7);
5. adopt the 73.3 replacement acceptance gates before any further `t = 10`
   run is scored.

No exact-key application to the fluid state, no MPI extension and no
hierarchical transfer are authorised until the dual diagnostic reports,
consistent with section 72's own restriction.
