"""Generated SmartDataObject implementation for AIigEnumValue_1."""
from __future__ import annotations
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.model.impl.intf.aiigd_enum_value_1 import AIigdEnumValue_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.model.aiig_enum_value_1 import AIigEnumValue_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigEnumValue_1,))
class AIcgdEnumValue_1(AIcSmartDataObject, AIigdEnumValue_1):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/EnumValue', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/EnumValue', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getWireValue(self):
        return self.get_EffectiveField('WireValue')

    def setWireValue(self, a_value):
        self.set_RawField('WireValue', a_value)

    def _getRaw_WireValue(self):
        return self.get_RawField('WireValue')

    def _isPresent_WireValue(self):
        return self.isPresent_Field('WireValue')

    def _unset_WireValue(self):
        self.unset_Field('WireValue')

    def _setEmpty_WireValue(self):
        self.set_EmptyField('WireValue')

    def _isEmpty_WireValue(self):
        return self.isEmpty_Field('WireValue')

    def getDisplayName(self):
        return self.get_EffectiveField('DisplayName')

    def setDisplayName(self, a_value):
        self.set_RawField('DisplayName', a_value)

    def _getRaw_DisplayName(self):
        return self.get_RawField('DisplayName')

    def _isPresent_DisplayName(self):
        return self.isPresent_Field('DisplayName')

    def _unset_DisplayName(self):
        self.unset_Field('DisplayName')

    def _setEmpty_DisplayName(self):
        self.set_EmptyField('DisplayName')

    def _isEmpty_DisplayName(self):
        return self.isEmpty_Field('DisplayName')
