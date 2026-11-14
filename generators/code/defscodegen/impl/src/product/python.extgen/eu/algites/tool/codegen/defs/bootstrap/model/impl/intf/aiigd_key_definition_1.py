"""Generated mutable contract for AIigKeyDefinition_1."""
from __future__ import annotations
from abc import abstractmethod
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_key_definition_1 import AIigKeyDefinition_1
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
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject


class AIigdKeyDefinition_1(AIigKeyDefinition_1, AIiSmartDataObject):
    __data_object__ = AIcdDataObject(title='', description='Deferred XML key constraint', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/KeyDefinition', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/KeyDefinition', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/KeyDefinition', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='KeyDefinition')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='KeyDefinition')
    __xml_data_object_fields__ = {
        'identifier': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='identifier', value_kind=AInXmlValueKind.ELEMENT),
        'selector': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='selector', value_kind=AInXmlValueKind.ELEMENT),
        'source_pointer': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='source_pointer', value_kind=AInXmlValueKind.ELEMENT),
        'fields': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='fields', value_kind=AInXmlValueKind.ELEMENT),
        'required': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='required', value_kind=AInXmlValueKind.ELEMENT),
    }
    __xml_schema_fields__ = {
        'identifier': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='identifier', value_kind=AInXmlValueKind.ELEMENT),
        'selector': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='selector', value_kind=AInXmlValueKind.ELEMENT),
        'source_pointer': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='source_pointer', value_kind=AInXmlValueKind.ELEMENT),
        'fields': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='fields', value_kind=AInXmlValueKind.ELEMENT),
        'required': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='required', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigKeyDefinition_1, '__field_labels__', {}),
        'Identifier': AIaFieldLabel(label='Identifier', roleCode='field.name', labels=()),
        'Selector': AIaFieldLabel(label='Selector', roleCode='field.name', labels=()),
        'SourcePointer': AIaFieldLabel(label='Source pointer', roleCode='field.name', labels=()),
        'FieldsList': AIaFieldLabel(label='Fields list', roleCode='field.name', labels=()),
        'Required': AIaFieldLabel(label='Required', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setIdentifier(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Identifier(self) -> object: ...

    @abstractmethod
    def _isPresent_Identifier(self) -> bool: ...

    @abstractmethod
    def _unset_Identifier(self) -> None: ...

    @abstractmethod
    def _setEmpty_Identifier(self) -> None: ...

    @abstractmethod
    def _isEmpty_Identifier(self) -> bool: ...

    @abstractmethod
    def setSelector(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Selector(self) -> object: ...

    @abstractmethod
    def _isPresent_Selector(self) -> bool: ...

    @abstractmethod
    def _unset_Selector(self) -> None: ...

    @abstractmethod
    def _setEmpty_Selector(self) -> None: ...

    @abstractmethod
    def _isEmpty_Selector(self) -> bool: ...

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
    def _getRaw_FieldsList(self) -> object: ...

    @abstractmethod
    def _isPresent_FieldsList(self) -> bool: ...

    @abstractmethod
    def _unset_FieldsList(self) -> None: ...

    @abstractmethod
    def setRequired(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Required(self) -> object: ...

    @abstractmethod
    def _isPresent_Required(self) -> bool: ...

    @abstractmethod
    def _unset_Required(self) -> None: ...
