from __future__ import annotations
from typing import Any

from enum import Enum


class AIngComposition_1(str, Enum):
    """Group compositor; ALL is ordered for canonical traversal

    Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Composition; version: 1.
    Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}Composition; version: 1."""

    SEQUENCE = 'SEQUENCE'
    ALL = 'ALL'
    CHOICE = 'CHOICE'

    def code(self) -> str:
        """Return the exact typed wire code."""
        return self.value
