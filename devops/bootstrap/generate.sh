#!/usr/bin/env bash
set -euo pipefail
# Universal source generation: Defs runs first and Python SDO second.
# Both discover inputs under the selected root; without inputs both are no-ops.
# Java SDO follows after initial class compilation in the shared Gradle phase.
locDirectory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
locRepository="$(cd -- "$locDirectory/../.." && pwd -P)"
[[ "${MODUSTRO_BOOTSTRAP_REPOSITORY:-}" == "$locRepository" ]] || {
    echo 'Invoke devops/bootstrap/bootstrap.sh so generated sources are cleaned first' >&2
    exit 2
}
locPython="${ALGITES_PYTHON_EXECUTABLE:-python3}"
locCodegenWork="$(mktemp -d)"
trap 'rm -rf -- "$locCodegenWork"' EXIT
"$locPython" "$locDirectory/generate_sources.py" \
    --repository "$locRepository" \
    --root "${MODUSTRO_BOOTSTRAP_ROOT:?}" \
    --output "$locCodegenWork"
