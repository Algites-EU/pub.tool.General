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
from .aiig_element_list_child_1 import AIigElementListChild_1


@final
@dataclass(frozen=True)
class AIigElementListChildVariantElementList2_1(AIigElementListChild_1):
    """Exclusive canonical object variant"""
    __xml_choice_component_names__ = ('ElementList',)
    __xml_choice_first_qnames__ = ('{https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}ElementList',)
    __xml_data_object_fields__ = {
        'ElementList': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='ElementList', value_kind=AInXmlValueKind.ELEMENT, ),
    }

    field1: AIigElementList_1

    def __post_init__(self) -> None:
        """Validate required fields of this exact alternative."""
        if self.field1 is None:
            raise ValueError('ElementList' + " is required")

    def getElementList(self) -> AIigElementList_1:
        """Return field ElementList."""
        return self.field1
