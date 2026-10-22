# Proposed COSMA Blob campaign: reference matching, mesh and resolution

2026-10-22 — Codex (GPT-6), with Zhenyu Wu. Prepared on the local Mac.

**Status: recommendations for subsequent implementation and submission.**
No new IC adapter, configuration, executable, Slurm script or simulation is
provided or validated by this document. The current checkout remains
`feature/3d-moving-mesh`, HEAD `35ecccd16083`, with earlier uncommitted work.
See shared-log entries 21--25 and the
[numerical setup comparison](RD_3D_BLOB_REFERENCE_SETUPS_20261022.md).

## 1. Questions and interpretation

Keep two controls distinct: a Morton setup for the unresolved N1/current
lifetime difference, and a Braspenning setup for comparisons against other
hydrodynamic methods. Within the latter, measure sensitivity to resolution,
point arrangement and tetrahedron shape separately from time integration,
hierarchical scheduling and MPI partitioning.

[Braspenning sections 3.1, 3.4 and 4](https://arxiv.org/html/2203.13915v2#S3.SS1)
do not establish universal non-convergence. Several dense-gas curves become
insensitive to the tested resolution range, while behavior depends on chi,
method and diagnostic. Intermediate-temperature gas, covering fractions and
small-scale morphology need separate assessment. Common-scale coarse-graining
can alter the comparison. A converged dense-gas curve alone is insufficient
evidence of converged thermal mixing or morphology.

No physical viscosity or conduction is specified for this campaign; retain
the inviscid non-radiative reference. Numerical phase mixing and increasingly
fine unstable structure make this a demanding convergence test, not an
analytic accuracy standard. Do not add diffusion to force convergence, or
assume that higher resolution must move the lifetime monotonically toward
one reference curve. An optional regularized physical problem would be a
separately defined study.

## 2. Reference and loading gates before long jobs

1. Download and checksum the official ICs linked from SWIFT's dedicated
   [BlobTest_Braspenning2022](https://github.com/SWIFTSIM/SWIFT/tree/4a7fadaf4a0e23ed60dcddb29d17cca7d8a7182c/examples/HydroTests/BlobTest_Braspenning2022)
   example on COSMA if reachable. Read their units, box, counts, coordinates,
   masses, velocities and internal energies. Compute actual Mach and chi;
   do not infer them from the filename or generic BlobTest_3D script.
   Mac access timed out in entry 24; the reference counts below are estimates.
2. Preserve the downloaded particle masses as reference metadata. They are
   not directly RD nodal densities. For the current RD input convention,
   initialize the analytic phase density in the input Masses field, let the
   native median dual define the evolved extensive mass, then measure total
   and cloud mass after loading. Record the resulting difference from the
   reference sampling/mass quadrature. Do not silently interpret equal SPH
   masses as density or rescale phase states to force integrated agreement.
3. Reproduce the rectangular periodic domain explicitly. AREPO has LONG_X
   support (`src/init/begrun.c`); BoxSize=1 and LONG_X=4 is the natural
   R=0.1 representation. The RD adapter reads unfolded native point images
   and audits coverage using all three box extents. This source evidence
   does not validate the long-box RD path. The existing Blob generator is
   cubic and must be adapted, including HDF5 header/parameter conventions.
   Check actual extents, periodic seams and sum(dual)=4 before production.
4. Use short uniform/smooth tests on the long box at 1/2/4 ranks, then chi=10
   Blob to 0.05 t_cc at low resolution. Require existing raw geometry,
   conservation, positivity and MPI audits to pass. Record rank differences
   with ID-sorted states on matching physical times and the same global mesh.
   Archive failures without weakening checks or silently jittering an IC.
5. Add a no-wind isobaric-cloud control on each candidate geometry to 0.05
   t_cc, using the *reference wind's* t_cc only as a fixed reporting unit.
   This isolates startup/contact errors without the intended wind shock.
   Record nodal versus reconstructed pressure separately: entry 22 already
   demonstrates a contact limitation shared with the predecessor.

Match the loaded dimensionless state before interpreting a literature curve.
An adapted sampling experiment is still useful if the official files remain
unavailable, but label it as such rather than as an exact IC reproduction.

## 3. A staged allocation rather than a full factorial campaign

Use static N/lumped RK2 with equal steps as the first native method. Pure LDA
already fails the present Blob and is not a required sweep; 3D moving RD and
HLLC-RD are outside this campaign's implemented baseline.

| Stage | Proposed cases | Endpoint and decision |
| --- | --- | --- |
| A: loading and cost | long-box uniform/smooth; n=16, chi=10 Blob; one short n=32 case | uniform gates, then 0.05 t_cc; measure memory, steps, work and output size |
| B: first reference | official/adapted chi=10, n=32, N/RK2 equal; one SWIFT reference with the same official IC if available | first 1 t_cc; extend to 5 and 10 t_cc after cost/stability review |
| C: mesh sensitivity | n=32, chi=10; official grid, jittered grid and uniform-random or glass sampling; retain cloud-enhanced point density | short contact/pipeline gates first; selected cases through 5--10 t_cc |
| D: resolution | one fixed mesh-generation family at n=16,32,64; n=128 only after a measured resource decision | n=16 is mainly a coarse control; two useful levels show trends, not asymptotic convergence |
| E: contrast | chi=100, n=16 loading pilot, then n=32; selected n=64 | keep the same reference rules, not the same cloud point count as chi=10 |
| F: scheduling/MPI | one selected n=32 IC, equal versus hierarchy; short 1/2/4-rank checks, measured 8/16-rank timing if useful | match outputs and actual work; extend a physical pair only after short agreement |

For asymptotic claims, seek at least three adequately resolved levels
(potentially n=32,64,128), and compare changes to mesh-realization scatter.
Do not launch all contrasts, seeds, methods, ranks and resolutions together.
Archive each stage separately so partial scientific progress survives budget
or positivity limits. No stage above is currently submitted.

For the separate Morton track, use the existing cube/IC and actual v=6.15.
Compare forward Euler N1 and current Heun on the same tetrahedra, with a
controlled actual timestep and a dt/2 control. The current native 3D compile
guard requires RK2; removing that flag does not create an available N1 build.
An independently audited native adapter or full standalone replay is still
needed. Preserve the predecessor timestep-loop defect as evidence, not a
baseline to copy. Retrieve the original Fig. 20 time/mass calculation.

## 4. Mesh shape must be measured, not just named

Separate domain aspect ratio, point sampling and tetrahedral quality. For
the shape comparison, hold box, radius, chi, Mach, per-phase point-count
targets, density/pressure assignment, integration and analysis fixed. A
uniform-random control must still have the reference's enhanced cloud point
density; otherwise it changes local resolution as well as shape.

Retain the unmodified official grid as one family. For disordered families,
use at least three fixed seeds at n=32 initially (including 68315 where
applicable); report each result and the ensemble spread. Fix and record any
jitter amplitude relative to local spacing, phase-boundary treatment,
relaxation procedure and periodic translations of the grid relative to the
cloud. These are explicit variants. Refinement changes the wavelengths of
unseeded numerical perturbations; a separate fixed-physical-perturbation
family can help diagnose that effect but changes the original reference IC.

Exact lattice points can be co-spherical and admit non-unique Delaunay
diagonals. Record degeneracy handling and connectivity/geometry agreement
across ranks. An explicit jittered variant must not replace a failed official
grid without disclosure. Compare measured initial masses for all variants;
normalize mass histories by their own recorded initial mass and report
quadrature differences rather than altering densities to conceal them.

Archive, at minimum, the following for the bulk and cloud-interface elements:

- node and tetrahedron counts; cloud nodes; local spacing and nearest-neighbor
  distributions; median-dual volumes and cloud mass quadrature;
- positive oriented volumes, face areas, minimum altitudes, dihedral angles
  and a sliver-sensitive quality measure, e.g. q=3*r_in/R_circ (one for a
  regular tetrahedron, approaching zero for degenerate shapes); edge ratios
  alone do not identify all slivers;
- minima and 0.1/1/50-percentiles, plus spatial locations of the poorest cells;
  inherited spectral-solve audit/SVD usage and selected element timesteps;
- startup pressure/velocity errors and their association with interface
  cells, quality and initial P1-Z pressure structure.

In static runs the geometry is fixed, so an initial complete quality audit
is usually sufficient. First exclude time error with dt and dt/2 on the
reference and a poor-quality control; compare actual accepted steps rather
than equating CFL labels. A quality/lifetime correlation alone is not proof
of causation.

## 5. Diagnostics and what convergence would mean

Save at common requested t/t_cc, with extra early outputs and explicit maps
near 0, 1, 3, 5 and 10 t_cc where reached. Actual output times must accompany
the request schedule; record the interpolation rule if comparing nonmatching
times. Do not treat interpolated state differences as direct MPI evidence.

Report native dense-gas mass for rho>rho_cloud/3, the Morton combined cut,
and the already used density thresholds. Keep these definitions fixed across
resolution. Report half-mass and first-zero brackets, full mass curves,
intermediate-temperature mass with the paper's IC/unit/conversion convention,
temperature-density/entropy distributions and matched XY/XZ/YZ density and
pressure sections. Density-threshold mass is Eulerian; no material tracer
currently identifies surviving original cloud material.

Also apply one fixed physical coarse-graining scale to the usable resolution
levels: transverse 32-bin sampling means **128x32x32 bins** in the 4:1:1
domain, not 32x32x32 over the whole tunnel. Reproduce the paper's center-bin
mass deposition and mass-weighted thermodynamic averages as one explicitly
labelled analysis. Define periodic cloud centering and the no-dense-gas
fallback before analysis; report empty bins and under-sampled coarse maps.
Native thresholding and thresholding after coarse-graining are different
diagnostics. A smoother coarse curve does not validate microscopic mixing.

Judge resolution changes against dt sensitivity and seed spread, separately
for dense gas, intermediate-temperature gas and morphology. Report finite
resolution insensitivity only for the actual diagnostic/time interval/mesh
family tested. Similar mass curves do not require identical unstable fine
structure, and dissimilar pictures alone do not establish non-convergence.

## 6. COSMA handoff and cost record

Build/run on compute nodes with the configured COSMA environment, isolated
BUILD_DIR/executable/OutputDir and source/Config/IC/parameter/binary/linkage
hashes. Set OMP_NUM_THREADS, OPENBLAS_NUM_THREADS and MKL_NUM_THREADS to one.
Use [COSMA context](context_cosma.md) for the historical scheduler/account
and storage locations; recheck their current availability before submission.
The Mac audit archive and original IC downloads are not transferred by Git.

The completed 32768-node cube at eight ranks took 5.178 h equal or 2.832 h
hierarchy to 3 t_cc. This is a measured pair, not MPI scaling or a wall-time
prediction for the new geometry. At n=32 the reference has about four times
as many points; n=64 already has about 1.06--1.16 million. Slivers, timestep
selection and phase sampling can alter cost substantially. Calibrate each
new family and measure peak per-rank memory, stage work, accepted steps,
CPU/wall time and snapshot volume before requesting longer jobs. Do not
assume the observed hierarchy factor 1.828 transfers to the new setup.

Required return bundle: campaign inventory/status including failed jobs;
exact source/config/IC provenance and conversion audit; geometry summaries;
time histories with definitions/actual times; selected raw snapshots;
conservation/positivity/MPI/timestep diagnostics; and measured resource use.
Keep large campaigns off the small home quota. Compare the original SWIFT
method/version/flags explicitly; a current default SWIFT run is an independent
reference, not automatically the paper's production run.
