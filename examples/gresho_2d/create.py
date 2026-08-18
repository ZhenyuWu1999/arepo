#!/usr/bin/env python3

""" @package ./examples/Gresho_2d/create.py
Code that creates 2d Gresho vortex initial conditions

created by Rainer Weinberger, last modified 20.03.2020 -- comments welcome
modified by Zhenyu Wu
"""

import argparse
import os
import re
from math import floor

import h5py
import numpy as np
from numpy.random import default_rng

FloatType = np.float64  # double precision: np.float64, for single use np.float32
IntType = np.int32

Boxsize = FloatType(1.0)

def format_velocity_label(value):
    """Return the filename label historically used by this example."""

    if value == 0.0:
        return "v0"
    text = f"{value:g}".replace("e-0", "e-").replace("e+0", "e+")
    return f"v{text}"


parser = argparse.ArgumentParser(
    description="Generate one deterministic two-dimensional Gresho initial condition."
)
parser.add_argument("--mesh", choices=("ring", "random", "glass"), default="ring")
parser.add_argument("--resolution", type=int, default=48,
                    help="nominal cells per dimension for ring/random meshes")
parser.add_argument("--bulk-velocity", type=float, default=1.0e-8)
parser.add_argument("--velocity-label",
                    help="override the filename velocity label, e.g. v1e-8")
parser.add_argument("--glass-file",
                    help="input SWIFT glass; alternatively set GRESHO_GLASS_FILE")
parser.add_argument("--output-dir", default=os.path.dirname(os.path.abspath(__file__)),
                    help="destination directory (default: this example directory)")
parser.add_argument("--force", action="store_true",
                    help="overwrite an existing HDF5 initial condition")
parser.add_argument("--no-plot", action="store_true",
                    help="do not write the point-distribution PNG")
args = parser.parse_args()

## parameters
density_0 = 1.0
velocity_0 = args.bulk_velocity
velocity_label = args.velocity_label or format_velocity_label(velocity_0)
gamma = 5.0 / 3.0
gamma_minus_one = gamma - 1.0
mesh_type = args.mesh
CellsPerDimension = IntType(args.resolution)
glass_file = args.glass_file or os.environ.get("GRESHO_GLASS_FILE")
simulation_directory = os.path.abspath(args.output_dir)

if CellsPerDimension <= 0:
    parser.error("--resolution must be positive")
if mesh_type == "glass" and not glass_file:
    parser.error("--mesh glass requires --glass-file or GRESHO_GLASS_FILE")
if not os.path.isdir(simulation_directory):
    parser.error(f"--output-dir is not a directory: {simulation_directory}")


def load_swift_glass(glass_file, target_boxsize):
    with h5py.File(glass_file, "r") as glass:
        Coordinates = np.asarray(glass["/PartType0/Coordinates"][:, :], dtype=FloatType)

        box_attr = glass["/Header"].attrs["BoxSize"]
        box_array = np.atleast_1d(np.asarray(box_attr, dtype=FloatType))
        source_boxsize = box_array[0]

    if Coordinates.ndim != 2 or Coordinates.shape[1] < 2:
        raise ValueError(
            f"Unexpected coordinates shape {Coordinates.shape} in {glass_file}."
        )
    if source_boxsize <= 0:
        raise ValueError(f"Invalid BoxSize={source_boxsize} in {glass_file}.")

    xPosFromCenter = np.mod(Coordinates[:,0] / source_boxsize, 1.0) * target_boxsize
    yPosFromCenter = np.mod(Coordinates[:,1] / source_boxsize, 1.0) * target_boxsize
    xPosFromCenter -= 0.5 * target_boxsize
    yPosFromCenter -= 0.5 * target_boxsize
    Radius = np.sqrt(xPosFromCenter**2 + yPosFromCenter**2)
    return Radius, xPosFromCenter, yPosFromCenter


def plot_point_distribution(Pos, boxsize, filepath):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(Pos[:,0], Pos[:,1], s=4, c="k", linewidths=0)
    ax.set_xlim(0.0, boxsize)
    ax.set_ylim(0.0, boxsize)
    ax.set_aspect("equal")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(f"Gresho 2D point distribution ({mesh_type})")
    fig.tight_layout()
    fig.savefig(filepath, dpi=200)
    plt.close(fig)


if mesh_type == "glass":
    glass_label = os.path.splitext(os.path.basename(glass_file))[0]
    glass_resolution = re.search(r"(\d+)$", glass_label)
    if glass_resolution:
        filename = f"IC_gresho_{velocity_label}_{mesh_type}{glass_resolution.group(1)}.hdf5"
    else:
        filename = f"IC_gresho_{velocity_label}_{mesh_type}.hdf5"
else:
    filename = f"IC_gresho_{velocity_label}_{mesh_type}{int(CellsPerDimension)}.hdf5"

FilePath = os.path.join(simulation_directory, filename)
PlotFilePath = os.path.splitext(FilePath)[0] + ".png"

if os.path.exists(FilePath) and not args.force:
    raise SystemExit(
        f"{FilePath} already exists; use --force to replace it"
    )

print("examples/Gresho_2d/create.py: creating ICs in directory " + simulation_directory)
print("examples/Gresho_2d/create.py: writing " + FilePath)
if not args.no_plot:
    print("examples/Gresho_2d/create.py: writing " + PlotFilePath)

if mesh_type == "glass":
    print("examples/Gresho_2d/create.py: reading SWIFT glass " + glass_file)

np.random.seed(0)

""" set up grid: equidistant polar 2d grid; similar to Pakmor et al (2016) """
d_ring = Boxsize / CellsPerDimension
## place central cell
Radius = [0.0]
xPosFromCenter = [0.0]
yPosFromCenter = [0.0]

if mesh_type == "ring":
    i_ring = 0
    while d_ring * FloatType(i_ring) <= 0.71 * Boxsize:
        i_ring += 1
        ## place i_ring cells at this distance
        phi = np.random.uniform(0, 2.0 * np.pi)  ## random starting angle
        for i_cell in np.arange(IntType(2.0 * np.pi * i_ring)):
            radius_this_cell = d_ring * FloatType(i_ring)
            xcoord = radius_this_cell * np.cos(phi)
            ycoord = radius_this_cell * np.sin(phi)

            ## only include the cell if coordinates are within the box
            if (
                xcoord >= -0.5 * Boxsize
                and xcoord < 0.5 * Boxsize
                and ycoord >= -0.5 * Boxsize
                and ycoord < 0.5 * Boxsize
            ):
                Radius.append(radius_this_cell)
                xPosFromCenter.append(xcoord)
                yPosFromCenter.append(ycoord)

            phi += (2.0 * np.pi * i_ring) / IntType(2.0 * np.pi * i_ring) / FloatType(
                i_ring
            )
elif mesh_type == "random":
    rng = default_rng(0)
    choice_per_dimension = int(5000)
    position_index = rng.choice(
        choice_per_dimension**2, size=CellsPerDimension**2, replace=False
    )

    for i in range(CellsPerDimension**2):
        xcoord = (position_index[i] % choice_per_dimension) / float(
            choice_per_dimension
        ) * Boxsize
        ycoord = floor(position_index[i] / choice_per_dimension) / float(
            choice_per_dimension
        ) * Boxsize
        xcoord -= 0.5 * Boxsize
        ycoord -= 0.5 * Boxsize
        radius_this_cell = np.sqrt(xcoord**2 + ycoord**2) * Boxsize

        Radius.append(radius_this_cell)
        xPosFromCenter.append(xcoord)
        yPosFromCenter.append(ycoord)
elif mesh_type == "glass":
    Radius, xPosFromCenter, yPosFromCenter = load_swift_glass(glass_file, Boxsize)
else:
    raise ValueError(f"Unknown mesh_type={mesh_type}")

## convert to numpy arrays now that number of cells is known
Radius = np.array(Radius, dtype=FloatType)
xPosFromCenter = np.array(xPosFromCenter, dtype=FloatType)
yPosFromCenter = np.array(yPosFromCenter, dtype=FloatType)
NumberOfCells = Radius.shape[0]
## set up structure for positions (in code coordinates, i.e. from 0 to Boxsize)
Pos = np.zeros([NumberOfCells, 3], dtype=FloatType)
Pos[:, 0] = xPosFromCenter + 0.5 * Boxsize
Pos[:, 1] = yPosFromCenter + 0.5 * Boxsize

""" set up hydrodynamical quantitites """
## mass insetad of density
Density = np.full(NumberOfCells, density_0, dtype=FloatType)
## different zones
i1, = np.where(Radius < 0.2)
i2, = np.where((Radius >= 0.2) & (Radius < 0.4))
i3, = np.where(Radius >= 0.4)

## velocity
RotationVelocity = np.zeros(NumberOfCells, dtype=FloatType)
RotationVelocity[i1] = 5.0 * Radius[i1]
RotationVelocity[i2] = 2.0 - 5.0 * Radius[i2]
RotationVelocity[i3] = 0.0
Vel = np.zeros([NumberOfCells, 3], dtype=FloatType)
i_all_but_central, = np.where(Radius > 0.0)
Vel[i_all_but_central,0] = -RotationVelocity[i_all_but_central] * yPosFromCenter[i_all_but_central] / Radius[i_all_but_central]
Vel[i_all_but_central,1] =  RotationVelocity[i_all_but_central] * xPosFromCenter[i_all_but_central] / Radius[i_all_but_central]
Vel[:, 0] += velocity_0

## specific internal energy
Pressure = np.zeros(NumberOfCells, dtype=FloatType)
Pressure[i1] = 5.0 + 12.5 * Radius[i1] * Radius[i1]
Pressure[i2] = (
    9.0
    + 12.5 * Radius[i2] * Radius[i2]
    - 20.0 * Radius[i2]
    + 4.0 * np.log(Radius[i2] / 0.2)
)
Pressure[i3] = 3.0 + 4.0 * np.log(2.0)
Uthermal = Pressure / density_0 / gamma_minus_one

""" write *.hdf5 file; minimum number of fields required by Arepo """
IC = h5py.File(FilePath, "w")

## create hdf5 groups
header = IC.create_group("Header")
part0 = IC.create_group("PartType0")

## header entries
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
if Pos.dtype == np.float64:
    header.attrs.create("Flag_DoublePrecision", 1)
else:
    header.attrs.create("Flag_DoublePrecision", 0)

## copy datasets
part0.create_dataset("ParticleIDs", data=np.arange(1, NumberOfCells + 1))
part0.create_dataset("Coordinates", data=Pos)
part0.create_dataset("Masses", data=Density)
part0.create_dataset("Velocities", data=Vel)
part0.create_dataset("InternalEnergy", data=Uthermal)

## close file
IC.close()

if not args.no_plot:
    plot_point_distribution(Pos, Boxsize, PlotFilePath)
