#!/usr/bin/env bash
set -euo pipefail

# Run from the target repository root, before or after extracting the updated ZIP.
# git mv stages the path change; existing updated destination content is preserved.
# This script does not commit changes, remove module build files, or contact remotes.
locDryRun=false
if [[ ${1:-} == --dry-run && $# -eq 1 ]]; then
    locDryRun=true
elif [[ $# -ne 0 ]]; then
    echo "Usage: bash $0 [--dry-run] (from the target repository root)" >&2
    exit 2
fi
locRepositoryDir="$(pwd -P)"
locGitRoot="$(git rev-parse --show-toplevel)"
locGitRoot="$(cd -- "${locGitRoot}" && pwd -P)"
if [[ "${locRepositoryDir}" != "${locGitRoot}" ]]; then
    echo "Run this script from the target Git repository root." >&2
    exit 1
fi

locOldPaths=(
    "algites-source-repository.yml"
    "generators/algites-artifact-set.yml"
    "generators/code/algites-artifact-set.yml"
    "generators/code/defscodegen/algites-artifact-set.yml"
    "generators/code/defscodegen/cli/algites-artifact.yml"
    "generators/code/defscodegen/impl/algites-artifact.yml"
    "generators/code/defscodegen/intf/algites-artifact.yml"
    "naming/algites-artifact-set.yml"
    "naming/validator/algites-artifact-set.yml"
    "naming/validator/cli/algites-artifact.yml"
)
locNewPaths=(
    "modustro-source-repository.yml"
    "generators/modustro-artifact-set.yml"
    "generators/code/modustro-artifact-set.yml"
    "generators/code/defscodegen/modustro-artifact-set.yml"
    "generators/code/defscodegen/cli/modustro-artifact.yml"
    "generators/code/defscodegen/impl/modustro-artifact.yml"
    "generators/code/defscodegen/intf/modustro-artifact.yml"
    "naming/modustro-artifact-set.yml"
    "naming/validator/modustro-artifact-set.yml"
    "naming/validator/cli/modustro-artifact.yml"
)

# Validate the entire migration before changing the index or working tree.
for locIndex in "${!locOldPaths[@]}"; do
    locOld="${locOldPaths[locIndex]}"
    locNew="${locNewPaths[locIndex]}"
    if [[ -L "${locOld}" || -L "${locNew}" ]]; then
        echo "Refusing a symbolic link: ${locOld} -> ${locNew}" >&2; exit 1
    fi
    if [[ -f "${locOld}" ]]; then
        git ls-files --error-unmatch -- "${locOld}" >/dev/null 2>&1 || {
            echo "Original path is not tracked: ${locOld}" >&2; exit 1;
        }
        if git ls-files --error-unmatch -- "${locNew}" >/dev/null 2>&1; then
            echo "Both paths are tracked; resolve the existing index changes first: ${locOld} -> ${locNew}" >&2
            exit 1
        fi
        if [[ -e "${locNew}" && ! -f "${locNew}" ]]; then
            echo "Destination is not a regular file: ${locNew}" >&2; exit 1
        fi
        if git ls-files --unmerged -- "${locOld}" "${locNew}" | read -r locConflict; then
            echo "Resolve the merge conflict first: ${locOld} -> ${locNew}" >&2; exit 1
        fi
    elif [[ -f "${locNew}" ]] && git ls-files --error-unmatch -- "${locNew}" >/dev/null 2>&1; then
        : # Already migrated; a repeated invocation can safely skip it.
    else
        echo "Missing tracked source (or already tracked destination): ${locOld} -> ${locNew}" >&2
        exit 1
    fi
 done

locBackupDir="$(mktemp -d "${TMPDIR:-/tmp}/modustro-git-mv.XXXXXXXX")"
locRestorePath=""
locRestoreBackup=""
AIcCleanup() {
    if [[ -n "${locRestorePath}" && -f "${locRestoreBackup}" ]]; then
        cp -p -- "${locRestoreBackup}" "${locRestorePath}"
    fi
    rm -rf -- "${locBackupDir}"
}
trap AIcCleanup EXIT
for locIndex in "${!locOldPaths[@]}"; do
    locOld="${locOldPaths[locIndex]}"
    locNew="${locNewPaths[locIndex]}"
    if [[ ! -f "${locOld}" ]]; then
        printf 'Already renamed: %s\n' "${locNew}"
        continue
    fi
    printf 'git mv -- %q %q\n' "${locOld}" "${locNew}"
    if [[ "${locDryRun}" == true ]]; then continue; fi
    if [[ -f "${locNew}" ]]; then
        # Preserve the content from an updated ZIP without replacing it with the old source.
        locRestoreBackup="${locBackupDir}/${locIndex}"
        locRestorePath="${locRepositoryDir}/${locNew}"
        cp -p -- "${locNew}" "${locRestoreBackup}"
        rm -- "${locNew}"
    fi
    git mv -- "${locOld}" "${locNew}"
    if [[ -n "${locRestorePath}" ]]; then
        cp -p -- "${locRestoreBackup}" "${locRestorePath}"
        locRestorePath=""
        locRestoreBackup=""
    fi
 done
if [[ "${locDryRun}" == true ]]; then
    echo "Dry run complete; no files or index entries were changed."
else
    echo "Descriptor paths renamed. Extract the updated ZIP if needed, review git diff, then stage the updated content."
fi
