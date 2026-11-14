"""Generated SmartDataObject implementation for AIigEnum_1."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_enum_value_1 import AIigdEnumValue_1
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.dataobject.yamldefs.aia_yaml_data_object import AIaYamlDataObject
from eu.algites.lib.data.dataobject.jsondefs.aia_json_data_object import AIaJsonDataObject
from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_enum_1 import AIigdEnum_1
from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject
from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_enum_1 import AIigEnum_1


@AIaSmartDataObjectImplementationBinding(readContracts=(AIigEnum_1,))
class AIcgdEnum_1(AIcSmartDataObject, AIigdEnum_1['AIigdEnumValue_1']):
    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Generated implementation; inherited fields use parent behavior."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Enum', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Enum', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Enum', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')

    def getBaseScalarType(self):
        return self.get_EffectiveField('BaseScalarType')

    def setBaseScalarType(self, a_value):
        self.set_RawField('BaseScalarType', a_value)

    def _getRaw_BaseScalarType(self):
        return self.get_RawField('BaseScalarType')

    def _isPresent_BaseScalarType(self):
        return self.isPresent_Field('BaseScalarType')

    def _unset_BaseScalarType(self):
        self.unset_Field('BaseScalarType')

    def getValuesList(self) -> list[AIigdEnumValue_1]:
        return self.get_OrCreateCollectionField('ValuesList', False)

    def _getRaw_ValuesList(self) -> list[AIigdEnumValue_1]:
        return self.get_RawField('ValuesList')

    def _isPresent_ValuesList(self):
        return self.isPresent_Field('ValuesList')

    def _unset_ValuesList(self):
        self.unset_Field('ValuesList')
