from __future__ import annotations
from typing import Any

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.lib.data.dataobject.aia_data_object_field_default import AIaDataObjectFieldDefault
from eu.algites.lib.data.dataobject.ain_data_object_field_default_kind import AInDataObjectFieldDefaultKind
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.common.list.aii_bounded_list import AIiBoundedList
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind

if TYPE_CHECKING:
    from .aing_scalar_kind_1 import AIngScalarKind_1
    from .aiig_enum_value_1 import AIigEnumValue_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigEnum_1(AIiDataObject):
    """Canonical enumeration"""

    __data_object__ = AIcdDataObject(description='Canonical enumeration')
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Enum', schema_version=1)
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Enum', schema_version=1)

    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Enum')

    __xml_scalar_type_imports__ = {'base_scalar_type': 'eu.algites.tool.codegen.defs.model.aing_scalar_kind_1:AIngScalarKind_1'}

    __xml_schema_fields__ = {
        'BaseScalarType': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='base_scalar_type', value_kind=AInXmlValueKind.ELEMENT),
        'ValuesList': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='values', value_kind=AInXmlValueKind.ELEMENT),
    }

    __xml_repeated_fields__ = ('ValuesList',)

    class CONSTEnum:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__BASE_SCALAR_TYPE = 'base_scalar_type'
        FIELD_NAME__VALUES = 'values'

    @AIaDataObjectField(dataFieldName='base_scalar_type', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getBaseScalarType(self) -> AIngScalarKind_1:
        """Return Canonical field base_scalar_type. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectFieldListConstraints(min_items=1)
    @AIaDataObjectField(dataFieldName='values', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=AIiBoundedList, order=1, min_item_count=1, max_item_count=-1, is_empty_allowed=False)
    @abstractmethod
    def getValuesList(self) -> AIiBoundedList[AIigEnumValue_1]:
        """Return Canonical field values. (required, cardinality 1..-1)."""
        raise NotImplementedError

