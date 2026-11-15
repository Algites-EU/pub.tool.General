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

if TYPE_CHECKING:
    from .aing_xml_wire_name_value_kind_1 import AIngXmlWireNameValueKind_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigXmlWireName_1(AIiDataObject):
    """Exact XML field QName and attribute/element kind, independent of semantic schema ID."""

    __data_object__ = AIcdDataObject(description='Exact XML field QName and attribute/element kind, independent of semantic schema ID.')
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/XmlWireName', schema_version=1)
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/XmlWireName', schema_version=1)

    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='XmlWireName')

    __xml_scalar_type_imports__ = {'value_kind': 'eu.algites.tool.codegen.defs.model.aing_xml_wire_name_value_kind_1:AIngXmlWireNameValueKind_1'}

    __xml_schema_fields__ = {
        'NamespaceUri': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='namespace_uri', value_kind=AInXmlValueKind.ELEMENT),
        'LocalName': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='local_name', value_kind=AInXmlValueKind.ELEMENT),
        'ValueKind': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='value_kind', value_kind=AInXmlValueKind.ELEMENT),
    }

    class CONSTXmlWireName:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__NAMESPACE_URI = 'namespace_uri'
        FIELD_NAME__LOCAL_NAME = 'local_name'
        FIELD_NAME__VALUE_KIND = 'value_kind'

    @AIaDataObjectField(dataFieldName='namespace_uri', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=str, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getNamespaceUri(self) -> str:
        """Return Canonical field namespace_uri. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='local_name', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=str, order=1, min_item_count=1, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getLocalName(self) -> str:
        """Return Canonical field local_name. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='value_kind', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=2, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getValueKind(self) -> AIngXmlWireNameValueKind_1:
        """Return Canonical field value_kind. (required, cardinality 1..1)."""
        raise NotImplementedError

