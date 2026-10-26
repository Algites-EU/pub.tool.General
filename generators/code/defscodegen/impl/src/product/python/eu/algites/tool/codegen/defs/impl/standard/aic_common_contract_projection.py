"""Project only the compatible semantic overlap of format-specific definitions."""
from dataclasses import replace
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.tool.codegen.defs.aicd_value_constraints import AIcdValueConstraints
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind


def _common_type(types, context):
    """Keep structural types, intersect object members and relax wire-specific facets."""
    first = types[0]
    if any(t.kind is not first.kind for t in types):
        # XSD anyType can stand in for a more specific YAML/JSON value shape.
        if (any(t.kind is AInDataTypeKind.ANY for t in types)
            or all(t.kind is AInDataTypeKind.STRING or
                   (t.kind is AInDataTypeKind.REFERENCE and t.reference.targets_enum)
                   for t in types)
            or (any(t.kind is AInDataTypeKind.REFERENCE for t in types)
                and all(t.kind is AInDataTypeKind.OBJECT or
                        (t.kind is AInDataTypeKind.REFERENCE and t.reference.target_data_type is not None
                         and t.reference.target_data_type.kind is AInDataTypeKind.OBJECT)
                        for t in types))
            or all(t.kind in (AInDataTypeKind.OBJECT, AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF)
                   or (t.kind is AInDataTypeKind.REFERENCE and t.reference.target_data_type is not None
                       and t.reference.target_data_type.kind in (
                           AInDataTypeKind.OBJECT, AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF))
                   for t in types)):
            from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
            return AIcdDataType(AInDataTypeKind.ANY)
        raise ValueError('Incompatible common field type: ' + context + ' / ' + str([(t.kind.name, repr(t.reference) if t.reference else None) for t in types]))
    constraints = (first.constraints if all(t.constraints == first.constraints for t in types)
                   else AIcdValueConstraints())
    if first.kind is AInDataTypeKind.OBJECT:
        maps = [{f.source_name: f for f in t.properties} for t in types]
        fields = []
        for field in first.properties:
            matches = [m.get(field.source_name) for m in maps]
            if any(f is None for f in matches):
                continue
            shape = _common_type([f.data_type for f in matches], context + '.' + field.source_name)
            if any(f.presence is AInFieldPresenceKind.FORBIDDEN for f in matches):
                raise ValueError('Incompatible forbidden common field: ' + context + '.' + field.source_name)
            presence = (AInFieldPresenceKind.REQUIRED if all(f.presence is AInFieldPresenceKind.REQUIRED
                        for f in matches) else AInFieldPresenceKind.ALLOWED)
            fields.append(replace(field, data_type=shape, presence=presence,
                nullable=any(f.nullable for f in matches), xml_field=None))
        return replace(first, properties=tuple(fields), constraints=constraints)
    if first.kind is AInDataTypeKind.ARRAY:
        return replace(first, element_type=_common_type([t.element_type for t in types], context + '[]'),
            constraints=constraints)
    if first.kind in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
        if any(len(t.alternatives) != len(first.alternatives) for t in types):
            raise ValueError('Incompatible common choice: ' + context)
        return replace(first, alternatives=tuple(_common_type([t.alternatives[i] for t in types],
            context + '[' + str(i) + ']') for i in range(len(first.alternatives))), constraints=constraints)
    if first.kind is AInDataTypeKind.REFERENCE:
        if any(t.reference.logical_name != first.reference.logical_name
               or t.reference.version != first.reference.version for t in types):
            raise ValueError('Incompatible common reference: ' + context)
        return replace(first, constraints=constraints)
    return replace(first, constraints=constraints)


def merge_common(definitions):
    """Merge cross-format common roles without discarding specialized members."""
    if not definitions:
        raise ValueError('No common representations')
    first = definitions[0]
    if len(definitions) == 1:
        return first
    if any(d.version != first.version for d in definitions):
        raise ValueError('Incompatible common contract version: ' + first.logical_name)
    kinds = {d.data_type.kind for d in definitions}
    if len(kinds) > 1:
        if not kinds.issubset({AInDataTypeKind.OBJECT, AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF}):
            raise ValueError('Incompatible common contract root kinds: ' + first.logical_name)
        from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
        data_type = AIcdDataType(AInDataTypeKind.OBJECT)
    elif first.data_type.kind is AInDataTypeKind.OBJECT:
        data_type = _common_type([d.data_type for d in definitions], first.logical_name)
    else:
        if any(d.data_type != first.data_type or d.enum_values != first.enum_values
               for d in definitions):
            raise ValueError('Non-object common contracts must be identical: ' + first.logical_name)
        data_type = first.data_type
    identity = first.identity
    for d in definitions:
        if d.identity.startswith('urn:algites:'):
            marker = {'YAMLDEFS': ':yamldef:', 'JSONDEFS': ':jsondef:'}.get(d.source_kind.name)
            identity = d.identity.replace(marker, ':', 1) if marker else d.identity
            break
    origins = '; '.join(dict.fromkeys(f'{d.source_kind.name}: {d.identity} ({d.source_resource})'
                                       for d in definitions))
    # The common contract has no one representation-specific publication URL.
    # The JSONDEFS/YAMLDEFS specialized contracts retain their own URL mappings.
    return replace(first, identity=identity, data_type=data_type,
        schema_url='', data_source_schema_url_field='',
        data_source_schema_identifier_field='', data_source_schema_version_field='',
        description=(first.description + '\n\n' if first.description else '')
                    + 'Common representations: ' + origins)
