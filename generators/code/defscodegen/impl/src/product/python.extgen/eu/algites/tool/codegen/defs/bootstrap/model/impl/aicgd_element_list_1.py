"""Generated SmartDataObject implementation for AIigElementList_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.tool.codegen.defs.bootstrap.model.aiig_element_list_child_1 import AIigElementListChild_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_yaml_data_object import AIaYamlDataObject
from eu.algites.lib.data.dataobject.jsondefs.aia_json_data_object import AIaJsonDataObject
from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_element_list_1 import AIigdElementList_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_element_list_1 import AIigElementList_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigElementList_1,))
class AIcgdElementList_1(AIcSmartDataObject, AIigdElementList_1):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ElementList', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ElementList', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ElementList', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getComposition(self):
        return self.get_EffectiveField('Composition')

    def setComposition(self, a_value):
        self.set_RawField('Composition', a_value)

    def _getRaw_Composition(self):
        return self.get_RawField('Composition')

    def _isPresent_Composition(self):
        return self.isPresent_Field('Composition')

    def _unset_Composition(self):
        self.unset_Field('Composition')

    def getChildrenList(self) -> list[AIigElementListChild_1]:
        return self.get_OrCreateCollectionField('ChildrenList', False)

    def _getRaw_ChildrenList(self) -> list[AIigElementListChild_1]:
        return self.get_RawField('ChildrenList')

    def _isPresent_ChildrenList(self):
        return self.isPresent_Field('ChildrenList')

    def _unset_ChildrenList(self):
        self.unset_Field('ChildrenList')

    def getMinItemCount(self):
        return self.get_EffectiveField('MinItemCount')

    def setMinItemCount(self, a_value):
        self.set_RawField('MinItemCount', a_value)

    def _getRaw_MinItemCount(self):
        return self.get_RawField('MinItemCount')

    def _isPresent_MinItemCount(self):
        return self.isPresent_Field('MinItemCount')

    def _unset_MinItemCount(self):
        self.unset_Field('MinItemCount')

    def getMaxItemCount(self):
        return self.get_EffectiveField('MaxItemCount')

    def setMaxItemCount(self, a_value):
        self.set_RawField('MaxItemCount', a_value)

    def _getRaw_MaxItemCount(self):
        return self.get_RawField('MaxItemCount')

    def _isPresent_MaxItemCount(self):
        return self.isPresent_Field('MaxItemCount')

    def _unset_MaxItemCount(self):
        self.unset_Field('MaxItemCount')

    def getMinProperties(self):
        return self.get_EffectiveField('MinProperties')

    def setMinProperties(self, a_value):
        self.set_RawField('MinProperties', a_value)

    def _getRaw_MinProperties(self):
        return self.get_RawField('MinProperties')

    def _isPresent_MinProperties(self):
        return self.isPresent_Field('MinProperties')

    def _unset_MinProperties(self):
        self.unset_Field('MinProperties')

    def getMaxProperties(self):
        return self.get_EffectiveField('MaxProperties')

    def setMaxProperties(self, a_value):
        self.set_RawField('MaxProperties', a_value)

    def _getRaw_MaxProperties(self):
        return self.get_RawField('MaxProperties')

    def _isPresent_MaxProperties(self):
        return self.isPresent_Field('MaxProperties')

    def _unset_MaxProperties(self):
        self.unset_Field('MaxProperties')
