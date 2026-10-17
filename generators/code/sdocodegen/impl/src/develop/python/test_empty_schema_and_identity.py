"""An annotated empty read-only schema is a valid SmartDataObject contract."""
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService


class AIigEmpty(AIiDataObject):
    __data_object__ = AIcdDataObject(schema_id='unit.empty', schema_version=1)
    __data_object_fields__ = ()


def test_empty_contract_and_importable_generated_identity():
    AIigEmpty.__module__ = 'unit.example.aiig_empty'
    result=AIcSdoCodegenService().generate(AIigEmpty)
    assert result.mutable_interface.type_name == 'AIigdEmpty'
    assert result.implementation.type_name == 'AIcgdEmpty'
    assert result.implementation.fully_qualified_type_name.endswith('.AIcgdEmpty')
    assert result.implementation.source_definition_id == 'unit.empty'
    assert result.implementation.source_definition_version == 1
