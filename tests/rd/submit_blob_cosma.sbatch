#!/usr/bin/env bash
#SBATCH --job-name=BlobFullSubmit
#SBATCH --partition=dine2
#SBATCH --account=do020
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:02:00

# Submit with --dependency=afterok:CALIBRATION_JOB_ID.
set -euo pipefail
CAMPAIGN="${1:?absolute campaign directory}"
python3 "${CAMPAIGN}/submit_3d_blob_full_cosma.py" "${CAMPAIGN}"
