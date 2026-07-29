# AREPO Residual Distribution Development Log

This log records numerical assumptions, code changes, tests, and unresolved
questions for the experimental RD solver in `/home/zwu/arepo_rd/arepo`.

## Log metadata

- Author: `gpt-5.6-sol high`
- Time zone: Europe/London
- Metadata added: 2026-07-27 18:03:00 BST (+0100)

## 2026-07-27: initial code audit

- Author: `gpt-5.6-sol high`
- The audit was performed earlier in the same working session. Exact audit
  start/end times were not captured; this metadata was added retrospectively at
  2026-07-27 18:03:00 BST (+0100), rather than inventing an audit timestamp.

### Scope reviewed

- `context.md`
- `src/hydro/residual_distribution_solver.c`
- RD changes in initialization, primitive recovery, mesh exchange, and the main
  time integration loop
- Gresho and Yee RD configurations
- existing 2-rank and 4-rank Gresho output under
  `Hydro_data_analysis/Data_arepo_RD/gresho_2d`

### Confirmed observations

1. The current solver is a two-dimensional, vertex-based RD implementation. It
   uses the median-dual/lumped control area, assigning `|T|/3` from every
   Delaunay triangle to each vertex. Density is recovered from
   `Mass / DualArea`, rather than from the AREPO Voronoi volume.

2. RD residuals are called at both locations where the normal AREPO solver calls
   `compute_interface_fluxes()`. Each call applies half of the triangle
   timestep. This resembles AREPO's two half-step flux update, but it has not
   been shown to be equivalent to the RK2 method assumed in the RD derivation.

3. The primitive-variable time extrapolation is effectively disabled by a
   boolean-condition bug:

       if(st->rho + delta_time->rho ||
          st->press + delta_time->press < 0)

   The first operand is normally nonzero and therefore true, so the extrapolated
   state is almost always rejected.

4. Individual timesteps are not currently conservative for this element-based
   update. Only triangles containing an active local vertex are selected.
   Element residuals cancel globally only when the appropriate complete set of
   elements is advanced consistently. In addition, a boundary element can be
   assigned to a rank on which none of its local vertices is active, even when a
   remote vertex is active.

5. `DualArea` is cleared for all local gas cells inside `compute_residuals()`,
   but reconstructed only from the selected active triangles. It therefore does
   not necessarily represent the complete median control area when individual
   timesteps or MPI boundaries are involved.

6. The boundary-element responsibility function assumes every vertex has a
   non-negative MPI task. Actual Delaunay data contains infinity/sentinel
   vertices with negative point and task indices. Such elements must be rejected
   before responsibility, geometry, or state lookup.

7. The B scheme contains two definite implementation errors: integer `abs()` is
   applied to doubles, and `Sum_Flux_N[i]` uses the outer triangle index instead
   of the fluid-variable index `k`.

8. Matrix regularization currently checks whether any matrix entry is close to
   zero. This is not a singularity or conditioning test. The code then forms an
   explicit inverse and does not consistently handle both LAPACK failure codes.

9. Boundary-triangle duplicate detection sorts `MyIDType` values with
   `sizeof(int)` and an integer comparator. This works only while `LONGIDS` is
   disabled.

10. Unconditional triangulation diagnostics in `run.c` add large output and
    access invalid particle indices for sentinel Delaunay points.

### Evidence from existing runs

- The 4-rank LDA/random48 run terminates after gas particle ID 431 obtains
  negative mass shortly after the first few synchronization points.
- Comparable 2-rank runs reach the final time.
- Existing `energy.txt` files show gas-mass changes from 1.0 to approximately:

  - `1.00037` for ring48
  - `1.00208` for random48
  - `1.00975` for v1e-8/random48

  A completed run is therefore not sufficient evidence of conservation.

### Test-infrastructure problems

- `examples/gresho_2d/check.py` assumes a bulk velocity of 3.0, whereas the
  current IC generator uses `1e-8`.
- The checker expects `IC.hdf5` and an `output/` subdirectory that the current
  launcher does not create.
- `default_rng()` is used without a seed for random meshes, so nominally
  comparable runs can use different particle distributions.
- No automated pass/fail criterion currently checks global mass, momentum,
  energy, finite primitive variables, or MPI-rank invariance.

### Immediate development decision

Until a consistent asynchronous RD formulation is derived and tested, the
validated baseline will be restricted to:

- two dimensions;
- a static mesh;
- one globally synchronized hydrodynamic timestep;
- exactly one of LDA, N, or B distribution schemes.

The median dual area will remain the reference control volume for this baseline.
Using the AREPO Voronoi volume is a separate discretization choice that requires
a mathematical derivation rather than a direct substitution.

### Planned validation sequence

1. Fix deterministic condition, indexing, type, and sentinel-vertex bugs.
2. Compute the complete median control area independently of the active residual
   set.
3. Make the Gresho IC and checker deterministic and self-consistent.
4. Run identical static-mesh cases with 1, 2, and 4 MPI ranks using equal
   timesteps.
5. Require finite and positive states and monitor global mass, momentum, and
   energy at every output.
6. Only after the synchronized baseline is rank-independent, investigate the
   time integrator and then individual timesteps.

### Open mathematical questions

- Whether the two AREPO half-step calls can be formulated as a valid
  second-order RD predictor/corrector, or whether a separate SSP-RK2 stage
  implementation is required.
- How to formulate local/asynchronous element updates without losing
  conservation.
- How the moving median control volume and element residual must be coupled to
  satisfy the ALE geometric conservation law.
- Whether an alternative Voronoi control volume can retain the desired RD
  accuracy and conservation properties.

## 2026-07-27: synchronized-baseline implementation and smoke tests

- Author: `gpt-5.6-sol high`
- Code modification window, reconstructed from file modification timestamps:
  2026-07-27 17:15:17 to 17:19:51 BST (+0100).
- Test execution and result logging completed by:
  2026-07-27 17:25:18 BST (+0100).
- Timestamp metadata verified and added:
  2026-07-27 18:03:00 BST (+0100).

### Code changes

- Added compile-time guards requiring the currently validated RD path to use
  `TWODIMS`, `VORONOI_STATIC_MESH`, `FORCE_EQUAL_TIMESTEPS`, and exactly one
  residual distribution scheme.
- Enabled `FORCE_EQUAL_TIMESTEPS` in the Gresho and Yee RD example configs.
- Added a physical-element predicate that rejects Delaunay triangles containing
  sentinel points, invalid tasks, or invalid exchanged-particle indices before
  geometry and MPI responsibility logic.
- Fixed the primitive-state extrapolation positivity condition so valid
  extrapolated states are no longer rejected unconditionally.
- Recomputed the complete median control area independently of the active
  residual set, and added a finite/positive control-area check before primitive
  recovery.
- Sized the exported RD flux list directly from the selected element set and
  added an explicit capacity check.
- Made boundary-element ID sorting compatible with `LONGIDS`.
- Fixed the B-scheme `abs()` and index errors.
- Made LAPACK inversion failures terminate consistently with a non-success
  status instead of calling `exit(0)`.
- Moved verbose triangulation dumps behind `RD_OUTPUT_DIAGNOSTICS`.
- Seeded the random Gresho point generator with `default_rng(0)`.

The current matrix regularization criterion and explicit inverse remain to be
reworked; this change only makes failure reporting reliable.

### Build result

The Gresho RD configuration compiled successfully with GCC/OpenMPI and MKL.
The RD source still reports pre-existing unused-variable warnings, but there
were no new compilation errors.

### Runtime tests

All tests used the same binary, static mesh, LDA scheme, equal timesteps, and
double precision. Temporary output is stored under
`/tmp/arepo_rd_smoke.MtjbOE`.

1. Ring48, `t=0.01`, 1/2/4 MPI ranks:

   - all runs reached the final time;
   - total mass remained 1.0 at the precision written to `energy.txt`;
   - 2-rank and 4-rank snapshots differed from the 1-rank snapshot by only
     approximately `1e-15` in scaled primitive/conserved fields;
   - minimum density was about `0.99947` and minimum pressure about `4.9997`.

2. Ring48, `t=0.1`, 1/4 MPI ranks:

   - both runs reached the final time;
   - reported relative mass change was zero and relative total-energy change
     was about `3.48e-8`;
   - rank-to-rank field differences remained at approximately `1e-15`;
   - all masses, densities, and pressures remained positive.

3. The previously problematic v0/random48 mesh, `t=0.01`, 1/4 MPI ranks:

   - both runs reached the final time;
   - reported relative mass change was zero and relative total-energy change
     was about `2.67e-7`;
   - rank-to-rank field differences remained at approximately `1e-15`;
   - minimum density was about `0.99433` and minimum pressure about `4.9994`.

## 2026-07-27: deferred MPI simplex-responsibility redesign

- Author: `gpt-5.6-sol high`
- Design review recorded: 2026-07-27 23:20:26 BST (+0100).
- Sources reviewed:

  - AREPO's native finite-volume responsibility and flux exchange in
    `src/hydro/finite_volume_solver.c`;
  - active-mesh and ghost construction in `src/mesh/voronoi/voronoi.c` and
    `src/mesh/voronoi/voronoi_ghost_search.c`;
  - the corresponding 2D and 3D Voronoi geometry paths;
  - the current RD triangle responsibility, time-bin selection, duplicate
    removal, and remote residual exchange;
  - `/home/zwu/MyThesis/useful_resources/MPI_1.png` and `MPI_2.png`.

### Finding

AREPO's native face rule is simpler than the current RD majority-task rule:

1. Skip a Voronoi face if neither of its two cells is active.
2. Order the two cells by globally unique particle ID.
3. If the lower-ID cell is active, its owning task computes the face.
4. Otherwise the active higher-ID cell's task computes the face.
5. Apply the opposite-side update locally or through the MPI flux list.

This guarantees that the selected owner holds an active primary cell. That is
important because the normal hierarchical mesh is constructed around active
primary cells and completed with the ghost points needed for their local
Delaunay stars. The responsibility rule is independent of mesh position and
face velocity, so mesh motion does not alter ownership.

The current RD rule instead assigns a boundary simplex to the task owning the
largest number of its vertices. With individual time bins, that task may own no
active vertex and may not have constructed the relevant active-cell simplex.
Because `has_one_active_local` is evaluated before responsibility, every rank
can reject the same globally active simplex. For example, a triangle with one
active red vertex and two inactive green vertices is rejected by red because
green wins the majority rule, and rejected by green because it has no active
local vertex.

### Proposed dimension-independent ownership rule

Use the active vertex with the smallest global particle ID as the canonical
simplex owner. In 2D the simplex has three vertices; in 3D it has four. The
ownership loop itself therefore does not need separate 2D and 3D algorithms.

Conceptual pseudocode:

```text
function rd_simplex_responsibility(simplex):
    active_vertices = []

    for each vertex p in simplex:
        if p is a sentinel or has invalid task/index metadata:
            return INVALID

        # DP[p].timebin is available for both local and imported mesh points.
        if TimeBinSynchronized[DP[p].timebin]:
            active_vertices.append(p)

    if active_vertices is empty:
        return INACTIVE

    # Particle IDs are the global, geometry-independent ordering.
    owner_key = minimum((DP[p].ID, DP[p].task)
                        for p in active_vertices)

    # Compute only on the copy containing the selected cell as a local
    # primary point. Ghost or periodic-image copies do not claim ownership.
    owner_is_local_primary =
        exists p in simplex such that
            (DP[p].ID, DP[p].task) == owner_key and
            DP[p].task == ThisTask and
            0 <= DP[p].index < NumGas

    if not owner_is_local_primary:
        return NOT_RESPONSIBLE

    return RESPONSIBLE
```

For ordinary globally unique IDs, `task` is only a deterministic secondary
key. Equal IDs can occur for reflective or periodic images, so those cases
must follow an explicit primary-copy rule analogous to AREPO's native face
handling.

Activity must be determined from all simplex vertices, including imported
vertices. It must not be prefiltered by `has_one_active_local`. Once a simplex
has one owner, its residual contributions can be applied to local vertices and
exported to remote vertices using the existing conservative flux-list pattern.

### Why implementation is deferred

The ownership rule itself is modest and naturally extends to a tetrahedron, but
enabling the full requested modes is substantially more complex:

- A periodic or reflective simplex can have multiple local geometric images.
  It remains to be demonstrated that the local-primary condition alone removes
  every duplicate without deleting a distinct physical image.
- A debug coverage audit is needed before replacing the current rule. A
  canonical simplex key should count global copies, owner claims, and actual
  residual evaluations, requiring exactly one evaluation for every active
  physical simplex.
- Selecting an owner does not by itself establish a conservative and
  second-order asynchronous RD integrator. Stage timing, prediction times, and
  updates to inactive vertices still need a derivation.
- Moving-mesh RD additionally requires a consistent ALE element residual,
  time-dependent median control volumes, and satisfaction of the geometric
  conservation law. The current use of an average vertex velocity is not a
  sufficient derivation.
- The current RD algebra is strongly hard-coded for a 2D triangle: three
  vertices, four Euler variables, 2D normals, and 4-by-4 matrices. A 3D
  tetrahedral solver needs four vertices, five Euler variables, 3D face
  normals, and 5-by-5 distribution matrices. This is separate from the
  ownership generalization.

### Deferred validation sequence

1. Keep the current static-mesh, equal-timestep baseline while completing
   manual grid and MPI-rank tests.
2. Add a debug-only global simplex coverage audit to the existing rule.
3. Prototype the minimum-active-ID owner rule in 2D with equal timesteps and
   verify one owner and one evaluation per simplex.
4. Enable fixed-mesh hierarchical time bins only after deriving and testing
   the asynchronous RD stage update.
5. Address moving-mesh ALE geometry and the geometric conservation law.
6. Generalize the numerical RD operator to tetrahedra only after the 2D
   moving/local-time formulation is validated.

Decision: do not replace MPI responsibility in the current patch. Preserve the
compile-time restrictions to 2D, static mesh, and equal timesteps, and treat
the minimum-active-ID rule plus coverage audit as the planned redesign.

## 2026-07-27: complete B-scheme floating-point blend fix

- Author: `gpt-5.6-sol high`
- Modification started: 2026-07-27 23:34:35 BST (+0100).
- Build and smoke-test verification completed:
  2026-07-27 23:37:15 BST (+0100).

### Code change

The remaining integer absolute-value call in the B-scheme blend coefficient
was changed from

```c
Theta_E[k] = abs(Phi[k]) / Sum_Flux_N[k];
```

to

```c
Theta_E[k] = dmin(1.0, fabs(Phi[k]) / Sum_Flux_N[k]);
```

This prevents conversion of the floating-point total residual to `int` and
keeps the theoretically bounded blend coefficient in `[0, 1]` in the presence
of roundoff. No integer `abs()` calls remain in the RD source.

`regularize_matrix()` was deliberately left unchanged. Its fixed entry-wise
threshold remains a temporary measure pending replacement by a scale-aware
conditioning test and a direct linear solve.

### Verification

- An independent `B_SCHEME` binary compiled successfully with OpenMPI, HDF5,
  and MKL. The first direct build attempt lacked the MKL module and failed to
  locate `lapacke.h`; rebuilding with the project modules loaded succeeded.
- A one-rank, static-mesh, equal-timestep Gresho ring48 run reached `t=0.01`.
- Initial/final total mass was `1.0`; total energy changed from
  `8.616765015730412` to `8.616765015730413`.
- Final minimum density was `0.9994729553`, final minimum pressure was
  `4.9997163183`, and all checked mass, density, and pressure values were
  finite and positive.
- Temporary build and output are under `/tmp/arepo_rd_bscheme.K03pY0`.

This is a compile and single-rank smoke test only; B-scheme MPI-rank invariance
and long-time stability remain untested.

## 2026-07-28: independent review of the CodeX changes and re-analysis of the time integration

- Author: `Kimi K3`
- Review recorded: 2026-07-28 00:12:53 BST (+0100).
- Sources reviewed:
  - the full uncommitted CodeX diff (`git diff`, ~230 lines across 11 files);
  - `src/hydro/residual_distribution_solver.c` in full context;
  - the original public-AREPO `run.c` / `finite_volume_solver.c` at root commit
    `b1f3f61` for comparison;
  - `src/hydro/update_primitive_variables.c` (`TimeLastPrimUpdate` stamping);
  - sentinel/ghost point bookkeeping in `src/mesh/voronoi/voronoi_2d.c` and
    `voronoi_ghost_search.c`;
  - thesis Chapter 3 and
    `/home/zwu/MyThesis/useful_resources/RD_schemes_notes.md`;
  - git history of the extrapolation bug and of the "test RK2 for RD" commit
    `d40c490`.

### Assessment of the CodeX changes

Verified correct:

- `rd_triangle_is_physical()`: sentinel points are negative DP indices
  (`DPinfinity = -4`, `DP[-3..-1]`, `voronoi_2d.c:160-180`); ghost points carry
  the real remote task `< NTask`; local image points use `task = ThisTask` with
  `index = p + NumGas`, consistent with the downstream `SphP_index -= NumGas`
  convention. The predicate matches the actual tessellation bookkeeping.
- B-scheme fix: the new `Theta_E[k] = min(1, |Phi[k]| / sum_j |Flux_N[k][j]|)`
  is exactly the thesis formula `Theta_l = |phi_l^T| / sum_j |(phi_j^{N,T})_l|`,
  which lies in `[0, 1]` by construction; `dmin` only guards roundoff. The old
  code had two definite bugs (integer `abs()` on doubles, `Sum_Flux_N[i]` using
  the outer triangle index).
- `mat_inv` error propagation (return LAPACK info, `terminate_program` on
  failure instead of `exit(0)`), `lapack_int ipiv[n]`, LONGIDS-safe ID
  sorting, FluxRD capacity sizing/check, DualArea decoupled from the active
  residual set plus the validity check in `update_primitive_variables.c:191`,
  diagnostics behind `RD_OUTPUT_DIAGNOSTICS`, deterministic IC seed, and the
  compile-time guards (`TWODIMS` + `VORONOI_STATIC_MESH` +
  `FORCE_EQUAL_TIMESTEPS` + exactly one scheme). The guards make the
  DualArea-completeness argument self-consistent (all cells active).
- Deferring the MPI simplex-responsibility redesign: the proposed
  minimum-active-ID ownership rule is isomorphic to AREPO's native face rule
  and the deferral rationale is sound.

Caveats:

1. The extrapolation-condition fix changes the numerics of the validated
   baseline: the old bug made time extrapolation a no-op, so all previous
   "correct" results (including comparisons with the standalone code) were
   obtained without extrapolation. Post-fix verification was smoke-test level
   only; quantitative accuracy must be re-established.
2. The comment `triangle_dt *= 0.5; // RK2 half timestep`
   (`residual_distribution_solver.c:460`) is misleading; see the time
   integration analysis below. It should be renamed to describe what the code
   actually does.
3. Minor performance notes (non-blocking): `reset_dualarea` redoes the full
   classification and MPI exchange on every `compute_residuals` call (twice
   per step, redundant on a static mesh);
   `boundary_triangle_check_responsibility_thistask` `mymalloc`s an
   `NTask`-sized array per boundary triangle per call.
4. `build_case.sh ensure_mkl_environment` hard-exits when MKL is absent,
   which prevents falling back to system LAPACKE off-cluster; a warning would
   be preferable.

### Re-analysis of the time integration (supersedes "open question 1" wording)

With `FORCE_EQUAL_TIMESTEPS` and a static mesh, the two `compute_residuals`
calls per loop iteration now (post-fix) have the following structure.
`TimeLastPrimUpdate` is stamped at `All.Time` in
`update_primitive_variables` (`update_primitive_variables.c:94`), which runs
at the bottom of each iteration after `find_next_sync_point()` has advanced
`All.Ti_Current`. Therefore, for the step from `t_k` to `t_{k+1}`:

- first call (`run.c:229`, `All.Time = t_k`):
  `dt_Extrapolation = t_k - TimeLastPrimUpdate = 0`, so the residual is
  evaluated exactly at `W^k`, applied with weight `dt/2`;
- second call (`run.c:324`, `All.Time = t_{k+1}`):
  `dt_Extrapolation = dt`, so the residual is evaluated at
  `W* = W^k + dt * (Lax-Wendroff-type Taylor extrapolation using the
  Green-Gauss gradients of W^k)`, applied with weight `dt/2`;
- primitive variables are not updated between the two calls, so the combined
  update is `U^{k+1} = U^k - (dt/2) [phi(W^k) + phi(W*)]`.

This is Heun's explicit trapezoidal rule, a legitimate two-stage RK2, with a
first-order Taylor predictor in place of the RD lumped predictor. It is
formally second order in time. The earlier audit statement "not shown to be
equivalent to RK2" is thus too pessimistic: the skeleton of an RK2 is present
after the extrapolation fix. Before the fix, both calls evaluated `phi(W^k)`,
i.e. the update was effectively forward Euler.

Remaining deviations from the thesis RK2-RD (Ricchiuto & Abgrall 2010):

- the space-time total residual distributes the time-defect term
  `sum_j m_ij (U*_j - U^n_j)/dt` with `m_ij = (|T|/3) beta_i`; the current
  lumped Heun form coincides with this only for the N scheme
  (`m_ij = (|T|/3) delta_ij`). For LDA/B the linearity-preserving property of
  the space-time scheme is not guaranteed;
- the B-scheme blend coefficient should act on the total space-time residual;
  it is currently computed per stage on spatial residuals;
- the predictor uses AREPO's Green-Gauss gradient extrapolation rather than
  the RD lumped update `U* = U^n - (dt/|S_i|) sum phi_i(U^n)`. Both are
  first-order predictors so the formal order is unaffected, but the gradient
  predictor needs its slope limiter on non-smooth flows (relevant before
  B-scheme shock tests; verify the limiter is active on the RD path).

### The old Yee-vortex convergence numbers are not a usable baseline

The extrapolation bug entered in `febd68f` (2023-04-05); before that
(`a117a12`, 2023-03-26) no extrapolation machinery existed. Hence the
previously measured convergence orders (N < 1, LDA ~ 2, B ~ 1.5) were all
obtained with effectively forward-Euler time integration. Two consequences:

- LDA ~ 2 despite first-order time integration shows the test setup was
  insensitive to temporal order (spatial error dominated); those numbers can
  neither validate nor invalidate the RK2 question;
- N < 1 is suspicious (N should be first order) and was likely polluted by
  bugs fixed only later in 2023 (index, DualArea, sentinel handling). It must
  be re-measured on the current code.

### Prioritized test plan

- P0: repair the test infrastructure. `check.py` still assumes bulk velocity
  3.0, expects `IC.hdf5` and an `output/` directory the launcher does not
  create, and has no pass/fail criteria. Add automated checks: global
  mass/momentum/energy drift thresholds, positivity of rho/p, MPI-rank
  invariance (~1e-15), and clean termination.
- P1: new temporal convergence test (decisive for the RK2 question): fixed
  Yee mesh, CourantFac 0.4 / 0.2 / 0.1 / 0.05, plot L1/L2 error vs dt.
  Expect ~2 for LDA/B post-fix and 1 with extrapolation disabled (run the
  latter as a control). Before trusting the static analysis above, add a
  one-line diagnostic printing `dt_Extrapolation` at both call sites and
  confirm the 0 / dt pattern.
- P1: re-run the spatial Yee convergence at small fixed CFL on the current
  code; confirm LDA ~ 2, B between 1 and 2, N ~ 1, and investigate any
  sub-first-order N result.
- P2: bring N and B schemes to the same validation level as LDA
  (1/2/4-rank invariance, long runs, glass IC). Test B-scheme monotonicity on
  a shock problem (Noh or 2D Sod; LDA should oscillate, B should not), after
  confirming the gradient limiter is active in the RD predictor.
- P2: instrument `regularize_matrix` (count trigger frequency in standard
  tests; `sum K^-` is near-singular for uniform/quiet flow, most dangerous
  for the N-scheme inversion), then replace the entry-wise threshold with a
  scale-aware conditioning test and a direct solve. Also close the thesis
  red-note TODO on normal-vector normalization consistency between the
  derivation (`|n_i|` = opposite edge length) and `triangle_get_normals_area`.
- P3: MPI stress coverage: odd rank counts (3), glass IC, full-period
  `t = 3` runs, and reproducing/archiving the occasional mesh-dependent
  termination noted in `context.md` item 4.

### Outlook

If the P1 temporal test confirms the Heun structure, synchronized static-mesh
time integration is no longer the main bottleneck. The harder problems are
the conservative asynchronous update (`context.md` item 4, audit observation
4) and the moving-mesh ALE formulation with the geometric conservation law
(item 5); the remaining equal-timestep RK2-RD differences (time-defect
distribution, B-blend location) are accuracy-property questions that can be
quantified with sensitivity tests on distorted (random/glass) Yee meshes.

## 2026-07-28: review of the CodeX and Kimi work; removal of matrix regularisation

- Author: `Claude Code Opus5`
- Sources reviewed:

  - `context.md` and the whole of this log;
  - the CodeX changes as committed in `ebe1be2`;
  - `src/hydro/residual_distribution_solver.c` in full, plus
    `triangle_get_normals_area()` in `src/mesh/voronoi/voronoi.c`, the
    orientation guarantees in `src/mesh/voronoi/voronoi_2d.c`, the two
    `compute_residuals()` call sites in `src/main/run.c`, and the Riemann
    solver selection in `src/hydro/finite_volume_solver.c`;
  - thesis chapter 3 and `/home/zwu/MyThesis/useful_resources/RD_schemes_notes.md`,
    sections 8 and 10;
  - `examples/gresho_2d/` and `examples/yee_2d/` initial conditions, parameter
    files and checkers.

### Assessment of the CodeX changes

Agreed with, and independently re-derived where relevant:

- the compile-time restriction to `TWODIMS` + `VORONOI_STATIC_MESH` +
  `FORCE_EQUAL_TIMESTEPS` + exactly one scheme;
- decoupling `DualArea` from the active residual set;
- `rd_triangle_is_physical()`, the LONGIDS-safe ID sorting, the `FluxRD_list`
  capacity check, the extrapolation-condition fix, and the diagnostics guard;
- deferring the MPI simplex-responsibility redesign.

One item deserves more credit than it was given: `int ipiv[n+1]` ->
`lapack_int ipiv[n]` is not a style fix. The build now links `-lmkl_rt`; if MKL
resolves to the ILP64 interface, `lapack_int` is 64-bit and the original `int`
array is overrun by `dgetrf`.

The principal disagreement is with the decision to leave `regularize_matrix()`
in place. It is not a cosmetic wart. See the next two sections and
`regularize_matrix_debug_report.md`.

A second point: the smoke tests were run to `t = 0.01` and `t = 0.1`, while
`examples/gresho_2d/param_RD.txt` sets `TimeMax = 3.0`. Being 30 to 300 times
shorter than the real case, they cannot detect the drift that motivated the
audit, so "relative mass change zero" was not evidence of a fix.

### Assessment of the Kimi review

The line-by-line verification of the CodeX diff is sound and is not repeated
here. The time-integration re-analysis is also correct as far as the mechanics
go: `dt_Extrapolation` is indeed `0` at `run.c:229` and `dt` at `run.c:324`,
and the two half-weight calls do form a two-stage update. Two corrections:

1. **The conclusion that time integration is no longer the main bottleneck is
   premature.** The scheme applies `m_ij = (|T|/3) delta_ij` — the N-scheme
   lumped mass matrix — to LDA and B as well. Per `RD_schemes_notes.md`
   section 10.5, the LDA choice is `m_ij^{LDA} = (|T|/3) beta_i^{LDA}`. The
   naive combination of a lumped mass with a linearity-preserving spatial
   distribution is exactly the construction that Ricchiuto & Abgrall (2010)
   introduced the total-residual RK-RD formulation to repair: it is not LP, and
   for unsteady problems it degrades to first order. The issue is not temporal
   order, it is the combined space-time accuracy.

2. **The proposed P1 test cannot answer the question it is posed for.**
   Refining `dt` at fixed mesh converges to the semi-discrete solution and
   measures only the ODE order; it will report second order regardless of the
   mass-matrix problem. Worse, `examples/yee_2d/create.py` has no bulk
   velocity, so the Yee vortex as configured is a *stationary* solution — a
   temporal refinement study on it has almost no signal. The same applies to
   the current Gresho setup, where the IC generator uses `1e-8` instead of the
   bulk boost of `3.0` that `check.py` still assumes. The historical
   `LDA ~ 2 / N ~ 1 / B ~ 1.5` numbers are steady-state convergence orders,
   for which LDA second order and N first order are the expected results.

   The decisive experiment is an *advected* smooth vortex on a fixed mesh with
   `dt` proportional to `h`. It does not exist in the repository yet.

Additional practical findings on the test setup:

- `examples/yee_2d/create.py:44` calls `np.random.uniform` unseeded for the
  ring starting angles. CodeX seeded the Gresho generator but not this one, so
  Yee convergence studies are currently not reproducible.
- The Yee mesh is polar and centred on the vortex, hence aligned with the flow.
  An advected test must use a glass or random mesh; a regular Cartesian point
  set should be avoided because its Delaunay triangulation is degenerate
  (cocircular points) and anisotropic.
- Restoring the boosted Gresho gives a Galilean-invariance test, which is the
  sharper test for a vertex-based scheme on a static mesh.

### New findings

1. **`regularize_matrix()` breaks conservation, at `O(1)` in stagnant flow.**
   The conservation of both LDA and N rests on `sum_i K_i^+ = -S^-`. Adding
   `eps I` to `S^-` before inversion gives
   `sum_i beta_i = S^- (S^- + eps I)^{-1} = I - eps (S^- + eps I)^{-1}`, whose
   per-mode deficit is `eps / (sigma_p + eps)`. Measured on one representative
   triangle: `1.0` at `u = 0`, `1.3e-2` at `|u| = 1e-8`, `3e-10` at
   `|u| = 0.5`.

   These are per-element relative figures. I initially expected them to explain
   the historical gas-mass changes (1.00037 / 1.00208 / 1.00975) recorded above;
   the A/B measurement below shows that they do **not**. Those runs predate the
   `ebe1be2` fixes, and the regularisation alone accounts for a drift of order
   `1e-14` in the current code, not `1e-2`. The historical drift was almost
   certainly caused by the bugs CodeX fixed. The reason the per-element defect
   does not translate into a comparable global drift is that a stagnant element
   is usually also a nearly uniform one, where `phi^T` is close to zero — so the
   broken identity multiplies an almost vanishing residual. That is a fortunate
   accident of these test problems, not a property the scheme controls.

2. **`S^-` is structurally rank deficient when `u_n = v_n`.** At stagnation the
   entropy and shear eigenvalues vanish, `K_j^-` becomes rank 1, and the sum
   over three vertices has rank at most 3. This is not round-off. The
   degeneracy condition is the mesh moving with the fluid, so on a Lagrangian
   moving mesh it is the normal state of every element — the fix below is a
   prerequisite for ALE-RD, not only a Gresho patch.

3. **The singularity is removable.** `phi^T` provably lies in `range(S^-)`, and
   the distributed residuals are invariant under adding any null-space vector
   to the solution, because `z in null(S^-)` implies `K_i^+ z = 0` for each `i`
   separately. The LDA and N distributions are therefore well defined and
   unique at stagnation; only `(S^-)^{-1}` fails to exist. No regularisation is
   mathematically required. Proofs and numerical verification are in
   `regularize_matrix_debug_report.md`, section 3.

4. **`triangle_get_normals_area()` uses Heron's formula**
   (`src/mesh/voronoi/voronoi.c:1169-1170`), which suffers catastrophic
   cancellation on sliver triangles and can return NaN. The three vertex
   coordinates are already available, so the signed cross product is both
   cheaper and stable, and supplies the orientation check for free. AREPO does
   guarantee positively oriented 2D triangles (`voronoi_2d.c:733-739`), but
   nothing on the RD path asserts it, and a flipped orientation silently
   reverses the upwind direction. Not yet changed; scheduled next.

5. **`apply_FluxRD_list()` and `apply_DualArea_list()` index `P[p]`/`SphP[p]`
   without bounds checking** (`residual_distribution_solver.c:1100`, `:1185` in
   the baseline numbering). Given commits `5db43bb` and `c64a069`, a one-line
   guard would convert silent memory corruption into a clean error.

6. **Under the enforced `VORONOI_STATIC_MESH`, calling `reset_dualarea()` from
   `compute_residuals()` is dead work** — four full classifications and two
   extra MPI collectives per step for a quantity that cannot change. The intent
   is right; the call belongs after mesh construction.

7. **Duplicate boundary-triangle detection keys on the sorted ID triple only.**
   In a periodic box two geometrically distinct images can share an ID triple,
   in which case a real element is dropped. The key should include the periodic
   offset or the centroid.

8. **Low-Mach dissipation affects AREPO's own finite-volume solver equally.**
   The default path is the exact Riemann solver (`finite_volume_solver.c:354`)
   and there is no low-Mach correction anywhere in `src/`. The moving mesh
   removes the advective (Galilean) error but not the acoustic low-Mach error,
   which depends on `u/c` within the fluid and not on the frame. Consequently a
   low-Mach preconditioner applied to RD alone would bias the RD-versus-FV
   comparison. Recorded as an open question, not scheduled.

### Code change made

`regularize_matrix()` and `needs_regularization()` were removed, together with
`THRESHOLD` and `REGULARIZATION_CONSTANT`. The explicit inverse of `S^-` was
replaced by a solve against the same matrix for both right-hand sides, with a
pivot-ratio guard and a minimum-norm least-squares fallback, followed by an
isotropic rebalance that restores `sum_i phi_i = phi^T` to machine precision.
Assertions A1 and A2 and the `RD-DIAG` solver statistics were added behind a
new `RD_DEBUG_ASSERTS` compile flag, which is enabled in both RD example
configurations.

The full derivation, the defect analysis, the two lemmas, the change list and
the deliberate exclusions are documented in
**`regularize_matrix_debug_report.md`** (same directory). The previous
behaviour remains reproducible at commit `ebe1be2`.

### Verification

Both binaries were built from the same `Config_RD.sh` (LDA, static mesh, equal
timesteps, double precision) against system LAPACKE, and run on one rank on
`IC_gresho_v1e-8_random48`. Totals were recomputed from the snapshots, because
`energy.txt` is written with `%g` and carries only six significant digits — a
point worth noting for future conservation checks.

| | `ebe1be2` | this change |
| --- | --- | --- |
| gas-mass drift at `t = 0.5` | `-2.198e-14` | `-2.220e-16` |
| gas-mass drift at `t = 1.0` | `-2.276e-14` | `-8.882e-16` |
| total-energy drift at `t = 1.0` | `-2.062e-16` | `-2.062e-16` |
| `min(rho)` at `t = 0.5` / `t = 1.0` | `0.997078` / `0.995596` | `0.997078` / `0.995596` |

Mass conservation improves by roughly two orders of magnitude, to accumulated
round-off. Over 26322 solver calls the pseudo-inverse fallback was never needed
on this initial condition; the worst pivot ratio was `8.05e-12`
(`kappa ~ 1.2e11`) and the worst pre-rebalance conservation defect `1.64e-14`.

The baseline drift barely grows between `t = 0.5` and `t = 1.0`, so it is
incurred during the early stagnant phase and then frozen — consistent with the
minimum pivot ratio rising from `4.3e-10` at `t = 0` to `2.8e-5` by `t ~ 0.96`
as the vortex spins up. `min(rho)` agrees to all six printed digits between the
two runs, so the solutions are not measurably different in this configuration.

Repeating on `IC_gresho_v0_random48`, where the outer region is at rest exactly,
does exercise the rank-deficient path: **2108 of 4610 elements, 45.7 per cent,
are rank deficient at `t = 0`**, the minimum pivot ratio falls to `3.13e-20`,
and mass and energy still hold to `2.2e-16` at `t = 0.05`. Nearly half the mesh
was previously being handled by an arbitrary diagonal shift.

Two things the drift metric does not show, and which matter more than the drift
itself. First, in those 45.7 per cent of elements the baseline computed
`beta_i^{LDA}` from a perturbed matrix, so the *distribution* was wrong even
where the *sum* was nearly right — an accuracy effect invisible to a
conservation check, and a further reason not to trust convergence orders
measured while the regularisation was active. Second, `REGULARIZATION_CONSTANT`
is an absolute number in a code with a free unit system; the present agreement
depends on the test problems happening to be `O(1)` in code units.

Not yet verified: multi-rank invariance under this change; the N and B schemes
(only LDA was built and run); and behaviour with MKL rather than system LAPACKE,
since MKL was unavailable on the machine used and `build_case.sh` had to be
bypassed in favour of a direct `make`.

### Revised priorities

Ordered so that no measurement is taken while a known contaminant is still
active.

- P0: the change above; triangle area via signed cross product plus assertion
  A3; bounds checks in the two flux-application routines; a uniform static
  medium retention test (`phi^T = 0` identically, so the state must be
  preserved to machine precision) added to the test suite.
- P0: repair `check.py` — read the bulk velocity from the IC, align the
  directory convention with the launcher, and add automatic pass/fail criteria
  on mass, momentum, energy, positivity and MPI-rank invariance. Seed
  `examples/yee_2d/create.py`.
- P1: advected smooth vortex on a glass mesh, `dt` proportional to `h`, with a
  boost ladder `u0` in `{0, 0.25, 1}`. This answers the mass-matrix question
  and quantifies Galilean-invariance loss in one experiment. Archive the result
  as the static-mesh baseline that ALE-RD will later be compared against.
- P1: three-way comparison at fixed resolution using the existing
  `Config_StaticMesh.sh`, `Config_RD.sh` and `Config_MM.sh` — static-mesh FV,
  static-mesh RD, moving-mesh FV. Only the first two isolate the scheme
  difference; the third is the target to beat.
- P1: re-measure the Gresho and Yee convergence orders, which could not be
  trusted while the regularisation was active.
- P2: bring N and B to the LDA validation level; `reset_dualarea()` placement;
  periodic duplicate key; `build_case.sh` should warn rather than exit when MKL
  is absent.
- P3: MPI stress coverage; minimum-active-ID ownership prototype with a
  coverage audit.

### Open questions added

- **Low-Mach accuracy.** Not a consistency defect: after the change above the
  scheme is conservative and convergent, and the low-Mach problem only inflates
  the error constant, roughly as `1/M`. The current test problems sit at
  `M ~ 0.3` (Gresho) and `M ~ 0.7` (Yee), so it does not bite yet. It becomes
  mandatory before self-gravity, cooling and ISM physics. Diagnostic: a
  small-amplitude oblique acoustic wave on a uniform background, measuring the
  L1 error against `M`. Note the possibility, worth checking against Rieper &
  Bader (2009) and related work, that the degeneracy is substantially milder on
  simplicial meshes than on Cartesian ones, which would lower the priority
  further. Because AREPO's finite-volume solver is affected equally, RD and FV
  must be treated together or not at all.
- **Well balancing under gravity.** With self-gravity, `u = 0` but
  `grad p = -rho grad Phi_grav != 0`, so `phi^T != 0` must be cancelled exactly
  by the source term. The current Strang-split treatment is not well balanced
  and a hydrostatic atmosphere will drift. Independent of the low-Mach question.

## 2026-07-29: P0 follow-up — rank invariance, triangle area, floor test

- Author: `Claude Code Opus5`
- Continues the entry above. Full detail in `regularize_matrix_debug_report.md`,
  which now carries the complete verification record.

### 1. Multi-rank invariance

`t = 0.1` on `IC_gresho_v{0,1e-8}_random48`, 1 / 2 / 4 ranks, snapshots matched
by particle ID. Worst relative field difference against the 1-rank run:

| IC | 2 ranks | 4 ranks |
| --- | --- | --- |
| `v1e-8` | `9.6e-15` | `6.2e-15` |
| `v0` | `6.0e-15` | `6.2e-15` |

The element-solve count is *identical* across rank counts (4720640 for `v0`,
9441280 for `v1e-8`), so triangle ownership and duplicate removal reproduce
exactly the same global element set under every decomposition. That is a
stronger statement than the field comparison and is worth keeping as a standing
check when the MPI responsibility rule is eventually replaced.

One caveat this test found: the pseudo-inverse fallback count is `29821` on one
rank against `29820` on two and four. **The branch decision is marginally rank
dependent** — one element in ~4.7 million solves crosses the `1e-12` pivot
threshold differently because a boundary triangle's ghost coordinates come from
a periodic image and `S^-` differs in the last bits. Harmless by Lemma 2, and
the field agreement confirms it, but the solve path is not bit-deterministic
across decompositions.

### 2. Triangle area via signed cross product, plus assertion A3

`triangle_get_normals_area()` now uses
`0.5*((x1-x0)(y2-y0) - (x2-x0)(y1-y0))` and terminates on a non-positive result.

**Correction to my previous entry.** I listed Heron's formula as a plausible
cause of the occasional run termination in `context.md` item 4. Measurement does
not support that. On the periodic Delaunay triangulation of
`IC_gresho_v0_random48` (9959 triangles, worst edge aspect ratio 139) Heron
produces no negative radicands, a maximum relative area error of `1.75e-14`, and
a solution change of `~1e-14`. Heron needs far worse conditioning than these
meshes generate. The change is therefore insurance, not a bug fix.

What it does buy is assertion A3, free with the cross product, guarding the most
dangerous silent failure in the solver: a flipped triangle orientation would
negate all three normals, exchange `K^+` and `K^-`, and make the scheme
anti-diffusive with no error raised. A3 never fired — AREPO's orientation
guarantee holds — but the RD path now checks it instead of assuming it.

### 3. Uniform static medium: floor test and discriminating variant

New case `examples/uniform_static_2d/` with two modes.

`uniform` — periodic unit box, seeded irregular point set, `rho = p = 1`,
`u = 0`. All vertex states coincide, so `phi^T = (sum_i K_i) Uhat = 0`
identically and nothing may change:

```
   1 rank,  t=0.50 : max|drho|/rho = 1.11e-15  max|v| = 5.16e-15  mass drift = 0
   4 ranks, t=0.50 : max|drho|/rho = 6.66e-16  max|v| = 6.10e-15  mass drift = 0
```

This is simultaneously the maximally degenerate solver configuration:
**2097152 of 2097152 element solves, 100 per cent, take the minimum-norm path**.
The new code path is therefore exercised completely, and the state survives.

`perturbed` — the same at rest, plus a smooth periodic pressure ripple of
relative amplitude `1e-3`. Every element stays at stagnation, but `phi^T` is now
non-zero and driven by `grad p`. This is the variant that actually discriminates
between the two code versions, because the plain uniform case cannot (with
`phi^T = 0`, a broken `sum_i beta_i` is invisible). Pre-fix against post-fix:

| | `t = 0.25` | `t = 0.50` |
| --- | --- | --- |
| Density | `1.08e-14` | `2.96e-14` |
| InternalEnergy | `1.18e-14` | `2.93e-14` |
| **Velocities** | **`1.47e-10`** | **`1.66e-10`** |

The difference sits in the velocity field and equals `REGULARIZATION_CONSTANT`
numerically. Both facts are predicted:

- at `u = 0` the flux reduces to `F = (0,p,0,0)` and `(0,0,p,0)`, so `phi^T` has
  only momentum components and the damage must appear in the velocity;
- the `O(1)` loss lives only along `null(S^-) = span{(1,0,0,0)}`, the density
  direction, where by Lemma 1 `phi^T` has exactly zero component. The
  catastrophic term multiplies a strictly vanishing quantity, which is *why the
  old code never blew up*. What remains is the benign `eps/sigma_p` term, equal
  to `eps` when `sigma_p = O(1)`.

This closes the loop on the two over-claims in my previous entry. The
regularisation was survivable because of Lemma 1, not by design, and the error
level was being set directly by an absolute constant. In these code units `K` is
`O(1)` and `eps = 1e-10` costs `1e-10`; in a unit system where `K` entries are
`1e-6` the same constant would cost `O(1)`. D1 and D2 are one defect seen twice.

### Status

P0 items from the previous entry are complete except for the `check.py` repair
and the `examples/yee_2d/create.py` seed. Still unverified: the N and B schemes
(only LDA was built and run), MKL rather than system LAPACKE, odd rank counts,
and long runs to `TimeMax = 3.0` under the final code.

Next per the agreed order is P1: the advected smooth vortex on a glass mesh with
`dt` proportional to `h` and a boost ladder, which is the decisive test for the
lumped-mass-matrix question.

## 2026-07-29: P1 prerequisites on the cluster (Slurm, MKL binary)

- Author: `Claude Code Opus5`

### Operational correction

All testing recorded in the two entries above was run on the login node
`cuillin`, and built there against the system LAPACKE. That was the wrong place,
and it left a real gap: `/usr/local/oneapi` is in `MODULEPATH` on the login node
but does not exist on disk there, so a login-node build silently falls back to
system LAPACKE. The MKL binary, which is what the cluster workflow actually
uses, had never been built or run.

Two scripts were added or generalised so this does not recur:

- `build_case.sbatch` — builds on a compute node, where the oneAPI module tree
  exists, and prints the resulting `ldd` linkage so a silent fallback is
  visible. Supports `--exec` for building a side-by-side binary.
- `run_case.sbatch` — now accepts `--param` and `--binary`; `--ntasks` comes
  from the `sbatch` command line. The previous edit-two-variables workflow still
  works unchanged.

The MKL build succeeded (`libmkl_rt.so.2 => /usr/local/oneapi/mkl/2025.1/...`)
with no new compiler warnings, and reproduces the system-LAPACKE results. The
"MKL not verified" caveat in the previous entries is now closed.

### 1. Rank invariance at 16 and at an odd rank count

`t = 0.1`, `IC_gresho_v{0,1e-8}_random48`, MKL binary, 1 / 3 / 4 / 16 ranks on
compute nodes. Worst relative field difference against the 1-rank run:

| IC | 3 ranks | 4 ranks | 16 ranks |
| --- | --- | --- | --- |
| `v1e-8` | `6.4e-15` | `8.2e-15` | `6.6e-15` |
| `v0` | `5.3e-15` | `1.2e-14` | `6.2e-15` |

Total gas mass is exactly `1` in all eight runs. Odd rank counts show nothing
anomalous, so the historical "certain numbers of MPI processors" failure
(`5db43bb`) does not reproduce under the current synchronized baseline.

The element-solve count is identical across every rank count
(`9441280` for `v1e-8`, `4720640` for `v0`), confirming again that triangle
ownership and duplicate removal reproduce the same global element set under
every decomposition.

The marginal branch non-determinism noted earlier persists and is unchanged in
character: the pseudo-inverse count for `v0` is `29821` at 1, 3 and 4 ranks and
`29820` at 16. One element in 4.7 million crosses the pivot threshold
differently. Harmless by Lemma 2 and confirmed harmless by the field agreement,
but worth remembering that the solve path is not bit-reproducible across
decompositions.

### 2. `dt_Extrapolation` wiring confirmed at runtime

The `RD-DIAG` line now reports the range of `dt_Extrapolation` over each
`compute_residuals()` call. For the 1-rank `v1e-8` run the whole history is
exactly two values, in strict alternation:

```
   1024 calls  dt_extrap=[0.000000e+00, 0.000000e+00]     <- run.c:229, All.Time = t_k
   1024 calls  dt_extrap=[9.765625e-05, 9.765625e-05]     <- run.c:324, All.Time = t_{k+1}
```

with `9.765625e-05` equal to the timestep. Minimum and maximum coincide in every
call, as they must under `FORCE_EQUAL_TIMESTEPS`.

This confirms Kimi's static reading at runtime: the first call evaluates the
residual at `W^k` and the second at `W^k + dt * (Taylor extrapolation)`, each
with weight `dt/2`. The two-stage structure is wired correctly, so the
lumped-mass question is now cleanly separated from any suspicion that the
predictor/corrector pair is simply mis-plumbed.

Note what this does *not* establish, restating the point from the earlier entry:
the two-stage structure being correct is a statement about temporal accuracy
only. The mass-matrix defect degrades *spatial* accuracy on unsteady problems
and is invisible to any fixed-mesh `dt` refinement. It is measured by refining
`h` at fixed CFL on an advected smooth vortex, which is next.

### Status

All three P1 prerequisites are complete. Remaining unverified from earlier
entries: the N and B schemes (only LDA has been built and run) and long runs to
`TimeMax = 3.0` under the final code.

Results and parameter files are archived under
`/home/zwu/Hydro_data_analysis/Data_arepo_RD/gresho_2d/rank_invariance/`.
The validated MKL binary is `arepo/Arepo_rd_mkl`.

## 2026-07-29: N and B code paths exercised; two build failures and a false alarm

- Author: `Claude Code Opus5`
- Detail in `regularize_matrix_debug_report.md`.

**Scope disclaimer.** Nothing in this entry measures error against an exact
solution. The tests below establish only that the N and B code paths execute,
conserve, are independent of the MPI decomposition, and produce genuinely
distinct results. In particular the Gresho runs compare different rank counts
*to each other*, never to the true solution. Every question about accuracy and
convergence order remains open, including the lumped-mass-matrix question.

### Why N and B came before the convergence study

Two reasons that outrank the "P2 coverage" rationale in the earlier plan.
First, the change to the upwind solve rewrote the N branch as well as the LDA
branch, and the N branch had never been compiled, let alone run. Second, N is
the *control* for the convergence study: its first-order behaviour is the
cleanest prediction in RD theory, so if N does not come out at 1 the test setup
is wrong rather than the scheme.

### Result

All three schemes pass the uniform floor test, the perturbed test and rank
invariance at 1 / 4 / 16 ranks, with mass conserved to machine precision. The
schemes are genuinely distinct and the blend sits where it should: on Gresho,
`B vs LDA = 3.7e-2`, `B vs N = 1.2e-1`, `N vs LDA = 1.5e-1`, i.e. B is close to
LDA in a smooth flow, as a working `Theta` requires.

### Two build failures, both silent

Recorded because they are specific to running many automated builds rather than
editing one Config by hand, and because the second one is a trap in the
repository that will catch anyone who tries the same thing.

1. **Concurrent builds corrupt each other.** Two `build_case.sbatch` jobs
   submitted together share `./build`, `make clean` each other's objects and
   relink what is left. The two binaries came out with identical md5 sums.

2. **`BUILD_DIR` does not isolate a build.** `src/main/allvars.h:44` contains
   `#include "./../../build/arepoconfig.h"` with the path hardcoded, so giving
   each Config its own `BUILD_DIR` writes the generated header to the new
   directory while every compilation unit keeps reading the stale
   `./build/arepoconfig.h`. All three binaries were compiled as LDA and their
   `residual_distribution_solver.o` files were byte-identical. This is worse
   than the first failure because it looks like a fix.

`build_case.sbatch` now takes an `flock` so submissions serialise, and the
constraint is documented in the script and in `context.md`. The symptom to watch
for is any scheme comparison in which two schemes agree to more than a few
digits.

Verification that the binaries really differ:
`nm -S | grep compute_residuals` gives 20213 / 20704 / 24513 bytes for
LDA / N / B, B being largest since it carries both branches and the blend.

### A false alarm from my own instrumentation

The first version of `rd_enforce_conservation()` normalised the conservation
defect by the element's own magnitude. For N and B this reported `3.8`-`3.9`
against `1e-14` for LDA, and since the algebraic maximum of that ratio is `4`,
it appeared that the N distribution was maximally non-conservative and that the
rebalance was doing `O(1)` work. I reported that as a probable defect. It was
not one.

Adding the absolute figure and dumping the worst element settled it: the
offending element has every quantity between `1e-18` and `1e-16` while the run's
largest element residual is `3.3e-2`. It is a quiet element in the outer Gresho
region where the exact answer is `phi^T = 0`, and the metric was dividing
round-off by round-off. Absolute defects are `1.4e-17` (LDA), `1.8e-15` (N),
`1.8e-15` (B) against `max|phi^T| = 3.3e-2`.

The hundred-fold gap between LDA and N is real and structural, and worth
keeping in mind: LDA's conservation *is* the residual of the linear solve, so
`phi^T = 0` gives `x = 0` and every `phi_i` exactly zero, whereas N needs the
identity `sum_i K_i^+ = -S^-` to hold to high relative accuracy against `||y||`.
Both remain machine noise.

`RD-DIAG` now reports `cons_defect_abs` with `max_phi` from the same call and
derives the relative figure from those two, which is scale-free without being
fooled by quiet elements. `RD-WORST` triggers on the absolute defect.

Lesson worth generalising: a scale-free diagnostic needs an absolute floor, or
it will scream loudest exactly where the true answer is zero.

### Status

Remaining from earlier entries: long runs to `TimeMax = 3.0` under the final
code. Next is the advected smooth vortex convergence study, now with all three
schemes available and N usable as the control.

## 2026-07-29: independent audit of the Kimi/Claude review and recommendations for the next validation stage

- Author: `gpt-5.6-sol high`
- Review recorded: 2026-07-29 10:22:03 BST (+0100).
- Repository state reviewed: `develop_pureC_RD` at `87877a2`, including
  `53c3fc4`, `07f264a` and `87877a2`.
- Scope: Kimi's review and time-integration analysis; Claude's removal of
  `regularize_matrix()`, new invariant diagnostics and tests; the LDA/N/B
  direct-solve paths; build infrastructure; and the existing Yee generator and
  checker.
- No source code was changed as part of this audit.

### Overall assessment

The current code is a substantially better synchronized static-mesh baseline
than `ebe1be2`. Replacing the fixed diagonal regularisation is mathematically
justified and is necessary before an ALE/moving-mesh formulation. The uniform,
perturbed-uniform, Gresho and MPI-rank tests give strong evidence for algebraic
correctness, exercise of the singular path, conservation to round-off, and
consistent triangle coverage under the enforced equal-timestep configuration.

These tests do **not** establish an accuracy or convergence order. The current
baseline should be accepted for further validation, but not yet described as a
demonstrated second-order unsteady RD method.

Keeping `FORCE_EQUAL_TIMESTEPS` is the right choice for this stage because it
isolates the spatial distribution, predictor and mass/time-defect questions.
Hierarchical active time bins, moving mesh and the MPI ownership redesign should
remain disabled until this synchronized baseline passes an exact-solution
convergence test.

### Findings confirmed

1. **Removal of `regularize_matrix()` is correct.** At mesh-relative
   stagnation, `S^- = sum_i K_i^-` is structurally singular. Adding an absolute
   `1e-10 I` is unit-dependent and breaks `sum_i K_i^+ = -S^-`. A direct solve
   with a singular-capable path is the correct approach.

2. **The rewritten LDA and N algebra is correct.** The row-major `4 x 2` LAPACKE
   right-hand-side layout is consistent with `ldb = nrhs`, and

   ```
   phi_i^LDA = -K_i^+ x,       S^- x = phi^T
   phi_i^N   =  K_i^+(U_i-y),  S^- y = sum_j K_j^- U_j
   ```

   reproduces the standard distributions without forming an explicit inverse
   or the full `BetaLDA` tensor.

3. **The singular-path and MPI tests are meaningful.** The uniform case takes
   the minimum-norm path for every solve and preserves the state to about
   `1e-15`. The pressure-perturbed uniform case is the discriminating variant
   because its momentum residual is non-zero at stagnation. Field differences
   near `1e-14` plus identical element counts are strong evidence that the
   current synchronized ownership rules cover the same elements under the
   tested decompositions.

4. **The signed-area change is useful insurance, not an identified fix for the
   historical termination.** The cross product and orientation assertion are
   preferable to Heron's formula. Claude's later measurement correctly retracts
   the earlier suggestion that Heron cancellation caused the observed failure.

5. **Kimi's `0 / dt` reading is confirmed.** The two half-weight calls are wired
   as a two-stage update. This establishes the predictor/corrector mechanics,
   but not the combined space-time linearity-preserving property of LDA or B.

### Remaining solver concerns

#### LU and DGELSD use inconsistent notions of numerical rank

The LU path is rejected when the ratio of the smallest to largest diagonal
pivot is below `1e-12`, but the fallback calls `DGELSD` with `rcond = -1`, which
uses a machine-precision rank threshold. A matrix rejected as too ill-
conditioned for LU may therefore still be treated as full rank by DGELSD,
retaining its small singular values rather than returning a truncated numerical-
rank solution.

This does not show that the reported results are wrong: exactly stagnant cases
are genuinely rank deficient and the tested branch differences remain at
round-off. It is nevertheless a mismatch between implementation and comments.
Also, partial pivoting does not order diagonal pivots by magnitude, and
`min(abs(diag(U))) / max(abs(diag(U)))` is a heuristic rather than a condition-
number estimate. The gauge-invariance proof in the debug report is specifically
for exact stagnation and should not automatically be extended to every state
selected by a near-singular heuristic.

Before changing `rcond`, perform an element-level sweep over mesh-relative
speeds of roughly `1e-16` to `1e-4`, comparing LU, DGELSD and forced-SVD
residual distributions. The required continuity is that of the final `phi_i`,
not necessarily the intermediate solution vector. Then choose and document one
policy: a stable full-rank SVD solve with a machine threshold, or a scale-aware
numerical-rank truncation used consistently in both tests.

#### Diagnostics should distinguish exact and near singularity

If `dgetrf()` returns non-zero `info`, the code takes the pseudoinverse path
without setting `RD_stat_min_pivot_ratio` to zero. A 100-percent singular case
can consequently report `min_pivot_ratio = 1`. Record zero or add an explicit
`exact_singular` count.

The numerical rank returned by DGELSD is unused. Diagnostics should record the
rank and the residuals `||S^-x-phi^T||` and `||S^-y-b||`, distinguishing an
expected gauge singularity from an unexpected inconsistent least-squares solve.

### Conservation rebalance is mathematically unnecessary

`rd_enforce_conservation()` is not part of the mathematical LDA, N or B scheme.
In exact arithmetic no correction is needed. For LDA,

```
sum_i phi_i^LDA = -S^+ x = S^- x = phi^T.
```

For N,

```
sum_i phi_i^N
  = sum_i K_i^+ U_i - S^+ y
  = sum_i K_i^+ U_i + sum_i K_i^- U_i
  = phi^T.
```

B is a component-wise blend of two distributions whose sums both equal
`phi^T`, so it is conservative as well. At exact stagnation the same result
holds with a Moore-Penrose solution because the right-hand sides are consistent
and the distributed residual is independent of the null-space gauge.

The current rebalance is defensible only as a floating-point projection after
its correction has already been shown to be round-off. Claude's raw defects of
about `1e-15` support that interpretation. Applying it unconditionally is still
risky because it can hide a future error in the solve, `K` matrices, indexing or
MPI path. Assertion A2 is checked after the correction and is therefore nearly
true by construction, not an independent validation of the raw distribution.
Equal splitting also does not make the correction part of RD theory; if it ever
exceeds round-off it can alter dissipation or linearity properties.

Recommended action before convergence testing:

1. Add a controlled switch disabling the correction while retaining raw-defect
   diagnostics.
2. Compare correction-on/off runs for uniform, perturbed-uniform, Gresho
   `v0`/`v1e-8`, and 1/4 MPI ranks.
3. Measure element defects, global mass/momentum/energy drift and snapshot
   differences.
4. If the uncorrected path remains at accumulated round-off, remove the
   rebalance and retain a diagnostic assertion only.
5. If a projection is retained for bit-level local conservation, allow it only
   when the raw defect satisfies a floating-point error bound; otherwise stop
   rather than repair the result.

The bound should be based on pre-cancellation operation magnitudes, e.g.

```
eps_machine * sum |K_i^+| |x|              (LDA)
eps_machine * sum |K_i^+| (|U_i| + |y|)    (N)
```

with an operation-count factor. A fixed absolute tolerance is unit-dependent,
while dividing by a nearly zero element `|phi^T|` repeats the quiet-element
false alarm already documented.

### Yee infrastructure is not ready for convergence measurements

The current `examples/yee_2d/` case is a stationary vortex on a polar,
flow-aligned point set. The generator has an unseeded random ring angle and no
bulk velocity. The checker assumes a stationary centre and can silently produce
invalid results:

- it divides `RotationVelocity_ref` by `Radius` at the central point where
  `Radius = 0`, producing NaN;
- `NaN > tolerance` is false, so this need not fail the test;
- no readable snapshots can still lead to a successful exit;
- finite-value, positivity, global conservation and clean-termination checks
  are absent;
- `sqrt(NumberOfCells)` is not the requested linear resolution of this polar
  point set.

Create a separate deterministic `yee_advected_2d` case rather than overwriting
the historical stationary test. Store resolution, seed, mesh family and boost
in IC metadata. Translate the analytic centre periodically,

```
x_c(t) = (x_c(0) + u_boost * t) mod L,
```

and compare density, internal energy and the full velocity vector using volume-
weighted L1/L2 norms. Reject non-finite values and non-positive density/pressure,
require the expected final snapshot, and record global conserved quantities.

### How to interpret Yee plus boost

Claude is correct that an advected smooth vortex is more sensitive to the
lumped mass/time-defect problem than stationary Yee. A fixed-mesh `dt`
refinement alone measures convergence to the semi-discrete solution and cannot
determine unsteady spatial order.

The boosted vortex nevertheless measures the complete space-time method, not
the mass matrix in isolation. It also contains the spatial distribution,
predictor, mesh alignment and Galilean error. The strongest evidence chain is:

1. stationary Yee retains its expected spatial behaviour;
2. boosted Yee is refined in `h` with actual `dt` proportional to `h`;
3. a separate fixed-mesh boosted temporal refinement confirms the two-stage
   order until the spatial-error plateau.

If stationary LDA remains approximately second order, boosted LDA drops toward
first order, and the independent temporal refinement remains second order, the
combination strongly implicates the lumped mass/time-defect distribution. Kimi's
temporal test is useful as a control, but cannot answer that question alone.

### Recommended work order

1. **P0: remove or strictly guard conservation rebalance**, then run the
   correction-on/off regressions before producing convergence results.
2. **P0: harden upwind-solve diagnostics** and perform the near-stagnation
   velocity sweep before selecting a numerical-rank policy.
3. **P0: build a reproducible advected-Yee harness** using a deterministic
   glass or mildly perturbed unstructured mesh. Avoid an exactly Cartesian
   point set because of cocircular Delaunay degeneracy and directional bias.
4. **P1: run a convergence pilot** with resolutions `32, 64, 128` (then `256`
   if necessary), schemes N/LDA/B, boosts `0` and `1` initially, and a fixed
   CFL under `FORCE_EQUAL_TIMESTEPS`. Record actual dyadic timesteps and step
   counts. Add boost `0.25` after the first result if useful.
5. **P1: run the temporal control** on one sufficiently fine boosted mesh with
   CFL values near `0.4, 0.2, 0.1, 0.05`.
6. **P1/P2: finish long synchronized regressions** to Gresho `TimeMax = 3`, but
   do not interpret them as exact-solution accuracy tests.
7. **P3: only then revisit hierarchical active bins and moving mesh**, whose
   conservative update and MPI responsibility problems would otherwise be
   mixed with unresolved baseline-accuracy questions.

### Build-system note

The `flock` in `build_case.sbatch` is an effective workaround, but
`src/main/allvars.h` still hardcodes `build/arepoconfig.h`. Direct concurrent
`build_case.sh` calls remain unprotected and `BUILD_DIR` remains unsafe. Keep
all convergence builds serialized, then replace the hardcoded generated-header
include with a build-directory-aware include path in a later infrastructure
change.

## 2026-07-29: second independent review — adjudication of the rebalance dispute and the near-stagnation gap

- Author: `Kimi K3`
- Review recorded: 2026-07-29 10:49:51 BST (+0100).
- Repository state reviewed: `develop_pureC_RD` at `87877a2`, comprising
  `ebe1be2` (CodeX baseline), `53c3fc4` (MKL build infrastructure), `07f264a`
  (Claude: direct solve replacing `regularize_matrix()`, invariant checks),
  and `87877a2` (dev_log move).
- Sources reviewed in full: the code diff `ebe1be2..07f264a`;
  `dev_log/regularize_matrix_debug_report.md` (all 720 lines, including the
  two lemmas); the log entries of 2026-07-28 and the three of 2026-07-29;
  the signed-area change in `src/mesh/voronoi/voronoi.c`; and the CodeX audit
  entry of 2026-07-29 10:22.
- No source code was changed as part of this review.

### Verdict on the `regularize_matrix()` removal and the direct solve

The change is mathematically correct and necessary. Independently verified:

- **Lemma 1 (consistency) holds.** At mesh-relative stagnation the flux
  reduces to the pressure terms, so `phi^T = (0, 1/2 sum n_x p_i,
  1/2 sum n_y p_i, 0)`, which lies in
  `range(S^-) = span{(1,0,0,H), (0,1,0,0), (0,0,1,0)}`. The system is
  consistent; only the solution is non-unique.
- **Lemma 2 (gauge invariance) holds.** `null(S^-) = span{(1,0,0,0)}`, the
  isobaric density direction, and at `u = 0` the Euler Jacobian annihilates
  it (`A_x (delta,0,0,0)^T = 0`, since `dp/d rho = -(gamma-1) u^2 / 2 = 0`),
  so `K_i^+ z = 0` and the distributed residuals are independent of the
  gauge. The minimum-norm least-squares solution is a valid choice.
- The implementation matches the thesis formulas: `phi_i^LDA = -K_i^+ x`
  with `S^- x = phi^T` is `beta_i phi^T = -K_i^+ (S^-)^{-1} phi^T`; the N
  branch `Bracket = Uhat_i - y` with `S^- y = sum_j K_j^- Uhat_j` is the
  inflow-state form. The row-major `4 x 2` right-hand-side layout with
  `ldb = nrhs = 2` is correct for both `dgetrs` and `dgelsd`. One
  factorisation serving both right-hand sides also eliminates the explicit
  inverse and the `BetaLDA[4][4][3]` tensor.
- The test campaign is of high quality: the uniform floor test (100 per cent
  of solves on the minimum-norm path, state preserved to `1e-15`), the
  perturbed variant whose error was correctly predicted to appear only in
  the velocity field at exactly `REGULARIZATION_CONSTANT` scale, the
  element-solve-count audit across decompositions (a stronger coverage
  statement than field comparison), and the honest retraction of the Heron
  hypothesis after measurement.

### Adjudication: the conservation rebalance (CodeX position upheld, with a concrete resolution)

Both sides are mathematically right: in exact arithmetic
`rd_enforce_conservation()` is the identity, and the measured pre-correction
defects (`1e-15` to `1e-17` absolute) are genuinely round-off. The
disagreement is engineering policy, and there CodeX's three objections are
decisive:

1. Assertion A2 is evaluated **after** the correction and is therefore true
   by construction. An assertion that cannot fire has no validation value;
   it will not catch a future error in the solve, the `K` matrices, the
   indexing, or the MPI path.
2. An unconditional repair masks exactly the class of bug this code base has
   repeatedly produced. Equal splitting of the defect has no basis in RD
   theory; the remark that it coincides with the centred distribution is
   rhetorically true but mathematically irrelevant, and if the defect ever
   exceeds round-off the split arbitrarily alters the distribution.
3. Claude's own bound — the correction is
   `O(kappa(S^-) * eps_mach * ||phi^T||)` — should be **enforced**, not
   assumed.

Resolution (adopting CodeX's recommendation 5): apply the rebalance **only
when the raw defect satisfies a scale-aware floating-point bound**, e.g.
`eps_mach * sum |K_i^+| |x|` (LDA) or `eps_mach * sum |K_i^+| (|U_i| + |y|)`
(N), times a small operation-count factor; otherwise terminate. Move A2 to
the **raw** distribution. Keep the `RD-DIAG` pre-correction statistics,
which are the honest part of the current implementation. An optional
alternative used elsewhere in the RD literature: compute the distribution at
two vertices and close the third by `phi_3 = phi^T - phi_1 - phi_2`, which
is conservative to round-off by construction at the cost of vertex symmetry;
it can serve as a control implementation.

The user has reviewed both positions and endorses this resolution: the
unconditional rebalance is a redundant step that risks hiding problems.

### The LU/DGELSD rank-criterion mismatch (CodeX finding endorsed, and strengthened)

CodeX is correct that the two paths use inconsistent notions of numerical
rank, and the issue is somewhat sharper than "implementation-comment
mismatch". Both lemmas are proved for **exact** stagnation. Near stagnation
(`u_n` small but non-zero), `S^-` is full rank but ill-conditioned; the
pivot-ratio guard (`1e-12`) rejects the LU, but `dgelsd` with `rcond = -1`
truncates only at machine precision, so it retains the small singular value
and returns a solution with a large near-null-space component. The
annihilation `K_i^+ z = 0` holds only in exact arithmetic; in floating point
the induced error in `phi_i` scales like `eps_mach * ||K|| / u_n`, which at
`u_n ~ 1e-8` is an `O(1e-8)` relative effect — an accuracy problem, not a
cosmetic one. CodeX's proposed element-level sweep over mesh-relative speeds
`1e-16` to `1e-4`, comparing LU / DGELSD / forced-SVD distributions and
requiring continuity of the final `phi_i` (not of the intermediate solution
vector), is the right experiment; one documented policy (stable full-rank
SVD with machine threshold, or a scale-aware truncation used consistently in
both the guard and the fallback) should be chosen from its outcome.

### On Yee+boost: Claude's critique of the Kimi P1 test is accepted

The fixed-mesh `dt`-refinement test proposed in the 2026-07-28 review
measures only the temporal order of the semi-discrete ODE — it converges to
the semi-discrete solution and cannot detect an unsteady spatial-accuracy
degradation from the lumped mass matrix. The cited theory (Ricchiuto &
Abgrall 2010: lumped mass combined with an LP spatial distribution is not LP
and degrades unsteady accuracy to first order; this is what the
total-residual RK-RD formulation repairs) is consistent with the thesis
notes (`m_ij^{LDA} = (|T|/3) beta_i^{LDA}`). The correct evidence chain is
the three-step one from the CodeX audit:

1. stationary Yee spatial convergence as control (LDA should remain ~2);
2. **advected Yee on a glass/random mesh, `h`-refined with `dt` proportional
   to `h` at fixed CFL** — if boosted LDA drops toward first order while N
   stays first order, the lumped-mass/time-defect defect is confirmed, and
   the remedy is known (distribute the time-defect term with
   `m_ij = (|T|/3) beta_i`);
3. the fixed-mesh temporal refinement retained only as a control.

The design constraints from both reviews are endorsed: glass or mildly
perturbed unstructured mesh (no Cartesian point set — cocircular Delaunay
degeneracy and directional bias; no polar flow-aligned mesh), periodically
translated analytic centre, volume-weighted L1/L2 norms, and a checker that
cannot pass on NaN (the current Yee checker divides by `Radius = 0` at the
centre and `NaN > tolerance` is false). Note that the P0 debts from earlier
entries — `check.py` repair and seeding `examples/yee_2d/create.py` — are
still open and are the only thing blocking this decisive experiment.

### Minor endorsements

- Diagnostics: record zero (or an explicit `exact_singular` count) in
  `min_pivot_ratio` when `dgetrf` returns `info != 0`; record the `dgelsd`
  numerical rank and the residuals `||S^-x - phi^T||`, `||S^-y - b||` to
  distinguish an expected gauge singularity from an inconsistent
  least-squares solve.
- The marginal rank-dependence of the pseudo-inverse branch (29821 vs 29820
  in ~4.7M solves) is harmless by Lemma 2, but the `RD_ALWAYS_PSEUDOINVERSE`
  reference path should be run once as a full control to confirm branch
  independence formally.
- `reset_dualarea()` per `compute_residuals()` call is dead work under
  `VORONOI_STATIC_MESH` (two full classifications and extra collectives per
  step); move it to after mesh construction. Correctness is unaffected.
- Boundary-triangle duplicate detection keys on the sorted ID triple only;
  two geometrically distinct periodic images sharing an ID triple would
  silently drop a real element. Include `image_flags` or the centroid offset
  in the key, and add a reconciliation against the global Delaunay triangle
  count — the current element-count audit is per-task and cannot see this
  loss.
- Build hygiene: the `flock` serialisation is a reasonable stopgap, but
  `src/main/allvars.h:44` hardcodes `./../../build/arepoconfig.h`, so
  `BUILD_DIR` isolation silently compiles every configuration against the
  stale header. Any scheme comparison in which two schemes agree to more
  than a few digits should be treated as a build failure until this is fixed
  properly.
- Conservation checks must always be recomputed from snapshots:
  `energy.txt` is written with `%g` (six significant digits).

### Consolidated priorities (this review's adjudication)

- **P0**: conditional (scale-aware, bound-checked) rebalance with A2 moved
  to the raw distribution; `check.py` repair, Yee generator seed, Yee
  checker NaN fix; pivot/rank diagnostics completion.
- **P1**: near-stagnation sweep to fix one rank policy; then build the
  deterministic `yee_advected_2d` case (glass mesh, boost ladder, IC
  metadata for resolution/seed/boost) and run the three-step evidence chain
  with N as control.
- **P2**: if boosted LDA is confirmed to degrade, implement the
  total-residual RK-RD time-defect distribution `m_ij = (|T|/3) beta_i`;
  long Gresho `t = 3` regressions; proper `BUILD_DIR` fix.
- **P3**: only after baseline accuracy is quantified, return to hierarchical
  time bins, the MPI ownership redesign, and the moving-mesh ALE/GCL
  formulation.

## 2026-07-29: review by Codex and Kimi — rebalance to be removed, rank criterion inconsistent

- Recorded by: `Claude Code Opus5`
- Findings by: `Codex` and `Kimi K3`, reviewing commit `07f264a`
- Implementation of the two accepted changes is assigned to `Codex`, since the
  second finding is his.

### Accepted without dispute

Both reviewers accept the removal of `regularize_matrix()` and the replacement
of the explicit inverse by a direct solve, together with the supporting analysis
in `regularize_matrix_debug_report.md`.

### 1. The conservation rebalance is unnecessary and should be removed

Both reviewers judge `rd_enforce_conservation()`'s *correction* to be
unnecessary, and warn that as engineering it can mask defects. I agree, and the
strongest argument is my own measurement.

Section 4.2 of the report justifies the rebalance by showing that the correction
is identically zero in exact arithmetic and `O(kappa * eps * ||phi^T||)` in
floating point. Measured absolute defects are `1.4e-17` (LDA) and `1.8e-15`
(N, B) against `max|phi^T| = 3.3e-2`. **"It never changes anything" is itself the
argument for not having it.**

There is a sharper form of the objection that I had not seen:

> The A2 assertion and the rebalance are redundant, and keeping the rebalance
> weakens the assertion.

A2 exists to catch a broken conservation identity. The rebalance guarantees that
A2 passes after the correction. The measurement is taken before the correction,
so the measurement is doing all the work and the correction contributes only a
surface on which a future defect — a reintroduced regularisation, a dropped
element in the asynchronous work, an indexing error — could be silently absorbed
while the mass-drift check still passes.

Worth stating plainly: this is the same category of error I criticised
`regularize_matrix()` for. A numerical patch applied over a symptom without the
underlying condition being verified. I removed one and installed another in the
same commit, and did not notice.

Agreed replacement:

- delete the correction, keep the measurement;
- promote A2 from a report to a hard assertion, `defect_abs > tol * max|phi^T|`
  terminating the run, with `tol = 1e-10` (measured values are `1e-13`, leaving
  three orders of headroom);
- confirm by a control run that the mass drift is unchanged, which it should be,
  since the correction was of that size.

If conservation later becomes genuinely difficult in the asynchronous or ALE
formulations, the requirement is to *see* the failure, not to pass through it.

### 2. LU and DGELSD apply inconsistent rank criteria (found by Codex)

A real defect. `rd_solve_upwind_system()` uses two thresholds four orders of
magnitude apart:

```
     if(!(ratio >= 1e-12)) use_pseudo_inverse = 1;       LU guard, threshold 1e-12
     LAPACKE_dgelsd(..., singular_values, -1.0, &rank);  rcond = -1 -> cut-off at eps ~ 2.2e-16
```

This creates a band in which the fallback does nothing:

```
     sigma_min/sigma_max  in  ( 2.2e-16 , 1e-12 )

        LU guard : ratio < 1e-12   -> declared rank deficient, handed to dgelsd
        dgelsd   : ratio > 2.2e-16 -> declared full rank, solved normally
        => returns exactly the ill-conditioned solution the guard exists to avoid
```

The fallback is a no-op over precisely the band of matrices it was written for.

Why the tests did not catch it, which is the part worth remembering:

| case | `min_pivot_ratio` | path taken |
| --- | --- | --- |
| Gresho `v1e-8` | `2.8e-11` to `4.3e-10` | above `1e-12`, LU path, `dgelsd` never called |
| Gresho `v0`, uniform | `3.1e-20` | below `2.2e-16`, `dgelsd` truncates correctly |

Both ends of the range are covered and the middle is never touched. **The gap in
test coverage coincides exactly with the location of the defect.** A conditioning
threshold needs a test case straddling it, not only cases far on either side.

Proposed fix, subject to whatever Codex prefers: pass
`rcond = RD_PIVOT_RATIO_TOLERANCE` instead of `-1`, so the pivot ratio only
decides whether to consult `dgelsd` while `dgelsd` makes the authoritative
decision at the same tolerance. A condition estimate via `dgecon` instead of the
pivot-ratio proxy would be a stronger variant. Either way, add a case with
`sigma_min/sigma_max` near `1e-14`; a Gresho background velocity of order
`1e-5` should land in the band.

### 3. Attribution in the advected-vortex study (Codex)

Codex accepts the experiment but notes that a finer analysis is needed before a
loss of order can be attributed to the mass matrix. Agreed. An h-refinement
slope shows *that* the order drops, not *why*, and the confounders are real:
static-mesh advection error growing with `u0`, the gradient predictor differing
from the RD lumped predictor, the location of the B blend, glass meshes at
different resolutions not forming a single mesh family, and limiter activation.

What tightens the attribution, in order of strength:

- **Intervention is the gold standard.** Implement the total-residual form
  `m_ij^{LDA} = (|T|/3) beta_i^{LDA}` and rerun the same ladder. Order recovering
  to 2 establishes the attribution by changing the cause; order not recovering
  refutes it. About thirty lines, since only the distribution of the temporal
  term changes.
- **Read the slope, not the magnitude.** Static-mesh advection error is `O(h^2)`
  for a linearity-preserving scheme, so it moves the error constant; the mass
  matrix moves the slope. This requires at least four resolutions and a check
  that the slope has stabilised.
- **Use N as a control.** N is not LP even for steady problems. If boosting
  leaves N's order unchanged while LDA's degrades, the mechanism is LP-specific,
  which excludes advection error since that affects both schemes alike.
- **`u0 = 0` is the internal control.** The temporal defect vanishes identically
  for a steady solution, so the mass matrix cannot appear. That line must come
  out at 2; if it does not, the test setup is wrong rather than the scheme.

Sequencing: run the observational parts first. If the order is 2 across the
ladder then the lumped mass does not bite at these resolutions, which is itself
a useful result, and the intervention is unnecessary. Only a measured
degradation justifies implementing the total-residual form.

### Assignment

Items 1 and 2 are assigned to Codex. Section 4.2 of
`regularize_matrix_debug_report.md` currently argues *for* the rebalance and
carries a note marking it superseded by this entry; it should be rewritten once
the change is made.

## 2026-07-29: remove conservation rebalance and make the numerical-rank policy consistent

- Author: `gpt-5.6-sol high`
- Change recorded: 2026-07-29 11:41:42 BST (+0100).
- Implements the two items assigned in the preceding review.

### 1. Conservation rebalance removed

`rd_enforce_conservation()` has been replaced by
`rd_check_conservation()`. The new routine never modifies `Flux_RD`,
`Flux_LDA`, or `Flux_N`. The LDA, N and B distributions now enter the cell
update exactly as computed by the scheme.

The raw defect

```
max_k |phi_k^T - sum_i phi_{i,k}|
```

is still recorded in `RD-DIAG`. Under `RD_DEBUG_ASSERTS`, A2 is now evaluated
on the raw distribution and terminates instead of repairing an excessive
defect.

The A2 scale is formed from the absolute matrix-vector products before
cancellation:

```
LDA: |phi^T| + sum |K_i^+| |x|
N:   |phi^T| + sum |K_i^+| (|U_i| + |y|)
```

and B includes both input scales plus the absolute blend operands. The
tolerance is `4096 * DBL_EPSILON * scale`.

The distinction between `|U|+|y|` and `|U-y|` was verified by a useful failed
test. The first implementation scaled N with the already-cancelled bracket.
On a quiet Gresho element, `U-y` was about `1e-15` although it came from
subtracting order-unity states; A2 correctly fired on a `9.39e-17` defect
against an incorrectly tiny `1.22e-27` bound. Using the pre-cancellation scale
fixes the diagnostic without weakening it into a residual correction.

### 2. LU/DGELSD rank thresholds unified

The LU diagonal-pivot ratio remains a cheap trigger at
`RD_PIVOT_RATIO_TOLERANCE = 1e-12`; it is no longer described as a condition
estimate or as ordered pivots. When the trigger fires, DGELSD now receives

```
rcond = RD_PIVOT_RATIO_TOLERANCE
```

instead of `-1`. DGELSD therefore makes the authoritative singular-value rank
decision using the same relative threshold, closing the previous
machine-epsilon-to-`1e-12` gap.

Diagnostics now distinguish:

- the number of SVD fallbacks;
- the number of exactly singular LU factorizations;
- the minimum numerical rank returned by DGELSD;
- the minimum LU pivot ratio.

An exactly singular LU path records a zero pivot ratio rather than leaving the
misleading initial value `1`.

### 3. Build verification

The LDA, N and B Gresho configurations were built sequentially against system
LAPACKE. All three compile and link. Only the pre-existing warnings in AREPO
and the previously noted unused RD variables remain.

Sequential builds were used deliberately because `BUILD_DIR` isolation is
still broken by the hardcoded generated-header include.

### 4. Runtime verification

#### B-scheme Gresho `v0_random48`

This case exercises LDA, N and the blend in one binary and starts with a large
rank-deficient region.

- 1 rank and 4 ranks both reached `t = 0.01` without A2 firing.
- At `t = 0`, 2108/4610 elements used DGELSD and returned rank 3.
- The subsequent run traversed pivot ratios from below machine precision
  through the previously untested `2e-16`--`1e-12` band.
- The largest raw conservation defect in the short run was about `1.2e-13`;
  it remained inside the pre-cancellation forward-error bound and was not
  corrected.
- Snapshot totals on one rank:

  ```
  mass drift      = -4.77e-15
  momentum drift  <  1.5e-16 per component
  energy drift    =  0 at double-precision recomputation
  ```

- Matching the 1-rank and 4-rank final snapshots by particle ID gave maximum
  relative field differences no larger than `2.7e-15`.

#### Uniform static medium, B scheme

A 256-cell uniform run reached `t = 0.005`; every solve used DGELSD at rank 3.
With no conservation correction:

```
mass change             = 0
max density change      = 8.88e-16
max velocity magnitude  = 6.29e-17
max internal-U change   = 0
```

As expected, `cons_defect_abs/max_phi` is meaningless in this case because
both numerator and denominator are numerical zero. The pre-cancellation A2
scale accepts the order-`1e-15` raw defect while leaving the state and
distribution untouched.

### 5. Documentation

`dev_log/regularize_matrix_debug_report.md` section 4 has been rewritten:

- the obsolete rebalance argument is replaced by the implemented raw A2 check;
- the LU trigger and DGELSD rank threshold are documented separately;
- the assertion/diagnostic tables reflect the current code;
- the new one-/four-rank and uniform results are recorded.

### Status

The two accepted changes are implemented and pass the local system-LAPACKE
regressions. A compute-node MKL rerun and longer final-time regressions remain
useful confirmation, but there is no longer a conservation rebalance in the
numerical path and the previously inconsistent rank thresholds are closed.

## 2026-07-29: DGELSD `rcond` sensitivity test revises the rank policy

- Author: `gpt-5.6-sol high`
- Change recorded: 2026-07-29 11:53:15 BST (+0100).
- This entry tests, and supersedes, the preceding entry's provisional choice
  `rcond = 1e-12`.

### 1. Question and controlled comparison

The LU pivot-ratio trigger was held fixed at `1e-12`. Only DGELSD's
singular-value cutoff was varied:

```
rcond = -1       DGELSD machine-precision default
rcond = 1e-14
rcond = 1e-12    provisional production choice
rcond = 1e-10
```

All binaries used the B scheme, a static random-48 Gresho mesh, equal
timesteps, double precision, `RD_DEBUG_ASSERTS`, system LAPACKE, and
`TimeMax = 0.01`. The test added a rank histogram to `RD-DIAG`, so “SVD was
called” and “SVD discarded a direction” can be distinguished directly.

Three background velocities were tested on otherwise identical HDF5 initial
conditions:

- `v0`, which begins with structurally rank-3 elements and later traverses the
  near-singular band;
- `vx += 1e-11`, chosen after measurement to put full-rank systems below the LU
  trigger;
- `vx += 1e-5`, retained as a negative control. Contrary to the earlier
  estimate, its minimum pivot ratio is about `6e-8`, so it never calls DGELSD.

### 2. One-rank results

The following values aggregate 128 residual calls and 590080 element solves in
each run. Rank counts include only the DGELSD fallback calls.

#### Gresho `v0`

| DGELSD `rcond` | rank 3 | rank 4 | max raw A2 defect | mass drift |
| --- | ---: | ---: | ---: | ---: |
| `-1` | 18996 | 15676 | `5.25e-15` | `-1.11e-16` |
| `1e-14` | 25331 | 9341 | `7.87e-15` | `-1.11e-16` |
| `1e-12` | 34672 | 0 | `1.19e-13` | `-4.77e-15` |
| `1e-10` | 34672 | 0 | `1.19e-13` | `-4.77e-15` |

Relative to `rcond = -1`, the `1e-14` final fields agree at approximately
machine precision. With `rcond = 1e-12`, the maximum final differences are:

```
density          1.76e-13
pressure         1.33e-14
internal energy  1.53e-12
velocity         2.00e-15
mass             5.50e-17
```

The `1e-10` run is bitwise-equivalent to the `1e-12` result at the reported
level because all fallback fourth singular values already lie below `1e-12`.

#### Gresho with `vx += 1e-11`

This is the direct test of a resolvable but near-singular fourth direction.
There are 620 DGELSD calls and no exactly singular LU factorization:

| DGELSD `rcond` | rank 3 | rank 4 | max raw A2 defect |
| --- | ---: | ---: | ---: |
| `-1` | 0 | 620 | `1.69e-15` |
| `1e-14` | 0 | 620 | `1.69e-15` |
| `1e-12` | 620 | 0 | `9.72e-14` |
| `1e-10` | 620 | 0 | `9.72e-14` |

Thus `1e-12` does not merely choose a safer solver. It deletes a singular
direction that DGELSD can resolve. The resulting least-squares solution no
longer satisfies the consistent equation `S^- x = rhs` to round-off, and the
raw conservation identity worsens by roughly a factor of 58.

The `vx += 1e-5` control takes the LU path in every element for every binary;
all four final snapshots are identical. This also corrects the earlier
prediction that a boost of order `1e-5` would probe the threshold band.

All runs remain positive. The smallest final density is about `0.993785` and
the smallest pressure about `5.00027`. Total momentum and energy drift remain
at round-off, so this short test exposes a numerical-policy error rather than a
macroscopic instability.

### 3. Four-rank cross-check

The `v0` and `vx += 1e-11` cases were repeated with four MPI ranks for
`rcond = -1` and `1e-12`.

- `v0`: maximum raw defect `6.17e-15` versus `1.19e-13`; maximum final
  internal-energy difference `1.52e-12`.
- `vx += 1e-11`: maximum raw defect `2.23e-15` versus `9.72e-14`; maximum
  final internal-energy difference `7.11e-13`.
- Rank decisions reproduce the one-rank pattern: the default retains the
  resolvable fourth direction, while `1e-12` truncates every fallback solve.
- No A2 assertion, negative density, negative pressure, or non-finite value was
  observed.

This does not validate the existing MPI triangle-responsibility algorithm; it
only shows that the `rcond` conclusion is not a one-rank artefact.

### 4. Revised numerical policy

The proposed “unified threshold” conflated two different decisions:

```
LU pivot ratio < 1e-12:
    LU is not trusted; use a backward-stable SVD solver

DGELSD rcond:
    decide whether a singular direction is numerically unresolvable
```

The first is a solver-selection heuristic. It need not, and based on these
tests must not, force the second to discard the same direction. The previous
“fallback is a no-op” wording was therefore incorrect: switching from LU to
SVD is already meaningful even when DGELSD reports full rank.

The production policy is now:

- `RD_LU_FALLBACK_PIVOT_RATIO = 1e-12`;
- `RD_SVD_RCOND = -1.0`, DGELSD's machine-precision rank cutoff;
- DGELSD is the sole authoritative numerical-rank decision;
- `RD_SVD_RCOND` remains compile-time overridable for sensitivity studies;
- `RD-DIAG` reports `svd_rcond` and rank counts 0 through 4.

The test override is registered in `defines_extra`. A no-fallback diagnostic
now reports `min_svd_rank = -1` instead of the misleading value 4.

### 5. Remaining validation

This is strong evidence against `rcond = 1e-12`, but it is still a short
B-scheme/static-mesh test. The retained machine-default policy should later be
checked with MKL, long-time Gresho, the planned Yee-plus-boost convergence
ladder, and eventually moving mesh/hierarchical timebins. None of those later
tests justifies knowingly introducing an `O(rcond)` residual into the
consistent element solve now.
