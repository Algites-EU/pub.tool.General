#!/usr/bin/env bash
set -euo pipefail

repo="${1:-.}"
repo="$(cd "$repo" && pwd -P)"
tracked_root="$(git -C "$repo" rev-parse --show-toplevel)"
if [[ "$repo" != "$tracked_root" ]]; then
    printf 'ERROR: Provide pub.tool.General repository root. Actual Git root: %s\n' "$tracked_root" >&2
    exit 1
fi

source_path='generators/code/defscodegen/impl/src/product/resources/eu/algites/tool/codegen/defs/schema-python-runtime.py'
target_path='generators/code/defscodegen/impl/src/product/resources/eu/algites/tool/codegen/defs/impl/standard/schema-python-runtime.py'

if [[ ! -f "$repo/$source_path" ]]; then
    printf 'ERROR: Source file does not exist: %s\n' "$source_path" >&2
    exit 1
fi
if [[ -e "$repo/$target_path" ]]; then
    printf 'ERROR: Target file already exists: %s\n' "$target_path" >&2
    exit 1
fi

mkdir -p "$repo/$(dirname "$target_path")"
git -C "$repo" mv -- "$source_path" "$target_path"
printf 'Staged Git move:\n  %s\n  -> %s\n' "$source_path" "$target_path"
