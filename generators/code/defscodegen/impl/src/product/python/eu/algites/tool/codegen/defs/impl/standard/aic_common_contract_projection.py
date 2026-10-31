"""Project only the compatible semantic overlap of format-specific definitions."""
from dataclasses import replace
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.tool.codegen.defs.aicd_value_constraints import AIcdValueConstraints
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind


def _compatible_key_definitions(types, context):
    """Validate explicit versus virtual keys without discarding their meaning.

    XML ``xs:key`` obtains its unique string key from a required physical item
    field; JSON/YAML ``additionalProperties`` obtains that key from the property
    name. They may share a canonical map only when both encode one mandatory,
    unique string key per item. Unrelated composite and nonunique indexes do
    not become equivalent merely because their counts match.
    """
    definitions = [t.key_definitions for t in types]
    first = definitions[0]
    if all(value == first for value in definitions):
        return first
    if any(len(value) != 1 for value in definitions):
        raise ValueError('Incompatible common key definitions: ' + context)
    keys = [value[0] for value in definitions]
    virtual = [key for key in keys if key.virtual]
    physical = [key for key in keys if not key.virtual]
    if not virtual or not physical or not all(key.unique for key in keys):
        raise ValueError('Incompatible common key definitions: ' + context)
    if any(key.fields != virtual[0].fields or key.name != virtual[0].name for key in virtual):
        raise ValueError('Incompatible virtual common key definitions: ' + context)
    for typ, key in zip(types, keys):
        if key.virtual:
            continue
        if len(key.fields) != 1 or '.' in key.fields[0]:
            raise ValueError('Incompatible physical common key definition: ' + context)
        field = next((candidate for candidate in typ.keyed_value_type.properties
                      if candidate.source_name == key.fields[0]), None)
        if (field is None or field.data_type.kind is not AInDataTypeKind.STRING
                or field.presence is not AInFieldPresenceKind.REQUIRED or field.nullable):
            raise ValueError('Physical common key must be a required string: ' + context)
    return (virtual[0],)


def _common_type(types, context):
    """Keep structural types, intersect object members and relax wire-specific facets."""
    first = types[0]
    if any(t.kind is not first.kind for t in types):
        # Cross-representation contracts must not silently broaden methods
        # to Object. A different type-kind is only compatible when the code
        # generator can emit exactly the same public type, which is the
        # primitive STRING case. Any/enum/reference/object combinations
        # require an explicit, verified mapping rather than guessing.
        # A non-enumerated closed choice of strings can be exposed as
        # String in every language. An enum-valued choice cannot: its
        # nominal Java enum is not a subtype of java.lang.String.
        def plain_string_choice(t):
            if t.kind is AInDataTypeKind.STRING:
                return not t.constraints.enum_values
            return (t.kind in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF)
                and bool(t.alternatives)
                and all(plain_string_choice(option) for option in t.alternatives))
        if all(plain_string_choice(t) for t in types):
            from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
            return AIcdDataType(AInDataTypeKind.STRING)
        kinds = [(t.kind.name, repr(t.reference) if t.reference else None)
                 for t in types]
        raise ValueError('Incompatible common field type: ' + context
                         + ' / ' + str(kinds))
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
        has_keys = [t.keyed_value_type is not None for t in types]
        if any(has_keys) and not all(has_keys):
            raise ValueError('Incompatible KEYED_VALUES declarations: ' + context)
        if all(has_keys):
            common_keys = _compatible_key_definitions(types, context)
            keyed = _common_type([t.keyed_value_type for t in types], context + '{key}')
        else:
            common_keys = ()
            keyed = None
        return replace(first, properties=tuple(fields), keyed_value_type=keyed,
            key_definitions=common_keys, constraints=constraints)
    if first.kind is AInDataTypeKind.ARRAY:
        if any(len(t.position_types) != len(first.position_types) for t in types):
            raise ValueError('Incompatible POSITION_TYPED_VALUE slots: ' + context)
        positions = tuple(_common_type([t.position_types[i] for t in types],
                          context + '[' + str(i) + ']') for i in range(len(first.position_types)))
        return replace(first, element_type=_common_type([t.element_type for t in types], context + '[]'),
            position_types=positions, constraints=constraints)
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
        if first.data_type.kind in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
            # XML QName and JSON $defs pointers can differ while their
            # target logical contract and branch order are identical.
            # _common_type checks every nominal target, never raw pointer text.
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
