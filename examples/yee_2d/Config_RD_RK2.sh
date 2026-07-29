#!/bin/bash
# Yee vortex, LDA residual distribution with the GL+F1 total-residual RK2
# time integration. Companion to Config_RD.sh, which uses the mass-lumped
# baseline; the pair is the controlled comparison for convergence order.

TWODIMS
GAMMA=1.4
READ_MASS_AS_DENSITY_IN_INPUT
VORONOI_STATIC_MESH

RESIDUAL_DISTRIBUTION
LDA_SCHEME
RD_DEBUG_ASSERTS
RD_RK2_TOTAL_RESIDUAL                    # GL+F1 total-residual RK2

TREE_BASED_TIMESTEPS
FORCE_EQUAL_TIMESTEPS

DOUBLEPRECISION=1
INPUT_IN_DOUBLEPRECISION
OUTPUT_IN_DOUBLEPRECISION
OUTPUT_CENTER_OF_MASS

HAVE_HDF5
DEBUG
