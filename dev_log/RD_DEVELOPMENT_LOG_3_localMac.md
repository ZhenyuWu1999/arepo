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
| 22 | Sod actual Nx=48 (full box 96^2): matched N/LDA RK2 topology comparisons and OpenMP runtime correction |
| 23 | High-repair semantics, LDA velocity ablations and older Sod plotting conventions |
| 24 | Actual Sod resolution and glass controls: GL/F1 undershoot and contour scatter without flips |
| 25 | Baseline first: four Heun paths, temporal versus spatial accuracy, and historical decisions |
| 26 | Matched advected-Yee baseline and auxiliary time ladder |
| 27 | Moving LDA baselines and the limit of direct ALE rate-Heun |
| 28 | Gauss physical-flux contour suppresses the Sod plateau scatter |
| 29 | Gauss contour cost and smooth/sharp moving KH |
| 30 | P1/ALE contour derivation and late-KH literature comparison |
| 31 | Chapter 4 Gauss draft and legacy Roe-split KH/Sod controls |
| 32 | Extending legacy split with Gauss: equivalence, not a third scheme |
| 33 | Static contour Gauss with hierarchy and MPI; frozen-F1 accuracy boundary |
| 34 | Sod plotted coordinates, shock-local hierarchy and Morton comparison |
| 35 | Moving Euler hierarchy retry: actual-interval star closure |
| 36 | Static Chapter 4 baseline audit and selective return to develop |
| 37 | Review of the static Chapter 4 baseline; accepted corrections, F1 hierarchy consistency, weakened spatial-order claim |
| 38 | Codex review of section 37: geometry bug in its scalar model, and five further qualifications |
| 39 | Static Chapter 4 priorities and a bounded F1 hierarchy repair direction |
| 40 | Where F1 enters the complete static update |
| 41 | Chapter 4 flowchart, hierarchy and MPI figure feasibility |
| 42 | Split static equal RK2 between the main-loop hydro hooks |
| 43 | Revise a copy of the AREPO flowchart to the loop body |
| 44 | Editable draw.io version of the revised main-loop figure |
| 45 | Moving-RD scope and proposed flowchart numbering |
| 46 | Experimental moving equal RK2 split; short gates pass, long pointwise gates fail |
| 47 | Remove the preview; common RD begin/end hooks with one mesh per step |
| 48 | Claude review handoff: current RD begin/end structure, one-mesh evidence, and editable flowchart locations |
| 49 | Review of the begin/end refactor and the revised main-loop figure; section 38 accepted |
| 50 | Apply the review: debug equal-bin guard and a numbered common-hook flowchart; correct the active-node drift attribution |
| 51 | Explore genuine old/new-mesh ALE stages: local conservative balance, independent Euler gates, and unresolved time order/positivity |
| 52 | Arpaia extension of the true split: topology balance alone is insufficient; derive and probe the additional endpoint-weight correction |
| 53 | Generic RD/FV function-name flowchart: remove static/ALE dispatch labels, retain numbered layout and preserve originals |
| 54 | Rename the two generic flowchart headings to first/second hydrodynamic stage; preserve function names |
| 55 | Sync thesis updates, insert the user-finalised PDF in Section 4.1, and prepare an RD/FV comparison table for review |
| 56 | Revise the comparison into a concise English table of numerical properties and their FV/RD ingredients |
| 57 | Insert the approved table with Voronoi/Delaunay elements and organise Section 4.1 into implementation and computational efficiency |
| 58 | Enlarge Figure 4.1 with a compact editable layout and a landscape thesis page, preserving the user-finalised originals |
| 59 | Export a native four-rank glass triangulation; verify ownership, periodic topology and MPI packets; illustrate real boundary examples |

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

> **2026-09-13 correction notice (see section 37).** Codex's section 18.1 raises
> four qualifications to this section and all four are verified correct. Three
> are errors of mine: (a) 17.6's regular-star threshold r*=13 describes the
> FULL-PATCH map and does not rehabilitate the active-only map, whose obstruction
> survives a regular star for r>6, so using it to "correct" section 16's
> active-only counterexample conflated two different operators; (b) 17.6's random
> Euler scan used low-Mach velocities and cannot support a positivity statement
> for arbitrary admissible states -- counter-streaming at density contrast 1
> already breaks the high map; (c) 17.4's convex-hull argument bounds CONSERVED
> components only, not pressure or specific entropy, so the relaxed-DMP limiter
> proposed there does NOT target the section-71.4 entropy excursion, which was
> its stated rationale. The limiter may still be worth having for positivity, at
> lower priority and for a different reason. 17.7's operator identity also holds
> only when the asynchronous remainder Q^- - g^- U vanishes.


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


## 36. Static Chapter4 baseline audit and selective return to develop (2026-09-13)

User requested a review of remaining static AREPO-RD issues, allowed returning
to develop_pureC_RD, and requested a Markdown table of the mathematical and
technical baseline. User clarified that static mesh should be treated as the
sigma=0, fixed-connectivity limit of the moving formulation. New primary note:
[RD_STATIC_BASELINE_CHAPTER4.md](RD_STATIC_BASELINE_CHAPTER4.md).
It records the unified ALE choices, their static degenerations, actual code
flags, measured evidence and limits on thesis claims. No thesis text edited.

The clean research branch remains test/colombo-re-explicit-hierarchy at53cb65a.
Switched this checkout back to develop_pureC_RD (previous315bece). Selectively
ported the existing Gauss helper, its lab/frame call sites, and static
full-mesh LDA/F1 contour guards; CR transfer, topology primitive-refresh,
moving Euler local-closure scripts and lumped diagnostic solver changes were
not merged. Carried forward the continuous log3/context and historical
reports, whose experimental code still belongs to their referenced branch.

Source484512a initially failed the standard make macro check because the
new option was not yet registered. Registered RD_ALE_CONTOUR_GAUSS in
Template-Config and froze corrected source943f7ae. All five configurations
then compile through normal make; no checks bypassed. The initial build
failure is retained separately and never entered fluid evolution.
Default Config.sh remains untouched. Two explicit reference configurations:

- examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_EQUAL.sh
- examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_HIER.sh

**26 new native runs complete normally.** Twelve replay gates (uniform;
equal, equal-bin hierarchy, mixed-bin Yee; Gauss3/5; natural hierarchy Sod,
ranks1/4) reproduce archived test-branch final conservative densities exactly
by particle ID: maximum U difference0. The new build retains the previous
static solver behavior without requiring unrelated moving experiments.
Maximum saved normalized four-component conservation drift across all26 is
2.0573e-14; maximum1/4-rank state difference, including KH t2,3.9524e-14.
Equal-bin degeneration difference≤1.2879e-14. Coordinates and generator
velocities are exactly static; area reconstructed from Masses/Density varies
by≤2.0817e-17. All saved rho/p positive and IDs intact. make check_rd passes.

Eight new static glass48 KH controls use the prior smooth width.025 and
sharp ICs, gamma1.4, p2.5, vy=.1 sin4pi x, CFL.3/cap.02, and zero mesh
motion. Both equal and natural hierarchy complete smooth t2 and sharp t.05
on1/4 ranks. Smooth minimum saved rho/p equal=.75707/2.07039,
hierarchy=.81522/2.08697; sharp=.91912/2.29443 versus.90513/2.31707.
Natural hierarchy actually has two bins, max ratio2 and max frozen counts
322/101. Static sharp KH does NOT reproduce the earlier moving sharp KH
first-step range failure; do not transfer that failure indiscriminately
between mesh-motion choices. These endpoints do not prove long-time accuracy.

Six additional Gauss3 advected-Yee t1 runs fill the gap left by the shorter
§33 Gauss sequence and the older Roe t1 references. Same glass family,
box10/gamma1.4/beta5/boost1, ranks4, n48/96/192, caps1/256,1/512,1/1024:

| Method | rho L1,48/96/192 | rho h slopes | velocity-vector h slopes |
|---|---|---|---|
| Equal Gauss3/F1 | 6.15304e-4 /1.67929e-4 /5.13448e-5 | 1.873/1.710 | 1.809/1.856 |
| Forced2:1 frozen-star Gauss3/F1 | 1.07819e-3 /3.59428e-4 /1.13916e-4 | 1.585/1.658 | 1.712/1.736 |

At192, hierarchy rho/velocity errors are2.22/1.75 times equal-step. This is
a coupled h/dt finite-resolution sequence, not a dt-extrapolated spatial-order
proof. The old fixed-h Gauss time orders≈1 and persistent hierarchy-minus-equal
limit from §33 remain valid; no time algorithm was changed here. Gauss t1
equal-step trends are comparable to old Roe/F1, but old tables were not
substituted for new Gauss measurements.

The baseline table makes distinctions that remain essential in the static
limit. Arpaia A_mid/modified-divisor and Campoli endpoint-average/new-area
weights coincide when Aold=Amid=Anew. The implemented local frame uses the
mean GENERATOR velocity, so sigma0 gives the identity Galilean transform;
it is separate from cosmological comoving coordinates, which are disabled.
However F1 versus lumped, and F(P1-U) versus F(U(P1-Z)), do not collapse when
sigma0. Select P1-U contour Gauss3, Roe K matrices, LDA/F1, lab-frame extensive
ledgers, full local mesh and existing ownership/exchange. Gauss5 is a control,
N/lumped and rate-Heun separate references. No Gauss point becomes a degree
of freedom or requires an additional MPI field.

**Audit decision:** freeze these named configurations as reproducible,
qualified Chapter4 experimental baselines; do not label the static solver
problem-free. Remaining material limits: standard two-stage GL/F1 fixed-h
time order1; frozen mask changes leading F1 operator; shock undershoot and
no general positivity theorem; hierarchical mid-stage restart unsupported
(run.c deliberately rejects stop/scheduled checkpoints there); no large-rank
scaling, active-only Gauss, forced migration, 3-D or cosmological validation.
Existing finite-row rank fallback is a temporal mass fallback, not a spatial
range completion or a limiter. If the chapter requires an accuracy-equivalent
second-order multirate LDA method, these results do not establish it.

Reproduction: tests/rd/review_static_baseline.py, stages
prepare/build/spatial/run/analyze, no CR imports. Archive:
workspace local_runs/static_baseline_review_20260913/native; includes frozen
source/configs/binaries, linkage, IC hashes, logs, snapshots, summary and
figures/yee_t1_spatial PNG/PDF. Failed initial build/check_rd log and branch
provenance are retained in the parent. New solver build source943f7ae;
later runner additions are case/analysis-only. No log1/log2 or thesis edits.

## 37. 2026-09-13: review of the static Chapter 4 baseline; accepted corrections, an F1 hierarchy consistency finding, and a weakened claim about spatial order

> **2026-09-14 correction notice (see sections 38 and 49).** Three errors in this
> section. (a) The scalar model of 37.5 wrapped connectivity indices but not
> coordinates, so seam triangles were built from opposite sides of the box: its
> operator norms are inflated by about 35% and its area sum was 3.4 rather than 1.
> Corrected in 49.1; the plateau and the stale-rate mechanism both survive the fix.
> (b) 37.4 offered the median-dual/Voronoi mismatch as a live competing
> explanation, but that attribution was withdrawn in volume 1 and the code uses
> DualArea throughout; the recommendation there stands, its stated reason does not.
> (c) 37.3 cited Morton figure 7 / section 5.1.1 for KH conservation; the correct
> reference is figure 6 / section 5.2.1.


**Author:** Claude Code (Opus 5), at Zhenyu's request. **Source reviewed:**
`603465e` (`943f7ae` for the native solver build). No production C, Config or
thesis file was changed in this entry and no native run was made; the checks
below are independent Python model problems and algebra, listed in 37.6.

Scope: review of sections 18--36 and `RD_STATIC_BASELINE_CHAPTER4.md`, answering
Zhenyu's two questions -- whether Chapter 4 may present the static mesh first
with moving mesh following, and whether the static solver can now be called
problem-free -- and recording his three directions on the answers.

### 37.1 Codex's four qualifications to section 17 are accepted

All four were re-derived in exact rational arithmetic and all four hold. A
correction notice now heads section 17. In summary:

1. The active-only obstruction is **not** an artefact of small exterior masses.
   With old nodal masses (1,1,1,1), new (5/6,7/6,5/6,7/6), A and C active and
   rho=(1,r,1,r), the required active mass is 2-r/3, negative for r>6. My
   r*=13 table describes the full-patch high map, a different operator; using it
   against section 16's active-only counterexample was a conflation.
2. Low density contrast does not imply positivity of the full-patch high map.
   On the same regular star with gamma=1.4, rho=p=1, vx=(4,-4,4,-4), E=10.5, the
   high map gives pressures (-7/45, 89/45, -7/45, 89/45). My random scan drew
   velocities from N(0,0.3) and never sampled counter-streaming; it cannot
   establish a theorem for arbitrary admissible states.
3. The section-17.7 identity between the widened active-only map and the
   production map omits the asynchronous remainder Q^- - g^- U, and holds only
   where that vanishes.
4. **The most consequential.** A convex hull of conserved vectors bounds
   conserved components, not pressure or specific entropy. On the same
   counter-streaming state every old p=1 while the conservative patch average
   has p=4.2: mixing converts kinetic to internal energy. Section 71.4 measured
   the excursion in specific entropy, so a relaxed component DMP does not bound
   it. **The stated rationale for the section-17.4 limiter is therefore wrong.**
   The limiter remains defensible as a positivity device -- qualification 2
   shows the high map does produce negative pressure -- but it is not the remedy
   for the recorded entropy excursion, and it drops in priority accordingly.

### 37.2 Chapter 4 organisation: agreed, with the emphasis made explicit

Zhenyu clarified that "moving mesh as ongoing work" always meant: present the
**equal-step** moving-mesh results as the substantive content, and mention
hierarchical timesteps briefly as ongoing work whose conclusions are not
settled. That is the same position reached independently here, and my earlier
concern was a misreading of the shorthand rather than a disagreement.

Writing the static mesh as the sigma=0, fixed-connectivity limit of the unified
ALE formulation is the right construction. The mathematics is stated once, the
chapter needs no restructuring when the moving material arrives, and the table
in section 2 of `RD_STATIC_BASELINE_CHAPTER4.md` does the load-bearing work by
naming what does **not** degenerate at sigma=0 -- F1 versus lumped, and
F(P1-U) versus F(U(P1-Z)). Those are exactly the two places where a static
result would otherwise be over-extended to the moving case.

The distinction worth keeping visible in the chapter is that the static limit
is a controlled baseline rather than a contribution: static triangular RD is
established work. The contribution lives in the ALE/moving material of tier 2,
and the chapter's framing should make that ordering evident so the static
sections read as validation rather than as the result.

### 37.3 Measuring the hierarchy's benefit: two figures, not one

Zhenyu asks for a figure demonstrating the benefit of hierarchical timesteps,
citing Morton (2023), where -- in his account -- the hierarchical timestep was
not conservative and the paper therefore plotted the relative energy error
against time on Kelvin--Helmholtz. Agreed, and the present situation calls for
two distinct figures because our conservation status is different.

1. **A relative-drift-against-time figure on KH.** Our static hierarchy is
   conservative to roundoff: section 36 records maximum normalised
   four-component drift 2.0573e-14 over 26 runs. Plotted against a
   Morton-style curve this shows directly that the predecessor's known
   non-conservation has been removed. This is a comparison to prior work, and
   its value is precisely that our curve is flat.
2. **A work-precision figure.** Because our curve is flat, figure 1 says nothing
   about whether multirate *pays*. That requires error against cost -- L1 error
   versus wall-clock time for equal-step and hierarchy at several resolutions,
   run to the same final time with the same spatial discretisation. This is the
   figure that answers the question the chapter actually poses.

**The second is currently unsupported: no speedup, wall-time or efficiency
measurement appears anywhere in the logs or reports.** Meanwhile the accuracy
cost is now measured -- section 36 gives hierarchy errors 2.22x (density) and
1.75x (velocity) of equal-step at 192^2. A chapter about hierarchical timesteps
that quantifies only the cost and not the benefit is incomplete, and the missing
half is cheap: the existing Sod and KH configurations need only to be timed.

Two cautions on the figures. Wall-clock on this laptop is noisy and was already
flagged as unusable for the earlier moving-mesh timing (section 71.2 of volume 2
recorded a shared node); cost should be reported as a machine-independent count
-- due-element sweeps or residual evaluations -- with wall time as a secondary
column. And `RD_STATIC_BASELINE_CHAPTER4.md` section 3 notes the Gauss contour
already raises flux evaluations per sweep from 3 to about 15/21, so the cost
axis must be defined consistently across both methods. On the Morton details,
`context_localMac.md` already records that his setup uses gamma 5/3, CFL 0.4 and
first-order LDA/N, and that section 5.1.1 / figure 7 do not state a final time;
any comparison figure must be labelled as a comparison, not a reproduction.

### 37.4 Spatial order: my contamination claim is weakened to an open question

I had argued that the section-36 Yee t=1 table cannot establish second-order
spatial accuracy because dt is refined proportionally to h while the measured
fixed-h time order is about 1, so the total error behaves as A h^2 + B dt and
the observed order drifts down rather than up. A two-term least-squares fit to
the equal-step density sequence gives A=5.54e-4, B=6.10e-5, reproducing the
observed 1.873 -> 1.710 and putting the linear term at 10%/18%/31% of the total
at n=48/96/192.

**Zhenyu's recollection that the time error was not important on earlier Yee
experiments is well founded, and it exposes a gap in that argument.** The fit
establishes only that a term **linear in h** contributes about a third of the
error at n=192. It cannot attribute that term to the time discretisation,
because a spatial error linear in h fits identically. There is a specific
competing candidate already on record: the median-dual versus Voronoi cell
inconsistency, open question 1 of `context.md` and still open, which the
2026-07-30 volume-1 entry proposed as the cause of exactly this signature.

The historical record does not separate them either. That entry measured
advected Yee orders 1.55 then 1.31 -- the same downward drift -- and attributed
it to geometry. Its boost=0 control gave clean 2.01/2.07, but a stationary
vortex is a steady solution, so the time-discretisation error vanishes
identically there; the control is therefore consistent with both hypotheses and
discriminates neither.

The decisive experiment is cheap and should replace the argument: **hold h fixed
at the finest resolution and refine dt alone.** If the L1 error against the
analytic solution falls by roughly the predicted third, the linear term is
temporal; if it barely moves, it is spatial or geometric and Zhenyu's
recollection is confirmed. Either way the presentational conclusion is
unchanged and modest -- a sequence with dt tied to h does not by itself
establish a spatial order -- but the cause should not be asserted until that
run exists.

### 37.5 The frozen-star F1 hierarchy is not a consistent refinement of equal-step

This is the one finding here that is not a qualification of something already
recorded, and Zhenyu has asked Codex to re-verify it. The model specification is
given in full so that it can be checked independently.

Sections 33 and 36 state that with lumped S, F1 mass action M, v=-S^{-1}R and
live mask P, the equal-step leading rate is v+(I-S^{-1}M)v while the hierarchy
gives v+(I-S^{-1}M)Pv, and that the difference survives dt->0. An independent
reimplementation confirms this and adds two observations.

First, the two-pass structure is exactly one Jacobi iteration preconditioned by
S toward the consistent-mass system M w = -R: starting from w0 = v,
w1 = w0 + S^{-1}(-R - M w0) = v + (I - S^{-1}M)v. This identifies what the
second pass is approximating and why masking it is not a neutral scheduling
choice.

Second, the magnitude. On a periodic perturbed structured triangulation with
scalar advection and LDA betas, ||I - S^{-1}M||_2 = 1.3012, 1.3747, 1.4163 at
n=12, 24, 48: an O(1) operator that grows slightly under refinement rather than
vanishing. Masking it at frozen vertices is therefore an O(1) relative change of
the rate there, not a small perturbation. (Uniform states remain exact because R
annihilates constants, giving v=0; this does not come from the row sums of
I - S^{-1}M, which are not zero.)

At fixed mesh n=24 with a fixed 50% frozen mask, RK2, T=0.05, the difference
between hierarchy and equal-step is 1.101510e-2, 1.101511e-2, 1.101512e-2,
1.101512e-2, 1.101512e-2, 1.101512e-2 for 50 to 1600 steps, i.e. constant to six
significant figures across a 32-fold reduction in dt. This reproduces the
native Yee48 observation in section 33, where the difference moved from 5.028e-4
to 5.078e-4 instead of falling.

**The mechanism is the masking, not the multirate schedule.** Replacing the
zeroed frozen rate with a stale one -- the frozen vertices contribute v
evaluated on their own frozen state, refreshed once per coarse step -- gives
differences 1.226056e-4, 6.103277e-5, 3.044877e-5, 1.520747e-5, 7.599507e-6,
3.798696e-6 over the same ladder: clean first-order convergence to the
equal-step answer. The cost is one extra residual evaluation per coarse vertex
per coarse step.

**Limits of this model.** Scalar advection, linear flux, fixed mask, fixed
geometry, no MPI, and the scalar beta rather than the matrix beta of the Euler
system. It locates a mechanism and is not a proposed production algorithm; in
particular it does not address how a frozen vertex's stale rate would be
obtained when its incident triangles are not due, nor what the equivalent
statement is once the mask itself changes with the solution. The value of the
finding, if Codex's re-verification sustains it, is that section 36's "frozen
mask changes the leading F1 operator" moves from an intrinsic accuracy cost to
be reported, to an implementation choice that may be repairable -- which would
also change what the work-precision figure of 37.3 is measuring.

### 37.6 Assessment and suggested order

The static baseline should not be described as problem-free, and
`RD_STATIC_BASELINE_CHAPTER4.md` is right to decline that description. It is a
defensible frozen baseline with declared limits. The material open items, in the
order I would address them:

| priority | item | state |
| --- | --- | --- |
| P0 | Timing/cost measurement for the hierarchy, and the two figures of 37.3 | benefit never measured anywhere; cost already measured at 2.22x |
| P0 | Fixed-h dt refinement at the finest Yee resolution (37.4) | decides between temporal and geometric attribution; either way the table cannot alone establish spatial order |
| P1 | Codex re-verification of 37.5, then a decision on the stale-rate variant | determines whether the hierarchy's accuracy cost is intrinsic or an implementation choice |
| P2 | Naming: standard two-pass GL/F1 has fixed-h time order about 1 while the configurations are named RK2 | already recorded in section 36; needs to be explicit in the chapter text, not only in the log |
| P3 | Section-17.4 limiter, on positivity grounds only | rationale corrected in 37.1; qualification 2 shows the need is real |
| declared | Sod undershoot and absence of a positivity theorem; mid-stage restart unsupported; MPI limited to 1/2/4 ranks with CREATE_FULL_MESH | acceptable as stated limitations |

Reproduction, all NumPy-only and independent of the solver:

```sh
PY=/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python
$PY verify_codex.py      # 37.1, exact rational checks of the four qualifications
$PY f1_consistency.py    # 37.5, operator norm and the dt ladder plateau
$PY f1_fix.py            # 37.5, stale-rate variant restoring first-order convergence
$PY order_fit.py         # 37.4, two-term fit; see the attribution caveat there
```

These are scratch model problems rather than archived campaigns; they are
retained under the session scratchpad and should be re-run from the listing
above rather than cited as provenance. They are not Euler PDE, MPI, moving-mesh
or convergence validation of the solver itself.

## 38. 2026-09-13: Codex review of Claude's Chapter 4 writing comments

**Author:** Codex (GPT-6), at Zhenyu's request. Reviewed section 37, its four
scratch scripts, the current static source, Chapter 4 draft, later historical
corrections and Morton2023. HEAD5f3db11; native baseline remains943f7ae.
No thesis, production C or Config edits; no new native AREPO runs. Claude's
235 staged log lines are preserved. Full review:
[RD_CHAPTER4_CLAUDE_REVIEW_20260913.md](RD_CHAPTER4_CLAUDE_REVIEW_20260913.md).

The proposed chapter structure and the fixed-h F1 mask diagnosis are accepted,
with six corrections/qualifications:

1. The median-dual/Voronoi mismatch invoked in37.4 was explicitly excluded in
   log1: update, primitive recovery and norms use DualArea, as current code
   still does. August1 completed dt ladders already separated the old jittered
   h-order defect from its sub-2% temporal effect. September11 Roe/glass native
   controls also measured small temporal effects. New Gauss192,t1 needs its
   own check; this does not make the historical evidence absent.
2. The scalar model wraps connectivity indices but not triangle coordinates.
   Its unit-box area sums are3.360967/3.673606/3.835069, with44/92/188 inverted
   triangles at n12/24/48. Independent assembly reproduces its reported norms
   and ladders. Correct periodic lifting gives area1, no inversions and norms
   1.020864/1.021939/1.022443, replacing1.301185/1.374722/1.416294.
3. The corrected n24 model still has a masked/equal plateau: mean nodal L1
   1.33024105e-2 to1.33024211e-2 for50--1600 steps, T.05. Cached-rate error
   falls1.13441625e-4 to3.52298429e-6; maximum weighted mass drift1.35e-16.
   Thus the mechanism survives the geometry correction. This all-node Heun
   ODE model implements no due-triangle scheduler, live-star closure or MPI;
   it establishes neither a production repair nor its claimed coarse-vertex
   cost. An operator norm is not a lower bound on every state's masked error.
4. A fitted31% linear-in-h share is not a measured temporal-error budget.
   Total L1 can rise as dt shrinks because errors cancel; historical native
   runs show that. Compare numerical states and use a verified dt ladder,
   not a predicted one-third drop. Continuous stationary Yee does not imply
   a discrete exact equilibrium or identically zero time error.
5. Morton KH conservation is Fig6 / section5.2.1. The Fig7/section5.1.1 and
   first-order solver details copied into37.3 belong to the earlier Sod audit.
   Use case-specific KH energy history and matched/declared settings; the
   26-run maximum four-component drift is not a KH energy time series.
6. Existing Gauss CPU/wall timings, GL/F1--rate-Heun timings and moving-model
   work counts refute the blanket claim of no cost measurements anywhere.
   They still do not supply the missing current static-hierarchy work-precision
   comparison. Timing Sod/KH alone is insufficient without an accuracy target.

Writing may proceed with static implementation/validation followed by equal-step
moving results and a brief moving-hierarchy outlook. Static RD theory is prior
work, but the conservative AREPO implementation and MPI/hierarchy audit remain
reportable project results. Efficiency claims require matched cost evidence;
implementing stale-rate is not a prerequisite for describing the existing
qualified baseline. Keep fixed-h time order and hierarchy operator differences
explicit, and retain section37.1's accepted corrections.

Reproduction: tests/rd/review_ch37_models.py (NumPy/SciPy, one OMP/BLAS thread).
Archive: workspace local_runs/chapter4_claude_review_20260913, with original
scripts/log snapshot and hashes, independent script, geometry/model JSON,
and exact active-only/pressure counterexamples. This is algebra/model evidence,
not new Euler, moving-mesh, MPI or spatial-order validation.

## 39. 2026-09-13: static Chapter 4 priorities and a bounded F1 hierarchy repair direction

**Author:** Codex (GPT-6), responding to Zhenyu's follow-up. Zhenyu agrees
that the hierarchical implementation needs a figure showing its benefit,
referring to Morton2023's non-conservative DRIFT KH energy history, recalls
small temporal effects on earlier Yee tests, and asks for an opinion on F1
hierarchical timesteps. This entry records advice, not authorization to switch
the baseline or a completed solver change.

A KH fractional-energy-drift history is a worthwhile result in its own right:
it demonstrates the conservation improvement relative to the earlier method.
Use current equal/hierarchical runs with actual bins and matching settings,
and describe any unmatched Morton comparison explicitly. A speed/efficiency
claim additionally needs work versus accuracy; the conservation figure alone
does not measure that. The September11 Roe/glass controls support Zhenyu's
memory: halving dt changes analytic density L1 by under1%, with state
differences about1.3--1.4% of the original error. A matched latest-Gauss check
is useful, but there is no basis to assert a one-third temporal contamination.

Recommendation: retain F1 and the current frozen-star implementation as an
identified reference, while prioritising recovery of the equal-step fixed-h
limit in an isolated static experiment. The current mask changes that limit;
this does not by itself prove failure of joint h/dt convergence to the PDE,
nor establish that the accuracy penalty is intrinsic to multirate methods.
The first repair target is consistency with the existing equal-step GL/F1,
whose measured fixed-h time order remains one, rather than simultaneous
replacement of the mass matrix, time integrator and spatial residual.

A concrete candidate is to separate the F1 mass rate from the hydrodynamic
stage trace. Preserve the existing shared frozen spatial trace. For mass
correction only, use current full-star v at live vertices and a timestamped,
previously complete full-star v at frozen vertices. On a static triangle let
a_i^T=h_T r_i and use the entire correction

    delta Q_i^T = (A_T/3) [ a_i^T - beta_i^T sum_j a_j^T ].

Its sum is zero when sum_i beta_i^T=I; apply the existing lumped fallback as
a whole on rank-deficient elements. Replacing both terms together preserves
this algebraic property for any common element rate data. Do not simply put
a coarse predictor into RD_dU: that field also changes spatial stage states.
The cached v must be normalised by the full nodal area and assembled over
the full star, not over only currently due triangles. Obtaining and exchanging
that rate with correct timestamps is the unresolved implementation/cost issue.

For a fixed smooth stable branch, a cache age of O(h_coarse) and a bounded
mass action would leave an O(h_coarse) rate perturbation, consistent with the
corrected scalar model in section38. This is a candidate derivation only.
The decisive next native gate would use fixed geometry and a fixed2:1 pattern,
refining both bins together and verifying that hierarchy-minus-equal tends
to zero while conservation remains at roundoff. Only after that gate should
one assess Yee h-error, Sod/KH behaviour, MPI and work--precision for the new
candidate. No native runs, C/Config changes or thesis edits made here.

## 40. 2026-09-13: where F1 enters the complete static update

**Author:** Codex (GPT-6). Zhenyu asks for the full-update position of F1
and why the current hierarchy is more than an equal-step scheduling change.
Source/read-only derivation; no implementation, run or thesis change.

For static median-dual S, Q=SU and assembled LDA residual R, write
w(U)=-S^-1 R(U). The equal-step predictor is delta U=dt w(Un), U*=Un+delta U.
F1 has element blocks m_ij^T=(A_T/3) beta_i^T for every j in T, so its mass
action couples the three nodal time increments. With the current mixed-stage
convention, the temporal mass uses beta* and the spatial halves use beta^n
and beta*, respectively. The full GL/F1 update is exactly

    Unew = U* - S^-1 M* delta U - (dt/2) S^-1 [R(Un)+R(U*)]
         = Un - (dt/2) S^-1 [R(Un)+R(U*)] + (I-S^-1 M*) delta U.

Thus F1 sits in the corrector's temporal residual; the method does not invert
the global F1 mass matrix. Setting M=S removes the last correction and gives
ordinary lumped Heun. The code's U*+delta U/2 form is algebraically identical
after substituting delta U=-dt S^-1 R(Un).

For each due hierarchy triangle with interval dt_T, the combined opening and
closing ledger increment is

    delta Q_iT = -(dt_T/2)[phi_iT(U0)+phi_iT(U1)]
                 +(A_T/3)[delta U_i - beta_iT* sum_j delta U_j].

The hierarchy supplies a full predictor at a stage-live vertex and zero at
a frozen vertex. Its Q ledger still receives increments: zero RD_dU is a
stage-trace policy, not zero conserved evolution. Reusing that zero in the
F1 mass action suppresses the frozen coupling and also changes neighbouring
vertices' temporal corrections. The correction still sums to zero per
element; global spatial conservation additionally relies on shared traces
and complete interval coverage. The rank-deficient lumped fallback removes
the temporal correction locally and does not invalidate this distinction.

For fixed mask P, smooth states and coherent interval coverage, taking all
steps to zero at fixed mesh yields w+(I-S^-1M)w for equal-step, versus
w+(I-S^-1M)Pw for the current hierarchy. Their rate difference need not
vanish. A scheduling approximation to the same discretisation should instead
recover the same fixed-mesh rate as all bins shrink with their ratios fixed;
finite-step equality is not required. Equal-bin degeneration P=I and exact
conservation therefore do not by themselves establish that stronger property.

Follow-up notation preference from Zhenyu: explain this using Chapter3's
existing nodal/element notation and define every added symbol before use.
Re-read chapter3.tex lines1009--1112: lowercase phi_i^T is the distributed
spatial residual, uppercase Phi_i^T includes the temporal mass contribution,
and F1 is the displayed LDA choice m_ij^T=(|T|/3) beta_i^{LDA,T}. If used,
delta U_i is explicitly U_i* minus U_i^n, the predictor increment, not the
completed step U_i^{n+1} minus U_i^n. Prefer these element formulas to newly
introduced global S/M/P/rate notation when explaining the mechanism. No
Chapter3 or Chapter4 edits made.

Zhenyu's subsequent assessment: a test can demonstrate that the conservative
hierarchy is not exactly equivalent to advancing all vertices at the finest
bin; he regards this as potentially a manageable limitation and asks whether
live/frozen interleaving is common to hierarchical methods. Agreed that this
need not block static Chapter4 writing or force an immediate repair. Distinguish
ordinary finite-step differences from the persistent fixed-mesh limiting-rate
difference already measured here. The current complete-star frozen rule is
stronger than simply being inactive on one fine tick; zeroing its F1 stage
increment is a specific choice, not a mathematical necessity of asynchronous
clocks. Existing cached-rate scalar controls illustrate the distinction without
establishing a native alternative. A useful presentation pairs conservation
with a controlled fixed2:1 timestep ladder against equal steps at the finest
interval, plus actual error/cost when judging utility. Severity should follow
observed accuracy, robustness and cost for the intended cases; disagreement
with equal-step alone neither disqualifies a method nor proves acceptable
PDE accuracy. User has not requested implementation of a new F1 variant.

## 41. 2026-09-14: Chapter 4 flowchart, hierarchy and MPI figure feasibility

**Author:** Codex (GPT-6). Zhenyu asks to consult log1/2 and the old thesis
resources, assess the feasibility of an AREPO/RD flowchart, a triangle-based
hierarchical-timestep algorithm with KH conservation/cost results, and MPI
responsibility illustrations. Full recommendations and source anchors:
[RD_CHAPTER4_STRUCTURE_FEASIBILITY_20260914.md](RD_CHAPTER4_STRUCTURE_FEASIBILITY_20260914.md).

Inspected the complete one-page 2023 Arepo_flowchart.pdf under MyThesis,
relevant old logs/notes, current source hooks, and the old task-responsibility
PNG/notebook under Desktop/arepo_test. The flowchart already includes RD;
redrawing must distinguish equal internal two-stage execution at the later
hook from static hierarchy predictor/corrector at separate hooks. The old
notebook uses majority-task ownership: reuse its visual style, not that rule.
Current full/persistent mesh ownership uses the minimum (ID,task) vertex's
primary instance, independently of due activity; active-only rebuild has a
conditional minimum-finest-bin rule. Large source refactoring is not a
prerequisite to drawing or writing.

Recommend three method figures (outer flow plus RD inset; triangle bins and
opening/closing timeline; MPI ownership and state/increment exchanges), then
KH energy history and matched work--precision results. The node remains the
unknown/timebin owner; the triangle is the residual scheduling unit. Use
Chapter3 notation and define additional symbols. Keep current frozen F1 as
an explicitly characterised implementation choice; user has not requested
a replacement and this need not block Chapter4 writing.

Read-only inventory of archived 943f7ae outputs is saved at
`../local_runs/chapter4_structure_review_20260913/existing_result_inventory_20260914.json`,
including snapshot hashes, actual times, energy histories and raw wall times.
Smooth KH equal/hierarchy at ranks1/4 each have11 snapshots through t=2;
maximum sampled fractional energy drift across them is2.77e-16. Hierarchy
rank1 sums to zero in this analysis and rank4 reaches1.38e-16: this is a
floating-point sampled result, not an all-stage exactness claim. Natural KH
has at most two bins here. The conservation history can be drawn now.

Found an important performance-comparison mismatch: forced two-bin Yee at
t=1 uses a finest step half the equal case under the same stated cap. For
48/96/192, equal uses1/256,1/512,1/1024 and hierarchy finest uses1/512,1/1024,
1/2048, respectively. Existing wall-time ratios are therefore not speedup
relative to equal-at-finest. The original times are also single-shot DEBUG
runs. Add matched actual finest steps and repeated, controlled timing before
an efficiency claim; pair analytic Yee error with cost and use KH for the
conservation/flow example. No new native simulations, C/Config changes or
thesis edits. Preserved the existing235 staged log insertions untouched.

## 42. 2026-09-14: split static equal RK2 between the main-loop hydro hooks

**Author:** Codex (GPT-6). Zhenyu authorizes trying the equal predictor at the
first hydro hook and corrector at the second, as the first implementation
step. He also clarifies the later diagram: timebins belong to nodes;
triangles use the finest incident-node frequency; frozen nodes passively
receive conserved increments without refreshing their stage state on each
such event. This turn implements and validates the code change only.

Implemented opt-in RD_RK2_SPLIT_STAGES and the explicit Gauss3/F1 trial Config
`examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_EQUAL_SPLIT.sh`. Static equal N/LDA
reuse the original full-step predictor/F1 corrector algebra across two calls;
hierarchy's ledger and frozen policy are unchanged. Stage Un lives in SphP,
predictor DualArea survives the corrector, and temporary triangle indices
are rebuilt. Renamed the internal algebra guard RD_RK2_INTERNAL_LOOP to
RD_RK2_EQUALSTEP so its name also fits split calls. Moving/B/four-pass Heun
remain internal and incompatible split combinations are guarded.

Added All.RD_EqualStepEnd as a binary-restart stage marker and endpoint
assertion. Pending checkpoints resume the corrector; a completed restart
starts a new predictor when extended. The initial extension test exposed
static restart mesh construction restoring particle bins but leaving
timebin lists in the temporary all-active bin. Split restart setup now
reconstructs the lists and active-bin metadata after restoring actual bins;
timebase extension also rescales the pending endpoint.

Full report: [RD_EQUAL_SPLIT_STAGES_20260914.md](RD_EQUAL_SPLIT_STAGES_20260914.md).
Final archive: `../local_runs/equal_split_stages_20260914_v2`. Frozen base
5f3db112 plus source patch SHA256
67d22fd4d3c1646f81a9bf4f9ebdb9f0222c1de176360f6a7284a0d6e9f2f7a9;
source tar SHA25636e534ca5ed2c57ddc2572c5a39a2f4208c73e4dc985349ce283c25c201c0d81.
Eight isolated configs;24 successful native cases/30 launches. Both thread
limits set to1. Same-rank split vs internal U is exactly identical for Yee,
uniform, Sod, N and KH(t=2), including Yee96 t=1 against the frozen archive.
All compared MPI/hierarchy degeneration differences <=1.29e-14; maximum
sampled normalized global conservation defect7.50e-15. Stop/resume and both
completed/pending checkpoint extensions reproduce continuous runs exactly.
Changing allowed domain parameters on resume migrates1155/2304 nodes before
the pending corrector; final difference6.66e-15. Ordinary repeated rebuilds
settle to zero transfers, so that separate remap gate supplies actual
migration evidence. All existing make check_rd algebra checks passed.

Preserved a setup-name failure, sandbox MPI launch failure and v1 endpoint
assertion failure; details in the report. The final working C/config source
matches the v2 archive. No speedup claim: split calls classify geometry twice.
Reference/default configs, thesis, historical logs and the existing235 staged
log insertions remain unchanged. No commit made; the opt-in code is ready
for review without promoting it over the named September13 reference.

## 43. 2026-09-14: revise a copy of the AREPO flowchart to the loop body

**Author:** Codex (GPT-6). Zhenyu requests retaining only the main-loop body,
lightly revising the wording, and editing a copy without touching the original.
Copied the 2023 PDF first, preserved its coloured vector layout, removed the
initialization/pre-loop lanes, and updated the two red blocks to the static
RD predictor/corrector hooks validated in section42. Retained FV labels and
conditional gravity/source/mesh context; no new equation notation added.

Merged mark_active_timebins into the next-sync-point box, matching the actual
call and removing the old crossing. Removed all seven FV formula /Stamp
annotations; replaced old outlined labels with searchable embedded-font text.
Rendered and inspected the complete final page, checked extracted labels and
verified that the original SHA256 is unchanged:
48d19858dcd4d93a478c4dd2105d4556803a78e7c01cec3132f962dca7af5d9a.

Delivered a new file beside the original:
`/Users/zhenyuwu/Desktop/MyThesis/useful_resources/Arepo_document/Arepo_flowchart_main_loop_RD_20260914.pdf`.
Final SHA256718c231c340926e239f2fe7c703b422038622ed40a303534203fa7444f9b1e15.
An identical workspace copy is under `output/pdf/`. Reproducible label editor
and notes are in `dev_log/figures/build_arepo_main_loop_flowchart.py` and
[AREPO_MAIN_LOOP_20260914.md](figures/AREPO_MAIN_LOOP_20260914.md).
No C, Config, thesis chapter or staged content changed in this figure turn.

## 44. 2026-09-14: editable draw.io version of the revised main-loop figure

**Author:** Codex (GPT-6). Zhenyu has installed draw.io and requests converting
the existing revised flowchart for manual editing, then explicitly requests
a white background for the thesis. Reconstructed 14 process nodes and their
14 attached loop connectors plus one entry arrow as native mxGraph objects,
with editable text, legend and notes on three layers. Preserved the PDF's
wording, colours and node geometry; no embedded raster/flattened PDF.

Opened and saved in draw.io 31.4.5, inspected the complete white layout,
verified attached-arrow behaviour by moving the predictor and undoing, then
checked the saved XML: white #FFFFFF background, original title, all14 stage
labels/positions and15 valid edges. Editor appearance changed from automatic
dark to Light following the user's white-background instruction. Original
and revised PDFs retain their previous checksums.

Delivered alongside the PDFs:
`/Users/zhenyuwu/Desktop/MyThesis/useful_resources/Arepo_document/Arepo_flowchart_main_loop_RD_20260914.drawio`.
SHA2569e17fc08018e39f0b45094fe21dec585d66ed5d342d75a13375b995557b47c5b.
An identical native source and its standard-library builder are in
`dev_log/figures/`; see [figure notes](figures/AREPO_MAIN_LOOP_20260914.md).
No solver, Config, thesis chapter or existing staged content changed.

Zhenyu then requests a second editable version retaining function names for
comparison. Delivered `Arepo_flowchart_main_loop_RD_functions_20260914.drawio`
in the same resource directory and `dev_log/figures/`, preserving the concise
version. It keeps the same14-node loop and descriptions, with wider boxes and
monospaced calls checked against current run.c/predict.c, including explicit
predictor/corrector stage arguments and the internal mark_active_timebins call.
Opened in draw.io and inspected a complete native CLI white-background render;
validated14 process vertices/15 edges and unchanged concise-source checksum.
Function-version SHA256cf149b7e0a4713b41482609eb14c745e9aa3db86994462204d31406a071919c4.
Builder and details are in the same figure directory/notes. No PDF, code,
Config, thesis chapter or staged content changed for this comparison version.

## 45. 2026-09-14: moving-RD scope and proposed flowchart numbering

**Author:** Codex (GPT-6). Zhenyu prefers the function-name figure, has made
minor edits, and asks whether it can also represent current moving-mesh RD
and whether its14 blocks should be numbered for Chapter4 references.
Located his edits in the workspace `dev_log/figures/` copy: the two gravity
boxes omit their in-box "(if enabled)" text; the optional legend remains.
Current user-edited SHA256645d20cf7045140d18e680f2c7904eac1acc5f91eadf18fdb55a3fe3fdd651d6.
The Desktop resource copy still has the original function-version checksum.
Preserved both copies, including the user's native-editor backup.

Code inspection on develop_pureC_RD confirms a common outer loop but distinct
RD stage placement. In run.c's first hydro hook (proposed block7), static
hierarchy and opt-in static equal split call the predictor; ALE hierarchy
skips it, and equal total-residual ALE also has no call. After drift and mesh
reconstruction, proposed block12 calls compute_residuals(&Mesh) for equal ALE
(both stages inside the solver), or calls predictor and corrector successively
for ALE hierarchy. Sources: run.c249--262,343--379; solver2427,2798,3827--3863.
The equal split option is explicitly restricted to static N/LDA at solver200--208.
Moving geometry is built on the post-rebuild connectivity, pulled back over
the drift/element interval; the two stages reuse that connectivity. This is
the current implementation's choice, not a necessity for every ALE method.

Recommend retaining one general AREPO/RD loop figure, qualifying blocks7/12
by static split versus moving RD, and describing moving mesh reconstruction
explicitly at block10. Simply removing "static" would misstate current calls.
Number1--14 along the actual edges (left1--5, middle6--10, right11--14);
use attached small corner labels so manual moves retain their numbers. Text
can discuss1--5 preparation,6--7 first hydro hook,8--11 time/mesh transition,
and12--14 closure. No figure edits or thesis prose were requested/performed
in this review; no code change or new numerical test is needed for this
call-graph inspection. Existing staged log content preserved.

## 46. 2026-09-14: experimental moving equal RK2 split; short gates pass, long pointwise gates fail

**Author:** Codex (GPT-6). Zhenyu asks to extend the two main-loop stage hooks
to moving mesh, testing at least equal timesteps. Implemented an opt-in
RD_ALE_EQUALSTEP + RD_RK2_SPLIT_STAGES path for one-rank N and standard LDA/F1.
The first hook runs a real predictor on a preview of the endpoint mesh;
the ordinary loop owns the physical drift/rebuild and the later corrector.
This retains the existing new-connectivity ALE formulation, but costs an
extra mesh build and a full temporary node/connectivity snapshot per step.
It is not a performance optimization or a default/reference replacement.

Node caches hold the original physical Q, repaired old U where enabled,
temporal divisor and endpoint area alongside the existing RK stage fields.
The second hook checks an order-independent connectivity fingerprint,
element count and per-node geometric agreement before consuming its saved
stage. Persistent DC lists and both RNG states are rolled back with the
node/timeline state; the neighbour tree is restored by rebuilding. Pending
and closed binary checkpoints, including TimeMax extensions, are supported
within this single-rank equal-step scope. Moving hierarchy/B/four-pass/MPI
remain outside this change. No change to the hierarchical F1 frozen policy.

Report: [RD_MOVING_EQUAL_SPLIT_STAGES_20260914.md](RD_MOVING_EQUAL_SPLIT_STAGES_20260914.md).
Named experimental Config:
`examples/yee_2d/Config_RD_ALE_LDA_GAUSS3_EQUAL_SPLIT.sh`.
Final archive: `../local_runs/moving_equal_split_stages_20260914_v4`, base
5f3db112, source patch SHA256
a11c167175a4fd53ba29a2f3c5aac02fcd33705fe41a36ec57265e3f04d5f7fc;
source tar SHA256433784d67e4a98ce21c386cdd4bbb4566e79d190fa115f20903849752f01275c.
All10 configs have isolated native binaries/headers/provenance. The25 cases
(28 launches) use2304-node glass48, periodic box10², gamma1.4, Yee boost1,
CFL.2, actualdt1/256 and one MPI rank with both thread limits1.

All25 runs complete, but this is **not an all-pass comparison campaign**:
11 of14 gates pass, while all3 t=1 pointwise pairs fail the original1e-10
threshold. Short Yee/N/Campoli/repair differences are <=9.77e-15; zero-motion
matches exactly. At t=.25,3 steps have changed connectivity and the LDA
maximum U difference is2.22e-14. Uniform error <=6.22e-15, normalized sampled
conservation <=9.95e-16. Pending stop/resume and both completed/pending
extensions reproduce continuous split runs exactly. All geometry guards
and predictor/corrector event-count checks pass.

At t=1, Arpaia/Campoli/Arpaia+repair have maximum U differences
9.25e-5/8.04e-4/1.41e-5 and coordinate differences
3.00e-4/4.28e-4/3.36e-5. Respectively131/132/125 of256 steps change triangle
connectivity (not counts of individual flipped edges). Timebins still match.
Two separate original-internal-method controls perturb IC x/y by1 and8 ULP
(max1.78e-15/1.42e-14); t=1 U differences amplify to3.29e-5/5.86e-5.
This supports mesh/state sensitivity as an explanation but does not prove
that every split discrepancy is roundoff. Kept all3 failed gates explicit.

Final-area-weighted analytic Yee density L1 is.00106156270547 internal and
.00106156270293 split; velocity-vector L1 is.00128675311903 and
.00128676040730. This does not establish a new convergence order or long
pointwise equivalence. Existing physical endpoint conservation limitations
persist: unrepaired t=1 drift about3.79e-5 and repaired Arpaia about9.94e-9
for both paths. The split does not solve ALE topology/endpoint conservation.
Single DEBUG t=1 process times3.70/5.32 seconds are smoke timings only.

Six static regressions on the v3 frozen source pass (same-rank exact;
maximum cross-path1.29e-14), including the retained static reference.
The only v3-to-v4 C change is RNG preservation inside the ALE split guard;
the static preprocessed path is unchanged. make check_rd passes all3
existing algebra scripts with the configured numerical Python.

Preserved v1's DC-chain rollback failure, v2's invalid wrapping-table Bus
error, v3/v4's long pointwise gate failures, and the first check_rd missing
NumPy log. A static runner invocation used the wrong CLI argument order and
was corrected before running. No assertions were loosened. A revised
analysis writer records all comparisons before returning failure.

Recommendation: keep this a reviewable experimental option. A14-box figure
can describe it if block7 explicitly includes rd_ale_split_predictor and
its endpoint-mesh preview; merely deleting the static qualification would
still misdescribe default moving and hierarchy execution. No figure or
thesis file changed, no commit made, existing235 staged log lines preserved.

## 47. 2026-09-14: remove the preview; common RD begin/end hooks with one mesh per step

**Author:** Codex (GPT-6). Zhenyu explicitly rejects the extra mesh build and
clarifies that the aim is the flowchart's outer form without extra numerical
work. Removed section46's preview implementation from the working source.
The main loop now calls rd_step_begin(&Mesh) and rd_step_end(&Mesh). Static
split/hierarchy still evaluate their predictor/corrector at those positions.
Equal ALE begin only records the pending endpoint; after the ordinary single
mesh rebuild, end executes the original internal predictor/corrector loop.
Moving hierarchy retains its original two consecutive post-rebuild calls.
This unifies step lifecycle hooks, not the numerical stage placement.

Deleted the speculative clock/drift, full P/SphP/DC/RNG snapshot rollback,
extra neighbour-tree/mesh build, per-node80-byte preview cache and repeated
ALE geometry preparation. Restored rd_ale_prepare_step exactly to the
pre-preview implementation. The first ALE hook now has only constant-time
endpoint checks, no node sweep or MPI collective. Existing equal binary
restart marker and TimeMax rescaling remain; a completed restart builds its
opening mesh before starting a new step. Historical SPLIT flag/Config names
are retained with explicit begin/end semantics in their comments.

Report: [RD_MOVING_SINGLE_MESH_HOOKS_20260914.md](RD_MOVING_SINGLE_MESH_HOOKS_20260914.md).
Frozen archive: `../local_runs/moving_single_mesh_hooks_20260914_v1`, base
5f3db112. Source patch SHA256
53c74844ed3107a97b7fac665f6ffdde2a5dacdfe0bc1b2f0d5f934666722ea7;
source tar SHA256cb6dcaefac2d019c3f9c660809c74aba178bc325b0036e6507089a2e5410b212.
Named Config: `examples/yee_2d/Config_RD_ALE_LDA_GAUSS3_EQUAL_SPLIT.sh`.
The final C/Template/defines source matches the frozen archive.

All25 moving cases/28 launches and14 comparison gates pass. Same-method
hooks/internal comparisons, pending stop/resume and completed/pending
extensions have exactly zero final differences in U, coordinates and area,
with identical timebins. Includes N, LDA/F1 Gauss3, zero-motion, Campoli and
topology repair/exact-patch controls through t=1. The previously failing
three long pointwise comparisons are now exact without changing tolerances.
All512 stage checksum lines in each of the three long hooks cases match
the corresponding previous-v4 original internal reference. The new internal
controls likewise match those archived original states exactly.

Setup remains2304-node glass48, periodic10², gamma1.4, Yee beta5/boost1,
CFL.2, actualdt1/256, one rank, both thread limits1. All stored rho/p are
positive; uniform maximum U variation6.22e-15. Exact-patch diagnostics detect
125 changed-connectivity steps out of256 in both long repair controls.
Physical endpoint conservation is unchanged; this refactor does not repair
the existing ALE topology/area limitations or establish a new accuracy order.

Every one of1216 begin/end intervals has exactly one mesh construction,
one ALE geometry preparation and two residual sweeps. Total campaign2272
physical steps. A256-step run logs258 builds:2 initialization builds plus
256 endpoint builds, identical to the original. Complete-step continuation
adds one opening mesh at restart, not one extra mesh per physical step.
No old RD-ALE-SPLIT preview log remains. Dominant numerical work counts are
unchanged; only function dispatch, endpoint checks and DEBUG lines are added.
Single DEBUG LDA t=1 wall times4.285/4.317 seconds are smoke timings, not a
claim of speedup or an exact measurement of call overhead.

Seven static regressions pass: same-rank internal/split,1/4 ranks, equal-bin
and mixed-bin hierarchy, uniform. Same-rank/archive differences are zero;
largest cross-path difference1.29e-14. make check_rd passes all3 scripts.
The first analysis combined restart logs in filesystem enumeration order;
sorting by filename restores chronological begin/end pairing. Kept that
analysis failure log; no numerical rerun or threshold relaxation was needed.

Figure recommendation: retain the14 boxes but label the red interfaces
Begin RD step / Complete RD step, with rd_step_begin / rd_step_end. The
caption must say moving ALE's two numerical stages run after rebuilding.
No figure/thesis edits were made; the user's modified draw.io hash is
preserved. Marked the previous focused report as superseded, retaining all
historical failed archives. No commit; existing235 staged log lines untouched.

## 48. 2026-09-14: 给 Claude 的审核入口——代码结构与流程图位置

**Author:** Codex (GPT-6). Zhenyu 要求在主日志中汇总，随后由他交给 Claude
审核。本节是当前状态的导航；实现与完整验证见 §47 和
[一次网格构造报告](/Users/zhenyuwu/arepo_rd/arepo/dev_log/RD_MOVING_SINGLE_MESH_HOOKS_20260914.md)。
**§46 的双网格预构造方案已经撤下，不是当前实现。**

### 48.1 用户要求及当前代码结构

要求是让 RD 在 AREPO 主循环中具有统一的前后两个入口，方便流程图表述，
同时不增加网格构造、几何准备或残差扫描。不要求为了方框位置重新设计 ALE 算法。

主循环的两个入口已经统一为：

- [run.c:260](/Users/zhenyuwu/arepo_rd/arepo/src/main/run.c:260)：`rd_step_begin(&Mesh)`。
- 正常的时间推进、domain decomposition 和 moving mesh 重建仍在两者之间。
- [run.c:366](/Users/zhenyuwu/arepo_rd/arepo/src/main/run.c:366)：`rd_step_end(&Mesh)`。

分派逻辑集中在
[residual_distribution_solver.c:3653](/Users/zhenyuwu/arepo_rd/arepo/src/hydro/residual_distribution_solver.c:3653)
和 [同文件:3675](/Users/zhenyuwu/arepo_rd/arepo/src/hydro/residual_distribution_solver.c:3675)：

| 路径 | 前入口实际工作 | 后入口实际工作 |
|---|---|---|
| static equal，启用 `RD_RK2_SPLIT_STAGES` | predictor | corrector |
| static hierarchy | predictor | corrector |
| moving equal，启用上述开关 | 只记录待完成的时间端点 | 在正常重建的新网格上连续执行原 predictor/corrector |
| moving equal，未启用上述开关 | 不执行残差扫描 | 原内部两阶段计算 |
| moving hierarchy | 不执行残差扫描 | 原来的两次阶段调用，顺序和位置不变 |

这里统一的是**步开始／结束接口**，不是所有方法的数值阶段位置。
FV 分支仍使用原来的 `compute_interface_fluxes(&Mesh)`。
已删除预构造函数、额外网格和邻居树构造、整份 P/SphP/DC/RNG 回退及节点预构造缓存。
ALE 几何准备回到一次调用，两阶段共用同一元素集合和几何。

相关文件还包括 [声明](/Users/zhenyuwu/arepo_rd/arepo/src/main/cpp_functions.h)、
[端点标记](/Users/zhenyuwu/arepo_rd/arepo/src/main/allvars.h:1058)、
[标记初始化](/Users/zhenyuwu/arepo_rd/arepo/src/init/init.c:67)、
[重启时间轴重标定](/Users/zhenyuwu/arepo_rd/arepo/src/io/restart.c:1334)，
以及 [完整步末重启的处理](/Users/zhenyuwu/arepo_rd/arepo/src/main/run.c:185)。
Config 的历史名称仍含 SPLIT，注释已说明 moving 的实际含义：
[Config_RD_ALE_LDA_GAUSS3_EQUAL_SPLIT.sh](/Users/zhenyuwu/arepo_rd/arepo/examples/yee_2d/Config_RD_ALE_LDA_GAUSS3_EQUAL_SPLIT.sh)。

### 48.2 流程图文件位置与当前标签状态

**优先审核用户手调的、带函数名的工作区版本：**
[Arepo_flowchart_main_loop_RD_functions_20260914.drawio](/Users/zhenyuwu/arepo_rd/arepo/dev_log/figures/Arepo_flowchart_main_loop_RD_functions_20260914.drawio)。
本次核对 SHA256 为
`645d20cf7045140d18e680f2c7904eac1acc5f91eadf18fdb55a3fe3fdd651d6`。
它保留用户对两个 gravity 框的手动文字调整；不要运行 builder 覆盖这份文件。

论文资源目录还有一份较早的函数名版本：
[资源目录中的 draw.io](/Users/zhenyuwu/Desktop/MyThesis/useful_resources/Arepo_document/Arepo_flowchart_main_loop_RD_functions_20260914.drawio)。
其 SHA256 仍为
`cf149b7e0a4713b41482609eb14c745e9aa3db86994462204d31406a071919c4`，
**与用户手调版本不同，不是自动同步副本**。
该资源目录解析到 `/Users/zhenyuwu/Desktop/PhD/Arepo_document`。

同目录的 [原始流程图 PDF](/Users/zhenyuwu/Desktop/MyThesis/useful_resources/Arepo_document/Arepo_flowchart.pdf)
和 [只保留循环主体的 PDF](/Users/zhenyuwu/Desktop/MyThesis/useful_resources/Arepo_document/Arepo_flowchart_main_loop_RD_20260914.pdf)
都保留；PDF 是较早导出，并不自动反映 draw.io 或此次代码调整。

**图本身尚未按 §47 更新。** 当前副标题和 scope 仍写 static RD，红框仍按
旧 predictor/corrector 调用表述。拟保持14个方框及连线，只调整两处入口：

- 沿实际流程顺序的第7框：`Begin RD step`，函数 `rd_step_begin(&Mesh)`。
- 第12框：`Complete RD step`，函数 `rd_step_end(&Mesh)`。
- 网格重建框仍在原位置，moving 每个正常大循环只重建一次。
- 图注交代 static split 的 predictor/corrector 分列两入口，而 moving ALE
  两个数值阶段均在重建后完成；不能直接把 static 字样删掉就算完成更新。

1–14编号仍是建议，尚未写入图；编号顺序为左列1–5、中列6–10、右列11–14。
本轮只补主日志，没有修改任何流程图、builder 或 thesis chapter。

### 48.3 验证入口和建议审核重点

冻结档案在
`/Users/zhenyuwu/arepo_rd/local_runs/moving_single_mesh_hooks_20260914_v1/`：
[结果汇总](/Users/zhenyuwu/arepo_rd/local_runs/moving_single_mesh_hooks_20260914_v1/summary.json)、
[最终核对记录](/Users/zhenyuwu/arepo_rd/local_runs/moving_single_mesh_hooks_20260914_v1/final_verification.json)、
[源码标识](/Users/zhenyuwu/arepo_rd/local_runs/moving_single_mesh_hooks_20260914_v1/source_provenance.json)。
25个 moving 算例、14组逐节点比较全部通过，状态／坐标／面积差为0；
包含 LDA 三个长时对照、N 短时对照、均匀流、零网格速度及重启/续算。
1216个启用接口的区间逐一验证为1次 mesh、1次 ALE 几何准备、2次残差扫描。
7个 static 回归与3组 `make check_rd` 代数检查通过。详细边界与计数见 §47。

建议 Claude 重点检查：接口命名是否准确反映上表的阶段位置；是否还存在隐藏的
重复构造或状态修改；pending/完整步 checkpoint 和 TimeMax 延长是否闭合；
流程图两份文件及未更新标签是否被正确区分。数值测试并不新增 moving MPI/
hierarchy 的科学验证，也没有修复既有 ALE 端点守恒问题。
源码和新配置目前未提交；已有235行 staged 主日志内容原样保留，勿混入提交。

## 49. 2026-09-14: review of the begin/end refactor and the revised main-loop figure; section 38 accepted

**Author:** Claude Code (Opus 5), at Zhenyu's request. **Reviewed:** HEAD
`5f3db11` plus the uncommitted working tree (`src/main/run.c`,
`src/hydro/residual_distribution_solver.c`, `src/main/allvars.h`,
`src/io/restart.c`, `src/init/init.c`, `Template-Config.sh`, `defines_extra`),
`dev_log/figures/`, and sections 38--48. No C, Config, figure or thesis file
was changed in this entry and no native run was made.

### 49.1 Section 38 is accepted, including the geometry bug in my scalar model

All of section 38's points were re-derived independently. The periodic mesh in
my section-37.5 script wrapped connectivity indices but not coordinates, so
every triangle crossing the seam was built from points on opposite sides of the
box. Reproduced exactly:

| n | total area (should be 1) | inverted triangles | norm mine / corrected |
| ---: | ---: | ---: | --- |
| 12 | 3.360967 | 44 | 1.301185 / 1.020864 |
| 24 | 3.673606 | 92 | 1.374722 / 1.021939 |
| 48 | 3.835069 | 188 | 1.416294 / 1.022443 |

With the lift corrected the area sum is exactly 1 with no inverted elements,
and **the mechanism survives**: the masked difference is 1.33024105e-2 to
1.33024211e-2 across a 32-fold dt reduction, while the stale-rate variant falls
1.134416e-4 to 3.522984e-6, matching section 38's figures. So section 37.5's
conclusion stands, but its quoted operator norms were inflated by about 35% and
its "grows under refinement" reading is much weaker than stated (1.0209 to
1.0224).

Two further corrections of mine, beyond what section 38 lists:

- **Section 37.4 resurrected a withdrawn hypothesis.** I offered the
  median-dual versus Voronoi mismatch as a live competing explanation, citing
  the 2026-07-30 volume-1 entry. That attribution was explicitly withdrawn
  later in the same volume (`### 6. Corrections to my own earlier entries`),
  and the code does use `DualArea` throughout --
  `update_primitive_variables.c:195` recovers density as `Mass / DualArea`. The
  competing explanation I named does not exist. The recommendation in 37.4 is
  unaffected: a sequence with dt tied to h still cannot establish a spatial
  order on its own, and a fixed-h dt ladder at the finest resolution remains
  the test. Only my stated reason for weakening the attribution was wrong.
- **Section 37.3 cited the wrong Morton figure.** KH conservation is figure 6 /
  section 5.2.1; the figure 7 / section 5.1.1 reference I used was copied from a
  `context_localMac.md` note about the Sod audit. Section 38.5 is right.

Section 38.6 is also right that "no cost measurements anywhere" was too blanket;
existing Gauss CPU/wall timings and model work counts exist. The specific gap I
meant -- a work-precision comparison for the current static hierarchy -- remains,
and section 38 agrees.

### 49.2 The begin/end refactor: the main loop now matches AREPO's structure

`run.c` now holds exactly two RD call sites, in structural correspondence with
the native pair:

```
260:  rd_step_begin(&Mesh);      262:  compute_interface_fluxes(&Mesh);
366:  rd_step_end(&Mesh);        368:  compute_interface_fluxes(&Mesh);
```

This is the right refactor and it achieves what was asked. Previously each site
required expanding `RD_HIERARCHICAL_TIMESTEPS`, `RD_ALE_HIERARCHICAL` and
`RD_RK2_TOTAL_RESIDUAL` together to learn what was actually called; the
dispatch now lives in the solver where the schemes are defined.

Points that are done well and are easy to lose in a later edit:

- `All.RD_EqualStepEnd` is a member of `All`, so AREPO's binary restart
  serialises it with everything else, and `readjust_timebase()` rescales it
  beside `Ti_Current`/`Previous_Ti_Current`. Integer-timebase rescaling on a
  `TimeMax` extension is a standard place to lose a saved endpoint; it was not
  lost here.
- The `RestartFlag = 0` assignment before the loop is correct. It reuses
  AREPO's own `if(RestartFlag != 1) { ... } else RestartFlag = 0;` structure:
  `RD_EqualStepEnd == 0` means the archive sits on a completed step, so the
  skip-to-second-hook semantics must not apply and a fresh step must open.
  Duplicate output is already prevented by the existing
  `if(All.Ti_lastoutput != All.Ti_Current)` guard, and nothing between the new
  assignment and the loop's own test at `run.c:209` reads the flag.
- The new stage assertion caught a real latent defect: `create_mesh()` places
  nodes in a temporary all-active bin and rebuilds the linked lists, and the
  previous restart path restored `P[].TimeBinHydro` without restoring those
  lists, so a rescaled `TimeMax` could select a wrong next synchronisation.
  That failure was silent before the assertion existed.
- Renaming `RD_RK2_INTERNAL_LOOP` to `RD_RK2_EQUALSTEP` names the algebra
  rather than an implementation detail, and is consistent with the fact that
  the path may now execute one sweep per call.
- The earlier moving experiment's mesh preview was withdrawn (section 47). That
  was the right call: it had to save and restore the persistent DC adjacency
  chain and the random-number stream, which is a large amount of hidden state
  to keep correct across a refactor.

Two recommendations.

**1. Split the commit.** The working tree currently mixes a behaviour-preserving
refactor (`rd_step_begin`/`rd_step_end`, the rename) with new functionality
(`RD_RK2_SPLIT_STAGES`, the new `All` member, new restart semantics). The first
is reviewable by the argument that nothing changed and is worth being bisectable
on its own; the second needs its 24-run campaign as evidence. Two commits would
separate those two kinds of claim.

**2. The ALE entry's timestep check is weaker than the static one, for no
reason.** `rd_step_begin` under `RD_ALE_EQUALSTEP` reads

    int bin = P[0].TimeBinHydro; /* FORCE_EQUAL_TIMESTEPS assigns the same bin to all nodes. */

and then validates only the range and `TimeBinSynchronized[bin]`, taking the
all-equal property from a comment. The static path validates the same property
properly, reducing both `min(bin)` and `min(-bin)` across ranks and requiring
them to agree. The ALE branch does require `NTask == 1`, so the risk is low, but
the quantity being guarded is an integer endpoint carried across two main-loop
call sites, and a violation would surface far away as a corrector mismatch.
Making the ALE check match the static one is a few lines.

### 49.3 The revised main-loop figure

The presentation decisions are right. Retaining the original coloured vector
boxes, loop layout and connectors while cropping initialization means a reader
who knows the AREPO paper figure maps onto it immediately. Merging the
synchronized-bin side box into the next-sync-point box is correct --
`find_next_sync_point()` does call `mark_active_timebins()` -- and removes a
crossing connector. Removing the seven FV-only `/Stamp` annotations was better
than leaving stale formulae. The scope note is in the figure itself, not only in
the accompanying document. Native draw.io XML with separate layers, rather than
a flattened export, is the right format for a figure that will be edited during
writing.

Three findings, in order of importance.

**1. The function-name version no longer matches `run.c`.** Its two red blocks
show

    RD: compute_residuals(&Mesh, RD_RK_STAGE_PREDICTOR)
    RD: compute_residuals(&Mesh, RD_RK_STAGE_CORRECTOR)

while the main loop now calls `rd_step_begin(&Mesh)` and `rd_step_end(&Mesh)`,
with `compute_residuals` one level below. The refactor and the figure were
produced in the same session and the figure was not updated afterwards. Since
checkability against the source is the entire purpose of this variant, this
should be fixed. The better fix is two lines per block rather than a
substitution: the hook call first, then the dispatched call indented beneath it.
That is more informative than either name alone, because it shows the hook is a
dispatch point whose target depends on configuration -- which is the content of
the refactor.

**2. "RD: predictor" on the first hook is false for the ALE split configuration
that now exists.** Under `RD_ALE_EQUALSTEP`, `rd_step_begin` performs no sweep
at all; it records the endpoint and both sweeps run at `rd_step_end` after the
single mesh rebuild. The figure's scope note restricts the RD labels to the
static path, so this is not an error in the figure as scoped. But
`Config_RD_ALE_LDA_GAUSS3_EQUAL_SPLIT.sh` now exists, and Chapter 4's
contribution is the moving path, so a figure whose RD labels describe only the
static case will need a companion. Deciding now whether to produce an ALE
variant -- begin records the endpoint with no sweep, end performs both sweeps on
the one rebuilt mesh -- is cheaper than discovering the need mid-writing.

**3. The active-list block carries a description that belongs to the next
block.** It reads "Build active-node list; drift nodes to the current time" and
lists only `make_list_of_active_particles()`. `drift_all_particles()` is at
`run.c:322`, inside
`if(All.HighestActiveTimeBin >= All.SmallestTimeBinWithDomainDecomposition)`,
i.e. in the following block and conditional; the per-particle drift is otherwise
lazy through `drift_particle()`, called from `create_mesh()` at
`voronoi.c:152`. The drift phrase should move to the domain/mesh block.

### 49.4 An unrelated find: `.gitignore` was eating the figure sources

While committing this entry, `git add dev_log/figures/` was refused. Line 15 of
`.gitignore` is `Arepo*`, under `#binaries` and intended for the root executable,
but it is unanchored, so it matches a path component beginning with `Arepo`
anywhere in the tree -- and `core.ignorecase` is true on this macOS checkout, so
the match is case-insensitive as well. The revised flowchart sources and
`AREPO_MAIN_LOOP_20260914.md` were therefore silently untracked.

This had already cost something. `dev_log/colombo_re_spike/arepo_integration.md`
is referenced from section 21 of this log and twice from the committed
`colombo_re_spike/README.md`, but the same rule dropped it when `484512a` added
that directory, leaving dangling references in committed history.

Anchored to `/Arepo*` and `/Arepo.dSYM`, which still ignores the root binary --
build outputs are already covered by the `build` rule -- and added an ignore for
draw.io's `.$*.drawio.bkp` scratch files. `arepo_integration.md` and the figure
sources are committed with this entry. Worth checking whether any other
thesis-facing file has been lost the same way.

### 49.5 Reproduction

The geometry re-check of 49.1 is `f1_fixed_geom.py`, retained in the session
scratchpad alongside the section-37 scripts. It builds the same scalar model
with and without the periodic lift, prints the area sums, inverted-triangle
counts and operator norms in the table above, and repeats the dt ladder for the
masked and stale-rate variants. It is a NumPy model problem, not solver
validation, and it supersedes the geometry of the section-37.5 script rather
than adding evidence.

## 50. 2026-09-14：落实 Claude §49 的代码与流程图微调

**作者：Codex；请求：Zhenyu 要求查看 Claude 的评论，并处理必要的代码与流程图微调。**
本轮从 `develop_pureC_RD` / `adc424ba93f8cb98ff494dd8e98b41fafcd2e98b`
开始；保留既有未提交改动，未切分或创建 commit。§49 的原文和作者记录保留。

### 50.1 审核结论与一处更正

同意 §49.2 对共同 `rd_step_begin/end` 入口、单次网格重建及 restart 处理的认可，
也同意 §49.3 要求流程图同时显示入口函数与其内部调用。新版用一张图标明 static
和 equal-step ALE 的差异：后者 begin 只记录终点，两次数值扫描都在 end 完成。
没有重新移动 ALE predictor，也没有恢复被撤回的预构造方案。

**§49.3 第3点对 drift 的归属不完整。**
`src/time_integration/predict.c` 的 `make_list_of_active_particles()` 在构建
hydro / gravity 活跃列表时，分别于当前第461、480行调用
`drift_particle(i, All.Ti_Current)`，条件是对应 bin 同步且该节点尚未漂移到当前时间。
因此第9框仍保留 drift，但限定为 synchronized nodes，并列出这个内部调用。
第10框单独标出 domain update 时的 `drift_all_particles()`；这不同于第9框的操作。
网格构造中的 lazy drift 也确实存在，但不是删除第9框 drift 描述的理由。

§49.1 对 §38 的接受记录继续有效。本轮未重新解释 F1 hierarchy 的精度问题，
也未将标量模型、守恒、空间阶或性能收益混为新的 native 验证结果。
Claude 已提交的 `.gitignore` 根目录限定及图源补录保持原样。
拆分行为保持重构和新增 split/restart 功能的 commit 建议留待提交时处理。

### 50.2 ALE begin 的全节点 timebin 调试检查

在 `src/hydro/residual_distribution_solver.c` 的 `rd_step_begin()` 中，
保留单 rank、非空、纯 gas、非 comoving、闭合步和首节点有效同步 bin 的现有检查；
新增 `RD_DEBUG_ASSERTS` 下的 `P[1..NumGas-1].TimeBinHydro` 一致性检查。
若不一致，在写入 `All.RD_EqualStepEnd` 之前报告节点下标、实际 bin 和期望 bin。

这是对 §49.2 第2条建议的有意限定：正式配置继续由
`FORCE_EQUAL_TIMESTEPS` 的分配规则保证相等，**没有额外全节点扫描或 MPI reduction**；
开启 `RD_DEBUG_ASSERTS` 的配置增加一次整数检查循环，以尽早发现违约。
本轮 native Config 开启该调试标志。没有修改残差、F1、网格或时间积分公式。

### 50.3 新图、编号和原件保护

可继续手动编辑的新图：
[工作区 draw.io](/Users/zhenyuwu/arepo_rd/arepo/dev_log/figures/Arepo_flowchart_main_loop_RD_functions_reviewed_20260914.drawio)，
[白底 PNG 预览](/Users/zhenyuwu/arepo_rd/arepo/dev_log/figures/Arepo_flowchart_main_loop_RD_functions_reviewed_20260914.png)。
同名 draw.io / PNG 已放到
`/Users/zhenyuwu/Desktop/MyThesis/useful_resources/Arepo_document/`
（实际目录 `/Users/zhenyuwu/Desktop/PhD/Arepo_document`）。

新版从用户手调的 `Arepo_flowchart_main_loop_RD_functions_20260914.drawio` 复制，
保留两个 gravity 框的文字修改、14个框的几何位置和全部15条连线。
新增1–14编号，编号是对应方框的子对象，拖动方框时一起移动。
第7、12框分别列出 `rd_step_begin/end`，并在其下标明 static 的 predictor/corrector
调用和 equal ALE 的记录终点／两阶段调用。第9、10框区分两种 drift；第10框注明
moving 每步重建一次、static 按需重建。图注明确覆盖 static N/LDA split-equal 或
hierarchy，以及带 split 标志的 equal ALE；未宣称已经验证 moving hierarchy。
初始化和 restart setup 不在这张主循环图中。

生成脚本
[build_arepo_main_loop_reviewed_drawio.py](/Users/zhenyuwu/arepo_rd/arepo/dev_log/figures/build_arepo_main_loop_reviewed_drawio.py)
校验输入 SHA、函数存在性、方框位置、连线和用户 gravity 文字，并拒绝覆盖已有输出。
不要用旧 builder 覆盖用户图。使用本机 draw.io 31.4.5 按 light theme / page size
导出，并实际查看最终 PNG：文字、分支、编号均在框内，背景为白色。
首次沙箱内启动 draw.io 失败；沙箱外本地导出成功，这是工具环境问题。

SHA256：

- 原用户工作区图未变：`645d20cf7045140d18e680f2c7904eac1acc5f91eadf18fdb55a3fe3fdd651d6`。
- 新 draw.io：`d4d124cac61c4e9e69660c2dd2a3cd5ad6565b98879f52cd9655de87f892038e`。
- 新 PNG：`980195e5c67bf8e5846093edf961fcbe7b7095d94d9ca4627d57cf388d100157`。

资源目录中的原 PDF、较早主体 PDF 和较早函数版 draw.io 均逐字节保留；
复制前后记录见下述档案的 `figure_delivery.json`。旧 PDF 不代表新版标签。
未修改 thesis 正文或原始流程图。

### 50.4 验证范围与证据

冻结档案：
`/Users/zhenyuwu/arepo_rd/local_runs/rd_review_polish_20260914_v1/`。
源码为上述 `adc424b` 加当时的全部相关工作树源码 diff，先冻结后编译：

- `source.patch` SHA256：`97e1d11312b4f8c4931e48578c4b56f73b73f74265ff1e9d8ba542b7ed0dd082`。
- `source.tar` SHA256：`b18aee79a1297fcddb6b8eb3348c808cdacf6e6fc993eec71d0ec3e779d9fb7c`。
- 本轮 solver 文件 SHA256：`1ca5e428a0578752a18fc7af6b34e0341dbb3b6ce1d1d7d5a10d27dbe9e13636`；与最终工作区一致。
- 单独的 `lda_split` 构建、Config、生成头、binary SHA、linkage、参数、IC SHA 和运行日志均保留。
  `make -j4`；运行单 MPI rank，`OMP_NUM_THREADS=1`、`OPENBLAS_NUM_THREADS=1`。

本轮只选择3个已有算例（没有重跑25例完整 campaign）：2304节点 glass48 Yee，
周期盒长10，LDA/F1、Arpaia、Gauss3、equal ALE，时间步长1/256。
比较参考是 §47 的 `moving_single_mesh_hooks_20260914_v1` 同名算例。

| 算例 | 最终时间 | 物理步数 | 网格构造总数（其中 setup） | 保存快照数 | 一致的阶段校验记录数 |
| --- | --- | --- | --- | --- | --- |
| `yee_lda_split` | 0.125 | 32 | 34（2） | 3 | 64 |
| `extend_lda`，完整步 checkpoint 后延长 TimeMax | 0.25 | 64 | 67（3） | 5 | 128 |
| `pending_extend_lda`，pending checkpoint 后延长 TimeMax | 0.25 | 64 | 66（2） | 3 | 128 |

5次进程启动全部成功。每一个 begin/end 区间均验证为1次 mesh、1次 ALE 几何准备、
2次残差扫描。全部11份保存快照按 ParticleID 比较，守恒密度、坐标和 median-dual
面积的最大差均为0，ID / timebin 完全一致；320条阶段 checksum 文本也完全一致。
参考比较的可执行脚本和结果分别为 `compare_previous.py`、`previous_comparison.json`；
主分析为 `summary.json`（明确记录 completed 3 / planned 25）。

另外，`check_begin_guard.py` 从冻结源码直接提取真实 begin 函数，以最小 C 状态夹具
编译 debug / non-debug 两种版本。20项检查通过：debug 11项、non-debug 9项。
其中第二节点或最后节点 bin 不同均在记录终点之前被拒绝；还覆盖有效输入、非法 bin、
不同步、空输入、非纯 gas、多 rank、comoving 和重复 begin。预处理输出确认 non-debug
不包含新扫描。夹具不执行物理残差，不能代替以上 native 测试；它验证的是入口契约。
详见 `guard_summary.json` 和 `guard_harness/`。
`make check_rd PYTHON=/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python` 的3项既有代数检查通过。

这些结果验证了新增调试检查的行为和已有解的保持。它们不构成速度测量或新的
moving MPI / hierarchy 验证，也不修复既有 ALE 守恒误差：本轮短 Yee 的归一化总量
最大漂移约 `2.30e-10`，两种延长情形约 `1.41e-6`，与参考一致。

## 51. 2026-09-14：探索数值上真正分开的 moving ALE-RD 两阶段

**作者：Codex；请求：Zhenyu 要求探索修改数值方法，让 predictor / corrector
真正位于网格移动和重建前后，同时保持每物理步一次 Delaunay 构造。**
工作树仍为 `develop_pureC_RD` / `adc424ba93f8cb98ff494dd8e98b41fafcd2e98b`
加此前未提交改动；本轮没有修改 native C、Config、已有流程图或 thesis，未创建 commit。
当前 ALE begin/end 的实际行为仍为 §47、§50 所述。

完整符号、推导、反例、复现方法和 native 落地边界见
[RD_TRUE_ALE_SPLIT_EXPLORATION_20260914.md](RD_TRUE_ALE_SPLIT_EXPLORATION_20260914.md)。
这是一个新候选的独立数值探索，不是已启用的 AREPO 算法。

### 51.1 候选与成立的结论

equal-step begin 已知 dt 和节点速度，所以可以在不构造未来 Delaunay 网格的情况下，
计算旧连接关系的向前几何和真正的 predictor。正常移动后只构造一次新网格；
corrector 的第二次残差及 F1 时间质量项使用新连接关系及其拉回几何。

朴素混用旧/新残差不守恒。本轮在项目已有的 **Campoli endpoint-mass 配对**上，
推导了跨连接关系的精确总量缺口：每个完整 changed cavity 内，
“新减旧的起点面积差 + 新减旧的终点面积差”的一半乘以起点节点密度，再求和。
按新节点完整 median-dual 面积分配并扣除该局部向量，恰好消去缺口。
无翻边时修正为零；均匀状态在完整区域内也给出零修正。
这是局部几何代数项，不需要第三次物理残差扫描；但会增加缓存、两套几何计算和区域匹配，
**没有 wall-time 零开销结论，也没有直接替换当前 Arpaia 形式**。
新修正由本轮推导，并非 Campoli 文献已证明的跨拓扑算法。

### 51.2 独立实验：守恒通过，但不能据此宣称完整二阶/正性

主组为二维周期单位盒、256 个 jittered Cartesian 节点、512 三角形，
固定线性节点路径，64 步到 t=.25，dt=1/256。10 个标量/Euler 的 N/lumped 和 LDA/F1
uniform、density/entropy wave、Yee 型 vortex 测试全部完成。每例48个翻边步，
累计170个删除三角形，最大区域7节点；65次构网含1次初始化，64次 predictor /64次 corrector。
Euler 最大归一化总量漂移1.89e-15，均匀状态误差5.33e-15；逐步独立核对缺口公式，
最大绝对差4.97e-15。已测 predictor/最终状态密度和压力均为正。

这不是 native Euler 代码的完整移植：未覆盖实际 mesh-velocity 反馈、
sigma≈u 的奇异 Roe 情况、完整 element-frame / Uhat / limiter、shock、MPI、hierarchy
或 restart。小涡核的256节点例仅为非线性可行性测试，不是 thesis Yee 精度基准。

时间精度检查保留了失败证据：144节点固定连接关系的极限 ODE 对照，N/lumped 时间阶≈2，
LDA/F1≈1，重现既有 F1 限制；加入真实拓扑转换后，新候选对2048步参考的最后细化阶
约1.12 /1.22，没有清楚的时间二阶。该参考有限，斜率不是严格渐近阶。
新候选的64/256/1024节点光滑标量空间组，h和dt同时减半，LDA/F1 的 h 斜率1.780/1.891；
不能以此替代 native glass Yee 或固定h时间分析。

另有确定的正性反例：单位方形四节点的瞬时翻边，将正输入(.01,10,.01,10)
按该无限制局部修正变成(-3.32,6.67,-3.32,6.67)，总量仍为3.34。
因此这是**守恒但不普遍正性**的候选；需额外 admissible 限制或步长策略，不能直接投入激波。
此前的 full-patch high map 的同类局限继续有效。

### 51.3 产物和后续建议

本轮新增5个实验脚本和1个绘图脚本，均在 `tests/rd/explore_true_ale_split*.py`
及 `tests/rd/plot_true_ale_split_exploration.py`。
档案在工作区 `local_runs/true_ale_split_{scalar,euler,order,balance,balance_checks}_20260914_v1/`，
各自包含运行前冻结脚本、SHA256、原始结果；总体验证记录在
`local_runs/true_ale_split_audit_20260914_v1/manifest.json`。
旧连接 corrector + remap 的备选结果与新候选分别保留，不混作同一方法的证据。
时间/空间对照图为 `dev_log/figures/rd_true_ale_split_order_20260914.png` / `.svg`。

建议首先审查局部总量修正与正性限制，再考虑 opt-in、单rank、equal-step、Campoli 的
native 试验；同时实测额外几何/区域匹配开销。完整轨迹几何有效性、按ID持有缓存、
两hook间checkpoint的数值状态保存都是实际移植条件。
若要求固定h完整时间二阶，F1 stage 速率一致性与翻边事件/状态转移还要分别处理。
现有四扫描 rate-Heun 的 ALE 不守恒问题不能通过此处形式拆分消除。

solver SHA256 仍为 `1ca5e428a0578752a18fc7af6b34e0341dbb3b6ce1d1d7d5a10d27dbe9e13636`。
原用户函数图和 §50 reviewed 图哈希均未变；没有为未落地的候选改动流程图。

## 52. 2026-09-14：真正两阶段方案是否也适用于 Arpaia

**作者：Codex；请求：Zhenyu 追问 §51 的方案仅对 Campoli 成立，还是也对 Arpaia 成立。**
结论：两入口分别计算旧/新连接关系上的阶段，对二者都可组织；但 §51 的
仅翻边区域修正对 Arpaia 不充分。核对 `rd_ale_triangle_geometry_build()`、
`rd_ale_prepare_step()` 和 `rd_ale_finish_step()` 后，推导额外 endpoint-weight 项。
详见 [Arpaia 补充报告](RD_TRUE_ALE_SPLIT_ARPAIA_20260914.md)。

令 d_i 为新连接关系的“终点 median-dual 面积减 Arpaia 更新分母”，
即新连接关系起终面积均值减中点面积；Uhat 为未修正的 corrector 密度。
跨连接关系的总量缺口恰为 §51 的 topology 项，加 `sum_i d_i*(Uhat_i-Uold_i)`。
只扣 topology 项后，即使没有翻边也会剩余后一项。保持 Arpaia 内部配对时，
可以在各节点终点 Q 写回中额外扣 `d_i*(Uhat_i-Uold_i)`；该项需使用修正前的 Uhat。
两项相加给出一个新的守恒 Arpaia-based 变体，仍不增加网格构造或物理残差扫描。
它一般不局限于翻边节点，且不等价于换成 Campoli。

新增 `tests/rd/probe_true_ale_split_arpaia.py`：144节点周期 jitter mesh，dt=1/16，
固定连接/实际Delaunay重建（删除26三角形）、N/LDA、标量/Euler、均匀/非均匀共16组，
每组另有 Campoli 对照。缺口公式最大绝对误差1.76e-15；全部修正后2.22e-15；
均匀密度向量误差3.11e-15。仅拓扑修正的无翻边 N Euler 对照仍有能量缺口-1.626e-6。
修正后两配对仍有非零逐点差，不能宣称它们成为相同算法。
档案为工作区 `local_runs/true_ale_split_arpaia_20260914_v1`，含运行前冻结脚本及SHA。

这是16组独立单步恒等式核对（含参考共32个更新），不是新增native、多步稳定性或收敛证据。
§51 的时间阶/正性问题继续存在；没有修改 C、Config、流程图、thesis 或旧报告/档案，
没有创建commit。当前代码中的 Arpaia 仍未加入本文提出的修正。

## 53. 2026-09-14：流程图改用通用 RD / FV 表述

**作者：Codex；用户决定：moving-mesh 数值方法研究留待以后，当前回到流程图，
去掉 static RD 限定，笼统表示 RD 或 FV。**

从 §50 的编号函数版复制新文件
`dev_log/figures/Arepo_flowchart_main_loop_RD_FV_functions_20260914.drawio`，
另导出同名白底 PNG。标题、图注和第7/12框统一使用 RD or FV；两个 hydro 框分别为
Begin step / End step，保留 `rd_step_begin/end(&Mesh)` 与
`compute_interface_fluxes(&Mesh)`，删除 static / equal ALE 的内部 dispatch 细节。
第10框改为按需 domain/tree update 与 mesh construction；不再列 static/moving 分支。
这张图表达共同主循环入口，未把尚未落地的真正 ALE 两阶段方案画成现有实现。

14个方框、1–14编号、全部15条连线、颜色、位置及用户手调 gravity 文字均保留。
图中不再出现 static、moving、ALE 或 `RD_RK_STAGE_*` 标签。
新 builder 为 `dev_log/figures/build_arepo_main_loop_rd_fv_drawio.py`，只改8个文字对象及
页面名称，验证其余 XML 内容不变并拒绝覆盖输出。

用本机 draw.io 导出2802×2562 RGB PNG，light theme / page size / scale2；
实际查看全图，文字、函数名、编号、连线均正常，背景像素为白色。
draw.io和PNG已以新文件名放入用户的
`/Users/zhenyuwu/Desktop/MyThesis/useful_resources/Arepo_document/`
（实际 `/Users/zhenyuwu/Desktop/PhD/Arepo_document/`）。旧图与PDF逐字节保留。
交付及哈希记录：工作区 `local_runs/flowchart_rd_fv_20260914_v1/delivery.json`。
新 draw.io SHA256：`f9c29f50570aae1336867219d1e37865162ea2737ef69b46818880e33110ca33`。
未修改 solver、Config 或 thesis 正文，也未继续 moving 数值实验；本轮不需要 hydro 回归。

## 54. 2026-09-15：流程图采用 first / second hydrodynamic stage

**作者：Codex；请求：Zhenyu 认为 begin/end step 的语言不理想，提出 first/second
或 predictor/corrector。** 采用 First hydrodynamic stage / Second hydrodynamic stage，
用 stage 表示同一时间步内的阶段，并保持通用 RD/FV 主循环含义；没有为所有 RD/FV
路径指定 predictor/corrector 数值语义。实际函数名 `rd_step_begin/end` 保留。

仅改第7、12框标题，保留 `(RD or FV)`、函数名、所有其他文字、14个编号方框、15条连线
和白底布局。新文件为 `dev_log/figures/Arepo_flowchart_main_loop_RD_FV_functions_20260915.drawio`
及同名PNG，已放到用户 thesis 的 Arepo_document 资源目录，9月14日及更早版本均保留。
用 draw.io 原生导出2802×2562 PNG并查看，两个新标题均完整显示。
编辑和交付记录在工作区 `local_runs/flowchart_rd_fv_stage_labels_20260915_v1`。
无 solver、Config、数值实验或 thesis 正文改动。

## 55. 2026-09-15：同步 thesis、插入 4.1 流程图、整理 RD/FV 对比表待审稿

**作者：Codex；请求：Zhenyu 已删减流程图文字并指定最终 PDF，要求先同步 Overleaf
更新到本地、处理可能的冲突，再插入 Chapter 4.1；随后整理 RD/FV 对比表，审核后才入正文。**

### 55.1 同步与内容保留

实际 thesis 仓库为 `/Users/zhenyuwu/Desktop/MyThesis/Zhenyu-PhDThesis`。
该仓库的 `SKILL.md` 记录 Overleaf → GitHub → 本地的同步流程，当前只有 GitHub
`origin`。执行 fetch 后，`main` 从 `0a279019aa6a3619c08a9118ef586ff09e698bd4`
快进到 `162f9fcc56e38f74ef38da66f7b64e7a63d11b0c`（`start writing chapter 4`）。
远端只新增章首介绍；原本未提交的 Gauss physical-flux 小节等共141行，在备份、
临时 stash 和恢复后逐字核对保留。没有合并冲突，也没有改写用户的远端介绍。

档案：工作区 `local_runs/thesis_flowchart_20260915_v1/`，含同步前全文与补丁、
同步后正文、单独插图补丁、最终 thesis 补丁和 `manifest.json`。本次未 commit 或 push。

### 55.2 插图与排版验证

使用用户指定的原始 PDF：
`/Users/zhenyuwu/Desktop/MyThesis/useful_resources/Arepo_document/Arepo_flowchart_main_loop_RD_FV_functions.pdf`。
原样复制到 thesis 的
`zhenyu_thesis/chapter4/figures/Arepo_flowchart_main_loop_RD_FV_functions.pdf`；
两份 SHA256 均为 `ed179859cb1b985b6edba7345814798025c716c485ad396c66c2e509c3bf9d1d`。
没有重新导出或修改 draw.io，用户删去的文字保持删除。

`chapter4/chapter4.tex` 的 4.1 中加入正文引用和图注，说明第7/12框为 RD/FV 入口；
stage 表示主循环入口，内部算法依配置而定。采用正文宽度并在4.2前清空浮动体，
图号为 **Figure 4.1，论文第140页**；4.2从第141页开始。
最终正文减去本次插图内容后，与同步后的原文完全一致，4.1之外没有内容改写。

用 XeLaTeX/latexmk 完整编译232页 thesis，exit0，全部引用和文献引用已解析。
第一次独立 outdir 构建遇到 BibTeX 路径问题；改用隔离的源文件副本和原图链接后成功，
没有为构建修改论文的 bibliography、preamble 或旧生成文件。
逐页查看138–141页：图、图注及4.2分界正常，无裁切；原图按正文宽度缩小后函数名较小，
矢量内容放大可读，此实际排版特点已告知用户。
现存4.2之后一处2.8231pt overfull 和全书其他既有版式警告不属于此次插图修改。

完整编译结果在上述档案的 `compile_project/master.pdf`；
便于审核的三页摘录为 `chapter4_1_flowchart_review.pdf`（论文138–140页）。

### 55.3 RD/FV 表格草稿与范围

新报告：[RD_FV_CHAPTER4_1_COMPARISON_DRAFT_20260915.md](RD_FV_CHAPTER4_1_COMPARISON_DRAFT_20260915.md)，
包含符号定义、中文审核表、英文候选表及定稿限定；**未插入 thesis**。
以8月1日 [旧报告](AREPO_FV_RD_comparison.md) 的表为基础，对照当前 FV/RD 源码和后续审查。
表包括自由度/权重、局部对象、空间表示、迎风、空间守恒、时间入口、层级时间步、
冻结状态、MPI责任和 moving geometry。

修正旧表容易造成误解的表述：当前 FV 有两个半权重 flux calls；不把两阶段标题
自动写成严格时间二阶。timebin 始终属于节点，三角形最细bin只是派生的计算频率；
frozen 节点接收积分量增量，不因此自动成为stage-live。区分 Gauss `P1(U)` 和旧 Roe
`P1(Z)`，以及空间守恒恒等式和完整 moving 更新守恒。当前 moving C 仍为 begin
记录区间、end 在单次正常重建网格上做两个扫描；独立 old/new 两阶段候选没有移植。

未修改 solver 或 Config，没有新增流体测试或继续 moving 数值研究。
solver SHA256 仍为 `1ca5e428a0578752a18fc7af6b34e0341dbb3b6ce1d1d7d5a10d27dbe9e13636`。


## 56. 2026-09-15：RD/FV 表改为英文数值性质对比

**作者：Codex；用户修正：去掉局部对象、时间推进、hierarchy、MPI、moving mesh 和
inactive nodes，按性质比较；二阶精度对应 FV spatial reconstruction 与 RD P1+LDA，
positivity 对应 slope limiter 与 N scheme。**

重写 [表格草稿](RD_FV_CHAPTER4_1_COMPARISON_DRAFT_20260915.md)，保留六行：
solution representation、conservation、upwinding、second-order spatial accuracy、
positivity / oscillation control、accuracy–robustness balance。
最后一行对比 nonlinear slope limiting 与 N–LDA blending（B scheme）。
第一行可在正文已解释自由度后省略。所有表格内容及图注、脚注均用英文。

核对 Chapter 3、8月1日旧表，以及 Springel (2010) §3.1、Morton et al. (2023) §2.2.3。
精度行明确为光滑流的空间二阶；positivity 脚注说明稳定化机制与 Euler 密度/压力的
无条件正性不同，N 的标量正性需满足 CFL。没有把 face-normal Riemann solve 直接
等同于整个 FV 方法按维度分裂，也不把每一种 B blending 写成已保证二阶且正性。
这些是论文表述核对，没有新的数值试验结论。

前一版全文保存在工作区
`local_runs/rd_fv_property_table_20260915_v1/previous_comparison_draft.md`，
新旧文件哈希与当前源代码标识在同目录记录。没有修改 thesis、流程图、solver 或 Config；
新表仍待用户审核，不插入4.1，不commit/push。


## 57. 2026-09-15：对比表入4.1，并按 implementation / efficiency 组织

**作者：Codex；用户批准：在英文性质表中增加 Voronoi cells / Delaunay triangulation
作为计算单元的对比，然后放入4.1；建议4.1.1为 Implementation of RD in AREPO，
4.1.2为 Increasing computational efficiency，下分 hierarchical timestep 与 MPI。**

本地 thesis 的4.1改为 **Overview of AREPO-RD**，保留原4.1标签；新增：

- **4.1.1 Implementation of RD in AREPO**：AREPO几何介绍、RD接入说明、英文对比表与原流程图。
- **4.1.2 Increasing computational efficiency**：Hierarchical timesteps 与 MPI parallelisation
  两个子标题，写入简短原理概述。强调bin属于节点、三角形取最细频率，以及残差责任唯一性。

表格为 **Table 4.1，论文第139页**，七行；新增行写为
`Computational elements | Voronoi cells | Delaunay triangles`。
正文另说明前者为控制体，后者为残差组装单元，RD自由度仍在顶点。
精度行、positivity脚注和B方案的性质对比按§56审核意见保留；表格使用正文宽度、
11pt级字号与booktabs。原流程图仍为 **Figure 4.1，第140页**，PDF逐字节未变。

4.1.2从第141页开始，4.2从第143页开始。效率部分仅为概述，没有新增加速比、MPI扩展
结果或流体测试。当前F1的hierarchy/equal区别作简短提示，并引用既有4.3.3的moving
几何讨论。原章首用户介绍及4.2之后全部正文保持不变；只对4.1的一句几何介绍作等义
精简以消除单词孤行，并保持MPI性能讨论段落在同一页。

完整XeLaTeX/latexmk编译235页，exit0，引用及文献引用全部解析、无重复label。
初次编译发现新增4.1.1标签与既有4.3标签重名；已将新标签改为
`section:AREPO_RD_implementation_overview`，既有4.3引用不变。
4.1无overfull/underfull；4.2之后原有2.8231pt超宽警告未改。

本轮档案在工作区 `local_runs/thesis_section41_table_20260915_v1/`，包括旧正文和对比表、
本次插入片段、隔离构建、最终正文差异及哈希；五页审核PDF为 `chapter4_1_review.pdf`
（论文138–142页）。表格记录文件
[RD_FV_CHAPTER4_1_COMPARISON_DRAFT_20260915.md](RD_FV_CHAPTER4_1_COMPARISON_DRAFT_20260915.md)
已更新为“approved and inserted”。没有再次pull、commit或push，尚未同步回Overleaf。
未修改solver、Config、Chapters1–3或其他论文源文件；无需流体回归。


## 58. 2026-09-15：流程图重排为横向整页，字号约放大两倍

**作者：Codex；请求：Zhenyu 希望流程图更大，允许在 draw.io 中调整方框位置，或在
thesis 中横向放置。** 从用户最终 PDF 内嵌的原生 draw.io XML 建立新副本，保留全部
14个编号方框、函数名和15条连接关系，以及用户已删除的说明文字。所有旧 PDF/draw.io
保持原样；原始 PDF SHA256 仍为 `ed179859cb1b985b6edba7345814798025c716c485ad396c66c2e509c3bf9d1d`。

新布局保持三列阅读顺序，将各列行位置对齐、压缩空白及方框高度，并把14→1的返回线
移至方框上方。白底与分类配色保留，多数方框文字改深色以提高对比度；重新安排换行，
说明文字18px、函数名14px。原生 draw.io 导出为可缩放的矢量 PDF，同时保留可编辑图。

新文件：`dev_log/figures/Arepo_flowchart_main_loop_RD_FV_functions_landscape_20260915.drawio`
及同名 PDF，两份均已复制到 thesis 的 `useful_resources/Arepo_document/`。
thesis `chapter4/figures/` 中另放同名 PDF，正文引用此新文件。重排脚本为
`dev_log/figures/build_arepo_main_loop_landscape_drawio.py`，输入用户 PDF 提取的 XML；
它检查全部标签、编号、连接端点和归属关系，并拒绝覆盖现有输出。

论文使用 `pdflscape` 的 landscape 环境，PDF 阅读器会直接显示横向页。
`master.tex` 只增加该宏包；Chapter4 只改插图尺寸/环境并将原说明段移到图后，
避免一个只有说明段的额外竖向页。正文、表格、图注内容均未改写。
**Figure4.1 仍在第140页；4.1.2仍从第141页开始，4.2仍从第143页开始，全书235页。**
按编译后 PDF 的实际字体统计，函数名从约3.38pt增至6.80pt，普通说明从3.95pt增至8.75pt。

完整 XeLaTeX/latexmk 编译 exit0，引用全部解析，无新增重复label或超高浮动体。
逐页查看138–143页，方框、长函数名、箭头与图注无裁切或重叠；后续4.2保留原版式及
既有警告。新旧正文去除本次排版变化并复位说明段后相同，4.2及以后逐字节未变。

本轮档案：工作区 `local_runs/thesis_flowchart_landscape_20260915_v1/`，包括原文备份、
PDF提取的用户图、布局迭代、隔离编译、最终六页 `chapter4_1_landscape_review.pdf`、
局部补丁和文件哈希。第一轮横向排版多出说明段单页，第二轮已消除；最终235页。
更改仅在本地，未pull/commit/push；未改solver、Config或Chapters1–3。


## 59. 2026-09-15：4-rank真实glass三角形分工图与原生MPI核对

**作者：Codex；请求：Zhenyu将在Overleaf继续写4.1，要求用真实glass IC和4个MPI
ranks导出triangulation并按计算责任着色；若Python重建需核对实际节点归属，并可举
跨rank边界例子。** 报告：[RD_MPI_GLASS_OWNERSHIP_20260915.md](RD_MPI_GLASS_OWNERSHIP_20260915.md)。

使用已归档SWIFT glass48的全部2304个节点（源SHA256为157e1a47…d88f），
Yee流体状态、box10、gamma1.4、静态完整局部网格、Gauss3 LDA/F1及split equal-step。
两个时间步0.001953125到0.00390625，4-rank导出、同binary关闭导出对照、1-rank导出
三次native运行均完成。两个线程环境变量均设为1。

在隔离冻结的源码副本中添加只读输出，直接抓取P的primary节点、RD选中的DT/DP
三角形、实际残差循环的顶点贡献、FluxRD发送缓存和MPI接收缓存。工作solver及默认
Config未改；原solver SHA256仍为1ca5e428…13636。原生图形不依赖后处理重建。

核对结果：4608个唯一物理三角形、6912条周期边，面积和99.99999999999994。
SciPy的3×3周期Delaunay重建与native逐一相同（键含ID和相对周期像偏移），1/4rank
native拓扑也相同；顶点ID、primary rank、远端目标本地索引和坐标全部一致。
两个捕获stage分别实际执行4608次三角形计算；各649条远端顶点贡献，预测路由、实际
发送和接收记录的四分量值逐条精确匹配。开关导出的端点状态逐位相同，1/4rank最大
状态差2.665e-15。完整周期坐标匹配确认真实源glass，未用jitter或抽稀代替。

每rank576个primary节点；rank0/1/2/3分别负责1210/1144/1155/1099个三角形。
当前full-mesh规则取所有顶点的最小(ID,task)，且只由最小ID节点的primary实例claim；
不是按多数顶点投票。图中A的顶点为1142(rank1)、1146(rank2)、1147(rank2)，
由rank1计算并给rank2发两条贡献；相邻B为1142(rank1)、1146(rank2)、1150(rank3)，
也由rank1计算，远端贡献分别发给rank2和rank3。均取自实际网格和通信记录。

英文图为`dev_log/figures/rd_mpi_glass_rank4_overview_20260915`和
`rd_mpi_glass_rank4_boundary_20260915`（PDF/SVG/PNG）。总览并排区分节点owner与
三角形owner，边界图标出ID和rank。逐张渲染最终PDF检查；初版总览标题/图例重叠已
修正，旧预览仅留档。资源副本、报告、native节点/三角形CSV及audit.json放在thesis
`useful_resources/Arepo_document/RD_MPI_glass_rank4_20260915/`，没有改4.1正文。

完整档案：工作区`local_runs/mpi_glass_ownership_20260915_v1/`；四个复现文件在
`tests/rd/capture_mpi_mesh.py`、`mpi_mesh_capture.h`、`analyse_mpi_mesh.py`、
`plot_mpi_mesh.py`。实际binary SHA256为37e1bb25…53c86；配置、生成header、冻结源、
链接库、参数和运行日志均保存。没有MPI速度测量；不外推至active-only重建、moving
mesh/migration或大规模MPI。未pull/commit/push；用户的Overleaf文本由用户继续完善。


## 60. 2026-09-15：补齐4.1比较正文，拆分状态存储、控制体和残差计算对象

**作者：Codex；请求：Zhenyu已写好4.1 comparison部分草稿，要求补充完整，并将
computational element拆分为fluid-state storage、control volume和flux/residual
computational element，允许优化英文表达。** 当前论文HEAD为b013be7（用户的
comparison草稿），前一提交6777107替换流程图；cached origin/main同为b013be7。
本轮没有pull；直接以含用户所述占位段落的当前本地草稿为编辑依据。

仅替换4.1.1从“In fact, many concepts...”开始到comparison表结束的文本。
补齐共享节点存储、FV cell average与RD nodal state、median dual的P1行和集中权重、
face flux与triangle residual、局部守恒、多维迎风、reconstruction/LDA及limiter/N
的作用和B blending段落。符号沿用Chapter3，并在使用前定义T、phi^T、phi_i^T和S_i。
“perfect B scheme”改为在不同流动中平衡精度与稳健性仍需完善；不新增无条件Euler
正性或当前完整算法时间二阶的宣称。引用现有Springel2010、Pakmor2016、Morton2023
和Deconinck2017条目，在线核对前两篇论文的重构/梯度相关段落，未修改bib。

表格由7行改为9行，Fluid-state storage将FV/RD两列合并：同一mesh-generating
point即Delaunay **vertex** / Voronoi **generator**，使用P[i]和SphP[i]。明确generator
通常不等于Voronoi centroid；质量在P[i].Mass，动量、能量和primitive在SphP[i]。
Control volume为Voronoi cell / median dual cell；Flux / residual evaluation为
Voronoi face flux exchange / Delaunay triangle residual distributed to vertices。
其余solution representation、conservation、upwinding、spatial accuracy、positivity
及B scheme比较保留。代码核对DualArea=sum(|T|/3)和Q/area恢复nodal state。

原稿、完整tracked-file hash清单及旧comparison报告先备份到工作区
`local_runs/thesis_comparison_completion_20260915_v1/`。在隔离source mirror中完成
XeLaTeX/latexmk全书编译，exit0、237页；所有引用解析，无comparison新增overfull。
Table4.1在141页，原横向Figure4.1在142页，4.1.2从143页开始。最终六页review覆盖
138–143，全部渲染目检，表格完整单页、字号可读、无裁切或重叠。

通过源文件hash guard后写入本地chapter4/chapter4.tex；其SHA256为
22017625810fdebc54ff598e193be81e55c7c191779a05e556eeb5dd1f6c8819。
124个tracked thesis文件中只改此文件；它在comparison之前及表格之后的内容逐字节
保持原样，用户AREPO introduction中的项目列表占位符仍留给用户继续写作。
没有改流程图、master、Chapters1–3、solver或Config；未pull/commit/push。
工作solver SHA256仍为1ca5e428…13636。本地变更等待用户正常同步至Overleaf。

报告更新：[RD_FV_CHAPTER4_1_COMPARISON_DRAFT_20260915.md](RD_FV_CHAPTER4_1_COMPARISON_DRAFT_20260915.md)。
最终review：档案内`output/pdf/chapter4_comparison_review.pdf`；完整build、原文备份、
proposed_chapter4.tex、thesis_change.patch、前后hash清单及PNG QA均保存。


## 61. 2026-09-15：MPI glass图精简并插入4.1.2

**作者：Codex；请求：Zhenyu要求去掉总览的主标题和最底部2304 nodes统计行；
detail去掉标题、副标题、整个(b)和底部文字，只保留rank0–3颜色legend，然后将
两图放入4.1.2。** 核对原图后，(b)是右侧Responsibility and routing说明栏，
不是网格中的大写B三角形；已向用户说明这一解释。两个真实A/B三角形与节点ID/rank
标注保留，右侧说明及所有footer文字删除，规则移至正文/图注。

绘图脚本tests/rd/plot_mpi_mesh.py新增--thesis和--output-dir选项，原默认输出保留。
新图名rd_mpi_glass_rank4_overview_thesis_20260915及boundary同格式，PDF/SVG/PNG
放在dev_log/figures与thesis资源目录RD_MPI_glass_rank4_20260915。两张PDF另复制到
chapter4/figures。修改只涉及标题、文字栏、画布及间距；原配色、坐标、原生triangles、
节点归属和通信数据不变，原图另存保留。本轮没有新跑MPI，也没有改solver或Config。

当前论文仍以b013be7为HEAD，保留§60的未提交comparison修改；本轮先备份该当前稿，
只新增MPI说明和两张图/图注。总览用横向页：Figure4.2，第145页；detail用竖向页：
Figure4.3，第146页。正文解释full-local-mesh配置的最小ParticleID owner、primary
实例去重，以及A向rank2、B向rank2/3发送贡献的实际例子。没有新增速度测量宣称。
此前全部thesis文字逐字节保留；去掉两块新增内容可以精确恢复本轮输入。

隔离XeLaTeX/latexmk全书编译exit0、239页；引用解析，无新增overfull或超高float。
最终两张独立PDF及143–146四页thesis review均渲染目检，图注、节点标注和legend
无裁切重叠。PDF文本检查确认指定标题、(b)栏和底部说明已删，四个rank及四个ID仍在。
写回前核对全部124个tracked thesis文件未被其他操作修改；写回后仅chapter4.tex变化，
另新增两张PDF。Chapter4最终SHA256为3130b55de1d05c3efe7a29392aa78d55ea60b8fd8c1135e49ee48b4f527c20bd。
11个受保护原图、native数据及solver文件hash保持不变，14份新asset复制hash全部相符。

档案：工作区local_runs/thesis_mpi_figures_20260915_v1，包含原文/脚本备份、两块新增
TeX、source mirror、精确patch、前后manifest、生成图和PNG QA。最终审阅文件为
output/pdf/chapter4_1_2_mpi_review.pdf。报告追加于RD_MPI_GLASS_OWNERSHIP_20260915.md。
本地thesis和资源已写入；未pull/commit/push，等待用户正常同步到Overleaf。


## 62. 2026-09-15：以5节点、3三角形重画AREPO式hierarchical timestep示意图

**作者：Codex；请求：Zhenyu希望把以前的hierarchical timestep示意图改成类似
AREPO的形式，以Delaunay triangulation替代Voronoi cell，并减少element数量。**
核对Springel2010 Figure17：其结构是连续时间的clock+mesh小图。参考本地published
PDF第30页（印刷p.820；arXiv物理第33页），也读取了论文7.2。旧图为资源目录及
chapter4/figures中的delaunay-rd-moving-mesh-timeline.png，含moving翻边及时间轴；
旧log1/PhaseB报告10.1另有JKL/KML的4:1 frozen-stage文字时间轴。旧图和文本均保留。

新图采用白底、2×2四个时刻0、dt、2dt、3dt；只有5节点和3个相邻三角形。
J/K/L节点dt_i=4dt，M=2dt，N=dt。由三顶点最小bin得到T1(JKL)=4dt、T2(KLM)=2dt、
T3(LMN)=dt。各面板开启的triangle intervals为{1,2,3}、{3}、{2,3}、{3}；4dt共同
同步并重复。时间轴和节点同色表示nodal timestep；实心/空心表示timebin同步与否；
着色三角形表示当前开启子步；箭头表示给三个顶点分配贡献，包含未同步的粗步节点。

**没有把timebin同步画成RK-stage-live。** 当前source的star判据对这个孤立示意网格
只使J和N stage-live；K/L/M受到更细incident triangle影响。特别是面板(c)的M虽然
是timebin同步实心节点，但不能据此推断它执行独立predictor。图注/README明确这一区别，
两个hydro stages没有逐一画出，图中也不表示具体贡献的时间权重、大小或流动方向。
本图仅展示固定位置、固定bin的静网格调度，不扩展到moving flip或bin迁移。

绘图脚本dev_log/figures/build_rd_hierarchical_timestep_schematic.py使用明确五点坐标；
SciPy Delaunay集合恰好等于所画三角形，程序检查min-node timebin、所有due集合、
4dt重复和各顶点收取贡献的路径。一个4dt周期内共7个triangle intervals，而全部用
最小步是12个；这是示意算例计数，不是native速度结果。没有运行新的hydro实验。

最终PDF/SVG/PNG为dev_log/figures/rd_hierarchical_timestep_schematic_20260915，
PDF已渲染目检，箭头、节点标签、时间轴及legend无裁切或重叠；首版预览留档。英文
caption先定义dt_i、dt_T与最小dt，引用已有Springel_Pur_2010。工作区档案为
local_runs/hierarchical_timestep_schematic_20260915_v1，含caption.tex、README、
schematic_schedule.json、最终output/pdf、绘图结果和保护文件hash。

7份新资源（PDF/SVG/PNG、schedule JSON、caption、README、builder）放入thesis
useful_resources/Arepo_document/RD_hierarchical_timestep_20260915。用户请求的是
示意图修改，因此未替换原moving图或插入Chapter4；新图供本轮审阅。原图两份、当前
chapter4.tex及solver的hash保持不变。未改Config、未commit/push。


## 63. 2026-09-16：hierarchy示意图改用A–E，节点颜色始终表示自身timebin

**作者：Codex；请求：Zhenyu要求从ABCD开始标字母，强调timebin先赋给节点，
triangle只取三顶点的最小值，并让每个节点始终使用对应timebin的颜色，以显示
frozen节点也能被动接收update。** 在§62图的独立新版中将J/K/L/M/N改为A/B/C/D/E。
A/B/C为蓝色4dt、D为青绿色2dt、E为橙色dt；不再用空心表示未同步节点。
颜色始终保留，timebin同步另用外圈标记，clock对应事件也采用相同外圈。
底部明确写出derived triangle timestep：dt_T=min_{i in T}dt_i。

三个三角形仍为T1(ABC)=4dt、T2(BCD)=2dt、T3(CDE)=dt，几何和调度未变。
例如t=dt面板仅E带同步外圈，C/D仍保持蓝/青绿色，而T3的三个箭头分别指向C/D/E，
显示粗步节点仍接受分配贡献。外圈只说明自身timebin是否同步，不代表RK stage-live。
当前孤立三角网格的whole-star判据给出A/E stage-live、B/C/D frozen；D在t=2dt
有外圈但仍为stage-frozen。英文caption和README明确此区别，不把被动收取贡献解释
为更新自身predictor；图仍省略两个RK stages和具体ledger deposit时刻。

新文件：dev_log/figures/rd_hierarchical_timestep_schematic_20260916.{pdf,svg,png}。
更新同目录builder，旧builder备份在工作区档案
local_runs/hierarchical_timestep_schematic_20260916_v1/original_builder.py。
档案另含最终PDF、PDF渲染预览、caption、README、schedule和hash清单；7份资源
另存至useful_resources/Arepo_document/RD_hierarchical_timestep_20260916。

程序重新核对Delaunay连接、nodal minimum、各时刻due集合、共同同步和贡献接收节点，
并与§62数据确认几何及调度相同。最终单页PDF渲染目检通过，A–E、持续节点颜色、
同步外圈、箭头和图例无裁切重叠。14个受保护文件hash不变，包括旧版图和资源、原
moving图、chapter4.tex与solver。本轮只改图及说明，未插入论文、未运行hydro实验，
未改Config、未commit/push。


## 64. 2026-09-16：同步GitHub的4.1.1新稿、核对原始引用并推送MPI图

**作者：Codex；请求：Zhenyu已从Overleaf推送新稿，要求comparison正文以GitHub为准，
少量补充Auriga/THESAN及AREPO limiter等原始论文引用，解释B scheme与nonlinear
slope limiting的类比，保留英式英语的-ization拼写，再推送本地4.1.2图片。**
实际本地HEAD为66d08ae，未提交内容仅为§61的50行MPI说明/图注和两张PDF。
先备份，再fetch得到5a35005；远端改动在comparison区域，本地MPI patch可干净应用，
没有重叠文本冲突。以远端全文为底稿，保留其表格位置、9行内容及精简文字；没有恢复
§60的长篇旧稿。表格逐字节不变，4.2及以后正文也逐字节不变。

在项目介绍加入Pillepich2018、Grand2017、Kannan2022；技术段加入已有van1984relation
和Toro2009，保留Pakmor2016。按Springel2010 §3.1、Eq45–47补充Barth & Jespersen1989，
核对本地原论文封面及NASA记录，正确姓氏为Jespersen，AREPO原文写作Jesperson。
另增Dobeš & Deconinck2008作为N/LDA blending的原始文献，保留review和Morton引用。
明确类比只涉及调节耗散以兼顾精度和振荡控制：limiter改变重构梯度，B改变分配残差；
不推出update等价或同样的正性保证。删除已核对的红字问题。小幅修正P1基函数定义在
Delaunay triangles、median dual提供nodal control area，避免把两者混同；将绝对的
“unique feature”改成element-level multidimensional upwinding的distinguishing feature。
没有把用户的discretization、summarized、stabilizing等改成s拼写。

共享bibliography虽存放于chapter1目录，但本轮只核正所请求两条项目引用的author字段：
Kannan名字为Rahul，THESAN完整7人无需others；Auriga的Campbell为David J. R.，
无Guedes。Chapters1–3正文未改；两个新方法条目写入chapter4bib.bib。
§61两张native MPI PDF及全部50行本地说明合入4.1.2，图文件hash与原图一致。
§63的独立hierarchy示意图此前尚未插入4.1.2，本轮也未擅自增加该插图。

隔离XeLaTeX/latexmk最终全书编译exit0、238页，无未解析引用。Table4.1在印刷139页，
comparison在139–140页；flowchart141页，MPI两图144–145页。最终138–145八页review
全部渲染目检，相关bibliography四页也目检。压缩新增解释以消除flowchart前单独一行
占页的情况。最初输出目录缺少include aux子目录，另一次只转换不完整XDV；均保留
并不作为验证，最终使用预建所有include目录的新build_final完整编译。

确认本地文件未被并发修改后，保留原MPI变更stash 44b646cf，再fast-forward到5a35005，
写入已验证稿。仅5个目标文件提交为e26d5ab429e5f31355d39cf7fd9ebfd9bb63e2d0，
已push origin/main，并以ls-remote独立确认远端同一hash。无force push；既有未跟踪
编辑器/build文件保持原样，无tracked或staged变更遗留。GitHub直连超时，通过用户
已经启用的系统代理127.0.0.1:7897和单次git -c http.proxy解决，未改全局配置。

档案：local_runs/thesis_sync_citations_20260916_v1，含前后源码、patch、编译与QA、
README引用核对记录、delivery.json和原本地stash标识。审阅PDF为
output/pdf/chapter4_1_synced_review.pdf。只完成GitHub同步，未操作Overleaf网页；
用户可以按正常流程从GitHub拉入Overleaf。AREPO solver/Config及数值数据均未改。

## 65. 2026-09-16：comparison表的limiting、振荡控制与Euler物理正性辨析

**作者：Codex；请求：Zhenyu询问nonlinear slope limiting与AREPO limiter的区别、
accuracy--robustness行是否重复、星号脚注是否必要，以及标量正性证明与Euler的关系。**
本轮为文献与源码核对，没有修改thesis、solver或Config，没有新增数值实验。

Springel2010 §3.1 Eq45--47中limited gradient=alpha_i*gradient，alpha由局部解的
极值和外推差确定，因此AREPO的limiting本身就是nonlinear；这不是另一种额外方法，
也不表示空间多项式高于一次。原论文明确该limiter并不严格TVD，允许小幅post-shock
oscillations。建议保留三行时把最后一行FV写成Slope-limited linear reconstruction，
RD写成Nonlinear blending of N and LDA residuals，明确它是精度与振荡控制的组合。
建议将Positivity / oscillation control改为Oscillation control near discontinuities，
相应去掉泛化的星号脚注；这些仅为建议，尚未写入论文。

区分scalar maximum principle、系统系数/特征意义的positivity与Euler物理正性。
Chapter3的标量凸组合证明不自动证明Euler更新后rho>0、p>0；E在本论文是总能量密度，
p=(gamma-1)*(E-rho*|v|^2/2)，动量本身可为负。不同守恒分量分别满足界限也不足以
保证内能为正。系统matrix N文献存在特征/CFL和稳定性分析，不能反过来断言一切
N-scheme理论都仅限scalar；但未据此建立当前F1/RK2/hierarchy完整更新的物理正性。
N/LDA的普通B blending也不能仅凭混合形式推出该结论。

FV并非只有标量正性证明：Einfeldt et al.1991研究完整Euler的Godunov与HLLE（后者
要求适当波速），高阶推广还需匹配的重构、通量、CFL及时间推进。Zhang/Xia/Shu的
三角网格论文明确区分标量maximum principle与Euler正密度/压力，并给出相关高阶构造。
本地finite_volume_solver.c:1323 face_add_extrapolations会拒绝导致负rho/p的外推；
:1649 face_limit_fluxes限制donor质量流出并同比缩放通量。因此实际AREPO稳健性不能
全部归因于slope limiter。RD的rd_rk2_prepare_corrector在非物理predictor时终止，
该检查不是positivity-preserving limiter。既有baseline中已保存rho/p为正的结果是
有限测试证据，不是定理；Sod的负vx欠冲也不能解释成负压力。

核对来源：
- https://arxiv.org/html/0901.4107v3 （§3.1、§8.2）
- https://doi.org/10.1016/0021-9991(91)90211-3
- https://www.math.purdue.edu/~zhan1966/research/paper/triangle.pdf
- https://www.math.u-bordeaux.fr/~rabgrall/mes_papiers/caf_2006_35.pdf （§2.6）
- https://www.math.u-bordeaux.fr/~mricchiu/dc-mario.pdf （matrix N/B及CFL讨论）

## 66. 2026-09-16：保留4.1.1定稿、补全F1代码说明，添加4.2/4.3审阅草稿

**作者：Codex；请求：Zhenyu要求维持4.1.1现稿，只改必要语法、核对并补全红字和
函数名下划线；在4.2加入hierarchy图及守恒/KH说明，在4.3写MPI草稿，科学问题另报。**
开始时本地thesis已为fdb3db590da4d98d07c27d70288ab5064ae70bdc；只读ls-remote确认
GitHub相同，没有pull/push。本轮仅对本地thesis写入四个文件，保留用户审核状态。

4.1.1 comparison表及其科学说明逐字节未变。只修正三个小语法问题和红字段落附近的
calculation/distribution表达；rd_step_begin()/rd_step_end()改为verbatim等宽格式。
红字替换为当前源码的实际行为：static predictor使用Chapter3 lumped update，corrector
使用预测态重算K/分配算子，F1通过第三个RHS求解应用；旧/新空间残差保留各自stage，
rank-deficient inflow matrix的时间项回退lumped。删去未经限定的“两个时刻beta差不多”
和省略号，明确static split-stage配置条件，没有把equal ALE也说成同一阶段安排。

**两项原文科学问题单独报告、未擅自改写：**(1)FV正文把Pakmor Eq14的formal Heun
predictor当作Block7真实Q写入；代码每次flux乘0.5，Pakmor实际采用Eq19--21的primitive
Taylor predictor，论文明确称其RK/MUSCL-Hancock hybrid。(2)该段U称primitive，但
Chapter3 U为conserved density；新RD段重新定义U，原FV符号暂保留供用户决定。
详细核对、源码锚点和建议在档案SCIENCE_REVIEW.md。

按请求将hierarchy和MPI提升为4.2/4.3两个section，后续ALE/DF仅自动编号顺延，源文
逐字节不变。4.2加入§63的A--E节点色图，说明nodal bins、triangle minimum、完整star
判据、frozen state与被动接收conserved increments的区别。守恒解释包含共享边时间
覆盖与F1-minus-lumped零和，明确检查所有相关区间闭合后的共同同步时刻；没有声称
单个triangle residual为零，或每次中间ledger deposit都保持全局物理总量不变。
另保留F1 hierarchy并非equal-at-finest的单纯调度优化、两阶段不推出时间二阶的限制。

引用核对：Morton2023 §4/Fig6是DRIFT；JUMP在Morton博士论文§4.2.2--4.2.3。
新增Morton_Thesis_2021条目于chapter4bib，year2021据Edinburgh repository正式日期
2021-07-31（PDF封面2020）；author按institutional metadata，doi10.7488/era/1086。
未改Chapter1--3源文或其bib。

新KH守恒图使用既有943f7ae原生存档，不是新模拟：static smooth KH、真实glass2304、
unit box、gamma1.4、rho=1+band、vx=-.5+band、vy=.1sin(4pi*x)、p2.5，tanh width.025，
LDA/F1、Gauss3、CFL.3。4 ranks equal实际dt1/1024，hierarchy1/1024和1/512；11个
snapshot到code time2，hierarchy所有非初始输出均有bins18/19且时间是1/512整数倍。
用double HDF5的Masses/InternalEnergy/Velocities重构每节点总能量，以补偿求和累加
相对初态的逐节点差值。没有使用六位打印的energy.txt，也没有误用Voronoi Volume。
4-rank max|deltaE/E0|：equal7.44e-17，hierarchy9.39e-17；1-rank对照1.23e-16/6.23e-17。
这些是round-off量级的输出重构诊断，不能用于精度排序。先汇总舍入后的总E再相减
可得略不同的浮点结果，均保留CSV；这解释与§41直接numpy求和的末位差异。
图和正文写of order1e-16，不声称精确零、不比较Morton不同resolution/bins的数值大小，
不由这组DEBUG单次walltime推speedup。

4.3补全node/triangle ownership、primary/periodic copy、active-only条件变体、状态
交换与FluxRD增量回传、完整star的MPI归并，以及2304nodes/4608triangles的已核对
分工和边界A/B例子。两张已批准native MPI PDF及原caption均保留。

隔离全书XeLaTeX/latexmk编译exit0、244页、无未解析引用，新增4.1--4.3区域无overfull。
印刷138--151的14页审阅稿逐页视觉核对；最后文字修改后重渲染，未变页面像素hash
一致，变化的143/147--149页重新目检，函数名下划线、图和caption均完整。
安装前核对全部126个tracked文件hash和HEAD未被并发修改；只安装chapter4.tex、
chapter4bib.bib及两张新PDF，所有其它tracked文件hash不变。未commit/push、未改
AREPO solver/Config、未运行新hydro测试。一次编辑脚本相对路径错误后以绝对路径
重跑并完整重编译；最终compile_final.json为接受结果。

档案：`../local_runs/chapter4_sections_draft_20260916_v1/`，含原稿/hash、隔离源码、
edit/install脚本、SCIENCE_REVIEW.md、逐snapshot数据/hash/provenance、KH绘图脚本、
编译/QA及delivery.json。交付审阅PDF：`output/pdf/chapter4_1_to_4_3_review.pdf`；
独立图：`output/pdf/rd_kh_energy_conservation_20260916.pdf`。本地thesis新增图名同档案；
现有workflow需要用户审核后再同步GitHub/Overleaf。

## 67. 2026-09-17：复核 FV 第一入口的 Q 写入和 Chapter 3 的 U 定义

**作者：Codex；请求：Zhenyu追问Block 7是否确实由Q接收第一阶段更新，
第二入口是否外推W'后计算通量，以及Chapter 3哪里将U定义为conserved。**
本轮只读核查源码、thesis和Pakmor2016 §3，未改solver或thesis，未commit/push。

用户对Q实际接收第一阶段贡献的记忆正确。§66的“formal Heun predictor不等于
Block 7实际更新”应明确限定为权重和预测态构造方式，不能解释成Q没有更新。
`src/main/run.c:262,368`两次调用同一FV函数；
`src/hydro/finite_volume_solver.c:1092`取完整face timestep，`:454`乘0.5，
`:500--503,565`直接累加Mass/Momentum/Energy。因此无源项、equal timestep时，
第一入口写入 Q_after7 = Q_n - dt/2 sum(A_n F_n)，不是formal Heun的
Q' = Q_n - dt sum(A_n F_n)。Q_after7只是部分累加结果，不应解释为物理半时刻状态。
第二入口添加新端点通量的另一半贡献，原文最终端点平均公式可保留。

`:834--846,863,914`读取保存的primitive字段/梯度，外推间隔为
All.Time - TimeLastPrimUpdate；`:1172`局部变量虽名dt_half，实际取dtExtrapolation。
`:288--295`先作时间/空间外推再组装Riemann states。equal timestep同步节点在第一
入口的时间外推为零，第二入口为完整dt，构造W'；它不是由Q_after7反算所得。
`run.c:371`在第二通量调用后才update_primitive_variables，后者`:94`刷新时间戳。
hierarchy时两次入口均可能需要对邻居从其最近primitive更新时间外推，不能普遍称
第一入口绝无外推。Pakmor2016 Eq19--21及其后说明与此一致。
来源：https://academic.oup.com/mnras/article/455/1/1134/986779

Chapter 3当前源码`:313--314`明确写“The conserved state”以及
U=(rho,rho vx,rho vy,E)^T；`:45`说明E是total energy density，`:482--484`
再次明确conserved variables U。该处在“RD for Euler Equations”小节。
git blame显示这两行分别来自2026-07-15的67e4c9e7和2026-07-14的5a924553，
并非§66补写内容。应区分primitive W=(rho,vx,vy,p)、conserved density U与
积分守恒量Q；“未乘control volume”并不意味着primitive。本次保持原文待用户决定。

## 68. 2026-09-17：按用户确认修改 FV 累加公式并统一 W/U/Q

**作者：Codex；请求：Zhenyu同意§67核查结果，要求将两个入口写成Q +=形式，
并统一primitive W、conserved density U、integrated conserved Q。**
仅修改本地thesis的chapter4.tex中FV流程说明：Block 7和12分别写
Q += -dt/2 sum(A F)，保持向外通量为正；明确Q先为Q_n，两次累加后为Q_n+1。
定义W=(rho,vx,vy,p)、U=(rho,rho vx,rho vy,E)、FV的Q=integral_V U，
并定义面积/边长和数值通量。补充W'的Euler时间外推与空间重构，明确它不是从
部分累加的Q反算得到；Block 13才同步primitive state。公式限定equal timestep、
无源项，时间推进说明改为Heun-type flux average with a primitive-variable predictor。

本次修改区域之外的chapter4前后文逐字节不变；comparison table、RD/F1段、4.2/4.3
及后续正文均保留。写回前后对126个tracked文件核对hash，除chapter4.tex外均未变。
未改solver、Chapter1--3或bib，未commit/push。新chapter4 SHA256为
f9593ab9b5f69f36f3f8929276d7d5107e94a53a3055ce978ec071bba8eab638。

隔离全书XeLaTeX/latexmk最终编译exit0、245页、零未解析引用；审阅印刷142--143页，
两个+=式、状态定义、引用及RD段衔接目检通过。首次编译因include的输出子目录缺失
失败；补齐目录后latexmk曾只转换旧的未完成XDV，检查发现引用缺失而拒收。
随后强制latexmk -g完整编译并重新提取/渲染，最终QA对应这个完整结果。
档案：`../local_runs/chapter4_fv_notation_20260917_v1/`，含before/hash、source、
patch、prepare/install脚本、编译记录和qa/delivery.json；审阅PDF为
`output/pdf/chapter4_fv_update_review.pdf`。§66审阅稿为修改前版本，此档案接续它。

## 69. 2026-09-17：解释 N/LDA 在两个 RK 阶段的分配与时间质量

**作者：Codex；请求：Zhenyu询问beta_N和beta_LDA如何处理不同阶段，认为当前文字
不够直观。本轮核查并建议文字，未改thesis或solver。**
当前标准static `RD_RK2_TOTAL_RESIDUAL`（排除四遍rate-consistent实验）中，
两个空间分配均从本stage状态重新计算。`rd_rk2_prepare_corrector():3576`从predictor
Q恢复W*、存RD_dU=U*-U_n；`:3934--3935`随后交换W*/RD_dU。
`:4068`明确不作FV式Taylor外推。每个stage重建Roe平均、K+/K-、Sminus和inflow solve。
固定网格只固定几何，Euler状态改变仍会改变这些矩阵。

LDA的空间项等效为beta_n phi(U_n)和beta_* phi(U*)，并非一个冻结beta同时作用
两阶段残差，也不是平均beta后重新分配旧残差。`:4981--5001`用
Sminus x=phi、phi_i=-K_i+ x直接实现，不存beta或显式逆。
N没有对应的显式beta_N数组；`:4969--4973,5019--5046`求当前stage inflow state，
直接形成K_i+ (Uhat_i-Uhat_in)。因此N也在U_n/U*分别重算空间分配，但不宜仿照
LDA将Euler N全部写作一个固定矩阵beta_N乘element residual。

corrector时间项是另一层选择。令dU_j=U_j*-U_j^n：LDA/F1使用
(|T|/3) beta_i* sum_j(dU_j/dt)，只用predictor-state beta，不取beta_n或两者平均；
`:4624--4653`构造第三RHS，`:5280--5317`使用第二stage的同一K/Sminus factorization。
rank<4时只有该F1时间项回退lumped。N在`:5499--5503`直接使用
(|T|/3)dU_i/dt；不存在为N时间项选择beta_n还是beta_*的问题。
旧空间分配的影响通过predictor increment保留：`:3555--3574,3638--3643`
的局部+dU/2与`:5524--5526`的T_time+0.5 phi_i(U*)组合等效于Chapter3
带旧/新空间半和的total-residual公式，不需要存每个旧beta。

用*表示预测的末端状态，应避免把beta_*写成基于最终U_(n+1)的beta_(n+1)。
hierarchy的closing-stage仍重建矩阵，但`:4202--4218`只给stage-live节点加dU，
frozen节点保持原状态；因此beta_*可依赖同一三角形的预测态/冻结态组合。
建议正文按“旧状态空间分配→预测态重算空间分配→N lumped/LDA F1时间项”说明，
将linear solve和rank fallback等工程细节移到后面，而不称beta本身被时间积分。

## 70. 2026-09-17：用英文阶段公式替换 RD 长段，并核对文献和旧 beta 对照

**作者：Codex；请求：Zhenyu要求减少文字，用§69的数学解释改写4.1.1，查找旧的
beta时刻比较，并尽量用RD论文支撑。**
仅改chapter4.tex的RD流程说明段。新增阶段符号、predictor/corrector、N/lumped总
残差及LDA/F1三项展开，明确旧空间项beta_n、新空间项和F1时间项beta_*；用
underbrace标明各项。保留W/U/Q约定，将linear solve和rank fallback缩至脚注。
前面的FV、comparison table以及从4.2起的全部源文均逐字节保留；未改Ch1--3/bib。
三个文献条目原已在全书bib中，无须复制条目。

文献核对：Ricchiuto & Abgrall 2010 §3--4支持一致质量矩阵和explicit RK-RD框架；
Arpaia/Ricchiuto/Abgrall2015印刷508页Eq28给F1，510页§3.4.1明确N不显式构造
同类分配系数并采用lumped形式，513页Eq49--53给RK/global lumping。对这三页作
整页渲染目检。Paardekooper2017 §3.4 Eq60--65直接并列N/lumped和LDA/F1。
后者Eq63用一个共同beta乘空间残差之和，因此正文明确当前代码的分阶段写法，
没有声称它与文献共同beta形式逐项相同。未找到“改变beta取值时刻必然无明显
影响”的直接文献结论；框架引用不能替代这个比较的实验证据。

找回log1的2026-08-01 three-way stage-beta experiment（从4923行开始），及
`LDA_F1_Heun_vs_standard_LDA_RK2.md` §12.2。旧版固定Yee，nominal n64、
deterministic jitter、boost1、t1、MPI1、dt1/256--1/2048，比较mixed、coherent
beta_n、coherent beta_*。dt1/256的density L1依次6.486073e-4、6.477352e-4、
6.478240e-4，误差标量相对mixed变化约-0.134%/-0.121%；velocity误差变化约
-0.016%/-0.017%。相邻时间步解的DualArea加权Richardson时间阶均0.993--0.997。
这支持“那组Yee结果对三种约定不敏感”的回忆，但不是解场完全相等，也没有恢复
二阶时间阶。尤其三组同时改了空间项分配，并非只改F1时间项beta的独立对照。
本轮只找回已存日志及其provenance，未重新取COSMA snapshots或运行新模拟；旧测试
细节写入核查报告，没有未经审核加进4.1.1正文或推广为当前Gauss/hierarchy结果。

隔离完整编译245页、exit0、零未解析引用；印刷143--144页两个阶段及分项公式、
文献、脚注排版检查通过。写回前后核对126个tracked文件，只有chapter4.tex变化。
当前chapter4 SHA256：153382c966338a48b2c2cdfd703a043cf7985f27b477ec7f719cc48f56789c6f。
未改solver、未commit/push。档案：`../local_runs/chapter4_rd_stage_math_20260917_v1/`，
含源码/before/hash/patch、文献页和文本、SCIENCE_REVIEW.md、历史误差比较JSON、
compile_final.json、qa.json、delivery.json。审阅PDF：
`output/pdf/chapter4_rd_stage_math_review.pdf`。

## 71. 2026-09-17：Paardekooper 的 LDA beta 使用旧状态，不能作为 mixed-stage beta 的直接依据

**作者：Codex；请求：Zhenyu澄清要找的是beta分阶段本身的文献支持，并问
Paardekooper使用哪个时刻。** 只读核查论文及作者公开ASTRIX源码，未改thesis或solver。

明确结论：ASTRIX v1.1.0（2017-05-18，b8dc85a569d8aa87166af2d8f7903dbaa5b2dae1）
在timeloop.cpp:245--252先用预测态构造新空间总残差和N贡献，然后:254--264明确调用
CalculateParameterVector(1)，切回保存的旧状态，再调用CalcTotalResLDA。
param.cu:118--137确认flag1取vertexStateOld；totalresLDA.cu确认该旧状态决定K和
LDA分配，作用于包括时间项在内的整个total residual。v1.0.0（2017-02-10）也有此切换。

因此论文Eq63/65中没有时间下标的beta，在这些同时期公开实现中是beta_n：旧空间项、
新空间项、F1时间项全用beta_n。新空间残差本身仍由U*计算。不能从“第二阶段重算
residual”推出“第二阶段LDA beta也重算于U*”。当前AREPO-RD的旧空间beta_n、
新空间beta_*、F1 beta_*是不同约定。N则不同：Eq62及源码确实分别计算U_n/U*的
N空间分配，时间项lumped，不能将此支持直接移用于LDA/F1。

§70列出的文献支持RK-RD/F1框架，但本轮仍未找到对当前mixed LDA约定的直接论述；
这是已查文献的边界，不是断言所有RD文献都没有分阶段beta。旧Yee三组对照中的
coherent-old对应这里识别出的beta时刻，但不意味着其它算法细节与ASTRIX相同。

完整源码链、固定commit链接及两种corrector公式记录在
`PAARDEKOOPER_STAGE_BETA_AUDIT_20260917.md`。公开源码及hash档案：
`../local_runs/paardekooper_stage_beta_audit_20260917_v1/`。未编译或运行ASTRIX；未做
新hydro测试，未commit/push。chapter4源文件SHA256仍为§70的153382c9...。

## 72. 2026-09-17：早期 RK2-RD 的 common beta 与是否统一旧状态的判断

**作者：Codex；请求：Zhenyu问早期RK2-RD是否都使用相同beta、是否省略取值细节，
以及当前方法是否应统一beta_n。** 本轮只作文献核对、数学比较和建议，未改solver/thesis。

应区分：corrector时间项和两个空间项共用一个beta，与predictor/corrector全程都取
步初beta_n。Ricchiuto & Abgrall2010 Eq13/36/42/53及Arpaia2015 Eq28/49--53明确
共同分配结构，但LDA beta没有明确非线性state的时间下标；线性定常advection推导中
固定网格的LDA beta本来不随解变化。Warzynski/Hubbard/Ricchiuto2015 Eq8及§5也
是common unindexed beta，其主方法要解global consistent-mass系统，不能混同当前GL。

更广的RK-RD并非必须冻结beta：Ricchiuto2015 JCP280:306--344，
doi10.1016/j.jcp.2014.09.027，§4.3 Eq43--47明确在predictor用空间LF残差、corrector
用总LF残差分别投影/限制并构造LLF分配系数。这是nonlinear LLF的stage-dependent
系数，不是当前Euler LDA的mixed beta_n/beta_*，不能移作后者的直接依据。

数学上定义PhiT=(|T|/3)sum(deltaU/dt)+.5(phi_n+phi_*)，当前mixed残差恰为
beta_* PhiT + .5(beta_n-beta_*)phi_n。多出的三角形内重分配项在每stage sum(beta)=I
时总和为零；因此改变分配而不自动破坏守恒。共同beta保留了直接分配整个total
residual的结构，但该恒等式不是精度、稳定性或beta_n优越性的证明。

Codex建议：在最终确定static LDA/F1论文基准时，倾向coherent beta_n候选，与公开
ASTRIX约定一致并减少无已证收益的自由度；不是必须马上修的bug，也不直接替换默认。
先用当前Gauss3/glass equal配置作小范围对照，不能用旧Roe/jittered Yee结果替代。
旧实验density L1标量差约0.13%，三组固定h时间阶都约1，所以改beta不能宣称修复时间阶。
hierarchy的n必须按元素所对应区间起点定义；moving的几何/拓扑另论。新phi仍取U*，
只有分配/F1取旧beta，不能把整个第二遍状态冻结，也无需数值上增加网格构造或残差遍数。

完整出处和推导追加到`PAARDEKOOPER_STAGE_BETA_AUDIT_20260917.md`的Follow-up。
未运行新hydro测试、未commit/push。


## 73. 2026-09-17：将 static LDA/F1 默认改为共同 beta_n，并更新 Chapter 4

**作者：Codex；请求：Zhenyu明确同意将默认改成共同beta，并在thesis说明早期beta_n、
beta_*比较暂未发现明显差别。** 标准static LDA/F1的equal内部两遍、equal split hooks
和hierarchy默认共同使用区间起点beta_n。新增显式对照flag `RD_LDA_MIXED_STAGE_BETA`
恢复原mixed；N/B、moving ALE、四遍rate-Heun和root Config未改。

实现将计算新空间残差的stage Roe平均与构造K+/K-的opening平均分开。equal从U*减去
已交换的dU恢复U_n；hierarchy在加stage-live predictor之前保留区间opening状态。
不新增mesh build、残差sweep、factorization或MPI payload，仅增加局部平均计算。
共同beta不意味着把phi(U*)也冻结。完整说明：`RD_COMMON_BETA_DEFAULT_20260917.md`。

初版仅冻结beta，15个case完成，但Sod equal/hier均在首个corrector触发A2，原始失败
保存在native/。根因是旧静止Euler入流矩阵rank3，新phi*可不在旧Sminus的range内；
直接广义逆会丢掉range外分量。equal首个报告defect2.6479e-6，tol2.2607e-15。
最终common空间路径明确采用beta_i=-K_i+ Sdag+(I-S Sdag)/3，保留range内分配，
将缺失部分均分三点。先独立核对raw分配之和等于Sx，再核对完整phi，未放宽A2/SVD
阈值。该延拓是数值选择，不是唯一极限或positivity证明；时间项仍用既有rank<4
lumped回退。论文脚注明确此处不再是完整的full-rank F1公式。没有把该延拓归于文献。

最终冻结源base adc424b加已存工作diff，source.tar SHA256
2ca8059f1e5de15b2d02889bbbff26e9ef31c1dc0e4bd350372268ac27bf4c06。
7配置独立native arm64构建，17/17原生算例通过：glass2304 Yee t1、KH t2等步/自然
层级及MPI1/4、uniform、16384-node Sod t.08、split中途checkpoint/restart、旧mixed
输出重放。MPI最大状态差3.2641e-14；equal internal/split和restart/control完全相等；
equal-bin hierarchy差2.8866e-14；所有snapshot普通求和最大归一化守恒误差1.4806e-14。
3个mixed对照与旧archive的按ID排序final U完全相等。Sod虽保持正的已存rho/p，仍有
undershoot，不宣称一般positivity。make check_rd全部通过；新增编译生产K构造及
range延拓helper的测试覆盖300个非平凡stage对和rank3静止态/100个compatible target。
初次MPI sandbox bind失败单独存failed_setup/，与上述两个数值失败严格区分。

当前Gauss3、glass2304、boost1、t1 Yee的DualArea加权rho L1：共同beta_n
6.1417994083e-4，mixed6.1530423075e-4，相对差约-0.183%；velocity L1约-0.0020%。
这不是解场相等，也不是time-order验证。共同beta_*本轮未重跑；论文中三方案“very
similar measured solution errors”明确指Earlier Yee tests，即§70恢复的2026-08-01
Roe/jittered对照，不冒充当前Gauss三方案实验。保留约time1及frozen-star F1限制。

thesis只改chapter4.tex中RD公式/简短解释、hierarchy interval-opening说明与KH引用；
增加common-beta KH图并保留旧mixed图。4-rank新KH max|deltaE/E0|为equal2.8023e-16、
hier2.9144e-16，均11个同步快照至t2，natural bins18/19。没有时间效率或两方案精度
排名结论。全书编译246页、零未解析引用；印刷143--149七页逐页渲染审核，公式引导句
与公式保持同页，脚注与图例清楚。写回前后核对126个tracked thesis文件，仅chapter4
变化；Ch1--3、FV/comparison、MPI、bib均保留。新chapter4 SHA256
b2d59518ff5e2bb5310d491b7727c35bb75288c934d1c679f3bb60f574bad38d。

档案：workspace `local_runs/common_beta_default_20260917_v1/`，包括before、初版native、
最终native_final、validation、common_beta_only.patch、参数/Config/header/binary/hash、
两轮beta_summary、KH CSV/audit、thesis_source、compile/qa/delivery记录。
审阅PDF：`output/pdf/chapter4_common_beta_review.pdf`；新KH standalone PDF同目录。
更新本地context与static baseline顶部，旧收敛结果明确标为历史mixed基准。
本轮未commit/push，未更改任何他人既有工作。


## 74. 2026-09-17：重跑 KH，核对 equal/hierarchy 能量曲线相反趋势

**作者：Codex；请求：Zhenyu要求重新做KH，问为何新版equal dE/E向下而hierarchy向上。**
用§73最终相同binary/IC/参数重新跑equal/hier、MPI1/2/4共6个case；原rank1/4的44个
快照全部字段按ID排序后逐位复现。另在隔离源的io.c添加仅snapshot时的逐rank十六进制
SphP.Energy/Mass/Momentum/W只读输出，共6个诊断case；66个快照与无诊断rerun逐位相同。
全部12case完成，未改生产solver或thesis，未改任何阈值，KH没有F1 rank fallback。

结论需要比“输出舍入”更准确：趋势确实存在于原始conserved energy中，而不是主要由
后处理重构造成。以100位Decimal累加原始double能量，t2的dE/E如下：
MPI1 equal=-7.17794e-17，hier=+3.85570e-16；
MPI2 equal=+4.40940e-17，hier=+2.41538e-16；
MPI4 equal=-2.24184e-16，hier=+2.90967e-16。
改变rank数会使equal终点符号反转，因此不能把负号当成equal方法固有的总能量耗散。
所有变化只是全局E0≈6.42249的几个binary64 ULP；一ULP/E0=1.38292e-16。
这支持演化中浮点误差累积的解释，但没有逐项定位哪个残差/变量转换/ledger加法贡献最大，
也不宣称hierarchy在所有输入/长时间总会增能。浮点偏置可有相关性，不一定上下随机跳动。

将stored Q、100位算术重构primitive能量、原float64重构三层分离。4rank t2的primitive
转换误差为equal -1.39762e-18、hier -7.01609e-19；后处理算术误差+2.27545e-18、
+1.17429e-18，远小于evolution中的≈3e-16。原图使用逐node能量差的fsum，复跑一致；
若改用Python普通顺序sum再减总量，equal会被求和误差改成+1.1063e-15，因此不能用
挑选求和算法/曲线方向来“改善”图。建议论文日后优先直接统计stored extensive energy。

真实配置仍为static glass2304、Gauss3/common beta_n、gamma1.4、CFL.3、equal dt1/1024、
hierarchy dt1/1024与1/512、t0--2、11个共同同步输出。新的6面板图按MPI1/2/4分别展示
snapshot重构与stored energy，并保持相同纵轴；PDF渲染目检通过。
报告：`RD_KH_ENERGY_ROUNDOFF_AUDIT_20260917.md`。
档案：workspace `local_runs/kh_roundoff_audit_20260917_v1/`，含原binary/provenance、
6个rerun、diagnostic/source及patch/2构建/6运行、hex dumps、分析脚本和CSV/JSON、QA。
新图：`output/pdf/kh_energy_roundoff_audit.pdf`。source母档案SHA256仍为
2ca8059f1e5de15b2d02889bbbff26e9ef31c1dc0e4bd350372268ac27bf4c06。
未commit/push，未修改已放入thesis的图。


## 75. 2026-09-17：删除 RD 公式下方大括号

**作者：Codex；请求：Zhenyu要求公式下面不要大括号。** 仅去掉chapter4中N/lumped和
LDA/F1两条公式的3个underbrace及其说明标签，数学项、符号、公式编号与正文保留。
全书编译245页，零未解析引用；印刷143--144页渲染核对通过。核对126个tracked文件，
仅chapter4.tex变化。档案：workspace `local_runs/chapter4_no_underbraces_20260917_v1/`，
含before、diff、编译/QA/delivery和`output/pdf/rd_formula_review.pdf`。未改solver、图、
Ch1--3，未commit/push。


## 76. 2026-09-17：恢复 mixed-stage 基准，common beta_n 保留为对照

**作者：Codex；请求：Zhenyu希望以旧设置为基准，并在thesis说明像Paardekooper
那样保持共同beta_n也未显著改变已测结果。** 标准static LDA/F1不带flag时恢复
beta_n起点空间项、beta_*终点空间项/F1时间项。新增显式
RD_LDA_COMMON_OPENING_BETA比较开关，旧RD_LDA_MIXED_STAGE_BETA兼容保留；两者
互斥。common秩亏空间延拓保留在opt-in分支，未触及N/B/moving/rate-Heun或root Config。

冻结源独立构建internal/hier/common；4-rank KH equal/hier至t2各11快照，Yee
mixed/common至t1各5快照，共32份状态按ID逐位复现此前对应档案。positive/conservation
门槛不变，make check_rd四脚本通过。源tar SHA256
af2bd74ea3830839ad2f55fc53b111f82750a4c2af55dc8e44ae60bd2d71ffe3
。回归复现不代表重新证明时间阶或一般positivity。

Chapter4恢复mixed公式，common beta_n段落保留Paardekooper引用，明确只说已测
advected Yee误差变化不明显；共同beta_*明确为earlier tests。公式下不加大括号。
恢复旧rank4 mixed KH数据，y轴Delta E/E0 [10^-16]；曲线方向不作为物理精度排名。
此前准备的rank2 common图未安装，档案保留。全书245页、零未解析引用，印刷143--148
逐页渲染审核。安装前后核对126个tracked文件，只改chapter4.tex并新增KH图，其它
章节、bib、FV/comparison、MPI保留；chapter4 SHA256
70284abc1147c58cc5f67aef47e4bf71774e904b0b4e2464ce6672018cb7d60f。

报告：`RD_MIXED_BETA_BASELINE_RESTORED_20260917.md`。档案：workspace
`local_runs/restore_mixed_baseline_20260917_v1/`，含before、patch、source/config/header/
binary provenance、native_summary、figure_data、thesis compile/QA/delivery。审阅PDF：
`output/pdf/chapter4_mixed_baseline_review.pdf`。更新context与baseline顶部标明§73被取代。
未commit/push，保留所有既有未提交工作。


## 77. 2026-09-17：hierarchy 示意图去掉底部说明，thesis 图片去掉日期

**作者：Codex；请求：Zhenyu指定删去hierarchy图底部两行说明，并将图片名去掉091x日期。**
修改科学矢量图生成器，删除Shaded triangle/Distributed contribution说明及Derived
triangle timestep公式行；保留节点timebin颜色与Ring synchronized图例，tight bbox
去掉底部多余区域。输出无日期stem，原日期版本在开发档案中保留以维持证据链。
Thesis全部带202609xx日期的6个图片重命名去掉日期（含未使用的旧KH/common对照图），
Chapter4四处引用同步修改；flowchart本来无日期。其它图内容和正文保持。

隔离全书编译245页、零未解析引用，5张图所在页164/169/171/174/175逐页渲染审核。
安装前核对所有tracked文件及figure目录hash；其它章节/bib与未修改图片内容保持。
Chapter4 SHA256：1febba10238cd28c2eb2bfcd4053e6446b796533538c1454caa3e015d3f38f49
档案：workspace `local_runs/chapter4_figures_clean_names_20260917_v1/`，包含before hashes、
generator before、rename_map、compile/QA/delivery与审阅PDF。没有solver改动、native重跑、
commit或push。


## 78. 2026-09-18：整理 Chapter 4.2/4.3，选定 moving baseline 并将替代方案标红 to delete

**作者：Codex；请求：Zhenyu明确要求整理moving mesh RD theory和implementation，
以Arpaia + contour integral + comoving frame为baseline，其它方案移至两节末尾，
红字注明“to delete”。** 输入thesis HEAD为cb8d26d，tracked tree clean；最新本地
结构已将hierarchy/MPI收回static 4.1，所以moving部分确实编号4.2/4.3。
本轮没有fetch/pull/commit/push，保留所有既有untracked资源及AREPO未提交工作。

选定的**thesis reference implementation**是2D median-dual nodal P1-U、nonconservative
intensive contour、nonlinear physical flux Gauss3、Arpaia midpoint temporal area/modified
divisor、element frame b_T=mean generator velocity、mixed-stage LDA/F1。对应现有
`examples/yee_2d/Config_RD_ALE_LDA_GAUSS3_EQUAL_SPLIT.sh`；未改变solver/default Config。
该原生路径限于单rank、global equal hydro timestep、pure gas、noncosmological flow。
rd_step_begin只登记endpoint；正常重建一次new Delaunay后，rd_step_end连续执行两个
physical residual sweep，同new connectivity/midpoint geometry。不是old-mesh predictor。
空间rank/range守恒断言及rank<4 temporal lumped fallback照实描述；RD CFL diagnostic
只报告，不写成已强制采用的timestep选择。

4.2以所选Gauss3 nonlinear contour和element-frame表达代替“working alternative”的
不确定表述，保留continuous ALE、DGCL及Arpaia两阶段推导，明确beta时刻属于本项目
约定；静态退化指相同mass/update结构及已选Gauss residual，不能自动等同旧Chapter3
Roe physical residual。保留uniform/positivity/time-order/endpoint conservation的区别，
不宣称当前GL/F1固定h时间二阶。4.3按真实Q^n/m_old→D_i U_old→RK→m_new U_new
重写storage流程，避免把旧draft中的endpoint rebase当成native temporary ledger。

加入同new-connectivity两扫描的endpoint总量分解：
`sum(Qnew-Qold)=sum((mhat_old-mactual_old)Uold)+sum((mnew-D)(Unew-Uold))`。
这是在periodic shared history、有效三角剖分、守恒分配及正确temporal column sums下
的代数推导，不是新native gate。第一项topology basis rebase，第二项Arpaia divisor到
actual endpoint Q的权重转换；无flip时第二项仍可能非零。uniform跨flip保持不能代替
非均匀态endpoint守恒。此前old/new-stage cavity correction公式不是这个baseline的
两扫描公式。完整推导、文献边界和source查验放在档案SCIENCE_REVIEW.md。
旧Sod/Yee Gauss实验涉及各自topology-repair配置，不能把所有结果转借给本轮不启用
repair的exact reference。论文正文已明确这一provenance边界。

两节末尾分别以红色group和“Alternative ... (to delete)”保留其它选项：nodal-flux
trapezoid、legacy Roe split、Gauss5、lab/arbitrary frame、N/B/其它mass或time operator、
Campoli；direct U/pending numerator、Voronoi evolution、真正old/new stage split、
fictitious deformation/remap及moving hierarchy open intervals。moving hierarchy旧图
留在红色候选段，caption和label也为红字；group后4.3/4.4恢复黑字。未修改图片本身。

隔离full XeLaTeX编译exit0、247页，引用全部解析，无duplicate label。
印刷153--177页渲染审核，baseline公式、两节红字及transition检查通过；PDF content
colour检查确认red alternatives和caption，没有颜色泄漏。原全书其它章节/4.1的既有
排版警告保留；新moving段只有不可见的0.10518pt paragraph overfull，无裁切。
安装前核对HEAD/全部tracked文件和Chapter4 PDF资源hash；只写chapter4.tex。
4.1及4.4后源文逐字节保持，Ch1--3/bib/figures保持。新chapter4 SHA256：
`0336d95e0d3d0faadbba2af7d2eb1e147a53f2b77a5036d15b3087833f80065f`。Documentation-only，未build/run hydro，无新增数值验证。

档案：`../local_runs/chapter4_moving_baseline_20260918_v1/`，含before/hash/source mirror、
exact chapter4 patch、science review、compile、rendered pages、colour/QA与delivery。
审阅PDF：`output/pdf/chapter4_moving_mesh_review.pdf`。
本地thesis需按用户正常GitHub/Overleaf流程同步；未commit/push。


## 79. 2026-09-19：以 thesis 为准恢复 mixed-stage 默认并修正 4.1 元数据

**作者：Codex；请求：Zhenyu指定以Chapter 4.1的mixed-stage公式为准，修改代码默认；
KH图改回真实4 MPI ranks，并修复逐边通量积分。** 标准static LDA/F1再次恢复为
无flag时mixed-stage：起点空间项使用beta_n，终点空间项及F1时间项使用beta_*。
`RD_LDA_COMMON_OPENING_BETA`显式选择共同opening beta_n；
`RD_LDA_MIXED_STAGE_BETA`保留为兼容的显式默认选择，两者互斥且只允许标准static
LDA/F1。当前solver与§76冻结并原生回归过的source逐字节一致；Template注释原已表达
这一选择。`make PYTHON=/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python check_rd`
四项全部通过。

Thesis只做用户指定的三处修改：KH caption及正文由2 ranks改为4 ranks，与现用PDF的
rank4 mixed数据一致；边界通量末项改为
`sum_{e subset partial T} int_e F(U_h) dot n_{T,e} dl`。未扩写hierarchy守恒条件，
未改N-scheme positive表述或其它4.1文字。完整thesis以XeLaTeX编译通过，246页，
零未解析引用。
本轮未commit/push，保留所有既有工作。


## 80. 2026-09-20：合并 Chapter 4.2.1/4.2.2 并改用 fixed-coordinate partial derivative

**作者：Codex；请求：Zhenyu要求合并moving triangulation与ALE Euler equation两小节，
并去掉容易混淆的 $\mathrm D_{\boldsymbol\sigma}/\mathrm Dt$ 记号。** Chapter 4.2原
4.2.1和4.2.2现合并为“Moving triangulation and ALE equations”；两个既有section
label均保留并指向新的4.2.1，后续小节自动前移。开头统一定义参考映射
$\mathbf x(\mathbf X,t)$、$J$、移动三角剖分和节点轨迹，并新增fixed-reference与
fixed-space导数关系
$\left.\partial_t f\right|_{\mathbf X}=\left.\partial_t f\right|_{\mathbf x}
+\boldsymbol\sigma\cdot\nabla_{\mathbf x}f$，其中连续网格速度明确写为
$\boldsymbol\sigma=\left.\partial\mathbf x/\partial t\right|_{\mathbf X}$，
而$\boldsymbol\sigma_h$保留给$P^1$离散插值。基函数输运式和intensive ALE Euler
equation均直接使用带$\mathbf X/\mathbf x$下标的$\partial$，不再使用
$\mathrm D_{\boldsymbol\sigma}/\mathrm Dt$。

在临时完整源树中以XeLaTeX编译通过，共245页；无未解析引用、citation或重复label。
目录确认合并小节为4.2.1、后续contour residual为4.2.2；印刷页152--154的PDF文字
提取核对了导数关系、GCL及conservative/intensive ALE公式。本轮未改solver、其它
章节、bibliography或图片，未commit/push。

## 81. 2026-09-21：合并 ALE balance 与 Arpaia contour residual 推导

**作者：Codex；请求：Zhenyu批准将讨论后的4.2.1/4.2.2结构写入本地thesis，暂不提交GitHub。**
保留用户最新4.16及之前的推导；以随网格运动的control volume C(t)及固定preimage
为起点，用参考域积分、换元和散度定理的连等式推出4.17。正文只定义Arpaia
intensive spatial residual tilde phi，再引入移动仿射三角形、P1解与网格速度插值，
推导element-mean mesh velocity对应的contour form。明确4.17右端在相同离散场下
等于负tilde phi加geometric integral，避免混淆完整保守边界通量与Arpaia空间项。
原phi_ALE定义及差值关系移入节末红色“to delete”候选段；正文uniform-state说明
相应调整。Gauss quadrature内容后移到现有RK2之后，未改RK2/co-moving公式。
4.3、其它章节、bibliography和图片保持不变。

隔离完整源树XeLaTeX编译成功，246页，无未解析引用/citation或重复label。
PDF页174--177、184--186完成渲染审核，调整两处分页使引导句和公式保持在一起。
安装前比对所有tracked文件hash以防覆盖并发修改；只安装chapter4.tex与master.pdf。
本地预览：`/Users/zhenyuwu/Desktop/MyThesis/Zhenyu-PhDThesis/zhenyu_thesis/master.pdf`。
档案：`../local_runs/chapter4_ale_contour_20260921_v1/`，含原文/hash、完整编译源树、
changes.patch、qa.json、页面渲染及delivery.json。Documentation-only，未运行hydro，
未commit/push。


## 82. 2026-09-21：补充 Hubbard conservative ALE 对照与 contour 选择动机

**作者：Codex；请求：Zhenyu建议简述其它residual选择，并解释为何选contour表达。**
在4.17与Arpaia residual定义之间补充Hubbard等(2020)采用对应conservative ALE的
space-time构造；不把完整space-time residual等同于此处瞬时空间边界通量。
核对出版商摘要 DOI 10.1016/j.camwa.2019.09.019 的conservative ALE表述。
在contour推导后列出旧sum K_phys Uhat减integral sigma_h dot grad U_h的split表达，
解释其混合Roe-linearised Uhat与P1 conservative U，而contour在两项中使用同一U_h。
明确非线性Euler的两种physical-flux构造一般不同，不能无条件当作代数恒等改写。
本轮仅新增两处说明和一处分页面包装；后续co-moving/RK2、4.3及其它章节均保持。

完整XeLaTeX编译通过，246页，无未解析引用或重复label；PDF176--178页渲染核对通过。
安装前逐一核对tracked文件hash，只更新本地chapter4.tex与master.pdf，未commit/push。
档案：`../local_runs/chapter4_residual_motivation_20260921_v1/`（diff、REVIEW.md、
编译、QA、渲染及delivery.json）。Documentation-only，无新增hydro运行。


## 83. 2026-09-21：先讲 RK2，压缩 DGCL 并后置计算细节

**作者：Codex；请求：Zhenyu批准先调整4.2论述顺序，随后逐步审核推导。**
4.2.1 ALE/residual之后直接接4.2.2 Arpaia midpoint RK2；comoving coordinates
与Gauss quadrature改为4.2.3和4.2.4，scope为4.2.5。技术内容仍在4.2后部，4.3不变。
删除独立DGCL长小节及重复的median-area和uniform-state公式；RK2开头保留线性
vertex trajectory与二维midpoint area identity，作为modified mass的必要定义。
DGCL压缩为两stage更新之后的四句说明，保留uniform-state与一般守恒性的区别。
核心modified mass、predictor、corrector、second residual、F1公式逐字保持；LDA
展开式使用通用tilde phi，Gauss3选择留至后文。为首次使用K补充其ALE速度shift，
frame保持条件改为向后引用。现有time-order与divisor限制仍保留。

完整XeLaTeX编译成功，246页，零未解析引用/重复label；PDF178--181、184页渲染
审核，RK2位于印刷156--158页。安装前检查所有tracked文件hash，更新本地
chapter4.tex及master.pdf；此前ALE推导、comoving/求积内容、红色候选段、4.3及
其它章节保持。Documentation-only，无solver修改/运行，未commit/push。
档案：`../local_runs/chapter4_rk2_order_20260921_v1/`，含before/hash、diff、
REVIEW.md、编译源树、QA、页面渲染和delivery.json。


## 84. 2026-09-22：明确坐标、Euler K-matrix 与当前三角剖分上的梯度

**作者：Codex；请求：Zhenyu批准按讨论小改4.13、K matrix和gradient/basis表述，并只预览4.2。**
4.13引导句直接引用Chapter3的坐标、守恒变量与Euler flux定义，移除physical coordinates
称呼。梯度定义改为“the spatial gradient on the current triangulation, evaluated at
fixed time”，保留小写x下标。明确current basis与fixed reference basis的pullback关系，
并写出n_i(t)=2|T(t)| grad_x psi_i(x,t)，注明inward normal按对边长度缩放，恒等式在
每个固定时刻成立。K_phys引用Chapter3的共同Roe状态Euler矩阵，速度是在U相同参考系
下尚未扣除网格速度的Roe平均流体速度；phys仅标记Euler通量部分。

所有既有编号公式逐字不变；4.1、4.3及其它章节保持。完整XeLaTeX编译成功，246页，
零未解析引用/重复label。截取4.2印刷151--167页，共17页，首页面裁切去除4.1内容。
仅打开 `../output/pdf/chapter4_2_preview.pdf` 供用户预览，编号保持全书编号。
预览1--6及末页渲染检查通过。安装前校验tracked文件hash，保存chapter4.tex/master.pdf。
档案：`../local_runs/chapter4_coordinate_wording_20260922_v1/`，含diff、before/hash、
编译、QA、excerpt脚本及渲染。无solver改动或hydro运行，未commit/push。


## 85. 2026-09-22：统一 K/ALE 记号、公式引用与4.2前两小节结构

**作者：Codex；请求：Zhenyu要求取消K_phys，说明Arpaia的ALE shift及Uhat/U无法直接合并，
并调整Equation引用格式、两节标题和median-dual段落位置。** 无上标K沿用Chapter3的
Roe Euler矩阵；k_ALE标量公式引用Arpaia2015 Equation59，同时给出K_ALE=K减网格速度
投影乘I/2。说明矩阵shift本身成立，但sum K_ALE Uhat把网格输运作用在Uhat_h上，
不能无修正替代作用在U_h上的旧split residual。4.2后续矩阵及4.3唯一一个K的LDA求解
公式同步标ALE，避免把未shift和已shift矩阵混用。

标题改为“ALE form of Euler equations”和“RK2 RD on moving mesh”。4.24--4.25的
median mass与静态semidiscrete update移到RK2节开头，公式未改成新的显式时间格式。
4.2正文引用改为Equation加数字、不加括号；display公式右侧标准编号括号保留。
RK2核心时间/质量公式保持，标签集合完整，未改变算法或solver。

完整XeLaTeX编译通过，246页，无未解析引用/重复label；只打开4.2预览，共18页，
首页/末页裁切以排除4.1/4.3。预览5--8及末页已渲染审核。安装前检查tracked文件hash，
保存本地chapter4.tex/master.pdf，更新 `../output/pdf/chapter4_2_preview.pdf`。
档案：`../local_runs/chapter4_k_notation_20260922_v1/`。无hydro运行，未commit/push。


## 86. 2026-09-22：审核 Chapter 3 到 Arpaia RK2 的推导衔接（讨论，未改 thesis）

**作者：Codex；请求：Zhenyu指出4.2.2直接列出方案而缺少推导，希望从Chapter3延伸，
并以|S_i(t)|替代面积别名m_i(t)，m只用于时间质量矩阵。** 核对Chapter3的RK defect、
时间质量分配及global-lumped corrector；核对Arpaia2015最终期刊版4.4.2、4.5与Appendix，
特别是73--84和91。关键衔接是Galerkin移动域时间项减geometric source，与采用
stage-shifted时间增量的稳定化项分开离散；第一阶段稳定化时间增量为0，第二阶段为
U*减Un。midpoint product重写之后，source与几何增量配对，得到
(1+dt div sigma/2)乘Galerkin状态增量，再global lumping得到modified area。
这不是只把静态phi替换为ALE phi，也不是DGCL单独唯一确定的算法。

审核中的重要限定：直线vertex motion的二维面积差midpoint identity精确，但几何
midpoint面积一般不等于端点面积平均。Arpaia Equation74写成等号；按当前thesis的
几何midpoint定义，直接按reference P1积分展开会剩下(area_endpoint_average -
area_midpoint)乘状态增量的项。固定光滑mesh motion时面积差O(dt^2)、状态增量O(dt)，
故该乘积重写需说明O(dt^3)近似，而不能作为任意二维变形下的精确恒等式。
此处是本轮代数审核发现的限定，尚未写入thesis，不将其当作新数值验证。
用户记号偏好已记录；后续正文应区分真实|S_i^{n+1/2}|与修正|bar S_i^{n+1/2}|。
本轮仅讨论和read-only文献核对，未改thesis/solver，未commit/push。


## 87. 2026-09-22：只读审核4.2.1，重写4.2.2的RK2推导

**作者：Codex；请求：Zhenyu要求不改其润色的4.2.1，按已讨论推导重写4.2.2。**
4.2.1与4.2.2以外全部源码逐字保持。只读发现：P1 conservative contour residual
与Chapter3 Roe sum K Uhat的直接等号一般不成立；scalar flux derivative不普遍等于
fluid velocity；Hubbard完整space-time residual不宜直接等同瞬时boundary flux；
geometric source应说进入modified area coefficient而非实际median-dual几何面积。
已向用户报告，未代改4.2.1。

4.2.2先定义直线vertex paths、Tmid、实际|S_i(t)|与midpoint积分<>；从移动域
Galerkin balance与Chapter3 residual-correction延伸。显式写出Arpaia78a/78b的source
与stabilization分离，第一阶段零stage-shifted增量、第二阶段U*减Un；展示时间项与
source抵消为Un1减U*，经row-sum lumping得到modified area。保留<>，不定义q或
面积别名m(t)，m仅时间质量矩阵。引用期刊Equation50/55/63--65/73--78/81/84/91。
保留stage-dependent LDA/F1选择、DGCL简述与时间收敛限制。按§86限定，将Equation74
的几何midpoint乘积改写标为光滑情形下O(dt^3)积分近似，区别于精确二维面积差恒等式。

完整XeLaTeX编译通过，249页，零未解析引用/重复标签；只预览4.2共20页。
新增推导印刷156--161页已渲染审核，无新增overfull公式。预览生成曾在编译输出PDF
尚未写完时提前读取，出现EOF错误；编译完成后重跑通过，交付校验使用最终PDF hash。
安装前核对所有tracked文件hash，保存chapter4.tex/master.pdf；未commit/push。
档案：`../local_runs/chapter4_rk2_derivation_20260922_v1/`，含before/hash、diff、REVIEW、
编译源树、QA、渲染、delivery。预览：`../output/pdf/chapter4_2_preview.pdf`。
Documentation-only，无solver修改/运行。


## 88. 2026-09-22：补充contour/Roe相同的条件，简化scalar速度表述

**作者：Codex；请求：Zhenyu建议补充contour flux与Roe构造何时相同，并保留Hubbard简述。**
仅修改4.2.1 K-matrix对照附近：Equation4.24改为split approximation与近似号；说明
Euler-flux部分使用相同Chapter3 Roe-parameter interpolant时精确相同，而当前P1-U
contour与Roe构造在小状态变化的线性阶相同，光滑且足够细网格给出该小变化条件。
这是对Chapter3 quadratic-in-Z构造与Taylor展开的判断，不宣称光滑时有限网格精确相等。
将a说明为characteristic advection velocity，并简短括注passive scalar transport时
就是fluid velocity。核对Clawpack Riemann book Advection官方章节。Hubbard与4.2.2
及其余源码逐字保持，无扩展讨论。

完整XeLaTeX编译通过，249页，零未解析引用/重复label；仅4.2预览20页，改动附近
印刷155--157页渲染审核。安装前核对tracked文件hash；保存chapter4.tex/master.pdf。
档案：`../local_runs/chapter4_flux_equivalence_20260922_v1/`。无solver改动/运行，
未commit/push。预览仍为`../output/pdf/chapter4_2_preview.pdf`。


## 89. 2026-09-22：按用户习惯精简4.2.2文字与统一美式拼写

**作者：Codex；请求：Zhenyu要求4.2.2用美式拼写、少用分号，并直接引入RK2/midpoint。**
仅调整4.2.2 prose：开头压缩为两句“We construct the RK2 time integration for moving
mesh RD in this section. Following Arpaia et al., we first define the midpoint
geometry.” 统一stabilization、normalized等美式拼写，移除本小节所有分号，精简重复
铺垫与连接句。保留Chapter3衔接、文献式号、midpoint近似限定及其它数学含义。
所有display公式与label逐一比较保持原样，4.2.1及4.2.2外源码逐字保持。

完整XeLaTeX编译通过，249页，零未解析引用/重复label，无新增overfull公式。
4.2预览20页，4.2.2印刷156--161页渲染审核通过。安装前核对tracked文件hash。
本地chapter4.tex/master.pdf及`../output/pdf/chapter4_2_preview.pdf`已更新。
档案：`../local_runs/chapter4_rk2_wording_20260922_v1/`。未commit/push，无solver改动/运行。


## 90. 2026-09-23：讨论midpoint geometry的顶点面积恒等式（未改thesis）

**作者：Codex；请求：Zhenyu要求结合Arpaia Equation62--65，用顶点展开面积及面积差。**
核对最终期刊版p516原PDF。逆时针、无翻转三角形面积为shoelace determinant的一半，
等于(1/4)sum x_i dot n_i，其中n_i为对边长度缩放的inward normal。
面积差精确为(1/2)sum n_i^mid dot (x_i^{n+1}-x_i^n)。Equation62的几何向量k_i
在当前thesis法向记号下对应n_i/2，不是Equation59的scalar upwind coefficient。
取Equation63的displacement velocity并用P1 sigma_h，得到Equation64的
Delta area=dt int_Tmid div sigma_h。对直线vertex trajectories，面积随时间二次，
其时间导数一次，因此Equation65的时间midpoint积分精确。midpoint vertex geometry
不等同于端点面积的算术平均。仅讨论并记录，未修改thesis或solver。


## 91. 2026-09-23：讨论Galerkin/stabilization拆分的原因（未改thesis）

**作者：Codex；请求：Zhenyu询问Arpaia为何区分Galerkin与stabilization。**
核对期刊3.2/3.5/4.4/4.5、Equation27/49--51/68--70/78a--b及Appendix91。
用scalar notation解释test weight w_i=psi_i+gamma_i：Galerkin给基础弱形式，gamma提供
upwind/residual-distribution修正。拆分在静态explicit RK-RD中已经存在，原因是Galerkin
使用当前stage未知增量，stabilization使用已知stage-shifted增量（第一stage零，第二
U*减Un），随后lumping实现显式更新。移动网格增加DGCL配平需求：Galerkin moving
integral derivative与负geometric source成对，stabilization采用intensive ALE residual，
避免对常状态留下未配平几何项。连续GCL下不同表达可等价，离散stage-shift后不能
任意互换。两部分是相加形成最终离散方程，不是分别强制满足的两组独立方程。
未修改thesis或solver。


## 92. 2026-09-23：保留用户新前文，调整stage标题与时间残差分配解释

**作者：Codex；请求：Zhenyu已同步修改至First stage，要求普通标题换行、少用Galerkin/
stabilization术语，并按Equation4.32 RHS行次解释，先本地编译。** 以当前Desktop源文
为基准，只改First stage至LDA段之前的stage prose。之前用户修改及之后全部源码逐字
保持，所有display公式与label均逐一比较保持原样。

First stage (predictor): / Second stage (corrector): 改为普通字体独立行。用4.32 RHS
第一/二/三行对应时间/空间/geometric source，明确Chapter3的时间RD分配给出第二
阶段的matrix action减P1 weighted action。保留所选离散方案的性质，不宣称单靠DGCL
推出。4.37抵消改用行与项的位置说明。保留Arpaia49--51/91及81/84的式号对应。

完整XeLaTeX编译通过，249页，无未解析引用/重复label，无新增overfull公式。
预览4.2共20页，印刷158--160页渲染检查标题/公式通过。安装前校验tracked文件hash，
更新本地chapter4.tex/master.pdf与`../output/pdf/chapter4_2_preview.pdf`。
档案：`../local_runs/chapter4_stage_exposition_20260923_v1/`，含before/hash、diff、
REVIEW、编译、QA和delivery。无solver改动或hydro运行，未commit/push/写Overleaf。


## 93. 2026-09-23：统一T含顶点i记号并补充row-sum lumping推导

**作者：Codex；请求：Zhenyu要求把T in D_i改为T ni i，避免与dual area混淆，稍详写mass lumping。**
替换chapter4中全部7处T in D_i（均在4.2）。4.34之前补充单元时间项展开、P1质量矩阵
行和利用partition of unity等于|Tmid|/3的两条不编号公式，解释将行和放入对角线后只
乘节点i增量。明确lumping是离散近似，几何系数在每个三角形内恒定并乘其row sum。
其余文字和已有公式内容保持，标签及原编号保持，4.34仍在印刷159页。

完整XeLaTeX编译通过，249页，零未解析引用/重复label，无新增overfull公式。
4.2预览21页，印刷159--160页已渲染检查。安装前核对tracked文件hash，保存本地
chapter4.tex/master.pdf及`../output/pdf/chapter4_2_preview.pdf`。
档案：`../local_runs/chapter4_mass_lumping_20260923_v1/`。无solver改动/运行，
未commit/push/写Overleaf。


## 94. 2026-09-23：给出实际dual-area定义并删除独立DGCL说明段

**作者：Codex；请求：Zhenyu要求Note that...说明modified coefficient与实际面积的区别，
并删除过长DGCL部分。** 4.34后改为Note that modified |bar S_mid| is generally different
from actual median-dual area |S_mid|=sum_{T ni i}|Tmid|/3。删除独立Discrete geometric
conservation标题、未被引用的section label及uniform-state证明段。前面推导必需的
几何恒等式与所有display公式保持，静态极限、divisor与时间阶限制不是本轮删除对象。

完整XeLaTeX编译通过，249页，零未解析引用/重复标签。4.2预览21页，印刷159、161页
渲染审核通过。安装前核对tracked文件hash，更新本地chapter4.tex/master.pdf及
`../output/pdf/chapter4_2_preview.pdf`。档案：`../local_runs/chapter4_dgcl_trim_20260923_v1/`。
无solver改动或hydro运行，未commit/push/写Overleaf。


## 95. 2026-09-23：解释4.36的来源及4.32的ALE/Lagrangian关系（讨论）

**作者：Codex；请求：Zhenyu询问为何加入4.36，以及4.32是否可称类似Lagrangian守恒律。**
核对当前Chapter3时间残差定义与Arpaia54--55。解释4.36不是零恒等式，也不是4.32或
DGCL强制给出的项：先将Un1-Un拆成(Un1-U*)+(U*-Un)，结合几何项后得到modified
coefficient乘corrector增量及剩余P1 weighted predictor增量。用Chapter3所选RD temporal
matrix action替换后一个贡献，差额恰为4.36，故是离散分配选择。4.32可重组为随mesh
运动的weighted conservative ALE balance；仅sigma等于fluid velocity时为真正material/
Lagrangian描述，任意mesh velocity时宜称weighted ALE conservation form following
moving mesh，可解释其Lagrangian-like视角。未改thesis或solver。


## 96. 2026-09-23：second stage先合并时间/几何项，再解释mass-matrix替换

**作者：Codex；请求：Zhenyu接受先合并moving-domain time和geometric source，再用文字
说明把predictor增量的weighted integral替换为时间mass-matrix action。** 仅重写second
stage推导段。新4.36展示时间项与source合并，新4.37将Un1-Un拆成corrector增量加
predictor增量。文字说明第二项采用Chapter3的temporal RD distribution，保留Arpaia
49--51/91的出处，再引出不变的4.38 residual、4.39 balance和4.40 lumped update。
删除旧4.36“先加correction”和旧4.37长装配式，替换两个局部label且无外部引用。
其余源码和最终scheme保持不变，不引入Galerkin/stabilization记号。

完整XeLaTeX编译通过，249页，零未解析引用/重复标签，无新增overfull公式。
4.2预览21页，印刷159--161页渲染检查通过，重点推导在160页。安装前核对tracked
文件hash，更新本地chapter4.tex/master.pdf及`../output/pdf/chapter4_2_preview.pdf`。
档案：`../local_runs/chapter4_corrector_order_20260923_v1/`。无solver改动/运行，
未commit/push/写Overleaf。


## 97. 2026-09-23：明确mass replacement两端，补充LDA/N与K_ALE用途

**作者：Codex；请求：Zhenyu要求给出replace两边数学式，同时说明LDA和N，并核查K_ALE是否
与4.2.1冲突。** 仅改4.2.2两段：展开weighted predictor increment为P1 mass积分作用，
用longmapsto明确替换为RD temporal matrix action，强调这是离散选择而非代数等式。
补充K_ALE在此构造相对波速的characteristic splitting，不将contour total认作sum K_ALE Uhat。
4.2.1逐字保持。LDA直接以beta分配选定total，full-rank时sum beta=I。N raw残差则闭合
到shifted Roe total；如选contour total，必须补偿差额。列出等分修正这一选择，并限定
传统scalar N monotonicity不可自动沿用。核对当前solver.c的RD_ALE_CONTOUR_RESIDUAL
N/B correction（约5209行），与已有等分实现一致；不声称Gauss3/N已验证。另列N/lumped
和LDA/F1 temporal matrices及second-stage residual，selected baseline仍LDA/F1。

全文XeLaTeX编译通过250页，零未解析引用/重复label，无新增overfull公式。保留已有
编号与labels，4.2预览22页。新增段落印刷160--162页渲染核对通过。安装前检查全部
tracked文件hash，更新本地chapter4.tex/master.pdf和`../output/pdf/chapter4_2_preview.pdf`。
档案：`../local_runs/chapter4_n_lda_distribution_20260923_v1/`，含before/hash、diff、编译、
QA截图及delivery。无solver改动或hydro运行，未commit/push/写Overleaf。


## 98. 2026-09-24：省略空间梯度下标，前移精简Gauss3，并解释weighted moving balance

**作者：Codex；请求：Zhenyu要求开头统一说明空间梯度，后续省略x下标，将原4.2.4精简为
4.2.1末尾subsubsection；并在原4.32后加weighted conservation/Lagrangian条件说明。**
以当日Desktop最新源文为基准，统一nabla而保留时间偏导的fixed x/X标记。定义句明确
spatial gradient on current triangulation，with respect to x at fixed time。Gauss3保留
P1 edge interpolation、contour quadrature与nodes/weights、mesh term精确和nonlinear flux
近似的区别，删去重复LDA分配与后文重复的性质说明。后续quadrature引用改指公式，原有
Gauss公式labels保持。新增用户两句在moving weighted balance后，原4.32现为4.34。
4.1以及Scope之后全部源码逐字保持，其他章节/solver未改。

XeLaTeX全文250页编译通过，无未解析引用/重复label，无新增overfull box。仅4.2预览
21页；印刷152、156、158页渲染核对定义、积分和新增句子。安装前检查全部tracked hashes，
写回chapter4.tex/master.pdf和`../output/pdf/chapter4_2_preview.pdf`。档案：
`../local_runs/chapter4_gradient_quadrature_20260924_v1/`。无hydro运行或commit/push/Overleaf操作。


## 99. 2026-09-24：复核旧Roe split对照与co-moving实现（讨论，未改thesis）

**作者：Codex；请求：Zhenyu询问过去是否测试保留Roe split，以及是否难以结合co-moving。**
复核§31报告、legacy_split_20260912的summary/verification/config和当前solver的frame split
correction。该批为e33aea3历史冻结源码、LDA/GL-F1/Arpaia配对，对照IC已核验匹配：smooth
KH glass48²的lab/frame都在t=.800476同ID923负质量；Gauss3/5复用档到t10。Sod有效Nx64、
t=.08，split lab/frame均969步完成，平台速度std .023080/.022979，Gauss3 .022730；sharp
split两种frame均首步A2失败。uniform两种frame最大变化5.55e-16。
解释co-moving已经实现：将整个split correction C=-int sigma grad(U-Uhat)按C'=GC变换，
不能因特征算子mean sigma'=0就丢弃它。这是保持原lab离散算子的内部坐标变换，不意味着
该混合残差自动具备对外部boost的离散Galilean协变性；Gauss选择有smooth KH证据支持，
不是Roe积分本身不精确的结论。没有重跑实验或修改solver/thesis。

阅读旧RD_ALE_FORM_SELECTION.md时发现§3.2把缺陷解释为Roe Z在Galilean boost下非线性，
该说法不正确，不应继续引用：常数boost下Z'=H_b Z是线性变换，且U(Z'_h)=G U(Z_h)。这里
的问题是Euler flux采用U(Z_h)，mesh transport采用P1-U的混合重构；其额外boost项由两种
插值之差产生。旧实验数字与错误的机制解释需要分开使用，当前答复不重复后者。


## 100. 2026-09-24：核对LDA/N如何守恒分配contour及当前Gauss支持范围

**作者：Codex；请求：Zhenyu确认LDA独立用K_ALE作分配是否保持contour总和，以及N的当前代码。**
直接读当前develop_pureC_RD工作树solver（有既存未提交改动），未改solver或thesis、未运行实验。
LDA实现解Sminus X=Phi，再phi_i=-Kplus_i X，满秩/兼容解下保持target total；秩亏时广义逆
仅给range投影，不能无条件声称sum beta=I。moving标准路径用A2检查，静态common-beta
opt-in才有额外range补全；F1时间项另有rank-deficient diagonal lumping。
N在RD_ALE_CONTOUR_RESIDUAL下已有逐分量(Phi-sum rawN)/3等分修正（约5209--5246行），
随后A2检查。标准N不自动闭合到独立target，修正N可以，正性/单调性不因此获证。
RD_ALE_CONTOUR_GAUSS guard（75--82行）明确要求LDA，故现有N/B contour支持不能冒充
N+P1-U Gauss3/5支持；目前N contour是旧nodal-flux contour。单元空间residual-sum性质
与移动网格完整时间/几何/拓扑更新后的全局守恒分别表述。根Config.sh未存在，不猜当前二进制
配置；moving Gauss3示例配置确为LDA+F1+element frame。


## 101. 2026-09-24：N + Gauss3 原生试验与 N/LDA 的 Roe split 负质量复现

**作者：Codex；请求：Zhenyu要求试跑N+Gauss3的Sod和长期KH，并分别检查N/LDA的KH负质量。**
仅放开equal-step ALE N+Gauss3编译guard，复用已有N差额等分修正，不加positivity limiter、
不放宽A2，也不改变默认baseline。新增显式N示例配置与独立campaign/analysis脚本。
冻结adc424ba工作树（含用户既有改动），826 tracked文件校验，8配置独立build/binary，
所有原生运行单rank且OMP/BLAS各1线程，最多4任务。源码包SHA256为
b2a915f657bfc46ae6cce1cc315ea3776fafb74e8cd3e8d08b6d7a43302dd9c6。

8个uniform gate全部通过（最大变化1.9984e-15），make check_rd四项通过。
四组Sod全部完成t=.08（periodic128²，单管有效Nx约64，归一化时间.16，CFL.08）。
N/Roe与N/Gauss3密度L1为.0235933/.0233814，平台速度std为.0139150/.0146614，
不能称Gauss在N上普遍更准确。smooth KH glass48²、CFL.3、dt cap.02下，N/Roe、
N/Gauss3、LDA/Gauss3均完成t10。当前LDA/Roe于t1.0327148、ID374出现质量-8.234e-6，
前一步为1.36862e-5；predictor仍正、A2未失败、完整两阶段后最终状态检查失败。
另用历史e33aea3原二进制精确重放旧LDA/Roe，复现t.800476、ID923、质量-1.06377e-5，
五个保存快照的各字段逐项相同。历史与当前topology路径不同，不能混成同源码对照。

当前完成KH的终点质量漂移为1.19–1.38%，故空间分配闭合不代表完整moving update严格守恒。
该漂移根因未在本轮定位；Gauss改善本组LDA/KH生存性，不证明普遍正性、长期准确性，
也不能宣称N必须用Gauss。未开放N/Gauss5、static N/Gauss或moving hierarchy。
17次原生尝试共15正常完成、2次保留的负质量失败。报告含同色标KH演化、Sod解析对照、
质量/能量诊断及所有配置/二进制/日志溯源：
[专题报告](RD_N_GAUSS3_SPLIT_20260924.md)，档案
`../local_runs/n_gauss3_split_20260924_v1/`。未改thesis，未commit/push。


## 102. 2026-09-24：论文区分 N/Roe split 与 LDA/contour，并明确 ALE 特征分配守恒

**作者：Codex；请求：Zhenyu授权直接修改thesis，并澄清N用K_ALE时保留mesh correction。**
以本地最新chapter4.tex为基准，删除“不可以使用K_ALE”的过重表述。Numerical integration
先定义K_ALE，再写Roe split的两行等式，显式保留-int sigma grad(U-Uhat)。简述初步LDA/KH
负质量和contour完成对照，注明测试仍进行中，不放图或把正性当作定理。随后引入LDA的
P1-U contour与Gauss3。Distribution schemes以K_ALE正负分裂构造两scheme，明确LDA即使
使用contour总残差，仍用ALE特征速度/方向分配；在Sminus可逆假设下sum beta=I，故单元
residual总和守恒。N删去contour差额修正，改为原Roe split mesh correction的三顶点等分。
补充co-moving时该完整修正向量仍须变换并保留，修正后续仅LDA使用Gauss的交叉引用。

全文XeLaTeX250页通过，零未解析引用/重复标签，无新增公式溢出。4.2预览21页，印刷
155--157、162--163、166页渲染检查。保留既有labels，4.1和Scope之后（包括4.3）逐字不变。
安装前核对所有tracked thesis hashes以防覆盖并发编辑，写回chapter4.tex/master.pdf。
预览：`../output/pdf/chapter4_2_preview.pdf`；档案含before/diff/compile/QA：
`../local_runs/chapter4_n_split_lda_contour_20260924_v1/`。未改solver，未commit/push/写Overleaf。


## 103. 2026-09-24：当前 N/Roe 与 LDA/Gauss3 的 Gresho lab/co-moving 对照

**作者：Codex；请求：Zhenyu希望在当前scheme/residual选择下复测boost10，判断co-moving是否仍必要。**
采用旧generator的jitter48²、seed20260811、gamma5/3、unit box、boost0/10、CFL.3、cap.01，
冻结当前adc424ba工作树，分别构建N/Roe split与LDA/Gauss3的lab/frame四版本。当前common
begin/end/new-connectivity几何，不冒充历史Linux二进制精确重放，N保留完整mesh correction。
8个short t.02与8个long t1全部完成，long均4096步，没有A2/负质量终止；旧boost10首步失败
未在当前两方案复现。t1方位速度area-L1：N约.01971/.01976（b0/b10），LDA约.00792314，
lab/frame宏观剖面误差基本相同。全部长期质量漂移4.56e-5--6.20e-5，非严格全局守恒验证。

短时按ID匹配并去boost的velocity mean-absolute：N lab/frame均1.4981e-5；LDA lab8.0094e-13、
frame9.6632e-15。N的boost依赖不因计算坐标改变而消失。长期N约.002644，LDA约6e-10，
长期几何/拓扑与舍入扩散不能简单归结为单次线性求解误差。
现有condition-diagnostic另2次原生短跑，隔离副本仅加首步矩阵打印又2次短跑，保存快照
均与无诊断对照逐项一致。首stage4608元素，排除shift-cond>=1e8的2099个，余2509元素
boost10的cond2中位lab5.72e8/shift2.11e4，配对降低倍数中位2.40e4；全元素max-abs entry
中位9.38/.0538。真实近秩亏仍存在，co-moving改善坐标尺度但不消除rank deficiency。

4个boost10 uniform都正常完成，但N/lab压力变化1.1822e-12未通过原1e-12绝对门槛，
其frame为1.3856e-13，LDA lab/frame1.6076e-13/1.3145e-13。science launcher因此正确阻止
首次启动，日志保留；随后明确作为用户所请求的诊断对照运行，没有放宽gate/求解器断言。
总计6二进制24原生运行完成，但uniform门禁仅3/4通过。使用单rank，OMP/BLAS各1线程，
主对照4并发，与额外串行诊断重叠时最多5个rank。生产solver/thesis/默认Config未改。

结论：保留frame作为矩阵条件改善手段有依据，但本组当前boost10运行不以它为必要条件。
报告与图： [专题报告](RD_GRESHO_FRAME_COMPARISON_20260924.md)；完整归档
`../local_runs/gresho_frame_20260924_v1/`，含source/binary/IC/params/hashes、失败的门禁日志、
统计、剖面图和独立matrix_probe。新增campaign/analysis脚本，未commit/push。


## 104. 2026-09-24：关闭 co-moving 的 N/Roe 与 LDA/Gauss3 Sod / smooth KH 对照

**作者：Codex；请求：Zhenyu倾向将co-moving降为代码可选优化，先验证lab-frame的Sod和smooth KH。**
复用§101精确冻结source.tar，核验当前相关source hashes仍相同。4个新配置只移除
RD_ELEMENT_COMOVING_FRAME，其余scheme、IC、参数、CFL、mesh、Arpaia面积/双sweep不变，
对应co-moving控制复用已验证二进制及输出（未冒称重跑）。新4构建、4uniform和4science，
单rank、OMP/BLAS各1线程、最多4并发。uniform最大变化1.1102e-15，全通过原1e-12门槛。

新Sod N/Roe与LDA/Gauss3均完成t.08（periodic glass128²，单管有效Nx64，gamma1.4，CFL.08）。
lab/co-moving density L1分别N .023602714/.023593296，LDA .016941941/.016938943；相对变化
约.040%/.018%，velocity L1变化均低于.2%。LDA速度undershoot仍约-.738，与co-moving相近。

smoothKH glass48²、tanh宽度.025、gamma1.4、CFL.3、cap.02，N/lab与LDA/lab均完成t10，
没有负质量或A2失败。t10 lab N rho范围1.06459--2.27642、pmin2.33786，LDA rho范围
.842624--2.09448、pmin2.07284。lab N/LDA相对总质量漂移1.2339%/1.2231%，对应co-moving
1.3819%/1.1884%。终点横向动能lab N/LDA .0572951/.0807987，对照.0721590/.0935961，
分别低20.6%/13.7%。早期场接近，长期轨迹/涡细节明显分离，不能将其称作精确等价或
直接判定哪一个更准确。没有独立隔离舍入、rank、时间步、topology对差异放大的贡献。

结论：这组结果支持暂不将co-moving作为论文参考方案的必选技术环节，保留代码选项；
Sod和运行稳定性支持较强，KH长期精度支持有限，完整moving更新的全局守恒仍未验证。
此次不改thesis、生产solver或默认Config，未commit/push。保持Gresho中改善矩阵条件的
证据，不将旧LDA/Roe/lab boost10失败套用于当前LDA/Gauss3。

报告：[lab-frame Sod/KH对照](RD_SOD_KH_LAB_FRAME_20260924.md)。档案含输入/配置/来源
核验、原始日志、配对JSON、Sod解析剖面、KH演化和diagnostics：
`../local_runs/sod_kh_lab_frame_20260924_v1/`。新增独立campaign/analysis脚本，源码和配置
校验通过，绘图检查完成。相同时间快照按ID比较，未跨不同输出时间插值或外推。


## 105. 2026-09-24：Gresho boost10 图与当前 moving Yee 的 lab/co-moving 收敛对照

**作者：Codex；请求：Zhenyu希望用Gresho/Yee判断是否将thesis默认frame改为lab，
并核对KH质量漂移与edge flip、moving hierarchy的关系。此轮只做测试/图/记录。**

复用并核验§104/前序档案的4个gamma1.4不可变二进制、同一冻结源码及4个uniform门禁，
新跑16例Yee：N/Roe+mesh correction与LDA/P1-U Gauss3，分别lab/comoving，glass
48²/96²/192²，box10，gamma1.4，beta5，boost=(1,0)，t1，CFL.2，dt caps
1/256、1/512、1/1024；96²额外减半。最大4个并发单rank，OMP/BLAS均1线程。
实际步数全部符合cap，16/16完成，保存rho/p为正，无负质量/A2终止。只开关frame，
不加topology repair，不改变Arpaia/new-connectivity双sweep或N/LDA时间质量选项。

最终median-dual area=m/rho加权、在实际最终坐标上比较解析解：

| Scheme/frame | rho orders 48→96 / 96→192 | velocity orders |
|---|---|---|
| N lab | .8328 / .9023 | .8377 / .9176 |
| N comoving | .8329 / .9029 | .8377 / .9178 |
| LDA lab | 1.8395 / 1.7570 | 1.7526 / 1.3845 |
| LDA comoving | 1.8397 / 1.7596 | 1.7517 / 1.3934 |

所有配对解析误差变化：rho最大.194%，velocity最大.551%。96²减半dt的rho变化
不超过.194%、velocity不超过.608%。这是h/dt共同加密的观测阶，不是固定h时间阶；
尤其不能称所有变量均严格二阶。Yee总质量漂移随分辨率减小，但非roundoff守恒。

Gresho复用§103的boost10、t1、jitter48²数据，画去boost后的节点方位速度图及剖面。
lab/comoving vphi L1：N .0197645029/.0197644772，LDA .00792314439/.00792314433。
两frame宏观误差基本重合，N/LDA差异更大。§103中N/lab boost10 uniform pressure
1.1822e−12超过原绝对1e−12门槛的记录保留，不能把science完成写成所有门禁通过。
本轮Yee为boost1，不是boost10。Gresho与Yee的152个相关src/build文件hash完全相同。

KH归因核对：log2 §71的旧topology repair将相对质量漂移2.523e−3降至6.923e−6，
说明当时topology是主要来源；§73.5修正了剩余误差的简单归因。当前§78端点恒等式
含basis change与Arpaia divisor→actual endpoint两项，后者无flip时也可能非零。
未对当前1.2–1.4% KH漂移新做逐步分解。Moving hierarchy还存在§11的实际element
lifetime/timebin覆盖问题；受限N-only原型已存在，§35独立Euler prototype支持可行性，
但一般native topology/hierarchy及LDA/F1/MPI/restart仍未验证。

建议支持lab作为thesis reference、comoving作为可选conditioning优化；用户待审核后
确认。未改thesis、生产solver、默认Config，未commit/push。报告：
[当前Yee/Gresho frame图与收敛](RD_YEE_GRESHO_FRAME_FIGURES_20260924.md)。
档案：`../local_runs/yee_frame_convergence_20260924_v1/`，含16例输入/快照/日志、
源码/二进制provenance、分析JSON和PNG/PDF。新增run/analyze_yee_frame_convergence.py。


## 106. 2026-09-24：thesis采用lab-frame reference，comoving整段移入红字备选

**作者：Codex；请求：Zhenyu同意§105结论，要求把整个comoving部分标红并移至后面的
红字部分。明确授权修改本地thesis。**

4.2原Element-local co-moving conservative coordinates整段及全部公式/原label保留，
移入Alternative formulations (to delete)红色group。正文Scope改为laboratory frame，
RK2正文不再前引可选frame。4.3改用未变换的LDA residual与F1 RHS，明确保留mean
mesh-advection，直接积累lab ledger；原G变换/带prime公式/固定frame要求移入4.3红色
Alternative implementations。现有example Config实际仍启用frame，因此把该文件路径
和RD_ELEMENT_COMOVING_FRAME说明一起移到红字，正文只列lab reference的选项。
没有修改生产Config、solver或测试结果，也未把新实验图插入论文。

本地当前源为准，4.1和4.2.1逐字保留。全书XeLaTeX编译251页，零未定义引用/引用文献、
零重复label。保留所有旧label；新增两个红字primed implementation label。4.2单独
预览21页；完整PDF第186/187/192/196/199页渲染QA，程序验证红字颜色及全部原frame
理论公式保留。安装前128个tracked thesis文件hash核验，安装后其余文件保持不变。
仅交付chapter4.tex和master.pdf，旧文件备份在档案；未commit/push，未同步Overleaf。

档案：`../local_runs/chapter4_comoving_optional_20260924_v1/`，含原始hash/source、
changes.patch、编译记录、qa.json、页面PNG和chapter4_2_preview.pdf。
用户已确认论文的lab-frame reference；comoving仍是代码里的可选conditioning优化。


## 107. 2026-09-24：Yee384扩展与匹配static/moving对照（已完成）

**作者：Codex；请求：Zhenyu要求为Yee+boost收敛曲线增加更高resolution，并与static
mesh比较。沿用已确认lab frame、boost1、t1；此次不编辑thesis。**

档案 `../local_runs/yee_static_moving_384_20260924_v1/`，同§105冻结源，2个新static
二进制，复用已核验moving N/Roe与LDA/Gauss3二进制及6个48/96/192 science结果。
新跑2个static uniform、8个static science、2个moving384。相同SWIFT glass48周期
铺接1/2/4/8倍，384²为147456节点；helper逐项精确复现前三档IC后才生成384。
box10、gamma1.4、beta5、boost1、CFL.2、t1，dt cap1/256、1/512、1/1024、1/2048。
384 memory cap1024MiB，其它512MiB；最多4个singleton，OMP/BLAS均1线程。

运行中阶段记录：两个新static uniform gates通过；static48/96/192/384全部完成。192时moving/static
L1比值：N rho .86758、velocity .56265；LDA rho1.70917、velocity .78496。不能预设
moving在所有变量上更好。前三档初始节点/状态一致，static坐标/网格速度/面积核验通过。
Static384 rho/velocity L1：N 5.33660e−4/2.05251e−3，LDA1.85296e−5/6.02721e−5。
Static192→384 rho/velocity阶：N .975/.959，LDA1.470/1.628。
两个moving384仍在运行，尚无完整第四点比较或最终结论。moving显著慢于static，
已核验各约单核CPU、380MiB RSS正常推进；最初约两小时的总时长估计偏短。

运行入口 `tests/rd/run_yee_static_moving_convergence.py`，分析入口
`tests/rd/analyze_yee_static_moving_convergence.py`；逐例状态在档案runs/下，progress.py
和summary_partial.json只反映已完成或实际日志状态。保留所有断言/容差，不改变solver。

用户随后要求转后台并结束前台对话。交接时两个moving384约t=.45，停止的仅为前台
轮询；native driver PID14433及其children14437/14438继续运行。watcher PID14608
在全部完成后自动分析、验证、生成PNG/PDF及focused report。后续仍需视觉QA、最终
解释和本条/context收尾；不把尚未完成的moving384计作成功结果。

用户追问moving耗时：读取所有四例相同Step1024/t=.5的cpu.txt。累计计时N static/moving
1085.67/6519.64s，LDA1087.48/6509.29s，均约6倍。Moving voronoi占77.7–78.5%，
其insert子项占总计67.7–68.7%；RD占14.8–15.7%。LDA static/moving RD累计
810.80/963.03s，网格8.57/5111.52s。父子计时不可相加；这是并发运行下内置计时，
不是控制机器负载的性能benchmark。冻结run.c每moving步调用create_mesh，static保留
网格。两者均单rank、FORCE_EQUAL_TIMESTEPS、相同dt cap，故未启用MPI/hierarchy
不能解释配对约6倍差距。当前ALE equalstep在rd_ale_prepare_step明确拒绝NTask!=1，
并行化需要实现/验证，不能直接mpirun加核；hierarchy受全域dt cap约束，本收敛对照
不能假定有明显收益。原始同刻计时保存timing_at_t0p5.json。后台计算未改变。


**最终完成与复核（用户恢复high-res分析后）：** 全部12新run完成，含两个moving384，
并复用6个moving低分辨率controls。所有来源/IC/参数/步数核验通过，152个production
文件未改。两张图已视觉检查，summary.json、verification.json、report.md已生成。

384 rho/velocity L1：N static5.33660e−4/2.05251e−3，moving4.67114e−4/1.15948e−3；
LDA static1.85296e−5/6.02721e−5，moving2.88755e−5/6.87148e−5。
末段rho/velocity阶：N static.975/.959、moving.963/.954；LDA static1.470/1.628、
moving1.604/1.090。N moving误差降低12.47%/43.51%；LDA moving误差高55.83%/14.01%，
velocity在384已被static反超。不能宣称moving普遍更优或LDA所有变量已稳定二阶。
这是h/dt共同加密，不是纯时间阶；未新跑384半dt或comoving。

384 moving N/LDA质量相对漂移−6.065e−7/−2.870e−7，static约机器精度。
保存状态及日志predictor均正，无science failure。Element conservation最大绝对defect
N5.227e−16/LDA1.233e−15。LDA moving F1 fallback次数48/96/192/384为0/0/71/31898，
384约占corrector-element更新0.00528%；不能由次数推断其为速度降阶原因。
归因仍需固定h的dt敏感性及有针对性的消融，旧低分辨率frame结果不能替代384验证。
总耗时moving约2h53min、static约32min，配对比约5.4–5.5，属于并发运行计时。

报告：[Yee384四点static/moving对照](RD_YEE_STATIC_MOVING_384_20260924.md)。
两后台exec session已正常退出并回收，无待运行算例。本轮数值分析不再修改thesis。


## 108. 2026-09-24：Chapter 3伪逆说明与moving distribution精简

**作者：Codex；请求：Zhenyu明确授权在Chapter 3补充伪逆说明，精简4.2 distribution，
只编译Chapter 3与4.2局部预览。**

依据log1及regularize_matrix_debug_report.md §3：在停滞的Roe线性化系统中，LDA/N
右端属于range(S^-)，且K_i^+消去ker(S^-)。伪逆给出相容系统的精确解，节点residual
唯一，虽然中间解不唯一。新增段落说明旧S^-对角扰动破坏守恒恒等式，现解未扰动系统。
没有声称任意速度扰动都破坏守恒，也没有把此证明外推到任意Gauss contour右端。
Chapter 3的LDA守恒表述改为sum beta_i phi=phi，避免奇异时错误声称全空间sum beta=I。

4.2 distribution删除突兀的invertibility假设、重复midpoint/global-lumping/阶段解释，
保留全部公式和labels、N的mesh correction及N/lumped、LDA/F1的阶段式。LDA表述为
必须满足的element residual守恒条件，并引用现有4.3求解实现。4.3的spatial compatibility
和temporal fallback说明逐字保留。保留精简后的modified area positivity与时间阶限制。

只编译Chapter 3和Section 4.2，XeLaTeX通过，零未定义引用/文献、零重复label。
预览分别33页、20页；渲染检查修改页（combined PDF13/14/44/45）。原4.2.1已有
1.57pt overfull不在本轮编辑范围。外部引用复用上次完整编译的labels/citations，预览
页码为局部页码，公式/节编号不变。只安装两份TeX，其余126个tracked文件hash未变，
master.pdf未动，未commit/push/同步Overleaf。

档案：`../local_runs/chapter3_4_distribution_20260924_v1/`，含原文/hash、patch、
局部编译源/日志、qa.json、两份preview PDF和安装核验。用户自行通过原工作流同步。


## 109. 2026-09-24：Yee四点整体收敛拟合及结论措辞修正

**作者：Codex；用户纠正：收敛阶用全体点的log-log直线拟合，不能将某相邻区间
的斜率当作整体阶。单个分辨率点可能偏离趋势，需继续加密才可判断趋势是否持续；
本轮没有时间跑768²，只在讨论中列出可能机制。**

主图改为原始误差散点加每组一条幂律拟合线，四点等权OLS：log(E)=log(C)+p log(h)，
h=10/Nx。全部误差和static/moving ratios逐项与旧summary一致，没有选择性删点。
整体rho/velocity阶：N static.9720/.9279、moving.8995/.9044；LDA static1.6870/1.7738、
moving1.7358/1.4065。R²记录在summary fits和报告；相邻斜率移到附录仅作诊断。

修正§107先前过度强调末段的解释：不能凭192→384区间断言LDA持续降阶。
384同分辨率误差大小仍是有效观测，但不等于渐近阶判定。讨论保留空间/时间误差混合、
网格几何/regularization/拓扑变化、矩阵条件数/数值秩与少量F1 fallback等可能因素，
没有归因结论。用户明确不追加768²，本轮也未启动其它模拟或修改thesis。

脚本、主图PNG/PDF、summary/report/context已更新；拟合用独立中心化斜率公式核对，
图已视觉检查。旧产物保留在档案before_global_fit/。


## 110. 2026-09-24：boosted Yee的LDA密度profile与径向误差

**作者：Codex；用户要求解释boost下moving未必优于static，并直接画密度profile。**
只后处理§107的384²、t1、boost1、lab/Gauss3 LDA两例。147456原始节点直接绘制，
半径相对解析中心(6,5)，周期距离，不拟合中心/不重插值；bin0.05，先计算每节点
解析误差再按median-dual面积加权。完整域L1复现原summary，shell贡献和也核验。

密度profile几乎重合。Moving的核心r<1平均误差+2.251e−4，1<r<2为−7.993e−5，
有正负非轴对称散布；r<2贡献moving总rho L1的87.79%，static为63.14%。r<1 moving
MAE3.6826e−4/static1.0170e−4，r1–2为1.4630e−4/9.0239e−5；r2–3反而更小，
1.7307e−5/3.3935e−5，外围也总体更小。因此额外误差集中核心，非整个profile失真。

boost1与解析最大旋转速度.7958同量级；当前网格随局部流速+压力预测+规整运动，
不是只随boost刚性平移。减小bulk-advection误差不保证减小其它离散项的总和。
图支持空间定位，不证明具体误差源；保留几何/拓扑、时间项、条件数/F1等候选机制，
不判定持续降阶、不追加模拟或修改thesis。全四点拟合口径维持§109。

报告：[Yee密度profile](RD_YEE_DENSITY_PROFILES_20260924.md)。脚本
`tests/rd/plot_yee_density_profiles.py`及档案副本，density_profiles.json含快照hash和
全部统计，两张PNG/PDF已生成，PNG视觉检查通过。


## 111. 2026-09-24：Yee boost10静态/移动LDA对照（后台运行中）

**作者：Codex；用户要求提高vx并比较192²及以下，以区分bulk-advection优势与
可能的moving误差平台。** 本轮不改thesis/solver/default，不commit/push。

冻结复用§107两份LDA lab/Gauss3 mixed-F1静态/移动二进制，source SHA256
b2a915f657bfc46ae6cce1cc315ea3776fafb74e8cd3e8d08b6d7a43302dd9c6，核验当前152个
production文件hash。Boost1→10仅改IC vx，其它字段逐项不变。48/96/192²到t1，
四种mesh/boost组合统一dt cap1/1024,1/2048,1/4096；补跑匹配boost1 controls，
避免将旧4倍大dt对照当纯boost测试。四uniform gates和两192短pilot均通过。
最多四单线程solver workers，另48co-moving诊断临时增至五（已结束），符合local
6–8core预算；OMP和OpenBLAS均1，MaxMem512MiB。未追加384/768。

目前七science完成，一失败，四192继续。96² density L1 static boost1/10为
1.7031580e-4/1.8668099e-3；moving2.9420123e-4/2.9433091e-4。Boost增加static
10.9609倍，moving只增.04408%；boost10 moving/static rho=.157665,velocity=.0487785。
原始节点rho(r)和面积加权annular绝对误差图已绘制、视觉检查。Moving两个boost
径向曲线几乎重合。48/96 boost1减dt后density变化约1%，不能解释上述boost效应。

48movingboost10 lab在step243,t≈.237305触发A2 raw residual conservation：
defect4.8811713e-12>tol2.1550948e-12，roundoff_scale2.36955。之前rho/p predictor
正；保留失败，不放宽容差，不赋t1误差。此前一完整步SVD fallback6850/9216，
rank3/4=1249/5601，min pivot1.11e-21，F1 lumped476。不可据此唯一归因或称负密度。

随后仅补同48² boost10 co-moving诊断，核验Config唯一差RD_ELEMENT_COMOVING_FRAME，
source/IC/dt/容差一致。Uniform defect1.9873e-14，science1024步到t1，存盘及日志
predictor正。rho L1 .0010557291,velocity .0013091227,mass drift−1.4197e-5。
此诊断说明frame敏感性，不唯一确定失败矩阵步骤，也不替代lab曲线缺失点。

当前不能称error floor：旧boost1 rho随h一直降至384²。对boost不敏感不等于对h
不敏感；edge flip/geometry/time terms/reconstruction/quadrature/matrix/F1可列候选，
未作独立归因。仅完整三点系列做全范围log-log拟合，不从失败系列剩下两点宣称三点阶。

Archive `../local_runs/yee_boost10_static_moving_20260924_v2/`含README、progress.py、
全部provenance、scripts、partial summary和96图。Main session5902在所有运行结束后
会因原all-success断言非零退出（预期，不取消其它运行）；独立session94005 watcher
等待status_science.json并对成功/失败统一后处理。最后的图需人工视觉QA并更新记录。
诊断session13500已正常结束。Preparation-only v1也保留失败记录，无solver启动。

报告：[Yee boost10对照](RD_YEE_BOOST10_SENSITIVITY_20260924.md)。后续只需检查后台
完成状态、最终verification/report/plots与失败，不重跑既有目录。

**2026-09-25运行状态纠正与恢复（Codex）：** 用户问是否完成。13:59CST检查发现
四192日志最后更新均为前晚23:36，原parent/watcher/native进程均不存在，session5902
也已无效。确切中断原因不明，不声称solver失败。此前“后台仍持续运行”的保证不准确，
已向用户纠正。最后t：moving boost1/.10为.358154/.291504，static为.744385/.650635。
没有可用192 restart checkpoint，保留原日志及hash，未覆盖既有输出。

只将四192在新archive `../local_runs/yee_boost10_static_moving_20260925_recovery_v1/`
从原IC重跑，source/binary/IC/dt完全一致，仅OutputDir不同。已完成/明确失败案例
通过symlink只读复用；48lab失败继续保留。改用一次性macOS launchd任务，label
com.zhenyuwu.codex.yee-boost10-recovery-20260925-v1，非周期调度/无KeepAlive。
已验证parentPID30904/PPID1，四run日志推进；四workers且OMP/BLAS1。
新pipeline等四例结束后自动failure-aware分析，不再因既有48失败跳过分析。
最终结果/视觉QA仍待完成。旧watcher不再使用。无solver/default/thesis修改。

## 112. 2026-09-25：开启co-moving数值对照，保留thesis选择及A2容差

**作者：Codex；用户决定当前先开启co-moving，但不改thesis默认；询问是否守恒要求过严。**
核对A2代码：D=max|Phi−sum flux|，tol=4096 eps S，S含相消前|K+||x|与Phi构造尺度。
不是严格零误差，也不是固定绝对1e-12。48Yee失败D/S=2.05996e-12、允许9.09495e-13，
超阈2.264945倍。可能全流程roundoff尺度估计不足，但因4096安全因子及未知数值秩/
相容性，不能直接判定过严。现日志不含失败单元的完整矩阵/奇异值；之前aggregate
rank不能替代。Phi+B x=(Phi−Sminus x)+(Sminus+B)x可分解solve/range和split误差，
需将来针对性采集，不据小绝对数值宣称全局守恒已满足。Gresho同boost通过不保证
Yee局部矩阵同样数值性质。容差及production source未修改。

新增archive `../local_runs/yee_boost10_comoving_20260925_v1/`，moving两boost1/10及
三分辨率48/96/192全部co-moving，避免混合frame拟合。静态lab controls复用recovery，
已有lab恢复运行继续保留作对照。复用已完成48boost10 co-moving及uniform，补boost1
uniform、boost10短192pilot和五science。验证sole Config差为frameflag、同source及
152production hashes。MaxMem512MiB、OMP/BLAS1、最多额外2workers（总计最多6）。
一次性launchd label com.zhenyuwu.codex.yee-comoving-20260925-v1，启动日志正常，
uniform通过；pilot后检查再science。最终分析等待复用static也完成，图需视觉QA。

报告：[A2容差核对与co-moving运行选择](RD_YEE_A2_TOLERANCE_AUDIT_20260925.md)。
不改变默认Config、thesis或容差，不commit/push；lab失败记录保留。

## 113. 2026-09-25：停止本地测试，整理提交并准备COSMA接续

**作者：Codex；用户明确要求停止当前测试，清理代码并提交GitHub，详细记录待办。**
两launchd任务及六个active worker已SIGTERM，随后注销任务并用process list确认没有
solver/launcher存活。所有原始输出保留。四lab/static192恢复运行停止于t=.205811,
.165771,.706299,.704590；两个co-moving192停止于t=.0175781。新增co-moving48/96
其余三例尚未开始。每例termination_status.json及汇总明确user_stopped/not_started，
不是物理失败或成功终态；没有人为写run_status=0。原48lab A2失败仍独立保留。

[详细COSMA交接](RD_COSMA_YEE_HANDOFF_20260925.md)记录全部决定、结果、失败、中断与
七项顺序待办：重建/gates、匹配收敛组、lab复现、全点拟合/密度profile、独立diagnostics、
A2单元分解及后续误差机制消融。当前moving单rank限制必须明确，集群并行独立case。
不改thesis，不调A2容差，不启动COSMA jobs。

代码整理包括此前已验证但未提交的begin/end及restart处理、显式common-beta选项、
实验N/Gauss3 guard、配置和对应测试；标准mixed-stage行为不改。补充独立lab配置，
修正boost science中有失败就跳过全部后处理的driver问题，gate仍保持fail-closed。
增加portable `prepare_yee_boost_cosma.py`，校验8个原IC的tracked hash，重写目的地路径，
生成18primary或27含lab独立case及manifest/TSV，不负责提交。保存parameter template，
明确不能用polar Yee generator替代当前glass48 tiled家族。7.4MB输入包在local_runs/
cosma_handoff_20260925/yee_inputs，未加入Git，需另行rsync。

验证：152production文件hash与先前数值档案完全一致；make check_rd四脚本全部通过，
含compiled common-beta fixture；29份新增Python脚本语法通过；27case准备、3配置active
flags与归档binary一致；输入缺失/变化和重写已有目录均被拒绝；diff whitespace和shell
syntax通过。未重启任何hydro模拟。COSMA运行以及适配Slurm日志的完整分析仍待完成，
没有把Mac专用历史driver假装成portable。

当前未提交的图稿/绘图资产和Chapter3.7 scratch与运行迁移无关，保留原状不合入。
代码与交接文档分开提交；首次GitHub fetch超时，push状态以最终Git核验为准。

## 114. 2026-09-25：Chapter3奇异矩阵说明按用户思路简化

**作者：Codex；用户要求解释N/LDA求解Sminus*x=b，伪逆特解与零空间分量消去，随后
强调无需展开过多术语。** 仅替换本地chapter3既有singular-matrix段落，顺序为逆的
作用/线性系统→停滞时仍有解→伪逆给x0→x=x0+z、Sminus*z=0→Kplus*z=0→节点
residual不受不唯一性影响。未引入range/minimum-norm等新讨论，保留Roe停滞情形
这一必要适用范围。旧diagonal-perturbation说明保留；所有原scheme公式和label未改。

Chapter3局部XeLaTeX编译34页，无未定义引用/文献、无overfull，编辑页13–14已视觉
核对。仅安装chapter3.tex，其余tracked文件与原master.pdf均保持hash；Chapter4、
solver、COSMA任务未动。无commit/push/Overleaf同步。Archive：
`../local_runs/chapter3_singular_clarification_20260925_v1/`，含原文/hash、patch、编译/
局部PDF、渲染页及安装核验。外部章节引用复用已有labels；不是全书重新编译。

**§114文字顺序修订：** 用户要求保留原来语言风格，先讲fluid velocity=0及K矩阵很多
zero entries，接旧diagonal perturbation，再介绍当前pseudoinverse及零空间消去。
按该顺序仅重排/调整这段，保留Roe零速度情形限定。Chapter3局部重编译34页，
无未定义引用/overfull，页13–14视觉检查通过；只安装chapter3.tex，无同步/提交。
更新archive：`../local_runs/chapter3_singular_clarification_20260925_v2/`。

## 115. 2026-09-26：只读复核 thesis 4.2 数学及 Scope 精简建议

**作者：Codex；用户请求：再检查 moving mesh RD theory 是否有大问题，并判断删除4.2.3。**
以thesis main当前0f560a0的chapter4.tex为准，读取Chapter3及4.3相关定义，对照Arpaia2015
§4.4.2/4.5/6.1和Appendix。ALE变换、P1 mean-mesh contour、Roe mesh correction、二维
midpoint DGCL、O(dt³)时间乘积及两阶段modified-area推导未发现需要重构的代数错误。
200组独立三角形检查最大defect3.49e-16；不是native hydro验证或普遍二阶/正性证明。

必须补条件：4.2当前无条件sum LDA residual=target，秩亏伪逆实际上只给Sminus的range
投影；Chapter3对Roe RHS的说明不能直接外推到Gauss contour。独立正状态三角形反例
rho=p=1、速度(1,0)/(0,1)/(-1,-1)、gamma1.4，Roe速度0、H25/6、rank3，G3 exact
contour=(-1,0,.1,-257/60)，左零向量与target乘积−7/60，明确不相容。4.3已解释空间
assertion及F1 temporal lumping，建议4.2补相容条件并交叉引用，不必再展开伪逆。
不将此反例当作此前Yee A2失败的机制归因。

另需修正4.2引言：Arpaia2015§6明确包含完整理想气体Euler，不是只有scalar/simplified
Euler；geometric source应说吸收到modified dual-area coefficient。Scope无新推导且
其label没有其它.tex引用，可以删去独立4.2.3，将必要固定连接/守恒边界衔接留在4.2.2
末尾，lab/equalstep/MPI范围并入4.3。4.3的endpoint/topology conservation说明仍须保留。

报告：[4.2数学复核](RD_THESIS_42_MATH_REVIEW_20260926.md)；档案
`../local_runs/chapter4_2_math_review_20260926_v1/`。未改/编译thesis，源码hash保持；
未运行hydro、未改solver、未commit/push。结论是可以开始4.3，4.2定稿前补上述条件和事实。

## 116. 2026-09-26：Roe/Gauss伪逆比较、Arpaia第6节细查及一处授权措辞修改

**作者：Codex；用户要求比较奇异时两种residual，明确Arpaia的标量推导/Euler推广区别，
并授权只把geometric source句中的median dual cell改为modified dual-area coefficient。**

同矩阵下LDA节点和为P*Phi，P=Sminus*Sminus_dagger。纯特征Roe RHS在所述停滞情形
相容，而独立Gauss RHS不必相容；投影Gauss不等于改回Roe。前轮单元的Roe target
(-1,0,1/14,-25/6)经伪逆sum误差8.88e-16，G3 target(-1,0,.1,-257/60)的sum误差.0264750。
重要补充：实际moving Roe含C=-int sigma grad(U-Uhat)，C不能自动继承相容性。给前例
加共同boost/mesh speed(0,1)，C=(0,0,0,-1/14)；把完整Roe target送入LDA产生.0169579
defect，N在伪逆特征分配后直接加C/3则闭合至1.05e-15。故不能说所有moving Roe均相容。
全为独立单元代数，不是native试验或Yee失败归因；生产代码仅阅读。

用户关于“主要推导使用标量方程”的澄清准确。Arpaia§6.1只是简述矩阵/特征分解推广，
并把细节引向旧文献；但§6.2确实解完整Euler，包括二维Riemann与Mach3移动壁面。
其§3.3.1允许contour或exact mean-Jacobian，不可无依据断言“他们只Roe、我们才Gauss”。
§6未展开我们的U/Z/Uhat mesh correction、G3规则或伪逆相容性/F1 fallback，且网格为
固定连接的给定连续变形，不覆盖AREPO重连。区别是推导详细程度和具体构造，不是PDE
是否完整。§115前轮解释在此细化。

只安装chapter4.tex第454行的一处短语替换；其余128个tracked/snapshotted文件和PDF
hash均未变。未编译（一处普通文字替换、公式/label/TeX命令不变），未commit/push/sync。
报告：[伪逆与Arpaia第6节详查](RD_THESIS_42_ARPAIA_SINGULAR_FOLLOWUP_20260926.md)。
档案：`../local_runs/chapter4_2_followup_20260926_v1/`，含patch、hash及独立数值对照。

## 117. 2026-09-26：零速度时Roe/Gauss显式推导及Arpaia积分含义澄清

**作者：Codex；用户要求详细展开v=0时两种residual及伪逆效果，并追问Arpaia是否
直接精确积分Euler Jacobian而不作线性化。** 本轮仅讨论与独立代数核对，未改thesis。

确认两种residual的差异先于矩阵求逆：当前Gauss对应P1-U非线性边界通量，守恒Roe
对应P1-Z的精确通量积分；二者重构不同。静止网格、Roe平均v=0时，显式Sminus秩3，
右零向量e_rho、左零向量(-H,0,0,1)，相容条件Phi_E=H*Phi_rho。报告给出K、Sminus、
伪逆解和每节点分配公式。标准数值坐标中，伪逆将不相容Gauss的质量/能量分量一起
投影，动量不变；并非变回Roe。变量缩放会改变不相容RHS的最小二乘投影。

关键限定：若每个节点v_i=0且网格静止，则Roe/Gauss的质量及能量residual均为零，
二者都相容，伪逆不丢失总residual。压力residual仍可因P1-U/P1-Z而不同：直角单位
三角形rho=(1,4,9)、p=1、gamma1.4，Gauss=0而Roe=(0,-7/36,-1/18,0)。此前反例
只有Roe平均速度为零，不能描述为所有节点速度均为零。moving时须改为相对速度
及单独处理混合重构修正C；不将静止结论无条件外推。

Arpaia2015§3.3.1给出contour与exact mean-Jacobian两种路径；§6.1未指定Euler的
体积分/边界求积规则，故不能说他实际计算精确Euler平均Jacobian且不作线性化。
进一步查其[14] Ricchiuto–Abgrall2010作者公开稿§5.1式(52)，明确上风矩阵取节点
守恒量算术平均状态的Jacobian，这不是P1-U的真实单元平均Jacobian；不能反向推定
2015具体实现。应区分非线性总residual计算和局部特征矩阵构造。

报告：[零速度显式推导](RD_THESIS_42_ZERO_VELOCITY_DERIVATION_20260926.md)。档案
`../local_runs/chapter4_2_zero_velocity_20260926_v1/`。三组独立单元检查通过，包含
Sminus/projector/每节点分配/N闭合以及Roe与P1-Z contour一致性；后者最大误差
8.89e-16。初次脚本最终wrapper遇Python list/abs类型错误，修正后通过，未改公式。
无hydro运行、无solver/thesis编辑、无编译/commit/sync；chapter4 hash仍为b3d3e720…f64b。

## 118. 2026-09-26：Chapter 4收尾结构讨论，implementation精简及三组测试

**作者：Codex；用户倾向维持4.2现有表述，将contour residual进一步测试放future work，
下一步简述implementation，展示Yee+boost收敛、Gresho+boost、Sod后结束本章。**
尊重本轮写作范围，不继续改写4.2，也不删除4.2.3或编辑4.3；此前数学/文献核对保留
为记录，用户的组织选择不自动消除已识别的适用条件。

阅读现有4.3和log3§103–113后，建议保留4.3 implementation and results标题，将现有
五个实现小节压成一个约1–2页overview，再依次设Yee、Gresho、Sod三个结果小节，
最后短summary/outlook。正文只留状态/面积关系、一次重建后的midpoint与两阶段更新、
实际scheme/residual/frame及运行范围；函数名、编译宏、临时存储和长诊断推导移出正文。
测试设置可共用一表，保留影响结果解释的奇异处理、拓扑/端点守恒限制简述。

三测试分工：Yee检验光滑精度与boost敏感性，用所有有效分辨率点整体log-log拟合；
Gresho展示涡旋保持及boost前后去平移的vphi剖面；Sod展示激波/接触与振荡，报告节点
散布，不能用平滑均值掩盖undershoot。若测试采用Gauss，应在implementation中明示，
系统Roe/Gauss比较及奇异时稳健性留future work。无需增加新的测试家族。

本地记录已有完整boost1 Yee四点拟合和当前Gresho/Sod对照；匹配boost1/10后续系列在
§113被用户停止并交接COSMA，不能把中断输出当收敛终点，也未在本轮读取远端进展。
最终曲线须使用同配置、同结束时间的完整结果，不混用lab/comoving及历史repair版本。
无新模拟、无thesis/solver编辑、无commit/sync。本条是结构建议与用户偏好记录。

## 119. 2026-09-26：4.3三小节结构确定，Implementation overview草稿取舍

**作者：Codex；用户指定4.3.1 Implementation overview、4.3.2 Numerical tests、
4.3.3 Ongoing work，后者简述hierarchical timesteps中的edge flip问题；本轮要求
查看已有草稿并建议哪些内容保留。** 阅读chapter4.tex现有4.3全部正式草稿，以及
4.1存储说明、4.2 midpoint/distribution和草稿末尾hierarchical flip讨论；未编辑thesis。

建议核心保留现有State storage与One mesh rebuild两部分，压缩数据字段/函数/宏/临时
ledger细节。沿用既有median dual area与modified dual-area coefficient符号，说明端点
Q=|S|U与RK更新权重的区别，不再为实现单独增加m_i/D_i符号体系。保留新Delaunay
connectivity下回算old/midpoint坐标，以及一次重建后用同一midpoint几何作两阶段更新。
可引用4.1流程图，最多保留存储关系及坐标回算两组公式。

LDA solves与F1部分压成方法选择和必要求解说明；概述须覆盖后面测试实际使用的
N/Roe+lumped与LDA/Gauss3+F1，不能把所有测试统称LDA/F1。Gauss correction的实现
拆分、重复的LDA/F1公式及因子分解细节可移出正文；保留简短伪逆、F1 temporal
lumping及空间分配检查说明。运行范围和实际timestep选择简述，具体参数归4.3.2。

Connectivity/endpoint长推导不放overview，但其当前守恒限制不能被完全删掉或说成
仅hierarchy存在：概述末尾留一句，必要解释归4.3.3。后者重点讲coarse interval内
edge flip可令旧三角形在RK闭合前消失，新三角形缺少对应阶段历史，已有静态hierarchy
规则不能直接照搬；共同端点的flip与coarse interval内部的flip要区分。既有示意图
可选保留，完整pending-history/repair算法列表无需进入精简正文。

建议4.3.1写成约五段连续文字（约1–1.5页）：承接静态实现与范围→面积/状态→网格
与两阶段流程→实际residual/distribution选择及求解→检查和局限衔接。不增新测试或
数学证明，不修改4.2、不安装结构调整、不编译、不commit/sync。

## 120. 2026-09-26：按授权删除4.2末尾红字alternative formulations

**作者：Codex；用户明确要求先删除4.2.2红字部分。** 定位到现有4.2末尾唯一的
红字Alternative formulations (to delete)块，删除原chapter4.tex第920–1453行（含
配对begingroup/endgroup，534行、29个label）。保留4.2黑字推导及Scope subsection；
4.3正文与红字Alternative implementations保留，仅把其中一处指向已删除co-moving
理论段的hyperref及“retained among the alternative formulations”改为独立描述，
避免失效链接与失实位置指引。未执行前轮讨论中的4.3结构重写。

删除前全文、被删块、patch与核验归档于
`../local_runs/chapter4_2_remove_red_20260926_v1/`。TeX环境配对及删除label的跨文件
引用检查通过；本轮diff whitespace检查通过。相对HEAD的既有第454行尾空格仍保留。
128个其它tracked/snapshotted文件（含master.pdf）hash未变。未编译、commit或同步。

## 121. 2026-09-26：整合4.3.1并保留红字详细草稿，生成PDF预览

**作者：Codex；用户授权整合4.3.1 Implementation overview，将移出部分放入4.3红字
区，并先查看PDF。** 以用户已提交的thesis e4fcd84为起点，新增约450词、五段正文，
保留两组公式：Q=median area*U及新连接关系下old/midpoint坐标回算。正文简述共同
时间步/二维单rank范围、一次mesh rebuild后的两阶段更新、N/Roe+lumped与LDA/Gauss3
+F1、伪逆/F1 lumping和几何/守恒限制。沿用modified dual-area coefficient措辞。

原4.3开头及五个实现小节完整移入红字Implementation details retained for revision，
小节改为不编号标题；原Alternative implementations同样保留。所有原label和文字均
核对保留，红字仅调整标题/换行/图文排版。4.1/4.2逐字未变，未恢复上一轮删除的4.2
红字；未编写4.3.2结果或4.3.3 Ongoing work。只安装chapter4.tex，其余128个原文件
（含master.pdf）hash未变，无commit/push/sync。

使用LaTeX compile与PDF技能，在隔离副本XeLaTeX编译Chapter4并抽取4.3预览，共13页：
第1–2页为新overview，第3–13页为红字留存。引用其它章节时复用已有aux，编号为局部
Chapter4构建；不是全书重编译。无未定义引用、无重复label、4.3零overfull；此前4.1/
4.2的既有overfull不在交付PDF范围。所有预览页已视觉检查，修正长代码名换行、图与
caption跨页及段落首行孤行。一次排版helper因已有另一samepage环境触发断言，未写入，
改为目标段定位后通过；不涉及数学修改。

档案：`../local_runs/chapter4_3_1_overview_20260926_v1/`，含原文/hash、完整移出文字、
patch、编译副本/日志、QA与安装核验。PDF：`output/pdf/chapter4_3_preview.pdf`。

## 122. 2026-09-27：equal-timestep edge flip与新dual area的实际代码路径核对

**作者：Codex；用户指出4.3.1缺少connectivity change/edge flip说明，要求确认代码
是否修正，以及此前“换成新的S”的含义。** 只读检查本地94cd37a，相关source无未提交
修改。main/run.c:344重建mesh后在:366调用rd_step_end；solver:3702开头hook只记时间，
:3736在新connectivity上计算两遍residual，没有旧三角形的半步状态需要跨flip保留。

主路径确实实施保持节点U的面积权重转换：solver:2513–2521用保留的旧实际DualArea
恢复Uold=Qold/Sold；:2554及geometry.c:36–59用新三角形节点回算old/mid/new几何；
:2629累积实际新端点Snew，:2636累积modified coefficient D，默认D每元素贡献
[A_mid+(A_new-A_old)/2]/3，A_old属于新连接的回算几何。:2678–2679同时令临时Q=D*Uold、
DualArea=D；两阶段完成后:2705–2711取Unew=Qbar_new/D，写回Qnew=Snew*Unew及DualArea=Snew。
因此不是只替换分母而保持原Q不变；保留的是节点状态，而新P1插值基与积分权重改变。
当前Arpaia选择的RK除数D也不能简单写成实际Snew；Campoli选项才在prepare直接用Snew。

源码另有RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC保护的rd_ale_apply_topology_repair
(:2175–2449)，按changed-patch defect修正节点状态，并在prepare重标定前调用。
它是实际可选修正代码，并非只有设想，但当前论文/Yee参考配置及核对的Gresho/Sod
编译header未启用。该patch transfer只针对actual old basis到pulled-back new basis，
不自动消除后续Arpaia divisor到endpoint权重转换的另一项误差。finish对非均匀场记录
endpoint总量漂移，严格终止检查只应用于uniform case（:2727–2738）。

结论：应在overview明确“继承节点U、按新连接重算权重、同步重标定Q”；这已实现，
与独立的严格守恒修正是两件事。单纯在同一时刻换基产生sum(Snew-Sold)*Uold，通常
非零，所以不能把已有新S处理说成无条件守恒remap。现有overview最后一句应理解为
参考配置未应用该守恒修正，而非源码里不存在修正实现。

档案`../local_runs/chapter4_3_connectivity_audit_20260927_v1/audit.json`记录source与
配置/hash及thesis hash。本轮未运行hydro、未改代码/thesis/PDF、未commit或同步。

## 123. 2026-09-27：4.3.1以三句话补充equal-step edge flip处理

**作者：Codex；用户授权用两三句话提及上一轮核对的connectivity处理。** 将overview
末尾原守恒限制说明扩为三句：继承用旧dual area恢复的节点状态，在新triangulation
重算modified dual-area coefficient及endpoint area；按这些权重重标定extensive量，
两个RK阶段均使用新connectivity；非均匀场的connectivity/endpoint转换守恒误差在
参考配置中未作conservative correction。避免原“remains ongoing work”被理解为源码
没有可选修正，也未将基线重标定称为严格守恒remap。

只改本地chapter4.tex的4.3.1末段；前文、4.2及4.3红字草稿逐字未变。备份、独立patch
和hash核验保存在`../local_runs/chapter4_3_1_edgeflip_note_20260927_v1/`。
本轮仅纯文本编辑及diff核验，未重新编译PDF、未运行hydro、未commit/push/sync。

## 124. 2026-09-27：4.3.1加入RK前后两组面积转换公式

**作者：Codex；用户要求写入此前解释中第2、3步的公式，分别明确RK更新前转换与
收到RK更新后的转换。** 以用户已提交的thesis cb6beb3为起点，只扩展overview存储段：
先Uold=Qold/Sold、Qbar_base=Sbar*Uold；两个RK阶段把Qbar_base更新为Qbar_new后，
再Unew=Qbar_new/Sbar、Qnew=Snew*Unew。使用既有modified dual-area coefficient
符号，不引入新的D_i记号，并定义Qbar为使用modified coefficient表示的extensive量。
上一轮edge-flip说明、其余4.3及红字草稿、4.1/4.2均未变。

隔离副本XeLaTeX编译成功；新增公式在预览中编号4.47、4.48。交付的2页overview PDF
已逐页视觉检查，无公式溢出/遮挡、未定义引用或重复label。Chapter4其它部分原有的
overfull提示不在交付范围。首次提取调用系统Python缺少pypdf，改用已配置的bundled
Python后成功，无安装依赖。tracked hash及git diff --check确认仅chapter4.tex修改。

档案`../local_runs/chapter4_3_1_area_conversions_20260927_v1/`含原文、hash、独立patch、
编译副本及QA。PDF为`output/pdf/implementation_overview.pdf`；不是全书重新编译，
本地master.pdf未覆盖。未运行hydro、未commit/push/sync。

## 125. 2026-09-27：解决thesis main推送被远端Overleaf更新拒绝

**作者：Codex；用户报告git push因fetch first失败，按其同步意图完成整合和重推。**
本地main为用户提交e9ba5c7（4.3.1两组转换公式），tracked工作区干净。fetch后远端为
9cf7a6a，含Overleaf提交c91056b及其merge；净改动只有master.tex中SK批注颜色orange
改red、abstract.tex增加SK评语，与本地chapter4.tex无路径重叠。

先保存HEAD、文件hash与Chapter4副本，执行无冲突merge并在提交前检查暂存区只含
两项远端修改；逐文件核验它们与origin一致，Chapter4及30个未跟踪文件hash未变。
创建merge commit 6af0539（按项目约定标注Zhenyu Wu与Codex GPT-6），保留双方原始
提交历史；普通push成功，远端main与本地HEAD一致，无force push或rebase。
tracked工作区干净，原有未跟踪编译文件/配置未加入提交。未修改论文内容或编译PDF。

档案：`../local_runs/thesis_push_reconcile_20260927_v1/`，含原始状态、hash及核验记录。

## 126. 2026-09-27：保存本地AREPO工作，登记COSMA结果，准备回到Mac实验

**作者：Codex；用户要求commit本地AREPO，合并GitHub上的COSMA Yee+boost工作，
并说明后续暂时不用COSMA，回到本地实验。** 已将全部44项既有本地改动保存为
`e3ec73b`：log3至§125、4.2数学核对报告、旧main-loop/MPI/hierarchy图件与诊断工具。
无production source/Config更改；保存前后的44文件逐一hash一致。Python语法与XML
解析通过；初次完整diff whitespace检查报告生成SVG的原有行尾空格，保留图件原始
字节；排除SVG后的diff whitespace检查通过。未运行hydro或重绘图件。

实际远端状态与用户预期不同：两次fetch及GitHub全部branch head查询中，
`origin/develop_pureC_RD`仍是`94cd37a`，未找到Sep25之后的COSMA提交。只读SSH尝试
因keyboard-interactive认证失败，未进入COSMA。已向用户询问正确仓库/分支/提交号，
或在尚未push时先完成COSMA推送；未将本地旧source冒称为合并后的COSMA源码。
本次未push本地分支，COSMA源码与日志的Git合并仍待该信息。

用户scp的`../cosma_runs/yee_n_boost10_20260926/comparison_latest/`共19文件原地保留。
8项文件hash检查通过；comparison.json中16个science case均记为t1完整、boost(10,0)、
一rank、Nx48/96/192/384、N与LDA、static lab与moving comoving。按记录误差值独立
复算8组四点mass-weighted收敛阶，全部相符。这只验证复制与summary内部一致性，
不等于重检native结果；当前副本没有raw HDF5、binary、Configs或job/gate logs，报告
中的12个gate结论保留其原始来源归属。

新增[文件清单](COSMA_RESULT_IMPORT_20260927.json)与
[回到本地的交接记录](RD_LOCAL_RESUME_COSMA_IMPORT_20260927.md)，更新local/COSMA
context：后续用LocalMac/Homebrew/OpenBLAS、OMP与BLAS线程均1、独立build/run档案；
此前中止的Mac案例不自动重启。本轮无新实验、无Linux binary移植、无thesis改动。
Git整合档案位于`../local_runs/arepo_cosma_reconcile_20260927_v1/`。
