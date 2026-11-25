#!/usr/bin/env bash
# The one aggregate check of this repository: a fresh environment built offline from the evido
# artefact store, then every test against the WORKING TREE (the package itself is never
# installed into that environment, so a stale wheel in the store cannot answer for the source).
#
#   EVIDO_ARTIFACT_STORE   store root (default: ../evido-v1.0/artifact-store)
#   SUPERTONIC_TEST_MODEL  model snapshot for the tests (default: see conftest.py)
#   PYTHON                 interpreter for the environment (default: python3.12, the image's)
# Extra arguments go to pytest.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STORE="${EVIDO_ARTIFACT_STORE:-${REPO}/../evido-v1.0/artifact-store}"
RUNTIME_WHEELS="${STORE}/python/supertonic-wheels-cp312"
TEST_WHEELS="${STORE}/python/backend-wheels"
VENV="${REPO}/.venv"

for dir in "${RUNTIME_WHEELS}" "${TEST_WHEELS}"; do
    [ -d "${dir}" ] || { echo "ERROR: wheel folder missing: ${dir} (set EVIDO_ARTIFACT_STORE)" >&2; exit 2; }
done

export PYTHONDONTWRITEBYTECODE=1
uv venv --quiet --clear --no-python-downloads --python "${PYTHON:-python3.12}" "${VENV}"
# -r pyproject.toml installs the declared dependencies only, never the project.
uv pip install --quiet --python "${VENV}/bin/python" --no-index \
    --find-links "${RUNTIME_WHEELS}" --find-links "${TEST_WHEELS}" \
    -r "${REPO}/pyproject.toml" --extra serve -r "${REPO}/requirements-test.in"

if "${VENV}/bin/python" -I -c "import importlib.util, sys; sys.exit(importlib.util.find_spec('supertonic') is None)"; then
    echo "ERROR: supertonic is installed in ${VENV}; the tests must import the working tree" >&2
    exit 2
fi

cd "${REPO}"
exec "${VENV}/bin/python" -m pytest -p no:cacheprovider -q "$@" tests
