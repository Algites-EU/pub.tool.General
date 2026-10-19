"""Immutable, recursively composable canonical schema data types."""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING
from .ain_data_type_kind import AInDataTypeKind
from .aicd_value_constraints import AIcdValueConstraints
if TYPE_CHECKING:
    from .aicd_property_definition import AIcdPropertyDefinition
    from .aicd_definition_reference import AIcdDefinitionReference


@dataclass(frozen=True, slots=True)
class AIcdDataType:
    """One type node; arrays, objects and closed choices contain recursive child nodes."""
    kind: AInDataTypeKind
    element_type: AIcdDataType | None = None
    properties: tuple[AIcdPropertyDefinition, ...] = ()
    alternatives: tuple[AIcdDataType, ...] = ()
    reference: AIcdDefinitionReference | None = None
    constraints: AIcdValueConstraints = AIcdValueConstraints()

    def __post_init__(self):
        object.__setattr__(self, 'properties', tuple(self.properties))
        object.__setattr__(self, 'alternatives', tuple(self.alternatives))
        if self.kind is AInDataTypeKind.ARRAY and self.element_type is None:
            raise ValueError('ARRAY requires an element type')
        if self.kind in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF) and not self.alternatives:
            raise ValueError('Closed choice requires alternatives')
        if self.kind is AInDataTypeKind.REFERENCE and self.reference is None:
            raise ValueError('REFERENCE requires a target')

    @classmethod
    def choice(cls, kind: AInDataTypeKind, alternatives):
        """Create an exclusive or inclusive closed choice explicitly."""
        if kind not in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
            raise ValueError(f'Not a choice: {kind}')
        return cls(kind, alternatives=tuple(alternatives))


    def with_properties(self, properties):
        """Replace an OBJECT node's members without modifying its other structural metadata."""
        from dataclasses import replace
        if self.kind is not AInDataTypeKind.OBJECT:
            raise ValueError('Only an OBJECT data type has named properties')
        return replace(self, properties=tuple(properties))

    def referenced_definition(self):
        """Find a direct reference, optionally below nested array levels."""
        if self.kind is AInDataTypeKind.REFERENCE:
            return self.reference
        if self.kind is AInDataTypeKind.ARRAY:
            return self.element_type.referenced_definition()
        return None
