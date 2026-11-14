"""Generated SmartDataObject implementation for AIigList_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.tool.codegen.defs.bootstrap.model.aiig_structure_1 import AIigStructure_1
    from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_key_definition_1 import AIigdKeyDefinition_1
    from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_xml_wire_name_1 import AIigdXmlWireName_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_yaml_data_object import AIaYamlDataObject
from eu.algites.lib.data.dataobject.jsondefs.aia_json_data_object import AIaJsonDataObject
from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_list_1 import AIigdList_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_list_1 import AIigList_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigList_1,))
class AIcgdList_1(AIcSmartDataObject, AIigdList_1['AIigdXmlWireName_1', 'AIigdKeyDefinition_1']):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/List', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/List', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/List', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

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

    def getItem(self) -> AIigStructure_1:
        return self.get_EffectiveField('Item')

    def setItem(self, a_value: AIigStructure_1):
        self.set_RawField('Item', a_value)

    def _getRaw_Item(self) -> AIigStructure_1:
        return self.get_RawField('Item')

    def _isPresent_Item(self):
        return self.isPresent_Field('Item')

    def _unset_Item(self):
        self.unset_Field('Item')

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

    def getXmlWire(self) -> AIigdXmlWireName_1:
        return self.get_EffectiveField('XmlWire')

    def setXmlWire(self, a_value: AIigdXmlWireName_1):
        self.set_RawField('XmlWire', a_value)

    def _getRaw_XmlWire(self) -> AIigdXmlWireName_1:
        return self.get_RawField('XmlWire')

    def _isPresent_XmlWire(self):
        return self.isPresent_Field('XmlWire')

    def _unset_XmlWire(self):
        self.unset_Field('XmlWire')

    def getKeyDefinitionsList(self) -> list[AIigdKeyDefinition_1]:
        return self.get_OrCreateCollectionField('KeyDefinitionsList', False)

    def _getRaw_KeyDefinitionsList(self) -> list[AIigdKeyDefinition_1]:
        return self.get_RawField('KeyDefinitionsList')

    def _isPresent_KeyDefinitionsList(self):
        return self.isPresent_Field('KeyDefinitionsList')

    def _unset_KeyDefinitionsList(self):
        self.unset_Field('KeyDefinitionsList')

    def getUniqueItems(self):
        return self.get_EffectiveField('UniqueItems')

    def setUniqueItems(self, a_value):
        self.set_RawField('UniqueItems', a_value)

    def _getRaw_UniqueItems(self):
        return self.get_RawField('UniqueItems')

    def _isPresent_UniqueItems(self):
        return self.isPresent_Field('UniqueItems')

    def _unset_UniqueItems(self):
        self.unset_Field('UniqueItems')
