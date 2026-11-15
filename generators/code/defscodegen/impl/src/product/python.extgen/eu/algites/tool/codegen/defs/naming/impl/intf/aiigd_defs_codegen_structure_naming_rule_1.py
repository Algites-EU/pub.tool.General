"""Generated mutable contract for AIigDefsCodegenStructureNamingRule_1."""
from __future__ import annotations
from abc import abstractmethod
from eu.algites.tool.codegen.defs.naming.aiig_defs_codegen_structure_naming_rule_1 import AIigDefsCodegenStructureNamingRule_1
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


class AIigdDefsCodegenStructureNamingRule_1(AIigDefsCodegenStructureNamingRule_1, AIiSmartDataObject):
    __data_object__ = AIcdDataObject(title='', description='DefsCodegenStructureNamingRule', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenStructureNamingRule', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenStructureNamingRule', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd', namespace_local_name='DefsCodegenStructureNamingRule')
    __xml_schema_fields__ = {
        'Value': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='Value', value_kind=AInXmlValueKind.ELEMENT),
        'Kind': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='kind', value_kind=AInXmlValueKind.ATTRIBUTE),
    }
    __field_labels__ = {**getattr(AIigDefsCodegenStructureNamingRule_1, '__field_labels__', {}),
        'Value': AIaFieldLabel(label='Value', roleCode='field.name', labels=()),
        'Kind': AIaFieldLabel(label='Kind', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setValue(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Value(self) -> object: ...

    @abstractmethod
    def _isPresent_Value(self) -> bool: ...

    @abstractmethod
    def _unset_Value(self) -> None: ...

    @abstractmethod
    def _setEmpty_Value(self) -> None: ...

    @abstractmethod
    def _isEmpty_Value(self) -> bool: ...

    @abstractmethod
    def setKind(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Kind(self) -> object: ...

    @abstractmethod
    def _isPresent_Kind(self) -> bool: ...

    @abstractmethod
    def _unset_Kind(self) -> None: ...
