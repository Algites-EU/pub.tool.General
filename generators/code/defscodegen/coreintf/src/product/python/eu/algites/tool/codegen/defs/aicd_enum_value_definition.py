from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AIcdEnumValueDefinition:
    """Describes one canonical enum wire value.

    Attributes:
        value: Exact serialized enum value.
        description: Human-readable description of the enum value when supplied.
    """

    value: str
    description: str | None = None
