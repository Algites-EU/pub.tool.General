"""Validate and serialize the schema-generated canonical Defs object graph.

The authoritative JSON shape is emitted by the generated SmartDataObject
implementation of ``AIigCanonicalModel_1``. No parallel handwritten JSON
projection or intermediary DTO hierarchy is maintained here.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgd_jCanonicalModel_1, AIcgd_jType_1, AIcgd_jElementList_1,
    AIcgd_jElement_1, AIcgd_jList_1, AIcgd_jMap_1,
    AIigResolutionState_1,
)


def _require_linked(node: Any) -> None:
    """Reject unresolved symbolic references anywhere in a generated model tree."""
    if isinstance(node, AIcgd_jType_1):
        if node.resolution_state is not AIigResolutionState_1.RESOLVED:
            raise ValueError(f'Unresolved canonical TYPE at {node.identity!r}: '
                             f'{node.resolution_state.value}; resolve references before contract emission')
        if node.target_identity:
            if node.structure is not None:
                raise ValueError(f'TYPE {node.identity!r} cannot own both a target and a structure')
        elif node.structure is not None:
            _require_linked(node.structure)
        else:
            raise ValueError(f'Resolved canonical TYPE {node.identity!r} has no structure or target')
    elif isinstance(node, AIcgd_jElementList_1):
        for child in node.children:
            _require_linked(child)
    elif isinstance(node, AIcgd_jElement_1):
        _require_linked(node.structure)
    elif isinstance(node, AIcgd_jList_1):
        _require_linked(node.item)
    elif isinstance(node, AIcgd_jMap_1):
        _require_linked(node.key_type)
        _require_linked(node.value_type)


class AIcDefsCodegenCanonicalContractPayload:
    """Serialize only the generated canonical model contract with source provenance."""

    @staticmethod
    def emit(types: Iterable[AIcgd_jType_1]) -> dict[str, Any]:
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
            if not isinstance(declared, AIcgd_jType_1):
                raise TypeError('Top-level canonical declarations must be TYPE')
            if declared.identity in seen:
                raise ValueError(f'Duplicate canonical TYPE identity: {declared.identity}')
            seen.add(declared.identity)
            _require_linked(declared)
        document = AIcgd_jCanonicalModel_1()
        document.setTypes(roots)
        return document.to_mapping()
