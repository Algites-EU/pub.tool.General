from __future__ import annotations
from typing import Any

from enum import Enum


class AIngXmlWireNameValueKind_1(str, Enum):
    """Schema enum

    Canonical identity: generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json#/$defs/XmlWireName/properties/value_kind#synthetic:synthetic_inline_enum_type; version: 1.
    Equivalent schema identity: generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd/schema/XmlWireName/sequence/sequence/2#synthetic:synthetic_inline_enum_type; version: 1.
    Equivalent schema identity: generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.yamldef.schema.json#/$defs/XmlWireName/properties/value_kind#synthetic:synthetic_inline_enum_type; version: 1."""

    ELEMENT = 'ELEMENT'
    ATTRIBUTE = 'ATTRIBUTE'

    def code(self) -> str:
        """Return the exact typed wire code."""
        return self.value
