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
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind

if TYPE_CHECKING:
    from .aiig_defs_codegen_name_conventions_type_property_name_conventions_1 import AIigDefsCodegenNameConventionsTypePropertyNameConventions_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1(AIiDataObject):
    """Contract for DefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions."""

    __data_object__ = AIcdDataObject(description='DefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions')

    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='', namespace_local_name='generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd/schema/DefsCodegenNameConventionsType/complexContent/extension/sequence/sequence/0#synthetic:synthetic_property_type')

    __xml_schema_fields__ = {
        'NameConventions': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='NameConventions', value_kind=AInXmlValueKind.ELEMENT),
    }

    class CONSTDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__NAME_CONVENTIONS = 'NameConventions'
        KEY_ID__UNIQUE_PROFILE_IDS = 'UniqueProfileIds'
        FIELD_NAME__NAME = 'name'

    __scoped_key_definitions__ = {
        'NameConventions': (
            ('NameConvention', 'UniqueProfileIds', ('name',), True),
        ),
    }

    @AIaDataObjectField(dataFieldName='NameConventions', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getNameConventions(self) -> AIigDefsCodegenNameConventionsTypePropertyNameConventions_1:
        """Return Canonical field NameConventions. (required, cardinality 1..1)."""
        raise NotImplementedError

