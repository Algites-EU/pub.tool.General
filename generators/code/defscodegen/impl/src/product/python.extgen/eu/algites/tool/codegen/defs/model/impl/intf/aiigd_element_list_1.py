"""Generated mutable contract for AIigElementList_1."""
from __future__ import annotations
from abc import abstractmethod
from eu.algites.tool.codegen.defs.model.aiig_element_list_1 import AIigElementList_1
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.tool.codegen.defs.model.aiig_element_list_child_1 import AIigElementListChild_1
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


class AIigdElementList_1(AIigElementList_1, AIiSmartDataObject):
    __data_object__ = AIcdDataObject(title='', description='Ordered composition of structural children', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ElementList', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ElementList', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='ElementList')
    __xml_schema_fields__ = {
        'Composition': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='composition', value_kind=AInXmlValueKind.ELEMENT),
        'ChildrenList': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='children', value_kind=AInXmlValueKind.ELEMENT),
        'MinItemCount': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='min_item_count', value_kind=AInXmlValueKind.ELEMENT),
        'MaxItemCount': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='max_item_count', value_kind=AInXmlValueKind.ELEMENT),
        'MinProperties': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='min_properties', value_kind=AInXmlValueKind.ELEMENT),
        'MaxProperties': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='max_properties', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigElementList_1, '__field_labels__', {}),
        'Composition': AIaFieldLabel(label='Composition', roleCode='field.name', labels=()),
        'ChildrenList': AIaFieldLabel(label='Children list', roleCode='field.name', labels=()),
        'MinItemCount': AIaFieldLabel(label='Min item count', roleCode='field.name', labels=()),
        'MaxItemCount': AIaFieldLabel(label='Max item count', roleCode='field.name', labels=()),
        'MinProperties': AIaFieldLabel(label='Min properties', roleCode='field.name', labels=()),
        'MaxProperties': AIaFieldLabel(label='Max properties', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setComposition(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Composition(self) -> object: ...

    @abstractmethod
    def _isPresent_Composition(self) -> bool: ...

    @abstractmethod
    def _unset_Composition(self) -> None: ...

    @abstractmethod
    def getChildrenList(self) -> AIiBoundedList[AIigElementListChild_1]: ...

    @abstractmethod
    def _getRaw_ChildrenList(self) -> AIiBoundedList[AIigElementListChild_1]: ...

    @abstractmethod
    def _isPresent_ChildrenList(self) -> bool: ...

    @abstractmethod
    def _unset_ChildrenList(self) -> None: ...

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
    def setMinProperties(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_MinProperties(self) -> object: ...

    @abstractmethod
    def _isPresent_MinProperties(self) -> bool: ...

    @abstractmethod
    def _unset_MinProperties(self) -> None: ...

    @abstractmethod
    def setMaxProperties(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_MaxProperties(self) -> object: ...

    @abstractmethod
    def _isPresent_MaxProperties(self) -> bool: ...

    @abstractmethod
    def _unset_MaxProperties(self) -> None: ...
