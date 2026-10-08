# Local two-dimensional Sedov pilot

The initial pilot follows the physical setup in the local SWIFT
`examples/HydroTests/SedovBlast_2D`: unit periodic box, glass128 (16384 nodes),
gamma = 5/3, initial density 1, velocity 0, background pressure 1e-6, central
thermal energy 1, and target time 0.05. The first seed heats the nearest
21 nodes. Their maximum radius is about 0.0196.

The RD initial density is uniform. Its nodal masses are the native median-dual
areas, not equal SPH particle masses. Accordingly, the common hot specific
energy is `1 / sum(m_hot)`. This deposits exactly one unit of energy in the
hot region; the cold background contributes its small additional energy.
Periodic SciPy Delaunay areas used to normalize the seed are checked against
native AREPO initial snapshot masses before science runs are allowed.

The first comparison reuses frozen, verified native binaries for static and
moving N/Roe/lumped RK2, and static and moving LDA/Gauss3/F1 RK2. The moving
methods use the current equal-step ALE hooks and RD spectral CFL restriction.
All use the laboratory frame, standard mesh regularization, global equal
adaptive timesteps, Courant factor 0.1 and maximum timestep 0.01. The cap is
not intended to impose a fixed timestep. No new floor, limiter or changed
assertion is introduced. There is no gravity or cosmological integration.

`run.py prepare ARCHIVE` creates inputs and copies source provenance,
binaries, Configs, linkage and reference scripts. `run.py run ARCHIVE --group
uniform` runs native uniform-state gates. `--group nearest21` runs the initial
Sedov set. Both OpenMP and BLAS are restricted to one thread; the runner uses
at most two simultaneous single-rank solvers. Existing outputs are never
overwritten. Source production-file hashes must match the archived binaries.

The September 29 archive additionally contains explicitly separated controls:

- `disk005`: same energy and cold background, but a radius-0.05 circular seed
  containing 130 nodes; CFL remains 0.1.
- `half_cfl21`: the original 21-node IC, N schemes with CFL 0.05.
- `nearest21_N_static_firstorder`: the original IC and CFL 0.1, but the frozen
  static predictor-only first-order N binary, with its own uniform gate.
- `early21`: two short LDA runs used to locate their immediate failures.

Seven snapshots are requested in diagnostic controls to locate failure onset;
their actual times can be slightly later than requested because outputs occur
on the next native synchronization. Failed outputs and logs are retained.

`analyze.py ARCHIVE --group GROUP` verifies IC energy, source/input/binary
hashes, saved-state positivity, static coordinates, uniform-state errors and
mass/energy changes. Only runs reaching their target are shown as completed
results. Plots retain raw nodal scatter and unweighted radial-bin means.

The analytic reference is the **two-dimensional cylindrical** Sedov solution,
using the three analytic functions from the archived SWIFT plotting script
with dimension `nu=2`. Its shock radius scales as `t**0.5`; its energy integral
and shock jump are checked. A finite seed has an initial transient and is not
the exact point-source initial condition.

Morton et al. (2023), section 5.2.3, motivates distributed injection by the
strong directional asymmetry caused by a single heated vertex; it does not
state that every single-point injection necessarily fails. It also reports
unstable LDA results for this test. The local standalone Morton source uses
different dimensional parameters and a less extreme hot/cold pressure ratio;
this pilot is not an exact reproduction of its Figure 13.

Reference: https://arxiv.org/html/2204.01757v2#S5.SS2.SSS3

Results and limitations are recorded in the local archive and the associated
development-log entry. These are local experiments, not thesis additions.

## Optional positivity experiment (2026-09-29)

`Config_Rusanov_static.sh` and `Config_Rusanov_moving.sh` select
`RD_RUSANOV_LOW_ORDER`. This bypasses the Roe N spatial residual entirely;
`N_SCHEME` selects the existing lumped temporal machinery only. The new
spatial residual is Rusanov with trapezoidal fluxes, not LDA/Gauss3. Its
dissipation uses all endpoint wave speeds. It checks admissible pair states,
actual predictor/corrector CFL bounds, ALE convex weights and stage density
and internal energy before primitive recovery. It never repairs a failed
state by clipping. This is a single-rank equal-step experiment, not an MPI or
hierarchical scheme and not a high-order limiter.

Use `run_positivity.py prepare ARCHIVE`, then `build ARCHIVE` to freeze and
build the working implementation independently. Run `run ARCHIVE --group
uniform` first, followed by `nearest21` and `disk005`. Each command uses at
most two solvers; do not exceed four total simultaneous solvers for these
128² comparisons. `analyze_positivity.py ARCHIVE` audits stage positivity,
endpoint mass/energy, provenance and completed radial profiles. The prepare
step uses the original pilot archive as the source of byte-identical ICs.

The old N baseline is also rebuilt with the new flag absent for a short
regression. The actual September 29 campaign additionally ran the original
archived N binary with identical numerical parameters; all five snapshots
matched bitwise by particle ID.

The moving prototype retains the existing modified-area and connectivity
treatment. Positivity does not imply physical endpoint conservation. See
[`RD_SEDOV_POSITIVITY_20260929.md`](../../dev_log/RD_SEDOV_POSITIVITY_20260929.md)
for the derivation, literature, native results and remaining LDA/remap work.

`run_positivity.py prepare ARCHIVE --topology-repair` prepares a separate
moving comparison using the existing unlimited connectivity repair. In this
Rusanov combination only, predictor primitives are recovered from the repaired
state; interval mesh velocities remain fixed. The repair itself has no
positivity guarantee: both strong Sedov seeds terminate with negative pressure
inside the repair, before the next physical update. Do not use this as a
validated positivity-preserving configuration. `analyze_topology_repair.py
ARCHIVE BASELINE_ARCHIVE` audits the failures and compares endpoint budgets.
See [the repair report](../../dev_log/RD_SEDOV_TOPOLOGY_REPAIR_20260929.md).

## Smaller injection controls

`run_injection_sweep.py prepare ARCHIVE` copies the separately frozen moving
Rusanov binaries with and without the unlimited topology repair, including
each binary's own source archive and build provenance. It generates 1-node
and 7-node seeds on the same glass128² positions, keeping hot energy exactly
one and background pressure 1e-6. Run `run ARCHIVE --group uniform` first,
then `--group nearest1` and `--group nearest7`. The two science commands may
run concurrently, for a maximum of four single-rank solvers.

`analyze_injection_sweep.py ARCHIVE RUSANOV_BASELINE_ARCHIVE` audits the
accepted stages, failures, saved states and source/input hashes, and compares
completed runs against the archived 21-node seed. Radial profiles are centered
on the initial excess-energy centroid: the nearest single glass node is not
exactly at the box center. The locally supplied SWIFT SedovBlast_2D generator
defaults to 21 heated particles, despite its singular "central particle"
comment. No SWIFT hydro simulation is performed by this comparison.
