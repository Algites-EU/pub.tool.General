"""Generated SmartDataObject implementation for AIigFieldBindingType_1."""
from __future__ import annotations
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.impl.intf.aiigd_field_binding_type_1 import AIigdFieldBindingType_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.aiig_field_binding_type_1 import AIigFieldBindingType_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigFieldBindingType_1,))
class AIcgdFieldBindingType_1(AIcSmartDataObject, AIigdFieldBindingType_1):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/FieldBindingType', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.schema-field-bindings#/$defs/FieldBindingType', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getSchema(self):
        return self.get_EffectiveField('Schema')

    def setSchema(self, a_value):
        self.set_RawField('Schema', a_value)

    def _getRaw_Schema(self):
        return self.get_RawField('Schema')

    def _isPresent_Schema(self):
        return self.isPresent_Field('Schema')

    def _unset_Schema(self):
        self.unset_Field('Schema')

    def _setEmpty_Schema(self):
        self.set_EmptyField('Schema')

    def _isEmpty_Schema(self):
        return self.isEmpty_Field('Schema')

    def getPointer(self):
        return self.get_EffectiveField('Pointer')

    def setPointer(self, a_value):
        self.set_RawField('Pointer', a_value)

    def _getRaw_Pointer(self):
        return self.get_RawField('Pointer')

    def _isPresent_Pointer(self):
        return self.isPresent_Field('Pointer')

    def _unset_Pointer(self):
        self.unset_Field('Pointer')

    def _setEmpty_Pointer(self):
        self.set_EmptyField('Pointer')

    def _isEmpty_Pointer(self):
        return self.isEmpty_Field('Pointer')

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

    def getCommonOneOfFields(self):
        return self.get_EffectiveField('CommonOneOfFields')

    def setCommonOneOfFields(self, a_value):
        self.set_RawField('CommonOneOfFields', a_value)

    def _getRaw_CommonOneOfFields(self):
        return self.get_RawField('CommonOneOfFields')

    def _isPresent_CommonOneOfFields(self):
        return self.isPresent_Field('CommonOneOfFields')

    def _unset_CommonOneOfFields(self):
        self.unset_Field('CommonOneOfFields')
