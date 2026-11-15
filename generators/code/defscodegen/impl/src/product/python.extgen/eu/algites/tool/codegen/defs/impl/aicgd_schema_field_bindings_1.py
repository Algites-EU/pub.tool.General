"""Generated SmartDataObject implementation for AIigSchemaFieldBindings_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.common.list.aii_bounded_list import AIiBoundedList
    from eu.algites.tool.codegen.defs.impl.intf.aiigd_field_binding_type_1 import AIigdFieldBindingType_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.impl.intf.aiigd_schema_field_bindings_1 import AIigdSchemaFieldBindings_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.aiig_schema_field_bindings_1 import AIigSchemaFieldBindings_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigSchemaFieldBindings_1,))
class AIcgdSchemaFieldBindings_1(AIcSmartDataObject, AIigdSchemaFieldBindings_1['AIigdFieldBindingType_1']):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.schema-field-bindings', schema_version=1, schema_url='https://defs.dev.algites.eu/api/jsondefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.jsondef.schema.json', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.schema-field-bindings', schema_version=1, schema_url='https://defs.dev.algites.eu/api/yamldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.yamldef.schema.json', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getArtifact(self):
        return self.get_EffectiveField('Artifact')

    def setArtifact(self, a_value):
        self.set_RawField('Artifact', a_value)

    def _getRaw_Artifact(self):
        return self.get_RawField('Artifact')

    def _isPresent_Artifact(self):
        return self.isPresent_Field('Artifact')

    def _unset_Artifact(self):
        self.unset_Field('Artifact')

    def getImplementationArtifact(self):
        return self.get_EffectiveField('ImplementationArtifact')

    def setImplementationArtifact(self, a_value):
        self.set_RawField('ImplementationArtifact', a_value)

    def _getRaw_ImplementationArtifact(self):
        return self.get_RawField('ImplementationArtifact')

    def _isPresent_ImplementationArtifact(self):
        return self.isPresent_Field('ImplementationArtifact')

    def _unset_ImplementationArtifact(self):
        self.unset_Field('ImplementationArtifact')

    def getLanguagesList(self):
        return self.get_OrCreateCollectionField('LanguagesList', False)

    def _getRaw_LanguagesList(self):
        return self.get_RawField('LanguagesList')

    def _isPresent_LanguagesList(self):
        return self.isPresent_Field('LanguagesList')

    def _unset_LanguagesList(self):
        self.unset_Field('LanguagesList')

    def getBindingsList(self) -> AIiBoundedList[AIigdFieldBindingType_1]:
        return self.get_OrCreateCollectionField('BindingsList', False)

    def _getRaw_BindingsList(self) -> AIiBoundedList[AIigdFieldBindingType_1]:
        return self.get_RawField('BindingsList')

    def _isPresent_BindingsList(self):
        return self.isPresent_Field('BindingsList')

    def _unset_BindingsList(self):
        self.unset_Field('BindingsList')
