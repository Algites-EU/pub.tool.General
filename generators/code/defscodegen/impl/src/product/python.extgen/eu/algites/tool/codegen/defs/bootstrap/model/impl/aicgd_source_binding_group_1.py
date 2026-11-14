"""Generated SmartDataObject implementation for AIigSourceBindingGroup_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.common.list.aii_bounded_list import AIiBoundedList
    from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_source_binding_1 import AIigdSourceBinding_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_yaml_data_object import AIaYamlDataObject
from eu.algites.lib.data.dataobject.jsondefs.aia_json_data_object import AIaJsonDataObject
from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_source_binding_group_1 import AIigdSourceBindingGroup_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_source_binding_group_1 import AIigSourceBindingGroup_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigSourceBindingGroup_1,))
class AIcgdSourceBindingGroup_1(AIcSmartDataObject, AIigdSourceBindingGroup_1['AIigdSourceBinding_1']):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBindingGroup', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBindingGroup', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBindingGroup', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getInputKind(self):
        return self.get_EffectiveField('InputKind')

    def setInputKind(self, a_value):
        self.set_RawField('InputKind', a_value)

    def _getRaw_InputKind(self):
        return self.get_RawField('InputKind')

    def _isPresent_InputKind(self):
        return self.isPresent_Field('InputKind')

    def _unset_InputKind(self):
        self.unset_Field('InputKind')

    def getBindingList(self) -> AIiBoundedList[AIigdSourceBinding_1]:
        return self.get_OrCreateCollectionField('BindingList', False)

    def _getRaw_BindingList(self) -> AIiBoundedList[AIigdSourceBinding_1]:
        return self.get_RawField('BindingList')

    def _isPresent_BindingList(self):
        return self.isPresent_Field('BindingList')

    def _unset_BindingList(self):
        self.unset_Field('BindingList')
