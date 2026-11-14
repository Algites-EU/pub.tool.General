"""Generated SmartDataObject implementation for AIigMap_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.tool.codegen.defs.bootstrap.model.aiig_structure_1 import AIigStructure_1
    from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_source_bindings_1 import AIigdSourceBindings_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_yaml_data_object import AIaYamlDataObject
from eu.algites.lib.data.dataobject.jsondefs.aia_json_data_object import AIaJsonDataObject
from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_map_1 import AIigdMap_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_map_1 import AIigMap_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigMap_1,))
class AIcgdMap_1(AIcSmartDataObject, AIigdMap_1['AIigdSourceBindings_1']):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Map', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Map', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Map', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

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

    def getMapKind(self):
        return self.get_EffectiveField('MapKind')

    def setMapKind(self, a_value):
        self.set_RawField('MapKind', a_value)

    def _getRaw_MapKind(self):
        return self.get_RawField('MapKind')

    def _isPresent_MapKind(self):
        return self.isPresent_Field('MapKind')

    def _unset_MapKind(self):
        self.unset_Field('MapKind')

    def getKeyType(self) -> AIigStructure_1:
        return self.get_EffectiveField('KeyType')

    def setKeyType(self, a_value: AIigStructure_1):
        self.set_RawField('KeyType', a_value)

    def _getRaw_KeyType(self) -> AIigStructure_1:
        return self.get_RawField('KeyType')

    def _isPresent_KeyType(self):
        return self.isPresent_Field('KeyType')

    def _unset_KeyType(self):
        self.unset_Field('KeyType')

    def getValueType(self) -> AIigStructure_1:
        return self.get_EffectiveField('ValueType')

    def setValueType(self, a_value: AIigStructure_1):
        self.set_RawField('ValueType', a_value)

    def _getRaw_ValueType(self) -> AIigStructure_1:
        return self.get_RawField('ValueType')

    def _isPresent_ValueType(self):
        return self.isPresent_Field('ValueType')

    def _unset_ValueType(self):
        self.unset_Field('ValueType')

    def getSourceBindings(self) -> AIigdSourceBindings_1:
        return self.get_EffectiveField('SourceBindings')

    def setSourceBindings(self, a_value: AIigdSourceBindings_1):
        self.set_RawField('SourceBindings', a_value)

    def _getRaw_SourceBindings(self) -> AIigdSourceBindings_1:
        return self.get_RawField('SourceBindings')

    def _isPresent_SourceBindings(self):
        return self.isPresent_Field('SourceBindings')

    def _unset_SourceBindings(self):
        self.unset_Field('SourceBindings')
