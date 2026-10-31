#!/usr/bin/env bash
# Preserve Git rename history for generated-dataobject-method-kind_1 ->
# generated-dataobject-structure-kind_1 in pub.tool.General.
#
# Usage (from any directory):
#   bash git-mv-generated-dataobject-structure-kind.sh /path/to/pub.tool.General
#
# Run before OR after overlaying the updated archive. If the renamed destination
# already exists, its contents are preserved. Only these six paths are touched.
set -euo pipefail

if (( $# > 1 )); then
    printf 'Usage: %s [path-to-pub.tool.General]\n' "$0" >&2
    exit 2
fi

repo="${1:-.}"
if ! root="$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null)"; then
    printf 'ERROR: Not a Git working tree: %s\n' "$repo" >&2
    exit 1
fi
cd "$root"

base='generators/code/common/src/product'
old_name='generated-dataobject-method-kind_1'
new_name='generated-dataobject-structure-kind_1'

move_file() {
    local dialect="$1" extension="$2"
    local dir="$base/$dialect/eu/algites/tool/codegen/common/naming"
    local old="$dir/${old_name}.${extension}"
    local new="$dir/${new_name}.${extension}"
    local tmp

    if git ls-files --error-unmatch -- "$old" >/dev/null 2>&1; then
        if [[ -f "$old" && ! -e "$new" ]]; then
            git mv -- "$old" "$new"
            printf 'RENAMED: %s -> %s\n' "$old" "$new"
        elif [[ -f "$old" && -f "$new" ]]; then
            # Do not silently discard local edits to the legacy source.
            if ! git diff --quiet -- "$old"; then
                printf 'ERROR: Legacy source has local changes; resolve manually: %s\n' "$old" >&2
                return 1
            fi
            # Typical case after overlaying a new repository snapshot.
            # Save new content, record the rename, then restore new content.
            tmp="$(mktemp)"
            cp -p -- "$new" "$tmp"
            rm -- "$new"
            if git mv -- "$old" "$new"; then
                cp -p -- "$tmp" "$new"
                rm -- "$tmp"
                git add -- "$new"
                printf 'RENAMED (updated contents retained): %s -> %s\n' "$old" "$new"
            else
                cp -p -- "$tmp" "$new"
                rm -- "$tmp"
                printf 'ERROR: git mv failed for %s\n' "$old" >&2
                return 1
            fi
        elif [[ ! -e "$old" && -f "$new" ]]; then
            # Original was already removed by extraction. Git still detects
            # renames from the staged delete/add pair (similarity permitting).
            git add -u -- "$old"
            git add -- "$new"
            printf 'STAGED existing delete/add (rename detection by Git): %s -> %s\n' "$old" "$new"
        else
            printf 'ERROR: Expected source or destination not found: %s / %s\n' "$old" "$new" >&2
            return 1
        fi
    elif [[ -f "$new" ]]; then
        printf 'SKIP (already renamed or source not tracked): %s\n' "$new"
    else
        printf 'ERROR: Neither tracked original nor renamed file is available: %s / %s\n' "$old" "$new" >&2
        return 1
    fi
}

for dialect in xmldefs yamldefs jsondefs; do
    case "$dialect" in
        xmldefs) extension='xsd' ;;
        yamldefs) extension='yamldef.schema.json' ;;
        jsondefs) extension='jsondef.schema.json' ;;
    esac
    move_file "$dialect" "$extension"
    move_file "$dialect" "$extension.meta.yml"
done

printf '\nGit staged changes in relevant naming paths:\n'
git diff --cached --name-status --find-renames -- "$base"
printf '\nNext: review the diff and stage remaining source changes with git add.\n'
