# Portable static 3D Blob analysis

Two standalone scripts need only NumPy and h5py. Matplotlib is optional for
`analyse.py --plot`. No AREPO repository, compiler, MPI, SciPy or COSMA module
is needed on the Mac.

## Run on the Mac

Use your existing Python environment containing NumPy/h5py, or install the
small requirements list into a virtual environment.

    python3 scripts/analyse.py . --out analysis_mac
    python3 scripts/analyse.py . --out analysis_mac --plot

A standalone snapshot folder also works:

    python3 scripts/analyse.py /path/to/output --out analysis_mac

The latter cannot infer a solver exit status without the bundle metadata.
For the bundled failed LDA cases, checking their initial snapshot does not
mean the simulation completed or the rejected raw state was positive.

CSV files contain actual saved times, normalized times, threshold cloud mass,
finite-state minima and five-component conservation defects. The summary JSON
keeps solver completion/failure separate from checks of saved snapshots.
Optional plots show available time histories; failed LDA cases have only t=0.

## Regenerate the IC

    python3 scripts/make_ic.py blob32_regenerated.hdf5 --n 32

The default random seed is 68315. The script refuses to overwrite a file.
Its particle arrays and Header attributes reproduce the archived ICs; HDF5
file bytes/checksums can vary with HDF5 versions. Input `Masses` stores
**density** under `READ_MASS_AS_DENSITY_IN_INPUT`. Snapshot `Masses` stores
actual extensive mass. Use snapshot `Masses/Density` as the RD median-dual
volume rather than the separately stored Voronoi `Volume`.

## Physical and numerical context

Periodic cube side 10; cloud centre (2.5,5,5), radius 1; cloud/wind density
100/10; uniform pressure 100; gamma 5/3; wind vx=6.15; cloud vx=1e-8;
transverse velocities=1e-7. Define t_cr=2 R sqrt(10)/6.15, including the factor
two. Cloud mass selects rho>64 and p/rho<9; it is not a material tracer.

The two N cases completed to 1.5 t_cr on 32768 random generators, with 140
initial cloud nodes. Both LDA cases failed a raw stage-1 negative-pressure
check near .02142334 t_cr, ID 14151, and have only the initial full-run
snapshot. N uses lumped/RK2 and LDA uses the current F1/RK2 path. Neither is
paper N1; the RK2 flag alone does not establish formal temporal order.
Hierarchy and equal-step trajectories need not agree exactly. Compare actual
saved times rather than treating requested .05 t_cr output intervals as exact.

`cases/` holds full-run snapshots and small original parameter/status/result
records. `configs/` and per-case `provenance/` preserve exact native settings
and binary/source fingerprints. `provenance/` identifies the full originals
on COSMA. LDA native failure logs are gzip-compressed. No solver binaries,
object files, restart dumps, large performance logs or full source archives
are included. The originals are retained on COSMA.

Check file integrity with `shasum -a 256 -c SHA256SUMS` on macOS. This verifies
packaged bytes, not physical convergence or correctness of unimplemented
moving-3D methods. No simulation is rerun by these scripts.
