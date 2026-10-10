# Experimental native 3D static N baseline

This is the first AREPO tetrahedral RD integration gate. It supports a periodic
unit cube, one MPI rank, gas only, static full mesh, equal timesteps, and the
N scheme with lumped RK2. `RD_3D_STATIC` is an explicit opt-in; unsupported
combinations are rejected. Moving tetrahedra, connectivity transfer, LDA/B,
hierarchical timesteps and MPI validation are subsequent work.

The spatial kernel uses inward **unit** face normals, face area/3 in K, and
tetra volume/4 in the lumped mass. It includes all five Euler components and
both shear modes. See the [mathematical audit and validation record](../../dev_log/RD_3D_KERNEL_MATHEMATICS_20261010.md).
The existing two-dimensional default Config is unchanged. No lazy or repair
option is enabled in this baseline.

## Reproduce on the configured local Mac

From the repository root, with the documented native toolchain and Python
environment containing NumPy and h5py:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 make check_rd PYTHON=python3
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python3 tests/rd/run_3d_static_gates.py all ../local_runs/rd_3d_static_new
```

Use a **new archive directory** for each campaign. The driver freezes current
tracked and untracked source, then builds separate normal-LU/fallback-SVD and
always-SVD binaries. It records source/binary/config/IC/parameter hashes,
generated headers, linkage, logs, actual timesteps, and numerical comparisons.
It uses the repository's existing local build helpers (including `otool`).
Individual actions are `prepare`, `build`, `run`, and `analyse`; `--select`
takes method names for `build` and case names for `run`/`analyse`. For complete
cross-case checks, use `analyse` without a selection.

The seven cases use gamma=1.4 and a periodic unit cube, with 8³ or 16³ nodes
on a Cartesian grid jittered independently by ±0.12 spacings in each axis
(seed 912+n). They run to t=1/32, with snapshots at 0, 1/64 and 1/32:

- Uniform rest and uniform flow at v=(0.3, -0.2, 0.4).
- Zero initial velocity with a small smooth pressure perturbation, exercising
  the rank-four S-minus solve with a nontrivial residual.
- Smooth density advection on both grids; a smaller cap on 16³ must halve the
  **actual** timestep, even when the RD spectral CFL overrides the larger cap.
- The same 8³ advection with every element forced through SVD, compared by ID.

The driver checks all five global conserved quantities, median-dual coverage,
positive finite states, fixed coordinates, uniform-state preservation and
an initial error-decrease trend. The solver checks both RK stage states before
ordinary primitive recovery can apply a floor. Norms use median-dual volume
weights. The recorded two-grid trend is not a formal convergence result or a
positivity proof. Strong shocks, long integrations and parallel agreement have
not yet been tested for this 3D path.


Static LDA/F1 is now available through `Config_LDA_static.sh`. Reproduce its
one-rank gates with `tests/rd/run_3d_feature_gates.py all ARCHIVE --suite lda`
using the NumPy/h5py Python environment. See
`dev_log/RD_3D_FEATURES_AND_BENCHMARKS_20261010.md` for rank-deficient F1
lumping and exact evidence. MPI/hierarchy extension gates are being added;
these should not be inferred from the one-rank suite.
