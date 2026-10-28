#!/usr/bin/env bash
set -euo pipefail
# Compatibility entry point. The repository's universal bootstrap is canonical;
# the selected root, descriptors, cleanup and build are handled there.
locRepository="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
locRootPassed=0
for locArgument in "$@"; do
    if [[ "$locArgument" == --root || "$locArgument" == --root=* ]]; then
        locRootPassed=1
    fi
done
if (( locRootPassed )); then
    exec bash "$locRepository/devops/bootstrap/bootstrap.sh" "$@"
else
    exec bash "$locRepository/devops/bootstrap/bootstrap.sh" --root generators/code "$@"
fi
