# AREPO Residual Distribution Development Log, volume 3: local Mac

This log records local Apple Silicon development and validation performed while
access to the Cuillin cluster is unreliable. It complements
`RD_DEVELOPMENT_LOG_2.md`; it does not replace or renumber the missing Cuillin
entries.

- Opened: 2026-08-31.
- Time zone: Asia/Shanghai.
- Local repository: `/Users/zhenyuwu/arepo_rd/arepo`.
- Branch at opening: `develop_pureC_RD`.
- Commit at opening: `6a92cd671366bfffd6040d33c1b6b6acb66831bf`.
- Environment reference: `dev_log/context_localMac.md`.

The local copy of volume 2 currently ends at section 73, while
`Aug26_update_bundle/Aug26_update.md` refers to sections through 83. Before
making a definitive chronological handover statement here, check the complete
volume 2 on Cuillin. Until then, the August 26 update is the supplementary
handoff for the intervening moving-mesh hierarchy work.

---

## Index of sections

| # | subject in one line |
| --- | --- |
| 1 | Native Apple Silicon environment and first static RD smoke gates |
| 2 | Chapter 3 Gresho and Rayleigh--Taylor local feasibility audit |
| 3 | Native SWIFT SPHENIX and GIZMO MFV support for Chapter 3 |
| 4 | Official SWIFT 2-D SPHENIX Gresho baseline to t=3 |
| 5 | SWIFT n48 representative and high-neighbour Gresho comparison |
| 6 | GIZMO n48 meshless finite-volume Gresho run to t=3 |
| 7 | Controlled GIZMO MFV mesh-motion, neighbour and limiter tests |
| 8 | Matched AREPO MMFV and static RK2 RD Gresho results |
| 9 | Matched static N/LDA fixed-buffer Rayleigh--Taylor results |
| 10 | Moving N hierarchy + MPI spike; independent Arpaia endpoint-conservation defect |
| 11 | Flip-dependent local-clock coverage defect; conservative topology/epoch design |
| 12 | Representation-level alternatives and implementation cost in existing AREPO |
| 13 | Return to P1; patch-synchronous topology transfer |
| 14 | Deep-bin concern; active-only remap and triangle interval closure |
| 15 | Positivity blocks promoting the active-only remap |
| 16 | Positivity and comparison of three topology schedules |
| 17 | Independent review of 10--16; corrections on exact patches, MOOD and the retention window |

---

## 1. Native Apple Silicon environment and first static RD smoke gates

**Date:** 2026-08-31

The local machine is an arm64 Apple M4 MacBook Pro running macOS 26.6.2. The
AREPO `LocalMac` make configuration uses the Homebrew installation rooted at
`/opt/homebrew`, including Open MPI 5.0.7, parallel HDF5 1.14.6, GSL 2.8,
GMP 6.3.0, FFTW 3.3.10, hwloc 2.11.2 and OpenBLAS 0.3.29. A joint
compile/link check including LAPACKE passed. The resulting AREPO executable is
a native arm64 Mach-O binary linked against the Homebrew libraries.

The existing Conda environment
`/Users/zhenyuwu/miniconda3/envs/21cmfast` is the temporary Python baseline. It
already provides the scientific Python packages needed for current IC
generation, output inspection and tests. A dedicated `arepo-local` environment
can be frozen later, but is not required for the current smoke-test phase.

Three pure-Python RD algebraic tests and `make check_rd` passed. A 16-cell
two-dimensional Yee IC with 259 particles was generated locally and evolved to
`t=0.02` in isolated directories outside the Git repository.

The static N+RK2 case completed on both one and two MPI ranks. Density and
pressure remained positive and the maximum element conservation defect was
approximately `2e-15`. Final snapshots compared after sorting by ParticleID:
coordinates and timestep bins were identical, while the largest differences
among velocity, density, pressure and internal energy were of order
`1e-15`. This passes the first local MPI and rank-invariance smoke gate.

The matching static LDA+GL/F1 RK2 case completed on one rank. Its final minimum
density and pressure were approximately `0.49366` and `0.37220`; all recorded
fields were finite. The maximum reported element conservation defect was
`4.16e-17` (relative `4.45e-16`), with `f1_lumped=0` at both steps. This passes
the first static LDA+GL/F1 smoke gate.

The Cuillin `.sbatch` launchers remain unchanged. Local tests can run
concurrently without Slurm provided every case has a separate build directory,
executable, working directory, output directory and log. Concurrent builds
must not target the same build tree, and concurrent runs must not write to the
same output directory. For small campaigns, set `OPENBLAS_NUM_THREADS=1` and
keep the total MPI rank count conservative on the 10-core, 16-GB laptop.

The next validation sequence is moving equal-step N, moving hierarchical N in
the equal-bin limit, and then the moving two-bin N gate. Run the first instance
of each gate serially and on one rank; only introduce local case concurrency or
moving-mesh MPI after the corresponding baseline is accepted.

---

## 2. Chapter 3 Gresho and Rayleigh--Taylor local feasibility audit

**Date:** 2026-08-31

The Chapter 3 static-mesh figure campaign was audited against the locally
available source trees, analysis scripts and copied data. The existing Yee
figure can be retained and Sedov is out of scope. The Enzo Gresho dataset and
its rendered figures are present locally under
`/Users/zhenyuwu/Hydro_data_analysis/Data_Enzo/gresho_2d`, so Enzo does not
need to be rerun.

The public-AREPO Gresho generator produced a 2301-point ring-48 IC. Both the
built-in moving-mesh finite-volume configuration (`Config_MM.sh`) and the
static RD LDA configuration (`Config_RD_LDA_Static.sh`) compiled natively and
completed isolated runs to `t=0.02`. The moving-mesh case took approximately
0.44 seconds. The debug RD/LDA case took approximately 25 seconds and retained
element conservation at round-off level. These establish that both central
AREPO Gresho curves can be regenerated locally; a full debug RD run to `t=3`
will be materially slower and should be launched only after the final campaign
matrix is frozen.

The preferred classical Rayleigh--Taylor setup is the `gizmo-fixed` profile:
`gamma=1.4`, `g_y=-0.5`, a logistic density transition from one to two, and
fixed reservoir strips in the elongated `0.5 x 1.5` domain. The official SWIFT
`glassPlane_48.hdf5` was used to generate a 1731-point seeded IC. The exact
static N+RK2 configuration (`Config_RT_GIZMO_FIXED_N_RK2.sh`) compiled and ran
to `t=0.01` in 3.6 seconds. Its final snapshot contained finite fields with
`rho` in `[0.99927, 2.00354]` and pressure in
`[0.68756, 1.81211]`. The fixed-boundary and external-gravity diagnostics were
active. A formal morphology campaign must pair every seeded run with the
matching zero-amplitude hydrostatic control.

The analysis code is present but is not yet path-portable. Gresho plotting
scripts contain fixed `/home/zwu` input paths. The RT preparation script also
fixes its data root and parameter template to Cuillin paths, while
`rt_common.py` fixes the shared analysis path and SWIFT glass path. Convert
these to command-line or environment-selected local roots before producing
thesis figures.

SWIFT and GIZMO are feasible but are not yet locally build-ready. SWIFT lacks a
generated configure/build tree and the required Homebrew autotools are not
installed. The official `glassPlane_128.hdf5` has been downloaded for the n128
Gresho case, but the checked-in SWIFT example still uses the stock 48-neighbour
SPHENIX setup. The thesis comparison expected the Cuillin-tuned case of roughly
400 effective neighbours, so the exact YAML or `resolution_eta` must be
recovered before rerunning it. GIZMO has the MFV Gresho configuration and a
20-neighbour parameter file, but its build scripts and library paths are still
Cuillin/Intel-Mac specific and need an Apple-Silicon `LocalMac` target.

---

## 3. Native SWIFT SPHENIX and GIZMO MFV support for Chapter 3

**Date:** 2026-09-01

Homebrew Autoconf 2.73, Automake 1.18.1 and GNU libtool 2.6.2 were installed to
generate the SWIFT build system. Homebrew's automatic cleanup removed the
existing ripgrep installation as an unintended side effect; ripgrep 15.2.0
was immediately reinstalled.

SWIFT v2026.01 was configured in `build-localmac` with Apple Clang, Open MPI
5.0.7, parallel HDF5 1.14.6, SPHENIX and two-dimensional hydro. Handwritten
vectorization was disabled because the current source does not provide its
`VEC_*` abstraction on Apple ARM64. A tracked `build_localmac_2d.sh` records
the complete configuration. Both `swift` and `swift_mpi` are native arm64
Mach-O executables.

The official n128 glass produced a 16384-particle Gresho IC. The serial SWIFT
binary ran with two task threads to `t=0.002`, wrote initial and final HDF5
snapshots, and all numerical datasets in the final snapshot were finite. The
final density range was approximately `[0.97317, 1.01804]`. The run also
exposed a scientifically important configuration issue: in compiled 2-D mode,
`resolution_eta=1.2348` reports approximately 15.14 neighbours, not the 48
stated in the example comment. The former Cuillin high-neighbour comparison
must therefore be recovered or recalibrated before a thesis production run.

GIZMO gained a `LocalMac` machine block using `/opt/homebrew`, while leaving
the default Cuillin selector intact. `build_gizmo.sh` now locates its repository
dynamically, accepts `SYSTYPE` and `JOBS`, and defaults locally to `LocalMac`.
The Gresho IC generator now accepts explicit `--glass` and `--output` paths.
The MFV configuration compiled into a native arm64 executable.

Using the official n48 glass, GIZMO generated a 2304-particle IC and completed
an MFV run to `t=0.002`. Both snapshots were readable and finite; final density
was approximately `[0.98698, 1.01497]`. GIZMO's Linux-oriented memory summary
prints nonsensical available-memory values on macOS, but its internal allocator
reported only about 8 MB and the simulation completed normally. This cosmetic
platform-reporting issue does not block the small hydro campaign.

The GIZMO run also confirmed that the optional accuracy and SPH-control lines
in the existing parameter file are ignored unless `DEVELOPER_MODE` (and, for
the SPH-only entries, the matching SPH switches) is compiled. In particular,
the listed `CourantFac=0.025` was not applied to this MFV binary. The production
comparison must either retain and document the compiled defaults or explicitly
enable developer parameters and revalidate the case.

---

## 4. Official SWIFT 2-D SPHENIX Gresho baseline to t=3

**Date:** 2026-09-01

The current official `GreshoVortex_2D` example was run as the first SPH
baseline. Its n128 glass contains 16384 particles and the SWIFT executable was
the native two-dimensional SPHENIX build. The example configuration was left
unchanged except for extending `time_end` from one to three. The serial,
one-thread calculation completed 8192 steps and exited normally after about
231 seconds. All velocity values in the final snapshot were finite.

The snapshot metadata, rather than the stale YAML comment, identifies the
actual smoothing setup: cubic-spline (M4), `resolution_eta=1.2348`, and target
`N_ngb=15.14285`. This is a genuinely two-dimensional neighbour count. It must
not be described as 48 neighbours or compared directly with a three-dimensional
eta-to-neighbour conversion.

At `t=0`, the mean azimuthal velocity in the `0.19 <= r < 0.21` ring was
approximately `0.97490`; at `t=3` it was `-0.01468` with a particle scatter of
about `0.04189`. Using particles with `r < 0.4`, the mean absolute error in
azimuthal velocity increased from approximately `4.18e-4` to `0.51543`. Thus
the default low-neighbour 2-D SPHENIX setup has essentially erased the Gresho
vortex by `t=3`, consistent with the earlier Cuillin observation.

The isolated working case remains in
`/Users/zhenyuwu/arepo_rd/local_runs/ch3_swift_gresho_official_t3`. A complete
archive was copied to
`/Users/zhenyuwu/Hydro_data_analysis/Data_Swift/gresho_2d/sphenix_n128_default_eta1p2348_t3`.
All future SWIFT Gresho outputs use the latter data root, and the formal
cross-code comparison uses the 2304-particle `glassPlane_48.hdf5` (48 squared)
rather than n128. The existing local analysis script points to a historical
Cuillin directory named `equivalentNngb400/n128_sphenix`, confirming that the
old run deliberately changed the smoothing setup, although the exact YAML is
not present locally. For a true 2-D cubic-spline build, eta about 2.50352 is a
3-D-equivalent 400-neighbour choice but corresponds to an actual reported 2-D
target of only about 62.25 neighbours. This baseline is diagnostic, not a
recommended cosmological-production neighbour choice.

The formal high-neighbour matrix was subsequently fixed to the paper-style
3-D-equivalent definition rather than 400 actual neighbours in 2-D. At 48
squared, an actual 2-D target of 400 would give a support radius about 0.235 in
the unit box, larger than the radius 0.2 of the Gresho velocity peak, and would
therefore erase physical resolution. With Wendland C6, the adopted
3-D-equivalent target of 400 is `resolution_eta=1.866014` and corresponds to an
actual 2-D target of about 63.81. The planned matched runs are SWIFT `gadget2`
(traditional density-entropy), `sphenix`, and `pressure-entropy`, all using the
same n48 glass, kernel and eta.

For reference, SWIFT uses `h=eta*ell` in the uniform limit, compact-support
radius `H=kernel_gamma*h`, and reported geometric target
`N_ngb=V_d*(kernel_gamma*eta)^d`. Thus cubic-spline eta 1.2348 is a 3-D
48-neighbour choice but a true 2-D 15.14-neighbour choice; a true 2-D target of
48 would require eta about 2.19843. Kernel gamma changes with both dimension
and kernel, so labels must state whether a neighbour count is actual 2-D or
3-D-equivalent.

Before using the high-neighbour limit, run a representative n48 pair to `t=3`:
traditional GADGET-2 density-entropy SPH with cubic spline and eta 1.2348, and
SPHENIX with the production-style quartic spline and eta 1.2348. The latter is
about 64.90 neighbours in 3-D and 18.73 in the actual 2-D build. Only move to
the 3-D-equivalent 400-neighbour Wendland-C6 case if these results are too
strongly degraded for the RD/FV comparison. Store SWIFT Gresho data under
`/Users/zhenyuwu/Hydro_data_analysis/Data_Swift/gresho_2d`.

---

## 5. SWIFT n48 representative and high-neighbour Gresho comparison

**Date:** 2026-09-01

The formal SWIFT comparison was run with one shared `glassPlane_48.hdf5` IC:
2304 particles in the compiled two-dimensional build. Each case used one task
thread, evolved to `t=3`, wrote 31 snapshots, exited normally and contained
finite final velocity fields. Separate native arm64 executables were built for
each hydro/kernel combination so that no case depended on a run-time kernel
switch.

The representative pair confirmed that the stock-sized smoothing
neighbourhood is not adequate for the Chapter 3 Gresho comparison. Traditional
GADGET-2 density--entropy SPH with the cubic spline, `eta=1.2348` and actual
2-D target `N_ngb=15.14285` had `L1(v_phi)=0.50252` for `r<0.4` at `t=3`;
its maximum binned mean velocity was only `0.00654`. SPHENIX with the quartic
spline, the same eta and actual 2-D target `N_ngb=18.72546` was better but
still strongly dissipative: `L1(v_phi)=0.27624` and maximum binned mean
velocity `0.33950`. For reference, the common IC had `L1` below `9e-4` and a
maximum binned mean near `0.955` at `t=0`.

Because the representative pair was strongly degraded, the planned fallback
was executed. Both schemes used Wendland C6 with `eta=1.866014`, corresponding
to 3-D-equivalent `N_ngb=400` but actual 2-D target `N_ngb=63.81117`.
Traditional SPH improved to `L1(v_phi)=0.15464` and maximum binned mean
velocity `0.55320`; SPHENIX improved to `L1(v_phi)=0.14196` and maximum binned
mean velocity `0.60613`. Mean velocity in the peak ring
`0.18 <= r < 0.22` was respectively `0.53538` and `0.59120`, compared with
the analytic peak of one. The vortex remains visibly damped, but the
high-neighbour Wendland-C6 configurations preserve enough structure for a
meaningful RD/FV comparison, with SPHENIX modestly better than traditional
SPH in this test.

The combined comparison is saved as both PNG and PDF. The archive root is
`/Users/zhenyuwu/Hydro_data_analysis/Data_Swift/gresho_2d/n48_t3_sph_comparison`;
it contains the shared IC, plotting script, four isolated run directories,
complete logs and all snapshots. Experimental decisions and results are
recorded here in development log 3; `context_localMac.md` remains the general
local-environment reference.

---

## 6. GIZMO n48 meshless finite-volume Gresho run to t=3

**Date:** 2026-09-01

The native arm64 GIZMO executable was confirmed from its startup configuration
to use `BOX_SPATIAL_DIMENSION=2` and `HYDRO_MESHLESS_FINITE_VOLUME` (MFV), not
MFM. It used the locally generated 2304-particle `glassPlane_48` Gresho IC,
`DesNumNgb=20`, one MPI task and `MaxSizeTimestep=5e-4`. The isolated run
advanced through 8192 synchronization points to `t=3`, wrote 31 snapshots at
interval 0.1 and exited normally after approximately 132 seconds. All final
gas fields were finite.

Using the same azimuthal-velocity diagnostic as the SWIFT comparison, the
initial profile had `L1(v_phi)=5.33e-8` for `r<0.4`, maximum binned mean
velocity `0.95524` and peak-ring mean `0.94947`. At `t=3`, MFV retained
`L1(v_phi)=0.08898`, maximum binned mean velocity `0.71702` and peak-ring mean
`0.70980`. This is appreciably less dissipative than the best n48 SWIFT case
run above: SPHENIX with Wendland C6 and 3-D-equivalent `N_ngb=400` had
`L1=0.14196` and maximum binned mean velocity `0.60613`.

Total mass changed by approximately `-2.91e-10` in relative terms and total
energy by `-6.53e-8`; the two in-plane momentum changes were below `6.3e-8` in
absolute value. Final density remained in `[0.98092, 1.03103]`. The old GIZMO
macOS system-memory summary remains nonsensical, but the internal allocator
used only about 8 MB and the calculation was unaffected.

The standalone PNG/PDF profile, JSON diagnostics, plotting script, parameter
file, shared IC and complete snapshots are archived under
`/Users/zhenyuwu/Hydro_data_analysis/Data_gizmo/gresho_2d/mfv_n48_t3`.

---

## 7. Controlled GIZMO MFV mesh-motion, neighbour and limiter tests

**Date:** 2026-09-01

Three controlled n48 MFV runs isolated the differences between the TMOX
baseline and a Hopkins-2015-style configuration. All cases used the same
2304-particle glass IC, cubic-spline kernel, `gamma=5/3`, one MPI task,
`MaxSizeTimestep=5e-4`, 31 snapshots and `t=3`. Two native arm64 executables
were built in an isolated copy of the source with
`HYDRO_FIX_MESH_MOTION=7`; they differed only in explicit
`SLOPE_LIMITER_TOLERANCE=1` versus 2. All three runs exited normally and all
final fields were finite.

At fixed `DesNumNgb=20` and limiter 1, changing from the current TMOX default
smoothed-Lagrangian mesh motion (mode 5) to fully Lagrangian mode 7 reduced
`L1(v_phi)` from `0.08898` to `0.07966`, reduced the peak-ring scatter from
`0.04699` to `0.03947`, and raised the peak-ring mean from `0.70980` to
`0.71917`. The maximum binned velocity changed only from `0.71702` to
`0.72013`. Mesh motion is therefore measurable but is not the main cause of
the lower peak relative to Hopkins (2015) Figure 4.

At fixed mode 7 and limiter 1, reducing the actual 2-D neighbour target from
20 to the paper value 16 did not improve this n48 glass. `L1` increased to
`0.09554`, peak-ring scatter increased to `0.05746`, and the peak-ring mean
fell slightly to `0.71046`; the maximum binned velocity was `0.71685`.
Although 16 is the paper-style neighbour count, 20 is the better-behaved
choice for this particular IC and current code version.

At mode 7 and `DesNumNgb=16`, changing limiter 1 to limiter 2 produced the
largest recovery of the vortex peak. The maximum binned velocity increased
from `0.71685` to `0.76791` and the peak-ring mean from `0.71046` to `0.75259`.
This came with a larger peak-ring scatter of `0.06519`; `L1=0.08209` remained
slightly worse than the mode-7, 20-neighbour, limiter-1 result because the L1
metric penalizes that added noise. The experiment confirms the expected
accuracy/noise trade-off of the aggressive limiter, but the paper-style
combination still does not reproduce the approximately 0.9 peak visible in
Figure 4. Remaining differences are most plausibly associated with the
2015-versus-TMOX-2020 implementation and limiter details, and possibly the
paper's internally inconsistent 40-squared versus 64-squared resolution
description, rather than a defective local glass.

The neighbour-number convention was subsequently checked directly against
Hopkins (2015), Section 4.2.3. The paper explicitly states that the MFM/MFV
runs use the cubic spline with fixed `N_NGB=32` in 3-D and `N_NGB=16` in 2-D
(following Gaburov & Nitadori 2011). Thus the controlled
`DesNumNgb=16` cases use the paper's actual two-dimensional target; 32 is the
quoted three-dimensional equivalent, not the parameter that should be entered
for this 2-D build. The GIZMO target is kernel-weighted rather than a strict
integer top-hat count. In the limiter-2 run at `t=3`, the literal number of
particles within each particle's kernel support had median 16, mean 15.63 and
range 13--19, consistent with the target. For the thesis comparison, the
selected representative GIZMO result is therefore mode 7,
`DesNumNgb=16`, `SLOPE_LIMITER_TOLERANCE=2`: it uses the paper-style mesh
motion and neighbour convention while giving the best peak retention in the
current TMOX implementation. It should be described as a representative
current-code result, not as an exact reproduction of the 2015 curve.

For every controlled run the relative mass change was below `4e-10` and the
relative total-energy change below `9e-8`. The complete campaign, including
exact build configurations, native executables, logs, snapshots, JSON metrics
and comparison figures, is archived under
`/Users/zhenyuwu/Hydro_data_analysis/Data_gizmo/gresho_2d/mfv_n48_controlled`.

---

## 8. Matched AREPO MMFV and static RK2 RD Gresho results

**Date:** 2026-09-01

Three matched n48 Gresho runs used the same 2304-point SWIFT glass, zero bulk
velocity, `gamma=5/3`, CFL 0.3, output interval 0.1 and endpoint `t=3`. The
generated AREPO IC has SHA256
`da76535f6f6366fa8d9b43d3e27f0f8b1bdfb461eead3c2d80aed401c935df64`,
which exactly matches the retained legacy glass48 manifest. The source glass
has SHA256
`157e1a4767f4678df4cd80d2df9aa248fa520899e12e777a448e17f31e47d88f`.

The native baseline is AREPO's moving-mesh finite-volume solver with the
standard centre-of-mass and face-angle regularisation; it is therefore stored
under `Data_arepo_MMFV`. The two pure-C RD cases use a fixed Voronoi mesh,
`RD_RK2_TOTAL_RESIDUAL`, `FORCE_EQUAL_TIMESTEPS`, and respectively
`LDA_SCHEME` or `N_SCHEME`. `RD_DEBUG_ASSERTS` was omitted from these production
builds because the earlier short validation runs had already exercised it and
the assertions do not define the numerical scheme.

Each case used one MPI rank and wrote 31 HDF5 snapshots. MMFV finished in
103.53 seconds. LDA and N finished in 4867.91 and 4871.53 seconds
(approximately 81 minutes) and exited normally. A short test with four ranks
per RD case was slower on the local M4 for this 2304-cell problem. AREPO's CPU
breakdown attributed approximately 99.2 per cent of the RD time to the
residual-distribution kernel, not I/O, geometry, restart or logging. The
small-matrix LAPACK solve performed for every triangle and RK2 stage is the
dominant local cost; simply increasing MPI ranks is not an effective
optimisation at this resolution.

The common final diagnostic uses the unweighted cell/particle mean
`L1(v_phi)` for `r<0.4`, bins of width 0.02, and the mean over
`0.18 <= r < 0.22`. This is the same profile convention used in the local
GIZMO and SWIFT comparison scripts.

| scheme, t=3 | L1(r<0.4) | binned peak | peak-ring mean |
| --- | ---: | ---: | ---: |
| AREPO MMFV, moving mesh | 0.02833219 | 0.84987032 | 0.84689156 |
| RD LDA RK2, static mesh | **0.01831895** | **0.89405271** | **0.89154904** |
| RD N RK2, static mesh | 0.20877097 | 0.44826399 | 0.43637485 |

LDA reduces the matched L1 error by 35.34 per cent relative to native MMFV
and retains a visibly higher vortex peak, confirming the expected Chapter 3
accuracy advantage. Its final density remains in
`[0.9980548, 1.0021097]`. Mass and total energy change only at approximately
`2.2e-16` relative, and the in-plane momentum changes are below `1e-16`.

Pure static N is stable and conservative but far more diffusive than LDA or
MMFV. Its final density range is `[0.9939706, 1.0520907]`, with exact printed
mass and energy conservation. The result is consistent with N being a robust
first-order monotone control, but it sharpens the earlier qualitative claim
about particle methods: N is better than the stock-sized local SWIFT SPHENIX
case (`L1=0.27624`) and traditional SPH case (`L1=0.50252`), but it is worse
than the selected high-neighbour Wendland-C6 SPHENIX (`L1=0.14196`) and
traditional SPH (`L1=0.15464`) cases. It is also worse than the selected GIZMO
MFV mode-7, 16-neighbour, limiter-2 result (`L1=0.08209`). The thesis should
therefore label N as a deliberately dissipative robustness/control scheme,
not claim that it is uniformly better than every SPH configuration.

The isolated local campaign is
`/Users/zhenyuwu/arepo_rd/local_runs/ch3_arepo_gresho_n48_mmfv_rd_static_rk2`.
It contains the exact compile configs, parameters, binaries, logs, IC,
analysis script, JSON diagnostics, PNG/PDF comparison and the complete local
outputs. The production archive is split by solver family under
`/Users/zhenyuwu/Hydro_data_analysis/Data_arepo_MMFV/gresho_2d/mmfv_glass48_t3`
and
`/Users/zhenyuwu/Hydro_data_analysis/Data_arepo_RD/gresho_2d/rk2_static_glass48_t3`.

---

## 9. Matched static N/LDA fixed-buffer Rayleigh--Taylor results

**Date:** 2026-09-03

The Chapter-3 Rayleigh--Taylor campaign prepared on COSMA was reproduced
locally while the COSMA Slurm partitions were down for maintenance.  The
preferred `gizmo-fixed` setup was retained: a static `0.5 x 1.5` glass with
6912 vertices (nominal `n=96`), `gamma=1.4`, `g_y=-0.5`, a logistic density
transition from one to two of width `0.025` at `y=0.75`, interface pressure
`10/7`, and perturbation coefficient `0.025`.  The actual peak seed velocity
is `0.09992899687639602`.  Vertices with `y<0.15` or `y>=1.35` are fixed
reservoirs.  Five snapshots were written at `t=0,1,2,3,4`; the boundary-
affected `t=5` endpoint was deliberately excluded.

The N executable used
`examples/rt_2d/Config_RT_GIZMO_FIXED_N_RK2.sh`.  The new standard LDA+GL/F1
configuration is
`examples/rt_2d/Config_RT_GIZMO_FIXED_LDA_RK2.sh`: it differs from the N file
only by selecting `LDA_SCHEME`, and its SHA-256 is
`5185e4e2f1194915536db695ab38472809a5c048b6c1898fe26f5ec347cf6173`.
This exactly matches the generated LDA configuration recorded in the COSMA
campaign.  It does not enable the older experimental
`RD_RK2_RATE_CONSISTENT_HEUN` option.  Both native arm64 binaries were rebuilt
from commit `cd0a7ffd8a7ffbd97c7397a2a714810c0fd346e3` plus this new tracked
configuration, using the `LocalMac` Homebrew/OpenBLAS target.

A zero-seed `n=48`, `t=0.02` gate passed first for both schemes.  All fields
were finite and positive, fixed-layer velocity and internal energy remained
bitwise unchanged, and the maximum element conservation defects were
`2.425e-16` for N and `1.388e-17` for LDA.  Matched seeded and zero-seed
`n=96` cases were then each advanced for 8192 equal steps to `t=4`.  All four
runs exited normally.  The two seeded runs each required about 211 seconds
when run concurrently as independent one-rank processes.

At `t=4`, the principal diagnostics are:

| case | rho min | seed-mode amplitude | non-mode RMS vy | reservoir mass fraction | near-boundary max abs(vy) |
| --- | ---: | ---: | ---: | ---: | ---: |
| seeded N | 0.848850 | 0.081521 | 0.108359 | 0.065299 | 0.061691 |
| control N | 0.990795 | 0.005323 | 0.017345 | 0.020943 | 0.016872 |
| seeded LDA | 0.676675 | 0.063917 | 0.137959 | 0.066191 | 0.052979 |
| control LDA | 0.954407 | 0.005153 | 0.029032 | 0.016024 | 0.022170 |

Every final pressure is positive; the minimum pressure in every case is
`0.6872674`.  The minimum predictor densities over the complete seeded runs
are `0.84854` for N and `0.49541` for LDA.  Maximum element conservation
defects are `1.272e-16` and `6.939e-18`, respectively.  Fixed-layer velocity
and internal energy remain bitwise unchanged in all four runs.  Summed
reservoir mass exchange closes against the snapshot mass change to
`6.48e-11` (seeded N), `1.43e-10` (seeded LDA), `3.87e-12` (control N), and
`1.36e-11` (control LDA) in absolute mass units.

The local N numbers reproduce the retained Cuillin report: at `t=4` the
reservoir fraction is 6.53 per cent, the adjacent active-layer maximum
`abs(vy)` is 0.0617, and the seeded/control non-mode RMS values are
0.1084/0.01734.  Thus the local Apple-Silicon result independently recovers
the earlier x86-64 morphology and diagnostics within the reported precision.

Both schemes form the imposed large-scale mushroom through `t=2`.  N remains
the smoother and more dissipative solution at `t=3--4`; LDA retains and
amplifies substantially more small-scale structure.  The controls develop
only much weaker glass/contact-seeded fingers and no comparable coherent
primary mushroom, confirming that the main mode is imposed-seed driven.
Late LDA filaments are nevertheless not claimed to be a converged physical
roll-up; they should be presented as the scheme admitting more secondary
structure on this glass.

The complete local work directories are
`/Users/zhenyuwu/arepo_rd/local_runs/ch3_arepo_rt_n96_static_rk2_seed0025_t4`
and `ch3_arepo_rt_n96_static_rk2_control_t4`.  Compact production archives are
under
`/Users/zhenyuwu/Hydro_data_analysis/Data_arepo_RD/rt_2d/`
`rk2_static_gizmo_fixed_n96_d0025_seed0025_t4_localmac` and
`rk2_static_gizmo_fixed_n96_d0025_control_t4_localmac`.  They retain the IC,
five snapshots per scheme, exact executable and configuration, parameters,
compressed run log, JSON diagnostics, seeded/control plots, and the common-
colour N/LDA comparison in PNG and PDF.  Restart files and large per-step CPU,
time-bin, and balance logs were not duplicated into the production archive.

---

## 10. Moving N hierarchy + MPI and a separate Arpaia conservation defect

**Date:** 2026-09-08. **Author:** Codex (GPT-6), at Zhenyu's request.

The moving-mesh context, log 2, the August 26 handoff, the recent local/COSMA
logs and the actual hierarchy code were audited before selecting Chapter 4
mathematics. Local log 2 still ends at section 73; the unavailable sections
74--83 were not recovered. The source baseline is
`75c3d6ac65b8edce2741a372fc9507dacf22151e`.

The main feasibility result is positive: an isolated MPI port of the existing
moving N hierarchy completes on 1, 2 and 4 ranks with both Campoli and Arpaia
mass forms. It exports endpoint areas, due-element divisor contributions and
geometric increments to vertex primaries, closes only complete stars, and
adds the missing predictor-to-corrector ghost refresh. Existing minimum-ID
simplex ownership, star-bin reductions and extensive residual exports are
reused. Removing only the one-rank guard would not have supplied these steps.

There is also a substantive correction to the August 26 interpretation.
Let `B_i` be a live vertex's physical ledger after geometric closure, `D_i`
the Arpaia divisor, `m_i+` the endpoint area and `L_i` its integrated fluid
plus temporal residual increment. The current open/close rebase gives

\[
Q_i^{new}=B_i+\frac{m_i^+}{D_i}L_i
=B_i+L_i+\left(\frac{m_i^+}{D_i}-1\right)L_i.
\]

The last term has no general zero-sum identity. It vanishes on a uniform
state but is nonzero on a smooth nonuniform state even without topology
changes. This was established independently with a scalar N experiment and
then reproduced with the unmodified Euler solver. It is a truncation-order
channel, not evidence that the solver cannot execute hierarchically.

The Euler discriminator uses 64 jittered periodic vertices, gamma 1.4,
nonuniform density/velocity/pressure, a controlled 2:1 bin split, coarse
`H=0.004`, and final time `0.008`. All four event triangulations are unchanged;
the basis closure remains at round-off. Physical mass/energy changes are
round-off for Campoli and about `-2.052e-10`/`-1.062e-9` for Arpaia.
Halving `H` produces approximately cubic single-macrostep defect scaling.
The instrumented sum of opening plus closing rebase changes accounts for
the measured drift to round-off. The old gross closing `dQ` diagnostic was
not the net defect.

Both forms pass the 1/2/4-rank particle-ID comparison on this discriminator:
all inspected field differences from the unmodified one-rank solver are below
`3.6e-15`, and timebins agree exactly. The small runs repeatedly perform domain
decomposition. This is a correctness gate, not a speedup or production-CFL
claim.

Extending the same problem to `t=0.064` produces topology changes (endpoint
triangle-key symmetric difference 16, not a flip count). Both forms pass the
1/4-rank comparison to below `6.7e-15`, but both have physical mass changes
of approximately `-4.414e-4`. The basis ledger explains that change; adding
the separately measured Arpaia net-rebase contribution closes all remaining
conserved totals to below `1e-15`. No new MPI or unexplained hierarchy channel
was detected in this bounded window. Keep-U topology closure remains a
nonconservative operation for a general state.

Recommendation for mathematical review: use Campoli endpoint storage as the
conservative transport/MPI reference. Retain current Arpaia as a comparison
with its explicit defect, or derive an Arpaia-divisor predictor with a direct
conservative endpoint commit. The latter passed the independent scalar
conservation test here but was not implemented for Euler. No production
Config was changed.

Moving LDA/F1 remains unimplemented, though its conservative temporal
column-sum contract can be written down. The existing static frozen-star
LDA hierarchy already measured approximately first-order time convergence
across bin interfaces; “RK2 stages” must not become a claim of second-order
multirate accuracy. Exact conservative topology transfer, deeper-bin CFL and
pullback validity, and restart/accuracy gates remain separate work.

Full derivation, evidence and engineering contract:
[`RD_moving_hierarchy_MPI_audit_20260908.md`](RD_moving_hierarchy_MPI_audit_20260908.md).
Reviewable isolated source patch:
[`patches/20260908_moving_hierarchy_mpi_spike.patch`](patches/20260908_moving_hierarchy_mpi_spike.patch).
The independent scalar audit is
`tests/rd/audit_ale_hierarchy_mass_rebase.py`.

All campaign inputs, binaries, generated headers, source-copy/patch,
provenance, three snapshots per case, logs and JSON summaries are retained in
`/Users/zhenyuwu/arepo_rd/local_runs/moving_hierarchy_audit_20260908`.
Tracked solver C and thesis files were not modified; no commit was made.

## 11. 2026-09-09: topology changes can expose an additional local-clock defect

Following the user's request to distinguish extra hierarchy/MPI errors from
edge-flip nonconservation, the previous §10 conclusion was tested with a
fixed generator trajectory shared across all bin patterns and rank counts.
The previous two-bin flip window remains a valid measurement, but it did not
exercise the decisive case: a flip that changes the fine/coarse membership of
the involved triangles.

The current hierarchy uses only endpoint connectivity and pulls every due
triangle backwards over its full current minimum-bin interval. There is no
persistent triangle birth/death history. Thus an old coarse element can die
before its due time, while a new coarse element is retrospectively assigned
an interval before it existed. Positive pullback areas and complete endpoint
box coverage do not imply complete space-time coverage.

An independent frozen-P1 scalar discriminator isolates this scheduler with
zero mesh velocity on a 16-node periodic grid. Old and new complete spatial
residual sums are round-off. With H=0.08, h=0.01 and a diagonal swap at 0.03,
mixed clocks produce an integrated residual of magnitude `1.23e-4`. Fixed
connectivity, equal clocks, and actual lifetime partitioning all give below
`1.6e-18`. This is an algebraic quadrature test, not a complete PDE simulation.

An isolated Euler campaign then used the 64-node Campoli N/MPI prototype,
H=0.004, final time 0.128, prescribed per-ID mesh velocity, smooth and uniform
states, and eight bin patterns on 1/4 ranks: 32 cases. Only-one-fine-vertex
patterns deliberately target the first flip quadrilateral; they develop a
nonclosure balance of `2.35e-6`–`1.18e-5`. Equal, two-bin and four-stripe
controls remain at round-off in this window. The first signal appears at the
first common synchronization after the first detected flip.

Here nonclosure balance means physical total change minus accumulated
implementation basis close. It is **not** the full physical conservation
error. The uniform controls preserve physical totals and U to round-off but
still show a nonzero nonclosure balance, canceled by that close. Therefore
the logged basis itself includes temporal geometry coverage under these
events and cannot be identified with a pure same-time spatial transfer.
All 1/4-rank field differences are below `1.25e-14`, with identical bins;
no additional MPI contribution was detected. This is not a scaling/restart
or changing-bin transition result.

The spatial operator in log 2 §68 remains valid at a defined common time:
delta Q_i = delta m_i U_i - w_i sum_j(delta m_j U_j), with sum_i w_i=1.
It is locally conservative and preserves affine states. Full-new-nodal-mass
weights additionally make an unlimited same-time flip/reverse exactly
invertible. A changed-patch average gives an admissible conservative low-order
endpoint, and one patch-common limiter preserves both invariants. In 1,000
random admissible Euler patches, the new algebra test measured maximum
conservation and unlimited flip/reverse errors of `7.11e-15`; 774 deliberately
high-contrast samples required limiting. This is not a positivity proof for
the full RD timestep.

A complete combined remedy requires both spatial transfer and time-interval
coverage. The smaller constructive reference is a persistent RD triangulation
and frozen mesh velocity within a common macro epoch, with actual hierarchical
substeps, followed by conservative remapping at synchronization. It needs a
positive-area bound and a persistent RD element/halo layer. Immediate fine-event
flips instead require lifetime/edge registers, compatible stage traces,
common-time patch states and exactly-once MPI transactions. A four-vertex
wakeup alone does not establish these properties. Neither design is yet a
production implementation, and second-order multirate accuracy remains a
separate unmet claim.

Full derivation, evidence, engineering contract and literature links:
[`RD_topology_hierarchy_conservation_20260909.md`](RD_topology_hierarchy_conservation_20260909.md).
Algebra discriminator: `tests/rd/audit_flip_time_coverage.py`.
The preceding §10 report now has an explicit follow-up notice.
The full isolated campaign and provenance are retained at
`/Users/zhenyuwu/arepo_rd/local_runs/topology_hierarchy_audit_20260909`.
Tracked solver C and thesis files remain unchanged; no commit was made.

## 12. 2026-09-09: compare representation choices against existing AREPO infrastructure

> Later user decision: park the native-FV prototype at its existing Python
> algebra checks; it is future work, not the current thesis development plan.
> The P1 continuation is recorded in §13 below.

The user asked whether macro synchronization really solves intermediate
flips, whether remapping is an unavoidable complication of current RD, and
whether a more elegant alternative is practical in an existing AREPO project.

A synchronized endpoint is insufficient to reconstruct intermediate transport
on changing triangulations. Deliberately retaining hydrodynamic connectivity
for a whole macrostep is a different, conditionally conservative algorithm.
That construction remains useful, but its persistent element/halo and validity
requirements mean it is not automatically the cheapest engineering choice.

The finite jump is intrinsic to the current P1 representation. On a unit
square, changing AC to BD changes lumped coefficients from
(1/3,1/6,1/3,1/6) to (1/6,1/3,1/6,1/3). General unchanged nodal data therefore
change the represented integral even at the exact cocircular time. A local
transfer, geometric flux or space-time jump condition must account for that
change. In contrast, true Voronoi cells have no finite volume jump at a generic
flip; their disappearing face shrinks to zero. This distinction does not
eliminate finite-step GCL or flux quadrature errors.

A promising bounded alternative is to retain native Voronoi cell averages and
derive multidimensional corner/face fluxes from RD. Current source already
supplies active-face scheduling, common face timesteps, unique MPI ownership,
updates to inactive-cell conserved quantities, remote extensive exports and
Volume-based primitive recovery. The new work can potentially be concentrated
in a corner geometry/state/flux interface inside the native FV driver, rather
than a new persistent mesh and distributed topology-time ledger.

The Gaburro–Ricchiuto–Dumbser paper mentioned in log 2 §7.7 was checked at
arXiv:2506.00207v2 (2026-01-31). It supports deriving static corner fluxes from
RD fluctuations, including N. Its actual polygons are barycenter-based
Voronoi-like cells, not AREPO's true circumcentric Voronoi cells; that geometry
and its auxiliary triangle cannot be copied blindly. A true-Voronoi ALE/LTS
extension is a new method, not changing the existing DualArea denominator.

An independent scalar audit checked the small linear-algebra bridge to a
native face implementation: at a nondegenerate three-cell corner, zero-sum
corner contributions can be represented by one common spatial flux vector.
For 1,000 scalar N samples, maximum representation error was `2.67e-15`.
The same script compares the P1 jump with continuously varying Voronoi areas.
This does not validate an Euler flux, a discrete moving GCL, local-time accuracy,
or a larger MPI stencil.

The recommendation is to keep existing RD as the main reference, complete
its bounded equal-step conservative result, and investigate a small native-FV
corner-flux prototype before committing to a large immediate-flip P1/LTS
rewrite. Frozen-connectivity macro epochs remain a mathematical reference;
full space-time RD and a different continuous nodal basis are longer-term
directions. No architecture switch has been applied to production code.

Full derivation and source-level implementation map:
[`RD_moving_representation_design_20260909.md`](RD_moving_representation_design_20260909.md).
New independent test: `tests/rd/audit_voronoi_corner_flux_algebra.py`.
JSON, scientific illustration and provenance are retained under
`/Users/zhenyuwu/arepo_rd/local_runs/topology_alternatives_20260909`.
No new Euler simulation was run in this follow-up. Solver C and thesis files
remain unchanged; no commit was made.

## 13. 2026-09-09: return to P1; test patch-synchronous topology transfer

The user prioritizes human-verifiable P1 RD development before thesis submission
and declines a native-FV/corner-RD implementation campaign. The FV route is parked
at the existing Python algebra checks as possible future work.

The next bounded P1 design delays adoption of changed RD connectivity until all
vertices modified by its transfer reach their own natural synchronization point.
Finish the old-connectivity sweep first, recover synchronized states, then remap.
With aligned fixed dyadic bins, every triangle incident to a changed node has also
finished its interval at that time. This avoids both triangle-lifetime truncation
and changing frozen nodal traces inside other triangles' coarse intervals. The
patch may synchronize before the rest of the domain; it need not force a global
wakeup. Persistent RD connectivity and an old-triangle validity condition remain
necessary. This is a proposed scheduling change, not immediate-flip repair.

New independent scalar test `tests/rd/audit_p1_patch_sync.py` runs 192 combinations
of fixed/patch-synchronous/immediate adoption, moving/static geometry, uniform/
nonuniform states, two step sizes, two event offsets and four fine-node choices.
All assertions pass. Patch-synchronous global-sync mass error is at most
`4.45e-16`, uniform error `4.45e-16`, with no missing or pre-birth triangle
intervals. All four remaps occur midway through global steps (ticks 4,12,20,28;
global period 8). Synthetic requested flips are not Delaunay detection.

A stronger negative control remaps at tick 2: deleted/new triangles all have
completed intervals, and each map conserves Q, yet changing inactive patch-node
states disturbs their other incident intervals; mass error reaches `1.70e-7`.
At tick 3 lifetime errors also appear, with mass error up to `1.14e-5`.
Uniform flow still passes these unsafe controls, so it is insufficient alone.

Source inspection suggests a private RD triangle view could reuse the existing
DP/DT-based N kernel and geometric ledger. The current diagnostic snapshot only
stores sorted IDs and area/3; it is not a persistent mesh. Orientation, periodic
winding, ownership/migration and old-node halo remain real implementation work.
No C solver was changed and no new Euler/MPI simulation was run this turn.

Detailed derivation, limitations and human-review gates:
[`RD_P1_patch_synchronization_20260909.md`](RD_P1_patch_synchronization_20260909.md).
Raw output/provenance: `/Users/zhenyuwu/arepo_rd/local_runs/p1_patch_sync_20260909`.
Campoli is the initial target to isolate the separate current Arpaia storage
rebase defect. No second-order mixed-bin claim or one-week completion guarantee
is made.

## 14. 2026-09-09: deep-bin concern; active-only remap and triangle interval closure

The user noted that waiting for every affected vertex can leave the RD mesh
far from Delaunay when cosmological timestep ratios are large. The previous
all-node condition is sufficient for its all-node primitive update, not a
necessary condition for every conservative ledger transfer.

A candidate map keeps inactive U and Q-gU unchanged while updating Q and g:
delta g=delta m, delta Q=delta m U-wD, D=sum delta m U; w has unit sum and
is supported on active nodes. Only active primitives are changed. For an
isolated 2-to-2 flip, natural old/new triangle clocks all align on the second
smallest of the four vertex steps, not the largest. A scalar 1:2:256:1024
case can therefore flip at tick 2 instead of 1024 with roundoff total error.

The isolated-fine-node case 1:1024:1024:1024 still needs more. A second scalar
prototype closes removed triangles' outstanding intervals at the event, starts
new triangles at their birth time, and latches touched inactive vertices frozen
through their current own-step endpoint. This closes local triangle ledgers
without waking entire vertex stars. Losing the latch can retroactively enable
a predictor whose history no longer exists; the corresponding ablation fails.

`audit_p1_active_transfer.py`: 192 standard and 8 deep-bin cases; active-only
standard total error <=4.45e-16. Its separate 1000-state Euler transfer audit
checks conditional positivity and supplies an explicit infeasible example;
these are not Euler PDE simulations or physical failure frequencies.
`audit_p1_event_flush.py`: 128 standard and 8 deep-bin cases; complete-rule
global-sync total error <=2.00e-15, uniform error <=7.78e-16. Deep cases flip
at ticks 1/1025, including 1:1024:1024:1024. Without the frozen-until latch,
error reaches 2.32e-6 in the standard campaign.

Active-only correction can be too large to preserve positivity; no limiter
can solve a negative required active total mass. Event closure also requires
a nonempty active correction support and valid old geometry over each actual
interval. These remain explicit restrictions, not a complete cosmological
algorithm. Natural-sync adoption plus bounded local interval closure is now
the more promising P1 direction than unconditional waiting for all vertices.

Details, source integration points, counterexamples and scope:
[`RD_P1_deep_hierarchy_topology_20260909.md`](RD_P1_deep_hierarchy_topology_20260909.md).
Outputs: `/Users/zhenyuwu/arepo_rd/local_runs/p1_active_transfer_20260909`.
No production C or thesis changes, no new Euler PDE/MPI run; native FV remains
parked. All moving tests here are synthetic 2D topology with prescribed motion.

## 15. 2026-09-10: positivity blocks promoting the active-only remap

> The consolidated positivity decision and comparison of the three topology
> schedules are in section 16 below. Current development continues in this
> localMac log; volume 2 remains the historical moving-mesh record.

The user correctly identifies positivity as a material acceptance condition.
The active-only topology map can make admissible input states nonphysical,
even if the N transport update itself is assumed positive. This is a failure
of the composed method, not a counterexample to the original N residual.

A sharper exact-arithmetic counterexample uses density contrast only 4:
unit-square AC->BD, equal exterior nodal weights 1/12, active A,C and inactive
B,D. Old/new full weights are (5/12,1/4,5/12,1/4) and
(1/4,5/12,1/4,5/12). Old densities (1,4,1,4), zero velocity and constant positive
pressure are admissible. Old total mass is 17/6; keeping the inactive densities
fixed after the basis change requires mass 10/3 on those two nodes alone.
The required active total is therefore -1/2. No active weights or positivity
limiter can satisfy this constraint. The check used Python fractions.Fraction.

The full-patch convex low-order map instead gives positive densities
(5/3,12/5,5/3,12/5), conserving 17/6 exactly. It changes inactive primitives,
so its direct use does not solve asynchronous frozen-state consistency.
This distinguishes a too-restrictive active-only design from an impossibility
of all conservative positive P1 transfers.

Decision: retain interval closure/frozen-until as a conditional conservation
result, but do not promote active-only remap to a robust main scheme. A positive
transfer with a consistent asynchronous ledger interpretation is required
before this route can be accepted. Current equal-step unlimited high-order
repair also checks and aborts on nonphysical output; its previously derived
convex fallback is not wired into the inspected production C path.
Details and proof are appended as §9 of
[`RD_P1_deep_hierarchy_topology_20260909.md`](RD_P1_deep_hierarchy_topology_20260909.md).
No solver/thesis changes or new Euler PDE run were made.

## 16. 2026-09-10: positivity and comparison of three topology schedules

This consolidates the discussion and bounded experiments in sections 13--15.
Per the user's logging convention, all current work is appended to this
localMac volume. The temporarily misplaced volume-2 addendum has been moved
here, and volume 2 restored without changes. Source baseline for the tests:
`75c3d6ac65b8edce2741a372fc9507dacf22151e`. No production C or thesis files were
changed in this research sequence.

Terminology clarification: local interval closure shortens the affected
triangle's actual integration interval at a topology event. It does not change
the CFL coefficient itself, and does not by itself move all coarse vertices
to finer own-state bins or wake them up. A smaller integration interval alone
also does not remove the active-only transfer's positivity obstruction.

### Acceptance decision: active-only remap is not a robust positive scheme

The user identifies positivity as a critical requirement. Even assuming a
positive N transport update under its applicable conditions, an additional
non-positive topology transfer can destroy positivity of the composed method.
The counterexample concerns the added transfer, not a refutation of the
original N residual. Passing scalar conservation and uniform-flow checks
does not resolve this objection.

The restricted candidate keeps inactive primitives U frozen and preserves
their accumulated non-geometric ledger Q-gU. With delta m the same-time P1
mass change, D=sum delta m_i U_i, and unit-sum weights supported only on active
vertices, the map is

    delta g_i = delta m_i,
    delta Q_i = delta m_i U_i - w_i D,
    w_i = 0 for inactive vertices.

Only active vertices recover a new U. The map conserves total Q, but its
required active total can be outside the Euler admissible set. Changing
weights or applying a limiter cannot repair an infeasible total.

Exact example: unit-square AC->BD, exterior nodal mass contributions 1/12,
active A,C, inactive B,D. The old/new full nodal masses are

    m^- = (5/12, 1/4, 5/12, 1/4),
    m^+ = (1/4, 5/12, 1/4, 5/12).

For densities (1,4,1,4), zero velocity and constant positive pressure, all
input Euler states are admissible. Old total mass is 17/6. Keeping the
inactive densities fixed after the geometric transfer requires 10/3 on those
nodes alone, so the required active total is -1/2. This exact-arithmetic
obstruction is independent of a transport CFL reduction that leaves the same
active set and forced flip in place.

With all nodes allowed to change, the established low-order patch-average
transfer gives positive densities (5/3,12/5,5/3,12/5), conserving 17/6 exactly.
Thus positive conservative P1 transfer is possible; the active-only restriction
is the obstruction in this example. Directly changing inactive U, however,
would violate the frozen time history unless the time algorithm is changed.

**Decision:** retain local interval closure and frozen-until as conditional
conservation findings, but do not promote active-only remap as the robust main
scheme. A positive transfer with a consistent asynchronous interpretation is
required. Allowing inactive conserved ledgers to share corrections while U
stays frozen is a possible next investigation, not a proved solution.

### Definitions shared by the three schedules

P is a complete changed cavity; for one 2-to-2 flip it contains four vertices.
Vertex h_i is the own-state update period. The existing natural triangle period
is h_T=min_{i in T} h_i. Inactive vertices keep their residual-evaluation state
U fixed, but can still receive Q and g increments, and their positions continue
to drift. Keeping old RD connectivity does not freeze the geometry. Native
AREPO Delaunay connectivity may already have changed while RD retains old
triangles for its own integration.

### Comparison of the three proposed schedules

| Question | 1. Wait for all cavity vertices | 2. Change active states only | 3. Add local interval closure |
|---|---|---|---|
| When may RD adopt the flip? | All vertices in P reach their own natural step endpoints | All removed and inserted triangles have aligned natural interval boundaries | A selected event time, after explicitly closing removed triangles to it; active correction support and valid geometry are required |
| How is old transport finished? | Normal due sweeps; every incident triangle of P has finished | Normal due sweeps; all changed triangles and all triangles incident to modified active states have finished | Normal due sweeps plus forced partial sweeps of removed triangles not naturally due |
| Who changes U at remap? | All P vertices, which are active now | Only active P vertices | Only active P vertices in the tested version |
| What happens to inactive P vertices? | There are none at the transfer time | U stays frozen; Q and g receive geometric transfer increments | Same transfer rule as option 2; also latch frozen status through the end of the current own interval |
| Does it change triangle interval lengths? | No | No: acceptance occurs on compatible boundaries | Yes: use actual last-integrated/birth times; first new-triangle interval can be shorter than h_T |
| Principal cost or failure | Waiting may degrade old geometry | An isolated fine node may still wait a long time; active-only positivity can be impossible | Persistent interval/frozen history is needed; the active-only positivity obstruction remains |
| Positivity status | A conservative positive low-order same-time transfer exists for admissible inputs and a valid cavity; it must actually be used/limited | No unconditional positive transfer under the tested active-only constraints | No improvement to transfer positivity merely from closing intervals |

For option 1, synchronizing P need not synchronize the entire domain. The
existing full-mass high-order correction is not itself an unconditional
positive map: the positive low-order endpoint/common-alpha fallback is a
separate requirement. The inspected production equal-step C code currently
aborts on an inadmissible high-order result rather than applying that fallback.

For a single four-point flip with fixed aligned dyadic vertex periods sorted
as h_(1)<=h_(2)<=h_(3)<=h_(4), option 1 uses a common boundary of h_(4), whereas
option 2 uses a common boundary of h_(2). The four old/new triangles exhaust
the four three-point subsets, so max_T min_{i in T} h_i=h_(2). General cavities
must use their actual removed/inserted triangles rather than this shortcut.

Option 3 is option 2's state-transfer choice plus an additional time-history
mechanism; it is not an independent cure for positivity. A removed triangle
integrates [last_time,event_time], and a new triangle starts at event_time.
The predictor and corrector must use the same interval. A touched inactive
vertex remains frozen through its current own-step endpoint, even if its new
star would otherwise classify it as live. Without that latch, the endpoint
predictor can act on an interval history that no longer matches it.

### Simple timeline and evidence limits

In the smooth scalar toy tests, all clocks begin at zero and a flip is
requested at t=h. The following are tested adoption times, not a promise
that an arbitrary Euler state passes the active-only positivity check:

| Four vertex periods | Option 1 | Option 2 | Option 3 |
|---|---:|---:|---:|
| h,2h,256h,1024h | 1024h | 2h | h |
| h,1024h,1024h,1024h | 1024h | 1024h | h |

All three still require valid old geometry over the intervals actually used.
None repairs a triangle that already inverted between events. Option 3 also
cannot use the tested active-only map if the active correction set is empty.

The independent scalar campaigns support conditional conservation:

- `audit_p1_patch_sync.py`: 192 combinations, including unsafe controls;
  patch-synchronous global-sync mass error <=4.45e-16.
- `audit_p1_active_transfer.py`: 192 standard and 8 deep-bin combinations;
  standard active-only mass error <=4.45e-16. Separate random Euler *state
  transfers* and the exact counterexample establish the positivity limitation.
- `audit_p1_event_flush.py`: 128 standard and 8 deep-bin combinations;
  complete interval/freeze rules give mass error <=2.00e-15. Removing the
  frozen-until latch gives error up to 2.32e-6 in the controls.

These are synthetic 2D flips, fixed bins and prescribed linear trajectories.
They are not Euler PDE, actual cosmological, changing-bin or MPI validation,
and do not establish second-order time accuracy. Native FV/corner RD remains
parked at its existing Python algebra checks as possible future work.

Detailed derivations and provenance:
[`RD_P1_patch_synchronization_20260909.md`](RD_P1_patch_synchronization_20260909.md),
[`RD_P1_deep_hierarchy_topology_20260909.md`](RD_P1_deep_hierarchy_topology_20260909.md),
and sections 13--15 above. Raw campaigns are under
`/Users/zhenyuwu/arepo_rd/local_runs/p1_patch_sync_20260909` and
`/Users/zhenyuwu/arepo_rd/local_runs/p1_active_transfer_20260909`.

## 17. 2026-09-10: independent review of the topology/hierarchy proposals, with two corrections to section 16 and two to my own first pass

**Author:** Claude Code (Opus 5), at Zhenyu's request. **Baseline:**
`75c3d6ac65b8edce2741a372fc9507dacf22151e`. No production C or thesis file was
changed; no Euler PDE, MPI or cosmological run was performed. Every number
below comes from synthetic 2-D algebra or prescribed-motion point sets, and the
new scripts are listed in 17.8.

This section reviews sections 10--16 and the four design documents, answers
Zhenyu's two follow-up questions, and records two places where my own first
pass was wrong.

### 17.1 Native Voronoi RD: park it, and the reason is not only cost

I concur with the user's decision and with the parking recorded in section 12.
Three specific grounds, beyond the size of the change:

1. **The cited support does not cover the intended use.** Gaburro, Ricchiuto
   and Dumbser (arXiv:2506.00207v2) construct corner fluxes on a *static* mesh
   over *barycentre-based* Voronoi-like polygons with an auxiliary residual
   triangle, not AREPO's circumcentric Voronoi cells. A true-Voronoi ALE + LTS
   corner scheme has no published foundation. Section 12 states this; it is a
   reason to stop, not merely a caveat.
2. **"Voronoi has no volume jump" is only half an argument.** The cell area is
   continuous at a generic flip, but the corner *stencil* is not: a Delaunay
   triangle appears or disappears, and the closure identity (7) of
   `RD_moving_representation_design_20260909.md` needs rank-2 corner normals,
   which fail exactly at the >3-cell degenerate corner that a flip passes
   through. The genuine gain is that the discontinuity no longer moves
   conserved mass; it is not that the flux construction becomes smooth.
3. **Nothing from Chapter 4 transfers.** LDA/F1, the B blend and both
   Campoli/Arpaia temporal-mass forms are tied to the nodal representation.
   Conservation, GCL, positivity and convergence would all be re-derived.

The one idea worth keeping is section 12's observation that a face-based
representation makes LTS conservation *transactional* rather than dependent on
cancellation between differently scheduled triangle histories. That belongs in
the thesis as motivation for future work. It does not justify a prototype now.

### 17.2 Correction to my own first pass: exact patches are not the fix

In my first response to Zhenyu I proposed promoting
`RD_ALE_EXACT_PATCH_DIAGNOSTIC` from a scratch-array diagnostic to the applied
path, on the strength of section 71.5's hypothesis A (the union-find support
detector merges independent flips through unchanged triangles). **That work has
already been done and it did not fix the problem.** `Aug26_update.md` section
2.5, summarising the volume-2 sections missing locally, records:

- the exact old/new triangle-key diagnostic was implemented and run;
- merging was real but involved only about **3--5%** of patch instances;
- **the largest local corrections persisted on exact, unmerged patches**, with
  `max|dU| ~ 0.1038` against `0.1065` for the merged detector.

So hypothesis A is largely rejected and hypothesis B (section 73.3, my own) is
largely confirmed. I withdraw the recommendation. It was an error of reading:
the relevant evidence is in the August 26 handoff rather than in local volume 2,
whose copy still ends at section 73.

`Aug26_update.md` section 2.5 also proves the weight choice is optimal in its
own norm: the full-mass weights are the unique solution of

    min 1/2 sum_i mhat_i |dU_i|^2   subject to   sum_i mhat_i dU_i = -D_P,

giving the uniform patch shift `dU_i = -D_P / sum_j mhat_j`, which is also the
minimax correction. **No reweighting can beat it under that objective.** I
tested a first-moment-constrained reweighting and record it as refuted in 17.4.

### 17.3 Is the interface price avoidable? Separating "intrinsic" from "unbounded"

Zhenyu asks whether the earlier attribution -- discretisation error meeting a
discontinuous state, hard to avoid -- leaves any good option. The attribution is
correct as far as it goes, but it conflates two statements that have different
consequences.

The exact identity behind it (section 73.1) is linear exactness,

    D_P = sum_i dm_i ( U_i - L(x_i) )   for every affine L,

verified here to `1.4e-15` over 20000 random convex flip cavities, with the
zeroth and first moment identities at `5.8e-16` and `3.4e-16`
(`audit_flip_transfer_moments.py`). It gives

- smooth patch: `D_P = O( sum|dm| h_P^2 |grad^2 U| )`;
- layer of width comparable to `h`: no affine fit removes the variation, so
  `D_P = O( sum|dm| [U] )`.

The second line is what was measured. But **the KH layer width `W = 0.025` is a
fixed physical scale**, so `W/h` grows under refinement and the second regime
must give way to the first. Held at fixed `W` and refined `h`, the idealised
patch model in `audit_flip_transfer_resolution.py` gives observed orders
`1.81, 2.52, 2.86, 2.96` between successive halvings, approaching the
linear-exactness rate once `W/h > 2`.

**Caveat, stated plainly:** that model yields about `5e-3` at the glass48 row,
roughly **20 times smaller** than the `0.104` measured on a real unmerged KH
patch. A single tanh layer on a near-square quad is not a late-time KH braid,
and the reported `max|dU|` is a maximum over four conserved components of
different scale. The constant is therefore *not* validated; only the scaling
is, and the scaling rests on the exact identity above rather than on the model.

The consequence is nevertheless decisive for the acceptance question:
**hypothesis B does not say the operator is inconsistent; it says the price is
a function of `W/h`.** Whether the price vanishes under refinement is a
measurement that has never been made. Section 73.3 gate 3 proposed it, and
neither it nor gate 1 (smooth Gresho/Sod/Yee regressions with repair applied,
estimated then at an afternoon) appears anywhere in volume 2 up to section 73,
in `Aug26_update.md`, or in this volume.

One real risk to record against this: late-time KH rolls up and generates
structure down to the grid, so the *effective* local `W` need not stay fixed. A
resolution study run to `t = 10` may therefore show no convergence for reasons
that have nothing to do with the operator. Section 73.3 gate 2 already
anticipates this by proposing the matched comparison at `t = 2`.

### 17.4 What is actually still open: the correction is extremum-creating

Minimum norm is not minimum damage. The uniform shift moves **all four patch
nodes by the same amount**, so for any component with `D_P != 0` the patch
minimum (if `D_P > 0`) or maximum (if `D_P < 0`) is pushed outside its old
range. This is unconditional, not occasional, and was confirmed on 100% of
samples in `audit_flip_transfer_dmp.py`.

That is a better match to the section-71.4 symptom than a diffusive price is.
The entropy excursion grew from `0.183` to `0.655` at `t = 2` and stayed 3--5x
the control at every later time. Mixing at fixed conserved totals moves states
*into* the local hull and cannot create excursions outside it; a sign-coherent
shift can and does.

The low-order endpoint of section 68.11 is, by contrast, a convex combination:

    U_i^L = (m_{i,out}/m_i^+) U_i^- + (m_{i,P}^+/m_i^+) Ubar_P ,
    m_i^+ = m_{i,out} + m_{i,P}^+ ,

with both coefficients non-negative and summing to one, and `Ubar_P` itself a
convex combination of the old patch states. Since the Euler admissible set is
convex, `U^L` lies in the hull of `{U_j^-}`: it can neither go inadmissible nor
create a new extremum. Section 73.2 answer 5 established the admissibility half;
the hull property is the stronger statement and is what matters here.

**The proposal that survives** is therefore to keep the existing high-order map
and existing common-`alpha` machinery, but to choose `alpha` under a *relaxed
discrete maximum principle* as well as positivity: allow the patch states to
leave their old range by at most a small tolerance times the patch range.
Conservation is exact for every `alpha`, so this costs nothing in the conserved
totals; it costs linear exactness only where the bound binds, which by 17.3 is
only where `W/h ~ 1`. `alpha = 0` always satisfies the bound, so the limiter can
never fail to find a value.

**Two proposals I tested and am recording as refuted or unsupported:**

1. *First-moment-preserving weights.* The correction enters as `w_i D_P`, so
   when `D_P` is small the weights have no leverage on the first moment at all.
   The exactly aligned case `U = (1,1,2,2)` has `D_P = 0` and zero correction,
   yet the lumped first moment still changes by `1.667e-1` purely from the
   basis change. Reweighting cannot address that, and it is anyway ruled out in
   its own norm by 17.2. Refuted.
2. *Exact local L2 overlap projection as a drop-in operator.* My first
   construction of it was wrong: restricted to the flip quad it conserves the
   quad integral, not the lumped ledger that includes each node's exterior mass,
   and it moved nodes B and D by `0.5` because most of their support lies
   outside the quad. It remains valid as the *offline arbiter* proposed in
   section 73.3, but it needs a star-wide, lumped-consistent formulation before
   it can be compared with the patch operator at all. Not attempted here.

### 17.5 Correction to my own first pass: the a-posteriori fallback was shelved

Zhenyu is right to challenge this. In my first response I wrote that this
solver's positivity strategy "is already a-posteriori", citing
`RD_ALE_APOSTERIORI_FALLBACK` at `residual_distribution_solver.c:5690`. **That
is wrong and I withdraw it.** The record is:

- section 52 implemented the MOOD-type local LDA-to-N a-posteriori retry;
- section 52.6 / 54 found the per-step positivity-and-mass-ratio detector fires
  too late, because the moving-LDA KH failure is a **secular, monotone,
  single-signed** precursor (minimum density `0.98, 0.94, 0.84, 0.53, 0.31` from
  `t = 0.2` to `1.0`) to which a per-step *ratio* test is structurally blind;
- by the time it fires, the incoming star state is already contaminated, so
  even a full N-star recompute is negative -- growing the halo from 6 to 1128
  triangles left the bad nodal value unchanged;
- volume 2's own summary table calls it "useful debug tool, ... **not a
  production fallback**";
- section 55 candidate 3 was designed to decide whether MOOD survived at all,
  and section 56 chose the scalar-B sprint instead;
- the flag appears in exactly one Config,
  `examples/shocktube_2d/Config_KH_APOSTERIORI_f050.sh`, and in no production
  Config.

So there is no established a-posteriori positivity strategy to appeal to.

**Why the 17.4 recommendation nevertheless stands.** The transfer limiter is
not a MOOD fallback and does not inherit its failure mode. MOOD failed on a
*detection* problem: it had to notice slow contamination of a transported
solution, and it noticed too late to repair anything. The transfer limiter has
no detection problem:

| | section-52 MOOD | transfer `alpha` limiter |
| --- | --- | --- |
| what is judged | a completed timestep's solution | one closed-form algebraic map |
| input validity | unknown, possibly already bad | admissible by construction |
| when applied | after the step, by rollback | before committing, in place |
| fallback existence | hoped for; an N star can also fail | proved: `alpha = 0` is in the hull |
| tuning | a threshold that must fire in time | a tolerance on an explicit bound |

It is a limiter in the sense of a slope or invariant-domain limiter, not an
a-posteriori rollback. The honest residual risk is the same one MOOD has -- the
choice of tolerance -- but here a wrong tolerance costs accuracy at the flip,
not an unrecoverable state.

### 17.6 Positivity of the transfer, recomputed

Section 16's counterexample takes the four exterior lumped contributions as
`1/12`, i.e. a vertex owned almost entirely by the flip cavity. In a regular
star the cavity owns only `2/n` or `1/n` of a vertex's mass. Recomputing the
production map's critical density contrast exactly
(`audit_flip_transfer_positivity.py`, Python `fractions`):

| triangles per vertex | patch mass M | critical contrast r* |
| ---: | ---: | ---: |
| 3 | 2 | 7 |
| 4 | 8/3 | 9 |
| 6 (regular) | 4 | **13** |
| 8 | 16/3 | 17 |
| section-16 parameters | 4/3 | 5 |

Random admissible Euler patches with a 6-neighbour star, 4000 per row:

| density contrast | high-order admissible | low-order admissible | median limiting `alpha` |
| ---: | ---: | ---: | ---: |
| 2 / 4 / 8 | 1.0000 | 1.0000 | -- |
| 13 | 0.9948 | 1.0000 | 0.968 |
| 20 | 0.8938 | 1.0000 | 0.921 |
| 50 | 0.5645 | 1.0000 | 0.775 |

So the equal-step repair's clean record on KH (density ratio 2), Gresho and Yee
is structural, not luck. It is still not unconditional, and `:2342` aborts
rather than limiting. When the limiter does engage it takes `alpha ~ 0.97`, so
the accuracy cost is negligible; this is the same machinery 17.4 needs.

### 17.7 The active-only map, and how long a stale triangle may be kept

**An algebraic identity worth recording.** Section 16's active-only map with the
weight support widened to the whole patch, `w_i = m_i^+ / M`, reduces to

    Q_i^+ = m_i^+ U_i^- - (m_i^+/M) D   i.e.   U_i^+ = U_i^- - D/M,

which is exactly the production map at `residual_distribution_solver.c:2272-2320`.
I found this by testing it as an independent scheme and obtaining bit-identical
results. Consequently section 16's "possible next investigation -- allow the
inactive conserved ledger to share the correction" is **not a new operator**; it
is the existing repair applied to `Q` with the primitives left frozen. Letting
inactive nodes receive `Q` and `g` increments while `U` stays frozen is what the
frozen-star hierarchy already does, and what native AREPO FV does for inactive
cells (Springel 2009, section 7.2). The invariant `Q_i - g_i U_i` that section 16
preserves is a bookkeeping convention, not a physical requirement; preserving it
is what makes the problem infeasible. The genuine open cost is that positivity
is then checked only when the node wakes, with no way to re-limit the transfer
retroactively -- that is unproved and should be recorded as such.

**How long may RD retain a post-flip triangle?** The N distribution is LED under
`dt <= |T| / sum_i k_i^+` on any non-degenerate triangle; Delaunay is not part
of that hypothesis, and the lumped `DualArea = sum_T A_T/3` is positive whenever
areas are. So delaying a flip does not break N's positivity structurally. What
it does is tighten that triangle's own bound, since `|T| / sum k_i^+` scales
with the inradius. Measuring the window on moving point sets with Lagrangian
velocity plus Lloyd-type regularisation capped at `CellShapingSpeed = 0.5 c_s`
(the value in every tracked KH/Gresho parameter file), by two independent
methods -- step-by-step tracking and event-time frozen-velocity extrapolation:

| field | regularisation | median age at `dt_N -> 50%` | 5th percentile | median at inversion |
| --- | --- | ---: | ---: | ---: |
| KH | chi = 0.5 | 3.3--5.9 | 0.3--2.0 | 5.3--14 |
| KH | chi = 0 | 32--33 | 17--18 | 67--79 |
| Gresho | chi = 0.5 | 1.5--3.3 | 0.1--2.0 | 1.0--5.5 |
| Gresho | chi = 0 | 58--66 | 36--39 | 96--100 |
| RT | chi = 0.5 | 1.4--4.0 | 0.1--1.7 | 1.8--8.0 |

All ages are in local CFL steps. A hierarchical wait of one coarse step costs
`2^k` of them. Even on the most favourable row the 5th percentile is 17--39,
i.e. a bin ratio of at most 8--16; with regularisation active it is 2--4.

**Therefore options 1 and 2 of section 16 are bounded to shallow hierarchies.**
Their failure mode worsens precisely as the hierarchy deepens, which is when the
hierarchy is wanted. Option 3, closing intervals at the event, needs no wait and
is the only one whose geometric safety does not degrade with bin depth. Section
16 treats option 3 as also blocked by positivity; that couples two separable
axes. The comparison is better drawn as 2 x 3, `{correction support: active-only,
full patch} x {adoption time: wait-all, wait-h(2), event closure}`, which shows
the blocked cell is the whole active-only column.

**Limits of this measurement.** My Lloyd drift is applied to every point every
step, unlike AREPO's `MaxFaceAngle > 0.75 * CellMaxAngleFactor` gate, so it is
more aggressive than production. Its flip rate, about 2% of triangles per CFL
step, is about 40x the rate in the real KH run, where section 71.3 records 79033
replaced edges over 31502 steps, about 2.5 per step, with per-step maxima of 12
edges, 11 patches and 46 affected nodes. The true retention window lies between
the two chi rows. The flip *rate* matters separately: at 2.5 edges per step on
roughly 4600 triangles, waiting `2^k` steps leaves about `5 * 2^k` triangles
pending, which is a few per cent at `k = 5` and exceeds the whole mesh at
`k = 10`.

Two interactions neither design document raises: vertex time bins shrink where
shocks form, which is where flips are dense, so a pending cavity's target
synchronisation time moves during the wait (`timestep.c:199` iterates active
particles only); and a pending cavity can straddle a rank boundary with
particles migrating mid-wait.

### 17.8 Recommended order, and reproduction

The ordering changes from section 16's, mainly because 17.2 removes the
locality fix and 17.3 identifies a cheaper decisive measurement.

| priority | item | why |
| --- | --- | --- |
| P0 | Section 73.3 gate 1: smooth Gresho/Sod/Yee regressions **with repair applied**, checking corrections are `O(h^2)` and metrics move by about a per cent | proposed 2026-08-25, never run, an afternoon locally, and it separates "operator defect" from "under-resolution price" without any long run |
| P0 | Section 73.3 gate 3: a matched short repair/control pair at glass48 and glass96, KH to `t = 2`, asking whether the divergence *shrinks with resolution* | the measurement that decides whether the repair can ever be the default; never run at any resolution |
| P1 | Choose the existing common `alpha` under a relaxed DMP as well as positivity (17.4), and replace the `:2342` abort with it | conservation is exact for every `alpha`; targets the measured entropy excursion; `alpha = 0` always exists |
| P2 | Publish the equal-step moving-mesh result with its scope stated by the P0 outcome | this is the part of Chapter 4 that can stand |
| P3 | Hierarchy: option 3 (event-time interval closure with the frozen-until latch) with **full-patch** correction support, single rank, Campoli, prescribed motion, fixed bins | the only schedule whose geometry does not degrade with bin depth; reuses the existing map rather than a new one |
| -- | Record as limitations: MPI + topology + hierarchy together, deep cosmological bin ratios, second-order multirate accuracy, native Voronoi corner RD | scoping honestly is better than passing one conservation gate |

New scripts, all NumPy-only, in `tests/rd/`:

```sh
PY=/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python
$PY tests/rd/audit_flip_transfer_positivity.py    # 17.6 exact thresholds + Euler scan
$PY tests/rd/audit_flip_transfer_moments.py       # 17.3 moment identities, linear exactness
$PY tests/rd/audit_flip_transfer_dmp.py           # 17.4 extremum creation, relaxed-DMP alpha
$PY tests/rd/audit_flip_transfer_resolution.py    # 17.3 scaling with W/h, with its caveat
$PY tests/rd/audit_flip_retention_window.py       # 17.7 fast event-time estimate
$PY tests/rd/audit_flip_retention_tracked.py      # 17.7 step-by-step tracking, ~6 min
```

Outputs, SHA256 provenance and the baseline commit are retained in
`/Users/zhenyuwu/arepo_rd/local_runs/topology_review_20260910`. These are
synthetic 2-D flips, prescribed trajectories and patch algebra. They are not
Euler PDE, MPI, changing-bin or cosmological validation, and they establish no
statement about time accuracy.
