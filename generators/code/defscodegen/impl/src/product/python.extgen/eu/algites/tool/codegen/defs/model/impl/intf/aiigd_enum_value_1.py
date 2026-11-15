"""Generated mutable contract for AIigEnumValue_1."""
from __future__ import annotations
from abc import abstractmethod
from eu.algites.tool.codegen.defs.model.aiig_enum_value_1 import AIigEnumValue_1
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


class AIigdEnumValue_1(AIigEnumValue_1, AIiSmartDataObject):
    __data_object__ = AIcdDataObject(title='', description='Canonical enumeration value', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/EnumValue', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/EnumValue', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='EnumValue')
    __xml_schema_fields__ = {
        'WireValue': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='wire_value', value_kind=AInXmlValueKind.ELEMENT),
        'DisplayName': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='display_name', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigEnumValue_1, '__field_labels__', {}),
        'WireValue': AIaFieldLabel(label='Wire value', roleCode='field.name', labels=()),
        'DisplayName': AIaFieldLabel(label='Display name', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setWireValue(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_WireValue(self) -> object: ...

    @abstractmethod
    def _isPresent_WireValue(self) -> bool: ...

    @abstractmethod
    def _unset_WireValue(self) -> None: ...

    @abstractmethod
    def _setEmpty_WireValue(self) -> None: ...

    @abstractmethod
    def _isEmpty_WireValue(self) -> bool: ...

    @abstractmethod
    def setDisplayName(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_DisplayName(self) -> object: ...

    @abstractmethod
    def _isPresent_DisplayName(self) -> bool: ...

    @abstractmethod
    def _unset_DisplayName(self) -> None: ...

    @abstractmethod
    def _setEmpty_DisplayName(self) -> None: ...

    @abstractmethod
    def _isEmpty_DisplayName(self) -> bool: ...
