#!/usr/bin/env bash
# Preserve Git rename tracking for codegen profile files and feature test renames.
# Run from any subdirectory INSIDE the pub.tool.General git worktree.
# --dry-run: show what would change, without changing files or the index.
# Intended to run BEFORE or AFTER extracting the updated pub.tool.General TGZ.
set -euo pipefail

DRY_RUN=0
case "${1:-}" in
  --dry-run|--check) DRY_RUN=1 ;;
  "") ;;
  *) printf 'Usage: %s [--dry-run]\n' "$0" >&2; exit 2 ;;
esac

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  printf 'ERROR: Run this script within the pub.tool.General Git repository.\n' >&2
  exit 2
}
cd "$ROOT"
if [[ "$(basename "$ROOT")" != 'pub.tool.General' ]]; then
  printf 'ERROR: Expected pub.tool.General repo root, found %s\n' "$ROOT" >&2
  exit 2
fi

moved=0
already=0
untracked=0
missing=0

is_tracked() { git ls-files --error-unmatch -- "$1" >/dev/null 2>&1; }

move_one() {
  local src="$1" dst="$2" tmp

  if is_tracked "$dst"; then
    if is_tracked "$src"; then
      printf 'ERROR: Source and destination are both independently tracked:\n  %s\n  %s\n' "$src" "$dst" >&2
      exit 1
    fi
    printf 'ALREADY TRACKED: %s\n' "$dst"
    ((already+=1))
    return 0
  fi

  if ! is_tracked "$src"; then
    if [[ -e "$src" || -e "$dst" ]]; then
      printf 'NEW/UNTRACKED (no old Git history available): %s\n' "$dst"
      ((untracked+=1))
    else
      printf 'NOT PRESENT IN THIS GIT REVISION: %s\n' "$src"
      ((missing+=1))
    fi
    return 0
  fi

  # Never silently lose edits on the old path when an updated new path
  # also exists. An unchanged indexed old source may safely be replaced by
  # the already-extracted destination, but two independent edits are a conflict.
  if [[ -e "$src" && -e "$dst" ]] && ! cmp -s -- "$src" "$dst"; then
    if ! (git show ":$src" | cmp -s - "$src"); then
      printf 'ERROR: Source and destination BOTH have distinct edits; refusing to overwrite either:\n  %s\n  %s\n' "$src" "$dst" >&2
      exit 1
    fi
  fi

  if [[ ! -e "$src" && ! -e "$dst" ]]; then
    printf 'ERROR: Tracked source and destination are both absent:\n  %s\n  %s\n' "$src" "$dst" >&2
    exit 1
  fi
  if ((DRY_RUN)); then
    printf 'WOULD GIT MV: %s -> %s%s\n' "$src" "$dst" "$([[ -e "$dst" ]] && printf ' (keep existing destination contents)' || true)"
    ((moved+=1))
    return 0
  fi

  mkdir -p -- "$(dirname "$dst")"
  if [[ ! -e "$src" ]]; then
    # Old path was deleted by unpacking a new archive. Restore only the
    # indexed original bytes, then git-mv it. No uncommitted old content
    # is overwritten because the old working-tree path does not exist.
    mkdir -p -- "$(dirname "$src")"
    git show ":$src" > "$src"
  fi
  if [[ -e "$dst" ]]; then
    # The archive may already contain updated destination content. Move it
    # aside without losing contents or mtime, stage the original git rename,
    # then put the updated file back as an unstaged working-tree change.
    tmp="$(mktemp -d)"
    mv -- "$dst" "$tmp/destination"
    if ! git mv -- "$src" "$dst"; then
      mv -- "$tmp/destination" "$dst"
      rmdir -- "$tmp"
      printf 'ERROR: git mv failed; existing destination restored: %s\n' "$dst" >&2
      exit 1
    fi
    mv -f -- "$tmp/destination" "$dst"
    rmdir -- "$tmp"
    printf 'GIT MV (destination content and mtime preserved): %s -> %s\n' "$src" "$dst"
  else
    git mv -- "$src" "$dst"
    printf 'GIT MV: %s -> %s\n' "$src" "$dst"
  fi
  ((moved+=1))
}

printf '\n=== Codegen convention catalogs: 18 moves ===\n'
move_one "generators/code/profile/algites/src/product/config/eu/algites/tool/codegen/algites-java-common-codegen-conventions.yml" "generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-java-common-codegen-conventions.yml"
move_one "generators/code/profile/algites/src/product/config/eu/algites/tool/codegen/algites-java-defs-codegen-conventions.yml" "generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-java-defs-codegen-conventions.yml"
move_one "generators/code/profile/algites/src/product/config/eu/algites/tool/codegen/algites-java-sdo-codegen-conventions.yml" "generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-java-sdo-codegen-conventions.yml"
move_one "generators/code/profile/algites/src/product/config/eu/algites/tool/codegen/algites-python-common-codegen-conventions.yml" "generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-python-common-codegen-conventions.yml"
move_one "generators/code/profile/algites/src/product/config/eu/algites/tool/codegen/algites-python-defs-codegen-conventions.yml" "generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-python-defs-codegen-conventions.yml"
move_one "generators/code/profile/algites/src/product/config/eu/algites/tool/codegen/algites-python-sdo-codegen-conventions.yml" "generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-python-sdo-codegen-conventions.yml"
move_one "generators/code/profile/standardpostfix/src/product/config/eu/algites/tool/codegen/standardpostfix-java-common-codegen-conventions.yml" "generators/code/profile/standardpostfix/src/product/config/eu/algites/lib/naming/convention/sourcecode/standardpostfix-java-common-codegen-conventions.yml"
move_one "generators/code/profile/standardpostfix/src/product/config/eu/algites/tool/codegen/standardpostfix-java-defs-codegen-conventions.yml" "generators/code/profile/standardpostfix/src/product/config/eu/algites/lib/naming/convention/sourcecode/standardpostfix-java-defs-codegen-conventions.yml"
move_one "generators/code/profile/standardpostfix/src/product/config/eu/algites/tool/codegen/standardpostfix-java-sdo-codegen-conventions.yml" "generators/code/profile/standardpostfix/src/product/config/eu/algites/lib/naming/convention/sourcecode/standardpostfix-java-sdo-codegen-conventions.yml"
move_one "generators/code/profile/standardpostfix/src/product/config/eu/algites/tool/codegen/standardpostfix-python-common-codegen-conventions.yml" "generators/code/profile/standardpostfix/src/product/config/eu/algites/lib/naming/convention/sourcecode/standardpostfix-python-common-codegen-conventions.yml"
move_one "generators/code/profile/standardpostfix/src/product/config/eu/algites/tool/codegen/standardpostfix-python-defs-codegen-conventions.yml" "generators/code/profile/standardpostfix/src/product/config/eu/algites/lib/naming/convention/sourcecode/standardpostfix-python-defs-codegen-conventions.yml"
move_one "generators/code/profile/standardpostfix/src/product/config/eu/algites/tool/codegen/standardpostfix-python-sdo-codegen-conventions.yml" "generators/code/profile/standardpostfix/src/product/config/eu/algites/lib/naming/convention/sourcecode/standardpostfix-python-sdo-codegen-conventions.yml"
move_one "generators/code/profile/standardprefix/src/product/config/eu/algites/tool/codegen/standardprefix-java-common-codegen-conventions.yml" "generators/code/profile/standardprefix/src/product/config/eu/algites/lib/naming/convention/sourcecode/standardprefix-java-common-codegen-conventions.yml"
move_one "generators/code/profile/standardprefix/src/product/config/eu/algites/tool/codegen/standardprefix-java-defs-codegen-conventions.yml" "generators/code/profile/standardprefix/src/product/config/eu/algites/lib/naming/convention/sourcecode/standardprefix-java-defs-codegen-conventions.yml"
move_one "generators/code/profile/standardprefix/src/product/config/eu/algites/tool/codegen/standardprefix-java-sdo-codegen-conventions.yml" "generators/code/profile/standardprefix/src/product/config/eu/algites/lib/naming/convention/sourcecode/standardprefix-java-sdo-codegen-conventions.yml"
move_one "generators/code/profile/standardprefix/src/product/config/eu/algites/tool/codegen/standardprefix-python-common-codegen-conventions.yml" "generators/code/profile/standardprefix/src/product/config/eu/algites/lib/naming/convention/sourcecode/standardprefix-python-common-codegen-conventions.yml"
move_one "generators/code/profile/standardprefix/src/product/config/eu/algites/tool/codegen/standardprefix-python-defs-codegen-conventions.yml" "generators/code/profile/standardprefix/src/product/config/eu/algites/lib/naming/convention/sourcecode/standardprefix-python-defs-codegen-conventions.yml"
move_one "generators/code/profile/standardprefix/src/product/config/eu/algites/tool/codegen/standardprefix-python-sdo-codegen-conventions.yml" "generators/code/profile/standardprefix/src/product/config/eu/algites/lib/naming/convention/sourcecode/standardprefix-python-sdo-codegen-conventions.yml"

printf '\n=== Feature-test renames: 5 moves ===\n'
move_one "generators/code/defscodegen/impl/src/develop/python/test_bootstrap_setter_policy_dependency_guard.py" "generators/code/defscodegen/impl/src/develop/python/test_selfhosted_dependency_preflight.py"
move_one "generators/code/defscodegen/impl/src/develop/python/test_canonical_type_without_legacy_fields.py" "generators/code/defscodegen/impl/src/develop/python/test_canonical_type_field_projection.py"
move_one "generators/code/defscodegen/impl/src/develop/python/test_choice_marker_r19.py" "generators/code/defscodegen/impl/src/develop/python/test_choice_contract_metadata.py"
move_one "generators/code/defscodegen/impl/src/develop/python/test_new_canonical_frontend.py" "generators/code/defscodegen/impl/src/develop/python/test_canonical_schema_frontend.py"
move_one "generators/code/sdocodegen/impl/src/develop/python/test_synthetic_map_value_new.py" "generators/code/sdocodegen/impl/src/develop/python/test_synthetic_map_entry_contract.py"

printf '\nSummary: moved=%s already-tracked=%s untracked/new=%s absent-in-revision=%s\n' "$moved" "$already" "$untracked" "$missing"
if ((DRY_RUN)); then printf 'Dry run: no changes were made.\n'; fi
printf 'Review: git status --short && git diff --cached --summary\n'
