#!/usr/bin/env bash
# Move the R21 Defs/SDO Codegen Java and Python source APIs into the legacy .old namespaces.
# Generated java.gen/python.gen trees and schema identities MUST NOT be edited here.
set -euo pipefail

usage() {
    printf 'Usage: %s [--dry-run|--apply]\n' "$0" >&2
    exit 2
}
mode="${1:---dry-run}"
[[ "$mode" == '--dry-run' || "$mode" == '--apply' ]] || usage
[[ $# -le 1 ]] || usage
repo="$(git rev-parse --show-toplevel)"
cd "$repo"
[[ -d generators/code/defscodegen && -d generators/code/sdocodegen ]] || {
    echo 'ERROR: Run in a pub.tool.General Git checkout.' >&2; exit 2;
}

count=0
for family in 'defscodegen:defs' 'sdocodegen:sdo'; do
    artifact="${family%%:*}"
    namespace="${family#*:}"
    for component in intf impl cli; do
        for scope in product develop; do
            for language in java python; do
                package_root="generators/code/$artifact/$component/src/$scope/$language/eu/algites/tool/codegen/$namespace"
                [[ -d "$package_root" ]] || continue
                shopt -s nullglob
                for child in "$package_root"/* "$package_root"/.[!.]* "$package_root"/..?*; do
                    [[ -e "$child" ]] || continue
                    [[ "${child##*/}" == old ]] && continue
                    # Some trees contain only namespace package parents; never move untracked files.
                    git ls-files -- "$child" | grep -q . || continue
                    target="$package_root/old/${child##*/}"
                    if [[ "$mode" == '--dry-run' ]]; then
                        printf 'git mv %q %q\n' "$child" "$target"
                    else
                        mkdir -p "$package_root/old"
                        git mv "$child" "$target"
                    fi
                    count=$((count + 1))
                done
                shopt -u nullglob
            done
        done
    done
done

# Configuration defaults are classpath resources in the generator's own namespace.
# Their physical locations must move together with the Java/Python package.
for family in 'defscodegen:defs' 'sdocodegen:sdo'; do
    artifact="${family%%:*}"
    namespace="${family#*:}"
    conf="generators/code/$artifact/intf/src/product/config/eu/algites/tool/codegen/$namespace"
    [[ -d "$conf" ]] || continue
    shopt -s nullglob
    for child in "$conf"/*; do
        [[ -e "$child" ]] || continue
        [[ "${child##*/}" == old ]] && continue
        git ls-files -- "$child" | grep -q . || continue
        target="$conf/old/${child##*/}"
        if [[ "$mode" == '--dry-run' ]]; then
            printf 'git mv %q %q\n' "$child" "$target"
        else
            mkdir -p "$conf/old"
            git mv "$child" "$target"
        fi
        count=$((count + 1))
    done
    shopt -u nullglob
done

# A package-relative Java resource used via AIcScalarGeneration.class.getResourceAsStream().
resource='generators/code/defscodegen/impl/src/product/resources/eu/algites/tool/codegen/defs/impl/standard/schema-python-runtime.py'
if [[ -f "$resource" ]]; then
    dest='generators/code/defscodegen/impl/src/product/resources/eu/algites/tool/codegen/defs/old/impl/standard/schema-python-runtime.py'
    if [[ "$mode" == '--dry-run' ]]; then
        printf 'git mv %q %q\n' "$resource" "$dest"
    else
        mkdir -p "${dest%/*}"
        git mv "$resource" "$dest"
    fi
    count=$((count + 1))
fi

if [[ "$mode" == '--dry-run' ]]; then
    echo "DRY RUN: $count git mv operations; text rewrites not executed."
    exit 0
fi

# Rewrite only manually maintained source/tests, CLI launch paths, and explanatory docs.
# Do NOT modify generated files, schema definitions or schema identity fields.
python3 - "$repo" <<'PY'
from pathlib import Path
import re
import sys

repo = Path(sys.argv[1])
patterns = (
    (re.compile(r'\beu\.algites\.tool\.codegen\.(defs|sdo)(?!\.old\b)'),
     lambda m: f'eu.algites.tool.codegen.{m.group(1)}.old'),
    (re.compile(r'eu/algites/tool/codegen/(defs|sdo)/(?!old/)'),
     lambda m: f'eu/algites/tool/codegen/{m.group(1)}/old/'),
)

paths = []
for artifact in ('defscodegen', 'sdocodegen'):
    for child in (repo / 'generators/code' / artifact).rglob('*'):
        if not child.is_file() or child.suffix not in {'.java', '.py'}:
            continue
        if any(part.endswith('.gen') for part in child.parts):
            continue
        # Only Java/Python source roots; not JSON schema or resource templates.
        if not ('src' in child.parts and ('java' in child.parts or 'python' in child.parts)):
            continue
        if 'resources' in child.parts:
            continue
        paths.append(child)
for child in (repo / 'generators/code').rglob('*.py'):
    if child.name == 'regenerate_sources.py':
        paths.append(child)
for child in (repo / 'devops').rglob('*'):
    if child.is_file() and child.suffix in {'.py', '.gradle', '.kts'}:
        paths.append(child)
for child in (repo / 'generators/code').rglob('*.md'):
    # Dialect vocabulary documents carry published schema URLs, not Java package names.
    if 'dialect' not in child.parts:
        paths.append(child)

changed = 0
for path in dict.fromkeys(paths):
    source = path.read_text(encoding='utf-8')
    result = source
    for pattern, substitution in patterns:
        # Do not rewrite generated output source paths in bootstrap tests.
        # The generated contracts are intentionally left at their existing path.
        if 'bootstrap-tests' in path.parts and path.name == 'test_sdo_binary_contract_discovery.py':
            pass
        result = pattern.sub(substitution, result)
    if path.name in {'test_sdo_binary_contract_discovery.py', 'test_sdo_java_gradle_execution.py'}:
        result = result.replace('defscodegen/intf/src/product/java.gen/eu/algites/tool/codegen/defs/old',
                                'defscodegen/intf/src/product/java.gen/eu/algites/tool/codegen/defs')
        result = result.replace('eu/algites/tool/codegen/defs/old/AIigSchemaFieldBindings_1.java',
                                'eu/algites/tool/codegen/defs/AIigSchemaFieldBindings_1.java')
    # Test schemas and generated schema identities are not package names.
    if path.name == 'test_common_contract_projection.py':
        result = result.replace('https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/old/',
                                'https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/')
    if path.name == 'test_xsd_named_complex_type_linkage.py':
        result = result.replace('eu/algites/tool/codegen/defs/old/schema-field-bindings_1',
                                'eu/algites/tool/codegen/defs/schema-field-bindings_1')
    if path.name == 'test_field_label_generation.py':
        result = result.replace('eu/algites/tool/codegen/defs/old/{name}_1.xsd',
                                'eu/algites/tool/codegen/defs/{name}_1.xsd')
    if path.name == 'test_setter_inheritance_configuration.py':
        result = result.replace("(tmp_path / 'eu/algites/tool/codegen/defs')",
                                "(tmp_path / 'eu/algites/tool/codegen/defs/old')")
        result = result.replace("(directory / 'eu/algites/tool/codegen/defs').mkdir",
                                "(directory / 'eu/algites/tool/codegen/defs/old').mkdir")
        # Idempotency: an already-migrated fixture directory must not become old/old.
        result = result.replace('eu/algites/tool/codegen/defs/old/old',
                                'eu/algites/tool/codegen/defs/old')
    if path.name in {'aic_defs_codegen_cli.py', 'aic_sdo_codegen_cli.py'}:
        result = result.replace("'python', 'defs')", "'python', 'defs.old')")
        result = result.replace("'python', 'sdo')", "'python', 'sdo.old')")
    if path.name in {'AIcDefsCodegenCli.java', 'AIcSdoCodegenCli.java'}:
        result = result.replace('"java", "defs")', '"java", "defs.old")')
        result = result.replace('"java", "sdo")', '"java", "sdo.old")')
    if path.name == '_layered_settings.py':
        result = result.replace("/ package / name", "/ package.replace('.', '/') / name")
        result = result.replace("/ package / override_name", "/ package.replace('.', '/') / override_name")
    if path.name == 'AIcLayeredCodegenSettings.java':
        result = result.replace('aPackage + "/"', 'aPackage.replace(".", "/") + "/"')
    if source != result:
        path.write_text(result, encoding='utf-8')
        changed += 1
print(f'Applied migration: {changed} maintained files rewritten; generated files untouched.')
PY

echo "Applied $count git mv operations. Next: run bootstrap/tests and review 'git diff --find-renames'."
