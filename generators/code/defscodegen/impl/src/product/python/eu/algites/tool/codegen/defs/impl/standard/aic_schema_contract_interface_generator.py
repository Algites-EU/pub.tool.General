"""Native first-stage generator from canonical Defs into read-only contracts."""
from __future__ import annotations

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException

import keyword
import re
from eu.algites.tool.codegen.defs.impl.standard.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
from eu.algites.tool.codegen.defs.impl.standard.aic_generation_names import AIcGenerationNames
from eu.algites.tool.codegen.defs.impl.standard.aic_scalar_generation import scalar_type
from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.aicd_generated_source import AIcdGeneratedSource
from eu.algites.tool.codegen.defs.aicd_generated_type_identity import AIcdGeneratedTypeIdentity
from ._recursive_contract_type import contract_type
from ._setter_inheritance_policy_configuration import effective_default


_TECHNOLOGY_DATA_OBJECT = {
    AInDefinitionSourceKind.XMLDEFS: ('eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object', 'AIiXmlDataObject', 'eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject'),
    AInDefinitionSourceKind.JSONDEFS: ('eu.algites.lib.data.dataobject.jsondefs.aii_json_data_object', 'AIiJsonDataObject', 'eu.algites.lib.data.dataobject.jsondefs.AIiJsonDataObject'),
    AInDefinitionSourceKind.YAMLDEFS: ('eu.algites.lib.data.dataobject.yamldefs.aii_yaml_data_object', 'AIiYamlDataObject', 'eu.algites.lib.data.dataobject.yamldefs.AIiYamlDataObject'),
}

def _visible_title(title, name):
    if title:
        return title
    value = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2',
        re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', name)).replace('_', ' ').replace('-', ' ').strip()
    return value[0].upper() + value[1:] if value else name


def _nested_array_type(data_type, java=False):
    """Map array-of-array scalar leaves without collapsing inner dimensions."""
    if data_type.kind is AInDataTypeKind.ARRAY:
        inner = _nested_array_type(data_type.element_type, java)
        return f'java.util.List<{inner}>' if java else f'tuple[{inner}, ...]'
    from eu.algites.tool.codegen.defs.impl.standard.aic_scalar_generation import scalar_type
    kinds = {AInDataTypeKind.STRING: AInDataTypeKind.STRING,
             AInDataTypeKind.INTEGER: AInDataTypeKind.INTEGER,
             AInDataTypeKind.NUMBER: AInDataTypeKind.NUMBER,
             AInDataTypeKind.BOOLEAN: AInDataTypeKind.BOOLEAN,
             AInDataTypeKind.ANY: AInDataTypeKind.ANY}
    if data_type.kind not in kinds:
        raise AIxCodegenValidationException(f'Nested {data_type.kind.name} requires a generated named contract', 'Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.')
    return scalar_type(kinds[data_type.kind], data_type.constraints, java)


def _property_name(value):
    name = re.sub(r'[^a-zA-Z0-9_]', '_', value)
    if not name or name[0].isdigit():
        name = '_' + name
    return name + '_' if keyword.iskeyword(name) else name


def _synthetic_entry_value_type(model, request, names, *, java=False, imports=None):
    """Render the typed value of a virtual JSON/YAML map entry.

    Args:
        model: Canonical synthetic additionalProperties value contract.
        request: Generation request with an explicit naming profile.
        names: Structure-aware type name renderer.
        java: True for Java return types; false for Python.
        imports: Mutable Python import set; unused for Java.

    Returns:
        A strongly typed Java or Python declaration without an Object/Any fallback.

    Raises:
        ValueError: If the recursive value type cannot be expressed safely.
    """
    def node(shape, logical):
        if shape.kind is AInDataTypeKind.ARRAY:
            value_type = node(shape.element_type, logical + '-items')
            return f'java.util.List<? extends {value_type}>' if java else f'tuple[{value_type}, ...]'
        if shape.kind is AInDataTypeKind.REFERENCE:
            reference = shape.reference
            role = AInDefsNameRole.ENUM_TYPE if reference.targets_enum else AInDefsNameRole.INTERFACE_TYPE
            filename_role = (AInDefsNameRole.ENUM_TYPE_FILE_STEM if reference.targets_enum
                             else AInDefsNameRole.INTERFACE_TYPE_FILE_STEM)
            typename = names.render(reference.logical_name, reference.version, request.naming_profile, role)
            if not java and imports is not None:
                filename = names.render(reference.logical_name, reference.version, request.naming_profile, filename_role)
                imports.add(f'from .{filename} import {typename}')
            return typename
        if shape.kind in (AInDataTypeKind.OBJECT, AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
            typename = names.render(logical, model.version, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE)
            if not java and imports is not None:
                filename = names.render(logical, model.version, request.naming_profile,
                    AInDefsNameRole.INTERFACE_TYPE_FILE_STEM)
                imports.add(f'from .{filename} import {typename}')
            return typename
        if shape.kind is AInDataTypeKind.ENUM:
            typename = names.render(logical, model.version, request.naming_profile, AInDefsNameRole.ENUM_TYPE)
            if not java and imports is not None:
                filename = names.render(logical, model.version, request.naming_profile,
                    AInDefsNameRole.ENUM_TYPE_FILE_STEM)
                imports.add(f'from .{filename} import {typename}')
            return typename
        result = scalar_type(shape.kind, shape.constraints, java=java)
        if result in ('Object', 'Any'):
            raise AIxCodegenValidationException('Untyped synthetic map value cannot be widened to Object/Any: ' + model.source_resource, 'Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.')
        if result == 'Decimal' and imports is not None:
            imports.add('from decimal import Decimal')
        if result in ('AIcSchemaTemporalValue', 'AIcSchemaDuration'):
            raise AIxCodegenValidationException('Temporal synthetic map values require explicit named contracts: ' + model.source_resource, 'Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.')
        return result
    return node(model.data_type, model.logical_name)


class AIcSchemaContractInterfaceGenerator:
    """Generate importable AIig and AIng sources without generating any DTO."""

    def __init__(self):
        self.names = AIcGenerationNames()

    def generate(self, request, parent: tuple[str, str] | None = None) -> AIcdGeneratedSource:
        """Generate canonical read contracts and preserve the explicit parent edge."""
        if request.definition.data_type.kind in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
            if parent is not None:
                raise AIxCodegenValidationException('Closed choice cannot inherit object contracts', 'Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.')
            from .aic_closed_choice_generator import AIcClosedChoiceGenerator
            return AIcClosedChoiceGenerator().generate(request)[0]
        if request.definition.data_type.kind is AInDataTypeKind.ENUM:
            if parent is not None:
                raise AIxCodegenValidationException('Enums cannot inherit object contracts', 'Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.')
            return AIcDefaultDefsCodegenService().generate(request)
        if request.target is not AInCodeGenerationTarget.PYTHON:
            return self._generate_java(request, parent)
        return self._generate_python(request, parent)

    def generate_sources(self, request, parent=None):
        """Return every independently compiled source, including closed-choice wrappers."""
        if request.definition.data_type.kind in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
            if parent is not None:
                raise AIxCodegenValidationException('Closed choice cannot inherit object contracts', 'Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.')
            from .aic_closed_choice_generator import AIcClosedChoiceGenerator
            return AIcClosedChoiceGenerator().generate(request)
        return (self.generate(request, parent),)

    def _generate_python(self, request, parent):
        model = request.definition
        interface = self.names.type_name(model, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE)
        stem = self.names.file_stem(model, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE_FILE_STEM)
        path = request.package_name.replace('.', '/') + '/' + stem + '.py'
        ref_imports = set()
        fields = []
        getter_rows = []
        metadata_rows = []
        label_rows = []
        xml_field_rows = []
        xml_key_rows = []
        has_temporal = False
        for field_order, prop in enumerate(model.data_type.properties):
            # SchemaMetadataNaming defines transport metadata, not domain fields.
            # Compare the original wire name, never a normalized accessor name.
            if prop.source_name in (
                    model.data_source_schema_url_field,
                    model.data_source_schema_identifier_field,
                    model.data_source_schema_version_field,
            ) and prop.source_name:
                continue
            name = _property_name(self.names.property_name(prop.source_name, request.naming_profile))
            getter_name = self.names.getter_name(prop.source_name, request.naming_profile)
            field_type = contract_type(prop, request, self.names, imports=ref_imports)
            if 'AIcSchemaTemporalValue' in field_type or 'AIcSchemaDuration' in field_type:
                has_temporal = True
            reference = prop.data_type.referenced_definition()
            array = prop.data_type.kind is AInDataTypeKind.ARRAY
            kind_type = field_type
            if reference is not None and not array:
                kind_type = self.names.render(reference.logical_name, reference.version, request.naming_profile,
                    AInDefsNameRole.ENUM_TYPE if reference.targets_enum else AInDefsNameRole.INTERFACE_TYPE)
            if prop.nullable:
                field_type += ' | None'
            fields.append(f'    {name}: {field_type}')
            constant = self.names.schema_field_name_constant(prop.source_name, request.naming_profile)
            fields.append(f'    {constant}: ClassVar[str] = {prop.source_name!r}')
            title = _visible_title(prop.title, prop.source_name)
            entries = (f'(AIaFieldLabel.Entry(roleCode=AIaFieldLabel.FIELD_DESCRIPTION, label={prop.description!r}),)'
                if prop.description else '()')
            if prop.data_type.kind is AInDataTypeKind.ARRAY and prop.data_type.key_definitions:
                xml_key_rows.append('        ' + repr(prop.source_name) + ': '
                    + repr(tuple((entry.name, tuple(entry.fields), entry.required)
                                 for entry in prop.data_type.key_definitions)) + ',')
            if prop.xml_field is not None:
                wire = prop.xml_field
                xml_field_rows.append(f'        {prop.source_name!r}: AIaXmlDataObjectField('
                    f'namespace={wire.namespace!r}, namespace_local_name={wire.namespace_local_name!r}, '
                    f'value_kind=AInXmlValueKind.{wire.value_kind.name}, order={field_order}, '
                    f'min_occurs={wire.min_occurs}, max_occurs={wire.max_occurs}, '
                    f'wildcard_namespace={wire.wildcard_namespace!r}, '
                    f'wildcard_process_contents={wire.wildcard_process_contents!r}),')
            label_rows.append(f'        {prop.source_name!r}: AIaFieldLabel(label={title!r}, labels={entries}),')
            # A common contract and its XML/JSON/YAML implementations must expose
            # the same semantic type. Restricting expected_type to XMLDEFS makes
            # unrelated branches of the generated inheritance diamond conflict.
            expected_type = {
                AInDataTypeKind.STRING: 'str', AInDataTypeKind.INTEGER: 'int',
                AInDataTypeKind.NUMBER: 'Decimal', AInDataTypeKind.BOOLEAN: 'bool',
            }.get(prop.data_type.kind)
            if array:
                expected_type = 'AIiMultiMappedList' if prop.data_type.key_definitions else 'list'
            field_decorator = ('    @AIaDataObjectField(field_name=' + repr(prop.source_name)
                + ', presence=AInFieldPresenceKind.' + prop.presence.name
                + ', allows_null=' + str(bool(prop.nullable))
                + (', expected_type=' + expected_type if expected_type else '')
                + ', setter_inheritance_policy=AInFieldSetterInheritancePolicy.' + effective_default().name + ')')
            if expected_type == 'AIiMultiMappedList':
                ref_imports.add('from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList')
            getter_type = ''
            if ((reference is not None and not array and not reference.targets_enum)
                    or (array and prop.data_type.element_type is not None
                        and prop.data_type.element_type.referenced_definition() is not None)):
                getter_type = f' -> {kind_type}' + (' | None' if prop.nullable else '')
            getter_rows.extend([field_decorator, f'    @AIaFieldLabel(label={title!r}, labels={entries})',
                '    @abstractmethod', f'    def {getter_name}(self){getter_type}:',
                f'        """Return {prop.description or prop.source_name}.\n\n        Returns:\n            Value of {prop.source_name} according to the generated schema contract.\n        """',
                '        raise NotImplementedError', ''])
        if (request.contract_role != 'common'
                and model.source_kind in (AInDefinitionSourceKind.JSONDEFS, AInDefinitionSourceKind.YAMLDEFS)
                and model.source_resource.endswith('/additionalProperties')):
            synthetic_name = request.naming_profile.multi_mapped_list_key_synthetic_getter()
            getter_rows.extend(['    @abstractmethod',
                f'    def {synthetic_name}(self) -> str:',
                '        """Return the parent object property key without writing it as a value field."""',
                '        raise NotImplementedError', ''])
        if (request.contract_role != 'common'
                and model.source_kind in (AInDefinitionSourceKind.JSONDEFS, AInDefinitionSourceKind.YAMLDEFS)
                and model.source_resource.endswith('/additionalProperties')
                and model.data_type.kind not in (AInDataTypeKind.OBJECT, AInDataTypeKind.ENUM)):
            value_name = request.naming_profile.multi_mapped_list_value_synthetic_getter()
            value_type = _synthetic_entry_value_type(model, request, self.names, imports=ref_imports)
            getter_rows.extend(['    @abstractmethod', f'    def {value_name}(self) -> {value_type}:',
                '        """Return the typed JSON/YAML property value without serializing this getter.',
                '', '        Returns:',
                '            The original typed property value associated with the synthetic key.',
                '        """', '        raise NotImplementedError', ''])
        parent_import = ''
        base_module, base_type, _ = _TECHNOLOGY_DATA_OBJECT[model.source_kind]
        if request.contract_role == 'common':
            base_module, base_type = ('eu.algites.lib.data.dataobject.aii_data_object', 'AIiDataObject')
        parent_name = base_type + ', ABC'
        if (model.data_type.keyed_value_type is not None and parent is None
                and request.common_naming_profile is None):
            ref_imports.add('from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList')
            key_type = self.names.render(model.logical_name + '-additional-properties',
                model.version, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE)
            key_file = self.names.render(model.logical_name + '-additional-properties',
                model.version, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE_FILE_STEM)
            ref_imports.add(f'from .{key_file} import {key_type}')
            parent_name += f', AIiMultiMappedList[{key_type}]'
        if parent:
            parent_name, parent_module = parent
            parent_import = f'from {parent_module} import {parent_name}\n'
        helpers = ('from dataclasses import dataclass\n\n'
            '@dataclass(frozen=True, slots=True)\nclass AIcSchemaTemporalValue:\n'
            '    lexical: str\n    data_type: str\n\n'
            '@dataclass(frozen=True, slots=True)\nclass AIcSchemaDuration:\n'
            '    lexical: str\n\n') if has_temporal else ''
        xml_imports, xml_metadata = '', ''
        if request.xml_type_qname is not None:
            namespace, local = request.xml_type_qname[1:].split('}', 1)
            xml_imports = ('from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject\n'
                'from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind\n')
            xml_metadata = ('    __xml_data_object__ = AIaXmlDataObject('
                f'definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace={namespace!r}, '
                f'namespace_local_name={local!r})\n')
        if xml_key_rows:
            xml_metadata += ('    __xml_key_definitions__ = {\n'
                + '\n'.join(xml_key_rows) + '\n    }\n')
        if xml_field_rows:
            xml_imports += ('from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field import AIaXmlDataObjectField\n'
                'from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind\n')
            xml_metadata += ('    __xml_data_object_fields__ = {\n' + '\n'.join(xml_field_rows) + '\n    }\n')
        source = ('from __future__ import annotations\n' + parent_import
            + '\nfrom abc import ABC, abstractmethod\n'
            + 'from typing import Any, ClassVar, Mapping\nfrom decimal import Decimal\n'
            + f'from {base_module} import {base_type}\n'
            + 'from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n'
            + 'from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField\n'
            + 'from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy\n'
            + 'from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind\n'
            + 'from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel\n'
            + xml_imports
            + '\n'.join(sorted(ref_imports)) + '\n\n' + helpers
            + f'class {interface}({parent_name}):\n'
            + f'    """Read-only generated contract for {model.logical_name}.\n\n    Author: linhart1.\n    """\n'
            + '    __data_object__ = AIcdDataObject('
            + (f'schema_id={model.identity!r}, ' if model.schema_source_schema_identifier_field != '' else '')
            + (f'schema_version={model.version if model.version is not None else -1}, ' if model.schema_source_schema_version_field != '' else '')
            + (f'schema_url={model.schema_url!r}, ' if model.schema_source_schema_url_field != '' else '')
            + f'title={_visible_title(model.title, model.logical_name)!r}'
            + (f', data_source_schema_url_field={model.data_source_schema_url_field!r}' if model.data_source_schema_url_field else '')
            + (f', data_source_schema_identifier_field={model.data_source_schema_identifier_field!r}' if model.data_source_schema_identifier_field else '')
            + (f', data_source_schema_version_field={model.data_source_schema_version_field!r}' if model.data_source_schema_version_field else '')
            + f', description={(model.description or "")!r}, '
            + f'naming_convention={request.naming_convention!r}, setter_inheritance_policy=AInFieldSetterInheritancePolicy.{effective_default().name})\n'
            + xml_metadata
            + '    __field_labels__ = {\n' + '\n'.join(label_rows)
            + '\n    }\n\n' + '\n'.join(fields)
            + '\n\n    __slots__ = ()\n\n' + '\n'.join(getter_rows) + '\n')
        return AIcdGeneratedSource(interface, path, source,
            (AIcdGeneratedTypeIdentity.from_request(request, interface, path, AInDefsNameRole.INTERFACE_TYPE),))

    def _generate_java(self, request, parent):
        # Java rendering here is the Python implementation of the canonical
        # contract model; it must not invoke the paired DTO renderer.
        from eu.algites.tool.codegen.defs.impl.standard._support import _java_quote, _java_integer, _java_type
        from eu.algites.tool.codegen.defs.impl.standard.aic_scalar_generation import java_identifier
        model = request.definition
        interface = self.names.type_name(model, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE)
        stem = self.names.file_stem(model, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE_FILE_STEM)
        if stem != interface:
            raise AIxCodegenValidationException(f'Java public interface and source filename must agree: {interface} vs {stem}', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
        path = request.package_name.replace('.', '/') + '/' + stem + '.java'
        extends = ((parent[1] + '.' + parent[0]) if parent else
            ('eu.algites.lib.data.dataobject.AIiDataObject' if request.contract_role == 'common' else
                _TECHNOLOGY_DATA_OBJECT[model.source_kind][2]))
        if (model.data_type.keyed_value_type is not None and parent is None
                and request.common_naming_profile is None):
            key_type = self.names.render(model.logical_name + '-additional-properties',
                model.version, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE)
            extends += ', eu.algites.lib.common.list.AIiMultiMappedList<' + key_type + '>'
        rows = [f'package {request.package_name};', '',
            '/**\n * Generated schema contract. Do not edit manually.\n *\n * @author linhart1\n */',
            '@eu.algites.lib.data.dataobject.AIaDataObject('
            + ('schemaId = ' + _java_quote(model.identity) + ', ' if model.schema_source_schema_identifier_field != '' else '')
            + ('schemaVersion = ' + str(model.version if model.version is not None else -1) + ', ' if model.schema_source_schema_version_field != '' else '')
            + ('schemaUrl = ' + _java_quote(model.schema_url) + ', ' if model.schema_source_schema_url_field != '' else '')
            + 'title = ' + _java_quote(_visible_title(model.title, model.logical_name))
            + (', dataSourceSchemaUrlField = ' + _java_quote(model.data_source_schema_url_field) if model.data_source_schema_url_field else '')
            + (', dataSourceSchemaIdentifierField = ' + _java_quote(model.data_source_schema_identifier_field) if model.data_source_schema_identifier_field else '')
            + (', dataSourceSchemaVersionField = ' + _java_quote(model.data_source_schema_version_field) if model.data_source_schema_version_field else '')
            + ', description = ' + _java_quote(model.description or '')
            + ', namingConvention = ' + _java_quote(request.naming_convention)
            + ', setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.' + effective_default().name + ')',
            f'public interface {interface} extends {extends} {{',
            '    /** Canonical schema ID independent of any representation-specific publication URL. */',
            f'    String CANONICAL_SOURCE_ID = {_java_quote(model.identity)};',
            '    /** Version identifying the canonical schema definition. */',
            f'    Integer CANONICAL_SOURCE_VERSION = {_java_integer(model.version)};',
            '    /** Published URL of the schema representation, separate from its logical identifier. */',
            f'    String CANONICAL_SOURCE_URL = {_java_quote(model.schema_url)};',
            '    /** Definition source resource retained for provenance and diagnostics. */',
            f'    String CANONICAL_SOURCE_RESOURCE = {_java_quote(model.source_resource)};']
        if request.xml_type_qname is not None:
            namespace, local = request.xml_type_qname[1:].split('}', 1)
            rows.insert(4, '@eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject('
                'definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, '
                + 'namespace = ' + _java_quote(namespace) + ', namespaceLocalName = ' + _java_quote(local) + ')')
        for field_order, prop in enumerate(model.data_type.properties):
            # SchemaMetadataNaming defines transport metadata, not domain fields.
            # Compare the original wire name, never a normalized accessor name.
            if prop.source_name in (
                    model.data_source_schema_url_field,
                    model.data_source_schema_identifier_field,
                    model.data_source_schema_version_field,
            ) and prop.source_name:
                continue
            desc = re.sub(r'\s+', ' ', (prop.description or f'Canonical field {prop.source_name}.').replace('*/', '* /')).replace('<', '&lt;').replace('>', '&gt;')
            name = java_identifier(self.names.property_name(prop.source_name, request.naming_profile))
            typ = contract_type(prop, request, self.names, java=True)
            title = _visible_title(prop.title, prop.source_name)
            entries = (', labels = {@eu.algites.lib.common.object.props.labels.AIaFieldLabel.Entry(roleCode = eu.algites.lib.common.object.props.labels.AIaFieldLabel.FIELD_DESCRIPTION, label = '
                + _java_quote(prop.description) + ')}') if prop.description else ''
            rows.extend([f'    /** <strong>Field Name:</strong> {{@code {prop.source_name}}}. {desc} */',
                f'    String {self.names.schema_field_name_constant(prop.source_name, request.naming_profile)} = {_java_quote(prop.source_name)};',
                f'    /** {desc}\n     * @return value of the {{@code {prop.source_name}}} schema field; see the field presence and nullability annotations\n     */',
                f'    @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = {_java_quote(title)}{entries})',
                '    @eu.algites.lib.data.dataobject.AIaDataObjectField(fieldName = '
                    + _java_quote(prop.source_name)
                    + ', presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.' + prop.presence.name
                    + ', allowsNull = ' + str(bool(prop.nullable)).lower()
                    + ', setterInheritancePolicy = eu.algites.lib.data.dataobject.AInFieldSetterInheritancePolicy.' + effective_default().name + ')'])
            if prop.data_type.kind is AInDataTypeKind.ARRAY:
                for key in prop.data_type.key_definitions:
                    fields = ', '.join(_java_quote(field) for field in key.fields)
                    rows.append('    @eu.algites.lib.data.dataobject.xmldefs.AIaXmlKeyDefinition('
                                + 'name = ' + _java_quote(key.name) + ', fields = {' + fields + '}, required = ' + str(bool(key.required)).lower() + ')')
            if prop.xml_field is not None:
                wire = prop.xml_field
                rows.append('    @eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField('
                    + 'namespace = ' + _java_quote(wire.namespace)
                    + ', namespaceLocalName = ' + _java_quote(wire.namespace_local_name)
                    + ', valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.'
                    + wire.value_kind.name + ', order = ' + str(field_order)
                    + ', minOccurs = ' + str(wire.min_occurs) + ', maxOccurs = ' + str(wire.max_occurs)
                    + ', wildcardNamespace = ' + _java_quote(wire.wildcard_namespace)
                    + ', wildcardProcessContents = ' + _java_quote(wire.wildcard_process_contents) + ')')
            rows.append(f'    {typ} {self.names.getter_name(prop.source_name, request.naming_profile)}();')
        if (request.contract_role != 'common'
                and model.source_kind in (AInDefinitionSourceKind.JSONDEFS, AInDefinitionSourceKind.YAMLDEFS)
                and model.source_resource.endswith('/additionalProperties')):
            synthetic_name = request.naming_profile.multi_mapped_list_key_synthetic_getter()
            rows.extend(['    /** Return the synthetic parent JSON/YAML object property key. '
                + 'This getter is not serialized inside the value object. '
                + '@return non-null parent property key, stable while stored in a mapped list. */',
                '    String ' + synthetic_name + '();'])
        if (request.contract_role != 'common'
                and model.source_kind in (AInDefinitionSourceKind.JSONDEFS, AInDefinitionSourceKind.YAMLDEFS)
                and model.source_resource.endswith('/additionalProperties')
                and model.data_type.kind not in (AInDataTypeKind.OBJECT, AInDataTypeKind.ENUM)):
            value_name = request.naming_profile.multi_mapped_list_value_synthetic_getter()
            value_type = _synthetic_entry_value_type(model, request, self.names, java=True)
            rows.extend(['    /** Return the typed value associated with this synthetic JSON/YAML map entry.',
                '     * This getter is virtual and does not become a nested serialized field.',
                '     * @return typed serialized property value; never a synthetic property name',
                '     */', f'    {value_type} {value_name}();'])
        rows.append('}')
        return AIcdGeneratedSource(interface, path, '\n'.join(rows) + '\n',
            (AIcdGeneratedTypeIdentity.from_request(request, interface, path, AInDefsNameRole.INTERFACE_TYPE),))
