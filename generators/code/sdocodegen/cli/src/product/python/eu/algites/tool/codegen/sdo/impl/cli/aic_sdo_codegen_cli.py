"""Native Python SDO CLI with explicit semantic naming roles and external settings."""
from __future__ import annotations

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
from eu.algites.tool.codegen.common.validation_batch import (
    AIcCodegenValidationBatch, selected_policy, parse_boolean)


import argparse
import ast
import importlib.resources
import os
from pathlib import Path
import sys

from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService
from eu.algites.tool.codegen.common.workspace import (
    artifact_root, invocation_workspace, publish_sources, cleanup_inactive_workspaces)
from ._layered_settings import expand as expand_layered_settings
from ._catalog_sources import expand_naming_catalogs



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


def _main(arguments: list[str]):
    """Generate SDO sources from already expanded native CLI arguments.

    Every qualified option is interpreted directly.  Explicit input classes
    restrict selection rather than adding unwanted transitive contracts.
    """
    from contextlib import ExitStack
    from tempfile import TemporaryDirectory
    from zipfile import ZipFile
    from eu.algites.tool.codegen.common.artifact_resolver import (
        parse_artifacts, resolve_artifacts)

    root = Path('.')
    directories: dict[str, str] = {}
    input_roles: dict[str, str] = {}
    mutable_roles: dict[str, str] = {}
    concrete_roles: dict[str, str] = {}
    naming_sources: list[str] = []
    dependency_paths: list[str] = []
    dependency_artifacts: list[str] = []
    input_classes: list[str] = []
    input_artifacts: list[str] = []
    input_paths: list[str] = []
    method_profile = None
    common_profile = sdo_profile = None
    catalog_kinds: set[str] = set()
    mutable_package = concrete_package = ''
    setter_policy = None
    validation_policy = selected_policy(arguments)
    check = clean = cleanup = False
    for option in arguments:
        if option in {'--check', '--clean-only'}:
            if option == '--check': check = True
            else: clean = True
            continue
        if not option.startswith('--') or '=' not in option:
            raise AIxCodegenValidationException(f'Invalid SDO option: {option}', 'Check the qualified CLI option and the active layered settings. Supply the required value, role and technology and remove conflicting options.')
        key, value = option[2:].split('=', 1)
        name, *qualifiers = key.split(':')
        if (qualifiers == ['java']
                and name in {'technology-sdointf-output-dir',
                             'technology-sdoimpl-output-dir', 'generated-dataobject-method-naming-convention',
                             'common-codegen-naming-convention', 'sdo-codegen-naming-convention',
                             'dointf-naming-convention', 'sdointf-naming-convention',
                             'sdoimpl-naming-convention',
                             'sdo-dependency-artifacts', 'sdo-dependency-paths',
                             'sdo-input-artifacts', 'sdo-input-paths', 'dointf-input-classes'}):
            continue  # The Java SDO CLI consumes the corresponding Java keys.
        if name in {'repository-root', 'sdointf-subpackage', 'sdoclass-subpackage',
                    'setter-inheritance-policy', 'codegen-validate-one-input-at-a-time-only',
                    'cleanup-output-folder-before-generation'} and not qualifiers:
            if name == 'repository-root': root = Path(value).resolve()
            elif name == 'sdointf-subpackage': mutable_package = value
            elif name == 'sdoclass-subpackage': concrete_package = value
            elif name == 'cleanup-output-folder-before-generation':
                if value not in {'true', 'false'}:
                    raise AIxCodegenValidationException(
                        '--cleanup-output-folder-before-generation expects true or false',
                        'Use --cleanup-output-folder-before-generation=true or =false.')
                cleanup = value == 'true' 
            elif name == 'setter-inheritance-policy': setter_policy = value
            else: validation_policy = parse_boolean(value)
        elif name == 'naming-conventions-file' and len(qualifiers) == 1:
            catalog_kinds.add(qualifiers[0])
            naming_sources.append(value)
        elif name in {'technology-sdointf-output-dir',
                      'technology-sdoimpl-output-dir'} and qualifiers == ['python']:
            directories[name] = value
        elif name == 'generated-dataobject-method-naming-convention' and qualifiers == ['python']:
            method_profile = value
        elif name == 'common-codegen-naming-convention' and qualifiers == ['python']:
            common_profile = value
        elif name == 'sdo-codegen-naming-convention' and qualifiers == ['python']:
            sdo_profile = value
        elif name == 'dointf-naming-convention' and qualifiers == ['python']:
            input_roles['common'] = value
        elif name == 'sdointf-naming-convention' and qualifiers == ['python']:
            mutable_roles['common'] = value
        elif name == 'sdoimpl-naming-convention' and qualifiers == ['python']:
            concrete_roles['common'] = value
        elif name == 'sdo-dependency-artifacts' and qualifiers == ['python']:
            dependency_artifacts.extend(part.strip() for part in value.split(';') if part.strip())
        elif name == 'sdo-dependency-paths' and qualifiers == ['python']:
            dependency_paths.extend(part.strip() for part in value.split(';') if part.strip())
        elif name == 'sdo-input-artifacts' and qualifiers == ['python']:
            input_artifacts.extend(part.strip() for part in value.split(';') if part.strip())
        elif name == 'sdo-input-paths' and qualifiers == ['python']:
            input_paths.extend(part.strip() for part in value.split(';') if part.strip())
        elif name == 'dointf-input-classes' and qualifiers == ['python']:
            input_classes = [item.strip() for item in value.split(';') if item.strip()]
        else:
            raise AIxCodegenValidationException(f'Unknown or unqualified Python SDO option: {option}', 'Check the qualified CLI option and the active layered settings. Supply the required value, role and technology and remove conflicting options.')
    if check and cleanup:
        raise AIxCodegenValidationException('--check conflicts with --cleanup-output-folder-before-generation=true',
                                             'Use cleanup during a generating run, not --check.')
    if check and clean:
        raise AIxCodegenValidationException('--check and --clean-only cannot both be used', 'Check the qualified CLI option and the active layered settings. Supply the required value, role and technology and remove conflicting options.')
    # Avoid loading profiles for an optional source root that is absent.
    # Source bootstrap intentionally invokes the CLI only when eligible
    # contracts exist, while direct invocations may use an empty root.
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
    if common_profile is not None or sdo_profile is not None:
        if (not common_profile or not sdo_profile or method_profile is not None
                or not {'codegen_common', 'codegen_sdo'} <= catalog_kinds):
            raise AIxCodegenValidationException(
                'SDO needs Common and SDO naming profiles and both catalog files',
                'Use the paired new naming profile selectors without the legacy method profile.')
        catalog = catalog.with_codegen_naming_profiles(common_profile, sdo_profile, 'sdo')
    elif method_profile:
        catalog = catalog.with_generated_method_profile(method_profile)
    if any('common' not in mapping for mapping in (input_roles, mutable_roles, concrete_roles)):
        raise AIxCodegenValidationException(
            'Select --dointf-naming-convention:python, --sdointf-naming-convention:python and --sdoimpl-naming-convention:python',
            'Supply one schema-neutral naming profile for each SDO input/output role.')
    profiles = [input_roles, mutable_roles, concrete_roles]
    for roles in profiles:
        for role, profile in roles.items():
            try: catalog.profile(profile)
            except KeyError as exc:
                raise AIxCodegenValidationException(f'Missing naming profile {profile!r} for {role}', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.') from exc
    if clean:
        artifact = artifact_root(root, mutable_root)
        if artifact != artifact_root(root, concrete_root):
            raise ValueError('SDO output roots must belong to same artifact')
        with invocation_workspace(root, artifact, 'sdocodegen') as run:
            publish_sources(root, artifact, 'sdocodegen', {}, run,
                            cleanup_output_folder_before_generation=True)
        cleanup_inactive_workspaces(root, artifact, 'sdocodegen')
        return 0
    source_roots: list[Path] = []
    if not clean and not (input_artifacts or input_paths or input_classes):
        raise AIxCodegenValidationException('No Python SDO inputs selected: use --sdo-input-paths:python or --sdo-input-artifacts:python', 'Declare the read-only DataObject sources separately from their dependencies.')
    selected_qualified = set()
    for item in input_classes:
        module, separator, class_name = item.partition(':')
        if not separator or not module or not class_name.isidentifier():
            raise AIxCodegenValidationException(f'Expected module.path:ClassName in --dointf-input-classes:python: {item}', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
        selected_qualified.add((module, class_name))
    if artifact_root(root, mutable_root) != artifact_root(root, concrete_root):
        raise AIxCodegenValidationException('SDO output roots must belong to the same artifact',
            'Invoke SDO independently for each declared artifact.')
    artifact = artifact_root(root, mutable_root)
    with invocation_workspace(root, artifact, 'sdocodegen') as run, ExitStack() as stack:
        # A direct .py selector names exactly one read-only contract module,
        # not every sibling in the enclosing technology source tree.
        direct_source_files: dict[Path, set[Path]] = {}
        unrestricted_source_roots: set[Path] = set()
        def python_module_root(source: Path) -> Path:
            return next((parent for parent in source.parents
                         if parent.name in {'python', 'python.gen'}), source.parent)
        archives = list(resolve_artifacts(parse_artifacts(';'.join(input_artifacts), 'python'), 'python')) if input_artifacts else []
        archives += [(root / value).resolve() for value in input_paths]
        for archive in archives:
            if archive.is_dir():
                source = archive.resolve()
                unrestricted_source_roots.add(source)
                if source not in source_roots: source_roots.append(source)
            elif archive.is_file() and archive.suffix == '.py':
                source = archive.resolve()
                module_root = python_module_root(source)
                direct_source_files.setdefault(module_root, set()).add(source)
                if module_root not in source_roots: source_roots.append(module_root)
            elif not archive.is_file() or archive.suffix not in {'.whl', '.zip'}:
                raise AIxCodegenValidationException(f'Unsupported Python SDO input: {archive}',
                    'Select a Python source directory, .py module, or Python wheel/ZIP archive.')
        for index, archive in enumerate(a for a in archives if a.is_file() and a.suffix in {'.whl', '.zip'}):
            target = run / 'tmp' / f'sdo-wheel-{index}'
            target.mkdir(parents=True)
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
        dependencies = [(root / value).resolve() for value in dependency_paths]
        if dependency_artifacts:
            dependencies += list(resolve_artifacts(parse_artifacts(';'.join(dependency_artifacts), 'python'), 'python'))
        for index, dependency in enumerate(dependencies):
            if not dependency.exists():
                raise FileNotFoundError(f'SDO dependency not found: {dependency}')
            if dependency.is_file():
                target = run / 'tmp' / f'dependency-{index}'
                target.mkdir(parents=True)
                with ZipFile(dependency) as zf:
                    for entry in zf.infolist():
                        relative = Path(entry.filename)
                        if relative.is_absolute() or '..' in relative.parts:
                            raise ValueError(f'Unsafe SDO dependency entry: {entry.filename}')
                        if entry.is_dir() or not entry.filename.endswith('.py'):
                            continue
                        dst = target / relative
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        dst.write_bytes(zf.read(entry))
                dependency = target
            if dependency.is_file() and dependency.suffix == '.py':
                dependency = python_module_root(dependency.resolve())
            absolute = str(dependency)
            if absolute not in sys.path:
                sys.path.insert(0, absolute)
                added.append(absolute)
        results = {}
        validation = AIcCodegenValidationBatch(validation_policy)
        found = set()
        policy_key = 'ALGITES_SDO_CODEGEN_SETTER_INHERITANCE_POLICY'
        previous_policy = os.environ.get(policy_key)
        if setter_policy is not None: os.environ[policy_key] = setter_policy
        try:
            for source_root in source_roots:
                selected = {}
                for source in sorted(source_root.rglob('*.py')):
                    if (source_root not in unrestricted_source_roots
                            and source_root in direct_source_files
                            and source.resolve() not in direct_source_files[source_root]):
                        continue
                    try:
                        # Discover candidates from Python declarations, never
                        # from their module filenames or naming composition.
                        # The service checks their actual DataObject ancestry
                        # after import. A single-class module may be an
                        # unannotated child of a neutral annotated interface.
                        module = ast.parse(source.read_text(encoding='utf-8'), filename=str(source))
                        declarations = [item for item in module.body
                                        if isinstance(item, ast.ClassDef)]
                        if not declarations:
                            continue
                        def declares_metadata(declaration):
                            return any(isinstance(node, (ast.Assign, ast.AnnAssign)) and (
                                any(isinstance(target, ast.Name) and target.id == '__data_object__'
                                    for target in node.targets) if isinstance(node, ast.Assign)
                                else isinstance(node.target, ast.Name)
                                and node.target.id == '__data_object__')
                                for node in declaration.body)
                        annotated = [item.name for item in declarations
                                     if declares_metadata(item)]
                        if len(annotated) > 1:
                            raise AIxCodegenValidationException(
                                f'Multiple DataObject declarations in {source}: {annotated}',
                                'Select one explicit class or split the contracts into separate modules.')
                        if annotated:
                            selected[source.relative_to(source_root)] = annotated[0]
                        elif len(declarations) == 1:
                            selected[source.relative_to(source_root)] = declarations[0].name
                        # Ambiguous multi-class modules without a declaration
                        # require --dointf-input-classes:python. No guess from names.
                    except AIxCodegenValidationException as exc:
                        validation.add(exc, source=str(source))
                    except (SyntaxError, UnicodeError, ValueError) as exc:
                        validation.add(AIxCodegenValidationException(str(exc),
                            'Correct the Python DataObject source declaration.'), source=str(source))
                    validation.finish_input(str(source))
                # Explicit module:Class selectors can name hand-written
                # contracts that do not use the generated filename grammar.
                for module, selected_class in selected_qualified:
                    candidate = Path(*module.split('.')).with_suffix('.py')
                    if (source_root / candidate).is_file():
                        # A syntax error was already reported during the source
                        # discovery pass. Do not abort exhaustive validation by
                        # reparsing that same broken source unguarded.
                        try:
                            declarations = ast.parse((source_root / candidate).read_text(encoding='utf-8'))
                        except (SyntaxError, UnicodeError):
                            continue
                        if any(isinstance(item, ast.ClassDef) and item.name == selected_class
                               for item in declarations.body):
                            selected[candidate] = selected_class
                if selected_qualified:
                    selected = {rel: name for rel, name in selected.items()
                        if ('.'.join(rel.with_suffix('').parts), name) in selected_qualified}
                for rel, name in selected.items():
                    found.add(('.'.join(rel.with_suffix('').parts), name))
                if selected:
                    # Each DataObject source is an independent validation unit
                    # in both modes. Never let one failed contract conceal the
                    # remaining contracts in exhaustive mode.
                    groups = [{relative: type_name} for relative, type_name in selected.items()]
                    for group in groups:
                        try:
                            generated = AIcSdoCodegenService().generate_from_sources(
                                source_root, group, naming=(*profiles, catalog),
                                mutable_subpackage=mutable_package,
                                concrete_subpackage=concrete_package,
                                enabled_roles=set(input_roles) & set(mutable_roles) & set(concrete_roles))
                            results.update({(source_root, key): item for key, item in generated.items()})
                        except AIxCodegenValidationException as exc:
                            validation.add(exc, source=str(source_root / next(iter(group))))
                        except (ValueError, SyntaxError) as exc:
                            validation.add(AIxCodegenValidationException(str(exc),
                                'Correct the invalid Python DataObject contract.'),
                                source=str(source_root / next(iter(group))))
                        validation.finish_input(str(source_root / next(iter(group))))
            missing = selected_qualified - found
            if missing:
                validation.add(AIxCodegenValidationException(
                    f'Explicit Python DataObject contracts not found: {sorted(missing)}',
                    'Verify that each class exists in the selected source roots.'),
                    source=';'.join(str(item) for item in source_roots))
            validation.finish()
            validation.report_non_errors(generator='SDO Codegen (Python)')
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
        contents = {}
        for item in results.values():
            for out_root, generated in ((mutable_root, item.mutable_interface),
                                        (concrete_root, item.implementation)):
                dst = out_root / generated.relative_path
                if dst in contents and contents[dst] != generated.source:
                    raise AIxCodegenValidationException(f'Conflicting SDO output: {dst}',
                        'Select unique SDO naming conventions.')
                contents[dst] = generated.source
        for path in publish_sources(root, artifact, 'sdocodegen', contents,
                                    run, check=check,
                                    cleanup_output_folder_before_generation=cleanup):
            print(path)
    return 0


def main(args=None):
    """Log Python SDO generation for its selected artifact and duration."""
    from eu.algites.tool.codegen.common.run_logging import generation_log
    expanded = _settings(list(args) if args is not None else sys.argv[1:])
    options = {key: value for option in expanded if option.startswith('--') and '=' in option
               for key, value in [option[2:].split('=', 1)]}
    root = Path(options.get('repository-root', '.')).resolve()
    mutable_output = options.get('technology-sdointf-output-dir:python')
    if mutable_output is None:
        return _main(expanded)
    artifact = artifact_root(root, root / mutable_output)
    with generation_log('SDO Codegen', 'python', root, artifact):
        return _main(expanded)


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
