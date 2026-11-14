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
from eu.algites.lib.data.dataobject.jsondefs.aia_json_data_object import AIaJsonDataObject
from eu.algites.lib.data.dataobject.yamldefs.aia_yaml_data_object import AIaYamlDataObject
from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field import AIaXmlDataObjectField
from eu.algites.lib.data.dataobject.xmlschema.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind

if TYPE_CHECKING:
    from .aing_scalar_kind_1 import AIngScalarKind_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject
from eu.algites.lib.data.dataobject.xmlschema.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigScalar_1(AIiDataObject):
    """Canonical scalar value"""

    __data_object__ = AIcdDataObject(description='Canonical scalar value')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Scalar', schema_version=1)
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Scalar', schema_version=1)
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Scalar', schema_version=1)

    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Scalar')

    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Scalar')

    __xml_scalar_type_imports__ = {'scalar_kind': 'eu.algites.tool.codegen.defs.model.aing_scalar_kind_1:AIngScalarKind_1'}

    __xml_data_object_fields__ = {
        'scalar_kind': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='scalar_kind', value_kind=AInXmlValueKind.ELEMENT, ),
        'format': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='format', value_kind=AInXmlValueKind.ELEMENT, ),
        'min_length': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='min_length', value_kind=AInXmlValueKind.ELEMENT, ),
        'max_length': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='max_length', value_kind=AInXmlValueKind.ELEMENT, ),
        'pattern': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='pattern', value_kind=AInXmlValueKind.ELEMENT, ),
        'minimum': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='minimum', value_kind=AInXmlValueKind.ELEMENT, ),
        'maximum': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='maximum', value_kind=AInXmlValueKind.ELEMENT, ),
        'exclusive_minimum': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='exclusive_minimum', value_kind=AInXmlValueKind.ELEMENT, ),
        'exclusive_maximum': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='exclusive_maximum', value_kind=AInXmlValueKind.ELEMENT, ),
        'multiple_of': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='multiple_of', value_kind=AInXmlValueKind.ELEMENT, ),
    }

    __xml_schema_fields__ = {
        'scalar_kind': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='scalar_kind', value_kind=AInXmlValueKind.ELEMENT),
        'format': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='format', value_kind=AInXmlValueKind.ELEMENT),
        'min_length': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='min_length', value_kind=AInXmlValueKind.ELEMENT),
        'max_length': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='max_length', value_kind=AInXmlValueKind.ELEMENT),
        'pattern': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='pattern', value_kind=AInXmlValueKind.ELEMENT),
        'minimum': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='minimum', value_kind=AInXmlValueKind.ELEMENT),
        'maximum': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='maximum', value_kind=AInXmlValueKind.ELEMENT),
        'exclusive_minimum': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='exclusive_minimum', value_kind=AInXmlValueKind.ELEMENT),
        'exclusive_maximum': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='exclusive_maximum', value_kind=AInXmlValueKind.ELEMENT),
        'multiple_of': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='multiple_of', value_kind=AInXmlValueKind.ELEMENT),
    }

    class CONSTScalar:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__SCALAR_KIND = 'scalar_kind'
        FIELD_NAME__FORMAT = 'format'
        FIELD_NAME__MIN_LENGTH = 'min_length'
        FIELD_NAME__MAX_LENGTH = 'max_length'
        FIELD_NAME__PATTERN = 'pattern'
        FIELD_NAME__MINIMUM = 'minimum'
        FIELD_NAME__MAXIMUM = 'maximum'
        FIELD_NAME__EXCLUSIVE_MINIMUM = 'exclusive_minimum'
        FIELD_NAME__EXCLUSIVE_MAXIMUM = 'exclusive_maximum'
        FIELD_NAME__MULTIPLE_OF = 'multiple_of'

    @AIaDataObjectField(dataFieldName='scalar_kind', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getScalarKind(self) -> AIngScalarKind_1:
        """Return Canonical field scalar_kind. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='format', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=str, order=1, min_item_count=0, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getFormat(self) -> str:
        """Return Canonical field format. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='min_length', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=int, order=2, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getMinLength(self) -> int:
        """Return Canonical field min_length. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='max_length', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=int, order=3, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getMaxLength(self) -> int:
        """Return Canonical field max_length. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='pattern', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=str, order=4, min_item_count=0, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getPattern(self) -> str:
        """Return Canonical field pattern. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='minimum', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=str, order=5, min_item_count=0, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getMinimum(self) -> str:
        """Return Canonical field minimum. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='maximum', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=str, order=6, min_item_count=0, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getMaximum(self) -> str:
        """Return Canonical field maximum. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='exclusive_minimum', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=bool, order=7, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getExclusiveMinimum(self) -> bool:
        """Return Canonical field exclusive_minimum. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='exclusive_maximum', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=bool, order=8, min_item_count=0, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getExclusiveMaximum(self) -> bool:
        """Return Canonical field exclusive_maximum. (optional, cardinality 0..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='multiple_of', presence=AInFieldPresenceKind.ALLOWED, allows_null=False, expected_type=str, order=9, min_item_count=0, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getMultipleOf(self) -> str:
        """Return Canonical field multiple_of. (optional, cardinality 0..1)."""
        raise NotImplementedError

