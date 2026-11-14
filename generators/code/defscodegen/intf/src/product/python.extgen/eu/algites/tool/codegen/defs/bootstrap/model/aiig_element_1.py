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
from eu.algites.lib.data.dataobject.jsondefs.aia_json_data_object import AIaJsonDataObject
from eu.algites.lib.data.dataobject.yamldefs.aia_yaml_data_object import AIaYamlDataObject
from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field import AIaXmlDataObjectField
from eu.algites.lib.data.dataobject.xmlschema.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind

if TYPE_CHECKING:
    from .aing_element_kind_1 import AIngElementKind_1
    from .aiig_structure_1 import AIigStructure_1
    from .aiig_xml_wire_name_1 import AIigXmlWireName_1
    from .aiig_key_definition_1 import AIigKeyDefinition_1
    from .aiig_source_bindings_1 import AIigSourceBindings_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject
from eu.algites.lib.data.dataobject.xmlschema.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigElement_1(AIiDataObject):
    """Member of an ELEMENTLIST: referenced serialized member or unnamed embedded structural group."""

    __data_object__ = AIcdDataObject(description='Member of an ELEMENTLIST: referenced serialized member or unnamed embedded structural group.')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Element', schema_version=1)
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Element', schema_version=1)
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Element', schema_version=1)

    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Element')

    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Element')

    __xml_scalar_type_imports__ = {'element_kind': 'eu.algites.tool.codegen.defs.model.aing_element_kind_1:AIngElementKind_1'}

    __xml_data_object_fields__ = {
        'element_kind': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='element_kind', value_kind=AInXmlValueKind.ELEMENT, ),
        'name': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='name', value_kind=AInXmlValueKind.ELEMENT, ),
        'structure': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='structure', value_kind=AInXmlValueKind.ELEMENT, ),
        'description': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='description', value_kind=AInXmlValueKind.ELEMENT, ),
        'xml_wire': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='xml_wire', value_kind=AInXmlValueKind.ELEMENT, ),
        'key_definitions': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='key_definitions', value_kind=AInXmlValueKind.ELEMENT, ),
        'source_bindings': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='source_bindings', value_kind=AInXmlValueKind.ELEMENT, ),
        'min_item_count': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='min_item_count', value_kind=AInXmlValueKind.ELEMENT, ),
        'max_item_count': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='max_item_count', value_kind=AInXmlValueKind.ELEMENT, ),
        'default_kind': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='default_kind', value_kind=AInXmlValueKind.ELEMENT, ),
        'default_value': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='default_value', value_kind=AInXmlValueKind.ELEMENT, ),
        'is_empty_allowed': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='is_empty_allowed', value_kind=AInXmlValueKind.ELEMENT, ),
    }

    __xml_schema_fields__ = {
        'element_kind': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='element_kind', value_kind=AInXmlValueKind.ELEMENT),
        'name': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='name', value_kind=AInXmlValueKind.ELEMENT),
        'structure': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='structure', value_kind=AInXmlValueKind.ELEMENT),
        'description': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='description', value_kind=AInXmlValueKind.ELEMENT),
        'xml_wire': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='xml_wire', value_kind=AInXmlValueKind.ELEMENT),
        'key_definitions': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='key_definitions', value_kind=AInXmlValueKind.ELEMENT),
        'source_bindings': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='source_bindings', value_kind=AInXmlValueKind.ELEMENT),
        'min_item_count': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='min_item_count', value_kind=AInXmlValueKind.ELEMENT),
        'max_item_count': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='max_item_count', value_kind=AInXmlValueKind.ELEMENT),
        'default_kind': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='default_kind', value_kind=AInXmlValueKind.ELEMENT),
        'default_value': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='default_value', value_kind=AInXmlValueKind.ELEMENT),
        'is_empty_allowed': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='is_empty_allowed', value_kind=AInXmlValueKind.ELEMENT),
    }

    __xml_repeated_fields__ = ('key_definitions',)

    class CONSTElement:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__ELEMENT_KIND = 'element_kind'
        FIELD_NAME__NAME = 'name'
        FIELD_NAME__STRUCTURE = 'structure'
        FIELD_NAME__DESCRIPTION = 'description'
        FIELD_NAME__XML_WIRE = 'xml_wire'
        FIELD_NAME__KEY_DEFINITIONS = 'key_definitions'
        FIELD_NAME__SOURCE_BINDINGS = 'source_bindings'
        FIELD_NAME__MIN_ITEM_COUNT = 'min_item_count'
        FIELD_NAME__MAX_ITEM_COUNT = 'max_item_count'
        FIELD_NAME__DEFAULT_KIND = 'default_kind'
        FIELD_NAME__DEFAULT_VALUE = 'default_value'
        FIELD_NAME__IS_EMPTY_ALLOWED = 'is_empty_allowed'

    @AIaDataObjectField(dataFieldName='element_kind', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getElementKind(self) -> AIngElementKind_1:
        """Return Canonical field element_kind. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='name', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=str, order=1, min_item_count=1, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getName(self) -> str:
        """Return Canonical field name. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='structure', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=2, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getStructure(self) -> AIigStructure_1:
        """Return Canonical field structure. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='description', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=str, order=3, min_item_count=0, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getDescription(self) -> str:
        """Return Canonical field description. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='xml_wire', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, order=4, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getXmlWire(self) -> AIigXmlWireName_1:
        """Return Canonical field xml_wire. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='key_definitions', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=list, order=5, min_item_count=0, max_item_count=-1, is_empty_allowed=False)
    @abstractmethod
    def getKeyDefinitionsList(self) -> list[AIigKeyDefinition_1]:
        """Return Canonical field key_definitions. (optional, cardinality 0..-1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='source_bindings', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, order=6, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getSourceBindings(self) -> AIigSourceBindings_1:
        """Return Canonical field source_bindings. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='min_item_count', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=int, order=7, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getMinItemCount(self) -> int:
        """Return Canonical field min_item_count. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='max_item_count', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=int, order=8, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getMaxItemCount(self) -> int:
        """Return Canonical field max_item_count. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='default_kind', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=str, order=9, min_item_count=0, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getDefaultKind(self) -> str:
        """Return Canonical field default_kind. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='default_value', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=str, order=10, min_item_count=0, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getDefaultValue(self) -> str:
        """Return Canonical field default_value. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='is_empty_allowed', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=bool, order=11, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getIsEmptyAllowed(self) -> bool:
        """Return Canonical field is_empty_allowed. (optional, cardinality 0..1)."""
        raise NotImplementedError

