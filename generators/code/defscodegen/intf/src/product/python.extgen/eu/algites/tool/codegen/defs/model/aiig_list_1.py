from __future__ import annotations
from typing import Any

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.lib.data.dataobject.aia_data_object_field_default import AIaDataObjectFieldDefault
from eu.algites.lib.data.dataobject.ain_data_object_field_default_kind import AInDataObjectFieldDefaultKind
from eu.algites.lib.data.dataobject.aii_field_default_scalar_value_factory import AIiFieldDefaultScalarValueFactory
from eu.algites.lib.factory.cpdiscovery.aia_category_provider_factory_definition import AIaCategoryProviderFactoryDefinition
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.common.list.aii_bounded_list import AIiBoundedList
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind

if TYPE_CHECKING:
    from .aiig_structure_1 import AIigStructure_1
    from .aiig_xml_wire_name_1 import AIigXmlWireName_1
    from .aiig_key_definition_1 import AIigKeyDefinition_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigList_1(AIiDataObject):
    """Homogeneous collection"""

    __data_object__ = AIcdDataObject(description='Homogeneous collection')
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/List', schema_version=1)
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/List', schema_version=1)

    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='List')

    __xml_schema_fields__ = {
        'Name': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='name', value_kind=AInXmlValueKind.ELEMENT),
        'Item': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='item', value_kind=AInXmlValueKind.ELEMENT),
        'MinItemCount': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='min_item_count', value_kind=AInXmlValueKind.ELEMENT),
        'MaxItemCount': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='max_item_count', value_kind=AInXmlValueKind.ELEMENT),
        'XmlWire': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='xml_wire', value_kind=AInXmlValueKind.ELEMENT),
        'KeyDefinitionsList': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='key_definitions', value_kind=AInXmlValueKind.ELEMENT),
        'UniqueItems': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='unique_items', value_kind=AInXmlValueKind.ELEMENT),
    }

    __xml_repeated_fields__ = ('KeyDefinitionsList',)

    class CONSTList:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__NAME = 'name'
        FIELD_NAME__ITEM = 'item'
        FIELD_NAME__MIN_ITEM_COUNT = 'min_item_count'
        FIELD_NAME__MAX_ITEM_COUNT = 'max_item_count'
        FIELD_NAME__XML_WIRE = 'xml_wire'
        FIELD_NAME__KEY_DEFINITIONS = 'key_definitions'
        FIELD_NAME__UNIQUE_ITEMS = 'unique_items'

    @AIaDataObjectField(dataFieldName='name', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=str, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getName(self) -> str:
        """Return Canonical field name. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='item', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=1, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getItem(self) -> AIigStructure_1:
        """Return Canonical field item. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='min_item_count', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=int, order=2, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getMinItemCount(self) -> int:
        """Return Canonical field min_item_count. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='max_item_count', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=int, order=3, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getMaxItemCount(self) -> int:
        """Return Canonical field max_item_count. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='xml_wire', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, order=4, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getXmlWire(self) -> AIigXmlWireName_1:
        """Return Canonical field xml_wire. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='key_definitions', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=AIiBoundedList, order=5, min_item_count=0, max_item_count=-1, is_empty_allowed=False)
    @abstractmethod
    def getKeyDefinitionsList(self) -> AIiBoundedList[AIigKeyDefinition_1]:
        """Return Canonical field key_definitions. (optional, cardinality 0..-1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='unique_items', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=bool, order=6, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getUniqueItems(self) -> bool:
        """Return Canonical field unique_items. (optional, cardinality 0..1)."""
        raise NotImplementedError

