"""Immutable canonical properties with one recursive structural type."""
from __future__ import annotations
from dataclasses import dataclass
from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
from eu.algites.tool.codegen.defs.aicd_xml_field_representation import AIcdXmlFieldRepresentation
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind

@dataclass(frozen=True, slots=True)
class AIcdPropertyDefinition:
    """One field: a recursive type, a presence policy, nullability, and wire metadata."""
    source_name: str
    data_type: AIcdDataType
    presence: AInFieldPresenceKind = AInFieldPresenceKind.ALLOWED
    nullable: bool = False
    description: str | None = None
    title: str | None = None
    xml_field: AIcdXmlFieldRepresentation | None = None

    def __post_init__(self):
        if not self.source_name or self.data_type is None:
            raise ValueError('Canonical member name and recursive type are required')
