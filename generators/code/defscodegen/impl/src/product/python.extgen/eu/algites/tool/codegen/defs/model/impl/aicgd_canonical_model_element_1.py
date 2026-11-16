"""Generated SmartDataObject implementation for AIigCanonicalModelElement_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.common.list.aii_bounded_list import AIiBoundedList
    from eu.algites.tool.codegen.defs.model.impl.intf.aiigd_type_1 import AIigdType_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.tool.codegen.defs.model.impl.intf.aiigd_canonical_model_element_1 import AIigdCanonicalModelElement_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.model.aiig_canonical_model_element_1 import AIigCanonicalModelElement_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigCanonicalModelElement_1,))
class AIcgdCanonicalModelElement_1(AIcSmartDataObject, AIigdCanonicalModelElement_1['AIigdType_1']):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""

    def getTypesList(self) -> AIiBoundedList[AIigdType_1]:
        return self.get_OrCreateCollectionField('TypesList', False)

    def _getRaw_TypesList(self) -> AIiBoundedList[AIigdType_1]:
        return self.get_RawField('TypesList')

    def _isPresent_TypesList(self):
        return self.isPresent_Field('TypesList')

    def _unset_TypesList(self):
        self.unset_Field('TypesList')
