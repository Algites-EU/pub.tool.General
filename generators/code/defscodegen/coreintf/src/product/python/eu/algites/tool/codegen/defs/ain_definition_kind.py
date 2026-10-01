from __future__ import annotations

from enum import Enum

class AInDefinitionKind(str, Enum):
    """Defines the definition kind enumeration."""
    OBJECT = "OBJECT"
    ENUM = "ENUM"
    SCALAR = "SCALAR"
