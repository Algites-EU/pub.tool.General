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
    from .aing_composition_1 import AIngComposition_1
    from .aiig_element_list_child_1 import AIigElementListChild_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigElementList_1(AIiDataObject):
    """Ordered composition of structural children"""

    __data_object__ = AIcdDataObject(description='Ordered composition of structural children')
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ElementList', schema_version=1)
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ElementList', schema_version=1)

    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='ElementList')

    __xml_scalar_type_imports__ = {'composition': 'eu.algites.tool.codegen.defs.model.aing_composition_1:AIngComposition_1'}

    __xml_schema_fields__ = {
        'Composition': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='composition', value_kind=AInXmlValueKind.ELEMENT),
        'ChildrenList': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='children', value_kind=AInXmlValueKind.ELEMENT),
        'MinItemCount': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='min_item_count', value_kind=AInXmlValueKind.ELEMENT),
        'MaxItemCount': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='max_item_count', value_kind=AInXmlValueKind.ELEMENT),
        'MinProperties': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='min_properties', value_kind=AInXmlValueKind.ELEMENT),
        'MaxProperties': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='max_properties', value_kind=AInXmlValueKind.ELEMENT),
    }

    __xml_repeated_fields__ = ('ChildrenList',)

    class CONSTElementList:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__COMPOSITION = 'composition'
        FIELD_NAME__CHILDREN = 'children'
        FIELD_NAME__MIN_ITEM_COUNT = 'min_item_count'
        FIELD_NAME__MAX_ITEM_COUNT = 'max_item_count'
        FIELD_NAME__MIN_PROPERTIES = 'min_properties'
        FIELD_NAME__MAX_PROPERTIES = 'max_properties'

    @AIaDataObjectField(dataFieldName='composition', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getComposition(self) -> AIngComposition_1:
        """Return Canonical field composition. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectFieldListConstraints(min_items=1)
    @AIaDataObjectField(dataFieldName='children', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=AIiBoundedList, order=1, min_item_count=1, max_item_count=-1, is_empty_allowed=False)
    @abstractmethod
    def getChildrenList(self) -> AIiBoundedList[AIigElementListChild_1]:
        """Return Canonical field children. (required, cardinality 1..-1)."""
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

    @AIaDataObjectField(dataFieldName='min_properties', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=int, order=4, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getMinProperties(self) -> int:
        """Return Canonical field min_properties. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='max_properties', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=int, order=5, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getMaxProperties(self) -> int:
        """Return Canonical field max_properties. (optional, cardinality 0..1)."""
        raise NotImplementedError

