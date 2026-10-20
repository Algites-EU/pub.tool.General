"""Native first-stage generator from canonical Defs into read-only contracts."""
from __future__ import annotations

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
        raise ValueError(f'Nested {data_type.kind.name} requires a generated named contract')
    return scalar_type(kinds[data_type.kind], data_type.constraints, java)


def _property_name(value):
    name = re.sub(r'[^a-zA-Z0-9_]', '_', value)
    if not name or name[0].isdigit():
        name = '_' + name
    return name + '_' if keyword.iskeyword(name) else name


class AIcSchemaContractInterfaceGenerator:
    """Generate importable AIig and AIng sources without generating any DTO."""

    def __init__(self):
        self.names = AIcGenerationNames()

    def generate(self, request, parent: tuple[str, str] | None = None) -> AIcdGeneratedSource:
        """Generate canonical read contracts and preserve the explicit parent edge."""
        if request.definition.data_type.kind in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
            if parent is not None:
                raise ValueError('Closed choice cannot inherit object contracts')
            from .aic_closed_choice_generator import AIcClosedChoiceGenerator
            return AIcClosedChoiceGenerator().generate(request)[0]
        if request.definition.data_type.kind is AInDataTypeKind.ENUM:
            if parent is not None:
                raise ValueError('Enums cannot inherit object contracts')
            return AIcDefaultDefsCodegenService().generate(request)
        if request.target is not AInCodeGenerationTarget.PYTHON:
            return self._generate_java(request, parent)
        return self._generate_python(request, parent)

    def generate_sources(self, request, parent=None):
        """Return every independently compiled source, including closed-choice wrappers."""
        if request.definition.data_type.kind in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
            if parent is not None:
                raise ValueError('Closed choice cannot inherit object contracts')
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
        has_temporal = False
        for field_order, prop in enumerate(model.data_type.properties):
            name = _property_name(self.names.property_name(prop.source_name, request.naming_profile))
            suffix = name[0].upper() + name[1:]
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
            if prop.xml_field is not None:
                wire = prop.xml_field
                xml_field_rows.append(f'        {prop.source_name!r}: AIaXmlDataObjectField('
                    f'namespace={wire.namespace!r}, namespace_local_name={wire.namespace_local_name!r}, '
                    f'value_kind=AInXmlValueKind.{wire.value_kind.name}, order={field_order}, '
                    f'min_occurs={wire.min_occurs}, max_occurs={wire.max_occurs}),')
            label_rows.append(f'        {prop.source_name!r}: AIaFieldLabel(label={title!r}, labels={entries}),')
            metadata_rows.append('        AIcdDataObjectField(field_name=' + repr(prop.source_name)
                + ', presence=AInFieldPresenceKind.' + prop.presence.name
                + ', allows_null=' + str(bool(prop.nullable))
                + ', getter_name=' + repr('get' + suffix) + '),')
            getter_type = ''
            if reference is not None and not array and not reference.targets_enum:
                getter_type = f' -> {kind_type}' + (' | None' if prop.nullable else '')
            getter_rows.extend([f'    @AIaFieldLabel(label={title!r}, labels={entries})',
                '    @abstractmethod', f'    def get{suffix}(self){getter_type}:',
                '        raise NotImplementedError', ''])
        parent_import = ''
        base_module, base_type, _ = _TECHNOLOGY_DATA_OBJECT[model.source_kind]
        if request.contract_role == 'common':
            base_module, base_type = ('eu.algites.lib.data.dataobject.aii_data_object', 'AIiDataObject')
        parent_name = base_type + ', ABC'
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
        if xml_field_rows:
            xml_imports += ('from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field import AIaXmlDataObjectField\n'
                'from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind\n')
            xml_metadata += ('    __xml_data_object_fields__ = {\n' + '\n'.join(xml_field_rows) + '\n    }\n')
        source = ('from __future__ import annotations\n' + parent_import
            + '\nfrom abc import ABC, abstractmethod\n'
            + 'from typing import Any, ClassVar, Mapping\nfrom decimal import Decimal\n'
            + f'from {base_module} import {base_type}\n'
            + 'from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n'
            + 'from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField\n'
            + 'from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind\n'
            + 'from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel\n'
            + xml_imports
            + '\n'.join(sorted(ref_imports)) + '\n\n' + helpers
            + f'class {interface}({parent_name}):\n'
            + f'    __data_object__ = AIcdDataObject(schema_id={model.identity!r}, '
            + f'schema_version={model.version if model.version is not None else -1}, '
            + f'title={_visible_title(model.title, model.logical_name)!r}, description={(model.description or "")!r}, '
            + f'naming_convention={request.naming_convention!r})\n'
            + xml_metadata
            + '    __data_object_fields__ = (\n' + '\n'.join(metadata_rows)
            + '\n    )\n\n    __field_labels__ = {\n' + '\n'.join(label_rows)
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
        path = request.package_name.replace('.', '/') + '/' + interface + '.java'
        extends = ((parent[1] + '.' + parent[0]) if parent else
            ('eu.algites.lib.data.dataobject.AIiDataObject' if request.contract_role == 'common' else
                _TECHNOLOGY_DATA_OBJECT[model.source_kind][2]))
        rows = [f'package {request.package_name};', '', '/** Generated schema contract. Do not edit manually. */',
            '@eu.algites.lib.data.dataobject.AIaDataObject(schemaId = '
            + _java_quote(model.identity) + ', schemaVersion = '
            + str(model.version if model.version is not None else -1)
            + ', title = ' + _java_quote(_visible_title(model.title, model.logical_name))
            + ', description = ' + _java_quote(model.description or '')
            + ', namingConvention = ' + _java_quote(request.naming_convention) + ')',
            f'public interface {interface} extends {extends} {{',
            '    /** Canonical schema ID independent of any representation-specific publication URL. */',
            f'    String CANONICAL_SOURCE_ID = {_java_quote(model.identity)};',
            '    /** Version identifying the canonical schema definition. */',
            f'    Integer CANONICAL_SOURCE_VERSION = {_java_integer(model.version)};',
            '    /** Definition source resource retained for provenance and diagnostics. */',
            f'    String CANONICAL_SOURCE_RESOURCE = {_java_quote(model.source_resource)};']
        if request.xml_type_qname is not None:
            namespace, local = request.xml_type_qname[1:].split('}', 1)
            rows.insert(4, '@eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject('
                'definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, '
                + 'namespace = ' + _java_quote(namespace) + ', namespaceLocalName = ' + _java_quote(local) + ')')
        for field_order, prop in enumerate(model.data_type.properties):
            desc = re.sub(r'\s+', ' ', (prop.description or f'Canonical field {prop.source_name}.').replace('*/', '* /')).replace('<', '&lt;').replace('>', '&gt;')
            name = java_identifier(self.names.property_name(prop.source_name, request.naming_profile))
            typ = contract_type(prop, request, self.names, java=True)
            title = _visible_title(prop.title, prop.source_name)
            entries = (', labels = {@eu.algites.lib.common.object.props.labels.AIaFieldLabel.Entry(roleCode = eu.algites.lib.common.object.props.labels.AIaFieldLabel.FIELD_DESCRIPTION, label = '
                + _java_quote(prop.description) + ')}') if prop.description else ''
            rows.extend([f'    /** <strong>Field Name:</strong> {{@code {prop.source_name}}}. {desc} */',
                f'    String {self.names.schema_field_name_constant(prop.source_name, request.naming_profile)} = {_java_quote(prop.source_name)};',
                f'    /** {desc} */',
                f'    @eu.algites.lib.common.object.props.labels.AIaFieldLabel(label = {_java_quote(title)}{entries})',
                '    @eu.algites.lib.data.dataobject.AIaDataObjectField(fieldName = '
                    + _java_quote(prop.source_name)
                    + ', presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.' + prop.presence.name
                    + ', allowsNull = ' + str(bool(prop.nullable)).lower() + ')'])
            if prop.xml_field is not None:
                wire = prop.xml_field
                rows.append('    @eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField('
                    + 'namespace = ' + _java_quote(wire.namespace)
                    + ', namespaceLocalName = ' + _java_quote(wire.namespace_local_name)
                    + ', valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.'
                    + wire.value_kind.name + ', order = ' + str(field_order)
                    + ', minOccurs = ' + str(wire.min_occurs) + ', maxOccurs = ' + str(wire.max_occurs) + ')')
            rows.append(f'    {typ} {name}();')
        rows.append('}')
        return AIcdGeneratedSource(interface, path, '\n'.join(rows) + '\n',
            (AIcdGeneratedTypeIdentity.from_request(request, interface, path, AInDefsNameRole.INTERFACE_TYPE),))
