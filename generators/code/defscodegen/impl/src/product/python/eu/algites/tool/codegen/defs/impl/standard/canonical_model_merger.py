"""Lossless merge of equivalent canonical definitions across source technologies.

The first source establishes the canonical declaration order, names and synthetic
identities. Equivalent subsequent declarations append all source bindings at every
nested node. A semantic disagreement raises an error at its precise canonical path;
no duplicate names or independent source representations are silently overwritten.
"""
from __future__ import annotations

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import replace
from collections.abc import Iterable

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgdType_1 as TypeNode, AIcgdElementList_1 as ElementList,
    AIcgdElement_1 as Element, AIcgdList_1 as ListNode,
    AIcgdMap_1 as MapNode, AIcgdScalar_1 as Scalar,
    AIcgdEnum_1 as EnumNode, AIngTypeOrigin_1 as Origin,
    merge_bindings,
)


class AIcDefsCodegenCanonicalModelMerger:
    """Combines identical logical definitions while accumulating source provenance."""

    @staticmethod
    def merge(types: Iterable[TypeNode]) -> tuple[TypeNode, ...]:
        """Combine declarations with the same logical identity in input order.

        Raises:
            ValueError: Invalid top-level input or incompatible representations.
                Diagnostics include the logical identity and nested property path.
        """
        result: dict[str, TypeNode] = {}
        for root in types:
            if not isinstance(root, TypeNode) or root.target_identity:
                raise ValueError('Canonical source declarations must be unlinked TYPE roots')
            if root.identity in result:
                previous = result[root.identity]
                try:
                    result[root.identity] = _combine(previous, root, root.identity,
                                                     same_declared_identity=True)
                except ValueError as exc:
                    def provenance(node):
                        return ', '.join(f'{binding.source_resource}{binding.source_pointer}'
                                         for bindings in node.source_bindings.values()
                                         for binding in bindings)
                    raise ValueError(f'{exc} [sources: {provenance(previous)}; '
                                     f'{provenance(root)}]') from exc
            else:
                result[root.identity] = root
        return tuple(result.values())


def _combine(left, right, path: str, *, same_declared_identity=False):
    """Merge structural equals and retain source-specific bindings at each node."""
    def conflict(details):
        raise ValueError(f'Conflicting canonical definitions at {path}: {details}')

    if type(left) is not type(right):
        conflict(f'{type(left).__name__} versus {type(right).__name__}')
    if isinstance(left, TypeNode):
        if left.origin != right.origin or left.name != right.name or \
                left.path_segments != right.path_segments or \
                left.inherited_from_types != right.inherited_from_types or \
                left.resolution_state != right.resolution_state or \
                left.target_identity != right.target_identity or \
                (left.schema_version and right.schema_version and left.schema_version != right.schema_version) or \
                (left.description and right.description and left.description != right.description):
            conflict('type name, ancestry, origin or resolution differs')
        if left.identity != right.identity and (same_declared_identity or left.origin is not Origin.SYNTHETIC):
            conflict(f'type identities differ: {left.identity} versus {right.identity}')
        if (left.structure is None) != (right.structure is None):
            conflict('one representation has no structure')
        return replace(left, structure=_combine(left.structure, right.structure, path + '/structure')
                       if left.structure is not None else None,
                       source_bindings=merge_bindings(left.source_bindings, right.source_bindings),
                       schema_version=left.schema_version or right.schema_version,
                       description=left.description or right.description)
    if isinstance(left, ElementList):
        if (left.composition != right.composition or len(left.children) != len(right.children)
                or left.min_item_count != right.min_item_count or left.max_item_count != right.max_item_count
                or left.min_properties != right.min_properties
                or left.max_properties != right.max_properties):
            conflict('group composition or child count differs')
        return replace(left, children=tuple(_combine(a, b, path + f'/children/{i}')
                                            for i, (a, b) in enumerate(zip(left.children, right.children))))
    if isinstance(left, Element):
        if (left.name != right.name or left.key_definitions != right.key_definitions
                or left.min_item_count != right.min_item_count or left.max_item_count != right.max_item_count
                or (left.xml_wire is not None and right.xml_wire is not None
                    and left.xml_wire != right.xml_wire)
                or (left.description and right.description and left.description != right.description)):
            conflict('field name, XML QName, documentation, occurrences or key definitions differ')
        return replace(left, structure=_combine(left.structure, right.structure, path + '/' + left.name),
                       source_bindings=merge_bindings(left.source_bindings, right.source_bindings),
                       description=left.description or right.description,
                       xml_wire=left.xml_wire or right.xml_wire)
    if isinstance(left, ListNode):
        if (left.name != right.name or left.min_item_count != right.min_item_count
                or left.max_item_count != right.max_item_count
                or left.unique_items != right.unique_items
                or left.key_definitions != right.key_definitions
                or (left.xml_wire is not None and right.xml_wire is not None
                    and left.xml_wire != right.xml_wire)):
            conflict('array names, XML QName, key definitions or occurrence bounds differ')
        return replace(left, item=_combine(left.item, right.item, path + '/items'),
                       xml_wire=left.xml_wire or right.xml_wire)
    if isinstance(left, MapNode):
        if left.name != right.name or left.map_kind != right.map_kind:
            conflict('map names or kinds differ')
        return replace(left, key_type=_combine(left.key_type, right.key_type, path + '/keys'),
                       value_type=_combine(left.value_type, right.value_type, path + '/values'),
                       source_bindings=merge_bindings(left.source_bindings, right.source_bindings))
    if isinstance(left, (Scalar, EnumNode)):
        if left != right:
            conflict('scalar kind, format or enumeration values differ')
        return left
    conflict('unsupported canonical structure')
