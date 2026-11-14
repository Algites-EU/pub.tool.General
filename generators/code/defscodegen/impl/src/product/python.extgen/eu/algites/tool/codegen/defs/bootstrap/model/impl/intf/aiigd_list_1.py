"""Generated mutable contract for AIigList_1."""
from __future__ import annotations
from typing import TypeVar, Generic
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.tool.codegen.defs.bootstrap.model.aiig_structure_1 import AIigStructure_1
    from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_key_definition_1 import AIigdKeyDefinition_1
    from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_xml_wire_name_1 import AIigdXmlWireName_1
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
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_list_1 import AIigList_1
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject

TXmlWire = TypeVar('TXmlWire', bound='AIigdXmlWireName_1')
TKeyDefinitionsList = TypeVar('TKeyDefinitionsList', bound='AIigdKeyDefinition_1')


class AIigdList_1(AIigList_1, AIiSmartDataObject, Generic[TXmlWire, TKeyDefinitionsList]):
    __data_object__ = AIcdDataObject(title='', description='Homogeneous collection', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/List', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/List', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/List', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='List')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='List')
    __xml_data_object_fields__ = {
        'name': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='name', value_kind=AInXmlValueKind.ELEMENT),
        'item': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='item', value_kind=AInXmlValueKind.ELEMENT),
        'min_item_count': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='min_item_count', value_kind=AInXmlValueKind.ELEMENT),
        'max_item_count': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='max_item_count', value_kind=AInXmlValueKind.ELEMENT),
        'xml_wire': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='xml_wire', value_kind=AInXmlValueKind.ELEMENT),
        'key_definitions': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='key_definitions', value_kind=AInXmlValueKind.ELEMENT),
        'unique_items': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='unique_items', value_kind=AInXmlValueKind.ELEMENT),
    }
    __xml_schema_fields__ = {
        'name': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='name', value_kind=AInXmlValueKind.ELEMENT),
        'item': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='item', value_kind=AInXmlValueKind.ELEMENT),
        'min_item_count': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='min_item_count', value_kind=AInXmlValueKind.ELEMENT),
        'max_item_count': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='max_item_count', value_kind=AInXmlValueKind.ELEMENT),
        'xml_wire': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='xml_wire', value_kind=AInXmlValueKind.ELEMENT),
        'key_definitions': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='key_definitions', value_kind=AInXmlValueKind.ELEMENT),
        'unique_items': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='unique_items', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigList_1, '__field_labels__', {}),
        'Name': AIaFieldLabel(label='Name', roleCode='field.name', labels=()),
        'Item': AIaFieldLabel(label='Item', roleCode='field.name', labels=()),
        'MinItemCount': AIaFieldLabel(label='Min item count', roleCode='field.name', labels=()),
        'MaxItemCount': AIaFieldLabel(label='Max item count', roleCode='field.name', labels=()),
        'XmlWire': AIaFieldLabel(label='Xml wire', roleCode='field.name', labels=()),
        'KeyDefinitionsList': AIaFieldLabel(label='Key definitions list', roleCode='field.name', labels=()),
        'UniqueItems': AIaFieldLabel(label='Unique items', roleCode='field.name', labels=()),
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
    def getItem(self) -> AIigStructure_1: ...

    @abstractmethod
    def setItem(self, a_value: AIigStructure_1) -> None: ...

    @abstractmethod
    def _getRaw_Item(self) -> AIigStructure_1: ...

    @abstractmethod
    def _isPresent_Item(self) -> bool: ...

    @abstractmethod
    def _unset_Item(self) -> None: ...

    @abstractmethod
    def setMinItemCount(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_MinItemCount(self) -> object: ...

    @abstractmethod
    def _isPresent_MinItemCount(self) -> bool: ...

    @abstractmethod
    def _unset_MinItemCount(self) -> None: ...

    @abstractmethod
    def setMaxItemCount(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_MaxItemCount(self) -> object: ...

    @abstractmethod
    def _isPresent_MaxItemCount(self) -> bool: ...

    @abstractmethod
    def _unset_MaxItemCount(self) -> None: ...

    @abstractmethod
    def getXmlWire(self) -> TXmlWire: ...

    @abstractmethod
    def setXmlWire(self, a_value: TXmlWire) -> None: ...

    @abstractmethod
    def _getRaw_XmlWire(self) -> TXmlWire: ...

    @abstractmethod
    def _isPresent_XmlWire(self) -> bool: ...

    @abstractmethod
    def _unset_XmlWire(self) -> None: ...

    @abstractmethod
    def getKeyDefinitionsList(self) -> list[TKeyDefinitionsList]: ...

    @abstractmethod
    def _getRaw_KeyDefinitionsList(self) -> list[TKeyDefinitionsList]: ...

    @abstractmethod
    def _isPresent_KeyDefinitionsList(self) -> bool: ...

    @abstractmethod
    def _unset_KeyDefinitionsList(self) -> None: ...

    @abstractmethod
    def setUniqueItems(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_UniqueItems(self) -> object: ...

    @abstractmethod
    def _isPresent_UniqueItems(self) -> bool: ...

    @abstractmethod
    def _unset_UniqueItems(self) -> None: ...
