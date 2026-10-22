from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit, unquote

from eu.algites.lib.naming.convention.impl.algites.aic_algites_naming_profiles_1 import AIcAlgitesNamingProfiles_1
from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from eu.algites.lib.naming.convention.impl.algites.aic_name_convention_catalog_1 import AIcNameConventionCatalog_1
from eu.algites.tool.codegen.defs.impl.standard._schema_loading import load_schema
from eu.algites.tool.codegen.defs.impl.standard.aic_canonical_definition_merger import AIcCanonicalDefinitionMerger
from eu.algites.tool.codegen.defs.impl.standard.aic_generation_names import AIcGenerationNames
from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from eu.algites.tool.codegen.defs.impl.standard.aic_selected_naming_catalog import AIcSelectedNamingCatalog
from eu.algites.tool.codegen.defs.impl.standard.aic_json_schema_reader import AIcJsonSchemaReader
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_element_contract_generator import AIcXmlElementContractGenerator, xml_identifier
from eu.algites.tool.codegen.defs.impl.standard import aic_xml_namespace_contracts as xml_namespaces
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
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
        manifest = json.loads(Path(manifest_file).read_text(encoding='utf-8'))
        return self.generate_manifest(repository, manifest, check)

    def generate_manifest(self, repository: Path, manifest: dict, check: bool = False) -> list[dict[str, str]]:
        """Generate all selected targets from explicit schema roots and YAML naming catalogs."""
        repository = Path(os.path.abspath(repository))
        intf = self._inside(repository, manifest.get('artifact', '.'))
        explicit = 'schema_inputs' in manifest
        configured = 'technology_output_naming_conventions' in manifest
        shared_names = None
        if configured:
            files = []
            for source in manifest.get('naming_convention_files', []):
                files.append(source if source.startswith('resource:') else str(self._inside(repository, source)))
            shared_names = AIcNameConventionCatalog_1.load_many(files)
        output_roots = {t: self._inside(repository, d) for t, d in manifest.get('technology_outputs', {}).items()}
        catalogs = {t: AIcNameConventionCatalog_1.load(self._inside(repository, file))
                    for t, file in manifest.get('technology_naming_profiles', {}).items()}
        target_profiles = {t: AIcNameConventionCatalog_1.load(self._inside(repository, file))
                           for t, file in manifest.get('technology_naming_profiles', {}).items()}
        source_catalogs = {k: AIcNameConventionCatalog_1.load(self._inside(repository, file))
                           for k, file in manifest.get('schema_input_naming_profiles', {}).items()}
        if configured:
            catalogs = {language: shared_names for language in output_roots}
            target_profiles = dict(catalogs)
            source_catalogs = {kind: shared_names for kind in manifest.get('schema_input_naming_conventions', {})}
        if explicit and not configured:
            for technology in output_roots:
                if technology not in catalogs:
                    raise ValueError('Missing target naming catalog: ' + technology)
        # Only paths listed in generator ownership state can be deleted. Filename
        # convention matching is not proof of ownership when profiles are shared.
        state = repository / 'build/run/schema-contract-bindings/generated-files.json'
        previously_recorded = json.loads(state.read_text(encoding='utf-8')) if state.is_file() else []
        if not isinstance(previously_recorded, list) or any(not isinstance(x, str) for x in previously_recorded):
            raise ValueError(f'Invalid generation ownership file: {state}')
        previously_owned = set()
        unrelated_owned = set()
        for old in previously_recorded:
            stale = self._inside(repository, old)
            if not any(part.endswith('.gen') for part in stale.parts):
                raise ValueError(f'Invalid ownership state: {old}')
            if any(stale.is_relative_to(root) for root in output_roots.values()):
                previously_owned.add(stale)
            else:
                unrelated_owned.add(stale)
        if manifest.get('clean_only'):
            for stale in sorted(previously_owned):
                if stale.is_file():
                    stale.unlink()
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(json.dumps([p.relative_to(repository).as_posix()
                for p in sorted(unrelated_owned)], indent=2) + '\n', encoding='utf-8')
            return []
        overrides = {entry['schema'] + '#' + entry.get('pointer', ''): entry for entry in manifest.get('bindings', ())}
        units = []
        source_roots = manifest.get('schema_inputs') or [
            {'kind': kind, 'directory': str(intf / 'src/product' / kind)}
            for kind in ('jsondefs', 'yamldefs', 'xmldefs')]
        root_by_source = {}
        kind_by_source = {}
        for source_input in source_roots:
            kind = source_input['kind']
            suffix = {'jsondefs': '.jsondef.schema.json', 'yamldefs': '.yamldef.schema.json', 'xmldefs': '.xsd'}[kind]
            root = Path(source_input['directory']).resolve() if Path(source_input['directory']).is_absolute() else self._inside(repository, source_input['directory'])
            if not root.is_relative_to(repository):
                raise ValueError('Schema root escapes repository: ' + str(root))
            if kind in source_catalogs and not manifest.get('allow_unversioned_schemas', False):
                required_profile = f'algites-{kind[:-1] if kind != "xmldefs" else "xmldef"}-schema-versioned_1'
            else:
                required_profile = None
            if not root.is_dir():
                continue
            for source in sorted(root.rglob('*')):
                if not source.is_file() or not source.name.endswith(suffix):
                    continue
                schema = source.relative_to(repository).as_posix()
                if schema in root_by_source:
                    raise ValueError('Overlapping schema input roots: ' + schema)
                root_by_source[schema] = root
                kind_by_source[schema] = kind
                if configured and kind not in source_catalogs:
                    continue
                if kind in source_catalogs:
                    loc_profile = manifest.get('schema_input_naming_conventions', {}).get(kind) if configured else None
                    recognized = source_catalogs[kind].recognize_filename(source.name,
                        {loc_profile} if loc_profile else None)
                    if recognized is None:
                        raise ValueError('Schema filename violates input naming profile: ' + schema)
                    if not configured and required_profile is not None and recognized.convention_name != required_profile:
                        raise ValueError('Unversioned schema is not allowed: ' + schema)
                document = {} if kind == 'xmldefs' else load_schema(source)
                base = re.sub(r'_[0-9]+$', '', source.name[:-len(suffix)])
                if kind == 'xmldefs':
                    units.append(self.AIcdUnit(schema, '', base, {}, {}))
                    for name in AIcXmlDefsFrontend().additional_named_type_names(source):
                        units.append(self.AIcdUnit(schema, '@type/' + name, name, {}, {}))
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
            kind = kind_by_source[unit.schema]
            package = source.parent.relative_to(root_by_source[unit.schema]).as_posix().replace('/', '.')
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*', package):
                raise ValueError(f'Schema must have a legal package path: {unit.schema}')
            projection = deepcopy(unit.node)
            if kind != 'xmldefs':
                if '$defs' in unit.document:
                    projection['$defs'] = unit.document['$defs']
                projection['x-jsondefs-id'] = (unit.document.get('x-yamldefs-id') or unit.document.get('x-jsondefs-id') or unit.document.get('$id') or unit.schema) + ('#' + unit.pointer if unit.pointer else '')
                projection['x-jsondefs-name'] = unit.name
            parent_units = self._parent_units(unit, unit_index, repository) if kind != 'xmldefs' else ()
            for language in manifest['languages']:
                target = AInCodeGenerationTarget(language)
                profile = target_profiles.get(language) or (AIcAlgitesNamingProfiles_1.python_profile()
                            if target is AInCodeGenerationTarget.PYTHON else AIcAlgitesNamingProfiles_1.java_profile())
                load = AIcdDefinitionLoadRequest(source,
                    {'yamldefs': AInDefinitionSourceKind.YAMLDEFS, 'jsondefs': AInDefinitionSourceKind.JSONDEFS,
                     'xmldefs': AInDefinitionSourceKind.XMLDEFS}[kind], profile)
                if kind == 'xmldefs':
                    definition = (AIcXmlDefsFrontend().load_named_type(load, unit.pointer[6:])
                                  if unit.pointer.startswith('@type/') else AIcXmlDefsFrontend().load(load))
                else:
                    definition = reader.read(projection, load, load.source_kind, 'x-jsondefs-id', 'x-jsondefs-version', 'x-jsondefs-name')
                definition = replace(definition, source_resource=unit.schema + ('#' + unit.pointer if unit.pointer else ''))
                xml_type_qname = (('{' + AIcXmlDefsFrontend().schema_namespace(load) + '}' + unit.pointer[6:])
                    if unit.pointer.startswith('@type/') else AIcXmlDefsFrontend().root_type_qname(load)) if kind == 'xmldefs' else None
                if xml_type_qname is not None and xml_type_qname.endswith('}__root__'):
                    xml_type_qname = None
                source_role = 'xmldefs_type' if kind == 'xmldefs' else kind
                configured_roles = manifest.get('technology_output_naming_conventions', {}).get(language, {})
                enabled_roles = ([role for role in ('common', source_role) if role in configured_roles]
                                 if configured else [''])
                for role in enabled_roles:
                    selected_id = configured_roles[role] if configured else ''
                    role_profile = profile
                    if configured:
                        entries = {kind: selected_id for kind in (AInDefsNameRole.INTERFACE_TYPE,
                            AInDefsNameRole.INTERFACE_TYPE_FILE_STEM,
                            AInDefsNameRole.DATA_TYPE, AInDefsNameRole.DATA_TYPE_FILE_STEM)}
                        element_id = configured_roles.get('xmldefs_element')
                        if element_id:
                            entries.update({kind: element_id for kind in (AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE,
                                AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE_FILE_STEM)})
                        namespace_id = configured_roles.get('xmldefs_namespace',
                            f'algites-{language}-gen-xml-namespace-intf_1')
                        entries.update({kind: namespace_id for kind in
                            (AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE,
                             AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE_FILE_STEM)})
                        enum_id = manifest.get('technology_enum_output_naming_conventions', {}).get(language, selected_id)
                        entries.update({kind: enum_id for kind in (AInDefsNameRole.ENUM_TYPE,
                            AInDefsNameRole.ENUM_TYPE_FILE_STEM)})
                        role_profile = AIcSelectedNamingCatalog(profile, entries)
                    request = AIcdCodeGenerationRequest(definition, target, package, role_profile,
                        xml_type_qname, selected_id, role)
                    preview = generator.generate(request)
                    key = language + '#' + preview.relative_path
                    requests.setdefault(key, []).append(request)
                    unit_requests[(language, role, unit.schema, unit.pointer)] = request
                    relations.setdefault(key, []).append(parent_units)
                    result.append(dict(schema=unit.schema, pointer=unit.pointer, language=language, type=preview.type_name,
                        path=(output_roots.get(language, intf / 'src/product' / (language + '.gen')) / preview.relative_path).relative_to(repository).as_posix()))

        units_by_resource = {unit.schema + ('#' + unit.pointer if unit.pointer else ''): unit
                             for unit in units}
        # Source-format-specific inheritance must bind to an independently emitted
        # XML type, not the global element or an invented base name.
        xml_type_requests = {}
        for candidate in unit_requests.values():
            if candidate.xml_type_qname is None:
                continue
            key = (candidate.target, candidate.contract_role,
                candidate.package_name if candidate.xml_type_qname.startswith('{}') else '',
                candidate.xml_type_qname)
            previous = xml_type_requests.setdefault(key, candidate)
            if previous.package_name != candidate.package_name:
                raise ValueError(f'Ambiguous XML named type {candidate.xml_type_qname}')
        # Resolve one XML namespace marker per target/namespace across all schema packages.
        # Only XML requests participate; JSON and YAML have no namespace interfaces.
        xml_namespace_owners = {}
        for (language, role, schema, pointer), req in unit_requests.items():
            if kind_by_source[schema] != 'xmldefs' or role == 'common':
                continue
            namespace = req.xml_type_qname[1:].split('}', 1)[0] if req.xml_type_qname else None
            if namespace is not None:
                xml_namespace_owners.setdefault((language, namespace), req)
            for field in req.definition.data_type.properties:
                xml = field.xml_field
                if xml is None or not xml.wildcard_namespace:
                    continue
                explicit_namespace = xml_namespaces.namespace_of_wildcard(xml.wildcard_namespace, xml.namespace)
                if explicit_namespace is not None:
                    xml_namespace_owners.setdefault((language, explicit_namespace), req)
        def namespace_ref(language, namespace):
            owner = xml_namespace_owners.get((language, namespace))
            if owner is None:
                raise ValueError('Missing generated XML namespace contract: ' + namespace)
            name, stem, module = xml_namespaces.namespace_contract(owner, namespace)
            return module + '.' + name if language == 'python' else owner.package_name + '.' + name

        for representations in requests.values():
            first = representations[0]
            common_role = first.contract_role == 'common'
            identities = {(self._common_identity(r.definition, r.package_name,
                          self._canonical_identity(r.definition, r.package_name, units_by_resource))
                          if common_role else self._canonical_identity(r.definition, r.package_name, units_by_resource))
                          for r in representations}
            if common_role:
                explicit = {item for item in identities if item[0] != 'implicit'}
                implicit = any(item[0] == 'implicit' for item in identities)
                if explicit and implicit:
                    candidate = next(iter(explicit))[1]
                    tail = f':{first.definition.logical_name}:{first.definition.version}'
                    if not (candidate.startswith('urn:algites:') and candidate.endswith(tail)):
                        explicit.add(('incompatible', 'implicit-identity'))
                if explicit:
                    identities = explicit
            if len(identities) != 1:
                raise ValueError('Canonical identity collision for one generated output: ' +
                    str([(r.definition.identity, r.definition.source_resource) for r in representations]))
            if common_role and len(representations) > 1:
                from eu.algites.tool.codegen.defs.impl.standard.aic_common_contract_projection import merge_common
                merged = merge_common([r.definition for r in representations])
            else:
                merged = AIcCanonicalDefinitionMerger.merge_strict((r.definition for r in representations), repository)
            parent_relations = relations[first.target.value + '#' + generator.generate(first).relative_path]
            def represented_parents(relation):
                result = []
                for unit in relation:
                    request = unit_requests.get((first.target.value, first.contract_role, unit.schema, unit.pointer))
                    if request is None:
                        raise ValueError('allOf parent has no generated contract in role '
                                         + first.contract_role + ': ' + unit.schema + '#' + unit.pointer)
                    result.append((request.package_name, generator.generate(request).type_name))
                return tuple(result)
            expected_parents = represented_parents(parent_relations[0])
            shared_parents = all(represented_parents(relation) == expected_parents
                                 for relation in parent_relations)
            if not shared_parents and not common_role:
                raise ValueError('Conflicting allOf parents across schema representations')
            parent_requests = []
            for unit in (parent_relations[0] if shared_parents else ()) :
                inherited = unit_requests.get((first.target.value, first.contract_role, unit.schema, unit.pointer))
                if inherited is None:
                    raise ValueError('allOf parent has no generated contract in role ' + first.contract_role
                                     + ': ' + unit.schema + '#' + unit.pointer)
                parent_requests.append(inherited)
            parent = None
            additional_parents = []
            inherited_fields = {}
            for inherited in parent_requests:
                if inherited.definition.data_type.kind is not AInDataTypeKind.OBJECT or merged.data_type.kind is not AInDataTypeKind.OBJECT:
                    raise ValueError('allOf inheritance must connect object contracts')
                for field in inherited.definition.data_type.properties:
                    existing = inherited_fields.setdefault(field.source_name, field)
                    if self._field_shape(existing) != self._field_shape(field):
                        raise ValueError('Conflicting fields among allOf parents: ' + field.source_name)
                preview = generator.generate(inherited)
                parent_module = inherited.package_name
                if first.target is AInCodeGenerationTarget.PYTHON:
                    parent_module += '.' + preview.relative_path.rsplit('/', 1)[-1][:-3]
                if parent is None:
                    parent = (preview.type_name, parent_module)
                else:
                    additional_parents.append((preview.type_name, parent_module))
            if parent_requests:
                own_fields = []
                for field in merged.data_type.properties:
                    inherited_field = inherited_fields.get(field.source_name)
                    if inherited_field is None or self._field_shape(field) != self._field_shape(inherited_field):
                        if inherited_field is not None and not self._field_narrows(inherited_field, field):
                            raise ValueError('Conflicting inherited field: ' + field.source_name)
                        own_fields.append(field)
                merged = replace(merged, data_type=merged.data_type.with_properties(tuple(own_fields)))
            if first.xml_type_qname is not None:
                xml_origin = units_by_resource.get(first.definition.source_resource)
                if xml_origin is None:
                    raise ValueError(f'Unknown XSD source {first.definition.source_resource}')
                load = AIcdDefinitionLoadRequest(self._inside(repository, xml_origin.schema),
                    AInDefinitionSourceKind.XMLDEFS, first.naming_profile)
                parent_qname = (AIcXmlDefsFrontend().named_type_extension_base_qname(load, xml_origin.pointer[6:])
                    if xml_origin.pointer.startswith('@type/')
                    else AIcXmlDefsFrontend().root_extension_base_qname(load))
                if parent_qname is not None:
                    inherited = xml_type_requests.get((first.target, first.contract_role,
                        first.package_name if parent_qname.startswith('{}') else '', parent_qname))
                    if inherited is None or inherited == first:
                        raise ValueError('XML extension base has no independently emitted contract: '
                            + parent_qname + ' for ' + first.xml_type_qname)
                    if merged.data_type.kind is not AInDataTypeKind.OBJECT or inherited.definition.data_type.kind is not AInDataTypeKind.OBJECT:
                        raise ValueError('XML extension requires object contracts')
                    inherited_fields = {field.source_name: field for field in inherited.definition.data_type.properties}
                    own_fields = []
                    for field in merged.data_type.properties:
                        base_field = inherited_fields.get(field.source_name)
                        if base_field is None:
                            own_fields.append(field)
                        elif self._field_shape(base_field) != self._field_shape(field):
                            raise ValueError(f'Incompatible inherited XML extension field: {field.source_name}')
                    from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
                    merged = replace(merged, data_type=merged.data_type.with_properties(tuple(own_fields)))
                    preview = generator.generate(inherited)
                    parent_module = inherited.package_name
                    if first.target is AInCodeGenerationTarget.PYTHON:
                        parent_module += '.' + preview.relative_path.rsplit('/', 1)[-1][:-3]
                    parent = (preview.type_name, parent_module)
            language = first.target.value
            for index, pair in enumerate(generator.generate_sources(replace(first, definition=merged), parent)):
                alternative = None
                if (merged.source_kind is not AInDefinitionSourceKind.XMLDEFS
                        and merged.data_type is not None and merged.data_type.kind in
                        (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF) and index > 0):
                    alternative = merged.data_type.alternatives[index - 1]
                choice_reference = alternative.reference if alternative is not None and alternative.kind is AInDataTypeKind.REFERENCE else None
                rendered = pair.source
                if additional_parents:
                    if language == 'java':
                        declaration = f'public interface {pair.type_name} extends '
                        start = rendered.index(declaration)
                        end = rendered.index(' {', start)
                        rendered = (rendered[:end] + ', ' + ', '.join(module + '.' + name
                            for name, module in additional_parents) + rendered[end:])
                    else:
                        imports = ''.join('from ' + module + ' import ' + name + '\n'
                            for name, module in additional_parents)
                        rendered = rendered.replace('from __future__ import annotations\n',
                            'from __future__ import annotations\n' + imports)
                        declaration = f'class {pair.type_name}('
                        start = rendered.index(declaration)
                        end = rendered.index('):', start)
                        rendered = (rendered[:end] + ', ' + ', '.join(name for name, _ in additional_parents)
                                    + rendered[end:])
                if configured and first.contract_role != 'common' and merged.data_type.kind is AInDataTypeKind.OBJECT:
                    origin = units_by_resource.get(first.definition.source_resource)
                    common = (unit_requests.get((language, 'common', origin.schema, origin.pointer))
                              if origin is not None else None)
                    if common is not None:
                        preview = generator.generate(common)
                        if language == 'java':
                            declaration = f'public interface {pair.type_name} extends '
                            rendered = rendered.replace(declaration, declaration +
                                common.package_name + '.' + preview.type_name + ', ')
                        else:
                            stem = preview.relative_path.rsplit('/', 1)[-1].removesuffix('.py')
                            rendered = rendered.replace('from __future__ import annotations\n',
                                'from __future__ import annotations\nfrom ' + common.package_name +
                                '.' + stem + ' import ' + preview.type_name + '\n')
                            declaration = f'class {pair.type_name}('
                            rendered = rendered.replace(declaration, declaration + preview.type_name + ', ')
                rendered = self._qualify_references(rendered, first, requests, True, choice_reference)
                if first.xml_type_qname is not None and index == 0 and merged.data_type.kind in (
                        AInDataTypeKind.OBJECT, AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
                    namespace = first.xml_type_qname[1:].split('}', 1)[0]
                    wildcard_fields = {}
                    for field in merged.data_type.properties:
                        xml = field.xml_field
                        if xml is None or not xml.wildcard_namespace:
                            continue
                        selected = xml_namespaces.namespace_of_wildcard(xml.wildcard_namespace, xml.namespace)
                        wildcard_fields[field.source_name] = (namespace_ref(language, selected)
                            if selected is not None else
                            ('eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object.AIiXmlDataObject'
                                if language == 'python' else
                                'eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject'))
                    rendered = xml_namespaces.decorate(rendered, first,
                        namespace_ref(language, namespace), wildcard_fields, language == 'python')
                self._add(pending, output_roots.get(language, intf / 'src/product' / (language + '.gen')) / pair.relative_path,
                    rendered)

        # Global XSD element declarations occupy a separate QName symbol space from
        # content types. Build complete target-specific indexes before emitting any
        # element so forward and cross-file substitution references are supported.
        xml_generator = AIcXmlElementContractGenerator()
        xml_frontend = AIcXmlDefsFrontend()
        for language in manifest['languages']:
            if configured and 'xmldefs_element' not in manifest['technology_output_naming_conventions'].get(language, {}):
                continue
            xml_requests = [(schema, pointer, req) for (target, role, schema, pointer), req in unit_requests.items()
                            if target == language and kind_by_source[schema] == 'xmldefs'
                            and role == ('xmldefs_type' if configured else '')]
            type_index, element_index, declarations, value_types = {}, {}, [], set()
            for schema, pointer, req in xml_requests:
                loaded = AIcdDefinitionLoadRequest(self._inside(repository, schema),
                    AInDefinitionSourceKind.XMLDEFS, req.naming_profile)
                root_qname = req.xml_type_qname or xml_frontend.root_type_qname(loaded)
                if req.definition.data_type.kind in (AInDataTypeKind.OBJECT, AInDataTypeKind.ENUM,
                        AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
                    if req.definition.data_type.kind in (AInDataTypeKind.ENUM,
                            AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
                        value_types.add(root_qname)
                    preview = generator.generate(req)
                    qualified = req.package_name + '.' + (preview.relative_path.rsplit('/', 1)[-1][:-3] + '.'
                        if language == 'python' else '') + preview.type_name
                    if root_qname in type_index and type_index[root_qname] != qualified:
                        raise ValueError('Duplicate XML global content type: ' + root_qname)
                    type_index[root_qname] = qualified
                if pointer:
                    continue
                for element in xml_frontend.global_element_declarations(loaded):
                    element_name = generator.names.render(
                        xml_identifier(element.local_name), req.definition.version, req.naming_profile,
                        AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE)
                    stem = generator.names.render(xml_identifier(element.local_name), req.definition.version,
                        req.naming_profile, AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE_FILE_STEM)
                    qualified = req.package_name + '.' + (stem + '.' if language == 'python' else '') + element_name
                    if element.qname in element_index:
                        raise ValueError('Duplicate XML global element: ' + element.qname)
                    element_index[element.qname] = qualified
                    declarations.append((schema, req, element))
            for schema, req, element in declarations:
                generated = xml_generator.generate(req, element, type_index, element_index, value_types)
                output_root = output_roots.get(language, intf / 'src/product' / (language + '.gen'))
                element_namespace = element.namespace
                if (language, element_namespace) not in xml_namespace_owners:
                    xml_namespace_owners[(language, element_namespace)] = req
                rendered = xml_namespaces.decorate(generated.source, req,
                    namespace_ref(language, element_namespace), {}, language == 'python')
                self._add(pending, output_root / generated.relative_path, rendered)
                result.append(dict(schema=schema, pointer='@element/' + element.local_name,
                    language=language, type=generated.type_name,
                    path=(output_root / generated.relative_path).relative_to(repository).as_posix()))

        for (language, namespace), owner in sorted(xml_namespace_owners.items()):
            name, relative, generated = xml_namespaces.source(owner, namespace)
            output_root = output_roots.get(language, intf / 'src/product' / (language + '.gen'))
            self._add(pending, output_root / relative, generated)
            result.append(dict(schema=owner.definition.source_resource, pointer='@namespace/' + namespace,
                language=language, type=name,
                path=(output_root / relative).relative_to(repository).as_posix()))

        # Preserve files owned by unrelated output technologies. A matching
        # naming pattern alone must never delete a manually authored source.
        for stale in sorted(previously_owned - set(pending)):
            if stale.is_file():
                if check:
                    raise ValueError(f'Stale generated binding: {stale}')
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
            owned = unrelated_owned | set(pending)
            state.write_text(json.dumps([p.relative_to(repository).as_posix()
                for p in sorted(owned)], indent=2) + '\n', encoding='utf-8')
        return result

    @staticmethod
    def _canonical_identity(definition, package_name, units_by_resource):
        """Normalize only format-specific publication aliases, never arbitrary schema IDs."""
        origin = units_by_resource[definition.source_resource]
        document = origin.document
        explicit_id = (document.get('x-yamldefs-id') or document.get('x-jsondefs-id')
                       or document.get('$id')) if document else None
        if not explicit_id and (definition.source_kind is not AInDefinitionSourceKind.XMLDEFS
                                or definition.identity == definition.logical_name):
            return ('implicit', package_name, definition.logical_name, definition.version, origin.pointer)
        identity = str(definition.identity)
        identity = re.sub(r'(/api/)(?:yamldefs|jsondefs|xmldefs)(/)', r'\1schema\2', identity)
        identity = re.sub(r'\.(?:yamldef|jsondef)\.schema\.json(?=#|$)|\.xsd(?=#|$)',
                          '.schema', identity)
        return ('explicit', identity, definition.version)

    @staticmethod
    def _common_identity(definition, package_name, identity):
        """Treat only the source-kind URN segment as a serialization alias of a common type."""
        if identity[0] != 'explicit' or not str(identity[1]).startswith('urn:algites:'):
            return identity
        name = {'YAMLDEFS': 'yamldef', 'JSONDEFS': 'jsondef'}.get(definition.source_kind.name)
        if name:
            return ('explicit', str(identity[1]).replace(':' + name + ':', ':', 1), definition.version)
        return identity

    @staticmethod
    def _field_shape(field):
        return (field.source_name, field.data_type, field.presence, field.nullable,
            field.xml_field)

    @classmethod
    def _field_narrows(cls, parent, child):
        """Permit only provable presence/nullability narrowing in an inherited property."""
        from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
        if (parent.source_name != child.source_name or parent.data_type != child.data_type
                or parent.xml_field != child.xml_field):
            return False
        if parent.presence is AInFieldPresenceKind.REQUIRED and child.presence is not AInFieldPresenceKind.REQUIRED:
            return False
        if parent.presence is AInFieldPresenceKind.FORBIDDEN and child.presence is not AInFieldPresenceKind.FORBIDDEN:
            return False
        if not parent.nullable and child.nullable:
            return False
        return parent.presence != child.presence or parent.nullable != child.nullable

    @staticmethod
    def _parent_units(unit, index, repository):
        """Resolve all allOf contract references without dropping any parent branch."""
        branches = unit.node.get('allOf', [])
        if not isinstance(branches, list):
            raise ValueError('allOf must be an array')
        references = [branch['$ref'] for branch in branches
                      if isinstance(branch, dict) and '$ref' in branch]
        parents = []
        for reference in references:
            parts = urlsplit(reference)
            if parts.fragment and not unquote(parts.fragment).startswith('/'):
                raise ValueError('Unsupported allOf parent anchor: ' + reference)
            if parts.scheme and parts.scheme != 'file':
                matches = [candidate for candidate in index.values()
                    if candidate.document.get('$id') == reference.split('#', 1)[0]
                    and candidate.pointer == unquote(parts.fragment)]
                if len(matches) != 1:
                    raise ValueError('Unresolved or ambiguous allOf parent: ' + reference)
                parents.append(matches[0])
                continue
            if parts.scheme == 'file':
                target = Path(unquote(parts.path))
            else:
                target = (repository / unit.schema).parent / unquote(parts.path) if parts.path else repository / unit.schema
            target = Path(os.path.abspath(target))
            if not target.is_relative_to(repository):
                raise ValueError('allOf parent escapes repository: ' + reference)
            pointer = unquote(parts.fragment)
            parent = index.get((target.relative_to(repository).as_posix(), pointer))
            if parent is None:
                raise ValueError('allOf parent is not an emitted contract: ' + reference)
            parents.append(parent)
        if len({(unit.schema, unit.pointer) for unit in parents}) != len(parents):
            raise ValueError('Duplicate allOf parent in ' + unit.schema)
        return tuple(parents)

    @staticmethod
    def _qualify_references(source, request, requests, contract, choice_reference=None):
        names = AIcGenerationNames()
        references = [prop.data_type.referenced_definition() for prop in request.definition.data_type.properties if prop.data_type.referenced_definition() is not None]
        if choice_reference is not None:
            references.append(choice_reference)
        for ref in references:
            resource = ref.identity.split('#', 1)[0]
            owner = request.definition.source_resource.split('#', 1)[0]
            parsed = urlsplit(resource)
            local = None if parsed.scheme else (owner if not resource else Path(os.path.normpath(str(Path(owner).parent / resource))).as_posix())
            published = None
            if parsed.scheme == 'https' and parsed.netloc == 'defs.dev.algites.eu':
                for kind in ('yamldefs', 'jsondefs', 'xmldefs'):
                    prefix = '/api/' + kind + '/'
                    if parsed.path.startswith(prefix):
                        published = 'src/product/' + kind + '/' + parsed.path[len(prefix):]
                        break
            candidates = {r.package_name for representations in requests.values() for r in representations
                if r.target is request.target and (r.definition.source_resource in (local, published)
                    or r.definition.identity == resource)}
            if len(candidates) != 1:
                raise ValueError(f'Cannot resolve generated reference package: {ref.identity} in {owner}')
            package = next(iter(candidates))
            if package == request.package_name:
                continue
            is_enum = ref.targets_enum
            type_kind = AInDefsNameRole.ENUM_TYPE if is_enum else (AInDefsNameRole.INTERFACE_TYPE if contract else AInDefsNameRole.DATA_TYPE)
            file_kind = AInDefsNameRole.ENUM_TYPE_FILE_STEM if is_enum else (AInDefsNameRole.INTERFACE_TYPE_FILE_STEM if contract else AInDefsNameRole.DATA_TYPE_FILE_STEM)
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
        if not pointer or node.get('type') == 'object' or 'properties' in node or 'enum' in node or 'oneOf' in node or 'anyOf' in node:
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
