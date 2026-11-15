"""Generated SmartDataObject implementation for AIigSourceBinding_1."""
from __future__ import annotations
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.model.impl.intf.aiigd_source_binding_1 import AIigdSourceBinding_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.model.aiig_source_binding_1 import AIigSourceBinding_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigSourceBinding_1,))
class AIcgdSourceBinding_1(AIcSmartDataObject, AIigdSourceBinding_1):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBinding', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBinding', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getSourceResource(self):
        return self.get_EffectiveField('SourceResource')

    def setSourceResource(self, a_value):
        self.set_RawField('SourceResource', a_value)

    def _getRaw_SourceResource(self):
        return self.get_RawField('SourceResource')

    def _isPresent_SourceResource(self):
        return self.isPresent_Field('SourceResource')

    def _unset_SourceResource(self):
        self.unset_Field('SourceResource')

    def _setEmpty_SourceResource(self):
        self.set_EmptyField('SourceResource')

    def _isEmpty_SourceResource(self):
        return self.isEmpty_Field('SourceResource')

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

    def getRepresentationKind(self):
        return self.get_EffectiveField('RepresentationKind')

    def setRepresentationKind(self, a_value):
        self.set_RawField('RepresentationKind', a_value)

    def _getRaw_RepresentationKind(self):
        return self.get_RawField('RepresentationKind')

    def _isPresent_RepresentationKind(self):
        return self.isPresent_Field('RepresentationKind')

    def _unset_RepresentationKind(self):
        self.unset_Field('RepresentationKind')

    def _setEmpty_RepresentationKind(self):
        self.set_EmptyField('RepresentationKind')

    def _isEmpty_RepresentationKind(self):
        return self.isEmpty_Field('RepresentationKind')
