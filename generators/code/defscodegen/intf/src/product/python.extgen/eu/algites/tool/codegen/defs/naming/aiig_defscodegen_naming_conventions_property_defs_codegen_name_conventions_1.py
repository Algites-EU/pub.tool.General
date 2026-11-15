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

if TYPE_CHECKING:
    from .aiig_defscodegen_naming_conventions_property_name_conventions_1 import AIigDefscodegenNamingConventionsPropertyNameConventions_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
class AIigDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1(AIiDataObject):
    """Contract for DefscodegenNamingConventionsPropertyDefsCodegenNameConventions."""

    __data_object__ = AIcdDataObject(description='DefscodegenNamingConventionsPropertyDefsCodegenNameConventions')
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/properties/DefsCodegenNameConventions#synthetic:synthetic_property_type', schema_version=1)
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json#/properties/DefsCodegenNameConventions#synthetic:synthetic_property_type', schema_version=1)

    class CONSTDefscodegenNamingConventionsPropertyDefsCodegenNameConventions:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__NAME_CONVENTIONS = 'NameConventions'

    @AIaDataObjectField(dataFieldName='NameConventions', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getNameConventions(self) -> AIigDefscodegenNamingConventionsPropertyNameConventions_1:
        """Return Canonical field NameConventions. (required, cardinality 1..1)."""
        raise NotImplementedError

