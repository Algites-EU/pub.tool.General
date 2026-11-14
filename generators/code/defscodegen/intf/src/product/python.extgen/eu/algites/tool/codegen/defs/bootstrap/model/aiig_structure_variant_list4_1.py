from __future__ import annotations
from typing import Any

from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field import AIaXmlDataObjectField
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
from dataclasses import dataclass
from typing import final
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from .aiig_structure_1 import AIigStructure_1


@final
@dataclass(frozen=True)
class AIigStructureVariantList4_1(AIigStructure_1):
    """Exclusive canonical object variant"""
    __xml_choice_component_names__ = ('List',)
    __xml_choice_first_qnames__ = ('{https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}List',)
    __xml_data_object_fields__ = {
        'List': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='List', value_kind=AInXmlValueKind.ELEMENT, ),
    }

    field1: AIigList_1

    def __post_init__(self) -> None:
        """Validate required fields of this exact alternative."""
        if self.field1 is None:
            raise ValueError('List' + " is required")

    def getList(self) -> AIigList_1:
        """Return field List."""
        return self.field1
