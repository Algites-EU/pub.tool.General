from __future__ import annotations
from typing import Any

from enum import Enum


class AIngStructureKind_1(str, Enum):
    """Seven canonical kinds

    Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/StructureKind; version: 1.
    Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}StructureKind; version: 1."""

    TYPE = 'TYPE'
    ELEMENTLIST = 'ELEMENTLIST'
    ELEMENT = 'ELEMENT'
    LIST = 'LIST'
    MAP = 'MAP'
    SCALAR = 'SCALAR'
    ENUM = 'ENUM'

    def code(self) -> str:
        """Return the exact typed wire code."""
        return self.value
