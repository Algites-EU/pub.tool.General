"""Kinds of recursively composable canonical schema data types."""
from enum import Enum


class AInDataTypeKind(str, Enum):
    """Structural type categories independent of serialization format."""
    ANY = 'ANY'
    STRING = 'STRING'
    INTEGER = 'INTEGER'
    NUMBER = 'NUMBER'
    BOOLEAN = 'BOOLEAN'
    OBJECT = 'OBJECT'
    ARRAY = 'ARRAY'
    ENUM = 'ENUM'
    REFERENCE = 'REFERENCE'
    ONE_OF = 'ONE_OF'
    ANY_OF = 'ANY_OF'
