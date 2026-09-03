# AREPO-RD COSMA context

Updated: 2026-09-02

This file records the COSMA environment for compiling and running the public
AREPO residual-distribution branch. It supplements context.md (the original
Cuillin workflow) and context_localMac.md (small native Apple-Silicon tests).
The scientific history remains in the numbered development logs.

## Scope and current status

- COSMA is the current Linux cluster replacement while Cuillin connectivity is
  unreliable. The laptop remains useful for inexpensive local tests.
- The checked-out repository is
  /cosma/home/do020/dc-wu8/arepo_rd/arepo.
- Branch at setup: develop_pureC_RD.
- Commit at setup: c7ba956b10c4db1acefd51679d4f56544e65d45d.
- The COSMA GNU/OpenMPI/parallel-HDF5/MKL build and a static N+RK2 Yee test have
  passed on one and two MPI ranks.
- The validated run directory is
  /cosma/home/do020/dc-wu8/arepo_rd/cosma_runs/yee_static_n_smoke.

The first artifact was built from a dirty tree because it validates the new
COSMA Makefile and wrapper changes themselves. Its immutable bundle includes
source.patch and source_status.txt. After these changes are reviewed and
committed, formal baselines should be rebuilt with --require-clean.

## Login node and scheduler

The interactive host login8a.pri.cosma.local is a login node. Compile AREPO and
run simulations through Slurm, not directly on the login node.

The current allocation uses:

| item | COSMA value |
| --- | --- |
| partition | dine2 |
| account | do020 |
| nodes | gc001--gc008 |
| cores per node | 64 |
| memory per node | approximately 2,060,000 MB |
| partition wall-time limit | 3 days |

Both partition and account must be explicit. Omitting the account causes
sbatch to reject the submission before a job is created.

## Storage quota and data policy

The approximate storage quotas currently available to this account are:

| path | approximate quota | intended use |
| --- | ---: | --- |
| /cosma/home/do020/dc-wu8 | 10 GB | source, scripts, documentation and small test results |
| /cosma/apps/do020/dc-wu8/ | 100 GB | larger builds, campaigns and analysis data |

The home allocation is small, so do not accumulate large snapshot campaigns,
restart files or duplicated build products there. If Hydro_data_analysis
contains large datasets, they may later be moved or archived on the local
MacBook rather than retained on COSMA. Keep source-controlled analysis scripts,
manifests and compact derived diagnostics on COSMA so that the provenance of
any relocated data remains recoverable.

## Pinned compiler and library stack

Load the tracked environment from the repository:

    cd /cosma/home/do020/dc-wu8/arepo_rd/arepo
    source ./cosma_env.sh

The script purges inherited modules and loads this tested stack:

| component | module/version |
| --- | --- |
| COSMA base | cosma/2024 |
| C compiler | gnu_comp/14.1.0 |
| MPI | openmpi/5.0.3 |
| HDF5 | parallel_hdf5/1.14.4 |
| GSL | gsl/2.8 |
| FFTW | fftw/3.3.10 |
| hwloc | hwloc/2.11.1 |
| oneAPI module tree | oneAPI/2024.2.0 |
| oneAPI runtime prerequisites | compiler-rt/2024.2.0, tbb/2021.13 |
| LAPACKE backend | mkl/2024.2 |

The serial hdf5/1.14.4 module is not the selected dependency. Its h5cc reports
Parallel HDF5: no. The selected parallel_hdf5 module supplies h5pcc and reports
Parallel HDF5: yes.

The module order matters. OpenMPI must load after the GNU compiler, and
parallel HDF5 and FFTW must load after both compiler and MPI. COSMA's MKL module
requires compiler-rt and TBB even though AREPO itself is compiled with GCC.

cosma_env.sh also defaults OMP_NUM_THREADS and MKL_NUM_THREADS to one. This
prevents every MPI process from creating its own threaded MKL pool.

## COSMA Makefile target

Makefile has a tracked SYSTYPE="COSMA" branch. The ignored, machine-local
Makefile.systype in this checkout selects:

    SYSTYPE="COSMA"

Do not reuse the Cuillin branch. Cuillin expects libmkl_rt under
MKLROOT/lib/intel64; COSMA oneAPI 2024.2 installs it under MKLROOT/lib. The
COSMA branch also takes parallel HDF5 from HDF5_HOME, which the COSMA module
exports.

The RD source includes lapacke.h. The COSMA branch puts src/mkl_compat first in
the include path so that this maps to MKL's mkl_lapacke.h, and links
libmkl_rt.so with a runtime path.

## Reproducible build workflow

Submit builds from the AREPO repository root:

    cd /cosma/home/do020/dc-wu8/arepo_rd/arepo
    sbatch build_case_cosma.sbatch \
        --config examples/yee_2d/Config_RD_RK2_N_INTERNAL.sh \
        --name cosma-yee-static-n \
        --require-clean

The COSMA wrapper sources cosma_env.sh and then delegates to build_case.sh.
Slurm copies a submitted script into a spool directory, so the wrapper uses
SLURM_SUBMIT_DIR to recover the original repository. Submit it from the
repository root, or export an absolute AREPO_REPO_ROOT before submission.

build_case.sh continues to provide the repository build lock, isolated
temporary BUILD_DIR, immutable artifacts, source/config fingerprints,
checksums, generated arepoconfig.h, compiler wrapper details, build log, ldd
output and manifest.

The first validated artifact is:

    build_artifacts/cosma-yee-static-n/
      c7ba956b10c4-b215f65b888d95a6/Arepo

Its ldd record resolves libmpi, libhdf5, libgsl and libmkl_rt from the selected
COSMA installations, with no missing libraries.

## Run workflow

Run a managed artifact through:

    cd /cosma/home/do020/dc-wu8/arepo_rd/arepo
    sbatch --ntasks=N run_case_cosma.sbatch \
        --binary build_artifacts/NAME/ARTIFACT/Arepo \
        --param /absolute/path/to/param.txt

The wrapper loads the identical module stack and delegates to run_case.sh.
That script checks the binary checksum, resolves the run directory, copies
build and run provenance into the output, and launches mpirun within the Slurm
allocation.

Every run must have a distinct OutputDir. Do not point concurrent ranks or
cases at the same output directory.

## Python for IC generation and inspection

The login-node system Python lacks h5py. COSMA's Python module supplies the
required NumPy and h5py versions:

    module purge
    module load cosma/2024 python/3.12.4

At setup this provided Python 3.12.4, NumPy 2.0.0 and h5py 3.11.0. It was used
to generate and inspect the Yee HDF5 files. A dedicated analysis environment
can be added later if SciPy, Matplotlib, yt or the wider campaign tooling is
needed.

## First validated hydro smoke test

A 16-cell-per-dimension Yee IC generated 262 particles in this checkout. The
static N scheme used RD_RK2_TOTAL_RESIDUAL, FORCE_EQUAL_TIMESTEPS, debug
asserts, double precision and HDF5 output. It ran to t=0.02 with
MaxSizeTimestep=0.01.

Jobs 11914167 (one rank) and 11914168 (two ranks) both completed on gc002 and
wrote initial/final HDF5 snapshots. At the endpoint:

- all inspected density, pressure and internal-energy values were finite;
- minimum density was 0.4992163812;
- minimum pressure was 0.3788707825;
- there were no SVD fallbacks or exactly singular RD elements;
- the maximum reported element conservation defect was 1.615e-15 on one rank
  and 1.687e-15 on two ranks;
- coordinates and hydro time bins were bitwise rank invariant;
- after sorting by ParticleID, maximum one-rank/two-rank differences were
  2.22e-16 in velocity, 4.44e-16 in density, 5.55e-16 in pressure and
  1.78e-15 in internal energy.

This passes the initial COSMA build, HDF5 I/O, positivity, conservation and MPI
rank-invariance smoke gates.

## Next gates

1. Commit/review the COSMA support and rebuild the static N artifact with
   --require-clean.
2. Repeat the small static LDA+GL/F1 gate.
3. Run moving-mesh equal-step N.
4. Check moving hierarchical N in the equal-bin limit.
5. Run the moving two-bin N gate, first on one rank and then across MPI ranks.

Cross-machine comparisons should use explicit tolerances rather than bitwise
identity. COSMA uses Linux x86-64, GCC 14, OpenMPI 5, HDF5 1.14 and MKL 2024.2;
the Mac uses ARM64 Clang/OpenMPI/OpenBLAS, and Cuillin used an older
GCC/OpenMPI/HDF5/MKL stack.
