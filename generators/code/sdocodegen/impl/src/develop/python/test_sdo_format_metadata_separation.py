"""Regression tests for independent JSONDEFS/YAMLDEFS metadata."""
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from explicit_sdo_fixture import configured_service


class AIigIndependentFormatMetadata_1(AIiDataObject):
    """JSONDEFS and YAMLDEFS have independent identities and URLs."""
    __data_object__ = AIcdDataObject()
    __json_schema__ = AIaDataObjectJsonSchema(
        schema_id='json-identity', schema_version=2,
        schema_url='https://example.org/json-schema')
    __yaml_schema__ = AIaDataObjectYamlSchema(
        schema_id='yaml-identity', schema_version=5,
        schema_url='https://example.org/yaml-schema')
    __data_object_fields__ = ()


def test_json_and_yaml_metadata_are_independent():
    """SDO preserves one descriptor for each format without aliases."""
    read = AIigIndependentFormatMetadata_1
    read.__module__ = 'unit.example.aiig_independent_format_metadata_1'
    result = configured_service().generate(read)
    assert result.implementation.source_definition_id == 'json-identity'
    assert result.implementation.source_definition_version == 2
    for emitted in (result.mutable_interface.source, result.implementation.source):
        assert emitted.count('__json_schema__ = AIaDataObjectJsonSchema(') == 1
        assert emitted.count('__yaml_schema__ = AIaDataObjectYamlSchema(') == 1
        assert "schema_id='json-identity', schema_version=2" in emitted
        assert "schema_id='json-identity', schema_version=2" in emitted
        assert "schema_id='yaml-identity', schema_version=5" in emitted
        assert 'https://example.org/json-schema' in emitted
        assert 'https://example.org/yaml-schema' in emitted


def test_bootstrap_does_not_label_codegen_validation_as_bootstrap():
    """Diagnostics are Codegen-owned even at the bootstrap invocation boundary."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[7]
    source = (root / 'devops/bootstrap/generate_sources.py').read_text(encoding='utf-8')
    assert "report_exception(failure, generator='Codegen')" in source
    assert 'Bootstrap Codegen' not in source
