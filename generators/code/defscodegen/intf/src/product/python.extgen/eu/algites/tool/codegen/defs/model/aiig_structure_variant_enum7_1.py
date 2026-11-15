from __future__ import annotations
from typing import Any

from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
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
class AIigStructureVariantEnum7_1(AIigStructure_1):
    """Exclusive canonical object variant"""
    __xml_choice_component_names__ = ('Enum',)
    __xml_choice_first_qnames__ = ('{https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}Enum',)
    __xml_schema_fields__ = {
        'Enum': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Enum', value_kind=AInXmlValueKind.ELEMENT, ),
    }

    field1: AIigEnum_1

    def __post_init__(self) -> None:
        """Validate required fields of this exact alternative."""
        if self.field1 is None:
            raise ValueError('Enum' + " is required")

    def getEnum(self) -> AIigEnum_1:
        """Return field Enum."""
        return self.field1
