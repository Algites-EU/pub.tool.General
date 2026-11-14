"""Opt-in native canonical Defs CLI, separate from the historical .old CLI.

This CLI exercises the new schema frontend + validation + source emitter end to
end for the explicitly supported contract subset. Naming catalogs and all
source roots are supplied by a checked-in JSON manifest. No legacy generator
is called, and generated files are only written in owned *.gen roots. The
historical bootstrap remains unchanged until full schema parity is verified.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import io
import os
import re
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
from typing import Any, Mapping
from collections import defaultdict

import yaml

from eu.algites.tool.codegen.common.naming_profiles import (
    resolve_codegen_naming_profiles, with_external_sourcecode_conventions)
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgdEnum_1, AIngSourceInputKind_1,
    AIcgdElementList_1, AIcgdElement_1, AIcgdList_1, AIcgdMap_1,
    AIcgdScalar_1, replace as model_replace)
from eu.algites.tool.codegen.defs.impl.standard.schema_reference_resolver import (
    SchemaReferenceResolver)
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
    AIcDefsCodegenCanonicalPipeline, AIcdDefsCodegenSourceDocument)
from eu.algites.tool.codegen.defs.impl.standard.canonical_source_emitter import (
    AIcdDefsCodegenEmissionName, AIcDefsCodegenCanonicalSourceEmitter)

_KINDS = {'xmldefs': AIngSourceInputKind_1.XMLDEFS,
          'jsondefs': AIngSourceInputKind_1.JSONDEFS,
          'yamldefs': AIngSourceInputKind_1.YAMLDEFS}
_ALLOWED_SUFFIXES = {'xmldefs': '.xsd', 'jsondefs': '.jsondef.schema.json',
                     'yamldefs': '.yamldef.schema.json'}


def _read_document(path: Path) -> Mapping[str, Any]:
    """Read a JSON or YAML mapping, rejecting scalar/sequence configurations."""
    if path.suffix == '.json':
        value = json.loads(path.read_text(encoding='utf-8'))
    else:
        value = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(value, Mapping):
        raise ValueError(f'Expected mapping document in {path}')
    return value


def _selected_file(manifest_file: Path, configured: str) -> Path:
    """Resolve an explicit catalog path without repository-specific defaults."""
    path = Path(configured)
    return (path if path.is_absolute() else manifest_file.parent / path).resolve()


def _inside(root: Path, configured: str, *, generated: bool = False) -> Path:
    """Require a repository-internal, non-symlink destination/source directory."""
    path = (root / configured).absolute()
    if not path.is_relative_to(root) or path.resolve() != path or path.is_symlink():
        raise ValueError(f'Path escapes repository or traverses a symlink: {configured}')
    if generated and not any(part.endswith('.gen') for part in path.relative_to(root).parts):
        raise ValueError(f'Output directory is not a generated-source root: {configured}')
    return path


def _profile(manifest_file: Path, setting: Mapping[str, str]):
    """Resolve one target's Common/Defs profile plus explicit source-code catalog."""
    if 'sdo_file' in setting or 'sdo_id' in setting:
        raise ValueError('SDO naming belongs to the independent SDO Codegen, not Defs Codegen')
    common = _read_document(_selected_file(manifest_file, setting['common_file']))
    defs = _read_document(_selected_file(manifest_file, setting['defs_file']))
    external = _read_document(_selected_file(manifest_file, setting['sourcecode_catalog']))
    profile = resolve_codegen_naming_profiles(common, setting['common_id'],
                                               defs, setting['defs_id'])
    return with_external_sourcecode_conventions(profile, external)


def _documents(repository: Path, inputs: list[dict[str, str]],
               manifest_file: Path, input_naming: Mapping[str, Any]):
    """Read typed source schemas with exact repository-relative provenance."""
    from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import (
        AIcNameConventionCatalog)
    catalogs = {}
    for kind in {entry['kind'].lower() for entry in inputs}:
        setting = input_naming.get(kind)
        if not isinstance(setting, Mapping) or set(setting) != {'catalog', 'profile'}:
            raise ValueError(f'Missing explicit source filename naming catalog/profile for {kind}')
        catalog_file = _selected_file(manifest_file, setting['catalog'])
        catalogs[kind] = (AIcNameConventionCatalog.load(catalog_file), setting['profile'])
    documents = []
    for entry in inputs:
        kind = entry['kind'].lower()
        if kind not in _KINDS:
            raise ValueError(f'Unknown canonical input technology: {kind}')
        filename = entry['path']
        if not filename.endswith(_ALLOWED_SUFFIXES[kind]):
            raise ValueError(f'Unexpected {kind} schema extension: {filename}')
        file = _inside(repository, filename)
        if not file.is_file():
            raise FileNotFoundError(file)
        content = (file.read_text(encoding='utf-8') if kind == 'xmldefs'
                   else _read_document(file))
        catalog, selected = catalogs[kind]
        parsed = catalog.recognize_filename(file.name, {selected})
        if parsed is None or not parsed.variables.get('identifier') or not parsed.variables.get('version'):
            raise ValueError(f'{file}: filename does not match configured {kind} profile '
                             f'{selected!r} with identifier and version')
        variables = parsed.variables
        source_identifier_convention = catalog.identifier_convention(selected, 'file_name_stem')
        root_name = catalog.format(selected, 'type_name', variables,
                                   source_identifier_convention)
        version = variables['version']
        if kind == 'xmldefs':
            declared_version = ET.fromstring(content).attrib.get('x-algites-schema-version')
            if declared_version and str(declared_version) != version:
                raise ValueError(f'{file}: /xs:schema/@x-algites-schema-version {declared_version!r} '
                                 f'does not match filename version {version!r}')
        if isinstance(content, Mapping):
            declared_version = content.get('x-algites-schema-version')
            if declared_version is not None and str(declared_version) != version:
                raise ValueError(f'{file}: #/x-algites-schema-version {declared_version!r} '
                                 f'does not match filename version {version!r}')
        documents.append(AIcdDefsCodegenSourceDocument(_KINDS[kind],
            file.relative_to(repository).as_posix(), content, root_name, version))
    if not documents:
        raise ValueError('At least one input schema is required')
    return tuple(documents)


def _names(declarations, versions: Mapping[str, str], profile, compositions: Mapping[str, str],
           language: str, documents=()) -> dict[str, tuple[str, str]]:
    """Use selected catalog compositions to form exact names for every TYPE."""
    result = {}
    source_versions = {source.resource: source.source_version for source in documents
                       if source.source_version}
    for declaration in declarations:
        enum = isinstance(declaration.structure, AIcgdEnum_1)
        role = 'enum' if enum else 'interface'
        # The filename-profile version has priority over the manifest wildcard
        # for *every* declaration, including embedded synthetic TYPE nodes.
        source_paths = {binding.source_resource
                        for bindings in declaration.source_bindings.values()
                        for binding in bindings}
        selected_versions = {source_versions[path] for path in source_paths
                             if path in source_versions}
        if len(selected_versions) > 1:
            raise ValueError(f'{declaration.identity}: different input filename versions '
                             f'{sorted(selected_versions)} from {sorted(source_paths)}')
        source_version = next(iter(selected_versions), '')
        if source_version and declaration.schema_version and declaration.schema_version != source_version:
            raise ValueError(f'{declaration.identity} ({sorted(source_paths)}): '
                             f'declared schema version {declaration.schema_version!r} '
                             f'does not match filename version {source_version!r}')
        version = (source_version or declaration.schema_version
                   or versions.get(declaration.identity) or versions.get('*'))
        if not version:
            raise ValueError(f'Missing source version and explicit default for {declaration.identity}')
        typename = profile.composed_name(compositions[role], declaration.name, version=str(version))
        module = (profile.composed_name(compositions[role + '_file'], declaration.name,
                                        version=str(version)) if language == 'python' else typename)
        result[declaration.identity] = (typename, module)
    return result




def _existing_contracts(roots: tuple[Path, ...],
                        required_ids: frozenset[str] | None = None) -> dict[str, dict[str, str]]:
    """Find external contracts by schema identity and actual interface inheritance.

    One unified DataObject can declare independent XMLDEFS, JSONDEFS and
    YAMLDEFS identities. Each points to the same canonical read-only contract;
    transient compiled/ABI seed copies cannot override the current source.
    Genuine unrelated source declarations sharing an identity are errors.
    """
    # schema identity -> technology -> fully qualified symbol -> immediate bases
    candidates: dict[str, dict[str, dict[str, frozenset[str]]]] = {}
    origins: dict[tuple[str, str, str], Path] = {}
    if required_ids is not None and not required_ids:
        return {}

    def add_candidate(key_id: str, language: str, symbol: str,
                      parents: frozenset[str], source: Path) -> None:
        """Index only required identities and retain exact collision provenance."""
        if required_ids is not None and key_id not in required_ids:
            return
        group = candidates.setdefault(key_id, {}).setdefault(language, {})
        previous = group.get(symbol)
        if previous is not None and previous != parents:
            original = origins[(key_id, language, symbol)]
            raise ValueError(
                f'Conflicting generated contract definitions for {key_id} ({language}): '
                f'{symbol}; {original}: parents={sorted(previous)}; '
                f'{source}: parents={sorted(parents)}')
        if previous is None:
            group[symbol] = parents
            origins[(key_id, language, symbol)] = source

    java_package = re.compile(r'^package\s+([a-zA-Z0-9_.]+)\s*;', re.M)
    java_type = re.compile(r'\bpublic\s+interface\s+([A-Za-z0-9_]+)\b')

    def schema_keys(content: str, language: str) -> set[str]:
        """Index each format independently on the *same* read-only contract.

        Never compare XML, JSON or YAML IDs, versions or URLs with each other.
        Migrated and transitional annotations of one format are deduplicated;
        the new JSON/XML annotations take precedence over deprecated peers.
        """
        result: set[str] = set()
        if language == 'java':
            annotations = {
                match.group(1): match.group(2)
                for match in re.finditer(
                    r'@(?:[\w.]+\.)?(AIaDataObjectJsonSchema|AIaDataObjectXmlSchema|'
                    r'AIaJsonDataObject|AIaYamlDataObject|AIaXmlDataObject)\s*\(([^)]*)\)',
                    content)}
            xml = (annotations.get('AIaDataObjectXmlSchema') or
                   annotations.get('AIaXmlDataObject'))
            json_meta = (annotations.get('AIaDataObjectJsonSchema') or
                         annotations.get('AIaJsonDataObject'))
            yaml_meta = annotations.get('AIaYamlDataObject')
            url_pattern = r'\bschemaUrl\s*=\s*"(https://[^"\s]+)"'
            id_pattern = r'\bschemaId\s*=\s*"([^"\s]+)"'
            xml_name = r'\bnamespaceLocalName\s*=\s*"([^"]+)"'
            xml_namespace = r'\bnamespace\s*=\s*"([^"]*)"'
            xml_kind = r'\bdefinitionKind\s*=\s*[\w.]+\.TYPE\b'
        else:
            annotations = {
                match.group(1): match.group(2)
                for match in re.finditer(
                    r'__(xml_schema|json_schema|xml_data_object|json_data_object|'
                    r'yaml_data_object)__\s*=\s*AIa\w+\s*\(([^)]*)\)',
                    content)}
            xml = annotations.get('xml_schema') or annotations.get('xml_data_object')
            json_meta = annotations.get('json_schema') or annotations.get('json_data_object')
            yaml_meta = annotations.get('yaml_data_object')
            url_pattern = r"\bschema_url\s*=\s*['\"](https://[^'\"\s]+)['\"]"
            id_pattern = r"\bschema_id\s*=\s*['\"]([^'\"\s]+)['\"]"
            xml_name = r"\bnamespace_local_name\s*=\s*['\"]([^'\"]+)['\"]"
            xml_namespace = r"\bnamespace\s*=\s*['\"]([^'\"]*)['\"]"
            xml_kind = r'\bdefinition_kind\s*=\s*[\w.]+\.TYPE\b'
        if xml and re.search(xml_kind, xml):
            name, namespace = re.search(xml_name, xml), re.search(xml_namespace, xml)
            if name and namespace:
                result.add('{' + namespace.group(1) + '}' + name.group(1))
        for metadata in (json_meta, yaml_meta):
            if not metadata:
                continue
            name, location = re.search(id_pattern, metadata), re.search(url_pattern, metadata)
            if name and location and '#' not in name.group(1):
                result.add(location.group(1))
        return result

    def python_declaration(content: str, module: str) -> tuple[str, frozenset[str]] | None:
        """Extract an annotated class and its imported parent symbols using AST."""
        tree = ast.parse(content)
        imports: dict[str, str] = {}
        for statement in tree.body:
            if isinstance(statement, ast.ImportFrom) and statement.module and not statement.level:
                for alias in statement.names:
                    imports[alias.asname or alias.name] = statement.module + '.' + alias.name
        for declaration in tree.body:
            if not isinstance(declaration, ast.ClassDef):
                continue
            # Format schema annotations belong to the same unified read-only
            # contract as AIaDataObject; all identities are indexed there.
            metadata_slots = {'__xml_schema__', '__json_schema__',
                              '__xml_data_object__', '__json_data_object__',
                              '__yaml_data_object__'}
            if not any(isinstance(item, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id in metadata_slots
                    for target in item.targets) for item in declaration.body):
                continue
            # The external parent is a Defs *read-only* contract. Writable SDO
            # contracts repeat the same __data_object__ metadata, but expose
            # mutations and must never replace the source interface. Recognize
            # that semantic role from the generated class members and parents,
            # rather than from its naming-profile-dependent class prefix.
            if (any(isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and
                    (item.name.startswith('set') or item.name.startswith('_unset'))
                    for item in declaration.body) or
                    (ast.get_docstring(declaration) or '').startswith('Generated mutable contract')):
                continue
            bases: set[str] = set()
            for base in declaration.bases:
                if isinstance(base, ast.Name):
                    bases.add(imports.get(base.id, module + '.' + base.id))
                elif isinstance(base, ast.Attribute):
                    # Handle a module-qualified parent without assuming class prefixes.
                    parts = []
                    node = base
                    while isinstance(node, ast.Attribute):
                        parts.append(node.attr)
                        node = node.value
                    if isinstance(node, ast.Name):
                        bases.add('.'.join((imports.get(node.id, node.id), *reversed(parts))))
            if any('.smartdataobject.' in parent for parent in bases):
                continue
            return declaration.name, frozenset(bases)
        return None

    def java_bases(content: str, match: re.Match[str], package: str) -> frozenset[str]:
        """Resolve source parents as binary .class parents using Java imports."""
        header = content[match.end():content.find('{', match.end())]
        inheritance = re.search(r'\bextends\s+(.+)', header, flags=re.S)
        if not inheritance:
            return frozenset()
        imports = {
            name.rsplit('.', 1)[-1]: name
            for name in re.findall(r'^\s*import\s+(?!static\b)([\w.]+)\s*;',
                                   content, flags=re.M)
        }
        # The common contract can have parameterized parents. Remove generic
        # arguments at arbitrary nesting depth before splitting interface names.
        depth = 0
        flat = []
        for character in inheritance.group(1):
            if character == '<':
                depth += 1
            elif character == '>':
                depth -= 1
            elif depth == 0:
                flat.append(character)
        if depth != 0:
            raise ValueError(f'Malformed generic interface parents for {package}.{match.group(1)}')
        return frozenset(
            name if '.' in name else imports.get(name, package + '.' + name)
            for part in ''.join(flat).split(',')
            if (name := part.strip().split()[0])
        )

    from ._class_contracts import read_class_contracts

    def indexable_files(root: Path) -> dict[str, list[Path]]:
        """Scan a dependency root without entering previous bootstrap workspaces.

        A source checkout can contain arbitrarily many historic setuptools
        ``build/lib`` trees under ``build/run/bootstrap/<run-id>``. They are
        *not* declared dependencies and must never affect contract selection,
        even when the checkout has no current source for a requested identity.
        Explicitly unpacked JAR/wheel roots still work: their importable files
        are directly below the selected root, not in a nested ``build`` tree.
        """
        excluded = {'.git', '.gradle', '.tox', '.venv', '__pycache__',
                    'build', 'dist', 'target', 'node_modules'}
        found: dict[str, list[Path]] = {'.class': [], '.java': [], '.py': []}
        for folder, children, names in os.walk(root, topdown=True, followlinks=False):
            directory = Path(folder)
            children[:] = [name for name in sorted(children)
                           if name not in excluded and not (directory / name).is_symlink()]
            for name in sorted(names):
                file = directory / name
                if file.suffix in found and file.is_file() and not file.is_symlink():
                    found[file.suffix].append(file)
        return found

    for root in roots:
        discovered = indexable_files(root)
        for file in discovered['.class']:
            for key_id, symbol, parents in read_class_contracts(file):
                add_candidate(key_id, 'java', symbol, parents, file)
        for branch, extension in (('java.gen', '.java'), ('python.gen', '.py')):
            for file in discovered[extension]:
                relative_parts = file.relative_to(root).parts
                # An extracted wheel may put modules directly under eu/ or
                # inside a standard installation wrapper. A source checkout's
                # arbitrary src/product/python/eu subtree is NOT a wheel.
                published_python_module = (branch == 'python.gen' and (
                    relative_parts[:2] == ('eu', 'algites') or
                    any(relative_parts[index + 1:index + 3] == ('eu', 'algites')
                        for index, piece in enumerate(relative_parts)
                        if piece in {'site-packages', 'purelib', 'platlib'})))
                if (not file.is_file() or file.is_symlink() or file.stat().st_size > 2_000_000 or
                        (branch not in file.parts and not published_python_module) or
                        any(piece in {'.git', '__pycache__'} for piece in relative_parts)):
                    continue
                content = file.read_text(encoding='utf-8')
                if branch == 'java.gen':
                    pack, typ = java_package.search(content), java_type.search(content)
                    format_annotations = ('AIaDataObjectJsonSchema', 'AIaDataObjectXmlSchema',
                                          'AIaJsonDataObject', 'AIaYamlDataObject',
                                          'AIaXmlDataObject')
                    if (not (pack and typ) or not any(
                            re.search(r'@(?:[\w.]+\.)?' + name + r'\s*\(', content)
                            for name in format_annotations)):
                        continue
                    # Writable SDO interfaces repeat the read-only metadata but
                    # must never supersede the generated Defs parent. Match
                    # semantic API members, not technology-specific name prefixes.
                    interface_header_end = content.find('{', typ.end())
                    if interface_header_end < 0:
                        continue
                    if ('AIiSmartDataObject' in content[typ.end():interface_header_end] or
                            re.search(r'\b(?:set[A-Z]\w*|_unset\w*)\s*\(',
                                      content[interface_header_end + 1:])):
                        continue
                    keys = schema_keys(content, 'java')
                    if not keys:
                        continue
                    package = pack.group(1)
                    symbol = package + '.' + typ.group(1)
                    parents = java_bases(content, typ, package)
                    language = 'java'
                else:
                    keys = schema_keys(content, 'python')
                    if not keys:
                        continue
                    source_path = next((parent for parent in file.parents
                                        if parent.name == 'python.gen'), None)
                    if source_path is None:
                        # Distributions may include a site-packages wrapper.
                        module = '.'.join(relative_parts[relative_parts.index('eu'):])
                        module = module.removesuffix('.py')
                    else:
                        module = '.'.join(file.relative_to(source_path).with_suffix('').parts)
                    declaration = python_declaration(content, module)
                    if declaration is None:
                        continue
                    symbol = module + '.' + declaration[0]
                    parents = declaration[1]
                    language = 'python'
                for key_id in keys:
                    add_candidate(key_id, language, symbol, parents, file)

    def unique_most_derived(key_id: str, language: str,
                            group: dict[str, frozenset[str]]) -> str:
        """Select the unique source interface, ignoring stale packaging copies.

        Source checkout scanning excludes historic build and staging trees.
        When a separate compiled/ABI dependency is explicitly selected along
        with live ``src/product/*.gen`` sources, the live source prevails for
        its identity. Real source-to-source ambiguities remain errors, and
        standalone unpacked distributions remain supported.
        """
        # Staging ABI seeds (*.extgen), compiled copies, and wheel build/lib
        # may still expose obsolete per-format interfaces. They are not peers
        # of newly regenerated product contracts. Prefer the real product
        # source *for this same identity and language*, independent of format.
        source_component = 'java.gen' if language == 'java' else 'python.gen'
        live_present = any(
            source_component in origins[(key_id, language, symbol)].parts
            for symbol in group)
        if live_present:
            group = {
                symbol: bases for symbol, bases in group.items()
                if source_component in origins[(key_id, language, symbol)].parts
                or not (any(part.endswith('.extgen') for part in
                            origins[(key_id, language, symbol)].parts)
                        or any(pair == ('build', 'lib') for pair in zip(
                            origins[(key_id, language, symbol)].parts,
                            origins[(key_id, language, symbol)].parts[1:]))
                        or origins[(key_id, language, symbol)].suffix == '.class')
            }

        def ancestors(symbol: str) -> set[str]:
            found: set[str] = set()
            pending = list(group[symbol])
            while pending:
                parent = pending.pop()
                if parent == symbol or parent in found:
                    continue
                found.add(parent)
                pending.extend(group.get(parent, ()))
            return found
        choices = [symbol for symbol in group if all(
            symbol == other or other in ancestors(symbol) for other in group)]
        if len(choices) != 1:
            raise ValueError('Ambiguous existing generated contract '
                             f'{key_id} ({language}): unrelated candidates '
                             + ', '.join(f'{symbol} [{origins[(key_id, language, symbol)]}]'
                                         for symbol in sorted(group)))
        return choices[0]

    result: dict[str, dict[str, str]] = {}
    for key_id, languages in candidates.items():
        # Indexing declared checkouts must not diagnose unrelated contracts.
        # A neighboring Security artifact may legitimately contain different
        # projections of its own XSD types; Defs is not compiling that artifact.
        if required_ids is not None and key_id not in required_ids:
            continue
        selected: dict[str, str] = {}
        if 'java' in languages:
            selected['java'] = unique_most_derived(key_id, 'java', languages['java'])
        if 'python' in languages:
            symbol = unique_most_derived(key_id, 'python', languages['python'])
            selected['python_module'], selected['python_type'] = symbol.rsplit('.', 1)
        result[key_id] = selected
    return result


def _required_external_contract_ids(
        documents: tuple[AIcdDefsCodegenSourceDocument, ...]) -> frozenset[str]:
    """Find only schema identities actually used as external API dependencies.

    XML imports are document dependencies, not implicit inheritance from every
    type they declare.  Resolve imported QName references in XSD type/base
    attributes; unrelated contracts in a sibling checkout must not block a
    separate generation batch.  JSON/YAML inheritance is explicit via $ref.
    """
    required: set[str] = set()
    qname_attributes = ('base', 'type', 'ref', 'itemType', 'memberTypes',
                        'substitutionGroup')
    for source in documents:
        if source.kind in (AIngSourceInputKind_1.JSONDEFS,
                           AIngSourceInputKind_1.YAMLDEFS):
            schema = source.content
            refs = list(schema.get('x-algites-defscodegen-extends', ()))
            refs.extend(entry['$ref'] for entry in schema.get('allOf', ())
                        if isinstance(entry, Mapping) and '$ref' in entry)
            for ref in refs:
                if isinstance(ref, str) and ref.startswith('https://'):
                    required.add(ref.partition('#')[0])
            continue
        if source.kind is not AIngSourceInputKind_1.XMLDEFS:
            continue
        text = source.content
        namespaces = {prefix: uri for _, (prefix, uri) in
                      ET.iterparse(io.BytesIO(text.encode('utf-8')),
                                   events=('start-ns',))}
        root = ET.fromstring(text)
        imported = {child.get('namespace', '') for child in root
                    if child.tag == '{http://www.w3.org/2001/XMLSchema}import'}
        for element in root.iter():
            for attribute in qname_attributes:
                for value in element.get(attribute, '').split():
                    if ':' not in value:
                        continue
                    prefix, local = value.split(':', 1)
                    namespace = namespaces.get(prefix)
                    if namespace in imported and local:
                        required.add('{' + namespace + '}' + local)
    return frozenset(required)


def _external_parents(manifest: Mapping[str, Any], manifest_file: Path,
                      documents: tuple[AIcdDefsCodegenSourceDocument, ...]
                      ) -> tuple[dict[str, dict[str, str]], frozenset[str]]:
    """Verify remote parent schemas and bind them to existing external interfaces."""
    repository = _selected_file(manifest_file, manifest['repository_root'])
    roots = tuple(_selected_file(manifest_file, path) for path in manifest.get('reference_roots', ()))
    source_roots = tuple(root for root in roots if root.is_dir())
    contract_index = _existing_contracts(
        source_roots, _required_external_contract_ids(documents))
    # Explicit manifest bindings may be used with packaged (not checked-out)
    # dependencies. They still require fetching and verifying the source schema.
    for uri, declaration in manifest.get('external_contracts', {}).items():
        if not isinstance(declaration, Mapping):
            raise ValueError('External contract binding must be an object: ' + uri)
        contract_index[uri] = dict(declaration)
    requested: set[str] = set()
    for source in documents:
        if source.kind not in (AIngSourceInputKind_1.JSONDEFS, AIngSourceInputKind_1.YAMLDEFS):
            continue
        schema = source.content
        for reference in schema.get('x-algites-defscodegen-extends', ()):
            requested.add(reference)
        for entry in schema.get('allOf', ()):
            if isinstance(entry, Mapping) and '$ref' in entry:
                requested.add(entry['$ref'])
    resolver = SchemaReferenceResolver(source_roots,
        cache_dir=_selected_file(manifest_file, manifest.get('schema_cache',
            str(Path.home() / '.modustro/cache/defs-schemas'))),
        locations_file=_selected_file(manifest_file, manifest['schema_locations_property_file'])
        if manifest.get('schema_locations_property_file') else None)
    result = {}
    local_ids = {str(source.content.get('$id')) for source in documents
                 if isinstance(source.content, Mapping)}
    for reference in sorted(requested):
        # A root allOf can also refer to a local named definition; that is not
        # an external contract and remains a normal canonical link.
        if reference.startswith('#') or reference in local_ids:
            continue
        document_uri = reference.partition('#')[0]
        if not document_uri.startswith('https://'):
            continue  # canonical linker will diagnose non-HTTPS unresolved refs
        resolver.resolve(reference)
        contract = contract_index.get(document_uri)
        if contract is None or set(contract) != {'java', 'python_module', 'python_type'}:
            raise ValueError('External schema exists but no unambiguous Java/Python '
                             'generated contract is declared: ' + reference)
        result[reference] = contract
    # Resolve imported XML types using the *import's own* targetNamespace and
    # declare only public contracts with verified existing Java/Python bindings.
    # Local imports still need to be present as explicit generation inputs.
    declared_xsd: set[str] = set()
    imported_documents: dict[str, bytes] = {}
    for source in documents:
        if source.kind is not AIngSourceInputKind_1.XMLDEFS:
            continue
        root = ET.fromstring(source.content)
        for child in root:
            if child.tag != '{http://www.w3.org/2001/XMLSchema}import':
                continue
            location = child.get('schemaLocation')
            namespace = child.get('namespace', '')
            if not location:
                raise ValueError('XSD import requires schemaLocation in ' + source.resource)
            if location.startswith('https://'):
                imported = resolver.resolve(location, namespace=namespace).content
                document_uri = location.partition('#')[0]
            else:
                if '://' in location or Path(location).is_absolute():
                    raise ValueError('Unsupported XSD import location: ' + location)
                target = (repository / source.resource).parent / location
                if not target.resolve().is_relative_to(repository.resolve()):
                    raise ValueError('XSD relative import escapes repository: ' + location)
                if not target.is_file():
                    raise FileNotFoundError('Missing local XSD import: ' + str(target))
                imported = target.read_bytes()
                document_uri = ''
            imported_root = ET.fromstring(imported)
            imported_documents[location] = imported
            if imported_root.get('targetNamespace', '') != namespace:
                raise ValueError('XSD imported targetNamespace mismatch: ' + location)
            for declaration in imported_root:
                if declaration.tag not in ('{http://www.w3.org/2001/XMLSchema}complexType',
                                           '{http://www.w3.org/2001/XMLSchema}simpleType'):
                    continue
                name = declaration.get('name')
                if not name:
                    continue
                identity = '{' + namespace + '}' + name if namespace else name
                declared_xsd.add(identity)
                if document_uri and identity in contract_index:
                    contract = contract_index[identity]
                    if set(contract) == {'java', 'python_module', 'python_type'}:
                        result[identity] = contract
    return result, frozenset(declared_xsd), imported_documents

def prepare(manifest_file: Path, *, include_common_context: bool = False):
    """Construct and render all output targets without modifying the repository.

    This is intentionally strict: the manifest provides the original schema
    documents, selected naming catalogs, explicit versions and source outputs.
    Every supported source is validated through the generated JSON contract.
    """
    manifest_file = manifest_file.resolve()
    manifest = _read_document(manifest_file)
    if {'mutable_sdo_java', 'mutable_sdo_python'} & manifest.keys():
        raise ValueError('Defs Codegen produces read-only DataObject contracts only; '
                         'run SDO Codegen separately on generated or manually written interfaces')
    root_value = manifest['repository_root']
    repository = _selected_file(manifest_file, root_value)
    if not repository.is_dir():
        raise ValueError('Repository root does not exist')
    schema = _read_document(_selected_file(manifest_file, manifest['canonical_schema']))
    package = manifest['package_name']
    documents = _documents(repository, manifest['inputs'], manifest_file,
                           manifest.get('input_naming', {}))
    # Carry document-level representation URLs beside the canonical graph.
    # x-algites-schema-id remains the *logical* type ID; the published $id is
    # independent format metadata and must never replace that logical ID.
    schema_urls = {(source.kind, source.resource): source.content['$id']
                   for source in documents
                   if source.kind in (AIngSourceInputKind_1.JSONDEFS,
                                      AIngSourceInputKind_1.YAMLDEFS)
                   and isinstance(source.content, Mapping)
                   and isinstance(source.content.get('$id'), str)
                   and source.content['$id'].startswith('https://')
                   and '#' not in source.content['$id']}
    external, external_xsd_types, external_xsd_documents = _external_parents(
        manifest, manifest_file, documents)
    versions = manifest.get('versions', {})
    outputs = {}
    common_context = {}
    for language in sorted(manifest['profiles']):
        settings = manifest['profiles'][language]
        naming = _profile(manifest_file, settings)
        compiled = AIcDefsCodegenCanonicalPipeline(
            naming, schema, external_xsd_types=external_xsd_types,
            external_xsd_documents=external_xsd_documents).process(
            documents, external_parents=external)
        declarations = AIcDefsCodegenCanonicalSourceEmitter.declarations(compiled.types)
        selected = _names(declarations, versions, naming,
                          manifest['output_compositions'][language], language, documents)
        # This target may carry different (yet semantically equivalent) synthetic
        # identifier spellings than the other language's naming profile.
        names = {node.identity: AIcdDefsCodegenEmissionName(
            selected[node.identity][0] if language == 'java' else f'AIxUnused{index}',
            selected[node.identity][0] if language == 'python' else f'AIxUnused{index}',
            selected[node.identity][1] if language == 'python' else f'aix_unused_{index}')
            for index, node in enumerate(declarations)}
        compositions = manifest['output_compositions'][language]
        if not compositions.get('common_interface') or not compositions.get('common_interface_file'):
            raise ValueError(f'{manifest_file}: missing explicit common interface naming '
                             f'compositions for {language}')
        common_roles = dict(compositions, interface=compositions['common_interface'],
                            interface_file=compositions['common_interface_file'])
        common_selected = _names(declarations, versions, naming, common_roles,
                                 language, documents)
        common_names = {node.identity: AIcdDefsCodegenEmissionName(
            common_selected[node.identity][0] if language == 'java' else f'AIxUnused{index}',
            common_selected[node.identity][0] if language == 'python' else f'AIxUnused{index}',
            common_selected[node.identity][1] if language == 'python' else f'aix_unused_{index}')
            for index, node in enumerate(declarations)}
        # The source dialect no longer has its own public DO interface.
        # Emit its enum/value types separately; unified interfaces come from
        # the common contract merger using the canonical source representation.
        emitter = AIcDefsCodegenCanonicalSourceEmitter(
            naming, names, package, compositions['interface'],
            external_parents=external, schema_urls=schema_urls)
        produced = [item for item in emitter.render(compiled.types) if item.language == language]
        output_root = _inside(repository, manifest['output_dirs'][language], generated=True)
        if include_common_context:
            # Retain the linked, representation-specific canonical graph as the
            # authoritative material for cross-format common contract merging.
            # Never parse generated Java/Python text to recover schema semantics.
            shared_emitter = AIcDefsCodegenCanonicalSourceEmitter(
                naming, common_names, package, external_parents=external,
                schema_urls=schema_urls, common_projection=True)
            shared_files = shared_emitter.render(compiled.types)
            nodes = {node.identity: node for node in declarations}
            for shared in shared_files:
                if shared.language != language:
                    continue
                relative = (output_root / shared.relative_path).relative_to(repository).as_posix()
                common_context[relative] = (nodes[shared.type_identity], nodes,
                                            shared_emitter, compiled.types, language, shared.content)
        for item in produced:
            file = output_root / item.relative_path
            if not file.is_relative_to(output_root):
                raise ValueError('Invalid generated relative path')
            relative = file.relative_to(repository).as_posix()
            if include_common_context and relative not in common_context \
                    and not isinstance(nodes[item.type_identity].structure, AIcgdEnum_1):
                # A schema dialect no longer owns a separate nominal SDO
                # read-only interface: the unified contract is the output.
                continue
            if relative in outputs:
                raise ValueError('Duplicate generated output file: ' + relative)
            outputs[relative] = item.content
    return (repository, outputs, common_context) if include_common_context else (repository, outputs)


def publish(repository: Path, outputs: Mapping[str, str], check: bool = False,
            cleanup_output_folder_before_generation: bool = False) -> list[str]:
    """Publish one isolated transaction per declared artifact with scoped locking.

    The shared batch has already validated every source representation and
    merged common contracts. An artifact's publication lock is acquired only
    around the final ownership check and staging commit, never compilation.
    """
    from eu.algites.tool.codegen.common.workspace import (
        artifact_root, invocation_workspace, publish_sources)
    groups = defaultdict(dict)
    for relative, content in outputs.items():
        destination = _inside(repository, relative, generated=True)
        groups[artifact_root(repository, destination)][destination] = content
    produced = []
    for artifact, contents in sorted(groups.items()):
        with invocation_workspace(repository, artifact, 'defscodegen') as run:
            produced.extend(publish_sources(repository, artifact, 'defscodegen',
                                            contents, run, check=check,
                                            cleanup_output_folder_before_generation=
                                            cleanup_output_folder_before_generation))
    return sorted(path.relative_to(repository).as_posix() for path in produced)



_ENUM_ORIGIN = re.compile(
    r'Generated from canonical definition ([^\n]*?)\. Source: ([^\n]*?)\. Do not edit manually\.')
_ENUM_CANONICAL_IDENTITY = re.compile(r'Canonical identity: ([^;\n]+); version: ([0-9]+)\.')
_ENUM_JAVA_LEGACY_ALTERNATE = re.compile(
    r'(?m)^ \* <p>Equivalent schema identity: (.*?)</p>\n')
_ENUM_PYTHON_LEGACY_ALTERNATE = re.compile(
    r'(?m)\n    Equivalent schema identity: (.*?); version: ([0-9]+)\.(?=\n|""")')
_ENUM_JAVA_ALTERNATE = re.compile(
    r'(?m)^ \* <p>Equivalent enum schema: (.*?) Source: (.*?)</p>\n')
_ENUM_PYTHON_ALTERNATE = re.compile(
    r'(?m)\n    Equivalent enum schema: (.*?) Source: (.*?)(?=\n|""")')
_ENUM_JAVA_SOURCE_CONSTANT = re.compile(
    r'(?m)^\s*public static final String CANONICAL_SOURCE_(?:ID|RESOURCE)\s*=\s*"(?:\\.|[^"\\])*";\s*$')


def _enum_provenance(source: str, *, python: bool) -> list[tuple[str, str]]:
    """Read either canonical-emitter or older schema-backend enum provenance."""
    generated = _ENUM_ORIGIN.search(source)
    older = _ENUM_CANONICAL_IDENTITY.search(source)
    if generated:
        values = [(generated.group(1), generated.group(2))]
    elif older:
        # The canonical emitter has no physical source resource in its ENUM
        # documentation. Never invent one; preserve its exact schema identity.
        values = [(older.group(1) + '/' + older.group(2), '')]
    else:
        return []
    alternate = _ENUM_PYTHON_ALTERNATE if python else _ENUM_JAVA_ALTERNATE
    values.extend(alternate.findall(source))
    if python:
        values.extend((identifier + '/' + version, '')
                      for identifier, version in _ENUM_PYTHON_LEGACY_ALTERNATE.findall(source))
    else:
        default_version = values[0][0].rpartition('/')[2]
        for tag in _ENUM_JAVA_LEGACY_ALTERNATE.findall(source):
            identifier, sep, version = tag.rpartition('; version: ')
            values.append(((identifier if sep else tag) + '/' +
                           (version.rstrip('.') if sep else default_version), ''))
    return list(dict.fromkeys(values))


def _enum_api(source: str, *, python: bool) -> str:
    """Compare executable enum contracts, not representation-specific Javadocs.

    Only Java's canonical SOURCE_ID and SOURCE_RESOURCE fields are excluded:
    these denote the original wire schema rather than the shared enum ABI.
    CANONICAL_SOURCE_VERSION and all enum values/methods stay in the comparison.
    """
    if python:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)) and node.body:
                first = node.body[0]
                if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                        and isinstance(first.value.value, str)):
                    node.body.pop(0)
        return ast.dump(tree, include_attributes=False)
    without_sources = _ENUM_JAVA_SOURCE_CONSTANT.sub('', source)
    without_comments = re.sub(r'/\*.*?\*/', '', without_sources, flags=re.DOTALL)
    return '\n'.join(line.strip() for line in without_comments.splitlines() if line.strip())


def _coalesce_equivalent_enum_sources(existing: str, proposed: str, path: str) -> str:
    """Coalesce format-equivalent enum declarations while retaining all origins.

    Enums are shared named value types across XMLDEFS/JSONDEFS/YAMLDEFS.
    Different descriptions, schema IDs and source locations are expected;
    different code, wire values, public signatures or versions are not.
    The canonical source selected for the compatibility constants is stable
    regardless of input order; all other source identities appear in docs.
    """
    if existing == proposed:
        return existing
    is_java = path.endswith('.java')
    is_python = path.endswith('.py')
    if not ((is_java and 'public enum ' in existing and 'public enum ' in proposed)
            or (is_python and 'class ' in existing and 'class ' in proposed
                and 'Enum' in existing and 'Enum' in proposed)):
        raise ValueError(f'Conflicting Defs outputs at {path}: non-enum declaration collision')
    origins_a = _enum_provenance(existing, python=is_python)
    origins_b = _enum_provenance(proposed, python=is_python)
    origins = sorted(set(origins_a + origins_b), key=lambda x: (x[1], x[0]))
    if not origins_a or not origins_b or _enum_api(existing, python=is_python) != _enum_api(proposed, python=is_python):
        raise ValueError(f'Conflicting Defs enum declarations at {path}: '
                         f'{origins_a or ["missing canonical provenance"]} versus '
                         f'{origins_b or ["missing canonical provenance"]}; '
                         'enum values, version or public API differ')
    versions = {identifier.rpartition('/')[2] for identifier, _ in origins}
    if len(versions) != 1 or not next(iter(versions)).isdigit():
        raise ValueError(f'Conflicting Defs enum schema versions at {path}: {origins}')
    # First choose a stable source regardless of input/manifest ordering.
    primary = origins[0]
    source = existing if origins_a[0] == primary else proposed
    alternate = _ENUM_PYTHON_ALTERNATE if is_python else _ENUM_JAVA_ALTERNATE
    source = alternate.sub('', source)
    source = (_ENUM_PYTHON_LEGACY_ALTERNATE if is_python
              else _ENUM_JAVA_LEGACY_ALTERNATE).sub('', source)
    extras = [item for item in origins if item != primary]
    if not extras:
        return source
    if is_java:
        marker = ' * @author '
        additions = ''.join(
            (f' * <p>Equivalent enum schema: {name} Source: {resource}</p>\n'
             if resource else f' * <p>Equivalent schema identity: '
                              f'{name.rpartition("/")[0]}; version: '
                              f'{name.rpartition("/")[2]}.</p>\n')
            for name, resource in extras)
        if marker in source:
            return source.replace(marker, additions + marker, 1)
        end = source.find(' */')
        if end < 0:
            raise ValueError(f'Missing Java enum Javadoc at {path}')
        return source[:end] + additions + source[end:]
    match = _ENUM_ORIGIN.search(source) or _ENUM_CANONICAL_IDENTITY.search(source)
    if match is None:
        raise ValueError(f'Missing Python enum provenance insertion point at {path}')
    additions = ''.join(
        (f'\n    Equivalent enum schema: {name} Source: {resource}' if resource else
         f'\n    Equivalent schema identity: {name.rpartition("/")[0]}; '
         f'version: {name.rpartition("/")[2]}.') for name, resource in extras)
    return source[:match.end()] + additions + source[match.end():]


def _combine_common_scalar(values):
    """Keep constraints that are valid for *every* source representation.

    The representation-specific method retains its full original facets. A
    common getter may advertise only constraints all representations satisfy.
    """
    if not all(isinstance(item, AIcgdScalar_1) for item in values):
        return values[0]
    first = values[0]
    if any(item.scalar_kind != first.scalar_kind or item.format != first.format
           for item in values[1:]):
        raise ValueError('Conflicting scalar type in common DataObject projection')
    def lower(name):
        bounds = [getattr(item, name) for item in values]
        return min(bounds) if all(x != -1 for x in bounds) else -1
    def upper(name):
        bounds = [getattr(item, name) for item in values]
        return max(bounds) if all(x != -1 for x in bounds) else -1
    def bound(name, minimize):
        bounds = [getattr(item, name) for item in values]
        if not all(x != '' for x in bounds):
            return '', False
        from decimal import Decimal
        winner = min(bounds, key=lambda item: Decimal(item)) if minimize else max(bounds, key=lambda item: Decimal(item))
        return winner, all(getattr(item, name) == winner and getattr(item, 'exclusive_' + name)
                           for item in values)
    minimum, exclusive_minimum = bound('minimum', True)
    maximum, exclusive_maximum = bound('maximum', False)
    return model_replace(first, min_length=lower('min_length'),
                         max_length=upper('max_length'),
                         pattern=first.pattern if all(v.pattern == first.pattern for v in values) else '',
                         minimum=minimum, maximum=maximum,
                         exclusive_minimum=exclusive_minimum,
                         exclusive_maximum=exclusive_maximum,
                         multiple_of=first.multiple_of if all(v.multiple_of == first.multiple_of for v in values) else '')


def _common_member(member, counterparts):
    """Intersect source-neutral metadata without mutating the canonical inputs."""
    values = (member, *counterparts)
    def minimum_bound(attr):
        return min(getattr(value, attr) for value in values)
    def maximum_bound(attr):
        bounds = [getattr(value, attr) for value in values]
        return -1 if -1 in bounds else max(bounds)
    if isinstance(member, AIcgdElement_1) and all(isinstance(v, AIcgdElement_1) for v in values):
        structures = [v.structure for v in values]
        common_structure = _combine_common_scalar(structures)
        return model_replace(member, structure=common_structure,
                             min_item_count=minimum_bound('min_item_count'),
                             max_item_count=maximum_bound('max_item_count'),
                             default_kind=member.default_kind if all(v.default_kind == member.default_kind
                                and v.default_value == member.default_value for v in values) else '',
                             default_value=member.default_value if all(v.default_kind == member.default_kind
                                and v.default_value == member.default_value for v in values) else '',
                             is_empty_allowed=any(v.is_empty_allowed for v in values),
                             xml_wire=next((v.xml_wire for v in values if v.xml_wire is not None), None),
                             key_definitions=member.key_definitions)
    if isinstance(member, AIcgdList_1) and all(isinstance(v, AIcgdList_1) for v in values):
        return model_replace(member, min_item_count=minimum_bound('min_item_count'),
                             max_item_count=maximum_bound('max_item_count'),
                             unique_items=all(v.unique_items for v in values),
                             xml_wire=next((v.xml_wire for v in values if v.xml_wire is not None), None),
                             key_definitions=member.key_definitions)
    # The same public getter can have different internal structure (e.g. XML
    # repeated element versus JSON array). Preserve the first source only for
    # type emission; strip representation metadata from the common projection.
    return member


def _merge_common_contract(path: str, contexts) -> str:
    """Project a single common interface from all available format contracts.

    Source identities and wire metadata remain on the format-specific contracts.
    Every semantic member must have a matching, typed neutral declaration; a
    mismatch is reported with its output path rather than silently discarded.
    Source provenance selects a stable representative for documentation.
    """
    contexts = sorted(contexts, key=lambda context: (
        AIngSourceInputKind_1.XMLDEFS not in context[0].source_bindings,
        context[4], context[5]))
    representations = {}
    for node, *_ in contexts:
        for kind in node.source_bindings:
            if kind in representations and representations[kind] != node:
                raise ValueError(f'{path}: multiple incompatible {kind} representations')
            representations[kind] = node

    # The published URL belongs to each source document, not to the arbitrary
    # common emitter selected for one merged Java/Python type.
    schema_urls = {}
    for context in contexts:
        for key, value in context[2].schema_urls.items():
            previous = schema_urls.setdefault(key, value)
            if previous != value:
                raise ValueError(f'{path}: conflicting published schema URL for {key}')

    def render_shared(node, nodes, emitter, language):
        renderer = emitter.with_source_representations(representations, schema_urls)
        parents = renderer._choice_parents(nodes)
        return (renderer._java_source(node, nodes, parents) if language == 'java'
                else renderer._python_source(node, nodes, parents))

    if len(contexts) == 1:
        node, nodes, emitter, _, language, _ = contexts[0]
        return render_shared(node, nodes, emitter, language)
    # Exclusive alternatives are not objects with a common getter map. Their
    # shared CHOICE interface is deliberately empty; the concrete variants
    # remain format-owned and keep their complete alternative metadata.
    shapes = [context[0].structure for context in contexts]
    if all(isinstance(item, AIcgdElementList_1) and item.composition.name == 'CHOICE'
           for item in shapes):
        node, nodes, emitter, _, language, _ = contexts[0]
        return render_shared(node, nodes, emitter, language)
    entries = []
    for node, nodes, emitter, roots, language, original in contexts:
        structure = node.structure
        if not isinstance(structure, AIcgdElementList_1):
            raise ValueError(f'{path}: common representation merging of non-object types requires '
                             'an explicit compatible canonical structure')
        target = language
        fields = {field[0]: field for field in emitter._fields(node, nodes, target)}
        children = {member.name: member for member in structure.children
                    if isinstance(member, (AIcgdElement_1, AIcgdList_1, AIcgdMap_1))}
        entries.append((node, nodes, emitter, roots, language, fields, children))
    # A representation may specialize the wire format, but it must never
    # introduce a business field missing from the shared semantic contract.
    # In particular do not discard incompatible members or invent Object/Any.
    shared = set.union(*(set(entry[5]) for entry in entries))
    for name in sorted(shared):
        missing = [str(entry[0].origin) for entry in entries if name not in entry[5]]
        if missing:
            raise ValueError(
                f'{path}: semantic field {name!r} is absent in '
                f'{", ".join(missing)}; harmonize the XML/JSON/YAML schemas '
                'before generating a common DataObject contract')
        signatures = {(entry[5][name][1], entry[5][name][3]) for entry in entries}
        if len(signatures) != 1:
            differences = '; '.join(
                f'{entry[0].origin}: {entry[5][name][1]!r}, '
                f'{entry[5][name][3]!r}' for entry in entries)
            raise ValueError(
                f'{path}: incompatible types for semantic field {name!r} '
                f'({differences}); harmonize the XML/JSON/YAML structures, '
                'never drop a getter or substitute Object/Any')
    first = entries[0]
    node, nodes, emitter, roots, language = first[:5]
    children = [(_common_member(member, tuple(entry[6][member.name] for entry in entries[1:]))
                 if member.name in shared else None)
                for member in node.structure.children if hasattr(member, 'name')]
    bindings = {}
    for source in representations.values():
        for kind, values in source.source_bindings.items():
            if kind in bindings:
                raise ValueError(f'{path}: ambiguous source representation {kind}')
            bindings[kind] = values
    projected = model_replace(node, source_bindings=bindings, structure=model_replace(node.structure,
        children=tuple(child for child in children if child is not None)))
    # Preserve the other named declarations as type-resolution dependencies,
    # including synthetic types referenced by retained common getters.
    projected_types = dict(nodes, **{node.identity: projected})
    return render_shared(projected, projected_types, emitter, language)


def _execute_manifests(manifests: list[Path], *, check: bool = False,
                       cleanup_output_folder_before_generation: bool = False) -> int:
    """Internal canonical compilation, never a second public configuration API."""
    if not manifests:
        raise ValueError('No Defs input schemas selected')
    prepared = [prepare(manifest, include_common_context=True) for manifest in manifests]
    repository = prepared[0][0]
    outputs = {}
    common_groups = defaultdict(list)
    for repo, files, common in prepared:
        if repo != repository:
            raise ValueError('All Defs inputs must share one repository root')
        for path, context in common.items():
            common_groups[path].append(context)
        for path, content in files.items():
            if path in common:
                continue
            if path in outputs:
                outputs[path] = _coalesce_equivalent_enum_sources(outputs[path], content, path)
                continue
            outputs[path] = content
    for path, contexts in sorted(common_groups.items()):
        if path in outputs:
            raise ValueError('Source-specific/common output collision: ' + path)
        outputs[path] = _merge_common_contract(path, contexts)
    for path in publish(repository, outputs, check=check,
                        cleanup_output_folder_before_generation=cleanup_output_folder_before_generation):
        print(path)
    return 0


def main(args: list[str] | None = None) -> int:
    """Generate via the standard qualified Defs options and layered settings."""
    from ._standard_cli import execute
    return execute(list(args) if args is not None else __import__('sys').argv[1:])


if __name__ == '__main__':
    raise SystemExit(main())
