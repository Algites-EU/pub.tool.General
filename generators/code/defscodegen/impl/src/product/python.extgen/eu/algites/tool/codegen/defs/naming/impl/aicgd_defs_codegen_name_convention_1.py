"""Generated SmartDataObject implementation for AIigDefsCodegenNameConvention_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_name_convention_property_structure_naming_1 import AIigdDefsCodegenNameConventionPropertyStructureNaming_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_name_convention_1 import AIigdDefsCodegenNameConvention_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.naming.aiig_defs_codegen_name_convention_1 import AIigDefsCodegenNameConvention_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigDefsCodegenNameConvention_1,))
class AIcgdDefsCodegenNameConvention_1(AIcSmartDataObject, AIigdDefsCodegenNameConvention_1['AIigdDefsCodegenNameConventionPropertyStructureNaming_1']):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenNameConvention', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenNameConvention', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getCommonNamingConvention(self):
        return self.get_EffectiveField('CommonNamingConvention')

    def setCommonNamingConvention(self, a_value):
        self.set_RawField('CommonNamingConvention', a_value)

    def _getRaw_CommonNamingConvention(self):
        return self.get_RawField('CommonNamingConvention')

    def _isPresent_CommonNamingConvention(self):
        return self.isPresent_Field('CommonNamingConvention')

    def _unset_CommonNamingConvention(self):
        self.unset_Field('CommonNamingConvention')

    def _setEmpty_CommonNamingConvention(self):
        self.set_EmptyField('CommonNamingConvention')

    def _isEmpty_CommonNamingConvention(self):
        return self.isEmpty_Field('CommonNamingConvention')

    def getStructureNaming(self) -> AIigdDefsCodegenNameConventionPropertyStructureNaming_1:
        return self.get_EffectiveField('StructureNaming')

    def setStructureNaming(self, a_value: AIigdDefsCodegenNameConventionPropertyStructureNaming_1):
        self.set_RawField('StructureNaming', a_value)

    def _getRaw_StructureNaming(self) -> AIigdDefsCodegenNameConventionPropertyStructureNaming_1:
        return self.get_RawField('StructureNaming')

    def _isPresent_StructureNaming(self):
        return self.isPresent_Field('StructureNaming')

    def _unset_StructureNaming(self):
        self.unset_Field('StructureNaming')

    def getName(self):
        return self.get_EffectiveField('Name')

    def setName(self, a_value):
        self.set_RawField('Name', a_value)

    def _getRaw_Name(self):
        return self.get_RawField('Name')

    def _isPresent_Name(self):
        return self.isPresent_Field('Name')

    def _unset_Name(self):
        self.unset_Field('Name')

    def _setEmpty_Name(self):
        self.set_EmptyField('Name')

    def _isEmpty_Name(self):
        return self.isEmpty_Field('Name')
