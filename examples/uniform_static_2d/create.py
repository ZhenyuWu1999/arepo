""" @package ./examples/uniform_static_2d/create.py
Uniform static medium in 2D: the floor test for the residual-distribution solver.

The exact solution is trivial. Every vertex carries the same state, so the
element residual is

    phi^T = sum_{i in T} K_i Uhat_i = ( sum_{i in T} K_i ) Uhat = 0

identically, by the geometric identity sum_i n_i = 0. Every distributed residual
is therefore exactly zero and the state must be preserved to machine precision,
for any mesh, any number of MPI ranks and any number of timesteps.

This simultaneously exercises the geometry, the eigenvalue splitting, the upwind
system solve in its maximally degenerate configuration (u = 0 everywhere, so
S^- = sum_j K_j^- is rank deficient in *every* element), the distribution, the
MPI flux exchange, the DualArea accumulation and the primitive recovery.

Note it does NOT discriminate between the regularised-inverse code and the
direct-solve code: since phi^T = 0, a broken sum_i beta_i = I still yields zero.
Use the "perturbed" mode below for that. This mode is the floor and the
permanent regression guard.

Usage:
    python3 create.py <output_directory> [mode] [CellsPerDimension]

    mode = uniform     uniform state at rest                       (default)
           perturbed   uniform at rest plus a small pressure ripple
"""

import sys
import numpy as np
import h5py

simulation_directory = str(sys.argv[1])
mode = str(sys.argv[2]) if len(sys.argv) > 2 else "uniform"
CellsPerDimension = np.int32(sys.argv[3]) if len(sys.argv) > 3 else np.int32(32)

if mode not in ("uniform", "perturbed"):
    raise SystemExit("mode must be 'uniform' or 'perturbed'")

print("examples/uniform_static_2d/create.py: creating '%s' ICs in %s" % (mode, simulation_directory))

FloatType = np.float64
IntType = np.int32

Boxsize = FloatType(1.0)
gamma = FloatType(5.0 / 3.0)

density_0 = FloatType(1.0)
pressure_0 = FloatType(1.0)
# amplitude of the pressure ripple in 'perturbed' mode, as a fraction of p_0.
# Small enough to stay linear, large enough to sit far above round-off.
delta_p = FloatType(1.0e-3)

# Irregular point distribution: a Cartesian lattice would give a degenerate
# Delaunay triangulation (cocircular points) and an anisotropic set of
# diagonals, neither of which is representative.
rng = np.random.default_rng(0)
choice_per_dimension = IntType(5000)
position_index = rng.choice(choice_per_dimension**2, size=CellsPerDimension**2, replace=False)

NumberOfCells = position_index.shape[0]

Pos = np.zeros([NumberOfCells, 3], dtype=FloatType)
Pos[:, 0] = (position_index % choice_per_dimension + 0.5) * Boxsize / FloatType(choice_per_dimension)
Pos[:, 1] = (position_index // choice_per_dimension + 0.5) * Boxsize / FloatType(choice_per_dimension)

Density = np.full(NumberOfCells, density_0, dtype=FloatType)
Pressure = np.full(NumberOfCells, pressure_0, dtype=FloatType)
Vel = np.zeros([NumberOfCells, 3], dtype=FloatType)

if mode == "perturbed":
    # A smooth, periodic, purely isobaric-gradient perturbation. The velocity
    # stays exactly zero, so every element remains at the stagnation point where
    # S^- is rank deficient, but phi^T is now non-zero and driven by grad p.
    # This is precisely the configuration in which a broken sum_i beta_i = I
    # discards a real residual component.
    k = 2.0 * np.pi / Boxsize
    Pressure = pressure_0 * (1.0 + delta_p * np.sin(k * Pos[:, 0]) * np.cos(k * Pos[:, 1]))

Uthermal = Pressure / (gamma - 1.0) / Density

IC = h5py.File(simulation_directory + "/IC.hdf5", "w")

header = IC.create_group("Header")
part0 = IC.create_group("PartType0")

NumPart = np.array([NumberOfCells, 0, 0, 0, 0, 0], dtype=IntType)
header.attrs.create("NumPart_ThisFile", NumPart)
header.attrs.create("NumPart_Total", NumPart)
header.attrs.create("NumPart_Total_HighWord", np.zeros(6, dtype=IntType))
header.attrs.create("MassTable", np.zeros(6, dtype=IntType))
header.attrs.create("Time", 0.0)
header.attrs.create("Redshift", 0.0)
header.attrs.create("BoxSize", Boxsize)
header.attrs.create("NumFilesPerSnapshot", 1)
header.attrs.create("Omega0", 0.0)
header.attrs.create("OmegaB", 0.0)
header.attrs.create("OmegaLambda", 0.0)
header.attrs.create("HubbleParam", 1.0)
header.attrs.create("Flag_Sfr", 0)
header.attrs.create("Flag_Cooling", 0)
header.attrs.create("Flag_StellarAge", 0)
header.attrs.create("Flag_Metals", 0)
header.attrs.create("Flag_Feedback", 0)
header.attrs.create("Flag_DoublePrecision", 1)

# Masses is read as density because the RD configs set
# READ_MASS_AS_DENSITY_IN_INPUT; init.c then multiplies by DualArea.
part0.create_dataset("ParticleIDs", data=np.arange(1, NumberOfCells + 1))
part0.create_dataset("Coordinates", data=Pos)
part0.create_dataset("Masses", data=Density)
part0.create_dataset("Velocities", data=Vel)
part0.create_dataset("InternalEnergy", data=Uthermal)

IC.close()

print("  cells = %d, boxsize = %g, mode = %s" % (NumberOfCells, Boxsize, mode))
