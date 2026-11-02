"""Native Python SDO CLI with explicit semantic naming roles and external settings."""
from __future__ import annotations

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException

import argparse
import ast
import importlib.resources
import os
from pathlib import Path
import sys

from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService
from ._layered_settings import expand as expand_layered_settings
from ._catalog_sources import expand_naming_catalogs

_ROLES = {'common', 'xmldefs_type', 'xmldefs_element', 'yamldefs', 'jsondefs'}


def _settings(arguments: list[str]) -> list[str]:
    """Resolve packaged, classpath, invocation and CLI configuration layers."""
    return expand_layered_settings(arguments, 'sdocodegen', 'python', 'sdo')


def _write(root: Path, item, check: bool):
    output = (root / item.relative_path).resolve()
    if not output.is_relative_to(root):
        raise AIxCodegenValidationException(f'Generated SDO output escapes root: {item.relative_path}', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
    if check:
        if not output.is_file() or output.read_text(encoding='utf-8') != item.source:
            raise AIxCodegenValidationException(f'Missing or outdated generated SDO output: {output}', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        if not output.is_file() or output.read_text(encoding='utf-8') != item.source:
            output.write_text(item.source, encoding='utf-8')
    print(output)


def _clean_sdo_outputs(catalog, mutable_root: Path, concrete_root: Path,
                       profiles: list[dict[str, str]]) -> None:
    """Clean both output families together when they share a physical root."""
    if mutable_root == concrete_root:
        catalog.clean(mutable_root, set(profiles[1].values()) | set(profiles[2].values()))
    else:
        catalog.clean(mutable_root, set(profiles[1].values()))
        catalog.clean(concrete_root, set(profiles[2].values()))


def main(args=None):
    """Generate SDO sources from selected Python source roots and distribution artifacts.

    Every qualified option is interpreted directly.  Explicit input classes
    restrict selection rather than adding unwanted transitive contracts.
    """
    from contextlib import ExitStack
    from tempfile import TemporaryDirectory
    from zipfile import ZipFile
    from eu.algites.tool.codegen.common.artifact_resolver import (
        parse_artifacts, resolve_artifacts)

    arguments = _settings(list(args) if args is not None else sys.argv[1:])
    root = Path('.')
    directories: dict[str, str] = {}
    input_roles: dict[str, str] = {}
    mutable_roles: dict[str, str] = {}
    concrete_roles: dict[str, str] = {}
    naming_sources: list[str] = []
    classpaths: list[str] = []
    input_classes: list[str] = []
    input_artifacts = ''
    input_paths: list[str] = []
    method_profile = None
    mutable_package = concrete_package = ''
    setter_policy = None
    check = clean = False
    for option in arguments:
        if option in {'--check', '--clean-only'}:
            if option == '--check': check = True
            else: clean = True
            continue
        if not option.startswith('--') or '=' not in option:
            raise AIxCodegenValidationException(f'Invalid SDO option: {option}', 'Check the qualified CLI option and the active layered settings. Supply the required value, role and technology and remove conflicting options.')
        key, value = option[2:].split('=', 1)
        name, *qualifiers = key.split(':')
        if (qualifiers and qualifiers[0] == 'java'
                and name in {'technology-dointf-input-dir', 'technology-sdointf-output-dir',
                             'technology-sdoimpl-output-dir', 'generated-dataobject-method-naming-convention',
                             'input-technology-naming-convention', 'output-technology-naming-convention',
                             'dointf-classpath', 'dointf-input-classes', 'dointf-input-artifacts',
                             'dointf-input-paths'}):
            continue  # The Java SDO CLI consumes the corresponding Java keys.
        if name in {'repository-root', 'sdointf-subpackage', 'sdoclass-subpackage',
                    'setter-inheritance-policy'} and not qualifiers:
            if name == 'repository-root': root = Path(value).resolve()
            elif name == 'sdointf-subpackage': mutable_package = value
            elif name == 'sdoclass-subpackage': concrete_package = value
            else: setter_policy = value
        elif name == 'naming-conventions-file' and len(qualifiers) == 1:
            naming_sources.append(value)
        elif name in {'technology-dointf-input-dir', 'technology-sdointf-output-dir',
                      'technology-sdoimpl-output-dir'} and qualifiers == ['python']:
            directories[name] = value
        elif name == 'generated-dataobject-method-naming-convention' and qualifiers == ['python']:
            method_profile = value
        elif name == 'input-technology-naming-convention' and len(qualifiers) == 3 and qualifiers[0] == 'python' and qualifiers[1] in _ROLES and qualifiers[2] == 'defsintf':
            input_roles[qualifiers[1]] = value
        elif name == 'output-technology-naming-convention' and len(qualifiers) == 3 and qualifiers[0] == 'python' and qualifiers[1] in _ROLES and qualifiers[2] in {'sdointf', 'sdoclass'}:
            (mutable_roles if qualifiers[2] == 'sdointf' else concrete_roles)[qualifiers[1]] = value
        elif name == 'dointf-classpath' and qualifiers == ['python']:
            classpaths.extend(value.split(os.pathsep))
        elif name == 'dointf-input-artifacts' and qualifiers == ['python']:
            input_artifacts = value
        elif name == 'dointf-input-paths' and qualifiers == ['python']:
            input_paths = [part.strip() for part in value.split(';') if part.strip()]
        elif name == 'dointf-input-classes' and qualifiers == ['python']:
            input_classes = [item.strip() for item in value.split(';') if item.strip()]
        else:
            raise AIxCodegenValidationException(f'Unknown or unqualified Python SDO option: {option}', 'Check the qualified CLI option and the active layered settings. Supply the required value, role and technology and remove conflicting options.')
    if check and clean:
        raise AIxCodegenValidationException('--check and --clean-only cannot both be used', 'Check the qualified CLI option and the active layered settings. Supply the required value, role and technology and remove conflicting options.')
    # Avoid loading profiles for an optional source root that is absent.
    # Source bootstrap intentionally invokes the CLI only when eligible
    # contracts exist, while direct invocations may use an empty root.
    source_dir = directories.get('technology-dointf-input-dir')
    if (not clean and source_dir and not input_artifacts and not input_paths
            and not input_classes and not (root / source_dir).is_dir()):
        print(f'SDO Codegen: skipping configured input directory (not found): {(root / source_dir).resolve()}',
              file=sys.stderr)
        return 0
    if not naming_sources:
        raise AIxCodegenValidationException('At least one --naming-conventions-file:<id> is required', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
    if setter_policy is not None and setter_policy not in {'INHERIT_AS_GENERIC_PARAMETER', 'INHERIT_AS_FIXED_PARAMETER'}:
        raise AIxCodegenValidationException('Invalid setter inheritance policy: ' + setter_policy, 'Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.')
    if not {'technology-sdointf-output-dir', 'technology-sdoimpl-output-dir'} <= directories.keys():
        raise AIxCodegenValidationException('Both Python SDO output directories are required', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
    mutable_root = (root / directories['technology-sdointf-output-dir']).resolve()
    concrete_root = (root / directories['technology-sdoimpl-output-dir']).resolve()
    sources = [s if s.startswith(('classpath:', 'resource:')) else str((root / s).resolve())
               for s in naming_sources]
    with expand_naming_catalogs(sources) as paths:
        catalog = AIcNameConventionCatalog.load_many(paths)
    if method_profile:
        catalog = catalog.with_generated_method_profile(method_profile)
    profiles = [input_roles, mutable_roles, concrete_roles]
    for roles in profiles:
        for role, profile in roles.items():
            try: catalog.profile(profile)
            except KeyError as exc:
                raise AIxCodegenValidationException(f'Missing naming profile {profile!r} for {role}', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.') from exc
    if clean:
        _clean_sdo_outputs(catalog, mutable_root, concrete_root, profiles)
        return 0
    source_roots: list[Path] = []
    source_dir = directories.get('technology-dointf-input-dir')
    if source_dir:
        candidate = (root / source_dir).resolve()
        if candidate.is_dir(): source_roots.append(candidate)
        else: print(f'SDO Python: input root does not exist: {candidate}', file=sys.stderr)
    if not source_roots and not input_artifacts and not input_classes and not input_paths:
        if source_dir:
            return 0  # Missing optional source root (same behavior as before).
        raise AIxCodegenValidationException('No Python DataObject inputs selected', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
    selected_qualified = set()
    for item in input_classes:
        module, separator, class_name = item.partition(':')
        if not separator or not module or not class_name.isidentifier():
            raise AIxCodegenValidationException(f'Expected module.path:ClassName in --dointf-input-classes:python: {item}', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
        selected_qualified.add((module, class_name))
    with ExitStack() as stack:
        archives = list(resolve_artifacts(parse_artifacts(input_artifacts, 'python'), 'python')) if input_artifacts else []
        archives += [(root / value).resolve() for value in input_paths]
        for archive in archives:
            if archive.is_dir():
                source_roots.append(archive)
            elif not archive.is_file():
                raise AIxCodegenValidationException(f'Missing Python DataObject input: {archive}', 'Check --dointf-input-paths:python, or prepare the selected wheel before running SDO Codegen.')
        for index, archive in enumerate(a for a in archives if a.is_file()):
            target = Path(stack.enter_context(TemporaryDirectory(prefix=f'sdo-wheel-{index}-')))
            with ZipFile(archive) as zf:
                for entry in zf.infolist():
                    if entry.is_dir() or not entry.filename.endswith('.py'): continue
                    relative = Path(entry.filename)
                    if relative.is_absolute() or '..' in relative.parts:
                        raise AIxCodegenValidationException(f'Invalid path in wheel: {entry.filename}', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
                    output = target / relative
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_bytes(zf.read(entry))
            source_roots.append(target)
        if selected_qualified and not source_roots:
            raise AIxCodegenValidationException('Explicit classes require a selected source root or input artifact', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
        added = []
        for value in classpaths:
            absolute = str((root / value).resolve())
            if absolute not in sys.path:
                sys.path.insert(0, absolute)
                added.append(absolute)
        results = {}
        found = set()
        policy_key = 'ALGITES_SDO_CODEGEN_SETTER_INHERITANCE_POLICY'
        previous_policy = os.environ.get(policy_key)
        if setter_policy is not None: os.environ[policy_key] = setter_policy
        try:
            for source_root in source_roots:
                selected = {}
                for source in sorted(source_root.rglob('*.py')):
                    matches = []
                    for role, name in profiles[0].items():
                        match = catalog.recognize_filename(source.name, {name})
                        if match is not None:
                            parsed = catalog.parse(name, 'file_name_stem', source.stem)
                            try:
                                class_name = catalog.format(name, 'type_name', parsed,
                                                            catalog.identifier_convention(name, 'file_name_stem'))
                            except (KeyError, ValueError):
                                continue
                            matches.append((role, class_name))
                    names = {name for _, name in matches}
                    if len(names) > 1:
                        raise AIxCodegenValidationException(f'Ambiguous input DataObject class in {source}: {matches}', 'Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.')
                    if names and any(role in profiles[1] and role in profiles[2] for role, _ in matches):
                        selected[source.relative_to(source_root)] = next(iter(names))
                        continue
                    # Manually authored contracts do not have to match the Algites filename
                    # grammar. Their explicit metadata and actual marker bases select a role.
                    module = ast.parse(source.read_text(encoding='utf-8'), filename=str(source))
                    annotated_classes = []
                    for declaration in module.body:
                        if not isinstance(declaration, ast.ClassDef):
                            continue
                        if any(isinstance(node, (ast.Assign, ast.AnnAssign)) and (
                                any(isinstance(target, ast.Name) and target.id == '__data_object__'
                                    for target in node.targets) if isinstance(node, ast.Assign)
                                else isinstance(node.target, ast.Name) and node.target.id == '__data_object__')
                                for node in declaration.body):
                            annotated_classes.append(declaration.name)
                    if len(annotated_classes) > 1:
                        raise AIxCodegenValidationException(f'Multiple manually authored DataObject types in {source}: {annotated_classes}', 'Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.')
                    if annotated_classes:
                        selected[source.relative_to(source_root)] = annotated_classes[0]
                # Explicit module:Class selectors can name hand-written
                # contracts that do not use the generated filename grammar.
                for module, selected_class in selected_qualified:
                    candidate = Path(*module.split('.')).with_suffix('.py')
                    if (source_root / candidate).is_file():
                        declarations = ast.parse((source_root / candidate).read_text(encoding='utf-8'))
                        if any(isinstance(item, ast.ClassDef) and item.name == selected_class
                               for item in declarations.body):
                            selected[candidate] = selected_class
                if selected_qualified:
                    selected = {rel: name for rel, name in selected.items()
                        if ('.'.join(rel.with_suffix('').parts), name) in selected_qualified}
                for rel, name in selected.items():
                    found.add(('.'.join(rel.with_suffix('').parts), name))
                if selected:
                    generated = AIcSdoCodegenService().generate_from_sources(
                        source_root, selected, naming=(*profiles, catalog),
                        mutable_subpackage=mutable_package,
                        concrete_subpackage=concrete_package,
                        enabled_roles=set(input_roles) & set(mutable_roles) & set(concrete_roles))
                    results.update({(source_root, key): item for key, item in generated.items()})
            missing = selected_qualified - found
            if missing:
                raise AIxCodegenValidationException(f'Explicit Python DataObject contracts not found: {sorted(missing)}', 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')
        finally:
            if setter_policy is not None:
                if previous_policy is None: os.environ.pop(policy_key, None)
                else: os.environ[policy_key] = previous_policy
            for path in added:
                sys.path.remove(path)
        if not results:
            if input_artifacts or input_paths:
                raise AIxCodegenValidationException('No eligible DataObject contracts in selected input artifacts', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
            return 0
        outputs: set[Path] = set()
        for item in results.values():
            for out_root, generated in ((mutable_root, item.mutable_interface),
                                        (concrete_root, item.implementation)):
                path = (out_root / generated.relative_path).resolve()
                if path in outputs:
                    raise AIxCodegenValidationException(f'Conflicting generated SDO path: {path}', 'Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.')
                outputs.add(path)
        if not check:
            _clean_sdo_outputs(catalog, mutable_root, concrete_root, profiles)
        for item in results.values():
            _write(mutable_root, item.mutable_interface, check)
            _write(concrete_root, item.implementation, check)
    return 0


if __name__ == '__main__':
    # Library callers keep original exception types. Only the process boundary
    # translates expected input errors to readable diagnostics and exit code 2.
    from eu.algites.tool.codegen.common.diagnostics import report_exception
    try:
        raise SystemExit(main())
    except Exception as failure:
        if report_exception(failure, generator='SDO Codegen (Python)'):
            raise SystemExit(2) from None
        raise
