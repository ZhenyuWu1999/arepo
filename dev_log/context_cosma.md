# AREPO-RD COSMA context

Updated: 2026-10-20 (native Blob outcomes audited; no active jobs)

This file records the COSMA environment for compiling and running the public
AREPO residual-distribution branch. It supplements context.md (the original
Cuillin workflow) and context_localMac.md (small native Apple-Silicon tests).
Earlier scientific history remains in the numbered development logs.

## Compact Mac downloads available, 2026-10-20

Two validated download archives are now under `/cosma/home/do020/dc-wu8/arepo_rd/cosma_runs/`:
`blob3d_scripts_20261020_v1.tar.gz` (156.4 KiB; two standalone Python tools
plus small configs/provenance) and `blob3d_mac_analysis_20261020_v1.tar.gz`
(162.2 MiB; tools, original full-run snapshots/IC, failure logs and analysis).
Archive checksum sidecars moved with the downloads; the file hashes are unchanged.
Full native archives and unpacked analysis trees remain in apps storage; no data was transferred to the Mac. The tools need NumPy/h5py,
with Matplotlib optional, and were tested after relocation outside the repo.
See [shared-log entry 16](dev_log_3D_moving_mesh.md#16-2026-10-20-standalone-initializationanalysis-scripts-and-compact-mac-bundles)
and the [package record](RD_3D_BLOB_COSMA_20261019.md#compact-mac-packages-created-2026-10-20).

## Latest Blob execution status, 2026-10-20

All eight preparation-chain jobs completed on gc001 on 2026-10-19. The queue
is empty. Full N equal12187329 and hierarchy12187330 completed to 1.5 t_cr
and passed their per-run analysis (05:10:44 and 02:49:59); normalized snapshot
conservation defects are 8.43e-14/3.68e-14 and actual hierarchy ratio 8.
Full LDA equal12187332 and hierarchy12187333 both failed numerical raw-state
positivity checks at stage 1, ID 14151, near .02142334 t_cr. Short LDA gates
and calibration passed, but neither full LDA run completed; only its initial
snapshot exists. Exact rejected pressures and provenance are in
[shared-log entry 14](dev_log_3D_moving_mesh.md#14-2026-10-20-cosma-execution-audit--n-completes-lda-stops-at-negative-pressure)
and the [campaign report](RD_3D_BLOB_COSMA_20261019.md).

The N-v2 and LDA-v1 apps archives remain authoritative. Their submission
manifests' initial PENDING text is historical; use Slurm accounting, run status
and analysis JSON for actual outcomes. No restart/resubmission or numerical
repair was performed. Existing results do not validate moving 3D, matched N1
reproduction or converged cloud disruption. The preparation handoffs below
retain their writing dates and are superseded as descriptions of job state.

## Blob preparation record, 2026-10-19

**N/LDA update:** the user requires Blob with both schemes. The N campaign
and chain below remain active; separate LDA jobs 12187273 (build),12187274
(gates),12187275 (32³ calibration),12187276 (conditional full submitter)
are now also pending. LDA evidence is
`/cosma/apps/do020/dc-wu8/arepo-rd/rd_3d_blob_20261019_lda_v1/`.
Both schemes target equal and natural-hierarchy 32³ runs to 1.5 t_cr on eight
ranks each, with their own gates/timings/budgets. Exact physical IC arrays
and solver source match between campaigns. See
[shared-log entry 13](dev_log_3D_moving_mesh.md#13-2026-10-19-user-correction--test-blob-with-both-n-and-lda).
No native run has started; keep all four N jobs as well as these four LDA
jobs. The driver supports `--schemes N LDA`, or single-scheme preparation
for independent dependency chains. No numerical success is claimed.


Live inspection on `login5c` confirms dine2/do020 and the documented module
stack/Python are available. All dine2 nodes are under the `ciuk2` reservation
until 09:00 Europe/London today; the scheduler currently estimates a 09:00
start, subject to change. No compute-node compilation or hydro result exists
for the new campaign yet.

[Shared-log entry 12](dev_log_3D_moving_mesh.md#12-2026-10-19-cosma-static-3d-blob-preparation-and-dependent-submissions)
and the [COSMA Blob report](RD_3D_BLOB_COSMA_20261019.md) record the final frozen
campaign at `/cosma/apps/do020/dc-wu8/arepo-rd/rd_3d_blob_20261019_v2/`.
Base source is `35ecccd` on `feature/3d-moving-mesh`; the solver is unchanged.
Pending jobs are 12187116 (build), 12187117 (gates), 12187118 (32³ calibration)
and 12187119 (conditional full submission). Only after successful checks and
a measured wall budget <=3 days will the last stage submit separate 8-rank
32³ N/RK2 equal/hierarchy runs to 1.5 t_cr. Actual long IDs/results will be
in `full_submissions.json` and per-case analysis. Do not resubmit this chain
or interpret its pending state as a validation pass.

The Linux companion `tests/rd/run_3d_blob_cosma.py` and its Slurm wrappers
freeze source, capture `ldd` and use the managed run launcher. The original
Mac helper still calls `otool`; do not use its build action on COSMA. Full
case outputs and analysis are independent, and all OMP/BLAS thread counts are
one. The preceding v1 pending jobs were cancelled before execution; both
archives are retained. The original local handoff below remains historical.

## Current 3D handoff, 2026-10-19

Zhenyu plans to log into COSMA and check resources for the next tests.
[Shared-log entry 11](dev_log_3D_moving_mesh.md#11-2026-10-19-cluster-recommendation-and-cosma-handoff)
contains the current recommendation and validation sequence. The source branch
is `feature/3d-moving-mesh`; inspect the actual fetched revision and preserve
any COSMA working changes before integrating. No live COSMA access, allocation,
module check, build or job submission occurred during this local handoff.

Static 3D N/LDA supports equal steps and the experimental frozen-dU hierarchy,
with small 1/2/4-rank MPI gates. The latest 16³ Blob workflow check also passes
with natural bin ratio 4 on 1/2 ranks. Native moving 3D RD is still pending;
static results do not validate moving geometry, transfer or moving MPI.

Full 32³+ Blob, long stability/resolution studies and MPI scaling should use
cluster compute nodes. Recheck the historical settings below before submitting,
rebuild natively under Slurm, and begin with short feature gates and a 32³ timing
calibration. Use immutable artifacts and separate run/output directories, an
available campaign storage location, and explicit wall time. The historical
run wrapper defaults to 20 minutes and two ranks; override these deliberately.
Never build/run AREPO on the login node or transfer the Mac executable.

The new Blob driver uses the existing macOS campaign build helper, including
`otool -L`; use/adapt the managed COSMA build wrapper and Linux linkage capture.
Its generated Blob configs use gamma5/3, whereas generic 3D configs default to
gamma1.4. Local `../local_runs/` archives and prepared ICs are not Git assets;
regenerate or explicitly transfer inputs with provenance. The source pull alone
does not deliver the already generated 32³ IC or local results.

The older handoffs and environment/setup sections below retain their dates
and do not establish current resource availability. All new 3D execution and
results belong in the shared English log, not a separate COSMA 3D log.

## Shared 3D moving-mesh record, 2026-10-11

Use [dev_log_3D_moving_mesh.md](dev_log_3D_moving_mesh.md) for all subsequent
3D moving-mesh work, including any COSMA adaptation or tests. The same
version-controlled log is used on the Mac, Cuillin and other hosts; this file
continues to describe the COSMA environment. Zhenyu now plans further testing
on Cuillin. Shared-log entry 1 records the local M1/M2 evidence and pending
Linux campaign adaptation; no cluster build, submission or live environment
inspection occurred while opening it. The historical handoffs and setup
evidence below describe their writing dates.

## Historical handoff: return to local experiments, 2026-09-27

Zhenyu has requested that subsequent experiments run on the local Mac; COSMA
is not needed for the next phase. The copied boosted-Yee comparison figures
and summaries are available in the workspace's
`cosma_runs/yee_n_boost10_20260926/comparison_latest/` directory.
See [the local return record](RD_LOCAL_RESUME_COSMA_IMPORT_20260927.md) for
verified file provenance and the source/log integration status. The user has
confirmed that the COSMA work is not yet committed and deferred that merge.
This local handoff does not claim to have checked live COSMA jobs or raw
snapshots, and does not launch, cancel or restart a cluster campaign.

## Historical handoff: boosted Yee LDA, 2026-09-25

The local Mac tests were stopped at the user's request on2026-09-25. Follow
[RD_COSMA_YEE_HANDOFF_20260925.md](RD_COSMA_YEE_HANDOFF_20260925.md) for exact inputs,
portable preparation, compute-node builds, phased gates, run matrix and remaining
analysis/A2 diagnostics. No COSMA jobs have been submitted for this new campaign.
Moving comparisons now use element co-moving variables, while the thesis lab
reference is unchanged. **Current equal-step moving RD requires one MPI rank**;
parallelize independent cases and explicitly override run_case_cosma.sbatch's
historical two-rank default with `--ntasks=1`. General moving MPI and hierarchical
validation are not prerequisites to this one-rank campaign and must not be assumed
from the old setup tests below. Rebuild the new committed source with pinned
modules; never transfer the Mac executable. The remaining sections describe the
Sep2 environment validation and historical setup, not current campaign completion.

## Historical environment and setup status

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

## Historical setup gates

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
