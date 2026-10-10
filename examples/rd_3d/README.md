# Experimental static tetrahedral RD

`RD_3D_STATIC` supports periodic gas-only Euler flow on a static full mesh,
with N/lumped RK2 or LDA/F1 RK2, equal steps or the existing experimental
frozen-dU hierarchy. Native double-precision gates cover 1/2/4 MPI ranks.
Moving tetrahedra, reconnection transfer, B, active-only 3D reconstruction
and open-stage checkpoint/restart remain unsupported. Unsupported method
combinations are rejected at compilation. The two-dimensional default Config
is unchanged; no lazy or repair option is enabled by these static configs.

The spatial operator uses inward **unit** face normals, face area/3 in K,
tetra volume/4 in the mass, all five Euler components and both shear modes.
LDA uses full-rank F1 distribution and conservative element-local lumping for
rank-deficient temporal targets. Raw element/stage conservation and positive
stage states are checked before ordinary primitive recovery can apply floors.
See the [kernel mathematics](../../dev_log/RD_3D_KERNEL_MATHEMATICS_20261010.md)
and [feature/benchmark evidence](../../dev_log/RD_3D_FEATURES_AND_BENCHMARKS_20261010.md).

## Configurations and local reproduction

- `Config_N_static.sh`, `Config_LDA_static.sh`: equal steps.
- `Config_N_hierarchical.sh`, `Config_LDA_hierarchical.sh`: natural CFL bins.
- The feature driver generates separate equal-bin, controlled split, natural
  pressure-patch and always-SVD configurations in the frozen archive.

On the configured local Mac, use the native toolchain and a Python environment
containing NumPy, h5py and Matplotlib:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
PY=/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python
make check_rd PYTHON="$PY"
"$PY" tests/rd/run_3d_feature_gates.py all ../local_runs/rd_3d_features_new --suite features
"$PY" tests/rd/run_3d_swift_benchmarks.py all ../local_runs/rd_3d_benchmarks_new
```

Use a **new archive directory** for each campaign. Drivers freeze source and
record separate build directories/binaries, generated headers, source/config/
IC/parameter hashes, linkage, logs, snapshots and actual timesteps. Actions
are `prepare`, `build`, `run`, `analyse`, `all`; the feature driver's `--select`
uses method names for build and case names for run/analyse. Its smaller suites
are `lda`, `mpi`, `natural`. Benchmark `analyse --output NEW_DIRECTORY`
preserves previous analysis products. The benchmark CLI returns status 2
when a case fails, after writing the failure summary and successful profiles.

The final 50 feature gates use 8³/16³ jittered unit cubes (seed 912+n,
±.12 spacings), gamma1.4, t=1/32, median-dual norm weights and full 3D
velocity (.3,-.2,.4). They check five-component conservation, coverage,
positivity, fixed coordinates, uniform preservation, LU/SVD, actual halved
dt, equal-bin degeneration, controlled bins and actual natural mixed bins.
The pressure patch uses p=1+8 exp(-|x-.5|²/.12²), rho1 and an inactive cap.
Two-grid smooth error decreases; this is not an asymptotic-order proof.

## SWIFT benchmark adaptations and limits

The second driver follows SWIFT v2026.04 Sod, Gresho and Sedov physical
families, using a **16³ AREPO jittered unit cube** rather than SWIFT's glass
sampling and resolution. Gamma is 5/3, CFL=.1. Sod uses (rho,p)=(1,1)/(.125,.1)
with a contact at x=.5, t=.08; only the central half is compared with the
analytic solution, before the periodic boundary waves reach it. Gresho is a
stationary cylindrical vortex independent of z, t=.1. Sedov has rho1, p1e-6,
E1 replacing the energy of the nearest 15 nodes; injection is normalized
using measured AREPO median-dual volumes. Refer to the feature report for
pinned official source URLs, precise differences and archived provenance.

Sod and Gresho N/LDA complete these initial tests; N also agrees on 1/2 ranks.
Cold Sedov currently **fails the raw solve-compatibility audit** near the first
two steps, with absolute defects around 1e-33. This is not a passed shock
benchmark or an observed negative-pressure failure. Its diagnostics remain
preserved; no threshold, floor or repair was changed to obtain a pass.
Sod hierarchy in this benchmark stayed equal-bin: genuine mixed-bin evidence
comes from the feature pressure-patch and controlled-bin cases.

Per user instruction, local runs remain small functional checks. Convergence
sequences, long-time stability and MPI scaling belong on COSMA/Cuillin with
the corresponding project environment instructions. The current archive/build
helpers target macOS (including `otool`); adapt their linkage/provenance step
and use the cluster's configured SYSTYPE before Linux campaign builds.
