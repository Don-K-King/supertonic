#!/usr/bin/env bash
# Builds the supertonic wheel from ONE commit of this repository, offline and repeatably.
#
#   tools/build-wheel.sh [--commit <40 hex>] --build-wheels <dir> --build-lock <file> --out <dir>
#
# The source is `git archive <commit>` in a fresh directory, never the working tree; without
# --commit the call takes HEAD and refuses a tree with uncommitted changes to tracked files.
# The build tools (setuptools, wheel) come from --build-wheels with --no-index, at exactly the
# versions and hashes of --build-lock: the setuptools version is written INTO the wheel
# (dist-info/WHEEL "Generator:"), so "whatever the folder holds" would change the sha256.
# SOURCE_DATE_EPOCH is the commit time and the umask 022, so two builds give the same bytes.
# Prints one line: <wheel path> <size> <sha256>.
set -euo pipefail

usage() {
    echo "usage: $0 [--commit <40 hex>] --build-wheels <dir> --build-lock <file> --out <dir>" >&2
    exit 2
}

commit="" build_wheels="" build_lock="" out=""
while [ $# -gt 0 ]; do
    case "$1" in
        --commit) commit="${2:-}"; shift 2 ;;
        --build-wheels) build_wheels="${2:-}"; shift 2 ;;
        --build-lock) build_lock="${2:-}"; shift 2 ;;
        --out) out="${2:-}"; shift 2 ;;
        *) usage ;;
    esac
done
[ -n "${build_wheels}" ] && [ -n "${build_lock}" ] && [ -n "${out}" ] || usage
[ -d "${build_wheels}" ] || { echo "ERROR: --build-wheels is no directory: ${build_wheels}" >&2; exit 2; }
[ -f "${build_lock}" ] || { echo "ERROR: --build-lock is no file: ${build_lock}" >&2; exit 2; }

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -z "${commit}" ]; then
    if [ -n "$(git -C "${REPO}" status --porcelain --untracked-files=no)" ]; then
        echo "ERROR: uncommitted changes to tracked files - commit them or pass --commit" >&2
        exit 2
    fi
    commit="$(git -C "${REPO}" rev-parse HEAD)"
fi
[[ "${commit}" =~ ^[0-9a-f]{40}$ ]] || { echo "ERROR: --commit must be 40 hex: ${commit}" >&2; exit 2; }
git -C "${REPO}" cat-file -e "${commit}^{commit}" 2>/dev/null \
    || { echo "ERROR: commit ${commit} does not exist in ${REPO}" >&2; exit 2; }

build_wheels="$(cd "${build_wheels}" && pwd)"
build_lock="$(cd "$(dirname "${build_lock}")" && pwd)/$(basename "${build_lock}")"
mkdir -p "${out}"
out="$(cd "${out}" && pwd)"

umask 022
work="$(mktemp -d "${TMPDIR:-/tmp}/supertonic-wheel-build.XXXXXX")"
trap 'rm -rf "${work:?}"' EXIT
mkdir "${work}/src" "${work}/dist" "${work}/uv-cache"
git -C "${REPO}" archive "${commit}" | tar -x -C "${work}/src"

SOURCE_DATE_EPOCH="$(git -C "${REPO}" show -s --format=%ct "${commit}")"
export SOURCE_DATE_EPOCH PYTHONDONTWRITEBYTECODE=1
UV_CACHE_DIR="${work}/uv-cache" uv build --quiet --wheel --no-python-downloads \
    --python "${PYTHON:-python3.12}" \
    --no-index --find-links "${build_wheels}" \
    --build-constraints "${build_lock}" --require-hashes \
    --out-dir "${work}/dist" "${work}/src"

shopt -s nullglob
wheels=("${work}"/dist/*.whl)
[ "${#wheels[@]}" -eq 1 ] || { echo "ERROR: expected one wheel, got ${#wheels[@]}" >&2; exit 1; }
target="${out}/$(basename "${wheels[0]}")"
cp "${wheels[0]}" "${target}"
echo "${target} $(stat -c %s "${target}") $(sha256sum "${target}" | cut -d' ' -f1)"
