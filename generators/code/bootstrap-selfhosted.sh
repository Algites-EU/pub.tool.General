#!/usr/bin/env bash
# Compatibility launcher for old self-hosted Codegen invocations.
# All real builds now follow the same descriptor-driven Defs/SDO pipeline.
# In particular this entry point must NEVER call defs.old or generate sources
# through generators/code/regenerate_sources.py.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
locRepository="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
locHasRoot=0
for locArgument in "$@"; do
    case "$locArgument" in --root|--root=*) locHasRoot=1;; esac
done
if (( locHasRoot )); then
    exec bash "$locRepository/devops/bootstrap/bootstrap.sh" "$@"
fi
exec bash "$locRepository/devops/bootstrap/bootstrap.sh" --root generators/code "$@"
