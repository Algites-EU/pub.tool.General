"""Generated mutable contract for AIigDefsCodegenNameConvention_1."""
from __future__ import annotations
from typing import TypeVar, Generic
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_name_convention_property_structure_naming_1 import AIigdDefsCodegenNameConventionPropertyStructureNaming_1
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.tool.codegen.defs.naming.aiig_defs_codegen_name_convention_1 import AIigDefsCodegenNameConvention_1
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject

TStructureNaming = TypeVar('TStructureNaming', bound='AIigdDefsCodegenNameConventionPropertyStructureNaming_1')


class AIigdDefsCodegenNameConvention_1(AIigDefsCodegenNameConvention_1, AIiSmartDataObject, Generic[TStructureNaming]):
    __data_object__ = AIcdDataObject(title='', description='DefsCodegenNameConvention', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenNameConvention', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenNameConvention', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd', namespace_local_name='DefsCodegenNameConvention')
    __xml_schema_fields__ = {
        'CommonNamingConvention': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='CommonNamingConvention', value_kind=AInXmlValueKind.ELEMENT),
        'StructureNaming': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='StructureNaming', value_kind=AInXmlValueKind.ELEMENT),
        'Name': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='name', value_kind=AInXmlValueKind.ATTRIBUTE),
    }
    __field_labels__ = {**getattr(AIigDefsCodegenNameConvention_1, '__field_labels__', {}),
        'CommonNamingConvention': AIaFieldLabel(label='Common naming convention', roleCode='field.name', labels=()),
        'StructureNaming': AIaFieldLabel(label='Structure naming', roleCode='field.name', labels=()),
        'Name': AIaFieldLabel(label='Name', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setCommonNamingConvention(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_CommonNamingConvention(self) -> object: ...

    @abstractmethod
    def _isPresent_CommonNamingConvention(self) -> bool: ...

    @abstractmethod
    def _unset_CommonNamingConvention(self) -> None: ...

    @abstractmethod
    def _setEmpty_CommonNamingConvention(self) -> None: ...

    @abstractmethod
    def _isEmpty_CommonNamingConvention(self) -> bool: ...

    @abstractmethod
    def getStructureNaming(self) -> TStructureNaming: ...

    @abstractmethod
    def setStructureNaming(self, a_value: TStructureNaming) -> None: ...

    @abstractmethod
    def _getRaw_StructureNaming(self) -> TStructureNaming: ...

    @abstractmethod
    def _isPresent_StructureNaming(self) -> bool: ...

    @abstractmethod
    def _unset_StructureNaming(self) -> None: ...

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
