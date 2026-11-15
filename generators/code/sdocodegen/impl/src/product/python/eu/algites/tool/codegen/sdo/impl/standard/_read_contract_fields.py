"""Inspect annotated read-only contracts without importing either SDO runtime.

Only current ``AIaDataObjectField`` getter annotations are authoritative.  In
particular this module never imports the deprecated SmartDataObject metadata
cache, since the Defs and SDO generators are independent of that runtime.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Callable

from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind


def _declared_fields(owner: type, identity_provider: Callable | None = None):
    """Return fields annotated directly on *owner*, in declaration order.

    Args:
        owner: Read-only DataObject interface (or an ancestor).
        identity_provider: Selected input naming catalogue's getter resolver.

    Returns:
        Immutable tuple of normalized field descriptors.  Legacy runtime
        caches and deprecated class-level descriptors are deliberately ignored.
    """
    found = []
    for getter_name, getter in owner.__dict__.items():
        definition = getattr(getter, '__sdo_new_field_definition__', None)
        if definition is None:
            continue
        if not callable(getter):
            raise ValueError('DataObject field annotation is not on a getter: ' + getter_name)
        if identity_provider is None:
            if not getter_name.startswith('get') or len(getter_name) < 4 or not getter_name[3].isupper():
                raise ValueError('Getter needs the explicit naming profile: ' + getter_name)
            semantic = getter_name[3:]
        else:
            semantic = identity_provider(owner, getter_name)
        data_name = definition.dataFieldName
        found.append(AIcdDataObjectField(
            field_name=data_name,
            embedded=definition.embedded,
            presence=definition.presence,
            allows_null=definition.allows_null,
            default_value_resolver=definition.default_value_resolver,
            expected_type=definition.expected_type,
            getter_name=getter_name,
            setter_inheritance_policy=definition.setter_inheritance_policy,
            semantic_id=semantic,
            order=definition.order,
            min_item_count=definition.min_item_count,
            max_item_count=definition.max_item_count,
            is_empty_allowed=definition.is_empty_allowed,
            default_value=definition.default_value,
            string_constraints=getattr(getter, '__data_object_field_string_constraints__', None),
            numeric_constraints=getattr(getter, '__data_object_field_numeric_constraints__', None),
            list_constraints=getattr(getter, '__data_object_field_list_constraints__', None),
            object_constraints=getattr(getter, '__data_object_field_object_constraints__', None),
        ))
    return tuple(found)


def _data_object_fields(cls: type, identity_provider: Callable | None = None) -> dict[str, AIcdDataObjectField]:
    """Resolve annotated fields and narrow inherited contract metadata.

    Args:
        cls: Concrete read-only interface whose inherited shape is needed.
        identity_provider: Getter-name resolver from the explicitly selected
            source naming convention; never inferred from a serialized key.

    Returns:
        Insertion-ordered semantic-field map.  A derived getter can narrow
        presence/nullability, retain inherited constraints and cannot change
        the canonical data field name of its parent.

    Raises:
        ValueError: On ambiguous or incompatible inherited field declarations.
    """
    result: dict[str, AIcdDataObjectField] = {}
    owners: dict[str, type] = {}
    for owner in reversed(cls.__mro__):
        schema = (owner.__dict__.get('__json_schema__') or
                  owner.__dict__.get('__yaml_schema__'))
        reserved = {n for n in (
            getattr(schema, 'data_source_schema_url_field', ''),
            getattr(schema, 'data_source_schema_identifier_field', ''),
            getattr(schema, 'data_source_schema_version_field', ''),
        ) if n}
        for declared in _declared_fields(owner, identity_provider):
            name = declared.semantic_id
            previous = result.get(name)
            if declared.field_name and declared.field_name in reserved:
                continue
            if previous is not None:
                if previous.getter_name != declared.getter_name:
                    raise ValueError('Inherited getter changed identity: ' + name)
                if declared.field_name and declared.field_name != previous.field_name:
                    raise ValueError('Inherited getter changed dataFieldName: ' + name)
                if declared.embedded != previous.embedded:
                    raise ValueError('Inherited getter changed embedding: ' + name)
                if previous.presence is AInFieldPresenceKind.REQUIRED and declared.presence is not AInFieldPresenceKind.REQUIRED:
                    raise ValueError('Inherited getter widens required presence: ' + name)
                if previous.presence is AInFieldPresenceKind.FORBIDDEN and declared.presence is not AInFieldPresenceKind.FORBIDDEN:
                    raise ValueError('Inherited getter widens forbidden presence: ' + name)
                if not previous.allows_null and declared.allows_null:
                    raise ValueError('Inherited getter introduces null: ' + name)
                if not issubclass(owner, owners[name]) and declared != previous:
                    raise ValueError('Unrelated inherited contracts disagree on ' + name)
            # An omitted data name on a derived annotated getter inherits its
            # parent's canonical data identity; names never drive semantic IDs.
            data_name = declared.field_name or (previous.field_name if previous else name)
            constraints = {
                key: getattr(previous, key) for key in (
                    'string_constraints', 'numeric_constraints',
                    'list_constraints', 'object_constraints')
                if previous is not None and getattr(declared, key) is None
            }
            result[name] = replace(declared, field_name=data_name, **constraints)
            owners[name] = owner
    data_owners: dict[str, str] = {}
    for name, field in result.items():
        if field.embedded:
            continue
        owner = data_owners.setdefault(field.field_name, name)
        if owner != name:
            raise ValueError('Duplicate dataFieldName ' + field.field_name + ': ' + owner + ', ' + name)
    return result
