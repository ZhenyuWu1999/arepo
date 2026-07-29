#!/usr/bin/env bash
#SBATCH --job-name=ArepoBuild
#SBATCH --time=00:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G

# Build AREPO on a compute node, where the Intel oneAPI/MKL module tree exists.
# The login node (cuillin) has /usr/local/oneapi in MODULEPATH but not on disk,
# so a login-node build silently falls back to the system LAPACKE and produces a
# binary that may not run on the compute nodes.
#
# Usage:
#   sbatch build_case.sbatch --config examples/gresho_2d/Config_RD.sh [--exec PATH]
#
# All arguments are forwarded to build_case.sh except --exec, which overrides the
# output binary path (default: the repository's ./Arepo).

set -euo pipefail

REPO_ROOT="/home/zwu/arepo_rd/arepo"
cd "${REPO_ROOT}"

# IMPORTANT: builds must be serialised.
#
# src/main/allvars.h line 44 includes "./../../build/arepoconfig.h" with the
# path hardcoded, so overriding BUILD_DIR does NOT isolate a build: the
# generated header lands in the alternative directory while every compilation
# unit keeps reading the stale ./build/arepoconfig.h. Two builds with different
# Config files therefore cannot run at the same time, and a BUILD_DIR override
# is worse than useless because it produces binaries that silently correspond to
# some other Config while looking correctly isolated.
#
# The lock below makes concurrent submissions queue up instead of corrupting
# each other. Verify a build with:  grep _SCHEME build/arepoconfig.h
exec 9> "${REPO_ROOT}/.build_case.lock"
if ! flock -w 3600 9; then
  echo "timed out waiting for the build lock" >&2
  exit 75
fi
echo "Build lock  : acquired"

EXEC_PATH=""
BUILD_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --exec) EXEC_PATH="$2"; shift 2 ;;
    *) BUILD_ARGS+=("$1"); shift ;;
  esac
done

echo "Host        : $(hostname)"
echo "Job ID      : ${SLURM_JOB_ID:-none}"
echo "Build args  : ${BUILD_ARGS[*]:-<none>}"
echo "Exec path   : ${EXEC_PATH:-${REPO_ROOT}/Arepo}"
echo

if command -v module >/dev/null 2>&1; then
  module load openmpi || true
  module load hdf5-openmpi || true
  module load mkl/latest || true
fi

echo "MKLROOT     : ${MKLROOT:-<unset>}"
if [[ -n "${MKLROOT:-}" && -f "${MKLROOT}/include/mkl_lapacke.h" ]]; then
  echo "MKL headers : found"
else
  echo "MKL headers : NOT FOUND -- the build will fall back to system LAPACKE" >&2
fi
echo

if [[ -n "${EXEC_PATH}" ]]; then
  # build_case.sh does not expose EXEC, so drive make directly in that case.
  CONFIG_PATH=""
  for ((i = 0; i < ${#BUILD_ARGS[@]}; i++)); do
    [[ "${BUILD_ARGS[$i]}" == "--config" ]] && CONFIG_PATH="${BUILD_ARGS[$((i + 1))]}"
  done
  if [[ -z "${CONFIG_PATH}" ]]; then
    echo "--exec requires --config" >&2
    exit 2
  fi

  make CONFIG="${CONFIG_PATH}" EXEC="${EXEC_PATH}" clean
  make CONFIG="${CONFIG_PATH}" EXEC="${EXEC_PATH}" -j "${SLURM_CPUS_PER_TASK:-8}"
  BINARY="${EXEC_PATH}"
else
  ./build_case.sh "${BUILD_ARGS[@]}" --jobs "${SLURM_CPUS_PER_TASK:-8}"
  BINARY="${REPO_ROOT}/Arepo"
fi

echo
echo "=== linkage of ${BINARY} ==="
ldd "${BINARY}" | grep -iE "mkl|lapack|blas" || echo "(no BLAS/LAPACK entries found)"
echo
echo "Build completed: ${BINARY}"
