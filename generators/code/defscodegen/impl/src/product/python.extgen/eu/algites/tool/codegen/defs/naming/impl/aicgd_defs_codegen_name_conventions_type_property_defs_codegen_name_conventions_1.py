"""Generated SmartDataObject implementation for AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_name_conventions_type_property_name_conventions_1 import AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_name_conventions_type_property_defs_codegen_name_conventions_1 import AIigdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.naming.aiig_defs_codegen_name_conventions_type_property_defs_codegen_name_conventions_1 import AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1,))
class AIcgdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1(AIcSmartDataObject, AIigdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1['AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1']):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""

    def getNameConventions(self) -> AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1:
        return self.get_EffectiveField('NameConventions')

    def setNameConventions(self, a_value: AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1):
        self.set_RawField('NameConventions', a_value)

    def _getRaw_NameConventions(self) -> AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1:
        return self.get_RawField('NameConventions')

    def _isPresent_NameConventions(self):
        return self.isPresent_Field('NameConventions')

    def _unset_NameConventions(self):
        self.unset_Field('NameConventions')
