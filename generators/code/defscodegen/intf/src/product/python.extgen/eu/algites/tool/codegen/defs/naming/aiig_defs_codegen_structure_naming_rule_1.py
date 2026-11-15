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
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind

if TYPE_CHECKING:
    from .aing_defscodegen_structure_kind_1 import AIngDefscodegenStructureKind_1


from eu.algites.lib.data.dataobject.aia_data_object_field_object_constraints import AIaDataObjectFieldObjectConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_list_constraints import AIaDataObjectFieldListConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_numeric_constraints import AIaDataObjectFieldNumericConstraints
from eu.algites.lib.data.dataobject.aia_data_object_field_string_constraints import AIaDataObjectFieldStringConstraints
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
class AIigDefsCodegenStructureNamingRule_1(AIiDataObject):
    """Contract for DefsCodegenStructureNamingRule."""

    __data_object__ = AIcdDataObject(description='DefsCodegenStructureNamingRule')
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenStructureNamingRule', schema_version=1)
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.naming.defscodegen-naming-conventions#/$defs/DefsCodegenStructureNamingRule', schema_version=1)

    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd', namespace_local_name='DefsCodegenStructureNamingRule')

    __xml_scalar_type_imports__ = {'kind': 'eu.algites.tool.codegen.defs.naming.aing_defscodegen_structure_kind_1:AIngDefscodegenStructureKind_1'}

    __xml_schema_fields__ = {
        'Value': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='Value', value_kind=AInXmlValueKind.ELEMENT),
        'Kind': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='kind', value_kind=AInXmlValueKind.ATTRIBUTE),
    }

    class CONSTDefsCodegenStructureNamingRule:
        """Stable key IDs and field names for this DataObject."""
        FIELD_NAME__VALUE = 'Value'
        FIELD_NAME__KIND = 'kind'

    @AIaDataObjectField(dataFieldName='Value', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, expected_type=str, order=0, min_item_count=1, max_item_count=1, is_empty_allowed=True)
    @abstractmethod
    def getValue(self) -> str:
        """Return Canonical field Value. (required, cardinality 1..1)."""
        raise NotImplementedError

    @AIaDataObjectField(dataFieldName='kind', presence=AInFieldPresenceKind.REQUIRED, allows_null=False, order=1, min_item_count=1, max_item_count=1, is_empty_allowed=False)
    @abstractmethod
    def getKind(self) -> AIngDefscodegenStructureKind_1:
        """Return Canonical field kind. (required, cardinality 1..1)."""
        raise NotImplementedError

