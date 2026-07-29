#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AREPO_REPO_ROOT="${SCRIPT_DIR}"
AREPO_BUILD_JOBS="${AREPO_BUILD_JOBS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)}"

resolve_repo_path() {
  local path_input="${1:-}"

  if [[ -z "${path_input}" ]]; then
    return 1
  fi

  if [[ "${path_input}" = /* ]]; then
    printf '%s\n' "${path_input}"
  else
    printf '%s\n' "${AREPO_REPO_ROOT}/${path_input}"
  fi
}

require_file() {
  local label="${1}"
  local path_input="${2}"
  local resolved

  resolved="$(resolve_repo_path "${path_input}")"
  if [[ ! -f "${resolved}" ]]; then
    echo "${label} not found: ${resolved}" >&2
    return 1
  fi

  printf '%s\n' "${resolved}"
}

ensure_mkl_environment() {
  if [[ -n "${MKLROOT:-}" && -f "${MKLROOT}/include/mkl_lapacke.h" ]]; then
    return 0
  fi

  if command -v module >/dev/null 2>&1; then
    module load openmpi || true
    module load hdf5-openmpi || true
    module load mkl/latest || true
  fi

  if [[ -n "${MKLROOT:-}" && -f "${MKLROOT}/include/mkl_lapacke.h" ]]; then
    return 0
  fi

  cat >&2 <<'EOF'
MKL is not available in the current shell, so this build would fall back to the
system LAPACKE library. On this cluster that usually produces a binary that
fails on compute nodes.

Recommended workflow:
  1. Either use `cnode` to enter a compute node, or SSH to an FCFS node
     such as `ssh zwu@fcfs1`.
  2. Run `module load openmpi hdf5-openmpi mkl/latest`
  3. Re-run ./build_case.sh --config ...
EOF
  exit 3
}

usage() {
  cat <<'EOF'
Usage:
  ./build_case.sh --config PATH [options]

Rebuild AREPO from an explicitly chosen Config file.

Options:
  --config PATH   Config file to pass to make
  --jobs N        Parallel make jobs
  --no-clean      Skip make clean before building
  -h, --help      Show this help
EOF
}

CONFIG_PATH=""
MAKE_JOBS="${AREPO_BUILD_JOBS}"
DO_CLEAN=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      CONFIG_PATH="${2}"
      shift 2
      ;;
    --jobs)
      MAKE_JOBS="${2}"
      shift 2
      ;;
    --no-clean)
      DO_CLEAN=0
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

if [[ -z "${CONFIG_PATH}" ]]; then
  usage >&2
  exit 2
fi

CONFIG_PATH="$(require_file "Config file" "${CONFIG_PATH}")"

echo "Repository    : ${AREPO_REPO_ROOT}"
echo "Config        : ${CONFIG_PATH}"
echo "Make jobs     : ${MAKE_JOBS}"
echo

cd "${AREPO_REPO_ROOT}"
ensure_mkl_environment

if [[ "${DO_CLEAN}" -eq 1 ]]; then
  echo "+ make CONFIG=${CONFIG_PATH} clean"
  make CONFIG="${CONFIG_PATH}" clean
  echo
fi

echo "+ make CONFIG=${CONFIG_PATH} -j ${MAKE_JOBS}"
make CONFIG="${CONFIG_PATH}" -j "${MAKE_JOBS}"
echo

cp "${CONFIG_PATH}" "${AREPO_REPO_ROOT}/Config.current.build"

echo "Build completed."
echo "Binary: ${AREPO_REPO_ROOT}/Arepo"
