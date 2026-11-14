#!/usr/bin/env bash
set -euo pipefail

# The very first Python invocation must not write bytecode beside source files.
# The flag is inherited by generators, Gradle subprocesses and nested bootstraps.
export PYTHONDONTWRITEBYTECODE=1


# Universal Algites/Modustro bootstrap entry point. Repository differences are
# declared by the artifact tree and its build/generator adapters, not this CLI.
locBootstrapDirectory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
locRepository="$(cd -- "$locBootstrapDirectory/../.." && pwd -P)"
locAction=--upload
locRootInput=.
locActionSeen=0
locRootSeen=0
locValidateSeen=0
locCleanupSeen=0
while (( $# )); do
    case "$1" in
        --plan-only|--prepare-only|--upload|--upload-prepared)
            (( locActionSeen == 0 )) || { echo 'Specify only one bootstrap action' >&2; exit 2; }
            locAction="$1"; locActionSeen=1; shift ;;
        --root)
            (( locRootSeen == 0 )) || { echo '--root may be specified only once' >&2; exit 2; }
            (( $# >= 2 )) || { echo '--root requires a directory' >&2; exit 2; }
            locRootInput="$2"; locRootSeen=1; shift 2 ;;
        --root=*)
            (( locRootSeen == 0 )) || { echo '--root may be specified only once' >&2; exit 2; }
            locRootInput="${1#--root=}"; locRootSeen=1; shift ;;
        --codegen-validate-one-input-at-a-time-only=*)
            (( locValidateSeen == 0 )) || { echo 'Specify Codegen validation policy only once' >&2; exit 2; }
            locValidatePolicy="${1#--codegen-validate-one-input-at-a-time-only=}"
            [[ "$locValidatePolicy" == true || "$locValidatePolicy" == false ]] || {
                echo 'Codegen validation policy must be true or false' >&2; exit 2;
            }
            export MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY="$locValidatePolicy"
            locValidateSeen=1; shift ;;
        --cleanup-output-folder-before-generation=*)
            (( locCleanupSeen == 0 )) || { echo 'Specify Codegen cleanup policy only once' >&2; exit 2; }
            locCleanupPolicy="${1#--cleanup-output-folder-before-generation=}"
            [[ "$locCleanupPolicy" == true || "$locCleanupPolicy" == false ]] || {
                echo 'Codegen cleanup must be true or false' >&2; exit 2;
            }
            export MODUSTRO_CODEGEN_CLEANUP_OUTPUT_FOLDER_BEFORE_GENERATION="$locCleanupPolicy"
            locCleanupSeen=1; shift ;;
        --help|-h)
            cat <<'HELP'
Usage: bash devops/bootstrap/bootstrap.sh [--root DIRECTORY] [--plan-only|--prepare-only|--upload|--upload-prepared]
    [--codegen-validate-one-input-at-a-time-only=true|false]
    [--cleanup-output-folder-before-generation=true|false]
By default the root is the complete source repository and the action is upload.
--upload-prepared skips generation/build and uploads the last verified Maven snapshot and
latest matching complete Python wheel+sdist from the local artifact repositories.
--root restricts artifact selection, code generation, optional generated-source cleanup,
build and publication to a directory below this repository. Paths are resolved
relative to the source repository (not the caller's working directory).
--plan-only never deletes generated sources, compiles or uploads.
--cleanup-output-folder-before-generation defaults to repository bootstrap policy: existing outputs
are replaced individually; other files remain untouched. When true, the
selected *.gen source folders are cleaned once before generation.
The Codegen validation policy defaults to false (aggregate all input errors).
With true, stop after checking the first failing input in full.
HELP
            exit 0 ;;
        *) echo "Unsupported bootstrap option: $1" >&2; exit 2 ;;
    esac
done

# All generator CLIs, including Gradle's Java SDO process, inherit one policy.
export MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY="${MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY:-false}"
# The bootstrap engine is identical in all repositories. Only the optional
# bootstrap-specializations.yml declares exceptional self-hosting behavior.
locSelfhosting="$locBootstrapDirectory/selfhosting.py"
locCleanupDefault="$("${ALGITES_PYTHON_EXECUTABLE:-python3}" "$locSelfhosting" clean-default --repository "$locRepository")"
locRequireFresh="$("${ALGITES_PYTHON_EXECUTABLE:-python3}" "$locSelfhosting" require-fresh --repository "$locRepository")"
export MODUSTRO_CODEGEN_CLEANUP_OUTPUT_FOLDER_BEFORE_GENERATION="${MODUSTRO_CODEGEN_CLEANUP_OUTPUT_FOLDER_BEFORE_GENERATION:-$locCleanupDefault}"
[[ "$MODUSTRO_CODEGEN_CLEANUP_OUTPUT_FOLDER_BEFORE_GENERATION" == true ||
   "$MODUSTRO_CODEGEN_CLEANUP_OUTPUT_FOLDER_BEFORE_GENERATION" == false ]] || {
    echo 'MODUSTRO_CODEGEN_CLEANUP_OUTPUT_FOLDER_BEFORE_GENERATION must be true or false' >&2; exit 2;
}
[[ "$MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY" == true ||
   "$MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY" == false ]] || {
    echo 'MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY must be true or false' >&2; exit 2;
}
locPython="${ALGITES_PYTHON_EXECUTABLE:-python3}"
command -v "$locPython" >/dev/null 2>&1 || { echo "Missing Python: $locPython" >&2; exit 2; }
# Unique UUID isolates generated sources, schema mappings and Maven staging.
locBootstrapRunId="$("$locPython" -c 'import uuid; print(uuid.uuid4())')"
# Self-hosting generator artifacts may explicitly require a clean first pass.
if [[ "$locAction" != --plan-only && "$locAction" != --upload-prepared &&
      "$locRequireFresh" == true &&
      "$MODUSTRO_CODEGEN_CLEANUP_OUTPUT_FOLDER_BEFORE_GENERATION" != true ]]; then
    echo 'Configured self-hosting bootstrap requires cleanup=true' >&2
    exit 2
fi
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
printf 'Bootstrap repository: %s\nBootstrap root: %s\nBootstrap action: %s\nBootstrap run ID: %s\n' "$locRepository" "$locRoot" "$locAction" "$locBootstrapRunId"
# Validate the complete repository bootstrap descriptor before any generator runs or
# generated-source directory is emptied. A missing/invalid descriptor must not
# leave the working tree with deleted generated sources.
locConfigLoader="$locBootstrapDirectory/bootstrap-config.py"
[[ -f "$locConfigLoader" ]] || { echo "Missing bootstrap configuration loader: $locConfigLoader" >&2; exit 2; }
"$locPython" "$locConfigLoader" --repository "$locRepository" > /dev/null

# Upload existing local publications without touching source/generated outputs,
# preparing prerequisites or invoking Gradle. Inspect the entire selected
# dependency-independent publication batch before authentication or upload.
if [[ "$locAction" == --upload-prepared ]]; then
    locVersion="$($locPython - "$locRepository/modustro-source-repository.yml" <<'PY_VERSION'
import sys, yaml
v = yaml.safe_load(open(sys.argv[1], encoding='utf-8'))['Version']
print(str(v['ReleaseLineVersion']) + '.' + str(v['Revision']) +
      ('-SNAPSHOT' if str(v.get('QualifierKind', 'release')).lower() == 'snapshot' else ''))
PY_VERSION
)"
    locVersion="${MODUSTRO_BOOTSTRAP_VERSION:-$locVersion}"
    [[ ! -L "$locRepository/build" ]] || { echo 'Symlinked build root' >&2; exit 2; }
    locUploadRoot="$locRepository/build/run/upload-prepared/$locBootstrapRunId"
    locPythonVersionArgs=()
    if [[ -n "${MODUSTRO_BOOTSTRAP_PYTHON_VERSION:-}" ]]; then
        locPythonVersionArgs=(--python-version "$MODUSTRO_BOOTSTRAP_PYTHON_VERSION")
    fi
    "$locPython" "$locBootstrapDirectory/upload-prepared.py" \
        --repository "$locRepository" --root "$locRoot" \
        --output "$locUploadRoot" --version "$locVersion" \
        "${locPythonVersionArgs[@]}"
    mapfile -d '' -t locPublicationSettings < <("$locPython" "$locConfigLoader" --repository "$locRepository" --nul)
    locMavenTarget="${MODUSTRO_BOOTSTRAP_JAVA_CLOUDSMITH_REPO:-${locPublicationSettings[0]}}"
    locPythonTarget="${MODUSTRO_BOOTSTRAP_PYTHON_CLOUDSMITH_REPO:-${locPublicationSettings[1]}}"
    command -v algites-cloudsmith >/dev/null || { echo 'algites-cloudsmith is required for upload' >&2; exit 2; }
    algites-cloudsmith --session -- bash "$locBootstrapDirectory/upload-cloudsmith.sh" \
        "$locMavenTarget" "$locUploadRoot/packages.tsv" \
        "$locPythonTarget" "$locUploadRoot/python-packages.tsv"
    echo 'Prepared local artifacts uploaded without generation or build.'
    exit 0
fi

# All adapters receive the same, validated root; never compile a larger tree.
locBuild="$locBootstrapDirectory/build.sh"
[[ -f "$locBuild" ]] || { echo "Missing repository build adapter: $locBuild" >&2; exit 2; }
# Freeze the schema dependency graph before any generated-source cleanup.
# The public URL remains the schema identity; Defs Codegen only reads the
# local file recorded for it. This map is scoped to the selected --root and
# reused by both Java and Python Codegen executions in this invocation.
if [[ "$locAction" != --plan-only ]]; then
    [[ ! -L "$locRepository/build" ]] || { echo 'Symlinked build root' >&2; exit 2; }
    locSchemaMap="$locRepository/build/run/schema-locations/$locBootstrapRunId.properties"
    "$locPython" "$locBootstrapDirectory/schema-locations.py" \
        --repository "$locRepository" --root "$locRoot" --output "$locSchemaMap"
    export MODUSTRO_BOOTSTRAP_SCHEMA_LOCATIONS_PROPERTY_FILE="$locSchemaMap"
fi

# Source dependencies are checked before any generator can remove source files.
# --plan-only reports their order and never invokes a prerequisite build.
if [[ "${MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE:-remote}" == source &&
      "${MODUSTRO_BOOTSTRAP_SOURCE_PREREQUISITES_READY:-0}" != 1 ]]; then
    locSourceAction=prepare
    if [[ "$locAction" == --plan-only ]]; then locSourceAction=plan; fi
    "$locPython" "$locBootstrapDirectory/source-dependencies.py" "$locSourceAction" \
        --repository "$locRepository" --root "$locRoot"
fi
if [[ "${MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE:-remote}" == source &&
      -z "${MODUSTRO_BOOTSTRAP_SOURCE_GROUPS:-}" ]]; then
    export MODUSTRO_BOOTSTRAP_SOURCE_GROUPS="$("$locPython" \
        "$locBootstrapDirectory/source-dependencies.py" groups \
        --repository "$locRepository" --root "$locRoot")"
fi
if [[ "$locAction" == --plan-only ]]; then
    bash "$locBuild" "$locAction"
    exit 0
fi

# Source mode exposes the resolved build-time graph to Codegen. Internal
# artifacts selected only by an undeclared CLI option may not be loaded from
# an unrelated old snapshot in the local binary repository.
if [[ "${MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE:-remote}" == source ]]; then
    export MODUSTRO_BOOTSTRAP_PREPARED_ARTIFACTS="$("$locPython" \
        "$locBootstrapDirectory/source-dependencies.py" identifiers \
        --repository "$locRepository" --root "$locRoot")"
fi

# The source dependency resolver can recursively launch another
# pub.tool.General bootstrap to prepare the SDO CLI. Locking the parent
# before that subprocess finishes would deadlock on the same flock file.
# Acquire the repository-wide lock AFTER prerequisite builds, immediately
# before the first cleanup/generator mutation.
[[ ! -L "$locRepository/build" ]] || { echo 'Symlinked build root' >&2; exit 2; }
mkdir -p "$locRepository/build"
command -v flock >/dev/null 2>&1 || { echo 'Missing flock for safe bootstrap locking' >&2; exit 2; }
exec {locBootstrapLockFd}>"$locRepository/build/.bootstrap.lock"
flock -x "$locBootstrapLockFd"

# Remove only this invocation's disposable Python/Java ownership indices.
# Never read or delete another invocation's files; do this while holding
# the repository lock so a later bootstrap cannot race this cleanup.
locCleanupBootstrapInvocation() {
    if [[ -d "$locRepository/build" ]]; then
        find "$locRepository/build" -type d \
            -path "*/bootstrap-invocations/$locBootstrapRunId" -prune \
            -exec rm -rf -- {} +
    fi
}
trap locCleanupBootstrapInvocation EXIT

# Every repository has invocation-scoped generation/packaging ownership.
export MODUSTRO_BOOTSTRAP_RUN_ID="$locBootstrapRunId"
export MODUSTRO_BOOTSTRAP_FRESH_GENERATION=1

# Validate output roots even when cleanup is disabled; never follow symlinks.
"$locPython" "$locBootstrapDirectory/clean_generated.py" list --repository "$locRepository" --root "$locRoot" >/dev/null

# Clean selected *.gen trees once before independent Defs/SDO generators.
# Never clean between their generation stages.
if [[ "$MODUSTRO_CODEGEN_CLEANUP_OUTPUT_FOLDER_BEFORE_GENERATION" == true ]]; then
    "$locPython" "$locBootstrapDirectory/clean_generated.py" clean --repository "$locRepository" --root "$locRoot"
fi
if [[ -f "$locBootstrapDirectory/generate.sh" ]]; then
    bash "$locBootstrapDirectory/generate.sh"
fi
bash "$locBuild" "$locAction"
# Only explicitly configured self-hosting artifacts may promote gen ->
# extgen, and only after all selected compilation/packaging checks passed.
"$locPython" "$locSelfhosting" phase --repository "$locRepository" \
    --root "$locRoot" --phase after-bootstrap
