#!/bin/bash            # this line only there to enable syntax highlighting in this file

## examples/shocktube_2d/Config_SOD_N_RK2.sh
## 2-D periodic Sod shock tube: the first non-smooth test of the RD solver.
## The mesh is static, so the regularisation options of the Yee config are dropped.

#--------------------------------------- Basic operation mode of code
TWODIMS                                  # 2d simulation
GAMMA=1.4                                # Adiabatic index of gas; 5/3 if not set
READ_MASS_AS_DENSITY_IN_INPUT            # Reads the mass field in the IC as density

#--------------------------------------- Mesh motion and regularization
VORONOI_STATIC_MESH

#--------------------------------------- Residual Distribution hydrodynamics solver
RESIDUAL_DISTRIBUTION
N_SCHEME
RD_DEBUG_ASSERTS                         # invariant assertions + solver statistics (validation runs)
RD_RK2_TOTAL_RESIDUAL                    # two-stage GL+F1 total-residual RK2

#--------------------------------------- Time integration options
TREE_BASED_TIMESTEPS                     # non-local timestep criterion (take 'signal speed' into account)
FORCE_EQUAL_TIMESTEPS                    # temporary validated RD baseline

#---------------------------------------- Single/Double Precision
DOUBLEPRECISION=1                        # Mode of double precision: not defined: single; 1: full double precision 2: mixed, 3: mixed, fewer single precisions; unless short of memory, use 1.
INPUT_IN_DOUBLEPRECISION                 # initial conditions are in double precision
OUTPUT_IN_DOUBLEPRECISION                # snapshot files will be written in double precision
OUTPUT_CENTER_OF_MASS                    # output centers of cells

#--------------------------------------- Output/Input options
HAVE_HDF5                                # needed when HDF5 I/O support is desired (recommended)

#--------------------------------------- Testing and Debugging options
DEBUG                                    # enables core-dumps



