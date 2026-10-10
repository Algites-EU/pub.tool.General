from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit, unquote

from eu.algites.lib.naming.convention.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.lib.naming.convention.ain_output_name_kind import AInOutputNameKind
from eu.algites.tool.codegen.defs._schema_loading import load_schema
from eu.algites.tool.codegen.defs.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger
from eu.algites.tool.codegen.defs.aic_generation_names import AIcGenerationNames
from eu.algites.tool.codegen.defs.aic_json_schema_reader import AIcJsonSchemaReader
from eu.algites.tool.codegen.defs.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.tool.codegen.defs.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_definition_kind import AInDefinitionKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind


class AIcSchemaContractBindingsGenerator:
    """Generate annotated read-only repository contracts in each schema package."""

    @dataclass(frozen=True, slots=True)
    class AIcdUnit:
        schema: str
        pointer: str
        name: str
        node: dict
        document: dict

    def generate_repository(self, repository: Path, manifest_file: Path, check: bool = False) -> list[dict[str, str]]:
        """Generate interface outputs only, or verify them without modifying files."""
        repository = Path(os.path.abspath(repository))
        manifest = json.loads(Path(manifest_file).read_text(encoding='utf-8'))
        intf = self._inside(repository, manifest['artifact'])
        overrides = {entry['schema'] + '#' + entry.get('pointer', ''): entry for entry in manifest.get('bindings', ())}
        units = []
        for kind, suffix in (('jsondefs', '.jsondef.schema.json'), ('yamldefs', '.yamldef.schema.json'), ('xmldefs', '.xsd')):
            root = intf / 'src/product' / kind
            if not root.is_dir():
                continue
            for source in sorted(root.rglob('*')):
                if not source.is_file() or not source.name.endswith(suffix):
                    continue
                schema = source.relative_to(repository).as_posix()
                document = {} if kind == 'xmldefs' else load_schema(source)
                base = re.sub(r'_[0-9]+$', '', source.name[:-len(suffix)])
                if kind == 'xmldefs':
                    units.append(self.AIcdUnit(schema, '', base, {}, {}))
                else:
                    self._collect(document, '', base, schema, document, overrides, units)
        discovered = {unit.schema + '#' + unit.pointer for unit in units}
        for key in overrides:
            if key not in discovered:
                raise ValueError(f'Binding override no longer identifies a schema object: {key}')

        requests, result, pending = {}, [], {}
        unit_requests = {}
        relations = {}
        unit_index = {(unit.schema, unit.pointer): unit for unit in units}
        reader = AIcJsonSchemaReader()
        generator = AIcSchemaContractInterfaceGenerator()
        for unit in units:
            source = self._inside(repository, unit.schema)
            kind = next(k for k in ('yamldefs', 'jsondefs', 'xmldefs') if '/' + k + '/' in unit.schema)
            package = source.parent.relative_to(intf / 'src/product' / kind).as_posix().replace('/', '.')
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*', package):
                raise ValueError(f'Schema must have a legal package path: {unit.schema}')
            projection = deepcopy(unit.node)
            if kind != 'xmldefs':
                if '$defs' in unit.document:
                    projection['$defs'] = unit.document['$defs']
                projection['x-jsondefs-id'] = unit.document.get('$id', unit.schema) + ('#' + unit.pointer if unit.pointer else '')
                projection['x-jsondefs-name'] = unit.name
            parent_unit = self._parent_unit(unit, unit_index, repository) if kind != 'xmldefs' else None
            for language in manifest['languages']:
                target = AInCodeGenerationTarget(language)
                profile = AIcAlgitesNamingProfiles.python_profile() if target is AInCodeGenerationTarget.PYTHON else AIcAlgitesNamingProfiles.java_profile()
                load = AIcdDefinitionLoadRequest(source,
                    {'yamldefs': AInDefinitionSourceKind.YAMLDEFS, 'jsondefs': AInDefinitionSourceKind.JSONDEFS,
                     'xmldefs': AInDefinitionSourceKind.XMLDEFS}[kind], profile)
                if kind == 'xmldefs':
                    definition = AIcXmlDefsFrontend().load(load)
                else:
                    definition = reader.read(projection, load, load.source_kind, 'x-jsondefs-id', 'x-jsondefs-version', 'x-jsondefs-name')
                definition = replace(definition, source_resource=unit.schema + ('#' + unit.pointer if unit.pointer else ''))
                request = AIcdCodeGenerationRequest(definition, target, package, profile)
                preview = generator.generate(request)
                key = language + '#' + preview.relative_path
                requests.setdefault(key, []).append(request)
                unit_requests[(language, unit.schema, unit.pointer)] = request
                relations.setdefault(key, []).append((language, parent_unit))
                result.append(dict(schema=unit.schema, pointer=unit.pointer, language=language, type=preview.type_name,
                    path=(intf / 'src/product' / (language + '.gen') / preview.relative_path).relative_to(repository).as_posix()))

        for representations in requests.values():
            first = representations[0]
            if len({r.definition.source_kind for r in representations}) != len(representations):
                raise ValueError('Different objects resolve to the same generated type: ' + str([r.definition.source_resource for r in representations]))
            merged = AIcCanonicalDefinitionMerger.merge(r.definition for r in representations)
            parent_relations = relations[first.target.value + '#' + generator.generate(first).relative_path]
            parent_requests = [None if value is None else unit_requests.get(
                (first.target.value, value.schema, value.pointer)) for _, value in parent_relations]
            parent_types = {None if value is None else (value.package_name, generator.generate(value).type_name)
                for value in parent_requests}
            if len(parent_types) > 1:
                raise ValueError('Conflicting inherited contracts across schema representations')
            parent = None
            if parent_requests[0] is not None:
                inherited = parent_requests[0]
                if inherited.definition.kind is not AInDefinitionKind.OBJECT or merged.kind is not AInDefinitionKind.OBJECT:
                    raise ValueError('allOf inheritance must connect object contracts')
                inherited_fields = {field.source_name: field for field in inherited.definition.properties}
                for field in merged.properties:
                    if field.source_name in inherited_fields:
                        parent_field = inherited_fields[field.source_name]
                        if self._field_shape(field) != self._field_shape(parent_field):
                            raise ValueError('Conflicting inherited field: ' + field.source_name)
                merged = replace(merged, properties=tuple(
                    field for field in merged.properties if field.source_name not in inherited_fields))
                parent_type = generator.generate(inherited).type_name
                parent_module = inherited.package_name
                if first.target is AInCodeGenerationTarget.PYTHON:
                    parent_module += '.' + generator.generate(inherited).relative_path.rsplit('/', 1)[-1][:-3]
                parent = (parent_type, parent_module)
            pair = generator.generate(replace(first, definition=merged), parent)
            language = first.target.value
            self._add(pending, intf / 'src/product' / (language + '.gen') / pair.relative_path,
                self._qualify_references(pair.source, first, requests, True))

        state = repository / 'build/run/schema-contract-bindings/generated-files.json'
        previous = json.loads(state.read_text(encoding='utf-8')) if state.is_file() else []
        for old in previous:
            stale = self._inside(repository, old)
            if not any(part.endswith('.gen') for part in stale.parts):
                raise ValueError(f'Invalid ownership state: {old}')
            if stale not in pending and stale.exists():
                if check:
                    raise ValueError(f'Stale generated binding: {old}')
                stale.unlink()
        for path, source in sorted(pending.items()):
            if check:
                if not path.is_file() or path.read_text(encoding='utf-8') != source:
                    raise ValueError(f'Missing or outdated generated binding: {path}')
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.is_file() or path.read_text(encoding='utf-8') != source:
                    path.write_text(source, encoding='utf-8')
        if not check:
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(json.dumps([p.relative_to(repository).as_posix() for p in sorted(pending)], indent=2) + '\n', encoding='utf-8')
        return result

    @staticmethod
    def _field_shape(field):
        return (field.source_name, field.value_kind, field.required, field.nullable,
            field.item_value_kind, field.reference, field.constraints, field.item_constraints)

    @staticmethod
    def _parent_unit(unit, index, repository):
        branches = unit.node.get('allOf', []) 
        if not isinstance(branches, list):
            raise ValueError('allOf must be an array')
        references = [branch['$ref'] for branch in branches if isinstance(branch, dict) and '$ref' in branch]
        if not references:
            return None
        if len(references) != 1:
            raise ValueError('Exactly one allOf parent reference is supported')
        parts = urlsplit(references[0])
        if parts.scheme and parts.scheme != 'file':
            matches = [candidate for candidate in index.values()
                if candidate.document.get('$id') == references[0].split('#', 1)[0]
                and candidate.pointer == ('/' + unquote(parts.fragment)[1:] if parts.fragment.startswith('/') else '')]
            if len(matches) != 1:
                raise ValueError('Unresolved or ambiguous allOf parent: ' + references[0])
            return matches[0]
        if parts.scheme == 'file':
            target = Path(unquote(parts.path))
        else:
            target = (repository / unit.schema).parent / unquote(parts.path) if parts.path else repository / unit.schema
        target = Path(os.path.abspath(target))
        if not target.is_relative_to(repository):
            raise ValueError('allOf parent escapes repository: ' + references[0])
        pointer = unquote(parts.fragment) if parts.fragment.startswith('/') else ''
        parent = index.get((target.relative_to(repository).as_posix(), pointer))
        if parent is None:
            raise ValueError('allOf parent is not an emitted contract: ' + references[0])
        return parent

    @staticmethod
    def _qualify_references(source, request, requests, contract):
        names = AIcGenerationNames()
        for prop in request.definition.properties:
            ref = prop.reference
            if ref is None:
                continue
            resource = ref.identity.split('#', 1)[0]
            owner = request.definition.source_resource.split('#', 1)[0]
            local = None if urlsplit(resource).scheme else Path(os.path.normpath(str(Path(owner).parent / resource))).as_posix()
            candidates = {r.package_name for representations in requests.values() for r in representations
                if r.target is request.target and (r.definition.source_resource == local or r.definition.identity == resource)}
            if len(candidates) != 1:
                raise ValueError(f'Cannot resolve generated reference package: {ref.identity} in {owner}')
            package = next(iter(candidates))
            if package == request.package_name:
                continue
            is_enum = ref.target_kind is AInDefinitionKind.ENUM
            type_kind = AInOutputNameKind.ENUM_TYPE if is_enum else (AInOutputNameKind.INTERFACE_TYPE if contract else AInOutputNameKind.DATA_TYPE)
            file_kind = AInOutputNameKind.ENUM_TYPE_FILE_STEM if is_enum else (AInOutputNameKind.INTERFACE_TYPE_FILE_STEM if contract else AInOutputNameKind.DATA_TYPE_FILE_STEM)
            typ = names.render(ref.logical_name, ref.version, request.naming_profile, type_kind)
            if request.target is AInCodeGenerationTarget.PYTHON:
                file = names.render(ref.logical_name, ref.version, request.naming_profile, file_kind)
                source = source.replace(f'from .{file} import {typ}', f'from {package}.{file} import {typ}')
            else:
                source = re.sub(r'(?<![A-Za-z0-9_$.])' + re.escape(typ) + r'\b', lambda _: package + '.' + typ, source)
        return source

    def _collect(self, node, pointer, name, schema, document, overrides, result):
        if not isinstance(node, dict):
            return
        override = overrides.get(schema + '#' + pointer)
        if override is not None and override.get('common_one_of_fields', False):
            node = self._common_fields(node, document)
        if not pointer or node.get('type') == 'object' or 'properties' in node or 'enum' in node:
            result.append(self.AIcdUnit(schema, pointer, override['name'] if override is not None else name, node, document))
        for keyword in ('properties', '$defs', 'definitions', 'patternProperties'):
            for key, value in node.get(keyword, {}).items():
                token = key.replace('~', '~0').replace('/', '~1')
                separator = '-definition-' if keyword in ('$defs', 'definitions') else ('-pattern-' if keyword == 'patternProperties' else '-')
                self._collect(value, pointer + '/' + keyword + '/' + token, name + separator + self._kebab(key), schema, document, overrides, result)
        for keyword in ('items', 'additionalProperties', 'contains', 'not', 'if', 'then', 'else', 'unevaluatedProperties'):
            self._collect(node.get(keyword), pointer + '/' + keyword, name + '-' + self._kebab(keyword), schema, document, overrides, result)
        for keyword in ('oneOf', 'anyOf', 'allOf', 'prefixItems'):
            for index, value in enumerate(node.get(keyword, ())):
                self._collect(value, pointer + '/' + keyword + '/' + str(index), name + '-' + self._kebab(keyword) + '-' + str(index), schema, document, overrides, result)

    @staticmethod
    def _common_fields(node, document):
        variants = []
        for variant in node['oneOf']:
            ref = variant['$ref']
            if not ref.startswith('#/'):
                raise ValueError('A shared contract requires local object variants')
            resolved = document
            try:
                for token in ref[2:].split('/'):
                    key = token.replace('~1', '/').replace('~0', '~')
                    resolved = resolved[int(key)] if isinstance(resolved, list) else resolved[key]
            except (KeyError, IndexError, TypeError, ValueError) as error:
                raise ValueError(f'Missing union object: {ref}') from error
            if 'properties' not in resolved:
                raise ValueError(f'Missing union object: {ref}')
            variants.append(resolved)
        if not variants:
            raise ValueError('Empty union')
        properties = {}
        for name, value in variants[0]['properties'].items():
            if any(name not in v['properties'] or len(v['properties']) != len(variants[0]['properties']) for v in variants):
                raise ValueError('Union variants no longer have the same fields')
            properties[name] = value if all(value == v['properties'][name] for v in variants) else {'type': 'string'}
        return dict(type='object', properties=properties,
            required=[field for field in variants[0].get('required', ()) if all(field in v.get('required', ()) for v in variants)],
            description='Shared field contract of every value-source variant.')

    @staticmethod
    def _kebab(name):
        return re.sub(r'[^A-Za-z0-9]+', '-', re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', name)).strip('-').lower()

    @staticmethod
    def _inside(repository, relative):
        path = Path(os.path.abspath(repository / relative))
        if Path(relative).is_absolute() or not path.is_relative_to(repository):
            raise ValueError(f'Path escapes repository: {relative}')
        return path

    @staticmethod
    def _add(pending, path, source):
        path = Path(os.path.normpath(path))
        if path in pending:
            raise ValueError(f'Generated type collision: {path}')
        pending[path] = source

    @staticmethod
    def main(args=None):
        """Standalone Python entry point equivalent to the JVM repository generator."""
        import argparse
        parser = argparse.ArgumentParser(description=AIcSchemaContractBindingsGenerator.__doc__)
        parser.add_argument('repository', type=Path)
        parser.add_argument('manifest', type=Path)
        parser.add_argument('--check', action='store_true')
        parser.add_argument('--json', action='store_true')
        parsed = parser.parse_args(args)
        result = AIcSchemaContractBindingsGenerator().generate_repository(parsed.repository, parsed.manifest, parsed.check)
        print(json.dumps(result, indent=2) if parsed.json else f'{"Verified" if parsed.check else "Generated"} {len(result)} schema representations.')
        return 0


if __name__ == '__main__':
    raise SystemExit(AIcSchemaContractBindingsGenerator.main())
