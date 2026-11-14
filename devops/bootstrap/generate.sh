#!/usr/bin/env bash
set -euo pipefail
# Universal source generation: Defs runs first and Python SDO second.
# Both discover inputs under the selected root; without inputs both are no-ops.
# Java SDO follows after initial class compilation in the shared Gradle phase.
locDirectory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
locRepository="$(cd -- "$locDirectory/../.." && pwd -P)"
[[ "${MODUSTRO_BOOTSTRAP_REPOSITORY:-}" == "$locRepository" ]] || {
    echo 'Invoke devops/bootstrap/bootstrap.sh for validated generation settings' >&2
    exit 2
}
locPython="${ALGITES_PYTHON_EXECUTABLE:-python3}"
# Self-hosting seed checks (or pruning) are opt-in per artifact.
"$locPython" "$locDirectory/selfhosting.py" phase \
    --repository "$locRepository" --root "${MODUSTRO_BOOTSTRAP_ROOT:?}" \
    --phase before-generation
# Each invocation owns its temporary files inside the repository build tree.
# Keep this distinct from build/run/bootstrap: build.sh removes that directory
# when assembling the publication staging area.
locWorkRoot="$locRepository/build/run/codegen"
[[ ! -L "$locRepository/build" && ! -L "$locRepository/build/run" && ! -L "$locWorkRoot" ]] || {
    echo 'Refusing symlinked bootstrap work root' >&2; exit 2;
}
mkdir -p -- "$locWorkRoot"
locRunId="${MODUSTRO_BOOTSTRAP_RUN_ID:?missing bootstrap run ID}"
[[ "$locRunId" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]] || {
    echo 'Invalid bootstrap run ID' >&2; exit 2;
}
locCodegenWork="$locWorkRoot/$locRunId"
mkdir -- "$locCodegenWork"
trap 'rm -rf -- "$locCodegenWork"' EXIT
"$locPython" "$locDirectory/generate_sources.py" \
    --repository "$locRepository" \
    --root "${MODUSTRO_BOOTSTRAP_ROOT:?}" \
    --output "$locCodegenWork"
