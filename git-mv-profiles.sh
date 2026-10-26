#!/usr/bin/env bash
set -euo pipefail

# Preserve Git rename history when applying the profile refactoring archives.
# Run once from ANY directory, passing a path to your original pub.tool.General
# checkout (containing its .git directory). The BP profile archive may be
# unpacked over that checkout before running this script.
#
# Usage: bash git-mv-profiles.sh /path/to/pub.tool.General --dry-run
#        bash git-mv-profiles.sh /path/to/pub.tool.General --apply
#
# The relocated naming files are the ONLY genuine moves: built-in defaults
# stay in their original locations (with neutral contents), and all standard
# profile resources are newly created files, not renames.

repo="${1:-.}"
mode="${2:---dry-run}"
case "$mode" in --dry-run|--apply) ;; *) echo 'Use --dry-run or --apply' >&2; exit 2 ;; esac
repo="$(cd "$repo" && pwd -P)"
if ! git -C "$repo" rev-parse --show-toplevel >/dev/null 2>&1; then
    echo "Not a Git working tree: $repo" >&2; exit 2
fi
root="$(git -C "$repo" rev-parse --show-toplevel)"
if [[ "$root" != "$repo" ]]; then
    echo "Supply the pub.tool.General Git root, not a subdirectory: $root" >&2; exit 2
fi

source_prefix='generators/code/common/src/product/config/eu/algites/lib/naming/convention'
target_prefix='generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention'

move_file() {
    local filename="$1"
    local from="$source_prefix/$filename" to="$target_prefix/$filename"
    if ! git -C "$root" ls-files --error-unmatch -- "$from" >/dev/null 2>&1; then
        if git -C "$root" ls-files --error-unmatch -- "$to" >/dev/null 2>&1; then
            printf 'Already renamed in index: %s\n' "$to"
            return
        fi
        echo "Cannot find tracked source; inspect manually: $from" >&2
        return 1
    fi
    printf 'git mv %q %q\n' "$from" "$to"
    [[ "$mode" == --apply ]] || return 0

    local buffer='' staged=''
    if [[ -f "$root/$to" ]]; then
        # Preserve the NEW profile content already extracted from the archive.
        buffer="$(mktemp)"
        cp -p -- "$root/$to" "$buffer"
        rm -- "$root/$to"
    fi
    mkdir -p -- "$root/$target_prefix"
    if [[ ! -f "$root/$from" ]]; then
        # Overlay may have removed the legacy file: reconstruct its exact
        # staged content for git mv, never silently invent file contents.
        git -C "$root" show ":$from" > "$root/$from"
    fi
    if ! git -C "$root" mv -- "$from" "$to"; then
        if [[ -n "$buffer" ]]; then cp -p -- "$buffer" "$root/$to"; rm -f -- "$buffer"; fi
        return 1
    fi
    if [[ -n "$buffer" ]]; then
        cp -p -- "$buffer" "$root/$to"
        rm -f -- "$buffer"
    fi
    # Stage actual new contents separately, allowing Git's rename detection
    # to compare them against the original history.
    git -C "$root" add -- "$to"
}

move_file algites-java-codegen-method-conventions.yml
move_file algites-python-codegen-method-conventions.yml
if [[ "$mode" == --apply ]]; then
    printf '\nCompleted moves. New modules must be added separately:\n'
    printf '  git -C %q add generators/code/profile\n' "$root"
    printf '\nGit status (renames and additions):\n'
    git -C "$root" status --short -- generators/code/common generators/code/profile
fi
