"""Generated mutable contract for AIigFieldBindingType_1."""
from __future__ import annotations
from abc import abstractmethod
from eu.algites.tool.codegen.defs.aiig_field_binding_type_1 import AIigFieldBindingType_1
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


class AIigdFieldBindingType_1(AIigFieldBindingType_1, AIiSmartDataObject):
    __data_object__ = AIcdDataObject(title='', description='Maps a schema resource and JSON pointer to an optional generated field binding.', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/FieldBindingType', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/FieldBindingType', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd', namespace_local_name='FieldBindingType')
    __xml_schema_fields__ = {
        'Schema': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd', namespace_local_name='schema', value_kind=AInXmlValueKind.ELEMENT),
        'Pointer': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd', namespace_local_name='pointer', value_kind=AInXmlValueKind.ELEMENT),
        'Name': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd', namespace_local_name='name', value_kind=AInXmlValueKind.ELEMENT),
        'CommonOneOfFields': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.xsd', namespace_local_name='common_one_of_fields', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigFieldBindingType_1, '__field_labels__', {}),
        'Schema': AIaFieldLabel(label='Schema', roleCode='field.name', labels=()),
        'Pointer': AIaFieldLabel(label='Pointer', roleCode='field.name', labels=()),
        'Name': AIaFieldLabel(label='Name', roleCode='field.name', labels=()),
        'CommonOneOfFields': AIaFieldLabel(label='Common one of fields', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setSchema(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Schema(self) -> object: ...

    @abstractmethod
    def _isPresent_Schema(self) -> bool: ...

    @abstractmethod
    def _unset_Schema(self) -> None: ...

    @abstractmethod
    def _setEmpty_Schema(self) -> None: ...

    @abstractmethod
    def _isEmpty_Schema(self) -> bool: ...

    @abstractmethod
    def setPointer(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Pointer(self) -> object: ...

    @abstractmethod
    def _isPresent_Pointer(self) -> bool: ...

    @abstractmethod
    def _unset_Pointer(self) -> None: ...

    @abstractmethod
    def _setEmpty_Pointer(self) -> None: ...

    @abstractmethod
    def _isEmpty_Pointer(self) -> bool: ...

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
    def setCommonOneOfFields(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_CommonOneOfFields(self) -> object: ...

    @abstractmethod
    def _isPresent_CommonOneOfFields(self) -> bool: ...

    @abstractmethod
    def _unset_CommonOneOfFields(self) -> None: ...
