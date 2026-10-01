from __future__ import annotations

from enum import Enum

class AInValueKind(str, Enum):
    """Defines the value kind enumeration."""
    STRING = "STRING"
    INTEGER = "INTEGER"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    ARRAY = "ARRAY"
    OBJECT = "OBJECT"
    REFERENCE = "REFERENCE"
    ANY = "ANY"
