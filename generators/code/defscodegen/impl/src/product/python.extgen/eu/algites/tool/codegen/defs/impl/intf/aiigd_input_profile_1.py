"""Generated mutable contract for AIigInputProfile_1."""
from __future__ import annotations
from abc import abstractmethod
from eu.algites.tool.codegen.defs.aiig_input_profile_1 import AIigInputProfile_1
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


class AIigdInputProfile_1(AIigInputProfile_1, AIiSmartDataObject):
    __data_object__ = AIcdDataObject(title='', description='Root document configuring one input-definition family.', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.input-profile', schema_version=1, schema_url='https://defs.dev.algites.eu/api/jsondefs/eu/algites/tool/codegen/defs/input-profile_1.jsondef.schema.json', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.input-profile', schema_version=1, schema_url='https://defs.dev.algites.eu/api/yamldefs/eu/algites/tool/codegen/defs/input-profile_1.yamldef.schema.json', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.ELEMENT, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd', namespace_local_name='InputProfile')
    __xml_schema_fields__ = {
        'SourceKind': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd', namespace_local_name='SourceKind', value_kind=AInXmlValueKind.ELEMENT),
        'NamingProfile': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd', namespace_local_name='NamingProfile', value_kind=AInXmlValueKind.ELEMENT),
        'RequireCanonicalIdentity': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd', namespace_local_name='RequireCanonicalIdentity', value_kind=AInXmlValueKind.ELEMENT),
        'RequireDefinitionVersion': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd', namespace_local_name='RequireDefinitionVersion', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigInputProfile_1, '__field_labels__', {}),
        'SourceKind': AIaFieldLabel(label='Source kind', roleCode='field.name', labels=()),
        'NamingProfile': AIaFieldLabel(label='Naming profile', roleCode='field.name', labels=()),
        'RequireCanonicalIdentity': AIaFieldLabel(label='Require canonical identity', roleCode='field.name', labels=()),
        'RequireDefinitionVersion': AIaFieldLabel(label='Require definition version', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setSourceKind(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_SourceKind(self) -> object: ...

    @abstractmethod
    def _isPresent_SourceKind(self) -> bool: ...

    @abstractmethod
    def _unset_SourceKind(self) -> None: ...

    @abstractmethod
    def setNamingProfile(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_NamingProfile(self) -> object: ...

    @abstractmethod
    def _isPresent_NamingProfile(self) -> bool: ...

    @abstractmethod
    def _unset_NamingProfile(self) -> None: ...

    @abstractmethod
    def _setEmpty_NamingProfile(self) -> None: ...

    @abstractmethod
    def _isEmpty_NamingProfile(self) -> bool: ...

    @abstractmethod
    def setRequireCanonicalIdentity(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_RequireCanonicalIdentity(self) -> object: ...

    @abstractmethod
    def _isPresent_RequireCanonicalIdentity(self) -> bool: ...

    @abstractmethod
    def _unset_RequireCanonicalIdentity(self) -> None: ...

    @abstractmethod
    def setRequireDefinitionVersion(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_RequireDefinitionVersion(self) -> object: ...

    @abstractmethod
    def _isPresent_RequireDefinitionVersion(self) -> bool: ...

    @abstractmethod
    def _unset_RequireDefinitionVersion(self) -> None: ...
