"""Immutable, recursively composable canonical schema data types."""
from __future__ import annotations

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
from dataclasses import dataclass
from typing import TYPE_CHECKING
from .ain_data_type_kind import AInDataTypeKind
from .aicd_value_constraints import AIcdValueConstraints
from .aicd_key_definition import AIcdKeyDefinition
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
    keyed_value_type: AIcdDataType | None = None
    key_definitions: tuple[AIcdKeyDefinition, ...] = ()
    position_types: tuple[AIcdDataType, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, 'properties', tuple(self.properties))
        object.__setattr__(self, 'alternatives', tuple(self.alternatives))
        object.__setattr__(self, 'key_definitions', tuple(self.key_definitions))
        object.__setattr__(self, 'position_types', tuple(self.position_types))
        if self.keyed_value_type is not None and self.kind is not AInDataTypeKind.OBJECT:
            raise AIxCodegenValidationException('KEYED_VALUES requires an OBJECT parent', 'Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.')
        if self.keyed_value_type is not None and not self.key_definitions:
            raise AIxCodegenValidationException('KEYED_VALUES requires an explicit key definition', 'Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.')
        if self.key_definitions and self.keyed_value_type is None and self.kind is not AInDataTypeKind.ARRAY:
            raise AIxCodegenValidationException('Key definitions require an ARRAY or a keyed OBJECT', 'Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.')
        if self.position_types and self.kind is not AInDataTypeKind.ARRAY:
            raise AIxCodegenValidationException('POSITION_TYPED_VALUE requires ARRAY', 'Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.')
        if self.kind is AInDataTypeKind.ARRAY and self.element_type is None:
            raise AIxCodegenValidationException('ARRAY requires an element type', 'Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.')
        if self.kind in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF) and not self.alternatives:
            raise AIxCodegenValidationException('Closed choice requires alternatives', 'Check that each choice/enum branch is declared once with a supported, resolvable type and that any required choice annotation is present.')
        if self.kind is AInDataTypeKind.REFERENCE and self.reference is None:
            raise AIxCodegenValidationException('REFERENCE requires a target', 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')

    @classmethod
    def choice(cls, kind: AInDataTypeKind, alternatives):
        """Create an exclusive or inclusive closed choice explicitly."""
        if kind not in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
            raise AIxCodegenValidationException(f'Not a choice: {kind}', 'Check that each choice/enum branch is declared once with a supported, resolvable type and that any required choice annotation is present.')
        return cls(kind, alternatives=tuple(alternatives))


    def with_properties(self, properties):
        """Replace an OBJECT node's members without modifying its other structural metadata."""
        from dataclasses import replace
        if self.kind is not AInDataTypeKind.OBJECT:
            raise AIxCodegenValidationException('Only an OBJECT data type has named properties', 'Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.')
        return replace(self, properties=tuple(properties))

    def referenced_definition(self):
        """Find a direct reference, optionally below nested array levels."""
        if self.kind is AInDataTypeKind.REFERENCE:
            return self.reference
        if self.kind is AInDataTypeKind.ARRAY:
            return self.element_type.referenced_definition()
        return None
