"""Generated SmartDataObject implementation for AIigDefsCodegenNameConventionsType_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.naming.convention.impl.intf.aiigd_identifier_conventions_1 import AIigdIdentifierConventions_1
    from eu.algites.lib.naming.convention.impl.intf.aiigd_name_compositions_1 import AIigdNameCompositions_1
    from eu.algites.lib.naming.convention.impl.intf.aiigd_name_fragments_1 import AIigdNameFragments_1
    from eu.algites.lib.naming.convention.impl.intf.aiigd_version_conventions_1 import AIigdVersionConventions_1
    from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_name_conventions_type_property_defs_codegen_name_conventions_1 import AIigdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_name_conventions_type_1 import AIigdDefsCodegenNameConventionsType_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.naming.aiig_defs_codegen_name_conventions_type_1 import AIigDefsCodegenNameConventionsType_1
from eu.algites.lib.naming.convention.impl.aicgd_common_naming_conventions_1 import AIcgdCommonNamingConventions_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigDefsCodegenNameConventionsType_1,))
class AIcgdDefsCodegenNameConventionsType_1(AIcSmartDataObject, AIigdDefsCodegenNameConventionsType_1['AIigdIdentifierConventions_1', 'AIigdVersionConventions_1', 'AIigdNameFragments_1', 'AIigdNameCompositions_1', 'AIigdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1']):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""

    def getStandardConventionsFile(self):
        return self.get_EffectiveField('StandardConventionsFile')

    def setStandardConventionsFile(self, a_value):
        self.set_RawField('StandardConventionsFile', a_value)

    def _getRaw_StandardConventionsFile(self):
        return self.get_RawField('StandardConventionsFile')

    def _isPresent_StandardConventionsFile(self):
        return self.isPresent_Field('StandardConventionsFile')

    def _unset_StandardConventionsFile(self):
        self.unset_Field('StandardConventionsFile')

    def _setEmpty_StandardConventionsFile(self):
        self.set_EmptyField('StandardConventionsFile')

    def _isEmpty_StandardConventionsFile(self):
        return self.isEmpty_Field('StandardConventionsFile')

    def getIdentifierConventions(self) -> AIigdIdentifierConventions_1:
        return self.get_EffectiveField('IdentifierConventions')

    def setIdentifierConventions(self, a_value: AIigdIdentifierConventions_1):
        self.set_RawField('IdentifierConventions', a_value)

    def _getRaw_IdentifierConventions(self) -> AIigdIdentifierConventions_1:
        return self.get_RawField('IdentifierConventions')

    def _isPresent_IdentifierConventions(self):
        return self.isPresent_Field('IdentifierConventions')

    def _unset_IdentifierConventions(self):
        self.unset_Field('IdentifierConventions')

    def getVersionConventions(self) -> AIigdVersionConventions_1:
        return self.get_EffectiveField('VersionConventions')

    def setVersionConventions(self, a_value: AIigdVersionConventions_1):
        self.set_RawField('VersionConventions', a_value)

    def _getRaw_VersionConventions(self) -> AIigdVersionConventions_1:
        return self.get_RawField('VersionConventions')

    def _isPresent_VersionConventions(self):
        return self.isPresent_Field('VersionConventions')

    def _unset_VersionConventions(self):
        self.unset_Field('VersionConventions')

    def getNameFragments(self) -> AIigdNameFragments_1:
        return self.get_EffectiveField('NameFragments')

    def setNameFragments(self, a_value: AIigdNameFragments_1):
        self.set_RawField('NameFragments', a_value)

    def _getRaw_NameFragments(self) -> AIigdNameFragments_1:
        return self.get_RawField('NameFragments')

    def _isPresent_NameFragments(self):
        return self.isPresent_Field('NameFragments')

    def _unset_NameFragments(self):
        self.unset_Field('NameFragments')

    def getNameCompositions(self) -> AIigdNameCompositions_1:
        return self.get_EffectiveField('NameCompositions')

    def setNameCompositions(self, a_value: AIigdNameCompositions_1):
        self.set_RawField('NameCompositions', a_value)

    def _getRaw_NameCompositions(self) -> AIigdNameCompositions_1:
        return self.get_RawField('NameCompositions')

    def _isPresent_NameCompositions(self):
        return self.isPresent_Field('NameCompositions')

    def _unset_NameCompositions(self):
        self.unset_Field('NameCompositions')

    def getDefsCodegenNameConventions(self) -> AIigdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1:
        return self.get_EffectiveField('DefsCodegenNameConventions')

    def setDefsCodegenNameConventions(self, a_value: AIigdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1):
        self.set_RawField('DefsCodegenNameConventions', a_value)

    def _getRaw_DefsCodegenNameConventions(self) -> AIigdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1:
        return self.get_RawField('DefsCodegenNameConventions')

    def _isPresent_DefsCodegenNameConventions(self):
        return self.isPresent_Field('DefsCodegenNameConventions')

    def _unset_DefsCodegenNameConventions(self):
        self.unset_Field('DefsCodegenNameConventions')
