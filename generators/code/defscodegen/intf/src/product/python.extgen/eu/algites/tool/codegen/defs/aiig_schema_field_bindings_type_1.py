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
    from .aing_language_type_1 import AIngLanguageType_1
    from .aiig_field_binding_type_1 import AIigFieldBindingType_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigSchemaFieldBindingsType_1(AIiDataObject):
    """Generator instructions identifying canonical JSON Schema resources and optional field-binding projections."""

    __data_object__ = AIcdDataObject(description='Generator instructions identifying canonical JSON Schema resources and optional field-binding projections.')
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/SchemaFieldBindingsType', schema_version=1)
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/SchemaFieldBindingsType', schema_version=1)

    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd', namespace_local_name='SchemaFieldBindingsType')

    __xml_schema_fields__ = {
        'Artifact': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd', namespace_local_name='artifact', value_kind=AInXmlValueKind.ELEMENT),
        'ImplementationArtifact': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd', namespace_local_name='implementation_artifact', value_kind=AInXmlValueKind.ELEMENT),
        'LanguagesList': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd', namespace_local_name='languages', value_kind=AInXmlValueKind.ELEMENT),
        'BindingsList': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd', namespace_local_name='bindings', value_kind=AInXmlValueKind.ELEMENT),
    }

    __xml_repeated_fields__ = ('LanguagesList', 'BindingsList')

    class CONSTSchemaFieldBindingsType:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__ARTIFACT = 'artifact'
        FIELD_NAME__IMPLEMENTATION_ARTIFACT = 'implementation_artifact'
        FIELD_NAME__LANGUAGES = 'languages'
        FIELD_NAME__BINDINGS = 'bindings'

    @AIaDataObjectFieldStringConstraints(min_length=1)
    @AIaDataObjectField(dataFieldName='artifact', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=str, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getArtifact(self) -> str:
        """Return Specifies the artifact associated with this definition. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectFieldStringConstraints(min_length=1)
    @AIaDataObjectField(dataFieldName='implementation_artifact', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=str, order=1, min_item_count=0, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getImplementationArtifact(self) -> str:
        """Return Specifies the implementation artifact associated with this definition. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectFieldListConstraints(min_items=1)
    @AIaDataObjectField(dataFieldName='languages', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=AIiBoundedList, order=2, min_item_count=1, max_item_count=-1, is_empty_allowed=False)
    @abstractmethod
    def getLanguagesList(self) -> AIiBoundedList[AIngLanguageType_1]:
        """Return Canonical field languages. (required, cardinality 1..-1)."""
        raise NotImplementedError

    @AIaDataObjectFieldListConstraints(min_items=1)
    @AIaDataObjectField(dataFieldName='bindings', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=AIiBoundedList, order=3, min_item_count=1, max_item_count=-1, is_empty_allowed=False)
    @abstractmethod
    def getBindingsList(self) -> AIiBoundedList[AIigFieldBindingType_1]:
        """Return Canonical field bindings. (required, cardinality 1..-1)."""
        raise NotImplementedError

