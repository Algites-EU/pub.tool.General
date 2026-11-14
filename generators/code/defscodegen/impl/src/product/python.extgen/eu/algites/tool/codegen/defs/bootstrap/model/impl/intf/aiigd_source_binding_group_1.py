"""Generated mutable contract for AIigSourceBindingGroup_1."""
from __future__ import annotations
from typing import TypeVar, Generic
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_source_binding_1 import AIigdSourceBinding_1
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
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_source_binding_group_1 import AIigSourceBindingGroup_1
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject

TBindingList = TypeVar('TBindingList', bound='AIigdSourceBinding_1')


class AIigdSourceBindingGroup_1(AIigSourceBindingGroup_1, AIiSmartDataObject, Generic[TBindingList]):
    __data_object__ = AIcdDataObject(title='', description='One source technology and all ordered bindings from that technology.', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBindingGroup', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBindingGroup', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBindingGroup', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='SourceBindingGroup')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='SourceBindingGroup')
    __xml_data_object_fields__ = {
        'InputKind': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='InputKind', value_kind=AInXmlValueKind.ELEMENT),
        'Binding': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Binding', value_kind=AInXmlValueKind.ELEMENT),
    }
    __xml_schema_fields__ = {
        'InputKind': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='InputKind', value_kind=AInXmlValueKind.ELEMENT),
        'Binding': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Binding', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigSourceBindingGroup_1, '__field_labels__', {}),
        'InputKind': AIaFieldLabel(label='Input kind', roleCode='field.name', labels=()),
        'BindingList': AIaFieldLabel(label='Binding list', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setInputKind(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_InputKind(self) -> object: ...

    @abstractmethod
    def _isPresent_InputKind(self) -> bool: ...

    @abstractmethod
    def _unset_InputKind(self) -> None: ...

    @abstractmethod
    def getBindingList(self) -> list[TBindingList]: ...

    @abstractmethod
    def _getRaw_BindingList(self) -> list[TBindingList]: ...

    @abstractmethod
    def _isPresent_BindingList(self) -> bool: ...

    @abstractmethod
    def _unset_BindingList(self) -> None: ...
