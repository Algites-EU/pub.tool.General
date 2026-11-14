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
    from .aing_type_origin_1 import AIngTypeOrigin_1
    from .aiig_type_content_1 import AIigTypeContent_1
    from .aing_resolution_state_1 import AIngResolutionState_1
    from .aiig_source_bindings_1 import AIigSourceBindings_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject
from eu.algites.lib.data.dataobject.xmlschema.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigType_1(AIiDataObject):
    """Declared or synthetic named type"""

    __data_object__ = AIcdDataObject(description='Declared or synthetic named type')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Type', schema_version=1)
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Type', schema_version=1)
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Type', schema_version=1)

    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Type')

    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Type')

    __xml_scalar_type_imports__ = {'origin': 'eu.algites.tool.codegen.defs.model.aing_type_origin_1:AIngTypeOrigin_1', 'resolution_state': 'eu.algites.tool.codegen.defs.model.aing_resolution_state_1:AIngResolutionState_1'}

    __xml_data_object_fields__ = {
        'identity': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='identity', value_kind=AInXmlValueKind.ELEMENT, ),
        'name': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='name', value_kind=AInXmlValueKind.ELEMENT, ),
        'origin': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='origin', value_kind=AInXmlValueKind.ELEMENT, ),
        'schema_version': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='schema_version', value_kind=AInXmlValueKind.ELEMENT, ),
        'description': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='description', value_kind=AInXmlValueKind.ELEMENT, ),
        'path_segments': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='path_segments', value_kind=AInXmlValueKind.ELEMENT, ),
        'inherited_from_types': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='inherited_from_types', value_kind=AInXmlValueKind.ELEMENT, ),
        'content': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='content', value_kind=AInXmlValueKind.ELEMENT, ),
        'resolution_state': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='resolution_state', value_kind=AInXmlValueKind.ELEMENT, ),
        'source_bindings': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='source_bindings', value_kind=AInXmlValueKind.ELEMENT, ),
    }

    __xml_schema_fields__ = {
        'identity': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='identity', value_kind=AInXmlValueKind.ELEMENT),
        'name': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='name', value_kind=AInXmlValueKind.ELEMENT),
        'origin': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='origin', value_kind=AInXmlValueKind.ELEMENT),
        'schema_version': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='schema_version', value_kind=AInXmlValueKind.ELEMENT),
        'description': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='description', value_kind=AInXmlValueKind.ELEMENT),
        'path_segments': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='path_segments', value_kind=AInXmlValueKind.ELEMENT),
        'inherited_from_types': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='inherited_from_types', value_kind=AInXmlValueKind.ELEMENT),
        'content': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='content', value_kind=AInXmlValueKind.ELEMENT),
        'resolution_state': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='resolution_state', value_kind=AInXmlValueKind.ELEMENT),
        'source_bindings': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='source_bindings', value_kind=AInXmlValueKind.ELEMENT),
    }

    __xml_repeated_fields__ = ('path_segments', 'inherited_from_types')

    class CONSTType:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__IDENTITY = 'identity'
        FIELD_NAME__NAME = 'name'
        FIELD_NAME__ORIGIN = 'origin'
        FIELD_NAME__SCHEMA_VERSION = 'schema_version'
        FIELD_NAME__DESCRIPTION = 'description'
        FIELD_NAME__PATH_SEGMENTS = 'path_segments'
        FIELD_NAME__INHERITED_FROM_TYPES = 'inherited_from_types'
        FIELD_NAME__CONTENT = 'content'
        FIELD_NAME__RESOLUTION_STATE = 'resolution_state'
        FIELD_NAME__SOURCE_BINDINGS = 'source_bindings'

    @AIaDataObjectField(dataFieldName='identity', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=str, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getIdentity(self) -> str:
        """Return Canonical field identity. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='name', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=str, order=1, min_item_count=1, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getName(self) -> str:
        """Return Canonical field name. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='origin', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=2, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getOrigin(self) -> AIngTypeOrigin_1:
        """Return Canonical field origin. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='schema_version', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=str, order=3, min_item_count=0, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getSchemaVersion(self) -> str:
        """Return Canonical field schema_version. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='description', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=str, order=4, min_item_count=0, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getDescription(self) -> str:
        """Return Canonical field description. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='path_segments', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=list, order=5, min_item_count=0, max_item_count=-1, is_empty_allowed=False)
    @abstractmethod
    def getPathSegmentsList(self) -> list[str]:
        """Return Canonical field path_segments. (optional, cardinality 0..-1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='inherited_from_types', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=list, order=6, min_item_count=0, max_item_count=-1, is_empty_allowed=False)
    @abstractmethod
    def getInheritedFromTypesList(self) -> list[str]:
        """Return Canonical field inherited_from_types. (optional, cardinality 0..-1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='content', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=7, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getContent(self) -> AIigTypeContent_1:
        """Return Canonical field content. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='resolution_state', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=8, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getResolutionState(self) -> AIngResolutionState_1:
        """Return Canonical field resolution_state. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='source_bindings', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, order=9, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getSourceBindings(self) -> AIigSourceBindings_1:
        """Return Canonical field source_bindings. (optional, cardinality 0..1)."""
        raise NotImplementedError

