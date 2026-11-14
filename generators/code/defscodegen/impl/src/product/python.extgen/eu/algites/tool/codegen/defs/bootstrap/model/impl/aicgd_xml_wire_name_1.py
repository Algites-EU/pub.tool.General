"""Generated SmartDataObject implementation for AIigXmlWireName_1."""
from __future__ import annotations
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_yaml_data_object import AIaYamlDataObject
from eu.algites.lib.data.dataobject.jsondefs.aia_json_data_object import AIaJsonDataObject
from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_xml_wire_name_1 import AIigdXmlWireName_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_xml_wire_name_1 import AIigXmlWireName_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigXmlWireName_1,))
class AIcgdXmlWireName_1(AIcSmartDataObject, AIigdXmlWireName_1):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/XmlWireName', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/XmlWireName', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/XmlWireName', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getNamespaceUri(self):
        return self.get_EffectiveField('NamespaceUri')

    def setNamespaceUri(self, a_value):
        self.set_RawField('NamespaceUri', a_value)

    def _getRaw_NamespaceUri(self):
        return self.get_RawField('NamespaceUri')

    def _isPresent_NamespaceUri(self):
        return self.isPresent_Field('NamespaceUri')

    def _unset_NamespaceUri(self):
        self.unset_Field('NamespaceUri')

    def _setEmpty_NamespaceUri(self):
        self.set_EmptyField('NamespaceUri')

    def _isEmpty_NamespaceUri(self):
        return self.isEmpty_Field('NamespaceUri')

    def getLocalName(self):
        return self.get_EffectiveField('LocalName')

    def setLocalName(self, a_value):
        self.set_RawField('LocalName', a_value)

    def _getRaw_LocalName(self):
        return self.get_RawField('LocalName')

    def _isPresent_LocalName(self):
        return self.isPresent_Field('LocalName')

    def _unset_LocalName(self):
        self.unset_Field('LocalName')

    def _setEmpty_LocalName(self):
        self.set_EmptyField('LocalName')

    def _isEmpty_LocalName(self):
        return self.isEmpty_Field('LocalName')

    def getValueKind(self):
        return self.get_EffectiveField('ValueKind')

    def setValueKind(self, a_value):
        self.set_RawField('ValueKind', a_value)

    def _getRaw_ValueKind(self):
        return self.get_RawField('ValueKind')

    def _isPresent_ValueKind(self):
        return self.isPresent_Field('ValueKind')

    def _unset_ValueKind(self):
        self.unset_Field('ValueKind')
