from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from eu.algites.lib.naming.convention.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.lib.naming.convention.ain_output_name_kind import AInOutputNameKind
from eu.algites.tool.codegen.defs._schema_loading import load_schema
from eu.algites.tool.codegen.defs.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger
from eu.algites.tool.codegen.defs.aic_generation_names import AIcGenerationNames
from eu.algites.tool.codegen.defs.aic_json_schema_reader import AIcJsonSchemaReader
from eu.algites.tool.codegen.defs.aic_schema_interface_generator import AIcSchemaInterfaceGenerator
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_definition_kind import AInDefinitionKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind


class AIcSchemaObjectBindingsGenerator:
    """Generate repository contracts and implementations in each owning schema package."""

    @dataclass(frozen=True, slots=True)
    class AIcdUnit:
        schema: str
        pointer: str
        name: str
        node: dict
        document: dict

    def generate_repository(self, repository: Path, manifest_file: Path, check: bool = False) -> list[dict[str, str]]:
        """Generate intf/impl outputs, or verify them without modifying any file."""
        repository = Path(os.path.abspath(repository))
        manifest = json.loads(Path(manifest_file).read_text(encoding='utf-8'))
        intf = self._inside(repository, manifest['artifact'])
        impl = self._inside(repository, manifest['implementation_artifact'])
        if intf == impl:
            raise ValueError('Interface and implementation artifacts must differ')
        overrides = {entry['schema'] + '#' + entry.get('pointer', ''): entry for entry in manifest.get('bindings', ())}
        units = []
        for kind, suffix in (('jsondefs', '.jsondef.schema.json'), ('yamldefs', '.yamldef.schema.json')):
            root = intf / 'src/product' / kind
            if not root.is_dir():
                continue
            for source in sorted(root.rglob('*')):
                if not source.is_file() or not source.name.endswith(suffix):
                    continue
                schema = source.relative_to(repository).as_posix()
                document = load_schema(source)
                base = re.sub(r'_[0-9]+$', '', source.name[:-len(suffix)])
                self._collect(document, '', base, schema, document, overrides, units)
        discovered = {unit.schema + '#' + unit.pointer for unit in units}
        for key in overrides:
            if key not in discovered:
                raise ValueError(f'Binding override no longer identifies a schema object: {key}')

        requests, result, pending = {}, [], {}
        reader = AIcJsonSchemaReader()
        generator = AIcSchemaInterfaceGenerator()
        for unit in units:
            source = self._inside(repository, unit.schema)
            kind = 'yamldefs' if '/yamldefs/' in unit.schema else 'jsondefs'
            package = source.parent.relative_to(intf / 'src/product' / kind).as_posix().replace('/', '.')
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*', package):
                raise ValueError(f'Schema must have a legal package path: {unit.schema}')
            projection = deepcopy(unit.node)
            if '$defs' in unit.document:
                projection['$defs'] = unit.document['$defs']
            projection['x-jsondefs-id'] = unit.document.get('$id', unit.schema) + ('#' + unit.pointer if unit.pointer else '')
            projection['x-jsondefs-name'] = unit.name
            for language in manifest['languages']:
                target = AInCodeGenerationTarget(language)
                profile = AIcAlgitesNamingProfiles.python_profile() if target is AInCodeGenerationTarget.PYTHON else AIcAlgitesNamingProfiles.java_profile()
                load = AIcdDefinitionLoadRequest(source,
                    AInDefinitionSourceKind.YAMLDEFS if kind == 'yamldefs' else AInDefinitionSourceKind.JSONDEFS, profile)
                definition = reader.read(projection, load, load.source_kind, 'x-jsondefs-id', 'x-jsondefs-version', 'x-jsondefs-name')
                definition = replace(definition, source_resource=unit.schema + ('#' + unit.pointer if unit.pointer else ''))
                request = AIcdCodeGenerationRequest(definition, target, package, profile)
                preview = generator.generate(request)
                requests.setdefault(language + '#' + preview.contract.relative_path, []).append(request)
                result.append(dict(schema=unit.schema, pointer=unit.pointer, language=language, type=preview.contract.type_name,
                    path=(intf / 'src/product' / (language + '.gen') / preview.contract.relative_path).relative_to(repository).as_posix()))

        for representations in requests.values():
            first = representations[0]
            if len({r.definition.source_kind for r in representations}) != len(representations):
                raise ValueError('Different objects resolve to the same generated type: ' + str([r.definition.source_resource for r in representations]))
            merged = AIcCanonicalDefinitionMerger.merge(r.definition for r in representations)
            pair = generator.generate(replace(first, definition=merged))
            language = first.target.value
            self._add(pending, intf / 'src/product' / (language + '.gen') / pair.contract.relative_path,
                self._qualify_references(pair.contract.source, first, requests, True))
            if pair.implementation is not None:
                self._add(pending, impl / 'src/product' / (language + '.gen') / pair.implementation.relative_path,
                    self._qualify_references(pair.implementation.source, first, requests, False))

        state = repository / 'build/run/schema-bindings/generated-files.json'
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
        parser = argparse.ArgumentParser(description=AIcSchemaObjectBindingsGenerator.__doc__)
        parser.add_argument('repository', type=Path)
        parser.add_argument('manifest', type=Path)
        parser.add_argument('--check', action='store_true')
        parser.add_argument('--json', action='store_true')
        parsed = parser.parse_args(args)
        result = AIcSchemaObjectBindingsGenerator().generate_repository(parsed.repository, parsed.manifest, parsed.check)
        print(json.dumps(result, indent=2) if parsed.json else f'{"Verified" if parsed.check else "Generated"} {len(result)} schema representations.')
        return 0


if __name__ == '__main__':
    raise SystemExit(AIcSchemaObjectBindingsGenerator.main())
