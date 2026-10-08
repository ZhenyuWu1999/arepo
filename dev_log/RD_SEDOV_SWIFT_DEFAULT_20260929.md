# Local SWIFT default Sedov 2D run, 2026-09-29

Author: Codex. User requested a local run of SWIFT's default Sedov example
for comparison with the current moving RD results.

## Run and provenance

**Completed successfully to t=.05 in 2.189 s of process wall time**, with396
evolution steps after initialization and six snapshots at0,.01,.02,.03,.04,.05.
No hydrodynamics parameters, initial-condition generator or solver were edited.

The pre-existing `/Users/zhenyuwu/SWIFT/build-localmac/swift` identified itself
as revision7fbba7e0-dirty, whereas the clean source checkout is
`8dc43c3c1f08755250a2c0edd141d78120d00b21`. It was not used for this science run.
A git archive of the current revision was extracted into an isolated directory
and built from scratch using the established Apple-Silicon 2D build options.
Autotools/configuration/build took approximately8.35/22.62/20.89 s. The archive
has no .git, so the executable reports unknown Git metadata; the exact source
revision and tar hash are recorded independently, rather than inferred from
that banner.

Archive: `../local_runs/swift_sedov_default_20260929_v1/`.

- Source tar SHA256: `e12d8d8e956b9d75e9d7c1d03424838b350fe1b095d7be44112044aecd93f29a`.
- Binary SHA256: `e7787bed22deacfff7634c250085d05cd80a97b4f4b078c6d8c7ad5b678a907d`.
- Frozen config, configure/build logs, linkage and executable are under `artifact/`.
- Unchanged stock makeIC.py/sedov.yml/run.sh/plotSolution.py, input glass,
  generated IC, runtime logs, used/unused parameters and outputs are under `run/`.
- Runner: `examples/Sedov_2d/run_swift_default.py`.
- Analysis: `examples/Sedov_2d/analyze_swift_default.py`.

One serial process, one SWIFT task/thread-pool thread,
OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1. MPI support is available in the build,
but the serial executable was used. Handwritten vectorization is disabled for
the local ARM platform; hydro method defaults are unchanged. A non-optimal
thread-barrier warning affects performance, not an asserted numerical failure.

## Confirmed configuration

SPHENIX (the source version's default hydro scheme), 2D, cubic-spline M4 kernel,
gamma5/3, ideal gas, no pressure floor, minimum specific internal energy0.
Runtime metadata confirms resolution_eta1.2348 corresponds to **15.14285
unweighted target neighbours in2D**, not48 as the generic YAML comment states.
Default artificial viscosity has initialalpha.1/max2/min0; artificial thermal
diffusion has initialalpha0/max1. The timestep limiter is enabled exactly as
in stock run.sh, allowing maximum neighbour time-bin difference2. Hierarchical
particle timesteps are active; this is not the equal-step RD integrator.

Unchanged physical inputs: periodic unit square, glass128²=16384 particles,
rho0=1,pbg1e−6,Ehot1, zero input velocity, nearest21 heated particles. Stock
float IC storage gives total input energy1.000001516703897. Max requested
timestep.01, CFL.1; the dyadic timeline's cap is.00625. Final time.05 and
snapshot interval.01 are unchanged.

## Results against moving Rusanov RD

The primary comparison is SWIFT21 versus RD21: same glass and heated set,
with the previously documented small mass-normalization difference. RD1 is
shown as the latest additional experiment. RD uses Rusanov spatial residual,
lumped RK2, adaptive equal steps and no connectivity repair. It is not LDA.
All radial coordinates use each initial injected-excess-energy centroid.
The SWIFT/RD21 centroids differ by only about4e−6; RD1 is naturally offset.

| t=.05 diagnostic | SWIFT21 | Moving RD21 | Moving RD1 |
|---|---:|---:|---:|
| Min nodal/particle density |.0368658|.196009|.195762|
| Max nodal/particle density |3.60417|2.63044|2.61579|
| Relative mass change |0|−.239707%|−.237630%|
| Energy change relative to input IC |+.0400534%|−2.414700%|−2.576317%|
| Number inside r<.05 |7|3|1|
| Number inside r<.1 |21|12|7|
| Number inside r<.15 |116|72|78|

The cylindrical analytic shock density is4. SWIFT resolves a sharper, higher
shell peak and lower central density. The radial-mean density also follows
the analytic inner profile more closely. This supports the importance of
diffusion in the current low-order RD result, but is not a controlled change
of RD spatial order alone.

SWIFT is **not uniformly closer to the analytic solution**. Its core has large
pressure deviations and radial-velocity scatter, including some inward
velocities. For actual particles in0<r<.05, unweighted meanp=2.3766 versus
analytic values at those particles1.60516. In.05<r<.1, meanp=2.95481 versus
1.60987; in.1<r<.15, meanp=1.34483 versus1.67446. Individual core pressures
span.8282–3.2264 and radial velocities−.4025–1.3027. These values are retained
in the plot; they are not clipped or deleted as outliers. The current RD
pressure profile is smoother and closer in parts of the core, despite its
worse density rarefaction and global energy budget.

The default low neighbour count and finite heated particle set are relevant
context, but no additional neighbour-number or SPH formulation sweep was run.
Do not claim those settings uniquely explain the pressure feature. SPH density
is a kernel estimate, whereas RD density is tied to its dual-area mass; same
particle count does not imply identical effective resolution.

### Energy normalization detail

SWIFT's saved t=0 state is not byte-identical to the zero-velocity IC: specific
internal energies are unchanged but saved velocities have maximum component
1.82056, giving total saved energy1.001531130188754. Snapshot and statistics
velocity export both use `hydro/SPHENIX/hydro_io.h:convert_part_vel`, which
extrapolates the leapfrog velocity to the output time. The initial fake step
and this output convention must be accounted for when choosing a baseline;
we have not instrumented that lifecycle to establish a separate hydro defect.

The final snapshot energy is1.000402051126305: +.0400534% relative to the actual
zero-velocity input IC, or −.1127353% relative to the first saved state.
The independent statistics file gives +.0400483% relative to input and
−.1127886% relative to its own first row, consistent to output precision.
The budget figure uses the **input IC baseline** and shows the initial output
offset openly. Neither definition supports exact SWIFT energy conservation;
both give much smaller error than the present moving RD runs.

## Validation and deliverables

All six saved SWIFT states have finite, positive rho, pressure and internal
energy; IDs and individual masses are preserved exactly, and actual output
times match the configured sequence. This audits saved states, not every
internal stage. The binary/config/source/input hashes and the reused RD
binary/config/snapshot provenance were checked before comparison.

`analysis/verification.json` contains all checks, hydro metadata, annular
values and both energy baselines. The analytic reference uses the previously
checked dense central sampling (integrated energy1.000000024).

- `analysis/swift_rd_profiles.png` and `.pdf`: full profiles plus core detail,
  300dpi PNG, raw samples and unweighted means in radial bins of width.005.
  Empty bins are left empty rather than bridged with fabricated samples.
- `analysis/swift_rd_budgets.png`: mass/energy histories, IC normalization.

Both figures were visually checked. `analysis_initial/` preserves the first
render, whose core axis limits were too narrow for SWIFT's pressure/velocity
range and whose energy baseline was the first output; the current figures
correct these presentation issues without changing any native results.

No active solver remains. No AREPO solver, default Config, original SWIFT
checkout, thesis, COSMA, commit or push was changed in this task.
