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


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigKeyDefinition_1(AIiDataObject):
    """Deferred XML key constraint"""

    __data_object__ = AIcdDataObject(description='Deferred XML key constraint')
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/KeyDefinition', schema_version=1)
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/KeyDefinition', schema_version=1)

    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='KeyDefinition')

    __xml_schema_fields__ = {
        'Identifier': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='identifier', value_kind=AInXmlValueKind.ELEMENT),
        'Selector': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='selector', value_kind=AInXmlValueKind.ELEMENT),
        'SourcePointer': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='source_pointer', value_kind=AInXmlValueKind.ELEMENT),
        'FieldsList': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='fields', value_kind=AInXmlValueKind.ELEMENT),
        'Required': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='required', value_kind=AInXmlValueKind.ELEMENT),
    }

    __xml_repeated_fields__ = ('FieldsList',)

    class CONSTKeyDefinition:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__IDENTIFIER = 'identifier'
        FIELD_NAME__SELECTOR = 'selector'
        FIELD_NAME__SOURCE_POINTER = 'source_pointer'
        FIELD_NAME__FIELDS = 'fields'
        FIELD_NAME__REQUIRED = 'required'

    @AIaDataObjectField(dataFieldName='identifier', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=str, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getIdentifier(self) -> str:
        """Return Canonical field identifier. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='selector', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=str, order=1, min_item_count=1, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getSelector(self) -> str:
        """Return Canonical field selector. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='source_pointer', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=str, order=2, min_item_count=1, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getSourcePointer(self) -> str:
        """Return Canonical field source_pointer. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='fields', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=AIiBoundedList, order=3, min_item_count=0, max_item_count=-1, is_empty_allowed=False)
    @abstractmethod
    def getFieldsList(self) -> AIiBoundedList[str]:
        """Return Canonical field fields. (optional, cardinality 0..-1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='required', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=bool, order=4, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getRequired(self) -> bool:
        """Return Canonical field required. (optional, cardinality 0..1)."""
        raise NotImplementedError

