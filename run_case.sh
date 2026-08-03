#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}"

resolve_repo_path() {
  local path_input="${1:-}"

  if [[ -z "${path_input}" ]]; then
    return 1
  fi

  if [[ "${path_input}" = /* ]]; then
    printf '%s\n' "${path_input}"
  else
    printf '%s\n' "${REPO_ROOT}/${path_input}"
  fi
}

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

usage() {
  cat <<'EOF'
Usage:
  ./run_case.sh --binary PATH --param PATH [options]

Run an explicitly selected immutable AREPO build artifact and copy its build
provenance into the simulation output. Relative IC and OutputDir values are
resolved by running AREPO from the selected working directory.

Options:
  --binary PATH             Artifact binary produced by build_case.sh (required)
  --param PATH              Runtime parameter file (required)
  --tasks N                 MPI ranks (default: MPI_TASKS or 2)
  --work-dir PATH           Runtime working directory (default: parameter directory)
  --allow-unmanaged-binary  Permit a binary without an artifact manifest
  -h, --help                Show this help
EOF
}

BINARY=""
PARAM_FILE=""
WORK_DIR=""
MPI_TASKS="${MPI_TASKS:-2}"
ALLOW_UNMANAGED_BINARY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --binary)
      BINARY="${2}"
      shift 2
      ;;
    --param)
      PARAM_FILE="${2}"
      shift 2
      ;;
    --tasks)
      MPI_TASKS="${2}"
      shift 2
      ;;
    --work-dir)
      WORK_DIR="${2}"
      shift 2
      ;;
    --allow-unmanaged-binary)
      ALLOW_UNMANAGED_BINARY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${BINARY}" || -z "${PARAM_FILE}" ]]; then
  usage >&2
  exit 2
fi
if ! [[ "${MPI_TASKS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "--tasks must be a positive integer: ${MPI_TASKS}" >&2
  exit 2
fi

BINARY="$(resolve_repo_path "${BINARY}")"
PARAM_FILE="$(resolve_repo_path "${PARAM_FILE}")"

if [[ ! -x "${BINARY}" ]]; then
  echo "AREPO binary not found or not executable: ${BINARY}" >&2
  exit 3
fi
if [[ ! -f "${PARAM_FILE}" ]]; then
  echo "Parameter file not found: ${PARAM_FILE}" >&2
  exit 4
fi

if [[ -z "${WORK_DIR}" ]]; then
  WORK_DIR="$(dirname "${PARAM_FILE}")"
else
  WORK_DIR="$(resolve_repo_path "${WORK_DIR}")"
fi
if [[ ! -d "${WORK_DIR}" ]]; then
  echo "Working directory not found: ${WORK_DIR}" >&2
  exit 5
fi

BINARY="$(readlink -f "${BINARY}")"
PARAM_FILE="$(readlink -f "${PARAM_FILE}")"
WORK_DIR="$(readlink -f "${WORK_DIR}")"

ARTIFACT_DIR="$(dirname "${BINARY}")"
if [[ -f "${ARTIFACT_DIR}/manifest.txt" && -f "${ARTIFACT_DIR}/binary.sha256" ]]; then
  (
    cd "${ARTIFACT_DIR}"
    sha256sum --quiet -c binary.sha256
  ) || {
    echo "Artifact binary checksum verification failed: ${BINARY}" >&2
    exit 6
  }
  MANAGED_ARTIFACT=1
  LAPACK_BACKEND_USED="$(sed -n 's/^lapack_backend=//p' "${ARTIFACT_DIR}/manifest.txt")"
elif [[ "${ALLOW_UNMANAGED_BINARY}" -eq 1 ]]; then
  MANAGED_ARTIFACT=0
  LAPACK_BACKEND_USED="unknown"
  echo "WARNING: running an unmanaged binary without build provenance." >&2
else
  echo "Binary is not a managed build artifact: ${BINARY}" >&2
  echo "Use build_case.sh, or pass --allow-unmanaged-binary for a diagnostic run." >&2
  exit 6
fi

OUTPUT_VALUE="$(param_value "${PARAM_FILE}" "OutputDir")"
if [[ -z "${OUTPUT_VALUE}" ]]; then
  echo "Could not read OutputDir from parameter file: ${PARAM_FILE}" >&2
  exit 7
fi
if [[ "${OUTPUT_VALUE}" = /* ]]; then
  OUTPUT_DIR="${OUTPUT_VALUE}"
else
  OUTPUT_DIR="${WORK_DIR}/${OUTPUT_VALUE}"
fi
OUTPUT_DIR="$(readlink -m "${OUTPUT_DIR}")"
mkdir -p "${OUTPUT_DIR}"

if command -v module >/dev/null 2>&1; then
  module load openmpi >/dev/null 2>&1 || true
  module load hdf5-openmpi >/dev/null 2>&1 || true
  if [[ "${LAPACK_BACKEND_USED}" = "mkl" || "${MANAGED_ARTIFACT}" -eq 0 ]]; then
    module load mkl/latest >/dev/null 2>&1 || true
  fi
fi

# This cluster disallows process_vm_readv for OpenMPI's vader CMA path.  Force
# the portable two-copy path, as the campaign wrapper already does, so direct
# managed-artifact runs work reliably with more than one local MPI rank.
export OMPI_MCA_btl_vader_single_copy_mechanism=none

RUN_TAG="$(date -u '+%Y%m%dT%H%M%SZ').$$"
RUN_LOG="${OUTPUT_DIR}/run-${RUN_TAG}.log"
AREPO_LOG="${OUTPUT_DIR}/arepo-${RUN_TAG}.log"
PROVENANCE_DIR="${OUTPUT_DIR}/provenance-${RUN_TAG}"
mkdir -p "${PROVENANCE_DIR}"

BINARY_SHA256="$(sha256sum "${BINARY}" | awk '{print $1}')"
PARAM_SHA256="$(sha256sum "${PARAM_FILE}" | awk '{print $1}')"

cp "${PARAM_FILE}" "${PROVENANCE_DIR}/param.used"
if [[ "${MANAGED_ARTIFACT}" -eq 1 ]]; then
  cp "${ARTIFACT_DIR}/manifest.txt" "${PROVENANCE_DIR}/build_manifest.used"
  cp "${ARTIFACT_DIR}/binary.sha256" "${PROVENANCE_DIR}/binary.sha256"
  cp "${ARTIFACT_DIR}/Config.used" "${PROVENANCE_DIR}/Config.used"
  cp "${ARTIFACT_DIR}/arepoconfig.h.used" "${PROVENANCE_DIR}/arepoconfig.h.used"
  if [[ -f "${ARTIFACT_DIR}/source_status.txt" ]]; then
    cp "${ARTIFACT_DIR}/source_status.txt" "${PROVENANCE_DIR}/source_status.txt"
  fi
  if [[ -f "${ARTIFACT_DIR}/source.patch" ]]; then
    cp "${ARTIFACT_DIR}/source.patch" "${PROVENANCE_DIR}/source.patch"
  fi
fi

git -C "${REPO_ROOT}" rev-parse HEAD > "${PROVENANCE_DIR}/runner_git_commit.txt"
git -C "${REPO_ROOT}" status --short > "${PROVENANCE_DIR}/runner_git_status.txt"
ldd "${BINARY}" > "${PROVENANCE_DIR}/binary.ldd.txt" 2>&1 || true

{
  printf 'run_timestamp_utc=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  printf 'host=%s\n' "$(hostname)"
  printf 'binary=%s\n' "${BINARY}"
  printf 'binary_sha256=%s\n' "${BINARY_SHA256}"
  printf 'managed_artifact=%s\n' "${MANAGED_ARTIFACT}"
  printf 'lapack_backend=%s\n' "${LAPACK_BACKEND_USED}"
  printf 'parameter_file=%s\n' "${PARAM_FILE}"
  printf 'parameter_sha256=%s\n' "${PARAM_SHA256}"
  printf 'work_dir=%s\n' "${WORK_DIR}"
  printf 'output_dir=%s\n' "${OUTPUT_DIR}"
  printf 'mpi_tasks=%s\n' "${MPI_TASKS}"
} > "${PROVENANCE_DIR}/run_manifest.txt"

exec > >(tee "${RUN_LOG}") 2>&1

echo "Host          : $(hostname)"
echo "Binary        : ${BINARY}"
echo "Binary SHA256 : ${BINARY_SHA256}"
echo "Artifact dir  : ${ARTIFACT_DIR}"
echo "Parameter     : ${PARAM_FILE}"
echo "Working dir   : ${WORK_DIR}"
echo "Output dir    : ${OUTPUT_DIR}"
echo "Provenance    : ${PROVENANCE_DIR}"
echo "Run log       : ${RUN_LOG}"
echo "AREPO log     : ${AREPO_LOG}"
echo "MPI tasks     : ${MPI_TASKS}"
echo

cd "${WORK_DIR}"
set +e
mpirun -np "${MPI_TASKS}" "${BINARY}" "${PARAM_FILE}" > "${AREPO_LOG}" 2>&1
RUN_STATUS=$?
set -e

printf '%s\n' "${RUN_STATUS}" > "${PROVENANCE_DIR}/exit_status.txt"
if [[ "${RUN_STATUS}" -ne 0 ]]; then
  echo "Run failed with exit status ${RUN_STATUS}; see ${AREPO_LOG}" >&2
  exit "${RUN_STATUS}"
fi

echo "Run completed."
