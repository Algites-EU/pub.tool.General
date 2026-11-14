"""Validate and serialize the schema-generated canonical Defs object graph.

The authoritative JSON shape is emitted by the generated SmartDataObject
implementation of ``AIigCanonicalModel_1``. No parallel handwritten JSON
projection or intermediary DTO hierarchy is maintained here.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import is_dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgdCanonicalModel_1, AIcgdType_1, AIcgdElementList_1,
    AIcgdElement_1, AIcgdList_1, AIcgdMap_1,
    AIngResolutionState_1,
)


def _require_linked(node: Any) -> None:
    """Reject unresolved symbolic references anywhere in a generated model tree."""
    if isinstance(node, AIcgdType_1):
        if node.resolution_state is not AIngResolutionState_1.RESOLVED:
            raise ValueError(f'Unresolved canonical TYPE at {node.identity!r}: '
                             f'{node.resolution_state.value}; resolve references before contract emission')
        if node.target_identity:
            if node.structure is not None:
                raise ValueError(f'TYPE {node.identity!r} cannot own both a target and a structure')
        elif node.structure is not None:
            _require_linked(node.structure)
        else:
            raise ValueError(f'Resolved canonical TYPE {node.identity!r} has no structure or target')
    elif isinstance(node, AIcgdElementList_1):
        for child in node.children:
            _require_linked(child)
    elif isinstance(node, AIcgdElement_1):
        _require_linked(node.structure)
    elif isinstance(node, AIcgdList_1):
        _require_linked(node.item)
    elif isinstance(node, AIcgdMap_1):
        _require_linked(node.key_type)
        _require_linked(node.value_type)


def _generated_data_tree(value: Any) -> Any:
    """Project generated SDO fields into their schema-declared data names.

    This is a format-neutral view of *existing generated objects*, not another
    canonical model or a replacement for the independent SDO serializer. The
    field names come from runtime metadata and choice branch declarations.

    :param value: Generated SDO object, sealed-choice record, sequence or scalar.
    :return: Plain mapping, sequence, or schema-coded scalar.
    :raises TypeError: If a non-generated value cannot be represented safely.
    """
    if value is None or isinstance(value, (str, int, float, bool, Decimal)):
        return value
    if isinstance(value, Enum):
        code = getattr(value, 'code', None)
        if not callable(code):
            raise TypeError('Canonical enum has no schema code(): ' + repr(type(value)))
        return code()
    if isinstance(value, AIcSmartDataObject):
        raw = value.getRawValues()
        return {field.getDataFieldName(): _generated_data_tree(raw[field.getSemanticFieldName()])
                for field in value._metadata().getFields()
                if field.getSemanticFieldName() in raw}
    if is_dataclass(value) and hasattr(value, '__xml_choice_component_names__'):
        result = {}
        for name in value.__xml_choice_component_names__:
            getter = getattr(value, 'get' + (''.join(part.title() for part in name.split('_')) if '_' in name else name[0].upper() + name[1:]), None)
            if not callable(getter):
                raise TypeError('Generated choice has no getter for ' + repr(name))
            result[name] = _generated_data_tree(getter())
        return result
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise TypeError('Canonical data object keys must be strings')
        return {key: _generated_data_tree(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_generated_data_tree(item) for item in value]
    raise TypeError('Unexpected canonical generated value: ' + repr(type(value)))


class AIcDefsCodegenCanonicalContractPayload:
    """Serialize only the generated canonical model contract with source provenance."""

    @staticmethod
    def emit(types: Iterable[AIcgdType_1]) -> dict[str, Any]:
        """Serialize linked definitions as one generated canonical document.

        Args:
            types: Top-level, linked schema-generated TYPE implementations.

        Returns:
            JSON-schema compatible mapping produced by the independent SDO runtime.

        Raises:
            TypeError: An input is not a generated TYPE implementation.
            ValueError: A duplicate identity or unresolved symbolic type is found.
        """
        roots = list(types)
        seen: set[str] = set()
        for declared in roots:
            if not isinstance(declared, AIcgdType_1):
                raise TypeError('Top-level canonical declarations must be TYPE')
            if declared.identity in seen:
                raise ValueError(f'Duplicate canonical TYPE identity: {declared.identity}')
            seen.add(declared.identity)
            _require_linked(declared)
        document = AIcgdCanonicalModel_1()
        document.getTypesList().extend(roots)
        # The generated SDO runtime owns all field definitions. Use only its
        # current schema-neutral metadata, never deprecated to_mapping().
        return _generated_data_tree(document)
