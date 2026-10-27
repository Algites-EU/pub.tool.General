"""An annotated empty read-only schema is a valid SmartDataObject contract."""
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from explicit_sdo_fixture import configured_service, explicit_generic_manifest


class AIigEmpty(AIiDataObject):
    __data_object__ = AIcdDataObject(schema_id='unit.empty', schema_version=1)
    __data_object_fields__ = ()


def test_empty_contract_and_importable_generated_identity():
    AIigEmpty.__module__ = 'unit.example.aiig_empty'
    result=configured_service().generate(AIigEmpty)
    assert result.mutable_interface.type_name == 'AIigdEmpty'
    assert result.implementation.type_name == 'AIcgdEmpty'
    assert result.implementation.fully_qualified_type_name.endswith('.AIcgdEmpty')
    assert result.implementation.source_definition_id == 'unit.empty'
    assert result.implementation.source_definition_version == 1
