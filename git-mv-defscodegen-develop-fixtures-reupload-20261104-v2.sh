#!/usr/bin/env bash
# Relocate Defs Codegen develop-only schemas into examples without losing Git history.
# Run from the root of the pub.tool.General repository BEFORE extracting the updated TGZ.
# The script intentionally touches neither product schemas nor generated sources.
set -euo pipefail

if [[ ! -f modustro-source-repository.yml || ! -d generators/code/defscodegen/impl ]]; then
    printf 'ERROR: run from the pub.tool.General repository root.\n' >&2
    exit 2
fi
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    printf 'ERROR: a Git working tree is required for git mv.\n' >&2
    exit 2
fi

mode="${1:-}"
if [[ "$mode" != "" && "$mode" != "--dry-run" ]]; then
    printf 'Usage: %s [--dry-run]\n' "$0" >&2
    exit 2
fi

while IFS=$'\t' read -r old new; do
    if [[ -f "$old" ]]; then
        if [[ -e "$new" ]]; then
            printf 'ERROR: destination already exists: %s\n' "$new" >&2
            exit 3
        fi
        if [[ "$mode" == "--dry-run" ]]; then
            printf 'git mv -- %q %q\n' "$old" "$new"
        else
            mkdir -p -- "$(dirname -- "$new")"
            git mv -- "$old" "$new"
            printf 'Moved: %s -> %s\n' "$old" "$new"
        fi
    elif [[ -f "$new" ]]; then
        printf 'Already moved: %s\n' "$new"
    else
        printf 'ERROR: both old and new files missing: %s / %s\n' "$old" "$new" >&2
        exit 4
    fi
done <<'MOVES'
generators/code/defscodegen/impl/src/develop/jsondefs/document-common-metadata_1.jsondef.schema.json	generators/code/defscodegen/impl/src/develop/examples/jsondefs/document-common-metadata_1.jsondef.schema.json
generators/code/defscodegen/impl/src/develop/jsondefs/parity-child_1.jsondef.schema.json	generators/code/defscodegen/impl/src/develop/examples/jsondefs/parity-child_1.jsondef.schema.json
generators/code/defscodegen/impl/src/develop/jsondefs/parity-leaf_1.jsondef.schema.json	generators/code/defscodegen/impl/src/develop/examples/jsondefs/parity-leaf_1.jsondef.schema.json
generators/code/defscodegen/impl/src/develop/jsondefs/parity-status_1.jsondef.schema.json	generators/code/defscodegen/impl/src/develop/examples/jsondefs/parity-status_1.jsondef.schema.json
generators/code/defscodegen/impl/src/develop/jsondefs/parity-supported-builtins_1.jsondef.schema.json	generators/code/defscodegen/impl/src/develop/examples/jsondefs/parity-supported-builtins_1.jsondef.schema.json
generators/code/defscodegen/impl/src/develop/jsondefs/parity-supported_1.jsondef.schema.json	generators/code/defscodegen/impl/src/develop/examples/jsondefs/parity-supported_1.jsondef.schema.json
generators/code/defscodegen/impl/src/develop/yamldefs/document-common-metadata_1.yamldef.schema.json	generators/code/defscodegen/impl/src/develop/examples/yamldefs/document-common-metadata_1.yamldef.schema.json
generators/code/defscodegen/impl/src/develop/yamldefs/parity-child_1.yamldef.schema.json	generators/code/defscodegen/impl/src/develop/examples/yamldefs/parity-child_1.yamldef.schema.json
generators/code/defscodegen/impl/src/develop/yamldefs/parity-leaf_1.yamldef.schema.json	generators/code/defscodegen/impl/src/develop/examples/yamldefs/parity-leaf_1.yamldef.schema.json
generators/code/defscodegen/impl/src/develop/yamldefs/parity-status_1.yamldef.schema.json	generators/code/defscodegen/impl/src/develop/examples/yamldefs/parity-status_1.yamldef.schema.json
generators/code/defscodegen/impl/src/develop/yamldefs/parity-supported-builtins_1.yamldef.schema.json	generators/code/defscodegen/impl/src/develop/examples/yamldefs/parity-supported-builtins_1.yamldef.schema.json
generators/code/defscodegen/impl/src/develop/yamldefs/parity-supported_1.yamldef.schema.json	generators/code/defscodegen/impl/src/develop/examples/yamldefs/parity-supported_1.yamldef.schema.json
generators/code/defscodegen/impl/src/develop/xmldefs/parity-child_1.xsd	generators/code/defscodegen/impl/src/develop/examples/xmldefs/parity-child_1.xsd
generators/code/defscodegen/impl/src/develop/xmldefs/parity-leaf_1.xsd	generators/code/defscodegen/impl/src/develop/examples/xmldefs/parity-leaf_1.xsd
generators/code/defscodegen/impl/src/develop/xmldefs/parity-status_1.xsd	generators/code/defscodegen/impl/src/develop/examples/xmldefs/parity-status_1.xsd
generators/code/defscodegen/impl/src/develop/xmldefs/parity-supported-builtins_1.xsd	generators/code/defscodegen/impl/src/develop/examples/xmldefs/parity-supported-builtins_1.xsd
generators/code/defscodegen/impl/src/develop/xmldefs/parity-supported_1.xsd	generators/code/defscodegen/impl/src/develop/examples/xmldefs/parity-supported_1.xsd
MOVES

if [[ "$mode" == "--dry-run" ]]; then
    printf '\nDry-run complete. No files were changed.\n'
else
    printf '\nMoves complete. Inspect with: git diff --cached --summary\n'
fi
