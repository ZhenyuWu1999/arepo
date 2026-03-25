#!/usr/bin/env bash

set -euo pipefail

# Before running, rebuild ./Arepo with the matching Config via
#   ./build_case.sh --config <path-to-config>
# Then update PARAM_FILE below to the case you want to run.

REPO_ROOT="/home/zwu/arepo_rd/arepo"
BINARY="${REPO_ROOT}/Arepo"
PARAM_FILE="${REPO_ROOT}/examples/gresho_2d/param_RD.txt"
MPI_TASKS="${MPI_TASKS:-2}"

param_value() {
  local param_file="${1}"
  local key="${2}"

  python3 - "${param_file}" "${key}" <<'PY'
import pathlib
import sys

param_path = pathlib.Path(sys.argv[1])
key = sys.argv[2]

for line in param_path.read_text().splitlines():
    stripped = line.strip()
    if not stripped or stripped.startswith("%"):
        continue
    parts = stripped.split()
    if parts and parts[0] == key and len(parts) > 1:
        print(parts[1])
        break
PY
}

if command -v module >/dev/null 2>&1; then
  module load openmpi || true
  module load hdf5-openmpi || true
fi

if [[ ! -x "${BINARY}" ]]; then
  echo "AREPO binary not found: ${BINARY}" >&2
  echo "Build it first with ./build_case.sh --config <path-to-config>" >&2
  exit 1
fi

if [[ ! -f "${PARAM_FILE}" ]]; then
  echo "Parameter file not found: ${PARAM_FILE}" >&2
  exit 2
fi

OUTPUT_DIR="$(param_value "${PARAM_FILE}" "OutputDir")"
if [[ -z "${OUTPUT_DIR}" ]]; then
  echo "Could not read OutputDir from parameter file: ${PARAM_FILE}" >&2
  exit 3
fi

mkdir -p "${OUTPUT_DIR}"

RUN_TAG="login.$(date +%Y%m%d_%H%M%S)"
RUN_LOG="${OUTPUT_DIR}/run-${RUN_TAG}.log"
AREPO_LOG="${OUTPUT_DIR}/arepo-${RUN_TAG}.log"

exec > >(tee "${RUN_LOG}") 2>&1

git -C "${REPO_ROOT}" rev-parse HEAD > "${OUTPUT_DIR}/git_commit.txt"
git -C "${REPO_ROOT}" status --short > "${OUTPUT_DIR}/git_status.txt"
cp "${PARAM_FILE}" "${OUTPUT_DIR}/param.used"
if [[ -f "${REPO_ROOT}/Config.current.build" ]]; then
  cp "${REPO_ROOT}/Config.current.build" "${OUTPUT_DIR}/Config.used"
fi
if [[ -f "${REPO_ROOT}/build/arepoconfig.h" ]]; then
  cp "${REPO_ROOT}/build/arepoconfig.h" "${OUTPUT_DIR}/arepoconfig.h.used"
fi

echo "Host          : $(hostname)"
echo "Binary        : ${BINARY}"
echo "Parameter     : ${PARAM_FILE}"
echo "Output dir    : ${OUTPUT_DIR}"
echo "Run log       : ${RUN_LOG}"
echo "AREPO log     : ${AREPO_LOG}"
echo "MPI tasks     : ${MPI_TASKS}"
echo

cd "${OUTPUT_DIR}"
mpirun -np "${MPI_TASKS}" "${BINARY}" "${PARAM_FILE}" > "${AREPO_LOG}" 2>&1

echo "Run completed."
