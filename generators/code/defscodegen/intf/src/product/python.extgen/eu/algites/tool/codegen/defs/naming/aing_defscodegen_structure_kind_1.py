from __future__ import annotations
from typing import Any

from enum import Enum


class AIngDefscodegenStructureKind_1(str, Enum):
    """Strictly typed naming role vocabulary for the defs domain. Roles in other domains are forbidden.

    Canonical identity: eu.algites.tool.codegen.defs.naming.defscodegen-structure-kind; version: 1.
    Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-structure-kind_1.xsd}DefscodegenStructureKind; version: 1."""

    SYNTHETIC_PROPERTY_TYPE = 'synthetic_property_type'
    SYNTHETIC_INLINE_ENUM_TYPE = 'synthetic_inline_enum_type'
    SYNTHETIC_LIST_ITEM_TYPE = 'synthetic_list_item_type'
    SYNTHETIC_MAP_VALUE_TYPE = 'synthetic_map_value_type'
    SYNTHETIC_POSITIONAL_ITEM_TYPE = 'synthetic_positional_item_type'
    SYNTHETIC_CHOICE_VARIANT_TYPE = 'synthetic_choice_variant_type'
    SYNTHETIC_GROUP_TYPE = 'synthetic_group_type'
    STRING_ENUM_ITEM = 'string_enum_item'
    NON_STRING_ENUM_ITEM = 'non_string_enum_item'

    def code(self) -> str:
        """Return the exact typed wire code."""
        return self.value
