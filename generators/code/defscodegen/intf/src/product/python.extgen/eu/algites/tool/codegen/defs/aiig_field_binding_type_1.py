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
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigFieldBindingType_1(AIiDataObject):
    """Maps a schema resource and JSON pointer to an optional generated field binding."""

    __data_object__ = AIcdDataObject(description='Maps a schema resource and JSON pointer to an optional generated field binding.')
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/FieldBindingType', schema_version=1)
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/FieldBindingType', schema_version=1)

    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd', namespace_local_name='FieldBindingType')

    __xml_schema_fields__ = {
        'Schema': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd', namespace_local_name='schema', value_kind=AInXmlValueKind.ELEMENT),
        'Pointer': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd', namespace_local_name='pointer', value_kind=AInXmlValueKind.ELEMENT),
        'Name': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd', namespace_local_name='name', value_kind=AInXmlValueKind.ELEMENT),
        'CommonOneOfFields': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd', namespace_local_name='common_one_of_fields', value_kind=AInXmlValueKind.ELEMENT),
    }

    class CONSTFieldBindingType:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__SCHEMA = 'schema'
        FIELD_NAME__POINTER = 'pointer'
        FIELD_NAME__NAME = 'name'
        FIELD_NAME__COMMON_ONE_OF_FIELDS = 'common_one_of_fields'

    @AIaDataObjectFieldStringConstraints(min_length=1)
    @AIaDataObjectField(dataFieldName='schema', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=str, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getSchema(self) -> str:
        """Return Canonical URI or path identifying the source schema. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='pointer', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=str, order=1, min_item_count=0, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getPointer(self) -> str:
        """Return Optional JSON Pointer identifying a particular position within the schema. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectFieldStringConstraints(min_length=1)
    @AIaDataObjectField(dataFieldName='name', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=str, order=2, min_item_count=0, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getName(self) -> str:
        """Return Optional override of the generated binding name. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='common_one_of_fields', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=bool, order=3, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getCommonOneOfFields(self) -> bool:
        """Return Whether shared fields from oneOf branches are retained in bindings. (optional, cardinality 0..1)."""
        raise NotImplementedError

