"""Generated mutable contract for AIigXmlWireName_1."""
from __future__ import annotations
from abc import abstractmethod
from eu.algites.tool.codegen.defs.model.aiig_xml_wire_name_1 import AIigXmlWireName_1
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject


class AIigdXmlWireName_1(AIigXmlWireName_1, AIiSmartDataObject):
    __data_object__ = AIcdDataObject(title='', description='Exact XML field QName and attribute/element kind, independent of semantic schema ID.', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/XmlWireName', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/XmlWireName', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='XmlWireName')
    __xml_schema_fields__ = {
        'NamespaceUri': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='namespace_uri', value_kind=AInXmlValueKind.ELEMENT),
        'LocalName': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='local_name', value_kind=AInXmlValueKind.ELEMENT),
        'ValueKind': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='value_kind', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigXmlWireName_1, '__field_labels__', {}),
        'NamespaceUri': AIaFieldLabel(label='Namespace uri', roleCode='field.name', labels=()),
        'LocalName': AIaFieldLabel(label='Local name', roleCode='field.name', labels=()),
        'ValueKind': AIaFieldLabel(label='Value kind', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setNamespaceUri(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_NamespaceUri(self) -> object: ...

    @abstractmethod
    def _isPresent_NamespaceUri(self) -> bool: ...

    @abstractmethod
    def _unset_NamespaceUri(self) -> None: ...

    @abstractmethod
    def _setEmpty_NamespaceUri(self) -> None: ...

    @abstractmethod
    def _isEmpty_NamespaceUri(self) -> bool: ...

    @abstractmethod
    def setLocalName(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_LocalName(self) -> object: ...

    @abstractmethod
    def _isPresent_LocalName(self) -> bool: ...

    @abstractmethod
    def _unset_LocalName(self) -> None: ...

    @abstractmethod
    def _setEmpty_LocalName(self) -> None: ...

    @abstractmethod
    def _isEmpty_LocalName(self) -> bool: ...

    @abstractmethod
    def setValueKind(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_ValueKind(self) -> object: ...

    @abstractmethod
    def _isPresent_ValueKind(self) -> bool: ...

    @abstractmethod
    def _unset_ValueKind(self) -> None: ...
