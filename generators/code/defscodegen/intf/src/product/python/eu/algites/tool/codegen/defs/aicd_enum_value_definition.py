from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AIcdEnumValueDefinition:
    """Describes one canonical enum wire value.

    Attributes:
        value: Exact serialized enum value.
        description: Human-readable description of the enum value when supplied.
        title: Short English enum-value title from the definition.
    """

    value: str
    description: str | None = None
    title: str | None = None
