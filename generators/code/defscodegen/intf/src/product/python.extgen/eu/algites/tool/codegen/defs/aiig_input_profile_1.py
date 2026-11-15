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

if TYPE_CHECKING:
    from .aing_source_kind_type_1 import AIngSourceKindType_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
class AIigInputProfile_1(AIiDataObject):
    """Defines how defs-codegen interprets one supported source-definition family."""

    __data_object__ = AIcdDataObject(description='Defines how defs-codegen interprets one supported source-definition family.')
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.input-profile', schema_version=1, schema_url='https://defs.dev.algites.eu/api/jsondefs/eu/algites/tool/codegen/defs/input-profile_1.jsondef.schema.json')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.input-profile', schema_version=1, schema_url='https://defs.dev.algites.eu/api/yamldefs/eu/algites/tool/codegen/defs/input-profile_1.yamldef.schema.json')

    class CONSTInputProfile:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__SOURCE_KIND = 'SourceKind'
        FIELD_NAME__NAMING_PROFILE = 'NamingProfile'
        FIELD_NAME__REQUIRE_CANONICAL_IDENTITY = 'RequireCanonicalIdentity'
        FIELD_NAME__REQUIRE_DEFINITION_VERSION = 'RequireDefinitionVersion'

    @AIaDataObjectField(dataFieldName='SourceKind', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getSourceKind(self) -> AIngSourceKindType_1:
        """Return Canonical field SourceKind. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='NamingProfile', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=str, order=1, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getNamingProfile(self) -> str:
        """Return Names the naming profile applied while interpreting and generating identifiers. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='RequireCanonicalIdentity', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=bool, order=2, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getRequireCanonicalIdentity(self) -> bool:
        """Return Requires every loaded definition to expose a canonical identity. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='RequireDefinitionVersion', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=bool, order=3, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getRequireDefinitionVersion(self) -> bool:
        """Return Requires every loaded definition to expose a semantic version. (optional, cardinality 0..1)."""
        raise NotImplementedError

