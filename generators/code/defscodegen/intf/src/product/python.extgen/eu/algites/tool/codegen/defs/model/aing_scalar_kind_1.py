from __future__ import annotations
from typing import Any

from enum import Enum


class AIngScalarKind_1(str, Enum):
    """Canonical scalar type

    Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ScalarKind; version: 1.
    Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}ScalarKind; version: 1."""

    ANY = 'ANY'
    STRING = 'STRING'
    INTEGER = 'INTEGER'
    NUMBER = 'NUMBER'
    BOOLEAN = 'BOOLEAN'
    NULL = 'NULL'

    def code(self) -> str:
        """Return the exact typed wire code."""
        return self.value
