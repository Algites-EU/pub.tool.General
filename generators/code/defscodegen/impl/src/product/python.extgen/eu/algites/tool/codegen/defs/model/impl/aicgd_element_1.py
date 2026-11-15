"""Generated SmartDataObject implementation for AIigElement_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.common.list.aii_bounded_list import AIiBoundedList
    from eu.algites.tool.codegen.defs.model.aiig_structure_1 import AIigStructure_1
    from eu.algites.tool.codegen.defs.model.impl.intf.aiigd_key_definition_1 import AIigdKeyDefinition_1
    from eu.algites.tool.codegen.defs.model.impl.intf.aiigd_source_bindings_1 import AIigdSourceBindings_1
    from eu.algites.tool.codegen.defs.model.impl.intf.aiigd_xml_wire_name_1 import AIigdXmlWireName_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.model.impl.intf.aiigd_element_1 import AIigdElement_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.model.aiig_element_1 import AIigElement_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigElement_1,))
class AIcgdElement_1(AIcSmartDataObject, AIigdElement_1['AIigdXmlWireName_1', 'AIigdKeyDefinition_1', 'AIigdSourceBindings_1']):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Element', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Element', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getElementKind(self):
        return self.get_EffectiveField('ElementKind')

    def setElementKind(self, a_value):
        self.set_RawField('ElementKind', a_value)

    def _getRaw_ElementKind(self):
        return self.get_RawField('ElementKind')

    def _isPresent_ElementKind(self):
        return self.isPresent_Field('ElementKind')

    def _unset_ElementKind(self):
        self.unset_Field('ElementKind')

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

    def getStructure(self) -> AIigStructure_1:
        return self.get_EffectiveField('Structure')

    def setStructure(self, a_value: AIigStructure_1):
        self.set_RawField('Structure', a_value)

    def _getRaw_Structure(self) -> AIigStructure_1:
        return self.get_RawField('Structure')

    def _isPresent_Structure(self):
        return self.isPresent_Field('Structure')

    def _unset_Structure(self):
        self.unset_Field('Structure')

    def getDescription(self):
        return self.get_EffectiveField('Description')

    def setDescription(self, a_value):
        self.set_RawField('Description', a_value)

    def _getRaw_Description(self):
        return self.get_RawField('Description')

    def _isPresent_Description(self):
        return self.isPresent_Field('Description')

    def _unset_Description(self):
        self.unset_Field('Description')

    def _setEmpty_Description(self):
        self.set_EmptyField('Description')

    def _isEmpty_Description(self):
        return self.isEmpty_Field('Description')

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

    def getKeyDefinitionsList(self) -> AIiBoundedList[AIigdKeyDefinition_1]:
        return self.get_OrCreateCollectionField('KeyDefinitionsList', False)

    def _getRaw_KeyDefinitionsList(self) -> AIiBoundedList[AIigdKeyDefinition_1]:
        return self.get_RawField('KeyDefinitionsList')

    def _isPresent_KeyDefinitionsList(self):
        return self.isPresent_Field('KeyDefinitionsList')

    def _unset_KeyDefinitionsList(self):
        self.unset_Field('KeyDefinitionsList')

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

    def getDefaultKind(self):
        return self.get_EffectiveField('DefaultKind')

    def setDefaultKind(self, a_value):
        self.set_RawField('DefaultKind', a_value)

    def _getRaw_DefaultKind(self):
        return self.get_RawField('DefaultKind')

    def _isPresent_DefaultKind(self):
        return self.isPresent_Field('DefaultKind')

    def _unset_DefaultKind(self):
        self.unset_Field('DefaultKind')

    def _setEmpty_DefaultKind(self):
        self.set_EmptyField('DefaultKind')

    def _isEmpty_DefaultKind(self):
        return self.isEmpty_Field('DefaultKind')

    def getDefaultValue(self):
        return self.get_EffectiveField('DefaultValue')

    def setDefaultValue(self, a_value):
        self.set_RawField('DefaultValue', a_value)

    def _getRaw_DefaultValue(self):
        return self.get_RawField('DefaultValue')

    def _isPresent_DefaultValue(self):
        return self.isPresent_Field('DefaultValue')

    def _unset_DefaultValue(self):
        self.unset_Field('DefaultValue')

    def _setEmpty_DefaultValue(self):
        self.set_EmptyField('DefaultValue')

    def _isEmpty_DefaultValue(self):
        return self.isEmpty_Field('DefaultValue')

    def getIsEmptyAllowed(self):
        return self.get_EffectiveField('IsEmptyAllowed')

    def setIsEmptyAllowed(self, a_value):
        self.set_RawField('IsEmptyAllowed', a_value)

    def _getRaw_IsEmptyAllowed(self):
        return self.get_RawField('IsEmptyAllowed')

    def _isPresent_IsEmptyAllowed(self):
        return self.isPresent_Field('IsEmptyAllowed')

    def _unset_IsEmptyAllowed(self):
        self.unset_Field('IsEmptyAllowed')
