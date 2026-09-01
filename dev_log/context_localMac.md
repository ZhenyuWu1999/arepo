# AREPO-RD local macOS context

Updated: 2026-09-01

This file records the local Apple Silicon development environment for small
two-dimensional AREPO residual-distribution tests. It supplements `context.md`;
the cluster development logs remain the scientific history of the project.

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

The latest local handoff says that one-rank moving-mesh N hierarchy has passed
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
`OPENBLAS_NUM_THREADS=1` for MPI runs so that each rank does not create its own
pool of BLAS threads.

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
