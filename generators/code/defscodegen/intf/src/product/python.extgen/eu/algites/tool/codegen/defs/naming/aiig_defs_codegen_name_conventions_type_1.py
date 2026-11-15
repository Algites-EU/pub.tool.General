from __future__ import annotations
from typing import Any

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField
from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.lib.data.dataobject.aia_data_object_field_default import AIaDataObjectFieldDefault
from eu.algites.lib.data.dataobject.ain_data_object_field_default_kind import AInDataObjectFieldDefaultKind
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
from eu.algites.lib.naming.convention.aiig_common_naming_conventions_1 import AIigCommonNamingConventions_1

if TYPE_CHECKING:
    from .aiig_defs_codegen_name_conventions_type_property_defs_codegen_name_conventions_1 import AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigDefsCodegenNameConventionsType_1(AIigCommonNamingConventions_1):
    """Contract for DefsCodegenNameConventionsType."""

    __data_object__ = AIcdDataObject(description='DefsCodegenNameConventionsType')

    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd', namespace_local_name='DefsCodegenNameConventionsType')

    __xml_schema_fields__ = {
        'DefsCodegenNameConventions': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='DefsCodegenNameConventions', value_kind=AInXmlValueKind.ELEMENT),
    }

    class CONSTDefsCodegenNameConventionsType:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__DEFS_CODEGEN_NAME_CONVENTIONS = 'DefsCodegenNameConventions'

    @AIaDataObjectField(dataFieldName='DefsCodegenNameConventions', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getDefsCodegenNameConventions(self) -> AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1:
        """Return Canonical field DefsCodegenNameConventions. (required, cardinality 1..1)."""
        raise NotImplementedError

