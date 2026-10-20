#!/usr/bin/env bash
#SBATCH --job-name=RD3DBlob
#SBATCH --partition=dine2
#SBATCH --account=do020
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=00:30:00

# Submit from the repository root. ACTION is build, gates, calibration or full.
# sbatch --output=CAMPAIGN/slurm-%j.log tests/rd/blob_cosma.sbatch ACTION CAMPAIGN
set -euo pipefail
REPO_ROOT="${AREPO_REPO_ROOT:-${SLURM_SUBMIT_DIR:?submit from the repository root}}"
cd "${REPO_ROOT}"
source ./cosma_env.sh
module load python/3.12.4
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export OMPI_MCA_btl_vader_single_copy_mechanism=none
ACTION="${1:?build, gates, calibration or full}"
CAMPAIGN="${2:?absolute campaign directory}"
DRIVER="${CAMPAIGN}/source/tests/rd/run_3d_blob_cosma.py"
if [[ "${ACTION}" = build ]]; then
    python3 "${DRIVER}" build "${CAMPAIGN}" --jobs "${SLURM_NTASKS}"
else
    python3 "${DRIVER}" run "${CAMPAIGN}" --group "${ACTION}" "${@:3}"
    python3 "${DRIVER}" analyse "${CAMPAIGN}" --group "${ACTION}" "${@:3}"
fi
