# Static contour–Gauss LDA: hierarchy and MPI validation

2026-09-12–13. User chose to retain contour Gauss and requested, at minimum,
static-mesh hierarchical timesteps with MPI. Branch:
`test/colombo-re-explicit-hierarchy`; native build source `255046f`.

**The static full-mesh extension works as a conservative, MPI-consistent
frozen-star LDA/F1 implementation.** Twenty-seven native runs completed with
all existing assertions enabled. This does not make the hierarchy a second-order
multirate integrator or guarantee the same accuracy as equal-step F1. The
additional fixed-h controls expose a persistent difference in the leading
F1 operator at frozen vertices; this qualification is stronger than merely
saying that the hierarchy has a first-order time error.

## 1. Implemented scope

Only two compile-time restrictions in
`src/hydro/residual_distribution_solver.c` changed. Contour/Gauss now also
permits `VORONOI_STATIC_MESH + CREATE_FULL_MESH + LDA_SCHEME +
RD_RK2_TOTAL_RESIDUAL`, with either existing equal-step or hierarchical
scheduling. The physical quadrature, K matrices, LDA distribution, F1 mass,
predictor, ownership and MPI exchange algorithms are unchanged. No limiter,
positivity repair or relaxed assertion was introduced.

Three- and five-point Gauss both passed mixed-bin one/four-rank Yee tests.
This validated scope is periodic 2-D Euler, laboratory coordinates, static
complete local tessellations including their ghosts. `CREATE_FULL_MESH` does
not mean one MPI rank redundantly solves the whole global domain: physical
triangles have unique owners and remote vertex increments are exchanged.

Active-only mesh reconstruction, forced domain migration, moving LDA hierarchy,
gravity, cosmological integration and 3-D were not tested here. Moving
one-rank restrictions and the moving-hierarchy N-only restriction remain.
The element-comoving-frame option remains excluded from static hierarchy.
All native snapshots verify exactly zero generator velocity and unchanged
coordinates. The default Config was not changed.

## 2. Why Gauss fits the existing static machinery

For outward edge normal n and edge endpoints a,b, define

\[
 U_e(s)=(1-s)U_a+sU_b,\qquad
 C_{Te}=|e|\sum_{q=1}^{n_q}w_qF(U_e(s_q))\cdot n_{Te},\qquad
 \Phi_T=\sum_{e\subset\partial T}C_{Te}.
\]

The code uses inward opposite-vertex normals and assembles an equivalent
nodal contour plus Gauss correction. For static mesh there is no mesh
transport term. Symmetric nodes/weights give opposite contributions when
the two adjacent triangles use the same edge states and reversed normals.
This cancellation holds for the numerical quadrature itself; it does not
require Gauss3 to integrate the nonlinear Euler flux exactly.

LDA distributes this total as `phi_iT = beta_iT Phi_T`, with the existing
conservation/range checks. Crucially, no Gauss point becomes an evolved
unknown, a timebin owner, or an MPI ghost. The already exchanged nodal state
and predictor determine every quadrature value.

### Hierarchical time contract

The existing implementation uses triangle interval `h_T=min_i h_i` and
complete vertex-star interval `h_i^star=min_{T contains i} h_T`. A vertex is
stage-live when `h_i^star=h_i`; otherwise `dU_i=0` for the entire star.
Inactive vertices receive extensive ledger increments, while the residual
continues to consume synchronized primitive states and the allowed predictor.

At an edge separating triangles with unequal intervals, both edge vertices
are frozen relative to the faster adjacent star. Over a common interval with
unchanged bins, their edge trace is constant; repeated fine-edge contributions
therefore sum to the coarse-edge contribution with opposite sign. At equal
triangle intervals the coherent opening/closing traces cancel directly. This
is the relevant time-integrated cancellation; an arbitrary partial event
need not constitute a complete global conservation interval. Bin changes
must retain the existing nested synchronization contract.

For LDA/F1, an element's opening and closing deposits are

\[
 \Delta Q^0_{iT}=-\frac{h_T}{2}\phi_{iT}(U^n),
\]
\[
 \Delta Q^1_{iT}=\frac{A_T}{3}dU_i
 -\frac{A_T}{3}\beta^*_{iT}\sum_jdU_j
 -\frac{h_T}{2}\phi_{iT}(U^*).
\]

Summing i cancels the two F1 temporal terms because `sum_i beta_iT=I`.
The existing rank-deficient temporal fallback instead cancels them locally.
Gauss changes only the spatial total in these expressions. Conservation
therefore still depends on coherent edge histories and complete ledger
deposits, not on a new temporal quadrature at Gauss points.

### MPI contract retained

1. Minimum-ID physical-simplex ownership avoids duplicate residuals.
2. Complete star minima are reduced from the globally owned triangles;
   local ghost copies alone do not determine the star.
3. Primitive, timebin, star-bin and predictor-end metadata reach remote vertices.
4. Extensive residual/predictor deposits reach every vertex owner, including
   inactive vertices. Assemble the complete predictor before the corrector.

Gauss adds local edge-flux evaluations, but no new message field or collective.
These are code-structure statements. The rank tests below validate them on
the exercised decompositions; they are not a large-rank scaling study.

## 3. Native tests and measured results

All ICs are glass. Yee uses the existing boost-one analytic vortex in a
10×10 box; the 48/96/192 sequence is a scaled periodic tiling of the same
glass48 family. Sod uses the previous periodic double tube, gamma=1.4,
16384 vertices in the whole box: **actual single-tube Nx≈64**, not128.

| Gate | Native runs | Result |
|---|---:|---|
| Uniform48, forced 2:1, Gauss3, ranks1/4 | 2 | Preserved to round-off |
| Yee48, equal/internal, equal/hierarchy and forced2:1, ranks1/4 | 6 | Complete; equal-bin degeneration verified |
| Yee48, forced2:1, Gauss3 rank2 | 1 | Matches ranks1/4 |
| Yee48, forced2:1, Gauss5 ranks1/4 | 2 | Complete and rank invariant |
| Yee48, three finer timestep caps, equal and forced2:1 | 6 | Both fixed-h self-orders≈1 |
| Sod, equal / forced refinement / CFL-selected hierarchy, ranks1/4 | 6 | All complete to t=.08 |
| Yee96/192, equal and forced hierarchy, rank4 | 4 | Error decreases; no stable second-order h result in this short-time test |

Yee ends at t=.125; uniform at .03125. All27 runs have normal `bye!` exits,
finite admissible saved states, identical particle IDs, unchanged coordinates,
fixed median-dual areas and zero vertex velocity. Compared rank pairs have
bitwise identical final timebins. All four hydrodynamic conserved quantities
are checked at common final endpoints.

- Largest final relative mass drift: **1.45e−16**; energy: **6.47e−16**.
- Largest final momentum drift normalized by initial mass: **5.79e−15**.
- Maximum normalized four-component drift over all saved snapshots:
  **8.54e−15**. This is not a measurement at every asynchronous half-call.
- Largest 1/2/4-rank difference in `(rho,rho vx,rho vy,E)` by particle ID:
  **1.36e−14**. Forced Yee48 Gauss3 is **3.11e−15**.
- Equal-bin two-call hierarchy versus the internal equal-step RK path:
  **1.29e−14** maximum component difference.

The controlled Yee48 hierarchy has2206 live /98 frozen vertices and alternates
2402/4608 due triangles; both actual bins occur. In Sod, the `hier_two` build
means one additional forced refinement applied to the current CFL candidate,
**not necessarily only two global bins**. It produces three output bins and
maximum star ratio4; the natural CFL run also reaches three bins, with maximum
star ratio2. Frozen counts vary, reaching659/585 respectively.

The first sandboxed MPI launch failed before AREPO because PRTE could not
bind localhost sockets. Its log/status are retained separately. All27 native
starts with local socket access succeed; the launcher failure is not a fluid
failure or a discarded numerical result.

## 4. Accuracy: the F1 mask changes more than the formal time order

Use S for the diagonal lumped nodal area matrix, M(U) for the assembled F1
mass action, R(U) for the spatial nodal residual and
`v(U)=-S^{-1}R(U)`. The earlier baseline audit already established that the
existing standard two-pass equal-step GL/F1 method has leading rate

\[
 G_{eq}=v+(I-S^{-1}M)v=(2I-S^{-1}M)v.
\]

It is not a genuine Heun integration of G; the old fixed-h first-order time
finding therefore applies to the equal-step control too. Here its U-L1
self-orders are0.9990/0.9995; hierarchy gives1.0009/1.0003. Saying that all
of the measured first-order error is newly caused by hierarchy would be wrong.

Let P be the diagonal live-vertex mask (identity blocks at live vertices and
zero blocks at frozen vertices). For a fixed bin pattern and smooth state,
each stage-live vertex has `dU_i/h_T=v_i` in every incident triangle; frozen
vertices have zero. Dividing the summed deposits above by the common elapsed
time gives the hierarchy's leading rate

\[
 G_{hier}=v+(I-S^{-1}M)Pv,
\]
\[
 G_{hier}-G_{eq}=(S^{-1}M-I)(I-P)v.
\]

This is a source-based leading-order derivation for a fixed mask and coherent
interval coverage, not an assertion that naturally changing bins form a
single smooth autonomous operator. Use the existing fallback mass action on
rank-deficient elements. It shows why the difference need not disappear at
fixed spatial resolution when all timesteps shrink. The same mechanism is
present in frozen-F1 with the old spatial residual; Gauss did not create P.

Measured hierarchy-minus-equal U-L1 differences at Yee48, t=.125, with caps
1/256,1/512,1/1024,1/2048 are
`5.02821e−4,5.05659e−4,5.07108e−4,5.07847e−4`.
Both timestep ladders self-converge, but the difference plateaus. Thus
**self-convergence alone cannot certify equivalence to the equal-step F1
spatial/temporal-mass discretization**. Replacing the frozen trace with dense
output would require shared edge histories/composite time integration; it
is not safe to change only `dU=0` into a coarse predictor.

The auxiliary h sequence holds t=.125 and uses caps1/256,1/512,1/1024:

| Method | rho L1 at48/96/192 | observed adjacent h-orders | velocity L1 h-orders |
|---|---|---|---|
| Gauss3 equal | 1.06600e−4 /3.50557e−5 /1.83776e−5 | 1.604 /0.932 | 1.596 /1.233 |
| Gauss3 frozen hierarchy | 1.45050e−4 /5.07426e−5 /2.42762e−5 | 1.515 /1.064 | 1.385 /1.297 |

Errors decrease, but this early-time, three-resolution sequence is not a
second-order spatial validation for either configuration. It uses a different
endpoint from the previous t=1 baseline and does not supersede those results.
Hierarchy has larger smooth-flow error here, especially velocity. No claim
about long-time accuracy or cosmological-scale deep bins follows.

## 5. Sod quality is not degraded in these hierarchy controls

Four-rank results; the matching one-rank results agree to round-off:

| Method | rho L1 | vx L1 | min vx | max vx |
|---|---:|---:|---:|---:|
| Equal Gauss3 F1 | .0157222 | .0391711 | −.72929 | 1.04215 |
| Forced refinement + CFL hierarchy | .0145629 | .0269592 | −.11289 | .98119 |
| Natural CFL hierarchy | .0143734 | .0276688 | −.19525 | 1.06058 |

The negative trough is smaller in these mixed-bin runs, but the frozen mass
action also changes the solution. These comparisons retain identical ICs/CFL
and measure practical behavior, not identical per-element timesteps. The
natural cap1/100 allows the physical CFL to select bins; the other cap is
1/3000. Equal, forced and natural runs take873/1024/887 synchronization events.
No positivity theorem follows from positive rho/p in these examples. The
existing rank-deficient F1 fallback is still enabled and is not a positivity
limiter. All-node scatter is shown, not only bin averages.

## 6. Consequences for moving mesh

The additional Gauss correction is local and introduces no new clock, MPI
state or topology-transfer term. For coherent edge states it retains the
physical-edge cancellation. This makes Gauss itself compatible with a future
moving hierarchical/MPI implementation. It does **not** resolve the remaining
ALE requirements:

- Moving equal-step LDA MPI still needs old/mid/new geometry and nodal divisor
  reductions, remote predictor refresh, and consistent ownership of flip-patch
  corrections. Removing the one-rank guard is insufficient.
- Moving hierarchical LDA/F1 is still absent. Its changing-area temporal mass,
  geometric conservation and extensive endpoint storage must be derived and
  checked together. The previous Arpaia rebase defect remains relevant.
- A flip changes both basis support and incident triangle clocks. Shared local
  interval settlement and topology transfer must cover the same physical time
  exactly once, including across MPI boundaries. More accurate edge integration
  cannot provide that missing coverage identity.

See the earlier [MPI audit](../RD_moving_hierarchy_MPI_audit_20260908.md) and
[topology/clock correction](../RD_topology_hierarchy_conservation_20260909.md).
The most useful next moving gate is Gauss LDA on fixed connectivity with
validated temporal mass and remote geometry, before reintroducing flips.
MPI does not impose a different Euler discretization, but preserving event
ownership and complete geometry/history across ranks is real engineering work.

## 7. Reproduction and artifacts

Archive:
`/Users/zhenyuwu/arepo_rd/local_runs/static_gauss_hierarchy_mpi_20260912`.
It contains27 complete runs, frozen binaries/configs/generated headers/linkage,
IC hashes, full `git archive` of build source255046f, toolchain metadata,
campaign/summary JSON, analysis scripts, figure PNG/PDF pairs and provenance.
Source code remains on the existing test branch. No thesis, default config,
log1 or log2 edits were made.

For a fresh root, use `tests/rd/run_static_gauss_hierarchy_mpi.py` in stages
`prepare ROOT`, `build ROOT`, optionally `spatial ROOT`, and `run ROOT`.
Build requires a clean checkout. The harness resolves the frozen input archives
listed in its source, runs sequentially with1/2/4 ranks, and refuses to overwrite
native logs. Analysis: `tests/rd/analyze_static_gauss_hierarchy_mpi.py ROOT`.
The analysis also compiles/runs no new fluid state: it checks outputs against
independent analytic functions and compares sorted particle IDs.

Set `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1`; plotting uses
`MPLCONFIGDIR=/private/tmp/cr_matplotlib`. Local MPI requires localhost socket
permission. The current actual C Gauss helper was independently compiled and
checked for200 random edge states each for3/5 points: reversed-edge cancellation,
uniform preservation, covariance and agreement with independently evaluated
quadrature all pass. These algebra tests complement, rather than replace,
the native hierarchy/MPI runs.

Figures:

- [Sod, common axis scales](/Users/zhenyuwu/arepo_rd/local_runs/static_gauss_hierarchy_mpi_20260912/figures/sod_static_hierarchy.png)
- [Conservation and fixed-h timestep controls](/Users/zhenyuwu/arepo_rd/local_runs/static_gauss_hierarchy_mpi_20260912/figures/conservation_and_temporal_order.png)
- [Short-time spatial sequence](/Users/zhenyuwu/arepo_rd/local_runs/static_gauss_hierarchy_mpi_20260912/figures/yee_spatial_hierarchy.png)
