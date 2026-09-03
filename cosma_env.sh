#!/usr/bin/env bash

# Pinned COSMA build/run environment for AREPO-RD.
#
# Usage from an interactive shell:
#   source ./cosma_env.sh
#
# Batch launchers source this file themselves. Executing it as a subprocess
# can perform the checks, but cannot modify the caller's environment.

if ! command -v module >/dev/null 2>&1; then
  echo "COSMA environment modules are unavailable in this shell." >&2
  return 1 2>/dev/null || exit 1
fi

module purge
module load cosma/2024
module load gnu_comp/14.1.0
module load openmpi/5.0.3
module load parallel_hdf5/1.14.4
module load gsl/2.8
module load fftw/3.3.10
module load hwloc/2.11.1

# The oneAPI MKL module requires both compiler-rt and TBB even though AREPO is
# compiled with GCC and uses only MKL's LAPACKE/runtime interface.
module load oneAPI/2024.2.0
module load compiler-rt/2024.2.0
module load tbb/2021.13
module load mkl/2024.2

# Prevent one MPI rank from spawning a full pool of BLAS/OpenMP threads.
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"

if [[ ! -x "$(command -v mpicc)" ]]; then
  echo "mpicc is unavailable after loading the COSMA modules." >&2
  return 1 2>/dev/null || exit 1
fi
if [[ -z "${HDF5_HOME:-}" || ! -f "${HDF5_HOME}/include/hdf5.h" ]]; then
  echo "parallel HDF5 headers are unavailable after loading the COSMA modules." >&2
  return 1 2>/dev/null || exit 1
fi
if [[ -z "${MKLROOT:-}" || ! -f "${MKLROOT}/include/mkl_lapacke.h" ||
      ! -f "${MKLROOT}/lib/libmkl_rt.so" ]]; then
  echo "MKL LAPACKE headers/runtime are unavailable after loading the COSMA modules." >&2
  return 1 2>/dev/null || exit 1
fi

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "COSMA dependencies verified. Source this script to retain the environment:"
  echo "  source ./cosma_env.sh"
else
  echo "Loaded AREPO-RD COSMA environment:"
  module -t list 2>&1
fi
