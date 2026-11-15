"""Generated SmartDataObject implementation for AIigSourceBindings_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.common.list.aii_bounded_list import AIiBoundedList
    from eu.algites.tool.codegen.defs.model.impl.intf.aiigd_source_binding_group_1 import AIigdSourceBindingGroup_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.model.impl.intf.aiigd_source_bindings_1 import AIigdSourceBindings_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.model.aiig_source_bindings_1 import AIigSourceBindings_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigSourceBindings_1,))
class AIcgdSourceBindings_1(AIcSmartDataObject, AIigdSourceBindings_1['AIigdSourceBindingGroup_1']):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBindings', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceBindings', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getSourceBindingGroupList(self) -> AIiBoundedList[AIigdSourceBindingGroup_1]:
        return self.get_OrCreateCollectionField('SourceBindingGroupList', False)

    def _getRaw_SourceBindingGroupList(self) -> AIiBoundedList[AIigdSourceBindingGroup_1]:
        return self.get_RawField('SourceBindingGroupList')

    def _isPresent_SourceBindingGroupList(self):
        return self.isPresent_Field('SourceBindingGroupList')

    def _unset_SourceBindingGroupList(self):
        self.unset_Field('SourceBindingGroupList')
