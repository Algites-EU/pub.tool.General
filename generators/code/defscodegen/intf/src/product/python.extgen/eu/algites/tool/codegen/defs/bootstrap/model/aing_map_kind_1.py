from __future__ import annotations
from typing import Any

from enum import Enum


class AIngMapKind_1(str, Enum):
    """Map participation and property-map policy

    Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/MapKind; version: 1.
    Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}MapKind; version: 1."""

    COMMON_MAP = 'COMMON_MAP'
    INTEGRATED_PROPERTY_MAP = 'INTEGRATED_PROPERTY_MAP'

    def code(self) -> str:
        """Return the exact typed wire code."""
        return self.value
