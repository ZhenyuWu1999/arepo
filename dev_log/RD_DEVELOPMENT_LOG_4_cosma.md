# AREPO Residual Distribution Development Log, volume 4: COSMA

This log records COSMA environment work and validation begun while Cuillin
connectivity is unreliable. It follows the local-Mac work in volume 3 without
replacing the moving-mesh scientific history in volume 2.

- Opened: 2026-09-02.
- Time zone: Europe/London.
- Repository: /cosma/home/do020/dc-wu8/arepo_rd/arepo.
- Branch at opening: develop_pureC_RD.
- Commit at opening: c7ba956b10c4db1acefd51679d4f56544e65d45d.
- Environment reference: dev_log/context_cosma.md.

---

## Index of sections

| # | subject in one line |
| --- | --- |
| 1 | COSMA compiler, MPI, HDF5 and MKL environment |
| 2 | Static N+RK2 Yee build and one/two-rank smoke gate |
| 3 | Chapter-3 fixed-buffer RT reproduction prepared; dine2 outage blocks execution |

---

## 1. COSMA compiler, MPI, HDF5 and MKL environment

**Date:** 2026-09-02

The active login host was login8a.pri.cosma.local. Slurm exposes partition
dine2 to account do020; it contains eight gc nodes with 64 cores and roughly
2 TB memory per node and has a three-day wall-time limit. COSMA requires an
explicit account, so the new batch wrappers specify both --partition=dine2
and --account=do020.

The selected build stack is GNU 14.1.0, OpenMPI 5.0.3, parallel HDF5 1.14.4,
GSL 2.8, FFTW 3.3.10, hwloc 2.11.1 and oneAPI MKL 2024.2. The oneAPI module
tree requires compiler-rt 2024.2.0 and TBB 2021.13 before MKL loads. The serial
hdf5 module was explicitly rejected after h5cc reported Parallel HDF5: no;
parallel_hdf5 supplies an MPI-matched installation and reports yes.

A tracked cosma_env.sh now pins the module order, checks mpicc, HDF5 headers,
MKL's LAPACKE header and libmkl_rt, and defaults MKL/OpenMP threading to one.
Makefile now has a separate COSMA system branch. This separation is necessary:
Cuillin's oneAPI library path ends in lib/intel64, while COSMA's ends in lib.
The COSMA HDF5 path comes from HDF5_HOME.

Two new Slurm entry points, build_case_cosma.sbatch and
run_case_cosma.sbatch, preserve the existing immutable artifact and provenance
workflow. The first submission exposed a Slurm portability detail: BASH_SOURCE
points to Slurm's private spool copy, not to the submitted repository file.
Both wrappers now derive the repository from SLURM_SUBMIT_DIR and must be
submitted from the AREPO root unless AREPO_REPO_ROOT is explicitly set.

The workspace-local ignored Makefile.systype selects SYSTYPE="COSMA".
Template-Makefile.systype documents Cuillin and COSMA as available targets.

---

## 2. Static N+RK2 Yee build and one/two-rank smoke gate

**Date:** 2026-09-02

Build job 11914163 completed on gc002 in five seconds using
examples/yee_2d/Config_RD_RK2_N_INTERNAL.sh. The immutable artifact is:

    build_artifacts/cosma-yee-static-n/
      c7ba956b10c4-b215f65b888d95a6/Arepo

The manifest records GCC 14.1.0 through the OpenMPI 5.0.3 wrapper, parallel
HDF5 1.14.4 and MKLROOT for oneAPI 2024.2. ldd resolves libmpi.so.40,
libhdf5.so.310, libgsl.so.28 and libmkl_rt.so.2, with no unresolved library.
Because the COSMA support itself was an uncommitted source change, the artifact
correctly records source_state=dirty and includes the exact source patch.

The smoke IC was generated with examples/yee_2d/create.py at 16 cells per
dimension and contained 262 particles. The generic Yee parameter file needed
two static-test corrections: CellShapingSpeed and CellMaxAngleFactor are
moving-mesh-only tags and were removed, and MaxSizeTimestep was reduced from
1.0 to 0.01 because the shortened endpoint is t=0.02. The two rejected
parameter attempts ended during AREPO validation before hydrodynamic
integration and are retained in the run provenance.

Job 11914167 completed the corrected case with one MPI rank. Job 11914168
completed the matching case with two ranks. Both reached t=0.02 in two steps,
wrote snap_000.hdf5 and snap_001.hdf5, and exited through MPI_Finalize.

At the endpoint all inspected fields were finite. On one rank the density
range was [0.4992163811854316, 1.0000083952715715], the pressure range was
[0.3788707825003522, 1.0000117725151512], and the internal-energy range was
[1.8973274755161855, 2.5000092796938373]. There were no SVD fallbacks or
exactly singular elements. The final maximum element conservation defect was
1.615e-15 on one rank and 1.687e-15 on two ranks.

Final snapshots were sorted by ParticleID. Coordinates and TimebinHydro were
bitwise identical. Maximum absolute one-rank/two-rank differences were:

| field | maximum absolute difference |
| --- | ---: |
| velocity | 2.220446049250313e-16 |
| density | 4.440892098500626e-16 |
| pressure | 5.551115123125783e-16 |
| internal energy | 1.776356839400251e-15 |
| mass | 2.220446049250313e-16 |
| centre of mass | 3.552713678800501e-15 |

This establishes the first COSMA compile/link, HDF5 I/O, positivity,
conservation and MPI rank-invariance gate. The next environment-level test is
the matching static LDA+GL/F1 smoke case. Moving equal-step and hierarchical N
gates should follow after the COSMA support is reviewed and a clean artifact
is built.

---

## 3. Chapter-3 fixed-buffer RT reproduction prepared; dine2 outage blocks execution

**Date:** 2026-09-03

The recent local-Mac record in volume 3 was reviewed before returning to the
Chapter-3 figures. The Yee result remains the existing convergence-order
figure. The current Gresho result is the matched local n=48 comparison, while
the COSMA work here targets the missing N-versus-LDA Rayleigh--Taylor
morphology.

The retained Cuillin fixed-buffer report was used as the reference rather than
the rejected reflective-wall pilot. The reproduction therefore uses a static
0.5 by 1.5 mesh with 6912 vertices (nominal n=96), gamma=1.4, gy=-0.5, a
logistic rho=1 to 2 transition at y=0.75 with width 0.025, interface pressure
10/7, and the localized perturbation coefficient 0.025 (actual peak vy is
0.09992899687639602). Vertices below y=0.15 and at or above y=1.35 are fixed
reservoirs. This is analogous to SWIFT's fixed boundary-particle strips and the
AREPO wind-tunnel injection region, but the RD implementation rejects both
hydrodynamic RK-stage increments and gravity kicks at every fixed vertex.
Results will be presented only through t=4 because the old Cuillin audit found
material boundary interaction after that time.

The Hydro_data_analysis RT generator was made portable: analysis imports,
data roots, the parameter template and the 48^2 SWIFT glass no longer require
/home/zwu. Defaults are repository-relative and SWIFT_GLASS_48 remains an
explicit override. A self-contained static RT parameter template and a common
colour-scale N/LDA morphology plot were added. A temporary n=48 IC-generation
gate produced 1731 finite states with rho in [1,2] and the expected seed peak.

Matched n=96 campaigns were then prepared in the larger COSMA apps allocation:

- cosma_gizmo_fixed_n96_seed0025_t4_20260903, IC SHA-256
  f82e8c5ba9a6f57fb60ad53a75c72c7a6844d174c321aea7da52ff455c69df27;
- cosma_gizmo_fixed_n96_control_t4_20260903, IC SHA-256
  43331d2c39d6c934fea96fd11c65967228fadca614d1e639a7304dab0b84cfe1.

Their coordinates, masses/density samples, internal energies and particle IDs
are bitwise identical; only the seeded velocity differs, and the seed vanishes
inside both fixed strips. Both contain N and LDA cases, output every 0.5, end at
t=4, and retain the Cuillin maximum step 5/8192. The LDA build uses the current
standard GL+F1 total-residual RK2 formulation, not the older experimental
rate-consistent Heun variant; its generated config SHA-256 is
5185e4e2f1194915536db695ab38472809a5c048b6c1898fe26f5ec347cf6173.

Managed build jobs 11915280 (N) and 11915281 (LDA) were submitted. At submission
all eight gc nodes were idle, but partition dine2 was administratively DOWN;
Slurm therefore left the N build pending with PartitionDown and the dependent
LDA build pending. The COSMA maintenance notice subsequently identified this as
a planned system-wide window beginning Wednesday 2 September at 15:00 British
time. It states that all Slurm partitions are affected, login nodes and storage
remain available, and queued jobs should remain queued. At 05:22 BST on 3
September both jobs were still pending and all 512 dine2 CPU cores were idle.
COSMA exposed no FCFS partition or resolvable fcfs1 host, so no Cuillin-style
FCFS shortcut was assumed and no computation was run on the login node. This
section records preparation only and must not be cited as a hydrodynamic
validation until the jobs run and the short seeded/control gates pass.
