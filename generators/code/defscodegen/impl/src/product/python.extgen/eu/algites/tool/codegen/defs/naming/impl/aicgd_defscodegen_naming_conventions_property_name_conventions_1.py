"""Generated SmartDataObject implementation for AIigDefscodegenNamingConventionsPropertyNameConventions_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList
    from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_name_convention_1 import AIigdDefsCodegenNameConvention_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defscodegen_naming_conventions_property_name_conventions_1 import AIigdDefscodegenNamingConventionsPropertyNameConventions_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.naming.aiig_defscodegen_naming_conventions_property_name_conventions_1 import AIigDefscodegenNamingConventionsPropertyNameConventions_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigDefscodegenNamingConventionsPropertyNameConventions_1,))
class AIcgdDefscodegenNamingConventionsPropertyNameConventions_1(AIcSmartDataObject, AIigdDefscodegenNamingConventionsPropertyNameConventions_1['AIigdDefsCodegenNameConvention_1']):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/properties/DefsCodegenNameConventions/properties/NameConventions#synthetic:synthetic_property_type', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json#/properties/DefsCodegenNameConventions/properties/NameConventions#synthetic:synthetic_property_type', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getNameConventionList(self) -> AIiMultiMappedList[AIigdDefsCodegenNameConvention_1]:
        return self.get_OrCreateCollectionField('NameConventionList', True)

    def _getRaw_NameConventionList(self) -> AIiMultiMappedList[AIigdDefsCodegenNameConvention_1]:
        return self.get_RawField('NameConventionList')

    def _isPresent_NameConventionList(self):
        return self.isPresent_Field('NameConventionList')

    def _unset_NameConventionList(self):
        self.unset_Field('NameConventionList')
