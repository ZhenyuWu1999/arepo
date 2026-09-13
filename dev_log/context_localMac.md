# AREPO-RD local macOS context

Updated: 2026-09-13

This file records the local Apple Silicon development environment for small
two-dimensional AREPO residual-distribution tests. It supplements `context.md`;
the cluster development logs remain the scientific history of the project.

**Logging convention, confirmed 2026-09-10:** all current work continues in
`RD_DEVELOPMENT_LOG_3_localMac.md`. Keep volume 2 as the historical moving-mesh
record; do not append new local findings there. For the current scientific
status, read the latest volume-3 entries; the setup-era handoff below is historical.

**Current checkout/baseline (2026-09-13, log3 §36):** returned to
`develop_pureC_RD`; selective static contour/Gauss port build source943f7ae.
The experimental branch is preserved at53cb65a. Primary baseline/choice table:
`RD_STATIC_BASELINE_CHAPTER4.md`. Static is the sigma0 fixed-connectivity ALE
limit: Arpaia/Campoli geometry choices coincide and the implemented local
mesh frame is the identity; F1/lumped and P1-U/P1-Z flux choices still differ.
The named equal/hierarchy Gauss3 configs are qualified experimental baselines,
not a claim of problem-free or second-order multirate LDA. Default Config
and thesis are untouched. Details and latest measurements are appended below.

## Scope and data policy

- The immediate goal is to compile AREPO-RD natively and rerun inexpensive 2-D
  tests locally while the Cuillin connection is unreliable.
- Old debug campaigns, repeated snapshots, restart files, build artifacts and
  Slurm logs do not need to be copied. Initial conditions should be regenerated
  locally when practical.
- `/Users/zhenyuwu/Hydro_data_analysis` currently contains the analysis code and
  only a small subset of Enzo data. Empty `Data_*` directories are expected and
  are not evidence of an incomplete local environment.
- Cluster binaries are Linux x86-64 binaries and must not be used on this Mac.
  Every local executable must be rebuilt from source.
- Local results are for smoke tests, regression tests and small 2-D comparisons.
  Large formal campaigns may still be run on the cluster when it is available.

## Local path map

| Purpose | Local path |
| --- | --- |
| AREPO-RD workspace | `/Users/zhenyuwu/arepo_rd` |
| AREPO-RD Git repository | `/Users/zhenyuwu/arepo_rd/arepo` |
| Hydro analysis and selected data | `/Users/zhenyuwu/Hydro_data_analysis` |
| Development AREPO reference | `/Users/zhenyuwu/arepo-dev` |
| SWIFT reference | `/Users/zhenyuwu/SWIFT` |
| GIZMO reference | `/Users/zhenyuwu/gizmo-tmox` |
| Enzo reference | `/Users/zhenyuwu/enzo-dev` |
| Thesis repository | `/Users/zhenyuwu/Desktop/MyThesis/Zhenyu-PhDThesis` |
| Thesis resources | `/Users/zhenyuwu/Desktop/MyThesis/useful_resources` |

The old cluster roots `/home/zwu/...` are not valid local paths. In particular,
the local Enzo repository is named `enzo-dev`, not `enzo`.

## Source and documentation state

At the time this file was created:

- AREPO-RD branch: `develop_pureC_RD`.
- Commit: `6a92cd671366bfffd6040d33c1b6b6acb66831bf` (`rd: add ALE
  hierarchy and topology diagnostics`, committed 2026-08-29).
- The AREPO-RD working tree was clean and matched
  `origin/develop_pureC_RD`.
- `context.md` and `arepo/dev_log/context.md` are identical.
- Volume 1, `arepo/dev_log/RD_DEVELOPMENT_LOG.md`, is closed and remains the
  archive for the static-mesh phase.
- Volume 2, `arepo/dev_log/RD_DEVELOPMENT_LOG_2.md`, is the moving-mesh log but
  the local copy currently ends at section 73 (2026-08-25).
- Volume 3, `arepo/dev_log/RD_DEVELOPMENT_LOG_3_localMac.md`, records work
  performed on this Mac. Its exact chronological handover from volume 2 will
  be confirmed after the complete Cuillin copy of volume 2 is checked.
- `Aug26_update_bundle/Aug26_update.md` summarises later hierarchy work and
  refers to log sections through section 83. Those sections are not present in
  any currently available local Git ref. Treat the August 26 update as a
  necessary supplementary handoff until sections 74--83 can be recovered from
  Cuillin or another backup.

The setup-era handoff (superseded by current log3 audits) said that one-rank moving-mesh N hierarchy had passed
the existing equal-bin, two-bin, stationary-mesh, known-flip and KH gates for
both the Arpaia and Campoli temporal-mass forms. Arpaia remains the intended
Chapter 4/production form; Campoli is its endpoint-mass sibling and control.
Topology repair remains diagnostic rather than the production default. The
next scientific engineering target is moving-mesh MPI and rank-boundary
conservation, followed by hierarchical LDA/F1 after the N/MPI path is stable.

## Local machine and compiler stack

- Hardware: Apple M4 MacBook Pro, 10 CPU cores, 16 GB memory.
- Architecture: `arm64`.
- Operating system at setup: macOS 26.6.2.
- Apple Clang: 16.0.0.
- GNU Make: 3.81.
- Homebrew prefix: `/opt/homebrew`.
- Python environments are managed separately; do not copy a cluster Conda or
  virtual environment.

Homebrew libraries detected at setup:

| Dependency | Local version/backend |
| --- | --- |
| Open MPI | 5.0.7 |
| HDF5 | 1.14.6, parallel HDF5 enabled |
| GSL | 2.8 |
| GMP | 6.3.0 |
| FFTW | 3.3.10 |
| hwloc | 2.11.2 |
| BLAS/LAPACK/LAPACKE | OpenBLAS 0.3.29 |
| Autoconf | 2.73 |
| Automake | 1.18.1 |
| GNU libtool | 2.6.2 (`glibtool` on macOS) |

OpenBLAS supplies both `/opt/homebrew/opt/openblas/include/lapacke.h` and the
`LAPACKE_dgelsd` symbol required by the RD linear solves. Intel MKL is not the
native backend on Apple Silicon. A combined MPI/HDF5/GSL/FFTW/LAPACKE compile
and link smoke test passed when this file was created.

The local numerical stack differs from the Cuillin formal-build stack:

| Local Mac | Cuillin formal builds |
| --- | --- |
| Apple ARM64 | Linux x86-64 |
| Apple Clang | GCC |
| Open MPI 5 | Open MPI 4.1 |
| HDF5 1.14 | HDF5 1.10 |
| OpenBLAS/LAPACKE | Intel MKL |

Therefore compare conservation, diagnostic counters and error norms using
explicit tolerances. Do not require bitwise equality between local and cluster
binaries, especially on pseudo-inverse/LAPACK paths.

## AREPO machine configuration

`arepo/Makefile.systype` is a local ignored file selecting:

```make
SYSTYPE="LocalMac"
```

The tracked `LocalMac` block in `arepo/Makefile` uses `/opt/homebrew` and links
the RD LAPACKE calls through OpenBLAS. `Darwin` remains the legacy MacPorts
configuration. The former Intel-Homebrew `MacBookPro` block has been replaced
because that machine is no longer used.

On 2026-08-31 a complete direct build with
`examples/yee_2d/Config_RD.sh` succeeded in `build/local-yee-rd`. The output
was a native arm64 Mach-O executable linked to Homebrew Open MPI, parallel
HDF5, GSL, GMP and OpenBLAS. The build emitted existing source warnings and a
harmless duplicate `-lmpi` linker warning, but no missing-header, undefined-
symbol or unresolved-library error.

## Python analysis environment

The default Python installation does not currently contain the numerical
analysis packages. The existing environment
`/Users/zhenyuwu/miniconda3/envs/21cmfast` contains NumPy, SciPy, h5py,
Matplotlib, yt, mpi4py and pytest. It is the selected temporary local baseline.

A dedicated environment is preferable for reproducibility. A minimal local
environment needs NumPy, SciPy, h5py, Matplotlib and pytest. Add yt and Astropy
only for analyses that use them. Record the final package set after the first
validated simulation.

The following algebraic tests passed under the existing `21cmfast`
environment on 2026-08-31:

```text
tests/rd/test_lda_f1_rank_deficiency.py
tests/rd/test_n_frame_covariance.py
tests/rd/test_ale_shear_eigenvalue_floor.py
```

## Local build and run policy

Slurm files (`*.sbatch`) are not used locally. `build_case.sh` and
`run_case.sh` preserve valuable artifact/provenance behaviour, but they still
contain Linux-specific `flock`, `ldd` and GNU `readlink` assumptions. They are
optional for the first local smoke test and should not be used until made
portable.

The laptop can run several independent cases concurrently without Slurm, but
there is no scheduler to prevent oversubscription or output collisions. Every
Config must have a distinct `BUILD_DIR` and `EXEC`, and every run must have a
distinct working directory and `OutputDir`. Never run concurrent builds in the
same build directory or concurrent simulations in the same output directory.
On this 10-core/16-GB laptop, begin with no more than 6--8 total MPI ranks and
reduce that limit for larger meshes after measuring memory use. Set
both `OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1` for MPI and singleton
runs so that each rank does not create its own pool of BLAS threads.

**Verified 2026-09-11:** the Homebrew OpenBLAS 0.3.29 on this machine reports
`openblas_get_parallel()=2` (OpenMP). `OPENBLAS_NUM_THREADS=1` alone still
reports 10 BLAS threads; adding `OMP_NUM_THREADS=1` reports one. Sampling the
96² Sod run found substantial time in OpenMP barriers inside the tiny
`dgetrs` solves. Preserve both settings in run provenance; the earlier local
campaigns that recorded only the OpenBLAS variable did not enforce one thread.

Routine production and comparison runs should write only 3--5 snapshots in
total, normally including the initial and final states. Increase the output
cadence only for a declared time-evolution diagnostic, instability onset,
failure localization or other analysis that genuinely needs intermediate
states. This keeps local and cluster archives compact and avoids copying
redundant debug data.

For the initial direct build, work inside the AREPO repository and keep build
outputs out of the source tree where possible:

```bash
cd /Users/zhenyuwu/arepo_rd/arepo

make \
  CONFIG=examples/yee_2d/Config_RD.sh \
  BUILD_DIR=build/local-yee-rd \
  EXEC=build/local-yee-rd/Arepo \
  -j4
```

Inspect the executable with:

```bash
file build/local-yee-rd/Arepo
otool -L build/local-yee-rd/Arepo
```

The output must be an arm64 Mach-O binary linked to the `/opt/homebrew`
Open MPI, HDF5, GSL and OpenBLAS libraries. The repository-root `Arepo` and a
stale `build/arepoconfig.h` must not be used as evidence of which Config built
an executable.

## SWIFT and GIZMO Chapter 3 support

The local SWIFT repository has a reproducible Apple-Silicon build entry point:

```bash
cd /Users/zhenyuwu/SWIFT
./build_localmac_2d.sh
```

It creates `build-localmac/swift` and `build-localmac/swift_mpi` as native
arm64 binaries. This is deliberately a 2-D SPHENIX hydro-test build using MPI,
parallel HDF5 and `--disable-vec`; the latter is required because this SWIFT
version's handwritten vector abstraction is not implemented for Apple ARM64.
FFTW, GSL, METIS, NUMA and special allocators are disabled because the current
Gresho comparison is hydro-only. A separate build directory and configuration
must be used if later work needs 3-D or gravity.

The GIZMO repository now provides `SYSTYPE=LocalMac`, using Homebrew libraries
under `/opt/homebrew`. Its existing build wrapper is path-portable and defaults
to the MFV Gresho configuration:

```bash
cd /Users/zhenyuwu/gizmo-tmox
./build_gizmo.sh
```

`Makefile.systype` continues to select `cuillin` by default so the tracked
cluster workflow is not silently changed; `build_gizmo.sh` passes `LocalMac`
explicitly. The Gresho IC generator accepts `--glass` and `--output`, avoiding
the former `/home/zwu` dependency.

Official SWIFT `glassPlane_48.hdf5` and `glassPlane_128.hdf5` files are present
under `SWIFT/examples/HydroTests/GreshoVortex_2D`. They are shared inputs for
the SWIFT and GIZMO Gresho generators.

The current SWIFT release reports that `resolution_eta=1.2348` in its compiled
2-D SPHENIX mode corresponds to approximately 15.14 neighbours, despite the
example YAML comment stating 48. The Cuillin thesis comparison used a much
larger effective-neighbour case. Recover or re-derive the exact dimensionality,
kernel and `resolution_eta` before starting the formal comparison; do not label
the stock local run as the old `N_ngb~400` case.

The checked-in GIZMO MFV Config does not enable `DEVELOPER_MODE`. Consequently
the parameter reader ignores the optional `CourantFac`, `ErrTolIntAccuracy`,
`MaxRMSDisplacementFac` and SPH-only viscosity/conductivity entries in
`gresho48.params`; GIZMO uses its compiled defaults instead. This matches the
current Config/parameter pairing but must be documented or deliberately
changed before the thesis production run.

For direct local execution, run from the directory against which relative IC
and `OutputDir` paths in the parameter file are resolved. Begin with one MPI
rank in a normal Terminal, then repeat with two ranks. MPI launch tests from a
sandboxed agent process may fail because local socket binding is denied; that
does not by itself indicate a broken Open MPI installation.

## Initial local verification sequence

1. Run the three pure-Python RD algebraic tests.
2. Generate a small Yee IC locally rather than copying campaign output.
3. Build and complete a static N smoke test on one rank.
4. Build and complete a static LDA smoke test on one rank.
5. Run the same small case on two ranks and compare by ParticleID.
6. Run moving-mesh equal-step N.
7. Check the equal-bin degeneration of moving hierarchical N.
8. Run the small moving two-bin N gate.

For every binary record the Git commit, Config file, generated
`arepoconfig.h`, compiler version and `otool -L` result. For every run retain
the parameter file, stdout/stderr log and final diagnostic summary. Large
intermediate snapshots and restart files may be deleted after the test has
been accepted.

Minimum acceptance criteria are:

- all three RD algebraic tests pass;
- the executable is native arm64 and has no unresolved dynamic libraries;
- a small 2-D run finishes and writes readable HDF5 output;
- density and pressure remain positive and no element inversion is reported;
- conservation and DGCL diagnostics meet their established gates;
- equal-bin hierarchical execution degenerates to the equal-step result;
- one-rank and two-rank results agree by ParticleID within the established
  cross-platform tolerance.

### First native run, 2026-08-31

A short static N+RK2 Yee test was generated locally at 16 cells per dimension
(259 particles) and evolved to `t=0.02`. The runtime directories are outside
the Git repository:

```text
/Users/zhenyuwu/arepo_rd/local_runs/yee_static_n_smoke
/Users/zhenyuwu/arepo_rd/local_runs/yee_static_n_smoke_np2
```

Both the singleton and 2-rank runs completed, wrote readable HDF5 snapshots and
kept density and pressure positive. The maximum element conservation defect
was approximately `2e-15`. Comparison of the final snapshots after sorting by
ParticleID gave maximum absolute 1-rank/2-rank differences of `2.22e-16` in
velocity, `6.66e-16` in density, `8.88e-16` in pressure and `1.78e-15` in
internal energy. Coordinates and timestep bins were bitwise identical. This
establishes the initial local MPI and rank-invariance smoke gate.

The corresponding static LDA+GL/F1 RK2 case was then run in
`/Users/zhenyuwu/arepo_rd/local_runs/yee_static_lda_rk2_smoke` with the same
IC and end time. It completed on one rank with 259 finite particles; the final
minimum density and pressure were approximately `0.49366` and `0.37220`.
The maximum reported element conservation defect was `4.16e-17` (relative
`4.45e-16`), and `f1_lumped=0` at both steps. This passes the first static
LDA+GL/F1 smoke gate; moving-mesh validation remains deliberately later in the
sequence.

## Known follow-up work

- Recover or reconstruct moving-mesh log sections 74--83.
- Create and freeze a dedicated `arepo-local` Python environment.
- Decide whether to make `build_case.sh` and `run_case.sh` portable. This is
  useful for provenance but is not required to prove that direct local builds
  and small tests work.
- After the N path is stable locally, validate moving MPI before attempting
  hierarchical LDA/F1.

## Sod comparison conventions (user confirmed 2026-09-11)

- Use relaxed **glass IC** as the primary Sod comparison mesh. A jittered
  Cartesian lattice is a separate diagnostic, not a glass.
- Label the initial effective resolution of one shock tube as the main N_x.
  For the current unit-square periodic box, the comparison interval has
  length0.5, so full96² is actualNx48 and full128² is actualNx≈64. On glass use
  h=sqrt(A_box/N_total) and Nx=L_tube/h; there are no literal columns.
- Preserve full-box counts and old directory names as provenance, and state
  both counts in figures. Morton Figure7 uses first-order LDA/N, not GL/F1 RK2.
- See log3 section24 for matched glass controls isolating GL/F1 undershoot and
  contour-residual scatter even with sigma=0 and no flips. Do not attribute
  the previous static/moving difference entirely to movement or repair.

**Current priority (2026-09-12, log3 §§28–29):** pause new CR/basis-repair extensions
and recover the physical baseline first. Keep lumped LDA Heun, standard GL/F1,
and F1 rate-consistent Heun distinct; the latter was not rejected for failing
time order. Separate fixed-h temporal tests, smooth advected spatial tests,
and all-node glass Sod shock quality. See `colombo_re_spike/heun_baseline_history.md`.

The matched 48/96/192 static glass advected-Yee campaign is now complete:
lumped Heun gives density h-orders .902/1.001 despite time p≈2; standard
GL/F1 gives1.879/1.737 with fixed-h time p≈1; F1 rate-Heun gives1.881/1.741
with time p≈2. Halving the spatial-test dt changes density L1 by less than1%
at48/96. Rate-Heun retains the strong glass Sod undershoot (minvx=-.762 versus
-.777 for standard GL/F1). No default was changed, and this is not a proof of
asymptotic order2 on arbitrary glass; the older mass-order note records the
384 glass degradation. Full results: `colombo_re_spike/lda_baseline_convergence.md`.

The moving counterpart is complete (45 native runs, source `11d8abc`):
48/96/192 glass Yee density h-orders are .792/.886 for ALE lumped temporal
RK2, 1.816/1.763 for standard GL/F1, and 1.832/1.777 for a direct ALE
four-pass diagnostic. The last is **not a validated moving rate-Heun**:
its static proof does not transfer through the existing frozen ALE slab.
A derived endpoint defect, independent contour/algebra checks, and no-flip
Campoli controls demonstrate an extra conservation error. Moving Sod at
initial effective Nx≈64 gives relative mass drift 8.59e-5 for this diagnostic
versus 1.19e-9 for standard GL/F1. Do not promote it as a moving alternative.
Lumped Sod is smoother but more diffuse; GL/F1 retains severe vx scatter
(range −.672 to1.352), also with element frame. New frame Sod reproduces
the previous archive exactly. Roe zero-motion and deforming uniform-flow
gates pass; the earlier zero-motion **contour shock** problem remains open.
Main Yee dt halving changes density L1 by <.7%; moving matched-ID time
differences are not formal fixed-grid time orders. Only a protected lumped
diagnostic guard was extended; no default, CR/hierarchy, thesis or log1/log2
change. Full report: `colombo_re_spike/lda_moving_baseline.md`; data and
PNG/PDF figures: `local_runs/lda_moving_baseline_glass_20260911` under the
workspace root. Result/source commits and SHA256 provenance are archived.

**Latest targeted fix (log3 §28):** the user prioritised the large Sod
shock-plateau scatter at x_tube=.7–.8, accepting a static-like negative-vx
trough. Implemented the Gauss-on-P1-U physical-flux quadrature proposed in
log2 §36.4, retaining GL/F1, mesh transport and basis repair. Eleven new
native runs pass. At effective initial Nx≈64, moving plateau vx standard
deviation in [.70,.76] falls from .08256 to .02273 (Gauss3) / .02244 (Gauss5),
versus static Roe .02239; maxvx falls1.3655→1.0510. Density L1 changes
by only+.13%. Zero-motion contour scatter also shrinks substantially.
Moving mass drift remains≈1.5e-9, not the earlier four-pass defect. Yee48/96
density/velocity h-orders are1.874/1.763; no lumped-like order degradation.
Use `RD_ALE_CONTOUR_GAUSS=3` (or5 for integration accuracy control), a
guarded equal-step LDA option; default builds unchanged. This is a promising
physical baseline candidate, not validation for all flows or hierarchy.
Initial Gauss3 artifacts use source559f8a4 and its historical flag name;
Gauss5 usesa4d5a76. Full report: `colombo_re_spike/sod_contour_quadrature.md`.
Archive: workspace `local_runs/sod_contour_gauss3_20260912`.


**Latest KH/cost follow-up (log3 §29):** matched glass48² moving smooth KH
(tanh width .025, historical physical profile) now runs to t=10 with pure
LDA Gauss3 and Gauss5, as does current scalar B; old nodal LDA fails at
t=.444717 with negative mass. Mass/energy drift stays O(2e-8). Late Gauss
morphology, kinetic energy and entropy-proxy excursions differ from B and
between G3/G5; completion is not a long-time accuracy/positivity proof.
All four sharp-interface cases instead stop at the first-step A2 assertion,
before flips. Captured rank3 Sminus cannot represent the full contour Phi:
80-digit least squares and forced SVD confirm a genuine outside-range
residual (1.263e-11,129x A2 tolerance), also present with old nodal contour.
Keep guards intact; conservative spatial null-space completion is a separate
unresolved operator issue. Do not confuse it with the earlier F1 time-mass
problem or describe these sharp failures as late physical KH instability.
Eighteen serial,512-step timings measure G3/G5 CPU overhead about2.9%/4.0%
in early smooth KH (current diagnostic build; not a release/MPI prediction).
Report: `colombo_re_spike/kh_gauss_and_cost.md`; archive under workspace
`local_runs/kh_gauss_20260912`. Main source59b2161, capture source3d6eea9.


**Mathematical clarification and literature (log3 §30):** see
`colombo_re_spike/gauss_p1_ale_math_and_kh_literature.md` for the full ALE/P1
chain and primary-source comparisons. Mean-sigma contour spatial residual
must not be confused with the actual moving-control-volume flux: the latter
has a geometric volume term when related to the former. Gauss integrates
F(U_h) instead of I_hF, fully compatible with P1 but not a positivity proof.
SWIFT/SPHENIX reports highly mixed late KH; AREPO regularization studies also
show that mesh noise can create false secondary structures. Current48² KH
resolves each seeded wavelength with only24 initial spacings. Late disorder
alone neither invalidates nor validates our solution; no new native runs in
this literature/math follow-up.


**Latest old-form control / Chapter4 update (log3 §31):** explicit user
request added Gauss-versus-nodal/split equations to local Chapter4 math draft
(section label ALE_RD_Gauss_physical_flux), with isolated compile/visual QA;
no Overleaf sync or changes to Chapters1–3. Current-source legacy Roe-Uhat/U
split was re-enabled by config only and tested in lab/frame. Both smoothKH
runs fail at t=.800476 (same negative-mass particle), versus nodal.444717
and Gauss3/5 normal completion10. Both sharp controls first-step A2 fail.
Sod succeeds: old split plateau vx std≈.0230, almost Gauss3 .02273, versus
nodal .08256. Hence Gauss is not the only Sod fix; old split remains a useful
control but does not replace Gauss on smoothKH survival. Full report
`colombo_re_spike/legacy_split_kh_sod.md`; archive `local_runs/legacy_split_20260912`.
Eight new native starts, four normal/four diagnosed failures, seven reused
references; no C/default/hierarchy edits. Build sourcee33aea3.


**Legacy+Gauss identity (log3 §32):** Gauss on linear Roe Z already equals the
old physical residual (quadratic flux, Gauss2 exact). Adding the full edge
flux difference F(P1-U)-F(U(P1-Z)) to old split recovers existing Gauss-U,
not a distinct scheme. Include all4 components and consistent frame handling;
current nodal-to-Gauss helper cannot be pasted onto old split.200 random
triangle algebra checks pass≈1e-14; no new native fluid tests or thesis edit.
See `colombo_re_spike/legacy_split_gauss_identity.md`.


**Static Gauss hierarchy/MPI (log3 §33, 2026-09-12–13):** narrow guard
extension permits static full-mesh LDA/F1 contour Gauss3/5 with existing
hierarchy and MPI. Build source255046f;27 native glass uniform/Yee/Sod runs
all pass. Ranks1/2/4 agree by ID to1.36e-14; equal-bin hierarchy degenerates
to internal RK at1.29e-14. Final relative mass/energy drift≤1.45e-16/6.47e-16;
Sod natural CFL hierarchy reaches three bins, completes t=.08, actualNx≈64.
No new Gauss communication fields, limiter or loosened assertions.
Important accuracy qualification: both standard equal-step F1 and mixed-bin
F1 self-converge at fixed-h time order≈1 (equal-step limitation already known).
Frozen mask P changes the leading rate from v+(I-S^-1 M)v to
v+(I-S^-1 M)Pv; measured hierarchy-minus-equal difference plateaus as dt shrinks.
Thus this is a conservative parallel hierarchy baseline, not an equivalent
multirate realization of equal-step F1. Short t=.125 Yee48/96/192 errors fall
but show no stable second-order h convergence; hierarchy velocity error is
larger. Sod negative-vx trough is smaller in these hierarchy controls.
Moving LDA hierarchy/MPI, active-only reconstruction and domain migration
remain outside this validation; existing moving guards remain intact.
Report `colombo_re_spike/static_gauss_hierarchy_mpi.md`; reproducible Config
`examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_HIER.sh`; archive workspace
`local_runs/static_gauss_hierarchy_mpi_20260912`. No thesis/default change.

**Sod coordinate/clock clarification (log3 §34):** plotted xi=2(x-.25)
maps xi=.8 to raw x=.65, outside forced left-half refinement. Hierarchy
still applies globally. In the330 final vertices at xi∈[.78,.82), forced and
natural runs have131/129 reconstructed frozen vertices; their bins20/21 give
2–4 times the equal-run bin19 step. Frozen-F1 therefore acts near the shock
too. Independent periodic-star counts match native diagnostics; no new runs.
The unit-length tube also needs tau=2t, so current t=.08 corresponds to.16.
Morton2023 uses gamma5/3, CFL.4, first-order LDA/N and row-offset Cartesian,
not current gamma1.4/CFL.08/glass/F1. Paper §5.1.1/Fig7 do not specify final
time; tau≈.2 inferred from its wave positions is not an original-data check.
Current rescaling/actualNx is valid but does not make it a Morton reproduction.
Audit/figure under workspace local_runs/sod_coordinates_20260913.

**Moving Euler hierarchy retry (log3 §35, 2026-09-13):** new independent
Python P1/Gauss3/LDA/F1 experiment closes full old vertex stars and uses
actual triangle birth/last-integrated times before same-time basis repair.
Critical addition: a predictor is live only on complete stars whose actual
integration starts agree; equal bins alone fail after event truncation.
Conservative Campoli-endpoint two-stage deposits and zero-sum F1 action
then close Euler extensive conservation through real periodic Delaunay
changes. This is a new candidate, not an enabled native AREPO solver.
22 positive controls pass, three deliberately wrong rules fail (dying-only
geometric coverage; bin-live/all-closed-live conservation7.65e-7/2.47e-6).
Moving glass Sod t=.08, effectiveNx24:384 changed-cavity events, conservation
5.53e-15; moving glass KH t=.5:2092 events,4.44e-15, admissible checked
states. Uniform depth1024 error2.38e-14; seven populated bins1–64 also pass.
All remaps use theta1, i.e. original basis high, not CR low diffusion.
Static two-step native reference agrees2.665e-15; native binary reused from
source255046f, no production C/build/default changes. All failed exploratory
and setup attempts are retained separately. The source/analysis/case runners
are under tests/rd; report `colombo_re_spike/euler_flip_closure.md`, archive
workspace `local_runs/euler_flip_closure_20260913`.
Still missing: actual native triangle history and forced-refresh lifecycle,
changing CFL bins, moving MPI/migration/restart, geometric-step policy,
long-time stability and accuracy convergence. Frozen-F1 leading-operator
problem (§33) remains. Chapter4 static hierarchy/MPI → equal-step moving
extension is still recommended; this candidate can support an ongoing-work
subsection, not a completed moving-hierarchy claim. Thesis untouched.

**Static baseline review (log3 §36, 2026-09-13):** develop_pureC_RD now has
the selected Gauss helper/static LDA contour permissions; no CR, moving
Euler interval-closure or topology-refresh solver code was merged. Historical
log/report continuity was retained; old experimental scripts remain at their
referenced test-branch commits. Initial source484512a failed option registration
before evolution; corrected build source943f7ae passes standard make for5configs.
Two explicit examples/yee_2d configs: Config_RD_RK2_LDA_GAUSS3_EQUAL.sh and
Config_RD_RK2_LDA_GAUSS3_HIER.sh. Default Config unchanged.
26 new native runs all complete:12 replay gates exactly match archived test
branch U by ID;8 static KH (smooth t2, sharp t.05, equal/natural,1/4ranks)
pass, including actual mixed bins;6 Gauss Yee t1 h cases. Max conservation
2.06e-14; max rank-state difference3.96e-14; equal-bin degeneration1.29e-14.
Static sharp KH does not reproduce the moving sharp first-step A2 failure.
Gauss Yee t1 rho slopes equal1.873/1.710, hierarchy1.585/1.658; at192²,
hierarchy rho/velocity errors are2.22/1.75x equal. h/dt refined together;
no strict asymptotic second-order claim. make check_rd passes.
Persistent limits: GL/F1 fixed-h time1; frozen hierarchy changes leading
operator; shock undershoot/no general positivity; mid-stage hierarchy
restart rejected by existing guards; no active-only Gauss/migration/large-rank
or cosmological validation. Qualified Chapter4 experimental baseline only.
Chinese summary/table: RD_STATIC_BASELINE_CHAPTER4.md. Native archive:
workspace local_runs/static_baseline_review_20260913/native; source943f7ae,
tests/rd/review_static_baseline.py and Yee t1 PNG/PDF. Thesis untouched.
