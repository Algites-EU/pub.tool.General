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
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.naming.convention.aiig_common_naming_conventions_1 import AIigCommonNamingConventions_1

if TYPE_CHECKING:
    from .aiig_defscodegen_naming_conventions_property_defs_codegen_name_conventions_1 import AIigDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
class AIigDefscodegenNamingConventions_1(AIigCommonNamingConventions_1):
    """New defs naming profiles; other-domain roles forbidden."""

    __data_object__ = AIcdDataObject(description='New defs naming profiles; other-domain roles forbidden.')
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions', schema_version=1, schema_url='https://defs.dev.algites.eu/api/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions', schema_version=1, schema_url='https://defs.dev.algites.eu/api/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json')

    class CONSTDefscodegenNamingConventions:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__DEFS_CODEGEN_NAME_CONVENTIONS = 'DefsCodegenNameConventions'

    @AIaDataObjectField(dataFieldName='DefsCodegenNameConventions', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getDefsCodegenNameConventions(self) -> AIigDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1:
        """Return Canonical field DefsCodegenNameConventions. (required, cardinality 1..1)."""
        raise NotImplementedError

