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
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList

if TYPE_CHECKING:
    from .aiig_defs_codegen_name_convention_1 import AIigDefsCodegenNameConvention_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
class AIigDefscodegenNamingConventionsPropertyNameConventions_1(AIiDataObject):
    """Contract for DefscodegenNamingConventionsPropertyNameConventions."""

    __data_object__ = AIcdDataObject(description='DefscodegenNamingConventionsPropertyNameConventions')
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/properties/DefsCodegenNameConventions/properties/NameConventions#synthetic:synthetic_property_type', schema_version=1)
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json#/properties/DefsCodegenNameConventions/properties/NameConventions#synthetic:synthetic_property_type', schema_version=1)

    class CONSTDefscodegenNamingConventionsPropertyNameConventions:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__NAME_CONVENTION = 'NameConvention'
        KEY_ID__UNIQUE_PROFILE_IDS = 'UniqueProfileIds'
        FIELD_NAME__NAME = 'name'

    __key_definitions__ = {
        'NameConvention': ((CONSTDefscodegenNamingConventionsPropertyNameConventions.KEY_ID__UNIQUE_PROFILE_IDS, (CONSTDefscodegenNamingConventionsPropertyNameConventions.FIELD_NAME__NAME,), True),),
    }

    @AIaDataObjectField(dataFieldName='NameConvention', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=AIiMultiMappedList, order=0, min_item_count=0, max_item_count=-1, is_empty_allowed=False)
    @abstractmethod
    def getNameConventionList(self) -> AIiMultiMappedList[AIigDefsCodegenNameConvention_1]:
        """Return Canonical field NameConvention. (optional, cardinality 0..-1)."""
        raise NotImplementedError

