from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class AIcdParsedVersionedName:
    """Carries immutable parsed versioned name data.

    Attributes:
        logical_name: Logical name without its version suffix.
        version: Canonical definition version.
    """
    logical_name: str
    version: int | None
