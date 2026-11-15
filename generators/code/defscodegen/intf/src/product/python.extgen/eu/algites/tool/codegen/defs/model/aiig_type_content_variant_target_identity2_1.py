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
from .aiig_type_content_1 import AIigTypeContent_1


@final
@dataclass(frozen=True)
class AIigTypeContentVariantTargetIdentity2_1(AIigTypeContent_1):
    """Exclusive canonical object variant"""
    __xml_choice_component_names__ = ('target_identity',)
    __xml_choice_first_qnames__ = ('{https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}target_identity',)
    __xml_schema_fields__ = {
        'target_identity': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='target_identity', value_kind=AInXmlValueKind.ELEMENT, ),
    }

    field1: str

    def __post_init__(self) -> None:
        """Validate required fields of this exact alternative."""
        if self.field1 is None:
            raise ValueError('target_identity' + " is required")

    @AIaDataObjectFieldStringConstraints(min_length=1)
    def getTargetIdentity(self) -> str:
        """Return field target_identity."""
        return self.field1
