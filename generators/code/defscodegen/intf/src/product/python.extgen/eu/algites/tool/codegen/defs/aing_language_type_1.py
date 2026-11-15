from __future__ import annotations
from typing import Any

from enum import Enum


class AIngLanguageType_1(str, Enum):
    """One supported output programming language.

    Canonical identity: eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/LanguageType; version: 1.
    Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd}LanguageType; version: 1."""

    JAVA = 'java'
    PYTHON = 'python'

    def code(self) -> str:
        """Return the exact typed wire code."""
        return self.value
