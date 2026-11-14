#!/usr/bin/env bash
# Rename handwritten Defs canonical-model Java classes while preserving Git history.
# Run this in the ORIGINAL checkout BEFORE overlaying the renamed checkpoint.
set -euo pipefail
if ! command -v git >/dev/null 2>&1; then
    echo 'ERROR: git is required' >&2
    exit 2
fi
root=$(git rev-parse --show-toplevel) || {
    echo 'ERROR: run this inside the pub.tool.General Git checkout' >&2
    exit 2
}
cd "$root"
dir=generators/code/defscodegen/impl/src/product/java/eu/algites/tool/codegen/defs/impl/standard/model
names=(
    Bridge Element ElementList Enum EnumValue KeyDefinition List Map Scalar
    SourceBinding SourceBindings StructureNormalizer Type XmlWireName
)
from=()
to=()
for suffix in "${names[@]}"; do
    from+=("$dir/AIcSdoCanonical${suffix}.java")
    to+=("$dir/AIcDefsCanonical${suffix}.java")
done
from+=("$dir/AIiSdoCanonicalStructure.java")
to+=("$dir/AIiDefsCanonicalStructure.java")
# Validate every move before changing the index to avoid partial migration.
for i in "${!from[@]}"; do
    if [[ -e ${from[i]} && -e ${to[i]} ]]; then
        printf 'ERROR: both source and target exist: %s / %s\n' "${from[i]}" "${to[i]}" >&2
        exit 3
    fi
    if [[ ! -e ${from[i]} && ! -e ${to[i]} ]]; then
        printf 'ERROR: neither source nor target exists: %s / %s\n' "${from[i]}" "${to[i]}" >&2
        exit 3
    fi
done
moved=0
for i in "${!from[@]}"; do
    if [[ -e ${from[i]} ]]; then
        git mv -- "${from[i]}" "${to[i]}"
        ((moved+=1))
    else
        printf 'Already renamed: %s\n' "${to[i]}"
    fi
done
printf 'Renamed %d of %d Java sources. Update and stage their callers from the new checkpoint.\n' "$moved" "${#from[@]}"
