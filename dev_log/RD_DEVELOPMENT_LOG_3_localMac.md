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
