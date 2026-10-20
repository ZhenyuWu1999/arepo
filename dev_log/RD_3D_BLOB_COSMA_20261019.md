# COSMA static 3D Blob campaign preparation, 2026-10-19

**Current download location (2026-10-20):** both compact `.tar.gz` files and
checksum sidecars have moved to
`/cosma/home/do020/dc-wu8/arepo_rd/cosma_runs/` at the user's request.
Their filenames, bytes and SHA256 values are unchanged. Native campaigns
and unpacked bundle trees remain in apps storage. Earlier artifact locations
below record creation history, rather than the current archive download path.

**Execution audit, 2026-10-20:** the queue is now empty. Both N full jobs
completed to 1.5 t_cr and passed analysis; both LDA full jobs failed at raw
negative pressure near .02142334 t_cr. All preceding build/gate/calibration
stages passed. See shared-log entry 14 and the appended execution audit.
The pending statuses below are the original preparation record.

**Scope update:** the original N campaign below remains active. The user
subsequently required LDA Blob too; an independent LDA campaign is now queued.
See the appended N/LDA update and shared-log entry 13. The full matrix now
contains N equal/hierarchy and LDA equal/hierarchy.

Codex (GPT-6), with Zhenyu Wu. Preparation host: `login5c.pri.cosma.local`.
Branch: `feature/3d-moving-mesh`; base revision `35ecccd` (full hash in the
campaign provenance). No production solver, default Config or thesis edit.

## Actual status

The final **v2** campaign is prepared and submitted, **not numerically
validated on COSMA yet**. As inspected on 2026-10-19, all four jobs are pending:

| Stage | Slurm job | Requirement | Allocation / limit |
| --- | --- | --- | --- |
| Native N/LDA equal/hierarchy builds | 12187116 | Available compute node | 8 CPUs, 16 GiB, 30 min |
| 22 feature controls + four 16³ Blob gates | 12187117 | Successful build | 8 CPUs, 16 GiB, 30 min |
| Six short 32³ timing/rank cases | 12187118 | Successful native gates and analysis | 8 CPUs, 16 GiB, 30 min |
| Submit the two long cases | 12187119 | Successful calibration and analysis | 1 CPU, 1 GiB, 2 min |

The scheduler initially projects the build at **09:00 Europe/London on
2026-10-19**, after the `ciuk2` reservation ends. This is an estimate, not an
actual start or guaranteed resource availability. `dine2/do020` is available;
all gc001--gc008 CPUs are covered by that reservation despite some appearing
idle. Do not use the other user's reservation or run on the login node.
The next reservation begins on 2026-10-23 at 17:00.

The v1 preparation and jobs 12187098/12187099/12187100 were superseded before
execution to give independent long cases separate analysis files and include
the final dispatcher in the source freeze. Those three jobs were cancelled
by this session while pending. The v1 directory is retained; there is no
numerical failure, build failure or solver result in either archive yet.

## Evidence and portable workflow

Campaign storage (outside the small home quota):

    /cosma/apps/do020/dc-wu8/arepo-rd/rd_3d_blob_20261019_v2/

The approximate per-user home/apps quotas remain the historical 10/100 GB
figures; filesystem-wide free space does not establish a user's remaining
quota. `quota -s` is unsupported on this host; `quota -v` returned no usage
information. The prepared archive is small; larger snapshots stay under apps.

Important files:

- `source.tar`, `base.tar`, `source/`, `working_tree.patch`,
  `source_provenance.json`: exact source and tracked/untracked file hashes.
  Source archive SHA256:
  `a64002b924c6c3166c94e655d61424a8d8d5bda2dad7293b4e74dff16f221afa`.
- `campaign.json`, `configs/`, `inputs/`, `runs/*/param.txt`: scientific
  definitions and IC/parameter hashes. `submissions.json` records the queue
  chain; `preflight.json` records completed preparation checks.
- `artifacts/METHOD/`: isolated native binary, Config, generated header,
  version file, build log/status, binary/config/header checksums, Linux `ldd`,
  compiler wrapper and source-archive provenance, when builds complete.
- `runs/CASE/output/provenance-*/`: managed launcher build/run provenance;
  `run_status.json`, native `arepo-*.log`, snapshots and analysis retain each
  attempt. `gates_results.json` and `calibration_results.json` appear only
  after their assertions pass. Independent full cases write their own
  `runs/CASE/analysis.json`.
- `full_submissions.json`: actual long-job IDs and measured budget decisions,
  created by job 12187119. Its absence before that job executes is expected.

The [driver](../tests/rd/run_3d_blob_cosma.py) reuses the existing IC/state
helpers, freezes source before compilation and builds from that frozen tree
with separate `BUILD_DIR` and executable per configuration. It captures Linux
linkage rather than calling macOS `otool`. The
[Slurm wrapper](../tests/rd/blob_cosma.sbatch) loads `cosma_env.sh` and Python;
AREPO compilation and evolution are guarded to require a Slurm compute node.
It uses the existing managed `run_case.sh` launcher, whose hash is checked
against the frozen copy. The live repository is used only for that launcher
and runner Git status, not for numerical compilation inputs. Frozen-tree
`git_version.sh` may embed `unknown`; the archive hash and base revision in
the artifact manifest identify the source, rather than that banner.

The [long-run submitter](../tests/rd/submit_3d_blob_full_cosma.py) and its
[batch wrapper](../tests/rd/submit_blob_cosma.sbatch) are also archived. After
both prerequisite result files pass, it submits **separate** 8-rank equal-step
and natural-hierarchy cases. For each, wall time is twice the same-method,
same-rank 0.001 t_cr cost extrapolated to 1.5 t_cr, plus 15 minutes, rounded up
to five minutes. An estimate above the partition's three-day limit is recorded
as **not submitted**. A lock and persistent per-case records prevent duplicate
submission. The projection includes initialization and is a budget heuristic;
it does not establish scaling or late-time stability. No long job ID exists yet.

## Verified environment

The module recipe loads successfully on the login host for dependency
inspection: `cosma/2024`, GNU 14.1.0, OpenMPI 5.0.3, parallel HDF5 1.14.4,
GSL 2.8, FFTW 3.3.10, hwloc 2.11.1, oneAPI 2024.2, compiler-rt/TBB and MKL
2024.2. `Makefile.systype` selects COSMA. `h5pcc` reports parallel HDF5 enabled.
Python 3.12.4 provides NumPy 2.0.0 and h5py 3.11.0. All three of
`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS` are explicitly 1.
Compute-node build/linkage validation remains pending, including MKL presence
and absence of unresolved libraries in `ldd`.

## Scientific definition and checks

This follows the physical setup in the
[Mac Blob preparation report](RD_3D_BLOB_PREPARATION_20261018.md): periodic
side-10 cube; random seed 68315; cloud centre (2.5,5,5), radius 1; cloud/wind
rho=100/10; p=100; gamma=5/3; wind vx=6.15, cloud vx=1e-8 and both transverse
speeds 1e-7. Actual Mach=1.5064 and
`t_cr=2 R sqrt(10)/6.15=1.0283829789165462`. Generic 3D configs' gamma1.4 is
explicitly replaced in all campaign configs. N uses the current lumped/RK2
implementation; this does **not** reproduce the paper's predictor-only N1.
Natural hierarchy uses the experimental frozen-dU scheduling, with no forced
bin pattern. No shock remedy, rescaling, floor or assertion relaxation is added.

| Group | Actual mesh / interval | Methods and ranks |
| --- | --- | --- |
| Equal-bin controls | 8³ jittered unit cube, uniform/oblique density advection; end=8*2^-18, cap=2^-18, CFL .2 | N and LDA equal np1; natural hierarchy np1/2/4, required actual bin ratio 1 |
| Natural mixed-bin controls | 8³ jittered unit cube, p=1+8 exp(-|x-.5|²/.12²); end=.03125, cap=1/64, CFL .2 | N/LDA hierarchy np1/2/4, required actual bin ratio >=2 |
| Blob gates | 16³=4096 random nodes, **14 cloud nodes**, end=.01 t_cr, cap=end/4, CFL .01 | N equal np1; N hierarchy np1/2/4 |
| Calibration | 32³=32768 random nodes, **140 cloud nodes**, end=.001 t_cr, cap=end/4, CFL .01 | N equal np1/8; N hierarchy np1/2/4/8 |
| Full, conditional | Same 32³ IC, end=1.5 t_cr, cap=end/4, CFL .01 | N equal np8 and N hierarchy np8; independent runs |

Control energies are regenerated consistently with gamma 5/3. Uniform and
oblique controls exercise all three velocity components (.3,-.2,.4).
The fine-bin cap is deliberately small for equal-bin degeneration; the
pressure patch and Blob cases must demonstrate actual mixed bins.
All cases have unique work and output directories, and are never rerun in
place. Full outputs are requested every .05 t_cr (including .5,1,1.5), while
short groups request initial/mid/final snapshots. Actual saved times and
selected timesteps must be taken from output/logs, not inferred from these
requested values or caps.

Analysis checks fixed coordinates and matched IDs, finite positive saved
rho/p/dual volume, coverage, and the five extensive components using
`Masses/Density` median-dual weights. Total conserved defects must be <1e-12;
near-zero momentum uses total mass as its normalization floor. MPI/equal-bin
comparisons require identical printed stage-1 times and each field difference
`abs(b-a)/max(1,abs(a)) <1e-9`. The unchanged native debug assertions separately
reject inadmissible raw stages. These are separate conservation, positivity,
scheduling and rank checks, not an accuracy-order proof.

Cloud mass selects rho>64 and p/rho<9; divide by its measured initial value.
There is no material tracer. A short 140-node cloud cannot establish physical
breakup, quantitative mixing, convergence or moving-mesh support. The full
runs are intended to provide subsequent cloud-mass histories and common-time
snapshots; plots and physical interpretation await actual output.

## Completed checks and follow-up

Completed: Python/shell syntax, all 34 IC/parameter hashes, source archive,
gamma/timestep flags, and a temporary mock-only dispatch check for budget
calculation, duplicate prevention and over-limit refusal. The latter made no
real `sbatch` call. Native build, hydro gates, timings and long jobs are all
pending. Production source is unchanged, so the algebra suite was not rerun
on the login node.

Inspect actual states with:

    squeue -j 12187116,12187117,12187118,12187119
    sacct -j 12187116,12187117,12187118,12187119 --format=JobID,JobName,State,Elapsed,ExitCode

Read `full_submissions.json` for subsequent long IDs; inspect those jobs too.
If any stage fails, preserve its logs and status. Dependencies are afterok
with invalid-dependency cancellation; no downstream solver run should start.
Append compute hosts, native outcomes, actual bins/timesteps, conservation,
rank differences, timing and any failed attempts to the shared 3D log when
results exist. The queued driver records JSON/log evidence; it does not
silently turn this pending documentation entry into a success claim.

## N/LDA scope update, 2026-10-19

The initial campaign includes LDA warm controls but only N Blob. Following
the user's explicit correction, **both schemes now have Blob coverage**.
The N queue 12187116/12187117/12187118/12187119 remains unchanged.
Independent LDA jobs are:

| Stage | LDA job | Condition |
| --- | --- | --- |
| Build LDA equal/hierarchy | 12187273 | Compute node available |
| Warm controls and 16³ Blob | 12187274 | LDA build succeeds |
| 32³ timing and rank checks | 12187275 | LDA gates and analysis succeed |
| Submit LDA full cases | 12187276 | LDA calibration and analysis succeed |

All remain pending as of this preparation update. Long-job IDs do not exist
yet. N and LDA each target two full 8-rank cases (equal, natural hierarchy),
32³, gamma 5/3, CFL.01 and 1.5 t_cr, with requested .05 t_cr outputs. Each
scheme's wall budget uses its own same-method/rank timing. The shared
three-day guard, failure preservation and thresholds are unchanged.

LDA evidence root:

    /cosma/apps/do020/dc-wu8/arepo-rd/rd_3d_blob_20261019_lda_v1/

The source archive SHA256 is
`7b8c949183ef4ef3c9d9bad00c0f4a572f0489bbc1958f788bbd9d1a105950a9`.
All solver source hashes match N's archive. The 16³ and 32³ HDF5 particle
datasets are exactly equal across schemes. LDA's 23 cases are 11 warm
controls +4 short16³ Blob checks +6 short32³ calibrations +2 conditional
full cases. Cases and final analysis live in separate directories; neither
scheme's success substitutes for the other's.

The driver now exposes `--schemes N LDA` (both by default); explicitly use
`--schemes N` or `--schemes LDA` for independent campaigns, as submitted here
for LDA. The LDA mixed-bin assertion is enabled and all numerical thresholds
are unchanged. Actual LDA stability, positivity, conservation and timings
await native execution. The temporary dispatcher check used fake sbatch
outputs only; actual job IDs are the four Slurm IDs in the table.

## Execution audit, 2026-10-20

Read-only audit on login5c; actual jobs ran on gc001 on 2026-10-19. No jobs
remain queued/running. Source, IC, configs and raw outputs are preserved.
All eight preparation-chain jobs completed successfully. Both roots contain
passing `gates_results.json` and `calibration_results.json`.

| Case | Job | Outcome | Elapsed | Final/failed t/t_cr |
| --- | --- | --- | --- | --- |
| N equal | 12187329 | COMPLETED; analysis passed | 05:10:44 | 1.5 |
| N hierarchy | 12187330 | COMPLETED; analysis passed | 02:49:59 | 1.5 |
| LDA equal | 12187332 | FAILED; raw pressure<0 | 00:06:23 | .02142333984375 |
| LDA hierarchy | 12187333 | FAILED; raw pressure<0 | 00:03:30 | .02142333984375 |

N's31 snapshots per case preserve positivity, fixed coordinates and conserved
extensive content with maximum normalized defects 8.42995e-14 /3.68044e-14.
Actual hierarchy ratio reaches8. Both final HDF5 headers give actual raw
time 1.5425744683748193. The equal step is approximately 1.1768909213e-5;
both report131072 stage-1 records. Final min rho/p are 8.83711955/71.09158543
and 8.83702587/71.08843824. The observed eight-rank elapsed ratio is 1.828 for
this pair. It is not a formal scaling or accuracy/convergence study.

LDA's two failures reject stage 1, ID 14151, at sync1872, raw time
.022031398046857161. Equal's rejected rho/p are 2.74190814416/-5.0089129e-5;
hierarchy's are 2.70647762499/-.03303868561. The direct conserved-state
validator rejects negative pressure and triggers MPI_ABORT. Both have 1871
previous stage-1 records and only the initial snapshot. There is no saved
late-time LDA profile or passing full analysis. This is preserved numerical
failure evidence; the deeper cause and a remedy have not been investigated.

The two N threshold cloud-mass histories reach zero by the first saved time
near 1.05 t_cr. The32³ mesh contains 140 initial cloud nodes and has no material
tracer; these are threshold diagnostics, not converged disruption times.
Requested common output times are rounded to actual synchronization times:
.5/1 become .5000038147/1.0000076294 for equal and .5000610352/1.0001220703
for hierarchy. Compare actual times, not exact nominal timestamps.

For complete source, normalization, timestep and failed-state provenance see
[shared-log entry 14](dev_log_3D_moving_mesh.md#14-2026-10-20-cosma-execution-audit--n-completes-lda-stops-at-negative-pressure).
No new simulations, source edits, assertion changes or resubmissions occurred
in this audit.

## Storage inventory and Mac analysis suitability, 2026-10-20

Read-only inventory on login5c. No transfer, compression, deletion or archive
reorganization was performed. Sizes below sum regular-file logical bytes;
`du -sh` reports approximately 2.3G for N and 547M for LDA, with small filesystem
allocation differences. GiB/MiB here use powers of1024.

Common parent: `/cosma/apps/do020/dc-wu8/arepo-rd/`.

| Archive | File bytes | Logical size |
| --- | --- | --- |
| `rd_3d_blob_20261019_v2` (N full cases and preparation) | 2410306537 | 2.245 GiB |
| `rd_3d_blob_20261019_lda_v1` | 572749293 | 546.216 MiB |
| Combined | 2983055830 | 2.778 GiB |

N full snapshots are under
`runs/full_blob32_N_equal_np8/output/` and
`runs/full_blob32_N_hier_np8/output/` in the N archive, with 31
`snap_*.hdf5` each. Each file is approximately 2.894 MiB and 32768 generators;
the62 full N snapshots total 179.444 MiB. Each failed LDA full case has just
one initial2.894 MiB snapshot; its native failure diagnostics are in the
same case's `output/arepo-*.log`. All snapshots including short gates and
calibrations total 240.319 MiB in N and 64.546 MiB in LDA.

A measured core-analysis selection (both roots' inputs/configs/top-level JSON;
full-case params/status/analysis, snapshots and per-output provenance; plus
LDA full-case native failure logs) totals 198.684 MiB across150 files.
This is a selection size, not a newly created download package. Complete
archives are also small enough for local storage: allow approximately 5–10 GB
free for copies and derived analysis products, depending on plots/caches.
Large non-snapshot components include N's two `cpu.txt` files
(381.598 MiB each), native logs(212.796/303.829 MiB), restart dumps and
source/build archives. Retain original cluster evidence even if selecting a
smaller local download.

The documented Mac is an Apple M4 MacBook Pro with 16 GB RAM. Sequential
analysis of these32768-point HDF5 snapshots is suitable for that machine;
h5py/NumPy and ordinary plotting can read coordinates, density, pressure,
velocity, mass and internal energy directly. Reconstruct median-dual volume
as `Masses/Density` for RD-weighted diagnostics, following the native analysis.
The snapshot `Volume` field is also present, but is not a substitute for that
RD weight. Use actual Header.Time and the recorded t_cr normalization.
The largest files need not be loaded into memory for snapshot plotting.
Local storage/free space and the Mac SSH alias were not inspected from COSMA.
No data has yet been copied to the Mac by this session.

## Compact Mac packages created, 2026-10-20

The user's request to retain only necessary initialization/analysis code is
implemented as new download bundles. Original N/LDA evidence remains intact
in its frozen campaign roots; no original file was deleted or rewritten.
The large originals contain roughly763 MiB of full-N CPU diagnostics,
540 MiB of logs,517 MiB of restart dumps, duplicated source/build material
and all preliminary runs. Full N snapshots themselves are only179.444 MiB.

Two standalone tools now live in `tests/rd/blob_tools/`:

- `make_ic.py`: NumPy/h5py, deterministic Blob ICs, exclusive file creation.
- `analyse.py`: stream snapshots to cloud-mass/conservation CSV and JSON;
  optional Matplotlib PNG/PDF output. Works with a bundle root or a snapshot
  folder, without AREPO/Git/MPI/compiler/SciPy imports.

`export_bundle.py` reproducibly assembles the downloads. Small exact configs,
parameters, native result/status records, source/binary fingerprints and
compressed LDA failure evidence remain with the relevant data. The two entry
point scripts are copied into each bundle's `scripts/` folder.

Artifacts under `/cosma/apps/do020/dc-wu8/arepo-rd/`:

| File | Exact bytes | Contents |
| --- | --- | --- |
| `blob3d_scripts_20261020_v1.tar.gz` | 160123 | Two Python tools, README/requirements, configs and small provenance/status metadata; no HDF5 data |
| `blob3d_mac_analysis_20261020_v1.tar.gz` | 170099139 | Same tools plus all62 N full snapshots, two initial LDA full snapshots, original32³ IC, compressed LDA failure logs, provenance and regenerated CSV/JSON |

These are approximately 156.4 KiB and 162.2 MiB compressed. Unpacked totals are
492689 bytes and 197838239 bytes respectively. Each archive has a neighboring
`.tar.gz.sha256` file. Each extracted tree contains `SHA256SUMS`, inventory
with origin/checksum/size, README and requirements. Original absolute paths
in native parameter/provenance copies identify COSMA inputs; portable analysis
uses bundle-relative snapshot paths. No automatic transfer to the Mac occurred.

Typical use after downloading/extracting the data bundle:

    cd blob3d_mac_analysis_20261020_v1
    python3 scripts/analyse.py . --out analysis_mac --plot
    python3 scripts/make_ic.py blob32_regenerated.hdf5 --n 32
    shasum -a 256 -c SHA256SUMS

Use an existing NumPy/h5py environment; Matplotlib is only needed for --plot.
The scripts-only package can regenerate ICs or analyse a supplied snapshot
directory, but does not itself contain the simulation data.

Validation: regenerated16³/32³ Header attributes and all particle arrays
exactly match archived ICs; overwrite attempts are refused. All N full-run
cloud-history samples, endpoints and normalized conservation results match
native analysis. The two LDA cases retain failed exit status and one initial
snapshot each; checking saved states does not certify the rejected raw stage.
Both compressed archives pass a complete streaming checksum check. The data
archive was extracted to a temporary directory outside the repository and
analysis rerun with identical summary; optional Matplotlib PNG/PDF output was
also exercised successfully. Details are in
[BLOB_PORTABLE_CHECKS_20261020.json](BLOB_PORTABLE_CHECKS_20261020.json).
No solver rebuild or native hydrodynamic rerun was performed.

## Archive relocation and Git publication, 2026-10-20

The user explicitly requested moving both download archives to the existing
`cosma_runs` folder and committing/pushing the Blob-related code and records.
The existing folder is outside this Git repository:

    /cosma/home/do020/dc-wu8/arepo_rd/cosma_runs/

It now contains `blob3d_scripts_20261020_v1.tar.gz` and
`blob3d_mac_analysis_20261020_v1.tar.gz`, plus both `.sha256` sidecars.
Hashes were verified before and after the move; file bytes are unchanged.
The original archive paths in apps no longer contain these four files.
Full native campaigns and unpacked bundle trees were retained in apps.

Git publication targets the actual checked-out `feature/3d-moving-mesh`.
The remote was fetched and matched base 35ecccd before the new commit.
The staged scope is Blob campaign/dispatch wrappers, standalone IC/analysis/
export tools, verification JSON, the campaign report and relevant contexts/
shared log. Download archives, snapshots, native binaries, build products
and restart data stay outside the commit. Source author credit follows the
project's Zhenyu Wu and Codex (GPT-6) convention with a co-author trailer.

Existing scientific validation is retained: short native N/LDA MPI/hierarchy
gates, two completed N full runs, preserved negative-pressure LDA failures,
exact regenerated IC arrays/Headers, portable/native analysis parity and
relocated analysis/plot execution. Publication checks cover script/shell
syntax, documentation links, staged-file scope, whitespace and moved hashes.
No production numerical change, hydrodynamic rerun or new Slurm job is made.
The final commit and push outcome are checked against Git after publication.
