from __future__ import annotations

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException

from copy import deepcopy
from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit, unquote

from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
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
            from ._catalog_sources import expand_naming_catalogs
            sources = [source if source.startswith(('classpath:', 'resource:'))
                       else str(self._inside(repository, source))
                       for source in manifest.get('naming_convention_files', [])]
            with expand_naming_catalogs(sources) as files:
                shared_names = AIcNameConventionCatalog.load_many(files)
        output_roots = {t: self._inside(repository, d) for t, d in manifest.get('technology_outputs', {}).items()}
        catalogs = {t: AIcNameConventionCatalog.load(self._inside(repository, file))
                    for t, file in manifest.get('technology_naming_profiles', {}).items()}
        target_profiles = {t: AIcNameConventionCatalog.load(self._inside(repository, file))
                           for t, file in manifest.get('technology_naming_profiles', {}).items()}
        source_catalogs = {k: AIcNameConventionCatalog.load(self._inside(repository, file))
                           for k, file in manifest.get('schema_input_naming_profiles', {}).items()}
        if configured:
            catalogs = {language: shared_names for language in output_roots}
            method_profiles = manifest.get('generated_dataobject_method_naming_conventions', {})
            target_profiles = {language: shared_names.with_generated_method_profile(method_profiles[language])
                               if language in method_profiles else shared_names
                               for language in output_roots}
            source_catalogs = {kind: shared_names for kind in manifest.get('schema_input_naming_conventions', {})}
        if not configured and not manifest.get('technology_naming_profiles'):
            raise AIxCodegenValidationException('No explicit output naming catalog configured', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
        if explicit and not configured:
            for technology in output_roots:
                if technology not in catalogs:
                    raise AIxCodegenValidationException('Missing target naming catalog: ' + technology, 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
        # Only paths listed in generator ownership state can be deleted. Filename
        # convention matching is not proof of ownership when profiles are shared.
        state = repository / 'build/run/schema-contract-bindings/generated-files.json'
        previously_recorded = json.loads(state.read_text(encoding='utf-8')) if state.is_file() else []
        if not isinstance(previously_recorded, list) or any(not isinstance(x, str) for x in previously_recorded):
            raise AIxCodegenValidationException(f'Invalid generation ownership file: {state}', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
        previously_owned = set()
        unrelated_owned = set()
        for old in previously_recorded:
            stale = self._inside(repository, old)
            if not any(part.endswith('.gen') for part in stale.parts):
                raise AIxCodegenValidationException(f'Invalid ownership state: {old}', 'Review the indicated source declaration and the generator contract. Correct the incompatible input rather than editing the generated outputs.')
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
        profile_by_source = {}
        kind_by_source = {}
        declared_identity_by_source = {}
        existing_source_directories = 0
        for source_input in source_roots:
            kind = source_input['kind']
            suffix = {'jsondefs': '.jsondef.schema.json', 'yamldefs': '.yamldef.schema.json', 'xmldefs': '.xsd'}[kind]
            root = Path(source_input['directory']).resolve() if Path(source_input['directory']).is_absolute() else self._inside(repository, source_input['directory'])
            if not root.is_relative_to(repository):
                raise AIxCodegenValidationException('Schema root escapes repository: ' + str(root), 'Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.')
            if not root.is_dir():
                print(f'Defs Codegen: skipping configured {kind} input directory (not found): {root}', file=__import__('sys').stderr)
                continue
            existing_source_directories += 1
            for source in sorted(root.rglob('*')):
                if not source.is_file() or not source.name.endswith(suffix):
                    continue
                schema = source.relative_to(repository).as_posix()
                if schema in root_by_source:
                    raise AIxCodegenValidationException('Overlapping schema input roots: ' + schema, 'Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.')
                root_by_source[schema] = root
                kind_by_source[schema] = kind
                if configured and kind not in source_catalogs:
                    continue
                if kind in source_catalogs:
                    loc_profile = manifest.get('schema_input_naming_conventions', {}).get(kind) if configured else None
                    recognized = source_catalogs[kind].recognize_filename(source.name,
                        {loc_profile} if loc_profile else None)
                    if recognized is None:
                        raise AIxCodegenValidationException('Schema filename violates input naming profile: ' + schema, 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
                    profile_by_source[schema] = recognized.convention_name
                    if not manifest.get('allow_unversioned_schemas', False) and 'version' not in recognized.variables:
                        raise AIxCodegenValidationException('Unversioned schema is not allowed: ' + schema, 'Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.')
                document = {} if kind == 'xmldefs' else load_schema(source)
                if kind != 'xmldefs':
                    source_catalog = source_catalogs.get(kind)
                    source_profile = profile_by_source.get(schema)
                    if source_catalog is None or not source_profile:
                        raise AIxCodegenValidationException('Missing source naming catalog/profile for ' + schema, 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
                    id_field = source_catalog.schema_metadata_fields(source_profile).get(
                        'schema_source_schema_identifier', '')
                    declared_identity_by_source[schema] = bool(id_field and document.get(id_field))
                match = source_catalogs[kind].recognize_filename(source.name,
                    {profile_by_source[schema]})
                if match is None or not match.variables.get('identifier'):
                    raise AIxCodegenValidationException('Schema file name cannot be parsed by source profile: ' + schema, 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
                base = match.variables['identifier']
                if kind == 'xmldefs':
                    units.append(self.AIcdUnit(schema, '', base, {}, {}))
                    for name in AIcXmlDefsFrontend().additional_named_type_names(source):
                        units.append(self.AIcdUnit(schema, '@type/' + name, name, {}, {}))
                else:
                    self._collect(document, '', base, schema, document, overrides, units,
                        source_catalogs[kind], profile_by_source[schema])
        if existing_source_directories == 0:
            print('Defs Codegen: no configured schema input directory exists; nothing to generate',
                  file=__import__('sys').stderr)
            return []
        discovered = {unit.schema + '#' + unit.pointer for unit in units}
        for key in overrides:
            if key not in discovered:
                raise AIxCodegenValidationException(f'Binding override no longer identifies a schema object: {key}', 'Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.')

        # No-namespace XML declarations are scoped to their defining schema, not
        # to one fictitious global {} QName registry shared by unrelated XSDs.
        # Put genuinely colliding XML-specialized types in document-specific
        # packages; common XML/YAML/JSON contracts keep their original package.
        anonymous_owners = {}
        xml_scope_frontend = AIcXmlDefsFrontend()
        for unit in units:
            if kind_by_source[unit.schema] != 'xmldefs':
                continue
            source = self._inside(repository, unit.schema)
            if not target_profiles:
                raise AIxCodegenValidationException('No output naming profile configured', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
            load = AIcdDefinitionLoadRequest(source, AInDefinitionSourceKind.XMLDEFS,
                next(iter(target_profiles.values())), profile_by_source[unit.schema])
            if unit.pointer.startswith('@type/') and xml_scope_frontend.is_synthetic_choice_type_name(
                    source, unit.pointer[6:]):
                continue
            qname = ('{' + xml_scope_frontend.schema_namespace(load) + '}' + unit.pointer[6:]
                if unit.pointer.startswith('@type/') else xml_scope_frontend.root_type_qname(load))
            if qname.startswith('{}'):
                anonymous_owners.setdefault(('type', qname), set()).add(unit.schema)
            if not unit.pointer:
                for element in xml_scope_frontend.global_element_declarations(load):
                    if not element.namespace:
                        anonymous_owners.setdefault(('element', element.qname), set()).add(unit.schema)
        scoped_xml_documents = set().union(*(owners for owners in anonymous_owners.values()
            if len(owners) > 1)) if anonymous_owners else set()
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
                raise AIxCodegenValidationException(f'Schema must have a legal package path: {unit.schema}', 'Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.')
            projection = deepcopy(unit.node)
            fields = {}
            if kind != 'xmldefs':
                if '$defs' in unit.document:
                    projection['$defs'] = unit.document['$defs']
                source_catalog = source_catalogs.get(kind)
                source_profile = profile_by_source.get(unit.schema)
                if source_catalog is None or not source_profile:
                    raise AIxCodegenValidationException('Missing source naming catalog/profile for ' + unit.schema, 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
                fields = source_catalog.schema_metadata_fields(source_profile) if source_catalog and source_profile else {}
                id_key = fields.get('schema_source_schema_identifier', '')
                version_key = fields.get('schema_source_schema_version', '')
                url_key = fields.get('schema_source_schema_url', '')
                declared_id = str(unit.document.get(id_key) or unit.name) if id_key else unit.name
                projection['x-jsondefs-id'] = declared_id + ('#' + unit.pointer if unit.pointer else '')
                if version_key and version_key in unit.document:
                    projection['x-jsondefs-version'] = unit.document[version_key]
                if url_key and url_key in unit.document:
                    projection['$id'] = unit.document[url_key]
                projection['x-jsondefs-name'] = unit.name
            parent_units = self._parent_units(unit, unit_index, repository) if kind != 'xmldefs' else ()
            for language in manifest['languages']:
                target = AInCodeGenerationTarget(language)
                profile = target_profiles.get(language)
                if profile is None:
                    raise AIxCodegenValidationException(f'No output naming profile configured for {language}', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
                load = AIcdDefinitionLoadRequest(source,
                    {'yamldefs': AInDefinitionSourceKind.YAMLDEFS, 'jsondefs': AInDefinitionSourceKind.JSONDEFS,
                     'xmldefs': AInDefinitionSourceKind.XMLDEFS}[kind], profile,
                     profile_by_source[unit.schema])
                if kind == 'xmldefs':
                    definition = (AIcXmlDefsFrontend().load_named_type(load, unit.pointer[6:])
                                  if unit.pointer.startswith('@type/') else AIcXmlDefsFrontend().load(load))
                else:
                    definition = reader.read(projection, load, load.source_kind, 'x-jsondefs-id', 'x-jsondefs-version', 'x-jsondefs-name', '$id')
                # Source naming decides which schema properties were read; the
                # selected method/output profile independently controls wire emission.
                # XMLDEFS do not use JSON/YAML document-header mappings. Preserve
                # legacy XML contract annotations instead of applying JSON metadata
                # requirements to an XSD without such source fields.
                output_fields = ({} if kind == 'xmldefs' else
                    profile.schema_metadata_fields(profile.generated_method_profile)
                    if profile.generated_method_profile else fields)
                for suffix in ('url', 'identifier', 'version'):
                    output_key = f'data_source_schema_{suffix}'
                    if output_fields.get(output_key) and (
                            not fields.get(f'schema_source_schema_{suffix}')
                            or not output_fields.get(f'schema_source_schema_{suffix}')):
                        raise AIxCodegenValidationException(f'{unit.schema}: {output_key} has no schema source', 'Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.')
                definition = replace(definition, source_resource=unit.schema + ('#' + unit.pointer if unit.pointer else ''),
                    data_source_schema_url_field=output_fields.get('data_source_schema_url', ''),
                    data_source_schema_identifier_field=output_fields.get('data_source_schema_identifier', ''),
                    data_source_schema_version_field=output_fields.get('data_source_schema_version', ''),
                    schema_source_schema_url_field=(None if kind == 'xmldefs' else
                        fields.get('schema_source_schema_url', '')
                        if output_fields.get('schema_source_schema_url') else ''),
                    schema_source_schema_identifier_field=(None if kind == 'xmldefs' else
                        fields.get('schema_source_schema_identifier', '')
                        if output_fields.get('schema_source_schema_identifier') else ''),
                    schema_source_schema_version_field=(None if kind == 'xmldefs' else
                        fields.get('schema_source_schema_version', '')
                        if output_fields.get('schema_source_schema_version') else ''))
                xml_type_qname = (('{' + AIcXmlDefsFrontend().schema_namespace(load) + '}' + unit.pointer[6:]
                    if not AIcXmlDefsFrontend().is_synthetic_choice_type_name(source, unit.pointer[6:]) else None)
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
                        namespace_id = configured_roles.get('xmldefs_namespace')
                        if namespace_id:
                            entries.update({kind: namespace_id for kind in
                                (AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE,
                                 AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE_FILE_STEM)})
                        enum_id = manifest.get('technology_enum_output_naming_conventions', {}).get(language, selected_id)
                        entries.update({kind: enum_id for kind in (AInDefsNameRole.ENUM_TYPE,
                            AInDefsNameRole.ENUM_TYPE_FILE_STEM)})
                        role_profile = AIcSelectedNamingCatalog(profile, entries)
                    output_package = package
                    if kind == 'xmldefs' and role != 'common' and unit.schema in scoped_xml_documents:
                        document = re.sub(r'[^A-Za-z0-9_]', '_', source.stem).lower()
                        output_package += '.xmlschema_' + document
                    common_profile = None
                    common_keyed_fields = frozenset()
                    common_id = configured_roles.get('common')
                    if role != 'common' and common_id:
                        common_profile = AIcSelectedNamingCatalog(profile, {
                            kind: common_id for kind in (AInDefsNameRole.INTERFACE_TYPE,
                                AInDefsNameRole.INTERFACE_TYPE_FILE_STEM,
                                AInDefsNameRole.DATA_TYPE, AInDefsNameRole.DATA_TYPE_FILE_STEM)})
                        common_keyed_fields = frozenset(field.source_name
                            for field in definition.data_type.properties
                            if field.data_type.keyed_value_type is not None)
                    request = AIcdCodeGenerationRequest(definition, target, output_package, role_profile,
                        xml_type_qname, selected_id, role, common_profile, common_keyed_fields)
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
                raise AIxCodegenValidationException(f'Ambiguous XML named type {candidate.xml_type_qname}', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
        # Resolve one XML namespace marker per target/namespace across all schema packages.
        # Only XML requests participate; JSON and YAML have no namespace interfaces.
        def namespace_key(language, namespace, req):
            """Scope absent XML namespaces by document, retaining explicit global URIs."""
            source = req.definition.source_resource.split('#', 1)[0]
            return (language, namespace, source if not namespace and source in scoped_xml_documents else '')
        xml_namespace_owners = {}
        for (language, role, schema, pointer), req in unit_requests.items():
            if kind_by_source[schema] != 'xmldefs' or role == 'common':
                continue
            namespace = req.xml_type_qname[1:].split('}', 1)[0] if req.xml_type_qname else None
            if namespace is not None:
                xml_namespace_owners.setdefault(namespace_key(language, namespace, req), req)
            for field in req.definition.data_type.properties:
                xml = field.xml_field
                if xml is None or not xml.wildcard_namespace:
                    continue
                explicit_namespace = xml_namespaces.namespace_of_wildcard(xml.wildcard_namespace, xml.namespace)
                if explicit_namespace is not None:
                    xml_namespace_owners.setdefault(namespace_key(language, explicit_namespace, req), req)
        def namespace_ref(language, namespace, req):
            owner = xml_namespace_owners.get(namespace_key(language, namespace, req))
            if owner is None:
                raise AIxCodegenValidationException('Missing generated XML namespace contract: ' + namespace, 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
            name, stem, module = xml_namespaces.namespace_contract(owner, namespace)
            return module + '.' + name if language == 'python' else owner.package_name + '.' + name

        # XML named complexTypes and JSON/YAML inline `items` are independent
        # declarations, even when they model exactly the same object.  Link
        # their generated contracts only after checking structural compatibility:
        # the XML-specific interface can then legally narrow the typed common
        # getter (rather than forcing the common getter to return Object).
        xml_inline_bridges = {}
        xml_common_projections = {}

        def same_contract_shape(left, right):
            """Require identical public getter shapes before adding a nominal parent."""
            if left.kind is not right.kind:
                return False
            if left.kind is AInDataTypeKind.OBJECT:
                left_fields = {field.source_name: field for field in left.properties}
                right_fields = {field.source_name: field for field in right.properties}
                return (left_fields.keys() <= right_fields.keys()
                    and all(same_contract_shape(field.data_type,
                        right_fields[name].data_type) for name, field in left_fields.items()))
            if left.kind is AInDataTypeKind.ARRAY:
                return same_contract_shape(left.element_type, right.element_type)
            if left.kind is AInDataTypeKind.REFERENCE:
                return (left.reference.logical_name == right.reference.logical_name
                    and left.reference.version == right.reference.version)
            if left.kind in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
                return len(left.alternatives) == len(right.alternatives) and all(
                    same_contract_shape(x, y) for x, y in zip(left.alternatives, right.alternatives))
            return True

        for candidates in requests.values():
            if not candidates or candidates[0].contract_role != 'common':
                continue
            xml_candidates = [c for c in candidates if c.definition.source_kind is AInDefinitionSourceKind.XMLDEFS]
            structured = [c for c in candidates if c.definition.source_kind in
                (AInDefinitionSourceKind.JSONDEFS, AInDefinitionSourceKind.YAMLDEFS)]
            if len(xml_candidates) != 1 or not structured:
                continue
            xml_request = xml_candidates[0]
            replacements = {}
            for xml_field in xml_request.definition.data_type.properties:
                xml_array = xml_field.data_type
                if xml_array.kind is not AInDataTypeKind.ARRAY:
                    continue
                ref_type = xml_array.element_type
                if (ref_type.kind is not AInDataTypeKind.REFERENCE
                        or not ref_type.reference.identity.startswith('#@type/')):
                    continue
                named_pointer = '@type/' + ref_type.reference.identity.removeprefix('#@type/')
                xml_origin = units_by_resource.get(xml_request.definition.source_resource)
                if xml_origin is None:
                    continue
                named_xml = unit_requests.get((xml_request.target.value, 'xmldefs_type',
                    xml_origin.schema, named_pointer))
                if named_xml is None or named_xml.definition.data_type.kind is not AInDataTypeKind.OBJECT:
                    continue
                candidate_inlines = []
                for structured_request in structured:
                    matching = next((f for f in structured_request.definition.data_type.properties
                        if f.source_name == xml_field.source_name), None)
                    if matching is None or matching.data_type.kind is not AInDataTypeKind.ARRAY:
                        break
                    item = matching.data_type.element_type
                    if item.kind is not AInDataTypeKind.OBJECT:
                        break
                    source = structured_request.definition.source_resource.split('#', 1)[0]
                    escaped = xml_field.source_name.replace('~', '~0').replace('/', '~1')
                    common_item = unit_requests.get((xml_request.target.value, 'common',
                        source, '/properties/' + escaped + '/items'))
                    if common_item is None or not same_contract_shape(
                            common_item.definition.data_type, named_xml.definition.data_type):
                        break
                    candidate_inlines.append((item, common_item))
                else:
                    if not candidate_inlines:
                        continue
                    common_names = {generator.generate(item).type_name
                        for _, item in candidate_inlines}
                    if len(common_names) != 1:
                        raise AIxCodegenValidationException('Ambiguous common XML item bridge: '
                            + xml_request.definition.source_resource + ':' + xml_field.source_name, 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
                    key = (xml_request.target.value, xml_origin.schema, named_pointer)
                    selected = candidate_inlines[0][1]
                    previous = xml_inline_bridges.setdefault(key, selected)
                    if generator.generate(previous).type_name != generator.generate(selected).type_name:
                        raise AIxCodegenValidationException('Conflicting common XML item bridge: ' + str(key), 'Check xs:key/xs:unique selectors and all xs:field paths against the selected repeated element. A key requires complete values; a unique constraint permits absent values.')
                    replacements[xml_field.source_name] = named_xml.definition.data_type
            if replacements:
                xml_common_projections[id(xml_request)] = replacements

        for representations in requests.values():
            first = representations[0]
            common_role = first.contract_role == 'common'
            identities = {(self._common_identity(r.definition, r.package_name,
                          self._canonical_identity(r.definition, r.package_name, units_by_resource, declared_identity_by_source))
                          if common_role else self._canonical_identity(r.definition, r.package_name, units_by_resource, declared_identity_by_source))
                          for r in representations}
            if common_role:
                explicit = {item for item in identities if item[0] != 'implicit'}
                implicit = any(item[0] == 'implicit' for item in identities)
                if explicit and implicit:
                    if any(not self._common_explicit_matches_implicit(expl, impl)
                           for expl in explicit for impl in identities if impl[0] == 'implicit'):
                        explicit.add(('incompatible', 'implicit-identity'))
                if explicit:
                    identities = explicit
            if len(identities) != 1 and common_role:
                # XML has global named types with one root document namespace,
                # whereas JSON/YAML $defs has an explicit per-definition ID.
                # These two distinct wire identities may share a GENERATED
                # common contract only when the output's uniquely selected
                # non-XML logical identity agrees, all named XML sources are
                # children of the same schema root, and merge_common below
                # proves a compatible typed contract. Never normalize two
                # conflicting explicit JSON/YAML identities together.
                structured = [r for r in representations if r.definition.source_kind
                    in (AInDefinitionSourceKind.JSONDEFS, AInDefinitionSourceKind.YAMLDEFS)]
                xml_nested = [r for r in representations if r.definition.source_kind
                    is AInDefinitionSourceKind.XMLDEFS and '#@type/' in r.definition.source_resource]
                if structured and xml_nested and len(structured) + len(xml_nested) == len(representations):
                    document_ids = {self._common_identity(r.definition, r.package_name,
                        self._canonical_identity(r.definition, r.package_name,
                            units_by_resource, declared_identity_by_source)) for r in structured}
                    if (len(document_ids) == 1 and all(
                        r.definition.logical_name == structured[0].definition.logical_name
                        and r.definition.version == structured[0].definition.version
                        and r.package_name == structured[0].package_name
                        and (lambda xml_name, json_name: (
                            source_catalogs['xmldefs'].recognize_filename(xml_name).variables['identifier']
                            == source_catalogs[structured[0].definition.source_kind.value]
                                .recognize_filename(json_name).variables['identifier']))(
                            Path(r.definition.source_resource.split('#', 1)[0]).name,
                            Path(structured[0].definition.source_resource.split('#', 1)[0]).name)
                        for r in xml_nested)):
                        identities = document_ids
            if len(identities) != 1:
                raise AIxCodegenValidationException('Canonical identity collision for one generated output: ' +
                    str([(r.definition.identity, r.definition.source_resource) for r in representations]), 'Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.')
            if common_role and len(representations) > 1:
                from eu.algites.tool.codegen.defs.impl.standard.aic_common_contract_projection import merge_common
                common_definitions = []
                for representation in representations:
                    replacements = xml_common_projections.get(id(representation), {})
                    if not replacements:
                        common_definitions.append(representation.definition)
                        continue
                    props = []
                    for field in representation.definition.data_type.properties:
                        item_type = replacements.get(field.source_name)
                        if item_type is None:
                            props.append(field)
                        else:
                            props.append(replace(field, data_type=replace(field.data_type,
                                element_type=item_type)))
                    common_definitions.append(replace(representation.definition,
                        data_type=representation.definition.data_type.with_properties(tuple(props))))
                merged = merge_common(common_definitions)
                # Matching logical identity implies one shared Java interface.
                # An inline XML complex object maps to Map<String,Object> in
                # the current XML emitter, whereas JSON/YAML inline objects
                # have generated nominal interfaces. They cannot override a
                # common typed getter. Reject this *before* writing sources.
                # This check is intentionally limited to actual overlapping
                # representations; XML-only definitions are unaffected.
                xml_parts = [r for r in representations if r.definition.source_kind
                             is AInDefinitionSourceKind.XMLDEFS]
                document_parts = [r for r in representations if r.definition.source_kind in
                                  (AInDefinitionSourceKind.JSONDEFS,
                                   AInDefinitionSourceKind.YAMLDEFS)]
                for xml_rep in xml_parts:
                    for xml_field in xml_rep.definition.data_type.properties:
                        if xml_field.data_type.kind is not AInDataTypeKind.OBJECT:
                            continue
                        if xml_field.data_type.keyed_value_type is not None:
                            # Both sides use the same typed AIiMultiMappedList
                            # API. Its key/value compatibility is checked by
                            # merge_common, never relaxed to Object.
                            continue
                        for doc_rep in document_parts:
                            matching = next((field for field in doc_rep.definition.data_type.properties
                                if field.source_name == xml_field.source_name), None)
                            if matching is not None and matching.data_type.kind is AInDataTypeKind.OBJECT:
                                raise AIxCodegenValidationException('Incompatible shared XML/JSON/YAML getter: '
                                    + xml_rep.definition.logical_name + '.' + xml_field.source_name
                                    + ': XML inline complex type currently emits Map<String,Object> '
                                    + 'but the JSON/YAML contract emits a named interface; '
                                    + 'define compatible schema representations or explicit mapping. '
                                    + 'Sources: ' + xml_rep.definition.source_resource + ' ; '
                                    + doc_rep.definition.source_resource, 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
            else:
                merged = AIcCanonicalDefinitionMerger.merge_strict((r.definition for r in representations),
                    repository, naming_profile=first.naming_profile)
            parent_relations = relations[first.target.value + '#' + generator.generate(first).relative_path]
            def represented_parents(relation):
                result = []
                for unit in relation:
                    request = unit_requests.get((first.target.value, first.contract_role, unit.schema, unit.pointer))
                    if request is None:
                        raise AIxCodegenValidationException('explicit parent has no generated contract in role '
                                         + first.contract_role + ': ' + unit.schema + '#' + unit.pointer, 'Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.')
                    result.append((request.package_name, generator.generate(request).type_name))
                return tuple(result)
            expected_parents = represented_parents(parent_relations[0])
            shared_parents = all(represented_parents(relation) == expected_parents
                                 for relation in parent_relations)
            if not shared_parents and not common_role:
                raise AIxCodegenValidationException('Conflicting explicit parents across schema representations', 'Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.')
            parent_requests = []
            for unit in (parent_relations[0] if shared_parents else ()) :
                inherited = unit_requests.get((first.target.value, first.contract_role, unit.schema, unit.pointer))
                if inherited is None:
                    raise AIxCodegenValidationException('explicit parent has no generated contract in role ' + first.contract_role
                                     + ': ' + unit.schema + '#' + unit.pointer, 'Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.')
                parent_requests.append(inherited)
            parent = None
            additional_parents = []
            inherited_fields = {}
            for inherited in parent_requests:
                if inherited.definition.data_type.kind is not AInDataTypeKind.OBJECT or merged.data_type.kind is not AInDataTypeKind.OBJECT:
                    raise AIxCodegenValidationException('explicit inheritance must connect object contracts', 'Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.')
                for field in inherited.definition.data_type.properties:
                    existing = inherited_fields.setdefault(field.source_name, field)
                    if self._field_shape(existing) != self._field_shape(field):
                        raise AIxCodegenValidationException('Conflicting fields among explicit parents: ' + field.source_name, 'Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.')
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
                            raise AIxCodegenValidationException('Conflicting inherited field: ' + field.source_name, 'Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.')
                        own_fields.append(field)
                merged = replace(merged, data_type=merged.data_type.with_properties(tuple(own_fields)))
            if first.xml_type_qname is not None and first.contract_role != 'common':
                xml_origin = units_by_resource.get(first.definition.source_resource)
                bridge = (xml_inline_bridges.get((first.target.value,
                    xml_origin.schema, xml_origin.pointer)) if xml_origin is not None else None)
                if bridge is not None:
                    preview = generator.generate(bridge)
                    parent_module = bridge.package_name
                    if first.target is AInCodeGenerationTarget.PYTHON:
                        parent_module += '.' + preview.relative_path.rsplit('/', 1)[-1][:-3]
                    additional_parents.append((preview.type_name, parent_module))
            if first.xml_type_qname is not None:
                xml_origin = units_by_resource.get(first.definition.source_resource)
                if xml_origin is None:
                    raise AIxCodegenValidationException(f'Unknown XSD source {first.definition.source_resource}', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
                load = AIcdDefinitionLoadRequest(self._inside(repository, xml_origin.schema),
                    AInDefinitionSourceKind.XMLDEFS, first.naming_profile,
                    profile_by_source[xml_origin.schema])
                parent_qname = (AIcXmlDefsFrontend().named_type_extension_base_qname(load, xml_origin.pointer[6:])
                    if xml_origin.pointer.startswith('@type/')
                    else AIcXmlDefsFrontend().root_extension_base_qname(load))
                if parent_qname is not None:
                    inherited = xml_type_requests.get((first.target, first.contract_role,
                        first.package_name if parent_qname.startswith('{}') else '', parent_qname))
                    if inherited is None or inherited == first:
                        raise AIxCodegenValidationException('XML extension base has no independently emitted contract: '
                            + parent_qname + ' for ' + first.xml_type_qname, 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
                    if merged.data_type.kind is not AInDataTypeKind.OBJECT or inherited.definition.data_type.kind is not AInDataTypeKind.OBJECT:
                        raise AIxCodegenValidationException('XML extension requires object contracts', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
                    inherited_fields = {field.source_name: field for field in inherited.definition.data_type.properties}
                    own_fields = []
                    for field in merged.data_type.properties:
                        base_field = inherited_fields.get(field.source_name)
                        if base_field is None:
                            own_fields.append(field)
                        elif self._field_shape(base_field) != self._field_shape(field):
                            raise AIxCodegenValidationException(f'Incompatible inherited XML extension field: {field.source_name}', 'Compare the derived XSD type with its base. A restriction must not add fields, widen cardinality, or relax inherited type constraints.')
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
                        (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF)):
                    # One top-level choice source is followed by inline payload
                    # definitions, then one selected-value wrapper per branch.
                    # Mapping by index-1 was valid only when payloads were
                    # accidentally not emitted; it breaks multi-branch choices.
                    payload_count = sum(option.kind is AInDataTypeKind.OBJECT
                        for option in merged.data_type.alternatives)
                    wrapper_index = index - 1 - payload_count
                    if 0 <= wrapper_index < len(merged.data_type.alternatives):
                        alternative = merged.data_type.alternatives[wrapper_index]
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
                if (configured and first.contract_role != 'common' and index == 0 and merged.data_type.kind in (
                        AInDataTypeKind.OBJECT, AInDataTypeKind.ONE_OF,
                        AInDataTypeKind.ANY_OF, AInDataTypeKind.REFERENCE)):
                    origin = units_by_resource.get(first.definition.source_resource)
                    common = (unit_requests.get((language, 'common', origin.schema, origin.pointer))
                              if origin is not None else None)
                    if common is not None:
                        preview = generator.generate(common)
                        if language == 'java':
                            declaration = f'public interface {pair.type_name} extends '
                            if merged.data_type.kind in (AInDataTypeKind.OBJECT, AInDataTypeKind.REFERENCE):
                                rendered = rendered.replace(declaration, declaration +
                                    common.package_name + '.' + preview.type_name + ', ')
                            else:
                                declaration = f'public sealed interface {pair.type_name}'
                                start = rendered.find(declaration)
                                if start < 0:
                                    raise AIxCodegenValidationException('Expected closed choice interface: ' + pair.type_name, 'Check that each choice/enum branch is declared once with a supported, resolvable type and that any required choice annotation is present.')
                                permits = rendered.find(' permits ', start + len(declaration))
                                if permits < 0:
                                    raise AIxCodegenValidationException('Expected closed choice permit list: ' + pair.type_name, 'Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.')
                                suffix = rendered[start + len(declaration):permits]
                                common_parent = common.package_name + '.' + preview.type_name
                                if suffix.startswith(' extends '):
                                    suffix += ', ' + common_parent
                                elif not suffix:
                                    suffix = ' extends ' + common_parent
                                else:
                                    raise AIxCodegenValidationException('Unexpected sealed choice declaration: ' + suffix, 'Check that each choice/enum branch is declared once with a supported, resolvable type and that any required choice annotation is present.')
                                rendered = rendered[:start + len(declaration)] + suffix + rendered[permits:]
                        else:
                            stem = preview.relative_path.rsplit('/', 1)[-1].removesuffix('.py')
                            rendered = rendered.replace('from __future__ import annotations\n',
                                'from __future__ import annotations\nfrom ' + common.package_name +
                                '.' + stem + ' import ' + preview.type_name + '\n')
                            declaration = f'class {pair.type_name}('
                            if declaration in rendered:
                                rendered = rendered.replace(declaration,
                                    declaration + preview.type_name + ', ')
                            else:
                                rendered = rendered.replace(f'class {pair.type_name}:',
                                    f'class {pair.type_name}({preview.type_name}):')
                rendered = self._qualify_references(rendered, first, requests, True, choice_reference)
                if first.xml_type_qname is not None and first.contract_role != 'common' and index == 0 and merged.data_type.kind in (
                        AInDataTypeKind.OBJECT, AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
                    namespace = first.xml_type_qname[1:].split('}', 1)[0]
                    wildcard_fields = {}
                    for field in merged.data_type.properties:
                        xml = field.xml_field
                        if xml is None or not xml.wildcard_namespace:
                            continue
                        selected = xml_namespaces.namespace_of_wildcard(xml.wildcard_namespace, xml.namespace)
                        wildcard_fields[field.source_name] = (namespace_ref(language, selected, first)
                            if selected is not None else
                            ('eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object.AIiXmlDataObject'
                                if language == 'python' else
                                'eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject'))
                    rendered = xml_namespaces.decorate(rendered, first,
                        namespace_ref(language, namespace, first), wildcard_fields, language == 'python')
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
            local_types, local_elements, local_value_types = {}, {}, {}
            for schema, pointer, req in xml_requests:
                loaded = AIcdDefinitionLoadRequest(self._inside(repository, schema),
                    AInDefinitionSourceKind.XMLDEFS, req.naming_profile,
                    profile_by_source[schema])
                if pointer.startswith('@type/') and xml_frontend.is_synthetic_choice_type_name(
                        loaded.path, pointer[6:]):
                    continue
                root_qname = req.xml_type_qname or xml_frontend.root_type_qname(loaded)
                if req.definition.data_type.kind in (AInDataTypeKind.OBJECT, AInDataTypeKind.ENUM,
                        AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
                    if req.definition.data_type.kind in (AInDataTypeKind.ENUM,
                            AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
                        (local_value_types.setdefault(schema, set()) if root_qname.startswith('{}')
                            else value_types).add(root_qname)
                    preview = generator.generate(req)
                    qualified = req.package_name + '.' + (preview.relative_path.rsplit('/', 1)[-1][:-3] + '.'
                        if language == 'python' else '') + preview.type_name
                    types = local_types.setdefault(schema, {}) if root_qname.startswith('{}') else type_index
                    if root_qname in types and types[root_qname] != qualified:
                        raise AIxCodegenValidationException('Duplicate XML content type: ' + root_qname + ' in ' + schema, 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
                    types[root_qname] = qualified
                if pointer:
                    continue
                for element in xml_frontend.global_element_declarations(loaded):
                    element_name = generator.names.render(
                        xml_identifier(element.local_name), req.definition.version, req.naming_profile,
                        AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE)
                    stem = generator.names.render(xml_identifier(element.local_name), req.definition.version,
                        req.naming_profile, AInDefsNameRole.XML_ELEMENT_INTERFACE_TYPE_FILE_STEM)
                    qualified = req.package_name + '.' + (stem + '.' if language == 'python' else '') + element_name
                    elements = local_elements.setdefault(schema, {}) if not element.namespace else element_index
                    if element.qname in elements:
                        raise AIxCodegenValidationException('Duplicate XML global element: ' + element.qname + ' in ' + schema, 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
                    elements[element.qname] = qualified
                    declarations.append((schema, req, element))
            for schema, req, element in declarations:
                generated = xml_generator.generate(req, element,
                    {**type_index, **local_types.get(schema, {})},
                    {**element_index, **local_elements.get(schema, {})},
                    value_types | local_value_types.get(schema, set()))
                output_root = output_roots.get(language, intf / 'src/product' / (language + '.gen'))
                element_namespace = element.namespace
                owner_key = namespace_key(language, element_namespace, req)
                if owner_key not in xml_namespace_owners:
                    xml_namespace_owners[owner_key] = req
                rendered = xml_namespaces.decorate(generated.source, req,
                    namespace_ref(language, element_namespace, req), {}, language == 'python')
                self._add(pending, output_root / generated.relative_path, rendered)
                result.append(dict(schema=schema, pointer='@element/' + element.local_name,
                    language=language, type=generated.type_name,
                    path=(output_root / generated.relative_path).relative_to(repository).as_posix()))

        for (language, namespace, _source), owner in sorted(xml_namespace_owners.items()):
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
                    raise AIxCodegenValidationException(f'Stale generated binding: {stale}', 'Review the indicated source declaration and the generator contract. Correct the incompatible input rather than editing the generated outputs.')
                stale.unlink()
        for path, source in sorted(pending.items()):
            if check:
                if not path.is_file() or path.read_text(encoding='utf-8') != source:
                    raise AIxCodegenValidationException(f'Missing or outdated generated binding: {path}', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
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
    def _canonical_identity(definition, package_name, units_by_resource, declared_identity_by_source):
        """Normalize only format-specific publication aliases, never arbitrary schema IDs."""
        origin = units_by_resource[definition.source_resource]
        if not declared_identity_by_source.get(origin.schema, False) and (
                definition.source_kind is not AInDefinitionSourceKind.XMLDEFS
                                or definition.identity == definition.logical_name):
            return ('implicit', package_name, definition.logical_name, definition.version, origin.pointer)
        identity = str(definition.identity)
        identity = re.sub(r'(/api/)(?:yamldefs|jsondefs|xmldefs)(/)', r'\1schema\2', identity)
        identity = re.sub(r'\.(?:yamldef|jsondef)\.schema\.json(?=#|$)|\.xsd(?=#|$)',
                          '.schema', identity)
        return ('explicit', identity, definition.version)

    @staticmethod
    def _common_explicit_matches_implicit(explicit, implicit):
        """Accept exact format aliases only, without weakening explicit identity checks.

        An XML schema often uses ``package.logical-name`` as its namespace,
        whereas JSON/YAML formats without a declared logical ID use an implicit
        ``(package, logical-name, version)`` identity. The dotted form is a
        structural alias only for a root contract, never a nested definition.
        Existing Algites URN aliases retain their original guarded behaviour.
        """
        if explicit[0] != 'explicit' or implicit[0] != 'implicit':
            return False
        _, package, name, version, pointer = implicit
        if explicit[2] != version:
            return False
        candidate = str(explicit[1])
        return ((not pointer and candidate == package + '.' + name)
                or (candidate.startswith('urn:algites:')
                    and candidate.endswith(f':{name}:{version}')))

    @staticmethod
    def _common_identity(definition, package_name, identity):
        """Normalize proven serialization aliases of the same common contract.

        Recognize an exact publication URL for a versioned root schema only
        when its path matches the package, logical schema name and version.
        Existing strictly guarded legacy URN aliases remain supported.
        Unrelated namespace URIs do not become equivalent merely because
        their generated declarations share a simple name.
        """
        if identity[0] != 'explicit':
            return identity
        value = str(identity[1])
        if ('#' not in definition.source_resource
                and value.startswith('https://defs.dev.algites.eu/api/schema/')
                and definition.version is not None):
            # A publication URL is the exact global XSD namespace, whereas the
            # format-neutral JSON/YAML contract has an explicit logical ID.
            # Only match the URL when its directory maps to the generated
            # package and its versioned filename maps to the logical schema.
            expected = ('https://defs.dev.algites.eu/api/schema/'
                + package_name.replace('.', '/') + '/'
                + definition.logical_name + '_' + str(definition.version) + '.schema')
            if value == expected:
                return ('explicit', package_name + '.' + definition.logical_name,
                        definition.version)
        if (definition.source_kind.name == 'XMLDEFS' and
                package_name.startswith('eu.algites.') and
                definition.version is not None):
            suffix = package_name.removeprefix('eu.algites.').replace('.', ':')
            expected = (f'urn:eu:algites:{suffix}:'
                        f'{definition.logical_name}:{definition.version}')
            if value == expected:
                return ('explicit', package_name + '.' + definition.logical_name,
                        definition.version)
        if value.startswith('urn:algites:'):
            name = {'YAMLDEFS': 'yamldef', 'JSONDEFS': 'jsondef'}.get(
                definition.source_kind.name)
            if name:
                return ('explicit', value.replace(':' + name + ':', ':', 1),
                        definition.version)
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
        """Resolve only explicit Defs Codegen parents; constraints never define inheritance."""
        references = unit.node.get('x-algites-defscodegen-extends', [])
        if not isinstance(references, list) or any(not isinstance(item, str) for item in references):
            raise AIxCodegenValidationException('x-algites-defscodegen-extends must be an array of URI references', 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')
        parents = []
        for reference in references:
            parts = urlsplit(reference)
            if parts.fragment and not unquote(parts.fragment).startswith('/'):
                raise AIxCodegenValidationException('Unsupported explicit parent anchor: ' + reference, 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')
            if parts.scheme and parts.scheme != 'file':
                matches = [candidate for candidate in index.values()
                    if candidate.document.get('$id') == reference.split('#', 1)[0]
                    and candidate.pointer == unquote(parts.fragment)]
                if len(matches) != 1:
                    raise AIxCodegenValidationException('Unresolved or ambiguous explicit parent: ' + reference, 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')
                parents.append(matches[0])
                continue
            if parts.scheme == 'file':
                target = Path(unquote(parts.path))
            else:
                target = (repository / unit.schema).parent / unquote(parts.path) if parts.path else repository / unit.schema
            target = Path(os.path.abspath(target))
            if not target.is_relative_to(repository):
                raise AIxCodegenValidationException('explicit parent escapes repository: ' + reference, 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')
            pointer = unquote(parts.fragment)
            parent = index.get((target.relative_to(repository).as_posix(), pointer))
            if parent is None:
                raise AIxCodegenValidationException('explicit parent is not an emitted contract: ' + reference, 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')
            parents.append(parent)
        if len({(unit.schema, unit.pointer) for unit in parents}) != len(parents):
            raise AIxCodegenValidationException('Duplicate explicit parent in ' + unit.schema, 'Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.')
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
                if r.target is request.target and (r.definition.source_resource.split('#', 1)[0] == local
                    or (published is not None and
                        (r.definition.source_resource.split('#', 1)[0] == published or
                         r.definition.source_resource.split('#', 1)[0].endswith('/' + published)))
                    or r.definition.identity == resource)}
            if len(candidates) != 1:
                raise AIxCodegenValidationException(f'Cannot resolve generated reference package: {ref.identity} in {owner}', 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')
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

    def _collect(self, node, pointer, name, schema, document, overrides, result,
                 source_catalog, source_profile):
        """Discover schema contracts; named definitions retain local type identity.

        Named ``$defs`` contracts have an independently validated local name.
        Their schema-qualified identity remains the containing schema plus the
        exact JSON Pointer, and is never guessed from the document filename.
        """
        if not isinstance(node, dict):
            return
        override = overrides.get(schema + '#' + pointer)
        if override is not None and override.get('common_one_of_fields', False):
            raise AIxCodegenValidationException('common_one_of_fields is obsolete: declare shared properties directly', 'Check that each choice/enum branch is declared once with a supported, resolvable type and that any required choice annotation is present.')
        if not pointer or pointer.endswith('/additionalProperties') or node.get('type') == 'object' or 'properties' in node or 'enum' in node or 'x-algites-defscodegen-choice' in node:
            result.append(self.AIcdUnit(schema, pointer, override['name'] if override is not None else name, node, document))
        for keyword in ('properties', '$defs', 'definitions', 'patternProperties'):
            for key, value in node.get(keyword, {}).items():
                token = key.replace('~', '~0').replace('/', '~1')
                if keyword in ('$defs', 'definitions'):
                    from .aic_declared_type_identity import canonical_type_identifier
                    try:
                        child_name = canonical_type_identifier(source_catalog, source_profile, key)
                    except ValueError as failure:
                        raise AIxCodegenValidationException(
                            str(failure),
                            'Rename this $defs/definitions type according to the selected '
                            'type_name profile and update all $ref references. '
                            'Do not rename ordinary document property names.',
                            source=str(schema),
                            location='#' + pointer + '/' + keyword + '/' + token) from failure
                else:
                    child_name = name + ('-pattern-' if keyword == 'patternProperties' else '-') + self._kebab(key)
                self._collect(value, pointer + '/' + keyword + '/' + token,
                    child_name, schema, document, overrides, result,
                    source_catalog, source_profile)
        for keyword in ('items', 'additionalProperties'):
            self._collect(node.get(keyword), pointer + '/' + keyword,
                name + '-' + self._kebab(keyword), schema, document, overrides,
                result, source_catalog, source_profile)
        for keyword in ('prefixItems',):
            for index, value in enumerate(node.get(keyword, ())):
                self._collect(value, pointer + '/' + keyword + '/' + str(index),
                    name + '-' + self._kebab(keyword) + '-' + str(index),
                    schema, document, overrides, result, source_catalog, source_profile)

    @staticmethod
    def _kebab(name):
        return re.sub(r'[^A-Za-z0-9]+', '-', re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', name)).strip('-').lower()

    @staticmethod
    def _inside(repository, relative):
        path = Path(os.path.abspath(repository / relative))
        if Path(relative).is_absolute() or not path.is_relative_to(repository):
            raise AIxCodegenValidationException(f'Path escapes repository: {relative}', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
        return path

    @staticmethod
    def _add(pending, path, source):
        path = Path(os.path.normpath(path))
        if path in pending:
            raise AIxCodegenValidationException(f'Generated type collision: {path}', 'Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.')
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
