"""Generated mutable contract for AIigDefsCodegenNameConventionPropertyStructureNaming_1."""
from __future__ import annotations
from typing import TypeVar, Generic
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList
    from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_structure_naming_rule_1 import AIigdDefsCodegenStructureNamingRule_1
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.tool.codegen.defs.naming.aiig_defs_codegen_name_convention_property_structure_naming_1 import AIigDefsCodegenNameConventionPropertyStructureNaming_1
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject

TRuleList = TypeVar('TRuleList', bound='AIigdDefsCodegenStructureNamingRule_1')


class AIigdDefsCodegenNameConventionPropertyStructureNaming_1(AIigDefsCodegenNameConventionPropertyStructureNaming_1, AIiSmartDataObject, Generic[TRuleList]):
    __data_object__ = AIcdDataObject(title='', description='DefsCodegenNameConventionPropertyStructureNaming', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/$defs/DefsCodegenNameConvention/properties/StructureNaming#synthetic:synthetic_property_type', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json#/$defs/DefsCodegenNameConvention/properties/StructureNaming#synthetic:synthetic_property_type', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='', namespace_local_name='generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd/schema/DefsCodegenNameConvention/sequence/sequence/1#synthetic:synthetic_property_type')
    __xml_schema_fields__ = {
        'RuleList': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='Rule', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigDefsCodegenNameConventionPropertyStructureNaming_1, '__field_labels__', {}),
        'RuleList': AIaFieldLabel(label='Rule list', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def getRuleList(self) -> AIiMultiMappedList[TRuleList]: ...

    @abstractmethod
    def _getRaw_RuleList(self) -> AIiMultiMappedList[TRuleList]: ...

    @abstractmethod
    def _isPresent_RuleList(self) -> bool: ...

    @abstractmethod
    def _unset_RuleList(self) -> None: ...
