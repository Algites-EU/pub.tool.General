"""Generated SmartDataObject implementation for AIigType_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.tool.codegen.defs.model.aiig_type_content_1 import AIigTypeContent_1
    from eu.algites.tool.codegen.defs.model.impl.intf.aiigd_source_bindings_1 import AIigdSourceBindings_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.model.impl.intf.aiigd_type_1 import AIigdType_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.model.aiig_type_1 import AIigType_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigType_1,))
class AIcgdType_1(AIcSmartDataObject, AIigdType_1['AIigdSourceBindings_1']):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Type', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Type', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getIdentity(self):
        return self.get_EffectiveField('Identity')

    def setIdentity(self, a_value):
        self.set_RawField('Identity', a_value)

    def _getRaw_Identity(self):
        return self.get_RawField('Identity')

    def _isPresent_Identity(self):
        return self.isPresent_Field('Identity')

    def _unset_Identity(self):
        self.unset_Field('Identity')

    def _setEmpty_Identity(self):
        self.set_EmptyField('Identity')

    def _isEmpty_Identity(self):
        return self.isEmpty_Field('Identity')

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

    def getOrigin(self):
        return self.get_EffectiveField('Origin')

    def setOrigin(self, a_value):
        self.set_RawField('Origin', a_value)

    def _getRaw_Origin(self):
        return self.get_RawField('Origin')

    def _isPresent_Origin(self):
        return self.isPresent_Field('Origin')

    def _unset_Origin(self):
        self.unset_Field('Origin')

    def getSchemaVersion(self):
        return self.get_EffectiveField('SchemaVersion')

    def setSchemaVersion(self, a_value):
        self.set_RawField('SchemaVersion', a_value)

    def _getRaw_SchemaVersion(self):
        return self.get_RawField('SchemaVersion')

    def _isPresent_SchemaVersion(self):
        return self.isPresent_Field('SchemaVersion')

    def _unset_SchemaVersion(self):
        self.unset_Field('SchemaVersion')

    def _setEmpty_SchemaVersion(self):
        self.set_EmptyField('SchemaVersion')

    def _isEmpty_SchemaVersion(self):
        return self.isEmpty_Field('SchemaVersion')

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

    def getPathSegmentsList(self):
        return self.get_OrCreateCollectionField('PathSegmentsList', False)

    def _getRaw_PathSegmentsList(self):
        return self.get_RawField('PathSegmentsList')

    def _isPresent_PathSegmentsList(self):
        return self.isPresent_Field('PathSegmentsList')

    def _unset_PathSegmentsList(self):
        self.unset_Field('PathSegmentsList')

    def getInheritedFromTypesList(self):
        return self.get_OrCreateCollectionField('InheritedFromTypesList', False)

    def _getRaw_InheritedFromTypesList(self):
        return self.get_RawField('InheritedFromTypesList')

    def _isPresent_InheritedFromTypesList(self):
        return self.isPresent_Field('InheritedFromTypesList')

    def _unset_InheritedFromTypesList(self):
        self.unset_Field('InheritedFromTypesList')

    def getContent(self) -> AIigTypeContent_1:
        return self.get_EffectiveField('Content')

    def setContent(self, a_value: AIigTypeContent_1):
        self.set_RawField('Content', a_value)

    def _getRaw_Content(self) -> AIigTypeContent_1:
        return self.get_RawField('Content')

    def _isPresent_Content(self):
        return self.isPresent_Field('Content')

    def _unset_Content(self):
        self.unset_Field('Content')

    def getResolutionState(self):
        return self.get_EffectiveField('ResolutionState')

    def setResolutionState(self, a_value):
        self.set_RawField('ResolutionState', a_value)

    def _getRaw_ResolutionState(self):
        return self.get_RawField('ResolutionState')

    def _isPresent_ResolutionState(self):
        return self.isPresent_Field('ResolutionState')

    def _unset_ResolutionState(self):
        self.unset_Field('ResolutionState')

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
