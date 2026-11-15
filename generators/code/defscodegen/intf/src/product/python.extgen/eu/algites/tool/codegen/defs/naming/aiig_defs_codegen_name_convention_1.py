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
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind

if TYPE_CHECKING:
    from .aiig_defs_codegen_name_convention_property_structure_naming_1 import AIigDefsCodegenNameConventionPropertyStructureNaming_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigDefsCodegenNameConvention_1(AIiDataObject):
    """Contract for DefsCodegenNameConvention."""

    __data_object__ = AIcdDataObject(description='DefsCodegenNameConvention')
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenNameConvention', schema_version=1)
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenNameConvention', schema_version=1)

    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd', namespace_local_name='DefsCodegenNameConvention')

    __xml_schema_fields__ = {
        'CommonNamingConvention': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='CommonNamingConvention', value_kind=AInXmlValueKind.ELEMENT),
        'StructureNaming': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='StructureNaming', value_kind=AInXmlValueKind.ELEMENT),
        'Name': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='name', value_kind=AInXmlValueKind.ATTRIBUTE),
    }

    class CONSTDefsCodegenNameConvention:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__COMMON_NAMING_CONVENTION = 'CommonNamingConvention'
        FIELD_NAME__STRUCTURE_NAMING = 'StructureNaming'
        FIELD_NAME__NAME = 'name'
        KEY_ID__UNIQUE_STRUCTURE_ROLES = 'UniqueStructureRoles'
        FIELD_NAME__KIND = 'kind'

    __scoped_key_definitions__ = {
        'StructureNaming': (
            ('Rule', 'UniqueStructureRoles', ('kind',), True),
        ),
    }

    @AIaDataObjectField(dataFieldName='CommonNamingConvention', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=str, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getCommonNamingConvention(self) -> str:
        """Return Canonical field CommonNamingConvention. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='StructureNaming', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=1, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getStructureNaming(self) -> AIigDefsCodegenNameConventionPropertyStructureNaming_1:
        """Return Canonical field StructureNaming. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectFieldStringConstraints(min_length=1)
    @AIaDataObjectField(dataFieldName='name', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=str, order=2, min_item_count=1, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getName(self) -> str:
        """Return Canonical field name. (required, cardinality 1..1)."""
        raise NotImplementedError

