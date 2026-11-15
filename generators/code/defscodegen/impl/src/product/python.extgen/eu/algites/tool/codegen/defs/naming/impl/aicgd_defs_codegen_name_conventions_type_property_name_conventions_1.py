"""Generated SmartDataObject implementation for AIigDefsCodegenNameConventionsTypePropertyNameConventions_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList
    from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_name_convention_1 import AIigdDefsCodegenNameConvention_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_name_conventions_type_property_name_conventions_1 import AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.naming.aiig_defs_codegen_name_conventions_type_property_name_conventions_1 import AIigDefsCodegenNameConventionsTypePropertyNameConventions_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigDefsCodegenNameConventionsTypePropertyNameConventions_1,))
class AIcgdDefsCodegenNameConventionsTypePropertyNameConventions_1(AIcSmartDataObject, AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1['AIigdDefsCodegenNameConvention_1']):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""

    def getNameConventionList(self) -> AIiMultiMappedList[AIigdDefsCodegenNameConvention_1]:
        return self.get_OrCreateCollectionField('NameConventionList', True)

    def _getRaw_NameConventionList(self) -> AIiMultiMappedList[AIigdDefsCodegenNameConvention_1]:
        return self.get_RawField('NameConventionList')

    def _isPresent_NameConventionList(self):
        return self.isPresent_Field('NameConventionList')

    def _unset_NameConventionList(self):
        self.unset_Field('NameConventionList')
