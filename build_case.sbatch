#!/usr/bin/env bash
#SBATCH --job-name=ArepoBuild
#SBATCH --time=00:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G

# Build AREPO on a compute node, where Intel oneAPI/MKL is available.
#
# Usage:
#   sbatch build_case.sbatch --config examples/yee_2d/Config_RD.sh \
#       --name yee-lda-lumped --require-clean
#
# All arguments are forwarded to build_case.sh. The shell wrapper provides the
# repository-wide build lock, isolated temporary BUILD_DIR, immutable artifact,
# checksum, and provenance manifest.

set -euo pipefail

REPO_ROOT="/home/zwu/arepo_rd/arepo"
cd "${REPO_ROOT}"

if command -v module >/dev/null 2>&1; then
  module load openmpi
  module load hdf5-openmpi
  module load mkl/latest
fi

echo "Host       : $(hostname)"
echo "Job ID     : ${SLURM_JOB_ID:-none}"
echo "Build args : $*"
echo "MKLROOT    : ${MKLROOT:-<unset>}"
echo

exec ./build_case.sh "$@" --jobs "${SLURM_CPUS_PER_TASK:-8}"
