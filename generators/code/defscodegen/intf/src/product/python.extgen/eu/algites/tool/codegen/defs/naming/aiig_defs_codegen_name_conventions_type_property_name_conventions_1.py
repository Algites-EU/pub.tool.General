from __future__ import annotations
from typing import Any

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.lib.data.dataobject.aia_data_object_field_default import AIaDataObjectFieldDefault
from eu.algites.lib.data.dataobject.ain_data_object_field_default_kind import AInDataObjectFieldDefaultKind
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind

if TYPE_CHECKING:
    from .aiig_defs_codegen_name_convention_1 import AIigDefsCodegenNameConvention_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
class AIigDefsCodegenNameConventionsTypePropertyNameConventions_1(AIiDataObject):
    """Contract for DefsCodegenNameConventionsTypePropertyNameConventions."""

    __data_object__ = AIcdDataObject(description='DefsCodegenNameConventionsTypePropertyNameConventions')

    __xml_schema_fields__ = {
        'NameConventionList': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='NameConvention', value_kind=AInXmlValueKind.ELEMENT),
    }

    __xml_repeated_fields__ = ('NameConventionList',)

    class CONSTDefsCodegenNameConventionsTypePropertyNameConventions:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__NAME_CONVENTION = 'NameConvention'

    @AIaDataObjectField(dataFieldName='NameConvention', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=AIiMultiMappedList, order=0, min_item_count=0, max_item_count=-1, is_empty_allowed=False)
    @abstractmethod
    def getNameConventionList(self) -> AIiMultiMappedList[AIigDefsCodegenNameConvention_1]:
        """Return Canonical field NameConvention. (optional, cardinality 0..-1)."""
        raise NotImplementedError

