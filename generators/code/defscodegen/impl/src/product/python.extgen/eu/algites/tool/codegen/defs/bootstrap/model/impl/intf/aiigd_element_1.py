"""Generated mutable contract for AIigElement_1."""
from __future__ import annotations
from typing import TypeVar, Generic
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.common.list.aii_bounded_list import AIiBoundedList
    from eu.algites.tool.codegen.defs.bootstrap.model.aiig_structure_1 import AIigStructure_1
    from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_key_definition_1 import AIigdKeyDefinition_1
    from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_source_bindings_1 import AIigdSourceBindings_1
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
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_element_1 import AIigElement_1
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject

TXmlWire = TypeVar('TXmlWire', bound='AIigdXmlWireName_1')
TKeyDefinitionsList = TypeVar('TKeyDefinitionsList', bound='AIigdKeyDefinition_1')
TSourceBindings = TypeVar('TSourceBindings', bound='AIigdSourceBindings_1')


class AIigdElement_1(AIigElement_1, AIiSmartDataObject, Generic[TXmlWire, TKeyDefinitionsList, TSourceBindings]):
    __data_object__ = AIcdDataObject(title='', description='Member of an ELEMENTLIST: referenced serialized member or unnamed embedded structural group.', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Element', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Element', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Element', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Element')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Element')
    __xml_data_object_fields__ = {
        'element_kind': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='element_kind', value_kind=AInXmlValueKind.ELEMENT),
        'name': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='name', value_kind=AInXmlValueKind.ELEMENT),
        'structure': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='structure', value_kind=AInXmlValueKind.ELEMENT),
        'description': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='description', value_kind=AInXmlValueKind.ELEMENT),
        'xml_wire': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='xml_wire', value_kind=AInXmlValueKind.ELEMENT),
        'key_definitions': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='key_definitions', value_kind=AInXmlValueKind.ELEMENT),
        'source_bindings': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='source_bindings', value_kind=AInXmlValueKind.ELEMENT),
        'min_item_count': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='min_item_count', value_kind=AInXmlValueKind.ELEMENT),
        'max_item_count': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='max_item_count', value_kind=AInXmlValueKind.ELEMENT),
        'default_kind': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='default_kind', value_kind=AInXmlValueKind.ELEMENT),
        'default_value': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='default_value', value_kind=AInXmlValueKind.ELEMENT),
        'is_empty_allowed': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='is_empty_allowed', value_kind=AInXmlValueKind.ELEMENT),
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
    __field_labels__ = {**getattr(AIigElement_1, '__field_labels__', {}),
        'ElementKind': AIaFieldLabel(label='Element kind', roleCode='field.name', labels=()),
        'Name': AIaFieldLabel(label='Name', roleCode='field.name', labels=()),
        'Structure': AIaFieldLabel(label='Structure', roleCode='field.name', labels=()),
        'Description': AIaFieldLabel(label='Description', roleCode='field.name', labels=()),
        'XmlWire': AIaFieldLabel(label='Xml wire', roleCode='field.name', labels=()),
        'KeyDefinitionsList': AIaFieldLabel(label='Key definitions list', roleCode='field.name', labels=()),
        'SourceBindings': AIaFieldLabel(label='Source bindings', roleCode='field.name', labels=()),
        'MinItemCount': AIaFieldLabel(label='Min item count', roleCode='field.name', labels=()),
        'MaxItemCount': AIaFieldLabel(label='Max item count', roleCode='field.name', labels=()),
        'DefaultKind': AIaFieldLabel(label='Default kind', roleCode='field.name', labels=()),
        'DefaultValue': AIaFieldLabel(label='Default value', roleCode='field.name', labels=()),
        'IsEmptyAllowed': AIaFieldLabel(label='Is empty allowed', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setElementKind(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_ElementKind(self) -> object: ...

    @abstractmethod
    def _isPresent_ElementKind(self) -> bool: ...

    @abstractmethod
    def _unset_ElementKind(self) -> None: ...

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
    def getStructure(self) -> AIigStructure_1: ...

    @abstractmethod
    def setStructure(self, a_value: AIigStructure_1) -> None: ...

    @abstractmethod
    def _getRaw_Structure(self) -> AIigStructure_1: ...

    @abstractmethod
    def _isPresent_Structure(self) -> bool: ...

    @abstractmethod
    def _unset_Structure(self) -> None: ...

    @abstractmethod
    def setDescription(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Description(self) -> object: ...

    @abstractmethod
    def _isPresent_Description(self) -> bool: ...

    @abstractmethod
    def _unset_Description(self) -> None: ...

    @abstractmethod
    def _setEmpty_Description(self) -> None: ...

    @abstractmethod
    def _isEmpty_Description(self) -> bool: ...

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
    def getKeyDefinitionsList(self) -> AIiBoundedList[TKeyDefinitionsList]: ...

    @abstractmethod
    def _getRaw_KeyDefinitionsList(self) -> AIiBoundedList[TKeyDefinitionsList]: ...

    @abstractmethod
    def _isPresent_KeyDefinitionsList(self) -> bool: ...

    @abstractmethod
    def _unset_KeyDefinitionsList(self) -> None: ...

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
    def setDefaultKind(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_DefaultKind(self) -> object: ...

    @abstractmethod
    def _isPresent_DefaultKind(self) -> bool: ...

    @abstractmethod
    def _unset_DefaultKind(self) -> None: ...

    @abstractmethod
    def _setEmpty_DefaultKind(self) -> None: ...

    @abstractmethod
    def _isEmpty_DefaultKind(self) -> bool: ...

    @abstractmethod
    def setDefaultValue(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_DefaultValue(self) -> object: ...

    @abstractmethod
    def _isPresent_DefaultValue(self) -> bool: ...

    @abstractmethod
    def _unset_DefaultValue(self) -> None: ...

    @abstractmethod
    def _setEmpty_DefaultValue(self) -> None: ...

    @abstractmethod
    def _isEmpty_DefaultValue(self) -> bool: ...

    @abstractmethod
    def setIsEmptyAllowed(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_IsEmptyAllowed(self) -> object: ...

    @abstractmethod
    def _isPresent_IsEmptyAllowed(self) -> bool: ...

    @abstractmethod
    def _unset_IsEmptyAllowed(self) -> None: ...
