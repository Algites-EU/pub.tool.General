from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class AIcdGeneratedSource:
    """Carries immutable generated source data.

    Attributes:
        type_name: Generated primary type name.
        relative_path: Generated source relative path.
        source: Complete generated source text.
    """
    type_name: str
    relative_path: str
    source: str
