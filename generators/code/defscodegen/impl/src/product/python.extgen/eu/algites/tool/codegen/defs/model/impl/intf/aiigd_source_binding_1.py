"""Generated mutable contract for AIigSourceBinding_1."""
from __future__ import annotations
from abc import abstractmethod
from eu.algites.tool.codegen.defs.model.aiig_source_binding_1 import AIigSourceBinding_1
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


class AIigdSourceBinding_1(AIigSourceBinding_1, AIiSmartDataObject):
    __data_object__ = AIcdDataObject(title='', description='Exact source binding', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBinding', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBinding', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='SourceBinding')
    __xml_schema_fields__ = {
        'SourceResource': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='source_resource', value_kind=AInXmlValueKind.ELEMENT),
        'SourcePointer': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='source_pointer', value_kind=AInXmlValueKind.ELEMENT),
        'RepresentationKind': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='representation_kind', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigSourceBinding_1, '__field_labels__', {}),
        'SourceResource': AIaFieldLabel(label='Source resource', roleCode='field.name', labels=()),
        'SourcePointer': AIaFieldLabel(label='Source pointer', roleCode='field.name', labels=()),
        'RepresentationKind': AIaFieldLabel(label='Representation kind', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setSourceResource(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_SourceResource(self) -> object: ...

    @abstractmethod
    def _isPresent_SourceResource(self) -> bool: ...

    @abstractmethod
    def _unset_SourceResource(self) -> None: ...

    @abstractmethod
    def _setEmpty_SourceResource(self) -> None: ...

    @abstractmethod
    def _isEmpty_SourceResource(self) -> bool: ...

    @abstractmethod
    def setSourcePointer(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_SourcePointer(self) -> object: ...

    @abstractmethod
    def _isPresent_SourcePointer(self) -> bool: ...

    @abstractmethod
    def _unset_SourcePointer(self) -> None: ...

    @abstractmethod
    def _setEmpty_SourcePointer(self) -> None: ...

    @abstractmethod
    def _isEmpty_SourcePointer(self) -> bool: ...

    @abstractmethod
    def setRepresentationKind(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_RepresentationKind(self) -> object: ...

    @abstractmethod
    def _isPresent_RepresentationKind(self) -> bool: ...

    @abstractmethod
    def _unset_RepresentationKind(self) -> None: ...

    @abstractmethod
    def _setEmpty_RepresentationKind(self) -> None: ...

    @abstractmethod
    def _isEmpty_RepresentationKind(self) -> bool: ...
