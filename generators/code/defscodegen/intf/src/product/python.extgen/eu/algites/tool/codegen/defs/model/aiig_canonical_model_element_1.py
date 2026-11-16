from __future__ import annotations
from typing import Any

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.lib.data.dataobject.aia_data_object_field_default import AIaDataObjectFieldDefault
from eu.algites.lib.data.dataobject.ain_data_object_field_default_kind import AInDataObjectFieldDefaultKind
from eu.algites.lib.data.dataobject.aii_field_default_scalar_value_factory import AIiFieldDefaultScalarValueFactory
from eu.algites.lib.factory.cpdiscovery.aia_category_provider_factory_definition import AIaCategoryProviderFactoryDefinition
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.common.list.aii_bounded_list import AIiBoundedList
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind

if TYPE_CHECKING:
    from .aiig_type_1 import AIigType_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigCanonicalModelElement_1(AIiDataObject):
    """Contract for CanonicalModelElement."""

    __data_object__ = AIcdDataObject(description='CanonicalModelElement')

    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.ELEMENT, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='CanonicalModel')

    __xml_schema_fields__ = {
        'TypesList': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='types', value_kind=AInXmlValueKind.ELEMENT),
    }

    __xml_repeated_fields__ = ('TypesList',)

    class CONSTCanonicalModelElement:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__TYPES = 'types'

    @AIaDataObjectFieldListConstraints(min_items=1)
    @AIaDataObjectField(dataFieldName='types', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=AIiBoundedList, order=0, min_item_count=1, max_item_count=-1, is_empty_allowed=False)
    @abstractmethod
    def getTypesList(self) -> AIiBoundedList[AIigType_1]:
        """Return Canonical field types. (required, cardinality 1..-1)."""
        raise NotImplementedError

