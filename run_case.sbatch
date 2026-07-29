#!/usr/bin/env bash
#SBATCH --job-name=ArepoHydro
#SBATCH --time=00:20:00
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G

# Run an explicitly selected immutable build artifact.
#
# Usage:
#   sbatch --ntasks=N run_case.sbatch \
#       --binary build_artifacts/yee-lda-lumped/<artifact-id>/Arepo \
#       --param /absolute/or/repository/relative/param.txt
#
# run_case.sh verifies the binary checksum, resolves relative IC/OutputDir paths
# from the parameter-file directory, and records build and run provenance.

set -euo pipefail

REPO_ROOT="/home/zwu/arepo_rd/arepo"
cd "${REPO_ROOT}"

exec ./run_case.sh "$@" --tasks "${SLURM_NTASKS:-1}"
