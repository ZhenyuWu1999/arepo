#!/usr/bin/env bash
#SBATCH --job-name=ArepoBuild
#SBATCH --partition=dine2
#SBATCH --account=do020
#SBATCH --time=00:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G

# COSMA compute-node wrapper for the immutable AREPO build workflow.
# Usage:
#   sbatch build_case_cosma.sbatch --config CONFIG --name NAME

set -euo pipefail

REPO_ROOT="${AREPO_REPO_ROOT:-${SLURM_SUBMIT_DIR:?submit this job from the AREPO repository}}"
cd "${REPO_ROOT}"
source ./cosma_env.sh

echo "Host       : $(hostname)"
echo "Job ID     : ${SLURM_JOB_ID:-none}"
echo "Build args : $*"
echo "MKLROOT    : ${MKLROOT}"
echo "HDF5_HOME  : ${HDF5_HOME}"
echo

exec ./build_case.sh "$@" --jobs "${SLURM_CPUS_PER_TASK:-8}"
