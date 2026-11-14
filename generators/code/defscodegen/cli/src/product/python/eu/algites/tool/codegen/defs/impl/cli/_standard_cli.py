"""Public qualified Defs CLI adaptation for the native canonical pipeline.

The temporary canonical batches are an internal implementation detail. Neither
bootstrap nor callers provide a secondary manifest protocol. All input and
external-dependency selectors are separate and technology-qualified.

@author linhart1
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import ExitStack
import importlib.resources
import json
import os
from pathlib import Path
import re
import shutil
from typing import Mapping
import uuid
from zipfile import ZipFile

import yaml

from eu.algites.tool.codegen.common.artifact_resolver import parse_artifacts, resolve_artifacts
from eu.algites.tool.codegen.common.workspace import (
    artifact_root, invocation_workspace, publish_sources, cleanup_inactive_workspaces)
from ._layered_settings import expand as expand_settings
from eu.algites.tool.codegen.defs.impl.standard._catalog_sources import expand_naming_catalogs

_KINDS = {'xmldefs': '.xsd', 'jsondefs': '.jsondef.schema.json',
          'yamldefs': '.yamldef.schema.json'}
_LIST_OPTIONS = {'defs-input-artifacts', 'defs-input-paths',
                 'defs-dependency-artifacts', 'defs-dependency-paths'}
_TECHNOLOGIES = {'java', 'python'}


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split(';') if part.strip()]


def _effective(arguments: list[str]) -> dict[str, str]:
    """Load documented settings, preserving repeated input/dependency lists."""
    explicit = defaultdict(list)
    remaining = []
    for arg in arguments:
        if arg.startswith('--') and '=' in arg:
            key, value = arg[2:].split('=', 1)
            if key.split(':')[0] in _LIST_OPTIONS:
                explicit[key].extend(_split(value))
                continue
        remaining.append(arg)
    effective = {}
    for arg in expand_settings(remaining, 'defscodegen', 'python', 'defs'):
        if arg in {'--check', '--clean-only', '--allow-unversioned-schemas'}:
            effective[arg[2:]] = 'true'
        else:
            key, value = arg[2:].split('=', 1)
            effective[key] = value
    for key, items in explicit.items():
        if key.partition(':')[2] not in _TECHNOLOGIES:
            raise ValueError(f'Invalid qualified source selector --{key}')
        old = _split(effective.get(key, ''))
        effective[key] = ';'.join([*old, *items])
    supported_unqualified = {'repository-root', 'setter-inheritance-policy',
                             'codegen-validate-one-input-at-a-time-only',
                             'check', 'clean-only', 'allow-unversioned-schemas',
                             'cleanup-output-folder-before-generation',
                             'schema-locations-property-file'}
    supported_qualified = {'naming-conventions-file', 'input-schema-naming-convention',
                           'technology-dointf-output-dir',
                           'dointf-naming-convention',
                           'output-enum-technology-naming-convention',
                           'common-codegen-naming-convention',
                           'defs-codegen-naming-convention', *_LIST_OPTIONS}
    for key in effective:
        name, sep, qualifiers = key.partition(':')
        if not sep and name not in supported_unqualified or sep and name not in supported_qualified:
            raise ValueError(f'Unknown Defs Codegen option --{key}')
        if name in _LIST_OPTIONS and qualifiers not in _TECHNOLOGIES:
            raise ValueError(f'Expected --{name}:java or --{name}:python')
    return effective


def _files_for_path(path: Path, *, source: str):
    """Yield safe schema sources relative to an explicitly selected path."""
    if not path.exists():
        raise FileNotFoundError(f'{source}: {path}')
    if path.is_symlink():
        raise ValueError(f'{source}: symlinked source path {path}')
    files = [path] if path.is_file() else sorted(path.rglob('*'))
    for file in files:
        if not file.is_file():
            continue
        if file.is_symlink():
            raise ValueError(f'{source}: symlinked schema file {file}')
        kind = next((name for name, suffix in _KINDS.items()
                     if file.name.endswith(suffix)), None)
        if kind:
            yield kind, file



def _stage_external_input(path: Path, repository: Path, run: Path,
                          language: str, index: int) -> Path:
    """Materialize an out-of-repository input in this invocation's private tree.

    Canonical source provenance must remain repository-relative. Copy the
    containing technology subtree rather than inventing a new public manifest
    protocol or rewriting source IDs; preserve sibling schema imports. Never
    follow links out of a caller-selected source directory.
    """
    if path.is_relative_to(repository):
        return path
    technology_root = next((parent for parent in (path, *path.parents)
                            if parent.name in _KINDS), None)
    if path.is_file() and technology_root is None:
        raise ValueError(f'External Defs schema must be under an xmldefs, '
                         f'jsondefs or yamldefs directory: {path}')
    source = technology_root or path
    for candidate in [source, *source.rglob('*')]:
        if candidate.is_symlink():
            raise ValueError(f'External Defs source traverses symlink: {candidate}')
    destination = run / 'tmp' / 'external-input' / language / str(index) / source.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, symlinks=True)
    return destination / path.relative_to(source)


def _package(file: Path, kind: str) -> str:
    """Derive the package from the input technology subtree, never its title."""
    parts = file.parts
    positions = [index for index, part in enumerate(parts[:-1]) if part == kind]
    if not positions:
        raise ValueError(f'{file}: no {kind} source directory from which to derive package')
    package = parts[positions[-1] + 1:-1]
    if not package or any(not part.isidentifier() for part in package):
        raise ValueError(f'{file}: invalid package path beneath {kind}: {package}')
    return '.'.join(package)


def _unpack_archive(archive: Path, destination: Path) -> None:
    """Expand selected archives to private staging; reject traversal and links."""
    with ZipFile(archive) as zf:
        for member in zf.infolist():
            relative = Path(member.filename)
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError(f'{archive}: unsafe archive entry {member.filename}')
            if member.is_dir():
                continue
            # ZIP symlinks have a Unix mode in the external attribute.
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError(f'{archive}: symlink entry {member.filename}')
            if member.file_size > 128 * 1024 * 1024:
                raise ValueError(f'{archive}: oversized resource {member.filename}')
            output = destination / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(zf.read(member))


def _canonical_schema(repository: Path) -> Path:
    """Find the published canonical-model schema in the installed Codegen source."""
    suffix = Path('generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/'
                  'tool/codegen/defs/model/canonical-model_1.jsondef.schema.json')
    import sys
    here = Path(__file__).resolve()
    candidates = [repository, *here.parents, *(Path(p).resolve() for p in sys.path if p)]
    for candidate in candidates:
        path = candidate / suffix
        if path.is_file():
            return path
    # Installed source distributions may publish it as a package resource.
    try:
        resource = importlib.resources.files('eu.algites.tool.codegen.defs.model').joinpath(
            'canonical-model_1.jsondef.schema.json')
        if resource.is_file() and isinstance(resource, Path):
            return resource
    except (ModuleNotFoundError, FileNotFoundError, TypeError):
        pass
    raise FileNotFoundError('Missing packaged canonical-model_1.jsondef.schema.json: '
                            'install the Defs model/intf resource dependency')


def _catalogs(options: Mapping[str, str], stack: ExitStack) -> dict[str, Path]:
    sources = {key.partition(':')[2]: value for key, value in options.items()
               if key.startswith('naming-conventions-file:')}
    if not sources:
        raise ValueError('Missing --naming-conventions-file:<entry> catalogs')
    expanded = stack.enter_context(expand_naming_catalogs(sources.values()))
    # Some package roots ship duplicate catalogs: only the exact matching
    # catalogue identifier is selected and conflicting duplicates fail closed.
    result = {}
    for entry, location in sources.items():
        requested = Path(location.partition(':')[2] if location.startswith(('classpath:', 'resource:'))
                         else location).name
        matches = [Path(path) for path in expanded if Path(path).name == requested]
        if not matches:
            raise FileNotFoundError(f'Naming catalog {location!r} selected by {entry}')
        bodies = {p.read_bytes() for p in matches}
        if len(bodies) != 1:
            raise ValueError(f'Ambiguous different naming catalog resources for {location}')
        result[entry] = matches[0]
    return result


def _filename_rule(path: Path, identity: str) -> str:
    """Resolve one XSD-named profile and its file-stem Rule without ambiguous matches."""
    document = yaml.safe_load(path.read_text(encoding='utf-8'))
    where = f'{path}: SourceStructureNameConventions/NameConventions/NameConvention'
    try:
        entries = document['SourceStructureNameConventions']['NameConventions']['NameConvention']
    except (KeyError, TypeError) as exc:
        raise ValueError(f'{where}: expected named profile list') from exc
    if not isinstance(entries, list):
        raise ValueError(f'{where}: expected array')
    found = None
    seen = set()
    for number, entry in enumerate(entries):
        if not isinstance(entry, dict) or not isinstance(entry.get('name'), str) or not entry['name']:
            raise ValueError(f'{where}[{number}]: missing nonempty name')
        name = entry['name']
        if name in seen:
            raise ValueError(f'{where}[{number}]: duplicate name {name!r}')
        seen.add(name)
        if name == identity:
            found = entry
    if found is None:
        raise ValueError(f'{where}: missing naming profile {identity!r}')
    where = f'{where}/{identity}/StructureNaming/Rule'
    try:
        rules = found['StructureNaming']['Rule']
    except (KeyError, TypeError) as exc:
        raise ValueError(f'{where}: expected rules list') from exc
    if not isinstance(rules, list):
        raise ValueError(f'{where}: expected array')
    seen = set()
    stem = None
    for number, rule in enumerate(rules):
        if not isinstance(rule, dict) or not isinstance(rule.get('kind'), str) or not rule['kind']:
            raise ValueError(f'{where}[{number}]: missing nonempty kind')
        kind = rule['kind']
        if kind in seen:
            raise ValueError(f'{where}[{number}]: duplicate kind {kind!r}')
        seen.add(kind)
        if kind == 'file_name_stem':
            stem = rule.get('Value')
    if not isinstance(stem, str) or not stem:
        raise ValueError(f'{where}: missing nonempty file_name_stem for {identity!r}')
    return stem


def _configurations(options: Mapping[str, str], repository: Path, selected: list[tuple[str, Path]],
                    dependencies: list[Path], catalogs: Mapping[str, Path], run: Path):
    languages = {key.split(':')[1] for key in options
                 if key.startswith('technology-dointf-output-dir:')}
    if not languages:
        raise ValueError('Missing --technology-dointf-output-dir:java|python')
    profiles = {}
    compositions = {}
    for lang in sorted(languages):
        for key in (f'common-codegen-naming-convention:{lang}',
                    f'defs-codegen-naming-convention:{lang}',
                    f'dointf-naming-convention:{lang}',
                    f'output-enum-technology-naming-convention:{lang}'):
            if key not in options:
                raise ValueError(f'Missing Defs Codegen naming option --{key}')
        if not ({lang} <= catalogs.keys() and
                ('codegen_common' in catalogs or f'codegen_common_{lang}' in catalogs) and
                ('codegen_defs' in catalogs or f'codegen_defs_{lang}' in catalogs)):
            raise ValueError(f'Missing Defs naming catalogs for {lang}: codegen_common/codegen_defs/{lang}')
        profiles[lang] = {'common_file': str(catalogs.get(f'codegen_common_{lang}', catalogs.get('codegen_common'))),
                          'common_id': options[f'common-codegen-naming-convention:{lang}'],
                          'defs_file': str(catalogs.get(f'codegen_defs_{lang}', catalogs.get('codegen_defs'))),
                          'defs_id': options[f'defs-codegen-naming-convention:{lang}'],
                          'sourcecode_catalog': str(catalogs[lang])}
        # Output composition is selected entirely from catalog data.
        common_id = options[f'dointf-naming-convention:{lang}']
        enum_id = options[f'output-enum-technology-naming-convention:{lang}']
        compositions[lang] = {
            'common_interface': common_id,
            'common_interface_file': _filename_rule(catalogs[lang], common_id),
            'enum': enum_id,
            'enum_file': _filename_rule(catalogs[lang], enum_id)}
    catalog_input = {}
    for kind, _ in selected:
        key = f'input-schema-naming-convention:{kind}'
        if key not in options or kind not in catalogs:
            raise ValueError(f'Missing source naming catalog/profile for {kind}')
        catalog_input[kind] = {'catalog': str(catalogs[kind]), 'profile': options[key]}
    grouped = defaultdict(list)
    for kind, file in selected:
        grouped[(kind, _package(file, kind))].append(
            {'kind': kind, 'path': file.relative_to(repository).as_posix()})
    configurations = []
    for (kind, package), inputs in sorted(grouped.items()):
        group_compositions = {}
        for lang in sorted(languages):
            intf = options[f'dointf-naming-convention:{lang}']
            group_compositions[lang] = {**compositions[lang], 'interface': intf,
                                         'interface_file': _filename_rule(catalogs[lang], intf)}
        configurations.append({
            **({'schema_locations_property_file': str((repository / options['schema-locations-property-file']).resolve())}
               if options.get('schema-locations-property-file') else {}),
            'repository_root': str(repository),
            'inputs': inputs,
            'input_naming': {kind: catalog_input[kind]},
            'canonical_schema': str(_canonical_schema(repository)),
            'profiles': profiles,
            'output_compositions': group_compositions,
            'package_name': package,
            'versions': {},
            'reference_roots': [str(path) for path in dependencies],
            'output_dirs': {lang: options[f'technology-dointf-output-dir:{lang}']
                            for lang in sorted(languages)}
        })
    return configurations


def _execute_effective(options: dict[str, str]) -> int:
    """Execute one already normalized native Defs configuration."""
    from . import canonical_defs_codegen_cli as canonical
    repository = Path(options.get('repository-root', '.')).resolve(strict=True)
    cleanup = options.get('cleanup-output-folder-before-generation', 'false').lower()
    if cleanup not in {'true', 'false'}:
        raise ValueError('--cleanup-output-folder-before-generation must be true or false')
    if options.get('check') == 'true' and cleanup == 'true':
        raise ValueError('--check conflicts with --cleanup-output-folder-before-generation=true')
    if options.get('check') == 'true' and options.get('clean-only') == 'true':
        raise ValueError('--check conflicts with --clean-only')
    languages = {key.split(':')[1] for key in options
                 if key.startswith('technology-dointf-output-dir:')}
    if not languages:
        raise ValueError('No Defs output technology selected')
    roots = [repository / options[f'technology-dointf-output-dir:{lang}']
             for lang in sorted(languages)]
    artifacts = {artifact_root(repository, root) for root in roots}
    if len(artifacts) != 1:
        raise ValueError('One Defs invocation must target one artifact; invoke per artifact')
    artifact = next(iter(artifacts))
    if options.get('clean-only') == 'true':
        with invocation_workspace(repository, artifact, 'defscodegen') as run:
            publish_sources(repository, artifact, 'defscodegen', {}, run,
                            cleanup_output_folder_before_generation=True)
        cleanup_inactive_workspaces(repository, artifact, 'defscodegen')
        return 0
    with invocation_workspace(repository, artifact, 'defscodegen') as run:
        with ExitStack() as stack:
            selected = {}
            dependencies = []
            for role in ('input', 'dependency'):
                for lang in sorted(_TECHNOLOGIES):
                    entries = []
                    path_key = f'defs-{role}-paths:{lang}'
                    artifact_key = f'defs-{role}-artifacts:{lang}'
                    for item in _split(options.get(path_key, '')):
                        entries.append((repository / item).resolve())
                    specified = options.get(artifact_key)
                    if specified:
                        entries.extend(resolve_artifacts(parse_artifacts(specified, lang), lang))
                    for index, path in enumerate(entries):
                        if not path.exists():
                            raise FileNotFoundError(f'--defs-{role} ({lang}): {path}')
                        if path.is_file() and path.suffix in {'.jar', '.whl', '.zip'}:
                            dest = run / 'tmp' / role / lang / str(index)
                            dest.mkdir(parents=True, exist_ok=True)
                            _unpack_archive(path, dest)
                            path = dest
                        if role == 'input':
                            source_root = _stage_external_input(path, repository, run, lang, index)
                            for kind, source in _files_for_path(source_root, source=role):
                                selected[(kind, source.resolve())] = (kind, source.resolve())
                        elif path not in dependencies:
                            dependencies.append(path)
            if not selected and options.get('clean-only') != 'true':
                raise ValueError('No Defs input schemas selected by --defs-input-*')
            catalogs = _catalogs(options, stack)
            configurations = _configurations(options, repository, list(selected.values()),
                                             dependencies, catalogs, run)
            manifest_paths = []
            for index, config in enumerate(configurations):
                path = run / 'tmp' / f'canonical-{index:04}.json'
                path.write_text(json.dumps(config, indent=2), encoding='utf-8')
                manifest_paths.append(path)
            # Only the CLI internally owns these temporary files. They are NOT a
            # bootstrap/API protocol and can change without external callers.
            return canonical._execute_manifests(manifest_paths,
                                                check=options.get('check') == 'true',
                                                cleanup_output_folder_before_generation=cleanup == 'true')


def execute(arguments: list[str]) -> int:
    """Generate and time each output technology for the selected artifact."""
    from contextlib import ExitStack
    from eu.algites.tool.codegen.common.run_logging import generation_log
    options = _effective(arguments)
    repository = Path(options.get('repository-root', '.')).resolve(strict=True)
    languages = sorted(key.split(':')[1] for key in options
                       if key.startswith('technology-dointf-output-dir:'))
    with ExitStack() as timing:
        if languages:
            for language in languages:
                artifact = artifact_root(repository,
                    repository / options[f'technology-dointf-output-dir:{language}'])
                timing.enter_context(generation_log('Defs Codegen', language,
                                                    repository, artifact))
        return _execute_effective(options)
