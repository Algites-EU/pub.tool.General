"""Private conversion of reader syntax hints to recursive canonical types.

No flat descriptor is retained in or exposed by the canonical API.
"""
from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind

def from_source_hints(kind, item_kind=None, reference=None, constraints=None, item_constraints=None):
    """Normalize source kind hints into a single canonical recursive structural type."""
    from eu.algites.tool.codegen.defs.aicd_value_constraints import AIcdValueConstraints
    if kind is AInDataTypeKind.ARRAY:
        member = AIcdDataType(AInDataTypeKind.REFERENCE, reference=reference) if reference is not None else AIcdDataType(
            item_kind or AInDataTypeKind.ANY, constraints=item_constraints or AIcdValueConstraints())
        return AIcdDataType(AInDataTypeKind.ARRAY, element_type=member)
    if kind is AInDataTypeKind.REFERENCE:
        if reference is None:
            raise ValueError('Reference kind requires a canonical target')
        return AIcdDataType(AInDataTypeKind.REFERENCE, reference=reference)
    if kind is AInDataTypeKind.OBJECT:
        return AIcdDataType(AInDataTypeKind.OBJECT)
    return AIcdDataType(kind or AInDataTypeKind.ANY, constraints=constraints or AIcdValueConstraints())
