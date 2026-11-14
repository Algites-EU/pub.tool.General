"""Generated SmartDataObject implementation for AIigScalar_1."""
from __future__ import annotations
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_yaml_data_object import AIaYamlDataObject
from eu.algites.lib.data.dataobject.jsondefs.aia_json_data_object import AIaJsonDataObject
from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_scalar_1 import AIigdScalar_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_scalar_1 import AIigScalar_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigScalar_1,))
class AIcgdScalar_1(AIcSmartDataObject, AIigdScalar_1):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Scalar', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Scalar', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Scalar', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getScalarKind(self):
        return self.get_EffectiveField('ScalarKind')

    def setScalarKind(self, a_value):
        self.set_RawField('ScalarKind', a_value)

    def _getRaw_ScalarKind(self):
        return self.get_RawField('ScalarKind')

    def _isPresent_ScalarKind(self):
        return self.isPresent_Field('ScalarKind')

    def _unset_ScalarKind(self):
        self.unset_Field('ScalarKind')

    def getFormat(self):
        return self.get_EffectiveField('Format')

    def setFormat(self, a_value):
        self.set_RawField('Format', a_value)

    def _getRaw_Format(self):
        return self.get_RawField('Format')

    def _isPresent_Format(self):
        return self.isPresent_Field('Format')

    def _unset_Format(self):
        self.unset_Field('Format')

    def _setEmpty_Format(self):
        self.set_EmptyField('Format')

    def _isEmpty_Format(self):
        return self.isEmpty_Field('Format')

    def getMinLength(self):
        return self.get_EffectiveField('MinLength')

    def setMinLength(self, a_value):
        self.set_RawField('MinLength', a_value)

    def _getRaw_MinLength(self):
        return self.get_RawField('MinLength')

    def _isPresent_MinLength(self):
        return self.isPresent_Field('MinLength')

    def _unset_MinLength(self):
        self.unset_Field('MinLength')

    def getMaxLength(self):
        return self.get_EffectiveField('MaxLength')

    def setMaxLength(self, a_value):
        self.set_RawField('MaxLength', a_value)

    def _getRaw_MaxLength(self):
        return self.get_RawField('MaxLength')

    def _isPresent_MaxLength(self):
        return self.isPresent_Field('MaxLength')

    def _unset_MaxLength(self):
        self.unset_Field('MaxLength')

    def getPattern(self):
        return self.get_EffectiveField('Pattern')

    def setPattern(self, a_value):
        self.set_RawField('Pattern', a_value)

    def _getRaw_Pattern(self):
        return self.get_RawField('Pattern')

    def _isPresent_Pattern(self):
        return self.isPresent_Field('Pattern')

    def _unset_Pattern(self):
        self.unset_Field('Pattern')

    def _setEmpty_Pattern(self):
        self.set_EmptyField('Pattern')

    def _isEmpty_Pattern(self):
        return self.isEmpty_Field('Pattern')

    def getMinimum(self):
        return self.get_EffectiveField('Minimum')

    def setMinimum(self, a_value):
        self.set_RawField('Minimum', a_value)

    def _getRaw_Minimum(self):
        return self.get_RawField('Minimum')

    def _isPresent_Minimum(self):
        return self.isPresent_Field('Minimum')

    def _unset_Minimum(self):
        self.unset_Field('Minimum')

    def _setEmpty_Minimum(self):
        self.set_EmptyField('Minimum')

    def _isEmpty_Minimum(self):
        return self.isEmpty_Field('Minimum')

    def getMaximum(self):
        return self.get_EffectiveField('Maximum')

    def setMaximum(self, a_value):
        self.set_RawField('Maximum', a_value)

    def _getRaw_Maximum(self):
        return self.get_RawField('Maximum')

    def _isPresent_Maximum(self):
        return self.isPresent_Field('Maximum')

    def _unset_Maximum(self):
        self.unset_Field('Maximum')

    def _setEmpty_Maximum(self):
        self.set_EmptyField('Maximum')

    def _isEmpty_Maximum(self):
        return self.isEmpty_Field('Maximum')

    def getExclusiveMinimum(self):
        return self.get_EffectiveField('ExclusiveMinimum')

    def setExclusiveMinimum(self, a_value):
        self.set_RawField('ExclusiveMinimum', a_value)

    def _getRaw_ExclusiveMinimum(self):
        return self.get_RawField('ExclusiveMinimum')

    def _isPresent_ExclusiveMinimum(self):
        return self.isPresent_Field('ExclusiveMinimum')

    def _unset_ExclusiveMinimum(self):
        self.unset_Field('ExclusiveMinimum')

    def getExclusiveMaximum(self):
        return self.get_EffectiveField('ExclusiveMaximum')

    def setExclusiveMaximum(self, a_value):
        self.set_RawField('ExclusiveMaximum', a_value)

    def _getRaw_ExclusiveMaximum(self):
        return self.get_RawField('ExclusiveMaximum')

    def _isPresent_ExclusiveMaximum(self):
        return self.isPresent_Field('ExclusiveMaximum')

    def _unset_ExclusiveMaximum(self):
        self.unset_Field('ExclusiveMaximum')

    def getMultipleOf(self):
        return self.get_EffectiveField('MultipleOf')

    def setMultipleOf(self, a_value):
        self.set_RawField('MultipleOf', a_value)

    def _getRaw_MultipleOf(self):
        return self.get_RawField('MultipleOf')

    def _isPresent_MultipleOf(self):
        return self.isPresent_Field('MultipleOf')

    def _unset_MultipleOf(self):
        self.unset_Field('MultipleOf')

    def _setEmpty_MultipleOf(self):
        self.set_EmptyField('MultipleOf')

    def _isEmpty_MultipleOf(self):
        return self.isEmpty_Field('MultipleOf')
