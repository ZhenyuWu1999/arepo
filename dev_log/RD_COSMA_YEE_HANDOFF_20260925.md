# COSMA handoff: boosted Yee moving-mesh LDA, 2026-09-25

Author: Codex, at Zhenyu's request. All local hydro tests were stopped by the
user for migration to COSMA. No COSMA jobs have been submitted by this handoff.
The solver, assertion tolerance and thesis defaults were not changed during
cleanup. Runtime commit `2bde40d` records the same production source used by the recent
Mac campaigns. Local binaries are ARM64 and must not be copied as COSMA executables.

## Decisions to retain

- Current numerical comparison: **moving LDA/F1 with Gauss3 contour and
  RD_ELEMENT_COMOVING_FRAME enabled**. Static controls use the lab frame.
- Keep separate moving lab controls for diagnosis. Never mix lab/co-moving
  points into one convergence curve. The thesis still uses lab as its reference;
  co-moving stays in the optional/red discussion until the mechanism is understood.
- N remains Roe split with the mesh correction in the reference exposition.
  Experimental N/Gauss3 support is retained in code, not made the baseline.
- Standard static LDA/F1 uses mixed stage beta. Common-opening beta is an
  explicitly enabled comparison; do not accidentally enable it for this campaign.
- Global equal timesteps, current Arpaia geometry, regularization unchanged,
  one mesh rebuild per moving step, no topology repair or hierarchical timesteps.
- **Moving equal-step is one MPI rank only.** Parallelize separate cases across
  Slurm jobs. Do not run one moving case with `--ntasks=2` (the generic COSMA run
  wrapper defaults to two ranks, so always override it). Set OMP, MKL and
  OpenBLAS thread counts to1. Element co-moving is unrelated to cosmological
  `ComovingIntegrationOn`, which remains0.

## Local evidence and exactly what stopped

Boost1 four-resolution48/96/192/384, t1, lab-frame campaign completed earlier:
LDA global log-log fitted density/velocity orders are static1.68698/1.77380,
moving1.73576/1.40654. Do not infer a persistent order reduction from the final
adjacent pair; no768 run is requested. Density errors still decreased with h.

The newer matched boost1/10 campaign uses dt caps **1/1024,1/2048,1/4096** for
48/96/192. Earlier boost1 runs used four times larger caps. Completed96 t1 density
L1: static boost1/10=1.7031580e-4/1.8668099e-3; moving lab=
2.9420123e-4/2.9433091e-4. This shows boost sensitivity of static error and nearly
unchanged moving error, not a resolution-independent error floor.

48 moving lab boost10 failed at t=.23730469, stage0, triangle4544:
D=4.8811713134963575e-12, tolerance=2.1550948148822679e-12,
scale=2.3695518079228197. Positive predictors preceded the assertion. No final
error is assigned. Matched48 co-moving passed1024 steps to t1, rho L1=
.0010557291445673761, velocity L1=.0013091227446223796. Gresho boost10 previously
passed in lab, so the mechanism is not established.

The original four192 processes disappeared on Sep24 at23:36, with unknown cause.
They were restarted separately on Sep25. The user subsequently requested stopping
all local runs; both launchd jobs and all six active workers were terminated and
absence of solver processes verified. The two new co-moving uniform/pilot gates
passed, but their full192 runs did not finish. Exact termination records/log hashes:
[YEE_LOCAL_TERMINATION_20260925.json](YEE_LOCAL_TERMINATION_20260925.json).

| Active case at user stop | Last logged step | Last logged t |
|---|---:|---:|
|192 static lab boost1|2893|.706299|
|192 static lab boost10|2886|.704590|
|192 moving lab boost1|843|.205811|
|192 moving lab boost10|679|.165771|
|192 moving co-moving boost1|72|.0175781|
|192 moving co-moving boost10|72|.0175781|

New co-moving boost1 at48/96 and boost10 at96 had not started. These stopped or
queued cases are **not numerical failures and not completed convergence points**.
The old48 co-moving success remains available, but rerun it on COSMA to keep the
new convergence series on one platform. No partial snapshot should replace a t1
snapshot. Raw logs/snapshots remain in local_runs outside Git.

## Inputs and portable preparation

The exact glass48 tiled ICs are required. `examples/yee_2d/create.py` generates a
randomly rotated polar mesh, not these ICs, and is not a substitute. Eight HDF5
files (six Yee + two uniform) total about7.4MB and are intentionally outside Git.
Their file hashes/sizes are tracked in
`examples/yee_2d/boost_comparison/inputs_manifest.json`.

A self-contained transfer directory on the Mac is:

```
/Users/zhenyuwu/arepo_rd/local_runs/cosma_handoff_20260925/yee_inputs/
```

Transfer it using the user's COSMA SSH alias (the following assumes `cosma`):

```bash
rsync -av /Users/zhenyuwu/arepo_rd/local_runs/cosma_handoff_20260925/yee_inputs/ \
  cosma:/cosma/apps/do020/dc-wu8/yee_boost_20260925/inputs/
```

Create that destination parent first if needed. Data/builds should use the larger
apps allocation, not the10GB home quota. On COSMA, review local changes before
pulling `develop_pureC_RD`; use `git pull --ff-only`. Do not reset a dirty checkout.
Then prepare destination-specific paths:

```bash
cd /cosma/home/do020/dc-wu8/arepo_rd/arepo
module purge
module load cosma/2024 python/3.12.4
python3 tests/rd/prepare_yee_boost_cosma.py \
  /cosma/apps/do020/dc-wu8/yee_boost_20260925/campaign \
  --inputs /cosma/apps/do020/dc-wu8/yee_boost_20260925/inputs \
  --include-lab
```

This checks every input hash before creating27 independent case directories:
6 uniform gates,3 short192 pilots and18 science cases (three mesh/frame methods,
two boosts, three resolutions). It does not submit jobs. Omitting `--include-lab`
prepares18 cases for the primary static-lab/moving-co-moving comparison. It refuses
to overwrite an existing campaign. `campaign.json` records config/IC/parameter
hashes, actual n², expected steps, frame and source checkout; `cases.tsv` is the
submission inventory. Preparation was exercised locally and all three active
Config sets matched the tested native binaries. COSMA execution is still pending.

## Build and run on compute nodes

Use [context_cosma.md](context_cosma.md) for pinned GNU/OpenMPI/HDF5/MKL modules.
Build/run only in Slurm compute allocations, with partition dine2/account do020.
For each prepared Config (example below is co-moving):

```bash
export AREPO_ARTIFACT_ROOT=/cosma/apps/do020/dc-wu8/yee_boost_20260925/build_artifacts
sbatch build_case_cosma.sbatch \
  --config /cosma/apps/do020/dc-wu8/yee_boost_20260925/campaign/configs/LDA_moving_comoving.sh \
  --name yee-lda-moving-comoving --require-clean
```

Likewise build LDA_static_lab and optional LDA_moving_lab. Use the exact immutable
artifact directory printed by each completed build, not the repository-root
Arepo. Verify Config.used, generated header, manifest, checksum and ldd/MKL before
running. COSMA MKL and Mac OpenBLAS need not reproduce roundoff bitwise.

Run a selected prepared case with its matching artifact:

```bash
sbatch --ntasks=1 --cpus-per-task=1 --time=04:00:00 \
  --export=ALL,OMP_NUM_THREADS=1,MKL_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1 \
  run_case_cosma.sbatch \
  --binary /absolute/path/to/the/matching/managed/artifact/Arepo \
  --param /absolute/path/to/campaign/runs/CASE/param.txt
```

The walltime is an initial allocation, not a measured runtime prediction. Keep
one rank even for static controls in the main comparison. Start with a few
independent jobs; do not assume more allocated ranks accelerate one moving run.
The existing wrapper preserves source/build/runtime provenance and output logs.

## Work to do, in order

1. **Rebuild and gate all selected configurations on COSMA.** Run uniform
   boost1/10 at48² to t=.03125,32steps. Require finite positive fields and max
   change of rho,p,v <1e-12; retain any failure rather than changing the threshold.
   Then boost10 short192 to t=.0078125,32steps, with positive saved/logged predictors
   and no A1/A2 failure. Inspect actual timesteps, frame flag and mass interpretation.
2. **Complete the primary matched convergence series on one platform:** static
   lab and moving co-moving, boosts1/10,48²/96²/192², t1. Same inputs, gamma1.4,
   beta5,box10,CFL.2, dt caps above. Expect1024/2048/4096 steps. Snapshots0,.5,1.
   No384/768 run yet; start with the requested resolutions.
3. **Keep lab as a distinct diagnostic series.** Prioritize48 boost10 to check
   whether the Mac assertion reproduces under MKL. Complete other lab controls
   only as needed for frame/boost comparisons; do not replace failed lab points
   with successful co-moving values.
4. **Analyze with whole-series fits, not adjacent slopes.** At each actual final
   node use periodic analytic center(5+boost*t,5), density/velocity exact Yee
   fields. Weight by final median-dual area=m/rho, normalized by total area.
   Velocity norm is the Euclidean2-component error. Fit log E=log C+p log(10/Nx)
   to all three successful points and report R². Incomplete series stays incomplete.
   Plot native rho(r) and annular absolute errors computed per node before binning;
   no interpolation or fitted recentering. Compare boosts at equal n and actual dt.
5. **Record independent diagnostics:** positivity, element raw A2 defects and
   scales, global mass/energy drift, SVD fallback/rank counts, F1 lumping, mesh and
   solver timings, topology statistics if available. None proves another property.
   Report total conservation separately from local distribution closure.
6. **A2 mechanism, only after the reproducibility check:** capture the failed
   triangle's stage, states, geometry, K+/K-, Sminus, Phi, computed solve vector,
   singular values and rank. Separate solve/range residual `(Phi-Sminus*x)` from
   split defect `(Sminus+sum Kplus)*x` and final arithmetic rounding. Compare the
   *same local problem* in lab/co-moving and, if useful, higher precision. Existing
   condition diagnostics can guide this, but their aggregate maxima are not the
   failed triangle. Do not loosen4096 merely to obtain a pass. See the
   [A2 audit](RD_YEE_A2_TOLERANCE_AUDIT_20260925.md).
7. **Only then discuss a revised assertion/error model or error sources.** Neither
   the present error decrease nor boost-insensitive errors demonstrate a floor.
   Separate possible topology/geometry, quadrature/reconstruction and time/F1
   effects with controlled comparisons if needed. Gresho success is not a proof
   that Yee's local matrices have the same rank or scaling.

The historical `run_yee_*` scripts intentionally refer to Mac archives and cannot
be launched unchanged on COSMA. Use the portable preparer above, the managed Slurm
wrappers, and adapt analysis to Slurm's `output/arepo-*.log` plus job exit states.
`analyze_yee_boost_sensitivity.py` contains the exact-field/norm/fit logic, but its
Mac campaign/status schema is not a drop-in COSMA collector. This adaptation is
remaining work; do not invent successful run_status records to make it accept
partial Slurm outputs. A cancelled/time-limited job is not a numerical failure.

## Cleanup and verification for this commit

- No hydro simulations restarted after the stop request.
- `make check_rd` passed all four algebra tests, including compiled common-beta
  stage tests; no claim of a new full native hydro validation.
- New Python scripts compile; portable preparation creates27 cases with valid
  hashes/paths/step counts, matching archived active Config options. Bad-input
  and overwrite rejection checked. `git diff --check` and shell syntax checks pass.
- Historical run helper now always analyzes finished science results even if one
  science case failed; uniform/pilot failures still block further launch.
- Runtime code, flags and tests from the existing local development are included
  with their reports. Unrelated thesis diagram assets and Chapter3.7 scratch work
  are left untouched. No simulation HDF5, executable, build directory or secret is
  included in Git. Data transfer and COSMA job submission remain to be done.
