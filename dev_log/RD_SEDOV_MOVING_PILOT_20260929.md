# Moving-mesh Sedov pilot, 2026-09-29

Author: Codex. User requested a first moving-mesh Sedov trial, referring to
the local SWIFT SedovBlast_2D example and Morton (2023).

**Outcome:** The current moving N and LDA methods do not complete this strong
blast test. Enlarging the injection region makes static N/RK2 complete, but
moving N/RK2 still develops negative mass. Halving CFL does not rescue the
21-node case. No solver fix or thesis edit is included in this experiment.

## Reference and initial conditions

Morton et al. (2023), [section 5.2.3](https://arxiv.org/html/2204.01757v2#S5.SS2.SSS3),
explains that heating one vertex makes propagation strongly directional along
its few mesh connections. They therefore heat a circular region. This is a
symmetry argument, not a statement that every single-vertex case must crash.
The paper also reports unstable LDA results for Sedov.

The local SWIFT example (revision `8dc43c3c1f08755250a2c0edd141d78120d00b21`)
uses glass128, a unit periodic box, gamma=5/3, rho0=1, P0=1e-6, zero velocity,
E0=1, the nearest21 particles, CFL0.1 and final time0.05. Its files were copied
unchanged to the archive's `reference/` directory with hashes.

The RD pilot uses those physical parameters, but uniform density implies
unequal median-dual nodal masses. Hot specific energy is normalized with the
actual sum of hot nodal masses, rather than SWIFT's equal particle mass. The
periodic Delaunay areas used in IC generation are independently checked
against native initial-snapshot masses. The total *hot-region* energy is1;
the cold exterior adds a small background contribution.

| Seed | Heated nodes | Outer radius | Hot pressure | Initial total energy |
|---|---:|---:|---:|---:|
| Nearest21 |21|0.01959655049|520.8929463|1.00000149808022|
| Circular disk |130|0.05|84.03502948|1.00000148810020|

Both are finite injection regions; neither is a single-point experiment.
The local standalone Morton source has box10, radius0.25, hot/background
pressures1e6/100 and CFL0.2. Its pressure contrast is much smaller. This pilot
is not a reproduction of the original paper's initial conditions or figure.

**Later correction (2026-09-29, log3 §161):** The hot pressure above describes
the provisional setup assignment, not the full initialization. The committed
Morton `main.cpp` subsequently normalizes hot-region energy to 300000 using
the mesh's actual hot dual area. See the [complete scale audit](RD_SEDOV_CORE_REFERENCE_AUDIT_20260929.md)
for the source provenance and dimensionless comparison.

## Methods and native checks

Reused individually hashed, frozen binaries from the September27 Gresho
campaign: N/Roe/lumped RK2 and LDA/Gauss3/F1 RK2, each static and moving.
All production source hashes match the current checkout. Moving configurations
use RD_ALE_EQUALSTEP, split stages, mesh regularization and the RD spectral CFL
constraint; all calculations use the lab frame and global equal timesteps.
No new limiter, floor, frame transformation or relaxed assertion was added.
`MinEgySpec=0` retains the existing primitive-recovery zero-energy floor; saved
state positivity does not establish that all intermediate states stayed positive.

A separate frozen static first-order N binary from the Morton Sod campaign
was checked against the same production source and given its own uniform gate.
Five glass128 uniform gates passed with maximum state defect8.88e-16.
Every run uses one MPI rank, OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1.
Each runner uses two workers; overlapping diagnostic runners reached at most
four solvers. Native outputs, failures, configuration, source tar, linkage,
binary/input hashes and scripts are retained. No new hydrodynamics build was
needed. All18 native attempts are finished: five uniform gates and thirteen
science/diagnostic attempts, including two early LDA failure-localization runs.

The main CFL is0.1 with maximum step0.01, so these are adaptive CFL-selected
dyadic timesteps, not the matched fixed steps used for the vortex comparisons.
Half-CFL controls use0.05 and identical ICs. Seven saved times in later
controls localize failure onset; actual output times follow native sync points.

## Results

Times below are the last logged synchronization/failed update times. For the
two short LDA localization runs, changing TimeMax to0.002 also changes the
dyadic timeline; their exact first-failure times differ slightly from the
main0.05 runs. These are not independent successful science results.

| Seed | Method | CFL | Final/failed time | Result |
|---|---|---:|---:|---|
|21|Static N/RK2|0.1|0.00672073|Predictor negative pressure, ID8228|
|21|Moving N/RK2|0.1|0.00226440|Negative mass after corrector, ID8259|
|21|Static LDA/F1|0.1|0.0000244141|Predictor negative pressure|
|21|Moving LDA/F1|0.1|0.0000122070|Predictor negative pressure|
|130|Static N/RK2|0.1|**0.05**|**Completed**|
|130|Moving N/RK2|0.1|0.00828857|Negative mass after corrector, ID8277|
|130|Static LDA/F1|0.1|0.0000732422|Predictor negative pressure|
|130|Moving LDA/F1|0.1|0.0000366211|Predictor negative pressure|
|21|Static N/RK2|0.05|0.00672493|Predictor negative pressure, same ID8228|
|21|Moving N/RK2|0.05|0.00296021|Negative mass after corrector, ID8126|
|21|Static first-order N|0.1|0.00663452|Negative mass, ID8228|

For the130-node moving N failure, the predictor's minimum density is still
7.938554e-4 before the corrector; the later mass check finds -4.40857e-7.
The midpoint CFL diagnostic remained above the selected step: its minimum
ratio is1.1087 for21 nodes and1.184958 for130 nodes. Thus these failures are not
explained simply by exceeding that recorded spectral bound. This does not
prove a positivity bound for the nonlinear Euler update or identify the root
cause. The static first-order failure also rules out treating all observed
failures as uniquely due to the RK2 second stage.

The completed static N disk run takes1942 steps. At0.05, rho_min=0.04377381,
rho_max=2.42160966 and p_min=1e-6; final relative mass drift is0 and energy drift
is-2.22e-16. The shock is broadened, and the interior velocity has substantial
nodal scatter, including negative radial velocities. Completion is not a
claim of high accuracy or a general robustness result.

At the matched saved time0.0050048828125, moving N has a sharper shell but
relative energy drift-0.00650671 (about-0.65%) and mass drift+3.00169e-6.
The energy drift varies later; this value is specifically the plotted saved
state, not the failed endpoint. The step-end ledger immediately before the
130-node failure reaches roughly+0.75% energy drift and includes an invalid
mass, so it is not a valid physical endpoint. The21-node moving failure and
half-CFL failure have ledger energy deficits about2.90% and3.76%, respectively.

## Analytic reference and artifacts

The analytic curves use SWIFT's **two-dimensional cylindrical** solution
(`nu=2`), with R proportional to t^(1/2). The shock radius at0.05 is
0.2579946124. The energy integral and strong-shock density jump4 are checked.
Finite injection introduces a transient; early maps are explicitly marked as
states before failure and are not presented as completed Sedov solutions.

Archive: `../../local_runs/sedov_2d_20260929_v1/`.

- `analysis/disk005/early_density.png`: matched static/moving maps at0.005005;
  cyan circle marks the initial injection radius, not the analytic shock.
- `analysis/disk005/profiles.png`: completed static N profiles at0.05 against
  the2D similarity solution, all raw scatter plus unweighted radial means.
- `analysis/disk005/density.png`: completed static N density map.
- `analysis/*/summary.json`: snapshot hashes, positivity, conservation,
  timesteps, completion status and exact native failure lines.
- `campaign.json`, `artifacts/`, `reference/`, `inputs/`, `runs/`: full setup
  and audit trail, including failed cases.

Canonical preparation/analysis entry points are in `examples/Sedov_2d/`.
The next issue to investigate is positivity and conservation in the strong
blast update, including the moving corrector and geometry changes. No cause
has been isolated sufficiently to justify a solver modification here.
