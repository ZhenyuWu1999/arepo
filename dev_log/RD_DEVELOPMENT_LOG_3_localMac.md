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
| 165 | Rusanov/Sedov literature provenance and LDA blending choices |
| 166 | Staggered Lagrangian RD versus the current moving ALE mesh |
| 167 | Conservative positive LDA/F1 + common-Gauss Rusanov prototype |
| 168 | Sedov angular scatter audit, separated from radial shock broadening |
| 169 | Proposed entropy and local oscillation constraints; not implemented |
| 170 | Classical RD B/Bmax experiment, complete RK correction and native tests |
| 171 | Consolidated LDA/Rusanov development record, results and remaining limits |
| 172 | Local thesis 4.3.3 Ongoing work draft and two-page review PDF |
| 173 | Explain conservation defects through the P1 basis change and label repair experimental |

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

## 127. 2026-09-27：4.3.2加入两张Yee图，核对Gresho boost图的可用性

**作者：Codex；用户确认COSMA尚未commit、暂缓整合，转而要求将两张Yee图放入4.3.2，
并准备Gresho boost0/3/10图、查看本地boost结果。** 更新交接记录为用户明确deferred，
未继续fetch/SSH或改动Git提交。论文新增Numerical tests与Yee subsubsection，复制原始
vector PDF为chapter4/figures/yee_boost10_convergence.pdf及yee_boost10_profiles.pdf。
两份复制与已验证COSMA figure hashes相同；正文/图注明确boost(10,0)、t1、N48/96/192/384、
匹配dt1/1024至1/8192、最终mass权重、四点log-log拟合，以及static lab/moving comoving
选择。图中低误差与拟合阶分别描述，不声称严格Galilean不变性或理论阶。4.3.1及此前
正文、所有红字留存逐字不变；Gresho后续插图位置仅留source comments。

隔离副本XeLaTeX成功，导出4.3.2三页预览，图号4.6/4.7；逐页检查文字、图例和caption，
无裁切/重叠、未定义引用/重复label或本节overfull。旧4.1/4.2警告在交付范围之外。
只改chapter4.tex并新增两份PDF，其它原tracked文件hash不变；无commit/push或主PDF覆盖。
档案`../local_runs/chapter4_3_2_yee_figures_20260927_v1/`，预览
`output/pdf/numerical_tests_yee.pdf`。

本地当前Gresho有moving N/Roe、LDA/Gauss3，lab/comoving、boost0/10共8个t1结果；
逐一打开终点HDF5确认2304节点，各4096步；153个生产/构建文件hash与当前本地一致。
已查看现有boost叠加剖面与boost10节点图：LDA峰.9391，N在b0/b10分别.8524/.8590，
解析峰1。boost3只有历史不同配置的图，不能直接拼接当前结果；当前matched static
controls也不齐。若只moving需补两个b3；若static/moving还需六个匹配static control。
尚未启动新模拟。详细[图件准备记录](RD_GRESHO_THESIS_FIGURE_READINESS_20260927.md)。

## 128. 2026-09-27：glass48、boost10、lab-only Gresho static/moving对照完成

**作者：Codex；用户将Gresho改为glass IC、只要lab frame，并要求先做boost10，视结果
决定是否省略boost3。** 从本地2858d43及当前工作树冻结source，独立构建N/Roe+lumped、
LDA/Gauss3+mixed-F1的static/moving四套Mac程序。无production/default Config修改；
一rank，OMP与OpenBLAS均1，最多四个独立案例并行。保留source tar、hash、Config/
header、binary/linkage、参数、所有native日志与快照。未恢复旧中止campaign、未访问COSMA。

采用既有SWIFT glass48的2304点，unit box、gamma5/3、boost(10,0)，一个稍超周期边界
的坐标分量mod1后再计算解析IC；四组t0快照按ID逐位相同。全部lab，moving保留现有
Arpaia权重、mesh regularization及谱CFL限制，无topology repair。四组t1均4096等步
（dt1/4096），存t0/.5/1三个快照。四个uniform控制及四个Gresho短程pilot均到.03125；
uniform最大状态差分别2.043e-13/3.331e-13/1.874e-13/2.363e-13，均通过原1e-12门槛。
四个science全部正常结束，已存快照状态有限且rho/p为正，无native断言失败。12案例
现已全部结束，boost0/3未启动。

t1最终mass加权vphi L1：N static .2399602、moving .01890833；LDA static .1635014、
moving .00717532。moving/static为.07880/.04389，约改善12.7/22.8倍；moving峰值
.85338/.95336。static N强扩散，static LDA剖面明显散开、含负vphi；不能仅看峰值评价。
moving总质量相对漂移+3.70739e-5/+4.13801e-5，总能量+2.71762e-5/+2.48148e-5；
static为roundoff。此例没有给topology与endpoint权重误差单独归因，也未验证严格
Galilean不变性或收敛阶。用于简要展示强boost下moving/static差异，可先省boost3。

完成lab-only两panel的N/LDA剖面PDF/PNG，扣除已知解析平移及速度boost，使用全部
原生点，不拟合中心/插值/binning。PDF渲染视觉检查通过；初稿裁掉33个static LDA负尾
点，最终已扩展坐标范围完整显示。gate报告最初对舍入Time作差得到伪dt范围，后改报
Systemstep；只修分析元数据，无重新积分或参数修改。冻结runner保留，修订gate检查
helper另存。论文尚未加入新Gresho图、无commit/push。

详见[结果及限制](RD_GRESHO_GLASS_BOOST10_LAB_20260927.md)。档案
`../local_runs/gresho_glass_boost10_lab_20260927_v1/`；最终PDF为
`output/pdf/gresho_glass_boost10_lab_static_moving.pdf`。

## 129. 2026-09-27：补N的static/moving boost0，区分网格优势与Galilean invariance

**作者：Codex；用户怀疑moving N boost10比static N boost0还好，要求补static0并询问
这是否还能说明Galilean invariance。** 同时补moving0以直接分离mesh与boost因素。
复用§128冻结且hash核验相同的两套N binary/header/Config，不重编译或改solver。
相同glass48、gamma5/3、lab、t1、4096等步、dt1/4096；新IC仅把原boost10的vx减10，
其他dataset逐位相同。各自uniform、pilot、science共6个新案例全部完成；uniform最大
缺陷1.60e-14/7.99e-15通过原1e-12标准；所有已存状态有限且rho/p正，无native断言失败。
两worker、一rank、OMP/BLAS各1。152个production/build文件hash未变。

最终mass加权vphi L1：static0 .05809649，moving0 .01888672；复用static10 .23996020、
moving10 .01890833。moving10/static0=.32546，约低3.07倍，确认用户观察；moving10/
moving0=1.001144，误差指标仅相差.1144%。static0峰.66347，moving0/10峰.85168/.85338。
moving0总质量漂移+3.9302e-5，仍不严格全局守恒。

解释：boost0仍有局部旋转穿越static网格；moving去掉常数boost后网格仍跟随旋转，
并未变成static0。代码K特征速度包含(u-sigma).n，实际sigma还含压力预测/regularization。
因此moving10好于static0与Galilean invariance不矛盾。符合boost试验定义的比较是
moving0/10；另核对Springel2010 §3.4/§8.5，不把FV证明套用到当前RD。

仍不能宣称严格invariance：t1去boost按ID匹配的velocity-vector L1差.00238766，
坐标RMS差.00238050，最大坐标差.0388953；这属于联合mesh/state covariance检查，
不是相同空间点的Eulerian场误差。短程.03125已经有最大速度差9.0841e-5、坐标差
1.4501e-6。本轮没有将差异归因到某一种residual/矩阵/flip机制，也未称全是roundoff。
适合写“moving N对bulk boost很不敏感”；.1144%是误差指标之差，不是逐点解之差。

新两panel PDF/PNG：static与moving分别叠加boost0/10，只lab，全部原生节点。
PDF已渲染及视觉检查，点未裁切、图例可读。详见
[控制实验及解释](RD_GRESHO_N_BOOST0_CONTROLS_20260927.md)。档案
`../local_runs/gresho_n_glass_boost0_controls_20260927_v1/`，含复用provenance、全部raw
输出、gates、summary及图件。没有LDA0/boost3、thesis修改、commit/push或COSMA操作。

## 130. 2026-09-27：完成boost3、t3的glass N/LDA static/moving对比图

**作者：Codex；用户明确要求新增boost vel=3、t=3，LDA和N的moving/static对照。**
沿用glass48（2304点）、lab、gamma5/3及§128四套冻结binary，各自复制独立artifact与
输入/运行目录；程序hash完全相同，无重编译、production/default Config更改。新IC只
把boost10输入的vx减7，其他dataset逐位相同。四个uniform及四个pilot均到.046875，
各256步；uniform最大差2.653e-15/1.039e-13/1.860e-15/3.461e-15，全过原1e-12门槛。

四个science均正常完成t3，无native断言失败，全部20个已存science快照状态有限、
rho/p/mass正。完整时间步序列相同，均16384步：原cap1/4096在TimeMax3的integer
timebase下向下量化为实际dt3/16384。不能误写12288步或实际dt1/4096。存0/.75/1.5/
2.25/3共5个快照；四组t0坐标及原始物理字段按ID逐位相同，static坐标始终固定。
本地最多4worker、一rank/例、OMP/BLAS各1；全部12案例结束，无活动solver。

t3质量加权vphi L1：N static .23991685、moving .04720931；LDA static .22266181、
moving .01260077。moving/static=.196774/.056592，约改善5.08/17.67倍。N static/
moving峰.13646/.72920；LDA static/moving峰.89870/.90243，但static LDA散点畸变明显、
最低vphi−.69283，不能只看峰值。moving质量相对漂移+1.42443e-4/+1.77547e-4，能量
−7.6013e-5/−1.31865e-4；static守恒为roundoff。没有将此前boost10/t1与此boost3/t3
混作相同时间的Galilean invariance验证。

已有analyzer改为从campaign读取boost/end/output times并核验完整dt histories；新
通用runner支持复用冻结四套binary。旧档案/图片/scripts未改。最终两panel PDF/PNG
显示全部原生点，扣已知boost、无拟合中心/插值/binning；保留负尾，图例移到坐标轴外
避免遮点，PDF已渲染与视觉核查。配置/输入/参数/hash检查通过。无thesis修改或commit/
push/COSMA操作。报告[boost3/t3结果](RD_GRESHO_GLASS_BOOST3_T3_LAB_20260927.md)，
档案`../local_runs/gresho_glass_boost3_t3_lab_20260927_v1/`，PDF为
`output/pdf/gresho_glass_boost3_t3_lab_static_moving.pdf`。

## 131. 2026-09-27：glass48、t3的moving N/LDA boost0/10单独预览

**作者：Codex；用户选择glass48、t3、boost0/10的moving LDA/N，并明确“先单独预览”。**
保持lab frame，用§128冻结binary新跑4个science（N/LDA×boost0/10）及各自uniform/
pilot，共12个native案例。两个boost子目录独立保存输入、Config/header、binary与
source/build/linkage provenance；同一scheme的两boost程序hash一致。runner新增
method选择，不额外启动static。初始输入只改vx整体boost，其他dataset逐位相同。

四个uniform和四个pilot均到.046875并过原门槛；四个science全到t3，无native断言
失败，20个science快照有限且rho/p/mass正。四组完整时间步序列相同，16384步、
dt3/16384；存0/.75/1.5/2.25/3。相同boost下N/LDA初始快照逐位相同；跨boost坐标、
ID和mass完全相同，扣boost速度差至多1.78e-15、pressure2.13e-14。152个production/
build hash未改，OMP/BLAS1、一rank/例、最多四worker，现已全部结束。

最终mass加权vphi L1：N boost0 .04724472、boost10 .04707784；LDA .01252980/.01249125。
boost10/0为.996468/.996924，误差指标相对差.3532%/.3076%；两boost径向剖面接近
重合。N峰.73544/.74164，LDA峰.89759/.89396。moving质量漂移N +1.519e-4/+1.592e-4，
LDA +1.769e-4/+1.710e-4，仍不是严格全局守恒。

不把误差指标接近解释为完整解严格Galilean不变：t3按ID扣boost后的坐标RMS差为
N .0472334、LDA .00957318；速度vector L1差.0448393/.0104613。由于节点位置已不同，
这是联合mesh/state covariance诊断，不是相同空间点的Eulerian场误差。此轮未隔离
机制，也不把差别全称为roundoff。只支持本测试中径向剖面/误差对bulk boost敏感度小。

生成N/LDA两panel、每panel叠加boost0/10及解析曲线的单独PDF/PNG，使用全部原生点，
不拟合中心或插值/binning，图例置于轴外。最终PDF渲染视觉检查通过；一次分析未结束
时提前查看render路径失败，待完成后正常检查，不涉及hydro失败或重跑。按用户要求
未修改论文。报告[boost0/10 t3预览](RD_GRESHO_MOVING_BOOST0_10_T3_20260927.md)，
档案`../local_runs/gresho_glass_moving_boost0_10_t3_lab_20260927_v1/`，PDF为
`output/pdf/gresho_glass48_t3_moving_boost0_10.pdf`。无commit/push/COSMA操作。

## 132. 2026-09-27：t3预览左侧增加static N、boost0对照

**作者：Codex；用户要求左侧补static mesh boost0，仍为glass48、t3，以展示涡旋自身
旋转的耗散也因moving mesh减小。** 沿用“先单独预览”，没有修改论文。复用§128
冻结N static binary，新跑uniform/pilot/science共三例，一rank、OMP/BLAS各1，
未重编译或改production/default Config；155个source/build文件hash仍匹配。

uniform及pilot到.046875，256步，uniform最大差2.49e-14低于原1e-12门槛；science
正常到t3，耗时201.91s，16384步、dt3/16384。完整time/step历史与§131四组moving
相同；static0和moving0 N初始字段按ID逐位相同，static坐标各快照固定。全部25个
science快照有限且rho/p/mass正，无native断言失败，已无活动solver。

t3 static0 N mass加权vphi L1=.12085623，moving0=.04724472，比例.39091671，约
降低60.91%（2.558倍）；峰值.485980/.735437。面积加权L1=.12048805/.04715843，
vector速度L1=.12831442/.04903911。结果支持无bulk boost时局部旋转涡旋衰减也更小；
并不隔离某一flux/regularization/flip机制。原boost0/10剖面的弱boost敏感性结论及
完整mesh/state非精确不变的限制仍保留。static质量/能量漂移为−6.66e-16/0；moving0
N仍为+1.519e-4/−2.087e-4，不混淆耗散和全局守恒性质。

新analyzer读取并重新核验原moving数据，不覆盖旧图/summary；新两panel图左侧加灰色
static0方点，右侧LDA保留原数据。全部2304原生点、解析中心、不插值/binning；最终
PDF渲染检查通过，图例可读、点未裁切。报告
[static0/t3对照](RD_GRESHO_STATIC0_T3_OVERLAY_20260927.md)，档案
`../local_runs/gresho_glass_t3_static0_overlay_20260927_v1/`，PDF为
`output/pdf/gresho_glass48_t3_moving_boost0_10_static0.pdf`。无commit/push/COSMA操作。

## 133. 2026-09-27：拉取Overleaf更新，4.3.1采用远端版本

**作者：Codex；用户明确要求从GitHub拉取Overleaf变化，主要4.3.1采用Overleaf版。**
论文仓库main原HEAD6af0539，远端新增3个提交至06c9647；本地唯一tracked改动是
chapter4.tex中新增4.3.2 Yee测试。先备份本地/基线/远端正文、完整diff、状态和两个
Yee PDF，生成三方合并预览，无冲突；定向暂存Chapter4后fast-forward，再恢复本地
增量。远端4.3.1、删除4.2.3与Chapter1修改已同步；没有改写Overleaf内容。

核验4.3.1逐字匹配远端，本地4.3.2 Yee内容保留，32个untracked文件hash不变；
HEAD等于origin/main、index为空、无冲突且diff检查通过。仅清理本轮临时stash，
两条原有stash保留。没有新commit/push，未编译PDF，现有master.pdf早于此次同步。
备份与verification位于`../local_runs/thesis_overleaf_sync_20260927_234550/`。
Gresho仍为单独预览，未在此次同步时插入论文。AREPO代码与实验数据未改。

## 134. 2026-09-27/28：完成Chapter3三处红字与K矩阵核验，编译审核PDF

**作者：Codex；用户明确授权Chapter3红字修改，包括distribution schemes、CGAL
引用和K matrix复核，并要求编译PDF审核。** 在论文main06c9647上保留本地Chapter4
改动，备份正文/bib/PDF及tracked hashes后处理全部三处TODO。Distribution Schemes
增加Deconinck/Ricchiuto2017、Csik2002、Paardekooper2017、Morton2023的出处说明及
N定义的Roe/Sidilkover1992引用；CGAL新增官方文献表核验的Fabri et al.2000条目。

K显式矩阵16项原式无误。正文明确n_i=ell_i*n_hat_i，K_i=ell_i*A(n_hat_i)/2，
特征值同样缩放。检查原standalone triangle2D.h和当前AREPO几何/矩阵构造，均保存
单位法向量并另乘0.5*边长。符号求导16项差全部为零；提取未修改native C函数验证
160个三角形/480个K矩阵（gamma1.4和5/3，含零速），完整矩阵scaled差1.06e-14，
K±差≤2.40e-14，特征值差1.45e-13。没有production修改或新的hydro实验。

XeLaTeX全文247页完成，零未解析引用/交叉引用，零编译错误。初次隔离build缺少
include子目录、随后缓存转换旧XDV均未交付；完整重编译后又发现root旧bbl遮住
新引用，改用build目录BibTeX和build优先TEXINPUTS解决。PDF转换从thesis目录运行，
使相对图片路径有效。原有其他章节overfull与少量bib/package警告不扩大修改范围。
最终正文114--117、123及书目198页渲染检查通过，法向量定义与公式同页，矩阵/引用
清晰。核验tracked修改仅本次Chapter3 tex/bib，Chapter4 hash与任务开始逐字一致。

审核PDF `output/pdf/thesis_chapter3_review.pdf` 位于
`../local_runs/thesis_ch3_rednotes_20260927_235021/`；本地论文master.pdf和生成bbl也已
刷新。完整审核/构建记录见[报告](RD_THESIS_CH3_REDNOTES_20260928.md)。未commit/push，
未写Overleaf，Gresho仍未插入论文。

## 135. 2026-09-28：按用户澄清恢复K/Distribution原文，追溯LDA和N出处

**作者：Codex；用户明确要求撤回§134中K与Distribution Schemes的新增文字。**
用户只要求核验K元素，且distribution引用应追溯早期LDA/N来源，而非再增加review、
Morton或Paardekooper介绍。两块已逐字恢复到修改前/论文HEAD06c9647，包括原红字
TODO；保留CGAL/Fabri2000引用。K矩阵16项原式无误，未修改元素或重复运行solver。

研究核实N可追溯Roe1987 CoA8720，Roe/Sidilkover1992是合适的早期期刊出处。
Deconinck等1993 Computational Mechanics论文§3.1、式(23)明确将LDA命名归于
Struijs/Deconinck/Roe1991 VKI LS1991-01；官方VKI目录也确认元数据。Euler system
N的matrix推广应另看van der Weide/Deconinck1996，Abgrall/Barth2002明确归因。
1987/1991/1996原件未取得，未声称读过或断言1991绝对首创LDA；新引用尚未写入论文。
完整出处、证据和最小引用建议见[研究记录](RD_THESIS_CH3_LDA_N_ORIGINS_20260928.md)。

完整247页PDF重编译成功，无未解析引用/交叉引用；正文115--117页渲染检查通过。
保留其他章节原有BibTeX警告。论文master.pdf/bbl已刷新，Chapter4 hash不变。
档案`../local_runs/thesis_ch3_origins_20260928_105952/`，审核PDF
`output/pdf/thesis_chapter3_restored.pdf`。无commit/push/Overleaf写入/COSMA操作。

## 136. 2026-09-28：按用户指定添加N、LDA及Euler矩阵形式的四篇引用

**作者：Codex；用户明确指定N用Roe1992、LDA用Struijs1991，Euler矩阵形式加
van der Weide1996与Abgrall2002。** 在原有介绍句中插入引用：N名称括号内引用
Roe/Sidilkover1992，N矩阵公式前引用van der Weide/Deconinck1996和Abgrall/Barth2002；
LDA名称括号内引用Struijs/Deconinck/Roe1991。新增后三篇BibTeX条目（Roe1992原有），
移除Distribution节“add ref”红字。核验移除新增citation后逐字等于修改前正文
（除已完成的TODO），未增加说明句、未改公式或K区域；Chapter4 hash不变。

引用来源沿用§135记录，另核对SIAM官方Abgrall/Barth条目24(3):732--769。
论文采用通常引用年份2002（原文copyright2002；出版社当前issue页面标January2003）。
XeLaTeX/BibTeX/xdvipdfmx全文247页完成，无LaTeX错误或未解析引用；原Chapter1两项
BibTeX警告仍保留。正文117--118与书目189、220、223页渲染检查通过，四篇引用显示正确。
档案`../local_runs/thesis_ch3_scheme_citations_20260928_111819/`，包含修改前备份、
diff、完整build和verification；审核PDF为`output/pdf/thesis_chapter3_scheme_citations.pdf`。
master.pdf/bbl同步刷新。无commit/push、Overleaf写入、solver/COSMA操作。

## 137. 2026-09-28：Chapter2 Table2.1改成与AREPO流程图相同的整页横向

**作者：Codex；用户明确授权Chapter2 Table1旋转排版以改善阅读。** 原表使用
sidewaystable，只旋转内容，PDF页无Rotate；AREPO流程图使用pdflscape，PDF页Rotate90。
将Table2.1改为landscape内table[p]，通过afterpage保持原有分页及标题与段落衔接；
master.tex仅新增afterpage包。表内数据、caption、label和全部正文逐字保留。

XeLaTeX两遍与xdvipdfmx完整构建成功，仍247页，无编译错误/未解析引用。全PDF逐页
提取文字对照完全相同（忽略空白），仅PDF106页/正文84页旋转元数据从0变为90；
正文83--85页渲染检查通过，表格直接横向正读，列与引用未裁切。Chapter3 tex/bib及
Chapter4 hash不变，master.pdf已刷新。档案
`../local_runs/thesis_ch2_table_landscape_20260928_112503/`含before、diff、build和verification；
交付`output/pdf/thesis_chapter2_table_landscape.pdf`。未commit/push或写Overleaf。

## 138. 2026-09-28：Gresho boost图改为均值线与浅散点，讨论合并vortex测试

**作者：Codex；用户提出4.3.2中Yee/Gresho boost合并，并要求参考Chapter3加平均线、
降低散点透明度、图例放图内、标题缩短。** 按之前“先单独预览”的范围，只生成新图，
没有修改论文。复用§132的五组glass48/t3/lab原始数据，核验summary/PDF/snapshot hashes
并精确复现原mass-weighted L1；没有solver测试或重跑。

绘图沿用Chapter3的35个[0,0.7)等宽径向bin、无权重节点平均，alpha0.09全部节点散点。
每组2304节点全在bins内且全部绘制。moving0实线与moving10虚线、错开的空心marker
避免近重合曲线互相遮盖；static N0灰色对照保留。图例移至右上角、移除L1长文本；
标题仅Gresho/glass48²/t3，panel仅N/LDA。PDF渲染检查通过，原图/数据/论文hash不变。

建议统一subsubsection为Boosted vortex tests，Yee收敛与Gresho保持性分别叙述和成图。
指出现有Yee moving数据用element co-moving frame，而本Gresho组用lab frame；实际
合并时要缩窄Yee原文“For these boosted tests”的范围，不能写成共用同一frame配置。
档案`../local_runs/gresho_boost_style_preview_20260928_114134/`保存PDF/PNG、5份bin CSV、
拟用caption及验证记录。详见[图形与结构建议](RD_GRESHO_BOOST_STYLE_20260928.md)。
无论文插图/commit/push/COSMA操作。

## 139. 2026-09-28：区分Gresho两侧moving boost0配色

**作者：Codex；用户要求两侧moving boost0不要同为橙色。** 保留N面板橙色，
LDA面板改为紫色（#9467bd），散点、均值线和图例同步。其他样式不变。
重新生成独立PDF/PNG并渲染检查；五组case记录、输入hash与五份径向均值CSV
均与§138逐字一致，无新solver运行或论文修改。档案：
`../local_runs/gresho_boost_color_preview_20260928_v1/`，含绘图脚本及verification.json。

## 140. 2026-09-28：Gresho插入4.3.2，并准备三组Sod本地审核图

**作者：Codex；用户授权将§139配色版Gresho图插入4.3.2，少写文字，并先本地审核Sod。**
Yee/Gresho共用Boosted vortex tests小标题，新增一段Gresho设置与结果说明及Figure4.8。
限定Yee原co-moving说明的范围，Gresho明确lab frame；无4.3.1或理论改动。
为避免浮动插图混入红字备选稿，三张vortex图后clearpage。249页全文编译通过，
无未解析引用/LaTeX错误；正文165--169渲染审核，Figure4.8在正文168/PDF190页。
论文master.pdf更新；Chapter2/3/master.tex等原改动及红字正文逐字保留。

Sod复用§104完成的lab moving N/Roe与LDA/Gauss3：glass128²共16384节点，
单管初始有效Nx64，gamma1.4，rawt=.08、tau=.16；CFL.08、cap1/3000，N/LDA实际
917/970步，未声称相同步长历史。制作三页独立审核PDF及各页PNG/PDF：密度/vx/压力/
比内能全剖面，接触间断/激波放大，rawt0/.04/.08二维密度中央条带。散点保留全管
8187节点，均值用128等宽xi bins；误差仍按原节点median-dual area加权。
检查源码/二进制/Config/IC/参数hash、五份快照时间和正性，复现原3个L1至1e-14；
比内能与状态方程一致。密度图仅从快照节点重建Delaunay进行显示，不当作native
connectivity诊断。三页PDF均已渲染审核，输入hash复检不变。

N较弥散，LDA更尖锐但vx最低-0.737816，密度/压力欠冲也保留；原全局质量/能量漂移
完整记录。只是一组分辨率的moving结果，无新增hydro运行、static对照或收敛结论。
Sod暂未放论文。档案：`../local_runs/sod_thesis_preview_20260928_v2/`；论文更新档案
`../local_runs/thesis_gresho_sod_preview_20260928_v1/`。详见
[Sod审核记录](RD_SOD_THESIS_PREVIEW_20260928.md)。无commit/push/Overleaf/COSMA操作。

## 141. 2026-09-28：匹配static Sod，并以一阶LDA检查Morton比较

**作者：Codex；用户要求绘制static mesh Sod，检查是否像Morton2023那样无明显振荡。**
新建4个冻结同源static二进制，先过4个uniform门禁，再完成4个Sod science运行。
与§104 moving对照使用相同glass128²/单管Nx64、gamma1.4、rawt.08/tau.16、CFL.08、
cap1/3000。Static N/Roe+lumped RK2、LDA/Gauss3+F1为主对照；另外用现有
RD_DIAG_PREDICTOR_ONLY跑Gauss3/Roe一阶LDA。无生产源码或默认配置修改。

结论：static LDA/F1最低vx=-.729293，moving=-.737816，大幅欠冲未随网格固定而消失。
Static N最低-2.13e-8；一阶Gauss/Roe LDA最低-1.60/-1.71e-8，负速度 trough消失，
但最高vx1.1695/1.1385仍有正向过冲。主F1与一阶CFL/cap相同、实际步历史不同；
不能声称严格同dt因果隔离或证明F1代码错误。结果表明网格运动/edge flip并非
该欠冲的必要条件，后续可检查时间更新/质量形式。Static质量/能量漂移≤4e-16。

核验binary/Config/IC/param/source hashes；所有static坐标逐位不变、VertexVelocity=0，
初态与moving匹配1e-14，所有保存状态正且有限，原moving L1复现到1e-14。
三页PDF包含全剖面、contact/shock放大、静态F1/一阶LDA对照，散点保留8187节点，
均值128xi bins、误差仍按原始节点dual area加权；三页渲染通过。

重新核对Morton原文§5.1.1/Fig7：一阶LDA1/N1、规则隔行错点、gamma5/3、CFL.4，
明确指出LDA1在x=.5有振荡并随分辨率减弱，不是无振荡保证。本轮保留当前glass和
gamma1.4等，不冒称完整Morton复现。档案`../local_runs/sod_static_matched_20260928_v1/`；
[报告](RD_SOD_STATIC_COMPARISON_20260928.md)。论文未改，无commit/push/COSMA操作。

## 142. 2026-09-28：推送用户已提交的三张moving-mesh论文图

**作者：Codex；用户要求先将上次commit的图片推送GitHub。** 检查确认目标为thesis
main上的用户提交2efbebe（add figures for moving mesh results），只新增Yee convergence、
Yee profiles和Gresho boost profiles三个PDF。Fetch发现origin/main从268bb20前进到
8f3d53f，新增Overleaf Chapter1修改及merge。将尚未发布的图片提交rebase到其上，
无冲突，新hash aa3712a；核验三张图片blob与原提交一致、Chapter1与远端逐字一致。
正常push origin HEAD:main成功（8f3d53f→aa3712a），随后核对远端main与本地HEAD。
未新增图片内容、未提交本地未跟踪文件、未push AREPO仓库或Sod预览。保留用户原
commit作者。此次仅Git同步，未重新编译；本地master.pdf尚未包含新拉取的Chapter1更新。

## 143. 2026-09-28：删除Chapter3 TODO并调整两张RT图为横向页面

**作者：Codex；用户要求删除Chapter3 TODO，将两张R–T instability图横过来方便阅读。**
删除K矩阵附近唯一剩余的法向量归一化TODO，矩阵公式与说明不变。将Figure3.8/3.9
由sidewaysfigure改为afterpage内的landscape/figure，沿用已加载的包；图宽改用横页
linewidth，保持原有图形比例。两份原图PDF、caption、label和其余章节逐字保留。

全文XeLaTeX编译成功，249页；两图在正文134/135页（PDF156/157），Rotate90，打开即
可正向横读。矩阵所在页、两图及相邻正文页均渲染检查，无裁切或分页异常；无编译
错误、未解析引用或过大浮动警告。核对所有tracked文件hash，仅chapter3.tex变化；
git diff --check通过。master.pdf/master.bbl已刷新，也包含§142拉取的Chapter1内容。
档案`../local_runs/thesis_ch3_rt_landscape_20260928_v1/`保存before/build/diff/verification，
交付`output/pdf/thesis_chapter3_rt_landscape.pdf`。无solver操作、commit或push。

## 144. 2026-09-28：核实Sod坐标、镜像分辨率及Morton/SWIFT初值差异

**作者：Codex；用户要求先核实initial condition、xi/tau、镜像后的有效resolution，
进一步对比Morton2023和SWIFT Sod2D。** 直接检查共享IC、六组static/moving零时快照、
归档Config/参数/hash；均为单位周期方盒，x<.5高密高压，周期接缝处反向Riemann问题。
16384节点，半盒管道8187节点；h0=1/128，Ltube=.5，初始有效Nx64。不是128个bin或
sqrt8187。IC位置逐位等于取模后的SWIFT glass128；几何并非逐点镜像。

xi=2(x-.25)、tau=2t保持pseudo1D Euler缩放，速度/密度/压力不改。10001点解析解
rawt.08与tau.16逐位一致；按精确波速，周期双激波首次相遇rawt.142681，晚于当前终点。
Morton§5.1.1初始rho/v/p相同，但gamma5/3而本组1.4；其规则隔行错点、CFL.4、LDA1/N1
也不同。文中该节/图注未列终止时间，不声称t.2已经核实或当前组是论文复现。

核对本地SWIFT与upstream b2ac805的Sod2D源码：makeIC/参数逐字一致。默认rhoR=.140625、
gamma5/3；两种glass128²/48²各缩放.5后沿x铺两份，2×.5盒共37376粒子。由面积和粒子数
直接得到rhoR/rhoL=(48/128)²，名义粒子等质量。其中央单位宽图窗左/右间距1/256与1/96，
两半段分别128/48间隔；不同于我们两侧1/64，也不能称为统一Nx128。默认时间.2/CFL.1。

此核实不改变先前共用IC的static/moving或F1/FE内部对照结论；只限定跨论文/代码比较。
[详细记录](RD_SOD_IC_MORTON_SWIFT_AUDIT_20260928.md)；档案
`../local_runs/sod_ic_audit_20260928_v1/`含audit.py/json、hash和固定revision的SWIFT源文件。
未修改实验输入、solver或论文，未新跑hydro，无commit/push。

## 145. 2026-09-28：Sod_2d_Morton的glass一阶N/LDA两档计算

**作者：Codex；用户要求改成Morton2023设置但保留glass，并命名Sod_2d_Morton。**
新增独立example/run/analyze/README，使用同源冻结构建，无solver/default改动。
核对本地原RD SODX constants/setup：2×2周期盒、中央高态、T_TOT=.2；此副本无Git元数据，
不冒称已经确认论文Figure7原始revision。按论文设置v=0而不复制本地旧代码1e-9seed。
gamma5/3，rho/p=1/1与.125/.1，CFL.4，静网格Roe残差、完整forward-Euler N/LDA。
通过既有predictor-only guard实现一阶，避免关闭RK2落入legacy两调用路径。

有效Nx64/128对应全盒128²/256²；统一wrapped relaxed glass128，高分辨率2×2周期铺接。
新图取1<x<2，xi=x-1、tau=t，终止.2；不沿用旧单位盒tau=2t。5时刻输出。
两项uniform先过（最大9.44e-16），再跑四项science，最多2worker、每rank OMP/BLAS1。
四项均完成，实际226/481（N）和235/489（LDA）步；AREPO carrier/tree/dyadic时间步保留，
虽CourantFac相同，不声称与原代码nodal RD CFL逐步一致。cap.02未限制实际步长。

N vx_max .867319/.856229，LDA .955933/.879791，解析平台.841195。LDA稀疏波尾部过冲仍有，
高分辨率明显减弱；Nx64最低vx约-.000210，Nx128约-1.8e-8，没有先前F1约-.73的大槽。
本轮同时改变EOS/时间格式等，不能单独归因gamma或称所有RK2错误。全部保存状态正/有限，
N/LDA初态逐位匹配，坐标不变/VertexVelocity0，最大质量漂移3.95e-16、能量8.08e-16。
两页PDF与nativePNG保留全部节点散点及128bin均值，误差按原节点dual area加权，已渲染审核。

[详细记录](RD_SOD_2D_MORTON_GLASS_20260928.md)。档案
`../local_runs/Sod_2d_Morton/20260928_v1/`含source/config/binary/IC/参数及hash、日志、快照、
summary/verification和审核PDF。未写论文、commit/push或操作COSMA。

## 146. 2026-09-28：同一Sod_2d_Morton配置补齐moving mesh与RK2/F1

**作者：Codex；用户澄清应针对该物理配置把moving mesh、RK2等都算一遍。**
沿用§145完全相同IC/source：gamma5/3、2×2周期盒、有效Nx64/128、xi=x-1、tau=t、
终点.2、CFL.4、cap.02、lab frame。新增7隔离构建、7uniform gate和14science runs；
连同4项已完成一阶Roe基准，共18science全部完成，无数值失败或调小CFL重试。
新增static N/RK2、LDA/Euler/Gauss3、LDA/F1 Roe/Gauss3；moving N/RK2/Roe split、
LDA/F1 Roe split/Gauss3。既有split-stage guard禁止predictor-only，未硬拼moving Euler，
未修改guard、solver、默认Config或增添limiter。单rank，OMP/BLAS均1，最多2worker。

9项总uniform最大偏差2.00e-15；135保存状态均正/有限，初态匹配、EOS、stage0/1、
static位置不变及moving实际运动均核查。归档source/config/binary/IC/参数/快照hash复核。
所有组使用相同CFL/cap而非相同dt；moving Roe/F1 Nx128最小dt9.76562e-5，其余Nx128
最小.000390625。均未触及cap.02。未声称这些时间步等同原standalone nodal RD CFL。

LDA/F1大负速度槽仍在：Nx128 static/moving Roe为-.594770/-.595945，Gauss3为
-.594740/-.583813。静网格一阶和N/RK2没有同量级负槽，不能泛称所有RK2有问题。
静网格加密后负槽面积约减半但深度不明显下降。Moving三组在两档均降低rho L1，
接触间断更锐利，但vx/p L1均升高。Moving Roe/F1 Nx128有明显接触区散点离群：
vx_max1.200884、e_max8.531915；Gauss3为.991746/2.324658，平均线会掩盖局部极值。
静网格质量/能量漂移≤3.95e-16/1.08e-15；moving最大为.0958%/.2112%，明确记录，
不以uniform gate代替非均匀物理守恒验证。逐步ALE记录与快照漂移相符至打印精度。

`run_variants.py`/`analyze_variants.py`及README加入example。完整18行误差与步长表见
[报告](RD_SOD_2D_MORTON_VARIANTS_20260928.md)。档案
`../local_runs/Sod_2d_Morton/20260928_full_v1/`保存全部配置、数据、日志和summary/verification。
六页PDF按mesh/time/residual各两档排列，保留全部原始散点与128bin均值，误差按原节点
当前dual area加权。全部页面渲染检查；Roe大能量离群点专门标注并复核，无裁切。
纯本地预览，未改论文、commit/push或操作COSMA；所有计划计算均已结束。

## 147. 2026-09-28：Sod管道横轴简化为x，沿用t=.2比较约定

**作者：Codex；用户接受默认Morton输出t=.2，并询问周期镜像与xi平移的关系，要求简化横轴。**
按横轴直接标x、范围0–1理解其“改成x = 1”，已先说明此理解。核对实际IC生成器与
本地原SODX setup：原坐标X∈[0,2)，.5<X<1.5为高态，外侧低态；左管0<X<1为反向
Riemann初态，右管1<X<2为标准Sod，原盒两端低态周期连接。这里仅物理量初态镜像，
不声称glass节点逐点对称。新显示坐标x=X-1等于原xi，只平移，不缩放长度或时间。

两种analysis绘图入口的横轴改为x，标题时间改为t=.2；不改任何IC、原archive metadata、
CSV、误差数据或solver。新presentation档案`../local_runs/Sod_2d_Morton/20260928_display_x_v1/`
从18个原终点快照与bin CSV重画六页PDF；逐位核对原散点/均值，输入hash前后不变。
六页渲染审核及文本标签检查通过，保留所有离群点与极值标注。用户t=.2约定已记录，
仍区分采用的比较时间与论文图注是否明确标注的文献事实。未重跑hydro、改论文或push。

## 148. 2026-09-28：确认一阶RD更新并收敛Sod主图范围

**作者：Codex；用户重申thesis中LDA默认Gauss3 contour，主要比较static/moving RK2
及static first-order RD，并核实forward Euler是否就是删去Chapter3的RK2第二阶段。**
核对solver3921–3972、4057–4071、5382附近及实际归档Config：predictor-only使用完整dt，
stage0完成后直接break，保留U*=U^n-dt/|S_i| sum(phi_i^T)，不进入corrector或F1时间项。
与Chapter3 eq:RD_2D_update/eq:RD_RK2_predictor一致。保持TOTAL_RESIDUAL+PREDICTOR_ONLY
是为了走完整时间步路径；不能简单去掉TOTAL_RESIDUAL后落入legacy半权重调用。

新增plot_main_comparison.py，从既有18组中选12组：两档Nx的N一阶Roe/static、N RK2
Roe/static/moving，LDA一阶Roe/static、LDA RK2 Gauss3/F1/static/moving。主图每列只保留
三个数值曲线和解析解；图例改为first-order RD，页脚明确一阶Roe及RK2残差配置。
Morton式LDA一阶基准与thesis默认RK2之间同时改变残差，不能当作纯时间格式对照；
static/moving RK2是同残差家族的mesh对照。诊断Roe-LDA moving组保留原档案，不再混入主图。

新presentation档案`../local_runs/Sod_2d_Morton/20260928_main_comparison_v1/`，两页按
Nx128、Nx64排列；全部原始散点及128-bin均值保留，输入SHA和重算均值逐位核对通过。
PDF两页渲染检查通过，无裁切或图例遮挡关键特征。README/local context同步。
未重新计算hydro、修改solver/论文、commit/push或操作COSMA。

## 149. 2026-09-28：Sod曲线改虚线、简化标题并核实比内能振荡

**作者：Codex；用户要求三条数值曲线均改虚线避免遮挡，去掉页脚，标题仅保留Sod
shock tube, Nx=...，并询问specific internal energy为何振荡明显。**
plot_main_comparison.py改用短/中/长虚线及不同相位，解析解保留黑实线。新v2档案
`../local_runs/Sod_2d_Morton/20260928_main_comparison_v2/`保留原v1和全部science数据；
输入hash与原始散点/128-bin均值核对不变，两页Nx128/64均渲染检查。

读取实际HDF5的Density/Pressure/InternalEnergy，对12个终点快照491520节点逐点检查
e=p/[(gamma-1)rho]：最大绝对偏差4.44e-16、相对偏差2.14e-16。不是把total energy当成
specific internal energy，也未混用gamma。源码update_primitive_variables.c的非宇宙学
理想气体路径先由E/M-v²/2恢复e，再用p=(gamma-1)rho e设置压力；EOS一致性只证明
绘图字段关系正确，不能排除产生rho/p误差的solver问题。

Nx128 static LDA/Gauss3/RK2在x=.709069的节点rho=.176757（解析.229806，-23.08%），
p=.293417（解析.293945，-.18%），所以e=2.490006（解析1.918654，+29.78%）。该接触
区域的bin峰值e_mean=2.270096，p_mean/[(gamma-1)rho_mean]=2.269239；平均运算与取比值
不交换，但此差别远小于主峰，不是主峰来源。激波前x=.884357节点p低65.48%、rho低
40.84%，e相应低41.64%；moving对应最低e=.583489，压力/密度相对下冲也吻合。
上述是振荡在派生变量中的代数表现，尚不判定RK2/F1振荡的具体数值机制。

audit_internal_energy.py/json保存检查和节点ID，verification保存输出hash/审核结果。
未重新跑hydro、修改solver/论文、commit/push或操作COSMA。

## 150. 2026-09-28：Sod仅保留rho/vx/p并提高导出清晰度

**作者：Codex；用户要求去掉specific internal energy，提高DPI，并随即澄清标题应为
Sod shock tube, Nx=..., gamma=..., t=...。** plot_main_comparison.py改为3×2布局，
两页仍为Nx128、Nx64，标题包含gamma5/3和t.2；保持已有虚线、颜色、全部散点和均值。
PNG由180dpi提升到600dpi（5700×4740）；PDF显式600dpi raster scatter，曲线/文字为矢量。
直接检查PDF12个嵌入散点图层的像素尺寸和变换矩阵，确认两向均600dpi。

新档案`../local_runs/Sod_2d_Morton/20260928_main_comparison_v3/`保留旧版本，复核science
输入hash、散点/均值及方法metadata不变；两页渲染检查通过。README/local context同步。
此为展示修改，未重新跑hydro、改solver/thesis、commit/push或操作COSMA。

## 151. 2026-09-28：将Nx64 Sod图和简短描述加入Chapter4.3.2

**作者：Codex；用户选择Nx64用于thesis，理由为Nx128虽精度更高但定性行为不变，
点数较多影响可读性，要求先放入图片并添加少量文字。** 在Chapter4.3.2新增Sod shock
tube小标题和两短段，交代gamma5/3初态、128² glass全盒2×2、周期反向双管、显示x=X-1、
有效Nx64、lab frame/CFL.4、t.2，以及moving接触间断更锐利和两种mesh的LDA/RK2振荡。
图注记录N/LDA、static first-order/static RK2/moving RK2、全节点散点和128-bin无权均值，
并明确一阶Roe、N RK2/Roe、LDA RK2/Gauss3+F1，未将其解释为纯时间推进对照。

从已审核v3两页PDF提取第2页到thesis `chapter4/figures/sod_glass_Nx64_t02_profiles.pdf`，
逐字节核对page content和所有XObject数据流，保持矢量曲线/文字与600dpi散点。
新图为Figure4.9，正文169页（PDF191），说明文字在正文166页（PDF188）。新增短图目录
标题以避免完整图注扩张list of figures；原vortex文字、图注、红色草稿与4.3.1逐字保留。

隔离完整源树XeLaTeX/latexmk编译成功，共250页，无编译错误、未解析引用、重复label或
float-too-large。渲染检查PDF187–192页通过；新内容无裁切或溢出。复核tracked文件hash，
本轮仅chapter4.tex变化，用户原chapter3修改完整保留。master.pdf/master.bbl已刷新。
档案`../local_runs/thesis_ch4_sod_20260928_v1/`保存before、source/build、diff、provenance、
verification和两页Sod新增内容review PDF。未重新计算hydro、commit/push或操作COSMA。

## 152. 2026-09-29：审核用户的boosted-vortex文字并核实Yee盒长

**作者：Codex；用户修改4.3.2的Yee/Gresho说明后要求审阅，并询问box size10是否正确。**
读取thesis main219853e（及前一Yee修改），本轮不编辑论文。参数模板
examples/yee_2d/boost_comparison/param.template:26为BoxSize10；本地COSMA移交的
Nx48/96/192 boost10 HDF5 Header均10，坐标覆盖0–10；COSMA comparison归档分析函数以
中心(5+10t,5)和周期10求精确解，故t1正好平移一个盒长。Gresho使用单位周期盒。
移交HDF5符合本地inputs_manifest，但其文件SHA与后来COSMA comparison.json记录不同，
初次尝试逐文件对应断言失败，未将本地文件冒称为逐字节验证过的COSMA原始IC。
COSMA原始快照/参数不在当前导入副本；此处核实配置和坐标定义，未连接COSMA重验原始运行。

按comparison.json重算四点mass-weighted拟合：moving LDA密度阶1.739337，速度阶
1.401267，用户将1.401写成density是明确笔误。速度仅前三点阶1.553560，相邻阶
1.736805、1.370314、1.106998，故不能把偏低阶数仅归于384单点。密度前三点1.813868。
两种mesh误差比支持显著降低；最大速度改善约22.5倍，密度约4.4–8.5倍。

核对当前所有匹配glass Gresho campaign：static boost10终点t1，static boost3终点t3，
static boost0终点t3；boost0/10的t3配对只有moving。未找到支持文中新句static boost10
在t3 completely dissipated的当前结果。boost10/t1 static N峰.15345确实强耗散，但不
代替未计算的t3。重叠径向剖面支持弱boost敏感性，不证明完整mesh/state轨迹严格不变。
建议保留用户强调的bulk advection与涡旋自身旋转两项意义，弱化严格不变及因果表述，
将edge-flip影响留作未验证机制；恢复一句Yee static-lab/moving-comoving与h/dt同步细化
说明，修正scalar/vector boost记号、0和10间缺and及equal timesteps语法。
本轮仅更新本项目工作记录；无论文修改、编译、hydro运行、commit/push或远程操作。

## 153. 2026-09-29：澄清Yee static盒长、周期边界和N²分辨率定义

**作者：Codex；用户追问static Yee是否同样box10，periodic是否要求单位盒，以及固定N²
是否降低分辨率。** 再读static boost10参数：BoxSize10、PeriodicBoundariesOn1，与moving
共用盒长和IC。直接读取本地yee_static_moving_384_20260924_v1/inputs的四个HDF5，
Header均10、节点数依次2304/9216/36864/147456，确为48²/96²/192²/384²。
当前解析初值函数在(5,5)中心使用exp(-r²)尺度，未将r除以盒长，涡旋长度尺度约1。

解释periodic仅要求U(x+L)=U(x)，不限定L1。N是每盒边名义点数而非每单位长度点数，
h_nom=sqrt(A/Ntot)=10/N，四档为.208333/.104167/.0520833/.0260417。
若保持涡旋物理尺度不变而把L由1放到10，用户指出的线性分辨率降低10倍成立；
若连涡旋尺度与单位一致归一化，则h/涡旋尺度不变。不能仅将BoxSize改1而保持未缩放
的Yee公式，因为这同时改变涡旋相对盒长及周期镜像问题。Static/moving同盒同点集，
比较不因盒长10失配；固定L下以N拟合收敛阶仍正确，建议论文明确h_nom=10/N。
本轮仅解释并更新记录，无论文修改或新运行。

## 154. 2026-09-29：按用户决定保留boost文字，仅修正1.401的变量笔误

**作者：Codex；用户明确保留现有4.3.2表述，只授权修正1.401对应变量。**
在本地chapter4.tex中仅将该句的density error改为velocity error，数值和其余文字不变。
用户决定不额外加入h=10/N，不将Galilean invariance改为approximate，保留edge flip
可能影响误差的猜测，也不加入lab/comoving frame说明。Comoving frame目前是优化手段，
不作为默认或必需选项；是否必要仍待研究，Gresho boost10已经在lab frame运行。
用户解释省略static boost10/t3曲线是因为t1已经耗散，不需为此另画结果；此为其文字
解释，不记作新增t3计算证据。上述编辑决定取代§152–153的相应修改建议。
核对thesis差异仅一个词；未编译PDF、运行模拟或commit/push，仍待正常GitHub/Overleaf同步。

## 155. 2026-09-29：解释equal timestep、CFL和二进制步长上限

**作者：Codex；用户询问为何此前使用1/xxx步长而不直接由CFL计算。** 核对原参数、
COSMA导入的prepare脚本、Gresho冻结Config及当前timestep.c：CFL仍计算，MaxSizeTimestep
只是额外上限；FORCE_EQUAL_TIMESTEPS取全节点及MPI最小候选值，并向下分到二进制timebin。
Equal指同一轮全节点共用步长，不要求各轮步长恒定。此前vortex对照有意使用共同小上限，
让static/moving及不同boost的实际时间步序列匹配；Yee随N翻倍将上限减半，依次1/1024至
1/8192，CourantFac=.2。Gresho cap1/4096、CourantFac=.3、TimeMax3，向下分档后实际
3/16384，五条展示曲线时间序列相同。移动Gresho冻结Config保留RD_ALE_CFL_TIMESTEP。
这种选择用于控制比较中的时间离散差异，不是equal-step算法要求，也不是最优运行效率
测试。满足CFL不自动证明时间误差可忽略；完整时间步独立性需对应配置的减半对照。
本轮解释现有设置，不修改论文、参数、solver或运行新模拟。

## 156. 2026-09-29：首次moving Sedov试跑及区域注入/CFL/一阶对照

**作者：Codex；用户要求参考本地SWIFT SedovBlast_2D尝试moving mesh，并核实Morton
区域注入的动机。** Morton§5.2.3主要为避免单点沿少数连边传播造成方向不对称，且明确
报告LDA不稳定；不把它改述为单点必然求解失败。SWIFT采用最近21粒子、glass128²、
单位周期盒、gamma5/3、rho1、P0=1e-6、E1、t.05。RD按实际median-dual质量归一化
热区能量，SciPy周期Delaunay面积与native初始质量核对，避免照搬等质量SPH归一化。

复用经production源码hash核对的四份Gresho冻结N/Roe/lumped RK2及LDA/Gauss3/F1
static/moving二进制，并补冻结static first-order N。保持lab、mesh regularization、
equal adaptive CFL、moving RD谱限制，CFL.1/cap.01；不修改solver、limiter、floor或
assert。五个128² uniform gate通过，最大8.88e-16。每runner最多2worker，重叠诊断
最多4solver，全部单rank、OMP/BLAS1。18次native尝试全部结束，无活动进程。

21点(rmax.01959655)：static N/RK2在t.00672073 predictor负压，moving N在.00226440
corrector后负质量；LDA两个mesh在2步左右负压。扩大r=.05到130点后static N完成t.05，
moving N仍在.00828857负质量，LDA两mesh仍早期负压。21点CFL减半后static/moving N
分别在.00672493/.00296021失败；一阶static N在.00663452负质量。因此不能仅归因RK2，
也未证明扩大注入区域或减小CFL即可得到稳定moving强激波结果。

130点static N最终rho_min .04377381、rho_max2.42160966、p_min1e-6，质量/能量漂移
0/-2.22e-16；激波扩散且中心径向速度散点较大。Moving在共同存盘t.00500488时激波
更尖，但能量漂移-.650671%、质量+3.00169e-6；失败前后账本还显示变化，未把图像
清晰等同守恒或稳定。其predictor末rho_min7.94e-4仍正，corrector后出现负质量。
所记录midpoint CFL比值始终>1，根因仍未隔离，不据此修改数学或放宽正性要求。

使用SWIFT二维圆柱解析函数(nu2，R∝t^.5)，t.05激波半径.2579946124，能量积分与
shock jump核查。保留有限注入半径的早期瞬态限制，不使用球对称t^.4参考。
新增`examples/Sedov_2d/`准备/分析入口；完整设置、失败点、预览与限制见
[报告](RD_SEDOV_MOVING_PILOT_20260929.md)。档案`../local_runs/sedov_2d_20260929_v1/`
保留所有源/二进制/Config/IC/参数hash、失败日志、快照、summary和verification。
早期static/moving密度图明确标注before failure；仅static完整结果画t.05解析对照。
未编译新solver、改论文、commit/push或操作COSMA。

## 157. 2026-09-29：Sedov的LDA可行性与改进次序

**作者：Codex；用户询问LDA是否可以完成、如何改进。** 复核§156日志：两种注入和
两种mesh的纯LDA/Gauss3/F1均在早期predictor恢复压力时失败，130点moving为第3步
t3.66211e-5、p=-2.1355e-8，相对冷背景1e-6已非机器舍入尺度。这里只定位触发检查
在predictor，不排除前几步corrector累积影响；不能据此把全部原因归于F1或edge flip。

读现有guard确认RD_RK2_SPLIT_STAGES仅接受N/LDA，不能将B_SCHEME作为当前路径的
一键修复。旧RD_ALE_APOSTERIORI_FALLBACK是B-engine诊断，§17.5已撤回其production
正性策略地位；局部N重算本身曾失败，本次Sedov N也会负质量，故无保证的N/LDA
混合不能自动获得Euler正性。Rank-deficient F1 lumping和Gauss3均不是正性limiter。

建议先固定130点、CFL.1原IC，以完成的static N作基线定位moving负质量及几何转换
守恒缺陷；逐阶段区分临时Q更新、modified coefficient转换和endpoint Q。之后构造
或验证具有适用ALE/CFL正性性质的保守低阶后备，再对LDA高阶修正进行保守限制，
覆盖predictor/corrector及必要的几何转移。Graph viscosity/LLF-type是候选而非现成
保证，必须在实际ALE系数和时间更新下重推/验证。初值平滑和较低压差只能作敏感性
对照，不等于修复原强Sedov；不能靠硬截断rho/p给出守恒已解决的结论。

核对文献：Morton2023§5.2.3报告LDA1/LDA2不稳定；Guermond et al.
https://arxiv.org/abs/1710.00417 以正性低阶graph-viscosity更新和convex limiting构造
高阶Euler方案；Bacigaluppi/Abgrall/Tokareva https://arxiv.org/abs/1902.07773 给出
RD的MOOD型后验限制策略。这些支持研究方向，不证明当前移动实现可直接使用。
本轮为代码/日志/文献审核与建议，无新运行、solver或thesis修改。

## 158. 2026-09-29：RD Sedov保正文献与Rusanov低阶原生改造

**作者：Codex；用户要求查阅以往RD求解Sedov的方法，并改造RD增加正性。** 核对
Morton2023§5.2.3（N/强N混合成功，LDA不稳定）、Abgrall/Lipnikov/Morgan/Tokareva
2020§8.3（Lagrangian staggered-grid RD + MARS完成Sedov）、Bacigaluppi/Abgrall/
Tokareva2023（MOOD最终后备为Rusanov，并非无条件信任N）、Guermond等2018/2020/
2023（graph viscosity + convex limiting；ALE Euler明确固定connectivity）。SGH变量
布局和时间离散与本代码不同，ALE论文也不是现成edge-flip解决方案。原文链接、
适用范围、保正推导与后续LDA限制设计见
[完整报告](RD_SEDOV_POSITIVITY_20260929.md)。

新增显式实验开关RD_RUSANOV_LOW_ORDER；保留N宏选择lumped RK2时间项，但完全绕过
Roe矩阵，用trapezoidal Euler/ALE通量与scalar Rusanov耗散构造新的空间分布。
这不是原N、不是Gauss3 LDA，也不是高阶limiter。alpha取全部顶点/方向的声学速度
上界；由LF pair-bar凸组合导出dt/S_i sum_T(4alpha_T/3)<=1。当前网格选择步长，
两个实际stage再次检查CFL、bar state、rho及内能；ALE lumped corrector另检查
b_i=1.5-Mmid_i/Smodified_i在(0,1]及CFL*/(2b_i)<=1。Endpoint正面积缩放保留U的正性，
但未修复一般非均匀ALE总量。只支持单rank、periodic、equal-step hydro原型。无新增
rho/p floor或assert放宽，无默认Config或论文修改。

新增C kernel及5000组编译核随机状态/三角形验证；flux一致性/局部守恒最大归一化
误差1.764e-16，Euler步正性与uniform均通过。全部5个make check_rd通过。
v1因header guard未加入defines_extra产生build配置失败，原样保留；修正后v2冻结
源码并建3份独立binary，9次native运行全部完成，共45独立快照。3个uniform gate
最大误差1.11e-15；关闭新开关的static N t.001与原存档binary的5快照按ID逐点bitwise
相同。生产源码hash仍与v2一致，无活动solver。新文档/runner补充不改变已测binary。

同原128² glass、gamma5/3、rho1、Pbg1e-6、Ehot1、CFL.1/cap.01、lab设置：
21点及r.05/130点的static/moving Rusanov四组均完成t.05，分别3051/3118/2780/2762
步（依次21-static/21-moving/130-static/130-moving）。全部23422个science stage
rho和内能严格为正，内能密度最小约1.5e-6，actual CFL最大.105566<1，moving b最小
.497315。原moving N在.00226440/.00828857失败，故同IC下原生鲁棒性改善已证实。

Static质量能量守恒至3.33e-16；moving两组质量漂移-.2397%/-.2358%，能量漂移
-2.4147%/-1.3154%，因此仍不是完整守恒的Sedov验证。不能把漂移全部归因edge flip。
Rusanov moving峰值rho约2.63，static约2.00，解析跳跃4；旧static N/130点峰值2.42，
说明低阶后备的代价是更强耗散。21点最终剖面和二维密度图已视觉检查。

档案`../local_runs/sedov_positivity_20260929_v2/`；入口`examples/Sedov_2d/run_positivity.py`
与analyze_positivity.py，显式Config_Rusanov_static/moving.sh。下一步高阶方案应限制
成对反对称的保守修正（含F1时间修正）并覆盖两个stage；trapezoid与Gauss3总残差
不同，不能任意局部混合。报告给出共享Phi_G的admissible element inflow候选与CFL，
以及physical endpoint Q一致/保守保正remap的前提。这部分尚未实现，不恢复旧§17.5
已经搁置的LDA→N MOOD诊断为production策略。无commit/push、COSMA或thesis操作。

## 159. 2026-09-29：Sedov 复用旧 connectivity repair 的守恒收益与负压失败

**作者：Codex；用户追问能否像以前一样做 connectivity repair。** 复核§21–23
及当前C代码，允许实验Rusanov与已有RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC组合。
旧support-patch修正公式完全保留；只在此新组合中，从修正后U恢复predictor原始变量，
使残差输入与RK起点一致，沿用§21.4指出的同步要求。区间mesh velocity不改变，
不调用带floor副作用的通用recovery。普通N/LDA和无repair分支保持原行为。

冻结一次独立原生build后，uniform及两组相同IC的Sedov完成尝试。uniform误差
1.11e−15；21点在t.00546875的repair产生p_min=−.01900419，130点在t.0015991211
首次非零repair产生p=−.0003433578，均在物理stage之前终止。21点此前成功213个
非零repair步（不是flip计数），全局remap守恒审计最大4.44e−16；两组已接受788/130步，
1836个science stage正性/CFL/b检查全部通过，最大CFL.104797，最小b.497598。

在共同到达的21点时刻t.00545654296875，无repair/有repair相对质量漂移分别
−1.75028022e−4/−1.97228878e−9，能量漂移−1.24978715e−2/−1.04590062e−6。
因此旧修正确实明显改善早期守恒，但下一次remap破坏正性，不能宣称已完成t.05。
130点首次repair之前两组总量至舍入一致。剩余小漂移可能涉及已有Arpaia endpoint
conversion缺口，本轮未独立闭合该项，不把全部误差确定归因于它。

独立square-diagonal flip反例验证：旧修正U_i^H=U_i−D_P/ΣŜ，虽然总量守恒，
却可把热冷对比下的冷点内能减为负数。后续应在各自守恒的Q^L和Q^H间使用同patch
theta凸混合，而不是仅缩小−w_iD_P（后者留下守恒缺口）。简单patch均值low保正但
耗散，历史CR low+limited high更值得接回；当前强Sedov尚未验证该fallback。
本轮未实现新limiter。详见[报告](RD_SEDOV_TOPOLOGY_REPAIR_20260929.md)。

档案`../local_runs/sedov_topology_repair_20260929_v1/`保留源码/Config/header/binary/
linkage/参数/输入/所有失败日志；成功build binary SHA256
bbba3d6878bd65d9a04991c74caaf6e79948b901239f16b8470dfee362afd852。
analyze_topology_repair.py核验双方存档hash、快照及逐stage检查，输出完整JSON和
守恒时间曲线，已视觉检查。make check_rd首次误用缺numpy的系统Python；显式项目
Python重跑5项全部通过。全部3次native尝试已结束，无活动solver，无thesis、COSMA、
commit/push或默认Config变更。

## 160. 2026-09-29：Sedov 更少注入点及 SWIFT 21粒子初值核实

**作者：Codex；用户要求尝试更少注入点，并问SWIFT是否只加热一个粒子。** 本机
SedovBlast_2D/makeIC.py与官方上游逐字节相同，明确N_inject=21，按到中心距离选
最近21粒子并分配总热能1；单数注释不能代表实际选择。未运行SWIFT hydro。

同128² glass、pbg1e−6、Ehot1、gamma5/3、lab、CFL.1/cap.01、moving Rusanov/lumped
RK2，新增1点和7点；RD比内能按实际median-dual热区总质量归一化。复用两套已冻结
binary，保留有/无旧repair对照，没有修改solver或编译。两uniform gate均1.11e−15。

无repair两组均完成t.05，3189/3142步，峰值rho2.61579/2.64780，质量变化
−.237630%/−.239931%，能量变化−2.576317%/−2.665694%。与既有21点峰值2.63044、
能量−2.414700%相比，径向均线基本重合，减少注入点没有明显改善激波展宽。
单点位置略偏离中心，三组均以初始注入超额能量质心作径向坐标后比较；不是任意
平移最终数据。密度图接近圆形但有环向起伏，不宣称严格对称或已完成角向误差审计。

旧repair仍分别在t.00506591796875/.0054443359375失败，最低p−.02073846/−.01911174，
均为IDs7932/7977，与21点失败相同。在此之前的物理stage均正性通过，失败明确在
topology map内。全部science已接受stage共16156，最大CFL.109499<1，最小b.497257。
6次native尝试已结束（4成功含2uniform，2数值失败），22新快照均审计。详细表格、
输入/软件出处及限制见[报告](RD_SEDOV_FEWER_INJECTION_POINTS_20260929.md)。

档案`../local_runs/sedov_injection_sweep_20260929_v1/`含分方法source.tar、binary/
Config/header/linkage、IC/参数/日志和脚本hash，输出径向图、二维密度及守恒曲线，
均已视觉检查。分析最初用uniform速度直接bitwise比IC而触发1ulp差异，改成按native
实际(m*v)/m初始化round trip核对后逐值完全相同；保留初版及错误说明，无物理数据
或solver断言变化。结束无活动solver，无thesis、默认Config、commit/push或COSMA操作。

## 161. 2026-09-29：Sedov 中心偏差、Morton尺度和SWIFT时间核实

**作者：Codex；用户要求解释r<.15偏高并比较Morton box10及SWIFT输出时刻。** 只读
审计既有4组Rusanov快照，未新跑hydro。t.05单点moving在r<.05/.1仅1/7节点，
static21有130/516；中心平均sqrt(S) .0624/.00781。静态守恒至舍入也有明显中心
密度过高，所以低阶耗散和moving核心采样稀疏是有证据的解释；不可把全部局部偏差
归为connectivity损失。pressure/velocity的分项机制尚未独立隔离。中心analytic
rho/vr趋零而p有限1.604968；能量−2.5763%单独按相似律只令R−.65%、中心p−1.30%，
不足以解释moving中心p约+11%。既有repair匹配时刻对照仍支持全局守恒损失主要源自
connectivity change，但该repair不保正。

Morton原代码检出工作目录有本地修改，故冻结commit ba336488的main/setup/template
作依据：L10,rho1,pbg100,rinj.25,t.01,CFL.2。新发现main在构网后将热区能量归一到
3e5；旧pilot只看setup的p1e6不完整，已附加更正。二维以L,rho,E归一，t.01→.0547723，
pbg100→.0333333。当前L1/E1/t.05接近其时刻，但pbg1e−6更冷，不能仅凭box rescale
称为完全相同初值。同N的h/L不因box缩小而变差。SWIFT终止t.05匹配实际最终快照；
配置输出间隔.01而RD为.0125。没有SWIFT数值模拟结果，图中线是其公式算的解析解。

旧analytic等距v采样首个正半径.03447，细化v_min附近采样后消除中心插值粗糙，
能量积分1.000000024、shock rho4、shock半径变化7.27e−8，原偏差依然存在。
新增audit_reference_scales.py，档案`../local_runs/sedov_core_reference_audit_20260929_v1/`
保留冻结参考文件/hash/JSON/脚本和中心3变量+节点数图，已视觉检查。详细比较与
推断限制见[报告](RD_SEDOV_CORE_REFERENCE_AUDIT_20260929.md)。无solver、默认Config、
thesis、commit/push或COSMA修改。

## 162. 2026-09-29：SWIFT、当前RD与Morton初值三方对照

**作者：Codex；用户要求单列SWIFT条件比较。** 重新读本地及上游makeIC/sedov.yml/
run.sh，扩充§161报告。SWIFT明确二维、周期、L1/rho1/gamma5/3/pbg1e−6/Ehot1、
glass128²、最近21粒子、初速0、终止t.05、CFL.1、dtmax.01、输出间隔.01。
当前RD21物理参数相同，增加的1/7点版本只改变注入选择及对应热状态。

源glass实际缓存在local_runs/swift_glass，不在SWIFT示例目录；初次读取后者报缺失，
由原runner确认缓存路径后完成检查。RD坐标与源glass按周期mod1逐值相同（原文件有7个
坐标分量稍越界），受热21点ID相同。SWIFT等质量热区质量21/16384，名义phot520.126984；
RD实际dual质量.001279853512，phot520.892946，相差.147%，两者热区能量均归一到1。
SPH实际核密度与目标rho0可有差异，不把名义phot当作已运行SWIFT的测量压力。

Morton归一化后pbg.0333333/rinj.025/t.0547723，与SWIFT/RD的冷背景存在明显差别。
SWIFT脚本启用--limiter是timestep limiter，不是RD topology positivity repair；具体
SPH formulation/kernel需查编译配置，未凭YAML指定。只补充[对照报告](RD_SEDOV_CORE_REFERENCE_AUDIT_20260929.md)
及context，无新hydro、solver、thesis、commit/push或COSMA操作。

## 163. 2026-09-29：本地运行SWIFT默认Sedov 2D并对比RD

**作者：Codex；用户明确要求用SWIFT默认设置本地运行。** 旧build-localmac/swift自报
7fbba7e0-dirty，与当前干净源码8dc43c3c不符，因此冻结git archive另行编译；不修改
原SWIFT目录。按既有Mac编译选项使用默认SPHENIX、2D、cubic M4，禁手写vectorization，
串行1thread，OMP/BLAS1。stock makeIC.py/sedov.yml及--hydro --limiter --threads=1
保持不变。原glass128²最近21粒子、Ehot1/pbg1e−6/t.05/CFL.1。全流程成功：构建20.89s，
native2.189s，396 evolution steps，6个快照达到0,.01,.02,.03,.04,.05。

运行metadata确认eta1.2348在2D仅15.14285目标邻居，不能引用YAML的48注释。
SWIFT最终rho_min/max=.0368658/3.60417，明显优于当前RD中心rho约.196和峰值2.63；
但中心压力显著过冲/欠冲，vr散点包含负值。r<.05/.1粒子数7/21，当前RD21为3/12。
这是不同空间方法、时间积分和密度估计的整体对照，不能唯一归因为某一个算子。
未调整SPH邻居数或人工粘性/扩散参数；未新跑RD。

SWIFT质量严格不变。最终E=1.000402051；输入IC E=1.000001517，因此误差+.0400534%。
注意savedt0 E=1.00153113，其u与IC相同但输出速度非零（最大分量1.82056）；io和statistics
都用leapfrog速度外推convert_part_vel，不能把首次快照当作原始静止IC。相对首次快照
误差−.112735%，statistics独立核对一致。当前预算图统一按input IC归一，保留t0输出偏移。
未对初始fake-step/output生命周期做更深入的代码缺陷判断。

全部6状态有限、rho/p/u正、IDs/逐粒子mass保持，实际时间匹配；不声称审核了每个内部
stage。native只运行1次且成功，无活动solver。新增run_swift_default.py和
analyze_swift_default.py，档案`../local_runs/swift_sedov_default_20260929_v1/`含源码/
配置/二进制/链接/输入/日志/hash/JSON。binary SHA256
e7787bed22deacfff7634c250085d05cd80a97b4f4b078c6d8c7ad5b678a907d。
全区+中心3变量图及预算图已视觉检查，初版截轴/首次输出归一图保留analysis_initial，
当前版本展示所有中心异常值并使用IC预算。详见[报告](RD_SEDOV_SWIFT_DEFAULT_20260929.md)。
无AREPO solver、默认Config、原SWIFT源码、thesis、COSMA或commit/push修改。

## 164. 2026-09-29：AREPO MMFV Sedov及moving/static RD对照

**作者：Codex；用户要求本地MMFV并与RD moving/static比较。** 新增显式
Config_MMFV_moving.sh，冻结当前源码另行编译，关闭RD，使用AREPO原生Voronoi FV、
exact Euler Riemann、原有重构/限制器和常规mesh regularization，无refinement。
全局equal adaptive CFL.1/cap.01与RD匹配，1rank、OMP/BLAS1。相同glass128²和最近21
受热ID，Ehot1/pbg1e−6/rho1/gamma5/3/t.05，按native Voronoi热区面积.001279857918
归一化，phot520.89115与RD520.89295仅差.000344%。

uniform成功1.315s，恒态最大缺陷2.054e−13。初始wrapper额外设置1e−14初始rho断言，
实际几何重构舍入6.239e−14导致其在成功native之后停止。独立确认rho=mass/Volume逐值
相同、总volume/mass=1，统一使用项目既有1e−12恒态判据后从冻结gate续跑；未改变
solver、未重跑该native，旧wrapper保留source.tar，续跑脚本和说明归档。

science完成1179步/179.293s，最终rho_min/max=.0284307/3.97057；r<.05仅4cell但均压
1.59613（解析1.60505）。全部5science快照最大M/E相对误差2.22e−16/6.66e−16。
移动Rusanov RD原21点峰值2.6304、中心最低.1960、能量−2.4147%；静态峰值2.0022、
最低.1248、守恒至舍入。MMFV整体剖面更接近解析，moving RD比static更好保留激波峰值，
但中心/守恒仍待改善。MMFV稀疏中心仍较准确，不能仅以中心点数少解释RD偏差；不同
空间方法的对照未唯一隔离耗散与ALE更新贡献。未运行ENZO。

复用现有RD static/moving与SWIFT21（hash核验），四组均21点注入。MMFV cell-average
按cell centroid绘制，RD按node，SWIFT按particle；径向原点为各自初始能量质心。
记录raw峰值与binwidth.005的均线峰值，MMFV分别3.9706/3.3024，避免混淆。
全部10新快照rho/p/u/mass正且有限，EOS最大相对误差4.42e−16；2358 flux记录无mass
flux reduction或negative-state诊断（不代表空间重构limiter没工作）。2 native尝试均
成功，已结束。档案`../local_runs/sedov_mmfv_20260929_v1/`，binary SHA256
198b64f36c0fbed9454493a4798513a320a72334ea81f3cb7c56a2b880bed915。
新增run_mmfv.py/analyze_mmfv.py，完整剖面+中心放大与预算图已视觉检查。详见
[报告](RD_SEDOV_MMFV_COMPARISON_20260929.md)。无生产solver、默认Config、thesis、COSMA、
commit/push变更。

## 165. 2026-09-29：核实Rusanov/Sedov文献并评估LDA混合

**作者：Codex；用户要求追溯文献实际做法，并问LDA+N或LDA+Rusanov是否可行。**
逐段核查SGH RD、MOOD RD、convex limiting及Morton正文，与当前C kernel和B分支对照。
纠正来源关系：当前实现是本地构造的低阶Rusanov原型，并非成功SGH RD/MARS Sedov的
复现；MOOD文章没有Sedov测试。详细原文定位与算法差异见
[文献及blending报告](RD_SEDOV_RUSANOV_LITERATURE_AUDIT_20260929.md)。

LDA+N已是现有B，但当前强Sedov的N失败意味着不能以N作可靠保正终点。建议下一步
研究LDA+Rusanov的守恒保正混合，限制完整守恒变量更新而不是只调残差传感器；需要
处理Gauss3/trapezoidal总残差差异及F1/lumped时间项。正性不自动消除正值过冲，
恢复二阶也需平滑问题验证。connectivity repair仍需独立的守恒保正remap。
补充原positivity报告的来源澄清与local context；没有新solver改动、hydro运行、
thesis修改、commit/push或COSMA操作，未将建议标为已验证实现。

## 166. 2026-09-29：SGH RD的物质网格与当前准拉格朗日ALE对照

**作者：Codex；用户追问staggered Lagrangian RD如何移动网格及与当前差别。**
核对原文§§2–3、Eq.35c、§8.2：位置/速度共享连续运动学基函数，dx/dt=u，几何用
二阶段推进，rho J=rho0；热力学使用单元局部空间。§3明确要求映射一一对应，
remapping不在本文范围，不能作为AREPO Delaunay edge flip的解决方案。

核对本地set_vertex_velocities.c及当前moving Sedov Config：网格生成点速度包含
流速、压力加速度半步预测和centroid/face-angle regularization，随后按区间速度漂移。
因此当前配置是准拉格朗日，不能简写成严格w=u。我们还保留同位守恒变量、median-dual
质量定义及随Delaunay重连变化的邻接关系；即使去掉regularization，重连后的dual
也不自动成为物质单元。附录式对照已加入[来源报告](RD_SEDOV_RUSANOV_LITERATURE_AUDIT_20260929.md)。
无solver、配置、实验输出、thesis或Git历史修改。

## 167. 2026-09-29：LDA/F1 + common-Gauss Rusanov保正混合原型

**作者：Codex；用户要求针对现有代码研究LDA+Rusanov。** 新增显式
RD_LDA_RUSANOV_BLEND=1（保正混合）/0（同Gauss3低阶对照），限定static/periodic/
1rank/equal timestep，RK两阶段同call。低阶构造Uin=Ubar-Phi_G/(3alpha)，增大alpha
直到admissible；dt sumalpha/S<=1。两支同总残差，完整F1/lumped时间修正共同受限。
每三角形使用同一标量限制所有节点/分量，按节点incident degree构造凸组合保正，
局部修正零和保持守恒。不裁剪rho/p/E；默认LDA/N和moving原型不改。

2000 compiled随机核/patch检查通过，原5项make check_rd通过。首次make用了缺NumPy
的system Python，在import失败；指定既有21cmfast Python后通过，属于环境问题。
冻结dirty源码+配置，独立构建mixed、low、flag-absent LDA，全部12个native运行完成，
60个新快照全部正/有限/静态位置不变，EOS一致，3个恒态缺陷5.55e-16。

相同glass128²/nearest21/Ehot1/pbg1e-6/gamma5/3/CFL.1/cap.01，最终t.05：
mixed4689步/705.06s，rho_min/max=.0191126/3.79111，径向均值峰2.79825，dE/E=-2.22e-16；
low2476步/388.58s，rho_min/max=.124614/2.00629，均值峰1.96123，dE/E=6.66e-16。
原梯形Rusanov几乎等同low。r<.05的mixed均压1.60741（解析1.60510），均rho.027686
（解析.004353，low.135722）。中心/耗散改善，但前沿外侧meanrho欠冲到约.6，vr散点
显著增加且有负值；pmin5.03e-12，K=p/rho^gamma最小仅初始下界的3.47e-5，527点
违反该下界。不是最终无振荡Sedov方案，下一步需要entropy/oscillation constraints。

全部9378 mixed+4952 low science stage检查通过，实际CFL最大.100857/.099992<1，
mixed correction预算最大缺陷8.44e-15。平均全域1.12%元素受限，主要在corrector。
独立平滑density-advection16²/32²/64²阶数2.1166/2.0327，mixed与LDA最大差2.45e-14；
这不是Yee/glass普遍二阶证明。完整剖面、中心细节和预算/limiter图已视觉检查。
档案`../local_runs/sedov_lda_rusanov_20260929_v1/`；详见
[报告](RD_LDA_RUSANOV_BLEND_20260929.md)。无运行中solver，无moving、thesis、COSMA
或commit/push操作。源码保留为可选实验，未提交。

## 168. 2026-09-29：区分LDA/Rusanov Sedov径向展宽与真实角向散点

**作者：Codex；用户追问为什么LDA scatter明显大于Rusanov。** 对既有static混合与
common-Gauss低阶最终快照作只读后处理，hash、IDs、坐标和dual面积核验通过；图中
蓝色是LDA/F1+保正混合，不是pure LDA。按dual面积加权，在dr=.005内去掉径向线性
趋势。.05<=r<.10远离激波，386点：径向速度RMS .158645/.00460087（34.48倍），
切向速度RMS .0655025/.00374668（17.48倍），径向均值.468728/.476766。改用box中心
仍有同样结论；更大内部区间也显著。故不能把散点全解释成更尖激波的径向投影。

低耗散保留/产生的非单调扰动与仅保正限制器相容；Rusanov显式黏性压制动量差异。
混合内区rho更低使v=m/rho对误差更敏感，但动量本身散布也增加，不能全归于除rho。
静态图不涉及edge flip。glass/离散注入、F1各自贡献尚未隔离；entropy bound缺失
不等于加上就必定消除速度散点。未改solver或运行新hydro。详见
[报告follow-up](RD_LDA_RUSANOV_BLEND_20260929.md)，可重现分析与JSON在原档案
`../local_runs/sedov_lda_rusanov_20260929_v1/analysis/scatter_audit.{py,json}`。

## 169. 2026-09-29：设计混合修正的熵下界与局部振荡约束

**作者：Codex；用户问如何增加约束并检查熵下界。** 对照现有kernel及Guermond等
§§4.1/4.6/4.7，给出保持triangle公共ell和完整F1修正的凸限制设计。熵用
Psi=E-|m|²/(2rho)-Kmin rho^gamma/(gamma-1)>=0；当前传入extensive Q，必须除以S，
或在M^gamma项加入S^(1-gamma)。先把common-Gauss Uin的要求从保正扩展到熵下界，
同步alpha/CFL，才能证明低阶起点可用；不能只凭以前的low输出未违规作保证。

密度/速度界取低阶凸分解的源状态和Uin辅助状态，corrector纳入U^n；不能只取旧
邻点极值，否则Sedov从rho=1、v=0开始会阻止膨胀与压力加速。速度界是另加的数值
约束，并非Euler maximum principle。光滑区需研究几何适配的O(h²)松弛；严格熵
下界和二阶兼容性不能直接声称成立。每阶段分开审计low/high/accepted，熵最小值
不等价于完整entropy stability。

复查既有快照hash：527个全局K<1e-6违规点全部位于r=.277602–.312356，中心r<.1的
K_min=89.371。因此全局熵floor不直接约束中心scatter，需局部熵/振荡约束对照。
完整[设计](RD_LDA_RUSANOV_CONSTRAINT_DESIGN_20260929.md)。本次为推导与只读诊断，
未实现新solver、未运行hydro、未修改thesis或提交Git。

## 170. 2026-09-29：试验RD文献的B/Bmax残差比值修正

**作者：Codex；用户要求优先尝试已用于RD的方法。** 核实Morton2023§2.2.3与
Ricchiuto–Abgrall2010§5.2，移植传统B/Bmax残差比值规则，以现有common-Gauss Rusanov
替代N低阶分支，外层保留已验证的守恒保正限制。新增显式B_SENSOR=1/2，仅限既有
static研究路径；没有自行加入熵或局部速度界，非RPJ/MOOD复现。

v1只把原修正乘1-theta，遗漏corrector替换旧predictor残差，contact阶1.3166/1.1066
暴露问题；两项Sedov在212s主动终止，returncode-15，完整档案与说明保留。v2保存
old LDA/Rusanov/accepted三分布，混合完整旧新RK残差，再相对SSP低阶候选作守恒修正。
2000原kernel/patch+1000sensor+1000独立full-RK对照通过，原5项make check_rd通过。

v2全部10native完成，50新快照正/有限/EOS一致/静态坐标不变，恒态误差5.55e-16；
contact16/32/64阶1.74527/1.85625（两方案相同），仍比原LDA误差大，不宣称Yee/glass
一般二阶。相同glass128²/21点/E1/pbg1e-6/gamma5/3/CFL.1/t.05：B3102步/458.08s，
Bmax2559步/378.64s。B raw rho_max10.0045而均线峰2.3794，有严重离群；Bmax raw2.1786，
均线峰2.1471（pureRusa1.9612，原混合2.7983）。内区.05<=r<.1去趋势vr RMS：
原混合.158645，B.0920415，Bmax.00387403，Rusa.00460087。Bmax减少散点约41倍，但耗散
仍强；core r<.05均压1.54876介于pureRusa1.44343与解析1.60510之间。

Bmax Kmin/Kinitial=.999770，47点超过1e-8阈值，最大熵下界欠缺.023%，不是严格保熵；
B为.0688545/56点。两组保存质量/能量误差到舍入，全stage正性/CFL通过。档案
`../local_runs/sedov_rd_bsensor_20260929_v2/`，四方案完整散点图及Bmax聚焦图已检查。
详见[报告](RD_SEDOV_B_SENSOR_20260929.md)。所有solver结束；无moving、thesis、COSMA、
commit/push操作。默认Config未改，新代码未提交。

## 171. 2026-09-29：LDA/Rusanov与B/Bmax改进的总开发记录

**作者：Codex；按用户要求汇总本轮改进。** 本节是 §§165–170 的统一交接摘要；
保留各节的推导、失败记录和验证细节。当前成果是 static RD 的可选实验路径，
尚未推广到 moving mesh、connectivity repair 或 hierarchical timestep。

### 已实现的改进及其适用范围

1. **统一高低阶总残差。** LDA/Gauss3/F1 与 Rusanov 使用相同的 Gauss contour
   residual。低阶辅助状态为 `Uin=Ubar-Phi_G/(3 alpha_T)`，增大 `alpha_T` 直到
   密度与内能可接受，并检查实际阶段 `dt sum_T(alpha_T)/S_i <= 1`。
2. **守恒且耦合保正的混合。** 限制完整空间/时间修正，每个三角形对全部节点和
   Euler 分量使用同一标量因子。修正逐元素零和；节点按 incident degree 形成
   可接受状态的凸组合。不通过裁剪密度、压力或能量维持正性。
3. **移植 RD 文献的 B/Bmax 残差比值。** `theta_k=|sum_i D^L_ki|/sum_i|D^L_ki|`，
   B 分量分别混合，Bmax 使用所有分量的最大值；外层继续保留上述保正限制。
   文献低阶 N 在本实验中替换为 common-Gauss Rusanov，采用守恒分量形式，未做
   characteristic projection，因此不能称为原文算法、RPJ 或 MOOD 的完整复现。
4. **修正完整 RK 混合。** v1 仅将既有修正乘以 `1-theta`，遗漏 corrector 中
   旧 predictor 分布的替换，导致 contact 收敛阶约 1.32/1.11。v2 保存旧 LDA、
   旧 Rusanov 和实际接受的 predictor 三组残差，按新的 theta 混合完整旧/新
   RK residual，再相对 SSP 低阶候选作修正。独立完整 RK 恒等式检查通过。
   v1 两项 Sedov 为主动终止（returncode -15），不是 hydro 崩溃；失败源码、
   输出及原因保留，未作为完成的科学对照。

编译选项：`RD_LDA_RUSANOV_BLEND=0` 为同 Gauss 低阶对照，`=1` 为保正混合；
在 `BLEND=1` 下，`RD_LDA_RUSANOV_B_SENSOR=1/2` 分别选 B/Bmax，不设则沿用
仅保正混合。当前限定 static、periodic、全网格 equal timestep、单 MPI rank、
同一次调用内完成的两阶段 RK、无源 hydro。默认 Config 未启用这些选项。
实现位于 `src/hydro/rd_lda_rusanov.h`、`src/hydro/residual_distribution_solver.c`
及 `defines_extra`；检查与运行入口为 `tests/rd/test_lda_rusanov.py` 和
`examples/Sedov_2d/run_blend.py`，分析入口为 `examples/Sedov_2d/analyze_bsensor.py`。

### 匹配 Sedov 对照的主要结果

四种方法使用相同 glass 128²、单位周期盒、初始 rho=1/v=0、gamma=5/3、背景
p=1e-6、最近 21 点注入热能 1（按 RD dual mass 归一化），演化到 t=.05。
CFL=.1、步长上限 .01，由 CFL 自适应选择全局共同二进制步长，实际步数不同。
径向原点取初始注入能量质心 `(0.5006033127941537, 0.4999065173644349)`。

| 方法 | 密度径向均值峰 | 原始密度最大值 | 内区径向速度散点 RMS | 中心均压 | 最小 K / 初始 K_min |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原仅保正 LDA/Rusanov | 2.79825 | 3.79111 | .158645 | 1.60741 | 3.47320e-5 |
| 分量 B | 2.37938 | 10.0045 | .0920415 | 1.57331 | .0688545 |
| 标量 Bmax | 2.14706 | 2.17861 | .00387403 | 1.54876 | .999770 |
| common-Gauss Rusanov | 1.96123 | 2.00629 | .00460087 | 1.44343 | 1 |

密度均值峰采用 dr=.005 的不加权分箱均值；速度 RMS 在 `.05<=r<.1` 的相同
386 个节点上按 dual area 加权，并逐径向 bin 去掉线性趋势。中心均压为 r<.05
的 130 点不加权平均，同节点解析均压为 1.60510。`K=p/rho^gamma`，初始下界
为 1e-6。原混合的内区散点是真实角向扰动，不能全归于尖锐激波的径向投影。

Bmax 将该内区径向散点降低约 41 倍，中心压力比纯低阶更接近解析值，但激波
仍明显耗散；分量 B 的密度离群值达到约 10，当前不适合作为 Sedov 候选。
Bmax 的 K 下界仍有最大 .0230% 欠缺，47 点超过相对 1e-8 的判据，不能当作
舍入误差或严格保熵结果。正性、全局熵最小值和完整离散熵不等式是不同性质。

### 已完成的验证与保留问题

- 原保正混合完成 12 个 native runs / 60 个新快照；v2 B/Bmax 完成 10 个
  native runs / 50 个新快照。保存状态有限且正、EOS 一致、静态坐标及 IDs
  不变；恒态缺陷 5.55e-16。B/Bmax 全部阶段的正性/CFL 检查通过，保存的
  质量/能量误差在舍入量级（最大绝对能量漂移分别 1.11e-15 / 2.22e-16）。
- 4000 个 compiled cases 覆盖低阶辅助状态/保正 patch、B 比值/共同总残差/
  单位缩放、完整旧新 RK 恒等式；原有 5 项 `make check_rd` 在最终源码通过。
- 独立规则网格 contact：rho=1+.2 sin(2pi(x+y))、v=(.37,-.21)、p=1、
  gamma=5/3、单位周期盒，16²/32²/64²，t=.1，步长上限 1/8192。
  原保正混合的 density L1 阶为 2.1166/2.0327，场值与 LDA 相差不超过
  2.45e-14；B/Bmax 阶为 1.7453/1.8563，误差更大，仅显示趋近二阶，不能
  外推为 Yee、glass 或 moving mesh 的一般二阶结论。
- 熵下界和局部振荡约束目前只是 §169 的设计，尚未实现。若继续，应分别
  研究 characteristic limiting、Rusanov-PSI/stabilization 或 RD-MOOD，
  同时保留光滑精度检查；现有结果不代表已解决 moving topology 的守恒与保正。

详细资料：[保正混合](RD_LDA_RUSANOV_BLEND_20260929.md)、
[熵与振荡约束设计](RD_LDA_RUSANOV_CONSTRAINT_DESIGN_20260929.md)、
[B/Bmax 文献、RK 公式及完整结果](RD_SEDOV_B_SENSOR_20260929.md)。
冻结档案位于工作区 `local_runs/sedov_lda_rusanov_20260929_v1/`、
`local_runs/sedov_rd_bsensor_20260929_v1/`（失败尝试）及
`local_runs/sedov_rd_bsensor_20260929_v2/`（修正后完成）。
[完整四方法图](../../local_runs/sedov_rd_bsensor_20260929_v2/analysis/rd_bsensor_profiles.png)
保留 B 的所有离群点；[Bmax 对照图](../../local_runs/sedov_rd_bsensor_20260929_v2/analysis/rd_bmax_comparison.png)
展示 Bmax、原混合和低阶。

本次仅整理总日志及 context 导航，没有新增运行或修改 solver/thesis。
全部 native solver 已结束；开发源码仍未提交，未执行 commit/push。

## 172. 2026-09-29：4.3.3 Ongoing work本地草稿与审核PDF

**作者：Codex；用户明确要求暂不写Sedov结果，先起草edge flip守恒问题与moving
hierarchical timestep进展。** 论文仓库已在上一轮快进至GitHub `1bb457f`，保留本地
1.401对应velocity error的更正。本轮仅编辑Chapter4：在4.3.2之后加入正式编号的
4.3.3 Ongoing work（四段），将4.3.1已落实的红字TODO换为该节交叉引用。
原Sod/Yee/Gresho正文、其他章节、bibliography及末尾红色备选材料保留。

草稿依据本日志 §§10–11、35、122、159及已有红色数学草稿，分别陈述：保持节点U
跨flip并不保证积分总量守恒；局部守恒修正的负压风险；modified coefficient到
endpoint area的另一项守恒误差；粗时间区间被flip截断与新三角形缺少历史的问题；
按实际triangle birth/last-integrated time闭合完整old incident stars、守恒转移、
重启区间并限制predictor实际区间兼容性的尝试。明确独立Euler实验的舍入级守恒
不等于native AREPO已完成集成，也不保证正性、精度或动态bin/MPI适用性。
未加入Sedov数据、图或结果段落，论文当前数值结果仍说明采用global equal steps。

在隔离目录用XeLaTeX编译全论文（251页）。首次构建读到论文目录的旧bbl，随后
在隔离目录重新运行BibTeX并优先读取新bbl，再完成两次XeLaTeX；最终没有未定义
引用/文献或缺字警告。已有其他页的排版警告未作越界修改。摘出物理页191–192，
即印刷页169–170（4.3.3起始页也包含前一节Sod讨论），逐页渲染检查通过。
提取检查最初按固定换行匹配结尾字符串失败，核实文本完整后改为规范化空白再检查；
不是编译或正文缺失。

审核文件：[chapter4_3_3_ongoing_work_review.pdf](../../output/pdf/chapter4_3_3_ongoing_work_review.pdf)。
完整编译、草稿快照、diff、来源信息与渲染在工作区
`local_runs/thesis_ongoing_work_20260929_v1/`。
本地草稿待用户审核，未commit/push或同步Overleaf；未修改solver、未运行hydro。

## 173. 2026-09-29：详述basis change导致的守恒变化，明确repair仍为实验功能

**作者：Codex；用户要求把4.3.3的物理/数学原因写清楚，并说明正在尝试repair。**
扩充该节开头：用沿用的P1基函数psi_i写出old/new两组U_h展开，明确比较的是同一
物理时刻、相同节点位置下的两种connectivity。节点U不变，但basis的support与
gradient改变，故三角形内部重构不同。利用积分psi_i等于median dual area，加入
Delta Q_basis = integral(U_h_new-U_h_old) = sum_i(Snew_i-Sold_i)U_i，并说明总面积
不变只保证uniform cancellation，不能保证一般非均匀状态的总量守恒。

新增repair的具体含义：比较受影响patch的新旧basis-weighted总量，再向节点分配
补偿修正以恢复该patch的守恒。显式写明这是正在测试的experimental feature，
未在4.3.2展示的数值测试中启用；保留unrestricted repair的负压风险和独立的
modified-coefficient/endpoint转换误差。hierarchical段落原文保留。

继续采用本地草稿、不加Sedov结果的范围。档案更新为工作区
`local_runs/thesis_ongoing_work_20260929_v2/`；v1原审核PDF已另存为
`local_runs/thesis_ongoing_work_20260929_v1/review_v1.pdf`。
复用已核验且引用内容未变的bibliography，隔离XeLaTeX编译；新增两组公式编号
4.50/4.51。当前审核PDF扩为印刷页169–171；仅在4.3.3局部设置widow penalty，
避免段落结尾孤行跨页。未改其他章节或solver，未commit/push。
最终全论文252页，无未定义引用或缺字警告；三张最终审核页已逐页检查，公式无
越界，源码与归档hash一致。审核PDF仍使用上一节的固定链接，内容已更新。


## 174. 2026-09-29：拉取thesis远端Lay Summary并合并本地4.3.3提交

**作者：Zhenyu Wu 与 Codex（GPT-6）；用户明确要求拉取GitHub/Overleaf更新并与
本地4.3.3 Ongoing work提交合并。** 论文仓库main原为`c3aa858`，跟踪文件干净；
fetch origin得到`9e428fd`（write Lay Summary），共同基点`1bb457f`。远端只改
`zhenyu_thesis/thesis-frontmatter/abstract.tex`，本地提交只改Chapter4，无冲突。
用fetch+merge完成pull的获取与合并，生成本地merge commit `b6786ed`，保留两个
原始提交及其历史；没有rebase、force push或直接操作Overleaf。

核验最终tree等于预计算merge tree；Chapter4与`c3aa858`逐字节一致，摘要与
`9e428fd`逐字节一致，其余跟踪文件不变。30个未跟踪文件的SHA256及两个既有stash
全部保持不变。diff --check仅报远端摘要第5行既有行尾空格，保留原文未清理。
本地main现在比origin/main领先2个提交（本地草稿+merge），落后0；跟踪工作树干净。
按本次Git同步范围未重新编译PDF，未push；现有PDF仍为之前的构建。

保留分支`backup/pre-thesis-merge-20260929-c3aa858`，状态、两侧patch及核验记录在
`../local_runs/thesis_merge_20260929_214454/`。AREPO源码与已有未提交研究工作未改；
本轮仅追加此日志并更新context的thesis同步状态。


## 175. 2026-09-29：轻度润色Lay Summary，保留原叙述语气

**作者：Codex（GPT-6）；用户提供三篇既有示例，明确要求稍作润色且不大改语言
风格。** 在论文main `b6786ed`上，仅修改`thesis-frontmatter/abstract.tex`中
Lay Summary部分。保留原开头、观测/理论对照、第一人称叙述，以及早期黑洞与
动力摩擦加热→RD/AREPO的研究顺序；修正语法和搭配，将原长首段拆开。用简短
wake解释gaseous dynamical friction；为Lyman–Werner、baryonic matter及bulk
velocity换用/补充浅白说明。将almost all galaxies等过强表述收敛，保留主要
定量信息；没有新增研究结果。纯文本改写，未作新的文献审查。

源文按空白分词约482→528词（含标题/TeX），主要增加来自术语解释。正式Abstract
从章节命令起逐字节保留；全部其他跟踪论文文件hash不变，4.3.3保持原样。
未stage、commit、push或操作Overleaf；后续仍需按正常流程同步。

复用论文preamble/customisations，在隔离目录用XeLaTeX编译Lay Summary两页；
无LaTeX/引用/缺字/overfull/underfull警告，两页已渲染并检查。完整master.pdf未
重编译。审核PDF：[lay_summary_review.pdf](../../output/pdf/lay_summary_review.pdf)。
原文、修改后全文、diff、构建和检查记录在
`../local_runs/thesis_lay_summary_polish_20260929_v1/`。


## 176. 2026-09-29：Chapter4结构定型，删除章末红字草稿

**作者：Codex（GPT-6）；用户确认Chapter4整体结构已定型，4.3.2后续可能补充
Sedov等数值结果，connectivity change只作为ongoing work简述，不再保留红字
层次的详细推导。** 当前论文main/origin-main均为`8cfb119`（用户已提交同步
Lay Summary），起始跟踪工作树干净。在Chapter4章末删除整个431行红字块及前导
空行：Implementation details retained for revision与Alternative implementations
(to delete)。删除的25个label未被保留论文TeX正文引用。4.3.3及其之前正文逐字节
保留（仅规范文件末尾空行）；所有其他跟踪/未跟踪论文文件hash与两个stash保持不变。
原始红字同时保留在Git历史及本次档案`chapter4_removed_red_draft.tex`中。

4.3.1与4.3.3已经说明当前equal-step/one-rank范围、basis-change守恒误差、独立
endpoint-weight误差、repair实验状态及moving hierarchy待完成内容。删除详细草稿
不等于这些问题已解决；不增加Sedov结果，也不将备选方案迁回正文。根据本次用户
决定，更新AGENTS.md和context.md，替换旧的“Chapter4仅为数学工作草稿”定位，
详细研究继续留在开发记录；explicit thesis-edit授权边界不变。

从当前tracked源码冻结独立完整工程，使用LaTeX编译技能的XeLaTeX/latexmk重建全
论文及bibliography。成功输出242页，零未定义引用/文献和缺字警告；保留未编辑
正文中的11处既有overfull hbox报告，未越界修改排版。Chapter4为物理页161–194，
印刷页138–171，共34页；末尾169–171及Chapter5起始172已逐页渲染检查，衔接正常。
审核PDF：[chapter4_clean_review.pdf](../../output/pdf/chapter4_clean_review.pdf)。
完整PDF、源码快照、删除备份、diff及核验在
`../local_runs/thesis_ch4_remove_red_20260929_v1/`。论文目录原master.pdf未覆盖。
本轮修改未stage/commit/push，未操作Overleaf或运行hydro。


## 177. 2026-09-29：讨论Chapter5的双主题总结与future work结构

**作者：Codex（GPT-6）；用户提供约三页的结论章示例，提出按gaseous dynamical
friction与RD hydro solver两部分，各自写research summary和future work。** 本轮
只读示例、当前Chapter2/3结论、Chapter4实现/结果及Ben Morton结论章；Chapter5
仍只有标题，未起草或修改论文。Ben的Chapter6确实以Dynamical Friction和RD Solver
分节，并在各主题中接续future directions。建议本论文采用同样主题组织，篇幅先
控制约3–4页，再按实际模板调整。

用户提出的DF后续方向：在宇宙学背景下模拟subhalo与gas的动力摩擦，加入gas
self-gravity、chemistry与cooling，检验解析模型的适用范围。讨论建议将检验指标
具体化为轨道能量损失、实际加热及空间沉积、H2生成/冷却、塌缩与碎裂，允许wake
压缩促进冷却而改变净效应；不预设模拟必定证实DF抑制恒星形成。

用户提出的RD后续方向：moving-mesh hierarchical timesteps与MPI、进一步3D
测试、适用于不同流态的通用blended scheme（尤其shock识别与spurious oscillation
控制），远期耦合引力和其它astrophysics modules。写作时区分已完成的static
hierarchy/MPI与待完成的moving扩展；区分既有standalone3D框架与AREPO-RD的3D
扩展/验证；保留connectivity conservation作为moving扩展的前置问题，但不重复
4.3.3的推导。RD尚未用于完成Chapter2的宇宙学DF数值验证，两条路线的结合是展望。
这些是用户拟议方向与本轮结构建议，尚未写入正式Chapter5正文。


## 178. 2026-09-29：通读当前论文并在对话中起草Chapter5

**作者：Codex（GPT-6）；用户要求通读全篇，按双主题结构写Chapter5草稿，明确
要求仅在对话输出、暂不加入thesis。** 阅读当前master引用的Lay Summary/Abstract、
Chapters1--4全文和Appendix1，并复核用户提供的结论章示例。草稿以gaseous
dynamical friction与RD hydrodynamics为两节，各含research summary和future
work；只总结现有正文结果，不纳入尚未加入论文的Sedov开发结果。

DF部分涵盖TNG50 evolved SHMF、主要贡献的较大质量比subhaloes、约两数量级的
加热散布、低红移大质量halo与高红移H2冷却比较、径向分布的限制。下一步为宇宙学
subhalo--gas模拟，加入self-gravity/chemistry/cooling，检验实际能量传递、热化和
空间沉积及冷却/塌缩响应，不预设一定产生DCBH或抑制恒星形成。

RD部分区分既有standalone框架与本人的测试/AREPO实现，概括静态LDA/N/B、
hierarchy/MPI及移动网格初步测试。移动connectivity与endpoint-weight守恒问题
只简述；moving hierarchy/MPI、3D扩展验证、shock识别与振荡控制的通用blend、
引力和其它物理模块耦合均保留为future work。Chapter1末尾提及已完成Chapter4
DF-with-cooling的旧outline不作为结果依据；正文未改。

本轮未修改任何论文文件、未编译、未commit/push；Chapter5仍只有既有标题。
保留上一轮Chapter4删除红字的工作树修改以及所有无关代码/文档工作。


## 179. 2026-09-29：讨论Overleaf connectivity段落的逻辑与措辞

**作者：Codex（GPT-6）；用户保留Chapter5草稿不动，提供Overleaf新版ongoing
work，询问need not cancel及uniform-flow结尾的含义。** 仅提供对话中的解释与
替换文字，未拉取/修改thesis。说明need not cancel表示“不一定抵消”，并非“不
需要抵消”；建议以非均匀场跨flip保留节点值仍可能改变积分总量为主线，去掉结尾
突兀的uniform-flow/implementation conversion回指。四点不同不意味着必然出错：
若各守恒分量来自同一个affine场，两种P1插值仍相同，因此保留generally/may。

median dual area等于basis函数积分，故面积权重跳变与basis change为同一机制；
重新计算面积不等于已完成守恒转移。核对Springel2010原文，Voronoi邻接关系也会
改变，但旧面收缩至零、几何连续；对比应限定为当前Delaunay-RD与Voronoi-FV。
按用户意图可将此段聚焦edge flip，不再展开midpoint问题。复核本日志§159：
repair显著降低早期Sedov质量/能量漂移，支持该阶段connectivity贡献重要；§128
等测试未单独归因，不将其推广为所有算例的误差主次，也不据此断言Arpaia形式
天然无须考虑其它守恒误差。未运行新的数值试验。


## 180. 2026-09-30：在本地润色Chapter4 connectivity ongoing work

**作者：Codex（GPT-6）；用户授权将上一轮讨论的措辞应用到本地论文。** 本地
仍为较早版本，故以用户贴出的Overleaf段落及§179讨论为依据，只更新Chapter4
4.3.3的connectivity部分。补入四点共圆的flip事件及Delaunay-RD/Voronoi-FV的
几何对比，引用已有Springel2010；明确重算median dual areas本身不保证守恒。
将need-not-cancel及uniform-flow回指改为非均匀P1场跨flip后积分可能改变的直接
说明，保留generally/may限定。按用户的范围取舍，删除此段独立midpoint/endpoint
误差讨论；4.3.1已有的一般守恒限制说明未改，也未宣称其它误差已经消失。

两组公式与label、repair的实验状态/负压限制、之后的hierarchical timestep
正文均保留。以编辑前tracked-file SHA256核验，只有Chapter4变化；前文及hierarchy
逐字节一致。此前删除章末红字的未提交修改保持不变；Chapter5及其它章节未动。

冻结当前tracked源码，使用LaTeX编译技能在隔离目录以XeLaTeX/latexmk重建完整
242页论文，引用/文献全部解析，无缺字；11处既有overfull报告与上一版数量一致。
用PDF检查流程逐页查看物理页192--194（印刷169--171），公式、分页、引用正常。
原论文目录master.pdf未覆盖，未stage/commit/push或访问Overleaf；未运行hydro。
源文备份、hash、此次diff、冻结工程、编译记录及页面PNG位于工作区
`local_runs/thesis_connectivity_polish_20260930_v1/`。


## 181. 2026-09-30：简化moving hierarchical timestep的ongoing-work叙述

**作者：Codex（GPT-6）；用户认为无图/公式的两段实现说明过于技术化，要求突出
问题和可能思路。** 在本地Chapter4 §4.3.3只替换hierarchy两段：不同三角形更新
时间不同，flip可能在原时间步结束前替换三角形，不一致的续接可能遗漏/重复演化；
候选思路为受影响区域先推进至flip时刻，再守恒转移到新三角剖分并从该时刻继续。
去掉timebin规则、triangle birth/last-integrated time、incident stars、predictor
区间兼容性及独立Euler实验的细节，保留AREPO集成/验证与并行仍待完成，以及
本章moving测试所有节点使用同一时间步的范围。未把候选方案写成完成的算法。

本轮开始时用户已提交章末红字删除，thesis HEAD为`beb977d`，领先origin/main一个
提交；前轮connectivity润色仍为工作树修改。本轮未stage/commit/push，只改指定
两段，前文与章尾逐字节保留，其它tracked论文文件hash未变，diff --check通过。
纯文字修改未重新编译，§180的PDF对应上一次文本；未改Chapter5或solver。
备份、hash和本次diff在工作区`local_runs/thesis_hierarchy_prose_20260930_v1/`。


## 182. 2026-09-30：将4.3.1末段改为数值测试与ongoing work的简短过渡

**作者：Codex（GPT-6）；用户要求4.3.1末段edge-flip说明更自然，与已有4.3.3
衔接。** 删除该段old-area/new-connectivity重标定细节，改为三句：下一节展示
当前实现的数值测试；connectivity change的守恒处理仍需完善；该问题及hierarchical
timestep扩展统一指向4.3.3。保留未完成守恒处理的范围说明，不再在overview
重复ongoing-work机制。其它正文、公式和4.3.3均未改。

本轮开始时用户已将前两轮4.3.3润色提交/同步为`12e9451`，thesis跟踪工作树干净。
git diff确认本轮仅替换4.3.1末段，diff --check通过。纯文字调整未重编译，未
stage/commit/push，未操作Overleaf或solver；修改前版本保存在既有Git提交中。


## 183. 2026-09-30：全文公式句末标点检查与修正

**作者：Codex（GPT-6）；用户明确授权全文处理SK提出的公式缺少句末标点问题。**
本轮thesis已由用户提交/同步为`99df79a`（main/origin-main），包含此前Chapter4
润色与Chapter5；跟踪工作树起始干净。遍查master包含的前置页、Chapters1--5和
Appendix1，排除注释中的旧公式，共248个有效陈列公式块。结合前后文判断句末
句号、where/with/and等衔接逗号及多行独立等式的分隔，不在一个跨行等式中
机械插入标点，也不把`\right.`的不可见定界符误认作句号。

修改93个公式块：Chapter1 66、Chapter2 20、Chapter3 5、Chapter4 1、Appendix1 1。
大部分为补漏，另纠正少量句号/逗号与后文不匹配处；Chapter3线性平流示例补
逗号后，将接续的The改为the。Chapter3两个公式分别继续接in 2D和for限定
条件，保留不加句末标点的连续写法。数学内容、labels、环境/编号及全部sk/zw
批注保留，包括本次已处理的SK原批注。仅清理本次改动行的末尾空格，其它正文、
Chapter5、参考文献及图均逐字节保持。diff --check及全tracked-file SHA256核验通过。

按LaTeX编译技能冻结源码后，以XeLaTeX/latexmk隔离编译完整245页论文，退出码0，
无未定义引用/文献、无缺字。编译仍报告11处既有overfull hbox，与前次完整编译的
位置相同；其中Chapter1式1.25/1.26补句号后宽度分别从5.86183/12.58615pt增至
8.47292/15.19724pt，未借此扩展到重排长公式。逐页查看物理页39、40、44、51、55、
72、83、141、142、184、204、205，新增标点、嵌套方程/分段函数与文字衔接正常，
无新增裁切或重叠。原论文目录master.pdf未覆盖，未stage/commit/push/操作Overleaf，
未运行hydro。备份、248块清单、修改明细、diff、hash、编译记录和PNG保存在工作区
`local_runs/thesis_equation_punctuation_20260930_v1/`。

## 184. 2026-09-30：Sedov激波的RD文献处理与moving RD优化方向，一阶MMFV诊断

**作者：Claude Code（Opus 5.5）；用户认为现有RD Sedov不如MMFV/SWIFT，要求查找
RD文献对shock/Sedov的处理并评估优化空间；用户补充Morton2023 static LDA也不行，
MMFV单cell注入也能跑。** 先澄清：现有moving RD Sedov是纯一阶
`RD_RUSANOV_LOW_ORDER`+lumped RK2；LDA/Rusanov混合与B/Bmax只在static上运行过。

文献（原文核对）：Deconinck–Ricchiuto综述用LDA/N blending或limited(PSI)格式，
系统按特征分解；Abgrall–Bacigaluppi–Tokareva 2019用特征变量Rusanov-PSI+Θ混合
+Burman jump稳定化，测试W–C blast、Mach3台阶等，无Sedov；Paardekooper2017在Noh上
指出较低耗散的blend会失败或需N后备，柱面blast中N≈HLL、B误差更大；Morton2023
Sedov中LDA不稳定、blend退化为N；Campoli等2017 ALE RD捕获激波时LDA/LDAN下游
不光滑；SGH RD+MARS完成Sedov但结构不可移植；与我们P1 ALE最接近的是
Guermond–Popov–Saavedra2020：边局部graph viscosity+密度/比熵局部界的convex
limiting（Noh、W–C等，固定connectivity）。综述§3.6.1给出中位对偶FV配任意守恒
通量即为RD（元素总残差为梯形Φ_T），因此Riemann通量可作RD低阶格式。
Ricchiuto–Abgrall2010及Arpaia ALE报告全文本机无法下载，未声称其细节。

机制：MMFV单cell稳定来自逐面精确Riemann问题（一阶Godunov保正）、负ρ/p时丢弃
face外推（finite_volume_solver.c:1330）及0.9上游质量的通量限制；Roe型线性化
（N/LDA）近真空不保正（Einfeldt1991）。Rusanov恢复保正，但α≈cℓ/2对ρ/m/E同等
施加，在准拉格朗日网格上质量扩散由声速而非|u−w|决定，且随膨胀核心单元变大。

新增诊断（非生产配置）：`Config_MMFV_moving_first_order{,_hllc}.sh`=原MMFV Config
+DISABLE_SPATIAL/TIME_EXTRAPOLATION(+RIEMANN_HLLC)；`run_mmfv_first_order.py`冻结
HEAD2858d43+工作树patch+untracked文件，独立BUILD_DIR，复用二阶MMFV的hash核验IC和
参数（仅改路径）。uniform缺陷2.05e−13；science 970/961步、126/118s，全部快照正/
有限，质量能量守恒至舍入。t=.05结果：一阶exact/HLLC raw ρmax3.434/3.427，
均线峰3.099/3.070，r<.05面积平均ρ .0276/.0280（3–4样本），中心p1.670/1.687；
二阶MMFV 3.971/3.302/.0300/1.596；moving Rusanov RD 2.630/2.428/.1977/1.721
（核心同为3样本）。故一阶到一阶，RD→MMFV使均线峰2.43→3.1、核心密度降7倍；
MMFV一阶→二阶仅3.10→3.30。主要缺陷是低阶耗散形式，而非缺二阶或核心采样稀疏；
HLLC与exact一阶几乎相同。限制：Voronoi与median dual、前向Euler与RK2、重连守恒
差异未隔离，结论为推断。

建议（未实现）：①在w_T坐标系用边中位对偶HLLC通量替换Rusanov低阶（总残差与现有
梯形ALE Φ_T相同，RK2/b_i检查可沿用；需保证波速上界与失败即停的星态检查）；
②再将static凸限制LDA/F1修正移植到ALE，并加局部ρ界与比熵下界（参照GPS2020及
§169设计），仅保正不足；③独立处理重连的守恒保正remap。单调B/Bmax/Bx调参、以N为
保正终点、扩大注入或裁剪不推荐。完整对照表、公式与来源见
[报告](RD_SEDOV_SHOCK_LITERATURE_OPTIMIZATION_20260930.md)。档案
`../local_runs/sedov_mmfv_first_order_20260930_v1/`（source/binary/Config/header/
linkage/IC/参数/日志/verification.json/剖面图，图已目视检查）。未改RD solver、默认
Config或thesis，未commit/push；2次native build与4次run均完成，无活动solver。


## 185. 2026-09-30：按用户十点意见处理Chapter1及Abstract红字

**作者：Codex（GPT-6）；用户明确授权逐项修改，要求保留本地git diff供检查。**
thesis起始HEAD为`447c9a0`（用户已提交§183标点修改，main领先origin/main一个
提交），跟踪工作树干净。本轮论文仓库仅修改Chapter1、formal Abstract和
`chapter1bib-cosmology.bib`，没有修改其它章节或Lay Summary。

1. Abstract明确将gaseous DF heating表述为可能延迟PopIII形成、与LW背景共同
   有利于DCBH种子形成的新机制，仍以analytic model结果为基础，未声称完成形成模拟。
2. decaying mode改为标准结构增长计算通常保留growing mode，其相对贡献在物质
   主导时期衰减；没有称其unphysical，也没有声称模拟初始条件的transients永无影响。
3. 按要求采用Gaussian with only slight deviations措辞，限定于primordial density
   field，并将给出的Gaussian联合分布及two-point完整描述限定为Gaussian近似。
4. 删除missing-satellite问题的孤立句及该处引用，保留subhalos/satellites/HOD背景。
5. 直接引入Hubble sequence，新增Hubble1926，ApJ64,321--369，DOI10.1086/143018。
6. 椭圆星系允许有序旋转和随机运动，形态不独自决定动力学支撑；新增Cappellari
   et al.2011 ATLAS3D I与Emsellem et al.2011 III，后者直接支持许多形态椭圆星系
   是fast rotators。正文不增加样本比例或详细分类标准。
7. 删除已经解决的公式句末标点SK批注，保留上一轮全部公式修正。
8. 保留式1.82，明确观测KS law为面密度关系、模拟需要局部体积率；补充竖直结构/
   有效EOS假设，以及Schaye & Dalla Vecchia2008通过压力处方复现输入KS law的
   slope/normalization/threshold。复用已有BibTeX条目。
9. DF理论段落增加which will be presented in Chapter2，使用已有chapter_2 label。
10. Outline更新为当前DF analytic model/散布与空间profile、本人static RD测试、
    AREPO静态hierarchy/MPI及moving初步测试/ongoing work；删除“Chapter4已做含
    Grackle cooling的DF模拟”旧计划。保留Ben Morton原代码与本人测试的归属，
    Chapter5对应两条研究线的总结与展望。

核对了Hubble1926原文、ATLAS3D I/III和Schaye2008原论文，以及Planck2018/Crocce2006
相关论述；三条新增文献的作者、卷页、DOI经Crossref/ADS/出版页核验。公开来源URL
与Crossref元数据存于档案。已处理的10条sk/zw批注全部移除，其它章节批注不动。

全tracked-file hash检查仅上述3文件变化；所有Chapter1陈列公式及labels逐字节
保留，Lay Summary/Abstract其余段落和其它章节不变。新增cite keys无重复，
git diff --check通过。冻结源文以XeLaTeX/latexmk隔离编译完整246页，退出码0，
无未定义引用/文献、无缺字。overfull hbox从11降为10（删除含长URL的SK批注），
保留原有zwicky1933die空journal警告。检查物理页4、5、28、31、61--63、69、70、
215、219、223，文字、公式和新增文献排版正常。未重排原有Abstract/章末余页，
未覆盖根目录master.pdf，未stage/commit/push或操作Overleaf，未修改solver/运行hydro。
备份、hash、diff、资料、冻结源码、编译记录与PNG在
`../local_runs/thesis_ch1_comments_20260930_v1/`。保留并行写入的§184及其context条目。

## 186. 2026-09-30：阅读thesis与删除红字，实现边HLLC低阶RD并完成Sedov原生测试

**作者：Claude Code（Opus 5.5）；用户要求先读MyThesis（含两个delete red text提交）
和代码，判断§184第一步是否与现有AREPO相容，可行则测试。** 读thesis main`447c9a0`
的Chapter4全文、Chapter5及Chapter3分布格式/时间步部分，逐行读`e4fcd84`（§4.2
备选：element co-moving frame与Galilean矩阵G(b)、守恒/Arpaia残差差、Campoli端点
质量）与`beb977d`（章末实现细节：Q=mU与D_i账本、重连rebase与端点换算两项缺陷、
RD CFL、Voronoi-cell、true predictor、拓扑算子、moving hierarchy）。结论：HLLC核
保持Arpaia残差的同一元素总量½ΣG_j·n_j（w=σ̄_T），在核内用G(σ̄_T)做Galilean变换；
不改D_i/账本/重连，故不能消除端点与重连缺陷；在Chapter3分类中属FV-RD而非MU。

相容性：`RD_RUSANOV_LOW_ORDER`已提供ALE几何、lumped RK2、阶段CFL/b_i/正性检查与
时间步钩子，只需替换单元核与每顶点系数。新增`src/hydro/rd_hllc.h`与显式选项
`RD_LOW_ORDER_HLLC`（必须配合RD_RUSANOV_LOW_ORDER）；solver仅改include/guard及
时间步选择和阶段装配两处调用；defines_extra加两宏。中位对偶面ν_ij=(n_j−n_i)/6
（i→j），φ_i=Σ_j[H(U_i,U_j;ν_ij)−G(U_i)·ν_ij]，H为w_T坐标系HLLC（Einfeldt/Batten+
Davis波速，Toro星态，星态不可接受即中止）；每对只算一次，右侧为跳量减左侧，
阶段系数Σ|ν_ij|s_ij。A3断言保证内法向，核另拒绝顺时针输入。

核测试`tests/rd/test_hllc_positivity.py`（4000例，ρ1e−3–1e3、p1e−6–1e3、|v|,|w|~3）：
守恒3.8e−16，对独立Python HLLC2.7e−13，Galilean协变4.3e−12，系数限内前向步恒正，
均匀态与相对w静止的接触间断残差为零，顺时针拒绝；原5项make check_rd通过。测试
框架两处设置错误已修正（-Werror误报未用Rusanov函数；取负法向无法由法向判定）。

原生`../local_runs/sedov_hllc_20260930_v1/`：冻结HEAD2858d43+patch+untracked，
HLLC_static/moving与无flag Rusanov_moving三独立binary；IC与参数与既有Rusanov存档
逐字节一致。uniform缺陷5.55e−16/6.66e−16/1.11e−15；无flag Rusanov重放与存档五个
快照**逐位相同**。7次运行全部返回0，8850/4884/5716个science stage全部通过正性/
CFL(最大.110)/b(最小.4947)检查。t=.05（21点）moving HLLC：raw ρmax3.413、均线峰
2.980、r<.05面积平均ρ .0276、中心p1.714；moving Rusanov 2.630/2.428/.1977/1.721；
一阶MMFV 3.434/3.099/.0276/1.670；二阶MMFV 3.971/3.302/.0300/1.596。static HLLC
2.461/2.328/.0309/1.531（Rusanov static 2.002/1.957/.1360/1.444），守恒至舍入。
单个热点moving HLLC无repair/floor完成t.05，均线峰2.999。

结论：边HLLC把moving RD核心密度降至与一阶MMFV相同，峰值接近一阶MMFV，证实主要
缺陷是Rusanov耗散形式。未解决：空间一阶（离二阶MMFV峰3.30与中心p仍有差距）；
moving预算仍漂移（21点质量−.329%、能量+.698%；1点−.335%/−1.606%，能量非单调），
来自未改动的重连与端点换算项，不归因于核，也不声称一般更小；仅5个快照采样；
无MPI/hierarchy/repair；未测平滑精度与Sod接触。静态运行步数4425>Rusanov3051。
详见[报告](RD_SEDOV_HLLC_LOW_ORDER_20260930.md)，图已目视检查。下一步：ALE上凸限制
LDA修正（Gauss3−梯形边修正、局部ρ/比熵界），再做守恒保正重连remap。未改thesis、
默认Config，未commit/push；无活动solver。

**§186补充（用户追问“HLLC-RD是哪篇论文、是否仍是RD”）：** 未找到提出“HLLC-RD”
的论文，该名称只是本次构造的简称。依据是Deconinck–Ricchiuto综述§3.6.1（中位对偶
一阶FV配任意守恒通量即为FS/RD格式，元素总残差为梯形Φ_T）及Abgrall2017的RD–通量
等价；HLLC出自Toro等1994，波速取Einfeldt1988/Batten1997。结构上是RD：元素残差在
单元内沿三条中位对偶线段按HLLC涨落A⁻ΔU/A⁺ΔU拆分且和为Φ_T，即一维Roe涨落分裂的
多维类比；但它不是MU/LP格式，属一阶FV-RD，与Rusanov/LxF地位相同。论文应称为
“涨落分裂形式的一阶保正后备格式”，RD的多维特征需由第二步限制后的LDA修正提供。
报告§5.5已补充。无代码或运行变更。

**§186再补充（用户要求用thesis Figure 4.2解释代码实际做法）：** 当前Figure 4.2为
“Node timebins and triangle residual scheduling”（节点A–E、三角形T1–T3）。新增示意
脚本`examples/Sedov_2d/plot_hllc_schematic.py`，输出存档`analysis/hllc_rd_schematic.png`
（沿用该图节点布局，几何仅示意）：代码按Delaunay三角形循环，不使用Voronoi面；
每个三角形先算Φ_T，再在单元内三条中位对偶线段上各解一个一阶HLLC，把A⁻ΔU/A⁺ΔU
分给两端节点，三份之和为Φ_T，即图中箭头；节点再汇总并除以Arpaia面积。MMFV则按
Voronoi面循环，每条Delaunay边一个Riemann问题（面O₂O₃，重构后的面状态）；RD每条边
由相邻两三角形各解半个面（G₂–m_CD–G₃，各自w_T），两者仅在重心与外心重合时相同。
报告§5.5已补充，无代码或运行变更。

**§186再补充（用户问C–D是否在T2、T3各算一次）：** 是，每条内部Delaunay边解两次，
但各按半面长度|ν^T|加权，两半合成一个中位对偶面，并非重复计数。两次解的节点状态
相同，法向与w_T不同；中心通量对ν线性，与一条直面相同，仅耗散满足Σ|ν^T|s^T≥|Σν^T|s。
新增只读审计`analysis/halfface_audit.py/.txt`，共49152条边：glass t=0时Σ|ν|/|Σν|
中位/99%为1.000/1.027，弯折角中位/99%为0.4°/26°；moving HLLC t=.05时为1.000/1.138、
0.8°/57°。半面总长/Voronoi面长中位约0.999，近共圆边上Voronoi面趋零（翻转前）而
中位对偶面有限。每步Riemann解数约为MMFV的4倍。按元素保留是为了元素守恒、第二步
限制、Figure4.2三角形调度及MPI三角形归属；按边合并耗散只是后续可选优化，未推导ALE。
报告已补充；无solver或hydro运行变更。

**§186再补充（第二步路线，用户决定）：** 不采用MUSCL式把HLLC外推到面上求二阶
（那会变成二阶顶点型FV，取代LDA）；采用类似blended scheme的逐元素、逐RK2阶段组合：
φ=φ^L+ℓ_T(φ^LDA−φ^L)，ℓ_T由可接受性与局部ρ/比熵界决定而非残差比传感器，限制对象
含corrector的F1−lumped时间差。**用户决定LDA的Gauss3暂不改动。** 总量匹配放在低阶
一侧：Φ_G=Φ_trap+ΣΔΦ_e，ΔΦ_e取自`rd_contour_gauss_correction`的逐边项（只依赖边端
状态与中点法向，相邻三角形互为相反数，ALE网格项两种积分都精确）；每边½ΔΦ_e分给两
端点后，元素低阶总量等于Φ_G、修正元素零和，而节点低阶更新在舍入内不变，正性论证
保留。备选（未选用，留作以后）：LDA改用梯形节点通量围道使总量天然一致（e4fcd84
红字对照）。设计写入报告§5.6；尚未实现。

## 187. 2026-09-30：实验性moving LDA/F1+边HLLC限制混合，Sedov 21点与单点注入

**作者：Claude Code（Opus 5.5）；用户要求实验LDA+HLLC，先跑Sedov（21点与单点注入）；
thesis中LDA的Gauss3不改，实验内可自由选择。** 新增显式子选项（沿用`RD_LDA_RUSANOV_BLEND`
框架，默认与静态混合不变）：`RD_BLEND_LOW_HLLC`（仅equal-step ALE LDA/F1/Gauss3；
低阶端点为边HLLC+`rd_hllc_gauss_edge_split`逐边½ΔΦ_e，元素总量等于LDA的Φ_G并逐元素
检查；低阶阶段按ALE权重a_i、b_i=3/2−a_i检查凸性与CFL/(2b)）；`RD_BLEND_LOCAL_BOUNDS`
（限制器额外要求ρ在元素模板[min,max]、K=p/ρ^γ不低于模板最小值，模板取U^n、校正阶段
U*及低阶状态，Zalesak型、未对光滑极值放宽；二分后按舍入回退确保返回ℓ满足界）。
ℓ_T逐元素共用，修正零和、凸平均保证守恒与可接受性，不裁剪、不加floor。

新测试`tests/rd/test_lda_hllc_blend.py`：60个抖动周期网格上元素总量与独立Gauss3 ALE
围道一致3.2e−16、边项节点抵消1.2e−16；3000例界限制器ℓ合法且极大。HLLC核测试与全部
5项make check_rd通过。档案`../local_runs/sedov_lda_hllc_20260930_v1/`：冻结源码，四个
独立binary；uniform缺陷6.66e−16/5.55e−16；无新子选项的静态LDA/Rusanov混合在其16²
contact存档上重放五快照**逐位相同**。ℓ=0对照经LDA路径重现单独HLLC运行至≤6.1e−12，
步数2443与预算相同，确认边项在整次moving运行中节点抵消、ALE检查接线正确。

t=.05（21点）bounds：raw ρmax3.797、均线峰2.889、r<.05面积平均ρ.0293、中心p1.653、
v_r去趋势RMS.0846、v_t RMS.0656、ΔM−.452%、ΔE−.963%；HLLC低阶3.413/2.980/.0276/
1.714/.0287/.0309；一阶MMFV3.434/3.099/.0276/1.670/.0180/.0121；二阶MMFV3.971/3.302/
.0300/1.596/.0487/.0277。单点bounds：raw3.861、均线峰2.925、中心单样本ρ.0044（解析
面积均值.0043）、中心p1.595，但ΔE−6.40%（HLLC−1.61%）。所有阶段可接受；限制元素平均
预测.7%、校正4.7%。无激波前欠冲，无K低于初始最小值。结论：LDA修正使激波更尖、中心
压力更接近解析，但速度/角向散点约为HLLC的3倍、二阶MMFV的1.7倍（v_r），因此均线峰
未超过HLLC；局部界是必要的。

仅保正（无局部界）对照：t=.025时ρ_min.0015、T=p/ρ最大2059、411个节点K低于初始最小值、
v_t RMS.355（bounds.105，HLLC.064），时间步塌缩至6.1e−6；首段在AREPO的0.85×TimeLimitCPU
=1530s处停于t=.0235/.0171（设置限制，非数值失败），已用restart（TimeLimitCPU14400）续跑，
续跑动作单独记录。守恒：按RD-ALE-FINISH分项，几乎全部漂移在步开始的temporary/connectivity
rebase项（端点换算≤.016%）；bounds在t≤.0125时21点/单点能量−2.69%/−7.49%（HLLC−.25%/
−2.54%），剖面越尖重连损失越大，因此第三步守恒保正重连remap已成为主要瓶颈。限制：界
未放宽、未做光滑精度测试、单次运行、5个快照、无MPI/层级/repair。详见
[报告](RD_SEDOV_LDA_HLLC_BLEND_20260930.md)。未改thesis/默认Config，未commit/push。

**§187补充（仅保正对照续跑完成）：** 两个仅保正运行经restart续跑后均到t=.05（21点共
8156步，单点9951步），全部阶段可接受但阶段最小密度约5e−5（近真空）。21点/单点：raw ρmax
4.809/5.349（超过解析跳跃4），均线峰2.683/2.618，中心p1.562/1.571，v_r/v_t散点.194/.162
与.164/.142（约HLLC的5倍，核心v_r出现负值），分别有503/528个节点K低于初始最小值（最低
1.4e−5/2.6e−6倍），ΔE+1.46%/+2.81%。限制器仅约2%的corrector元素起作用，LDA几乎未受
限制。结论不变：局部界是必须的。分析脚本已纳入续跑日志，最终图在档案`analysis/`
（`analysis_preliminary_bounds_only/`保留为中间版本），报告§3.4已补充。


## 188. 2026-09-30：按用户反馈收简Chapter1措辞并恢复outline原文

**作者：Codex（GPT-6）；用户授权Chapter1定点修订。** 在§185未提交改动上，
将decaying-mode句子替换为用户给出的negligible with time原句；Gaussian段落恢复
The current开头及原结构，仅替换mostly Gaussian并保留评论删除；椭圆星系改为
支持显著旋转的简短表述，ATLAS3D仅留引用；Schaye与Dalla Vecchia扩写缩为一句
压力处方及观测定律再现，保留面密度/体密度区别。Outline的Chapter2段落恢复HEAD
原文，Ben Morton贡献句逐字恢复，其余已获认可的改动保留。

核实正式Abstract修改一直在thesis-frontmatter/abstract.tex第12行的unstaged diff中，
本轮未再改动Abstract或bib。本轮源码仅Chapter1变化；此前三文件改动均未stage/commit/push。
隔离完整XeLaTeX编译成功，245页，无未解析引用或缺字；已有10处overfull hbox保留。
目视检查物理页28、31、61、62、69、70。未覆盖thesis根目录master.pdf。存档：
`../local_runs/thesis_ch1_followup_20260930_v1/`，含前后源码hash、diff、冻结源码、
编译记录、PDF和页面预览。未改solver或其他thesis章节。

**§187再补充（用户问散点来源；决定论文倾向仅用HLLC）：** 只读审计
`analysis/scatter_origin_audit.py/.txt`：切向速度RMS在激波带最大，t=.0125/.025/.05时
HLLC .161/.101/.062、bounds .212/.128/.094、仅保正.292/.280/.214、二阶MMFV .084/.055/.028；
内区bounds约为HLLC的2倍，仅保正早期达1.07（近真空热核）。36扇区峰值半径标准差：HLLC
.0025、bounds .0041、仅保正.0049、MMFV2 .0011，LDA使激波前沿角向起皱，因而均线峰下降。
推断机制：线性二阶LDA在捕获激波处不单调并带几何依赖的非径向扰动，且去掉HLLC的耗散；
界只约束ρ、K且模板宽松，速度无约束，逐元素ℓ切换也会引入粗糙；HLLC前沿噪声仍约为MMFV2
的2倍，glass/median dual/翻转提供基底。**用户决定：LDA/HLLC混合尚不成熟，论文倾向只用
HLLC结果；混合保留为实验记录。** 报告§4已补充；无solver或hydro运行变更。

## 189. 2026-09-30：HLLC Sedov论文预览图、N scheme匹配对比与文字草稿

**作者：Claude Code（Opus 5.5）；用户要求先不动论文，预览结果图并在对话中审核HLLC-RD文字，
补充N scheme结果（可仅static）。** 新增`plot_hllc_thesis_preview.py`：21点HLLC moving/static、
二阶MMFV、SWIFT与解析解（坐标轴包含全部样本，避免遮住SWIFT核心离群点），输出
`sedov_hllc_20260930_v1/analysis/thesis_preview/`。21点N在两种网格都失败（§156），唯一完成
的是130点(r=.05)注入的static N/RK2；因此用冻结HLLC binary（hash核验、不重编译）在同一IC上
补跑static/moving（`run_hllc_disk005.py`，档案`sedov_hllc_disk005_20260930_v1/`，均返回0）。
t=.05：static N/HLLC均线峰2.300/2.324、中心ρ .0851/.0857、中心p1.559/1.552几乎相同，但N的
v_r/v_t散点.191/.088，HLLC仅.024/.006，N内区ρ可达.65；moving HLLC峰2.943、ΔE+2.10%，
moving N在此注入下失败。中心平台来自注入气体的绝热膨胀：ρ_c≈(p_c/K_inj)^{1/γ}，21点估计
.031（MMFV2 .030、HLLC .028），130点.097（HLLC moving .090），单点.005（.003），说明
MMFV/HLLC的中心平台不是数值扩散，而Rusanov的~.2是数值混合。文字草稿
[RD_SEDOV_HLLC_THESIS_TEXT_DRAFT_20260930.md](RD_SEDOV_HLLC_THESIS_TEXT_DRAFT_20260930.md)，
报告§7已补充。未改thesis、默认Config，未commit/push。


## 190. 2026-09-30：拉取GitHub/Overleaf的Chapter4/5批注并合并本地thesis

**作者：Codex（GPT-6）；用户要求拉取并与本地合并。** 本地main为6e02014，
其与447c9a0分别保存Chapter1/Abstract修订及公式标点，tracked工作区干净。
Fetch获得origin/main的04dcc4a（Sadegh Chapter4/5批注和少量文字修改，另含Lay Summary
centre→center）。三方合并无冲突，产生68399ec，父提交为6e02014与04dcc4a。
核对Chapter1完整保留、Chapter5与远端完全一致；Chapter4相对远端仅保留本地公式
句号修订，Abstract完整保留新的DF机制表述。30个未跟踪文件hash全部不变。
远端Chapter5两处行末空格原样保留。未处理批注内容，未重新编译或覆盖PDF，未push。
当前main领先origin/main三个提交，tracked工作区干净。证据：
`../local_runs/thesis_github_merge_20260930_v1/`（refs、双向diff、文件hash、验证）。

**§189补充（用户问两张图moving HLLC在r<.15为何不同；Morton风格二维图；单点注入）：**
差异来自注入质量而非方法：21点/130点注入质量.00128/.00793；moving网格上被加热的生成点
t=.05位于r≤.106（ρ≈.030）/r≤.160（ρ≈.098），点源解析解在r=.103/.148内才包含同样质量且那里
密度已升到.096/.296，故较大的130点热泡明显低于解析曲线；static网格把热泡与周围混合。
新增`plot_sedov_maps.py`（plasma线性0–4、全盒、共用色标；RD按P1插值，MMFV按Voronoi最近
生成点），输出`sedov_hllc_20260930_v1/analysis/maps_preview_v1/`：static HLLC壳圆但厚，MMFV圆
且薄（有glass条纹），**moving HLLC壳薄但呈多边形**：前沿半径傅里叶模m=5–6为主、幅值约.0018
（R的.7%），MMFV≤.0008，static HLLC≤.0007；单点moving同样多边形，推测为离散注入与近六边形
连接的印记被低耗散moving网格保留（Morton分散注入的理由相同），原因未隔离。单点moving
HLLC完成t=.05（峰3.00，中心.0033，ΔE−1.61%）；static单点已用冻结binary启动
（`run_hllc_reuse.py`，`sedov_hllc_nearest1_static_20260930_v1/`），因孤立热点时间步≈3e−6，
耗时较长。报告§8已补充；未改thesis。

## 191. 2026-10-01：static单点HLLC-RD、AREPO单cell对照与moving RD前沿多边形的诊断

**作者：Claude Code（Opus 5.5）；用户问static能否单点注入，以及为何AREPO单点/少量点也很圆。**
static单点HLLC-RD完成t=.05（11120步、764s，22240阶段全部可接受，守恒至舍入，峰2.33、中心
ρ.024），只是孤立热点使时间步约3–6e−6。用冻结二阶MMFV binary与同一热点ID、按Voronoi面积
归一化跑单cell（`run_mmfv_single.py`，`sedov_mmfv_single_20261001_v1/`，1204步、145s）：峰3.31、
中心p1.59、守恒至舍入，前沿很圆。前沿半径傅里叶最大模/R（t=.0125→.05）：moving HLLC单点
1.63→.71%、21点2.03→.77%、130点1.10→.79%（不衰减）；static HLLC 21点.80→.29%；MMFV二阶21点
.94→.32%、一阶21点1.14→.35%、二阶单cell .38→.17%，主模m=6/5。结论：多边形只出现在moving
RD，与注入大小、空间阶数无关；中位对偶与Voronoi面法向差异中位仅1.25°（注入边界≤2.8°），
不足以单独解释。主要推测：moving RD在翻转时中位对偶面积与P1基跳变并做非守恒rebase，
在受压剪切的壳层反复发生且随局部网格取向，而MMFV的Voronoi面连续变化且通量交换严格守恒；
需用守恒保正翻转remap（第三步）验证，原因尚未隔离。另：两个核测试原先用相反符号的法向
（等价于点反射三角形，代数检查有效），已改为solver公式n_0=(y1−y2,x2−x1)并全部通过。
新图`sedov_hllc_20260930_v1/analysis/maps_preview_v2/`；报告§9。未改thesis/solver，未commit。


## 192. 2026-10-01：只读检查thesis前言至Chapter2末尾

用户要求检查剩余红字及需修改之处。审阅thesis `68399ec`（现已与origin/main相同）
的frontmatter、Chapter1和Chapter2；未改论文。正文无活跃红字，PDF图目录xx页仍有
Figures4.6--4.8的3条SK批注，源于Chapter4完整图注；Chapter2三处旧批注已用%关闭。

发现明确公式/符号问题：Chapter1比能与能量密度混用、共动动量通量多一个v、
Boltzmann碰撞不变量误用宏观v、HLL星区速度加减号、DF横向冲量漏倒数、球塌缩Lambda
项漏c²、Press--Schechter密度误写p及Poisson分布函数定义不一致；Chapter2质量加权
H2积分的上限与dr不匹配。Maxwellian速度弥散约定应明确。Chapter2 SHMF的ln/lg和冷却
率nH²归一化需对照分析代码，不能仅凭论文写法判定数值结果有误。Figure1.4图注错误、
Abstract完成范围、Morton对比适用条件、分辨率措辞及重复bib/作者名也列入报告。
核对Springel2010、Morton2025和Wu2026出版信息等一手来源；Springel原文Eq116本身
似也有同一多余v排印问题，修正依据是量纲和本章后续推导。

冻结全部跟踪源码，XeLaTeX/latexmk隔离编译246页，引用解析正常；红字提取及11页
目视检查完成。原thesis master.pdf未覆盖。末尾复核所有跟踪文件hash不变、Git跟踪
工作树干净，30个既有未跟踪文件保留。完整review.txt、源文件manifest、编译PDF/日志、
预览和verification.json：`../local_runs/thesis_front_ch2_review_20261001_v1/`。
未运行或修改solver，未commit/push。

**§191补充（SWIFT默认21点与单点注入）：** SWIFT默认即stock makeIC的N_inject=21。新增
`run_swift_single.py`复用冻结默认binary/stock yml/glass（hash核验），仅把N_inject改为1（存diff），
热粒子ID8256与RD/MMFV单点一致，2.4s完成：ρmax4.27（超解析4）、均线峰2.84、中心单粒子p≈11.8、
v_t RMS .241（默认.176）。前沿最大模/R（早期→t=.05）：SWIFT 21点3.73%→.58%、单点5.61%→1.87%；
HLLC static .80/.64%→.29%；HLLC moving 2.03/1.63%→.77/.71%；MMFV .94/.38%→.32/.17%。新2×4
Morton风格图`sedov_hllc_20260930_v1/analysis/maps_preview_v3/sedov_maps_grid.png`。修正解释：没有
网格翻转的SWIFT同样多边形且单点更明显，故翻转并非唯一原因；MMFV最圆，moving HLLC介于MMFV与
SWIFT之间；翻转非守恒rebase仍是可能的RD特有贡献，原因未隔离。报告§10。未改thesis/solver。


## 193. 2026-10-01：按用户确认修改Chapter1公式、图注及thesis参考文献

在原Chapter1.tex中落实确认项：PS的rho与mass-function措辞、Poisson加m及d³v、
Cartesian能量rhoE、微观碰撞不变量、HLL星区速度加号、DF横向冲量倒数、
X=v/(sqrt2 sigma)并定义一维速度弥散，Figure1.4图注改为用户指定的comparison。
用户明确保留球塌缩Lambda项、Chapter2积分上限和SHMF/cooling归一化；此前c²
问题应限定为符号约定一致性，不能直接判定教材漏项。用户已考虑ln/lg且t_cool
遵循Grackle计算，本轮不据文字推断数值有误。Springel arXivv3 Eq116确实也有
多余v；共动方程、Morton措辞和Abstract仅回答/提供建议，暂未改。

审计7个bib库367条，合并Bond1991/Lacey1993/Bryan2014三组重复，剩364条；
对应Chapter2和Appendix1仅替换引用键。修正Kennicutt/Spitzer/Ford/Gott后缀、
Zwicky姓名与缺失出版信息、Peacock出版社及若干卷页/文章号；补Ferland完整
作者列表和页码，去掉Boylan-Kolchin标题重复的running title。Wu2026已更新
为MNRAS551(2),stag1461,DOI10.1093/mnras/stag1461。来源见归档notes.txt和
Crossref响应。BibTeX使用实际bst验证全部364条，无警告；344个活跃引用键均
解析，git diff --check通过。未逐条重新核查每篇论文的全部元数据。

遵守用户当前编辑器要求，原位编辑并两次调用内置编译；章节片段在line3的
\chapter处因缺master前导而失败，未另建文档、PDF或切换标签。本轮完整PDF
未验证。仅7个thesis跟踪文件变化，既有未跟踪文件列表不变；未commit/push，
未改solver。归档：`../local_runs/thesis_confirmed_fixes_20261001_v1/`，含前快照、
diff、bib审计/验证、原生编译诊断和用户保留项记录。


## 194. 2026-10-01：确认共动方程与Abstract修改，保留Morton表述

用户确认：Chapter2研究精确到量级，Morton相关差异不足以影响本研究，保持现有
比较措辞。按授权修正Chapter1 Eq1.52共动动量通量，去掉额外v，明确三条方程
通量的散度及能量重力源的点积。Abstract Chapter4段采用上一轮建议原文：
集成AREPO并扩展moving mesh、Galilean测试、未来应用framework；删去connectivity
与hierarchical/MPI展开，static hierarchy/MPI已在Chapter4开头交代。

本轮仅两文件变化，Chapter1差异严格限于共动方程；早先公式/bib修改保留，
Morton文字未改。diff --check通过。内置编译按用户要求检查当前chapter1.tex，
仍因章节片段缺master前导在line3的\chapter失败；未另建文档/PDF或切换标签，
未验证完整PDF。未commit/push。归档：
`../local_runs/thesis_comoving_abstract_20261001_v1/`。

**§191再补充（8个运行的一维质量加权平均剖面）：** 新增`plot_sedov_profiles_mw.py`，输出
`sedov_hllc_20260930_v1/analysis/profiles_mass_weighted_v1/`：两行（21点/单点）×三列（ρ、v_r、p），
每条曲线为宽.005径向bin内Σm q/Σm，半径取各自初始注入能量质心，空bin留空、孤立bin以点标出。
质量加权密度峰：HLLC static 2.328/2.329、HLLC moving 2.982/3.000、MMFV 3.289/3.296、SWIFT
2.995/2.840（21点/单点）；r<.05质量加权压强：1.53/1.53、1.71/1.65、1.60/1.59、2.38/11.8
（解析1.605）。HLLC-RD与MMFV几乎不随注入点数变化，SWIFT单点明显退化。报告§11。


## 195. 2026-10-01：只读讨论Chapter3 SK批注与Galilean invariance归属

用户要求先不改thesis，倾向最小修改Chapter3，稍后说明C++→C重写接入AREPO
和inverse-K处理修正。读取全部Chapter3 SK批注：重点为个人贡献、相较Ben新增
内容、3D与时间积分来源、测试归属和其他求解器比较。现有§distribution schemes
已说明S⁻=sum K_j⁻的对角扰动破坏守恒及伪逆处理；Gresho已比较AREPO/Enzo/
SWIFT/GIZMO。建议在章首/对应段落/结论明确这些贡献，区分2023论文时贡献和
之后移植修正，说明3D/时间积分已有工作来源，不必扩写新理论或测试章节。

Galilean不变性区分连续Euler方程、固定网格离散误差、随boost一致变换的ALE
格式。Chapter3当前固定网格RD一般有bulk-velocity相关耗散，不应声称严格
离散Galilean不变；但moving mesh不是唯一可实现该性质的方法（SPH/MFM/MFV
也可）。Moving mesh也需网格运动/离散更新满足变换一致性。Chapter4已有
boosted Yee/Gresho数值验证；测试重合不是完整数学证明。若增加推导，放Chapter4
ALE部分，Chapter3只需过渡引用即可。核对Springel2010和Hopkins2015原始论文：
https://arxiv.org/abs/0901.4107 ; https://arxiv.org/pdf/1409.7395 。

本轮thesis HEAD `090740b`（用户已提交前轮修改）；前后跟踪工作树均干净。
未编辑thesis、未编译/开新标签、未改solver或运行实验，未commit/push。


## 196. 2026-10-01：Chapter3零速度逆矩阵零空间证明长度讨论

Author: Codex. 用户已自行修改Chapter3，3D沿用Ben的标准实现，不拟扩写；本轮只读
核对新inverse matrix implementation段落和既有报告
`RD_THESIS_42_ZERO_VELOCITY_DERIVATION_20260926.md` §§2–4。

建议将零Roe平均速度情形的证明压缩为约半页（3–4个公式）：非退化二维三角形，
h=Hbar>0，c²=(gamma−1)h，L=sum|n_i|，G=sum n_i n_i^T/|n_i|。
G正定，S⁻z=−c/4 [(L/h)z_E, G z_m, L z_E]^T，所以ker S⁻=span(e_rho)。
Ki e_rho=0，谱分裂也给Ki⁺ e_rho=0，因此分配残差与零空间分量无关。
论证依赖精确零Roe平均速度、共同Roe状态和标准正负特征值分裂；近零速度的
数值秩判定另属浮点实现问题。正文不必引入一般流速下的共同对称化矩阵证明。

同时指出：伪逆为精确解还需要右端相容；此情形条件为b_E=h b_rho，Chapter3
所述Roe N/LDA右端满足。不能仅由矩阵奇异推出必有无穷多解。
未编辑thesis、未编译/新开标签、未改solver或运行hydro测试，未commit/push。


## 197. 2026-10-01：按用户确认补入Chapter3秩条件及简短零空间计算

Author: Codex. 用户要求用rank([S⁻|b])=rank(S⁻)<n表达有无穷多解的条件，
不另写相容性讨论；用零速度下的直接代入计算替换“It can be shown”。仅修改
`chapter3/chapter3.tex`的inverse matrix implementation段落：明确零Roe平均速度，
定义n（二维4），给出S⁻z的L/G块表达式，利用非退化三角形G正定得到z=z_rho e_rho，
再明确写Ki⁺z=z_rho Ri Lambda_i⁺ Ri⁻¹ e_rho=0。因此中间解虽不唯一，分配残差
不受自由参数影响。保留用户其余文字与3D内容。

thesis仅此一份跟踪文件变化，git diff --check通过。内置编译检查保存后的chapter3.tex，
在第一行的chapter命令失败，因为章节片段缺主文档前导；未向章节添加前导或创建
替代文档/PDF，未切换当前编辑器标签。本轮完整PDF未验证。未改solver、未运行
hydro测试、未commit/push。


## 198. 2026-10-01：Chapter4加入已完成的高分辨率Sod图

Author: Codex. 查看用户最新e3ef001（Chapter4批注清理、章首强调hierarchical能量
守恒、no→on等）；Chapter4源码无sk/zw或显式红字标记。按用户要求小改，暂不
添加vortex/boost的标准AREPO对比。

从`../local_runs/Sod_2d_Morton/20260928_main_comparison_v3/output/pdf/`的两页
主比较PDF无损提取第一页作为`chapter4/figures/sod_glass_Nx128_t02_profiles.pdf`。
源SHA256验证与归档一致，PDF内容流/文字保持原样；第二页正是现有Nx64图的来源。
高分辨率effective Nx128，全2×2周期盒256²=65536点，t=.2，gamma5/3；N/LDA左右列，
静态一阶、静态RK2、moving RK2，与现有图相同图例/布局。没有新hydro运行。

Caption采用“Same as Figure [原图引用], but with a higher effective initial resolution
of Nx=128.”，另有简短LoF标题。正文加新图引用，说明间断处更锐利而整体行为类似；
删除仅展示低分辨率for clarity的句子。只改Chapter4.tex并新增一张图，其他内容保留。
PDF提取后重新渲染并目视检查通过，git diff --check通过。内置章节编译仍在line1的
chapter因缺master前导失败；未另编全文PDF、未切换编辑器标签。未commit/push。
归档：`../local_runs/thesis_ch4_sod_highres_20261001_v1/`，含图来源、diff、验证与PNG。

## 199. 2026-10-01：HLLC-RD完整开发记录（思路来源、数学、代码、实验与结论）

**作者：Claude Code（Opus 5.5）；用户要求把HLLC-RD的思路来源、数学与代码实现细节、实验列表
及图链接、主要结论写入开发日志。** 完整内容见
[RD_HLLC_RD_SUMMARY_20261001.md](RD_HLLC_RD_SUMMARY_20261001.md)，本节为摘要。

思路来源：审计发现原moving Sedov实为纯一阶Rusanov（LDA/Rusanov与Bmax仅static）；Rusanov耗散
α_T≈(|u−w|+c)ℓ/2对密度同样作用，在准拉格朗日网格上质量以声速扩散，且随膨胀核心单元增大，解释
中心密度moving .198>static .125>MMFV .028；文献中Deconinck–Ricchiuto§3.6.1指出中位对偶一阶FV配
任意守恒通量即为FS/RD格式；一阶MMFV对照（峰3.10、中心.028）证明主要缺陷是耗散形式而非阶数，
HLLC与exact一阶几乎相同，故选HLLC。

数学：沿用Arpaia残差Φ=½ΣG_j·n_j（G=F−U⊗σ̄_T，中点内法向）；单元内中位对偶线段ν_ij=(n_j−n_i)/6
（i→j，Σ_{j≠i}ν_ij=−n_i/2）；φ_i=Σ_j[H(U_i,U_j;ν_ij)−G(U_i)·ν_ij]，守恒通量成对抵消使Σφ_i=Φ；
每对一次HLLC（σ̄_T系，Einfeldt/Batten+Davis波速，Toro星态并检查可接受），左/右涨落A⁻ΔU/A⁺ΔU分给
两端，经G(−σ̄_T)变回实验室系；单侧HLLC扇平均给出正性条件(dt/S_i)Σ|ν_ij|s_ij≤1，ALE校正另需
0<b_i≤1与CFL/(2b_i)≤1；相对网格静止的接触间断残差为零；结构上是RD（元素守恒拆分、一维即Roe
涨落分裂），但非MU、一阶；与MMFV区别：按三角形循环、每边两半面（各自σ̄_T）、面过重心而非外心、
节点一阶状态、元素残差拆分而非Voronoi单元间通量交换。

代码：新`src/hydro/rd_hllc.h`（rd_hllc_pair、rd_hllc_residual，另有供混合实验的
rd_hllc_gauss_edge_split）；solver中`RD_LOW_ORDER_HLLC`挂在`RD_RUSANOV_LOW_ORDER`路径下，仅改
时间步选择与阶段装配两处（每顶点系数、守恒检查），沿用ALE几何、lumped RK2与全部阶段检查；
defines_extra两宏；Config_HLLC_{static,moving}.sh；测试tests/rd/test_hllc_positivity.py（4000例，
已改用solver法向公式）。仅单rank、等步长、周期、hydro、lab frame。

实验（档案与图链接见总结§4）：一阶MMFV诊断；HLLC static/moving 21点与moving单点及Rusanov
逐位回归；论文风格预览；130点注入与唯一完成的static N匹配对比；static单点HLLC；MMFV单cell与
SWIFT单粒子（同ID8256）；Morton风格2×4密度图；8个运行的质量加权剖面；半面几何审计与示意图；
实验性LDA/HLLC限制混合。

主要结论：moving HLLC-RD（21点）raw ρmax3.41、峰2.98、中心ρ.028、中心p1.71、ΔM−.33%/ΔE+.70%，
达到一阶MMFV水平（3.43/3.10/.028/1.67），远优于原Rusanov（2.63/2.43/.198）；static HLLC峰2.33且
守恒至舍入；单点注入在两种网格都可完成；static下N与HLLC均值相同但N噪声约8倍且moving N失败；
中心平台为注入气体的绝热膨胀；剩余问题为一阶精度、来自重连rebase的预算漂移，以及前沿约
.7–.8%R的多边形（MMFV最圆，SWIFT亦多边形，原因未隔离）；LDA/HLLC混合尚不成熟，用户决定论文
优先采用HLLC-RD。未改thesis，源码未提交。


## 200. 2026-10-01：独立审查Claude的HLLC-RD Sedov结果与方法归属

Author: Codex. 用户认为HLLC较Rusanov明显改善，但可能不是典型RD。审查Claude
最新汇总、低阶实现、调用分支、草稿、归档和原始快照；不修改thesis或solver。
报告：`RD_HLLC_RD_REVIEW_20261001.md`；审查归档：
`../local_runs/hllc_rd_review_20261001_v1/`。

40个快照hash及重新计算的8组统计通过；核对HLLC campaign源码tar、3个binary/config、
IC/参数hash。冻结真实归档低阶header，用修正法向后的现有测试重跑4000例通过：
守恒1.64e−16，独立HLLC1.06e−12，boost协变2.93e−12（相对flux scale）。增加编译
单元反例：静态直角三角形rho=(1,1,3)、v=(1,0)、p=1，总残差0，但节点密度分配
(0,−1/3,+1/3)，显示横向耗散，不具该配置的N/LDA多维迎风分配。未运行新hydro。

moving21点：普通径向bin峰2.428→2.980，r<.05面积均密度.1977→.02764，但质量
−.329%、能量+.698%；moving1点能量−1.606%。改进可靠，不能声称守恒已修复或
N/LDA已通过Sedov。实际HLLC分支绕过K分配；可称median-dual FV residual distribution
嵌入ALE-RD框架。Abgrall2017§4.1明确给出FV→RD构造：
https://arxiv.org/html/1708.03108v3#S4.SS1 。

主要措辞问题：不能将相对MMFV2的差距全部归因空间阶数；原表bin均值与后来
mass-weighted曲线需区分（core_rows的docstring也误称mass weighted）；一维HLLC
不是Roe求解器；失败LDA使用Gauss3/F1而非Roe残差；temporary_change同时包含准备
和stage更新，不能把这一列直接当作翻转误差测量；contact zero需共同fluid v=w_T，
不只是各点跟随各自流速；faceting原因尚未隔离。完整说明及建议定位见报告。
保留所有既有修改，未commit/push。环境h5py缺失/旧Python file_digest不支持仅为
审查脚本启动问题，使用已有21cmfast环境和通用hash写法后通过。


## 201. 2026-10-01：Riemann通量构造RD的原始文献与几何示意图

Author: Codex. 用户要求找HLLC或其它Riemann solver进入RD的历史依据，并仿照
thesis Figure3.2画图。报告：`RD_RIEMANN_FLUX_RD_LITERATURE_20261001.md`。
核对2017版Deconinck–Ricchiuto原文：应引用§4.1、式(55)–(59)，不是旧稿§3.6.1；
明确给出median-dual FV→FS/RD。Abgrall2018（2017预印本）§4.1式(23)–(24)
给一般构造。新增Hu–Li–Tang2010 JCP229,1681–1697：§2式(5)后确实使用HLLC，
但为cell-centred steady high-order RD-type，不是当前moving vertex-centred实现。

独立新图用双三角形展示内部median-dual段、Riemann flux、减去端点物理通量得到
两个fluctuation，以及各点residual与元素总残差。强调总残差对应插值nodal flux，
不等同于非线性F(U_h)精确积分；该空间恒等式不能证明完整ALE/flip守恒或N/LDA的
多维迎风性。代码/公式对应见报告。保留上一轮审查和Claude记录。

图、PDF/SVG/PNG与绘图源码：`../local_runs/riemann_rd_schematic_20261001_v1/`。
法向方向/长度/垂直性、几何恒等式及任意vector flux的守恒和式通过（误差8.88e-16）；
PDF重渲染后目视检查通过。不改thesis/solver，不跑新hydro，无commit/push。

§201 follow-up (Codex): clarified H versus F_i.nu: both contain interface
length; H is a two-state Riemann numerical flux, not quadrature of the original
continuous P1 field. Added the HLLC wave-fan formula D_i/j=ell sum S^-/+ W,
static nodal Euler assembly, and scalar upwind example to the focused report.
Changing the solver changes the distribution even though the element total
is unchanged. Full ALE/RK2 update distinguished from this spatial illustration.
No thesis/solver changes or new runs.

§201 citation-scope follow-up (Codex): compared verified2017 §4.1 directly
with rd_hllc.h:133–191 and the native caller. Static spatial construction is
an instance of the review's median-dual FV–RD rewriting. HLLC is a flux choice;
Euler-system algebra is allowed by the review, while its scalar stability
results do not automatically prove Euler positivity/entropy properties.
Current ALE velocity, geometric weights, RK2 and edge flips require separate
justification. Detailed mapping and a short optional English paragraph added
to the focused report; no thesis edits, solver edits or new runs.


## 202. 2026-10-01：对 Claude 的 HLLC FV–RD 工作的综合评论与示意图归档

**作者：Codex；按用户要求整理。** 用户接受当前方法属于 FV–RD、不同于 N/LDA
的 multidimensional upwinding，认为它对 Sedov 等强激波问题具有价值，并将其
moving-mesh 后续发展视为值得继续研究的方向。这是对方法定位和研究方向的确认，
不表示完整 moving-mesh 守恒、正性或高阶混合已完成验证。本轮未修改 thesis 或 solver，
未运行新模拟，未 commit/push；保留 Claude 的原始记录及此前审查结果。

### 对已有工作的评价

1. **Sedov 改进有实证支持。** 此前独立审查已重算 40 个快照、核对 8 组实验，并对
   归档 C kernel 重跑 4000 例测试。HLLC 相比 Rusanov 明显改善峰值密度和中心过度
   混合，说明已有 RD 框架可以容纳适合强激波的另一种低阶空间分配。它的价值无需
   依赖 N/LDA 的多维迎风性质；这些 Sedov 结果应归属于实际运行的 HLLC FV–RD 分支。
2. **方法归属应明确。** 建议称为 “HLLC-based finite-volume residual distribution
   on the median dual mesh, incorporated into the ALE-RD framework”。当前实现对
   内部 median-dual 界面求两状态 Riemann 问题，并将 fluctuation 分配给两端顶点；
   它绕过 N/LDA 的 K-matrix 分配，空间仍为一阶。配置中的 N_SCHEME 或采用 RK2
   都不能据此声称该空间算子具有 N/LDA 的多维迎风性质或二阶空间精度。
3. **有直接的理论来源。** [Deconinck & Ricchiuto (2017)](https://team.inria.fr/cardamom/files/2019/10/deconinck-ricchiuto2017.pdf)
   第 4.1 节、式 (55) 后的一般通量表达式及式 (57) 后的求和关系，可以作为空间
   FV–RD 构造的主要依据。静态极限下，代码采用相同的 median-dual 几何、物理通量
   扣除和元素残差组装。HLLC 是我们选择的 numerical flux；Euler 方程组延拓保留该
   代数关系。综述在这一节对标量迎风格式给出的稳定性结论不自动证明完整 Euler/ALE
   实现的正性或熵稳定性。2017 版节号是 4.1，旧文本的 3.6.1 不宜混用。
4. **当前结论仍需保持边界。** 元素内 sum(phi_i)=Phi 不等于完整 moving run 的预算
   守恒。在此前 128² 初始节点、21 热节点、t=.05 的归档 moving HLLC 实验中，
   质量和总能量变化仍分别约为 −0.329% 和 +0.698%。不要把这些缺陷说成已经由 HLLC
   修复；现有 temporary_change 记录也没有单独隔离 edge-flip 的贡献。中心密度
   样本数较少，不能把与参考结果数值接近表述为高精度的连续解验证。
5. **原叙述中应修正的点保留在详细审查中。** HLLC 的一维 fluctuation 形式不能
   等同于 Roe solver；普通径向 bin 均值、质量加权均值和面积加权中心密度需区分；
   相对 MMFV 的差距未被证明全部来自空间阶数；failed LDA 的 Gauss3/F1 配置应准确
   标识；当前接触保持和正性结论有相应状态/CFL 条件；shock-front faceting 的成因
   尚未隔离。这些限定不否定已有 Sedov 改进。

### 后续研究定位

当前已有 moving-mesh 初步结果。下一步有意义的工作是进一步区分空间通量、时间与
几何更新、connectivity change 对守恒和解质量的影响，并验证相应修正的正性、精度
与鲁棒性。与高阶 RD 的受限混合也是后续方向，现有实验性 LDA/HLLC 混合不应被写成
已完成的方法。本文现阶段可以用 HLLC FV–RD 的强激波测试体现框架的可扩展性；
N/LDA 的多维迎风优势仍由其自己的 vortex 等测试支持。

详细材料：

- [对 Claude 结果和论述的独立审查](RD_HLLC_RD_REVIEW_20261001.md)。
- [原始文献、与综述的逐项对应、flux-to-fluctuation 推导及顶点更新](RD_RIEMANN_FLUX_RD_LITERATURE_20261001.md)。
- [Claude 的原始汇总（保留原文）](RD_HLLC_RD_SUMMARY_20261001.md)。

### 几何示意图

下图是此前按 thesis Figure 3.2 的几何说明方式绘制的原始示意图。本轮将已经验证的
PDF/PNG/SVG、绘图脚本和几何检查结果按字节复制到仓库内，方便日志随 Git 一起保存；
未重新生成或修改图片。源归档及 SHA256 记录见
[provenance.json](figures/riemann_flux_to_rd/provenance.json)。

![Riemann numerical flux to median-dual residual distribution](figures/riemann_flux_to_rd/output/pdf/riemann_flux_to_rd.png)

左图：沿重心与边中点之间的内部界面求 Riemann 通量；右图：扣除相应顶点的物理
通量后，将两个 fluctuation 分给两端。所有界面贡献在顶点组装，三个顶点 residual
之和等于元素总 residual。图中箭头表示分配方向，不表示 fluctuation 的正负。
图展示静态空间构造，总 residual 采用线性插值的 nodal flux；完整 ALE 更新还需
单独处理时间、几何和拓扑变化。

文件：[矢量 PDF](figures/riemann_flux_to_rd/output/pdf/riemann_flux_to_rd.pdf)、
[PNG](figures/riemann_flux_to_rd/output/pdf/riemann_flux_to_rd.png)、
[可编辑 SVG](figures/riemann_flux_to_rd/output/pdf/riemann_flux_to_rd.svg)、
[绘图脚本](figures/riemann_flux_to_rd/plot_riemann_to_rd.py)。

## 203. 2026-10-01：审阅Codex评论；Chapter4新增HLLC FV-RD小节与示意图

**作者：Claude Code（Opus 5.5）；用户明确要求在thesis Chapter4 "Distribution schemes"
之后新增subsubsection写出HLLC/FV-RD数学，并可仿DR2017 Figure 2作图。**

审阅Codex §§200–202：方法归属（median-dual HLLC FV-RD嵌入ALE-RD，非N/LDA多维迎风、
非LP、一阶）、2017版应引§4.1式(55)–(59)、HLLC不等同Roe、接触保持需共同v=σ̄_T、
正性有条件、全局预算未修复（temporary_change非仅翻转项）、bin均值/质量加权标签需区分、
与MMFV2差距不能全归因阶数、faceting原因未隔离——均同意，并已体现在新thesis文字中
（只陈述空间构造与有条件性质，不写Sedov结论）。我此前汇总中的§3.6.1已改为2017版§4.1。
核对存档2017原文（`../local_runs/riemann_rd_schematic_20261001_v1/sources/`）：§4.1
的中位对偶几何、式(55)恒等式、减去同态通量的RD形式及(57)后元素求和，与
`rd_hllc.h`静态极限逐项一致，故DR2017可作空间构造的主要理论依据；HLLC本身引
Toro1994/2009，波传播形式引LeVeque2002，ALE时间推进沿用Arpaia。DR2017的标量稳定性
结论不自动给出Euler正性，正性另由HLLC扇平均凸组合论证（条件：中间态可接受、C_i≤1、
0<b_i≤1、C_i(U*)≤2b_i），实现中逐阶段检查。

Thesis改动（仅Chapter4，基于5feca22，未commit）：在"Distribution schemes"后、
§4.3前新增`\subsubsection{HLLC finite-volume residual distribution}`
（label `section:ALE_RD_HLLC_FVRD`），内容：动机与DR2017§4.1归属；ν_ij=(n_j−n_i)/6
及闭合恒等式；中位对偶FV式→RD式φ_i=Σ[H−F_i·ν]与元素和=线性插值通量残差（梯形）；
成对涨落D^(i),D^(j)；ALE相对通量G_T及与Arpaia残差/G3式的关系、RK2用N的lumped质量；
运动系HLLC（变换M(w)R、波速、λ_*与星态、W_p、D=|ν|MRΣλ^∓W）；接触保持、扇平均正性、
校正步凸组合式；与N/LDA及AREPO Voronoi FV的区别；实现与时间步/检查。新图
`chapter4/figures/rd_hllc_fvrd_schematic.pdf`（Figure 4.6）：(a)相邻中位对偶单元与两段
界面（虚线为Voronoi面），(b)单三角形S_i∩T法向闭合，(c)HLLC波扇与涨落分配；(a)(b)沿用
DR2017 Fig.2几何，图为原创绘制并在caption致谢，未从PDF抽取。图几何恒等式数值验证
（误差8.9e−16）。整本master在scratch副本用latexmk/xelatex编译通过：无未定义引用，
新文字无overfull，印刷页164–170目视检查。归档：
`../local_runs/thesis_ch4_hllc_fvrd_20261001_v1/`（绘图脚本、geometry_check、PDF/PNG、
thesis diff、审阅页PDF、provenance）。未改solver、未运行新模拟、未commit/push。


## 204. 2026-10-01：仅编译 Chapter4 新增 FV–RD 小节供用户预览

Author: Codex. 用户将整篇编译请求收窄为只编译新增内容对应页面。读取本地
Chapter4，SHA256 与 Claude §203 的已验证版本一致；未 git pull、未修改论文。
在独立临时目录中使用原 master 前导、customisations 和原始小节文字（保留起始页
前一段），只编译该片段。外部引用编号按同一 source hash 的既有整篇编译预览核对，
引用作者年份由已有 natbib 标签提供；公式从4.46、图从4.6、页码从164开始。
没有重新编译整篇或其它章节，预览中的跨章节超链接关闭。

LaTeX 编译技能调用已有 TeX Live/latexmk/XeLaTeX 完成，产出7页（164–170）。
临时 wrapper 的标签载入位置首次触发 preamble-only 错误，移至前导后编译成功；
没有修改 thesis 正文来解决预览工具问题。最终无未定义引用/文献或 overfull，
7页均渲染目视检查；所有已跟踪 thesis 文件 hash 保持不变。仅做编译排版检查，
不在本轮展开用户稍后要做的内容审查或润色。按用户查看请求调用右侧PDF打开工具，
界面返回 queued；原章节源编辑器保留。无commit/push。

预览：[Chapter4 FV–RD, pages164–170](../../local_runs/thesis_ch4_fvrd_preview_20261001_v1/output/pdf/chapter4_fvrd_preview.pdf)。
编译日志、临时源、引用快照和验证：`../../local_runs/thesis_ch4_fvrd_preview_20261001_v1/`。

## 205. 2026-10-01：文献检索——以FV作为RD的已有结果

**作者：Claude Code（Opus 5.5）；用户要求检索以往把FV用作RD的格式及其结果。**
报告：[RD_FV_AS_RD_LITERATURE_20261001.md](RD_FV_AS_RD_LITERATURE_20261001.md)。
结论：FV⇔RD等价在理论上成熟（Roe1982一维；Paillère1995与DR2017§4.1中位对偶；
Abgrall2018§4.1；Barsukow–Ciallella–Ricchiuto–Torlo2025 Prop.6角通量FV≡RD）。
真正以FV通量作RD分配并给出数值结果的很少：Paillère的upwind FV-RD（标量，正、非LP、
一阶，DR2017称其耗散与Δt限制均劣于N）；Barsukow等2025有Euler结果（含圆形Sod、KH）
但为Cartesian网格、多维角通量、着重稳态保持。未找到三角形中位对偶HLLC/近似Riemann
FV-RD用于Euler、运动网格或Sedov的已发表结果（检索结论，非证明不存在）。
Hu–Li–Tang2010自述仅在最后一步不同——用Newton求解而非残差分配，实为单元中心重构
格式，故§201称其为"genuine HLLC+RD precedent"偏强。RD与独立FV代码的比较较多：
Paardekooper2017圆柱爆炸N与HLL几乎相同、Noh中低耗散blend需N备份；DR2017 LN优于二阶
Roe FV；Guzik–Groth2008标量RD远优于FV。建议论文可补引Paillère1995、Barsukow2025，
新颖性表述为"应用"（HLLC中位对偶FV-RD嵌入Arpaia ALE-RD并用于重连运动网格Sedov），
不称新格式族。未改thesis/solver，未运行模拟。

## 206. 2026-10-01：Chapter4 FV–RD 符号统一及 moving-frame/ALE 说明

Author: Codex. 用户明确要求把新增小节和示意图的 D 改成 phi、nu_ij 改成
n_ij，并说明 moving-frame 通量与 Phi 中 moving-mesh 项的关系，再局部编译。
仅修改本地 thesis Chapter4 的 HLLC finite-volume residual distribution 小节：
成对 fluctuation 用 `\phi_{ij}^{(i/j)}`，中位对偶界面长度加权法向用
`\mathbf n_{ij}^T`，单位法向相应调整；caption、正文、公式和图一致。
以 `\Phi_{\mathrm{HLLC}}^T` 指代线性插值 Euler 通量的元素残差，明确它与
ALE 总残差使用同一 midpoint geometry 和 nodal states；后者增加的项为
`-\int_T\boldsymbol\sigma_h\cdot\nabla\mathbf U_h\,\mathrm dA`。
说明 moving frame 中求 Riemann flux 再映射回 laboratory conserved variables
已经得到 relative flux G_T，不能再重复加 mesh 项；相对速度还改变波速及分配。

在新归档中复制 Claude §203 的原绘图脚本，只更新显示符号并稍移右星态标签以
避免与波线重叠；保留旧归档。几何闭合检查最大误差 8.9e-16。新版矢量 PDF
写回 thesis 的 `chapter4/figures/rd_hllc_fvrd_schematic.pdf`。
内置 editor compiler 对裸 Chapter4 在首行 chapter 命令失败（缺 master 前导，
多文件工程限制），未为此改写论文章节。沿用 §204 的 master 前导、引用编号
快照及原排版，用已有 TeX Live/XeLaTeX 只编译本小节，成功生成7页（164–170）。
最终无未定义引用/文献、无 overfull；7页全部渲染目视检查。前后 hash 验证：
已跟踪 thesis 文件只有 Chapter4.tex 变化，且变化范围仅该小节，另有上述新图。
未改 solver、未运行模拟、未 git pull/commit/push。

新版预览：[Chapter4 FV–RD, pages164–170](../../local_runs/thesis_ch4_fvrd_notation_20261001_v1/output/pdf/chapter4_fvrd_preview.pdf)。
修改前备份、精确 diff、绘图脚本、编译片段、日志与验证记录：
`../../local_runs/thesis_ch4_fvrd_notation_20261001_v1/`。

## 207. 2026-10-02：HLLC moving-frame 矩阵与 Springel2010 的对照验算

Author: Codex. 用户要求在对话中详细验算，不修改 thesis。核对 Springel2010
原文 arXiv:0901.4107v3 §3.3–3.4，Eqs35、38–45：M(w) 是其 Eq45 boost
作用于守恒变量的二维矩阵表示；R 是 Eq39 旋转的逆方向（normal/tangent→x/y），
不是 Eq38 的 primitive-variable PDE Jacobian。Springel 先把 Riemann 状态变回
lab 再用 Eq42 的 F−U⊗w；当前写法把 moving-frame 通量用 MR 映回，二者代数等价。
逐分量展开能量通量得到 (E+p)v_n−Ew_n，包括由动量通量变换贡献的 p w_n。
仅变换状态与直接变换通量应区分；后者无需重复减去 U w_n。

对固定时刻/几何/节点状态，令 w=mean(sigma_i)，F_h=Σpsi_i F(U_i)。
H_ij 反对称、Σ_j n_ij=−n_i/2 给出 Σ_i phi_i=½Σ_i(F_i−U_i⊗w)·n_i。
P1 梯度 grad U_h=Σ_i U_i⊗n_i/(2|T|) 为常数，因此
∫sigma_h·grad U_h=½Σ_i(w·n_i)U_i，严格得到目标等式。
这里的 Phi 是 nodal-flux/trapezoid 总残差，不自动等于 G3 或 Roe 的总残差。
元素平均速度通常不是实际中位对偶面的运动速度；用真实 sigma_h 作边界通量时，
其散度还包含 U_h div(sigma_h)。Arpaia 空间残差等于该边界通量加
∫U_h div(sigma_h)，几何贡献由其时间/面积处理。此恒等式不证明完整 moving
solver 的全局守恒或 connectivity transfer。

独立 NumPy 代数检查1000组随机状态、旋转、非退化三角形与非均匀节点网格速度：
状态变换、通量变换、P1网格积分、任意反对称 pair flux 抵消、目标残差等式的
最大归一化误差分别为 1.58e-15、1.76e-15、1.39e-15、2.00e-15、2.66e-15。
仅检查代数与几何，非新的 HLLC/正性/时间积分/完整水动力验证。脚本及结果：
`../../local_runs/hllc_ale_matrix_check_20261002_v1/`。未修改 thesis 或 solver，
未运行新模拟、未 commit/push。

## 208. 2026-10-02：Chapter3 插入 FV–RD 几何图

Author: Codex. 用户已自行精简旧内容并开始 Chapter3 的 FV–RD 介绍，本轮只要求
插入 `geometry_FV_RD_scheme`。现有 PNG 位于 Chapter3 figures，正文有空的
Figure ref。仅在该段后加入标准 figure 环境、简短两面板 caption 和
`fig:RD_FV_geometry`，补上正文引用；本图为 Figure3.3。caption 标明取自
Deconinck & Ricchiuto Figure2，已与本地 review PDF 第14页核对。没有改写
用户仍在编辑的其余段落或增加推导，没有改 Chapter4。

内置编译器无法独立编译缺少 master 前导的 Chapter3；使用当前 master 前导及
已有引用编号在临时目录只编译本小节，XeLaTeX 成功生成1页，无未定义引用或
overfull，图片、caption、正文引用目视检查通过。精确 diff、源备份及局部检查：
`../../local_runs/thesis_ch3_fvrd_figure_20261002_v1/`。只修改本地 Chapter3.tex，
原 PNG 保持不变；未 pull/commit/push，待用户按通常流程同步 Overleaf。

## 209. 2026-10-02：Chapter3 补入静态 FV–RD 推导并统一符号

Author: Codex. 用户要求把之前内容到 ALE 部分加入 Chapter3、完善已有符号，并
保留 taken-from Deconinck & Ricchiuto 的图。按已告知的解释，将旧稿 ALE form
小节之前的静态内容整理进 `section:FV_RD_schemes`；未恢复长篇 HLLC/ALE 实现。
来源为 §206 归档的 Chapter4 旧稿及已核对的2017 review §4.1 Eqs55–59。

补全三角形、重心、边中点和 median-dual segment 的数学记号，沿用 n_ij^T、
phi_i^T 和 pair fluctuation phi_ij^(i/j)。加入五个编号公式：内部法向与闭合关系、
FV 更新、FV→RD 转换、元素总和以及 pair fluctuation。明确 H 已乘界面长度，
说明一致性、成对守恒、闭合 hull 上零项的减去，以及与一维 Roe 分裂的联系。
总残差使用 Chapter3 的小写 phi_FV^T，区分线性插值节点通量 F_h 与非线性
F(U_h)，不声称梯形总量等于 Roe 线性化总量。简要指出可以换用 HLLC，且分配
仍来自一维法向 Riemann 问题。保留原图文件、figure 环境、caption 和来源不变。

内置 compiler 对裸 Chapter3 仍因缺 master 前导失败；以原 master 前导只局部
编译本小节，TeX Live/XeLaTeX 成功，3页全部渲染检查，无未定义引用或 overfull。
新公式编号3.44–3.48，图仍3.3。diff --check 通过；前后 hash 验证仅已跟踪的
Chapter3.tex 改变，且范围仅该小节，图及其 caption 字节不变。未改 Chapter4、
solver 或 bibliography，未运行模拟、未 pull/commit/push。备份、精确 diff、
验证记录与局部编译：`../../local_runs/thesis_ch3_fvrd_text_20261002_v1/`。

## 210. 2026-10-02：恢复 Chapter3 FV–RD 原文并去掉段内硬换行

Author: Codex. 用户明确要求保留自己原有语句，只修正数学符号。本轮从 §209
编辑前备份恢复 FV–RD 开头两段的原文、引用方式与 Chapter4 引用，仅把几何
变量排为数学符号；保留 §209 新增推导。该小节正文段落及 caption 各合并为
单行，保留段落空行与多行公式环境。核对公式环境及小节外源码字节不变。
内置 compiler 因裸 chapter 缺少 master 前导失败；使用 master 前导局部
XeLaTeX 编译成功，3页目视检查通过，无未定义引用或 overfull。diff --check
通过。未改图、solver 或其它章节，未同步或提交。备份及本轮精确 diff：
`../../local_runs/thesis_ch3_fvrd_prose_restore_20261002_v1/`。

## 211. 2026-10-02：Sedov 8组质量加权剖面叠加全部样本点；解析压力两行相同

**作者：Claude Code（Opus 5.5）；用户要求在质量加权一维剖面上用淡色点叠加全部数据点，
并询问右列解析压力为何单点与21点不同。** 新脚本
`examples/Sedov_2d/plot_sedov_profiles_mw_points.py`（复用v1的load_all/mass_weighted，
不改v1）；输出 `../local_runs/sedov_hllc_20260930_v1/analysis/profiles_mass_weighted_points_v1/`。
每个RD顶点、MMFV单元质心、SWIFT粒子为淡点（alpha .12，PDF中栅格化），质量加权线在上；
y轴按列在两行共享（ρ[−.15,4.45]、v_r[−.5,2.3]、p[−.25,5.6]）。
解析解：两行完全相同（同一点源相似解，E=1、t=.05，激波半径.258，峰压4.99，中心压1.605）。
v1中单点行压力面板看似不同，仅因自动纵轴被SWIFT单个热粒子（r=.0042，p=11.8，
两行中唯一p>6的样本）拉到12；新图在面板顶边以三角标记并注明，元数据列出该越界样本。
未改thesis/solver，未运行新模拟。

§211 follow-up (Claude, 2026-10-02): user asked whether to average only r>.1 and to
remove the off-scale text. Bin counts (width .005): moving HLLC-RD, MMFV and SWIFT have
only 17–25 samples in r<.1 (0–8 per bin, still 0–25 per bin in .10–.14); static HLLC-RD
has ~515 (2–50 per bin). A fixed r>.1 cut is therefore too strict for the static run and
too loose for the mass-following methods. Instead, `--min-count 5`: each mean line starts
at the innermost radius beyond which every bin of that run has ≥5 samples (same rule for
all methods; faint points still all shown). Start radii: static .005–.010; MMFV .110–.115;
SWIFT .105–.115; moving HLLC-RD .130–.135. Off-scale text removed (triangle marker kept;
sample listed in metadata). Output `profiles_mass_weighted_points_v2/` (v1 kept). The
remaining low SWIFT values at r≈.11–.15 are many particles, not a few outliers.

§211 second follow-up (Claude, 2026-10-02): user chose a fixed start radius r=.05 for all
mean lines (`--rmin 0.05`, no min-count). Output `profiles_mass_weighted_points_v3/`
(v1, v2 kept). Sparse bins in .05–.13 (0–8 samples per bin for moving HLLC-RD, MMFV, SWIFT)
remain visible, e.g. the SWIFT 21-point pressure segment up to ~3.2 near r≈.08.

## 212. 2026-10-02：将最新 Sedov 二维密度图与一维剖面复制到 thesis Chapter4 图目录

**作者：Claude Code（Opus 5.5）；用户要求。** 仅复制文件，未改任何 .tex，未 commit。
`chapter4/figures/sedov_glass128_t005_density_maps.pdf` ← `maps_preview_v3/sedov_maps_grid.pdf`
（2×4 密度图，21点/单点 × HLLC-RD静态/运动、AREPO MMFV、SWIFT，色标截断[0,4]，14.2×7.0 in）；
`chapter4/figures/sedov_glass128_t005_profiles.pdf` ← `profiles_mass_weighted_points_v3/...points.pdf`
（淡点+质量加权均值，r≥.05起画，按列共享y轴，越界SWIFT热粒子以三角标记，12.8×7.2 in）。
SHA256 一致（6168…03ed、8bb1…6ae2）；thesis HEAD 5d957e8。来源与哈希：
`../local_runs/thesis_ch4_sedov_figures_20261002_v1/provenance.json`。均为预览图尺寸，
插入正文时以 \textwidth 缩放；尚无 Sedov 正文/caption。

## 213. 2026-10-02：审阅 thesis 中 FV–RD 与 Sedov 文字；Chapter4 插入 Sedov 两图

**作者：Claude Code（Opus 5.5）；用户要求检查 Chapter3/4 中 FV–RD 与 Sedov 文字，并把两图加入
Chapter4。** 只改 Chapter4（基于 a376fb1，未 commit）：Sedov 设置段后加一句引用两图与对照
（AREPO MMFV、SWIFT SPHENIX，同 glass、同加热粒子），并插入 Figure 4.11
（`sedov_glass128_t005_density_maps.pdf`，label `fig:ALE_RD_sedov_maps`）与 Figure 4.12
（`sedov_glass128_t005_profiles.pdf`，label `fig:ALE_RD_sedov_profiles`）及事实性 caption；
用户原文未改。scratch 副本整本 xelatex 编译：无未定义引用，新文字无 overfull。
diff 与审阅页：`../local_runs/thesis_ch4_sedov_figures_20261002_v1/`。
审阅要点（仅报告，未改用户文字）：
(1) Ch4 Sedov段"directly use the HLLC solver in AREPO"不准确——RD用自写`rd_hllc.h`
（Toro星态，Davis+Roe平均波速，σ̄_T系），AREPO `riemann_hllc.c`只用Davis估计，且MMFV对照用exact；
(2) Ch4 FV-RD 运动网格段"the only difference ... Voronoi face geometry with w"过强：还有半面几何
（每条Delaunay边两段过重心，各用本三角形σ̄_T）、帧速度定义、一阶节点态vs MUSCL-Hancock、Arpaia
RK2/修正对偶面积vs Voronoi体积；所引Springel(2010)"equation 33 and 42"在arXiv版为梯度估计式，
移动面通量为式(27)，请对照MNRAS版核实；
(3) Ch3 由φ_i去掉ΣF·n_ij需闭合壳恒等式Σ_{T∋i}n_i=0（DR2017式55第二式，内点/周期）；
(4) Ch4"N需要多点注入"应写明为本工作测试：21/1点失败，仅130点(r<.05)静态完成，运动网格亦失败；
(5) Ch3 FV-RD 节宜补一句性质：一阶、合适通量下CFL正性、非MU非LP；
(6) FS术语源自Roe(1982)对Roe(1981)的再解释；"Section 4.1 of \citep"宜用\citet；
另有语法小处。图内字体在\textwidth下约4–4.5 pt，建议按5.7 in重绘（未做，待用户决定）。

## 214. 2026-10-02：按用户确认修改 Chapter3/4 中 FV–RD 与 Sedov 文字

**作者：Claude Code（Opus 5.5）；用户接受§213第1、2点并指定第3点改法，另要求改小的措辞问题。**
基于 a376fb1，未 commit。Chapter4：(1) Sedov 段改为"We use the HLLC approximate Riemann solver
(Toro1994), evaluated in the frame moving with σ̄_T, and refer to the scheme as HLLC-RD."；(2) FV–RD
运动网格段"the only difference…（equation 33 and 42）…replace their w"两句改为"The Riemann problem is
solved in the rest frame of the interface as in the MMFV method of AREPO (Springel 2010), but with the
frame velocity σ̄_T and the median-dual interfaces instead of the Voronoi faces."；该段相对通量的
\mathcal{F} 改为粗体；"supernova explosion"→"explosions"；Sod 段"whlie"→"while"。Chapter3（获授权，
仅此几处）：(3) "Using Equation (dual normals)"→"Using Equation (dual normals) and Σ_{T∋i} n_i = 0"
（保留对式的引用，因两者都需要）；"which remains"→"remain"；"experiments … finds"→"find"；
"It's"→"It is"。未改 \citep/\citet、FS 归属、N 注入说明与 FV-RD 性质句（未获要求）。scratch
副本整本编译：无未定义引用，被改行无 overfull。累计 diff：
`../local_runs/thesis_ch4_sedov_figures_20261002_v1/thesis_review_fixes_cumulative.diff`。

§214 follow-up (Claude, 2026-10-02): user asked to rotate the two Sedov figure pages like the
AREPO flowchart. Both figures now use `\begin{landscape}` + `figure[p]`, wrapped together in
`\afterpage{...}` as in the Chapter3 Rayleigh–Taylor pair, so page 173 fills with text first.
Maps at `width=\linewidth`; profiles at `0.88\linewidth` (0.92 overflowed by 14 pt with its
4-line caption). Full scratch build: no undefined refs, no float-too-large; printed pages 174/175
are rotated (/Rotate 90), text resumes on 176. Diff and pages:
`../local_runs/thesis_ch4_sedov_figures_20261002_v1/` (thesis_landscape_cumulative.diff,
review/chapter4_sedov_landscape_pages_173_176.pdf). Uncommitted.

## 215. 2026-10-02：thesis 全文终检——红字/批注、Ch1/3/4 参考文献、Ch3/4 科学问题（只读）

**作者：Claude Code（Opus 5.5）；用户要求检查剩余红字与批注、Ch1/3/4 参考文献真实性与重复、
Ch3/4 主要科学问题。** thesis HEAD d93eb77，未改 thesis。
红字/批注：正文无生效的 \sk/\zw/\red/\adg；仅 Chapter2 注释行（18、271、504）内残留，PDF 不显示。
scratch 全新编译：无未定义/重复标签与引用，BibTeX 无警告，共 345 条文献。
文献：Ch1/3/4 引用 206 条，逐条经 DOI（Crossref）、arXiv ID 或标题检索核对；无重复（近似对均为
不同论文：Planck 2015/2018、Hafen 2019/2020、AGORA I/II、Morton 论文/学位论文等）；无仅 arXiv 文献。
需改：Bromm & Loeb 2003 DOI 应为 10.1086/377529（现指向他文）；Begelman+2006 DOI 应为
10.1111/j.1365-2966.2006.10467.x（现指向他文）；arpaia2015mesh 为 Inria 研究报告 RR-8666
（hal-01102124），bib 误作 @phdthesis。其余标记为无 DOI 的经典/书籍或网络首发年差异，已确认真实。
科学：Ch3 未见主要问题（Roe 参数代数、K 矩阵与特征值、N/LDA/B、RK2 质量矩阵守恒与 Heun、CFL、
Yee/Gresho/RT、FV-RD 推导均核对）。Ch4 主要问题：(1) Sedov 段称 DR2017"uses FV-RD and LN scheme
for shock-shock interaction"不符——原文为 LN 对比二阶单元中心 FV（Barth–Jespersen）；(2) 对
Abgrall et al. 2020"cannot be applied to astrophysics simulations"表述过强，宜写为固定连接的 Lagrangian
交错网格；(3) Sedov 结果未报告运动网格守恒漂移（21点 ΔM −0.33%、ΔE +0.70%；单点 ΔE −1.6%；静态
舍入级）及一阶导致峰值低于 MMFV；(4) Ch4 引言"significantly increase the performance"无计时依据；
另：剖面图 caption 删减后三角标记未解释。核对脚本与结果：
`../local_runs/thesis_review_refs_science_20261002_v1/`。

§215 follow-up (Claude, 2026-10-02): user-requested fixes on thesis HEAD 1873f1d, uncommitted.
(0) Bibliography: Bromm_Formation_2003 DOI → 10.1086/377529; Begelman_Formation_2006 DOI →
10.1111/j.1365-2966.2006.10467.x (chapter1bib-cosmology.bib); arpaia2015mesh @phdthesis →
@techreport (Research Report RR-8666, Inria Bordeaux Sud-Ouest, HAL hal-01102124). (1) Chapter4
Sedov: "apply the FV-RD and LN scheme" → "apply the FV and LN schemes" (DR2017's FV is a
second-order cell-centred Roe/Barth–Jespersen scheme, not median-dual FV-RD). (2)–(4) unchanged by
user decision. (5) Profile figure re-rendered without the off-scale triangle
(`--no-offscale-marker`, new script option; otherwise identical to v3, same line starts and
limits) → `profiles_mass_weighted_points_v4/`, copied over
`chapter4/figures/sedov_glass128_t005_profiles.pdf` (sha 5dd98e3c…). Full scratch build: no
undefined refs, no BibTeX warnings. Noted new active SK comments from commit 1873f1d (Ch4 l.1075,
Ch5 l.4) left untouched. Diff: `../local_runs/thesis_review_refs_science_20261002_v1/fixes_after_review.diff`.

§215 second follow-up (Claude, 2026-10-02): per user, Chapter4 Sedov paragraph adopts SK's sentence as
"Given the limited exploration of the Sedov blast test with RD, we here present initial first-order
FV-RD results and discuss this scheme (see …) as a temporary solution." ("intial"→"initial"; undefined
"ST" written as "Sedov blast test"). Chapter5 l.4: "that achieve numerical convergence quickly" adopted
(placed after "hydrodynamic solvers" so it modifies the solvers); SK's DF-test note deleted (user: DF
tested with MMFV, not yet RD). SK's "To this end … novel developments" left in place pending the
user's choice (it duplicates "As a first step …"). Build clean. Diff:
`../local_runs/thesis_review_refs_science_20261002_v1/sk_comments_resolution.diff`. Uncommitted.

§215 third follow-up (Claude, 2026-10-02): user asked to set the local Chapter5 first paragraph to
the current Overleaf text. Line 4 replaced verbatim (all three \sk comments restored); chapter5.tex
is now identical to HEAD 1873f1d, i.e. the earlier Ch5 convergence-phrase edit and DF-note deletion
are reverted. Remaining uncommitted thesis changes: the two DOI fixes, arpaia2015mesh @techreport,
the Chapter4 FV/LN and SK-sentence edits, and the triangle-free profile figure.

## 216. 2026-10-02：独立复查 thesis 最终版本（Codex，只读）

用户要求检查 Chapter 3/4 重大科学问题、Chapter 1/3/4 参考文献及全文红字/批注。
审查 thesis HEAD 5d31697（finalize Chapter 5），已跟踪文件干净，未修改论文、同步或提交。
详见 [独立审查报告](RD_THESIS_FINAL_AUDIT_20261002.md)；脚本、来源清单、元数据与反例：
../local_runs/thesis_final_audit_codex_20261002_v1/。

新的重点发现：(1) Ch4 G3(P1 U) residual 配 Roe beta，在 S^- 奇异时原始伪逆只分配
S^- (S^-)† Phi；其 RHS 不必在值域内，不能无条件声明逐元素守恒。正密度/压力三节点反例
得到 Phi_E − Hbar Phi_rho = −0.2。Ch3 对相容 Roe RHS 的零空间证明不受此反例否定；
F1 temporal lumped fallback 也不修复 spatial residual。当前原生源码的空间 range completion
仅在 opt-in common-beta 路径，不能当成默认实现。本次是独立代数检查，不是新原生 hydro run。
(2) Ch4 l.300 对 Arpaia et al. 2015 的概括不实：原文 §6/§6.1 已有完整 perfect-gas Euler
方程、矩阵分裂和测试；Colombo & Re 2022 的 collapse/expansion 是局部 patch 且包含 connectivity
changes。(3) Ch3 结论的无条件时间二阶声明应区分 lumped N/Heun 与默认 LDA/F1；
既有 fixed-h 时间一阶证据和 hierarchy leading-operator 差异仍适用。Boost 测试只能支持已测范围
内的低 advection error/近似 boost independence，不能单凭图证明严格离散 GI。

参考文献：365 存储条目、345 全文引用、206 个 Ch1/3/4 引用；无重复 key/title/DOI/eprint/ISBN、
缺失引用或发现的虚构文献。遗留小错：Campoli2017 页码应113–129；van2006upwind 混用
2003 AIAA conference 和 2006 CiCP journal 信息；Lumina arXiv 已称 Accepted by MNRAS，
本地 Submitted 过时（正式卷期未核实，不补猜测值）；Abgrall-Barth 年份2002/2003涉及版权/期刊日期口径。
Wu2026 的 MNRAS551(2),stag1461 信息已正确，Morton thesis 经 DataCite 确认。
这修正§215旧记录中“no arXiv-only references”的概括。

全文无生效的红字/批注；Chapter2 l.18/271/504仅有被百分号注释的旧评论。源文件扫描无未定义引用、
重复label或空引用。全部已记录源文件hash不变；本次未新编译整本论文。

§216 follow-up (Codex, 2026-10-02): 用户仅授权修改 Campoli_ShockFitting_2017 和
van2006upwind；其余数学问题留到后续最终版本处理。已在本地 thesis 将 Campoli 页码改为
113–129；van2006upwind 保留 key 和 2006 年，改为 @article，期刊 Communications in
Computational Physics，1(2),192–206，删除混入的会议字段。只修改这两个 bib 条目，
正文及其余文献不变。检查 diff 与空白格式；未重新编译整本，未 commit/push。

## 217. 2026-10-08：新分支启动：flip 元素（守恒+正性）与运动网格分层时间步——Phase 0 与内核

**作者：Claude Code（Opus 5.5）；用户批准计划（~/.claude/plans/i-have-already-submitted-tender-spindle.md）。**
用户决定：分阶段（先 flip 作为 RD 单元，再评估 lazy flipping）；分层支持 N、LDA，理想含 B 与 FV-RD；单 rank；
>2 个月，viva 11/17 前可选部分结果；优先级：舍入级守恒 > Sedov 正性 > 小精度代价 > 分层加速。
Phase 0：`develop_pureC_RD` 未提交工作已提交为 `eacc3f9`（作者 Zhenyu Wu, Codex (GPT-6) and Claude Code (Opus 5.5)；
check_rd、HLLC/blend 测试通过）；新分支 `feature/ale-flip-conservation-hierarchy`；Makefile INCL 补 rd_hllc.h、
rd_lda_rusanov.h、rd_contour_quadrature.h；自测试分支引入 Python 参考 colombo_re_limited.py、colombo_re_explicit.py、
audit_euler_flip_closure.py、audit_p1_ledger_remap.py。文献（三个调研代理）：Colombo & Re 2022（ghost 单元，局部
自适应+隐式 BDF）、Gaburro et al. 2020（时空 sliver）、Steinberg+2016（donor 修正）、Alauzet–Mehrenberger 2010、
Kuzmin+2010、Guermond 凸限制；无“分层+中途重连”文献。设计报告
[RD_FLIP_ELEMENT_AND_MOVING_HIERARCHY_DESIGN_20261008.md](RD_FLIP_ELEMENT_AND_MOVING_HIERARCHY_DESIGN_20261008.md)，
详细实施计划 [RD_FLIP_HIERARCHY_IMPLEMENTATION_PLAN_20261008.md](RD_FLIP_HIERARCHY_IMPLEMENTATION_PLAN_20261008.md)。
数学数值核对（20000 随机 flip）：亏损=∫(U_h^new−U_h^old)、=flip 四面体体积；边 donor-cell 体积重现 δm；低阶
映射守恒、正、密度在包内、熵下界（精确有理数验证；donor 须逐位保持，Q/g 重算在冷高速气体丢 1e-6 内能）。
内核 `src/hydro/rd_flip_transfer.h`（高阶=均匀平移，低阶=donor-cell 最小混合，公共 θ 二分）与
`tests/rd/test_flip_transfer.py`：2597 单 flip 守恒 6.2e-16、独立公式 5.4e-16、均匀/仿射不变 θ=1、高阶可逆、
极端对比可容许；待修：Delaunay 多 flip 腔体部分有效性筛选拒绝了全部样本（0 例）。设计观察：热 donor 时
均匀平移把能量加到所有点（在界内，θ=1），这正是旧修复的 KH 扰动来源之一，待测“仅 receiver 分配”的高阶端。
规划代理补充：旧修复 KH −20.6% 可能部分源于 N/LDA 预测器用未修复 primitive 的 bug，应先只修 refresh 重跑；
分层中强制刷新可不改时间箱（每点 CFL ledger）。下一步：修多 flip 测试→加入 check_rd→registry/cavity（C）→
RD_ALE_FLIP_TRANSFER 接线+全方案 primitive refresh→Campoli 全方案→原生 gate。未改 thesis。

## 218. 2026-10-09：Phase 1 实现——RD_ALE_FLIP_TRANSFER、全方案 primitive refresh、Campoli 全方案；KH 三方对比与 Sedov 首批结果

**作者：Claude Code（Opus 5.5）；分支 `feature/ale-flip-conservation-hierarchy`，提交 46632e7…9de3bb3。未改 thesis。**

**代码。**
- 多 flip 测试改为逐腔体有效性（取向、面积平铺、非凸包点、g⁺>0），295 个 Delaunay 腔体（156 个 >4 点）。
  `test_flip_transfer.py` 与 `test_lda_rusanov.py`、`test_hllc_positivity.py`、`test_lda_hllc_blend.py` 加入
  `make check_rd`（9 项全过）。
- 新增 `RD_ALE_FLIP_TRANSFER`（仅等步长、单 rank）：
  - 旧三角形捕获升为生产代码，以排序 ID 三元组为键。
  - 新三角形回拉到 x^n，排序合并求对称差；对变化三角形的顶点做 union-find 得到精确腔体。
  - g=DualArea，δm=pullback−DualArea；断言腔外 |δm|/g≤1e-10、腔内守恒 ≤1e-12。
  - 调用内核后写回 ale_uold，并刷新 primitive。
  - `RD-FLIP` 诊断行；Campoli+transfer 时 `RD-ALE-FINISH` 改为硬断言（每步 endpoint_change ≤1e-11 相对）。
  - 与旧修复互斥，需 EQUALSTEP。
- **Bug 修复（全方案）：** 旧拓扑修复后只有 Rusanov 路径刷新 Density/Vel/Pressure，N/LDA/B 的 stage-0
  用的是未修复的 primitive。现改为所有方案都刷新；`RD_ALE_REPAIR_STALE_PRIMITIVES` 可重现旧行为供对比。
- Campoli 现可用于 Rusanov/HLLC（等步长）及 LDA/HLLC blend（含 transfer）。低阶校正器
  (a−½)Uⁿ+b[…] 中 a=时间质量/除数，b=3/2−a；两种质量都有运行时检查。
- 内核新增 `high_mode=1`（`RD_FLIP_HIGH_MODE`）：donor 不动，线性精确修正只加在 receiver 上，L1 变化同为 |D|。
  - 两种模式都通过全部测试；随机单 flip 中 mode 1 受限 1912 次，mode 0 为 2894 次。
  - 新增驻定接触测试（v=0、p 均匀、ρ 跳变至 1e6）：任何 θ 下 v 精确为 0、p 均匀到舍入。
  - 熵测试容差加入 K_min 自身的舍入（冷点 e/E≈6e-8，单例 41）。
- **最优性说明：** 在 L∞ 与集中质量 L2 意义下，均匀平移都是满足守恒的最小修正：
  min Σg⁺ΔU² s.t. Σg⁺ΔU=−D 给出 ΔU=常数。
  - 单个 2-2 flip（正方形边长 h）：D=−H_xy h⁴/6，每点变化 O(h²U'')。
  - KH glass48 中 tanh 宽 .025≈1.2h，界面处单次 flip 的密度变化约 3%；glass96 应降为约 1/4。

**KH t=10（glass48，Arpaia N，`run_kh_repair_refresh.py`）。**
- 归档 `../local_runs/kh_repair_refresh_20261009_v1`；分析 `examples/gresho_2d/analyze_kh_repair_refresh.py`。
- 三个方法：control（无修复）、stale（旧修复+旧 primitive）、refresh（旧修复+刷新）。

| 方法 | E_ky 峰值（时刻） | 相对 control | 质量漂移 | 能量漂移 |
|---|---|---|---|---|
| control | 0.0585 (t=8.0) | — | +1.35e-3 | −5.3e-4 |
| stale | 0.0729 (t=9.0) | +24.7% | −7.0e-6 | −1.0e-7 |
| refresh | 0.0887 (t=10，仍在增长) | +51.6% | −2.4e-8 | −1.3e-8 |

- 结论：**修 refresh 后差异没有变小，反而变大。**
- 时间序列显示：
  - 初始 seed 模式先振荡衰减（t<2.5），t=1.2 处三者只差 5–6%。
  - 此后增长从噪声级 seed 重新开始，起始时间对小扰动敏感（control≈3.0、stale≈3.2、refresh≈3.6）。
  - 因此 glass48 的晚期 E_ky 峰值主要反映起始时间，不是稳健的精度指标。
- 已启动分辨率研究（见下）。

**Sedov HLLC-RD moving + Campoli + transfer（scratch 开发运行，非冻结）。**

| 注入方式 | 到达时刻 | 腔体 | θ<1 | θ_min | 总量漂移 |
|---|---|---|---|---|---|
| 21 点 | t=0.05 | 4720 | 93 | 0.034 | ≤1.3e-15 |
| 1 点 | t=0.0488（被参数 TimeLimitCPU=1800 截停） | 4664 | 88 | 0.038 | ≤1.2e-14 |

- 两例都保持正性；旧修复在此情形因负压中止。
- 对照 thesis 的 Arpaia 运行，t=0.0375 时 Arpaia 漂移为：
  - 21 点：质量 −0.28%、能量 +0.33%；
  - 1 点：质量 −0.29%、能量 −1.97%。
- 剖面差 L1(ρ)≈0.0076；壳峰 3.40 vs 3.34。
- LDA/HLLC blend + Campoli + transfer 冒烟（pos/bounds）：t≈0.006–0.01 内每步守恒约 1e-16，b_min≈0.495，
  约 30% 腔体 θ<1。

**冻结 gate 活动（进行中）。**
- `../local_runs/flip_gates_20261009_v1`（`tests/rd/run_flip_gates.py`、`analyze_flip_gates.py`）：
  - 方法：{N,LDA,B,HLLC}×{Campoli, Campoli+transfer}，外加 N_flip_h1，γ=1.4。
  - uniform 组 18/18 通过：glass48 t=1/32 无 flip；随机点均匀态 t=1/4 有 1278 个腔体、θ=1，
    状态缺陷 ≤5e-15，总量精确不变。
  - Sod 与 Yee48/96（science 组）、KH t=10（kh 组）待跑。
- `../local_runs/kh_flip_resolution_20261009_v1`（`examples/gresho_2d/run_kh_flip_resolution.py`）：
  - N {arpaia, campoli, flip, flip_h1} × glass48/96。
  - glass48 IC 逐位重现归档 IC；glass96 为 2×2 平铺。
  - glass96 每例约 1 天。
- 待做：Sedov 冻结 gate（`examples/Sedov_2d/run_flip_sedov.py`，HLLC 与 blend，有/无 transfer）；
  限制器敏感性（floor κ、DMP、熵界）。

## 219. 2026-10-09：Phase 2——运动网格实际区间分层（RD_ALE_INTERVAL_HIERARCHY）：N、LDA、B、HLLC-RD

**作者：Claude Code（Opus 5.5）；提交 288c1fd、c509350、ae7c3f0、7bc1351、c911bec、9d062d9。单 rank。未改 thesis。**

**实现**（`residual_distribution_solver.c`，`RD_ALE_INTERVAL_HIERARCHY` 块；需 `RD_ALE_HIERARCHICAL`+Campoli）。
- 持久三角形 registry：排序 ID 键、CCW ID、区间起点 s_T 与诞生时刻。
  - 首次 opening hook 时由网格建立；`RD_DEBUG_ASSERTS` 下每步核对与活网格一致。
  - 重启不支持（终止）。
- 每个同步时刻 t：
  1. 与新 Delaunay 求差，用 union-find 得腔体；
  2. 闭合集 C = 自然到期三角形（顶点最细 bin 同步）∪ 接触腔体顶点的全部 registry 三角形；
  3. 在 C 的合成 tessellation 上执行两次集中式 Campoli sweep，h_T = t − s_T；
     预测器 live ⇔ 整个星形都在 C 且起点相同；
  4. 星形完全闭合的顶点全部刷新（⊇ 活跃点与腔体点）：
     - 几何 ledger 与星形面积对比，断言 ≤1e-10；
     - **以 ledger 作除数**（离散 GCL：均匀态 1.1e-13→8e-15）；
     - 被强制刷新的点不改 bin 与 VelVertex；
  5. 每个腔体执行 flip 元素传递（Phase 1 内核）；
  6. 提交 registry：保留的三角形沿用 s_T（闭合者为 t），新三角形从 t 开始。
- 每个公共闭合时刻硬断言 ΣQ 守恒 ≤1e-12、覆盖 ≤1e-12。
  `RD_ALE_INTERVAL_NO_TRANSFER` 为负对照。
- 守恒的理由：区间不等的共享边，其端点冻结（非 live）且线性运动，中点法向使边通量在两侧精确积分一致。
- 各方案的处理：
  - **N**：沿用集中式沉积，(ΔA/3)U⁰ − (h/2)(φ⁰+φ¹) + (ΔA/6)dU。
  - **LDA**：静态分层的冻结 dU F1 校正（Campoli 时间质量、实际区间），并对 LDA 也施加质量变体项 (D−M)dU/3。
  - **B**：预测调用按合成元素保存 N⁰、L⁰、已施加的 b⁰ 与 Φ⁰；校正调用施加
    θ(N⁰+N¹)+(1−θ)(L⁰+L¹)−b⁰+2(1−θ)(T_F1−T_lumped)，元素总量为 Φ(U*)，θ 由区间总残差确定。
    - 修过一个 bug：求解后 rhs[·][2] 已是解 z 而非 F1 目标，原先误用导致 θ≈1。
  - **HLLC-RD / Rusanov**：
    - 允许 natural bin 与 Campoli，以 HLLC 自身的梯形周线代替 contour residual。
    - live 点沿用等步长的 a/b 与 stage-CFL 检查（triangle_dt=h/2）。
    - 冻结点用新的 `SphP.RD_CFLLedger` = Σ(h/2)(coeff⁰+coeff¹)，刷新时报告，正性需其 ≤ 刷新质量。
    - 每个刷新态都检查可容许。

**Scratch 检查（非冻结）。**
- 等 bin 退化（H1）：与等步长 Campoli 对比，N 4e-15、LDA 5e-15、B 4e-15；HLLC 在首次 flip 前 7e-13/p≈259。
  - 首次 flip 后，A/B 两种 flip 约定在爆炸中心差异明显（t=0.00125 时 p 差 0.19）。
- 随机点均匀态 + 双 bin（1274 腔体）：N/LDA/B 状态缺陷均 ≤8e-15。
- Yee glass48、双 bin（分界 x=0.5 穿过涡心）、t=1，相对等步长 Campoli（等步长参考无 transfer，漂移约 2e-5；分层守恒到舍入）：

| 方案 | ρL1（分层/等步长） | 变化 |
|---|---|---|
| N | 2.96e-3 / 2.85e-3 | +4% |
| LDA | 1.19e-3 / 1.02e-3 | +17% |
| B | 1.55e-3 / 1.18e-3 | +32% |

  - 速度误差：N −1%，LDA +33%，B +24%。冻结 F1 的界面代价在预期之内（决策 D5）。
  - 双 bin 元素工作量为全细步长的 76%。
- KH glass48 N 双 bin 到 t=2：16558 腔体、117k 次强制闭合，公共闭合守恒 2e-15，无中止。
- Sedov 21 点 HLLC-RD natural bin（进行中，t≈0.009）：
  - 8 个占用 bin，dt 比 128；
  - 公共闭合守恒 1e-14，CFL ledger ≤0.105；
  - 元素工作量约为全细步长的 2.6%。
  - 墙钟时间受 CREATE_FULL_MESH 每步重建全网格限制，待测。

**冻结活动。**
- `../local_runs/interval_hierarchy_gates_20261009_v1`（`tests/rd/run_interval_hierarchy_gates.py`）：
  - N/LDA × {ref_flip, ih_equal, ih_twobin, ih_twobin25, ih_natural}，外加 N 负对照。
  - 冻结于"仅刷新活跃+腔体点"的旧规则（c911bec 之前）。
  - uniform 组 11/11 通过：缺陷 ≤9.5e-15，1249–1275 腔体。
  - Yee/KH 组进行中。
- 最终规则需重新冻结 v2，并加入 B 与 HLLC-Sedov。

## 220. 2026-10-09（续）：Phase 1 gate 结果、Sedov 自然 bin 分层、lazy flip（Phase 3）、限制器敏感性排队

**作者：Claude Code（Opus 5.5）；提交 ff8b3f4..（见 git log）。完整结果见 [RD_FLIP_HIERARCHY_RESULTS_20261009.md](RD_FLIP_HIERARCHY_RESULTS_20261009.md)。未改 thesis。**

- **flip_gates science 组 27/27 完成**（`../local_runs/flip_gates_20261009_v1`）。
  - Sod：有 transfer 的各方案守恒 ≤1.4e-15；仅 Campoli 时漂移 1e-4–1e-3。
  - Yee：flip 与无 flip 的 ρL1 差，glass48→96 比值为 N 3.3、LDA 3.5、B 3.6、HLLC 2.5，约二阶收敛。
    - 相对解析误差的增量：N +4.2%→+2.1%，LDA +5.4%→+2.6%。
    - 可回答用户"更优雅"的问题：均匀平移是 L∞ 与集中 L2 意义下的最小守恒修正，其扰动按 O(h²) 消失。
  - KH 组之前因排队循环的 `pgrep -f` 自匹配而未启动，已直接启动。
    - **教训：后台等待请用 PID（kill -0），不要用 pgrep -f 模式。**
- **Sedov gate（21 点，HLLC）。**
  - 仅 Campoli 与 thesis 的 Arpaia 结果相同（L1 1.4e-6），漂移完全来自 flip。
  - 加 transfer 后守恒到舍入，壳峰半径 0.2503（thesis 0.2462，解析 0.258）。
  - 1 点注入与 blend 组进行中。
- **Sedov 分层，HLLC natural bin（scratch，非冻结）。**
  - 2448 个事件，最多 8 个 bin，守恒 ≤2.1e-14，CFL ledger ≤0.108；剖面与等步长 flip 差 L1 1e-3。
  - 元素工作量 8.0%；RD CPU 15 s，等步长为 284 s；总 CPU 1141 s，等步长为 1634 s（1.4×）。
  - Voronoi 全网格重建占 70%。冻结复现见 v2。
- **Lazy flip（`RD_ALE_LAZY_FLIP`，e825d34）。**
  - 仅当旧三角形最小角 <15°，或 Delaunay 违反 >20° 时才采纳该连通改变；否则保留旧连接（不强制闭合，不传递）。
  - 采纳率：均匀态 1249→407，Yee 245→64，KH 76858→18180。
  - 精度：Yee 不变。KH 熵偏移 0.66→0.48（Arpaia 无处理为 0.42）。
  - KH 晚期 E_ky 在三者之间都不同，起始时刻由噪声决定，不可作为精度排序。
- **其他改动。**
  - 直接地址 ID 表（结果逐位一致）。
  - 分层 gate v1 已停止（规则被取代，见 STOPPED.txt）；v2 冻结并运行中：19 个方法，含 B 与 HLLC-Sedov。
  - 分析与作图脚本：`analyze_interval_hierarchy_gates.py`、`plot_flip_hierarchy_sedov.py`、`analyze_kh_flip_resolution.py`。
- **限制器敏感性 D2**（`tests/rd/run_flip_limiter_sensitivity.py`，`../local_runs/flip_limiter_sensitivity_20261009_v1`）：
  - KH：entropy、dmp0、二者兼有；Sedov：κ=1e-12、κ=0.1、entropy、dmp0。
  - 已构建，排队等 Sedov gate 链结束后运行。

## 221. 2026-10-09（续）：全部 gate 完成；flip 默认高阶端改为 receiver-only（RD_FLIP_HIGH_MODE=1）

**作者：Claude Code（Opus 5.5）。详见 [RD_FLIP_HIERARCHY_RESULTS_20261009.md](RD_FLIP_HIERARCHY_RESULTS_20261009.md)。未改 thesis。**

- **Sedov flip gate 10/10 完成**，有 transfer 的全部守恒 ≤2e-14 且 p>0。
  - blend(bounds) 的 thesis 运行能量损失最高达 6.4%（1 点注入），现为精确守恒，壳更锐。
- **限制器敏感性（D2）**：
  - κ 不敏感，Sedov 的 θ<1 仅 39–93/4720。
  - 熵界与密度包限制都会把大多数 flip 推向 donor-cell 端，扩散更强（Sedov 峰值下降，KH 熵偏移下降）。
  - 结论：κ=0.5、熵界与密度包均关闭。
- **KH 分辨率研究**（48/96，16×16 网格对比）：
  - transfer−无 transfer 的差在 t=1 处为 1 阶收敛（比值 2.0）。
  - 所有 glass48 变体到 glass96 的距离相近（t=1 约 0.037，t=2 约 0.085），即 transfer 影响低于离散误差。
  - KH 欠分辨（tanh 宽约 1–2 格）。
- **receiver-only 高阶端（mode 1）**：
  - KH 熵偏移：glass48 为 0.29–0.36，mode 0 为 0.66–1.07；glass96 为 0.33，mode 0 为 0.71–0.79，Arpaia 无处理为 0.42/0.72。
  - 不需要限制；Yee/Sod 与 mode 0 无差别。
  - Sedov（`../local_runs/flip_mode1_sedov_20261009_v1`）守恒、正性，峰值低约 1%，壳半径不变。
- **默认值改为 `RD_FLIP_HIGH_MODE=1`**（求解器两处），`check_rd` 12/12 通过。
  - 此前冻结的档案若 Config 未注明，则为 mode 0。
- **LDA 的 KH 在所有变体中都失败**（含等步长参考），为已知的 moving-LDA KH 问题（§§52–56），与 flip 无关。
- **待完成**：kh_flip_resolution 的 flip_h1（glass48/96）；最终报告与图；thesis 文字建议（不改 thesis）。

## 222. 2026-10-09（续）：供 Codex 审阅的完整进展报告；KH 分辨率研究完成；3D 展望

**作者：Claude Code（Opus 5.5）；用户要求写详细报告供 Codex 审阅。未改 thesis。**

**审阅报告：[RD_FLIP_HIERARCHY_REPORT_20261009.md](RD_FLIP_HIERARCHY_REPORT_20261009.md)**
（取代 RD_FLIP_HIERARCHY_RESULTS_20261009.md）。内容：
- 数学推导：
  - Arpaia 与 Campoli 的权重代数：二者差 −c₂/4，D−M 相同；
  - flip 缺陷恒等式；
  - 两种高阶端（均匀平移的 L∞/L2 极小性；receiver-only）、donor-cell 低阶端、θ 混合；
  - 约定 A/B；
  - 实际区间分层：registry、闭合集、live 掩码、各方案沉积、守恒论证、CFL ledger 正性；
  - lazy 的有效性；
  - "已证明 / 数值验证 / 假设"清单。
- 代码地图：行号对应 8e325e9。
- 全部冻结活动：每项说明能确立什么、有何局限。
- 结果表。
- 失败与局限。
- 优先审阅清单（§9，8 项）。
- 3D 展望（§10）。
- 复现命令。

**KH 分辨率研究完成**（`../local_runs/kh_flip_resolution_20261009_v1`）：
- mode 1 的熵偏移：glass48 为 0.35，glass96 为 0.32。对照：mode 0 为 1.07/0.71，Campoli 为 0.42/0.36，Arpaia 为 0.42/0.72。
- 两种模式对早期场的改变相近：48→96 比值在 t=1 为 1.6–2.0，t=2 为 1.4。
- KH 欠分辨，未达渐近区；需要 glass192+ 才能下收敛结论。

**资源预算违规（如实记录）。**
- 2026-10-09 曾同时运行约 13 个模拟加构建（负载最高约 50），超过 context_localMac.md 规定的 6–8。
- 结果互相独立，不受影响；但当天所有墙钟与 CPU 计时不可靠。报告只引用元素工作量与单次运行内的 CPU 占比。
- 此后遵守 6–8 的上限。

**3D（用户提问；未实现）。**
- 可直接推广：数学部分（|T|/4 集中质量、cavity 由 2-3/3-2/4-4 变化构成、registry/分层/lazy）。
- 关键差异：线性运动下四面体体积对时间是三次的，面法向是二次的；中点规则不满足离散 GCL，也不能保证分层中共享面通量相消。需要精确的时间积分法向（两点 Gauss 或 Simpson；Lesoinne & Farhat 1996，Farhat et al. 2001）。
- 另需 3D N/LDA/B（5×5 系统）、3D HLLC-RD 面，以及 MPI。
- 建议：
  - 终稿前只做 Python 3D 代数检查（kernel 与分层守恒），作为维度无关性的证据；
- 3D AREPO 集成（可基于 Ben Morton 的 3D 代码，需先审阅）放到提交之后。

## 223. 2026-10-09：Codex 独立审核 Claude 的 flip / interval hierarchy / lazy 工作

**作者：Codex（GPT-6）；用户要求先审核 Claude Code 的工作。**
审核 `feature/ale-flip-conservation-hierarchy` 的 `eacc3f9..9672ad7`。
完整审核：[RD_FLIP_HIERARCHY_CODEX_REVIEW_20261009.md](RD_FLIP_HIERARCHY_CODEX_REVIEW_20261009.md)。
证据：`../local_runs/codex_flip_review_20261009_v1/`。没有修改求解器或 thesis。

**结论。** 支持 Campoli + 局部 flip transfer + 实际区间闭合在已测二维周期、
单 rank 范围内实现舍入级守恒。补全 unequal-interval 共享边 / element-frame 总量抵消
与 frozen-node CFL ledger 的条件正性论证；未发现否定守恒主路径的反例。
对 LDA-KH、接口精度、MPI/restart、几何恢复与性能的限制仍须保留。

**四项 P2 发现。**
1. 默认变为 mode 1 后，当前脚本中的 `N_plain`/`N_plain_h1`、`N_lazy`/`N_lazy_h1`
   有效配置相同。须为 mode 0 显式赋值；冻结历史档案不受影响。
2. frozen 顶点 ledger ratio>1 仅计数并清零，未强制执行正性充分条件。
   已测 runs 未超限；这不是已复现的负压失败。
3. 原报告 Arpaia 推导遗漏初始 rebase。无 flip 共同区间的完整缺陷是
   `Σ(Snew−D)(Unew−Uold)`，不是仅末端 `Σ(Snew−D)Unew`。独立代数复现。
4. 报告的 matched-ID L1 差包含移动坐标改变，不能直接作为共同空间的场差/收敛阶。
   Yee48 N mode1 的解析采样差约占该指标 32%；各自坐标上的解析误差指标正确。

**验证。** 现有 `make check_rd` 全通过。五套冻结 source/binary/config/input/param
哈希关联及首末快照独立核验：156/163 完成，七个已披露的 LDA-KH 失败。
排除负对照后公共闭合最大误差约 3.53e-14；原摘要“全部 ≤2e-14”需修正。
9,654 个 production-default flip 探针保持正性、守恒 ≤9.04e-16；独立严格内能
floor 比较有舍入级差异，原失败样本保留，未宣称 strict-floor gate 通过。

冻结当前 9672ad7，独立构建显式 mode1 + lazy + natural 配置：
- uniform/N（2304 点，t=.25）：404 cavities，状态误差 4.89e-15。
- Yee/N（2304 点，t=1）：64 cavities，rho L1=2.91870e-3；natural 实际为等步长。
- Sedov/HLLC（16384 点，21/1 hot，t=.005）：89/87 cavities，正性通过；
  公共闭合误差 1.09e-14 / 3.84e-14，ledger ratio ≤.128。
- 仅补充短程默认组合证据，不替代 t=.05 长程验证。两个并发，OMP/BLAS=1。
  首次构建因 conda mpicc 的 PATH 优先级失败，保留 setup 日志；Homebrew 重试成功。

建议先修实验定义/CFL执行约束，再完成最终默认配置的完整 gates 和共同空间精度比较，
随后再考虑 KH192+、MPI/restart/3D。原报告保持不动，以上为独立审核更正。

## 224. 2026-10-09（续）：按 Codex 审核（§223）修正 R1–R4 与报告

**作者：Claude Code（Opus 5.5）；用户要求核查 Codex 指出的错误。四项全部核实并接受。未改 thesis。**
Codex 的审核文件、§223 与 handoff 原样以 Codex 署名单独提交（1000c67）；本节修正见 95a1a26。

- **R1（模式别名）。**
  - 所有驱动脚本的 transfer Config 现在显式写出 `RD_FLIP_HIGH_MODE`：原档案用旧默认值的写 0。
  - 新增 `tests/rd/flip_campaign_checks.py`：prepare 时若缺少 mode 或两个方法的 Config 相同，即报错。
  - campaign 元数据记录 `flip_high_mode`。
  - 历史冻结档案不受影响。
- **R2（CFL ledger 未强制）。**
  - 冻结顶点的比值若非有限，或超过 `RD_CFL_LEDGER_LIMIT`（默认 1），现在直接终止。
  - live 顶点的比值可合法达到 1.5，由其 stage 检查覆盖。
  - 冻结 gate `../local_runs/cfl_ledger_gate_20261009_v1`（Sedov21，HLLC，natural，mode 1，t=0.005）：
    - 默认限值：完成，ledger 最大 0.103；
    - 限值 0.05：按预期终止（0.0688 > 0.05）。
  - 仍没有自动重试或提前闭合。
- **R3（Arpaia 推导）。**
  - 我漏了步初的 rebase（SⁿUⁿ→DUⁿ）。无 flip 时的完整缺陷为 Σ ε(Uⁿ⁺¹−Uⁿ)，ε=Sⁿ⁺¹−D=Σc₂/12，每步 O(Δt³)；而不是只算末端的 Σ εUⁿ⁺¹。
  - 我在对话中给用户的解释同样有误，已更正。
  - "Sedov 中转换泄漏可忽略"只是对该问题的直接对照，不是一般结论。
- **R4（matched-ID 指标）。**
  - 原"transfer−无 transfer ρL1"是同 ID、不同末坐标的轨迹差，不是 Eulerian 场差，不能给出收敛阶。
  - 已改名为 matched-ID difference，并记录平均位移；新增 analytic-error increase（各自坐标上的解析误差之差）。
  - Yee 中 transfer 带来的误差增量，glass48→96 下降 3–7×（N 1.18e-4→3.4e-5），但只有两个分辨率、对照不守恒，因此不宣称阶数。
  - 公共空间比较、第三分辨率（Yee192）与 dt 控制列为下一步。
- **其他。**
  - 守恒上限更正为约 3.5e-14。
  - 混合时端点相等的值直接复制，mode 1 的 donor 对任意 θ 都逐位不变（kernel 测试已断言；check_rd 12/12）。
  - "不需要限制"仅指 KH runs。
  - lazy 阈值不是"不会翻转"的保证。
  - KH 网格距离不是误差界。
  - 2026-10-09 的计时不可引用。
- **报告。** [RD_FLIP_HIERARCHY_REPORT_20261009.md](RD_FLIP_HIERARCHY_REPORT_20261009.md) 顶部新增勘误块，正文就地更正并标注 *(corrected)*。
- **下一步（按 Codex 建议顺序）。**
  1. 对最终默认配置（mode 1 + lazy + natural）做完整冻结 gate：Sedov 1/21 到 t=0.05；N/LDA/B 的 mode 1 等步长退化、混合 bin 与负对照；几何翻转失败 gate。
  2. 光滑解在公共空间比较，加入 Yee192 与 dt 减半。
  3. 之后再考虑 KH192+、MPI/restart/3D。
