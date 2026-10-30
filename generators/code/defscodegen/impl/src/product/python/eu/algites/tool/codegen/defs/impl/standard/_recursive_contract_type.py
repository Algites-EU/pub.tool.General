"""Render nested canonical shapes using repository-discovered named contracts.

The logical-name path mirrors repository batch discovery, so no synthetic
business packages or duplicate compilation units are introduced.
"""
from __future__ import annotations
import re
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from .aic_scalar_generation import scalar_type


def _kebab(name):
    return re.sub(r'[^A-Za-z0-9]+', '-', re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', name)).strip('-').lower()


def contract_type(prop, request, names, *, java=False, imports=None):
    """Project one property without discarding arrays, inline types or choices."""
    path = request.definition.logical_name + '-' + _kebab(prop.source_name)
    def node(shape, logical, keyed_entry=False):
        kind = shape.kind
        if kind is AInDataTypeKind.ARRAY:
            if shape.position_types:
                if java:
                    raise ValueError('Java positional tuple requires a generated positional interface: ' + logical)
                prefix = [node(value, logical + '-prefix-items-' + str(i))
                          for i, value in enumerate(shape.position_types)]
                if shape.constraints.max_items == len(prefix):
                    return 'tuple[' + ', '.join(prefix) + ']'
                trailing = node(shape.element_type, logical + '-items')
                return 'tuple[' + ', '.join(prefix + ['*tuple[' + trailing + ', ...]']) + ']'
            inner = node(shape.element_type, logical + '-items')
            if shape.key_definitions:
                if not java and imports is not None:
                    imports.add('from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList')
                return ('eu.algites.lib.common.list.AIiMultiMappedList<' + inner + '>'
                        if java else 'AIiMultiMappedList[' + inner + ']')
            return f'java.util.List<? extends {inner}>' if java else f'tuple[{inner}, ...]'
        if kind is AInDataTypeKind.OBJECT and shape.keyed_value_type is not None:
            inner = node(shape.keyed_value_type, logical + '-additional-properties', keyed_entry=True)
            if (request.common_naming_profile is not None
                    and prop.source_name in request.common_keyed_field_names):
                # Java generics are invariant. Format-specific interfaces must
                # preserve the *same* mapped value type as their common parent;
                # the specialized value interfaces still extend that common type.
                inner = names.render(logical + '-additional-properties',
                    request.definition.version, request.common_naming_profile,
                    AInDefsNameRole.INTERFACE_TYPE)
                if not java and imports is not None:
                    file = names.render(logical + '-additional-properties',
                        request.definition.version, request.common_naming_profile,
                        AInDefsNameRole.INTERFACE_TYPE_FILE_STEM)
                    imports.add(f'from .{file} import {inner}')
            if java:
                return 'eu.algites.lib.common.list.AIiMultiMappedList<' + inner + '>'
            if imports is not None:
                imports.add('from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList')
            return 'AIiMultiMappedList[' + inner + ']'
        reference = kind is AInDataTypeKind.REFERENCE
        inline = kind in (AInDataTypeKind.OBJECT, AInDataTypeKind.ONE_OF,
                          AInDataTypeKind.ANY_OF, AInDataTypeKind.ENUM)
        if inline and not keyed_entry and request.definition.source_kind is AInDefinitionSourceKind.XMLDEFS:
            if kind is AInDataTypeKind.OBJECT and not shape.properties:
                return scalar_type(AInDataTypeKind.OBJECT, shape.constraints, java)
            raise ValueError('Inline XML complex/choice member needs an explicitly generated XSD content contract: ' + logical)
        if reference or inline:
            ref = shape.reference if reference else None
            # An inline oneOf consisting exclusively of distinct scalar constants
            # is published as a single named enum by the schema reader.  Treat it
            # as an enum here too: naming it as an interface would introduce an
            # unresolved reference in a generated property's signature.
            literal_choice = (kind is AInDataTypeKind.ONE_OF
                and bool(shape.alternatives)
                and all(alternative.kind in (AInDataTypeKind.STRING,
                    AInDataTypeKind.INTEGER, AInDataTypeKind.NUMBER,
                    AInDataTypeKind.BOOLEAN)
                    and len(alternative.constraints.enum_values) == 1
                    for alternative in shape.alternatives))
            enum = ref.targets_enum if ref else (kind is AInDataTypeKind.ENUM or literal_choice)
            base = ref.logical_name if ref else logical
            version = ref.version if ref else request.definition.version
            role = AInDefsNameRole.ENUM_TYPE if enum else AInDefsNameRole.INTERFACE_TYPE
            file_role = AInDefsNameRole.ENUM_TYPE_FILE_STEM if enum else AInDefsNameRole.INTERFACE_TYPE_FILE_STEM
            result = names.render(base, version, request.naming_profile, role)
            if not java and imports is not None:
                file = names.render(base, version, request.naming_profile, file_role)
                imports.add(f'from .{file} import {result}')
            return result
        scalar = {AInDataTypeKind.STRING: AInDataTypeKind.STRING,
                  AInDataTypeKind.INTEGER: AInDataTypeKind.INTEGER,
                  AInDataTypeKind.NUMBER: AInDataTypeKind.NUMBER,
                  AInDataTypeKind.BOOLEAN: AInDataTypeKind.BOOLEAN,
                  AInDataTypeKind.ANY: AInDataTypeKind.ANY}
        if kind not in scalar:
            raise ValueError(f'Unsupported recursive contract node: {kind.name}')
        return scalar_type(scalar[kind], shape.constraints, java)
    return node(prop.data_type, path)
