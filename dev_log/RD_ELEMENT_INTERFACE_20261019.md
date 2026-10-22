# Shared 2D/3D element interfaces: first native integration

Author: Codex (GPT-6), with Zhenyu Wu, 2026-10-19. Execution host: local Mac.
Baseline: `35ecccd160834e45c921d77d9761d015fc4306d3` on
`feature/3d-moving-mesh`, with the pre-existing documentation edits preserved.
Zhenyu authorized incremental interface consolidation after shared-log entry 19.

## 1. Contract and module boundaries

`src/hydro/rd_element.h` defines borrowed, compact element views. They do not
own arrays or depend on AREPO particle/mesh storage. Dimension is explicit:
`nvert = ndim + 1`, `nvar = ndim + 2`, with ndim equal to 2 or 3.

| View | Layout and meaning |
| --- | --- |
| `rd_element_geometry` | Named element `measure`, inward unit normals `[nvert][ndim]`, and opposite-face measures `[nvert]` |
| `rd_element_input` | Geometry and conserved nodal densities `[nvert][nvar]` |
| `rd_element_output` | Element total `[nvar]`, spatial distribution and optional temporal action `[nvar][nvert]` |
| `rd_element_flux` | Final stage rate `[nvar][nvert]`, consumed by the native ledger after the selected backend completes its corrections |

The public boundary uses component-first residuals, matching the native stage
ledger. The existing pure Euler kernels retain their vertex-first ABI.
`rd_element_roe_residual()` performs the layout conversion and explicitly
selects static P1-Z/Roe N or LDA. It forwards the existing solver policy,
diagnostics and return codes. When no F1 target is supplied, the temporal
output is left untouched. For rank-deficient F1 the kernel's zero action is
preserved; the integrator supplies its existing conservative lumped fallback.
Malformed dimension, measure, scheme or temporal-output contracts are rejected.

This adapter does not change `rd_euler.c`, `rd_linalg.c`, `rd_state.c`,
`rd_timestep.c` or `rd_simplex_geometry.c`. There is no new floor, rescaling,
regularization, contour residual, mass choice or timestep acceptance rule.
`Makefile` links the new module and `defines_extra` registers its include guard.

## 2. Native 2D and 3D connections

Both native dimensions construct the geometry/state view at the element
evaluation boundary. The 2D backend reads the named geometry view in its
existing Roe/Gauss/ALE/B/HLLC paths. Its detailed state/residual arithmetic
remains inline, including frame transforms, contour reconciliation, temporal
mass and blend/positivity policies. The 3D static N/LDA backend calls the new
Roe adapter and receives component-first spatial/F1 arrays.

After either backend assembles the complete stage rate, it emits
`rd_element_flux`. The common `rd_deposit_element()` in
`residual_distribution_solver.c` applies that rate to the local mass,
momenta and energy or appends the corresponding remote primary deposit. It
also assembles live hierarchy predictors using the complete interval.
Fixed-boundary absorption and the explicit zero 2D z-momentum export retain
their existing treatment. No particle/ghost communication is performed by
the pure spatial adapter.

The ledger receives two distinct time quantities: the actual deposit weight
and the complete predictor interval. In the static hierarchy these are h_T/2
and h_T, respectively. Preserving both prevents a layout refactor from silently
halving the predictor or applying the timestep twice. Element ownership,
ghost exchange, reverse addition and `apply_FluxRD_list()` remain with AREPO.

The view hides the legacy `triangle_normals.area` name: its `measure` means
area in static 2D and volume in static 3D. The underlying native storage is
retained for compatibility. On an ALE path the caller still selects the stage
geometry and temporal measure. A positive selected temporal measure is not a
proof of positive signed volume throughout a moving interval.

## 3. Explicit method boundaries

The shared interface does not identify the following choices with one another:

- P1-Z/Roe total residual and Gauss-integrated contour residual;
- N/lumped and mixed-stage LDA/F1, including its singular temporal fallback;
- static geometry and time-dependent geometric conservation;
- equal-step and frozen-predictor hierarchy;
- component-layout equivalence and long-time moving-trajectory compatibility.

Native 3D remains the supported static periodic gas-only N/LDA path. Moving
tetrahedral geometry/transfer, 3D HLLC/B, active-only reconstruction and open
RK-stage restart are not supplied by this change. The 3D spectral CFL remains
its existing dedicated adapter. Further extraction of the legacy 2D numerical
backend can use the same contract, with its own frozen-baseline regression.
It is not a prerequisite for the next controlled moving-3D milestone.

## 4. Verification record

Local archive: `../local_runs/rd_element_interface_20261019_v1/`. It contains
independent frozen before/after source trees, source tarballs/patches and
hashes, per-configuration native build directories, generated headers,
compiler/linkage/binary provenance, copied ICs, parameters, logs and snapshots.
Both `OMP_NUM_THREADS` and `OPENBLAS_NUM_THREADS` are one. The native runner
uses at most two cases concurrently, hence at most eight ranks when both use
four ranks. Builds use four compiler workers.

`tests/rd/test_simplex_kernels.py` retains its independent geometry, flux
quadrature, characteristic and F1 oracles and now checks the adapter's exact
layout correspondence in all 700 triangle/tetra cases. This includes both
gamma values, all-zero/uniform residuals, full-rank and rank-deficient cases,
70 zero-velocity cases, untouched unused temporal outputs and invalid-contract
rejection. The complete `make check_rd` passes.

The initial `candidate_v1` native build stopped at AREPO's macro check because
`RD_ELEMENT_H` was not yet registered in `defines_extra`. It is preserved as a
build-setup failure with no native evolution. `candidate_v2` adds that
registration. A preflight also reduced the shortened HLLC control's maximum
step to fit its requested runtime before those runs were launched; original
preflight parameter files are retained.

The fresh baseline and candidate moving LDA/B Yee48 controls each complete
256 steps to t=1. At all five outputs, every PartType0 dataset is bitwise
identical after ID sorting, including coordinates (55 datasets per method).
This is a comparison with the current pre-refactor source, not a repair of the
separately deferred pre-`dd7a31b` trajectory-compatibility issue.

The complete matrix has now finished: 50 static 3D feature cases and 12 2D
cases on each source, hence 62 before/after pairs and 124 successful native
executions. The 2D cases are moving N/LDA/B Yee48, static N/LDA controlled
hierarchy on two ranks (uniform and Yee), equal-step static Gauss LDA, and
short static/moving HLLC uniform/Sedov controls. The original HLLC uniform
runtime is .001; the hot controls are shortened to .005, with maximum step
.00125 and output spacing .00125. They are compatibility controls, not a new
matched physical benchmark campaign.

An independent audit checks dtype, shape and the actual contiguous bytes of
every ID-sorted PartType0 array, rather than only floating-point equality.
All **200 snapshot pairs and 1726 particle arrays** are byte-identical. All
logged synchronization times/steps and deterministic stage/hierarchy/RK2
diagnostics match. `verification.json` and its `verify_native.py` reproducer
retain the checks, including positive finite saved states and parameter/IC
matching. `two_d_comparison.json`, `three_d_comparison.json` and the native
driver logs retain the per-case comparisons.

The candidate 3D suite also passes its independent physical/assembly gates:

| Property | Maximum defect or observed value |
| --- | ---: |
| Five-component normalized conservation | 2.443e-15 |
| Median-dual box coverage | 1.111e-16 |
| Uniform-state preservation | 6.662e-16 |
| MPI/equal-bin matched-field difference | 8.882e-15 |
| Natural pressure-patch star-bin ratio on 1/2/4 ranks | 2 |

The shortened **moving HLLC Sedov** compatibility control retains the
pre-existing normalized conserved-total drift of **3.095e-3** at .005; the
before/after particle arrays are nevertheless byte-identical. That historical
configuration does not enable `RD_ALE_FLIP_TRANSFER`. The result is a passed
interface regression, not a passed conservative moving-blast validation or a
repair to that older moving geometry path. The other tested 2D saved-total
drifts are at most 4.340e-15. No conservation assertion was relaxed to hide the
control's drift, and no shock/transfer remedy is included in this refactor.

Finally, `source_equivalence.json` confirms that the 2D numerical backend is
text-identical after substituting the geometry-view names, that the extracted
ledger deposit has the same arithmetic tokens as the previous inline body,
and that the five original algebra/state/CFL/geometry modules are unchanged.
The current source matches the frozen candidate for every changed numerical
source/build/test file. These source checks complement the native regressions;
they do not prove compatibility for every untested configuration or compiler.
