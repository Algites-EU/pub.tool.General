"""Generated SmartDataObject implementation for AIigDefsCodegenNameConventionPropertyStructureNaming_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList
    from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_structure_naming_rule_1 import AIigdDefsCodegenStructureNamingRule_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_name_convention_property_structure_naming_1 import AIigdDefsCodegenNameConventionPropertyStructureNaming_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.naming.aiig_defs_codegen_name_convention_property_structure_naming_1 import AIigDefsCodegenNameConventionPropertyStructureNaming_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigDefsCodegenNameConventionPropertyStructureNaming_1,))
class AIcgdDefsCodegenNameConventionPropertyStructureNaming_1(AIcSmartDataObject, AIigdDefsCodegenNameConventionPropertyStructureNaming_1['AIigdDefsCodegenStructureNamingRule_1']):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/$defs/DefsCodegenNameConvention/properties/StructureNaming#synthetic:synthetic_property_type', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json#/$defs/DefsCodegenNameConvention/properties/StructureNaming#synthetic:synthetic_property_type', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getRuleList(self) -> AIiMultiMappedList[AIigdDefsCodegenStructureNamingRule_1]:
        return self.get_OrCreateCollectionField('RuleList', True)

    def _getRaw_RuleList(self) -> AIiMultiMappedList[AIigdDefsCodegenStructureNamingRule_1]:
        return self.get_RawField('RuleList')

    def _isPresent_RuleList(self):
        return self.isPresent_Field('RuleList')

    def _unset_RuleList(self):
        self.unset_Field('RuleList')
