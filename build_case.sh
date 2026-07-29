#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AREPO_REPO_ROOT="${SCRIPT_DIR}"
AREPO_BUILD_JOBS="${AREPO_BUILD_JOBS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)}"
AREPO_ARTIFACT_ROOT="${AREPO_ARTIFACT_ROOT:-${AREPO_REPO_ROOT}/build_artifacts}"

TEMP_BUILD_DIR=""
STAGING_DIR=""

cleanup() {
  if [[ -n "${STAGING_DIR}" && -d "${STAGING_DIR}" ]]; then
    rm -rf -- "${STAGING_DIR}"
  fi
  if [[ -n "${TEMP_BUILD_DIR}" && -d "${TEMP_BUILD_DIR}" ]]; then
    rm -rf -- "${TEMP_BUILD_DIR}"
  fi
}
trap cleanup EXIT

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

sanitize_label() {
  local label="${1}"
  local sanitized

  sanitized="$(printf '%s' "${label}" | sed 's/[^A-Za-z0-9._-]/-/g; s/--*/-/g; s/^-//; s/-$//')"
  if [[ -z "${sanitized}" ]]; then
    echo "Build name contains no usable characters: ${label}" >&2
    return 1
  fi
  printf '%s\n' "${sanitized}"
}

sha256_file() {
  sha256sum "${1}" | awk '{print $1}'
}

ensure_linear_algebra_environment() {
  if [[ -n "${MKLROOT:-}" && -f "${MKLROOT}/include/mkl_lapacke.h" ]]; then
    LAPACK_BACKEND="mkl"
    return 0
  fi

  if command -v module >/dev/null 2>&1; then
    module load openmpi >/dev/null 2>&1 || true
    module load hdf5-openmpi >/dev/null 2>&1 || true
    module load mkl/latest >/dev/null 2>&1 || true
  fi

  if [[ -n "${MKLROOT:-}" && -f "${MKLROOT}/include/mkl_lapacke.h" ]]; then
    LAPACK_BACKEND="mkl"
    return 0
  fi

  if [[ "${ALLOW_SYSTEM_LAPACKE}" -eq 1 ]]; then
    LAPACK_BACKEND="system-lapacke"
    cat >&2 <<'EOF'
WARNING: building against system LAPACKE by explicit request. On this cluster
such a binary normally cannot run on compute nodes. The backend is recorded in
the build manifest.
EOF
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

For a local-only diagnostic binary, pass --allow-system-lapacke explicitly.
EOF
  exit 3
}

usage() {
  cat <<'EOF'
Usage:
  ./build_case.sh --config PATH [options]

Build AREPO in an isolated temporary directory, then publish an immutable
binary/configuration bundle under build_artifacts/. Builds are serialised by a
repository-wide flock; published binaries can be run concurrently.

Options:
  --config PATH             Config file to pass to make (required)
  --name NAME               Human-readable build family (default: Config basename)
  --jobs N                  Parallel make jobs
  --artifact-root PATH      Destination root for immutable build bundles
  --require-clean           Refuse tracked source changes relative to HEAD
  --allow-system-lapacke    Permit a local-only non-MKL build
  -h, --help                Show this help
EOF
}

CONFIG_PATH=""
BUILD_NAME=""
MAKE_JOBS="${AREPO_BUILD_JOBS}"
REQUIRE_CLEAN=0
ALLOW_SYSTEM_LAPACKE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      CONFIG_PATH="${2}"
      shift 2
      ;;
    --name)
      BUILD_NAME="${2}"
      shift 2
      ;;
    --jobs)
      MAKE_JOBS="${2}"
      shift 2
      ;;
    --artifact-root)
      AREPO_ARTIFACT_ROOT="$(resolve_repo_path "${2}")"
      shift 2
      ;;
    --require-clean)
      REQUIRE_CLEAN=1
      shift
      ;;
    --allow-system-lapacke)
      ALLOW_SYSTEM_LAPACKE=1
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
if ! [[ "${MAKE_JOBS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "--jobs must be a positive integer: ${MAKE_JOBS}" >&2
  exit 2
fi

CONFIG_PATH="$(require_file "Config file" "${CONFIG_PATH}")"
if [[ -z "${BUILD_NAME}" ]]; then
  BUILD_NAME="$(basename "${CONFIG_PATH}")"
  BUILD_NAME="${BUILD_NAME%.sh}"
fi
BUILD_NAME="$(sanitize_label "${BUILD_NAME}")"

if ! command -v flock >/dev/null 2>&1; then
  echo "flock is required to serialise AREPO builds." >&2
  exit 4
fi

cd "${AREPO_REPO_ROOT}"
exec 9>"${AREPO_REPO_ROOT}/.build_case.lock"
echo "Waiting for repository build lock..."
flock 9
echo "Build lock acquired."

ensure_linear_algebra_environment

TEMP_BUILD_DIR="$(mktemp -d "${AREPO_REPO_ROOT}/.build-case.${BUILD_NAME}.XXXXXX")"
CONFIG_SNAPSHOT="${TEMP_BUILD_DIR}/Config.input"
cp "${CONFIG_PATH}" "${CONFIG_SNAPSHOT}"

GIT_COMMIT="$(git rev-parse HEAD)"
GIT_SHORT="$(git rev-parse --short=12 HEAD)"
CONFIG_SHA256="$(sha256_file "${CONFIG_SNAPSHOT}")"
SYSTYPE_SHA256="$(sha256_file "${AREPO_REPO_ROOT}/Makefile.systype")"

if git diff --quiet HEAD --; then
  SOURCE_STATE="clean"
  SOURCE_DIFF_SHA256="none"
else
  SOURCE_STATE="dirty"
  SOURCE_DIFF_SHA256="$(git diff --binary HEAD -- | sha256sum | awk '{print $1}')"
  if [[ "${REQUIRE_CLEAN}" -eq 1 ]]; then
    echo "Tracked source changes are present; --require-clean refuses this build." >&2
    exit 5
  fi
fi

MPICC_PATH="$(command -v mpicc)"
MPICC_VERSION="$(mpicc --version | sed -n '1p')"
MPICC_SHOW="$(mpicc -show 2>/dev/null || printf 'unavailable')"
TOOLCHAIN_KEY="${MPICC_PATH}|${MPICC_VERSION}|${MPICC_SHOW}|${LAPACK_BACKEND}|${MKLROOT:-unset}|${SYSTYPE_SHA256}"
TOOLCHAIN_SHA256="$(printf '%s' "${TOOLCHAIN_KEY}" | sha256sum | awk '{print $1}')"
FINGERPRINT_INPUT="${GIT_COMMIT}|${SOURCE_DIFF_SHA256}|${CONFIG_SHA256}|${TOOLCHAIN_SHA256}"
BUILD_FINGERPRINT="$(printf '%s' "${FINGERPRINT_INPUT}" | sha256sum | awk '{print $1}')"
ARTIFACT_ID="${GIT_SHORT}-${BUILD_FINGERPRINT:0:16}"
ARTIFACT_PARENT="${AREPO_ARTIFACT_ROOT}/${BUILD_NAME}"
ARTIFACT_DIR="${ARTIFACT_PARENT}/${ARTIFACT_ID}"

if [[ -d "${ARTIFACT_DIR}" ]]; then
  if [[ -x "${ARTIFACT_DIR}/Arepo" &&
        -f "${ARTIFACT_DIR}/binary.sha256" &&
        -f "${ARTIFACT_DIR}/manifest.txt" &&
        -f "${ARTIFACT_DIR}/Config.used" &&
        -f "${ARTIFACT_DIR}/arepoconfig.h.used" &&
        -f "${ARTIFACT_DIR}/binary.ldd.txt" ]] &&
     (cd "${ARTIFACT_DIR}" && sha256sum --quiet -c binary.sha256); then
    echo "Matching immutable build already exists; reusing it."
    echo "Artifact: ${ARTIFACT_DIR}"
    echo "Binary  : ${ARTIFACT_DIR}/Arepo"
    exit 0
  fi

  echo "Artifact directory exists but is incomplete or corrupted: ${ARTIFACT_DIR}" >&2
  echo "It was not overwritten." >&2
  exit 6
fi

mkdir -p "${ARTIFACT_PARENT}"

echo "Repository     : ${AREPO_REPO_ROOT}"
echo "Config         : ${CONFIG_PATH}"
echo "Build name     : ${BUILD_NAME}"
echo "Git commit     : ${GIT_COMMIT}"
echo "Source state   : ${SOURCE_STATE}"
echo "LAPACK backend : ${LAPACK_BACKEND}"
echo "Temporary build: ${TEMP_BUILD_DIR}"
echo "Artifact       : ${ARTIFACT_DIR}"
echo "Make jobs      : ${MAKE_JOBS}"
echo

echo "+ make CONFIG=${CONFIG_SNAPSHOT} BUILD_DIR=${TEMP_BUILD_DIR} EXEC=${TEMP_BUILD_DIR}/Arepo -j ${MAKE_JOBS}"
make CONFIG="${CONFIG_SNAPSHOT}" BUILD_DIR="${TEMP_BUILD_DIR}" EXEC="${TEMP_BUILD_DIR}/Arepo" -j "${MAKE_JOBS}" \
  2>&1 | tee "${TEMP_BUILD_DIR}/build.log"

if [[ ! -x "${TEMP_BUILD_DIR}/Arepo" ]]; then
  echo "Build completed without producing an executable: ${TEMP_BUILD_DIR}/Arepo" >&2
  exit 7
fi

if [[ "$(git rev-parse HEAD)" != "${GIT_COMMIT}" ]]; then
  echo "HEAD changed while the build was running; refusing to publish mixed provenance." >&2
  exit 8
fi
if git diff --quiet HEAD --; then
  POST_BUILD_DIFF_SHA256="none"
else
  POST_BUILD_DIFF_SHA256="$(git diff --binary HEAD -- | sha256sum | awk '{print $1}')"
fi
if [[ "${POST_BUILD_DIFF_SHA256}" != "${SOURCE_DIFF_SHA256}" ]]; then
  echo "Tracked source changed while the build was running; refusing to publish mixed provenance." >&2
  exit 8
fi

STAGING_DIR="$(mktemp -d "${ARTIFACT_PARENT}/.${ARTIFACT_ID}.staging.XXXXXX")"
cp "${TEMP_BUILD_DIR}/Arepo" "${STAGING_DIR}/Arepo"
cp "${CONFIG_SNAPSHOT}" "${STAGING_DIR}/Config.used"
cp "${TEMP_BUILD_DIR}/arepoconfig.h" "${STAGING_DIR}/arepoconfig.h.used"
cp "${TEMP_BUILD_DIR}/build.log" "${STAGING_DIR}/build.log"
ldd "${STAGING_DIR}/Arepo" > "${STAGING_DIR}/binary.ldd.txt"

if grep -q "not found" "${STAGING_DIR}/binary.ldd.txt"; then
  echo "Built binary has unresolved shared-library dependencies; refusing to publish." >&2
  grep "not found" "${STAGING_DIR}/binary.ldd.txt" >&2
  exit 9
fi
if [[ "${LAPACK_BACKEND}" = "mkl" ]] && ! grep -q "libmkl_rt" "${STAGING_DIR}/binary.ldd.txt"; then
  echo "MKL build was requested but libmkl_rt is absent from ldd; refusing to publish." >&2
  exit 9
fi

if [[ "${SOURCE_STATE}" = "dirty" ]]; then
  git diff --binary HEAD -- > "${STAGING_DIR}/source.patch"
fi
git status --short --untracked-files=no > "${STAGING_DIR}/source_status.txt"

(
  cd "${STAGING_DIR}"
  sha256sum Arepo > binary.sha256
)

{
  printf 'build_timestamp_utc=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  printf 'repository=%s\n' "${AREPO_REPO_ROOT}"
  printf 'git_commit=%s\n' "${GIT_COMMIT}"
  printf 'source_state=%s\n' "${SOURCE_STATE}"
  printf 'source_diff_sha256=%s\n' "${SOURCE_DIFF_SHA256}"
  printf 'config_source=%s\n' "${CONFIG_PATH}"
  printf 'config_sha256=%s\n' "${CONFIG_SHA256}"
  printf 'makefile_systype_sha256=%s\n' "${SYSTYPE_SHA256}"
  printf 'mpicc_path=%s\n' "${MPICC_PATH}"
  printf 'mpicc_version=%s\n' "${MPICC_VERSION}"
  printf 'mpicc_show=%s\n' "${MPICC_SHOW}"
  printf 'lapack_backend=%s\n' "${LAPACK_BACKEND}"
  printf 'mklroot=%s\n' "${MKLROOT:-unset}"
  printf 'toolchain_sha256=%s\n' "${TOOLCHAIN_SHA256}"
  printf 'build_fingerprint=%s\n' "${BUILD_FINGERPRINT}"
  printf 'build_name=%s\n' "${BUILD_NAME}"
  printf 'artifact_id=%s\n' "${ARTIFACT_ID}"
} > "${STAGING_DIR}/manifest.txt"

mv "${STAGING_DIR}" "${ARTIFACT_DIR}"
STAGING_DIR=""

echo
echo "Build completed and published atomically."
echo "Artifact: ${ARTIFACT_DIR}"
echo "Binary  : ${ARTIFACT_DIR}/Arepo"
echo "Linear-algebra linkage:"
grep -iE "mkl|lapack|blas" "${ARTIFACT_DIR}/binary.ldd.txt" || echo "(no BLAS/LAPACK entries found)"
