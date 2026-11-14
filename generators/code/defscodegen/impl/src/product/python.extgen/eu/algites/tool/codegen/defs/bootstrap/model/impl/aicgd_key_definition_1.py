"""Generated SmartDataObject implementation for AIigKeyDefinition_1."""
from __future__ import annotations
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_yaml_data_object import AIaYamlDataObject
from eu.algites.lib.data.dataobject.jsondefs.aia_json_data_object import AIaJsonDataObject
from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_key_definition_1 import AIigdKeyDefinition_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_key_definition_1 import AIigKeyDefinition_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigKeyDefinition_1,))
class AIcgdKeyDefinition_1(AIcSmartDataObject, AIigdKeyDefinition_1):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/KeyDefinition', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/KeyDefinition', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/KeyDefinition', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getIdentifier(self):
        return self.get_EffectiveField('Identifier')

    def setIdentifier(self, a_value):
        self.set_RawField('Identifier', a_value)

    def _getRaw_Identifier(self):
        return self.get_RawField('Identifier')

    def _isPresent_Identifier(self):
        return self.isPresent_Field('Identifier')

    def _unset_Identifier(self):
        self.unset_Field('Identifier')

    def _setEmpty_Identifier(self):
        self.set_EmptyField('Identifier')

    def _isEmpty_Identifier(self):
        return self.isEmpty_Field('Identifier')

    def getSelector(self):
        return self.get_EffectiveField('Selector')

    def setSelector(self, a_value):
        self.set_RawField('Selector', a_value)

    def _getRaw_Selector(self):
        return self.get_RawField('Selector')

    def _isPresent_Selector(self):
        return self.isPresent_Field('Selector')

    def _unset_Selector(self):
        self.unset_Field('Selector')

    def _setEmpty_Selector(self):
        self.set_EmptyField('Selector')

    def _isEmpty_Selector(self):
        return self.isEmpty_Field('Selector')

    def getSourcePointer(self):
        return self.get_EffectiveField('SourcePointer')

    def setSourcePointer(self, a_value):
        self.set_RawField('SourcePointer', a_value)

    def _getRaw_SourcePointer(self):
        return self.get_RawField('SourcePointer')

    def _isPresent_SourcePointer(self):
        return self.isPresent_Field('SourcePointer')

    def _unset_SourcePointer(self):
        self.unset_Field('SourcePointer')

    def _setEmpty_SourcePointer(self):
        self.set_EmptyField('SourcePointer')

    def _isEmpty_SourcePointer(self):
        return self.isEmpty_Field('SourcePointer')

    def getFieldsList(self):
        return self.get_OrCreateCollectionField('FieldsList', False)

    def _getRaw_FieldsList(self):
        return self.get_RawField('FieldsList')

    def _isPresent_FieldsList(self):
        return self.isPresent_Field('FieldsList')

    def _unset_FieldsList(self):
        self.unset_Field('FieldsList')

    def getRequired(self):
        return self.get_EffectiveField('Required')

    def setRequired(self, a_value):
        self.set_RawField('Required', a_value)

    def _getRaw_Required(self):
        return self.get_RawField('Required')

    def _isPresent_Required(self):
        return self.isPresent_Field('Required')

    def _unset_Required(self):
        self.unset_Field('Required')
