"""Generated SmartDataObject implementation for AIigInputProfileType_1."""
from __future__ import annotations
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.impl.intf.aiigd_input_profile_type_1 import AIigdInputProfileType_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.aiig_input_profile_type_1 import AIigInputProfileType_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigInputProfileType_1,))
class AIcgdInputProfileType_1(AIcSmartDataObject, AIigdInputProfileType_1):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.input-profile#/$defs/InputProfileType', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.input-profile#/$defs/InputProfileType', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getSourceKind(self):
        return self.get_EffectiveField('SourceKind')

    def setSourceKind(self, a_value):
        self.set_RawField('SourceKind', a_value)

    def _getRaw_SourceKind(self):
        return self.get_RawField('SourceKind')

    def _isPresent_SourceKind(self):
        return self.isPresent_Field('SourceKind')

    def _unset_SourceKind(self):
        self.unset_Field('SourceKind')

    def getNamingProfile(self):
        return self.get_EffectiveField('NamingProfile')

    def setNamingProfile(self, a_value):
        self.set_RawField('NamingProfile', a_value)

    def _getRaw_NamingProfile(self):
        return self.get_RawField('NamingProfile')

    def _isPresent_NamingProfile(self):
        return self.isPresent_Field('NamingProfile')

    def _unset_NamingProfile(self):
        self.unset_Field('NamingProfile')

    def _setEmpty_NamingProfile(self):
        self.set_EmptyField('NamingProfile')

    def _isEmpty_NamingProfile(self):
        return self.isEmpty_Field('NamingProfile')

    def getRequireCanonicalIdentity(self):
        return self.get_EffectiveField('RequireCanonicalIdentity')

    def setRequireCanonicalIdentity(self, a_value):
        self.set_RawField('RequireCanonicalIdentity', a_value)

    def _getRaw_RequireCanonicalIdentity(self):
        return self.get_RawField('RequireCanonicalIdentity')

    def _isPresent_RequireCanonicalIdentity(self):
        return self.isPresent_Field('RequireCanonicalIdentity')

    def _unset_RequireCanonicalIdentity(self):
        self.unset_Field('RequireCanonicalIdentity')

    def getRequireDefinitionVersion(self):
        return self.get_EffectiveField('RequireDefinitionVersion')

    def setRequireDefinitionVersion(self, a_value):
        self.set_RawField('RequireDefinitionVersion', a_value)

    def _getRaw_RequireDefinitionVersion(self):
        return self.get_RawField('RequireDefinitionVersion')

    def _isPresent_RequireDefinitionVersion(self):
        return self.isPresent_Field('RequireDefinitionVersion')

    def _unset_RequireDefinitionVersion(self):
        self.unset_Field('RequireDefinitionVersion')
