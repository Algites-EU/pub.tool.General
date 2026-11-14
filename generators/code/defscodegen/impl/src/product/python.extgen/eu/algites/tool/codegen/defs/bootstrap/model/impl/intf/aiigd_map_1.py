"""Generated mutable contract for AIigMap_1."""
from __future__ import annotations
from typing import TypeVar, Generic
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.tool.codegen.defs.bootstrap.model.aiig_structure_1 import AIigStructure_1
    from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_source_bindings_1 import AIigdSourceBindings_1
from eu.algites.lib.data.dataobject.xmlschema.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field import AIaXmlDataObjectField
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
from eu.algites.lib.data.dataobject.xmlschema.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
from eu.algites.lib.data.dataobject.yamldefs.aia_yaml_data_object import AIaYamlDataObject
from eu.algites.lib.data.dataobject.jsondefs.aia_json_data_object import AIaJsonDataObject
from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_map_1 import AIigMap_1
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject

TSourceBindings = TypeVar('TSourceBindings', bound='AIigdSourceBindings_1')


class AIigdMap_1(AIigMap_1, AIiSmartDataObject, Generic[TSourceBindings]):
    __data_object__ = AIcdDataObject(title='', description='Ordinary or integrated property map', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Map', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Map', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Map', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Map')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Map')
    __xml_data_object_fields__ = {
        'name': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='name', value_kind=AInXmlValueKind.ELEMENT),
        'map_kind': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='map_kind', value_kind=AInXmlValueKind.ELEMENT),
        'key_type': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='key_type', value_kind=AInXmlValueKind.ELEMENT),
        'value_type': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='value_type', value_kind=AInXmlValueKind.ELEMENT),
        'source_bindings': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='source_bindings', value_kind=AInXmlValueKind.ELEMENT),
    }
    __xml_schema_fields__ = {
        'name': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='name', value_kind=AInXmlValueKind.ELEMENT),
        'map_kind': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='map_kind', value_kind=AInXmlValueKind.ELEMENT),
        'key_type': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='key_type', value_kind=AInXmlValueKind.ELEMENT),
        'value_type': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='value_type', value_kind=AInXmlValueKind.ELEMENT),
        'source_bindings': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='source_bindings', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigMap_1, '__field_labels__', {}),
        'Name': AIaFieldLabel(label='Name', roleCode='field.name', labels=()),
        'MapKind': AIaFieldLabel(label='Map kind', roleCode='field.name', labels=()),
        'KeyType': AIaFieldLabel(label='Key type', roleCode='field.name', labels=()),
        'ValueType': AIaFieldLabel(label='Value type', roleCode='field.name', labels=()),
        'SourceBindings': AIaFieldLabel(label='Source bindings', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setName(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Name(self) -> object: ...

    @abstractmethod
    def _isPresent_Name(self) -> bool: ...

    @abstractmethod
    def _unset_Name(self) -> None: ...

    @abstractmethod
    def _setEmpty_Name(self) -> None: ...

    @abstractmethod
    def _isEmpty_Name(self) -> bool: ...

    @abstractmethod
    def setMapKind(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_MapKind(self) -> object: ...

    @abstractmethod
    def _isPresent_MapKind(self) -> bool: ...

    @abstractmethod
    def _unset_MapKind(self) -> None: ...

    @abstractmethod
    def getKeyType(self) -> AIigStructure_1: ...

    @abstractmethod
    def setKeyType(self, a_value: AIigStructure_1) -> None: ...

    @abstractmethod
    def _getRaw_KeyType(self) -> AIigStructure_1: ...

    @abstractmethod
    def _isPresent_KeyType(self) -> bool: ...

    @abstractmethod
    def _unset_KeyType(self) -> None: ...

    @abstractmethod
    def getValueType(self) -> AIigStructure_1: ...

    @abstractmethod
    def setValueType(self, a_value: AIigStructure_1) -> None: ...

    @abstractmethod
    def _getRaw_ValueType(self) -> AIigStructure_1: ...

    @abstractmethod
    def _isPresent_ValueType(self) -> bool: ...

    @abstractmethod
    def _unset_ValueType(self) -> None: ...

    @abstractmethod
    def getSourceBindings(self) -> TSourceBindings: ...

    @abstractmethod
    def setSourceBindings(self, a_value: TSourceBindings) -> None: ...

    @abstractmethod
    def _getRaw_SourceBindings(self) -> TSourceBindings: ...

    @abstractmethod
    def _isPresent_SourceBindings(self) -> bool: ...

    @abstractmethod
    def _unset_SourceBindings(self) -> None: ...
