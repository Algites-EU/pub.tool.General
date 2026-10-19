"""Canonical schema definitions backed exclusively by recursive structural types."""
from __future__ import annotations
from dataclasses import dataclass
from eu.algites.tool.codegen.defs.aicd_enum_value_definition import AIcdEnumValueDefinition
from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind

@dataclass(frozen=True, slots=True)
class AIcdCanonicalDefinition:
    """Definition identity, source provenance and a single canonical recursive root type."""
    identity: str
    version: int | None
    logical_name: str
    source_kind: AInDefinitionSourceKind
    source_resource: str
    description: str | None
    data_type: AIcdDataType
    enum_values: tuple[AIcdEnumValueDefinition, ...] = ()
    title: str | None = None

    def __post_init__(self):
        if not self.identity or not self.logical_name or not self.source_resource or self.data_type is None:
            raise ValueError('Canonical identity, source and recursive type are required')
        object.__setattr__(self, 'enum_values', tuple(self.enum_values))
        if self.enum_values and self.data_type.kind is not AInDataTypeKind.ENUM:
            raise ValueError('Enumeration wire values require an ENUM root type')
