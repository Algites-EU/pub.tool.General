"""Native Python SDO CLI with explicit semantic naming roles and external settings."""
from __future__ import annotations

import argparse
import ast
import importlib.resources
import os
from pathlib import Path
import sys

from eu.algites.lib.naming.convention.impl.algites.aic_name_convention_catalog_1 import AIcNameConventionCatalog_1
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
        raise ValueError(f'Generated SDO output escapes root: {item.relative_path}')
    if check:
        if not output.is_file() or output.read_text(encoding='utf-8') != item.source:
            raise ValueError(f'Missing or outdated generated SDO output: {output}')
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
    """Generate selected mutable and implementation roles from explicit DataObject inputs."""
    arguments = _settings(list(args) if args is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository-root', default='.')
    parser.add_argument('--technology-dointf-input-dir', action='append', default=[])
    parser.add_argument('--technology-sdointf-output-dir', action='append', default=[])
    parser.add_argument('--technology-sdoimpl-output-dir', action='append', default=[])
    parser.add_argument('--input-technology-naming-convention', action='append', default=[])
    parser.add_argument('--output-technology-naming-convention', action='append', default=[])
    parser.add_argument('--naming-conventions-file', action='append', default=[])
    parser.add_argument('--dointf-classpath', action='append', default=[])
    parser.add_argument('--sdointf-subpackage', default='')
    parser.add_argument('--sdoclass-subpackage', default='')
    parser.add_argument('--setter-inheritance-policy', choices=(
        'INHERIT_AS_GENERIC_PARAMETER', 'INHERIT_AS_FIXED_PARAMETER'))
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--clean-only', action='store_true')
    options = parser.parse_args(arguments)
    if options.check and options.clean_only:
        parser.error('--clean-only and --check cannot both be used')
    root = Path(options.repository_root).resolve()

    def directory(values):
        selected = None
        for value in values:
            kind, sep, path = value.partition(':')
            if kind != 'python' or sep != ':' or not path:
                continue
            selected = (root / path).resolve()
        return selected

    source_root = directory(options.technology_dointf_input_dir)
    mutable_root = directory(options.technology_sdointf_output_dir)
    concrete_root = directory(options.technology_sdoimpl_output_dir)
    if mutable_root is None or concrete_root is None:
        parser.error('Python mutable and implementation output directories are required')
    if not options.clean_only and source_root is None:
        parser.error('Python DataObject input directory is required')
    if not options.naming_conventions_file:
        parser.error('At least one --naming-conventions-file is required')
    sources = [value if value.startswith(('classpath:', 'resource:'))
               else str((root / value).resolve()) for value in options.naming_conventions_file]
    with expand_naming_catalogs(sources) as resolved_catalogs:
        catalog = AIcNameConventionCatalog_1.load_many(resolved_catalogs)
    profiles = [{}, {}, {}]
    for value in options.input_technology_naming_convention:
        parts = value.split(':', 2)
        if len(parts) != 3 or parts[0] not in {'java', 'python'} or parts[1] not in _ROLES:
            parser.error(f'Invalid input naming convention: {value}')
        if parts[0] == 'python':
            if not parts[2].startswith('defsintf=') or not parts[2][9:]:
                parser.error(f'Invalid defsintf assignment: {value}')
            profiles[0][parts[1]] = parts[2][9:]
    for value in options.output_technology_naming_convention:
        parts = value.split(':', 2)
        if len(parts) != 3 or parts[0] not in {'java', 'python'} or parts[1] not in _ROLES:
            parser.error(f'Invalid output naming convention: {value}')
        if parts[0] != 'python':
            continue
        for entry in parts[2].split(','):
            key, sep, name = entry.partition('=')
            if sep != '=' or not name or key not in {'sdointf', 'sdoclass'}:
                parser.error(f'Invalid SDO role assignment: {entry}')
            profiles[1 if key == 'sdointf' else 2][parts[1]] = name
    for entry in profiles:
        for role, name in entry.items():
            try:
                catalog.profile(name)
            except KeyError as exc:
                raise ValueError(f'Missing naming convention {name!r} for role {role}') from exc
    if options.clean_only:
        _clean_sdo_outputs(catalog, mutable_root, concrete_root, profiles)
        return 0
    if not source_root.is_dir():
        print(f'SDO Codegen: skipping configured input directory (not found): {source_root}', file=sys.stderr)
        return 0
    selected = {}
    for source in sorted(source_root.rglob('*.py')):
        matches = []
        for role, name in profiles[0].items():
            match = catalog.recognize_filename(source.name, {name})
            if match is not None:
                parsed = catalog.parse(name, 'file_name_stem', source.stem)
                try:
                    class_name = catalog.format(name, 'main_container_name', parsed,
                                                catalog.identifier_convention(name, 'file_name_stem'))
                except (KeyError, ValueError):
                    continue
                matches.append((role, class_name))
        names = {name for _, name in matches}
        if len(names) > 1:
            raise ValueError(f'Ambiguous input DataObject class in {source}: {matches}')
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
            raise ValueError(f'Multiple manually authored DataObject types in {source}: {annotated_classes}')
        if annotated_classes:
            selected[source.relative_to(source_root)] = annotated_classes[0]
    if not selected:
        return 0
    added = []
    for item in options.dointf_classpath:
        for path in item.split(os.pathsep):
            absolute = str((root / path).resolve())
            if absolute not in sys.path:
                sys.path.insert(0, absolute)
                added.append(absolute)
    try:
        policy_key = 'ALGITES_SDO_CODEGEN_SETTER_INHERITANCE_POLICY'
        previous_policy = os.environ.get(policy_key)
        if options.setter_inheritance_policy is not None:
            os.environ[policy_key] = options.setter_inheritance_policy
        try:
            generated = AIcSdoCodegenService().generate_from_sources(
                source_root, selected, naming=(*profiles, catalog),
                mutable_subpackage=options.sdointf_subpackage,
                concrete_subpackage=options.sdoclass_subpackage,
                enabled_roles=set(profiles[0]) & set(profiles[1]) & set(profiles[2]))
        finally:
            if options.setter_inheritance_policy is not None:
                if previous_policy is None:
                    os.environ.pop(policy_key, None)
                else:
                    os.environ[policy_key] = previous_policy
    finally:
        for path in added:
            sys.path.remove(path)
    paths: set[Path] = set()
    for result in generated.values():
        for target in ((mutable_root, result.mutable_interface),
                       (concrete_root, result.implementation)):
            output = (target[0] / target[1].relative_path).resolve()
            if output in paths:
                raise ValueError(f'SDO naming roles generate duplicate output path: {output}')
            paths.add(output)
    if not options.check:
        _clean_sdo_outputs(catalog, mutable_root, concrete_root, profiles)
    for result in generated.values():
        _write(mutable_root, result.mutable_interface, options.check)
        _write(concrete_root, result.implementation, options.check)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
