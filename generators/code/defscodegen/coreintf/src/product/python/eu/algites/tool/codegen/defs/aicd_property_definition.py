from __future__ import annotations

from dataclasses import dataclass
from eu.algites.tool.codegen.defs.aicd_definition_reference import AIcdDefinitionReference
from eu.algites.tool.codegen.defs.ain_value_kind import AInValueKind

@dataclass(frozen=True, slots=True)
class AIcdPropertyDefinition:
    """Carries immutable property definition data.

    Attributes:
        source_name: Canonical property name.
        value_kind: Normalized property value kind.
        required: Whether the property is required.
        nullable: Whether null is accepted.
        item_value_kind: Normalized array item value kind.
        reference: Referenced canonical definition.
        description: Human-readable description.
    """
    source_name: str
    value_kind: AInValueKind
    required: bool = False
    nullable: bool = False
    item_value_kind: AInValueKind | None = None
    reference: AIcdDefinitionReference | None = None
    description: str | None = None
