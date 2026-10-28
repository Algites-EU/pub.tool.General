#!/usr/bin/env bash
set -euo pipefail

# Universal Algites/Modustro bootstrap entry point. Repository differences are
# declared by the artifact tree and its build/generator adapters, not this CLI.
locBootstrapDirectory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
locRepository="$(cd -- "$locBootstrapDirectory/../.." && pwd -P)"
locAction=--upload
locRootInput=.
locActionSeen=0
locRootSeen=0
while (( $# )); do
    case "$1" in
        --plan-only|--prepare-only|--upload)
            (( locActionSeen == 0 )) || { echo 'Specify only one bootstrap action' >&2; exit 2; }
            locAction="$1"; locActionSeen=1; shift ;;
        --root)
            (( locRootSeen == 0 )) || { echo '--root may be specified only once' >&2; exit 2; }
            (( $# >= 2 )) || { echo '--root requires a directory' >&2; exit 2; }
            locRootInput="$2"; locRootSeen=1; shift 2 ;;
        --root=*)
            (( locRootSeen == 0 )) || { echo '--root may be specified only once' >&2; exit 2; }
            locRootInput="${1#--root=}"; locRootSeen=1; shift ;;
        --help|-h)
            cat <<'HELP'
Usage: bash devops/bootstrap/bootstrap.sh [--root DIRECTORY] [--plan-only|--prepare-only|--upload]
By default the root is the complete source repository and the action is upload.
--root restricts artifact selection, code generation, generated-source cleanup,
build and publication to a directory below this repository. Paths are resolved
relative to the source repository (not the caller's working directory).
--plan-only never deletes generated sources, compiles or uploads.
HELP
            exit 0 ;;
        *) echo "Unsupported bootstrap option: $1" >&2; exit 2 ;;
    esac
done

locPython="${ALGITES_PYTHON_EXECUTABLE:-python3}"
command -v "$locPython" >/dev/null 2>&1 || { echo "Missing Python: $locPython" >&2; exit 2; }
locRoot="$("$locPython" "$locBootstrapDirectory/clean_generated.py" validate --repository "$locRepository" --root "$locRootInput")"
export MODUSTRO_BOOTSTRAP_REPOSITORY="$locRepository"
export MODUSTRO_BOOTSTRAP_ROOT="$locRoot"
export MODUSTRO_BOOTSTRAP_ROOT_RELATIVE="$("$locPython" - "$locRepository" "$locRoot" <<'PY'
from pathlib import Path
import sys
print(Path(sys.argv[2]).relative_to(Path(sys.argv[1])).as_posix())
PY
)"
export MODUSTRO_BOOTSTRAP_ACTION="$locAction"
if [[ "$locAction" == --prepare-only ]]; then export MODUSTRO_BOOTSTRAP_PREPARE_ONLY=1; fi
printf 'Bootstrap repository: %s\nBootstrap root: %s\nBootstrap action: %s\n' "$locRepository" "$locRoot" "$locAction"

# All adapters receive the same, validated root; never compile a larger tree.
locBuild="$locBootstrapDirectory/build.sh"
[[ -f "$locBuild" ]] || { echo "Missing repository build adapter: $locBuild" >&2; exit 2; }
if [[ "$locAction" == --plan-only ]]; then
    bash "$locBuild" "$locAction"
    exit 0
fi

# A fresh build can NEVER use previously generated source files. Cleanup is
# exactly the same operation in every repository and runs before ANY generator.
"$locPython" "$locBootstrapDirectory/clean_generated.py" clean --repository "$locRepository" --root "$locRoot"
if [[ -f "$locBootstrapDirectory/generate.sh" ]]; then
    bash "$locBootstrapDirectory/generate.sh"
fi
bash "$locBuild" "$locAction"
