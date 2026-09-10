# Moving ALE-RD with hierarchical timesteps and MPI: audit and bounded prototype

Date: 2026-09-08. Author: Codex (GPT-6), at Zhenyu's request.
Source baseline: `75c3d6a`;
the authoritative full commit is in `provenance.json` in the campaign below.
Status: mathematical assessment and isolated engineering experiment, not a
production promotion. No thesis file or tracked solver C file was changed.

**Follow-up, 2026-09-09:** targeted flips that change the local triangle clock
expose a missing time-interval coverage identity that the bounded §6.4 window
did not exercise. The logged `basis` close is not a pure same-time topology
term in those cases. Read
[`RD_topology_hierarchy_conservation_20260909.md`](RD_topology_hierarchy_conservation_20260909.md)
before generalizing the conservation conclusions below. The fixed-topology
Arpaia result and the reported rank-equivalence measurements remain valid.

## 1. Decision supported by this investigation

**Moving mesh, hierarchical timesteps and MPI can coexist.** A bounded port of
the existing concentrated N hierarchy completed the same 64-vertex, two-bin
Euler problem on 1, 2 and 4 MPI ranks, with repeated domain decompositions.
This was demonstrated for both Campoli and the current Arpaia implementation,
including a short interval containing topology changes.

There is, however, a mathematical correction to the August 26 handoff:
**the current Arpaia open/close rebase is not exactly conservative in physical
endpoint storage, even on fixed connectivity.** Uniform-flow preservation
does not establish that property. An independent scalar experiment, the
unchanged Euler code, and instrumented MPI runs all expose the same channel.
The error is small and of truncation order, but it is not round-off and is
independent of the topology/basis correction.

Recommendation for review: use **Campoli endpoint storage as the reference
for a strictly conservative transport/MPI implementation**. Keep the current
Arpaia algorithm as a comparison, with its newly identified error explicitly
reported. An Arpaia-divisor predictor with a conservative endpoint commit is
a viable alternative to derive and test, but it is a different discrete
update, not an exact rewrite of the current Arpaia algorithm.

The current topology closure remains nonconservative for nonuniform states
in both forms. Also, the frozen-star hierarchy does not promise second-order
accuracy across bin interfaces. These two qualifications must survive into
any Chapter 4 formulation.

## 2. Sources and existing implementation boundaries

Read: root and repository `context.md`, `context_localMac.md`, recent local
log sections 8--9, COSMA log 4, moving log 2 handover and relevant mathematics,
form-selection, conservation/topology sections, and the August 26 update.
The local log 2 still ends at section 73; the update refers to unavailable
sections 74--83. Those sections were not recovered or represented as read.

The source is more restrictive than a general reading of “hierarchy works”:

| Existing path | Hierarchy | MPI before this experiment |
| --- | --- | --- |
| Static N and LDA/F1 | Implemented, validated in earlier logs | Implemented, validated |
| Moving N, Campoli | Concentrated event prototype | Explicit `NTask != 1` termination |
| Moving N, Arpaia | Concentrated event prototype with local rebase | Same termination |
| Moving LDA/F1 | Excluded by moving-hierarchy compile guard | Not implemented |
| Moving B | Hierarchical theta semantics deferred | Not implemented |

Relevant source anchors, at the baseline commit:

- `src/hydro/residual_distribution_solver.c:136`: moving hierarchy requires N,
  `CREATE_FULL_MESH`, periodic 2-D, total-residual RK and one selected mass pair.
- `:338`: complete star-bin reduction from uniquely owned simplices.
- `:1314`: minimum-ID primary simplex ownership, with periodic-image handling.
- `:2767`: geometry preparation, local-only accesses and one-rank guard.
- `:2890`: endpoint/geometric ledger closure.
- `:2918` and `:2981`: Arpaia open rebase and final endpoint conversion.
- `:5455`: moving N temporal-mass correction.
- `:5589`: divide the assembled predictor only after receiving remote increments.
- `src/main/run.c:352`: consecutive predictor/corrector calls on one rebuilt mesh.

The original consecutive moving calls do **not** refresh ghosts between the
assembled predictor and corrector. Removing the one-rank guard alone would
therefore consume stale remote predictors as well as incomplete geometry.

Primary references checked:

- Arpaia, Ricchiuto & Abgrall (2015), Proposition 4.1, equations (77),
  (80)--(84), inspected in the local PDF including rendered pages 520--521;
  DOI [10.1007/s10915-014-9910-5](https://doi.org/10.1007/s10915-014-9910-5).
- Campoli et al. (2017), section 2.2, equations (2)--(8),
  [author manuscript](https://www.math.u-bordeaux.fr/~mricchiu/sf-draft.pdf).
- Colombo & Re (2022),
  [author postprint](https://arxiv.org/abs/2204.11668), treats connectivity
  changes through fictitious continuous deformation. It is not an existing
  AREPO hierarchical/MPI implementation to port.

The defect derived below is a statement about this repository's exact
discrete update and endpoint conserved quantity. It does not require a broad
claim that all versions or interpretations of the published ALE method fail.

## 3. A mathematical contract that can be implemented under MPI

Use the RD conservative state `U=(rho,rho vx,rho vy,E)` and distinguish

\[
Q_i\quad\hbox{(extensive physical ledger)},\qquad
U_i^{\rm sync}\quad\hbox{(last synchronized intensive state)},\qquad
g_i\quad\hbox{(geometric ledger)}.
\]

An inactive coarse vertex may receive increments in `Q` and `g`, but its
primitive state is frozen. In general `Q_i/g_i` between complete closures is
not a state that the next fine residual is allowed to consume.

For a triangle due at an event ending at `t+`, let

\[
h_T=\min_{i\in T}h_i,\qquad
x_i^-=x_i^+-h_T\sigma_i,\qquad
x_i^{1/2}=x_i^+-\tfrac12h_T\sigma_i.
\]

Both stages use this same connectivity, interval, geometry and ownership.
Under nested dyadic bins with the existing velocity-update contract, the
vertex trajectories are linear over this interval. Changes of velocity,
bin epoch, migration or topology must not silently invalidate that contract.

Write `A-`, `Am`, `A+` for the three signed areas and
`Delta A=A+-A-`. The geometry deposits are

\[
\Delta g_{iT}=\frac{\Delta A_T}{3},\qquad
\Delta Q^{g}_{iT}=\frac{\Delta A_T}{3}U_i^{\rm sync}.
\]

All owned triangles, including those not due, contribute to the **endpoint**
star area `m_i+=sum_T A_T+/3`. At a synchronized vertex, the existing closure is

\[
c_i=m_i^+-g_i,\qquad Q_i\gets Q_i+c_iU_i^{\rm sync},\qquad g_i\gets m_i^+.
\]

On unchanged connectivity with valid clocks, geometric increments telescope,
so `c_i=0` to round-off. At a changed basis, this keeps a uniform state but
does not constitute a conservative transfer for a general `U`.

The complete star sets `hstar_i=min_{T contains i}h_T`. A vertex is stage-live
when `hstar_i=h_i` and its interval is due. Otherwise its stage increment is
zero, even if it synchronizes at the present event. For N,

\[
dU_i=-\frac{1}{D_i}\sum_{T\ni i,\,due}h_T\phi_{iT}(U^{\rm sync}),
\qquad U_i^*=U_i^{\rm sync}+dU_i
\]

on stage-live vertices. The sum must be complete across MPI ranks before
division by `D_i` and before the corrector uses it.

The two scalar pairs are

| Form | `M_T` (temporal area) | `D_T` (divisor area) |
| --- | --- | --- |
| Campoli | `(A-+A+)/2` | `A+` |
| Arpaia | `Am` | `Am+(A+-A-)/2` |

Both obey `D_T-M_T=Delta A_T/2`. Thus the integrated N fluid plus temporal
increment, excluding the geometric and basis deposits above, is

\[
L_{iT}=-\frac{h_T}{2}\{\phi_{iT}(U^{\rm sync})+\phi_{iT}(U^*)\}
       +\frac{\Delta A_T}{6}dU_i.\tag{1}
\]

The reference physical update is simply `Q_i += sum_T L_iT`. Campoli already
does this and has `D_i=m_i+` at live vertices. No global stage mass solve is
required; MPI communicates sums of extensive increments.

### 3.1 Why the frozen-interface Campoli update conserves

The implemented contour residual has the element total

\[
R_T(U)=\int_{\partial T}I_1F(U)\cdot n\,ds
       -\int_T\sigma_h\cdot\nabla U_h\,dx.
\]

For affine geometry and a P1 state, integration by parts and the element DGCL give

\[
R_T(U)=C_T(U)+\frac{\Delta A_T}{h_T}\bar U_T,\quad
C_T(U)=\int_{\partial T}[I_1F(U)-\sigma_h U_h]\cdot n\,ds,
\quad\bar U_T=\tfrac13\sum_iU_i.
\]

Summing (1) over its vertices, then adding the geometry deposit, cancels the
volume terms exactly. The remaining element balance is the trapezoidal
combination of the ALE boundary flux. Here the product `sigma_h U_h` is an
exact polynomial identity; replacing its edge integral by an inconsistent
quadrature would change the argument.

For equal-bin neighbours, shared edge contributions cancel. For a coarse/fine
shared edge, the frozen-star rule freezes both endpoint states and their RK
increments throughout the coarse interval. Their nodal physical fluxes and
mesh velocities are constant; the scaled edge normal is linear in time.
Composite fine midpoint quadrature therefore equals the coarse midpoint
quadrature. Cancellation holds over a complete common synchronization interval.

This proves the fixed-connectivity periodic conservation statement under the
stated assumptions. It does not say every fine event has a synchronized
physical global state, or that independently chosen coarse/fine dense-output
predictors could replace the frozen states without a flux register.

## 4. The Arpaia rebase introduces an additional physical increment

At a live vertex let `B_i` be the physical endpoint ledger after geometry and
basis closure, and let `L_i=sum_T L_iT` use the actually assembled Arpaia
predictor. The current implementation performs

\[
\bar Q_i^{open}=\frac{D_i}{m_i^+}B_i,\qquad
\bar Q_i^{close}=\bar Q_i^{open}+L_i,\qquad
Q_i^{new}=\frac{m_i^+}{D_i}\bar Q_i^{close}.
\]

Consequently

\[
\boxed{Q_i^{new}=B_i+L_i+e_i,\qquad
e_i=\left(\frac{m_i^+}{D_i}-1\right)L_i.}\tag{2}
\]

The extra term has no general zero-sum identity. It vanishes for uniform flow
because `L_i=0`, which explains why that gate passed. Nor does a global
`sum D_i=box area` imply `sum e_i=0`: the increments are spatially nonuniform.

For linearly moving vertices,

\[
\delta_T=\frac{A_T^-+A_T^+}{2}-A_T^{1/2}
=\frac{h_T^2}{8}(\sigma_1-\sigma_0)\times(\sigma_2-\sigma_0).
\]

At a live vertex, `m_i+-D_i=sum_T delta_T/3`. On a fixed spatial mesh with
smooth coefficients, `e_i=O(h_i^3)` per update. This permits second-order
closeness between two methods at a fixed physical endpoint while excluding
an assertion of identical discrete conservation. Even equal timesteps do
not remove the local weighted defect; the scalar experiment tests that case too.

A useful exact identity, for any nodal component on one fixed triangle, is

\[
A^+U^+-A^-U^-
=A^{1/2}(U^+-U^-)
 +\frac{A^+-A^-}{2}(U^++U^-)
 +\delta_T(U^+-U^-).
\]

Thus “equivalent through second order” must not be used as a synonym for
“the same exact endpoint integral.” This is the distinction missing from
the handoff's rebase argument.

The existing `stage=commit dQ` measures the **gross closing conversion**.
It is not (2). The diagnostic added in this experiment sums the opening and
closing conversion changes to obtain the **net rebase**. Comparisons of a
maximum closing change against a maximum basis change cannot establish its
absence or its total accumulated contribution.

### 4.1 Options for the mathematical form

1. **Campoli reference:** keep physical endpoint storage, `D_i=m_i+`, and (1).
   This is the narrowest path with an exact fixed-connectivity balance.
2. **Current Arpaia comparison:** retain it and measure (2). Do not claim
   round-off conservation, and do not label all drift as topology error.
3. **Conservative Arpaia-predictor candidate:** compute `dU_i` using the
   Arpaia divisor in a scratch stage array, but apply (1) directly to physical
   `Q`. This removes (2). It passed the independent scalar conservation gates
   here; it was not implemented or validated for Euler in this session.
   It differs from the current algorithm at truncation order, so equal-bin
   bitwise/round-off agreement with the current Arpaia reference is no longer
   an appropriate acceptance condition.

No default Config was changed. The recommendation is for review before the
Chapter 4 equations are fixed.

## 5. Isolated MPI implementation and its synchronization order

The prototype changes two C files in a copied `SRC_DIR`. It preserves the
existing mathematical updates, including the Arpaia defect, to separate
parallel equivalence from numerical-method changes.

The event sequence is:

1. Rebuild the full distributed mesh; exchange synchronized primitives,
   current bins and the mesh velocities that actually performed the drift.
2. Select exactly one owner per physical triangle. Use only owned simplices
   for geometry, residuals and the complete-star minimum.
3. Each owner sends `(endpoint area, due divisor contribution, due Delta g)`
   to each vertex's primary owner. Sum remote and local contributions before
   doing any nodal closure or rebase. Read remote velocities from `PrimExch`.
4. The primary applies its geometric deposit and closes synchronized vertices.
   Form the live Arpaia divisor only after the complete star has arrived.
5. Execute the predictor residual sweep; export extensive half-step ledger
   increments and full predictor increments through the existing flux list.
6. Complete imports; divide the full live predictor once on its primary.
   **Exchange primitives/stage metadata here.** This refreshes `RD_dU` and
   `RD_PredictorEnd` before the corrector sees remote vertices.
7. Execute the corrector on the same mesh and interval; complete all imports;
   apply any local final representation conversion; recover primitives only
   for synchronized vertices using the endpoint area.

An inactive primary still receives ledger increments. An MPI rank with no
local active primary must still participate in collective communication and
may own due triangles driven by remote vertices. Ownership is not an
activity filter. Domain migration cannot occur in the middle of this event.

The new geometry records use `(task, originalindex)` only while the mesh and
exchange map are stable. They are not persistent identifiers across domain
decompositions. `Q`, `g`, the synchronized state and velocity belong to the
particle/SphP records and migrate with them. Stable particle IDs, interval
endpoints and mesh epochs should key future persistent topology/flux history.

This spike uses `MPI_Alltoallv` of owned-element geometry records, not an
all-gather of every vertex or a replicated global triangulation. The existing
owner/star and flux-export machinery remains in use. Diagnostics reduce
global coverage, geometry, basis and rebase totals. It is intentionally not a
performance-optimized communication implementation.

Patch: `dev_log/patches/20260908_moving_hierarchy_mpi_spike.patch`.
The tracked solver remains guarded to one rank until this patch is reviewed
and the remaining acceptance gates are completed.

## 6. New numerical evidence

Campaign root:

`/Users/zhenyuwu/arepo_rd/local_runs/moving_hierarchy_audit_20260908`

The experiment is native arm64, Apple Clang 16, Homebrew Open MPI/OpenBLAS,
with `OPENBLAS_NUM_THREADS=1`. Each baseline Config and each prototype Config
has a separate build directory and executable. Initial conditions, parameters,
logs, generated headers, executable hashes and the exact patch are retained.
All physical totals below use stored `Masses`, momenta and total energies;
they do not use density times Voronoi `Volume`.

### 6.1 Independent scalar discriminator

`tests/rd/audit_ale_hierarchy_mass_rebase.py` uses a periodic 64-node jittered
triangulation, fixed connectivity, affine-in-time vertex trajectories and
the scalar N distribution. It tests uniform/nonuniform states, equal/mixed
bins, three macrostep lengths, and the three commit choices in section 4.1.

For nonuniform mixed bins and one macro interval:

| `H` | Campoli total mass change | Current Arpaia total mass change |
| --- | ---: | ---: |
| 0.02 | `1.11e-16` | `1.82273534e-8` |
| 0.01 | `2.22e-16` | `2.27796249e-9` |
| 0.005 | `0` | `2.84715584e-10` |

Equation (2) accounts for the defect to approximately `2e-16`. Equal-bin
nonuniform tests also have a nonzero Arpaia defect. Every uniform-flow test
passes. Both Campoli and the proposed Arpaia-predictor/endpoint-commit variant
conserve to round-off in all these scalar cases. This is not an Euler accuracy
or positivity result for the proposed variant.

### 6.2 Unmodified Euler code: four-event two-bin gate

The reproducible IC is a smooth, positive periodic Euler field on the same
64-node mesh, with `gamma=1.4`. Density, both velocity components and pressure
vary. Regularization shaping speed is zero. There are 32 vertices in each
bin, 48 stage-live vertices and 16 frozen vertices. The coarse step is
`H=0.004`, fine step `H/2`, final time `0.008`; three snapshots are retained.

The periodic Delaunay keys reconstructed at all four event positions are
unchanged. Geometric/basis closure is at round-off at every event.

| Unchanged solver form | Final total mass change | Final total energy change |
| --- | ---: | ---: |
| Campoli | `0` at printed precision | `0` at printed precision |
| Arpaia | `-2.05190087e-10` | `-1.06201581e-9` |

The snapshot reductions are performed after sorting by ParticleID; another
summation order can change round-off values. Halving the coarse step gives
single-macrostep Arpaia mass changes `-1.08343e-10`, `-1.39391e-11`, and
`-1.76703e-12` for `H=0.004,0.002,0.001`, consistent with the cubic local
error. These changing endpoints are a local-error discriminator, not a
fixed-final-time convergence measurement.

### 6.3 MPI: simultaneous moving mesh and hierarchy

The identical four-event problem passed on 1, 2 and 4 ranks for both forms.
At four ranks, maximum absolute differences from the **unmodified one-rank
solver**, after sorting by ParticleID, are:

| Field | Campoli | Arpaia |
| --- | ---: | ---: |
| Density | `1.33e-15` | `1.44e-15` |
| Velocity | `1.67e-16` | `3.05e-16` |
| Pressure | `1.11e-15` | `8.88e-16` |
| Internal energy | `2.66e-15` | `3.55e-15` |
| Timestep bins | identical | identical |

Campoli remains conservative to round-off. Arpaia has the same physical
defect on every rank count. Its four-rank net-rebase sum is approximately
`(-2.05190059e-10, 1.93336364e-10, -6.72949385e-11, -1.06201588e-9)`.
Subtracting both basis and net rebase from the measured physical change
leaves at most about `2e-16` in this run.

The logs report six domain-decomposition entries including setup, and
repeated decompositions between the four evolution events. This tests
decomposition/reordering in this small case; it is not an exhaustive proof
of arbitrary migration, load balance or restart behavior.

### 6.4 Bounded topology window

The same problem was extended to `t=0.064`, with `H=0.004` and 32 fine events,
on 1 and 4 ranks for both forms. Endpoint triangle-key symmetric difference
is 16. This is a key-set difference, **not** a count of 16 flips.

| One-rank form | Mass change | Energy change | Largest unexplained total after basis + net rebase |
| --- | ---: | ---: | ---: |
| Campoli | `-4.41399433e-4` | `+2.44580543e-4` | `3.3e-16` |
| Arpaia | `-4.41400184e-4` | `+2.44576206e-4` | `5.6e-17` |

At four ranks the unexplained residual remains below `1e-15`; maximum
particle-field differences from one rank are `5.33e-15` (Campoli) and
`6.67e-15` (Arpaia). All final density and pressure values are positive.

This supports the hierarchy's existing topology accounting in this window
and finds no additional rank-boundary or unaccounted transport channel.
It also demonstrates that the known topology term is physically nonzero.
It is not evidence that exact conservation across arbitrary topology events
has been solved.

The September 9 follow-up provides a counterexample outside this window:
when a flip changes a fine/coarse element's lifetime assignment, the
nonclosure balance need not vanish. Its uniform-flow control also shows why
`basis` cannot then be identified with the pure spatial topology jump.

## 7. What must be settled beyond the N/MPI prototype

### 7.1 Topology: conservative transfer is separate from keep-U closure

At a reconnection, a general state cannot keep every `U_i` fixed and also
preserve `sum_i m_i U_i` unless the basis-weighted change happens to cancel.
A local transfer must instead satisfy

\[
\sum_{i\in P}m_i^{new}U_i^{new}
=\sum_{i\in P}m_i^{old}U_i^{old},
\]

with constant-state preservation, an admissibility strategy, and an explicit
accuracy requirement. Log 2 sections 68--73 and the August 26 update already
show why such a correction can materially change an under-resolved KH
interface. That evidence is not undone by the MPI port.

For arbitrary hierarchical reconnections, the transfer's operands must refer
to a defined common patch time. Partially accumulated `Q` values must not be
treated as synchronized samples without closing their missing contributions.
The current keep-U geometry closure avoids storing old element intervals;
that does not by itself provide the temporal contract for an added
conservative remap.

A possible exact design is an interval/edge register plus a topology-patch
transaction: close the relevant old intervals, establish patch states at a
common time, perform one conservative transfer, then install the new epoch.
Another is a suitable space-time control-volume formulation. Both require
additional mathematics and engineering. Simply waking four flip vertices
does not automatically close all incident coarse stars, and ad hoc early
closure can propagate synchronization. These are requirements for future
work, not failures newly observed in the short topology window above.

### 7.2 LDA/F1 is possible algebraically but is not a macro switch

For temporal blocks `m_ij^T` satisfying
`sum_i m_ij^T=(M_T/3)I`, a direct extension of the physical corrector is

\[
L_{iT}^{F1}= -\frac{h_T}{2}(\phi_{iT}^n+\phi_{iT}^*)
 +\frac{D_T}{3}dU_i-\sum_jm_{ij}^T dU_j.\tag{3}
\]

Its summed temporal contribution is `Delta A_T sum_i dU_i/6`, the same as N.
For the existing mixed-stage F1 convention,
`m_ij^T=beta_i^* M_T/3`. A rank-deficient distribution retains a conservative
lumped fallback. All components and `dU` must transform consistently into
and out of the element frame. MPI requires the completed vector predictor,
not a global implicit mass solve.

Equation (3) is a proposed moving extension of the validated static F1
contract, not a new implemented result. The current static F1 branch uses
the same area for both terms; merely deleting the moving-N compile guard
would omit the required `D_T-M_T` contribution. Moving LDA/F1 needs explicit
code and equal-bin regression, stage positivity and rank-deficiency tests.

Most importantly, the static hierarchy already measured **first-order time
convergence** across the frozen interface for both N and LDA/F1: see
`RD_hierarchical_timestep_phaseb_prototype.md` sections 7.4 and 10.3 (LDA
orders approximately 0.994--0.997 in L1). Adding F1, Arpaia or MPI does not
remove that error. Achieving genuinely second-order multirate accuracy
requires compatible coarse dense output and time-integrated edge flux
matching/refluxing, or another conservative multirate construction.

B remains a separate extension requiring the frozen total-residual blend
to be defined across bins. It is not supplied by (3).

### 7.3 Geometry, CFL, restart and cost

- Complete-star RD signal bounds must be reduced to primaries before assigning
  bins. A candidate restriction is `h_i <= C m_i/sum_T alpha_T`; the existing
  `RD_ALE_CFL_TIMESTEP` is still an equal-step, one-rank path. The tests here
  use a small imposed cap and controlled 2:1 pattern, not a validated
  production hierarchical RD CFL estimator.
- The Arpaia live divisor must be positive. Signed area checks at old,
  midpoint and new configurations alone do not certify the entire interval:
  for quadratic area, also check any interior minimum. Deeper bins and
  changing geometry need a proactive pullback-validity bound.
- The full mesh is rebuilt and scanned at every fine event. MPI execution
  and fewer residual evaluations do not establish speedup. A later cost
  model should weight owned simplex frequency and solve cost; active-only
  moving mesh requires a separate completeness proof.
- Restart only at a defined physical endpoint until event state is explicitly
  serializable. Ensure the synchronized primitive timestamp, bin/velocity
  epoch and `RD_GeoLedger` survive. Do not checkpoint Arpaia temporary storage
  as though it were physical `Q`.
- In sensitive long runs, compare timebin schedules, connectivity and
  LU/pseudo-inverse branches before diagnosing rank divergence. The present
  small gates do not settle all round-off-sensitive branches.

## 8. Recommended closure sequence and Chapter 4 boundary

The next reference design should explicitly choose between current Arpaia's
truncation-order physical defect and a conservative endpoint update. Campoli
is the least ambiguous existing reference. The transport/geometry/MPI
contract above can then be reviewed and promoted separately from topology
repair and higher-order multirate reconstruction.

Before calling it a production moving hierarchy, require matched equal-bin,
stationary/rigid-translation, nonuniform deforming, deeper-bin and changing-bin
gates; repeated migration and restart; flip/cascade/periodic-seam accounting;
then modest Yee/Gresho and discontinuous-flow tests using the agreed CFL.
The new small tests already answer the immediate coexistence and error-
attribution questions, so no large KH campaign was needed in this session.

Chapter 4 can state a feasible distributed event/ledger construction and
clearly identified conservation and accuracy conditions. It should not yet
state that the existing Arpaia rebase is exactly physically conservative,
that keep-U topology closure is a conservative transfer, or that a two-stage
hierarchy is necessarily second-order across bins. Its final scientific
result set should distinguish validated limited-scope behavior from the
remaining mathematical choices.

## 9. Reproduction and retained artifacts

From the AREPO root, the independent audit is:

```bash
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python \
  tests/rd/audit_ale_hierarchy_mass_rebase.py
```

The campaign contains `prepare_euler.py`, `patch_mpi_prototype.py`,
`validate_euler.py`, `validate_flip.py`, `scalar_rebase.json`,
`euler_summary.json`, `flip_summary.json`, `provenance.json`, four isolated
builds, their Config/header snapshots, linkage reports and run directories.
The complete copied source is `mpi_src`; the reviewable patch also resides
under `dev_log/patches/`.

Use the repository Makefile with `SRC_DIR=<campaign>/mpi_src`, a specific
`CONFIG=<campaign>/config/{campoli,arpaia}.sh`, and distinct `BUILD_DIR`/`EXEC`
to reproduce the MPI builds. Run `validate_euler.py --run-mpi` and
`validate_flip.py --run` from the campaign directory in an environment that
allows local OpenMPI process sockets. Without the run flags they inspect the
retained results. Three snapshots per case are sufficient for these gates.

The first baseline parameter attempt was rejected because maximum timestep
equalled total runtime; it was corrected to two coarse intervals before any
evolution. The first sandboxed `mpiexec` attempt failed to bind a local socket;
the same bounded simulations completed with the required local-socket access.
Neither rejected attempt is counted as a numerical failure or a passed gate.
