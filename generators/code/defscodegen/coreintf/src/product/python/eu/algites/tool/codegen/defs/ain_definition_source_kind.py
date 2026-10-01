from __future__ import annotations

from enum import Enum

class AInDefinitionSourceKind(str, Enum):
    """Defines the definition source kind enumeration."""
    YAMLDEFS = "yamldefs"
    JSONDEFS = "jsondefs"
    XMLDEFS = "xmldefs"
