"""Semantic addressing roles for schema collection fields.

These roles describe how values are located; they do not replace the value's
scalar, object, reference or union data type. Each source frontend must preserve
information it cannot represent rather than broadening it to ANY.
"""
from enum import Enum


class AInFieldValueRole(str, Enum):
    """Addressing mechanism for a member of a canonical schema contract."""

    NAMED_VALUE = 'NAMED_VALUE'
    KEYED_VALUES = 'KEYED_VALUES'
    POSITION_TYPED_VALUE = 'POSITION_TYPED_VALUE'
    SEQUENTIAL_VALUES = 'SEQUENTIAL_VALUES'
