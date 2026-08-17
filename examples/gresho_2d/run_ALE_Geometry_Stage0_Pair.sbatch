#!/bin/bash
#SBATCH --job-name=ale-geom-pair
#SBATCH --time=00:10:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G
#SBATCH --output=ale-geometry-pair-%j.log

set -euo pipefail

module load openmpi
module load hdf5-openmpi

cd /home/zwu/arepo_rd/arepo

mkdir -p output_ALE_geometry_stage0_on_long
mkdir -p output_ALE_geometry_stage0_off_long

make -j "${SLURM_CPUS_PER_TASK}" \
  CONFIG=examples/gresho_2d/Config_ALE_Geometry_Stage0.sh \
  BUILD_DIR=build_ale_stage0 \
  EXEC=Arepo_ALE_Geometry_Stage0

mpirun -np 1 ./Arepo_ALE_Geometry_Stage0 examples/gresho_2d/param_ALE_Geometry_Stage0_On_Long.txt

make -j "${SLURM_CPUS_PER_TASK}" \
  CONFIG=examples/gresho_2d/Config_ALE_Geometry_Stage0_NoReg.sh \
  BUILD_DIR=build_ale_stage0_noreg \
  EXEC=Arepo_ALE_Geometry_Stage0_NoReg

mpirun -np 1 ./Arepo_ALE_Geometry_Stage0_NoReg examples/gresho_2d/param_ALE_Geometry_Stage0_Off_Long.txt
