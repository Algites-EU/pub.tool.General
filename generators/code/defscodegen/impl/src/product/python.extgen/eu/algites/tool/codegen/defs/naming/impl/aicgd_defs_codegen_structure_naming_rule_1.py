"""Generated SmartDataObject implementation for AIigDefsCodegenStructureNamingRule_1."""
from __future__ import annotations
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_structure_naming_rule_1 import AIigdDefsCodegenStructureNamingRule_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.naming.aiig_defs_codegen_structure_naming_rule_1 import AIigDefsCodegenStructureNamingRule_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigDefsCodegenStructureNamingRule_1,))
class AIcgdDefsCodegenStructureNamingRule_1(AIcSmartDataObject, AIigdDefsCodegenStructureNamingRule_1):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenStructureNamingRule', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenStructureNamingRule', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getValue(self):
        return self.get_EffectiveField('Value')

    def setValue(self, a_value):
        self.set_RawField('Value', a_value)

    def _getRaw_Value(self):
        return self.get_RawField('Value')

    def _isPresent_Value(self):
        return self.isPresent_Field('Value')

    def _unset_Value(self):
        self.unset_Field('Value')

    def _setEmpty_Value(self):
        self.set_EmptyField('Value')

    def _isEmpty_Value(self):
        return self.isEmpty_Field('Value')

    def getKind(self):
        return self.get_EffectiveField('Kind')

    def setKind(self, a_value):
        self.set_RawField('Kind', a_value)

    def _getRaw_Kind(self):
        return self.get_RawField('Kind')

    def _isPresent_Kind(self):
        return self.isPresent_Field('Kind')

    def _unset_Kind(self):
        self.unset_Field('Kind')
