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
| 18 | Full-patch actual-ledger remap; instantaneous positivity versus remaining frozen outflow |
| 19 | Reassessing Colombo--Re: published P1 geometry, implicit time coupling, and AREPO port cost |
| 20 | Test branch: explicit geometric generator, local nodal closure, five-agent validation and C kernel |
| 21 | Native CR-inspired Euler tests, limited high repair, RK2 dissipation audit and Campoli controls |
| 22 | Sod actual Nx=48 (full box 96²): matched N/LDA RK2 topology comparisons and OpenMP runtime correction |
| 23 | High-repair semantics, LDA velocity ablations and older Sod plotting conventions |
| 24 | Actual Sod resolution and glass controls: GL/F1 undershoot and contour scatter without flips |
| 25 | Baseline first: four Heun paths, temporal versus spatial accuracy, and historical decisions |

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

## 18. 2026-09-10: review of Claude §17; positive full-patch ledger transfer and the remaining frozen-outflow obstruction

User requested a careful reading of Claude's latest comments, especially the
different positivity interpretation, and continued work on P1 moving-mesh
hierarchy. Two independent reviews and two small Python audits were used.
This entry follows the current logging convention: volume 2 is unchanged.
No production C or thesis files were modified, and native FV/corner RD remains
future work. Detailed derivations and counterexamples are in
`RD_P1_full_patch_ledger_20260910.md`.

### 18.1 What the review changes, and what it does not

**Claude is right that topology adoption time and correction support are
independent choices.** The active-only counterexample in §§15–16 does not
disprove event-time interval closure with full-patch correction. Keeping an
inactive residual state U frozen does not physically require keeping Q-gU
unchanged. The latter was an extra restriction of our previous transfer.

Four qualifications to §17 are necessary:

1. The regular-star density threshold r*=13 in §17.6 concerns the full-patch
   high-order uniform shift, not the active-only map. Even with old complete
   nodal masses (1,1,1,1), new masses (5/6,7/6,5/6,7/6), A,C active and
   rho=(1,r,1,r), the active mass target is 2-r/3. It is negative for r>6;
   r=8 gives -2/3. The active-only obstruction is not an artefact of tiny
   exterior masses.
2. Low density contrast alone does not imply Euler positivity of the full
   high map. On that same regular star, gamma=1.4, rho=p=1, vx=(4,-4,4,-4)
   and E=10.5 give high-map pressures (-7/45,89/45,-7/45,89/45). The prior
   low-velocity random scan cannot establish a theorem for arbitrary Euler
   states, nor does this counterexample invalidate the actual KH test data.
3. The §17.7 operator identity omits the asynchronous history remainder:
   Q+=Q-+delta_m U-wD=m+ U+(Q--m- U)-wD. Equivalently the remainder is
   Q--g- U when written with the actual geometric ledger. Only when it
   vanishes does this reduce to the synchronous production map. A synchronous
   low-map increment applied to arbitrary admissible Q need not remain
   positive; the detailed note gives an algebraic counterexample and does
   not claim its arbitrary input has been dynamically reached.
4. A convex hull of conserved vectors bounds conserved components, not the
   maxima of nonlinear pressure or specific entropy. The positive low map
   for the opposite-velocity example above gives p≈(1.7964,2.9737,...),
   although all old p=1. This is kinetic-to-internal-energy conversion during
   conservative mixing. A relaxed component DMP is a valid extra condition,
   but it does not by itself control the recorded KH entropy excursion.
   Adding an entropy upper bound requires a separate feasible-endpoint proof;
   alpha=0 is not automatically a fallback for that bound.

The existing production transfer still aborts on inadmissibility rather than
using the proposed positive low endpoint. The candidate limiter must not be
described as an established production MOOD or positivity strategy.

### 18.2 A full-patch transfer using the actual asynchronous ledger

Under the fixed-bin endpoint-ledger/event-closure model, the geometric ledger
has the exact interpretation

    g_i = sum_{T contains i} A_T(s_T)/3,

where s_T is each triangle's last integrated time. Flush all removed triangles
to the event before transferring. If a_i and b_i are the changed patch's old
and new masses at that event, o_i=g_i-a_i is the non-negative contribution of
unchanged triangles at their own times. Thus g_i+=o_i+b_i. At a normal active
vertex all incident intervals have ended, so g_i=m_i(t). This relies on valid
geometry and consistent history; it is not a licence to reset away a large
geometric closure error or the separate Arpaia storage defect in §10.

Define W_i=Q_i/g_i, distinct from the frozen residual U_i. A conditional
positive low endpoint is

    Wbar = sum a_i W_i / sum a_i
    Q_i^L = o_i W_i + b_i Wbar.

For sum a=sum b it conserves total Q. For admissible W and non-negative
geometric weights, Q_i^L/g_i+ is a convex combination and is Euler-admissible.
Constant states are preserved. This remap does not require an active node
inside the cavity. A corresponding high candidate is

    D_g = sum (b_i-a_i) W_i,    G = sum g_i+
    Q_i^H = g_i+ (W_i-D_g/G).

A common-alpha blend preserves conservation and can enforce admissibility
and explicitly chosen conserved-component bounds. Inactive U remains frozen;
only naturally active vertices recover U. The frozen-until latch remains
necessary. Equal-time g=m, W=U recovers the earlier synchronous endpoints;
asynchronous W is a mixed-history ledger, so this does not establish time
accuracy or that the high endpoint is high order in the full method.

The algebra audit passed 2000 wide-distribution Euler input samples with a
2% component relaxed DMP: maximum relative conservation error 3.28e-16 and
uniform-state error 5.21e-16. There were 1445 inadmissible high endpoints and
1992 limited samples, minimum alpha 0.1391. These are synthetic sampling
counts, not physical failure rates; incoming W admissibility is assumed.

### 18.3 A positive remap can still make the remaining coarse step negative

The independent time-integration audit uses the existing scalar N residual on
a static periodic 4x4 vertex mesh, one synthetic diagonal change at tick 1,
one fine node and a 1:8 hierarchy. One inactive node starts at U=1 and the
others at 0.01. Both old and new nodal CFL minima are 0.5208333333; the coarse
step is H=0.95 times this bound. Removed intervals are flushed, new elements
start at birth, and touched inactive states stay frozen to their own endpoint.

| Method | Transfer input/output | Minimum state at coarse endpoint |
|---|---|---:|
| Fixed old connectivity | no transfer | 0.01 |
| Full-patch convex low ledger remap | both positive | **-0.03443564406** |
| Remaining-outflow-reserving low remap | both positive | 0.01 |

In the failing case every calculated predictor state is also positive, minimum
0.01. Total mass is conserved and orphan/prebirth interval counters are zero.
The remap leaves the high inactive node with Q=0.05627031762, while its still
frozen U=1 owes future outgoing contributions of 0.059375. Subsequent inflow
does not make up the shortfall. Thus instantaneous remap positivity is not a
sufficient condition for positivity of the asynchronous composition. Merely
cutting a removed triangle's interval does not shorten the coarse node's
remaining frozen interval.

### 18.4 A conditional scalar construction that reserves future outflow

For static scalar N, Phi_iT=k_iT^+(U_i-U_in,T), with k_iT^+ non-negative.
For an inactive node frozen to its own endpoint t_i,end, define after adoption

    lambda_i = sum_{T contains i} k_iT^+ (t_i,end-s_T)
    R_i = lambda_i U_i.

The starts s_T include all outstanding unchanged-triangle intervals, including
ones beginning BEFORE the flip; event-to-end alone is insufficient. At tick 1
the example still owes as much as 8h, not 7h. Active nodes have lambda=0.
Provided

    d_i^- = g_i^- - lambda_i > 0,    d_i^+ = g_i^+ - lambda_i > 0,
    S = sum_P (Q_i-R_i) >= 0,

one simple whole-patch low endpoint is

    Q_i^L = R_i + d_i^+ S / sum_P d_i^-.

Since sum d^+=sum d^-, this is conservative, preserves a uniform state, and
leaves Q_i>=R_i. With fixed future coefficients, no later event changing the
budget and non-negative incoming stage states, the inactive node can pay all
remaining frozen outflow without becoming negative. Strict positivity uses
S>0 and d_i^+>0. It is deliberately diffusive, not linear-exact, and is not
the outside-preserving map of 18.2. A future high/low limiter would need to
enforce the reserve, not just Q>0; that limiter was not implemented here.

If S<0, no redistribution confined to this patch can satisfy all these
reserves while conserving Q. The construction also requires positive d.
This may require a wider patch, prospective timestep restriction at legal
node boundaries, or actual closure of affected nodal intervals. It cannot
be fixed by clipping. The reserve is sufficient rather than necessary: a
budget shortfall need not produce a negative state if inflow compensates.

All 24 diagnostic combinations (theta=.5,.8,.9,.95; constant/nonconstant;
three modes) met their expected assertions, including the negative control.
Maximum mass error was 1.39e-17 and uniform error 1.11e-16. Only one flip and
one coarse cycle were advanced. This is not a moving Euler positivity proof:
moving geometry requires future coefficient/volume bounds, and Euler matrix
N splitting cannot be treated as a scalar non-negative outflow coefficient.
Density reserves alone would not establish pressure positivity.

### 18.5 Engineering direction and remaining decisive work

The leading P1 candidate is now event-time triangle closure + full-patch
actual-ledger transfer + a constraint on the remaining frozen interval.
It retains existing P1 geometry, RD residuals and extensive increment paths;
it is more than simply calling the equal-step repair on inactive nodes.
Before production changes, the decisive mathematical task is to establish
usable remaining-interval admissibility conditions for the actual Euler
N/RK/ALE update, or show why local nodal interval closure is necessary.
The static scalar lambda formula must not be copied directly into Euler C.

Persistent triangle IDs/winding and birth/last times, common actual intervals
for both RK stages, frozen-until, actual Q/g and old/new cavity masses remain
the principal bookkeeping changes. AREPO can build the new Delaunay mesh
normally while RD retains deleted elements only to finish their histories;
this avoids making AREPO retain a long-lived non-Delaunay Voronoi mesh.
Validity of old elements throughout their outstanding interval is still
required. Closing whole nodal intervals would also need compatible shared
traces and predictors and may enlarge the synchronization region; it is not
yet a proved cheap wakeup operation.

MPI adds ownership, old-element halo, event agreement and exactly-once
increment/migration work rather than a new fluid formulation. The isolated
earlier MPI prototype does not validate these persistent topology histories.
Single-rank mathematics still precedes this integration. Campoli endpoint
storage is the initial control; Arpaia's separate §10 rebase issue remains.
No second-order multirate claim or cosmological conclusion follows here.

Reproduction from the repository root:

```sh
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/audit_p1_ledger_remap.py
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/audit_p1_ledger_future_outflow.py
```

The second imports existing audit helpers and needs SciPy as well as NumPy.
Raw outputs, summary and SHA256 provenance are retained under
`/Users/zhenyuwu/arepo_rd/local_runs/full_patch_ledger_20260910/`.
Baseline HEAD: `315bece11785f4e05c98c07819b0842a8cf4d156`.

## 19. 2026-09-10: is the repair becoming too complicated? Reassessing Colombo & Re (2022)

The user challenged the engineering complexity of section 18 and asked to
reconsider Colombo & Re. The paper was re-read, with independent checks of
its time/positivity formulation and of the local AREPO integration points.
This is a paper/source/design review, not a new simulation campaign.

**Revised engineering judgement:** the remaining-outflow construction is a
useful diagnostic and scalar existence result, but should not yet be the
implementation target. Combining element lifetime tracking, frozen-state
latches, actual-ledger remapping and a still-unproved Euler future-outflow
constraint has exceeded the scope of a small repair. Section 18.5's preference
for that route was too strong as an engineering recommendation. Its algebra
and counterexample remain valid; the priority changes in light of the user's
cost and thesis-verification constraints.

### 19.1 What the cited paper actually supplies

Compact primary-source checks:

| Item | Verified scope |
|---|---|
| Spatial representation | Continuous P1; base nodal mass is area/3 (§§2.1–2.2). |
| Residual | LF-based, with characteristic limiting/stabilization for higher order (§§2.2,2.6). |
| Physical time | Global BDF; nonlinear equations solved by implicit pseudo-time iterations (§§2.4,4). |
| Topology | Collapse/expand accumulates swept geometry; fluid states are then solved jointly (§3, Eq.23). |
| History | Removed ghost elements retain old mass/sweep history until the BDF stencil no longer needs them (§3.1). |
| Positivity | LF spectral-radius local condition is discussed; no explicit hierarchical Euler invariant-domain theorem is provided (§2.2, Eqs.11–12). |

[Colombo & Re, primary-source full text](https://arxiv.org/html/2204.11668v1).
The adaptive pseudo-time CFL is not a hierarchy of physical timesteps. The
geometrical collapse parameter is also not an explicit fluid integration
through zero-area triangles. These distinctions are essential to the port.

### 19.2 What becomes simpler, and what gets replaced

Our interpretation: the appealing part is the organization of the method.
Old mass history, geometry changes and new states enter a single residual
balance. This offers a principled alternative to repairing a completed update
with a uniform patch shift. It stays within P1; neither native Voronoi FV nor
a wholesale move to consistent FE mass is required by this idea.

But that mathematical organization is obtained with a different time solver.
The following are distinct projects:

| Route | What it could provide | Work relative to the present AREPO RD |
|---|---|---|
| Reproduce the complete published method | A literature-backed synchronous topology treatment | BDF history, nonlinear solve, pseudo-time driver, LF/limited space-time residual and ghost elements; present explicit hierarchy would be replaced, not retained |
| Borrow swept geometry while retaining Campoli/N/RK | A geometrically defined topology residual/transfer in the existing P1 code | Derive the explicit mass/residual pairing and positivity; add old/new geometry records; hierarchical state/interval coupling remains new work |
| Use a local implicit or subcycled topology-only solve | Potentially a controlled small-patch transfer | New split method; must prove closed-patch balance, state quadrature and its coupling to frozen physical histories |

Thus a full port is not demonstrably cheaper than the present research path.
The geometry-only borrowing is a smaller experiment, but cannot be described
as an already validated explicit variant of the paper. A successful same-time
transfer would improve one part of the method, not finish hierarchy.

### 19.3 Why geometry alone does not remove the asynchronous obstruction

This subsection is our inference, not a negative result about the published
algorithm. If a replacement topology operator leaves an inactive node with
less Q while future physical residuals still use its old frozen U, the same
possible overspending identified in section 18 remains. An instantaneous
positive local implicit solve does not, by itself, remove those future terms.
The published common-time solve avoids this exact frozen-history setup;
retaining it in AREPO requires an additional time-discretization argument.

Two tempting shortcuts also need care:

1. **Explicit substeps along the collapse path.** The cancellation of signed
   exterior swept areas does not imply cancellation of state-weighted flux:

       integral dA = 0 does not imply integral U(tau) dA = 0.

   If U evolves between collapse and expansion, the exterior contribution
   needs a consistent common trace or explicit accounting. A local topology
   solver must establish its own closed boundary balance; simply reusing a
   cancellation of geometry is insufficient.
2. **Reduce the ordinary physical CFL until the flip is harmless.** For an
   instantaneous basis change with finite swept area A_top, a first-step
   effective geometry rate scales as nu_top=A_top/dt. The explicit geometric
   Courant contribution therefore scales as dt|nu_top|/m=|A_top|/m, rather
   than vanishing with dt. Smaller physical steps may change event frequency
   and states, but cannot alone make a fixed finite basis jump infinitesimal.
   Geometry subcycling is a separate proposal, with its own proof and cost.

Nor is the original paper refuted by saying that explicit CFL would vanish at
a collapsed triangle: it does not require that explicit marching operation.
Its LF local-positivity discussion should be acknowledged, without converting
it into a proof for our Euler N/RK or for arbitrary asynchronous histories.

### 19.4 The concrete AREPO integration issues

The local driver captures an old topology diagnostic at `src/main/run.c:267`,
then releases the old mesh at `:282`. The subsequent `create_mesh()` starts
from a fresh tessellation (`src/mesh/voronoi/voronoi.c:158`) and inserts points
(`:234`). Consequently, flips inside
`src/mesh/voronoi/voronoi_2d.c:473` are construction operations on the fresh
mesh. They are not the sequence of topology changes between the previous and
current physical RD meshes. Attaching a swept-history callback there would
record the wrong history unless the mesh-update architecture were changed.

The smaller approach is to compare complete old/new physical triangle sets,
form closed changed cavities, and construct an artificial geometry path for
each cavity outside the native mesher. The current snapshot at
`src/hydro/residual_distribution_solver.c:1548` stores only sorted IDs and
area/3. It would need orientation, coordinates and periodic winding, and a
hierarchical variant would still need actual interval metadata. Old elements
could be transient event records once their histories are fully closed;
there is no need to require their connectivity to survive many coarse steps.
Finding valid common cavities after severe distortion is itself a condition,
not something the old/new ID difference alone proves.

There is also a kernel mismatch. The current characteristic builder at
`src/hydro/residual_distribution_solver.c:642` uses one mean mesh velocity,
whose shifts are proportional to current edge normals and sum to zero.
A ghost with zero current normals but nonzero integrated swept contribution
cannot be represented by choosing another mean velocity. The present code's
separate geometric correction does not make it the same LF ghost operator.
A dedicated topology residual or a rederived N/temporal-mass coupling is
needed; adding one velocity argument is insufficient.

For MPI, the spatial construction can use one owner per cavity and additive
conservative exports, but short-lived old-element geometry and state history
still need correct ownership and migration. With a global implicit port,
distributed nonlinear iteration becomes additional engineering. Calling MPI
only an easy final wrapper would understate either route's integration work.

### 19.5 Bounded next comparison and thesis scope

Pause promotion of the reserve construction to production C. Prioritize a
Colombo-inspired **same-time, single-cavity** comparison, preserving P1 and
the existing physical solver as the reference. First formulate the old/new
temporal contributions and the swept geometry for one 2-to-2 flip. Establish
conservation, uniform-state preservation and a clearly stated positivity
condition before any full fluid run. Then compare its linear-field behavior
and mixing against the current repair, particularly for unequal densities
and counterstreaming velocities. An explicit or local implicit variant must
be labelled as our extension, not a reproduction of the published method.

Only if this produces a useful, reviewable operator should it be coupled to
one mixed-bin event. That coupling must decide whether affected nodal
intervals really close or whether a provable frozen-history constraint is
retained. If it still requires the same extensive reserve machinery, the
geometry improvement is not a simplification of the full hierarchy. No
one-week completion or automatic Euler positivity claim is warranted.

Current implementation scope remains unchanged: no production C, thesis or
volume-2 edits, no new numerical tests this turn, and no native FV development.
The complete log through section 18 was saved as
`local_runs/full_patch_ledger_20260910/log3_through_section18.md` (relative to
the workspace root), matching the earlier audit's recorded log hash before
this append and index update. All earlier numerical results retain their
original scope.

## 20. 2026-09-10: new Colombo-inspired test branch; explicit topology and local nodal closure

The user requested a new Git test branch, 5–10 subagents and algorithm tests.
Created `test/colombo-re-explicit-hierarchy` from `315bece`. The preceding
uncommitted notes/audits were first preserved in commit `c479457`, leaving
`develop_pureC_RD` at its original commit. Five distinct subagents worked in
batches on geometry, explicit positivity, hierarchy, adversarial schedules,
and C/AREPO integration; the root task added independent accuracy/ODE checks,
module composition and prescribed-motion scalar ALE tests. The runtime allows
only three concurrent children; existing agent tasks were reused when the
new-thread limit was reached.

The consolidated, human-reviewable account and reproduction commands are in
`dev_log/colombo_re_spike/README.md`, with five supporting reports. No
production `src/`, thesis or volume-2 file was modified. Native FV remains
outside this work. A standalone C99 topology kernel was added under tests.

### 20.1 Explicit geometry construction and conditional Euler positivity

The geometry module constructs signed semi-edge sweeps for old/new records
of a convex 2-to-2 cavity in a common periodic embedding. It independently
checks swept quadrilateral areas against space-time Gauss integration. The
required identities are element sum(nu)=Delta A and, for every cavity node,
sum_records(nu)=0. The latter is stronger than zero total cavity area change.
One thousand randomized cavities passed at errors below 3.34e-16; orientation
and prescribed periodic-image changes agreed to roundoff.

Combining the old ghost and new records yields the pure-geometry generator

    L_T = -1 nu_T^T/3 + alpha_T (I-11^T/3),
    1^T L=0,    L1=-delta_m,    L_ij<=0 for i!=j.

On the positive full-nodal-mass path g(s)=g^-+s delta_m, use

    A=diag(g(s))-ds L,
    Q_next=A [Q/g(s)],    g_next=g(s)+ds delta_m.

For ds L_ii<=g_i(s), A is nonnegative, its column sums give extensive
conservation and its row sums give constant-state preservation. Dividing by
g_next produces convex combinations of the old conservative states, proving
same-time Euler admissibility for admissible input. This is a new explicit
extension informed by Colombo--Re geometry, not the published BDF method.
Fluid states never pass through zero-area physical triangles.

Two rules were tested: spectral alpha=max|nu| and the smaller pure-geometry
bound alpha=max(0,-min nu), labelled graph_minimal. The latter establishes
off-diagonal signs for the combined generator and is not a replacement for
Euler physical LF wave-speed bounds or a globally optimal dissipation rule.
All 4096 safe adaptive Euler-state transfers passed; maximum relative
conservation error was 7.12e-16. Unsafe one-shot controls were retained.

Successive geometry records cannot in general be deleted merely because an
intermediate triangle has zero net area change: its nodal signed sweeps may
sum to a nonzero vector if its birth/death collapse paths differ. A direct
old-to-final cavity path is a different construction, not automatically the
same state transfer.

### 20.2 A simpler first-order hierarchy coupling than the reserve

The new time reference closes every triangle incident to any of the four
cavity nodes before refreshing those nodes' states. Exterior nodes receive
extensive increments but keep their traces unless naturally active. After
same-time transfer, the four trace epochs reset; new elements start at the
event, retained elements keep their last time, and natural bins/endpoints
are unchanged. There is no RK predictor or frozen-until latch in this
first-order model, and no future-outflow reserve is needed.

Every triangle containing a changed trace has already ended at the event.
At the outer boundary of this star union the traces are unchanged, so closure
does not recursively require new state refreshes. This gives a transparent
piecewise-constant-time trace argument. On a regular square cavity the union
contains 16 triangles and 14 receiving vertices, with only four refreshed
states; a 16x16 example involves 16/512 triangles. This is an example, not a
universal bound on unstructured-star size or on total event cost.

The static scalar proof uses ordinary nodal CFL bounds for both allowed
connectivities. A refreshed node starts from Q=gU, its cumulative outgoing
coefficient before the next refresh is bounded by its original own step, and
the N inflow weights are nonnegative. The same-time positive map restarts the
argument. Euler matrix N, changing coefficients and RK2 are not included in
that static proof.

Thirty baseline cases included 21 safe closure cases and explicit negative
controls. The frozen-ledger peak case gave min U=-0.0342762; complete local
closure gave min U=0.01; refreshing four states while closing only dying
triangles produced mass error 0.00155499 and ten crossed-trace intervals.
Safe cases included repeated flips and depths 1:1024 and 1:2:1024, with
maximum completed/macro mass error 2.45e-15.

### 20.3 Independent stress tests and coupling to moving scalar ALE

The adversarial driver independently extended the static model to random
dyadic bins and multiple cavities. Twenty-four cases performed 1769 flips,
including 846 same-tick additional flips and 514 periodic-boundary cavities.
The physical step used 0.99 times a nodal CFL envelope over all 16 possible
local diagonal arrangements. Completed/macro mass error was below 2.00e-15,
all scalar states respected the initial range, and trace-crossing/orphan/
prebirth/incomplete-refresh counters were zero. Its deliberately incomplete
closure control gave 189 trace crossings and macro mass error 8.46e-3.
This independent driver uses geometry_records and the new adaptive spectral
topological_remap, so the 1769 events also exercise the CR transfer with static
scalar hierarchy. This does not extend the original single-cavity driver API
to arbitrary production meshes or establish moving Euler behavior.

The separately composed CR callback passed 12 safe cases among 18 controls
and coupled runs. Leaving the old U frozen still fails: spectral/minimal
peak controls reach -0.357643/-0.0804715. Full local closure with the same
maps remains positive, including depth 1024 and repeated flips.

The root task also added 16 prescribed-motion scalar ALE cases, including
depth 1024, with linear periodic vertex trajectories and synthetic flips.
The per-triangle physical increment is

    Delta Q_iT = (A_end-A_start) U_i/3 - dt phi_iT(midpoint).

For the prescribed constant nodal velocities and frozen nodal states, the
element total is the exact time-integrated ALE contour balance. Individual
N-distributed increments are a first-order physical-time approximation, not
exact per-node integration. Geometry keeps g_i=sum_T A_T(last_T)/3; full
local closure makes patch g equal the actual current nodal mass before remap.

An independent review checked the geometric and temporal argument and found
a diagnostic gap: a topology map could hide a negative preceding physical
state if only post-transfer minima were recorded. The driver now separately
checks pre-transfer Q/U, virtually completed Q and the accumulated scalar
coefficient margin g_i-sum(dt k_iT^+) since each complete trace refresh.
All tested margins were positive. This is a checked sufficient condition for
these trajectories, not a general moving-grid timestep selector.

Moving completed-total error was at most 4.44e-16, macro error 3.34e-16,
active geometric closure error 1.81e-16 and uniform error 1.49e-14. Signed
triangle area is checked over the whole quadratic trajectory interval.
These are modest prescribed motions with fixed vertex velocities; actual
Delaunay-event detection, changing velocities/bins, Euler transport and
cosmological dynamics were not exercised.

### 20.4 Accuracy result: the low operator is not yet a good default

An independent DOP853 reference confirms convergence of the explicit
subcycles to the proposed geometry ODE. It does not remove that ODE's own
dissipation. On affine scalar 1+0.2x-0.1y over a unit cavity, maximum nodal
changes are:

| Transfer | Affine change | Nonuniform flip/reverse variance retained |
|---|---:|---:|
| CR spectral low | 0.117857 | 0.01459 |
| CR graph_minimal low | 0.0535714 | 0.22695 |
| Previous full-patch low | 0.0428571 | 0.34620 |
| Previous high uniform shift | roundoff | 1 |

The high endpoint lacks unconditional positivity; the comparison therefore
does not select it unconditionally. It establishes that a published geometric
motivation and a positive low endpoint do not automatically give better
accuracy. The local affine defect scales as O(h) as the cavity shrinks. A
low-dissipation/high-order treatment remains a decisive research requirement.

### 20.5 C interface, production semantics and remaining integration work

A bounded standalone C99 kernel implements the same-time generator interface
without linking or changing AREPO. Compilation uses -Wall -Wextra -Werror
-pedantic. In 256 Euler cases, C/Python discrepancy was at most 4.35e-16 and
relative conservation error 6.44e-16; all outputs were admissible. An ODE
refinement sequence, malformed-input controls and six scalar hierarchy C
callback cases also passed. The C kernel receives L; swept geometry and
physical topology detection have not been ported to C.

The production-code audit confirms that existing RD hierarchy likewise does
not demand raw sum(Q) conservation at every fine event: it submits triangle
residuals whose sum is Phi_T, not zero. The existing design document explicitly
uses common endpoints. Our independent stress test had raw partial-ledger
drift up to 4.86e-2; this must not be reported as fine-tick conservation.
The virtual completion diagnostic never commits a hidden global fine step.

Current RD_ALE_HIERARCHICAL performs predictor and corrector consecutively
at one mesh event. The static split-call path's potentially prebooked half
step must not be attributed automatically to this moving path. Nevertheless,
RK quadrature states, actual element interval, geometry and temporal mass
terms still need a new consistency argument before early nodal refresh.

The smallest future AREPO integration needs persistent oriented triangle IDs,
periodic geometry, birth/last times and trace epochs; an explicit extra hydro
refresh list distinct from natural activity; and one actual interval shared
by all operations. A first-order path cannot be made by calling the present
predictor once because its half-weights and mass-gap terms belong to RK2.
MPI ownership/import completion and migration of independent triangle tables
remain additional work. Details are in `colombo_re_spike/arepo_integration.md`.

**Current decision:** retain complete local nodal interval closure as the
simpler first-order coupling reference. Retain the new geometry operator as
a conservative positive low baseline, not the final default. The next
decisive questions are controlled dissipation and compatibility with actual
Euler/RK2 updates; no production, second-order, changing-bin or MPI claim is
made. All reproduction commands, exact JSON and SHA256 provenance are in
the report and `/Users/zhenyuwu/arepo_rd/local_runs/colombo_re_spike_20260910/`.

## 21. 2026-09-11: native Euler tests, limited high repair and the source of CR-low dissipation

The user authorized the next Colombo–Re experiment in actual standard hydro
tests, then asked whether the larger dissipation came from omitting our RK2.
On `test/colombo-re-explicit-hierarchy`, a compile-guarded same-time topology
operator is now connected to the existing equal-step moving N/RK2 solver.
The detailed, human-reviewable report is
[`colombo_re_spike/phase2_hydro.md`](colombo_re_spike/phase2_hydro.md).
No thesis or volume-2 files were changed.

### 21.1 What the native experiment actually changes

Exact old/new changed-triangle components are transferred at the old physical
time, using the new connectivity pulled back to that time; the ordinary ALE
step then evolves to the endpoint. Signed semi-edge geometry is assembled in
a common periodic chart and checked for matching oriented boundary chains,
nodal swept balance, full mass closure and global extensive conservation.
The construction is a direct old-to-new path, not reconstruction of the
actual chronological sequence of Delaunay flips. Component counts are not
flip counts. Native components reached six nodes; this bounded 2-D experiment
uses zero third velocity and remains a one-rank equal-step path.

Three CR modes select graph-minimal low, the previous uniform-shift high with
a common positivity limiter toward that low, or the same map with a hard
component density-range bound. The high endpoint is our existing correction,
not a newly derived Colombo–Re high-order scheme. The original repair and a
primitive-refresh-only control are retained, as is a matched Campoli control.
All native binaries enable the existing `N_SCHEME + RD_RK2_TOTAL_RESIDUAL`.

### 21.2 Low topology mixing persists under geometric RK2

For the scalar geometry ODE Q'=-LU, Q=gU, g'=dm, column conservation and
L1=-dm give the exact lumped-variance identity

    d/ds sum_i g_i (U_i-c)^2 = -sum_(i!=j) (-L_ij) (U_i-U_j)^2 <= 0.

Thus the low generator mixes states even with exact artificial-time
integration. Seven geometries and two generators passed independent
FE/midpoint/Heun refinement against DOP853: FE approaches first order, RK2
second order, but both approach the same mixed result. On the unit-square
full-mass-one example, flip/reverse retained variance is 0.226954 for one-step
FE, 0.272489 for four-substep FE, 0.286250 for four-substep Heun, and 0.285884
for the high-accuracy ODE. Existing unlimited high returns the original state
in this paired example. This is a local scalar diagnostic, not a universal
71% dissipation rate, an Euler entropy statement, or unconditional positivity
of high. See `colombo_re_spike/geometry_rk2.md`.

### 21.3 Twenty standard hydro runs and images

Yee n24 (578 nodes) and n48 (2304 nodes), boost=(0.5,0), t=0.2, and periodic
Sod 32x32 at t=0.08 completed with positive finite outputs and actual
connectivity changes. The twenty runs include original/refresh/low/positive/
density-DMP comparisons, two Campoli pairs and four Sod half-timestep controls.
Each run stores only initial/final snapshots. Error weights use RD median
dual m/rho; Sod compares the central Riemann solution before periodic waves
interact. No global spatial or multirate temporal order is inferred.

| Case | Density L1, original repair with primitive refresh | CR low | Limited high |
|---|---:|---:|---:|
| Yee n24 | .00261535 | .00284189 | .00261582 |
| Yee n48 | .00143104 | .00160020 | .00143104 |
| Sod n32 | .05081558 | .05137482 | .05088581 |

Yee n48 low increases density L1 by about 12%; its velocity L1 is about
2.26 times the refreshed repair. Sod low increases pressure L1 by about 12%.
These full-flow errors also include the resulting mesh and physical evolution,
so only the isolated operator audit separates topology dissipation completely.
All native positivity-only cases accept theta=1: their accuracy is evidence
for retaining our high endpoint, not for a superior CR-low solution. Hard
density DMP is active in almost all components. Random standalone Euler
tests, rather than these native cases, exercise the positivity fallback.

Chapter-3-style scientific PNG/PDF figures are available under
`/Users/zhenyuwu/arepo_rd/local_runs/colombo_re_hydro_20260911/figures/`:
Sod density/velocity/pressure cuts, Yee density and analytic-error maps,
Yee radial/entropy profiles, geometry-RK2 convergence/variance, and physical
mass conservation. The figures have been rendered and visually inspected.

### 21.4 Separate consistency and conservation controls

The existing repair updates ale_uold/storage but stage-0 fluxes read primitive
fields. A guarded primitive refresh makes those fields consistent after the
same-time remap. The original Sod mass/energy drift of about 9.67e-7/1.96e-6
falls to 6.65e-9/7.23e-9 in the refresh-only control with nearly unchanged L1.

The residual Arpaia drift reproduces the endpoint-rebase defect already
established in section 10, not a new CR nonconservation channel. For limited
high, halving Sod dt reduces mass/energy error from 6.54e-9/7.02e-9 to
1.65e-9/1.77e-9. Changing only the temporal mass to Campoli produces
1.97e-16/3.23e-16 on Sod and 1.45e-16/2.20e-16 on Yee n24, with essentially
unchanged flow error. Retain Campoli as the conservative reference while
resolving RK2/hierarchy composition. Physical-CFL diagnostics remain distinct
from the geometric positivity condition.

### 21.5 Independent validation and remaining boundary

The limited map passes 4608 random Euler transfers and 48 repeated-event
configurations; relative conservation is at most 8.49e-16. Independent Gauss
geometry plus Python remap replays 104 native event dumps with full-state
relative differences below 1.80e-13 and transfer conservation below 4.22e-16.
All sampled events have four nodes; native six-node components are not claimed
as independently replayed. A conditioning-sensitive density-bound case exposed
a Python limiter fallback that halved theta; it now retains the last actually
accepted bisection candidate. The captured native event is a regression fixture,
and the affected audits were rerun. Small-component relative/limiter-parameter
differences are reported explicitly in the detailed report.

Thirty-six limited-map local-closure scalar cases, static and prescribed-motion,
including depth 1024, pass with completed-total error below 3.78e-15 and minimum
scalar above 6.95e-14. These retain the previous first-order trace construction.
They do not establish production Euler RK2 with hierarchy, varying bins,
strong-shock fallback behavior or moving MPI.

**Decision:** retain the old high as the accuracy candidate, CR low as a
provable same-time positivity reference, and complete local interval closure
as the first-order hierarchy reference. The present data do not justify a
pure-low default. Increasing artificial-time order alone does not address
the generator's mixing. Runtime summaries, plots, immutable build copies and
checksums are preserved in `local_runs/colombo_re_hydro_20260911` outside Git;
the source, exact configs, analysis tools and reports are tracked on the test
branch. This remains an explicit extension, not the published implicit BDF
algorithm or a completed hierarchical moving Euler solver.

## 22. 2026-09-11: Sod actual Nx=48 (full box 96²), N/LDA CR versus basis repair

The user requested higher-resolution Sod plots, increasing 32² to 96², with
both N and LDA using RK2. Six matched native runs completed at t=0.08 on the
test branch: each physical RD scheme with primitive-consistent basis repair,
pure CR graph-minimal low, and existing high plus CR positivity fallback.
The solver C is unchanged. New LDA configs replace only the N scheme selector
and its descriptive comment; existing GL/F1 and rank-deficient mass fallback
remain enabled. All runs use Arpaia temporal mass and the existing ALE
contour/comoving-frame/equal-step path, without extra shear or entropy floors.

The deterministic IC contains 9216 jittered vertices, gamma1.4, a central Sod
jump and its periodic counterpart. CourantFac=.08 and MaxSizeTimestep=1/3000
are shared. Actual dyadic schedules depend on each evolved flow, so equal-step
means synchronous vertices within each run, not identical schedules between
runs. All terminate at the same t=.08, with 490–540 steps and maximum actual
dt=.0003125. Only initial/final snapshots are retained. Error comparisons use
RD median-dual weights m/rho over .25<x<.75, before periodic-wave interaction.

| Scheme / topology | Density L1 | 2-D velocity L1 | Pressure L1 | Transverse RMS |
|---|---:|---:|---:|---:|
| N / basis | .028099 | .067963 | .032956 | .005670 |
| N / CR low | .030218 | .072592 | .035127 | .006205 |
| N / high + fallback | .028098 | .067811 | .032924 | .005588 |
| LDA / basis | .023041 | .096919 | .025941 | .054975 |
| LDA / CR low | .022302 | .054927 | .023825 | .012245 |
| LDA / high + fallback | .023028 | .097205 | .025977 | .054653 |

**The physical-scheme dependence matters:** low topology mixing increases
N's density/velocity/pressure errors by 7.54/6.81/6.59 per cent. For LDA it
reduces the corresponding errors by 3.21/43.33/8.16 per cent and transverse
RMS by 77.73 per cent. The contact is broader in both low cases, but LDA's
velocity scatter is substantially reduced. Intrinsic low-operator mixing
therefore does not imply larger net error in every shock calculation.
These results support neither a universal pure-low default nor a general
positivity/stability theorem for moving LDA.

Both high-plus-fallback runs accept theta=1 everywhere, retaining the existing
high behavior and LDA oscillations. Exact-component grouping differs from
the old support grouping, so this need not produce bitwise-identical solutions.
Native CR components reach eight nodes; 4901/10519 high components and
5156/6636 low components are not elementary flip counts. Independent replay
of the first eight dumps from each CR run (32 four-node samples) agrees to
2.23e-16 in full-state relative scale and conserves to 2.56e-16. This replay
does not independently cover the native eight-node components.

All six runs return zero with finite positive endpoint fields and positive
recorded predictor minima. LDA basis reaches predictor rho/p minima
.062570/.029547; LDA low .082623/.051848. Arpaia total drift remains at
relative mass 1.06e-10–6.20e-9 and energy 1.02e-10–9.65e-9. It is retained
as the established comparison from sections10/21, not promoted to roundoff
physical conservation or interpreted as failed same-time CR conservation.

The detailed report [sod96.md](colombo_re_spike/sod96.md) includes main 2x3
N/LDA profiles, contact/transverse-velocity details, errors, and PNG/PDF links.
All particle scatter is retained in the main figure; curves are RD-area means
in common x bins. The density detail is explicitly zoomed, while transverse
velocity is not clipped. Figures were rendered and visually inspected.
Data, frozen binaries/configs/generated headers/build logs, reproduction
commands and SHA256 provenance are in
`/Users/zhenyuwu/arepo_rd/local_runs/cr_sod96_20260911_omp1`.

A local runtime correction substantially reduced cost. This Homebrew OpenBLAS
uses its OpenMP backend: OPENBLAS_NUM_THREADS=1 alone still reports ten
threads; additionally setting OMP_NUM_THREADS=1 reports one. A read-only
sample found the original runs spending most time in barriers inside tiny
dgetrs solves. The incomplete first attempt was explicitly stopped and
preserved separately; identical frozen binaries and IC were restarted with
both variables, completing each run in about76–83 seconds with at most two
singleton jobs. Shared early logged global totals match exactly (117 N and
106 LDA endpoints), without claiming full-state bitwise validation. This
correction is recorded in context_localMac.md and the new run driver.
No thesis or volume-2 files were modified; no new hierarchy/MPI claim is made.

## 23. 2026-09-11: high-repair semantics and unexpectedly large LDA vx scatter

The user asked whether both high repairs show the large vx scatter and recalled
cleaner older results. Their high formula is identical on a common patch;
support versus exact-component grouping differs. CR fallback selects a common
theta toward low only when high fails Euler admissibility. Both Sod96 runs
keep theta=1, so neither imposes a velocity maximum principle. High names a
topology-transfer endpoint, not a different physical LDA/RK2 method.

Three new native controls use identical96² IC and t=.08, with unchanged solver
C: moving no-repair, original repair without primitive refresh, and static
LDA/GL/F1 RK2. All finish with two snapshots. Central-half vx ranges are
[-1.0323,1.0949] static, [-.5041,1.7644] no-repair, [-.8830,1.7849] original;
the existing refreshed-basis and CR-high cases give [-.8694,1.8019] and
[-.8838,1.8425]. CR low gives [-.4015,1.0373]. Their respective transverse
RMS values are .01540,.04545,.05486,.05498,.05465,.01224.

The large moving scatter does not require the new CR fallback or primitive
refresh, but repair can still change or amplify it through flow/mesh feedback.
No-repair has mass drift3.15e-4 and is an intentionally nonconservative
diagnostic, not a recommended alternative. Static LDA has a strong localized
shock undershoot. Completion and positive rho/p are insufficient quality
criteria; improvement over an oscillatory baseline is not a general accuracy
proof for CR low.

The user correctly clarified that Morton's original benchmark is static.
The local Morton-labelled n128 figure includes a later moving-LDA extension;
its oscillations must not be attributed to the published static benchmark.
Old figures and their code were read: that local moving extension already
shows oscillation but displays512-bin means without all particles, on a row-offset
1e-6 h jittered mesh with gamma5/3. The new IC uses .08 h Cartesian jitter and
gamma1.4. The glass48 shear-floor summary displays rho,p,vy rather than vx;
the entropy-floor summary also excludes vx and plots means plus one standard
deviation without all outliers. These verified differences prevent a direct
visual comparison. They do not isolate how much amplitude change comes from
geometry, EOS, resolution, timestep or historical code; no matched historical
commit rerun was made. Do not dismiss the user's recollection or attribute
the entire difference to plotting.

Details and the six-panel velocity-control figure are in
[sod96_regression.md](colombo_re_spike/sod96_regression.md). Frozen binaries,
configs, outputs, summaries, figures and provenance are preserved in
`/Users/zhenyuwu/arepo_rd/local_runs/cr_sod96_regression_20260911`.

The requested static LDA test is complete, with density/pressure L1 errors
.0202691/.0192008 and relative mass/energy drift1.97e-16/0. A second figure,
`figures/static_moving_lda_profiles.png` (and PDF), compares static versus
refreshed-basis moving LDA in rho,vx,p on identical axes with every central-half
particle retained. Both figures were visually inspected. This is a matched
control for the present Sod96 campaign, not a reproduction of Morton's setup.

## 24. 2026-09-11: actual Sod resolution, glass IC and two isolated oscillation mechanisms

The user requested that Sod be labelled by the resolution of one tube, not
by the full periodic setup, and that glass be the primary IC. In the current
unit-square box the comparison fan has length0.5. Using initial mean spacing
h=sqrt(A_box/N_total), full96² means actualNx48, full32² means actualNx16.
The present official relaxed SWIFT glass128² means actualNx≈64. Glass has no
literal columns. Old result directories retain their archive names; the
tracked reports and regenerated figure titles now state actualNx48, with
original figures/provenance retained in labels_before_resolution_correction.
Future Sod metadata includes full_box_nside/effective_resolution_x.

Morton2023 section5.1.1/Figure7 specifies first-order LDA/N, gamma5/3,
CFL0.4 and a Cartesian lattice with alternate rows shifted by half a spacing.
The published plot cannot be treated as a GL/F1 RK2 glass benchmark. The
existing local Config_GLASSSOD_STATIC_LDA_RK2.sh had a misleading first-order
comment despite enabling RK2; its comment is corrected, without config changes.

Twelve native controls completed, all at t=.08 with five snapshots per case.
Main controls use identical glass coordinates/IDs/states, gamma1.4, CFL.08,
cap1/3000; a half-step case halves both controls. At actualNx≈64:

| glass case | min vx | max vx | RMS(vy) |
| --- | ---: | ---: | ---: |
| Static LDA1 / Forward Euler | -1.71e-8 | 1.13847 | .0045345 |
| Static lumped-mass LDA Heun | -2.40e-8 | 1.14390 | .0045304 |
| Static current GL/F1 RK2 | -.77657 | 1.00935 | .0102383 |
| Static GL/F1, half timestep | -.76719 | 1.01007 | .0102375 |
| Zero-motion ALE Roe GL/F1 | -.77657 | 1.00935 | .0102383 |
| Zero-motion ALE contour GL/F1 | -.66237 | 2.48730 | .0252756 |
| Moving contour GL/F1 + refreshed basis | -.71756 | 1.36551 | .0177152 |

First-order uses the existing RD_DIAG_PREDICTOR_ONLY switch, not the legacy
Taylor-extrapolated two-half-call path reached by merely disabling RK2.
The only new solver code is RD_DIAG_LDA_LUMPED_TEMPORAL: guarded to static,
equal-step LDA with the ordinary two-pass total-residual engine. It replaces
T_time by (A_T/3)dU_j/dt, retains its column sum and both spatial sweeps, and
reduces the update exactly to lumped Heun. It does not affect default builds.
The initial extension build caught a missing defines_extra declaration; after
adding it, the isolated build and full hydro control passed. The failed build
log is preserved. No production method is switched.

These controls isolate a GL/F1-associated strong negative-vx undershoot in
this test, not a universal defect of RK2. With v=-S^-1 R and C=S^-1 M_F1,
the existing corrector gives Unew=Un+dt(1.5vn+0.5vstar-Cstar vn). On a regular
state branch, its dt→0 rate is (2I-C)v, whereas FE/lumped Heun advance v.
Thus reducing dt alone does not remove this spatial mass coupling. Half-dt
results support that interpretation without establishing a full convergence
study. FE/lumped still overshoot above the exact velocity plateau and have
larger density/pressure L1 errors, so absence of the large negative trough
is not a reason to replace the production mass matrix.

Zero-motion runs have exactly unchanged coordinates and no removed/inserted
triangles in all864 contour/845 Roe records. Geometry diagnostics give
stationary=1, static_bit_mismatch=0 and static_max_diff=0. The zero-motion Roe
endpoint agrees by ID with static GL/F1 to max absolute rho/p/v differences
1.82e-14/2.39e-15/1.20e-14. Changing only the total to contour therefore exposes
an additional source of scatter without motion or flips. The contour total
interpolates nodal physical fluxes, whereas Roe uses parameter-vector
linearisation; nonlinear shock residuals need not coincide. This does not
by itself identify an algebraic coding bug or justify reverting moving ALE
without revisiting its established conservation/GCL requirements.

This corrects the attribution in section23: its static/moving pair changed
both mesh motion and total residual. Scatter cannot all be called movement
amplification; here moving contour even has smaller maximum scatter than
zero-motion contour. Topology/hierarchy work should be judged against a
fixed physical shock baseline, not by whether CR low suppresses this noise.

At the sameNx64, jittered GL/F1 still gives minvx=-.60509; glass reduces
transverse RMS but does not universally reduce the worst negative value.
Glass gamma5/3 GL/F1 still gives minvx=-.59730; first-order glass has no
significant negative vx. Regular first-order gamma5/3 preserves transverse
symmetry at1.23e-16 RMS and maxvx=.89076. These are causal controls, not an
exact reproduction of the paper's original time/CFL/code or raw data.

All static/zero-motion controls conserve mass to3.95e-16 and energy to1.23e-14;
moving Arpaia mass drift is1.24e-9, consistent with the previously retained
endpoint limitation. No new hierarchy/MPI guarantee is claimed. Scientific
figures retain all central-half nodes, with RD-area means and exact curves;
main profiles, mass/residual controls and EOS/geometry panels were inspected.
Detailed mathematics, full table and figure links:
[sod_glass_oscillations.md](colombo_re_spike/sod_glass_oscillations.md).
Data, frozen builds, inputs, logs, summaries and provenance:
`/Users/zhenyuwu/arepo_rd/local_runs/sod_glass_nx64_20260911`.

## 25. 2026-09-11: pause topology expansion; distinguish four historical Heun paths

The user explicitly prioritised recovering the physical baseline before more
CR/basis work, and recalled rejecting Heun for time-order failure and using
N's mass matrix with LDA. Volume1/2 and the standing F1 note were reread.
No simulation, solver/default-config or thesis change was made in this audit.

The history does not say that genuine lumped LDA Heun fails time order two.
It distinguishes (1) the old two-half-call Taylor-predicted RD hybrid,
(2) genuine Heun on v=-S^-1 R_LDA, (3) standard two-pass GL/F1 with leading
rate G=(2I-S^-1 M_F1)v, and (4) four-pass rate-consistent Heun on G.
Path2 is time-order two on a smooth regular ODE branch; its time ladder has
not been newly measured in this glass campaign. Path3's historical fixed-mesh
orders are about1; path4's measured orders are about2.000. Both retain F1,
whereas path2 uses the same diagonal mass formula selected for N, without
changing its spatial LDA distribution into N.

Early volume1 wording called path1 formally second order merely because its
Taylor predictor was first order. The later fixed-mesh experiment found the
old N baseline p=1.001 and genuine N/RK2 p=2.009. In general a predictor rate
P_h differing from the actual RD rate f_h gives a second-order coefficient
(1/2)f'_h P_h instead of (1/2)f'_h f_h; the Heun-like shape is insufficient.
Do not use the N-versus-LDA rows alone as a pure mass isolation, as one old
entry did: their spatial distributions differ as well.

Separately, the old lumped advected-Yee h order persisted after dt→0
extrapolation: .970 became .971. That supports the nonstationary spatial/mass
accuracy concern independently of the old hybrid's temporal defect. The
reason to introduce F1 was not solely to make a two-stage driver or to avoid
an intrinsically illegal N mass. Lumped is a conservative mass option whose
accuracy with nodal LDA must be demonstrated. A cleaner shock can reflect
more diffusion and does not settle the smooth-flow accuracy target.

The four-pass F1 rate-Heun was subsequently retained as an analysis option,
not rejected for bad time order: 2026-08-04 comparisons found1.57--1.77x cost
and about1.4--2.3% larger density L1 on the specific Yee/Sod tests. Its old A2
roundoff-scale failure was repaired by eb72efd and is not a current reason
for exclusion. Volume2 section37.3 explicitly protected this validated
rate-consistent option from erroneous deletion. Current configs select
standard GL/F1; old documents' word "current" must be read chronologically.

Pakmor2016 section3 starts from Heun and then explicitly describes the
primitive-extrapolation implementation as an RK/MUSCL-Hancock hybrid. This
supports the user's recollection of AREPO's structure, but the FV proof does
not automatically establish nodal RD order after swapping its spatial rate.

Detailed references, chronology and local expansions are in
[heun_baseline_history.md](colombo_re_spike/heun_baseline_history.md).
Baseline work should separately audit fixed-h dt convergence, advected-Yee
h convergence with controlled time error, and all-node Sod oscillations on
matched glass/Roe setups. Rate-Heun preserves the same limiting G as GL/F1,
so correcting temporal order alone is not expected to automatically remove
the F1-associated shock effect. Baseline validation remains unfinished;
no new production replacement or restored shock guarantee is asserted.

## 26. 2026-09-11: matched advected-Yee baseline and auxiliary time ladder

Following the user's priority, completed21 new native static glass/Roe LDA
Yee runs and1 F1 rate-Heun Sod run, reusing the two existing matched glass
Sod controls. Source0899c7e; no solver/default-config or thesis change.
Three methods: genuine lumped LDA Heun, standard two-pass GL/F1, and four-pass
F1 rate-consistent Heun. This is baseline work, not renewed topology expansion.

Yee: box10, gamma1.4, beta5, boost1, t1, generator sampling; the established
glass48 periodic tiling family at48²/96²/192². Main dt=1/256,1/512,1/1024;
n48 also has1/512,1/1024,1/2048, n96 also1/1024. All actual Yee step counts
and Systemstep values match; no silent CFL alteration. Same-IC and static
geometry/area checks pass; all21 Yee f1_lumped counts are zero. Norm weights
are RD median-dual Masses/Density, not Voronoi Volume.

Density L1, n48/n96/n192:

| Method | n48 | n96 | n192 | h refinement orders |
|---|---:|---:|---:|---:|
| Lumped Heun | 2.913729e-3 | 1.558756e-3 | 7.788923e-4 | .902/1.001 |
| Standard GL/F1 | 6.430158e-4 | 1.748167e-4 | 5.245707e-5 | 1.879/1.737 |
| F1 rate-Heun | 6.551337e-4 | 1.778519e-4 | 5.319881e-5 | 1.881/1.741 |

Velocity L1 orders are .935/.956,1.811/1.861,1.814/1.866 respectively.
The two F1 methods reproduce the historic glass results. These are finite
h,dt~h refinement slopes, not proof of asymptotic second order: the standing
mass_matrix_order_analysis.md also records a historical glass384 slope1.481,
which was not rerun here. The new n192 lumped density error is14.85x GL/F1.

Fixed-n48 numerical self-convergence gives finest density time p=2.0014,
.9958,1.9988 respectively; conserved-vector L1 gives2.0007,.9961,2.0003.
Thus genuine lumped Heun is time2 but still spatially about1 on this problem.
Halving the principal dt changes analytic density L1 at48/96 by only
-.000408%/-.000196% (lumped), +.9276%/+.8535% (GL/F1),
-.00981%/-.00830% (rate-Heun). Numerical density-state differences are also
small: at most1.44% of the analytic error. This supports using time order as
an auxiliary diagnostic for these practical spatial comparisons, while
continuing to label standard GL/F1's fixed-h time order honestly.

Two-finest-rung n48 Richardson states put GL/F1 versus rate-Heun density L1
difference at1.1783e-8, compared with lumped versus rate-Heun2.6796e-3. Their
estimated analytic density errors are6.550453e-4,6.550479e-4,2.913713e-3.
These approximate limits support the shared F1 rate G and distinct lumped v.
Standard GL/F1's slightly lower finite-dt error includes cancellation; it is
not a universal advantage or justification to conflate the time integrators.

Sod uses actualNx≈64 per single tube (full128² periodic glass), gamma1.4,
t.08, same CFL.08/cap1/3000. Rate-Heun min/maxvx=-.76181/1.01037,
vyRMS=.01020684, densityL1=.01589310; standard GL/F1 has
-.77657/1.00935,.01023829,.01576321. The large undershoot survives temporal
order repair. Lumped Heun has minvx=-2.40e-8 but maxvx1.14390 and larger
densityL1=.02346909; a cleaner negative trough is not uniformly better shock
accuracy. Actual Sod steps512/845/843, respectively; F1 methods use both
7.8125e-5 and1.5625e-4, lumped only the latter. This is matched CFL/cap,
not identical per-step histories. Prior GL/F1 halfstep control also retained
the undershoot.

Sod f1_lumped is the rank-deficient temporal-mass fallback counter, not a
positivity-limiter count. Rate-Heun accumulates two mass-action stages and
the lumped diagnostic still counts the branch before overriding T_time;
raw maxima31207/31207/63975 are not comparable bad-element fractions.
All output rho/p remain positive: negative vx is an undershoot, not itself
loss of Euler admissibility or a new positivity theorem.

All22 runs complete normally; maximum new-run initial/final relative mass
and energy drifts1.45e-15 and7.69e-16. All-node Sod figures, spatial curves
and auxiliary time figures were inspected and saved as PNG/PDF. Source/ICs,
configs, frozen binaries, logs, snapshots and SHA256 provenance are retained
under `/Users/zhenyuwu/arepo_rd/local_runs/lda_baseline_glass_20260911`.
Full tables, norm definitions and plot links:
[lda_baseline_convergence.md](colombo_re_spike/lda_baseline_convergence.md).

Physical baseline remains unfinished: retain these three distinct references,
investigate F1-associated shock behavior and the independently observed
zero-motion ALE contour scatter before CR/hierarchy can be evaluated cleanly.
No production switch or new moving-mesh/MPI/hierarchy guarantee is claimed.

## 27. 2026-09-12: moving LDA baselines and the limit of direct ALE rate-Heun

The user requested the same tests on moving meshes. All45 native runs
completed normally:13 short gates,26 main runs,6 no-flip conservation
controls. Source `11d8abcbde665bc384875924a546d07eb043bdd9` only extends
the protected lumped-temporal LDA diagnostic to existing equal-step ALE;
defaults remain unchanged. ICs match section26 exactly. Common moving
comparisons use laboratory-frame contour residual, Arpaia geometry, existing
basis repair/stage-zero refresh, and the existing fluid mesh velocity policy
with regularization. An element-frame GL/F1 is retained as a separate control.

The three methods must be named distinctly: ALE lumped temporal RK2,
existing GL/F1 two-pass, and **direct ALE F1 four-pass diagnostic**. The last
composes the static rate-Heun sweeps with current ALE prepare/finish; it is
not automatically a conservative or time-second-order moving method.

| Moving glass Yee method | rho L1 at48/96/192 | rho h-orders | velocity h-orders |
|---|---|---|---|
| Lumped temporal | .00287907 / .00166246 / .00089940 | .792 / .886 | .835 / .918 |
| GL/F1 two-pass | .00107436 / .00030503 / .00008988 | 1.816 / 1.763 | 1.708 / 1.403 |
| F1 four-pass diagnostic | .00106477 / .00029897 / .00008721 | 1.832 / 1.777 | 1.720 / 1.418 |

Norms use analytic fields at final moved coordinates and final RD areas.
All22 main Yee actual step counts/dt match the specified caps. Halving dt
at48/96 changes rho L1 by less than .7% in every method. Matched-ID time
differences also include changed trajectories/topology and show irregular
slopes: they cannot establish fixed-grid time order. Static reference curves
use Roe while moving curves use contour; differences are not solely motion.

Moving Sod uses full128² glass, initial **single-tube effective Nx≈64**.
Lumped gives rho L1=.023558, vx range≈0..1.0173 and vy RMS=.005721;
GL/F1 gives .017169, −.6722..1.3524 and .017750. Four-pass gives .017372,
−.6764..1.4462 and .016688. Lumped suppresses the trough/scatter but is
more diffuse; smaller integrated GL/F1 error does not establish shock
quality. Output rho/p remain positive; negative vx is not itself loss of
Euler admissibility. Element-frame GL/F1 retains the same problem and
reproduces the earlier archived moving Sod fields/coordinates exactly.

**Additional conservation failure of the direct four-pass ALE composition:**
Sod relative mass/energy drifts are8.5861e-5/9.8684e-5, compared with
1.1898e-9/3.5977e-9 for standard GL/F1. This is not all edge-flip error.
For a no-flip Campoli slab, let D=diag(s1), b=(s0+s1)/2, a=(s1-s0)/h,
v=-D^-1 R and G=2v-D^-1 Mv. Contour/mass column sums are
1^T R=a^T U and1^T M=b^T. Existing two-pass endpoint balance cancels;
direct Heun on this frozen G instead leaves
`Delta Q = h^2/4 * a^T (v0 + vH - 2G0)`.
This vanishes in the static and uniform-flow gates but generally not for
nonuniform moving flow. The full derivation is in the linked report.

Independent three-node algebra checks match the defect formula to3.8e-17.
A2304-node/4608-triangle periodic P1 Euler contour check verifies the
geometric summation identity to4.65e-14. All6 native short Yee controls
have zero topology-repair steps: Campoli two-pass lumped/GLF1 conserve to
output rounding, while Campoli four-pass has relative mass/energy changes
−2.508e-10/−2.898e-10. Arpaia has its separate endpoint-divisor limitation.
Thus the static rate-Heun proof cannot simply be transferred to moving mesh;
the direct diagnostic is not accepted as a new moving baseline.

Zero-motion Roe equals matching static fields within3.11e-15. Deforming
uniform flow stays constant within5.56e-16 (RD areas change by up to8.25e-4).
These gates do not settle the previous zero-motion contour shock scatter.
Across39 campaign cases, maximum repaired mass residual is1.136868e-13;
repair balance is distinct from the endpoint time-update balance above.

All runs use one rank and OMP/BLAS one thread. At most4 independent runs
were concurrent after checking local memory; each has its own directory.
All-node figures and convergence/conservation panels were visually checked
and saved as PNG/PDF. ICs, configs, frozen binaries, logs, snapshots, source
snapshots, completion checks, result/source commit metadata and SHA256
provenance are retained under
`/Users/zhenyuwu/arepo_rd/local_runs/lda_moving_baseline_glass_20260911`.
Full tables, derivation and figures:
[lda_moving_baseline.md](colombo_re_spike/lda_moving_baseline.md).

Physical baseline remains unresolved: GL/F1 improves smooth-flow accuracy
but retains shock scatter; lumped is a more diffuse diagnostic reference.
This work adds no CR/hierarchy/MPI guarantee and changes no thesis or log1/2.

## 28. 2026-09-12: Gauss physical-flux contour suppresses the Sod plateau scatter

The user separated the large x_tube=.7–.8 moving scatter from the localized
negative-vx trough: a static-like trough is acceptable for the present
baseline, but the broad particle scatter is not. Followed the existing log2
§36.4 proposal, supported by section24's no-motion/no-flip contour control.

The old physical contour integrates nodal physical fluxes by an edge
trapezoid, I_h F(U_i). The new guarded option integrates F(U_h) with Gauss
points on the same conservative P1 state. Mesh transport, F1 mass, RK
sweeps, mesh velocity and topology repair remain unchanged. This is neither
a switch to lumped mass nor a postprocessing smoother. It changes the
spatial flux discretisation and its effective dissipation. Shared-edge
corrections cancel, and Galilean covariance survives because the additional
linear-in-U flux terms have zero quadrature defect. Mass flux is linear,
so its correction is explicitly zero. Gauss quadrature remains approximate
for nonlinear Euler fluxes; it is not a claimed exact boundary integral.

Source559f8a4 introduced the protected three-point experiment; sourcea4d5a76
generalised the flag to `RD_ALE_CONTOUR_GAUSS=3/5` for an integration accuracy
control. Only equal-step contour LDA is enabled; default builds unchanged.
The actual C helper is tested by200 random nonuniform Euler states against
edge reversal, Galilean transformation and independent high-order rules.
Maximum edge/covariance defects are O(1e-15)/O(1e-14). Both degree tests pass.

All11 new native cases complete normally:4 initial uniform/short-Yee gates,
3 Gauss3 Sod controls,2 long Yee cases,1 Gauss5 uniform gate,1 Gauss5 Sod.
Three existing reference cases are reused unchanged. Sod ICs are identical
glass128², initial **single-tube effective Nx≈64**, gamma1.4, CFL.08,
cap1/3000, t=.08. All-node figures retain both global profiles and a zoom.

| Configuration | vx std in [.70,.76] | full-tube max vx | full-tube min vx | rho L1 |
|---|---:|---:|---:|---:|
| Static Roe GL/F1 | .022394 | 1.00935 | −.77657 | .0157632 |
| Zero-motion nodal contour | .120801 | 2.48730 | −.66237 | .0161405 |
| Zero-motion Gauss3 | .027307 | 1.04215 | −.72929 | .0157222 |
| Moving nodal contour, element frame | .082562 | 1.36551 | −.71756 | .0171760 |
| Moving Gauss3, element frame | .022730 | 1.05103 | −.74318 | .0171985 |
| Moving Gauss5, element frame | .022445 | 1.05165 | −.74922 | .0171945 |

The plateau interval avoids the exact shock at x_tube≈.780. Its standard
deviation is RD-area weighted about the regional mean, not a pure transverse
mode measurement. Moving scatter falls72.5% to approximately the static
level. The requested wider [.70,.80] exact-state vx L1 also improves:
.136595→.095329 (G3). Overall rho L1 increases only .13%; vx/p L1 become
.045830/.018404. The negative trough persists as expected. This supports
flux quadrature as a major cause of this particular scatter; it does not
prove the old discretisation inconsistent or solve every moving-LDA issue.

G3/G5 statistics are close (plateau standard deviations differ1.26%), but
long-time pointwise trajectories/fields differ: no pointwise quadrature
convergence claim is made. Short Yee lab/frame differences are≤5.11e-15;
long Sod lab/frame distributions have similar global statistics but are not
pointwise identical. G3 lab plateau std=.022740 confirms the improvement
does not rely on selecting the element frame.

Zero-motion G3 mass/energy drifts are1.97e-16/4.85e-16. Moving G3 frame
gives1.5393e-9/3.6272e-9; G5 gives1.5263e-9/3.6036e-9. This retains the
existing Arpaia-scale limitation without introducing the direct four-pass
imbalance. Both moving degree runs take970 steps with actual dt in
[7.8125e-5,1.5625e-4], versus969 old moving steps under the same controls.
Maximum repaired mass residual across the new campaign is7.11e-14.
Every stored new Sod output is admissible (minimum rho=.05615,p=.02993);
this is finite test evidence, not a positivity theorem.

Moving Yee at48²/96² and t=1, actualdt1/256 and1/512, retains smooth-flow
accuracy: G3 density h-order1.874, pressure1.937, velocity1.763, compared
with nodal contour1.816/1.874/1.708. Density/pressure errors increase modestly
while velocity errors decrease; there is no lumped-like near-first-order
degradation. Two resolutions from one glass family do not establish a
general asymptotic order, and no new fixed-h time-order claim is made.

The targeted Sod problem now has an effective tested correction. Treat
Gauss contour + GL/F1 as a baseline candidate; no KH/Gresho long-time,
independent glass seed, higher-resolution Sod, hierarchy or MPI validation
is inferred. Source, IC/config/binary hashes, logs, snapshots and checked
PNG/PDF figures are archived at
`/Users/zhenyuwu/arepo_rd/local_runs/sod_contour_gauss3_20260912`.
Full mathematics, tables, source/result provenance and reproduction:
[sod_contour_quadrature.md](colombo_re_spike/sod_contour_quadrature.md).
No thesis, CR/hierarchy algorithm, log1 or log2 changes were made.


## 29. Gauss contour cost and smooth/sharp moving KH (2026-09-12)

The user requested an explanation of Gauss3/5 versus the original moving
contour, measured cost, and a revisit of the historical scalar-B KH workaround.
The old physical contour exactly integrates the linear nodal flux interpolant
I_h F(U_i). Gauss instead integrates F(U_h), with conservative P1 U_h along
each edge. These are different nonlinear integrands. Three/five-point rules
are exact for polynomials through degree5/9, not for general Euler F(U_h),
and do not raise the complete P1/RK2 method to order5/9. Mesh transport, F1,
Arpaia geometry and refreshed basis repair are retained.

Per triangle per RK scan there are9/15 internal quadrature points. The current
correction-on-top prototype also repeats endpoints, giving15/21 physical
state-flux evaluations versus3 originally. This is not a whole-code5x/7x cost.
Eighteen serial native timings (two problems, three methods, three repetitions
in rotating order; one rank/thread;512 actual steps each) give CPU median
increases of .81%/2.20% for near-rigid uniform translation and2.91%/3.95%
for early smooth KH. The latter includes slightly differing flow trajectories;
these percentages describe the current local diagnostic build, not general
release/MPI performance. Concurrent long-run wall times are not used to
estimate quadrature overhead.

The historical successful scalar-B case in log2 §60.5 already used tanh
interfaces of width .025. Reconstructed that physical profile on the available
relaxed glass48²: rho=1+b, vx=-.5+b, vy=.1 sin(4 pi x), p=2.5, gamma1.4.
A sharp control replaces only b with an indicator. All four methods use the
same current equal-step settings, CFL.3, cap.02, fluid mesh velocity and
regularization, plus refreshed basis repair. This is not a byte-identical
reproduction of the unavailable historical IC or its no-repair binary.

| Smooth KH method | Outcome | Final rho range | Final mass / energy relative drift |
|---|---|---|---|
| Old nodal LDA | Negative mass at t=.444717 | Last saved t=.400085: .253–2.450 | — |
| Gauss3 LDA | Normal completion, t=10 | .84695–2.21388 | 2.3341e-8 / 1.9084e-8 |
| Gauss5 LDA | Normal completion, t=10 | .83938–2.13895 | 2.2674e-8 / 1.9641e-8 |
| Scalar B, nodal contour | Normal completion, t=10 | 1.00548–2.12783 | 2.3013e-8 / 1.4712e-8 |

Gauss runs contain no N blending. All51 saved states in each successful run
have finite positive rho/p; maximum logged raw distribution defects are
O(1e-17). Thus Gauss fixes the long-run survival problem for this smooth KH
case. It does not establish positivity or long-time accuracy generally.
Gauss preserves more density contrast than B and develops very different
late transverse kinetic energies (.07755/.06400 versus .02111 at t=10).
G3/G5 themselves differ by21% in that last statistic. Their entropy-proxy
excursions outside the initial p/rho^gamma range are larger than B at t=10;
this is a diagnostic, not an exact entropy error. Resolution, independent
glass and reference-solution checks remain necessary for accuracy claims.

All four sharp-interface attempts stop on the first step, t=.00061035156,
before flips, at the shared A2 spatial conservation assertion. This is not a
long-time KH instability ranking. A read-only matrix capture and a forced-SVD
build show rank3 Sminus; Phi has a nonzero component outside Range(Sminus).
The raw LDA sum projects Phi to Sminus*Sminus^dagger*Phi and loses that
component. For captured Gauss3 triangle4 the residual is1.26343e-11 versus
A2 tolerance9.79136e-14 (129x). Eighty-digit least squares reproduces it to
1.09e-20; sum Kplus + Sminus closes to6.94e-18. The old contour also has
this defect. More Gauss points alone cannot repair this spatial range issue.
No assertion was disabled/relaxed and no new null-space completion was added.
A conservative spatial completion is a separate next operator problem,
distinct from F1 temporal mass treatment and from edge-flip repair.

Main build source59b2161; read-only capture source3d6eea9. Eight main KH
starts (3 normal,5 diagnosed failures),2 capture/SVD probes,18 successful
fixed-step timings:28 native starts total. Checked density-evolution and
history PNG/PDF figures, inputs, binaries, logs, snapshots, algebra checks,
source/result commits and SHA256 provenance are archived at
`/Users/zhenyuwu/arepo_rd/local_runs/kh_gauss_20260912`.
Full derivation, data tables, limitations and reproduction:
[kh_gauss_and_cost.md](colombo_re_spike/kh_gauss_and_cost.md).
No thesis, default algorithm, CR/hierarchy, log1 or log2 changes.


## 30. P1/ALE contour derivation and late-KH literature comparison (2026-09-12)

User requested the full placement of Gauss in the contour integral, its
compatibility with P1, and comparison with SWIFT SPH / AREPO MMFV late KH.
No new native run or algorithm change in this follow-up. Code reviewed at
ede418b. Full equations and cited primary-source comparisons:
[gauss_p1_ale_math_and_kh_literature.md](colombo_re_spike/gauss_p1_ale_math_and_kh_literature.md).

For affine moving P1 triangles, the spatial strong residual integrates
(div F(U_h) - sigma_h dot grad U_h). Since grad U_h is constant, this equals
the boundary flux of F(U_h)-U_h*sigma_bar. The actual moving-control-volume
flux uses sigma_h instead and differs by integral U_h div sigma_h. Thus the
prior claim that mesh transport is already integrated exactly concerns the
frozen spatial operator with mean sigma, not the full space-time slab.
Gauss replaces only I_hF nodal interpolation by quadrature of F(U_h).
P1 constrains the state representation, not the nonlinear flux polynomial
degree. No new DOF, RK stage, F1 mass choice or basis repair is introduced.
Burgers flux provides a simple exact example: the integrated difference from
the trapezoid is -(b-a)^2/12 even with a P1 state. Ideal-gas admissible endpoint
states give admissible convex P1 quadrature states, not positivity of the
whole update. The sharp-KH range defect occurs in LDA distribution after
contour assembly; edge cancellation alone does not guarantee nodal sums.

Borrow et al.2022 SPHENIX §5.6/Fig.13 shows SWIFT sharp KH to10 tau_KH,
including a highly mixed late state. With density ratio2, velocity jump1 and
wavelength.5, that paper's time convention gives tau=1.06066, so ourt10 is
about9.43 tau (a scale comparison, not an exact finite-width growth rate).
Springel2010 AREPO Fig.32 only supplies the cited comparison through t2.
Mocz et al.2015 §3.1/Figs.1–3 shows that AREPO mesh regularization can remove
mesh-scale secondary KH structures even when old runs already use improved
RK/gradients. Lecoanet et al.2016 demonstrates the need to control diffusion
and noise when validating nonlinear KH. Therefore late disorder can accompany
nonlinear mixing, but specific fine structure is not certified physical by
its appearance. Current48² gives only24 initial spacings per seeded wavelength;
tanh delta=.025 is1.2h (not the entire transition width). Keep the strong
Gauss survival/Sod improvement evidence distinct from long-time accuracy.
Next validation priorities: primary-mode growth, higher resolution/another
glass seed, grid-scale non-primary power, late energy/mixing statistics.
No thesis, defaults or historical log1/2 edits.


## 31. Chapter4 Gauss draft and legacy Roe-split KH/Sod controls (2026-09-12)

User explicitly authorized updating Chapter4 mathematics and requested the
older Uhat/U mixed residual as an alternative to contour/Gauss. Added a
working subsection to local chapter4.tex (label ALE_RD_Gauss_physical_flux),
showing old nodal-flux versus nonlinear-P1-U quadrature, Gauss rules, unchanged
mesh transport/F1/RK2, and the legacy split alternative. Independent Chapter4
pdflatex wrapper compiles; new formula pages5–7 visually checked. External
chapter/bibliography references remain unresolved in this isolated preview.
Only Chapter4 changed; no push/pull or Overleaf sync, no Chapters1–3 edits.
The reviewed original, updated file and hashes are archived.

No C changes: source e33aea3 builds four existing-operator variants, KH/Sod
in lab/frame coordinates, explicitly enabling RD_ALE_SPLIT_MESH_VELOCITY
while disabling contour and Gauss. The old physical Roe integral is simple
because Euler U and F are quadratic in Roe parameters Z. Linear Z_h and
linear U_h lead to different flux fields; Gauss is not merely a more accurate
evaluation of the old Roe interpolant. Keep the old split as a valid control.

Eight native starts:2 uniform gates (max state change5.55e-16, zero total
drift),2 smoothKH,2 sharpKH and2 Sod. Match frozen current ICs, GL/F1,
Arpaia mass, refreshed repair, motion and original timestep controls. KH
uses glass48² and spectral CFL; Sod glass128² has effective single-tubeNx64.
Initial IDs, coordinates, conservative states and RD areas agree exactly
between new and reused baselines. Seven reference cases reused, not rerun.

Smooth split LDA fails in both lab and frame at t=.800476, at the sameID923
with negative mass approximately-1.064e-5. Last saved t=.800171 rho_min=.02683,
entropy-range excursion210.49, mass/energy drifts1.304e-8/1.456e-8. This
outlasts nodal contour (.444717) but does not reproduce Gauss3/5 survival to10.
Both sharp split cases stop at first-step A2 (defects2.65e-8/2.62e-8); no
assertion relaxation or new high-precision capture of these old operators.

Sod succeeds and supports the user's alternative for this particular issue:

| Scheme | Plateau vx std [.70,.76] | Full maxvx | Full minvx | rho L1 |
|---|---:|---:|---:|---:|
| Nodal contour | .082562 | 1.36551 | -.71756 | .0171760 |
| Split lab | .023080 | 1.07405 | -.79469 | .0175158 |
| Split frame | .022979 | 1.07389 | -.79902 | .0175099 |
| Gauss3 | .022730 | 1.05103 | -.74318 | .0171985 |

Thus old split suppresses72.2% of the targeted scatter, almost as well as
Gauss3, with slightly deeper negative trough and1.8% higher rho L1. The
wider[.70,.80] exact-vx L1 is.09797 versus Gauss3.09533 and nodal.13659.
Both split runs take969 steps; mass drift≈1.69e-9, energy≈3.92e-9. Coordinate
variants are not long-time pointwise identical but agree in the main result.
Gauss is not uniquely needed for Sod; its stronger current argument is the
combined Sod/smoothKH evidence. No general positivity or KH accuracy claim.

Figures, data, statuses, thesis snapshots/preview and provenance:
`/Users/zhenyuwu/arepo_rd/local_runs/legacy_split_20260912`.
Detailed mathematics and report:
[legacy_split_kh_sod.md](colombo_re_spike/legacy_split_kh_sod.md).
No default, hierarchy, log1 or log2 changes.


## 32. Extending legacy split with Gauss: equivalence, not a third scheme (2026-09-12)

User asked whether old Uhat/U split can receive an analogous Gauss extension.
For ideal-gas Euler, F(U(Z_h)) is quadratic on each edge of a linear-Z
triangle, so Gauss2/3/5 reproduce the old physical Roe residual. More points
on that same interpolant cannot supply a new stability improvement.
An added edge integral of F(U_h)-F(U(Z_h)) does change the old split, but
then exactly yields the existing conservative-P1-U Gauss spatial total.
With unchanged distribution/F1/time/topology, this is an alternative assembly
of the same method, not a new independent candidate.

Two engineering details: (1) Roe-to-Gauss correction can have a nonzero mass
component, so do not reuse the nodal-to-Gauss helper's mass skip. (2) Under
boost b, the directly recomputed difference transforms as G[deltaPhi minus
integral (b dot n)(U_h-U_Z)]; it is not simply G deltaPhi. Forming the full
corrected laboratory residual and transforming it avoids double-counting
legacy frame/split terms. Uhat is an auxiliary linearisation vector, not a
physical nodal interpolation to insert into F.

Independent Python algebra on200 random admissible-state triangles, rules
2/3/5, verifies Roe/Gauss-Z equality and corrected/direct-Gauss-U equality to
1.24e-14, and the boosted extra-term identity to1.22e-14. This is algebraic
verification, not a native timestep test or a new KH stability result.
Full derivation: [legacy_split_gauss_identity.md](colombo_re_spike/legacy_split_gauss_identity.md).
Script: tests/rd/test_legacy_split_gauss_identity.py; output under workspace
local_runs/legacy_split_gauss_identity_20260912. No C, thesis or default changes.


## 33. Static contour Gauss with hierarchy and MPI; frozen-F1 accuracy boundary (2026-09-12–13)

User chose to continue contour Gauss and asked to secure static hierarchical
timesteps with MPI before further moving development. Source255046f extends
two compile guards to allow static full-mesh LDA/F1. No spatial quadrature,
F1 update, ownership, exchange or tolerance algorithm changed. Gauss points
are reconstructed locally from the existing synchronized nodal/predictor
states; no new MPI payload or timebin variable is required. Moving one-rank,
moving-hierarchy N-only and active-mesh Gauss exclusions remain.

Twenty-seven native glass runs complete: uniform48, Yee48 equal-bin and forced
2:1 on1/2/4 ranks, Gauss3/5 controls, matched fixed-h timestep ladders, Sod
actualNx≈64 on1/4 ranks with equal/forced/CFL-selected hierarchy, and short
Yee48/96/192 spatial controls. Build source, five frozen binaries, configs,
IC hashes and complete logs/outputs are archived. One preceding sandbox MPI
launcher failure is retained separately; no AREPO evolution occurred in it.

Final mass/energy relative drift is≤1.45e-16/6.47e-16; mass-normalized momentum
drift≤5.79e-15. Maximum normalized four-component drift over saved snapshots
is8.54e-15. MPI state difference by ID≤1.36e-14; equal-bin degeneration to
internal RK≤1.29e-14. All coordinates and generator velocities remain static;
all saved rho/p are positive. Yee has2206 live/98 frozen vertices and due
triangle counts2402/4608. Natural Sod reaches three bins and max star ratio2;
forced refinement on CFL candidates also has three bins and max ratio4.

The full mathematical report explains edge/time cancellation and existing
MPI contracts. A material accuracy qualification emerged from extra controls:
**frozen LDA/F1 changes the fixed-h leading operator, not only time order.**
With lumped S, F1 action M, v=-S^-1 R and live mask P, equal-step leading
rate is v+(I-S^-1 M)v, while fixed-pattern hierarchy gives
v+(I-S^-1 M)Pv. The difference survives dt→0 at fixed mesh. This mechanism
comes from existing frozen-F1, not from new Gauss points.

At Yee48,t=.125, both equal and mixed-bin methods have time self-orders≈1;
the equal-step finding is consistent with log3 §26 and must not be blamed
entirely on hierarchy. Their U-L1 difference for caps1/256 through1/2048 is
5.028e-4→5.078e-4, rather than tending to zero. The short48/96/192 sequence
has falling errors but no stable second-order h result: rho orders equal
1.60/.93, hierarchy1.52/1.06; velocity1.60/1.23 versus1.39/1.30. This early
endpoint does not replace the earlier t=1 spatial campaigns. Do not promote
this conservative parallel baseline to accuracy-equivalent multirate RK2.

Sod hierarchy remains usable in these controls: rho L1 equal/forced/natural
.01572/.01456/.01437, minimum vx−.729/−.113/−.195. Reduced undershoot is not
a positivity or general accuracy proof; the mass action and local steps differ.
Existing rank-deficient F1 fallback remains and is not a positivity limiter.
Common-axis plots display every central-tube node and the exact solution.

For moving mesh, Gauss adds no new mathematical topology burden, but the
existing changing-area F1, geometric ledger, remote predictor/geometry and
flip-clock coverage problems remain. No moving hierarchy or MPI capability
was silently enabled. Next useful gate is moving fixed-connectivity LDA
with validated temporal mass and remote geometry, followed by coherent flip
patch/time settlement. Main report and figures:
[static_gauss_hierarchy_mpi.md](colombo_re_spike/static_gauss_hierarchy_mpi.md).
Archive: workspace local_runs/static_gauss_hierarchy_mpi_20260912.
Ready config: examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_HIER.sh.
No thesis, default Config, log1 or log2 edits.


## 34. Sod plotted coordinates, shock-local hierarchy and Morton comparison (2026-09-13)

User correctly noted that the improved discontinuity near plotted x=.8 lies
outside the forced x<.5 region. The plot uses xi=2(x-.25), so xi=.8 is raw
x=.65. The forced candidate-step halving is confined to raw x<.5 (also
xi<.5 in the displayed strip), but **the hierarchy/F1 algorithm applies to
the entire mesh**. CFL-generated timebin interfaces on the right also create
frozen stars. It was misleading to describe the comparison as if only the
left-half evolution changed.

Read-only audit of the existing final four-rank Sod snapshots: xi in[.78,.82)
(raw x in[.64,.66)) contains330 vertices in every run. Equal-step has330 in
bin19, none frozen. Forced hierarchy has125/205 in bins20/21, with131 frozen;
natural hierarchy has146/184 in bins20/21, with129 frozen. Bins19/20/21 mean
raw dt=7.8125e-5/1.5625e-4/3.125e-4. Thus the final shock-local vertex steps
in the hierarchy are2–4 times larger, not smaller, than equal-step. The
improvement cannot be described simply as extra local timestep refinement.
The existing frozen-F1 mass action and asynchronous trace treatment operate
at the shock as well as at the artificial mid-box split. This is evidence
of the local mechanism being present, not a controlled decomposition of how
much each mechanism causes the reduced trough.

The audit independently reconstructs the periodic static Delaunay stars from
3×3 tiled coordinates, verifies32768 distinct primary triangles, and exactly
matches the last native opening diagnostic's global frozen counts for both
hierarchies. Black dots in the new timebin figure identify these reconstructed
frozen vertices; no new AREPO integration was run.

Morton2023 §5.1.1/Figure7 were checked directly at
https://academic.oup.com/mnras/article/518/3/4401/6847219 . The paper uses
rho,p=(1,1)/(.125,.1), gamma5/3, CFL.4, first-order LDA/N, and a Cartesian
grid with alternate rows offset by half a spacing. Current tests instead use
gamma1.4, CFL.08, glass, and two-stage GL/F1. The current half-box cut and
rescaling is our periodic-pair presentation, not a documented Morton plotting
operation. Its effective Nx≈64 can be compared as a spacing-based single-tube
resolution, but the entire 2-D mesh/boundary setup is not thereby identical.

To interpret the central half-box as a unit-length 1-D tube with unchanged
rho,p,v, use **xi=2(x-.25), tau=2t**. Current raw t=.08 therefore corresponds
to unit-tube tau=.16. Exact gamma1.4 waves then lie at xi=.310685 (fan head),
.648392 (contact), .780345 (shock). At gamma5/3,tau=.16 the shock is.795116;
at gamma5/3,tau=.2 it is.868895. The latter is compatible with the supplied
Morton plot's approximate wave positions, but is an inference: the checked
paper section and Figure7 caption do not state the final time. Do not promote
tau=.2 to a confirmed original run parameter without original data/code.
Current exact overlays are consistent with current IC/time/gamma; they are
not the Morton analytic curve. Merely relabeling the x-axis cannot align EOS
and normalized evolutionary time.

Script: tests/rd/audit_sod_hierarchy_coordinates.py. Archive/figure:
workspace local_runs/sod_coordinates_20260913 (audit.json, shock_timebins PNG/PDF).
Existing campaign inputs/outputs were read only; no solver/thesis/default edits.


## 35. Moving Euler hierarchy retry: actual-interval star closure (2026-09-13)

User requested one more attempt to resolve moving-hierarchy edge flips before
deciding whether Chapter4 should present static hierarchy/MPI first and moving
mesh as an extension. **This attempt finds a constructive conservation route,
but does not enable it in native AREPO.** The proposed chapter structure is
still appropriate; the moving hierarchy now has a more substantial ongoing-work
result. No thesis edits were requested or made.

New `tests/rd/audit_euler_flip_closure.py` replaces the earlier scalar/synthetic
local-closure evidence with 2-D Euler, real periodic Delaunay changes,
Gauss3/P1-U LDA, a conservative Campoli-endpoint F1 two-stage interval update,
and stored per-triangle birth/last-integrated clocks. Natural bins remain
fixed; mesh velocities may change to fluid velocities at every refreshed
vertex. Complete old incident stars are closed before refreshing cavity
vertices and applying the EXISTING high basis repair, with the existing
full-patch positive low map available as a fallback. All successful cases
use theta=1: no CR graph remap diffusion is responsible for the result.

The decisive new condition is: **a vertex predictor is live only when all
its incident triangles are due AND share the same actual integration start**.
After event-induced truncation, equal timebins do not imply equal intervals.
Other star vertices receive ledger deposits without having their trace or
mesh velocity refreshed. Consequently local closure does not recursively
force the entire mesh onto the finest step or wait for a macro-sync.

At triangle endpoints A0,A1, let dA=A1-A0, M=(A0+A1)/2, and h its actual
interval. With midpoint-geometry Gauss LDA phi0/phi1 and vertex predictor dU,
the extensive deposit is

    dQ_i = (dA/3) U_i - (h/2)(phi_i0+phi_i1) + (dA/6) dU_i
           + (M/3) [dU_i - beta_i1 sum_j dU_j],
    dg_i = dA/3.

The final F1 correction is zero-sum; rank-deficient temporal action uses a
conservative lumped fallback. Summing gives the time-centered ALE edge flux.
Equal actual intervals cancel shared-edge stage fluxes; unequal intervals
have frozen shared-edge endpoint states, making the midpoint flux additive
over the linear-motion interval. Closing before trace/velocity changes
preserves that partition. Uniform states satisfy dQ=U dg. Full derivation
and assumptions are in `colombo_re_spike/euler_flip_closure.md`.

Negative controls on identical smooth Euler data at depth8 are decisive:
dying-only closure fails geometric coverage; full-star closure with the old
bin-live mask fails common-endpoint conservation at7.65239e-7; making every
fully closed vertex live fails at2.46771e-6. The actual-interval mask instead
reaches t=.1 with maximum drift3.02e-15. These are three expected failures,
retained in the archive. They are not a theorem excluding other multirate
methods, but explain why simply adding basis repair to old scheduling fails.

Final independent collection: **22 positive controls pass; three deliberate
negative controls fail as intended**. Highlights:

| Case | Changed-cavity events | Max normalized conserved-sum error |
|---|---:|---:|
| Uniform, prescribed motion, depth1024, t=.01 | 3 | 5.62e-14 |
| Smooth Euler, fluid motion, depth64, t=.1 | 9 | 3.49e-15 |
| Smooth Euler, seven populated bin bands1–64, t=.04 | 16 | 1.43e-15 |
| Glass48 Sod, fluid motion, depth8, t=.08 | 384 | 5.53e-15 |
| Glass48 smooth KH, fluid motion, depth8, t=.5 | 2092 | 4.44e-15 |

Events count connected changed cavities, not necessarily individual flips.
The final KH changes8526 triangle records and performs4161 early vertex
refreshes; its minimum observed ledger rho/p are1.00160/2.48689. Deep-uniform
state error is2.38e-14. The seven-bin and final KH controls perform37.3% and
58.7% of full fine-step triangle work; these are counts, not native speedups.
The first core18 cases use small jittered Cartesian meshes; later hydro uses
the retained glass48 generator coordinates. Glass48 means2304 full-box
vertices and **effective single-Sod x-resolution24**.

Glass Sod remains oscillatory: equal versus mixed min vx=-.629/-.459,
rho L1=.03277/.03467, vx L1=.09886/.09094. The equal control uses dt=.001;
hierarchy uses natural dt=.000125/.001, so this is not a matched-cost or
matched-finest-step accuracy comparison. All checked predictor and closure
states remain admissible, with minimum pressure over the run .03020/.04863.
A successful positive trajectory does not establish LDA/N transport
positivity. The same-time positive map cannot fix inadmissible pre-remap
physical transport. KH t=.5 is not a long-time t=10 validation.

The independent final spatial/temporal kernel matches a new two-step static
native Gauss3 LDA/F1 reference to2.665e-15 in conservative densities. That
single successful native run reuses immutable source255046f binary; no new
C build was made. The initial incomplete IC header failed before evolution
and remains archived. Initial lab-frame explicit-beta Euler experiments
hit roundoff range/conservation assertions; switching to direct RHS solves
in the element-comoving frame (as in the existing native contour path)
resolves them without relaxing the scaled assertion. Rank detection remains
an independent SVD/pseudoinverse policy, not native bitwise equivalence.
An initial follow-up launcher omitted an imported module; its four setup
failures are also retained, separate from the25 mathematical controls.

Native engineering still needs persistent triangle IDs/periodic image
records across mesh destruction, actual element dt weights, a forced-refresh
list, coherent changing-area mass action, and a single topology transaction
that does not also apply the old keep-U geometric correction. Moving MPI
adds ownership, full cavity/star data and history migration/restart contracts.
Existing moving-N/one-rank guards remain intact. Dynamic CFL-bin changes,
native regularization, geometric step rejection, long-time hydro and accuracy
convergence remain unvalidated. The frozen-F1 leading-operator qualification
from §33 is NOT resolved by this new conservation result.

Recommended writing boundary: established static hierarchy/MPI, followed by
validated equal-step moving extension; present this actual-interval closure
and its Euler tests as ongoing work until native integration and accuracy
gates pass. Do not claim either production moving hierarchy or impossibility.

Report: `colombo_re_spike/euler_flip_closure.md`. Runner and analysis:
`tests/rd/run_euler_flip_closure_campaign.py`,
`tests/rd/analyze_euler_flip_closure.py`; tracked core case list
`tests/rd/euler_flip_closure_cases.json`.
Archive: workspace `local_runs/euler_flip_closure_20260913`, including
source snapshots, failure records, JSON/NPZ outputs, native reference, and
`figures/closure_controls` and `figures/glass_sod_profiles` PNG/PDF pairs.
No production source/default Config, thesis, log1 or log2 changes.
