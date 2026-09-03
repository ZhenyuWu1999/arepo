#!/usr/bin/env bash
#SBATCH --job-name=ArepoHydro
#SBATCH --partition=dine2
#SBATCH --account=do020
#SBATCH --time=00:20:00
#SBATCH --ntasks=2
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G

# COSMA compute-node wrapper for a managed immutable AREPO artifact.
# Usage:
#   sbatch --ntasks=N run_case_cosma.sbatch --binary BINARY --param PARAM

set -euo pipefail

REPO_ROOT="${AREPO_REPO_ROOT:-${SLURM_SUBMIT_DIR:?submit this job from the AREPO repository}}"
cd "${REPO_ROOT}"
source ./cosma_env.sh

exec ./run_case.sh "$@" --tasks "${SLURM_NTASKS:-1}"
